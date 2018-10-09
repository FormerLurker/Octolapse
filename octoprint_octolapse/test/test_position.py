# coding=utf-8
##################################################################################
# Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
# Copyright (C) 2017  Brad Hochgesang
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
from octoprint_octolapse.gcode_parser import Commands
from octoprint_octolapse.position import Pos
from octoprint_octolapse.position import Position
from octoprint_octolapse.settings import OctolapseSettings


class TestPosition(unittest.TestCase):
    def setUp(self):
        self.Commands = Commands()
        self.Settings = OctolapseSettings(NamedTemporaryFile().name)
        self.Settings.printers[self.Settings.DefaultPrinter.guid] = self.Settings.DefaultPrinter
        self.Settings.current_printer_profile_guid = self.Settings.DefaultPrinter.guid
        # in the general test case we want auto_detect_position to be false
        # else we'll have to simulate a position update (m114 return) after
        # a home (g28) command
        self.Settings.current_printer().auto_detect_position = False
        # since we've set auto_detect_position to false, we need to set
        # an origin, else X,Y and Z will still be None after a home command
        self.Settings.current_printer().origin_x = 0
        self.Settings.current_printer().origin_y = 0
        self.Settings.current_printer().origin_z = 0

        self.OctoprintPrinterProfile = self.create_octolapse_printer_profile()

    def tearDown(self):
        del self.Commands
        del self.Settings

    @staticmethod
    def create_octolapse_printer_profile():
        return {
            "volume": {
                "custom_box": False,
                "width": 250,
                "depth": 200,
                "height": 200
            }
        }

    def test_PositionError(self):
        """Test the IsInBounds function to make sure the program will not attempt to operate after being told to move
        out of bounds. """
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)

        # Initial test, should return false without any coordinates
        self.assertFalse(position.has_position_error())
        self.assertIsNone(position.position_error())
        # home the axis and test
        position.update(Commands.parse("G28"))
        self.assertFalse(position.has_position_error())
        self.assertIsNone(position.position_error())

        # X axis tests
        # reset, set relative extruder and absolute xyz, home the axis and test again
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        position.update(Commands.parse("M83"))
        position.update(Commands.parse("G90"))
        position.update(Commands.parse("G28"))
        self.assertFalse(position.has_position_error())
        self.assertIsNone(position.position_error())
        # move out of bounds min
        position.update(Commands.parse("G0 x-0.0001"))
        self.assertTrue(position.has_position_error())
        self.assertTrue(position.position_error() is not None)
        # move back in bounds
        position.update(Commands.parse("G0 x0.0"))
        self.assertFalse(position.has_position_error())
        self.assertIsNone(position.position_error())
        # move to middle
        position.update(Commands.parse("G0 x125"))
        self.assertFalse(position.has_position_error())
        self.assertIsNone(position.position_error())
        # move to max
        position.update(Commands.parse("G0 x250"))
        self.assertFalse(position.has_position_error())
        self.assertIsNone(position.position_error())
        # move out of bounds max
        position.update(Commands.parse("G0 x250.0001"))
        self.assertTrue(position.has_position_error())
        self.assertTrue(position.position_error() is not None)

        # Y axis tests
        # reset, set relative extruder and absolute xyz, home the axis and test again
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        position.update(Commands.parse("M83"))
        position.update(Commands.parse("G90"))
        position.update(Commands.parse("G28"))
        self.assertFalse(position.has_position_error())
        self.assertIsNone(position.position_error())
        # move out of bounds min
        position.update(Commands.parse("G0 y-0.0001"))
        self.assertTrue(position.has_position_error())
        self.assertTrue(position.position_error() is not None)
        # move back in bounds
        position.update(Commands.parse("G0 y0.0"))
        self.assertFalse(position.has_position_error())
        self.assertIsNone(position.position_error())
        # move to middle
        position.update(Commands.parse("G0 y100"))
        self.assertFalse(position.has_position_error())
        self.assertIsNone(position.position_error())
        # move to max
        position.update(Commands.parse("G0 y200"))
        self.assertFalse(position.has_position_error())
        self.assertIsNone(position.position_error())
        # move out of bounds max
        position.update(Commands.parse("G0 y200.0001"))
        self.assertTrue(position.has_position_error())
        self.assertTrue(position.position_error() is not None)

        # Z axis tests
        # reset, home the axis and test again
        # reset, set relative extruder and absolute xyz, home the axis and test again
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        position.update(Commands.parse("M83"))
        position.update(Commands.parse("G90"))
        position.update(Commands.parse("G28"))
        self.assertFalse(position.has_position_error())
        self.assertIsNone(position.position_error())
        # move out of bounds min
        position.update(Commands.parse("G0 z-0.0001"))
        self.assertTrue(position.has_position_error())
        self.assertTrue(position.position_error() is not None)
        # move back in bounds
        position.update(Commands.parse("G0 z0.0"))
        self.assertFalse(position.has_position_error())
        self.assertIsNone(position.position_error())
        # move to middle
        position.update(Commands.parse("G0 z100"))
        self.assertFalse(position.has_position_error())
        self.assertIsNone(position.position_error())
        # move to max
        position.update(Commands.parse("G0 z200"))
        self.assertFalse(position.has_position_error())
        self.assertIsNone(position.position_error())
        # move out of bounds max
        position.update(Commands.parse("G0 z200.0001"))
        self.assertTrue(position.has_position_error())
        self.assertTrue(position.position_error() is not None)

    def test_reset(self):
        """Test init state."""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        # reset all initialized vars to something else
        position.update(Commands.parse("G28"))
        position.update(Commands.parse("G0 X1 Y1 Z1"))

        # reset
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)

        # test initial state
        self.assertEqual(len(position.Positions), 0)
        self.assertIsNone(position.SavedPosition)

    def test_Home(self):
        """Test the home command.  Make sure the position is set to 0,0,0 after the home."""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)

        position.update(Commands.parse("G28"))
        self.assertEqual(position.x(), 0)
        self.assertTrue(position.get_position().XHomed)
        self.assertEqual(position.y(), 0)
        self.assertTrue(position.get_position().YHomed)
        self.assertEqual(position.z(), 0)
        self.assertTrue(position.get_position().ZHomed)
        self.assertTrue(position.has_homed_axes())
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        position.update(Commands.parse("G28 X"))
        self.assertEqual(position.x(), 0)
        self.assertTrue(position.get_position().XHomed)
        self.assertIsNone(position.y())
        self.assertFalse(position.get_position().YHomed)
        self.assertIsNone(position.z())
        self.assertFalse(position.get_position().ZHomed)
        self.assertFalse(position.has_homed_axes())

        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        position.update(Commands.parse("G28 Y"))
        self.assertIsNone(position.x())
        self.assertFalse(position.get_position().XHomed)
        self.assertEqual(position.y(), 0)
        self.assertTrue(position.get_position().YHomed)
        self.assertIsNone(position.z())
        self.assertFalse(position.get_position().ZHomed)
        self.assertFalse(position.has_homed_axes())

        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        position.update(Commands.parse("G28 Z"))
        self.assertIsNone(position.x())
        self.assertFalse(position.get_position().XHomed)
        self.assertIsNone(position.y())
        self.assertFalse(position.get_position().YHomed)
        self.assertEqual(position.z(), 0)
        self.assertTrue(position.get_position().ZHomed)
        self.assertFalse(position.has_homed_axes())

        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        position.update(Commands.parse("G28 Z X Y"))
        self.assertEqual(position.x(), 0)
        self.assertTrue(position.get_position().XHomed)
        self.assertEqual(position.y(), 0)
        self.assertTrue(position.get_position().YHomed)
        self.assertEqual(position.z(), 0)
        self.assertTrue(position.get_position().ZHomed)
        self.assertTrue(position.has_homed_axes())

        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        position.update(Commands.parse("g28"))
        position.update(Commands.parse("g1 x0 y0 z0"))
        # here we have seen the upded coordinates, but we do not know the position
        self.assertEqual(position.x(), 0)
        self.assertTrue(position.get_position().XHomed)
        self.assertEqual(position.y(), 0)
        self.assertTrue(position.get_position().YHomed)
        self.assertEqual(position.z(), 0)
        self.assertTrue(position.get_position().ZHomed)
        # give it another position, now we have homed axis with a known position
        position.update(Commands.parse("g1 x0 y0 z0"))
        self.assertEqual(position.x(), 0)
        self.assertTrue(position.get_position().XHomed)
        self.assertEqual(position.y(), 0)
        self.assertTrue(position.get_position().YHomed)
        self.assertEqual(position.z(), 0)
        self.assertTrue(position.get_position().ZHomed)
        self.assertTrue(position.has_homed_axes())

    def test_UpdatePosition_force(self):
        """Test the UpdatePosition function with the force option set to true."""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        position.update(Commands.parse("G28"))
        position.update_position(x=0, y=0, z=0, e=0, force=True)

        self.assertEqual(position.x(), 0)
        self.assertEqual(position.y(), 0)
        self.assertEqual(position.z(), 0)
        self.assertEqual(position.e(), 0)

        position.update_position(x=1, y=2, z=3, e=4, force=True)
        self.assertEqual(position.x(), 1)
        self.assertEqual(position.y(), 2)
        self.assertEqual(position.z(), 3)
        self.assertEqual(position.e(), 4)

        position.update_position(x=None, y=None, z=None, e=None, force=True)
        self.assertEqual(position.x(), 1)
        self.assertEqual(position.y(), 2)
        self.assertEqual(position.z(), 3)
        self.assertEqual(position.e(), 4)

    def test_UpdatePosition_noforce(self):
        """Test the UpdatePosition function with the force option set to true."""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        # no homed axis
        position.update_position(x=0, y=0, z=0, e=0)
        self.assertIsNone(position.x())
        self.assertIsNone(position.y())
        self.assertIsNone(position.z())
        self.assertIsNone(position.e(), 0)

        # set homed axis, test absolute position (default)
        position.update(Commands.parse("G28"))
        position.update_position(x=0, y=0, z=0)
        self.assertEqual(position.x(), 0)
        self.assertEqual(position.y(), 0)
        self.assertEqual(position.z(), 0)
        self.assertEqual(position.e(), 0)

        # update absolute position
        position.update_position(x=1, y=2, z=3)
        self.assertEqual(position.x(), 1)
        self.assertEqual(position.y(), 2)
        self.assertEqual(position.z(), 3)
        self.assertEqual(position.e(), 0)

        # set relative position
        position.update(Commands.parse("G91"))
        position.update_position(x=1, y=1, z=1)
        self.assertEqual(position.x(), 2)
        self.assertEqual(position.y(), 3)
        self.assertEqual(position.z(), 4)
        self.assertEqual(position.e(), 0)

        # set extruder absolute
        position.update(Commands.parse("M82"))
        position.update_position(e=100)
        self.assertEqual(position.x(), 2)
        self.assertEqual(position.y(), 3)
        self.assertEqual(position.z(), 4)
        self.assertEqual(position.e(), 100)
        position.update_position(e=-10)
        self.assertEqual(position.x(), 2)
        self.assertEqual(position.y(), 3)
        self.assertEqual(position.z(), 4)
        self.assertEqual(position.e(), -10)

        # set extruder relative
        position.update(Commands.parse("M83"))
        position.update_position(e=20)
        self.assertEqual(position.x(), 2)
        self.assertEqual(position.y(), 3)
        self.assertEqual(position.z(), 4)
        self.assertEqual(position.e(), 10)
        position.update_position(e=-1)
        self.assertEqual(position.x(), 2)
        self.assertEqual(position.y(), 3)
        self.assertEqual(position.z(), 4)
        self.assertEqual(position.e(), 9)

        position.update_position(x=1, y=2, z=3, e=4, force=True)
        self.assertEqual(position.x(), 1)
        self.assertEqual(position.y(), 2)
        self.assertEqual(position.z(), 3)
        self.assertEqual(position.e(), 4)

        position.update_position(x=None, y=None, z=None, e=None, force=True)
        self.assertEqual(position.x(), 1)
        self.assertEqual(position.y(), 2)
        self.assertEqual(position.z(), 3)
        self.assertEqual(position.e(), 4)

    def test_G90InfluencesExtruder_UpdatePosition(self):
        """Test G90 for machines where it influences the coordinate system of the extruder."""
        position = Position(self.Settings, self.OctoprintPrinterProfile, True)
        # Make sure the axis is homed
        position.update(Commands.parse("G28"))
        # set absolute mode with G90
        position.update(Commands.parse("g90"))
        # update the position to 10 (absolute)
        position.update_position(e=10)
        self.assertEqual(position.e(), 10)
        # update the position to 10 again (absolute) to make sure we are in absolute
        # coordinates.
        position.update_position(e=10)
        self.assertEqual(position.e(), 10)

        # set relative mode with G90
        position.update(Commands.parse("g91"))
        # update the position to 20 (relative)
        position.update_position(e=20)
        self.assertEqual(position.e(), 30)

    def test_G90InfluencesExtruder_Update(self):
        """Test G90 for machines where it influences the coordinate system of the extruder."""
        position = Position(self.Settings, self.OctoprintPrinterProfile, True)
        # Make sure the axis is homed
        position.update(Commands.parse("G28"))

        # set absolute mode with G90
        position.update(Commands.parse("g90"))
        # update the position to 10 (absolute)
        position.update(Commands.parse("G1 E10.0"))
        self.assertEqual(position.e(), 10)

        # update the position to 10 again (absolute) to make sure we are in absolute
        # coordinates.
        position.update(Commands.parse("G1 E10.0"))
        self.assertEqual(position.e(), 10)

        # set relative mode with G90
        position.update(Commands.parse("g91"))
        # update the position to 20 (relative)
        position.update(Commands.parse("G1 E20.0"))
        self.assertEqual(position.e(), 30)

    def test_Update(self):
        """Test the Update() function, which accepts gcode and updates the current position state and extruder state."""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        # no homed axis
        position.update(Commands.parse("G1 x100 y200 z300"))
        self.assertIsNone(position.x())
        self.assertIsNone(position.y())
        self.assertIsNone(position.z())

        # set relative extruder and absolute xyz, home axis and update absolute position
        position.update(Commands.parse("M83"))
        position.update(Commands.parse("G90"))
        position.update(Commands.parse("G28"))
        position.update(Commands.parse("G1 x100 y200 z150"))
        self.assertEqual(position.x(), 100)
        self.assertEqual(position.y(), 200)
        self.assertEqual(position.z(), 150)

        # move again and retest
        position.update(Commands.parse("G1 x101 y199 z151"))
        self.assertEqual(position.x(), 101)
        self.assertEqual(position.y(), 199)
        self.assertEqual(position.z(), 151)

        # switch to relative and update position
        position.update(Commands.parse("G91"))
        position.update(Commands.parse("G1 x-1 y-1 z1.0"))
        self.assertEqual(position.x(), 100)
        self.assertEqual(position.y(), 198)
        self.assertEqual(position.z(), 152)

        # move again and retest
        position.update(Commands.parse("G1 x-99 y-196 z-149.0"))
        self.assertEqual(position.x(), 1)
        self.assertEqual(position.y(), 2)
        self.assertEqual(position.z(), 3)

        # go back to absolute and move to origin
        position.update(Commands.parse("G90"))
        position.update(Commands.parse("G1 x0 y0 z0.0"))
        self.assertEqual(position.x(), 0)
        self.assertEqual(position.y(), 0)
        self.assertEqual(position.z(), 0)

    # G92 Test Set Position
    def test_G92SetPosition(self):
        """Test the G92 command, settings the position."""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        # no homed axis
        position.update(Commands.parse("G92 x10 y20 z30"))
        self.assertEqual(position.x(), 10)
        self.assertEqual(position.y(), 20)
        self.assertEqual(position.z(), 30)
        self.assertFalse(position.has_homed_axes())

        # set homed axis, absolute coordinates, and set position
        position.update(Commands.parse("G28"))
        position.update(Commands.parse("G90"))
        position.update(Commands.parse("G1 x100 y200 z150"))
        position.update(Commands.parse("G92 x10 y20 z30"))
        self.assertEqual(position.x(), 100)
        self.assertEqual(position.x_offset(), 90)
        self.assertEqual(position.y(), 200)
        self.assertEqual(position.y_offset(), 180)
        self.assertEqual(position.z(), 150)
        self.assertEqual(position.z_offset(), 120)

        # Move to same position and retest
        position.update(Commands.parse("G1 x0 y0 z0"))
        self.assertEqual(position.x(), 90)
        self.assertEqual(position.x_offset(), 90)
        self.assertEqual(position.y(), 180)
        self.assertEqual(position.y_offset(), 180)
        self.assertEqual(position.z(), 120)
        self.assertEqual(position.z_offset(), 120)

        # Move and retest
        position.update(Commands.parse("G1 x-10 y10 z20"))
        self.assertEqual(position.x(), 80)
        self.assertEqual(position.x_offset(), 90)
        self.assertEqual(position.y(), 190)
        self.assertEqual(position.y_offset(), 180)
        self.assertEqual(position.z(), 140)
        self.assertEqual(position.z_offset(), 120)

        # G92 with no parameters
        position.update(Commands.parse("G92"))
        self.assertEqual(position.x(), 80)
        self.assertEqual(position.x_offset(), 80)
        self.assertEqual(position.y(), 190)
        self.assertEqual(position.y_offset(), 190)
        self.assertEqual(position.z(), 140)
        self.assertEqual(position.z_offset(), 140)

    # G92 Test Absolute Movement
    def test_G92AbsoluteMovement(self):
        """Test the G92 command, move in absolute mode and test results."""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)

        # set homed axis, absolute coordinates, and set position
        position.update(Commands.parse("G28"))
        position.update(Commands.parse("G90"))
        position.update(Commands.parse("G1 x100 y200 z150"))
        position.update(Commands.parse("G92 x10 y20 z30"))
        self.assertEqual(position.x(), 100)
        self.assertEqual(position.x_offset(), 90)
        self.assertEqual(position.y(), 200)
        self.assertEqual(position.y_offset(), 180)
        self.assertEqual(position.z(), 150)
        self.assertEqual(position.z_offset(), 120)

        # move to origin
        position.update(Commands.parse("G1 x-90 y-180 z-120"))
        self.assertEqual(position.x(), 0)
        self.assertEqual(position.x_offset(), 90)
        self.assertEqual(position.y(), 0)
        self.assertEqual(position.y_offset(), 180)
        self.assertEqual(position.z(), 0)
        self.assertEqual(position.z_offset(), 120)

        # move back
        position.update(Commands.parse("G1 x0 y0 z0"))
        self.assertEqual(position.x(), 90)
        self.assertEqual(position.x_offset(), 90)
        self.assertEqual(position.y(), 180)
        self.assertEqual(position.y_offset(), 180)
        self.assertEqual(position.z(), 120)
        self.assertEqual(position.z_offset(), 120)

    # G92 Test Relative Movement
    def test_G92RelativeMovement(self):
        """Test the G92 command, move in relative mode and test results."""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)

        # set homed axis, relative coordinates, and set position
        position.update(Commands.parse("G28"))
        position.update(Commands.parse("G91"))
        position.update(Commands.parse("G1 x100 y200 z150"))
        position.update(Commands.parse("G92 x10 y20 z30"))
        self.assertEqual(position.x(), 100)
        self.assertEqual(position.x_offset(), 90)
        self.assertEqual(position.y(), 200)
        self.assertEqual(position.y_offset(), 180)
        self.assertEqual(position.z(), 150)
        self.assertEqual(position.z_offset(), 120)

        # move to origin
        position.update(Commands.parse("G1 x-100 y-200 z-150"))
        self.assertEqual(position.x(), 0)
        self.assertEqual(position.x_offset(), 90)
        self.assertEqual(position.y(), 0)
        self.assertEqual(position.y_offset(), 180)
        self.assertEqual(position.z(), 0)
        self.assertEqual(position.z_offset(), 120)

        # advance each axis
        position.update(Commands.parse("G1 x1 y2 z3"))
        self.assertEqual(position.x(), 1)
        self.assertEqual(position.x_offset(), 90)
        self.assertEqual(position.y(), 2)
        self.assertEqual(position.y_offset(), 180)
        self.assertEqual(position.z(), 3)
        self.assertEqual(position.z_offset(), 120)

        # advance again
        position.update(Commands.parse("G1 x1 y2 z3"))
        self.assertEqual(position.x(), 2)
        self.assertEqual(position.x_offset(), 90)
        self.assertEqual(position.y(), 4)
        self.assertEqual(position.y_offset(), 180)
        self.assertEqual(position.z(), 6)
        self.assertEqual(position.z_offset(), 120)

    def test_HeightAndLayerChanges(self):
        """Test the height and layer changes."""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)

        # test initial state
        self.assertIsNone(position.height())
        self.assertIsNone(position.layer(), None)
        self.assertFalse(position.is_layer_change())

        # check without homed axis
        position.update(Commands.parse("G1 x0 y0 z0.20000 e1"))
        self.assertEqual(position.height(), 0)
        self.assertEqual(position.layer(), 0)
        self.assertFalse(position.is_layer_change())

        # set homed axis, absolute xyz coordinates, relative extruder coordinates and check height and layer
        position.update(Commands.parse("M83"))
        position.update(Commands.parse("G90"))
        position.update(Commands.parse("G28"))
        self.assertEqual(position.height(), 0)
        self.assertEqual(position.layer(), 0)
        self.assertFalse(position.is_layer_change())

        # move without extruding, height and layer should not change
        position.update(Commands.parse("G1 x100 y200 z150"))
        self.assertEqual(position.height(), 0)
        self.assertEqual(position.layer(), 0)
        self.assertFalse(position.is_layer_change())

        # move to origin, height and layer stuff should stay the same
        position.update(Commands.parse("G1 x0 y0 z0"))
        self.assertEqual(position.height(), 0)
        self.assertEqual(position.layer(), 0)
        self.assertFalse(position.is_layer_change())

        # extrude, height change!
        position.update(Commands.parse("G1 x0 y0 z0 e1"))
        self.assertEqual(position.height(), 0)
        self.assertEqual(position.layer(), 1)
        self.assertTrue(position.is_layer_change())

        # extrude higher, update layer., this will get rounded to 0.2
        position.update(Commands.parse("G1 x0 y0 z0.1999 e1"))
        self.assertEqual(position.height(), 0.2)
        self.assertEqual(position.layer(), 2)
        self.assertTrue(position.is_layer_change())

        # extrude just slightly higher, but with rounding on the same layer
        position.update(Commands.parse("G1 x0 y0 z0.20000 e1"))
        self.assertEqual(position.height(), .2)
        self.assertEqual(position.layer(), 2)
        self.assertFalse(position.is_layer_change())

        # extrude again on same layer - Height Previous should now be updated, and
        # IsLayerChange should be false
        position.update(Commands.parse("G1 x0 y0 z0.20000 e1"))
        self.assertEqual(position.height(), .2)
        self.assertEqual(position.layer(), 2)
        self.assertFalse(position.is_layer_change())

        # extrude again on same layer - No changes
        position.update(Commands.parse("G1 x0 y0 z0.20000 e1"))
        self.assertEqual(position.height(), .2)
        self.assertEqual(position.layer(), 2)
        self.assertFalse(position.is_layer_change())

        # extrude below the current layer - No changes
        position.update(Commands.parse("G1 x0 y0 z0.00000 e1"))
        self.assertEqual(position.height(), .2)
        self.assertEqual(position.layer(), 2)
        self.assertFalse(position.is_layer_change())

        # extrude up higher and change the height/layer.  Should never happen, but
        # it's an interesting test case
        position.update(Commands.parse("G1 x0 y0 z0.60000 e1"))
        self.assertEqual(position.height(), .6)
        self.assertEqual(position.layer(), 3)
        self.assertTrue(position.is_layer_change())

        # extrude up again
        position.update(Commands.parse("G1 x0 y0 z0.65000 e1"))
        self.assertEqual(position.height(), .65)
        self.assertEqual(position.layer(), 4)
        self.assertTrue(position.is_layer_change())

        # extrude on previous layer
        position.update(Commands.parse("G1 x0 y0 z0.60000 e1"))
        self.assertEqual(position.height(), .65)
        self.assertEqual(position.layer(), 4)
        self.assertFalse(position.is_layer_change())

        # extrude on previous layer again
        position.update(Commands.parse("G1 x0 y0 z0.60000 e1"))
        self.assertEqual(position.height(), .65)
        self.assertEqual(position.layer(), 4)
        self.assertFalse(position.is_layer_change())

        # move up but do not extrude
        position.update(Commands.parse("G1 x0 y0 z0.70000"))
        self.assertEqual(position.height(), .65)
        self.assertEqual(position.layer(), 4)
        self.assertFalse(position.is_layer_change())

        # move up but do not extrude a second time
        position.update(Commands.parse("G1 x0 y0 z0.80000"))
        self.assertEqual(position.height(), .65)
        self.assertEqual(position.layer(), 4)
        self.assertFalse(position.is_layer_change())

        # extrude at a different height
        position.update(Commands.parse("G1 x0 y0 z0.80000 e.1"))
        position.update(Commands.parse("G1 x0 y0 z0.85000 e.1"))
        self.assertEqual(.85, position.height())
        self.assertEqual(6, position.layer())
        self.assertTrue(position.is_layer_change())

    # M82 and M83 - Test extruder movement
    def test_ExtruderMovement(self):
        """Test the M82 and M83 command."""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        previous_pos = Pos(self.Settings.current_printer(), self.OctoprintPrinterProfile)
        # test initial position
        self.assertIsNone(position.e())
        self.assertIsNone(position.is_extruder_relative())
        self.assertIsNone(position.e_relative_pos(previous_pos))

        # set extruder to relative coordinates
        position.update(Commands.parse("M83"))

        # test movement
        previous_pos = Pos(self.Settings.current_printer(), self.OctoprintPrinterProfile, position.get_position())
        position.update(Commands.parse("G0 E100"))
        self.assertEqual(position.e(), 100)
        # this is somewhat reversed from what we do in the position.py module
        # there we update the pos() object and compare to the current state, so
        # comparing the current state to the
        # previous will result in the opposite sign
        self.assertEqual(position.e_relative_pos(previous_pos), -100)

        # switch to absolute movement
        previous_pos = Pos(self.Settings.current_printer(), self.OctoprintPrinterProfile, position.get_position())
        position.update(Commands.parse("M82"))
        self.assertFalse(position.is_extruder_relative())
        self.assertEqual(position.e(), 100)
        self.assertEqual(position.e_relative_pos(previous_pos), 0)

        # move to -25
        previous_pos = Pos(self.Settings.current_printer(), self.OctoprintPrinterProfile, position.get_position())
        position.update(Commands.parse("G0 E-25"))
        self.assertEqual(position.e(), -25)
        self.assertEqual(position.e_relative_pos(previous_pos), 125)

        # test movement to origin
        previous_pos = Pos(self.Settings.current_printer(), self.OctoprintPrinterProfile, position.get_position())
        position.update(Commands.parse("G0 E0"))
        self.assertEqual(position.e(), 0)
        self.assertEqual(position.e_relative_pos(previous_pos), -25)

        # switch to relative position
        previous_pos = Pos(self.Settings.current_printer(), self.OctoprintPrinterProfile, position.get_position())
        position.update(Commands.parse("M83"))
        position.update(Commands.parse("G0 e1.1"))
        self.assertEqual(position.e(), 1.1)
        self.assertEqual(position.e_relative_pos(previous_pos), -1.1)

        # move and test
        previous_pos = Pos(self.Settings.current_printer(), self.OctoprintPrinterProfile, position.get_position())
        position.update(Commands.parse("G0 e1.1"))
        self.assertEqual(position.e(), 2.2)
        self.assertEqual(position.e_relative_pos(previous_pos), -1.1)

        # move and test
        previous_pos = Pos(self.Settings.current_printer(), self.OctoprintPrinterProfile, position.get_position())
        position.update(Commands.parse("G0 e-2.2"))
        self.assertEqual(position.e(), 0)
        self.assertEqual(position.e_relative_pos(previous_pos), 2.2)

    def test_zHop(self):
        """Test zHop detection."""
        # set zhop distance
        self.Settings.current_printer().z_hop = .5
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)

        # test initial state
        self.assertFalse(position.is_zhop())

        # check without homed axis
        position.update(Commands.parse("G1 x0 y0 z0"))
        self.assertFalse(position.is_zhop())
        position.update(Commands.parse("G1 x0 y0 z0.5"))
        self.assertFalse(position.is_zhop())

        # set relative extruder, absolute xyz, home axis, check again
        position.update(Commands.parse("M83"))
        position.update(Commands.parse("G90"))
        position.update(Commands.parse("G28"))
        self.assertFalse(position.is_zhop())
        # Position reports as NotHomed (misnomer, need to replace), needs to get
        # coordinates
        position.update(Commands.parse("G1 x0 y0 z0"))

        # Move up without extrude, this is not a zhop since we haven't extruded
        # anything!
        position.update(Commands.parse("g0 z0.5"))
        self.assertFalse(position.is_zhop())
        # move back down to 0 and extrude
        position.update(Commands.parse("g0 z0 e1"))
        self.assertFalse(position.is_zhop())
        # Move up without extrude, this should trigger zhop start
        position.update(Commands.parse("g0 z0.5"))
        self.assertTrue(position.is_zhop())
        # move below zhop threshold
        position.update(Commands.parse("g0 z0.3"))
        self.assertFalse(position.is_zhop())

        # move right up to zhop without going over, we are within the rounding error
        position.update(Commands.parse("g0 z0.4999"))
        self.assertTrue(position.is_zhop())

        # Extrude on z5
        position.update(Commands.parse("g0 z0.5 e1"))
        self.assertFalse(position.is_zhop())

        # partial z lift, , we are within the rounding error
        position.update(Commands.parse("g0 z0.9999"))
        self.assertTrue(position.is_zhop())
        # Still hopped!
        position.update(Commands.parse("g0 z1"))
        self.assertTrue(position.is_zhop())
        # test with extrusion start at 1.5
        position.update(Commands.parse("g0 z1.5 e1"))
        self.assertFalse(position.is_zhop())
        # test with extrusion at 2
        position.update(Commands.parse("g0 z2 e1"))
        self.assertFalse(position.is_zhop())

        # zhop
        position.update(Commands.parse("g0 z2.5 e0"))
        self.assertTrue(position.is_zhop())

        position.update(Commands.parse("no-command"))
        self.assertTrue(position.is_zhop())

    # todo: IsAtCurrent/PreviousPosition tests
    def test_IsAtCurrentPosition(self):
        # Received: x:119.91,y:113.34,z:2.1,e:0.0, Expected:
        # x:119.9145519,y:113.33847,z:2.1
        # G1 X119.915 Y113.338 F7200
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        position.Printer.printer_position_confirmation_tolerance = .0051
        position.update(Commands.parse("M83"))
        position.update(Commands.parse("G90"))
        position.update(Commands.parse("G28"))
        position.update(Commands.parse("G1 X119.915 Y113.338 Z2.1 F7200"))
        self.assertTrue(position.is_at_current_position(119.91, 113.34, 2.1))
        position.update(Commands.parse("g0 x120 y121 z2.1"))
        self.assertTrue(position.is_at_previous_position(119.91, 113.34, 2.1))

    @unittest.skip("Not yet implemented")
    def test_extruder_axis_default_mode_relative(self):
        # test e_axis_default_mode = 'relative'
        raise NotImplementedError

    @unittest.skip("Not yet implemented")
    def test_extruder_axis_default_mode_absolute(self):
        # test e_axis_default_mode = 'absolute'
        raise NotImplementedError

    @unittest.skip("Not yet implemented")
    def test_extruder_axis_default_mode_require_explicit(self):
        # test e_axis_default_mode = 'require-explicit'
        raise NotImplementedError

    @unittest.skip("Not yet implemented")
    def test_xyz_axis_default_mode_relative(self):
        # test xyz_axes_default_mode = 'relative'
        raise NotImplementedError

    @unittest.skip("Not yet implemented")
    def test_xyz_axis_default_mode_absolute(self):
        # test xyz_axes_default_mode = 'absolute'
        raise NotImplementedError

    @unittest.skip("Not yet implemented")
    def test_xyz_axis_default_mode_require_explicit(self):
        # test xyz_axes_default_mode = 'require-explicit'
        raise NotImplementedError

    @unittest.skip("Not yet implemented")
    def test_g90_influences_extruder_use_octoprint_settings(self):
        # test g90_influences_extruder = 'use-octoprint-settings'
        raise NotImplementedError

    @unittest.skip("Not yet implemented")
    def test_g90_influences_extruder_true(self):
        # test g90_influences_extruder = 'true'
        raise NotImplementedError

    @unittest.skip("Not yet implemented")
    def test_g90_influences_extruder_false(self):
        # test g90_influences_extruder = 'false'
        raise NotImplementedError

    @unittest.skip("Not yet implemented")
    def test_priming_height(self):
        # test the priming height > 0
        raise NotImplementedError

    @unittest.skip("Not yet implemented")
    def test_priming_height_0(self):
        # test the priming height = 0
        raise NotImplementedError


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPosition)
    unittest.TextTestRunner(verbosity=3).run(suite)
