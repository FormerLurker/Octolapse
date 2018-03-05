# coding=utf-8

import collections
import operator
# This file is subject to the terms and conditions defined in
# file called 'LICENSE', which is part of this source code package.
import re
import string
import sys

import octoprint_octolapse.utility as utility
from octoprint_octolapse.command import Commands
from octoprint_octolapse.settings import *


class SnapshotGcode(object):
    CommandsDictionary = Commands()

    def __init__(self, isTestMode):
        self.GcodeCommands = []
        self.__OriginalGcodeCommands = []
        self.X = None
        self.ReturnX = None
        self.Y = None
        self.ReturnY = None
        self.Z = None
        self.ReturnZ = None
        self.SnapshotIndex = -1
        self.IsTestMode = isTestMode

    def Append(self, command):
        self.__OriginalGcodeCommands.append(command)

        if self.IsTestMode:
            command = self.CommandsDictionary.GetTestModeCommandString(command)
        command = command.upper().strip()
        if command != "":
            self.GcodeCommands.append(command)

    def EndIndex(self):
        return len(self.GcodeCommands) - 1

    def SetSnapshotIndex(self):
        self.SnapshotIndex = self.EndIndex()

    def GetOriginalReturnCommands(self):
        if len(self.__OriginalGcodeCommands) > self.SnapshotIndex + 1:
            return self.__OriginalGcodeCommands[self.SnapshotIndex + 1:]
        return []

    def SnapshotCommands(self):
        if len(self.GcodeCommands) > 0:
            return self.GcodeCommands[0:self.SnapshotIndex + 1]
        return []

    def ReturnCommands(self):
        if len(self.GcodeCommands) > self.SnapshotIndex + 1:
            return self.GcodeCommands[self.SnapshotIndex + 1:]
        return []


class SnapshotGcodeGenerator(object):
    CurrentXPathIndex = 0
    CurrentYPathIndex = 0

    def __init__(self, octolapseSettings, octoprintPrinterProfile):
        self.Settings = octolapseSettings
        self.StabilizationPaths = self.Settings.current_stabilization().get_stabilization_paths()
        self.Snapshot = Snapshot(self.Settings.current_snapshot())
        self.Printer = Printer(self.Settings.current_printer())
        self.OctoprintPrinterProfile = octoprintPrinterProfile
        self.BoundingBox = utility.get_bounding_box(
            self.Printer, octoprintPrinterProfile)
        self.IsTestMode = self.Settings.current_debug_profile().is_test_mode
        self.HasSnapshotPositionErrors = False
        self.SnapshotPositionErrors = ""

    def Reset(self):
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

    def GetSnapshotPosition(self, xPos, yPos):
        xPath = self.StabilizationPaths["X"]
        xPath.CurrentPosition = xPos
        yPath = self.StabilizationPaths["Y"]
        yPath.CurrentPosition = yPos

        coords = dict(X=self.GetSnapshotCoordinate(xPath),
                      Y=self.GetSnapshotCoordinate(yPath))

        if not utility.is_in_bounds(self.BoundingBox, x=coords["X"]):

            message = "The snapshot X position ({0}) is out of bounds!".format(
                coords["X"])
            self.HasSnapshotPositionErrors = True
            self.Settings.current_debug_profile().log_error(
                "gcode.py - GetSnapshotPosition - {0}".format(message))
            if self.Printer.abort_out_of_bounds:
                coords["X"] = None
            else:
                coords["X"] = utility.get_closest_in_bounds_position(
                    self.BoundingBox, x=coords["X"])["X"]
                message += "  Using nearest in-bound position ({0}).".format(
                    coords["X"])
            self.SnapshotPositionErrors += message
        if not utility.is_in_bounds(self.BoundingBox, y=coords["Y"]):
            message = "The snapshot Y position ({0}) is out of bounds!".format(
                coords["Y"])
            self.HasSnapshotPositionErrors = True
            self.Settings.current_debug_profile().log_error(
                "gcode.py - GetSnapshotPosition - {0}".format(message))
            if self.Printer.abort_out_of_bounds:
                coords["Y"] = None
            else:
                coords["Y"] = utility.get_closest_in_bounds_position(
                    self.BoundingBox, y=coords["Y"])["Y"]
                message += "  Using nearest in-bound position ({0}).".format(
                    coords["Y"])
            if len(self.SnapshotPositionErrors) > 0:
                self.SnapshotPositionErrors += "  "
            self.SnapshotPositionErrors += message
        return coords

    def GetSnapshotCoordinate(self, path):
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
            return self.GetBedRelativeCoordinate(path.Axis, coord)

    def GetBedRelativeCoordinate(self, axis, coord):
        relCoord = None
        if axis == "X":
            relCoord = self.GetBedRelativeX(coord)
        elif axis == "Y":
            relCoord = self.GetBedRelativeY(coord)
        elif axis == "Z":
            relCoord = self.GetBedRelativeZ(coord)

        return relCoord

    def GetBedRelativeX(self, percent):
        return self.GetRelativeCoordinate(percent, self.BoundingBox["min_x"], self.BoundingBox["max_x"])

    def GetBedRelativeY(self, percent):
        return self.GetRelativeCoordinate(percent, self.BoundingBox["min_y"], self.BoundingBox["max_y"])

    def GetBedRelativeZ(self, percent):
        return self.GetRelativeCoordinate(percent, self.BoundingBox["min_z"], self.BoundingBox["max_z"])

    def GetRelativeCoordinate(self, percent, min, max):
        return ((float(max) - float(min)) * (percent / 100.0)) + float(min)

    def AppendFeedrateGcode(self, snapshotGcode, desiredSpeed):
        if desiredSpeed > 0:
            snapshotGcode.Append(self.GetFeedrateSetGcode(desiredSpeed))
            self.FCurrent = desiredSpeed

    def CreateSnapshotGcode(self, x, y, z, f, isRelative, isExtruderRelative, extruder, zLift, savedCommand=None):
        self.Reset()
        if x is None or y is None or z is None:
            self.HasSnapshotPositionErrors = True
            message = "Cannot create GCode when x,y,or z is None.  Values: x:{0} y:{1} z:{2}".format(
                x, y, z)
            self.SnapshotPositionErrors = message
            self.Settings.current_debug_profile().log_error(
                "gcode.py - CreateSnapshotGcode - {0}".format(message))
            return None

        self.FOriginal = f
        self.FCurrent = f
        self.RetractedBySnapshotStartGcode = False
        self.RetractedLength = 0
        self.ZhopBySnapshotStartGcode = False
        self.ZLift = zLift
        self.IsRelativeOriginal = isRelative
        self.IsRelativeCurrent = isRelative
        self.IsExtruderRelativeOriginal = isExtruderRelative
        self.IsExtruderRelativeCurrent = isExtruderRelative

        newSnapshotGcode = SnapshotGcode(self.IsTestMode)
        # retract if necessary
        # Note that if IsRetractedStart is true, that means the printer is now retracted.  IsRetracted will be false because we've undone the previous position update.
        if self.Snapshot.retract_before_move and not (extruder.is_retracted() or extruder.is_retracting_start()):
            if not self.IsExtruderRelativeCurrent:
                newSnapshotGcode.Append(
                    self.GetSetExtruderRelativePositionGcode())
                self.IsExtruderRelativeCurrent = True
            self.AppendFeedrateGcode(
                newSnapshotGcode, self.Printer.retract_speed)
            retractedLength = extruder.length_to_retract()
            if retractedLength > 0:
                newSnapshotGcode.Append(self.GetRetractGcode(retractedLength))
                self.RetractedLength = retractedLength
                self.RetractedBySnapshotStartGcode = True
        # Can we hop or is the print too tall?

        # todo: detect zhop and only zhop if we are not currently hopping.
        canZHop = self.Printer.z_hop > 0 and utility.is_in_bounds(
            self.BoundingBox, z=z + self.Printer.z_hop)
        # if we can ZHop, do
        if canZHop and self.ZLift > 0:
            if not self.IsRelativeCurrent:  # must be in relative mode
                newSnapshotGcode.Append(self.GetSetRelativePositionGcode())
                self.IsRelativeCurrent = True
            self.AppendFeedrateGcode(
                newSnapshotGcode, self.Printer.z_hop_speed)
            newSnapshotGcode.Append(self.GetRelativeZLiftGcode(self.ZLift))
            self.ZhopBySnapshotStartGcode = True

        # Wait for current moves to finish before requesting the startgcodeposition
        # newSnapshotGcode.Append(self.GetWaitForCurrentMovesToFinishGcode())

        # Get the final position after the saved command.  When we get this position we'll know it's time to resume the print.
        # newSnapshotGcode.Append(self.GetPositionGcode())
        # Log the commands
        # self.Settings.CurrentDebugProfile().LogSnapshotGcode("Snapshot Start Gcode")
        # for str in newSnapshotGcode.GcodeCommands:
        #	self.Settings.CurrentDebugProfile().LogSnapshotGcode("    {0}".format(str))

        # End start gcode
        # Create code to move from the current extruder position to the snapshot position
        # get the X and Y coordinates of the snapshot
        snapshotPosition = self.GetSnapshotPosition(x, y)
        newSnapshotGcode.X = snapshotPosition["X"]
        newSnapshotGcode.Y = snapshotPosition["Y"]

        if newSnapshotGcode.X is None or newSnapshotGcode.Y is None:
            # either x or y is out of bounds.
            return None

        # Move back to the snapshot position - make sure we're in absolute mode for this
        if self.IsRelativeCurrent:  # must be in absolute mode
            newSnapshotGcode.Append(self.GetSetAbsolutePositionGcode())
            self.IsRelativeCurrent = False

        # speed change - Set to movement speed IF we have specified one

        self.AppendFeedrateGcode(newSnapshotGcode, self.Printer.movement_speed)

        # Move to Snapshot Position
        newSnapshotGcode.Append(self.GetMoveGcode(
            newSnapshotGcode.X, newSnapshotGcode.Y))

        # Wait for current moves to finish before requesting the position
        newSnapshotGcode.Append(self.GetWaitForCurrentMovesToFinishGcode())

        # Get the final position after moving.  When we get a response from the, we'll know that the snapshot is ready to be taken
        newSnapshotGcode.Append(self.GetPositionGcode())
        # mark the snapshot command index
        newSnapshotGcode.SetSnapshotIndex()

        # create return gcode
        # record our previous position for posterity
        newSnapshotGcode.ReturnX = x
        newSnapshotGcode.ReturnY = y
        newSnapshotGcode.ReturnZ = z

        # Move back to previous position - make sure we're in absolute mode for this (hint: we already are right now)
        # if self.IsRelativeCurrent:
        #	newSnapshotGcode.Append(self.GetSetAbsolutePositionGcode())
        #	self.IsRelativeCurrent = False

        if x is not None and y is not None:
            newSnapshotGcode.Append(self.GetMoveGcode(x, y))

        # If we zhopped in the beginning, lower z
        if self.ZhopBySnapshotStartGcode:
            if not self.IsRelativeCurrent:
                newSnapshotGcode.Append(self.GetSetRelativePositionGcode())
                self.IsRelativeCurrent = True
            self.AppendFeedrateGcode(
                newSnapshotGcode, self.Printer.z_hop_speed)
            newSnapshotGcode.Append(self.GetRelativeZLowerGcode(self.ZLift))

        # detract
        if self.RetractedBySnapshotStartGcode:
            if not self.IsExtruderRelativeCurrent:
                newSnapshotGcode.Append.GetSetExtruderRelativePositionGcode()
                self.IsExtruderRelativeCurrent = True
            self.AppendFeedrateGcode(
                newSnapshotGcode, self.Printer.detract_speed)
            if self.RetractedLength > 0:
                newSnapshotGcode.Append(
                    self.GetDetractGcode(self.RetractedLength))

        # reset the coordinate systems for the extruder and axis
        if self.IsRelativeOriginal != self.IsRelativeCurrent:
            if self.IsRelativeCurrent:
                newSnapshotGcode.Append(self.GetSetAbsolutePositionGcode())
            else:
                newSnapshotGcode.Append(self.GetSetRelativePositionGcode())
            self.IsRelativeCurrent = self.IsRelativeOriginal

        if self.IsExtruderRelativeOriginal != self.IsExtruderRelativeCurrent:
            if self.IsExtruderRelativeOriginal:
                newSnapshotGcode.Append(
                    self.GetSetExtruderRelativePositionGcode())
            else:
                newSnapshotGcode.Append(
                    self.GetSetExtruderAbslutePositionGcode())

        # Make sure we return to the original feedrate
        self.AppendFeedrateGcode(newSnapshotGcode, self.FOriginal)
        # What the hell was this for?!
        # newSnapshotGcode.GcodeCommands[-1] = "{0}".format(newSnapshotGcode.GcodeCommands[-1])
        # add the saved command, if there is one
        if savedCommand is not None:
            newSnapshotGcode.Append(savedCommand)

        # Wait for current moves to finish before requesting the save command position
        newSnapshotGcode.Append(self.GetWaitForCurrentMovesToFinishGcode())

        # Get the final position after the saved command.  When we get this position we'll know it's time to resume the print.
        newSnapshotGcode.Append(self.GetPositionGcode())

        self.Settings.current_debug_profile().log_snapshot_gcode(
            "Snapshot Gcode - SnapshotCommandIndex:{0}, EndIndex{1}, Gcode:".format(newSnapshotGcode.SnapshotIndex,
                                                                                    newSnapshotGcode.EndIndex()))
        for str in newSnapshotGcode.GcodeCommands:
            self.Settings.current_debug_profile(
            ).log_snapshot_gcode("    {0}".format(str))

        self.Settings.current_debug_profile().log_snapshot_position(
            "Snapshot Position: (x:{0:f},y:{1:f})".format(newSnapshotGcode.X, newSnapshotGcode.Y))
        self.Settings.current_debug_profile().log_snapshot_return_position(
            "Return Position: (x:{0:f},y:{1:f})".format(newSnapshotGcode.ReturnX, newSnapshotGcode.ReturnY))

        return newSnapshotGcode

    def GetSetExtruderRelativePositionGcode(self):
        return "M83"

    def GetSetExtruderAbslutePositionGcode(self):
        return "M82"

    def GetSetAbsolutePositionGcode(self):
        return "G90"

    def GetSetRelativePositionGcode(self):
        return "G91"

    def GetDelayGcode(self, delay):
        return "G4 P{0:d}".format(delay)

    def GetMoveGcode(self, x, y):
        return "G1 X{0:.3f} Y{1:.3f}".format(x, y)

    def GetRelativeZLiftGcode(self, distance):
        return "G1 Z{0:.3f}".format(distance)

    def GetRelativeZLowerGcode(self, distance):
        return "G1 Z{0:.3f}".format(-1.0 * distance)

    def GetRetractGcode(self, distance):
        return "G1 E{0:.3f}".format(-1 * distance)

    def GetDetractGcode(self, distance):
        return "G1 E{0:.3f}".format(distance)

    def GetResetLineNumberGcode(self, lineNumber):
        return "M110 N{0:d}".format(lineNumber)

    def GetWaitForCurrentMovesToFinishGcode(self):
        return "M400"

    def GetPositionGcode(self):
        return "M114"

    def GetFeedrateSetGcode(self, f):
        return "G1 F{0}".format(int(f))
