---
paths:
  - "**/*.py"
---

# Python Style

These rules apply to every `.py` file.

## Runtime

Judges run with `python3` on Python 3.10 or newer, with nothing installed. Import only the standard library.

## Style

No tool checks this repository, so these rules are kept by hand:

- Lines wrap at 120 characters.
- Strings use single quotes. Docstrings use `"""`.
- Imports are sorted in two groups: the standard library, then the problem's own `judge` module in tests. No unused
  imports.
- Never import `typing.Any`, `pathlib` or `sys`.
- Every function annotates all its parameters and its return type.

## Less is more

Write the minimum code that solves the problem. No speculative abstractions, no configuration hook nothing asks for, no
layer added because a second judge might use it.

## Functions

Wrap code in a helper only when it holds something non-obvious, such as a formula, a regex or a multi-step
transformation. A one-liner that reads as what it does stays where it is.

```python
# WRONG: too simple to warrant a function
def get_example_path(folder: str) -> str:
    return os.path.join(folder, 'example.in')


# RIGHT: wrap the strict integer check, because int() alone accepts too much
def parse_int(token: str, line_number: int) -> int:
    if re.fullmatch(r'-?[0-9]+', token) is None:
        raise InvalidOutput(f'line {line_number}: expected an integer, found {token!r}')
    return int(token)
```

## Type hints

Annotate function parameters and return types, not variables.

Use the lowercase built-in generics, such as `list`, `dict` and `tuple`, not their `typing` equivalents, and `X | Y` for
unions.

```python
def read_rides(lines: list[str], ride_count: int) -> list[tuple[int, int]]: ...
```

Never `Any`. It switches off type checking for everything it touches. The ban has no exemptions.

## Data

Hold parsed problems and solutions in `@dataclasses.dataclass(frozen=True)` classes, not in loose tuples or dicts.

## Paths

`os.path`, not `pathlib`. A single `Path` spreads through every signature it meets.

```python
# WRONG
from pathlib import Path

example = Path(folder) / 'example.in'

# RIGHT
import os

example = os.path.join(folder, 'example.in')
```

## Exit

Do not import `sys`. A judge ends a failed run with `raise SystemExit(message)`, which prints to stderr and exits with
status 1.

## Shebang

Never write a shebang line (`#!/usr/bin/env python3`). Run Python files with `python3 <file>`.

## Spacing

Blank lines group related statements: the work that reads, the work that checks, the work that counts.

A signature that does not fit on one line takes one argument per line. End the last argument with a trailing comma, so a
formatter keeps one argument per line instead of packing them onto one.

```python
def check_delivery(
    order: Order,
    drone: Drone,
    turn: int,
    line_number: int,
) -> None: ...
```

## Zen of Python

- Beautiful is better than ugly.
- Simple is better than complex.
- Flat is better than nested.
- Readability counts.
- Errors should never pass silently.
- There should be one obvious way to do it.
- If the implementation is hard to explain, it's a bad idea.
