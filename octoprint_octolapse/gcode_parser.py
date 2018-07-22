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
import operator
from six import string_types


class CommandParameter(object):
    def __init__(self, name, parse_function, order):
        self.Name = name
        self.ParseFunction = parse_function
        self.Order = order

    @staticmethod
    def parse_float_positive(parameter_string):
        value, parameters = CommandParameter.parse_float(parameter_string)
        if value is None:
            return None
        elif value < 0:
            raise ValueError("The parameter value is negative, which is not allowed.")

        return value, parameters

    @staticmethod
    def parse_float(parameter_string):
        assert (isinstance(parameter_string, string_types))
        parameter_string = parameter_string.lstrip()

        index = 0
        sign_seen = False
        period_seen = False

        float_string = ""
        for index in range(0, len(parameter_string)):
            _c = parameter_string[index]
            if _c.isspace():
                continue
            if _c in ["+", "-"]:
                if not sign_seen:
                    sign_seen = True
                    float_string += _c
                else:
                    raise ValueError("Could not parse float from parameter string, saw multiple signs.")
            elif "0" <= _c <= "9":
                float_string += _c
            elif _c == ".":
                if not period_seen:
                    float_string += _c
                    period_seen = True
                else:
                    raise ValueError("Could not parse float from parameter string, saw multiple decimal points.")
            else:
                break
        if len(parameter_string) > index:
            parameter_string = parameter_string[index:]
        else:
            parameter_string = ""

        value = None
        if len(float_string) > 0:
            value = float(float_string)

        return value, parameter_string


class Command(object):

    def __init__(self, command, name, display_template=None, parameters=None, text_only_parameter=False):
        self.Command = command
        self.Name = name
        self.DisplayTemplate = display_template
        self.Parameters = parameters
        self.TextOnlyParameter = text_only_parameter

    def parse_parameters(self, parameters_string):
        parameters = {}
        parameter = None
        parameter_cmd = None
        index = 0
        for index in range(0, len(parameters_string)):
            _c = parameters_string[index].upper()
            if _c.isspace():
                continue
            elif _c in self.Parameters:
                parameter = _c
                parameter_cmd = self.Parameters[parameter].ParseFunction

                break

        if parameter is not None and len(parameters_string) > 0:
            parameters_string = parameters_string[index + 1:]
            if parameter_cmd is not None:
                parameter_value, parameters_string = parameter_cmd(parameters_string)
                parameters[parameter] = parameter_value
                additional_parameters = self.parse_parameters(parameters_string)
                if any(filter(parameters.has_key, additional_parameters.keys())):
                    raise ValueError("Either a parameter value was repeated or an unexpected character was found, "
                                     "cannot parse gcode.")
                parameters.update(additional_parameters)

        return parameters

    def to_string(self):
        # if we do not have gcode, construct from the command and parameters
        command_string = self.Command

        # loop through each parameter and add the parameter name and value to the command string
        for parameter in (sorted(self.Parameters.values(), key=operator.attrgetter('Order'))):
            if parameter.Value is not None:
                command_string += " " + parameter.Name + str(parameter.Value)
        # since there is no gcode, we can't have a comment.  Time to return the command string
        return command_string


class Commands(object):
    G0 = Command(
        "G0",
        "Rapid linear move",
        "G0 - Linear move to X={X}, Y={Y}, Z={Z}, E={E}, F={F}",
        parameters={
            "X": CommandParameter("X", CommandParameter.parse_float, 1),
            "Y": CommandParameter("Y", CommandParameter.parse_float, 2),
            "Z": CommandParameter("Z", CommandParameter.parse_float, 3),
            "E": CommandParameter("E", CommandParameter.parse_float, 4),
            "F": CommandParameter("F", CommandParameter.parse_float_positive, 5)
        }
    )

    G1 = Command(
        "G1",
        "Linear move",
        "G1 - Linear move to X={X}, Y={Y}, Z={Z}, E={E}, F={F}",
        parameters={
            "X": CommandParameter("X", CommandParameter.parse_float, 1),
            "Y": CommandParameter("Y", CommandParameter.parse_float, 2),
            "Z": CommandParameter("Z", CommandParameter.parse_float, 3),
            "E": CommandParameter("E", CommandParameter.parse_float, 4),
            "F": CommandParameter("F", CommandParameter.parse_float_positive, 5)
        }
    )
    G2 = Command(
        "G2",
        "Clockwise Arc Move",
        "G2 - Clockwise arc move to X={X}, Y={Y}, I={I}, J={J}, R={R}, E={E}, F={F}",
        parameters={
            "X": CommandParameter("X", CommandParameter.parse_float, 1),
            "Y": CommandParameter("Y", CommandParameter.parse_float, 2),
            "I": CommandParameter("I", CommandParameter.parse_float, 3),
            "J": CommandParameter("J", CommandParameter.parse_float, 4),
            "R": CommandParameter("R", CommandParameter.parse_float, 5),
            "E": CommandParameter("E", CommandParameter.parse_float, 6),
            "F": CommandParameter("F", CommandParameter.parse_float_positive, 7)
        }
    )
    G3 = Command(
        "G3",
        "Counter-Clockwise Arc Move",
        "G3 - Counter-clockwise arc move to X={X}, Y={Y}, I={I}, J={J}, R={R}, E={E}, F={F}",
        parameters={
            "X": CommandParameter("X", CommandParameter.parse_float, 1),
            "Y": CommandParameter("Y", CommandParameter.parse_float, 2),
            "I": CommandParameter("I", CommandParameter.parse_float, 3),
            "J": CommandParameter("J", CommandParameter.parse_float, 4),
            "R": CommandParameter("R", CommandParameter.parse_float, 5),
            "E": CommandParameter("E", CommandParameter.parse_float, 6),
            "F": CommandParameter("F", CommandParameter.parse_float_positive, 7)
        }
    )
    G10 = Command(
        "G10",
        "Retract"
        "G10 - Retract or Tool Offset",
        parameters={
            "P": CommandParameter("P", CommandParameter.parse_float, 1),
            "X": CommandParameter("X", CommandParameter.parse_float, 1),
            "Y": CommandParameter("Y", CommandParameter.parse_float, 1),
            "U": CommandParameter("U", CommandParameter.parse_float, 1),
            "V": CommandParameter("V", CommandParameter.parse_float, 1),
            "W": CommandParameter("W", CommandParameter.parse_float, 1),
            "Z": CommandParameter("Z", CommandParameter.parse_float, 1),
            "R": CommandParameter("R", CommandParameter.parse_float, 1),
            "S": CommandParameter("S", CommandParameter.parse_float, 1)
        }
    )

    G11 = Command(
        "G11",
        "Retract"
        "G11 - Unretract",
        parameters={
            "S": CommandParameter("S", CommandParameter.parse_float, 1)
        }
    )
    G20 = Command(
        "G20",
        "Set units to inches"
        "G20 - Set Units to Inches",
        parameters={}
    )

    G21 = Command(
        "G21",
        "Set units to millimeters"
        "G21 - Set Units to Millimeters",
        parameters={}
    )

    G28 = Command(
        "G28",
        "Go to origin",
        "G28 - Go to origin X={X}, Y={Y}, Z={Z}, W={W}",
        parameters={
            "X": CommandParameter("X", CommandParameter.parse_float, 1),
            "Y": CommandParameter("Y", CommandParameter.parse_float, 2),
            "Z": CommandParameter("Z", CommandParameter.parse_float, 3),
            "W": CommandParameter("W", CommandParameter.parse_float, 4)
        }
    )

    G29 = Command(
        "G29",
        "Detailed Z-Prob",
        "G29 - Dtailed z-probe: S={S}",
        parameters={
            "S": CommandParameter("S", CommandParameter.parse_float, 1)
        }
    )

    G80 = Command(
        "G80",
        "Cancel canned cycle (firmware specific)"
        "G80 - Cancel canned cycle (firmware specific)",
        parameters={}
    )

    G90 = Command(
        "G90",
        "Set XYZ axes to absolute coordinates",
        "G90 - Set XYZ axes to absolute coordinates",
        parameters={}
    )
    G91 = Command(
        "G91",
        "Set XYZ axes to relative coordinates",
        "G91 - Set XYZ axes to relative coordinates",
        parameters={}
    )

    G92 = Command(
        "G92",
        "Set absolute position",
        "G02 - Set absolute position to X={X}, Y={Y}, Z={Z}, E={E}",
        parameters={
            "X": CommandParameter("X", CommandParameter.parse_float, 1),
            "Y": CommandParameter("Y", CommandParameter.parse_float, 2),
            "Z": CommandParameter("Z", CommandParameter.parse_float, 3),
            "E": CommandParameter("E", CommandParameter.parse_float, 4),
            "O": CommandParameter("O", CommandParameter.parse_float, 5)
        }
    )

    M82 = Command(
        "M82",
        "Set extruder relative mode",
        "M82 - Set extruder to relative mode",
        parameters={}
    )

    M83 = Command(
        "M83",
        "Set extruder absolute mode",
        "M83 - Set extruder to absolute mode",
        parameters={}
    )

    M104 = Command(
        "M104",
        "Set extruder temperature",
        "M104 - Set extruder temperature: S={S}",
        parameters={
            "S": CommandParameter("S", CommandParameter.parse_float, 1)
        }
    )

    M105 = Command(
        "M105",
        "Get temperature",
        "M105 - Get temperatures",
        parameters={}
    )

    M106 = Command(
        "M106",
        "Set part fan speed",
        "M106 - Set part fan speed: S={S}, P={P}, I={I}, F={F}, L={L}, B={B}, R={R}, T={T}",
        parameters={
            "S": CommandParameter("S", CommandParameter.parse_float, 1),
            "P": CommandParameter("P", CommandParameter.parse_float, 2),  # previously only supported ints
            "I": CommandParameter("I", CommandParameter.parse_float, 3),  # previously only supported booleans
            "F": CommandParameter("F", CommandParameter.parse_float, 4),  # previously only supported ints
            "L": CommandParameter("L", CommandParameter.parse_float, 5),
            "B": CommandParameter("B", CommandParameter.parse_float, 6),  # previously only supported ints
            "R": CommandParameter("R", CommandParameter.parse_float, 7),  # previously only supported ints
            "T": CommandParameter("T", CommandParameter.parse_float, 8),  # previously only supported ints
        }
    )

    M109 = Command(
        "M109",
        "Set extruder temperature and wait",
        display_template="M109 - Set extruder temperature and wait: S={S}, R={R}",
        parameters={
            "S": CommandParameter("S", CommandParameter.parse_float, 1),
            "R": CommandParameter("R", CommandParameter.parse_float, 2)
        }
    )

    M114 = Command(
        "M114",
        "Get position"
        "M114 - Get current position",
        parameters={}
    )

    M116 = Command(
        "M116",
        "Wait for temperature",
        display_template="M116 - Wait for temperature: P={P}, H={H}, C={C}",
        parameters={
            "P": CommandParameter("P", CommandParameter.parse_float, 1),
            "H": CommandParameter("H", CommandParameter.parse_float, 2),
            "C": CommandParameter("C", CommandParameter.parse_float, 3)
        }
    )

    M140 = Command(
        "M140",
        "Set bed temperature",
        "M140 - Set bed temperature: S={S}, H={H}",
        parameters={
            "S": CommandParameter("S", CommandParameter.parse_float, 1),
            "H": CommandParameter("H", CommandParameter.parse_float, 2)
        }
    )

    M141 = Command(
        "M141",
        "Set chamber temperature",
        "M141 - Set chamber temperature: S={S}, H={H}",
        parameters={
            "S": CommandParameter("S", CommandParameter.parse_float, 1),
            "H": CommandParameter("H", CommandParameter.parse_float, 2)
        }
    )

    M190 = Command(
        "M190",
        "Set bed temperature and wait",
        "M190 - Set bed temperature and wait: S={S}, R={R}",
        parameters={
            "S": CommandParameter("S", CommandParameter.parse_float, 1),
            "R": CommandParameter("R", CommandParameter.parse_float, 2)
        }
    )

    M191 = Command(
        "M191",
        "Set chamber temperature and wait",
        "M191 - Set chamber temperature and wait: S={S}, R={R}",
        parameters={
            "S": CommandParameter("S", CommandParameter.parse_float, 1),
            "R": CommandParameter("R", CommandParameter.parse_float, 2)
        }
    )

    M207 = Command(
        "M207",
        "Set retract length"
        "M207 - Set retract length",
        parameters={
            "S": CommandParameter("S", CommandParameter.parse_float, 1),
            "R": CommandParameter("R", CommandParameter.parse_float, 2),
            "F": CommandParameter("F", CommandParameter.parse_float, 3),
            "T": CommandParameter("T", CommandParameter.parse_float, 4),
            "Z": CommandParameter("Z", CommandParameter.parse_float, 5)
        }
    )

    M208 = Command(
        "M208",
        "Set detract length"
        "M208 - Set detract length",
        parameters={
            "S": CommandParameter("S", CommandParameter.parse_float, 1),
            "F": CommandParameter("F", CommandParameter.parse_float, 2),

        }
    )

    M400 = Command(
        "M400",
        "Wait for moves to finish",
        "M400 - Wait for moves to finish",
        parameters={}
    )

    CommandsDictionary = {
            G0.Command: G0,
            G1.Command: G1,
            G2.Command: G2,
            G3.Command: G3,
            G10.Command: G10,
            G11.Command: G11,
            G20.Command: G20,
            G21.Command: G21,
            G28.Command: G28,
            G29.Command: G29,
            G80.Command: G80,
            G90.Command: G90,
            G91.Command: G91,
            G92.Command: G92,
            M82.Command: M82,
            M83.Command: M83,
            M104.Command: M104,
            M105.Command: M105,
            M106.Command: M106,
            M109.Command: M109,
            M114.Command: M114,
            M116.Command: M116,
            M140.Command: M140,
            M141.Command: M141,
            M190.Command: M190,
            M191.Command: M191,
            M207.Command: M207,
            M208.Command: M208,
            M400.Command: M400
        }

    GcodeWords = {"G", "M"}
    SuppressedSavedCommands = [M105.Command, M400.Command]
    SuppressedSnapshotGcodeCommands = [M105.Command]
    CommandsRequireMetric = [G0.Command, G1.Command, G2.Command, G3.Command, G28.Command, G92.Command]
    TestModeSuppressExtrusionCommands = [G0.Command, G1.Command, G2.Command, G3.Command]
    TestModeSuppressCommands = [
        G10.Command, G11.Command,
        M104.Command, M140.Command, M141.Command,
        M109.Command, M190.Command, M191.Command,
        M116.Command, M106.Command
    ]

    @staticmethod
    def parse(gcode):
        # strip off any trailing comments
        ix = gcode.find(";")
        if ix > -1:
            if ix <= len(gcode) - 1:
                gcode = gcode[0:ix]
            else:
                return None, None

        # remove any comments from ('s
        start_comment_index = None
        end_comment_index = None

        index = 0
        while index < len(gcode):
            if end_comment_index is not None:
                # we have a comment to remove.
                if start_comment_index == 0:
                    if len(gcode) == end_comment_index + 1:
                        gcode = ""
                        index = 0
                    else:
                        gcode = gcode[end_comment_index + 1:]
                        index = 0

                elif end_comment_index + 1 == len(gcode):
                    gcode = gcode[0:start_comment_index]
                    index = start_comment_index + 1
                else:
                    gcode = gcode[0:start_comment_index] + gcode[end_comment_index + 1:]
                    index = start_comment_index

                start_comment_index = None
                end_comment_index = None

            for index in range(index, len(gcode)):
                c = gcode[index]
                if start_comment_index is None and c == "(":
                    start_comment_index = index
                elif start_comment_index is not None and c == ")":
                    end_comment_index = index
                    break

            if start_comment_index is None or end_comment_index is None:
                break

        # strip whitespace
        gcode = gcode.strip()

        # ignore blank lines
        if len(gcode) < 1:
            return None, None

        # ignore any lines that start with a %
        if gcode[0] == "%":
            return None, None

        # make sure our string is greater than 2 characters
        if len(gcode) < 2:
            return None, None

        # extract any line numbers
        if gcode[0] == "N":
            _n_temp = ""
            # extract any integers and ignore whitespace
            for index in range(0, len(gcode) - 1):
                _c = gcode[index].upper()

                if _c.isspace():
                    continue
                if "0" <= _c <= "9":
                    _n_temp += _c
                else:
                    break

            # remove the line number from the command string and strip off whitespace from the front
            gcode = gcode[index:].lstrip()

        # Now we should be left with the command and any parameters
        # Make sure our command is a valid one
        if len(gcode) < 2:
            return None, None

        # get the command letter
        command_letter = gcode[0].upper()
        if command_letter not in Commands.GcodeWords:
            return None, None

        # search for decimals or periods to build the command address
        command_address = ""
        has_seen_period = False
        for index in range(1, len(gcode)):
            c = gcode[index]
            if c.isspace():
                continue
            elif "0" <= c <= "9":
                command_address += c
            elif c == ".":
                if not has_seen_period:
                    # if the command add
                    command_address = str(int(command_address))
                    command_address += c
                    has_seen_period = True
                else:
                    raise ValueError("Cannot parse the gcode address, multiple periods seen.")
            else:
                break
        # If we've not seen any periods, strip any leading 0s from the gcode
        if not has_seen_period:
            command_address = str(int(command_address))

        # make sure the command is in the dictionary
        command_to_search = command_letter + command_address
        if command_to_search not in Commands.CommandsDictionary.keys():
            return command_to_search, None

        cmd = Commands.CommandsDictionary[command_to_search]

        # get the parameter string
        if len(gcode) > index:
            parameters = gcode[index:]
        else:
            parameters = ""

        if not cmd.TextOnlyParameter:
            parameters = cmd.parse_parameters(parameters)

        return command_to_search, parameters

    @staticmethod
    def to_string(cmd, parameters):
        if cmd is None:
            return ""
        gcode = cmd

        if parameters is not None:
            for key, value in parameters.items():
                gcode += " " + key + str(value)
        return gcode

    @staticmethod
    def alter_for_test_mode(command_string, cmd, parameters, return_string=False):
        if cmd is None:
            if return_string:
                return command_string
            return None

        if cmd in Commands.TestModeSuppressExtrusionCommands and "E" in parameters:
            parameters.pop("E")
            # reform the gcode
            gcode = Commands.to_string(cmd, parameters)
            if return_string:
                return gcode
            return gcode,
        elif cmd in Commands.TestModeSuppressCommands:
            if return_string:
                return ""
            return None,
        else:
            if return_string:
                # reform the gcode
                return command_string
            return None
