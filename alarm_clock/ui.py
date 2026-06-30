"""Terminal color and formatting helpers.

Uses raw ANSI escape codes only - no third party dependency - since macOS
Terminal / iTerm2 support ANSI natively. Colors are disabled automatically
when output is not a real terminal (e.g. piped to a file).
"""

import sys


def _supports_color() -> bool:
    return sys.stdout.isatty()


class Colors:
    enabled = _supports_color()

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    BG_RED = "\033[41m"


def _wrap(code: str, text: str) -> str:
    if not Colors.enabled:
        return text
    return f"{code}{text}{Colors.RESET}"


def bold(text: str) -> str:
    return _wrap(Colors.BOLD, text)


def dim(text: str) -> str:
    return _wrap(Colors.DIM, text)


def red(text: str) -> str:
    return _wrap(Colors.RED, text)


def green(text: str) -> str:
    return _wrap(Colors.GREEN, text)


def yellow(text: str) -> str:
    return _wrap(Colors.YELLOW, text)


def blue(text: str) -> str:
    return _wrap(Colors.BLUE, text)


def cyan(text: str) -> str:
    return _wrap(Colors.CYAN, text)


def magenta(text: str) -> str:
    return _wrap(Colors.MAGENTA, text)


def success(text: str) -> None:
    print(f"{green('✓')} {text}")


def info(text: str) -> None:
    print(f"{cyan('i')} {text}")


def warn(text: str) -> None:
    print(f"{yellow('!')} {text}")


def error(text: str) -> None:
    print(f"{red('✗')} {text}", file=sys.stderr)


def hint(text: str) -> None:
    print(f"  {dim(text)}")


def rule(char: str = "─", width: int = 60) -> str:
    return char * width
