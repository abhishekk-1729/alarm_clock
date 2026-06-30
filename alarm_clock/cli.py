"""Main CLI entry point.

Wires up argparse subcommands and ensures that no internal exception ever
reaches the user as a raw Python traceback - all expected errors are
caught and shown as clean, actionable messages.
"""

from __future__ import annotations

import argparse
import difflib
import sys

from alarm_clock import ui, commands
from alarm_clock.errors import AlarmClockError
from alarm_clock.logging_setup import get_logger

logger = get_logger()

KNOWN_COMMANDS = [
    "add", "list", "delete", "update", "enable", "disable",
    "watch", "test", "config",
]


EPILOG = """
examples:
  alarm add --time 07:30 --days mon,tue,wed,thu,fri --label "Wake up"
  alarm add --time 09:00 --days once --label "Dentist reminder"
  alarm list
  alarm update a1b2c3d4 --time 08:00
  alarm disable a1b2c3d4
  alarm delete a1b2c3d4
  alarm watch
  alarm test a1b2c3d4
  alarm config --ring-duration 180 --snooze-minutes 10

Run 'alarm <command> --help' for details and examples on any command.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="alarm",
        description="A terminal based alarm clock with recurring schedules.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    # add
    p_add = subparsers.add_parser(
        "add",
        help="Create a new alarm",
        description="Create a new alarm.",
        epilog=(
            "examples:\n"
            "  alarm add --time 07:30 --days mon,tue,wed,thu,fri --label \"Wake up\"\n"
            "  alarm add --time 21:00 --days daily --label \"Wind down\"\n"
            "  alarm add --time 09:00 --days once --label \"Dentist reminder\"\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_add.add_argument("--time", required=True, help="Time in 24-hour HH:MM format, e.g. 07:30")
    p_add.add_argument(
        "--days", required=True,
        help="Comma separated days (mon,tue,...), 'daily', or 'once'",
    )
    p_add.add_argument("--label", help="A short description for this alarm")
    p_add.add_argument(
        "--snooze-minutes", type=int, dest="snooze_minutes",
        help="Override the default snooze length for this alarm",
    )
    p_add.add_argument(
        "--ring-duration", type=int, dest="ring_duration",
        help="Override the default ring duration (seconds) for this alarm",
    )
    p_add.set_defaults(func=commands.cmd_add)

    # list
    p_list = subparsers.add_parser(
        "list",
        help="List all alarms",
        description="List all alarms with their schedule and status.",
        epilog="examples:\n  alarm list\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_list.set_defaults(func=commands.cmd_list)

    # delete
    p_delete = subparsers.add_parser(
        "delete",
        help="Delete an alarm",
        description="Permanently delete an alarm.",
        epilog="examples:\n  alarm delete a1b2c3d4\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_delete.add_argument("id", help="The alarm id (see 'alarm list')")
    p_delete.set_defaults(func=commands.cmd_delete)

    # update
    p_update = subparsers.add_parser(
        "update",
        help="Update an existing alarm",
        description="Update one or more fields of an existing alarm.",
        epilog=(
            "examples:\n"
            "  alarm update a1b2c3d4 --time 08:00\n"
            "  alarm update a1b2c3d4 --days mon,wed,fri\n"
            "  alarm update a1b2c3d4 --label \"New label\"\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_update.add_argument("id", help="The alarm id (see 'alarm list')")
    p_update.add_argument("--time", help="New time in 24-hour HH:MM format")
    p_update.add_argument("--days", help="New days: comma separated, 'daily', or 'once'")
    p_update.add_argument("--label", help="New label")
    p_update.add_argument("--snooze-minutes", type=int, dest="snooze_minutes", help="New snooze length override")
    p_update.add_argument("--ring-duration", type=int, dest="ring_duration", help="New ring duration override")
    p_update.set_defaults(func=commands.cmd_update)

    # enable / disable
    p_enable = subparsers.add_parser(
        "enable",
        help="Enable an alarm",
        description="Enable a previously disabled alarm.",
        epilog="examples:\n  alarm enable a1b2c3d4\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_enable.add_argument("id", help="The alarm id (see 'alarm list')")
    p_enable.set_defaults(func=commands.cmd_enable)

    p_disable = subparsers.add_parser(
        "disable",
        help="Disable an alarm without deleting it",
        description="Disable an alarm. It stays saved but will not ring.",
        epilog="examples:\n  alarm disable a1b2c3d4\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_disable.add_argument("id", help="The alarm id (see 'alarm list')")
    p_disable.set_defaults(func=commands.cmd_disable)

    # watch
    p_watch = subparsers.add_parser(
        "watch",
        help="Start watching for due alarms (keep this terminal open)",
        description=(
            "Start the foreground watcher. This must be running in an open "
            "terminal window for alarms to actually ring."
        ),
        epilog="examples:\n  alarm watch\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_watch.set_defaults(func=commands.cmd_watch)

    # test
    p_test = subparsers.add_parser(
        "test",
        help="Ring an alarm immediately as a dry run",
        description="Ring an alarm right now, regardless of its schedule. Does not affect its real schedule.",
        epilog="examples:\n  alarm test a1b2c3d4\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_test.add_argument("id", help="The alarm id (see 'alarm list')")
    p_test.set_defaults(func=commands.cmd_test)

    # config
    p_config = subparsers.add_parser(
        "config",
        help="View or change global default settings",
        description="View or change global defaults for ring duration and snooze length.",
        epilog=(
            "examples:\n"
            "  alarm config\n"
            "  alarm config --ring-duration 180\n"
            "  alarm config --snooze-minutes 10\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_config.add_argument("--ring-duration", type=int, dest="ring_duration", help="Default ring duration in seconds")
    p_config.add_argument("--snooze-minutes", type=int, dest="snooze_minutes", help="Default snooze length in minutes")
    p_config.set_defaults(func=commands.cmd_config_show)

    return parser


def _suggest_command(unknown: str) -> str | None:
    matches = difflib.get_close_matches(unknown, KNOWN_COMMANDS, n=1, cutoff=0.5)
    return matches[0] if matches else None


def main(argv=None) -> int:
    parser = build_parser()
    argv = argv if argv is not None else sys.argv[1:]

    if not argv:
        parser.print_help()
        return 0

    # Intercept unknown top-level commands before argparse's generic error,
    # so we can offer a "did you mean" suggestion instead of a raw error.
    if argv[0] not in KNOWN_COMMANDS and not argv[0].startswith("-"):
        suggestion = _suggest_command(argv[0])
        ui.error(f"Unknown command: '{argv[0]}'")
        if suggestion:
            ui.hint(f"Did you mean: alarm {suggestion}")
        ui.hint("Run 'alarm --help' to see all available commands.")
        return 2

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse already printed its own usage/help text; just propagate
        # its exit code without letting a traceback through.
        return exc.code or 0

    if not hasattr(args, "func"):
        parser.print_help()
        return 0

    try:
        args.func(args)
        return 0
    except AlarmClockError as exc:
        ui.error(exc.message)
        if exc.suggestion:
            ui.hint(exc.suggestion)
        logger.warning("Handled user-facing error: %s", exc.message)
        return 1
    except KeyboardInterrupt:
        print()
        ui.info("Cancelled.")
        return 130
    except Exception as exc:  # noqa: BLE001 - last resort guard, never show a traceback
        logger.exception("Unexpected internal error")
        ui.error("Something unexpected went wrong.")
        ui.hint("This has been logged. Run 'alarm --help' to check command usage.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
