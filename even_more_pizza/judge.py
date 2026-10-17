"""Score an output file for Hash Code 2021, Practice Round: Even more pizza.

python3 judge.py -i example.in -o example.out
"""

import argparse
import dataclasses
import re

TEAM_SIZES = (2, 3, 4)


class InvalidInput(Exception):
    """The input file breaks the format of the problem statement, which is a bug in the data set."""


class InvalidOutput(Exception):
    """The output file breaks a rule of the problem statement."""


@dataclasses.dataclass(frozen=True)
class Problem:
    pizzas: list[frozenset[str]]
    team_counts: dict[int, int]


@dataclasses.dataclass(frozen=True)
class Solution:
    deliveries: list[list[int]]


def parse_input_int(token: str, line_number: int, name: str, low: int, high: int) -> int:
    if re.fullmatch(r'[0-9]{1,6}', token) is None or not low <= int(token) <= high:
        raise InvalidInput(f'line {line_number}: found {name} = {token!r}, expected an integer from {low} to {high}')
    return int(token)


def read_pizza(lines: list[str], line_number: int) -> frozenset[str]:
    if line_number > len(lines):
        raise InvalidInput(f'line {line_number}: found the end of the file, expected a pizza as I ingredient_1 ...')
    tokens = lines[line_number - 1].split()
    if not tokens:
        raise InvalidInput(f'line {line_number}: found 0 tokens, expected a pizza as I ingredient_1 ...')
    ingredient_count = parse_input_int(tokens[0], line_number, 'I', 1, 10_000)
    ingredients = tokens[1:]
    if len(ingredients) != ingredient_count:
        raise InvalidInput(f'line {line_number}: found {len(ingredients)} ingredients, expected I = {ingredient_count}')

    for ingredient in ingredients:
        if re.fullmatch(r'[a-z-]{1,20}', ingredient) is None:
            raise InvalidInput(
                f'line {line_number}: found the ingredient {ingredient!r}, '
                'expected 1 to 20 lowercase ASCII letters and dashes'
            )
    pizza = frozenset(ingredients)
    if len(pizza) != ingredient_count:
        raise InvalidInput(f'line {line_number}: found an ingredient twice, expected I different ingredients')
    return pizza


def read_problem(input_file: str) -> Problem:
    with open(input_file, encoding='ascii', newline='') as file:
        lines = file.read().split('\n')

    header = lines[0].split()
    if len(header) != 4:
        raise InvalidInput(f'line 1: found {lines[0]!r}, expected M T2 T3 T4')
    pizza_count = parse_input_int(header[0], 1, 'M', 1, 100_000)
    team_counts = {
        size: parse_input_int(token, 1, f'T{size}', 0, 50_000) for size, token in zip(TEAM_SIZES, header[1:])
    }

    pizzas = [read_pizza(lines, line_number) for line_number in range(2, pizza_count + 2)]

    for line_number in range(pizza_count + 2, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidInput(f'line {line_number}: found {lines[line_number - 1]!r}, expected the end of the file')

    return Problem(pizzas, team_counts)


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


def read_delivery(lines: list[str], line_number: int) -> list[int]:
    """Read a delivery as L P1 ... PL, checking only that the line holds L pizzas for a team of 2, 3 or 4."""
    if line_number > len(lines):
        raise InvalidOutput(f'line {line_number}: found the end of the file, expected a delivery as L P1 ... PL')
    tokens = lines[line_number - 1].split()
    if not tokens:
        raise InvalidOutput(f'line {line_number}: found 0 tokens, expected a delivery as L P1 ... PL')

    team_size = parse_int(tokens[0], line_number)
    if team_size not in TEAM_SIZES:
        raise InvalidOutput(f'line {line_number}: found a team of {team_size} people, expected 2, 3 or 4')
    # Everybody in the team gets exactly one pizza, or the team gets no delivery and no line.
    if len(tokens) - 1 != team_size:
        raise InvalidOutput(f'line {line_number}: found {len(tokens) - 1} pizzas, expected L = {team_size}')

    return [parse_int(token, line_number) for token in tokens[1:]]


def read_solution(output_file: str, problem: Problem) -> Solution:
    lines = read_lines(output_file)

    if not lines:
        raise InvalidOutput('line 1: found the end of the file, expected the number of deliveries')
    header = lines[0].split()
    if len(header) != 1:
        raise InvalidOutput(f'line 1: found {len(header)} tokens, expected the number of deliveries')
    delivery_count = parse_int(header[0], 1)
    team_count = sum(problem.team_counts.values())
    if not 1 <= delivery_count <= team_count:
        raise InvalidOutput(
            f'line 1: found {delivery_count} deliveries, expected 1 to T2 + T3 + T4 = {team_count}'
        )

    pizza_count = len(problem.pizzas)
    deliveries_by_size = dict.fromkeys(TEAM_SIZES, 0)
    # The line of the delivery that holds each pizza, or 0 while no delivery holds it.
    delivered_on_line = [0] * pizza_count
    deliveries = []
    for line_number in range(2, delivery_count + 2):
        pizzas = read_delivery(lines, line_number)

        team_size = len(pizzas)
        deliveries_by_size[team_size] += 1
        if deliveries_by_size[team_size] > problem.team_counts[team_size]:
            raise InvalidOutput(
                f'line {line_number}: found delivery {deliveries_by_size[team_size]} to a team of {team_size} '
                f'people, expected at most T{team_size} = {problem.team_counts[team_size]}'
            )

        for pizza in pizzas:
            if not 0 <= pizza < pizza_count:
                raise InvalidOutput(
                    f'line {line_number}: pizza {pizza} does not exist, expected a pizza from 0 to {pizza_count - 1}'
                )
            # Each pizza goes to at most one team, even when two pizzas have the same ingredients.
            if delivered_on_line[pizza]:
                raise InvalidOutput(
                    f'line {line_number}: pizza {pizza} is delivered a second time, '
                    f'first delivered on line {delivered_on_line[pizza]}'
                )
            delivered_on_line[pizza] = line_number
        deliveries.append(pizzas)

    for line_number in range(delivery_count + 2, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidOutput(f'line {line_number}: found {lines[line_number - 1]!r}, expected the end of the file')

    return Solution(deliveries)


def score(problem: Problem, solution: Solution) -> int:
    return sum(
        len(frozenset().union(*(problem.pizzas[pizza] for pizza in delivery))) ** 2
        for delivery in solution.deliveries
    )


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
