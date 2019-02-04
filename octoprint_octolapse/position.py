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

from collections import deque

import math

import octoprint_octolapse.utility as utility
from octoprint_octolapse.gcode_parser import Commands
from octoprint_octolapse.settings import PrinterProfile, SnapshotProfile, SlicerPrintFeatures, OctolapseGcodeSettings
from octoprint_octolapse.extruder import Extruder
import copy


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
    # Add slots for faster copy and init
    __slots__ = ["parsed_command", "F", "X", "XOffset", "XHomed", "Y", "YOffset", "YHomed", "Z", "ZOffset", "ZHomed",
                 "E", "EOffset", "IsRelative", "IsExtruderRelative", "IsMetric", "LastExtrusionHeight", "Layer",
                 "Height", "IsPrimed", "MinimumLayerHeightReached", "IsInPosition", "InPathPosition", "IsTravelOnly",
                 "Features", "HasOneFeatureEnabled", "FirmwareRetractionLength", "FirmwareUnretractionAdditionalLength",
                 "FirmwareRetractionFeedrate", "FirmwareUnretractionFeedrate", "FirmwareZLift", "HasHomedPosition",
                 "IsLayerChange","IsHeightChange", "IsZHop", "HasPositionChanged", "HasStateChanged",
                 "HasReceivedHomeCommand", "HasPositionError", "PositionError"]

    def __init__(self,copy_from_pos=None, reset_state=False):
        self.parsed_command = None if copy_from_pos is None else copy_from_pos.parsed_command
        self.F = None if copy_from_pos is None else copy_from_pos.F
        self.X = None if copy_from_pos is None else copy_from_pos.X
        self.XOffset = 0 if copy_from_pos is None else copy_from_pos.XOffset
        self.XHomed = False if copy_from_pos is None else copy_from_pos.XHomed
        self.Y = None if copy_from_pos is None else copy_from_pos.Y
        self.YOffset = 0 if copy_from_pos is None else copy_from_pos.YOffset
        self.YHomed = False if copy_from_pos is None else copy_from_pos.YHomed
        self.Z = None if copy_from_pos is None else copy_from_pos.Z
        self.ZOffset = 0 if copy_from_pos is None else copy_from_pos.ZOffset
        self.ZHomed = False if copy_from_pos is None else copy_from_pos.ZHomed
        self.E = 0 if copy_from_pos is None else copy_from_pos.E
        self.EOffset = 0 if copy_from_pos is None else copy_from_pos.EOffset
        self.IsRelative = False if copy_from_pos is None else copy_from_pos.IsRelative
        self.IsExtruderRelative = False if copy_from_pos is None else copy_from_pos.IsExtruderRelative
        self.IsMetric = True if copy_from_pos is None else copy_from_pos.IsMetric
        self.LastExtrusionHeight = None if copy_from_pos is None else copy_from_pos.LastExtrusionHeight
        self.Layer = 0 if copy_from_pos is None else copy_from_pos.Layer
        self.Height = 0 if copy_from_pos is None else copy_from_pos.Height
        self.IsPrimed = False if copy_from_pos is None else copy_from_pos.IsPrimed
        self.MinimumLayerHeightReached = False if copy_from_pos is None else copy_from_pos.MinimumLayerHeightReached
        self.IsInPosition = False if copy_from_pos is None else copy_from_pos.IsInPosition
        self.InPathPosition = False if copy_from_pos is None else copy_from_pos.InPathPosition
        self.FirmwareRetractionLength = None if copy_from_pos is None else copy_from_pos.FirmwareRetractionLength
        self.FirmwareUnretractionAdditionalLength = None if copy_from_pos is None else copy_from_pos.FirmwareUnretractionAdditionalLength
        self.FirmwareRetractionFeedrate = None if copy_from_pos is None else copy_from_pos.FirmwareRetractionFeedrate
        self.FirmwareUnretractionFeedrate = None if copy_from_pos is None else copy_from_pos.FirmwareUnretractionFeedrate
        self.FirmwareZLift = None if copy_from_pos is None else copy_from_pos.FirmwareZLift
        self.HasPositionError = False if copy_from_pos is None else copy_from_pos.HasPositionError
        self.PositionError = None if copy_from_pos is None else copy_from_pos.PositionError
        self.HasHomedPosition = False if copy_from_pos is None else copy_from_pos.HasHomedPosition

        if reset_state:
            # Resets state changes
            self.IsLayerChange = False
            self.IsHeightChange = False
            self.IsTravelOnly = False
            self.IsZHop = False
            self.HasPositionChanged = False
            self.HasStateChanged = False
            self.HasReceivedHomeCommand = False
            self.HasOneFeatureEnabled = False
            self.Features = []
        else:
            # Copy or default states
            self.IsLayerChange = False if copy_from_pos is None else copy_from_pos.IsLayerChange
            self.IsHeightChange = False if copy_from_pos is None else copy_from_pos.IsHeightChange
            self.IsTravelOnly = False if copy_from_pos is None else copy_from_pos.IsTravelOnly
            self.IsZHop = False if copy_from_pos is None else copy_from_pos.IsZHop
            self.HasPositionChanged = False if copy_from_pos is None else copy_from_pos.HasPositionChanged
            self.HasStateChanged = False if copy_from_pos is None else copy_from_pos.HasStateChanged
            self.HasReceivedHomeCommand = False if copy_from_pos is None else copy_from_pos.HasReceivedHomeCommand
            self.HasOneFeatureEnabled = False if copy_from_pos is None else copy_from_pos.HasOneFeatureEnabled
            self.Features = [] if copy_from_pos is None else copy_from_pos.Features

    @staticmethod
    def copy_to(source, target):
        target.parsed_command = source.parsed_command
        target.F = source.F
        target.X = source.X
        target.XOffset = source.XOffset
        target.XHomed = source.XHomed
        target.Y = source.Y
        target.YOffset = source.YOffset
        target.YHomed = source.YHomed
        target.Z = source.Z
        target.ZOffset = source.ZOffset
        target.ZHomed = source.ZHomed
        target.E = source.E
        target.EOffset = source.EOffset
        target.IsRelative = source.IsRelative
        target.IsExtruderRelative = source.IsExtruderRelative
        target.IsMetric = source.IsMetric
        target.LastExtrusionHeight = source.LastExtrusionHeight
        target.Layer = source.Layer
        target.Height = source.Height
        target.IsPrimed = source.IsPrimed
        target.MinimumLayerHeightReached = source.MinimumLayerHeightReached
        target.IsInPosition = source.IsInPosition
        target.InPathPosition = source.InPathPosition
        target.IsTravelOnly = source.IsTravelOnly
        target.Features = source.Features
        target.HasOneFeatureEnabled = source.HasOneFeatureEnabled
        target.FirmwareRetractionLength = source.FirmwareRetractionLength
        target.FirmwareUnretractionAdditionalLength = source.FirmwareUnretractionAdditionalLength
        target.FirmwareRetractionFeedrate = source.FirmwareRetractionFeedrate
        target.FirmwareUnretractionFeedrate = source.FirmwareUnretractionFeedrate
        target.FirmwareZLift = source.FirmwareZLift
        target.HasHomedPosition = source.HasHomedPosition
        target.IsLayerChange = source.IsLayerChange
        target.IsHeightChange = source.IsHeightChange
        target.IsZHop = source.IsZHop
        target.HasPositionChanged = source.HasPositionChanged
        target.HasStateChanged = source.HasStateChanged
        target.HasReceivedHomeCommand = source.HasReceivedHomeCommand
        target.HasPositionError = source.HasPositionError
        target.PositionError = source.PositionError
        return target

    @classmethod
    def create_initial(cls,printer, octoprint_printer_profile):
        initialPos = Pos()
        if printer.e_axis_default_mode in ['absolute', 'relative']:
            initialPos.IsExtruderRelative = True if printer.e_axis_default_mode == 'relative' else False
        else:
            initialPos.IsExtruderRelative = None
        if printer.xyz_axes_default_mode in ['absolute', 'relative']:
            initialPos.IsRelative = True if printer.xyz_axes_default_mode == 'relative' else False
        else:
            initialPos.IsRelative = None
        if printer.units_default in ['inches', 'millimeters']:
            initialPos.IsMetric = True if printer.units_default == 'millimeters' else False
        else:
            initialPos.IsMetric = None

        # default firmware retraction length and feedrate if default_firmware_retractions isenabled
        if printer.default_firmware_retractions:
            initialPos.FirmwareRetractionLength = printer.retract_length
            initialPos.FirmwareUnretractionAdditionalLength = None  # todo:  add this setting
            initialPos.FirmwareRetractionFeedrate = printer.retract_speed
            initialPos.FirmwareUnretractionFeedrate = printer.deretract_speed
        if printer.default_firmware_retractions_zhop:
            initialPos.FirmwareZLift = printer.get_z_hop_for_slicer_type()

        return initialPos

    def is_state_equal(self, pos):
        if (self.XHomed == pos.XHomed and self.YHomed == pos.YHomed
                and self.ZHomed == pos.ZHomed
                and self.IsLayerChange == pos.IsLayerChange
                and self.IsHeightChange == pos.IsHeightChange
                and self.IsZHop == pos.IsZHop
                and self.IsRelative == pos.IsRelative
                and self.IsExtruderRelative == pos.IsExtruderRelative
                and pos.Layer == self.Layer
                and pos.Height == self.Height
                and (
                    (pos.LastExtrusionHeight is None and self.LastExtrusionHeight is None) or
                    pos.LastExtrusionHeight == self.LastExtrusionHeight
                )
                and self.IsPrimed == pos.IsPrimed
                and self.MinimumLayerHeightReached == pos.MinimumLayerHeightReached
                and self.IsInPosition == pos.IsInPosition
                and self.InPathPosition == pos.InPathPosition
                and self.HasOneFeatureEnabled == pos.HasOneFeatureEnabled
                and self.HasPositionError == pos.HasPositionError
                and self.PositionError == pos.PositionError
                and self.HasReceivedHomeCommand == pos.HasReceivedHomeCommand
                and self.IsTravelOnly == pos.IsTravelOnly):
            return True

        return False

    def is_position_equal(self, pos):

        return (
            pos.X == self.X and
            pos.Y == self.Y and
            pos.Z == self.Z
        )

    def to_state_dict(self):
        return {
            "GCode": "" if self.parsed_command is None else self.parsed_command.gcode,
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
            "HasOneFeatureEnabled": self.HasOneFeatureEnabled,
            "InPathPosition": self.InPathPosition,
            "IsPrimed": self.IsPrimed,
            "MinimumLayerHeightReached": self.MinimumLayerHeightReached,
            "HasPositionError": self.HasPositionError,
            "PositionError": self.PositionError,
            "HasReceivedHomeCommand": self.HasReceivedHomeCommand,
            "IsTravelOnly": self.IsTravelOnly
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
            "EOffset": self.EOffset,
            "Features": self.Features,
        }

    def to_dict(self):
        return {
            "GCode": "" if self.parsed_command is None else self.parsed_command.gcode,
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
            "Features": self.Features,
            "InPathPosition": self.InPathPosition,
            "IsPrimed": self.IsPrimed,
            "MinimumLayerHeightReached": self.MinimumLayerHeightReached,
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

    def update_position(
        self,
        x=None,
        y=None,
        z=None,
        e=None,
        f=None,
        force=False,
        tolerance=utility.FLOAT_MATH_EQUALITY_RANGE
    ):

        if f is not None:
            self.F = float(f)
        if force:
            # Force the coordinates in as long as they are provided.
            #
            if x is not None:
                self.X = utility.round_to_value(float(x) + self.XOffset, tolerance)
            if y is not None:
                self.Y = utility.round_to_value(float(y) + self.YOffset, tolerance)
            if z is not None:
                self.Z = utility.round_to_value(float(z) + self.ZOffset, tolerance)
            if e is not None:
                self.E = utility.round_to_value(float(e) + self.EOffset, tolerance)
        else:
            # Update the previous positions if values were supplied
            if x is not None and self.XHomed:
                if self.IsRelative:
                    if self.X is not None:
                        self.X = utility.round_to_value(float(x) + self.X, tolerance)
                else:
                    self.X = utility.round_to_value(float(x) + self.XOffset, tolerance)

            if y is not None and self.YHomed:
                if self.IsRelative:
                    if self.Y is not None:
                        self.Y = utility.round_to_value(float(y) + self.Y, tolerance)
                else:
                    self.Y = utility.round_to_value(float(y) + self.YOffset, tolerance)

            if z is not None and self.ZHomed:
                if self.IsRelative:
                    if self.Z is not None:
                        self.Z = utility.round_to_value(float(z)+self.Z, tolerance)
                else:
                    self.Z = utility.round_to_value(float(z) + self.ZOffset, tolerance)

            if e is not None:
                if self.IsExtruderRelative:
                    if self.E is not None:
                        self.E = utility.round_to_value(float(e) + self.E, tolerance)
                else:
                    self.E = utility.round_to_value(float(e) + self.EOffset, tolerance)

            #if (not utility.is_in_bounds(
            #        bounding_box, self.X, self.XOffset, self.Y , self.YOffset, self.Z, self.ZOffset)):
            #    self.HasPositionError = True
            #    self.PositionError = "Position - Coordinates {0} are out of the printer area!  " \
            #                         "Cannot resume position tracking until the axis is homed, "  \
            #                         "or until absolute coordinates are received.".format(
            #                            get_formatted_coordinates(self.X, self.Y, self.Z, self.E))
            #else:
            #    self.HasPositionError = False
            #    self.PositionError = None

    def distance_to_zlift(self, z_hop, restrict_lift_height=True):
        if self.Z is None or self.LastExtrusionHeight is None:
            return None

        current_lift = self.Z - self.LastExtrusionHeight
        amount_to_lift = z_hop - current_lift

        if restrict_lift_height:
            if amount_to_lift < utility.FLOAT_MATH_EQUALITY_RANGE:
                return 0
            elif amount_to_lift > z_hop:
                return z_hop
            else:
                # we are in-between 0 and z_hop, calculate lift
                return amount_to_lift

        return amount_to_lift

    def x_with_offset(self):
        return utility.coordinate_to_offset_position(self.X, self.XOffset)

    def y_with_offset(self):
        return utility.coordinate_to_offset_position(self.Y, self.YOffset)

    def z_with_offset(self):
        return utility.coordinate_to_offset_position(self.Z, self.ZOffset)


class Position(object):
    def __init__(self, octolapse_settings, octoprint_printer_profile,
                 g90_influences_extruder):
        self.Settings = octolapse_settings
        self.Printer = self.Settings.profiles.current_printer()

        self.Snapshot = self.Settings.profiles.current_snapshot()
        self.SlicerFeatures = SlicerPrintFeatures(self.Printer.get_current_slicer_settings(), self.Snapshot)
        self.OctoprintPrinterProfile = octoprint_printer_profile
        self.Origin = {
            "X": self.Printer.origin_x,
            "Y": self.Printer.origin_y,
            "Z": self.Printer.origin_z
        }

        self.BoundingBox = utility.get_bounding_box(self.Printer,
                                                    octoprint_printer_profile)
        self.PrinterTolerance = utility.FLOAT_MATH_EQUALITY_RANGE
        self.Positions = deque(maxlen=5)
        self.SavedPosition = None
        self.HasRestrictedPosition = (
            len(self.Snapshot.position_restrictions) > 0 and self.Snapshot.position_restrictions_enabled
        )
        self.Extruder = Extruder(octolapse_settings)
        if self.Printer.g90_influences_extruder in ['true', 'false']:
            self.G90InfluencesExtruder = True if self.Printer.g90_influences_extruder == 'true' else False
        else:
            self.G90InfluencesExtruder = g90_influences_extruder

        self.gcode_generation_settings = self.Printer.get_current_state_detection_settings()
        assert (isinstance(self.gcode_generation_settings, OctolapseGcodeSettings))

        self.ZHop = 0 if self.gcode_generation_settings.z_lift_height is None else self.gcode_generation_settings.z_lift_height

        self.LocationDetectionCommands = []
        self.create_location_detection_commands()

        self.current_pos = Pos.create_initial(self.Printer, self.OctoprintPrinterProfile)
        self.previous_pos = Pos.create_initial(self.Printer, self.OctoprintPrinterProfile)

        self.Positions.append(self.previous_pos)
        self.Positions.append(self.current_pos)

        self.gcode_functions = self.get_gcode_functions()
        self.extruder_update_commands = {'G0', 'G1', 'G3', 'G4' ,'G10' ,'G11' ,'G28' ,'G80' ,'M109' ,'M116' ,'M190', 'M191'}

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
        # remove support for G161 and G162 until they are better understood
        # if "G161" not in self.LocationDetectionCommands:
        #     self.LocationDetectionCommands.append("G161")
        # if "G162" not in self.LocationDetectionCommands:
        #     self.LocationDetectionCommands.append("G162")

    def update_position(self,
                        x=None,
                        y=None,
                        z=None,
                        e=None,
                        f=None,
                        force=False):
        num_positions = len(self.Positions)
        if num_positions == 0:
            return
        self.current_pos.update_position(x, y, z, e, f, force)

    def to_position_dict(self):
        if len(self.Positions) > 0:
            return self.current_pos.to_dict()
        return None

    def to_state_dict(self):
        if len(self.Positions) > 0:
            return self.current_pos.to_state_dict()
        return None

    def z_delta(self, pos=None, index=None):
        if index is not None and pos is not None and index < len(self.Positions):
            self.previous_pos = self.get_position(index)
            return pos.Height - self.previous_pos.Height
        else:
            return self.current_pos.Height - self.previous_pos.Height

    def distance_to_zlift(self, index=0):
        pos = self.get_position(index)
        assert(isinstance(pos, Pos))

        if pos is None:
            return None

        # get the lift amount, but don't restrict it so we can log properly
        amount_to_lift = pos.distance_to_zlift(self.ZHop, False)

        if amount_to_lift < 0:
            # the current lift is negative
            self.Settings.Logger.log_warning("position.py - A 'distance_to_zlift' was requested, "
                                                              "but the current lift is already above the z_hop height.")
            return 0
        elif amount_to_lift > self.ZHop:
            # For some reason we're lower than we expected
            self.Settings.Logger.log_warning("position.py - A 'distance_to_zlift' was requested, "
                                                              "but was found to be more than the z_hop height.")
            return self.ZHop
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

    def features(self, index=0):
        pos = self.get_position(index)
        if pos is None:
            return None
        return pos.Features

    def has_one_feature_enabled(self, index=0):
        pos = self.get_position(index)
        if pos is None:
            return False
        return pos.HasOneFeatureEnabled

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

    def has_position_state_errors(self, index=0):
        if (not self.has_homed_axes(index)
            or self.is_relative(index) is None
            or self.is_extruder_relative(index) is None
            or not self.is_metric(index)
            or self.has_position_error(index)
        ):
            return True
        return False

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
           if cmd in self.LocationDetectionCommands:
                return True
        return False

    def requires_location_detection(self, index=0):
        pos = self.get_position(index)
        if pos is None or pos.parsed_command is None:
            return False

        if self.command_requires_location_detection(pos.parsed_command.cmd):
            return True
        return False

    def undo_update(self):

        # set pos to the previous pos and pop the current position
        if len(self.Positions) < 2:
            raise Exception("Cannot undo updates when there is less than one position in the position queue.")
        previous_position = self.Positions.popleft()
        previous_extruder = self.Extruder.undo_update()
        self.current_pos = self.Positions[0]
        self.previous_pos = self.Positions[1]
        return previous_position, previous_extruder


    def get_position(self, index=0):
        if len(self.Positions) > index:
            return self.Positions[index]
        return None

    def get_gcode_functions(self):
        return {
            "G0": self.process_g0_g1,
            "G1": self.process_g0_g1,
            "G2": self.process_g2_g3,
            "G3": self.process_g2_g3,
            "G10": self.process_g10,
            "G11": self.process_g11,
            "G20": self.process_g20,
            "G21": self.process_g21,
            "G28": self.process_g28,
            "G90": self.process_g90,
            "G91": self.process_g91,
            "G92": self.process_g92,
            "M82": self.process_m82,
            "M83": self.process_m83,
            "M207": self.process_m207,
            "M208": self.process_m208
        }

    def update(self, parsed_command):

        num_positions = len(self.Positions)

        # swap positions
        Pos.copy_to(self.current_pos, self.previous_pos)
        # create copy of the current pos for the previous pos
        self.current_pos = Pos(self.previous_pos, reset_state=True)
        # set the pos gcode cmd
        self.current_pos.parsed_command = parsed_command

        # apply the cmd to the position tracker
        cmd = self.current_pos.parsed_command.cmd
        if cmd is not None and self.current_pos.parsed_command.cmd in self.gcode_functions:
            if self.current_pos.parsed_command.cmd in Commands.CommandsRequireMetric and not self.current_pos.IsMetric:
                self.current_pos.HasPositionError = True
                self.current_pos.PositionError = "Units are not metric.  Unable to continue print."
            else:
                # call the gcode function
                self.gcode_functions[cmd]()

        ########################################
        # Update the extruder monitor.
        # todo: should we use 0 as a tolerance here?
        should_update_extruder = False

        e_relative = self.e_relative_pos()
        if e_relative != 0 or parsed_command.cmd in self.extruder_update_commands:
            should_update_extruder = True

        self.Extruder.update(e_relative, update_state=should_update_extruder)

        # Have the XYZ positions or states changed?
        self.current_pos.HasPositionChanged = not self.current_pos.is_position_equal(self.previous_pos)
        self.current_pos.HasStateChanged = not self.current_pos.is_state_equal(self.previous_pos)

        if not self.current_pos.HasHomedPosition:
            self.current_pos.HasHomedPosition = (
                self.current_pos.XHomed and self.current_pos.YHomed and self.current_pos.ZHomed and
                self.current_pos.IsMetric and
                self.current_pos.X is not None and
                self.current_pos.Y is not None and
                self.current_pos.Z is not None and
                self.current_pos.IsRelative is not None and
                self.current_pos.IsExtruderRelative is not None
             )

        if (
            self.current_pos.HasHomedPosition and
            self.previous_pos.HasHomedPosition and
            (self.Extruder.current_state.HasChanged or self.current_pos.HasPositionChanged)
        ):
            # If we have a homed for the current and previous position, and either the exturder or position has changed

            if self.HasRestrictedPosition:
                # If we're using restricted positions, calculate intersections and determine if we are in position
                can_calculate_intersections = self.current_pos.parsed_command.cmd in ["G0", "G1"]
                _is_in_position, _intersections = self.calculate_path_intersections(
                    self.Snapshot.position_restrictions,
                    self.current_pos.X,
                    self.current_pos.Y,
                    self.previous_pos.X,
                    self.previous_pos.Y,
                    can_calculate_intersections
                )
                if _is_in_position:
                    self.current_pos.IsInPosition = _is_in_position

                else:
                    self.current_pos.IsInPosition = False
                    self.current_pos.InPathPosition = _intersections
            else:
                self.current_pos.IsInPosition = True

            # calculate LastExtrusionHeight and Height
            # If we are extruding on a higher level, or if retract is enabled and the nozzle is primed
            # adjust the last extrusion height
            if (
                self.Extruder.current_state.IsExtruding

            ):
                self.current_pos.LastExtrusionHeight = self.current_pos.Z

                if not self.current_pos.IsPrimed:
                    # We haven't primed yet, check to see if we have priming height restrictions
                    if self.Printer.priming_height > 0:
                        # if a priming height is configured, see if we've extruded below the  height
                        if self.current_pos.LastExtrusionHeight < self.Printer.priming_height:
                            self.current_pos.IsPrimed = True
                    else:
                        # if we have no priming height set, just set IsPrimed = true.
                        self.current_pos.IsPrimed = True

                if not self.current_pos.MinimumLayerHeightReached:
                    # see if we've extruded at the minimum layer height.

                    if self.Printer.minimum_layer_height > 0:
                        # if a priming height is configured, see if we've extruded below the  height
                        if self.current_pos.LastExtrusionHeight >= self.Printer.minimum_layer_height:
                            self.current_pos.MinimumLayerHeightReached = True
                    else:
                        # if we have no priming height set, just set IsPrimed = true.
                        self.current_pos.MinimumLayerHeightReached = True


                # make sure we are primed before calculating height/layers
                if self.current_pos.IsPrimed:
                    if self.current_pos.Height is None or self.current_pos.Z > self.previous_pos.Height:
                        self.current_pos.Height = self.current_pos.Z
                    # calculate layer change
                    if (
                        self.current_pos.MinimumLayerHeightReached
                        and (
                            self.current_pos.Height - self.previous_pos.Height > 0
                            or self.current_pos.Layer == 0
                        )
                    ):
                        # Todo:  Is this the layer change?  Looks to me like the extrusion length is 0!
                        self.current_pos.IsLayerChange = True
                        self.current_pos.Layer += 1
                    else:
                        self.current_pos.IsLayerChange = False

            # Calculate ZHop based on last extrusion height
            if self.current_pos.LastExtrusionHeight is not None:
                # calculate lift, taking into account floating point
                # rounding
                distance_to_lift = self.current_pos.distance_to_zlift(self.ZHop)

                # todo:  replace rounding with a call to is close or greater than utility function
                is_lifted = distance_to_lift <= 0.0 and not (
                    self.Extruder.current_state.IsExtruding
                    or self.Extruder.current_state.IsExtrudingStart
                    or self.Extruder.current_state.IsPrimed
                )
                if is_lifted or self.ZHop == 0:
                    self.current_pos.IsZHop = True

        # Update Feature Detection
        if self.current_pos.F is not None:
            # see if at least one feature is enabled, or if feature detection is disabled
            self.current_pos.HasOneFeatureEnabled = self.SlicerFeatures.is_one_feature_enabled(self.current_pos.F, self.current_pos.Layer)

        self.Positions.appendleft(self.current_pos)

    def process_g0_g1(self):
        # Movement

        x = self.current_pos.parsed_command.parameters[
            "X"] if "X" in self.current_pos.parsed_command.parameters else None
        y = self.current_pos.parsed_command.parameters[
            "Y"] if "Y" in self.current_pos.parsed_command.parameters else None
        z = self.current_pos.parsed_command.parameters[
            "Z"] if "Z" in self.current_pos.parsed_command.parameters else None
        e = self.current_pos.parsed_command.parameters[
            "E"] if "E" in self.current_pos.parsed_command.parameters else None
        f = self.current_pos.parsed_command.parameters[
            "F"] if "F" in self.current_pos.parsed_command.parameters else None

        # If we're moving on the X/Y plane only, mark this position as travel only
        self.current_pos.IsTravelOnly = e is None and z is None and (
            x is not None or y is not None
        )

        if x is not None or y is not None or z is not None or f is not None:
            if self.current_pos.IsRelative is not None:
                if self.current_pos.HasPositionError and not self.current_pos.IsRelative:
                    self.current_pos.HasPositionError = False
                    self.current_pos.PositionError = ""
                self.current_pos.update_position(x, y, z, e=None, f=f)
            else:
                self.Settings.Logger.log_position_command_received(
                    "Position - Unable to update the X/Y/Z axis position, the axis mode ("
                    "relative/absolute) has not been explicitly set via G90/G91. "
                )
                self.current_pos.HasPositionError = True
                self.current_pos.PositionError = "XYZ movement was detected, but the axis mode has not been set.  Please add" \
                                                 " a G90 or G91 to the top of your start gcode.  " \
                                                 "<a href=\"https://github.com/FormerLurker/Octolapse/wiki/Troubleshooting" \
                                                 "#for-xyz-choose-one-of-the-following-options\" target=\"_blank\">See this " \
                                                 "guide for details:  </a>"

        if e is not None:
            if self.current_pos.IsExtruderRelative is not None:
                if self.current_pos.HasPositionError and not self.current_pos.IsExtruderRelative:
                    self.current_pos.HasPositionError = False
                    self.current_pos.PositionError = ""
                self.current_pos.update_position(
                    x=None,
                    y=None,
                    z=None,
                    e=e,
                    f=None)
            else:
                self.Settings.Logger.log_error(
                    "Position - Unable to update the extruder position, the extruder mode ("
                    "relative/absolute) has been selected (absolute/relative). "
                )

    def process_g2_g3(self):
        # Movement Type
        movement_type = ""
        if self.current_pos.parsed_command.cmd == "G2":
            movement_type = "clockwise"
            self.Settings.Logger.log_position_command_received("Received G2 - Clockwise Arc")
        else:
            movement_type = "counter-clockwise"
            self.Settings.Logger.log_position_command_received("Received G3 - Counter-Clockwise Arc")

        x = self.current_pos.parsed_command.parameters[
            "X"] if "X" in self.current_pos.parsed_command.parameters else None
        y = self.current_pos.parsed_command.parameters[
            "Y"] if "Y" in self.current_pos.parsed_command.parameters else None
        i = self.current_pos.parsed_command.parameters[
            "I"] if "I" in self.current_pos.parsed_command.parameters else None
        j = self.current_pos.parsed_command.parameters[
            "J"] if "J" in self.current_pos.parsed_command.parameters else None
        r = self.current_pos.parsed_command.parameters[
            "R"] if "R" in self.current_pos.parsed_command.parameters else None
        e = self.current_pos.parsed_command.parameters[
            "E"] if "E" in self.current_pos.parsed_command.parameters else None
        f = self.current_pos.parsed_command.parameters[
            "F"] if "F" in self.current_pos.parsed_command.parameters else None

        # If we're moving on the X/Y plane only, mark this position as travel only
        self.current_pos.IsTravelOnly = e is None

        can_update_position = False
        if r is not None and (i is not None or j is not None):
            self.Settings.Logger.log_error(
                "Received {0} - but received R and either I or J, which is not allowed.".format(
                    self.current_pos.parsed_command.cmd))
        elif i is not None or j is not None:
            # IJ Form
            if x is not None and y is not None:
                # not a circle, the position has changed
                can_update_position = True
                self.Settings.Logger.log_info(
                    "Cannot yet calculate position restriction intersections when G2/G3.")
        elif r is not None:
            # R Form
            if x is None and y is None:
                self.Settings.Logger.log_error(
                    "Received {0} - but received R without x or y, which is not allowed."
                        .format(self.current_pos.parsed_command.cmd)
                )
            else:
                can_update_position = True
                self.Settings.Logger.log_info(
                    "Cannot yet calculate position restriction intersections when G2/G3.")

        if can_update_position:
            if x is not None and y is not None:
                if self.current_pos.IsRelative is not None:
                    if self.current_pos.HasPositionError and not self.current_pos.IsRelative:
                        self.current_pos.HasPositionError = False
                        self.current_pos.PositionError = ""
                    self.current_pos.update_position(self.BoundingBox, x, y, z=None, e=None, f=f)
                else:
                    self.Settings.Logger.log_position_command_received(
                        "Position - Unable to update the X/Y/Z axis position, the axis mode ("
                        "relative/absolute) has not been explicitly set via G90/G91. "
                    )
                    self.current_pos.HasPositionError = True
                    self.current_pos.PositionError = "XYZ movement was detected, but the axis mode has not been set.  Please add" \
                                                     " a G90 or G91 to the top of your start gcode.  " \
                                                     "<a href=\"https://github.com/FormerLurker/Octolapse/wiki/Troubleshooting" \
                                                     "#for-xyz-choose-one-of-the-following-options\" target=\"_blank\">See this " \
                                                     "guide for details:  </a>"
            if e is not None:
                if self.current_pos.IsExtruderRelative is not None:
                    if self.current_pos.HasPositionError and not self.current_pos.IsExtruderRelative:
                        self.current_pos.HasPositionError = False
                        self.current_pos.PositionError = ""
                    self.current_pos.update_position(
                        self.BoundingBox,
                        x=None,
                        y=None,
                        z=None,
                        e=e,
                        f=None)
                else:
                    self.Settings.Logger.log_error(
                        "Position - Unable to update the extruder position, the extruder mode ("
                        "relative/absolute) has been selected (absolute/relative). "
                    )

            message = "Position Change - {0} - {1} {2} Arc From(X:{3},Y:{4},Z:{5},E:{6}) - To(X:{7},Y:{8}," \
                      "Z:{9},E:{10})"
            if self.previous_pos is None:
                message = message.format(
                    self.current_pos.parsed_command.gcode, "Relative" if self.current_pos.IsRelative else "Absolute", movement_type
                    , "None", "None",
                    "None", "None", self.current_pos.X, self.current_pos.Y, self.current_pos.Z, self.current_pos.E)
            else:
                message = message.format(
                    self.current_pos.parsed_command.gcode, "Relative" if self.current_pos.IsRelative else "Absolute", movement_type,
                    self.previous_pos.X,
                    self.previous_pos.Y, self.previous_pos.Z, self.previous_pos.E, self.current_pos.X,
                    self.current_pos.Y, self.current_pos.Z, self.current_pos.E)
            self.Settings.Logger.log_position_change(
                message)

    def process_g10(self):
        if "P" not in self.current_pos.parsed_command.parameters:
            e = 0 if self.current_pos.FirmwareRetractionLength is None else -1.0 * self.current_pos.FirmwareRetractionLength
            previous_extruder_relative = self.current_pos.IsExtruderRelative
            previous_relative = self.current_pos.IsRelative

            self.current_pos.IsRelative = True
            self.current_pos.IsExtruderRelative = True
            self.current_pos.update_position(self.BoundingBox, x=None, y=None, z=self.current_pos.FirmwareZLift, e=e,
                                             f=self.current_pos.FirmwareRetractionFeedrate)
            self.current_pos.IsRelative = previous_relative
            self.current_pos.IsExtruderRelative = previous_extruder_relative

    def process_g11(self):
        lift_distance = 0 if self.current_pos.FirmwareZLift is None else -1.0 * self.current_pos.FirmwareZLift
        e = 0 if self.current_pos.FirmwareRetractionLength is None else self.current_pos.FirmwareRetractionLength

        if self.current_pos.FirmwareUnretractionFeedrate is not None:
            f = self.current_pos.FirmwareUnretractionFeedrate
        else:
            f = self.current_pos.FirmwareRetractionFeedrate

        if self.current_pos.FirmwareUnretractionAdditionalLength:
            e = e + self.current_pos.FirmwareUnretractionAdditionalLength

        previous_extruder_relative = self.current_pos.IsExtruderRelative
        previous_relative = self.current_pos.IsRelative

        self.current_pos.IsRelative = True
        self.current_pos.IsExtruderRelative = True
        self.current_pos.update_position(self.BoundingBox, x=None, y=None, z=lift_distance,
                                         e=e, f=f)
        self.current_pos.IsRelative = previous_relative
        self.current_pos.IsExtruderRelative = previous_extruder_relative

    def process_g20(self):
        # change units to inches
        if self.current_pos.IsMetric is None or self.current_pos.IsMetric:
            self.current_pos.IsMetric = False

    def process_g21(self):
        # change units to millimeters
        if self.current_pos.IsMetric is None or not self.current_pos.IsMetric:
            self.current_pos.IsMetric = True

    def process_g28(self):
        # Home
        self.current_pos.HasReceivedHomeCommand = True
        x = True if "X" in self.current_pos.parsed_command.parameters else None
        y = True if "Y" in self.current_pos.parsed_command.parameters else None
        z = True if "Z" in self.current_pos.parsed_command.parameters else None
        # ignore the W parameter, it's used in Prusa firmware to indicate a home without mesh bed leveling
        # w = parameters["W"] if "W" in parameters else None

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
            self.current_pos.XHomed = True
            self.current_pos.X = self.Origin["X"] if not self.Printer.auto_detect_position else None
        if y_homed:
            self.current_pos.YHomed = True
            self.current_pos.Y = self.Origin[
                "Y"] if not self.Printer.auto_detect_position else None

        if z_homed:
            self.current_pos.ZHomed = True
            self.current_pos.Z = self.Origin[
                "Z"] if not self.Printer.auto_detect_position else None

        self.current_pos.HasPositionError = False
        self.current_pos.PositionError = None
        # we must do this in case we have more than one home command
        # TODO: do we really?  This seems fishy, need to look into -- answer: hopefully not, it messes with homing
        # self.previous_pos = Pos(self.current_pos)

    def process_g90(self):
        # change x,y,z to absolute
        if self.current_pos.IsRelative is None or self.current_pos.IsRelative:
            self.current_pos.IsRelative = False

        if self.G90InfluencesExtruder:
            if self.current_pos.IsExtruderRelative is None or self.current_pos.IsExtruderRelative:
                self.current_pos.IsExtruderRelative = False

    def process_g91(self):
        # change x,y,z to relative
        if self.current_pos.IsRelative is None or not self.current_pos.IsRelative:
            self.current_pos.IsRelative = True

        # for some firmwares we need to switch the extruder to
        # absolute
        # coordinates
        # as well
        if self.G90InfluencesExtruder:
            if self.current_pos.IsExtruderRelative is None or not self.current_pos.IsExtruderRelative:
                self.current_pos.IsExtruderRelative = True

    def process_g92(self):# Set Position (offset)

        x = self.current_pos.parsed_command.parameters["X"] if "X" in self.current_pos.parsed_command.parameters else None
        y = self.current_pos.parsed_command.parameters["Y"] if "Y" in self.current_pos.parsed_command.parameters else None
        z = self.current_pos.parsed_command.parameters["Z"] if "Z" in self.current_pos.parsed_command.parameters else None
        e = self.current_pos.parsed_command.parameters["E"] if "E" in self.current_pos.parsed_command.parameters else None
        o = True if "O" in self.current_pos.parsed_command.parameters else False

        if o:
            self.current_pos.XHomed = True
            self.current_pos.YHomed = True
            self.current_pos.ZHomed = True

        if not o and x is None and y is None and z is None and e is None:
            if self.current_pos.X is not None:
                self.current_pos.XOffset = self.current_pos.X
            if self.current_pos.Y is not None:
                self.current_pos.YOffset = self.current_pos.Y
            if self.current_pos.Z is not None:
                self.current_pos.ZOffset = self.current_pos.Z
            if self.current_pos.E is not None:
                self.current_pos.EOffset = self.current_pos.E

        # set the offsets if they are provided
        if x is not None:
            if self.current_pos.X is not None and self.current_pos.XHomed:
                self.current_pos.XOffset = self.current_pos.X - utility.get_float(x, 0)
            else:
                self.current_pos.X = utility.get_float(x, 0)
                self.current_pos.XOffset = 0

            if o:
                self.current_pos.XHomed = True
        if y is not None:
            if self.current_pos.Y is not None and self.current_pos.YHomed:
                self.current_pos.YOffset = self.current_pos.Y - utility.get_float(y, 0)
            else:
                self.current_pos.Y = utility.get_float(y, 0)
                self.current_pos.YOffset = 0

            if o:
                self.current_pos.YHomed = True

        if z is not None:
            if self.current_pos.Z is not None and self.current_pos.ZHomed:
                self.current_pos.ZOffset = self.current_pos.Z - utility.get_float(z, 0)
            else:
                self.current_pos.Z = utility.get_float(z, 0)
                self.current_pos.ZOffset = 0

            if o:
                self.current_pos.ZHomed = True

        if e is not None:
            if self.current_pos.E is not None:
                self.current_pos.EOffset = self.current_pos.E - utility.get_float(e, 0)
            else:
                self.current_pos.E = utility.get_float(e, 0)

    def process_m82(self):
        # Extruder - Set Absolute
        if self.current_pos.IsExtruderRelative is None or self.current_pos.IsExtruderRelative:
            self.current_pos.IsExtruderRelative = False

    def process_m83(self):
        # Extruder - Set Relative
        if self.current_pos.IsExtruderRelative is None or not self.current_pos.IsExtruderRelative:
            self.current_pos.IsExtruderRelative = True

    def process_m207(self):
        # Firmware Retraction Tracking
        if "S" in self.current_pos.parsed_command.parameters:
            self.current_pos.FirmwareRetractionLength = self.current_pos.parsed_command.parameters["S"]
        if "R" in self.current_pos.parsed_command.parameters:
            self.current_pos.FirmwareUnretractionAdditionalLength = self.current_pos.parsed_command.parameters["R"]
        if "F" in self.current_pos.parsed_command.parameters:
            self.current_pos.FirmwareRetractionFeedrate = self.current_pos.parsed_command.parameters["F"]
        if "T" in self.current_pos.parsed_command.parameters:
            self.current_pos.FirmwareUnretractionFeedrate = self.current_pos.parsed_command.parameters["T"]
        if "Z" in self.current_pos.parsed_command.parameters:
            self.current_pos.FirmwareZLift = self.current_pos.parsed_command.parameters["Z"]

    def process_m208(self):
        # Firmware Retraction Tracking
        if "S" in self.current_pos.parsed_command.parameters:
            self.current_pos.FirmwareUnretractionAdditionalLength = self.current_pos.parsed_command.parameters["S"]
        if "F" in self.current_pos.parsed_command.parameters:
            self.current_pos.FirmwareUnretractionFeedrate = self.current_pos.parsed_command.parameters["F"]

    # Eventually this code will support the G161 and G162 commands
    # Hold this code for the future
    # Not ready to be released as of now.
    # def _g161_received(self, pos):
    #     # Home
    #     pos.HasReceivedHomeCommand = True
    #     x = True if "X" in pos.parsed_command.parameters else None
    #     y = True if "Y" in pos.parsed_command.parameters else None
    #     z = True if "Z" in pos.parsed_command.parameters else None
    #     f = True if "F" in pos.parsed_command.parameters else None
    #     # ignore the W parameter, it's used in Prusa firmware to indicate a home without mesh bed leveling
    #     # w = parameters["W"] if "W" in parameters else None
    #
    #     x_homed = False
    #     y_homed = False
    #     z_homed = False
    #     if x is not None:
    #         x_homed = True
    #     if y is not None:
    #         y_homed = True
    #     if z is not None:
    #         z_homed = True
    #
    #     if f is not None:
    #         pos.F = f
    #
    #     # if there are no x,y or z parameters, we're homing all axes
    #     if x is None and y is None and z is None:
    #         x_homed = True
    #         y_homed = True
    #         z_homed = True
    #
    #     home_strings = []
    #     if x_homed:
    #         pos.XHomed = True
    #         pos.X = self.Origin["X"] if not self.Printer.auto_detect_position else None
    #         if pos.X is None:
    #             home_strings.append("Homing X to Unknown Origin.")
    #         else:
    #             home_strings.append("Homing X to {0}.".format(
    #                 get_formatted_coordinate(pos.X)))
    #     if y_homed:
    #         pos.YHomed = True
    #         pos.Y = self.Origin["Y"] if not self.Printer.auto_detect_position else None
    #         if pos.Y is None:
    #             home_strings.append("Homing Y to Unknown Origin.")
    #         else:
    #             home_strings.append("Homing Y to {0}.".format(
    #                 get_formatted_coordinate(pos.Y)))
    #     if z_homed:
    #         pos.ZHomed = True
    #         pos.Z = self.Origin["Z"] if not self.Printer.auto_detect_position else None
    #         if pos.Z is None:
    #             home_strings.append("Homing Z to Unknown Origin.")
    #         else:
    #             home_strings.append("Homing Z to {0}.".format(
    #                 get_formatted_coordinate(pos.Z)))
    #
    #     self.Settings.Logger.log_position_command_received(
    #         "Received G161 - ".format(" ".join(home_strings)))
    #     pos.HasPositionError = False
    #     pos.PositionError = None
    #
    # def _g162_received(self, pos):
    #     # Home
    #     pos.HasReceivedHomeCommand = True
    #     x = True if "X" in pos.parsed_command.parameters else None
    #     y = True if "Y" in pos.parsed_command.parameters else None
    #     z = True if "Z" in pos.parsed_command.parameters else None
    #     f = True if "F" in pos.parsed_command.parameters else None
    #
    #     x_homed = False
    #     y_homed = False
    #     z_homed = False
    #     if x is not None:
    #         x_homed = True
    #     if y is not None:
    #         y_homed = True
    #     if z is not None:
    #         z_homed = True
    #
    #     if f is not None:
    #         pos.F = f
    #
    #     # if there are no x,y or z parameters, we're homing all axes
    #     if x is None and y is None and z is None:
    #         x_homed = True
    #         y_homed = True
    #         z_homed = True
    #
    #     home_strings = []
    #     if x_homed:
    #         pos.XHomed = True
    #         pos.X = self.Origin["X"] if not self.Printer.auto_detect_position else None
    #         if pos.X is None:
    #             home_strings.append("Homing X to Unknown Origin.")
    #         else:
    #             home_strings.append("Homing X to {0}.".format(
    #                 get_formatted_coordinate(pos.X)))
    #     if y_homed:
    #         pos.YHomed = True
    #         pos.Y = self.Origin["Y"] if not self.Printer.auto_detect_position else None
    #         if pos.Y is None:
    #             home_strings.append("Homing Y to Unknown Origin.")
    #         else:
    #             home_strings.append("Homing Y to {0}.".format(
    #                 get_formatted_coordinate(pos.Y)))
    #     if z_homed:
    #         pos.ZHomed = True
    #         pos.Z = self.Origin["Z"] if not self.Printer.auto_detect_position else None
    #         if pos.Z is None:
    #             home_strings.append("Homing Z to Unknown Origin.")
    #         else:
    #             home_strings.append("Homing Z to {0}.".format(
    #                 get_formatted_coordinate(pos.Z)))
    #
    #     self.Settings.Logger.log_position_command_received(
    #         "Received G162 - ".format(" ".join(home_strings)))
    #     pos.HasPositionError = False
    #     pos.PositionError = None

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

    def e_relative_pos(self):
        if len(self.Positions) < 2:
            return None
        return self.current_pos.E - self.previous_pos.E

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

    def calculate_path_intersections(self, restrictions, x, y, previous_x, previous_y, can_calculate_intersections):

        if self.calculate_is_in_position(
            restrictions,
            x,
            y,
            self.Printer.printer_position_confirmation_tolerance
        ):
            return True, None

        if previous_x is None or previous_y is None:
            return False, False

        if not can_calculate_intersections:
            return False, None

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
