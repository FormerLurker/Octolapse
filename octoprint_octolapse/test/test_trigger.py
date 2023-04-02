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

import octoprint_octolapse.trigger as trigger
from octoprint_octolapse.settings import OctolapseSettings


class TestTrigger(unittest.TestCase):
    def setUp(self):
        self.Settings = OctolapseSettings(NamedTemporaryFile().name)
        self.PrinterTolerance = 0.0
    def tearDown(self):
        del self.Settings

    def test_is_in_position_Rect_Forbidden(self):
        restrictions_dict = [
            {"Shape": "rect", "X": 10.0, "Y": 10.0, "X2": 20.0, "Y2": 20.0, "Type": "forbidden", "R": 1.0}]
        restrictions = self.Settings.profiles.current_snapshot().get_trigger_position_restrictions(restrictions_dict)
        self.assertTrue(trigger.is_in_position(restrictions, 0, 0, self.PrinterTolerance))
        self.assertTrue(trigger.is_in_position(restrictions, 100, 0, self.PrinterTolerance))
        self.assertTrue(trigger.is_in_position(restrictions, 20.1, 20.1, self.PrinterTolerance))
        self.assertTrue(trigger.is_in_position(restrictions, 15, 25, self.PrinterTolerance))
        self.assertTrue(trigger.is_in_position(restrictions, 25, 15, self.PrinterTolerance))

        self.assertFalse(trigger.is_in_position(restrictions, 10, 10, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 15, 15, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 20, 20, self.PrinterTolerance))

    def test_is_in_position_Rect_Required(self):
        restrictions_dict = [
            {"Shape": "rect", "X": 10.0, "Y": 10.0, "X2": 20.0, "Y2": 20.0, "Type": "required", "R": 1.0}]
        restrictions = self.Settings.profiles.current_snapshot().get_trigger_position_restrictions(restrictions_dict)
        self.assertFalse(trigger.is_in_position(restrictions, 0, 0, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 100, 0, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 20.1, 20.1, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 15, 25, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 25, 15, self.PrinterTolerance))

        self.assertTrue(trigger.is_in_position(restrictions, 10, 10, self.PrinterTolerance))
        self.assertTrue(trigger.is_in_position(restrictions, 15, 15, self.PrinterTolerance))
        self.assertTrue(trigger.is_in_position(restrictions, 20, 20, self.PrinterTolerance))

    def test_is_in_position_Rect_ForbiddenAndRequired(self):
        # test to restrictions, forbidden and required, have them overlap.
        restrictions_dict = [
            {"Shape": "rect", "X": 10.0, "Y": 10.0, "X2": 20.0, "Y2": 20.0, "Type": "required", "R": 1.0},
            {"Shape": "rect", "X": 15.0, "Y": 15.0, "X2": 25.0, "Y2": 25.0, "Type": "forbidden", "R": 1.0},
        ]
        restrictions = self.Settings.profiles.current_snapshot().get_trigger_position_restrictions(restrictions_dict)
        # out of all areas, restricted and forbidden
        self.assertFalse(trigger.is_in_position(restrictions, 0, 0, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 100, 0, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 12.5, 25, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 25, 12.5, self.PrinterTolerance))

        # test only in forbidden area
        self.assertFalse(trigger.is_in_position(restrictions, 20.1, 25, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 20.1, 20.1, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 25, 20.1, self.PrinterTolerance))

        # test in required area only
        self.assertTrue(trigger.is_in_position(restrictions, 10, 10, self.PrinterTolerance))
        self.assertTrue(trigger.is_in_position(restrictions, 12.5, 12.5, self.PrinterTolerance))
        self.assertTrue(trigger.is_in_position(restrictions, 14.99, 14.99, self.PrinterTolerance))

        # test overlapping area
        self.assertFalse(trigger.is_in_position(restrictions, 15, 15, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 20, 20, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 15, 20, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 20, 15, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 17.5, 17.5, self.PrinterTolerance))

    def test_is_in_position_Circle_Forbidden(self):
        restrictions_dict = [{"Shape": "circle", "R": 1.0, "Y": 10.0, "X": 10.0, "Type": "forbidden", "X2": 0, "Y2": 0}]
        restrictions = self.Settings.profiles.current_snapshot().get_trigger_position_restrictions(restrictions_dict)
        # tests outside forbidden area
        self.assertTrue(trigger.is_in_position(restrictions, 0, 0, self.PrinterTolerance))
        self.assertTrue(trigger.is_in_position(restrictions, 100, 0, self.PrinterTolerance))
        self.assertTrue(trigger.is_in_position(restrictions, 9, 9, self.PrinterTolerance))
        self.assertTrue(trigger.is_in_position(restrictions, 11, 11, self.PrinterTolerance))
        self.assertTrue(trigger.is_in_position(restrictions, 9, 11, self.PrinterTolerance))
        self.assertTrue(trigger.is_in_position(restrictions, 11, 9, self.PrinterTolerance))
        # tests inside forbidden area
        self.assertFalse(trigger.is_in_position(restrictions, 10, 10, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 10, 9, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 9, 10, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 10, 11, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 11, 10, self.PrinterTolerance))

    def test_is_in_position_Circle_Required(self):
        restrictions_dict = [
            {"Shape": "circle", "R": 1.0, "Y": 10.0, "X": 10.0, "Type": "required", "X2": 20.0, "Y2": 20.0}]
        restrictions = self.Settings.profiles.current_snapshot().get_trigger_position_restrictions(restrictions_dict)
        # tests outside area
        self.assertFalse(trigger.is_in_position(restrictions, 0, 0, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 100, 0, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 9, 9, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 11, 11, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 9, 11, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 11, 9, self.PrinterTolerance))

        # tests inside area
        self.assertTrue(trigger.is_in_position(restrictions, 10, 10, self.PrinterTolerance))
        self.assertTrue(trigger.is_in_position(restrictions, 10, 9, self.PrinterTolerance))
        self.assertTrue(trigger.is_in_position(restrictions, 9, 10, self.PrinterTolerance))
        self.assertTrue(trigger.is_in_position(restrictions, 10, 11, self.PrinterTolerance))
        self.assertTrue(trigger.is_in_position(restrictions, 11, 10, self.PrinterTolerance))

    def test_is_in_position_Circle_ForbiddenAndRequired(self):
        # test to restrictions, forbidden and required, have them overlap.
        restrictions_dict = [
            {"Shape": "circle", "R": 1.0, "Y": 10.0, "X": 10.0, "Type": "required", "X2": 20.0, "Y2": 20.0},
            {"Shape": "circle", "R": 1.0, "Y": 10.0, "X": 11.0, "Type": "forbidden", "X2": 25.0, "Y2": 25.0},
        ]
        restrictions = self.Settings.profiles.current_snapshot().get_trigger_position_restrictions(restrictions_dict)
        # out of all areas, restricted and forbidden
        self.assertFalse(trigger.is_in_position(restrictions, 0, 0, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 100, 0, self.PrinterTolerance))

        # test only in forbidden area
        self.assertFalse(trigger.is_in_position(restrictions, 12, 10, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 11, 11, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 11, 9, self.PrinterTolerance))

        # test in required area only
        self.assertTrue(trigger.is_in_position(restrictions, 10, 11, self.PrinterTolerance))
        self.assertTrue(trigger.is_in_position(restrictions, 10, 9, self.PrinterTolerance))
        self.assertTrue(trigger.is_in_position(restrictions, 9, 10, self.PrinterTolerance))

        # test overlapping area
        self.assertFalse(trigger.is_in_position(restrictions, 10, 10, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 11, 10, self.PrinterTolerance))
        self.assertFalse(trigger.is_in_position(restrictions, 10.5, 10, self.PrinterTolerance))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTrigger)
    unittest.TextTestRunner(verbosity=3).run(suite)
