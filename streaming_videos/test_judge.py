import os
import tempfile
import unittest

import judge

FOLDER = os.path.dirname(__file__)
EXAMPLE_IN = os.path.join(FOLDER, 'example.in')
EXAMPLE_OUT = os.path.join(FOLDER, 'example.out')

# 2 videos of 10 MB, caches of 20 MB, 1 endpoint with 100 ms to the data center, 40 ms to cache 0 and 70 ms to cache 1.
TWO_CACHES_IN = b'2 1 3 2 20\n10 10\n100 2\n0 40\n1 70\n0 0 1\n1 0 2\n0 0 1\n'


class TestJudge(unittest.TestCase):
    def score_files(self, input_data: bytes, output: bytes) -> int:
        with tempfile.TemporaryDirectory() as folder:
            input_file = os.path.join(folder, 'input.in')
            output_file = os.path.join(folder, 'output.out')
            with open(input_file, 'wb') as file:
                file.write(input_data)
            with open(output_file, 'wb') as file:
                file.write(output)
            return judge.main(input_file, output_file)

    def score_output(self, output: bytes) -> int:
        with open(EXAMPLE_IN, 'rb') as file:
            return self.score_files(file.read(), output)

    def assert_invalid(self, output: bytes, message: str) -> None:
        with self.assertRaises(judge.InvalidOutput) as context:
            self.score_output(output)
        self.assertEqual(str(context.exception), message)

    def assert_invalid_input(self, input_data: bytes) -> None:
        with self.assertRaises(judge.InvalidInput):
            self.score_files(input_data, b'0\n')

    def test_example_score_matches_statement(self) -> None:
        self.assertEqual(judge.main(EXAMPLE_IN, EXAMPLE_OUT), 462500)

    def test_no_cache_described(self) -> None:
        self.assertEqual(self.score_output(b'0\n'), 0)

    def test_cache_described_without_videos(self) -> None:
        self.assertEqual(self.score_output(b'2\n0\n1 3\n'), 1500 * 700 * 1000 // 4000)

    def test_request_takes_the_fastest_cache_holding_the_video(self) -> None:
        # Video 0 is requested twice, 1 time each, and video 1 is requested 2 times: 4 requests in total.
        self.assertEqual(self.score_files(TWO_CACHES_IN, b'2\n1 0 1\n0 0\n'), (2 * 60 + 2 * 30) * 1000 // 4)
        self.assertEqual(self.score_files(TWO_CACHES_IN, b'1\n1 0\n'), 2 * 30 * 1000 // 4)

    def test_cache_not_connected_to_the_endpoint_saves_nothing(self) -> None:
        # Endpoint 1 requests video 0, which only cache 0 holds, but endpoint 1 is not connected to any cache.
        self.assertEqual(self.score_output(b'1\n0 0\n'), 0)

    def test_score_rounds_down(self) -> None:
        # (1 * 60 + 2 * 10) * 1000 / 3 = 26666.67, rounded down to 26666.
        three_requests_in = b'2 1 2 2 10\n10 10\n100 2\n0 40\n1 90\n0 0 1\n1 0 2\n'
        self.assertEqual(self.score_files(three_requests_in, b'2\n0 0\n1 1\n'), 26666)

    def test_cache_filled_to_capacity(self) -> None:
        self.assertEqual(self.score_output(b'1\n0 0 1\n'), 1000 * 900 * 1000 // 4000)

    def test_cache_over_capacity(self) -> None:
        self.assert_invalid(b'2\n0 2\n2 0 1 3\n', 'line 3: cache 2 holds 130 MB of videos, expected at most 100 MB')

    def test_video_bigger_than_any_cache(self) -> None:
        self.assert_invalid(b'1\n0 4\n', 'line 2: cache 0 holds 110 MB of videos, expected at most 100 MB')

    def test_video_listed_twice_in_a_cache(self) -> None:
        self.assert_invalid(b'1\n1 3 3\n', 'line 2: video 3 is listed a second time for cache 1')

    def test_cache_described_twice(self) -> None:
        self.assert_invalid(
            b'2\n1 3\n1 1\n', 'line 3: cache 1 is described a second time, first described on line 2'
        )

    def test_same_video_in_several_caches(self) -> None:
        self.assertEqual(self.score_output(b'3\n0 1\n1 1\n2 1\n'), 1000 * 900 * 1000 // 4000)

    def test_cache_or_video_out_of_range(self) -> None:
        cases = [
            (b'1\n3 0\n', 'line 2: cache 3 does not exist, expected an ID from 0 to 2'),
            (b'1\n-1 0\n', 'line 2: cache -1 does not exist, expected an ID from 0 to 2'),
            (b'1\n0 5\n', 'line 2: video 5 does not exist, expected an ID from 0 to 4'),
            (b'1\n0 -1\n', 'line 2: video -1 does not exist, expected an ID from 0 to 4'),
        ]
        for output, message in cases:
            with self.subTest(output=output):
                self.assert_invalid(output, message)

    def test_description_count_out_of_range(self) -> None:
        self.assert_invalid(b'4\n0\n1\n2\n0\n', 'line 1: found N = 4, expected 0 to 3')
        self.assert_invalid(b'-1\n', 'line 1: found N = -1, expected 0 to 3')

    def test_description_count_is_alone_on_its_line(self) -> None:
        self.assert_invalid(b'1 0 2\n', 'line 1: found 3 tokens, expected N')
        self.assert_invalid(b'\n1\n0 2\n', 'line 1: found 0 tokens, expected N')

    def test_fewer_lines_than_n(self) -> None:
        self.assert_invalid(
            b'2\n0 2\n', 'line 3: found the end of the file, expected a cache ID followed by its video IDs'
        )

    def test_more_lines_than_n(self) -> None:
        self.assert_invalid(b'1\n0 2\n1 3\n', "line 3: found '1 3', expected the end of the file")

    def test_blank_line_before_the_last_cache(self) -> None:
        self.assert_invalid(
            b'2\n0 2\n\n1 3\n', 'line 3: found an empty line, expected a cache ID followed by its video IDs'
        )

    def test_any_whitespace_and_blank_lines_at_the_end(self) -> None:
        self.assertEqual(self.score_output(b' 3 \r\n0\t2\r\n1  3 1\r\n2 0 1 \r\n\r\n  \n'), 462500)

    def test_missing_newline_at_the_end(self) -> None:
        self.assertEqual(self.score_output(b'3\n0 2\n1 3 1\n2 0 1'), 462500)

    def test_empty_file(self) -> None:
        self.assert_invalid(b'', 'line 1: found the end of the file, expected N')

    def test_integers_are_parsed_strictly(self) -> None:
        for token in ['+1', '1.0', '0x1', '1_0', 'one']:
            with self.subTest(token=token):
                self.assert_invalid(f'1\n0 {token}\n'.encode('ascii'), f'line 2: found {token!r}, expected an integer')

    def test_non_ascii_byte(self) -> None:
        self.assert_invalid('1\n0 ١\n'.encode('utf-8'), 'line 2: found the byte 0xd9, expected ASCII text')

    def test_integer_with_thousands_of_digits(self) -> None:
        with self.assertRaises(judge.InvalidOutput):
            self.score_output(b'1\n0 ' + b'1' * 5000 + b'\n')

    def test_input_without_a_newline_at_the_end(self) -> None:
        self.assertEqual(self.score_files(TWO_CACHES_IN.rstrip(b'\n'), b'1\n0 0\n'), 2 * 60 * 1000 // 4)

    def test_duplicate_request_descriptions_each_count(self) -> None:
        self.assertEqual(self.score_files(TWO_CACHES_IN, b'1\n0 0\n'), 2 * 60 * 1000 // 4)

    def test_input_with_a_cache_connected_twice(self) -> None:
        self.assert_invalid_input(b'1 1 1 2 10\n10\n100 2\n0 40\n0 50\n0 0 1\n')

    def test_input_out_of_range(self) -> None:
        for input_data in [
            b'0 1 1 1 10\n\n100 0\n0 0 1\n',
            b'1 1 1 1 500001\n10\n100 0\n0 0 1\n',
            b'1 1 1 1 10\n1001\n100 0\n0 0 1\n',
            b'1 1 1 1 10\n10\n1 0\n0 0 1\n',
            b'1 1 1 1 10\n10\n100 2\n0 40\n0 40\n0 0 1\n',
            b'1 1 1 1 10\n10\n100 1\n1 40\n0 0 1\n',
            b'1 1 1 1 10\n10\n100 1\n0 100\n0 0 1\n',
            b'1 1 1 1 10\n10\n4000 1\n0 501\n0 0 1\n',
            b'1 1 1 1 10\n10\n100 0\n1 0 1\n',
            b'1 1 1 1 10\n10\n100 0\n0 1 1\n',
            b'1 1 1 1 10\n10\n100 0\n0 0 0\n',
            b'1 1 1 1 10\n10\n100 0\n0 0 10001\n',
        ]:
            with self.subTest(input_data=input_data):
                self.assert_invalid_input(input_data)

    def test_input_breaks_the_format(self) -> None:
        for input_data in [
            b'1 1 1 1\n10\n100 0\n0 0 1\n',
            b'1 1 1 1 10\n10 10\n100 0\n0 0 1\n',
            b'1 1 1 1 10\n10\n100  0\n0 0 1\n',
            b'1 1 1 1 10\r\n10\r\n100 0\r\n0 0 1\r\n',
            b'1 1 1 1 10\n+10\n100 0\n0 0 1\n',
        ]:
            with self.subTest(input_data=input_data):
                self.assert_invalid_input(input_data)

    def test_input_with_fewer_requests_than_r(self) -> None:
        self.assert_invalid_input(b'1 1 2 1 10\n10\n100 0\n0 0 1\n')

    def test_input_with_more_requests_than_r(self) -> None:
        self.assert_invalid_input(b'1 1 1 1 10\n10\n100 0\n0 0 1\n0 0 1\n')
