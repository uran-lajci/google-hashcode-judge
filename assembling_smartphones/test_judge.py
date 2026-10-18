import os
import tempfile
import unittest

import judge

FOLDER = os.path.dirname(__file__)
EXAMPLE_IN = os.path.join(FOLDER, 'example.in')
EXAMPLE_OUT = os.path.join(FOLDER, 'example.out')


def workspace_input(
    width: int,
    height: int,
    mount_points: list[tuple[int, int]],
    tasks: list[list[tuple[int, int]]],
    steps: int,
) -> bytes:
    """Every task scores its ID plus one, and every mount point can take an arm."""
    lines = [f'{width} {height} {len(mount_points)} {len(mount_points)} {len(tasks)} {steps}']
    lines += [f'{x} {y}' for x, y in mount_points]
    for task, points in enumerate(tasks):
        lines += [f'{task + 1} {len(points)}', ' '.join(f'{x} {y}' for x, y in points)]
    return ''.join(f'{line}\n' for line in lines).encode('ascii')


# A row of four cells with an arm mounted at each end. Task 0 is the cell next to the left arm, task 1 the cell next to
# the right arm.
ROW = workspace_input(4, 1, [(0, 0), (3, 0)], [[(1, 0)], [(2, 0)]], 5)


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
            self.score_files(input_data, b'1\n1 1 1 1\n0\nU\n')

    def test_example_score_matches_statement(self) -> None:
        self.assertEqual(judge.main(EXAMPLE_IN, EXAMPLE_OUT), 11)

    def test_arm_expands_to_a_gripper_that_retracts_in_the_same_step(self) -> None:
        # In step 3 of the example, the arm mounted at [1, 1] expands to [2, 3] as the other gripper leaves it. The
        # order of the arms in the file does not matter.
        self.assertEqual(self.score_output(b'2\n1 3 1 4\n2\nR R L L\n1 1 1 5\n0\nU R W U R\n'), 11)

    def test_arm_expands_to_a_gripper_that_stays(self) -> None:
        self.assert_invalid(
            b'2\n1 1 1 5\n0\nU R W U R\n1 3 1 4\n2\nR R L W\n',
            'line 4: in step 3, the arm expands to [2, 3], which the arm mounted at [1, 3] occupies',
        )
        self.assert_invalid(
            b'2\n1 3 1 4\n2\nR R L W\n1 1 1 5\n0\nU R W U R\n',
            'line 7: in step 3, the arm expands to [2, 3], which the arm mounted at [1, 3] occupies',
        )

    def test_grippers_swap_cells(self) -> None:
        self.assertEqual(self.score_files(ROW, b'2\n0 0 1 1\n0\nR\n3 0 1 1\n1\nL\n'), 3)
        self.assert_invalid(
            b'2\n0 0 1 2\n0\nR R\n3 0 1 2\n1\nL L\n',
            'line 4: in step 1, the arm expands to [2, 0], which the arm mounted at [3, 0] occupies',
            ROW,
        )

    def test_two_arms_expand_to_the_same_cell(self) -> None:
        input_data = workspace_input(3, 1, [(0, 0), (2, 0)], [[(1, 0)], [(1, 0)]], 1)
        self.assert_invalid(
            b'2\n0 0 1 1\n0\nR\n2 0 1 1\n1\nL\n',
            'line 7: in step 0, the arm expands to [1, 0], which the arm mounted at [0, 0] occupies',
            input_data,
        )

    def test_arm_expands_to_a_cell_another_gripper_retracts_to(self) -> None:
        # In step 2 the arm mounted at [1, 1] retracts from [2, 2] to [1, 2], which stays part of it.
        self.assert_invalid(
            b'2\n1 1 1 3\n0\nU R L\n1 3 1 3\n2\nW W D\n',
            'line 7: in step 2, the arm expands to [1, 2], which the arm mounted at [1, 1] occupies',
        )

    def test_arm_expands_to_cells_freed_in_earlier_steps(self) -> None:
        # The left arm leaves [2, 0] in step 2 and [1, 0] in step 3, one step before the right arm takes each.
        self.assertEqual(self.score_files(ROW, b'2\n0 0 1 4\n1\nR R L L\n3 0 1 5\n0\nW W W L L\n'), 2 + 1)

    def test_arm_expands_to_a_mount_point_without_an_arm(self) -> None:
        self.assert_invalid(
            b'1\n1 1 1 3\n0\nR R U\n', 'line 4: in step 2, the arm expands to [3, 2], which is a mount point'
        )

    def test_arm_expands_to_its_own_mount_point(self) -> None:
        # The gripper comes back to [1, 1] from [1, 2], which is not the cell it came from.
        self.assert_invalid(
            b'1\n1 1 1 4\n0\nR U L D\n', 'line 4: in step 3, the arm expands to [1, 1], which is a mount point'
        )

    def test_arm_expands_to_its_own_body(self) -> None:
        self.assert_invalid(
            b'1\n1 1 1 5\n1\nR R D L U\n', 'line 4: in step 4, the arm expands to [2, 1], which the arm itself occupies'
        )

    def test_arm_expands_outside_the_workspace(self) -> None:
        message = 'line 4: in step {}, the arm expands to {}, outside the workspace of 5 x 4 cells'
        self.assert_invalid(b'1\n1 1 1 2\n1\nD D\n', message.format(1, '[1, -1]'))
        self.assert_invalid(b'1\n1 3 1 1\n2\nU\n', message.format(0, '[1, 4]'))

    def test_arm_does_not_complete_its_task(self) -> None:
        self.assert_invalid(
            b'1\n1 1 1 3\n0\nU R U\n', 'line 3: the arm does not complete task 0, it visits 1 of its 2 assembly points'
        )

    def test_arm_completes_its_tasks_in_the_given_order(self) -> None:
        self.assertEqual(self.score_output(b'1\n1 3 2 2\n0 2\nR R\n'), 11)
        self.assert_invalid(
            b'1\n1 3 2 2\n2 0\nR R\n', 'line 3: the arm does not complete task 0, it visits 0 of its 2 assembly points'
        )

    def test_assembly_point_visited_for_another_task_does_not_count(self) -> None:
        # The first example of the statement: the arm passes [0, 1] while it works on task 0, so it comes back for
        # task 1.
        input_data = workspace_input(3, 3, [(2, 0)], [[(0, 0), (0, 2)], [(0, 1)]], 5)
        self.assert_invalid(
            b'1\n2 0 2 4\n0 1\nL L U U\n',
            'line 3: the arm does not complete task 1, it visits 0 of its 1 assembly points',
            input_data,
        )
        self.assertEqual(self.score_files(input_data, b'1\n2 0 2 5\n0 1\nL L U U D\n'), 1 + 2)

    def test_several_tasks_finish_in_the_same_step(self) -> None:
        # The second example of the statement: task 0 finishes at [0, 1] in step 1, and so do tasks 1 and 2, which
        # need only that cell. Task 3 starts there too and finishes in step 2.
        input_data = workspace_input(2, 3, [(1, 0)], [[(0, 0), (0, 1)], [(0, 1)], [(0, 1)], [(0, 1), (0, 2)]], 3)
        self.assertEqual(self.score_files(input_data, b'1\n1 0 4 3\n0 1 2 3\nL U U\n'), 1 + 2 + 3 + 4)

    def test_assembly_point_twice_in_a_row_takes_no_extra_step(self) -> None:
        input_data = workspace_input(2, 1, [(0, 0)], [[(1, 0), (1, 0)]], 1)
        self.assertEqual(self.score_files(input_data, b'1\n0 0 1 1\n0\nR\n'), 1)

    def test_retracted_gripper_visits_assembly_points(self) -> None:
        input_data = workspace_input(3, 1, [(0, 0)], [[(2, 0), (1, 0)]], 3)
        self.assertEqual(self.score_files(input_data, b'1\n0 0 1 3\n0\nR R L\n'), 1)

    def test_arm_may_end_anywhere(self) -> None:
        self.assertEqual(self.score_output(b'1\n1 1 1 5\n0\nU R U R W\n'), 10)

    def test_task_assigned_twice(self) -> None:
        self.assert_invalid(
            b'2\n1 1 1 1\n0\nU\n1 3 1 1\n0\nR\n', 'line 6: task 0 is assigned a second time, first assigned on line 3'
        )
        self.assert_invalid(
            b'1\n1 3 2 2\n2 2\nR R\n', 'line 3: task 2 is assigned a second time, first assigned on line 3'
        )

    def test_task_that_does_not_exist(self) -> None:
        message = 'line 3: task {} does not exist, expected an ID from 0 to 2'
        self.assert_invalid(b'1\n1 1 1 1\n3\nU\n', message.format(3))
        self.assert_invalid(b'1\n1 1 1 1\n-1\nU\n', message.format(-1))

    def test_arm_not_at_a_mount_point(self) -> None:
        self.assert_invalid(b'1\n2 2 1 1\n0\nU\n', 'line 2: cell [2, 2] is not a mount point')
        self.assert_invalid(b'1\n-1 1 1 1\n0\nU\n', 'line 2: cell [-1, 1] is not a mount point')

    def test_two_arms_at_the_same_mount_point(self) -> None:
        self.assert_invalid(
            b'2\n1 1 1 1\n0\nU\n1 1 1 1\n1\nU\n',
            'line 5: mount point [1, 1] is used a second time, first used on line 2',
        )

    def test_arm_count_out_of_range(self) -> None:
        self.assert_invalid(b'0\n', 'line 1: found A = 0, expected 1 to R = 2')
        self.assert_invalid(b'3\n', 'line 1: found A = 3, expected 1 to R = 2')

    def test_task_count_out_of_range(self) -> None:
        self.assert_invalid(b'1\n1 1 0 1\n\nU\n', 'line 2: found Z = 0, expected 1 to T = 3')
        self.assert_invalid(b'1\n1 1 4 1\n0 1 2 0\nU\n', 'line 2: found Z = 4, expected 1 to T = 3')

    def test_instruction_count_out_of_range(self) -> None:
        self.assert_invalid(b'1\n1 1 1 0\n0\n\n', 'line 2: found K = 0, expected 1 to L = 5')
        self.assert_invalid(b'1\n1 1 1 6\n0\nU R W U R W\n', 'line 2: found K = 6, expected 1 to L = 5')

    def test_counts_that_differ_from_the_lines_after_them(self) -> None:
        self.assert_invalid(b'1\n1 1 2 1\n0\nU\n', 'line 3: found 1 tokens, expected Z = 2 task IDs')
        self.assert_invalid(b'1\n1 1 1 1\n0 1\nU\n', 'line 3: found 2 tokens, expected Z = 1 task IDs')
        self.assert_invalid(b'1\n1 1 1 2\n0\nU\n', 'line 4: found 1 tokens, expected K = 2 instructions')
        self.assert_invalid(b'1\n1 1 1 1\n0\nU R\n', 'line 4: found 2 tokens, expected K = 1 instructions')

    def test_instruction_that_does_not_exist(self) -> None:
        for instruction in ['X', 'u', 'UR', '0', 'RIGHT']:
            with self.subTest(instruction=instruction):
                self.assert_invalid(
                    f'1\n1 1 1 1\n0\n{instruction}\n'.encode('ascii'),
                    f'line 4: found {instruction!r}, expected an instruction R, L, U, D or W',
                )

    def test_line_with_wrong_token_count(self) -> None:
        self.assert_invalid(b'1 2\n', 'line 1: found 2 tokens, expected A')
        self.assert_invalid(b'1\n1 1 1\n0\nU\n', 'line 2: found 3 tokens, expected x, y, Z and K')
        self.assert_invalid(b'1\n1 1 1 1 1\n0\nU\n', 'line 2: found 5 tokens, expected x, y, Z and K')

    def test_blank_line_inside_the_file(self) -> None:
        self.assert_invalid(b'1\n\n1 1 1 1\n0\nU\n', 'line 2: found 0 tokens, expected x, y, Z and K')

    def test_fewer_lines_than_expected(self) -> None:
        self.assert_invalid(b'2\n1 1 1 5\n0\nU R W U R\n', 'line 5: found the end of the file, expected x, y, Z and K')
        self.assert_invalid(b'1\n1 1 1 1\n', 'line 3: found the end of the file, expected Z = 1 task IDs')
        self.assert_invalid(b'1\n1 1 1 1\n0\n', 'line 4: found the end of the file, expected K = 1 instructions')

    def test_more_lines_than_expected(self) -> None:
        with open(EXAMPLE_OUT, 'rb') as file:
            self.assert_invalid(file.read() + b'W\n', "line 8: found 'W', expected the end of the file")

    def test_any_whitespace_and_blank_lines_at_the_end(self) -> None:
        output = b' 2 \r\n1  1\t1 5\r\n0 \nU R W U R \n1 3 1 4\n\t2\nR  R L L\r\n\r\n \n'
        self.assertEqual(self.score_output(output), 11)

    def test_missing_newline_at_the_end(self) -> None:
        with open(EXAMPLE_OUT, 'rb') as file:
            self.assertEqual(self.score_output(file.read().rstrip(b'\n')), 11)

    def test_empty_file(self) -> None:
        self.assert_invalid(b'', 'line 1: found the end of the file, expected A')

    def test_integers_are_parsed_strictly(self) -> None:
        for token in ['+0', '0.0', '0x0', '0_0', 'zero']:
            with self.subTest(token=token):
                self.assert_invalid(
                    f'1\n1 1 1 1\n{token}\nU\n'.encode('ascii'), f'line 3: found {token!r}, expected an integer'
                )

    def test_non_ascii_byte(self) -> None:
        self.assert_invalid('1\n1 1 1 1\n٠\nU\n'.encode('utf-8'), 'line 3: found the byte 0xd9, expected ASCII text')

    def test_integer_with_thousands_of_digits(self) -> None:
        with self.assertRaises(judge.InvalidOutput):
            self.score_output(b'1\n1 1 1 1\n' + b'1' * 5000 + b'\nU\n')

    def test_input_without_a_newline_at_the_end(self) -> None:
        with open(EXAMPLE_IN, 'rb') as file:
            self.assertEqual(self.score_files(file.read().rstrip(b'\n'), b'1\n1 3 1 2\n2\nR R\n'), 1)

    def test_input_out_of_range(self) -> None:
        with open(EXAMPLE_IN, 'rb') as file:
            valid = file.read()
        for header in [
            '0 4 2 3 3 5',
            '1001 4 2 3 3 5',
            '5 0 2 3 3 5',
            '5 1001 2 3 3 5',
            '5 4 0 3 3 5',
            '5 4 101 3 3 5',
            '5 4 4 3 3 5',
            '5 4 2 3 0 5',
            '5 4 2 3 1001 5',
            '5 4 2 3 3 0',
            '5 4 2 3 3 10001',
        ]:
            with self.subTest(header=header):
                self.assert_invalid_input(valid.replace(b'5 4 2 3 3 5', header.encode('ascii')))
        for old, new in [
            (b'\n1 3\n', b'\n5 3\n'),
            (b'\n1 3\n', b'\n1 4\n'),
            (b'10 2\n', b'0 2\n'),
            (b'10 2\n', b'1000001 2\n'),
            (b'5 1\n4 0', b'5 0\n'),
            (b'5 1\n4 0', b'5 1\n5 0'),
            (b'5 1\n4 0', b'5 1\n4 4'),
        ]:
            with self.subTest(new=new):
                self.assert_invalid_input(valid.replace(old, new))

    def test_input_breaks_the_format(self) -> None:
        with open(EXAMPLE_IN, 'rb') as file:
            valid = file.read()
        for old, new in [
            (b'\n1 3\n', b'\n1  3\n'),
            (b'\n1 3\n', b'\n1 3 \n'),
            (b'\n1 3\n', b'\n1 3\r\n'),
            (b'\n1 3\n', b'\n+1 3\n'),
            (b'\n1 3\n', b'\n1\n'),
            (b'5 1\n4 0', b'5 1\n4 0 0'),
            (b'5 1\n4 0', b'5 2\n4 0'),
        ]:
            with self.subTest(new=new):
                self.assert_invalid_input(valid.replace(old, new, 1))

    def test_input_with_two_mount_points_in_one_cell(self) -> None:
        with open(EXAMPLE_IN, 'rb') as file:
            self.assert_invalid_input(file.read().replace(b'\n1 3\n', b'\n1 1\n'))

    def test_input_with_an_assembly_point_at_a_mount_point(self) -> None:
        with open(EXAMPLE_IN, 'rb') as file:
            self.assert_invalid_input(file.read().replace(b'5 1\n4 0', b'5 1\n3 2'))

    def test_input_with_fewer_tasks_than_t(self) -> None:
        with open(EXAMPLE_IN, 'rb') as file:
            self.assert_invalid_input(file.read().replace(b'5 4 2 3 3 5', b'5 4 2 3 4 5'))

    def test_input_with_more_lines_than_expected(self) -> None:
        with open(EXAMPLE_IN, 'rb') as file:
            self.assert_invalid_input(file.read() + b'1 1\n')
