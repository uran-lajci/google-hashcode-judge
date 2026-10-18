"""Score an output file for Hash Code 2016, Final Round: Satellites.

python3 judge.py -i example.in -o example.out
"""

import argparse
import bisect
import dataclasses
import re

QUARTER_TURN = 324000
HALF_TURN = 648000
FULL_TURN = 1296000
EARTH_ROTATION = 15
MAX_IMAGE_LATITUDE = 306000


class InvalidInput(Exception):
    """The input file breaks the format of the problem statement, which is a bug in the data set."""


class InvalidOutput(Exception):
    """The output file breaks a rule of the problem statement."""


def wrap_longitude(longitude: int) -> int:
    """Wrap a longitude into -648000 to 647999, so that -648001 becomes 647999."""
    return (longitude + HALF_TURN) % FULL_TURN - HALF_TURN


@dataclasses.dataclass(frozen=True)
class Satellite:
    latitude: int
    longitude: int
    velocity: int
    max_orientation_change: int
    max_orientation: int

    def position(self, turn: int) -> tuple[int, int]:
        """Return [φ, λ] at the turn, as the movement table of the statement gives it turn by turn."""
        # Mirroring a southbound satellite makes it northbound and turns the South Pole rule into the North Pole rule.
        direction = 1 if self.velocity > 0 else -1
        unfolded = direction * self.latitude + abs(self.velocity) * turn
        # The satellite flies over a pole each time the unfolded latitude passes 90°, 270°, 450° and so on.
        # Reaching exactly 90° is not a crossing: the table moves on normally while φ + v ≤ 90°.
        crossings = 0 if unfolded <= QUARTER_TURN else (unfolded - QUARTER_TURN - 1) // HALF_TURN + 1
        if crossings % 2 == 0:
            latitude = unfolded - HALF_TURN * crossings
        else:
            latitude = HALF_TURN * crossings - unfolded
        # Each crossing adds -180° to the longitude, on top of the rotation of the Earth.
        longitude = wrap_longitude(self.longitude - EARTH_ROTATION * turn - HALF_TURN * crossings)
        return direction * latitude, longitude


@dataclasses.dataclass(frozen=True)
class Collection:
    value: int
    locations: list[tuple[int, int]]
    ranges: list[tuple[int, int]]


@dataclasses.dataclass(frozen=True)
class Problem:
    turns: int
    satellites: list[Satellite]
    collections: list[Collection]


@dataclasses.dataclass(frozen=True)
class Image:
    latitude: int
    longitude: int
    turn: int
    satellite: int
    line_number: int


@dataclasses.dataclass(frozen=True)
class Solution:
    images: list[Image]


def read_input_line(lines: list[str], line_number: int, count: int, expected: str) -> list[int]:
    """Read count integers separated by single spaces."""
    if line_number > len(lines):
        raise InvalidInput(f'line {line_number}: found the end of the file, expected {expected}')
    tokens = lines[line_number - 1].split(' ')
    if len(tokens) != count or any(re.fullmatch(r'-?[0-9]{1,10}', token) is None for token in tokens):
        raise InvalidInput(
            f'line {line_number}: found {lines[line_number - 1][:100]!r}, '
            f'expected {expected} separated by single spaces'
        )
    return [int(token) for token in tokens]


def check_input_range(value: int, line_number: int, name: str, low: int, high: int) -> None:
    if not low <= value <= high:
        raise InvalidInput(f'line {line_number}: found {name} = {value}, expected {low} to {high}')


def read_satellite(lines: list[str], line_number: int) -> Satellite:
    latitude, longitude, velocity, max_orientation_change, max_orientation = read_input_line(
        lines, line_number, 5, 'φ, λ, v, w and d'
    )
    check_input_range(latitude, line_number, 'φ', -QUARTER_TURN, QUARTER_TURN)
    check_input_range(longitude, line_number, 'λ', -HALF_TURN, HALF_TURN - 1)
    check_input_range(abs(velocity), line_number, '|v|', 100, 500)
    check_input_range(max_orientation_change, line_number, 'w', 0, 200)
    check_input_range(max_orientation, line_number, 'd', 0, 10000)
    return Satellite(latitude, longitude, velocity, max_orientation_change, max_orientation)


def read_collection(lines: list[str], line_number: int, turns: int) -> Collection:
    """Read the collection that starts on the line. The collection ends on line + L + R."""
    value, location_count, range_count = read_input_line(lines, line_number, 3, 'V, L and R')
    check_input_range(value, line_number, 'V', 0, 10000)
    check_input_range(location_count, line_number, 'L', 1, 100)
    check_input_range(range_count, line_number, 'R', 1, 100)

    locations = []
    for location_line in range(line_number + 1, line_number + location_count + 1):
        latitude, longitude = read_input_line(lines, location_line, 2, 'φ and λ')
        check_input_range(latitude, location_line, 'φ', -MAX_IMAGE_LATITUDE, MAX_IMAGE_LATITUDE)
        check_input_range(longitude, location_line, 'λ', -HALF_TURN, HALF_TURN - 1)
        locations.append((latitude, longitude))

    ranges = []
    first_range_line = line_number + location_count + 1
    for range_line in range(first_range_line, first_range_line + range_count):
        start, end = read_input_line(lines, range_line, 2, 't_start and t_end')
        check_input_range(start, range_line, 't_start', 0, turns - 1)
        check_input_range(end, range_line, 't_end', start, turns - 1)
        ranges.append((start, end))

    # The ranges of a collection do not overlap.
    ranges.sort()
    for (_, previous_end), (start, _) in zip(ranges, ranges[1:]):
        if start <= previous_end:
            raise InvalidInput(f'line {line_number}: the time ranges of this collection overlap at turn {start}')
    return Collection(value, locations, ranges)


def read_problem(input_file: str) -> Problem:
    with open(input_file, encoding='ascii', newline='') as file:
        lines = file.read().split('\n')

    (turns,) = read_input_line(lines, 1, 1, 'T')
    check_input_range(turns, 1, 'T', 1, 604800)

    (satellite_count,) = read_input_line(lines, 2, 1, 'S')
    check_input_range(satellite_count, 2, 'S', 1, 100)
    satellites = [read_satellite(lines, line_number) for line_number in range(3, satellite_count + 3)]

    line_number = satellite_count + 3
    (collection_count,) = read_input_line(lines, line_number, 1, 'C')
    check_input_range(collection_count, line_number, 'C', 0, 10000)
    line_number += 1

    collections = []
    for _ in range(collection_count):
        collection = read_collection(lines, line_number, turns)
        collections.append(collection)
        line_number += 1 + len(collection.locations) + len(collection.ranges)

    for line_number in range(line_number, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidInput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    return Problem(turns, satellites, collections)


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


def read_output_line(lines: list[str], line_number: int, count: int, expected: str) -> list[int]:
    if line_number > len(lines):
        raise InvalidOutput(f'line {line_number}: found the end of the file, expected {expected}')
    tokens = lines[line_number - 1].split()
    if not tokens:
        raise InvalidOutput(f'line {line_number}: found an empty line, expected {expected}')
    if len(tokens) != count:
        raise InvalidOutput(f'line {line_number}: found {len(tokens)} values, expected {count}: {expected}')
    return [parse_int(token, line_number) for token in tokens]


def check_output_range(value: int, line_number: int, name: str, low: int, high: int) -> None:
    if not low <= value <= high:
        raise InvalidOutput(f'line {line_number}: found {name} = {value}, expected {low} to {high}')


def orientation(problem: Problem, image: Image) -> tuple[int, int]:
    """Return the orientation [Δφ, Δλ] that points the camera of the satellite at the image."""
    latitude, longitude = problem.satellites[image.satellite].position(image.turn)
    # The camera points at λ + Δλ, which wraps around like any longitude, so Δλ is the shortest way round.
    return image.latitude - latitude, wrap_longitude(image.longitude - longitude)


def read_image(lines: list[str], line_number: int, problem: Problem) -> Image:
    latitude, longitude, turn, satellite = read_output_line(lines, line_number, 4, 'φ, λ, t and s')
    check_output_range(latitude, line_number, 'φ', -MAX_IMAGE_LATITUDE, MAX_IMAGE_LATITUDE)
    check_output_range(longitude, line_number, 'λ', -HALF_TURN, HALF_TURN - 1)
    check_output_range(turn, line_number, 't', 0, problem.turns - 1)
    check_output_range(satellite, line_number, 's', 0, len(problem.satellites) - 1)
    image = Image(latitude, longitude, turn, satellite, line_number)

    # Each picture is in range of the satellite when it is taken.
    max_orientation = problem.satellites[satellite].max_orientation
    delta_latitude, delta_longitude = orientation(problem, image)
    if abs(delta_latitude) > max_orientation or abs(delta_longitude) > max_orientation:
        raise InvalidOutput(
            f'line {line_number}: satellite {satellite} needs the orientation [{delta_latitude}, {delta_longitude}] '
            f'at turn {turn}, expected each value from -{max_orientation} to {max_orientation}'
        )
    return image


def check_camera_speed(problem: Problem, images: list[Image]) -> None:
    """Check that no satellite turns its camera faster than w arcseconds per turn, starting from [0, 0] at turn 0."""
    images_by_satellite = [[] for _ in problem.satellites]
    for image in images:
        images_by_satellite[image.satellite].append(image)

    for satellite_id, satellite_images in enumerate(images_by_satellite):
        max_change = problem.satellites[satellite_id].max_orientation_change
        previous_turn, previous_orientation, previous_place = 0, (0, 0), 'the start'
        for image in sorted(satellite_images, key=lambda image: image.turn):
            delta_latitude, delta_longitude = orientation(problem, image)
            elapsed = image.turn - previous_turn
            change = max(
                abs(delta_latitude - previous_orientation[0]), abs(delta_longitude - previous_orientation[1])
            )
            if change > max_change * elapsed:
                raise InvalidOutput(
                    f'line {image.line_number}: satellite {satellite_id} turns its camera from '
                    f'[{previous_orientation[0]}, {previous_orientation[1]}] at turn {previous_turn} '
                    f'({previous_place}) to [{delta_latitude}, {delta_longitude}] at turn {image.turn}, '
                    f'a change of {change} in {elapsed} turns, expected at most w * {elapsed} = {max_change * elapsed}'
                )
            previous_turn, previous_orientation = image.turn, (delta_latitude, delta_longitude)
            previous_place = f'line {image.line_number}'


def read_solution(output_file: str, problem: Problem) -> Solution:
    lines = read_lines(output_file)

    (image_count,) = read_output_line(lines, 1, 1, 'P')
    location_count = sum(len(collection.locations) for collection in problem.collections)
    # P cannot be bigger than the total number of location entries in all collections.
    check_output_range(image_count, 1, 'P', 0, location_count)

    images = []
    line_by_satellite_turn = {}
    for line_number in range(2, image_count + 2):
        image = read_image(lines, line_number, problem)
        # Each satellite can take one image per turn at most.
        key = (image.satellite, image.turn)
        if key in line_by_satellite_turn:
            raise InvalidOutput(
                f'line {line_number}: satellite {image.satellite} takes a second image at turn {image.turn}, '
                f'first taken on line {line_by_satellite_turn[key]}'
            )
        line_by_satellite_turn[key] = line_number
        images.append(image)

    for line_number in range(image_count + 2, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidOutput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    check_camera_speed(problem, images)
    return Solution(images)


def in_ranges(turn: int, ranges: list[tuple[int, int]]) -> bool:
    """Tell whether the turn falls in one of the sorted, non-overlapping ranges."""
    index = bisect.bisect_right(ranges, turn, key=lambda turn_range: turn_range[0]) - 1
    return index >= 0 and ranges[index][1] >= turn


def score(problem: Problem, solution: Solution) -> int:
    turns_by_location = {}
    for image in solution.images:
        turns_by_location.setdefault((image.latitude, image.longitude), []).append(image.turn)

    points = 0
    for collection in problem.collections:
        # Each location needs an image in one of the ranges; different locations may use different ranges.
        if all(
            any(in_ranges(turn, collection.ranges) for turn in turns_by_location.get(location, []))
            for location in collection.locations
        ):
            points += collection.value
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
