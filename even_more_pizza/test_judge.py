import os
import tempfile
import unittest

import judge

FOLDER = os.path.dirname(__file__)
EXAMPLE_IN = os.path.join(FOLDER, 'example.in')


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

    def test_example_score_matches_statement(self) -> None:
        score = judge.main(EXAMPLE_IN, os.path.join(FOLDER, 'example.out'))
        self.assertEqual(score, 65)

    def test_deliveries_and_pizzas_in_any_order(self) -> None:
        self.assertEqual(self.score_output(b'2\n3 3 2 0\n2 4 1\n'), 65)

    def test_every_team_size(self) -> None:
        self.assertEqual(self.score_files(b'9 1 1 1\n' + b'1 a\n' * 9, b'3\n4 0 1 2 3\n3 4 5 6\n2 7 8\n'), 3)

    def test_two_pizzas_with_the_same_ingredients(self) -> None:
        self.assertEqual(self.score_output(b'1\n2 1 3\n'), 9)

    def test_any_whitespace_and_blank_lines_at_the_end(self) -> None:
        self.assertEqual(self.score_output(b' 2\r\n2\t1  4 \r\n3 0 2 3\r\n\r\n  \n'), 65)

    def test_pizza_delivered_to_two_teams(self) -> None:
        self.assert_invalid(
            b'2\n2 1 4\n3 0 2 1\n',
            'line 3: pizza 1 is delivered a second time, first delivered on line 2',
        )

    def test_pizza_delivered_twice_to_one_team(self) -> None:
        self.assert_invalid(
            b'1\n3 0 2 0\n',
            'line 2: pizza 0 is delivered a second time, first delivered on line 2',
        )

    def test_pizza_that_does_not_exist(self) -> None:
        self.assert_invalid(b'1\n2 1 5\n', 'line 2: pizza 5 does not exist, expected a pizza from 0 to 4')
        self.assert_invalid(b'1\n2 -1 1\n', 'line 2: pizza -1 does not exist, expected a pizza from 0 to 4')

    def test_fewer_pizzas_than_people(self) -> None:
        self.assert_invalid(b'1\n4 0 1 2\n', 'line 2: found 3 pizzas, expected L = 4')

    def test_more_pizzas_than_people(self) -> None:
        self.assert_invalid(b'1\n2 0 1 2\n', 'line 2: found 3 pizzas, expected L = 2')

    def test_team_of_a_size_that_does_not_exist(self) -> None:
        for team_size in ['0', '1', '5', '-2']:
            with self.subTest(team_size=team_size):
                self.assert_invalid(
                    f'1\n{team_size} 0 1\n'.encode('ascii'),
                    f'line 2: found a team of {team_size} people, expected 2, 3 or 4',
                )

    def test_more_deliveries_to_a_team_size_than_teams(self) -> None:
        self.assert_invalid(
            b'2\n2 1 4\n2 0 2\n',
            'line 3: found delivery 2 to a team of 2 people, expected at most T2 = 1',
        )

    def test_delivery_to_a_team_size_with_no_teams(self) -> None:
        with self.assertRaises(judge.InvalidOutput) as context:
            self.score_files(b'4 2 0 0\n' + b'1 a\n' * 4, b'1\n3 0 1 2\n')
        self.assertEqual(
            str(context.exception),
            'line 2: found delivery 1 to a team of 3 people, expected at most T3 = 0',
        )

    def test_number_of_deliveries_out_of_range(self) -> None:
        self.assert_invalid(b'0\n', 'line 1: found 0 deliveries, expected 1 to T2 + T3 + T4 = 4')
        self.assert_invalid(b'-1\n', 'line 1: found -1 deliveries, expected 1 to T2 + T3 + T4 = 4')
        self.assert_invalid(b'5\n', 'line 1: found 5 deliveries, expected 1 to T2 + T3 + T4 = 4')

    def test_more_deliveries_than_d(self) -> None:
        self.assert_invalid(b'1\n2 1 4\n3 0 2 3\n', "line 3: found '3 0 2 3', expected the end of the file")

    def test_fewer_deliveries_than_d(self) -> None:
        self.assert_invalid(
            b'3\n2 1 4\n3 0 2 3\n',
            'line 4: found the end of the file, expected a delivery as L P1 ... PL',
        )

    def test_blank_line_between_deliveries(self) -> None:
        self.assert_invalid(b'2\n2 1 4\n\n3 0 2 3\n', 'line 3: found 0 tokens, expected a delivery as L P1 ... PL')

    def test_d_and_a_delivery_on_one_line(self) -> None:
        self.assert_invalid(b'1 2 1 4\n', 'line 1: found 4 tokens, expected the number of deliveries')

    def test_empty_file(self) -> None:
        self.assert_invalid(b'', 'line 1: found the end of the file, expected the number of deliveries')

    def test_integers_are_parsed_strictly(self) -> None:
        for token in ['+1', '1.0', '0x1', '1_0', '1,']:
            with self.subTest(token=token):
                self.assert_invalid(
                    f'1\n2 0 {token}\n'.encode('ascii'),
                    f'line 2: found {token!r}, expected an integer',
                )

    def test_non_ascii_byte(self) -> None:
        self.assert_invalid('1\n2 0 ١\n'.encode('utf-8'), 'line 2: found the byte 0xd9, expected ASCII text')

    def test_integer_with_thousands_of_digits(self) -> None:
        with self.assertRaises(judge.InvalidOutput):
            self.score_output(b'1\n2 0 ' + b'1' * 5000 + b'\n')

    def test_input_with_fewer_ingredients_than_i(self) -> None:
        with self.assertRaises(judge.InvalidInput):
            self.score_files(b'2 1 0 0\n2 a\n1 b\n', b'1\n2 0 1\n')

    def test_input_with_an_ingredient_twice_on_one_pizza(self) -> None:
        with self.assertRaises(judge.InvalidInput):
            self.score_files(b'2 1 0 0\n2 a a\n1 b\n', b'1\n2 0 1\n')

    def test_input_with_an_ingredient_that_breaks_the_format(self) -> None:
        for ingredient in [b'Basil', b'olive_oil', b'a' * 21]:
            with self.subTest(ingredient=ingredient):
                with self.assertRaises(judge.InvalidInput):
                    self.score_files(b'2 1 0 0\n1 ' + ingredient + b'\n1 b\n', b'1\n2 0 1\n')

    def test_input_with_fewer_pizzas_than_m(self) -> None:
        with self.assertRaises(judge.InvalidInput):
            self.score_files(b'3 1 0 0\n1 a\n1 b\n', b'1\n2 0 1\n')
