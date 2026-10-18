"""Score an output file for Hash Code 2021, Final Round: Software engineering at scale.

python3 judge.py -i example.in -o example.out
"""

import argparse
import dataclasses
import heapq
import re


class InvalidInput(Exception):
    """The input file breaks the format of the problem statement, which is a bug in the data set."""


class InvalidOutput(Exception):
    """The output file breaks a rule of the problem statement."""


@dataclasses.dataclass(frozen=True)
class Feature:
    difficulty: int
    users: int
    services: frozenset[int]


@dataclasses.dataclass(frozen=True)
class Problem:
    duration: int
    engineer_count: int
    service_names: list[str]
    service_ids: dict[str, int]
    # The binary in which each service initially runs.
    initial_binaries: list[int]
    binary_count: int
    features: dict[str, Feature]
    new_binary_days: int


@dataclasses.dataclass(frozen=True)
class Implement:
    line_number: int
    feature: str
    binary: int


@dataclasses.dataclass(frozen=True)
class Move:
    line_number: int
    service: int
    binary: int


@dataclasses.dataclass(frozen=True)
class NewBinary:
    line_number: int


@dataclasses.dataclass(frozen=True)
class Wait:
    line_number: int
    days: int


Task = Implement | Move | NewBinary | Wait


@dataclasses.dataclass(frozen=True)
class Solution:
    # The day on which each feature launches, for the features that launch before day L.
    launch_days: dict[str, int]


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


def read_feature(
    lines: list[str],
    line_number: int,
    service_ids: dict[str, int],
) -> tuple[str, Feature]:
    # Matches 'foo 3 3 100'
    pattern = r'[a-z-]{1,20} [0-9]{1,6} [0-9]{1,6} [0-9]{1,6}'
    tokens = read_input_line(lines, line_number, pattern, 'the feature name, M, D and U')
    name, service_count, difficulty, users = tokens[0], int(tokens[1]), int(tokens[2]), int(tokens[3])
    check_input_range(service_count, line_number, 'M', 1, len(service_ids))
    check_input_range(difficulty, line_number, 'D', 1, 100)
    check_input_range(users, line_number, 'U', 1, 100_000)

    # Matches 'sc sb sd'
    names = read_input_line(lines, line_number + 1, r'[a-z-]{1,20}( [a-z-]{1,20})*', 'the names of the services')
    if len(names) != service_count:
        raise InvalidInput(f'line {line_number + 1}: found {len(names)} services, expected M = {service_count}')
    for service in names:
        if service not in service_ids:
            raise InvalidInput(f'line {line_number + 1}: service {service} does not exist')
    if len(set(names)) != len(names):
        raise InvalidInput(f'line {line_number + 1}: a service is listed twice')
    return name, Feature(difficulty, users, frozenset(service_ids[service] for service in names))


def read_problem(input_file: str) -> Problem:
    with open(input_file, encoding='ascii', newline='') as file:
        lines = file.read().split('\n')

    tokens = read_input_line(lines, 1, r'[0-9]{1,6}( [0-9]{1,6}){5}', 'L, G, S, B, F and N')
    duration, engineer_count, service_count, binary_count, feature_count, new_binary_days = (
        int(token) for token in tokens
    )
    check_input_range(duration, 1, 'L', 1, 1000)
    check_input_range(engineer_count, 1, 'G', 1, 100_000)
    check_input_range(service_count, 1, 'S', 1, 10_000)
    check_input_range(binary_count, 1, 'B', 1, 10_000)
    check_input_range(feature_count, 1, 'F', 1, 10_000)
    check_input_range(new_binary_days, 1, 'N', 1, 10)

    service_names = []
    service_ids = {}
    initial_binaries = []
    for line_number in range(2, service_count + 2):
        # Matches 'sa 1'
        name, binary = read_input_line(lines, line_number, r'[a-z-]{1,20} [0-9]{1,6}', 'the service name and B_i')
        if name in service_ids:
            raise InvalidInput(f'line {line_number}: service {name} is described a second time')
        check_input_range(int(binary), line_number, 'B_i', 0, binary_count - 1)
        service_ids[name] = len(service_names)
        service_names.append(name)
        initial_binaries.append(int(binary))

    # Initially each binary contains at least one service.
    empty_binaries = set(range(binary_count)) - set(initial_binaries)
    if empty_binaries:
        raise InvalidInput(f'binary {min(empty_binaries)} initially contains no service')

    features = {}
    line_number = service_count + 2
    for _ in range(feature_count):
        name, feature = read_feature(lines, line_number, service_ids)
        if name in features:
            raise InvalidInput(f'line {line_number}: feature {name} is described a second time')
        features[name] = feature
        line_number += 2

    for line_number in range(line_number, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidInput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    return Problem(
        duration,
        engineer_count,
        service_names,
        service_ids,
        initial_binaries,
        binary_count,
        features,
        new_binary_days,
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


def read_single_int(lines: list[str], line_number: int, expected: str) -> int:
    if line_number > len(lines):
        raise InvalidOutput(f'line {line_number}: found the end of the file, expected {expected}')
    tokens = lines[line_number - 1].split()
    if len(tokens) != 1:
        raise InvalidOutput(f'line {line_number}: found {len(tokens)} tokens, expected {expected}')
    return parse_int(tokens[0], line_number)


def parse_binary(token: str, line_number: int) -> int:
    # Whether the binary exists depends on the day the task starts, so the simulation checks the upper bound.
    binary = parse_int(token, line_number)
    if binary < 0:
        raise InvalidOutput(f'line {line_number}: binary {binary} does not exist')
    return binary


def read_task(lines: list[str], line_number: int, problem: Problem) -> Task:
    expected = 'a task: impl, move, new or wait'
    if line_number > len(lines):
        raise InvalidOutput(f'line {line_number}: found the end of the file, expected {expected}')
    tokens = lines[line_number - 1].split()
    if not tokens:
        raise InvalidOutput(f'line {line_number}: found 0 tokens, expected {expected}')

    expected_tokens = {'impl': 3, 'move': 3, 'new': 1, 'wait': 2}
    kind = tokens[0]
    if kind not in expected_tokens:
        raise InvalidOutput(f'line {line_number}: found {kind[:100]!r}, expected impl, move, new or wait')
    if len(tokens) != expected_tokens[kind]:
        raise InvalidOutput(
            f'line {line_number}: found {len(tokens)} tokens, expected {expected_tokens[kind]} for {kind}'
        )

    if kind == 'impl':
        if tokens[1] not in problem.features:
            raise InvalidOutput(f'line {line_number}: feature {tokens[1][:100]!r} does not exist')
        return Implement(line_number, tokens[1], parse_binary(tokens[2], line_number))
    if kind == 'move':
        if tokens[1] not in problem.service_ids:
            raise InvalidOutput(f'line {line_number}: service {tokens[1][:100]!r} does not exist')
        return Move(line_number, problem.service_ids[tokens[1]], parse_binary(tokens[2], line_number))
    if kind == 'new':
        return NewBinary(line_number)

    days = parse_int(tokens[1], line_number)
    if not 1 <= days <= problem.duration:
        raise InvalidOutput(f'line {line_number}: found W = {days}, expected 1 to L = {problem.duration}')
    return Wait(line_number, days)


class Simulation:
    """The binaries on one day, and the tasks in progress in them."""

    def __init__(self, problem: Problem) -> None:
        self.problem = problem
        self.binary_services = [set() for _ in range(problem.binary_count)]
        for service, binary in enumerate(problem.initial_binaries):
            self.binary_services[binary].add(service)
        self.service_binary = list(problem.initial_binaries)
        # The line of each implement task in progress in a binary, by feature. Their number is C.
        self.implementing = [{} for _ in range(problem.binary_count)]
        # The line of the move task in progress to or from a binary, or 0 if there is none.
        self.moving_on_line = [0] * problem.binary_count
        # The binary each move in progress takes its service from, by the line of the move.
        self.move_sources = {}
        self.remaining_services = {name: set(feature.services) for name, feature in problem.features.items()}
        self.launch_days = {}

    def check_binary_exists(self, binary: int, line_number: int, day: int) -> None:
        # A new binary only exists once the engineer who creates it is done.
        if binary >= len(self.binary_services):
            raise InvalidOutput(
                f'line {line_number}: on day {day}, binary {binary} does not exist, '
                f'expected an ID from 0 to {len(self.binary_services) - 1}'
            )

    def check_no_move(self, binary: int, line_number: int, day: int) -> None:
        # No engineer can start working on a binary until a move to or from it is finished.
        if self.moving_on_line[binary]:
            raise InvalidOutput(
                f'line {line_number}: on day {day}, binary {binary} is busy with the move that started on line '
                f'{self.moving_on_line[binary]}'
            )

    def check_no_implement(self, binary: int, line_number: int, day: int) -> None:
        # A move cannot start while an engineer is implementing a feature in either binary.
        if self.implementing[binary]:
            raise InvalidOutput(
                f'line {line_number}: on day {day}, binary {binary} is busy with the implementation that started on '
                f'line {min(self.implementing[binary].values())}'
            )

    def start(self, task: Task, day: int) -> int:
        """Start the task on the day, and return the number of days it takes."""
        if isinstance(task, Implement):
            binary = task.binary
            self.check_binary_exists(binary, task.line_number, day)
            self.check_no_move(binary, task.line_number, day)
            # Only one engineer at a time can implement a feature in one binary.
            if task.feature in self.implementing[binary]:
                raise InvalidOutput(
                    f'line {task.line_number}: on day {day}, feature {task.feature} is already being implemented in '
                    f'binary {binary} by the task on line {self.implementing[binary][task.feature]}'
                )
            days = (
                self.problem.features[task.feature].difficulty
                + len(self.binary_services[binary])
                + len(self.implementing[binary])
            )
            self.implementing[binary][task.feature] = task.line_number
            return days

        if isinstance(task, Move):
            target = task.binary
            self.check_binary_exists(target, task.line_number, day)
            source = self.service_binary[task.service]
            if source == target:
                raise InvalidOutput(
                    f'line {task.line_number}: on day {day}, service {self.problem.service_names[task.service]} '
                    f'already runs in binary {target}'
                )
            for binary in source, target:
                self.check_no_move(binary, task.line_number, day)
                self.check_no_implement(binary, task.line_number, day)
            days = max(len(self.binary_services[source]), len(self.binary_services[target]))
            # No task can start in either binary until the move is over, so no task sees the service in transit.
            self.binary_services[source].remove(task.service)
            self.binary_services[target].add(task.service)
            self.service_binary[task.service] = target
            self.moving_on_line[source] = task.line_number
            self.moving_on_line[target] = task.line_number
            self.move_sources[task.line_number] = source
            return days

        if isinstance(task, NewBinary):
            return self.problem.new_binary_days
        return task.days

    def finish(self, task: Task, day: int) -> None:
        if isinstance(task, Implement):
            binary = task.binary
            del self.implementing[binary][task.feature]
            # Moves cannot touch the binary during the implementation, so its services are the same as at the start.
            remaining = self.remaining_services[task.feature]
            if remaining:
                self.remaining_services[task.feature] = remaining - self.binary_services[binary]
                if not self.remaining_services[task.feature]:
                    self.launch_days[task.feature] = day
        elif isinstance(task, Move):
            self.moving_on_line[self.move_sources.pop(task.line_number)] = 0
            self.moving_on_line[task.binary] = 0
        elif isinstance(task, NewBinary):
            # Its ID is the smallest one not used yet.
            self.binary_services.append(set())
            self.implementing.append({})
            self.moving_on_line.append(0)


def simulate(problem: Problem, schedules: list[list[Task]]) -> dict[str, int]:
    """Run the schedules, and return the day on which each feature launches if it does before day L."""
    simulation = Simulation(problem)
    # The day on which each engineer starts their next task, and the number of tasks they have started.
    queue = [(0, engineer) for engineer in range(len(schedules))]
    started = [0] * len(schedules)
    # Tasks that start on or after day L are ignored. Tasks that start earlier take up their binaries even if they end
    # after L, but nothing that ends after L can change the score.
    while queue and queue[0][0] < problem.duration:
        day = queue[0][0]
        engineers = []
        while queue and queue[0][0] == day:
            engineers.append(heapq.heappop(queue)[1])

        # Tasks that end on a day free their binaries for the tasks that start on it. Engineers come out of the heap
        # in the order of the submission file, so the one listed earlier starts first.
        for engineer in engineers:
            if started[engineer]:
                simulation.finish(schedules[engineer][started[engineer] - 1], day)
        for engineer in engineers:
            schedule = schedules[engineer]
            if started[engineer] < len(schedule):
                days = simulation.start(schedule[started[engineer]], day)
                started[engineer] += 1
                heapq.heappush(queue, (day + days, engineer))

    return simulation.launch_days


def read_solution(output_file: str, problem: Problem) -> Solution:
    lines = read_lines(output_file)

    engineer_count = read_single_int(lines, 1, 'E')
    if not 0 <= engineer_count <= problem.engineer_count:
        raise InvalidOutput(f'line 1: found E = {engineer_count}, expected 0 to G = {problem.engineer_count}')

    schedules = []
    line_number = 2
    for engineer in range(engineer_count):
        task_count = read_single_int(lines, line_number, f'T, the number of tasks of engineer {engineer}')
        if not 1 <= task_count <= problem.duration:
            raise InvalidOutput(
                f'line {line_number}: found T = {task_count}, expected 1 to L = {problem.duration}'
            )
        task_lines = range(line_number + 1, line_number + 1 + task_count)
        schedules.append([read_task(lines, task_line, problem) for task_line in task_lines])
        line_number = task_lines.stop

    for line_number in range(line_number, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidOutput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    return Solution(simulate(problem, schedules))


def score(problem: Problem, solution: Solution) -> int:
    points = 0
    for name, day in solution.launch_days.items():
        points += problem.features[name].users * max(0, problem.duration - day)
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
