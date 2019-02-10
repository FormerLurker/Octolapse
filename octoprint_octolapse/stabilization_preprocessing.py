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

import octoprint_octolapse.gcode_parser
import octoprint_octolapse.position
import octoprint_octolapse.settings
import time
import os
import fastgcodeparser
import utility

class PositionPreprocessor(object):
    def __init__(
        self,
        process_position_callback,
        notification_period_seconds,
        notification_lines_min,
        on_update_progress,
        logger,
        printer_profile,
        snapshot_profile,
        octoprint_printer_profile,
        g90_influences_extruder,
        process_error_callback=None,

    ):
        self.process_position_callback = process_position_callback
        self.process_error_callback = process_error_callback
        self.commands = octoprint_octolapse.gcode_parser.Commands()
        self.printer = printer_profile
        self.position = octoprint_octolapse.position.Position(
            logger, printer_profile,
            snapshot_profile,
            octoprint_printer_profile,
            g90_influences_extruder
        )
        self.update_progress_callback = on_update_progress
        self.notification_period_seconds = notification_period_seconds
        self.notification_lines_min = notification_lines_min
        self.current_line = 0
        self.current_file_position = 0
        self.file_size_bytes = 0
        self._last_notification_time = None
        self._next_notification_time = None
        self.start_time = None
        self.end_time = None
        self.snapshot_plans = []
        self.file = None

    def process_file(self, target_file_path):
        self.current_line = 0
        # get the start time so we can time the process
        self.start_time = time.time()
        self.end_time = None

        # Don't process any lines if there are no processors
        self.current_file_position = 0
        self.file_size_bytes = os.path.getsize(target_file_path)

        # Set the time of our last notification the the current time.
        # We will periodically call on_update_progress to report our
        # current parsing progress
        self._next_notification_time = time.time() + self.notification_period_seconds
        self._next_notification_line = self.notification_lines_min
        # process any forward items
        self.process_forwards(target_file_path)

        self.end_time = time.time()
        self.notify_progress(end_progress=True)

        return self.get_results()

    def process_forwards(self, target_file_path):
        # open the file for streaming
        # we're using binary read to avoid file.tell() issues with windows
        with open(target_file_path, 'rb') as self.file:
            for line in self.file:
                fast_cmd = fastgcodeparser.ParseGcode(line)
                if not fast_cmd:
                    continue
                self.current_line += 1
                cmd = octoprint_octolapse.gcode_parser.ParsedCommand(fast_cmd[0], fast_cmd[1], line)

                if cmd.cmd is not None:
                    self.position.update(cmd)
                    self.process_position_callback(self.position)

                if self._next_notification_line < self.current_line:
                    if self._next_notification_time < time.time():
                        self.notify_progress()
                        self._next_notification_time = time.time() + self.notification_period_seconds
                    self._last_notification_line = self.current_line + self.notification_lines_min

        self.file = None

    def notify_progress(self, end_progress=False):
        if self.update_progress_callback is None:
            return
        if end_progress:
            self.update_progress_callback(100, self.end_time - self.start_time, self.current_line)
        else:
            if self.file is None:
                self.current_file_position = self.file.tell()
            self.update_progress_callback(self.get_percent_finished(), time.time() - self.start_time, self.current_line)

    def get_current_file_position(self):
        if self.file is not None:
            return self.file.tell()

    def get_results(self):
        return {
            "snapshot_plans": self.snapshot_plans,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "bytes_processed": self.file_size_bytes,
            "lines_processed": self.current_line
        }


    def get_percent_finished(self):
        try:
            if self.file_size_bytes == 0:
                return 0
            return float(self.current_file_position)/float(self.file_size_bytes) * 100.0
        except ValueError as e:
            return 0
        except Exception as e:
            return 0

    def add_snapshot_plan(self, plan):
        self.snapshot_plans.append(plan)

    def default_matching_function(self, matches):
        pass


TRAVEL_ACTION = "travel"
SNAPSHOT_ACTION = "snapshot"
class SnapshotPlanStep(object):
    def __init__(self, action, x=None, y=None, z=None, e=None, f=None):
        self.action = action
        if action == TRAVEL_ACTION:
            self.X = x
            self.Y = y
            self.Z = z
            self.e = e
            self.f = f


class SnapshotPlan(object):
    def __init__(self, initial_position, file_line_number, saved_position_file_position, z_lift_height, retraction_length, parsed_command,
                 send_parsed_command='first'):
        self.file_line_number = file_line_number
        self.x = initial_position.x
        self.y = initial_position.y
        self.z = initial_position.z
        self.speed = initial_position.f
        self.is_xyz_relative = initial_position.is_relative
        self.is_e_relative = initial_position.is_extruder_relative
        self.lift_amount = initial_position.distance_to_zlift(z_lift_height)
        self.retract_amount = initial_position.length_to_retract(retraction_length)
        self.is_metric = initial_position.is_metric
        self.steps = []
        self.parsed_command = parsed_command
        self.send_parsed_command = send_parsed_command
        self.saved_position_file_position = saved_position_file_position

    def add_step(self, step):
        assert (isinstance(step, SnapshotPlanStep))
        self.steps.append(step)


class NearestToPrintPreprocessor(PositionPreprocessor):
    FRONT_LEFT = "front-left"
    FRONT_RIGHT = "front-right"
    BACK_LEFT = "back-left"
    BACK_RIGHT = "back-right"
    FAVOR_X = "x"
    FAVOR_Y = "y"

    def __init__(self, logger, printer_profile, snapshot_profile, octoprint_printer_profile, g90_influences_extruder,
                 nearest_to=FRONT_LEFT, favor_axis=FAVOR_X, bounding_box=None, update_progress_callback=None,
                 process_error_callback=None, z_lift_height=0, retraction_distance=0, height_increment=0):
        super(NearestToPrintPreprocessor, self).__init__(
            self.position_received,
            1,
            5000,
            update_progress_callback,
            logger,
            printer_profile,
            snapshot_profile,
            octoprint_printer_profile,
            g90_influences_extruder,
            process_error_callback
        )
        self.is_bound = bounding_box is not None
        if self.is_bound:
            self.x_min = bounding_box[0]
            self.x_max = bounding_box[1]
            self.y_min = bounding_box[2]
            self.y_max = bounding_box[3]
            self.z_min = bounding_box[4]
            self.z_max = bounding_box[5]

        self.nearest_to = nearest_to
        self.favor_x = favor_axis == self.FAVOR_X
        self.z_lift_height = 0
        self.retraction_distance = 0
        self.z_lift_height = z_lift_height
        self.retraction_distance = retraction_distance
        self.height_increment = height_increment
        self.current_layer = 0
        self.current_height = 0
        self.saved_position = None
        self.saved_position_line = 0
        self.saved_position_file_position = 0
    def position_received(self, position):
        current_pos = position.current_pos
        if (
            current_pos.is_layer_change and
            self.saved_position is not None
        ):
            # On layer change create a plan
            # TODO:  get rid of newlines and whitespace in the fast gcode parser
            self.saved_position.parsed_command.gcode = self.saved_position.parsed_command.gcode.strip()
            plan = SnapshotPlan(
                self.saved_position,
                self.saved_position_line,
                self.saved_position_file_position,
                self.z_lift_height,
                self.retraction_distance,
                self.saved_position.parsed_command,
                send_parsed_command='first'

            )
            plan.add_step(SnapshotPlanStep(SNAPSHOT_ACTION))
            # add the plan to our list of plans
            self.add_snapshot_plan(plan)
            self.current_height = self.saved_position.height
            self.current_layer = self.saved_position.layer
            # set the state for the next layer
            self.saved_position = None
            self.saved_position_line = None
            self.current_file_position = None
        if (
            current_pos.layer > 0 and
            current_pos.x is not None and
            current_pos.y is not None and
            current_pos.z is not None and
            current_pos.height is not None and
            (
                current_pos.is_extruding and
                (
                    self.height_increment == 0 or
                    self.current_height == 0 or
                    (
                        utility.round_to_float_equality_range(
                                current_pos.height - self.current_height) >= self.height_increment
                        and
                        (
                            self.saved_position is None or current_pos.height > self.current_height
                        )
                    )
                )
            )
        ):
            if self.is_closer(current_pos):
                self.saved_position = current_pos
                self.saved_position_line = self.current_line
                self.saved_position_file_position = self.get_current_file_position()

    def is_closer(self, position):
        # check our bounding box
        if self.is_bound:
            if (
                position.x < self.x_min or
                position.x > self.x_max or
                position.y < self.y_min or
                position.y > self.y_max or
                position.z < self.z_min or
                position.z > self.z_max
            ):
                return False
        if self.saved_position is None:
            return True

        first_coordinate = position.x if self.favor_x else position.y
        first_coordinate_saved = self.saved_position.x if self.favor_x else self.saved_position.y
        second_coordinate = position.y if self.favor_x else position.x
        second_coordinate_saved = self.saved_position.y if self.favor_x else self.saved_position.x

        if self.nearest_to == NearestToPrintPreprocessor.FRONT_LEFT:
            if first_coordinate < first_coordinate_saved:
                return True
            elif first_coordinate == first_coordinate_saved and second_coordinate < second_coordinate_saved:
                return True
        elif self.nearest_to == NearestToPrintPreprocessor.FRONT_RIGHT:
            if first_coordinate < first_coordinate_saved:
                return True
            elif first_coordinate == first_coordinate_saved and second_coordinate > second_coordinate_saved:
                return True
        elif self.nearest_to == NearestToPrintPreprocessor.BACK_LEFT:
            if first_coordinate > first_coordinate_saved:
                return True
            elif first_coordinate == first_coordinate_saved and second_coordinate < second_coordinate_saved:
                return True
        elif self.nearest_to == NearestToPrintPreprocessor.BACK_RIGHT:
            if first_coordinate > first_coordinate_saved:
                return True
            elif first_coordinate == first_coordinate_saved and second_coordinate > second_coordinate_saved:
                return True

        return False
