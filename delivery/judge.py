"""Score an output file for Hash Code 2016, Qualification Round: Delivery.

python3 judge.py -i example.in -o example.out
"""

import argparse
import dataclasses
import fractions
import math
import re

TOKEN_COUNTS = {'L': 5, 'U': 5, 'D': 5, 'W': 3}
EXPECTED_COMMAND = 'd L w p n, d U w p n, d D o p n or d W t'
VERBS = {'L': 'load', 'U': 'unload', 'D': 'deliver'}


class InvalidInput(Exception):
    """The input file breaks the format of the problem statement, which is a bug in the data set."""


class InvalidOutput(Exception):
    """The output file breaks a rule of the problem statement."""


@dataclasses.dataclass(frozen=True)
class Warehouse:
    row: int
    column: int
    stock: list[int]


@dataclasses.dataclass(frozen=True)
class Order:
    row: int
    column: int
    item_counts: dict[int, int]


@dataclasses.dataclass(frozen=True)
class Problem:
    row_count: int
    column_count: int
    drone_count: int
    turn_count: int
    max_load: int
    product_weights: list[int]
    warehouses: list[Warehouse]
    orders: list[Order]


@dataclasses.dataclass(frozen=True)
class Command:
    """One line of the output file. A wait has no place and no product, and its count is the number of turns."""

    drone: int
    tag: str
    place: int | None
    product: int | None
    count: int


@dataclasses.dataclass
class Drone:
    row: int
    column: int
    next_turn: int = 0
    load: int = 0
    inventory: dict[int, int] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True)
class StockChange:
    turn: int
    line_number: int
    drone: int
    warehouse: int
    product: int
    change: int


@dataclasses.dataclass(frozen=True)
class Delivery:
    order: int
    product: int
    count: int
    turn: int


@dataclasses.dataclass(frozen=True)
class Solution:
    deliveries: list[Delivery]


def read_input_line(lines: list[str], line_number: int, count: int, expected: str) -> list[int]:
    """Read count natural numbers separated by single spaces."""
    if line_number > len(lines):
        raise InvalidInput(f'line {line_number}: found the end of the file, expected {expected}')
    tokens = lines[line_number - 1].split(' ')
    if len(tokens) != count or any(re.fullmatch(r'[0-9]{1,7}', token) is None for token in tokens):
        raise InvalidInput(
            f'line {line_number}: found {lines[line_number - 1][:100]!r}, '
            f'expected {expected} separated by single spaces'
        )
    return [int(token) for token in tokens]


def check_input_range(value: int, line_number: int, name: str, low: int, high: int) -> None:
    if not low <= value <= high:
        raise InvalidInput(f'line {line_number}: found {name} = {value}, expected {low} to {high}')


def read_cell(lines: list[str], line_number: int, row_count: int, column_count: int) -> tuple[int, int]:
    row, column = read_input_line(lines, line_number, 2, 'row and column')
    check_input_range(row, line_number, 'row', 0, row_count - 1)
    check_input_range(column, line_number, 'column', 0, column_count - 1)
    return row, column


def read_problem(input_file: str) -> Problem:
    with open(input_file, encoding='ascii', newline='') as file:
        lines = file.read().split('\n')

    row_count, column_count, drone_count, turn_count, max_load = read_input_line(
        lines, 1, 5, 'rows, columns, D, T and maximum load'
    )
    check_input_range(row_count, 1, 'rows', 1, 10000)
    check_input_range(column_count, 1, 'columns', 1, 10000)
    check_input_range(drone_count, 1, 'D', 1, 1000)
    check_input_range(turn_count, 1, 'T', 1, 1000000)
    check_input_range(max_load, 1, 'maximum load', 1, 10000)

    (product_count,) = read_input_line(lines, 2, 1, 'P')
    check_input_range(product_count, 2, 'P', 1, 10000)
    product_weights = read_input_line(lines, 3, product_count, f'{product_count} product weights')
    for weight in product_weights:
        check_input_range(weight, 3, 'weight', 1, max_load)

    (warehouse_count,) = read_input_line(lines, 4, 1, 'W')
    check_input_range(warehouse_count, 4, 'W', 1, 10000)
    line_number = 5
    warehouses = []
    warehouse_cells = set()
    for _ in range(warehouse_count):
        row, column = read_cell(lines, line_number, row_count, column_count)
        if (row, column) in warehouse_cells:
            raise InvalidInput(f'line {line_number}: a second warehouse is located at [{row}, {column}]')
        warehouse_cells.add((row, column))
        stock = read_input_line(lines, line_number + 1, product_count, f'{product_count} item counts')
        for item_count in stock:
            check_input_range(item_count, line_number + 1, 'number of items', 0, 10000)
        warehouses.append(Warehouse(row, column, stock))
        line_number += 2

    (order_count,) = read_input_line(lines, line_number, 1, 'C')
    check_input_range(order_count, line_number, 'C', 1, 10000)
    line_number += 1
    orders = []
    for _ in range(order_count):
        row, column = read_cell(lines, line_number, row_count, column_count)
        if (row, column) in warehouse_cells:
            raise InvalidInput(f'line {line_number}: the order is delivered to the warehouse at [{row}, {column}]')
        (item_count,) = read_input_line(lines, line_number + 1, 1, 'L')
        check_input_range(item_count, line_number + 1, 'L', 1, 9999)
        item_counts = {}
        for product in read_input_line(lines, line_number + 2, item_count, f'{item_count} product types'):
            check_input_range(product, line_number + 2, 'product type', 0, product_count - 1)
            item_counts[product] = item_counts.get(product, 0) + 1
        orders.append(Order(row, column, item_counts))
        line_number += 3

    for blank_line_number in range(line_number, len(lines) + 1):
        if lines[blank_line_number - 1].split():
            raise InvalidInput(
                f'line {blank_line_number}: found {lines[blank_line_number - 1][:100]!r}, expected the end of the file'
            )

    for product in range(product_count):
        ordered = sum(order.item_counts.get(product, 0) for order in orders)
        stocked = sum(warehouse.stock[product] for warehouse in warehouses)
        if ordered > stocked:
            raise InvalidInput(f'product {product} is ordered {ordered} times, but the warehouses stock {stocked}')

    return Problem(row_count, column_count, drone_count, turn_count, max_load, product_weights, warehouses, orders)


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


def check_id(value: int, line_number: int, name: str, count: int) -> None:
    if not 0 <= value < count:
        raise InvalidOutput(
            f'line {line_number}: {name} {value} does not exist, expected an ID from 0 to {count - 1}'
        )


def read_command_count(lines: list[str], problem: Problem) -> int:
    if not lines:
        raise InvalidOutput('line 1: found the end of the file, expected Q')
    tokens = lines[0].split()
    if len(tokens) != 1:
        raise InvalidOutput(f'line 1: found {len(tokens)} tokens, expected Q')

    command_count = parse_int(tokens[0], 1)
    max_command_count = problem.drone_count * problem.turn_count
    if not 0 <= command_count <= max_command_count:
        raise InvalidOutput(f'line 1: found Q = {command_count}, expected 0 to {max_command_count}')
    return command_count


def read_command(lines: list[str], line_number: int, problem: Problem) -> Command:
    if line_number > len(lines):
        raise InvalidOutput(f'line {line_number}: found the end of the file, expected {EXPECTED_COMMAND}')
    tokens = lines[line_number - 1].split()
    if len(tokens) < 2:
        raise InvalidOutput(f'line {line_number}: found {len(tokens)} tokens, expected {EXPECTED_COMMAND}')
    tag = tokens[1]
    if tag not in TOKEN_COUNTS:
        raise InvalidOutput(f'line {line_number}: found the tag {tag!r}, expected L, U, D or W')
    if len(tokens) != TOKEN_COUNTS[tag]:
        raise InvalidOutput(
            f'line {line_number}: found {len(tokens)} tokens, expected {TOKEN_COUNTS[tag]} for the tag {tag}'
        )

    drone, *numbers = (parse_int(token, line_number) for token in tokens[:1] + tokens[2:])
    check_id(drone, line_number, 'drone', problem.drone_count)
    if tag == 'W':
        (turns,) = numbers
        if turns < 1:
            raise InvalidOutput(f'line {line_number}: found {turns} turns, expected a positive number')
        return Command(drone, tag, None, None, turns)

    place, product, item_count = numbers
    if tag == 'D':
        check_id(place, line_number, 'order', len(problem.orders))
    else:
        check_id(place, line_number, 'warehouse', len(problem.warehouses))
    check_id(product, line_number, 'product type', len(problem.product_weights))
    if item_count < 1:
        raise InvalidOutput(f'line {line_number}: found {item_count} items, expected a positive number')
    return Command(drone, tag, place, product, item_count)


def flight_turns(from_row: int, from_column: int, to_row: int, to_column: int) -> int:
    """The Euclidean distance between two cells, rounded up."""
    squared = (from_row - to_row) ** 2 + (from_column - to_column) ** 2
    root = math.isqrt(squared)
    return root if root * root == squared else root + 1


def check_stock(problem: Problem, stock_changes: list[StockChange]) -> None:
    stock = {}
    # In the same turn, all unloads at a warehouse happen before all loads there.
    for change in sorted(stock_changes, key=lambda change: (change.turn, change.change < 0, change.line_number)):
        key = (change.warehouse, change.product)
        available = stock.get(key, problem.warehouses[change.warehouse].stock[change.product])
        if available + change.change < 0:
            raise InvalidOutput(
                f'line {change.line_number}: warehouse {change.warehouse} holds {available} items of product type '
                f'{change.product} in turn {change.turn}, expected at least {-change.change} '
                f'for drone {change.drone} to load'
            )
        stock[key] = available + change.change


def read_solution(output_file: str, problem: Problem) -> Solution:
    lines = read_lines(output_file)
    command_count = read_command_count(lines, problem)

    first_warehouse = problem.warehouses[0]
    drones = [Drone(first_warehouse.row, first_warehouse.column) for _ in range(problem.drone_count)]
    delivered = [{} for _ in problem.orders]
    stock_changes = []
    deliveries = []
    for line_number in range(2, command_count + 2):
        command = read_command(lines, line_number, problem)
        drone = drones[command.drone]

        if command.place is None or command.product is None:
            drone.next_turn += command.count
            if drone.next_turn > problem.turn_count:
                raise InvalidOutput(
                    f'line {line_number}: drone {command.drone} waits until turn {drone.next_turn - 1}, '
                    f'expected at most turn {problem.turn_count - 1}'
                )
            continue

        destination = problem.orders[command.place] if command.tag == 'D' else problem.warehouses[command.place]
        turn = drone.next_turn + flight_turns(drone.row, drone.column, destination.row, destination.column)
        if turn >= problem.turn_count:
            raise InvalidOutput(
                f'line {line_number}: drone {command.drone} would {VERBS[command.tag]} in turn {turn}, '
                f'expected at most turn {problem.turn_count - 1}'
            )
        drone.row, drone.column, drone.next_turn = destination.row, destination.column, turn + 1

        carried = drone.inventory.get(command.product, 0)
        weight = command.count * problem.product_weights[command.product]
        if command.tag == 'L':
            if drone.load + weight > problem.max_load:
                raise InvalidOutput(
                    f'line {line_number}: drone {command.drone} would carry a weight of {drone.load + weight}, '
                    f'expected at most {problem.max_load}'
                )
            drone.load += weight
            drone.inventory[command.product] = carried + command.count
            stock_changes.append(
                StockChange(turn, line_number, command.drone, command.place, command.product, -command.count)
            )
            continue

        if carried < command.count:
            raise InvalidOutput(
                f'line {line_number}: drone {command.drone} carries {carried} items of product type '
                f'{command.product}, expected at least {command.count} to {VERBS[command.tag]}'
            )
        drone.load -= weight
        drone.inventory[command.product] = carried - command.count
        if command.tag == 'U':
            stock_changes.append(
                StockChange(turn, line_number, command.drone, command.place, command.product, command.count)
            )
            continue

        # No order receives more items of a product type than it ordered.
        order_delivered = delivered[command.place]
        total = order_delivered.get(command.product, 0) + command.count
        ordered = problem.orders[command.place].item_counts.get(command.product, 0)
        if total > ordered:
            raise InvalidOutput(
                f'line {line_number}: order {command.place} would receive {total} items of product type '
                f'{command.product}, expected at most {ordered}'
            )
        order_delivered[command.product] = total
        deliveries.append(Delivery(command.place, command.product, command.count, turn))

    for line_number in range(command_count + 2, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidOutput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    check_stock(problem, stock_changes)
    return Solution(deliveries)


def score(problem: Problem, solution: Solution) -> int:
    delivered = [{} for _ in problem.orders]
    completion_turns = [0] * len(problem.orders)
    for delivery in solution.deliveries:
        order_delivered = delivered[delivery.order]
        order_delivered[delivery.product] = order_delivered.get(delivery.product, 0) + delivery.count
        completion_turns[delivery.order] = max(completion_turns[delivery.order], delivery.turn)

    total = 0
    turn_count = problem.turn_count
    for order, order_delivered, turn in zip(problem.orders, delivered, completion_turns):
        if order_delivered == order.item_counts:
            total += math.ceil(fractions.Fraction(turn_count - turn, turn_count) * 100)
    return total


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
