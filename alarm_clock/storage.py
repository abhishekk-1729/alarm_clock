"""Persistence layer for alarms. Uses atomic writes (write temp + rename)
so a crash mid-write never corrupts the alarms file.
"""

from __future__ import annotations

import json
from typing import Optional

from alarm_clock.errors import StorageError, AlarmNotFoundError
from alarm_clock.logging_setup import get_logger
from alarm_clock.models import Alarm
from alarm_clock.paths import ALARMS_FILE, ensure_app_dir

logger = get_logger()


def load_alarms() -> list[Alarm]:
    ensure_app_dir()
    if not ALARMS_FILE.exists():
        return []
    try:
        with open(ALARMS_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return [Alarm.from_dict(item) for item in raw]
    except (json.JSONDecodeError, OSError, KeyError) as exc:
        logger.error("Failed to load alarms file: %s", exc)
        raise StorageError(
            "Could not read your saved alarms.",
            suggestion=f"The alarms file may be corrupted: {ALARMS_FILE}",
        ) from exc


def save_alarms(alarms: list[Alarm]) -> None:
    ensure_app_dir()
    tmp_path = ALARMS_FILE.with_suffix(".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump([a.to_dict() for a in alarms], f, indent=2)
        tmp_path.replace(ALARMS_FILE)
    except OSError as exc:
        logger.error("Failed to save alarms file: %s", exc)
        raise StorageError(
            "Could not save your alarms.",
            suggestion="Check that you have write permission to your home directory.",
        ) from exc


def get_alarm(alarms: list[Alarm], alarm_id: str) -> Alarm:
    for alarm in alarms:
        if alarm.id == alarm_id:
            return alarm
    raise AlarmNotFoundError(
        f"No alarm found with id '{alarm_id}'.",
        suggestion="Run 'alarm list' to see valid alarm ids.",
    )


def find_alarm_loose(alarms: list[Alarm], alarm_id: str) -> Optional[Alarm]:
    """Find an alarm allowing a unique prefix match, for convenience."""
    matches = [a for a in alarms if a.id.startswith(alarm_id)]
    if len(matches) == 1:
        return matches[0]
    return None
