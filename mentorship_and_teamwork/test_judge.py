import os
import tempfile
import unittest

import judge

FOLDER = os.path.dirname(__file__)
EXAMPLE_IN = os.path.join(FOLDER, 'example.in')
EXAMPLE_OUT = os.path.join(FOLDER, 'example.out')


def section(spec: str) -> str:
    """Turn 'Ann: A 5, B 1' into the lines of a contributor, or 'P 1 10 10: A 3' into the lines of a project."""
    head, skills = spec.split(': ')
    skill_lines = skills.split(', ')
    return '\n'.join([f'{head} {len(skill_lines)}'] + skill_lines) + '\n'


def team_input(contributors: list[str], projects: list[str]) -> bytes:
    header = f'{len(contributors)} {len(projects)}\n'
    return (header + ''.join(section(spec) for spec in contributors + projects)).encode('ascii')


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
        self.assertEqual(judge.main(EXAMPLE_IN, EXAMPLE_OUT), 33)

    def test_no_project_scores_zero(self) -> None:
        self.assertEqual(self.score_output(b'0\n'), 0)

    def test_contributor_learns_for_a_later_project(self) -> None:
        # Anna has C++ 2 and Logging needs C++ 3. She reaches 3 on WebServer, but only if it comes first.
        self.assertEqual(self.score_output(b'2\nWebServer\nBob Anna\nLogging\nAnna\n'), 10 + 3)
        self.assert_invalid(
            b'2\nLogging\nAnna\nWebServer\nBob Anna\n',
            'line 3: Anna has C++ at level 2 for role 0 of project Logging, expected level 3, or 2 with a mentor, '
            'but no other contributor on the project has C++ at level 3 or higher',
        )

    def test_contributor_waits_for_their_previous_project(self) -> None:
        # WebChat keeps Bob busy until day 10, so WebServer runs from day 10 to 16 although Anna is free from day 0.
        # Late by 17 - 7 = 10 days, it scores 10 - 10 = 0 points.
        self.assertEqual(self.score_output(b'2\nWebChat\nMaria Bob\nWebServer\nBob Anna\n'), 20)

    def test_project_that_ends_the_day_before_best_before_scores_in_full(self) -> None:
        contributors = ['Ann: A 1']
        self.assertEqual(self.score_files(team_input(contributors, ['P 5 10 5: A 1']), b'1\nP\nAnn\n'), 10)
        self.assertEqual(self.score_files(team_input(contributors, ['P 5 10 4: A 1']), b'1\nP\nAnn\n'), 9)

    def test_late_project_scores_no_less_than_zero(self) -> None:
        input_data = team_input(['Ann: A 1', 'Ben: A 1'], ['Late 10 3 1: A 1', 'Early 1 5 10: A 1'])
        self.assertEqual(self.score_files(input_data, b'2\nLate\nAnn\nEarly\nBen\n'), 5)

    def test_project_that_scores_zero_still_teaches(self) -> None:
        # Ann reaches A 3 on Late, which ends on day 10, and Next then ends on day 11.
        input_data = team_input(['Ann: A 2'], ['Late 10 1 1: A 2', 'Next 1 10 100: A 3'])
        self.assertEqual(self.score_files(input_data, b'2\nLate\nAnn\nNext\nAnn\n'), 10)

    def test_contributor_above_the_required_level_does_not_learn(self) -> None:
        input_data = team_input(['Ann: A 3'], ['Easy 1 10 10: A 2', 'Exact 1 10 10: A 3', 'Hard 1 10 10: A 4'])
        self.assertEqual(self.score_files(input_data, b'2\nExact\nAnn\nHard\nAnn\n'), 20)
        self.assert_invalid(
            b'2\nEasy\nAnn\nHard\nAnn\n',
            'line 5: Ann has A at level 3 for role 0 of project Hard, expected level 4, or 3 with a mentor, '
            'but no other contributor on the project has A at level 4 or higher',
            input_data,
        )

    def test_mentored_contributor_learns_and_mentor_does_not(self) -> None:
        # Ann mentors Ben on A from a role that needs A 1, and Ben reaches A 3.
        input_data = team_input(
            ['Ann: A 5', 'Ben: A 2'],
            ['Pair 1 10 10: A 3, A 1', 'Ben3 1 10 10: A 3', 'Ann6 1 10 10: A 6'],
        )
        self.assertEqual(self.score_files(input_data, b'2\nPair\nBen Ann\nBen3\nBen\n'), 20)
        self.assert_invalid(
            b'2\nPair\nBen Ann\nAnn6\nAnn\n',
            'line 5: Ann has A at level 5 for role 0 of project Ann6, expected level 6, or 5 with a mentor, '
            'but no other contributor on the project has A at level 6 or higher',
            input_data,
        )

    def test_contributor_without_the_skill_is_mentored_from_level_0(self) -> None:
        # Ann knows no B. Mentored on Pair, she reaches B 1, which is all that Next needs.
        input_data = team_input(['Ann: A 1', 'Ben: B 2'], ['Pair 1 10 10: B 1, B 2', 'Next 1 10 10: B 1'])
        self.assertEqual(self.score_files(input_data, b'2\nPair\nAnn Ben\nNext\nAnn\n'), 20)

    def test_mentor_with_too_low_a_level(self) -> None:
        input_data = team_input(['Ann: A 2', 'Ben: A 2'], ['Pair 1 10 10: A 3, A 1'])
        self.assert_invalid(
            b'1\nPair\nAnn Ben\n',
            'line 3: Ann has A at level 2 for role 0 of project Pair, expected level 3, or 2 with a mentor, '
            'but no other contributor on the project has A at level 3 or higher',
            input_data,
        )

    def test_two_levels_short_even_with_a_mentor(self) -> None:
        # Anna knows no HTML, two levels short of HTML 3, although Bob has HTML 5.
        self.assert_invalid(
            b'1\nWebServer\nAnna Bob\n',
            'line 3: Anna has HTML at level 0 for role 0 of project WebServer, expected level 3, or 2 with a mentor',
        )

    def test_one_mentor_for_several_contributors(self) -> None:
        input_data = team_input(['Ann: A 5', 'Ben: A 2', 'Cid: A 2'], ['Trio 1 10 10: A 3, A 3, A 1'])
        self.assertEqual(self.score_files(input_data, b'1\nTrio\nBen Cid Ann\n'), 10)

    def test_contributor_mentors_and_is_mentored_at_once(self) -> None:
        input_data = team_input(['Ann: A 5, B 1', 'Ben: A 1, B 5'], ['Pair 1 10 10: A 2, B 2'])
        self.assertEqual(self.score_files(input_data, b'1\nPair\nBen Ann\n'), 10)

    def test_level_learned_on_a_project_cannot_mentor_on_it(self) -> None:
        # Ann reaches A 5 only when Pair is completed, so nobody on it has A 5 to mentor Ben.
        input_data = team_input(['Ann: A 4', 'Ben: A 4'], ['Pair 1 10 10: A 4, A 5'])
        self.assert_invalid(
            b'1\nPair\nAnn Ben\n',
            'line 3: Ben has A at level 4 for role 1 of project Pair, expected level 5, or 4 with a mentor, '
            'but no other contributor on the project has A at level 5 or higher',
            input_data,
        )

    def test_project_count_out_of_range(self) -> None:
        self.assert_invalid(b'-1\n', 'line 1: found E = -1, expected 0 to P = 3')
        self.assert_invalid(b'4\n', 'line 1: found E = 4, expected 0 to P = 3')

    def test_project_count_line_with_more_than_one_token(self) -> None:
        self.assert_invalid(b'1 1\n', 'line 1: found 2 tokens, expected E')

    def test_project_that_does_not_exist(self) -> None:
        self.assert_invalid(b'1\nWebShop\nBob Anna\n', "line 2: project 'WebShop' does not exist")
        self.assert_invalid(b'1\nwebserver\nBob Anna\n', "line 2: project 'webserver' does not exist")

    def test_project_line_with_more_than_one_token(self) -> None:
        self.assert_invalid(b'1\nWebServer Bob Anna\n', 'line 2: found 3 tokens, expected a project name')
        self.assert_invalid(b'1\n\nWebServer\nBob Anna\n', 'line 2: found 0 tokens, expected a project name')

    def test_project_listed_twice(self) -> None:
        self.assert_invalid(
            b'2\nWebChat\nMaria Bob\nWebChat\nMaria Bob\n',
            'line 4: project WebChat is listed a second time, first listed on line 2',
        )

    def test_contributor_count_differs_from_role_count(self) -> None:
        expected = 'expected the names of the 2 contributors of project WebServer'
        self.assert_invalid(b'1\nWebServer\nBob\n', f'line 3: found 1 tokens, {expected}')
        self.assert_invalid(b'1\nWebServer\nBob Anna Maria\n', f'line 3: found 3 tokens, {expected}')
        self.assert_invalid(b'1\nWebServer\n\n', f'line 3: found 0 tokens, {expected}')

    def test_contributor_that_does_not_exist(self) -> None:
        self.assert_invalid(b'1\nWebServer\nBob Eve\n', "line 3: contributor 'Eve' does not exist")
        self.assert_invalid(b'1\nWebServer\nbob Anna\n', "line 3: contributor 'bob' does not exist")

    def test_contributor_in_two_roles_of_one_project(self) -> None:
        # Bob has HTML 5 and could mentor himself to C++ 2 if he counted as his own mentor.
        self.assert_invalid(
            b'1\nWebServer\nBob Bob\n', 'line 3: contributor Bob fills a second role on project WebServer'
        )

    def test_fewer_lines_than_expected(self) -> None:
        self.assert_invalid(b'2\nWebServer\nBob Anna\n', 'line 4: found the end of the file, expected a project name')
        self.assert_invalid(
            b'1\nWebServer\n',
            'line 3: found the end of the file, expected the names of the 2 contributors of project WebServer',
        )

    def test_more_lines_than_expected(self) -> None:
        self.assert_invalid(
            b'1\nWebChat\nMaria Bob\nLogging\n', "line 4: found 'Logging', expected the end of the file"
        )

    def test_any_whitespace_and_blank_lines_at_the_end(self) -> None:
        output = b' 3 \r\nWebServer\r\n\tBob  Anna\nLogging \nAnna\nWebChat\nMaria\tBob\r\n\r\n \n'
        self.assertEqual(self.score_output(output), 33)

    def test_missing_newline_at_the_end(self) -> None:
        with open(EXAMPLE_OUT, 'rb') as file:
            self.assertEqual(self.score_output(file.read().rstrip(b'\n')), 33)

    def test_empty_file(self) -> None:
        self.assert_invalid(b'', 'line 1: found the end of the file, expected E')

    def test_integers_are_parsed_strictly(self) -> None:
        for token in ['+1', '1.0', '0x1', '0_1', 'one']:
            with self.subTest(token=token):
                self.assert_invalid(
                    f'{token}\nWebChat\nMaria Bob\n'.encode('ascii'), f'line 1: found {token!r}, expected an integer'
                )

    def test_non_ascii_byte(self) -> None:
        self.assert_invalid(
            '1\nWebChat\nMaria Böb\n'.encode('utf-8'), 'line 3: found the byte 0xc3, expected ASCII text'
        )

    def test_integer_with_thousands_of_digits(self) -> None:
        with self.assertRaises(judge.InvalidOutput):
            self.score_output(b'1' * 5000 + b'\n')

    def test_input_without_a_newline_at_the_end(self) -> None:
        with open(EXAMPLE_IN, 'rb') as file:
            input_data = file.read().rstrip(b'\n')
        with open(EXAMPLE_OUT, 'rb') as file:
            self.assertEqual(self.score_files(input_data, file.read()), 33)

    def test_role_may_require_a_level_above_10(self) -> None:
        input_data = team_input(['Ann: A 10', 'Ben: A 10'], ['Lead 1 10 10: A 10', 'Top 1 10 10: A 11'])
        self.assertEqual(self.score_files(input_data, b'2\nLead\nAnn\nTop\nAnn\n'), 20)

    def test_input_out_of_range(self) -> None:
        valid = ['1 1\n', 'Ann 1\n', 'A 1\n', 'P 1 1 1 1\n', 'A 1\n']
        for index, line in [
            (0, '0 1\n'),
            (0, '1 0\n'),
            (0, '100001 1\n'),
            (1, 'Ann 0\n'),
            (1, 'Ann 101\n'),
            (2, 'A 0\n'),
            (2, 'A 11\n'),
            (3, 'P 0 1 1 1\n'),
            (3, 'P 100001 1 1 1\n'),
            (3, 'P 1 0 1 1\n'),
            (3, 'P 1 1 0 1\n'),
            (3, 'P 1 1 1 0\n'),
            (3, 'P 1 1 1 101\n'),
            (4, 'A 0\n'),
            (4, 'A 101\n'),
        ]:
            with self.subTest(line=line):
                lines = valid.copy()
                lines[index] = line
                self.assert_invalid_input(''.join(lines).encode('ascii'))

    def test_input_breaks_the_format(self) -> None:
        with open(EXAMPLE_IN, 'rb') as file:
            valid = file.read()
        for old, new in [
            (b'Anna 1', b'Anna  1'),
            (b'Anna 1', b'Anna 1 '),
            (b'Anna 1\n', b'Anna 1\r\n'),
            (b'Anna 1', b'Anna +1'),
            (b'Anna', b'An-na'),
            (b'Anna', b'A' * 21),
            (b'C++ 2', b'C# 2'),
            (b'C++ 2', b'C' * 21 + b' 2'),
            (b'Logging', b'Log+ging'),
        ]:
            with self.subTest(new=new):
                self.assert_invalid_input(valid.replace(old, new, 1))

    def test_input_with_a_name_twice(self) -> None:
        self.assert_invalid_input(team_input(['Ann: A 1', 'Ann: B 1'], ['P 1 1 1: A 1']))
        self.assert_invalid_input(team_input(['Ann: A 1'], ['P 1 1 1: A 1', 'P 1 1 1: A 1']))

    def test_input_with_a_skill_twice_for_one_contributor(self) -> None:
        self.assert_invalid_input(team_input(['Ann: A 1, A 2'], ['P 1 1 1: A 1']))

    def test_input_with_fewer_sections_than_announced(self) -> None:
        self.assert_invalid_input(team_input(['Ann: A 1'], ['P 1 1 1: A 1']).replace(b'1 1\n', b'2 1\n', 1))
        self.assert_invalid_input(team_input(['Ann: A 1'], ['P 1 1 1: A 1, B 1']).replace(b'P 1 1 1 2', b'P 1 1 1 3'))

    def test_input_with_more_lines_than_expected(self) -> None:
        self.assert_invalid_input(team_input(['Ann: A 1'], ['P 1 1 1: A 1']) + b'A 1\n')
