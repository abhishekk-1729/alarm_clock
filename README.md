# Alarm Clock

A terminal based alarm clock with recurring schedules, snooze/skip/dismiss
responses, and a clean colored CLI. Built with zero third-party
dependencies — only the Python standard library.

## Features

- Add, list, update, delete, enable, and disable alarms
- Recurring alarms (specific weekdays, daily, or one-off)
- When an alarm rings you can snooze (default or custom minutes), skip for
  today, or dismiss it permanently
- Configurable ring duration with a sensible default (5 minutes)
- A dry-run `test` command to ring an alarm immediately without waiting
- Alarms that fire at the same moment are grouped into a single banner
- Persisted state across runs in `~/.alarm_clock/`
- Production style rotating log file, kept separate from the clean
  user-facing terminal output
- No raw Python errors are ever shown to the user — all errors are caught
  and shown with a clear message and next steps

## Requirements

- Python 3.9 or later
- macOS (this build targets macOS Terminal/iTerm2; it relies on the
  terminal bell character and ANSI colors, which both work natively there)

No `pip install` is required to run the tool.

## Installation

You can run it directly with Python, or install it so the `alarm` command
is available anywhere on your system.

### Option A: Run directly, no installation

```bash
cd alarm_clock
python3 alarm.py --help
```

Every example below assumes you've installed the `alarm` command (Option
B). If you're running it directly, just replace `alarm` with
`python3 alarm.py` in any command.

### Option B: Install as the `alarm` command (recommended)

```bash
cd alarm_clock
pip install --user -e .
```

This installs an `alarm` command on your PATH using the standard library
only (`setuptools` is the one tool needed to install it, not to run it).
Verify it worked:

```bash
alarm --help
```

If `alarm: command not found` appears after installing, your Python user
scripts directory isn't on your PATH. Add it, for example:

```bash
export PATH="$HOME/Library/Python/3.9/bin:$PATH"
```

(Adjust the Python version number to match yours, or run
`python3 -m site --user-base` to find the correct directory.)

## Quick start

```bash
# Create a recurring weekday alarm
alarm add --time 07:30 --days mon,tue,wed,thu,fri --label "Wake up"

# Create a one-off alarm
alarm add --time 09:00 --days once --label "Dentist reminder"

# See all your alarms
alarm list

# Start watching for alarms — keep this terminal window open
alarm watch
```

While `alarm watch` is running, due alarms will display a banner, ring
the terminal bell, and wait for your response.

## Command reference

### `alarm add`

Create a new alarm.

```bash
alarm add --time 07:30 --days mon,tue,wed,thu,fri --label "Wake up"
alarm add --time 21:00 --days daily --label "Wind down"
alarm add --time 09:00 --days once --label "Dentist reminder"
alarm add --time 06:00 --days mon --label "Gym" --snooze-minutes 10 --ring-duration 120
```

Flags:
- `--time` (required) — 24-hour `HH:MM`, e.g. `07:30`
- `--days` (required) — comma separated weekdays (`mon,tue,wed,thu,fri,sat,sun`), or `daily`, or `once`
- `--label` — short description shown when the alarm rings and in `alarm list`
- `--snooze-minutes` — override the global default snooze length for this alarm
- `--ring-duration` — override the global default ring duration (seconds) for this alarm

If the time you set has already passed today, the alarm is created
normally but the CLI tells you explicitly that it will first ring
tomorrow (or on its next matching weekday).

### `alarm list`

```bash
alarm list
```

Shows every alarm with its id, enabled/disabled status, time, days, and
label.

### `alarm update`

Update one or more fields of an existing alarm.

```bash
alarm update a1b2c3d4 --time 08:00
alarm update a1b2c3d4 --days mon,wed,fri
alarm update a1b2c3d4 --label "New label"
alarm update a1b2c3d4 --snooze-minutes 10 --ring-duration 180
```

The alarm id can be the full id from `alarm list`, or any unique prefix
of it.

### `alarm delete`

```bash
alarm delete a1b2c3d4
```

Permanently removes an alarm.

### `alarm enable` / `alarm disable`

```bash
alarm enable a1b2c3d4
alarm disable a1b2c3d4
```

Disabling keeps the alarm saved (so you can re-enable it later) but it
will not ring while disabled.

### `alarm watch`

```bash
alarm watch
```

Starts the foreground watcher. This needs to be running in an open
terminal window for alarms to actually ring — there is no background
daemon. Press `Ctrl+C` to stop watching at any time; your alarms remain
saved and will resume working the next time you run `alarm watch`.

When an alarm rings, respond with:
- `s` — snooze for the default length
- `s<N>` — snooze for `N` minutes, e.g. `s10`
- `k` — skip just today; the alarm will ring again on its next scheduled day
- `d` — dismiss forever; this disables the alarm

If you don't respond within the configured ring duration (default 5
minutes), the alarm stops automatically and is logged as unattended; it
remains armed for its next scheduled occurrence.

Alarms scheduled for the exact same moment are grouped into a single
banner, and your response applies to all of them at once.

### `alarm test`

```bash
alarm test a1b2c3d4
```

Rings an alarm immediately as a dry run, regardless of its schedule. This
is useful to confirm your terminal bell and banner display work as
expected, and to preview what the alarm will look like. It does not
affect the alarm's real schedule.

### `alarm config`

View or change global defaults that apply to all alarms unless a given
alarm has its own override.

```bash
alarm config
alarm config --ring-duration 180
alarm config --snooze-minutes 10
```

### Help

Every command has its own detailed help with examples:

```bash
alarm --help
alarm add --help
alarm update --help
alarm watch --help
```

## How state is stored

Everything is kept in `~/.alarm_clock/`:

- `alarms.json` — your alarms
- `config.json` — global defaults
- `alarm.log` — rotating log file with technical/diagnostic detail (not
  shown in the terminal; useful if something needs investigating)

Writes are atomic (written to a temp file, then renamed), so an
interrupted write won't corrupt your saved alarms.

## Notes on behavior

- A one-off (`--days once`) alarm is automatically disabled after it has
  rung (or gone unattended, or been skipped) once, since it has no future
  occurrence.
- Recurring alarms only ring once per matching day, even if `alarm watch`
  is running continuously.
- Typing an unknown command shows a suggestion for the closest valid
  command, and invalid input always comes with a specific next step
  (usually pointing you to the relevant `--help`).

## Uninstalling

```bash
pip uninstall alarm-clock
rm -rf ~/.alarm_clock
```
# alarm_clock
