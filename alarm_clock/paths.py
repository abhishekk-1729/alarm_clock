"""Central place for filesystem paths used by the app."""

from pathlib import Path

APP_DIR = Path.home() / ".alarm_clock"
ALARMS_FILE = APP_DIR / "alarms.json"
CONFIG_FILE = APP_DIR / "config.json"
LOG_FILE = APP_DIR / "alarm.log"


def ensure_app_dir() -> None:
    """Create the application directory if it does not exist yet."""
    APP_DIR.mkdir(parents=True, exist_ok=True)
