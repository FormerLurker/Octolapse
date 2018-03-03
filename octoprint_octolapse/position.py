# coding=utf-8

# This file is subject to the terms and conditions defined in
# file called 'LICENSE', which is part of this source code package.
from collections import deque

import octoprint_octolapse.command as command
import octoprint_octolapse.utility as utility
from octoprint_octolapse.extruder import Extruder


def GetFormattedCoordinates(x, y, z, e):
    xString = "None"
    if (x is not None):
        xString = GetFormattedCoordinate(float(x))

    yString = "None"
    if (y is not None):
        yString = GetFormattedCoordinate(float(y))

    zString = "None"
    if (z is not None):
        zString = GetFormattedCoordinate(float(z))

    eString = "None"
    if (e is not None):
        eString = GetFormattedCoordinate(float(e))

    return "(X:{0},Y:{1},Z:{2},E:{3})".format(xString, yString, zString,
                                              eString)


def GetFormattedCoordinate(coord):
    return "{0:.5f}".format(coord)


class Pos(object):
    def __init__(self, printer, octoprintPrinterProfile, pos=None):
        self.OctoprintPrinterProfile = octoprintPrinterProfile
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
        else:
            if printer.e_axis_default_mode in ['absolute', 'relative']:
                self.IsExtruderRelative = True if printer.e_axis_default_mode == 'relative' else False
            else:
                self.IsExtruderRelative = None
            if printer.xyz_axes_default_mode in ['absolute', 'relative']:
                self.IsRelative = True if printer.xyz_axes_default_mode == 'relative' else False
            else:
                self.IsRelative = None

        self.LastExtrusionHeight = None if pos is None else pos.LastExtrusionHeight
        # Layer and Height Tracking
        self.Layer = 0 if pos is None else pos.Layer
        self.Height = 0 if pos is None else pos.Height
        self.IsPrimed = False if pos is None else pos.IsPrimed

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

    def ResetState(self):
        self.IsLayerChange = False
        self.IsHeightChange = False
        self.IsZHop = False
        self.HasPositionChanged = False
        self.HasStateChanged = False
        self.HasReceivedHomeCommand = False

    def IsStateEqual(self, pos, tolerance):
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
            and self.HasPositionError == pos.HasPositionError
            and self.PositionError == pos.PositionError
            and self.HasReceivedHomeCommand == pos.HasReceivedHomeCommand):
            return True

        return False

    def IsPositionEqual(self, pos, tolerance):
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

    def ToStateDict(self):
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
            "Layer": self.Layer,
            "Height": self.Height,
            "LastExtrusionHeight": self.LastExtrusionHeight,
            "HasPositionError": self.HasPositionError,
            "PositionError": self.PositionError,
            "HasReceivedHomeCommand": self.HasReceivedHomeCommand
        }

    def ToPositionDict(self):
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
        }

    def ToDict(self):
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
            "LastExtrusionHeight": self.LastExtrusionHeight,
            "IsLayerChange": self.IsLayerChange,
            "IsZHop": self.IsZHop,
            "HasPositionError": self.HasPositionError,
            "PositionError": self.PositionError,
            "HasPositionChanged": self.HasPositionChanged,
            "HasStateChanged": self.HasStateChanged,
            "IsLayerChange": self.IsLayerChange,
            "Layer": self.Layer,
            "Height": self.Height,
            "HasReceivedHomeCommand": self.HasReceivedHomeCommand
        }

    def HasHomedAxis(self):
        return (self.XHomed and self.YHomed and self.ZHomed)

    def HasHomedPosition(self):
        return (self.HasHomedAxis() and self.X is not None
                and self.Y is not None and self.Z is not None)

    def UpdatePosition(self,
                       boundingBox,
                       x=None,
                       y=None,
                       z=None,
                       e=None,
                       f=None,
                       force=False):

        if (f is not None):
            self.F = float(f)
        if (force):
            # Force the coordinates in as long as they are provided.
            #
            if (x is not None):
                x = float(x)
                x = x + self.XOffset
                self.X = x
            if (y is not None):
                y = float(y)
                y = y + self.YOffset
                self.Y = y
            if (z is not None):
                z = float(z)
                z = z + self.ZOffset
                self.Z = z

            if (e is not None):
                e = float(e)
                e = e + self.EOffset
                self.E = e

        else:

            # Update the previous positions if values were supplied
            if (x is not None and self.XHomed):
                x = float(x)
                if (self.IsRelative):
                    if (self.X is not None):
                        self.X += x
                else:
                    self.X = x + self.XOffset

            if (y is not None and self.YHomed):
                y = float(y)
                if (self.IsRelative):
                    if (self.Y is not None):
                        self.Y += y
                else:
                    self.Y = y + self.YOffset

            if (z is not None and self.ZHomed):

                z = float(z)
                if (self.IsRelative):
                    if (self.Z is not None):
                        self.Z += z
                else:
                    self.Z = z + self.ZOffset

            if (e is not None):

                e = float(e)
                if (self.IsExtruderRelative):
                    if (self.E is not None):
                        self.EPrevious = self.E
                        self.E += e
                else:
                    self.EPrevious = self.E
                    self.E = e + self.EOffset

            if (not utility.IsInBounds(
                boundingBox, x=self.X, y=self.Y, z=self.Z)):
                self.HasPositionError = True
                self.PositionError = "Position - Coordinates {0} are out of the printer area!  Cannot resume position tracking until the axis is homed, or until absolute coordinates are received.".format(
                    GetFormattedCoordinates(self.X, self.Y, self.Z, self.E))
            else:
                self.HasPositionError = False
                self.PositionError = None


class Position(object):
    def __init__(self, octolapseSettings, octoprintPrinterProfile,
                 g90InfluencesExtruder):
        self.Settings = octolapseSettings
        self.Printer = self.Settings.CurrentPrinter()
        self.OctoprintPrinterProfile = octoprintPrinterProfile
        self.Origin = {
            "X": self.Printer.origin_x,
            "Y": self.Printer.origin_y,
            "Z": self.Printer.origin_z
        }

        self.BoundingBox = utility.GetBoundingBox(self.Printer,
                                                  octoprintPrinterProfile)
        self.PrinterTolerance = self.Printer.printer_position_confirmation_tolerance
        self.Positions = deque(maxlen=5)
        self.Reset()

        self.Extruder = Extruder(octolapseSettings)
        if self.Printer.g90_influences_extruder in ['true', 'false']:
            self.G90InfluencesExtruder = True if self.Printer.g90_influences_extruder == 'true' else False
        else:
            self.G90InfluencesExtruder = g90InfluencesExtruder

        if (self.Printer.z_hop is None):
            self.Printer.z_hop = 0

        self.Commands = command.Commands()
        self.CreateLocationDetectionCommands()

    def CreateLocationDetectionCommands(self):
        self.LocationDetectionCommands = []
        if (self.Printer.auto_position_detection_commands is not None):
            trimmedCommands = self.Printer.auto_position_detection_commands.strip(
            )
            if (len(trimmedCommands) > 0):
                self.LocationDetectionCommands = [
                    x.strip().upper()
                    for x in
                    self.Printer.auto_position_detection_commands.split(',')
                ]
        if ("G28" not in self.LocationDetectionCommands):
            self.LocationDetectionCommands.append("G28")
        if ("G29" not in self.LocationDetectionCommands):
            self.LocationDetectionCommands.append("G29")

    def Reset(self):
        # todo: This reset function doesn't seem to reset everything.
        self.Positions.clear()
        self.SavedPosition = None

    def UpdatePosition(self,
                       x=None,
                       y=None,
                       z=None,
                       e=None,
                       f=None,
                       force=False,
                       calculateChanges=False):
        numPositions = len(self.Positions)
        if (numPositions == 0):
            return
        pos = self.Positions[0]
        pos.UpdatePosition(self.BoundingBox, x, y, z, e, f, force)
        if (calculateChanges and numPositions > 1):
            previousPos = self.Positions[1]
            pos.HasPositionChanged = not pos.IsPositionEqual(
                previousPos, self.PrinterTolerance)
            pos.HasStateChanged = not pos.IsStateEqual(previousPos,
                                                       self.PrinterTolerance)

    def SavePosition(self, x=None, y=None, z=None, e=None, f=None,
                     force=False):
        if (len(self.Positions) == 0):
            return
        self.SavedPosition = Pos(self.Printer, self.OctoprintPrinterProfile, self.Positions[0])

    def ToDict(self):
        positionDict = None
        if (len(self.Positions) > 0):
            previousPos = self.Positions[0]
            return previousPos.ToDict()
        return None

    def ToPositionDict(self):
        positionDict = None
        if (len(self.Positions) > 0):
            previousPos = self.Positions[0]
            return previousPos.ToPositionDict()
        return None

    def ToStateDict(self):
        positionDict = None
        if (len(self.Positions) > 0):
            previousPos = self.Positions[0]
            return previousPos.ToStateDict()
        return None

    def GetPosition(self, index=0):
        if (len(self.Positions) > index):
            return self.Positions[index]
        return None

    def ZDelta(self, pos, index=0):
        previousPos = self.GetPosition(index)
        if (previousPos is not None):
            # calculate ZDelta
            if (pos.Height is not None):
                if (previousPos.Height is None):
                    return pos.Height
                else:
                    return pos.Height - previousPos.Height
        return 0

    def DistanceToZLift(self, index=0):
        pos = self.GetPosition(index)
        if (pos is None):
            return None
        currentLift = utility.round_to(pos.Z - pos.Height,
                                       self.PrinterTolerance)
        if (currentLift < self.Printer.z_hop):
            return self.Printer.z_hop - currentLift
        return 0

    def HasStateChanged(self, index=0):
        pos = self.GetPosition(index)
        if (pos is None):
            return None
        return pos.HasStateChanged

    def HasPositionChanged(self, index=0):
        pos = self.GetPosition(index)
        if (pos is None):
            return None
        return pos.HasPositionChanged

    def HasPositionError(self, index=0):
        pos = self.GetPosition(index)
        if (pos is None):
            return None
        return pos.HasPositionError

    def PositionError(self, index=0):
        pos = self.GetPosition(index)
        if (pos is None):
            return None
        return pos.PositionError

    def X(self, index=0):
        pos = self.GetPosition(index)
        if (pos is None):
            return None
        return pos.X

    def XOffset(self, index=0):
        pos = self.GetPosition(index)
        if (pos is None):
            return None
        return pos.XOffset

    def Y(self, index=0):
        pos = self.GetPosition(index)
        if (pos is None):
            return None
        return pos.Y

    def YOffset(self, index=0):
        pos = self.GetPosition(index)
        if (pos is None):
            return None
        return pos.YOffset

    def Z(self, index=0):
        pos = self.GetPosition(index)
        if (pos is None):
            return None
        return pos.Z

    def ZOffset(self, index=0):
        pos = self.GetPosition(index)
        if (pos is None):
            return None
        return pos.ZOffset

    def E(self, index=0):
        pos = self.GetPosition(index)
        if (pos is None):
            return None
        return pos.E

    def EOffset(self, index=0):
        pos = self.GetPosition(index)
        if (pos is None):
            return None
        return pos.EOffset

    def F(self, index=0):
        pos = self.GetPosition(index)
        if (pos is None):
            return None
        return pos.F

    def IsZHop(self, index=0):
        pos = self.GetPosition(index)
        if (pos is None):
            return None
        return pos.IsZHop

    def IsLayerChange(self, index=0):
        pos = self.GetPosition(index)
        if (pos is None):
            return None
        return pos.IsLayerChange

    def Layer(self, index=0):
        pos = self.GetPosition(index)
        if (pos is None):
            return None
        return pos.Layer

    def Height(self, index=0):
        pos = self.GetPosition(index)
        if (pos is None):
            return None
        return pos.Height

    def IsRelative(self, index=0):
        pos = self.GetPosition(index)
        if (pos is None):
            return None
        return pos.IsRelative

    def IsExtruderRelative(self, index=0):
        pos = self.GetPosition(index)
        if (pos is None):
            return None
        return pos.IsExtruderRelative

    def HasReceivedHomeCommand(self, index=0):
        pos = self.GetPosition(index)
        if (pos is None):
            return False
        return pos.HasReceivedHomeCommand and self.HasHomedAxis(index)

    def DoesCommandRequireLocationDetection(self, cmd):
        if (self.Printer.auto_detect_position):
            gcode = command.GetGcodeFromString(cmd)
            if (gcode in self.LocationDetectionCommands):
                return True
        return False

    def RequiresLocationDetection(self, index=0):
        pos = self.GetPosition(index)
        if (pos is None):
            return False

        if (self.DoesCommandRequireLocationDetection(pos.GCode)):
            return True
        return False

    def UndoUpdate(self):
        pos = self.GetPosition(0)
        if (pos is not None):
            self.Positions.popleft()
        self.Extruder.UndoUpdate()

    def GetPosition(self, index=0):
        if (len(self.Positions) > index):
            return self.Positions[index]
        return None

    def Update(self, gcode):
        cmd = self.Commands.GetCommand(gcode)
        # a new position

        pos = None
        previousPos = None
        numPositions = len(self.Positions)
        if (numPositions > 0):
            pos = Pos(self.Printer, self.OctoprintPrinterProfile, self.Positions[0])
            previousPos = Pos(self.Printer, self.OctoprintPrinterProfile, self.Positions[0])
        if (pos is None):
            pos = Pos(self.Printer, self.OctoprintPrinterProfile)
        if (previousPos is None):
            previousPos = Pos(self.Printer, self.OctoprintPrinterProfile)

        # reset the current position state (copied from the previous position,
        # or a
        # new position)
        pos.ResetState()
        # set the pos gcode cmd
        pos.GCode = gcode

        # apply the cmd to the position tracker
        if (cmd is not None):
            # I'm currently too lazy to keep this DRY
            # TODO: Make DRY
            if (cmd.Command in ["G0", "G1"]):
                # Movement
                if (cmd.Parse()):
                    self.Settings.CurrentDebugProfile(
                    ).LogPositionCommandReceived("Received {0}".format(
                        cmd.Name))
                    x = cmd.Parameters["X"].Value
                    y = cmd.Parameters["Y"].Value
                    z = cmd.Parameters["Z"].Value
                    e = cmd.Parameters["E"].Value
                    f = cmd.Parameters["F"].Value

                    if (x is not None or y is not None or z is not None
                        or f is not None):
                        if pos.IsRelative is not None:
                            if (pos.HasPositionError and not pos.IsRelative):
                                pos.HasPositionError = False
                                pos.PositionError = ""
                            pos.UpdatePosition(
                                self.BoundingBox, x, y, z, e=None, f=f)
                        else:
                            self.Settings.CurrentDebugProfile().LogPositionCommandReceived(
                                "Position - Unable to update the X/Y/Z axis position, the axis mode (relative/absolute) has not been explicitly set via G90/G91."
                            )
                    if (e is not None):
                        if (pos.IsExtruderRelative is not None):
                            if (pos.HasPositionError
                                and not pos.IsExtruderRelative):
                                pos.HasPositionError = False
                                pos.PositionError = ""
                            pos.UpdatePosition(
                                self.BoundingBox,
                                x=None,
                                y=None,
                                z=None,
                                e=e,
                                f=None)
                        else:
                            self.Settings.CurrentDebugProfile().LogError(
                                "Position - Unable to update the extruder position, the extruder mode (relative/absolute) has been selected (absolute/relative)."
                            )
                    message = "Position Change - {0} - {1} Move From(X:{2},Y:{3},Z:{4},E:{5}) - To(X:{6},Y:{7},Z:{8},E:{9})"
                    if (previousPos is None):
                        message = message.format(
                            gcode, "Relative"
                            if pos.IsRelative else "Absolute", "None", "None",
                            "None", "None", pos.X, pos.Y, pos.Z, pos.E)
                    else:
                        message = message.format(
                            gcode, "Relative"
                            if pos.IsRelative else "Absolute", previousPos.X,
                            previousPos.Y, previousPos.Z, previousPos.E, pos.X,
                            pos.Y, pos.Z, pos.E)
                    self.Settings.CurrentDebugProfile().LogPositionChange(
                        message)

                else:
                    self.Settings.CurrentDebugProfile().LogError(
                        "Position - Unable to parse the gcode command: {0}".
                            format(gcode))
            elif (cmd.Command == "G28"):
                # Home
                if (cmd.Parse()):
                    pos.HasReceivedHomeCommand = True
                    x = cmd.Parameters["X"].Value
                    y = cmd.Parameters["Y"].Value
                    z = cmd.Parameters["Z"].Value
                    w = cmd.Parameters["W"].Value
                    xHomed = False
                    yHomed = False
                    zHomed = False
                    if (x is not None):
                        xHomed = True
                    if (y is not None):
                        yHomed = True
                    if (z is not None):
                        zHomed = True
                    # removing the test for the W param.  I think it can be
                    # safely ignored
                    # here.
                    # Todo: Create issue to monitor and get feedback regarding
                    # the W param
                    # if (x is None and y is None and z is None and w is None):
                    if (x is None and y is None and z is None):
                        xHomed = True
                        yHomed = True
                        zHomed = True

                    homeStrings = []
                    if (xHomed):
                        pos.XHomed = True
                        pos.X = self.Origin[
                            "X"] if not self.Printer.auto_detect_position else None
                        if (pos.X is None):
                            homeStrings.append("Homing X to Unknown Origin.")
                        else:
                            homeStrings.append("Homing X to {0}.".format(
                                GetFormattedCoordinate(pos.X)))
                    if (yHomed):
                        pos.YHomed = True
                        pos.Y = self.Origin[
                            "Y"] if not self.Printer.auto_detect_position else None
                        if (pos.Y is None):
                            homeStrings.append("Homing Y to Unknown Origin.")
                        else:
                            homeStrings.append("Homing Y to {0}.".format(
                                GetFormattedCoordinate(pos.Y)))
                    if (zHomed):
                        pos.ZHomed = True
                        pos.Z = self.Origin[
                            "Z"] if not self.Printer.auto_detect_position else None
                        if (pos.Z is None):
                            homeStrings.append("Homing Z to Unknown Origin.")
                        else:
                            homeStrings.append("Homing Z to {0}.".format(
                                GetFormattedCoordinate(pos.Z)))

                    self.Settings.CurrentDebugProfile(
                    ).LogPositionCommandReceived("Received G28 - ".format(
                        " ".join(homeStrings)))
                    pos.HasPositionError = False
                    pos.PositionError = None
                    # we must do this in case we have more than one home
                    # command
                    previousPos = Pos(self.Printer, self.OctoprintPrinterProfile, pos)
                else:
                    self.Settings.CurrentDebugProfile().LogError(
                        "Position - Unable to parse the Gcode:{0}".format(
                            gcode))

            elif cmd.Command == "G90":
                # change x,y,z to absolute
                if pos.IsRelative is None or pos.IsRelative:
                    self.Settings.CurrentDebugProfile(
                    ).LogPositionCommandReceived(
                        "Received G90 - Switching to absolute x,y,z coordinates."
                    )
                    pos.IsRelative = False
                else:
                    self.Settings.CurrentDebugProfile(
                    ).LogPositionCommandReceived(
                        "Received G90 - Already using absolute x,y,z coordinates."
                    )

                # for some firmwares we need to switch the extruder to
                # absolute
                # coordinates
                # as well
                if self.G90InfluencesExtruder:
                    if pos.IsExtruderRelative is None or pos.IsExtruderRelative:
                        self.Settings.CurrentDebugProfile(
                        ).LogPositionCommandReceived(
                            "Received G90 - Switching to absolute extruder coordinates"
                        )
                        pos.IsExtruderRelative = False
                    else:
                        self.Settings.CurrentDebugProfile(
                        ).LogPositionCommandReceived(
                            "Received G90 - Already using absolute extruder coordinates"
                        )
            elif (cmd.Command == "G91"):
                # change x,y,z to relative
                if (pos.IsRelative is None or not pos.IsRelative):
                    self.Settings.CurrentDebugProfile(
                    ).LogPositionCommandReceived(
                        "Received G91 - Switching to relative x,y,z coordinates"
                    )
                    pos.IsRelative = True
                else:
                    self.Settings.CurrentDebugProfile(
                    ).LogPositionCommandReceived(
                        "Received G91 - Already using relative x,y,z coordinates"
                    )

                # for some firmwares we need to switch the extruder to
                # absolute
                # coordinates
                # as well
                if (self.G90InfluencesExtruder):
                    if (pos.IsExtruderRelative is None or not pos.IsExtruderRelative):
                        self.Settings.CurrentDebugProfile(
                        ).LogPositionCommandReceived(
                            "Received G91 - Switching to relative extruder coordinates"
                        )
                        pos.IsExtruderRelative = True
                    else:
                        self.Settings.CurrentDebugProfile(
                        ).LogPositionCommandReceived(
                            "Received G91 - Already using relative extruder coordinates"
                        )
            elif (cmd.Command == "M83"):
                # Extruder - Set Relative
                if (pos.IsExtruderRelative is None
                    or not pos.IsExtruderRelative):
                    self.Settings.CurrentDebugProfile(
                    ).LogPositionCommandReceived(
                        "Received M83 - Switching Extruder to Relative Coordinates"
                    )
                    pos.IsExtruderRelative = True
            elif (cmd.Command == "M82"):
                # Extruder - Set Absolute
                if (pos.IsExtruderRelative is None or pos.IsExtruderRelative):
                    self.Settings.CurrentDebugProfile(
                    ).LogPositionCommandReceived(
                        "Received M82 - Switching Extruder to Absolute Coordinates"
                    )
                    pos.IsExtruderRelative = False
            elif (cmd.Command == "G92"):
                # Set Position (offset)
                if (cmd.Parse()):
                    x = cmd.Parameters["X"].Value
                    y = cmd.Parameters["Y"].Value
                    z = cmd.Parameters["Z"].Value
                    e = cmd.Parameters["E"].Value
                    if (x is None and y is None and z is None and e is None):
                        pos.XOffset = pos.X
                        pos.YOffset = pos.Y
                        pos.ZOffset = pos.Z
                        pos.EOffset = pos.E
                    # set the offsets if they are provided
                    if (x is not None and pos.X is not None and pos.XHomed):
                        pos.XOffset = pos.X - utility.getfloat(x, 0)
                    if (y is not None and pos.Y is not None and pos.YHomed):
                        pos.YOffset = pos.Y - utility.getfloat(y, 0)
                    if (z is not None and pos.Z is not None and pos.ZHomed):
                        pos.ZOffset = pos.Z - utility.getfloat(z, 0)
                    if (e is not None and pos.E is not None):
                        pos.EOffset = pos.E - utility.getfloat(e, 0)
                    self.Settings.CurrentDebugProfile(
                    ).LogPositionCommandReceived(
                        "Received G92 - Set Position.  Command:{0}, XOffset:{1}, YOffset:{2}, ZOffset:{3}, EOffset:{4}".
                            format(gcode, pos.XOffset, pos.YOffset, pos.ZOffset,
                                   pos.EOffset))
                else:
                    self.Settings.CurrentDebugProfile().LogError(
                        "Position - Unable to parse the Gcode:{0}".format(
                            gcode))

        ########################################
        # Update the extruder monitor.
        self.Extruder.Update(self.ERelative(pos))
        ########################################
        # If we have a homed axis, detect changes.
        ########################################
        hasExtruderChanged = self.Extruder.HasChanged()

        pos.HasPositionChanged = not pos.IsPositionEqual(
            previousPos, 0)
        pos.HasStateChanged = not pos.IsStateEqual(previousPos,
                                                   self.PrinterTolerance)

        if (pos.HasHomedPosition() and previousPos.HasHomedPosition()):

            # if (hasExtruderChanged or pos.HasPositionChanged):

            # calculate LastExtrusionHeight and Height
            if self.Extruder.IsExtruding():
                pos.LastExtrusionHeight = pos.Z

                # see if we have primed yet
                if self.Printer.priming_height > 0:
                    if (not pos.IsPrimed and pos.LastExtrusionHeight < self.Printer.priming_height):
                        pos.IsPrimed = True
                else:
                    # if we have no priming height set, just set IsPrimed = true.
                    pos.IsPrimed = True

                # make sure we are primed before calculating height/layers
                if (pos.IsPrimed):
                    if (pos.Height is None or
                        utility.round_to(pos.Z, self.PrinterTolerance)
                        > previousPos.Height):
                        pos.Height = utility.round_to(
                            pos.Z, self.PrinterTolerance)
                        self.Settings.CurrentDebugProfile(
                        ).LogPositionHeightChange(
                            "Position - Reached New Height:{0}.".format(
                                pos.Height))

                    # calculate layer change
                    if (utility.round_to(
                        self.ZDelta(pos), self.PrinterTolerance) > 0
                        or pos.Layer == 0):
                        pos.IsLayerChange = True
                        pos.Layer += 1
                        self.Settings.CurrentDebugProfile(
                        ).LogPositionLayerChange(
                            "Position - Layer:{0}.".format(pos.Layer))
                    else:
                        pos.IsLayerChange = False

            # Calculate ZHop based on last extrusion height
            if (pos.LastExtrusionHeight is not None):
                # calculate lift, taking into account floating point
                # rounding
                lift = utility.round_to(
                    pos.Z - pos.LastExtrusionHeight,
                    self.PrinterTolerance)
                if (lift >= self.Printer.z_hop):
                    lift = self.Printer.z_hop
                isLifted = lift >= self.Printer.z_hop and (
                    not self.Extruder.IsExtruding() or self.Extruder.IsExtrudingStart()
                )

                if isLifted or self.Printer.z_hop == 0:
                    pos.IsZHop = True

            if pos.IsZHop and self.Printer.z_hop > 0:
                self.Settings.CurrentDebugProfile().LogPositionZHop(
                    "Position - Zhop:{0}".format(self.Printer.z_hop))

        self.Positions.appendleft(pos)

    def HasHomedPosition(self, index=0):
        if (len(self.Positions) <= index):
            return None
        pos = self.Positions[index]
        return pos.HasHomedPosition()

    def HasHomedAxis(self, index=0):
        if (len(self.Positions) <= index):
            return None
        pos = self.Positions[index]
        return pos.HasHomedAxis()

    def ERelative(self, pos):
        if (len(self.Positions) < 1):
            return None
        previousPos = self.Positions[0]
        return pos.E - previousPos.E

    def IsAtPosition(self, x, y, z, pos, tolerance, applyOffset):
        if (applyOffset):
            x = x + pos.XOffset
            y = y + pos.YOffset
            if (z is not None):
                z = z + pos.ZOffset

        if ((pos.X is None or utility.isclose(pos.X, x, abs_tol=tolerance)) and
            (pos.Y is None or utility.isclose(pos.Y, y, abs_tol=tolerance))
            and (z is None or pos.Z is None
                 or utility.isclose(pos.Z, z, abs_tol=tolerance))):
            return True
        return False

    def IsAtPreviousPosition(self, x, y, z=None, applyOffset=True):
        if (len(self.Positions) < 2):
            return False
        return self.IsAtPosition(
            x, y, z, self.Positions[1],
            self.Printer.printer_position_confirmation_tolerance, True)

    def IsAtCurrentPosition(self, x, y, z=None, applyOffset=True):
        if (len(self.Positions) < 1):
            return False
        return self.IsAtPosition(
            x, y, z, self.Positions[0],
            self.Printer.printer_position_confirmation_tolerance, True)

    def IsAtSavedPosition(self, x, y, z=None, applyOffset=True):
        if (self.SavedPosition is None):
            return False
        return self.IsAtPosition(
            x, y, z, self.SavedPosition,
            self.Printer.printer_position_confirmation_tolerance, True)

    def GetPositionString(self, index=0):
        if (len(self.Positions) < 1):
            return GetFormattedCoordinates(None, None, None, None)
        currentPosition = self.Positions[0]
        return GetFormattedCoordinates(currentPosition.X, currentPosition.Y,
                                       currentPosition.Z, currentPosition.E)
