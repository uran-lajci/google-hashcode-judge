import os
import tempfile
import unittest

import judge

FOLDER = os.path.dirname(__file__)
EXAMPLE_IN = os.path.join(FOLDER, 'example.in')
EXAMPLE_OUT = os.path.join(FOLDER, 'example.out')


def example_input_with_balloons(balloon_count: int) -> bytes:
    with open(EXAMPLE_IN, 'rb') as file:
        lines = file.read().split(b'\n')
    lines[1] = f'2 1 {balloon_count} 5'.encode('ascii')
    return b'\n'.join(lines)


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
        self.assertEqual(judge.main(EXAMPLE_IN, EXAMPLE_OUT), 5)

    def test_balloon_on_the_ground_covers_nothing(self) -> None:
        # The starting cell [1, 2] is within radius 1 of the target [0, 2].
        self.assertEqual(self.score_output(b'0\n0\n0\n0\n0\n'), 0)

    def test_balloon_moves_with_the_wind_at_its_altitude(self) -> None:
        # At altitude 1 it drifts east along row 1 and covers [0, 4] from [1, 4] and [0, 2] from [1, 2].
        self.assertEqual(self.score_output(b'1\n0\n0\n0\n0\n'), 2)

    def test_lost_balloon_covers_nothing(self) -> None:
        # The balloon covers both targets from [0, 3] at the end of turn 1, then the wind blows it north off the grid.
        self.assertEqual(self.score_output(b'1\n1\n0\n0\n0\n'), 2)

    def test_target_covered_by_two_balloons_scores_once(self) -> None:
        self.assertEqual(self.score_files(example_input_with_balloons(2), b'1 1\n1 1\n1 1\n0 0\n0 0\n'), 5)

    def test_balloons_score_together(self) -> None:
        # The first balloon scores 2 at the end of turn 1, then is lost. The second follows the example one turn later
        # and scores 2, 1 and 1 at the end of turns 2, 3 and 4.
        self.assertEqual(self.score_files(example_input_with_balloons(2), b'1 0\n1 1\n0 1\n0 1\n0 0\n'), 2 + 4)

    def test_windows_line_endings_trailing_spaces_and_blank_lines(self) -> None:
        self.assertEqual(self.score_output(b'1 \r\n1 \r\n1 \r\n0 \r\n0 \r\n\r\n\n'), 5)

    def test_balloon_on_the_ground_cannot_go_down(self) -> None:
        self.assert_invalid(
            b'-1\n0\n0\n0\n0\n', 'line 1: balloon 0 is on the ground, expected 0 to stay or 1 to launch'
        )

    def test_launched_balloon_cannot_land(self) -> None:
        self.assert_invalid(b'1\n-1\n0\n0\n0\n', 'line 2: balloon 0 would reach altitude 0, expected 1 to A = 3')

    def test_balloon_cannot_rise_above_a(self) -> None:
        self.assert_invalid(b'1\n1\n1\n1\n0\n', 'line 4: balloon 0 would reach altitude 4, expected 1 to A = 3')

    def test_lost_balloon_still_stays_between_1_and_a(self) -> None:
        # The balloon is lost at the end of turn 2.
        self.assert_invalid(b'1\n1\n0\n1\n1\n', 'line 5: balloon 0 would reach altitude 4, expected 1 to A = 3')
        self.assert_invalid(b'1\n1\n0\n-1\n-1\n', 'line 5: balloon 0 would reach altitude 0, expected 1 to A = 3')

    def test_adjustment_out_of_range(self) -> None:
        self.assert_invalid(b'2\n0\n0\n0\n0\n', 'line 1: found 2 for balloon 0, expected -1, 0 or 1')

    def test_adjustment_that_is_not_an_integer(self) -> None:
        self.assert_invalid(b'+1\n0\n0\n0\n0\n', "line 1: found '+1', expected an integer")

    def test_line_with_the_wrong_number_of_adjustments(self) -> None:
        self.assert_invalid(b'1 0\n0\n0\n0\n0\n', 'line 1: found 2 tokens, expected B = 1 altitude adjustments')
        self.assert_invalid(b'1\n\n0\n0\n0\n', 'line 2: found 0 tokens, expected B = 1 altitude adjustments')

    def test_fewer_than_t_lines(self) -> None:
        self.assert_invalid(b'1\n1\n', 'line 3: found the end of the file, expected B = 1 altitude adjustments')

    def test_more_than_t_lines(self) -> None:
        self.assert_invalid(b'1\n1\n1\n0\n0\n0\n', "line 6: found '0', expected the end of the file")

    def test_more_than_1000_targets_is_a_valid_input(self) -> None:
        # The statement caps L at 1000, but the official input has L = 2250.
        cells = [(row, column) for row in range(2) for column in range(501)][:1001]
        targets = ''.join(f'{row} {column}\n' for row, column in cells)
        winds = (' '.join(['0 0'] * 501) + '\n') * 2
        input_data = f'2 501 1\n1001 0 1 1\n0 0\n{targets}{winds}'.encode('ascii')
        self.assertEqual(self.score_files(input_data, b'1\n'), 1)

    def test_target_listed_twice_is_an_invalid_input(self) -> None:
        with open(EXAMPLE_IN, 'rb') as file:
            input_data = file.read().replace(b'0 4\n', b'0 2\n', 1)
        with self.assertRaises(judge.InvalidInput):
            self.score_files(input_data, b'1\n1\n1\n0\n0\n')
