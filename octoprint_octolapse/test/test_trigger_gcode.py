import unittest
from octoprint_octolapse.settings import OctolapseSettings
from octoprint_octolapse.trigger import GcodeTrigger
from octoprint_octolapse.position import Position


class Test_GcodeTrigger(unittest.TestCase):
	def setUp(self):
		self.Settings = OctolapseSettings("c:\\test\\")
		self.OctoprintPrinterProfile = self.CreateOctoprintPrinterProfile()
	def tearDown(self):
		del self.Settings
		del self.OctoprintPrinterProfile

	def CreateOctoprintPrinterProfile(self):
		return {
			"volume": {
				"custom_box":False,
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
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# send a command that is NOT the snapshot command using the defaults
		trigger.Update(position,"NotTheSnapshotCommand")
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# send a command that is the snapshot command without the axis being homes
		trigger.Update(position,"snap")
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# home the axis and resend the snap command - will be false because the PREVEIOUS state must be homed
		position.Update("g28")
		trigger.Update(position,"snap")
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# try again, should now work
		position.Update("Snap")
		trigger.Update(position,"snap")
		self.assertTrue(trigger.IsTriggered == True)
		self.assertTrue(trigger.IsWaiting == False)

		# try again, but this time set RequresZHop to true
		trigger.RequireZHop = True
		trigger.Update(position,"snap")
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == True)
		# send another command to see if we are still waiting
		trigger.Update(position,"NotTheSnapshotCommand")
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == True)
		# fake a zhop
		position.IsZHop = True
		trigger.Update(position,"NotTheSnapshotCommand")
		self.assertTrue(trigger.IsTriggered == True)
		self.assertTrue(trigger.IsWaiting == False)
		
		# send a command that is NOT the snapshot command using the defaults
		trigger.Update(position,"NotTheSnapshotCommand")
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# change the snapshot triggers and make sure they are working
		self.Settings.CurrentSnapshot().gcode_trigger_require_zhop = False
		self.Settings.CurrentSnapshot().gcode_trigger_on_extruding = True
		self.Settings.CurrentSnapshot().gcode_trigger_on_extruding_start = False
		self.Settings.CurrentSnapshot().gcode_trigger_on_primed = False
		self.Settings.CurrentSnapshot().gcode_trigger_on_retracting = False
		self.Settings.CurrentSnapshot().gcode_trigger_on_retracted = False
		self.Settings.CurrentSnapshot().gcode_trigger_on_detracting = False
		trigger = GcodeTrigger(self.Settings)
		position.Extruder.IsExtruding = False
		position.Extruder.IsExtrudingStart = False
		position.Extruder.IsPrimed = False
		position.Extruder.IsRetracting = False
		position.Extruder.IsRetracted = False
		position.Extruder.IsDetracting = False
		# send a command that is the snapshot command using the defaults
		trigger.Update(position,"snap")
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == True)
		# change the extruder state and test
		position.Extruder.IsExtruding = True
		trigger.Update(position,"NotTheSnapshotCommand")
		self.assertTrue(trigger.IsTriggered == True)
		self.assertTrue(trigger.IsWaiting == False)

if __name__ == '__main__':
	suite = unittest.TestLoader().loadTestsFromTestCase(Test_GcodeTrigger)
	unittest.TextTestRunner(verbosity=3).run(suite)
