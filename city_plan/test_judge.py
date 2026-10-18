import os
import tempfile
import unittest

import judge

FOLDER = os.path.dirname(__file__)
EXAMPLE_IN = os.path.join(FOLDER, 'example.in')
EXAMPLE_OUT = os.path.join(FOLDER, 'example.out')


def city_input(height: int, width: int, distance: int, projects: list[str]) -> bytes:
    """Turn 'R 25: .#/##/.#' into the lines of a residential project of capacity 25 with that plan."""
    lines = [f'{height} {width} {distance} {len(projects)}']
    for spec in projects:
        head, plan = spec.split(': ')
        kind, value = head.split(' ')
        rows = plan.split('/')
        lines += [f'{kind} {len(rows)} {len(rows[0])} {value}'] + rows
    return ('\n'.join(lines) + '\n').encode('ascii')


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
            self.score_files(input_data, b'0\n')

    def test_example_score_matches_statement(self) -> None:
        self.assertEqual(judge.main(EXAMPLE_IN, EXAMPLE_OUT), 75)

    def test_no_building_scores_zero(self) -> None:
        self.assertEqual(self.score_output(b'0\n'), 0)

    def test_example_without_its_second_residential_building(self) -> None:
        self.assertEqual(self.score_output(b'3\n0 0 0\n1 3 0\n2 0 2\n'), 50)

    def test_walking_distance_is_inclusive(self) -> None:
        input_data = city_input(1, 7, 2, ['R 10: #', 'U 3: #'])
        self.assertEqual(self.score_files(input_data, b'2\n0 0 0\n1 0 2\n'), 10)
        self.assertEqual(self.score_files(input_data, b'2\n0 0 0\n1 0 3\n'), 0)

    def test_distance_is_manhattan(self) -> None:
        # The diagonal neighbor is at distance 2.
        self.assertEqual(self.score_files(city_input(2, 2, 1, ['R 10: #', 'U 3: #']), b'2\n0 0 0\n1 1 1\n'), 0)
        self.assertEqual(self.score_files(city_input(2, 2, 2, ['R 10: #', 'U 3: #']), b'2\n0 0 0\n1 1 1\n'), 10)

    def test_distance_between_the_closest_occupied_cells(self) -> None:
        # The free cell [0, 2] is at distance 3 from [0, 5], but the closest occupied cell, [1, 2], is at distance 4.
        input_data = city_input(2, 6, 3, ['R 10: #../###', 'U 3: #'])
        self.assertEqual(self.score_files(input_data, b'2\n0 0 0\n1 0 5\n'), 0)
        self.assertEqual(self.score_files(input_data, b'2\n0 0 0\n1 1 5\n'), 10)

    def test_utility_in_the_notch_of_a_residential_building(self) -> None:
        input_data = city_input(2, 3, 1, ['R 10: #.#/###', 'U 3: #'])
        self.assertEqual(self.score_files(input_data, b'2\n0 0 0\n1 0 1\n'), 10)

    def test_buildings_in_between_do_not_block(self) -> None:
        input_data = city_input(1, 3, 2, ['R 10: #', 'U 3: #', 'R 20: #'])
        self.assertEqual(self.score_files(input_data, b'3\n0 0 0\n2 0 1\n1 0 2\n'), 30)

    def test_each_service_type_counts_once(self) -> None:
        input_data = city_input(3, 3, 1, ['R 10: #', 'U 0: #', 'U 0: #', 'U 7: #'])
        self.assertEqual(self.score_files(input_data, b'3\n0 1 1\n1 0 1\n2 1 0\n'), 10)
        self.assertEqual(self.score_files(input_data, b'3\n0 1 1\n1 0 1\n1 1 0\n'), 10)
        self.assertEqual(self.score_files(input_data, b'3\n0 1 1\n1 0 1\n3 1 0\n'), 20)

    def test_one_utility_serves_every_residential_building_near_it(self) -> None:
        input_data = city_input(1, 3, 1, ['R 10: #', 'U 3: #', 'R 20: #'])
        self.assertEqual(self.score_files(input_data, b'3\n0 0 0\n1 0 1\n2 0 2\n'), 30)

    def test_residential_and_utility_buildings_alone_score_nothing(self) -> None:
        input_data = city_input(1, 3, 2, ['R 10: #', 'U 3: #'])
        self.assertEqual(self.score_files(input_data, b'2\n0 0 0\n0 0 1\n'), 0)
        self.assertEqual(self.score_files(input_data, b'2\n1 0 0\n1 0 1\n'), 0)

    def test_walking_distance_past_the_edge_of_the_city(self) -> None:
        input_data = city_input(3, 3, 20, ['R 10: #', 'U 3: #'])
        self.assertEqual(self.score_files(input_data, b'2\n0 0 0\n1 2 2\n'), 10)
        self.assertEqual(self.score_files(input_data, b'2\n0 2 2\n1 0 0\n'), 10)

    def test_project_built_several_times(self) -> None:
        output = b'5\n1 3 2\n2 1 2\n0 1 0\n0 0 4\n1 0 0\n'
        self.assertEqual(self.score_output(output), 100)

    def test_free_cells_may_overlap(self) -> None:
        # The statement's placement: 111 / 21. / 22.
        input_data = city_input(3, 3, 1, ['R 10: ###/.#.', 'U 3: #./##'])
        self.assertEqual(self.score_files(input_data, b'2\n0 0 0\n1 1 0\n'), 10)

    def test_occupied_cells_overlap(self) -> None:
        self.assert_invalid(
            b'2\n2 0 2\n1 1 0\n',
            'line 3: project 1 placed at [1, 0] occupies cell [1, 2], which the building on line 2 occupies',
        )
        self.assert_invalid(
            b'2\n0 0 0\n0 0 0\n',
            'line 3: project 0 placed at [0, 0] occupies cell [0, 1], which the building on line 2 occupies',
        )

    def test_building_past_the_edge_of_the_city(self) -> None:
        self.assert_invalid(
            b'1\n0 2 0\n', 'line 2: project 0 placed at [2, 0] covers rows 2 to 4, expected rows up to H - 1 = 3'
        )
        self.assert_invalid(
            b'1\n1 0 4\n',
            'line 2: project 1 placed at [0, 4] covers columns 4 to 7, expected columns up to W - 1 = 6',
        )
        self.assertEqual(self.score_output(b'1\n1 3 3\n'), 0)

    def test_building_count_out_of_range(self) -> None:
        self.assert_invalid(b'-1\n', 'line 1: found N = -1, expected 0 to H × W = 28')
        self.assert_invalid(b'29\n' + b'2 0 0\n' * 29, 'line 1: found N = 29, expected 0 to H × W = 28')

    def test_numbers_out_of_range(self) -> None:
        self.assert_invalid(b'1\n3 0 0\n', 'line 2: found b = 3, expected 0 to B - 1 = 2')
        self.assert_invalid(b'1\n-1 0 0\n', 'line 2: found b = -1, expected 0 to B - 1 = 2')
        self.assert_invalid(b'1\n2 4 0\n', 'line 2: found r = 4, expected 0 to H - 1 = 3')
        self.assert_invalid(b'1\n2 -1 0\n', 'line 2: found r = -1, expected 0 to H - 1 = 3')
        self.assert_invalid(b'1\n2 0 7\n', 'line 2: found c = 7, expected 0 to W - 1 = 6')
        self.assert_invalid(b'1\n2 0 -1\n', 'line 2: found c = -1, expected 0 to W - 1 = 6')

    def test_building_count_line_with_more_than_one_token(self) -> None:
        self.assert_invalid(b'1 0 0 0\n', 'line 1: found 4 tokens, expected N')

    def test_building_line_with_the_wrong_number_of_tokens(self) -> None:
        self.assert_invalid(b'1\n0 0\n', 'line 2: found 2 tokens, expected b, r and c')
        self.assert_invalid(b'1\n0 0 0 0\n', 'line 2: found 4 tokens, expected b, r and c')
        self.assert_invalid(b'1\n\n0 0 0\n', 'line 2: found 0 tokens, expected b, r and c')

    def test_fewer_lines_than_expected(self) -> None:
        self.assert_invalid(b'2\n0 0 0\n', 'line 3: found the end of the file, expected b, r and c')

    def test_more_lines_than_expected(self) -> None:
        self.assert_invalid(b'1\n0 0 0\n2 0 2\n', "line 3: found '2 0 2', expected the end of the file")

    def test_any_whitespace_and_blank_lines_at_the_end(self) -> None:
        output = b' 4 \r\n0\t0 0\r\n1  3 0\n 2 0 2 \n0 0 5\r\n\r\n \n'
        self.assertEqual(self.score_output(output), 75)

    def test_missing_newline_at_the_end(self) -> None:
        with open(EXAMPLE_OUT, 'rb') as file:
            self.assertEqual(self.score_output(file.read().rstrip(b'\n')), 75)

    def test_empty_file(self) -> None:
        self.assert_invalid(b'', 'line 1: found the end of the file, expected N')

    def test_integers_are_parsed_strictly(self) -> None:
        for token in ['+1', '1.0', '0x1', '0_1', 'one']:
            with self.subTest(token=token):
                self.assert_invalid(
                    f'{token}\n0 0 0\n'.encode('ascii'), f'line 1: found {token!r}, expected an integer'
                )
                self.assert_invalid(
                    f'1\n0 {token} 0\n'.encode('ascii'), f'line 2: found {token!r}, expected an integer'
                )

    def test_non_ascii_byte(self) -> None:
        self.assert_invalid('1\n0 0 ٠\n'.encode('utf-8'), 'line 2: found the byte 0xd9, expected ASCII text')

    def test_integer_with_thousands_of_digits(self) -> None:
        with self.assertRaises(judge.InvalidOutput):
            self.score_output(b'1' * 5000 + b'\n')

    def test_input_with_a_newline_at_the_end(self) -> None:
        # The example input, like a_example.in, has no newline at the end.
        with open(EXAMPLE_IN, 'rb') as file:
            input_data = file.read()
        self.assertEqual(self.score_files(input_data + b'\n', b'4\n0 0 0\n1 3 0\n2 0 2\n0 0 5\n'), 75)

    def test_input_out_of_range(self) -> None:
        for header, projects in [
            ('0 1 1', ['R 1: #', 'U 1: #']),
            ('1001 1 1', ['R 1: #', 'U 1: #']),
            ('1 0 1', ['R 1: #', 'U 1: #']),
            ('1 1001 1', ['R 1: #', 'U 1: #']),
            ('1 1 0', ['R 1: #', 'U 1: #']),
            ('1 1 21', ['R 1: #', 'U 1: #']),
            ('1 1 1', ['R 1: #']),
            ('1 1 1', ['R 0: #', 'U 1: #']),
            ('1 1 1', ['R 1001: #', 'U 1: #']),
            ('1 1 1', ['R 1: #', 'U 1001: #']),
            ('1 2 1', ['R 1: #/#', 'U 1: #']),
            ('2 1 1', ['R 1: ##', 'U 1: #']),
            ('60 60 1', ['R 1: ' + '#' * 51, 'U 1: #']),
            ('60 60 1', ['R 1: ' + '/'.join(['#'] * 51), 'U 1: #']),
        ]:
            with self.subTest(header=header, projects=projects):
                height, width, distance = (int(token) for token in header.split(' '))
                self.assert_invalid_input(city_input(height, width, distance, projects))

    def test_input_largest_values(self) -> None:
        input_data = city_input(1000, 1000, 20, ['R 1000: ' + '#' * 50, 'U 1000: ' + '/'.join(['#'] * 50)])
        self.assertEqual(self.score_files(input_data, b'2\n0 0 0\n1 1 0\n'), 1000)

    def test_input_without_both_project_types(self) -> None:
        self.assert_invalid_input(city_input(1, 1, 1, ['R 1: #', 'R 1: #']))
        self.assert_invalid_input(city_input(1, 1, 1, ['U 1: #', 'U 1: #']))

    def test_input_plans_from_the_statement(self) -> None:
        self.score_files(city_input(3, 4, 1, ['R 1: ####/.#../####', 'U 1: #']), b'0\n')
        for plan in ['..##/.###/..##', '#.##/.#../#.##', '####/#..#/####']:
            with self.subTest(plan=plan):
                self.assert_invalid_input(city_input(3, 4, 1, ['R 1: ' + plan, 'U 1: #']))

    def test_input_plan_without_an_occupied_cell_on_an_edge(self) -> None:
        for plan in ['...', '##./##.', '.##/.##', '##/..']:
            with self.subTest(plan=plan):
                self.assert_invalid_input(city_input(3, 3, 1, ['R 1: ' + plan, 'U 1: #']))

    def test_input_plan_with_a_hole_open_to_the_border_by_a_corner(self) -> None:
        # The free cell [1, 1] touches the free cell [2, 2] only by a corner, so it is a hole.
        self.assert_invalid_input(city_input(3, 3, 1, ['R 1: ###/#.#/##.', 'U 1: #']))
        self.score_files(city_input(3, 3, 1, ['R 1: ###/#..', 'U 1: #']), b'0\n')

    def test_input_breaks_the_format(self) -> None:
        with open(EXAMPLE_IN, 'rb') as file:
            valid = file.read()
        for old, new in [
            (b'4 7 2 3', b'4 7 2  3'),
            (b'4 7 2 3', b'4 7 2 3 '),
            (b'4 7 2 3\n', b'4 7 2 3\r\n'),
            (b'R 3 2 25', b'R 3 2 +25'),
            (b'R 3 2 25', b'H 3 2 25'),
            (b'R 3 2 25', b'r 3 2 25'),
            (b'.#\n##', b'.#\n#'),
            (b'.#\n##', b'.#\n###'),
            (b'.#\n##', b'.#\n#o'),
            (b'U 2 2 5', b'U 3 2 5'),
        ]:
            with self.subTest(new=new):
                self.assert_invalid_input(valid.replace(old, new, 1))

    def test_input_with_more_lines_than_expected(self) -> None:
        self.assert_invalid_input(city_input(1, 1, 1, ['R 1: #', 'U 1: #']) + b'#\n')

