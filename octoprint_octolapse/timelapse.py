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

import threading
import time
import uuid
try:
    # noinspection PyPep8Naming
    import queue as Queue
except ImportError:
    import Queue as Queue

import octoprint_octolapse.utility as utility
from octoprint_octolapse.gcode import SnapshotGcodeGenerator, SnapshotGcode
from octoprint_octolapse.gcode_parser import Commands, ParsedCommand, Response
from octoprint_octolapse.position import Position
from octoprint_octolapse.render import RenderError, RenderingProcessor, RenderingCallbackArgs
from octoprint_octolapse.settings import PrinterProfile, OctolapseSettings
from octoprint_octolapse.snapshot import CaptureSnapshot, SnapshotJobInfo
from octoprint_octolapse.trigger import Triggers
import octoprint_octolapse.stabilization_preprocessing as preprocessing
import fastgcodeparser


class Timelapse(object):

    def __init__(
            self, settings, octoprint_printer, data_folder, timelapse_folder,
            on_print_started=None, on_print_start_failed=None,
            on_snapshot_start=None, on_snapshot_end=None, on_new_thumbnail_available=None,
            on_render_start=None, on_render_success=None, on_render_error=None,
            on_timelapse_stopping=None, on_timelapse_stopped=None,
            on_state_changed=None, on_timelapse_end=None,
            on_snapshot_position_error=None, on_position_error=None, on_plugin_message_sent=None):
        # config variables - These don't change even after a reset
        self._data_folder = data_folder
        self._settings = settings  # type: OctolapseSettings
        self._octoprint_printer = octoprint_printer
        self._default_timelapse_directory = timelapse_folder
        self._print_start_callback = on_print_started
        self._print_start_failed_callback = on_print_start_failed
        self._render_start_callback = on_render_start
        self._render_success_callback = on_render_success
        self._render_error_callback = on_render_error
        self._snapshot_start_callback = on_snapshot_start
        self._snapshot_complete_callback = on_snapshot_end
        self._new_thumbnail_available_callback = on_new_thumbnail_available
        self._timelapse_stopping_callback = on_timelapse_stopping
        self._timelapse_stopped_callback = on_timelapse_stopped
        self._state_changed_callback = on_state_changed
        self._timelapse_end_callback = on_timelapse_end
        self._snapshot_position_error_callback = on_snapshot_position_error
        self._position_error_callback = on_position_error
        self._plugin_message_sent_callback = on_plugin_message_sent
        self._commands = Commands()  # used to parse and generate gcode
        self._triggers = None
        self._print_end_status = "Unknown"
        self._last_state_changed_message_time = None
        self._state_change_message_thread = None
        self._last_position_error_message_time = None
        self._position_error_message_thread = None
        self.has_position_errors_to_report = False
        self.position_errors_to_report = None
        # Settings that may be different after StartTimelapse is called

        self._octoprint_printer_profile = None
        self._current_job_info = None
        self._ffmpeg_path = None
        self._snapshot = None
        self._stabilization = None
        self._gcode = None
        self._printer = None
        self._capture_snapshot = None
        self._rendering_processor = None
        self._position = None
        self._state = TimelapseState.Idle
        self._is_test_mode = False
        self._snapshot_command = None
        # State Tracking that should only be reset when starting a timelapse
        self._has_been_stopped = False
        self._timelapse_stop_requested = False
        self.SecondsAddedByOctolapse = 0
        # State tracking variables
        self.RequiresLocationDetectionAfterHome = False
        self._position_request_sent = False
        # fetch position private variables
        self._position_payload = None
        self._position_timeout_long = 600.0
        self._position_timeout_short = 60.0
        self._position_signal = threading.Event()
        self._position_signal.set()

        # get snapshot async private variables
        self._snapshot_success = False
        # It shouldn't take more than 5 seconds to take a snapshot!
        self._snapshot_timeout = 5.0
        self._snapshot_signal = threading.Event()
        self._snapshot_signal.set()
        self._most_recent_snapshot_payload = None

        self._current_profiles = {}
        self._current_file_line = 0

        self.snapshot_plans = None  # type: [preprocessing.SnapshotPlan]
        self.current_snapshot_plan_index = 0
        self.current_snapshot_plan = None  # type: preprocessing.SnapshotPlan
        self.is_realtime = True
        # snapshot thread queue
        self._snapshot_task_queue = Queue.Queue(maxsize=1)
        self._rendering_task_queue = Queue.Queue(maxsize=0)

        self._reset()

    def get_snapshot_count(self):
        if self._capture_snapshot is None:
            return 0
        return self._capture_snapshot.SnapshotsTotal

    def get_printer_volume_dict(self):
        return utility.get_bounding_box(
            self._printer, self._octoprint_printer_profile)

    def get_current_profiles(self):
        return self._current_profiles

    def get_current_state(self):
        return self._state

    def start_timelapse(
        self, settings, octoprint_printer_profile, ffmpeg_path, g90_influences_extruder,
        gcode_file_path, snapshot_plans=None
    ):
        # we must supply the settings first!  Else reset won't work properly.
        self._reset()
        # in case the settings have been destroyed and recreated
        self._settings = settings
        # ToDo:  all cloning should be removed after this point.  We already have a settings object copy.
        #  Also, we no longer need the original settings since we can use the global OctolapseSettings.Logger now
        self._printer = self._settings.profiles.current_printer()
        self._snapshot_command = self._printer.snapshot_command
        self._stabilization = self._settings.profiles.current_stabilization()
        self.snapshot_plans = snapshot_plans
        self.current_snapshot_plan = None
        self.current_snapshot_plan_index = 0
        # set the current snapshot plan if we have any
        if self.snapshot_plans is not None and len(self.snapshot_plans) > 0:
            self.current_snapshot_plan = self.snapshot_plans[self.current_snapshot_plan_index]
        # if we have at least one snapshot plan, we must have preprocessed, so set is_realtime to false.
        self.is_realtime = self.current_snapshot_plan is None
        assert (isinstance(self._printer, PrinterProfile))

        # time tracking - how much time did we add to the print?
        self.SecondsAddedByOctolapse = 0
        self.RequiresLocationDetectionAfterHome = False
        self._octoprint_printer_profile = octoprint_printer_profile
        self._ffmpeg_path = ffmpeg_path
        self._current_job_info = utility.TimelapseJobInfo(
            job_guid=uuid.uuid4(),
            print_start_time=time.time(),
            print_file_name=utility.get_filename_from_full_path(gcode_file_path)
        )
        # Note that the RenderingProcessor makes copies of all objects sent to it
        self._snapshot = self._settings.profiles.current_snapshot()

        self._rendering_processor = RenderingProcessor(
            self._rendering_task_queue,
            self._settings.Logger,
            self._current_job_info,
            self._settings.profiles.current_rendering(),
            self._settings.profiles.active_cameras(),
            self._data_folder,
            self._default_timelapse_directory,
            self._ffmpeg_path,
            self._on_render_start,
            self._on_render_success,
            self._on_render_error,
            self._snapshot.cleanup_after_render_complete,
            self._snapshot.cleanup_after_render_fail,
        )

        self._gcode = SnapshotGcodeGenerator(
            self._settings, octoprint_printer_profile)

        self._capture_snapshot = CaptureSnapshot(
            self._settings,
            self._data_folder,
            self._settings.profiles.active_cameras(),
            self._current_job_info,
            self.send_gcode_for_camera,
            self._new_thumbnail_available_callback
        )
        self._position = Position(
            self._settings.Logger, self._settings.profiles.current_printer(),
            self._settings.profiles.current_snapshot(), octoprint_printer_profile, g90_influences_extruder
        )
        self._state = TimelapseState.WaitingForTrigger
        self._is_test_mode = self._settings.profiles.current_debug_profile().is_test_mode
        self._triggers = Triggers(self._settings)
        self._triggers.create()

        # take a snapshot of the current settings for use in the Octolapse Tab
        self._current_profiles = self._settings.profiles.get_profiles_dict()

    def on_position_received(self, payload):
        # added new position request sent flag so that we can prevent position requests NOT from Octolapse from
        # triggering a snapshot.
        if self._position_request_sent:
            self._position_request_sent = False
            self._settings.Logger.log_print_state_change(
                "Octolapse has received a position request response.")
            if self._state in [
                TimelapseState.AcquiringLocation, TimelapseState.TakingSnapshot, TimelapseState.WaitingToEndTimelapse,
                TimelapseState.WaitingToRender
            ]:
                # set flag to false so that it can be triggered again after the next M114 sent by Octolapse
                self._position_payload = payload
            else:
                self._position_payload = None
                self._settings.Logger.log_print_state_change(
                    "Octolapse was not in the correct state to receive a position update.  StateId:{0}"
                    .format(self._state)
                )
            self._position_signal.set()
        else:
            self._settings.Logger.log_print_state_change(
                "Octolapse has received an position response but did not request one.  Ignoring.")

    def send_snapshot_gcode_array(self, gcode_array):
        self._octoprint_printer.commands(gcode_array, tags={"snapshot_gcode"})

    def send_gcode_for_camera(self, gcode_array, timeout):
        self.get_position_async(
            start_gcode=gcode_array, timeout=timeout
        )

    # requests a position from the printer (m400-m114), and can send optional gcode before the position request.
    # this ensures any gcode sent in the start_gcode parameter will be executed before the function returns.
    def get_position_async(self, start_gcode=None, timeout=None):
        if timeout is None:
            timeout = self._position_timeout_long

        self._settings.Logger.log_print_state_change("Octolapse is requesting a position.")

        # Warning, we can only request one position at a time!
        if self._position_signal.is_set():
            self._position_signal.clear()

            # build the staret commands
            commands_to_send = ["M400", "M114"]
            # send any code that is to be run before the position request
            if start_gcode is not None and len(start_gcode) > 0:
                commands_to_send = start_gcode + commands_to_send

            if self._state in [
                TimelapseState.TakingSnapshot, TimelapseState.AcquiringLocation, TimelapseState.WaitingToEndTimelapse,
                TimelapseState.WaitingToRender
            ]:
                self.send_snapshot_gcode_array(commands_to_send)
            else:
                self._settings.Logger.log_warning(
                    "Warning:  The printer was not in the expected state to send octolapse gcode.  State:{0}"
                    .format(self._state)
                )
                return None
        event_is_set = self._position_signal.wait(timeout)

        if not event_is_set:
            # we ran into a timeout while waiting for a fresh position
            self._settings.Logger.log_warning(
                "Warning:  A timeout occurred while requesting the current position."
            )

            return None

        return self._position_payload

    def _take_snapshots(self):
        snapshot_payload = {
            "success": False,
            "error": "Waiting on thread to signal, aborting"
        }

        # start the snapshot
        self._settings.Logger.log_snapshot_download("Taking a snapshot.")
        self._snapshot_task_queue.join()
        self._snapshot_task_queue.put("snapshot_job")
        try:
            results = self._capture_snapshot.take_snapshots()
        finally:
            self._snapshot_task_queue.get()
            self._snapshot_task_queue.task_done()
        # todo - notify client here
        # todo - maintain snapshot number separately for each camera!

        succeeded = len(results) > 0
        errors = []
        for result in results:
            assert(isinstance(result, SnapshotJobInfo))
            if not result.success:
                succeeded = False
                errors.append(result.error)
        snapshot_payload["success"] = succeeded
        # todo:  format this so the errors look better

        error_message = ""
        if len(errors) == 1:
            error_message = errors[0]
        if len(errors) > 1:
            error_message = "There were {0} snapshot errors:".format(len(errors))
            for num, error in enumerate(errors):
                error_message += "\n\nError {0} - {1}".format(num+1, error)

        snapshot_payload["error"] = error_message

        return snapshot_payload

    def _take_timelapse_snapshot_realtime(
        self, parsed_command, trigger
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

            has_error = False
            show_real_snapshot_time = self._settings.main_settings.show_real_snapshot_time
            snapshot_start_time = time.time()
            # create the GCode for the timelapse and store it
            snapshot_gcode = self._gcode.create_snapshot_gcode(
                self._position,
                trigger,
                parsed_command
            )
            # save the gcode fo the payload
            timelapse_snapshot_payload["snapshot_gcode"] = snapshot_gcode

            if self._gcode.has_snapshot_position_errors:
                timelapse_snapshot_payload["error"] = self._gcode.snapshot_position_errors

            if snapshot_gcode is None:
                self._settings.Logger.log_warning(
                    "No snapshot gcode was generated."
                )
                return timelapse_snapshot_payload

            assert (isinstance(snapshot_gcode, SnapshotGcode))

            # If we have any initialization gcodes, send them before waiting for moves to finish (in case we are
            # tracking itme)
            if len(snapshot_gcode.InitializationGcode) > 0:
                self._settings.Logger.log_snapshot_gcode(
                    "Sending initialization gcode.")
                self.send_snapshot_gcode_array(snapshot_gcode.InitializationGcode)

            if show_real_snapshot_time:
                # wait for commands to finish before recording start time - this will give us a very accurate
                # snapshot time, but requires an m400 + m114
                self._settings.Logger.log_snapshot_gcode(
                    "Waiting for commands to finish to calculate snapshot time accurately.")
                start_position = self.get_position_async()
                snapshot_start_time = time.time()
                if start_position is None:
                    has_error = True
                    self._settings.Logger.log_error(
                        "Unable to acquire the starting position.  Either the print has cancelled or a timeout has "
                        "been reached. "
                    )
                    # don't send any more gcode if we're cancelling
                    if self._octoprint_printer.get_state_id() == "CANCELLING":
                        return None
            # Combine the start gcode with the snapshot commands
            gcodes_to_send = snapshot_gcode.StartGcode + snapshot_gcode.snapshot_commands

            snapshot_position = None
            # If we have any Start/Snapshot commands to send, do it!
            if len(gcodes_to_send) > 0:
                self._settings.Logger.log_snapshot_gcode(
                    "Sending snapshot start gcode and snapshot commands.")
                snapshot_position = self.get_position_async(
                    start_gcode=gcodes_to_send
                )
                if snapshot_position is None:
                    has_error = True
                    self._settings.Logger.log_error(
                        "The snapshot position is None.  Either the print has cancelled or a timeout has been reached."
                    )

                    # don't send any more gcode if we're cancelling
                    if self._octoprint_printer.get_state_id() == "CANCELLING":
                        return None

            # record the snapshot position
            timelapse_snapshot_payload["snapshot_position"] = snapshot_position
            # by now we should be ready to take a snapshot
            if not has_error:
                snapshot_payload = self._take_snapshots()
                timelapse_snapshot_payload["snapshot_payload"] = snapshot_payload

            if not show_real_snapshot_time:
                # return the print head to the start position
                gcode_to_send = snapshot_gcode.ReturnCommands + snapshot_gcode.EndGcode
                if len(gcode_to_send) > 0:
                    if self._state == TimelapseState.TakingSnapshot:
                        self._settings.Logger.log_snapshot_gcode(
                            "Sending snapshot return and end gcode.")
                        self.send_snapshot_gcode_array(gcode_to_send)
            else:
                if len(snapshot_gcode.ReturnCommands) > 0:
                    self._settings.Logger.log_snapshot_gcode("Sending return gcode.")
                    return_position = self.get_position_async(
                        start_gcode=snapshot_gcode.ReturnCommands, timeout=self._position_timeout_short
                    )
                    timelapse_snapshot_payload["return_position"] = return_position
                    if return_position is None:
                        self._settings.Logger.log_error(
                            "The snapshot_position is None.  Either the print has cancelled or a timeout has been "
                            "reached. "
                        )
                        # don't send any more gcode if we're cancelling
                        if self._octoprint_printer.get_state_id() == "CANCELLING":
                            return None
                # calculate the total snapshot time
                snapshot_end_time = time.time()
                snapshot_time = snapshot_end_time - snapshot_start_time
                self._settings.Logger.log_snapshot_gcode(
                    "Stabilization and snapshot process complected in {0} seconds".format(snapshot_time)
                )
                self.SecondsAddedByOctolapse += snapshot_time
                timelapse_snapshot_payload["current_snapshot_time"] = snapshot_time
                timelapse_snapshot_payload["total_snapshot_time"] = self.SecondsAddedByOctolapse

                if len(snapshot_gcode.EndGcode) > 0:
                    if self._state == TimelapseState.TakingSnapshot:
                        self._settings.Logger.log_snapshot_gcode("Sending end gcode.")
                        self.send_snapshot_gcode_array(snapshot_gcode.EndGcode)

            # we've completed the procedure, set success
            timelapse_snapshot_payload["success"] = not has_error and not self._gcode.has_snapshot_position_errors

        except Exception as e:
            self._settings.Logger.log_exception(e)
            timelapse_snapshot_payload["error"] = "An unexpected error was encountered while running the timelapse " \
                                                  "snapshot procedure. "

        return timelapse_snapshot_payload

    def _take_timelapse_snapshot_precalculated(
        self, parsed_command
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
            snapshot_start_time = time.time()
            has_error = False
            show_real_snapshot_time = self._settings.main_settings.show_real_snapshot_time
            # create the GCode for the timelapse and store it
            snapshot_gcode = self._gcode.create_gcode_for_snapshot_plan(
                self.current_snapshot_plan, parsed_command, self._position.g90_influences_extruder
            )
            # save the gcode fo the payload
            timelapse_snapshot_payload["snapshot_gcode"] = snapshot_gcode

            if self._gcode.has_snapshot_position_errors:
                timelapse_snapshot_payload["error"] = self._gcode.Snapshotposition_errors

            if snapshot_gcode is None:
                self._settings.Logger.log_warning(
                    "No snapshot gcode was generated."
                )
                return timelapse_snapshot_payload

            assert (isinstance(snapshot_gcode, SnapshotGcode))

            gcodes_sent_without_waiting = False
            # If we have any initialization gcodes, send them before waiting for moves to finish
            # (in case we are tracking item)
            if len(snapshot_gcode.InitializationGcode) > 0:
                gcodes_sent_without_waiting = True
                self._settings.Logger.log_snapshot_gcode(
                    "Sending initialization gcode.")
                self.send_snapshot_gcode_array(snapshot_gcode.InitializationGcode)

            if show_real_snapshot_time and gcodes_sent_without_waiting:
                # wait for commands to finish before recording start time - this will give us a very accurate
                # snapshot time, but requires an m400 + m114
                self._settings.Logger.log_snapshot_gcode(
                    "Waiting for commands to finish to calculate snapshot time accurately.")
                start_position = self.get_position_async()
                gcodes_sent_without_waiting = False
                snapshot_start_time = time.time()
                if start_position is None:
                    has_error = True
                    self._settings.Logger.log_error(
                        "Unable to acquire the starting position.  Either the print has cancelled or a timeout has "
                        "been reached. "
                    )
                    # don't send any more gcode if we're cancelling
                    if self._octoprint_printer.get_state_id() == "CANCELLING":
                        return None

            # start building up a list of gcodes to send, starting with (appropriately) the start gcode
            gcodes_to_send = snapshot_gcode.StartGcode

            for gcode in snapshot_gcode.snapshot_commands:
                if utility.is_snapshot_command(gcode, self._printer.snapshot_command):
                    snapshot_position = None
                    if len(gcodes_to_send) > 0:
                        snapshot_position = self.get_position_async(
                            start_gcode=gcodes_to_send
                        )
                        gcodes_sent_without_waiting = False
                        if snapshot_position is None:
                            has_error = True
                            self._settings.Logger.log_error(
                                "The snapshot position is None.  Either the print has cancelled or a timeout has been "
                                "reached. "
                            )
                            # don't send any more gcode if we're cancelling
                            if self._octoprint_printer.get_state_id() == "CANCELLING":
                                return None
                    # wait if we need to.
                    if gcodes_sent_without_waiting:
                        snapshot_position = self.get_position_async()

                    # TODO:  ALLOW MULTIPLE PAYLOADS
                    timelapse_snapshot_payload["snapshot_position"] = snapshot_position
                    # take a snapshot
                    snapshot_payload = self._take_snapshots()
                    # TODO:  ALLOW MULTIPLE PAYLOADS
                    timelapse_snapshot_payload["snapshot_payload"] = snapshot_payload
                    gcodes_to_send = []
                else:
                    gcodes_to_send.append(gcode)

            if len(gcodes_to_send) > 0:
                # if any commands are left, send them!
                self.send_snapshot_gcode_array(gcodes_to_send)

            if not show_real_snapshot_time:
                # return the printhead to the start position
                gcode_to_send = snapshot_gcode.ReturnCommands + snapshot_gcode.EndGcode
                if len(gcode_to_send) > 0:
                    if self._state == TimelapseState.TakingSnapshot:
                        self._settings.Logger.log_snapshot_gcode(
                            "Sending snapshot return and end gcode.")
                        self.send_snapshot_gcode_array(gcode_to_send)
            else:
                if len(snapshot_gcode.ReturnCommands) > 0:
                    self._settings.Logger.log_snapshot_gcode("Sending return gcode.")
                    return_position = self.get_position_async(
                        start_gcode=snapshot_gcode.ReturnCommands, timeout=self._position_timeout_short
                    )
                    timelapse_snapshot_payload["return_position"] = return_position
                    if return_position is None:
                        self._settings.Logger.log_error(
                            "The snapshot_position is None.  Either the print has cancelled or a timeout has been "
                            "reached. "
                        )
                        # don't send any more gcode if we're cancelling
                        if self._octoprint_printer.get_state_id() == "CANCELLING":
                            return None
                # calculate the total snapshot time
                snapshot_end_time = time.time()
                snapshot_time = snapshot_end_time - snapshot_start_time
                self._settings.Logger.log_snapshot_gcode(
                    "Stabilization and snapshot process complected in {0} seconds".format(snapshot_time)
                )
                self.SecondsAddedByOctolapse += snapshot_time
                timelapse_snapshot_payload["current_snapshot_time"] = snapshot_time
                timelapse_snapshot_payload["total_snapshot_time"] = self.SecondsAddedByOctolapse

                if len(snapshot_gcode.EndGcode) > 0:
                    if self._state == TimelapseState.TakingSnapshot:
                        self._settings.Logger.log_snapshot_gcode("Sending end gcode.")
                        self.send_snapshot_gcode_array(snapshot_gcode.EndGcode)

            # we've completed the procedure, set success
            timelapse_snapshot_payload["success"] = not has_error and not self._gcode.has_snapshot_position_errors

        except Exception as e:
            self._settings.Logger.log_exception(e)
            timelapse_snapshot_payload["error"] = "An unexpected error was encountered while running the timelapse " \
                                                  "snapshot procedure. "

        return timelapse_snapshot_payload

    # public functions
    def to_state_dict(self, include_timelapse_start_data=False):
        try:
            position_dict = None
            position_state_dict = None
            extruder_dict = None
            trigger_state = None
            snapshot_plan = None
            if self._settings is not None:
                if self.is_realtime:
                    if self._position is not None:
                        position_dict = self._position.to_position_dict()
                        position_state_dict = self._position.to_state_dict()
                        extruder_dict = self._position.current_pos.to_extruder_state_dict()
                    if self._triggers is not None:
                        trigger_state = {
                            "name": self._triggers.name,
                            "triggers": self._triggers.state_to_list()
                        }
                else:
                    snapshot_plans = None
                    printer_volume = None
                    if include_timelapse_start_data:
                        snapshot_plans = [x.to_dict() for x in self.snapshot_plans]
                        printer_volume = self.get_printer_volume_dict()
                    snapshot_plan = {
                        "printer_volume": printer_volume,
                        "snapshot_plans": snapshot_plans,
                        "current_plan_index": self.current_snapshot_plan_index,
                        "current_file_line": self._current_file_line,
                        "stabilization_type": "pre-calculated" if not self.is_realtime else "real-time",
                    }

            state_dict = {
                "extruder": extruder_dict,
                "position": position_dict,
                "position_state": position_state_dict,
                "trigger_state": trigger_state,
                "stabilization_type": "pre-calculated" if not self.is_realtime else "real-time",
                "snapshot_plan": snapshot_plan

            }
            return state_dict
        except Exception as e:
            self._settings.Logger.log_exception(e)
        # if we're here, we've reached and logged an error.
        return {
            "extruder": None,
            "position": None,
            "position_state": None,
            "trigger_state": None
        }

    def stop_snapshots(self, message=None, error=False):
        self._state = TimelapseState.WaitingToRender
        if self._timelapse_stopped_callback is not None:
            timelapse_stopped_callback_thread = threading.Thread(
                target=self._timelapse_stopped_callback, args=[message, error]
            )
            timelapse_stopped_callback_thread.daemon = True
            timelapse_stopped_callback_thread.start()
        return True

    def on_print_failed(self):
        if self._state != TimelapseState.Idle:
            self.end_timelapse("FAILED")

    def on_print_disconnecting(self):
        if self._state != TimelapseState.Idle:
            self.end_timelapse("DISCONNECTING")

    def on_print_disconnected(self):
        if self._state != TimelapseState.Idle:
            self.end_timelapse("DISCONNECTED")

    def on_print_cancelling(self):
        self._state = TimelapseState.Cancelling
        if not self._position_signal.is_set():
            self._settings.Logger.log_error(
                "The print is cancelling, but a position request is in progress.")
            self._position_payload = None
            self._position_signal.set()
        if not self._snapshot_signal.is_set():
            self._settings.Logger.log_error(
                "The print is cancelling, but a snapshot request is in progress.")
            self._most_recent_snapshot_payload = None
            self._snapshot_signal.set()

    def on_print_canceled(self):
        if self._state != TimelapseState.Idle:
            self.end_timelapse("CANCELED")

    def on_print_completed(self):
        if self._state != TimelapseState.Idle:
            self.end_timelapse("COMPLETED")

    def end_timelapse(self, print_status):
        self._print_end_status = print_status
        try:
            if self._current_job_info is None or self._current_job_info.PrintStartTime is None:
                self._reset()
            elif self._state in [
                TimelapseState.WaitingForTrigger, TimelapseState.WaitingToRender, TimelapseState.WaitingToEndTimelapse,
                TimelapseState.Cancelling
            ]:
                if not self._render_timelapse(self._print_end_status):
                    if self._render_error_callback is not None:
                        error = RenderError('timelapse_start', "The render_start function returned false")
                        render_end_callback_thread = threading.Thread(
                            target=self._render_error_callback, args=[error]
                        )
                        render_end_callback_thread.daemon = True
                        render_end_callback_thread.start()
                self._reset()

            if self._state != TimelapseState.Idle:
                self._state = TimelapseState.WaitingToEndTimelapse

        except Exception as e:
            self._settings.Logger.log_exception(e)

        if self._timelapse_end_callback is not None:
            self._timelapse_end_callback()

    def on_print_paused(self):
        try:
            if self._state == TimelapseState.Idle:
                return
            elif self._state < TimelapseState.WaitingToRender:
                self._settings.Logger.log_print_state_change("Print Paused.")
                self._triggers.pause()
        except Exception as e:
            self._settings.Logger.log_exception(e)

    def on_print_resumed(self):
        try:
            if self._state == TimelapseState.Idle:
                return
            elif self._state < TimelapseState.WaitingToRender:
                self._triggers.resume()
        except Exception as e:
            self._settings.Logger.log_exception(e)

    def is_timelapse_active(self):
        if (
            self._settings is None
            or self._state in [TimelapseState.Idle, TimelapseState.Initializing, TimelapseState.WaitingToRender]
            or self._octoprint_printer.get_state_id() == "CANCELLING"
            or self._triggers is None
            or self._triggers.count() < 1
        ):
            return False
        return True

    def get_is_rendering(self):
        return self._rendering_task_queue.qsize() > 0

    def get_is_taking_snapshot(self):
        return self._snapshot_task_queue.qsize() > 0

    def on_print_start(self, parsed_command):
        return self._print_start_callback(parsed_command)

    def on_print_start_failed(self, message):
        self._print_start_failed_callback(message)

    def on_gcode_queuing(self, command_string, cmd_type, gcode, tags):
        if self.detect_timelapse_start(command_string, tags) == (None,):
            # suppress command if the timelapse start detection routine tells us to
            # this is because preprocessing happens on a thread, and will send any detected commands after completion.
            return None,

        if not self.is_timelapse_active():
            if utility.is_snapshot_command(command_string, self._snapshot_command):
                if self._settings.profiles.current_printer().suppress_snapshot_command_always:
                    self._settings.Logger.log_info(
                        "Snapshot command {0} detected while octolapse was disabled."
                        " Suppressing command.".format(command_string)
                    )
                    return None,
                else:
                    self._settings.Logger.log_info(
                        "Snapshot command {0} detected while octolapse was disabled.  Not suppressing since "
                        "'suppress_snapshot_command_always' is false.".format(command_string)
                    )
            # if the timelapse is not active, exit without changing any gcode
            return None

        self.check_current_line_number(tags)

        self._settings.Logger.log_gcode_queuing(
            "Queuing Command: Command Type:{0}, gcode:{1}, cmd: {2}, tags: {3}".format(
                cmd_type, gcode, command_string, tags
            )
        )

        fast_cmd = fastgcodeparser.ParseGcode(command_string)

        if fast_cmd:
            parsed_command = ParsedCommand(fast_cmd[0], fast_cmd[1], command_string)
        else:
            parsed_command = ParsedCommand(None, None, command_string)

        if self.is_realtime:
            return_value = self.process_realtime_gcode(parsed_command, tags)
        else:
            return_value = self.process_pre_calculated_gcode(parsed_command, tags)

        # notify any callbacks
        self._send_state_changed_message()

        if return_value == (None,) or utility.is_snapshot_command(command_string, self._snapshot_command):
            return None,

        if parsed_command.cmd is not None:
            # see if the current command is G92 with a dummy parameter (O)
            # note that this must be done BEFORE stripping commands for test mode
            if (
                parsed_command.cmd == "G92"
                and ("O" in parsed_command.parameters)
            ):
                parsed_command.parameters.pop("O")
                if len(parsed_command.parameters) == 0:
                    # suppress command, the g92 ONLY contained an O (fake home) parameter
                    return None,
                return Commands.to_string(parsed_command)

            # look for test mode
            if self._is_test_mode and self._state >= TimelapseState.WaitingForTrigger:
                return self._commands.alter_for_test_mode(parsed_command)

        # Send the original unaltered command
        return None

    def set_next_snapshot_plan(self):
        self.current_snapshot_plan = None
        self.current_snapshot_plan_index += 1
        if len(self.snapshot_plans) > self.current_snapshot_plan_index:
            self.current_snapshot_plan = self.snapshot_plans[self.current_snapshot_plan_index]

    def process_pre_calculated_gcode(self, parsed_command, tags):
        if not {'plugin:octolapse', 'snapshot_gcode'}.issubset(tags) and 'source:file' in tags:
            if self.current_snapshot_plan is None:
                return None
            if (
                self._state == TimelapseState.WaitingForTrigger
                and self._octoprint_printer.is_printing()
                and self.current_snapshot_plan.file_line_number == self.get_current_file_line(tags)
            ):
                # time to take a snapshot!
                if self.current_snapshot_plan.parsed_command.gcode != parsed_command.gcode:
                    self._settings.Logger.log_error("The snapshot plan position does not match the actual position!  "
                                                    "Aborting Snapshot, moving to next plan.")
                    self.set_next_snapshot_plan()
                    return None

                if self._octoprint_printer.set_job_on_hold(True):
                    # We are triggering, take a snapshot
                    self._state = TimelapseState.TakingSnapshot
                    # take the snapshot on a new thread
                    thread = threading.Thread(
                        target=self.acquire_snapshot_precalculated, args=[parsed_command]
                    )
                    thread.daemon = True
                    thread.start()
                    # suppress the current command, we'll send it later
                    return None,
        return None

    def process_realtime_gcode(self, parsed_command, tags):
        # a flag indicating that we should suppress the command (prevent it from being sent to the printer)
        suppress_command = False

        # update the position tracker so that we know where all of the axis are.
        # We will need this later when generating snapshot gcode so that we can return to the previous
        # position
        try:
            # get the position state in case it has changed
            # if there has been a position or extruder state change, inform any listener

            self._position.update(parsed_command)

            # if this code is snapshot gcode, simply return it to the printer.
            if not {'plugin:octolapse', 'snapshot_gcode'}.issubset(tags):
                if not self.check_for_non_metric_errors():
                    if (self._state == TimelapseState.WaitingForTrigger
                        and (self._position.command_requires_location_detection(
                            parsed_command.cmd) and self._octoprint_printer.is_printing())):
                        # there is no longer a need to detect Octoprint start/end script, so
                        # we can put the job on hold without fear!
                        self._state = TimelapseState.AcquiringLocation

                        if self._octoprint_printer.set_job_on_hold(True):
                            thread = threading.Thread(target=self.acquire_position, args=[parsed_command])
                            thread.daemon = True
                            thread.start()
                            return None,
                    elif (
                        self._position.current_pos.has_position_error and
                        self._state != TimelapseState.AcquiringLocation
                    ):
                        # There are position errors, report them!
                        self._on_position_error()
                    elif (self._state == TimelapseState.WaitingForTrigger
                          and self._octoprint_printer.is_printing()
                          and not self._position.current_pos.has_position_error):
                        # update the triggers with the current position
                        self._triggers.update(self._position, parsed_command)

                        # see if at least one trigger is triggering
                        _first_triggering = self.get_first_triggering()

                        if _first_triggering:
                            # get the job lock
                            if self._octoprint_printer.set_job_on_hold(True):
                                # We are triggering, take a snapshot
                                self._state = TimelapseState.TakingSnapshot
                                # pause any timer triggers that are enabled
                                self._triggers.pause()

                                # take the snapshot on a new thread
                                thread = threading.Thread(
                                    target=self.acquire_snapshot_realtime, args=[parsed_command, _first_triggering]
                                )
                                thread.daemon = True
                                thread.start()
                                # suppress the current command, we'll send it later
                                return None,

                    elif self._state == TimelapseState.TakingSnapshot:
                        # Don't do anything further to any commands unless we are
                        # taking a timelapse , or if octolapse paused the print.
                        # suppress any commands we don't, under any circumstances,
                        # to execute while we're taking a snapshot

                        if parsed_command.cmd in self._commands.SuppressedSnapshotGcodeCommands:
                            suppress_command = True  # suppress the command

        except Exception as e:
            self._settings.Logger.log_exception(e)
            raise

        # do any post processing for test mode
        if suppress_command:
            return None,

    def detect_timelapse_start(self, command_string, tags):
        # detect print start, including any start gcode script
        if (
            self._settings.main_settings.is_octolapse_enabled and
            self._state == (
                (
                    TimelapseState.Idle and
                    {'trigger:comm.start_print', 'trigger:comm.reset_line_numbers'} <= tags or
                    {'script:beforePrintStarted', 'trigger:comm.send_gcode_script'} <= tags
                ) and self._octoprint_printer.is_printing()
            )
        ):
            if self._octoprint_printer.set_job_on_hold(True):

                self._state = TimelapseState.Initializing

                self._settings.Logger.log_print_state_change(
                    "Print Start Detected.  Command: {0}, Tags:{1}".format(command_string, tags)
                )
                # parse the command string
                fast_cmd = fastgcodeparser.ParseGcode(command_string)
                if fast_cmd:
                    parsed_command = ParsedCommand(fast_cmd[0], fast_cmd[1], command_string)
                else:
                    parsed_command = ParsedCommand(None, None, command_string)

                # call the synchronous callback on_print_start
                if self.on_print_start(parsed_command):
                    if self._state == TimelapseState.WaitingForTrigger:
                        # set the current line to 0 so that the plugin checks for line 1 below after startup.
                        self._current_file_line = 0
                    self._octoprint_printer.set_job_on_hold(False)
                else:
                    return None,
            else:
                self.on_print_start_failed(
                    "Unable to start timelapse, failed to acquire a job lock.  Print start failed."
                )
        return None

    def preprocessing_finished(self, parsed_command):
        self.send_snapshot_gcode_array([parsed_command.gcode])
        self._octoprint_printer.set_job_on_hold(False)

    @staticmethod
    def get_current_file_line(tags):
        # check the current line number
        if 'source:file' in tags:
            for tag in tags:
                if len(tag) > 9 and tag.startswith("fileline:"):
                    actual_file_line = tag[9:]
                    return int(actual_file_line)
        return None

    def check_current_line_number(self, tags):
        # check the current line number
        if 'source:file' in tags:
            # this line is from the file, advance!
            self._current_file_line += 1
            if "fileline:{0}".format(self._current_file_line) not in tags:
                actual_file_line = "unknown"
                for tag in tags:
                    if len(tag) > 9 and tag.startswith("fileline:"):
                        actual_file_line = tag[9:]
                message = "File line number {0} was expected, but {1} was received!".format(
                    self._current_file_line + 1,
                    actual_file_line
                )
                self._settings.Logger.log_error(message)
                self.stop_snapshots(message, True)

    def check_for_non_metric_errors(self):
        # make sure we're not using inches
        is_metric = self._position.current_pos.is_metric
        has_error = False
        error_message = ""
        if is_metric is None and self._position.current_pos.has_position_error:
            has_error = True
            error_message = "The printer profile requires an explicit G21 command before any position " \
                            "altering/setting commands, including any home commands.  Stopping timelapse, " \
                            "but continuing the print. "

        elif not is_metric and self._position.current_pos.has_position_error:
            has_error = True
            if self._printer.units_default == "inches":
                error_message = "The printer profile uses 'inches' as the default unit of measurement.  In order to" \
                    " use Octolapse, a G21 command must come before any position altering/setting commands, including" \
                    " any home commands.  Stopping timelapse, but continuing the print. "
            else:
                error_message = "The gcode file contains a G20 command (set units to inches), which Octolapse " \
                    "does not support.  Stopping timelapse, but continuing the print."

        if has_error:
            self.stop_snapshots(error_message, has_error)

        return has_error

    def get_first_triggering(self):
        try:
            # make sure we're in a state that could want to check for triggers
            if not self._state == TimelapseState.WaitingForTrigger:
                return False
            # see if the PREVIOUS command triggered (that means current gcode gets sent if the trigger[0]
            # is triggering
            first_trigger = self._triggers.get_first_triggering(0, Triggers.TRIGGER_TYPE_IN_PATH)

            if first_trigger:
                self._settings.Logger.log_triggering("An in-path snapshot is triggering")
                return first_trigger

            first_trigger = self._triggers.get_first_triggering(0, Triggers.TRIGGER_TYPE_DEFAULT)
            if first_trigger:  # We're triggering
                self._settings.Logger.log_triggering("A snapshot is triggering")
                return first_trigger
        except Exception as e:
            self._settings.Logger.log_exception(e)
            # no need to re-raise here, the trigger just won't happen
        return False

    def acquire_position(self, parsed_command):
        try:
            assert (isinstance(parsed_command, ParsedCommand))
            self._settings.Logger.log_print_state_change(
                "A position altering command has been detected.  Fetching and updating position.  "
                "Position Command: {0}".format(parsed_command.gcode))
            # Undo the last position update, we will be resending the command
            self._position.undo_update()
            current_position = self.get_position_async()

            if current_position is None:
                self._print_end_status = "POSITION_TIMEOUT"
                self._state = TimelapseState.WaitingToEndTimelapse
                self._settings.Logger.log_print_state_change(
                    "Unable to acquire a position.")
            else:
                # update position
                self._position.update_position(
                    current_position["x"],
                    current_position["y"],
                    current_position["z"],
                    current_position["e"],
                    None,
                    force=True)

            # adjust the triggering command
            gcode = parsed_command.gcode

            if gcode != "":
                if self._state == TimelapseState.AcquiringLocation:
                    self._settings.Logger.log_print_state_change(
                        "Sending triggering command for position acquisition - {0}.".format(gcode))
                    # send the triggering command
                    self.send_snapshot_gcode_array([gcode])
                else:
                    self._settings.Logger.log_print_state_change(
                        "Unable to send triggering command for position acquisition - incorrect state:{0}."
                        .format(self._state)
                    )
            # set the state
            if self._state == TimelapseState.AcquiringLocation:
                self._state = TimelapseState.WaitingForTrigger

            self._settings.Logger.log_print_state_change("Position Acquired")

        finally:
            self._octoprint_printer.set_job_on_hold(False)

    def acquire_snapshot_precalculated(self, parsed_command):
        try:
            self._settings.Logger.log_snapshot_download(
                "About to take a snapshot.  Triggering Command: {0}".format(parsed_command.gcode))
            if self._snapshot_start_callback is not None:
                snapshot_callback_thread = threading.Thread(target=self._snapshot_start_callback)
                snapshot_callback_thread.daemon = True
                snapshot_callback_thread.start()

            # take the snapshot
            self._most_recent_snapshot_payload = self._take_timelapse_snapshot_precalculated(
                parsed_command
            )

            if self._most_recent_snapshot_payload is None:
                self._settings.Logger.log_error("acquire_snapshot received a null payload.")
            else:
                self._settings.Logger.log_snapshot_download("The snapshot has completed")

        finally:

            # set the state
            if self._state == TimelapseState.TakingSnapshot:
                self._state = TimelapseState.WaitingForTrigger

            # notify that we're finished, but only if we haven't just stopped the timelapse.
            if self._most_recent_snapshot_payload is not None:
                self._settings.Logger.log_info("Sending on_snapshot_complete payload.")
                # send a copy of the dict in case it gets changed by threads.
                new_payload = self._most_recent_snapshot_payload.copy()
                self._on_trigger_snapshot_complete(new_payload)
                self._most_recent_snapshot_payload = None

            # set the next snapshot plan
            self.set_next_snapshot_plan()
            self._octoprint_printer.set_job_on_hold(False)

    def acquire_snapshot_realtime(self, parsed_command, trigger):
        try:
            self._settings.Logger.log_snapshot_download(
                "About to take a snapshot.  Triggering Command: {0}".format(parsed_command.gcode))
            if self._snapshot_start_callback is not None:
                snapshot_callback_thread = threading.Thread(target=self._snapshot_start_callback)
                snapshot_callback_thread.daemon = True
                snapshot_callback_thread.start()

            # take the snapshot
            # Todo:  We probably don't need the payload here.
            self._most_recent_snapshot_payload = self._take_timelapse_snapshot_realtime(
                parsed_command, trigger
            )

            if self._most_recent_snapshot_payload is None:
                self._settings.Logger.log_error("acquire_snapshot received a null payload.")
            else:
                self._settings.Logger.log_snapshot_download("The snapshot has completed")

        finally:

            # set the state
            if self._state == TimelapseState.TakingSnapshot:
                self._state = TimelapseState.WaitingForTrigger

            self._triggers.resume()

            # notify that we're finished, but only if we haven't just stopped the timelapse.
            if self._most_recent_snapshot_payload is not None:
                self._settings.Logger.log_info("Sending on_snapshot_complete payload.")
                # send a copy of the dict in case it gets changed by threads.
                new_payload = self._most_recent_snapshot_payload.copy()
                self._on_trigger_snapshot_complete(new_payload)
                self._most_recent_snapshot_payload = None

            self._octoprint_printer.set_job_on_hold(False)

    def on_gcode_sending(self, cmd, tags):
        if cmd == "M114" and 'plugin:octolapse' in tags:
            self._settings.Logger.log_print_state_change("The position request is being sent")
            self._position_request_sent = True

    def on_gcode_sent(self, cmd, cmd_type, gcode, tags):
        self._settings.Logger.log_gcode_sent(
            "Sent to printer: Command Type:{0}, gcode:{1}, cmd: {2}, tags: {3}".format(cmd_type, gcode, cmd, tags))

    def on_gcode_received(self, line):
        self._settings.Logger.log_gcode_received(
            "Received from printer: line:{0}".format(line)
        )
        if self._position_request_sent:
            payload = Response.check_for_position_request(line)
            if payload:
                self.on_position_received(payload)

        return line

    # internal functions
    ####################
    def _send_state_changed_message(self):
        """Notifies any callbacks about any changes contained in the dictionaries.
        If you send a dict here the client will get a message, so check the
        settings to see if they are subscribed to notifications before populating the dictinaries!"""

        if self._last_state_changed_message_time is not None and self._state != TimelapseState.Idle:
            # do not send more than 1 per second

            time_since_last_update = time.time() - self._last_state_changed_message_time
            if time_since_last_update < 1:
                if self._position.current_pos.has_position_error:
                    self.has_position_errors_to_report = True
                    self.position_errors_to_report = self._position.current_pos.has_position_error
                return

        # if another thread is trying to send the message, stop it
        if self._state_change_message_thread is not None and self._state_change_message_thread.isAlive():
            # don't send any messages if another thread is alive.
            return
        try:
            # Notify any callbacks
            if self._state_changed_callback is not None:

                def send_real_time_change_message(has_position_state_error):
                    trigger_change_list = None
                    position_change_dict = None
                    position_state_change_dict = None
                    extruder_change_dict = None
                    trigger_changes_dict = None

                    # Get the changes
                    if self._settings.main_settings.show_trigger_state_changes:
                        trigger_change_list = self._triggers.state_to_list()
                    if self._settings.main_settings.show_position_changes:
                        position_change_dict = self._position.to_position_dict()

                    update_position_state = (
                        self._settings.main_settings.show_position_state_changes
                        or has_position_state_error
                    )

                    if update_position_state:
                        position_state_change_dict = self._position.to_state_dict()
                    if self._settings.main_settings.show_extruder_state_changes:
                        extruder_change_dict = self._position.current_pos.to_extruder_state_dict()

                    # if there are any state changes, send them
                    if (
                        position_change_dict is not None
                        or position_state_change_dict is not None
                        or extruder_change_dict is not None
                        or trigger_change_list is not None
                    ):
                        if trigger_change_list is not None and len(trigger_change_list) > 0:
                            trigger_changes_dict = {
                                "name": self._triggers.name,
                                "triggers": trigger_change_list
                            }
                    change_dict = {
                        {
                            "extruder": extruder_change_dict,
                            "position": position_change_dict,
                            "position_state": position_state_change_dict,
                            "trigger_state": trigger_changes_dict,
                            "stabilization_type": self._stabilization.stabilization_type
                        }
                    }

                    if (
                        change_dict["extruder"] is not None
                        or change_dict["position"] is not None
                        or change_dict["position_state"] is not None
                        or change_dict["trigger_state"] is not None
                    ):
                        self._state_changed_callback(change_dict)
                        self._last_state_changed_message_time = time.time()

                def send_pre_calculated_change_message():
                    if (
                        not self._settings.main_settings.show_snapshot_plan_information or
                        self.current_snapshot_plan is None
                    ):
                        return
                    # if there are any state changes, send them
                    change_dict = {

                        "stabilization_type": "pre-calculated",
                        "snapshot_plan":
                        {
                            "printer_volume": self.get_printer_volume_dict(),
                            "current_plan_index": self.current_snapshot_plan_index,
                            "current_file_line": self._current_file_line,
                        }
                    }
                    self._state_changed_callback(change_dict)
                    self._last_state_changed_message_time = time.time()

                if self.is_realtime:
                    position_errors = False
                    if self.has_position_errors_to_report:
                        position_errors = self.position_errors_to_report
                    elif self._position.current_pos.has_position_error:
                        position_errors = self._position.current_pos.position_error
                    self._state_change_message_thread = threading.Thread(
                        target=send_real_time_change_message, args=[position_errors]
                    )
                else:
                    self._state_change_message_thread = threading.Thread(
                        target=send_pre_calculated_change_message
                    )
                self._state_change_message_thread.daemon = True
                self._state_change_message_thread.start()

        except Exception as e:
            # no need to re-raise, callbacks won't be notified, however.
            self._settings.Logger.log_exception(e)

    def _send_plugin_message(self, message_type, message):
        self._plugin_message_sent_callback(message_type, message)

    def _send_plugin_message_async(self, message_type, message):
        warning_thread = threading.Thread(target=self._send_plugin_message, args=[message_type, message])
        warning_thread.daemon = True
        warning_thread.start()

    def _is_trigger_waiting(self):
        # make sure we're in a state that could want to check for triggers
        if not self._state == TimelapseState.WaitingForTrigger:
            return None
        # Loop through all of the active currentTriggers
        waiting_trigger = self._triggers.get_first_waiting()
        if waiting_trigger is not None:
            return True
        return False

    def _on_position_error(self):
        # rate limited position error notification
        delay_seconds = 0
        # if another thread is trying to send the message, stop it
        if self._position_error_message_thread is not None and self._position_error_message_thread.isAlive():
            self._position_error_message_thread.cancel()

        if self._last_position_error_message_time is not None:
            # do not send more than 1 per second
            time_since_last_update = time.time() - self._last_position_error_message_time
            if time_since_last_update < 1:
                delay_seconds = 1 - time_since_last_update
                if delay_seconds < 0:
                    delay_seconds = 0

        message = self._position.current_pos.position_error
        self._settings.Logger.log_error(message)

        def _send_position_error(position_error_message):
            self._position_error_callback(position_error_message)
            self._last_position_error_message_time = time.time()

        # Send a delayed message
        self._position_error_message_thread = threading.Timer(
            delay_seconds,
            _send_position_error,
            [message]

        )
        self._position_error_message_thread.daemon = True
        self._position_error_message_thread.start()

    def _on_trigger_snapshot_complete(self, snapshot_payload):
        if self._snapshot_complete_callback is not None:
            payload = {
                "success": snapshot_payload["success"],
                "error": snapshot_payload["error"],
                "snapshot_count":  self._capture_snapshot.SnapshotsTotal,
                "snapshot_payload": snapshot_payload["snapshot_payload"],
                "total_snapshot_time": snapshot_payload["total_snapshot_time"],
                "current_snapshot_time": snapshot_payload["total_snapshot_time"]
            }

            snapshot_complete_callback_thread = threading.Thread(
                target=self._snapshot_complete_callback, args=[payload]
            )
            snapshot_complete_callback_thread.daemon = True
            snapshot_complete_callback_thread.start()

    def _render_timelapse(self, print_end_state):
        # make sure we have a non null TimelapseSettings object.  We may have terminated the timelapse for some reason
        if self._rendering_processor is not None and self._rendering_processor.enabled:
            # If we are still taking snapshots, wait for them all to finish
            if self.get_is_taking_snapshot():
                self._settings.Logger.log_render_start(
                    "Snapshot jobs are running, waiting for them to finish before rendering.")
                self._snapshot_task_queue.join()
                self._settings.Logger.log_render_start(
                    "Snapshot jobs queue has completed, starting to render.")

            self._rendering_processor.start_rendering(
                print_end_state,
                time.time(),
                self.SecondsAddedByOctolapse
            )

            return True
        return False

    def _on_render_start(self, payload):
        assert (isinstance(payload, RenderingCallbackArgs))
        self._settings.Logger.log_render_start(
            "Started rendering/synchronizing the timelapse. JobId: {0}".format(payload.JobId))

        # notify the caller
        if self._render_start_callback is not None:
            render_start_complete_callback_thread = threading.Thread(
                target=self._render_start_callback, args=(payload,)
            )
            render_start_complete_callback_thread.daemon = True
            render_start_complete_callback_thread.start()

    def _on_render_success(self, payload):
        assert (isinstance(payload, RenderingCallbackArgs))
        self._settings.Logger.log_render_complete(
            "Completed rendering. JobId: {0}".format(payload.JobId)
        )
        if self._snapshot.cleanup_after_render_complete:
            self._capture_snapshot.clean_snapshots(payload.SnapshotDirectory, payload.JobDirectory)

        if self._render_success_callback is not None:
            render_success_complete_callback_thread = threading.Thread(
                target=self._render_success_callback, args=(payload,)
            )
            render_success_complete_callback_thread.daemon = True
            render_success_complete_callback_thread.start()

    def _on_render_error(self, payload, error):
        assert (isinstance(payload, RenderingCallbackArgs))
        self._settings.Logger.log_render_complete(
            "Completed rendering. JobId: {0}".format(payload.JobId)
        )

        if self._snapshot.cleanup_after_render_fail:
            self._capture_snapshot.clean_snapshots(payload.SnapshotDirectory, payload.JobDirectory)

        if self._render_error_callback is not None:
            render_error_complete_callback_thread = threading.Thread(
                target=self._render_error_callback, args=(payload, error)
            )
            render_error_complete_callback_thread.daemon = True
            render_error_complete_callback_thread.start()

    def _reset(self):
        self._state = TimelapseState.Idle
        self._current_file_line = 0
        if self._triggers is not None:
            self._triggers.reset()
        self.CommandIndex = -1

        self._last_state_changed_message_time = None
        self._current_job_info = None
        self._snapshotGcodes = None
        self._positionRequestAttempts = 0
        self._is_test_mode = False
        self._position_request_sent = False

        # A list of callbacks who want to be informed when a timelapse ends
        self._timelapse_stop_requested = False
        self._snapshot_success = False
        self._snapshotError = ""
        self._has_been_stopped = False
        self._current_profiles = {
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
        self._current_job_info = None

    def _reset_snapshot(self):
        self._state = TimelapseState.WaitingForTrigger
        self.CommandIndex = -1
        self._snapshotGcodes = None
        self._positionRequestAttempts = 0
        self._snapshot_success = False
        self._snapshotError = ""


class TimelapseState(object):
    Idle = 1
    Initializing = 2
    WaitingForTrigger = 3
    AcquiringLocation = 4
    TakingSnapshot = 5
    WaitingToRender = 6
    WaitingToEndTimelapse = 7
    Cancelling = 8
