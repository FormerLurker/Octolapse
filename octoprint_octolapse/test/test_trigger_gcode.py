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

from octoprint_octolapse.position import Position
from octoprint_octolapse.settings import OctolapseSettings
from octoprint_octolapse.trigger import GcodeTrigger


class TestGcodeTrigger(unittest.TestCase):
    def setUp(self):
        self.Settings = OctolapseSettings(NamedTemporaryFile().name)
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
        self.Settings.profiles.current_snapshot().gcode_trigger_require_zhop = False

        position = Position(self.Settings, self.OctoprintPrinterProfile, False)
        trigger = GcodeTrigger(self.Settings)
        # test initial state
        self.assertFalse(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

        # send a command that is NOT the snapshot command using the defaults
        trigger.update(position, "NotThesnapshot_command")
        self.assertFalse(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

        # send a command that is the snapshot command without the axis being homes
        trigger.update(position, "snap")
        self.assertFalse(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

        # reset, set relative extruder and absolute xyz, home the axis, and resend the snap command, should wait
        # since we require the home command to complete (sent to printer) before triggering
        position.update("M83")
        position.update("G90")
        position.update("G28")
        trigger.update(position, "snap")
        self.assertFalse(trigger.is_triggered(0))
        self.assertTrue(trigger.is_waiting(0))

        # try again, Snap is encountered, but it must be the previous command to trigger
        position.update("G0 X0 Y0 Z0 E1 F0")
        trigger.update(position, "G0 X0 Y0 Z0 E1 F0")
        self.assertTrue(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

        # try again, but this time set require_zhop to true
        trigger.require_zhop = True
        trigger.update(position, "snap")
        self.assertFalse(trigger.is_triggered(0))
        self.assertTrue(trigger.is_waiting(0))
        # send another command to see if we are still waiting
        trigger.update(position, "NotThesnapshot_command")
        self.assertFalse(trigger.is_triggered(0))
        self.assertTrue(trigger.is_waiting(0))
        # fake a zhop
        position.is_zhop = lambda x: True
        trigger.update(position, "NotThesnapshot_command")
        self.assertTrue(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

        # send a command that is NOT the snapshot command using the defaults
        trigger.update(position, "NotThesnapshot_command")
        self.assertFalse(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))

        # change the snapshot triggers and make sure they are working
        self.Settings.profiles.current_snapshot().gcode_trigger_require_zhop = None
        self.Settings.profiles.current_snapshot().gcode_trigger_on_extruding = True
        self.Settings.profiles.current_snapshot().gcode_trigger_on_extruding_start = None
        self.Settings.profiles.current_snapshot().gcode_trigger_on_primed = None
        self.Settings.profiles.current_snapshot().gcode_trigger_on_retracting = None
        self.Settings.profiles.current_snapshot().gcode_trigger_on_partially_retracted = None
        self.Settings.profiles.current_snapshot().gcode_trigger_on_retracted = None
        self.Settings.profiles.current_snapshot().gcode_trigger_on_deretracting_start = None
        self.Settings.profiles.current_snapshot().gcode_trigger_on_deretracting = None
        self.Settings.profiles.current_snapshot().gcode_trigger_on_deretracted = None
        trigger = GcodeTrigger(self.Settings)

        # send a command that is the snapshot command using the defaults
        trigger.update(position, "snap")
        self.assertFalse(trigger.is_triggered(0))
        self.assertTrue(trigger.is_waiting(0))
        # change the extruder state and test
        # should not trigger because trigger tests the previous command
        position.update("G0 X0 Y0 Z0 E10 F0")
        trigger.update(position, "NotThesnapshot_command")
        self.assertTrue(trigger.is_triggered(0))
        self.assertFalse(trigger.is_waiting(0))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGcodeTrigger)
    unittest.TextTestRunner(verbosity=3).run(suite)
