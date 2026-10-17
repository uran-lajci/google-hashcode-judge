"""Score an output file for Hash Code 2019, Qualification Round: Photo slideshow.

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
class Photo:
    is_vertical: bool
    tags: frozenset[str]


@dataclasses.dataclass(frozen=True)
class Problem:
    photos: list[Photo]


@dataclasses.dataclass(frozen=True)
class Solution:
    slides: list[list[int]]


def parse_input_int(token: str, line_number: int, name: str, low: int, high: int) -> int:
    if re.fullmatch(r'[0-9]{1,6}', token) is None or not low <= int(token) <= high:
        raise InvalidInput(f'line {line_number}: found {name} = {token!r}, expected an integer from {low} to {high}')
    return int(token)


def read_photo(lines: list[str], line_number: int) -> Photo:
    expected = 'a photo as H or V, M and M tags separated by single spaces'
    if line_number > len(lines):
        raise InvalidInput(f'line {line_number}: found the end of the file, expected {expected}')
    tokens = lines[line_number - 1].split(' ')
    if len(tokens) < 2 or tokens[0] not in ('H', 'V'):
        raise InvalidInput(f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected {expected}')

    tag_count = parse_input_int(tokens[1], line_number, 'M', 1, 100)
    tags = tokens[2:]
    if len(tags) != tag_count:
        raise InvalidInput(f'line {line_number}: found {len(tags)} tags, expected M = {tag_count}')
    for tag in tags:
        if re.fullmatch(r'[a-z0-9]{1,10}', tag) is None:
            raise InvalidInput(
                f'line {line_number}: found the tag {tag[:100]!r}, '
                'expected 1 to 10 lowercase ASCII letters and digits'
            )
    # A photo is described by a set of tags.
    if len(frozenset(tags)) != tag_count:
        raise InvalidInput(f'line {line_number}: found a tag twice, expected M different tags')

    return Photo(tokens[0] == 'V', frozenset(tags))


def read_problem(input_file: str) -> Problem:
    with open(input_file, encoding='ascii', newline='') as file:
        lines = file.read().split('\n')

    photo_count = parse_input_int(lines[0], 1, 'N', 1, 100_000)
    photos = [read_photo(lines, line_number) for line_number in range(2, photo_count + 2)]

    for line_number in range(photo_count + 2, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidInput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    return Problem(photos)


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


def read_slide_count(lines: list[str], problem: Problem) -> int:
    if not lines:
        raise InvalidOutput('line 1: found the end of the file, expected S')
    tokens = lines[0].split()
    if len(tokens) != 1:
        raise InvalidOutput(f'line 1: found {len(tokens)} tokens, expected S')

    slide_count = parse_int(tokens[0], 1)
    photo_count = len(problem.photos)
    # The slideshow must have at least one slide.
    if not 1 <= slide_count <= photo_count:
        raise InvalidOutput(f'line 1: found S = {slide_count}, expected 1 to N = {photo_count}')
    return slide_count


def read_slide(lines: list[str], line_number: int, problem: Problem) -> list[int]:
    expected = 'one horizontal photo or two vertical photos'
    if line_number > len(lines):
        raise InvalidOutput(f'line {line_number}: found the end of the file, expected {expected}')
    tokens = lines[line_number - 1].split()
    if not 1 <= len(tokens) <= 2:
        raise InvalidOutput(f'line {line_number}: found {len(tokens)} photo IDs, expected {expected}')

    photo_count = len(problem.photos)
    slide = []
    for token in tokens:
        photo = parse_int(token, line_number)
        if not 0 <= photo < photo_count:
            raise InvalidOutput(
                f'line {line_number}: photo {photo} does not exist, expected an ID from 0 to {photo_count - 1}'
            )
        # A slide holds a single horizontal photo or two vertical photos side by side.
        is_vertical = problem.photos[photo].is_vertical
        if len(tokens) == 1 and is_vertical:
            raise InvalidOutput(f'line {line_number}: photo {photo} is vertical, expected a horizontal photo')
        if len(tokens) == 2 and not is_vertical:
            raise InvalidOutput(f'line {line_number}: photo {photo} is horizontal, expected two vertical photos')
        slide.append(photo)
    return slide


def read_solution(output_file: str, problem: Problem) -> Solution:
    lines = read_lines(output_file)
    slide_count = read_slide_count(lines, problem)

    # The line of the slide that holds each photo, or 0 while no slide holds it.
    used_on_line = [0] * len(problem.photos)
    slides = []
    for line_number in range(2, slide_count + 2):
        slide = read_slide(lines, line_number, problem)
        # Each photo is used once or not at all, which also forbids the same vertical photo twice on one slide.
        for photo in slide:
            if used_on_line[photo]:
                raise InvalidOutput(
                    f'line {line_number}: photo {photo} is used a second time, first used on line '
                    f'{used_on_line[photo]}'
                )
            used_on_line[photo] = line_number
        slides.append(slide)

    for line_number in range(slide_count + 2, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidOutput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    return Solution(slides)


def interest_factor(tags: frozenset[str], next_tags: frozenset[str]) -> int:
    common = len(tags & next_tags)
    return min(common, len(tags) - common, len(next_tags) - common)


def score(problem: Problem, solution: Solution) -> int:
    tags_by_slide = [frozenset().union(*(problem.photos[photo].tags for photo in slide)) for slide in solution.slides]
    return sum(interest_factor(tags, next_tags) for tags, next_tags in zip(tags_by_slide, tags_by_slide[1:]))


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
