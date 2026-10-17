import os
import tempfile
import unittest

import judge

FOLDER = os.path.dirname(__file__)
EXAMPLE_IN = os.path.join(FOLDER, 'example.in')
EXAMPLE_OUT = os.path.join(FOLDER, 'example.out')

# Three intersections and F = 10. Street zero enters intersection 0, from which one leads to 1 in one second and side
# leads to 2 in two seconds. Intersection 2 has two incoming streets, side and two.
STREETS = '2 0 zero 1\n0 1 one 1\n0 2 side 2\n1 2 two 1\n'
ZERO_ALWAYS_GREEN = b'1\n0\n1\nzero 1\n'


def city_input(duration: int, paths: list[str]) -> bytes:
    lines = [f'{duration} 3 4 {len(paths)} 10\n', STREETS] + [f'{path}\n' for path in paths]
    return ''.join(lines).encode('ascii')


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
        self.assertEqual(judge.main(EXAMPLE_IN, EXAMPLE_OUT), 1002)

    def test_both_cars_finish_when_intersection_1_alternates(self) -> None:
        # The second car finishes at T = 4 as in the statement. The first crosses intersection 1 at T = 1, when
        # rue-d-amsterdam turns green, and finishes at T = 6, which is D, so it scores F only.
        output = b'3\n0\n1\nrue-de-londres 1\n1\n2\nrue-d-athenes 1\nrue-d-amsterdam 1\n2\n1\nrue-de-moscou 1\n'
        self.assertEqual(self.score_output(output), 1000 + 1002)

    def test_car_that_finishes_at_d_scores_f(self) -> None:
        self.assertEqual(self.score_files(city_input(2, ['2 zero side']), ZERO_ALWAYS_GREEN), 10)

    def test_car_that_finishes_after_d_scores_zero(self) -> None:
        # The second car crosses at T = 1 and finishes at 3.
        self.assertEqual(self.score_files(city_input(2, ['2 zero side', '2 zero side']), ZERO_ALWAYS_GREEN), 10)

    def test_one_car_crosses_every_second(self) -> None:
        # The cars finish at T = 1 and T = 2.
        self.assertEqual(self.score_files(city_input(2, ['2 zero one', '2 zero one']), ZERO_ALWAYS_GREEN), 11 + 10)

    def test_car_listed_first_in_the_input_goes_first(self) -> None:
        # The car on side goes second and finishes at T = 3, after D. Listed first, it finishes at 2, as does the other.
        self.assertEqual(self.score_files(city_input(2, ['2 zero one', '2 zero side']), ZERO_ALWAYS_GREEN), 11)
        self.assertEqual(self.score_files(city_input(2, ['2 zero side', '2 zero one']), ZERO_ALWAYS_GREEN), 10 + 10)

    def test_order_of_the_schedule_sets_when_a_light_is_green(self) -> None:
        input_data = city_input(5, ['2 side zero'])
        self.assertEqual(self.score_files(input_data, b'1\n2\n2\nside 1\ntwo 2\n'), 10 + 4)
        self.assertEqual(self.score_files(input_data, b'1\n2\n2\ntwo 2\nside 1\n'), 10 + 2)

    def test_schedule_repeats_until_the_end(self) -> None:
        # Side is green at T = 0 and T = 3 only, so the second car crosses at 3 and finishes at 4.
        input_data = city_input(5, ['2 side zero', '2 side zero'])
        self.assertEqual(self.score_files(input_data, b'1\n2\n2\nside 1\ntwo 2\n'), 14 + 11)

    def test_street_left_out_of_a_schedule_stays_red(self) -> None:
        self.assertEqual(self.score_files(city_input(5, ['2 side zero']), b'1\n2\n1\ntwo 1\n'), 0)

    def test_no_schedule_scores_zero(self) -> None:
        self.assertEqual(self.score_output(b'0\n'), 0)

    def test_schedule_count_out_of_range(self) -> None:
        self.assert_invalid(b'-1\n', 'line 1: found A = -1, expected 0 to I = 4')
        self.assert_invalid(b'5\n', 'line 1: found A = 5, expected 0 to I = 4')

    def test_schedule_count_line_with_more_than_one_token(self) -> None:
        self.assert_invalid(b'1 0\n', 'line 1: found 2 tokens, expected A')

    def test_intersection_out_of_range(self) -> None:
        message = 'line 2: intersection {} does not exist, expected an ID from 0 to 3'
        self.assert_invalid(b'1\n4\n1\nrue-de-rome 1\n', message.format(4))
        self.assert_invalid(b'1\n-1\n1\nrue-de-rome 1\n', message.format(-1))

    def test_intersection_listed_twice(self) -> None:
        self.assert_invalid(
            b'2\n0\n1\nrue-de-londres 1\n0\n1\nrue-de-londres 2\n',
            'line 5: intersection 0 is listed a second time, first listed on line 2',
        )

    def test_intersection_line_with_more_than_one_token(self) -> None:
        self.assert_invalid(b'1\n1 2\n', 'line 2: found 2 tokens, expected the intersection ID i')

    def test_street_count_out_of_range(self) -> None:
        message = 'line 3: found E = {}, expected 1 to 2, the number of streets that enter intersection 1'
        self.assert_invalid(b'1\n1\n0\n', message.format(0))
        self.assert_invalid(b'1\n1\n3\nrue-d-athenes 1\nrue-d-amsterdam 1\nrue-de-rome 1\n', message.format(3))

    def test_street_count_line_with_more_than_one_token(self) -> None:
        self.assert_invalid(
            b'1\n1\n1 1\nrue-d-athenes 1\n',
            'line 3: found 2 tokens, expected E, the number of streets in the schedule of intersection 1',
        )

    def test_street_that_does_not_exist(self) -> None:
        self.assert_invalid(b'1\n1\n1\nrue-de-paris 1\n', "line 4: street 'rue-de-paris' does not exist")
        self.assert_invalid(b'1\n1\n1\nRUE-D-ATHENES 1\n', "line 4: street 'RUE-D-ATHENES' does not exist")

    def test_street_that_does_not_enter_the_intersection(self) -> None:
        # rue-de-moscou leaves intersection 1, so it is not one of its incoming streets.
        self.assert_invalid(
            b'1\n1\n1\nrue-de-moscou 1\n',
            'line 4: street rue-de-moscou does not enter intersection 1, it enters intersection 2',
        )

    def test_street_listed_twice_in_one_schedule(self) -> None:
        self.assert_invalid(
            b'1\n1\n2\nrue-d-athenes 1\nrue-d-athenes 2\n',
            'line 5: street rue-d-athenes is listed a second time, first listed on line 4',
        )

    def test_duration_out_of_range(self) -> None:
        self.assert_invalid(b'1\n1\n1\nrue-d-athenes 0\n', 'line 4: found T = 0, expected 1 to D = 6')
        self.assert_invalid(b'1\n1\n1\nrue-d-athenes 7\n', 'line 4: found T = 7, expected 1 to D = 6')
        self.assert_invalid(b'1\n1\n1\nrue-d-athenes -1\n', 'line 4: found T = -1, expected 1 to D = 6')

    def test_duration_of_d_is_valid(self) -> None:
        self.assertEqual(self.score_output(b'1\n1\n1\nrue-d-athenes 6\n'), 0)

    def test_street_line_with_wrong_token_count(self) -> None:
        expected = 'expected a street name and the duration T'
        self.assert_invalid(b'1\n1\n1\nrue-d-athenes\n', f'line 4: found 1 tokens, {expected}')
        self.assert_invalid(b'1\n1\n1\nrue-d-athenes 1 1\n', f'line 4: found 3 tokens, {expected}')

    def test_fewer_lines_than_expected(self) -> None:
        self.assert_invalid(
            b'2\n0\n1\nrue-de-londres 1\n', 'line 5: found the end of the file, expected the intersection ID i'
        )
        self.assert_invalid(
            b'1\n1\n',
            'line 3: found the end of the file, expected E, the number of streets in the schedule of intersection 1',
        )
        self.assert_invalid(
            b'1\n1\n2\nrue-d-athenes 1\n',
            'line 5: found the end of the file, expected a street name and the duration T',
        )

    def test_more_lines_than_expected(self) -> None:
        self.assert_invalid(
            b'1\n0\n1\nrue-de-londres 1\nrue-de-rome 1\n', "line 5: found 'rue-de-rome 1', expected the end of the file"
        )

    def test_any_whitespace_and_blank_lines_at_the_end(self) -> None:
        output = (
            b' 3 \r\n1\r\n\t2\nrue-d-athenes  2\nrue-d-amsterdam\t1 \n0\n1\nrue-de-londres 2\n2\n1\n'
            b'rue-de-moscou 1\r\n\r\n \n'
        )
        self.assertEqual(self.score_output(output), 1002)

    def test_missing_newline_at_the_end(self) -> None:
        with open(EXAMPLE_OUT, 'rb') as file:
            self.assertEqual(self.score_output(file.read().rstrip(b'\n')), 1002)

    def test_empty_file(self) -> None:
        self.assert_invalid(b'', 'line 1: found the end of the file, expected A')

    def test_integers_are_parsed_strictly(self) -> None:
        for token in ['+2', '2.0', '0x2', '0_2', 'two']:
            with self.subTest(token=token):
                self.assert_invalid(
                    f'1\n1\n1\nrue-d-athenes {token}\n'.encode('ascii'),
                    f'line 4: found {token!r}, expected an integer',
                )

    def test_non_ascii_byte(self) -> None:
        self.assert_invalid(
            '1\n1\n1\nrue-d-athenes ٢\n'.encode('utf-8'), 'line 4: found the byte 0xd9, expected ASCII text'
        )

    def test_integer_with_thousands_of_digits(self) -> None:
        with self.assertRaises(judge.InvalidOutput):
            self.score_output(b'1\n1\n1\nrue-d-athenes ' + b'1' * 5000 + b'\n')

    def test_input_without_a_newline_at_the_end(self) -> None:
        input_data = city_input(2, ['2 zero side']).rstrip(b'\n')
        self.assertEqual(self.score_files(input_data, ZERO_ALWAYS_GREEN), 10)

    def test_path_may_begin_and_end_at_intersections_the_car_crosses(self) -> None:
        # Side leaves intersection 0 and the path ends at 2. The car crosses 2, 0 and 1, each only once.
        self.assertEqual(self.score_files(city_input(5, ['4 side zero one two']), b'0\n'), 0)

    def test_input_out_of_range(self) -> None:
        for header in ['0 3 4 1 10', '10001 3 4 1 10', '2 1 4 1 10', '2 3 4 0 10', '2 3 4 1 0', '2 3 4 1 1001']:
            with self.subTest(header=header):
                self.assert_invalid_input(f'{header}\n{STREETS}2 zero one\n'.encode('ascii'))
        for streets in ['3 0 zero 1', '2 3 zero 1', '2 0 zero 0', '2 0 zero 3']:
            with self.subTest(streets=streets):
                input_data = city_input(2, ['2 zero one']).replace(b'2 0 zero 1', streets.encode('ascii'))
                self.assert_invalid_input(input_data)
        self.assert_invalid_input(city_input(2, ['1 zero']))

    def test_input_breaks_the_format(self) -> None:
        valid = city_input(2, ['2 zero one'])
        for old, new in [
            (b'2 0 zero 1', b'2  0 zero 1'),
            (b'2 0 zero 1', b'2 0 zero 1 '),
            (b'2 0 zero 1\n', b'2 0 zero 1\r\n'),
            (b'2 0 zero 1', b'2 0 zero +1'),
            (b'zero', b'Zero'),
            (b'side', b'si'),
            (b'side', b'side' * 8),
        ]:
            with self.subTest(new=new):
                self.assert_invalid_input(valid.replace(old, new, 1))

    def test_input_with_a_street_name_twice(self) -> None:
        self.assert_invalid_input(city_input(2, ['2 zero one']).replace(b'side', b'zero'))

    def test_input_with_two_streets_in_the_same_direction(self) -> None:
        # side and two then both lead from intersection 1 to 2.
        self.assert_invalid_input(city_input(2, ['2 zero one']).replace(b'0 2 side', b'1 2 side'))

    def test_input_with_an_intersection_without_incoming_streets(self) -> None:
        self.assert_invalid_input(city_input(2, ['2 zero one']).replace(b'2 3 4 1 10', b'2 4 4 1 10'))

    def test_input_with_a_path_that_breaks(self) -> None:
        self.assert_invalid_input(city_input(2, ['2 zero two']))

    def test_input_with_a_car_that_goes_through_an_intersection_twice(self) -> None:
        self.assert_invalid_input(city_input(5, ['5 zero one two zero one']))

    def test_input_with_a_path_of_a_different_length_than_p(self) -> None:
        self.assert_invalid_input(city_input(2, ['3 zero one']))
        self.assert_invalid_input(city_input(2, ['2 zero one two']))

    def test_input_with_a_path_through_a_street_that_does_not_exist(self) -> None:
        self.assert_invalid_input(city_input(2, ['2 zero three']))

    def test_input_with_fewer_cars_than_v(self) -> None:
        self.assert_invalid_input(city_input(2, ['2 zero one']).replace(b'2 3 4 1 10', b'2 3 4 2 10'))

    def test_input_with_more_lines_than_expected(self) -> None:
        self.assert_invalid_input(city_input(2, ['2 zero one']) + b'2 zero one\n')
