"""Score an output file for Hash Code 2015, Qualification Round: Optimize a data center.

python3 judge.py -i example.in -o example.out
"""

import argparse
import dataclasses
import re

UNAVAILABLE = -1


class InvalidInput(Exception):
    """The input file breaks the format of the problem statement, which is a bug in the data set."""


class InvalidOutput(Exception):
    """The output file breaks a rule of the problem statement."""


@dataclasses.dataclass(frozen=True)
class Server:
    size: int
    capacity: int


@dataclasses.dataclass(frozen=True)
class Problem:
    row_count: int
    slot_count: int
    pool_count: int
    unavailable_slots: frozenset[tuple[int, int]]
    servers: list[Server]


@dataclasses.dataclass(frozen=True)
class Placement:
    row: int
    slot: int
    pool: int


@dataclasses.dataclass(frozen=True)
class Solution:
    """The placement of each server in input order, or None for a server left unallocated."""

    placements: list[Placement | None]


def read_input_line(lines: list[str], line_number: int, names: list[str]) -> list[int]:
    """Read one integer for each name, separated by single spaces."""
    expected = ' '.join(names)
    if line_number > len(lines):
        raise InvalidInput(f'line {line_number}: found the end of the file, expected {expected}')
    line = lines[line_number - 1]
    if re.fullmatch(' '.join([r'[0-9]{1,7}'] * len(names)), line) is None:
        raise InvalidInput(f'line {line_number}: found {line!r}, expected {expected} separated by single spaces')
    return [int(token) for token in line.split(' ')]


def check_input_range(value: int, line_number: int, name: str, low: int, high: int) -> None:
    if not low <= value <= high:
        raise InvalidInput(f'line {line_number}: found {name} = {value}, expected {low} to {high}')


def read_problem(input_file: str) -> Problem:
    with open(input_file, encoding='ascii', newline='') as file:
        lines = file.read().split('\n')

    row_count, slot_count, unavailable_count, pool_count, server_count = read_input_line(
        lines, 1, ['R', 'S', 'U', 'P', 'M']
    )
    check_input_range(row_count, 1, 'R', 1, 1000)
    check_input_range(slot_count, 1, 'S', 1, 1000)
    check_input_range(unavailable_count, 1, 'U', 0, row_count * slot_count)
    check_input_range(pool_count, 1, 'P', 1, 1000)
    check_input_range(server_count, 1, 'M', 1, row_count * slot_count)

    unavailable_slots = set()
    for line_number in range(2, unavailable_count + 2):
        row, slot = read_input_line(lines, line_number, ['r', 's'])
        check_input_range(row, line_number, 'r', 0, row_count - 1)
        check_input_range(slot, line_number, 's', 0, slot_count - 1)
        if (row, slot) in unavailable_slots:
            raise InvalidInput(f'line {line_number}: row {row}, slot {slot} is listed as unavailable a second time')
        unavailable_slots.add((row, slot))

    servers = []
    for line_number in range(unavailable_count + 2, unavailable_count + server_count + 2):
        size, capacity = read_input_line(lines, line_number, ['z', 'c'])
        check_input_range(size, line_number, 'z', 1, slot_count)
        check_input_range(capacity, line_number, 'c', 1, 1000)
        servers.append(Server(size, capacity))

    for line_number in range(unavailable_count + server_count + 2, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidInput(f'line {line_number}: found {lines[line_number - 1]!r}, expected the end of the file')

    return Problem(row_count, slot_count, pool_count, frozenset(unavailable_slots), servers)


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
        raise InvalidOutput(f'line {line_number}: found {token!r}, expected an integer')
    try:
        return int(token)
    except ValueError:
        # Since Python 3.10.7, int() refuses more than 4300 digits by default.
        raise InvalidOutput(
            f'line {line_number}: found an integer of {len(token)} characters, which is too long'
        ) from None


def read_placement(lines: list[str], line_number: int, problem: Problem) -> Placement | None:
    expected = 'x or ar as ap'
    if line_number > len(lines):
        raise InvalidOutput(f'line {line_number}: found the end of the file, expected {expected}')
    tokens = lines[line_number - 1].split()
    if tokens == ['x']:
        return None
    if len(tokens) == 1:
        raise InvalidOutput(f'line {line_number}: found {tokens[0]!r}, expected {expected}')
    if len(tokens) != 3:
        raise InvalidOutput(f'line {line_number}: found {len(tokens)} tokens, expected {expected}')

    row, slot, pool = (parse_int(token, line_number) for token in tokens)
    if not 0 <= row < problem.row_count:
        raise InvalidOutput(
            f'line {line_number}: row {row} does not exist, expected a row from 0 to {problem.row_count - 1}'
        )
    if not 0 <= slot < problem.slot_count:
        raise InvalidOutput(
            f'line {line_number}: slot {slot} does not exist, expected a slot from 0 to {problem.slot_count - 1}'
        )
    if not 0 <= pool < problem.pool_count:
        raise InvalidOutput(
            f'line {line_number}: pool {pool} does not exist, expected a pool from 0 to {problem.pool_count - 1}'
        )
    return Placement(row, slot, pool)


def read_solution(output_file: str, problem: Problem) -> Solution:
    lines = read_lines(output_file)

    # The output line of the server in each slot, 0 while the slot is free, or UNAVAILABLE.
    occupied_by_line = [[0] * problem.slot_count for _ in range(problem.row_count)]
    for row, slot in problem.unavailable_slots:
        occupied_by_line[row][slot] = UNAVAILABLE

    placements = []
    for server_id, server in enumerate(problem.servers):
        line_number = server_id + 1
        placement = read_placement(lines, line_number, problem)
        placements.append(placement)
        if placement is None:
            continue

        last_slot = placement.slot + server.size - 1
        if last_slot >= problem.slot_count:
            raise InvalidOutput(
                f'line {line_number}: server {server_id} of size {server.size} at slot {placement.slot} '
                f'ends at slot {last_slot}, expected at most slot {problem.slot_count - 1}'
            )
        row_slots = occupied_by_line[placement.row]
        for slot in range(placement.slot, last_slot + 1):
            if row_slots[slot] == UNAVAILABLE:
                raise InvalidOutput(
                    f'line {line_number}: server {server_id} occupies row {placement.row}, slot {slot}, '
                    'which is unavailable'
                )
            if row_slots[slot]:
                raise InvalidOutput(
                    f'line {line_number}: server {server_id} occupies row {placement.row}, slot {slot}, '
                    f'which server {row_slots[slot] - 1} on line {row_slots[slot]} already occupies'
                )
            row_slots[slot] = line_number

    for line_number in range(len(problem.servers) + 1, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidOutput(f'line {line_number}: found {lines[line_number - 1]!r}, expected the end of the file')

    return Solution(placements)


def score(problem: Problem, solution: Solution) -> int:
    capacity_by_pool_and_row = [[0] * problem.row_count for _ in range(problem.pool_count)]
    for server, placement in zip(problem.servers, solution.placements):
        if placement is not None:
            capacity_by_pool_and_row[placement.pool][placement.row] += server.capacity

    # The guaranteed capacity of a pool is what it keeps when the row holding most of its capacity goes down.
    return min(sum(row_capacities) - max(row_capacities) for row_capacities in capacity_by_pool_and_row)


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
