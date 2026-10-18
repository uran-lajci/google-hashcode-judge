import os
import tempfile
import unittest

import judge

FOLDER = os.path.dirname(__file__)
EXAMPLE_IN = os.path.join(FOLDER, 'example.in')
EXAMPLE_OUT = os.path.join(FOLDER, 'example.out')

# In the example, T = 15 and D = 3. Up to 15 kg the sleigh accelerates by at most 8, up to 30 kg by 6, up to 45 kg by 4
# and up to 60 kg by 2. Olivia (score 1, 10 kg) lives at [5, 1], Emma (2, 10 kg) at [-10, 1], Liam (5, 10 kg) at [8, 4]
# and Bob (10, 15 kg) at [0, -100].
EXAMPLE_INPUT = b'15 3 4 4\n15 8\n30 6\n45 4\n60 2\nOlivia 1 10 5 1\nEmma 2 10 -10 1\nLiam 5 10 8 4\nBob 10 15 0 -100'

# From [3, 0], the edge of the range of Lapland, Near at [6, 0] is exactly D = 3 away, Diagonal at [5, 2] is sqrt(8)
# away and Far at [4, 3] is sqrt(10) away.
RANGE_INPUT = b'10 3 1 3\n100 10\nNear 1 1 6 0\nDiagonal 2 1 5 2\nFar 4 1 4 3\n'


def actions(*lines: str) -> bytes:
    return '\n'.join([str(len(lines)), *lines]).encode('ascii') + b'\n'


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
        return self.score_files(EXAMPLE_INPUT, output)

    def assert_invalid(self, output: bytes, message: str, input_data: bytes = EXAMPLE_INPUT) -> None:
        with self.assertRaises(judge.InvalidOutput) as context:
            self.score_files(input_data, output)
        self.assertEqual(str(context.exception), message)

    def assert_invalid_input(self, input_data: bytes) -> None:
        with self.assertRaises(judge.InvalidInput):
            self.score_files(input_data, b'0\n')

    def test_example_score_matches_statement(self) -> None:
        self.assertEqual(judge.main(EXAMPLE_IN, EXAMPLE_OUT), 16)

    def test_example_input_is_the_data_set(self) -> None:
        with open(EXAMPLE_IN, 'rb') as file:
            self.assertEqual(file.read(), EXAMPLE_INPUT)

    def test_no_action_scores_zero(self) -> None:
        self.assertEqual(self.score_output(b'0\n'), 0)

    def test_gift_left_on_the_sleigh_scores_nothing(self) -> None:
        self.assertEqual(self.score_output(actions('LoadGift Olivia', 'LoadGift Bob')), 0)

    def test_gift_within_the_range_is_delivered(self) -> None:
        output = actions(
            'LoadGift Near',
            'LoadGift Diagonal',
            'LoadCarrots 1',
            'AccRight 3',
            'Float 1',
            'DeliverGift Near',
            'DeliverGift Diagonal',
        )
        self.assertEqual(self.score_files(RANGE_INPUT, output), 1 + 2)

    def test_gift_out_of_the_range_is_not_delivered(self) -> None:
        output = actions('LoadGift Far', 'LoadCarrots 1', 'AccRight 3', 'Float 1', 'DeliverGift Far')
        self.assert_invalid(
            output,
            'line 6: the sleigh at [3, 0] is further than D = 3 from Far at [4, 3]',
            RANGE_INPUT,
        )

    def test_gift_can_be_loaded_and_delivered_at_once(self) -> None:
        output = actions('LoadCarrots 1', 'AccRight 3', 'Float 1', 'LoadGift Near', 'DeliverGift Near')
        self.assertEqual(self.score_files(RANGE_INPUT, output), 1)

    def test_loading_exactly_d_from_lapland(self) -> None:
        output = actions('LoadCarrots 1', 'AccRight 3', 'Float 1', 'LoadGift Far')
        self.assertEqual(self.score_files(RANGE_INPUT, output), 0)

    def test_loading_carrots_further_than_d_from_lapland(self) -> None:
        self.assert_invalid(
            actions('LoadCarrots 1', 'AccRight 4', 'Float 1', 'LoadCarrots 1'),
            'line 5: the sleigh at [4, 0] is further than D = 3 from [0, 0], so it cannot load carrots',
        )

    def test_loading_a_gift_further_than_d_from_lapland(self) -> None:
        self.assert_invalid(
            actions('LoadCarrots 1', 'AccUp 4', 'Float 1', 'LoadGift Olivia'),
            'line 5: the sleigh at [0, 4] is further than D = 3 from [0, 0], so it cannot load a gift',
        )

    def test_gift_is_loaded_at_most_once(self) -> None:
        self.assert_invalid(
            actions('LoadGift Olivia', 'LoadGift Olivia'),
            'line 3: the gift for Olivia is loaded a second time, first loaded on line 2',
        )

    def test_delivered_gift_cannot_be_loaded_again(self) -> None:
        output = actions(
            'LoadCarrots 1', 'AccRight 3', 'Float 1', 'LoadGift Near', 'DeliverGift Near', 'LoadGift Near'
        )
        self.assert_invalid(
            output,
            'line 7: the gift for Near is loaded a second time, first loaded on line 5',
            RANGE_INPUT,
        )

    def test_gift_is_delivered_at_most_once(self) -> None:
        output = actions(
            'LoadCarrots 1', 'AccRight 3', 'Float 1', 'LoadGift Near', 'DeliverGift Near', 'DeliverGift Near'
        )
        self.assert_invalid(
            output, 'line 7: the gift for Near is delivered a second time, first delivered on line 6', RANGE_INPUT
        )

    def test_gift_must_be_loaded_before_delivery(self) -> None:
        output = actions('LoadCarrots 1', 'AccRight 3', 'Float 1', 'DeliverGift Near')
        self.assert_invalid(output, 'line 5: the gift for Near is not on the sleigh', RANGE_INPUT)

    def test_unknown_child(self) -> None:
        self.assert_invalid(actions('LoadGift olivia'), "line 2: there is no gift for a child named 'olivia'")
        self.assert_invalid(actions('DeliverGift Santa'), "line 2: there is no gift for a child named 'Santa'")

    def test_maximum_acceleration_includes_the_upper_weight_limit(self) -> None:
        self.assertEqual(self.score_output(actions('LoadCarrots 15', 'AccUp 8')), 0)
        self.assert_invalid(
            actions('LoadCarrots 16', 'AccUp 7'),
            'line 3: found an acceleration of 7, expected 0 to 6 for a sleigh of 16 kg',
        )

    def test_weight_counts_gifts_and_the_carrot_about_to_be_eaten(self) -> None:
        self.assert_invalid(
            actions('LoadGift Olivia', 'LoadCarrots 6', 'AccUp 7'),
            'line 4: found an acceleration of 7, expected 0 to 6 for a sleigh of 16 kg',
        )

    def test_eaten_carrot_lowers_the_weight(self) -> None:
        self.assertEqual(self.score_output(actions('LoadCarrots 16', 'AccUp 6', 'Float 1', 'AccDown 8')), 0)

    def test_delivered_gift_lowers_the_weight(self) -> None:
        # At [4, 0], the sleigh carries Olivia and 6 carrots, 16 kg, until it delivers her gift.
        self.assert_invalid(
            actions('LoadGift Olivia', 'LoadCarrots 7', 'AccRight 4', 'Float 1', 'AccUp 7'),
            'line 6: found an acceleration of 7, expected 0 to 6 for a sleigh of 16 kg',
        )
        output = actions('LoadGift Olivia', 'LoadCarrots 7', 'AccRight 4', 'Float 1', 'DeliverGift Olivia', 'AccUp 7')
        self.assertEqual(self.score_output(output), 1)

    def test_sleigh_too_heavy_to_accelerate(self) -> None:
        self.assertEqual(self.score_output(actions('LoadCarrots 61', 'AccUp 0')), 0)
        self.assert_invalid(
            actions('LoadCarrots 61', 'AccUp 1'),
            'line 3: found an acceleration of 1, expected 0 to 0 for a sleigh of 61 kg',
        )

    def test_acceleration_needs_a_carrot(self) -> None:
        self.assert_invalid(actions('AccUp 0'), 'line 2: the sleigh has no carrot, so it cannot accelerate')

    def test_acceleration_by_zero_eats_a_carrot(self) -> None:
        self.assert_invalid(
            actions('LoadCarrots 1', 'AccUp 0', 'Float 1', 'AccUp 0'),
            'line 5: the sleigh has no carrot, so it cannot accelerate',
        )

    def test_negative_acceleration(self) -> None:
        self.assert_invalid(
            actions('LoadCarrots 1', 'AccUp -1'),
            'line 3: found an acceleration of -1, expected 0 to 8 for a sleigh of 1 kg',
        )

    def test_two_accelerations_need_a_float_between_them(self) -> None:
        self.assert_invalid(
            actions('LoadCarrots 2', 'AccUp 1', 'AccLeft 1', 'Float 1'),
            'line 4: the sleigh accelerates again without a Float since line 3',
        )
        self.assert_invalid(
            actions('LoadCarrots 2', 'Float 1', 'AccUp 1', 'LoadCarrots 1', 'AccDown 1'),
            'line 6: the sleigh accelerates again without a Float since line 4',
        )

    def test_acceleration_after_the_last_float(self) -> None:
        self.assertEqual(self.score_output(actions('LoadCarrots 1', 'Float 1', 'AccUp 1')), 0)

    def test_velocity_is_kept_while_floating(self) -> None:
        # Moving right by 1 per second, the sleigh reaches [3, 0] after 3 seconds and stops there.
        output = actions(
            'LoadGift Near', 'LoadCarrots 2', 'AccRight 1', 'Float 3', 'AccLeft 1', 'Float 5', 'DeliverGift Near'
        )
        self.assertEqual(self.score_files(RANGE_INPUT, output), 1)

    def test_every_gift_of_the_example_can_be_delivered(self) -> None:
        # Two teams scored 18 on this data set. This plan, found by an exhaustive search, delivers Bob at second 14.
        output = actions(
            *['LoadGift Olivia', 'LoadGift Emma', 'LoadGift Liam', 'LoadGift Bob', 'Float 1', 'Float 1'],
            *['LoadCarrots 1', 'AccRight 2', 'Float 1', 'LoadCarrots 1', 'AccUp 1', 'LoadCarrots 3', 'Float 1'],
            *['DeliverGift Olivia', 'AccUp 1', 'Float 1', 'DeliverGift Liam', 'AccLeft 6', 'Float 1', 'AccDown 5'],
            *['Float 1', 'LoadCarrots 1', 'AccLeft 2', 'LoadCarrots 6', 'Float 1', 'DeliverGift Emma', 'AccRight 6'],
            *['Float 1', 'AccDown 5', 'Float 1', 'AccDown 6', 'Float 1', 'AccDown 6', 'Float 1', 'AccDown 6'],
            *['Float 1', 'AccRight 6', 'Float 1', 'DeliverGift Bob'],
        )
        self.assertEqual(self.score_output(output), 18)

    def test_floats_add_up_to_at_most_t(self) -> None:
        self.assertEqual(self.score_output(actions('Float 10', 'Float 5')), 0)
        self.assert_invalid(
            actions('Float 10', 'Float 6'),
            'line 3: the sleigh would float until second 16, after the time limit T = 15',
        )
        self.assert_invalid(
            actions('Float 15', 'Float 1'),
            'line 3: the sleigh would float until second 16, after the time limit T = 15',
        )

    def test_gift_delivered_once_the_time_has_run_out(self) -> None:
        # The statement forbids only floating past T, so the sleigh still delivers when it stops at second T = 10.
        output = actions(
            'LoadGift Near', 'LoadCarrots 2', 'AccRight 1', 'Float 3', 'AccLeft 1', 'Float 7', 'DeliverGift Near'
        )
        self.assertEqual(self.score_files(RANGE_INPUT, output), 1)

    def test_float_out_of_range(self) -> None:
        self.assert_invalid(actions('Float 0'), 'line 2: found the time t = 0, expected 1 to 15')
        self.assert_invalid(actions('Float 16'), 'line 2: found the time t = 16, expected 1 to 15')

    def test_carrot_count_out_of_range(self) -> None:
        self.assert_invalid(
            actions('LoadCarrots 0'), 'line 2: found the number of carrots N = 0, expected 1 to 1000000000'
        )
        self.assertEqual(self.score_output(actions('LoadCarrots 1000000000', 'AccUp 0')), 0)
        self.assert_invalid(
            actions('LoadCarrots 1000000001'),
            'line 2: found the number of carrots N = 1000000001, expected 1 to 1000000000',
        )

    def test_argument_that_is_not_an_integer(self) -> None:
        self.assert_invalid(actions('LoadCarrots 1', 'AccUp +1'), "line 3: found '+1', expected an integer")
        self.assert_invalid(actions('Float 1.0'), "line 2: found '1.0', expected an integer")

    def test_unknown_action(self) -> None:
        self.assert_invalid(
            actions('accup 1'),
            "line 2: found the action 'accup', expected AccUp, AccDown, AccLeft, AccRight, Float, LoadCarrots, "
            'LoadGift or DeliverGift',
        )

    def test_action_with_the_wrong_number_of_tokens(self) -> None:
        self.assert_invalid(actions('Float'), 'line 2: found 1 tokens, expected an action and its argument')
        self.assert_invalid(actions('Float 1 1'), 'line 2: found 3 tokens, expected an action and its argument')

    def test_count_of_actions(self) -> None:
        self.assert_invalid(b'', 'line 1: found the end of the file, expected C')
        self.assert_invalid(b'1 2\n', 'line 1: found 2 tokens, expected C')
        self.assert_invalid(b'-1\n', 'line 1: found C = -1, expected 0 to 1000000')
        self.assert_invalid(b'1000001\n', 'line 1: found C = 1000001, expected 0 to 1000000')

    def test_fewer_than_c_actions(self) -> None:
        self.assert_invalid(b'2\nLoadCarrots 1\n', 'line 3: found the end of the file, expected an action')
        self.assert_invalid(b'2\n\nLoadCarrots 1\n', 'line 2: found 0 tokens, expected an action and its argument')

    def test_more_than_c_actions(self) -> None:
        self.assert_invalid(b'1\nLoadCarrots 1\nFloat 1\n', "line 3: found 'Float 1', expected the end of the file")

    def test_windows_line_endings_trailing_spaces_and_blank_lines(self) -> None:
        with open(EXAMPLE_OUT, 'rb') as file:
            output = file.read().replace(b'\n', b' \r\n') + b'\r\n\n'
        self.assertEqual(self.score_output(output), 16)

    def test_output_that_is_not_ascii(self) -> None:
        self.assert_invalid(b'1\nLoadGift Ol\xc3\xafvia\n', 'line 2: found the byte 0xc3, expected ASCII text')

    def test_invalid_inputs(self) -> None:
        self.assert_invalid_input(EXAMPLE_INPUT.replace(b'Emma', b'Olivia'))
        self.assert_invalid_input(EXAMPLE_INPUT.replace(b'-10 1', b'5 1'))
        self.assert_invalid_input(EXAMPLE_INPUT.replace(b'-10 1', b'0 0'))
        self.assert_invalid_input(EXAMPLE_INPUT.replace(b'30 6', b'15 6'))
        self.assert_invalid_input(EXAMPLE_INPUT.replace(b'30 6', b'30 8'))
        self.assert_invalid_input(EXAMPLE_INPUT.replace(b'15 3 4 4', b'15 3 4 5'))
        self.assert_invalid_input(EXAMPLE_INPUT + b'\nAnna 1 1 1 1')
        self.assert_invalid_input(EXAMPLE_INPUT.replace(b'Bob 10 15', b'Bob 10 1001'))
