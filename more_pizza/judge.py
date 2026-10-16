"""Score an output file for Hash Code 2020, Practice Round: More pizza.

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
    max_slices: int
    slices: list[int]


@dataclasses.dataclass(frozen=True)
class Solution:
    pizza_types: list[int]


def read_problem(input_file: str) -> Problem:
    with open(input_file, encoding='ascii', newline='') as file:
        lines = file.read().split('\n')

    header = re.fullmatch(r'([0-9]+) ([0-9]+)', lines[0])
    if header is None:
        raise InvalidInput(f'line 1: found {lines[0]!r}, expected M N separated by a single space')
    max_slices, type_count = (int(number) for number in header.groups())
    if not 1 <= max_slices <= 10**9:
        raise InvalidInput(f'line 1: found M = {max_slices}, expected M from 1 to 10^9')
    if not 1 <= type_count <= 10**5:
        raise InvalidInput(f'line 1: found N = {type_count}, expected N from 1 to 10^5')

    if lines[-1] != '':
        raise InvalidInput(f'line {len(lines)}: found the end of the file, expected a newline')
    if len(lines) != 3:
        raise InvalidInput(f'found {len(lines) - 1} lines, expected 2')
    if re.fullmatch(r'[0-9]+( [0-9]+)*', lines[1]) is None:
        raise InvalidInput('line 2: expected the sizes of the pizza types as integers separated by single spaces')

    slices = [int(size) for size in lines[1].split(' ')]
    if len(slices) != type_count:
        raise InvalidInput(f'line 2: found {len(slices)} pizza types, expected N = {type_count}')
    for pizza_type, size in enumerate(slices):
        if not 1 <= size <= max_slices:
            raise InvalidInput(
                f'line 2: pizza type {pizza_type} has {size} slices, expected 1 to M = {max_slices}'
            )
    if slices != sorted(slices):
        raise InvalidInput('line 2: found the sizes of the pizza types out of order, expected non-decreasing order')

    return Problem(max_slices, slices)


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


def read_line(lines: list[str], line_number: int, token_count: int, expected: str) -> list[str]:
    if line_number > len(lines):
        raise InvalidOutput(f'line {line_number}: found the end of the file, expected {expected}')
    tokens = lines[line_number - 1].split()
    if len(tokens) != token_count:
        raise InvalidOutput(f'line {line_number}: found {len(tokens)} tokens, expected {expected}')
    return tokens


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


def read_solution(output_file: str, problem: Problem) -> Solution:
    lines = read_lines(output_file)

    type_count = len(problem.slices)
    ordered_type_count = parse_int(read_line(lines, 1, 1, 'the number of pizza types to order')[0], 1)
    if not 0 <= ordered_type_count <= type_count:
        raise InvalidOutput(f'line 1: found {ordered_type_count} pizza types, expected 0 to N = {type_count}')

    # With K = 0 the second line is empty, and an empty last line reads the same as no line at all.
    if ordered_type_count == 0 and len(lines) == 1:
        return Solution([])

    tokens = read_line(lines, 2, ordered_type_count, f'K = {ordered_type_count} pizza types')
    # The token on line 2 that orders each pizza type, or 0 while no token orders it.
    ordered_by_token = [0] * type_count
    pizza_types = []
    for token_number, token in enumerate(tokens, start=1):
        pizza_type = parse_int(token, 2)
        if not 0 <= pizza_type < type_count:
            raise InvalidOutput(
                f'line 2: pizza type {pizza_type} does not exist, expected a type from 0 to {type_count - 1}'
            )
        # At most one pizza of each type, even when two types have the same size.
        if ordered_by_token[pizza_type]:
            raise InvalidOutput(
                f'line 2: pizza type {pizza_type} is ordered a second time by token {token_number}, '
                f'first ordered by token {ordered_by_token[pizza_type]}'
            )
        ordered_by_token[pizza_type] = token_number
        pizza_types.append(pizza_type)

    ordered_slices = sum(problem.slices[pizza_type] for pizza_type in pizza_types)
    if ordered_slices > problem.max_slices:
        raise InvalidOutput(
            f'line 2: the pizzas ordered have {ordered_slices} slices, expected at most M = {problem.max_slices}'
        )

    for line_number in range(3, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidOutput(f'line {line_number}: found {lines[line_number - 1]!r}, expected the end of the file')

    return Solution(pizza_types)


def score(problem: Problem, solution: Solution) -> int:
    return sum(problem.slices[pizza_type] for pizza_type in solution.pizza_types)


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
