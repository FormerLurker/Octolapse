import unittest
from tempfile import NamedTemporaryFile

from octoprint_octolapse.command import Commands
from octoprint_octolapse.position import Pos
from octoprint_octolapse.position import Position
from octoprint_octolapse.settings import OctolapseSettings


class Test_Position(unittest.TestCase):
    def setUp(self):
        self.Commands = Commands()
        self.Settings = OctolapseSettings(NamedTemporaryFile().name)
        # in the general test case we want auto_detect_position to be false
        # else we'll have to simulate a position update (m114 return) after
        # a home (g28) command
        self.Settings.CurrentPrinter().auto_detect_position = False
        # since we've set auto_detect_position to false, we need to set
        # an origin, else X,Y and Z will still be None after a home command
        self.Settings.CurrentPrinter().origin_x = 0
        self.Settings.CurrentPrinter().origin_y = 0
        self.Settings.CurrentPrinter().origin_z = 0

        self.OctoprintPrinterProfile = self.CreateOctoprintPrinterProfile()

    def tearDown(self):
        del self.Commands
        del self.Settings

    def CreateOctoprintPrinterProfile(self):
        return {
            "volume": {
                "custom_box": False,
                "width": 250,
                "depth": 200,
                "height": 200
            }
        }

    def test_PositionError(self):
        """Test the IsInBounds function to make sure the program will not attempt to operate after being told to move out of bounds."""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)

        # Initial test, should return false without any coordinates
        self.assertFalse(position.HasPositionError())
        self.assertIsNone(position.PositionError())
        # home the axis and test
        position.Update("G28")
        self.assertFalse(position.HasPositionError())
        self.assertIsNone(position.PositionError())

        # X axis tests
        # reset, home the axis and test again
        position.Reset()
        position.Update("G28")
        self.assertFalse(position.HasPositionError())
        self.assertIsNone(position.PositionError())
        # move out of bounds min
        position.Update("G0 x-0.0001")
        self.assertTrue(position.HasPositionError())
        self.assertTrue(position.PositionError() is not None)
        # move back in bounds
        position.Update("G0 x0.0")
        self.assertFalse(position.HasPositionError())
        self.assertIsNone(position.PositionError())
        # move to middle
        position.Update("G0 x125")
        self.assertFalse(position.HasPositionError())
        self.assertIsNone(position.PositionError())
        # move to max
        position.Update("G0 x250")
        self.assertFalse(position.HasPositionError())
        self.assertIsNone(position.PositionError())
        # move out of bounds max
        position.Update("G0 x250.0001")
        self.assertTrue(position.HasPositionError())
        self.assertTrue(position.PositionError() is not None)

        # Y axis tests
        # reset, home the axis and test again
        position.Reset()
        position.Update("G28")
        self.assertFalse(position.HasPositionError())
        self.assertIsNone(position.PositionError())
        # move out of bounds min
        position.Update("G0 y-0.0001")
        self.assertTrue(position.HasPositionError())
        self.assertTrue(position.PositionError() is not None)
        # move back in bounds
        position.Update("G0 y0.0")
        self.assertFalse(position.HasPositionError())
        self.assertIsNone(position.PositionError())
        # move to middle
        position.Update("G0 y100")
        self.assertFalse(position.HasPositionError())
        self.assertIsNone(position.PositionError())
        # move to max
        position.Update("G0 y200")
        self.assertFalse(position.HasPositionError())
        self.assertIsNone(position.PositionError())
        # move out of bounds max
        position.Update("G0 y200.0001")
        self.assertTrue(position.HasPositionError())
        self.assertTrue(position.PositionError() is not None)

        # Z axis tests
        # reset, home the axis and test again
        position.Reset()
        position.Update("G28")
        self.assertFalse(position.HasPositionError())
        self.assertIsNone(position.PositionError())
        # move out of bounds min
        position.Update("G0 z-0.0001")
        self.assertTrue(position.HasPositionError())
        self.assertTrue(position.PositionError() is not None)
        # move back in bounds
        position.Update("G0 z0.0")
        self.assertFalse(position.HasPositionError())
        self.assertIsNone(position.PositionError())
        # move to middle
        position.Update("G0 z100")
        self.assertFalse(position.HasPositionError())
        self.assertIsNone(position.PositionError())
        # move to max
        position.Update("G0 z200")
        self.assertFalse(position.HasPositionError())
        self.assertIsNone(position.PositionError())
        # move out of bounds max
        position.Update("G0 z200.0001")
        self.assertTrue(position.HasPositionError())
        self.assertTrue(position.PositionError() is not None)

    def test_reset(self):
        """Test init state."""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        # reset all initialized vars to something else
        position.Update("G28")
        position.Update("G0 X1 Y1 Z1")

        # reset
        position.Reset()

        # test initial state
        self.assertEqual(len(position.Positions), 0)
        self.assertIsNone(position.SavedPosition)

    def test_Home(self):
        """Test the home command.  Make sure the position is set to 0,0,0 after the home."""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)

        position.Update("G28")
        self.assertEqual(position.X(), 0)
        self.assertTrue(position.GetPosition().XHomed)
        self.assertEqual(position.Y(), 0)
        self.assertTrue(position.GetPosition().YHomed)
        self.assertEqual(position.Z(), 0)
        self.assertTrue(position.GetPosition().ZHomed)
        self.assertTrue(position.HasHomedPosition())
        position.Reset()
        position.Update("G28 X")
        self.assertEqual(position.X(), 0)
        self.assertTrue(position.GetPosition().XHomed)
        self.assertIsNone(position.Y())
        self.assertFalse(position.GetPosition().YHomed)
        self.assertIsNone(position.Z())
        self.assertFalse(position.GetPosition().ZHomed)
        self.assertFalse(position.HasHomedPosition())

        position.Reset()
        position.Update("G28 Y")
        self.assertIsNone(position.X())
        self.assertFalse(position.GetPosition().XHomed)
        self.assertEqual(position.Y(), 0)
        self.assertTrue(position.GetPosition().YHomed)
        self.assertIsNone(position.Z())
        self.assertFalse(position.GetPosition().ZHomed)
        self.assertFalse(position.HasHomedPosition())

        position.Reset()
        position.Update("G28 Z")
        self.assertIsNone(position.X())
        self.assertFalse(position.GetPosition().XHomed)
        self.assertIsNone(position.Y())
        self.assertFalse(position.GetPosition().YHomed)
        self.assertEqual(position.Z(), 0)
        self.assertTrue(position.GetPosition().ZHomed)
        self.assertFalse(position.HasHomedPosition())

        position.Reset()
        position.Update("G28 Z X Y")
        self.assertEqual(position.X(), 0)
        self.assertTrue(position.GetPosition().XHomed)
        self.assertEqual(position.Y(), 0)
        self.assertTrue(position.GetPosition().YHomed)
        self.assertEqual(position.Z(), 0)
        self.assertTrue(position.GetPosition().ZHomed)
        self.assertTrue(position.HasHomedPosition())

        position.Reset()
        position.Update("g28")
        position.Update("g1 x0 y0 z0")
        # here we have seen the upded coordinates, but we do not know the position
        self.assertEqual(position.X(), 0)
        self.assertTrue(position.GetPosition().XHomed)
        self.assertEqual(position.Y(), 0)
        self.assertTrue(position.GetPosition().YHomed)
        self.assertEqual(position.Z(), 0)
        self.assertTrue(position.GetPosition().ZHomed)
        # give it another position, now we have homed axis with a known position
        position.Update("g1 x0 y0 z0")
        self.assertEqual(position.X(), 0)
        self.assertTrue(position.GetPosition().XHomed)
        self.assertEqual(position.Y(), 0)
        self.assertTrue(position.GetPosition().YHomed)
        self.assertEqual(position.Z(), 0)
        self.assertTrue(position.GetPosition().ZHomed)
        self.assertTrue(position.HasHomedPosition())

    def test_UpdatePosition_force(self):
        """Test the UpdatePosition function with the force option set to true."""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        position.Update("G28")
        position.UpdatePosition(x=0, y=0, z=0, e=0, force=True)

        self.assertEqual(position.X(), 0)
        self.assertEqual(position.Y(), 0)
        self.assertEqual(position.Z(), 0)
        self.assertEqual(position.E(), 0)

        position.UpdatePosition(x=1, y=2, z=3, e=4, force=True)
        self.assertEqual(position.X(), 1)
        self.assertEqual(position.Y(), 2)
        self.assertEqual(position.Z(), 3)
        self.assertEqual(position.E(), 4)

        position.UpdatePosition(x=None, y=None, z=None, e=None, force=True)
        self.assertEqual(position.X(), 1)
        self.assertEqual(position.Y(), 2)
        self.assertEqual(position.Z(), 3)
        self.assertEqual(position.E(), 4)

    def test_UpdatePosition_noforce(self):
        """Test the UpdatePosition function with the force option set to true."""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        # no homed axis
        position.UpdatePosition(x=0, y=0, z=0, e=0)
        self.assertIsNone(position.X())
        self.assertIsNone(position.Y())
        self.assertIsNone(position.Z())
        self.assertIsNone(position.E(), 0)

        # set homed axis, test absolute position (default)
        position.Update("G28")
        position.UpdatePosition(x=0, y=0, z=0)
        self.assertEqual(position.X(), 0)
        self.assertEqual(position.Y(), 0)
        self.assertEqual(position.Z(), 0)
        self.assertEqual(position.E(), 0)

        # update absolute position
        position.UpdatePosition(x=1, y=2, z=3)
        self.assertEqual(position.X(), 1)
        self.assertEqual(position.Y(), 2)
        self.assertEqual(position.Z(), 3)
        self.assertEqual(position.E(), 0)

        # set relative position
        position.Update("G91")
        position.UpdatePosition(x=1, y=1, z=1)
        self.assertEqual(position.X(), 2)
        self.assertEqual(position.Y(), 3)
        self.assertEqual(position.Z(), 4)
        self.assertEqual(position.E(), 0)

        # set extruder absolute
        position.Update("M82")
        position.UpdatePosition(e=100)
        self.assertEqual(position.X(), 2)
        self.assertEqual(position.Y(), 3)
        self.assertEqual(position.Z(), 4)
        self.assertEqual(position.E(), 100)
        position.UpdatePosition(e=-10)
        self.assertEqual(position.X(), 2)
        self.assertEqual(position.Y(), 3)
        self.assertEqual(position.Z(), 4)
        self.assertEqual(position.E(), -10)

        # set extruder relative
        position.Update("M83")
        position.UpdatePosition(e=20)
        self.assertEqual(position.X(), 2)
        self.assertEqual(position.Y(), 3)
        self.assertEqual(position.Z(), 4)
        self.assertEqual(position.E(), 10)
        position.UpdatePosition(e=-1)
        self.assertEqual(position.X(), 2)
        self.assertEqual(position.Y(), 3)
        self.assertEqual(position.Z(), 4)
        self.assertEqual(position.E(), 9)

        position.UpdatePosition(x=1, y=2, z=3, e=4, force=True)
        self.assertEqual(position.X(), 1)
        self.assertEqual(position.Y(), 2)
        self.assertEqual(position.Z(), 3)
        self.assertEqual(position.E(), 4)

        position.UpdatePosition(x=None, y=None, z=None, e=None, force=True)
        self.assertEqual(position.X(), 1)
        self.assertEqual(position.Y(), 2)
        self.assertEqual(position.Z(), 3)
        self.assertEqual(position.E(), 4)

    def test_G90InfluencesExtruder_UpdatePosition(self):
        """Test G90 for machines where it influences the coordinate system of the extruder."""
        position = Position(self.Settings, self.OctoprintPrinterProfile, True)
        # Make sure the axis is homed
        position.Update("G28")
        # set absolute mode with G90
        position.Update("g90")
        # update the position to 10 (absolute)
        position.UpdatePosition(e=10)
        self.assertEqual(position.E(), 10)
        # update the position to 10 again (absolute) to make sure we are in absolute
        # coordinates.
        position.UpdatePosition(e=10)
        self.assertEqual(position.E(), 10)

        # set relative mode with G90
        position.Update("g91")
        # update the position to 20 (relative)
        position.UpdatePosition(e=20)
        self.assertEqual(position.E(), 30)

    def test_G90InfluencesExtruder_Update(self):
        """Test G90 for machines where it influences the coordinate system of the extruder."""
        position = Position(self.Settings, self.OctoprintPrinterProfile, True)
        # Make sure the axis is homed
        position.Update("G28")

        # set absolute mode with G90
        position.Update("g90")
        # update the position to 10 (absolute)
        position.Update("G1 E10.0")
        self.assertEqual(position.E(), 10)

        # update the position to 10 again (absolute) to make sure we are in absolute
        # coordinates.
        position.Update("G1 E10.0")
        self.assertEqual(position.E(), 10)

        # set relative mode with G90
        position.Update("g91")
        # update the position to 20 (relative)
        position.Update("G1 E20.0")
        self.assertEqual(position.E(), 30)

    def test_Update(self):
        """Test the Update() function, which accepts gcode and updates the current position state and extruder state."""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        # no homed axis
        position.Update("G1 x100 y200 z300")
        self.assertIsNone(position.X())
        self.assertIsNone(position.Y())
        self.assertIsNone(position.Z())

        # set homed axis and update absolute position
        position.Update("G28")
        position.Update("G1 x100 y200 z150")
        self.assertEqual(position.X(), 100)
        self.assertEqual(position.Y(), 200)
        self.assertEqual(position.Z(), 150)

        # move again and retest
        position.Update("G1 x101 y199 z151")
        self.assertEqual(position.X(), 101)
        self.assertEqual(position.Y(), 199)
        self.assertEqual(position.Z(), 151)

        # switch to relative and update position
        position.Update("G91")
        position.Update("G1 x-1 y-1 z1.0")
        self.assertEqual(position.X(), 100)
        self.assertEqual(position.Y(), 198)
        self.assertEqual(position.Z(), 152)

        # move again and retest
        position.Update("G1 x-99 y-196 z-149.0")
        self.assertEqual(position.X(), 1)
        self.assertEqual(position.Y(), 2)
        self.assertEqual(position.Z(), 3)

        # go back to absolute and move to origin
        position.Update("G90")
        position.Update("G1 x0 y0 z0.0")
        self.assertEqual(position.X(), 0)
        self.assertEqual(position.Y(), 0)
        self.assertEqual(position.Z(), 0)

    # G92 Test Set Position
    def test_G92SetPosition(self):
        """Test the G92 command, settings the position."""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        # no homed axis
        position.Update("G92 x10 y20 z30")
        self.assertIsNone(position.X())
        self.assertIsNone(position.Y())
        self.assertIsNone(position.Z())

        # set homed axis, absolute coordinates, and set position
        position.Update("G28")
        position.Update("G90")
        position.Update("G1 x100 y200 z150")
        position.Update("G92 x10 y20 z30")
        self.assertEqual(position.X(), 100)
        self.assertEqual(position.XOffset(), 90)
        self.assertEqual(position.Y(), 200)
        self.assertEqual(position.YOffset(), 180)
        self.assertEqual(position.Z(), 150)
        self.assertEqual(position.ZOffset(), 120)

        # Move to same position and retest
        position.Update("G1 x0 y0 z0")
        self.assertEqual(position.X(), 90)
        self.assertEqual(position.XOffset(), 90)
        self.assertEqual(position.Y(), 180)
        self.assertEqual(position.YOffset(), 180)
        self.assertEqual(position.Z(), 120)
        self.assertEqual(position.ZOffset(), 120)

        # Move and retest
        position.Update("G1 x-10 y10 z20")
        self.assertEqual(position.X(), 80)
        self.assertEqual(position.XOffset(), 90)
        self.assertEqual(position.Y(), 190)
        self.assertEqual(position.YOffset(), 180)
        self.assertEqual(position.Z(), 140)
        self.assertEqual(position.ZOffset(), 120)

        # G92 with no parameters
        position.Update("G92")
        self.assertEqual(position.X(), 80)
        self.assertEqual(position.XOffset(), 80)
        self.assertEqual(position.Y(), 190)
        self.assertEqual(position.YOffset(), 190)
        self.assertEqual(position.Z(), 140)
        self.assertEqual(position.ZOffset(), 140)

    # G92 Test Absolute Movement
    def test_G92AbsoluteMovement(self):
        """Test the G92 command, move in absolute mode and test results."""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)

        # set homed axis, absolute coordinates, and set position
        position.Update("G28")
        position.Update("G90")
        position.Update("G1 x100 y200 z150")
        position.Update("G92 x10 y20 z30")
        self.assertEqual(position.X(), 100)
        self.assertEqual(position.XOffset(), 90)
        self.assertEqual(position.Y(), 200)
        self.assertEqual(position.YOffset(), 180)
        self.assertEqual(position.Z(), 150)
        self.assertEqual(position.ZOffset(), 120)

        # move to origin
        position.Update("G1 x-90 y-180 z-120")
        self.assertEqual(position.X(), 0)
        self.assertEqual(position.XOffset(), 90)
        self.assertEqual(position.Y(), 0)
        self.assertEqual(position.YOffset(), 180)
        self.assertEqual(position.Z(), 0)
        self.assertEqual(position.ZOffset(), 120)

        # move back
        position.Update("G1 x0 y0 z0")
        self.assertEqual(position.X(), 90)
        self.assertEqual(position.XOffset(), 90)
        self.assertEqual(position.Y(), 180)
        self.assertEqual(position.YOffset(), 180)
        self.assertEqual(position.Z(), 120)
        self.assertEqual(position.ZOffset(), 120)

    # G92 Test Relative Movement
    def test_G92RelativeMovement(self):
        """Test the G92 command, move in relative mode and test results."""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)

        # set homed axis, relative coordinates, and set position
        position.Update("G28")
        position.Update("G91")
        position.Update("G1 x100 y200 z150")
        position.Update("G92 x10 y20 z30")
        self.assertEqual(position.X(), 100)
        self.assertEqual(position.XOffset(), 90)
        self.assertEqual(position.Y(), 200)
        self.assertEqual(position.YOffset(), 180)
        self.assertEqual(position.Z(), 150)
        self.assertEqual(position.ZOffset(), 120)

        # move to origin
        position.Update("G1 x-100 y-200 z-150")
        self.assertEqual(position.X(), 0)
        self.assertEqual(position.XOffset(), 90)
        self.assertEqual(position.Y(), 0)
        self.assertEqual(position.YOffset(), 180)
        self.assertEqual(position.Z(), 0)
        self.assertEqual(position.ZOffset(), 120)

        # advance each axis
        position.Update("G1 x1 y2 z3")
        self.assertEqual(position.X(), 1)
        self.assertEqual(position.XOffset(), 90)
        self.assertEqual(position.Y(), 2)
        self.assertEqual(position.YOffset(), 180)
        self.assertEqual(position.Z(), 3)
        self.assertEqual(position.ZOffset(), 120)

        # advance again
        position.Update("G1 x1 y2 z3")
        self.assertEqual(position.X(), 2)
        self.assertEqual(position.XOffset(), 90)
        self.assertEqual(position.Y(), 4)
        self.assertEqual(position.YOffset(), 180)
        self.assertEqual(position.Z(), 6)
        self.assertEqual(position.ZOffset(), 120)

    def test_HeightAndLayerChanges(self):
        """Test the height and layer changes."""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)

        # test initial state
        self.assertIsNone(position.Height())
        self.assertIsNone(position.Layer(), None)
        self.assertFalse(position.IsLayerChange())

        # check without homed axis
        position.Update("G1 x0 y0 z0.20000 e1")
        self.assertEqual(position.Height(), 0)
        self.assertEqual(position.Layer(), 0)
        self.assertFalse(position.IsLayerChange())

        # set homed axis, absolute coordinates, and check height and layer
        position.Update("G28")
        self.assertEqual(position.Height(), 0)
        self.assertEqual(position.Layer(), 0)
        self.assertFalse(position.IsLayerChange())

        # move without extruding, height and layer should not change
        position.Update("G1 x100 y200 z150")
        self.assertEqual(position.Height(), 0)
        self.assertEqual(position.Layer(), 0)
        self.assertFalse(position.IsLayerChange())

        # move to origin, height and layer stuff should stay the same
        position.Update("G1 x0 y0 z0")
        self.assertEqual(position.Height(), 0)
        self.assertEqual(position.Layer(), 0)
        self.assertFalse(position.IsLayerChange())

        # extrude, height change!
        position.Update("G1 x0 y0 z0 e1")
        self.assertEqual(position.Height(), 0)
        self.assertEqual(position.Layer(), 1)
        self.assertTrue(position.IsLayerChange())

        # extrude higher, update layer., this will get rounded to 0.2
        position.Update("G1 x0 y0 z0.1999 e1")
        self.assertEqual(position.Height(), 0.2)
        self.assertEqual(position.Layer(), 2)
        self.assertTrue(position.IsLayerChange())

        # extrude just slightly higher, but with rounding on the same layer
        position.Update("G1 x0 y0 z0.20000 e1")
        self.assertEqual(position.Height(), .2)
        self.assertEqual(position.Layer(), 2)
        self.assertFalse(position.IsLayerChange())

        # extrude again on same layer - Height Previous should now be updated, and
        # IsLayerChange should be false
        position.Update("G1 x0 y0 z0.20000 e1")
        self.assertEqual(position.Height(), .2)
        self.assertEqual(position.Layer(), 2)
        self.assertFalse(position.IsLayerChange())

        # extrude again on same layer - No changes
        position.Update("G1 x0 y0 z0.20000 e1")
        self.assertEqual(position.Height(), .2)
        self.assertEqual(position.Layer(), 2)
        self.assertFalse(position.IsLayerChange())

        # extrude below the current layer - No changes
        position.Update("G1 x0 y0 z0.00000 e1")
        self.assertEqual(position.Height(), .2)
        self.assertEqual(position.Layer(), 2)
        self.assertFalse(position.IsLayerChange())

        # extrude up higher and change the height/layer.  Should never happen, but
        # it's an interesting test case
        position.Update("G1 x0 y0 z0.60000 e1")
        self.assertEqual(position.Height(), .6)
        self.assertEqual(position.Layer(), 3)
        self.assertTrue(position.IsLayerChange())

        # extrude up again
        position.Update("G1 x0 y0 z0.65000 e1")
        self.assertEqual(position.Height(), .65)
        self.assertEqual(position.Layer(), 4)
        self.assertTrue(position.IsLayerChange())

        # extrude on previous layer
        position.Update("G1 x0 y0 z0.60000 e1")
        self.assertEqual(position.Height(), .65)
        self.assertEqual(position.Layer(), 4)
        self.assertFalse(position.IsLayerChange())

        # extrude on previous layer again
        position.Update("G1 x0 y0 z0.60000 e1")
        self.assertEqual(position.Height(), .65)
        self.assertEqual(position.Layer(), 4)
        self.assertFalse(position.IsLayerChange())

        # move up but do not extrude
        position.Update("G1 x0 y0 z0.70000")
        self.assertEqual(position.Height(), .65)
        self.assertEqual(position.Layer(), 4)
        self.assertFalse(position.IsLayerChange())

        # move up but do not extrude a second time
        position.Update("G1 x0 y0 z0.80000")
        self.assertEqual(position.Height(), .65)
        self.assertEqual(position.Layer(), 4)
        self.assertFalse(position.IsLayerChange())

        # extrude at a different height
        position.Update("G1 x0 y0 z0.80000 e.1")
        position.Update("G1 x0 y0 z0.85000 e.1")
        self.assertEqual(.85, position.Height())
        self.assertEqual(6, position.Layer())
        self.assertTrue(position.IsLayerChange())

    # M82 and M83 - Test extruder movement
    def test_ExtruderMovement(self):
        """Test the M82 and M83 command."""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        previousPos = Pos(self.OctoprintPrinterProfile)
        # test initial position
        self.assertIsNone(position.E())
        self.assertIsNone(position.IsExtruderRelative())
        self.assertIsNone(position.ERelative(previousPos))

        # test movement
        previousPos = Pos(self.OctoprintPrinterProfile, position.GetPosition())
        position.Update("G0 E100")
        self.assertEqual(position.E(), 100)
        # this is somewhat reversed from what we do in the position.py module
        # there we update the pos() object and compare to the current state, so
        # comparing the current state to the
        # previous will result in the opposite sign
        self.assertEqual(position.ERelative(previousPos), -100)

        # switch to absolute movement
        previousPos = Pos(self.OctoprintPrinterProfile, position.GetPosition())
        position.Update("M82")
        self.assertFalse(position.IsExtruderRelative())
        self.assertEqual(position.E(), 100)
        self.assertEqual(position.ERelative(previousPos), 0)

        # move to -25
        previousPos = Pos(self.OctoprintPrinterProfile, position.GetPosition())
        position.Update("G0 E-25")
        self.assertEqual(position.E(), -25)
        self.assertEqual(position.ERelative(previousPos), 125)

        # test movement to origin
        previousPos = Pos(self.OctoprintPrinterProfile, position.GetPosition())
        position.Update("G0 E0")
        self.assertEqual(position.E(), 0)
        self.assertEqual(position.ERelative(previousPos), -25)

        # switch to relative position
        previousPos = Pos(self.OctoprintPrinterProfile, position.GetPosition())
        position.Update("M83")
        position.Update("G0 e1.1")
        self.assertEqual(position.E(), 1.1)
        self.assertEqual(position.ERelative(previousPos), -1.1)

        # move and test
        previousPos = Pos(self.OctoprintPrinterProfile, position.GetPosition())
        position.Update("G0 e1.1")
        self.assertEqual(position.E(), 2.2)
        self.assertEqual(position.ERelative(previousPos), -1.1)

        # move and test
        previousPos = Pos(self.OctoprintPrinterProfile, position.GetPosition())
        position.Update("G0 e-2.2")
        self.assertEqual(position.E(), 0)
        self.assertEqual(position.ERelative(previousPos), 2.2)

    def test_zHop(self):
        """Test zHop detection."""
        # set zhop distance
        self.Settings.CurrentPrinter().z_hop = .5
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)

        # test initial state
        self.assertFalse(position.IsZHop())

        # check without homed axis
        position.Update("G1 x0 y0 z0")
        self.assertFalse(position.IsZHop())
        position.Update("G1 x0 y0 z0.5")
        self.assertFalse(position.IsZHop())

        # Home axis, check again
        position.Update("G28")
        self.assertFalse(position.IsZHop())
        # Position reports as NotHomed (misnomer, need to replace), needs to get
        # coordinates
        position.Update("G1 x0 y0 z0")

        # Move up without extrude, this is not a zhop since we haven't extruded
        # anything!
        position.Update("g0 z0.5")
        self.assertFalse(position.IsZHop())
        # move back down to 0 and extrude
        position.Update("g0 z0 e1")
        self.assertFalse(position.IsZHop())
        # Move up without extrude, this should trigger zhop start
        position.Update("g0 z0.5")
        self.assertTrue(position.IsZHop())
        # move below zhop threshold
        position.Update("g0 z0.3")
        self.assertFalse(position.IsZHop())

        # move right up to zhop without going over, we are within the rounding error
        position.Update("g0 z0.4999")
        self.assertTrue(position.IsZHop())

        # Extrude on z5
        position.Update("g0 z0.5 e1")
        self.assertFalse(position.IsZHop())

        # partial z lift, , we are within the rounding error
        position.Update("g0 z0.9999")
        self.assertTrue(position.IsZHop())
        # Still hopped!
        position.Update("g0 z1")
        self.assertTrue(position.IsZHop())
        # test with extrusion start at 1.5
        position.Update("g0 z1.5 e1")
        self.assertFalse(position.IsZHop())
        # test with extrusion at 2
        position.Update("g0 z2 e1")
        self.assertFalse(position.IsZHop())

        # zhop
        position.Update("g0 z2.5 e0")
        self.assertTrue(position.IsZHop())
        
        position.Update("no-command")
        self.assertTrue(position.IsZHop())

    # todo: IsAtCurrent/PreviousPosition tests
    def test_IsAtCurrentPosition(self):
        # Received: x:119.91,y:113.34,z:2.1,e:0.0, Expected:
        # x:119.9145519,y:113.33847,z:2.1
        # G1 X119.915 Y113.338 F7200
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        position.Printer.printer_position_confirmation_tolerance = .0051
        position.Update("g28")
        position.Update("G1 X119.915 Y113.338 Z2.1 F7200")
        self.assertTrue(position.IsAtCurrentPosition(119.91, 113.34, 2.1))
        position.Update("g0 x120 y121 z2.1")
        self.assertTrue(position.IsAtPreviousPosition(119.91, 113.34, 2.1))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(Test_Position)
    unittest.TextTestRunner(verbosity=3).run(suite)
