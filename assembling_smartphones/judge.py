"""Score an output file for Hash Code 2020, Final Round: Assembling smartphones.

python3 judge.py -i example.in -o example.out
"""

import argparse
import dataclasses
import re

MOVES = {'R': (1, 0), 'L': (-1, 0), 'U': (0, 1), 'D': (0, -1)}


class InvalidInput(Exception):
    """The input file breaks the format of the problem statement, which is a bug in the data set."""


class InvalidOutput(Exception):
    """The output file breaks a rule of the problem statement."""


@dataclasses.dataclass(frozen=True)
class Task:
    score: int
    points: list[tuple[int, int]]


@dataclasses.dataclass(frozen=True)
class Problem:
    width: int
    height: int
    arm_count: int
    step_count: int
    mount_points: set[tuple[int, int]]
    tasks: list[Task]


@dataclasses.dataclass(frozen=True)
class Arm:
    """The tasks of an arm are on the line after line_number, and its instructions on the line after that."""

    line_number: int
    mount_point: tuple[int, int]
    tasks: list[int]
    instructions: list[str]


@dataclasses.dataclass(frozen=True)
class Solution:
    arms: list[Arm]


def read_input_line(lines: list[str], line_number: int, count: int, expected: str) -> list[int]:
    """Read count natural numbers separated by single spaces."""
    if line_number > len(lines):
        raise InvalidInput(f'line {line_number}: found the end of the file, expected {expected}')
    tokens = lines[line_number - 1].split(' ')
    if len(tokens) != count or any(re.fullmatch(r'[0-9]{1,7}', token) is None for token in tokens):
        raise InvalidInput(
            f'line {line_number}: found {lines[line_number - 1][:100]!r}, '
            f'expected {expected} separated by single spaces'
        )
    return [int(token) for token in tokens]


def check_input_range(value: int, line_number: int, name: str, low: int, high: int) -> None:
    if not low <= value <= high:
        raise InvalidInput(f'line {line_number}: found {name} = {value}, expected {low} to {high}')


def read_task(lines: list[str], line_number: int, width: int, height: int, mount_points: set[tuple[int, int]]) -> Task:
    task_score, point_count = read_input_line(lines, line_number, 2, 'S and P')
    check_input_range(task_score, line_number, 'S', 1, 10**6)
    check_input_range(point_count, line_number, 'P', 1, 1000)

    coordinates = read_input_line(lines, line_number + 1, 2 * point_count, f'the {2 * point_count} coordinates')
    points = list(zip(coordinates[::2], coordinates[1::2]))
    for x, y in points:
        check_input_range(x, line_number + 1, 'x', 0, width - 1)
        check_input_range(y, line_number + 1, 'y', 0, height - 1)
        # An assembly point is never in the same cell as a mount point.
        if (x, y) in mount_points:
            raise InvalidInput(f'line {line_number + 1}: assembly point [{x}, {y}] is a mount point')
    return Task(task_score, points)


def read_problem(input_file: str) -> Problem:
    with open(input_file, encoding='ascii', newline='') as file:
        lines = file.read().split('\n')

    width, height, arm_count, mount_count, task_count, step_count = read_input_line(
        lines, 1, 6, 'W, H, R, M, T and L'
    )
    check_input_range(width, 1, 'W', 1, 1000)
    check_input_range(height, 1, 'H', 1, 1000)
    check_input_range(arm_count, 1, 'R', 1, 100)
    check_input_range(mount_count, 1, 'M', arm_count, 1000)
    check_input_range(task_count, 1, 'T', 1, 1000)
    check_input_range(step_count, 1, 'L', 1, 10**4)

    mount_points = set()
    for line_number in range(2, mount_count + 2):
        x, y = read_input_line(lines, line_number, 2, 'x and y')
        check_input_range(x, line_number, 'x', 0, width - 1)
        check_input_range(y, line_number, 'y', 0, height - 1)
        if (x, y) in mount_points:
            raise InvalidInput(f'line {line_number}: cell [{x}, {y}] has a second mount point')
        mount_points.add((x, y))

    task_lines = range(mount_count + 2, mount_count + 2 + 2 * task_count, 2)
    tasks = [read_task(lines, line_number, width, height, mount_points) for line_number in task_lines]

    for line_number in range(task_lines.stop, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidInput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    return Problem(width, height, arm_count, step_count, mount_points, tasks)


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


def read_tokens(lines: list[str], line_number: int, count: int, expected: str) -> list[str]:
    if line_number > len(lines):
        raise InvalidOutput(f'line {line_number}: found the end of the file, expected {expected}')
    tokens = lines[line_number - 1].split()
    if len(tokens) != count:
        raise InvalidOutput(f'line {line_number}: found {len(tokens)} tokens, expected {expected}')
    return tokens


def read_arm(
    lines: list[str],
    line_number: int,
    problem: Problem,
    mounted_on_line: dict[tuple[int, int], int],
    assigned_on_line: dict[int, int],
) -> Arm:
    tokens = read_tokens(lines, line_number, 4, 'x, y, Z and K')
    x, y, task_count, instruction_count = (parse_int(token, line_number) for token in tokens)
    if (x, y) not in problem.mount_points:
        raise InvalidOutput(f'line {line_number}: cell [{x}, {y}] is not a mount point')
    # No two robotic arms can be installed at the same mount point.
    if (x, y) in mounted_on_line:
        raise InvalidOutput(
            f'line {line_number}: mount point [{x}, {y}] is used a second time, '
            f'first used on line {mounted_on_line[(x, y)]}'
        )
    if not 1 <= task_count <= len(problem.tasks):
        raise InvalidOutput(f'line {line_number}: found Z = {task_count}, expected 1 to T = {len(problem.tasks)}')
    if not 1 <= instruction_count <= problem.step_count:
        raise InvalidOutput(
            f'line {line_number}: found K = {instruction_count}, expected 1 to L = {problem.step_count}'
        )

    task_line = line_number + 1
    tasks = []
    for token in read_tokens(lines, task_line, task_count, f'Z = {task_count} task IDs'):
        task = parse_int(token, task_line)
        if not 0 <= task < len(problem.tasks):
            raise InvalidOutput(
                f'line {task_line}: task {task} does not exist, expected an ID from 0 to {len(problem.tasks) - 1}'
            )
        # Each task is assigned to at most one arm, and only once to it.
        if task in assigned_on_line:
            raise InvalidOutput(
                f'line {task_line}: task {task} is assigned a second time, first assigned on line '
                f'{assigned_on_line[task]}'
            )
        assigned_on_line[task] = task_line
        tasks.append(task)

    instruction_line = line_number + 2
    instructions = read_tokens(lines, instruction_line, instruction_count, f'K = {instruction_count} instructions')
    for instruction in instructions:
        if instruction not in MOVES and instruction != 'W':
            raise InvalidOutput(
                f'line {instruction_line}: found {instruction[:100]!r}, expected an instruction R, L, U, D or W'
            )

    mounted_on_line[(x, y)] = line_number
    return Arm(line_number, (x, y), tasks, instructions)


def simulate(problem: Problem, arms: list[Arm]) -> None:
    """Run the instructions step by step, and check that the arms move legally and complete all their tasks."""
    # The cells each arm occupies, from its mount point to its gripper.
    bodies = [[arm.mount_point] for arm in arms]
    # Unused mount points block every arm, so they belong to no arm.
    owners = dict.fromkeys(problem.mount_points, -1)
    for index, arm in enumerate(arms):
        owners[arm.mount_point] = index
    # For each arm, the position in its task list and the position in the points of its current task.
    task_positions = [0] * len(arms)
    point_positions = [0] * len(arms)

    for step in range(max(len(arm.instructions) for arm in arms)):
        # All retractions free their cells first, because an arm can expand to a cell that is occupied by the gripper
        # of another arm if that gripper retracts in the same step.
        expansions = []
        for index, arm in enumerate(arms):
            if step >= len(arm.instructions) or arm.instructions[step] == 'W':
                continue
            body = bodies[index]
            dx, dy = MOVES[arm.instructions[step]]
            cell = (body[-1][0] + dx, body[-1][1] + dy)
            if len(body) > 1 and body[-2] == cell:
                del owners[body.pop()]
            else:
                expansions.append((index, cell))

        for index, (x, y) in expansions:
            line_number = arms[index].line_number + 2
            if not (0 <= x < problem.width and 0 <= y < problem.height):
                raise InvalidOutput(
                    f'line {line_number}: in step {step}, the arm expands to [{x}, {y}], '
                    f'outside the workspace of {problem.width} x {problem.height} cells'
                )
            if (x, y) in problem.mount_points:
                raise InvalidOutput(
                    f'line {line_number}: in step {step}, the arm expands to [{x}, {y}], which is a mount point'
                )
            if (x, y) in owners:
                owner = owners[(x, y)]
                occupant = 'the arm itself' if owner == index else f'the arm mounted at {list(arms[owner].mount_point)}'
                raise InvalidOutput(
                    f'line {line_number}: in step {step}, the arm expands to [{x}, {y}], which {occupant} occupies'
                )
            owners[(x, y)] = index
            bodies[index].append((x, y))

        # The work at an assembly point takes no time, so the gripper can visit several points of its tasks in a step.
        for index, arm in enumerate(arms):
            gripper = bodies[index][-1]
            while task_positions[index] < len(arm.tasks):
                points = problem.tasks[arm.tasks[task_positions[index]]].points
                if points[point_positions[index]] != gripper:
                    break
                point_positions[index] += 1
                if point_positions[index] == len(points):
                    task_positions[index] += 1
                    point_positions[index] = 0

    for index, arm in enumerate(arms):
        if task_positions[index] < len(arm.tasks):
            task = arm.tasks[task_positions[index]]
            raise InvalidOutput(
                f'line {arm.line_number + 1}: the arm does not complete task {task}, it visits '
                f'{point_positions[index]} of its {len(problem.tasks[task].points)} assembly points'
            )


def read_solution(output_file: str, problem: Problem) -> Solution:
    lines = read_lines(output_file)

    arm_count = parse_int(read_tokens(lines, 1, 1, 'A')[0], 1)
    if not 1 <= arm_count <= problem.arm_count:
        raise InvalidOutput(f'line 1: found A = {arm_count}, expected 1 to R = {problem.arm_count}')

    mounted_on_line = {}
    assigned_on_line = {}
    arm_lines = range(2, 2 + 3 * arm_count, 3)
    arms = [read_arm(lines, line_number, problem, mounted_on_line, assigned_on_line) for line_number in arm_lines]

    for line_number in range(arm_lines.stop, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidOutput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    simulate(problem, arms)
    return Solution(arms)


def score(problem: Problem, solution: Solution) -> int:
    return sum(problem.tasks[task].score for arm in solution.arms for task in arm.tasks)


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
