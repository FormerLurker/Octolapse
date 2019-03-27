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
import math
import octoprint_octolapse.utility as utility
from octoprint_octolapse.settings import SlicerPrintFeatures, OctolapseGcodeSettings
from octoprint_octolapse.gcode_parser import ParsedCommand
import GcodePositionProcessor
# create the module level logger
from octoprint_octolapse.log import LoggingConfigurator
logging_configurator = LoggingConfigurator()
logger = logging_configurator.get_logger(__name__)


class Pos(object):
    # Add slots for faster copy and init
    __slots__ = [
        "parsed_command", "f", "x", "x_offset", "x_homed", "y", "y_offset", "y_homed", "z", "z_offset", "z_homed",
        "e", "e_offset", "is_relative", "is_extruder_relative", "is_metric", "last_extrusion_height", "layer",
        "height", "is_printer_primed", "minimum_layer_height_reached", "is_in_position", "in_path_position",
        "is_travel_only", "has_one_feature_enabled", "firmware_retraction_length",
        "firmware_unretraction_additional_length", "firmware_retraction_feedrate", "firmware_unretraction_feedrate", 
        "firmware_z_lift", "has_homed_position", "is_layer_change", "is_height_change", "is_zhop",
        "has_position_changed", "has_state_changed", "has_received_home_command", "has_position_error", 
        "position_error", 'e_relative', 'extrusion_length', 'extrusion_length_total', 'retraction_length', 
        'deretraction_length', 'is_extruding_start', 'is_extruding', 'is_primed', 'is_retracting_start', 
        'is_retracting', 'is_retracted', 'is_partially_retracted', 'is_deretracting_start', 'is_deretracting',
        'is_deretracted'
    ]

    def __init__(self, copy_from_pos=None, reset_state=False):

        if copy_from_pos is not None:
            self.parsed_command = copy_from_pos.parsed_command
            self.f = copy_from_pos.f
            self.x = copy_from_pos.x
            self.x_offset = copy_from_pos.x_offset
            self.x_homed = copy_from_pos.x_homed
            self.y = copy_from_pos.y
            self.y_offset = copy_from_pos.y_offset
            self.y_homed = copy_from_pos.y_homed
            self.z = copy_from_pos.z
            self.z_offset = copy_from_pos.z_offset
            self.z_homed = copy_from_pos.z_homed
            self.e = copy_from_pos.e
            self.e_offset = copy_from_pos.e_offset
            self.is_relative = copy_from_pos.is_relative
            self.is_extruder_relative = copy_from_pos.is_extruder_relative
            self.is_metric = copy_from_pos.is_metric
            self.last_extrusion_height = copy_from_pos.last_extrusion_height
            self.layer = copy_from_pos.layer
            self.height = copy_from_pos.height
            self.is_printer_primed = copy_from_pos.is_printer_primed
            self.minimum_layer_height_reached = copy_from_pos.minimum_layer_height_reached
            self.firmware_retraction_length = copy_from_pos.firmware_retraction_length
            self.firmware_unretraction_additional_length = copy_from_pos.firmware_unretraction_additional_length
            self.firmware_retraction_feedrate = copy_from_pos.firmware_retraction_feedrate
            self.firmware_unretraction_feedrate = copy_from_pos.firmware_unretraction_feedrate
            self.firmware_z_lift = copy_from_pos.firmware_z_lift
            self.has_position_error = copy_from_pos.has_position_error
            self.position_error = copy_from_pos.position_error
            self.has_homed_position = copy_from_pos.has_homed_position

            # Extruder Tracking
            self.e_relative = copy_from_pos.e_relative
            self.extrusion_length = copy_from_pos.extrusion_length
            self.extrusion_length_total = copy_from_pos.extrusion_length_total
            self.retraction_length = copy_from_pos.retraction_length
            self.deretraction_length = copy_from_pos.deretraction_length
            self.is_extruding_start = copy_from_pos.is_extruding_start
            self.is_extruding = copy_from_pos.is_extruding
            self.is_primed = copy_from_pos.is_primed
            self.is_retracting_start = copy_from_pos.is_retracting_start
            self.is_retracting = copy_from_pos.is_retracting
            self.is_retracted = copy_from_pos.is_retracted
            self.is_partially_retracted = copy_from_pos.is_partially_retracted
            self.is_deretracting_start = copy_from_pos.is_deretracting_start
            self.is_deretracting = copy_from_pos.is_deretracting
            self.is_deretracted = copy_from_pos.is_deretracted
            self.is_in_position = copy_from_pos.is_in_position
            self.has_one_feature_enabled = copy_from_pos.has_one_feature_enabled
            self.in_path_position = copy_from_pos.in_path_position
            self.is_zhop = copy_from_pos.is_zhop
            #######
            if reset_state:
                # Resets state changes
                self.is_layer_change = False
                self.is_height_change = False
                self.is_travel_only = False
                self.has_position_changed = False
                self.has_state_changed = False
                self.has_received_home_command = False
            else:
                # Copy or default states
                self.is_layer_change = copy_from_pos.is_layer_change
                self.is_height_change = copy_from_pos.is_height_change
                self.is_travel_only = copy_from_pos.is_travel_only
                self.has_position_changed = copy_from_pos.has_position_changed
                self.has_state_changed = copy_from_pos.has_state_changed
                self.has_received_home_command = copy_from_pos.has_received_home_command

        else:
            self.parsed_command = None
            self.f = None
            self.x = None
            self.x_offset = 0
            self.x_homed = False
            self.y = None
            self.y_offset = 0
            self.y_homed = False
            self.z = None
            self.z_offset = 0
            self.z_homed = False
            self.e = 0
            self.e_offset = 0
            self.is_relative = False
            self.is_extruder_relative = False
            self.is_metric = True
            self.last_extrusion_height = None
            self.layer = 0
            self.height = 0
            self.is_printer_primed = False
            self.minimum_layer_height_reached = False
            self.firmware_retraction_length = None
            self.firmware_unretraction_additional_length = None
            self.firmware_retraction_feedrate = None
            self.firmware_unretraction_feedrate = None
            self.firmware_z_lift = None
            self.has_position_error = False
            self.position_error = None
            self.has_homed_position = False

            # Extruder Tracking
            self.e_relative = 0
            self.extrusion_length = 0.0
            self.extrusion_length_total = 0.0
            self.retraction_length = 0.0
            self.deretraction_length = 0.0
            self.is_extruding_start = False
            self.is_extruding = False
            self.is_primed = False
            self.is_retracting_start = False
            self.is_retracting = False
            self.is_retracted = False
            self.is_partially_retracted = False
            self.is_deretracting_start = False
            self.is_deretracting = False
            self.is_deretracted = False

            # Resets state changes
            self.is_layer_change = False
            self.is_height_change = False
            self.is_travel_only = False
            self.is_zhop = False
            self.has_position_changed = False
            self.has_state_changed = False
            self.has_received_home_command = False
            self.has_one_feature_enabled = False
            self.is_in_position = False
            self.in_path_position = False

    @classmethod
    def copy_from_cpp_pos(cls, cpp_pos, target):

        target.x = None if cpp_pos[52] > 0 else cpp_pos[0]
        target.y = None if cpp_pos[53] > 0 else cpp_pos[1]
        target.z = None if cpp_pos[54] > 0 else cpp_pos[2]
        target.f = None if cpp_pos[55] > 0 else cpp_pos[3]
        target.e = cpp_pos[4]
        target.x_offset = cpp_pos[5]
        target.y_offset = cpp_pos[6]
        target.z_offset = cpp_pos[7]
        target.e_offset = cpp_pos[8]
        target.e_relative = cpp_pos[9]
        target.extrusion_length = cpp_pos[10]
        target.extrusion_length_total = cpp_pos[11]
        target.retraction_length = cpp_pos[12]
        target.deretraction_length = cpp_pos[13]
        target.last_extrusion_height = None if cpp_pos[58] > 0 else cpp_pos[14]
        target.height = cpp_pos[15]
        target.firmware_retraction_length = None if cpp_pos[60] > 0 else cpp_pos[16]
        target.firmware_unretraction_additional_length = None if cpp_pos[61] > 0 else cpp_pos[17]
        target.firmware_retraction_feedrate = None if cpp_pos[62] > 0 else cpp_pos[18]
        target.firmware_unretraction_feedrate = None if cpp_pos[63] > 0 else cpp_pos[19]
        target.firmware_z_lift = None if cpp_pos[64] > 0 else cpp_pos[20]
        target.layer = cpp_pos[21]
        target.x_homed = cpp_pos[22] > 0
        target.y_homed = cpp_pos[23] > 0
        target.z_homed = cpp_pos[24] > 0
        target.is_relative = None if cpp_pos[56] > 0 else cpp_pos[25] > 0
        target.is_extruder_relative = None if cpp_pos[57] > 0 else cpp_pos[26] > 0
        target.is_metric = None if cpp_pos[59] > 0 else cpp_pos[27] > 0
        target.is_printer_primed = cpp_pos[28] > 0
        target.minimum_layer_height_reached = cpp_pos[29] > 0
        target.has_position_error = cpp_pos[30] > 0
        target.has_homed_position = cpp_pos[31] > 0
        target.is_extruding_start = cpp_pos[32] > 0
        target.is_extruding = cpp_pos[33] > 0
        target.is_primed = cpp_pos[34] > 0
        target.is_retracting_start = cpp_pos[35] > 0
        target.is_retracting = cpp_pos[36] > 0
        target.is_retracted = cpp_pos[37] > 0
        target.is_partially_retracted = cpp_pos[38] > 0
        target.is_deretracting_start = cpp_pos[39] > 0
        target.is_deretracting = cpp_pos[40] > 0
        target.is_deretracted = cpp_pos[41] > 0
        target.is_layer_change = cpp_pos[42] > 0
        target.is_height_change = cpp_pos[43] > 0
        target.is_travel_only = cpp_pos[44] > 0
        target.is_zhop = cpp_pos[45] > 0
        target.has_position_changed = cpp_pos[46] > 0
        target.has_state_changed = cpp_pos[47] > 0
        target.has_received_home_command = cpp_pos[48] > 0
        # Todo:  figure out how to deal with these things which must be currently ignored
        #target.has_one_feature_enabled = cpp_pos[49] > 0
        #target.is_in_position = cpp_pos[50] > 0
        #target.in_path_position = cpp_pos[51] > 0
        fast_position = cpp_pos[65]
        if fast_position is not None:
            target.parsed_command = ParsedCommand(fast_position[0], fast_position[1], fast_position[2])
        else:
            target.parsed_command = None

        return target

    @classmethod
    def create_from_cpp_pos(cls, cpp_pos):
        pos = Pos()
        pos.x = None if cpp_pos[52] > 0 else cpp_pos[0]
        pos.y = None if cpp_pos[53] > 0 else cpp_pos[1]
        pos.z = None if cpp_pos[54] > 0 else cpp_pos[2]
        pos.f = None if cpp_pos[55] > 0 else cpp_pos[3]
        pos.e = cpp_pos[4]
        pos.x_offset = cpp_pos[5]
        pos.y_offset = cpp_pos[6]
        pos.z_offset = cpp_pos[7]
        pos.e_offset = cpp_pos[8]
        pos.e_relative = cpp_pos[9]
        pos.extrusion_length = cpp_pos[10]
        pos.extrusion_length_total = cpp_pos[11]
        pos.retraction_length = cpp_pos[12]
        pos.deretraction_length = cpp_pos[13]
        pos.last_extrusion_height = None if cpp_pos[58] > 0 else cpp_pos[14]
        pos.height = cpp_pos[15]
        pos.firmware_retraction_length = None if cpp_pos[60] > 0 else cpp_pos[16]
        pos.firmware_unretraction_additional_length = None if cpp_pos[61] > 0 else cpp_pos[17]
        pos.firmware_retraction_feedrate = None if cpp_pos[62] > 0 else cpp_pos[18]
        pos.firmware_unretraction_feedrate = None if cpp_pos[63] > 0 else cpp_pos[19]
        pos.firmware_z_lift = None if cpp_pos[64] > 0 else cpp_pos[20]
        pos.layer = cpp_pos[21]
        pos.x_homed = cpp_pos[22] > 1
        pos.y_homed = cpp_pos[23] > 1
        pos.z_homed = cpp_pos[24] > 1
        pos.is_relative = None if cpp_pos[56] > 0 else cpp_pos[25] > 0
        pos.is_extruder_relative = None if cpp_pos[57] > 0 else cpp_pos[26] > 0
        pos.is_metric = None if cpp_pos[59] > 0 else cpp_pos[27] > 0
        pos.is_printer_primed = cpp_pos[28] > 1
        pos.minimum_layer_height_reached = cpp_pos[29] > 1
        pos.has_position_error = cpp_pos[30] > 1
        pos.has_homed_position = cpp_pos[31] > 1
        pos.is_extruding_start = cpp_pos[32] > 1
        pos.is_extruding = cpp_pos[33] > 1
        pos.is_primed = cpp_pos[34] > 1
        pos.is_retracting_start = cpp_pos[35] > 1
        pos.is_retracting = cpp_pos[36] > 1
        pos.is_retracted = cpp_pos[37] > 1
        pos.is_partially_retracted = cpp_pos[38] > 1
        pos.is_deretracting_start = cpp_pos[39] > 1
        pos.is_deretracting = cpp_pos[40] > 1
        pos.is_deretracted = cpp_pos[41] > 1
        pos.is_layer_change = cpp_pos[42] > 1
        pos.is_height_change = cpp_pos[43] > 1
        pos.is_travel_only = cpp_pos[44] > 1
        pos.is_zhop = cpp_pos[45] > 1
        pos.has_position_changed = cpp_pos[46] > 1
        pos.has_state_changed = cpp_pos[47] > 1
        pos.has_received_home_command = cpp_pos[48] > 1
        # Todo:  figure out how to deal with these things which must be currently ignored
        #pos.has_one_feature_enabled = cpp_pos[49] > 1
        #pos.is_in_position = cpp_pos[50] > 1
        #pos.in_path_position = cpp_pos[51] > 1

        fast_position = cpp_pos[65]
        if fast_position is not None:
            pos.parsed_command = ParsedCommand(fast_position[0], fast_position[1], fast_position[2])
        else:
            pos.parsed_command = None

        return pos

    def to_extruder_state_dict(self):
        return {
            "e": self.e_relative,
            "extrusion_length": self.extrusion_length,
            "extrusion_length_total": self.extrusion_length_total,
            "retraction_length": self.retraction_length,
            "deretraction_length": self.deretraction_length,
            "is_extruding_start": self.is_extruding_start,
            "is_extruding": self.is_extruding,
            "is_primed": self.is_primed,
            "is_retracting_start": self.is_retracting_start,
            "is_retracting": self.is_retracting,
            "is_retracted": self.is_retracted,
            "is_partially_retracted": self.is_partially_retracted,
            "is_deretracting_start": self.is_deretracting_start,
            "is_deretracting": self.is_deretracting,
            "is_deretracted": self.is_deretracted,
            "has_changed": self.has_state_changed
        }

    def to_state_dict(self):
        return {
            "gcode": "" if self.parsed_command is None else self.parsed_command.gcode,
            "x_homed": self.x_homed,
            "y_homed": self.y_homed,
            "z_homed": self.z_homed,
            "is_layer_change": self.is_layer_change,
            "is_height_change": self.is_height_change,
            "is_zhop": self.is_zhop,
            "is_relative": self.is_relative,
            "is_extruder_relative": self.is_extruder_relative,
            "is_metric": self.is_metric,
            "layer": self.layer,
            "height": self.height,
            "last_extrusion_height": self.last_extrusion_height,
            "is_in_position": self.is_in_position,
            "has_one_feature_enabled": self.has_one_feature_enabled,
            "in_path_position": self.in_path_position,
            "is_printer_primed": self.is_printer_primed,
            "minimum_layer_height_reached": self.minimum_layer_height_reached,
            "has_position_error": self.has_position_error,
            "position_error": self.position_error,
            "has_received_home_command": self.has_received_home_command,
            "is_travel_only": self.is_travel_only
        }

    def to_position_dict(self):
        return {
            "F": self.f,
            "x": self.x,
            "x_offset": self.x_offset,
            "y": self.y,
            "y_offset": self.y_offset,
            "z": self.z,
            "z_offset": self.z_offset,
            "e": self.e,
            "e_offset": self.e_offset
        }

    def to_dict(self):
        return {
            "gcode": "" if self.parsed_command is None else self.parsed_command.gcode,
            "f": self.f,
            "x": self.x,
            "x_offset": self.x_offset,
            "x_homed": self.x_homed,
            "y": self.y,
            "y_offset": self.y_offset,
            "y_homed": self.y_homed,
            "z": self.z,
            "z_offset": self.z_offset,
            "z_homed": self.z_homed,
            "e": self.e,
            "e_offset": self.e_offset,
            "is_relative": self.is_relative,
            "is_extruder_relative": self.is_extruder_relative,
            "is_metric": self.is_metric,
            "last_extrusion_height": self.last_extrusion_height,
            "is_layer_change": self.is_layer_change,
            "is_zhop": self.is_zhop,
            "is_in_position": self.is_in_position,
            "in_path_position": self.in_path_position,
            "is_primed": self.is_primed,
            "minimum_layer_height_reached": self.minimum_layer_height_reached,
            "has_position_error": self.has_position_error,
            "position_error": self.position_error,
            "has_position_changed": self.has_position_changed,
            "has_state_changed": self.has_state_changed,
            "layer": self.layer,
            "height": self.height,
            "has_received_home_command": self.has_received_home_command
        }

    def distance_to_zlift(self, z_hop, restrict_lift_height=True):
        amount_to_lift = (
            None if self.z is None or 
            self.last_extrusion_height is None 
            else self.z - self.last_extrusion_height - z_hop
        )
        if restrict_lift_height:
            if amount_to_lift < utility.FLOAT_MATH_EQUALITY_RANGE:
                return 0
            elif amount_to_lift > z_hop:
                return z_hop
        return utility.round_to(amount_to_lift, utility.FLOAT_MATH_EQUALITY_RANGE)

    def length_to_retract(self, amount_to_retract):
        # if we don't have any history, we want to retract
        retract_length = utility.round_to_float_equality_range(
            utility.round_to_float_equality_range(amount_to_retract - self.retraction_length)
        )
        if retract_length < 0:
            retract_length = 0
        elif retract_length > amount_to_retract:
            retract_length = amount_to_retract
        # return the calculated retraction length
        return retract_length


class Position(object):
    def __init__(self, printer_profile, snapshot_profile, octoprint_printer_profile,
                 g90_influences_extruder):
        # This key is used to call the unique gcode_position object for Octolapse.
        # This way multiple position trackers can be used at the same time with no
        # ill effects.
        self.key = "plugin_octolapse"

        # Todo:  make sure this setting is being read correctly, it doesn't look correct
        if printer_profile.g90_influences_extruder in ['true', 'false']:
            self.g90_influences_extruder = True if printer_profile.g90_influences_extruder == 'true' else False
        else:
            self.g90_influences_extruder = g90_influences_extruder

        # create location detection commands
        self._location_detection_commands = []
        if printer_profile.auto_position_detection_commands is not None:
            trimmed_commands = printer_profile.auto_position_detection_commands.strip()
            if len(trimmed_commands) > 0:
                self._location_detection_commands = [
                    x.strip().upper()
                    for x in
                    printer_profile.auto_position_detection_commands.split(',')
                ]
        if "G28" not in self._location_detection_commands:
            self._location_detection_commands.append("G28")
        if "G29" not in self._location_detection_commands:
            self._location_detection_commands.append("G29")

        # remove support for G161 and G162 until they are better understood
        # if "G161" not in self._location_detection_commands:
        #     self._location_detection_commands.append("G161")
        # if "G162" not in self._location_detection_commands:
        #     self._location_detection_commands.append("G162")
        self._gcode_generation_settings = printer_profile.get_current_state_detection_settings()

        xyz_axes_default_mode = printer_profile.xyz_axes_default_mode
        e_axis_default_mode = printer_profile.e_axis_default_mode
        units_default = printer_profile.units_default

        cpp_position_args = (
            self.key,  # gcode_position key
            printer_profile.auto_detect_position,
            0.0 if printer_profile.origin_x is None else printer_profile.origin_x,
            True if printer_profile.origin_x is None else False,  # is_origin_x_none
            0.0 if printer_profile.origin_y is None else printer_profile.origin_y,
            True if printer_profile.origin_y is None else False,  # is_origin_x_none
            0.0 if printer_profile.origin_z is None else printer_profile.origin_z,
            True if printer_profile.origin_z is None else False,  # is_origin_x_none
            self._gcode_generation_settings.retraction_length,
            (
                0 if self._gcode_generation_settings.z_lift_height is None
                else self._gcode_generation_settings.z_lift_height
            ),
            printer_profile.priming_height,
            printer_profile.minimum_layer_height,
            self.g90_influences_extruder,
            xyz_axes_default_mode,
            e_axis_default_mode,
            units_default,
            self._location_detection_commands
        )

        GcodePositionProcessor.Initialize(cpp_position_args)

        self._slicer_features = None if snapshot_profile is None else SlicerPrintFeatures(
            printer_profile.get_current_slicer_settings(), snapshot_profile
        )
        self.feature_restrictions_enabled = (
            False if snapshot_profile is None else snapshot_profile.feature_restrictions_enabled
        )
        self._auto_detect_position = printer_profile.auto_detect_position
        self._priming_height = printer_profile.priming_height
        self._position_restrictions = None if snapshot_profile is None else snapshot_profile.position_restrictions
        self._octoprint_printer_profile = octoprint_printer_profile
        self._origin = {
            "x": printer_profile.origin_x,
            "y": printer_profile.origin_y,
            "z": printer_profile.origin_z
        }

        self._retraction_length = self._gcode_generation_settings.retraction_length

        self._has_restricted_position = False if snapshot_profile is None else (
            len(snapshot_profile.position_restrictions) > 0 and snapshot_profile.position_restrictions_enabled
        )
        # Todo:  make sure this setting is being read correctly, it doesn't look correct
        if printer_profile.g90_influences_extruder in ['true', 'false']:
            self.g90_influences_extruder = True if printer_profile.g90_influences_extruder == 'true' else False
        else:
            self.g90_influences_extruder = g90_influences_extruder

        self._gcode_generation_settings = printer_profile.get_current_state_detection_settings()
        assert (isinstance(self._gcode_generation_settings, OctolapseGcodeSettings))
        self._z_lift_height = (
            0 if self._gcode_generation_settings.z_lift_height is None 
            else self._gcode_generation_settings.z_lift_height
        )
        self._priming_height = printer_profile.priming_height
        self._minimum_layer_height = printer_profile.minimum_layer_height

        current_pos_cpp = GcodePositionProcessor.GetCurrentPositionTuple(self.key)
        previous_pos_cpp = GcodePositionProcessor.GetPreviousPositionTuple(self.key)

        self.current_pos = Pos.create_from_cpp_pos(current_pos_cpp)
        self.previous_pos = Pos.create_from_cpp_pos(current_pos_cpp)
        self.undo_pos = Pos()
        Pos.copy_from_cpp_pos(previous_pos_cpp, self.undo_pos)

    def update_position(self, x, y, z, e, f):
        cpp_pos = GcodePositionProcessor.UpdatePosition(
            self.key,
            0.0 if x is None else x,
            True if x is None else False,
            0.0 if y is None else y,
            True if y is None else False,
            0.0 if z is None else z,
            True if z is None else False,
            0.0 if e is None else e,
            True if e is None else False,
            0.0 if f is None else f,
            True if f is None else False,
        )

        Pos.copy_from_cpp_pos(cpp_pos, self.current_pos)


    def to_position_dict(self):
        ret_dict = self.current_pos.to_dict()
        ret_dict["features"] = self._slicer_features.get_printing_features_list(
            self.current_pos.f, self.current_pos.layer
        )
        return ret_dict

    def to_state_dict(self):
        return self.current_pos.to_state_dict()

    def distance_to_zlift(self):
        # get the lift amount, but don't restrict it so we can log properly
        return self.current_pos.distance_to_zlift(self._z_lift_height, True)

    def length_to_retract(self):
        return self.current_pos.length_to_retract(self._retraction_length)

    # TODO: do we need this?
    def x_relative_to_current(self, x):
        if x:
            return x - self.current_pos.x + self.current_pos.x_offset
        else:
            return self.current_pos.x - self.previous_pos.x

    # TODO: do we need this?
    def y_relative_to_current(self, y):
        if y:
            return y - self.current_pos.y + self.current_pos.y_offset
        else:
            return self.current_pos.y - self.previous_pos.y

    # TODO: do we need this?
    def e_relative_to_current(self, e):
        if e:
            return e - self.current_pos.e + self.current_pos.e_offset
        else:
            return self.current_pos.e - self.previous_pos.e

    def command_requires_location_detection(self, cmd):
        if self._auto_detect_position:
            if cmd in self._location_detection_commands:
                return True
        return False

    def undo_update(self):

        GcodePositionProcessor.Undo(self.key)
        # set pos to the previous pos and pop the current position
        if self.undo_pos is None:
            raise Exception("Cannot undo updates when there is less than one position in the position queue.")

        previous_position = self.current_pos
        self.current_pos = self.previous_pos
        self.previous_pos = self.undo_pos
        self.undo_pos = None
        return previous_position

    @staticmethod
    def copy_pos(source, target):
        """does not copy all items, only what is necessary for the Position.Update command"""
        target.f = source.f
        target.x = source.x
        target.x_offset = source.x_offset
        target.x_homed = source.x_homed
        target.y = source.y
        target.y_offset = source.y_offset
        target.y_homed = source.y_homed
        target.z = source.z
        target.z_offset = source.z_offset
        target.z_homed = source.z_homed
        target.e = source.e
        target.e_offset = source.e_offset
        target.is_relative = source.is_relative
        target.is_extruder_relative = source.is_extruder_relative
        target.is_metric = source.is_metric
        target.last_extrusion_height = source.last_extrusion_height
        target.layer = source.layer
        target.height = source.height
        target.is_printer_primed = source.is_printer_primed
        target.minimum_layer_height_reached = source.minimum_layer_height_reached
        target.firmware_retraction_length = source.firmware_retraction_length
        target.firmware_unretraction_additional_length = source.firmware_unretraction_additional_length
        target.firmware_retraction_feedrate = source.firmware_retraction_feedrate
        target.firmware_unretraction_feedrate = source.firmware_unretraction_feedrate
        target.firmware_z_lift = source.firmware_z_lift
        target.has_position_error = source.has_position_error
        target.position_error = source.position_error
        target.has_homed_position = source.has_homed_position
        target.has_one_feature_enabled = source.has_one_feature_enabled
        target.in_path_position = source.in_path_position
        target.is_zhop = source.is_zhop

        # Extruder Tracking
        target.e_relative = source.e_relative
        target.extrusion_length = source.extrusion_length
        target.extrusion_length_total = source.extrusion_length_total
        target.retraction_length = source.retraction_length
        target.deretraction_length = source.deretraction_length
        target.is_extruding_start = source.is_extruding_start
        target.is_extruding = source.is_extruding
        target.is_primed = source.is_primed
        target.is_retracting_start = source.is_retracting_start
        target.is_retracting = source.is_retracting
        target.is_retracted = source.is_retracted
        target.is_partially_retracted = source.is_partially_retracted
        target.is_deretracting_start = source.is_deretracting_start
        target.is_deretracting = source.is_deretracting
        target.is_deretracted = source.is_deretracted
        target.is_in_position = source.is_in_position

        # Resets state changes
        target.is_layer_change = False
        target.is_height_change = False
        target.is_travel_only = False
        target.has_position_changed = False
        target.has_state_changed = False
        target.has_received_home_command = False

    def update(self, gcode):
        # Move the current position to the previous and the previous to the undo position
        # then copy previous to current
        if self.undo_pos is None:
            self.undo_pos = Pos()
        old_undo_pos = self.undo_pos
        self.undo_pos = self.previous_pos
        self.previous_pos = self.current_pos
        self.current_pos = old_undo_pos
        # TODO:  We probably don't need to copy previous since we'll get the current pos from 'Update' below
        Position.copy_pos(self.previous_pos, self.current_pos)

        previous = self.previous_pos
        current = self.current_pos

        # parse the gcode command
        cpp_pos = GcodePositionProcessor.Update(self.key, gcode)
        current = Pos.copy_from_cpp_pos(cpp_pos, current)

        # apply the cmd to the position tracker
        # cmd = current.parsed_command.cmd
        cmd = current.parsed_command.cmd

        # Update Extruder States - Note that e_relative must be rounded and non-null
        if current.has_position_changed:
            # Calcluate position restructions
            if self._has_restricted_position:
                # If we have a homed for the current and previous position, and either the exturder or position has
                # # changed
                if (
                    current.x is not None and
                    current.y is not None and
                    previous.x is not None and
                    previous.y is not None
                ):
                    # If we're using restricted positions, calculate intersections and determine if we are in position
                    can_calculate_intersections = current.parsed_command.cmd in ["G0", "G1"]
                    _is_in_position, _intersections = self.calculate_path_intersections(
                        self._position_restrictions,
                        current.x,
                        current.y,
                        previous.x,
                        previous.y,
                        can_calculate_intersections
                    )
                    if _is_in_position:
                        current.is_in_position = _is_in_position

                    else:
                        current.in_path_position = _intersections
            else:
                current.is_in_position = True


            # Update Feature Detection
            if self.feature_restrictions_enabled:
                if current.f is not None or current.has_position_changed:
                    # see if at least one feature is enabled, or if feature detection is disabled
                    current.has_one_feature_enabled = self._slicer_features.is_one_feature_enabled(
                        current.f, current.layer
                    )
            else:
                current.has_one_feature_enabled = True

    #def process_g2_g3(self, cmd):
    #    parameters = self.current_pos.parsed_command.parameters
    #    # Movement Type
    #    if cmd == "G2":
    #        movement_type = "clockwise"
    #        #self._logger.log_position_command_received("Received G2 - Clockwise Arc")
    #    else:
    #        movement_type = "counter-clockwise"
    #        #self._logger.log_position_command_received("Received G3 - Counter-Clockwise Arc")
#
    #    x = parameters["X"] if "X" in parameters else None
    #    y = parameters["Y"] if "Y" in parameters else None
    #    i = parameters["I"] if "I" in parameters else None
    #    j = parameters["J"] if "J" in parameters else None
    #    r = parameters["R"] if "R" in parameters else None
    #    e = parameters["E"] if "E" in parameters else None
    #    f = parameters["F"] if "F" in parameters else None
#
    #    # If we're moving on the X/Y plane only, mark this position as travel only
    #    self.current_pos.is_travel_only = e is None
#
    #    can_update_position = False
    #    if r is not None and (i is not None or j is not None):
    #        # todo:  deal with logging!  Doesn't work in multiprocessing because of pickle
    #        pass
    #        #self._logger.log_error("Received {0} - but received R and either I or J, which is not allowed.".format(cmd))
    #    elif i is not None or j is not None:
    #        # IJ Form
    #        if x is not None and y is not None:
    #            # not a circle, the position has changed
    #            can_update_position = True
    #            #self._logger.log_info("Cannot yet calculate position restriction intersections when G2/G3.")
    #    elif r is not None:
    #        # R Form
    #        if x is None and y is None:
    #            # Todo: deal with logging, doesn't work in multiprocessing or with pickle
    #            pass
    #            #self._logger.log_error("Received {0} - but received R without x or y, which is not allowed.".format(cmd))
    #        else:
    #            can_update_position = True
    #            #self._logger.log_info("Cannot yet calculate position restriction intersections when G2/G3.")
#
    #    if can_update_position:
    #        self.current_pos.update_position(x, y, None, e, f)
#
    #        message = "Position Change - {0} - {1} {2} Arc From(X:{3},Y:{4},Z:{5},E:{6}) - To(X:{7},Y:{8}," \
    #                  "Z:{9},E:{10})"
    #        if self.previous_pos is None:
    #            message = message.format(
    #                self.current_pos.parsed_command.gcode, "Relative" if self.current_pos.is_relative else "Absolute",
    #                movement_type, "None", "None", "None", "None", self.current_pos.x, self.current_pos.y,
    #                self.current_pos.z, self.current_pos.e
    #            )
    #        else:
    #            message = message.format(
    #                self.current_pos.parsed_command.gcode, "Relative" if self.current_pos.is_relative else "Absolute",
    #                movement_type,
    #                self.previous_pos.x,
    #                self.previous_pos.y, self.previous_pos.z, self.previous_pos.e, self.current_pos.x,
    #                self.current_pos.y, self.current_pos.z, self.current_pos.e)
    #        #self._logger.log_position_change(message)
#
    #def process_g10(self):
    #    parameters = self.current_pos.parsed_command.parameters
    #    if "P" not in parameters:
    #        e = (
    #            0 if self.current_pos.firmware_retraction_length is None
    #            else -1.0 * self.current_pos.firmware_retraction_length
    #        )
    #        previous_extruder_relative = self.current_pos.is_extruder_relative
    #        previous_relative = self.current_pos.is_relative
#
    #        self.current_pos.is_relative = True
    #        self.current_pos.is_extruder_relative = True
    #        self.current_pos.update_position(None, None, self.current_pos.firmware_z_lift, e,
    #                                         self.current_pos.firmware_retraction_feedrate)
    #        self.current_pos.is_relative = previous_relative
    #        self.current_pos.is_extruder_relative = previous_extruder_relative
#
    #def process_g11(self):
    #    lift_distance = 0 if self.current_pos.firmware_z_lift is None else -1.0 * self.current_pos.firmware_z_lift
    #    e = 0 if self.current_pos.firmware_retraction_length is None else self.current_pos.firmware_retraction_length
#
    #    if self.current_pos.firmware_unretraction_feedrate is not None:
    #        f = self.current_pos.firmware_unretraction_feedrate
    #    else:
    #        f = self.current_pos.firmware_retraction_feedrate
#
    #    if self.current_pos.firmware_unretraction_additional_length:
    #        e = e + self.current_pos.firmware_unretraction_additional_length
#
    #    previous_extruder_relative = self.current_pos.is_extruder_relative
    #    previous_relative = self.current_pos.is_relative
#
    #    self.current_pos.is_relative = True
    #    self.current_pos.is_extruder_relative = True
#
    #    # Todo:  verify this next line
    #    self.current_pos.update_position(None, None, lift_distance, e, f)
    #    self.current_pos.is_relative = previous_relative
    #    self.current_pos.is_extruder_relative = previous_extruder_relative

    #def process_g20(self):
    #    # change units to inches
    #    if self.current_pos.is_metric is None or self.current_pos.is_metric:
    #        self.current_pos.is_metric = False
#
    #def process_g21(self):
    #    # change units to millimeters
    #    if self.current_pos.is_metric is None or not self.current_pos.is_metric:
    #        self.current_pos.is_metric = True

    #def process_m207(self):
    #    parameters = self.current_pos.parsed_command.parameters
    #    # Firmware Retraction Tracking
    #    if "S" in parameters:
    #        self.current_pos.firmware_retraction_length = parameters["S"]
    #    if "R" in parameters:
    #        self.current_pos.firmware_unretraction_additional_length = parameters["R"]
    #    if "F" in parameters:
    #        self.current_pos.firmware_retraction_feedrate = parameters["F"]
    #    if "T" in parameters:
    #        self.current_pos.firmware_unretraction_feedrate = parameters["T"]
    #    if "Z" in parameters:
    #        self.current_pos.firmware_z_lift = parameters["Z"]
#
    #def process_m208(self):
    #    parameters = self.current_pos.parsed_command.parameters
    #    # Firmware Retraction Tracking
    #    if "S" in parameters:
    #        self.current_pos.firmware_unretraction_additional_length = parameters["S"]
    #    if "F" in parameters:
    #        self.current_pos.firmware_unretraction_feedrate = parameters["F"]

    # Eventually this code will support the G161 and G162 commands
    # Hold this code for the future
    # Not ready to be released as of now.
    # def _g161_received(self, pos):
    #     # Home
    #     pos.has_received_home_command = True
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
    #         pos.x_homed = True
    #         pos.X = self._origin["x"] if not self._auto_detect_position else None
    #         if pos.X is None:
    #             home_strings.append("Homing X to Unknown Origin.")
    #         else:
    #             home_strings.append("Homing X to {0}.".format(
    #                 get_formatted_coordinate(pos.X)))
    #     if y_homed:
    #         pos.y_homed = True
    #         pos.Y = self._origin["y"] if not self._auto_detect_position else None
    #         if pos.Y is None:
    #             home_strings.append("Homing Y to Unknown Origin.")
    #         else:
    #             home_strings.append("Homing Y to {0}.".format(
    #                 get_formatted_coordinate(pos.Y)))
    #     if z_homed:
    #         pos.z_homed = True
    #         pos.Z = self._origin["z"] if not self._auto_detect_position else None
    #         if pos.Z is None:
    #             home_strings.append("Homing Z to Unknown Origin.")
    #         else:
    #             home_strings.append("Homing Z to {0}.".format(
    #                 get_formatted_coordinate(pos.Z)))
    #
    #     self._logger.log_position_command_received(
    #         "Received G161 - ".format(" ".join(home_strings)))
    #     pos.has_position_error = False
    #     pos.position_error = None
    #
    # def _g162_received(self, pos):
    #     # Home
    #     pos.has_received_home_command = True
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
    #         pos.x_homed = True
    #         pos.X = self._origin["x"] if not self._auto_detect_position else None
    #         if pos.X is None:
    #             home_strings.append("Homing X to Unknown Origin.")
    #         else:
    #             home_strings.append("Homing X to {0}.".format(
    #                 get_formatted_coordinate(pos.X)))
    #     if y_homed:
    #         pos.y_homed = True
    #         pos.Y = self._origin["y"] if not self._auto_detect_position else None
    #         if pos.Y is None:
    #             home_strings.append("Homing Y to Unknown Origin.")
    #         else:
    #             home_strings.append("Homing Y to {0}.".format(
    #                 get_formatted_coordinate(pos.Y)))
    #     if z_homed:
    #         pos.z_homed = True
    #         pos.Z = self._origin["z"] if not self._auto_detect_position else None
    #         if pos.Z is None:
    #             home_strings.append("Homing Z to Unknown Origin.")
    #         else:
    #             home_strings.append("Homing Z to {0}.".format(
    #                 get_formatted_coordinate(pos.Z)))
    #
    #     self._logger.log_position_command_received(
    #         "Received G162 - ".format(" ".join(home_strings)))
    #     pos.has_position_error = False
    #     pos.position_error = None

    def calculate_path_intersections(self, restrictions, x, y, previous_x, previous_y, can_calculate_intersections):

        if self.calculate_is_in_position(
            restrictions,
            x,
            y,
            utility.FLOAT_MATH_EQUALITY_RANGE
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
            utility.FLOAT_MATH_EQUALITY_RANGE
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
            options.on_extruding_start, self.current_pos.is_extruding_start
        )
        extruding_triggered = self._extruder_state_triggered(
            options.on_extruding, self.current_pos.is_extruding
        )
        primed_triggered = self._extruder_state_triggered(
            options.on_primed, self.current_pos.is_primed
        )
        retracting_start_triggered = self._extruder_state_triggered(
            options.on_retracting_start, self.current_pos.is_retracting_start
        )
        retracting_triggered = self._extruder_state_triggered(
            options.on_retracting, self.current_pos.is_retracting
        )
        partially_retracted_triggered = self._extruder_state_triggered(
            options.on_partially_retracted, self.current_pos.is_partially_retracted
        )
        retracted_triggered = self._extruder_state_triggered(
            options.on_retracted, self.current_pos.is_retracted
        )
        deretracting_start_triggered = self._extruder_state_triggered(
            options.on_deretracting_start, self.current_pos.is_deretracting_start
        )
        deretracting_triggered = self._extruder_state_triggered(
            options.on_deretracting, self.current_pos.is_deretracting
        )
        deretracted_triggered = self._extruder_state_triggered(
            options.on_deretracted, self.current_pos.is_deretracted
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
        'on_extruding_start',
        'on_extruding',
        'on_primed',
        'on_retracting_start',
        'on_retracting',
        'on_partially_retracted',
        'on_retracted',
        'on_deretracting_start',
        'on_deretracting',
        'on_deretracted'
    ]

    def __init__(
        self, on_extruding_start, on_extruding, on_primed, on_retracting_start, on_retracting, on_partially_retracted,
        on_retracted, on_deretracting_start, on_deretracting, on_deretracted
    ):
        # To trigger on an extruder state, set to True.
        # To prevent triggering on an extruder state, set to False.
        # To ignore the extruder state, set to None
        self.on_extruding_start = on_extruding_start
        self.on_extruding = on_extruding
        self.on_primed = on_primed
        self.on_retracting_start = on_retracting_start
        self.on_retracting = on_retracting
        self.on_partially_retracted = on_partially_retracted
        self.on_retracted = on_retracted
        self.on_deretracting_start = on_deretracting_start
        self.on_deretracting = on_deretracting
        self.on_deretracted = on_deretracted

    def are_all_triggers_ignored(self):
        if (
            self.on_extruding_start is None
            and self.on_extruding is None
            and self.on_primed is None
            and self.on_retracting_start is None
            and self.on_retracting is None
            and self.on_partially_retracted is None
            and self.on_retracted is None
            and self.on_deretracting_start is None
            and self.on_deretracting is None
            and self.on_deretracted is None
        ):
            return True
        return False
