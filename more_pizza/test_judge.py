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
        self.assertEqual(score, 16)

    def test_pizza_types_in_any_order(self) -> None:
        self.assertEqual(self.score_output(b'3\n3 0 2\n'), 16)

    def test_no_pizzas_with_or_without_the_empty_second_line(self) -> None:
        for output in [b'0\n', b'0\n\n', b'0', b'0\n \n\n']:
            with self.subTest(output=output):
                self.assertEqual(self.score_output(output), 0)

    def test_exactly_m_slices(self) -> None:
        self.assertEqual(self.score_files(b'10 2\n4 6\n', b'2\n0 1\n'), 10)

    def test_any_whitespace_and_blank_lines_at_the_end(self) -> None:
        self.assertEqual(self.score_output(b' 3\r\n0\t2  3 \r\n\r\n  \n'), 16)

    def test_more_than_m_slices(self) -> None:
        self.assert_invalid(b'4\n0 1 2 3\n', 'line 2: the pizzas ordered have 21 slices, expected at most M = 17')

    def test_same_pizza_type_twice(self) -> None:
        self.assert_invalid(
            b'2\n2 2\n',
            'line 2: pizza type 2 is ordered a second time by token 2, first ordered by token 1',
        )

    def test_two_pizza_types_of_the_same_size(self) -> None:
        self.assertEqual(self.score_files(b'10 2\n5 5\n', b'2\n0 1\n'), 10)
        with self.assertRaises(judge.InvalidOutput) as context:
            self.score_files(b'10 2\n5 5\n', b'2\n0 0\n')
        self.assertEqual(
            str(context.exception),
            'line 2: pizza type 0 is ordered a second time by token 2, first ordered by token 1',
        )

    def test_pizza_type_that_does_not_exist(self) -> None:
        self.assert_invalid(b'1\n4\n', 'line 2: pizza type 4 does not exist, expected a type from 0 to 3')
        self.assert_invalid(b'1\n-1\n', 'line 2: pizza type -1 does not exist, expected a type from 0 to 3')

    def test_more_pizza_types_than_n(self) -> None:
        self.assert_invalid(b'5\n0 1 2 3 0\n', 'line 1: found 5 pizza types, expected 0 to N = 4')
        self.assert_invalid(b'-1\n', 'line 1: found -1 pizza types, expected 0 to N = 4')

    def test_fewer_pizza_types_than_k(self) -> None:
        self.assert_invalid(b'3\n0 2\n', 'line 2: found 2 tokens, expected K = 3 pizza types')

    def test_more_pizza_types_than_k(self) -> None:
        self.assert_invalid(b'2\n0 2 3\n', 'line 2: found 3 tokens, expected K = 2 pizza types')
        self.assert_invalid(b'0\n1\n', 'line 2: found 1 tokens, expected K = 0 pizza types')

    def test_missing_second_line(self) -> None:
        self.assert_invalid(b'3\n', 'line 2: found the end of the file, expected K = 3 pizza types')

    def test_pizza_types_split_over_two_lines(self) -> None:
        self.assert_invalid(b'3\n0 2\n3\n', 'line 2: found 2 tokens, expected K = 3 pizza types')

    def test_blank_line_before_the_pizza_types(self) -> None:
        self.assert_invalid(b'3\n\n0 2 3\n', 'line 2: found 0 tokens, expected K = 3 pizza types')

    def test_line_after_the_pizza_types(self) -> None:
        self.assert_invalid(b'3\n0 2 3\n1\n', "line 3: found '1', expected the end of the file")
        self.assert_invalid(b'0\n\n1\n', "line 3: found '1', expected the end of the file")

    def test_k_and_pizza_types_on_one_line(self) -> None:
        self.assert_invalid(b'3 0 2 3\n', 'line 1: found 4 tokens, expected the number of pizza types to order')

    def test_empty_file(self) -> None:
        self.assert_invalid(b'', 'line 1: found the end of the file, expected the number of pizza types to order')

    def test_integers_are_parsed_strictly(self) -> None:
        for token in ['+0', '0.0', '0x0', '1_0', '0,']:
            with self.subTest(token=token):
                self.assert_invalid(
                    f'1\n{token}\n'.encode('ascii'),
                    f'line 2: found {token!r}, expected an integer',
                )

    def test_non_ascii_byte(self) -> None:
        self.assert_invalid('1\n٣\n'.encode('utf-8'), 'line 2: found the byte 0xd9, expected ASCII text')

    def test_integer_with_thousands_of_digits(self) -> None:
        with self.assertRaises(judge.InvalidOutput):
            self.score_output(b'1\n' + b'1' * 5000 + b'\n')

    def test_input_with_pizza_sizes_out_of_order(self) -> None:
        with self.assertRaises(judge.InvalidInput):
            self.score_files(b'17 2\n5 2\n', b'0\n')

    def test_input_with_a_pizza_larger_than_m(self) -> None:
        with self.assertRaises(judge.InvalidInput):
            self.score_files(b'17 2\n2 18\n', b'0\n')
