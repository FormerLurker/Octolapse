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
                 "Height", "IsPrinterPrimed", "MinimumLayerHeightReached", "IsInPosition", "InPathPosition",
                 "IsTravelOnly",
                 "Features", "HasOneFeatureEnabled", "FirmwareRetractionLength", "FirmwareUnretractionAdditionalLength",
                 "FirmwareRetractionFeedrate", "FirmwareUnretractionFeedrate", "FirmwareZLift", "HasHomedPosition",
                 "IsLayerChange", "IsHeightChange", "IsZHop", "HasPositionChanged", "HasStateChanged",
                 "HasReceivedHomeCommand", "HasPositionError", "PositionError", 'ERelative', 'ExtrusionLength',
                 'ExtrusionLengthTotal', 'RetractionLength', 'DeretractionLength', 'IsExtrudingStart', 'IsExtruding',
                 'IsPrimed', 'IsRetractingStart', 'IsRetracting', 'IsRetracted', 'IsPartiallyRetracted',
                 'IsDeretractingStart', 'IsDeretracting', 'IsDeretracted'
                 ]

    def __init__(self, copy_from_pos=None, reset_state=False):

        if copy_from_pos is not None:
            self.parsed_command = copy_from_pos.parsed_command
            self.F = copy_from_pos.F
            self.X = copy_from_pos.X
            self.XOffset = copy_from_pos.XOffset
            self.XHomed = copy_from_pos.XHomed
            self.Y = copy_from_pos.Y
            self.YOffset = copy_from_pos.YOffset
            self.YHomed = copy_from_pos.YHomed
            self.Z = copy_from_pos.Z
            self.ZOffset = copy_from_pos.ZOffset
            self.ZHomed = copy_from_pos.ZHomed
            self.E = copy_from_pos.E
            self.EOffset = copy_from_pos.EOffset
            self.IsRelative = copy_from_pos.IsRelative
            self.IsExtruderRelative = copy_from_pos.IsExtruderRelative
            self.IsMetric = copy_from_pos.IsMetric
            self.LastExtrusionHeight = copy_from_pos.LastExtrusionHeight
            self.Layer = copy_from_pos.Layer
            self.Height = copy_from_pos.Height
            self.IsPrinterPrimed = copy_from_pos.IsPrinterPrimed
            self.MinimumLayerHeightReached = copy_from_pos.MinimumLayerHeightReached
            self.FirmwareRetractionLength = copy_from_pos.FirmwareRetractionLength
            self.FirmwareUnretractionAdditionalLength = copy_from_pos.FirmwareUnretractionAdditionalLength
            self.FirmwareRetractionFeedrate = copy_from_pos.FirmwareRetractionFeedrate
            self.FirmwareUnretractionFeedrate = copy_from_pos.FirmwareUnretractionFeedrate
            self.FirmwareZLift = copy_from_pos.FirmwareZLift
            self.HasPositionError = copy_from_pos.HasPositionError
            self.PositionError = copy_from_pos.PositionError
            self.HasHomedPosition = copy_from_pos.HasHomedPosition

            ####### Extruder Tracking
            self.ERelative = copy_from_pos.E
            self.ExtrusionLength = copy_from_pos.ExtrusionLength
            self.ExtrusionLengthTotal = copy_from_pos.ExtrusionLengthTotal
            self.RetractionLength = copy_from_pos.RetractionLength
            self.DeretractionLength = copy_from_pos.DeretractionLength
            self.IsExtrudingStart = copy_from_pos.IsExtrudingStart
            self.IsExtruding = copy_from_pos.IsExtruding
            self.IsPrimed = copy_from_pos.IsPrimed
            self.IsRetractingStart = copy_from_pos.IsRetractingStart
            self.IsRetracting = copy_from_pos.IsRetracting
            self.IsRetracted = copy_from_pos.IsRetracted
            self.IsPartiallyRetracted = copy_from_pos.IsPartiallyRetracted
            self.IsDeretractingStart = copy_from_pos.IsDeretractingStart
            self.IsDeretracting = copy_from_pos.IsDeretracting
            self.IsDeretracted = copy_from_pos.IsDeretracted
            self.IsInPosition = copy_from_pos.IsInPosition
            self.HasOneFeatureEnabled = copy_from_pos.HasOneFeatureEnabled
            self.InPathPosition = copy_from_pos.InPathPosition
            self.IsZHop = copy_from_pos.IsZHop
            self.Features = copy_from_pos.Features
            #######
            if reset_state:
                # Resets state changes
                self.IsLayerChange = False
                self.IsHeightChange = False
                self.IsTravelOnly = False
                self.HasPositionChanged = False
                self.HasStateChanged = False
                self.HasReceivedHomeCommand = False
                self.Features = []
            else:
                # Copy or default states
                self.IsLayerChange = copy_from_pos.IsLayerChange
                self.IsHeightChange = copy_from_pos.IsHeightChange
                self.IsTravelOnly = copy_from_pos.IsTravelOnly
                self.HasPositionChanged = copy_from_pos.HasPositionChanged
                self.HasStateChanged = copy_from_pos.HasStateChanged
                self.HasReceivedHomeCommand = copy_from_pos.HasReceivedHomeCommand

        else:
            self.parsed_command = None
            self.F = None
            self.X = None
            self.XOffset = 0
            self.XHomed = False
            self.Y = None
            self.YOffset = 0
            self.YHomed = False
            self.Z = None
            self.ZOffset = 0
            self.ZHomed = False
            self.E = 0
            self.EOffset = 0
            self.IsRelative = False
            self.IsExtruderRelative = False
            self.IsMetric = True
            self.LastExtrusionHeight = None
            self.Layer = 0
            self.Height = 0
            self.IsPrinterPrimed = False
            self.MinimumLayerHeightReached = False
            self.FirmwareRetractionLength = None
            self.FirmwareUnretractionAdditionalLength = None
            self.FirmwareRetractionFeedrate = None
            self.FirmwareUnretractionFeedrate = None
            self.FirmwareZLift = None
            self.HasPositionError = False
            self.PositionError = None
            self.HasHomedPosition = False

            ####### Extruder Tracking
            self.ERelative = 0
            self.ExtrusionLength = 0.0
            self.ExtrusionLengthTotal = 0.0
            self.RetractionLength = 0.0
            self.DeretractionLength = 0.0
            self.IsExtrudingStart = False
            self.IsExtruding = False
            self.IsPrimed = False
            self.IsRetractingStart = False
            self.IsRetracting = False
            self.IsRetracted = False
            self.IsPartiallyRetracted = False
            self.IsDeretractingStart = False
            self.IsDeretracting = False
            self.IsDeretracted = False

            # Resets state changes
            self.IsLayerChange = False
            self.IsHeightChange = False
            self.IsTravelOnly = False
            self.IsZHop = False
            self.HasPositionChanged = False
            self.HasStateChanged = False
            self.HasReceivedHomeCommand = False
            self.HasOneFeatureEnabled = False
            self.IsInPosition = False
            self.InPathPosition = False
            self.Features = []

    @classmethod
    def create_initial(cls, printer, octoprint_printer_profile):
        initial_pos = Pos()
        if printer.e_axis_default_mode in ['absolute', 'relative']:
            initial_pos.IsExtruderRelative = True if printer.e_axis_default_mode == 'relative' else False
        else:
            initial_pos.IsExtruderRelative = None
        if printer.xyz_axes_default_mode in ['absolute', 'relative']:
            initial_pos.IsRelative = True if printer.xyz_axes_default_mode == 'relative' else False
        else:
            initial_pos.IsRelative = None
        if printer.units_default in ['inches', 'millimeters']:
            initial_pos.IsMetric = True if printer.units_default == 'millimeters' else False
        else:
            initial_pos.IsMetric = None

        # default firmware retraction length and feedrate if default_firmware_retractions isenabled
        if printer.default_firmware_retractions:
            initial_pos.FirmwareRetractionLength = printer.retract_length
            initial_pos.FirmwareUnretractionAdditionalLength = None  # todo:  add this setting
            initial_pos.FirmwareRetractionFeedrate = printer.retract_speed
            initial_pos.FirmwareUnretractionFeedrate = printer.deretract_speed
        if printer.default_firmware_retractions_zhop:
            initial_pos.FirmwareZLift = printer.get_z_hop_for_slicer_type()

        return initial_pos

    def is_state_equal(self, pos):
        if (self.XHomed == pos.XHomed and self.YHomed == pos.YHomed
            and self.ZHomed == pos.ZHomed
            and self.IsLayerChange == pos.IsLayerChange
            and self.IsHeightChange == pos.IsHeightChange
            and self.IsZHop == pos.IsZHop
            and self.IsRelative == pos.IsRelative
            and self.IsExtruderRelative == pos.IsExtruderRelative
            and self.Layer == pos.Layer
            and self.Height == pos.Height
            and self.LastExtrusionHeight == pos.LastExtrusionHeight
            and self.IsPrinterPrimed == pos.IsPrinterPrimed
            and self.MinimumLayerHeightReached == pos.MinimumLayerHeightReached
            and self.IsInPosition == pos.IsInPosition
            and self.InPathPosition == pos.InPathPosition
            and self.HasOneFeatureEnabled == pos.HasOneFeatureEnabled
            and self.HasPositionError == pos.HasPositionError
            and self.PositionError == pos.PositionError
            and self.HasReceivedHomeCommand == pos.HasReceivedHomeCommand
            and self.IsTravelOnly == pos.IsTravelOnly
            and self.IsExtrudingStart == pos.IsExtrudingStart
            and self.IsExtruding == pos.IsExtruding
            and self.IsPrimed == pos.IsPrimed
            and self.IsRetractingStart == pos.IsRetractingStart
            and self.IsRetracting == pos.IsRetracting
            and self.IsRetracted == pos.IsRetracted
            and self.IsPartiallyRetracted == pos.IsPartiallyRetracted
            and self.IsDeretractingStart == pos.IsDeretractingStart
            and self.IsDeretracting == pos.IsDeretracting
            and self.IsDeretracted == pos.IsDeretracted

        ):
            return True

        return False

    def is_position_equal(self, pos):

        return (
            pos.X == self.X and
            pos.Y == self.Y and
            pos.Z == self.Z
        )

    def to_extruder_state_dict(self):
        return {
            "E": self.ERelative,
            "ExtrusionLength": self.ExtrusionLength,
            "ExtrusionLengthTotal": self.ExtrusionLengthTotal,
            "RetractionLength": self.RetractionLength,
            "DeretractionLength": self.DeretractionLength,
            "IsExtrudingStart": self.IsExtrudingStart,
            "IsExtruding": self.IsExtruding,
            "IsPrimed": self.IsPrimed,
            "IsRetractingStart": self.IsRetractingStart,
            "IsRetracting": self.IsRetracting,
            "IsRetracted": self.IsRetracted,
            "IsPartiallyRetracted": self.IsPartiallyRetracted,
            "IsDeretractingStart": self.IsDeretractingStart,
            "IsDeretracting": self.IsDeretracting,
            "IsDeretracted": self.IsDeretracted,
            "HasChanged": self.HasStateChanged
        }

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
            "IsPrinterPrimed": self.IsPrinterPrimed,
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
        x,
        y,
        z,
        e,
        f,
        force=False,
        is_g1=False
    ):
        if is_g1:
            self.IsTravelOnly = e is None and z is None and (
                x is not None or y is not None
            )
        if f is not None:
            self.F = f

        if force:
            # Force the coordinates in as long as they are provided.
            #
            if x is not None:
                self.X = utility.round_to_float_equality_range(x + self.XOffset)
            if y is not None:
                self.Y = utility.round_to_float_equality_range(y + self.YOffset)
            if z is not None:
                self.Z = utility.round_to_float_equality_range(z + self.ZOffset)
            if e is not None:
                self.E = utility.round_to_float_equality_range(e + self.EOffset)
            return

        if self.IsRelative:
            if x is not None:
                self.X = None if self.X is None else utility.round_to_float_equality_range(x + self.X)
            if y is not None:
                self.Y = None if self.Y is None else utility.round_to_float_equality_range(y + self.Y)
            if z is not None:
                self.Z = None if self.Z is None else utility.round_to_float_equality_range(z + self.Z)
        else:
            if x is not None:
                self.X = utility.round_to_float_equality_range(x + self.XOffset)
            if y is not None:
                self.Y = utility.round_to_float_equality_range(y + self.YOffset)
            if z is not None:
                self.Z = utility.round_to_float_equality_range(z + self.ZOffset)

        if e is not None:
            if self.IsExtruderRelative:
                self.E = None if self.E is None else utility.round_to_float_equality_range(e + self.E)
            else:
                self.E = utility.round_to_float_equality_range(e + self.EOffset)

    def is_zhop(self, z_hop):
        return (
            False if self.Z is None or self.LastExtrusionHeight is None
            else self.Z - self.LastExtrusionHeight - z_hop <= 0
        )

    def distance_to_zlift(self, z_hop, restrict_lift_height=True):
        amount_to_lift = None if self.Z is None or self.LastExtrusionHeight is None else self.Z - self.LastExtrusionHeight - z_hop
        if restrict_lift_height:
            if amount_to_lift < utility.FLOAT_MATH_EQUALITY_RANGE:
                return 0
            elif amount_to_lift > z_hop:
                return z_hop

        return utility.round_to(amount_to_lift, utility.FLOAT_MATH_EQUALITY_RANGE)

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
        self.feature_restrictions_enabled = self.Snapshot.feature_restrictions_enabled
        self.OctoprintPrinterProfile = octoprint_printer_profile
        self.Origin = {
            "X": self.Printer.origin_x,
            "Y": self.Printer.origin_y,
            "Z": self.Printer.origin_z
        }

        self.BoundingBox = utility.get_bounding_box(self.Printer,
                                                    octoprint_printer_profile)
        self.gcode_generation_settings = self.Settings.profiles.current_printer().get_current_state_detection_settings()
        self.retraction_length = self.gcode_generation_settings.retraction_length
        self.PrinterTolerance = utility.FLOAT_MATH_EQUALITY_RANGE
        self.Positions = deque(maxlen=5)
        self.SavedPosition = None
        self.HasRestrictedPosition = (
            len(self.Snapshot.position_restrictions) > 0 and self.Snapshot.position_restrictions_enabled
        )
        if self.Printer.g90_influences_extruder in ['true', 'false']:
            self.G90InfluencesExtruder = True if self.Printer.g90_influences_extruder == 'true' else False
        else:
            self.G90InfluencesExtruder = g90_influences_extruder

        self.gcode_generation_settings = self.Printer.get_current_state_detection_settings()
        assert (isinstance(self.gcode_generation_settings, OctolapseGcodeSettings))

        self.ZHop = 0 if self.gcode_generation_settings.z_lift_height is None else self.gcode_generation_settings.z_lift_height
        self.priming_height = self.Printer.priming_height
        self.minimum_layer_height = self.Printer.minimum_layer_height
        self.LocationDetectionCommands = []
        self.create_location_detection_commands()

        self.current_pos = Pos.create_initial(self.Printer, self.OctoprintPrinterProfile)
        self.previous_pos = Pos.create_initial(self.Printer, self.OctoprintPrinterProfile)

        self.Positions.append(self.previous_pos)
        self.Positions.append(self.current_pos)

        self.gcode_functions = self.get_gcode_functions()
        self.extruder_update_commands = {'G0', 'G1', 'G3', 'G4', 'G10', 'G11', 'G28', 'G80', 'M109', 'M116', 'M190',
                                         'M191'}

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

    def update_position(self, x, y, z, e, f, force=False):
        self.current_pos.update_position(x, y, z, e, f, force)

    def to_position_dict(self):
        if len(self.Positions) > 0:
            ret_dict = self.current_pos.to_dict()
            ret_dict["Features"] = self.SlicerFeatures.get_printing_features_list(self.current_pos.F,self.current_pos.Layer)
            return ret_dict
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

    def distance_to_zlift(self):
        # get the lift amount, but don't restrict it so we can log properly
        return self.current_pos.distance_to_zlift(self.ZHop, True)

    def length_to_retract(self):
        # if we don't have any history, we want to retract
        retract_length = utility.round_to_float_equality_range(
            self.retraction_length - self.current_pos.RetractionLength
        )

        # Don't round the retraction length
        # retractLength = utility.round_to(retract_length, self.PrinterTolerance)

        if retract_length < 0:
            # This means we are beyond fully retracted, return 0
            self.Settings.Logger.log_warning("extruder.py - A 'length_to_retract' was requested, "
                                             "but the extruder is beyond the configured retraction "
                                             "length.")
            retract_length = 0
        elif retract_length > self.retraction_length:
            self.Settings.Logger.log_error("extruder.py - A 'length_to_retract' was requested, "
                                           "but was found to be greater than the retraction "
                                           "length.")
            # for some reason we are over the retraction length.  Return 0
            retract_length = self.retraction_length

        if abs(retract_length) < utility.FLOAT_MATH_EQUALITY_RANGE:
            return 0.0
        # return the calculated retraction length
        return retract_length

    def is_extruder_triggered(self, options):
        # if there are no extruder trigger options, return true.
        if options is None:
            return True


        # Matches the supplied extruder trigger options to the current
        # extruder state.  Returns true if triggering, false if not.

        extruding_start_triggered = self._extruder_state_triggered(
            options.OnExtrudingStart, self.current_state.IsExtrudingStart
        )
        extruding_triggered = self._extruder_state_triggered(
            options.OnExtruding, self.current_state.IsExtruding
        )
        primed_triggered = self._extruder_state_triggered(
            options.OnPrimed, self.current_state.IsPrimed
        )
        retracting_start_triggered = self._extruder_state_triggered(
            options.OnRetractingStart, self.current_state.IsRetractingStart
        )
        retracting_triggered = self._extruder_state_triggered(
            options.OnRetracting, self.current_state.IsRetracting
        )
        partially_retracted_triggered = self._extruder_state_triggered(
            options.OnPartiallyRetracted, self.current_state.IsPartiallyRetracted
        )
        retracted_triggered = self._extruder_state_triggered(
            options.OnRetracted, self.current_state.IsRetracted
        )
        deretracting_start_triggered = self._extruder_state_triggered(
            options.OnDeretractingStart, self.current_state.IsDeretractingStart
        )
        deretracting_triggered = self._extruder_state_triggered(
            options.OnDeretracting, self.current_state.IsDeretracting
        )
        deretracted_triggered = self._extruder_state_triggered(
            options.OnDeretracted, self.current_state.IsDeretracted
        )

        ret_value = False
        is_triggering_prevented = (
            (extruding_start_triggered is not None and not extruding_start_triggered)
            or (extruding_triggered is not None and not extruding_triggered)
            or (primed_triggered is not None and not primed_triggered)
            or (retracting_start_triggered is not None and not retracting_start_triggered)
            or (retracting_triggered is not None and not retracting_triggered)
            or (partially_retracted_triggered is not None and not partially_retracted_triggered)
            or (retracted_triggered is not None and not retracted_triggered)
            or (deretracting_start_triggered is not None and not deretracting_start_triggered)
            or (deretracting_triggered is not None and not deretracting_triggered)
            or (deretracted_triggered is not None and not deretracted_triggered))

        if (not is_triggering_prevented
            and
            (
                (extruding_start_triggered is not None and extruding_start_triggered)
                or (extruding_triggered is not None and extruding_triggered)
                or (primed_triggered is not None and primed_triggered)
                or (retracting_start_triggered is not None and retracting_start_triggered)
                or (retracting_triggered is not None and retracting_triggered)
                or (partially_retracted_triggered is not None and partially_retracted_triggered)
                or (retracted_triggered is not None and retracted_triggered)
                or (deretracting_start_triggered is not None and deretracting_start_triggered)
                or (deretracting_triggered is not None and deretracting_triggered)
                or (deretracted_triggered is not None and deretracted_triggered)
                or (options.are_all_triggers_ignored()))):
            ret_value = True

        return ret_value


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
        self.current_pos = self.Positions[0]
        self.previous_pos = self.Positions[1]
        return previous_position

    def get_position(self, index=0):
        if len(self.Positions) > index:
            return self.Positions[index]
        return None

    def get_gcode_functions(self):
        return {
            "G0": self.process_g0_g1,
            "G1": self.process_g0_g1,
            "G2": self.process_g2,
            "G3": self.process_g3,
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

        # Move the current position to the previous and
        self.previous_pos = self.current_pos
        self.current_pos = Pos(self.previous_pos, reset_state=True)

        previous = self.previous_pos
        current = self.current_pos

        # set the pos gcode cmd
        current.parsed_command = parsed_command

        # apply the cmd to the position tracker
        # cmd = current.parsed_command.cmd
        cmd = parsed_command.cmd

        # This is a secial case for optimization reasons.
        # These two are by far the most used commands, so
        # call them directly and avoid the hash lookup and extra function call
        has_processed_command = False
        if cmd == "G1" or cmd == "G0":
            has_processed_command = True
            self.current_pos.update_position(
                parsed_command.parameters["X"] if "X" in parsed_command.parameters else None,
                parsed_command.parameters["Y"] if "Y" in parsed_command.parameters else None,
                parsed_command.parameters["Z"] if "Z" in parsed_command.parameters else None,
                parsed_command.parameters["E"] if "E" in parsed_command.parameters else None,
                parsed_command.parameters["F"] if "F" in parsed_command.parameters else None,
                is_g1=True
            )
        elif parsed_command.cmd in self.gcode_functions:
            self.gcode_functions[parsed_command.cmd]()
            has_processed_command = True
            # Have the XYZ positions changed after processing a command?

        if has_processed_command:
            current.HasPositionChanged = (
                current.X != previous.X or current.Y != previous.Y or current.E != previous.E
                or current.Z != previous.Z
            )

            # see if our position is homed
            if not current.HasHomedPosition:
                current.HasHomedPosition = (
                    current.XHomed and current.YHomed and current.ZHomed and
                    current.IsMetric and
                    current.X is not None and
                    current.Y is not None and
                    current.Z is not None and
                    current.IsRelative is not None and
                    current.IsExtruderRelative is not None
                )

        # update the extruder state.  Note that e_relative must be rounded and non-null

        ### Update Extruder States
        # this value should already be rounded
        current.ERelative = utility.round_to_float_equality_range(current.E - previous.E)
        if current.ERelative != 0:
            # Update RetractionLength and ExtrusionLength
            current.RetractionLength = utility.round_to_float_equality_range(current.RetractionLength - current.ERelative)
            if current.RetractionLength <= 0:
                # we can use the negative retraction length to calculate our extrusion length!
                current.ExtrusionLength = abs(current.RetractionLength)
                # set the retraction length to 0 since we are extruding
                current.RetractionLength = 0
            else:
                current.ExtrusionLength = 0
                # Update extrusion length
                current.ExtrusionLengthTotal = utility.round_to_float_equality_range(
                    current.ExtrusionLengthTotal + current.ExtrusionLength
                )
            # calculate deretraction length
            if previous.RetractionLength > current.RetractionLength:
                current.DeretractionLength = utility.round_to_float_equality_range(
                    previous.RetractionLength - current.RetractionLength,
                )
            else:
                current.DeretractionLength = 0

        if current.ERelative != 0 or current.HasPositionChanged:
            # rounding should all be done by now
            current.IsExtrudingStart = True if current.ExtrusionLength > 0 and not previous.IsExtruding else False
            current.IsExtruding = True if current.ExtrusionLength > 0 else False
            current.IsPrimed = True if current.ExtrusionLength == 0 and current.RetractionLength == 0 else False
            current.IsRetractingStart = True if not previous.IsRetracting and current.RetractionLength > 0 else False
            current.IsRetracting = True if current.RetractionLength > previous.RetractionLength else False
            current.IsPartiallyRetracted = True if (
                0 < current.RetractionLength < self.retraction_length) else False
            current.IsRetracted = True if current.RetractionLength >= self.retraction_length else False
            current.IsDeretractingStart = True if current.DeretractionLength > 0 and not previous.IsDeretracting else False
            current.IsDeretracting = True if current.DeretractionLength > previous.DeretractionLength else False
            current.IsDeretracted = True if previous.IsRetracted and current.RetractionLength == 0 else False
            # has this changed

        # determine state changes
        # state changes can happen with every gcode command, even if it's not parsed.  Update
        #current.HasStateChanged = not current.is_state_equal(previous)

        #if current.HasStateChanged or current.HasPositionChanged:
        if (
            current.HasPositionChanged
        ):
            # calculate LastExtrusionHeight and Height
            # If we are extruding on a higher level, or if retract is enabled and the nozzle is primed
            # adjust the last extrusion height
            if current.Z is not None and current.Z != current.LastExtrusionHeight:
                if current.IsExtruding:
                    current.LastExtrusionHeight = current.Z
                    # Is Primed
                    if not current.IsPrinterPrimed:
                        # We haven't primed yet, check to see if we have priming height restrictions
                        if self.Printer.priming_height > 0:
                            # if a priming height is configured, see if we've extruded below the  height
                            if current.LastExtrusionHeight < self.priming_height:
                                current.IsPrinterPrimed = True
                        else:
                            # if we have no priming height set, just set IsPrinterPrimed = true.
                            current.IsPrinterPrimed = True
                    # Has Reached Minimum Layer Height
                    if not current.MinimumLayerHeightReached:
                        if self.minimum_layer_height > 0:
                            # if a priming height is configured, see if we've extruded below the  height
                            if current.LastExtrusionHeight >= self.minimum_layer_height:
                                current.MinimumLayerHeightReached = True
                        else:
                            # if we have no priming height set, just set IsPrinterPrimed = true.
                            current.MinimumLayerHeightReached = True

                #Calculate Layer Change
                if ((current.IsPrimed and current.Layer > 0) or current.IsExtruding) and current.IsPrinterPrimed:
                    if current.Z > previous.Height:
                        current.Height = current.Z

                        # calculate layer change
                        if current.MinimumLayerHeightReached and (
                            utility.round_to_float_equality_range(current.Height - previous.Height) > 0
                            or current.Layer == 0
                        ):
                            current.IsLayerChange = True
                            current.Layer += 1

            # Calcluate position restructions
            if self.HasRestrictedPosition:
                # If we have a homed for the current and previous position, and either the exturder or position has changed
                if current.X is not None and current.Y is not None and previous.X is not None and previous.Y is not None:
                    # If we're using restricted positions, calculate intersections and determine if we are in position
                    can_calculate_intersections = current.parsed_command.cmd in ["G0", "G1"]
                    _is_in_position, _intersections = self.calculate_path_intersections(
                        self.Snapshot.position_restrictions,
                        current.X,
                        current.Y,
                        previous.X,
                        previous.Y,
                        can_calculate_intersections
                    )
                    if _is_in_position:
                        current.IsInPosition = _is_in_position

                    else:
                        current.InPathPosition = _intersections
            else:
                current.IsInPosition = True
                # Calculate ZHop based on last extrusion height
                #current.IsZHop = current.is_zhop(self.ZHop)

            current.IsZHop = (
                False if current.IsExtruding or current.Z is None or current.LastExtrusionHeight is None
                else current.Z - current.LastExtrusionHeight >= self.ZHop
            )
            # Update Feature Detection
            if self.feature_restrictions_enabled:
                if current.F is not None or current.HasPositionChanged:
                    # see if at least one feature is enabled, or if feature detection is disabled
                    current.HasOneFeatureEnabled = self.SlicerFeatures.is_one_feature_enabled(current.F, current.Layer)
            else:
                current.HasOneFeatureEnabled = True
        self.Positions.appendleft(current)

    def process_g0_g1(self):

        # If we're moving on the X/Y plane only, mark this position as travel only
        parameters = self.current_pos.parsed_command.parameters
        self.current_pos.update_position(
            parameters["X"] if "X" in parameters else None,
            parameters["Y"] if "T" in parameters else None,
            parameters["Z"] if "Z" in parameters else None,
            parameters["E"] if "E" in parameters else None,
            parameters["F"] if "F" in parameters else None,
            is_g1=True
        )

    def process_g2(self):
        self.process_g2_g3("G2")

    def process_g3(self, parameters):
        self.process_g2_g3("G3")

    def process_g2_g3(self, cmd):
        parameters = self.current_pos.parsed_command.parameters
        # Movement Type
        movement_type = ""
        if cmd == "G2":
            movement_type = "clockwise"
            self.Settings.Logger.log_position_command_received("Received G2 - Clockwise Arc")
        else:
            movement_type = "counter-clockwise"
            self.Settings.Logger.log_position_command_received("Received G3 - Counter-Clockwise Arc")

        x = parameters["X"] if "X" in parameters else None
        y = parameters["Y"] if "Y" in parameters else None
        i = parameters["I"] if "I" in parameters else None
        j = parameters["J"] if "J" in parameters else None
        r = parameters["R"] if "R" in parameters else None
        e = parameters["E"] if "E" in parameters else None
        f = parameters["F"] if "F" in parameters else None

        # If we're moving on the X/Y plane only, mark this position as travel only
        self.current_pos.IsTravelOnly = e is None

        can_update_position = False
        if r is not None and (i is not None or j is not None):
            self.Settings.Logger.log_error(
                "Received {0} - but received R and either I or J, which is not allowed.".format(cmd))
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
                    "Received {0} - but received R without x or y, which is not allowed.".format(cmd)
                )
            else:
                can_update_position = True
                self.Settings.Logger.log_info(
                    "Cannot yet calculate position restriction intersections when G2/G3.")

        if can_update_position:
            self.current_pos.update_position(x, y, None, e, f)

            message = "Position Change - {0} - {1} {2} Arc From(X:{3},Y:{4},Z:{5},E:{6}) - To(X:{7},Y:{8}," \
                      "Z:{9},E:{10})"
            if self.previous_pos is None:
                message = message.format(
                    self.current_pos.parsed_command.gcode, "Relative" if self.current_pos.IsRelative else "Absolute",
                    movement_type
                    , "None", "None",
                    "None", "None", self.current_pos.X, self.current_pos.Y, self.current_pos.Z, self.current_pos.E)
            else:
                message = message.format(
                    self.current_pos.parsed_command.gcode, "Relative" if self.current_pos.IsRelative else "Absolute",
                    movement_type,
                    self.previous_pos.X,
                    self.previous_pos.Y, self.previous_pos.Z, self.previous_pos.E, self.current_pos.X,
                    self.current_pos.Y, self.current_pos.Z, self.current_pos.E)
            self.Settings.Logger.log_position_change(
                message)

    def process_g10(self):
        parameters = self.current_pos.parsed_command.parameters
        if "P" not in parameters:
            e = 0 if self.current_pos.FirmwareRetractionLength is None else -1.0 * self.current_pos.FirmwareRetractionLength
            previous_extruder_relative = self.current_pos.IsExtruderRelative
            previous_relative = self.current_pos.IsRelative

            self.current_pos.IsRelative = True
            self.current_pos.IsExtruderRelative = True
            self.current_pos.update_position(None, None, self.current_pos.FirmwareZLift, e,
                                             self.current_pos.FirmwareRetractionFeedrate)
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
        self.current_pos.update_position({None, None, None, lift_distance, e, f})
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
        parameters = self.current_pos.parsed_command.parameters
        # Home
        self.current_pos.HasReceivedHomeCommand = True
        x = True if "X" in parameters else None
        y = True if "Y" in parameters else None
        z = True if "Z" in parameters else None
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

    def process_g92(self):  # Set Position (offset)
        parameters = self.current_pos.parsed_command.parameters
        x = parameters["X"] if "X" in parameters else None
        y = parameters["Y"] if "Y" in parameters else None
        z = parameters["Z"] if "Z" in parameters else None
        e = parameters["E"] if "E" in parameters else None
        o = True if "O" in parameters else False

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
        parameters = self.current_pos.parsed_command.parameters
        # Firmware Retraction Tracking
        if "S" in parameters:
            self.current_pos.FirmwareRetractionLength = parameters["S"]
        if "R" in parameters:
            self.current_pos.FirmwareUnretractionAdditionalLength = parameters["R"]
        if "F" in parameters:
            self.current_pos.FirmwareRetractionFeedrate = parameters["F"]
        if "T" in parameters:
            self.current_pos.FirmwareUnretractionFeedrate = parameters["T"]
        if "Z" in parameters:
            self.current_pos.FirmwareZLift = parameters["Z"]

    def process_m208(self):
        parameters = self.current_pos.parsed_command.parameters
        # Firmware Retraction Tracking
        if "S" in parameters:
            self.current_pos.FirmwareUnretractionAdditionalLength = parameters["S"]
        if "F" in parameters:
            self.current_pos.FirmwareUnretractionFeedrate = parameters["F"]

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
            return x - pos.X + pos.XOffset

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
            if len(self.Positions) <= index + 1:
                return None
            pos = self.Positions[index]
            previous_pos = self.Positions[index + 1]
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

    @staticmethod
    def _extruder_state_triggered(option, state):
        if option is None:
            return None
        if option and state:
            return True
        if not option and state:
            return False
        return None

    def is_extruder_triggered(self, options):
        # if there are no extruder trigger options, return true.
        if options is None:
            return True

        # Matches the supplied extruder trigger options to the current
        # extruder state.  Returns true if triggering, false if not.

        extruding_start_triggered = self._extruder_state_triggered(
            options.OnExtrudingStart, self.current_pos.IsExtrudingStart
        )
        extruding_triggered = self._extruder_state_triggered(
            options.OnExtruding, self.current_pos.IsExtruding
        )
        primed_triggered = self._extruder_state_triggered(
            options.OnPrimed, self.current_pos.IsPrimed
        )
        retracting_start_triggered = self._extruder_state_triggered(
            options.OnRetractingStart, self.current_pos.IsRetractingStart
        )
        retracting_triggered = self._extruder_state_triggered(
            options.OnRetracting, self.current_pos.IsRetracting
        )
        partially_retracted_triggered = self._extruder_state_triggered(
            options.OnPartiallyRetracted, self.current_pos.IsPartiallyRetracted
        )
        retracted_triggered = self._extruder_state_triggered(
            options.OnRetracted, self.current_pos.IsRetracted
        )
        deretracting_start_triggered = self._extruder_state_triggered(
            options.OnDeretractingStart, self.current_pos.IsDeretractingStart
        )
        deretracting_triggered = self._extruder_state_triggered(
            options.OnDeretracting, self.current_pos.IsDeretracting
        )
        deretracted_triggered = self._extruder_state_triggered(
            options.OnDeretracted, self.current_pos.IsDeretracted
        )

        ret_value = False
        is_triggering_prevented = (
            (extruding_start_triggered is not None and not extruding_start_triggered)
            or (extruding_triggered is not None and not extruding_triggered)
            or (primed_triggered is not None and not primed_triggered)
            or (retracting_start_triggered is not None and not retracting_start_triggered)
            or (retracting_triggered is not None and not retracting_triggered)
            or (partially_retracted_triggered is not None and not partially_retracted_triggered)
            or (retracted_triggered is not None and not retracted_triggered)
            or (deretracting_start_triggered is not None and not deretracting_start_triggered)
            or (deretracting_triggered is not None and not deretracting_triggered)
            or (deretracted_triggered is not None and not deretracted_triggered))

        if (not is_triggering_prevented
            and
            (
                (extruding_start_triggered is not None and extruding_start_triggered)
                or (extruding_triggered is not None and extruding_triggered)
                or (primed_triggered is not None and primed_triggered)
                or (retracting_start_triggered is not None and retracting_start_triggered)
                or (retracting_triggered is not None and retracting_triggered)
                or (partially_retracted_triggered is not None and partially_retracted_triggered)
                or (retracted_triggered is not None and retracted_triggered)
                or (deretracting_start_triggered is not None and deretracting_start_triggered)
                or (deretracting_triggered is not None and deretracting_triggered)
                or (deretracted_triggered is not None and deretracted_triggered)
                or (options.are_all_triggers_ignored()))):
            ret_value = True

        return ret_value


class ExtruderTriggers(object):
    __slots__ = [
        'OnExtrudingStart',
        'OnExtruding',
        'OnPrimed',
        'OnRetractingStart',
        'OnRetracting',
        'OnPartiallyRetracted',
        'OnRetracted',
        'OnDeretractingStart',
        'OnDeretracting',
        'OnDeretracted'
    ]

    def __init__(
        self, on_extruding_start, on_extruding, on_primed,
        on_retracting_start, on_retracting, on_partially_retracted,
        on_retracted, on_deretracting_start, on_deretracting, on_deretracted):
        # To trigger on an extruder state, set to True.
        # To prevent triggering on an extruder state, set to False.
        # To ignore the extruder state, set to None
        self.OnExtrudingStart = on_extruding_start
        self.OnExtruding = on_extruding
        self.OnPrimed = on_primed
        self.OnRetractingStart = on_retracting_start
        self.OnRetracting = on_retracting
        self.OnPartiallyRetracted = on_partially_retracted
        self.OnRetracted = on_retracted
        self.OnDeretractingStart = on_deretracting_start
        self.OnDeretracting = on_deretracting
        self.OnDeretracted = on_deretracted

    def are_all_triggers_ignored(self):
        if (
            self.OnExtrudingStart is None
            and self.OnExtruding is None
            and self.OnPrimed is None
            and self.OnRetractingStart is None
            and self.OnRetracting is None
            and self.OnPartiallyRetracted is None
            and self.OnRetracted is None
            and self.OnDeretractingStart is None
            and self.OnDeretracting is None
            and self.OnDeretracted is None
        ):
            return True
        return False
