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

from octoprint_octolapse.stabilization_gcode import SnapshotGcode
from octoprint_octolapse.position import Position
from octoprint_octolapse.settings import OctolapseSettings
from octoprint_octolapse.timelapse import Timelapse, TimelapseState


class OctoprintTestPrinter(object):
    def __init__(self):
        self.IsPaused = False
        self.IsPrinting = False
        self.GcodeCommands = []

    def pause_print(self):
        self.IsPaused = True

    def resume_print(self):
        self.IsPaused = False

    def is_paused(self):
        return self.IsPaused

    def commands(self, commands):
        if (isinstance(commands, basestring)):
            self.GcodeCommands.append(commands)
        elif (isinstance(commands, list)):
            self.GcodeCommands.extend(commands)
        elif (isinstance(obj, tuple)):
            self.GcodeCommands.extend(list(commands))


class GcodeTest(object):
    def __init__(self, gcodeCommands):
        self.X = None
        self.Y = None
        self.Z = None
        self.GcodeCommands = gcodeCommands

    def CreateSnapshotGcode(self, *args, **kwargs):
        return self.GcodeCommands


# used to replace commands within the Timelapse class that we don't want to execute


def ReturnNone(*args, **kwargs):
    return None


def ReturnTrue(*args, **kwargs):
    return True


class TestTimelapse(unittest.TestCase):
    def setUp(self):
        self.OctoprintPrinterProfile = self.CreateOctoprintPrinterProfile()
        self.Settings = OctolapseSettings("c:\\temp\\octolapse\\data\\")
        # configure settings for tests
        currentSnapshot = self.Settings.profiles.current_snapshot()
        currentSnapshot.gcode_trigger_enabled = True
        currentSnapshot.layer_trigger_enabled = False
        currentSnapshot.timer_trigger_enabled = False
        currentSnapshot.gcode_trigger_require_zhop = False
        currentSnapshot.layer_trigger_require_zhop = False
        currentSnapshot.timer_trigger_require_zhop = False
        currentSnapshot.timer_trigger_seconds = 1
        self.Timelapse_GcodeTrigger = Timelapse(self.Settings,
                                                "c:\\temp\\octolapse\\data\\", "c:\\temp\\octolapse\\data\\timelapse\\",
                                                onMovieRendering=self.OnMovieRendering, onMovieDone=self.OnMovieDone,
                                                onMovieFailed=self.OnMovieFailed)
        currentSnapshot.gcode_trigger_enabled = False
        currentSnapshot.timer_trigger_enabled = True
        self.Timelapse_TimerTrigger = Timelapse(self.Settings,
                                                "c:\\temp\\octolapse\\data\\", "c:\\temp\\octolapse\\data\\timelapse\\",
                                                onMovieRendering=self.OnMovieRendering, onMovieDone=self.OnMovieDone,
                                                onMovieFailed=self.OnMovieFailed)
        self.MovieRendering = False
        self.MovieDone = False
        self.MovieFailed = False
        self.OctoprintTestPrinter = OctoprintTestPrinter()
        self.FfMpegPath = "C:\\Program Files\\ffmpeg\\"

    def tearDown(self):
        del self.OctoprintPrinterProfile
        del self.Settings
        del self.Timelapse_GcodeTrigger
        del self.MovieRendering
        del self.MovieDone
        del self.MovieFailed
        del self.OctoprintTestPrinter
        del self.FfMpegPath

    def CreateOctoprintPrinterProfile(self):
        return {
            "volume": {
                "custom_box": False,
                "width": 250,
                "depth": 200,
                "height": 200
            }
        }

    def OnMovieRendering(self):
        self.MovieRendering = True

    def OnMovieDone(self):
        self.MovieDone = True

    def OnMovieFailed(self):
        self.MovieFailed = True

    def test_Reset(self):
        """Test the reset function."""
        # test the initial state
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.Idle)
        self.assertTrue(len(self.Timelapse_GcodeTrigger.Triggers) == 0)
        self.assertTrue(self.Timelapse_GcodeTrigger.CommandIndex == -1)
        self.assertTrue(self.Timelapse_GcodeTrigger.SnapshotCount == 0)
        self.assertTrue(self.Timelapse_GcodeTrigger.PrintStartTime is None)
        self.assertTrue(self.Timelapse_GcodeTrigger.SnapshotGcodes is None)
        self.assertTrue(self.Timelapse_GcodeTrigger.SavedCommand is None)
        self.assertTrue(
            self.Timelapse_GcodeTrigger.PositionRequestAttempts == 0)

        # change all vars
        self.Timelapse_GcodeTrigger.State == TimelapseState.Idle
        self.Timelapse_GcodeTrigger.Triggers == ["test"]
        self.Timelapse_GcodeTrigger.CommandIndex = 1
        self.Timelapse_GcodeTrigger.SnapshotCount = 1
        self.Timelapse_GcodeTrigger.PrintStartTime = 1
        self.Timelapse_GcodeTrigger.SnapshotGcodes = ""
        self.Timelapse_GcodeTrigger.SavedCommand = ""
        self.Timelapse_GcodeTrigger.PositionRequestAttempts = 1

        # reset and test
        self.Timelapse_GcodeTrigger.Reset()
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.Idle)
        self.assertTrue(len(self.Timelapse_GcodeTrigger.Triggers) == 0)
        self.assertTrue(self.Timelapse_GcodeTrigger.CommandIndex == -1)
        self.assertTrue(self.Timelapse_GcodeTrigger.SnapshotCount == 0)
        self.assertTrue(self.Timelapse_GcodeTrigger.PrintStartTime is None)
        self.assertTrue(self.Timelapse_GcodeTrigger.SnapshotGcodes is None)
        self.assertTrue(self.Timelapse_GcodeTrigger.SavedCommand is None)
        self.assertTrue(
            self.Timelapse_GcodeTrigger.PositionRequestAttempts == 0)

    def test_ResetSnapshot(self):
        """Test the reset function."""
        # set initial state
        # test the initial state
        # Note that ResetSnapshot will change this to WaitingForTrigger
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.Idle)
        self.assertTrue(self.Timelapse_GcodeTrigger.CommandIndex == -1)
        self.assertTrue(self.Timelapse_GcodeTrigger.SnapshotGcodes is None)
        self.assertTrue(self.Timelapse_GcodeTrigger.SavedCommand is None)
        self.assertTrue(
            self.Timelapse_GcodeTrigger.PositionRequestAttempts == 0)

        # change all vars except state (that should change to WaitingForTrigger)
        self.Timelapse_GcodeTrigger.SnapshotGcodes = ""
        self.Timelapse_GcodeTrigger.SavedCommand = ""
        self.Timelapse_GcodeTrigger.PositionRequestAttempts = 1
        # reset and test
        self.Timelapse_GcodeTrigger.ResetSnapshot()
        # Note that ResetSnapshot will change this to WaitingForTrigger
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.WaitingForTrigger)
        self.assertTrue(self.Timelapse_GcodeTrigger.CommandIndex == -1)
        self.assertTrue(self.Timelapse_GcodeTrigger.SnapshotGcodes is None)
        self.assertTrue(self.Timelapse_GcodeTrigger.SavedCommand is None)
        self.assertTrue(
            self.Timelapse_GcodeTrigger.PositionRequestAttempts == 0)

    def test_StartTimelapse(self):
        """Test timelapse startup routine."""
        self.Settings.profiles.current_snapshot().gcode_trigger_enabled = True
        self.Settings.profiles.current_snapshot().layer_trigger_enabled = False
        self.Settings.profiles.current_snapshot().timer_trigger_enabled = False
        self.Timelapse_GcodeTrigger.start_timelapse(
            self.OctoprintTestPrinter, self.OctoprintPrinterProfile, self.FfMpegPath, False)
        # Test all settings
        self.assertTrue(
            self.Timelapse_GcodeTrigger.OctoprintPrinter == self.OctoprintTestPrinter)
        self.assertTrue(
            self.Timelapse_GcodeTrigger.OctoprintPrinterProfile == self.OctoprintPrinterProfile)
        self.assertTrue(
            self.Timelapse_GcodeTrigger.FfMpegPath == self.FfMpegPath)
        self.assertTrue(self.Timelapse_GcodeTrigger.PrintStartTime is not None)
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.WaitingForTrigger)
        self.assertTrue(len(self.Timelapse_GcodeTrigger.Triggers) == 1)

    def test_PrintPaused(self):
        """Test the 'Print Paused' routine"""
        # verify initial state
        self.Settings.profiles.current_snapshot().gcode_trigger_enabled = False
        self.Settings.profiles.current_snapshot().layer_trigger_enabled = False
        self.Settings.profiles.current_snapshot().timer_trigger_enabled = True
        self.assertTrue(self.Timelapse_TimerTrigger.State ==
                        TimelapseState.Idle)
        self.assertTrue(len(self.Timelapse_TimerTrigger.Triggers) == 0)

        # start the timelapse and verify that the trigger is created
        self.Timelapse_TimerTrigger.start_timelapse(
            self.OctoprintTestPrinter, self.OctoprintPrinterProfile, self.FfMpegPath, False)
        self.assertTrue(
            self.Timelapse_TimerTrigger.Triggers[0].pause_time is None)

        # Pause the print and test the idle state
        self.Timelapse_TimerTrigger.State = TimelapseState.Idle
        self.Timelapse_TimerTrigger.on_print_paused()
        self.assertTrue(self.Timelapse_TimerTrigger.State ==
                        TimelapseState.Idle)
        self.assertTrue(
            self.Timelapse_TimerTrigger.Triggers[0].pause_time is None)

        # pause the print and test the WaitingForTrigger state
        self.Timelapse_TimerTrigger.State = TimelapseState.WaitingForTrigger
        self.Timelapse_TimerTrigger.on_print_paused()
        self.assertTrue(
            self.Timelapse_TimerTrigger.Triggers[0].pause_time is not None)

        # Test with no triggers
        self.Timelapse_TimerTrigger.Triggers = None
        # we're OK as long as this doesn't throw an exception
        self.Timelapse_TimerTrigger.on_print_paused()

    def test_IsTimelapseActive(self):
        """Tests the IsTimelapseActive function"""
        # test initial state
        self.assertTrue(self.Timelapse_TimerTrigger.State ==
                        TimelapseState.Idle)
        self.assertTrue(
            self.Timelapse_TimerTrigger.Settings.is_octolapse_enabled)
        self.assertTrue(len(self.Timelapse_TimerTrigger.Triggers) == 0)

        # verify false return if state is idle
        self.Timelapse_TimerTrigger.Triggers = ["Something in the list"]
        self.assertFalse(self.Timelapse_TimerTrigger.is_timelapse_active())

        # verify false return if octolapse is not enabled
        self.Timelapse_TimerTrigger.Settings.is_octolapse_enabled = False
        self.Timelapse_TimerTrigger.State = TimelapseState.WaitingForTrigger
        self.assertFalse(self.Timelapse_TimerTrigger.is_timelapse_active())

        # verify true if not idle, enabled, and has triggers
        self.Timelapse_TimerTrigger.Settings.is_octolapse_enabled = True
        self.assertTrue(self.Timelapse_TimerTrigger.is_timelapse_active())

        # verify false return if there are no triggers
        self.Timelapse_TimerTrigger.Triggers = []
        self.assertFalse(self.Timelapse_TimerTrigger.is_timelapse_active())

    def test_Issnapshot_command(self):
        # set the snapshot command
        snapshotCommand = "snap"
        notsnapshot_command = "NotThesnapshot_command"
        self.Timelapse_GcodeTrigger.Printer = self.Settings.profiles.current_printer()
        self.Timelapse_GcodeTrigger.Printer.snapshot_command = snapshotCommand
        # test snapshot command
        self.assertTrue(
            self.Timelapse_GcodeTrigger.Issnapshot_command(snapshotCommand))
        # test non snapshot command
        self.assertFalse(
            self.Timelapse_GcodeTrigger.Issnapshot_command(notsnapshot_command))

    def test_IsTriggering_GcodeTrigger(self):
        # set the snapshot command
        snapshotCommand = "snap"
        notsnapshot_command = "NotThesnapshot_command"
        self.Settings.profiles.current_snapshot().gcode_trigger_enabled = True
        self.Settings.profiles.current_snapshot().layer_trigger_enabled = False
        self.Settings.profiles.current_snapshot().timer_trigger_enabled = False
        self.Settings.profiles.current_printer().snapshot_command = snapshotCommand
        # verify the initial state
        self.assertTrue(self.Timelapse_GcodeTrigger.IsTriggering(
            notsnapshot_command) is None)

        # start the timelapse
        self.Timelapse_GcodeTrigger.start_timelapse(
            self.OctoprintTestPrinter, self.OctoprintPrinterProfile, self.FfMpegPath, False)

        # make sure that the snapshot command returns false when the current position is not homed
        self.assertTrue(self.Timelapse_GcodeTrigger.IsTriggering(
            snapshotCommand) is None)

        # home the position, retest
        self.Timelapse_GcodeTrigger.Position.update("G28")
        self.assertTrue(self.Timelapse_GcodeTrigger.IsTriggering(
            notsnapshot_command) is None)
        # send snapshot gcode
        self.Timelapse_GcodeTrigger.Position.update("snapshotCommand")
        triggeringTrigger = self.Timelapse_GcodeTrigger.IsTriggering(
            snapshotCommand)
        self.assertTrue(triggeringTrigger ==
                        self.Timelapse_GcodeTrigger.Triggers[0])

    def test_IsTriggering_TimerTrigger(self):
        self.Settings.profiles.current_snapshot().gcode_trigger_enabled = False
        self.Settings.profiles.current_snapshot().layer_trigger_enabled = False
        self.Settings.profiles.current_snapshot().timer_trigger_enabled = True
        # verify the initial state
        self.assertTrue(self.Timelapse_TimerTrigger.IsTriggering("") is None)

        # start the timelapse
        self.Timelapse_TimerTrigger.start_timelapse(
            self.OctoprintTestPrinter, self.OctoprintPrinterProfile, self.FfMpegPath, False)

        # set timer triger time elsapsed so that it could trigger, but won't because the axis aren't homed
        self.Timelapse_TimerTrigger.Triggers[0].trigger_start_time = time.time(
        ) - 1.01
        self.assertTrue(self.Timelapse_TimerTrigger.IsTriggering("") is None)

        # home the position, retest
        self.Timelapse_TimerTrigger.Position.update("G28")
        self.Timelapse_TimerTrigger.Position.update("AnotherCommandAfterG28")
        self.Timelapse_TimerTrigger.Triggers[0].trigger_start_time = time.time(
        ) - 1.01
        self.assertTrue(self.Timelapse_TimerTrigger.IsTriggering(
            "") == self.Timelapse_TimerTrigger.Triggers[0])

        # try again immediately
        self.assertTrue(self.Timelapse_TimerTrigger.IsTriggering("") is None)

        # set to trigger and retest
        self.Timelapse_TimerTrigger.Triggers[0].trigger_start_time = time.time(
        ) - 1.01
        self.assertTrue(self.Timelapse_TimerTrigger.IsTriggering(
            "") == self.Timelapse_TimerTrigger.Triggers[0])

    def test_GcodeQueuing_TimelapseNotActive(self):
        snapshotCommand = "snap"
        notsnapshot_command = "NotThesnapshot_command"
        self.Settings.profiles.current_printer().snapshot_command = snapshotCommand
        self.Settings.profiles.current_snapshot().gcode_trigger_enabled = True
        self.Settings.profiles.current_snapshot().layer_trigger_enabled = False
        self.Settings.profiles.current_snapshot().timer_trigger_enabled = False

        # verify initial state
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.Idle)
        self.assertTrue(
            self.Timelapse_GcodeTrigger.Settings.is_octolapse_enabled)
        self.assertTrue(len(self.Timelapse_TimerTrigger.Triggers) == 0)

        # start the timelapse
        self.Timelapse_GcodeTrigger.start_timelapse(
            self.OctoprintTestPrinter, self.OctoprintPrinterProfile, self.FfMpegPath, False)
        # set the state to avoid the Idle return
        self.Timelapse_GcodeTrigger.State = TimelapseState.WaitingForTrigger

    def test_GcodeQueuing_TestSuppresssnapshot_command(self):
        snapshotCommand = "snap"
        notsnapshot_command = "NotThesnapshot_command"
        self.Settings.profiles.current_printer().snapshot_command = snapshotCommand
        self.Settings.profiles.current_snapshot().gcode_trigger_enabled = True
        self.Settings.profiles.current_snapshot().layer_trigger_enabled = False
        self.Settings.profiles.current_snapshot().timer_trigger_enabled = False
        # verify initial state
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.Idle)
        self.assertTrue(
            self.Timelapse_GcodeTrigger.Settings.is_octolapse_enabled)
        self.assertTrue(len(self.Timelapse_TimerTrigger.Triggers) == 0)

        # start the timelapse
        self.Timelapse_GcodeTrigger.start_timelapse(
            self.OctoprintTestPrinter, self.OctoprintPrinterProfile, self.FfMpegPath, False)
        # set the state to avoid the Idle return
        self.Timelapse_GcodeTrigger.State = TimelapseState.WaitingForTrigger
        # test the snapshot command and make sure it is suppressed
        # make sure the snapshot is inactive first
        returnVal = self.Timelapse_GcodeTrigger.on_gcode_queuing(
            None, None, snapshotCommand, None, None)
        self.assertTrue(returnVal == (None,))

    def test_GcodeQueuing_TestSuppressNonSnapshotGcodeCommand(self):
        snapshotCommand = "snap"
        notsnapshot_command = "NotThesnapshot_command"
        self.Settings.profiles.current_printer().snapshot_command = snapshotCommand
        self.Settings.profiles.current_snapshot().gcode_trigger_enabled = True
        self.Settings.profiles.current_snapshot().layer_trigger_enabled = False
        self.Settings.profiles.current_snapshot().timer_trigger_enabled = False
        # verify initial state
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.Idle)
        self.assertTrue(
            self.Timelapse_GcodeTrigger.Settings.is_octolapse_enabled)
        self.assertTrue(len(self.Timelapse_TimerTrigger.Triggers) == 0)

        # start the timelapse
        self.Timelapse_GcodeTrigger.start_timelapse(
            self.OctoprintTestPrinter, self.OctoprintPrinterProfile, self.FfMpegPath, False)
        # set the state to avoid the Idle return
        self.Timelapse_GcodeTrigger.State = TimelapseState.WaitingForTrigger

        # test the snapshot command and make sure it is suppressed
        returnVal = self.Timelapse_GcodeTrigger.on_gcode_queuing(
            None, None, notsnapshot_command, None, None)
        self.assertTrue(returnVal == None)

    def test_GcodeQueuing_M105Suppress(self):
        snapshotCommand = "snap"
        notsnapshot_command = "NotThesnapshot_command"
        self.Settings.profiles.current_printer().snapshot_command = snapshotCommand
        self.Settings.profiles.current_snapshot().gcode_trigger_enabled = True
        self.Settings.profiles.current_snapshot().layer_trigger_enabled = False
        self.Settings.profiles.current_snapshot().timer_trigger_enabled = False
        # verify initial state
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.Idle)
        self.assertTrue(
            self.Timelapse_GcodeTrigger.Settings.is_octolapse_enabled)
        self.assertTrue(len(self.Timelapse_TimerTrigger.Triggers) == 0)

        # start the timelapse
        self.Timelapse_GcodeTrigger.start_timelapse(
            self.OctoprintTestPrinter, self.OctoprintPrinterProfile, self.FfMpegPath, False)

        # M105 command received (also test lowercase commands with whitespace)
        # advance the state so that we will suppress the M105
        self.Timelapse_GcodeTrigger.State = TimelapseState.RequestingReturnPosition
        returnVal = self.Timelapse_GcodeTrigger.on_gcode_queuing(
            None, None, " m105  ", None, None)
        self.assertTrue(returnVal == (None,))

    def test_GcodeQueuing_SuppressNonSnapshotGcode(self):
        snapshotCommand = "snap"
        notsnapshot_command = "NotThesnapshot_command"
        self.Settings.profiles.current_printer().snapshot_command = snapshotCommand
        self.Settings.profiles.current_snapshot().gcode_trigger_enabled = True
        self.Settings.profiles.current_snapshot().layer_trigger_enabled = False
        self.Settings.profiles.current_snapshot().timer_trigger_enabled = False
        # verify initial state
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.Idle)
        self.assertTrue(
            self.Timelapse_GcodeTrigger.Settings.is_octolapse_enabled)
        self.assertTrue(len(self.Timelapse_TimerTrigger.Triggers) == 0)

        # start the timelapse
        self.Timelapse_GcodeTrigger.start_timelapse(
            self.OctoprintTestPrinter, self.OctoprintPrinterProfile, self.FfMpegPath, False)

        # Test suppressing gcodes that aren't in the Snapshot Gcode commands
        snapshotGcodes = SnapshotGcode(False)
        snapshotGcodes.GcodeCommands.extend(
            ["TestCommand1", "TestCommand2", "m105", "TestCommand4", "TestCommand4"])
        snapshotGcodes.SnapshotIndex = 2
        self.Timelapse_GcodeTrigger.SnapshotGcodes = snapshotGcodes
        self.Timelapse_GcodeTrigger.CommandIndex = 0
        # set the snapshot state to SendingSnapshotGcode
        self.Timelapse_GcodeTrigger.State = TimelapseState.SendingSnapshotGcode
        returnVal = self.Timelapse_GcodeTrigger.on_gcode_queuing(
            None, None, "NotInGcodeCommands", None, None)
        self.assertTrue(returnVal == (None,))

    def test_GcodeQueuing_SendAllsnapshot_commands(self):
        snapshotCommand = "snap"
        notsnapshot_command = "NotThesnapshot_command"
        self.Settings.profiles.current_printer().snapshot_command = snapshotCommand
        self.Settings.profiles.current_snapshot().gcode_trigger_enabled = True
        self.Settings.profiles.current_snapshot().layer_trigger_enabled = False
        self.Settings.profiles.current_snapshot().timer_trigger_enabled = False
        # verify initial state
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.Idle)
        self.assertTrue(
            self.Timelapse_GcodeTrigger.Settings.is_octolapse_enabled)
        self.assertTrue(len(self.Timelapse_TimerTrigger.Triggers) == 0)

        # start the timelapse
        self.Timelapse_GcodeTrigger.start_timelapse(
            self.OctoprintTestPrinter, self.OctoprintPrinterProfile, self.FfMpegPath, False)

        # Test suppressing gcodes that aren't in the Snapshot Gcode commands
        snapshotGcodes = SnapshotGcode(False)
        snapshotGcodes.GcodeCommands.extend(
            ["TestCommand1	", "	TestCommand2	", "	m114     ", "	TestCommand4	",
             "	TestCommand4	"])
        snapshotGcodes.SnapshotIndex = 2
        self.Timelapse_GcodeTrigger.SnapshotGcodes = snapshotGcodes
        self.Timelapse_GcodeTrigger.CommandIndex = 0
        # set the snapshot state to SendingSnapshotGcode
        self.Timelapse_GcodeTrigger.State = TimelapseState.SendingSnapshotGcode

        # test sending the first snapshot command
        returnVal = self.Timelapse_GcodeTrigger.on_gcode_queuing(
            None, None, snapshotGcodes.GcodeCommands[self.Timelapse_GcodeTrigger.CommandIndex], None, None)
        self.assertTrue(returnVal == (None))
        self.assertTrue(self.Timelapse_GcodeTrigger.CommandIndex == 1)
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.SendingSnapshotGcode)
        # test sending the second snapshot command
        returnVal = self.Timelapse_GcodeTrigger.on_gcode_queuing(
            None, None, snapshotGcodes.GcodeCommands[self.Timelapse_GcodeTrigger.CommandIndex], None, None)
        self.assertTrue(returnVal == (None))
        self.assertTrue(self.Timelapse_GcodeTrigger.CommandIndex == 2)
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.SendingSnapshotGcode)
        # simulate move command sent and taking snapshot
        self.Timelapse_GcodeTrigger.State = TimelapseState.TakingSnapshot

        # test sending the third snapshot command
        returnVal = self.Timelapse_GcodeTrigger.on_gcode_queuing(
            None, None, snapshotGcodes.GcodeCommands[self.Timelapse_GcodeTrigger.CommandIndex], None, None)
        self.assertTrue(returnVal == (None))
        self.assertTrue(self.Timelapse_GcodeTrigger.CommandIndex == 3)
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.SendingMoveCommand)

        # simulate sending return gcode
        self.Timelapse_GcodeTrigger.State = TimelapseState.SendingReturnGcode
        # test sending the fourth snapshot command
        returnVal = self.Timelapse_GcodeTrigger.on_gcode_queuing(
            None, None, snapshotGcodes.GcodeCommands[self.Timelapse_GcodeTrigger.CommandIndex], None, None)
        self.assertTrue(returnVal == (None))
        self.assertTrue(self.Timelapse_GcodeTrigger.CommandIndex == 4)
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.SendingReturnGcode)

        # test sending the fifth snapshot command
        returnVal = self.Timelapse_GcodeTrigger.on_gcode_queuing(
            None, None, snapshotGcodes.GcodeCommands[self.Timelapse_GcodeTrigger.CommandIndex], None, None)
        self.assertTrue(returnVal == (None))
        self.assertTrue(
            not self.Timelapse_GcodeTrigger.OctoprintPrinter.is_paused())
        # Note that ResetSnapshot will change this to WaitingForTrigger
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.WaitingForTrigger)
        self.assertTrue(self.Timelapse_GcodeTrigger.CommandIndex == -1)
        self.assertTrue(self.Timelapse_GcodeTrigger.SnapshotGcodes is None)
        self.assertTrue(self.Timelapse_GcodeTrigger.SavedCommand is None)
        self.assertTrue(
            self.Timelapse_GcodeTrigger.PositionRequestAttempts == 0)

    def test_GcodeQueuing_Triggering_SuppressedSavedCommand(self):
        suppressedSavedCommand = "  m105  "
        self.Settings.profiles.current_snapshot().gcode_trigger_enabled = True
        self.Settings.profiles.current_snapshot().layer_trigger_enabled = False
        self.Settings.profiles.current_snapshot().timer_trigger_enabled = False
        # verify initial state
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.Idle)
        self.assertTrue(
            self.Timelapse_GcodeTrigger.Settings.is_octolapse_enabled)
        self.assertTrue(len(self.Timelapse_TimerTrigger.Triggers) == 0)

        # start the timelapse
        self.Timelapse_GcodeTrigger.start_timelapse(
            self.OctoprintTestPrinter, self.OctoprintPrinterProfile, self.FfMpegPath, False)
        # home the axis
        self.Timelapse_GcodeTrigger.Position.update("G28")
        # set the trigger to waiting
        self.Timelapse_GcodeTrigger.Triggers[0].is_waiting = True
        # set the snapshot state to WaitingForTrigger
        self.Timelapse_GcodeTrigger.State = TimelapseState.WaitingForTrigger
        self.Timelapse_GcodeTrigger.OctoprintPrinter.Commands = []
        # test Trigger
        returnVal = self.Timelapse_GcodeTrigger.on_gcode_queuing(
            None, None, suppressedSavedCommand, None, None)
        self.assertTrue(returnVal == (None,))  # should be suppressed
        self.assertTrue(self.Timelapse_GcodeTrigger.SavedCommand is None)
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.RequestingReturnPosition)
        self.assertTrue(self.Timelapse_GcodeTrigger.OctoprintPrinter.IsPaused)

    def test_GcodeQueuing_Triggering_snapshot_command(self):
        snapshotCommand = "snap"
        notsnapshot_command = "NotThesnapshot_command"
        self.Settings.profiles.current_snapshot().gcode_trigger_enabled = True
        self.Settings.profiles.current_snapshot().layer_trigger_enabled = False
        self.Settings.profiles.current_snapshot().timer_trigger_enabled = False
        # verify initial state
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.Idle)
        self.assertTrue(
            self.Timelapse_GcodeTrigger.Settings.is_octolapse_enabled)
        self.assertTrue(len(self.Timelapse_TimerTrigger.Triggers) == 0)

        # start the timelapse
        self.Timelapse_GcodeTrigger.start_timelapse(
            self.OctoprintTestPrinter, self.OctoprintPrinterProfile, self.FfMpegPath, False)
        # home the axis
        self.Timelapse_GcodeTrigger.Position.update("G28")
        # set the snapshot state to WaitingForTrigger
        self.Timelapse_GcodeTrigger.State = TimelapseState.WaitingForTrigger
        self.Timelapse_GcodeTrigger.OctoprintPrinter.Commands = []
        # test Trigger
        returnVal = self.Timelapse_GcodeTrigger.on_gcode_queuing(
            None, None, snapshotCommand, None, None)
        self.assertTrue(returnVal == (None,))  # should be suppressed
        self.assertTrue(self.Timelapse_GcodeTrigger.SavedCommand is None)
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.RequestingReturnPosition)
        self.assertTrue(self.Timelapse_GcodeTrigger.OctoprintPrinter.IsPaused)

    def test_GcodeQueuing_Triggering_Nonsnapshot_command(self):
        notsnapshot_command = "NotThesnapshot_command"
        self.Settings.profiles.current_snapshot().gcode_trigger_enabled = True
        self.Settings.profiles.current_snapshot().layer_trigger_enabled = False
        self.Settings.profiles.current_snapshot().timer_trigger_enabled = False
        # verify initial state
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.Idle)
        self.assertTrue(
            self.Timelapse_GcodeTrigger.Settings.is_octolapse_enabled)
        self.assertTrue(len(self.Timelapse_TimerTrigger.Triggers) == 0)

        # start the timelapse
        self.Timelapse_GcodeTrigger.start_timelapse(
            self.OctoprintTestPrinter, self.OctoprintPrinterProfile, self.FfMpegPath, False)
        # home the axis
        self.Timelapse_GcodeTrigger.Position.update("G28")
        # set the trigger to is waiting so we trigger
        self.Timelapse_GcodeTrigger.Triggers[0].is_waiting = True
        # set the snapshot state to WaitingForTrigger
        self.Timelapse_GcodeTrigger.State = TimelapseState.WaitingForTrigger
        self.Timelapse_GcodeTrigger.OctoprintPrinter.Commands = []
        # test Trigger
        returnVal = self.Timelapse_GcodeTrigger.on_gcode_queuing(
            None, None, notsnapshot_command, None, None)
        self.assertTrue(returnVal == (None,))  # should be suppressed
        self.assertTrue(self.Timelapse_GcodeTrigger.SavedCommand.strip(
        ).upper() == notsnapshot_command.strip().upper())
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.RequestingReturnPosition)
        self.assertTrue(self.Timelapse_GcodeTrigger.OctoprintPrinter.IsPaused)

    def test_GcodeSent_IgnoredStates(self):
        """Tests WaitingForTrigger,	RequestingReturnPosition, SendingSnapshotGcode, TakingSnapshot, RequestingSnapshotPosition, SendingReturnGcode, all of which should be ignored except for a logging message."""
        snapshotCommand = "snap"
        self.Settings.profiles.current_printer().snapshot_command = snapshotCommand
        self.Settings.profiles.current_snapshot().gcode_trigger_enabled = True
        self.Settings.profiles.current_snapshot().layer_trigger_enabled = False
        self.Settings.profiles.current_snapshot().timer_trigger_enabled = False

        # start the timelapse
        self.Timelapse_GcodeTrigger.start_timelapse(
            self.OctoprintTestPrinter, self.OctoprintPrinterProfile, self.FfMpegPath, False)
        # set some variables to their non-defualt value so we can detect changes
        self.Timelapse_GcodeTrigger.CommandIndex = 10

        # Test WaitingForTrigger State
        self.Timelapse_GcodeTrigger.State = TimelapseState.WaitingForTrigger
        returnVal = self.Timelapse_GcodeTrigger.on_gcode_sent(
            None, None, snapshotCommand, None, None)
        self.assertTrue(returnVal is None)
        self.assertTrue(self.Timelapse_GcodeTrigger.CommandIndex == 10)

        # Test SendingSnapshotGcode State
        self.Timelapse_GcodeTrigger.State = TimelapseState.SendingSnapshotGcode
        returnVal = self.Timelapse_GcodeTrigger.on_gcode_sent(
            None, None, snapshotCommand, None, None)
        self.assertTrue(returnVal is None)
        self.assertTrue(self.Timelapse_GcodeTrigger.CommandIndex == 10)

        # Test RequestingReturnPosition State
        self.Timelapse_GcodeTrigger.State = TimelapseState.RequestingReturnPosition
        returnVal = self.Timelapse_GcodeTrigger.on_gcode_sent(
            None, None, snapshotCommand, None, None)
        self.assertTrue(returnVal is None)
        self.assertTrue(self.Timelapse_GcodeTrigger.CommandIndex == 10)

        # Test TakingSnapshot State
        self.Timelapse_GcodeTrigger.State = TimelapseState.TakingSnapshot
        returnVal = self.Timelapse_GcodeTrigger.on_gcode_sent(
            None, None, snapshotCommand, None, None)
        self.assertTrue(returnVal is None)
        self.assertTrue(self.Timelapse_GcodeTrigger.CommandIndex == 10)

        # Test ResumingPrint State
        self.Timelapse_GcodeTrigger.State = TimelapseState.ResumingPrint
        returnVal = self.Timelapse_GcodeTrigger.on_gcode_sent(
            None, None, snapshotCommand, None, None)
        self.assertTrue(returnVal is None)
        self.assertTrue(self.Timelapse_GcodeTrigger.CommandIndex == 10)

        # Test Completing State
        self.Timelapse_GcodeTrigger.State = TimelapseState.Completing
        returnVal = self.Timelapse_GcodeTrigger.on_gcode_sent(
            None, None, snapshotCommand, None, None)
        self.assertTrue(returnVal is None)
        self.assertTrue(self.Timelapse_GcodeTrigger.CommandIndex == 10)

    def test_GcodeSent_SendingSnapshotGcode_NotInSnapshotGcode(self):
        """Test SendingSnapshotGcode, which watch for the move command and then switch to the state RequestingSnapshotPosition"""
        notInGcodeCommand = "	DEFINITELYnotInTheGcode "
        self.Settings.profiles.current_snapshot().gcode_trigger_enabled = True
        self.Settings.profiles.current_snapshot().layer_trigger_enabled = False
        self.Settings.profiles.current_snapshot().timer_trigger_enabled = False

        # start the timelapse
        self.Timelapse_GcodeTrigger.start_timelapse(
            self.OctoprintTestPrinter, self.OctoprintPrinterProfile, self.FfMpegPath, False)
        # Test suppressing gcodes that aren't in the Snapshot Gcode commands
        snapshotGcodes = SnapshotGcode(False)
        snapshotGcodes.GcodeCommands.extend(
            ["TestCommand1", "TestCommand2", "m105", "TestCommand4", "TestCommand4"])
        snapshotGcodes.SnapshotIndex = 2
        self.Timelapse_GcodeTrigger.SnapshotGcodes = snapshotGcodes
        self.Timelapse_GcodeTrigger.CommandIndex = 0
        # set the snapshot state to SendingMoveCommand
        self.Timelapse_GcodeTrigger.State = TimelapseState.SendingMoveCommand

        # Test a command that is not in the snapshot gcode
        returnVal = self.Timelapse_GcodeTrigger.on_gcode_sent(
            None, None, notInGcodeCommand, None, None)
        self.assertTrue(returnVal is None)
        self.assertTrue(self.Timelapse_GcodeTrigger.CommandIndex == 0)

    def test_GcodeSent_SendingSnapshotGcode_NotMoveCommand(self):
        """Test SendingSnapshotGcode, which watch for the move command and then switch to the state RequestingSnapshotPosition"""

        self.Settings.profiles.current_snapshot().gcode_trigger_enabled = True
        self.Settings.profiles.current_snapshot().layer_trigger_enabled = False
        self.Settings.profiles.current_snapshot().timer_trigger_enabled = False

        # start the timelapse
        self.Timelapse_GcodeTrigger.start_timelapse(
            self.OctoprintTestPrinter, self.OctoprintPrinterProfile, self.FfMpegPath, False)
        # Test suppressing gcodes that aren't in the Snapshot Gcode commands
        snapshotGcodes = SnapshotGcode(False)
        snapshotGcodes.GcodeCommands.extend(
            ["TestCommand1", "TestCommand2", "m105", "TestCommand4", "TestCommand4"])
        snapshotGcodes.SnapshotIndex = 2
        self.Timelapse_GcodeTrigger.SnapshotGcodes = snapshotGcodes
        self.Timelapse_GcodeTrigger.CommandIndex = 0
        # set the snapshot state to SendingMoveCommand
        self.Timelapse_GcodeTrigger.State = TimelapseState.SendingSnapshotGcode

        # Test the all of the commands except the move command to make sure the state doesn't change
        returnVal = self.Timelapse_GcodeTrigger.on_gcode_sent(
            None, None, snapshotGcodes.GcodeCommands[0], None, None)
        self.assertTrue(returnVal is None)
        self.assertTrue(self.Timelapse_GcodeTrigger.CommandIndex == 0)
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.SendingSnapshotGcode)

        returnVal = self.Timelapse_GcodeTrigger.on_gcode_sent(
            None, None, snapshotGcodes.GcodeCommands[2], None, None)
        self.assertTrue(returnVal is None)
        self.assertTrue(self.Timelapse_GcodeTrigger.CommandIndex == 0)
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.SendingSnapshotGcode)

        returnVal = self.Timelapse_GcodeTrigger.on_gcode_sent(
            None, None, snapshotGcodes.GcodeCommands[3], None, None)
        self.assertTrue(returnVal is None)
        self.assertTrue(self.Timelapse_GcodeTrigger.CommandIndex == 0)
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.SendingSnapshotGcode)

        returnVal = self.Timelapse_GcodeTrigger.on_gcode_sent(
            None, None, snapshotGcodes.GcodeCommands[4], None, None)
        self.assertTrue(returnVal is None)
        self.assertTrue(self.Timelapse_GcodeTrigger.CommandIndex == 0)
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.SendingSnapshotGcode)

    def test_GcodeSent_SendingSnapshotGcode_RequestingSnapshotPosition(self):
        """Test SendingSnapshotGcode, which watch for the move command and then switch to the state RequestingSnapshotPosition"""
        self.Settings.profiles.current_snapshot().gcode_trigger_enabled = True
        self.Settings.profiles.current_snapshot().layer_trigger_enabled = False
        self.Settings.profiles.current_snapshot().timer_trigger_enabled = False

        # start the timelapse
        self.Timelapse_GcodeTrigger.start_timelapse(
            self.OctoprintTestPrinter, self.OctoprintPrinterProfile, self.FfMpegPath, False)
        # Test suppressing gcodes that aren't in the Snapshot Gcode commands
        snapshotGcodes = SnapshotGcode(False)
        snapshotGcodes.GcodeCommands.extend(
            ["TestCommand1", "TestCommand2", "m105", "TestCommand4", "TestCommand4"])
        snapshotGcodes.SnapshotIndex = 2
        self.Timelapse_GcodeTrigger.SnapshotGcodes = snapshotGcodes
        # set the snapshot state to SendingMoveCommand
        self.Timelapse_GcodeTrigger.State = TimelapseState.RequestingSnapshotPosition

    def test_SendPositionRequestGcode_Snapshot(self):
        """Test the SendPositionRequestGcode function to make sure it properly handles the Snapshot request"""
        self.Timelapse_GcodeTrigger.OctoprintPrinter = self.OctoprintTestPrinter
        self.Timelapse_GcodeTrigger.SendPositionRequestGcode(False)
        self.assertTrue(
            len(self.Timelapse_GcodeTrigger.OctoprintPrinter.GcodeCommands) == 2)
        self.assertTrue(
            self.Timelapse_GcodeTrigger.OctoprintPrinter.GcodeCommands[0] == "M400")
        self.assertTrue(
            self.Timelapse_GcodeTrigger.OctoprintPrinter.GcodeCommands[1] == "M114")
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.RequestingSnapshotPosition)

    def test_PositionReceived_IncorrectState(self):
        """Test the PositionReceived function"""
        # Test position match, no tolerance necessary
        # Test Pos 0,0,0 when at 0,0,0
        x = 0
        y = 0
        z = 0
        reason = "None"
        payload = {
            "x": x,
            "y": y,
            "z": z,
            "e": 0,
            "reason": reason
        }
        self.Timelapse_GcodeTrigger.State = TimelapseState.Idle
        success, message = self.Timelapse_GcodeTrigger.on_position_received(
            payload)
        self.assertTrue(not success)
        self.assertTrue(message == "Declined - Incorrect State")

    def test_PositionReceived_ReturnPosition_NoSnapshotGcode(self):
        """Test the PositionReceived function"""
        # Test position match, no tolerance necessary

        reason = "None in particular"
        # start the timelapse
        self.Timelapse_GcodeTrigger.start_timelapse(
            self.OctoprintTestPrinter, self.OctoprintPrinterProfile, self.FfMpegPath, False)
        self.Timelapse_GcodeTrigger.State = TimelapseState.RequestingReturnPosition
        snapshotGcodes = SnapshotGcode(False)
        snapshotGcodes.GcodeCommands.extend(
            ["TestCommand1", "TestCommand2", "m105", "TestCommand4", "TestCommand4"])
        snapshotGcodes.SnapshotIndex = 2
        gcodeTest = GcodeTest(None)
        self.Timelapse_GcodeTrigger.Gcode = gcodeTest

        # Test Pos 0,0,0 when at 0,0,0
        x = 0
        y = 0
        z = 0
        payload = {
            "x": x,
            "y": y,
            "z": z,
            "e": 0,
            "reason": reason
        }
        self.Timelapse_GcodeTrigger.Position.XPrevious = 0
        self.Timelapse_GcodeTrigger.Position.YPrevious = 0
        self.Timelapse_GcodeTrigger.Position.ZPrevious = 0
        success, message = self.Timelapse_GcodeTrigger.on_position_received(
            payload)
        self.assertTrue(not success)
        self.assertTrue(message == "Error - No Snapshot Gcode")

    def test_PositionReceived_ReturnPosition(self):
        """Test the PositionReceived function"""
        # Test position match, no tolerance necessary

        reason = "None in particular"
        # start the timelapse
        self.Timelapse_GcodeTrigger.start_timelapse(
            self.OctoprintTestPrinter, self.OctoprintPrinterProfile, self.FfMpegPath, False)
        self.Timelapse_GcodeTrigger.State = TimelapseState.RequestingReturnPosition
        snapshotGcodes = SnapshotGcode(False)
        snapshotGcodes.GcodeCommands.extend(
            ["TestCommand1", "TestCommand2", "m105", "TestCommand4", "TestCommand4"])
        snapshotGcodes.SnapshotIndex = 2
        gcodeTest = GcodeTest(snapshotGcodes)
        self.Timelapse_GcodeTrigger.Gcode = gcodeTest
        # Test Pos 0,0,0 when at 0,0,0
        x = 0
        y = 0
        z = 0
        payload = {
            "x": x,
            "y": y,
            "z": z,
            "e": 0,
            "reason": reason
        }

        self.Timelapse_GcodeTrigger.Position.XPrevious = 0
        self.Timelapse_GcodeTrigger.Position.YPrevious = 0
        self.Timelapse_GcodeTrigger.Position.ZPrevious = 0

        success, message = self.Timelapse_GcodeTrigger.on_position_received(
            payload)
        self.assertTrue(success)
        self.assertTrue(message == "Snapshot Commands Sent")
        self.assertTrue(
            len(self.Timelapse_GcodeTrigger.OctoprintPrinter.GcodeCommands) == 3)
        self.assertTrue(
            self.Timelapse_GcodeTrigger.OctoprintPrinter.GcodeCommands[0] == "TestCommand1")
        self.assertTrue(
            self.Timelapse_GcodeTrigger.OctoprintPrinter.GcodeCommands[1] == "TestCommand2")
        self.assertTrue(
            self.Timelapse_GcodeTrigger.OctoprintPrinter.GcodeCommands[2] == "m105")

    def test_PositionReceived_ReturnPosition_Difference(self):
        """Test the PositionReceived function"""
        # Test position match, no tolerance necessary

        reason = "None in particular"
        # start the timelapse
        self.Timelapse_GcodeTrigger.start_timelapse(
            self.OctoprintTestPrinter, self.OctoprintPrinterProfile, self.FfMpegPath, False)
        self.Timelapse_GcodeTrigger.State = TimelapseState.RequestingReturnPosition
        snapshotGcodes = SnapshotGcode(False)
        snapshotGcodes.GcodeCommands.extend(
            ["TestCommand1", "TestCommand2", "m105", "TestCommand4", "TestCommand4"])
        snapshotGcodes.SnapshotIndex = 2
        gcodeTest = GcodeTest(snapshotGcodes)
        self.Timelapse_GcodeTrigger.Gcode = gcodeTest
        # Test Pos 0,0,0 when at 1,1,1
        x = 0
        y = 0
        z = 0
        payload = {
            "x": x,
            "y": y,
            "z": z,
            "e": 0,
            "reason": reason
        }
        self.Timelapse_GcodeTrigger.Position.XPrevious = 1
        self.Timelapse_GcodeTrigger.Position.YPrevious = 1
        self.Timelapse_GcodeTrigger.Position.ZPrevious = 1

        success, message = self.Timelapse_GcodeTrigger.on_position_received(
            payload)
        self.assertTrue(success)
        self.assertTrue(message == "Snapshot Commands Sent")
        self.assertTrue(
            len(self.Timelapse_GcodeTrigger.OctoprintPrinter.GcodeCommands) == 3)
        self.assertTrue(
            self.Timelapse_GcodeTrigger.OctoprintPrinter.GcodeCommands[0] == "TestCommand1")
        self.assertTrue(
            self.Timelapse_GcodeTrigger.OctoprintPrinter.GcodeCommands[1] == "TestCommand2")
        self.assertTrue(
            self.Timelapse_GcodeTrigger.OctoprintPrinter.GcodeCommands[2] == "m105")
        self.assertTrue(self.Timelapse_GcodeTrigger.Position.x() == 0)
        self.assertTrue(self.Timelapse_GcodeTrigger.Position.y() == 0)
        self.assertTrue(self.Timelapse_GcodeTrigger.Position.z() == 0)

    def test_PositionReceived_SnapshotPosition_Received(self):
        """Test the PositionReceived function"""
        # Test position match, no tolerance necessary
        self.Timelapse_GcodeTrigger.State = TimelapseState.RequestingSnapshotPosition

        # replace the existing take snapshot function, no reason to test this here
        self.Timelapse_GcodeTrigger.TakeSnapshot = ReturnNone
        reason = "None in particular"
        self.Timelapse_GcodeTrigger.Position = Position(
            self.Settings, self.OctoprintPrinterProfile, False)
        self.Timelapse_GcodeTrigger.OctoprintPrinter = self.OctoprintTestPrinter
        self.Timelapse_GcodeTrigger.Printer = self.Settings.profiles.current_printer()
        # Test Pos 0,0,0 when at 0,0,0
        x = 0
        y = 0
        z = 0
        payload = {
            "x": x,
            "y": y,
            "z": z,
            "e": 0,
            "reason": reason
        }
        self.Timelapse_GcodeTrigger.Position.x = 0
        self.Timelapse_GcodeTrigger.Position.y = 0
        self.Timelapse_GcodeTrigger.Position.z = 0
        snapshotGcodes = SnapshotGcode(False)
        snapshotGcodes.X = 0
        snapshotGcodes.Y = 0
        snapshotGcodes.Z = 0
        self.Timelapse_GcodeTrigger.SnapshotGcodes = snapshotGcodes

        success, message = self.Timelapse_GcodeTrigger.on_position_received(
            payload)
        self.assertTrue(success)
        self.assertTrue(message == "Snapshot Taken")
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.TakingSnapshot)

    def test_PositionReceived_SnapshotPosition_ToleranceTest(self):
        """Test the PositionReceived function"""

        # replace the existing take snapshot function, no reason to test this here
        self.Timelapse_GcodeTrigger.ResendSnapshotPositionRequest = ReturnNone
        reason = "None in particular"
        # start the timelapse
        self.Timelapse_GcodeTrigger.start_timelapse(
            self.OctoprintTestPrinter, self.OctoprintPrinterProfile, self.FfMpegPath, False)
        self.Timelapse_GcodeTrigger.State = TimelapseState.RequestingSnapshotPosition
        # allow a difference up to +-0.0025 (0.005 total), but not at or over!

        # Test JUST over tolerance
        # Test Pos 0,0,0 when at 0.005, 0.0025, 0.0025
        x = 0
        y = 0
        z = 0
        payload = {
            "x": x,
            "y": y,
            "z": z,
            "e": 0,
            "reason": reason
        }
        snapshotGcodes = SnapshotGcode(False)
        snapshotGcodes.X = 0
        snapshotGcodes.Y = 0
        snapshotGcodes.Z = 0
        self.Timelapse_GcodeTrigger.SnapshotGcodes = snapshotGcodes
        # Over Tolerance +
        self.Timelapse_GcodeTrigger.Position.x = 0.00500001
        self.Timelapse_GcodeTrigger.Position.y = 0.00500001
        self.Timelapse_GcodeTrigger.Position.z = 0.00500001
        success, message = self.Timelapse_GcodeTrigger.on_position_received(
            payload)
        self.assertTrue(not success)
        self.assertTrue(message == "Incorrect Snapshot Position, Retrying")
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.RequestingSnapshotPosition)
        # At Tolerance +
        self.Timelapse_GcodeTrigger.Position.x = 0.005
        self.Timelapse_GcodeTrigger.Position.y = 0.005
        self.Timelapse_GcodeTrigger.Position.z = 0.005
        success, message = self.Timelapse_GcodeTrigger.on_position_received(
            payload)
        self.assertTrue(success)
        self.assertTrue(message == "Snapshot Taken")
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.TakingSnapshot)
        # reset state
        self.Timelapse_GcodeTrigger.State = TimelapseState.RequestingSnapshotPosition
        # Over Tolerance -
        self.Timelapse_GcodeTrigger.Position.x = -0.00500001
        self.Timelapse_GcodeTrigger.Position.y = -0.00500001
        self.Timelapse_GcodeTrigger.Position.z = -0.00500001
        success, message = self.Timelapse_GcodeTrigger.on_position_received(
            payload)
        self.assertTrue(not success)
        self.assertTrue(message == "Incorrect Snapshot Position, Retrying")
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.RequestingSnapshotPosition)
        # At Tolerance -
        self.Timelapse_GcodeTrigger.Position.x = -0.005
        self.Timelapse_GcodeTrigger.Position.y = -0.005
        self.Timelapse_GcodeTrigger.Position.z = -0.005
        success, message = self.Timelapse_GcodeTrigger.on_position_received(
            payload)
        self.assertTrue(success)
        self.assertTrue(message == "Snapshot Taken")
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.TakingSnapshot)

    def test_PositionReceived_SnapshotPosition_Incorrect(self):
        """Test the PositionReceived function"""

        # start the timelapse
        self.Timelapse_GcodeTrigger.start_timelapse(
            self.OctoprintTestPrinter, self.OctoprintPrinterProfile, self.FfMpegPath, False)

        # Test position match, no tolerance necessary
        self.Timelapse_GcodeTrigger.State = TimelapseState.RequestingSnapshotPosition

        # replace the existing take snapshot function, no reason to test this here
        self.Timelapse_GcodeTrigger.ResendSnapshotPositionRequest = ReturnNone
        reason = "None in particular"

        # Test Pos 0,0,0 when at 1,1,1
        x = 0
        y = 0
        z = 0
        payload = {
            "x": x,
            "y": y,
            "z": z,
            "e": 0,
            "reason": reason
        }
        self.Timelapse_GcodeTrigger.Position.x = 1
        self.Timelapse_GcodeTrigger.Position.y = 1
        self.Timelapse_GcodeTrigger.Position.z = 1

        snapshotGcodes = SnapshotGcode(False)
        snapshotGcodes.ReturnX = 0
        snapshotGcodes.ReturnY = 0
        snapshotGcodes.ReturnZ = 0
        self.Timelapse_GcodeTrigger.SnapshotGcodes = snapshotGcodes

        success, message = self.Timelapse_GcodeTrigger.on_position_received(
            payload)
        self.assertTrue(not success)
        self.assertTrue(message == "Incorrect Snapshot Position, Retrying")
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.RequestingSnapshotPosition)

    def test_ResendSnapshotPositionRequest(self):
        """Test the ResendSnapshotPositionRequest function"""
        # start the timelapse
        # self.Timelapse_GcodeTrigger.OctoprintPrinter = self.OctoprintTestPrinter
        self.Timelapse_GcodeTrigger.SendDelayedSnapshotPositionRequest = ReturnNone
        self.Timelapse_GcodeTrigger.SendSnapshotReturnCommands = ReturnNone
        self.Timelapse_GcodeTrigger.Snapshot = self.Settings.profiles.current_snapshot()
        self.Timelapse_GcodeTrigger.Snapshot.position_request_retry_attemps = 3
        self.Timelapse_GcodeTrigger.Snapshot.position_request_retry_delay_ms = 0  # no delay
        self.Timelapse_GcodeTrigger.PositionRequestAttempts = 0

        self.assertTrue(
            self.Timelapse_GcodeTrigger.ResendSnapshotPositionRequest())
        self.assertTrue(
            self.Timelapse_GcodeTrigger.PositionRequestAttempts == 1)
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.Idle)

        self.assertTrue(
            self.Timelapse_GcodeTrigger.ResendSnapshotPositionRequest())
        self.assertTrue(
            self.Timelapse_GcodeTrigger.PositionRequestAttempts == 2)
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.Idle)

        self.assertTrue(
            self.Timelapse_GcodeTrigger.ResendSnapshotPositionRequest())
        self.assertTrue(
            self.Timelapse_GcodeTrigger.PositionRequestAttempts == 3)
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.Idle)

        # We've reached our max attempts, this one will fail
        self.assertTrue(
            not self.Timelapse_GcodeTrigger.ResendSnapshotPositionRequest())
        self.assertTrue(
            self.Timelapse_GcodeTrigger.PositionRequestAttempts == 4)
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.SendingReturnGcode)

    def test_SendDelayedSnapshotPositionRequest(self):
        """Test the EndSnapshot function routine."""
        self.assertTrue(False, "Not implemented")

    def test_EndSnapshot(self):
        """Test the EndSnapshot function routine."""
        self.Timelapse_GcodeTrigger.OctoprintPrinter = self.OctoprintTestPrinter
        # test the initial state
        # Note that ResetSnapshot will change this to WaitingForTrigger
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.Idle)
        self.assertTrue(self.Timelapse_GcodeTrigger.CommandIndex == -1)
        self.assertTrue(self.Timelapse_GcodeTrigger.SnapshotGcodes is None)
        self.assertTrue(self.Timelapse_GcodeTrigger.SavedCommand is None)
        self.assertTrue(
            self.Timelapse_GcodeTrigger.PositionRequestAttempts == 0)

        # change all vars except state (that should change to WaitingForTrigger)
        self.Timelapse_GcodeTrigger.SnapshotGcodes = ""
        self.Timelapse_GcodeTrigger.SavedCommand = ""
        self.Timelapse_GcodeTrigger.PositionRequestAttempts = 1

        self.Timelapse_GcodeTrigger.OctoprintPrinter.IsPaused = True
        self.Timelapse_GcodeTrigger.EndSnapshot()

        # Note that ResetSnapshot will change this to WaitingForTrigger
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.WaitingForTrigger)
        self.assertTrue(self.Timelapse_GcodeTrigger.CommandIndex == -1)
        self.assertTrue(self.Timelapse_GcodeTrigger.SnapshotGcodes is None)
        self.assertTrue(self.Timelapse_GcodeTrigger.SavedCommand is None)
        self.assertTrue(
            self.Timelapse_GcodeTrigger.PositionRequestAttempts == 0)

    def test_TakeSnapshot(self):
        """Test the TakeSnapshot function routine."""
        self.assertTrue(False, "Not implemented")

    def test_OnSnapshotSuccess(self):
        """Test the OnSnapshotSuccess function routine."""
        self.assertTrue(False, "Not implemented")

    def test_OnSnapshotFail(self):
        """Test the OnSnapshotFail function routine."""
        self.assertTrue(
            self.Timelapse_GcodeTrigger.OnSnapshotFail("Failed") == "Failed")

    def test_OnSnapshotComplete(self):
        """Test the OnSnapshotComplete function routine."""
        self.Timelapse_GcodeTrigger.SendSnapshotReturnCommands = ReturnNone
        self.assertTrue(
            self.Timelapse_GcodeTrigger.OnSnapshotComplete() == None)

    def test_SendSnapshotReturnCommands(self):
        """Test the SendSnapshotReturnCommands function routine."""
        snapshotGcodes = SnapshotGcode(False)
        snapshotGcodes.GcodeCommands.extend(
            ["TestCommand1", "TestCommand2", "m105", "TestCommand4", "TestCommand4"])
        snapshotGcodes.SnapshotIndex = 2
        self.Timelapse_GcodeTrigger.SnapshotGcodes = snapshotGcodes
        gcodeTest = GcodeTest(None)

        self.Timelapse_GcodeTrigger.Gcode = gcodeTest
        self.Timelapse_GcodeTrigger.State = TimelapseState.Idle
        self.Timelapse_GcodeTrigger.OctoprintPrinter = self.OctoprintTestPrinter

        self.Timelapse_GcodeTrigger.SendSnapshotReturnCommands()
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.SendingReturnGcode)

        self.assertTrue(
            len(self.Timelapse_GcodeTrigger.OctoprintPrinter.GcodeCommands) == 2)
        self.assertTrue(
            self.Timelapse_GcodeTrigger.OctoprintPrinter.GcodeCommands[0] == "TestCommand4")
        self.assertTrue(
            self.Timelapse_GcodeTrigger.OctoprintPrinter.GcodeCommands[1] == "TestCommand4")

    def test_EndTimelapse(self):
        """Test the EndTimelapse function routine."""

        self.Timelapse_GcodeTrigger.RenderTimelapse = ReturnNone
        # test the reset portion of the code
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.Idle)
        self.assertTrue(len(self.Timelapse_GcodeTrigger.Triggers) == 0)
        self.assertTrue(self.Timelapse_GcodeTrigger.CommandIndex == -1)
        self.assertTrue(self.Timelapse_GcodeTrigger.SnapshotCount == 0)
        self.assertTrue(self.Timelapse_GcodeTrigger.PrintStartTime is None)
        self.assertTrue(self.Timelapse_GcodeTrigger.SnapshotGcodes is None)
        self.assertTrue(self.Timelapse_GcodeTrigger.SavedCommand is None)
        self.assertTrue(
            self.Timelapse_GcodeTrigger.PositionRequestAttempts == 0)
        self.assertTrue(not self.Timelapse_GcodeTrigger.IsTestMode)
        # change all vars except state

        self.Timelapse_GcodeTrigger.Triggers = ["test"]
        self.Timelapse_GcodeTrigger.CommandIndex = 1
        self.Timelapse_GcodeTrigger.SnapshotCount = 1
        self.Timelapse_GcodeTrigger.PrintStartTime = 1
        self.Timelapse_GcodeTrigger.SnapshotGcodes = ""
        self.Timelapse_GcodeTrigger.SavedCommand = ""
        self.Timelapse_GcodeTrigger.PositionRequestAttempts = 1
        self.Timelapse_GcodeTrigger.IsTestMode = True

        # Test reset in idle state - End Timelapse and retest
        self.Timelapse_GcodeTrigger.end_timelapse()
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.Idle)
        self.assertTrue(len(self.Timelapse_GcodeTrigger.Triggers) == 1)
        self.assertTrue(self.Timelapse_GcodeTrigger.CommandIndex == 1)
        self.assertTrue(self.Timelapse_GcodeTrigger.SnapshotCount == 1)
        self.assertTrue(self.Timelapse_GcodeTrigger.PrintStartTime == 1)
        self.assertTrue(self.Timelapse_GcodeTrigger.SnapshotGcodes == "")
        self.assertTrue(self.Timelapse_GcodeTrigger.SavedCommand == "")
        self.assertTrue(
            self.Timelapse_GcodeTrigger.PositionRequestAttempts == 1)
        self.assertTrue(self.Timelapse_GcodeTrigger.IsTestMode)

        # change to 'waiting for trigger' and end the timelapse - Now it should have reset
        self.Timelapse_GcodeTrigger.State = TimelapseState.WaitingForTrigger
        self.Timelapse_GcodeTrigger.end_timelapse()
        self.assertTrue(self.Timelapse_GcodeTrigger.State ==
                        TimelapseState.Idle)
        self.assertTrue(len(self.Timelapse_GcodeTrigger.Triggers) == 0)
        self.assertTrue(self.Timelapse_GcodeTrigger.CommandIndex == -1)
        self.assertTrue(self.Timelapse_GcodeTrigger.SnapshotCount == 0)
        self.assertTrue(self.Timelapse_GcodeTrigger.PrintStartTime is None)
        self.assertTrue(self.Timelapse_GcodeTrigger.SnapshotGcodes is None)
        self.assertTrue(self.Timelapse_GcodeTrigger.SavedCommand is None)
        self.assertTrue(
            self.Timelapse_GcodeTrigger.PositionRequestAttempts == 0)
        self.assertTrue(not self.Timelapse_GcodeTrigger.IsTestMode)

    def test_RenderTimelapse(self):
        """Test the RenderTimelapse function routine."""
        self.assertTrue(False, "Not Implemented")

    def test_OnRenderStart(self):
        """Test the OnRenderStart function routine."""
        self.Timelapse_GcodeTrigger.OnMovieRendering = ReturnNone
        self.assertTrue(
            self.Timelapse_GcodeTrigger.OnRenderStart("", "") is None)

    def test_OnRenderFail(self):
        """Test the OnRenderFail function routine."""
        self.Timelapse_GcodeTrigger.OnMovieFailed = ReturnNone
        self.assertTrue(self.Timelapse_GcodeTrigger.OnRenderFail(
            "", "", "", "") is None)

    def test_OnRenderSuccess(self):
        """Test the OnRenderSuccess function routine."""
        self.assertTrue(
            self.Timelapse_GcodeTrigger.OnRenderSuccess("", "") is None)

    def test_OnRenderingComplete(self):
        """Test the OnRenderingComplete function routine."""
        self.assertTrue(self.Timelapse_GcodeTrigger.OnRenderComplete() is None)

    def test_OnSynchronizeRenderingComplete(self):
        """Test the OnSynchronizeRenderingComplete function routine."""
        self.Timelapse_GcodeTrigger.OnMovieDone = ReturnNone
        self.assertTrue(
            self.Timelapse_GcodeTrigger.OnSynchronizeRenderingComplete("", "") is None)

    def test_OnSynchronizeRenderingFail(self):
        """Test the OnSynchronizeRenderingFail function routine."""
        self.Timelapse_GcodeTrigger.OnMovieFailed = ReturnNone
        self.assertTrue(
            self.Timelapse_GcodeTrigger.OnSynchronizeRenderingFail("", "") is None)

    def test_OnRenderTimelapseJobComplete(self):
        """Test the OnRenderTimelapseJobComplete function routine."""
        self.assertTrue(
            self.Timelapse_GcodeTrigger.OnRenderTimelapseJobComplete() is None)

    def test_OnMovieRendering(self):
        """Test the OnMovieRendering function routine."""

        self.Timelapse_GcodeTrigger.OnMovieRenderingCallback = None
        self.assertTrue(self.Timelapse_GcodeTrigger.OnMovieRendering(
            "Doesn't Matter") is None)
        self.Timelapse_GcodeTrigger.OnMovieRenderingCallback = ReturnTrue
        self.assertTrue(self.Timelapse_GcodeTrigger.OnMovieRendering(
            "Doesn't Matter") is None)

    def test_OnMovieDone(self):
        """Test the OnMovieDone function routine."""
        self.Timelapse_GcodeTrigger.OnMovieDoneCallback = None
        self.assertTrue(self.Timelapse_GcodeTrigger.OnMovieDone(
            "Doesn't Matter") is None)
        self.Timelapse_GcodeTrigger.OnMovieDoneCallback = ReturnTrue
        self.assertTrue(self.Timelapse_GcodeTrigger.OnMovieDone(
            "Doesn't Matter") is None)

    def test_OnMovieFailed(self):
        """Test the OnMovieFailed function routine."""
        self.Timelapse_GcodeTrigger.OnMovieFailedCallback = None
        self.assertTrue(self.Timelapse_GcodeTrigger.OnMovieFailed(
            "Doesn't Matter") is None)
        self.Timelapse_GcodeTrigger.OnMovieFailedCallback = ReturnTrue
        self.assertTrue(self.Timelapse_GcodeTrigger.OnMovieFailed(
            "Doesn't Matter") is None)

    def test_ReturnGcodeCommandToOctoprint(self):
        """Test the ReturnGcodeCommandToOctoprint function, which strips off commands that move the extruder, or set temps when test mode is enabled."""
        # Should return the original command unless we are in idle state.
        # if we are not in idle state, strip off any extruder movements or temp adjustments/waits
        # set test mode
        self.Timelapse_GcodeTrigger.IsTestMode = True
        # test in idle
        # set the state to waiting for trigger
        self.Timelapse_GcodeTrigger.State = TimelapseState.Idle
        # Send a command, should return None
        self.assertTrue(self.Timelapse_GcodeTrigger.ReturnGcodeCommandToOctoprint(
            "g0 x100.0 y100.0 z100.0 f7200;no extrusion") is None)

        self.Timelapse_GcodeTrigger.State = TimelapseState.WaitingForTrigger
        # Test a command while in WaitingForTrigger state, should NOT return None
        self.assertTrue(self.Timelapse_GcodeTrigger.ReturnGcodeCommandToOctoprint(
            "g0 x100.0 y100.0 z100.0 f7200;no extrusion") is not None)

        self.Timelapse_GcodeTrigger.State = TimelapseState.RequestingReturnPosition
        # Test a command while in RequestingReturnPosition state, should NOT return None
        self.assertTrue(self.Timelapse_GcodeTrigger.ReturnGcodeCommandToOctoprint(
            "g0 x100.0 y100.0 z100.0 f7200;no extrusion") is not None)

        self.Timelapse_GcodeTrigger.State = TimelapseState.RequestingSnapshotPosition
        # Test a command while in RequestingSnapshotPosition state, should NOT return None
        self.assertTrue(self.Timelapse_GcodeTrigger.ReturnGcodeCommandToOctoprint(
            "g0 x100.0 y100.0 z100.0 f7200;no extrusion") is not None)

        self.Timelapse_GcodeTrigger.State = TimelapseState.SendingMoveCommand
        # Test a command while in SendingMoveCommand state, should NOT return None
        self.assertTrue(self.Timelapse_GcodeTrigger.ReturnGcodeCommandToOctoprint(
            "g0 x100.0 y100.0 z100.0 f7200;no extrusion") is not None)

        self.Timelapse_GcodeTrigger.State = TimelapseState.SendingReturnGcode
        # Test a command while in SendingReturnGcode state, should NOT return None
        self.assertTrue(self.Timelapse_GcodeTrigger.ReturnGcodeCommandToOctoprint(
            "g0 x100.0 y100.0 z100.0 f7200;no extrusion") is not None)

        self.Timelapse_GcodeTrigger.State = TimelapseState.SendingSnapshotGcode
        # Test a command while in SendingSnapshotGcode state, should NOT return None
        self.assertTrue(self.Timelapse_GcodeTrigger.ReturnGcodeCommandToOctoprint(
            "g0 x100.0 y100.0 z100.0 f7200;no extrusion") is not None)

        self.Timelapse_GcodeTrigger.State = TimelapseState.TakingSnapshot
        # Test a command while in TakingSnapshot state, should NOT return None
        self.assertTrue(self.Timelapse_GcodeTrigger.ReturnGcodeCommandToOctoprint(
            "g0 x100.0 y100.0 z100.0 f7200;no extrusion") is not None)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTimelapse)
    nittest.TextTestRunner(verbosity=3).run(suite)
