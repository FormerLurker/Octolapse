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

import os
import threading
import time
import uuid
from Queue import Queue

import octoprint_octolapse.utility as utility
from octoprint_octolapse.gcode import SnapshotGcodeGenerator, SnapshotGcode
from octoprint_octolapse.gcode_parser import Commands
from octoprint_octolapse.position import Position
from octoprint_octolapse.render import Render, RenderingCallbackArgs, RenderError
from octoprint_octolapse.settings import (Printer, Rendering, Snapshot, OctolapseSettings)
from octoprint_octolapse.snapshot import CaptureSnapshot
from octoprint_octolapse.trigger import Triggers


class Timelapse(object):

    def __init__(
            self, settings, octoprint_printer, data_folder, timelapse_folder,
            on_print_started=None, on_print_start_failed=None,
            on_snapshot_start=None, on_snapshot_end=None,
            on_render_start=None, on_render_success=None, on_render_error=None,
            on_timelapse_stopping=None, on_timelapse_stopped=None,
            on_state_changed=None, on_timelapse_start=None, on_timelapse_end=None,
            on_snapshot_position_error=None, on_position_error=None, on_plugin_message_sent=None):
        # config variables - These don't change even after a reset
        self.DataFolder = data_folder
        self.Settings = settings  # type: OctolapseSettings
        self.OctoprintPrinter = octoprint_printer
        self.DefaultTimelapseDirectory = timelapse_folder
        self.OnPrintStartCallback = on_print_started
        self.OnPrintStartFailedCallback = on_print_start_failed
        self.OnRenderStartCallback = on_render_start
        self.OnRenderSuccessCallback = on_render_success
        self.OnRenderErrorCallback = on_render_error
        self.OnSnapshotStartCallback = on_snapshot_start
        self.OnSnapshotCompleteCallback = on_snapshot_end
        self.TimelapseStoppingCallback = on_timelapse_stopping
        self.TimelapseStoppedCallback = on_timelapse_stopped
        self.OnStateChangedCallback = on_state_changed
        self.OnTimelapseStartCallback = on_timelapse_start
        self.OnTimelapseEndCallback = on_timelapse_end
        self.OnSnapshotPositionErrorCallback = on_snapshot_position_error
        self.OnPositionErrorCallback = on_position_error
        self.OnPluginMessageSentCallback = on_plugin_message_sent
        self.Commands = Commands()  # used to parse and generate gcode
        self.Triggers = None
        self.PrintEndStatus = "Unknown"
        self.LastStateChangeMessageTime = None
        self.StateChangeMessageThread = None
        # Settings that may be different after StartTimelapse is called

        self.OctoprintPrinterProfile = None
        self.PrintStartTime = None
        self.FfMpegPath = None
        self.Snapshot = None
        self.Gcode = None
        self.Printer = None
        self.Camera = None
        self.CaptureSnapshot = None
        self.Position = None
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
        self._position_request_sent = False
        # fetch position private variables
        self._position_payload = None
        self._position_timeout_long = 60.0
        self._position_timeout_short = 10.0
        self._position_signal = threading.Event()
        self._position_signal.set()

        # get snapshot async private variables
        self._snapshot_success = False
        # It shouldn't take more than 5 seconds to take a snapshot!
        self._snapshot_timeout = 5.0
        self._snapshot_signal = threading.Event()
        self._snapshot_signal.set()
        self._most_recent_snapshot_payload = None

        self.CurrentProfiles = {}
        self.CurrentFileLine = 0

        # snapshot thread queue
        self._rendering_task_queue = Queue(maxsize=0)
        self._reset()

    def start_timelapse(
            self, settings, octoprint_printer_profile, ffmpeg_path, g90_influences_extruder):
        # we must supply the settings first!  Else reset won't work properly.
        self._reset()
        # in case the settings have been destroyed and recreated
        self.Settings = settings
        # time tracking - how much time did we add to the print?
        self.SnapshotCount = 0
        self.SecondsAddedByOctolapse = 0
        self.RequiresLocationDetectionAfterHome = False
        self.OctoprintPrinterProfile = octoprint_printer_profile
        self.FfMpegPath = ffmpeg_path
        self.PrintStartTime = time.time()
        self.Snapshot = Snapshot(self.Settings.current_snapshot())
        self.Gcode = SnapshotGcodeGenerator(
            self.Settings, octoprint_printer_profile)
        self.Printer = Printer(self.Settings.current_printer())
        self.Camera = self.Settings.current_camera()
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

        # send an initial state message
        self._on_timelapse_start()

    def on_position_received(self, payload):
        # added new position request sent flag so that we can prevent position requests NOT from Octolapse from
        # triggering a snapshot.
        if (
            self.State in [TimelapseState.AcquiringLocation, TimelapseState.TakingSnapshot]
            and self._position_request_sent
        ):
            # set flag to false so that it can be triggered again after the next M114 sent by Octolapse
            self._position_request_sent = False
            self.Settings.current_debug_profile().log_print_state_change(
                "Octolapse has received an position request response.")
            self._position_payload = payload
            self._position_signal.set()
        else:
            self.Settings.current_debug_profile().log_print_state_change(
                "Octolapse has received an position response but did not request one.  Ignoring.")

    def send_snapshot_gcode_array(self, gcode_array):
        self.OctoprintPrinter.commands(gcode_array, tags={"snapshot_gcode"})

    # requests a position from the printer (m400-m114), and can send optional gcode before the position request.
    # this ensures any gcode sent in the start_gcode parameter will be executed before the function returns.
    def get_position_async(self, start_gcode=None, timeout=None):
        if timeout is None:
            timeout = self._position_timeout_long

        self.Settings.current_debug_profile().log_print_state_change("Octolapse is requesting a position.")

        # Warning, we can only request one position at a time!
        if self._position_signal.is_set():
            self._position_signal.clear()

            # build the staret commands
            commands_to_send = ["M400", "M114"]
            # send any code that is to be run before the position request
            if start_gcode is not None and len(start_gcode) > 0:
                commands_to_send = start_gcode + commands_to_send

            if self.State in [TimelapseState.TakingSnapshot, TimelapseState.AcquiringLocation]:
                self.send_snapshot_gcode_array(commands_to_send)
            else:
                self.Settings.current_debug_profile().log_warning(
                    "Warning:  The printer was not in the expected state to send octolapse gcode.  State:{0}"
                    .format(self.State)
                )
                return None
        event_is_set = self._position_signal.wait(timeout)

        if not event_is_set:
            # we ran into a timeout while waiting for a fresh position
            self.Settings.current_debug_profile().log_warning(
                "Warning:  A timeout occurred while requesting the current position."
            )

            return None

        return self._position_payload

    def _on_snapshot_success(self, *args, **kwargs):
        # Increment the number of snapshots received
        self.SnapshotCount += 1
        self._snapshot_success = True

    def _on_snapshot_fail(self, *args, **kwargs):
        reason = args[0]
        message = "Failed to download the snapshot.  Reason: {0}".format(
            reason)

        self.Settings.current_debug_profile().log_snapshot_download(message)
        self._snapshot_success = False
        self.SnapshotError = message

    def _on_snapshot_complete(self, *args, **kwargs):
        self.Settings.current_debug_profile().log_snapshot_download("Snapshot download complete.")
        self._snapshot_signal.set()

    def _take_snapshot_async(self):
        snapshot_async_payload = {
            "success": False,
            "error": "Waiting on thread to signal, aborting"
        }
        if self.Camera.camera_type == "external-script":
            job = self.CaptureSnapshot.create_snapshot_script_job(
                "snapshot", self.Camera.external_camera_snapshot_script,
                utility.get_currently_printing_filename(self.OctoprintPrinter), self.SnapshotCount,
                on_complete=None, on_success=self._on_snapshot_success, on_fail=self._on_snapshot_fail)
            # run the job
            job()
        elif self.Camera.camera_type == "webcam":
            if self._snapshot_signal.is_set():
                # only clear signal and send a new M114 if we haven't already done that from another thread
                self._snapshot_signal.clear()
                # start the snapshot
                self.Settings.current_debug_profile().log_snapshot_download("Taking a snapshot.")


                snapshot_job = self.CaptureSnapshot.create_snapshot_job(
                    utility.get_currently_printing_filename(self.OctoprintPrinter),
                    self.SnapshotCount,
                    on_success=self._on_snapshot_success,
                    on_fail=self._on_snapshot_fail,
                    on_complete=self._on_snapshot_complete
                )
                snapshot_thread = threading.Thread(target=snapshot_job)
                snapshot_thread.daemon = True
                snapshot_thread.start()

            snapshot_timeout = self._snapshot_timeout + (self.Camera.delay/1000.0)
            event_is_set = self._snapshot_signal.wait(snapshot_timeout)
            if not event_is_set:
                # we ran into a timeout while waiting for a fresh position
                snapshot_async_payload["success"] = False
                snapshot_async_payload["error"] = \
                    "Snapshot timed out in {0} seconds.".format(snapshot_timeout)

            else:
                snapshot_async_payload["success"] = True
                snapshot_async_payload["error"] = ""

        return snapshot_async_payload

    def _take_timelapse_snapshot(
        self, trigger, command_string, cmd, parameters, triggering_command_position, triggering_extruder_position
    ):
        timelapse_snapshot_payload = {
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

            show_real_snapshot_time = self.Settings.show_real_snapshot_time
            # create the GCode for the timelapse and store it
            snapshot_gcode = self.Gcode.create_snapshot_gcode(
                self.Position,
                trigger,
                command_string,
                cmd,
                parameters,
                triggering_command_position,
                triggering_extruder_position
            )
            # save the gcode fo the payload
            timelapse_snapshot_payload["snapshot_gcode"] = snapshot_gcode
            if snapshot_gcode is None:
                self.Settings.current_debug_profile().log_warning(
                    "No snapshot gcode was generated."
                )
                return timelapse_snapshot_payload

            assert (isinstance(snapshot_gcode, SnapshotGcode))

            if not show_real_snapshot_time:
                gcodes_to_send = snapshot_gcode.StartGcode + snapshot_gcode.SnapshotCommands
                if len(gcodes_to_send) > 0:
                    self.Settings.current_debug_profile().log_snapshot_gcode(
                        "Sending snapshot start gcode and snapshot commands.")
                    snapshot_position = self.get_position_async(
                        start_gcode=snapshot_gcode.StartGcode + snapshot_gcode.SnapshotCommands
                    )
                    if snapshot_position is None:
                        self.Settings.current_debug_profile().log_error(
                            "The snapshot position is None.  Either the print has cancelled or a timeout has been reached."
                        )
                        return None
            else:
                self.Settings.current_debug_profile().log_snapshot_gcode(
                    "Sending snapshot start gcode.")
                # send start commands and zhop/retract if they exist
                if len(snapshot_gcode.StartGcode) > 0:
                    start_position = self.get_position_async(start_gcode=snapshot_gcode.StartGcode)

                    if start_position is None:
                        self.Settings.current_debug_profile().log_error(
                            "The start_position is None.  Either the print has cancelled or a timeout has been reached."
                        )
                        return None
                # park the printhead in the snapshot position and wait for the movement to complete
                snapshot_start_time = time.time()
                if len(snapshot_gcode.SnapshotCommands) > 0:
                    self.Settings.current_debug_profile().log_snapshot_gcode("Sending snapshot commands.")
                    snapshot_position = self.get_position_async(
                        start_gcode=snapshot_gcode.SnapshotCommands, timeout=self._position_timeout_short
                    )

                    if snapshot_position is None:
                        self.Settings.current_debug_profile().log_error(
                            "The snapshot_position is None.  Either the print has cancelled or a timeout has been reached."
                        )
                        return None
            # record the snapshot position
            timelapse_snapshot_payload["snapshot_position"] = snapshot_position
            # by now we should be ready to take a snapshot
            snapshot_async_payload = self._take_snapshot_async()
            timelapse_snapshot_payload["snapshot_payload"] = snapshot_async_payload

            if not show_real_snapshot_time:
                # return the printhead to the start position
                gcode_to_send = snapshot_gcode.ReturnCommands + snapshot_gcode.EndGcode
                if len (gcode_to_send) > 0:
                    if self.State == TimelapseState.TakingSnapshot:
                        self.Settings.current_debug_profile().log_snapshot_gcode(
                            "Sending snapshot return and end gcode.")
                        self.send_snapshot_gcode_array(gcode_to_send)
            else:

                if len(snapshot_gcode.ReturnCommands) > 0:
                    self.Settings.current_debug_profile().log_snapshot_gcode("Sending return gcode.")
                    return_position = self.get_position_async(
                        start_gcode=snapshot_gcode.ReturnCommands, timeout=self._position_timeout_short
                    )

                    timelapse_snapshot_payload["return_position"] = return_position
                    if return_position is None:
                        self.Settings.current_debug_profile().log_error(
                            "The snapshot_position is None.  Either the print has cancelled or a timeout has been reached."
                        )
                        return None
                # calculate the total snapshot time
                snapshot_end_time = time.time()
                snapshot_time = snapshot_end_time - snapshot_start_time
                self.SecondsAddedByOctolapse += snapshot_time
                timelapse_snapshot_payload["current_snapshot_time"] = snapshot_time
                timelapse_snapshot_payload["total_snapshot_time"] = self.SecondsAddedByOctolapse

                if len(snapshot_gcode.EndGcode) > 0:
                    if self.State == TimelapseState.TakingSnapshot:
                        if self.State == TimelapseState.TakingSnapshot:
                            self.Settings.current_debug_profile().log_snapshot_gcode("Sending end gcode.")
                            self.send_snapshot_gcode_array(snapshot_gcode.EndGcode)

            # we've completed the procedure, set success
            timelapse_snapshot_payload["success"] = True

        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)
            timelapse_snapshot_payload["error"] = "An unexpected error was encountered while running the timelapse " \
                                                  "snapshot procedure. "

        return timelapse_snapshot_payload

    # public functions
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
            timelapse_stopped_callback_thread = threading.Thread(
                target=self.TimelapseStoppedCallback, args=[message, error]
            )
            timelapse_stopped_callback_thread.daemon = True
            timelapse_stopped_callback_thread.start()
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

    def on_print_cancelling(self):
        self.State = TimelapseState.Cancelling
        if not self._position_signal.is_set():
            self.Settings.current_debug_profile().log_error(
                "The print is cancelling, but a position request is in progress.")
            self._position_payload = None
            self._position_signal.set()
        if not self._snapshot_signal.is_set():
            self.Settings.current_debug_profile().log_error(
                "The print is cancelling, but a snapshot request is in progress.")
            self._most_recent_snapshot_payload = None
            self._snapshot_signal.set()

    def on_print_canceled(self):
        if self.State != TimelapseState.Idle:
            self.end_timelapse("CANCELED")

    def on_print_completed(self):
        if self.State != TimelapseState.Idle:
            self.end_timelapse("COMPLETED")

    def end_timelapse(self, print_status):
        self.PrintEndStatus = print_status
        try:
            if self.PrintStartTime is None:
                self._reset()
            elif self.PrintStartTime is not None and self.State in [
                TimelapseState.WaitingForTrigger, TimelapseState.WaitingToRender, TimelapseState.WaitingToEndTimelapse
                , TimelapseState.Cancelling
            ]:

                if not self._render_timelapse(self.PrintEndStatus):
                    if self.OnRenderErrorCallback is not None:
                        error = RenderError('timelapse_start', "The render_start function returned false")
                        render_end_callback_thread = threading.Thread(
                            target=self.OnRenderErrorCallback, args=[error]
                        )
                        render_end_callback_thread.daemon = True
                        render_end_callback_thread.start()
                self._reset()
            if self.State != TimelapseState.Idle:
                self.State = TimelapseState.WaitingToEndTimelapse

        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)

        if self.OnTimelapseEndCallback is not None:
            self.OnTimelapseEndCallback()

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
            or self.State in [TimelapseState.Idle, TimelapseState.Initializing, TimelapseState.WaitingToRender]
            or self.OctoprintPrinter.get_state_id() == "CANCELLING"
            or self.Triggers is None
            or self.Triggers.count() < 1
        ):
            return False
        return True

    def get_is_rendering(self):
        return self._rendering_task_queue.qsize() > 0

    def on_print_start(self, tags):
        self.OnPrintStartCallback(tags)

    def on_print_start_failed(self, message):
        self.OnPrintStartFailedCallback(message)

    def on_gcode_queuing(self, command_string, cmd_type, gcode, tags):

        self.detect_timelapse_start(command_string, tags)

        # if the timelapse is not active, exit without changing any gcode
        if not self.is_timelapse_active():
            return

        self.check_current_line_number(tags)

        # update the position tracker so that we know where all of the axis are.
        # We will need this later when generating snapshot gcode so that we can return to the previous
        # position
        is_snapshot_gcode_command = self._is_snapshot_command(command_string)

        try:
            self.Settings.current_debug_profile().log_gcode_queuing(
                "Queuing Command: Command Type:{0}, gcode:{1}, cmd: {2}, tags: {3}".format(
                    cmd_type, gcode, command_string, tags
                )
            )

            try:
                cmd, parameters = Commands.parse(command_string)
            except ValueError as e:
                message = "An error was thrown by the gcode parser, stopping timelapse.  Details: {0}".format(str(e))
                self.Settings.current_debug_profile().log_warning(
                    message
                )
                self.stop_snapshots(message, True)
                return None

            # get the position state in case it has changed
            # if there has been a position or extruder state change, inform any listener

            if cmd is not None and not is_snapshot_gcode_command:
                # create our state change dictionaries
                self.Position.update(command_string, cmd, parameters)

            # if this code is snapshot gcode, simply return it to the printer.
            if {'plugin:octolapse', 'snapshot_gcode'}.issubset(tags):
                return None

            if not self.check_for_non_metric_errors():
                if self.Position.has_position_error(0):
                    # There are position errors, report them!
                    self._on_position_error()
                elif (self.State == TimelapseState.WaitingForTrigger
                        and (self.Position.requires_location_detection(1)) and self.OctoprintPrinter.is_printing()):
                    # there is no longer a need to detect Octoprint start/end script, so
                    # we can put the job on hold without fear!
                    self.State = TimelapseState.AcquiringLocation

                    if self.OctoprintPrinter.set_job_on_hold(True):
                        thread = threading.Thread(target=self.acquire_position, args=[command_string, cmd, parameters])
                        thread.daemon = True
                        thread.start()
                        return None,
                elif (self.State == TimelapseState.WaitingForTrigger
                      and self.OctoprintPrinter.is_printing()
                      and not self.Position.has_position_error(0)):
                    # update the triggers with the current position
                    self.Triggers.update(self.Position, command_string)

                    # see if at least one trigger is triggering
                    _first_triggering = self.get_first_triggering()

                    if _first_triggering:
                        # get the job lock
                        if self.OctoprintPrinter.set_job_on_hold(True):
                            # We are triggering, take a snapshot
                            self.State = TimelapseState.TakingSnapshot
                            # pause any timer triggers that are enabled
                            self.Triggers.pause()

                            # take the snapshot on a new thread
                            thread = threading.Thread(
                                target=self.acquire_snapshot, args=[command_string, cmd, parameters, _first_triggering]
                            )
                            thread.daemon = True
                            thread.start()
                            # suppress the current command, we'll send it later
                            return None,

                elif self.State == TimelapseState.TakingSnapshot:
                    # Don't do anything further to any commands unless we are
                    # taking a timelapse , or if octolapse paused the print.
                    # suppress any commands we don't, under any cirumstances,
                    # to execute while we're taking a snapshot

                    if cmd in self.Commands.SuppressedSnapshotGcodeCommands:
                        command_string = None,  # suppress the command

            if is_snapshot_gcode_command:
                # in all cases do not return the snapshot command to the printer.
                # It is NOT a real gcode and could cause errors.
                command_string = None,

        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)
            raise

        # notify any callbacks
        self._send_state_changed_message()

        # do any post processing for test mode
        if command_string != (None,):
            command_string = self._get_command_for_octoprint(command_string, cmd,parameters)
        return command_string

    def detect_timelapse_start(self, cmd, tags):
        # detect print start, including any start gcode script
        if (
            self.Settings.is_octolapse_enabled and
            self.State == TimelapseState.Idle and
            ({'trigger:comm.start_print', 'trigger:comm.reset_line_numbers'} <= tags or {'script:beforePrintStarted', 'trigger:comm.send_gcode_script'} <= tags) and
            self.OctoprintPrinter.is_printing()
        ):
            if self.OctoprintPrinter.set_job_on_hold(True):
                try:
                    self.State = TimelapseState.Initializing

                    self.Settings.current_debug_profile().log_print_state_change(
                        "Print Start Detected.  Command: {0}, Tags:{1}".format(cmd, tags)
                    )
                    # call the synchronous callback on_print_start
                    self.on_print_start(tags)

                    if self.State == TimelapseState.WaitingForTrigger:
                        # set the current line to 0 so that the plugin checks for line 1 below after startup.
                        self.CurrentFileLine = 0
                finally:
                    self.OctoprintPrinter.set_job_on_hold(False)
            else:
                self.on_print_start_failed(
                    "Unable to start timelapse, failed to acquire a job lock.  Print start failed."
                )

    def check_current_line_number(self, tags):
        # check the current line number
        if {'source:file'} in tags:
            # this line is from the file, advance!
            self.CurrentFileLine += 1
            if "fileline:{0}".format(self.CurrentFileLine) not in tags:
                actual_file_line = "unknown"
                for tag in tags:
                    if len(tag) > 9 and tag.startswith("fileline:"):
                        actual_file_line = tag[9:]
                message = "File line number {0} was expected, but {1} was received!".format(
                    self.CurrentFileLine + 1,
                    actual_file_line
                )
                self.Settings.current_debug_profile().log_error(message)
                self.stop_snapshots(message, True)

    def check_for_non_metric_errors(self):
        # make sure we're not using inches
        is_metric = self.Position.is_metric()
        has_error = False
        error_message = ""
        if is_metric is None and self.Position.has_position_error():
            has_error = True
            error_message = "The printer profile requires an explicit G21 command before any position " \
                            "altering/setting commands, including any home commands.  Stopping timelapse, " \
                            "but continuing the print. "

        elif not is_metric and self.Position.has_position_error():
            has_error = True
            if self.Printer.units_default == "inches":
                error_message = "The printer profile uses 'inches' as the default unit of measurement.  In order to" \
                    " use Octolapse, a G21 command must come before any position altering/setting commands, including" \
                    " any home commands.  Stopping timelapse, but continuing the print. "
            else:
                error_message = "The gcode file contains a G20 command (set units to inches), which Octolapse " \
                    "does not support.  Stopping timelapse, but continuing the print."

        if has_error:
            self.stop_snapshots(error_message,has_error)

        return has_error

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
                return first_trigger
        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)
            # no need to re-raise here, the trigger just won't happen
        return False

    def acquire_position(self, command_string, cmd, parameters):
        try:
            self.Settings.current_debug_profile().log_print_state_change(
                "A position altering command has been detected.  Fetching and updating position.  "
                "Position Command: {0}".format(cmd))
            # Undo the last position update, we will be resending the command
            self.Position.undo_update()
            current_position = self.get_position_async()

            if current_position is None:
                self.PrintEndStatus = "POSITION_TIMEOUT"
                self.State = TimelapseState.WaitingToEndTimelapse
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
            if self.IsTestMode:
                gcode = self.Commands.alter_for_test_mode(command_string, cmd, parameters, return_string=True)
            else:
                gcode = command_string

            if gcode != "":
                if self.State == TimelapseState.AcquiringLocation:
                    self.Settings.current_debug_profile().log_print_state_change(
                        "Sending triggering command for position acquisition - {0}.".format(gcode))
                    # send the triggering command
                    self.send_snapshot_gcode_array([gcode])
                else:
                    self.Settings.current_debug_profile().log_print_state_change(
                        "Unable to send triggering command for position acquisition - incorrect state:{0}."
                        .format(self.State)
                    )
            # set the state
            if self.State == TimelapseState.AcquiringLocation:
                self.State = TimelapseState.WaitingForTrigger

            self.Settings.current_debug_profile().log_print_state_change("Position Acquired")

        finally:
            self.OctoprintPrinter.set_job_on_hold(False)

    def acquire_snapshot(self, command_string, cmd, parameters, trigger):
        try:
            self.Settings.current_debug_profile().log_snapshot_download(
                "About to take a snapshot.  Triggering Command: {0}".format(cmd))
            if self.OnSnapshotStartCallback is not None:
                snapshot_callback_thread = threading.Thread(target=self.OnSnapshotStartCallback)
                snapshot_callback_thread.daemon = True
                snapshot_callback_thread.start()

            # Capture and undo the last position update, we're not going to be using it!
            triggering_command_position, triggering_extruder_position = self.Position.undo_update()

            # take the snapshot
            # Todo:  We probably don't need the payload here.
            self._most_recent_snapshot_payload = self._take_timelapse_snapshot(
                trigger, command_string, cmd, parameters, triggering_command_position, triggering_extruder_position
            )

            if self._most_recent_snapshot_payload is None:
                self.Settings.current_debug_profile().log_error("acquire_snapshot received a null payload.")
            else:
                self.Settings.current_debug_profile().log_snapshot_download("The snapshot has completed")

        finally:

            # set the state
            if self.State == TimelapseState.TakingSnapshot:
                self.State = TimelapseState.WaitingForTrigger

            self.Triggers.resume()

            self.OctoprintPrinter.set_job_on_hold(False)

            # notify that we're finished, but only if we haven't just stopped the timelapse.
            if self._most_recent_snapshot_payload is not None:
                self.Settings.current_debug_profile().log_info("Sending on_snapshot_complete payload.")
                # send a copy of the dict in case it gets changed by threads.
                self._on_trigger_snapshot_complete(self._most_recent_snapshot_payload.copy())

    def on_gcode_sending(self, cmd, cmd_type, gcode, tags):

        if cmd == "M114" and 'plugin:octolapse' in tags:
            self.Settings.current_debug_profile().log_print_state_change("The position request is being sent")
            self._position_request_sent = True

    def on_gcode_sent(self, cmd, cmd_type, gcode, tags):
        self.Settings.current_debug_profile().log_gcode_sent(
            "Sent to printer: Command Type:{0}, gcode:{1}, cmd: {2}, tags: {3}".format(cmd_type, gcode, cmd, tags))

    def on_gcode_received(self, comm, line, *args, **kwargs):
        self.Settings.current_debug_profile().log_gcode_received(
            "Received from printer: line:{0}".format(line)
        )
        return line

    # internal functions
    ####################
    def _get_command_for_octoprint(self, command_string, cmd, parameters):
        if command_string is None or command_string == (None,):
            return command_string

        if self.IsTestMode and self.State >= TimelapseState.WaitingForTrigger:
            return self.Commands.alter_for_test_mode(command_string, cmd, parameters)
        # if we were given a list, return it.
        if isinstance(command_string, list):
            return command_string
        # if we were given a command return None (don't change the command at all)
        return None

    def _send_state_changed_message(self):
        """Notifies any callbacks about any changes contained in the dictionaries.
        If you send a dict here the client will get a message, so check the
        settings to see if they are subscribed to notifications before populating the dictinaries!"""

        delay_seconds = 0
        # if another thread is trying to send the message, stop it
        if self.StateChangeMessageThread is not None and self.StateChangeMessageThread.isAlive():
            self.StateChangeMessageThread.cancel()

        if self.LastStateChangeMessageTime is not None:
            # do not send more than 1 per second
            time_since_last_update = time.time() - self.LastStateChangeMessageTime
            if time_since_last_update < 1:
                delay_seconds = 1-time_since_last_update
                if delay_seconds < 0:
                    delay_seconds = 0

        try:
            # Notify any callbacks
            if self.OnStateChangedCallback is not None:

                    def send_change_message():
                        trigger_change_list = None
                        position_change_dict = None
                        position_state_change_dict = None
                        extruder_change_dict = None
                        trigger_changes_dict = None

                        # Get the changes
                        if self.Settings.show_trigger_state_changes:
                            trigger_change_list = self.Triggers.state_to_list()
                        if self.Settings.show_position_changes:
                            position_change_dict = self.Position.to_position_dict()
                        if self.Settings.show_position_state_changes or self.Position.has_position_state_errors():
                            position_state_change_dict = self.Position.to_state_dict()
                        if self.Settings.show_extruder_state_changes:
                            extruder_change_dict = self.Position.Extruder.to_dict()

                        # if there are any state changes, send them
                        if (
                            position_change_dict is not None
                            or position_state_change_dict is not None
                            or extruder_change_dict is not None
                            or trigger_change_list is not None
                        ):
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

                        if (
                            change_dict["Extruder"] is not None
                            or change_dict["Position"] is not None
                            or change_dict["PositionState"] is not None
                            or change_dict["TriggerState"] is not None
                        ):
                            self.OnStateChangedCallback(change_dict)
                            self.LastStateChangeMessageTime = time.time()

                    # Send a delayed message
                    self.StateChangeMessageThread = threading.Timer(
                        delay_seconds,
                        send_change_message
                    )
                    self.StateChangeMessageThread.daemon = True
                    self.StateChangeMessageThread.start()

        except Exception as e:
            # no need to re-raise, callbacks won't be notified, however.
            self.Settings.current_debug_profile().log_exception(e)

    def _send_plugin_message(self, message_type, message):
        self.OnPluginMessageSentCallback(message_type, message)

    def _send_plugin_message_async(self, message_type, message):
        warning_thread = threading.Thread(target=self._send_plugin_message, args=[message_type, message])
        warning_thread.daemon = True
        warning_thread.start()

    def _is_snapshot_command(self, command_string):
        return command_string == self.Printer.snapshot_command

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
            position_error_callback_thread = threading.Thread(
                target=self.OnPositionErrorCallback, args=[message]
            )
            position_error_callback_thread.daemon = True
            position_error_callback_thread.start()

    def _on_trigger_snapshot_complete(self, snapshot_payload):
        if self.OnSnapshotCompleteCallback is not None:
            payload = {
                "success": snapshot_payload["success"],
                "error": snapshot_payload["error"],
                "snapshot_count": self.SnapshotCount,
                "total_snapshot_time": snapshot_payload["total_snapshot_time"],
                "current_snapshot_time": snapshot_payload["total_snapshot_time"]
            }
            if self.OnSnapshotCompleteCallback is not None:
                snapshot_complete_callback_thread = threading.Thread(
                    target=self.OnSnapshotCompleteCallback, args=[payload]
                )
                snapshot_complete_callback_thread.daemon = True
                snapshot_complete_callback_thread.start()

    def _render_timelapse(self, print_end_state):
        # make sure we have a non null TimelapseSettings object.  We may have terminated the timelapse for some reason
        if self.Rendering is not None and self.Rendering.enabled:
            job_id = "TimelapseRenderJob_{0}".format(str(uuid.uuid4()))
            job = Render.create_render_job(
                self.Settings,
                self.Snapshot,
                self.Rendering,
                self.DataFolder,
                os.path.dirname(
                    os.path.join(utility.get_temp_snapshot_driectory_template().format(DATADIRECTORY=self.DataFolder),
                                 utility.get_snapshot_filename(
                                     utility.get_currently_printing_filename(self.OctoprintPrinter),
                                     self.PrintStartTime, 0))),
                self.DefaultTimelapseDirectory,
                self.FfMpegPath,
                1,
                job_id,
                utility.get_currently_printing_filename(self.OctoprintPrinter),
                self.PrintStartTime,
                time.time(),
                print_end_state,
                self.SecondsAddedByOctolapse,
                self._on_render_start,
                self._on_render_success,
                self._on_render_error
            )
            rendering_thread = threading.Thread(target=job, args=[])
            rendering_thread.daemon = True
            job_id = "TimelapseRenderJob_{0}".format(str(uuid.uuid4()))
            self._rendering_task_queue.put(job_id)
            rendering_thread.start()
            return True
        return False

    def _on_render_start(self, job_id, payload):
        self.Settings.current_debug_profile().log_render_start(
            "Started rendering/synchronizing the timelapse. JobId: {0}".format(job_id))
        # notify the caller
        if self.OnRenderStartCallback is not None:
            render_start_complete_callback_thread = threading.Thread(
                target=self.OnRenderStartCallback, args=(payload,)
            )
            render_start_complete_callback_thread.daemon = True
            render_start_complete_callback_thread.start()

    def _on_render_success(self, job_id, payload):
        self.Settings.current_debug_profile().log_render_complete("Completed rendering. JobId: {0}".format(job_id))
        assert (isinstance(payload, RenderingCallbackArgs))

        if self.Snapshot.cleanup_after_render_complete:
            self.CaptureSnapshot.clean_snapshots(utility.get_snapshot_temp_directory(self.DataFolder))

        if self.OnRenderSuccessCallback is not None:
            render_success_complete_callback_thread = threading.Thread(
                target=self.OnRenderSuccessCallback, args=(payload,)
            )
            render_success_complete_callback_thread.daemon = True
            render_success_complete_callback_thread.start()

        self._rendering_task_queue.get()
        self._rendering_task_queue.task_done()

    def _on_render_error(self, job_id, error):
        self.Settings.current_debug_profile().log_render_complete("Completed rendering. JobId: {0}".format(job_id))

        if self.Snapshot.cleanup_after_render_fail:
            self.CaptureSnapshot.clean_snapshots(utility.get_snapshot_temp_directory(self.DataFolder))

        if self.OnRenderErrorCallback is not None:
            render_error_complete_callback_thread = threading.Thread(
                target=self.OnRenderErrorCallback, args=(error,)
            )
            render_error_complete_callback_thread.daemon = True
            render_error_complete_callback_thread.start()

        self._rendering_task_queue.get()
        self._rendering_task_queue.task_done()

    def _on_timelapse_start(self):
        if self.OnTimelapseStartCallback is None:
            return
        self.OnTimelapseStartCallback()

    def _reset(self):
        self.State = TimelapseState.Idle
        self.CurrentFileLine = 0
        if self.Triggers is not None:
            self.Triggers.reset()
        self.CommandIndex = -1

        self.LastStateChangeMessageTime = None
        self.PrintStartTime = None
        self.SnapshotGcodes = None
        self.SavedCommand = None
        self.PositionRequestAttempts = 0
        self.IsTestMode = False
        self._position_request_sent = False

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
        self._position_signal.set()
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
    Initializing = 2
    WaitingForTrigger = 3
    AcquiringLocation = 4
    TakingSnapshot = 5
    WaitingToRender = 6
    WaitingToEndTimelapse = 7
    Cancelling = 8

