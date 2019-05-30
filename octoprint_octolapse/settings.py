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
from __future__ import unicode_literals
import pprint
import shutil
import copy
import json
import os
import uuid
import tempfile
import sys
import octoprint_octolapse.utility as utility
import octoprint_octolapse.log as log
import math
import collections
import octoprint_octolapse.gcode_preprocessing as gcode_preprocessing
import octoprint_octolapse.settings_migration as settings_migration
import logging
from six import string_types

# create the module level logger
from octoprint_octolapse.log import LoggingConfigurator
logging_configurator = LoggingConfigurator()
logger = logging_configurator.get_logger(__name__)


class SettingsJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Settings) or isinstance(obj, StaticSettings):
            return obj.__dict__
        # Let the base class default method raise the TypeError
        elif isinstance(obj, bool):
            return "{}".format(obj).lower()
        elif isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


class SettingsJsonDecoder(json.JSONDecoder):
    # noinspection PyCallByClass
    def default(self, obj):
        if isinstance(obj, Settings) or isinstance(obj, StaticSettings):
            return obj.__dict__
        # Let the base class default method raise the TypeError
        # noinspection PyTypeChecker
        return json.JSONEncoder.default(self, obj)


class StaticSettings(object):
    """Classes that inherit from StaticSettings will not be updated.  Useful for defaults and options"""
    pass


class Settings(object):
    def clone(self):
        return copy.deepcopy(self)

    def to_dict(self):
        return self.__dict__.copy()

    def to_json(self):
        return json.dumps(self.to_dict(), cls=SettingsJsonEncoder)

    @classmethod
    def encode_json(cls, o):
        return o.__dict__

    def update(self, iterable):
        Settings._update(self, iterable)

    @staticmethod
    def _update(source, iterable):
        if isinstance(source, StaticSettings):
            return
        item_to_iterate = iterable

        if not isinstance(iterable, collections.Iterable):
            item_to_iterate = iterable.__dict__

        for key, value in item_to_iterate.items():
            try:
                class_item = getattr(source, key, '{octolapse_no_property_found}')
                if not (isinstance(class_item, string_types) and class_item == '{octolapse_no_property_found}'):
                    if isinstance(class_item, Settings):
                        class_item.update(value)
                    elif isinstance(class_item, StaticSettings):
                        pass
                    else:
                        source.__dict__[key] = source.try_convert_value(class_item, value, key)
            except Exception as e:
                logger.exception("Settings._update - Failed to update settings.  Key:%s, Value:%s", key, value)
                continue

    @classmethod
    def try_convert_value(cls, destination, value, key):
        if value is None:
            return None
        if isinstance(destination, float):
            return float(value)
        # Note that bools are also ints, so bools need to come first
        elif isinstance(destination, bool):
            return bool(value)
        elif isinstance(destination, int):
            # sometimes the destination can be an int, but the value is a float
            if int(value) == float(value):
                return int(value)
            return float(value)
        else:
            # default action, just return the value
            return value

    def save_as_json(self, output_file_path):
        # use a temporary file so that if there is an error creating the json the
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        try:
            json.dump(self.to_dict(), temp_file, cls=SettingsJsonEncoder)
            temp_file.flush()
            shutil.copy(temp_file.name, output_file_path)
        finally:
            try:
                temp_file.close()
                os.unlink(temp_file.name)
            except WindowsError as e:
                pass

    @classmethod
    def create_from(cls, iterable=()):
        new_object = cls()
        new_object.update(iterable)
        return new_object


class ProfileSettings(Settings):

    def __init__(self, name=""):
        self.name = name
        self.description = ""
        self.guid = "{}".format(uuid.uuid4())

    @staticmethod
    def get_options():
        return {}

    @classmethod
    def create_from(cls, iterable=()):
        new_object = cls("")
        new_object.update(iterable)
        return new_object


class SlicerAutomatic(Settings):
    def __init__(self):
        self.continue_on_failure = False
        self.disable_automatic_save = False


class PrinterProfileSlicers(Settings):
    def __init__(self):
        self.automatic = SlicerAutomatic()
        self.cura = CuraSettings()
        self.simplify_3d = Simplify3dSettings()
        self.slic3r_pe = Slic3rPeSettings()
        self.other = OtherSlicerSettings()


class PrinterProfile(ProfileSettings):

    minimum_height_increment = 0.05

    def __init__(self, name="New Printer Profile"):
        super(PrinterProfile, self).__init__(name)
        # flag that is false until the profile has been saved by the user at least once
        # this is used to show a warning to the user if a new printer profile is used
        # without being configured
        self.has_been_saved_by_user = False
        self.slicer_type = "automatic"
        self.gcode_generation_settings = OctolapseGcodeSettings()
        self.slicers = PrinterProfileSlicers()
        self.snapshot_command = "snap"
        self.suppress_snapshot_command_always = True
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
        self.restrict_snapshot_area = False
        self.snapshot_min_x = 0.0
        self.snapshot_max_x = 0.0
        self.snapshot_min_y = 0.0
        self.snapshot_max_y = 0.0
        self.snapshot_min_z = 0.0
        self.snapshot_max_z = 0.0
        self.auto_position_detection_commands = ""
        self.priming_height = 0.75  # Extrusion must occur BELOW this level before layer tracking will begin
        self.minimum_layer_height = 0.05  # Layer tracking won't start until extrusion at this height is reached.
        self.e_axis_default_mode = 'require-explicit'  # other values are 'relative' and 'absolute'
        self.g90_influences_extruder = 'use-octoprint-settings'  # other values are 'true' and 'false'
        self.xyz_axes_default_mode = 'require-explicit'  # other values are 'relative' and 'absolute'
        self.units_default = 'millimeters'
        self.axis_speed_display_units = 'mm-min'
        self.default_firmware_retractions = False
        self.default_firmware_retractions_zhop = False
        self.gocde_axis_compatibility_mode_enabled = True

    @staticmethod
    def get_options():
        return {
            'gcode_configuration_options': [
                dict(value='use-slicer-settings', name='Use Slicer Settings'),
                dict(value='manual', name='Manual Configuration')
            ],
            'slicer_type_options': [
                dict(value='automatic', name='Automatic Configuration'),
                dict(value='cura', name='Cura'),
                dict(value='simplify-3d', name='Simplify 3D'),
                dict(value='slic3r-pe', name='Slic3r Prusa Edition'),
                dict(value='other', name='Other Slicer')
            ],
            'e_axis_default_mode_options': [
                dict(value='require-explicit', name='Require Explicit M82/M83'),
                dict(value='relative', name='Default To Relative'),
                dict(value='absolute', name='Default To Absolute'),
                dict(value='force-absolute', name='Force Absolute (send M82 at print start)'),
                dict(value='force-relative', name='Force Relative (send M83 at print start)')
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
                dict(value='force-absolute', name='Force Absolute (send G90 at print start)'),
                dict(value='force-relative', name='Force Relative (send G91 at print start)')
            ],
            'units_default_options': [
                dict(value='require-explicit', name='Require Explicit G21'),
                dict(value='inches', name='Inches'),
                dict(value='millimeters', name='Millimeters')
            ],
            'cura_surface_mode_options': [
                dict(value="normal", name='Normal'),
                dict(value="surface", name='Surface'),
                dict(value="both", name='Both'),
            ],
            'cura_combing_mode_options': [
                dict(value="off", name='Off'),
                dict(value="all", name='All'),
                dict(value="noskin", name='Not in Skin'),
                dict(value="infill", name='Within Infill'),
            ]
        }

    def get_current_slicer_settings(self):
        return self.get_slicer_settings_by_type(self.slicer_type)

    def get_slicer_settings_by_type(self, slicer_type):
        if slicer_type == 'slic3r-pe':
            return self.slicers.slic3r_pe
        elif slicer_type == 'simplify-3d':
            return self.slicers.simplify_3d
        elif slicer_type == 'cura':
            return self.slicers.cura
        elif slicer_type == 'other':
            return self.slicers.other
        return None  # we return None on automatic.  This profile needs to be accessed directly

    def get_current_state_detection_settings(self):
        if self.slicer_type == 'automatic':
            return None

        return self.get_current_slicer_settings().get_gcode_generation_settings()

    def get_gcode_settings_from_file(self, gcode_file_path):
        simplify_preprocessor = gcode_preprocessing.Simplify3dSettingsProcessor(
            search_direction="both", max_forward_search=1000, max_reverse_search=1000
        )
        slic3r_preprocessor = gcode_preprocessing.Slic3rSettingsProcessor(
            search_direction="both", max_forward_search=1000, max_reverse_search=1000
        )
        cura_preprocessor = gcode_preprocessing.CuraSettingsProcessor(
            search_direction="both", max_forward_search=1000, max_reverse_search=1000
        )
        file_processor = gcode_preprocessing.GcodeFileProcessor(
            [simplify_preprocessor, slic3r_preprocessor, cura_preprocessor], 1, None
        )
        results = file_processor.process_file(gcode_file_path, filter_tags=['octolapse_setting'])

        # determine which results have the most settings
        current_max_slicer_type = None
        current_max_settings = 0
        if 'settings' not in results:
            return False
        settings = results['settings']

        for key, value in settings.items():
            num_settings = len(settings[key])
            if num_settings > current_max_settings:
                current_max_settings = num_settings
                current_max_slicer_type = key

        if current_max_slicer_type is not None:
            new_settings = settings[current_max_slicer_type]
            self.slicer_type = current_max_slicer_type

            if self.slicer_type == 'slic3r-pe':
                new_slicer_settings = Slic3rPeSettings()
            elif self.slicer_type == 'simplify-3d':
                new_slicer_settings = Simplify3dSettings()
            elif self.slicer_type == 'cura':
                new_slicer_settings = CuraSettings()
            else:
                raise Exception("An invalid slicer type has been detected while extracting settings from gcode.")

            new_slicer_settings.update_settings_from_gcode(new_settings)
            # check to make sure all of the required settings are there
            missing_settings = new_slicer_settings.get_missing_gcode_generation_settings()
            if len(missing_settings) > 0:
                return False, 'required-settings-missing', missing_settings
            # copy the settings into the current profile
            current_slicer_settings = self.get_current_slicer_settings()
            current_slicer_settings.update(new_slicer_settings)
            self.gcode_generation_settings.update(current_slicer_settings.get_gcode_generation_settings())

            return True, None, []

        return False, "no-settings-detected", ["No settings were detected in the gcode file."]

    def get_location_detection_command_list(self):
        if self.auto_position_detection_commands is not None:
            trimmed_commands = self.auto_position_detection_commands.strip()
            if len(trimmed_commands) > 0:
                return [
                    x.strip().upper()
                    for x in
                    self.auto_position_detection_commands.split(',')
                ]
        return []

    def try_convert_value(cls, destination, value, key):
        if key in ['origin_x','origin_y','origin_z']:
            if value is not None:
                return float(value)
        return super(PrinterProfile, cls).try_convert_value(destination, value, key)

    def get_position_args(self, octoprint_g90_influences_extruder):

        if self.g90_influences_extruder == 'true':
            g90_influences_extruder = True
        elif self.g90_influences_extruder == 'false':
            g90_influences_extruder = False
        else:
            g90_influences_extruder = octoprint_g90_influences_extruder

        return {
            "is_bound": self.restrict_snapshot_area,
            "bounds": {
                'x_min': self.snapshot_min_x,
                'x_max': self.snapshot_max_x,
                'y_min': self.snapshot_min_y,
                'y_max': self.snapshot_max_y,
                'z_min': self.snapshot_min_z,
                'z_max': self.snapshot_max_z,
            },
            "location_detection_commands": self.get_location_detection_command_list(),
            "xyz_axis_default_mode": self.xyz_axes_default_mode,
            "e_axis_default_mode": self.e_axis_default_mode,
            "units_default": self.units_default,
            "autodetect_position": self.auto_detect_position,
            "origin_x": self.origin_x,
            "origin_y": self.origin_y,
            "origin_z": self.origin_z,
            "slicer_settings": self.gcode_generation_settings.to_dict(),
            "priming_height": self.priming_height,
            "minimum_layer_height": self.minimum_layer_height,
            "g90_influences_extruder": g90_influences_extruder
        }


class StabilizationPath(Settings):
    def __init__(self):
        self.path = []
        self.coordinate_system = ""
        self.index = 0
        self.loop = True
        self.invert_loop = True
        self.increment = 1
        self.current_position = None
        self.type = 'disabled'
        self.options = {}


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

        self.type = restriction_type
        self.shape = shape
        self.x = float(x)
        self.y = float(y)
        self.x2 = float(x2)
        self.y2 = float(y2)
        self.r = float(r)
        self.calculate_intersections = calculate_intersections

    def to_dict(self):
        return {
            'type': self.type,
            'shape': self.shape,
            'x': self.x,
            'y': self.y,
            'x2': self.x2,
            'y2': self.y2,
            'r': self.r,
            'calculate_intersections': self.calculate_intersections
        }

    def get_intersections(self, x, y, previous_x, previous_y):
        if not self.calculate_intersections:
            return False

        if x is None or y is None or previous_x is None or previous_y is None:
            return False

        if self.Shape == 'rect':
            intersections = utility.get_intersections_rectangle(previous_x, previous_y, x, y, self.x, self.y, self.x2,
                                                                self.y2)
        elif self.Shape == 'circle':
            intersections = utility.get_intersections_circle(previous_x, previous_y, x, y, self.x, self.y, self.r)
        else:
            raise TypeError("SnapshotPosition shape must be 'rect' or 'circle'.")

        if not intersections:
            return False

        return intersections

    def is_in_position(self, x, y, tolerance):
        if x is None or y is None:
            return False

        if self.Shape == 'rect':
            return self.x <= x <= self.x2 and self.y <= y <= self.y2
        elif self.Shape == 'circle':
            lsq = math.pow(x - self.x, 2) + math.pow(y - self.y, 2)
            rsq = math.pow(self.r, 2)
            return utility.is_close(lsq, rsq, tolerance) or lsq < rsq
        else:
            raise TypeError("SnapshotPosition shape must be 'rect' or 'circle'.")


class StabilizationProfile(ProfileSettings):
    STABILIZATION_TYPE_REAL_TIME = "real-time"
    STABILIZATION_TYPE_SNAP_TO_PRINT = "snap-to-print"
    STABILIZATION_TYPE_SMART_LAYER = "smart-layer"

    EXTRUDER_TRIGGER_IGNORE_VALUE = ""
    EXTRUDER_TRIGGER_REQUIRED_VALUE = "trigger_on"
    EXTRUDER_TRIGGER_FORBIDDEN_VALUE = "forbidden"
    LAYER_TRIGGER_TYPE = 'layer'
    TIMER_TRIGGER_TYPE = 'timer'
    GCODE_TRIGGER_TYPE = 'gcode'

    def __init__(self, name="New Stabilization Profile"):
        super(StabilizationProfile, self).__init__(name)
        self.stabilization_type = StabilizationProfile.STABILIZATION_TYPE_REAL_TIME
        # Pre-Calculated stabilization options
        self.fastest_speed = True
        # Lock to corner options
        self.snap_to_print_disable_z_lift = True
        self.snap_to_print_disable_retract = False
        # smart layer trigger options
        self.smart_layer_trigger_on_extrude = False
        self.smart_layer_speed_threshold = 0
        # Real Time stabilization options
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

        # Settings that were formerly in the snapshot profile (now removed)
        self.is_default = False
        self.trigger_type = self.LAYER_TRIGGER_TYPE
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
        self.extruder_state_requirements_enabled = True
        self.trigger_on_extruding_start = StabilizationProfile.EXTRUDER_TRIGGER_REQUIRED_VALUE
        self.trigger_on_extruding = StabilizationProfile.EXTRUDER_TRIGGER_REQUIRED_VALUE
        self.trigger_on_primed = StabilizationProfile.EXTRUDER_TRIGGER_REQUIRED_VALUE
        self.trigger_on_retracting_start = StabilizationProfile.EXTRUDER_TRIGGER_IGNORE_VALUE
        self.trigger_on_retracting = StabilizationProfile.EXTRUDER_TRIGGER_IGNORE_VALUE
        self.trigger_on_partially_retracted = StabilizationProfile.EXTRUDER_TRIGGER_FORBIDDEN_VALUE
        self.trigger_on_retracted = StabilizationProfile.EXTRUDER_TRIGGER_REQUIRED_VALUE
        self.trigger_on_deretracting_start = StabilizationProfile.EXTRUDER_TRIGGER_IGNORE_VALUE
        self.trigger_on_deretracting = StabilizationProfile.EXTRUDER_TRIGGER_FORBIDDEN_VALUE
        self.trigger_on_deretracted = StabilizationProfile.EXTRUDER_TRIGGER_FORBIDDEN_VALUE

        # Feature Detection
        self.feature_trigger_on_wipe = None
        self.feature_restrictions_enabled = False
        self.feature_trigger_on_deretract = False
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

    def get_snapshot_plan_options(self):
        if self.stabilization_type == StabilizationProfile.STABILIZATION_TYPE_SNAP_TO_PRINT:
            return {
                'disable_z_lift': self.snap_to_print_disable_z_lift,
                'disable_retract': self.snap_to_print_disable_retract
            }
        return None

    @staticmethod
    def get_precalculated_stabilization_types():
        return [
            StabilizationProfile.STABILIZATION_TYPE_SNAP_TO_PRINT,
            StabilizationProfile.STABILIZATION_TYPE_SMART_LAYER
        ]
    def get_extruder_trigger_value_string(self, value):
        if value is None:
            return self.EXTRUDER_TRIGGER_IGNORE_VALUE
        elif value:
            return self.EXTRUDER_TRIGGER_REQUIRED_VALUE
        elif not value:
            return self.EXTRUDER_TRIGGER_FORBIDDEN_VALUE

    def get_stabilization_paths(self):
        x_stabilization_path = StabilizationPath()
        x_stabilization_path.type = self.x_type
        if self.x_type == 'fixed_coordinate':
            x_stabilization_path.path.append(self.x_fixed_coordinate)
            x_stabilization_path.coordinate_system = 'absolute'
        elif self.x_type == 'relative':
            x_stabilization_path.path.append(self.x_relative)
            x_stabilization_path.coordinate_system = 'bed_relative'
        elif self.x_type == 'fixed_path':
            x_stabilization_path.path = self.parse_csv_path(self.x_fixed_path)
            x_stabilization_path.coordinate_system = 'absolute'
            x_stabilization_path.loop = self.x_fixed_path_loop
            x_stabilization_path.invert_loop = self.x_fixed_path_invert_loop
        elif self.x_type == 'relative_path':
            x_stabilization_path.path = self.parse_csv_path(self.x_relative_path)
            x_stabilization_path.coordinate_system = 'bed_relative'
            x_stabilization_path.loop = self.x_relative_path_loop
            x_stabilization_path.invert_loop = self.x_relative_path_invert_loop

        y_stabilization_path = StabilizationPath()
        y_stabilization_path.type = self.y_type
        if self.y_type == 'fixed_coordinate':
            y_stabilization_path.path.append(self.y_fixed_coordinate)
            y_stabilization_path.CoordinateSystem = 'absolute'
        elif self.y_type == 'relative':
            y_stabilization_path.path.append(self.y_relative)
            y_stabilization_path.coordinate_system = 'bed_relative'
        elif self.y_type == 'fixed_path':
            y_stabilization_path.path = self.parse_csv_path(self.y_fixed_path)
            y_stabilization_path.coordinate_system = 'absolute'
            y_stabilization_path.loop = self.y_fixed_path_loop
            y_stabilization_path.invert_loop = self.y_fixed_path_invert_loop
        elif self.y_type == 'relative_path':
            y_stabilization_path.path = self.parse_csv_path(self.y_relative_path)
            y_stabilization_path.coordinate_system = 'bed_relative'
            y_stabilization_path.loop = self.y_relative_path_loop
            y_stabilization_path.invert_loop = self.y_relative_path_invert_loop

        return dict(
            x=x_stabilization_path,
            y=y_stabilization_path
        )

    @staticmethod
    def get_options():
        return {
            'stabilization_type_options': [
                dict(value=StabilizationProfile.STABILIZATION_TYPE_REAL_TIME, name='Real-Time'),
                dict(value=StabilizationProfile.STABILIZATION_TYPE_SMART_LAYER, name='Smart Layer Trigger'),
                dict(value=StabilizationProfile.STABILIZATION_TYPE_SNAP_TO_PRINT, name='Snap to Print')
            ],
            'real_time_xy_stabilization_type_options': [
                dict(value='disabled', name='Disabled'),
                dict(value='fixed_coordinate', name='Fixed Coordinate'),
                dict(value='fixed_path', name='List of Fixed Coordinates'),
                dict(value='relative', name='Relative Coordinate (0-100)'),
                dict(value='relative_path', name='List of Relative Coordinates')
            ],
            'lock_to_print_type_options': [
                dict(value='front_left', name='Front Left'),
                dict(value='front_right', name='Front Right'),
                dict(value='back_left', name='Back Left'),
                dict(value='back_right', name='Back Right'),
            ],
            'favor_axis_options': [
                dict(value='x', name='Favor X Axis'),
                dict(value='y', name='Favor Y Axis')
            ],
            'trigger_types': [
                dict(value=StabilizationProfile.LAYER_TRIGGER_TYPE, name="Layer/Height"),
                dict(value=StabilizationProfile.TIMER_TRIGGER_TYPE, name="Timer"),
                dict(value=StabilizationProfile.GCODE_TRIGGER_TYPE, name="Gcode")
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
                dict(value=StabilizationProfile.EXTRUDER_TRIGGER_IGNORE_VALUE, name='Ignore', visible=True),
                dict(value=StabilizationProfile.EXTRUDER_TRIGGER_REQUIRED_VALUE, name='Trigger', visible=True),
                dict(value=StabilizationProfile.EXTRUDER_TRIGGER_FORBIDDEN_VALUE, name='Forbidden', visible=True)
            ]
        }

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

    @staticmethod
    def get_extruder_trigger_value(value):
        if isinstance(value, string_types):
            if value is None or len(value) == 0:
                return None
            elif value.lower() == StabilizationProfile.EXTRUDER_TRIGGER_REQUIRED_VALUE:
                return True
            elif value.lower() == StabilizationProfile.EXTRUDER_TRIGGER_FORBIDDEN_VALUE:
                return False
            else:
                return None
        else:
            return bool(value)

    @staticmethod
    def get_trigger_position_restrictions(value):
        restrictions = []
        for restriction in value:
            try:
                restrictions.append(
                    SnapshotPositionRestrictions(
                        restriction["type"],
                        restriction["shape"],
                        restriction["x"],
                        restriction["y"],
                        restriction["x2"],
                        restriction["y2"],
                        restriction["r"],
                        restriction["calculate_intersections"]
                    )
                )
            except KeyError as e:
                logger.exception("Unable to find key for snapshot position restriction")
                continue
        return restrictions

    @staticmethod
    def get_trigger_position_restrictions_value_string(values):
        restrictions = []
        for restriction in values:
            restrictions.append(restriction.to_dict())
        return restrictions

    @classmethod
    def try_convert_value(cls, destination, value, key):
        if key == 'position_restrictions':
            if value is not None:
                return StabilizationProfile.get_trigger_position_restrictions(value)

        return super(StabilizationProfile, cls).try_convert_value(destination, value, key)


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
        # Snapshot Cleanup
        self.cleanup_after_render_complete = True
        self.cleanup_after_render_fail = False

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


class WebcamSettings(Settings):
    def __init__(self):
        self.address = "http://127.0.0.1/webcam/"
        self.snapshot_request_template = "{camera_address}?action=snapshot"
        self.stream_template = "/webcam/?action=stream"
        self.ignore_ssl_error = False
        self.username = ""
        self.password = ""
        self.brightness = 128
        self.contrast = 128
        self.saturation = 128
        self.white_balance_auto = True
        self.gain = 100
        self.powerline_frequency = 60
        self.white_balance_temperature = 4000
        self.sharpness = 128
        self.backlight_compensation_enabled = False
        self.exposure_type = 1
        self.exposure = 250
        self.exposure_auto_priority_enabled = True
        self.pan = 0
        self.tilt = 0
        self.autofocus_enabled = True
        self.focus = 28
        self.zoom = 100
        self.led1_mode = 'auto'
        self.led1_frequency = 0        
        self.jpeg_quality = 90
        self.mjpegstreamer = MjpegStreamerStaticSettings()


class MjpegStreamerStaticSettings(StaticSettings):
    
    def template_to_string(self, destination, plugin, setting_id, group):
        return (
            "{}?action=command&dest={}&plugin={}&id={}&group={}&value={}".format(
                "{camera_address}", destination, plugin, setting_id, group, "{value}"
            )
        )

    def format_request_template(camera_address, template, value):
        return template.format(camera_address=camera_address, value=value)
    
    def __init__(self):
        try:
            self.brightness_request_template = self.template_to_string(0, 0, 9963776, 1)
            self.contrast_request_template = self.template_to_string(0, 0, 9963777, 1)
            self.saturation_request_template = self.template_to_string(0, 0, 9963778, 1)
            self.white_balance_auto_request_template = self.template_to_string(0, 0, 9963788, 1)
            self.gain_request_template = self.template_to_string(0, 0, 9963795, 1)
            self.powerline_frequency_request_template = self.template_to_string(0, 0, 9963800, 1)
            self.white_balance_temperature_request_template = self.template_to_string(0, 0, 9963802, 1)
            self.sharpness_request_template = self.template_to_string(0, 0, 9963803, 1)
            self.backlight_compensation_enabled_request_template = self.template_to_string(0, 0, 9963804, 1)
            self.exposure_type_request_template = self.template_to_string(0, 0, 10094849, 1)
            self.exposure_request_template = self.template_to_string(0, 0, 10094850, 1)
            self.exposure_auto_priority_enabled_request_template = self.template_to_string(0, 0, 10094851, 1)
            self.pan_request_template = self.template_to_string(0, 0, 10094856, 1)
            self.tilt_request_template = self.template_to_string(0, 0, 10094857, 1)
            self.autofocus_enabled_request_template = self.template_to_string(0, 0, 10094860, 1)
            self.focus_request_template = self.template_to_string(0, 0, 10094858, 1)
            self.zoom_request_template = self.template_to_string(0, 0, 10094861, 1)
            self.led1_mode_request_template = self.template_to_string(0, 0, 168062213, 1)
            self.led1_frequency_request_template = self.template_to_string(0, 0, 168062214, 1)
            self.jpeg_quality_request_template = self.template_to_string(0, 0, 1, 3)
            self.file_request_template = "{camera_address}{value}"
            self.options = self.get_options()
        except Exception as e:
            print (e)
    
    @staticmethod
    def get_options():
        return {
            'camera_powerline_frequency_options': [
                dict(value='0', name='Disabled'),
                dict(value='1', name='50 HZ (Europe, China, India, etc)'),
                dict(value='2', name='60 HZ (North/South America, Japan, etc)')
            ],
            'camera_exposure_type_options': [
                dict(value='0', name='Brightness'),
                dict(value='1', name='Manual Mode'),
                dict(value='2', name='rast'),
                dict(value='3', name='Auto - Aperture Priority Mode')
            ],
            'camera_led_1_mode_options': [
                dict(value='on', name='On'),
                dict(value='off', name='Off'),
                dict(value='blink', name='Blink'),
                dict(value='auto', name='Auto')
            ]
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
        self.apply_settings_at_startup = False
        self.snapshot_transpose = ""
        self.webcam_settings = WebcamSettings()

    def format_snapshot_request_template(self):
        return self.snapshot_request_template.format(camera_address=self.address)

    def format_stream_template(self):
        return self.stream_template.format(camera_address=self.address)

    @staticmethod
    def format_url(url):
        if url[0] == "/":
            url = "http://172.0.0.1" + url
        return url

    def get_image_preferences(self):
        return {
            'guid': self.guid,
            'name': self.name,
            'stream_template': self.format_stream_template(),
            'address': self.address,
            'brightness': self.brightness,
            'contrast': self.contrast,
            'saturation': self.saturation,
            'white_balance_auto': self.white_balance_auto,
            'gain': self.gain,
            'powerline_frequency': self.powerline_frequency,
            'white_balance_temperature':  self.white_balance_temperature,
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
            'options': self.get_options()
        }

    @staticmethod
    def get_options():
        return {
            'camera_powerline_frequency_options': [
                dict(value='0', name='Disabled'),
                dict(value='1', name='50 HZ (Europe, China, India, etc)'),
                dict(value='2', name='60 HZ (North/South America, Japan, etc)')
            ],
            'camera_exposure_type_options': [
                dict(value='0', name='Brightness'),
                dict(value='1', name='Manual Mode'),
                dict(value='2', name='rast'),
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


class LoggerSettings(Settings):
    def __init__(self, name, log_level):
        self.name = name
        self.log_level = log_level


class DebugProfile(ProfileSettings):

    def __init__(self, name="New Debug Profile"):
        super(DebugProfile, self).__init__(name)
        # Configure the logger if it has not been created
        self.log_all_errors = True
        self.enabled = False
        self.log_to_console = False
        self.default_log_level = logging.DEBUG
        self.is_test_mode = False
        self.enabled_loggers = []
        for logger_name in logging_configurator.get_logger_names():
            self.enabled_loggers.append(LoggerSettings(logger_name, self.default_log_level))

    @classmethod
    def try_convert_value(cls, destination, value, key):
        if key == 'enabled_loggers':
            try:
                if value is not None:
                    return DebugProfile.get_enabled_loggers(value)
            except Exception as e:
                logger.exception("Unable to convert 'enabled_loggers', returning default.")
                return []

        return super(DebugProfile, cls).try_convert_value(destination, value, key)

    @classmethod
    def get_enabled_loggers(cls, values):
        logger_list = []
        for enabled_logger in values:
            logger_list.append({
                'name': enabled_logger["name"],
                'log_level': enabled_logger["log_level"]
            })
        return logger_list

    @staticmethod
    def get_options():
        return {
            'logging_levels': [
                dict(value=log.VERBOSE, name='Verbose'),
                dict(value=logging.DEBUG, name='Debug'),
                dict(value=logging.INFO, name='Info'),
                dict(value=logging.WARNING, name='Warning'),
                dict(value=logging.ERROR, name='Error'),
                dict(value=logging.CRITICAL, name='Critical'),
            ],
            'all_logger_names': logging_configurator.get_logger_names()

        }


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
        self.show_snapshot_plan_information = False
        self.show_real_snapshot_time = False
        self.cancel_print_on_startup_error = True
        self.platform = sys.platform,
        self.version = plugin_version


class ProfileOptions(StaticSettings):
    def __init__(self):
        self.printer = PrinterProfile.get_options()
        self.stabilization = StabilizationProfile.get_options()
        self.rendering = RenderingProfile.get_options()
        self.camera = CameraProfile.get_options()
        self.debug = DebugProfile.get_options()


class ProfileDefaults(StaticSettings):
    def __init__(self):
        self.printer = PrinterProfile("Default Printer")
        self.stabilization = StabilizationProfile("Default Stabilization")
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
            'current_rendering_profile_guid': self.current_rendering_profile_guid,
            'current_camera_profile_guid': self.current_camera_profile_guid,
            'current_debug_profile_guid': self.current_debug_profile_guid,
            'printers': [],
            'stabilizations': [],
            'renderings': [],
            'cameras': [],
            'debug': []
        }

        for key, printer in self.printers.items():
            profiles_dict["printers"].append({
                "name": printer.name,
                "guid": printer.guid,
                "has_been_saved_by_user": printer.has_been_saved_by_user,
                "slicer_type": printer.slicer_type
            })

        for key, stabilization in self.stabilizations.items():
            profiles_dict["stabilizations"].append({
                "name": stabilization.name,
                "guid": stabilization.guid,
                "stabilization_type": stabilization.stabilization_type
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
        _active_cameras = []
        for key in self.cameras:
            _current_camera = self.cameras[key]
            if _current_camera.enabled:
                _active_cameras.append(_current_camera)
        return _active_cameras

    def startup_cameras(self):
        _startup_cameras = []
        for key in self.cameras:
            _current_camera = self.cameras[key]
            if (
                _current_camera.enabled  and
                _current_camera.camera_type == 'webcam' and
                _current_camera.apply_settings_at_startup
            ):
                _startup_cameras.append(_current_camera)
        return _startup_cameras

    def get_profile(self, profile_type, guid):

        if profile_type == "Printer":
            profile = self.printers[guid]
        elif profile_type == "Stabilization":
            profile = self.stabilizations[guid]
        elif profile_type == "Rendering":
            profile = self.renderings[guid]
        elif profile_type == "Camera":
            profile = self.cameras[guid]
        elif profile_type == "Debug":
            profile = self.debug[guid]
        else:
            raise ValueError('An unknown profile type {} was received.'.format(profile_type))
        return profile

    def import_profile(self, profile_type, profile_json, update_existing=False):
        logger.info("Importing a profile.")

        # Create the profile by type
        if profile_type == "Printer":
            new_profile = PrinterProfile.create_from(profile_json)
            existing_profiles = self.printers
        elif profile_type == "Stabilization":
            new_profile = StabilizationProfile.create_from(profile_json)
            existing_profiles = self.stabilizations
        elif profile_type == "Rendering":
            new_profile = RenderingProfile.create_from(profile_json)
            existing_profiles = self.renderings
        elif profile_type == "Camera":
            new_profile = CameraProfile.create_from(profile_json)
            existing_profiles = self.cameras
        elif profile_type == "Debug":
            new_profile = DebugProfile.create_from(profile_json)
            existing_profiles = self.debug
        else:
            raise Exception("Unknown settings type:{0}".format(profile_type))
        # see if any existing profiles have the same name
        new_profile.name = OctolapseSettings.get_unique_profile_name(existing_profiles, new_profile.name)
        # create a new guid for the profile
        if not update_existing and new_profile.guid in existing_profiles:
            new_profile.guid = "{}".format(uuid.uuid4())
        existing_profiles[new_profile.guid] = new_profile

    def add_update_profile(self, profile_type, profile):
        # check the guid.  If it is null or empty, assign a new value.
        guid = profile["guid"]
        if guid is None or guid == "":
            guid = "{}".format(uuid.uuid4())
            profile["guid"] = guid

        if profile_type == "Printer":
            new_profile = PrinterProfile.create_from(profile)
            if new_profile.slicer_type != 'automatic':
                new_profile.gcode_generation_settings = (
                    new_profile.get_current_slicer_settings().get_gcode_generation_settings()
                )
            self.printers[guid] = new_profile
            if len(self.printers) == 1:
                self.current_printer_profile_guid = new_profile.guid
        elif profile_type == "Stabilization":
            new_profile = StabilizationProfile.create_from(profile)
            self.stabilizations[guid] = new_profile
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
            raise ValueError('An unknown profile type {} was received.'.format(profile_type))
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
            raise ValueError('An unknown profile type {} was received.'.format(profile_type)(profile_type))

        return True

    def set_current_profile(self, profile_type, guid):
        if profile_type == "Printer":
            if guid == "":
                guid = None
            self.current_printer_profile_guid = guid
        elif profile_type == "Stabilization":
            self.current_stabilization_profile_guid = guid
        elif profile_type == "Rendering":
            self.current_rendering_profile_guid = guid
        elif profile_type == "Camera":
            self.current_camera_profile_guid = guid
        elif profile_type == "Debug":
            self.current_debug_profile_guid = guid
        else:
            raise ValueError('An unknown profile type {} was received.'.format(profile_type))

    def update(self, iterable, **kwargs):
        try:
            item_to_iterate = iterable
            if not isinstance(iterable, collections.Iterable):
                item_to_iterate = iterable.__dict__

            for key, value in item_to_iterate.items():
                class_item = getattr(self, key, '{octolapse_no_property_found}')
                if not (isinstance(class_item, string_types) and class_item == '{octolapse_no_property_found}'):
                    if key == 'printers':
                        self.printers = {}
                        for profile_key, profile_value in value.items():
                            self.printers[profile_key] = PrinterProfile.create_from(profile_value)
                    elif key == 'stabilizations':
                        self.stabilizations = {}
                        for profile_key, profile_value in value.items():
                            self.stabilizations[profile_key] = StabilizationProfile.create_from(profile_value)
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
                    elif isinstance(class_item, StaticSettings):
                        # don't update any static settings, those come from the class itself!
                        continue
                    else:
                        self.__dict__[key] = self.try_convert_value(class_item, value, key)
        except Exception as e:
            raise e


class GlobalOptions(StaticSettings):
    def __init__(self):
        self.import_options = {
            'settings_import_methods': [
                dict(value='file', name='From a File'),
                dict(value='text', name='From Text'),
            ]
        }


class OctolapseSettings(Settings):
    DefaultDebugProfile = None

    def __init__(self, plugin_version="unknown"):
        self.main_settings = MainSettings(plugin_version)
        self.profiles = Profiles()
        self.global_options = GlobalOptions()

    def save(self, file_path):
        logger.info("Saving settings to: %s.", file_path)
        self.save_as_json(file_path)
        logger.info("Settings saved.")

    @classmethod
    def load(cls, file_path, plugin_version, default_settings_folder, default_settings_filename):
        # try to load the file path if it exists
        if file_path is not None:
            load_defualt_settings = not os.path.isfile(file_path)
        else:
            load_defualt_settings = True
        if not load_defualt_settings:
            logger.info("Loading existing settings file from: %s.", file_path)
            with open(file_path, 'r') as settings_file:
                try:
                    data = json.load(settings_file)
                    data = settings_migration.migrate_settings(
                        plugin_version, data, default_settings_folder
                    )
                    # if a settings file does not exist, create one ??
                    new_settings = OctolapseSettings.create_from_iterable(
                        plugin_version,
                        data
                    )
                    logger.info("Settings file loaded.")
                except ValueError as e:
                    logger.exception("The existing settings file is corrupted.  Will attempt to load the defaults")
                    load_defualt_settings = True
        # do not use elif here!
        if load_defualt_settings:
            # try to load the defaults
            with open(os.path.join(default_settings_folder, default_settings_filename), 'r') as settings_file:
                try:
                    data = json.load(settings_file)
                    data = settings_migration.migrate_settings(
                        plugin_version, data, default_settings_folder
                    )
                    # if a settings file does not exist, create one ??
                    new_settings = OctolapseSettings.create_from_iterable(
                        plugin_version,
                        data
                    )
                    logger.info("Default settings loaded.")
                except ValueError as e:
                    logger.exception("The defualt settings file is corrupted.  Something is seriously wrong!")
                    raise e

        return new_settings, load_defualt_settings

    def get_profile_export_json(self, profile_type, guid):
        profile = self.profiles.get_profile(profile_type, guid)
        export_dict = {
            'version': self.main_settings.version,
            'type': profile_type,
            'profile': profile
        }
        return json.dumps(export_dict, cls=SettingsJsonEncoder)

    def import_settings_from_file(
        self, settings_path, plugin_version, default_settings_folder,
        update_existing=False
    ):
        with open(settings_path, 'r') as settings_file:
            settings = json.load(settings_file)

        # see if this is a structured import
        if "type" in settings:
            if settings["version"] != plugin_version:
                raise Exception(
                    "Cannot import settings from an old version of Octolapse.  Current Version:{0}, Settings "
                    "Version:{1} ".format(settings.version, plugin_version)
                )
            else:
                self.profiles.import_profile(settings["type"], settings["profile"], update_existing=update_existing)
                return self
        else:
            # this is a regular settings file.  Try to migrate
            migrated_settings = settings_migration.migrate_settings(
                plugin_version, settings, default_settings_folder
            )
            new_settings = OctolapseSettings(plugin_version)
            new_settings.update(migrated_settings)
            return new_settings

    def import_settings_from_text(
        self, settings_text, plugin_version, default_settings_folder, update_existing=False
    ):
        logger.info("Importing python settings object.  Checking settings version.")
        settings = json.loads(settings_text)
        # see if this is a structured import
        if "type" in settings:
            if settings["version"] != plugin_version:
                raise Exception(
                    "Cannot import settings from an old version of Octolapse.  Current Version:{0}, Settings "
                    "Version:{1} ".format(settings.version, plugin_version)
                )
            else:
                self.profiles.import_profile(settings["type"], settings["profile"], update_existing=update_existing)
                return self
        else:
            # this is a regular settings file.  Try to migrate
            migrated_settings = settings_migration.migrate_settings(
                plugin_version, settings, default_settings_folder
            )
            new_settings = OctolapseSettings(plugin_version)
            new_settings.update(migrated_settings)
            return new_settings

    @staticmethod
    def get_unique_profile_name(profiles, name):
        copy_version = 1
        original_name = name
        is_unique = False
        while not is_unique:
            is_unique = True
            for profile_guid in profiles:
                profile = profiles[profile_guid]
                if profile.name == name:
                    name = original_name + " - Copy({0})".format(copy_version)
                    copy_version += 1
                    is_unique = False
                    break
        return name

    @classmethod
    def create_from_iterable(cls, plugin_version, iterable=()):
        logger.info("Creating settings from iterable.")
        new_object = cls(plugin_version)
        new_object.update(iterable)
        logger.info("Settings created from iterable.")
        return new_object


class OctolapseGcodeSettings(Settings):
    def __init__(self):
        self.retract_before_move = None
        self.retraction_length = None
        self.retraction_speed = None
        self.deretraction_speed = None
        self.x_y_travel_speed = None
        self.first_layer_travel_speed = None
        self.lift_when_retracted = None
        self.z_lift_height = None
        self.z_lift_speed = None
        self.vase_mode = None
        self.layer_height = None

class SlicerSettings(Settings):
    SlicerTypeOther = 'other'
    SlicerTypeCura = 'cura'
    SlicerTypeSimplify3D = 'simplify-3d'
    SlicerTypeSlic3rPe = 'slic3r-pe'

    def __init__(self, slicer_type, version):
        self.slicer_type = slicer_type
        self.version = version

    def get_speed_tolerance(self):
        raise NotImplementedError("You must implement get_speed_tolerance")

    def get_num_slow_layers(self):
        raise NotImplementedError("You must implement get_num_slow_layers")

    def get_gcode_generation_settings(self):
        """Returns OctolapseSlicerSettings"""
        raise NotImplementedError("You must implement get_gcode_generation_settings")

    def get_missing_gcode_generation_settings(self):
        settings = self.get_gcode_generation_settings()
        assert(isinstance(settings, OctolapseGcodeSettings))
        issue_list = []
        if settings.retraction_length is None:
            issue_list.append("Retraction Length")
        if settings.retraction_speed is None:
            issue_list.append("Retraction Speed")
        if settings.deretraction_speed is None:
            issue_list.append("Deretraction Speed")
        if settings.x_y_travel_speed is None:
            issue_list.append("X/Y Travel Speed")
        if settings.z_lift_height is None:
            issue_list.append("Z Lift Height")
        if settings.z_lift_speed is None:
            issue_list.append("Z Travel Speed")
        if settings.retract_before_move is None:
            issue_list.append("Retract Before Move")
        if settings.lift_when_retracted is None:
            issue_list.append("Lift When Retracted")
        return issue_list

    def get_print_features(self, print_feature_settings):
        """"Returns OctolapseSlicerSettings"""
        raise NotImplementedError("You must implement get_print_features")

    def get_speed_mm_min(self, speed, multiplier=None, speed_name=None):
        """Returns a speed in mm/min for a setting name"""
        raise NotImplementedError("You must implement get_speed_mm_min")

    def update_settings_from_gcode(self, settings_dict):
        raise NotImplementedError("You must implement update_settings_from_gcode")


class CuraSettings(SlicerSettings):
    def __init__(self, version="unknown"):
        super(CuraSettings, self).__init__(SlicerSettings.SlicerTypeCura, version)
        self.retraction_amount = None
        self.retraction_retract_speed = None
        self.retraction_prime_speed = None
        self.retraction_hop_enabled = None  # new setting
        self.retraction_enable = None  # new setting
        self.speed_print = None
        self.speed_infill = None
        self.speed_wall_0 = None
        self.speed_wall_x = None
        self.speed_topbottom = None
        self.speed_travel = None
        self.speed_print_layer_0 = None
        self.speed_travel_layer_0 = None
        self.skirt_brim_speed = None
        self.max_feedrate_z_override = None
        self.speed_slowdown_layers = None
        self.retraction_hop = None
        self.axis_speed_display_settings = 'mm-sec'
        self.layer_height = None
        self.smooth_spiralized_contours = None
        self.magic_mesh_surface_mode = None
        self.combing_mode = None

    def get_num_slow_layers(self):
        if self.speed_slowdown_layers is None or len("{}".format(self.speed_slowdown_layers).strip()) == 0:
            return None

        return int(self.speed_slowdown_layers)

    def get_speed_tolerance(self):
        return 0.1 / 60.0 / 2.0

    def get_gcode_generation_settings(self):
        settings = OctolapseGcodeSettings()
        settings.retraction_length = self.get_retraction_amount()
        settings.retraction_speed = self.get_retraction_retract_speed()
        settings.deretraction_speed = self.get_retraction_prime_speed()
        settings.x_y_travel_speed = self.get_speed_travel()
        settings.first_layer_travel_speed = self.get_slow_layer_speed_travel()
        settings.z_lift_height = self.get_retraction_hop()
        settings.z_lift_speed = self.get_speed_travel_z()
        settings.retract_before_move = (
            self.retraction_enable and settings.retraction_length is not None and settings.retraction_length > 0
        )
        settings.lift_when_retracted = (
            settings.retract_before_move and
            self.retraction_hop_enabled and
            settings.retraction_length is not None
            and settings.retraction_length > 0
        )
        settings.layer_height = self.layer_height
        settings.vase_mode = self.smooth_spiralized_contours and self.magic_mesh_surface_mode == "surface"
        return settings

    def get_wipe_speed(self):
        return self.speed_travel * 0.8

    def get_wipe_enabled(self):
        return self.combing_mode is not None and self.combing_mode != "" and self.combing_mode != "off"

    def get_retraction_amount(self):
        if self.retraction_amount is None or len("{}".format(self.retraction_amount).strip()) == 0:
            return None
        return float(self.retraction_amount)

    def get_retraction_hop(self):
        if self.retraction_hop is None or len("{}".format(self.retraction_hop).strip()) == 0:
            return None
        return float(self.retraction_hop)

    def get_speed_print(self):
        return self.get_speed_mm_min(self.speed_print)

    def get_slow_layer_speed_print(self):
        return self.get_speed_mm_min(self.speed_print_layer_0)

    def get_retraction_retract_speed(self):
        return self.get_speed_mm_min(self.retraction_retract_speed)

    def get_retraction_prime_speed(self):
        return self.get_speed_mm_min(self.retraction_prime_speed)

    def get_speed_infill(self):
        return self.get_speed_mm_min(self.speed_infill)

    def get_speed_wall_0(self):
        return self.get_speed_mm_min(self.speed_wall_0)

    def get_speed_wall_x(self):
        return self.get_speed_mm_min(self.speed_wall_x)

    def get_speed_topbottom(self):
        return self.get_speed_mm_min(self.speed_topbottom)

    def get_speed_travel(self):
        return self.get_speed_mm_min(self.speed_travel)

    def get_slow_layer_speed_travel(self):
        return self.get_speed_mm_min(self.speed_travel_layer_0)

    def get_skirt_brim_speed(self):
        return self.get_speed_mm_min(self.skirt_brim_speed)

    def get_speed_travel_z(self):
        z_max_feedrate = self.get_speed_mm_min(self.max_feedrate_z_override)
        travel_feedrate = self.get_speed_mm_min(self.speed_travel)
        if z_max_feedrate == 0:
            return travel_feedrate
        return min(z_max_feedrate, travel_feedrate)

    def get_print_features(self, stabilization_profile):
        return [
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Print Speed",
                "Initial Layer(s)",
                self.get_speed_print(),
                self.get_slow_layer_speed_print(),
                stabilization_profile.feature_trigger_on_normal_print_speed,
                (
                    stabilization_profile.feature_trigger_on_first_layer
                ),
                self.get_speed_tolerance(),
                self.get_num_slow_layers()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Retract",
                None,
                self.get_retraction_retract_speed(),
                None,
                stabilization_profile.feature_trigger_on_retract,
                None,
                self.get_speed_tolerance(),
                0
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Prime",
                None,
                self.get_retraction_prime_speed(),
                None,
                stabilization_profile.feature_trigger_on_deretract,
                None,
                self.get_speed_tolerance(),
                0
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Infill",
                "",
                self.get_speed_infill(),
                None,
                stabilization_profile.feature_trigger_on_infill,
                None,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Outer Wall",
                None,
                self.get_speed_wall_0(),
                None,
                stabilization_profile.feature_trigger_on_external_perimeters,
                None,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Inner Wall",
                None,
                self.get_speed_wall_x(),
                None,
                stabilization_profile.feature_trigger_on_perimeters,
                None,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Top/Bottom",
                None,
                self.get_speed_topbottom(),
                None,
                stabilization_profile.feature_trigger_on_top_solid_infill,
                None,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Travel",
                "Slow Layer Travel",
                self.get_speed_travel(),
                self.get_slow_layer_speed_travel(),
                stabilization_profile.feature_trigger_on_movement,
                stabilization_profile.feature_trigger_on_first_layer_travel,
                self.get_speed_tolerance(),
                self.get_num_slow_layers()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Skirt/Brim",
                None,
                self.get_skirt_brim_speed(),
                None,
                stabilization_profile.feature_trigger_on_skirt_brim,
                None,
                self.get_speed_tolerance(),
                0
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Z Travel",
                None,
                self.get_speed_travel_z(),
                None,
                stabilization_profile.feature_trigger_on_z_movement,
                None,
                self.get_speed_tolerance(),
                0
            )
        ]

    def get_speed_mm_min(self, speed, multiplier=None, speed_name=None):
        if speed is None or len("{}".format(speed).strip()) == 0:
            return None

        # Convert speed to mm/min
        speed = float(speed) * 60.0
        # round to .1
        return utility.round_to(speed, 0.1)

    def update_settings_from_gcode(self, settings_dict):
        # for cura we can just call the regular update function!
        self.update(settings_dict)


class Simplify3dSettings(SlicerSettings):

    def __init__(self, version="unknown"):
        super(Simplify3dSettings, self).__init__(SlicerSettings.SlicerTypeSimplify3D, version)
        self.retraction_distance = None
        self.retraction_vertical_lift = None
        self.retraction_speed = None
        self.first_layer_speed_multiplier = None
        self.above_raft_speed_multiplier = None
        self.prime_pillar_speed_multiplier = None
        self.ooze_shield_speed_multiplier = None
        self.default_printing_speed = None
        self.outline_speed_multiplier = None
        self.solid_infill_speed_multiplier = None
        self.support_structure_speed_multiplier = None
        self.x_y_axis_movement_speed = None
        self.z_axis_movement_speed = None
        self.bridging_speed_multiplier = None
        self.extruder_use_retract = None
        self.spiral_vase_mode = None
        self.layer_height = None
        # simplify has a fixed speed tolerance
        self.axis_speed_display_settings = 'mm-min'

    def get_num_slow_layers(self):
        return 1

    def get_speed_tolerance(self):
        return 1

    def get_gcode_generation_settings(self):
        """Returns OctolapseSlicerSettings"""
        settings = OctolapseGcodeSettings()
        settings.retraction_length = self.get_retraction_distance()
        settings.retraction_speed = self.get_retract_speed()
        settings.deretraction_speed = self.get_deretract_speed()
        settings.x_y_travel_speed = self.get_x_y_axis_movement_speed()
        settings.first_layer_travel_speed = self.get_x_y_axis_movement_speed()
        settings.z_lift_height = self.get_retraction_vertical_lift()
        settings.z_lift_speed = self.get_z_axis_movement_speed()
        settings.retract_before_move = (
            self.extruder_use_retract and settings.retraction_length is not None and settings.retraction_length > 0
        )
        settings.lift_when_retracted = (
            settings.retract_before_move and settings.z_lift_height is not None and settings.z_lift_height > 0
        )
        settings.vase_mode = self.spiral_vase_mode
        settings.layer_height = self.layer_height

        return settings

    def get_speed_mm_min(self, speed, multiplier=None, speed_name=None, is_half_speed_multiplier=False):
        if speed is None or len(str(speed).strip()) == 0:
            return None
        speed = float(speed)
        if multiplier is not None and not len(str(multiplier).strip()) == 0:
            if is_half_speed_multiplier:
                speed = 100.0 - (100 - float(multiplier) / 2.0)
            else:
                speed = speed * float(multiplier) / 100.0

        return utility.round_to(speed, 0.1)

    def get_wipe_speed(self):
        return self.get_x_y_axis_movement_speed() * 0.8

    def get_retraction_distance(self):
        return float(self.retraction_distance)

    def get_retraction_vertical_lift(self):
        return float(self.retraction_vertical_lift)

    def get_retract_speed(self):
        return self.get_speed_mm_min(self.retraction_speed)

    def get_deretract_speed(self):
        return self.get_retract_speed()

    def get_above_raft_speed(self):
        return self.get_speed_mm_min(self.get_default_printing_speed(), multiplier=self.above_raft_speed_multiplier)

    def get_prime_pillar_speed(self):
        return self.get_speed_mm_min(self.default_printing_speed, multiplier=self.prime_pillar_speed_multiplier)

    def get_first_layer_prime_pillar_speed(self):
        return self.get_speed_mm_min(
            self.get_prime_pillar_speed(),
            multiplier=self.first_layer_speed_multiplier
        )

    def get_ooze_shield_speed(self):
        return self.get_speed_mm_min(self.default_printing_speed, multiplier=self.ooze_shield_speed_multiplier)

    def get_first_layer_ooze_shield_speed(self):
        return self.get_speed_mm_min(
            self.get_ooze_shield_speed(),
            multiplier=self.first_layer_speed_multiplier
        )

    def get_default_printing_speed(self):
        return self.get_speed_mm_min(self.default_printing_speed)

    def get_first_layere_default_printing_speed(self):
        return self.get_speed_mm_min(self.default_printing_speed, multiplier=self.first_layer_speed_multiplier)

    def get_exterior_outline_speed(self):
        return self.get_speed_mm_min(self.default_printing_speed, multiplier=self.outline_speed_multiplier)

    def get_first_layer_exterior_outline_speed(self):
        return self.get_speed_mm_min(
                self.get_exterior_outline_speed(),
                multiplier=self.first_layer_speed_multiplier
            )

    def get_interior_outline_speed(self):
        return self.get_speed_mm_min(
            self.default_printing_speed, multiplier=self.outline_speed_multiplier, is_half_speed_multiplier=True
        )

    def get_first_layer_interior_outline_speed(self):
        return self.get_speed_mm_min(self.get_interior_outline_speed(), multiplier=self.first_layer_speed_multiplier)

    def get_solid_infill_speed(self):
        return self.get_speed_mm_min(self.default_printing_speed, multiplier=self.solid_infill_speed_multiplier)

    def get_first_layer_solid_infill_speed(self):
        return self.get_speed_mm_min(self.get_solid_infill_speed(), multiplier=self.first_layer_speed_multiplier)

    def get_support_structure_speed(self):
        return self.get_speed_mm_min(self.default_printing_speed, multiplier=self.support_structure_speed_multiplier)

    def get_first_layer_support_structure_speed(self):
        return self.get_speed_mm_min(
            self.get_support_structure_speed(),
            multiplier=self.first_layer_speed_multiplier
        )

    def get_x_y_axis_movement_speed(self):
        return self.get_speed_mm_min(self.x_y_axis_movement_speed)

    def get_z_axis_movement_speed(self):
        return self.get_speed_mm_min(self.z_axis_movement_speed)

    def get_bridge_speed(self):
        return self.get_speed_mm_min(self.default_printing_speed, multiplier=self.bridging_speed_multiplier)

    def get_first_prime_speed(self):
        return self.get_speed_mm_min(self.get_retract_speed(), multiplier=30)

    def get_print_features(self, stabilization_profile):
        return [
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Retraction",
                None,
                self.get_retract_speed(),
                None,
                stabilization_profile.feature_trigger_on_retract,
                stabilization_profile.feature_trigger_on_retract,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Above Raft",
                None,
                self.get_above_raft_speed(),
                None,
                stabilization_profile.feature_trigger_on_above_raft,
                stabilization_profile.feature_trigger_on_above_raft,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Prime Pillar",
                "First Layer Prime Pillar",
                self.get_prime_pillar_speed(),
                self.get_first_layer_prime_pillar_speed(),
                stabilization_profile.feature_trigger_on_prime_pillar,
                stabilization_profile.feature_trigger_on_prime_pillar and stabilization_profile.feature_trigger_on_first_layer,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Ooze Shield",
                "First Layer Ooze Shield",
                self.get_ooze_shield_speed(),
                self.get_first_layer_ooze_shield_speed(),
                stabilization_profile.feature_trigger_on_ooze_shield,
                stabilization_profile.feature_trigger_on_ooze_shield and stabilization_profile.feature_trigger_on_first_layer,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Printing Speed",
                "First Layer Printing Speed",
                self.get_default_printing_speed(),
                self.get_first_layere_default_printing_speed(),
                stabilization_profile.feature_trigger_on_normal_print_speed,
                (
                    stabilization_profile.feature_trigger_on_normal_print_speed and
                    stabilization_profile.feature_trigger_on_first_layer
                ),
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Exterior Outlines",
                "First Layer Exterior Outlines",
                self.get_exterior_outline_speed(),
                self.get_first_layer_exterior_outline_speed(),
                stabilization_profile.feature_trigger_on_external_perimeters,
                (
                    stabilization_profile.feature_trigger_on_external_perimeters and
                    stabilization_profile.feature_trigger_on_first_layer
                ),
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Interior Outlines",
                "First Layer Interior Outlines",
                self.get_interior_outline_speed(),
                self.get_first_layer_interior_outline_speed(),
                stabilization_profile.feature_trigger_on_perimeters,
                stabilization_profile.feature_trigger_on_perimeters and stabilization_profile.feature_trigger_on_first_layer,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Solid Infill",
                "First Layer Solid Infill",
                self.get_solid_infill_speed(),
                self.get_first_layer_solid_infill_speed(),
                stabilization_profile.feature_trigger_on_solid_infill,
                stabilization_profile.feature_trigger_on_solid_infill and stabilization_profile.feature_trigger_on_first_layer,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Supports",
                "First Layer Supports",
                self.get_support_structure_speed(),
                self.get_first_layer_support_structure_speed(),
                stabilization_profile.feature_trigger_on_supports,
                stabilization_profile.feature_trigger_on_supports and stabilization_profile.feature_trigger_on_first_layer,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "X/Y Movement",
                None,
                self.get_x_y_axis_movement_speed(),
                None,
                stabilization_profile.feature_trigger_on_movement,
                None,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Z Movement",
                None,
                self.get_z_axis_movement_speed(),
                None,
                stabilization_profile.feature_trigger_on_z_movement,
                None,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Bridging",
                None,
                self.get_bridge_speed(),
                None,
                stabilization_profile.feature_trigger_on_bridges,
                None,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                None,
                "First Prime",
                None,
                self.get_first_prime_speed(),
                None,
                stabilization_profile.feature_trigger_on_deretract and stabilization_profile.feature_trigger_on_first_layer,
                self.get_speed_tolerance()
            )
        ]

    def update_settings_from_gcode(self, settings_dict):

        def _primary_extruder():
            return settings_dict["primary_extruder"]

        def _retraction_distance():
            return settings_dict["extruder_retraction_distance"][_primary_extruder()]

        def _retraction_vertical_lift():
            return settings_dict["extruder_retraction_z_lift"][_primary_extruder()]

        def _retraction_speed():
            return settings_dict["extruder_retraction_speed"][_primary_extruder()]

        def _get_speed_multiplier(multiplier):
            if multiplier is not None:
                return float(multiplier) * 100
            return 100

        def _first_layer_speed_multiplier():
            return _get_speed_multiplier(settings_dict["first_layer_underspeed"])

        def _above_raft_speed_multiplier():
            return _get_speed_multiplier(settings_dict["above_raft_speed_multiplier"])

        def _prime_pillar_speed_multiplier():
            return _get_speed_multiplier(settings_dict["prime_pillar_speed_multiplier"])

        def _ooze_shield_speed_multiplier():
            return _get_speed_multiplier(settings_dict["ooze_shield_speed_multiplier"])

        def _default_printing_speed():
            return settings_dict["default_speed"]

        def _outline_speed_multiplier():
            return _get_speed_multiplier(settings_dict["outline_underspeed"])

        def _solid_infill_speed_multiplier():
            return _get_speed_multiplier(settings_dict["solid_infill_underspeed"])

        def _support_structure_speed_multiplier():
            return _get_speed_multiplier(settings_dict["support_underspeed"])

        def _x_y_axis_movement_speed():
            return settings_dict["rapid_xy_speed"]

        def _z_axis_movement_speed():
            return settings_dict["rapid_z_speed"]

        def _bridging_speed_multiplier():
            return _get_speed_multiplier(settings_dict["bridging_speed_multiplier"])

        def _extruder_use_retract():
            return settings_dict["extruder_use_retract"][_primary_extruder()]

        # for simplify we need to manually update the settings :(
        self.retraction_distance = _retraction_distance()
        self.retraction_vertical_lift = _retraction_vertical_lift()
        self.retraction_speed = _retraction_speed()
        self.first_layer_speed_multiplier = _first_layer_speed_multiplier()
        self.above_raft_speed_multiplier = _above_raft_speed_multiplier()
        self.prime_pillar_speed_multiplier = _prime_pillar_speed_multiplier()
        self.ooze_shield_speed_multiplier = _ooze_shield_speed_multiplier()
        self.default_printing_speed = _default_printing_speed()
        self.outline_speed_multiplier = _outline_speed_multiplier()
        self.solid_infill_speed_multiplier = _solid_infill_speed_multiplier()
        self.support_structure_speed_multiplier = _support_structure_speed_multiplier()
        self.x_y_axis_movement_speed = _x_y_axis_movement_speed()
        self.z_axis_movement_speed = _z_axis_movement_speed()
        self.bridging_speed_multiplier = _bridging_speed_multiplier()
        self.extruder_use_retract = _extruder_use_retract()


class Slic3rPeSettings(SlicerSettings):
    def __init__(self, version="unknown"):
        super(Slic3rPeSettings, self).__init__(SlicerSettings.SlicerTypeSlic3rPe, version)
        self.retract_before_travel = None
        self.retract_length = None
        self.retract_lift = None
        self.deretract_speed = None
        self.retract_speed = None
        self.perimeter_speed = None
        self.small_perimeter_speed = ''
        self.external_perimeter_speed = ''
        self.infill_speed = None
        self.solid_infill_speed = ''
        self.top_solid_infill_speed = ''
        self.support_material_speed = None
        self.bridge_speed = None
        self.gap_fill_speed = None
        self.travel_speed = None
        self.first_layer_speed = ''
        self.axis_speed_display_units = 'mm-sec'
        self.layer_height = None
        self.spiral_vase = None

    def get_speed_mm_min(self, speed, multiplier=None, setting_name=None):
        if speed is None:
            return None
        speed = float(speed)
        if self.axis_speed_display_units == "mm-sec":
            speed = speed * 60.0
        return speed

    def get_num_slow_layers(self):
        return 1

    def get_speed_tolerance(self):
        return 0.01 / 60.0 / 2.0

    def get_gcode_generation_settings(self):
        settings = OctolapseGcodeSettings()
        settings.retraction_length = self.get_retract_length()
        settings.retraction_speed = self.get_retract_speed()
        settings.deretraction_speed = self.get_deretract_speed()
        settings.x_y_travel_speed = self.get_travel_speed()
        settings.first_layer_travel_speed = self.get_travel_speed()
        settings.z_lift_height = self.get_retract_lift()
        settings.z_lift_speed = self.get_z_travel_speed()
        # calculate retract before travel and lift when retracted
        settings.retract_before_move = self.get_retract_before_travel()
        settings.lift_when_retracted = self.get_lift_when_retracted()
        settings.layer_height = self.layer_height
        settings.vase_mode = self.spiral_vase
        return settings

    def get_retract_before_travel(self):
        retract_length = self.get_retract_length()
        if (
            self.retract_before_travel is not None and
            float(self.retract_before_travel) > 0 and
            retract_length is not None and
            retract_length > 0
        ):
            return True
        return False

    def get_lift_when_retracted(self):
        retract_lift = self.get_retract_lift()
        if (
            self.get_retract_before_travel()
            and retract_lift is not None
            and retract_lift > 0
        ):
            return True
        return False

    def get_z_travel_speed(self):
        return self.get_travel_speed()

    def get_retract_length(self):
        if self.retract_length is None:
            return None

        return utility.round_to(float(self.retract_length), 0.00001)

    def get_retract_lift(self):
        if self.retract_lift is None:
            return None

        return utility.round_to(float(self.retract_lift), 0.001)

    @staticmethod
    def parse_percent(parse_string):
        try:
            if parse_string is None:
                return None
            if isinstance(parse_string, string_types):
                percent_index = "{}".format(parse_string).strip().find('%')
                if percent_index < 1:
                    return None
                try:
                    percent = float("{}".format(parse_string).encode(u'utf-8').translate(None, b'%')) / 100.0
                    return percent
                except ValueError:
                    return None
            return None
        except Exception as e:
            raise e

    def get_speed_from_setting(
        self, speed_setting, is_first_layer=False, has_base_setting=False, base_setting=None, round_to=0.01
    ):

        first_layer_multiplier = 1.0
        if is_first_layer:
            first_layer_multiplier = self.parse_percent(self.first_layer_speed)
            if first_layer_multiplier is None:
                if self.first_layer_speed is None or len("{}".format(self.first_layer_speed).strip()) == 0:
                    return None
                # If the first layer speed is not a percent, return it
                return utility.round_to(float(self.first_layer_speed), round_to)

        if speed_setting is None or len("{}".format(speed_setting).strip()) == 0:
            return None

        # see if the small perimeter speed is a percent
        speed_setting_percent = self.parse_percent(speed_setting)
        if speed_setting_percent is not None:
            # the small perimeter speed is not a percent, scale it by the first layer percent
            if has_base_setting and (base_setting is None or len("{}".format(base_setting).strip()) == 0):
                return None
            speed_setting = float(base_setting) * speed_setting_percent
        else:
            speed_setting = float(speed_setting)

        return utility.round_to(speed_setting * first_layer_multiplier * 60.0, round_to)

    def get_first_layer_perimeter_speed(self):
        return self.get_speed_from_setting(
            self.perimeter_speed,
            is_first_layer=True
        )

    def get_small_perimeter_speed(self):
        return self.get_speed_from_setting(
            self.small_perimeter_speed,
            base_setting=self.perimeter_speed,
            has_base_setting=True
        )

    def get_first_layer_small_perimeter_speed(self):
        return self.get_speed_from_setting(
            self.small_perimeter_speed,
            base_setting=self.perimeter_speed,
            has_base_setting=True,
            is_first_layer=True
        )

    def get_external_perimeter_speed(self):
        return self.get_speed_from_setting(
            self.small_perimeter_speed,
            base_setting=self.perimeter_speed,
            has_base_setting=True
        )

    def get_first_layer_external_perimeter_speed(self):
        return self.get_speed_from_setting(
            self.external_perimeter_speed,
            base_setting=self.perimeter_speed,
            has_base_setting=True,
            is_first_layer=True
        )

    def get_first_layer_infill_speed(self):
        return self.get_speed_from_setting(
            self.infill_speed,
            is_first_layer=True
        )

    def get_solid_infill_speed(self):
        return self.get_speed_from_setting(
            self.solid_infill_speed,
            base_setting=self.infill_speed,
            has_base_setting=True
        )

    def get_first_layer_solid_infill_speed(self):
        return self.get_speed_from_setting(
            self.solid_infill_speed,
            base_setting=self.infill_speed,
            has_base_setting=True,
            is_first_layer=True
        )

    def get_top_solid_infill_speed(self):
        return self.get_speed_from_setting(
            self.top_solid_infill_speed,
            base_setting=self.infill_speed,
            has_base_setting=True
        )

    def get_first_layer_top_solid_infill_speed(self):
        return self.get_speed_from_setting(
            self.top_solid_infill_speed,
            base_setting=self.infill_speed,
            has_base_setting=True,
            is_first_layer=True
        )

    def get_first_layer_supports_speed(self):
        return self.get_speed_from_setting(
            self.support_material_speed,
            is_first_layer=True
        )

    def get_first_layer_gaps_speed(self):
        return self.get_speed_from_setting(
            self.gap_fill_speed,
            is_first_layer=True
        )

    def get_travel_speed(self):
        return self.get_speed_from_setting(
            self.travel_speed
        )

    def get_wipe_speed(self):
        travel_speed = self.get_travel_speed()
        if travel_speed is not None:
            return travel_speed * 0.8
        return None

    def get_retract_speed(self):
        return self.get_speed_from_setting(
            self.retract_speed,
            round_to=1
        )

    def get_deretract_speed(self):
        if self.deretract_speed is None or len("{}".format(self.deretract_speed).strip()) == 0:
            return None
        deretract_speed = self.deretract_speed

        if float(self.deretract_speed) == 0:
            if self.retract_speed is None or len("{}".format(self.retract_speed).strip()) == 0:
                return None
            deretract_speed = self.retract_speed

        return self.get_speed_from_setting(
            deretract_speed,
            round_to=1
        )

    def get_perimeter_speed(self):
        return self.get_speed_from_setting(
            self.perimeter_speed
        )

    def get_infill_speed(self):
        return self.get_speed_from_setting(
            self.infill_speed
        )

    def get_support_material_speed(self):
        return self.get_speed_from_setting(
            self.support_material_speed
        )

    def get_bridge_speed(self):
        return self.get_speed_from_setting(
            self.bridge_speed
        )

    def get_gap_fill_speed(self):
        return self.get_speed_from_setting(
            self.gap_fill_speed
        )

    def get_print_features(self, stabilization_profile):
        return [
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Retraction",
                None,
                self.get_retract_speed(),
                None,
                stabilization_profile.feature_trigger_on_retract,
                None,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Deretraction",
                None,
                self.get_deretract_speed(),
                None,
                stabilization_profile.feature_trigger_on_deretract,
                None,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Perimeters",
                "First Layer Perimeters",
                self.get_perimeter_speed(),
                self.get_first_layer_perimeter_speed(),
                stabilization_profile.feature_trigger_on_perimeters,
                stabilization_profile.feature_trigger_on_perimeters and stabilization_profile.feature_trigger_on_first_layer,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Small Perimeters",
                "First Layer Small Perimeters",
                self.get_small_perimeter_speed(),
                self.get_first_layer_small_perimeter_speed(),
                stabilization_profile.feature_trigger_on_small_perimeters,
                (
                    stabilization_profile.feature_trigger_on_small_perimeters and
                    stabilization_profile.feature_trigger_on_first_layer
                ),
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "External Perimeters",
                "First Layer External Perimeters",
                self.get_external_perimeter_speed(),
                self.get_first_layer_external_perimeter_speed(),
                stabilization_profile.feature_trigger_on_external_perimeters,
                (
                    stabilization_profile.feature_trigger_on_external_perimeters and
                    stabilization_profile.feature_trigger_on_first_layer
                ),
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Infill",
                "First Layer Infill",
                self.get_infill_speed(),
                self.get_first_layer_infill_speed(),
                stabilization_profile.feature_trigger_on_infill,
                stabilization_profile.feature_trigger_on_infill and stabilization_profile.feature_trigger_on_first_layer,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Solid Infill",
                "First Layer Solid Infill",
                self.get_solid_infill_speed(),
                self.get_first_layer_solid_infill_speed(),
                stabilization_profile.feature_trigger_on_solid_infill,
                stabilization_profile.feature_trigger_on_solid_infill and stabilization_profile.feature_trigger_on_first_layer,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Top Solid Infill",
                "First Layer Top Solid Infill",
                self.get_top_solid_infill_speed(),
                self.get_first_layer_top_solid_infill_speed(),
                stabilization_profile.feature_trigger_on_top_solid_infill,
                (
                    stabilization_profile.feature_trigger_on_top_solid_infill and
                    stabilization_profile.feature_trigger_on_first_layer
                ),
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Supports",
                "First Layer Supports",
                self.get_support_material_speed(),
                self.get_first_layer_supports_speed(),
                stabilization_profile.feature_trigger_on_supports,
                stabilization_profile.feature_trigger_on_supports and stabilization_profile.feature_trigger_on_first_layer,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Bridges",
                None,
                self.get_bridge_speed(),
                None,
                stabilization_profile.feature_trigger_on_bridges,
                None,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Gaps",
                "First Layer Gaps",
                self.get_gap_fill_speed(),
                self.get_first_layer_gaps_speed(),
                stabilization_profile.feature_trigger_on_gap_fills,
                stabilization_profile.feature_trigger_on_gap_fills and stabilization_profile.feature_trigger_on_first_layer,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Travel",
                None,
                self.get_travel_speed(),
                None,
                stabilization_profile.feature_trigger_on_movement,
                None,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Wipe",
                None,
                self.get_wipe_speed(),
                None,
                stabilization_profile.feature_trigger_on_wipe,
                None,
                self.get_speed_tolerance()
            )
        ]

    def update_settings_from_gcode(self, settings_dict):
        try:
            for key, value in settings_dict.items():
                class_item = getattr(self, key, '{octolapse_no_property_found}')
                if not (isinstance(class_item, string_types) and class_item == '{octolapse_no_property_found}'):
                    if key in [
                        'support_material_interface_speed',
                        'support_material_xy_spacing',
                        'fill_density',
                        'infill_overlap',
                        'top_solid_infill_speed',
                        'first_layer_speed',
                        'small_perimeter_speed',
                        'solid_infill_speed',
                        'external_perimeter_speed'
                    ]:
                        if 'percent' in value:
                            self.__dict__[key] = "{}%".format(value['percent'])
                        elif 'mm' in value:
                            self.__dict__[key] = value['mm']
                    elif key == 'version':
                        self.version = value["version"]
                    elif isinstance(class_item, Settings):
                        class_item.update(value)
                    else:
                        self.__dict__[key] = self.try_convert_value(class_item, value, key)
        except Exception as e:
            raise e

    @classmethod
    def try_convert_value(cls, destination, value, key):
        if value is None or (isinstance(value, string_types) and value == 'None'):
            return None
        # all of the following can be either strings or percent strings, we need to save them as strings
        if(
            key in [
                'support_material_interface_speed',
                'support_material_xy_spacing',
                'fill_density',
                'infill_overlap',
                'top_solid_infill_speed',
                'first_layer_speed',
                'small_perimeter_speed',
                'solid_infill_speed',
                'external_perimeter_speed'
            ]
        ):
            return "{}".format(value)

        return super(Slic3rPeSettings, cls).try_convert_value(destination, value, key)


class OtherSlicerSettings(SlicerSettings):
    def __init__(self, version="unknown"):
        super(OtherSlicerSettings, self).__init__(SlicerSettings.SlicerTypeOther, version)
        self.retract_length = None
        self.z_hop = None
        self.travel_speed = None
        self.first_layer_travel_speed = None
        self.retract_speed = None
        self.deretract_speed = None
        self.print_speed = None
        self.first_layer_print_speed = None
        self.z_travel_speed = None
        self.perimeter_speed = None
        self.small_perimeter_speed = None
        self.external_perimeter_speed = None
        self.infill_speed = None
        self.solid_infill_speed = None
        self.top_solid_infill_speed = None
        self.support_speed = None
        self.bridge_speed = None
        self.gap_fill_speed = None
        self.skirt_brim_speed = None
        self.above_raft_speed = None
        self.ooze_shield_speed = None
        self.prime_pillar_speed = None
        self.num_slow_layers = None
        self.lift_when_retracted = None
        self.retract_before_move = None
        self.speed_tolerance = 1
        self.axis_speed_display_units = 'mm-min'
        self.vase_mode = None
        self.layer_height = None

    def update_settings_from_gcode(self, settings_dict):
        raise Exception("Cannot update 'Other Slicer' from gcode file!  Please select another slicer type to use this "
                        "function.")

    def get_num_slow_layers(self):
        return self.num_slow_layers

    def get_speed_tolerance(self):
        if self.axis_speed_display_units == 'mm-sec':
            return self.speed_tolerance * 60.0
        return self.speed_tolerance

    def get_gcode_generation_settings(self):
        """Returns OctolapseSlicerSettings"""
        settings = OctolapseGcodeSettings()
        settings.retraction_length = self.get_retract_length()
        settings.retraction_speed = self.get_retract_speed()
        settings.deretraction_speed = self.get_deretract_speed()
        settings.x_y_travel_speed = self.get_travel_speed()
        settings.first_layer_travel_speed = self.get_first_layer_travel_speed()
        settings.z_lift_height = self.get_z_hop()
        settings.z_lift_speed = self.get_z_hop_speed()
        settings.lift_when_retracted = self.lift_when_retracted
        settings.retract_before_move = self.retract_before_move
        settings.layer_height = self.layer_height
        settings.vase_mode = self.vase_mode
        return settings

    def get_retract_length(self):
        return self.retract_length

    def get_z_hop(self):
        return self.z_hop

    def get_z_hop_speed(self):
        return self.get_travel_speed()

    def get_speed_mm_min(self, speed, multiplier=None, setting_name=None):
        if speed is None:
            return None
        speed = float(speed)
        if self.axis_speed_display_units == "mm-sec":
            speed = speed * 60.0
        # Todo - Look at this, we need to round prob.
        return speed

    def get_print_speed(self):
        return self.get_speed_mm_min(self.print_speed)

    def get_first_layer_print_speed(self):
        return self.get_speed_mm_min(self.first_layer_print_speed)

    def get_first_layer_travel_speed(self):
        return self.get_speed_mm_min(self.first_layer_travel_speed)

    def get_travel_speed(self):
        return self.get_speed_mm_min(self.travel_speed)

    def get_z_travel_speed(self):
        return self.get_speed_mm_min(self.z_travel_speed)

    def get_retract_speed(self):
        return self.get_speed_mm_min(self.retract_speed)

    def get_deretract_speed(self):
        return self.get_speed_mm_min(self.deretract_speed)

    def get_perimeter_speed(self):
        return self.get_speed_mm_min(self.perimeter_speed)

    def get_small_perimeter_speed(self):
        return self.get_speed_mm_min(self.small_perimeter_speed)

    def get_external_perimeter_speed(self):
        return self.get_speed_mm_min(self.external_perimeter_speed)

    def get_infill_speed(self):
        return self.get_speed_mm_min(self.infill_speed)

    def get_solid_infill_speed(self):
        return self.get_speed_mm_min(self.solid_infill_speed)

    def get_top_solid_infill_speed(self):
        return self.get_speed_mm_min(self.top_solid_infill_speed)

    def get_support_speed(self):
        return self.get_speed_mm_min(self.support_speed)

    def get_bridge_speed(self):
        return self.get_speed_mm_min(self.bridge_speed)

    def get_gap_fill_speed(self):
        return self.get_speed_mm_min(self.gap_fill_speed)

    def get_above_raft_speed(self):
        return self.get_speed_mm_min(self.above_raft_speed)

    def get_ooze_shield_speed(self):
        return self.get_speed_mm_min(self.ooze_shield_speed)

    def get_prime_pillar_speed(self):
        return self.get_speed_mm_min(self.prime_pillar_speed)

    def get_skirt_brim_speed(self):
        return self.get_speed_mm_min(self.skirt_brim_speed)

    def get_print_features(self, stabilization_profile):
        return [
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Print Speed",
                "First Layer Print Speed",
                self.get_print_speed(),
                self.get_first_layer_print_speed(),
                stabilization_profile.feature_trigger_on_normal_print_speed,
                stabilization_profile.feature_trigger_on_first_layer,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Travel",
                "First Layer Travel",
                self.get_travel_speed(),
                self.get_first_layer_travel_speed(),
                stabilization_profile.feature_trigger_on_movement,
                stabilization_profile.feature_trigger_on_first_layer,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Z Movement",
                None,
                self.get_z_travel_speed(),
                None,
                stabilization_profile.feature_trigger_on_z_movement,
                None,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Retraction",
                None,
                self.get_retract_speed(),
                None,
                stabilization_profile.feature_trigger_on_retract,
                None,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Deretraction",
                None,
                self.get_deretract_speed(),
                None,
                stabilization_profile.feature_trigger_on_deretract,
                None,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Perimeters",
                None,
                self.get_perimeter_speed(),
                None,
                stabilization_profile.feature_trigger_on_perimeters,
                None,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Small Perimeters",
                None,
                self.get_small_perimeter_speed(),
                None,
                stabilization_profile.feature_trigger_on_small_perimeters,
                None,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "External Perimeters",
                None,
                self.get_external_perimeter_speed(),
                None,
                stabilization_profile.feature_trigger_on_external_perimeters,
                None,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Infill",
                None,
                self.get_infill_speed(),
                None,
                stabilization_profile.feature_trigger_on_infill,
                None,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Solid Infill",
                None,
                self.get_solid_infill_speed(),
                None,
                stabilization_profile.feature_trigger_on_solid_infill,
                None,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Top Solid Infill",
                None,
                self.get_top_solid_infill_speed(),
                None,
                stabilization_profile.feature_trigger_on_top_solid_infill,
                None,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Supports",
                None,
                self.get_support_speed(),
                None,
                stabilization_profile.feature_trigger_on_supports,
                None,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Bridges",
                None,
                self.get_bridge_speed(),
                None,
                stabilization_profile.feature_trigger_on_bridges,
                None,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Gap Fills",
                None,
                self.get_gap_fill_speed(),
                None,
                stabilization_profile.feature_trigger_on_gap_fills,
                None,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Above Raft",
                None,
                self.get_above_raft_speed(),
                None,
                stabilization_profile.feature_trigger_on_above_raft,
                None,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Ooze Shield",
                None,
                self.get_ooze_shield_speed(),
                None,
                stabilization_profile.feature_trigger_on_ooze_shield,
                None,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Prime Pillar",
                None,
                self.get_prime_pillar_speed(),
                None,
                stabilization_profile.feature_trigger_on_prime_pillar,
                None,
                self.get_speed_tolerance()
            ),
            PrintFeatureSetting(
                SlicerPrintFeatures.is_enabled, SlicerPrintFeatures.is_detected,
                "Skirt/Brim",
                None,
                self.get_skirt_brim_speed(),
                None,
                stabilization_profile.feature_trigger_on_skirt_brim,
                None,
                self.get_speed_tolerance()
            )
        ]


class SlicerPrintFeatures(Settings):
    def __init__(self, slicer_settings, stabilization_settings):
        assert (isinstance(slicer_settings, SlicerSettings))
        assert (isinstance(stabilization_settings, StabilizationProfile))
        self.previous_speed = 0
        self.previous_is_one_enabled = False
        self.num_slow_layers = slicer_settings.get_num_slow_layers()
        self.speed_tolerance = slicer_settings.get_speed_tolerance()
        try:
            self.features = slicer_settings.get_print_features(stabilization_settings)
        except Exception as e:
            raise e
        self.feature_detection_enabled = stabilization_settings.feature_restrictions_enabled

    @staticmethod
    def is_enabled(feature, current_speed, layer_num):
        """Calculates actual print speeds for a print feature"""
        if current_speed is None:
            return False

        if not (
            layer_num is None
            or feature.num_slow_layers < 1
            or layer_num > feature.num_slow_layers
            or feature.speed == feature.under_speed
            or feature.under_speed is None
        ):
            if not feature.enabled_for_slow_layer:
                return False
            if feature.num_slow_layers > 1:
                calculated_speed = (
                    feature.under_speed + (
                        (layer_num - 1) * (feature.speed - feature.under_speed) / feature.num_slow_layers
                    )
                )
            else:
                calculated_speed = feature.under_speed
        else:
            if not feature.enabled:
                return False
            calculated_speed = feature.speed

        if calculated_speed is not None and utility.is_close(current_speed, calculated_speed, feature.tolerance):
            return True
        else:
            return False

    @staticmethod
    def is_detected(feature, current_speed, layer_num):
        """Calculates actual print speeds for a print feature"""
        if current_speed is None:
            return False

        if not (
            layer_num is None
            or feature.num_slow_layers < 1
            or layer_num > feature.num_slow_layers
            or feature.speed == feature.under_speed
            or feature.under_speed is None
        ):
            layer_name = feature.slow_layer_name
            if feature.num_slow_layers > 1:
                calculated_speed = (
                    feature.under_speed + (
                        (layer_num - 1) * (feature.speed - feature.under_speed) / feature.num_slow_layers)
                )
            else:
                calculated_speed = feature.under_speed
        else:
            layer_name = feature.layer_name
            calculated_speed = feature.speed

        if calculated_speed is not None and utility.is_close(current_speed, calculated_speed, feature.tolerance):
            return True, layer_name
        else:
            return False

    def is_one_feature_enabled(self, speed, layer_num):
        if not self.feature_detection_enabled:
            return True

        if self.previous_speed == speed:
            return self.previous_is_one_enabled

        self.previous_speed = speed

        is_one_enabled = False
        for feature in self.features:
            assert (isinstance(feature, PrintFeatureSetting))
            if feature.is_enabled_function(feature, speed, layer_num):
                is_one_enabled = True
                break
        self.previous_is_one_enabled = is_one_enabled
        return is_one_enabled

    def get_printing_features_list(self, current_speed, layer_number):
        printing_features = []
        if self.feature_detection_enabled:
            for feature in self.features:
                assert (isinstance(feature, PrintFeatureSetting))
                val = feature.is_detected_function(feature, current_speed, layer_number)
                if val:
                    printing_features.append(val[1])
        return printing_features

    def get_feature_dict(
        self, speed_units, include_all_features=False, include_missing_speeds=True, include_nonunique_speeds=True
    ):
        all_speed_list = []
        non_unique_speed_dict = {}
        non_unique_speed_list = []
        missing_speeds_list = []
        missing_speeds_list_unique = []
        divisor = 1.0
        if speed_units == 'mm-sec':
            divisor = 60.0
        # create a list by name and a dict by speed
        for feature in self.features:
            assert (isinstance(feature, PrintFeatureSetting))
            speed = None
            under_speed = None
            # calculate speed and underspeed
            if feature.speed is not None:
                speed = feature.speed / divisor
            if feature.under_speed is not None:
                under_speed = feature.under_speed / divisor

            # add non_unique speeds
            if include_nonunique_speeds:
                if speed is not None:
                    if speed in non_unique_speed_dict:
                        non_unique_speed_dict[speed].append(feature.layer_name)
                    else:
                        non_unique_speed_dict[speed] = [feature.layer_name]
                if under_speed is not None:
                    if under_speed in non_unique_speed_dict:
                        non_unique_speed_dict[under_speed].append(feature.slow_layer_name)
                    else:
                        non_unique_speed_dict[under_speed] = [feature.slow_layer_name]

            # add features for speed and underspeed
            if include_all_features:
                if speed is not None:
                    all_speed_list.append(
                        {
                            'name': feature.layer_name,
                            'speed': speed,
                            'is_underspeed': False,
                            'description': ''
                        }
                    )
                if under_speed is not None:
                    all_speed_list.append(
                        {
                            'name': feature.slow_layer_name,
                            'speed': under_speed,
                            'is_underspeed': True,
                            'description': ''
                        }
                    )

            # add any missing features
            if include_missing_speeds:
                if speed is None and feature.layer_name is not None and len(feature.layer_name.strip()) > 0:
                    missing_speeds_list.append(feature.layer_name)
                if (
                    under_speed is None
                    and feature.slow_layer_name is not None
                    and len(feature.slow_layer_name.strip()) > 0
                ):
                    missing_speeds_list.append(feature.slow_layer_name)

        if include_nonunique_speeds:
            # erase any unique speeds from the non-unique speed list
            keys_to_delete = [key for key in non_unique_speed_dict if len(non_unique_speed_dict[key]) == 1]
            for key in keys_to_delete:
                del non_unique_speed_dict[key]

        if include_missing_speeds:
            # remove any duplicates from missing speed list
            seen = set()
            seen_add = seen.add
            missing_speeds_list_unique = [x for x in missing_speeds_list if not (x in seen or seen_add(x))]

        # convert the non_unique speed dict into an array of dicts so that it is easily iterable in javascript
        for key, val in non_unique_speed_dict.items():
            key_string = "{}{}".format(key, speed_units)
            non_unique_speed_list.append({"speed": key_string, "feature_names": val})

        return {
            'non-unique-speeds': non_unique_speed_list,
            'all-features': all_speed_list,
            'missing-speeds': missing_speeds_list_unique
        }


class PrintFeatureSetting(Settings):
    def __init__(
        self, is_enabled_function, is_detected_function, layer_name, initial_layer_name, speed, under_speed,
        enabled, enabled_for_slow_layer, tolerance, num_slow_layers=1
    ):
        self.layer_name = layer_name
        self.slow_layer_name = initial_layer_name
        self.speed = speed
        self.under_speed = under_speed
        self.is_detected_function = is_detected_function
        self.is_enabled_function = is_enabled_function
        self.enabled = enabled
        self.enabled_for_slow_layer = enabled_for_slow_layer
        self.num_slow_layers = num_slow_layers
        self.tolerance = tolerance
        self.calculated_speed = None
        self.calculated_layer_name = layer_name
        self.triggered = False
        self.detected = False

    def __repr__(self):
        return pprint.pformat(vars(self), indent=4, width=1)
