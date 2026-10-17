"""Score an output file for Hash Code 2022, Qualification Round: Mentorship and teamwork.

python3 judge.py -i example.in -o example.out
"""

import argparse
import dataclasses
import re


class InvalidInput(Exception):
    """The input file breaks the format of the problem statement, which is a bug in the data set."""


class InvalidOutput(Exception):
    """The output file breaks a rule of the problem statement."""


@dataclasses.dataclass(frozen=True)
class Role:
    skill: str
    level: int


@dataclasses.dataclass(frozen=True)
class Project:
    duration: int
    score: int
    best_before: int
    roles: list[Role]


@dataclasses.dataclass(frozen=True)
class Problem:
    skills: dict[str, dict[str, int]]
    projects: dict[str, Project]


@dataclasses.dataclass(frozen=True)
class Completion:
    project: str
    end_day: int


@dataclasses.dataclass(frozen=True)
class Solution:
    completions: list[Completion]


def read_input_line(lines: list[str], line_number: int, pattern: str, expected: str) -> list[str]:
    if line_number > len(lines):
        raise InvalidInput(f'line {line_number}: found the end of the file, expected {expected}')
    line = lines[line_number - 1]
    if re.fullmatch(pattern, line) is None:
        raise InvalidInput(
            f'line {line_number}: found {line[:100]!r}, expected {expected} separated by single spaces'
        )
    return line.split(' ')


def check_input_range(value: int, line_number: int, name: str, low: int, high: int) -> None:
    if not low <= value <= high:
        raise InvalidInput(f'line {line_number}: found {name} = {value}, expected {low} to {high}')


def read_skills(
    lines: list[str],
    line_number: int,
    count: int,
    max_level: int,
) -> list[tuple[str, int]]:
    skills = []
    for skill_line in range(line_number, line_number + count):
        # Matches 'C++ 3'
        tokens = read_input_line(lines, skill_line, r'[A-Za-z0-9+-]{1,20} [0-9]{1,3}', 'a skill name and its level')
        level = int(tokens[1])
        check_input_range(level, skill_line, 'L', 1, max_level)
        skills.append((tokens[0], level))
    return skills


def read_problem(input_file: str) -> Problem:
    with open(input_file, encoding='ascii', newline='') as file:
        lines = file.read().split('\n')

    tokens = read_input_line(lines, 1, r'[0-9]{1,6} [0-9]{1,6}', 'C and P')
    contributor_count, project_count = int(tokens[0]), int(tokens[1])
    check_input_range(contributor_count, 1, 'C', 1, 100_000)
    check_input_range(project_count, 1, 'P', 1, 100_000)

    line_number = 2
    skills = {}
    for _ in range(contributor_count):
        # Matches 'Anna 1'
        tokens = read_input_line(lines, line_number, r'[A-Za-z0-9]{1,20} [0-9]{1,3}', 'a contributor name and N')
        name, skill_count = tokens[0], int(tokens[1])
        check_input_range(skill_count, line_number, 'N', 1, 100)
        if name in skills:
            raise InvalidInput(f'line {line_number}: contributor {name} is described a second time')
        contributor_skills = dict(read_skills(lines, line_number + 1, skill_count, 10))
        if len(contributor_skills) != skill_count:
            raise InvalidInput(f'line {line_number}: contributor {name} has a skill listed twice')
        skills[name] = contributor_skills
        line_number += 1 + skill_count

    projects = {}
    for _ in range(project_count):
        # Matches 'WebServer 7 10 7 2'
        pattern = r'[A-Za-z0-9]{1,20}( [0-9]{1,6}){4}'
        tokens = read_input_line(lines, line_number, pattern, 'a project name, D, S, B and R')
        name = tokens[0]
        duration, project_score, best_before, role_count = (int(token) for token in tokens[1:])
        check_input_range(duration, line_number, 'D', 1, 100_000)
        check_input_range(project_score, line_number, 'S', 1, 100_000)
        check_input_range(best_before, line_number, 'B', 1, 100_000)
        check_input_range(role_count, line_number, 'R', 1, 100)
        if name in projects:
            raise InvalidInput(f'line {line_number}: project {name} is described a second time')
        roles = [Role(skill, level) for skill, level in read_skills(lines, line_number + 1, role_count, 100)]
        projects[name] = Project(duration, project_score, best_before, roles)
        line_number += 1 + role_count

    for line_number in range(line_number, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidInput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    return Problem(skills, projects)


def read_lines(output_file: str) -> list[str]:
    with open(output_file, 'rb') as file:
        data = file.read()
    try:
        text = data.decode('ascii')
    except UnicodeDecodeError as error:
        line_number = data.count(b'\n', 0, error.start) + 1
        raise InvalidOutput(
            f'line {line_number}: found the byte {data[error.start]:#04x}, expected ASCII text'
        ) from None

    lines = text.split('\n')
    # The newline at the end of the last line leaves an empty string after it, which is not a line.
    if lines[-1] == '':
        lines.pop()
    return lines


def parse_int(token: str, line_number: int) -> int:
    if re.fullmatch(r'-?[0-9]+', token) is None:
        raise InvalidOutput(f'line {line_number}: found {token[:100]!r}, expected an integer')
    try:
        return int(token)
    except ValueError:
        # Since Python 3.10.7, int() refuses more than 4300 digits by default.
        raise InvalidOutput(
            f'line {line_number}: found an integer of {len(token)} characters, which is too long'
        ) from None


def read_tokens(lines: list[str], line_number: int, expected: str) -> list[str]:
    if line_number > len(lines):
        raise InvalidOutput(f'line {line_number}: found the end of the file, expected {expected}')
    return lines[line_number - 1].split()


def read_project_name(lines: list[str], line_number: int, problem: Problem, listed_on_line: dict[str, int]) -> str:
    tokens = read_tokens(lines, line_number, 'a project name')
    if len(tokens) != 1:
        raise InvalidOutput(f'line {line_number}: found {len(tokens)} tokens, expected a project name')

    name = tokens[0]
    if name not in problem.projects:
        raise InvalidOutput(f'line {line_number}: project {name[:100]!r} does not exist')
    # Each project can be mentioned at most once in the submission file.
    if name in listed_on_line:
        raise InvalidOutput(
            f'line {line_number}: project {name} is listed a second time, first listed on line {listed_on_line[name]}'
        )
    return name


def read_contributor_names(lines: list[str], line_number: int, problem: Problem, project: str) -> list[str]:
    role_count = len(problem.projects[project].roles)
    expected = f'the names of the {role_count} contributors of project {project}'
    names = read_tokens(lines, line_number, expected)
    if len(names) != role_count:
        raise InvalidOutput(f'line {line_number}: found {len(names)} tokens, expected {expected}')

    for name in names:
        if name not in problem.skills:
            raise InvalidOutput(f'line {line_number}: contributor {name[:100]!r} does not exist')
    # Each contributor can fill at most one role on a single project.
    if len(set(names)) != len(names):
        twice = next(name for index, name in enumerate(names) if name in names[:index])
        raise InvalidOutput(f'line {line_number}: contributor {twice} fills a second role on project {project}')
    return names


def check_roles(
    project: Project,
    project_name: str,
    names: list[str],
    levels: list[int],
    skills: dict[str, dict[str, int]],
    line_number: int,
) -> None:
    """Check that each contributor can fill their role, with the skill levels they have when the project starts."""
    for index, (role, name, level) in enumerate(zip(project.roles, names, levels)):
        if level >= role.level:
            continue
        where = (
            f'line {line_number}: {name} has {role.skill} at level {level} for role {index} of project {project_name}'
        )
        if level < role.level - 1:
            raise InvalidOutput(f'{where}, expected level {role.level}, or {role.level - 1} with a mentor')
        # The mentor is another contributor on the project. The contributor being mentored is one level short, so
        # they never count as their own mentor.
        if all(skills[mentor].get(role.skill, 0) < role.level for mentor in names):
            raise InvalidOutput(
                f'{where}, expected level {role.level}, or {role.level - 1} with a mentor, but no other contributor '
                f'on the project has {role.skill} at level {role.level} or higher'
            )


def read_solution(output_file: str, problem: Problem) -> Solution:
    lines = read_lines(output_file)

    tokens = read_tokens(lines, 1, 'E')
    if len(tokens) != 1:
        raise InvalidOutput(f'line 1: found {len(tokens)} tokens, expected E')
    project_count = parse_int(tokens[0], 1)
    if not 0 <= project_count <= len(problem.projects):
        raise InvalidOutput(f'line 1: found E = {project_count}, expected 0 to P = {len(problem.projects)}')

    # Contributors learn as they go, so copy their skills rather than change the problem.
    skills = {name: dict(contributor_skills) for name, contributor_skills in problem.skills.items()}
    available_from = dict.fromkeys(problem.skills, 0)
    listed_on_line = {}
    completions = []
    for line_number in range(2, 2 * project_count + 2, 2):
        project_name = read_project_name(lines, line_number, problem, listed_on_line)
        listed_on_line[project_name] = line_number
        names = read_contributor_names(lines, line_number + 1, problem, project_name)

        project = problem.projects[project_name]
        levels = [skills[name].get(role.skill, 0) for role, name in zip(project.roles, names)]
        check_roles(project, project_name, names, levels, skills, line_number + 1)

        # A contributor works on their projects in the order of the submission file, so by the time this project
        # starts they have finished and learned from every project listed before it.
        start_day = max(available_from[name] for name in names)
        end_day = start_day + project.duration
        # Contributors learn when the project is completed, so a level gained here cannot mentor a role on it.
        for role, name, level in zip(project.roles, names, levels):
            if level <= role.level:
                skills[name][role.skill] = level + 1
            available_from[name] = end_day
        completions.append(Completion(project_name, end_day))

    for line_number in range(2 * project_count + 2, len(lines) + 1):
        if lines[line_number - 1].split():
            raise InvalidOutput(
                f'line {line_number}: found {lines[line_number - 1][:100]!r}, expected the end of the file'
            )

    return Solution(completions)


def score(problem: Problem, solution: Solution) -> int:
    points = 0
    for completion in solution.completions:
        project = problem.projects[completion.project]
        # A project whose last day of work, end_day - 1, comes before its best before day is not late.
        days_late = max(0, completion.end_day - project.best_before)
        points += max(0, project.score - days_late)
    return points


def main(input_file: str, output_file: str) -> int:
    problem = read_problem(input_file)
    solution = read_solution(output_file, problem)
    return score(problem, solution)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-i', '--input_file', required=True)
    parser.add_argument('-o', '--output_file', required=True)

    args = parser.parse_args()
    try:
        print(main(args.input_file, args.output_file))
    except InvalidOutput as error:
        raise SystemExit(f'Invalid output: {error}')
