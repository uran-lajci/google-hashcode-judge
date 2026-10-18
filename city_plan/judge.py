"""Score an output file for Hash Code 2018, Final Round: City plan.

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
class Project:
    residential: bool
    height: int
    width: int
    # The capacity r of a residential project, or the service type u of a utility project.
    value: int
    cells: list[tuple[int, int]]


@dataclasses.dataclass(frozen=True)
class Problem:
    height: int
    width: int
    distance: int
    projects: list[Project]


@dataclasses.dataclass(frozen=True)
class Building:
    project: int
    row: int
    column: int


@dataclasses.dataclass(frozen=True)
class Solution:
    buildings: list[Building]


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


def flood(grid: list[str], start: tuple[int, int]) -> set[tuple[int, int]]:
    """Return the cells reached from start by steps between neighboring cells with the same symbol."""
    symbol = grid[start[0]][start[1]]
    reached = {start}
    stack = [start]
    while stack:
        r, c = stack.pop()
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            nr, nc = neighbor
            if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and grid[nr][nc] == symbol and neighbor not in reached:
                reached.add(neighbor)
                stack.append(neighbor)
    return reached


def check_plan(plan: list[str], line_number: int) -> None:
    """Check the three conditions that the statement guarantees for every building plan."""
    height, width = len(plan), len(plan[0])
    edges = {
        'top row': plan[0],
        'bottom row': plan[-1],
        'left column': [row[0] for row in plan],
        'right column': [row[-1] for row in plan],
    }
    for edge, cells in edges.items():
        if '#' not in cells:
            raise InvalidInput(f'line {line_number}: the plan has no occupied cell in its {edge}')

    occupied = [(r, c) for r in range(height) for c in range(width) if plan[r][c] == '#']
    if len(flood(plan, occupied[0])) != len(occupied):
        raise InvalidInput(f'line {line_number}: the occupied cells of the plan are not connected')

    # A ring of free cells around the plan reaches every free cell that the border of the plan reaches.
    framed = ['.' * (width + 2)] + [f'.{row}.' for row in plan] + ['.' * (width + 2)]
    free_count = (height + 2) * (width + 2) - len(occupied)
    if len(flood(framed, (0, 0))) != free_count:
        raise InvalidInput(f'line {line_number}: the plan has a hole')


def read_problem(input_file: str) -> Problem:
    with open(input_file, encoding='ascii', newline='') as file:
        lines = file.read().split('\n')

    tokens = read_input_line(lines, 1, r'[0-9]{1,4} [0-9]{1,4} [0-9]{1,2} [0-9]{1,4}', 'H, W, D and B')
    height, width, distance, project_count = (int(token) for token in tokens)
    check_input_range(height, 1, 'H', 1, 1000)
    check_input_range(width, 1, 'W', 1, 1000)
    check_input_range(distance, 1, 'D', 1, 20)
    check_input_range(project_count, 1, 'B', 2, 1000)

    line_number = 2
    projects = []
    for _ in range(project_count):
        # Matches 'R 3 2 25'
        tokens = read_input_line(lines, line_number, r'[RU] [0-9]{1,2} [0-9]{1,2} [0-9]{1,4}', 'type, h, w and r or u')
        residential = tokens[0] == 'R'
        plan_height, plan_width, value = (int(token) for token in tokens[1:])
        check_input_range(plan_height, line_number, 'h', 1, min(height, 50))
        check_input_range(plan_width, line_number, 'w', 1, min(width, 50))
        if residential:
            check_input_range(value, line_number, 'r', 1, 1000)
        else:
            check_input_range(value, line_number, 'u', 0, 1000)

        plan = lines[line_number : line_number + plan_height]
        for row_line, row in enumerate(plan, line_number + 1):
            # Matches '.#' when w = 2
            if re.fullmatch(f'[#.]{{{plan_width}}}', row) is None:
                raise InvalidInput(f"line {row_line}: found {row[:100]!r}, expected {plan_width} cells, '#' or '.'")
        if len(plan) < plan_height:
            raise InvalidInput(f'line {len(lines) + 1}: found the end of the file, expected {plan_width} cells')
        check_plan(plan, line_number)

        cells = [(r, c) for r in range(plan_height) for c in range(plan_width) if plan[r][c] == '#']
        projects.append(Project(residential, plan_height, plan_width, value, cells))
        line_number += 1 + plan_height

    for line_number in range(line_number, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidInput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    if all(project.residential for project in projects):
        raise InvalidInput('there is no utility project')
    if not any(project.residential for project in projects):
        raise InvalidInput('there is no residential project')

    return Problem(height, width, distance, projects)


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


def read_tokens(lines: list[str], line_number: int, expected: str) -> list[str]:
    if line_number > len(lines):
        raise InvalidOutput(f'line {line_number}: found the end of the file, expected {expected}')
    return lines[line_number - 1].split()


def check_range(value: int, line_number: int, name: str, high_name: str, high: int) -> None:
    if not 0 <= value <= high:
        raise InvalidOutput(f'line {line_number}: found {name} = {value}, expected 0 to {high_name} = {high}')


def read_building(lines: list[str], line_number: int, problem: Problem) -> Building:
    expected = 'b, r and c'
    tokens = read_tokens(lines, line_number, expected)
    if len(tokens) != 3:
        raise InvalidOutput(f'line {line_number}: found {len(tokens)} tokens, expected {expected}')
    project, row, column = (parse_int(token, line_number) for token in tokens)
    check_range(project, line_number, 'b', 'B - 1', len(problem.projects) - 1)
    check_range(row, line_number, 'r', 'H - 1', problem.height - 1)
    check_range(column, line_number, 'c', 'W - 1', problem.width - 1)

    # Every edge of a plan has an occupied cell, so the whole plan fits in the city exactly when its occupied
    # cells do.
    plan = problem.projects[project]
    last_row, last_column = row + plan.height - 1, column + plan.width - 1
    if last_row >= problem.height:
        raise InvalidOutput(
            f'line {line_number}: project {project} placed at [{row}, {column}] covers rows {row} to {last_row}, '
            f'expected rows up to H - 1 = {problem.height - 1}'
        )
    if last_column >= problem.width:
        raise InvalidOutput(
            f'line {line_number}: project {project} placed at [{row}, {column}] covers columns {column} to '
            f'{last_column}, expected columns up to W - 1 = {problem.width - 1}'
        )
    return Building(project, row, column)


def read_solution(output_file: str, problem: Problem) -> Solution:
    lines = read_lines(output_file)

    tokens = read_tokens(lines, 1, 'N')
    if len(tokens) != 1:
        raise InvalidOutput(f'line 1: found {len(tokens)} tokens, expected N')
    building_count = parse_int(tokens[0], 1)
    check_range(building_count, 1, 'N', 'H × W', problem.height * problem.width)

    # The line of the building that occupies each cell of the city, row after row, or 0 for a free cell.
    occupied_by = [0] * (problem.height * problem.width)
    buildings = []
    for line_number in range(2, building_count + 2):
        building = read_building(lines, line_number, problem)
        for r, c in problem.projects[building.project].cells:
            row, column = building.row + r, building.column + c
            cell = row * problem.width + column
            if occupied_by[cell]:
                raise InvalidOutput(
                    f'line {line_number}: project {building.project} placed at [{building.row}, {building.column}] '
                    f'occupies cell [{row}, {column}], which the building on line {occupied_by[cell]} occupies'
                )
            occupied_by[cell] = line_number
        buildings.append(building)

    for line_number in range(building_count + 2, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidOutput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    return Solution(buildings)


def reach(project: Project, distance: int) -> list[tuple[int, int, int]]:
    """Return the cells within the walking distance of an occupied cell of the plan, as (row, first column, end
    column) runs relative to the top-left corner of the plan, with the end column excluded."""
    # The occupied cells of each row of the plan, as runs of consecutive columns.
    runs_by_row = {}
    for r, c in project.cells:
        runs = runs_by_row.setdefault(r, [])
        if runs and runs[-1][1] == c - 1:
            runs[-1] = (runs[-1][0], c)
        else:
            runs.append((c, c))

    result = []
    for row in range(-distance, project.height + distance):
        # A run of row r reaches, in this row, the columns up to distance - |row - r| to either side of it.
        intervals = sorted(
            (first - (distance - abs(row - r)), last + (distance - abs(row - r)))
            for r, runs in runs_by_row.items()
            if abs(row - r) <= distance
            for first, last in runs
        )
        merged = []
        for first, last in intervals:
            if merged and first <= merged[-1][1] + 1:
                merged[-1][1] = max(merged[-1][1], last)
            else:
                merged.append([first, last])
        result.extend((row, first, last + 1) for first, last in merged)
    return result


def score(problem: Problem, solution: Solution) -> int:
    distance = problem.distance
    # The service type of the utility that occupies each cell, or -1. A margin of D cells around the city lets
    # every reach run of a placed building be one slice of this list, without clipping.
    padded_width = problem.width + 2 * distance
    services = [-1] * ((problem.height + 2 * distance) * padded_width)
    for building in solution.buildings:
        project = problem.projects[building.project]
        if not project.residential:
            for r, c in project.cells:
                services[(building.row + distance + r) * padded_width + building.column + distance + c] = project.value

    slices = {}
    points = 0
    for building in solution.buildings:
        project = problem.projects[building.project]
        if not project.residential:
            continue
        if building.project not in slices:
            slices[building.project] = [
                (row * padded_width + first, row * padded_width + end) for row, first, end in reach(project, distance)
            ]
        origin = (building.row + distance) * padded_width + building.column + distance
        # Utilities never overlap the residential building, so each reachable service type has a cell within D of
        # an occupied cell of the building, which is the distance between the two buildings.
        types = set()
        for first, end in slices[building.project]:
            types.update(services[origin + first : origin + end])
        types.discard(-1)
        points += project.value * len(types)
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
