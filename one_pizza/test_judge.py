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

    def assert_invalid_input(self, input_data: bytes) -> None:
        with self.assertRaises(judge.InvalidInput):
            self.score_files(input_data, b'0\n')

    def test_example_score_matches_statement(self) -> None:
        score = judge.main(EXAMPLE_IN, os.path.join(FOLDER, 'example.out'))
        self.assertEqual(score, 2)

    def test_ingredients_in_any_order(self) -> None:
        self.assertEqual(self.score_output(b'4 tomatoes peppers mushrooms cheese\n'), 2)

    def test_empty_pizza(self) -> None:
        self.assertEqual(self.score_output(b'0\n'), 0)

    def test_every_client(self) -> None:
        self.assertEqual(self.score_output(b'3 basil cheese peppers\n'), 2)
        self.assertEqual(self.score_output(b'2 cheese peppers\n'), 1)
        self.assertEqual(self.score_output(b'1 basil\n'), 1)
        self.assertEqual(self.score_output(b'2 mushrooms tomatoes\n'), 1)

    def test_disliked_ingredient_keeps_the_client_away(self) -> None:
        self.assertEqual(self.score_output(b'2 basil pineapple\n'), 0)
        self.assertEqual(self.score_output(b'4 basil pineapple mushrooms tomatoes\n'), 0)

    def test_ingredient_that_only_a_dislike_mentions(self) -> None:
        self.assertEqual(self.score_output(b'3 pineapple cheese peppers\n'), 1)

    def test_client_who_likes_and_dislikes_the_same_ingredient_never_comes(self) -> None:
        self.assertEqual(self.score_files(b'2\n1 a\n1 a\n1 a\n0\n', b'1 a\n'), 1)

    def test_any_whitespace_and_blank_lines_at_the_end(self) -> None:
        self.assertEqual(self.score_output(b' 4\tcheese  mushrooms tomatoes peppers \r\n\r\n  \n'), 2)

    def test_missing_newline_at_the_end(self) -> None:
        self.assertEqual(self.score_output(b'4 cheese mushrooms tomatoes peppers'), 2)

    def test_ingredient_twice(self) -> None:
        self.assert_invalid(b'3 cheese peppers cheese\n', "line 1: ingredient 'cheese' is on the pizza a second time")

    def test_ingredient_that_no_client_mentions(self) -> None:
        for ingredient in ['olives', 'Cheese', 'cheese,', 'chees', '0']:
            with self.subTest(ingredient=ingredient):
                self.assert_invalid(
                    f'2 cheese {ingredient}\n'.encode('ascii'),
                    f'line 1: ingredient {ingredient!r} is not mentioned by any client',
                )

    def test_fewer_ingredients_than_n(self) -> None:
        self.assert_invalid(b'4 cheese mushrooms tomatoes\n', 'line 1: found 3 ingredients, expected N = 4')

    def test_more_ingredients_than_n(self) -> None:
        self.assert_invalid(b'2 cheese mushrooms tomatoes\n', 'line 1: found 3 ingredients, expected N = 2')

    def test_negative_n(self) -> None:
        self.assert_invalid(b'-1\n', 'line 1: found N = -1, expected 0 or more')

    def test_ingredients_on_the_next_line(self) -> None:
        self.assert_invalid(b'2\ncheese peppers\n', 'line 1: found 0 ingredients, expected N = 2')

    def test_second_pizza(self) -> None:
        self.assert_invalid(
            b'1 basil\n2 cheese peppers\n',
            "line 2: found '2 cheese peppers', expected the end of the file",
        )

    def test_blank_first_line(self) -> None:
        self.assert_invalid(b'\n2 cheese peppers\n', 'line 1: found 0 tokens, expected N ingredient_1 ... ingredient_N')

    def test_empty_file(self) -> None:
        self.assert_invalid(b'', 'line 1: found the end of the file, expected N ingredient_1 ... ingredient_N')

    def test_integers_are_parsed_strictly(self) -> None:
        for token in ['+2', '2.0', '0x2', '1_0', 'two']:
            with self.subTest(token=token):
                self.assert_invalid(
                    f'{token} cheese peppers\n'.encode('ascii'),
                    f'line 1: found {token!r}, expected an integer',
                )

    def test_non_ascii_byte(self) -> None:
        self.assert_invalid('1 basilé\n'.encode('utf-8'), 'line 1: found the byte 0xc3, expected ASCII text')

    def test_integer_with_thousands_of_digits(self) -> None:
        with self.assertRaises(judge.InvalidOutput):
            self.score_output(b'1' * 5000 + b' cheese\n')

    def test_input_without_a_newline_at_the_end(self) -> None:
        self.assertEqual(self.score_files(b'1\n1 a\n0', b'1 a\n'), 1)

    def test_input_with_fewer_ingredients_than_l(self) -> None:
        self.assert_invalid_input(b'1\n2 a\n0\n')

    def test_input_with_no_likes(self) -> None:
        self.assert_invalid_input(b'1\n0\n0\n')

    def test_input_with_more_than_five_dislikes(self) -> None:
        self.assert_invalid_input(b'1\n1 a\n6 b c d e f g\n')

    def test_input_with_an_ingredient_that_breaks_the_format(self) -> None:
        for ingredient in [b'Basil', b'olive_oil', b'a' * 16]:
            with self.subTest(ingredient=ingredient):
                self.assert_invalid_input(b'1\n1 ' + ingredient + b'\n0\n')

    def test_input_with_fewer_clients_than_c(self) -> None:
        self.assert_invalid_input(b'2\n1 a\n0\n')

    def test_input_with_more_clients_than_c(self) -> None:
        self.assert_invalid_input(b'1\n1 a\n0\n1 b\n0\n')
