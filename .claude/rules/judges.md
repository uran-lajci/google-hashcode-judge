---
paths:
  - "**/judge.py"
  - "**/test_judge.py"
---

# Judges

Every Hash Code problem gets one judge: a single file that reads an input file and an output file, checks the output
against every rule in the problem statement, and prints the score. All judges follow the same template, so a reader who
knows one knows them all. Everything else in the file follows `python.md`.

## Layout

One folder per problem, named after the problem title in lowercase with underscores, such as `book_scanning`,
`self_driving_rides` or `optimize_a_data_center`. The name has no year or round; the module docstring gives those.

```
book_scanning/
  judge.py          # the judge, standalone
  test_judge.py     # reproduces the example score from the statement
  example.in        # the example input from the statement
  example.out       # the example output from the statement
```

- A judge is standalone. It imports only the standard library, never another judge or a shared helper module. If two
  judges need the same reader, copy it.
- Keep `example.in` and `example.out` byte for byte as the statement prints them.

## Command line

Every judge takes the same two flags and prints one line: the score.

```
python3 book_scanning/judge.py -i example.in -o example.out
```

## Structure

Imports, data classes, the reader for the input file, the reader for the output file, the scoring function, `main`, then
the `__main__` block. Nothing runs at import time.

```python
"""Score an output file for Hash Code 2020, Qualification Round: Book scanning.

python3 judge.py -i example.in -o example.out
"""

import argparse
import dataclasses


class InvalidOutput(Exception):
    """The output file breaks a rule of the problem statement."""


@dataclasses.dataclass(frozen=True)
class Problem: ...


@dataclasses.dataclass(frozen=True)
class Solution: ...


def read_problem(input_file: str) -> Problem: ...


def read_solution(output_file: str, problem: Problem) -> Solution: ...


def score(problem: Problem, solution: Solution) -> int: ...


def main(input_file: str, output_file: str) -> int:
    problem = read_problem(input_file)
    solution = read_solution(output_file, problem)
    return score(problem, solution)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-i', '--input_file', required=True)
    parser.add_argument('-o', '--output_file', required=True)

    args = parser.parse_args()
    try:
        print(main(args.input_file, args.output_file))
    except InvalidOutput as error:
        raise SystemExit(f'Invalid output: {error}')
```

- The module docstring names the year, the round and the problem, and gives the exact run command. The parser uses it
  as `description=__doc__`.
- `main` returns the score, so tests call it directly. Only the `__main__` block prints.
- `raise SystemExit(message)` prints the message to stderr and exits with status 1. A valid output exits with 0.
- `read_solution` checks every rule. `score` assumes a valid solution and only counts points.

## Validation

The judge must reject every output the official judge would reject. A wrong score is worse than no score.

- Check every constraint the statement gives: counts, ranges, IDs that exist, items used at most once, capacities,
  deadlines, ordering. Go through the statement section by section and check that each rule has a check.
- Parse integers strictly. `int()` also accepts `'+5'`, `' 5'`, `'1_000'` and non-ASCII digits, so check the token
  against `-?[0-9]+` first.
- Split each line on whitespace. Reject a line with too few or too many tokens. Allow blank lines at the end of the
  file, and reject anything else after the last expected line.
- Read the input file with the same strict reader, but treat a bad input file as a bug in the data, not in the output.

An error message says where the problem is, what was found and what was expected, in that order:

```
line 4: library 7 does not exist, expected an ID from 0 to 5
line 9: book 3 is scanned a second time, first scanned on line 6
```

- Line numbers start at 1 and count lines of the output file.
- Stop at the first error. Do not collect a list.

## Score

- Compute the score with `int`. If the statement uses fractions or rounding, compute with `fractions.Fraction` and round
  once, at the end, exactly as the statement says. Never use `float`.
- The score of the example output must equal the score printed in the statement.

## Tests

`test_judge.py` uses `unittest`. It holds at least one test that runs `main` on `example.in` and `example.out` and
checks the score from the statement. Add a test for an invalid output when a rule is easy to get wrong.

```python
import os
import unittest

import judge

FOLDER = os.path.dirname(__file__)


class TestJudge(unittest.TestCase):
    def test_example_score_matches_statement(self) -> None:
        score = judge.main(os.path.join(FOLDER, 'example.in'), os.path.join(FOLDER, 'example.out'))
        self.assertEqual(score, 16)
```

Run the tests of one problem from its folder with `python3 -m unittest`.
