"""Global configuration: defaults for ring duration, timeout, snooze."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict

from alarm_clock.errors import StorageError
from alarm_clock.paths import CONFIG_FILE, ensure_app_dir

DEFAULT_RING_DURATION_SECONDS = 300  # 5 minutes max ringing
DEFAULT_TIMEOUT_SECONDS = 300  # alias of ring duration: stop if unattended
DEFAULT_SNOOZE_MINUTES = 5
POLL_INTERVAL_SECONDS = 2


@dataclass
class Config:
    ring_duration_seconds: int = DEFAULT_RING_DURATION_SECONDS
    snooze_minutes: int = DEFAULT_SNOOZE_MINUTES

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Config":
        return Config(
            ring_duration_seconds=data.get(
                "ring_duration_seconds", DEFAULT_RING_DURATION_SECONDS
            ),
            snooze_minutes=data.get("snooze_minutes", DEFAULT_SNOOZE_MINUTES),
        )


def load_config() -> Config:
    ensure_app_dir()
    if not CONFIG_FILE.exists():
        return Config()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Config.from_dict(data)
    except (json.JSONDecodeError, OSError) as exc:
        raise StorageError(
            "Could not read configuration file.",
            suggestion=f"Check or remove {CONFIG_FILE} and try again.",
        ) from exc


def save_config(config: Config) -> None:
    ensure_app_dir()
    tmp_path = CONFIG_FILE.with_suffix(".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, indent=2)
        tmp_path.replace(CONFIG_FILE)
    except OSError as exc:
        raise StorageError(
            "Could not save configuration file.",
            suggestion="Check that you have write permission to your home directory.",
        ) from exc
