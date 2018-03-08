# coding=utf-8

# This file is subject to the terms and conditions defined in
# file called 'LICENSE', which is part of this source code package.

from octoprint_octolapse.command import Commands
from octoprint_octolapse.settings import *


class SnapshotGcode(object):
    CommandsDictionary = Commands()

    def __init__(self, is_test_mode):
        self.GcodeCommands = []
        self.__OriginalGcodeCommands = []
        self.X = None
        self.ReturnX = None
        self.Y = None
        self.ReturnY = None
        self.Z = None
        self.ReturnZ = None
        self.SnapshotIndex = -1
        self.IsTestMode = is_test_mode

    def append(self, command):
        self.__OriginalGcodeCommands.append(command)

        if self.IsTestMode:
            command = self.CommandsDictionary.get_test_mode_command_string(command)
        command = command.upper().strip()
        if command != "":
            self.GcodeCommands.append(command)

    def end_index(self):
        return len(self.GcodeCommands) - 1

    def set_snapshot_index(self):
        self.SnapshotIndex = self.end_index()

    def get_original_return_commands(self):
        if len(self.__OriginalGcodeCommands) > self.SnapshotIndex + 1:
            return self.__OriginalGcodeCommands[self.SnapshotIndex + 1:]
        return []

    def get_snapshot_commands(self):
        if len(self.GcodeCommands) > 0:
            return self.GcodeCommands[0:self.SnapshotIndex + 1]
        return []

    def get_return_commands(self):
        if len(self.GcodeCommands) > self.SnapshotIndex + 1:
            return self.GcodeCommands[self.SnapshotIndex + 1:]
        return []


class SnapshotGcodeGenerator(object):
    CurrentXPathIndex = 0
    CurrentYPathIndex = 0

    def __init__(self, octolapse_settings, octoprint_printer_profile):
        self.Settings = octolapse_settings
        self.StabilizationPaths = self.Settings.current_stabilization().get_stabilization_paths()
        self.Snapshot = Snapshot(self.Settings.current_snapshot())
        self.Printer = Printer(self.Settings.current_printer())
        self.OctoprintPrinterProfile = octoprint_printer_profile
        self.BoundingBox = utility.get_bounding_box(
            self.Printer, octoprint_printer_profile)
        self.IsTestMode = self.Settings.current_debug_profile().is_test_mode

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
        self.ZLift = 0
        self.RetractedLength = 0

    def reset(self):
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
        self.ZLift = 0
        self.RetractedLength = 0

    def get_snapshot_position(self, x_pos, y_pos):
        x_path = self.StabilizationPaths["X"]
        x_path.CurrentPosition = x_pos
        y_path = self.StabilizationPaths["Y"]
        y_path.CurrentPosition = y_pos

        coordinates = dict(X=self.get_snapshot_coordinate(x_path),
                           Y=self.get_snapshot_coordinate(y_path))

        if not utility.is_in_bounds(self.BoundingBox, x=coordinates["X"]):

            message = "The snapshot X position ({0}) is out of bounds!".format(
                coordinates["X"])
            self.HasSnapshotPositionErrors = True
            self.Settings.current_debug_profile().log_error(
                "gcode.py - GetSnapshotPosition - {0}".format(message))
            if self.Printer.abort_out_of_bounds:
                coordinates["X"] = None
            else:
                coordinates["X"] = utility.get_closest_in_bounds_position(
                    self.BoundingBox, x=coordinates["X"])["X"]
                message += "  Using nearest in-bound position ({0}).".format(
                    coordinates["X"])
            self.SnapshotPositionErrors += message
        if not utility.is_in_bounds(self.BoundingBox, y=coordinates["Y"]):
            message = "The snapshot Y position ({0}) is out of bounds!".format(
                coordinates["Y"])
            self.HasSnapshotPositionErrors = True
            self.Settings.current_debug_profile().log_error(
                "gcode.py - GetSnapshotPosition - {0}".format(message))
            if self.Printer.abort_out_of_bounds:
                coordinates["Y"] = None
            else:
                coordinates["Y"] = utility.get_closest_in_bounds_position(
                    self.BoundingBox, y=coordinates["Y"])["Y"]
                message += "  Using nearest in-bound position ({0}).".format(
                    coordinates["Y"])
            if len(self.SnapshotPositionErrors) > 0:
                self.SnapshotPositionErrors += "  "
            self.SnapshotPositionErrors += message
        return coordinates

    def get_snapshot_coordinate(self, path):
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
            return self.get_bed_relative_coordinate(path.Axis, coord)

    def get_bed_relative_coordinate(self, axis, coord):
        rel_coordinate = None
        if axis == "X":
            rel_coordinate = self.get_bed_relative_x(coord)
        elif axis == "Y":
            rel_coordinate = self.get_bed_relative_y(coord)
        elif axis == "Z":
            rel_coordinate = self.get_bed_relative_z(coord)

        return rel_coordinate

    def get_bed_relative_x(self, percent):
        return self.get_relative_coordinate(percent, self.BoundingBox["min_x"], self.BoundingBox["max_x"])

    def get_bed_relative_y(self, percent):
        return self.get_relative_coordinate(percent, self.BoundingBox["min_y"], self.BoundingBox["max_y"])

    def get_bed_relative_z(self, percent):
        return self.get_relative_coordinate(percent, self.BoundingBox["min_z"], self.BoundingBox["max_z"])

    @staticmethod
    def get_relative_coordinate(percent, min_value, max_value):
        return ((float(max_value) - float(min_value)) * (percent / 100.0)) + float(min_value)

    def append_feedrate_gcode(self, snapshot_gcode, desired_speed):
        if desired_speed > 0:
            snapshot_gcode.append(self.get_gcode_feedrate(desired_speed))
            self.FCurrent = desired_speed

    def create_snapshot_gcode(
            self, x, y, z, f, is_relative, is_extruder_relative, extruder, z_lift):
        self.reset()
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
        self.ZLift = z_lift
        self.IsRelativeOriginal = is_relative
        self.IsRelativeCurrent = is_relative
        self.IsExtruderRelativeOriginal = is_extruder_relative
        self.IsExtruderRelativeCurrent = is_extruder_relative

        new_snapshot_gcode = SnapshotGcode(self.IsTestMode)
        # retract if necessary Note that if IsRetractedStart is true, that means the printer is now retracted.
        # IsRetracted will be false because we've undone the previous position update.
        if self.Snapshot.retract_before_move and not (extruder.is_retracted() or extruder.is_retracting_start()):
            if not self.IsExtruderRelativeCurrent:
                new_snapshot_gcode.append(
                    self.get_gcode_extruder_relative())
                self.IsExtruderRelativeCurrent = True
            self.append_feedrate_gcode(
                new_snapshot_gcode, self.Printer.retract_speed)
            retracted_length = extruder.length_to_retract()
            if retracted_length > 0:
                new_snapshot_gcode.append(self.get_gcode_retract(retracted_length))
                self.RetractedLength = retracted_length
                self.RetractedBySnapshotStartGcode = True
        # Can we hop or is the print too tall?

        # todo: detect zhop and only zhop if we are not currently hopping.
        can_zhop = self.Printer.z_hop > 0 and utility.is_in_bounds(
            self.BoundingBox, z=z + self.Printer.z_hop)
        # if we can ZHop, do
        if can_zhop and self.ZLift > 0:
            if not self.IsRelativeCurrent:  # must be in relative mode
                new_snapshot_gcode.append(self.get_gcode_axes_relative())
                self.IsRelativeCurrent = True
            self.append_feedrate_gcode(
                new_snapshot_gcode, self.Printer.z_hop_speed)
            new_snapshot_gcode.append(self.get_gcode_z_lift_relative(self.ZLift))
            self.ZhopBySnapshotStartGcode = True

        # Wait for current moves to finish before requesting the startgcodeposition
        # newSnapshotGcode.Append(self.GetWaitForCurrentMovesToFinishGcode())

        # Get the final position after the saved command.  When we get this position we'll know it's time to resume
        # the print. newSnapshotGcode.Append(self.GetPositionGcode()) Log the commands
        # self.Settings.CurrentDebugProfile().LogSnapshotGcode("Snapshot Start Gcode") for str in
        # newSnapshotGcode.GcodeCommands: self.Settings.CurrentDebugProfile().LogSnapshotGcode("    {0}".format(str))

        # End start gcode
        # Create code to move from the current extruder position to the snapshot position
        # get the X and Y coordinates of the snapshot
        snapshot_position = self.get_snapshot_position(x, y)
        new_snapshot_gcode.X = snapshot_position["X"]
        new_snapshot_gcode.Y = snapshot_position["Y"]

        if new_snapshot_gcode.X is None or new_snapshot_gcode.Y is None:
            # either x or y is out of bounds.
            return None

        # Move back to the snapshot position - make sure we're in absolute mode for this
        if self.IsRelativeCurrent:  # must be in absolute mode
            new_snapshot_gcode.append(self.get_gcode_axes_absolute())
            self.IsRelativeCurrent = False

        # speed change - Set to movement speed IF we have specified one

        self.append_feedrate_gcode(new_snapshot_gcode, self.Printer.movement_speed)

        # Move to Snapshot Position
        new_snapshot_gcode.append(self.get_gcode_travel(
            new_snapshot_gcode.X, new_snapshot_gcode.Y))

        # mark the position of the snapshot in the new gcode
        new_snapshot_gcode.set_snapshot_index()

        # create return gcode
        # record our previous position for posterity
        new_snapshot_gcode.ReturnX = x
        new_snapshot_gcode.ReturnY = y
        new_snapshot_gcode.ReturnZ = z

        # Move back to previous position - make sure we're in absolute mode for this (hint: we already are right now)
        if x is not None and y is not None:
            new_snapshot_gcode.append(self.get_gcode_travel(x, y))

        # If we zhopped in the beginning, lower z
        if self.ZhopBySnapshotStartGcode:
            if not self.IsRelativeCurrent:
                new_snapshot_gcode.append(self.get_gcode_axes_relative())
                self.IsRelativeCurrent = True
            self.append_feedrate_gcode(
                new_snapshot_gcode, self.Printer.z_hop_speed)
            new_snapshot_gcode.append(self.get_gocde_z_lower_relative(self.ZLift))

        # detract
        if self.RetractedBySnapshotStartGcode:
            if not self.IsExtruderRelativeCurrent:
                new_snapshot_gcode.append(self.get_gcode_extruder_relative())
                self.IsExtruderRelativeCurrent = True
            self.append_feedrate_gcode(
                new_snapshot_gcode, self.Printer.detract_speed)
            if self.RetractedLength > 0:
                new_snapshot_gcode.append(
                    self.get_gcode_detract(self.RetractedLength))

        # reset the coordinate systems for the extruder and axis
        if self.IsRelativeOriginal != self.IsRelativeCurrent:
            if self.IsRelativeCurrent:
                new_snapshot_gcode.append(self.get_gcode_axes_absolute())
            else:
                new_snapshot_gcode.append(self.get_gcode_axes_relative())
            self.IsRelativeCurrent = self.IsRelativeOriginal

        if self.IsExtruderRelativeOriginal != self.IsExtruderRelativeCurrent:
            if self.IsExtruderRelativeOriginal:
                new_snapshot_gcode.append(
                    self.get_gcode_extruder_relative())
            else:
                new_snapshot_gcode.append(
                    self.get_gcode_extruder_absolute())

        # Make sure we return to the original feedrate
        self.append_feedrate_gcode(new_snapshot_gcode, self.FOriginal)

        self.Settings.current_debug_profile().log_snapshot_gcode(
            "Snapshot Gcode - SnapshotCommandIndex:{0}, EndIndex{1}, Gcode:".format(new_snapshot_gcode.SnapshotIndex,
                                                                                    new_snapshot_gcode.end_index()))
        for gcode in new_snapshot_gcode.GcodeCommands:
            self.Settings.current_debug_profile().log_snapshot_gcode("    {0}".format(gcode))

        self.Settings.current_debug_profile().log_snapshot_position(
            "Snapshot Position: (x:{0:f},y:{1:f})".format(new_snapshot_gcode.X, new_snapshot_gcode.Y))
        self.Settings.current_debug_profile().log_snapshot_return_position(
            "Return Position: (x:{0:f},y:{1:f})".format(new_snapshot_gcode.ReturnX, new_snapshot_gcode.ReturnY))

        return new_snapshot_gcode

    @staticmethod
    def get_gcode_extruder_relative():
        return "M83"

    @staticmethod
    def get_gcode_extruder_absolute():
        return "M82"

    @staticmethod
    def get_gcode_axes_absolute():
        return "G90"

    @staticmethod
    def get_gcode_axes_relative():
        return "G91"

    @staticmethod
    def get_gcode_delay(delay):
        return "G4 P{0:d}".format(delay)

    @staticmethod
    def get_gcode_travel(x, y):
        return "G1 X{0:.3f} Y{1:.3f}".format(x, y)

    @staticmethod
    def get_gcode_z_lift_relative(distance):
        return "G1 Z{0:.3f}".format(distance)

    @staticmethod
    def get_gocde_z_lower_relative(distance):
        return "G1 Z{0:.3f}".format(-1.0 * distance)

    @staticmethod
    def get_gcode_retract(distance):
        return "G1 E{0:.3f}".format(-1 * distance)

    @staticmethod
    def get_gcode_detract(distance):
        return "G1 E{0:.3f}".format(distance)

    @staticmethod
    def get_gcode_reset_line(line_number):
        return "M110 N{0:d}".format(line_number)

    @staticmethod
    def get_gcode_wait_until_finished():
        return "M400"

    @staticmethod
    def get_gcode_current_position():
        return "M114"

    @staticmethod
    def get_gcode_feedrate(f):
        return "G1 F{0}".format(int(f))
