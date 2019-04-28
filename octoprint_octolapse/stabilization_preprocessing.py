# coding=utf-8
##################################################################################
# Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
# Copyright (C) 2019  Brad Hochgesang
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
from six.moves import queue
from octoprint_octolapse.gcode import SnapshotPlan, SnapshotGcodeGenerator
from octoprint_octolapse.settings import PrinterProfile, StabilizationProfile
import GcodePositionProcessor

# create the module level logger
from octoprint_octolapse.log import LoggingConfigurator
logging_configurator = LoggingConfigurator()
logger = logging_configurator.get_logger(__name__)


class StabilizationPreprocessingThread(Thread):

    def __init__(
        self,
        timelapse_settings,
        progress_callback,
        complete_callback,
        cancel_event,
        parsed_command,
        notification_period_seconds=1
    ):

        super(StabilizationPreprocessingThread, self).__init__()
        printer = timelapse_settings["settings"].profiles.current_printer()
        stabilization = timelapse_settings["settings"].profiles.current_stabilization()
        assert (isinstance(printer, PrinterProfile))
        assert (isinstance(stabilization, StabilizationProfile))
        assert (
            stabilization.stabilization_type in StabilizationProfile.get_precalculated_stabilization_types()
        )
        self.gcode_generator = SnapshotGcodeGenerator(timelapse_settings["settings"], timelapse_settings["octoprint_printer_profile"])
        self.progress_callback = progress_callback
        self.complete_callback = complete_callback
        self.timelapse_settings = timelapse_settings
        g90_influences_extruder = timelapse_settings["g90_influences_extruder"]
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
        self.error = None
        self.total_seconds = 0
        self.gcodes_processed = 0
        self.lines_processed = 0

        # create the position args
        autodetect_position = printer.auto_detect_position
        origin_x = printer.origin_x
        origin_y = printer.origin_y
        origin_z = printer.origin_z
        retraction_length = printer.gcode_generation_settings.retraction_length
        z_lift_height = printer.gcode_generation_settings.z_lift_height
        priming_height = printer.priming_height
        minimum_layer_height = printer.minimum_layer_height
        xyz_axis_default_mode = printer.xyz_axes_default_mode
        e_axis_default_mode = printer.e_axis_default_mode
        units_default = printer.units_default
        location_detection_commands = printer.get_location_detection_command_list()

        self.cpp_position_args = (
            autodetect_position,
            0.0 if origin_x is None else origin_x,
            True if origin_x is None else False,  # is_origin_x_none
            0.0 if origin_y is None else origin_y,
            True if origin_y is None else False,  # is_origin_x_none
            0.0 if origin_z is None else origin_z,
            True if origin_z is None else False,  # is_origin_x_none
            retraction_length,
            z_lift_height,
            priming_height,
            minimum_layer_height,
            g90_influences_extruder,
            xyz_axis_default_mode,
            e_axis_default_mode,
            units_default,
            location_detection_commands
        )

    def run(self):
        try:
            ret_val = self._run_stabilization()
            logger.info(
                "Received %s snapshot plans from the GcodePositionProcessor stabilization in %s seconds.",
                len(ret_val[2]), ret_val[3]
            )
            results = (
                ret_val[0],  # success
                ret_val[1],  # errors
                ret_val[2],  # snapshot_plans
                ret_val[3],  # seconds_elapsed
                ret_val[4],  # gcodes processed
                ret_val[5],  # lines_processed
            )

        except Exception as e:
            logger.exception("Gcode preprocessing failed.")
            self.error = "There was a problem preprocessing your gcode file.  See plugin_octolapse.log for details"
            results = (
                False,  # success
                self.error,
                False,
                [],
                0,
                0,
                0
            )
        logger.info("Unpacking results")
        success = results[0]
        errors = results[1]
        # get snapshot plans
        cpp_snapshot_plans = results[2]
        if not cpp_snapshot_plans:
            snapshot_plans = []
            success = False
        else:
            snapshot_plans = SnapshotPlan.create_from_cpp_snapshot_plans(cpp_snapshot_plans)
        seconds_elapsed = results[3]
        gcodes_processed = results[4]
        lines_processed = results[5]
        self.complete_callback(
            success, errors, self.is_cancelled, snapshot_plans, seconds_elapsed, gcodes_processed, lines_processed,
            self.timelapse_settings, self.parsed_command
        )

    def _create_stabilization_args(self):
        # height increment calculation.  If the self.stabilization_profile.lock_to_corner_height_increment == 0
        # and vase mode is enabled, use the layer height setting if it exists
        # I'm keeping this out of the c++ routine so it can be more easily changed based on slicer
        # changes.  I might add this to the settings class.
        if self.stabilization_profile.lock_to_corner_height_increment == 0:
            if (
                self.printer_profile.gcode_generation_settings.vase_mode and
                self.printer_profile.gcode_generation_settings.layer_height
            ):
                height_increment = self.printer_profile.gcode_generation_settings.layer_height
            else:
                # use the default height increment
                height_increment = PrinterProfile.minimum_height_increment
        else:
            height_increment = self.stabilization_profile.lock_to_corner_height_increment

        stabilization_args = {
            "gcode_settings": self.printer_profile.gcode_generation_settings, # contains retraction_length and z_lift_height
            "is_bound": self.printer_profile.restrict_snapshot_area,
            "bounds": {
                'x_min': self.printer_profile.snapshot_min_x,
                'x_max': self.printer_profile.snapshot_max_x,
                'y_min': self.printer_profile.snapshot_min_y,
                'y_max': self.printer_profile.snapshot_max_y,
                'z_min': self.printer_profile.snapshot_min_z,
                'z_max': self.printer_profile.snapshot_max_z,
            },
            'height_increment': height_increment,
            'disable_retract': self.stabilization_profile.lock_to_corner_disable_retract,
            'disable_z_lift': self.stabilization_profile.lock_to_corner_disable_z_lift,
            'fastest_speed': self.stabilization_profile.fastest_speed,
            'notification_period_seconds': self.notification_period_seconds,
            'on_progress_received': self.on_progress_received,
            'file_path': self.timelapse_settings["gcode_file_path"],
        }
        return stabilization_args

    def _run_stabilization(self):
        results = None
        stabilization_args = self._create_stabilization_args()
        stabilization_type = self.stabilization_profile.stabilization_type
        is_precalculated = (
            self.stabilization_profile.stabilization_type in StabilizationProfile.get_precalculated_stabilization_types()
        )
        # If the current stabilization is not precalculated, return an error
        if not is_precalculated:
            self.error = "The current stabilization is not a pre-calculated stabilization."
            results = (
                False,  # success
                self.error,  # errors
                [],  # snapshot_plans
                0,  # seconds_elapsed
                0,  # gcodes_processed
                0  # lines_processed
            )
        elif stabilization_type == StabilizationProfile.STABILIZATION_TYPE_LOCK_TO_PRINT:
            lock_to_print_args = {
                'nearest_to_corner': self.stabilization_profile.lock_to_corner_type,
                'favor_x_axis': self.stabilization_profile.lock_to_corner_favor_axis == "x"
            }
            # run lock_to_print stabilization
            results = GcodePositionProcessor.GetSnapshotPlans_SnapToPrint(
                self.cpp_position_args,
                stabilization_args,
                lock_to_print_args
            )
        elif stabilization_type == StabilizationProfile.STABILIZATION_TYPE_MINIMIZE_TRAVEL:
            # run minimize travel stabilization
            minimize_travel_args = {
                'gcode_generator': self.gcode_generator
            }
            results = GcodePositionProcessor.GetSnapshotPlans_MinimizeTravel(
                self.cpp_position_args,
                stabilization_args,
                minimize_travel_args
            )
        else:
            self.error = "Can't find a preprocessor named {0}, unable to preprocess gcode.".format(
                self.stabilization_profile.stabilization_type)
            results = (
                False,  # success
                self.error,  # errors
                [],  # snapshot_plans
                0,  # seconds_elapsed
                0,  # gcodes_processed
                0  # lines_processed
            )

        return results

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




