"""Applies the outcome of a ring (snooze/skip/dismiss/unattended) back onto
alarm state, and persists it.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from alarm_clock.models import Alarm
from alarm_clock.ring_engine import RingResult
from alarm_clock.logging_setup import get_logger

logger = get_logger()


def apply_outcome(alarm: Alarm, outcome: str, snooze_minutes: int, now: datetime) -> None:
    """Mutate the given alarm in place based on the ring outcome."""
    today_str = now.strftime("%Y-%m-%d")
    is_once = alarm.days == ["once"]

    if outcome == RingResult.SNOOZED:
        snooze_time = now + timedelta(minutes=snooze_minutes)
        alarm.time = snooze_time.strftime("%H:%M")
        logger.info(
            "Alarm '%s' (%s) snoozed for %d minutes, next ring at %s",
            alarm.label, alarm.id, snooze_minutes, alarm.time,
        )
        # Snoozed alarms are not marked as "rung today" so the watch loop
        # picks them back up at the new (later) time today.
        return

    if outcome == RingResult.SKIPPED:
        alarm.skip_date = today_str
        logger.info("Alarm '%s' (%s) skipped for today", alarm.label, alarm.id)

    elif outcome == RingResult.DISMISSED:
        alarm.enabled = False
        logger.info("Alarm '%s' (%s) dismissed permanently (disabled)", alarm.label, alarm.id)

    elif outcome == RingResult.UNATTENDED:
        logger.warning("Alarm '%s' (%s) went unattended", alarm.label, alarm.id)

    alarm.last_rung_on = today_str

    if is_once and outcome in (RingResult.UNATTENDED, RingResult.SKIPPED):
        # One-off alarms have no future occurrence once today's chance
        # has passed without a snooze, so disable to avoid confusion.
        alarm.enabled = False
