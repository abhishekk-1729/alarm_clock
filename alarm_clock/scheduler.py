"""Scheduling logic - figuring out when an alarm should next ring."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from alarm_clock.models import Alarm, DAY_INDEX, parse_time_str


def next_fire_datetime(alarm: Alarm, now: Optional[datetime] = None) -> datetime:
    """Compute the next datetime this alarm will fire, ignoring whether it
    has already rung today. Used for informational display purposes
    (e.g. telling the user when an alarm will first go off).
    """
    now = now or datetime.now()
    hour, minute = parse_time_str(alarm.time)
    candidate_today = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if alarm.days == ["once"]:
        if candidate_today > now:
            return candidate_today
        return candidate_today + timedelta(days=1)

    # Recurring: find the next matching weekday (today counts if time not passed yet)
    target_indices = {DAY_INDEX[d] for d in alarm.days}
    for offset in range(0, 8):
        check_date = now + timedelta(days=offset)
        if check_date.weekday() not in target_indices:
            continue
        candidate = check_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if offset == 0 and candidate <= now:
            continue
        return candidate

    # Should not happen given 7 day lookahead, but keep a safe fallback.
    return candidate_today + timedelta(days=1)


def is_due(alarm: Alarm, now: Optional[datetime] = None) -> bool:
    """Return True if the alarm should ring right now (matches today's
    weekday/once, matches HH:MM, and hasn't already rung today, and is not
    skipped for today).
    """
    if not alarm.enabled:
        return False

    now = now or datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    if alarm.last_rung_on == today_str:
        return False

    if alarm.skip_date == today_str:
        return False

    hour, minute = parse_time_str(alarm.time)
    if now.hour != hour or now.minute != minute:
        return False

    if alarm.days == ["once"]:
        return True

    weekday = now.weekday()
    target_indices = {DAY_INDEX[d] for d in alarm.days}
    return weekday in target_indices


def describe_next_fire(alarm: Alarm, now: Optional[datetime] = None) -> str:
    """Human readable description of when the alarm will next ring,
    including an explicit note when a 'once' alarm rolls to tomorrow.
    """
    now = now or datetime.now()
    fire_time = next_fire_datetime(alarm, now)
    today = now.date()

    if fire_time.date() == today:
        return f"today at {fire_time.strftime('%H:%M')}"
    elif fire_time.date() == today + timedelta(days=1):
        return f"tomorrow at {fire_time.strftime('%H:%M')}"
    else:
        return fire_time.strftime("%A %b %d at %H:%M")
