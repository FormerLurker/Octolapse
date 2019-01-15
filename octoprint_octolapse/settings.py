# coding=utf-8
##################################################################################
# Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
# Copyright (C) 2019  Brad Hochgesang
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

import copy
import json
import uuid
import sys
import octoprint_octolapse.utility as utility
import octoprint_octolapse.log as log
import math
import collections


class SettingsJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Settings):
            return obj.__dict__
        # Let the base class default method raise the TypeError
        elif isinstance(obj, log.Logger):
            return None
        elif isinstance(obj, bool):
            return str(obj).lower()

        return json.JSONEncoder.default(self, obj)


class SettingsJsonDecoder(json.JSONDecoder):
    def default(self, obj):
        if isinstance(obj, Settings):
            return obj.__dict__
        # Let the base class default method raise the TypeError
        if isinstance(obj, log.Logger):
            return None
        return json.JSONEncoder.default(self, obj)


class Settings(object):
    def clone(self):
        return copy.deepcopy(self)

    def to_dict(self):
        return self.__dict__.copy()

    def to_json(self, indent=0):
        return json.dumps(self.to_dict(), cls=SettingsJsonEncoder)

    @classmethod
    def encode_json(cls, o):
        return o.__dict__

    def update(self, iterable, **kwargs):
        Settings._update(self, iterable, **kwargs)

    @staticmethod
    def _update(source, iterable, **kwargs):
        try:
            item_to_iterate = iterable

            if not isinstance(iterable, collections.Iterable):
                item_to_iterate = iterable.__dict__

            for key, value in item_to_iterate.items():
                class_item = getattr(source, key, '{octolapse_no_property_found}')
                if not (isinstance(class_item, str) and class_item == '{octolapse_no_property_found}'):
                    if isinstance(class_item, log.Logger):
                        continue
                    elif isinstance(class_item, Settings):
                        class_item.update(value)
                    else:
                        source.__dict__[key] = source._try_convert_value(class_item, value)
        except Exception as e:
            raise e

    @staticmethod
    def _try_convert_value(destination, value):
        if value is None:
            return None
        if isinstance(destination, float):
            return float(value)
        # Note that bools are also ints, so bools need to come first
        elif isinstance(destination, bool):
            return bool(value)
        elif isinstance(destination, int):
            return int(value)
        else:
            # default action, just return the value
            return value

    @staticmethod
    def from_json(json_string):
        data = json.loads(json_string)
        return ProfileSettings.create_from(data)

    def save_as_json(self, output_file_path, indent=0):
        with open(output_file_path, 'w') as output_file:
            json.dump(self.to_dict(), output_file, cls=SettingsJsonEncoder)

    @classmethod
    def create_from(cls, iterable=(), **kwargs):
        new_object = cls()
        new_object.update(iterable, **kwargs)
        return new_object


class ProfileSettings(Settings):

    def __init__(self, name=""):
        self.name = name
        self.description = ""
        self.guid = str(uuid.uuid4())

    @staticmethod
    def get_options():
        return {}

    @classmethod
    def create_from(cls, iterable=(), **kwargs):
        new_object = cls("")
        new_object.update(iterable, **kwargs)
        return new_object


class PrinterProfile(ProfileSettings):
    def __init__(self, name="New Printer Profile"):
        super(PrinterProfile, self).__init__(name)
        # flag that is false until the profile has been saved by the user at least once
        # this is used to show a warning to the user if a new printer profile is used
        # without being configured
        self.has_been_saved_by_user = False
        # Slicer Settings
        self.slicer_type = "other"
        self.retract_length = 2.0
        self.retract_speed = 6000
        self.detract_speed = 3000
        self.movement_speed = 6000
        self.z_hop = .5
        self.z_hop_speed = 6000
        self.retract_speed = 4000
        # misc speeds
        self.maximum_z_speed = None
        self.print_speed = None
        self.perimeter_speed = None
        self.small_perimeter_speed = None
        self.external_perimeter_speed = None
        self.infill_speed = None
        self.solid_infill_speed = None
        self.top_solid_infill_speed = None
        self.support_speed = None
        self.bridge_speed = None
        self.gap_fill_speed = None
        self.first_layer_speed = None
        self.first_layer_travel_speed = None
        self.skirt_brim_speed = None
        self.above_raft_speed = None
        self.ooze_shield_speed = None
        self.prime_pillar_speed = None
        self.speed_tolerance = 0.6
        self.num_slow_layers = 0;
        # simplify 3d/slic3r speed multipliers
        self.first_layer_speed_multiplier = 100
        self.above_raft_speed_multiplier = 100
        self.prime_pillar_speed_multiplier = 100
        self.ooze_shield_speed_multiplier = 100
        self.outline_speed_multiplier = 100
        self.solid_infill_speed_multiplier = 100
        self.support_structure_speed_multiplier = 100
        self.bridging_speed_multiplier = 100
        self.small_perimeter_speed_multiplier = 100
        self.external_perimeter_speed_multiplier = 100
        self.top_solid_infill_speed_multiplier = 100
        # Slic3r only settings - Percent or mm/s text
        self.small_perimeter_speed_text = None
        self.external_perimeter_speed_text = None
        self.solid_infill_speed_text = None
        self.top_solid_infill_speed_text = None
        self.first_layer_speed_text = None

        self.snapshot_command = "snap"
        self.suppress_snapshot_command_always = True
        self.printer_position_confirmation_tolerance = 0.001
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
        self.priming_height = 0.75
        self.e_axis_default_mode = 'require-explicit'  # other values are 'relative' and 'absolute'
        self.g90_influences_extruder = 'use-octoprint-settings'  # other values are 'true' and 'false'
        self.xyz_axes_default_mode = 'require-explicit'  # other values are 'relative' and 'absolute'
        self.units_default = 'millimeters'
        self.axis_speed_display_units = 'mm-min'
        self.default_firmware_retractions = False
        self.default_firmware_retractions_zhop = False

    @staticmethod
    def get_options():
        return {
            'slicer_type_options': [
                dict(value='cura', name='Cura'),
                dict(value='simplify-3d', name='Simplify 3D'),
                dict(value='slic3r-pe', name='Slic3r Prusa Edition'),
                dict(value='other', name='Other Slicer')
            ],
            'e_axis_default_mode_options': [
                dict(value='require-explicit', name='Require Explicit M82/M83'),
                dict(value='relative', name='Default To Relative'),
                dict(value='absolute', name='Default To Absolute'),
                # dict(value='force-absolute', name='Force Absolute (send M82 at print start)'),
                # dict(value='force-relative', name='Force Relative (send M83 at print start)')
            ],
            'axis_speed_display_unit_options': [
                dict(value='mm-min', name='Millimeters per Minute (mm/min)'),
                dict(value='mm-sec', name='Millimeters per Second (mm/sec)')
            ],

            'g90_influences_extruder_options': [
                dict(value='use-octoprint-settings', name='Use Octoprint Settings'),
                dict(value='true', name='True'),
                dict(value='false', name='False'),
            ],
            'xyz_axes_default_mode_options': [
                dict(value='require-explicit', name='Require Explicit G90/G91'),
                dict(value='relative', name='Default To Relative'),
                dict(value='absolute', name='Default To Absolute'),
                # dict(value='force-absolute', name='Force Absolute (send G90 at print start)'),
                # dict(value='force-relative', name='Force Relative (send G91 at print start)')
            ],
            'units_default_options': [
                dict(value='require-explicit', name='Require Explicit G21'),
                dict(value='inches', name='Inches'),
                dict(value='millimeters', name='Millimeters')
            ],
        }

    # Todo:  Move all these functions into a separate class
    # Round and return speed in mm/min
    def get_speed_from_settings_slic3r_pe(self, speed, speed_name=None):
        if speed is None:
            return None

        # For some reason retract and detract speeds are rounded to the nearest mm/sec
        if speed_name is not None and speed_name in ["retract_speed", "detract_speed"]:
            speed = utility.round_to(speed, 1)

        # Convert speed to mm/min
        speed = speed * 60.0
        # round to .001

        return utility.round_to(speed, 0.01)

    def get_speed_from_settings_simplify_3d(self, speed, speed_name=None):
        if speed is None:
            return None
        speed -= 0.1
        return utility.round_to(speed, 1)

    def get_speed_from_settings_cura(self, speed, speed_nam=None):
        if speed is None:
            return None
        # Convert speed to mm/min
        speed = speed * 60.0
        # round to .1
        return utility.round_to(speed, 0.1)

    def get_speed_from_settings_other_slicer(self, speed, speed_name=None):
        if self.axis_speed_display_units == "mm-sec":
            speed = speed * 60.0
        # Todo - Look at this, we need to round prob.
        return speed

    def get_speed_for_slicer_type(self, speed, speed_name=None):
        if speed is None:
            return None
        if self.slicer_type == 'slic3r-pe':
            return self.get_speed_from_settings_slic3r_pe(speed, speed_name)
        elif self.slicer_type == 'simplify-3d':
            return self.get_speed_from_settings_simplify_3d(speed, speed_name)
        elif self.slicer_type == 'cura':
            return self.get_speed_from_settings_cura(speed, speed_name)
        elif self.slicer_type == 'other':
            return self.get_speed_from_settings_other_slicer(speed, speed_name)
        return speed

    def get_speed_tolerance_for_slicer_type(self):
        if self.slicer_type == 'slic3r-pe':
            return self.speed_tolerance * 60.0
        elif self.slicer_type == 'simplify-3d':
            return self.speed_tolerance
        elif self.slicer_type == 'cura':
            return self.speed_tolerance * 60.0
        elif self.slicer_type == 'other':
            if self.axis_speed_display_units == 'mm-sec':
                return self.speed_tolerance * 60
            return self.speed_tolerance
        return self.speed_tolerance

    def get_speed_by_multiple_for_simplify_3d(self, speed, multiple):
        if speed is None or multiple is None:
            return None
        return self.get_speed_from_settings_simplify_3d(speed * multiple / 100.0)

    def get_speed_by_multiple_for_cura(self, speed, multiple):
        if speed is None or multiple is None:
            return None
        return self.get_speed_from_settings_cura(speed * multiple / 100.0)

    def get_speed_by_multiple_for_slic3r_pe(self, speed, multiple):
        if speed is None or multiple is None:
            return None
        # round the speed multiplier to a multiple of 1
        return self.get_speed_from_settings_slic3r_pe(speed * multiple / 100.0)

    def get_speed_by_multiple_for_other_slicer(self, speed, multiple):
        if speed is None or multiple is None:
            return None
        return self.get_speed_from_settings_other_slicer(speed * multiple / 100.0)

    def get_speed_by_multiple_for_slicer_type(self, speed, multiple):
        if self.slicer_type == 'slic3r-pe':
            return self.get_speed_by_multiple_for_slic3r_pe(speed, multiple)
        if self.slicer_type == 'simplify-3d':
            return self.get_speed_by_multiple_for_simplify_3d(speed, multiple)
        if self.slicer_type == 'cura':
            return self.get_speed_by_multiple_for_cura(speed, multiple)
        return self.get_speed_by_multiple_for_other_slicer(speed, multiple)

    def get_retract_length_for_slicer_type(self):
        if self.slicer_type == 'slic3r-pe':
            return utility.round_to(self.retract_length, 0.00001)
        return self.retract_length

    def get_z_hop_for_slicer_type(self):
        if self.slicer_type == 'slic3r-pe':
            return utility.round_to(self.z_hop, 0.001)
        return self.z_hop


class StabilizationPath(Settings):
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


class StabilizationProfile(ProfileSettings):
    def __init__(self, name="New Stabilization Profile"):
        super(StabilizationProfile, self).__init__(name)
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

    @staticmethod
    def get_options():
        return {
            'stabilization_type_options': [
                dict(value='disabled', name='Disabled'),
                dict(value='fixed_coordinate', name='Fixed Coordinate'),
                dict(value='fixed_path', name='List of Fixed Coordinates'),
                dict(value='relative', name='Relative Coordinate (0-100)'),
                dict(value='relative_path', name='List of Relative Coordinates')
            ],
        }

    def get_stabilization_paths(self):
        x_stabilization_path = StabilizationPath()
        x_stabilization_path.Axis = "X"
        x_stabilization_path.Type = self.x_type
        if self.x_type == 'fixed_coordinate':
            x_stabilization_path.Path.append(self.x_fixed_coordinate)
            x_stabilization_path.CoordinateSystem = 'absolute'
        elif self.x_type == 'relative':
            x_stabilization_path.Path.append(self.x_relative)
            x_stabilization_path.CoordinateSystem = 'bed_relative'
        elif self.x_type == 'fixed_path':
            x_stabilization_path.Path = self.parse_csv_path(self.x_fixed_path)
            x_stabilization_path.CoordinateSystem = 'absolute'
            x_stabilization_path.Loop = self.x_fixed_path_loop
            x_stabilization_path.InvertLoop = self.x_fixed_path_invert_loop
        elif self.x_type == 'relative_path':
            x_stabilization_path.Path = self.parse_csv_path(self.x_relative_path)
            x_stabilization_path.CoordinateSystem = 'bed_relative'
            x_stabilization_path.Loop = self.x_relative_path_loop
            x_stabilization_path.InvertLoop = self.x_relative_path_invert_loop

        y_stabilization_path = StabilizationPath()
        y_stabilization_path.Axis = "Y"
        y_stabilization_path.Type = self.y_type
        if self.y_type == 'fixed_coordinate':
            y_stabilization_path.Path.append(self.y_fixed_coordinate)
            y_stabilization_path.CoordinateSystem = 'absolute'
        elif self.y_type == 'relative':
            y_stabilization_path.Path.append(self.y_relative)
            y_stabilization_path.CoordinateSystem = 'bed_relative'
        elif self.y_type == 'fixed_path':
            y_stabilization_path.Path = self.parse_csv_path(self.y_fixed_path)
            y_stabilization_path.CoordinateSystem = 'absolute'
            y_stabilization_path.Loop = self.y_fixed_path_loop
            y_stabilization_path.InvertLoop = self.y_fixed_path_invert_loop
        elif self.y_type == 'relative_path':
            y_stabilization_path.Path = self.parse_csv_path(self.y_relative_path)
            y_stabilization_path.CoordinateSystem = 'bed_relative'
            y_stabilization_path.Loop = self.y_relative_path_loop
            y_stabilization_path.InvertLoop = self.y_relative_path_invert_loop

        return dict(
            X=x_stabilization_path,
            Y=y_stabilization_path
        )

    @staticmethod
    def parse_csv_path(path_csv):
        """Converts a list of floats separated by commas into an array of floats."""
        path = []
        items = path_csv.split(',')
        for item in items:
            item = item.strip()
            if len(item) > 0:
                path.append(float(item))
        return path


class SnapshotPositionRestrictions(Settings):
    def __init__(self, restriction_type, shape, x, y, x2=None, y2=None, r=None, calculate_intersections=False):

        self.Type = restriction_type.lower()
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

        self.Type = restriction_type
        self.Shape = shape
        self.X = float(x)
        self.Y = float(y)
        self.X2 = float(x2)
        self.Y2 = float(y2)
        self.R = float(r)
        self.CalculateIntersections = calculate_intersections

    def to_dict(self):
        return {
            'Type': self.Type,
            'Shape': self.Shape,
            'X': self.X,
            'Y': self.Y,
            'X2': self.X2,
            'Y2': self.Y2,
            'R': self.R,
            'CalculateIntersections': self.CalculateIntersections
        }

    def get_intersections(self, x, y, previous_x, previous_y):
        if not self.CalculateIntersections:
            return False

        if x is None or y is None or previous_x is None or previous_y is None:
            return False

        if self.Shape == 'rect':
            intersections = utility.get_intersections_rectangle(previous_x, previous_y, x, y, self.X, self.Y, self.X2,
                                                                self.Y2)
        elif self.Shape == 'circle':
            intersections = utility.get_intersections_circle(previous_x, previous_y, x, y, self.X, self.Y, self.R)
        else:
            raise TypeError("SnapshotPosition shape must be 'rect' or 'circle'.")

        if not intersections:
            return False

        return intersections

    def is_in_position(self, x, y, tolerance):
        if x is None or y is None:
            return False

        if self.Shape == 'rect':
            return self.X <= x <= self.X2 and self.Y <= y <= self.Y2
        elif self.Shape == 'circle':
            lsq = math.pow(x - self.X, 2) + math.pow(y - self.Y, 2)
            rsq = math.pow(self.R, 2)
            return utility.is_close(lsq, rsq, tolerance) or lsq < rsq
        else:
            raise TypeError("SnapshotPosition shape must be 'rect' or 'circle'.")


class SnapshotProfile(ProfileSettings):
    ExtruderTriggerIgnoreValue = ""
    ExtruderTriggerRequiredValue = "trigger_on"
    ExtruderTriggerForbiddenValue = "forbidden"
    LayerTriggerType = 'layer'
    TimerTriggerType = 'timer'
    GcodeTriggerType = 'gcode'

    def __init__(self, name="New Snapshot Profile"):
        super(SnapshotProfile, self).__init__(name)
        self.is_default = False
        self.trigger_type = self.LayerTriggerType
        # timer trigger settings
        self.timer_trigger_seconds = 30
        # layer trigger settings
        self.layer_trigger_height = 0.0

        # Position Restrictions
        self.position_restrictions_enabled = False
        self.position_restrictions = []

        # Quality Settings
        self.require_zhop = False
        # Extruder State
        self.extruder_state_requirements_enabled = False
        self.trigger_on_extruding_start = None
        self.trigger_on_extruding = None
        self.trigger_on_primed = None
        self.trigger_on_retracting_start = None
        self.trigger_on_retracting = None
        self.trigger_on_partially_retracted = None
        self.trigger_on_retracted = None
        self.trigger_on_detracting_start = None
        self.trigger_on_detracting = None
        self.trigger_on_detracted = None
        self.feature_trigger_on_wipe = None
        # Feature Detection
        self.feature_restrictions_enabled = False
        self.feature_trigger_on_detract = False
        self.feature_trigger_on_retract = False
        self.feature_trigger_on_movement = False
        self.feature_trigger_on_z_movement = False
        self.feature_trigger_on_perimeters = True
        self.feature_trigger_on_small_perimeters = False
        self.feature_trigger_on_external_perimeters = False
        self.feature_trigger_on_infill = True
        self.feature_trigger_on_solid_infill = True
        self.feature_trigger_on_top_solid_infill = True
        self.feature_trigger_on_supports = False
        self.feature_trigger_on_bridges = False
        self.feature_trigger_on_gap_fills = True
        self.feature_trigger_on_first_layer = True
        self.feature_trigger_on_above_raft = False
        self.feature_trigger_on_ooze_shield = False
        self.feature_trigger_on_prime_pillar = True
        self.feature_trigger_on_normal_print_speed = False
        self.feature_trigger_on_skirt_brim = False
        self.feature_trigger_on_first_layer_travel = False
        # Lift and retract before move
        self.lift_before_move = True
        self.retract_before_move = True

        # Snapshot Cleanup
        self.cleanup_after_render_complete = True
        self.cleanup_after_render_fail = False

    @staticmethod
    def get_options():
        return {
            'trigger_types': [
                dict(value=SnapshotProfile.LayerTriggerType, name="Layer/Height"),
                dict(value=SnapshotProfile.TimerTriggerType, name="Timer"),
                dict(value=SnapshotProfile.GcodeTriggerType, name="Gcode")
            ],
            'position_restriction_shapes': [
                dict(value="rect", name="Rectangle"),
                dict(value="circle", name="Circle")
            ],
            'position_restriction_types': [
                dict(value="required", name="Must be inside"),
                dict(value="forbidden", name="Cannot be inside")
            ],
            'snapshot_extruder_trigger_options': [
                dict(value=SnapshotProfile.ExtruderTriggerIgnoreValue, name='Ignore', visible=True),
                dict(value=SnapshotProfile.ExtruderTriggerRequiredValue, name='Trigger', visible=True),
                dict(value=SnapshotProfile.ExtruderTriggerForbiddenValue, name='Forbidden', visible=True)
            ]
        }

    def get_extruder_trigger_value_string(self, value):
        if value is None:
            return self.ExtruderTriggerIgnoreValue
        elif value:
            return self.ExtruderTriggerRequiredValue
        elif not value:
            return self.ExtruderTriggerForbiddenValue

    def get_extruder_trigger_value(self, value):
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

    @staticmethod
    def get_trigger_position_restrictions(value):
        restrictions = []
        for restriction in value:
            restrictions.append(
                SnapshotPositionRestrictions(
                    restriction["Type"], restriction["Shape"],
                    restriction["X"], restriction["Y"],
                    restriction["X2"], restriction["Y2"],
                    restriction["R"], restriction["CalculateIntersections"]
                )
            )
        return restrictions

    @staticmethod
    def get_trigger_position_restrictions_value_string(values):
        restrictions = []
        for restriction in values:
            restrictions.append(restriction.to_dict())
        return restrictions


class RenderingProfile(ProfileSettings):
    def __init__(self, name="New Rendering Profile"):
        super(RenderingProfile, self).__init__(name)
        self.enabled = True
        self.fps_calculation_type = 'duration'
        self.run_length_seconds = 5
        self.fps = 30
        self.max_fps = 120.0
        self.min_fps = 2.0
        self.output_format = 'mp4'
        self.sync_with_timelapse = True
        self.bitrate = "8000K"
        self.post_roll_seconds = 0
        self.pre_roll_seconds = 0
        self.output_template = "{FAILEDFLAG}{FAILEDSEPARATOR}{GCODEFILENAME}_{PRINTENDTIME}"
        self.enable_watermark = False
        self.selected_watermark = ""
        self.overlay_text_template = ""
        self.overlay_font_path = ""
        self.overlay_font_size = 10
        self.overlay_text_pos = [10, 10]
        self.overlay_text_alignment = "left"  # Text alignment between lines in the overlay.
        self.overlay_text_valign = "top"  # Overall alignment of text box vertically.
        self.overlay_text_halign = "left"  # Overall alignment of text box horizontally.
        self.overlay_text_color = [255, 255, 255, 128]
        self.thread_count = 1

    @staticmethod
    def get_options():
        return {
            'rendering_file_templates': [
                "FAILEDFLAG",
                "FAILEDSTATE",
                "FAILEDSEPARATOR",
                "PRINTSTATE",
                "GCODEFILENAME",
                "DATETIMESTAMP",
                "PRINTENDTIME",
                "PRINTENDTIMESTAMP",
                "PRINTSTARTTIME",
                "PRINTSTARTTIMESTAMP",
                "SNAPSHOTCOUNT",
                "FPS"
            ],
            'overlay_text_templates': [
                "snapshot_number",
                "current_time",
                "time_elapsed",
            ],
            'overlay_text_alignment_options': [
                "left",
                "center",
                "right",
            ],
            'overlay_text_valign_options': [
                "top",
                "middle",
                "bottom",
            ],
            'overlay_text_halign_options': [
                "left",
                "center",
                "right",
            ],
            'rendering_fps_calculation_options': [
                dict(value='static', name='Static FPS'),
                dict(value='duration', name='Fixed Run Length')
            ],
            'rendering_output_format_options': [
                dict(value='avi', name='AVI'),
                dict(value='flv', name='FLV'),
                dict(value='gif', name='GIF'),
                dict(value='h264', name='H.264/MPEG-4 AVC'),
                dict(value='mp4', name='MP4 (libxvid)'),
                dict(value='mpeg', name='MPEG'),
                dict(value='vob', name='VOB'),
            ],
        }


class CameraProfile(ProfileSettings):
    def __init__(self, name="New Camera Profile"):
        super(CameraProfile, self).__init__(name)
        self.enabled = True
        self.camera_type = "webcam"
        self.gcode_camera_script = ""
        self.on_print_start_script = ""
        self.on_before_snapshot_script = ""
        self.external_camera_snapshot_script = ""
        self.on_after_snapshot_script = ""
        self.on_before_render_script = ""
        self.on_after_render_script = ""
        self.delay = 125
        self.timeout_ms = 5000
        self.apply_settings_before_print = False
        self.address = "http://127.0.0.1/webcam/"
        self.snapshot_request_template = "{camera_address}?action=snapshot"
        self.snapshot_transpose = ""
        self.ignore_ssl_error = False
        self.username = ""
        self.password = ""
        self.brightness = 128
        self.brightness_request_template = self.template_to_string(0, 0, 9963776, 1)
        self.contrast = 128
        self.contrast_request_template = self.template_to_string(0, 0, 9963777, 1)
        self.saturation = 128
        self.saturation_request_template = self.template_to_string(0, 0, 9963778, 1)
        self.white_balance_auto = True
        self.white_balance_auto_request_template = self.template_to_string(0, 0, 9963788, 1)
        self.gain = 100
        self.gain_request_template = self.template_to_string(0, 0, 9963795, 1)
        self.powerline_frequency = 60
        self.powerline_frequency_request_template = self.template_to_string(0, 0, 9963800, 1)
        self.white_balance_temperature = 4000
        self.white_balance_temperature_request_template = self.template_to_string(0, 0, 9963802, 1)
        self.sharpness = 128
        self.sharpness_request_template = self.template_to_string(0, 0, 9963803, 1)
        self.backlight_compensation_enabled = False
        self.backlight_compensation_enabled_request_template = self.template_to_string(0, 0, 9963804, 1)
        self.exposure_type = 1
        self.exposure_type_request_template = self.template_to_string(0, 0, 10094849, 1)
        self.exposure = 250
        self.exposure_request_template = self.template_to_string(0, 0, 10094850, 1)
        self.exposure_auto_priority_enabled = True
        self.exposure_auto_priority_enabled_request_template = self.template_to_string(0, 0, 10094851, 1)
        self.pan = 0
        self.pan_request_template = self.template_to_string(0, 0, 10094856, 1)
        self.tilt = 0
        self.tilt_request_template = self.template_to_string(0, 0, 10094857, 1)
        self.autofocus_enabled = True
        self.autofocus_enabled_request_template = self.template_to_string(0, 0, 10094860, 1)
        self.focus = 28
        self.focus_request_template = self.template_to_string(0, 0, 10094858, 1)
        self.zoom = 100
        self.zoom_request_template = self.template_to_string(0, 0, 10094861, 1)
        self.led1_mode = 'auto'
        self.led1_mode_request_template = self.template_to_string(0, 0, 168062213, 1)
        self.led1_frequency = 0
        self.led1_frequency_request_template = self.template_to_string(0, 0, 168062214, 1)
        self.jpeg_quality = 90
        self.jpeg_quality_request_template = self.template_to_string(0, 0, 1, 3)

    @staticmethod
    def template_to_string(destination, plugin, setting_id, group):
        return (
            "{camera_address}?action=command&"
            + "dest=" + str(destination)
            + "&plugin=" + str(plugin)
            + "&id=" + str(setting_id)
            + "&group=" + str(group)
            + "&value={value}"
        )

    @staticmethod
    def get_options():
        return {
            'camera_powerline_frequency_options': [
                dict(value='50', name='50 HZ (Europe, China, India, etc)'),
                dict(value='60', name='60 HZ (North/South America, Japan, etc)')
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
            'snapshot_transpose_options': [
                dict(value='', name='None'),
                dict(value='flip_left_right', name='Flip Left and Right'),
                dict(value='flip_top_bottom', name='Flip Top and Bottom'),
                dict(value='rotate_90', name='Rotate 90 Degrees'),
                dict(value='rotate_180', name='Rotate 180 Degrees'),
                dict(value='rotate_270', name='Rotate 270 Degrees'),
                dict(value='transpose', name='Transpose')
            ],
            'camera_type_options': [
                dict(value='webcam', name='Webcam'),
                dict(value='external-script', name='External Camera - Script'),
                dict(value='printer-gcode', name='Gcode Camera (built into printer)')
            ],
        }


class DebugProfile(ProfileSettings):

    def __init__(self, name="New Debug Profile"):
        super(DebugProfile, self).__init__(name)
        # Configure the logger if it has not been created

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
        self.gcode_received_all = False


class MainSettings(Settings):
    def __init__(self, plugin_version):
        # Main Settings
        self.show_navbar_icon = True
        self.show_navbar_when_not_printing = True
        self.is_octolapse_enabled = True
        self.auto_reload_latest_snapshot = True
        self.auto_reload_frames = 5
        self.show_position_state_changes = False
        self.show_position_changes = False
        self.show_extruder_state_changes = False
        self.show_trigger_state_changes = False
        self.show_real_snapshot_time = False
        self.cancel_print_on_startup_error = True
        self.platform = sys.platform,


class ProfileOptions(Settings):
    def __init__(self):
        self.printer = PrinterProfile.get_options()
        self.stabilization = StabilizationProfile.get_options()
        self.snapshot = SnapshotProfile.get_options()
        self.rendering = RenderingProfile.get_options()
        self.camera = CameraProfile.get_options()
        self.debug = DebugProfile.get_options()


class ProfileDefaults(Settings):
    def __init__(self):
        self.printer = PrinterProfile("Default Printer")
        self.stabilization = StabilizationProfile("Default Stabilization")
        self.snapshot = SnapshotProfile("Default Snapshot")
        self.rendering = RenderingProfile("Default Rendering")
        self.camera = CameraProfile("Default Camera")
        self.debug = DebugProfile("Default Debug")


class Profiles(Settings):
    def __init__(self):
        self.options = ProfileOptions()
        # create default profiles
        self.defaults = ProfileDefaults()

        # printers is initially empty - user must select a printer
        self.printers = {}
        self.current_printer_profile_guid = None

        self.current_stabilization_profile_guid = self.defaults.stabilization.guid
        self.stabilizations = {self.defaults.stabilization.guid: self.defaults.stabilization}

        self.current_snapshot_profile_guid = self.defaults.snapshot.guid
        self.snapshots = {self.defaults.snapshot.guid: self.defaults.snapshot}

        self.current_rendering_profile_guid = self.defaults.rendering.guid
        self.renderings = {self.defaults.rendering.guid: self.defaults.rendering}

        # there is no current camera profile guid.
        self.current_camera_profile_guid = self.defaults.camera.guid
        self.cameras = {self.defaults.camera.guid: self.defaults.camera}

        self.current_debug_profile_guid = self.defaults.debug.guid
        self.debug = {self.defaults.debug.guid: self.defaults.debug}

    def get_profiles_dict(self):
        profiles_dict = {
            'current_printer_profile_guid': self.current_printer_profile_guid,
            'current_stabilization_profile_guid': self.current_stabilization_profile_guid,
            'current_snapshot_profile_guid': self.current_snapshot_profile_guid,
            'current_rendering_profile_guid': self.current_rendering_profile_guid,
            'current_camera_profile_guid': self.current_camera_profile_guid,
            'current_debug_profile_guid': self.current_debug_profile_guid,
            'printers': [],
            'stabilizations': [],
            'snapshots': [],
            'renderings': [],
            'cameras': [],
            'debug': []
        }

        for key, printer in self.printers.items():
            profiles_dict["printers"].append({
                "name": printer.name,
                "guid": printer.guid,
                "has_been_saved_by_user": printer.has_been_saved_by_user
            })

        for key, stabilization in self.stabilizations.items():
            profiles_dict["stabilizations"].append({
                "name": stabilization.name,
                "guid": stabilization.guid
            })

        for key, snapshot in self.snapshots.items():
            profiles_dict["snapshots"].append({
                "name": snapshot.name,
                "guid": snapshot.guid
            })

        for key, rendering in self.renderings.items():
            profiles_dict["renderings"].append({
                "name": rendering.name,
                "guid": rendering.guid
            })

        for key, camera in self.cameras.items():
            profiles_dict["cameras"].append({
                "name": camera.name,
                "guid": camera.guid,
                "enabled": camera.enabled
            })

        for key, debugProfile in self.debug.items():
            profiles_dict["debug"].append({
                "name": debugProfile.name,
                "guid": debugProfile.guid
            })
        return profiles_dict

    def current_printer(self):
        if self.current_printer_profile_guid is None or self.current_printer_profile_guid not in self.printers:
            return None
        return self.printers[self.current_printer_profile_guid]

    def current_stabilization(self):
        if self.current_stabilization_profile_guid in self.stabilizations:
            return self.stabilizations[self.current_stabilization_profile_guid]
        return self.defaults.stabilization

    def current_snapshot(self):
        if self.current_snapshot_profile_guid in self.snapshots:
            return self.snapshots[self.current_snapshot_profile_guid]
        return self.defaults.snapshot

    def current_rendering(self):
        if self.current_rendering_profile_guid in self.renderings:
            return self.renderings[self.current_rendering_profile_guid]
        return self.defaults.rendering

    def current_camera_profile(self):
        if self.current_camera_profile_guid in self.cameras:
            return self.cameras[self.current_camera_profile_guid]
        return self.defaults.camera

    def current_debug_profile(self):
        if self.current_debug_profile_guid in self.debug:
            return self.debug[self.current_debug_profile_guid]
        return self.defaults.debug

    def active_cameras(self):
        # todo: make more pythonic
        _active_cameras = []
        for key in self.cameras:
            _current_camera = self.cameras[key]
            if _current_camera.enabled:
                _active_cameras.append(_current_camera)
        return _active_cameras

    # Add/Update/Remove/set current profile

    def add_update_profile(self, profile_type, profile):
        # check the guid.  If it is null or empty, assign a new value.
        guid = profile["guid"]
        if guid is None or guid == "":
            guid = str(uuid.uuid4())
            profile["guid"] = guid

        if profile_type == "Printer":
            new_profile = PrinterProfile.create_from(profile)
            self.printers[guid] = new_profile
            if len(self.printers) == 1:
                self.current_printer_profile_guid = new_profile.guid
        elif profile_type == "Stabilization":
            new_profile = StabilizationProfile.create_from(profile)
            self.stabilizations[guid] = new_profile
        elif profile_type == "Snapshot":
            new_profile = SnapshotProfile.create_from(profile)
            self.snapshots[guid] = new_profile
        elif profile_type == "Rendering":
            new_profile = RenderingProfile.create_from(profile)
            self.renderings[guid] = new_profile
        elif profile_type == "Camera":
            new_profile = CameraProfile.create_from(profile)
            self.cameras[guid] = new_profile
        elif profile_type == "Debug":
            new_profile = DebugProfile.create_from(profile)
            self.debug[guid] = new_profile
        else:
            raise ValueError('An unknown profile type ' +
                             str(profile_type) + ' was received.')

        return new_profile

    def remove_profile(self, profile_type, guid):

        if profile_type == "Printer":
            if self.current_printer_profile_guid == guid:
                return False
            del self.printers[guid]
        elif profile_type == "Stabilization":
            if self.current_stabilization_profile_guid == guid:
                return False
            del self.stabilizations[guid]
        elif profile_type == "Snapshot":
            if self.current_snapshot_profile_guid == guid:
                return False
            del self.snapshots[guid]
        elif profile_type == "Rendering":
            if self.current_rendering_profile_guid == guid:
                return False
            del self.renderings[guid]
        elif profile_type == "Camera":
            del self.cameras[guid]
        elif profile_type == "Debug":
            if self.current_debug_profile_guid == guid:
                return False
            del self.debug[guid]
        else:
            raise ValueError('An unknown profile type ' +
                             str(profile_type) + ' was received.')

        return True

    def set_current_profile(self, profile_type, guid):
        if profile_type == "Printer":
            if guid == "":
                guid = None
            self.current_printer_profile_guid = guid
        elif profile_type == "Stabilization":
            self.current_stabilization_profile_guid = guid
        elif profile_type == "Snapshot":
            self.current_snapshot_profile_guid = guid
        elif profile_type == "Rendering":
            self.current_rendering_profile_guid = guid
        elif profile_type == "Camera":
            self.current_camera_profile_guid = guid
        elif profile_type == "Debug":
            self.current_debug_profile_guid = guid
        else:
            raise ValueError('An unknown profile type ' +
                             str(profile_type) + ' was received.')

    def update(self, iterable, **kwargs):
        try:
            item_to_iterate = iterable
            if not isinstance(iterable, collections.Iterable):
                item_to_iterate = iterable.__dict__

            for key, value in item_to_iterate.items():
                class_item = getattr(self, key, '{octolapse_no_property_found}')
                if not (isinstance(class_item, str) and class_item == '{octolapse_no_property_found}'):
                    if key == 'printers':
                        self.printers = {}
                        for profile_key, profile_value in value.items():
                            self.printers[profile_key] = PrinterProfile.create_from(profile_value)
                    elif key == 'stabilizations':
                        self.stabilizations = {}
                        for profile_key, profile_value in value.items():
                            self.stabilizations[profile_key] = StabilizationProfile.create_from(profile_value)
                    elif key == 'snapshots':
                        self.snapshots = {}
                        for profile_key, profile_value in value.items():
                            self.snapshots[profile_key] = SnapshotProfile.create_from(profile_value)
                    elif key == 'renderings':
                        self.renderings = {}
                        for profile_key, profile_value in value.items():
                            self.renderings[profile_key] = RenderingProfile.create_from(profile_value)
                    elif key == 'cameras':
                        self.cameras = {}
                        for profile_key, profile_value in value.items():
                            self.cameras[profile_key] = CameraProfile.create_from(profile_value)
                    elif key == 'debug':
                        self.debug = {}
                        for profile_key, profile_value in value.items():
                            self.debug[profile_key] = DebugProfile.create_from(profile_value)
                    elif isinstance(class_item, Settings):
                        class_item.update(value)
                    else:
                        self.__dict__[key] = self._try_convert_value(class_item, value)
        except Exception as e:
            raise e


class OctolapseSettings(Settings):
    DefaultDebugProfile = None
    get_debug_function = None
    Logger = None

    def __init__(self, logging_path, plugin_version="unknown", get_debug_function=None):
        self.version = plugin_version
        self.main_settings = MainSettings(plugin_version)
        self.profiles = Profiles()
        if get_debug_function is not None and OctolapseSettings.Logger is None:
            # create the logger if it doesn't exist
            OctolapseSettings.Logger = log.Logger(logging_path, get_debug_function)

    def save(self, file_path):
        self.save_as_json(file_path)

    @classmethod
    def create_from(cls, logging_path, plugin_version, iterable=(), get_debug_function=None, **kwargs):
        new_object = cls(logging_path, plugin_version,get_debug_function=get_debug_function)
        new_object.update(iterable, **kwargs)
        return new_object

    @staticmethod
    def from_json(logging_path, plugin_version, json_string):
        data = json.loads(json_string)
        return OctolapseSettings.create_from(logging_path, plugin_version, data)


##################################################################################
## ToDo: Move these things into a separate file
##################################################################################
class PrintFeatureSetting(Settings):
    def __init__(self, speed_callback, layer_name, initial_layer_name, speed, under_speed, enabled,
                 enabled_for_slow_layer):
        self.layer_name = layer_name
        self.slow_layer_name = initial_layer_name
        self.speed = speed
        self.under_speed = under_speed
        self._speed_callback = speed_callback
        self.enabled = enabled
        self.enabled_for_slow_layer = enabled_for_slow_layer
        self.calculated_speed = None
        self.calculated_layer_name = layer_name
        self.triggered = False
        self.detected = False

    def update(self, speed, num_slow_layers, layer_num, tolerance):
        self.detected = False
        self.triggered = False
        if layer_num == 0:
            layer_num = 1
        self.calculated_speed, self.calculated_layer_name = self._speed_callback(
            self.layer_name, self.slow_layer_name, self.speed, self.under_speed, num_slow_layers, layer_num
        )

        if self.calculated_speed is not None and utility.is_close(speed, self.calculated_speed, tolerance):
            self.detected = True
            if (self.enabled and num_slow_layers < layer_num) or self.enabled_for_slow_layer:
                self.triggered = True


def calculate_speed(layer_name, slow_layer_name, speed, under_speed, num_slow_layers, layer_num, *args, **kwargs):
    if speed is None:
        return None, layer_name

    if (
        layer_num is None
        or num_slow_layers < 1
        or layer_num > num_slow_layers
        or speed == under_speed
        or under_speed is None
    ):
        return speed, layer_name
    # calculate an underspeed
    return (
        under_speed + ((layer_num - 1) * (speed - under_speed) / num_slow_layers)
        , slow_layer_name
    )


def calculate_speed_slic3r_pe(layer_name, slow_layer_name, speed, under_speed, num_slow_layers, layer_num, *args,
                              **kwargs):
    return calculate_speed(layer_name, slow_layer_name, speed, under_speed, 1, layer_num, *args, **kwargs)


def calculate_speed_cura(layer_name, slow_layer_name, speed, under_speed, num_slow_layers, layer_num, *args, **kwargs):
    return calculate_speed(layer_name, slow_layer_name, speed, under_speed, num_slow_layers, layer_num, *args, **kwargs)


def calculate_speed_simplify_3d(layer_name, slow_layer_name, speed, under_speed, num_slow_layers, layer_num, *args,
                                **kwargs):
    return calculate_speed(layer_name, slow_layer_name, speed, under_speed, num_slow_layers, layer_num, *args, **kwargs)


class SlicerPrintFeatures(Settings):
    def __init__(self, printer_profile, snapshot_profile):
        assert (isinstance(printer_profile, PrinterProfile))
        assert (isinstance(snapshot_profile, SnapshotProfile))

        self.speed_units = printer_profile.axis_speed_display_units
        self.num_slow_layers = printer_profile.num_slow_layers
        self.speed_tolerance = printer_profile.get_speed_tolerance_for_slicer_type()
        self.feature_detection_enabled = snapshot_profile.feature_restrictions_enabled
        self.features = []

        if printer_profile.slicer_type == 'other':
            self.create_other_slicer_feature_list(printer_profile, snapshot_profile)
        elif printer_profile.slicer_type == 'slic3r-pe':
            self.create_slic3r_pe_feature_list(printer_profile, snapshot_profile)
        elif printer_profile.slicer_type == 'cura':
            self.create_cura_feature_list(printer_profile, snapshot_profile)
        elif printer_profile.slicer_type == 'simplify-3d':
            self.create_simplify_3d_feature_list(printer_profile, snapshot_profile)

    def create_other_slicer_feature_list(self, printer_profile, snapshot_profile):
        movement_speed = printer_profile.get_speed_for_slicer_type(printer_profile.movement_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed,
                "Movement",
                "Movement",
                movement_speed,
                movement_speed,
                snapshot_profile.feature_trigger_on_movement,
                snapshot_profile.feature_trigger_on_movement))

        z_movement_speed = printer_profile.get_speed_for_slicer_type(printer_profile.z_hop_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed,
                "Z Movement",
                "Z Movement",
                z_movement_speed,
                z_movement_speed,
                snapshot_profile.feature_trigger_on_z_movement,
                snapshot_profile.feature_trigger_on_z_movement))

        retract_speed = printer_profile.get_speed_for_slicer_type(printer_profile.retract_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Retraction",
                "Retraction",
                retract_speed,
                retract_speed,
                snapshot_profile.feature_trigger_on_retract,
                snapshot_profile.feature_trigger_on_retract))
        detract_speed = printer_profile.get_speed_for_slicer_type(printer_profile.detract_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Detraction",
                "Detraction",
                detract_speed,
                detract_speed,
                snapshot_profile.feature_trigger_on_detract,
                snapshot_profile.feature_trigger_on_detract))
        print_speed = printer_profile.get_speed_for_slicer_type(printer_profile.print_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Normal Print Speed",
                "Normal Print Speed",
                print_speed,
                print_speed,
                snapshot_profile.feature_trigger_on_normal_print_speed,
                snapshot_profile.feature_trigger_on_normal_print_speed))
        perimeter_speed = printer_profile.get_speed_for_slicer_type(printer_profile.perimeter_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Perimeters",
                "Perimeters",
                perimeter_speed,
                perimeter_speed,
                snapshot_profile.feature_trigger_on_perimeters,
                snapshot_profile.feature_trigger_on_perimeters))
        small_perimeter_speed = printer_profile.get_speed_for_slicer_type(printer_profile.small_perimeter_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Small Perimeters",
                "Small Perimeters",
                small_perimeter_speed,
                small_perimeter_speed,
                snapshot_profile.feature_trigger_on_small_perimeters,
                snapshot_profile.feature_trigger_on_small_perimeters))
        external_perimeter_speed = printer_profile.get_speed_for_slicer_type(printer_profile.external_perimeter_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "External Perimeters",
                "External Perimeters",
                external_perimeter_speed,
                external_perimeter_speed,
                snapshot_profile.feature_trigger_on_external_perimeters,
                snapshot_profile.feature_trigger_on_external_perimeters))

        infill_speed = printer_profile.get_speed_for_slicer_type(printer_profile.infill_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Infill",
                "Infill",
                infill_speed,
                infill_speed,
                snapshot_profile.feature_trigger_on_infill,
                snapshot_profile.feature_trigger_on_infill))

        solid_infill_speed = printer_profile.get_speed_for_slicer_type(printer_profile.solid_infill_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Solid Infill",
                "Solid Infill",
                solid_infill_speed,
                solid_infill_speed,
                snapshot_profile.feature_trigger_on_solid_infill,
                snapshot_profile.feature_trigger_on_solid_infill))

        top_solid_infill_speed = printer_profile.get_speed_for_slicer_type(printer_profile.top_solid_infill_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Top Solid Infill",
                "Top Solid Infill",
                top_solid_infill_speed,
                top_solid_infill_speed,
                snapshot_profile.feature_trigger_on_top_solid_infill,
                snapshot_profile.feature_trigger_on_top_solid_infill))

        support_speed = printer_profile.get_speed_for_slicer_type(printer_profile.support_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Supports",
                "Supports",
                support_speed,
                support_speed,
                snapshot_profile.feature_trigger_on_supports,
                snapshot_profile.feature_trigger_on_supports))

        bridge_speed = printer_profile.get_speed_for_slicer_type(printer_profile.bridge_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Bridges",
                "Bridges",
                bridge_speed,
                bridge_speed,
                snapshot_profile.feature_trigger_on_bridges,
                snapshot_profile.feature_trigger_on_bridges))

        gap_fill_speed = printer_profile.get_speed_for_slicer_type(printer_profile.gap_fill_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Gap Fills",
                "Gap Fills",
                gap_fill_speed,
                gap_fill_speed,
                snapshot_profile.feature_trigger_on_gap_fills,
                snapshot_profile.feature_trigger_on_gap_fills))

        first_layer_speed = printer_profile.get_speed_for_slicer_type(printer_profile.first_layer_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "First Layer",
                "First Layer",
                first_layer_speed,
                first_layer_speed,
                snapshot_profile.feature_trigger_on_first_layer,
                snapshot_profile.feature_trigger_on_first_layer))

        above_raft_speed = printer_profile.get_speed_for_slicer_type(printer_profile.above_raft_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Above Raft",
                "Above Raft",
                above_raft_speed,
                above_raft_speed,
                snapshot_profile.feature_trigger_on_above_raft,
                snapshot_profile.feature_trigger_on_above_raft))

        ooze_shield_speed = printer_profile.get_speed_for_slicer_type(printer_profile.ooze_shield_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Ooze Shield",
                "Ooze Shield",
                ooze_shield_speed,
                ooze_shield_speed,
                snapshot_profile.feature_trigger_on_ooze_shield,
                snapshot_profile.feature_trigger_on_ooze_shield))

        prime_pillar_speed = printer_profile.get_speed_for_slicer_type(printer_profile.prime_pillar_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Prime Pillar",
                "Prime Pillar",
                prime_pillar_speed,
                prime_pillar_speed,
                snapshot_profile.feature_trigger_on_prime_pillar,
                snapshot_profile.feature_trigger_on_prime_pillar))

        skirt_brim_speed = printer_profile.get_speed_for_slicer_type(printer_profile.above_raft_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Skirt/Brim",
                "Skirt/Brim",
                skirt_brim_speed,
                skirt_brim_speed,
                snapshot_profile.feature_trigger_on_skirt_brim,
                snapshot_profile.feature_trigger_on_skirt_brim))

    def create_slic3r_pe_feature_list(self, printer_profile, snapshot_profile):

        # The retract and detract speeds are rounded to the nearest int
        retract_speed = printer_profile.get_speed_for_slicer_type(printer_profile.retract_speed, "retract_speed")
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Retraction",
                "Retraction",
                retract_speed,
                retract_speed,
                snapshot_profile.feature_trigger_on_retract,
                snapshot_profile.feature_trigger_on_retract))

        detract_speed = printer_profile.get_speed_for_slicer_type(printer_profile.detract_speed, "detract_speed")
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Detraction",
                "Detraction",
                detract_speed,
                detract_speed,
                snapshot_profile.feature_trigger_on_detract,
                snapshot_profile.feature_trigger_on_detract))

        perimeter_speed = printer_profile.get_speed_for_slicer_type(printer_profile.perimeter_speed)
        perimeter_underspeed = printer_profile.get_speed_by_multiple_for_slicer_type(printer_profile.perimeter_speed,
                                                                                     printer_profile.first_layer_speed_multiplier)
        # Perimeter Speed Feature
        perimeter_speed_feature = PrintFeatureSetting(
            calculate_speed_slic3r_pe,
            "Perimeters",
            "Perimeters",
            perimeter_speed,
            perimeter_speed,
            snapshot_profile.feature_trigger_on_perimeters,
            snapshot_profile.feature_trigger_on_perimeters)
        if perimeter_underspeed:
            # there is a first layer speed multiplier so scale the current speed
            perimeter_speed_feature.slow_layer_name = "First Layer Perimeters"
            perimeter_speed_feature.under_speed = perimeter_underspeed
            perimeter_speed_feature.enabled_for_slow_layer = snapshot_profile.feature_trigger_on_perimeters and snapshot_profile.feature_trigger_on_first_layer
        self.features.append(perimeter_speed_feature)

        # Small Perimeter Feature
        small_perimeter_speed = printer_profile.get_speed_for_slicer_type(printer_profile.small_perimeter_speed)
        small_perimeter_underspeed = printer_profile.get_speed_by_multiple_for_slicer_type(
            printer_profile.small_perimeter_speed, printer_profile.first_layer_speed_multiplier)
        small_perimeter_speed_feature = PrintFeatureSetting(
            calculate_speed_slic3r_pe,
            "Small Perimeters",
            "Small Perimeters",
            small_perimeter_speed,
            small_perimeter_speed,
            snapshot_profile.feature_trigger_on_small_perimeters,
            snapshot_profile.feature_trigger_on_small_perimeters)
        if small_perimeter_underspeed is not None:
            # there is a first layer speed multiplier so scale the current speed
            small_perimeter_speed_feature.slow_layer_name = "First Layer Small Perimeters"
            small_perimeter_speed_feature.under_speed = small_perimeter_underspeed
            small_perimeter_speed_feature.enabled_for_slow_layer = snapshot_profile.feature_trigger_on_small_perimeters and snapshot_profile.feature_trigger_on_first_layer
        self.features.append(small_perimeter_speed_feature)

        # External Perimeter Feature
        external_perimeter_speed = printer_profile.get_speed_for_slicer_type(printer_profile.external_perimeter_speed)
        external_perimeter_underspeed = printer_profile.get_speed_by_multiple_for_slicer_type(
            printer_profile.external_perimeter_speed, printer_profile.first_layer_speed_multiplier)
        external_perimeter_speed_feature = PrintFeatureSetting(
            calculate_speed_slic3r_pe,
            "External Perimeters",
            "External Perimeters",
            external_perimeter_speed,
            external_perimeter_speed,
            snapshot_profile.feature_trigger_on_external_perimeters,
            snapshot_profile.feature_trigger_on_external_perimeters)
        if external_perimeter_underspeed is not None:
            # there is a first layer speed multiplier so scale the current speed
            external_perimeter_speed_feature.slow_layer_name = "First Layer External Perimeters"
            external_perimeter_speed_feature.under_speed = external_perimeter_underspeed
            external_perimeter_speed_feature.enabled_for_slow_layer = snapshot_profile.feature_trigger_on_external_perimeters and snapshot_profile.feature_trigger_on_first_layer
        self.features.append(external_perimeter_speed_feature)

        # infill Feature
        infill_speed = printer_profile.get_speed_for_slicer_type(printer_profile.infill_speed)
        infill_underspeed = printer_profile.get_speed_by_multiple_for_slicer_type(printer_profile.infill_speed,
                                                                                  printer_profile.first_layer_speed_multiplier)
        infill_speed_feature = PrintFeatureSetting(
            calculate_speed_slic3r_pe,
            "Infill",
            "Infill",
            infill_speed,
            infill_speed,
            snapshot_profile.feature_trigger_on_infill,
            snapshot_profile.feature_trigger_on_infill)
        if infill_underspeed is not None:
            # there is a first layer speed multiplier so scale the current speed
            infill_speed_feature.slow_layer_name = "First Layer Infill"
            infill_speed_feature.under_speed = infill_underspeed
            infill_speed_feature.enabled_for_slow_layer = snapshot_profile.feature_trigger_on_infill and snapshot_profile.feature_trigger_on_first_layer
        self.features.append(infill_speed_feature)

        # solid_infill Feature
        solid_infill_speed = printer_profile.get_speed_for_slicer_type(printer_profile.solid_infill_speed)
        solid_infill_underspeed = printer_profile.get_speed_by_multiple_for_slicer_type(
            printer_profile.solid_infill_speed, printer_profile.first_layer_speed_multiplier)
        solid_infill_speed_feature = PrintFeatureSetting(
            calculate_speed_slic3r_pe,
            "Solid Infill",
            "Solid Infill",
            solid_infill_speed,
            solid_infill_speed,
            snapshot_profile.feature_trigger_on_solid_infill,
            snapshot_profile.feature_trigger_on_solid_infill)
        if solid_infill_underspeed is not None:
            # there is a first layer speed multiplier so scale the current speed
            solid_infill_speed_feature.slow_layer_name = "First Layer Solid Infill"
            solid_infill_speed_feature.under_speed = solid_infill_underspeed
            solid_infill_speed_feature.enabled_for_slow_layer = snapshot_profile.feature_trigger_on_solid_infill and snapshot_profile.feature_trigger_on_first_layer
        self.features.append(solid_infill_speed_feature)

        top_solid_infill_speed = printer_profile.get_speed_for_slicer_type(printer_profile.top_solid_infill_speed)
        top_solid_infill_underspeed = printer_profile.get_speed_by_multiple_for_slicer_type(
            printer_profile.top_solid_infill_speed, printer_profile.first_layer_speed_multiplier)
        # top top_solid_infill Feature
        top_solid_infill_speed_feature = PrintFeatureSetting(
            calculate_speed_slic3r_pe,
            "Top Solid Infill",
            "Top Solid Infill",
            top_solid_infill_speed,
            top_solid_infill_speed,
            snapshot_profile.feature_trigger_on_top_solid_infill,
            snapshot_profile.feature_trigger_on_top_solid_infill)
        if top_solid_infill_underspeed is not None:
            # there is a first layer speed multiplier so scale the current speed
            top_solid_infill_speed_feature.slow_layer_name = "First Layer Top Solid Infill"
            top_solid_infill_speed_feature.under_speed = top_solid_infill_underspeed
            top_solid_infill_speed_feature.enabled_for_slow_layer = snapshot_profile.feature_trigger_on_top_solid_infill and snapshot_profile.feature_trigger_on_first_layer
        self.features.append(top_solid_infill_speed_feature)

        # support Feature
        support_speed = printer_profile.get_speed_for_slicer_type(printer_profile.support_speed)
        support_underspeed = printer_profile.get_speed_by_multiple_for_slicer_type(printer_profile.support_speed,
                                                                                   printer_profile.first_layer_speed_multiplier)
        support_speed_feature = PrintFeatureSetting(
            calculate_speed_slic3r_pe,
            "Supports",
            "Supports",
            support_speed,
            support_speed,
            snapshot_profile.feature_trigger_on_supports,
            snapshot_profile.feature_trigger_on_supports)
        if support_underspeed is not None:
            # there is a first layer speed multiplier so scale the current speed
            support_speed_feature.slow_layer_name = "First Layer Supports"
            support_speed_feature.under_speed = support_underspeed
            support_speed_feature.enabled_for_slow_layer = snapshot_profile.feature_trigger_on_supports and snapshot_profile.feature_trigger_on_first_layer
        self.features.append(support_speed_feature)

        # bridge Feature
        bridge_speed = printer_profile.get_speed_for_slicer_type(printer_profile.bridge_speed)
        bridge_speed_feature = PrintFeatureSetting(
            calculate_speed_slic3r_pe,
            "Bridges",
            "Bridges",
            bridge_speed,
            bridge_speed,
            snapshot_profile.feature_trigger_on_bridges,
            snapshot_profile.feature_trigger_on_bridges)
        self.features.append(bridge_speed_feature)

        # gaps Feature
        gap_fill_speed = printer_profile.get_speed_for_slicer_type(printer_profile.gap_fill_speed)
        gap_fill_underspeed = printer_profile.get_speed_by_multiple_for_slicer_type(printer_profile.gap_fill_speed,
                                                                                    printer_profile.first_layer_speed_multiplier)
        gap_fill_speed_feature = PrintFeatureSetting(
            calculate_speed_slic3r_pe,
            "Gaps",
            "Gaps",
            gap_fill_speed,
            gap_fill_speed,
            snapshot_profile.feature_trigger_on_gap_fills,
            snapshot_profile.feature_trigger_on_gap_fills)
        if gap_fill_underspeed is not None:
            # there is a first layer speed multiplier so scale the current speed
            gap_fill_speed_feature.slow_layer_name = "First Layer Gaps"
            gap_fill_speed_feature.under_speed = gap_fill_underspeed
            gap_fill_speed_feature.enabled_for_slow_layer = snapshot_profile.feature_trigger_on_gap_fills and snapshot_profile.feature_trigger_on_first_layer
        self.features.append(gap_fill_speed_feature)

        movement_speed = printer_profile.get_speed_for_slicer_type(printer_profile.movement_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Movement",
                "Movement",
                movement_speed,
                movement_speed,
                snapshot_profile.feature_trigger_on_movement,
                snapshot_profile.feature_trigger_on_movement))

        wipe_speed = printer_profile.get_speed_for_slicer_type(printer_profile.movement_speed * 0.8)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_slic3r_pe,
                "Wipe",
                "Wipe",
                wipe_speed,
                wipe_speed,
                snapshot_profile.feature_trigger_on_wipe,
                snapshot_profile.feature_trigger_on_wipe))

        if printer_profile.first_layer_speed_multiplier is None:
            first_layer_speed = printer_profile.get_speed_for_slicer_type(printer_profile.first_layer_speed)
            self.features.append(
                PrintFeatureSetting(
                    calculate_speed_slic3r_pe,
                    "First Layer",
                    "First Layer Speed",
                    first_layer_speed,
                    first_layer_speed,
                    snapshot_profile.feature_trigger_on_first_layer,
                    snapshot_profile.feature_trigger_on_first_layer))

    def create_cura_feature_list(self, printer_profile, snapshot_profile):
        print_speed = printer_profile.get_speed_for_slicer_type(printer_profile.print_speed)
        slow_layer_speed = printer_profile.get_speed_for_slicer_type(printer_profile.first_layer_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_cura,
                "Print Speed",
                "Slow Layer Print Speed",
                print_speed,
                slow_layer_speed,
                snapshot_profile.feature_trigger_on_normal_print_speed,
                snapshot_profile.feature_trigger_on_normal_print_speed and snapshot_profile.feature_trigger_on_first_layer))

        retract_speed = printer_profile.get_speed_for_slicer_type(printer_profile.retract_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_cura,
                "Retract",
                "Retract",
                retract_speed,
                retract_speed,
                snapshot_profile.feature_trigger_on_retract,
                snapshot_profile.feature_trigger_on_retract and snapshot_profile.feature_trigger_on_first_layer))

        prime_speed = printer_profile.get_speed_for_slicer_type(printer_profile.detract_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_cura,
                "Prime",
                "Prime",
                prime_speed,
                prime_speed,
                snapshot_profile.feature_trigger_on_detract,
                snapshot_profile.feature_trigger_on_detract and snapshot_profile.feature_trigger_on_first_layer))

        infill_speed = printer_profile.get_speed_for_slicer_type(printer_profile.infill_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_cura,
                "Infill",
                "Slow Layer Infill",
                infill_speed,
                slow_layer_speed,
                snapshot_profile.feature_trigger_on_infill,
                snapshot_profile.feature_trigger_on_infill and snapshot_profile.feature_trigger_on_first_layer))

        external_perimeter_speed = printer_profile.get_speed_for_slicer_type(printer_profile.external_perimeter_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_cura,
                "Outer Wall",
                "Slow Layer Outer Wall",
                external_perimeter_speed,
                slow_layer_speed,
                snapshot_profile.feature_trigger_on_external_perimeters,
                snapshot_profile.feature_trigger_on_external_perimeters and snapshot_profile.feature_trigger_on_first_layer))

        perimeter_speed = printer_profile.get_speed_for_slicer_type(printer_profile.perimeter_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_cura,
                "Inner Wall",
                "Slow Layer Inner Wall",
                perimeter_speed,
                slow_layer_speed,
                snapshot_profile.feature_trigger_on_perimeters,
                snapshot_profile.feature_trigger_on_perimeters and snapshot_profile.feature_trigger_on_first_layer))

        top_solid_infill_speed = printer_profile.get_speed_for_slicer_type(printer_profile.top_solid_infill_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_cura,
                "Top/Bottom",
                "Slow Layer Top/Bottom",
                top_solid_infill_speed,
                slow_layer_speed,
                snapshot_profile.feature_trigger_on_top_solid_infill,
                snapshot_profile.feature_trigger_on_top_solid_infill and snapshot_profile.feature_trigger_on_first_layer))

        travel_speed = printer_profile.get_speed_for_slicer_type(printer_profile.movement_speed)
        slow_travel_speed = printer_profile.get_speed_for_slicer_type(printer_profile.first_layer_travel_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_cura,
                "Travel",
                "Slow Layer Travel",
                travel_speed,
                slow_travel_speed,
                snapshot_profile.feature_trigger_on_movement,
                snapshot_profile.feature_trigger_on_movement and snapshot_profile.feature_trigger_on_first_layer_travel))

        skirt_brim_speed = printer_profile.get_speed_for_slicer_type(printer_profile.skirt_brim_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_cura,
                "Skirt/Brim",
                "Skirt/Brim",
                skirt_brim_speed,
                skirt_brim_speed,
                snapshot_profile.feature_trigger_on_skirt_brim,
                snapshot_profile.feature_trigger_on_skirt_brim))

        z_travel_speed = printer_profile.get_speed_for_slicer_type(printer_profile.z_hop_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_cura,
                "Z Travel",
                "Z Travel",
                z_travel_speed,
                z_travel_speed,
                snapshot_profile.feature_trigger_on_z_movement,
                snapshot_profile.feature_trigger_on_z_movement))

    def create_simplify_3d_feature_list(self, printer_profile, snapshot_profile):

        retract_speed = printer_profile.get_speed_for_slicer_type(printer_profile.retract_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_simplify_3d,
                "Retraction",
                "Retraction",
                retract_speed,
                retract_speed,
                snapshot_profile.feature_trigger_on_retract,
                snapshot_profile.feature_trigger_on_retract))

        above_raft_speed = printer_profile.get_speed_for_slicer_type(printer_profile.above_raft_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_simplify_3d,
                "Above Raft",
                "Above Raft",
                above_raft_speed,
                above_raft_speed,
                snapshot_profile.feature_trigger_on_above_raft,
                snapshot_profile.feature_trigger_on_above_raft))

        prime_pillar_speed = printer_profile.get_speed_for_slicer_type(printer_profile.prime_pillar_speed)
        first_layer_prime_pillar_speed = printer_profile.get_speed_by_multiple_for_slicer_type(
            printer_profile.prime_pillar_speed, printer_profile.first_layer_speed_multiplier)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_simplify_3d,
                "Prime Pillar",
                "First Layer Prime Pillar",
                prime_pillar_speed,
                first_layer_prime_pillar_speed,
                snapshot_profile.feature_trigger_on_prime_pillar,
                snapshot_profile.feature_trigger_on_prime_pillar and snapshot_profile.feature_trigger_on_first_layer))

        ooze_shield_speed = printer_profile.get_speed_for_slicer_type(printer_profile.ooze_shield_speed)
        first_layer_ooze_shield_speed = printer_profile.get_speed_by_multiple_for_slicer_type(
            printer_profile.ooze_shield_speed, printer_profile.first_layer_speed_multiplier)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_simplify_3d,
                "Ooze Shield",
                "First Layer Ooze Shield",
                ooze_shield_speed,
                first_layer_ooze_shield_speed,
                snapshot_profile.feature_trigger_on_ooze_shield,
                snapshot_profile.feature_trigger_on_ooze_shield and snapshot_profile.feature_trigger_on_first_layer))

        print_speed = printer_profile.get_speed_for_slicer_type(printer_profile.print_speed)
        first_layer_print_speed = printer_profile.get_speed_by_multiple_for_slicer_type(printer_profile.print_speed,
                                                                                        printer_profile.first_layer_speed_multiplier)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_simplify_3d,
                "Printing Speed",
                "First Layer Printing Speed",
                print_speed,
                first_layer_print_speed,
                snapshot_profile.feature_trigger_on_normal_print_speed,
                snapshot_profile.feature_trigger_on_normal_print_speed and snapshot_profile.feature_trigger_on_first_layer))

        external_perimeter_speed = printer_profile.get_speed_for_slicer_type(printer_profile.external_perimeter_speed)
        first_layer_external_perimeter_speed = printer_profile.get_speed_by_multiple_for_slicer_type(
            printer_profile.external_perimeter_speed, printer_profile.first_layer_speed_multiplier)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_simplify_3d,
                "Exterior Outlines",
                "First Layer Exterior Outlines",
                external_perimeter_speed,
                first_layer_external_perimeter_speed,
                snapshot_profile.feature_trigger_on_external_perimeters,
                snapshot_profile.feature_trigger_on_external_perimeters and snapshot_profile.feature_trigger_on_first_layer))

        perimeter_speed = printer_profile.get_speed_for_slicer_type(printer_profile.perimeter_speed)
        first_layer_perimeter_speed = printer_profile.get_speed_by_multiple_for_slicer_type(
            printer_profile.perimeter_speed, printer_profile.first_layer_speed_multiplier)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_simplify_3d,
                "Interior Outlines",
                "First Layer Interior Outlines",
                perimeter_speed,
                first_layer_perimeter_speed,
                snapshot_profile.feature_trigger_on_perimeters,
                snapshot_profile.feature_trigger_on_perimeters and snapshot_profile.feature_trigger_on_first_layer))

        solid_infill_speed = printer_profile.get_speed_for_slicer_type(printer_profile.solid_infill_speed)
        first_layer_solid_infill_speed = printer_profile.get_speed_by_multiple_for_slicer_type(
            printer_profile.solid_infill_speed, printer_profile.first_layer_speed_multiplier)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_simplify_3d,
                "Solid Infill",
                "First Layer Solid Infill",
                solid_infill_speed,
                first_layer_solid_infill_speed,
                snapshot_profile.feature_trigger_on_solid_infill,
                snapshot_profile.feature_trigger_on_solid_infill and snapshot_profile.feature_trigger_on_first_layer))

        support_speed = printer_profile.get_speed_for_slicer_type(printer_profile.support_speed)
        first_layer_support_speed = printer_profile.get_speed_by_multiple_for_slicer_type(printer_profile.support_speed,
                                                                                          printer_profile.first_layer_speed_multiplier)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_simplify_3d,
                "Supports",
                "First Layer Supports",
                support_speed,
                first_layer_support_speed,
                snapshot_profile.feature_trigger_on_supports,
                snapshot_profile.feature_trigger_on_supports and snapshot_profile.feature_trigger_on_first_layer))

        xy_movement_speed = printer_profile.get_speed_for_slicer_type(printer_profile.movement_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_simplify_3d,
                "X/Y Movement",
                "X/Y Movement",
                xy_movement_speed,
                xy_movement_speed,
                snapshot_profile.feature_trigger_on_movement,
                snapshot_profile.feature_trigger_on_movement))

        z_movement_speed = printer_profile.get_speed_for_slicer_type(printer_profile.z_hop_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_simplify_3d,
                "Z Movement",
                "Z Movement",
                z_movement_speed,
                z_movement_speed,
                snapshot_profile.feature_trigger_on_z_movement,
                snapshot_profile.feature_trigger_on_z_movement))

        bridge_speed = printer_profile.get_speed_for_slicer_type(printer_profile.bridge_speed)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_simplify_3d,
                "Bridging",
                "Bridging",
                bridge_speed,
                bridge_speed,
                snapshot_profile.feature_trigger_on_bridges,
                snapshot_profile.feature_trigger_on_bridges))

        first_prime_speed = printer_profile.get_speed_for_slicer_type(printer_profile.retract_speed * 0.3)
        self.features.append(
            PrintFeatureSetting(
                calculate_speed_simplify_3d,
                "First Prime",
                "First Prime",
                first_prime_speed,
                first_prime_speed,
                snapshot_profile.feature_trigger_on_detract and snapshot_profile.feature_trigger_on_first_layer,
                snapshot_profile.feature_trigger_on_detract and snapshot_profile.feature_trigger_on_first_layer))

    def update(self, speed, layer_num):
        for feature in self.features:
            assert (isinstance(feature, PrintFeatureSetting))
            feature.update(speed, self.num_slow_layers, layer_num, self.speed_tolerance)

    def is_one_feature_enabled(self):
        if not self.feature_detection_enabled:
            return True

        for feature in self.features:
            assert (isinstance(feature, PrintFeatureSetting))
            if feature.triggered:
                return True
        return False

    def get_printing_features_list(self):
        printing_features = []
        if self.feature_detection_enabled:
            for feature in self.features:
                assert (isinstance(feature, PrintFeatureSetting))
                if feature.detected:
                    printing_features.append(feature.calculated_layer_name)
        if len(printing_features) == 0:
            printing_features = []
        return printing_features
