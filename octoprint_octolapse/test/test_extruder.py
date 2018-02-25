import unittest
from tempfile import NamedTemporaryFile

from octoprint_octolapse.extruder import Extruder, ExtruderTriggers, ExtruderState
from octoprint_octolapse.settings import OctolapseSettings


class Test_Extruder(unittest.TestCase):
	def setUp(self):
		self.Settings = OctolapseSettings(NamedTemporaryFile().name)
		self.Extruder = Extruder(self.Settings)

	def CreateOctoprintPrinterProfile(self):
		return {
			"volume": {
				"custom_box": False,
				"width": 250,
				"depth": 200,
				"height": 200
			}
		}

	def test_ResetInitialState(self):
		"""Test the initial extruder state, change all values, reset and check again"""
		# Check the initial state
		self.assertEquals(len(self.Extruder.StateHistory), 1)

		# add some states
		state1 = ExtruderState()
		self.Extruder.AddState(state1)

		state2 = ExtruderState()
		self.Extruder.AddState(state2)

		state3 = ExtruderState()
		self.Extruder.AddState(state3)

		# check the length of StateHistory
		self.assertEquals(len(self.Extruder.StateHistory), 4)

		# reset the state and check again
		self.Extruder.Reset()
		self.assertEquals(len(self.Extruder.StateHistory), 0)

	def testExtruderState_InitialValues(self):
		# create a new state
		state = ExtruderState()

		# verify the initial values
		self.assertEquals(state.E, 0)
		self.assertEquals(state.ExtrusionLength, 0.0)
		self.assertEquals(state.ExtrusionLengthTotal, 0.0)
		self.assertEquals(state.RetractionLength, 0.0)
		self.assertEquals(state.DetractionLength, 0.0)
		self.assertFalse(state.IsExtrudingStart)
		self.assertFalse(state.IsExtruding)
		self.assertFalse(state.IsPrimed)
		self.assertFalse(state.IsRetractingStart)
		self.assertFalse(state.IsRetracting)
		self.assertFalse(state.IsPartiallyRetracted)
		self.assertFalse(state.IsRetracted)
		self.assertFalse(state.IsDetractingStart)
		self.assertFalse(state.IsDetracting)
		self.assertFalse(state.IsDetracted)
		self.assertFalse(state.HasChanged)

	def testExtruderStateCopy(self):
		# create a new state
		state = ExtruderState()
		# change all the default values

		state.E = 1
		state.ExtrusionLength = 100
		state.ExtrusionLengthTotal = 200
		state.RetractionLength = 300
		state.DetractionLength = 400
		state.IsExtrudingStart = True
		state.IsExtruding = True
		state.IsPrimed = True
		state.IsRetractingStart = True
		state.IsRetracting = True
		state.IsPartiallyRetracted = True
		state.IsRetracted = True
		state.IsDetractingStart = True
		state.IsDetracting = True
		state.IsDetracted = True
		state.HasChanged = True

		# copy to a new state
		newState = ExtruderState(state)
		# verify the state was copied correctly
		self.assertEquals(newState.E, 1)
		self.assertEquals(newState.ExtrusionLength, 100)
		self.assertEquals(newState.ExtrusionLengthTotal, 200)
		self.assertEquals(newState.RetractionLength, 300)
		self.assertEquals(newState.DetractionLength, 400)
		self.assertTrue(newState.IsExtrudingStart)
		self.assertTrue(newState.IsExtruding)
		self.assertTrue(newState.IsPrimed)
		self.assertTrue(newState.IsRetractingStart)
		self.assertTrue(newState.IsRetracting)
		self.assertTrue(newState.IsPartiallyRetracted)
		self.assertTrue(newState.IsRetracted)
		self.assertTrue(newState.IsDetractingStart)
		self.assertTrue(newState.IsDetracting)
		self.assertTrue(newState.IsDetracted)
		self.assertTrue(newState.HasChanged)

	def test_HasChanged(self):
		"""Test the HasChanged flag"""
		# test the initial state
		self.assertFalse(self.Extruder.HasChanged())
		# test updating with no movement - Change to primed
		self.Extruder.Update(0)
		self.assertTrue(self.Extruder.HasChanged())

		# test updating with no movement
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.HasChanged())

		# test updating with movement
		self.Extruder.Update(1)
		self.assertTrue(self.Extruder.HasChanged())
		# test updating with no movement
		self.Extruder.Update(0)
		self.assertTrue(self.Extruder.HasChanged())
		# test updating with slight movement (below printer tolerance)
		self.Extruder.Update(.0001)
		self.assertFalse(self.Extruder.HasChanged())
		# test updating with slight movement (below printer tolerance)
		self.Extruder.Update(.0001)
		self.assertFalse(self.Extruder.HasChanged())
		# test updating with slight movement (above printer tolerance)
		self.Extruder.Update(.01)
		self.assertTrue(self.Extruder.HasChanged())
		# test updating with slight movement (above printer tolerance)
		self.Extruder.Update(.01)
		self.assertTrue(self.Extruder.HasChanged())
		# test updating with no movement
		self.Extruder.Update(0)
		self.assertTrue(self.Extruder.HasChanged())
		# test updating with no movement, IsPrimed changed from 0 to 1
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.HasChanged())
		# test updating with no movement
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.HasChanged())
		# test updating with slight negative movement
		self.Extruder.Update(-0.01)
		self.assertTrue(self.Extruder.HasChanged())

	def test_IsExtruderStates(self):
		"""Test the All Extruder States"""
		# set the retraction distance
		self.Extruder.PrinterRetractionLength = 4

		# test the initial state
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)

		########################################################
		# 1
		########################################################
		# 1, 1, 0
		self.Extruder.Reset()
		self.Extruder.Update(1)
		self.Extruder.Update(1)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertTrue(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# 1, 1, 1
		self.Extruder.Reset()
		self.Extruder.Update(1)
		self.Extruder.Update(1)
		self.Extruder.Update(1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertTrue(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# 1, 1, -1
		self.Extruder.Reset()
		self.Extruder.Update(1)
		self.Extruder.Update(1)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertTrue(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# 1, 0, 0
		self.Extruder.Reset()
		self.Extruder.Update(1)
		self.Extruder.Update(0)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertTrue(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# 1, 0, 1
		self.Extruder.Reset()
		self.Extruder.Update(1)
		self.Extruder.Update(0)
		self.Extruder.Update(1)
		self.assertTrue(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)

		# 1, 0, -1
		self.Extruder.Reset()
		self.Extruder.Update(1)
		self.Extruder.Update(0)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertTrue(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)

		# 1,-1, 0
		self.Extruder.Reset()
		self.Extruder.Update(1)
		self.Extruder.Update(-1)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertTrue(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# 1,-1, 1
		self.Extruder.Reset()
		self.Extruder.Update(1)
		self.Extruder.Update(-1)
		self.Extruder.Update(1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertTrue(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertTrue(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# 1,-1, -1
		self.Extruder.Reset()
		self.Extruder.Update(1)
		self.Extruder.Update(-1)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertTrue(self.Extruder.IsRetracting)
		self.assertTrue(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# 1,-2,0
		self.Extruder.Reset()
		self.Extruder.Update(1)
		self.Extruder.Update(-2)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertTrue(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# 1,-2,1
		self.Extruder.Reset()
		self.Extruder.Update(1)
		self.Extruder.Update(-2)
		self.Extruder.Update(1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertTrue(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertTrue(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# 1,-2,-1
		self.Extruder.Reset()
		self.Extruder.Update(1)
		self.Extruder.Update(-2)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertTrue(self.Extruder.IsRetracting)
		self.assertTrue(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# 1,-4,0
		self.Extruder.Reset()
		self.Extruder.Update(1)
		self.Extruder.Update(-4)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# 1,-4,1
		self.Extruder.Reset()
		self.Extruder.Update(1)
		self.Extruder.Update(-4)
		self.Extruder.Update(1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertTrue(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# 1,-4,-1
		self.Extruder.Reset()
		self.Extruder.Update(1)
		self.Extruder.Update(-4)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertTrue(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# 1,-5,0
		self.Extruder.Reset()
		self.Extruder.Update(1)
		self.Extruder.Update(-5)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# 1,-5,1
		self.Extruder.Reset()
		self.Extruder.Update(1)
		self.Extruder.Update(-5)
		self.Extruder.Update(1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertTrue(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# 1,-5, -1
		self.Extruder.Reset()
		self.Extruder.Update(1)
		self.Extruder.Update(-5)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertTrue(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		########################################################
		# 0
		########################################################
		# 0, 1, 0
		self.Extruder.Reset()
		self.Extruder.Update(0)
		self.Extruder.Update(1)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertTrue(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# 0, 1, 1
		self.Extruder.Reset()
		self.Extruder.Update(0)
		self.Extruder.Update(1)
		self.Extruder.Update(1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertTrue(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# 0, 1, -1
		self.Extruder.Reset()
		self.Extruder.Update(0)
		self.Extruder.Update(1)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertTrue(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)

		# 0, 0, 0
		self.Extruder.Reset()
		self.Extruder.Update(0)
		self.Extruder.Update(0)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertTrue(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# 0, 0, 1
		self.Extruder.Reset()
		self.Extruder.Update(0)
		self.Extruder.Update(0)
		self.Extruder.Update(1)
		self.assertTrue(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# 0, 0, -1
		self.Extruder.Reset()
		self.Extruder.Update(0)
		self.Extruder.Update(0)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertTrue(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)

		# 0,-1, 0
		self.Extruder.Reset()
		self.Extruder.Update(0)
		self.Extruder.Update(-1)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertTrue(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# 0,-1, 1
		self.Extruder.Reset()
		self.Extruder.Update(0)
		self.Extruder.Update(-1)
		self.Extruder.Update(1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertTrue(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertTrue(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# 0,-1, -1
		self.Extruder.Reset()
		self.Extruder.Update(0)
		self.Extruder.Update(-1)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertTrue(self.Extruder.IsRetracting)
		self.assertTrue(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)

		# 0,-4, 0
		self.Extruder.Reset()
		self.Extruder.Update(0)
		self.Extruder.Update(-4)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# 0,-4, 1
		self.Extruder.Reset()
		self.Extruder.Update(0)
		self.Extruder.Update(-4)
		self.Extruder.Update(1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertTrue(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# 0,-4, -1
		self.Extruder.Reset()
		self.Extruder.Update(0)
		self.Extruder.Update(-4)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertTrue(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)

		# 0,-5, 0
		self.Extruder.Reset()
		self.Extruder.Update(0)
		self.Extruder.Update(-5)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# 0,-5, 1
		self.Extruder.Reset()
		self.Extruder.Update(0)
		self.Extruder.Update(-5)
		self.Extruder.Update(1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertTrue(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# 0,-5, -1
		self.Extruder.Reset()
		self.Extruder.Update(0)
		self.Extruder.Update(-5)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertTrue(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		########################################################
		# -1
		########################################################
		# -1, 2, 0
		self.Extruder.Reset()
		self.Extruder.Update(-1)
		self.Extruder.Update(2)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertTrue(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -1, 2, 1
		self.Extruder.Reset()
		self.Extruder.Update(-1)
		self.Extruder.Update(2)
		self.Extruder.Update(1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertTrue(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -1, 2, -1
		self.Extruder.Reset()
		self.Extruder.Update(-1)
		self.Extruder.Update(2)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertTrue(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)

		# -1, 1, 0
		self.Extruder.Reset()
		self.Extruder.Update(-1)
		self.Extruder.Update(1)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertTrue(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertTrue(self.Extruder.IsDetracted)
		# -1, 1, 1
		self.Extruder.Reset()
		self.Extruder.Update(-1)
		self.Extruder.Update(1)
		self.Extruder.Update(1)
		self.assertTrue(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertTrue(self.Extruder.IsDetracted)
		# -1, 1, -1
		self.Extruder.Reset()
		self.Extruder.Update(-1)
		self.Extruder.Update(1)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertTrue(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertTrue(self.Extruder.IsDetracted)

		# -1, 0, 0
		self.Extruder.Reset()
		self.Extruder.Update(-1)
		self.Extruder.Update(0)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertTrue(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -1, 0, 1
		self.Extruder.Reset()
		self.Extruder.Update(-1)
		self.Extruder.Update(0)
		self.Extruder.Update(1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertTrue(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertTrue(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -1, 0, -1
		self.Extruder.Reset()
		self.Extruder.Update(-1)
		self.Extruder.Update(0)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertTrue(self.Extruder.IsRetracting)
		self.assertTrue(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)

		# -1,-1, 0
		self.Extruder.Reset()
		self.Extruder.Update(-1)
		self.Extruder.Update(-1)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertTrue(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -1,-1, 1
		self.Extruder.Reset()
		self.Extruder.Update(-1)
		self.Extruder.Update(-1)
		self.Extruder.Update(1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertTrue(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertTrue(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -1,-1, -1
		self.Extruder.Reset()
		self.Extruder.Update(-1)
		self.Extruder.Update(-1)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertTrue(self.Extruder.IsRetracting)
		self.assertTrue(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)

		# -1,-3, 0
		self.Extruder.Reset()
		self.Extruder.Update(-1)
		self.Extruder.Update(-3)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -1,-3, 1
		self.Extruder.Reset()
		self.Extruder.Update(-1)
		self.Extruder.Update(-3)
		self.Extruder.Update(1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertTrue(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -1,-3, -1
		self.Extruder.Reset()
		self.Extruder.Update(-1)
		self.Extruder.Update(-3)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertTrue(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)

		# -1,-4, 0
		self.Extruder.Reset()
		self.Extruder.Update(-1)
		self.Extruder.Update(-4)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -1,-4, 1
		self.Extruder.Reset()
		self.Extruder.Update(-1)
		self.Extruder.Update(-4)
		self.Extruder.Update(1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertTrue(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -1,-4, -1
		self.Extruder.Reset()
		self.Extruder.Update(-1)
		self.Extruder.Update(-4)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertTrue(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)

		########################################################
		# -4
		########################################################
		# -4, 5, 0
		self.Extruder.Reset()
		self.Extruder.Update(-4)
		self.Extruder.Update(5)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertTrue(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -4, 5, 1
		self.Extruder.Reset()
		self.Extruder.Update(-4)
		self.Extruder.Update(5)
		self.Extruder.Update(1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertTrue(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -4, 5, -1
		self.Extruder.Reset()
		self.Extruder.Update(-4)
		self.Extruder.Update(5)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertTrue(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)

		# -4, 4, 0
		self.Extruder.Reset()
		self.Extruder.Update(-4)
		self.Extruder.Update(4)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertTrue(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertTrue(self.Extruder.IsDetracted)
		# -4, 4, 1
		self.Extruder.Reset()
		self.Extruder.Update(-4)
		self.Extruder.Update(4)
		self.Extruder.Update(1)
		self.assertTrue(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertTrue(self.Extruder.IsDetracted)
		# -4, 4, -1
		self.Extruder.Reset()
		self.Extruder.Update(-4)
		self.Extruder.Update(4)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertTrue(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertTrue(self.Extruder.IsDetracted)

		# -4, 3, 0
		self.Extruder.Reset()
		self.Extruder.Update(-4)
		self.Extruder.Update(3)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertTrue(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -4, 3, 1
		self.Extruder.Reset()
		self.Extruder.Update(-4)
		self.Extruder.Update(3)
		self.Extruder.Update(1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertTrue(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertTrue(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -4, 3, -1
		self.Extruder.Reset()
		self.Extruder.Update(-4)
		self.Extruder.Update(3)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertTrue(self.Extruder.IsRetracting)
		self.assertTrue(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)

		# -4, 0, 0
		self.Extruder.Reset()
		self.Extruder.Update(-4)
		self.Extruder.Update(0)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -4, 0, 1
		self.Extruder.Reset()
		self.Extruder.Update(-4)
		self.Extruder.Update(0)
		self.Extruder.Update(1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertTrue(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -4, 0, -1
		self.Extruder.Reset()
		self.Extruder.Update(-4)
		self.Extruder.Update(0)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertTrue(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)

		# -4,-1, 0
		self.Extruder.Reset()
		self.Extruder.Update(-4)
		self.Extruder.Update(-1)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -4,-1, 1
		self.Extruder.Reset()
		self.Extruder.Update(-4)
		self.Extruder.Update(-1)
		self.Extruder.Update(1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertTrue(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -4,-1, -1
		self.Extruder.Reset()
		self.Extruder.Update(-4)
		self.Extruder.Update(-1)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertTrue(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		########################################################
		# -5
		########################################################
		# -5, 6, 0
		self.Extruder.Reset()
		self.Extruder.Update(-5)
		self.Extruder.Update(6)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertTrue(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -5, 6, 1
		self.Extruder.Reset()
		self.Extruder.Update(-5)
		self.Extruder.Update(6)
		self.Extruder.Update(1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertTrue(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -5, 6, -1
		self.Extruder.Reset()
		self.Extruder.Update(-5)
		self.Extruder.Update(6)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertTrue(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)

		# -5, 5, 0
		self.Extruder.Reset()
		self.Extruder.Update(-5)
		self.Extruder.Update(5)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertTrue(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertTrue(self.Extruder.IsDetracted)
		# -5, 5, 1
		self.Extruder.Reset()
		self.Extruder.Update(-5)
		self.Extruder.Update(5)
		self.Extruder.Update(1)
		self.assertTrue(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertTrue(self.Extruder.IsDetracted)
		# -5, 5, -1
		self.Extruder.Reset()
		self.Extruder.Update(-5)
		self.Extruder.Update(5)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertTrue(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertTrue(self.Extruder.IsDetracted)

		# -5, 4, 0
		self.Extruder.Reset()
		self.Extruder.Update(-5)
		self.Extruder.Update(4)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertTrue(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -5, 4, 1
		self.Extruder.Reset()
		self.Extruder.Update(-5)
		self.Extruder.Update(4)
		self.Extruder.Update(1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertTrue(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertTrue(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -5, 4, -1
		self.Extruder.Reset()
		self.Extruder.Update(-5)
		self.Extruder.Update(4)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertTrue(self.Extruder.IsRetracting)
		self.assertTrue(self.Extruder.IsPartiallyRetracted)
		self.assertFalse(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)

		# -5, 1, 0
		self.Extruder.Reset()
		self.Extruder.Update(-5)
		self.Extruder.Update(1)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -5, 1, 1
		self.Extruder.Reset()
		self.Extruder.Update(-5)
		self.Extruder.Update(1)
		self.Extruder.Update(1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertTrue(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -5, 1, -1
		self.Extruder.Reset()
		self.Extruder.Update(-5)
		self.Extruder.Update(1)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertTrue(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)

		# -5, 0, 0
		self.Extruder.Reset()
		self.Extruder.Update(-5)
		self.Extruder.Update(0)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -5, 0, 1
		self.Extruder.Reset()
		self.Extruder.Update(-5)
		self.Extruder.Update(0)
		self.Extruder.Update(1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertTrue(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -5, 0, -1
		self.Extruder.Reset()
		self.Extruder.Update(-5)
		self.Extruder.Update(0)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertTrue(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)

		# -5, -1, 0
		self.Extruder.Reset()
		self.Extruder.Update(-5)
		self.Extruder.Update(-1)
		self.Extruder.Update(0)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -5, -1, 1
		self.Extruder.Reset()
		self.Extruder.Update(-5)
		self.Extruder.Update(-1)
		self.Extruder.Update(1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertFalse(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertTrue(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)
		# -5, -1, -1
		self.Extruder.Reset()
		self.Extruder.Update(-5)
		self.Extruder.Update(-1)
		self.Extruder.Update(-1)
		self.assertFalse(self.Extruder.IsExtrudingStart)
		self.assertFalse(self.Extruder.IsExtruding)
		self.assertFalse(self.Extruder.IsPrimed)
		self.assertFalse(self.Extruder.IsRetractingStart)
		self.assertTrue(self.Extruder.IsRetracting)
		self.assertFalse(self.Extruder.IsPartiallyRetracted)
		self.assertTrue(self.Extruder.IsRetracted)
		self.assertFalse(self.Extruder.IsDetractingStart)
		self.assertFalse(self.Extruder.IsDetracting)
		self.assertFalse(self.Extruder.IsDetracted)

	def test_ExtruderStateTriggered(self):
		self.assertTrue(self.Extruder._ExtruderStateTriggered(None, False) is None)
		self.assertTrue(self.Extruder._ExtruderStateTriggered(None, True) is None)
		self.assertTrue(self.Extruder._ExtruderStateTriggered(True, False) is None)
		self.assertTrue(self.Extruder._ExtruderStateTriggered(True, True))
		self.assertTrue(self.Extruder._ExtruderStateTriggered(False, False) is None)
		self.assertFalse(self.Extruder._ExtruderStateTriggered(False, True))

	def test_extruderTriggers(self):
		"""Test the extruder triggers"""

		# test with no filters - should trigger
		self.Extruder.Reset()
		self.Extruder.IsPrimed = False  # turn this off so we don't have to account for this default state
		triggers = ExtruderTriggers(None, None, None, None, None, None, None, None, None, None)
		self.assertTrue(self.Extruder.IsTriggered(triggers))

		# test OnExtrudingStart - True Filter
		triggers = ExtruderTriggers(True, None, None, None, None, None, None, None, None, None)
		# test True with true filter
		self.Extruder.IsExtrudingStart = True
		self.Extruder.IsPrimed = False  # turn this off so we don't have to account for this default state
		self.assertTrue(self.Extruder.IsTriggered(triggers))
		# test False with True filter
		self.Extruder.IsExtrudingStart = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test OnExtrudingStart - False Filter
		triggers = ExtruderTriggers(False, None, None, None, None, None, None, None, None, None);
		# test True with False filter
		self.Extruder.IsExtrudingStart = True
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test False with False filter
		self.Extruder.IsExtrudingStart = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))

		# test onExtruding
		self.Extruder.Reset()
		triggers = ExtruderTriggers(None, True, None, None, None, None, None, None, None, None);
		# test True with true filter
		self.Extruder.IsExtruding = True
		self.Extruder.IsPrimed = False  # turn this off so we don't have to account for this default state
		self.assertTrue(self.Extruder.IsTriggered(triggers))
		# test False with True filter
		self.Extruder.IsExtruding = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test OnExtruding - False Filter
		triggers = ExtruderTriggers(None, False, None, None, None, None, None, None, None, None);
		# test True with False filter
		self.Extruder.IsExtruding = True
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test False with False filter
		self.Extruder.IsExtruding = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))

		# test OnPrimed
		self.Extruder.Reset()
		triggers = ExtruderTriggers(None, None, True, None, None, None, None, None, None, None);
		# test True with true filter
		self.Extruder.IsPrimed = True
		self.assertTrue(self.Extruder.IsTriggered(triggers))
		# test False with True filter
		self.Extruder.IsPrimed = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test OnPrimed - False Filter
		triggers = ExtruderTriggers(None, None, False, None, None, None, None, None, None, None);
		# test True with False filter
		self.Extruder.IsPrimed = True
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test False with False filter
		self.Extruder.IsPrimed = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))

		# test OnRetractingStart
		self.Extruder.Reset()
		triggers = ExtruderTriggers(None, None, None, True, None, None, None, None, None, None);
		# test True with true filter
		self.Extruder.IsRetractingStart = True
		self.Extruder.IsPrimed = False  # turn this off so we don't have to account for this default state
		self.assertTrue(self.Extruder.IsTriggered(triggers))
		# test False with True filter
		self.Extruder.IsRetractingStart = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test OnRetractingStart - False Filter
		triggers = ExtruderTriggers(None, None, None, False, None, None, None, None, None, None);
		# test True with False filter
		self.Extruder.IsRetractingStart = True
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test False with False filter
		self.Extruder.IsRetractingStart = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))

		# test OnRetracting
		self.Extruder.Reset()
		triggers = ExtruderTriggers(None, None, None, None, True, None, None, None, None, None);
		# test True with true filter
		self.Extruder.IsRetracting = True
		self.Extruder.IsPrimed = False  # turn this off so we don't have to account for this default state
		self.assertTrue(self.Extruder.IsTriggered(triggers))
		# test False with True filter
		self.Extruder.IsRetracting = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test OnRetracting - False Filter
		triggers = ExtruderTriggers(None, None, None, None, False, None, None, None, None, None);
		# test True with False filter
		self.Extruder.IsRetracting = True
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test False with False filter
		self.Extruder.IsRetracting = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))

		# test OnPartiallyRetracted
		self.Extruder.Reset()
		triggers = ExtruderTriggers(None, None, None, None, None, True, None, None, None, None);
		# test True with true filter
		self.Extruder.IsPartiallyRetracted = True
		self.Extruder.IsPrimed = False  # turn this off so we don't have to account for this default state
		self.assertTrue(self.Extruder.IsTriggered(triggers))
		# test False with True filter
		self.Extruder.IsPartiallyRetracted = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test OnPartiallyRetracted - False Filter
		triggers = ExtruderTriggers(None, None, None, None, None, False, None, None, None, None);
		# test True with False filter
		self.Extruder.IsPartiallyRetracted = True
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test False with False filter
		self.Extruder.IsPartiallyRetracted = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))

		# test OnRetracted
		self.Extruder.Reset()
		triggers = ExtruderTriggers(None, None, None, None, None, None, True, None, None, None);
		# test True with true filter
		self.Extruder.IsRetracted = True
		self.Extruder.IsPrimed = False  # turn this off so we don't have to account for this default state
		self.assertTrue(self.Extruder.IsTriggered(triggers))
		# test False with True filter
		self.Extruder.IsRetracted = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test OnRetracted - False Filter
		triggers = ExtruderTriggers(None, None, None, None, None, None, False, None, None, None);
		# test True with False filter
		self.Extruder.IsRetracted = True
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test False with False filter
		self.Extruder.IsRetracted = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))

		# test OnDetractingStart
		self.Extruder.Reset()
		triggers = ExtruderTriggers(None, None, None, None, None, None, None, True, None, None);
		# test True with true filter
		self.Extruder.IsDetractingStart = True
		self.Extruder.IsPrimed = False  # turn this off so we don't have to account for this default state
		self.assertTrue(self.Extruder.IsTriggered(triggers))
		# test False with True filter
		self.Extruder.IsDetractingStart = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test OnDetractingStart - False Filter
		triggers = ExtruderTriggers(None, None, None, None, None, None, None, False, None, None);
		# test True with False filter
		self.Extruder.IsDetractingStart = True
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test False with False filter
		self.Extruder.IsDetractingStart = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))

		# test OnDetracting
		self.Extruder.Reset()
		triggers = ExtruderTriggers(None, None, None, None, None, None, None, None, True, None);
		# test True with true filter
		self.Extruder.IsDetracting = True
		self.Extruder.IsPrimed = False  # turn this off so we don't have to account for this default state
		self.assertTrue(self.Extruder.IsTriggered(triggers))
		# test False with True filter
		self.Extruder.IsDetracting = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test OnDetracting - False Filter
		triggers = ExtruderTriggers(None, None, None, None, None, None, None, None, False, None);
		# test True with False filter
		self.Extruder.IsDetracting = True
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test False with False filter
		self.Extruder.IsDetracting = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))

		# test OnDetracted
		self.Extruder.Reset()
		triggers = ExtruderTriggers(None, None, None, None, None, None, None, None, None, True);
		# test True with true filter
		self.Extruder.IsDetracted = True
		self.Extruder.IsPrimed = False  # turn this off so we don't have to account for this default state
		self.assertTrue(self.Extruder.IsTriggered(triggers))
		# test False with True filter
		self.Extruder.IsDetracted = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test OnDetracted - False Filter
		triggers = ExtruderTriggers(None, None, None, None, None, None, None, None, None, False);
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
		triggers = ExtruderTriggers(None, None, None, None, None, None, None, None, None, False);
		# test True with False filter
		self.Extruder.IsDetracted = True
		self.assertTrue(not self.Extruder.IsTriggered(triggers))
		# test False with False filter
		self.Extruder.IsDetracted = False
		self.assertTrue(not self.Extruder.IsTriggered(triggers))

		# Test mixed nones, trues and flases
		self.Extruder.Reset()
		triggers = ExtruderTriggers(None, True, False, None, True, False, None, True, False, None);
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
		triggers = ExtruderTriggers(None, None, None, None, None, None, None, None, None, None);
		self.assertTrue(self.Extruder.IsTriggered(triggers))
		triggers = ExtruderTriggers(False, True, True, True, True, True, True, True, True, True);
		self.assertFalse(self.Extruder.IsTriggered(triggers))
		triggers = ExtruderTriggers(True, False, True, True, True, True, True, True, True, True);
		self.assertFalse(self.Extruder.IsTriggered(triggers))
		triggers = ExtruderTriggers(True, True, False, True, True, True, True, True, True, True);
		self.assertFalse(self.Extruder.IsTriggered(triggers))
		triggers = ExtruderTriggers(True, True, True, False, True, True, True, True, True, True);
		self.assertFalse(self.Extruder.IsTriggered(triggers))
		triggers = ExtruderTriggers(True, True, True, True, False, True, True, True, True, True);
		self.assertFalse(self.Extruder.IsTriggered(triggers))
		triggers = ExtruderTriggers(True, True, True, True, True, False, True, True, True, True);
		self.assertFalse(self.Extruder.IsTriggered(triggers))
		triggers = ExtruderTriggers(True, True, True, True, True, True, False, True, True, True);
		self.assertFalse(self.Extruder.IsTriggered(triggers))
		triggers = ExtruderTriggers(True, True, True, True, True, True, True, False, True, True);
		self.assertFalse(self.Extruder.IsTriggered(triggers))
		triggers = ExtruderTriggers(True, True, True, True, True, True, True, True, False, True);
		self.assertFalse(self.Extruder.IsTriggered(triggers))
		triggers = ExtruderTriggers(True, True, True, True, True, True, True, True, True, False);
		self.assertFalse(self.Extruder.IsTriggered(triggers))


if __name__ == '__main__':
	suite = unittest.TestLoader().loadTestsFromTestCase(Test_Extruder)
  unittest.TextTestRunner(verbosity=3).run(suite)