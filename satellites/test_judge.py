import os
import tempfile
import unittest

import judge

FOLDER = os.path.dirname(__file__)
EXAMPLE_IN = os.path.join(FOLDER, 'example.in')
EXAMPLE_OUT = os.path.join(FOLDER, 'example.out')

# 10 turns, 1 satellite at [0, 0] heading north at 100 per turn, with w = 50 and d = 250. At turn t it is at
# [100 * t, -15 * t]. Collection 0 wants [200, -30] in turns 2 to 4, collection 1 wants [200, -30] and [500, -75] in
# turns 0 to 2 or 5 to 9.
SMALL_IN = b'10\n1\n0 0 100 50 250\n2\n10 1 1\n200 -30\n2 4\n20 2 2\n200 -30\n500 -75\n0 2\n5 9\n'


def walk_table(satellite: judge.Satellite, turns: int) -> list[tuple[int, int]]:
    """Return [φ, λ] for each turn by applying the movement table of the statement one turn at a time."""
    latitude, longitude, velocity = satellite.latitude, satellite.longitude, satellite.velocity
    positions = []
    for _ in range(turns):
        positions.append((latitude, longitude))
        moved = latitude + velocity
        if moved > 324000:
            latitude, longitude, velocity = 648000 - moved, -648000 + (longitude - 15), -velocity
        elif moved < -324000:
            latitude, longitude, velocity = -648000 - moved, -648000 + (longitude - 15), -velocity
        else:
            latitude, longitude = moved, longitude - 15
        if longitude < -648000:
            longitude += 1296000
        if longitude > 647999:
            longitude -= 1296000
    return positions


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
        return self.score_files(SMALL_IN, output)

    def assert_invalid(self, output: bytes, message: str, input_data: bytes = SMALL_IN) -> None:
        with self.assertRaises(judge.InvalidOutput) as context:
            self.score_files(input_data, output)
        self.assertEqual(str(context.exception), message)

    def assert_invalid_input(self, input_data: bytes) -> None:
        with self.assertRaises(judge.InvalidInput):
            self.score_files(input_data, b'0\n')

    def test_example_score_matches_statement(self) -> None:
        self.assertEqual(judge.main(EXAMPLE_IN, EXAMPLE_OUT), 200)

    def test_movement_example_of_the_statement(self) -> None:
        satellite = judge.Satellite(176400, 7200, 120, 0, 0)
        self.assertEqual(satellite.position(1), (176520, 7185))
        # The statement prints [39600, -586800] for turn 3600, which adds 15″ per turn instead of subtracting it,
        # unlike turn 1 and the movement table. The table gives 7200 - 15 * 3600 - 648000, wrapped to 601200.
        self.assertEqual(satellite.position(3600), (39600, 601200))

    def test_position_follows_the_movement_table_over_both_poles(self) -> None:
        satellites = [
            judge.Satellite(176400, 7200, 120, 0, 0),
            judge.Satellite(-91637, -40501, -400, 0, 0),
            judge.Satellite(324000, 647999, 500, 0, 0),
            judge.Satellite(-324000, -648000, -100, 0, 0),
            # These land exactly on 90°, which is not a crossing: the table moves on normally while φ + v ≤ 90°.
            judge.Satellite(323700, 0, 300, 0, 0),
            judge.Satellite(-323600, 100, -200, 0, 0),
        ]
        for satellite in satellites:
            with self.subTest(satellite=satellite):
                positions = walk_table(satellite, 30000)
                self.assertEqual([satellite.position(turn) for turn in range(30000)], positions)

    def test_no_image(self) -> None:
        self.assertEqual(self.score_output(b'0\n'), 0)

    def test_image_counts_for_every_collection_with_its_location(self) -> None:
        self.assertEqual(self.score_output(b'2\n200 -30 2 0\n500 -75 5 0\n'), 10 + 20)

    def test_locations_can_use_different_ranges(self) -> None:
        # [200, -30] is taken in range 0 to 2 and [500, -75] in range 5 to 9 of collection 1.
        self.assertEqual(self.score_output(b'2\n200 -30 2 0\n500 -75 5 0\n'), 30)
        self.assertEqual(self.score_output(b'1\n200 -30 2 0\n'), 10)

    def test_ranges_include_both_ends(self) -> None:
        # The satellite is at [300, -45] at turn 3 and at [400, -60] at turn 4.
        self.assertEqual(self.score_output(b'1\n200 -30 3 0\n'), 10)
        self.assertEqual(self.score_output(b'1\n200 -30 4 0\n'), 10)

    def test_image_outside_every_range_earns_nothing(self) -> None:
        self.assertEqual(self.score_output(b'1\n500 -75 4 0\n'), 0)
        self.assertEqual(self.score_output(b'2\n200 -30 2 0\n500 -75 4 0\n'), 10)

    def test_image_of_a_location_in_no_collection_is_allowed(self) -> None:
        self.assertEqual(self.score_output(b'1\n150 -40 1 0\n'), 0)

    def test_image_at_turn_zero_needs_orientation_zero(self) -> None:
        self.assertEqual(self.score_output(b'1\n0 0 0 0\n'), 0)
        self.assert_invalid(
            b'1\n1 0 0 0\n',
            'line 2: satellite 0 turns its camera from [0, 0] at turn 0 (the start) to [1, 0] at turn 0, '
            'a change of 1 in 0 turns, expected at most w * 0 = 0',
        )

    def test_camera_starts_at_orientation_zero(self) -> None:
        # At turn 1 the satellite is at [100, -15], so [150, 35] needs [50, 50], exactly w from [0, 0].
        self.assertEqual(self.score_output(b'1\n150 35 1 0\n'), 0)
        self.assert_invalid(
            b'1\n151 35 1 0\n',
            'line 2: satellite 0 turns its camera from [0, 0] at turn 0 (the start) to [51, 50] at turn 1, '
            'a change of 51 in 1 turns, expected at most w * 1 = 50',
        )

    def test_camera_speed_is_checked_in_turn_order_not_line_order(self) -> None:
        # Turn 2 needs [0, 0] and turn 4 needs [100, 0]: 100 in 2 turns is exactly w * 2.
        self.assertEqual(self.score_output(b'2\n500 -60 4 0\n200 -30 2 0\n'), 10)
        self.assert_invalid(
            b'2\n501 -60 4 0\n200 -30 2 0\n',
            'line 2: satellite 0 turns its camera from [0, 0] at turn 2 (line 3) to [101, 0] at turn 4, '
            'a change of 101 in 2 turns, expected at most w * 2 = 100',
        )

    def test_camera_speed_is_checked_in_each_dimension(self) -> None:
        # Turn 2 needs [0, 0], and turn 3 at [300, -45] needs [-50, 51].
        self.assert_invalid(
            b'2\n200 -30 2 0\n250 6 3 0\n',
            'line 3: satellite 0 turns its camera from [0, 0] at turn 2 (line 2) to [-50, 51] at turn 3, '
            'a change of 51 in 1 turns, expected at most w * 1 = 50',
        )

    def test_image_out_of_range_of_the_satellite(self) -> None:
        # At turn 9 the satellite is at [900, -135], and d = 250.
        self.assertEqual(self.score_output(b'1\n1150 -385 9 0\n'), 0)
        self.assert_invalid(
            b'1\n1151 -135 9 0\n',
            'line 2: satellite 0 needs the orientation [251, 0] at turn 9, expected each value from -250 to 250',
        )
        self.assert_invalid(
            b'1\n900 -386 9 0\n',
            'line 2: satellite 0 needs the orientation [0, -251] at turn 9, expected each value from -250 to 250',
        )

    def test_image_across_the_date_line(self) -> None:
        # At turn 1 the satellite is at [100, 647995], so -647995 is 10 to the east, across 180°.
        input_data = b'10\n1\n0 -647990 100 50 120\n1\n7 1 1\n100 -647995\n0 9\n'
        self.assertEqual(self.score_files(input_data, b'1\n100 -647995 1 0\n'), 7)
        self.assert_invalid(
            b'1\n100 -647935 1 0\n',
            'line 2: satellite 0 turns its camera from [0, 0] at turn 0 (the start) to [0, 70] at turn 1, '
            'a change of 70 in 1 turns, expected at most w * 1 = 50',
            input_data,
        )

    def test_one_image_per_satellite_per_turn(self) -> None:
        message = 'line 3: satellite 0 takes a second image at turn 2, first taken on line 2'
        self.assert_invalid(b'2\n200 -30 2 0\n210 -30 2 0\n', message)
        self.assert_invalid(b'2\n200 -30 2 0\n200 -30 2 0\n', message)

    def test_two_satellites_can_take_the_same_image_in_one_turn(self) -> None:
        input_data = b'10\n2\n0 0 100 50 120\n0 0 100 50 120\n2\n5 1 1\n200 -30\n0 9\n6 1 1\n200 -30\n2 2\n'
        self.assertEqual(self.score_files(input_data, b'2\n200 -30 2 0\n200 -30 2 1\n'), 5 + 6)

    def test_image_count_at_most_the_number_of_locations(self) -> None:
        # The collections list 3 locations, one of them twice.
        self.assertEqual(self.score_output(b'3\n100 -15 1 0\n200 -30 2 0\n300 -45 3 0\n'), 10)
        self.assert_invalid(
            b'4\n100 -15 1 0\n200 -30 2 0\n300 -45 3 0\n400 -60 4 0\n', 'line 1: found P = 4, expected 0 to 3'
        )
        self.assert_invalid(b'-1\n', 'line 1: found P = -1, expected 0 to 3')

    def test_image_count_does_not_match_the_lines_that_follow(self) -> None:
        self.assert_invalid(b'2\n200 -30 2 0\n', 'line 3: found the end of the file, expected φ, λ, t and s')
        self.assert_invalid(
            b'1\n200 -30 2 0\n500 -75 5 0\n', "line 3: found '500 -75 5 0', expected the end of the file"
        )

    def test_values_out_of_range(self) -> None:
        cases = [
            (b'1\n306001 0 1 0\n', 'line 2: found φ = 306001, expected -306000 to 306000'),
            (b'1\n-306001 0 1 0\n', 'line 2: found φ = -306001, expected -306000 to 306000'),
            (b'1\n0 648000 1 0\n', 'line 2: found λ = 648000, expected -648000 to 647999'),
            (b'1\n0 -648001 1 0\n', 'line 2: found λ = -648001, expected -648000 to 647999'),
            (b'1\n0 0 10 0\n', 'line 2: found t = 10, expected 0 to 9'),
            (b'1\n0 0 -1 0\n', 'line 2: found t = -1, expected 0 to 9'),
            (b'1\n0 0 0 1\n', 'line 2: found s = 1, expected 0 to 0'),
            (b'1\n0 0 0 -1\n', 'line 2: found s = -1, expected 0 to 0'),
        ]
        for output, message in cases:
            with self.subTest(output=output):
                self.assert_invalid(output, message)

    def test_wrong_number_of_values(self) -> None:
        self.assert_invalid(b'1\n200 -30 2\n', 'line 2: found 3 values, expected 4: φ, λ, t and s')
        self.assert_invalid(b'1\n200 -30 2 0 0\n', 'line 2: found 5 values, expected 4: φ, λ, t and s')
        self.assert_invalid(b'1 2\n', 'line 1: found 2 values, expected 1: P')

    def test_blank_line_before_an_image(self) -> None:
        self.assert_invalid(b'1\n\n200 -30 2 0\n', 'line 2: found an empty line, expected φ, λ, t and s')

    def test_any_whitespace_and_blank_lines_at_the_end(self) -> None:
        self.assertEqual(self.score_output(b' 2\t\r\n200  -30 2 0 \r\n500 -75\t5 0\r\n\r\n  \n'), 30)

    def test_missing_newline_at_the_end(self) -> None:
        self.assertEqual(self.score_output(b'1\n200 -30 2 0'), 10)

    def test_empty_file(self) -> None:
        self.assert_invalid(b'', 'line 1: found the end of the file, expected P')

    def test_integers_are_parsed_strictly(self) -> None:
        for token in ['+2', '2.0', '0x2', '1_0', 'two']:
            with self.subTest(token=token):
                self.assert_invalid(
                    f'1\n200 -30 {token} 0\n'.encode(), f'line 2: found {token!r}, expected an integer'
                )

    def test_very_long_integer(self) -> None:
        self.assert_invalid(
            b'1\n200 -30 ' + b'1' * 5000 + b' 0\n', 'line 2: found an integer of 5000 characters, which is too long'
        )

    def test_non_ascii_output(self) -> None:
        self.assert_invalid(b'1\n200 -30 2 0\n\xc3\xa9\n', 'line 3: found the byte 0xc3, expected ASCII text')

    def test_invalid_input(self) -> None:
        cases = [
            b'10\n1\n0 0 100 50 120\n1\n10 1 2\n200 -30\n2 4\n4 6\n',  # the ranges overlap at turn 4
            b'10\n1\n0 0 100 50 120\n1\n10 1 1\n200 -30\n2 10\n',  # t_end = T
            b'10\n1\n0 0 99 50 120\n0\n',  # |v| < 100
            b'10\n1\n0 0 100 50 120\n1\n10 1 1\n306001 -30\n2 4\n',  # a location above 85°
            b'10\n1\n0 0 100 50 120\n1\n10 0 1\n2 4\n',  # L = 0
            b'10\n1\n0 0 100 50 120\n0\n0\n',  # a line after the last collection
        ]
        for input_data in cases:
            with self.subTest(input_data=input_data):
                self.assert_invalid_input(input_data)

