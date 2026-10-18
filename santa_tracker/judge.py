"""Score an output file for Hash Code 2022, Final Round: Santa Tracker.

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
class Gift:
    name: str
    score: int
    weight: int
    column: int
    row: int


@dataclasses.dataclass(frozen=True)
class Problem:
    time_limit: int
    reach: int
    # (l_i, a_i) for each acceleration range: up to l_i kg the sleigh accelerates by at most a_i.
    acceleration_ranges: list[tuple[int, int]]
    gifts: list[Gift]
    gift_ids: dict[str, int]


@dataclasses.dataclass(frozen=True)
class Solution:
    delivered: list[int]


DIRECTIONS = {
    'AccUp': (0, 1),
    'AccDown': (0, -1),
    'AccLeft': (-1, 0),
    'AccRight': (1, 0),
}


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


def read_gift(lines: list[str], line_number: int) -> Gift:
    # Matches 'Olivia 1 10 5 1' and 'Bob 10 15 0 -100'
    pattern = r'[a-zA-Z0-9]{1,30} [0-9]{1,5} [0-9]{1,4} -?[0-9]{1,10} -?[0-9]{1,10}'
    tokens = read_input_line(lines, line_number, pattern, 'the name, score, weight, column and row of a gift')
    name, score, weight, column, row = tokens[0], int(tokens[1]), int(tokens[2]), int(tokens[3]), int(tokens[4])
    check_input_range(score, line_number, 'the score', 1, 10_000)
    check_input_range(weight, line_number, 'the weight', 1, 1000)
    check_input_range(column, line_number, 'the column', -10**9, 10**9)
    check_input_range(row, line_number, 'the row', -10**9, 10**9)
    return Gift(name, score, weight, column, row)


def read_problem(input_file: str) -> Problem:
    with open(input_file, encoding='ascii', newline='') as file:
        lines = file.read().split('\n')

    tokens = read_input_line(lines, 1, r'[0-9]{1,6}( [0-9]{1,6}){3}', 'T, D, W and G')
    time_limit, reach, range_count, gift_count = (int(token) for token in tokens)
    check_input_range(time_limit, 1, 'T', 1, 10_000)
    check_input_range(reach, 1, 'D', 0, 100)
    check_input_range(range_count, 1, 'W', 1, 10)
    check_input_range(gift_count, 1, 'G', 1, 10_000)

    acceleration_ranges = []
    for line_number in range(2, range_count + 2):
        tokens = read_input_line(lines, line_number, r'[0-9]{1,7} [0-9]{1,3}', 'l_i and a_i')
        weight_limit, acceleration = int(tokens[0]), int(tokens[1])
        check_input_range(weight_limit, line_number, 'l_i', 1, 10**6)
        check_input_range(acceleration, line_number, 'a_i', 1, 100)
        if acceleration_ranges and not weight_limit > acceleration_ranges[-1][0]:
            raise InvalidInput(f'line {line_number}: l_i = {weight_limit} does not increase')
        if acceleration_ranges and not acceleration < acceleration_ranges[-1][1]:
            raise InvalidInput(f'line {line_number}: a_i = {acceleration} does not decrease')
        acceleration_ranges.append((weight_limit, acceleration))

    gifts = []
    gift_ids = {}
    listed_on_line = {(0, 0): 'Lapland'}
    for line_number in range(range_count + 2, range_count + gift_count + 2):
        gift = read_gift(lines, line_number)
        if gift.name in gift_ids:
            raise InvalidInput(f'line {line_number}: the child {gift.name} is listed a second time')
        # At most one child lives in each cell, and none in Lapland.
        cell = (gift.column, gift.row)
        if cell in listed_on_line:
            raise InvalidInput(f'line {line_number}: cell {list(cell)} already holds {listed_on_line[cell]}')
        listed_on_line[cell] = f'the child on line {line_number}'
        gift_ids[gift.name] = len(gifts)
        gifts.append(gift)

    for line_number in range(range_count + gift_count + 2, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidInput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    return Problem(time_limit, reach, acceleration_ranges, gifts, gift_ids)


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


def parse_bounded_int(token: str, line_number: int, name: str, low: int, high: int) -> int:
    value = parse_int(token, line_number)
    if not low <= value <= high:
        raise InvalidOutput(f'line {line_number}: found {name} = {value}, expected {low} to {high}')
    return value


def max_acceleration(problem: Problem, weight: int) -> int:
    """The largest acceleration a_i of the range (l_i-1, l_i] that holds the weight, or 0 above the last range."""
    for weight_limit, acceleration in problem.acceleration_ranges:
        if weight <= weight_limit:
            return acceleration
    return 0


def read_gift_name(problem: Problem, token: str, line_number: int) -> int:
    if token not in problem.gift_ids:
        raise InvalidOutput(f'line {line_number}: there is no gift for a child named {token[:100]!r}')
    return problem.gift_ids[token]


def read_solution(output_file: str, problem: Problem) -> Solution:
    lines = read_lines(output_file)
    if not lines:
        raise InvalidOutput('line 1: found the end of the file, expected C')
    tokens = lines[0].split()
    if len(tokens) != 1:
        raise InvalidOutput(f'line 1: found {len(tokens)} tokens, expected C')
    action_count = parse_bounded_int(tokens[0], 1, 'C', 0, 10**6)

    reach_squared = problem.reach ** 2
    time = 0
    column, row = 0, 0
    column_speed, row_speed = 0, 0
    carrots = 0
    gift_weight = 0
    # The line of the last acceleration since the last Float, or 0 if there is none.
    acceleration_line = 0
    loaded_on_line = {}
    delivered_on_line = {}
    for line_number in range(2, action_count + 2):
        if line_number > len(lines):
            raise InvalidOutput(f'line {line_number}: found the end of the file, expected an action')
        tokens = lines[line_number - 1].split()
        if len(tokens) != 2:
            raise InvalidOutput(f'line {line_number}: found {len(tokens)} tokens, expected an action and its argument')
        action, argument = tokens

        if action in DIRECTIONS:
            acceleration = parse_int(argument, line_number)
            if acceleration_line:
                raise InvalidOutput(
                    f'line {line_number}: the sleigh accelerates again without a Float since line {acceleration_line}'
                )
            # Every acceleration, even by 0, eats a carrot.
            if carrots == 0:
                raise InvalidOutput(f'line {line_number}: the sleigh has no carrot, so it cannot accelerate')
            # The weight includes the carrot about to be eaten.
            weight = gift_weight + carrots
            limit = max_acceleration(problem, weight)
            if not 0 <= acceleration <= limit:
                raise InvalidOutput(
                    f'line {line_number}: found an acceleration of {acceleration}, expected 0 to {limit} for a sleigh '
                    f'of {weight} kg'
                )
            column_step, row_step = DIRECTIONS[action]
            column_speed += column_step * acceleration
            row_speed += row_step * acceleration
            carrots -= 1
            acceleration_line = line_number

        elif action == 'Float':
            seconds = parse_bounded_int(argument, line_number, 'the time t', 1, problem.time_limit)
            # Only floating past T is forbidden, so the instantaneous actions at second T still count.
            if time + seconds > problem.time_limit:
                raise InvalidOutput(
                    f'line {line_number}: the sleigh would float until second {time + seconds}, after the time limit '
                    f'T = {problem.time_limit}'
                )
            time += seconds
            column += column_speed * seconds
            row += row_speed * seconds
            acceleration_line = 0

        elif action == 'LoadCarrots':
            count = parse_bounded_int(argument, line_number, 'the number of carrots N', 1, 10**9)
            if column ** 2 + row ** 2 > reach_squared:
                raise InvalidOutput(
                    f'line {line_number}: the sleigh at {[column, row]} is further than D = {problem.reach} from '
                    f'[0, 0], so it cannot load carrots'
                )
            carrots += count

        elif action == 'LoadGift':
            gift_id = read_gift_name(problem, argument, line_number)
            # Each gift is loaded at most once, even after it is delivered.
            if gift_id in loaded_on_line:
                raise InvalidOutput(
                    f'line {line_number}: the gift for {argument} is loaded a second time, first loaded on line '
                    f'{loaded_on_line[gift_id]}'
                )
            if column ** 2 + row ** 2 > reach_squared:
                raise InvalidOutput(
                    f'line {line_number}: the sleigh at {[column, row]} is further than D = {problem.reach} from '
                    f'[0, 0], so it cannot load a gift'
                )
            loaded_on_line[gift_id] = line_number
            gift_weight += problem.gifts[gift_id].weight

        elif action == 'DeliverGift':
            gift_id = read_gift_name(problem, argument, line_number)
            gift = problem.gifts[gift_id]
            if gift_id in delivered_on_line:
                raise InvalidOutput(
                    f'line {line_number}: the gift for {argument} is delivered a second time, first delivered on '
                    f'line {delivered_on_line[gift_id]}'
                )
            if gift_id not in loaded_on_line:
                raise InvalidOutput(f'line {line_number}: the gift for {argument} is not on the sleigh')
            if (column - gift.column) ** 2 + (row - gift.row) ** 2 > reach_squared:
                raise InvalidOutput(
                    f'line {line_number}: the sleigh at {[column, row]} is further than D = {problem.reach} from '
                    f'{argument} at {[gift.column, gift.row]}'
                )
            delivered_on_line[gift_id] = line_number
            gift_weight -= gift.weight

        else:
            raise InvalidOutput(
                f'line {line_number}: found the action {action[:100]!r}, expected AccUp, AccDown, AccLeft, AccRight, '
                f'Float, LoadCarrots, LoadGift or DeliverGift'
            )

    for line_number in range(action_count + 2, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidOutput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    return Solution(list(delivered_on_line))


def score(problem: Problem, solution: Solution) -> int:
    return sum(problem.gifts[gift_id].score for gift_id in solution.delivered)


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
