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
from __future__ import unicode_literals
import threading
import time
import uuid
# remove unused usings
# from six import iteritems, string_types
# Remove python 2 support
# from six.moves import queue
import queue as queue
import os
import octoprint_octolapse.utility as utility
from octoprint_octolapse.stabilization_gcode import SnapshotGcodeGenerator, SnapshotGcode
from octoprint_octolapse.gcode_commands import Commands, Response
from octoprint_octolapse.gcode_processor import ParsedCommand
from octoprint_octolapse.position import Position
from octoprint_octolapse.settings import PrinterProfile, OctolapseSettings
from octoprint_octolapse.snapshot import CaptureSnapshot, SnapshotJobInfo, SnapshotError
from octoprint_octolapse.trigger import Triggers
import octoprint_octolapse.error_messages as error_messages
import octoprint_octolapse.stabilization_preprocessing as preprocessing
from octoprint_octolapse.gcode_processor import GcodeProcessor
# create the module level logger
from octoprint_octolapse.log import LoggingConfigurator

logging_configurator = LoggingConfigurator()
logger = logging_configurator.get_logger(__name__)


class TimelapseStartException(Exception):
    def __init__(self, message, type):
        super(TimelapseStartException, self).__init__()
        self.message = message
        self.type = type


class Timelapse(object):

    def __init__(
        self, get_current_octolapse_settings, octoprint_printer, data_folder, default_settings_folder,
        octoprint_settings,
        on_print_started=None, on_print_start_failed=None,
        on_snapshot_start=None, on_snapshot_end=None, on_new_thumbnail_available=None,
        on_post_processing_error_callback=None, on_timelapse_stopping=None,
        on_timelapse_stopped=None, on_state_changed=None, on_timelapse_end=None, on_snapshot_position_error=None,
        on_rendering_start=None
    ):
        # config variables - These don't change even after a reset
        self.state_update_period_seconds = 1
        self._data_folder = data_folder
        self._temporary_folder = get_current_octolapse_settings().main_settings.get_temporary_directory(self._data_folder)
        self.get_current_octolapse_settings = get_current_octolapse_settings
        self._settings = self.get_current_octolapse_settings() # type: OctolapseSettings
        self._octoprint_settings = octoprint_settings
        self._octoprint_printer = octoprint_printer
        self._default_settings_folder = default_settings_folder
        self._print_start_callback = on_print_started
        self._print_start_failed_callback = on_print_start_failed
        self._snapshot_start_callback = on_snapshot_start
        self._snapshot_complete_callback = on_snapshot_end
        self._new_thumbnail_available_callback = on_new_thumbnail_available
        self._on_post_processing_error_callback = on_post_processing_error_callback
        self._timelapse_stopping_callback = on_timelapse_stopping
        self._timelapse_stopped_callback = on_timelapse_stopped
        self._state_changed_callback = on_state_changed
        self._timelapse_end_callback = on_timelapse_end
        self._snapshot_position_error_callback = on_snapshot_position_error
        self._on_rendering_start_callback = on_rendering_start
        self._commands = Commands()  # used to parse and generate gcode
        self._triggers = None
        self._print_end_status = "Unknown"
        self._last_state_changed_message_time = 0
        # Settings that may be different after StartTimelapse is called

        self._octoprint_printer_profile = None
        self._current_job_info = None
        self._stabilization = None
        self._trigger = None
        self._trigger_profile = None
        self._gcode = None
        self._printer = None
        self._capture_snapshot = None
        self._position = None
        self._state = TimelapseState.Idle
        self._test_mode_enabled = False
        # State Tracking that should only be reset when starting a timelapse
        self._has_been_stopped = False
        self._timelapse_stop_requested = False
        # State tracking variables
        self.job_on_hold = False
        self.RequiresLocationDetectionAfterHome = False
        self._position_request_sent = False
        # fetch position private variables
        self._position_payload = None
        self._position_timeout_long = 600.0
        self._position_timeout_short = 60.0
        self._position_timeout_very_short = 5.0
        self._position_signal = threading.Event()
        self._position_signal.set()

        # get snapshot async private variables
        self._snapshot_success = False
        # It shouldn't take more than 5 seconds to take a snapshot!
        self._snapshot_timeout = 5.0
        self._most_recent_snapshot_payload = None

        self._stabilization_signal = threading.Event()
        self._stabilization_signal.set()

        self._current_profiles = {}
        self._current_file_line = 0

        self.snapshot_plans = None  # type: [preprocessing.SnapshotPlan]
        self.current_snapshot_plan_index = 0
        self.current_snapshot_plan = None  # type: preprocessing.SnapshotPlan
        self.is_realtime = True
        self.was_started = False
        # snapshot thread queue
        self._snapshot_task_queue = queue.Queue(maxsize=1)

        self._reset()

    def validate_snapshot_command(self, command_string):
        # there needs to be at least one non-comment non-whitespace character for the gcode command to work.
        parsed_command = GcodeProcessor.parse(command_string)
        return len(parsed_command.gcode)>0

    def get_snapshot_count(self):
        if self._capture_snapshot is None:
            return 0, 0
        return self._capture_snapshot.SnapshotsTotal, self._capture_snapshot.ErrorsTotal

    def get_current_profiles(self):
        return self._current_profiles

    def get_current_settings(self):
        return self._settings

    def get_current_state(self):
        return self._state

    def start_timelapse(
        self, settings, overridable_printer_profile_settings,
        gcode_file_path, snapshot_plans=None
    ):
        logger.debug(
            "Starting the timelapse with the current configuration."
        )
        # we must supply the settings first!  Else reset won't work properly.
        self._reset()
        # in case the settings have been destroyed and recreated
        self._settings = settings
        # ToDo:  all cloning should be removed after this point.  We already have a settings object copy.
        #  Also, we no longer need the original settings since we can use the global OctolapseSettings.Logger now
        self._printer = self._settings.profiles.current_printer()
        self._temporary_folder = self._settings.main_settings.get_temporary_directory(self._data_folder)
        self._stabilization = self._settings.profiles.current_stabilization()
        self._trigger_profile = self._settings.profiles.current_trigger()
        self.snapshot_plans = snapshot_plans
        self.current_snapshot_plan = None
        self.current_snapshot_plan_index = 0
        # set the current snapshot plan if we have any
        if self.snapshot_plans is not None and len(self.snapshot_plans) > 0:
            self.current_snapshot_plan = self.snapshot_plans[self.current_snapshot_plan_index]
        # if we have at least one snapshot plan, we must have preprocessed, so set is_realtime to false.
        self.is_realtime = self.snapshot_plans is None
        assert (isinstance(self._printer, PrinterProfile))

        self.RequiresLocationDetectionAfterHome = False
        self.overridable_printer_profile_settings = overridable_printer_profile_settings

        self._current_job_info = utility.TimelapseJobInfo(
            job_guid=uuid.uuid4(),
            print_start_time=time.time(),
            print_file_name=utility.get_filename_from_full_path(gcode_file_path),
            print_file_extension=utility.get_extension_from_full_path(gcode_file_path),
        )
        # save the timelapse job info
        self._current_job_info.save(self._temporary_folder)
        # save the rendering settings for use by the RenderingProcessor for this timelapse
        self._settings.save_rendering_settings(self._temporary_folder, self._current_job_info.JobGuid)
        self._gcode = SnapshotGcodeGenerator(self._settings, self.overridable_printer_profile_settings)

        self._capture_snapshot = CaptureSnapshot(
            self._settings,
            self._data_folder,
            self._settings.profiles.active_cameras(),
            self._current_job_info,
            self.send_gcode_for_camera,
            self._new_thumbnail_available_callback,
            self._on_post_processing_error_callback,

        )

        self._position = Position(
            self._settings.profiles.current_printer(),
            self._settings.profiles.current_trigger(), self.overridable_printer_profile_settings
        )

        self._test_mode_enabled = self._settings.main_settings.test_mode_enabled
        self._triggers = Triggers(self._settings)
        self._triggers.create()

        # take a snapshot of the current settings for use in the Octolapse Tab
        self._current_profiles = self._settings.profiles.get_profiles_dict()
        # test the position request
        if not self._test_position_request():
            message = "Your printer does not support M114, and is incompatible with Octolapse."
            if not self._settings.main_settings.cancel_print_on_startup_error:
                message += " Continue on failure is enabled so your print will continue, but the timelapse has been " \
                           "aborted."
            raise TimelapseStartException(message, 'm114_not_supported')
        self._state = TimelapseState.WaitingForTrigger
        self.was_started = True
        logger.debug(
            "The timelapse configuration is set, waiting to stop the job-on-hold lock."
        )

    _stabilization_gcode_tags = {
        'snapshot-init',
        'snapshot-start',
        'snapshot-gcode',
        'snapshot-return',
        'snapshot-end'
    }

    def get_current_temporary_folder(self):
        return self._temporary_folder

    class StabilizationGcodeStateException(Exception):
        pass

    def send_snapshot_gcode_array(self, gcode_array, tags):
        self._octoprint_printer.commands(gcode_array, tags=tags)

    def send_gcode_for_camera(self, gcode_array, timeout, wait_for_completion=True, tags=None):
        if tags is None:
            tags = {'camera-gcode'}
        if wait_for_completion:
            self.get_position_async(
                start_gcode=gcode_array, timeout=timeout, tags=tags
            )
        else:
            self.send_snapshot_gcode_array(gcode_array, tags=tags)

    def _test_position_request(self):
        logger.info("Testing M114 Support.")
        if self.get_position_async(timeout=self._position_timeout_short, no_wait=True):
            return True
        return False

    # requests a position from the printer (m400-m114), and can send optional gcode before the position request.
    # this ensures any gcode sent in the start_gcode parameter will be executed before the function returns.
    _position_acquisition_array_wait = ["M400", "M114"]
    _position_acquisition_no_wait = ["M400", "M114"]

    def get_position_async(self, start_gcode=None, timeout=None, tags=None, no_wait=False):
        self._position_payload = None
        if timeout is None:
            timeout = self._position_timeout_long

        logger.info("Octolapse is requesting a position.")

        # Warning, we can only request one position at a time!
        if self._position_signal.is_set():
            self._position_signal.clear()
            if tags is None:
                tags = set()

            # send any code that is to be run before the position request
            if start_gcode is not None and len(start_gcode) > 0:
                self.send_snapshot_gcode_array(start_gcode, tags)
                tags = set(['wait-for-position'])

            if no_wait:
                self.send_snapshot_gcode_array(["M114"], tags)
            else:
                self.send_snapshot_gcode_array(["M400", "M114"], tags)
        event_is_set = self._position_signal.wait(timeout)
        if not event_is_set:
            # we ran into a timeout while waiting for a fresh position
            logger.warning("Warning:  A timeout occurred while requesting the current position.")
            return None
        return self._position_payload

    def on_position_received(self, payload):
        # added new position request sent flag so that we can prevent position requests NOT from Octolapse from
        # triggering a snapshot.
        if self._position_request_sent:
            self._position_request_sent = False
            logger.info("Octolapse has received a position request response.")
            # set flag to false so that it can be triggered again after the next M114 sent by Octolapse
            self._position_payload = payload
            self._position_signal.set()
        else:
            logger.info("Octolapse has received an position response but did not request one.  Ignoring.")

    def _take_snapshots(self, metadata):
        snapshot_payload = {
            "success": False,
            "error": "Waiting on thread to signal, aborting"
        }
        # start the snapshot
        logger.info("Taking a snapshot.")
        self._snapshot_task_queue.join()
        self._snapshot_task_queue.put("snapshot_job")
        try:
            results = self._capture_snapshot.take_snapshots(metadata, no_wait=not self._stabilization.wait_for_moves_to_finish)
        finally:
            self._snapshot_task_queue.get()
            self._snapshot_task_queue.task_done()
        # todo - notify client here
        # todo - maintain snapshot number separately for each camera!
        succeeded = len(results) > 0
        errors = {}
        error_count = 0
        for result in results:
            assert(isinstance(result, SnapshotJobInfo))
            if not result.success:
                succeeded = False
                error_count += 1
                if isinstance(result.error, SnapshotError):
                    error_message = result.error.message
                # remove python 2 support
                # elif isinstance(result.error, string_types):
                elif isinstance(result.error, str):
                    error_message = result.error

                if result.job_type not in errors:
                    errors[result.job_type] = {"error": error_message, 'count': 1}
                else:
                    previous_error = errors[result.job_type]
                    previous_error["error"] += error_message
                    previous_error["count"] += 1

        snapshot_payload["success"] = succeeded

        error_message = ""
        if error_count == 1:
            # remove python 2 support
            # for key, value in iteritems(errors):
            for key, value in errors.items():
                error = value["error"]
                if key == 'before-snapshot':
                    error_message = "Before Snapshot Script Error: {0}"
                elif key == 'after-snapshot':
                    error_message = "After Snapshot Script Error: {0}"
                else:
                    error_message = "{0}"

                error_message = error_message.format(error)

        elif error_count > 1:
            before_snapshot_error_count = False
            after_snapshot_error_count = False
            snapshot_error_count = False
            # remove python 2 support
            # for key, value in iteritems(errors):
            for key, value in errors.items():
                if key == 'before-snapshot':
                    before_snapshot_error_count = value["count"]
                elif key == 'after-snapshot':
                    after_snapshot_error_count = value["count"]
                else:
                    snapshot_error_count = value["count"]

            error_message = "Multiple errors occurred:"
            if before_snapshot_error_count > 0:
                error_message += "{0}{1} Before Snapshot Error{2}".format(
                    os.linesep, before_snapshot_error_count, "s" if before_snapshot_error_count > 1 else ""
                )
            if snapshot_error_count > 0:
                error_message += "{0}{1} Snapshot Error{2}".format(
                    os.linesep, snapshot_error_count, "s" if snapshot_error_count > 1 else ""
                )
            if after_snapshot_error_count > 0:
                error_message += "{0}{1} After Snapshot Error{2}".format(
                    os.linesep, after_snapshot_error_count, "s" if after_snapshot_error_count > 1 else ""
                )
                error_message += "{0}See plugin_octolapse.log for details.".format(os.linesep)

        snapshot_payload["error"] = error_message

        if len(error_message) > 0:
            self._snapshot_success = False

        return snapshot_payload

    def _take_timelapse_snapshot_precalculated(self):
        timelapse_snapshot_payload = {
            "snapshot_position": None,
            "return_position": None,
            "snapshot_gcode": None,
            "snapshot_payload": None,
            "success": False,
            "error": ""
        }
        try:
            has_error = False
            # create the GCode for the timelapse and store it
            snapshot_gcode = self._gcode.create_gcode_for_snapshot_plan(
                self.current_snapshot_plan, self._position.g90_influences_extruder,
                self._trigger_profile.get_snapshot_plan_options()
            )
            # save the gcode fo the payload
            timelapse_snapshot_payload["snapshot_gcode"] = snapshot_gcode

            if snapshot_gcode is None:
                logger.warning("No snapshot gcode was generated.")
                return timelapse_snapshot_payload

            assert (isinstance(snapshot_gcode, SnapshotGcode))

            # If we have any initialization gcodes, send them before waiting for moves to finish
            if len(snapshot_gcode.InitializationGcode) > 0:
                logger.info("Queuing %d initialization commands.", len(snapshot_gcode.InitializationGcode))
                self.send_snapshot_gcode_array(snapshot_gcode.InitializationGcode, {'snapshot-init'})

            # If we have any start gcodes (lift/retract), send them before waiting for moves to finish
            if len(snapshot_gcode.StartGcode) > 0:
                logger.info("Queuing %d start commands.", len(snapshot_gcode.StartGcode))
                self.send_snapshot_gcode_array(snapshot_gcode.StartGcode, {'snapshot-start'})

            ## Send the snapshot gcodes, making sure to send an M400+M114 before taking any snapshots
            gcodes_to_send = []
            # loop through the snapshot commands and build up gocdes_to_send array, only sending the current commands
            # once we hit the snapshot command.
            for gcode in snapshot_gcode.snapshot_commands:
                if gcode == "{0} {1}".format(PrinterProfile.OCTOLAPSE_COMMAND, PrinterProfile.DEFAULT_OCTOLAPSE_SNAPSHOT_COMMAND):
                    if self._stabilization.wait_for_moves_to_finish:
                        logger.debug(
                            "Queuing %d snapshot commands, an M400 and an M114 command.  Note that the actual snapshot command is never sent.",
                            len(gcodes_to_send)
                        )
                        snapshot_position = self.get_position_async(start_gcode=gcodes_to_send, tags={'snapshot-gcode'})
                        if snapshot_position is None:
                            has_error = True
                            logger.error(
                                "The snapshot position is None.  Either the print has cancelled or a timeout has been "
                                "reached. "
                            )
                    else:
                        logger.debug(
                            "Queuing %d snapshot commands.  Not waiting for moves to finish.",
                            len(gcodes_to_send)
                        )
                        snapshot_position = None
                        self.send_snapshot_gcode_array(gcodes_to_send, {'snapshot-gcode'})
                    gcodes_to_send = []

                    # TODO:  ALLOW MULTIPLE PAYLOADS
                    timelapse_snapshot_payload["snapshot_position"] = snapshot_position
                    # take a snapshot
                    timelapse_snapshot_payload["snapshot_payload"] = self._take_snapshots(self.current_snapshot_plan.get_snapshot_metadata())
                else:
                    gcodes_to_send.append(gcode)

            if len(gcodes_to_send) > 0:
                logger.info("Queuing remaining %d snapshot commands.", len(snapshot_gcode.StartGcode))
                self.send_snapshot_gcode_array(gcodes_to_send, {"snapshot-gcode"})

            # return the printhead to the starting position by sending the return commands
            if len(snapshot_gcode.ReturnCommands) > 0:
                logger.info("Queuing %d return commands.", len(snapshot_gcode.ReturnCommands))
                self.send_snapshot_gcode_array(snapshot_gcode.ReturnCommands, {"snapshot-return"})

            # send any end gcodes, including deretract, delift, axis mode corrections, etc
            if len(snapshot_gcode.EndGcode) > 0:
                logger.info("Queuing %d end commands.", len(snapshot_gcode.EndGcode))
                self.send_snapshot_gcode_array(snapshot_gcode.EndGcode, {"snapshot-end"})

            if self._state != TimelapseState.TakingSnapshot:
                logger.warning(
                    "The timelapse state was expected to TakingSnapshots, but was equal to {0}".format(self._state)
                )
            # we've completed the procedure, set success
            timelapse_snapshot_payload["success"] = not has_error

        except Timelapse.StabilizationGcodeStateException as e:
            logger.exception("The timelapse was in the wrong state to take a snapshot.")
            timelapse_snapshot_payload["success"] = False
            timelapse_snapshot_payload["error"] = "The timelapse was stopped in the middle of a snapshot.  Skipping."
        except Exception as e:
            logger.exception("Failed to take a snapshot for the provided snapshot plan.")
            timelapse_snapshot_payload["error"] = "An unexpected error was encountered while running the timelapse " \
                                                  "snapshot procedure. "

        return timelapse_snapshot_payload

    # public functions
    def to_state_dict(self, include_timelapse_start_data=False):
        try:
            position_dict = None
            printer_state_dict = None
            extruder_dict = None
            trigger_state = None
            snapshot_plan = None

            if self._settings is not None:
                if self.is_realtime:
                    if self._position is not None:
                        position_dict = self._position.to_position_dict()
                        printer_state_dict = self._position.to_state_dict()
                        extruder_dict = self._position.current_pos.to_extruder_state_dict()
                    if self._triggers is not None:
                        trigger_state = {
                            "name": self._triggers.name,
                            "triggers": self._triggers.state_to_list()
                        }
                else:
                    snapshot_plans = None
                    total_travel_distance = 0.0
                    total_saved_travel_distance = 0.0
                    if include_timelapse_start_data:
                        if self.snapshot_plans is not None:
                            snapshot_plans = []
                            for plan in self.snapshot_plans:
                                snapshot_plans.append(plan.to_dict())
                                total_travel_distance += plan.travel_distance
                                total_saved_travel_distance += plan.saved_travel_distance
                        printer_volume = self.overridable_printer_profile_settings["volume"]
                        snapshot_plan = {
                            "printer_volume": printer_volume,
                            "snapshot_plans": snapshot_plans,
                            "total_travel_distance": total_travel_distance,
                            "total_saved_travel_distance": total_saved_travel_distance,
                            "current_plan_index": self.current_snapshot_plan_index,
                            "current_file_line": self._current_file_line,
                        }

            state_dict = {
                "extruder": extruder_dict,
                "position": position_dict,
                "printer_state": printer_state_dict,
                "trigger_state": trigger_state,
                "trigger_type": "real-time" if self.is_realtime else "pre-calculated",
                "snapshot_plan": snapshot_plan,

            }
            return state_dict
        except Exception as e:
            logger.exception("Failed to create a timelapse state dict.")
            raise e

        # if we're here, we've reached and logged an error.
        return {
            "extruder": None,
            "position": None,
            "printer_state": None,
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

    def release_job_on_hold_lock(self, force=False, reset=False, parsed_command=None):
        if parsed_command is not None:
            self._octoprint_printer.commands([parsed_command.gcode], tags={"before_release_job_lock"})

        if self.job_on_hold:
            if force or (self._stabilization_signal.is_set() and self._position_signal.is_set()):
                logger.debug("Releasing job-on-hold lock.")
                if self._octoprint_printer.is_operational():
                    try:
                         self._octoprint_printer.set_job_on_hold(False)
                    except RuntimeError as e:
                        logger.exception("Unable to release job lock.  It's likely that the printer was disconnected.")
                self.job_on_hold = False
        if reset:
            self._reset()

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

    def on_print_canceled(self):
        if self._state != TimelapseState.Idle:
            self.end_timelapse("CANCELED")

    def on_print_completed(self):
        if self._state != TimelapseState.Idle:
            self.end_timelapse("COMPLETED")

    def on_print_ended(self):
        self.snapshot_plans = []

    def end_timelapse(self, print_status):
        self._print_end_status = print_status
        try:
            if self._state != TimelapseState.Idle:
                # See if there are enough snapshots to start renderings
                snapshot_count, error_count = self.get_snapshot_count()
                if snapshot_count > 1:
                    self._render_timelapse(self._print_end_status)
                self._reset()
        except Exception as e:
            logger.exception("Failed to end the timelapse")

        if self._timelapse_end_callback is not None:
            self._timelapse_end_callback()

    def on_print_paused(self):
        try:
            if self._state == TimelapseState.Idle:
                return
            elif self._state < TimelapseState.WaitingToRender:
                logger.info("Print Paused.")
                self._triggers.pause()
        except Exception as e:
            logger.exception("Failed to pause the print.")

    def on_print_resumed(self):
        try:
            if self._state == TimelapseState.Idle:
                return
            elif self._state < TimelapseState.WaitingToRender:
                self._triggers.resume()
        except Exception as e:
            logger.exception("Failed to resume the print")

    def is_timelapse_active(self):
        if (
            self._settings is None
            or self._state in [TimelapseState.Idle, TimelapseState.Initializing, TimelapseState.WaitingToRender]
            or self._octoprint_printer.get_state_id() == "CANCELLING"
            or (self.is_realtime and (self._triggers is None or self._triggers.count() < 1))
        ):
            return False
        return True

    def get_is_test_mode_active(self):
        return self._test_mode_enabled

    def get_is_taking_snapshot(self):
        return self._snapshot_task_queue.qsize() > 0

    def on_print_start(self, parsed_command):
        self._print_start_callback(parsed_command)

    def on_print_start_failed(self, message):
        self._print_start_failed_callback(message)

    def on_gcode_queuing(self, command_string, cmd_type, gcode, tags):
        if self.detect_timelapse_start(command_string, tags) == (None,):
            # suppress command if the timelapse start detection routine tells us to
            # this is because preprocessing happens on a thread, and will send any detected commands after completion.
            return None,

        if not self.is_timelapse_active():
            current_printer = self._settings.profiles.current_printer()
            if (
                current_printer is not None and
                current_printer.suppress_snapshot_command_always and
                current_printer.is_snapshot_command(command_string)
            ):
                logger.info(
                    "Snapshot command %s detected while octolapse was disabled."
                    " Suppressing command.".format(command_string)
                )
                return None,
            else:
                # if the timelapse is not active, exit without changing any gcode
                return None

        self.check_current_line_number(tags)

        if not (
            tags is not None and
            "plugin:octolapse" in tags and
            self.log_octolapse_gcode(logger.debug, "queuing", command_string, tags)
        ):
            logger.verbose("Queuing: %s", command_string)

        if self.is_realtime:
            return_value = self.process_realtime_gcode(command_string, tags)
            parsed_command = self._position.current_pos.parsed_command
        else:
            parsed_command = GcodeProcessor.parse(command_string)
            return_value = self.process_pre_calculated_gcode(parsed_command, tags)

        # notify any callbacks
        self._send_state_changed_message()

        if (
            return_value == (None,) or (
                self._printer.is_snapshot_command(command_string)
            )
        ):
            return None,

        if parsed_command is not None and parsed_command.cmd is not None:
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
            if self._test_mode_enabled and self._state >= TimelapseState.WaitingForTrigger:
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
            current_file_line = self.get_current_file_line(tags)
            # skip plans if we need to in case any were missed.
            if self.current_snapshot_plan.file_gcode_number < current_file_line:
                while (
                    self.current_snapshot_plan.file_gcode_number < current_file_line and
                    len(self.snapshot_plans) > self.current_snapshot_plan_index
                ):
                    self.set_next_snapshot_plan()

            if (
                self._state == TimelapseState.WaitingForTrigger
                and self._octoprint_printer.is_printing()
                and self.current_snapshot_plan.file_gcode_number == current_file_line
            ):
                # time to take a snapshot!
                if self.current_snapshot_plan.triggering_command.gcode != parsed_command.gcode:
                    logger.error(
                        "The snapshot plan position (gcode number: %s, gcode:%s, line number: %s) does not match the actual position (gcode number: %s, gcode: %s)!  "
                        "Aborting Snapshot, moving to next plan.",
                        self.current_snapshot_plan.file_gcode_number,
                        self.current_snapshot_plan.triggering_command.gcode,
                        self.current_snapshot_plan.file_line_number,
                        current_file_line,
                        parsed_command.gcode
                    )
                    self.set_next_snapshot_plan()
                    return None

                if self._octoprint_printer.set_job_on_hold(True):
                    logger.debug("Setting job-on-hold lock.")
                    # this was set to 'False' earlier.  Why?
                    self.job_on_hold = True
                    # We are triggering, take a snapshot
                    self._state = TimelapseState.TakingSnapshot

                    # take the snapshot on a new thread, making sure to set a signal so we know when it is finished
                    if not self._stabilization_signal.is_set():
                        self._stabilization_signal.clear()
                    thread = threading.Thread(
                        target=self.acquire_snapshot_precalculated, args=[parsed_command]
                    )
                    thread.daemon = True
                    thread.start()
                    # suppress the current command, we'll send it later
                    return None,
        return None

    def process_realtime_gcode(self, gcode, tags):
        # a flag indicating that we should suppress the command (prevent it from being sent to the printer)
        suppress_command = False

        # update the position tracker so that we know where all of the axis are.
        # We will need this later when generating snapshot gcode so that we can return to the previous
        # position
        try:
            # get the position state in case it has changed
            # if there has been a position or extruder state change, inform any listener
            file_line_number = self.get_current_file_line(tags)
            self._position.update(gcode, file_line_number=file_line_number)
            parsed_command = self._position.current_pos.parsed_command

            # if this code is snapshot gcode, simply return it to the printer.
            if not {'plugin:octolapse', 'snapshot_gcode'}.issubset(tags):
                if not self.check_for_non_metric_errors():

                    if (
                        self._state == TimelapseState.WaitingForTrigger
                        and self._position.previous_pos.parsed_command is not None
                        and (
                            self._position.command_requires_location_detection(
                                self._position.previous_pos.parsed_command.cmd
                            )
                            and self._octoprint_printer.is_printing()
                        )
                    ):
                        # there is no longer a need to detect Octoprint start/end script, so
                        # we can put the job on hold without fear!
                        self._state = TimelapseState.AcquiringLocation

                        if self._octoprint_printer.set_job_on_hold(True):
                            logger.debug("Setting job-on-hold lock.")
                            self.job_on_hold = True
                            thread = threading.Thread(target=self.acquire_position, args=[parsed_command])
                            thread.daemon = True
                            thread.start()
                            return None,
                    elif (self._state == TimelapseState.WaitingForTrigger
                          and self._octoprint_printer.is_printing()):
                        # update the triggers with the current position
                        self._triggers.update(self._position)

                        # see if at least one trigger is triggering
                        _first_triggering = self.get_first_triggering()

                        if _first_triggering:
                            # get the job lock
                            if self._octoprint_printer.set_job_on_hold(True):
                                logger.debug("Setting job-on-hold lock.")
                                self.job_on_hold = True
                                # We are triggering, take a snapshot
                                self._state = TimelapseState.TakingSnapshot
                                # pause any timer triggers that are enabled
                                self._triggers.pause()

                                # create the snapshot plan
                                self.current_snapshot_plan = self._gcode.create_snapshot_plan(
                                    self._position, _first_triggering)

                                # take the snapshot on a new thread, making sure to set a signal so we know when it
                                # is finished
                                if not self._stabilization_signal.is_set():
                                    self._stabilization_signal.clear()
                                thread = threading.Thread(
                                    target=self.acquire_snapshot_precalculated, args=[parsed_command]
                                )
                                thread.daemon = True
                                thread.start()

                                # undo the position update since we'll be suppressing this command
                                #self._position.undo_update()

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
            logger.exception("Realtime gcode processing failed.")
            raise

        # do any post processing for test mode
        if suppress_command:
            return None,

    def detect_timelapse_start(self, command_string, tags):
        # detect print start, including any start gcode script
        if (
            self._state == TimelapseState.Idle and
            self.get_current_octolapse_settings().main_settings.is_octolapse_enabled and
            (
                (
                    'trigger:comm.start_print' in tags and
                    (
                        'trigger:comm.reset_line_numbers' in tags or
                        command_string.startswith("M23")
                    )
                ) or {'script:beforePrintStarted', 'trigger:comm.send_gcode_script'} <= tags
            ) and self._octoprint_printer.is_printing()
        ):
            if command_string.startswith("M23"):
                # SD print, can't do anything about it.  Send a warning
                error = error_messages.get_error(["init", "cant_print_from_sd"])
                logger.info(error["description"])
                self.on_print_start_failed([error])
                # continue with the print since we can't stop it
                return None

            if self._octoprint_printer.set_job_on_hold(True):
                logger.debug("Setting job-on-hold lock.")
                self.job_on_hold = True
                self._state = TimelapseState.Initializing

                logger.info(
                    "Print Start Detected.  Command: %s, Tags:%s",
                    command_string,
                    tags
                )
                # parse the command string
                try:
                    parsed_command = GcodeProcessor.parse(command_string)
                except ValueError as e:
                    self._state = TimelapseState.Idle
                    logger.exception("Unable to parse the command string.")
                    # if we don't return NONE here, we will have problems with the print!
                    return None
                except Exception as e:
                    self._state = TimelapseState.Idle
                    logger.exception("An unexpected exception occurred while trying to parse the command string.")
                    # TODO:  REMOVE THIS BECAUSE IT'S TOO BROAD!
                    raise e

                # start a thread to start the timelapse

                def run_on_print_start_callback(parsed_command):
                    self.on_print_start(parsed_command)

                thread = threading.Thread(
                    target=run_on_print_start_callback, args=[parsed_command]
                )
                thread.daemon = True
                thread.start()
                return None,
            else:
                self.on_print_start_failed(
                    error_messages['timelapse']['cannot_aquire_job_lock']
                )
        return None

    def preprocessing_finished(self, parsed_command):
        if parsed_command is not None:
            self.send_snapshot_gcode_array([parsed_command.gcode], {'pre-processing-end'})
        self.release_job_on_hold_lock()
        logger.debug("Releasing job-on-hold lock.")
        self.job_on_hold = False

    @staticmethod
    def get_current_file_line(tags):
        # check the current line number
        if 'source:file' in tags:
            for tag in tags:
                if len(tag) > 9 and tag.startswith("fileline:"):
                    actual_file_line = tag[9:]
                    return int(actual_file_line)
        return None

    @staticmethod
    def get_current_file_position(tags):
        # check the current line number
        if 'source:file' in tags:
            for tag in tags:
                if len(tag) > 9 and tag.startswith("filepos:"):
                    actual_file_position = tag[8:]
                    return int(actual_file_position)
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
                logger.error(message)
                self.stop_snapshots(message, True)

    def check_for_non_metric_errors(self):
        # make sure we're not using inches
        is_metric = self._position.current_pos.is_metric
        has_error = False
        error_message = ""
        if is_metric is None:
            has_error = True
            error_message = "The printer profile requires an explicit G21 command before any position " \
                            "altering/setting commands, including any home commands.  Stopping timelapse, " \
                            "but continuing the print. "

        elif not is_metric:
            has_error = True
            if self._printer.units_default == "inches":
                error_message = "The printer profile uses 'inches' as the default unit of measurement.  In order to" \
                    " use Octolapse, a G21 command must come before any position altering/setting commands, including" \
                    " any home commands.  Stopping timelapse, but continuing the print. "
            else:
                error_message = "The gcode file contains a G20 command (set units to inches), which Octolapse " \
                    "does not support.  Stopping timelapse, but continuing the print."

        if has_error:
            logger.error(error_message)
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
                logger.info("An in-path snapshot is triggering")
                return first_trigger

            first_trigger = self._triggers.get_first_triggering(0, Triggers.TRIGGER_TYPE_DEFAULT)
            if first_trigger:  # We're triggering
                logger.info("A snapshot is triggering")
                return first_trigger
        except Exception as e:
            logger.exception("Failed checking snapshot trigger state.")
            # no need to re-raise here, the trigger just won't happen
        return False

    def acquire_position(self, parsed_command):
        try:
            assert (isinstance(parsed_command, ParsedCommand))
            logger.info(
                "A position altering command has been detected.  Fetching and updating position.  "
                "Position Command: %s",
                parsed_command.gcode
            )
            # Undo the last position update, we will be resending the command
            self._position.undo_update()
            current_position = self.get_position_async(tags={'acquire-position'})

            if current_position is None:
                self._print_end_status = "POSITION_TIMEOUT"
                self._state = TimelapseState.WaitingToEndTimelapse
                logger.info("Unable to acquire a position.")
            else:
                # update position
                self._position.update_position(
                    current_position["x"],
                    current_position["y"],
                    current_position["z"],
                    current_position["e"],
                    None)

            # adjust the triggering command
            gcode = parsed_command.gcode

            if gcode != "":
                if self._state == TimelapseState.AcquiringLocation:
                    logger.info("Sending triggering command for position acquisition - %s", gcode)
                    # send the triggering command
                    self.send_snapshot_gcode_array([gcode], {'location-detection-command'})
                else:
                    logger.warning(
                        "Unable to send triggering command for position acquisition - incorrect state:%s.",
                        self._state
                    )
            # set the state
            if self._state == TimelapseState.AcquiringLocation:
                self._state = TimelapseState.WaitingForTrigger

            logger.info("Position Acquired")

        finally:
            self._octoprint_printer.set_job_on_hold(False)
            logger.debug("Releasing job-on-hold lock.")
            self.job_on_hold = False

    def acquire_snapshot_precalculated(self, parsed_command):
        try:
            logger.info("About to take a snapshot.  Triggering Command: %s", parsed_command.gcode)
            if self._snapshot_start_callback is not None:
                snapshot_callback_thread = threading.Thread(target=self._snapshot_start_callback)
                snapshot_callback_thread.daemon = True
                snapshot_callback_thread.start()

            # take the snapshot
            self._most_recent_snapshot_payload = self._take_timelapse_snapshot_precalculated()

            if self._most_recent_snapshot_payload is None:
                logger.error("acquire_snapshot received a null payload.")
            else:
                logger.info("The snapshot has completed")

        finally:

            # set the state
            if self._state == TimelapseState.TakingSnapshot:
                self._state = TimelapseState.WaitingForTrigger

            # notify that we're finished, but only if we haven't just stopped the timelapse.
            if self._most_recent_snapshot_payload is not None:
                logger.info("Sending on_snapshot_complete payload.")
                # send a copy of the dict in case it gets changed by threads.
                new_payload = self._most_recent_snapshot_payload.copy()
                self._on_trigger_snapshot_complete(new_payload)
                self._most_recent_snapshot_payload = None

            # set the next snapshot plan
            if not self.is_realtime:
                self.set_next_snapshot_plan()
            self._octoprint_printer.set_job_on_hold(False)
            logger.debug("Releasing job-on-hold lock.")
            self.job_on_hold = False
            self._stabilization_signal.set()

    def on_gcode_sending(self, cmd, tags):
        if cmd == "M114" and 'plugin:octolapse' in tags:
            logger.debug("The position request is being sent")
            self._position_request_sent = True
        elif self._state == TimelapseState.Idle:
            return
        elif not (
            tags is not None
            and "plugin:octolapse" in tags
            and self.log_octolapse_gcode(logger.verbose, "sending", cmd, tags)
        ):
            logger.verbose("Sending: %s", cmd)

    def on_gcode_sent(self, cmd, cmd_type, gcode, tags={}):
        if self._state == TimelapseState.Idle:
            return
        if not (
            tags is not None
            and "plugin:octolapse" in tags
            and self.log_octolapse_gcode(logger.debug, "sent", cmd, tags)
        ):
            logger.debug("Sent: %s", cmd)

    def on_gcode_received(self, line):
        if self._position_request_sent:
            payload = Response.check_for_position_request(line)
            if payload:
                self.on_position_received(payload)
        elif self._state != TimelapseState.Idle:
            logger.verbose("Received: %s", line)
        return line

    def log_octolapse_gcode(self, logf, msg, cmd, tags):
        if "acquire-position" in tags:
            logf("Acquire snapshot position gcode - %s: %s", msg, cmd)
        elif "snapshot-init" in tags:
            logf("Snapshot gcode     INIT - %s: %s", msg, cmd)
        elif "snapshot-start" in tags:
            logf("Snapshot gcode    START - %s: %s", msg, cmd)
        elif "snapshot-gcode" in tags:
            logf("Snapshot gcode SNAPSHOT - %s: %s", msg, cmd)
        elif "snapshot-return" in tags:
            logf("Snapshot gcode   RETURN - %s: %s", msg, cmd)
        elif "snapshot-end" in tags:
            logf("Snapshot gcode      END - %s: %s", msg, cmd)
        elif "wait-for-position" in tags:
            logf("Waiting for moves to complete before continuing - %s: %s", msg, cmd)
        elif "pre-processing-end" in tags:
            logf("Pre processing finished gcode - %s: %s", msg, cmd)
        elif "current-position" in tags:
            logf("Current position gcode - %s: %s", msg, cmd)
        elif "before-snapshot-gcode" in tags:
            logf("Before snapshot gcode - %s: %s", msg, cmd)
        elif "after-snapshot-gcode" in tags:
            logf("After snapshot gcode - %s: %s", msg, cmd)
        elif "camera-gcode" in tags:
            logf("Camera gcode - %s: %s", msg, cmd)
        elif "force_xyz_axis" in tags:
            logf("Force XYZ axis mode gcode - %s: %s", msg, cmd)
        elif "force_e_axis" in tags:
            logf("Force E axis mode gcode - %s: %s", msg, cmd)
        elif "preview-stabilization" in tags:
            logf("Preview stabilization gcode - %s: %s", msg, cmd)
        else:
            return False
        return True


    # internal functions
    ####################
    def _send_state_changed_message(self):
        """Notifies any callbacks about any changes contained in the dictionaries.
        If you send a dict here the client will get a message, so check the
        settings to see if they are subscribed to notifications before populating the dictinaries!"""
        try:

            if self._last_state_changed_message_time + 1 > time.time():
                return
            # Notify any callbacks
            if self._state_changed_callback is not None:

                def send_real_time_change_message():
                    trigger_change_list = None
                    position_change_dict = None
                    printer_state_change_dict = None
                    extruder_change_dict = None
                    trigger_changes_dict = None

                    # Get the changes
                    if self.get_current_octolapse_settings().main_settings.show_trigger_state_changes:
                        trigger_change_list = self._triggers.state_to_list()
                    if self.get_current_octolapse_settings().main_settings.show_position_changes:
                        position_change_dict = self._position.to_position_dict()

                    update_printer_state = (
                        self.get_current_octolapse_settings().main_settings.show_printer_state_changes
                    )

                    if update_printer_state:
                        printer_state_change_dict = self._position.to_state_dict()
                    if self.get_current_octolapse_settings().main_settings.show_extruder_state_changes:
                        extruder_change_dict = self._position.current_pos.to_extruder_state_dict()

                    # if there are any state changes, send them
                    if (
                        position_change_dict is not None
                        or printer_state_change_dict is not None
                        or extruder_change_dict is not None
                        or trigger_change_list is not None
                    ):
                        if trigger_change_list is not None and len(trigger_change_list) > 0:
                            trigger_changes_dict = {
                                "name": self._triggers.name,
                                "triggers": trigger_change_list
                            }
                    change_dict = {

                        "trigger_type": "real-time",
                        "extruder": extruder_change_dict,
                        "position": position_change_dict,
                        "printer_state": printer_state_change_dict,
                        "trigger_state": trigger_changes_dict
                    }

                    if (
                        change_dict["extruder"] is not None
                        or change_dict["position"] is not None
                        or change_dict["printer_state"] is not None
                        or change_dict["trigger_state"] is not None
                    ):
                        self._state_changed_callback(change_dict)

                def send_pre_calculated_change_message():
                    if not self.get_current_octolapse_settings().main_settings.show_snapshot_plan_information:
                        return
                    # if there are any state changes, send them
                    change_dict = {

                        "trigger_type": "pre-calculated",
                        "snapshot_plan":
                        {
                            "printer_volume": self.overridable_printer_profile_settings["volume"],
                            "current_plan_index": self.current_snapshot_plan_index,
                            "current_file_line": self._current_file_line,
                        }
                    }
                    self._state_changed_callback(change_dict)

                if self.is_realtime:
                    send_real_time_change_message()
                else:
                    send_pre_calculated_change_message()

                self._last_state_changed_message_time = time.time()

        except Exception as e:
            # no need to re-raise, callbacks won't be notified, however.
            logger.exception("Failed to send state change message.")

    def _is_trigger_waiting(self):
        # make sure we're in a state that could want to check for triggers
        if not self._state == TimelapseState.WaitingForTrigger:
            return None
        # Loop through all of the active currentTriggers
        waiting_trigger = self._triggers.get_first_waiting()
        if waiting_trigger is not None:
            return True
        return False

    def _on_trigger_snapshot_complete(self, snapshot_payload):
        if self._snapshot_complete_callback is not None:
            payload = {
                "success": snapshot_payload["success"],
                "error": snapshot_payload["error"],
                "snapshot_count":  self._capture_snapshot.SnapshotsTotal,
                "snapshot_failed_count": self._capture_snapshot.ErrorsTotal,
                "snapshot_payload": snapshot_payload["snapshot_payload"],
            }

            snapshot_complete_callback_thread = threading.Thread(
                target=self._snapshot_complete_callback, args=[payload]
            )
            snapshot_complete_callback_thread.daemon = True
            snapshot_complete_callback_thread.start()

    def _render_timelapse(self, print_end_state):
        if self.was_started:
            # If we are still taking snapshots, wait for them all to finish
            if self.get_is_taking_snapshot():
                logger.info("Snapshot jobs are running, waiting for them to finish before rendering.")
                self._snapshot_task_queue.join()
            logger.info("Snapshot jobs queue has completed, starting to render.")
            # todo:  update print job info
            self._current_job_info.PrintEndTime = time.time()
            self._current_job_info.PrintEndState = print_end_state
            self._current_job_info.save(self._temporary_folder)
            for camera in self._settings.profiles.active_cameras():
                self._on_rendering_start_callback(self._current_job_info.JobGuid, camera.guid, self._temporary_folder)

    def _reset(self):
        self._state = TimelapseState.Idle
        self._current_file_line = 0
        if self._triggers is not None:
            self._triggers.reset()
        self.CommandIndex = -1

        self._last_state_changed_message_time = 0
        self._current_job_info = None
        self._snapshotGcodes = None
        self._positionRequestAttempts = 0
        self._test_mode_enabled = False
        self._position_request_sent = False

        # A list of callbacks who want to be informed when a timelapse ends
        self._timelapse_stop_requested = False
        self._snapshot_success = False
        self._snapshotError = ""
        self._has_been_stopped = False
        self._current_profiles = {
            "printer": "",
            "stabilization": "",
            "trigger": "",
            "snapshot": "",
            "rendering": "",
            "camera": "",
            "logging_profile": ""
        }
        # fetch position private variables
        self._position_payload = None
        self._position_signal.set()
        self._current_job_info = None
        self.was_started = False

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
