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
from octoprint_octolapse._version import get_versions
import octoprint_octolapse.utility as utility
from octoprint_octolapse_setuptools import NumberedVersion


class TestUtility(unittest.TestCase):
    def test_setbitrate(self):
        """test the setbitrate function"""
        self.assertTrue(utility.get_bitrate("800k", None) is not None)
        self.assertTrue(utility.get_bitrate("800K", None) is not None)
        self.assertTrue(utility.get_bitrate("8M", None) is not None)
        self.assertTrue(utility.get_bitrate("8m", None) is not None)
        self.assertTrue(utility.get_bitrate(" 800k", None) is None)
        self.assertTrue(utility.get_bitrate("800k ", None) is None)
        self.assertTrue(utility.get_bitrate(" 800k ", None) is None)
        self.assertTrue(utility.get_bitrate("800", None) is None)
        self.assertTrue(utility.get_bitrate("", None) is None)

    def test_IsInBounds(self):
        """Test the IsInBounds function to make sure the program will not attempt to operate after being told to move
        out of bounds. """

        bounding_box = {
            "min_x": 0,
            "max_x": 250,
            "min_y": 0,
            "max_y": 200,
            "min_z": 0,
            "max_z": 200
        }

        # Initial test, should return false without any coordinates
        self.assertFalse(utility.is_in_bounds(
            bounding_box, None, None, None), "")

        # test the origin (min), should return true
        self.assertTrue(utility.is_in_bounds(bounding_box, 0, 0, 0))

        # move X out of bounds of the min
        self.assertFalse(utility.is_in_bounds(bounding_box, -0.0001, 0, 0))
        # move X out of bounds of the max
        self.assertFalse(utility.is_in_bounds(bounding_box, 250.0001, 0, 0))
        # move X to the max of bounds of the max
        self.assertTrue(utility.is_in_bounds(bounding_box, 250.0000, 0, 0))

        # move Y out of bounds of the min
        self.assertFalse(utility.is_in_bounds(bounding_box, 0, -0.0001, 0))
        # move Y out of bounds of the max
        self.assertFalse(utility.is_in_bounds(bounding_box, 0, 200.0001, 0))
        # move Y to the max of bounds of the max
        self.assertTrue(utility.is_in_bounds(bounding_box, 0, 200.0000, 0))

        # move Z out of bounds of the min
        self.assertFalse(utility.is_in_bounds(bounding_box, 0, 0, -0.0001))
        # move Z out of bounds of the max
        self.assertFalse(utility.is_in_bounds(bounding_box, 0, 0, 200.0001))
        # move Z to the max of bounds of the max
        self.assertTrue(utility.is_in_bounds(bounding_box, 0, 0, 200.0000))

    def test_IsInBounds_CustomBox(self):
        """Test the IsInBounds function to make sure the program will not attempt to operate after being told to move
        out of bounds. """
        # test custom box with values above zero
        bounding_box = {
            "min_x": 1,
            "max_x": 200,
            "min_y": 1,
            "max_y": 200,
            "min_z": 1,
            "max_z": 200
        }

        # Initial test, should return false without any coordinates
        self.assertFalse(utility.is_in_bounds(bounding_box, None, None, None))

        # test the origin (min), should return false
        self.assertFalse(utility.is_in_bounds(bounding_box, 0, 0, 0))

        # test 1,1,1 - True
        self.assertTrue(utility.is_in_bounds(bounding_box, 1, 1, 1))

        # move X out of bounds - Min
        self.assertFalse(utility.is_in_bounds(bounding_box, .9999, 1, 1))
        # move X out of bounds - Max
        self.assertFalse(utility.is_in_bounds(bounding_box, 200.0001, 1, 1))
        # move X in bounds - Max
        self.assertTrue(utility.is_in_bounds(bounding_box, 200.0000, 1, 1))
        # move X in bounds - Middle
        self.assertTrue(utility.is_in_bounds(bounding_box, 100.5000, 1, 1))

        # move Y out of bounds - Min
        self.assertFalse(utility.is_in_bounds(bounding_box, 1, .9999, 1))
        # move Y out of bounds - Max
        self.assertFalse(utility.is_in_bounds(bounding_box, 1, 200.0001, 1))
        # move Y in bounds - Max
        self.assertTrue(utility.is_in_bounds(bounding_box, 1, 200.0000, 1))
        # move Y in bounds - Middle
        self.assertTrue(utility.is_in_bounds(bounding_box, 1, 100.5000, 1))

        # move Z out of bounds - Min
        self.assertFalse(utility.is_in_bounds(bounding_box, 1, 1, .9999))
        # move Z out of bounds - Max
        self.assertFalse(utility.is_in_bounds(bounding_box, 1, 1, 200.0001))
        # move Z in bounds - Max
        self.assertTrue(utility.is_in_bounds(bounding_box, 1, 1, 200.0000))
        # move Z in bounds - Middle
        self.assertTrue(utility.is_in_bounds(bounding_box, 1, 1, 100.5000))

    def test_IsInBounds_NegativeMin(self):
        # test custom box with negative min values
        bounding_box = {
            "min_x": -1,
            "max_x": 250,
            "min_y": -2,
            "max_y": 200,
            "min_z": -3,
            "max_z": 200
        }

        # move X out of bounds - Min
        self.assertFalse(utility.is_in_bounds(bounding_box, -1.0001, 1, 1))
        # move X out of bounds - Max
        self.assertFalse(utility.is_in_bounds(bounding_box, 250.0001, 1, 1))
        # move X in bounds - Max
        self.assertTrue(utility.is_in_bounds(bounding_box, 250.0000, 1, 1))
        # move X in bounds - Middle
        self.assertTrue(utility.is_in_bounds(bounding_box, 123.5000, 1, 1))

        # move Y out of bounds - Min
        self.assertFalse(utility.is_in_bounds(bounding_box, 1, -2.0001, 1))
        # move Y out of bounds - Max
        self.assertFalse(utility.is_in_bounds(bounding_box, 1, 200.0001, 1))
        # move Y in bounds - Max
        self.assertTrue(utility.is_in_bounds(bounding_box, 1, 200.0000, 1))
        # move Y in bounds - Middle
        self.assertTrue(utility.is_in_bounds(bounding_box, 1, 99.0000, 1))

        # move Z out of bounds - Min
        self.assertFalse(utility.is_in_bounds(bounding_box, 1, 1, -3.0001))
        # move Z out of bounds - Max
        self.assertFalse(utility.is_in_bounds(bounding_box, 1, 1, 200.0001))
        # move Z in bounds - Max
        self.assertTrue(utility.is_in_bounds(bounding_box, 1, 1, 200.0000))
        # move Z in bounds - Middle
        self.assertTrue(utility.is_in_bounds(bounding_box, 1, 1, 98.5000))

    def test_IsInBounds_AllNegativeMin(self):
        # test custom box with all negative min values
        bounding_box = {
            "min_x": -100,
            "max_x": -50,
            "min_y": -100,
            "max_y": -50,
            "min_z": -100,
            "max_z": -50
        }

        # test X axis
        # move out of bounds - Min
        self.assertFalse(utility.is_in_bounds(
            bounding_box, -100.0001, -100, -100))
        # move out of bounds - Max
        self.assertFalse(utility.is_in_bounds(
            bounding_box, -49.9999, -100, -100))
        # move in bounds - Max
        self.assertTrue(utility.is_in_bounds(bounding_box, -50.0000, -100, -100))
        # move in bounds - Middle
        self.assertTrue(utility.is_in_bounds(bounding_box, -75.0000, -100, -100))

        # test Y axis
        # move out of bounds - Min
        self.assertFalse(utility.is_in_bounds(
            bounding_box, -100, -100.0001, -100))
        # move out of bounds - Max
        self.assertFalse(utility.is_in_bounds(
            bounding_box, -100, -49.9999, -100))
        # move in bounds - Max
        self.assertTrue(utility.is_in_bounds(bounding_box, -100, -50.0000, -100))
        # move in bounds - Middle
        self.assertTrue(utility.is_in_bounds(bounding_box, -100, -75.0000, -100))

        # test Z axis
        # move out of bounds - Min
        self.assertFalse(utility.is_in_bounds(
            bounding_box, -100, -100, -100.0001))
        # move out of bounds - Max
        self.assertFalse(utility.is_in_bounds(
            bounding_box, -100, -100, -49.9999))
        # move in bounds - Max
        self.assertTrue(utility.is_in_bounds(bounding_box, -100, -100, -50.0000))
        # move in bounds - Middle
        self.assertTrue(utility.is_in_bounds(bounding_box, -100, -100, -75.0000))

    def test_GetClosestInBoundsPosition(self):
        bounding_box = {
            "min_x": 0,
            "max_x": 250,
            "min_y": 0,
            "max_y": 200,
            "min_z": 0,
            "max_z": 200
        }
        self.assertEqual(utility.get_closest_in_bounds_position(bounding_box, None, None, None),
                         {'X': None, 'Y': None, 'Z': None},
                         "Coordinates = 'None' should no closest position.")

        self.assertEqual(utility.get_closest_in_bounds_position(bounding_box, 175, 100, 100),
                         {'X': 175, 'Y': 100, 'Z': 100},
                         "Center is not in bounds.")

        self.assertEqual(utility.get_closest_in_bounds_position(bounding_box, 0, 0, 0), {'X': 0, 'Y': 0, 'Z': 0},
                         "Origin is not in bounds.")
        self.assertEqual(utility.get_closest_in_bounds_position(bounding_box, 250, 200, 200),
                         {'X': 250, 'Y': 200, 'Z': 200},
                         "Max is not in bounds.")

        self.assertEqual(utility.get_closest_in_bounds_position(bounding_box, -1, 0, 0), {'X': 0, 'Y': 0, 'Z': 0},
                         "-X axis failed.")
        self.assertEqual(utility.get_closest_in_bounds_position(bounding_box, 250.5, 0, 0), {'X': 250, 'Y': 0, 'Z': 0},
                         "+X axis failed.")
        self.assertEqual(utility.get_closest_in_bounds_position(bounding_box, 0, -1, 0), {'X': 0, 'Y': 0, 'Z': 0},
                         "-Y axis failed.")
        self.assertEqual(utility.get_closest_in_bounds_position(bounding_box, 0, 201, 0), {'X': 0, 'Y': 200, 'Z': 0},
                         "+Y axis failed.")
        self.assertEqual(utility.get_closest_in_bounds_position(bounding_box, 0, 0, -1), {'X': 0, 'Y': 0, 'Z': 0},
                         "-Z axis failed.")
        self.assertEqual(utility.get_closest_in_bounds_position(bounding_box, 0, 0, 200), {'X': 0, 'Y': 0, 'Z': 200},
                         "-Z axis failed.")

    def test_isclose(self):
        self.assertTrue(utility.is_close(113.33847, 113.34, 0.005))
        self.assertTrue(utility.is_close(119.9145519, 119.91, 0.005))

    def test_numbered_version(self):
        fallback_version = NumberedVersion.clean_version("0.4.0rc3")
        plugin_version = NumberedVersion.clean_version(get_versions()['version'])
        #if plugin_version == "0+unknown" or NumberedVersion(plugin_version) < NumberedVersion(fallback_version):
        if plugin_version == "0+unknown":
            plugin_version = fallback_version
            try:
                # This generates version in the following form:
                #   0.4.0rc1+?.GUID_GOES_HERE
                plugin_version += "+u." + versioneer.get_versions()['full-revisionid'][0:7]
            except:
                pass
        self.assertEqual(plugin_version, fallback_version)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUtility)
    unittest.TextTestRunner(verbosity=3).run(suite)
