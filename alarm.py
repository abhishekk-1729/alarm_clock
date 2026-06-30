#!/usr/bin/env python3
"""Entry point script for the alarm clock CLI.

Run directly:    python3 alarm.py <command> ...
Or make executable and run:   ./alarm.py <command> ...
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from alarm_clock.cli import main

if __name__ == "__main__":
    sys.exit(main())
