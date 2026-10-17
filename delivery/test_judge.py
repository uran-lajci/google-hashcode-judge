import os
import tempfile
import unittest

import judge

FOLDER = os.path.dirname(__file__)
EXAMPLE_IN = os.path.join(FOLDER, 'example.in')
EXAMPLE_OUT = os.path.join(FOLDER, 'example.out')

# 10 rows, 10 columns, 1 drone, 20 turns, maximum load 10; warehouse 0 at [0, 0], order 0 at [3, 4].
PYTHAGOREAN_IN = b'10 10 1 20 10\n1\n1\n1\n0 0\n1\n1\n3 4\n1\n0\n'


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
        self.assertEqual(judge.main(EXAMPLE_IN, EXAMPLE_OUT), 194)

    def test_no_commands(self) -> None:
        self.assertEqual(self.score_output(b'0\n'), 0)

    def test_order_delivered_in_part_scores_zero(self) -> None:
        self.assertEqual(self.score_output(b'2\n0 L 0 0 1\n0 D 0 0 1\n'), 0)

    def test_order_delivered_by_two_drones(self) -> None:
        # Drone 0 delivers product 0 in turn 3, drone 1 delivers product 2 in turn 15: (50 - 15) / 50 * 100 = 70.
        self.assertEqual(self.score_output(b'4\n0 L 0 0 1\n1 L 1 2 1\n0 D 0 0 1\n1 D 0 2 1\n'), 70)

    def test_flight_rounds_up_but_not_an_exact_distance(self) -> None:
        # The flight from [0, 0] to [3, 4] is exactly 5 turns, so the delivery is in turn 6: (20 - 6) / 20 * 100 = 70.
        self.assertEqual(self.score_files(PYTHAGOREAN_IN, b'2\n0 L 0 0 1\n0 D 0 0 1\n'), 70)
        # The flight from [0, 0] to [3, 3] is 4.24 rounded up to 5 turns: (50 - 6) / 50 * 100 = 88.
        self.assertEqual(self.score_output(b'2\n0 L 0 0 1\n0 D 1 0 1\n'), 88)

    def test_score_rounds_up(self) -> None:
        # With 30 turns, a delivery in turn 7 scores (30 - 7) / 30 * 100 = 76.67, rounded up to 77.
        thirty_turns_in = PYTHAGOREAN_IN.replace(b' 20 ', b' 30 ')
        self.assertEqual(self.score_files(thirty_turns_in, b'3\n0 L 0 0 1\n0 W 1\n0 D 0 0 1\n'), 77)

    def test_delivery_in_the_last_turn(self) -> None:
        # The load is in turn 43, the flight takes turns 44 to 48 and the delivery is in turn 49.
        self.assertEqual(self.score_output(b'3\n0 W 43\n0 L 0 0 1\n0 D 1 0 1\n'), 2)
        self.assert_invalid(
            b'3\n0 W 44\n0 L 0 0 1\n0 D 1 0 1\n',
            'line 4: drone 0 would deliver in turn 50, expected at most turn 49',
        )

    def test_wait_until_the_last_turn(self) -> None:
        self.assertEqual(self.score_output(b'1\n0 W 50\n'), 0)
        self.assertEqual(self.score_output(b'2\n0 W 49\n1 L 0 0 1\n'), 0)
        self.assert_invalid(b'2\n0 L 0 0 1\n0 W 50\n', 'line 3: drone 0 waits until turn 50, expected at most turn 49')

    def test_unload_happens_before_a_load_in_the_same_turn(self) -> None:
        # Drone 0 unloads product 2 at warehouse 0 in turn 17. Drone 1 loads it there in turn 17 and delivers in
        # turn 26: (50 - 26) / 50 * 100 = 48.
        drone_0 = b'0 L 1 2 1\n0 U 0 2 1\n'
        drone_1 = b'1 W 17\n1 L 0 2 1\n1 D 2 2 1\n'
        self.assertEqual(self.score_output(b'5\n' + drone_0 + drone_1), 48)
        self.assertEqual(self.score_output(b'5\n' + drone_1 + drone_0), 48)

    def test_load_before_the_unload(self) -> None:
        self.assert_invalid(
            b'5\n1 W 16\n1 L 0 2 1\n1 D 2 2 1\n0 L 1 2 1\n0 U 0 2 1\n',
            'line 3: warehouse 0 holds 0 items of product type 2 in turn 16, expected at least 1 for drone 1 to load',
        )

    def test_unloaded_items_return_to_the_warehouse(self) -> None:
        self.assertEqual(self.score_output(b'4\n0 L 0 0 5\n0 U 0 0 5\n1 W 2\n1 L 0 0 5\n'), 0)
        self.assert_invalid(
            b'4\n0 L 0 0 5\n0 U 0 0 4\n1 W 2\n1 L 0 0 5\n',
            'line 5: warehouse 0 holds 4 items of product type 0 in turn 2, expected at least 5 for drone 1 to load',
        )

    def test_warehouse_without_the_product(self) -> None:
        self.assert_invalid(
            b'1\n0 L 0 2 1\n',
            'line 2: warehouse 0 holds 0 items of product type 2 in turn 0, expected at least 1 for drone 0 to load',
        )

    def test_two_drones_load_the_last_items_in_the_same_turn(self) -> None:
        self.assertEqual(self.score_output(b'2\n0 L 0 0 3\n1 L 0 0 2\n'), 0)
        self.assert_invalid(
            b'2\n0 L 0 0 3\n1 L 0 0 3\n',
            'line 3: warehouse 0 holds 2 items of product type 0 in turn 0, expected at least 3 for drone 1 to load',
        )

    def test_maximum_load(self) -> None:
        self.assertEqual(self.score_output(b'1\n0 L 0 0 5\n'), 0)
        self.assert_invalid(
            b'2\n0 L 0 0 1\n0 L 1 2 1\n',
            'line 3: drone 0 would carry a weight of 550, expected at most 500',
        )

    def test_delivered_and_unloaded_items_free_the_load(self) -> None:
        # 100 delivered, then 450 + 10 * 5 = 500 loaded. Order 1 completes in turn 6.
        self.assertEqual(self.score_output(b'4\n0 L 0 0 1\n0 D 1 0 1\n0 L 1 2 1\n0 L 1 1 10\n'), 88)
        self.assertEqual(self.score_output(b'3\n0 L 0 0 5\n0 U 0 0 1\n0 L 0 0 1\n'), 0)

    def test_deliver_or_unload_more_than_carried(self) -> None:
        self.assert_invalid(
            b'2\n0 L 0 0 1\n0 D 1 0 2\n',
            'line 3: drone 0 carries 1 items of product type 0, expected at least 2 to deliver',
        )
        self.assert_invalid(
            b'2\n0 L 0 0 1\n1 U 0 0 1\n',
            'line 3: drone 1 carries 0 items of product type 0, expected at least 1 to unload',
        )
        self.assert_invalid(
            b'3\n0 L 0 0 1\n0 D 1 0 1\n0 D 1 0 1\n',
            'line 4: drone 0 carries 0 items of product type 0, expected at least 1 to deliver',
        )

    def test_order_receives_more_than_it_ordered(self) -> None:
        self.assert_invalid(
            b'2\n0 L 0 0 2\n0 D 1 0 2\n',
            'line 3: order 1 would receive 2 items of product type 0, expected at most 1',
        )
        self.assert_invalid(
            b'2\n0 L 0 1 1\n0 D 0 1 1\n',
            'line 3: order 0 would receive 1 items of product type 1, expected at most 0',
        )
        self.assert_invalid(
            b'4\n0 L 0 0 1\n1 L 0 0 1\n0 D 1 0 1\n1 D 1 0 1\n',
            'line 5: order 1 would receive 2 items of product type 0, expected at most 1',
        )

    def test_command_count(self) -> None:
        self.assert_invalid(b'2\n0 W 1\n', 'line 3: found the end of the file, expected ' + judge.EXPECTED_COMMAND)
        self.assert_invalid(b'1\n0 W 1\n0 W 1\n', "line 3: found '0 W 1', expected the end of the file")
        self.assert_invalid(b'-1\n', 'line 1: found Q = -1, expected 0 to 150')
        self.assert_invalid(b'151\n', 'line 1: found Q = 151, expected 0 to 150')
        self.assert_invalid(b'0 0\n', 'line 1: found 2 tokens, expected Q')
        self.assert_invalid(b'', 'line 1: found the end of the file, expected Q')

    def test_tag(self) -> None:
        self.assert_invalid(b'1\n0 l 0 0 1\n', "line 2: found the tag 'l', expected L, U, D or W")
        self.assert_invalid(b'1\n0 X 1\n', "line 2: found the tag 'X', expected L, U, D or W")
        self.assert_invalid(b'1\nL 0 0 0 1\n', "line 2: found the tag '0', expected L, U, D or W")
        self.assert_invalid(b'1\n0\n', 'line 2: found 1 tokens, expected ' + judge.EXPECTED_COMMAND)

    def test_wrong_number_of_tokens(self) -> None:
        self.assert_invalid(b'1\n0 L 0 0\n', 'line 2: found 4 tokens, expected 5 for the tag L')
        self.assert_invalid(b'1\n0 D 0 0 1 1\n', 'line 2: found 6 tokens, expected 5 for the tag D')
        self.assert_invalid(b'1\n0 W\n', 'line 2: found 2 tokens, expected 3 for the tag W')
        self.assert_invalid(b'1\n0 W 1 1 1\n', 'line 2: found 5 tokens, expected 3 for the tag W')

    def test_ids_out_of_range(self) -> None:
        cases = [
            (b'3 W 1', 'line 2: drone 3 does not exist, expected an ID from 0 to 2'),
            (b'-1 W 1', 'line 2: drone -1 does not exist, expected an ID from 0 to 2'),
            (b'0 L 2 0 1', 'line 2: warehouse 2 does not exist, expected an ID from 0 to 1'),
            (b'0 U -1 0 1', 'line 2: warehouse -1 does not exist, expected an ID from 0 to 1'),
            (b'0 D 3 0 1', 'line 2: order 3 does not exist, expected an ID from 0 to 2'),
            (b'0 L 0 3 1', 'line 2: product type 3 does not exist, expected an ID from 0 to 2'),
            (b'0 D 0 -1 1', 'line 2: product type -1 does not exist, expected an ID from 0 to 2'),
        ]
        for line, message in cases:
            with self.subTest(line=line):
                self.assert_invalid(b'1\n' + line + b'\n', message)

    def test_counts_are_positive(self) -> None:
        self.assert_invalid(b'1\n0 L 0 0 0\n', 'line 2: found 0 items, expected a positive number')
        self.assert_invalid(b'1\n0 U 0 0 -1\n', 'line 2: found -1 items, expected a positive number')
        self.assert_invalid(b'1\n0 W 0\n', 'line 2: found 0 turns, expected a positive number')

    def test_any_whitespace_and_blank_lines_at_the_end(self) -> None:
        self.assertEqual(self.score_output(b' 2 \r\n0\tL 0  0 1\r\n0 D 1 0 1\r\n\r\n  \n'), 88)

    def test_missing_newline_at_the_end(self) -> None:
        self.assertEqual(self.score_output(b'2\n0 L 0 0 1\n0 D 1 0 1'), 88)

    def test_blank_line_between_commands(self) -> None:
        self.assert_invalid(
            b'2\n0 L 0 0 1\n\n0 D 1 0 1\n',
            'line 3: found 0 tokens, expected ' + judge.EXPECTED_COMMAND,
        )

    def test_integers_are_parsed_strictly(self) -> None:
        for token in ['+1', '1.0', '0x1', '1_0', 'one']:
            with self.subTest(token=token):
                self.assert_invalid(
                    f'1\n0 L 0 0 {token}\n'.encode('ascii'),
                    f'line 2: found {token!r}, expected an integer',
                )

    def test_non_ascii_byte(self) -> None:
        self.assert_invalid('1\n0 W ×\n'.encode('utf-8'), 'line 2: found the byte 0xc3, expected ASCII text')

    def test_integer_with_thousands_of_digits(self) -> None:
        with self.assertRaises(judge.InvalidOutput):
            self.score_output(b'1\n0 W ' + b'1' * 5000 + b'\n')

    def test_input_without_a_newline_at_the_end(self) -> None:
        self.assertEqual(self.score_files(PYTHAGOREAN_IN.rstrip(b'\n'), b'2\n0 L 0 0 1\n0 D 0 0 1\n'), 70)

    def test_input_out_of_range(self) -> None:
        for input_data in [
            b'0 10 1 20 10\n1\n1\n1\n0 0\n1\n1\n3 4\n1\n0\n',
            b'10 10 1001 20 10\n1\n1\n1\n0 0\n1\n1\n3 4\n1\n0\n',
            b'10 10 1 20 10\n1\n11\n1\n0 0\n1\n1\n3 4\n1\n0\n',
            b'10 10 1 20 10\n1\n1\n1\n10 0\n1\n1\n3 4\n1\n0\n',
            b'10 10 1 20 10\n1\n1\n1\n0 0\n10001\n1\n3 4\n1\n0\n',
            b'10 10 1 20 10\n1\n1\n1\n0 0\n1\n1\n3 4\n1\n1\n',
            b'10 10 1 20 10\n1\n1\n1\n0 0\n1\n1\n3 4\n0\n\n',
        ]:
            with self.subTest(input_data=input_data):
                self.assert_invalid_input(input_data)

    def test_input_breaks_a_guarantee(self) -> None:
        for input_data in [
            b'10 10 1 20 10\n1\n1\n2\n0 0\n1\n0 0\n1\n1\n3 4\n1\n0\n',
            b'10 10 1 20 10\n1\n1\n1\n0 0\n1\n1\n0 0\n1\n0\n',
            b'10 10 1 20 10\n1\n1\n1\n0 0\n1\n1\n3 4\n2\n0 0\n',
        ]:
            with self.subTest(input_data=input_data):
                self.assert_invalid_input(input_data)

    def test_input_breaks_the_format(self) -> None:
        for input_data in [
            b'10 10 1 20\n1\n1\n1\n0 0\n1\n1\n3 4\n1\n0\n',
            b'10 10 1 20 10\n1\n1\n1\n0  0\n1\n1\n3 4\n1\n0\n',
            b'10 10 1 20 10\r\n1\r\n1\r\n1\r\n0 0\r\n1\r\n1\r\n3 4\r\n1\r\n0\r\n',
            b'10 10 1 20 10\n1\n1\n1\n0 0\n1\n1\n3 4\n2\n0\n',
            b'10 10 1 20 10\n1\n1\n1\n0 0\n1\n1\n3 4\n1\n0\n0\n',
        ]:
            with self.subTest(input_data=input_data):
                self.assert_invalid_input(input_data)
