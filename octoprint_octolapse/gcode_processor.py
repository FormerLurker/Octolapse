# coding=utf-8
##################################################################################
# Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
# Copyright (C) 2023  Brad Hochgesang
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

import GcodePositionProcessor
import octoprint_octolapse.utility as utility

# create the module level logger
from octoprint_octolapse.log import LoggingConfigurator
logging_configurator = LoggingConfigurator()
logger = logging_configurator.get_logger(__name__)


class Extruder(utility.JsonSerializable):
    __slots__ = [
        "x_firmware_offset",
        "y_firmware_offset",
        "z_firmware_offset",
        "e",
        "e_offset",
        "e_relative",
        "extrusion_length",
        "extrusion_length_total",
        "retraction_length",
        "deretraction_length",
        "is_extruding_start",
        "is_extruding",
        "is_primed",
        "is_retracting_start",
        "is_retracting",
        "is_retracted",
        "is_partially_retracted",
        "is_deretracting_start",
        "is_deretracting",
        "is_deretracted"
    ]

    def __init__(self, copy_from=None):
        if copy_from is None:
            self.x_firmware_offset = 0
            self.y_firmware_offset = 0
            self.z_firmware_offset = 0
            self.e = 0
            self.e_offset = 0
            self.e_relative = False
            self.extrusion_length = 0
            self.extrusion_length_total = 0
            self.retraction_length = 0
            self.deretraction_length = 0
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
        else:
            self.x_firmware_offset = copy_from.x_firmware_offset
            self.y_firmware_offset = copy_from.y_firmware_offset
            self.z_firmware_offset = copy_from.z_firmware_offset
            self.e = copy_from.e
            self.e_offset = copy_from.e_offset
            self.e_relative = copy_from.e_relative
            self.extrusion_length = copy_from.extrusion_length
            self.extrusion_length_total = copy_from.extrusion_length_total
            self.retraction_length = copy_from.retraction_length
            self.deretraction_length = copy_from.deretraction_length
            self.is_extruding_start = copy_from.is_extruding_start
            self.is_extruding = copy_from.is_extruding
            self.is_primed = copy_from.is_primed
            self.is_retracting_start = copy_from.is_retracting_start
            self.is_retracting = copy_from.is_retracting
            self.is_retracted = copy_from.is_retracted
            self.is_partially_retracted = copy_from.is_partially_retracted
            self.is_deretracting_start = copy_from.is_deretracting_start
            self.is_deretracting = copy_from.is_deretracting
            self.is_deretracted = copy_from.is_deretracted

    @staticmethod
    def copy_from_cpp_extruder(cpp_extruder, target):
        target.x_firmware_offset = cpp_extruder[0]
        target.y_firmware_offset = cpp_extruder[1]
        target.z_firmware_offset = cpp_extruder[2]
        target.e = cpp_extruder[3]
        target.e_offset = cpp_extruder[4]
        target.e_relative = cpp_extruder[5]
        target.extrusion_length = cpp_extruder[6]
        target.extrusion_length_total = cpp_extruder[7]
        target.retraction_length = cpp_extruder[8]
        target.deretraction_length = cpp_extruder[9]
        target.is_extruding_start = cpp_extruder[10] > 0
        target.is_extruding = cpp_extruder[11] > 0
        target.is_primed = cpp_extruder[12] > 0
        target.is_retracting_start = cpp_extruder[13] > 0
        target.is_retracting = cpp_extruder[14] > 0
        target.is_retracted = cpp_extruder[15] > 0
        target.is_partially_retracted = cpp_extruder[16] > 0
        target.is_deretracting_start = cpp_extruder[17] > 0
        target.is_deretracting = cpp_extruder[18] > 0
        target.is_deretracted = cpp_extruder[19] > 0

    @staticmethod
    def create_from_cpp_extruder(cpp_extruder):
        extruder = Extruder()
        Extruder.copy_from_cpp_extruder(cpp_extruder, extruder)
        return extruder

    def to_dict(self):
        return {
            "x_firmware_offset": self.x_firmware_offset,
            "y_firmware_offset": self.y_firmware_offset,
            "z_firmware_offset": self.z_firmware_offset,
            "e": self.e,
            "e_offset": self.e_offset,
            "e_relative": self.e_relative,
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
            "is_deretracted": self.is_deretracted
        }


class Pos(utility.JsonSerializable):
    # Add slots for faster copy and init
    __slots__ = [
        "x",
        "y",
        "z",
        "f",
        "x_offset",
        "y_offset",
        "z_offset",
        "x_firmware_offset",
        "y_firmware_offset",
        "z_firmware_offset",
        "z_relative",
        "last_extrusion_height",
        "height",
        "firmware_retraction_length",
        "firmware_unretraction_additional_length",
        "firmware_retraction_feedrate",
        "firmware_unretraction_feedrate",
        "firmware_z_lift",
        "layer",
        "height_increment",
        "height_increment_change_count",
        "current_tool",
        "num_extruders",
        "x_homed",
        "y_homed",
        "z_homed",
        "is_relative",
        "is_extruder_relative",
        "is_metric",
        "is_printer_primed",
        "has_definite_position",
        "is_layer_change",
        "is_height_change",
        "is_height_increment_change",
        "is_xy_travel",
        "is_xyz_travel",
        "is_zhop",
        "has_xy_position_changed",
        "has_position_changed",
        "has_received_home_command",
        "is_in_position",
        "in_path_position",
        "file_line_number",
        "gcode_number",
        "file_position",
        "is_in_bounds",
        "parsed_command",
        "extruders"
    ]

    min_length_to_retract = 0.0001

    def __init__(self):
        self.parsed_command = None
        self.f = None
        self.x = None
        self.x_offset = 0
        self.x_firmware_offset = 0
        self.x_homed = False
        self.y = None
        self.y_offset = 0
        self.y_firmware_offset = 0
        self.y_homed = False
        self.z = None
        self.z_offset = 0
        self.z_firmware_offset = 0
        self.z_homed = False
        self.z_relative = 0
        self.is_relative = False
        self.is_extruder_relative = False
        self.is_metric = True
        self.last_extrusion_height = None
        self.layer = 0
        self.height_increment = 0
        self.height_increment_change_count = 0
        self.height = 0
        self.is_printer_primed = False
        self.firmware_retraction_length = None
        self.firmware_unretraction_additional_length = None
        self.firmware_retraction_feedrate = None
        self.firmware_unretraction_feedrate = None
        self.firmware_z_lift = None
        self.has_definite_position = False
        # Extruders
        self.current_tool = None
        self.extruders = []

        # State
        self.is_layer_change = False
        self.is_height_change = False
        self.is_height_increment_change = False
        self.is_xy_travel = False
        self.is_xyz_travel = False
        self.is_zhop = False
        self.has_xy_position_changed = False
        self.has_position_changed = False
        self.has_received_home_command = False
        self.is_in_position = False
        self.in_path_position = False
        self.is_in_bounds = True
        # Gcode File Tracking
        self.file_line_number = -1
        self.gcode_number = -1
        self.file_position = -1

    @staticmethod
    def copy_from_cpp_pos(cpp_pos, target):
        target.x = None if cpp_pos[43] > 0 else cpp_pos[0]
        target.y = None if cpp_pos[44] > 0 else cpp_pos[1]
        target.z = None if cpp_pos[45] > 0 else cpp_pos[2]
        target.f = None if cpp_pos[46] > 0 else cpp_pos[3]
        target.x_offset = cpp_pos[4]
        target.y_offset = cpp_pos[5]
        target.z_offset = cpp_pos[6]
        target.x_firmware_offset = cpp_pos[7]
        target.y_firmware_offset = cpp_pos[8]
        target.z_firmware_offset = cpp_pos[9]
        target.z_relative = cpp_pos[10]
        target.last_extrusion_height = None if cpp_pos[49] > 0 else cpp_pos[11]
        target.height = cpp_pos[12]
        target.firmware_retraction_length = None if cpp_pos[51] > 0 else cpp_pos[13]
        target.firmware_unretraction_additional_length = None if cpp_pos[52] > 0 else cpp_pos[14]
        target.firmware_retraction_feedrate = None if cpp_pos[53] > 0 else cpp_pos[15]
        target.firmware_unretraction_feedrate = None if cpp_pos[54] > 0 else cpp_pos[16]
        target.firmware_z_lift = None if cpp_pos[55] > 0 else cpp_pos[17]
        target.layer = cpp_pos[18]
        target.height_increment = cpp_pos[19]
        target.height_increment_change_count = cpp_pos[20]
        target.current_tool = cpp_pos[21]
        target.num_extruders = cpp_pos[22]
        target.x_homed = cpp_pos[23] > 0
        target.y_homed = cpp_pos[24] > 0
        target.z_homed = cpp_pos[25] > 0
        target.is_relative = None if cpp_pos[47] > 0 else cpp_pos[26] > 0
        target.is_extruder_relative = None if cpp_pos[48] > 0 else cpp_pos[27] > 0
        target.is_metric = None if cpp_pos[50] > 0 else cpp_pos[28] > 0
        target.is_printer_primed = cpp_pos[29] > 0
        target.has_definite_position = cpp_pos[30] > 0

        target.is_layer_change = cpp_pos[31] > 0
        target.is_height_change = cpp_pos[32] > 0
        target.is_height_increment_change = cpp_pos[33]
        target.is_xy_travel = cpp_pos[34] > 0
        target.is_xyz_travel = cpp_pos[35] > 0
        target.is_zhop = cpp_pos[36] > 0
        target.has_xy_position_changed = cpp_pos[37] > 0
        target.has_position_changed = cpp_pos[38] > 0
        target.has_received_home_command = cpp_pos[39] > 0
        # Todo:  figure out how to deal with these things which must be currently ignored
        target.is_in_position = cpp_pos[40] > 0
        target.in_path_position = cpp_pos[41] > 0
        target.is_in_bounds = cpp_pos[42] > 0
        target.file_line_number = cpp_pos[56]
        target.gcode_number = cpp_pos[57]
        target.file_position = cpp_pos[58]
        parsed_command = cpp_pos[59]
        if parsed_command is not None:
            target.parsed_command = ParsedCommand(parsed_command[0], parsed_command[1], parsed_command[2], parsed_command[3])
        else:
            target.parsed_command = None
        extruders = cpp_pos[60]
        if extruders is not None:
            target.extruders = []
            for extruder in extruders:
                target.extruders.append(Extruder.create_from_cpp_extruder(extruder))
        else:
            target.extruders = None

        return target

    @staticmethod
    def create_from_cpp_pos(cpp_pos):
        pos = Pos()
        Pos.copy_from_cpp_pos(cpp_pos, pos)
        return pos

    @staticmethod
    def copy(source, target):
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
        target.is_relative = source.is_relative
        target.is_extruder_relative = source.is_extruder_relative
        target.is_metric = source.is_metric
        target.last_extrusion_height = source.last_extrusion_height
        target.layer = source.layer
        target.height_increment = source.height_increment
        target.height_increment_change_count = source.height_increment_change_count
        target.height = source.height
        target.is_printer_primed = source.is_printer_primed
        target.firmware_retraction_length = source.firmware_retraction_length
        target.firmware_unretraction_additional_length = source.firmware_unretraction_additional_length
        target.firmware_retraction_feedrate = source.firmware_retraction_feedrate
        target.firmware_unretraction_feedrate = source.firmware_unretraction_feedrate
        target.firmware_z_lift = source.firmware_z_lift
        target.has_definite_position = source.has_definite_position
        target.in_path_position = source.in_path_position
        target.is_zhop = source.is_zhop
        target.is_in_position = source.is_in_position

        # copy extruders
        target.extruders = []
        for extruder in source.extruders:
            target.extruders.append(Extruder(copy_from=extruder))

        # Resets state changes
        target.is_layer_change = False
        target.is_height_change = False
        target.is_height_increment_change = False
        target.is_xy_travel = False
        target.has_position_changed = False
        target.has_received_home_command = False
        target.is_in_bounds = True

    def get_current_extruder(self):
        if len(self.extruders) == 0:
            logger.error("The current extruder was requested, but none was found.")
            return None

        tool_index = self.current_tool
        if tool_index > len(self.extruders) - 1:
            tool_index = len(self.extruders) - 1
            logger.warning("The requested tool index of %d is greater than the number of extruders ($d).",
                           self.current_tool, len(self.extruders))
        if tool_index < 0:
            tool_index = 0
            logger.warning("The requested tool index was less than zero.  Index: %d.",
                           self.current_tool)
        return self.extruders[tool_index]

    def to_extruder_state_dict(self):
        extruder = self.get_current_extruder()
        return {
            "current_tool": self.current_tool,
            "x_firmware_offset": self.x_firmware_offset,
            "y_firmware_offset": self.y_firmware_offset,
            "z_firmware_offset": self.z_firmware_offset,
            "e": extruder.e_relative,
            "extrusion_length": extruder.extrusion_length,
            "extrusion_length_total": extruder.extrusion_length_total,
            "retraction_length": extruder.retraction_length,
            "deretraction_length": extruder.deretraction_length,
            "is_extruding_start": extruder.is_extruding_start,
            "is_extruding": extruder.is_extruding,
            "is_primed": extruder.is_primed,
            "is_retracting_start": extruder.is_retracting_start,
            "is_retracting": extruder.is_retracting,
            "is_retracted": extruder.is_retracted,
            "is_partially_retracted": extruder.is_partially_retracted,
            "is_deretracting_start": extruder.is_deretracting_start,
            "is_deretracting": extruder.is_deretracting,
            "is_deretracted": extruder.is_deretracted
        }

    def to_state_dict(self):
        return {
            "gcode": "" if self.parsed_command is None else self.parsed_command.gcode,
            "x_homed": self.x_homed,
            "y_homed": self.y_homed,
            "z_homed": self.z_homed,
            "has_definite_position": self.has_definite_position,
            "is_layer_change": self.is_layer_change,
            "is_height_change": self.is_height_change,
            "is_height_increment_change": self.is_height_change,
            "is_zhop": self.is_zhop,
            "is_relative": self.is_relative,
            "is_extruder_relative": self.is_extruder_relative,
            "is_metric": self.is_metric,
            "layer": self.layer,
            "height": self.height,
            "last_extrusion_height": self.last_extrusion_height,
            "is_in_position": self.is_in_position,
            "in_path_position": self.in_path_position,
            "is_printer_primed": self.is_printer_primed,
            "has_received_home_command": self.has_received_home_command,
            "is_xy_travel": self.is_xy_travel,
            "is_in_bounds": self.is_in_bounds,
        }

    def to_position_dict(self):
        extruder = self.get_current_extruder()
        return {
            "current_tool": self.current_tool,
            "f": self.f,
            "x": self.x,
            "x_offset": self.x_offset,
            "x_firmware_offset": self.x_firmware_offset,
            "y": self.y,
            "y_offset": self.y_offset,
            "y_firmware_offset": self.y_firmware_offset,
            "z": self.z,
            "z_offset": self.z_offset,
            "z_firmware_offset": self.z_firmware_offset,
            "e": extruder.e,
            "e_offset": extruder.e_offset
        }

    def to_dict(self):
        extruder = self.get_current_extruder()
        return {
            "current_tool": self.current_tool,
            "gcode": "" if self.parsed_command is None else self.parsed_command.gcode,
            "f": self.f,
            "x": self.x,
            "x_offset": self.x_offset,
            "x_firmware_offset": self.x_firmware_offset,
            "x_homed": self.x_homed,
            "y": self.y,
            "y_offset": self.y_offset,
            "y_firmware_offset": self.y_firmware_offset,
            "y_homed": self.y_homed,
            "z": self.z,
            "z_offset": self.z_offset,
            "z_firmware_offset": self.z_firmware_offset,
            "z_homed": self.z_homed,
            "z_relative": self.z_relative,
            "e": extruder.e,
            "e_offset": extruder.e_offset,
            "is_relative": self.is_relative,
            "is_extruder_relative": self.is_extruder_relative,
            "is_metric": self.is_metric,
            "last_extrusion_height": self.last_extrusion_height,
            "is_layer_change": self.is_layer_change,
            "is_height_increment_change": self.is_height_increment_change,
            "is_zhop": self.is_zhop,
            "is_in_position": self.is_in_position,
            "in_path_position": self.in_path_position,
            "is_primed": self.is_printer_primed,
            "has_xy_position_changed": self.has_xy_position_changed,
            "has_position_changed": self.has_position_changed,
            "layer": self.layer,
            "height_increment": self.height_increment,
            "height_increment_change_count": self.height_increment_change_count,
            "height": self.height,
            "has_received_home_command": self.has_received_home_command,
            "file_line_number": self.file_line_number,
            "gcode_number": self.gcode_number,
            "file_position": self.file_position,
            "is_in_bounds": self.is_in_bounds,
            "extruders": [x.to_dict() for x in self.extruders]
        }

    def distance_to_zlift(self, z_hop, restrict_lift_height=True):
        amount_to_lift = (
            None if self.z is None or
            self.last_extrusion_height is None
            else z_hop - (self.z - self.last_extrusion_height)
        )
        if amount_to_lift is None:
            return 0
        if restrict_lift_height:
            if amount_to_lift < utility.FLOAT_MATH_EQUALITY_RANGE:
                return 0
            elif amount_to_lift > z_hop:
                return z_hop
        return utility.round_to(amount_to_lift, utility.FLOAT_MATH_EQUALITY_RANGE)

    def length_to_retract(self, amount_to_retract):
        extruder = self.get_current_extruder()
        # if we don't have any history, we want to retract
        retract_length = utility.round_to_float_equality_range(
            utility.round_to_float_equality_range(amount_to_retract - extruder.retraction_length)
        )
        if retract_length < 0:
            retract_length = 0
        elif retract_length > amount_to_retract:
            retract_length = amount_to_retract
        elif retract_length < Pos.min_length_to_retract:
            # we don't want to retract less than the min_length_to_retract,
            # else we might have quality issues!
            retract_length = 0
        # return the calculated retraction length
        return retract_length

    def gcode_x(self, x=None):
        if x is None:
            x = self.x
        return x - self.x_offset + self.x_firmware_offset

    def gcode_y(self, y=None):
        if y is None:
            y = self.y
        return y - self.y_offset + self.y_firmware_offset

    def gcode_z(self, z=None):
        if z is None:
            z = self.z
        return z - self.z_offset + self.z_firmware_offset

    def gcode_e(self, e=None):
        extruder = self.get_current_extruder()
        if e is None:
            e = extruder.e
        return e - extruder.e_offset


class ParsedCommand(utility.JsonSerializable):
    # define slots for faster creation
    __slots__ = ['cmd', 'parameters', 'gcode', 'comment']

    def __init__(self, cmd, parameters, gcode, comment=None):
        self.cmd = cmd
        self.parameters = {} if parameters is None else parameters
        self.gcode = gcode
        self. comment = comment

    def to_dict(self):
        return {
            "cmd": self.cmd,
            "parameters": self.parameters,
            "gcode": self.gcode,
            "comment": self.comment
        }

    def update_gcode_string(self):
        self.gcode = ParsedCommand.to_string(self)

    @classmethod
    def create_from_cpp_parsed_command(cls, cpp_parsed_command):
        return ParsedCommand(cpp_parsed_command[0], cpp_parsed_command[1], cpp_parsed_command[2], cpp_parsed_command[3])

    @staticmethod
    def clean_gcode(gcode):
        if gcode is None:
            return None, None
        # strip off any trailing comments
        comment = ""
        ix = gcode.find(";")
        if ix > -1:
            # we have a comment!
            # see if we have anything AFTER the semicolon
            if ix+1 < len(gcode):
                comment = gcode[ix+1:].strip()
                gcode = gcode[0:ix]
        # remove any duplicated whitespace, replace all whitespace with a ' ' and make upper case
        gcode = ' '.join(gcode.upper())
        return gcode.strip().upper(), comment

    @staticmethod
    def to_string(parsed_command):
        has_parameters = False
        parameter_strings = []
        for key, value in parsed_command.parameters.items():
            has_parameters = True
            if value is None:
                value_string = ""
            elif isinstance(value, float):
                if key == "E":
                    value_string = "{0:.5f}".format(value)
                else:
                    value_string = "{0:.3f}".format(value)
            else:
                value_string = "{0}".format(value)

            parameter_strings.append("{0}{1}".format(key,value_string))

        if has_parameters:
            separator = " "
        else:
            separator = ""

        return "{0}{1}{2}".format(parsed_command.cmd, separator, " ".join(parameter_strings))

    def is_octolapse_command(self):
        return self.cmd == "@OCTOLAPSE" and len(self.parameters) == 1


class GcodeProcessor(object):
    _key = "plugin_octolapse"

    @staticmethod
    def initialize_position_processor(position_args, key=_key):
        try:
            GcodePositionProcessor.Initialize(key, position_args)
            return True
        except Exception as e:
            logger.exception("An error occurred while initializing the GcodePositionProcessor!")
            raise e
        return False

    @staticmethod
    def parse(gcode):
        parsed_command_cpp = GcodePositionProcessor.Parse(gcode.encode('ascii', errors="replace").decode())
        if parsed_command_cpp:
            parsed_command = ParsedCommand.create_from_cpp_parsed_command(parsed_command_cpp)
        else:
            # do our best to create a parsed command since the C++ processor couldn't do it
            gcode, comment = ParsedCommand.clean_gcode(gcode)
            parsed_command = ParsedCommand(None, None, gcode, comment)

        return parsed_command

    @staticmethod
    def get_current_position(key=_key):
        current_pos_cpp = GcodePositionProcessor.GetCurrentPositionTuple(key)
        return Pos.create_from_cpp_pos(current_pos_cpp)

    @staticmethod
    def get_previous_position(key=_key):
        previous_pos_cpp = GcodePositionProcessor.GetPreviousPositionTuple(key)
        return Pos.create_from_cpp_pos(previous_pos_cpp)

    @staticmethod
    def update_position(position, x, y, z, e, f, key=_key):
        cpp_pos = GcodePositionProcessor.UpdatePosition(
            key,
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
        Pos.copy_from_cpp_pos(cpp_pos, position)
        return position

    @staticmethod
    def undo(key=_key):
        GcodePositionProcessor.Undo(key)

    @staticmethod
    def update(gcode, position, key=_key):
        cpp_pos = GcodePositionProcessor.Update(key, gcode)
        Pos.copy_from_cpp_pos(cpp_pos, position)
        return position


# class GcodeStabilizationProcessor(object):
#
#     @staticmethod
#     def smart_layer_stabilization(position_args, stabilization_args, smart_layer_args):
#         try:
#             ret_val = list(GcodePositionProcessor.GetSnapshotPlans_SmartLayer(
#                 position_args,
#                 stabilization_args,
#                 smart_layer_args
#             ))
#             return ret_val
#         except Exception as e:
#             logger.exception("An error occurred while running the smart_layer_stabilization processor.")
#             raise e
