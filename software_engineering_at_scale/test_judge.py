import os
import tempfile
import unittest

import judge

FOLDER = os.path.dirname(__file__)
EXAMPLE_IN = os.path.join(FOLDER, 'example.in')
EXAMPLE_OUT = os.path.join(FOLDER, 'example.out')

# In the example, L = 10 and N = 5. Binary 0 runs se, binary 1 runs sa and sc, and binary 2 runs sb and sd. Feature foo
# (D = 3, U = 100) needs sc, sb and sd, and feature bar (D = 1, U = 20) needs sc and sa.
EXAMPLE_INPUT = b'10 2 5 3 2 5\nsa 1\nsb 2\nsc 1\nsd 2\nse 0\nfoo 3 3 100\nsc sb sd\nbar 2 1 20\nsc sa'


def schedule(*engineers: list[str]) -> bytes:
    lines = [str(len(engineers))]
    for tasks in engineers:
        lines += [str(len(tasks))] + tasks
    return '\n'.join(lines).encode('ascii') + b'\n'


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
        self.assertEqual(judge.main(EXAMPLE_IN, EXAMPLE_OUT), 220)

    def test_example_input_is_the_data_set(self) -> None:
        with open(EXAMPLE_IN, 'rb') as file:
            self.assertEqual(file.read(), EXAMPLE_INPUT)

    def test_no_engineer_scores_zero(self) -> None:
        self.assertEqual(self.score_output(b'0\n'), 0)

    def test_engineer_listed_earlier_starts_first_in_a_binary(self) -> None:
        # Listed first, bar takes 1 + 2 + 0 days and launches on day 3. Listed second, it takes 1 + 2 + 1.
        self.assertEqual(self.score_output(schedule(['impl bar 1'], ['impl foo 1'])), 20 * 7)
        self.assertEqual(self.score_output(schedule(['impl foo 1'], ['impl bar 1'])), 20 * 6)

    def test_engineer_who_finishes_on_a_day_does_not_count_for_c(self) -> None:
        # foo ends on day 5, so bar takes 1 + 2 + 0 days and launches on day 8.
        self.assertEqual(self.score_output(schedule(['impl foo 1'], ['wait 5', 'impl bar 1'])), 20 * 2)

    def test_same_feature_in_two_binaries_at_once(self) -> None:
        # bar launches on day 3, once binary 1 is done, since both of its services run there.
        self.assertEqual(self.score_output(schedule(['impl bar 1'], ['impl bar 2'])), 20 * 7)

    def test_same_feature_in_one_binary_after_the_first_engineer_is_done(self) -> None:
        self.assertEqual(self.score_output(schedule(['impl bar 1'], ['wait 3', 'impl bar 1'])), 20 * 7)

    def test_same_feature_in_one_binary_at_once(self) -> None:
        self.assert_invalid(
            schedule(['impl bar 1'], ['wait 2', 'impl bar 1']),
            'line 6: on day 2, feature bar is already being implemented in binary 1 by the task on line 3',
        )

    def test_feature_launched_on_day_l_scores_zero(self) -> None:
        self.assertEqual(self.score_output(schedule(['wait 6', 'impl bar 1'])), 20)
        self.assertEqual(self.score_output(schedule(['wait 7', 'impl bar 1'])), 0)

    def test_partial_feature_scores_zero(self) -> None:
        self.assertEqual(self.score_output(schedule(['impl foo 2'])), 0)

    def test_feature_stays_implemented_in_a_service_that_moves(self) -> None:
        # foo is done in sb on day 2, sb moves to binary 2 on day 3, and foo is done in sa on day 5.
        input_data = b'100 1 3 3 1 1\nsa 0\nsb 1\nsc 2\nfoo 2 1 10\nsa sb\n'
        self.assertEqual(self.score_files(input_data, schedule(['impl foo 1', 'move sb 2', 'impl foo 0'])), 10 * 95)

    def test_implementation_in_a_binary_without_the_feature_is_valid(self) -> None:
        self.assertEqual(self.score_output(schedule(['impl bar 0', 'impl bar 1'])), 20 * 5)

    def test_move_takes_the_size_of_the_larger_binary(self) -> None:
        # The move takes max(1, 2) days, then bar takes 1 + 3 + 0 in binary 1 and launches on day 6.
        self.assertEqual(self.score_output(schedule(['move se 1', 'impl bar 1'])), 20 * 4)

    def test_move_frees_its_binaries_on_the_day_it_ends(self) -> None:
        self.assertEqual(self.score_output(schedule(['move sc 2'], ['wait 2', 'move sa 0'])), 0)

    def test_move_to_the_binary_of_the_service(self) -> None:
        self.assert_invalid(schedule(['move sc 1']), 'line 3: on day 0, service sc already runs in binary 1')

    def test_move_while_a_feature_is_implemented_in_either_binary(self) -> None:
        message = 'line 5: on day 0, binary {} is busy with the implementation that started on line 3'
        self.assert_invalid(schedule(['impl bar 1'], ['move sa 2']), message.format(1))
        self.assert_invalid(schedule(['impl foo 2'], ['move sa 2']), message.format(2))

    def test_move_while_another_move_uses_either_binary(self) -> None:
        message = 'line 6: on day 1, binary {} is busy with the move that started on line 3'
        self.assert_invalid(schedule(['move sc 2'], ['wait 1', 'move se 1']), message.format(1))
        self.assert_invalid(schedule(['move sc 2'], ['wait 1', 'move sb 0']), message.format(2))

    def test_implementation_while_a_move_uses_the_binary(self) -> None:
        self.assert_invalid(
            schedule(['move sc 2'], ['impl bar 1']),
            'line 5: on day 0, binary 1 is busy with the move that started on line 3',
        )

    def test_engineer_listed_earlier_wins_a_binary_on_the_same_day(self) -> None:
        self.assert_invalid(
            schedule(['impl bar 1'], ['move sa 0']),
            'line 5: on day 0, binary 1 is busy with the implementation that started on line 3',
        )
        self.assert_invalid(
            schedule(['move sa 0'], ['impl bar 1']),
            'line 5: on day 0, binary 1 is busy with the move that started on line 3',
        )

    def test_binary_that_does_not_exist(self) -> None:
        message = 'line 3: on day 0, binary 3 does not exist, expected an ID from 0 to 2'
        self.assert_invalid(schedule(['impl foo 3']), message)
        self.assert_invalid(schedule(['move se 3']), message)
        self.assert_invalid(schedule(['impl foo -1']), 'line 3: binary -1 does not exist')

    def test_new_binary_exists_once_it_is_created(self) -> None:
        # N = 5, and moving se from binary 0 to the empty binary 3 takes one day.
        self.assertEqual(self.score_output(schedule(['new'], ['wait 5', 'move se 3'])), 0)
        self.assert_invalid(
            schedule(['new'], ['wait 4', 'move se 3']),
            'line 6: on day 4, binary 3 does not exist, expected an ID from 0 to 2',
        )

    def test_new_binaries_take_the_next_ids(self) -> None:
        self.assertEqual(self.score_output(schedule(['new', 'impl foo 4'], ['new'])), 0)
        self.assert_invalid(
            schedule(['new', 'impl foo 5'], ['new']),
            'line 4: on day 5, binary 5 does not exist, expected an ID from 0 to 4',
        )

    def test_tasks_that_start_on_day_l_or_later_are_ignored(self) -> None:
        self.assertEqual(self.score_output(schedule(['wait 10', 'move sc 1', 'impl foo 9'])), 0)
        self.assertEqual(self.score_output(schedule(['wait 6', 'wait 6', 'impl bar 1'], ['wait 10', 'impl bar 1'])), 0)

    def test_task_that_ends_after_l_still_takes_up_its_binary(self) -> None:
        # foo ends on day 12, after L.
        self.assert_invalid(
            schedule(['wait 7', 'impl foo 2'], ['wait 8', 'move sb 0']),
            'line 7: on day 8, binary 2 is busy with the implementation that started on line 4',
        )
        # foo ends on day 10, so bar takes 1 + 2 + 1 days and launches on day 10 as well.
        self.assertEqual(self.score_output(schedule(['wait 5', 'impl foo 1'], ['wait 6', 'impl bar 1'])), 0)

    def test_engineer_count_out_of_range(self) -> None:
        self.assert_invalid(b'-1\n', 'line 1: found E = -1, expected 0 to G = 2')
        self.assert_invalid(schedule(['wait 1'], ['wait 1'], ['wait 1']), 'line 1: found E = 3, expected 0 to G = 2')

    def test_task_count_out_of_range(self) -> None:
        self.assert_invalid(b'1\n0\n', 'line 2: found T = 0, expected 1 to L = 10')
        self.assert_invalid(schedule(['wait 1'] * 11), 'line 2: found T = 11, expected 1 to L = 10')

    def test_wait_out_of_range(self) -> None:
        self.assert_invalid(schedule(['wait 0']), 'line 3: found W = 0, expected 1 to L = 10')
        self.assert_invalid(schedule(['wait 11']), 'line 3: found W = 11, expected 1 to L = 10')
        self.assertEqual(self.score_output(schedule(['wait 10'])), 0)

    def test_unknown_task(self) -> None:
        self.assert_invalid(schedule(['build foo 1']), "line 3: found 'build', expected impl, move, new or wait")
        self.assert_invalid(schedule(['IMPL foo 1']), "line 3: found 'IMPL', expected impl, move, new or wait")
        self.assert_invalid(b'1\n1\n\n', 'line 3: found 0 tokens, expected a task: impl, move, new or wait')

    def test_task_with_wrong_token_count(self) -> None:
        self.assert_invalid(schedule(['impl foo']), 'line 3: found 2 tokens, expected 3 for impl')
        self.assert_invalid(schedule(['move sc 2 1']), 'line 3: found 4 tokens, expected 3 for move')
        self.assert_invalid(schedule(['new 3']), 'line 3: found 2 tokens, expected 1 for new')
        self.assert_invalid(schedule(['wait']), 'line 3: found 1 tokens, expected 2 for wait')

    def test_feature_or_service_that_does_not_exist(self) -> None:
        self.assert_invalid(schedule(['impl baz 1']), "line 3: feature 'baz' does not exist")
        self.assert_invalid(schedule(['impl sc 1']), "line 3: feature 'sc' does not exist")
        self.assert_invalid(schedule(['move foo 1']), "line 3: service 'foo' does not exist")

    def test_fewer_lines_than_expected(self) -> None:
        self.assert_invalid(b'', 'line 1: found the end of the file, expected E')
        self.assert_invalid(
            b'1\n', 'line 2: found the end of the file, expected T, the number of tasks of engineer 0'
        )
        self.assert_invalid(
            b'1\n2\nwait 1\n', 'line 4: found the end of the file, expected a task: impl, move, new or wait'
        )

    def test_more_lines_than_expected(self) -> None:
        self.assert_invalid(b'1\n1\nwait 1\nwait 1\n', "line 4: found 'wait 1', expected the end of the file")

    def test_count_line_with_more_than_one_token(self) -> None:
        self.assert_invalid(b'1 1\n', 'line 1: found 2 tokens, expected E')
        self.assert_invalid(
            b'1\n1 1\nwait 1\n', 'line 2: found 2 tokens, expected T, the number of tasks of engineer 0'
        )

    def test_any_whitespace_and_blank_lines_at_the_end(self) -> None:
        output = b' 2 \r\n2\r\n\tmove  sc 2\nimpl foo\t2 \n3\nwait 2\nimpl bar 1\r\nimpl bar 2\n\r\n \n'
        self.assertEqual(self.score_output(output), 220)

    def test_missing_newline_at_the_end(self) -> None:
        with open(EXAMPLE_OUT, 'rb') as file:
            self.assertEqual(self.score_output(file.read().rstrip(b'\n')), 220)

    def test_integers_are_parsed_strictly(self) -> None:
        for token in ['+2', '2.0', '0x2', '0_2', 'two']:
            with self.subTest(token=token):
                self.assert_invalid(schedule([f'wait {token}']), f'line 3: found {token!r}, expected an integer')
                self.assert_invalid(schedule([f'impl foo {token}']), f'line 3: found {token!r}, expected an integer')

    def test_non_ascii_byte(self) -> None:
        self.assert_invalid('1\n1\nwait ٢\n'.encode('utf-8'), 'line 3: found the byte 0xd9, expected ASCII text')

    def test_integer_with_thousands_of_digits(self) -> None:
        with self.assertRaises(judge.InvalidOutput):
            self.score_output(b'1\n1\nimpl foo ' + b'1' * 5000 + b'\n')

    def test_input_out_of_range(self) -> None:
        for header in [
            '0 2 5 3 2 5',
            '1001 2 5 3 2 5',
            '10 0 5 3 2 5',
            '10 100001 5 3 2 5',
            '10 2 5 0 2 5',
            '10 2 5 3 0 5',
            '10 2 5 3 2 0',
            '10 2 5 3 2 11',
        ]:
            with self.subTest(header=header):
                self.assert_invalid_input(EXAMPLE_INPUT.replace(b'10 2 5 3 2 5', header.encode('ascii')))
        for old, new in [
            (b'se 0', b'se 3'),
            (b'foo 3 3 100', b'foo 3 0 100'),
            (b'foo 3 3 100', b'foo 3 101 100'),
            (b'foo 3 3 100', b'foo 3 3 0'),
            (b'foo 3 3 100', b'foo 3 3 100001'),
            (b'bar 2 1 20\nsc sa', b'bar 0 1 20\n'),
        ]:
            with self.subTest(new=new):
                self.assert_invalid_input(EXAMPLE_INPUT.replace(old, new))

    def test_input_breaks_the_format(self) -> None:
        for old, new in [
            (b'sa 1', b'sa  1'),
            (b'sa 1', b'sa 1 '),
            (b'sa 1\n', b'sa 1\r\n'),
            (b'sa 1', b'sa +1'),
            (b'sa 1', b'Sa 1'),
            (b'sa 1', b'a' * 21 + b' 1'),
            (b'sc sb sd', b'sc  sb sd'),
        ]:
            with self.subTest(new=new):
                self.assert_invalid_input(EXAMPLE_INPUT.replace(old, new, 1))

    def test_input_with_a_name_twice(self) -> None:
        self.assert_invalid_input(EXAMPLE_INPUT.replace(b'sb 2', b'sa 2'))
        self.assert_invalid_input(EXAMPLE_INPUT.replace(b'bar 2', b'foo 2'))

    def test_input_with_a_binary_that_is_empty_at_first(self) -> None:
        self.assert_invalid_input(EXAMPLE_INPUT.replace(b'se 0', b'se 1'))

    def test_input_with_a_feature_that_lists_services_wrongly(self) -> None:
        self.assert_invalid_input(EXAMPLE_INPUT.replace(b'sc sb sd', b'sc sb'))
        self.assert_invalid_input(EXAMPLE_INPUT.replace(b'sc sb sd', b'sc sb sd sa'))
        self.assert_invalid_input(EXAMPLE_INPUT.replace(b'sc sb sd', b'sc sb sf'))
        self.assert_invalid_input(EXAMPLE_INPUT.replace(b'sc sb sd', b'sc sb sb'))

    def test_input_with_fewer_or_more_lines_than_expected(self) -> None:
        self.assert_invalid_input(EXAMPLE_INPUT.replace(b'10 2 5 3 2 5', b'10 2 5 3 3 5'))
        self.assert_invalid_input(EXAMPLE_INPUT + b'\nbaz 1 1 1\nsa\n')

    def test_input_with_a_newline_at_the_end(self) -> None:
        with open(EXAMPLE_OUT, 'rb') as file:
            self.assertEqual(self.score_files(EXAMPLE_INPUT + b'\n', file.read()), 220)


if __name__ == '__main__':
    unittest.main()
