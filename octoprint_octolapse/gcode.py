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
from __future__ import unicode_literals
from octoprint_octolapse.position import Pos, Position
from octoprint_octolapse.gcode_parser import ParsedCommand
from octoprint_octolapse.settings import *
from octoprint_octolapse.trigger import Triggers
# create the module level logger
from octoprint_octolapse.log import LoggingConfigurator
logging_configurator = LoggingConfigurator()
logger = logging_configurator.get_logger(__name__)


class SnapshotGcode(object):
    INITIALIZATION_GCODE = 'initialization-gcode'
    START_GCODE = 'start-gcode'
    SNAPSHOT_COMMANDS = 'snapshot-commands'
    RETURN_COMMANDS = 'return-commands'
    END_GCODE = 'end-gcode'

    def __init__(self):

        self.InitializationGcode = []  # commands executed here are not involved in timing calculations
        self.StartGcode = []
        self.snapshot_commands = []
        self.ReturnCommands = []
        self.EndGcode = []
        self.X = None
        self.Y = None
        self.Z = None
        self.SnapshotIndex = -1

    def snapshot_gcode(self):
        return self.InitializationGcode + self.StartGcode + self.snapshot_commands + self.ReturnCommands + self.EndGcode

    def append(self, command_type, command):
        if command_type == self.INITIALIZATION_GCODE:
            self.InitializationGcode.append(command)
        elif command_type == self.START_GCODE:
            self.StartGcode.append(command)
        elif command_type == self.SNAPSHOT_COMMANDS:
            self.snapshot_commands.append(command)
        elif command_type == self.RETURN_COMMANDS:
            self.ReturnCommands.append(command)
        elif command_type == self.END_GCODE:
            self.EndGcode.append(command)

    def end_index(self):
        return len(self.InitializationGcode) + len(self.StartGcode) + len(self.snapshot_commands) + len(self.ReturnCommands) + len(self.EndGcode) - 1

    def snapshot_index(self):
        return len(self.InitializationGcode) + len(self.StartGcode) + len(self.snapshot_commands) - 1


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
    TRAVEL_ACTION = "travel"

    def __init__(self,
                 file_line_number=None,
                 file_gcode_number=None,
                 triggering_command=None,
                 start_command=None,
                 initial_position=None,
                 steps=None,
                 return_position=None,
                 end_command=None,
                 wipe_steps=None):
        self.file_line_number = file_line_number
        self.file_gcode_number = file_gcode_number
        self.triggering_command = triggering_command
        self.initial_position = initial_position
        self.return_position = return_position
        if steps is not None:
            self.steps = steps
        else:
            self.steps = []
        if wipe_steps is not None:
            self.wipe_steps = wipe_steps
        else:
            self.wipe_steps = []
        self.start_command = start_command
        self.end_command = end_command

    SNAPSHOT_ACTION = "snapshot"

    def to_dict(self):
        try:
            return {
                "file_line_number": self.file_line_number,
                "file_gcode_number": self.file_gcode_number,
                "triggering_command": None if self.triggering_command is None else self.triggering_command.to_dict(),
                "start_command": None if self.start_command is None else self.start_command.to_dict(),
                "initial_position": None if self.initial_position is None else self.initial_position.to_dict(),
                "steps": [x.to_dict() for x in self.steps],
                "return_position": None if self.return_position is None else self.return_position.to_dict(),
                "end_command": None if self.end_command is None else self.end_command.to_dict(),
                #"wipe_steps": self.wipe_steps,  # Let's not send these yet.
            }
        except Exception as e:
            logger.exception("An error occurred while converting the snapshot plan to a dict.")
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
                triggering_command = None if cpp_plan[2] is None else ParsedCommand.create_from_cpp_parsed_command(cpp_plan[2])
                start_command = None if cpp_plan[3] is None else ParsedCommand.create_from_cpp_parsed_command(cpp_plan[3])
                initial_position = Pos.create_from_cpp_pos(cpp_plan[4])
                steps = []
                wipe_steps = []
                for step in cpp_plan[5]:
                    action = step[0]
                    x = step[1]
                    y = step[2]
                    z = step[3]
                    e = step[4]
                    f = step[5]
                    steps.append(SnapshotPlanStep(action, x, y, z, e, f))
                return_position = None if cpp_plan[6] is None else Pos.create_from_cpp_pos(cpp_plan[6])
                end_command = None if cpp_plan[7] is None else ParsedCommand.create_from_cpp_parsed_command(cpp_plan[7])
                wipe_steps = ParsedCommand.create_from_wipe_steps(cpp_plan[8])
                snapshot_plan = SnapshotPlan(
                    file_line_number,
                    file_gcode_number,
                    start_command,
                    triggering_command,
                    initial_position,
                    steps,
                    return_position,
                    end_command,
                    wipe_steps)
                snapshot_plans.append(snapshot_plan)
        except Exception as e:
            logger.exception("Failed to create snapshot plans")
            raise e
        return snapshot_plans


class SnapshotGcodeGenerator(object):
    CurrentXPathIndex = 0
    CurrentYPathIndex = 0

    def __init__(self, octolapse_settings, octoprint_printer_profile):
        self.Settings = octolapse_settings  # type: OctolapseSettings
        self._stabilization = self.Settings.profiles.current_stabilization()
        self.StabilizationPaths = self._stabilization.get_stabilization_paths()
        self.Printer = self.Settings.profiles.current_printer()
        self.snapshot_command = self.Printer.snapshot_command
        self.OctoprintPrinterProfile = octoprint_printer_profile
        self.BoundingBox = utility.get_bounding_box(
            self.Printer, octoprint_printer_profile)
        self.has_snapshot_position_errors = False
        self.snapshot_position_errors = ""
        self.gcode_generation_settings = self.Printer.get_current_state_detection_settings()
        assert(isinstance(self.gcode_generation_settings, OctolapseGcodeSettings))
        # this will be determined by the supplied position object
        self.g90_g91_affect_extruder = None
        # variables for gcode generation
        # return (original) values
        
        # current valuse
        self.x_current = None
        self.y_current = None
        self.z_current = None
        self.e_current = None
        self.f_current = None
        self.is_relative_current = None
        self.is_extruder_relative_current = None
        # calculated values
        # calculate printer retract amount
        self.length_to_retract = None
        self.distance_to_lift = None
        self.axis_mode_compatibility = self.Printer.gocde_axis_compatibility_mode_enabled

        #Snapshot Gcode Variable
        self.snapshot_gcode = None
        # state flags
        self.retracted_by_start_gcode = None
        self.lifted_by_start_gcode = None
        self.g90_influences_extruder = None
        # misc variables used for logging info
        self.last_extrusion_height = None
        self.snapshot_plan = None

    def initialize_for_snapshot_plan_processing(
        self, snapshot_plan, g90_influences_extruder, options=None
    ):
        assert(isinstance(snapshot_plan, SnapshotPlan))
        # reset any errors
        self.has_snapshot_position_errors = False
        self.snapshot_position_errors = ""

        # get the triggering command and extruder position by
        # undo the most recent position update since we haven't yet executed the most recent gcode command
        # Capture and undo the last position update, we're not going to be using it!

        # save the snapshot plan
        self.snapshot_plan = snapshot_plan

        # does G90/G91 influence the extruder
        self.g90_influences_extruder = g90_influences_extruder

        assert(isinstance(snapshot_plan.initial_position, Pos))

        self.x_current = snapshot_plan.initial_position.x
        self.y_current = snapshot_plan.initial_position.y
        self.z_current = snapshot_plan.initial_position.z
        self.e_current = snapshot_plan.initial_position.e
        self.f_current = snapshot_plan.initial_position.f
        self.is_relative_current = snapshot_plan.initial_position.is_relative
        self.is_extruder_relative_current = snapshot_plan.initial_position.is_extruder_relative

        if options is not None and "disable_z_lift" in options and options["disable_z_lift"]:
            self.distance_to_lift = 0
        else:
            z_lift_height = self.Printer.gcode_generation_settings.z_lift_height
            self.distance_to_lift = snapshot_plan.initial_position.distance_to_zlift(z_lift_height)
            if self.distance_to_lift is None:
                self.distance_to_lift = 0

        if options is not None and "disable_retract" in options and options["disable_retract"]:
            self.length_to_retract = 0
        else:
            retraction_length = self.Printer.gcode_generation_settings.retraction_length
            self.length_to_retract = snapshot_plan.initial_position.length_to_retract(retraction_length)
            if self.length_to_retract is None:
                self.length_to_retract = 0

        self.retracted_by_start_gcode = False
        self.lifted_by_start_gcode = False

        # create our gcode object
        self.snapshot_gcode = SnapshotGcode()

        return not self.has_initialization_errors()

    def has_initialization_errors(self):
        # check the units, only metric works.
        is_metric = self.snapshot_plan.initial_position.is_metric
        if is_metric is None or not is_metric:
            logger.error(
                "No unit of measurement has been set and the current"
                " printer profile is set to require explicit G20/G21, or the unit of measurement is inches. "
            )
            return True

        return False

    def get_snapshot_position(self, x_pos, y_pos):
        x_path = self.StabilizationPaths["x"]
        x_path.current_position = x_pos
        y_path = self.StabilizationPaths["y"]
        y_path.current_position = y_pos

        coordinates = dict(x=self.get_snapshot_coordinate(x_path, "x"),
                           y=self.get_snapshot_coordinate(y_path, "y"))

        if not utility.is_in_bounds(self.BoundingBox, coordinates["x"], None, None):

            message = "The snapshot X position ({0}) is out of bounds!".format(
                coordinates["x"])
            self.has_snapshot_position_errors = True
            logger.error("gcode.py - GetSnapshotPosition - %s", message)
            if self.Printer.abort_out_of_bounds:
                coordinates["x"] = None
            else:
                coordinates["x"] = utility.get_closest_in_bounds_position(
                    self.BoundingBox, x=coordinates["x"])["x"]
                message += "  Using nearest in-bound position ({0}).".format(
                    coordinates["x"])
            self.snapshot_position_errors += message
        if not utility.is_in_bounds(self.BoundingBox, None, coordinates["y"], None):
            message = "The snapshot Y position ({0}) is out of bounds!".format(
                coordinates["y"])
            self.has_snapshot_position_errors = True
            logger.error(message)
            if self.Printer.abort_out_of_bounds:
                coordinates["y"] = None
            else:
                coordinates["y"] = utility.get_closest_in_bounds_position(
                    self.BoundingBox, y=coordinates["y"])["y"]
                message += "  Using nearest in-bound position ({0}).".format(
                    coordinates["y"])
            if len(self.snapshot_position_errors) > 0:
                self.snapshot_position_errors += "  "
            self.snapshot_position_errors += message

        return coordinates

    def get_snapshot_coordinate(self, path, axis):
        if path.type == 'disabled':
            return path.current_position

        # Get the current coordinate from the path
        coord = path.path[path.index]
        # move our index forward or backward
        path.index += path.increment

        if path.index >= len(path.path):
            if path.loop:
                if path.invert_loop:
                    if len(path.path) > 1:
                        path.index = len(path.path) - 2
                    else:
                        path.index = 0
                    path.increment = -1
                else:
                    path.index = 0
            else:
                path.index = len(path.path) - 1
        elif path.index < 0:
            if path.loop:
                if path.invert_loop:
                    if len(path.path) > 1:
                        path.index = 1
                    else:
                        path.index = 0
                    path.increment = 1
                else:
                    path.index = len(path.path) - 1
            else:
                path.index = 0

        if path.coordinate_system == "absolute":
            return coord
        elif path.coordinate_system == "bed_relative":
            if self.OctoprintPrinterProfile["volume"]["formFactor"] == "circle":
                raise ValueError(
                    'Cannot calculate relative coordinates within a circular bed (yet...), sorry')
            return self.get_bed_relative_coordinate(axis, coord)

    def get_bed_relative_coordinate(self, axis, coord):
        rel_coordinate = None
        if axis == "x":
            rel_coordinate = self.get_bed_relative_x(coord)
        elif axis == "y":
            rel_coordinate = self.get_bed_relative_y(coord)
        elif axis == "Z":
            rel_coordinate = self.get_bed_relative_z(coord)

        return rel_coordinate

    def get_bed_relative_x(self, percent):
        return self.get_relative_coordinate(percent, self.BoundingBox["min_x"], self.BoundingBox["max_x"])

    def get_bed_relative_y(self, percent):
        return self.get_relative_coordinate(percent, self.BoundingBox["min_y"], self.BoundingBox["max_y"])

    def get_bed_relative_z(self, percent):
        return self.get_relative_coordinate(percent, self.BoundingBox["min_z"], self.BoundingBox["max_z"])

    @staticmethod
    def get_relative_coordinate(percent, min_value, max_value):
        return ((float(max_value) - float(min_value)) * (percent / 100.0)) + float(min_value)

    def set_e_to_relative(self, gcode_type):
        if not self.is_extruder_relative_current:
            self.snapshot_gcode.append(
                gcode_type,
                self.get_gcode_extruder_relative()
            )
            self.is_extruder_relative_current = True

    def set_xyz_to_relative(self, gcode_type):
        if not self.is_relative_current:  # must be in relative mode
            self.snapshot_gcode.append(
                gcode_type,
                self.get_gcode_axes_relative()
            )
            self.is_relative_current = True
            # this may also influence the extruder
            if self.g90_influences_extruder:
                self.is_extruder_relative_current = True

    def set_xyz_to_absolute(self, gcode_type):
        if self.is_relative_current:  # must be in relative mode
            self.snapshot_gcode.append(
                gcode_type,
                self.get_gcode_axes_absolute()
            )
            self.is_relative_current = False
            # this may also influence the extruder
            if self.g90_influences_extruder:
                self.is_extruder_relative_current = True

    def get_altered_feedrate(self, feedrate):
        if feedrate != self.f_current:
            self.f_current = feedrate
        else:
            feedrate = None
        return feedrate

    def can_retract(self):
        return self.gcode_generation_settings.retract_before_move and self.length_to_retract > 0

    def can_zhop(self):
        return (
            self.gcode_generation_settings.retract_before_move and
            self.gcode_generation_settings.lift_when_retracted and self.distance_to_lift > 0 and
            utility.is_in_bounds(
                self.BoundingBox, None, None, self.snapshot_plan.initial_position.z + self.distance_to_lift
            )
        )

    ###########################
    # Fixed mode travel, retract, and lift
    # These methods are safer, but produce more gcode
    ###########################
    def retract_relative(self):
        self.e_current -= self.length_to_retract
        self.set_e_to_relative(SnapshotGcode.START_GCODE)
        self.snapshot_gcode.append(
            SnapshotGcode.START_GCODE,
            self.get_gcode_retract(
                -1.0 * self.length_to_retract,
                self.get_altered_feedrate(self.gcode_generation_settings.retraction_speed)
            )
        )
        self.retracted_by_start_gcode = True

    def deretract_relative(self):
        if self.retracted_by_start_gcode:
            self.e_current += self.length_to_retract
            self.set_e_to_relative(SnapshotGcode.END_GCODE)
            self.snapshot_gcode.append(
                SnapshotGcode.END_GCODE,
                self.get_gcode_retract(
                    self.length_to_retract,
                    self.get_altered_feedrate(self.gcode_generation_settings.deretraction_speed)
                )
            )

    def lift_z_relative(self):
        # if we can ZHop, do
        self.z_current += self.distance_to_lift
        self.set_xyz_to_relative(SnapshotGcode.START_GCODE)
        # append to snapshot gcode
        self.snapshot_gcode.append(
            SnapshotGcode.START_GCODE,
            self.get_gcode_z_lift(
                self.distance_to_lift,
                self.get_altered_feedrate(self.gcode_generation_settings.z_lift_speed)
            )
        )
        self.lifted_by_start_gcode = True

    def delift_z_relative(self):
        if self.lifted_by_start_gcode:
            self.z_current -= self.distance_to_lift
            self.set_xyz_to_relative(SnapshotGcode.END_GCODE)
            self.snapshot_gcode.append(
                SnapshotGcode.END_GCODE,
                self.get_gcode_z_lift(
                    -1 * self.distance_to_lift,
                    self.get_altered_feedrate(self.gcode_generation_settings.z_lift_speed)
                )
            )

    def add_travel_action_absolute(self, step):
        assert (isinstance(step, SnapshotPlanStep))
        if self.x_current != step.x and self.y_current != step.y:
            # Move to Snapshot Position
            self.set_xyz_to_absolute(SnapshotGcode.SNAPSHOT_COMMANDS)
            self.x_current = step.x
            self.y_current = step.y
            self.snapshot_gcode.append(
                SnapshotGcode.SNAPSHOT_COMMANDS,
                self.get_gcode_travel(
                    step.x - self.snapshot_plan.initial_position.x_offset,
                    step.y - self.snapshot_plan.initial_position.y_offset,
                    self.get_altered_feedrate(self.gcode_generation_settings.x_y_travel_speed)
                )
            )

    def return_to_original_position_absolute(self):
        if self.snapshot_plan.return_position is not None:
            # Only return to the previous coordinates if we need to (which will be most cases,
            # except when the triggering command is a travel only (moves both X and Y, but not Z)
            if(
                self.snapshot_plan.return_position.x != self.x_current or
                self.snapshot_plan.return_position.y != self.y_current
            ):
                self.x_current = self.snapshot_plan.return_position.x
                self.y_current = self.snapshot_plan.return_position.y

                # Move back to previous position - make sure we're in absolute mode for this
                self.set_xyz_to_absolute(SnapshotGcode.RETURN_COMMANDS)

                self.snapshot_gcode.append(
                    SnapshotGcode.RETURN_COMMANDS,
                    self.get_gcode_travel(
                        self.snapshot_plan.return_position.x - self.snapshot_plan.return_position.x_offset,
                        self.snapshot_plan.return_position.y - self.snapshot_plan.return_position.y_offset,
                        self.get_altered_feedrate(self.gcode_generation_settings.x_y_travel_speed)
                    )
                )

    ###########################
    # Current axis mode travel, retract, and lift
    # These methods are safer, but produce more gcode
    ###########################
    def retract_current_mode(self):
        if self.is_extruder_relative_current:
            self.retract_relative()
        else:
            self.retracted_by_start_gcode = True
            self.e_current -= self.length_to_retract
            self.snapshot_gcode.append(
                SnapshotGcode.START_GCODE,
                self.get_gcode_retract(
                    self.e_current - self.snapshot_plan.initial_position.e_offset,
                    self.get_altered_feedrate(self.gcode_generation_settings.retraction_speed)
                )
            )

    def deretract_current_mode(self):
        if self.is_extruder_relative_current:
            self.deretract_relative()
        else:
            if self.retracted_by_start_gcode:
                self.e_current += self.length_to_retract
                self.snapshot_gcode.append(
                    SnapshotGcode.END_GCODE,
                    self.get_gcode_retract(
                        self.e_current - self.snapshot_plan.initial_position.e_offset,
                        self.get_altered_feedrate(self.gcode_generation_settings.retraction_speed)
                    )
                )

    def lift_z_current_mode(self):
        if self.is_relative_current:
            self.lift_z_relative()
        else:
            self.lifted_by_start_gcode = True
            self.z_current += self.distance_to_lift
            # append to snapshot gcode
            self.snapshot_gcode.append(
                SnapshotGcode.START_GCODE,
                self.get_gcode_z_lift(
                    self.z_current - self.snapshot_plan.initial_position.z_offset,
                    self.get_altered_feedrate(self.gcode_generation_settings.z_lift_speed)
                )
            )

    def delift_z_current_mode(self):
        if self.is_relative_current:
            self.delift_z()
        else:
            self.z_current -= self.distance_to_lift
            # append to snapshot gcode
            self.snapshot_gcode.append(
                SnapshotGcode.END_GCODE,
                self.get_gcode_z_lift(
                    self.z_current - self.snapshot_plan.initial_position.z_offset,
                    self.get_altered_feedrate(self.gcode_generation_settings.z_lift_speed)
                )
            )

    def add_travel_action_current_mode(self, step):
        assert (isinstance(step, SnapshotPlanStep))

        # Move to Snapshot Position
        if not self.is_relative_current:
            self.add_travel_action_absolute(step)
        elif self.x_current != step.x and self.y_current != step.y:
            self.x_current = step.x
            self.y_current = step.y
            self.snapshot_gcode.append(
                SnapshotGcode.SNAPSHOT_COMMANDS,
                self.get_gcode_travel(
                    self.x_current - self.snapshot_plan.initial_position.x_offset,
                    self.y_current - self.snapshot_plan.initial_position.y_offset,
                    self.get_altered_feedrate(self.gcode_generation_settings.x_y_travel_speed)
                )
            )

    def return_to_original_position_current_mode(self):
        if not self.is_relative_current:
            self.return_to_original_position_absolute()
        elif (
            self.snapshot_plan.return_position is not None and
            self.x_current != self.snapshot_plan.return_position.x and
            self.y_current != self.snapshot_plan.return_position.y
        ):
            x_relative = self.snapshot_plan.return_position.x - self.x_current
            y_relative = self.snapshot_plan.return_position.y - self.y_current
            self.x_current = self.snapshot_plan.return_position.x
            self.y_current = self.snapshot_plan.return_position.y
            self.snapshot_gcode.append(
                SnapshotGcode.RETURN_COMMANDS,
                self.get_gcode_travel(
                    x_relative,
                    y_relative,
                    self.get_altered_feedrate(self.gcode_generation_settings.x_y_travel_speed)
                )
            )

    ######################################
    # common functions for retract, lift, travel, and returning to the original position
    # Calls the appropriate functions based on the self.axis_mode_compatibility setting
    ######################################
    def send_wipe_steps(self, wipe_steps):
        for step in wipe_steps:
            self.snapshot_gcode.append(
                SnapshotGcode.INITIALIZATION_GCODE,
                step.gcode)
            # set the current feedrate if F is supplied
            if "F" in step.parameters:
                self.get_altered_feedrate(step.parameters["F"])

        self.retracted_by_start_gcode = True
        # We are fully retracted here.
        self.e_current -= self.length_to_retract

    def retract(self):
        # Todo: make sure that retract with axis mode compatibility works for wipe steps
        if self.can_retract():
            if self.snapshot_plan.wipe_steps is not None and len(self.snapshot_plan.wipe_steps)>0:
                self.send_wipe_steps(self.snapshot_plan.wipe_steps)
            elif self.axis_mode_compatibility:
                self.retract_relative()
            else:
                self.retract_current_mode()

    def deretract(self):
        if self.retracted_by_start_gcode:
            if self.axis_mode_compatibility:
                self.deretract_relative()
            else:
                self.deretract_current_mode()

    def lift_z(self):
        if (
            self.can_zhop()
        ):
            if self.axis_mode_compatibility:
                self.lift_z_relative()
            else:
                self.lift_z_current_mode()

    def delift_z(self):
        if self.lifted_by_start_gcode:
            if self.axis_mode_compatibility:
                self.delift_z_relative()
            else:
                self.delift_z_current_mode()

    def add_travel_action(self, step):
        if self.axis_mode_compatibility:
            self.add_travel_action_absolute(step)
        else:
            self.add_travel_action_current_mode(step)

    def return_to_original_position(self):
        if self.axis_mode_compatibility:
            self.return_to_original_position_absolute()
        else:
            self.return_to_original_position_current_mode()

    ###########################
    # Gcode generation functions that work in any axis mode
    ###########################
    def add_snapshot_action(self):
        # Move to Snapshot Position
        self.snapshot_gcode.append(
            SnapshotGcode.SNAPSHOT_COMMANDS,
            self.Printer.snapshot_command
        )

    def return_to_original_coordinate_systems(self):
        is_relative_return = self.snapshot_plan.initial_position.is_relative
        if self.snapshot_plan.return_position is not None:
            is_relative_return = self.snapshot_plan.return_position.is_relative

        if is_relative_return != self.is_relative_current:
            if self.is_relative_current:
                self.snapshot_gcode.append(
                    SnapshotGcode.END_GCODE,
                    self.get_gcode_axes_absolute()
                )
            else:
                self.snapshot_gcode.append(
                    SnapshotGcode.END_GCODE,
                    self.get_gcode_axes_relative()
                )
            self.is_relative_current = is_relative_return

        is_extruder_relative_return = self.snapshot_plan.initial_position.is_extruder_relative
        if self.snapshot_plan.return_position is not None:
            is_extruder_relative_return = self.snapshot_plan.return_position.is_extruder_relative

        if is_extruder_relative_return != self.is_extruder_relative_current:
            if is_extruder_relative_return:
                self.snapshot_gcode.append(
                    SnapshotGcode.END_GCODE,
                    self.get_gcode_extruder_relative())
            else:
                self.snapshot_gcode.append(
                    SnapshotGcode.END_GCODE,
                    self.get_gcode_extruder_absolute())
            self.is_extruder_relative_current = is_extruder_relative_return

    # Note that this command may alter the end_command's feedrate if it exists in order to reduce the number of gcodes
    # sent
    def return_to_original_feedrate(self):
        feedrate_set_in_end_command = (
            self.snapshot_plan.end_command is not None and
            "F" in self.snapshot_plan.end_command.parameters
        )
        f_return = self.snapshot_plan.initial_position.f
        if self.snapshot_plan.return_position is not None:
            f_return = self.snapshot_plan.return_position.f

        if not feedrate_set_in_end_command and f_return != self.f_current:
            # see if we can alter the end_command feedrate
            if self.snapshot_plan.end_command is not None and self.snapshot_plan.end_command.cmd in ["G0", "G1"]:
                self.snapshot_plan.end_command.parameters["F"] = f_return
                self.snapshot_plan.end_command.update_gcode_string()
            else:
                # we can't count on the end gcode to set f, set it here
                self.snapshot_gcode.append(
                    SnapshotGcode.END_GCODE,
                    self.get_gcode_feedrate(f_return))

    ###########################
    # Functions to send start and end commmand gcode
    ###########################
    def send_start_command(self, gcode_type=SnapshotGcode.INITIALIZATION_GCODE):
        # If we are returning, add the final command to the end gcode
        if self.snapshot_plan.start_command is not None:
            self.snapshot_gcode.append(
                gcode_type,
                self.snapshot_plan.start_command.gcode)

    def send_end_command(self, gcode_type=SnapshotGcode.END_GCODE):
        # If we are returning, add the final command to the end gcode
        if self.snapshot_plan.end_command is not None:
            self.snapshot_gcode.append(
                gcode_type,
                self.snapshot_plan.end_command.gcode)

    @staticmethod
    def get_triggered_type(trigger):
        if trigger is None:
            triggered_type = Triggers.TRIGGER_TYPE_DEFAULT
        else:
            triggered_type = trigger.triggered_type(0)
            if triggered_type is None:
                triggered_type = trigger.triggered_type(1)

        return triggered_type
    ###########################
    # Create a snapshot plan for real-time triggers
    ###########################

    def create_snapshot_plan(self, position, trigger):
        snapshot_plan = SnapshotPlan()

        # the parsed command has not been sent, but record it
        snapshot_plan.triggering_command = position.current_pos.parsed_command
        parsed_command_position = position.current_pos
        current_position = position.previous_pos
        # create the start and end gcode, which would include any split gcode (position restriction intersection)
        # or any saved command that needs to be appended

        # Flag to indicate that we should make sure the final feedrate = self.f_return
        # by default we want to change the feedrate if FCurrent != FOriginal
        if trigger is None:
            triggered_type = Triggers.TRIGGER_TYPE_DEFAULT
        else:
            triggered_type = trigger.triggered_type(0)
            if triggered_type is None:
                triggered_type = trigger.triggered_type(1)

        # handle the trigger types
        if triggered_type == Triggers.TRIGGER_TYPE_DEFAULT:
            snapshot_position = self.get_snapshot_position(current_position.x, current_position.y)
            snapshot_plan.start_command = None
            snapshot_plan.initial_position = current_position
            travel_step = SnapshotPlanStep(SnapshotPlan.TRAVEL_ACTION, x=snapshot_position["x"], y=snapshot_position["y"])
            snapshot_step = SnapshotPlanStep(SnapshotPlan.SNAPSHOT_ACTION)
            snapshot_plan.steps.append(travel_step)
            snapshot_plan.steps.append(snapshot_step)
            snapshot_plan.return_position = current_position
            snapshot_plan.end_command = snapshot_plan.triggering_command
            if parsed_command_position.is_travel_only:
                logger.info("The triggering command is travel only, skipping return command generation")
                snapshot_plan.return_position = None
        elif triggered_type == Triggers.TRIGGER_TYPE_IN_PATH:
            # see if the snapshot command is a g1 or g0
            if snapshot_plan.triggering_command.cmd:
                if snapshot_plan.triggering_command.cmd not in ["G0", "G1"]:
                    # if this isn't a g0 or g1, I don't know what's up!
                    return None
            gcode_1, gcode_2 = self.split_extrusion_gcode_at_point(
                snapshot_plan.triggering_command, current_position, parsed_command_position, parsed_command_position.in_path_position)
            snapshot_plan.start_command = gcode_1
            # calculate the initial position
            position.update(gcode_1)
            snapshot_plan.initial_position = position.current_pos
            # undo the update to the position processor
            position.undo_update()
            snapshot_position = self.get_snapshot_position(
                snapshot_plan.initial_position.x, snapshot_plan.initial_position.y)
            travel_step = SnapshotPlanStep(SnapshotPlan.TRAVEL_ACTION, x=snapshot_position["x"],
                                           y=snapshot_position["y"])
            snapshot_step = SnapshotPlanStep(SnapshotPlan.SNAPSHOT_ACTION)
            snapshot_plan.steps.append(travel_step)
            snapshot_plan.steps.append(snapshot_step)
            snapshot_plan.return_position = position.current_pos
            snapshot_plan.end_command = gcode_2
        else:
            return None

        return snapshot_plan

    def split_extrusion_gcode_at_point(self, triggering_command, start_position, end_position, intersection):
        # get the coordinates necessary to split one gcode into 2 at an intersection point
        # start offset coordinates
        start_x_offset = start_position.offset_x()
        start_y_offset = start_position.offset_y()
        start_e_offset = start_position.offset_e()
        # intersection offset coordinates
        intersection_x_offset = intersection["x"] - start_position.x_offset
        intersection_y_offset = intersection["y"] - start_position.y_offset
        # end offset coordinates
        end_x_offset = end_position.offset_x()
        end_y_offset = end_position.offset_y()
        end_e_offset = end_position.offset_e()
        # the feedrate won't change, but record it to make this obvious
        feedrate = end_position.f()

        # get the extrusion length
        extrusion_length = end_e_offset - start_e_offset

        # calculate the distance from x/y previous to the intersection
        distance_to_intersection = math.sqrt(
            math.pow(start_x_offset - intersection_x_offset, 2) +
            math.pow(start_y_offset - intersection_y_offset, 2)
        )
        # calculate the length of the lin x,y to previous_x, previous_y
        total_distance = math.sqrt(
            math.pow(start_x_offset - end_x_offset, 2) +
            math.pow(start_y_offset - end_y_offset, 2)
        )

        first_extrusion_length = (distance_to_intersection / total_distance) * extrusion_length
        e1_offset = start_e_offset + first_extrusion_length
        e2_offset = end_e_offset - first_extrusion_length

        # create the start and end gcode x and y in relative or offset x coordinates
        if start_position.is_relative_current:
            gcode1_x = intersection_x_offset - start_x_offset
            gcode1_y = intersection_y_offset - start_y_offset
            gcode2_x = end_x_offset - intersection_x_offset
            gcode2_y = end_y_offset - intersection_y_offset
        else:
            gcode1_x = intersection_x_offset
            gcode1_y = intersection_y_offset
            gcode2_x = end_x_offset
            gcode2_y = end_y_offset

        # create the start and end gcode e value in relative or absolute
        if start_position.is_extruder_relative_current:
            gcode1_e = e1_offset - start_e_offset
            gcode2_e = end_e_offset - e1_offset
        else:
            gcode1_e = e1_offset
            gcode2_e = e2_offset


        # create the gcodes
        triggering_command_1_parameters = {}
        if gcode1_x is not None:
            triggering_command_1_parameters["X"] = gcode1_x
        if gcode1_y is not None:
            triggering_command_1_parameters["Y"] = gcode1_y
        if gcode1_e is not None:
            triggering_command_1_parameters["E"] = gcode1_e
        triggering_command_1_parameters["F"] = feedrate
        triggering_command_1 = ParsedCommand(triggering_command.cmd, triggering_command_1_parameters, "")
        triggering_command_1.update_gcode_string()

        triggering_command_2_parameters = {}
        if gcode2_x is not None:
            triggering_command_2_parameters["X"] = gcode2_x
        if gcode2_y is not None:
            triggering_command_2_parameters["Y"] = gcode2_y
        if gcode2_e is not None:
            triggering_command_2_parameters["E"] = gcode2_e
        triggering_command_2_parameters["F"] = feedrate
        triggering_command_2 = ParsedCommand(triggering_command.cmd, triggering_command_2_parameters, "")
        triggering_command_2.update_gcode_string()

        return triggering_command_1, triggering_command_2

    def create_gcode_for_snapshot_plan(self, snapshot_plan, g90_influences_extruder, options):

        if not self.initialize_for_snapshot_plan_processing(
            snapshot_plan, g90_influences_extruder, options
        ):
            return None

        if not self.has_snapshot_position_errors:
            # Todo:  it's possible that the current command is a detract.  If it is we eventually will want to prevent
            # create the start command if it exists
            self.send_start_command()
            # retract if necessary
            self.retract()
            # lift if necessary
            self.lift_z()

            has_taken_snapshot = False
            assert(isinstance(snapshot_plan, SnapshotPlan))
            for step in snapshot_plan.steps:
                assert(isinstance(step, SnapshotPlanStep))
                if step.action == SnapshotPlan.TRAVEL_ACTION:
                    self.add_travel_action(step)
                if step.action == SnapshotPlan.SNAPSHOT_ACTION:
                    self.add_snapshot_action()

            # Create Return Gcode
            self.return_to_original_position()

            # If we zhopped in the beginning, lower z
            self.delift_z()

            # deretract if necessary
            self.deretract()

            # reset the coordinate systems for the extruder and axis
            self.return_to_original_coordinate_systems()

            self.return_to_original_feedrate()

            self.send_end_command()

        # print out log messages
        logger.info(
            "Snapshot Gcode - snapshot_commandIndex:%s, EndIndex:%s",
            self.snapshot_gcode.snapshot_index(),
            self.snapshot_gcode.end_index()
        )
        for gcode in self.snapshot_gcode.snapshot_gcode():
            logger.info("    %s", gcode)

        return self.snapshot_gcode

    @staticmethod
    def get_g_command(cmd, x, y, z, e, f):
        return "{0}{1}{2}{3}{4}{5}".format(
            cmd,
            "" if x is None else " X{0:.3f}".format(x),
            "" if y is None else " Y{0:.3f}".format(y),
            "" if z is None else " Z{0:.3f}".format(z),
            "" if e is None else " E{0:.5f}".format(e),
            "" if f is None else " F{0:.3f}".format(f)
        )

    @staticmethod
    def get_gcode_extruder_relative():
        return "M83"

    @staticmethod
    def get_gcode_extruder_absolute():
        return "M82"

    @staticmethod
    def get_gcode_axes_absolute():
        return "G90"

    @staticmethod
    def get_gcode_axes_relative():
        return "G91"

    @staticmethod
    def get_gcode_delay(delay):
        return "G4 P{0:d}".format(delay)

    @staticmethod
    def get_gcode_travel(x, y, f=None):
        return "G1 X{0:.3f} Y{1:.3f}{2}".format(
            x,
            y,
            "" if f is None else " F{0:.3f}".format(f)
        )

    @staticmethod
    def get_gcode_z_lift(distance, f=None):
        return "G1 Z{0:.3f}{1}".format(
            distance,
            "" if f is None else " F{0:.3f}".format(f)
        )

    @staticmethod
    def get_gcode_retract(distance, f=None):
        return "G1 E{0:.5f}{1}".format(
            distance,
            "" if f is None else " F{0:.3f}".format(f)
        )

    @staticmethod
    def get_gcode_reset_line(line_number):
        return "M110 N{0:d}".format(line_number)

    @staticmethod
    def get_gcode_wait_until_finished():
        return "M400"

    @staticmethod
    def get_gcode_current_position():
        return "M114"

    @staticmethod
    def get_gcode_feedrate(f):
        return "G1 F{0:.3f}".format(f)
