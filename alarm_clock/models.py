"""Data model for an Alarm."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

from alarm_clock.errors import ValidationError

VALID_DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
DAY_INDEX = {day: idx for idx, day in enumerate(VALID_DAYS)}  # mon=0 ... sun=6


def parse_time_str(time_str: str) -> tuple[int, int]:
    """Parse and validate a HH:MM 24-hour time string."""
    parts = time_str.strip().split(":")
    if len(parts) != 2:
        raise ValidationError(
            f"Invalid time format: '{time_str}'.",
            suggestion="Use 24-hour HH:MM format, e.g. --time 07:30",
        )
    hour_str, minute_str = parts
    if not (hour_str.isdigit() and minute_str.isdigit()):
        raise ValidationError(
            f"Invalid time format: '{time_str}'.",
            suggestion="Use 24-hour HH:MM format, e.g. --time 07:30",
        )
    hour, minute = int(hour_str), int(minute_str)
    if not (0 <= hour <= 23) or not (0 <= minute <= 59):
        raise ValidationError(
            f"Time out of range: '{time_str}'.",
            suggestion="Hour must be 00-23 and minute must be 00-59, e.g. --time 23:45",
        )
    return hour, minute


def parse_days_str(days_str: str) -> list[str]:
    """Parse and validate a comma separated days string, 'daily', or 'once'."""
    days_str = days_str.strip().lower()

    if days_str == "once":
        return ["once"]
    if days_str == "daily":
        return list(VALID_DAYS)

    raw_days = [d.strip() for d in days_str.split(",") if d.strip()]
    if not raw_days:
        raise ValidationError(
            "No days provided.",
            suggestion=(
                "Use --days daily, --days once, or a comma separated list "
                "like --days mon,wed,fri"
            ),
        )

    days = []
    invalid = []
    for d in raw_days:
        if d in VALID_DAYS:
            if d not in days:
                days.append(d)
        else:
            invalid.append(d)

    if invalid:
        raise ValidationError(
            f"Unrecognized day value(s): {', '.join(invalid)}.",
            suggestion=(
                "Valid days are: mon, tue, wed, thu, fri, sat, sun "
                "(or use --days daily / --days once)"
            ),
        )

    days.sort(key=lambda d: DAY_INDEX[d])
    return days


@dataclass
class Alarm:
    time: str  # "HH:MM"
    days: list[str]  # ["mon", "tue", ...] or ["once"]
    label: str = "Alarm"
    enabled: bool = True
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    snooze_minutes: Optional[int] = None  # None = use global default
    ring_duration_seconds: Optional[int] = None  # None = use global default
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    last_rung_on: Optional[str] = None  # ISO date string, prevents double-ring same day
    skip_date: Optional[str] = None  # ISO date string to skip just once

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Alarm":
        return Alarm(
            id=data["id"],
            time=data["time"],
            days=data["days"],
            label=data.get("label", "Alarm"),
            enabled=data.get("enabled", True),
            snooze_minutes=data.get("snooze_minutes"),
            ring_duration_seconds=data.get("ring_duration_seconds"),
            created_at=data.get("created_at", datetime.now().isoformat(timespec="seconds")),
            last_rung_on=data.get("last_rung_on"),
            skip_date=data.get("skip_date"),
        )

    def days_display(self) -> str:
        if self.days == ["once"]:
            return "once"
        if self.days == list(VALID_DAYS):
            return "daily"
        return ",".join(self.days)
