"""The ring engine: displays the alarm banner, sounds the terminal bell,
and listens for a keypress response with a timeout.

Uses only the standard library (select + stdin) so no external dependency
is required for keyboard input handling.
"""

from __future__ import annotations

import sys
import select
import time
from datetime import datetime, timedelta
from typing import Optional

from alarm_clock.config import Config
from alarm_clock.models import Alarm
from alarm_clock.logging_setup import get_logger
from alarm_clock import ui

logger = get_logger()

BANNER = r"""
   _    _    ____  __  __ _ 
  / \  | |  / \   |  \/  | |
 / _ \ | | /  _ \ | |\/| | |
/ ___ \| |/ ___ \ | |  | |_|
/_/   \_\_/_/   \_\|_|  |_(_)
"""

RING_PROMPT = (
    "[s] snooze   [s<N>] snooze N min   [k] skip today   [d] dismiss forever"
)


def _read_key_with_timeout(timeout_seconds: float) -> Optional[str]:
    """Read a line of input with a timeout, without blocking forever.
    Returns the stripped input string, or None if the timeout elapsed
    with no input.
    """
    try:
        ready, _, _ = select.select([sys.stdin], [], [], timeout_seconds)
    except (OSError, ValueError):
        # stdin not selectable in this environment; just wait out the slice.
        time.sleep(timeout_seconds)
        return None

    if ready:
        line = sys.stdin.readline()
        if line == "":
            # EOF on stdin (e.g. piped input exhausted) - treat as no more
            # responses coming, but don't busy loop reading EOF repeatedly.
            time.sleep(min(timeout_seconds, 0.5))
            return None
        return line.strip()
    return None


def _ring_bell(times: int = 1) -> None:
    sys.stdout.write("\a" * times)
    sys.stdout.flush()


def _print_banner(alarms: list[Alarm], remaining_seconds: int) -> None:
    print()
    print(ui.red(ui.bold(BANNER)))
    labels = ", ".join(a.label for a in alarms)
    times = ", ".join(a.time for a in alarms)
    print(ui.bold(f"  ALARM: {labels}"))
    print(ui.dim(f"  Scheduled for: {times}"))
    print(ui.dim(f"  Will stop automatically in {remaining_seconds} seconds if unanswered."))
    print()
    print(ui.yellow(RING_PROMPT))
    print(ui.dim("  > "), end="", flush=True)


class RingResult:
    SNOOZED = "snoozed"
    SKIPPED = "skipped"
    DISMISSED = "dismissed"
    UNATTENDED = "unattended"


def ring_alarms(alarms: list[Alarm], config: Config, dry_run: bool = False):
    """Ring one or more clubbed alarms together. Blocks until the user
    responds or the timeout elapses. Returns a tuple of
    (outcomes, snooze_minutes_chosen) both keyed by alarm id.

    In dry_run mode, the same flow runs but is clearly labeled as a test
    and does not require any special handling - it behaves identically
    from the user's perspective so testing is meaningful.
    """
    ring_duration = config.ring_duration_seconds
    for a in alarms:
        if a.ring_duration_seconds:
            ring_duration = max(ring_duration, a.ring_duration_seconds)

    deadline = datetime.now() + timedelta(seconds=ring_duration)
    outcomes: dict[str, str] = {}
    snooze_minutes_chosen: dict[str, int] = {}

    label_tag = "[TEST RING] " if dry_run else ""
    print()
    print(ui.magenta(f"{label_tag}{'=' * 60}"))

    last_bell = 0.0
    while datetime.now() < deadline and not outcomes:
        remaining = int((deadline - datetime.now()).total_seconds())
        now_ts = time.time()
        if now_ts - last_bell >= 2:
            _ring_bell(2)
            last_bell = now_ts

        _print_banner(alarms, remaining)

        response = _read_key_with_timeout(2.0)
        if response is None:
            continue

        response = response.lower()
        if response == "" or response == "s":
            chosen_minutes = config.snooze_minutes
            for a in alarms:
                outcomes[a.id] = RingResult.SNOOZED
                snooze_minutes_chosen[a.id] = a.snooze_minutes or chosen_minutes
            print(ui.green(f"\nSnoozing for {chosen_minutes} minutes..."))
        elif response.startswith("s") and response[1:].isdigit():
            chosen_minutes = int(response[1:])
            for a in alarms:
                outcomes[a.id] = RingResult.SNOOZED
                snooze_minutes_chosen[a.id] = chosen_minutes
            print(ui.green(f"\nSnoozing for {chosen_minutes} minutes..."))
        elif response == "k":
            for a in alarms:
                outcomes[a.id] = RingResult.SKIPPED
            print(ui.yellow("\nSkipping for today..."))
        elif response == "d":
            for a in alarms:
                outcomes[a.id] = RingResult.DISMISSED
            print(ui.red("\nDismissed. This alarm has been disabled."))
        else:
            print(ui.red(f"\nUnrecognized response: '{response}'. Try again."))

    if not outcomes:
        for a in alarms:
            outcomes[a.id] = RingResult.UNATTENDED
        print(ui.dim("\nNo response received. Alarm stopped automatically."))
        logger.warning(
            "Alarm(s) unattended: %s", ", ".join(a.label for a in alarms)
        )

    print(ui.magenta("=" * 60))
    print()
    return outcomes, snooze_minutes_chosen

