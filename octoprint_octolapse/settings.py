# coding=utf-8

# This file is subject to the terms and conditions defined in
# file called 'LICENSE', which is part of this source code package.

import logging
import math
import os
import sys
import time
import uuid
from datetime import datetime
from octoprint.plugin import PluginSettings
from pprint import pprint

import octoprint_octolapse.utility as utility

PROFILE_SNAPSHOT_GCODE_TYPE = "gcode"


class Printer(object):

    def __init__(
        self, printer=None, name="New Printer",
        guid=None, retract_length=2.0, retract_speed=4000,
        detract_speed=3000, movement_speed=6000, z_hop=0.5,
        z_hop_speed=6000, snapshot_command="snap"):
        self.guid = guid if guid else str(uuid.uuid4())
        self.name = name
        self.description = ""
        self.retract_length = 2.0
        self.retract_speed = 6000
        self.detract_speed = 3000
        self.movement_speed = 6000
        self.z_hop = .5
        self.z_hop_speed = 6000
        self.retract_speed = 4000
        self.snapshot_command = "snap"
        self.printer_position_confirmation_tolerance = 0.01
        self.auto_detect_position = True
        self.origin_x = None
        self.origin_y = None
        self.origin_z = None
        self.abort_out_of_bounds = True
        self.override_octoprint_print_volume = False
        self.min_x = 0.0
        self.max_x = 0.0
        self.min_y = 0.0
        self.max_y = 0.0
        self.min_z = 0.0
        self.max_z = 0.0
        self.auto_position_detection_commands = ""
        self.priming_height = 0
        self.e_axis_default_mode = 'require-explicit'  # other values are 'relative' and 'absolute'
        self.g90_influences_extruder = 'use-octoprint-settings'  # other values are 'true' and 'false'
        self.xyz_axes_default_mode = 'require-explicit'  # other values are 'relative' and 'absolute'

        if printer is not None:
            if isinstance(printer, Printer):
                self.guid = printer.guid
                self.name = printer.name
                self.description = printer.description
                self.retract_length = printer.retract_length
                self.retract_speed = printer.retract_speed
                self.detract_speed = printer.detract_speed
                self.movement_speed = printer.movement_speed
                self.z_hop = printer.z_hop
                self.z_hop_speed = printer.z_hop_speed
                self.snapshot_command = printer.snapshot_command
                self.printer_position_confirmation_tolerance = printer.printer_position_confirmation_tolerance
                self.auto_detect_position = printer.auto_detect_position
                self.auto_position_detection_commands = printer.auto_position_detection_commands
                self.origin_x = printer.origin_x
                self.origin_y = printer.origin_y
                self.origin_z = printer.origin_z
                self.abort_out_of_bounds = printer.abort_out_of_bounds
                self.override_octoprint_print_volume = printer.override_octoprint_print_volume
                self.min_x = printer.min_x
                self.max_x = printer.max_x
                self.min_y = printer.min_y
                self.max_y = printer.max_y
                self.min_z = printer.min_z
                self.max_z = printer.max_z
                self.priming_height = printer.priming_height
                self.e_axis_default_mode = printer.e_axis_default_mode
                self.g90_influences_extruder = printer.g90_influences_extruder
                self.xyz_axes_default_mode = printer.xyz_axes_default_mode
            else:
                self.Update(printer)

    def Update(self, changes):
        if "guid" in changes.keys():
            self.guid = utility.get_string(changes["guid"], self.guid)
        if "name" in changes.keys():
            self.name = utility.get_string(changes["name"], self.name)
        if "description" in changes.keys():
            self.description = utility.get_string(
                changes["description"], self.description)
        if "retract_length" in changes.keys():
            self.retract_length = utility.get_float(
                changes["retract_length"], self.retract_length)
        if "retract_speed" in changes.keys():
            self.retract_speed = utility.get_int(
                changes["retract_speed"], self.retract_speed)
        if "detract_speed" in changes.keys():
            self.detract_speed = utility.get_int(
                changes["detract_speed"], self.detract_speed)
        if "movement_speed" in changes.keys():
            self.movement_speed = utility.get_int(
                changes["movement_speed"], self.movement_speed)
        if "snapshot_command" in changes.keys():
            self.snapshot_command = utility.get_string(
                changes["snapshot_command"], self.snapshot_command)
        if "z_hop" in changes.keys():
            self.z_hop = utility.get_float(changes["z_hop"], self.z_hop)
        if "z_hop_speed" in changes.keys():
            self.z_hop_speed = utility.get_int(
                changes["z_hop_speed"], self.z_hop_speed)
        if "printer_position_confirmation_tolerance" in changes.keys():
            self.printer_position_confirmation_tolerance = utility.get_float(
                changes["printer_position_confirmation_tolerance"], self.printer_position_confirmation_tolerance)

        if "auto_position_detection_commands" in changes.keys():
            self.auto_position_detection_commands = utility.get_string(
                changes["auto_position_detection_commands"], self.auto_position_detection_commands)
        if "auto_detect_position" in changes.keys():
            self.auto_detect_position = utility.get_bool(
                changes["auto_detect_position"], self.auto_detect_position)
        if "origin_x" in changes.keys():
            self.origin_x = utility.get_nullable_float(
                changes["origin_x"], self.origin_x)
        if "origin_y" in changes.keys():
            self.origin_y = utility.get_nullable_float(
                changes["origin_y"], self.origin_y)
        if "origin_z" in changes.keys():
            self.origin_z = utility.get_nullable_float(
                changes["origin_z"], self.origin_z)
        if "abort_out_of_bounds" in changes.keys():
            self.abort_out_of_bounds = utility.get_bool(
                changes["abort_out_of_bounds"], self.abort_out_of_bounds)
        if "override_octoprint_print_volume" in changes.keys():
            self.override_octoprint_print_volume = utility.get_bool(
                changes["override_octoprint_print_volume"], self.override_octoprint_print_volume)

        if "min_x" in changes.keys():
            self.min_x = utility.get_float(changes["min_x"], self.min_x)
        if "max_x" in changes.keys():
            self.max_x = utility.get_float(changes["max_x"], self.max_x)
        if "min_y" in changes.keys():
            self.min_y = utility.get_float(changes["min_y"], self.min_y)
        if "max_y" in changes.keys():
            self.max_y = utility.get_float(changes["max_y"], self.max_y)
        if "min_z" in changes.keys():
            self.min_z = utility.get_float(changes["min_z"], self.min_z)
        if "max_z" in changes.keys():
            self.max_z = utility.get_float(changes["max_z"], self.max_z)
        if "priming_height" in changes.keys():
            self.priming_height = utility.get_float(changes["priming_height"], self.priming_height)
        if "e_axis_default_mode" in changes.keys():
            self.e_axis_default_mode = utility.get_string(
                changes["e_axis_default_mode"], self.e_axis_default_mode)
        if "g90_influences_extruder" in changes.keys():
            self.g90_influences_extruder = utility.get_string(
                changes["g90_influences_extruder"], self.g90_influences_extruder)
        if "xyz_axes_default_mode" in changes.keys():
            self.xyz_axes_default_mode = utility.get_string(
                changes["xyz_axes_default_mode"], self.xyz_axes_default_mode)

    def ToDict(self):
        return {
            'name': self.name,
            'description': self.description,
            'guid': self.guid,
            'retract_length': self.retract_length,
            'retract_speed': self.retract_speed,
            'detract_speed': self.detract_speed,
            'movement_speed': self.movement_speed,
            'z_hop': self.z_hop,
            'z_hop_speed': self.z_hop_speed,
            'snapshot_command': self.snapshot_command,
            'printer_position_confirmation_tolerance': self.printer_position_confirmation_tolerance,
            'auto_detect_position': self.auto_detect_position,
            'auto_position_detection_commands': self.auto_position_detection_commands,
            'origin_x': self.origin_x,
            'origin_y': self.origin_y,
            'origin_z': self.origin_z,
            'abort_out_of_bounds': self.abort_out_of_bounds,
            'override_octoprint_print_volume': self.override_octoprint_print_volume,
            'min_x': self.min_x,
            'max_x': self.max_x,
            'min_y': self.min_y,
            'max_y': self.max_y,
            'min_z': self.min_z,
            'max_z': self.max_z,
            'priming_height': self.priming_height,
            'e_axis_default_mode': self.e_axis_default_mode,
            'g90_influences_extruder': self.g90_influences_extruder,
            'xyz_axes_default_mode': self.xyz_axes_default_mode
        }


class StabilizationPath(object):
    def __init__(self):
        self.Axis = ""
        self.Path = []
        self.CoordinateSystem = ""
        self.Index = 0
        self.Loop = True
        self.InvertLoop = True
        self.Increment = 1
        self.CurrentPosition = None
        self.Type = 'disabled'
        self.Options = {}


class Stabilization(object):

    def __init__(self, stabilization=None, guid=None, name="Default Stabilization"):
        self.guid = guid if guid else str(uuid.uuid4())
        self.name = name
        self.description = ""
        self.x_type = "relative"
        self.x_fixed_coordinate = 0.0
        self.x_fixed_path = "0"
        self.x_fixed_path_loop = True
        self.x_fixed_path_invert_loop = True
        self.x_relative = 50.0
        self.x_relative_print = 50.0
        self.x_relative_path = "50.0"
        self.x_relative_path_loop = True
        self.x_relative_path_invert_loop = True
        self.y_type = 'relative'
        self.y_fixed_coordinate = 0.0
        self.y_fixed_path = "0"
        self.y_fixed_path_loop = True
        self.y_fixed_path_invert_loop = True
        self.y_relative = 50.0
        self.y_relative_print = 50.0
        self.y_relative_path = "50"
        self.y_relative_path_loop = True
        self.y_relative_path_invert_loop = True

        if stabilization is not None:
            self.Update(stabilization)

    def Update(self, changes):
        if "guid" in changes.keys():
            self.guid = utility.get_string(changes["guid"], self.guid)
        if "name" in changes.keys():
            self.name = utility.get_string(changes["name"], self.name)
        if "description" in changes.keys():
            self.description = utility.get_string(
                changes["description"], self.description)

        if "x_type" in changes.keys():
            self.x_type = utility.get_string(changes["x_type"], self.x_type)
        if "x_fixed_coordinate" in changes.keys():
            self.x_fixed_coordinate = utility.get_float(
                changes["x_fixed_coordinate"], self.x_fixed_coordinate)
        if "x_fixed_path" in changes.keys():
            self.x_fixed_path = utility.get_string(
                changes["x_fixed_path"], self.x_fixed_path)
        if "x_fixed_path_loop" in changes.keys():
            self.x_fixed_path_loop = utility.get_bool(
                changes["x_fixed_path_loop"], self.x_fixed_path_loop)
        if "x_fixed_path_invert_loop" in changes.keys():
            self.x_fixed_path_invert_loop = utility.get_bool(
                changes["x_fixed_path_invert_loop"], self.x_fixed_path_invert_loop)
        if "x_relative" in changes.keys():
            self.x_relative = utility.get_float(
                changes["x_relative"], self.x_relative)
        if "x_relative_print" in changes.keys():
            self.x_relative_print = utility.get_float(
                changes["x_relative_print"], self.x_relative_print)
        if "x_relative_path" in changes.keys():
            self.x_relative_path = utility.get_string(
                changes["x_relative_path"], self.x_relative_path)
        if "x_relative_path_loop" in changes.keys():
            self.x_relative_path_loop = utility.get_bool(
                changes["x_relative_path_loop"], self.x_relative_path_loop)
        if "x_relative_path_invert_loop" in changes.keys():
            self.x_relative_path_invert_loop = utility.get_bool(
                changes["x_relative_path_invert_loop"], self.x_relative_path_invert_loop)
        if "y_type" in changes.keys():
            self.y_type = utility.get_string(changes["y_type"], self.y_type)
        if "y_fixed_coordinate" in changes.keys():
            self.y_fixed_coordinate = utility.get_float(
                changes["y_fixed_coordinate"], self.y_fixed_coordinate)
        if "y_fixed_path" in changes.keys():
            self.y_fixed_path = utility.get_string(
                changes["y_fixed_path"], self.y_fixed_path)
        if "y_fixed_path_loop" in changes.keys():
            self.y_fixed_path_loop = utility.get_bool(
                changes["y_fixed_path_loop"], self.y_fixed_path_loop)
        if "y_fixed_path_invert_loop" in changes.keys():
            self.y_fixed_path_invert_loop = utility.get_bool(
                changes["y_fixed_path_invert_loop"], self.y_fixed_path_invert_loop)
        if "y_relative" in changes.keys():
            self.y_relative = utility.get_float(
                changes["y_relative"], self.y_relative)
        if "y_relative_print" in changes.keys():
            self.y_relative_print = utility.get_float(
                changes["y_relative_print"], self.y_relative_print)
        if "y_relative_path" in changes.keys():
            self.y_relative_path = utility.get_string(
                changes["y_relative_path"], self.y_relative_path)
        if "y_relative_path_loop" in changes.keys():
            self.y_relative_path_loop = utility.get_bool(
                changes["y_relative_path_loop"], self.y_relative_path_loop)
        if "y_relative_path_invert_loop" in changes.keys():
            self.y_relative_path_invert_loop = utility.get_bool(
                changes["y_relative_path_invert_loop"], self.y_relative_path_invert_loop)

    def ToDict(self):
        return {
            'guid': self.guid,
            'name': self.name,
            'description': self.description,
            'x_type': self.x_type,
            'x_fixed_coordinate': self.x_fixed_coordinate,
            'x_fixed_path': self.x_fixed_path,
            'x_fixed_path_loop': self.x_fixed_path_loop,
            'x_fixed_path_invert_loop': self.x_fixed_path_invert_loop,
            'x_relative': self.x_relative,
            'x_relative_print': self.x_relative_print,
            'x_relative_path': self.x_relative_path,
            'x_relative_path_loop': self.x_relative_path_loop,
            'x_relative_path_invert_loop': self.x_relative_path_invert_loop,
            'y_type': self.y_type,
            'y_fixed_coordinate': self.y_fixed_coordinate,
            'y_fixed_path': self.y_fixed_path,
            'y_fixed_path_loop': self.y_fixed_path_loop,
            'y_fixed_path_invert_loop': self.y_fixed_path_invert_loop,
            'y_relative': self.y_relative,
            'y_relative_print': self.y_relative_print,
            'y_relative_path': self.y_relative_path,
            'y_relative_path_loop': self.y_relative_path_loop,
            'y_relative_path_invert_loop': self.y_relative_path_invert_loop
        }

    def GetStabilizationPaths(self):
        xStabilizationPath = StabilizationPath()
        xStabilizationPath.Axis = "X"
        xStabilizationPath.Type = self.x_type
        if self.x_type == 'fixed_coordinate':
            xStabilizationPath.Path.append(self.x_fixed_coordinate)
            xStabilizationPath.CoordinateSystem = 'absolute'
        elif self.x_type == 'relative':
            xStabilizationPath.Path.append(self.x_relative)
            xStabilizationPath.CoordinateSystem = 'bed_relative'
        elif self.x_type == 'fixed_path':
            xStabilizationPath.Path = self.ParseCSVPath(self.x_fixed_path)
            xStabilizationPath.CoordinateSystem = 'absolute'
            xStabilizationPath.Loop = self.x_fixed_path_loop
            xStabilizationPath.InvertLoop = self.x_fixed_path_invert_loop
        elif self.x_type == 'relative_path':
            xStabilizationPath.Path = self.ParseCSVPath(self.x_relative_path)
            xStabilizationPath.CoordinateSystem = 'bed_relative'
            xStabilizationPath.Loop = self.x_relative_path_loop
            xStabilizationPath.InvertLoop = self.x_relative_path_invert_loop

        yStabilizationPath = StabilizationPath()
        yStabilizationPath.Axis = "Y"
        yStabilizationPath.Type = self.y_type
        if self.y_type == 'fixed_coordinate':
            yStabilizationPath.Path.append(self.y_fixed_coordinate)
            yStabilizationPath.CoordinateSystem = 'absolute'
        elif self.y_type == 'relative':
            yStabilizationPath.Path.append(self.y_relative)
            yStabilizationPath.CoordinateSystem = 'bed_relative'
        elif self.y_type == 'fixed_path':
            yStabilizationPath.Path = self.ParseCSVPath(self.y_fixed_path)
            yStabilizationPath.CoordinateSystem = 'absolute'
            yStabilizationPath.Loop = self.y_fixed_path_loop
            yStabilizationPath.InvertLoop = self.y_fixed_path_invert_loop
        elif self.y_type == 'relative_path':
            yStabilizationPath.Path = self.ParseCSVPath(self.y_relative_path)
            yStabilizationPath.CoordinateSystem = 'bed_relative'
            yStabilizationPath.Loop = self.y_relative_path_loop
            yStabilizationPath.InvertLoop = self.y_relative_path_invert_loop

        return dict(
            X=xStabilizationPath,
            Y=yStabilizationPath
        )

    def ParseCSVPath(self, pathCsv):
        """Converts a list of floats separated by commas into an array of floats."""
        path = []
        items = pathCsv.split(',')
        for item in items:
            item = item.strip()
            if len(item) > 0:
                path.append(float(item))
        return path


class SnapshotPositionRestrictions(object):
    def __init__(self, type, shape, x, y, x2=None, y2=None, r=None):

        self.Type = type.lower()
        if self.Type not in ["forbidden", "required"]:
            raise TypeError("SnapshotPosition type must be 'forbidden' or 'required'")

        self.Shape = shape.lower()

        if self.Shape not in ["rect", "circle"]:
            raise TypeError("SnapshotPosition shape must be 'rect' or 'circle'")
        if x is None or y is None:
            raise TypeError(
                "SnapshotPosition requires that x and y are not None")
        if self.Shape == 'rect' and (x2 is None or y2 is None):
            raise TypeError(
                "SnapshotPosition shape=rect requires that x2 and y2 are not None")
        if self.Shape == 'circle' and r is None:
            raise TypeError(
                "SnapshotPosition shape=circle requires that r is not None")

        self.Type = type
        self.Shape = shape
        self.X = float(x)
        self.Y = float(y)
        self.X2 = float(x2)
        self.Y2 = float(y2)
        self.R = float(r)

    def ToDict(self):
        return {
            'Type': self.Type,
            'Shape': self.Shape,
            'X': self.X,
            'Y': self.Y,
            'X2': self.X2,
            'Y2': self.Y2,
            'R': self.R
        }

    def IsInPosition(self, x, y):
        if x is None or y is None:
            return False
        isInPosition = None
        if self.Shape == 'rect':
            isInPosition = x >= self.X and x <= self.X2 and y >= self.Y and y <= self.Y2
        elif self.Shape == 'circle':
            isInPosition = math.pow(x - self.X, 2) + math.pow(y - self.Y, 2) <= math.pow(self.R, 2)
        else:
            raise TypeError("SnapshotPosition shape must be 'rect' or 'circle'.")

        return isInPosition


class Snapshot(object):
    # globals
    # Extruder Trigger Options
    ExtruderTriggerIgnoreValue = ""
    ExtruderTriggerRequiredValue = "trigger_on"
    ExtruderTriggerForbiddenValue = "forbidden"
    ExtruderTriggerOptions = [
        dict(value=ExtruderTriggerIgnoreValue, name='Ignore', visible=True),
        dict(value=ExtruderTriggerRequiredValue, name='Trigger', visible=True),
        dict(value=ExtruderTriggerForbiddenValue, name='Forbidden', visible=True)
    ]

    def __init__(self, snapshot=None, guid=None, name="Default Snapshot"):
        self.guid = guid if guid else str(uuid.uuid4())
        self.name = name
        self.description = ""
        # Initialize defaults
        # Gcode Trigger
        self.gcode_trigger_enabled = False
        self.gcode_trigger_require_zhop = False
        self.gcode_trigger_on_extruding_start = None
        self.gcode_trigger_on_extruding = None
        self.gcode_trigger_on_primed = None
        self.gcode_trigger_on_retracting_start = None
        self.gcode_trigger_on_retracting = None
        self.gcode_trigger_on_partially_retracted = None
        self.gcode_trigger_on_retracted = None
        self.gcode_trigger_on_detracting_start = None
        self.gcode_trigger_on_detracting = None
        self.gcode_trigger_on_detracted = None
        self.gcode_trigger_position_restrictions = []
        # Timer Trigger
        self.timer_trigger_enabled = False
        self.timer_trigger_seconds = 30
        self.timer_trigger_require_zhop = False
        self.timer_trigger_on_extruding_start = True
        self.timer_trigger_on_extruding = False
        self.timer_trigger_on_primed = True
        self.timer_trigger_on_retracting_start = False
        self.timer_trigger_on_retracting = False
        self.timer_trigger_on_partially_retracted = False
        self.timer_trigger_on_retracted = True
        self.timer_trigger_on_detracting_start = True
        self.timer_trigger_on_detracting = False
        self.timer_trigger_on_detracted = False
        self.timer_trigger_position_restrictions = []
        # Layer Trigger
        self.layer_trigger_enabled = True
        self.layer_trigger_height = 0.0
        self.layer_trigger_require_zhop = False
        self.layer_trigger_on_extruding_start = True
        self.layer_trigger_on_extruding = None
        self.layer_trigger_on_primed = True
        self.layer_trigger_on_retracting_start = False
        self.layer_trigger_on_retracting = False
        self.layer_trigger_on_partially_retracted = False
        self.layer_trigger_on_retracted = True
        self.layer_trigger_on_detracting_start = True
        self.layer_trigger_on_detracting = False
        self.layer_trigger_on_detracted = False
        self.layer_trigger_position_restrictions = []
        # other settings

        self.retract_before_move = True

        self.cleanup_after_render_complete = True
        self.cleanup_after_render_fail = False

        if snapshot is not None:
            if isinstance(snapshot, Snapshot):
                self.name = snapshot.name
                self.description = snapshot.description
                self.guid = snapshot.guid
                # gcode trigger members
                self.gcode_trigger_enabled = snapshot.gcode_trigger_enabled
                self.gcode_trigger_require_zhop = snapshot.gcode_trigger_require_zhop
                self.gcode_trigger_on_extruding_start = snapshot.gcode_trigger_on_extruding_start
                self.gcode_trigger_on_extruding = snapshot.gcode_trigger_on_extruding
                self.gcode_trigger_on_primed = snapshot.gcode_trigger_on_primed
                self.gcode_trigger_on_retracting_start = snapshot.gcode_trigger_on_retracting_start
                self.gcode_trigger_on_retracting = snapshot.gcode_trigger_on_retracting
                self.gcode_trigger_on_partially_retracted = snapshot.gcode_trigger_on_partially_retracted
                self.gcode_trigger_on_retracted = snapshot.gcode_trigger_on_retracted
                self.gcode_trigger_on_detracting_start = snapshot.gcode_trigger_on_detracting_start
                self.gcode_trigger_on_detracting = snapshot.gcode_trigger_on_detracting
                self.gcode_trigger_on_detracted = snapshot.gcode_trigger_on_detracted
                self.gcode_trigger_position_restrictions = snapshot.gcode_trigger_position_restrictions
                # timer trigger members
                self.timer_trigger_enabled = snapshot.timer_trigger_enabled
                self.timer_trigger_require_zhop = snapshot.timer_trigger_require_zhop
                self.timer_trigger_seconds = snapshot.timer_trigger_seconds
                self.timer_trigger_on_extruding_start = snapshot.timer_trigger_on_extruding_start
                self.timer_trigger_on_extruding = snapshot.timer_trigger_on_extruding
                self.timer_trigger_on_primed = snapshot.timer_trigger_on_primed
                self.timer_trigger_on_retracting_start = snapshot.timer_trigger_on_retracting_start
                self.timer_trigger_on_retracting = snapshot.timer_trigger_on_retracting
                self.timer_trigger_on_retracted = snapshot.timer_trigger_on_retracted
                self.timer_trigger_on_detracting_start = snapshot.timer_trigger_on_detracting_start
                self.timer_trigger_on_detracting = snapshot.timer_trigger_on_detracting
                self.timer_trigger_on_detracted = snapshot.timer_trigger_on_detracted
                self.timer_trigger_position_restrictions = snapshot.timer_trigger_position_restrictions
                # layer trigger members
                self.layer_trigger_enabled = snapshot.layer_trigger_enabled
                self.layer_trigger_height = snapshot.layer_trigger_height
                self.layer_trigger_require_zhop = snapshot.layer_trigger_require_zhop
                self.layer_trigger_on_extruding_start = snapshot.layer_trigger_on_extruding_start
                self.layer_trigger_on_extruding = snapshot.layer_trigger_on_extruding
                self.layer_trigger_on_primed = snapshot.layer_trigger_on_primed
                self.layer_trigger_on_retracting_start = snapshot.layer_trigger_on_retracting_start
                self.layer_trigger_on_retracting = snapshot.layer_trigger_on_retracting
                self.layer_trigger_on_partially_retracted = snapshot.layer_trigger_on_partially_retracted
                self.layer_trigger_on_retracted = snapshot.layer_trigger_on_retracted
                self.layer_trigger_on_detracting_start = snapshot.layer_trigger_on_detracting_start
                self.layer_trigger_on_detracting = snapshot.layer_trigger_on_detracting
                self.layer_trigger_on_detracted = snapshot.layer_trigger_on_detracted
                self.layer_trigger_position_restrictions = snapshot.layer_trigger_position_restrictions

                self.cleanup_after_render_complete = snapshot.cleanup_after_render_complete
                self.cleanup_after_render_fail = snapshot.cleanup_after_render_fail
                self.retract_before_move = snapshot.retract_before_move
            else:
                self.Update(snapshot)

    def Update(self, changes):
        # Initialize all values according to the provided changes, use defaults if
        # the values are null or incorrectly formatted
        if "guid" in changes.keys():
            self.guid = utility.get_string(changes["guid"], self.guid)
        if "name" in changes.keys():
            self.name = utility.get_string(changes["name"], self.name)
        if "description" in changes.keys():
            self.description = utility.get_string(
                changes["description"], self.description)
        # gcode trigger members
        if "gcode_trigger_enabled" in changes.keys():
            self.gcode_trigger_enabled = utility.get_bool(
                changes["gcode_trigger_enabled"], self.gcode_trigger_enabled)
        if "gcode_trigger_require_zhop" in changes.keys():
            self.gcode_trigger_require_zhop = utility.get_bool(
                changes["gcode_trigger_require_zhop"], self.gcode_trigger_require_zhop)
        if "gcode_trigger_on_extruding_start" in changes.keys():
            self.gcode_trigger_on_extruding_start = self.GetExtruderTriggerValue(
                changes["gcode_trigger_on_extruding_start"])
        if "gcode_trigger_on_extruding" in changes.keys():
            self.gcode_trigger_on_extruding = self.GetExtruderTriggerValue(
                changes["gcode_trigger_on_extruding"])
        if "gcode_trigger_on_primed" in changes.keys():
            self.gcode_trigger_on_primed = self.GetExtruderTriggerValue(
                changes["gcode_trigger_on_primed"])
        if "gcode_trigger_on_retracting_start" in changes.keys():
            self.gcode_trigger_on_retracting_start = self.GetExtruderTriggerValue(
                changes["gcode_trigger_on_retracting_start"])
        if "gcode_trigger_on_retracting" in changes.keys():
            self.gcode_trigger_on_retracting = self.GetExtruderTriggerValue(
                changes["gcode_trigger_on_retracting"])
        if "gcode_trigger_on_partially_retracted" in changes.keys():
            self.gcode_trigger_on_partially_retracted = self.GetExtruderTriggerValue(
                changes["gcode_trigger_on_partially_retracted"])
        if "gcode_trigger_on_retracted" in changes.keys():
            self.gcode_trigger_on_retracted = self.GetExtruderTriggerValue(
                changes["gcode_trigger_on_retracted"])
        if "gcode_trigger_on_detracting_start" in changes.keys():
            self.gcode_trigger_on_detracting_start = self.GetExtruderTriggerValue(
                changes["gcode_trigger_on_detracting_start"])
        if "gcode_trigger_on_detracting" in changes.keys():
            self.gcode_trigger_on_detracting = self.GetExtruderTriggerValue(
                changes["gcode_trigger_on_detracting"])
        if "gcode_trigger_on_detracted" in changes.keys():
            self.gcode_trigger_on_detracted = self.GetExtruderTriggerValue(
                changes["gcode_trigger_on_detracted"])
        if "gcode_trigger_position_restrictions" in changes.keys():
            self.gcode_trigger_position_restrictions = self.GetTriggerPositionRestrictions(
                changes["gcode_trigger_position_restrictions"])
        # timer trigger members
        if "timer_trigger_enabled" in changes.keys():
            self.timer_trigger_enabled = utility.get_bool(
                changes["timer_trigger_enabled"], self.timer_trigger_enabled)
        if "timer_trigger_require_zhop" in changes.keys():
            self.timer_trigger_require_zhop = utility.get_bool(
                changes["timer_trigger_require_zhop"], self.timer_trigger_require_zhop)
        if "timer_trigger_seconds" in changes.keys():
            self.timer_trigger_seconds = utility.get_int(
                changes["timer_trigger_seconds"], self.timer_trigger_seconds)
        if "timer_trigger_on_extruding_start" in changes.keys():
            self.timer_trigger_on_extruding_start = self.GetExtruderTriggerValue(
                changes["timer_trigger_on_extruding_start"])
        if "timer_trigger_on_extruding" in changes.keys():
            self.timer_trigger_on_extruding = self.GetExtruderTriggerValue(
                changes["timer_trigger_on_extruding"])
        if "timer_trigger_on_primed" in changes.keys():
            self.timer_trigger_on_primed = self.GetExtruderTriggerValue(
                changes["timer_trigger_on_primed"])
        if "timer_trigger_on_retracting_start" in changes.keys():
            self.timer_trigger_on_retracting_start = self.GetExtruderTriggerValue(
                changes["timer_trigger_on_retracting_start"])
        if "timer_trigger_on_retracting" in changes.keys():
            self.timer_trigger_on_retracting = self.GetExtruderTriggerValue(
                changes["timer_trigger_on_retracting"])
        if "timer_trigger_on_partially_retracted" in changes.keys():
            self.timer_trigger_on_partially_retracted = self.GetExtruderTriggerValue(
                changes["timer_trigger_on_partially_retracted"])
        if "timer_trigger_on_retracted" in changes.keys():
            self.timer_trigger_on_retracted = self.GetExtruderTriggerValue(
                changes["timer_trigger_on_retracted"])
        if "timer_trigger_on_detracting_start" in changes.keys():
            self.timer_trigger_on_detracting_start = self.GetExtruderTriggerValue(
                changes["timer_trigger_on_detracting_start"])
        if "timer_trigger_on_detracting" in changes.keys():
            self.timer_trigger_on_detracting = self.GetExtruderTriggerValue(
                changes["timer_trigger_on_detracting"])
        if "timer_trigger_on_detracted" in changes.keys():
            self.timer_trigger_on_detracted = self.GetExtruderTriggerValue(
                changes["timer_trigger_on_detracted"])
        if "timer_trigger_position_restrictions" in changes.keys():
            self.timer_trigger_position_restrictions = self.GetTriggerPositionRestrictions(
                changes["timer_trigger_position_restrictions"])
        # layer trigger members
        if "layer_trigger_enabled" in changes.keys():
            self.layer_trigger_enabled = utility.get_bool(
                changes["layer_trigger_enabled"], self.layer_trigger_enabled)
        if "layer_trigger_height" in changes.keys():
            self.layer_trigger_height = utility.get_float(
                changes["layer_trigger_height"], self.layer_trigger_height)
        if "layer_trigger_require_zhop" in changes.keys():
            self.layer_trigger_require_zhop = utility.get_bool(
                changes["layer_trigger_require_zhop"], self.layer_trigger_require_zhop)
        if "layer_trigger_on_extruding_start" in changes.keys():
            self.layer_trigger_on_extruding_start = self.GetExtruderTriggerValue(
                changes["layer_trigger_on_extruding_start"])
        if "layer_trigger_on_extruding" in changes.keys():
            self.layer_trigger_on_extruding = self.GetExtruderTriggerValue(
                changes["layer_trigger_on_extruding"])
        if "layer_trigger_on_primed" in changes.keys():
            self.layer_trigger_on_primed = self.GetExtruderTriggerValue(
                changes["layer_trigger_on_primed"])
        if "layer_trigger_on_retracting_start" in changes.keys():
            self.layer_trigger_on_retracting_start = self.GetExtruderTriggerValue(
                changes["layer_trigger_on_retracting_start"])
        if "layer_trigger_on_retracting" in changes.keys():
            self.layer_trigger_on_retracting = self.GetExtruderTriggerValue(
                changes["layer_trigger_on_retracting"])
        if "layer_trigger_on_partially_retracted" in changes.keys():
            self.layer_trigger_on_partially_retracted = self.GetExtruderTriggerValue(
                changes["layer_trigger_on_partially_retracted"])
        if "layer_trigger_on_retracted" in changes.keys():
            self.layer_trigger_on_retracted = self.GetExtruderTriggerValue(
                changes["layer_trigger_on_retracted"])
        if "layer_trigger_on_detracting_start" in changes.keys():
            self.layer_trigger_on_detracting_start = self.GetExtruderTriggerValue(
                changes["layer_trigger_on_detracting_start"])
        if "layer_trigger_on_detracting" in changes.keys():
            self.layer_trigger_on_detracting = self.GetExtruderTriggerValue(
                changes["layer_trigger_on_detracting"])
        if "layer_trigger_on_detracted" in changes.keys():
            self.layer_trigger_on_detracted = self.GetExtruderTriggerValue(
                changes["layer_trigger_on_detracted"])
        if "layer_trigger_position_restrictions" in changes.keys():
            self.layer_trigger_position_restrictions = self.GetTriggerPositionRestrictions(
                changes["layer_trigger_position_restrictions"])
        # other settings
        if "retract_before_move" in changes.keys():
            self.retract_before_move = utility.get_bool(
                changes["retract_before_move"], self.retract_before_move)
        if "cleanup_after_render_complete" in changes.keys():
            self.cleanup_after_render_complete = utility.get_bool(
                changes["cleanup_after_render_complete"], self.cleanup_after_render_complete)
        if "cleanup_after_render_fail" in changes.keys():
            self.cleanup_after_render_fail = utility.get_bool(
                changes["cleanup_after_render_fail"], self.cleanup_after_render_fail)

    def GetExtruderTriggerValueString(self, value):
        if value is None:
            return self.ExtruderTriggerIgnoreValue
        elif value:
            return self.ExtruderTriggerRequiredValue
        elif not value:
            return self.ExtruderTriggerForbiddenValue

    def GetExtruderTriggerValue(self, value):
        if isinstance(value, basestring):
            if value is None:
                return None
            elif value.lower() == self.ExtruderTriggerRequiredValue:
                return True
            elif value.lower() == self.ExtruderTriggerForbiddenValue:
                return False
            else:
                return None
        else:
            return bool(value)

    def GetTriggerPositionRestrictions(self, value):
        restrictions = []
        for restriction in value:
            restrictions.append(
                SnapshotPositionRestrictions(
                    restriction["Type"], restriction["Shape"],
                    restriction["X"], restriction["Y"],
                    restriction["X2"], restriction["Y2"],
                    restriction["R"]
                )
            )
        return restrictions

    def GetTriggerPositionRestrictionsValueString(self, values):
        restrictions = []
        for restriction in values:
            restrictions.append(restriction.ToDict())
        return restrictions

    def ToDict(self):
        GETVR = self.GetExtruderTriggerValueString
        return {
            'guid': self.guid,
            'name': self.name,
            'description': self.description,
            # Gcode Trigger
            'gcode_trigger_enabled': self.gcode_trigger_enabled,
            'gcode_trigger_require_zhop': self.gcode_trigger_require_zhop,
            'gcode_trigger_on_extruding_start': GETVR(self.gcode_trigger_on_extruding_start),
            'gcode_trigger_on_extruding': GETVR(self.gcode_trigger_on_extruding),
            'gcode_trigger_on_primed': GETVR(self.gcode_trigger_on_primed),
            'gcode_trigger_on_retracting_start': GETVR(self.gcode_trigger_on_retracting_start),
            'gcode_trigger_on_retracting': GETVR(self.gcode_trigger_on_retracting),
            'gcode_trigger_on_partially_retracted': GETVR(self.gcode_trigger_on_partially_retracted),
            'gcode_trigger_on_retracted': GETVR(self.gcode_trigger_on_retracted),
            'gcode_trigger_on_detracting_start': GETVR(self.gcode_trigger_on_detracting_start),
            'gcode_trigger_on_detracting': GETVR(self.gcode_trigger_on_detracting),
            'gcode_trigger_on_detracted': GETVR(self.gcode_trigger_on_detracted),
            'gcode_trigger_position_restrictions': self.GetTriggerPositionRestrictionsValueString(
                self.gcode_trigger_position_restrictions),
            # Timer Trigger
            'timer_trigger_enabled': self.timer_trigger_enabled,
            'timer_trigger_require_zhop': self.timer_trigger_require_zhop,
            'timer_trigger_seconds': self.timer_trigger_seconds,
            'timer_trigger_on_extruding_start': GETVR(self.timer_trigger_on_extruding_start),
            'timer_trigger_on_extruding': GETVR(self.timer_trigger_on_extruding),
            'timer_trigger_on_primed': GETVR(self.timer_trigger_on_primed),
            'timer_trigger_on_retracting_start': GETVR(self.timer_trigger_on_retracting_start),
            'timer_trigger_on_retracting': GETVR(self.timer_trigger_on_retracting),
            'timer_trigger_on_partially_retracted': GETVR(self.timer_trigger_on_partially_retracted),
            'timer_trigger_on_retracted': GETVR(self.timer_trigger_on_retracted),
            'timer_trigger_on_detracting_start': GETVR(self.timer_trigger_on_detracting_start),
            'timer_trigger_on_detracting': GETVR(self.timer_trigger_on_detracting),
            'timer_trigger_on_detracted': GETVR(self.timer_trigger_on_detracted),
            'timer_trigger_position_restrictions': self.GetTriggerPositionRestrictionsValueString(
                self.timer_trigger_position_restrictions),
            # Layer Trigger
            'layer_trigger_enabled': self.layer_trigger_enabled,
            'layer_trigger_height': self.layer_trigger_height,
            'layer_trigger_require_zhop': self.layer_trigger_require_zhop,
            'layer_trigger_on_extruding_start': GETVR(self.layer_trigger_on_extruding_start),
            'layer_trigger_on_extruding': GETVR(self.layer_trigger_on_extruding),
            'layer_trigger_on_primed': GETVR(self.layer_trigger_on_primed),
            'layer_trigger_on_retracting_start': GETVR(self.layer_trigger_on_retracting_start),
            'layer_trigger_on_retracting': GETVR(self.layer_trigger_on_retracting),
            'layer_trigger_on_partially_retracted': GETVR(self.layer_trigger_on_partially_retracted),
            'layer_trigger_on_retracted': GETVR(self.layer_trigger_on_retracted),
            'layer_trigger_on_detracting_start': GETVR(self.layer_trigger_on_detracting_start),
            'layer_trigger_on_detracting': GETVR(self.layer_trigger_on_detracting),
            'layer_trigger_on_detracted': GETVR(self.layer_trigger_on_detracted),
            'layer_trigger_position_restrictions': self.GetTriggerPositionRestrictionsValueString(
                self.layer_trigger_position_restrictions),

            # Other Settings
            'retract_before_move': self.retract_before_move,
            'cleanup_after_render_complete': self.cleanup_after_render_complete,
            'cleanup_after_render_fail': self.cleanup_after_render_fail,
        }


class Rendering(object):
    def __init__(self, rendering=None, guid=None, name="Default Rendering"):
        self.guid = guid if guid else str(uuid.uuid4())
        self.name = name
        self.description = ""
        self.enabled = True
        self.fps_calculation_type = 'duration'
        self.run_length_seconds = 5
        self.fps = 30
        self.max_fps = 120.0
        self.min_fps = 2.0
        self.output_format = 'mp4'
        self.sync_with_timelapse = True
        self.bitrate = "8000K"
        self.flip_h = False
        self.flip_v = False
        self.rotate_90 = False
        self.watermark = False
        self.post_roll_seconds = 0
        self.pre_roll_seconds = 0
        if not rendering is None:
            if isinstance(rendering, Rendering):
                self.guid = rendering.guid
                self.name = rendering.name
                self.description = rendering.description
                self.enabled = rendering.enabled
                self.fps_calculation_type = rendering.fps_calculation_type
                self.run_length_seconds = rendering.run_length_seconds
                self.fps = rendering.fps
                self.max_fps = rendering.max_fps
                self.min_fps = rendering.min_fps
                self.output_format = rendering.output_format
                self.sync_with_timelapse = rendering.sync_with_timelapse
                self.bitrate = rendering.bitrate
                self.flip_h = rendering.flip_h
                self.flip_v = rendering.flip_v
                self.rotate_90 = rendering.rotate_90
                self.watermark = rendering.watermark
                self.post_roll_seconds = rendering.post_roll_seconds
                self.pre_roll_seconds = rendering.pre_roll_seconds
            else:
                self.Update(rendering)

    def Update(self, changes):
        if "guid" in changes.keys():
            self.guid = utility.get_string(changes["guid"], self.guid)
        if "name" in changes.keys():
            self.name = utility.get_string(changes["name"], self.name)
        if "description" in changes.keys():
            self.description = utility.get_string(
                changes["description"], self.description)
        if "enabled" in changes.keys():
            self.enabled = utility.get_bool(changes["enabled"], self.enabled)
        if "fps_calculation_type" in changes.keys():
            self.fps_calculation_type = changes["fps_calculation_type"]
        if "run_length_seconds" in changes.keys():
            self.run_length_seconds = utility.get_float(
                changes["run_length_seconds"], self.run_length_seconds)
        if "fps" in changes.keys():
            self.fps = utility.get_float(changes["fps"], self.fps)
        if "max_fps" in changes.keys():
            self.max_fps = utility.get_float(changes["max_fps"], self.max_fps)
        if "min_fps" in changes.keys():
            self.min_fps = utility.get_float(changes["min_fps"], self.min_fps)
        if "output_format" in changes.keys():
            self.output_format = utility.get_string(
                changes["output_format"], self.output_format)

        if "sync_with_timelapse" in changes.keys():
            self.sync_with_timelapse = utility.get_bool(
                changes["sync_with_timelapse"], self.sync_with_timelapse)
        if "bitrate" in changes.keys():
            self.bitrate = utility.get_bitrate(changes["bitrate"], self.bitrate)
        if "flip_h" in changes.keys():
            self.flip_h = utility.get_bool(changes["flip_h"], self.flip_h)
        if "flip_v" in changes.keys():
            self.flip_v = utility.get_bool(changes["flip_v"], self.flip_v)
        if "rotate_90" in changes.keys():
            self.rotate_90 = utility.get_bool(
                changes["rotate_90"], self.rotate_90)
        if "watermark" in changes.keys():
            self.watermark = utility.get_bool(
                changes["watermark"], self.watermark)

        if "post_roll_seconds" in changes.keys():
            self.post_roll_seconds = utility.get_float(
                changes["post_roll_seconds"], self.post_roll_seconds)
        if "pre_roll_seconds" in changes.keys():
            self.pre_roll_seconds = utility.get_float(
                changes["pre_roll_seconds"], self.pre_roll_seconds)

    def ToDict(self):
        return {
            'guid': self.guid,
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
            'fps_calculation_type': self.fps_calculation_type,
            'run_length_seconds': self.run_length_seconds,
            'fps': self.fps,
            'max_fps': self.max_fps,
            'min_fps': self.min_fps,
            'output_format': self.output_format,
            'sync_with_timelapse': self.sync_with_timelapse,
            'bitrate': self.bitrate,
            'flip_h': self.flip_h,
            'flip_v': self.flip_v,
            'rotate_90': self.rotate_90,
            'watermark': self.watermark,
            'post_roll_seconds': self.post_roll_seconds,
            'pre_roll_seconds': self.pre_roll_seconds
        }


class Camera(object):

    def __init__(self, camera=None, guid=None, name="Default Camera"):
        self.guid = guid if guid else str(uuid.uuid4())
        self.name = name
        self.description = ""
        self.delay = 125
        self.apply_settings_before_print = False
        self.address = "http://127.0.0.1/webcam/"
        self.snapshot_request_template = "{camera_address}?action=snapshot"
        self.ignore_ssl_error = False
        self.username = ""
        self.password = ""
        self.brightness = 128
        self.brightness_request_template = self.TemplateToString(0, 0, 9963776, 1)
        self.contrast = 128
        self.contrast_request_template = self.TemplateToString(0, 0, 9963777, 1)
        self.saturation = 128
        self.saturation_request_template = self.TemplateToString(0, 0, 9963778, 1)
        self.white_balance_auto = True
        self.white_balance_auto_request_template = self.TemplateToString(0, 0, 9963788, 1)
        self.gain = 100
        self.gain_request_template = self.TemplateToString(0, 0, 9963795, 1)
        self.powerline_frequency = 60
        self.powerline_frequency_request_template = self.TemplateToString(0, 0, 9963800, 1)
        self.white_balance_temperature = 4000
        self.white_balance_temperature_request_template = self.TemplateToString(0, 0, 9963802, 1)
        self.sharpness = 128
        self.sharpness_request_template = self.TemplateToString(0, 0, 9963803, 1)
        self.backlight_compensation_enabled = False
        self.backlight_compensation_enabled_request_template = self.TemplateToString(0, 0, 9963804, 1)
        self.exposure_type = 1
        self.exposure_type_request_template = self.TemplateToString(0, 0, 10094849, 1)
        self.exposure = 250
        self.exposure_request_template = self.TemplateToString(0, 0, 10094850, 1)
        self.exposure_auto_priority_enabled = True
        self.exposure_auto_priority_enabled_request_template = self.TemplateToString(0, 0, 10094851, 1)
        self.pan = 0
        self.pan_request_template = self.TemplateToString(0, 0, 10094856, 1)
        self.tilt = 0
        self.tilt_request_template = self.TemplateToString(0, 0, 10094857, 1)
        self.autofocus_enabled = True
        self.autofocus_enabled_request_template = self.TemplateToString(0, 0, 10094860, 1)
        self.focus = 28
        self.focus_request_template = self.TemplateToString(0, 0, 10094858, 1)
        self.zoom = 100
        self.zoom_request_template = self.TemplateToString(0, 0, 10094861, 1)
        self.led1_mode = 'auto'
        self.led1_mode_request_template = self.TemplateToString(0, 0, 168062213, 1)
        self.led1_frequency = 0
        self.led1_frequency_request_template = self.TemplateToString(0, 0, 168062214, 1)
        self.jpeg_quality = 90
        self.jpeg_quality_request_template = self.TemplateToString(0, 0, 1, 3)

        if not camera is None:
            self.Update(camera)

    def TemplateToString(self, dest, plugin, id, group):
        return (
            "{camera_address}?action=command&"
            + "dest=" + str(dest)
            + "&plugin=" + str(plugin)
            + "&id=" + str(id)
            + "&group=" + str(group)
            + "&value={value}"
        )

    def Update(self, changes):
        if "guid" in changes.keys():
            self.guid = utility.get_string(changes["guid"], self.guid)
        if "name" in changes.keys():
            self.name = utility.get_string(changes["name"], self.name)
        if "description" in changes.keys():
            self.description = utility.get_string(
                changes["description"], self.description)
        if "delay" in changes.keys():
            self.delay = utility.get_int(
                changes["delay"], self.delay)
        if "address" in changes.keys():
            self.address = utility.get_string(changes["address"], self.address)
        if "apply_settings_before_print" in changes.keys():
            self.apply_settings_before_print = utility.get_bool(
                changes["apply_settings_before_print"], self.apply_settings_before_print)
        if "ignore_ssl_error" in changes.keys():
            self.ignore_ssl_error = utility.get_bool(
                changes["ignore_ssl_error"], self.ignore_ssl_error)
        if "username" in changes.keys():
            self.username = utility.get_string(
                changes["username"], self.username)
        if "password" in changes.keys():
            self.password = utility.get_string(
                changes["password"], self.password)

        if "brightness" in changes.keys():
            self.brightness = utility.get_int(
                changes["brightness"], self.brightness)
        if "contrast" in changes.keys():
            self.contrast = utility.get_int(changes["contrast"], self.contrast)
        if "saturation" in changes.keys():
            self.saturation = utility.get_int(
                changes["saturation"], self.saturation)
        if "white_balance_auto" in changes.keys():
            self.white_balance_auto = utility.get_bool(
                changes["white_balance_auto"], self.white_balance_auto)
        if "gain" in changes.keys():
            self.gain = utility.get_int(changes["gain"], self.gain)
        if "powerline_frequency" in changes.keys():
            self.powerline_frequency = utility.get_int(
                changes["powerline_frequency"], self.powerline_frequency)
        if "white_balance_temperature" in changes.keys():
            self.white_balance_temperature = utility.get_int(
                changes["white_balance_temperature"], self.white_balance_temperature)
        if "sharpness" in changes.keys():
            self.sharpness = utility.get_int(
                changes["sharpness"], self.sharpness)
        if "backlight_compensation_enabled" in changes.keys():
            self.backlight_compensation_enabled = utility.get_bool(
                changes["backlight_compensation_enabled"], self.backlight_compensation_enabled)
        if "exposure_type" in changes.keys():
            self.exposure_type = utility.get_int(
                changes["exposure_type"], self.exposure_type)
        if "exposure" in changes.keys():
            self.exposure = utility.get_int(changes["exposure"], self.exposure)
        if "exposure_auto_priority_enabled" in changes.keys():
            self.exposure_auto_priority_enabled = utility.get_bool(
                changes["exposure_auto_priority_enabled"], self.exposure_auto_priority_enabled)
        if "pan" in changes.keys():
            self.pan = utility.get_int(changes["pan"], self.pan)
        if "tilt" in changes.keys():
            self.tilt = utility.get_int(changes["tilt"], self.tilt)
        if "autofocus_enabled" in changes.keys():
            self.autofocus_enabled = utility.get_bool(
                changes["autofocus_enabled"], self.autofocus_enabled)
        if "focus" in changes.keys():
            self.focus = utility.get_int(changes["focus"], self.focus)
        if "zoom" in changes.keys():
            self.zoom = utility.get_int(changes["zoom"], self.zoom)
        if "led1_mode" in changes.keys():
            self.led1_mode = utility.get_string(
                changes["led1_mode"], self.led1_frequency)
        if "led1_frequency" in changes.keys():
            self.led1_frequency = utility.get_int(
                changes["led1_frequency"], self.led1_frequency)
        if "jpeg_quality" in changes.keys():
            self.jpeg_quality = utility.get_int(
                changes["jpeg_quality"], self.jpeg_quality)
        if "snapshot_request_template" in changes.keys():
            self.snapshot_request_template = utility.get_string(
                changes["snapshot_request_template"], self.snapshot_request_template)
        if "brightness_request_template" in changes.keys():
            self.brightness_request_template = utility.get_string(
                changes["brightness_request_template"], self.brightness_request_template)
        if "contrast_request_template" in changes.keys():
            self.contrast_request_template = utility.get_string(
                changes["contrast_request_template"], self.contrast_request_template)
        if "saturation_request_template" in changes.keys():
            self.saturation_request_template = utility.get_string(
                changes["saturation_request_template"], self.saturation_request_template)
        if "white_balance_auto_request_template" in changes.keys():
            self.white_balance_auto_request_template = utility.get_string(
                changes["white_balance_auto_request_template"], self.white_balance_auto_request_template)
        if "gain_request_template" in changes.keys():
            self.gain_request_template = utility.get_string(
                changes["gain_request_template"], self.gain_request_template)
        if "powerline_frequency_request_template" in changes.keys():
            self.powerline_frequency_request_template = utility.get_string(
                changes["powerline_frequency_request_template"], self.powerline_frequency_request_template)
        if "white_balance_temperature_request_template" in changes.keys():
            self.white_balance_temperature_request_template = utility.get_string(
                changes["white_balance_temperature_request_template"], self.white_balance_temperature_request_template)
        if "sharpness_request_template" in changes.keys():
            self.sharpness_request_template = utility.get_string(
                changes["sharpness_request_template"], self.sharpness_request_template)
        if "backlight_compensation_enabled_request_template" in changes.keys():
            self.backlight_compensation_enabled_request_template = utility.get_string(
                changes["backlight_compensation_enabled_request_template"],
                self.backlight_compensation_enabled_request_template
            )
        if "exposure_type_request_template" in changes.keys():
            self.exposure_type_request_template = utility.get_string(
                changes["exposure_type_request_template"], self.exposure_type_request_template)
        if "exposure_request_template" in changes.keys():
            self.exposure_request_template = utility.get_string(
                changes["exposure_request_template"], self.exposure_request_template)
        if "exposure_auto_priority_enabled_request_template" in changes.keys():
            self.exposure_auto_priority_enabled_request_template = utility.get_string(
                changes["exposure_auto_priority_enabled_request_template"],
                self.exposure_auto_priority_enabled_request_template
            )
        if "pan_request_template" in changes.keys():
            self.pan_request_template = utility.get_string(
                changes["pan_request_template"], self.pan_request_template)
        if "tilt_request_template" in changes.keys():
            self.tilt_request_template = utility.get_string(
                changes["tilt_request_template"], self.tilt_request_template)
        if "autofocus_enabled_request_template" in changes.keys():
            self.autofocus_enabled_request_template = utility.get_string(
                changes["autofocus_enabled_request_template"], self.autofocus_enabled_request_template)
        if "focus_request_template" in changes.keys():
            self.focus_request_template = utility.get_string(
                changes["focus_request_template"], self.focus_request_template)
        if "led1_mode_request_template" in changes.keys():
            self.led1_mode_request_template = utility.get_string(
                changes["led1_mode_request_template"], self.led1_mode_request_template)
        if "led1_frequency_request_template" in changes.keys():
            self.led1_frequency_request_template = utility.get_string(
                changes["led1_frequency_request_template"], self.led1_frequency_request_template)
        if "jpeg_quality_request_template" in changes.keys():
            self.jpeg_quality_request_template = utility.get_string(
                changes["jpeg_quality_request_template"], self.jpeg_quality_request_template)
        if "zoom_request_template" in changes.keys():
            self.zoom_request_template = utility.get_string(
                changes["zoom_request_template"], self.zoom_request_template)

    def ToDict(self):
        return {
            'guid': self.guid,
            'name': self.name,
            'description': self.description,
            'delay': self.delay,
            'address': self.address,
            'snapshot_request_template': self.snapshot_request_template,
            'apply_settings_before_print': self.apply_settings_before_print,
            'ignore_ssl_error': self.ignore_ssl_error,
            'password': self.password,
            'username': self.username,
            'brightness': self.brightness,
            'contrast': self.contrast,
            'saturation': self.saturation,
            'white_balance_auto': self.white_balance_auto,
            'gain': self.gain,
            'powerline_frequency': self.powerline_frequency,
            'white_balance_temperature': self.white_balance_temperature,
            'sharpness': self.sharpness,
            'backlight_compensation_enabled': self.backlight_compensation_enabled,
            'exposure_type': self.exposure_type,
            'exposure': self.exposure,
            'exposure_auto_priority_enabled': self.exposure_auto_priority_enabled,
            'pan': self.pan,
            'tilt': self.tilt,
            'autofocus_enabled': self.autofocus_enabled,
            'focus': self.focus,
            'zoom': self.zoom,
            'led1_mode': self.led1_mode,
            'led1_frequency': self.led1_frequency,
            'jpeg_quality': self.jpeg_quality,
            'brightness_request_template': self.brightness_request_template,
            'contrast_request_template': self.contrast_request_template,
            'saturation_request_template': self.saturation_request_template,
            'white_balance_auto_request_template': self.white_balance_auto_request_template,
            'gain_request_template': self.gain_request_template,
            'powerline_frequency_request_template': self.powerline_frequency_request_template,
            'white_balance_temperature_request_template': self.white_balance_temperature_request_template,
            'sharpness_request_template': self.sharpness_request_template,
            'backlight_compensation_enabled_request_template': self.backlight_compensation_enabled_request_template,
            'exposure_type_request_template': self.exposure_type_request_template,
            'exposure_request_template': self.exposure_request_template,
            'exposure_auto_priority_enabled_request_template': self.exposure_auto_priority_enabled_request_template,
            'pan_request_template': self.pan_request_template,
            'tilt_request_template': self.tilt_request_template,
            'autofocus_enabled_request_template': self.autofocus_enabled_request_template,
            'focus_request_template': self.focus_request_template,
            'zoom_request_template': self.zoom_request_template,
            'led1_mode_request_template': self.led1_mode_request_template,
            'led1_frequency_request_template': self.led1_frequency_request_template,
            'jpeg_quality_request_template': self.jpeg_quality_request_template,
        }


class DebugProfile(object):
    Logger = None
    FormatString = '%(asctime)s - %(levelname)s - %(message)s'
    ConsoleFormatString = '{asctime} - {levelname} - {message}'

    def __init__(self, logFilePath, debugProfile=None, guid=None, name="Default Debug Profile"):
        self.logFilePath = logFilePath
        self.guid = guid if guid else str(uuid.uuid4())
        self.name = name
        self.description = ""
        # Configure the logger if it has not been created
        if DebugProfile.Logger is None:
            DebugProfile.Logger = logging.getLogger(
                "octoprint.plugins.octolapse")

            from octoprint.logging.handlers import CleaningTimedRotatingFileHandler
            octoprint_logging_handler = CleaningTimedRotatingFileHandler(
                self.logFilePath, when="D", backupCount=3)
            octoprint_logging_handler.setFormatter(
                logging.Formatter("%(asctime)s %(message)s"))
            octoprint_logging_handler.setLevel(logging.DEBUG)
            DebugProfile.Logger.addHandler(octoprint_logging_handler)
            DebugProfile.Logger.propagate = False
            # we are controlling our logging via settings, so set to debug so that nothing is filtered
            DebugProfile.Logger.setLevel(logging.DEBUG)

        self.log_to_console = False
        self.enabled = False
        self.is_test_mode = False
        self.position_change = False
        self.position_command_received = False
        self.extruder_change = False
        self.extruder_triggered = False
        self.trigger_create = False
        self.trigger_wait_state = False
        self.trigger_triggering = False
        self.trigger_triggering_state = False
        self.trigger_layer_change = False
        self.trigger_height_change = False
        self.trigger_zhop = False
        self.trigger_time_unpaused = False
        self.trigger_time_remaining = False
        self.snapshot_gcode = False
        self.snapshot_gcode_endcommand = False
        self.snapshot_position = False
        self.snapshot_position_return = False
        self.snapshot_position_resume_print = False
        self.snapshot_save = False
        self.snapshot_download = False
        self.render_start = False
        self.render_complete = False
        self.render_fail = False
        self.render_sync = False
        self.snapshot_clean = False
        self.settings_save = False
        self.settings_load = False
        self.print_state_changed = False
        self.camera_settings_apply = False
        self.gcode_sent_all = False
        self.gcode_queuing_all = False

        if debugProfile is not None:
            self.Update(debugProfile)

    def Update(self, changes):
        if "guid" in changes.keys():
            self.guid = utility.get_string(changes["guid"], self.guid)
        if "name" in changes.keys():
            self.name = utility.get_string(changes["name"], self.name)
        if "description" in changes.keys():
            self.description = utility.get_string(
                changes["description"], self.description)
        if "enabled" in changes.keys():
            self.enabled = utility.get_bool(changes["enabled"], self.enabled)
        if "is_test_mode" in changes.keys():
            self.is_test_mode = utility.get_bool(
                changes["is_test_mode"], self.enabled)
        if "log_to_console" in changes.keys():
            self.log_to_console = utility.get_bool(
                changes["log_to_console"], self.log_to_console)
        if "position_change" in changes.keys():
            self.position_change = utility.get_bool(
                changes["position_change"], self.position_change)
        if "position_command_received" in changes.keys():
            self.position_command_received = utility.get_bool(
                changes["position_command_received"], self.position_command_received)
        if "extruder_change" in changes.keys():
            self.extruder_change = utility.get_bool(
                changes["extruder_change"], self.extruder_change)
        if "extruder_triggered" in changes.keys():
            self.extruder_triggered = utility.get_bool(
                changes["extruder_triggered"], self.extruder_triggered)
        if "trigger_create" in changes.keys():
            self.trigger_create = utility.get_bool(
                changes["trigger_create"], self.trigger_create)
        if "trigger_wait_state" in changes.keys():
            self.trigger_wait_state = utility.get_bool(
                changes["trigger_wait_state"], self.trigger_wait_state)
        if "trigger_triggering" in changes.keys():
            self.trigger_triggering = utility.get_bool(
                changes["trigger_triggering"], self.trigger_triggering)
        if "trigger_triggering_state" in changes.keys():
            self.trigger_triggering_state = utility.get_bool(
                changes["trigger_triggering_state"], self.trigger_triggering_state)
        if "trigger_layer_change" in changes.keys():
            self.trigger_layer_change = utility.get_bool(
                changes["trigger_layer_change"], self.trigger_layer_change)
        if "trigger_height_change" in changes.keys():
            self.trigger_height_change = utility.get_bool(
                changes["trigger_height_change"], self.trigger_height_change)
        if "trigger_time_remaining" in changes.keys():
            self.trigger_time_remaining = utility.get_bool(
                changes["trigger_time_remaining"], self.trigger_time_remaining)
        if "trigger_time_unpaused" in changes.keys():
            self.trigger_time_unpaused = utility.get_bool(
                changes["trigger_time_unpaused"], self.trigger_time_unpaused)
        if "trigger_zhop" in changes.keys():
            self.trigger_zhop = utility.get_bool(
                changes["trigger_zhop"], self.trigger_zhop)
        if "snapshot_gcode" in changes.keys():
            self.snapshot_gcode = utility.get_bool(
                changes["snapshot_gcode"], self.snapshot_gcode)
        if "snapshot_gcode_endcommand" in changes.keys():
            self.snapshot_gcode_endcommand = utility.get_bool(
                changes["snapshot_gcode_endcommand"], self.snapshot_gcode_endcommand)
        if "snapshot_position" in changes.keys():
            self.snapshot_position = utility.get_bool(
                changes["snapshot_position"], self.snapshot_position)
        if "snapshot_position_return" in changes.keys():
            self.snapshot_position_return = utility.get_bool(
                changes["snapshot_position_return"], self.snapshot_position_return)
        if "snapshot_position_resume_print" in changes.keys():
            self.snapshot_position_resume_print = utility.get_bool(
                changes["snapshot_position_resume_print"], self.snapshot_position_resume_print)
        if "snapshot_save" in changes.keys():
            self.snapshot_save = utility.get_bool(
                changes["snapshot_save"], self.snapshot_save)
        if "snapshot_download" in changes.keys():
            self.snapshot_download = utility.get_bool(
                changes["snapshot_download"], self.snapshot_download)
        if "render_start" in changes.keys():
            self.render_start = utility.get_bool(
                changes["render_start"], self.snapshot_download)
        if "render_complete" in changes.keys():
            self.render_complete = utility.get_bool(
                changes["render_complete"], self.render_complete)
        if "render_fail" in changes.keys():
            self.render_fail = utility.get_bool(
                changes["render_fail"], self.snapshot_download)
        if "render_sync" in changes.keys():
            self.render_sync = utility.get_bool(
                changes["render_sync"], self.snapshot_download)
        if "snapshot_clean" in changes.keys():
            self.snapshot_clean = utility.get_bool(
                changes["snapshot_clean"], self.snapshot_clean)
        if "settings_save" in changes.keys():
            self.settings_save = utility.get_bool(
                changes["settings_save"], self.settings_save)
        if "settings_load" in changes.keys():
            self.settings_load = utility.get_bool(
                changes["settings_load"], self.settings_load)
        if "print_state_changed" in changes.keys():
            self.print_state_changed = utility.get_bool(
                changes["print_state_changed"], self.print_state_changed)
        if "camera_settings_apply" in changes.keys():
            self.camera_settings_apply = utility.get_bool(
                changes["camera_settings_apply"], self.camera_settings_apply)
        if "gcode_sent_all" in changes.keys():
            self.gcode_sent_all = utility.get_bool(
                changes["gcode_sent_all"], self.gcode_sent_all)
        if "gcode_queuing_all" in changes.keys():
            self.gcode_queuing_all = utility.get_bool(
                changes["gcode_queuing_all"], self.gcode_queuing_all)

    def ToDict(self):
        return {
            'guid': self.guid,
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
            'is_test_mode': self.is_test_mode,
            'log_to_console': self.log_to_console,
            'position_change': self.position_change,
            'position_command_received': self.position_command_received,
            'extruder_change': self.extruder_change,
            'extruder_triggered': self.extruder_triggered,
            'trigger_create': self.trigger_create,
            'trigger_wait_state': self.trigger_wait_state,
            'trigger_triggering': self.trigger_triggering,
            'trigger_triggering_state': self.trigger_triggering_state,
            'trigger_layer_change': self.trigger_layer_change,
            'trigger_height_change': self.trigger_height_change,
            'trigger_time_remaining': self.trigger_time_remaining,
            'trigger_time_unpaused': self.trigger_time_unpaused,
            'trigger_zhop': self.trigger_zhop,
            'snapshot_gcode': self.snapshot_gcode,
            'snapshot_gcode_endcommand': self.snapshot_gcode_endcommand,
            'snapshot_position': self.snapshot_position,
            'snapshot_position_return': self.snapshot_position_return,
            'snapshot_position_resume_print': self.snapshot_position_resume_print,
            'snapshot_save': self.snapshot_save,
            'snapshot_download': self.snapshot_download,
            'render_start': self.render_start,
            'render_complete': self.render_complete,
            'render_fail': self.render_fail,
            'render_sync': self.render_sync,
            'snapshot_clean': self.snapshot_clean,
            'settings_save': self.settings_save,
            'settings_load': self.settings_load,
            'print_state_changed': self.print_state_changed,
            'camera_settings_apply': self.camera_settings_apply,
            'gcode_sent_all': self.gcode_sent_all,
            'gcode_queuing_all': self.gcode_queuing_all
        }

    def LogToConsole(self, levelName, message, force=False):
        if self.log_to_console or force:
            try:
                print(DebugProfile.ConsoleFormatString.format(asctime=str(
                    datetime.now()), levelname=levelName, message=message))
            except:
                print(message)

    def LogInfo(self, message):
        if self.enabled:
            try:
                self.Logger.info(message)
                self.LogToConsole('info', message)
            except:
                self.LogToConsole(
                    'error', "Error logging info: message:{0}".format(message), force=True)
                return

    def LogWarning(self, message):
        if self.enabled:
            try:
                self.Logger.warning(message)
                self.LogToConsole('warn', message)
            except:
                self.LogToConsole(
                    'error', "Error logging warining: message:{0}".format(message), force=True)
                return

    def LogException(self, exception):
        message = utility.exception_to_string(exception)
        try:
            self.Logger.error(message)
            self.LogToConsole('error', message)
        except:
            self.LogToConsole(
                'error', "Error logging exception:{0}".format(msg), force=True)
            return

    def LogError(self, message):

        try:
            self.Logger.error(message)
            self.LogToConsole('error', message)
        except:
            self.LogToConsole(
                'error', "Error logging exception: message:{0}".format(message), force=True)
            return

    def LogPositionChange(self, message):
        if self.position_change:
            self.LogInfo(message)

    def LogPositionCommandReceived(self, message):
        if self.position_command_received:
            self.LogInfo(message)

    def LogExtruderChange(self, message):
        if self.extruder_change:
            self.LogInfo(message)

    def LogExtruderTriggered(self, message):
        if self.extruder_triggered:
            self.LogInfo(message)

    def LogTriggerCreate(self, message):
        if self.trigger_create:
            self.LogInfo(message)

    def LogTriggerWaitState(self, message):
        if self.trigger_wait_state:
            self.LogInfo(message)

    def LogTriggering(self, message):
        if self.trigger_triggering:
            self.LogInfo(message)

    def LogTriggerTriggeringState(self, message):
        if self.trigger_triggering_state:
            self.LogInfo(message)

    def LogTriggerHeightChange(self, message):
        if self.trigger_height_change:
            self.LogInfo(message)

    def LogPositionLayerChange(self, message):
        if self.position_change:
            self.LogInfo(message)

    def LogPositionHeightChange(self, message):
        if self.position_change:
            self.LogInfo(message)

    def LogPositionZHop(self, message):
        if self.trigger_zhop:
            self.LogInfo(message)

    def LogTimerTriggerUnpaused(self, message):
        if self.trigger_time_unpaused:
            self.LogInfo(message)

    def LogTriggerTimeRemaining(self, message):
        if self.trigger_time_remaining:
            self.LogInfo(message)

    def LogTriggerTimeRemaining(self, message):
        if self.trigger_time_remaining:
            self.LogInfo(message)

    def LogSnapshotGcode(self, message):
        if self.snapshot_gcode:
            self.LogInfo(message)

    def LogSnapshotGcodeEndcommand(self, message):
        if self.snapshot_gcode_endcommand:
            self.LogInfo(message)

    def LogSnapshotPosition(self, message):
        if self.snapshot_position:
            self.LogInfo(message)

    def LogSnapshotPositionReturn(self, message):
        if self.snapshot_position_return:
            self.LogInfo(message)

    def LogSnapshotPositionResumePrint(self, message):
        if self.snapshot_position_resume_print:
            self.LogInfo(message)

    def LogSnapshotSave(self, message):
        if self.snapshot_save:
            self.LogInfo(message)

    def LogSnapshotDownload(self, message):
        if self.snapshot_download:
            self.LogInfo(message)

    def LogRenderStart(self, message):
        if self.render_start:
            self.LogInfo(message)

    def LogRenderComplete(self, message):
        if self.render_complete:
            self.LogInfo(message)

    def LogRenderFail(self, message):
        if self.render_fail:
            self.LogInfo(message)

    def LogRenderSync(self, message):
        if self.render_sync:
            self.LogInfo(message)

    def LogSnapshotClean(self, message):
        if self.snapshot_clean:
            self.LogInfo(message)

    def LogSettingsSave(self, message):
        if self.settings_save:
            self.LogInfo(message)

    def LogSettingsLoad(self, message):
        if self.settings_load:
            self.LogInfo(message)

    def LogPrintStateChange(self, message):
        if self.print_state_changed:
            self.LogInfo(message)

    def LogCameraSettingsApply(self, message):
        if self.camera_settings_apply:
            self.LogInfo(message)

    def LogSentGcode(self, message):
        if self.gcode_sent_all:
            self.LogInfo(message)

    def LogQueuingGcode(self, message):
        if self.gcode_queuing_all:
            self.LogInfo(message)


class OctolapseSettings(object):
    DefaultDebugProfile = None
    Logger = None

    # constants

    def __init__(self, logFilePath, settings=None):

        self.DefaultPrinter = Printer(
            name="Default Printer", guid="5d39248f-5e11-4c42-b7f4-810c7acc287e")
        self.DefaultStabilization = Stabilization(
            name="Default Stabilization", guid="3a94e945-f5d5-4655-909a-e61c1122cc1f")
        self.DefaultSnapshot = Snapshot(
            name="Default Snapshot", guid="5d16f0cb-512c-476a-b32d-a10191ad0d0e")
        self.DefaultRendering = Rendering(
            name="Default Rendering", guid="32d6ad28-0314-4a14-974c-0d7d92325f17")
        self.DefaultCamera = Camera(
            name="Default Camera", guid="6b3361a7-82b7-4abf-b3d1-e3046d457d8c")
        self.DefaultDebugProfile = DebugProfile(
            logFilePath=logFilePath, name="Default Debug", guid="08ad284a-76cc-4854-b8a0-f2658b784dd7")
        self.LogFilePath = logFilePath

        self.version = "0.1.0.0"
        self.show_navbar_icon = True
        self.show_navbar_when_not_printing = True
        self.is_octolapse_enabled = True
        self.auto_reload_latest_snapshot = True
        self.auto_reload_frames = 5
        self.show_position_state_changes = False
        self.show_position_changes = False
        self.show_extruder_state_changes = False
        self.show_trigger_state_changes = False
        printer = self.DefaultPrinter
        self.current_printer_profile_guid = printer.guid
        self.printers = {printer.guid: printer}

        stabilization = self.DefaultStabilization
        self.current_stabilization_profile_guid = stabilization.guid
        self.stabilizations = {stabilization.guid: stabilization}

        snapshot = self.DefaultSnapshot
        self.current_snapshot_profile_guid = snapshot.guid
        self.snapshots = {snapshot.guid: snapshot}

        rendering = self.DefaultRendering
        self.current_rendering_profile_guid = rendering.guid
        self.renderings = {rendering.guid: rendering}

        camera = self.DefaultCamera
        self.current_camera_profile_guid = camera.guid
        self.cameras = {camera.guid: camera}

        debugProfile = self.DefaultDebugProfile
        self.current_debug_profile_guid = debugProfile.guid
        self.debug_profiles = {debugProfile.guid: debugProfile}

        if settings is not None:
            self.Update(settings)

    def CurrentStabilization(self):
        if len(self.stabilizations.keys()) == 0:
            stabilization = Stabilization(None)
            self.stabilizations[stabilization.guid] = stabilization
            self.current_stabilization_profile_guid = stabilization.guid
        return self.stabilizations[self.current_stabilization_profile_guid]

    def CurrentSnapshot(self):
        if len(self.snapshots.keys()) == 0:
            snapshot = Snapshot(None)
            self.snapshots[snapshot.guid] = snapshot
            self.current_snapshot_profile_guid = snapshot.guid
        return self.snapshots[self.current_snapshot_profile_guid]

    def CurrentRendering(self):
        if len(self.renderings.keys()) == 0:
            rendering = Rendering(None)
            self.renderings[rendering.guid] = rendering
            self.current_rendering_profile_guid = rendering.guid
        return self.renderings[self.current_rendering_profile_guid]

    def CurrentPrinter(self):
        if len(self.printers.keys()) == 0:
            printer = Printer(printer=None)
            self.printers[printer.guid] = printer
            self.current_printer_profile_guid = printer.guid
        return self.printers[self.current_printer_profile_guid]

    def CurrentCamera(self):
        if len(self.cameras.keys()) == 0:
            camera = Camera(camera=None)
            self.cameras[camera.guid] = camera
            self.current_camera_profile_guid = camera.guid
        return self.cameras[self.current_camera_profile_guid]

    def CurrentDebugProfile(self):
        if len(self.debug_profiles.keys()) == 0:
            debug_profile = DebugProfile(self.LogFilePath, debug_profiles=None)
            self.debug_profiles[debug_profile.guid] = debug_profile
            self.current_debug_profile_guid = debug_profile.guid
        return self.debug_profiles[self.current_debug_profile_guid]

    def Update(self, changes):

        if HasKey(changes, "is_octolapse_enabled"):
            self.is_octolapse_enabled = bool(
                GetValue(changes, "is_octolapse_enabled", self.is_octolapse_enabled))
        if HasKey(changes, "auto_reload_latest_snapshot"):
            self.auto_reload_latest_snapshot = bool(GetValue(
                changes, "auto_reload_latest_snapshot", self.auto_reload_latest_snapshot))
        if HasKey(changes, "auto_reload_frames"):
            self.auto_reload_frames = int(
                GetValue(changes, "auto_reload_frames", self.auto_reload_frames))
        if HasKey(changes, "show_navbar_icon"):
            self.show_navbar_icon = bool(
                GetValue(changes, "show_navbar_icon", self.show_navbar_icon))
        if HasKey(changes, "show_navbar_when_not_printing"):
            self.show_navbar_when_not_printing = bool(GetValue(
                changes, "show_navbar_when_not_printing", self.show_navbar_when_not_printing))
        if HasKey(changes, "show_position_state_changes"):
            self.show_position_state_changes = bool(GetValue(
                changes, "show_position_state_changes", self.show_position_state_changes))
        if HasKey(changes, "show_position_changes"):
            self.show_position_changes = bool(
                GetValue(changes, "show_position_changes", self.show_position_changes))
        if HasKey(changes, "show_extruder_state_changes"):
            self.show_extruder_state_changes = bool(GetValue(
                changes, "show_extruder_state_changes", self.show_extruder_state_changes))
        if HasKey(changes, "show_trigger_state_changes"):
            self.show_trigger_state_changes = bool(GetValue(
                changes, "show_trigger_state_changes", self.show_trigger_state_changes))
        if HasKey(changes, "current_printer_profile_guid"):
            self.current_printer_profile_guid = str(GetValue(
                changes, "current_printer_profile_guid", self.current_printer_profile_guid))
        if HasKey(changes, "current_stabilization_profile_guid"):
            self.current_stabilization_profile_guid = str(GetValue(
                changes, "current_stabilization_profile_guid", self.current_stabilization_profile_guid))
        if HasKey(changes, "current_snapshot_profile_guid"):
            self.current_snapshot_profile_guid = str(GetValue(
                changes, "current_snapshot_profile_guid", self.current_snapshot_profile_guid))
        if HasKey(changes, "current_rendering_profile_guid"):
            self.current_rendering_profile_guid = str(GetValue(
                changes, "current_rendering_profile_guid", self.current_rendering_profile_guid))
        if HasKey(changes, "current_camera_profile_guid"):
            self.current_camera_profile_guid = str(GetValue(
                changes, "current_camera_profile_guid", self.current_camera_profile_guid))
        if HasKey(changes, "current_debug_profile_guid"):
            self.current_debug_profile_guid = str(GetValue(
                changes, "current_debug_profile_guid", self.current_debug_profile_guid))

        if HasKey(changes, "printers"):
            self.printers = {}
            printers = GetValue(changes, "printers", None)
            for printer in printers:
                if printer["guid"] == "":
                    printer["guid"] = str(uuid.uuid4())
                self.printers.update({printer["guid"]: Printer(printer=printer)})
        if HasKey(changes, "stabilizations"):
            self.stabilizations = {}
            stabilizations = GetValue(changes, "stabilizations", None)
            for stabilization in stabilizations:
                if stabilization["guid"] == "":
                    stabilization["guid"] = str(uuid.uuid4())
                self.stabilizations.update({stabilization["guid"]: Stabilization(stabilization=stabilization)})

        if HasKey(changes, "snapshots"):
            self.snapshots = {}
            snapshots = GetValue(changes, "snapshots", None)
            for snapshot in snapshots:
                if snapshot["guid"] == "":
                    snapshot["guid"] = str(uuid.uuid4())
                self.snapshots.update({snapshot["guid"]: Snapshot(snapshot=snapshot)})
        if HasKey(changes, "renderings"):
            self.renderings = {}
            renderings = GetValue(changes, "renderings", None)
            for rendering in renderings:
                if rendering["guid"] == "":
                    rendering["guid"] = str(uuid.uuid4())
                self.renderings.update({rendering["guid"]: Rendering(
                    rendering=rendering)})

        if HasKey(changes, "cameras"):
            self.cameras = {}
            cameras = GetValue(changes, "cameras", None)
            for camera in cameras:
                if camera["guid"] == "":
                    camera["guid"] = str(uuid.uuid4())
                self.cameras.update({camera["guid"]: Camera(camera=camera)})

        if HasKey(changes, "debug_profiles"):
            self.debug_profiles = {}
            debugProfiles = GetValue(changes, "debug_profiles", None)
            for debugProfile in debugProfiles:
                if debugProfile["guid"] == "":
                    debugProfile["guid"] = str(uuid.uuid4())
                self.debug_profiles.update(
                    {debugProfile["guid"]: DebugProfile(self.LogFilePath, debugProfile=debugProfile)})

    def ToDict(self, ):
        defaults = OctolapseSettings(self.LogFilePath)

        settingsDict = {
            'version': utility.get_string(
                self.version, defaults.version
            ),
            "is_octolapse_enabled": utility.get_bool(
                self.is_octolapse_enabled, defaults.is_octolapse_enabled
            ),
            "auto_reload_latest_snapshot": utility.get_bool(
                self.auto_reload_latest_snapshot, defaults.auto_reload_latest_snapshot
            ),
            "auto_reload_frames": utility.get_int(
                self.auto_reload_frames, defaults.auto_reload_frames
            ),
            "show_navbar_icon": utility.get_bool(
                self.show_navbar_icon, defaults.show_navbar_icon
            ),
            "show_navbar_when_not_printing": utility.get_bool(
                self.show_navbar_when_not_printing, defaults.show_navbar_when_not_printing
            ),
            "show_position_changes": utility.get_bool(
                self.show_position_changes, defaults.show_position_changes
            ),
            "show_position_state_changes": utility.get_bool(
                self.show_position_state_changes, defaults.show_position_state_changes
            ),
            "show_extruder_state_changes": utility.get_bool(
                self.show_extruder_state_changes, defaults.show_extruder_state_changes
            ),
            "show_trigger_state_changes": utility.get_bool(
                self.show_trigger_state_changes, defaults.show_trigger_state_changes
            ),
            "platform": sys.platform,
            'e_axis_default_mode_options': [
                dict(value='require-explicit', name='Require Explicit M82/M83'),
                dict(value='relative', name='Default To Relative'),
                dict(value='absolute', name='Default To Absolute')
            ],

            'g90_influences_extruder_options': [
                dict(value='use-octoprint-settings', name='Use Octoprint Settings'),
                dict(value='true', name='True'),
                dict(value='false', name='False'),
            ],
            'xyz_axes_default_mode_options': [
                dict(value='require-explicit', name='Require Explicit G90/G91'),
                dict(value='relative', name='Default To Relative'),
                dict(value='absolute', name='Default To Absolute')
            ],
            'stabilization_type_options': [
                dict(value='disabled', name='Disabled'),
                dict(value='fixed_coordinate', name='Fixed Coordinate'),
                dict(value='fixed_path', name='List of Fixed Coordinates'),
                dict(value='relative', name='Relative Coordinates (0-100)'),
                dict(value='relative_path', name='List of Relative Coordinates')
            ],

            'position_restriction_shapes': [
                dict(value="rect", name="Rectangle"),
                dict(value="circle", name="Circle")
            ],
            'position_restriction_types': [
                dict(value="required", name="Must be inside"),
                dict(value="forbidden", name="Cannot be inside")
            ],
            'snapshot_extruder_trigger_options': Snapshot.ExtruderTriggerOptions,
            'rendering_fps_calculation_options': [
                dict(value='static', name='Static FPS'),
                dict(value='duration', name='Fixed Run Length')
            ],
            'rendering_output_format_options': [
                dict(value='avi', name='AVI'),
                dict(value='flv', name='FLV'),
                dict(value='vob', name='VOB'),
                dict(value='mp4', name='MP4'),
                dict(value='mpeg', name='MPEG')
            ],
            'camera_powerline_frequency_options': [
                dict(value='50', name='50 HZ (Europe, China, India, etc)'),
                dict(value='60', name='60 HZ (North/South America, Japan, etc')
            ],
            'camera_exposure_type_options': [
                dict(value='0', name='Unknown - Let me know if you know what this option does.'),
                dict(value='1', name='Manual'),
                dict(value='2', name='Unknown - Let me know if you know what this option does.'),
                dict(value='3', name='Auto - Aperture Priority Mode')
            ],
            'camera_led_1_mode_options': [
                dict(value='on', name='On'),
                dict(value='off', name='Off'),
                dict(value='blink', name='Blink'),
                dict(value='auto', name='Auto')
            ],
            'current_printer_profile_guid': utility.get_string(
                self.current_printer_profile_guid, defaults.current_printer_profile_guid
            ),
            'printers': [],
            'current_stabilization_profile_guid': utility.get_string(
                self.current_stabilization_profile_guid, defaults.current_stabilization_profile_guid
            ),
            'stabilizations': [],
            'current_snapshot_profile_guid': utility.get_string(
                self.current_snapshot_profile_guid, defaults.current_snapshot_profile_guid
            ),
            'snapshots': [],
            'current_rendering_profile_guid': utility.get_string(
                self.current_rendering_profile_guid, defaults.current_rendering_profile_guid
            ),
            'renderings': [],
            'current_camera_profile_guid': utility.get_string(
                self.current_camera_profile_guid, defaults.current_camera_profile_guid
            ),
            'cameras': [],
            'current_debug_profile_guid': utility.get_string(
                self.current_debug_profile_guid, defaults.current_debug_profile_guid
            ),
            'debug_profiles': []
        }

        for key, printer in self.printers.items():
            settingsDict["printers"].append(printer.ToDict())
        settingsDict["default_printer_profile"] = self.DefaultPrinter.ToDict()

        for key, stabilization in self.stabilizations.items():
            settingsDict["stabilizations"].append(stabilization.ToDict())
        settingsDict["default_stabilization_profile"] = self.DefaultStabilization.ToDict()

        for key, snapshot in self.snapshots.items():
            settingsDict["snapshots"].append(snapshot.ToDict())
        settingsDict["default_snapshot_profile"] = self.DefaultSnapshot.ToDict()

        for key, rendering in self.renderings.items():
            settingsDict["renderings"].append(rendering.ToDict())
        settingsDict["default_rendering_profile"] = self.DefaultRendering.ToDict()

        for key, camera in self.cameras.items():
            settingsDict["cameras"].append(camera.ToDict())
        settingsDict["default_camera_profile"] = self.DefaultCamera.ToDict()

        for key, debugProfile in self.debug_profiles.items():
            settingsDict["debug_profiles"].append(debugProfile.ToDict())
        settingsDict["default_debug_profile"] = self.DefaultDebugProfile.ToDict()

        return settingsDict

    def GetMainSettingsDict(self):
        return {
            'is_octolapse_enabled': self.is_octolapse_enabled,
            'auto_reload_latest_snapshot': self.auto_reload_latest_snapshot,
            'auto_reload_frames': int(self.auto_reload_frames),
            'show_navbar_icon': self.show_navbar_icon,
            'show_navbar_when_not_printing': self.show_navbar_when_not_printing,
            'show_position_state_changes': self.show_position_state_changes,
            'show_position_changes': self.show_position_changes,
            'show_extruder_state_changes': self.show_extruder_state_changes,
            'show_trigger_state_changes': self.show_trigger_state_changes
        }

    # Add/Update/Remove/set current profile

    def addUpdateProfile(self, profileType, profile):
        # check the guid.  If it is null or empty, assign a new value.
        guid = profile["guid"]
        if guid is None or guid == "":
            guid = str(uuid.uuid4())
            profile["guid"] = guid
        newProfile = None

        if profileType == "Printer":
            newProfile = Printer(profile)
            self.printers[guid] = newProfile
        elif profileType == "Stabilization":
            newProfile = Stabilization(profile)
            self.stabilizations[guid] = newProfile
        elif profileType == "Snapshot":
            newProfile = Snapshot(profile)
            self.snapshots[guid] = newProfile
        elif profileType == "Rendering":
            newProfile = Rendering(profile)
            self.renderings[guid] = newProfile
        elif profileType == "Camera":
            newProfile = Camera(profile)
            self.cameras[guid] = newProfile
        elif profileType == "Debug":
            newProfile = DebugProfile(self.LogFilePath, debugProfile=profile)
            self.debug_profiles[guid] = newProfile
        else:
            raise ValueError('An unknown profile type ' +
                             str(profileType) + ' was received.')

        return newProfile

    def removeProfile(self, profileType, guid):

        if profileType == "Printer":
            del self.printers[guid]
        elif profileType == "Stabilization":
            del self.stabilizations[guid]
        elif profileType == "Snapshot":
            del self.snapshots[guid]
        elif profileType == "Rendering":
            del self.renderings[guid]
        elif profileType == "Camera":
            del self.cameras[guid]
        elif profileType == "Debug":
            del self.debug_profiles[guid]
        else:
            raise ValueError('An unknown profile type ' +
                             str(profileType) + ' was received.')

    def setCurrentProfile(self, profileType, guid):

        if profileType == "Printer":
            self.current_printer_profile_guid = guid
        elif profileType == "Stabilization":
            self.current_stabilization_profile_guid = guid
        elif profileType == "Snapshot":
            self.current_snapshot_profile_guid = guid
        elif profileType == "Rendering":
            self.current_rendering_profile_guid = guid
        elif profileType == "Camera":
            self.current_camera_profile_guid = guid
        elif profileType == "Debug":
            self.current_debug_profile_guid = guid
        else:
            raise ValueError('An unknown profile type ' +
                             str(profileType) + ' was received.')


def HasKey(object, key):
    if isinstance(object, dict):
        return key in object
    elif isinstance(object, PluginSettings):
        return object.has([key])


def GetValue(object, key, default=None):
    if isinstance(object, dict) and key in object:
        return object[key]
    elif isinstance(object, PluginSettings) and object.has([key]):
        return object.get([key])
    else:
        return default
