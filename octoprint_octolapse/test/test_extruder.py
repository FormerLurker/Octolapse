
import unittest
from octoprint_octolapse.settings import OctolapseSettings
from octoprint_octolapse.command import Command,Commands
from octoprint_octolapse.extruder import Extruder, ExtruderTriggers

class Test_Extruder(unittest.TestCase):
	def setUp(self):
		
		self.Settings = OctolapseSettings("c:\\test\\")
		self.Extruder = Extruder(self.Settings)

	def tearDown(self):
		del self.Extruder
		del self.Settings

	def CreateOctoprintPrinterProfile(self):
		return {
			"volume": {
				"custom_box":False,
				"width": 250,
				"depth": 200,
				"height": 200
			}
		}

	def test_ResetInitialState(self):
		"""Test the initial extruder state, change all values, reset and check again"""
		# Check the initial state
		self.assertTrue(self.Extruder.ExtrusionLengthTotal == 0.0)
		self.assertTrue(self.Extruder.RetractionLength == 0.0)
		self.assertTrue(self.Extruder.ExtrusionLength == 0.0)
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == False)
		self.assertTrue(self.Extruder.IsPrimed == True)
		self.assertTrue(self.Extruder.IsRetractingStart == False)
		self.assertTrue(self.Extruder.IsRetracting == False)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == False)
		self.assertTrue(self.Extruder.IsRetracted == False)
		self.assertTrue(self.Extruder.IsDetractingStart == False)
		self.assertTrue(self.Extruder.IsDetracting == False)
		self.assertTrue(self.Extruder.IsDetracted == False)
		self.assertTrue(self.Extruder.HasChanged == False)


		# reset all variables
		self.Extruder.ExtrusionLengthTotal = -1
		self.Extruder.RetractionLength = -1
		self.Extruder.ExtrusionLength = -1
		self.Extruder.IsExtrudingStart = True
		self.Extruder.IsExtruding = True
		self.Extruder.IsPrimed = False
		self.Extruder.IsRetractingStart = True
		self.Extruder.IsRetracting = True
		self.Extruder.IsPartiallyRetracted = True
		self.Extruder.IsRetracted = True
		self.Extruder.IsDetractingStart = True
		self.Extruder.IsDetracting = True
		self.Extruder.IsDetracted = True
		self.Extruder.HasChanged = True

		# reset the extruder and check to make sure the initial values are there again.
		self.Extruder.Reset()
		self.assertTrue(self.Extruder.ExtrusionLengthTotal == 0.0)
		self.assertTrue(self.Extruder.RetractionLength == 0.0)
		self.assertTrue(self.Extruder.ExtrusionLength == 0.0)
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == False)
		self.assertTrue(self.Extruder.IsPrimed == True)
		self.assertTrue(self.Extruder.IsRetractingStart == False)
		self.assertTrue(self.Extruder.IsRetracting == False)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == False)
		self.assertTrue(self.Extruder.IsRetracted == False)
		self.assertTrue(self.Extruder.IsDetractingStart == False)
		self.assertTrue(self.Extruder.IsDetracting == False)
		self.assertTrue(self.Extruder.IsDetracted == False)
		self.assertTrue(self.Extruder.HasChanged == False)

	def test_HasChanged(self):
		"""Test the HasChanged flag"""
		# test the initial state
		self.assertTrue(self.Extruder.HasChanged == False)
		# test updating with no movement
		self.Extruder.Update(0)
		self.assertTrue(self.Extruder.HasChanged == False)
		#test updating with movement
		self.Extruder.Update(1)
		self.assertTrue(self.Extruder.HasChanged == True)
		# test updating with no movement
		self.Extruder.Update(0)
		self.assertTrue(self.Extruder.HasChanged == True)
		#test updating with slight movement
		self.Extruder.Update(.0001)
		self.assertTrue(self.Extruder.HasChanged == True)
		#test updating with slight movement
		self.Extruder.Update(.0001)
		self.assertTrue(self.Extruder.HasChanged == True)
		#test updating with slight movement
		self.Extruder.Update(.0001)
		self.assertTrue(self.Extruder.HasChanged == False)
		# test updating with no movement
		self.Extruder.Update(0)
		self.assertTrue(self.Extruder.HasChanged == True)
		# test updating with no movement
		self.Extruder.Update(0)
		self.assertTrue(self.Extruder.HasChanged == False)
		# test updating with no movement
		self.Extruder.Update(0)
		self.assertTrue(self.Extruder.HasChanged == False)
		#test updating with slight negative movement
		self.Extruder.Update(-0.0001)
		self.assertTrue(self.Extruder.HasChanged == True)

	def test_IsExtruderStates(self):
		"""Test the All Extruder States"""
		# set the retraction distance
		self.Extruder.PrinterRetractionLength = 4

		# test the initial state
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == False)
		self.assertTrue(self.Extruder.IsPrimed == True)
		self.assertTrue(self.Extruder.IsRetractingStart == False)
		self.assertTrue(self.Extruder.IsRetracting == False)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == False)
		self.assertTrue(self.Extruder.IsRetracted == False)
		self.assertTrue(self.Extruder.IsDetractingStart == False)
		self.assertTrue(self.Extruder.IsDetracting == False)
		self.assertTrue(self.Extruder.IsDetracted == False)

		########################################################
		# 1
		########################################################
		# 1, 1
		self.Extruder.Reset()
		self.Extruder.Update(1)
		self.Extruder.Update(1)
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == True)
		self.assertTrue(self.Extruder.IsPrimed == False)
		self.assertTrue(self.Extruder.IsRetractingStart == False)
		self.assertTrue(self.Extruder.IsRetracting == False)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == False)
		self.assertTrue(self.Extruder.IsRetracted == False)
		self.assertTrue(self.Extruder.IsDetractingStart == False)
		self.assertTrue(self.Extruder.IsDetracting == False)
		self.assertTrue(self.Extruder.IsDetracted == False)
		# 1, 0
		self.Extruder.Reset()
		self.Extruder.Update(1)
		self.Extruder.Update(0)
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == False)
		self.assertTrue(self.Extruder.IsPrimed == True)
		self.assertTrue(self.Extruder.IsRetractingStart == False)
		self.assertTrue(self.Extruder.IsRetracting == False)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == False)
		self.assertTrue(self.Extruder.IsRetracted == False)
		self.assertTrue(self.Extruder.IsDetractingStart == False)
		self.assertTrue(self.Extruder.IsDetracting == False)
		self.assertTrue(self.Extruder.IsDetracted == False)
		# 1,-1
		self.Extruder.Reset()
		self.Extruder.Update(1)
		self.Extruder.Update(-1)
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == False)
		self.assertTrue(self.Extruder.IsPrimed == False)
		self.assertTrue(self.Extruder.IsRetractingStart == True)
		self.assertTrue(self.Extruder.IsRetracting == True)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == True)
		self.assertTrue(self.Extruder.IsRetracted == False)
		self.assertTrue(self.Extruder.IsDetractingStart == False)
		self.assertTrue(self.Extruder.IsDetracting == False)
		self.assertTrue(self.Extruder.IsDetracted == False)
		# 1,-2
		self.Extruder.Reset()
		self.Extruder.Update(1)
		self.Extruder.Update(-2)
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == False)
		self.assertTrue(self.Extruder.IsPrimed == False)
		self.assertTrue(self.Extruder.IsRetractingStart == True)
		self.assertTrue(self.Extruder.IsRetracting == True)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == True)
		self.assertTrue(self.Extruder.IsRetracted == False)
		self.assertTrue(self.Extruder.IsDetractingStart == False)
		self.assertTrue(self.Extruder.IsDetracting == False)
		self.assertTrue(self.Extruder.IsDetracted == False)
		# 1,-4
		self.Extruder.Reset()
		self.Extruder.Update(1)
		self.Extruder.Update(-4)
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == False)
		self.assertTrue(self.Extruder.IsPrimed == False)
		self.assertTrue(self.Extruder.IsRetractingStart == True)
		self.assertTrue(self.Extruder.IsRetracting == True)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == False)
		self.assertTrue(self.Extruder.IsRetracted == True)
		self.assertTrue(self.Extruder.IsDetractingStart == False)
		self.assertTrue(self.Extruder.IsDetracting == False)
		self.assertTrue(self.Extruder.IsDetracted == False)
		# 1,-5
		self.Extruder.Reset()
		self.Extruder.Update(1)
		self.Extruder.Update(-5)
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == False)
		self.assertTrue(self.Extruder.IsPrimed == False)
		self.assertTrue(self.Extruder.IsRetractingStart == True)
		self.assertTrue(self.Extruder.IsRetracting == True)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == False)
		self.assertTrue(self.Extruder.IsRetracted == True)
		self.assertTrue(self.Extruder.IsDetractingStart == False)
		self.assertTrue(self.Extruder.IsDetracting == False)
		self.assertTrue(self.Extruder.IsDetracted == False)
		
		########################################################
		# 0
		########################################################
		# 0, 1
		self.Extruder.Reset()
		self.Extruder.Update(0)
		self.Extruder.Update(1)
		self.assertTrue(self.Extruder.IsExtrudingStart == True)
		self.assertTrue(self.Extruder.IsExtruding == True)
		self.assertTrue(self.Extruder.IsPrimed == False)
		self.assertTrue(self.Extruder.IsRetractingStart == False)
		self.assertTrue(self.Extruder.IsRetracting == False)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == False)
		self.assertTrue(self.Extruder.IsRetracted == False)
		self.assertTrue(self.Extruder.IsDetractingStart == False)
		self.assertTrue(self.Extruder.IsDetracting == False)
		self.assertTrue(self.Extruder.IsDetracted == False)
		# 0, 0
		self.Extruder.Reset()
		self.Extruder.Update(0)
		self.Extruder.Update(0)
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == False)
		self.assertTrue(self.Extruder.IsPrimed == True)
		self.assertTrue(self.Extruder.IsRetractingStart == False)
		self.assertTrue(self.Extruder.IsRetracting == False)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == False)
		self.assertTrue(self.Extruder.IsRetracted == False)
		self.assertTrue(self.Extruder.IsDetractingStart == False)
		self.assertTrue(self.Extruder.IsDetracting == False)
		self.assertTrue(self.Extruder.IsDetracted == False)
		# 0,-1
		self.Extruder.Reset()
		self.Extruder.Update(0)
		self.Extruder.Update(-1)
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == False)
		self.assertTrue(self.Extruder.IsPrimed == False)
		self.assertTrue(self.Extruder.IsRetractingStart == True)
		self.assertTrue(self.Extruder.IsRetracting == True)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == True)
		self.assertTrue(self.Extruder.IsRetracted == False)
		self.assertTrue(self.Extruder.IsDetractingStart == False)
		self.assertTrue(self.Extruder.IsDetracting == False)
		self.assertTrue(self.Extruder.IsDetracted == False)
		# 0,-4
		self.Extruder.Reset()
		self.Extruder.Update(0)
		self.Extruder.Update(-4)
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == False)
		self.assertTrue(self.Extruder.IsPrimed == False)
		self.assertTrue(self.Extruder.IsRetractingStart == True)
		self.assertTrue(self.Extruder.IsRetracting == True)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == False)
		self.assertTrue(self.Extruder.IsRetracted == True)
		self.assertTrue(self.Extruder.IsDetractingStart == False)
		self.assertTrue(self.Extruder.IsDetracting == False)
		self.assertTrue(self.Extruder.IsDetracted == False)
		# 0,-5
		self.Extruder.Reset()
		self.Extruder.Update(0)
		self.Extruder.Update(-5)
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == False)
		self.assertTrue(self.Extruder.IsPrimed == False)
		self.assertTrue(self.Extruder.IsRetractingStart == True)
		self.assertTrue(self.Extruder.IsRetracting == True)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == False)
		self.assertTrue(self.Extruder.IsRetracted == True)
		self.assertTrue(self.Extruder.IsDetractingStart == False)
		self.assertTrue(self.Extruder.IsDetracting == False)
		self.assertTrue(self.Extruder.IsDetracted == False)
		########################################################
		# -1
		########################################################
		# -1, 2
		self.Extruder.Reset()
		self.Extruder.Update(-1)
		self.Extruder.Update(2)
		self.assertTrue(self.Extruder.IsExtrudingStart == True)
		self.assertTrue(self.Extruder.IsExtruding == True)
		self.assertTrue(self.Extruder.IsPrimed == False)
		self.assertTrue(self.Extruder.IsRetractingStart == False)
		self.assertTrue(self.Extruder.IsRetracting == False)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == False)
		self.assertTrue(self.Extruder.IsRetracted == False)
		self.assertTrue(self.Extruder.IsDetractingStart == True)
		self.assertTrue(self.Extruder.IsDetracting == True)
		self.assertTrue(self.Extruder.IsDetracted == True)
		# -1, 1
		self.Extruder.Reset()
		self.Extruder.Update(-1)
		self.Extruder.Update(1)
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == False)
		self.assertTrue(self.Extruder.IsPrimed == True)
		self.assertTrue(self.Extruder.IsRetractingStart == False)
		self.assertTrue(self.Extruder.IsRetracting == False)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == False)
		self.assertTrue(self.Extruder.IsRetracted == False)
		self.assertTrue(self.Extruder.IsDetractingStart == True)
		self.assertTrue(self.Extruder.IsDetracting == True)
		self.assertTrue(self.Extruder.IsDetracted == True)
		# -1, 0
		self.Extruder.Reset()
		self.Extruder.Update(-1)
		self.Extruder.Update(0)
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == False)
		self.assertTrue(self.Extruder.IsPrimed == False)
		self.assertTrue(self.Extruder.IsRetractingStart == False)
		self.assertTrue(self.Extruder.IsRetracting == False)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == True)
		self.assertTrue(self.Extruder.IsRetracted == False)
		self.assertTrue(self.Extruder.IsDetractingStart == False)
		self.assertTrue(self.Extruder.IsDetracting == False)
		self.assertTrue(self.Extruder.IsDetracted == False)
		# -1,-1
		self.Extruder.Reset()
		self.Extruder.Update(-1)
		self.Extruder.Update(-1)
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == False)
		self.assertTrue(self.Extruder.IsPrimed == False)
		self.assertTrue(self.Extruder.IsRetractingStart == False)
		self.assertTrue(self.Extruder.IsRetracting == True)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == True)
		self.assertTrue(self.Extruder.IsRetracted == False)
		self.assertTrue(self.Extruder.IsDetractingStart == False)
		self.assertTrue(self.Extruder.IsDetracting == False)
		self.assertTrue(self.Extruder.IsDetracted == False)
		# -1,-3
		self.Extruder.Reset()
		self.Extruder.Update(-1)
		self.Extruder.Update(-3)
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == False)
		self.assertTrue(self.Extruder.IsPrimed == False)
		self.assertTrue(self.Extruder.IsRetractingStart == False)
		self.assertTrue(self.Extruder.IsRetracting == True)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == False)
		self.assertTrue(self.Extruder.IsRetracted == True)
		self.assertTrue(self.Extruder.IsDetractingStart == False)
		self.assertTrue(self.Extruder.IsDetracting == False)
		self.assertTrue(self.Extruder.IsDetracted == False)
		# -1,-4
		self.Extruder.Reset()
		self.Extruder.Update(-1)
		self.Extruder.Update(-4)
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == False)
		self.assertTrue(self.Extruder.IsPrimed == False)
		self.assertTrue(self.Extruder.IsRetractingStart == False)
		self.assertTrue(self.Extruder.IsRetracting == True)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == False)
		self.assertTrue(self.Extruder.IsRetracted == True)
		self.assertTrue(self.Extruder.IsDetractingStart == False)
		self.assertTrue(self.Extruder.IsDetracting == False)
		self.assertTrue(self.Extruder.IsDetracted == False)

		########################################################
		# -4
		########################################################
		# -4, 5
		self.Extruder.Reset()
		self.Extruder.Update(-4)
		self.Extruder.Update(5)
		self.assertTrue(self.Extruder.IsExtrudingStart == True)
		self.assertTrue(self.Extruder.IsExtruding == True)
		self.assertTrue(self.Extruder.IsPrimed == False)
		self.assertTrue(self.Extruder.IsRetractingStart == False)
		self.assertTrue(self.Extruder.IsRetracting == False)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == False)
		self.assertTrue(self.Extruder.IsRetracted == False)
		self.assertTrue(self.Extruder.IsDetractingStart == True)
		self.assertTrue(self.Extruder.IsDetracting == True)
		self.assertTrue(self.Extruder.IsDetracted == True)
		# -4, 4
		self.Extruder.Reset()
		self.Extruder.Update(-4)
		self.Extruder.Update(4)
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == False)
		self.assertTrue(self.Extruder.IsPrimed == True)
		self.assertTrue(self.Extruder.IsRetractingStart == False)
		self.assertTrue(self.Extruder.IsRetracting == False)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == False)
		self.assertTrue(self.Extruder.IsRetracted == False)
		self.assertTrue(self.Extruder.IsDetractingStart == True)
		self.assertTrue(self.Extruder.IsDetracting == True)
		self.assertTrue(self.Extruder.IsDetracted == True)
		# -4, 3
		self.Extruder.Reset()
		self.Extruder.Update(-4)
		self.Extruder.Update(3)
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == False)
		self.assertTrue(self.Extruder.IsPrimed == False)
		self.assertTrue(self.Extruder.IsRetractingStart == False)
		self.assertTrue(self.Extruder.IsRetracting == False)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == True)
		self.assertTrue(self.Extruder.IsRetracted == False)
		self.assertTrue(self.Extruder.IsDetractingStart == True)
		self.assertTrue(self.Extruder.IsDetracting == True)
		self.assertTrue(self.Extruder.IsDetracted == False)
		# -4, 0
		self.Extruder.Reset()
		self.Extruder.Update(-4)
		self.Extruder.Update(0)
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == False)
		self.assertTrue(self.Extruder.IsPrimed == False)
		self.assertTrue(self.Extruder.IsRetractingStart == False)
		self.assertTrue(self.Extruder.IsRetracting == False)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == False)
		self.assertTrue(self.Extruder.IsRetracted == True)
		self.assertTrue(self.Extruder.IsDetractingStart == False)
		self.assertTrue(self.Extruder.IsDetracting == False)
		self.assertTrue(self.Extruder.IsDetracted == False)
		# -4,-1
		self.Extruder.Reset()
		self.Extruder.Update(-4)
		self.Extruder.Update(-1)
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == False)
		self.assertTrue(self.Extruder.IsPrimed == False)
		self.assertTrue(self.Extruder.IsRetractingStart == False)
		self.assertTrue(self.Extruder.IsRetracting == True)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == False)
		self.assertTrue(self.Extruder.IsRetracted == True)
		self.assertTrue(self.Extruder.IsDetractingStart == False)
		self.assertTrue(self.Extruder.IsDetracting == False)
		self.assertTrue(self.Extruder.IsDetracted == False)
		########################################################
		# -5
		########################################################
		# -5, 6
		self.Extruder.Reset()
		self.Extruder.Update(-5)
		self.Extruder.Update(6)
		self.assertTrue(self.Extruder.IsExtrudingStart == True)
		self.assertTrue(self.Extruder.IsExtruding == True)
		self.assertTrue(self.Extruder.IsPrimed == False)
		self.assertTrue(self.Extruder.IsRetractingStart == False)
		self.assertTrue(self.Extruder.IsRetracting == False)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == False)
		self.assertTrue(self.Extruder.IsRetracted == False)
		self.assertTrue(self.Extruder.IsDetractingStart == True)
		self.assertTrue(self.Extruder.IsDetracting == True)
		self.assertTrue(self.Extruder.IsDetracted == True)
		# -5, 5
		self.Extruder.Reset()
		self.Extruder.Update(-5)
		self.Extruder.Update(5)
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == False)
		self.assertTrue(self.Extruder.IsPrimed == True)
		self.assertTrue(self.Extruder.IsRetractingStart == False)
		self.assertTrue(self.Extruder.IsRetracting == False)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == False)
		self.assertTrue(self.Extruder.IsRetracted == False)
		self.assertTrue(self.Extruder.IsDetractingStart == True)
		self.assertTrue(self.Extruder.IsDetracting == True)
		self.assertTrue(self.Extruder.IsDetracted == True)
		# -5, 4
		self.Extruder.Reset()
		self.Extruder.Update(-5)
		self.Extruder.Update(4)
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == False)
		self.assertTrue(self.Extruder.IsPrimed == False)
		self.assertTrue(self.Extruder.IsRetractingStart == False)
		self.assertTrue(self.Extruder.IsRetracting == False)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == True)
		self.assertTrue(self.Extruder.IsRetracted == False)
		self.assertTrue(self.Extruder.IsDetractingStart == True)
		self.assertTrue(self.Extruder.IsDetracting == True)
		self.assertTrue(self.Extruder.IsDetracted == False)
		# -5, 1
		self.Extruder.Reset()
		self.Extruder.Update(-5)
		self.Extruder.Update(1)
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == False)
		self.assertTrue(self.Extruder.IsPrimed == False)
		self.assertTrue(self.Extruder.IsRetractingStart == False)
		self.assertTrue(self.Extruder.IsRetracting == False)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == False)
		self.assertTrue(self.Extruder.IsRetracted == True)
		self.assertTrue(self.Extruder.IsDetractingStart == True)
		self.assertTrue(self.Extruder.IsDetracting == True)
		self.assertTrue(self.Extruder.IsDetracted == False)
		# -5, 0
		self.Extruder.Reset()
		self.Extruder.Update(-5)
		self.Extruder.Update(0)
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == False)
		self.assertTrue(self.Extruder.IsPrimed == False)
		self.assertTrue(self.Extruder.IsRetractingStart == False)
		self.assertTrue(self.Extruder.IsRetracting == False)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == False)
		self.assertTrue(self.Extruder.IsRetracted == True)
		self.assertTrue(self.Extruder.IsDetractingStart == False)
		self.assertTrue(self.Extruder.IsDetracting == False)
		self.assertTrue(self.Extruder.IsDetracted == False)

		# -5, -1
		self.Extruder.Reset()
		self.Extruder.Update(-5)
		self.Extruder.Update(-1)
		self.assertTrue(self.Extruder.IsExtrudingStart == False)
		self.assertTrue(self.Extruder.IsExtruding == False)
		self.assertTrue(self.Extruder.IsPrimed == False)
		self.assertTrue(self.Extruder.IsRetractingStart == False)
		self.assertTrue(self.Extruder.IsRetracting == True)
		self.assertTrue(self.Extruder.IsPartiallyRetracted == False)
		self.assertTrue(self.Extruder.IsRetracted == True)
		self.assertTrue(self.Extruder.IsDetractingStart == False)
		self.assertTrue(self.Extruder.IsDetracting == False)
		self.assertTrue(self.Extruder.IsDetracted == False)

	def test_ExtruderStateTriggered(self):
		self.assertTrue(self.Extruder.ExtruderStateTriggered(None,False) is None)
		self.assertTrue(self.Extruder.ExtruderStateTriggered(None,True) is None)
		self.assertTrue(self.Extruder.ExtruderStateTriggered(True,False) is None)
		self.assertTrue(self.Extruder.ExtruderStateTriggered(True,True))
		self.assertTrue(self.Extruder.ExtruderStateTriggered(False,False) is None)
		self.assertTrue(not self.Extruder.ExtruderStateTriggered(False,True))
	def test_extruderTriggers(self):
		"""Test the extruder triggers"""

		# test with no filters - should trigger
		self.Extruder.Reset()
		self.Extruder.IsPrimed = False # turn this off so we don't have to account for this default state
		triggers = ExtruderTriggers(None,None,None, None, None, None, None, None, None, None);
		self.assertTrue(self.Extruder.IsTriggered(triggers))

		# test OnExtrudingStart - True Filter
		triggers = ExtruderTriggers(True,None,None, None, None, None, None, None, None, None);
		# test True with true filter
		self.Extruder.IsExtrudingStart = True
		self.Extruder.IsPrimed = False # turn this off so we don't have to account for this default state
		self.assertTrue(self.Extruder.IsTriggered(triggers))
		# test False with True filter
		self.Extruder.IsExtrudingStart = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test OnExtrudingStart - False Filter
		triggers = ExtruderTriggers(False,None,None, None, None, None, None, None, None, None);
		# test True with False filter
		self.Extruder.IsExtrudingStart = True
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test False with False filter
		self.Extruder.IsExtrudingStart = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))


		# test onExtruding
		self.Extruder.Reset()
		triggers = ExtruderTriggers(None,True,None, None, None, None, None, None, None, None);
		# test True with true filter
		self.Extruder.IsExtruding = True
		self.Extruder.IsPrimed = False # turn this off so we don't have to account for this default state
		self.assertTrue(self.Extruder.IsTriggered(triggers))
		# test False with True filter
		self.Extruder.IsExtruding = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test OnExtruding - False Filter
		triggers = ExtruderTriggers(None,False,None, None, None, None, None, None, None, None);
		# test True with False filter
		self.Extruder.IsExtruding = True
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test False with False filter
		self.Extruder.IsExtruding = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))

		# test OnPrimed
		self.Extruder.Reset()
		triggers = ExtruderTriggers(None,None,True, None, None, None, None, None, None, None);
		# test True with true filter
		self.Extruder.IsPrimed = True
		self.assertTrue(self.Extruder.IsTriggered(triggers))
		# test False with True filter
		self.Extruder.IsPrimed = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test OnPrimed - False Filter
		triggers = ExtruderTriggers(None,None,False, None, None, None, None, None, None, None);
		# test True with False filter
		self.Extruder.IsPrimed = True
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test False with False filter
		self.Extruder.IsPrimed = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))

		# test OnRetractingStart
		self.Extruder.Reset()
		triggers = ExtruderTriggers(None,None,None, True, None, None, None, None, None, None);
		# test True with true filter
		self.Extruder.IsRetractingStart = True
		self.Extruder.IsPrimed = False # turn this off so we don't have to account for this default state
		self.assertTrue(self.Extruder.IsTriggered(triggers))
		# test False with True filter
		self.Extruder.IsRetractingStart = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test OnRetractingStart - False Filter
		triggers = ExtruderTriggers(None,None,None, False, None, None, None, None, None, None);
		# test True with False filter
		self.Extruder.IsRetractingStart = True
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test False with False filter
		self.Extruder.IsRetractingStart = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))

		# test OnRetracting
		self.Extruder.Reset()
		triggers = ExtruderTriggers(None,None,None, None, True, None, None, None, None, None);
		# test True with true filter
		self.Extruder.IsRetracting = True
		self.Extruder.IsPrimed = False # turn this off so we don't have to account for this default state
		self.assertTrue(self.Extruder.IsTriggered(triggers))
		# test False with True filter
		self.Extruder.IsRetracting = False
		self.assertTrue( not self.Extruder.IsTriggered(triggers))
		# test OnRetracting - False Filter
		triggers = ExtruderTriggers(None,None,None, None, False, None, None, None, None, None);
		# test True with False filter
		self.Extruder.IsRetracting = True
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test False with False filter
		self.Extruder.IsRetracting = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))

		# test OnPartiallyRetracted
		self.Extruder.Reset()
		triggers = ExtruderTriggers(None,None,None, None, None, True, None, None, None, None);
		# test True with true filter
		self.Extruder.IsPartiallyRetracted = True
		self.Extruder.IsPrimed = False # turn this off so we don't have to account for this default state
		self.assertTrue(self.Extruder.IsTriggered(triggers))
		# test False with True filter
		self.Extruder.IsPartiallyRetracted = False
		self.assertTrue(not  self.Extruder.IsTriggered(triggers))
		# test OnPartiallyRetracted - False Filter
		triggers = ExtruderTriggers(None,None,None, None, None, False, None, None, None, None);
		# test True with False filter
		self.Extruder.IsPartiallyRetracted = True
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test False with False filter
		self.Extruder.IsPartiallyRetracted = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))

		# test OnRetracted
		self.Extruder.Reset()
		triggers = ExtruderTriggers(None,None,None, None, None, None, True, None, None, None);
		# test True with true filter
		self.Extruder.IsRetracted = True
		self.Extruder.IsPrimed = False # turn this off so we don't have to account for this default state
		self.assertTrue(self.Extruder.IsTriggered(triggers))
		# test False with True filter
		self.Extruder.IsRetracted = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test OnRetracted - False Filter
		triggers = ExtruderTriggers(None,None,None, None, None, None, False, None, None, None);
		# test True with False filter
		self.Extruder.IsRetracted = True
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test False with False filter
		self.Extruder.IsRetracted = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))

		# test OnDetractingStart
		self.Extruder.Reset()
		triggers = ExtruderTriggers(None,None,None, None, None, None, None, True, None, None);
		# test True with true filter
		self.Extruder.IsDetractingStart = True
		self.Extruder.IsPrimed = False # turn this off so we don't have to account for this default state
		self.assertTrue(self.Extruder.IsTriggered(triggers))
		# test False with True filter
		self.Extruder.IsDetractingStart = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test OnDetractingStart - False Filter
		triggers = ExtruderTriggers(None,None,None, None, None, None, None, False, None, None);
		# test True with False filter
		self.Extruder.IsDetractingStart = True
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test False with False filter
		self.Extruder.IsDetractingStart = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))

		# test OnDetracting
		self.Extruder.Reset()
		triggers = ExtruderTriggers(None,None,None, None, None, None, None, None, True, None);
		# test True with true filter
		self.Extruder.IsDetracting = True
		self.Extruder.IsPrimed = False # turn this off so we don't have to account for this default state
		self.assertTrue(self.Extruder.IsTriggered(triggers))
		# test False with True filter
		self.Extruder.IsDetracting = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test OnDetracting - False Filter
		triggers = ExtruderTriggers(None,None,None, None, None, None, None, None, False, None);
		# test True with False filter
		self.Extruder.IsDetracting = True
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test False with False filter
		self.Extruder.IsDetracting = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))

		# test OnDetracted
		self.Extruder.Reset()
		triggers = ExtruderTriggers(None,None,None, None, None, None, None, None, None, True);
		# test True with true filter
		self.Extruder.IsDetracted = True
		self.Extruder.IsPrimed = False # turn this off so we don't have to account for this default state
		self.assertTrue(self.Extruder.IsTriggered(triggers))
		# test False with True filter
		self.Extruder.IsDetracted = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test OnDetracted - False Filter
		triggers = ExtruderTriggers(None,None,None, None, None, None, None, None, None, False);
		# test True with False filter
		self.Extruder.IsDetracted = True
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test False with False filter
		self.Extruder.IsDetracted = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))

		# test False with True filter
		self.Extruder.IsDetracted = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test OnDetracted - False Filter
		triggers = ExtruderTriggers(None,None,None, None, None, None, None, None, None, False);
		# test True with False filter
		self.Extruder.IsDetracted = True
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test False with False filter
		self.Extruder.IsDetracted = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))

		# Test mixed nones, trues and flases
		self.Extruder.Reset()
		triggers = ExtruderTriggers(None,True,False, None, True, False, None, True, False, None);
		# Forbidden Due to IsPrimed
		self.Extruder.IsExtrudingStart = True
		self.Extruder.IsExtruding = True
		self.Extruder.IsPrimed = True
		self.Extruder.IsRetractingStart = True
		self.Extruder.IsRetracting = True
		self.Extruder.IsPartiallyRetracted = False
		self.Extruder.IsRetracted = True
		self.Extruder.IsDetractingStart = True
		self.Extruder.IsDetracting = False
		self.Extruder.IsDetracted = True
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# True - is extruding
		self.Extruder.IsExtrudingStart = False
		self.Extruder.IsExtruding = True
		self.Extruder.IsPrimed = False
		self.Extruder.IsRetractingStart = True
		self.Extruder.IsRetracting = False
		self.Extruder.IsPartiallyRetracted = False
		self.Extruder.IsRetracted = True
		self.Extruder.IsDetractingStart = False
		self.Extruder.IsDetracting = False
		self.Extruder.IsDetracted = True
		self.assertTrue(self.Extruder.IsTriggered(triggers))

		# Test all false states and all Nones
		self.Extruder.IsExtrudingStart = True
		self.Extruder.IsExtruding = True
		self.Extruder.IsPrimed = True
		self.Extruder.IsRetractingStart = True
		self.Extruder.IsRetracting = True
		self.Extruder.IsPartiallyRetracted = True
		self.Extruder.IsRetracted = True
		self.Extruder.IsDetractingStart = True
		self.Extruder.IsDetracting = True
		self.Extruder.IsDetracted = True
		triggers = ExtruderTriggers(None,None,None, None, None, None, None, None, None, None);
		self.assertTrue(self.Extruder.IsTriggered(triggers))
		triggers = ExtruderTriggers(False,True,True, True, True, True, True, True, True, True);
		self.assertFalse(self.Extruder.IsTriggered(triggers))
		triggers = ExtruderTriggers(True,False,True, True, True, True, True, True, True, True);
		self.assertFalse(self.Extruder.IsTriggered(triggers))
		triggers = ExtruderTriggers(True,True,False, True, True, True, True, True, True, True);
		self.assertFalse(self.Extruder.IsTriggered(triggers))
		triggers = ExtruderTriggers(True,True,True, False, True, True, True, True, True, True);
		self.assertFalse(self.Extruder.IsTriggered(triggers))
		triggers = ExtruderTriggers(True,True,True, True, False, True, True, True, True, True);
		self.assertFalse(self.Extruder.IsTriggered(triggers))
		triggers = ExtruderTriggers(True,True,True, True, True, False, True, True, True, True);
		self.assertFalse(self.Extruder.IsTriggered(triggers))
		triggers = ExtruderTriggers(True,True,True, True, True, True, False, True, True, True);
		self.assertFalse(self.Extruder.IsTriggered(triggers))
		triggers = ExtruderTriggers(True,True,True, True, True, True, True, False, True, True);
		self.assertFalse(self.Extruder.IsTriggered(triggers))
		triggers = ExtruderTriggers(True,True,True, True, True, True, True, True, False, True);
		self.assertFalse(self.Extruder.IsTriggered(triggers))
		triggers = ExtruderTriggers(True,True,True, True, True, True, True, True, True, False);
		self.assertFalse(self.Extruder.IsTriggered(triggers))

if __name__ == '__main__':
	suite = unittest.TestLoader().loadTestsFromTestCase(Test_Extruder)
	unittest.TextTestRunner(verbosity=3).run(suite)
