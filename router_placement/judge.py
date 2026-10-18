"""Score an output file for Hash Code 2017, Final Round: Router placement.

python3 judge.py -i example.in -o example.out
"""

import argparse
import dataclasses
import re

WALL = '#'
TARGET = '.'
NEIGHBOUR_OFFSETS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
QUADRANTS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]


class InvalidInput(Exception):
    """The input file breaks the format of the problem statement, which is a bug in the data set."""


class InvalidOutput(Exception):
    """The output file breaks a rule of the problem statement."""


@dataclasses.dataclass(frozen=True)
class Problem:
    height: int
    width: int
    radius: int
    backbone_price: int
    router_price: int
    budget: int
    initial_backbone: tuple[int, int]
    grid: list[str]


@dataclasses.dataclass(frozen=True)
class Solution:
    backbone: list[tuple[int, int]]
    routers: list[tuple[int, int]]


def read_input_line(lines: list[str], line_number: int, pattern: str, expected: str) -> list[str]:
    if line_number > len(lines):
        raise InvalidInput(f'line {line_number}: found the end of the file, expected {expected}')
    line = lines[line_number - 1]
    if re.fullmatch(pattern, line) is None:
        raise InvalidInput(
            f'line {line_number}: found {line[:100]!r}, expected {expected} separated by single spaces'
        )
    return line.split(' ')


def check_input_range(value: int, line_number: int, name: str, low: int, high: int) -> None:
    if not low <= value <= high:
        raise InvalidInput(f'line {line_number}: found {name} = {value}, expected {low} to {high}')


def read_problem(input_file: str) -> Problem:
    with open(input_file, encoding='ascii', newline='') as file:
        lines = file.read().split('\n')

    tokens = read_input_line(lines, 1, r'[0-9]{1,4} [0-9]{1,4} [0-9]{1,2}', 'H, W and R')
    height, width, radius = (int(token) for token in tokens)
    check_input_range(height, 1, 'H', 1, 1000)
    check_input_range(width, 1, 'W', 1, 1000)
    check_input_range(radius, 1, 'R', 1, 10)

    tokens = read_input_line(lines, 2, r'[0-9]{1,3} [0-9]{1,3} [0-9]{1,10}', 'Pb, Pr and B')
    backbone_price, router_price, budget = (int(token) for token in tokens)
    check_input_range(backbone_price, 2, 'Pb', 1, 5)
    check_input_range(router_price, 2, 'Pr', 5, 100)
    check_input_range(budget, 2, 'B', 1, 10**9)

    tokens = read_input_line(lines, 3, r'[0-9]{1,4} [0-9]{1,4}', 'br and bc')
    initial_row, initial_column = (int(token) for token in tokens)
    check_input_range(initial_row, 3, 'br', 0, height - 1)
    check_input_range(initial_column, 3, 'bc', 0, width - 1)

    grid = []
    for line_number in range(4, height + 4):
        if line_number > len(lines):
            raise InvalidInput(f'line {line_number}: found the end of the file, expected a row of the grid')
        row = lines[line_number - 1]
        if re.fullmatch(f'[#.-]{{{width}}}', row) is None:
            raise InvalidInput(
                f'line {line_number}: found {row[:100]!r}, expected W = {width} characters, each #, . or -'
            )
        grid.append(row)

    for line_number in range(height + 4, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidInput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    return Problem(
        height,
        width,
        radius,
        backbone_price,
        router_price,
        budget,
        (initial_row, initial_column),
        grid,
    )


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


def read_number(lines: list[str], line_number: int, expected: str) -> int:
    """Read a line that holds a single integer."""
    if line_number > len(lines):
        raise InvalidOutput(f'line {line_number}: found the end of the file, expected {expected}')
    tokens = lines[line_number - 1].split()
    if len(tokens) != 1:
        raise InvalidOutput(f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected {expected}')
    return parse_int(tokens[0], line_number)


def read_cell(lines: list[str], line_number: int, problem: Problem, expected: str) -> tuple[int, int]:
    if line_number > len(lines):
        raise InvalidOutput(f'line {line_number}: found the end of the file, expected {expected}')
    tokens = lines[line_number - 1].split()
    if len(tokens) != 2:
        raise InvalidOutput(f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected {expected}')

    row, column = parse_int(tokens[0], line_number), parse_int(tokens[1], line_number)
    if not 0 <= row < problem.height:
        raise InvalidOutput(f'line {line_number}: found r = {row}, expected 0 to H - 1 = {problem.height - 1}')
    if not 0 <= column < problem.width:
        raise InvalidOutput(f'line {line_number}: found c = {column}, expected 0 to W - 1 = {problem.width - 1}')
    return row, column


def read_solution(output_file: str, problem: Problem) -> Solution:
    lines = read_lines(output_file)
    cell_count = problem.height * problem.width

    backbone_count = read_number(lines, 1, 'N, the number of cells connected to the backbone')
    if not 0 <= backbone_count < cell_count:
        raise InvalidOutput(f'line 1: found N = {backbone_count}, expected 0 to W * H - 1 = {cell_count - 1}')

    # The line that connects each cell to the backbone, or 0 for the initial cell.
    connected_on_line = {problem.initial_backbone: 0}
    backbone = []
    for line_number in range(2, backbone_count + 2):
        cell = read_cell(lines, line_number, problem, 'r and c of a cell connected to the backbone')
        row, column = cell
        if cell == problem.initial_backbone:
            raise InvalidOutput(
                f'line {line_number}: cell [{row}, {column}] is the initial backbone cell, which must not be listed'
            )
        if cell in connected_on_line:
            raise InvalidOutput(
                f'line {line_number}: cell [{row}, {column}] is connected a second time, first connected on line '
                f'{connected_on_line[cell]}'
            )
        if all((row + row_offset, column + column_offset) not in connected_on_line
               for row_offset, column_offset in NEIGHBOUR_OFFSETS):
            raise InvalidOutput(
                f'line {line_number}: cell [{row}, {column}] has none of its 8 neighbours connected to the backbone, '
                f'expected a neighbour of the initial cell or of a cell listed above'
            )
        connected_on_line[cell] = line_number
        backbone.append(cell)

    router_line = backbone_count + 2
    router_count = read_number(lines, router_line, 'M, the number of routers')
    if not 0 <= router_count <= cell_count:
        raise InvalidOutput(f'line {router_line}: found M = {router_count}, expected 0 to W * H = {cell_count}')
    cost = backbone_count * problem.backbone_price + router_count * problem.router_price
    if cost > problem.budget:
        raise InvalidOutput(
            f'line {router_line}: N * Pb + M * Pr = {backbone_count} * {problem.backbone_price} + {router_count} * '
            f'{problem.router_price} = {cost}, expected at most the budget B = {problem.budget}'
        )

    placed_on_line = {}
    routers = []
    for line_number in range(router_line + 1, router_line + 1 + router_count):
        cell = read_cell(lines, line_number, problem, 'r and c of a router')
        row, column = cell
        if cell in placed_on_line:
            raise InvalidOutput(
                f'line {line_number}: a router is placed in cell [{row}, {column}] a second time, first placed on '
                f'line {placed_on_line[cell]}'
            )
        if cell not in connected_on_line:
            raise InvalidOutput(
                f'line {line_number}: cell [{row}, {column}] is not connected to the backbone, so it cannot hold a '
                f'router'
            )
        if problem.grid[row][column] == WALL:
            raise InvalidOutput(f'line {line_number}: cell [{row}, {column}] is a wall, so it cannot hold a router')
        placed_on_line[cell] = line_number
        routers.append(cell)

    for line_number in range(router_line + 1 + router_count, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidOutput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    return Solution(backbone, routers)


def add_covered_targets(problem: Problem, router: tuple[int, int], covered: set[tuple[int, int]]) -> None:
    """Add to covered the target cells that the router covers: those within R rows and R columns of it, with no wall
    in the smallest rectangle that encloses both."""
    router_row, router_column = router
    for row_step, column_step in QUADRANTS:
        # The rectangle up to a cell holds the rectangles up to the cells between it and the router, so moving away
        # row by row, the signal never reaches further sideways than it did in the row before.
        reach = problem.radius
        for distance in range(problem.radius + 1):
            row = router_row + row_step * distance
            if not 0 <= row < problem.height:
                break
            row_reach = -1
            for offset in range(reach + 1):
                column = router_column + column_step * offset
                if not 0 <= column < problem.width or problem.grid[row][column] == WALL:
                    break
                row_reach = offset
                if problem.grid[row][column] == TARGET:
                    covered.add((row, column))
            reach = row_reach


def score(problem: Problem, solution: Solution) -> int:
    covered = set()
    for router in solution.routers:
        add_covered_targets(problem, router, covered)
    cost = len(solution.backbone) * problem.backbone_price + len(solution.routers) * problem.router_price
    return 1000 * len(covered) + problem.budget - cost


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
