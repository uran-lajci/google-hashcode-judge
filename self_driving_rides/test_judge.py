import os
import tempfile
import unittest

import judge

FOLDER = os.path.dirname(__file__)
EXAMPLE_IN = os.path.join(FOLDER, 'example.in')
EXAMPLE_OUT = os.path.join(FOLDER, 'example.out')

# 1 vehicle, bonus 5, 10 steps. Ride 0 goes from [0, 1] to [0, 3] with latest finish 2, so the vehicle, which arrives at
# step 1, finishes it late at step 3. Ride 1 goes from [0, 0] to [0, 2] with latest finish 8.
LATE_RIDE_IN = b'1 10 1 2 5 10\n0 1 0 3 0 2\n0 0 0 2 0 8\n'


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
        self.assertEqual(judge.main(EXAMPLE_IN, EXAMPLE_OUT), 10)

    def test_no_ride_assigned(self) -> None:
        self.assertEqual(self.score_output(b'0\n0\n'), 0)

    def test_bonus_only_when_the_ride_starts_at_its_earliest_start(self) -> None:
        # Ride 0 is reached at step 0 and waits until its earliest start 2. Ride 2 is reached at step 2, after 0.
        self.assertEqual(self.score_output(b'1 0\n0\n'), 4 + 2)
        self.assertEqual(self.score_output(b'0\n1 2\n'), 2)

    def test_bonus_when_the_vehicle_arrives_exactly_at_the_earliest_start(self) -> None:
        # The vehicle reaches [0, 2] at step 2, the earliest start, and finishes at [0, 4] at step 4.
        self.assertEqual(self.score_files(b'1 5 1 1 3 10\n0 2 0 4 2 9\n', b'1 0\n'), 2 + 3)

    def test_ride_finishing_at_its_latest_finish_counts(self) -> None:
        # The statement's example: distance 3 and latest finish 3 is on time from step 0, but late from step 1.
        self.assertEqual(self.score_files(b'1 5 1 1 1 10\n0 0 0 3 0 3\n', b'1 0\n'), 3 + 1)
        self.assertEqual(self.score_files(b'1 5 1 1 1 10\n0 1 0 4 0 3\n', b'1 0\n'), 0)

    def test_ride_finishing_at_the_last_step_counts(self) -> None:
        # The latest finish equals T, so the ride is over exactly when the simulation ends.
        self.assertEqual(self.score_files(b'1 5 1 1 1 4\n0 1 0 4 1 4\n', b'1 0\n'), 3 + 1)

    def test_late_ride_still_moves_the_vehicle(self) -> None:
        self.assertEqual(self.score_files(LATE_RIDE_IN, b'1 1\n'), 2 + 5)
        # After the late ride the vehicle is at [0, 3] at step 3, back at [0, 0] at step 6 and finishes at step 8.
        self.assertEqual(self.score_files(LATE_RIDE_IN, b'2 0 1\n'), 2)

    def test_next_ride_starts_where_the_last_one_finished(self) -> None:
        # Ride 1 finishes at [0, 2] at step 2, and ride 0 starts there at step 2, its earliest start.
        input_data = b'1 5 1 2 3 10\n0 2 0 4 2 4\n0 0 0 2 0 2\n'
        self.assertEqual(self.score_files(input_data, b'2 1 0\n'), (2 + 3) + (2 + 3))

    def test_ride_assigned_to_two_vehicles(self) -> None:
        self.assert_invalid(b'1 0\n1 0\n', 'line 2: ride 0 is assigned a second time, first assigned on line 1')

    def test_ride_assigned_twice_to_one_vehicle(self) -> None:
        self.assert_invalid(b'2 1 1\n0\n', 'line 1: ride 1 is assigned a second time, first assigned on line 1')

    def test_ride_out_of_range(self) -> None:
        cases = [
            (b'1 3\n0\n', 'line 1: ride 3 does not exist, expected an ID from 0 to 2'),
            (b'0\n1 -1\n', 'line 2: ride -1 does not exist, expected an ID from 0 to 2'),
        ]
        for output, message in cases:
            with self.subTest(output=output):
                self.assert_invalid(output, message)

    def test_ride_count_out_of_range(self) -> None:
        self.assert_invalid(b'4 0 1 2 0\n0\n', 'line 1: found M = 4, expected 0 to 3')
        self.assert_invalid(b'-1\n0\n', 'line 1: found M = -1, expected 0 to 3')

    def test_ride_count_does_not_match_the_rides_that_follow(self) -> None:
        self.assert_invalid(b'2 0\n0\n', 'line 1: found M = 2, but the number of rides that follow is 1')
        self.assert_invalid(b'1 0\n1 2 1\n', 'line 2: found M = 1, but the number of rides that follow is 2')

    def test_fewer_lines_than_vehicles(self) -> None:
        self.assert_invalid(
            b'1 0\n', 'line 2: found the end of the file, expected M followed by the rides of vehicle 1'
        )

    def test_more_lines_than_vehicles(self) -> None:
        self.assert_invalid(b'1 0\n2 2 1\n0\n', "line 3: found '0', expected the end of the file")

    def test_blank_line_for_a_vehicle(self) -> None:
        self.assert_invalid(
            b'1 0\n\n2 2 1\n', 'line 2: found an empty line, expected M followed by the rides of vehicle 1'
        )

    def test_any_whitespace_and_blank_lines_at_the_end(self) -> None:
        self.assertEqual(self.score_output(b' 1\t0 \r\n2  2 1\r\n\r\n  \n'), 10)

    def test_missing_newline_at_the_end(self) -> None:
        self.assertEqual(self.score_output(b'1 0\n2 2 1'), 10)

    def test_empty_file(self) -> None:
        self.assert_invalid(b'', 'line 1: found the end of the file, expected M followed by the rides of vehicle 0')

    def test_integers_are_parsed_strictly(self) -> None:
        for token in ['+1', '1.0', '0x1', '1_0', 'one']:
            with self.subTest(token=token):
                self.assert_invalid(f'1 {token}\n0\n'.encode('ascii'), f'line 1: found {token!r}, expected an integer')

    def test_non_ascii_byte(self) -> None:
        self.assert_invalid('1 0\n1 ١\n'.encode('utf-8'), 'line 2: found the byte 0xd9, expected ASCII text')

    def test_integer_with_thousands_of_digits(self) -> None:
        with self.assertRaises(judge.InvalidOutput):
            self.score_output(b'1 ' + b'1' * 5000 + b'\n0\n')

    def test_input_without_a_newline_at_the_end(self) -> None:
        self.assertEqual(self.score_files(LATE_RIDE_IN.rstrip(b'\n'), b'1 1\n'), 2 + 5)

    def test_input_out_of_range(self) -> None:
        for input_data in [
            b'0 5 1 1 1 10\n0 0 0 3 0 3\n',
            b'1 10001 1 1 1 10\n0 0 0 3 0 3\n',
            b'1 5 0 1 1 10\n0 0 0 3 0 3\n',
            b'1 5 1001 1 1 10\n0 0 0 3 0 3\n',
            b'1 5 1 0 1 10\n',
            b'1 5 1 1 0 10\n0 0 0 3 0 3\n',
            b'1 5 1 1 1 0\n0 0 0 3 0 3\n',
            b'1 5 1 1 1 1000000001\n0 0 0 3 0 3\n',
            b'1 5 1 1 1 10\n1 0 0 3 0 3\n',
            b'1 5 1 1 1 10\n0 5 0 3 0 3\n',
            b'1 5 1 1 1 10\n0 0 1 3 0 3\n',
            b'1 5 1 1 1 10\n0 0 0 5 0 3\n',
            b'1 5 1 1 1 3\n0 0 0 1 3 3\n',
            b'1 5 1 1 1 10\n0 0 0 3 0 11\n',
        ]:
            with self.subTest(input_data=input_data):
                self.assert_invalid_input(input_data)

    def test_input_with_a_latest_finish_too_early_for_the_ride(self) -> None:
        self.assert_invalid_input(b'1 5 1 1 1 10\n0 0 0 3 1 3\n')

    def test_input_with_a_ride_that_starts_where_it_finishes(self) -> None:
        self.assert_invalid_input(b'1 5 1 1 1 10\n0 2 0 2 0 3\n')

    def test_input_breaks_the_format(self) -> None:
        for input_data in [
            b'1 5 1 1 1\n0 0 0 3 0 3\n',
            b'1 5 1 1 1 10\n0 0 0 3 0\n',
            b'1 5 1 1 1 10\n0  0 0 3 0 3\n',
            b'1 5 1 1 1 10\r\n0 0 0 3 0 3\r\n',
            b'1 5 1 1 1 10\n+0 0 0 3 0 3\n',
        ]:
            with self.subTest(input_data=input_data):
                self.assert_invalid_input(input_data)

    def test_input_with_fewer_rides_than_n(self) -> None:
        self.assert_invalid_input(b'1 5 1 2 1 10\n0 0 0 3 0 3\n')

    def test_input_with_more_rides_than_n(self) -> None:
        self.assert_invalid_input(b'1 5 1 1 1 10\n0 0 0 3 0 3\n0 0 0 3 0 3\n')
