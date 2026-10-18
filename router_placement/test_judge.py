import os
import tempfile
import unittest

import judge

FOLDER = os.path.dirname(__file__)
EXAMPLE_IN = os.path.join(FOLDER, 'example.in')
EXAMPLE_OUT = os.path.join(FOLDER, 'example.out')

# The building from the statement's example of the cells a router in S = [3, 7] covers with R = 3.
COVERAGE_GRID = [
    '.#..............',
    '.#......#.......',
    '.####...#.......',
    '....#...........',
    '....#...........',
    '....#...#.......',
    '....#...#.......',
]
# The building from the statement's backbone example, with b = [1, 1] and r = [0, 5] unmarked.
BACKBONE_GRID = ['--#....#', '--#....#', '--#....#']


def building_input(
    radius: int,
    prices: tuple[int, int],
    budget: int,
    initial: tuple[int, int],
    grid: list[str],
) -> bytes:
    lines = [f'{len(grid)} {len(grid[0])} {radius}', f'{prices[0]} {prices[1]} {budget}', f'{initial[0]} {initial[1]}']
    return ''.join(line + '\n' for line in lines + grid).encode('ascii')


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
        self.assertEqual(judge.main(EXAMPLE_IN, EXAMPLE_OUT), 35017)

    def test_coverage_matches_statement_figure(self) -> None:
        # Columns 5 to 7 of rows 0, 1, 2, 5 and 6, and columns 5 to 10 of rows 3 and 4: 27 target cells.
        input_data = building_input(3, (1, 5), 100, (3, 7), COVERAGE_GRID)
        self.assertEqual(self.score_files(input_data, b'0\n1\n3 7\n'), 27 * 1000 + 100 - 5)

    def test_backbone_through_a_wall_matches_statement_figure(self) -> None:
        # The cost 1 * Pr + 4 * Pb equals B, which is allowed. The router covers the 6 target cells around it.
        input_data = building_input(1, (1, 5), 9, (1, 1), BACKBONE_GRID)
        self.assertEqual(self.score_files(input_data, b'4\n1 2\n1 3\n1 4\n0 5\n1\n0 5\n'), 6 * 1000)

    def test_wall_on_the_edge_of_the_rectangle_blocks_the_signal(self) -> None:
        # From the initial cell [2, 7], the wall at [2, 8] blocks every cell to the right in rows 3 to 5, and the wall
        # at [1, 7] blocks the rows above. That leaves rows 2 to 5, columns 4 to 7.
        self.assertEqual(self.score_output(b'0\n1\n2 7\n'), 16 * 1000 + 220 - 100)

    def test_void_cells_hold_routers_but_are_not_counted(self) -> None:
        input_data = building_input(1, (1, 5), 20, (0, 0), ['-.-'])
        self.assertEqual(self.score_files(input_data, b'1\n0 1\n2\n0 0\n0 1\n'), 1000 + 20 - 1 - 10)

    def test_no_backbone_and_no_routers_scores_the_budget(self) -> None:
        self.assertEqual(self.score_output(b'0\n0\n'), 220)

    def test_backbone_connects_diagonally(self) -> None:
        self.assertEqual(self.score_output(b'2\n3 8\n4 9\n0\n'), 218)

    def test_router_on_initial_wall_cell(self) -> None:
        input_data = building_input(1, (1, 5), 10, (0, 0), ['#.'])
        with self.assertRaises(judge.InvalidOutput) as context:
            self.score_files(input_data, b'0\n1\n0 0\n')
        self.assertEqual(str(context.exception), 'line 3: cell [0, 0] is a wall, so it cannot hold a router')

    def test_backbone_cell_without_a_connected_neighbour(self) -> None:
        message = (
            'line 2: cell [{}] has none of its 8 neighbours connected to the backbone, expected a neighbour of the '
            'initial cell or of a cell listed above'
        )
        self.assert_invalid(b'1\n4 7\n0\n', message.format('4, 7'))
        # [3, 9] neighbours [3, 8], but only once [3, 8] is listed before it.
        self.assert_invalid(b'2\n3 9\n3 8\n0\n', message.format('3, 9'))

    def test_initial_backbone_cell_listed(self) -> None:
        self.assert_invalid(
            b'1\n2 7\n0\n',
            'line 2: cell [2, 7] is the initial backbone cell, which must not be listed',
        )

    def test_backbone_cell_listed_twice(self) -> None:
        self.assert_invalid(
            b'2\n3 6\n3 6\n0\n',
            'line 3: cell [3, 6] is connected a second time, first connected on line 2',
        )

    def test_router_off_the_backbone(self) -> None:
        self.assert_invalid(
            b'0\n1\n3 6\n',
            'line 3: cell [3, 6] is not connected to the backbone, so it cannot hold a router',
        )

    def test_router_on_a_wall(self) -> None:
        self.assert_invalid(b'1\n1 7\n1\n1 7\n', 'line 4: cell [1, 7] is a wall, so it cannot hold a router')

    def test_router_placed_twice(self) -> None:
        self.assert_invalid(
            b'1\n3 6\n2\n3 6\n3 6\n',
            'line 5: a router is placed in cell [3, 6] a second time, first placed on line 4',
        )

    def test_budget_exceeded(self) -> None:
        self.assert_invalid(
            b'3\n3 6\n3 8\n3 9\n3\n3 6\n3 8\n3 9\n',
            'line 5: N * Pb + M * Pr = 3 * 1 + 3 * 100 = 303, expected at most the budget B = 220',
        )
        self.assert_invalid(
            b'21\n' + b''.join(f'3 {column}\n'.encode('ascii') for column in range(8, 0, -1))
            + b''.join(f'4 {column}\n'.encode('ascii') for column in range(1, 14)) + b'2\n3 6\n3 8\n',
            'line 23: N * Pb + M * Pr = 21 * 1 + 2 * 100 = 221, expected at most the budget B = 220',
        )

    def test_backbone_count_out_of_range(self) -> None:
        self.assert_invalid(b'-1\n0\n', 'line 1: found N = -1, expected 0 to W * H - 1 = 175')
        self.assert_invalid(b'176\n0\n', 'line 1: found N = 176, expected 0 to W * H - 1 = 175')

    def test_router_count_out_of_range(self) -> None:
        self.assert_invalid(b'0\n-1\n', 'line 2: found M = -1, expected 0 to W * H = 176')
        self.assert_invalid(b'0\n177\n', 'line 2: found M = 177, expected 0 to W * H = 176')

    def test_cell_out_of_range(self) -> None:
        self.assert_invalid(b'1\n8 7\n0\n', 'line 2: found r = 8, expected 0 to H - 1 = 7')
        self.assert_invalid(b'1\n-1 7\n0\n', 'line 2: found r = -1, expected 0 to H - 1 = 7')
        self.assert_invalid(b'0\n1\n2 22\n', 'line 3: found c = 22, expected 0 to W - 1 = 21')
        self.assert_invalid(b'0\n1\n2 -1\n', 'line 3: found c = -1, expected 0 to W - 1 = 21')

    def test_line_with_wrong_token_count(self) -> None:
        self.assert_invalid(b'1 0\n', "line 1: found '1 0', expected N, the number of cells connected to the backbone")
        self.assert_invalid(b'1\n3\n0\n', "line 2: found '3', expected r and c of a cell connected to the backbone")
        self.assert_invalid(
            b'1\n3 6 1\n0\n',
            "line 2: found '3 6 1', expected r and c of a cell connected to the backbone",
        )
        self.assert_invalid(b'0\n1\n\n', "line 3: found '', expected r and c of a router")

    def test_token_that_is_not_a_plain_integer(self) -> None:
        self.assert_invalid(b'1\n+3 6\n0\n', "line 2: found '+3', expected an integer")
        self.assert_invalid(b'0.0\n0\n', "line 1: found '0.0', expected an integer")

    def test_fewer_lines_than_expected(self) -> None:
        self.assert_invalid(
            b'',
            'line 1: found the end of the file, expected N, the number of cells connected to the backbone',
        )
        self.assert_invalid(b'1\n3 6\n', 'line 3: found the end of the file, expected M, the number of routers')
        self.assert_invalid(b'0\n1\n', 'line 3: found the end of the file, expected r and c of a router')

    def test_content_after_the_last_router(self) -> None:
        with open(EXAMPLE_OUT, 'rb') as file:
            example = file.read()
        self.assert_invalid(example + b'3 7\n', "line 8: found '3 7', expected the end of the file")
        self.assertEqual(self.score_output(example + b'\n\n'), 35017)

    def test_output_that_is_not_ascii(self) -> None:
        self.assert_invalid(b'0\n0\n\xc3\xa9\n', 'line 3: found the byte 0xc3, expected ASCII text')

    def test_grid_row_of_the_wrong_width_is_a_bad_input(self) -> None:
        with self.assertRaises(judge.InvalidInput):
            self.score_files(building_input(1, (1, 5), 10, (0, 0), ['..', '.']), b'0\n0\n')


if __name__ == '__main__':
    unittest.main()
