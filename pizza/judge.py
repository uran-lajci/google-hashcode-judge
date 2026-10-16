"""Score an output file for Hash Code 2017, Practice Round: Pizza.

python3 judge.py -i example.in -o example.out
"""

import argparse
import dataclasses
import re


class InvalidInput(Exception):
    """The input file breaks the format of the problem statement, which is a bug in the data set."""


class InvalidOutput(Exception):
    """The output file breaks a rule of the problem statement."""


@dataclasses.dataclass(frozen=True)
class Problem:
    rows: int
    columns: int
    min_each_ingredient: int
    max_cells: int
    pizza: list[str]


@dataclasses.dataclass(frozen=True)
class Slice:
    top: int
    left: int
    bottom: int
    right: int

    @property
    def cells(self) -> int:
        return (self.bottom - self.top + 1) * (self.right - self.left + 1)


@dataclasses.dataclass(frozen=True)
class Solution:
    slices: list[Slice]


def read_problem(input_file: str) -> Problem:
    with open(input_file, encoding='ascii', newline='') as file:
        lines = file.read().split('\n')

    header = re.fullmatch(r'([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)', lines[0])
    if header is None:
        raise InvalidInput(f'line 1: found {lines[0]!r}, expected R C L H separated by single spaces')
    rows, columns, min_each_ingredient, max_cells = (int(number) for number in header.groups())
    if not all(1 <= number <= 1000 for number in (rows, columns, min_each_ingredient, max_cells)):
        raise InvalidInput(f'line 1: found {lines[0]!r}, expected R, C, L and H from 1 to 1000')

    if lines[-1] != '':
        raise InvalidInput(f'line {len(lines)}: found the end of the file, expected a newline')
    pizza = lines[1:-1]
    if len(pizza) != rows:
        raise InvalidInput(f'found {len(pizza)} rows of pizza after line 1, expected {rows}')
    for line_number, row in enumerate(pizza, start=2):
        if len(row) != columns or re.fullmatch('[MT]*', row) is None:
            raise InvalidInput(f'line {line_number}: found {row!r}, expected {columns} cells of M or T')

    return Problem(rows, columns, min_each_ingredient, max_cells, pizza)


def read_lines(output_file: str) -> list[str]:
    with open(output_file, 'rb') as file:
        data = file.read()
    try:
        text = data.decode('ascii')
    except UnicodeDecodeError as error:
        line_number = data.count(b'\n', 0, error.start) + 1
        raise InvalidOutput(
            f'line {line_number}: found the byte {data[error.start]:#04x}, expected ASCII text'
        ) from None

    lines = text.split('\n')
    # The newline at the end of the last line leaves an empty string after it, which is not a line.
    if lines[-1] == '':
        lines.pop()
    return lines


def read_line(lines: list[str], line_number: int, token_count: int, expected: str) -> list[str]:
    if line_number > len(lines):
        raise InvalidOutput(f'line {line_number}: found the end of the file, expected {expected}')
    tokens = lines[line_number - 1].split()
    if len(tokens) != token_count:
        raise InvalidOutput(f'line {line_number}: found {len(tokens)} tokens, expected {expected}')
    return tokens


def parse_int(token: str, line_number: int) -> int:
    if re.fullmatch(r'-?[0-9]+', token) is None:
        raise InvalidOutput(f'line {line_number}: found {token!r}, expected an integer')
    try:
        return int(token)
    except ValueError:
        # Since Python 3.10.7, int() refuses more than 4300 digits by default.
        raise InvalidOutput(
            f'line {line_number}: found an integer of {len(token)} characters, which is too long'
        ) from None


def read_slice(lines: list[str], line_number: int, problem: Problem) -> Slice:
    """Read a slice as r1 c1 r2 c2, where each pair of rows and of columns may come in either order."""
    tokens = read_line(lines, line_number, 4, 'a slice as r1 c1 r2 c2')
    row_1, column_1, row_2, column_2 = (parse_int(token, line_number) for token in tokens)

    for row in (row_1, row_2):
        if not 0 <= row < problem.rows:
            raise InvalidOutput(
                f'line {line_number}: row {row} is outside the pizza, expected a row from 0 to {problem.rows - 1}'
            )
    for column in (column_1, column_2):
        if not 0 <= column < problem.columns:
            raise InvalidOutput(
                f'line {line_number}: column {column} is outside the pizza, '
                f'expected a column from 0 to {problem.columns - 1}'
            )

    return Slice(min(row_1, row_2), min(column_1, column_2), max(row_1, row_2), max(column_1, column_2))


def check_slice(pizza_slice: Slice, line_number: int, problem: Problem) -> None:
    if pizza_slice.cells > problem.max_cells:
        raise InvalidOutput(
            f'line {line_number}: the slice has {pizza_slice.cells} cells, expected at most {problem.max_cells}'
        )

    rows = [
        row[pizza_slice.left:pizza_slice.right + 1]
        for row in problem.pizza[pizza_slice.top:pizza_slice.bottom + 1]
    ]
    for ingredient, name in (('M', 'mushroom'), ('T', 'tomato')):
        count = sum(row.count(ingredient) for row in rows)
        if count < problem.min_each_ingredient:
            raise InvalidOutput(
                f'line {line_number}: the slice has {count} cells of {name}, '
                f'expected at least {problem.min_each_ingredient}'
            )


def cut(pizza_slice: Slice, line_number: int, cut_on_line: list[list[int]]) -> None:
    """Mark the cells of the slice in cut_on_line, after checking that no earlier slice holds them."""
    for row in range(pizza_slice.top, pizza_slice.bottom + 1):
        for column in range(pizza_slice.left, pizza_slice.right + 1):
            if cut_on_line[row][column]:
                raise InvalidOutput(
                    f'line {line_number}: cell [{row}, {column}] is already in the slice '
                    f'on line {cut_on_line[row][column]}'
                )
            cut_on_line[row][column] = line_number


def read_solution(output_file: str, problem: Problem) -> Solution:
    lines = read_lines(output_file)

    slice_count = parse_int(read_line(lines, 1, 1, 'the number of slices')[0], 1)
    max_slice_count = problem.rows * problem.columns
    if not 0 <= slice_count <= max_slice_count:
        raise InvalidOutput(f'line 1: found {slice_count} slices, expected 0 to {max_slice_count}')

    # The line of the slice that holds each cell, or 0 while no slice holds it.
    cut_on_line = [[0] * problem.columns for _ in range(problem.rows)]
    slices = []
    for line_number in range(2, slice_count + 2):
        pizza_slice = read_slice(lines, line_number, problem)
        check_slice(pizza_slice, line_number, problem)
        cut(pizza_slice, line_number, cut_on_line)
        slices.append(pizza_slice)

    for line_number in range(slice_count + 2, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidOutput(f'line {line_number}: found {lines[line_number - 1]!r}, expected the end of the file')

    return Solution(slices)


def score(problem: Problem, solution: Solution) -> int:
    return sum(pizza_slice.cells for pizza_slice in solution.slices)


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
