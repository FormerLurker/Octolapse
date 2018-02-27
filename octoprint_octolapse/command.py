# coding=utf-8

# This file is subject to the terms and conditions defined in
# file called 'LICENSE', which is part of this source code package.


import re
import collections
import string
import operator
import sys
import octoprint_octolapse.utility as utility


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
        commandAndParameters = None

        # find the first semicolon.  If it exists, split the string into two
        commentIndex = gcode.find(";")

        # handle splitting comment from command and parameters
        if commentIndex > -1:
            # if we've found a semicolon
            if commentIndex > 0:
                commandAndParameters = gcode[0:commentIndex].strip()
            if len(gcode) >= commentIndex+1:
                # If there is anything after the semicolon
                self.Comment = gcode[commentIndex+1:]
            else:
                # If there is nothing after the semicolon
                self.Comment = ""
        else:
            commandAndParameters = gcode.strip()
        # now we should have a stripped commandAndParameters string and either a stripped comment, or no comment

        # If there are no commands or parameters, there is nothing more to do.
        # We have extracted any comment that might exist on the line
        if commandAndParameters is None or len(commandAndParameters) == 0:
            return

        # split the commandAndParameters array, stripping any redundant whitespace
        # This split command rocks!  How fun that the defaults work for my case!
        commandArray = commandAndParameters.split()
        # We will need to know how many elements are in this array later
        numParts = len(commandArray)

        if numParts == 0:
            return  # Our string contained only whitespace, time to go, leaving the Command = None and Parameters = []

        # we for sure have a command at this point, so set it now!
        self.Command = commandArray[0]

        # If we have anything extra in our commandArray, it must contain parameters.
        if numParts > 1:
            # everything but the first element
            self.Parameters = commandArray[1:]


def GetGcodeFromString(commandString):
    command = commandString.strip().split(' ', 1)[0].upper()
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

    def Parse(self, paramText):
        """parse the parameter text and store it in the Value member.  Return true if a match is found, false if not."""

        self.Value = None  # We haven't found a value yet.

        # if we have no compiled regex, we can't parse anything.
        if self.__compiled is None:
            return False

        # get any matches
        matches = self.__compiled.match(paramText)
        if matches is None:
            # No matches, time to go
            return False

        # How many capture groups did we find?
        numGroups = len(matches.groups())
        if numGroups > 0:
            self.Value = matches.group(1)
            if numGroups > 1:
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

    def ClearValues(self):
        for key, item in self.store.items():
            item.Value = None


class Command(object):
    CommentTemplate = "{comment}"
    CommentTextTemplate = "{commenttext}"
    CommentSeparator = ";"

    def __init__(self, name=None, command=None, regex=None, displayTemplate=None,  parameters=None, gcode=None):
        if type(command) is Command:
            self.Name = command.Name
            self.Command = command.Command
            self.DisplayTemplate = command.DisplayTemplate
            self.Parameters = command.Parameters
            self.CommandParts = command.CommandParts
        else:
            self.Name = name
            self.Command = command
            self.DisplayTemplate = displayTemplate
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

    def DisplayString(self):
        if self.DisplayTemplate is None:
            return self.Gcode()
        output = self.DisplayTemplate
        safeDict = utility.SafeDict()
        for key in self.Parameters:
            value = self.Parameters[key].Value
            safeDict.clear()
            if value is None:
                value = "None"

            safeDict[key] = value
            output = string.Formatter().vformat(output, (), safeDict)

        if self.CommandParts.Comment is not None:
            safeDict.clear()
            safeDict["Comment"] = self.CommentSeparator + \
                self.CommandParts.Comment
            safeDict["CommentText"] = self.CommandParts.Comment
            output = string.Formatter().vformat(output, (), safeDict)
        else:
            safeDict["Comment"] = ""
            safeDict["CommentText"] = ""
            output = string.Formatter().vformat(output, (), safeDict)

        return output

    def ToString(self, reform=False):
        # if we have gcode, just return it (duh...)
        if not reform and self.CommandParts.Gcode is not None:
            return self.CommandParts.Gcode

        # if we do not have gcode, construct from the command and parameters
        commandString = self.Command

        # loop through each parameter and add the parameter name and value to the command string
        for parameter in (sorted(self.Parameters.values(), key=operator.attrgetter('Order'))):
            if parameter.Value is not None:
                commandString += " " + parameter.Name + str(parameter.Value)
        # since there is no gcode, we can't have a comment.  Time to return the command string
        return commandString

    def Parse(self):

        # Clear any parameter values
        self.Parameters.ClearValues()

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
                if parameter.Parse(paramText):
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
        displayTemplate="Position: X={X}, Y={Y}, Z={Z}, E={E}, F={F}, Comment={CommentText}",
        parameters=[
            CommandParameter("X", "(?i)^x(?P<x>-?[0-9]{0,15}.?[0-9]{1,15})$", order=1),
            CommandParameter("Y", "(?i)^y(?P<y>-?[0-9]{0,15}.?[0-9]{1,15})$", order=2),
            CommandParameter("Z", "(?i)^z(?P<z>-?[0-9]{0,15}.?[0-9]{1,15})$", order=3),
            CommandParameter("E", "(?i)^e(?P<e>-?[0-9]{0,15}.?[0-9]{1,15})$", order=4),
            CommandParameter("F", "(?i)^f(?P<f>-?[0-9]{0,15}.?[0-9]{1,15})$", order=5)
        ]
    )
    G1 = Command(
        name="Linear Move", command="G1",
        displayTemplate="Position: X={X}, Y={Y}, Z={Z}, E={E}, F={F}{Comment}",
        parameters=[
            CommandParameter("X", "(?i)^x(?P<x>-?[0-9]{0,15}.?[0-9]{1,15})$", order=1),
            CommandParameter("Y", "(?i)^y(?P<y>-?[0-9]{0,15}.?[0-9]{1,15})$", order=2),
            CommandParameter("Z", "(?i)^z(?P<z>-?[0-9]{0,15}.?[0-9]{1,15})$", order=3),
            CommandParameter("E", "(?i)^e(?P<e>-?[0-9]{0,15}.?[0-9]{1,15})$", order=4),
            CommandParameter("F", "(?i)^f(?P<f>-?[0-9]{0,15}.?[0-9]{1,15})$", order=5)
        ]
    )
    G28 = Command(
        name="Go To Origin", command="G28",
        displayTemplate="G28 - Go to Origin{Comment}",
        parameters=[
            CommandParameter("X", "(?i)^(x)$", order=1),
            CommandParameter("Y", "(?i)^(y)$", order=2),
            CommandParameter("Z", "(?i)^(z)$", order=3),
            CommandParameter("W", "(?i)^(w)$", order=4)
        ]
    )
    G29 = Command(
        name="Detailed Z-Probe", command="G29",
        displayTemplate="G29 - Detailed Z-Probe{Comment}",
        parameters=[
            CommandParameter("S", "(?i)^s(?P<s>-?[0-9]{0,15}.?[0-9]{1,15})$", order=1)
        ]
    )
    G92 = Command(
        name="Set Absolute Position", command="G92",
        displayTemplate="New Absolute Position: X={X}, Y={Y}, Z={Z}, E={E}{Comment}",
        parameters=[
            CommandParameter("X", "(?i)^x(?P<x>-?[0-9]{0,15}.?[0-9]{1,15})$", order=1),
            CommandParameter("Y", "(?i)^y(?P<y>-?[0-9]{0,15}.?[0-9]{1,15})$", order=2),
            CommandParameter("Z", "(?i)^z(?P<z>-?[0-9]{0,15}.?[0-9]{1,15})$", order=3),
            CommandParameter("E", "(?i)^e(?P<e>-?[0-9]{0,15}.?[0-9]{1,15})$", order=4)
        ]
    )
    M82 = Command(
        name="Set Extruder Relative Mode", command="M82",
        displayTemplate="M82 - Set Extruder Relative Mode{Comment}",
        parameters=[]
    )
    M83 = Command(
        name="Set Extruder Absolute Mode", command="M83",
        displayTemplate="M83 - Set Extruder Absolute Mode{Comment}",
        parameters=[]
    )
    G28 = Command(
        name="Go To Origin", command="G28",
        displayTemplate="G28 - Go to Origin{Comment}",
        parameters=[
            CommandParameter("X", "(?i)^(x)(?:-?[0-9]{1,15}(?:.[0-9]{1,15})?)?$", order=1),
            CommandParameter("Y", "(?i)^(y)(?:-?[0-9]{1,15}(?:.[0-9]{1,15})?)?$", order=2),
            CommandParameter("Z", "(?i)^(z)(?:-?[0-9]{1,15}(?:.[0-9]{1,15})?)?$", order=3),
            CommandParameter("W", "(?i)^(w)(?:-?[0-9]{1,15}(?:.[0-9]{1,15})?)?$", order=4)
        ]
    )
    G80 = Command(
        name="Cancel Canned Cycle (firmware specific)", command="G80",
        displayTemplate="G80 - Cancel Canned Cycle (firmware specific){Comment}",
        parameters=[]
    )
    G90 = Command(
        name="Absolute Coordinates", command="G90",
        displayTemplate="G90 - Absolute Coordinates{Comment}",
        parameters=[]
    )
    G91 = Command(
        name="Relative Coordinates", command="G91",
        displayTemplate="G91 - Relative Coordinates{Comment}",
        parameters=[]
    )
    M114 = Command(
        name="Get Position", command="M114",
        displayTemplate="M114 - Get Current Position{Comment}",
        parameters=[]
    )
    M104 = Command(
        name="Set Extruder Temperature", command="M104",
        displayTemplate="M104 - Set Extruder Temperature{Comment}",
        parameters=[
            CommandParameter("S", "(?i)^s(?P<s>-?[0-9]{0,15}.?[0-9]{1,15})$", order=1)
        ]
    )
    M140 = Command(
        name="Set Bed Temperature", command="M140",
        displayTemplate="M140 - Set Bed Temperature{Comment}",
        parameters=[
            CommandParameter("S", "(?i)^s(?P<s>-?[0-9]{0,15}.?[0-9]{1,15})$", order=1),
            CommandParameter("H", "(?i)^h(?P<h>-?[0-9]{0,15})$", order=2)
        ]
    )
    M141 = Command(
        name="Set Chamber Temperature", command="M141",
        displayTemplate="M141 - Set Chamber Temperature{Comment}",
        parameters=[
            CommandParameter("S", "(?i)^s(?P<s>-?[0-9]{0,15}.?[0-9]{1,15})$", order=1),
            CommandParameter("H", "(?i)^h(?P<h>-?[0-9]{0,15})$", order=2)
        ]
    )
    M109 = Command(
        name="Set Extruder Temperature and Wait", command="M109",
        displayTemplate="M109 - Extruder Bed Temperature and Wait{Comment}",
        parameters=[
            CommandParameter("S", "(?i)^s(?P<s>-?[0-9]{0,15}.?[0-9]{1,15})$", order=1),
            CommandParameter("R", "(?i)^r(?P<r>-?[0-9]{0,15}.?[0-9]{1,15})$", order=2)
        ]
    )
    M190 = Command(
        name="Set Bed Temperature and Wait", command="M190",
        displayTemplate="M190 - Set Bed Temperature and Wait{Comment}",
        parameters=[
            CommandParameter("S", "(?i)^s(?P<s>-?[0-9]{0,15}.?[0-9]{1,15})$", order=1),
            CommandParameter("R", "(?i)^r(?P<r>-?[0-9]{0,15}.?[0-9]{1,15})$", order=2)
        ]
    )
    M191 = Command(
        name="Set Chamber Temperature and Wait", command="M191",
        displayTemplate="M191 - Set Bed Temperature and Wait{Comment}",
        parameters=[
            CommandParameter("S", "(?i)^s(?P<s>-?[0-9]{0,15}.?[0-9]{1,15})$", order=1),
            CommandParameter("R", "(?i)^r(?P<r>-?[0-9]{0,15}.?[0-9]{1,15})$", order=2)
        ]
    )
    M116 = Command(
        name="Wait for Temperature", command="M116",
        displayTemplate="M116 - Wait for Temperature{Comment}",
        parameters=[
            CommandParameter("P", "(?i)^p(?P<p>-?[0-9]{0,15})$", order=1),
            CommandParameter("H", "(?i)^h(?P<h>-?[0-9]{0,15})$", order=2),
            CommandParameter("C", "(?i)^c(?P<c>-?[0-9]{0,15})$", order=3)
        ]
    )
    M106 = Command(
        name="Set Part Fan Speed", command="M106",
        displayTemplate="M106 - Set Part Fan Speed{Comment}",
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

    CommandsDictionary = {
        G0.Command: G0,
        G1.Command: G1,
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

    def AlterCommandForTestMode(self, cmd):
        if cmd is None:
            return None
        gcodeCommand = self.GetCommand(cmd)
        if gcodeCommand is None:
            return None
        elif gcodeCommand.Command in [self.G0.Command, self.G1.Command]:
            gcodeCommand.Parameters["E"].Value = None
            return gcodeCommand.ToString(reform=True),
        elif gcodeCommand.Command in [
            self.M104.Command, self.M140.Command, self.M141.Command,
            self.M109.Command, self.M190.Command, self.M191.Command,
            self.M116.Command, self.M106.Command]:
            return (None,)
        else:
            return None

    def GetTestModeCommandString(self, cmd):
        gcodeCommand = self.GetCommand(cmd)
        if gcodeCommand is None:
            return cmd
        elif gcodeCommand.Command in [self.G0.Command, self.G1.Command]:
            gcodeCommand.Parameters["E"].Value = None
            return gcodeCommand.ToString(reform=True)
        elif gcodeCommand.Command in [
            self.M104.Command, self.M140.Command, self.M141.Command,
            self.M109.Command, self.M190.Command, self.M191.Command,
            self.M116.Command, self.M106.Command]:
            return ""
        else:
            return cmd

    def GetCommand(self, code):
        gcodeCommand = GetGcodeFromString(code)
        if gcodeCommand in self.CommandsDictionary.keys():
            # get the gcodeCommand from our dictionary
            cmd = self.CommandsDictionary[gcodeCommand]
            # set the gcode parts
            cmd.CommandParts = GcodeParts(code)
            # parse the gcodeCommand
            cmd.Parse()
            return cmd
        return None


class Responses(object):
    def __init__(self):
        self.M114 = Command(
            name="Get Position", command="M114",
            #regex="(?i).*?X:([-0-9.]+) Y:([-0-9.]+) Z:([-0-9.]+) E:([-0-9.]+).*?,"
            displayTemplate="Position: X={0}, Y={1}, Z={2}, E={3}",
            parameters=[
                CommandParameter("X", "(?i)^x:(?P<x>-?[0-9]{0,15}.?[0-9]{1,15})$", order=1),
                CommandParameter("Y", "(?i)^y:(?P<y>-?[0-9]{0,15}.?[0-9]{1,15})$", order=2),
                CommandParameter("Z", "(?i)^z:(?P<z>-?[0-9]{0,15}.?[0-9]{1,15})$", order=3),
                CommandParameter("E", "(?i)^e:(?P<e>-?[0-9]{0,15}.?[0-9]{1,15})$", order=4)
            ]
        )

