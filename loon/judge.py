"""Score an output file for Hash Code 2015, Final Round: Loon.

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
    altitudes: int
    radius: int
    balloon_count: int
    turns: int
    start: tuple[int, int]
    targets: list[tuple[int, int]]
    # winds[altitude - 1][row][column] is the vector (Δr, Δc) of the wind at that altitude over that cell.
    winds: list[list[list[tuple[int, int]]]]


@dataclasses.dataclass(frozen=True)
class Solution:
    # adjustments[turn][balloon] is -1, 0 or 1.
    adjustments: list[list[int]]


def read_input_line(lines: list[str], line_number: int, pattern: str, expected: str) -> list[int]:
    if line_number > len(lines):
        raise InvalidInput(f'line {line_number}: found the end of the file, expected {expected}')
    line = lines[line_number - 1]
    if re.fullmatch(pattern, line) is None:
        raise InvalidInput(
            f'line {line_number}: found {line[:100]!r}, expected {expected} separated by single spaces'
        )
    return [int(token) for token in line.split(' ')]


def check_input_range(value: int, line_number: int, name: str, low: int, high: int) -> None:
    if not low <= value <= high:
        raise InvalidInput(f'line {line_number}: found {name} = {value}, expected {low} to {high}')


def read_cell(lines: list[str], line_number: int, rows: int, columns: int, name: str) -> tuple[int, int]:
    row, column = read_input_line(lines, line_number, r'[0-9]+ [0-9]+', f'the row and column of {name}')
    check_input_range(row, line_number, 'the row', 0, rows - 1)
    check_input_range(column, line_number, 'the column', 0, columns - 1)
    return row, column


def read_wind_row(lines: list[str], line_number: int, columns: int) -> list[tuple[int, int]]:
    # Matches '0 1 -1 0' when columns is 2
    pattern = r'-?[0-9]{1,3}( -?[0-9]{1,3}){%d}' % (2 * columns - 1)
    values = read_input_line(lines, line_number, pattern, f'{2 * columns} wind components')
    for value in values:
        check_input_range(value, line_number, 'a wind component', -100, 100)
    return list(zip(values[0::2], values[1::2]))


def read_problem(input_file: str) -> Problem:
    with open(input_file, encoding='ascii', newline='') as file:
        lines = file.read().split('\n')

    rows, columns, altitudes = read_input_line(lines, 1, r'[0-9]+( [0-9]+){2}', 'R, C and A')
    check_input_range(rows, 1, 'R', 1, 1000)
    check_input_range(columns, 1, 'C', 1, 1000)
    check_input_range(altitudes, 1, 'A', 1, 1000)

    target_count, radius, balloon_count, turns = read_input_line(lines, 2, r'[0-9]+( [0-9]+){3}', 'L, V, B and T')
    # The statement caps L at 1000, but the official input has L = 2250. Targets are unique, so L <= R * C.
    check_input_range(target_count, 2, 'L', 1, rows * columns)
    check_input_range(radius, 2, 'V', 0, 100)
    check_input_range(balloon_count, 2, 'B', 1, 1000)
    check_input_range(turns, 2, 'T', 1, 1000)

    start = read_cell(lines, 3, rows, columns, 'the starting cell')

    targets = []
    listed_on_line = {}
    for line_number in range(4, target_count + 4):
        target = read_cell(lines, line_number, rows, columns, 'a target cell')
        if target in listed_on_line:
            raise InvalidInput(
                f'line {line_number}: target cell {list(target)} is listed a second time, first listed on line '
                f'{listed_on_line[target]}'
            )
        listed_on_line[target] = line_number
        targets.append(target)

    first_wind_line = target_count + 4
    winds = []
    for altitude in range(altitudes):
        first_line = first_wind_line + altitude * rows
        line_numbers = range(first_line, first_line + rows)
        winds.append([read_wind_row(lines, line_number, columns) for line_number in line_numbers])

    for line_number in range(first_wind_line + altitudes * rows, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidInput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    return Problem(rows, columns, altitudes, radius, balloon_count, turns, start, targets, winds)


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


def parse_int(token: str, line_number: int) -> int:
    if re.fullmatch(r'-?[0-9]+', token) is None:
        raise InvalidOutput(f'line {line_number}: found {token[:100]!r}, expected an integer')
    try:
        return int(token)
    except ValueError:
        # Since Python 3.10.7, int() refuses more than 4300 digits by default.
        raise InvalidOutput(
            f'line {line_number}: found an integer of {len(token)} characters, which is too long'
        ) from None


def read_solution(output_file: str, problem: Problem) -> Solution:
    lines = read_lines(output_file)
    expected = f'B = {problem.balloon_count} altitude adjustments'

    # The altitude of each balloon, 0 while it is on the ground.
    altitudes = [0] * problem.balloon_count
    adjustments = []
    for line_number in range(1, problem.turns + 1):
        if line_number > len(lines):
            raise InvalidOutput(f'line {line_number}: found the end of the file, expected {expected}')
        tokens = lines[line_number - 1].split()
        if len(tokens) != problem.balloon_count:
            raise InvalidOutput(f'line {line_number}: found {len(tokens)} tokens, expected {expected}')

        turn = [parse_int(token, line_number) for token in tokens]
        for balloon, adjustment in enumerate(turn):
            if adjustment not in (-1, 0, 1):
                raise InvalidOutput(
                    f'line {line_number}: found {adjustment} for balloon {balloon}, expected -1, 0 or 1'
                )
            if altitudes[balloon] == 0 and adjustment == -1:
                raise InvalidOutput(
                    f'line {line_number}: balloon {balloon} is on the ground, expected 0 to stay or 1 to launch'
                )
            # A launched balloon stays between altitudes 1 and A, even after it is lost.
            altitude = altitudes[balloon] + adjustment
            if altitudes[balloon] > 0 and not 1 <= altitude <= problem.altitudes:
                raise InvalidOutput(
                    f'line {line_number}: balloon {balloon} would reach altitude {altitude}, '
                    f'expected 1 to A = {problem.altitudes}'
                )
            altitudes[balloon] = altitude
        adjustments.append(turn)

    for line_number in range(problem.turns + 1, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidOutput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    return Solution(adjustments)


def column_distance(column: int, other_column: int, columns: int) -> int:
    distance = abs(column - other_column)
    return min(distance, columns - distance)


def covered_targets(
    problem: Problem,
    target_columns_by_row: list[list[int]],
    row: int,
    column: int,
) -> list[tuple[int, int]]:
    """Return the target cells that a balloon over [row, column] covers."""
    radius = problem.radius
    covered = []
    for target_row in range(max(0, row - radius), min(problem.rows, row + radius + 1)):
        for target_column in target_columns_by_row[target_row]:
            distance = column_distance(column, target_column, problem.columns)
            if (row - target_row) ** 2 + distance ** 2 <= radius ** 2:
                covered.append((target_row, target_column))
    return covered


def score(problem: Problem, solution: Solution) -> int:
    target_columns_by_row = [[] for _ in range(problem.rows)]
    for row, column in problem.targets:
        target_columns_by_row[row].append(column)
    coverage_by_cell = {}

    altitudes = [0] * problem.balloon_count
    # The cell of each balloon, or None once the wind has carried it off the grid.
    cells = [problem.start] * problem.balloon_count
    points = 0
    for turn in solution.adjustments:
        for balloon, adjustment in enumerate(turn):
            altitudes[balloon] += adjustment
            if altitudes[balloon] == 0 or cells[balloon] is None:
                continue
            row, column = cells[balloon]
            row_shift, column_shift = problem.winds[altitudes[balloon] - 1][row][column]
            if 0 <= row + row_shift < problem.rows:
                cells[balloon] = (row + row_shift, (column + column_shift) % problem.columns)
            else:
                cells[balloon] = None

        flying = {cell for cell, altitude in zip(cells, altitudes) if altitude > 0 and cell is not None}
        covered = set()
        for cell in flying:
            if cell not in coverage_by_cell:
                coverage_by_cell[cell] = covered_targets(problem, target_columns_by_row, *cell)
            covered.update(coverage_by_cell[cell])
        points += len(covered)
    return points


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
