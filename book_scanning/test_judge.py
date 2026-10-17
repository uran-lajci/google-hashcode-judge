import os
import tempfile
import unittest

import judge

FOLDER = os.path.dirname(__file__)
EXAMPLE_IN = os.path.join(FOLDER, 'example.in')
EXAMPLE_OUT = os.path.join(FOLDER, 'example.out')

# One library that signs up on day 0 and ships one book per day from day 1, so book 1 ships on day 2.
LAST_DAY_IN = b'2 1 3\n5 7\n2 1 1\n0 1\n'
DAY_AFTER_THE_LAST_IN = b'2 1 2\n5 7\n2 1 1\n0 1\n'

# Library 0 signs up on days 0 and 1 and ships on day 2, the last day. Library 1 then signs up on day 2, too late.
LATE_SIGNUP_IN = b'2 2 3\n5 7\n1 2 1\n0\n1 1 1\n1\n'


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
        self.assertEqual(judge.main(EXAMPLE_IN, EXAMPLE_OUT), 16)

    def test_best_order_scans_every_book(self) -> None:
        self.assertEqual(self.score_output(b'2\n0 5\n0 1 2 3 4\n1 1\n5\n'), 21)

    def test_order_of_the_books_decides_which_ship_in_time(self) -> None:
        # Library 0 ships on days 5 and 6 only, so 4 of its 5 books are scanned.
        self.assertEqual(self.score_output(b'2\n1 1\n5\n0 5\n0 1 2 3 4\n'), 16)
        self.assertEqual(self.score_output(b'2\n1 1\n5\n0 5\n4 3 2 1 0\n'), 20)

    def test_book_shipped_on_the_last_day_counts(self) -> None:
        self.assertEqual(self.score_files(LAST_DAY_IN, b'1\n0 2\n0 1\n'), 12)

    def test_book_shipped_after_the_last_day_is_ignored(self) -> None:
        self.assertEqual(self.score_files(DAY_AFTER_THE_LAST_IN, b'1\n0 2\n0 1\n'), 5)

    def test_library_signed_up_too_late_is_ignored(self) -> None:
        self.assertEqual(self.score_files(LATE_SIGNUP_IN, b'2\n0 1\n0\n1 1\n1\n'), 5)
        self.assertEqual(self.score_files(LATE_SIGNUP_IN, b'2\n1 1\n1\n0 1\n0\n'), 7)

    def test_library_signed_up_too_late_is_still_checked(self) -> None:
        with self.assertRaises(judge.InvalidOutput) as context:
            self.score_files(LATE_SIGNUP_IN, b'2\n0 1\n0\n1 1\n0\n')
        self.assertEqual(str(context.exception), 'line 5: book 0 is not in library 1')

    def test_book_shipped_by_two_libraries_counts_once(self) -> None:
        self.assertEqual(self.score_output(b'2\n1 1\n3\n0 1\n3\n'), 6)

    def test_no_library_scores_zero(self) -> None:
        self.assertEqual(self.score_output(b'0\n'), 0)

    def test_library_count_out_of_range(self) -> None:
        self.assert_invalid(b'-1\n', 'line 1: found A = -1, expected 0 to L = 2')
        self.assert_invalid(b'3\n0 1\n0\n1 1\n3\n0 1\n1\n', 'line 1: found A = 3, expected 0 to L = 2')

    def test_library_count_line_with_more_than_one_token(self) -> None:
        self.assert_invalid(b'1 0\n', 'line 1: found 2 tokens, expected A')

    def test_library_out_of_range(self) -> None:
        self.assert_invalid(b'1\n2 1\n0\n', 'line 2: library 2 does not exist, expected an ID from 0 to 1')
        self.assert_invalid(b'1\n-1 1\n0\n', 'line 2: library -1 does not exist, expected an ID from 0 to 1')

    def test_library_described_twice(self) -> None:
        self.assert_invalid(
            b'2\n1 1\n3\n1 1\n2\n', 'line 4: library 1 is described a second time, first described on line 2'
        )

    def test_book_count_out_of_range(self) -> None:
        self.assert_invalid(b'1\n1 0\n\n', 'line 2: found K = 0, expected 1 to N = 4 for library 1')
        self.assert_invalid(b'1\n1 5\n3 2 5 0 0\n', 'line 2: found K = 5, expected 1 to N = 4 for library 1')

    def test_library_line_with_wrong_token_count(self) -> None:
        self.assert_invalid(b'1\n1\n3\n', 'line 2: found 1 tokens, expected the library ID Y and the book count K')
        self.assert_invalid(b'1\n1 1 1\n3\n', 'line 2: found 3 tokens, expected the library ID Y and the book count K')

    def test_book_line_with_a_different_count_than_k(self) -> None:
        self.assert_invalid(b'1\n1 2\n3\n', 'line 3: found 1 book IDs, expected K = 2 book IDs')
        self.assert_invalid(b'1\n1 2\n3 2 5\n', 'line 3: found 3 book IDs, expected K = 2 book IDs')

    def test_book_out_of_range(self) -> None:
        self.assert_invalid(b'1\n1 1\n6\n', 'line 3: book 6 does not exist, expected an ID from 0 to 5')
        self.assert_invalid(b'1\n1 1\n-1\n', 'line 3: book -1 does not exist, expected an ID from 0 to 5')

    def test_book_not_in_the_library(self) -> None:
        self.assert_invalid(b'1\n1 1\n1\n', 'line 3: book 1 is not in library 1')

    def test_book_not_in_the_library_after_the_deadline(self) -> None:
        # After library 1, library 0 ships on days 5 and 6 only, so its fifth book would ship on day 7.
        self.assert_invalid(b'2\n1 1\n5\n0 5\n0 1 2 3 5\n', 'line 5: book 5 is not in library 0')

    def test_book_listed_twice_for_one_library(self) -> None:
        self.assert_invalid(
            b'1\n1 3\n3 2 3\n', 'line 3: book 3 is listed a second time for library 1, expected no duplicates'
        )

    def test_fewer_libraries_than_a(self) -> None:
        self.assert_invalid(
            b'2\n1 1\n3\n', 'line 4: found the end of the file, expected the library ID Y and the book count K'
        )
        self.assert_invalid(b'1\n1 1\n', 'line 3: found the end of the file, expected K = 1 book IDs')

    def test_more_libraries_than_a(self) -> None:
        self.assert_invalid(b'1\n1 1\n3\n0 1\n0\n', "line 4: found '0 1', expected the end of the file")

    def test_any_whitespace_and_blank_lines_at_the_end(self) -> None:
        self.assertEqual(self.score_output(b' 2 \r\n1\t3\r\n5  2 3 \n0 5\n0 1 2 3 4\r\n\r\n  \n'), 16)

    def test_missing_newline_at_the_end(self) -> None:
        self.assertEqual(self.score_output(b'2\n1 3\n5 2 3\n0 5\n0 1 2 3 4'), 16)

    def test_empty_file(self) -> None:
        self.assert_invalid(b'', 'line 1: found the end of the file, expected A')

    def test_integers_are_parsed_strictly(self) -> None:
        for token in ['+3', '3.0', '0x3', '0_3', 'three']:
            with self.subTest(token=token):
                self.assert_invalid(
                    f'1\n1 1\n{token}\n'.encode('ascii'), f'line 3: found {token!r}, expected an integer'
                )

    def test_non_ascii_byte(self) -> None:
        self.assert_invalid('1\n1 1\n٣\n'.encode('utf-8'), 'line 3: found the byte 0xd9, expected ASCII text')

    def test_integer_with_thousands_of_digits(self) -> None:
        with self.assertRaises(judge.InvalidOutput):
            self.score_output(b'1\n1 ' + b'1' * 5000 + b'\n3\n')

    def test_input_without_a_newline_at_the_end(self) -> None:
        self.assertEqual(self.score_files(LAST_DAY_IN.rstrip(b'\n'), b'1\n0 2\n0 1\n'), 12)

    def test_input_out_of_range(self) -> None:
        for input_data in [
            b'0 1 1\n\n1 1 1\n0\n',
            b'1 0 1\n5\n',
            b'1 1 0\n5\n1 1 1\n0\n',
            b'100001 1 1\n' + b'0 ' * 100000 + b'0\n1 1 1\n0\n',
            b'1 1 1\n1001\n1 1 1\n0\n',
            b'1 1 1\n5\n1 0 1\n0\n',
            b'1 1 1\n5\n1 1 0\n0\n',
            b'1 1 1\n5\n1 1 1\n1\n',
        ]:
            with self.subTest(input_data=input_data[:20]):
                self.assert_invalid_input(input_data)

    def test_input_with_a_book_twice_in_one_library(self) -> None:
        self.assert_invalid_input(b'2 1 1\n5 7\n2 1 1\n0 0\n')

    def test_input_breaks_the_format(self) -> None:
        for input_data in [
            b'1 1 1\n5\n1 1 1\n0 1\n',
            b'1 1 1\n5\n2 1 1\n0\n',
            b'1 1 1\n5 7\n1 1 1\n0\n',
            b'1 1 1\n5\n1 1\n0\n',
            b'1  1 1\n5\n1 1 1\n0\n',
            b'1 1 1\n5\n1 1 1\n0 \n',
            b'1 1 1\n5\n1 1 1\r\n0\n',
            b'1 1 1\n+5\n1 1 1\n0\n',
        ]:
            with self.subTest(input_data=input_data):
                self.assert_invalid_input(input_data)

    def test_input_with_fewer_libraries_than_l(self) -> None:
        self.assert_invalid_input(b'1 2 1\n5\n1 1 1\n0\n')

    def test_input_with_more_libraries_than_l(self) -> None:
        self.assert_invalid_input(b'1 1 1\n5\n1 1 1\n0\n1 1 1\n0\n')
