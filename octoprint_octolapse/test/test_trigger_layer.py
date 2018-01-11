import unittest
from octoprint_octolapse.settings import OctolapseSettings
from octoprint_octolapse.trigger import LayerTrigger
from octoprint_octolapse.position import Position
from octoprint_octolapse.extruder import ExtruderTriggers

class Test_LayerTrigger(unittest.TestCase):
	def setUp(self):
		self.Settings = OctolapseSettings("c:\\test\\")
		self.OctoprintPrinterProfile = self.CreateOctoprintPrinterProfile()
	def tearDown(self):
		del self.Settings
		del self.OctoprintPrinterProfile
	def CreateOctoprintPrinterProfile(self):
		return dict(
				volume = dict(
					width= 250,
					depth= 200,
					height= 200,
					formFactor="Not A Circle",
					custom_box=False,
				)
			)

	def TestReset(self):
		"""Test the reset function"""
		position = Position(self.Settings, self.OctoprintPrinterProfile, False)
		trigger = LayerTrigger(self.Settings)
		# test initial state
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)
		# set the flags to different valuse
		trigger.IsTriggered = True
		trigger.IsWaiting = True
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)
		
		# test the reset state
		trigger.Reset()
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)
	def test_LayerTrigger_LayerChange(self):
		"""Test the layer trigger for layer changes triggers"""

		position = Position(self.Settings, self.OctoprintPrinterProfile, False)
		trigger = LayerTrigger(self.Settings)
		trigger.ExtruderTriggers = ExtruderTriggers(None,None,None,None,None,None,None,None,None,None) #Ignore extruder
		trigger.RequireZHop = False # no zhop required
		trigger.HeightIncrement = 0 # Trigger on any height change
		# test initial state
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# send commands that normally would trigger a layer change, but without all axis homed.
		position.Update("g0 x0 y0 z.2 e1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# Home all axis and try again
		position.Update("g28")
		trigger.Update(position)
		position.Update("g0 x0 y0 z.2 e1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == True)
		self.assertTrue(trigger.IsWaiting == False)

		# extrude again on the same layer and make sure it does NOT trigger
		position.Update("g0 x1 y1 z.2 e1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# move to higher layer, but do not extrude (no layer change)
		position.Update("g0 x1 y1 z.4")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)
		position.Update("g0 x2 y2 z.4")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# return to previous layer, do not extrude
		position.Update("g0 x2 y2 z.2")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)
		position.Update("g0 x4 y4 z.2")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# extrude again on current layer
		position.Update("g0 x2 y2 z.2 e1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		#move up two times, down and extrude (this should trigger after the final command
		position.Update("g0 x2 y2 z.4")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)
		position.Update("g0 x2 y2 z.6")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)
		position.Update("g0 x2 y2 z.4 e1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == True)
		self.assertTrue(trigger.IsWaiting == False)

		# This should never happen in a print, but test extruding on previous layers
		# move down to previous layer, extrude,
		position.Update("g0 x2 y2 z.2 e1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)
		# move back to current layer (.4), extrude (no trigger)
		position.Update("g0 x2 y2 z.4 e1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)
		# move up one more layer and extrude (trigger)
		position.Update("g0 x2 y2 z.6 e1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == True)
		self.assertTrue(trigger.IsWaiting == False)
	def test_LayerTrigger_HeightChange(self):
		"""Test the layer trigger height change """

		position = Position(self.Settings, self.OctoprintPrinterProfile, False)
		trigger = LayerTrigger(self.Settings)
		trigger.ExtruderTriggers = ExtruderTriggers(None,None,None,None,None,None,None,None,None,None) #Ignore extruder
		trigger.RequireZHop = False # no zhop required
		trigger.HeightIncrement = .25 # Trigger every .25

		# test initial state
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# send commands that normally would trigger a layer change, but without all axis homed.
		position.Update("g0 x0 y0 z.2 e1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# cur increment 0.25
		# Home all axis and try again, under layer height
		position.Update("g28")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		position.Update("g0 x0 y0 z.2 e1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == True)
		self.assertTrue(trigger.IsWaiting == False)

		# cur increment 0.25
		# extrude again on the same layer and make sure it does NOT trigger
		position.Update("g0 x1 y1 z.2 e1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# cur increment 0.25
		# move to higher layer, but do not extrude (no layer change)
		position.Update("g0 x1 y1 z.4")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)
		position.Update("g0 x2 y2 z.4")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# cur increment 0.25
		# return to previous layer, do not extrude
		position.Update("g0 x2 y2 z.2")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)
		position.Update("g0 x4 y4 z.2")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# cur increment 0.25
		# extrude again on current layer
		position.Update("g0 x2 y2 z.2 e1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# cur increment 0.25
		#move up two times, down and extrude (this should trigger after the final command
		position.Update("g0 x2 y2 z.4")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)
		position.Update("g0 x2 y2 z.6")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)
		position.Update("g0 x2 y2 z.4 e1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == True)
		self.assertTrue(trigger.IsWaiting == False)

		# cur increment 0.5
		# This should never happen in a print, but test extruding on previous layers
		# move down to previous layer, extrude,
		position.Update("g0 x2 y2 z.2 e1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)
		# move back to current layer (.4), extrude (no trigger)
		position.Update("g0 x2 y2 z.4 e1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)
		# move up one more layer and extrude (trigger)
		position.Update("g0 x2 y2 z.6 e1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == True)
		self.assertTrue(trigger.IsWaiting == False)

		# test very close to height increment (.75)
		# move up one more layer and extrude (trigger)
		position.Update("g0 x2 y2 z0.7499 e1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# Test at the increment (.75)
		position.Update("g0 x2 y2 z0.7500 e1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == True)
		self.assertTrue(trigger.IsWaiting == False)
	def test_LayerTrigger_ExtruderTriggers_NotHomed(self):
		"""Make sure nothing triggers when the axis aren't homed"""
		position = Position(self.Settings, self.OctoprintPrinterProfile, False)
		trigger = LayerTrigger(self.Settings)
		trigger.RequireZHop = False # no zhop required
		trigger.HeightIncrement = 0 # Trigger on every layer change
		position.Extruder.PrinterRetractionLength = 4

		# Try on extruding start
		trigger.ExtruderTriggers = ExtruderTriggers(True,None,None,None,None,None,None,None,None,None) 
		position.Update("g0 x0 y0 z.2 e1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# try out on extruding
		trigger.ExtruderTriggers = ExtruderTriggers(None,True,None,None,None,None,None,None,None,None)
		position.Update("g0 x0 y0 z.3 e1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# try out on primed
		trigger.ExtruderTriggers = ExtruderTriggers(None,None,True,None,None,None,None,None,None,None)
		position.Update("g0 x0 y0 z.4 e1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# try out on retracting start
		trigger.ExtruderTriggers = ExtruderTriggers(None,None,None,True,None,None,None,None,None,None)
		position.Update("g0 x0 y0 z.5 e-1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# try out on retracting
		trigger.ExtruderTriggers = ExtruderTriggers(None,None,None,None,True,None,None,None,None,None)
		position.Update("g0 x0 y0 z.5 e-1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# try out on partially retracted
		trigger.ExtruderTriggers = ExtruderTriggers(None,None,None,None,None,True,None,None,None,None)
		position.Update("g0 x0 y0 z.5 e-1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# try out on retracted
		trigger.ExtruderTriggers = ExtruderTriggers(None,None,None,None,None,None,True,None,None,None)
		position.Update("g0 x0 y0 z.5 e-1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# try out on detracting
		trigger.ExtruderTriggers = ExtruderTriggers(None,None,None,None,None,None,True,None,None,None)
		position.Update("g0 x0 y0 z.5 e1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)
	def test_LayerTrigger_ExtruderTriggers(self):
		"""Test All Extruder Triggers"""
		position = Position(self.Settings, self.OctoprintPrinterProfile, False)
		# home the axis
		position.Update("G28")
		trigger = LayerTrigger(self.Settings)
		trigger.RequireZHop = False # no zhop required
		trigger.HeightIncrement = 0 # Trigger on every layer change

		#Reset the extruder
		
		position.Extruder.Reset()
		position.Extruder.IsPrimed = False
		trigger.IsWaiting = True
		# Try on extruding start right after home, should fail
		trigger.ExtruderTriggers = ExtruderTriggers(True,None,None,None,None,None,None,None,None,None)
		position.Extruder.IsExtrudingStart = True
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == True)

		# Try again, should trigger because the previous state was homed
		position.Update("m114");
		position.Extruder.IsExtrudingStart = True
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == True)
		self.assertTrue(trigger.IsWaiting == False)


		#Reset the extruder
		position.Extruder.Reset()
		position.Extruder.IsPrimed = False
		trigger.IsWaiting = True
		# try out on extruding
		trigger.ExtruderTriggers = ExtruderTriggers(None,True,None,None,None,None,None,None,None,None)
		position.Extruder.IsExtruding = True
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == True)
		self.assertTrue(trigger.IsWaiting == False)

		#Reset the extruder
		position.Extruder.Reset()
		position.Extruder.IsPrimed = False
		trigger.IsWaiting = True
		# try out on primed
		trigger.ExtruderTriggers = ExtruderTriggers(None,None,True,None,None,None,None,None,None,None)
		position.Extruder.IsPrimed = True
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == True)
		self.assertTrue(trigger.IsWaiting == False)

		#Reset the extruder
		position.Extruder.Reset()
		position.Extruder.IsPrimed = False
		trigger.IsWaiting = True
		# try out on retracting start
		trigger.ExtruderTriggers = ExtruderTriggers(None,None,None,True,None,None,None,None,None,None)
		position.Extruder.IsRetractingStart = True
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == True)
		self.assertTrue(trigger.IsWaiting == False)

		#Reset the extruder
		position.Extruder.Reset()
		position.Extruder.IsPrimed = False
		trigger.IsWaiting = True
		# try out on retracting
		trigger.ExtruderTriggers = ExtruderTriggers(None,None,None,None,True,None,None,None,None,None)
		position.Extruder.IsRetracting = True
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == True)
		self.assertTrue(trigger.IsWaiting == False)

		#Reset the extruder
		position.Extruder.Reset()
		position.Extruder.IsPrimed = False
		trigger.IsWaiting = True
		# try out on partially retracted
		trigger.ExtruderTriggers = ExtruderTriggers(None,None,None,None,None,True,None,None,None,None)
		position.Extruder.IsPartiallyRetracted = True
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == True)
		self.assertTrue(trigger.IsWaiting == False)

		#Reset the extruder
		position.Extruder.Reset()
		position.Extruder.IsPrimed = False
		trigger.IsWaiting = True
		# try out on retracted
		trigger.ExtruderTriggers = ExtruderTriggers(None,None,None,None,None,None,True,None,None,None)
		position.Extruder.IsRetracted = True
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == True)
		self.assertTrue(trigger.IsWaiting == False)

		#Reset the extruder
		position.Extruder.Reset()
		position.Extruder.IsPrimed = False
		trigger.IsWaiting = True
		# try out on detracting Start
		trigger.ExtruderTriggers = ExtruderTriggers(None,None,None,None,None,None,None,True,None,None)
		position.Extruder.IsDetractingStart = True
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == True)
		self.assertTrue(trigger.IsWaiting == False)

		#Reset the extruder
		position.Extruder.Reset()
		position.Extruder.IsPrimed = False
		trigger.IsWaiting = True
		# try out on detracting Start
		trigger.ExtruderTriggers = ExtruderTriggers(None,None,None,None,None,None,None,None,True,None)
		position.Extruder.IsDetracting = True
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == True)
		self.assertTrue(trigger.IsWaiting == False)

		#Reset the extruder
		position.Extruder.Reset()
		position.Extruder.IsPrimed = False
		trigger.IsWaiting = True
		# try out on detracting Start
		trigger.ExtruderTriggers = ExtruderTriggers(None,None,None,None,None,None,None,None,None,True)
		position.Extruder.IsDetracted = True
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == True)
		self.assertTrue(trigger.IsWaiting == False)
	def test_LayerTrigger_ExtruderTriggerWait(self):
		"""Test wait on extruder"""
		position = Position(self.Settings, self.OctoprintPrinterProfile, False)
		# home the axis and send another command to make sure the previous instruction was homed
		position.Update("G28")
		position.Update("PreviousHomed")
		trigger = LayerTrigger(self.Settings)
		trigger.RequireZHop = False # no zhop required
		trigger.HeightIncrement = 0 # Trigger on every layer change

		#Reset the extruder
		
		position.Extruder.Reset()
		position.Extruder.IsPrimed = False
		trigger.IsWaiting = False
		# Use on extruding start for this test.  
		trigger.ExtruderTriggers = ExtruderTriggers(True,None,None,None,None,None,None,None,None,None)
		position.Extruder.IsExtrudingStart = False
		position.IsLayerChange = True
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == True)

		# update again with no change
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == True)
		# set the trigger and try again
		position.Extruder.IsExtrudingStart = True
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == True)
		self.assertTrue(trigger.IsWaiting == False)
	def test_LayerTrigger_LayerChange_ZHop(self):
		"""Test the layer trigger for layer changes triggers"""
		self.Settings.CurrentSnapshot().layer_trigger_require_zhop = True
		self.Settings.CurrentPrinter().z_hop = .5
		position = Position(self.Settings, self.OctoprintPrinterProfile, False)
		trigger = LayerTrigger(self.Settings)
		trigger.ExtruderTriggers = ExtruderTriggers(None,None,None,None,None,None,None,None,None,None) #Ignore extruder
		trigger.HeightIncrement = 0 # Trigger on any height change
		# test initial state
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# send commands that normally would trigger a layer change, but without all axis homed.
		position.Update("g0 x0 y0 z.2 e1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# Home all axis and try again, will not trigger or wait, previous axis not homed
		position.Update("g28")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == False)

		# Waiting on ZHop
		position.Update("g0 x0 y0 z.2 e1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == True)
		# try zhop
		position.Update("g0 x0 y0 z.7 ")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == True)
		self.assertTrue(trigger.IsWaiting == False)

		# extrude on current layer, no trigger (wait on zhop)
		position.Update("g0 x0 y0 z.7 e1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == True)

		# do not extrude on current layer, still waiting
		position.Update("g0 x0 y0 z.7 ")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == True)

		# partial hop, but close enough based on our printer measurement tolerance (0.005)
		position.Update("g0 x0 y0 z1.1999")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == True)
		self.assertTrue(trigger.IsWaiting == False)

		# creat wait state
		position.Update("g0 x0 y0 z1.3 e1")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == True)

		# move down (should never happen, should behave properly anyway)
		position.Update("g0 x0 y0 z.8")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == True)

		# move back up to current layer (should NOT trigger zhop)
		position.Update("g0 x0 y0 z1.3")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == True)

		# move up a bit, not enough to trigger zhop
		position.Update("g0 x0 y0 z1.79749")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == False)
		self.assertTrue(trigger.IsWaiting == True)

		# move up a bit, just enough to trigger zhop
		position.Update("g0 x0 y0 z1.79751")
		trigger.Update(position)
		self.assertTrue(trigger.IsTriggered == True)
		self.assertTrue(trigger.IsWaiting == False)

if __name__ == '__main__':
	suite = unittest.TestLoader().loadTestsFromTestCase(Test_LayerTrigger)
	unittest.TextTestRunner(verbosity=3).run(suite)
