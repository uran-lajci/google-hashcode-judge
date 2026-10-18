"""Score an output file for Hash Code 2019, Final Round: Compiling Google.

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
class CompiledFile:
    compile_time: int
    replicate_time: int
    dependencies: list[str]


@dataclasses.dataclass(frozen=True)
class Target:
    deadline: int
    goal_points: int


@dataclasses.dataclass(frozen=True)
class Problem:
    server_count: int
    files: dict[str, CompiledFile]
    targets: dict[str, Target]


@dataclasses.dataclass(frozen=True)
class Step:
    file: str
    server: int


@dataclasses.dataclass(frozen=True)
class Solution:
    steps: list[Step]


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


def read_compiled_file(
    lines: list[str],
    line_number: int,
    files: dict[str, CompiledFile],
) -> tuple[str, CompiledFile]:
    # Matches 'c2 15 35'
    tokens = read_input_line(lines, line_number, r'[A-Za-z0-9]{1,10} [0-9]{1,7} [0-9]{1,7}', 'a file name, c and r')
    name, compile_time, replicate_time = tokens[0], int(tokens[1]), int(tokens[2])
    check_input_range(compile_time, line_number, 'c', 1, 1_000_000)
    check_input_range(replicate_time, line_number, 'r', 1, 1_000_000)
    if name in files:
        raise InvalidInput(f'line {line_number}: compiled file {name} is described a second time')

    # Matches '0' or '2 c1 c2'
    tokens = read_input_line(lines, line_number + 1, r'[0-9]{1,3}( [A-Za-z0-9]{1,10})*', 'n and the dependencies')
    dependency_count, dependencies = int(tokens[0]), tokens[1:]
    check_input_range(dependency_count, line_number + 1, 'n', 0, 100)
    if len(dependencies) != dependency_count:
        raise InvalidInput(
            f'line {line_number + 1}: found {len(dependencies)} dependencies, expected n = {dependency_count}'
        )
    # Every dependency is described earlier, so the dependencies form a directed acyclic graph. The statement does not
    # forbid listing a dependency twice, and f_big.in does so in 3,104 files.
    for dependency in dependencies:
        if dependency not in files:
            raise InvalidInput(f'line {line_number + 1}: dependency {dependency} is not described earlier')
    return name, CompiledFile(compile_time, replicate_time, dependencies)


def read_problem(input_file: str) -> Problem:
    with open(input_file, encoding='ascii', newline='') as file:
        lines = file.read().split('\n')

    tokens = read_input_line(lines, 1, r'[0-9]{1,6} [0-9]{1,6} [0-9]{1,3}', 'C, T and S')
    file_count, target_count, server_count = (int(token) for token in tokens)
    check_input_range(file_count, 1, 'C', 1, 100_000)
    check_input_range(target_count, 1, 'T', 1, file_count)
    check_input_range(server_count, 1, 'S', 1, 100)

    files = {}
    for line_number in range(2, 2 * file_count + 2, 2):
        name, compiled_file = read_compiled_file(lines, line_number, files)
        files[name] = compiled_file

    targets = {}
    target_lines = range(2 * file_count + 2, 2 * file_count + target_count + 2)
    for line_number in target_lines:
        # Matches 'c3 40 8'
        pattern = r'[A-Za-z0-9]{1,10} [0-9]{1,7} [0-9]{1,7}'
        tokens = read_input_line(lines, line_number, pattern, 'a file name, d and g')
        name, deadline, goal_points = tokens[0], int(tokens[1]), int(tokens[2])
        check_input_range(deadline, line_number, 'd', 1, 1_000_000)
        check_input_range(goal_points, line_number, 'g', 1, 1_000_000)
        if name not in files:
            raise InvalidInput(f'line {line_number}: target file {name} is not a compiled file')
        if name in targets:
            raise InvalidInput(f'line {line_number}: compiled file {name} is a target a second time')
        targets[name] = Target(deadline, goal_points)

    for line_number in range(target_lines.stop, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidInput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    return Problem(server_count, files, targets)


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


def read_step(lines: list[str], line_number: int, problem: Problem, compiled_earlier: set[str]) -> Step:
    expected = 'the name of a compiled file and a server'
    tokens = read_tokens(lines, line_number, expected)
    if len(tokens) != 2:
        raise InvalidOutput(f'line {line_number}: found {len(tokens)} tokens, expected {expected}')

    name = tokens[0]
    if name not in problem.files:
        raise InvalidOutput(f'line {line_number}: compiled file {name[:100]!r} does not exist')
    server = parse_int(tokens[1], line_number)
    if not 0 <= server < problem.server_count:
        raise InvalidOutput(
            f'line {line_number}: found s = {server}, expected 0 to S - 1 = {problem.server_count - 1}'
        )

    # Each dependency has to be produced by a compilation step that appears earlier in the output file, even when
    # that step finishes later in time.
    for dependency in problem.files[name].dependencies:
        if dependency not in compiled_earlier:
            raise InvalidOutput(
                f'line {line_number}: {name} depends on {dependency}, but no earlier line compiles {dependency}'
            )
    return Step(name, server)


def read_solution(output_file: str, problem: Problem) -> Solution:
    lines = read_lines(output_file)

    tokens = read_tokens(lines, 1, 'E')
    if len(tokens) != 1:
        raise InvalidOutput(f'line 1: found {len(tokens)} tokens, expected E')
    step_count = parse_int(tokens[0], 1)
    max_step_count = len(problem.files) * problem.server_count
    if not 1 <= step_count <= max_step_count:
        raise InvalidOutput(f'line 1: found E = {step_count}, expected 1 to C * S = {max_step_count}')

    # The same compilation step may be listed more than once, so a file compiled twice is not an error.
    compiled_earlier = set()
    steps = []
    for line_number in range(2, step_count + 2):
        step = read_step(lines, line_number, problem, compiled_earlier)
        compiled_earlier.add(step.file)
        steps.append(step)

    for line_number in range(step_count + 2, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidOutput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    return Solution(steps)


def score(problem: Problem, solution: Solution) -> int:
    server_free_at = [0] * problem.server_count
    compiled_on = {name: set() for name in problem.files}
    # The earliest time at which a step read so far finishes the file. Every copy reaches the other servers r seconds
    # after it is compiled, so the earliest copy is also the first to arrive.
    compiled_at = {}
    for step in solution.steps:
        compiled_file = problem.files[step.file]
        start = server_free_at[step.server]
        for dependency in compiled_file.dependencies:
            # A copy compiled earlier on the same server finished before the server became free.
            if step.server not in compiled_on[dependency]:
                start = max(start, compiled_at[dependency] + problem.files[dependency].replicate_time)

        end = start + compiled_file.compile_time
        server_free_at[step.server] = end
        compiled_on[step.file].add(step.server)
        compiled_at[step.file] = min(compiled_at.get(step.file, end), end)

    points = 0
    for name, target in problem.targets.items():
        if name in compiled_at and compiled_at[name] <= target.deadline:
            points += target.deadline - compiled_at[name] + target.goal_points
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
