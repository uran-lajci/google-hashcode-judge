"""Score an output file for Hash Code 2020, Qualification Round: Book scanning.

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
class Library:
    signup_days: int
    books_per_day: int
    books: frozenset[int]


@dataclasses.dataclass(frozen=True)
class Problem:
    day_count: int
    book_scores: list[int]
    libraries: list[Library]


@dataclasses.dataclass(frozen=True)
class Signup:
    library: int
    books: list[int]


@dataclasses.dataclass(frozen=True)
class Solution:
    signups: list[Signup]


def read_input_line(lines: list[str], line_number: int, expected: str) -> list[int]:
    if line_number > len(lines):
        raise InvalidInput(f'line {line_number}: found the end of the file, expected {expected}')
    line = lines[line_number - 1]
    if re.fullmatch(r'[0-9]{1,6}( [0-9]{1,6})*', line) is None:
        raise InvalidInput(
            f'line {line_number}: found {line[:100]!r}, expected {expected} as integers separated by single spaces'
        )
    return [int(token) for token in line.split(' ')]


def check_input_count(numbers: list[int], line_number: int, expected: str, count: int) -> None:
    if len(numbers) != count:
        raise InvalidInput(f'line {line_number}: found {len(numbers)} integers, expected {count} for {expected}')


def check_input_range(value: int, line_number: int, name: str, low: int, high: int) -> None:
    if not low <= value <= high:
        raise InvalidInput(f'line {line_number}: found {name} = {value}, expected {low} to {high}')


def read_library(lines: list[str], line_number: int, book_count: int) -> Library:
    expected = 'N, T and M'
    numbers = read_input_line(lines, line_number, expected)
    check_input_count(numbers, line_number, expected, 3)
    library_book_count, signup_days, books_per_day = numbers
    check_input_range(library_book_count, line_number, 'N', 1, 100_000)
    check_input_range(signup_days, line_number, 'T', 1, 100_000)
    check_input_range(books_per_day, line_number, 'M', 1, 100_000)

    expected = 'the IDs of the books in the library'
    books = read_input_line(lines, line_number + 1, expected)
    check_input_count(books, line_number + 1, expected, library_book_count)
    for book in books:
        check_input_range(book, line_number + 1, 'a book ID', 0, book_count - 1)
    # Each book ID is listed at most once per library.
    if len(frozenset(books)) != library_book_count:
        raise InvalidInput(f'line {line_number + 1}: found a book twice, expected N different books')

    return Library(signup_days, books_per_day, frozenset(books))


def read_problem(input_file: str) -> Problem:
    with open(input_file, encoding='ascii', newline='') as file:
        lines = file.read().split('\n')

    expected = 'B, L and D'
    numbers = read_input_line(lines, 1, expected)
    check_input_count(numbers, 1, expected, 3)
    book_count, library_count, day_count = numbers
    check_input_range(book_count, 1, 'B', 1, 100_000)
    check_input_range(library_count, 1, 'L', 1, 100_000)
    check_input_range(day_count, 1, 'D', 1, 100_000)

    expected = 'the scores of the books'
    book_scores = read_input_line(lines, 2, expected)
    check_input_count(book_scores, 2, expected, book_count)
    for book_score in book_scores:
        check_input_range(book_score, 2, 'a book score', 0, 1000)

    libraries = [read_library(lines, line_number, book_count) for line_number in range(3, 2 * library_count + 3, 2)]
    total = sum(len(library.books) for library in libraries)
    if total > 1_000_000:
        raise InvalidInput(f'found {total} books in all libraries, expected at most 1000000')

    for line_number in range(2 * library_count + 3, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidInput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    return Problem(day_count, book_scores, libraries)


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


def read_signup_count(lines: list[str], problem: Problem) -> int:
    if not lines:
        raise InvalidOutput('line 1: found the end of the file, expected A')
    tokens = lines[0].split()
    if len(tokens) != 1:
        raise InvalidOutput(f'line 1: found {len(tokens)} tokens, expected A')

    signup_count = parse_int(tokens[0], 1)
    library_count = len(problem.libraries)
    if not 0 <= signup_count <= library_count:
        raise InvalidOutput(f'line 1: found A = {signup_count}, expected 0 to L = {library_count}')
    return signup_count


def read_library_line(
    lines: list[str],
    line_number: int,
    problem: Problem,
    described_on_line: list[int],
) -> tuple[int, int]:
    expected = 'the library ID Y and the book count K'
    if line_number > len(lines):
        raise InvalidOutput(f'line {line_number}: found the end of the file, expected {expected}')
    tokens = lines[line_number - 1].split()
    if len(tokens) != 2:
        raise InvalidOutput(f'line {line_number}: found {len(tokens)} tokens, expected {expected}')
    library, book_count = (parse_int(token, line_number) for token in tokens)

    library_count = len(problem.libraries)
    if not 0 <= library < library_count:
        raise InvalidOutput(
            f'line {line_number}: library {library} does not exist, expected an ID from 0 to {library_count - 1}'
        )
    # Each library must be described only once.
    if described_on_line[library]:
        raise InvalidOutput(
            f'line {line_number}: library {library} is described a second time, first described on line '
            f'{described_on_line[library]}'
        )
    library_book_count = len(problem.libraries[library].books)
    if not 1 <= book_count <= library_book_count:
        raise InvalidOutput(
            f'line {line_number}: found K = {book_count}, expected 1 to N = {library_book_count} for library {library}'
        )
    return library, book_count


def read_books_line(lines: list[str], line_number: int, problem: Problem, library: int, book_count: int) -> list[int]:
    expected = f'K = {book_count} book IDs'
    if line_number > len(lines):
        raise InvalidOutput(f'line {line_number}: found the end of the file, expected {expected}')
    tokens = lines[line_number - 1].split()
    if len(tokens) != book_count:
        raise InvalidOutput(f'line {line_number}: found {len(tokens)} book IDs, expected {expected}')

    book_ids = len(problem.book_scores)
    library_books = problem.libraries[library].books
    books = []
    listed = set()
    for token in tokens:
        book = parse_int(token, line_number)
        if not 0 <= book < book_ids:
            raise InvalidOutput(
                f'line {line_number}: book {book} does not exist, expected an ID from 0 to {book_ids - 1}'
            )
        # Books are shipped from the library that holds them, even when they ship after the deadline.
        if book not in library_books:
            raise InvalidOutput(f'line {line_number}: book {book} is not in library {library}')
        if book in listed:
            raise InvalidOutput(
                f'line {line_number}: book {book} is listed a second time for library {library}, '
                'expected no duplicates'
            )
        listed.add(book)
        books.append(book)
    return books


def read_solution(output_file: str, problem: Problem) -> Solution:
    lines = read_lines(output_file)
    signup_count = read_signup_count(lines, problem)

    # The line that describes each library, or 0 while no line describes it.
    described_on_line = [0] * len(problem.libraries)
    signups = []
    for line_number in range(2, 2 * signup_count + 2, 2):
        library, book_count = read_library_line(lines, line_number, problem, described_on_line)
        described_on_line[library] = line_number
        books = read_books_line(lines, line_number + 1, problem, library, book_count)
        signups.append(Signup(library, books))

    for line_number in range(2 * signup_count + 2, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidOutput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    return Solution(signups)


def score(problem: Problem, solution: Solution) -> int:
    scanned = set()
    first_scan_day = 0
    for signup in solution.signups:
        library = problem.libraries[signup.library]
        # Signups run one after another, and a library ships books from the day after its signup ends.
        first_scan_day += library.signup_days
        scan_days = max(0, problem.day_count - first_scan_day)
        scanned.update(signup.books[:scan_days * library.books_per_day])
    return sum(problem.book_scores[book] for book in scanned)


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
