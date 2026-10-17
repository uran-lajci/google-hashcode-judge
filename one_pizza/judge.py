"""Score an output file for Hash Code 2022, Practice Round: One pizza.

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
class Client:
    likes: frozenset[str]
    dislikes: frozenset[str]


@dataclasses.dataclass(frozen=True)
class Problem:
    clients: list[Client]


@dataclasses.dataclass(frozen=True)
class Solution:
    pizza: frozenset[str]


def parse_input_int(token: str, line_number: int, name: str, low: int, high: int) -> int:
    if re.fullmatch(r'[0-9]{1,6}', token) is None or not low <= int(token) <= high:
        raise InvalidInput(f'line {line_number}: found {name} = {token!r}, expected an integer from {low} to {high}')
    return int(token)


def read_ingredients(lines: list[str], line_number: int, name: str, low: int) -> frozenset[str]:
    """Read the likes (name 'L') or dislikes (name 'D') of a client as a count and that many ingredients."""
    if line_number > len(lines):
        raise InvalidInput(f'line {line_number}: found the end of the file, expected {name} ingredient_1 ...')
    tokens = lines[line_number - 1].split()
    if not tokens:
        raise InvalidInput(f'line {line_number}: found 0 tokens, expected {name} ingredient_1 ...')
    ingredient_count = parse_input_int(tokens[0], line_number, name, low, 5)
    ingredients = tokens[1:]
    if len(ingredients) != ingredient_count:
        raise InvalidInput(
            f'line {line_number}: found {len(ingredients)} ingredients, expected {name} = {ingredient_count}'
        )

    for ingredient in ingredients:
        if re.fullmatch(r'[a-z0-9]{1,15}', ingredient) is None:
            raise InvalidInput(
                f'line {line_number}: found the ingredient {ingredient!r}, '
                'expected 1 to 15 lowercase ASCII letters and digits'
            )
    return frozenset(ingredients)


def read_problem(input_file: str) -> Problem:
    with open(input_file, encoding='ascii', newline='') as file:
        lines = file.read().split('\n')

    header = lines[0].split()
    if len(header) != 1:
        raise InvalidInput(f'line 1: found {lines[0]!r}, expected C')
    client_count = parse_input_int(header[0], 1, 'C', 1, 100_000)

    clients = [
        Client(
            likes=read_ingredients(lines, line_number, 'L', 1),
            dislikes=read_ingredients(lines, line_number + 1, 'D', 0),
        )
        for line_number in range(2, 2 * client_count + 2, 2)
    ]

    for line_number in range(2 * client_count + 2, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidInput(f'line {line_number}: found {lines[line_number - 1]!r}, expected the end of the file')

    return Problem(clients)


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


def read_solution(output_file: str, problem: Problem) -> Solution:
    lines = read_lines(output_file)

    if not lines:
        raise InvalidOutput('line 1: found the end of the file, expected N ingredient_1 ... ingredient_N')
    tokens = lines[0].split()
    if not tokens:
        raise InvalidOutput('line 1: found 0 tokens, expected N ingredient_1 ... ingredient_N')
    ingredient_count = parse_int(tokens[0], 1)
    if ingredient_count < 0:
        raise InvalidOutput(f'line 1: found N = {ingredient_count}, expected 0 or more')
    ingredients = tokens[1:]
    if len(ingredients) != ingredient_count:
        raise InvalidOutput(f'line 1: found {len(ingredients)} ingredients, expected N = {ingredient_count}')

    mentioned = frozenset().union(*(client.likes | client.dislikes for client in problem.clients))
    pizza = set()
    for ingredient in ingredients:
        # An ingredient that only some client dislikes is still mentioned, so it may go on the pizza.
        if ingredient not in mentioned:
            raise InvalidOutput(f'line 1: ingredient {ingredient!r} is not mentioned by any client')
        if ingredient in pizza:
            raise InvalidOutput(f'line 1: ingredient {ingredient!r} is on the pizza a second time')
        pizza.add(ingredient)

    for line_number in range(2, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidOutput(f'line {line_number}: found {lines[line_number - 1]!r}, expected the end of the file')

    return Solution(frozenset(pizza))


def score(problem: Problem, solution: Solution) -> int:
    return sum(
        client.likes <= solution.pizza and client.dislikes.isdisjoint(solution.pizza) for client in problem.clients
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
