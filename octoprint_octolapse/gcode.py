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

from octoprint_octolapse.gcode_parser import ParsedCommand
from octoprint_octolapse.position import Pos, Position
from octoprint_octolapse.settings import *
from octoprint_octolapse.trigger import Triggers
import fastgcodeparser
import octoprint_octolapse.stabilization_preprocessing as Preprocessing
class SnapshotGcode(object):
    INITIALIZATION_GCODE = 'initialization-gcode'
    START_GCODE = 'start-gcode'
    SNAPSHOT_COMMANDS = 'snapshot-commands'
    RETURN_COMMANDS = 'return-commands'
    END_GCODE = 'end-gcode'

    def __init__(self):

        self.InitializationGcode = []  # commands executed here are not involved in timing calculations
        self.StartGcode = []
        self.SnapshotCommands = []
        self.ReturnCommands = []
        self.EndGcode = []
        self.X = None
        self.ReturnX = None
        self.Y = None
        self.ReturnY = None
        self.Z = None
        self.ReturnZ = None
        self.SnapshotIndex = -1

    def snapshot_gcode(self):
        return self.InitializationGcode + self.StartGcode + self.SnapshotCommands + self.ReturnCommands + self.EndGcode

    def append(self, command_type, command):
        if command_type == self.INITIALIZATION_GCODE:
            self.InitializationGcode.append(command)
        elif command_type == self.START_GCODE:
            self.StartGcode.append(command)
        elif command_type == self.SNAPSHOT_COMMANDS:
            self.SnapshotCommands.append(command)
        elif command_type == self.RETURN_COMMANDS:
            self.ReturnCommands.append(command)
        elif command_type == self.END_GCODE:
            self.EndGcode.append(command)

    def end_index(self):
        return len(self.InitializationGcode) + len(self.StartGcode) + len(self.SnapshotCommands) + len(self.ReturnCommands) + len(self.EndGcode) - 1

    def snapshot_index(self):
        return len(self.InitializationGcode) + len(self.StartGcode) + len(self.SnapshotCommands) - 1


class SnapshotGcodeGenerator(object):
    CurrentXPathIndex = 0
    CurrentYPathIndex = 0

    def __init__(self, octolapse_settings, octoprint_printer_profile):
        self.Settings = octolapse_settings  # type: OctolapseSettings
        self.StabilizationPaths = self.Settings.profiles.current_stabilization().get_stabilization_paths()
        self.Snapshot = self.Settings.profiles.current_snapshot()
        self.Printer = self.Settings.profiles.current_printer()
        self.snapshot_command = self.Printer.snapshot_command
        self.OctoprintPrinterProfile = octoprint_printer_profile
        self.BoundingBox = utility.get_bounding_box(
            self.Printer, octoprint_printer_profile)
        self.HasSnapshotPositionErrors = False
        self.SnapshotPositionErrors = ""
        self.gcode_generation_settings = self.Printer.get_current_state_detection_settings()
        assert(isinstance(self.gcode_generation_settings, OctolapseGcodeSettings))
        # this will be determined by the supplied position object
        self.g90_g91_affect_extruder = None
        # variables for gcode generation
        # return (original) values
        self.x_return = None
        self.y_return = None
        self.z_return = None
        self.f_return = None
        self.is_relative_return = None
        self.is_extruder_relative_return = None
        self.is_metric_return = None
        # current valuse
        self.x_current = None
        self.y_current = None
        self.f_current = None
        self.is_relative_current = None
        self.is_extruder_relative_current = None
        self.retracted_length_current = None
        # calculated values
        self.distance_to_lift = None
        self.length_to_retract = None
        # stored gcode
        self.parsed_gcode = None
        # will hold the position and extruder state of the command that triggered the snapshot
        self.triggering_command_position = None
        #Snapshot Gcode Variable
        self.snapshot_gcode = None
        # state flags
        self.return_when_complete = None
        self.retracted_by_start_gcode = None
        self.zhopped_by_start_gcode = None

        # misc variables used for logging info
        self.last_extrusion_height = None

    def initialize_for_real_time_processing(self, position, trigger, parsed_command):
        # reset any errors
        self.HasSnapshotPositionErrors = False
        self.SnapshotPositionErrors = ""

        # get the triggering command and extruder position by
        # undo the most recent position update since we haven't yet executed the most recent gcode command
        # Capture and undo the last position update, we're not going to be using it!
        self.triggering_command_position = position.undo_update()
        assert (isinstance(self.triggering_command_position, Pos))
        assert (isinstance(position, Position))

        if len(position.Positions) < 1:
            return None

        # does G90/G91 influence the extruder
        self.g90_influences_extruder = position.G90InfluencesExtruder
        # get the command we will be probably sending at the end of the process
        if not utility.is_snapshot_command(parsed_command.gcode, self.snapshot_command):
            self.parsed_gcode = parsed_command.gcode
        else:
            self.parsed_gcode = None
        # record the return position, which is the current position
        self.x_return = position.current_pos.X
        self.y_return = position.current_pos.Y
        self.z_return = position.current_pos.Z
        self.f_return = position.current_pos.F
        self.is_relative_return = position.current_pos.IsRelative
        self.is_extruder_relative_return = position.current_pos.IsExtruderRelative
        self.is_metric_return = position.current_pos.IsMetric

        # keep track of the current position while creating gcode below.
        # these values will be updated and used to make sure we don't
        # issue gcodes that don't move the axis, which would slow down
        # the snapshot
        self.x_current = self.x_return
        self.y_current = self.y_return
        self.f_current = self.f_return
        self.is_relative_current = self.is_relative_return
        self.is_extruder_relative_current = self.is_extruder_relative_return
        self.retracted_length_current = 0
        self.distance_to_lift = position.distance_to_zlift()
        self.length_to_retract = position.length_to_retract()

        # State flags for triggering various functionality
        self.return_when_complete = True  # we only return if the final command is not travel only in XY plane
        self.retracted_by_start_gcode = False
        self.zhopped_by_start_gcode = False

        # create our gcode object
        self.snapshot_gcode = SnapshotGcode()

        return not self.has_initialization_errors()

    def initialize_for_snapshot_plan_processing(self, snapshot_plan, parsed_command, g90_influences_extruder):
        assert(isinstance(snapshot_plan, Preprocessing.SnapshotPlan))
        # reset any errors
        self.HasSnapshotPositionErrors = False
        self.SnapshotPositionErrors = ""

        # get the triggering command and extruder position by
        # undo the most recent position update since we haven't yet executed the most recent gcode command
        # Capture and undo the last position update, we're not going to be using it!

        # does G90/G91 influence the extruder
        self.g90_influences_extruder = g90_influences_extruder
        self.parsed_gcode = parsed_command.gcode

        # record the return position, which is the current position
        self.x_return = snapshot_plan.x
        self.y_return = snapshot_plan.y
        self.z_return = snapshot_plan.z
        self.f_return = snapshot_plan.speed
        self.is_relative_return = snapshot_plan.is_xyz_relative
        self.is_extruder_relative_return = snapshot_plan.is_e_relative
        self.is_metric_return = snapshot_plan.is_metric

        # keep track of the current position while creating gcode below.
        # these values will be updated and used to make sure we don't
        # issue gcodes that don't move the axis, which would slow down
        # the snapshot
        self.x_current = self.x_return
        self.y_current = self.y_return
        self.f_current = self.f_return
        self.is_relative_current = self.is_relative_return
        self.is_extruder_relative_current = self.is_extruder_relative_return
        self.retracted_length_current = 0
        self.distance_to_lift = snapshot_plan.lift_amount
        self.length_to_retract = snapshot_plan.retract_amount

        # State flags for triggering various functionality
        self.return_when_complete = True  # we only return if the final command is not travel only in XY plane
        self.retracted_by_start_gcode = False
        self.zhopped_by_start_gcode = False

        # create our gcode object
        self.snapshot_gcode = SnapshotGcode()

        return not self.has_initialization_errors()

    def has_initialization_errors(self):
        # check X Y and Z return
        if self.x_return is None or self.y_return is None or self.z_return is None:
            self.HasSnapshotPositionErrors = True
            message = "Cannot create GCode when x,y,or z is None.  Values: x:{0} y:{1} z:{2}".format(
                self.x_return, self.y_return, self.z_return)
            self.SnapshotPositionErrors = message
            self.Settings.Logger.log_error(
                "gcode.py - CreateSnapshotGcode - {0}".format(message))
            return True

        # check the units, only metric works.
        if self.is_metric_return is None or not self.is_metric_return:
            self.Settings.Logger.log_error(
                "No unit of measurement has been set and the current"
                " printer profile is set to require explicit G20/G21, or the unit of measurement is inches. "
            )
            return True

        return False

    def get_snapshot_position(self, x_pos, y_pos):
        x_path = self.StabilizationPaths["X"]
        x_path.CurrentPosition = x_pos
        y_path = self.StabilizationPaths["Y"]
        y_path.CurrentPosition = y_pos

        coordinates = dict(X=self.get_snapshot_coordinate(x_path),
                           Y=self.get_snapshot_coordinate(y_path))

        if not utility.is_in_bounds(self.BoundingBox, coordinates["X"], None, None):

            message = "The snapshot X position ({0}) is out of bounds!".format(
                coordinates["X"])
            self.HasSnapshotPositionErrors = True
            self.Settings.Logger.log_error(
                "gcode.py - GetSnapshotPosition - {0}".format(message))
            if self.Printer.abort_out_of_bounds:
                coordinates["X"] = None
            else:
                coordinates["X"] = utility.get_closest_in_bounds_position(
                    self.BoundingBox, x=coordinates["X"])["X"]
                message += "  Using nearest in-bound position ({0}).".format(
                    coordinates["X"])
            self.SnapshotPositionErrors += message
        if not utility.is_in_bounds(self.BoundingBox, None, coordinates["Y"], None):
            message = "The snapshot Y position ({0}) is out of bounds!".format(
                coordinates["Y"])
            self.HasSnapshotPositionErrors = True
            self.Settings.Logger.log_error(
                "gcode.py - GetSnapshotPosition - {0}".format(message))
            if self.Printer.abort_out_of_bounds:
                coordinates["Y"] = None
            else:
                coordinates["Y"] = utility.get_closest_in_bounds_position(
                    self.BoundingBox, y=coordinates["Y"])["Y"]
                message += "  Using nearest in-bound position ({0}).".format(
                    coordinates["Y"])
            if len(self.SnapshotPositionErrors) > 0:
                self.SnapshotPositionErrors += "  "
            self.SnapshotPositionErrors += message
        return coordinates

    def get_snapshot_coordinate(self, path):
        if path.Type == 'disabled':
            return path.CurrentPosition

        # Get the current coordinate from the path
        coord = path.Path[path.Index]
        # move our index forward or backward
        path.Index += path.Increment

        if path.Index >= len(path.Path):
            if path.Loop:
                if path.InvertLoop:
                    if len(path.Path) > 1:
                        path.Index = len(path.Path) - 2
                    else:
                        path.Index = 0
                    path.Increment = -1
                else:
                    path.Index = 0
            else:
                path.Index = len(path.Path) - 1
        elif path.Index < 0:
            if path.Loop:
                if path.InvertLoop:
                    if len(path.Path) > 1:
                        path.Index = 1
                    else:
                        path.Index = 0
                    path.Increment = 1
                else:
                    path.Index = len(path.Path) - 1
            else:
                path.Index = 0

        if path.CoordinateSystem == "absolute":
            return coord
        elif path.CoordinateSystem == "bed_relative":
            if self.OctoprintPrinterProfile["volume"]["formFactor"] == "circle":
                raise ValueError(
                    'Cannot calculate relative coordinates within a circular bed (yet...), sorry')
            return self.get_bed_relative_coordinate(path.Axis, coord)

    def get_bed_relative_coordinate(self, axis, coord):
        rel_coordinate = None
        if axis == "X":
            rel_coordinate = self.get_bed_relative_x(coord)
        elif axis == "Y":
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

    def retract(self):
        if self.gcode_generation_settings.retract_before_move and self.length_to_retract > 0:
            self.set_e_to_relative(SnapshotGcode.START_GCODE)
            self.snapshot_gcode.append(
                SnapshotGcode.START_GCODE,
                self.get_gcode_retract(
                    self.length_to_retract,
                    self.get_altered_feedrate(self.gcode_generation_settings.retraction_speed)
                )
            )
            self.retracted_by_start_gcode = True

    def deretract(self):

        if self.retracted_by_start_gcode:
            self.set_e_to_relative(SnapshotGcode.END_GCODE)
            self.snapshot_gcode.append(
                SnapshotGcode.END_GCODE,
                self.get_gcode_deretract(
                    self.length_to_retract,
                    self.get_altered_feedrate(self.gcode_generation_settings.deretraction_speed)
                )
            )

    def add_snapshot_action(self):
        # Move to Snapshot Position
        self.snapshot_gcode.append(
            SnapshotGcode.SNAPSHOT_COMMANDS,
            self.Printer.snapshot_command
        )

    def add_travel_action(self, step):
        assert(isinstance(step, Preprocessing.SnapshotPlanStep))
        # Move to Snapshot Position
        self.set_xyz_to_absolute(SnapshotGcode.SNAPSHOT_COMMANDS)
        self.snapshot_gcode.append(
            SnapshotGcode.SNAPSHOT_COMMANDS,
            self.get_gcode_travel(
                step.x,
                step.y,
                self.get_altered_feedrate(step.f)
            )
        )
        self.x_current = step.x
        self.y_current = step.y

    def can_zhop(self):
        return (
            utility.is_in_bounds(self.BoundingBox, None, None, self.z_return + self.distance_to_lift)
        )

    def lift_z(self):
        # if we can ZHop, do
        if (
            self.can_zhop() and
            self.distance_to_lift > 0 and
            self.gcode_generation_settings.retract_before_move and
            self.gcode_generation_settings.lift_when_retracted
        ):
            self.set_xyz_to_relative(SnapshotGcode.START_GCODE)
            # append to snapshot gcode
            self.snapshot_gcode.append(
                SnapshotGcode.START_GCODE,
                self.get_gcode_z_lift_relative(
                    self.distance_to_lift,
                    self.get_altered_feedrate(self.gcode_generation_settings.z_lift_speed)
                )
            )
            self.zhopped_by_start_gcode = True

    def delift_z(self):
        if self.zhopped_by_start_gcode:
            self.set_xyz_to_relative(SnapshotGcode.END_GCODE)
            self.snapshot_gcode.append(
                SnapshotGcode.END_GCODE,
                self.get_gocde_z_lower_relative(
                    self.distance_to_lift,
                    self.get_altered_feedrate(self.gcode_generation_settings.z_lift_speed)
                )
            )

    def go_to_snapshot_position(self):

        if self.snapshot_gcode.X is None or self.snapshot_gcode.Y is None:
            # either x or y is out of bounds.
            return None
        # make sure we aren't in the proper position already!
        if (
            self.snapshot_gcode.X != self.x_current or
            self.snapshot_gcode.Y != self.y_current
        ):
            self.set_xyz_to_absolute(SnapshotGcode.SNAPSHOT_COMMANDS)

            # Move to Snapshot Position
            self.snapshot_gcode.append(
                SnapshotGcode.SNAPSHOT_COMMANDS,
                self.get_gcode_travel(
                    self.snapshot_gcode.X,
                    self.snapshot_gcode.Y,
                    self.get_altered_feedrate(self.gcode_generation_settings.x_y_travel_speed)
                )
            )
            self.x_current = self.snapshot_gcode.X
            self.y_current = self.snapshot_gcode.Y

    def return_to_original_coordinate_systems(self):
        if self.is_relative_return != self.is_relative_current:
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
            self.is_relative_current = self.is_relative_return

        if self.is_extruder_relative_return != self.is_extruder_relative_current:
            if self.is_extruder_relative_return:
                self.snapshot_gcode.append(
                    SnapshotGcode.END_GCODE,
                    self.get_gcode_extruder_relative())
            else:
                self.snapshot_gcode.append(
                    SnapshotGcode.END_GCODE,
                    self.get_gcode_extruder_absolute())

    def return_to_original_feedrate(self, parsed_command=None):
        # Make sure we return to the original feedrate
        if (
            not self.return_when_complete
            or (
                (parsed_command is None or "F" not in parsed_command.parameters) and
                (self.f_return is not None and self.f_return != self.f_current)
            )
        ):
            # we can't count on the end gcode to set f, set it here
            self.snapshot_gcode.append(
                SnapshotGcode.END_GCODE,
                self.get_gcode_feedrate(self.f_return))

    def return_to_original_position(self):
        if self.return_when_complete:
            # Only return to the previous coordinates if we need to (which will be most cases,
            # except when the triggering command is a travel only (moves both X and Y, but not Z)
            # record our previous position for posterity
            self.snapshot_gcode.ReturnX = self.x_return
            self.snapshot_gcode.ReturnY = self.y_return
            self.snapshot_gcode.ReturnZ = self.z_return
            if(
                self.x_return is not None and self.y_return is not None
                and (self.x_return != self.x_current or self.y_return != self.y_current)
            ):
                # Move back to previous position - make sure we're in absolute mode for this
                self.set_xyz_to_absolute(SnapshotGcode.RETURN_COMMANDS)

                self.snapshot_gcode.append(
                    SnapshotGcode.RETURN_COMMANDS,
                    self.get_gcode_travel(
                        self.x_return,
                        self.y_return,
                        self.get_altered_feedrate(self.gcode_generation_settings.x_y_travel_speed)
                    )
                )
                self.x_current = self.x_return
                self.y_current = self.y_return
        else:
            # record the final position
            self.snapshot_gcode.ReturnX = self.triggering_command_position.X
            self.snapshot_gcode.ReturnY = self.triggering_command_position.Y
            # see about Z, we may need to suppress our
            self.snapshot_gcode.ReturnZ = self.triggering_command_position.Z
            self.Settings.Logger.log_snapshot_gcode(
                "Skipping return position, traveling to the triggering command position: X={0}, y={1}".format(
                    self.triggering_command_position.X, self.triggering_command_position.Y
                )
            )
            if (
                self.triggering_command_position.X is not None and self.triggering_command_position.Y is not None
                and
                (
                    self.triggering_command_position.X != self.x_current
                    or self.triggering_command_position.Y != self.y_current
                )
            ):
                # Move back to previous position - make sure we're in absolute mode for this
                # note we're adding this to the end-gcode to make sure it doesn't mess
                # with our time calculation
                self.set_xyz_to_absolute(SnapshotGcode.END_GCODE)

                self.snapshot_gcode.append(
                    SnapshotGcode.END_GCODE,
                    self.get_gcode_travel(
                        self.triggering_command_position.X,
                        self.triggering_command_position.Y,
                        self.get_altered_feedrate(self.gcode_generation_settings.x_y_travel_speed)
                    )
                )
                self.x_current = self.triggering_command_position.X
                self.y_current = self.triggering_command_position.Y

    def send_parsed_command(self, gcode_type=SnapshotGcode.END_GCODE):
        # If we are returning, add the final command to the end gcode
        if self.parsed_gcode is not None:
            self.snapshot_gcode.append(
                gcode_type,
                self.parsed_gcode)

    def create_snapshot_gcode(
        self, position, trigger, parsed_command
    ):
        # initialize returns true on success.  If false, we can't continue
        if not self.initialize_for_real_time_processing(position, trigger, parsed_command):
            return None

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
            if self.triggering_command_position.IsTravelOnly:
                self.Settings.Logger.log_snapshot_gcode(
                    "The triggering command is travel only, skipping return command generation"
                )
                # No need to perform the return step!  We'll go right the the next travel location after
                # taking the snapshot!
                self.return_when_complete = False
        elif triggered_type == Triggers.TRIGGER_TYPE_IN_PATH:
            # see if the snapshot command is a g1 or g0
            if parsed_command.cmd:
                if parsed_command.cmd not in ["G0", "G1"]:
                    # if this isn't a g0 or g1, I don't know what's up!
                    return None
            self.split_extrusion_gcode_at_point(parsed_command, position, trigger)
        else:
            return None


        # get the X and Y coordinates of the snapshot
        snapshot_position = self.get_snapshot_position(self.x_return, self.y_return)
        self.snapshot_gcode.X = snapshot_position["X"]
        self.snapshot_gcode.Y = snapshot_position["Y"]

        if not self.HasSnapshotPositionErrors:
            # retract if necessary
            self.retract()

            # lift if necessary
            self.lift_z()

            # Create code to move from the current extruder position to the snapshot position
            self.go_to_snapshot_position()

            # Create Return Gcode
            self.return_to_original_position()

            # If we zhopped in the beginning, lower z
            self.delift_z()

            # deretract if necessary
            self.deretract()

            # reset the coordinate systems for the extruder and axis
            self.return_to_original_coordinate_systems()

            self.return_to_original_feedrate(parsed_command)

        # send the final command if necessray
        if self.return_when_complete:
            self.send_parsed_command(SnapshotGcode.END_GCODE)

        # print out log messages
        self.Settings.Logger.log_snapshot_gcode(
            "Snapshot Gcode - SnapshotCommandIndex:{0}, EndIndex:{1}, Triggering Command:{2}".format(
                self.snapshot_gcode.snapshot_index(),
                self.snapshot_gcode.end_index(),
                parsed_command.gcode
            )
        )
        for gcode in self.snapshot_gcode.snapshot_gcode():
            self.Settings.Logger.log_snapshot_gcode("    {0}".format(gcode))

        return self.snapshot_gcode

    def split_extrusion_gcode_at_point(self, parsed_command, position, trigger):
        # get the data necessary to split the command up
        in_path_position = trigger.in_path_position(0)
        intersection = in_path_position["intersection"]
        path_ratio_1 = in_path_position["path_ratio_1"]
        path_ratio_2 = in_path_position["path_ratio_2"]

        _x1 = intersection[0]  # will be in absolute coordinates
        _y1 = intersection[1]  # will be in absolute coordinates
        _x2 = parsed_command.parameters[
            "X"] if "X" in parsed_command.parameters else None  # should remain in the original coordinate system
        _y2 = parsed_command.parameters[
            "Y"] if "Y" in parsed_command.parameters else None  # should remain in the original coordinate system
        _z = parsed_command.parameters[
            "Z"] if "Z" in parsed_command.parameters else None  # should remain in the original coordinate system
        _e = parsed_command.parameters["E"] if "E" in parsed_command.parameters else None
        _f = parsed_command.parameters["F"] if "F" in parsed_command.parameters else None
        # if the command has an F parameter, update FCurrent

        if _f:
            _f = float(_f)
            if self.f_current != _f:
                # if we have a new speed here, set it as the original
                self.f_current = _f
                self.f_return = _f

        _e1 = None
        _e2 = None
        # calculate e
        if _e:
            _e = float(_e)
            if not self.is_extruder_relative_current:
                _extrusion_amount = position.e_relative_current(_e)
                # set e1 absolute
                _e1 = _e - _extrusion_amount * path_ratio_2
                _e2 = _e
            else:
                _e1 = _e * path_ratio_1
                _e2 = _e * path_ratio_2

        # Convert X1 and y1 to relative
        if self.is_relative_current:
            if _x1:
                _x1 = position.x_relative_to_current(_x1)
            if _y1:
                _y1 = position.y_relative_to_current(_y1)

        if _x2:
            _x2 = float(_x2)
        if _y2:
            _y2 = float(_y2)

        if _z:
            _z = float(_z)
        if _f:
            _f = float(_f)

        gcode1 = self.get_g_command(parsed_command.cmd, _x1, _y1, _z, _e1, _f)
        self.x_current = _x1
        self.y_current = _y1
        # create the second command
        gcode2 = self.get_g_command(parsed_command.cmd, _x2, _y2, _z, _e2, _f)

        # append both commands
        self.snapshot_gcode.append(SnapshotGcode.INITIALIZATION_GCODE, gcode1)

        self.parsed_gcode = gcode2
        # set the return x and return y to the intersection point
        # must be in absolute coordinates
        self.x_return = intersection[0]  # will be in absolute coordinates
        self.y_return = intersection[1]  # will be in absolute coordinates

        # recalculate z_lift and retract distance since we have moved a bit
        fast_cmd = fastgcodeparser.ParseGcode(gcode1)
        command_1 = ParsedCommand(fast_cmd[0], fast_cmd[1], gcode1)

        position.update(command_1)
        # set self.z_return to the new z position
        # must be absolute
        self.z_return = position.z()
        self.distance_to_lift = position.distance_to_zlift()
        self.length_to_retract = position.length_to_retract()


        # undo the update since the position has not changed, only the zlift value and potentially the
        # retraction length
        position.undo_update()

    def create_gcode_for_snapshot_plan(self, snapshot_plan, parsed_command, g90_influences_extruder):
        if not self.initialize_for_snapshot_plan_processing(snapshot_plan, parsed_command, g90_influences_extruder):
            return None

        self.snapshot_gcode.X = snapshot_plan.x
        self.snapshot_gcode.Y = snapshot_plan.y

        if not self.HasSnapshotPositionErrors:
            if snapshot_plan.send_parsed_command == "first":
                self.send_parsed_command(SnapshotGcode.INITIALIZATION_GCODE)
            # retract if necessary
            self.retract()

            # lift if necessary
            self.lift_z()

            has_taken_snapshot = False
            assert(isinstance(snapshot_plan, Preprocessing.SnapshotPlan))
            for step in snapshot_plan.steps:
                assert(isinstance(step, Preprocessing.SnapshotPlanStep))
                if step.action == Preprocessing.TRAVEL_ACTION:
                    self.add_travel_action(step)
                if step.action == Preprocessing.SNAPSHOT_ACTION:
                    # todo: support multiple snapshots maybe? however, not today.
                    self.add_snapshot_action()

            # Create Return Gcode
            self.return_to_original_position()

            # If we zhopped in the beginning, lower z
            self.delift_z()

            # deretract if necessary
            self.deretract()

            # reset the coordinate systems for the extruder and axis
            self.return_to_original_coordinate_systems()

            final_command = None
            if snapshot_plan.send_parsed_command == "last":
                final_command = parsed_command
            self.return_to_original_feedrate(final_command)
            # end processing without errors

        # send the final command if necessary.  Note that we always try to send the final command, even on error.
        if snapshot_plan.send_parsed_command == "last":
            self.send_parsed_command(SnapshotGcode.END_GCODE)

        # print out log messages
        self.Settings.Logger.log_snapshot_gcode(
            "Snapshot Gcode - SnapshotCommandIndex:{0}, EndIndex:{1}, Triggering Command:{2}".format(
                self.snapshot_gcode.snapshot_index(),
                self.snapshot_gcode.end_index(),
                parsed_command.gcode
            )
        )
        for gcode in self.snapshot_gcode.snapshot_gcode():
            self.Settings.Logger.log_snapshot_gcode("    {0}".format(gcode))

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
    def get_gcode_z_lift_relative(distance, f=None):
        return "G1 Z{0:.3f}{1}".format(
            distance,
            "" if f is None else " F{0:.3f}".format(f)
        )

    @staticmethod
    def get_gocde_z_lower_relative(distance, f=None):
        return "G1 Z{0:.3f}{1}".format(
            -1.0 * distance,
            "" if f is None else " F{0:.3f}".format(f)
        )

    @staticmethod
    def get_gcode_retract(distance, f=None):
        return "G1 E{0:.5f}{1}".format(
            -1 * distance,
            "" if f is None else " F{0:.3f}".format(f)
        )

    @staticmethod
    def get_gcode_deretract(distance, f=None):
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
