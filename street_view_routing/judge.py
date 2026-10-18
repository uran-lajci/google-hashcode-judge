"""Score an output file for Hash Code 2014, Final Round: Street View routing.

python3 judge.py -i example.in -o example.out
"""

import argparse
import dataclasses
import fractions
import re


class InvalidInput(Exception):
    """The input file breaks the format of the problem statement, which is a bug in the data set."""


class InvalidOutput(Exception):
    """The output file breaks a rule of the problem statement."""


@dataclasses.dataclass(frozen=True)
class Street:
    start: int
    end: int
    bidirectional: bool
    cost: int
    length: int


@dataclasses.dataclass(frozen=True)
class Problem:
    junction_count: int
    duration: int
    car_count: int
    start: int
    streets: list[Street]
    street_by_move: dict[tuple[int, int], int]


@dataclasses.dataclass(frozen=True)
class Solution:
    itineraries: list[list[int]]


def read_input_line(lines: list[str], line_number: int, pattern: str, expected: str) -> list[str]:
    if line_number > len(lines):
        raise InvalidInput(f'line {line_number}: found the end of the file, expected {expected}')
    line = lines[line_number - 1]
    if re.fullmatch(pattern, line) is None:
        raise InvalidInput(
            f'line {line_number}: found {line[:100]!r}, expected {expected} separated by single spaces'
        )
    return line.split(' ')


def check_input_range(
    value: int | fractions.Fraction,
    line_number: int,
    name: str,
    low: int,
    high: int,
) -> None:
    if not low <= value <= high:
        raise InvalidInput(f'line {line_number}: found {name} = {value}, expected {low} to {high}')


def check_junction(lines: list[str], line_number: int) -> None:
    # Matches '48.8582 2.2945' or '-12 3.09'
    pattern = r'-?[0-9]{1,3}(\.[0-9]+)? -?[0-9]{1,3}(\.[0-9]+)?'
    latitude, longitude = read_input_line(lines, line_number, pattern, 'lat and long')
    check_input_range(fractions.Fraction(latitude), line_number, 'lat', -90, 90)
    check_input_range(fractions.Fraction(longitude), line_number, 'long', -180, 180)


def read_street(lines: list[str], line_number: int, junction_count: int) -> Street:
    tokens = read_input_line(lines, line_number, r'[0-9]{1,10}( [0-9]{1,10}){4}', 'A, B, D, C and L')
    a, b, d, cost, length = (int(token) for token in tokens)
    check_input_range(a, line_number, 'A', 0, junction_count - 1)
    check_input_range(b, line_number, 'B', 0, junction_count - 1)
    check_input_range(d, line_number, 'D', 1, 2)
    if a == b:
        raise InvalidInput(f'line {line_number}: the street starts and ends at junction {a}')
    return Street(a, b, d == 2, cost, length)


def read_problem(input_file: str) -> Problem:
    with open(input_file, encoding='ascii', newline='') as file:
        lines = file.read().split('\n')

    tokens = read_input_line(lines, 1, r'[0-9]{1,10}( [0-9]{1,10}){4}', 'N, M, T, C and S')
    junction_count, street_count, duration, car_count, start = (int(token) for token in tokens)
    check_input_range(start, 1, 'S', 0, junction_count - 1)

    for line_number in range(2, junction_count + 2):
        check_junction(lines, line_number)

    streets = []
    street_by_move = {}
    line_by_pair = {}
    for line_number in range(junction_count + 2, junction_count + street_count + 2):
        street = read_street(lines, line_number, junction_count)
        # Each pair of junctions is connected by at most one street.
        pair = (min(street.start, street.end), max(street.start, street.end))
        if pair in line_by_pair:
            raise InvalidInput(
                f'line {line_number}: junctions {pair[0]} and {pair[1]} are already connected by the street on line '
                f'{line_by_pair[pair]}'
            )
        line_by_pair[pair] = line_number

        street_by_move[street.start, street.end] = len(streets)
        if street.bidirectional:
            street_by_move[street.end, street.start] = len(streets)
        streets.append(street)

    for line_number in range(junction_count + street_count + 2, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidInput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    return Problem(junction_count, duration, car_count, start, streets, street_by_move)


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


def read_move(problem: Problem, origin: int, junction: int, line_number: int) -> int:
    """Return the street that a car drives to go from origin to junction."""
    move = (origin, junction)
    if move in problem.street_by_move:
        return problem.street_by_move[move]

    if (junction, origin) in problem.street_by_move:
        street = problem.street_by_move[junction, origin]
        raise InvalidOutput(
            f'line {line_number}: street {street} goes one way, from junction {junction} to junction {origin}, '
            f'so a car cannot drive it from {origin} to {junction}'
        )
    raise InvalidOutput(f'line {line_number}: no street connects junction {origin} to junction {junction}')


def read_itinerary(lines: list[str], line_number: int, problem: Problem, car: int) -> list[int]:
    visit_count = read_number(lines, line_number, f'V, the number of junctions visited by car {car}')
    if not 1 <= visit_count <= 10**6:
        raise InvalidOutput(f'line {line_number}: found V = {visit_count}, expected 1 to 1000000')

    itinerary = []
    time = 0
    for visit in range(visit_count):
        line_number += 1
        junction = read_number(lines, line_number, f'junction {visit} of car {car}')
        if not 0 <= junction < problem.junction_count:
            raise InvalidOutput(
                f'line {line_number}: junction {junction} does not exist, expected an ID from 0 to '
                f'{problem.junction_count - 1}'
            )

        if not itinerary:
            if junction != problem.start:
                raise InvalidOutput(
                    f'line {line_number}: car {car} starts at junction {junction}, expected the starting junction '
                    f'S = {problem.start}'
                )
        else:
            street = read_move(problem, itinerary[-1], junction, line_number)
            # A car cannot be in transit when the time runs out.
            time += problem.streets[street].cost
            if time > problem.duration:
                raise InvalidOutput(
                    f'line {line_number}: car {car} reaches junction {junction} at time {time}, after '
                    f'T = {problem.duration}'
                )
        itinerary.append(junction)
    return itinerary


def read_solution(output_file: str, problem: Problem) -> Solution:
    lines = read_lines(output_file)

    car_count = read_number(lines, 1, 'C, the number of cars')
    if car_count != problem.car_count:
        raise InvalidOutput(
            f'line 1: found C = {car_count}, expected {problem.car_count}, the number of cars in the input'
        )

    itineraries = []
    line_number = 2
    for car in range(car_count):
        itinerary = read_itinerary(lines, line_number, problem, car)
        itineraries.append(itinerary)
        line_number += 1 + len(itinerary)

    for line_number in range(line_number, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidOutput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    return Solution(itineraries)


def score(problem: Problem, solution: Solution) -> int:
    # A street counts once, however many cars drive it and in whichever direction.
    driven = {
        problem.street_by_move[move]
        for itinerary in solution.itineraries
        for move in zip(itinerary, itinerary[1:])
    }
    return sum(problem.streets[street].length for street in driven)


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
