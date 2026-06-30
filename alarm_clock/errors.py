"""Custom exceptions used throughout the app.

These are caught at the CLI boundary and turned into clean, colored,
user-facing error messages. They should never surface as raw tracebacks.
"""


class AlarmClockError(Exception):
    """Base class for all expected, user-facing errors.

    Attributes:
        message: Short human readable description of what went wrong.
        suggestion: Optional next-step text shown to the user.
    """

    def __init__(self, message: str, suggestion: str = ""):
        super().__init__(message)
        self.message = message
        self.suggestion = suggestion


class ValidationError(AlarmClockError):
    """Raised when user-provided input fails validation."""


class AlarmNotFoundError(AlarmClockError):
    """Raised when an alarm id does not exist."""


class StorageError(AlarmClockError):
    """Raised when alarm/config state cannot be read or written."""
