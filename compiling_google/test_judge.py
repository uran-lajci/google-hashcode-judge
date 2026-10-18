import os
import tempfile
import unittest

import judge

FOLDER = os.path.dirname(__file__)
EXAMPLE_IN = os.path.join(FOLDER, 'example.in')
EXAMPLE_OUT = os.path.join(FOLDER, 'example.out')


def build_input(server_count: int, files: list[str], targets: list[str]) -> bytes:
    """Turn 'b 3 1: a' into the lines of compiled file b, which takes 3s to compile, 1s to replicate and needs a."""
    lines = [f'{len(files)} {len(targets)} {server_count}']
    for spec in files:
        head, dependencies = spec.split(':')
        lines += [head, ' '.join([str(len(dependencies.split()))] + dependencies.split())]
    return '\n'.join(lines + targets).encode('ascii') + b'\n'


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

    def assert_invalid(self, output: bytes, message: str, input_data: bytes | None = None) -> None:
        with self.assertRaises(judge.InvalidOutput) as context:
            if input_data is None:
                self.score_output(output)
            else:
                self.score_files(input_data, output)
        self.assertEqual(str(context.exception), message)

    def assert_invalid_input(self, input_data: bytes) -> None:
        with self.assertRaises(judge.InvalidInput):
            self.score_files(input_data, b'1\nc0 0\n')

    def test_example_score_matches_statement(self) -> None:
        self.assertEqual(judge.main(EXAMPLE_IN, EXAMPLE_OUT), 60)

    def test_target_compiled_at_the_deadline_earns_its_goal_points(self) -> None:
        # c3 is ready at second 23, with deadline 40 and 8 goal points.
        self.assertEqual(self.score_output(b'2\nc1 0\nc3 0\n'), 40 - 23 + 8)
        input_data = build_input(1, ['a 5 1:'], ['a 5 7'])
        self.assertEqual(self.score_files(input_data, b'1\na 0\n'), 7)

    def test_target_compiled_after_the_deadline_scores_zero(self) -> None:
        input_data = build_input(1, ['a 5 1:'], ['a 4 7'])
        self.assertEqual(self.score_files(input_data, b'1\na 0\n'), 0)

    def test_target_never_compiled_scores_zero(self) -> None:
        self.assertEqual(self.score_output(b'1\nc0 0\n'), 0)

    def test_dependency_from_another_server_waits_for_replication(self) -> None:
        # a is ready on server 0 at second 2 and on server 1 at second 2 + 10. b then ends at second 13.
        input_data = build_input(2, ['a 2 10:', 'b 1 1: a'], ['b 100 1'])
        self.assertEqual(self.score_files(input_data, b'2\na 0\nb 1\n'), 100 - 13 + 1)
        self.assertEqual(self.score_files(input_data, b'2\na 0\nb 0\n'), 100 - 3 + 1)

    def test_server_waits_for_its_previous_steps(self) -> None:
        # a is ready at second 1, but server 1 is busy with c until second 50.
        input_data = build_input(2, ['a 1 1:', 'b 1 1: a', 'c 50 1:'], ['b 100 1'])
        self.assertEqual(self.score_files(input_data, b'3\na 0\nc 1\nb 1\n'), 100 - 51 + 1)

    def test_only_direct_dependencies_are_waited_for(self) -> None:
        # c needs b, which needs a. Server 1 never needs a, so it does not wait 1000s for its copy.
        input_data = build_input(2, ['a 1 1000:', 'b 1 1: a', 'c 1 1: b'], ['c 100 1'])
        self.assertEqual(self.score_files(input_data, b'3\na 0\nb 0\nc 1\n'), 100 - 4 + 1)

    def test_dependency_uses_the_earliest_copy_on_earlier_lines(self) -> None:
        # Server 0 has a at second 31 and server 1 at second 1. Server 2 gets the copy from server 1 at second 6.
        input_data = build_input(3, ['x 30 1:', 'a 1 5:', 'b 1 1: a'], ['b 100 1'])
        self.assertEqual(self.score_files(input_data, b'4\nx 0\na 0\na 1\nb 2\n'), 100 - 7 + 1)

    def test_copy_on_a_later_line_is_ignored_even_when_it_finishes_sooner(self) -> None:
        # The copy of a on line 5 is ready at second 1, but b on line 4 only sees the one on line 3, ready at 31 + 5.
        input_data = build_input(3, ['x 30 1:', 'a 1 5:', 'b 1 1: a'], ['b 100 1'])
        self.assertEqual(self.score_files(input_data, b'4\nx 0\na 0\nb 2\na 1\n'), 100 - 37 + 1)

    def test_target_counts_its_earliest_copy_on_any_line(self) -> None:
        input_data = build_input(2, ['x 30 1:', 'a 1 5:'], ['a 100 1'])
        self.assertEqual(self.score_files(input_data, b'3\nx 0\na 0\na 1\n'), 100 - 1 + 1)
        self.assertEqual(self.score_files(input_data, b'3\nx 0\na 1\na 0\n'), 100 - 1 + 1)

    def test_dependency_keeps_its_earliest_copy_when_a_later_line_finishes_later(self) -> None:
        # The copy of a on server 1 is ready at second 1 and reaches server 2 at second 6. The one on server 0 is late.
        input_data = build_input(3, ['x 30 1:', 'a 1 5:', 'b 1 1: a'], ['b 100 1'])
        self.assertEqual(self.score_files(input_data, b'4\na 1\nx 0\na 0\nb 2\n'), 100 - 7 + 1)

    def test_same_step_listed_twice_keeps_the_server_busy(self) -> None:
        # A second server raises C * S to 4, enough for three steps.
        input_data = build_input(2, ['a 10 1:', 'b 1 1:'], ['b 100 1'])
        self.assertEqual(self.score_files(input_data, b'3\na 0\na 0\nb 0\n'), 100 - 21 + 1)

    def test_dependency_listed_twice_is_waited_for_once(self) -> None:
        # f_big.in lists a dependency twice in 3,104 files.
        input_data = build_input(2, ['a 2 10:', 'b 1 1: a a'], ['b 100 1'])
        self.assertEqual(self.score_files(input_data, b'2\na 0\nb 1\n'), 100 - 13 + 1)

    def test_dependency_not_compiled_on_an_earlier_line(self) -> None:
        self.assert_invalid(b'1\nc2 0\n', 'line 2: c2 depends on c0, but no earlier line compiles c0')
        self.assert_invalid(b'2\nc2 0\nc0 0\n', 'line 2: c2 depends on c0, but no earlier line compiles c0')
        self.assert_invalid(
            b'4\nc0 0\nc2 0\nc4 0\nc1 1\n', 'line 4: c4 depends on c1, but no earlier line compiles c1'
        )

    def test_step_count_out_of_range(self) -> None:
        self.assert_invalid(b'0\n', 'line 1: found E = 0, expected 1 to C * S = 12')
        self.assert_invalid(b'-1\n', 'line 1: found E = -1, expected 1 to C * S = 12')
        self.assert_invalid(b'13\n', 'line 1: found E = 13, expected 1 to C * S = 12')

    def test_step_count_of_c_times_s(self) -> None:
        output = b'12\n' + b'c0 0\nc0 1\nc1 0\nc1 1\nc2 0\nc2 1\nc3 0\nc3 1\nc4 0\nc4 1\nc5 0\nc5 1\n'
        self.assertEqual(self.score_output(output), 0)

    def test_step_count_line_with_more_than_one_token(self) -> None:
        self.assert_invalid(b'1 c0 0\n', 'line 1: found 3 tokens, expected E')

    def test_file_that_does_not_exist(self) -> None:
        self.assert_invalid(b'1\nc6 0\n', "line 2: compiled file 'c6' does not exist")
        self.assert_invalid(b'1\nC0 0\n', "line 2: compiled file 'C0' does not exist")

    def test_server_out_of_range(self) -> None:
        self.assert_invalid(b'1\nc0 -1\n', 'line 2: found s = -1, expected 0 to S - 1 = 1')
        self.assert_invalid(b'1\nc0 2\n', 'line 2: found s = 2, expected 0 to S - 1 = 1')

    def test_step_line_with_the_wrong_number_of_tokens(self) -> None:
        expected = 'expected the name of a compiled file and a server'
        self.assert_invalid(b'1\nc0\n', f'line 2: found 1 tokens, {expected}')
        self.assert_invalid(b'1\nc0 0 1\n', f'line 2: found 3 tokens, {expected}')
        self.assert_invalid(b'2\n\nc0 0\n', f'line 2: found 0 tokens, {expected}')

    def test_fewer_lines_than_expected(self) -> None:
        self.assert_invalid(
            b'2\nc0 0\n', 'line 3: found the end of the file, expected the name of a compiled file and a server'
        )

    def test_more_lines_than_expected(self) -> None:
        self.assert_invalid(b'1\nc0 0\nc1 1\n', "line 3: found 'c1 1', expected the end of the file")

    def test_any_whitespace_and_blank_lines_at_the_end(self) -> None:
        output = b' 7 \r\nc1\t1\r\nc0  0\nc3 1 \nc2 0\nc2 1\nc4 0\nc5 1\r\n\r\n \n'
        self.assertEqual(self.score_output(output), 60)

    def test_missing_newline_at_the_end(self) -> None:
        with open(EXAMPLE_OUT, 'rb') as file:
            self.assertEqual(self.score_output(file.read().rstrip(b'\n')), 60)

    def test_empty_file(self) -> None:
        self.assert_invalid(b'', 'line 1: found the end of the file, expected E')

    def test_integers_are_parsed_strictly(self) -> None:
        for token in ['+1', '1.0', '0x1', '0_1', 'one']:
            with self.subTest(token=token):
                self.assert_invalid(
                    f'{token}\nc0 0\n'.encode('ascii'), f'line 1: found {token!r}, expected an integer'
                )
                self.assert_invalid(
                    f'1\nc0 {token}\n'.encode('ascii'), f'line 2: found {token!r}, expected an integer'
                )

    def test_non_ascii_byte(self) -> None:
        self.assert_invalid('1\nc0 0\nc1 ٠\n'.encode('utf-8'), 'line 3: found the byte 0xd9, expected ASCII text')

    def test_integer_with_thousands_of_digits(self) -> None:
        with self.assertRaises(judge.InvalidOutput):
            self.score_output(b'1' * 5000 + b'\n')
        with self.assertRaises(judge.InvalidOutput):
            self.score_output(b'1\nc0 ' + b'1' * 5000 + b'\n')

    def test_input_without_a_newline_at_the_end(self) -> None:
        with open(EXAMPLE_IN, 'rb') as file:
            input_data = file.read().rstrip(b'\n')
        with open(EXAMPLE_OUT, 'rb') as file:
            self.assertEqual(self.score_files(input_data, file.read()), 60)

    def test_input_out_of_range(self) -> None:
        valid = ['1 1 1', 'c0 1 1', '0', 'c0 1 1']
        for index, line in [
            (0, '0 1 1'),
            (0, '100001 1 1'),
            (0, '1 0 1'),
            (0, '1 2 1'),
            (0, '1 1 0'),
            (0, '1 1 101'),
            (1, 'c0 0 1'),
            (1, 'c0 1000001 1'),
            (1, 'c0 1 0'),
            (1, 'c0 1 1000001'),
            (3, 'c0 0 1'),
            (3, 'c0 1000001 1'),
            (3, 'c0 1 0'),
            (3, 'c0 1 1000001'),
        ]:
            with self.subTest(line=line):
                lines = valid.copy()
                lines[index] = line
                self.assert_invalid_input('\n'.join(lines).encode('ascii') + b'\n')

    def test_input_with_more_than_100_dependencies(self) -> None:
        files = [f'a{index} 1 1:' for index in range(101)]
        names = ' '.join(f'a{index}' for index in range(101))
        self.score_files(build_input(1, files[:100] + [f'b 1 1: {names[:-5]}'], ['b 1 1']), b'1\na0 0\n')
        self.assert_invalid_input(build_input(1, files + [f'b 1 1: {names}'], ['b 1 1']))

    def test_input_breaks_the_format(self) -> None:
        with open(EXAMPLE_IN, 'rb') as file:
            valid = file.read()
        for old, new in [
            (b'6 3 2', b'6  3 2'),
            (b'c0 15 5', b'c0 15 5 '),
            (b'c0 15 5\n', b'c0 15 5\r\n'),
            (b'c0 15 5', b'c0 +15 5'),
            (b'1 c0', b'1  c0'),
            (b'1 c0', b'1 c0 '),
            (b'c3 40 8', b'c3 40'),
        ]:
            with self.subTest(new=new):
                self.assert_invalid_input(valid.replace(old, new, 1))

    def test_input_with_a_bad_name(self) -> None:
        self.score_files(build_input(1, ['Abcde12345 1 1:'], ['Abcde12345 1 1']), b'1\nAbcde12345 0\n')
        for name in ['Abcde123456', 'c-0', 'c_0']:
            with self.subTest(name=name):
                self.assert_invalid_input(build_input(1, [f'{name} 1 1:'], [f'{name} 1 1']))

    def test_input_with_a_file_described_twice(self) -> None:
        self.assert_invalid_input(build_input(1, ['a 1 1:', 'a 1 1:'], ['a 1 1']))

    def test_input_with_a_dependency_not_described_earlier(self) -> None:
        self.assert_invalid_input(build_input(1, ['a 1 1: b', 'b 1 1:'], ['a 1 1']))
        self.assert_invalid_input(build_input(1, ['a 1 1: a'], ['a 1 1']))

    def test_input_with_the_wrong_number_of_dependencies(self) -> None:
        input_data = build_input(1, ['a 1 1:', 'b 1 1: a'], ['b 1 1'])
        self.assert_invalid_input(input_data.replace(b'1 a\n', b'2 a\n'))
        self.assert_invalid_input(input_data.replace(b'1 a\n', b'0 a\n'))

    def test_input_with_a_bad_target(self) -> None:
        self.assert_invalid_input(build_input(1, ['a 1 1:'], ['b 1 1']))
        self.assert_invalid_input(build_input(1, ['a 1 1:', 'b 1 1:'], ['a 1 1', 'a 2 2']))

    def test_input_with_fewer_targets_than_announced(self) -> None:
        self.assert_invalid_input(build_input(1, ['a 1 1:', 'b 1 1:'], ['a 1 1']).replace(b'2 1 1', b'2 2 1', 1))

    def test_input_with_more_lines_than_expected(self) -> None:
        self.assert_invalid_input(build_input(1, ['a 1 1:', 'b 1 1:'], ['a 1 1', 'b 1 1']).replace(b'2 2', b'2 1', 1))
