import os
import tempfile
import unittest

import judge

FOLDER = os.path.dirname(__file__)
EXAMPLE_IN = os.path.join(FOLDER, 'example.in')
EXAMPLE_OUT = os.path.join(FOLDER, 'example.out')

# The example city with 1 car and T = 75: street 0 goes one way from 0 to 1 in 30 seconds, street 1 joins 1 and 2 both
# ways in 45 seconds.
ONE_CAR_IN = b'3 2 75 1 0\n48.8582 2.2945\n50.0 3.09\n51.424242 3.02\n0 1 1 30 250\n1 2 2 45 200\n'

# Two junctions joined both ways by a street of cost 1, so a car can go back and forth for T = 1000000 seconds.
BACK_AND_FORTH_IN = b'2 1 1000000 1 0\n0 0\n1 1\n0 1 2 1 7\n'

# The first line of a valid input, which the input tests below complete with junctions and streets.
HEADER = b'3 2 3000 2 0\n'
JUNCTIONS = b'48.8582 2.2945\n50.0 3.09\n51.424242 3.02\n'


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

    def assert_invalid(self, output: bytes, message: str, input_data: bytes | None = None) -> None:
        with self.assertRaises(judge.InvalidOutput) as context:
            if input_data is None:
                self.score_output(output)
            else:
                self.score_files(input_data, output)
        self.assertEqual(str(context.exception), message)

    def assert_invalid_input(self, input_data: bytes) -> None:
        with self.assertRaises(judge.InvalidInput):
            self.score_files(input_data, b'2\n1\n0\n1\n0\n')

    def test_example_score_matches_statement(self) -> None:
        # The statement prints no score. The second car drives street 0 (250 m) and street 1 (200 m).
        self.assertEqual(judge.main(EXAMPLE_IN, EXAMPLE_OUT), 450)

    def test_cars_that_stay_at_the_start(self) -> None:
        self.assertEqual(self.score_output(b'2\n1\n0\n1\n0\n'), 0)

    def test_street_driven_by_two_cars_counts_once(self) -> None:
        self.assertEqual(self.score_output(b'2\n2\n0\n1\n2\n0\n1\n'), 250)

    def test_street_driven_both_ways_counts_once(self) -> None:
        self.assertEqual(self.score_output(b'2\n1\n0\n5\n0\n1\n2\n1\n2\n'), 450)

    def test_itinerary_that_takes_exactly_t(self) -> None:
        self.assertEqual(self.score_files(ONE_CAR_IN, b'1\n3\n0\n1\n2\n'), 450)

    def test_itinerary_that_takes_longer_than_t(self) -> None:
        self.assert_invalid(
            b'1\n4\n0\n1\n2\n1\n', 'line 6: car 0 reaches junction 1 at time 120, after T = 75', ONE_CAR_IN
        )
        self.assert_invalid(
            b'1\n3\n0\n1\n2\n',
            'line 5: car 0 reaches junction 2 at time 75, after T = 74',
            ONE_CAR_IN.replace(b' 75 ', b' 74 '),
        )

    def test_time_counts_per_car(self) -> None:
        # Each car takes 75 seconds, so together they take more than T, which is allowed.
        input_data = ONE_CAR_IN.replace(b' 75 1 ', b' 75 2 ')
        self.assertEqual(self.score_files(input_data, b'2\n3\n0\n1\n2\n3\n0\n1\n2\n'), 450)

    def test_one_way_street_driven_the_wrong_way(self) -> None:
        self.assert_invalid(
            b'2\n1\n0\n3\n0\n1\n0\n',
            'line 7: street 0 goes one way, from junction 0 to junction 1, so a car cannot drive it from 1 to 0',
        )

    def test_junctions_without_a_street(self) -> None:
        self.assert_invalid(b'2\n1\n0\n2\n0\n2\n', 'line 6: no street connects junction 0 to junction 2')

    def test_car_that_stays_at_a_junction_for_a_step(self) -> None:
        self.assert_invalid(b'2\n2\n0\n0\n1\n0\n', 'line 4: no street connects junction 0 to junction 0')

    def test_itinerary_that_does_not_start_at_s(self) -> None:
        self.assert_invalid(
            b'2\n1\n0\n2\n1\n2\n', 'line 5: car 1 starts at junction 1, expected the starting junction S = 0'
        )

    def test_junction_out_of_range(self) -> None:
        cases = [
            (b'2\n1\n0\n2\n0\n3\n', 'line 6: junction 3 does not exist, expected an ID from 0 to 2'),
            (b'2\n1\n-1\n1\n0\n', 'line 3: junction -1 does not exist, expected an ID from 0 to 2'),
        ]
        for output, message in cases:
            with self.subTest(output=output):
                self.assert_invalid(output, message)

    def test_visit_count_out_of_range(self) -> None:
        cases = [
            (b'2\n0\n1\n0\n', 'line 2: found V = 0, expected 1 to 1000000'),
            (b'2\n-1\n1\n0\n', 'line 2: found V = -1, expected 1 to 1000000'),
            (b'2\n1\n0\n1000001\n0\n', 'line 4: found V = 1000001, expected 1 to 1000000'),
        ]
        for output, message in cases:
            with self.subTest(output=output):
                self.assert_invalid(output, message)

    def test_a_million_visits(self) -> None:
        visits = b'0\n1\n' * 500_000
        self.assertEqual(self.score_files(BACK_AND_FORTH_IN, b'1\n1000000\n' + visits), 7)

    def test_car_count_does_not_match_the_input(self) -> None:
        cases = [
            (b'1\n1\n0\n', 'line 1: found C = 1, expected 2, the number of cars in the input'),
            (b'3\n1\n0\n1\n0\n1\n0\n', 'line 1: found C = 3, expected 2, the number of cars in the input'),
        ]
        for output, message in cases:
            with self.subTest(output=output):
                self.assert_invalid(output, message)

    def test_fewer_junctions_than_v(self) -> None:
        self.assert_invalid(b'2\n1\n0\n3\n0\n1\n', 'line 7: found the end of the file, expected junction 2 of car 1')

    def test_fewer_itineraries_than_cars(self) -> None:
        self.assert_invalid(
            b'2\n1\n0\n', 'line 4: found the end of the file, expected V, the number of junctions visited by car 1'
        )

    def test_more_lines_than_itineraries(self) -> None:
        self.assert_invalid(b'2\n1\n0\n1\n0\n0\n', "line 6: found '0', expected the end of the file")

    def test_blank_line_inside_the_file(self) -> None:
        self.assert_invalid(
            b'2\n1\n0\n\n1\n0\n', "line 4: found '', expected V, the number of junctions visited by car 1"
        )

    def test_two_numbers_on_one_line(self) -> None:
        self.assert_invalid(
            b'2\n1 0\n1\n0\n', "line 2: found '1 0', expected V, the number of junctions visited by car 0"
        )

    def test_windows_line_endings_whitespace_and_blank_lines_at_the_end(self) -> None:
        self.assertEqual(self.score_output(b'2\r\n 1\r\n0\t\r\n3\r\n0\r\n1\r\n2\r\n\r\n  \n'), 450)

    def test_missing_newline_at_the_end(self) -> None:
        self.assertEqual(self.score_output(b'2\n1\n0\n3\n0\n1\n2'), 450)

    def test_empty_file(self) -> None:
        self.assert_invalid(b'', 'line 1: found the end of the file, expected C, the number of cars')

    def test_integers_are_parsed_strictly(self) -> None:
        for token in ['+1', '1.0', '0x1', '1_0', 'one']:
            with self.subTest(token=token):
                output = f'2\n1\n0\n2\n0\n{token}\n'.encode('ascii')
                self.assert_invalid(output, f'line 6: found {token!r}, expected an integer')

    def test_non_ascii_byte(self) -> None:
        self.assert_invalid('2\n1\n0\n2\n0\n١\n'.encode('utf-8'), 'line 6: found the byte 0xd9, expected ASCII text')

    def test_integer_with_thousands_of_digits(self) -> None:
        with self.assertRaises(judge.InvalidOutput):
            self.score_output(b'2\n1\n0\n2\n0\n' + b'1' * 5000 + b'\n')

    def test_input_without_a_newline_at_the_end(self) -> None:
        self.assertEqual(self.score_files(ONE_CAR_IN.rstrip(b'\n'), b'1\n3\n0\n1\n2\n'), 450)

    def test_input_with_negative_and_integer_coordinates(self) -> None:
        input_data = HEADER + b'-90 -180\n90 180\n-0.5 0\n' + b'0 1 1 30 250\n1 2 2 45 200\n'
        self.assertEqual(self.score_files(input_data, b'2\n1\n0\n3\n0\n1\n2\n'), 450)

    def test_input_out_of_range(self) -> None:
        streets = b'0 1 1 30 250\n1 2 2 45 200\n'
        for input_data in [
            b'3 2 3000 2 3\n' + JUNCTIONS + streets,
            HEADER + b'90.0000001 2.2945\n50.0 3.09\n51.424242 3.02\n' + streets,
            HEADER + b'48.8582 -180.5\n50.0 3.09\n51.424242 3.02\n' + streets,
            HEADER + JUNCTIONS + b'0 3 1 30 250\n1 2 2 45 200\n',
            HEADER + JUNCTIONS + b'0 1 0 30 250\n1 2 2 45 200\n',
            HEADER + JUNCTIONS + b'0 1 3 30 250\n1 2 2 45 200\n',
        ]:
            with self.subTest(input_data=input_data):
                self.assert_invalid_input(input_data)

    def test_input_with_a_street_from_a_junction_to_itself(self) -> None:
        self.assert_invalid_input(HEADER + JUNCTIONS + b'0 1 1 30 250\n2 2 2 45 200\n')

    def test_input_with_two_streets_between_the_same_junctions(self) -> None:
        self.assert_invalid_input(HEADER + JUNCTIONS + b'0 1 1 30 250\n1 0 1 45 200\n')

    def test_input_breaks_the_format(self) -> None:
        streets = b'0 1 1 30 250\n1 2 2 45 200\n'
        for input_data in [
            b'3 2 3000 2\n' + JUNCTIONS + streets,
            HEADER + b'48.8582  2.2945\n50.0 3.09\n51.424242 3.02\n' + streets,
            HEADER + b'+48.8582 2.2945\n50.0 3.09\n51.424242 3.02\n' + streets,
            HEADER + b'48. 2.2945\n50.0 3.09\n51.424242 3.02\n' + streets,
            HEADER + JUNCTIONS + b'0 1 1 30\n1 2 2 45 200\n',
            HEADER + JUNCTIONS + b'0 1 1 -30 250\n1 2 2 45 200\n',
            HEADER.replace(b'\n', b'\r\n') + JUNCTIONS + streets,
        ]:
            with self.subTest(input_data=input_data):
                self.assert_invalid_input(input_data)

    def test_input_with_fewer_streets_than_m(self) -> None:
        self.assert_invalid_input(HEADER + JUNCTIONS + b'0 1 1 30 250\n')

    def test_input_with_more_lines_than_m_streets(self) -> None:
        self.assert_invalid_input(HEADER + JUNCTIONS + b'0 1 1 30 250\n1 2 2 45 200\n0 2 2 45 200\n')
