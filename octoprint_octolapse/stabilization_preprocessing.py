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
from threading import Thread, Event
import Queue
from gcode_parser import ParsedCommand
from settings import PrinterProfile, StabilizationProfile, OctolapseSettings
from octoprint_octolapse.position import Pos
import GcodePositionProcessor
import time
import traceback
TRAVEL_ACTION = "travel"
SNAPSHOT_ACTION = "snapshot"


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
        #assert (isinstance(progress_queue, Queue.Queue))
        printer = timelapse_settings["settings"].profiles.current_printer()
        stabilization = timelapse_settings["settings"].profiles.current_stabilization()
        assert (isinstance(printer, PrinterProfile))
        assert (isinstance(stabilization, StabilizationProfile))
        assert (
            stabilization.stabilization_type == StabilizationProfile.STABILIZATION_TYPE_PRE_CALCULATED
        )
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
            # Run the correct stabilization
            if (
                self.stabilization_profile.pre_calculated_stabilization_type ==
                StabilizationProfile.LOCK_TO_PRINT_CORNER_STABILIZATION
            ):
                ret_val = self._run_lock_to_print()
                OctolapseSettings.Logger.log_info(
                    "Received {0} snapshot plans from the GcodePositionProcessor stabilization in {1} seconds.".format(
                        len(ret_val[2]), ret_val[3]
                    )
                )
                results = (
                    ret_val[0],  # success
                    ret_val[1],  # errors
                    ret_val[2],  # snapshot_plans
                    ret_val[3],  # seconds_elapsed
                    ret_val[4],  # gcodes processed
                    ret_val[5],  # lines_processed
                )
            else:
                self.error = "Can't find a preprocessor named {0}, unable to preprocess gcode.".format(
                    self.stabilization_profile.pre_calculated_stabilization_type)
                results = (
                    False,  # success
                    self.error,  # errors
                    [],  # snapshot_plans
                    0,  # seconds_elapsed
                    0,  # gcodes_processed
                    0  # lines_processed
                )
        except Exception as e:
            OctolapseSettings.Logger.log_exception(e)
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
        OctolapseSettings.Logger.log_info("Unpacking results")
        success = results[0]
        errors = results[1]

        snapshot_plans = SnapshotPlan.create_from_cpp_snapshot_plans(results[2])
        seconds_elapsed = results[3]
        gcodes_processed = results[4]
        lines_processed = results[5]
        self.complete_callback(
            success, errors, self.is_cancelled, snapshot_plans, seconds_elapsed, gcodes_processed, lines_processed,
            self.timelapse_settings, self.parsed_command
        )


    def _run_lock_to_print(self):
        # create position processor arguments
        gcode_settings = self.printer_profile.gcode_generation_settings
        is_bound = self.printer_profile.restrict_snapshot_area
        x_min = self.printer_profile.snapshot_min_x
        x_max = self.printer_profile.snapshot_max_x
        y_min = self.printer_profile.snapshot_min_y
        y_max = self.printer_profile.snapshot_max_y
        z_min = self.printer_profile.snapshot_min_z
        z_max = self.printer_profile.snapshot_max_z
        stabilization_type = StabilizationProfile.LOCK_TO_PRINT_CORNER_STABILIZATION
        disable_retract = self.stabilization_profile.lock_to_corner_disable_retract
        retraction_length = gcode_settings.retraction_length
        disable_z_lift = self.stabilization_profile.lock_to_corner_disable_z_lift
        z_lift_height = gcode_settings.z_lift_height
        height_increment = self.stabilization_profile.lock_to_corner_height_increment
        nearest_to_corner = self.stabilization_profile.lock_to_corner_type
        favor_x_axis = self.stabilization_profile.lock_to_corner_favor_axis == "x"
        stabilization_args = (
            self.cpp_position_args,
            is_bound,
            x_min,
            x_max,
            y_min,
            y_max,
            z_min,
            z_max,
            stabilization_type,
            disable_retract,
            retraction_length,
            disable_z_lift,
            z_lift_height,
            height_increment,
            self.notification_period_seconds
        )
        # Start the processor
        return GcodePositionProcessor.GetSnapshotPlans_LockToPrint(
            self.timelapse_settings["gcode_file_path"],
            stabilization_args,
            self.on_progress_received,
            nearest_to_corner,
            favor_x_axis)

    def on_progress_received(self, percent_progress, seconds_elapsed, seconds_to_complete, gcodes_processed,
                             lines_processed):
        try:
            # Block if the we are finished processing to ensure the mail thread is always informed
            self.progress_callback(
                percent_progress, seconds_elapsed, seconds_to_complete, gcodes_processed, lines_processed
            )
        except Queue.Full:
            pass

        if not self.cancel_event.is_set():
            self.is_cancelled = True
            self.cancel_event.set()

        # return true to continue processing
        return not self.is_cancelled


class SnapshotPlanStep(object):
    def __init__(self, action, x=None, y=None, z=None, e=None, f=None):
        self.x = x
        self.y = y
        self.z = z
        self.e = e
        self.f = f
        self.action = action

    def to_dict(self):
        return {
            "action": self.action,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "e": self.e,
            "f": self.f,
        }


class SnapshotPlan(object):
    def __init__(self,
                 initial_position,
                 snapshot_positions,
                 return_position,
                 file_line_number,
                 file_gcode_number,
                 z_lift_height,
                 retraction_length,
                 parsed_command,
                 send_parsed_command='first'):
        self.file_line_number = file_line_number
        self.file_gcode_number = file_gcode_number
        self.initial_position = initial_position
        self.snapshot_positions = snapshot_positions
        self.return_position = return_position
        self.steps = []
        self.parsed_command = parsed_command
        self.send_parsed_command = send_parsed_command
        self.lift_amount = z_lift_height
        self.retract_amount = retraction_length

    def add_step(self, step):
        assert (isinstance(step, SnapshotPlanStep))
        self.steps.append(step)

    def to_dict(self):
        try:
            return {
                "initial_position": self.initial_position.to_dict(),
                "snapshot_positions": [x.to_dict() for x in self.snapshot_positions],
                "return_position": self.return_position.to_dict(),
                "steps": [x.to_dict() for x in self.steps],
                "parsed_command": self.parsed_command.to_dict(),
                "send_parsed_command": self.send_parsed_command,
                "file_line_number": self.file_line_number,
                "file_gcode_number": self.file_gcode_number,
                "lift_amount": self.lift_amount,
                "retract_amount": self.retract_amount,
            }
        except Exception as e:
            OctolapseSettings.Logger.log_exception(e)
            raise e

    @classmethod
    def create_from_cpp_snapshot_plans(cls, cpp_snapshot_plans):
        # turn the snapshot plans into a class
        snapshot_plans = []
        try:
            for cpp_plan in cpp_snapshot_plans:
                # extract the arguments
                file_line_number = cpp_plan[0]
                file_gcode_number = cpp_plan[1]
                initial_position = Pos.create_from_cpp_pos(cpp_plan[2])
                snapshot_positions = []
                for cpp_snapshot_position in cpp_plan[3]:
                    try:
                        pos = Pos.create_from_cpp_pos(cpp_snapshot_position)
                    except Exception as e:
                        OctolapseSettings.Logger.log_exception(e)
                        return None
                    snapshot_positions.append(pos)
                return_position = Pos.create_from_cpp_pos(cpp_plan[4])
                parsed_command = ParsedCommand.create_from_cpp_parsed_command(cpp_plan[6])
                send_parsed_command = cpp_plan[7]
                z_lift_height = cpp_plan[8]
                retraction_length = cpp_plan[9]
                snapshot_plan = SnapshotPlan(initial_position,
                                             snapshot_positions,
                                             return_position,
                                             file_line_number,
                                             file_gcode_number,
                                             z_lift_height,
                                             retraction_length,
                                             parsed_command,
                                             send_parsed_command)
                for step in cpp_plan[5]:
                    action = step[0]
                    x = step[1]
                    y = step[2]
                    z = step[3]
                    e = step[4]
                    f = step[5]
                    snapshot_plan.add_step(SnapshotPlanStep(action, x, y, z, e, f))

                snapshot_plans.append(snapshot_plan)
        except Exception as e:
            OctolapseSettings.Logger.log_exception(e)
            raise e
        return snapshot_plans

