"""The 'alarm watch' foreground loop.

Polls the persisted alarm list every few seconds, detects due alarms
(clubbing any that match to the same second), rings them, and applies
the resulting outcome back to storage.
"""

from __future__ import annotations

import time
from datetime import datetime

from alarm_clock.config import load_config, POLL_INTERVAL_SECONDS
from alarm_clock.storage import load_alarms, save_alarms
from alarm_clock.scheduler import is_due
from alarm_clock.ring_engine import ring_alarms
from alarm_clock.actions import apply_outcome
from alarm_clock.logging_setup import get_logger
from alarm_clock import ui

logger = get_logger()


def run_watch_loop() -> None:
    print(ui.bold(ui.cyan("Alarm Clock - watching for due alarms.")))
    print(ui.dim("Keep this terminal window open. Press Ctrl+C to stop watching."))
    print()
    logger.info("Watch loop started")

    try:
        while True:
            now = datetime.now()
            alarms = load_alarms()
            due = [a for a in alarms if is_due(a, now)]

            if due:
                config = load_config()
                outcomes, snooze_minutes_chosen = ring_alarms(due, config)

                for alarm in due:
                    outcome = outcomes.get(alarm.id)
                    minutes = snooze_minutes_chosen.get(alarm.id, config.snooze_minutes)
                    apply_outcome(alarm, outcome, minutes, now)

                save_alarms(alarms)

            time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print()
        print(ui.dim("Stopped watching. Your alarms remain saved and will"))
        print(ui.dim("ring the next time you run 'alarm watch'."))
        logger.info("Watch loop stopped by user")
