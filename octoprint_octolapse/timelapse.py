# coding=utf-8

# This file is subject to the terms and conditions defined in
# file called 'LICENSE', which is part of this source code package.

import time
import threading
import sys
import uuid

import octoprint_octolapse.utility as utility
from octoprint_octolapse.command import *
from octoprint_octolapse.gcode import SnapshotGcodeGenerator, SnapshotGcode
from octoprint_octolapse.position import Position
from octoprint_octolapse.render import Render, RenderingCallbackArgs
from octoprint_octolapse.settings import (Printer, Rendering, Snapshot, OctolapseSettings)
from octoprint_octolapse.snapshot import CaptureSnapshot
from octoprint_octolapse.trigger import Triggers

class Timelapse(object):

    def __init__(
            self, settings, octoprint_printer, data_folder, timelapse_folder,
            on_print_started=None, on_print_start_failed=None,
            on_snapshot_start=None, on_snapshot_end=None,
            on_render_start=None, on_render_end=None,
            on_timelapse_stopping=None, on_timelapse_stopped=None,
            on_state_changed=None, on_timelapse_start=None,
            on_snapshot_position_error=None, on_position_error=None):
        # config variables - These don't change even after a reset
        self.DataFolder = data_folder
        self.Settings = settings  # type: OctolapseSettings
        self.OctoprintPrinter = octoprint_printer
        self.DefaultTimelapseDirectory = timelapse_folder
        self.OnPrintStartCallback = on_print_started
        self.OnPrintStartFailedCallback = on_print_start_failed
        self.OnRenderStartCallback = on_render_start
        self.OnRenderEndCallback = on_render_end
        self.OnSnapshotStartCallback = on_snapshot_start
        self.OnSnapshotCompleteCallback = on_snapshot_end
        self.TimelapseStoppingCallback = on_timelapse_stopping
        self.TimelapseStoppedCallback = on_timelapse_stopped
        self.OnStateChangedCallback = on_state_changed
        self.OnTimelapseStartCallback = on_timelapse_start
        self.OnSnapshotPositionErrorCallback = on_snapshot_position_error
        self.OnPositionErrorCallback = on_position_error
        self.Responses = Responses()  # Used to decode responses from the 3d printer
        self.Commands = Commands()  # used to parse and generate gcode
        self.Triggers = None
        self.RenderingJobs = set()
        self.PrintEndStatus = "Unknown"
        # Settings that may be different after StartTimelapse is called

        self.OctoprintPrinterProfile = None
        self.PrintStartTime = None
        self.FfMpegPath = None
        self.Snapshot = None
        self.Gcode = None
        self.Printer = None
        self.CaptureSnapshot = None
        self.Position = None
        self.HasSentInitialStatus = False
        self.Rendering = None
        self.State = TimelapseState.Idle
        self.IsTestMode = False
        # State Tracking that should only be reset when starting a timelapse
        self.SnapshotCount = 0

        self.HasBeenStopped = False
        self.TimelapseStopRequested = False
        self.SavedCommand = None
        self.SecondsAddedByOctolapse = 0
        # State tracking variables
        self.RequiresLocationDetectionAfterHome = False

        # fetch position private variables
        self._position_payload = None
        self._position_timeout = 30.0
        self._position_signal = threading.Event()
        self._position_signal.set()

        # get snapshot async private variables
        self._snapshot_success = None
        self._snapshot_timeout = 30.0
        self._snapshot_signal = threading.Event()
        self._snapshot_signal.set()
        self.CurrentProfiles = {}
        self._reset()

    def on_position_received(self, payload):
        if self.State in [
            TimelapseState.AcquiringLocation,
            TimelapseState.TakingSnapshot,
            TimelapseState.WaitingToEndTimelapse,
            TimelapseState.WaitingToRender
        ]:
            self._position_payload = payload
            self._position_signal.set()

    def get_position_async(self, start_gcode=None, end_gcode=None):
        self.Settings.current_debug_profile().log_print_state_change("Octolapse is requesting a position.")
        if self._position_signal.is_set():
            # only clear signal and send a new M114 if we haven't already done that from another thread
            self._position_signal.clear()
            # send any code that is to be run before the position request
            if start_gcode is not None and len(start_gcode) > 0:
                self.OctoprintPrinter.commands(start_gcode)
            # wait for all motion to stop and request the position
            self.OctoprintPrinter.commands(["M400", "M114"])
            # send any remaining gcode
            if end_gcode is not None and len(end_gcode) > 0:
                self.OctoprintPrinter.commands(end_gcode)

        self._position_signal.wait(self._position_timeout)

        if not self._position_signal.is_set():
            # we ran into a timeout while waiting for a fresh position
            return None
        return self._position_payload

    def _on_snapshot_success(self, *args, **kwargs):
        # Increment the number of snapshots received
        self.SnapshotCount += 1
        self._snapshot_success = True
        self._snapshot_signal.set()

    def _on_snapshot_fail(self, *args, **kwargs):
        reason = args[0]
        message = "Failed to download the snapshot.  Reason: {0}".format(
            reason)
        self.Settings.current_debug_profile().log_snapshot_download(message)
        self._snapshot_success = False
        self.SnapshotError = message
        self._snapshot_signal.set()

    def _take_snapshot_async(self):
        snapshot_async_payload = {
            "success": False,
            "error": ""
        }

        if self._snapshot_signal.is_set():
            # only clear signal and send a new M114 if we haven't already done that from another thread
            self._snapshot_signal.clear()
            # start the snapshot
            self.Settings.current_debug_profile().log_snapshot_download("Taking a snapshot.")
            try:
                self.CaptureSnapshot.snap(
                    utility.get_currently_printing_filename(self.OctoprintPrinter), self.SnapshotCount,
                    on_success=self._on_snapshot_success,
                    on_fail=self._on_snapshot_fail
                )
                self._snapshot_signal.wait(self._snapshot_timeout)

                if not self._snapshot_signal.is_set():
                    # we ran into a timeout while waiting for a fresh position
                    snapshot_async_payload["error"] = \
                        "Snapshot timed out in {0} seconds.".format(self._snapshot_timeout)
                    return snapshot_async_payload

                snapshot_async_payload["success"] = True
                return self._snapshot_success

            except Exception as e:
                self.Settings.current_debug_profile().log_exception(e)
                snapshot_async_payload["error"] = "An unexpected error was encountered while taking a snapshot"

        return snapshot_async_payload

    def _take_timelapse_snapshot(self, trigger, triggering_command):
        timelapse_snapshot_payload = {
            "starting_position": None,
            "snapshot_position": None,
            "return_position": None,
            "snapshot_gcode": None,
            "snapshot_payload": None,
            "current_snapshot_time": 0,
            "total_snapshot_time": 0,
            "success": False,
            "error": ""
        }

        try:

            # create the GCode for the timelapse and store it
            snapshot_gcode = self.Gcode.create_snapshot_gcode(
                self.Position,
                trigger,
                triggering_command
            )
            assert (isinstance(snapshot_gcode, SnapshotGcode))

            # wait for the current position
            current_position = self.get_position_async(start_gcode=snapshot_gcode.StartGcode)
            # record the position
            timelapse_snapshot_payload["starting_position"] = current_position
            # todo: check current position

            # save the gcode fo the payload
            timelapse_snapshot_payload["snapshot_gcode"] = snapshot_gcode

            # start our snapshot timer AFTER we receive the initial position, since this tells us when the printer
            # has completed all of the gcode that was queued up.
            snapshot_start_time = time.time()

            # park the printhead in the snapshot position
            current_position = self.get_position_async(start_gcode=snapshot_gcode.SnapshotCommands)
            # record the position
            timelapse_snapshot_payload["snapshot_position"] = current_position
            # record the time
            timelapse_snapshot_payload["snapshot_time"] = time.time() - snapshot_start_time

            # todo: check current position

            # take the snapshot
            snapshot_async_payload = self._take_snapshot_async()
            # record snapshot payload
            timelapse_snapshot_payload["snapshot_payload"] = snapshot_async_payload
            # record the time
            timelapse_snapshot_payload["snapshot_time"] = time.time() - snapshot_start_time

            # return the printhead to the start position
            current_position = self.get_position_async(
                start_gcode=snapshot_gcode.ReturnCommands
            )

            # send any remaining gcode commands
            if len(snapshot_gcode.EndGcode)>0:
                current_position = self.get_position_async(
                    start_gcode=snapshot_gcode.EndGcode
                )
            # record the time
            # note that the previous get_position_async call returns right after sending the end gcode, so this
            # should add a negligible amount of time
            current_snapshot_time = time.time() - snapshot_start_time
            self.SecondsAddedByOctolapse += current_snapshot_time
            # record the position
            timelapse_snapshot_payload["return_position"] = current_position
            timelapse_snapshot_payload["current_snapshot_time"] = current_snapshot_time
            timelapse_snapshot_payload["total_snapshot_time"] = self.SecondsAddedByOctolapse
            # we've completed the procedure, set success
            timelapse_snapshot_payload["success"] = True
        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)
            timelapse_snapshot_payload["error"] = "An unexpected error was encountered while running the timelapse " \
                                                  "snapshot procedure. "

        return timelapse_snapshot_payload

    def alter_gcode_for_trigger(self, command):

        # We don't want to send the snapshot command to the printer, or any of
        # the SupporessedSavedCommands (gcode.py)
        if command is None or command == (None,) or command in self.Commands.SuppressedSavedCommands:
            # this will suppress the command since it won't be added to our snapshot commands list
            return None
        # adjust the triggering command for test mode
        command = self.Commands.get_test_mode_command_string(command)
        if command == "":
            return None
        # send the triggering command
        return command

    # public functions
    def start_timelapse(
            self, settings, octoprint_printer_profile, ffmpeg_path, g90_influences_extruder):
        # we must supply the settings first!  Else reset won't work properly.
        self._reset()
        # in case the settings have been destroyed and recreated
        self.Settings = settings
        # time tracking - how much time did we add to the print?
        self.SnapshotCount = 0
        self.SecondsAddedByOctolapse = 0
        self.HasSentInitialStatus = False
        self.RequiresLocationDetectionAfterHome = False
        self.OctoprintPrinterProfile = octoprint_printer_profile
        self.FfMpegPath = ffmpeg_path
        self.PrintStartTime = time.time()
        self.Snapshot = Snapshot(self.Settings.current_snapshot())
        self.Gcode = SnapshotGcodeGenerator(
            self.Settings, octoprint_printer_profile)
        self.Printer = Printer(self.Settings.current_printer())
        self.Rendering = Rendering(self.Settings.current_rendering())
        self.CaptureSnapshot = CaptureSnapshot(
            self.Settings, self.DataFolder, print_start_time=self.PrintStartTime)
        self.Position = Position(
            self.Settings, octoprint_printer_profile, g90_influences_extruder)
        self.State = TimelapseState.WaitingForTrigger
        self.IsTestMode = self.Settings.current_debug_profile().is_test_mode
        self.Triggers = Triggers(self.Settings)
        self.Triggers.create()

        # take a snapshot of the current settings for use in the Octolapse Tab
        self.CurrentProfiles = self.Settings.get_profiles_dict()

        # fetch position private variables
        self._position_payload = None
        self._position_timeout = 30.0
        self._position_signal.set()

        # get snapshot async private variables
        self._snapshot_success = None
        self._snapshot_timeout = 30.0
        self._snapshot_signal.set()

        # send an initial state message
        self._on_timelapse_start()

    def to_state_dict(self):
        try:

            position_dict = None
            position_state_dict = None
            extruder_dict = None
            trigger_state = None
            if self.Settings is not None:

                if self.Settings.show_position_changes and self.Position is not None:
                    position_dict = self.Position.to_position_dict()
                if self.Settings.show_position_state_changes and self.Position is not None:
                    position_state_dict = self.Position.to_state_dict()
                if self.Settings.show_extruder_state_changes and self.Position is not None:
                    extruder_dict = self.Position.Extruder.to_dict()
                if self.Settings.show_trigger_state_changes and self.Triggers is not None:
                    trigger_state = {
                        "Name": self.Triggers.Name,
                        "Triggers": self.Triggers.state_to_list()
                    }
            state_dict = {
                "Extruder": extruder_dict,
                "Position": position_dict,
                "PositionState": position_state_dict,
                "TriggerState": trigger_state
            }
            return state_dict
        except Exception as e:
            self.Settings.CurrentDebugProfile().log_exception(e)
        # if we're here, we've reached and logged an error.
        return {
            "Extruder": None,
            "Position": None,
            "PositionState": None,
            "TriggerState": None
        }

    def stop_snapshots(self, message=None, error=False):
        self.State = TimelapseState.WaitingToRender
        if self.TimelapseStoppedCallback is not None:
            self.TimelapseStoppedCallback(message, error)
        return True

    def on_print_failed(self):
        if self.State != TimelapseState.Idle:
            self.end_timelapse("FAILED")

    def on_print_disconnecting(self):
        if self.State != TimelapseState.Idle:
            self.end_timelapse("DISCONNECTING")

    def on_print_disconnected(self):
        if self.State != TimelapseState.Idle:
            self.end_timelapse("DISCONNECTED")

    def on_print_canceled(self):
        if self.State != TimelapseState.Idle:
            self.end_timelapse("CANCELED")

    def on_print_completed(self):
        if self.State != TimelapseState.Idle:
            self.end_timelapse("COMPLETED")

    def end_timelapse(self, print_status):
        self.PrintEndStatus = print_status
        try:
            if self.State in [
                TimelapseState.WaitingForTrigger, TimelapseState.WaitingToRender, TimelapseState.WaitingToEndTimelapse
            ]:
                if not self._render_timelapse(self.PrintEndStatus):
                    if self.OnRenderEndCallback is not None:
                        payload = RenderingCallbackArgs(
                            "Could not start timelapse job.",
                            -1,
                            "unknown",
                            "unknown",
                            "unknown",
                            "unknown",
                            "unknown",
                            "unknown",
                            False,
                            0,
                            0,
                            "RENDER")
                        self.OnRenderEndCallback(payload)
                self._reset()
            elif self.State != TimelapseState.Idle:
                self.State = TimelapseState.WaitingToEndTimelapse

        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)

    def on_print_paused(self):
        try:
            if self.State == TimelapseState.Idle:
                return
            elif self.State < TimelapseState.WaitingToRender:
                self.Settings.current_debug_profile().log_print_state_change("Print Paused.")
                self.Triggers.pause()
        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)

    def on_print_resumed(self):
        try:
            if self.State == TimelapseState.Idle:
                return
            elif self.State < TimelapseState.WaitingToRender:
                self.Triggers.resume()
        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)

    def is_timelapse_active(self):
        if (
            self.Settings is None
            or self.State in [TimelapseState.Idle, TimelapseState.WaitingToRender]
            or self.Triggers.count() < 1
        ):
            return False
        return True

    def get_is_rendering(self):
        return len(self.RenderingJobs) > 0

    def on_print_start(self, tags):
        if self.OnPrintStartCallback is not None:
            self.OnPrintStartCallback(tags)

    def on_print_start_failed(self, message):
        if self.OnPrintStartFailedCallback is not None:
            self.OnPrintStartFailedCallback(message)

    def on_gcode_queuing(self, cmd, cmd_type, gcode, tags):
        # detect print start
        if (
            self.Settings.is_octolapse_enabled and
            self.State == TimelapseState.Idle and
            self.OctoprintPrinter.is_printing() and
            set(['trigger:comm.start_print']) <= tags
        ):
            self.Settings.current_debug_profile().log_print_state_change(
                "Print Start Detected.  Command: {0}, Tags:{1}".format(cmd, tags)
            )
            if self.OctoprintPrinter.set_job_on_hold(True):
                try:
                    if 'fileline:1' in tags or 'filesentline:1' in tags:
                        self.on_print_start(tags)
                        # resend the command while we have the job lock.  This is important else your first
                        # two gcodes will run out of order.
                        if self.State == TimelapseState.WaitingForTrigger:
                            self.OctoprintPrinter.commands(cmd)
                        # suppress the current command so it doesn't get sent twice
                    return None,
                finally:
                    self.OctoprintPrinter.set_job_on_hold(False)
            else:
                self.on_print_start_failed(
                    "Octolapse was unable to start.  Unable to acquire the job lock."
                )

        # if the timelapse is not active, exit without changing any gcode
        if not self.is_timelapse_active():
            return
        try:
            self.Settings.current_debug_profile().log_gcode_queuing(
                "Queuing Command: Command Type:{0}, gcode:{1}, cmd: {2}, tags: {3}".format(cmd_type, gcode, cmd, tags))
            # update the position tracker so that we know where all of the axis are.
            # We will need this later when generating snapshot gcode so that we can return to the previous
            # position
            cmd = cmd.upper().strip()
            # create our state change dictionaries
            position_change_dict = None
            position_state_change_dict = None
            extruder_change_dict = None
            trigger_change_list = None
            self.Position.update(cmd)

            # capture any changes, if necessary, to the position, position state and extruder state
            # Note:  We'll get the trigger state later
            if (self.Settings.show_position_changes
                    and (self.Position.has_position_changed() or not self.HasSentInitialStatus)):
                position_change_dict = self.Position.to_position_dict()
            if (self.Settings.show_position_state_changes
                    and (self.Position.has_state_changed() or not self.HasSentInitialStatus)):
                position_state_change_dict = self.Position.to_state_dict()
            if (self.Settings.show_extruder_state_changes
                    and (self.Position.Extruder.has_changed() or not self.HasSentInitialStatus)):
                extruder_change_dict = self.Position.Extruder.to_dict()
            # get the position state in case it has changed
            # if there has been a position or extruder state change, inform any listener
            is_snapshot_gcode_command = self._is_snapshot_command(cmd)

            # make sure we're not using inches
            is_metric = self.Position.is_metric()
            if is_metric is None and self.Position.has_position_error():
                self.stop_snapshots(
                    "The printer profile requires an explicit G21 command before any position altering/setting "
                    "commands, including any home commands.  Stopping timelapse, but continuing the print. ",
                    error=True
                )
            elif not is_metric and self.Position.has_position_error():
                if self.Printer.units_default == "inches":
                    self.stop_snapshots(
                        "The printer profile uses 'inches' as the default unit of measurement.  In order to use "
                        "Octolapse, a G21 command must come before any position altering/setting commands, including"
                        " any home commands.  Stopping timelapse, but continuing the print. ",
                        error=True
                    )
                else:
                    self.stop_snapshots(
                        "The gcode file contains a G20 command (set units to inches), which Octolapse does not "
                        "support.  Stopping timelapse, but continuing the print.",
                        error=True
                    )
            elif self.Position.has_position_error(0):
                self._on_position_error()
            # check to see if we've just completed a home command
            elif (self.State == TimelapseState.WaitingForTrigger
                    and (self.Position.requires_location_detection(1)) and self.OctoprintPrinter.is_printing()):

                self.State = TimelapseState.AcquiringLocation

                def acquire_position_async(post_position_command):
                    try:
                        self.Settings.current_debug_profile().log_print_state_change(
                            "A position altering command has been detected.  Fetching and updating position.  "
                            "Position Command: {0}".format(post_position_command))
                        # Undo the last position update, we will be resending the command
                        self.Position.undo_update()
                        current_position = self.get_position_async()

                        if current_position is None:
                            self.Settings.current_debug_profile().log_print_state_change(
                                "Unable to acquire a position.")
                        else:
                            # update position
                            self.Position.update_position(
                                x=current_position["x"],
                                y=current_position["y"],
                                z=current_position["z"],
                                e=current_position["e"],
                                force=True,
                                calculate_changes=True)

                            # adjust the triggering command
                            if post_position_command is not None and post_position_command != (None,):
                                post_position_command = self.Commands.get_test_mode_command_string(
                                    post_position_command
                                )
                                if post_position_command != "":
                                    self.Settings.current_debug_profile().log_print_state_change(
                                        "Sending saved command - {0}.".format(post_position_command))
                                    # send the triggering command
                                    self.OctoprintPrinter.commands(post_position_command)
                            # set the state
                            if self.State == TimelapseState.AcquiringLocation:
                                self.State = TimelapseState.WaitingForTrigger

                            self.Settings.current_debug_profile().log_snapshot_download("Position Acquired")

                    finally:
                        try:
                            if self.State == TimelapseState.WaitingToEndTimelapse:
                                self.end_timelapse(self.PrintEndStatus)
                        finally:
                            self.OctoprintPrinter.set_job_on_hold(False)

                if self.OctoprintPrinter.set_job_on_hold(True):
                    thread = threading.Thread(target=acquire_position_async, args=[cmd])
                    thread.daemon = True
                    thread.start()
                    return None,
            elif (self.State == TimelapseState.WaitingForTrigger
                  and self.OctoprintPrinter.is_printing()
                  and not self.Position.has_position_error(0)):
                self.Triggers.update(self.Position, cmd)

                # If our triggers have changed, update our dict
                if self.Settings.show_trigger_state_changes and self.Triggers.has_changed():
                    trigger_change_list = self.Triggers.changes_to_list()

                _first_triggering = self.get_first_triggering()

                if _first_triggering:
                    # set the state
                    self.State = TimelapseState.TakingSnapshot

                    def take_snapshot_async(triggering_command, trigger):
                        timelapse_snapshot_payload = None
                        try:
                            self.Settings.current_debug_profile().log_snapshot_download(
                                "About to take a snapshot.  Triggering Command: {0}".format(
                                    triggering_command))
                            if self.OnSnapshotStartCallback is not None:
                                self.OnSnapshotStartCallback()

                            # Undo the last position update, we're not going to be using it!
                            self.Position.undo_update()

                            # take the snapshot
                            timelapse_snapshot_payload = self._take_timelapse_snapshot(trigger, triggering_command)

                            self.Settings.current_debug_profile().log_snapshot_download("The snapshot has completed")
                        finally:

                            # set the state
                            if self.State == TimelapseState.TakingSnapshot:
                                self.State = TimelapseState.WaitingForTrigger
                            timelapse_ended = False
                            try:
                                if self.State == TimelapseState.WaitingToEndTimelapse:
                                    timelapse_ended = False
                                    self.end_timelapse(self.PrintEndStatus)
                            finally:
                                self.OctoprintPrinter.set_job_on_hold(False)

                            if not timelapse_ended:
                                # notify that we're finished, but only if we haven't just stopped the timelapse.
                                self._on_trigger_snapshot_complete(timelapse_snapshot_payload)

                    if self.OctoprintPrinter.set_job_on_hold(True):
                        thread = threading.Thread(target=take_snapshot_async, args=[cmd, _first_triggering])
                        thread.daemon = True
                        thread.start()
                        return None,
            elif self.State == TimelapseState.TakingSnapshot:
                # Don't do anything further to any commands unless we are
                # taking a timelapse , or if octolapse paused the print.
                # suppress any commands we don't, under any cirumstances,
                # to execute while we're taking a snapshot

                if cmd in self.Commands.SuppressedSnapshotGcodeCommands:
                    cmd = None,  # suppress the command

            if is_snapshot_gcode_command:
                # in all cases do not return the snapshot command to the printer.
                # It is NOT a real gcode and could cause errors.
                cmd = None,

            # notify any callbacks
            self._on_state_changed(
                position_change_dict, position_state_change_dict, extruder_change_dict, trigger_change_list)
            self.HasSentInitialStatus = True

            if cmd != (None,):
                cmd = self._get_command_for_octoprint(cmd)
        except:
            e = sys.exc_info()[0]
            self.Settings.current_debug_profile().log_exception(e)
            raise

        return cmd

    def get_first_triggering(self):
        try:
            # make sure we're in a state that could want to check for triggers
            if not self.State == TimelapseState.WaitingForTrigger:
                return False
            # see if the PREVIOUS command triggered (that means current gcode gets sent if the trigger[0]
            # is triggering
            first_trigger = self.Triggers.get_first_triggering(0, Triggers.TRIGGER_TYPE_IN_PATH)

            if first_trigger:
                self.Settings.current_debug_profile().log_triggering("An in-path snapshot is triggering")
                return first_trigger

            first_trigger = self.Triggers.get_first_triggering(1, Triggers.TRIGGER_TYPE_DEFAULT)
            if first_trigger:  # We're triggering
                self.Settings.current_debug_profile().log_triggering("A snapshot is triggering")
                # notify any callbacks
                return first_trigger
        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)
            # no need to re-raise here, the trigger just won't happen
        return False

    def on_gcode_sent(self, cmd, cmd_type, gcode):
        self.Settings.current_debug_profile().log_gcode_sent(
            "Sent to printer: Command Type:{0}, gcode:{1}, cmd: {2}".format(cmd_type, gcode, cmd))

    # internal functions
    ####################
    def _get_command_for_octoprint(self, cmd):

        if cmd is None or cmd == (None,):
            return cmd

        if self.IsTestMode and self.State >= TimelapseState.WaitingForTrigger:
            return self.Commands.alter_for_test_mode(cmd)
        # if we were given a list, return it.
        if isinstance(cmd, list):
            return cmd
        # if we were given a command return None (don't change the command at all)
        return None

    def _on_state_changed(
            self, position_change_dict, position_state_change_dict, extruder_change_dict, trigger_change_list):
        """Notifies any callbacks about any changes contained in the dictionaries.
        If you send a dict here the client will get a message, so check the
        settings to see if they are subscribed to notifications before populating the dictinaries!"""
        trigger_changes_dict = None
        try:

            # Notify any callbacks
            if (self.OnStateChangedCallback is not None
                and (position_change_dict is not None
                     or position_state_change_dict is not None
                     or extruder_change_dict is not None
                     or trigger_change_list is not None)):

                if trigger_change_list is not None and len(trigger_change_list) > 0:
                    trigger_changes_dict = {
                        "Name": self.Triggers.Name,
                        "Triggers": trigger_change_list
                    }
                change_dict = {
                    "Extruder": extruder_change_dict,
                    "Position": position_change_dict,
                    "PositionState": position_state_change_dict,
                    "TriggerState": trigger_changes_dict
                }

                if (change_dict["Extruder"] is not None
                        or change_dict["Position"] is not None
                        or change_dict["PositionState"] is not None
                        or change_dict["TriggerState"] is not None):
                    self.OnStateChangedCallback(change_dict)
        except Exception as e:
            # no need to re-raise, callbacks won't be notified, however.
            self.Settings.current_debug_profile().log_exception(e)

    def _is_snapshot_command(self, command):
        command_name = get_gcode_from_string(command)
        snapshot_command_name = get_gcode_from_string(self.Printer.snapshot_command)
        return command_name == snapshot_command_name

    def _is_trigger_waiting(self):
        # make sure we're in a state that could want to check for triggers
        if not self.State == TimelapseState.WaitingForTrigger:
            return None
        # Loop through all of the active currentTriggers
        waiting_trigger = self.Triggers.get_first_waiting()
        if waiting_trigger is not None:
            return True
        return False

    def _on_position_error(self):
        message = self.Position.position_error(0)
        self.Settings.current_debug_profile().log_error(message)
        if self.OnPositionErrorCallback is not None:
            self.OnPositionErrorCallback(message)

    def _on_trigger_snapshot_complete(self, snapshot_payload):

        if self.OnSnapshotCompleteCallback is not None:
            payload = {
                "success": snapshot_payload["success"],
                "error": snapshot_payload["error"],
                "snapshot_count": self.SnapshotCount,
                "total_snapshot_time": snapshot_payload["total_snapshot_time"],
                "current_snapshot_time": snapshot_payload["total_snapshot_time"]
            }
            self.OnSnapshotCompleteCallback(payload)

    def _render_timelapse(self, print_end_state):
        # make sure we have a non null TimelapseSettings object.  We may have terminated the timelapse for some reason
        if self.Rendering.enabled:
            self.Settings.current_debug_profile().log_render_start("Started Rendering Timelapse")
            # we are rendering, set the state before starting the rendering job.

            timelapse_render_job = Render(
                self.Settings, self.Snapshot, self.Rendering, self.DataFolder,
                self.DefaultTimelapseDirectory, self.FfMpegPath, 1,
                time_added=self.SecondsAddedByOctolapse, on_render_start=self._on_render_start,
                on_render_fail=self._on_render_fail, on_render_success=self._on_render_success,
                on_render_complete=self.on_render_complete, on_after_sync_fail=self._on_synchronize_rendering_fail,
                on_after_sync_success=self._on_synchronize_rendering_complete, on_complete=self._on_render_end
            )
            job_id = "TimelapseRenderJob_{0}".format(str(uuid.uuid4()))
            self.RenderingJobs.add(job_id)
            try:

                timelapse_render_job.process(job_id, utility.get_currently_printing_filename(
                    self.OctoprintPrinter), self.PrintStartTime, time.time(), print_end_state)
                return True
            except Exception as e:
                self.Settings.current_debug_profile().log_exception(e)
                self.RenderingJobs.remove(job_id)

        return False

    def _on_render_start(self, *args, **kwargs):
        job_id = args[0]
        self.Settings.current_debug_profile().log_render_start(
            "Started rendering/synchronizing the timelapse. JobId: {0}".format(job_id))
        payload = args[1]
        # notify the caller
        if self.OnRenderStartCallback is not None:
            self.OnRenderStartCallback(payload)

    def _on_render_fail(self, *args, **kwargs):

        job_id = args[0]
        self.Settings.current_debug_profile().log_render_fail(
            "The timelapse rendering failed. JobId: {0}".format(job_id))

    def _on_render_success(self, *args, **kwargs):
        job_id = args[0]
        self.Settings.current_debug_profile().log_render_complete(
            "Rendering completed successfully. JobId: {0}".format(job_id))
        # payload = args[1]

    def on_render_complete(self, *args, **kwargs):
        job_id = args[0]
        # payload = args[1]
        self.Settings.current_debug_profile().log_render_complete(
            "Completed rendering the timelapse. JobId: {0}".format(job_id))

    def _on_synchronize_rendering_fail(self, *args, **kwargs):
        job_id = args[0]
        payload = args[1]
        self.Settings.current_debug_profile().log_render_sync(
            "Synchronization with the default timelapse plugin failed."
            "  JobId: {0}, Reason: {1}".format(job_id, payload.Reason)
        )

    def _on_synchronize_rendering_complete(self, *args, **kwargs):
        job_id = args[0]
        # payload = args[1]
        self.Settings.current_debug_profile().log_render_sync(
            "Synchronization with the default timelapse plugin was successful. JobId: {0}".format(job_id))

    def _on_render_end(self, *args, **kwargs):
        job_id = args[0]
        payload = args[1]

        self.Settings.current_debug_profile().log_render_complete("Completed rendering. JobId: {0}".format(job_id))
        assert (isinstance(payload, RenderingCallbackArgs))

        # Remove job from list.  If it is not there, raise an exception.
        self.RenderingJobs.remove(job_id)

        if payload.ErrorType is not None:
            if self.Snapshot.cleanup_after_render_fail:
                self.CaptureSnapshot.clean_snapshots(utility.get_snapshot_temp_directory(self.DataFolder))
        else:
            if self.Snapshot.cleanup_after_render_complete:
                self.CaptureSnapshot.clean_snapshots(utility.get_snapshot_temp_directory(self.DataFolder))

        if self.OnRenderEndCallback is not None:
            self.OnRenderEndCallback(payload)

    def _on_timelapse_start(self):
        if self.OnTimelapseStartCallback is None:
            return
        self.OnTimelapseStartCallback()

    def _reset(self):
        self.State = TimelapseState.Idle
        self.HasSentInitialStatus = False
        if self.Triggers is not None:
            self.Triggers.reset()
        self.CommandIndex = -1

        self.PrintStartTime = None
        self.SnapshotGcodes = None
        self.SavedCommand = None
        self.PositionRequestAttempts = 0
        self.IsTestMode = False

        self.ReturnPositionReceivedTime = None
        # A list of callbacks who want to be informed when a timelapse ends
        self.TimelapseStopRequested = False
        self._snapshot_success = False
        self.SnapshotError = ""
        self.HasBeenStopped = False
        self.CurrentProfiles = {
            "printer": "",
            "stabilization": "",
            "snapshot": "",
            "rendering": "",
            "camera": "",
            "debug_profile": ""
        }
        # fetch position private variables
        self._position_payload = None
        self._position_timeout = 30.0
        self._position_signal = threading.Event()
        self._position_signal.set()

        # get snapshot async private variables
        self._snapshot_success = None
        self._snapshot_timeout = 30.0
        self._snapshot_signal = threading.Event()
        self._snapshot_signal.set()

    def _reset_snapshot(self):
        self.State = TimelapseState.WaitingForTrigger
        self.CommandIndex = -1
        self.SnapshotGcodes = None
        self.SavedCommand = None
        self.PositionRequestAttempts = 0
        self._snapshot_success = False
        self.SnapshotError = ""


class TimelapseState(object):
    Idle = 1
    WaitingForTrigger = 2
    AcquiringLocation = 3
    TakingSnapshot = 4
    WaitingToRender = 5
    WaitingToEndTimelapse = 6
