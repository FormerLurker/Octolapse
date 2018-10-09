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

from octoprint_octolapse.gcode_parser import Commands
from octoprint_octolapse.position import Pos
from octoprint_octolapse.settings import *
from octoprint_octolapse.trigger import Triggers


class SnapshotGcode(object):
    CommandsDictionary = Commands()
    START_GCODE = 'start-gcode'
    SNAPSHOT_COMMANDS = 'snapshot-commands'
    RETURN_COMMANDS = 'return-commands'
    END_GCODE = 'end-gcode'

    def __init__(self):

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
        return self.StartGcode + self.SnapshotCommands + self.ReturnCommands + self.EndGcode

    def append(self, command_type, command):
        if command_type == self.START_GCODE:
            self.StartGcode.append(command)
        elif command_type == self.SNAPSHOT_COMMANDS:
            self.SnapshotCommands.append(command)
        elif command_type == self.RETURN_COMMANDS:
            self.ReturnCommands.append(command)
        elif command_type == self.END_GCODE:
            self.EndGcode.append(command)

    def end_index(self):
        return len(self.StartGcode) + len(self.SnapshotCommands) + len(self.ReturnCommands) + len(self.EndGcode) - 1

    def snapshot_index(self):
        return len(self.StartGcode) + len(self.SnapshotCommands) - 1


class SnapshotGcodeGenerator(object):
    CurrentXPathIndex = 0
    CurrentYPathIndex = 0

    def __init__(self, octolapse_settings, octoprint_printer_profile):
        self.Commands = Commands()
        self.Settings = octolapse_settings  # type: OctolapseSettings
        self.StabilizationPaths = self.Settings.current_stabilization().get_stabilization_paths()
        self.Snapshot = Snapshot(self.Settings.current_snapshot())
        self.Printer = Printer(self.Settings.current_printer())
        self.OctoprintPrinterProfile = octoprint_printer_profile
        self.BoundingBox = utility.get_bounding_box(
            self.Printer, octoprint_printer_profile)
        self.RetractedBySnapshotStartGcode = None
        self.ZhopBySnapshotStartGcode = None
        self.IsRelativeOriginal = None
        self.IsRelativeCurrent = None
        self.IsMetricOriginal = None
        self.IsMetricCurrent = None
        self.IsExtruderRelativeOriginal = None
        self.IsExtruderRelativeCurrent = None
        self.FOriginal = None
        self.FCurrent = None
        self.HasSnapshotPositionErrors = False
        self.SnapshotPositionErrors = ""
        self.ZLift = 0
        self.RetractedLength = 0
        self.AxisSpeedUnits = self.Printer.axis_speed_display_units
        self.ReturnWhenComplete = True
        if self.AxisSpeedUnits not in ["mm-min", "mm-sec"]:
            self.AxisSpeedUnits = "mm-min"

        self.RetractSpeed = self.Printer.get_speed_for_slicer_type(self.Printer.retract_speed, "retract_speed")
        self.DetractSpeed = self.Printer.get_speed_for_slicer_type(self.Printer.detract_speed, "detract_speed")
        self.TravelSpeed = self.Printer.get_speed_for_slicer_type(self.Printer.movement_speed, "movement_speed")
        self.ZHopSpeed = self.Printer.get_speed_for_slicer_type(self.Printer.z_hop_speed, "z_hop_speed")

    def reset(self):
        self.ReturnWhenComplete = True
        self.RetractedBySnapshotStartGcode = None
        self.ZhopBySnapshotStartGcode = None
        self.IsRelativeOriginal = None
        self.IsRelativeCurrent = None
        self.IsExtruderRelativeOriginal = None
        self.IsExtruderRelativeCurrent = None
        self.FOriginal = None
        self.FCurrent = None
        self.HasSnapshotPositionErrors = False
        self.SnapshotPositionErrors = ""
        self.ZLift = 0
        self.RetractedLength = 0

    def get_snapshot_position(self, x_pos, y_pos):
        x_path = self.StabilizationPaths["X"]
        x_path.CurrentPosition = x_pos
        y_path = self.StabilizationPaths["Y"]
        y_path.CurrentPosition = y_pos

        coordinates = dict(X=self.get_snapshot_coordinate(x_path),
                           Y=self.get_snapshot_coordinate(y_path))

        if not utility.is_in_bounds(self.BoundingBox, x=coordinates["X"]):

            message = "The snapshot X position ({0}) is out of bounds!".format(
                coordinates["X"])
            self.HasSnapshotPositionErrors = True
            self.Settings.current_debug_profile().log_error(
                "gcode.py - GetSnapshotPosition - {0}".format(message))
            if self.Printer.abort_out_of_bounds:
                coordinates["X"] = None
            else:
                coordinates["X"] = utility.get_closest_in_bounds_position(
                    self.BoundingBox, x=coordinates["X"])["X"]
                message += "  Using nearest in-bound position ({0}).".format(
                    coordinates["X"])
            self.SnapshotPositionErrors += message
        if not utility.is_in_bounds(self.BoundingBox, y=coordinates["Y"]):
            message = "The snapshot Y position ({0}) is out of bounds!".format(
                coordinates["Y"])
            self.HasSnapshotPositionErrors = True
            self.Settings.current_debug_profile().log_error(
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

    def create_snapshot_gcode(
        self, position, trigger, parsed_command
    ):
        # undo the most recent position update since we haven't yet executed the most recent gcode command
        # Capture and undo the last position update, we're not going to be using it!
        triggering_command_position, triggering_extruder_position = position.undo_update()

        assert (isinstance(triggering_command_position, Pos))

        current_position = position.get_position(0)
        if current_position is None:
            return None

        assert (isinstance(current_position, Pos))
        x_return = current_position.X
        y_return = current_position.Y
        z_return = current_position.Z
        f_return = current_position.F
        # e_return = position.e()

        is_relative = current_position.IsRelative
        is_extruder_relative = current_position.IsExtruderRelative
        is_metric = current_position.IsMetric

        z_lift = current_position.distance_to_zlift(position.ZHop)

        if z_lift is None:
            self.Settings.current_debug_profile().log_warning(
                "gcode.py - ZLift is none: Z:{0}, LastExtrusionHeight:{1}".format(
                    current_position.Z, current_position.LastExtrusionHeight))

        length_to_retract = position.Extruder.length_to_retract()
        final_command = parsed_command.gcode

        self.reset()
        if x_return is None or y_return is None or z_return is None:
            self.HasSnapshotPositionErrors = True
            message = "Cannot create GCode when x,y,or z is None.  Values: x:{0} y:{1} z:{2}".format(
                x_return, y_return, z_return)
            self.SnapshotPositionErrors = message
            self.Settings.current_debug_profile().log_error(
                "gcode.py - CreateSnapshotGcode - {0}".format(message))
            return None

        # Todo:  Clean this mess up (used to take separate params in the fn, now we take a position object)
        self.ReturnWhenComplete = True
        self.FOriginal = f_return
        self.FCurrent = f_return
        self.RetractedBySnapshotStartGcode = False
        self.RetractedLength = 0
        self.ZhopBySnapshotStartGcode = False
        self.ZLift = z_lift
        self.IsRelativeOriginal = is_relative
        self.IsRelativeCurrent = is_relative
        self.IsExtruderRelativeOriginal = is_extruder_relative
        self.IsExtruderRelativeCurrent = is_extruder_relative

        # check the units
        if is_metric is None or not is_metric:
            self.Settings.current_debug_profile().log_error(
                "No unit of measurement has been set and the current"
                " printer profile is set to require explicit G20/G21, or the unit of measurement is inches. "
            )
            return None

        # create our gcode object
        new_snapshot_gcode = SnapshotGcode()

        # create the start and end gcode, which would include any split gcode (position restriction intersection)
        # or any saved command that needs to be appended

        # Flag to indicate that we should make sure the final feedrate = self.FOriginal
        # by default we want to change the feedrate if FCurrent != FOriginal
        reset_feedrate_before_end_gcode = True
        if trigger is None:
            triggered_type = Triggers.TRIGGER_TYPE_DEFAULT
        else:
            triggered_type = trigger.triggered_type(0)
            if triggered_type is None:
                triggered_type = trigger.triggered_type(1)

        # handle the trigger types
        if triggered_type == Triggers.TRIGGER_TYPE_DEFAULT:
            if triggering_command_position.IsTravelOnly:
                self.Settings.current_debug_profile().log_snapshot_gcode(
                    "The triggering command is travel only, skipping return command generation"
                )
                # No need to perform the return step!  We'll go right the the next travel location after
                # taking the snapshot!
                self.ReturnWhenComplete = False
        elif triggered_type == Triggers.TRIGGER_TYPE_IN_PATH:
            # see if the snapshot command is a g1 or g0
            if parsed_command.cmd:
                if parsed_command.cmd not in ["G0", "G1"]:
                    # if this isn't a g0 or g1, I don't know what's up!
                    return None
                # get the data necessary to split the command up
                in_path_position = trigger.in_path_position(0)
                intersection = in_path_position["intersection"]
                path_ratio_1 = in_path_position["path_ratio_1"]
                path_ratio_2 = in_path_position["path_ratio_2"]

                _x1 = intersection[0]  # will be in absolute coordinates
                _y1 = intersection[1]  # will be in absolute coordinates
                _x2 = parsed_command.parameters["X"] if "X" in parsed_command.parameters else None  # should remain in the original coordinate system
                _y2 = parsed_command.parameters["Y"] if "Y" in parsed_command.parameters else None  # should remain in the original coordinate system
                _z = parsed_command.parameters["Z"] if "Z" in parsed_command.parameters else None  # should remain in the original coordinate system
                _e = parsed_command.parameters["E"] if "E" in parsed_command.parameters else None
                _f = parsed_command.parameters["F"] if "F" in parsed_command.parameters else None
                # if the command has an F parameter, update FCurrent

                if _f:
                    _f = float(_f)
                    if self.FCurrent != _f:
                        # if we have a new speed here, set it as the original
                        self.FCurrent = _f
                        self.FOriginal = _f

                _e1 = None
                _e2 = None
                # calculate e
                if _e:
                    _e = float(_e)
                    if not self.IsExtruderRelativeCurrent:
                        _extrusion_amount = position.e_relative(e=_e)
                        # set e1 absolute
                        _e1 = _e - _extrusion_amount * path_ratio_2
                        _e2 = _e
                    else:
                        _e1 = _e * path_ratio_1
                        _e2 = _e * path_ratio_2

                # Convert X1 and y1 to relative
                if self.IsRelativeCurrent:
                    if _x1:
                        _x1 = position.x_relative(_x1)
                    if _y1:
                        _y1 = position.y_relative(_y1)

                if _x2:
                    _x2 = float(_x2)
                if _y2:
                    _y2 = float(_y2)

                if _z:
                    _z = float(_z)
                if _f:
                    _f = float(_f)

                gcode1 = self.get_g_command(parsed_command.cmd, _x1, _y1, _z, _e1, _f)
                # create the second command
                gcode2 = self.get_g_command(parsed_command.cmd, _x2, _y2, _z, _e2, _f)

                # append both commands
                new_snapshot_gcode.append(SnapshotGcode.START_GCODE, gcode1)

                final_command = gcode2
                # set the return x and return y to the intersection point
                # must be in absolute coordinates
                x_return = intersection[0]  # will be in absolute coordinates
                y_return = intersection[1]  # will be in absolute coordinates

                # recalculate z_lift and retract distance since we have moved a bit
                command_1 = Commands.parse(gcode1)
                position.update(command_1)
                # set z_return to the new z position
                # must be absolute
                z_return = position.z()
                self.ZLift = position.distance_to_zlift()
                length_to_retract = position.Extruder.length_to_retract()

                # undo the update since the position has not changed, only the zlift value and potentially the
                # retraction length
                position.undo_update()
        else:
            return None

        if (
            self.Snapshot.retract_before_move and
            length_to_retract > 0
        ):
            if not self.IsExtruderRelativeCurrent:
                new_snapshot_gcode.append(
                    SnapshotGcode.START_GCODE,
                    self.get_gcode_extruder_relative()
                )
                self.IsExtruderRelativeCurrent = True

            if self.RetractSpeed != self.FCurrent:
                new_f = self.RetractSpeed
                self.FCurrent = new_f
            else:
                new_f = None
            if length_to_retract > 0:
                new_snapshot_gcode.append(
                    SnapshotGcode.START_GCODE,
                    self.get_gcode_retract(length_to_retract, new_f)
                )
                self.RetractedLength = length_to_retract
                self.RetractedBySnapshotStartGcode = True

        # Can we hop or are we too close to the top?
        can_zhop = self.ZLift is not None and self.Printer.z_hop > 0 and utility.is_in_bounds(
            self.BoundingBox, z=z_return + self.ZLift)
        # if we can ZHop, do
        if can_zhop and self.ZLift > 0 and self.Snapshot.lift_before_move:
            if not self.IsRelativeCurrent:  # must be in relative mode
                new_snapshot_gcode.append(
                    SnapshotGcode.START_GCODE,
                    self.get_gcode_axes_relative()
                )
                self.IsRelativeCurrent = True

            if self.ZHopSpeed != self.FCurrent:
                new_f = self.ZHopSpeed
                self.FCurrent = new_f
            else:
                new_f = None
            # append to snapshot gcode
            new_snapshot_gcode.append(
                SnapshotGcode.START_GCODE,
                self.get_gcode_z_lift_relative(self.ZLift, new_f)
            )
            self.ZhopBySnapshotStartGcode = True

        # Create code to move from the current extruder position to the snapshot position
        # get the X and Y coordinates of the snapshot
        snapshot_position = self.get_snapshot_position(x_return, y_return)
        new_snapshot_gcode.X = snapshot_position["X"]
        new_snapshot_gcode.Y = snapshot_position["Y"]

        if new_snapshot_gcode.X is None or new_snapshot_gcode.Y is None:
            # either x or y is out of bounds.
            return None

        # Move back to the snapshot position - make sure we're in absolute mode for this
        if self.IsRelativeCurrent:  # must be in absolute mode
            new_snapshot_gcode.append(
                SnapshotGcode.SNAPSHOT_COMMANDS,
                self.get_gcode_axes_absolute()
            )
            self.IsRelativeCurrent = False

        # detect speed change
        if self.FCurrent != self.TravelSpeed:
            new_f = self.TravelSpeed
            self.FCurrent = new_f
        else:
            new_f = None

        # Move to Snapshot Position
        new_snapshot_gcode.append(
            SnapshotGcode.SNAPSHOT_COMMANDS,
            self.get_gcode_travel(new_snapshot_gcode.X, new_snapshot_gcode.Y, new_f)
        )
        # End Snapshot Gcode

        # Start Return Gcode
        if self.ReturnWhenComplete:
            # Only return to the previous coordinates if we need to (which will be most cases,
            # except when the triggering command is a travel only (moves both X and Y)
            # record our previous position for posterity
            new_snapshot_gcode.ReturnX = x_return
            new_snapshot_gcode.ReturnY = y_return
            new_snapshot_gcode.ReturnZ = z_return

            # Move back to previous position - make sure we're in absolute mode for this (hint: we already are right now)
            # also, our current speed will be correct, no need to append F
            if x_return is not None and y_return is not None:
                new_snapshot_gcode.append(
                    SnapshotGcode.RETURN_COMMANDS,
                    self.get_gcode_travel(x_return, y_return)
                )
        else:
            # record the final position
            new_snapshot_gcode.ReturnX = triggering_command_position.X
            new_snapshot_gcode.ReturnY = triggering_command_position.Y
            # see about Z, we may need to suppress our
            new_snapshot_gcode.ReturnZ = triggering_command_position.Z
            self.Settings.current_debug_profile().log_snapshot_gcode(
                "Skipping return position, traveling to the triggering command position: X={0}, y={0}".format(
                    triggering_command_position.X, triggering_command_position.Y
                )
            )
            new_snapshot_gcode.append(
                SnapshotGcode.RETURN_COMMANDS,
                self.get_gcode_travel(triggering_command_position.X, triggering_command_position.Y)
            )


            # Return to the previous feedrate if it's changed

        # If we zhopped in the beginning, lower z
        if self.ZhopBySnapshotStartGcode:
            if not self.IsRelativeCurrent:
                new_snapshot_gcode.append(
                    SnapshotGcode.END_GCODE,
                    self.get_gcode_axes_relative()
                )
                self.IsRelativeCurrent = True

            if self.ZHopSpeed != self.FCurrent:
                new_f = self.ZHopSpeed
                self.FCurrent = new_f
            else:
                new_f = None

            new_snapshot_gcode.append(
                SnapshotGcode.END_GCODE,
                self.get_gocde_z_lower_relative(self.ZLift, new_f)
            )

        # detract
        if self.RetractedBySnapshotStartGcode:
            if not self.IsExtruderRelativeCurrent:
                new_snapshot_gcode.append(
                    SnapshotGcode.END_GCODE,
                    self.get_gcode_extruder_relative()
                )
                self.IsExtruderRelativeCurrent = True

            if self.DetractSpeed != self.FCurrent:
                new_f = self.DetractSpeed
                self.FCurrent = new_f
            else:
                new_f = None

            if self.RetractedLength > 0:
                new_snapshot_gcode.append(
                    SnapshotGcode.END_GCODE,
                    self.get_gcode_detract(self.RetractedLength, new_f)
                )

        # reset the coordinate systems for the extruder and axis
        if self.IsRelativeOriginal != self.IsRelativeCurrent:
            if self.IsRelativeCurrent:
                new_snapshot_gcode.append(
                    SnapshotGcode.END_GCODE,
                    self.get_gcode_axes_absolute()
                )
            else:
                new_snapshot_gcode.append(
                    SnapshotGcode.END_GCODE,
                    self.get_gcode_axes_relative()
                )
            self.IsRelativeCurrent = self.IsRelativeOriginal

        if self.IsExtruderRelativeOriginal != self.IsExtruderRelativeCurrent:
            if self.IsExtruderRelativeOriginal:
                new_snapshot_gcode.append(
                    SnapshotGcode.END_GCODE,
                    self.get_gcode_extruder_relative())
            else:
                new_snapshot_gcode.append(
                    SnapshotGcode.END_GCODE,
                    self.get_gcode_extruder_absolute())

        # Make sure we return to the original feedrate
        if reset_feedrate_before_end_gcode and self.FOriginal is not None and self.FOriginal != self.FCurrent:
            # we can't count on the end gcode to set f, set it here
            new_snapshot_gcode.append(
                SnapshotGcode.END_GCODE,
                self.get_gcode_feedrate(self.FOriginal))

        new_snapshot_gcode.append(
            SnapshotGcode.END_GCODE,
            final_command)

        self.Settings.current_debug_profile().log_snapshot_gcode(
            "Snapshot Gcode - SnapshotCommandIndex:{0}, EndIndex:{1}, Triggering Command:{2}".format(
                new_snapshot_gcode.snapshot_index(),
                new_snapshot_gcode.end_index(),
                parsed_command.gcode
            )
        )
        for gcode in new_snapshot_gcode.snapshot_gcode():
            self.Settings.current_debug_profile().log_snapshot_gcode("    {0}".format(gcode))

        return new_snapshot_gcode

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
    def get_gcode_detract(distance, f=None):
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
