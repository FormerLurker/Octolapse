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
# following email address: FormerLurker@protonmail.com
##################################################################################

from collections import deque

import math

import octoprint_octolapse.command as command
import octoprint_octolapse.utility as utility
from octoprint_octolapse.settings import Printer, Snapshot
from octoprint_octolapse.extruder import Extruder


def get_formatted_coordinates(x, y, z, e):
    x_string = "None"
    if x is not None:
        x_string = get_formatted_coordinate(float(x))

    y_string = "None"
    if y is not None:
        y_string = get_formatted_coordinate(float(y))

    z_string = "None"
    if z is not None:
        z_string = get_formatted_coordinate(float(z))

    e_string = "None"
    if e is not None:
        e_string = get_formatted_coordinate(float(e))

    return "(X:{0},Y:{1},Z:{2},E:{3})".format(x_string, y_string, z_string,
                                              e_string)


def get_formatted_coordinate(coord):
    return "{0:.5f}".format(coord)


class Pos(object):
    def __init__(self, printer, octoprint_printer_profile, pos=None):
        self.OctoprintPrinterProfile = octoprint_printer_profile
        # GCode
        self.GCode = None if pos is None else pos.GCode
        # F
        self.F = None if pos is None else pos.F
        # X
        self.X = None if pos is None else pos.X
        self.XOffset = 0 if pos is None else pos.XOffset
        self.XHomed = False if pos is None else pos.XHomed
        # Y
        self.Y = None if pos is None else pos.Y
        self.YOffset = 0 if pos is None else pos.YOffset
        self.YHomed = False if pos is None else pos.YHomed
        # Z
        self.Z = None if pos is None else pos.Z
        self.ZOffset = 0 if pos is None else pos.ZOffset
        self.ZHomed = False if pos is None else pos.ZHomed
        # E
        self.E = 0 if pos is None else pos.E
        self.EOffset = 0 if pos is None else pos.EOffset

        if pos is not None:
            self.IsRelative = pos.IsRelative
            self.IsExtruderRelative = pos.IsExtruderRelative
            self.IsMetric = pos.IsMetric
        else:
            if printer.e_axis_default_mode in ['absolute', 'relative']:
                self.IsExtruderRelative = True if printer.e_axis_default_mode == 'relative' else False
            else:
                self.IsExtruderRelative = None
            if printer.xyz_axes_default_mode in ['absolute', 'relative']:
                self.IsRelative = True if printer.xyz_axes_default_mode == 'relative' else False
            else:
                self.IsRelative = None
            if printer.units_default in ['inches', 'millimeters']:
                self.IsMetric = True if printer.units_default == 'millimeters' else False
            else:
                self.IsMetric = None

        self.LastExtrusionHeight = None if pos is None else pos.LastExtrusionHeight
        # Layer and Height Tracking
        self.Layer = 0 if pos is None else pos.Layer
        self.Height = 0 if pos is None else pos.Height
        self.IsPrimed = False if pos is None else pos.IsPrimed
        self.IsInPosition = False if pos is None else pos.IsInPosition
        self.InPathPosition = False if pos is None else pos.InPathPosition

        # State Flags
        self.IsLayerChange = False if pos is None else pos.IsLayerChange
        self.IsHeightChange = False if pos is None else pos.IsHeightChange
        self.IsZHop = False if pos is None else pos.IsZHop
        self.HasPositionChanged = False if pos is None else pos.HasPositionChanged
        self.HasStateChanged = False if pos is None else pos.HasStateChanged
        self.HasReceivedHomeCommand = False if pos is None else pos.HasStateChanged
        # Error Flags
        self.HasPositionError = False if pos is None else pos.HasPositionError
        self.PositionError = None if pos is None else pos.PositionError

    def reset_state(self):
        self.IsLayerChange = False
        self.IsHeightChange = False
        self.IsZHop = False
        self.HasPositionChanged = False
        self.HasStateChanged = False
        self.HasReceivedHomeCommand = False

    def is_state_equal(self, pos, tolerance):
        if (self.XHomed == pos.XHomed and self.YHomed == pos.YHomed
                and self.ZHomed == pos.ZHomed
                and self.IsLayerChange == pos.IsLayerChange
                and self.IsHeightChange == pos.IsHeightChange
                and self.IsZHop == pos.IsZHop
                and self.IsRelative == pos.IsRelative
                and self.IsExtruderRelative == pos.IsExtruderRelative
                and utility.round_to(pos.Layer, tolerance) != utility.round_to(
                    self.Layer, tolerance)
                and utility.round_to(pos.Height, tolerance) !=
                    utility.round_to(self.Height, tolerance)
                and utility.round_to(pos.LastExtrusionHeight, tolerance) !=
                    utility.round_to(self.LastExtrusionHeight, tolerance)
                and self.IsPrimed == pos.IsPrimed
                and self.IsInPosition == pos.IsInPosition
                and self.InPathPosition == Pos.InPathPosition
                and self.HasPositionError == pos.HasPositionError
                and self.PositionError == pos.PositionError
                and self.HasReceivedHomeCommand == pos.HasReceivedHomeCommand):
            return True

        return False

    def is_position_equal(self, pos, tolerance):
        if tolerance == 0:
            return (pos.X is not None and self.X is not None and pos.X == self.X
                    and pos.Y is not None and self.Y is not None and pos.Y == self.Y
                    and pos.Z is not None and self.Z is not None and pos.Z == self.Z)

        elif (pos.X is not None and self.X is not None and utility.round_to(
            pos.X, tolerance) == utility.round_to(self.X, tolerance)
              and pos.Y is not None and self.Y is not None
              and utility.round_to(pos.Y, tolerance) == utility.round_to(
                self.Y, tolerance) and pos.Z is not None
              and self.Z is not None and utility.round_to(
                pos.Z, tolerance) == utility.round_to(self.Z, tolerance)):
            return True
        return False

    def to_state_dict(self):
        return {
            "GCode": self.GCode,
            "XHomed": self.XHomed,
            "YHomed": self.YHomed,
            "ZHomed": self.ZHomed,
            "IsLayerChange": self.IsLayerChange,
            "IsHeightChange": self.IsHeightChange,
            "IsZHop": self.IsZHop,
            "IsRelative": self.IsRelative,
            "IsExtruderRelative": self.IsExtruderRelative,
            "IsMetric": self.IsMetric,
            "Layer": self.Layer,
            "Height": self.Height,
            "LastExtrusionHeight": self.LastExtrusionHeight,
            "IsInPosition": self.IsInPosition,
            "InPathPosition": self.InPathPosition,
            "IsPrimed": self.IsPrimed,
            "HasPositionError": self.HasPositionError,
            "PositionError": self.PositionError,
            "HasReceivedHomeCommand": self.HasReceivedHomeCommand
        }

    def to_position_dict(self):
        return {
            "F": self.F,
            "X": self.X,
            "XOffset": self.XOffset,
            "Y": self.Y,
            "YOffset": self.YOffset,
            "Z": self.Z,
            "ZOffset": self.ZOffset,
            "E": self.E,
            "EOffset": self.EOffset

        }

    def to_dict(self):
        return {
            "GCode": self.GCode,
            "F": self.F,
            "X": self.X,
            "XOffset": self.XOffset,
            "XHomed": self.XHomed,
            "Y": self.Y,
            "YOffset": self.YOffset,
            "YHomed": self.YHomed,
            "Z": self.Z,
            "ZOffset": self.ZOffset,
            "ZHomed": self.ZHomed,
            "E": self.E,
            "EOffset": self.EOffset,
            "IsRelative": self.IsRelative,
            "IsExtruderRelative": self.IsExtruderRelative,
            "IsMetric": self.IsMetric,
            "LastExtrusionHeight": self.LastExtrusionHeight,
            "IsLayerChange": self.IsLayerChange,
            "IsZHop": self.IsZHop,
            "IsInPosition": self.IsInPosition,
            "InPathPosition": self.InPathPosition,
            "IsPrimed": self.IsPrimed,
            "HasPositionError": self.HasPositionError,
            "PositionError": self.PositionError,
            "HasPositionChanged": self.HasPositionChanged,
            "HasStateChanged": self.HasStateChanged,
            "Layer": self.Layer,
            "Height": self.Height,
            "HasReceivedHomeCommand": self.HasReceivedHomeCommand
        }

    def has_homed_axes(self):
        return self.XHomed and self.YHomed and self.ZHomed

    def has_homed_position(self):
        return (self.has_homed_axes() and self.IsMetric and self.X is not None
                and self.Y is not None and self.Z is not None)

    def update_position(self,
                        bounding_box,
                        x=None,
                        y=None,
                        z=None,
                        e=None,
                        f=None,
                        force=False):

        if f is not None:
            self.F = float(f)
        if force:
            # Force the coordinates in as long as they are provided.
            #
            if x is not None:
                x = float(x)
                x = x + self.XOffset
                self.X = x
            if y is not None:
                y = float(y)
                y = y + self.YOffset
                self.Y = y
            if z is not None:
                z = float(z)
                z = z + self.ZOffset
                self.Z = z

            if e is not None:
                e = float(e)
                e = e + self.EOffset
                self.E = e

        else:

            # Update the previous positions if values were supplied
            if x is not None and self.XHomed:
                x = float(x)
                if self.IsRelative:
                    if self.X is not None:
                        self.X += x
                else:
                    self.X = x + self.XOffset

            if y is not None and self.YHomed:
                y = float(y)
                if self.IsRelative:
                    if self.Y is not None:
                        self.Y += y
                else:
                    self.Y = y + self.YOffset

            if z is not None and self.ZHomed:

                z = float(z)
                if self.IsRelative:
                    if self.Z is not None:
                        self.Z += z
                else:
                    self.Z = z + self.ZOffset

            if e is not None:
                e = float(e)
                if self.IsExtruderRelative:
                    if self.E is not None:
                        self.E += e
                else:
                    self.E = e + self.EOffset

            if (not utility.is_in_bounds(
                    bounding_box, x=self.X, y=self.Y, z=self.Z)):
                self.HasPositionError = True
                self.PositionError = "Position - Coordinates {0} are out of the printer area!  " \
                                     "Cannot resume position tracking until the axis is homed, "  \
                                     "or until absolute coordinates are received.".format(
                                        get_formatted_coordinates(self.X, self.Y, self.Z, self.E))
            else:
                self.HasPositionError = False
                self.PositionError = None

    def distance_to_zlift(self, z_hop, restrict_lift_height=True):

        current_lift = self.Z - self.LastExtrusionHeight
        amount_to_lift = z_hop - current_lift

        if restrict_lift_height:
            if amount_to_lift < 0:
                return 0
            elif amount_to_lift > z_hop:
                return z_hop
            else:
                # we are in-between 0 and z_hop, calculate lift
                return amount_to_lift

        return amount_to_lift


class Position(object):
    def __init__(self, octolapse_settings, octoprint_printer_profile,
                 g90_influences_extruder):
        self.Settings = octolapse_settings
        self.Printer = Printer(self.Settings.current_printer())
        self.Snapshot = Snapshot(self.Settings.current_snapshot())
        self.OctoprintPrinterProfile = octoprint_printer_profile
        self.Origin = {
            "X": self.Printer.origin_x,
            "Y": self.Printer.origin_y,
            "Z": self.Printer.origin_z
        }

        self.BoundingBox = utility.get_bounding_box(self.Printer,
                                                    octoprint_printer_profile)
        self.PrinterTolerance = self.Printer.printer_position_confirmation_tolerance
        self.Positions = deque(maxlen=5)
        self.SavedPosition = None
        self.HasRestrictedPosition = len(self.Snapshot.position_restrictions) > 0

        self.reset()

        self.Extruder = Extruder(octolapse_settings)
        if self.Printer.g90_influences_extruder in ['true', 'false']:
            self.G90InfluencesExtruder = True if self.Printer.g90_influences_extruder == 'true' else False
        else:
            self.G90InfluencesExtruder = g90_influences_extruder

        if self.Printer.z_hop is None:
            self.Printer.z_hop = 0

        self.Commands = command.Commands()
        self.LocationDetectionCommands = []
        self.create_location_detection_commands()


    def create_location_detection_commands(self):

        if self.Printer.auto_position_detection_commands is not None:
            trimmed_commands = self.Printer.auto_position_detection_commands.strip()
            if len(trimmed_commands) > 0:
                self.LocationDetectionCommands = [
                    x.strip().upper()
                    for x in
                    self.Printer.auto_position_detection_commands.split(',')
                ]
        if "G28" not in self.LocationDetectionCommands:
            self.LocationDetectionCommands.append("G28")
        if "G29" not in self.LocationDetectionCommands:
            self.LocationDetectionCommands.append("G29")

    def reset(self):
        # todo: This reset function doesn't seem to reset everything.
        self.Positions.clear()
        self.SavedPosition = None

    def update_position(self,
                        x=None,
                        y=None,
                        z=None,
                        e=None,
                        f=None,
                        force=False,
                        calculate_changes=False):
        num_positions = len(self.Positions)
        if num_positions == 0:
            return
        pos = self.Positions[0]
        pos.update_position(self.BoundingBox, x, y, z, e, f, force)
        if calculate_changes and num_positions > 1:
            previous_pos = self.Positions[1]
            pos.HasPositionChanged = not pos.is_position_equal(
                previous_pos, self.PrinterTolerance)
            pos.HasStateChanged = not pos.is_state_equal(previous_pos,
                                                         self.PrinterTolerance)

    def to_dict(self):
        if len(self.Positions) > 0:
            previous_pos = self.Positions[0]
            return previous_pos.to_dict()
        return None

    def to_position_dict(self):
        if len(self.Positions) > 0:
            previous_pos = self.Positions[0]
            return previous_pos.to_position_dict()
        return None

    def to_state_dict(self):
        if len(self.Positions) > 0:
            previous_pos = self.Positions[0]
            return previous_pos.to_state_dict()
        return None

    def z_delta(self, pos, index=0):
        previous_pos = self.get_position(index)
        if previous_pos is not None:
            # calculate ZDelta
            if pos.Height is not None:
                if previous_pos.Height is None:
                    return pos.Height
                else:
                    return pos.Height - previous_pos.Height
        return 0

    def distance_to_zlift(self, index=0):
        pos = self.get_position(index)
        assert(isinstance(pos, Pos))

        if pos is None:
            return None

        # get the lift amount, but don't restrict it so we can log properly
        amount_to_lift = pos.distance_to_zlift(self.Printer.z_hop, False)

        if amount_to_lift < 0:
            # the current lift is negative
            self.Settings.current_debug_profile().log_warning("position.py - A 'distance_to_zlift' was requested, "
                                                              "but the current lift is already above the z_hop height.")
            return 0
        elif amount_to_lift > self.Printer.z_hop:
            # For some reason we're lower than we expected
            self.Settings.current_debug_profile().log_warning("position.py - A 'distance_to_zlift' was requested, "
                                                              "but was found to be more than the z_hop height.")
            return self.Printer.z_hop
        else:
            # we are in-between 0 and z_hop, calculate lift
            return amount_to_lift

    def has_state_changed(self, index=0):
        pos = self.get_position(index)
        if pos is None:
            return None
        return pos.HasStateChanged

    def is_in_position(self, index=0):
        pos = self.get_position(index)
        if pos is None:
            return None
        return pos.IsInPosition

    def in_path_position(self, index=0):
        pos = self.get_position(index)
        if pos is None:
            return None
        return pos.InPathPosition

    def has_position_changed(self, index=0):
        pos = self.get_position(index)
        if pos is None:
            return None
        return pos.HasPositionChanged

    def has_position_error(self, index=0):
        pos = self.get_position(index)
        if pos is None:
            return None
        return pos.HasPositionError

    def position_error(self, index=0):
        pos = self.get_position(index)
        if pos is None:
            return None
        return pos.PositionError

    def x(self, index=0):
        pos = self.get_position(index)
        if pos is None:
            return None
        return pos.X

    def x_offset(self, index=0):
        pos = self.get_position(index)
        if pos is None:
            return None
        return pos.XOffset

    def y(self, index=0):
        pos = self.get_position(index)
        if pos is None:
            return None
        return pos.Y

    def y_offset(self, index=0):
        pos = self.get_position(index)
        if pos is None:
            return None
        return pos.YOffset

    def z(self, index=0):
        pos = self.get_position(index)
        if pos is None:
            return None
        return pos.Z

    def z_offset(self, index=0):
        pos = self.get_position(index)
        if pos is None:
            return None
        return pos.ZOffset

    def e(self, index=0):
        pos = self.get_position(index)
        if pos is None:
            return None
        return pos.E

    def e_offset(self, index=0):
        pos = self.get_position(index)
        if pos is None:
            return None
        return pos.EOffset

    def f(self, index=0):
        pos = self.get_position(index)
        if pos is None:
            return None
        return pos.F

    def is_zhop(self, index=0):
        pos = self.get_position(index)
        if pos is None:
            return None
        return pos.IsZHop

    def is_layer_change(self, index=0):
        pos = self.get_position(index)
        if pos is None:
            return None
        return pos.IsLayerChange

    def layer(self, index=0):
        pos = self.get_position(index)
        if pos is None:
            return None
        return pos.Layer

    def height(self, index=0):
        pos = self.get_position(index)
        if pos is None:
            return None
        return pos.Height

    def is_relative(self, index=0):
        pos = self.get_position(index)
        if pos is None:
            return None
        return pos.IsRelative

    def is_extruder_relative(self, index=0):
        pos = self.get_position(index)
        if pos is None:
            return None
        return pos.IsExtruderRelative

    def is_metric(self, index=0):
        pos = self.get_position(index)
        if pos is None:
            return None
        return pos.IsMetric

    def has_received_home_command(self, index=0):
        pos = self.get_position(index)
        if pos is None:
            return False
        return pos.HasReceivedHomeCommand and self.has_homed_axes(index)

    def command_requires_location_detection(self, cmd):
        if self.Printer.auto_detect_position:
            gcode = command.get_gcode_from_string(cmd)
            if gcode in self.LocationDetectionCommands:
                return True
        return False

    def requires_location_detection(self, index=0):
        pos = self.get_position(index)
        if pos is None:
            return False

        if self.command_requires_location_detection(pos.GCode):
            return True
        return False

    def undo_update(self):
        pos = self.get_position(0)
        if pos is not None:
            self.Positions.popleft()
        self.Extruder.undo_update()

    def get_position(self, index=0):
        if len(self.Positions) > index:
            return self.Positions[index]
        return None

    def update(self, gcode):
        cmd = self.Commands.get_command(gcode)
        # a new position

        pos = None
        previous_pos = None
        num_positions = len(self.Positions)
        if num_positions > 0:
            pos = Pos(self.Printer, self.OctoprintPrinterProfile, self.Positions[0])
            previous_pos = Pos(self.Printer, self.OctoprintPrinterProfile, self.Positions[0])
        if pos is None:
            pos = Pos(self.Printer, self.OctoprintPrinterProfile)
        if previous_pos is None:
            previous_pos = Pos(self.Printer, self.OctoprintPrinterProfile)

        # reset the current position state (copied from the previous position,
        # or a
        # new position)
        pos.reset_state()
        # set the pos gcode cmd
        pos.GCode = gcode

        # apply the cmd to the position tracker
        # TODO: this should NOT be an else/if structure anymore..  Simplify
        if cmd is not None:

            if cmd.Command in self.Commands.CommandsRequireMetric and not pos.IsMetric:
                pos.HasPositionError = True
                pos.PositionError = "Units are not metric.  Unable to continue print."
            elif cmd.Command in ["G0", "G1"]:
                # Movement
                if cmd.parse():
                    self.Settings.current_debug_profile().log_position_command_received("Received {0}".format(cmd.Name))
                    x = cmd.Parameters["X"].Value
                    y = cmd.Parameters["Y"].Value
                    z = cmd.Parameters["Z"].Value
                    e = cmd.Parameters["E"].Value
                    f = cmd.Parameters["F"].Value

                    if x is not None or y is not None or z is not None or f is not None:
                        if pos.IsRelative is not None:
                            if pos.HasPositionError and not pos.IsRelative:
                                pos.HasPositionError = False
                                pos.PositionError = ""
                            pos.update_position(self.BoundingBox, x, y, z, e=None, f=f)
                        else:
                            self.Settings.current_debug_profile().log_position_command_received(
                                "Position - Unable to update the X/Y/Z axis position, the axis mode ("
                                "relative/absolute) has not been explicitly set via G90/G91. "
                            )
                    if e is not None:
                        if pos.IsExtruderRelative is not None:
                            if pos.HasPositionError and not pos.IsExtruderRelative:
                                pos.HasPositionError = False
                                pos.PositionError = ""
                            pos.update_position(
                                self.BoundingBox,
                                x=None,
                                y=None,
                                z=None,
                                e=e,
                                f=None)
                        else:
                            self.Settings.current_debug_profile().log_error(
                                "Position - Unable to update the extruder position, the extruder mode ("
                                "relative/absolute) has been selected (absolute/relative). "
                            )
                    message = "Position Change - {0} - {1} Move From(X:{2},Y:{3},Z:{4},E:{5}) - To(X:{6},Y:{7},Z:{8}," \
                              "E:{9}) "
                    if previous_pos is None:
                        message = message.format(
                            gcode, "Relative"
                            if pos.IsRelative else "Absolute", "None", "None",
                            "None", "None", pos.X, pos.Y, pos.Z, pos.E)
                    else:
                        message = message.format(
                            gcode, "Relative"
                            if pos.IsRelative else "Absolute", previous_pos.X,
                            previous_pos.Y, previous_pos.Z, previous_pos.E, pos.X,
                            pos.Y, pos.Z, pos.E)
                    self.Settings.current_debug_profile().log_position_change(
                        message)
                else:
                    error_message = "Unable to parse the gcode command: {0}".format(gcode)
                    pos.HasPositionError = True
                    # Todo:  We need to end the timelapse if we get here
                    #pos.X = None
                    #pos.Y = None
                    #pos.Z = None
                    #pos.E = None#
                    #pos.F = None
                    pos.PositionError = "Unable to parse the gcode command"
                    self.Settings.current_debug_profile().log_error(
                        "Position - {0}".format(error_message))
            elif cmd.Command == "G20":
                # change units to inches
                if pos.IsMetric is None or pos.IsMetric:
                    self.Settings.current_debug_profile(
                    ).log_position_command_received(
                        "Received G20 - Switching units to inches."
                    )
                    pos.IsMetric = False
                else:
                    self.Settings.current_debug_profile(
                    ).log_position_command_received(
                        "Received G20 - Already in inches."
                    )
            elif cmd.Command == "G21":
                # change units to millimeters
                if pos.IsMetric is None or not pos.IsMetric:
                    self.Settings.current_debug_profile(
                    ).log_position_command_received(
                        "Received G21 - Switching units to millimeters."
                    )
                    pos.IsMetric = True
                else:
                    self.Settings.current_debug_profile(
                    ).log_position_command_received(
                        "Received G21 - Already in millimeters."
                    )
            elif cmd.Command == "G28":
                # Home
                if cmd.parse():
                    pos.HasReceivedHomeCommand = True
                    x = cmd.Parameters["X"].Value
                    y = cmd.Parameters["Y"].Value
                    z = cmd.Parameters["Z"].Value
                    # ignore the W parameter, it's used in Prusa firmware to indicate a home without mesh bed leveling
                    # w = cmd.Parameters["W"].Value
                    x_homed = False
                    y_homed = False
                    z_homed = False
                    if x is not None:
                        x_homed = True
                    if y is not None:
                        y_homed = True
                    if z is not None:
                        z_homed = True

                    # if there are no x,y or z parameters, we're homing all axes
                    if x is None and y is None and z is None:
                        x_homed = True
                        y_homed = True
                        z_homed = True

                    home_strings = []
                    if x_homed:
                        pos.XHomed = True
                        pos.X = self.Origin[
                            "X"] if not self.Printer.auto_detect_position else None
                        if pos.X is None:
                            home_strings.append("Homing X to Unknown Origin.")
                        else:
                            home_strings.append("Homing X to {0}.".format(
                                get_formatted_coordinate(pos.X)))
                    if y_homed:
                        pos.YHomed = True
                        pos.Y = self.Origin[
                            "Y"] if not self.Printer.auto_detect_position else None
                        if pos.Y is None:
                            home_strings.append("Homing Y to Unknown Origin.")
                        else:
                            home_strings.append("Homing Y to {0}.".format(
                                get_formatted_coordinate(pos.Y)))
                    if z_homed:
                        pos.ZHomed = True
                        pos.Z = self.Origin[
                            "Z"] if not self.Printer.auto_detect_position else None
                        if pos.Z is None:
                            home_strings.append("Homing Z to Unknown Origin.")
                        else:
                            home_strings.append("Homing Z to {0}.".format(
                                get_formatted_coordinate(pos.Z)))

                    self.Settings.current_debug_profile().log_position_command_received(
                        "Received G28 - ".format(" ".join(home_strings)))
                    pos.HasPositionError = False
                    pos.PositionError = None
                    # we must do this in case we have more than one home command
                    previous_pos = Pos(self.Printer, self.OctoprintPrinterProfile, pos)
                else:
                    self.Settings.current_debug_profile().log_error(
                        "Position - Unable to parse the Gcode:{0}".format(gcode))
            elif cmd.Command == "G90":
                # change x,y,z to absolute
                if pos.IsRelative is None or pos.IsRelative:
                    self.Settings.current_debug_profile(
                    ).log_position_command_received(
                        "Received G90 - Switching to absolute x,y,z coordinates."
                    )
                    pos.IsRelative = False
                else:
                    self.Settings.current_debug_profile(
                    ).log_position_command_received(
                        "Received G90 - Already using absolute x,y,z coordinates."
                    )

                # for some firmwares we need to switch the extruder to
                # absolute
                # coordinates
                # as well
                if self.G90InfluencesExtruder:
                    if pos.IsExtruderRelative is None or pos.IsExtruderRelative:
                        self.Settings.current_debug_profile(
                        ).log_position_command_received(
                            "Received G90 - Switching to absolute extruder coordinates"
                        )
                        pos.IsExtruderRelative = False
                    else:
                        self.Settings.current_debug_profile(
                        ).log_position_command_received(
                            "Received G90 - Already using absolute extruder coordinates"
                        )
            elif cmd.Command == "G91":
                # change x,y,z to relative
                if pos.IsRelative is None or not pos.IsRelative:
                    self.Settings.current_debug_profile().log_position_command_received(
                        "Received G91 - Switching to relative x,y,z coordinates")
                    pos.IsRelative = True
                else:
                    self.Settings.current_debug_profile(
                    ).log_position_command_received(
                        "Received G91 - Already using relative x,y,z coordinates"
                    )

                # for some firmwares we need to switch the extruder to
                # absolute
                # coordinates
                # as well
                if self.G90InfluencesExtruder:
                    if pos.IsExtruderRelative is None or not pos.IsExtruderRelative:
                        self.Settings.current_debug_profile().log_position_command_received(
                            "Received G91 - Switching to relative extruder coordinates"
                        )
                        pos.IsExtruderRelative = True
                    else:
                        self.Settings.current_debug_profile().log_position_command_received(
                            "Received G91 - Already using relative extruder coordinates"
                        )
            elif cmd.Command == "M83":
                # Extruder - Set Relative
                if pos.IsExtruderRelative is None or not pos.IsExtruderRelative:
                    self.Settings.current_debug_profile().log_position_command_received(
                        "Received M83 - Switching Extruder to Relative Coordinates"
                    )
                    pos.IsExtruderRelative = True
            elif cmd.Command == "M82":
                # Extruder - Set Absolute
                if pos.IsExtruderRelative is None or pos.IsExtruderRelative:
                    self.Settings.current_debug_profile().log_position_command_received(
                        "Received M82 - Switching Extruder to Absolute Coordinates"
                    )
                    pos.IsExtruderRelative = False
            elif cmd.Command == "G92":
                # Set Position (offset)
                if cmd.parse():
                    x = cmd.Parameters["X"].Value
                    y = cmd.Parameters["Y"].Value
                    z = cmd.Parameters["Z"].Value
                    e = cmd.Parameters["E"].Value
                    if x is None and y is None and z is None and e is None:
                        pos.XOffset = pos.X
                        pos.YOffset = pos.Y
                        pos.ZOffset = pos.Z
                        pos.EOffset = pos.E
                    # set the offsets if they are provided
                    if x is not None and pos.X is not None and pos.XHomed:
                        pos.XOffset = pos.X - utility.get_float(x, 0)
                    if y is not None and pos.Y is not None and pos.YHomed:
                        pos.YOffset = pos.Y - utility.get_float(y, 0)
                    if z is not None and pos.Z is not None and pos.ZHomed:
                        pos.ZOffset = pos.Z - utility.get_float(z, 0)
                    if e is not None and pos.E is not None:
                        pos.EOffset = pos.E - utility.get_float(e, 0)
                    self.Settings.current_debug_profile().log_position_command_received(
                        "Received G92 - Set Position.  Command:{0}, XOffset:{1}, " +
                        "YOffset:{2}, ZOffset:{3}, EOffset:{4}".format(
                            gcode, pos.XOffset, pos.YOffset, pos.ZOffset, pos.EOffset))
                else:
                    self.Settings.current_debug_profile().log_error(
                        "Position - Unable to parse the Gcode:{0}".format(
                            gcode))

        ########################################
        # Update the extruder monitor.
        self.Extruder.update(self.e_relative_pos(pos))

        ########################################
        # If we have a homed axis, detect changes.
        ########################################
        # for now we're going to ignore extruder changes and just run calculations every time.
        # has_extruder_changed = self.Extruder.HasChanged()

        pos.HasPositionChanged = not pos.is_position_equal(previous_pos, 0)
        pos.HasStateChanged = not pos.is_state_equal(previous_pos, self.PrinterTolerance)

        if pos.has_homed_position() and previous_pos.has_homed_position():

            # if (hasExtruderChanged or pos.HasPositionChanged):
            if pos.HasPositionChanged:
                if self.HasRestrictedPosition:
                    _is_in_position, _intersections = self.calculate_path_intersections(
                        self.Snapshot.position_restrictions,
                        pos.X,
                        pos.Y,
                        previous_pos.X,
                        previous_pos.Y
                    )
                    if _is_in_position:
                        pos.IsInPosition = _is_in_position

                    else:
                        pos.IsInPosition = False
                        pos.InPathPosition = _intersections
                else:
                    pos.IsInPosition = True

            # calculate LastExtrusionHeight and Height
            if self.Extruder.is_extruding():
                pos.LastExtrusionHeight = pos.Z

                # see if we have primed yet
                if self.Printer.priming_height > 0:
                    if not pos.IsPrimed and pos.LastExtrusionHeight < self.Printer.priming_height:
                        pos.IsPrimed = True
                else:
                    # if we have no priming height set, just set IsPrimed = true.
                    pos.IsPrimed = True

                # make sure we are primed before calculating height/layers
                if pos.IsPrimed:
                    if pos.Height is None or utility.round_to(pos.Z, self.PrinterTolerance) > previous_pos.Height:
                        pos.Height = utility.round_to(
                            pos.Z, self.PrinterTolerance)
                        self.Settings.current_debug_profile(
                        ).log_position_height_change(
                            "Position - Reached New Height:{0}.".format(
                                pos.Height))

                    # calculate layer change
                    if (utility.round_to(
                            self.z_delta(pos), self.PrinterTolerance) > 0
                            or pos.Layer == 0):
                        pos.IsLayerChange = True
                        pos.Layer += 1
                        self.Settings.current_debug_profile(
                        ).log_position_layer_change(
                            "Position - Layer:{0}.".format(pos.Layer))
                    else:
                        pos.IsLayerChange = False

            # Calculate ZHop based on last extrusion height
            if pos.LastExtrusionHeight is not None:
                # calculate lift, taking into account floating point
                # rounding
                lift = pos.distance_to_zlift(self.Printer.z_hop)

                # todo:  replace rounding with a call to is close or greater than utility function
                lift = utility.round_to(lift, self.PrinterTolerance)
                is_lifted = lift >= self.Printer.z_hop and (
                    not self.Extruder.is_extruding() or self.Extruder.is_extruding_start()
                )

                if is_lifted or self.Printer.z_hop == 0:
                    pos.IsZHop = True

            if pos.IsZHop and self.Printer.z_hop > 0:
                self.Settings.current_debug_profile().log_position_zhop(
                    "Position - Zhop:{0}".format(self.Printer.z_hop))

        self.Positions.appendleft(pos)

    def has_homed_position(self, index=0):
        if len(self.Positions) <= index:
            return None
        pos = self.Positions[index]
        return pos.has_homed_position()

    def has_homed_axes(self, index=0):
        if len(self.Positions) <= index:
            return None
        pos = self.Positions[index]
        return pos.has_homed_axes()

    def x_relative(self, index=0, x=None):

        if x:
            if len(self.Positions) <= index:
                return None
            pos = self.Positions[index]
            return x - pos.X+ pos.XOffset

        else:
            if len(self.Positions) <= index + 1:
                return None
            pos = self.Positions[index]
            previous_pos = self.Positions[index + 1]
            return pos.X - previous_pos.X

    def y_relative(self, index=0, y=None):

        if y:
            if len(self.Positions) <= index:
                return None
            pos = self.Positions[index]
            return y - pos.Y + pos.YOffset

        else:
            if len(self.Positions) <= index + 1:
                return None
            pos = self.Positions[index]
            previous_pos = self.Positions[index + 1]
            return pos.Y - previous_pos.Y

    def z_relative(self, index=0, z=None):

        if z:
            if len(self.Positions) <= index:
                return None
            pos = self.Positions[index]
            return z - pos.Z + pos.ZOffset

        else:
            if len(self.Positions) <= index + 1:
                return None
            pos = self.Positions[index]
            previous_pos = self.Positions[index + 1]
            return pos.Z - previous_pos.Z

    def e_relative(self, index=0, e=None):

        if e:
            if len(self.Positions) <= index:
                return None
            pos = self.Positions[index]
            return e - pos.E + pos.EOffset

        else:
            if len(self.Positions) <= index+1:
                return None
            pos = self.Positions[index]
            previous_pos = self.Positions[index+1]
            return pos.E - previous_pos.E

    def e_relative_pos(self, pos):
        if len(self.Positions) < 1:
            return None
        previous_pos = self.Positions[0]
        return pos.E - previous_pos.E

    @staticmethod
    def is_at_position(x, y, z, pos, tolerance, apply_offsets):
        if apply_offsets:
            x = x + pos.XOffset
            y = y + pos.YOffset
            if z is not None:
                z = z + pos.ZOffset

        if ((pos.X is None or utility.is_close(pos.X, x, abs_tol=tolerance))
                and (pos.Y is None or utility.is_close(pos.Y, y, abs_tol=tolerance))
                and (z is None or pos.Z is None
                     or utility.is_close(pos.Z, z, abs_tol=tolerance))):
            return True
        return False

    def is_at_previous_position(self, x, y, z=None):
        if len(self.Positions) < 2:
            return False
        return self.is_at_position(
            x, y, z, self.Positions[1],
            self.Printer.printer_position_confirmation_tolerance, True)

    def is_at_current_position(self, x, y, z=None):
        if len(self.Positions) < 1:
            return False
        return self.is_at_position(
            x, y, z, self.Positions[0],
            self.Printer.printer_position_confirmation_tolerance, True)

    def get_position_string(self, index=0):
        if len(self.Positions) < 1:
            return get_formatted_coordinates(None, None, None, None)
        current_position = self.Positions[index]
        return get_formatted_coordinates(current_position.X, current_position.Y,
                                         current_position.Z, current_position.E)

    def calculate_path_intersections(self, restrictions, x, y, previous_x, previous_y):

        if self.calculate_is_in_position(
            restrictions,
            x,
            y,
            self.Printer.printer_position_confirmation_tolerance
        ):
            return True, None

        if previous_x is None or previous_y is None:
            return False, False

        return False, self.calculate_in_position_intersection(
            restrictions,
            x,
            y,
            previous_x,
            previous_y,
            self.Printer.printer_position_confirmation_tolerance
        )

    @staticmethod
    def calculate_in_position_intersection(restrictions, x, y, previous_x, previous_y, tolerance):
        intersections = []
        for restriction in restrictions:
            cur_intersections = restriction.get_intersections(x, y, previous_x, previous_y)
            if cur_intersections:
                for cur_intersection in cur_intersections:
                    intersections.append(cur_intersection)

        if len(intersections) == 0:
            return False

        for intersection in intersections:
            if Position.calculate_is_in_position(restrictions, intersection[0], intersection[1], tolerance):
                # calculate the distance from x/y previous to the intersection
                distance_to_intersection = math.sqrt(
                    math.pow(previous_x - intersection[0], 2) + math.pow(previous_y - intersection[1], 2)
                )
                # calculate the length of the lin x,y to previous_x, previous_y
                total_distance = math.sqrt(
                    math.pow(previous_x - x, 2) + math.pow(previous_y - y, 2)
                )
                if total_distance > 0:
                    path_ratio_1 = distance_to_intersection / total_distance
                    path_ratio_2 = 1.0 - path_ratio_1
                else:
                    path_ratio_1 = 0
                    path_ratio_2 = 0

                return {
                    'intersection': intersection,
                    'path_ratio_1': path_ratio_1,
                    'path_ratio_2': path_ratio_2
                }
        return False

    @staticmethod
    def calculate_is_in_position(restrictions, x, y, tolerance):
        # we need to know if there is at least one required position
        has_required_position = False
        # isInPosition will be used to determine if we return
        # true where we have at least one required type
        in_position = False

        # loop through each restriction
        for restriction in restrictions:
            if restriction.Type == "required":
                # we have at least on required position, so at least one point must be in
                # position for us to return true
                has_required_position = True
            if restriction.is_in_position(x, y, tolerance):
                if restriction.Type == "forbidden":
                    # if we're in a forbidden position, return false now
                    return False
                else:
                    # we're in position in at least one required position restriction
                    in_position = True

        if has_required_position:
            # if at least one position restriction is required
            return in_position

        # if we're here then we only have forbidden restrictions, but the point
        # was not within the restricted area(s)
        return True
