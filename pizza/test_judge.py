import os
import tempfile
import unittest

import judge

FOLDER = os.path.dirname(__file__)
EXAMPLE_IN = os.path.join(FOLDER, 'example.in')


class TestJudge(unittest.TestCase):
    def score_output(self, output: bytes) -> int:
        with tempfile.TemporaryDirectory() as folder:
            output_file = os.path.join(folder, 'output.out')
            with open(output_file, 'wb') as file:
                file.write(output)
            return judge.main(EXAMPLE_IN, output_file)

    def assert_invalid(self, output: bytes, message: str) -> None:
        with self.assertRaises(judge.InvalidOutput) as context:
            self.score_output(output)
        self.assertEqual(str(context.exception), message)

    def test_example_score_matches_statement(self) -> None:
        score = judge.main(EXAMPLE_IN, os.path.join(FOLDER, 'example.out'))
        self.assertEqual(score, 15)

    def test_rows_and_columns_in_either_order(self) -> None:
        self.assertEqual(self.score_output(b'3\n2 1 0 0\n2 2 0 2\n2 4 0 3\n'), 15)

    def test_no_slices(self) -> None:
        self.assertEqual(self.score_output(b'0\n'), 0)

    def test_any_whitespace_and_blank_lines_at_the_end(self) -> None:
        self.assertEqual(self.score_output(b'3\r\n0\t0 2  1 \r\n0 2 2 2\r\n0 3 2 4\r\n\r\n  \n'), 15)

    def test_same_slice_twice(self) -> None:
        self.assert_invalid(
            b'2\n0 0 2 1\n0 0 2 1\n',
            'line 3: cell [0, 0] is already in the slice on line 2',
        )

    def test_crossing_slices_without_a_corner_inside_each_other(self) -> None:
        self.assert_invalid(
            b'2\n1 0 1 4\n0 2 2 2\n',
            'line 3: cell [1, 2] is already in the slice on line 2',
        )

    def test_too_many_cells(self) -> None:
        self.assert_invalid(b'1\n0 0 2 2\n', 'line 2: the slice has 9 cells, expected at most 6')

    def test_too_few_mushrooms(self) -> None:
        self.assert_invalid(b'1\n0 0 0 4\n', 'line 2: the slice has 0 cells of mushroom, expected at least 1')

    def test_too_few_tomatoes(self) -> None:
        self.assert_invalid(b'1\n1 1 1 3\n', 'line 2: the slice has 0 cells of tomato, expected at least 1')

    def test_cell_outside_the_pizza(self) -> None:
        self.assert_invalid(b'1\n0 0 3 1\n', 'line 2: row 3 is outside the pizza, expected a row from 0 to 2')
        self.assert_invalid(
            b'1\n0 -1 2 0\n',
            'line 2: column -1 is outside the pizza, expected a column from 0 to 4',
        )

    def test_more_slices_than_cells(self) -> None:
        self.assert_invalid(b'16\n', 'line 1: found 16 slices, expected 0 to 15')

    def test_fewer_slice_lines_than_slices(self) -> None:
        self.assert_invalid(
            b'4\n0 0 2 1\n0 2 2 2\n0 3 2 4\n',
            'line 5: found the end of the file, expected a slice as r1 c1 r2 c2',
        )

    def test_more_slice_lines_than_slices(self) -> None:
        self.assert_invalid(
            b'2\n0 0 2 1\n0 2 2 2\n0 3 2 4\n',
            "line 4: found '0 3 2 4', expected the end of the file",
        )

    def test_blank_line_between_slices(self) -> None:
        self.assert_invalid(
            b'3\n0 0 2 1\n\n0 2 2 2\n0 3 2 4\n',
            'line 3: found 0 tokens, expected a slice as r1 c1 r2 c2',
        )

    def test_wrong_number_of_tokens(self) -> None:
        self.assert_invalid(b'1\n0 0 2\n', 'line 2: found 3 tokens, expected a slice as r1 c1 r2 c2')
        self.assert_invalid(b'1 0 0 2 1\n', 'line 1: found 5 tokens, expected the number of slices')

    def test_empty_file(self) -> None:
        self.assert_invalid(b'', 'line 1: found the end of the file, expected the number of slices')

    def test_integers_are_parsed_strictly(self) -> None:
        for token in ['+0', '0.0', '0x0', '1_0', '0,']:
            with self.subTest(token=token):
                self.assert_invalid(
                    f'1\n{token} 0 2 1\n'.encode('ascii'),
                    f'line 2: found {token!r}, expected an integer',
                )

    def test_non_ascii_byte(self) -> None:
        self.assert_invalid(
            '1\n0 0 2 ١\n'.encode('utf-8'),
            'line 2: found the byte 0xd9, expected ASCII text',
        )

    def test_integer_with_thousands_of_digits(self) -> None:
        with self.assertRaises(judge.InvalidOutput):
            self.score_output(b'1\n0 0 2 ' + b'1' * 5000 + b'\n')
