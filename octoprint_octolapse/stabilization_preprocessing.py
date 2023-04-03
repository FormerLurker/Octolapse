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
from threading import Thread
# Remove python 2 support
# from six.moves import queue
import queue as queue
from octoprint_octolapse.stabilization_gcode import SnapshotPlan, SnapshotGcodeGenerator
from octoprint_octolapse.settings import PrinterProfile, TriggerProfile, StabilizationProfile
import GcodePositionProcessor
import octoprint_octolapse.error_messages as error_messages
# create the module level logger
from octoprint_octolapse.log import LoggingConfigurator
logging_configurator = LoggingConfigurator()
logger = logging_configurator.get_logger(__name__)


class StabilizationPreprocessingThread(Thread):

    def __init__(
        self,
        timelapse_settings,
        progress_callback,
        start_callback,
        complete_callback,
        cancel_event,
        parsed_command,
        notification_period_seconds=1
    ):

        super(StabilizationPreprocessingThread, self).__init__()
        logger.debug(
            "Pre-Processing thread is being constructed."
        )
        printer = timelapse_settings["settings"].profiles.current_printer()
        stabilization = timelapse_settings["settings"].profiles.current_stabilization()
        trigger = timelapse_settings["settings"].profiles.current_trigger()
        assert (isinstance(printer, PrinterProfile))
        assert (isinstance(stabilization, StabilizationProfile))
        assert (isinstance(trigger, TriggerProfile))
        assert (
            trigger.trigger_type in TriggerProfile.get_precalculated_trigger_types()
        )
        self.gcode_generator = SnapshotGcodeGenerator(
            timelapse_settings["settings"], timelapse_settings["overridable_printer_profile_settings"]
        )
        self.progress_callback = progress_callback
        self.start_callback = start_callback
        self.complete_callback = complete_callback
        self.timelapse_settings = timelapse_settings
        self.daemon = True
        self.parsed_command = parsed_command
        self.cancel_event = cancel_event
        self.is_cancelled = False
        # make sure the event is set to start with
        if not self.cancel_event.is_set():
            self.cancel_event.set()

        self.notification_period_seconds = notification_period_seconds
        self.snapshot_plans = []
        self.printer_profile = printer
        self.stabilization_profile = stabilization
        self.trigger_profile = trigger
        self.error = None
        self.total_seconds = 0
        self.gcodes_processed = 0
        self.lines_processed = 0
        self.cpp_position_args = printer.get_position_args(timelapse_settings["overridable_printer_profile_settings"])

        logger.debug(
            "Pre-Processing thread is constructed."
        )

    def run(self):
        try:
            logger.debug(
                "Pre-Processing thread is running."
            )
            # perform the start callback
            self.start_callback()
            ret_val, options = self._run_stabilization()
            logger.info(
                "Received %s snapshot plans from the GcodePositionProcessor stabilization in %s seconds.",
                len(ret_val[1]), ret_val[2]
            )
            results = (
                ret_val[0],  # success
                ret_val[1],  # snapshot_plans
                ret_val[2],  # seconds_elapsed
                ret_val[3],  # gcodes processed
                ret_val[4],  # lines_processed
                ret_val[5],  # snapshots_missed
                ret_val[6],  # quality issues
                ret_val[7],  # processing errors from c++
                ret_val[8],  # preprocessing errors from StabilizationPreprocessingThread
                options,
            )
        except Exception as e:
            logger.exception("An error occurred while running the gcode preprocessor.")
            error = error_messages.get_error(["preprocessor", "preprocessor_errors", "unhandled_exception"])
            results = (
                False,  # success
                False,
                0,
                0,
                0,
                0,
                [],
                [],
                [error],
                None
            )

        logger.info("Unpacking results")
        success = results[0]
        # get snapshot plans
        cpp_snapshot_plans = results[1]
        seconds_elapsed = results[2]
        gcodes_processed = results[3]
        lines_processed = results[4]
        missed_snapshots = results[5]
        quality_issues = self._get_quality_issues_from_cpp(results[6])
        processing_issues = self._get_processing_issues_from_cpp(results[7])
        other_errors = results[8]

        snapshot_plans = []
        if success and not cpp_snapshot_plans:
            success = False
            # see if there were any fatal processing issues
            has_fatal_issues = False
            for issue in processing_issues:
                if issue["is_fatal"]:
                    has_fatal_issues = True
                    break
            # only append the no snapshot plan error if there are no fatal processing issues and no other errors
            if not has_fatal_issues and len(other_errors) == 0:
                error = error_messages.get_error(["preprocessor", "preprocessor_errors", "no_snapshot_plans_returned"])
                other_errors.append(error)
        elif cpp_snapshot_plans:
            snapshot_plans = SnapshotPlan.create_from_cpp_snapshot_plans(cpp_snapshot_plans)

        errors = other_errors + processing_issues
        self.complete_callback(
            success, self.is_cancelled, snapshot_plans, seconds_elapsed, gcodes_processed, lines_processed,
            missed_snapshots, quality_issues, errors, self.timelapse_settings, self.parsed_command
        )

        logger.debug(
            "Pre-Processing thread is completed."
        )

    def _get_quality_issues_from_cpp(self, issues):
        quality_issues = []
        for issue in issues:
            quality_issues.append(
                error_messages.get_error(["preprocessor", "cpp_quality_issues", str(issue[0])])
            )

        return quality_issues

    def _get_processing_issues_from_cpp(self, issues):
        processing_issues = []
        for issue in issues:
            processing_issues.append(
                error_messages.get_error(["preprocessor", "cpp_processing_errors", str(issue[0])], **issue[2])
            )

        return processing_issues

    def _create_stabilization_args(self):
        # and vase mode is enabled, use the layer height setting if it exists
        # I'm keeping this out of the c++ routine so it can be more easily changed based on slicer
        # changes.  I might add this to the settings class.
        if (
            self.trigger_profile.layer_trigger_height == 0 and
            self.printer_profile.gcode_generation_settings.vase_mode and
            self.printer_profile.gcode_generation_settings.layer_height
        ):
            height_increment = self.printer_profile.gcode_generation_settings.layer_height
        else:
            height_increment = self.trigger_profile.layer_trigger_height

        stabilization_args = {
            'height_increment': height_increment,
            'notification_period_seconds': self.notification_period_seconds,
            'on_progress_received': self.on_progress_received,
            'file_path': self.timelapse_settings["gcode_file_path"],
            'gcode_generator': self.gcode_generator,
            "x_stabilization_disabled": (
                self.stabilization_profile.x_type == StabilizationProfile.STABILIZATION_AXIS_TYPE_DISABLED
            ),
            "y_stabilization_disabled": (
                self.stabilization_profile.y_type == StabilizationProfile.STABILIZATION_AXIS_TYPE_DISABLED
            ),
            "allow_snapshot_commands": self.trigger_profile.allow_smart_snapshot_commands,
            "snapshot_command": self.printer_profile.snapshot_command
        }
        return stabilization_args

    def _run_stabilization(self):
        options = {}
        stabilization_args = self._create_stabilization_args()
        # if this is a vase mode print, set the minimum layer height to the
        # height increment so we can get better layer change detection for vase mode
        if self.printer_profile.gcode_generation_settings.vase_mode:
            self.cpp_position_args["minimum_layer_height"] = stabilization_args["height_increment"]
        trigger_type = self.trigger_profile.trigger_type
        trigger_subtype = self.trigger_profile.trigger_subtype
        is_precalculated = (
            self.trigger_profile.trigger_type in TriggerProfile.get_precalculated_trigger_types()
        )
        if not is_precalculated:
            # If the current trigger is not precalculated, return an error
            # note that this would mean a programming error
            logger.error("The current trigger is not precalculated!")

            other_error = error_messages.get_error(["preprocessor", "preprocessor_errors", 'incorrect_trigger_type'])
            results = (
                False,  # success
                [],  # snapshot_plans
                0,  # seconds_elapsed
                0,  # gcodes_processed
                0,  # lines_processed
                0,  # missed_snapshots
                [],  # quality_issues
                [],  # processing_issues
                [other_error]  # other_errors
            )
        elif (
            trigger_type == TriggerProfile.TRIGGER_TYPE_SMART and
            trigger_subtype == TriggerProfile.LAYER_TRIGGER_TYPE
        ):
            # run smart layer trigger
            smart_layer_args = {
                'trigger_type': int(self.trigger_profile.smart_layer_trigger_type),
                'snap_to_print_high_quality': self.trigger_profile.smart_layer_snap_to_print_high_quality,
                'snap_to_print_smooth': self.trigger_profile.smart_layer_snap_to_print_smooth
            }
            ret_val = list(GcodePositionProcessor.GetSnapshotPlans_SmartLayer(
                self.cpp_position_args,
                stabilization_args,
                smart_layer_args
            ))
            # add the success indicator
            ret_val.insert(0, True)
            # add the 'other' errors (errors not related to the C++ call)
            ret_val.append([])
            # set the results as the ret_val in tuple form
            results = tuple(ret_val)
            logger.info("Stabilization results received, returning.")
        elif (
                trigger_type == TriggerProfile.TRIGGER_TYPE_SMART and
                trigger_subtype == TriggerProfile.GCODE_TRIGGER_TYPE
        ):
            # run smart gcode trigger
            # Note: there are no arguments for the smart gcode trigger currently
            smart_gcode_args = {

            }
            ret_val = list(GcodePositionProcessor.GetSnapshotPlans_SmartGcode(
                self.cpp_position_args,
                stabilization_args,
                smart_gcode_args
            ))
            # add the success indicator
            ret_val.insert(0, True)
            # add the 'other' errors (errors not related to the C++ call)
            ret_val.append([])
            # set the results as the ret_val in tuple form
            results = tuple(ret_val)
            logger.info("Stabilization results received, returning.")
        else:
            # If this is an unknown trigger type, report the error
            # This could happen if there is settings corruption, manual edits, or profile repo errors
            other_error = error_messages.get_error(
                ["preprocessor", "preprocessor_errors", 'unknown_trigger_type'],
                preprocessor_type=self.trigger_profile.trigger_type
            )
            results = (
                False,  # success
                [],  # snapshot_plans
                0,  # seconds_elapsed
                0,  # gcodes_processed
                0,  # lines processed
                0,  # missed_snapshots
                [],  # quality_issues
                [],  # processing_issues
                [other_error]
            )
            logger.error("The current precalculated trigger type is unknown.")
        # We need to sort the snapshot plans by line number because they can sometimes be out of order
        def sort_by_line_number(val):
            return val[0]
        results[1].sort(key=sort_by_line_number)
        return results, options

    def on_progress_received(self, percent_progress, seconds_elapsed, seconds_to_complete, gcodes_processed,
                             lines_processed):
        try:
            # Block if the we are finished processing to ensure the mail thread is always informed
            self.progress_callback(
                percent_progress, seconds_elapsed, seconds_to_complete, gcodes_processed, lines_processed
            )
        except queue.Full:
            pass

        if not self.cancel_event.is_set():
            self.is_cancelled = True
            self.cancel_event.set()

        # return true to continue processing
        return not self.is_cancelled




