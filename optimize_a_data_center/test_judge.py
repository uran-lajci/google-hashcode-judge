import os
import tempfile
import unittest

import judge

FOLDER = os.path.dirname(__file__)
EXAMPLE_IN = os.path.join(FOLDER, 'example.in')
EXAMPLE_OUT = os.path.join(FOLDER, 'example.out')


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
            self.score_files(input_data, b'x\n')

    def test_example_score_matches_statement(self) -> None:
        self.assertEqual(judge.main(EXAMPLE_IN, EXAMPLE_OUT), 5)

    def test_every_server_unallocated(self) -> None:
        self.assertEqual(self.score_output(b'x\nx\nx\nx\nx\n'), 0)

    def test_pool_without_servers_scores_zero(self) -> None:
        self.assertEqual(self.score_output(b'0 1 0\n1 0 0\n1 3 0\n0 4 0\nx\n'), 0)

    def test_pool_in_a_single_row_scores_zero(self) -> None:
        self.assertEqual(self.score_output(b'0 1 0\n1 0 1\n1 3 1\n0 4 1\nx\n'), 0)

    def test_guaranteed_capacity_drops_the_row_with_most_capacity(self) -> None:
        # Pool 0 has 10 + 1 in row 0 and 5 in row 1, pool 1 has 5 in row 0 and 10 in row 1.
        self.assertEqual(self.score_output(b'0 1 0\n1 0 1\n1 3 0\n0 4 1\nx\n'), 5)
        self.assertEqual(self.score_files(
            b'3 5 0 1 3\n5 7\n5 3\n5 4\n',
            b'0 0 0\n1 0 0\n2 0 0\n',
        ), 7)

    def test_single_row_scores_zero(self) -> None:
        self.assertEqual(self.score_files(b'1 5 0 1 1\n1 5\n', b'0 0 0\n'), 0)

    def test_server_fills_the_row_to_the_last_slot(self) -> None:
        self.assertEqual(self.score_files(b'2 5 0 1 2\n5 3\n5 4\n', b'0 0 0\n1 0 0\n'), 3)

    def test_any_whitespace_and_blank_lines_at_the_end(self) -> None:
        self.assertEqual(self.score_output(b' 0\t1  0 \r\n1 0 1\r\n1 3 0\r\n0 4 1\r\nx\r\n\r\n  \n'), 5)

    def test_missing_newline_at_the_end(self) -> None:
        self.assertEqual(self.score_output(b'0 1 0\n1 0 1\n1 3 0\n0 4 1\nx'), 5)

    def test_server_on_an_unavailable_slot(self) -> None:
        self.assert_invalid(
            b'0 0 0\n1 0 1\n1 3 0\n0 4 1\nx\n',
            'line 1: server 0 occupies row 0, slot 0, which is unavailable',
        )

    def test_servers_overlap(self) -> None:
        self.assert_invalid(
            b'0 1 0\n1 0 1\n1 3 0\n0 3 1\nx\n',
            'line 4: server 3 occupies row 0, slot 3, which server 0 on line 1 already occupies',
        )

    def test_servers_overlap_on_a_later_slot(self) -> None:
        self.assert_invalid(
            b'x\n1 2 1\n1 1 0\nx\nx\n',
            'line 3: server 2 occupies row 1, slot 2, which server 1 on line 2 already occupies',
        )

    def test_server_extends_beyond_the_row(self) -> None:
        self.assert_invalid(
            b'0 3 0\nx\nx\nx\nx\n',
            'line 1: server 0 of size 3 at slot 3 ends at slot 5, expected at most slot 4',
        )

    def test_row_slot_or_pool_out_of_range(self) -> None:
        cases = [
            (b'2 1 0', 'line 1: row 2 does not exist, expected a row from 0 to 1'),
            (b'-1 1 0', 'line 1: row -1 does not exist, expected a row from 0 to 1'),
            (b'0 5 0', 'line 1: slot 5 does not exist, expected a slot from 0 to 4'),
            (b'0 -1 0', 'line 1: slot -1 does not exist, expected a slot from 0 to 4'),
            (b'0 1 2', 'line 1: pool 2 does not exist, expected a pool from 0 to 1'),
            (b'0 1 -1', 'line 1: pool -1 does not exist, expected a pool from 0 to 1'),
        ]
        for line, message in cases:
            with self.subTest(line=line):
                self.assert_invalid(line + b'\nx\nx\nx\nx\n', message)

    def test_unallocated_server_is_a_lowercase_x_alone(self) -> None:
        self.assert_invalid(b'X\nx\nx\nx\nx\n', "line 1: found 'X', expected x or ar as ap")
        self.assert_invalid(b'x 0\nx\nx\nx\nx\n', 'line 1: found 2 tokens, expected x or ar as ap')
        self.assert_invalid(b'x x x\nx\nx\nx\nx\n', "line 1: found 'x', expected an integer")

    def test_wrong_number_of_tokens(self) -> None:
        self.assert_invalid(b'0 1\nx\nx\nx\nx\n', 'line 1: found 2 tokens, expected x or ar as ap')
        self.assert_invalid(b'0 1 0 0\nx\nx\nx\nx\n', 'line 1: found 4 tokens, expected x or ar as ap')

    def test_blank_line_before_the_last_server(self) -> None:
        self.assert_invalid(b'x\n\nx\nx\nx\nx\n', 'line 2: found 0 tokens, expected x or ar as ap')

    def test_fewer_lines_than_servers(self) -> None:
        self.assert_invalid(b'x\nx\nx\nx\n', 'line 5: found the end of the file, expected x or ar as ap')

    def test_more_lines_than_servers(self) -> None:
        self.assert_invalid(b'x\nx\nx\nx\nx\nx\n', "line 6: found 'x', expected the end of the file")

    def test_empty_file(self) -> None:
        self.assert_invalid(b'', 'line 1: found the end of the file, expected x or ar as ap')

    def test_integers_are_parsed_strictly(self) -> None:
        for token in ['+1', '1.0', '0x1', '1_0', 'one']:
            with self.subTest(token=token):
                self.assert_invalid(
                    f'0 {token} 0\nx\nx\nx\nx\n'.encode('ascii'),
                    f'line 1: found {token!r}, expected an integer',
                )

    def test_non_ascii_byte(self) -> None:
        self.assert_invalid('x\n×\n'.encode('utf-8'), 'line 2: found the byte 0xc3, expected ASCII text')

    def test_integer_with_thousands_of_digits(self) -> None:
        with self.assertRaises(judge.InvalidOutput):
            self.score_output(b'0 ' + b'1' * 5000 + b' 0\nx\nx\nx\nx\n')

    def test_input_without_a_newline_at_the_end(self) -> None:
        self.assertEqual(self.score_files(b'2 1 0 1 2\n1 4\n1 6', b'0 0 0\n1 0 0\n'), 4)

    def test_input_with_a_duplicate_unavailable_slot(self) -> None:
        self.assert_invalid_input(b'2 5 2 2 1\n0 0\n0 0\n1 1\n')

    def test_input_out_of_range(self) -> None:
        for input_data in [
            b'0 5 0 1 1\n1 1\n',
            b'1 1001 0 1 1\n1 1\n',
            b'1 5 6 1 1\n1 1\n',
            b'1 5 0 0 1\n1 1\n',
            b'1 5 0 1 6\n1 1\n1 1\n1 1\n1 1\n1 1\n1 1\n',
            b'1 5 1 1 1\n1 0\n1 1\n',
            b'1 5 1 1 1\n0 5\n1 1\n',
            b'1 5 0 1 1\n6 1\n',
            b'1 5 0 1 1\n1 1001\n',
        ]:
            with self.subTest(input_data=input_data):
                self.assert_invalid_input(input_data)

    def test_input_breaks_the_format(self) -> None:
        for input_data in [b'1 5 0 1\n1 1\n', b'1 5 0 1 1\n1  1\n', b'1 5 0 1 1\r\n1 1\r\n', b'1 5 0 1 1\n+1 1\n']:
            with self.subTest(input_data=input_data):
                self.assert_invalid_input(input_data)

    def test_input_with_fewer_servers_than_m(self) -> None:
        self.assert_invalid_input(b'1 5 0 1 2\n1 1\n')

    def test_input_with_more_servers_than_m(self) -> None:
        self.assert_invalid_input(b'1 5 0 1 1\n1 1\n1 1\n')
