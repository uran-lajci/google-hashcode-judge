"""Score an output file for Hash Code 2021, Qualification Round: Traffic signaling.

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
class Street:
    start: int
    end: int
    length: int


@dataclasses.dataclass(frozen=True)
class Problem:
    duration: int
    intersection_count: int
    bonus: int
    streets: dict[str, Street]
    paths: list[list[str]]


@dataclasses.dataclass(frozen=True)
class GreenLight:
    street: str
    duration: int


@dataclasses.dataclass(frozen=True)
class Schedule:
    intersection: int
    green_lights: list[GreenLight]


@dataclasses.dataclass(frozen=True)
class Solution:
    schedules: list[Schedule]


@dataclasses.dataclass(frozen=True)
class GreenWindow:
    """The light of a street is green while (time - start) % cycle < duration."""

    start: int
    duration: int
    cycle: int


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


def read_street(lines: list[str], line_number: int, duration: int, intersection_count: int) -> tuple[str, Street]:
    # Matches '2 0 rue-de-londres 1'
    pattern = r'[0-9]{1,6} [0-9]{1,6} [a-z-]{3,30} [0-9]{1,6}'
    tokens = read_input_line(lines, line_number, pattern, 'B, E, the street name and L')
    start, end, length = int(tokens[0]), int(tokens[1]), int(tokens[3])
    check_input_range(start, line_number, 'B', 0, intersection_count - 1)
    check_input_range(end, line_number, 'E', 0, intersection_count - 1)
    check_input_range(length, line_number, 'L', 1, duration)
    return tokens[2], Street(start, end, length)


def read_path(lines: list[str], line_number: int, streets: dict[str, Street]) -> list[str]:
    # Matches '3 rue-d-athenes rue-de-moscou rue-de-londres'
    tokens = read_input_line(lines, line_number, r'[0-9]{1,6}( [a-z-]{3,30})+', 'P and the names of the streets')
    street_count = int(tokens[0])
    check_input_range(street_count, line_number, 'P', 2, 1000)
    path = tokens[1:]
    if len(path) != street_count:
        raise InvalidInput(f'line {line_number}: found {len(path)} streets, expected P = {street_count}')

    for name in path:
        if name not in streets:
            raise InvalidInput(f'line {line_number}: street {name} does not exist')
    for name, next_name in zip(path, path[1:]):
        if streets[name].end != streets[next_name].start:
            raise InvalidInput(f'line {line_number}: street {next_name} does not start where street {name} ends')
    # Each car goes through an intersection at most once. It does not go through the one where its path ends.
    crossed = [streets[name].end for name in path[:-1]]
    if len(set(crossed)) != len(crossed):
        raise InvalidInput(f'line {line_number}: the car goes through an intersection twice')
    return path


def read_problem(input_file: str) -> Problem:
    with open(input_file, encoding='ascii', newline='') as file:
        lines = file.read().split('\n')

    tokens = read_input_line(lines, 1, r'[0-9]{1,6}( [0-9]{1,6}){4}', 'D, I, S, V and F')
    duration, intersection_count, street_count, car_count, bonus = (int(token) for token in tokens)
    check_input_range(duration, 1, 'D', 1, 10_000)
    check_input_range(intersection_count, 1, 'I', 2, 100_000)
    check_input_range(street_count, 1, 'S', 2, 100_000)
    check_input_range(car_count, 1, 'V', 1, 1000)
    check_input_range(bonus, 1, 'F', 1, 1000)

    streets = {}
    connected = set()
    for line_number in range(2, street_count + 2):
        name, street = read_street(lines, line_number, duration, intersection_count)
        if name in streets:
            raise InvalidInput(f'line {line_number}: street {name} is described a second time')
        # Two streets never connect two intersections in the same direction.
        if (street.start, street.end) in connected:
            raise InvalidInput(
                f'line {line_number}: a second street leads from intersection {street.start} to {street.end}'
            )
        streets[name] = street
        connected.add((street.start, street.end))

    # Each intersection has at least one street that comes into it and at least one that leaves it.
    starts = {street.start for street in streets.values()}
    ends = {street.end for street in streets.values()}
    for intersection in range(intersection_count):
        if intersection not in starts or intersection not in ends:
            raise InvalidInput(f'intersection {intersection} lacks a street that comes into it or leaves it')

    path_lines = range(street_count + 2, street_count + car_count + 2)
    paths = [read_path(lines, line_number, streets) for line_number in path_lines]

    for line_number in range(path_lines.stop, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidInput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    return Problem(duration, intersection_count, bonus, streets, paths)


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


def read_green_light(
    lines: list[str],
    line_number: int,
    problem: Problem,
    intersection: int,
    listed_on_line: dict[str, int],
) -> GreenLight:
    expected = 'a street name and the duration T'
    if line_number > len(lines):
        raise InvalidOutput(f'line {line_number}: found the end of the file, expected {expected}')
    tokens = lines[line_number - 1].split()
    if len(tokens) != 2:
        raise InvalidOutput(f'line {line_number}: found {len(tokens)} tokens, expected {expected}')

    name = tokens[0]
    if name not in problem.streets:
        raise InvalidOutput(f'line {line_number}: street {name[:100]!r} does not exist')
    street_end = problem.streets[name].end
    if street_end != intersection:
        raise InvalidOutput(
            f'line {line_number}: street {name} does not enter intersection {intersection}, '
            f'it enters intersection {street_end}'
        )
    # Each street can appear at most once in the schedule.
    if name in listed_on_line:
        raise InvalidOutput(
            f'line {line_number}: street {name} is listed a second time, first listed on line {listed_on_line[name]}'
        )

    duration = parse_int(tokens[1], line_number)
    if not 1 <= duration <= problem.duration:
        raise InvalidOutput(f'line {line_number}: found T = {duration}, expected 1 to D = {problem.duration}')
    return GreenLight(name, duration)


def read_solution(output_file: str, problem: Problem) -> Solution:
    lines = read_lines(output_file)
    incoming_counts = [0] * problem.intersection_count
    for street in problem.streets.values():
        incoming_counts[street.end] += 1

    schedule_count = read_single_int(lines, 1, 'A')
    if not 0 <= schedule_count <= problem.intersection_count:
        raise InvalidOutput(f'line 1: found A = {schedule_count}, expected 0 to I = {problem.intersection_count}')

    # The line that starts the schedule of each intersection, or 0 while no schedule covers it.
    scheduled_on_line = [0] * problem.intersection_count
    schedules = []
    line_number = 2
    for _ in range(schedule_count):
        intersection = read_single_int(lines, line_number, 'the intersection ID i')
        if not 0 <= intersection < problem.intersection_count:
            raise InvalidOutput(
                f'line {line_number}: intersection {intersection} does not exist, '
                f'expected an ID from 0 to {problem.intersection_count - 1}'
            )
        # Each intersection can only be listed once.
        if scheduled_on_line[intersection]:
            raise InvalidOutput(
                f'line {line_number}: intersection {intersection} is listed a second time, first listed on line '
                f'{scheduled_on_line[intersection]}'
            )
        scheduled_on_line[intersection] = line_number

        expected = f'E, the number of streets in the schedule of intersection {intersection}'
        street_count = read_single_int(lines, line_number + 1, expected)
        incoming_count = incoming_counts[intersection]
        if not 1 <= street_count <= incoming_count:
            raise InvalidOutput(
                f'line {line_number + 1}: found E = {street_count}, expected 1 to {incoming_count}, '
                f'the number of streets that enter intersection {intersection}'
            )

        listed_on_line = {}
        green_lights = []
        for street_line in range(line_number + 2, line_number + 2 + street_count):
            green_light = read_green_light(lines, street_line, problem, intersection, listed_on_line)
            listed_on_line[green_light.street] = street_line
            green_lights.append(green_light)
        schedules.append(Schedule(intersection, green_lights))
        line_number += 2 + street_count

    for line_number in range(line_number, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidOutput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    return Solution(schedules)


def next_green(window: GreenWindow, time: int) -> int:
    """Return the first second from time on at which the light is green."""
    into_window = (time - window.start) % window.cycle
    if into_window < window.duration:
        return time
    return time + window.cycle - into_window


def score(problem: Problem, solution: Solution) -> int:
    windows = {}
    for schedule in solution.schedules:
        cycle = sum(green_light.duration for green_light in schedule.green_lights)
        start = 0
        for green_light in schedule.green_lights:
            windows[green_light.street] = GreenWindow(start, green_light.duration, cycle)
            start += green_light.duration

    # A car waiting at the end of a street, as (the second it got there, car, index of the street in its path). Two cars
    # never reach the end of one street in the same second, because at most one car crosses an intersection per second.
    # The exception is the cars that start there, and the car listed first in the input goes first.
    waiting = [(0, car, 0) for car in range(len(problem.paths))]
    # The first second at which the next car in the queue of a street may cross, one second after the car before it.
    free_from = {}
    points = 0
    while waiting:
        arrival, car, index = heapq.heappop(waiting)
        path = problem.paths[car]
        street = path[index]
        if street not in windows:
            continue

        crossing = next_green(windows[street], max(arrival, free_from.get(street, 0)))
        free_from[street] = crossing + 1
        next_arrival = crossing + problem.streets[path[index + 1]].length
        if next_arrival > problem.duration:
            continue
        if index + 2 == len(path):
            points += problem.bonus + problem.duration - next_arrival
        else:
            heapq.heappush(waiting, (next_arrival, car, index + 1))
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
