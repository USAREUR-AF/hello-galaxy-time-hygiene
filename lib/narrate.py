"""Terminal output helpers. No dependencies, colour only when a TTY is attached."""

from __future__ import annotations

import os
import sys

_TTY = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _c(code: str, s: str) -> str:
    return f"\033[{code}m{s}\033[0m" if _TTY else s


def bold(s: str) -> str:
    return _c("1", s)


def green(s: str) -> str:
    return _c("32", s)


def red(s: str) -> str:
    return _c("31", s)


def amber(s: str) -> str:
    return _c("33", s)


def dim(s: str) -> str:
    return _c("2", s)


def title(s: str) -> None:
    print()
    print(bold(s))
    print(dim("─" * min(len(s), 78)))


def step(n: int, s: str) -> None:
    print(f"\n{bold(f'{n}.')} {s}")


def note(s: str) -> None:
    print(dim(f"   {s}"))


def verdict(ok: bool, s: str) -> None:
    print(f"   {green('PASS') if ok else red('FAIL')}  {s}")
