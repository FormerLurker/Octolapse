# coding=utf-8
##################################################################################
# Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
# Copyright (C) 2023  Brad Hochgesang
##################################################################################
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see the following:
# https://github.com/FormerLurker/Octolapse/blob/master/LICENSE
#
# You can contact the author either through the git-hub repository, or at the
# following email address: FormerLurker@pm.me
##################################################################################

import unittest
from tempfile import NamedTemporaryFile
from octoprint_octolapse.settings import OctolapseSettings
import octoprint_octolapse.utility as utility


class TestTrigger(unittest.TestCase):
    def setUp(self):
        self.Settings = OctolapseSettings(NamedTemporaryFile().name)

    def tearDown(self):
        del self.Settings

    def test_intersections_circle(self):
        tests = [
            {
                'name': "intersects_1",
                'p1': [-15, 0],
                'p2': [15, 0],
                'circle': [0, 0, 5],
                'assert': [[-5, 0], [5, 0]]
            },
            {
                'name': "tangent_1",
                'p1': [-15, 5.0],
                'p2': [15, 5.0],
                'circle': [0, 0, 5],
                'assert': [[0, 5]]
            },
            {
                'name': "all_inside",
                'p1': [-1, 0],
                'p2': [1, 0],
                'circle': [0, 0, 5],
                'assert': False
            },
            {
                'name': "partially_inside",
                'p1': [-6, 0],
                'p2': [0, 0],
                'circle': [0, 0, 5],
                'assert': [[-5, 0]]
            }
        ]
        for test in tests:
            intersections = utility.get_intersections_circle(
                test["p1"][0], test["p1"][1], test["p2"][0], test["p2"][1],
                test["circle"][0], test["circle"][1], test["circle"][2]
            )
            if test["assert"] and intersections:
                self.assertTrue(
                    all(elem in intersections for elem in test["assert"]) and
                    all(elem in test["assert"] for elem in intersections),
                    "Failed test_intersections_rectangle:  TestName: {0}".format(test["name"])
                )
            else:
                self.assertEqual(
                    test["assert"],
                    intersections,
                    "Failed test test_intersections_rectangle:  TestName: {0}".format(test["name"])
                )

    def test_intersections_rectangle(self):
        tests = [
            {
                'name': "intersects_1",
                'p1': [8, 10],
                'p2': [15, 3],
                'rect1': [10, 5],
                'rect2': [15, 10],
                'assert': [[10.0, 8.0], [13.0, 5.0]]
            },
            {
                'name': "intersects_2",
                'p1': [15, 3],
                'p2': [8, 10],
                'rect1': [10, 5],
                'rect2': [15, 10],
                'assert': [[10.0, 8.0], [13.0, 5.0]]
            },
            {
                'name': "intersects_3",
                'p1': [8, 10],
                'p2': [15, 3],
                'rect1': [15, 10],
                'rect2': [10, 5],
                'assert': [[13.0, 5.0], [10.0, 8.0]]
            },
            {
                'name': "intersects_4",
                'p1': [15, 3],
                'p2': [8, 10],
                'rect1': [15, 10],
                'rect2': [10, 5],
                'assert': [[10.0, 8.0], [13.0, 5.0]]
            },
            {
                'name': "parallel_1",
                'p1': [17, 10],
                'p2': [17, 5],
                'rect1': [15, 10],
                'rect2': [10, 5],
                'assert': False
            },
            {
                'name': "parallel_2",
                'p1': [17, 5],
                'p2': [17, 10],
                'rect1': [15, 10],
                'rect2': [10, 5],
                'assert': False
            },
            {
                'name': "parallel_3",
                'p1': [10, 2],
                'p2': [15, 2],
                'rect1': [15, 10],
                'rect2': [10, 5],
                'assert': False
            },
            {
                'name': "parallel_3",
                'p1': [10, 11],
                'p2': [15, 11],
                'rect1': [15, 10],
                'rect2': [10, 5],
                'assert': False
            },
            {
                'name': "left_edge_1",
                'p1': [10, 10],
                'p2': [10, 5],
                'rect1': [15, 10],
                'rect2': [10, 5],
                'assert': [[10.0, 10.0], [10.0, 5.0]]
            },
            {
                'name': "right_edge_1",
                'p1': [15, 10],
                'p2': [15, 5],
                'rect1': [15, 10],
                'rect2': [10, 5],
                'assert': [[15.0, 10.0], [15.0, 5.0]]
            },
            {
                'name': "top_edge_1",
                'p1': [10, 10],
                'p2': [15, 10],
                'rect1': [15, 10],
                'rect2': [10, 5],
                'assert': [[10.0, 10.0], [15.0, 10.0]]
            },
            {
                'name': "bottom_edge_1",
                'p1': [10, 5],
                'p2': [15, 5],
                'rect1': [15, 10],
                'rect2': [10, 5],
                'assert': [[10.0, 5.0], [15.0, 5.0]]
            },
            {
                'name': "left_edge_extends_1",
                'p1': [10, 11],
                'p2': [10, 4],
                'rect1': [15, 10],
                'rect2': [10, 5],
                'assert': [[10.0, 10.0], [10.0, 5.0]]
            },
            {
                'name': "right_edge_extends_1",
                'p1': [15, 4],
                'p2': [15, 11],
                'rect1': [15, 10],
                'rect2': [10, 5],
                'assert': [[15.0, 10.0], [15.0, 5.0]]
            },
            {
                'name': "top_edge_extends_1",
                'p1': [9, 10],
                'p2': [16, 10],
                'rect1': [15, 10],
                'rect2': [10, 5],
                'assert': [[10.0, 10.0], [15.0, 10.0]]
            },
            {
                'name': "bottom_edge_extends_1",
                'p1': [9, 5],
                'p2': [16, 5],
                'rect1': [15, 10],
                'rect2': [10, 5],
                'assert': [[10.0, 5.0], [15.0, 5.0]]
            },
            {
                'name': "does_not_intersect_1",
                'p1': [7, 6],
                'p2': [10, 3],
                'rect1': [10, 10],
                'rect2': [15, 5],
                'assert': False
            },
            {
                'name': "does_not_intersect_2",
                'p1': [10, 3],
                'p2': [7, 6],
                'rect1': [10, 10],
                'rect2': [15, 5],
                'assert': False
            },
            {
                'name': "does_not_intersect_3",
                'p1': [7, 6],
                'p2': [10, 3],
                'rect1': [15, 5],
                'rect2': [10, 10],
                'assert': False
            },
            {
                'name': "fully_inside_1",
                'p1': [13, 7],
                'p2': [12, 7],
                'rect1': [15, 5],
                'rect2': [10, 10],
                'assert': False
            },
            {
                'name': "partly_inside_1",
                'p1': [8, 7],
                'p2': [12, 7],
                'rect1': [15, 5],
                'rect2': [10, 10],
                'assert': [[10, 7]]
            },
            {
                'name': "does_not_intersect_4",
                'p1': [10, 3],
                'p2': [7, 6],
                'rect1': [15, 5],
                'rect2': [10, 10],
                'assert': False
            }
        ]

        for test in tests:
            intersections = utility.get_intersections_rectangle(
                test["p1"][0], test["p1"][1], test["p2"][0], test["p2"][1],
                test["rect1"][0], test["rect1"][1], test["rect2"][0], test["rect2"][1]
            )
            if test["assert"] and intersections:
                self.assertTrue(
                    all(elem in intersections for elem in test["assert"]) and
                    all(elem in test["assert"] for elem in intersections),
                    "Failed test_intersections_rectangle:  TestName: {0}".format(test["name"])
                )
            else:
                self.assertEqual(
                    test["assert"],
                    intersections,
                    "Failed test test_intersections_rectangle:  TestName: {0}".format(test["name"])
                )

    # def test_get_restriction_intersection_point(self):
    #    restrictions_dict = [
    #        {
    #            "Shape": "rect",
    #            "X": 10.0,
    #            "Y": 10.0,
    #            "X2": 20.0,
    #            "Y2": 20.0,
    #            "Type": "forbidden",
    #            "R": 1.0,
    #            "CalculateIntersections": False
    #        }
    #    ]
    #
    #    restrictions = self.Settings.profiles.current_snapshot().get_trigger_position_restrictions(restrictions_dict)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTrigger)
    unittest.TextTestRunner(verbosity=3).run(suite)
