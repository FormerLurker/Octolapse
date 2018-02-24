import unittest
from tempfile import NamedTemporaryFile

from octoprint_octolapse.position import Position
from octoprint_octolapse.settings import OctolapseSettings
from octoprint_octolapse.trigger import GcodeTrigger


class Test_GcodeTrigger(unittest.TestCase):
	def setUp(self):
		self.Settings = OctolapseSettings(NamedTemporaryFile().name)
		self.Settings.CurrentPrinter().auto_detect_position = False
		self.Settings.CurrentPrinter().origin_x = 0
		self.Settings.CurrentPrinter().origin_y = 0
		self.Settings.CurrentPrinter().origin_z = 0
		self.OctoprintPrinterProfile = self.CreateOctoprintPrinterProfile()

	def tearDown(self):
		del self.Settings
		del self.OctoprintPrinterProfile

	def CreateOctoprintPrinterProfile(self):
		return {
			"volume": {
				"custom_box": False,
				"width": 250,
				"depth": 200,
				"height": 200
			}
		}

	def test_GcodeTrigger(self):
		"""Test the gcode triggers"""
		self.Settings.CurrentSnapshot().gcode_trigger_require_zhop = False

		position = Position(self.Settings, self.OctoprintPrinterProfile, False)
		trigger = GcodeTrigger(self.Settings)
		# test initial state
		self.assertFalse(trigger.IsTriggered(0))
		self.assertFalse(trigger.IsWaiting(0))

		# send a command that is NOT the snapshot command using the defaults
		trigger.Update(position, "NotTheSnapshotCommand")
		self.assertFalse(trigger.IsTriggered(0))
		self.assertFalse(trigger.IsWaiting(0))

		# send a command that is the snapshot command without the axis being homes
		trigger.Update(position, "snap")
		self.assertFalse(trigger.IsTriggered(0))
		self.assertFalse(trigger.IsWaiting(0))

		# home the axis and resend the snap command - will be false because the PREVEIOUS state must be homed
		position.Update("G28")
		trigger.Update(position, "snap")
		self.assertFalse(trigger.IsTriggered(0))
		self.assertFalse(trigger.IsWaiting(0))

		# try again, should now work
		position.Update("G0 X0 Y0 Z0 E1 F0")
		trigger.Update(position, "snap")
		position.Update("Snap")
		trigger.Update(position, "snap")
		self.assertTrue(trigger.IsTriggered(0))
		self.assertFalse(trigger.IsWaiting(0))

		# try again, but this time set RequireZHop to true
		trigger.RequireZHop = True
		trigger.Update(position, "snap")
		self.assertFalse(trigger.IsTriggered(0))
		self.assertTrue(trigger.IsWaiting(0))
		# send another command to see if we are still waiting
		trigger.Update(position, "NotTheSnapshotCommand")
		self.assertFalse(trigger.IsTriggered(0))
		self.assertTrue(trigger.IsWaiting(0))
		# fake a zhop
		position.IsZHop = lambda x:True
		trigger.Update(position, "NotTheSnapshotCommand")
		self.assertTrue(trigger.IsTriggered(0))
		self.assertFalse(trigger.IsWaiting(0))

		# send a command that is NOT the snapshot command using the defaults
		trigger.Update(position, "NotTheSnapshotCommand")
		self.assertFalse(trigger.IsTriggered(0))
		self.assertFalse(trigger.IsWaiting(0))

		# change the snapshot triggers and make sure they are working
		self.Settings.CurrentSnapshot().gcode_trigger_require_zhop = False
		self.Settings.CurrentSnapshot().gcode_trigger_on_extruding = True
		self.Settings.CurrentSnapshot().gcode_trigger_on_extruding_start = False
		self.Settings.CurrentSnapshot().gcode_trigger_on_primed = False
		self.Settings.CurrentSnapshot().gcode_trigger_on_retracting = False
		self.Settings.CurrentSnapshot().gcode_trigger_on_retracted = False
		self.Settings.CurrentSnapshot().gcode_trigger_on_detracting = False
		trigger = GcodeTrigger(self.Settings)
		position.Extruder.IsExtruding = lambda:False
		position.Extruder.IsExtrudingStart = lambda:False
		position.Extruder.IsPrimed = lambda:False
		position.Extruder.IsRetracting = lambda:False
		position.Extruder.IsRetracted = lambda:False
		position.Extruder.IsDetracting = lambda:False
		# send a command that is the snapshot command using the defaults
		trigger.Update(position, "snap")
		self.assertFalse(trigger.IsTriggered(0))
		self.assertTrue(trigger.IsWaiting(0))
		# change the extruder state and test
		position.Extruder.Update(1.0)
		position.Extruder.Update(1.0)
		trigger.Update(position, "NotTheSnapshotCommand")
		self.assertTrue(trigger.IsTriggered(0))
		self.assertFalse(trigger.IsWaiting(0))


if __name__ == '__main__':
	suite = unittest.TestLoader().loadTestsFromTestCase(Test_GcodeTrigger)
	unittest.TextTestRunner(verbosity=3).run(suite)
