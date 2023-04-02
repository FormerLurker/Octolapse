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

from octoprint_octolapse.extruder import Extruder, ExtruderTriggers, ExtruderState
from octoprint_octolapse.settings import OctolapseSettings


class TestExtruder(unittest.TestCase):
    def setUp(self):
        self.Settings = OctolapseSettings(NamedTemporaryFile().name)
        self.Extruder = Extruder(self.Settings)
        # set the retraction distance
        self.Extruder.Printerretraction_length = 4

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
        self.assertEquals(state.extrusion_length, 0.0)
        self.assertEquals(state.extruder_length_total, 0.0)
        self.assertEquals(state.retraction_length, 0.0)
        self.assertEquals(state.deretraction_length, 0.0)
        self.assertFalse(state.is_extruding_start)
        self.assertFalse(state.is_extruding)
        self.assertFalse(state.is_primed)
        self.assertFalse(state.is_retracting_start)
        self.assertFalse(state.is_retracting)
        self.assertFalse(state.is_partially_retracted)
        self.assertFalse(state.is_retracted)
        self.assertFalse(state.is_deretracting_start)
        self.assertFalse(state.is_deretracting)
        self.assertFalse(state.is_deretracted)
        self.assertFalse(state.has_changed)

    def test_ExtruderStateCopy(self):
        # create a new state
        state = ExtruderState()
        # change all the default values

        state.E = 1
        state.extrusion_length = 100
        state.extruder_length_total = 200
        state.retraction_length = 300
        state.deretraction_length = 400
        state.is_extruding_start = True
        state.is_extruding = True
        state.is_primed = True
        state.is_retracting_start = True
        state.is_retracting = True
        state.is_partially_retracted = True
        state.is_retracted = True
        state.is_deretracting_start = True
        state.is_deretracting = True
        state.is_deretracted = True
        state.has_changed = True

        # copy to a new state
        new_state = ExtruderState(state)
        # verify the state was copied correctly
        self.assertEquals(new_state.E, 1)
        self.assertEquals(new_state.extrusion_length, 100)
        self.assertEquals(new_state.extruder_length_total, 200)
        self.assertEquals(new_state.retraction_length, 300)
        self.assertEquals(new_state.deretraction_length, 400)
        self.assertTrue(new_state.is_extruding_start)
        self.assertTrue(new_state.is_extruding)
        self.assertTrue(new_state.is_primed)
        self.assertTrue(new_state.is_retracting_start)
        self.assertTrue(new_state.is_retracting)
        self.assertTrue(new_state.is_partially_retracted)
        self.assertTrue(new_state.is_retracted)
        self.assertTrue(new_state.is_deretracting_start)
        self.assertTrue(new_state.is_deretracting)
        self.assertTrue(new_state.is_deretracted)
        self.assertTrue(new_state.has_changed)

    def test_has_changed(self):
        """Test the has_changed flag"""
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
        # test updating with no movement, is_primed changed from 0 to 1
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
        self.assertFalse(self.Extruder.is_deretracting_start())
        self.assertFalse(self.Extruder.is_deretracting())
        self.assertFalse(self.Extruder.is_deretracted())

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
        self.assertFalse(self.Extruder.is_deretracting_start())
        self.assertFalse(self.Extruder.is_deretracting())
        self.assertFalse(self.Extruder.is_deretracted())
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
        self.assertFalse(self.Extruder.is_deretracting_start())
        self.assertFalse(self.Extruder.is_deretracting())
        self.assertFalse(self.Extruder.is_deretracted())
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
        self.assertFalse(self.Extruder.is_deretracting_start())
        self.assertFalse(self.Extruder.is_deretracting())
        self.assertFalse(self.Extruder.is_deretracted())

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
        self.assertFalse(self.Extruder.is_deretracting_start())
        self.assertFalse(self.Extruder.is_deretracting())
        self.assertFalse(self.Extruder.is_deretracted())

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
        self.assertFalse(self.Extruder.is_deretracting_start())
        self.assertFalse(self.Extruder.is_deretracting())
        self.assertFalse(self.Extruder.is_deretracted())

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
        self.assertFalse(self.Extruder.is_deretracting_start())
        self.assertFalse(self.Extruder.is_deretracting())
        self.assertFalse(self.Extruder.is_deretracted())

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
        self.assertFalse(self.Extruder.is_deretracting_start())
        self.assertFalse(self.Extruder.is_deretracting())
        self.assertFalse(self.Extruder.is_deretracted())

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
        self.assertFalse(self.Extruder.is_deretracting_start())
        self.assertFalse(self.Extruder.is_deretracting())
        self.assertFalse(self.Extruder.is_deretracted())

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
        self.assertFalse(self.Extruder.is_deretracting_start())
        self.assertFalse(self.Extruder.is_deretracting())
        self.assertFalse(self.Extruder.is_deretracted())

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
        self.assertFalse(self.Extruder.is_deretracting_start())
        self.assertFalse(self.Extruder.is_deretracting())
        self.assertFalse(self.Extruder.is_deretracted())

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
        self.assertTrue(self.Extruder.is_deretracting_start())
        self.assertTrue(self.Extruder.is_deretracting())
        self.assertTrue(self.Extruder.is_deretracted())
        # -2,2 - deretract
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
        self.assertTrue(self.Extruder.is_deretracting_start())
        self.assertTrue(self.Extruder.is_deretracting())
        self.assertTrue(self.Extruder.is_deretracted())
        # -2,1 - deretract from partially retracted to partially retracted
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
        self.assertTrue(self.Extruder.is_deretracting_start())
        self.assertTrue(self.Extruder.is_deretracting())
        self.assertFalse(self.Extruder.is_deretracted())

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
        self.assertFalse(self.Extruder.is_deretracting_start())
        self.assertFalse(self.Extruder.is_deretracting())
        self.assertFalse(self.Extruder.is_deretracted())

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
        self.assertFalse(self.Extruder.is_deretracting_start())
        self.assertFalse(self.Extruder.is_deretracting())
        self.assertFalse(self.Extruder.is_deretracted())

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
        self.assertFalse(self.Extruder.is_deretracting_start())
        self.assertFalse(self.Extruder.is_deretracting())
        self.assertFalse(self.Extruder.is_deretracted())

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
        self.assertFalse(self.Extruder.is_deretracting_start())
        self.assertFalse(self.Extruder.is_deretracting())
        self.assertFalse(self.Extruder.is_deretracted())

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
        self.assertTrue(self.Extruder.is_deretracting_start())
        self.assertTrue(self.Extruder.is_deretracting())
        self.assertTrue(self.Extruder.is_deretracted())

        # -4,4 - Fully Retracted to Primed/Deretracted
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
        self.assertTrue(self.Extruder.is_deretracting_start())
        self.assertTrue(self.Extruder.is_deretracting())
        self.assertTrue(self.Extruder.is_deretracted())

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
        self.assertTrue(self.Extruder.is_deretracting_start())
        self.assertTrue(self.Extruder.is_deretracting())
        self.assertFalse(self.Extruder.is_deretracted())

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
        self.assertFalse(self.Extruder.is_deretracting_start())
        self.assertFalse(self.Extruder.is_deretracting())
        self.assertFalse(self.Extruder.is_deretracted())

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
        self.assertFalse(self.Extruder.is_deretracting_start())
        self.assertFalse(self.Extruder.is_deretracting())
        self.assertFalse(self.Extruder.is_deretracted())

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
        self.assertTrue(self.Extruder.is_deretracting_start())
        self.assertTrue(self.Extruder.is_deretracting())
        self.assertTrue(self.Extruder.is_deretracted())

        # -5,5 - Beyond fully retracted to primed/deretracted
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
        self.assertTrue(self.Extruder.is_deretracting_start())
        self.assertTrue(self.Extruder.is_deretracting())
        self.assertTrue(self.Extruder.is_deretracted())

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
        self.assertTrue(self.Extruder.is_deretracting_start())
        self.assertTrue(self.Extruder.is_deretracting())
        self.assertFalse(self.Extruder.is_deretracted())

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
        self.assertTrue(self.Extruder.is_deretracting_start())
        self.assertTrue(self.Extruder.is_deretracting())
        self.assertFalse(self.Extruder.is_deretracted())

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
        self.assertFalse(self.Extruder.is_deretracting_start())
        self.assertFalse(self.Extruder.is_deretracting())
        self.assertFalse(self.Extruder.is_deretracted())

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
        self.assertFalse(self.Extruder.is_deretracting_start())
        self.assertFalse(self.Extruder.is_deretracting())
        self.assertFalse(self.Extruder.is_deretracted())

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
        state.is_primed = False  # turn this off so we don't have to account for this default state
        triggers = ExtruderTriggers(None, None, None, None, None, None, None, None, None, None)
        self.assertTrue(self.Extruder.is_triggered(triggers))

    def test_extruderTriggers_on_extruding_start(self):
        self.Extruder.reset()
        state = ExtruderState()
        self.Extruder.add_state(state)
        # test on_extruding_start - True Filter
        triggers = ExtruderTriggers(True, None, None, None, None, None, None, None, None, None)
        # test True with true filter
        state.is_extruding_start = True
        state.is_primed = False  # turn this off so we don't have to account for this default state
        self.assertTrue(self.Extruder.is_triggered(triggers))
        # test False with True filter
        state.is_extruding_start = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test on_extruding_start - False Filter
        triggers = ExtruderTriggers(False, None, None, None, None, None, None, None, None, None)
        # test True with False filter
        state.is_extruding_start = True
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test False with False filter
        state.is_extruding_start = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))

    def test_extruderTriggers_on_extruding(self):
        # test onExtruding
        self.Extruder.reset()
        state = ExtruderState()
        self.Extruder.add_state(state)
        triggers = ExtruderTriggers(None, True, None, None, None, None, None, None, None, None)
        # test True with true filter
        state.is_extruding = True
        state.is_primed = False  # turn this off so we don't have to account for this default state
        self.assertTrue(self.Extruder.is_triggered(triggers))
        # test False with True filter
        state.is_extruding = False
        self.assertFalse(self.Extruder.is_triggered(triggers))
        # test on_extruding - False Filter
        triggers = ExtruderTriggers(None, False, None, None, None, None, None, None, None, None)
        # test True with False filter
        state.is_extruding = True
        self.assertFalse(self.Extruder.is_triggered(triggers))
        # test False with False filter
        state.is_extruding = False
        self.assertFalse(self.Extruder.is_triggered(triggers))

    def test_extruderTriggers_on_primed(self):
        self.Extruder.reset()
        state = ExtruderState()
        self.Extruder.add_state(state)
        triggers = ExtruderTriggers(None, None, True, None, None, None, None, None, None, None)
        # test True with true filter
        state.is_primed = True
        self.assertTrue(self.Extruder.is_triggered(triggers))
        # test False with True filter
        state.is_primed = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test on_primed - False Filter
        triggers = ExtruderTriggers(None, None, False, None, None, None, None, None, None, None)
        # test True with False filter
        state.is_primed = True
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test False with False filter
        state.is_primed = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))

    def test_extruderTriggers_on_retracting_start(self):
        # test on_retracting_start
        self.Extruder.reset()
        state = ExtruderState()
        self.Extruder.add_state(state)
        triggers = ExtruderTriggers(None, None, None, True, None, None, None, None, None, None)
        # test True with true filter
        state.is_retracting_start = True
        state.is_primed = False  # turn this off so we don't have to account for this default state
        self.assertTrue(self.Extruder.is_triggered(triggers))
        # test False with True filter
        state.is_retracting_start = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test on_retracting_start - False Filter
        triggers = ExtruderTriggers(None, None, None, False, None, None, None, None, None, None)
        # test True with False filter
        state.is_retracting_start = True
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test False with False filter
        state.is_retracting_start = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))

    def test_extruderTriggers_on_retracting(self):
        # test on_retracting
        self.Extruder.reset()
        state = ExtruderState()
        self.Extruder.add_state(state)
        triggers = ExtruderTriggers(None, None, None, None, True, None, None, None, None, None)
        # test True with true filter
        state.is_retracting = True
        state.is_primed = False  # turn this off so we don't have to account for this default state
        self.assertTrue(self.Extruder.is_triggered(triggers))
        # test False with True filter
        state.is_retracting = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test on_retracting - False Filter
        triggers = ExtruderTriggers(None, None, None, None, False, None, None, None, None, None)
        # test True with False filter
        state.is_retracting = True
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test False with False filter
        state.is_retracting = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))

    def test_extruderTriggers_on_partially_retracted(self):
        # test on_partially_retracted
        self.Extruder.reset()
        state = ExtruderState()
        self.Extruder.add_state(state)
        triggers = ExtruderTriggers(None, None, None, None, None, True, None, None, None, None)
        # test True with true filter
        state.is_partially_retracted = True
        state.is_primed = False  # turn this off so we don't have to account for this default state
        self.assertTrue(self.Extruder.is_triggered(triggers))
        # test False with True filter
        state.is_partially_retracted = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test on_partially_retracted - False Filter
        triggers = ExtruderTriggers(None, None, None, None, None, False, None, None, None, None)
        # test True with False filter
        state.is_partially_retracted = True
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test False with False filter
        state.is_partially_retracted = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))

    def test_extruderTriggers_on_retracted(self):
        # test on_retracted
        self.Extruder.reset()
        state = ExtruderState()
        self.Extruder.add_state(state)
        triggers = ExtruderTriggers(None, None, None, None, None, None, True, None, None, None)
        # test True with true filter
        state.is_retracted = True
        state.is_primed = False  # turn this off so we don't have to account for this default state
        self.assertTrue(self.Extruder.is_triggered(triggers))
        # test False with True filter
        state.is_retracted = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test on_retracted - False Filter
        triggers = ExtruderTriggers(None, None, None, None, None, None, False, None, None, None)
        # test True with False filter
        state.is_retracted = True
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test False with False filter
        state.is_retracted = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))

    def test_extruderTriggers_on_deretracting_start(self):
        # test on_deretracting_start
        self.Extruder.reset()
        state = ExtruderState()
        self.Extruder.add_state(state)
        triggers = ExtruderTriggers(None, None, None, None, None, None, None, True, None, None)
        # test True with true filter
        state.is_deretracting_start = True
        state.is_primed = False  # turn this off so we don't have to account for this default state
        self.assertTrue(self.Extruder.is_triggered(triggers))
        # test False with True filter
        state.is_deretracting_start = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test on_deretracting_start - False Filter
        triggers = ExtruderTriggers(None, None, None, None, None, None, None, False, None, None)
        # test True with False filter
        state.is_deretracting_start = True
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test False with False filter
        state.is_deretracting_start = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))

    def test_extruderTriggers_on_deretracting(self):
        # test on_deretracting
        self.Extruder.reset()
        state = ExtruderState()
        self.Extruder.add_state(state)
        triggers = ExtruderTriggers(None, None, None, None, None, None, None, None, True, None)
        # test True with true filter
        state.is_deretracting = True
        state.is_primed = False  # turn this off so we don't have to account for this default state
        self.assertTrue(self.Extruder.is_triggered(triggers))
        # test False with True filter
        state.is_deretracting = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test on_deretracting - False Filter
        triggers = ExtruderTriggers(None, None, None, None, None, None, None, None, False, None)
        # test True with False filter
        state.is_deretracting = True
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test False with False filter
        state.is_deretracting = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))

    def test_extruderTriggers_on_deretracted(self):
        # test on_deretracted
        self.Extruder.reset()
        state = ExtruderState()
        self.Extruder.add_state(state)
        triggers = ExtruderTriggers(None, None, None, None, None, None, None, None, None, True)
        # test True with true filter
        state.is_deretracted = True
        state.is_primed = False  # turn this off so we don't have to account for this default state
        self.assertTrue(self.Extruder.is_triggered(triggers))
        # test False with True filter
        state.is_deretracted = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test on_deretracted - False Filter
        triggers = ExtruderTriggers(None, None, None, None, None, None, None, None, None, False)
        # test True with False filter
        state.is_deretracted = True
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # test False with False filter
        state.is_deretracted = False
        self.assertTrue(not self.Extruder.is_triggered(triggers))

    def test_extruderTriggers_Mixed(self):
        # Test mixed nones, trues and falses
        self.Extruder.reset()
        state = ExtruderState()
        self.Extruder.add_state(state)
        triggers = ExtruderTriggers(None, True, False, None, True, False, None, True, False, None)
        # Forbidden Due to is_primed
        state.is_extruding_start = True
        state.is_extruding = True
        state.is_primed = True
        state.is_retracting_start = True
        state.is_retracting = True
        state.is_partially_retracted = False
        state.is_retracted = True
        state.is_deretracting_start = True
        state.is_deretracting = False
        state.is_deretracted = True
        self.assertTrue(not self.Extruder.is_triggered(triggers))
        # True - is extruding
        state.is_extruding_start = False
        state.is_extruding = True
        state.is_primed = False
        state.is_retracting_start = True
        state.is_retracting = False
        state.is_partially_retracted = False
        state.is_retracted = True
        state.is_deretracting_start = False
        state.is_deretracting = False
        state.is_deretracted = True
        self.assertTrue(self.Extruder.is_triggered(triggers))

        # Test all false states and all Nones
        state.is_extruding_start = True
        state.is_extruding = True
        state.is_primed = True
        state.is_retracting_start = True
        state.is_retracting = True
        state.is_partially_retracted = True
        state.is_retracted = True
        state.is_deretracting_start = True
        state.is_deretracting = True
        state.is_deretracted = True
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
