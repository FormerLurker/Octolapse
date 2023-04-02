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

import time
import unittest
from tempfile import NamedTemporaryFile

from octoprint_octolapse.extruder import ExtruderState
from octoprint_octolapse.extruder import ExtruderTriggers
from octoprint_octolapse.position import Position
from octoprint_octolapse.settings import OctolapseSettings
from octoprint_octolapse.trigger import TimerTrigger


class TestTimerTrigger(unittest.TestCase):
    def setUp(self):
        self.Settings = OctolapseSettings(NamedTemporaryFile().name)
        self.Settings.profiles.current_printer().e_axis_default_mode = 'relative'
        self.Settings.profiles.current_printer().xyz_axes_default_mode = 'absolute'
        self.Settings.profiles.current_printer().auto_detect_position = False
        self.Settings.profiles.current_printer().home_x = 0
        self.Settings.profiles.current_printer().home_y = 0
        self.Settings.profiles.current_printer().home_z = 0
        self.OctoprintPrinterProfile = self.create_octoprint_printer_profile()

    def tearDown(self):
        del self.Settings
        del self.OctoprintPrinterProfile

    @staticmethod
    def create_octoprint_printer_profile():
        return dict(
            volume=dict(
                width=250,
                depth=200,
                height=200,
                formFactor="Not A Circle",
                custom_box=False,
            )
        )

    def test_TimerTrigger(self):
        """Test the timer trigger"""
        # use a short trigger time so that the test doesn't take too long
        self.Settings.profiles.current_snapshot().timer_trigger_seconds = 2
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        trigger = TimerTrigger(self.Settings)
        trigger.ExtruderTriggers = ExtruderTriggers(None, None, None, None, None, None, None, None, None,
                                                    None)  # Ignore extruder
        trigger.require_zhop = False  # no zhop required
        trigger.height_increment = 0  # Trigger on any height change
        # test initial state
        self.assertFalse(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

        # set interval time to 0, send another command and test again (should not trigger, no homed axis)
        trigger.interval_seconds = 0
        position.update("g0 x0 y0 z.2 e1")
        trigger.update(position)
        self.assertFalse(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

        # Home all axis and try again with interval seconds 1 - should not trigger since the timer will start after
        # the home command
        trigger.interval_seconds = 2
        position.update("g28")
        trigger.update(position)
        self.assertFalse(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

        # send another command and try again, should not trigger cause we haven't waited 2 seconds yet
        position.update("g0 x0 y0 z.2 e1")
        trigger.update(position)
        self.assertFalse(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

        # Set the last trigger time to 1 before the previous LastTrigger time(equal to interval seconds), should not
        # trigger
        trigger.get_state(0).trigger_start_time = time.time() - 1.01
        position.update("g0 x0 y0 z.2 e1")
        trigger.update(position)
        self.assertFalse(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

        # Set the last trigger time to 1 before the previous LastTrigger time(equal to interval seconds), should trigger
        trigger.trigger_start_time = time.time() - 2.01
        position.update("g0 x0 y0 z.2 e1")
        trigger.update(position)
        self.assertFalse(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

    def test_TimerTrigger_ExtruderTriggers(self):
        """Test All Extruder Triggers"""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        # home the axis
        position.update("G28")
        trigger = TimerTrigger(self.Settings)
        trigger.interval_seconds = 1
        trigger.require_zhop = False  # no zhop required

        # Reset the extruder
        state = ExtruderState()
        position.Extruder.StateHistory[0] = state
        # Try on extruding start - previous position not homed, do not trigger
        trigger.ExtruderTriggers = ExtruderTriggers(
            True, None, None, None, None, None, None, None, None, None)
        trigger.get_state(0).trigger_start_time = time.time() - 1.01
        trigger.update(position)
        self.assertFalse(trigger.is_triggered(0))
        self.assertTrue(trigger.is_waiting(0))

        # Reset the extruder
        state = ExtruderState()
        position.Extruder.StateHistory[0] = state
        # send another command, now the previous state has been homed, should trigger
        position.update("AnotherCommandNowPreviousHomed")
        # set is extruding start, wont be set by the above command!
        position.Extruder.StateHistory[0].is_extruding_start = True
        trigger.update(position)
        self.assertTrue(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

        # Reset the extruder
        state = ExtruderState()
        position.Extruder.StateHistory[0] = state
        # try out on extruding
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, True, None, None, None, None, None, None, None, None)
        state.is_extruding = True
        trigger.get_state(0).trigger_start_time = time.time() - 1.01
        trigger.update(position)
        self.assertTrue(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

        # Reset the extruder
        state = ExtruderState()
        position.Extruder.StateHistory[0] = state
        # try out on primed
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, None, True, None, None, None, None, None, None, None)
        state.is_primed = True
        trigger.get_state(0).trigger_start_time = time.time() - 1.01
        trigger.update(position)
        self.assertTrue(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

        # Reset the extruder
        state = ExtruderState()
        position.Extruder.StateHistory[0] = state
        # try out on retracting start
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, None, None, True, None, None, None, None, None, None)
        state.is_retracting_start = True
        trigger.get_state(0).trigger_start_time = time.time() - 1.01
        trigger.update(position)
        self.assertTrue(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

        # Reset the extruder
        state = ExtruderState()
        position.Extruder.StateHistory[0] = state
        # try out on retracting
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, None, None, None, True, None, None, None, None, None)
        state.is_retracting = True
        trigger.get_state(0).trigger_start_time = time.time() - 1.01
        trigger.update(position)
        self.assertTrue(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

        # Reset the extruder
        state = ExtruderState()
        position.Extruder.StateHistory[0] = state
        # try out on partially retracted
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, None, None, None, None, True, None, None, None, None)
        state.is_partially_retracted = True
        trigger.get_state(0).trigger_start_time = time.time() - 1.01
        trigger.update(position)
        self.assertTrue(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

        # Reset the extruder
        state = ExtruderState()
        position.Extruder.StateHistory[0] = state
        # try out on retracted
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, None, None, None, None, None, True, None, None, None)
        state.is_retracted = True
        trigger.get_state(0).trigger_start_time = time.time() - 1.01
        trigger.update(position)
        self.assertTrue(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

        # Reset the extruder
        state = ExtruderState()
        position.Extruder.StateHistory[0] = state
        # try out on deretracting Start
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, None, None, None, None, None, None, True, None, None)
        state.is_deretracting_start = True
        trigger.get_state(0).trigger_start_time = time.time() - 1.01
        trigger.update(position)
        self.assertTrue(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

        # Reset the extruder
        state = ExtruderState()
        position.Extruder.StateHistory[0] = state
        # try out on deretracting Start
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, None, None, None, None, None, None, None, True, None)
        state.is_deretracting = True
        trigger.get_state(0).trigger_start_time = time.time() - 1.01
        trigger.update(position)
        self.assertTrue(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

        # Reset the extruder
        state = ExtruderState()
        position.Extruder.StateHistory[0] = state
        # try out on deretracting Start
        trigger.ExtruderTriggers = ExtruderTriggers(
            None, None, None, None, None, None, None, None, None, True)
        state.is_deretracted = True
        trigger.get_state(0).trigger_start_time = time.time() - 1.01
        trigger.update(position)
        self.assertTrue(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

    def test_TimerTrigger_ExtruderTriggerWait(self):
        """Test wait on extruder"""
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        # home the axis
        position.update("G28")
        trigger = TimerTrigger(self.Settings)
        trigger.require_zhop = False  # no zhop required
        trigger.interval_seconds = 1

        # Use on extruding start for this test.
        trigger.ExtruderTriggers = ExtruderTriggers(
            True, None, None, None, None, None, None, None, None, None)

        # set the extruder trigger
        position.Extruder.get_state(0).is_extruding_start = True
        # will not wait or trigger because not enough time has elapsed
        trigger.update(position)
        self.assertFalse(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

        # add 1 second to the state and try again
        trigger.get_state(0).trigger_start_time = time.time() - 1.01

        # send another command and try again
        position.update("PreviousPositionIsNowHomed")
        # set the extruder trigger
        position.Extruder.get_state(0).is_extruding_start = True
        trigger.update(position)
        self.assertTrue(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

    def test_TimerTrigger_LayerChange_ZHop(self):
        """Test the layer trigger for layer changes triggers"""
        self.Settings.profiles.current_snapshot().timer_trigger_require_zhop = True
        self.Settings.profiles.current_printer().z_hop = .5
        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        trigger = TimerTrigger(self.Settings)
        trigger.ExtruderTriggers = ExtruderTriggers(None, None, None, None, None, None, None, None, None,
                                                    None)  # Ignore extruder
        trigger.interval_seconds = 1
        # test initial state
        self.assertFalse(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

        # send commands that normally would trigger a layer change, but without all axis homed.
        position.update("g0 x0 y0 z.2 e1")
        trigger.update(position)
        self.assertFalse(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

        # Home all axis and try again, wait on zhop
        position.update("g28")
        trigger.update(position)
        self.assertFalse(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))
        position.update("g0 x0 y0 z.2 e1")
        trigger.get_state(0).trigger_start_time = time.time() - 1.01
        trigger.update(position)
        self.assertFalse(trigger.is_triggered(0))
        self.assertTrue(trigger.is_waiting(0))

        # try zhop
        position.update("g0 x0 y0 z.7 ")
        trigger.update(position)
        self.assertTrue(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

        # extrude on current layer, no trigger (wait on zhop)
        position.update("g0 x0 y0 z.7 e1")
        trigger.get_state(0).trigger_start_time = time.time() - 1.01
        trigger.update(position)
        self.assertFalse(trigger.is_triggered(0))
        self.assertTrue(trigger.is_waiting(0))

        # do not extrude on current layer, still waiting
        position.update("g0 x0 y0 z.7 ")
        trigger.update(position)
        self.assertFalse(trigger.is_triggered(0))
        self.assertTrue(trigger.is_waiting(0))

        # partial hop, but close enough based on our printer measurement tolerance (0.005)
        position.update("g0 x0 y0 z1.1999")
        trigger.update(position)
        self.assertTrue(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

        # creat wait state
        position.update("g0 x0 y0 z1.3 e1")
        trigger.get_state(0).trigger_start_time = time.time() - 1.01
        trigger.update(position)
        self.assertFalse(trigger.is_triggered(0))
        self.assertTrue(trigger.is_waiting(0))

        # move down (should never happen, should behave properly anyway)
        position.update("g0 x0 y0 z.8")
        trigger.update(position)
        self.assertFalse(trigger.is_triggered(0))
        self.assertTrue(trigger.is_waiting(0))

        # move back up to current layer (should NOT trigger zhop)
        position.update("g0 x0 y0 z1.3")
        trigger.update(position)
        self.assertFalse(trigger.is_triggered(0))
        self.assertTrue(trigger.is_waiting(0))

        # move up a bit, not enough to trigger zhop
        position.update("g0 x0 y0 z1.795")
        trigger.update(position)
        self.assertFalse(trigger.is_triggered(0))
        self.assertTrue(trigger.is_waiting(0))

        # move up a bit, just enough to trigger zhop
        position.update("g0 x0 y0 z1.7951")
        trigger.update(position)
        self.assertTrue(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTimerTrigger)
    unittest.TextTestRunner(verbosity=3).run(suite)
