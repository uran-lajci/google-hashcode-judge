import os
import tempfile
import unittest

import judge

FOLDER = os.path.dirname(__file__)
EXAMPLE_IN = os.path.join(FOLDER, 'example.in')
EXAMPLE_OUT = os.path.join(FOLDER, 'example.out')

# Photo 0 is horizontal with 6 tags. Vertical photos 1 and 2 share 3 of them, so their slide has 5 tags, not 8.
SHARED_TAGS_IN = b'3\nH 6 a b c x y z\nV 4 a b c p\nV 4 a b c q\n'


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
            self.score_files(input_data, b'1\n0\n')

    def test_example_score_matches_statement(self) -> None:
        self.assertEqual(judge.main(EXAMPLE_IN, EXAMPLE_OUT), 2)

    def test_transition_from_the_statement(self) -> None:
        # [garden, cat] to [selfie, smile, garden] is min(1, 1, 2) = 1.
        self.assertEqual(self.score_output(b'2\n3\n1 2\n'), 1)

    def test_single_slide_scores_zero(self) -> None:
        self.assertEqual(self.score_output(b'1\n0\n'), 0)
        self.assertEqual(self.score_output(b'1\n1 2\n'), 0)

    def test_transition_without_common_tags_scores_zero(self) -> None:
        self.assertEqual(self.score_output(b'2\n0\n1 2\n'), 0)

    def test_order_of_the_two_vertical_photos_does_not_matter(self) -> None:
        self.assertEqual(self.score_output(b'3\n0\n3\n2 1\n'), 2)

    def test_tags_of_two_vertical_photos_are_their_union(self) -> None:
        # 3 common tags, 3 only in photo 0, and 2 only in the slide [a, b, c, p, q].
        self.assertEqual(self.score_files(SHARED_TAGS_IN, b'2\n0\n1 2\n'), 2)
        self.assertEqual(self.score_files(SHARED_TAGS_IN, b'2\n2 1\n0\n'), 2)

    def test_not_every_photo_has_to_be_used(self) -> None:
        self.assertEqual(self.score_output(b'2\n0\n3\n'), 1)

    def test_slide_count_out_of_range(self) -> None:
        self.assert_invalid(b'0\n', 'line 1: found S = 0, expected 1 to N = 4')
        self.assert_invalid(b'-1\n', 'line 1: found S = -1, expected 1 to N = 4')
        self.assert_invalid(b'5\n0\n3\n1 2\n0\n3\n', 'line 1: found S = 5, expected 1 to N = 4')

    def test_slide_count_line_with_more_than_one_token(self) -> None:
        self.assert_invalid(b'1 0\n', 'line 1: found 2 tokens, expected S')

    def test_fewer_slides_than_slide_count(self) -> None:
        self.assert_invalid(
            b'3\n0\n3\n', 'line 4: found the end of the file, expected one horizontal photo or two vertical photos'
        )

    def test_more_slides_than_slide_count(self) -> None:
        self.assert_invalid(b'2\n0\n3\n1 2\n', "line 4: found '1 2', expected the end of the file")

    def test_vertical_photo_alone_on_a_slide(self) -> None:
        self.assert_invalid(b'2\n0\n1\n', 'line 3: photo 1 is vertical, expected a horizontal photo')

    def test_horizontal_photo_in_a_pair(self) -> None:
        self.assert_invalid(b'1\n0 3\n', 'line 2: photo 0 is horizontal, expected two vertical photos')
        self.assert_invalid(b'1\n1 3\n', 'line 2: photo 3 is horizontal, expected two vertical photos')

    def test_three_photos_on_a_slide(self) -> None:
        self.assert_invalid(
            b'1\n1 2 0\n', 'line 2: found 3 photo IDs, expected one horizontal photo or two vertical photos'
        )

    def test_blank_line_for_a_slide(self) -> None:
        self.assert_invalid(
            b'2\n0\n\n3\n', 'line 3: found 0 photo IDs, expected one horizontal photo or two vertical photos'
        )

    def test_photo_out_of_range(self) -> None:
        cases = [
            (b'1\n4\n', 'line 2: photo 4 does not exist, expected an ID from 0 to 3'),
            (b'1\n-1\n', 'line 2: photo -1 does not exist, expected an ID from 0 to 3'),
            (b'1\n1 -2\n', 'line 2: photo -2 does not exist, expected an ID from 0 to 3'),
        ]
        for output, message in cases:
            with self.subTest(output=output):
                self.assert_invalid(output, message)

    def test_photo_used_on_two_slides(self) -> None:
        self.assert_invalid(b'3\n0\n3\n0\n', 'line 4: photo 0 is used a second time, first used on line 2')

    def test_vertical_photo_twice_on_one_slide(self) -> None:
        self.assert_invalid(b'1\n1 1\n', 'line 2: photo 1 is used a second time, first used on line 2')

    def test_any_whitespace_and_blank_lines_at_the_end(self) -> None:
        self.assertEqual(self.score_output(b' 3 \r\n0\r\n\t3\n1   2\r\n\r\n  \n'), 2)

    def test_missing_newline_at_the_end(self) -> None:
        self.assertEqual(self.score_output(b'3\n0\n3\n1 2'), 2)

    def test_empty_file(self) -> None:
        self.assert_invalid(b'', 'line 1: found the end of the file, expected S')

    def test_integers_are_parsed_strictly(self) -> None:
        for token in ['+1', '1.0', '0x1', '1_0', 'one']:
            with self.subTest(token=token):
                self.assert_invalid(f'1\n{token} 2\n'.encode('ascii'), f'line 2: found {token!r}, expected an integer')

    def test_non_ascii_byte(self) -> None:
        self.assert_invalid('2\n0\n٣\n'.encode('utf-8'), 'line 3: found the byte 0xd9, expected ASCII text')

    def test_integer_with_thousands_of_digits(self) -> None:
        with self.assertRaises(judge.InvalidOutput):
            self.score_output(b'1\n' + b'1' * 5000 + b'\n')

    def test_input_without_a_newline_at_the_end(self) -> None:
        self.assertEqual(self.score_files(SHARED_TAGS_IN.rstrip(b'\n'), b'2\n0\n1 2\n'), 2)

    def test_input_out_of_range(self) -> None:
        for input_data in [
            b'0\n',
            b'100001\n' + b'H 1 a\n' * 100001,
            b'1\nH 0\n',
            b'1\nH 101 ' + b' '.join(f't{i}'.encode('ascii') for i in range(101)) + b'\n',
        ]:
            with self.subTest(input_data=input_data[:20]):
                self.assert_invalid_input(input_data)

    def test_input_with_a_bad_tag(self) -> None:
        for tag in [b'Cat', b'cat-1', b'abcdefghijk']:
            with self.subTest(tag=tag):
                self.assert_invalid_input(b'1\nH 1 ' + tag + b'\n')

    def test_input_with_a_tag_twice_on_one_photo(self) -> None:
        self.assert_invalid_input(b'1\nH 2 cat cat\n')

    def test_input_breaks_the_format(self) -> None:
        for input_data in [
            b'1\nX 1 cat\n',
            b'1\nh 1 cat\n',
            b'1\nH 2 cat\n',
            b'1\nH 1 cat dog\n',
            b'1\nH  1 cat\n',
            b'1\nH 1 cat\r\n',
            b'1\nH +1 cat\n',
            b'+1\nH 1 cat\n',
        ]:
            with self.subTest(input_data=input_data):
                self.assert_invalid_input(input_data)

    def test_input_with_fewer_photos_than_n(self) -> None:
        self.assert_invalid_input(b'2\nH 1 cat\n')

    def test_input_with_more_photos_than_n(self) -> None:
        self.assert_invalid_input(b'1\nH 1 cat\nH 1 dog\n')
