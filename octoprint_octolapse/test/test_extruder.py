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

from octoprint_octolapse.extruder import Extruder, ExtruderTriggers, ExtruderState
from octoprint_octolapse.settings import OctolapseSettings


class TestExtruder(unittest.TestCase):
    def setUp(self):
        self.Settings = OctolapseSettings(NamedTemporaryFile().name)
        self.Extruder = Extruder(self.Settings)
        # set the retraction distance
        self.Extruder.PrinterRetractionLength = 4

    @staticmethod
    def create_octoprint_printer_profile():
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
        self.Extruder.add_state(state1)

        state2 = ExtruderState()
        self.Extruder.add_state(state2)

        state3 = ExtruderState()
        self.Extruder.add_state(state3)

        # check the length of StateHistory
        self.assertEquals(len(self.Extruder.StateHistory), 4)

        # reset the state and check again
        self.Extruder.reset()
        self.assertEquals(len(self.Extruder.StateHistory), 0)

    def test_ExtruderState_InitialValues(self):
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

    def test_ExtruderStateCopy(self):
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
        new_state = ExtruderState(state)
        # verify the state was copied correctly
        self.assertEquals(new_state.E, 1)
        self.assertEquals(new_state.ExtrusionLength, 100)
        self.assertEquals(new_state.ExtrusionLengthTotal, 200)
        self.assertEquals(new_state.RetractionLength, 300)
        self.assertEquals(new_state.DetractionLength, 400)
        self.assertTrue(new_state.IsExtrudingStart)
        self.assertTrue(new_state.IsExtruding)
        self.assertTrue(new_state.IsPrimed)
        self.assertTrue(new_state.IsRetractingStart)
        self.assertTrue(new_state.IsRetracting)
        self.assertTrue(new_state.IsPartiallyRetracted)
        self.assertTrue(new_state.IsRetracted)
        self.assertTrue(new_state.IsDetractingStart)
        self.assertTrue(new_state.IsDetracting)
        self.assertTrue(new_state.IsDetracted)
        self.assertTrue(new_state.HasChanged)

    def test_HasChanged(self):
        """Test the HasChanged flag"""
        # test the initial state
        self.assertFalse(self.Extruder.has_changed())
        # test updating with no movement - Change to primed
        self.Extruder.update(0)
        self.assertTrue(self.Extruder.has_changed())

        # test updating with no movement
        self.Extruder.update(0)
        self.assertFalse(self.Extruder.has_changed())

        # test updating with movement
        self.Extruder.update(1)
        self.assertTrue(self.Extruder.has_changed())
        # test updating with no movement
        self.Extruder.update(0)
        self.assertTrue(self.Extruder.has_changed())
        # test updating with slight movement
        self.Extruder.update(.0001)
        self.assertTrue(self.Extruder.has_changed())
        # test updating with slight movement
        self.Extruder.update(.0001)
        self.assertTrue(self.Extruder.has_changed())
        # test updating with slight movement
        self.Extruder.update(.01)
        self.assertFalse(self.Extruder.has_changed())
        # test updating with slight movement
        self.Extruder.update(.01)
        self.assertFalse(self.Extruder.has_changed())
        # test updating with no movement
        self.Extruder.update(0)
        self.assertTrue(self.Extruder.has_changed())
        # test updating with no movement, IsPrimed changed from 0 to 1
        self.Extruder.update(0)
        self.assertFalse(self.Extruder.has_changed())
        # test updating with no movement
        self.Extruder.update(0)
        self.assertFalse(self.Extruder.has_changed())
        # test updating with slight negative movement
        self.Extruder.update(-0.01)
        self.assertTrue(self.Extruder.has_changed())

    def test_ExtruderStates_Initial(self):
        """Test the All Extruder States"""

        # test the initial state
        self.assertFalse(self.Extruder.is_extruding_start())
        self.assertFalse(self.Extruder.is_extruding())
        self.assertFalse(self.Extruder.is_primed())
        self.assertFalse(self.Extruder.is_retracting_start())
        self.assertFalse(self.Extruder.is_retracting())
        self.assertFalse(self.Extruder.is_partially_retracted())
        self.assertFalse(self.Extruder.is_retracted())
        self.assertFalse(self.Extruder.is_detracting_start())
        self.assertFalse(self.Extruder.is_detracting())
        self.assertFalse(self.Extruder.is_detracted())

    def test_ExtruderStates_FromExtruding(self):
        # 1, 0 - From extruding to primed
        self.Extruder.reset()
        self.Extruder.update(1)
        self.Extruder.update(0)
        self.assertFalse(self.Extruder.is_extruding_start())
        self.assertFalse(self.Extruder.is_extruding())
        self.assertTrue(self.Extruder.is_primed())
        self.assertFalse(self.Extruder.is_retracting_start())
        self.assertFalse(self.Extruder.is_retracting())
        self.assertFalse(self.Extruder.is_partially_retracted())
        self.assertFalse(self.Extruder.is_retracted())
        self.assertFalse(self.Extruder.is_detracting_start())
        self.assertFalse(self.Extruder.is_detracting())
        self.assertFalse(self.Extruder.is_detracted())
        # 1, 1 - keep extruding
        self.Extruder.reset()
        self.Extruder.update(1)
        self.Extruder.update(1)
        self.assertFalse(self.Extruder.is_extruding_start())
        self.assertTrue(self.Extruder.is_extruding())
        self.assertFalse(self.Extruder.is_primed())
        self.assertFalse(self.Extruder.is_retracting_start())
        self.assertFalse(self.Extruder.is_retracting())
        self.assertFalse(self.Extruder.is_partially_retracted())
        self.assertFalse(self.Extruder.is_retracted())
        self.assertFalse(self.Extruder.is_detracting_start())
        self.assertFalse(self.Extruder.is_detracting())
        self.assertFalse(self.Extruder.is_detracted())
        # 1, -1 - from extruding to partially retracted
        self.Extruder.reset()
        self.Extruder.update(1)
        self.Extruder.update(-1)
        self.assertFalse(self.Extruder.is_extruding_start())
        self.assertFalse(self.Extruder.is_extruding())
        self.assertFalse(self.Extruder.is_primed())
        self.assertTrue(self.Extruder.is_retracting_start())
        self.assertTrue(self.Extruder.is_retracting())
        self.assertTrue(self.Extruder.is_partially_retracted())
        self.assertFalse(self.Extruder.is_retracted())
        self.assertFalse(self.Extruder.is_detracting_start())
        self.assertFalse(self.Extruder.is_detracting())
        self.assertFalse(self.Extruder.is_detracted())

        # 1, -4 - from extruding to fully retracted
        self.Extruder.reset()
        self.Extruder.update(1)
        self.Extruder.update(-4)
        self.assertFalse(self.Extruder.is_extruding_start())
        self.assertFalse(self.Extruder.is_extruding())
        self.assertFalse(self.Extruder.is_primed())
        self.assertTrue(self.Extruder.is_retracting_start())
        self.assertTrue(self.Extruder.is_retracting())
        self.assertFalse(self.Extruder.is_partially_retracted())
        self.assertTrue(self.Extruder.is_retracted())
        self.assertFalse(self.Extruder.is_detracting_start())
        self.assertFalse(self.Extruder.is_detracting())
        self.assertFalse(self.Extruder.is_detracted())

        # 1, -5 - from extruding to beyond fully retracted
        self.Extruder.reset()
        self.Extruder.update(1)
        self.Extruder.update(-5)
        self.assertFalse(self.Extruder.is_extruding_start())
        self.assertFalse(self.Extruder.is_extruding())
        self.assertFalse(self.Extruder.is_primed())
        self.assertTrue(self.Extruder.is_retracting_start())
        self.assertTrue(self.Extruder.is_retracting())
        self.assertFalse(self.Extruder.is_partially_retracted())
        self.assertTrue(self.Extruder.is_retracted())
        self.assertFalse(self.Extruder.is_detracting_start())
        self.assertFalse(self.Extruder.is_detracting())
        self.assertFalse(self.Extruder.is_detracted())

    def test_ExtruderStates_FromPrimed(self):
        # 0, 0 - remain primed
        self.Extruder.reset()
        self.Extruder.update(0)
        self.Extruder.update(0)
        self.assertFalse(self.Extruder.is_extruding_start())
        self.assertFalse(self.Extruder.is_extruding())
        self.assertTrue(self.Extruder.is_primed())
        self.assertFalse(self.Extruder.is_retracting_start())
        self.assertFalse(self.Extruder.is_retracting())
        self.assertFalse(self.Extruder.is_partially_retracted())
        self.assertFalse(self.Extruder.is_retracted())
        self.assertFalse(self.Extruder.is_detracting_start())
        self.assertFalse(self.Extruder.is_detracting())
        self.assertFalse(self.Extruder.is_detracted())

        # 0, 1 - from primed to extruding
        self.Extruder.reset()
        self.Extruder.update(0)
        self.Extruder.update(1)
        self.assertTrue(self.Extruder.is_extruding_start())
        self.assertTrue(self.Extruder.is_extruding())
        self.assertFalse(self.Extruder.is_primed())
        self.assertFalse(self.Extruder.is_retracting_start())
        self.assertFalse(self.Extruder.is_retracting())
        self.assertFalse(self.Extruder.is_partially_retracted())
        self.assertFalse(self.Extruder.is_retracted())
        self.assertFalse(self.Extruder.is_detracting_start())
        self.assertFalse(self.Extruder.is_detracting())
        self.assertFalse(self.Extruder.is_detracted())

        # 0, -1 - from primed to partially retracted
        self.Extruder.reset()
        self.Extruder.update(0)
        self.Extruder.update(-1)
        self.assertFalse(self.Extruder.is_extruding_start())
        self.assertFalse(self.Extruder.is_extruding())
        self.assertFalse(self.Extruder.is_primed())
        self.assertTrue(self.Extruder.is_retracting_start())
        self.assertTrue(self.Extruder.is_retracting())
        self.assertTrue(self.Extruder.is_partially_retracted())
        self.assertFalse(self.Extruder.is_retracted())
        self.assertFalse(self.Extruder.is_detracting_start())
        self.assertFalse(self.Extruder.is_detracting())
        self.assertFalse(self.Extruder.is_detracted())

        # 0, -4 - from primed to fully retracted
        self.Extruder.reset()
        self.Extruder.update(0)
        self.Extruder.update(-4)
        self.assertFalse(self.Extruder.is_extruding_start())
        self.assertFalse(self.Extruder.is_extruding())
        self.assertFalse(self.Extruder.is_primed())
        self.assertTrue(self.Extruder.is_retracting_start())
        self.assertTrue(self.Extruder.is_retracting())
        self.assertFalse(self.Extruder.is_partially_retracted())
        self.assertTrue(self.Extruder.is_retracted())
        self.assertFalse(self.Extruder.is_detracting_start())
        self.assertFalse(self.Extruder.is_detracting())
        self.assertFalse(self.Extruder.is_detracted())

        # 0, -5 - from primed to beyond fully retracted
        self.Extruder.reset()
        self.Extruder.update(0)
        self.Extruder.update(-5)
        self.assertFalse(self.Extruder.is_extruding_start())
        self.assertFalse(self.Extruder.is_extruding())
        self.assertFalse(self.Extruder.is_primed())
        self.assertTrue(self.Extruder.is_retracting_start())
        self.assertTrue(self.Extruder.is_retracting())
        self.assertFalse(self.Extruder.is_partially_retracted())
        self.assertTrue(self.Extruder.is_retracted())
        self.assertFalse(self.Extruder.is_detracting_start())
        self.assertFalse(self.Extruder.is_detracting())
        self.assertFalse(self.Extruder.is_detracted())

    def test_ExtruderStates_FromPartiallyRetracted(self):
        # -2,3 - from partially retracted to extruding
        self.Extruder.reset()
        self.Extruder.update(-2)
        self.Extruder.update(3)
        self.assertTrue(self.Extruder.is_extruding_start())
        self.assertTrue(self.Extruder.is_extruding())
        self.assertFalse(self.Extruder.is_primed())
        self.assertFalse(self.Extruder.is_retracting_start())
        self.assertFalse(self.Extruder.is_retracting())
        self.assertFalse(self.Extruder.is_partially_retracted())
        self.assertFalse(self.Extruder.is_retracted())
        self.assertTrue(self.Extruder.is_detracting_start())
        self.assertTrue(self.Extruder.is_detracting())
        self.assertTrue(self.Extruder.is_detracted())
        # -2,2 - detract
        self.Extruder.reset()
        self.Extruder.update(-2)
        self.Extruder.update(2)
        self.assertFalse(self.Extruder.is_extruding_start())
        self.assertFalse(self.Extruder.is_extruding())
        self.assertTrue(self.Extruder.is_primed())
        self.assertFalse(self.Extruder.is_retracting_start())
        self.assertFalse(self.Extruder.is_retracting())
        self.assertFalse(self.Extruder.is_partially_retracted())
        self.assertFalse(self.Extruder.is_retracted())
        self.assertTrue(self.Extruder.is_detracting_start())
        self.assertTrue(self.Extruder.is_detracting())
        self.assertTrue(self.Extruder.is_detracted())
        # -2,1 - detract from partially retracted to partially retracted
        self.Extruder.reset()
        self.Extruder.update(-2)
        self.Extruder.update(1)
        self.assertFalse(self.Extruder.is_extruding_start())
        self.assertFalse(self.Extruder.is_extruding())
        self.assertFalse(self.Extruder.is_primed())
        self.assertFalse(self.Extruder.is_retracting_start())
        self.assertFalse(self.Extruder.is_retracting())
        self.assertTrue(self.Extruder.is_partially_retracted())
        self.assertFalse(self.Extruder.is_retracted())
        self.assertTrue(self.Extruder.is_detracting_start())
        self.assertTrue(self.Extruder.is_detracting())
        self.assertFalse(self.Extruder.is_detracted())

        # -2, 0 - remain partially retracted
        self.Extruder.reset()
        self.Extruder.update(-2)
        self.Extruder.update(0)
        self.assertFalse(self.Extruder.is_extruding_start())
        self.assertFalse(self.Extruder.is_extruding())
        self.assertFalse(self.Extruder.is_primed())
        self.assertFalse(self.Extruder.is_retracting_start())
        self.assertFalse(self.Extruder.is_retracting())
        self.assertTrue(self.Extruder.is_partially_retracted())
        self.assertFalse(self.Extruder.is_retracted())
        self.assertFalse(self.Extruder.is_detracting_start())
        self.assertFalse(self.Extruder.is_detracting())
        self.assertFalse(self.Extruder.is_detracted())

        # -2,-1 - retract from partially retracted to partially retracted
        self.Extruder.reset()
        self.Extruder.update(-2)
        self.Extruder.update(-1)
        self.assertFalse(self.Extruder.is_extruding_start())
        self.assertFalse(self.Extruder.is_extruding())
        self.assertFalse(self.Extruder.is_primed())
        self.assertFalse(self.Extruder.is_retracting_start())
        self.assertTrue(self.Extruder.is_retracting())
        self.assertTrue(self.Extruder.is_partially_retracted())
        self.assertFalse(self.Extruder.is_retracted())
        self.assertFalse(self.Extruder.is_detracting_start())
        self.assertFalse(self.Extruder.is_detracting())
        self.assertFalse(self.Extruder.is_detracted())

        # -2,-2 - from partially retracted to fully retracted
        self.Extruder.reset()
        self.Extruder.update(-2)
        self.Extruder.update(-2)
        self.assertFalse(self.Extruder.is_extruding_start())
        self.assertFalse(self.Extruder.is_extruding())
        self.assertFalse(self.Extruder.is_primed())
        self.assertFalse(self.Extruder.is_retracting_start())
        self.assertTrue(self.Extruder.is_retracting())
        self.assertFalse(self.Extruder.is_partially_retracted())
        self.assertTrue(self.Extruder.is_retracted())
        self.assertFalse(self.Extruder.is_detracting_start())
        self.assertFalse(self.Extruder.is_detracting())
        self.assertFalse(self.Extruder.is_detracted())

        # -2,-3 - from partially retracted to beyond partially retracted
        self.Extruder.reset()
        self.Extruder.update(-2)
        self.Extruder.update(-3)
        self.assertFalse(self.Extruder.is_extruding_start())
        self.assertFalse(self.Extruder.is_extruding())
        self.assertFalse(self.Extruder.is_primed())
        self.assertFalse(self.Extruder.is_retracting_start())
        self.assertTrue(self.Extruder.is_retracting())
        self.assertFalse(self.Extruder.is_partially_retracted())
        self.assertTrue(self.Extruder.is_retracted())
        self.assertFalse(self.Extruder.is_detracting_start())
        self.assertFalse(self.Extruder.is_detracting())
        self.assertFalse(self.Extruder.is_detracted())

    def test_ExtruderStates_FromFullyRetracted(self):
        # -4,5 - Fully Retracted To Extruding
        self.Extruder.reset()
        self.Extruder.update(-4)
        self.Extruder.update(5)
        self.assertTrue(self.Extruder.is_extruding_start())
        self.assertTrue(self.Extruder.is_extruding())
        self.assertFalse(self.Extruder.is_primed())
        self.assertFalse(self.Extruder.is_retracting_start())
        self.assertFalse(self.Extruder.is_retracting())
        self.assertFalse(self.Extruder.is_partially_retracted())
        self.assertFalse(self.Extruder.is_retracted())
        self.assertTrue(self.Extruder.is_detracting_start())
        self.assertTrue(self.Extruder.is_detracting())
        self.assertTrue(self.Extruder.is_detracted())

        # -4,4 - Fully Retracted to Primed/Detracted
        self.Extruder.reset()
        self.Extruder.update(-4)
        self.Extruder.update(4)
        self.assertFalse(self.Extruder.is_extruding_start())
        self.assertFalse(self.Extruder.is_extruding())
        self.assertTrue(self.Extruder.is_primed())
        self.assertFalse(self.Extruder.is_retracting_start())
        self.assertFalse(self.Extruder.is_retracting())
        self.assertFalse(self.Extruder.is_partially_retracted())
        self.assertFalse(self.Extruder.is_retracted())
        self.assertTrue(self.Extruder.is_detracting_start())
        self.assertTrue(self.Extruder.is_detracting())
        self.assertTrue(self.Extruder.is_detracted())

        # -4,1 - Fully Retracted to Partially Retracted
        self.Extruder.reset()
        self.Extruder.update(-4)
        self.Extruder.update(1)
        self.assertFalse(self.Extruder.is_extruding_start())
        self.assertFalse(self.Extruder.is_extruding())
        self.assertFalse(self.Extruder.is_primed())
        self.assertFalse(self.Extruder.is_retracting_start())
        self.assertFalse(self.Extruder.is_retracting())
        self.assertTrue(self.Extruder.is_partially_retracted())
        self.assertFalse(self.Extruder.is_retracted())
        self.assertTrue(self.Extruder.is_detracting_start())
        self.assertTrue(self.Extruder.is_detracting())
        self.assertFalse(self.Extruder.is_detracted())

        # -4,0 - Remain Fully Retracted
        self.Extruder.reset()
        self.Extruder.update(-4)
        self.Extruder.update(0)
        self.assertFalse(self.Extruder.is_extruding_start())
        self.assertFalse(self.Extruder.is_extruding())
        self.assertFalse(self.Extruder.is_primed())
        self.assertFalse(self.Extruder.is_retracting_start())
        self.assertFalse(self.Extruder.is_retracting())
        self.assertFalse(self.Extruder.is_partially_retracted())
        self.assertTrue(self.Extruder.is_retracted())
        self.assertFalse(self.Extruder.is_detracting_start())
        self.assertFalse(self.Extruder.is_detracting())
        self.assertFalse(self.Extruder.is_detracted())

        # -4,-1 - Fully Retracted, Continue Retracting
        self.Extruder.reset()
        self.Extruder.update(-4)
        self.Extruder.update(-1)
        self.assertFalse(self.Extruder.is_extruding_start())
        self.assertFalse(self.Extruder.is_extruding())
        self.assertFalse(self.Extruder.is_primed())
        self.assertFalse(self.Extruder.is_retracting_start())
        self.assertTrue(self.Extruder.is_retracting())
        self.assertFalse(self.Extruder.is_partially_retracted())
        self.assertTrue(self.Extruder.is_retracted())
        self.assertFalse(self.Extruder.is_detracting_start())
        self.assertFalse(self.Extruder.is_detracting())
        self.assertFalse(self.Extruder.is_detracted())

    def test_ExtruderStates_FromBeyondFullyRetracted(self):
        # -5,6 - Beyond fully retracted to extruding
        self.Extruder.reset()
        self.Extruder.update(-5)
        self.Extruder.update(6)
        self.assertTrue(self.Extruder.is_extruding_start())
        self.assertTrue(self.Extruder.is_extruding())
        self.assertFalse(self.Extruder.is_primed())
        self.assertFalse(self.Extruder.is_retracting_start())
        self.assertFalse(self.Extruder.is_retracting())
        self.assertFalse(self.Extruder.is_partially_retracted())
        self.assertFalse(self.Extruder.is_retracted())
        self.assertTrue(self.Extruder.is_detracting_start())
        self.assertTrue(self.Extruder.is_detracting())
        self.assertTrue(self.Extruder.is_detracted())

        # -5,5 - Beyond fully retracted to primed/detracted
        self.Extruder.reset()
        self.Extruder.update(-5)
        self.Extruder.update(5)
        self.assertFalse(self.Extruder.is_extruding_start())
        self.assertFalse(self.Extruder.is_extruding())
        self.assertTrue(self.Extruder.is_primed())
        self.assertFalse(self.Extruder.is_retracting_start())
        self.assertFalse(self.Extruder.is_retracting())
        self.assertFalse(self.Extruder.is_partially_retracted())
        self.assertFalse(self.Extruder.is_retracted())
        self.assertTrue(self.Extruder.is_detracting_start())
        self.assertTrue(self.Extruder.is_detracting())
        self.assertTrue(self.Extruder.is_detracted())

        # -5,4 - Beyond fully retracted to partially retracted
        self.Extruder.reset()
        self.Extruder.update(-5)
        self.Extruder.update(4)
        self.assertFalse(self.Extruder.is_extruding_start())
        self.assertFalse(self.Extruder.is_extruding())
        self.assertFalse(self.Extruder.is_primed())
        self.assertFalse(self.Extruder.is_retracting_start())
        self.assertFalse(self.Extruder.is_retracting())
        self.assertTrue(self.Extruder.is_partially_retracted())
        self.assertFalse(self.Extruder.is_retracted())
        self.assertTrue(self.Extruder.is_detracting_start())
        self.assertTrue(self.Extruder.is_detracting())
        self.assertFalse(self.Extruder.is_detracted())

        # -5,1 - Beyond fully retracted to fully retracted
        self.Extruder.reset()
        self.Extruder.update(-5)
        self.Extruder.update(1)
        self.assertFalse(self.Extruder.is_extruding_start())
        self.assertFalse(self.Extruder.is_extruding())
        self.assertFalse(self.Extruder.is_primed())
        self.assertFalse(self.Extruder.is_retracting_start())
        self.assertFalse(self.Extruder.is_retracting())
        self.assertFalse(self.Extruder.is_partially_retracted())
        self.assertTrue(self.Extruder.is_retracted())
        self.assertTrue(self.Extruder.is_detracting_start())
        self.assertTrue(self.Extruder.is_detracting())
        self.assertFalse(self.Extruder.is_detracted())

        # -5,0 - Remain beyond fully retracted
        self.Extruder.reset()
        self.Extruder.update(-5)
        self.Extruder.update(0)
        self.assertFalse(self.Extruder.is_extruding_start())
        self.assertFalse(self.Extruder.is_extruding())
        self.assertFalse(self.Extruder.is_primed())
        self.assertFalse(self.Extruder.is_retracting_start())
        self.assertFalse(self.Extruder.is_retracting())
        self.assertFalse(self.Extruder.is_partially_retracted())
        self.assertTrue(self.Extruder.is_retracted())
        self.assertFalse(self.Extruder.is_detracting_start())
        self.assertFalse(self.Extruder.is_detracting())
        self.assertFalse(self.Extruder.is_detracted())

        # -5, -1 - Beyond fully retracted, continuing to retract
        self.Extruder.reset()
        self.Extruder.update(-5)
        self.Extruder.update(-1)
        self.assertFalse(self.Extruder.is_extruding_start())
        self.assertFalse(self.Extruder.is_extruding())
        self.assertFalse(self.Extruder.is_primed())
        self.assertFalse(self.Extruder.is_retracting_start())
        self.assertTrue(self.Extruder.is_retracting())
        self.assertFalse(self.Extruder.is_partially_retracted())
        self.assertTrue(self.Extruder.is_retracted())
        self.assertFalse(self.Extruder.is_detracting_start())
        self.assertFalse(self.Extruder.is_detracting())
        self.assertFalse(self.Extruder.is_detracted())

    def test_ExtruderStateTriggered(self):
        self.assertTrue(self.Extruder._extruder_state_triggered(None, False) is None)
        self.assertTrue(self.Extruder._extruder_state_triggered(None, True) is None)
        self.assertTrue(self.Extruder._extruder_state_triggered(True, False) is None)
        self.assertTrue(self.Extruder._extruder_state_triggered(True, True))
        self.assertTrue(self.Extruder._extruder_state_triggered(False, False) is None)
        self.assertFalse(self.Extruder._extruder_state_triggered(False, True))

    def test_extruderTriggers_NoFilter(self):
        """Test the extruder triggers"""

        # test with no filters - should trigger
        self.Extruder.reset()
        state = ExtruderState()
        self.Extruder.add_state(state)
        state.IsPrimed = False  # turn this off so we don't have to account for this default state
        triggers = ExtruderTriggers(None, None, None, None, None, None, None, None, None, None)
        self.assertTrue(self.Extruder.is_triggered(triggers))

    def test_extruderTriggers_OnExtrudingStart(self):
        self.Extruder.reset()
        state = ExtruderState()
        self.Extruder.add_state(state)
        # test OnExtrudingStart - True Filter
        triggers = ExtruderTriggers(True, None, None, None, None, None, None, None, None, None)
        # test True with true filter
        state.IsExtrudingStart = True
        state.IsPrimed = False  # turn this off so we don't have to account for this default state
        self.assertTrue(self.Extruder.is_triggered(triggers))
        # test False with True filter
        state.IsExtrudingStart = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test OnExtrudingStart - False Filter
        triggers = ExtruderTriggers(False, None, None, None, None, None, None, None, None, None)
        # test True with False filter
        state.IsExtrudingStart = True
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test False with False filter
        state.IsExtrudingStart = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))

    def test_extruderTriggers_OnExtruding(self):
        # test onExtruding
        self.Extruder.reset()
        state = ExtruderState()
        self.Extruder.add_state(state)
        triggers = ExtruderTriggers(None, True, None, None, None, None, None, None, None, None)
        # test True with true filter
        state.IsExtruding = True
        state.IsPrimed = False  # turn this off so we don't have to account for this default state
        self.assertTrue(self.Extruder.is_triggered(triggers))
        # test False with True filter
        state.IsExtruding = False
        self.assertFalse(self.Extruder.is_triggered(triggers))
        # test OnExtruding - False Filter
        triggers = ExtruderTriggers(None, False, None, None, None, None, None, None, None, None)
        # test True with False filter
        state.IsExtruding = True
        self.assertFalse(self.Extruder.is_triggered(triggers))
        # test False with False filter
        state.IsExtruding = False
        self.assertFalse(self.Extruder.is_triggered(triggers))

    def test_extruderTriggers_OnPrimed(self):
        self.Extruder.reset()
        state = ExtruderState()
        self.Extruder.add_state(state)
        triggers = ExtruderTriggers(None, None, True, None, None, None, None, None, None, None)
        # test True with true filter
        state.IsPrimed = True
        self.assertTrue(self.Extruder.is_triggered(triggers))
        # test False with True filter
        state.IsPrimed = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test OnPrimed - False Filter
        triggers = ExtruderTriggers(None, None, False, None, None, None, None, None, None, None)
        # test True with False filter
        state.IsPrimed = True
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test False with False filter
        state.IsPrimed = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))

    def test_extruderTriggers_OnRetractingStart(self):
        # test OnRetractingStart
        self.Extruder.reset()
        state = ExtruderState()
        self.Extruder.add_state(state)
        triggers = ExtruderTriggers(None, None, None, True, None, None, None, None, None, None)
        # test True with true filter
        state.IsRetractingStart = True
        state.IsPrimed = False  # turn this off so we don't have to account for this default state
        self.assertTrue(self.Extruder.is_triggered(triggers))
        # test False with True filter
        state.IsRetractingStart = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test OnRetractingStart - False Filter
        triggers = ExtruderTriggers(None, None, None, False, None, None, None, None, None, None)
        # test True with False filter
        state.IsRetractingStart = True
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test False with False filter
        state.IsRetractingStart = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))

    def test_extruderTriggers_OnRetracting(self):
        # test OnRetracting
        self.Extruder.reset()
        state = ExtruderState()
        self.Extruder.add_state(state)
        triggers = ExtruderTriggers(None, None, None, None, True, None, None, None, None, None)
        # test True with true filter
        state.IsRetracting = True
        state.IsPrimed = False  # turn this off so we don't have to account for this default state
        self.assertTrue(self.Extruder.is_triggered(triggers))
        # test False with True filter
        state.IsRetracting = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test OnRetracting - False Filter
        triggers = ExtruderTriggers(None, None, None, None, False, None, None, None, None, None)
        # test True with False filter
        state.IsRetracting = True
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test False with False filter
        state.IsRetracting = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))

    def test_extruderTriggers_OnPartiallyRetracted(self):
        # test OnPartiallyRetracted
        self.Extruder.reset()
        state = ExtruderState()
        self.Extruder.add_state(state)
        triggers = ExtruderTriggers(None, None, None, None, None, True, None, None, None, None)
        # test True with true filter
        state.IsPartiallyRetracted = True
        state.IsPrimed = False  # turn this off so we don't have to account for this default state
        self.assertTrue(self.Extruder.is_triggered(triggers))
        # test False with True filter
        state.IsPartiallyRetracted = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test OnPartiallyRetracted - False Filter
        triggers = ExtruderTriggers(None, None, None, None, None, False, None, None, None, None)
        # test True with False filter
        state.IsPartiallyRetracted = True
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test False with False filter
        state.IsPartiallyRetracted = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))

    def test_extruderTriggers_OnRetracted(self):
        # test OnRetracted
        self.Extruder.reset()
        state = ExtruderState()
        self.Extruder.add_state(state)
        triggers = ExtruderTriggers(None, None, None, None, None, None, True, None, None, None)
        # test True with true filter
        state.IsRetracted = True
        state.IsPrimed = False  # turn this off so we don't have to account for this default state
        self.assertTrue(self.Extruder.is_triggered(triggers))
        # test False with True filter
        state.IsRetracted = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test OnRetracted - False Filter
        triggers = ExtruderTriggers(None, None, None, None, None, None, False, None, None, None)
        # test True with False filter
        state.IsRetracted = True
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test False with False filter
        state.IsRetracted = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))

    def test_extruderTriggers_OnDetractingStart(self):
        # test OnDetractingStart
        self.Extruder.reset()
        state = ExtruderState()
        self.Extruder.add_state(state)
        triggers = ExtruderTriggers(None, None, None, None, None, None, None, True, None, None)
        # test True with true filter
        state.IsDetractingStart = True
        state.IsPrimed = False  # turn this off so we don't have to account for this default state
        self.assertTrue(self.Extruder.is_triggered(triggers))
        # test False with True filter
        state.IsDetractingStart = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test OnDetractingStart - False Filter
        triggers = ExtruderTriggers(None, None, None, None, None, None, None, False, None, None)
        # test True with False filter
        state.IsDetractingStart = True
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test False with False filter
        state.IsDetractingStart = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))

    def test_extruderTriggers_OnDetracting(self):
        # test OnDetracting
        self.Extruder.reset()
        state = ExtruderState()
        self.Extruder.add_state(state)
        triggers = ExtruderTriggers(None, None, None, None, None, None, None, None, True, None)
        # test True with true filter
        state.IsDetracting = True
        state.IsPrimed = False  # turn this off so we don't have to account for this default state
        self.assertTrue(self.Extruder.is_triggered(triggers))
        # test False with True filter
        state.IsDetracting = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test OnDetracting - False Filter
        triggers = ExtruderTriggers(None, None, None, None, None, None, None, None, False, None)
        # test True with False filter
        state.IsDetracting = True
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test False with False filter
        state.IsDetracting = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))

    def test_extruderTriggers_OnDetracted(self):
        # test OnDetracted
        self.Extruder.reset()
        state = ExtruderState()
        self.Extruder.add_state(state)
        triggers = ExtruderTriggers(None, None, None, None, None, None, None, None, None, True)
        # test True with true filter
        state.IsDetracted = True
        state.IsPrimed = False  # turn this off so we don't have to account for this default state
        self.assertTrue(self.Extruder.is_triggered(triggers))
        # test False with True filter
        state.IsDetracted = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test OnDetracted - False Filter
        triggers = ExtruderTriggers(None, None, None, None, None, None, None, None, None, False)
        # test True with False filter
        state.IsDetracted = True
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test False with False filter
        state.IsDetracted = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))

    def test_extruderTriggers_Mixed(self):
        # Test mixed nones, trues and falses
        self.Extruder.reset()
        state = ExtruderState()
        self.Extruder.add_state(state)
        triggers = ExtruderTriggers(None, True, False, None, True, False, None, True, False, None)
        # Forbidden Due to IsPrimed
        state.IsExtrudingStart = True
        state.IsExtruding = True
        state.IsPrimed = True
        state.IsRetractingStart = True
        state.IsRetracting = True
        state.IsPartiallyRetracted = False
        state.IsRetracted = True
        state.IsDetractingStart = True
        state.IsDetracting = False
        state.IsDetracted = True
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # True - is extruding
        state.IsExtrudingStart = False
        state.IsExtruding = True
        state.IsPrimed = False
        state.IsRetractingStart = True
        state.IsRetracting = False
        state.IsPartiallyRetracted = False
        state.IsRetracted = True
        state.IsDetractingStart = False
        state.IsDetracting = False
        state.IsDetracted = True
        self.assertTrue(self.Extruder.is_triggered(triggers))

        # Test all false states and all Nones
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
        triggers = ExtruderTriggers(None, None, None, None, None, None, None, None, None, None)
        self.assertTrue(self.Extruder.is_triggered(triggers))
        triggers = ExtruderTriggers(False, True, True, True, True, True, True, True, True, True)
        self.assertFalse(self.Extruder.is_triggered(triggers))
        triggers = ExtruderTriggers(True, False, True, True, True, True, True, True, True, True)
        self.assertFalse(self.Extruder.is_triggered(triggers))
        triggers = ExtruderTriggers(True, True, False, True, True, True, True, True, True, True)
        self.assertFalse(self.Extruder.is_triggered(triggers))
        triggers = ExtruderTriggers(True, True, True, False, True, True, True, True, True, True)
        self.assertFalse(self.Extruder.is_triggered(triggers))
        triggers = ExtruderTriggers(True, True, True, True, False, True, True, True, True, True)
        self.assertFalse(self.Extruder.is_triggered(triggers))
        triggers = ExtruderTriggers(True, True, True, True, True, False, True, True, True, True)
        self.assertFalse(self.Extruder.is_triggered(triggers))
        triggers = ExtruderTriggers(True, True, True, True, True, True, False, True, True, True)
        self.assertFalse(self.Extruder.is_triggered(triggers))
        triggers = ExtruderTriggers(True, True, True, True, True, True, True, False, True, True)
        self.assertFalse(self.Extruder.is_triggered(triggers))
        triggers = ExtruderTriggers(True, True, True, True, True, True, True, True, False, True)
        self.assertFalse(self.Extruder.is_triggered(triggers))
        triggers = ExtruderTriggers(True, True, True, True, True, True, True, True, True, False)
        self.assertFalse(self.Extruder.is_triggered(triggers))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestExtruder)
    unittest.TextTestRunner(verbosity=3).run(suite)
