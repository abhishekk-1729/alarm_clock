"""Implementations for each CLI subcommand. Kept separate from argument
parsing (cli.py) so the logic is easy to test and read.
"""

from __future__ import annotations

from alarm_clock import ui
from alarm_clock.config import load_config, save_config
from alarm_clock.errors import AlarmNotFoundError
from alarm_clock.logging_setup import get_logger
from alarm_clock.models import Alarm, parse_time_str, parse_days_str
from alarm_clock.ring_engine import ring_alarms
from alarm_clock.scheduler import describe_next_fire
from alarm_clock.storage import load_alarms, save_alarms, get_alarm, find_alarm_loose
from alarm_clock.watch import run_watch_loop

logger = get_logger()


def cmd_add(args) -> None:
    days = parse_days_str(args.days)
    hour, minute = parse_time_str(args.time)  # validates format
    time_str = f"{hour:02d}:{minute:02d}"

    alarm = Alarm(
        time=time_str,
        days=days,
        label=args.label or "Alarm",
        snooze_minutes=args.snooze_minutes,
        ring_duration_seconds=args.ring_duration,
    )

    alarms = load_alarms()
    alarms.append(alarm)
    save_alarms(alarms)
    logger.info("Alarm added: id=%s time=%s days=%s label=%s", alarm.id, alarm.time, alarm.days_display(), alarm.label)

    ui.success(f"Alarm '{alarm.label}' created (id: {alarm.id})")
    ui.info(f"Set for {ui.bold(alarm.days_display())} at {ui.bold(alarm.time)}")

    when = describe_next_fire(alarm)
    if when.startswith("tomorrow"):
        ui.warn(f"That time has already passed today, so this alarm will first ring {when}.")
    else:
        ui.info(f"Will next ring {when}.")


def cmd_list(args) -> None:
    alarms = load_alarms()
    if not alarms:
        ui.info("You don't have any alarms yet.")
        ui.hint("Add one with: alarm add --time 07:30 --days mon,tue,wed,thu,fri --label \"Wake up\"")
        return

    header = f"{'ID':<10} {'STATUS':<10} {'TIME':<7} {'DAYS':<16} {'LABEL'}"
    print(ui.bold(header))
    print(ui.dim(ui.rule(width=len(header) + 10)))

    for alarm in sorted(alarms, key=lambda a: a.time):
        status = ui.green("enabled") if alarm.enabled else ui.dim("disabled")
        status_padded = status + " " * (10 - _strip_len(status))
        line = f"{alarm.id:<10} {status_padded} {alarm.time:<7} {alarm.days_display():<16} {alarm.label}"
        print(line)


def _strip_len(colored_text: str) -> int:
    """Approximate visible length accounting for our known status words."""
    for word in ("enabled", "disabled"):
        if word in colored_text:
            return len(word)
    return len(colored_text)


def _resolve_alarm(alarm_id: str):
    alarms = load_alarms()
    try:
        alarm = get_alarm(alarms, alarm_id)
        return alarms, alarm
    except AlarmNotFoundError:
        loose = find_alarm_loose(alarms, alarm_id)
        if loose:
            return alarms, loose
        raise


def cmd_delete(args) -> None:
    alarms, alarm = _resolve_alarm(args.id)
    alarms = [a for a in alarms if a.id != alarm.id]
    save_alarms(alarms)
    logger.info("Alarm deleted: id=%s label=%s", alarm.id, alarm.label)
    ui.success(f"Deleted alarm '{alarm.label}' (id: {alarm.id})")


def cmd_update(args) -> None:
    alarms, alarm = _resolve_alarm(args.id)

    changed = []
    if args.time:
        hour, minute = parse_time_str(args.time)
        alarm.time = f"{hour:02d}:{minute:02d}"
        changed.append("time")
    if args.days:
        alarm.days = parse_days_str(args.days)
        changed.append("days")
    if args.label:
        alarm.label = args.label
        changed.append("label")
    if args.snooze_minutes is not None:
        alarm.snooze_minutes = args.snooze_minutes
        changed.append("snooze duration")
    if args.ring_duration is not None:
        alarm.ring_duration_seconds = args.ring_duration
        changed.append("ring duration")

    if not changed:
        ui.warn("Nothing to update — provide at least one field to change.")
        ui.hint("Example: alarm update " + alarm.id + " --time 08:00")
        return

    save_alarms(alarms)
    logger.info("Alarm updated: id=%s fields=%s", alarm.id, ",".join(changed))
    ui.success(f"Updated {', '.join(changed)} for alarm '{alarm.label}' (id: {alarm.id})")

    when = describe_next_fire(alarm)
    if when.startswith("tomorrow"):
        ui.warn(f"That time has already passed today, so this alarm will next ring {when}.")


def cmd_enable(args) -> None:
    alarms, alarm = _resolve_alarm(args.id)
    alarm.enabled = True
    save_alarms(alarms)
    logger.info("Alarm enabled: id=%s", alarm.id)
    ui.success(f"Enabled alarm '{alarm.label}' (id: {alarm.id})")


def cmd_disable(args) -> None:
    alarms, alarm = _resolve_alarm(args.id)
    alarm.enabled = False
    save_alarms(alarms)
    logger.info("Alarm disabled: id=%s", alarm.id)
    ui.success(f"Disabled alarm '{alarm.label}' (id: {alarm.id})")


def cmd_watch(args) -> None:
    run_watch_loop()


def cmd_test(args) -> None:
    alarms, alarm = _resolve_alarm(args.id)
    config = load_config()

    ui.info(f"Test ringing alarm '{alarm.label}' now. This is a dry run — your schedule is unaffected.")
    outcomes, _ = ring_alarms([alarm], config, dry_run=True)
    outcome = outcomes.get(alarm.id)
    ui.info(f"Test complete. Recorded response: {outcome}")
    logger.info("Test ring completed: id=%s outcome=%s", alarm.id, outcome)


def cmd_config_show(args) -> None:
    config = load_config()
    changed = False

    if args.ring_duration is not None:
        config.ring_duration_seconds = args.ring_duration
        changed = True
    if args.snooze_minutes is not None:
        config.snooze_minutes = args.snooze_minutes
        changed = True

    if changed:
        save_config(config)
        logger.info("Global config updated: %s", config.to_dict())
        ui.success("Configuration updated.")

    print()
    print(ui.bold("Current defaults:"))
    print(f"  Ring duration:  {config.ring_duration_seconds} seconds")
    print(f"  Snooze length:  {config.snooze_minutes} minutes")
    print()
    ui.hint("Per-alarm overrides take priority over these defaults.")
