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


import collections
import operator
import re


class GcodeParts(object):
    """Contains the Gcode Command, an array of parameters, and a comment"""

    def __init__(self, gcode):
        # Member variables
        self.Gcode = gcode  # The original gcoce
        self.Command = None  # The trimmed command in the original case
        self.Parameters = []  # an array of trimmed parameters in the original case
        self.Comment = None  # Any text after the first semicolon, untrimmed and unaltered

        # if there is no gcode there is nothing to do.
        if gcode is None:
            return

        # create a temp variable to hold the command without the comment or semicolon
        command_and_parameters = None

        # find the first semicolon.  If it exists, split the string into two
        comment_index = gcode.find(";")

        # handle splitting comment from command and parameters
        if comment_index > -1:
            # if we've found a semicolon
            if comment_index > 0:
                command_and_parameters = gcode[0:comment_index].strip()
            if len(gcode) >= comment_index + 1:
                # If there is anything after the semicolon
                self.Comment = gcode[comment_index + 1:]
            else:
                # If there is nothing after the semicolon
                self.Comment = ""
        else:
            command_and_parameters = gcode.strip()
        # now we should have a stripped commandAndParameters string and either a stripped comment, or no comment

        # If there are no commands or parameters, there is nothing more to do.
        # We have extracted any comment that might exist on the line
        if command_and_parameters is None or len(command_and_parameters) == 0:
            return

        # split the commandAndParameters array, stripping any redundant whitespace
        # This split command rocks!  How fun that the defaults work for my case!
        command_array = command_and_parameters.split()
        # We will need to know how many elements are in this array later
        num_parts = len(command_array)

        if num_parts == 0:
            return  # Our string contained only whitespace, time to go, leaving the Command = None and Parameters = []

        # we for sure have a command at this point, so set it now!
        self.Command = command_array[0]

        # If we have anything extra in our commandArray, it must contain parameters.
        if num_parts > 1:
            # everything but the first element
            self.Parameters = command_array[1:]


def get_gcode_from_string(command_string):
    command = command_string.strip().split(' ', 1)[0].upper()
    ix = command.find(";")
    if ix > -1:
        command = command[0:ix]
    return command


class CommandParameter(object):
    def __init__(self, name, regex=None, value=None, order=None):
        self.Name = name
        if regex is not None:
            self.__compiled = re.compile(regex, re.IGNORECASE)
        else:
            self.__complied = None
        self.Value = value
        self.Order = order

    def parse(self, parameter_text):
        """parse the parameter text and store it in the Value member.  Return true if a match is found, false if not."""

        self.Value = None  # We haven't found a value yet.

        # if we have no compiled regex, we can't parse anything.
        if self.__compiled is None:
            return False

        # get any matches
        matches = self.__compiled.match(parameter_text)
        if matches is None:
            # No matches, time to go
            return False

        # How many capture groups did we find?
        num_groups = len(matches.groups())
        if num_groups > 0:
            self.Value = matches.group(1)
            if num_groups > 1:
                # if there were any extra matches, return false
                return False

        # if we're here, things went well.  Return True!
        return True


class CommandParameters(collections.MutableMapping):
    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs))  # use the free update to set keys

    def __getitem__(self, key):
        if self.__keytransform__(key) in self.store.keys():
            return self.store[self.__keytransform__(key)]
        return None

    def __setitem__(self, key, value):
        order = len(self.store) + 1
        if value.Order is None:
            value.Order = order
        self.store[self.__keytransform__(key)] = value

    def __delitem__(self, key):
        del self.store[self.__keytransform__(key)]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __keytransform__(self, key):
        return key

    def clear_values(self):
        for key, item in self.store.items():
            item.Value = None


class Command(object):
    CommentTemplate = "{comment}"
    CommentTextTemplate = "{commenttext}"
    CommentSeparator = ";"

    def __init__(self, name=None, command=None, display_template=None, parameters=None, gcode=None):
        if type(command) is Command:
            self.Name = command.Name
            self.Command = command.Command
            self.DisplayTemplate = command.DisplayTemplate
            self.Parameters = command.Parameters
            self.CommandParts = command.CommandParts
        else:
            self.Name = name
            self.Command = command
            self.DisplayTemplate = display_template
            self.Parameters = CommandParameters()
            self.CommandParts = GcodeParts(gcode)
            if parameters is not None:
                if type(parameters) is CommandParameter:
                    self.Parameters[parameters.Name] = parameters
                elif isinstance(parameters, list):
                    order = 1
                    for parameter in parameters:
                        if parameter.Order is None:
                            parameter.Order = order
                            order += 1
                        self.Parameters[parameter.Name] = parameter
                else:
                    self.Parameters = parameters

    def to_string(self, reform=False):
        # if we have gcode, just return it (duh...)
        if not reform and self.CommandParts.Gcode is not None:
            return self.CommandParts.Gcode

        # if we do not have gcode, construct from the command and parameters
        command_string = self.Command

        # loop through each parameter and add the parameter name and value to the command string
        for parameter in (sorted(self.Parameters.values(), key=operator.attrgetter('Order'))):
            if parameter.Value is not None:
                command_string += " " + parameter.Name + str(parameter.Value)
        # since there is no gcode, we can't have a comment.  Time to return the command string
        return command_string

    def parse(self):

        # Clear any parameter values
        self.Parameters.clear_values()

        # Validate the gcode command
        if self.CommandParts.Command.upper() != self.Command.upper():
            return False  # we're parsing the wrong command, fail

        # create a flag to hold any match errors
        errors = False  # initially false since there have been no errors thus far
        # Loop through any parameters in the command parts and try to parse them
        for paramText in self.CommandParts.Parameters:
            matched = False
            # Loop through the parameters
            for key, parameter in self.Parameters.items():
                # if this parameter already has a value, skip it
                if parameter.Value is not None:
                    continue
                # test for regex match
                if parameter.parse(paramText):
                    # it worked, break to the next parameter
                    matched = True
                    break
            if not matched:
                errors = True
        # if there were no errors, there was success!
        return not errors


class Commands(object):
    SuppressedSavedCommands = ["M105", "M400"]
    SuppressedSnapshotGcodeCommands = ["M105"]
    G0 = Command(
        name="Rapid Linear Move", command="G0",
        display_template="Position: X={X}, Y={Y}, Z={Z}, E={E}, F={F}, Comment={CommentText}",
        parameters=[
            CommandParameter("X", "(?i)^x(?P<x>[+-]?[0-9]{0,15}.?[0-9]{1,15})$", order=1),
            CommandParameter("Y", "(?i)^y(?P<y>[+-]?[0-9]{0,15}.?[0-9]{1,15})$", order=2),
            CommandParameter("Z", "(?i)^z(?P<z>[+-]?[0-9]{0,15}.?[0-9]{1,15})$", order=3),
            CommandParameter("E", "(?i)^e(?P<e>[+-]?[0-9]{0,15}.?[0-9]{1,15})$", order=4),
            CommandParameter("F", "(?i)^f(?P<f>[+-]?[0-9]{0,15}.?[0-9]{1,15})$", order=5)
        ]
    )
    G1 = Command(
        name="Linear Move", command="G1",
        display_template="Position: X={X}, Y={Y}, Z={Z}, E={E}, F={F}{Comment}",
        parameters=[
            CommandParameter("X", "(?i)^x(?P<x>[+-]?[0-9]{0,15}.?[0-9]{1,15})$", order=1),
            CommandParameter("Y", "(?i)^y(?P<y>[+-]?[0-9]{0,15}.?[0-9]{1,15})$", order=2),
            CommandParameter("Z", "(?i)^z(?P<z>[+-]?[0-9]{0,15}.?[0-9]{1,15})$", order=3),
            CommandParameter("E", "(?i)^e(?P<e>[+-]?[0-9]{0,15}.?[0-9]{1,15})$", order=4),
            CommandParameter("F", "(?i)^f(?P<f>[+-]?[0-9]{0,15}.?[0-9]{1,15})$", order=5)
        ]
    )
    G29 = Command(
        name="Detailed Z-Probe", command="G29",
        display_template="G29 - Detailed Z-Probe{Comment}",
        parameters=[
            CommandParameter("S", "(?i)^s(?P<s>-?[0-9]{0,15}.?[0-9]{1,15})$", order=1)
        ]
    )
    G92 = Command(
        name="Set Absolute Position", command="G92",
        display_template="New Absolute Position: X={X}, Y={Y}, Z={Z}, E={E}{Comment}",
        parameters=[
            CommandParameter("X", "(?i)^x(?P<x>[+-]?[0-9]{0,15}.?[0-9]{1,15})$", order=1),
            CommandParameter("Y", "(?i)^y(?P<y>[+-]?[0-9]{0,15}.?[0-9]{1,15})$", order=2),
            CommandParameter("Z", "(?i)^z(?P<z>[+-]?[0-9]{0,15}.?[0-9]{1,15})$", order=3),
            CommandParameter("E", "(?i)^e(?P<e>[+-]?[0-9]{0,15}.?[0-9]{1,15})$", order=4)
        ]
    )
    M82 = Command(
        name="Set Extruder Relative Mode", command="M82",
        display_template="M82 - Set Extruder Relative Mode{Comment}",
        parameters=[]
    )
    M83 = Command(
        name="Set Extruder Absolute Mode", command="M83",
        display_template="M83 - Set Extruder Absolute Mode{Comment}",
        parameters=[]
    )
    G20 = Command(
        name="Set Units to Inches", command="G20",
        display_template="G20 - Set Units to Inches{Comment}",
        parameters=[]
    )
    G21 = Command(
        name="Set Units to Millimeters", command="G21",
        display_template="G21 - Set Units to Millimeters{Comment}",
        parameters=[]
    )
    G28 = Command(
        name="Go To Origin", command="G28",
        display_template="G28 - Go to Origin{Comment}",
        parameters=[
            CommandParameter("X", "(?i)^(x)(?:[+-]?[0-9]{1,15}(?:.[0-9]{1,15})?)?$", order=1),
            CommandParameter("Y", "(?i)^(y)(?:[+-]?[0-9]{1,15}(?:.[0-9]{1,15})?)?$", order=2),
            CommandParameter("Z", "(?i)^(z)(?:[+-]?[0-9]{1,15}(?:.[0-9]{1,15})?)?$", order=3),
            CommandParameter("W", "(?i)^(w)(?:[+-]?[0-9]{1,15}(?:.[0-9]{1,15})?)?$", order=4)
        ]
    )
    G80 = Command(
        name="Cancel Canned Cycle (firmware specific)", command="G80",
        display_template="G80 - Cancel Canned Cycle (firmware specific){Comment}",
        parameters=[]
    )
    G90 = Command(
        name="Absolute Coordinates", command="G90",
        display_template="G90 - Absolute Coordinates{Comment}",
        parameters=[]
    )
    G91 = Command(
        name="Relative Coordinates", command="G91",
        display_template="G91 - Relative Coordinates{Comment}",
        parameters=[]
    )
    M114 = Command(
        name="Get Position", command="M114",
        display_template="M114 - Get Current Position{Comment}",
        parameters=[]
    )
    M104 = Command(
        name="Set Extruder Temperature", command="M104",
        display_template="M104 - Set Extruder Temperature{Comment}",
        parameters=[
            CommandParameter("S", "(?i)^s(?P<s>-?[0-9]{0,15}.?[0-9]{1,15})$", order=1)
        ]
    )
    M140 = Command(
        name="Set Bed Temperature", command="M140",
        display_template="M140 - Set Bed Temperature{Comment}",
        parameters=[
            CommandParameter("S", "(?i)^s(?P<s>-?[0-9]{0,15}.?[0-9]{1,15})$", order=1),
            CommandParameter("H", "(?i)^h(?P<h>-?[0-9]{0,15})$", order=2)
        ]
    )
    M141 = Command(
        name="Set Chamber Temperature", command="M141",
        display_template="M141 - Set Chamber Temperature{Comment}",
        parameters=[
            CommandParameter("S", "(?i)^s(?P<s>-?[0-9]{0,15}.?[0-9]{1,15})$", order=1),
            CommandParameter("H", "(?i)^h(?P<h>-?[0-9]{0,15})$", order=2)
        ]
    )
    M109 = Command(
        name="Set Extruder Temperature and Wait", command="M109",
        display_template="M109 - Extruder Bed Temperature and Wait{Comment}",
        parameters=[
            CommandParameter("S", "(?i)^s(?P<s>-?[0-9]{0,15}.?[0-9]{1,15})$", order=1),
            CommandParameter("R", "(?i)^r(?P<r>-?[0-9]{0,15}.?[0-9]{1,15})$", order=2)
        ]
    )
    M190 = Command(
        name="Set Bed Temperature and Wait", command="M190",
        display_template="M190 - Set Bed Temperature and Wait{Comment}",
        parameters=[
            CommandParameter("S", "(?i)^s(?P<s>-?[0-9]{0,15}.?[0-9]{1,15})$", order=1),
            CommandParameter("R", "(?i)^r(?P<r>-?[0-9]{0,15}.?[0-9]{1,15})$", order=2)
        ]
    )
    M191 = Command(
        name="Set Chamber Temperature and Wait", command="M191",
        display_template="M191 - Set Bed Temperature and Wait{Comment}",
        parameters=[
            CommandParameter("S", "(?i)^s(?P<s>-?[0-9]{0,15}.?[0-9]{1,15})$", order=1),
            CommandParameter("R", "(?i)^r(?P<r>-?[0-9]{0,15}.?[0-9]{1,15})$", order=2)
        ]
    )
    M116 = Command(
        name="Wait for Temperature", command="M116",
        display_template="M116 - Wait for Temperature{Comment}",
        parameters=[
            CommandParameter("P", "(?i)^p(?P<p>-?[0-9]{0,15})$", order=1),
            CommandParameter("H", "(?i)^h(?P<h>-?[0-9]{0,15})$", order=2),
            CommandParameter("C", "(?i)^c(?P<c>-?[0-9]{0,15})$", order=3)
        ]
    )
    M106 = Command(
        name="Set Part Fan Speed", command="M106",
        display_template="M106 - Set Part Fan Speed{Comment}",
        parameters=[
            CommandParameter("S", "(?i)^s(?P<s>-?[0-9]{0,15}.?[0-9]{1,15})$", order=1),
            CommandParameter("P", "(?i)^p(?P<p>-?[0-9]{0,15})$", order=2),
            CommandParameter("I", "(?i)^(i)$", order=3),
            CommandParameter("F", "(?i)^p(?P<f>-?[0-9]{0,15})$", order=4),
            CommandParameter("L", "(?i)^s(?P<l>-?[0-9]{0,15}.?[0-9]{1,15})$", order=5),
            CommandParameter("B", "(?i)^p(?P<b>-?[0-9]{0,15})$", order=6),
            CommandParameter("R", "(?i)^p(?P<r>-?[0-9]{0,15})$", order=7),
            CommandParameter("T", "(?i)^p(?P<t>-?[0-9]{0,15})$", order=8),
        ]
    )

    CommandsRequireMetric = ['G0', 'G1', 'G28', 'G92']
    CommandsDictionary = {
        G0.Command: G0,
        G1.Command: G1,
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
        M106.Command: M106,
        M109.Command: M109,
        M114.Command: M114,
        M116.Command: M116,
        M140.Command: M140,
        M141.Command: M141,
        M190.Command: M190,
        M191.Command: M191
    }

    def alter_for_test_mode(self, cmd):
        if cmd is None:
            return None
        gcode_command = self.get_command(cmd)
        if gcode_command is None:
            return None
        elif gcode_command.Command in [self.G0.Command, self.G1.Command]:
            gcode_command.Parameters["E"].Value = None
            return gcode_command.to_string(reform=True),
        elif gcode_command.Command in [
                self.M104.Command, self.M140.Command, self.M141.Command,
                self.M109.Command, self.M190.Command, self.M191.Command,
                self.M116.Command, self.M106.Command]:
            return None,
        else:
            return None

    def get_test_mode_command_string(self, cmd):
        gcode_command = self.get_command(cmd)
        if gcode_command is None:
            return cmd
        elif gcode_command.Command in [self.G0.Command, self.G1.Command]:
            gcode_command.Parameters["E"].Value = None
            return gcode_command.to_string(reform=True)
        elif gcode_command.Command in [
                self.M104.Command, self.M140.Command, self.M141.Command,
                self.M109.Command, self.M190.Command, self.M191.Command,
                self.M116.Command, self.M106.Command]:
            return ""
        else:
            return cmd

    def get_command(self, code):
        gcode_command = get_gcode_from_string(code)
        if gcode_command in self.CommandsDictionary.keys():
            # get the gcodeCommand from our dictionary
            cmd = self.CommandsDictionary[gcode_command]
            # set the gcode parts
            cmd.CommandParts = GcodeParts(code)
            # parse the gcodeCommand
            cmd.parse()
            return cmd
        return None


class Responses(object):
    def __init__(self):
        self.M114 = Command(
            name="Get Position", command="M114",
            display_template="Position: X={0}, Y={1}, Z={2}, E={3}",
            parameters=[
                CommandParameter("X", "(?i)^x:(?P<x>-?[0-9]{0,15}.?[0-9]{1,15})$", order=1),
                CommandParameter("Y", "(?i)^y:(?P<y>-?[0-9]{0,15}.?[0-9]{1,15})$", order=2),
                CommandParameter("Z", "(?i)^z:(?P<z>-?[0-9]{0,15}.?[0-9]{1,15})$", order=3),
                CommandParameter("E", "(?i)^e:(?P<e>-?[0-9]{0,15}.?[0-9]{1,15})$", order=4)
            ]
        )
