"""Score an output file for Hash Code 2017, Qualification Round: Streaming videos.

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
class Endpoint:
    data_center_latency: int
    latency_by_cache: dict[int, int]


@dataclasses.dataclass(frozen=True)
class Request:
    video: int
    endpoint: int
    count: int


@dataclasses.dataclass(frozen=True)
class Problem:
    cache_count: int
    cache_capacity: int
    video_sizes: list[int]
    endpoints: list[Endpoint]
    requests: list[Request]


@dataclasses.dataclass(frozen=True)
class Solution:
    videos_by_cache: dict[int, frozenset[int]]


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


def read_problem(input_file: str) -> Problem:
    with open(input_file, encoding='ascii', newline='') as file:
        lines = file.read().split('\n')

    video_count, endpoint_count, request_count, cache_count, cache_capacity = read_input_line(
        lines, 1, 5, 'V, E, R, C and X'
    )
    check_input_range(video_count, 1, 'V', 1, 10000)
    check_input_range(endpoint_count, 1, 'E', 1, 1000)
    check_input_range(request_count, 1, 'R', 1, 1000000)
    check_input_range(cache_count, 1, 'C', 1, 1000)
    check_input_range(cache_capacity, 1, 'X', 1, 500000)

    video_sizes = read_input_line(lines, 2, video_count, f'{video_count} video sizes')
    for size in video_sizes:
        check_input_range(size, 2, 'S', 1, 1000)

    line_number = 3
    endpoints = []
    for _ in range(endpoint_count):
        data_center_latency, connection_count = read_input_line(lines, line_number, 2, 'L_D and K')
        check_input_range(data_center_latency, line_number, 'L_D', 2, 4000)
        check_input_range(connection_count, line_number, 'K', 0, cache_count)
        line_number += 1

        latency_by_cache = {}
        for _ in range(connection_count):
            cache, latency = read_input_line(lines, line_number, 2, 'c and L_c')
            check_input_range(cache, line_number, 'c', 0, cache_count - 1)
            check_input_range(latency, line_number, 'L_c', 1, min(500, data_center_latency - 1))
            if cache in latency_by_cache:
                raise InvalidInput(f'line {line_number}: the endpoint is connected to cache {cache} a second time')
            latency_by_cache[cache] = latency
            line_number += 1
        endpoints.append(Endpoint(data_center_latency, latency_by_cache))

    requests = []
    for _ in range(request_count):
        video, endpoint, count = read_input_line(lines, line_number, 3, 'R_v, R_e and R_n')
        check_input_range(video, line_number, 'R_v', 0, video_count - 1)
        check_input_range(endpoint, line_number, 'R_e', 0, endpoint_count - 1)
        check_input_range(count, line_number, 'R_n', 1, 10000)
        requests.append(Request(video, endpoint, count))
        line_number += 1

    for blank_line_number in range(line_number, len(lines) + 1):
        if lines[blank_line_number - 1].split():
            raise InvalidInput(
                f'line {blank_line_number}: found {lines[blank_line_number - 1][:100]!r}, expected the end of the file'
            )

    return Problem(cache_count, cache_capacity, video_sizes, endpoints, requests)


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


def check_id(value: int, line_number: int, name: str, count: int) -> None:
    if not 0 <= value < count:
        raise InvalidOutput(
            f'line {line_number}: {name} {value} does not exist, expected an ID from 0 to {count - 1}'
        )


def read_description_count(lines: list[str], problem: Problem) -> int:
    if not lines:
        raise InvalidOutput('line 1: found the end of the file, expected N')
    tokens = lines[0].split()
    if len(tokens) != 1:
        raise InvalidOutput(f'line 1: found {len(tokens)} tokens, expected N')

    description_count = parse_int(tokens[0], 1)
    if not 0 <= description_count <= problem.cache_count:
        raise InvalidOutput(f'line 1: found N = {description_count}, expected 0 to {problem.cache_count}')
    return description_count


def read_cache_videos(lines: list[str], line_number: int, problem: Problem) -> tuple[int, frozenset[int]]:
    expected = 'a cache ID followed by its video IDs'
    if line_number > len(lines):
        raise InvalidOutput(f'line {line_number}: found the end of the file, expected {expected}')
    tokens = lines[line_number - 1].split()
    if not tokens:
        raise InvalidOutput(f'line {line_number}: found an empty line, expected {expected}')

    cache = parse_int(tokens[0], line_number)
    check_id(cache, line_number, 'cache', problem.cache_count)
    videos = set()
    for token in tokens[1:]:
        video = parse_int(token, line_number)
        check_id(video, line_number, 'video', len(problem.video_sizes))
        if video in videos:
            raise InvalidOutput(f'line {line_number}: video {video} is listed a second time for cache {cache}')
        videos.add(video)

    total_size = sum(problem.video_sizes[video] for video in videos)
    if total_size > problem.cache_capacity:
        raise InvalidOutput(
            f'line {line_number}: cache {cache} holds {total_size} MB of videos, '
            f'expected at most {problem.cache_capacity} MB'
        )
    return cache, frozenset(videos)


def read_solution(output_file: str, problem: Problem) -> Solution:
    lines = read_lines(output_file)
    description_count = read_description_count(lines, problem)

    videos_by_cache = {}
    line_by_cache = {}
    for line_number in range(2, description_count + 2):
        cache, videos = read_cache_videos(lines, line_number, problem)
        # Each cache server is described in at most one line.
        if cache in videos_by_cache:
            raise InvalidOutput(
                f'line {line_number}: cache {cache} is described a second time, first described on line '
                f'{line_by_cache[cache]}'
            )
        videos_by_cache[cache] = videos
        line_by_cache[cache] = line_number

    for line_number in range(description_count + 2, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidOutput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    return Solution(videos_by_cache)


def score(problem: Problem, solution: Solution) -> int:
    caches_by_video = [[] for _ in problem.video_sizes]
    for cache, videos in solution.videos_by_cache.items():
        for video in videos:
            caches_by_video[video].append(cache)

    saved_time = 0
    for request in problem.requests:
        endpoint = problem.endpoints[request.endpoint]
        best_latency = endpoint.data_center_latency
        for cache in caches_by_video[request.video]:
            # A cache the endpoint is not connected to cannot serve it.
            latency = endpoint.latency_by_cache.get(cache, best_latency)
            best_latency = min(best_latency, latency)
        saved_time += request.count * (endpoint.data_center_latency - best_latency)

    # The average saved time in milliseconds, times 1000 for microseconds, rounded down.
    request_total = sum(request.count for request in problem.requests)
    return saved_time * 1000 // request_total


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
