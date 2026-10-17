"""Score an output file for Hash Code 2018, Qualification Round: Self-driving rides.

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
class Ride:
    start_row: int
    start_column: int
    finish_row: int
    finish_column: int
    earliest_start: int
    latest_finish: int

    @property
    def distance(self) -> int:
        return abs(self.finish_row - self.start_row) + abs(self.finish_column - self.start_column)


@dataclasses.dataclass(frozen=True)
class Problem:
    vehicle_count: int
    bonus: int
    rides: list[Ride]


@dataclasses.dataclass(frozen=True)
class Solution:
    rides_by_vehicle: list[list[int]]


def read_input_line(lines: list[str], line_number: int, count: int, expected: str) -> list[int]:
    """Read count natural numbers separated by single spaces."""
    if line_number > len(lines):
        raise InvalidInput(f'line {line_number}: found the end of the file, expected {expected}')
    tokens = lines[line_number - 1].split(' ')
    if len(tokens) != count or any(re.fullmatch(r'[0-9]{1,10}', token) is None for token in tokens):
        raise InvalidInput(
            f'line {line_number}: found {lines[line_number - 1][:100]!r}, '
            f'expected {expected} separated by single spaces'
        )
    return [int(token) for token in tokens]


def check_input_range(value: int, line_number: int, name: str, low: int, high: int) -> None:
    if not low <= value <= high:
        raise InvalidInput(f'line {line_number}: found {name} = {value}, expected {low} to {high}')


def read_ride(lines: list[str], line_number: int, rows: int, columns: int, steps: int) -> Ride:
    a, b, x, y, s, f = read_input_line(lines, line_number, 6, 'a, b, x, y, s and f')
    check_input_range(a, line_number, 'a', 0, rows - 1)
    check_input_range(b, line_number, 'b', 0, columns - 1)
    check_input_range(x, line_number, 'x', 0, rows - 1)
    check_input_range(y, line_number, 'y', 0, columns - 1)
    check_input_range(s, line_number, 's', 0, steps - 1)
    check_input_range(f, line_number, 'f', 0, steps)
    ride = Ride(a, b, x, y, s, f)

    if ride.distance == 0:
        raise InvalidInput(f'line {line_number}: the ride starts and finishes at [{a}, {b}]')
    if f < s + ride.distance:
        raise InvalidInput(
            f'line {line_number}: found f = {f}, expected at least s + distance = {s + ride.distance}'
        )
    return ride


def read_problem(input_file: str) -> Problem:
    with open(input_file, encoding='ascii', newline='') as file:
        lines = file.read().split('\n')

    rows, columns, vehicle_count, ride_count, bonus, steps = read_input_line(lines, 1, 6, 'R, C, F, N, B and T')
    check_input_range(rows, 1, 'R', 1, 10000)
    check_input_range(columns, 1, 'C', 1, 10000)
    check_input_range(vehicle_count, 1, 'F', 1, 1000)
    check_input_range(ride_count, 1, 'N', 1, 10000)
    check_input_range(bonus, 1, 'B', 1, 10000)
    check_input_range(steps, 1, 'T', 1, 10**9)

    rides = [read_ride(lines, line_number, rows, columns, steps) for line_number in range(2, ride_count + 2)]

    for line_number in range(ride_count + 2, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidInput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    return Problem(vehicle_count, bonus, rides)


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


def read_vehicle_rides(lines: list[str], line_number: int, problem: Problem) -> list[int]:
    expected = f'M followed by the rides of vehicle {line_number - 1}'
    if line_number > len(lines):
        raise InvalidOutput(f'line {line_number}: found the end of the file, expected {expected}')
    tokens = lines[line_number - 1].split()
    if not tokens:
        raise InvalidOutput(f'line {line_number}: found an empty line, expected {expected}')

    ride_count = len(problem.rides)
    assigned_count = parse_int(tokens[0], line_number)
    if not 0 <= assigned_count <= ride_count:
        raise InvalidOutput(f'line {line_number}: found M = {assigned_count}, expected 0 to {ride_count}')
    if len(tokens) - 1 != assigned_count:
        raise InvalidOutput(
            f'line {line_number}: found M = {assigned_count}, but the number of rides that follow is {len(tokens) - 1}'
        )

    rides = []
    for token in tokens[1:]:
        ride = parse_int(token, line_number)
        if not 0 <= ride < ride_count:
            raise InvalidOutput(
                f'line {line_number}: ride {ride} does not exist, expected an ID from 0 to {ride_count - 1}'
            )
        rides.append(ride)
    return rides


def read_solution(output_file: str, problem: Problem) -> Solution:
    lines = read_lines(output_file)

    rides_by_vehicle = []
    line_by_ride = {}
    for line_number in range(1, problem.vehicle_count + 1):
        rides = read_vehicle_rides(lines, line_number, problem)
        # Each ride is assigned at most once, to one vehicle.
        for ride in rides:
            if ride in line_by_ride:
                raise InvalidOutput(
                    f'line {line_number}: ride {ride} is assigned a second time, first assigned on line '
                    f'{line_by_ride[ride]}'
                )
            line_by_ride[ride] = line_number
        rides_by_vehicle.append(rides)

    for line_number in range(problem.vehicle_count + 1, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidOutput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    return Solution(rides_by_vehicle)


def score(problem: Problem, solution: Solution) -> int:
    points = 0
    for rides in solution.rides_by_vehicle:
        step = 0
        row, column = 0, 0
        for ride_id in rides:
            ride = problem.rides[ride_id]
            arrival = step + abs(ride.start_row - row) + abs(ride.start_column - column)
            start = max(arrival, ride.earliest_start)
            # A late ride earns nothing, but the vehicle still drives it to the finish intersection.
            step = start + ride.distance
            row, column = ride.finish_row, ride.finish_column

            # The simulation ends at step T, but f <= T, so a ride that finishes by f also finishes by T.
            if step <= ride.latest_finish:
                points += ride.distance
                if start == ride.earliest_start:
                    points += problem.bonus
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
