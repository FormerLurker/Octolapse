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
from __future__ import unicode_literals
import shutil
import copy
import json
import os
import uuid
import tempfile
import sys
import re
import errno
from octoprint_octolapse_setuptools import NumberedVersion
import octoprint_octolapse.utility as utility
import octoprint_octolapse.log as log
import math
# remove python 2 support
#try:
#    from collections.abc import Iterable
#except ImportError:
#    # Python 2.7
#    from collections import Iterable
from collections.abc import Iterable
import octoprint_octolapse.settings_preprocessor as settings_preprocessor
import octoprint_octolapse.migration as migration
from octoprint_octolapse.gcode_processor import GcodeProcessor, ParsedCommand
# remove unused usings
# import six
from octoprint_octolapse.error_messages import OctolapseException
import inspect
# create the module level logger
from octoprint_octolapse.log import LoggingConfigurator
logging_configurator = LoggingConfigurator()
logger = logging_configurator.get_logger(__name__)


class SettingsJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if issubclass(type(obj), Settings):
            # Remove python 2 support
            # return {k: v for (k, v) in six.iteritems(obj.to_dict()) if not k.startswith("_")}
            return {k: v for (k, v) in obj.to_dict().items() if not k.startswith("_")}
        elif issubclass(type(obj), StaticSettings):
            return obj.__dict__
        # Let the base class default method raise the TypeError
        elif isinstance(obj, bool):
            return "{}".format(obj).lower()
        elif isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


class NonstaticSettingsJsonEncoder(SettingsJsonEncoder):
   def default(self, obj):
        if isinstance(obj, StaticSettings):
            return None
        return super(NonstaticSettingsJsonEncoder, self).default(obj)


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
        copy_dict = self.__dict__.copy()
        property_list = [p for p in dir(self) if isinstance(getattr(type(self), p, None), property)]
        for prop in property_list:
            copy_dict[prop] = getattr(self, prop)
        return copy_dict

    def to_json(self):
        # remove private variables
        # Remove python 2 support
        # filtered_dict = {k: v for (k, v) in six.iteritems(self.to_dict()) if not k.startswith("_")}
        filtered_dict = {k: v for (k, v) in self.to_dict().items() if not k.startswith("_")}
        return json.dumps(filtered_dict, cls=SettingsJsonEncoder)

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

        if not isinstance(iterable, Iterable):
            to_dict = getattr(iterable, "to_dict", None)
            if callable(to_dict):
                item_to_iterate = iterable.to_dict()
            else:
                item_to_iterate = iterable.__dict__

        for key, value in item_to_iterate.items():
            try:
                if key.startswith("_"):
                    continue
                class_item = getattr(source, key, '{octolapse_no_property_found}')
                # Remove python 2 support
                # if not (isinstance(class_item, six.string_types) and class_item == '{octolapse_no_property_found}'):
                if not (isinstance(class_item, str) and class_item == '{octolapse_no_property_found}'):
                    if isinstance(class_item, Settings):
                        class_item.update(value)
                    elif isinstance(class_item, StaticSettings):
                        pass
                    else:
                        # todo - Do not set the dict directly in other places.  Consider rewriting whole file since this methos of updating/serializing/deserializing is extremely painful
                        setattr(source, key, source.try_convert_value(class_item, value, key))
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
            floatValue = float(value)
            # sometimes the destination can be an int, but the value is a float
            if int(floatValue) == floatValue:
                return int(floatValue)
            return floatValue
        else:
            # default action, just return the value
            return value

    def save_as_json(self, output_file_path):
        # use a temporary file so that if there is an error creating the json the
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        try:
            json.dump(self.to_dict(), temp_file, cls=NonstaticSettingsJsonEncoder)
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

    def __setattr__(self, a, v):
        attr = getattr(self.__class__, a, None)
        if isinstance(attr, property):
            if attr.fset is None:
                raise AttributeError("No setter is available for the current attribute.")
            attr.fset(self, v)
        else:
            super(Settings, self).__setattr__(a, v)


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


class AutomaticConfiguration(Settings):
    def __init__(self):
        self.key_values = None
        self.version = None
        self.suppress_update_notification_version = False
        self.is_custom = False

    def is_updatable_from_server(self):
        if self.key_values is None:
            return False

        for key in self.key_values:
            if "value" not in key or key["value"] is None or key["value"] == "null":
                return False

        return not self.is_custom

    def get_server_update_identifiers_dict(self):
        return {
            'version': self.version,
            'suppress_update_notification_version': self.suppress_update_notification_version,
            'key_values': self.key_values
        }

    def suppress_updates(self, available_profile):
        if NumberedVersion(self.version) < NumberedVersion(available_profile["version"]):
            self.suppress_update_notification_version = available_profile["version"]

    def try_convert_value(cls, destination, value, key):
        if key == 'suppress_update_notification_version':
            if not value:
                return False
            else:
                return value
        return super(AutomaticConfiguration, cls).try_convert_value(destination, value, key)


class PrinterProfileSlicers(Settings):
    def __init__(self):
        self.cura = CuraSettings()
        self.simplify_3d = Simplify3dSettings()
        self.slic3r_pe = Slic3rPeSettings()
        self.other = OtherSlicerSettings()


class AutomaticConfigurationProfile(ProfileSettings):
    def __init__(self, name="Automatic Configuration Profile"):
        super(AutomaticConfigurationProfile, self).__init__(name)
        self.automatic_configuration = AutomaticConfiguration()

    @classmethod
    def update_from_server_profile(cls, current_profile, server_profile_dict):
        # make sure I didn't make a version mistake
        # we don't want to alter the provided profile information, so make copies
        current_profile_copy = current_profile.clone()
        # copy the profile portion of the profile
        server_profile_copy = copy.deepcopy(server_profile_dict)
        # save our current automatic configuration settings
        is_custom = current_profile_copy.automatic_configuration.is_custom

        # when updating, we don't want to change any of the guids, slicer settings,
        # gcode generation settings, so remove those items from the server profile
        if 'guid' in server_profile_copy:
            del server_profile_copy["guid"]

        # now update everything else
        current_profile_copy.update(server_profile_copy)

        # restore the previous automatic configuration setting
        current_profile_copy.automatic_configuration.is_custom = is_custom
        # clear the previous notification suppression version
        current_profile_copy.automatic_configuration.suppress_update_notification_version = None

        return current_profile_copy

    def is_updatable_from_server(self):
        return self.automatic_configuration.is_updatable_from_server()

    def get_server_update_identifiers_dict(self):
        identifiers = self.automatic_configuration.get_server_update_identifiers_dict()
        identifiers["guid"] = self.guid
        return identifiers

    def suppress_updates(self, available_profile):
        self.automatic_configuration.suppress_updates(available_profile)


class ExtruderOffset(Settings):
    def __init__(self):
        self.x = 0
        self.y = 0

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y
        }


class PrinterProfile(AutomaticConfigurationProfile):
    OCTOLAPSE_COMMAND = "@OCTOLAPSE"
    DEFAULT_OCTOLAPSE_SNAPSHOT_COMMAND = "TAKE-SNAPSHOT"
    LEGACY_SNAPSHOT_COMMAND = "SNAP"
    minimum_height_increment = 0.05
    bed_type_rectangular = 'rectangular'
    bed_type_circular = 'circular'
    origin_type_front_left = 'front_left'
    origin_type_center = 'center'

    def __init__(self, name="New Printer Profile"):
        super(PrinterProfile, self).__init__(name)
        # flag that is false until the profile has been saved by the user at least once
        # this is used to show a warning to the user if a new printer profile is used
        # without being configured
        self.automatic_configuration = AutomaticConfiguration()
        self.has_been_saved_by_user = False
        self.slicer_type = "automatic"
        self.gcode_generation_settings = OctolapseGcodeSettings()
        self.slicers = PrinterProfileSlicers()
        self._snapshot_command_text = ""
        self._parsed_snapshot_command = ParsedCommand(None,None,None)
        self.suppress_snapshot_command_always = True
        self.auto_detect_position = True
        self.origin_type = PrinterProfile.origin_type_front_left
        self.home_x = None
        self.home_y = None
        self.home_z = None
        self.override_octoprint_profile_settings = False
        self.bed_type = PrinterProfile.bed_type_rectangular
        self.diameter_xy = 0.0
        self.width = 0.0
        self.depth = 0.0
        self.height = 0.0
        self.custom_bounding_box = False
        self.min_x = 0.0
        self.max_x = 0.0
        self.min_y = 0.0
        self.max_y = 0.0
        self.min_z = 0.0
        self.max_z = 0.0
        self.restrict_snapshot_area = False
        self.snapshot_diameter_xy = 0.0
        self.snapshot_min_x = 0.0
        self.snapshot_max_x = 0.0
        self.snapshot_min_y = 0.0
        self.snapshot_max_y = 0.0
        self.snapshot_min_z = 0.0
        self.snapshot_max_z = 0.0
        self.auto_position_detection_commands = ""
        self.priming_height = 0.75  # Extrusion must occur BELOW this level before layer tracking will begin
        self.minimum_layer_height = 0.05  # Layer tracking won't start until extrusion at this height is reached.
        self.e_axis_default_mode = 'absolute'  # other values are 'relative' and 'absolute'
        self.g90_influences_extruder = 'false'  # other values are 'true' and 'false'
        self.xyz_axes_default_mode = 'absolute'  # other values are 'relative' and 'absolute'
        self.units_default = 'millimeters'
        self.axis_speed_display_units = 'mm-min'
        self.default_firmware_retractions = False
        self.default_firmware_retractions_zhop = False
        self.gocde_axis_compatibility_mode_enabled = True
        self.home_axis_gcode = "G90; Switch to Absolute XYZ\r\nG28 X Y; Home XY Axis"
        self.num_extruders = 1
        self.shared_extruder = False
        self.zero_based_extruder = True
        self.extruder_offsets = []
        self.default_extruder = 1  # The default extruder is 1 based!  It is not an index.

    @property
    def snapshot_command(self):
        return self._snapshot_command_text

    @snapshot_command.setter
    def snapshot_command(self, snapshot_command_text):
        parsed_command = GcodeProcessor.parse(snapshot_command_text)
        self._parsed_snapshot_command = parsed_command
        self._snapshot_command_text = snapshot_command_text
        return len(parsed_command.gcode) > 0

    def get_snapshot_command_gcode(self):
        if self._parsed_snapshot_command.gcode is None or len(self._parsed_snapshot_command.gcode) == 0:
            return None
        return self._parsed_snapshot_command.gcode

    @staticmethod
    def validate_snapshot_command(command_string):
        # there needs to be at least one non-comment non-whitespace character for the gcode command to work.
        parsed_command = GcodeProcessor.parse(command_string)
        return len(parsed_command.gcode)>0

    def is_snapshot_command(self, command_string):
        if command_string is None or len(command_string) == 0:
            return False
        snapshot_command_gcode = self.get_snapshot_command_gcode()
        return (
            (snapshot_command_gcode and snapshot_command_gcode == command_string) or
            command_string.startswith("{0} {1}".format(PrinterProfile.OCTOLAPSE_COMMAND, PrinterProfile.DEFAULT_OCTOLAPSE_SNAPSHOT_COMMAND)) or
            PrinterProfile.LEGACY_SNAPSHOT_COMMAND == command_string
        )

    @classmethod
    def update_from_server_profile(cls, current_profile, server_profile_dict):
        # make sure I didn't make a version mistake
        # we don't want to alter the provided profile information, so make copies
        current_profile_copy = current_profile.clone()
        # copy the profile portion of the profile
        server_profile_copy = copy.deepcopy(server_profile_dict)
        # save our current automatic configuration settings
        is_custom = current_profile_copy.automatic_configuration.is_custom


        # when updating, we don't want to change any of the guids, slicer settings,
        # gcode generation settings, so remove those items from the server profile
        if 'guid' in server_profile_copy:
            del server_profile_copy["guid"]
        if 'slicer_type' in server_profile_copy:
            del server_profile_copy["slicer_type"]
        if 'slicers' in server_profile_copy:
            del server_profile_copy["slicers"]
        if 'gcode_generation_settings' in server_profile_copy:
            del server_profile_copy["gcode_generation_settings"]

        # now update everything else
        current_profile_copy.update(server_profile_copy)

        # restore the previous automatic configuration setting
        current_profile_copy.automatic_configuration.is_custom = is_custom
        # clear the previous notification suppression version
        current_profile_copy.automatic_configuration.suppress_update_notification_version = None

        return current_profile_copy

    def is_updatable_from_server(self):
        return self.automatic_configuration.is_updatable_from_server()

    def get_server_update_identifiers_dict(self):
        identifiers = self.automatic_configuration.get_server_update_identifiers_dict()
        identifiers["guid"] = self.guid
        return identifiers

    def _get_overridable_settings_dict(self):
        settings_dict = {}
        volume_dict = {}
        volume_dict["bed_type"] = self.bed_type
        volume_dict["origin_type"] = self.origin_type
        if self.custom_bounding_box:
            # set the bounds to the custom box
            volume_dict["min_x"] = float(self.min_x)
            volume_dict["max_x"] = float(self.max_x)
            volume_dict["min_y"] = float(self.min_y)
            volume_dict["max_y"] = float(self.max_y)
            volume_dict["min_z"] = float(self.min_z)
            volume_dict["max_z"] = float(self.max_z)
        else:
            if self.bed_type == "circular":
                radius_xy = float(self.diameter_xy) / 2.0
                volume_dict["min_x"] = -1.0 * radius_xy
                volume_dict["max_x"] = radius_xy
                volume_dict["min_y"] = -1.0 * radius_xy
                volume_dict["max_y"] = radius_xy
            else:
                # see if we have a custom bounding box
                volume_dict["min_x"] = 0.0
                volume_dict["max_x"] = float(self.width)
                volume_dict["min_y"] = 0.0
                volume_dict["max_y"] = float(self.depth)
            volume_dict["min_z"] = 0.0
            volume_dict["max_z"] = float(self.height)

        if not self.restrict_snapshot_area:
            volume_dict["bounds"] = False
        else:
            if self.bed_type == "circular":
                radius_xy = float(self.snapshot_diameter_xy) / 2.0
                volume_dict["bounds"] = {
                    "min_x": -1 * radius_xy,
                    "max_x": radius_xy,
                    "min_y": -1 * radius_xy,
                    "max_y": radius_xy,
                }
            else:
                volume_dict["bounds"] = {
                    "min_x": float(self.snapshot_min_x),
                    "max_x": float(self.snapshot_max_x),
                    "min_y": float(self.snapshot_min_y),
                    "max_y": float(self.snapshot_max_y),
                }
            volume_dict["bounds"]["min_z"] = float(self.snapshot_min_z)
            volume_dict["bounds"]["max_z"] = float(self.snapshot_max_z)

        settings_dict["volume"] = volume_dict
        return settings_dict

    @staticmethod
    def get_octoprint_settings_dict(octoprint_printer_profile):
        settings_dict = {}
        volume = octoprint_printer_profile["volume"]
        # see if this is a circular or rectangular bed
        custom_box = volume["custom_box"]
        volume_dict = {}

        if volume["formFactor"] == "circle":
            volume_dict["bed_type"] = "circular"
        else:
            volume_dict["bed_type"] = "rectangular"

        volume_dict["origin_type"] = volume["origin"]

        if custom_box:
            # set the bounds to the custom box
            volume_dict["min_x"] = float(custom_box["x_min"])
            volume_dict["max_x"] = float(custom_box["x_max"])
            volume_dict["min_y"] = float(custom_box["y_min"])
            volume_dict["max_y"] = float(custom_box["y_max"])
            volume_dict["min_z"] = float(custom_box["z_min"])
            volume_dict["max_z"] = float(custom_box["z_max"])
        else:
            if volume["formFactor"] == "circle":
                radius_xy = float(volume["width"])/2.0
                volume_dict["min_x"] = -1.0 * radius_xy
                volume_dict["max_x"] = radius_xy
                volume_dict["min_y"] = -1.0 * radius_xy
                volume_dict["max_y"] = radius_xy
            else:
                # see if we have a custom bounding box
                volume_dict["min_x"] = 0.0
                volume_dict["max_x"] = float(volume["width"])
                volume_dict["min_y"] = 0.0
                volume_dict["max_y"] = float(volume["depth"])
            volume_dict["min_z"] = 0.0
            volume_dict["max_z"] = float(volume["height"])

        # there can be no bounds on the default octoprint printer profile
        volume_dict["bounds"] = False

        settings_dict["volume"] = volume_dict
        return settings_dict

    # Gets a bounding box or circle for the current printer profile
    # takes into account any octoprint printer profile settings if
    # they are not overridden
    def get_overridable_profile_settings(self, octoprint_g90_influences_extruder, octoprint_printer_profile):
        # Get Volume
        if self.override_octoprint_profile_settings:
            settings_dict = self._get_overridable_settings_dict()
        else:
            settings_dict = PrinterProfile.get_octoprint_settings_dict(octoprint_printer_profile)

        # get g90 influences extruder
        if self.g90_influences_extruder == 'use-octoprint-settings':
            settings_dict["g90_influences_extruder"] = octoprint_g90_influences_extruder
        else:
            settings_dict["g90_influences_extruder"] = self.g90_influences_extruder == 'true'

        return settings_dict

    @staticmethod
    def get_options():
        return {
            'origin_type_options': [
                dict(value=PrinterProfile.origin_type_front_left, name='Front Left'),
                dict(value=PrinterProfile.origin_type_center, name='Center')
            ],
            'bed_type_options': [
                dict(value=PrinterProfile.bed_type_rectangular, name='Rectangular'),
                dict(value=PrinterProfile.bed_type_circular, name='Circular')
            ],
            'gcode_configuration_options': [
                dict(value='use-slicer-settings', name='Use Slicer Settings'),
                dict(value='manual', name='Manual Configuration')
            ],
            'slicer_type_options': [
                dict(value='automatic', name='Automatic Configuration'),
                dict(value='cura_4_2', name='Cura V4.2 and Above'),
                dict(value='cura', name='Cura V4.1 and Below'),
                dict(value='simplify-3d', name='Simplify 3D'),
                dict(value='slic3r-pe', name='Slic3r/Slic3r PE/Prusa Slicer'),
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
            'cura_combing_mode_options': [
                dict(value="off", name='Off'),
                dict(value="all", name='All'),
                dict(value="noskin", name='Not in Skin'),
                dict(value="infill", name='Within Infill'),
            ],
            'server_profiles': None
        }

    def get_current_slicer_settings(self):
        return self.get_slicer_settings_by_type(self.slicer_type)

    def get_slicer_settings_by_type(self, slicer_type):
        if slicer_type == 'slic3r-pe':
            return self.slicers.slic3r_pe
        elif slicer_type == 'simplify-3d':
            return self.slicers.simplify_3d
        elif slicer_type in ['cura', 'cura_4_2']:
            return self.slicers.cura
        elif slicer_type == 'other':
            return self.slicers.other
        return None  # we return None on automatic.  This profile needs to be accessed directly

    def get_current_state_detection_settings(self):
        if self.slicer_type == 'automatic':
            return None
        return self.get_current_slicer_settings().get_gcode_generation_settings(slicer_type=self.slicer_type)

    def get_gcode_settings_from_file(self, gcode_file_path):
        simplify_preprocessor = settings_preprocessor.Simplify3dSettingsProcessor(
            search_direction="both", max_forward_search=1000, max_reverse_search=1000
        )
        slic3r_preprocessor = settings_preprocessor.Slic3rSettingsProcessor(
            search_direction="both", max_forward_search=1000, max_reverse_search=1000
        )
        cura_preprocessor = settings_preprocessor.CuraSettingsProcessor(
            search_direction="both", max_forward_search=1000, max_reverse_search=1000
        )
        file_processor = settings_preprocessor.GcodeFileProcessor(
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
            elif self.slicer_type in ['cura', 'cura_4_2']:
                new_slicer_settings = CuraSettings()
            else:
                raise Exception("An invalid slicer type has been detected while extracting settings from gcode.")

            new_slicer_settings.update_settings_from_gcode(new_settings, self)

            # check to make sure all of the required settings are there
            missing_settings = new_slicer_settings.get_missing_gcode_generation_settings(slicer_type=self.slicer_type)
            if len(missing_settings) > 0:
                return False, 'required-settings-missing', missing_settings
            # copy the settings into the current profile
            current_slicer_settings = self.get_current_slicer_settings()
            current_slicer_settings.update(new_slicer_settings)
            self.gcode_generation_settings.update(
                current_slicer_settings.get_gcode_generation_settings(
                    slicer_type=self.slicer_type
                )
            )

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
        if key in ['home_x', 'home_y', 'home_z']:
            if value is not None:
                return float(value)
        elif key == "extruder_offsets" and isinstance(value, list):
            result = []
            for offset in value:
                extruder_offset = ExtruderOffset()
                extruder_offset.update(offset)
                result.append(extruder_offset)
            return result
        return super(PrinterProfile, cls).try_convert_value(destination, value, key)

    def get_position_args(self, overridable_profile_settings):

        # get the settings that cannot be overridden by Octoprint settings

        # Get the number of extruders from the current gocode generation settings
        gcode_generation_settings = self.get_current_state_detection_settings()
        num_extruders = gcode_generation_settings.get_num_extruders()

        default_extruder = self.default_extruder
        if num_extruders < default_extruder:
            # we must have used automatic gcode settings extraction.
            default_extruder = num_extruders

        extruder_offsets = []
        if not self.shared_extruder and self.num_extruders > 1:
            extruder_offsets = [x.to_dict() for x in self.extruder_offsets]
        position_args = {
            "location_detection_commands": self.get_location_detection_command_list(),
            "xyz_axis_default_mode": self.xyz_axes_default_mode,
            "e_axis_default_mode": self.e_axis_default_mode,
            "units_default": self.units_default,
            "autodetect_position": self.auto_detect_position,
            "slicer_settings": gcode_generation_settings.to_dict(),
            "zero_based_extruder": self.zero_based_extruder,
            "priming_height": self.priming_height,
            "minimum_layer_height": self.minimum_layer_height,
            "num_extruders": num_extruders,
            "shared_extruder": self.shared_extruder,
            "default_extruder_index": default_extruder - 1,  # The default extruder is 1 based!
            "extruder_offsets": extruder_offsets,
            "home_position": {
                "home_x": None if self.home_x is None else float(self.home_x),
                "home_y": None if self.home_y is None else float(self.home_y),
                "home_z": None if self.home_z is None else float(self.home_z),
            }
        }
        # merge the overridable settings
        position_args.update(overridable_profile_settings)
        return position_args


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


class StabilizationProfile(AutomaticConfigurationProfile):
    STABILIZATION_AXIS_TYPE_DISABLED = 'disabled'
    STABILIZATION_AXIS_TYPE_FIXED_COORDINATE = 'fixed_coordinate'
    STABILIZATION_AXIS_TYPE_FIXED_PATH = 'fixed_path'
    STABILIZATION_AXIS_TYPE_RELATIVE_COORDINATE = 'relative'
    STABILIZATION_AXIS_TYPE_RELATIVE_PATH = 'relative_path'

    def __init__(self, name="New Stabilization Profile"):
        super(StabilizationProfile, self).__init__(name)
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
        self.wait_for_moves_to_finish = True

    def is_disabled(self):
        return (
            self.x_type == StabilizationProfile.STABILIZATION_AXIS_TYPE_DISABLED and
            self.y_type == StabilizationProfile.STABILIZATION_AXIS_TYPE_DISABLED
        )

    def get_stabilization_paths(self):
        x_stabilization_path = StabilizationPath()
        x_stabilization_path.type = self.x_type
        if self.x_type == StabilizationProfile.STABILIZATION_AXIS_TYPE_FIXED_COORDINATE:
            x_stabilization_path.path.append(self.x_fixed_coordinate)
            x_stabilization_path.coordinate_system = 'absolute'
        elif self.x_type == StabilizationProfile.STABILIZATION_AXIS_TYPE_RELATIVE_COORDINATE:
            x_stabilization_path.path.append(self.x_relative)
            x_stabilization_path.coordinate_system = 'bed_relative'
        elif self.x_type == StabilizationProfile.STABILIZATION_AXIS_TYPE_FIXED_PATH:
            x_stabilization_path.path = self.parse_csv_path(self.x_fixed_path)
            x_stabilization_path.coordinate_system = 'absolute'
            x_stabilization_path.loop = self.x_fixed_path_loop
            x_stabilization_path.invert_loop = self.x_fixed_path_invert_loop
        elif self.x_type == StabilizationProfile.STABILIZATION_AXIS_TYPE_RELATIVE_PATH:
            x_stabilization_path.path = self.parse_csv_path(self.x_relative_path)
            x_stabilization_path.coordinate_system = 'bed_relative'
            x_stabilization_path.loop = self.x_relative_path_loop
            x_stabilization_path.invert_loop = self.x_relative_path_invert_loop

        y_stabilization_path = StabilizationPath()
        y_stabilization_path.type = self.y_type
        if self.y_type == StabilizationProfile.STABILIZATION_AXIS_TYPE_FIXED_COORDINATE:
            y_stabilization_path.path.append(self.y_fixed_coordinate)
            y_stabilization_path.coordinate_system = 'absolute'
        elif self.y_type == StabilizationProfile.STABILIZATION_AXIS_TYPE_RELATIVE_COORDINATE:
            y_stabilization_path.path.append(self.y_relative)
            y_stabilization_path.coordinate_system = 'bed_relative'
        elif self.y_type == StabilizationProfile.STABILIZATION_AXIS_TYPE_FIXED_PATH:
            y_stabilization_path.path = self.parse_csv_path(self.y_fixed_path)
            y_stabilization_path.coordinate_system = 'absolute'
            y_stabilization_path.loop = self.y_fixed_path_loop
            y_stabilization_path.invert_loop = self.y_fixed_path_invert_loop
        elif self.y_type == StabilizationProfile.STABILIZATION_AXIS_TYPE_RELATIVE_PATH:
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
            'real_time_xy_stabilization_type_options': [
                dict(value='disabled', name='Disabled'),
                dict(value='fixed_coordinate', name='Fixed Coordinate'),
                dict(value='fixed_path', name='List of Fixed Coordinates'),
                dict(value='relative', name='Relative Coordinate (0-100)'),
                dict(value='relative_path', name='List of Relative Coordinates')
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

    @classmethod
    def try_convert_value(cls, destination, value, key):
        if key == 'position_restrictions':
            if value is not None:
                return StabilizationProfile.get_trigger_position_restrictions(value)

        return super(StabilizationProfile, cls).try_convert_value(destination, value, key)


class TriggerProfile(AutomaticConfigurationProfile):
    TRIGGER_TYPE_REAL_TIME = "real-time"
    TRIGGER_TYPE_SMART = "smart"
    SMART_TRIGGER_TYPE_SNAP_TO_PRINT = 0
    SMART_TRIGGER_TYPE_FAST = 1
    SMART_TRIGGER_TYPE_COMPATIBILITY = 2
    SMART_TRIGGER_TYPE_HIGH_QUALITY = 3
    EXTRUDER_TRIGGER_IGNORE_VALUE = ""
    EXTRUDER_TRIGGER_REQUIRED_VALUE = "trigger_on"
    EXTRUDER_TRIGGER_FORBIDDEN_VALUE = "forbidden"
    LAYER_TRIGGER_TYPE = 'layer'
    TIMER_TRIGGER_TYPE = 'timer'
    GCODE_TRIGGER_TYPE = 'gcode'

    def __init__(self, name="New Trigger Profile"):
        super(TriggerProfile, self).__init__(name)
        self.trigger_type = TriggerProfile.TRIGGER_TYPE_SMART
        # smart layer trigger options
        self.smart_layer_trigger_type = TriggerProfile.SMART_TRIGGER_TYPE_COMPATIBILITY
        self.smart_layer_snap_to_print_high_quality = False
        self.smart_layer_snap_to_print_smooth = False
        self.smart_layer_disable_z_lift = True
        self.allow_smart_snapshot_commands = True
        # Settings that were formerly in the snapshot profile (now removed)
        self.is_default = False
        self.trigger_subtype = TriggerProfile.LAYER_TRIGGER_TYPE
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
        self.trigger_on_extruding_start = TriggerProfile.EXTRUDER_TRIGGER_REQUIRED_VALUE
        self.trigger_on_extruding = TriggerProfile.EXTRUDER_TRIGGER_REQUIRED_VALUE
        self.trigger_on_primed = TriggerProfile.EXTRUDER_TRIGGER_REQUIRED_VALUE
        self.trigger_on_retracting_start = TriggerProfile.EXTRUDER_TRIGGER_IGNORE_VALUE
        self.trigger_on_retracting = TriggerProfile.EXTRUDER_TRIGGER_IGNORE_VALUE
        self.trigger_on_partially_retracted = TriggerProfile.EXTRUDER_TRIGGER_FORBIDDEN_VALUE
        self.trigger_on_retracted = TriggerProfile.EXTRUDER_TRIGGER_REQUIRED_VALUE
        self.trigger_on_deretracting_start = TriggerProfile.EXTRUDER_TRIGGER_IGNORE_VALUE
        self.trigger_on_deretracting = TriggerProfile.EXTRUDER_TRIGGER_FORBIDDEN_VALUE
        self.trigger_on_deretracted = TriggerProfile.EXTRUDER_TRIGGER_FORBIDDEN_VALUE

    def get_snapshot_plan_options(self):
        if (
            self.trigger_type == TriggerProfile.TRIGGER_TYPE_SMART and
            self.smart_layer_trigger_type == TriggerProfile.SMART_TRIGGER_TYPE_SNAP_TO_PRINT
        ):
            return {
                'disable_z_lift': self.smart_layer_disable_z_lift
            }
        return None

    @staticmethod
    def get_precalculated_trigger_types():
        return [
            TriggerProfile.TRIGGER_TYPE_SMART
        ]

    def get_extruder_trigger_value_string(self, value):
        if value is None:
            return self.EXTRUDER_TRIGGER_IGNORE_VALUE
        elif value:
            return self.EXTRUDER_TRIGGER_REQUIRED_VALUE
        elif not value:
            return self.EXTRUDER_TRIGGER_FORBIDDEN_VALUE

    @staticmethod
    def get_options():
        return {
            'trigger_type_options': [
                dict(value=TriggerProfile.TRIGGER_TYPE_REAL_TIME, name='Real-Time Triggers'),
                dict(value=TriggerProfile.TRIGGER_TYPE_SMART, name='Smart Triggers')
            ], 'real_time_xy_trigger_type_options': [
                dict(value='disabled', name='Disabled'),
                dict(value='fixed_coordinate', name='Fixed Coordinate'),
                dict(value='fixed_path', name='List of Fixed Coordinates'),
                dict(value='relative', name='Relative Coordinate (0-100)'),
                dict(value='relative_path', name='List of Relative Coordinates')
            ], 'smart_layer_trigger_type_options': [
                dict(value='{}'.format(TriggerProfile.SMART_TRIGGER_TYPE_FAST), name='Fast'),
                dict(value='{}'.format(TriggerProfile.SMART_TRIGGER_TYPE_COMPATIBILITY), name='Compatibility'),
                dict(value='{}'.format(TriggerProfile.SMART_TRIGGER_TYPE_HIGH_QUALITY), name='High Quality'),
                dict(value='{}'.format(TriggerProfile.SMART_TRIGGER_TYPE_SNAP_TO_PRINT), name='Snap to Print'),
            ], 'trigger_subtype_options': [
                dict(value=TriggerProfile.LAYER_TRIGGER_TYPE, name="Layer/Height"),
                dict(value=TriggerProfile.TIMER_TRIGGER_TYPE, name="Timer"),
                dict(value=TriggerProfile.GCODE_TRIGGER_TYPE, name="Gcode")
            ], 'position_restriction_shapes': [
                dict(value="rect", name="Rectangle"),
                dict(value="circle", name="Circle")
            ], 'position_restriction_types': [
                dict(value="required", name="Must be inside"),
                dict(value="forbidden", name="Cannot be inside")
            ], 'snapshot_extruder_trigger_options': [
                dict(value=TriggerProfile.EXTRUDER_TRIGGER_IGNORE_VALUE, name='Ignore', visible=True),
                dict(value=TriggerProfile.EXTRUDER_TRIGGER_REQUIRED_VALUE, name='Trigger', visible=True),
                dict(value=TriggerProfile.EXTRUDER_TRIGGER_FORBIDDEN_VALUE, name='Forbidden', visible=True)
            ]
        }

    @staticmethod
    def get_extruder_trigger_value(value):
        # Remove python 2 support
        #if isinstance(value, six.string_types):
        if isinstance(value, str):
            if value is None or len(value) == 0:
                return None
            elif value.lower() == TriggerProfile.EXTRUDER_TRIGGER_REQUIRED_VALUE:
                return True
            elif value.lower() == TriggerProfile.EXTRUDER_TRIGGER_FORBIDDEN_VALUE:
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
                return TriggerProfile.get_trigger_position_restrictions(value)

        return super(TriggerProfile, cls).try_convert_value(destination, value, key)


class RenderingProfile(AutomaticConfigurationProfile):
    default_output_template = "{FAILEDFLAG}{FAILEDSEPARATOR}{GCODEFILENAME}_{PRINTENDTIME}"
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
        self.constant_rate_factor = 28
        self.post_roll_seconds = 0
        self.pre_roll_seconds = 0
        self.output_template = RenderingProfile.default_output_template
        self.enable_watermark = False
        self.selected_watermark = ""
        self.overlay_text_template = ""
        self.overlay_font_path = ""
        self.overlay_font_size = 10
        self.overlay_text_pos = [10, 10]
        self.overlay_text_alignment = "left"  # Text alignment between lines in the overlay.
        self.overlay_text_valign = "top"  # Overall alignment of text box vertically.
        self.overlay_text_halign = "left"  # Overall alignment of text box horizontally.
        self.overlay_text_color = [255, 255, 255, 1.0]
        self.overlay_outline_color = [0, 0, 0, 1.0]
        self.overlay_outline_width = 1
        self.thread_count = 1
        # Snapshot Cleanup
        self.archive_snapshots = False

    def get_overlay_text_color(self):
        return RenderingProfile._get_color_(self.overlay_text_color)

    def get_overlay_outline_color(self):
        return RenderingProfile._get_color_(self.overlay_outline_color)

    @staticmethod
    def _get_color_(rgba_color):
        overlay_text_color = [255, 255, 255, 1.0]
        # Remove python 2 support
        # if isinstance(rgba_color, six.string_types):
        if isinstance(rgba_color, str):
            overlay_text_color = json.loads(rgba_color)
        elif isinstance(rgba_color, list):
            # make sure to copy the list so we don't alter the original
            overlay_text_color = list(rgba_color)
        overlay_text_color[3] = int(overlay_text_color[3] * 255.0)

        # verify and error correct all of the components of the color
        for index, value in enumerate(overlay_text_color):
            # make sure the value is an int
            value = int(value)
            if value < 0:
                value = 0
            elif value > 255:
                value = 255
            overlay_text_color[index] = value

        return overlay_text_color

    @classmethod
    def try_convert_value(cls, destination, value, key):
        if key in ['overlay_text_color', 'overlay_outline_color']:
            # Remove python 2 support
            # if isinstance(value, six.string_types):
            if isinstance(value, str):
                value = json.loads(value)
            if not isinstance(value, list):
                return None

            return value

        return super(RenderingProfile, cls).try_convert_value(destination, value, key)

    @staticmethod
    def get_archive_formats():
        return {
            'zip'
        }
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
                "FPS",
                "CAMERANAME"
            ],
            'overlay_text_templates': [
                "snapshot_number",
                "current_time",
                "time_elapsed",
                "layer",
                "height",
                "x",
                "y",
                "z",
                "e",
                "f",
                "x_snapshot",
                "y_snapshot",
                "gcode_file",
                "gcode_file_name",
                "gcode_file_extension",
                "print_end_state"
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
                dict(value='h264', name='H.264/MPEG-4 AVC (up to 4096x2048)'),
                dict(value='h265', name='H.265/MPEG-4 HEVC (up to 8192×4320)'),
                dict(value='mp4', name='MP4 (libxvid)'),
                dict(value='mpeg', name='MPEG'),
                dict(value='vob', name='VOB'),
            ],
        }


class StreamingServer(Settings):
    def __init__(self, name, server_type):
        self.name = name
        self.server_type = server_type


class MjpgStreamer(StreamingServer):
    server_type = "mjpg-streamer"
    server_name = "mjpg-streamer"

    def __init__(self):
        super(MjpgStreamer, self).__init__(MjpgStreamer.server_name, MjpgStreamer.server_type)
        self.controls = {}

    def controls_match_server(self, server_settings):
        # see if all of the existing settings and controls are the same for this camera, except for the value.
        # loop through each control and see if everything matches except for the value

        # first see if the  number of controls match
        if len(self.controls) != len(server_settings):
            return False
        # Remove python 2 support
        # for key, control in six.iteritems(self.controls):
        for key, control in self.controls.items():
            # convert the key to a string
            key = str(key)
            # if the key is not in the server_settings_dict, they don't match
            if str(key) not in server_settings:
                return False
            # get the server control
            server_control = server_settings[key]

            # see if it matches
            if not control.control_matches_server(server_control):
                return False
        # if we're here, everything matches!
        return True

    def update(self, iterable, **kwargs):
        item_to_iterate = iterable
        if not isinstance(iterable, Iterable):
            item_to_iterate = iterable.__dict__

        for key, value in item_to_iterate.items():
            class_item = getattr(self, key, '{octolapse_no_property_found}')
            # Remove python 2 support
            # if not (isinstance(class_item, six.string_types) and class_item == '{octolapse_no_property_found}'):
            if not (isinstance(class_item, str) and class_item == '{octolapse_no_property_found}'):
                if key == 'controls':
                    self.controls = {}
                    if isinstance(value, dict):
                        for control_key, control in value.items():
                            new_control = MjpgStreamerControl()
                            new_control.update(control)
                            self.controls[control_key] = new_control
                    elif isinstance(value, list):

                        for index in range(len(value)):
                            control = value[index]
                            new_control = MjpgStreamerControl()
                            new_control.order = index
                            new_control.update(control)
                            self.controls[value["id"]] = new_control

                elif isinstance(class_item, Settings):
                    class_item.update(value)
                elif isinstance(class_item, StaticSettings):
                    # don't update any static settings, those come from the class itself!
                    continue
                else:
                    setattr(self, key, self.try_convert_value(class_item, value, key))


class OtherStreamingServer(StreamingServer):
    server_type = "other"
    server_name = "Other"

    def __init__(self):
        super(OtherStreamingServer, self).__init__(OtherStreamingServer.server_name, OtherStreamingServer.server_type)


class MjpgStreamerControl(Settings):
    def __init__(self):
        self.name = None
        self.id = None
        self.type = None
        self.min = None
        self.max = None
        self.step = None
        self.default = None
        self.value = None
        self.dest = None
        self.flags = None
        self.group = None
        self.order = None
        self.menu = {}

    def control_matches_server(self, server_control):
        matches = True
        # get all of the control properties in such a way that if we add more members we won't have to change anything
        members = [
            attr
            for attr
            in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")
        ]
        # loop through all of the members and make sure the server control values are the same
        # but ignore the self.value and self.flags members
        for attr_name in members:
            if attr_name in ["value", "flags"] and attr_name in dir(server_control):
                # ignore the value
                continue
            # skip meta-data fields (these won't be in the server control always)
            if attr_name in ["order"]:
                continue

            if (
                attr_name not in dir(server_control) or
                str(self.__dict__[attr_name]) != str(server_control.__dict__[attr_name])
             ):
                return False
        # if we're here, it matches!
        return True

    def update(self, iterable, **kwargs):
        # first update the item with the super
        super(MjpgStreamerControl, self).update(iterable)

        control = iterable
        # make sure update works for both dicts and MjpgStreamerControl objects
        if isinstance(control, dict):
            control_id = control["id"]
            control_min = float(control["min"])
            control_max = float(control["max"])
            control_step = float(control["step"])
            control_value = float(control["value"])
            control_default = float(control["default"])

        elif isinstance(control, MjpgStreamerControl):
            control_id = control.id
            control_min = float(control.min)
            control_max = float(control.max)
            control_step = float(control.step)
            control_value = float(control.value)
            control_default = float(control.default)

        else:
            raise Exception("Unknown control type of {0} in MjpgStreamerControl.update".format(type(iterable)))

        def get_bounded_value(control_id, control_value, control_min, control_max, control_step):
            if control_min > control_value or control_max < control_value:
                if control_step == 0:
                    # prevent divide by zero
                    return control_value
                control_range = control_max - control_min
                steps = control_range / 2.0 / control_step
                control_value = (control_min + (steps * control_step))
                control_value = utility.round_to_value(control_value, control_step)
                value_str = str(control_value)
            else:
                value_str = str(control_value)
            return value_str.rstrip('0').rstrip('.')

        self.value = get_bounded_value(control_id, control_value, control_min, control_max, control_step)
        self.default = get_bounded_value(control_id, control_default, control_min, control_max, control_step)


class WebcamSettings(Settings):

    def __init__(self):
        self.address = "http://127.0.0.1/webcam/"
        self.snapshot_request_template = "{camera_address}?action=snapshot"
        self.stream_template = "/webcam/?action=stream"
        self.ignore_ssl_error = False
        self.server_type = MjpgStreamer.server_type
        self.username = ""
        self.password = ""
        self.type = None
        self.use_custom_webcam_settings_page = True
        self.mjpg_streamer = MjpgStreamer()
        self.stream_download = False

    def update(self, iterable, **kwargs):
        try:
            item_to_iterate = iterable
            if not isinstance(iterable, Iterable):
                item_to_iterate = iterable.__dict__

            for key, value in item_to_iterate.items():
                class_item = getattr(self, key, '{octolapse_no_property_found}')
                # Remove python 2 support
                # if not (isinstance(class_item, six.string_types) and class_item == '{octolapse_no_property_found}'):
                if not (isinstance(class_item, str) and class_item == '{octolapse_no_property_found}'):
                    if key == 'mjpg_streamer':
                        self.mjpg_streamer.controls = {}
                        if "controls" in value:
                            controls = value["controls"]
                            # controls might be a dict or a list, iterate appropriately
                            if isinstance(controls, dict):
                                # Remove python 2 support
                                # for key, control in six.iteritems(value["controls"]):
                                for key, control in value["controls"].items():
                                    if "id" in control:
                                        self.mjpg_streamer.controls[key] = (
                                            MjpgStreamerControl.create_from(control)
                                        )
                            elif isinstance(controls, list):
                                for control in value["controls"]:
                                    if "id" in control:
                                        self.mjpg_streamer.controls[control["id"]] = (
                                            MjpgStreamerControl.create_from(control)
                                        )
                    elif isinstance(class_item, Settings):
                        class_item.update(value)
                    elif isinstance(class_item, StaticSettings):
                        # don't update any static settings, those come from the class itself!
                        continue
                    else:
                        self.__dict__[key] = self.try_convert_value(class_item, value, key)
        except Exception as e:
            logger.exception("An unexpected exception occurred while updating webcam settings.")
            raise e


class CameraProfile(AutomaticConfigurationProfile):
    camera_type_webcam = 'webcam'
    camera_type_script = 'script'
    camera_type_gcode = 'gcode'

    def __init__(self, name="New Camera Profile"):
        super(CameraProfile, self).__init__(name)
        self.enabled = True
        self.camera_type = CameraProfile.camera_type_webcam
        self.on_before_snapshot_gcode = ""
        self.gcode_camera_script = ""
        self.on_after_snapshot_gcode = ""

        self.on_print_start_script = ""
        # self.print_start_script_timeout_ms = 0
        self.on_before_snapshot_script = ""
        # self.before_snapshot_script_timeout_ms = 0
        self.external_camera_snapshot_script = ""
        self.on_after_snapshot_script = ""
        # self.after_snapshot_script_timeout_ms = 0
        self.on_before_render_script = ""
        # self.before_snapshot_script_timeout_ms = 0
        self.on_after_render_script = ""
        # self.after_snapshot_script_timeout_ms = 0
        self.on_print_end_script = ""
        # self.print_end_script_timeout_ms = 0
        self.delay = 125
        self.timeout_ms = 5000
        self.snapshot_transpose = ""
        self.webcam_settings = WebcamSettings()
        self.enable_custom_image_preferences = False
        self.apply_settings_before_print = True
        self.apply_settings_at_startup = True
        self.apply_settings_when_disabled = True

    def format_snapshot_request_template(self):
        return self.snapshot_request_template.format(camera_address=self.address)

    def format_stream_template(self):
        return self.stream_template.format(camera_address=self.address)

    @staticmethod
    def format_url(url):
        if url[0] == "/":
            url = "http://127.0.0.1" + url
        return url

    @staticmethod
    def get_options():
        return {
            'webcam_server_type_options': [
                dict(value=MjpgStreamer.server_type, name=MjpgStreamer.server_type),
                dict(value=OtherStreamingServer.server_type, name=OtherStreamingServer.server_type)
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
                dict(value=CameraProfile.camera_type_webcam, name='Webcam'),
                dict(value=CameraProfile.camera_type_script, name='External Camera - Script'),
                dict(value=CameraProfile.camera_type_gcode, name='Gcode Camera (built into printer)')
            ],
        }


class LoggerSettings(Settings):
    def __init__(self, name, log_level):
        self.name = name
        self.log_level = log_level

    def to_dict(self):
        return {
            'name': self.name,
            'log_level': self.log_level
        }


class LoggingProfile(AutomaticConfigurationProfile):

    def __init__(self, name="New Logging Profile"):
        super(LoggingProfile, self).__init__(name)
        # Configure the logger if it has not been created
        self.enabled = False
        self.log_to_console = False
        self.default_log_level = log.DEBUG
        self.enabled_loggers = []
        for logger_name in logging_configurator.get_logger_names():
            self.enabled_loggers.append(LoggerSettings(logger_name, self.default_log_level))

    @classmethod
    def try_convert_value(cls, destination, value, key):
        if key == 'enabled_loggers':
            try:
                if value is not None:
                    return LoggingProfile.get_enabled_loggers(value)
            except Exception as e:
                logger.exception("Unable to convert 'enabled_loggers', returning default.")
                return []

        return super(LoggingProfile, cls).try_convert_value(destination, value, key)

    @classmethod
    def get_enabled_loggers(cls, values):
        logger_list = []
        for enabled_logger in values:
            logger_settings = LoggerSettings(enabled_logger["name"], enabled_logger["log_level"])
            logger_list.append(logger_settings)
        return logger_list

    @staticmethod
    def get_options():
        return {
            'logging_levels': [
                dict(value=log.VERBOSE, name='Verbose'),
                dict(value=log.DEBUG, name='Debug'),
                dict(value=log.INFO, name='Info'),
                dict(value=log.WARNING, name='Warning')
            ],
            'all_logger_names': logging_configurator.get_logger_names()
        }


class MainSettings(Settings):

    def __init__(self, plugin_version, git_version):
        # Main Settings
        self.show_navbar_icon = True
        self.show_navbar_when_not_printing = True
        self.is_octolapse_enabled = True
        self.auto_reload_latest_snapshot = True
        self.auto_reload_frames = 5
        self.show_printer_state_changes = False
        self.show_position_changes = False
        self.show_extruder_state_changes = False
        self.show_trigger_state_changes = False
        self.show_snapshot_plan_information = False
        self.cancel_print_on_startup_error = True
        self.platform = sys.platform
        self.version = plugin_version
        self.settings_version = NumberedVersion.CurrentSettingsVersion
        self.git_version = git_version
        self.preview_snapshot_plans = True
        self.preview_snapshot_plan_autoclose = False
        self.preview_snapshot_plan_seconds = 30
        self.automatic_updates_enabled = True
        self.automatic_update_interval_days = 7
        self.snapshot_archive_directory = ""
        self.timelapse_directory = ""
        self.temporary_directory = ""
        self.test_mode_enabled = False

    def get_snapshot_archive_directory(self, data_folder):
        directory = self.snapshot_archive_directory.strip()
        if len(directory) > 0:
            return self.snapshot_archive_directory
        return os.path.join(data_folder, utility.get_default_snapshot_archive_directory_name())

    def get_timelapse_directory(self, octoprint_timelapse_directory):
        directory = self.timelapse_directory.strip()
        if len(directory) > 0:
            return self.timelapse_directory
        return octoprint_timelapse_directory

    def get_temporary_directory(self, data_folder):
        directory = self.temporary_directory.strip()
        if len(directory) > 0:
            return self.temporary_directory
        return os.path.join(data_folder, 'tmp')

    def test_directories(self, data_folder, octoprint_timelapse_directory):
        errors = []
        snapshot_archive_directory = self.get_snapshot_archive_directory(data_folder)
        timelapse_directory = self.get_timelapse_directory(octoprint_timelapse_directory)
        temporary_directory = self.get_temporary_directory(data_folder)
        try:
            results = MainSettings.test_directory(snapshot_archive_directory)
            if not results[0]:
                errors.append({
                    "name": "Snapshot Archive Directory",
                    'error': results[1]
                })
            results = MainSettings.test_directory(timelapse_directory)
            if not results[0]:
                errors.append({
                    "name": "Timelapse Directory",
                    'error': results[1]
                })
            results = MainSettings.test_directory(temporary_directory)
            if not results[0]:
                errors.append({
                    "name": "Temporary Directory",
                    'error': results[1]
                })
        except Exception as e:
            logger.exception("An unexpected exception occurred while testing directories.")
            raise e

        return len(errors) == 0, errors

    @staticmethod
    def test_directory(path):
        # ensure the path is absolute
        if not os.path.isabs(path):
            return False, 'path-not-absolute'

        # ensure the directory exists
        if not os.path.isdir(path):
            try:
                os.makedirs(path)
            except (IOError, OSError) as e:
                return False, 'cannot-create'

        subdirectory = os.path.join(path, "octolapse_test_temp")
        if not os.path.isdir(subdirectory):
            try:
                os.mkdir(subdirectory)
            except (IOError, OSError) as e:
                return False, 'cannot-create-subdirectory'
        else:
            return False, 'subdirectory-test-path-exists'

        try:
            os.rmdir(subdirectory)
        except (IOError, OSError) as e:
            return False, 'cannot-delete-subdirectory'

        # test create and read
        test_create_path = os.path.join(path, "test_create.octolapse.tmp")
        try:
            with open(test_create_path, 'w+'):
                os.utime(path, None)
        except (IOError, OSError):
            False, 'cannot-write-file'

        # test delete
        try:
            utility.remove(test_create_path)
        except (IOError, OSError):
            False, 'cannot-delete-file'

        return True, None


class ProfileOptions(StaticSettings):
    def __init__(self):
        self.printer = PrinterProfile.get_options()
        self.stabilization = StabilizationProfile.get_options()
        self.trigger = TriggerProfile.get_options()
        self.rendering = RenderingProfile.get_options()
        self.camera = CameraProfile.get_options()
        self.logging = LoggingProfile.get_options()

    def update_server_options(self, available_profiles):
        if not available_profiles:
            return
        # Printer Profile Update
        self.printer["server_profiles"] = available_profiles.get("printer", None)
        self.stabilization["server_profiles"] = available_profiles.get("stabilization", None)
        self.trigger["server_profiles"] = available_profiles.get("trigger", None)
        self.rendering["server_profiles"] = available_profiles.get("rendering", None)
        self.camera["server_profiles"] = available_profiles.get("camera", None)
        self.logging["server_profiles"] = available_profiles.get("logging", None)


class ProfileDefaults(StaticSettings):
    def __init__(self, plugin_version, git_version):
        self.printer = PrinterProfile("Default Printer")
        self.stabilization = StabilizationProfile("Default Stabilization")
        self.trigger = TriggerProfile("Default Trigger")
        self.rendering = RenderingProfile("Default Rendering")
        self.camera = CameraProfile("Default Camera")
        self.logging = LoggingProfile("Default Logging")
        self.main_settings = MainSettings(plugin_version, git_version)


class Profiles(Settings):
    def __init__(self, plugin_version, git_version):
        self.options = ProfileOptions()
        # create default profiles
        self.defaults = ProfileDefaults(plugin_version, git_version)

        # printers is initially empty - user must select a printer
        self.printers = {}
        self.current_printer_profile_guid = None

        self.current_stabilization_profile_guid = self.defaults.stabilization.guid
        self.stabilizations = {self.defaults.stabilization.guid: self.defaults.stabilization}

        self.current_trigger_profile_guid = self.defaults.trigger.guid
        self.triggers = {self.defaults.trigger.guid: self.defaults.trigger}

        self.current_rendering_profile_guid = self.defaults.rendering.guid
        self.renderings = {self.defaults.rendering.guid: self.defaults.rendering}

        # there is no current camera profile guid.
        self.current_camera_profile_guid = self.defaults.camera.guid
        self.cameras = {self.defaults.camera.guid: self.defaults.camera}

        self.current_logging_profile_guid = self.defaults.logging.guid
        self.logging = {self.defaults.logging.guid: self.defaults.logging}

    def get_profiles_dict(self):
        profiles_dict = {
            'current_printer_profile_guid': self.current_printer_profile_guid,
            'current_stabilization_profile_guid': self.current_stabilization_profile_guid,
            'current_trigger_profile_guid': self.current_trigger_profile_guid,
            'current_rendering_profile_guid': self.current_rendering_profile_guid,
            'current_camera_profile_guid': self.current_camera_profile_guid,
            'current_logging_profile_guid': self.current_logging_profile_guid,
            'printers': [],
            'stabilizations': [],
            'triggers': [],
            'renderings': [],
            'cameras': [],
            'logging': []
        }

        for key, printer in self.printers.items():
            profiles_dict["printers"].append({
                "name": printer.name,
                "guid": printer.guid,
                "description": printer.description,
                "has_been_saved_by_user": printer.has_been_saved_by_user,
                "slicer_type": printer.slicer_type
            })

        for key, stabilization in self.stabilizations.items():
            profiles_dict["stabilizations"].append({
                "name": stabilization.name,
                "guid": stabilization.guid,
                "description": stabilization.description,
                "wait_for_moves_to_finish": stabilization.wait_for_moves_to_finish
            })

        for key, trigger in self.triggers.items():
            profiles_dict["triggers"].append({
                "name": trigger.name,
                "guid": trigger.guid,
                "description": trigger.description,
                "trigger_type": trigger.trigger_type
            })

        for key, rendering in self.renderings.items():
            profiles_dict["renderings"].append({
                "name": rendering.name,
                "guid": rendering.guid,
                "description": rendering.description,
            })

        for key, camera in self.cameras.items():
            profiles_dict["cameras"].append({
                "name": camera.name,
                "guid": camera.guid,
                "description": camera.description,
                "enabled": camera.enabled,
                "enable_custom_image_preferences": camera.enable_custom_image_preferences
            })

        for key, loggingProfile in self.logging.items():
            profiles_dict["logging"].append({
                "name": loggingProfile.name,
                "guid": loggingProfile.guid,
                "description": loggingProfile.description
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

    def current_trigger(self):
        if self.current_trigger_profile_guid in self.triggers:
            return self.triggers[self.current_trigger_profile_guid]
        return self.defaults.trigger

    def current_rendering(self):
        if self.current_rendering_profile_guid in self.renderings:
            return self.renderings[self.current_rendering_profile_guid]
        return self.defaults.rendering

    def current_camera_profile(self):
        if self.current_camera_profile_guid in self.cameras:
            return self.cameras[self.current_camera_profile_guid]
        return self.defaults.camera

    def current_logging_profile(self):
        if self.current_logging_profile_guid in self.logging:
            return self.logging[self.current_logging_profile_guid]
        return self.defaults.logging

    def active_cameras(self):
        _active_cameras = []
        for key in self.cameras:
            _current_camera = self.cameras[key]
            if _current_camera.enabled:
                _active_cameras.append(_current_camera)
        return _active_cameras

    def after_startup_cameras(self):
        _startup_cameras = []
        for key in self.cameras:
            _current_camera = self.cameras[key]
            is_startup_camera = (
                (_current_camera.enabled or _current_camera.apply_settings_when_disabled) and
                _current_camera.camera_type in [CameraProfile.camera_type_webcam] and
                _current_camera.apply_settings_at_startup
            )
            if is_startup_camera:
                _startup_cameras.append(_current_camera)
        return _startup_cameras

    def before_print_start_webcameras(self):
        _startup_cameras = []
        for key in self.cameras:
            _current_camera = self.cameras[key]
            if not _current_camera.camera_type == CameraProfile.camera_type_webcam:
                continue
            if not _current_camera.enabled or _current_camera.apply_settings_when_disabled:
                continue
            if not _current_camera.apply_settings_at_startup:
                continue

            _startup_cameras.append(_current_camera)

        return _startup_cameras

    def get_profile(self, profile_type, guid):

        profile_type = profile_type.lower()

        if profile_type == "printer":
            profile = self.printers[guid]
        elif profile_type == "stabilization":
            profile = self.stabilizations[guid]
        elif profile_type == "trigger":
            profile = self.triggers[guid]
        elif profile_type == "rendering":
            profile = self.renderings[guid]
        elif profile_type == "camera":
            profile = self.cameras[guid]
        elif profile_type == "logging":
            profile = self.logging[guid]
        else:
            raise ValueError('An unknown profile type {} was received.'.format(profile_type))
        return profile

    def import_profile(self, profile_type, profile_json, update_existing=False):
        logger.info("Importing a profile.")
        profile_type = profile_type.lower()
        # Create the profile by type
        if profile_type == "printer":
            new_profile = PrinterProfile.create_from(profile_json)
            existing_profiles = self.printers
        elif profile_type == "stabilization":
            new_profile = StabilizationProfile.create_from(profile_json)
            existing_profiles = self.stabilizations
        elif profile_type == "trigger":
            new_profile = TriggerProfile.create_from(profile_json)
            existing_profiles = self.triggers
        elif profile_type == "rendering":
            new_profile = RenderingProfile.create_from(profile_json)
            existing_profiles = self.renderings
        elif profile_type == "camera":
            new_profile = CameraProfile.create_from(profile_json)
            existing_profiles = self.cameras
        elif profile_type == "logging":
            new_profile = LoggingProfile.create_from(profile_json)
            existing_profiles = self.logging
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

        profile_type = profile_type.lower()
        if profile_type == "printer":
            new_profile = PrinterProfile.create_from(profile)
            if new_profile.slicer_type != 'automatic':
                new_profile.gcode_generation_settings = (
                    new_profile.get_current_slicer_settings().get_gcode_generation_settings(
                        slicer_type=new_profile.slicer_type
                    )
                )
            self.printers[guid] = new_profile
            if len(self.printers) == 1 or self.current_printer_profile_guid not in self.printers:
                self.current_printer_profile_guid = new_profile.guid
        elif profile_type == "stabilization":
            new_profile = StabilizationProfile.create_from(profile)
            self.stabilizations[guid] = new_profile
            if len(self.stabilizations) == 1 or self.current_stabilization_profile_guid not in self.stabilizations:
                self.current_stabilization_profile_guid = new_profile.guid
        elif profile_type == "trigger":
            new_profile = TriggerProfile.create_from(profile)
            self.triggers[guid] = new_profile
            if len(self.triggers) == 1 or self.current_trigger_profile_guid not in self.triggers:
                self.current_trigger_profile_guid = new_profile.guid
        elif profile_type == "rendering":
            new_profile = RenderingProfile.create_from(profile)
            self.renderings[guid] = new_profile
            if len(self.renderings) == 1 or self.current_rendering_profile_guid not in self.renderings:
                self.current_rendering_profile_guid = new_profile.guid
        elif profile_type == "camera":
            new_profile = CameraProfile.create_from(profile)
            self.cameras[guid] = new_profile
            if len(self.cameras) == 1 or self.current_camera_profile_guid not in self.cameras:
                self.current_camera_profile_guid = new_profile.guid
        elif profile_type == "logging":
            new_profile = LoggingProfile.create_from(profile)
            self.logging[guid] = new_profile
            if len(self.logging) == 1 or self.current_logging_profile_guid not in self.logging:
                self.current_logging_profile_guid = new_profile.guid
        else:
            raise ValueError('An unknown profile type {} was received.'.format(profile_type))
        return new_profile

    def remove_profile(self, profile_type, guid):

        profile_type = profile_type.lower()
        if profile_type == "printer":
            if self.current_printer_profile_guid == guid:
                return False
            del self.printers[guid]
        elif profile_type == "stabilization":
            if self.current_stabilization_profile_guid == guid:
                return False
            del self.stabilizations[guid]
        elif profile_type == "trigger":
            if self.current_trigger_profile_guid == guid:
                return False
            del self.triggers[guid]
        elif profile_type == "rendering":
            if self.current_rendering_profile_guid == guid:
                return False
            del self.renderings[guid]
        elif profile_type == "camera":
            del self.cameras[guid]
        elif profile_type == "logging":
            if self.current_logging_profile_guid == guid:
                return False
            del self.logging[guid]
        else:
            raise ValueError('An unknown profile type {} was received.'.format(profile_type)(profile_type))

        return True

    def set_current_profile(self, profile_type, guid):
        profile_type = profile_type.lower()
        if profile_type == "printer":
            if guid == "":
                guid = None
            self.current_printer_profile_guid = guid
        elif profile_type == "stabilization":
            self.current_stabilization_profile_guid = guid
        elif profile_type == "trigger":
            self.current_trigger_profile_guid = guid
        elif profile_type == "rendering":
            self.current_rendering_profile_guid = guid
        elif profile_type == "camera":
            self.current_camera_profile_guid = guid
        elif profile_type == "logging":
            self.current_logging_profile_guid = guid
        else:
            raise ValueError('An unknown profile type {} was received.'.format(profile_type))

    def update(self, iterable, **kwargs):
        item_to_iterate = iterable
        if not isinstance(iterable, Iterable):
            item_to_iterate = iterable.__dict__

        for key, value in item_to_iterate.items():
            class_item = getattr(self, key, '{octolapse_no_property_found}')
            # Remove python 2 support
            # if not (isinstance(class_item, six.string_types) and class_item == '{octolapse_no_property_found}'):
            if not (isinstance(class_item, str) and class_item == '{octolapse_no_property_found}'):
                profiles_found = True

                if key == 'printers':
                    profiles = self.printers
                    create_from = PrinterProfile.create_from
                elif key == 'stabilizations':
                    profiles = self.stabilizations
                    create_from = StabilizationProfile.create_from
                elif key == 'triggers':
                    profiles = self.triggers
                    create_from = TriggerProfile.create_from
                elif key == 'renderings':
                    profiles = self.renderings
                    create_from = RenderingProfile.create_from
                elif key == 'cameras':
                    profiles = self.cameras
                    create_from = CameraProfile.create_from
                elif key == 'logging':
                    profiles = self.logging
                    create_from = LoggingProfile.create_from
                else:
                    profiles_found = False

                if profiles_found:
                    profiles.clear()
                    for profile_key, profile_value in value.items():
                        profile = create_from(profile_value)
                        # ensure the guid key matches the profile guid
                        profile.guid = profile_key
                        profiles[profile_key] = profile
                elif isinstance(class_item, Settings):
                    class_item.update(value)
                elif isinstance(class_item, StaticSettings):
                    # don't update any static settings, those come from the class itself!
                    continue
                else:
                    self.__dict__[key] = self.try_convert_value(class_item, value, key)

    def update_from_server_profile(self, profile_type, current_profile_dict, server_profile_dict):
        profile_type = profile_type.lower()
        if profile_type == "printer":
            # get the current profile
            current_profile = PrinterProfile.create_from(current_profile_dict)
            new_profile = PrinterProfile.update_from_server_profile(current_profile, server_profile_dict)
        elif profile_type == "stabilization":
            # get the current profile
            current_profile = StabilizationProfile.create_from(current_profile_dict)
            new_profile = StabilizationProfile.update_from_server_profile(current_profile, server_profile_dict)
        elif profile_type == "trigger":
            # get the current profile
            current_profile = TriggerProfile.create_from(current_profile_dict)
            new_profile = TriggerProfile.update_from_server_profile(current_profile, server_profile_dict)
        elif profile_type == "rendering":
            # get the current profile
            current_profile = RenderingProfile.create_from(current_profile_dict)
            new_profile = RenderingProfile.update_from_server_profile(current_profile, server_profile_dict)
        elif profile_type == "camera":
            # get the current profile
            current_profile = CameraProfile.create_from(current_profile_dict)
            new_profile = CameraProfile.update_from_server_profile(current_profile, server_profile_dict)
        elif profile_type == "logging":
            # get the current profile
            current_profile = LoggingProfile.create_from(current_profile_dict)
            new_profile = LoggingProfile.update_from_server_profile(current_profile, server_profile_dict)
        else:
            raise ValueError('An unknown profile type {} was received.'.format(profile_type))
        return new_profile

    def get_updatable_profiles_dict(self):
        profiles = {
            "printer": [],
            "stabilization": [],
            "trigger": [],
            "rendering": [],
            "camera": [],
            "logging": []
        }
        has_profiles = False
        # Remove python 2 support
        # for key, printer_profile in six.iteritems(self.printers):
        for key, printer_profile in self.printers.items():
            if printer_profile.is_updatable_from_server():
                has_profiles = True
                identifiers = printer_profile.get_server_update_identifiers_dict()
                profiles["printer"].append(identifiers)
        # Remove python 2 support
        # for key, stabilization_profile in six.iteritems(self.stabilizations):
        for key, stabilization_profile in self.stabilizations.items():
            if stabilization_profile.is_updatable_from_server():
                has_profiles = True
                identifiers = stabilization_profile.get_server_update_identifiers_dict()
                profiles["stabilization"].append(identifiers)
        # Remove python 2 support
        # for key, trigger_profile in six.iteritems(self.triggers):
        for key, trigger_profile in self.triggers.items():
            if trigger_profile.is_updatable_from_server():
                has_profiles = True
                identifiers = trigger_profile.get_server_update_identifiers_dict()
                profiles["trigger"].append(identifiers)
        # Remove python 2 support
        # for key, rendering_profile in six.iteritems(self.renderings):
        for key, rendering_profile in self.renderings.items():
            if rendering_profile.is_updatable_from_server():
                has_profiles = True
                identifiers = rendering_profile.get_server_update_identifiers_dict()
                profiles["rendering"].append(identifiers)
        # Remove python 2 support
        # for key, camera_profile in six.iteritems(self.cameras):
        for key, camera_profile in self.cameras.items():
            if camera_profile.is_updatable_from_server():
                has_profiles = True
                identifiers = camera_profile.get_server_update_identifiers_dict()
                profiles["camera"].append(identifiers)
        # Remove python 2 support
        # for key, logging_profile in six.iteritems(self.logging):
        for key, logging_profile in self.logging.items():
            if logging_profile.is_updatable_from_server():
                has_profiles = True
                identifiers = logging_profile.get_server_update_identifiers_dict()
                profiles["logging"].append(identifiers)

        if not has_profiles:
            return None
        return profiles


class GlobalOptions(StaticSettings):
    def __init__(self):
        self.import_options = {
            'settings_import_methods': [
                dict(value='file', name='From a File'),
                dict(value='text', name='From Text'),
            ]
        }


class OctolapseSettings(Settings):

    camera_settings_file_name = "camera_settings.json"

    @staticmethod
    def is_camera_settings_file(file_name):
        return file_name.lower() == OctolapseSettings.camera_settings_file_name

    rendering_settings_file_name = "rendering_settings.json"

    @staticmethod
    def is_rendering_settings_file(file_name):
        return file_name.lower() == OctolapseSettings.rendering_settings_file_name

    DefaultLoggingProfile = None

    def __init__(self, plugin_version="unknown", git_version=None):
        self.main_settings = MainSettings(plugin_version, git_version)
        self.profiles = Profiles(plugin_version, git_version)
        self.global_options = GlobalOptions()
        self.upgrade_info = {
            "was_upgraded": False,
            "previous_version": None
        }

    def save(self, file_path):
        logger.info("Saving settings to: %s.", file_path)
        self.save_as_json(file_path)
        logger.info("Settings saved.")

    def save_rendering_settings(self, data_folder, job_guid):
        for camera in self.profiles.active_cameras():
            snapshot_directory = utility.get_temporary_snapshot_job_camera_path(
                data_folder, job_guid, camera.guid
            )
            # make sure the snapshot path exists
            if not os.path.exists(snapshot_directory):
                try:
                    os.makedirs(snapshot_directory)
                except OSError as e:
                    if e.errno == errno.EEXIST:
                        pass
                    else:
                        raise

            # get the rendering profile json
            rendering_profile_json = self.get_profile_export_json(
                'rendering', self.profiles.current_rendering_profile_guid
            )
            # get the camera profile json
            camera_profile_json = self.get_profile_export_json(
                'camera', camera.guid
            )

            # save the rendering json
            with open(os.path.join(snapshot_directory, OctolapseSettings.rendering_settings_file_name), "w") as settings_file:
                settings_file.write(rendering_profile_json)
            # save the camera json
            with open(os.path.join(snapshot_directory, OctolapseSettings.camera_settings_file_name), "w") as settings_file:
                settings_file.write(camera_profile_json)

    # Todo: raise reasonable exceptions
    @staticmethod
    def load_rendering_settings(plugin_version, data_directory, job_guid, camera_guid):
        """Attempt to load all rendering job settings from the snapshot path"""

        # attempt to load the rendering settings
        # get the settings path
        snapshot_directory = snapshot_directory = utility.get_temporary_snapshot_job_camera_path(
            data_directory, job_guid, camera_guid
        )

        # load the rendering profile
        rendering_settings_path = os.path.join(snapshot_directory, OctolapseSettings.rendering_settings_file_name)
        rendering_profile = None
        if os.path.exists(rendering_settings_path):
            try:
                with open(rendering_settings_path, 'r') as settings_file:
                    settings = json.load(settings_file)
                    if settings["version"] != plugin_version:
                        # TODO:  Attempt to migrate the profile
                        pass
                    if settings["type"] == "rendering" and "profile" in settings:
                        rendering_profile = RenderingProfile.create_from(settings["profile"])
            except (OSError, IOError, ValueError) as e:
                logger.exception(
                    "Could not load rendering settings for the given snapshot job at %s.", rendering_settings_path
                )
        else:
            logger.error(
                "The rendering settings file does not exist for the given snapshot job at %s.", rendering_settings_path
            )

        # load the camera profile
        camera_settings_path = os.path.join(snapshot_directory, OctolapseSettings.camera_settings_file_name)
        camera_profile = None
        if os.path.exists(camera_settings_path):
            try:
                with open(camera_settings_path, 'r') as settings_file:
                    settings = json.load(settings_file)
                    if settings["version"] != plugin_version:
                        # TODO:  Attempt to migrate the profile
                        pass
                    if settings["type"] == "camera" and "profile" in settings:
                        camera_profile = CameraProfile.create_from(settings["profile"])
                        # ensure the guid matches the supplied guid
                        camera_profile.guid = camera_guid
            except (OSError, IOError, ValueError) as e:
                logger.exception(
                    "Could not load camera settings for the given snapshot job at %s.", camera_settings_path
                )
        else:
            logger.error(
                "The camera settings file does not exist for the given snapshot job at %s.", camera_settings_path
            )

        if camera_profile is None:
            camera_profile = CameraProfile()
            camera_profile.name = "UNKNOWN"

        return (
            rendering_profile,
            camera_profile
        )

    @classmethod
    def get_plugin_version_from_file(cls, file_path):
        with open(file_path, 'r') as settings_file:
            try:
                data = json.load(settings_file)
                original_version = migration.get_version(data)
                return original_version
            except Exception:
                return None

    @classmethod
    def load(
        cls,
        file_path,
        plugin_version,
        git_version,
        default_settings_folder,
        default_settings_filename,
        data_directory,
        available_profiles=None
     ):
        # always create a new settings object when loading settings, since
        # it will contain static values that are NOT saved, and load settings might be missing values
        #settings = OctolapseSettings()

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
                    original_version = migration.get_version(data)
                    data = migration.migrate_settings(
                        plugin_version, data, default_settings_folder, data_directory
                    )

                    # if a settings file does not exist, create one ??
                    new_settings = OctolapseSettings.create_from_iterable(
                        plugin_version,
                        data
                    )
                    if original_version != plugin_version:
                        new_settings.upgrade_info = {
                            "was_upgraded": True,
                            "previous_version": original_version
                        }
                    else:
                        new_settings.upgrade_info = {
                            "was_upgraded": False,
                            "previous_version": None
                        }
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
                    data = migration.migrate_settings(
                        plugin_version, data, default_settings_folder, data_directory
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

        # update our server profile options if they were supplied
        if available_profiles:
            # update the profile options within the octolapse settings
            new_settings.profiles.options.update_server_options(available_profiles)

        # set the current and git versions (always use the passed in values)
        new_settings.main_settings.git_version = git_version
        new_settings.main_settings.version = plugin_version
        # set the settings version (always use NumberedVersion.CurrentSettingsVersion)
        new_settings.main_settings.settings_version = NumberedVersion.CurrentSettingsVersion

        return new_settings, load_defualt_settings

    @classmethod
    def get_settings_version_from_dict(cls, settings):
        if "type" in settings:
            return settings.get("settings_version", "unknown")
        main_settings = settings.get("main_settings", {})
        return main_settings.get("settings_version", "unknown")

    def get_profile_export_json(self, profile_type, guid):
        profile = self.profiles.get_profile(profile_type, guid)
        export_dict = {
            'version': self.main_settings.version,
            'settings_version': NumberedVersion.CurrentSettingsVersion,
            'type': profile_type,
            'profile': profile
        }
        return json.dumps(export_dict, cls=SettingsJsonEncoder)

    class IncorrectSettingsVersionException(Exception):
        pass

    def import_settings_from_file(
        self,
        settings_path,
        plugin_version,
        git_version,
        default_settings_folder,
        data_directory,
        available_server_profiles,
        update_existing=False
    ):
        with open(settings_path, mode='r') as settings_file:
            settings_text = settings_file.read()
        return self.import_settings_from_text(
            settings_text, plugin_version, git_version, default_settings_folder, data_directory,
            available_server_profiles, update_existing=update_existing
        )

    def import_settings_from_text(
        self,
        settings_text,
        plugin_version,
        git_version,
        default_settings_folder,
        data_directory,
        available_server_profiles,
        update_existing=False
    ):
        logger.info("Importing python settings object.  Checking settings version.")
        settings = json.loads(settings_text)
        settings_version = OctolapseSettings.get_settings_version_from_dict(settings)
        # see if this is a structured import
        if "type" in settings:
            if settings_version != NumberedVersion.CurrentSettingsVersion:
                raise OctolapseSettings.IncorrectSettingsVersionException(
                    "Cannot import profiles exported from an incompatible version of Octolapse ({0}).  Was expecting settings version: {1} ".format(
                        settings_version, NumberedVersion.CurrentSettingsVersion
                    )
                )
            else:
                self.profiles.import_profile(settings["type"], settings["profile"], update_existing=update_existing)
                settings = self
        else:
            # Make sure the settings version is not greater than the current version
            if settings_version != "unknown" and NumberedVersion(NumberedVersion.CurrentSettingsVersion) < NumberedVersion(settings_version):
                raise OctolapseSettings.IncorrectSettingsVersionException(
                    "Cannot import settings exported from a newer and incompatible version of Octolapse ({0}).  Was expecting settings version: {1} ".format(
                        settings_version, NumberedVersion.CurrentSettingsVersion
                    )
                )
            # this is a regular settings file.  Try to migrate
            migrated_settings = migration.migrate_settings(
                plugin_version, settings, default_settings_folder, data_directory
            )
            new_settings = OctolapseSettings(plugin_version, git_version)
            new_settings.update(migrated_settings)
            settings = new_settings

        settings.profiles.options.update_server_options(available_server_profiles)
        return settings

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


class OctolapseExtruderGcodeSettings(Settings):
    def __init__(self):
        self.retract_before_move = None
        self.retraction_length = None
        self.retraction_speed = None
        self.deretraction_speed = None
        self.lift_when_retracted = None
        self.z_lift_height = None
        self.x_y_travel_speed = None
        self.first_layer_travel_speed = None
        self.z_lift_speed = None


class OctolapseGcodeSettings(Settings):
    def __init__(self):
        # Per Extruder Settings
        self.extruders = []
        # Print Settings
        self.vase_mode = None
        self.layer_height = None

    def get_num_extruders(self):
        return len(self.extruders)

    def to_dict(self):
        extruders_list = []
        for extruder in self.extruders:
            if isinstance(extruder, dict):
                extruders_list.append(extruder)
            else:
                extruders_list.append(extruder.to_dict())
        return {
            "vase_mode": self.vase_mode,
            "layer_height": self.layer_height,
            "extruders": extruders_list,
        }


class SlicerExtruder(Settings):
    def __init__(self):
        pass


class SlicerSettings(Settings):
    SlicerTypeOther = 'other'
    SlicerTypeCura = 'cura'
    SlicerTypeSimplify3D = 'simplify-3d'
    SlicerTypeSlic3rPe = 'slic3r-pe'

    def __init__(self, slicer_type, version):
        self.slicer_type = slicer_type
        self.version = version
        self.extruders = []
    def get_speed_tolerance(self):
        raise NotImplementedError("You must implement get_speed_tolerance")

    def get_gcode_generation_settings(self, slicer_type=None):
        """Returns OctolapseSlicerSettings"""
        raise NotImplementedError("You must implement get_gcode_generation_settings")

    def get_missing_gcode_generation_settings(self, slicer_type=None):
        settings = self.get_gcode_generation_settings(slicer_type=slicer_type)
        assert(isinstance(settings, OctolapseGcodeSettings))
        issue_list = []
        extruder_number = 1
        if len(settings.extruders) == 0:
            issue_list.append("No extruder settings were found in your gcode file.")
        else:
            for extruder in settings.extruders:
                if len(settings.extruders) == 1:
                    extruder_label = ""
                else:
                    extruder_label = "Extruder {0} - ".format(extruder_number)
                    # Per Extruder Settings
                if extruder.retract_before_move is None:
                    issue_list.append("{}Retract Before Move".format(extruder_label))
                if extruder.retraction_length is None:
                    issue_list.append("{}Retraction Length".format(extruder_label))
                if extruder.retraction_speed is None:
                    issue_list.append("{}Retraction Speed".format(extruder_label))
                if extruder.deretraction_speed is None:
                    issue_list.append("{}Deretraction Speed".format(extruder_label))
                if extruder.lift_when_retracted is None:
                    issue_list.append("{}Lift When Retracted".format(extruder_label))
                if extruder.z_lift_height is None:
                    issue_list.append("{}Z Lift Height".format(extruder_label))
                if extruder.x_y_travel_speed is None:
                    issue_list.append("{}X/Y Travel Speed".format(extruder_label))
                if extruder.z_lift_speed is None:
                    issue_list.append("{}Z Travel Speed".format(extruder_label))
                extruder_number += 1
        # Print Settings
        if settings.vase_mode is None:
            issue_list.append("Is Vase Mode")
        return issue_list

    def get_speed_mm_min(self, speed, multiplier=None, speed_name=None):
        """Returns a speed in mm/min for a setting name"""
        raise NotImplementedError("You must implement get_speed_mm_min")

    def update_settings_from_gcode(self, settings_dict, printer_profile):
        raise NotImplementedError("You must implement update_settings_from_gcode")


class CuraExtruder(SlicerExtruder):
    def __init__(self):
        super(CuraExtruder, self).__init__()
        self.version = None
        self.speed_z_hop = None
        self.max_feedrate_z_override = None
        self.retraction_amount = None
        self.retraction_hop = None
        self.retraction_hop_enabled = False
        self.retraction_enable = False
        self.retraction_speed = None
        self.retraction_retract_speed = None
        self.retraction_prime_speed = None
        self.speed_travel = None

    def get_extruder(self, slicer_settings, slicer_type):
        extruder = OctolapseExtruderGcodeSettings()
        extruder.retract_before_move = self.get_retract_before_move()
        extruder.retraction_length = self.get_retraction_amount()
        extruder.retraction_speed = self.get_retraction_retract_speed()
        extruder.deretraction_speed = self.get_retraction_prime_speed()
        extruder.lift_when_retracted = self.get_lift_when_retracted()
        extruder.z_lift_height = self.get_retraction_hop()
        extruder.x_y_travel_speed = self.get_speed_travel()
        extruder.first_layer_travel_speed = self.get_speed_travel()
        extruder.z_lift_speed = self.get_speed_travel_z(slicer_type)
        return extruder

    def get_retract_before_move(self):
        retraction_amount = self.get_retraction_amount()
        return (
            self.retraction_enable and retraction_amount is not None and retraction_amount > 0
        )

    def get_lift_when_retracted(self):
        retraction_hop = self.get_retraction_hop()
        return (
            self.get_retract_before_move() and
            self.retraction_hop_enabled and
            retraction_hop is not None and
            retraction_hop > 0
        )

    def get_retraction_amount(self):
        if self.retraction_amount is None or len("{}".format(self.retraction_amount).strip()) == 0:
            return None
        return float(self.retraction_amount)

    def get_retraction_hop(self):
        if self.retraction_hop is None or len("{}".format(self.retraction_hop).strip()) == 0:
            return None
        return float(self.retraction_hop)

    def get_retraction_retract_speed(self):
        if self.retraction_retract_speed:
            return CuraSettings.get_speed_mm_min(self.retraction_retract_speed)
        return CuraSettings.get_speed_mm_min(self.retraction_speed)

    def get_retraction_prime_speed(self):
        if self.retraction_prime_speed:
            return CuraSettings.get_speed_mm_min(self.retraction_prime_speed)
        return CuraSettings.get_speed_mm_min(self.retraction_speed)

    def get_speed_travel(self):
        return CuraSettings.get_speed_mm_min(self.speed_travel)

    def get_speed_travel_z(self, slicer_type=None):
        if slicer_type == "cura_4_2" or (
            self.version and
            self.speed_z_hop is not None
        ):
            return CuraSettings.get_speed_mm_min(self.speed_z_hop)

        z_max_feedrate = 0
        if self.max_feedrate_z_override:
            z_max_feedrate = CuraSettings.get_speed_mm_min(self.max_feedrate_z_override)
        travel_feedrate = CuraSettings.get_speed_mm_min(self.speed_travel)
        if z_max_feedrate == 0:
            return travel_feedrate
        return min(z_max_feedrate, travel_feedrate)

    def update(self, iterable, **kwargs):
            item_to_iterate = iterable
            if not isinstance(iterable, Iterable):
                item_to_iterate = iterable.__dict__
            for key, value in item_to_iterate.items():
                class_item = getattr(self, key, '{octolapse_no_property_found}')
                # Remove python 2 support
                # if not (isinstance(class_item, six.string_types) and class_item == '{octolapse_no_property_found}'):
                if not (isinstance(class_item, str) and class_item == '{octolapse_no_property_found}'):
                    try:
                        if key in ['retraction_enable', 'retraction_hop_enabled']:
                            self.__dict__[key] = None if value is None else bool(value)
                        elif key == "version":
                            self.__dict__[key] = None if value is None else str(value)
                        else:
                            self.__dict__[key] = None if value is None else float(value)
                    except ValueError as e:
                        logger.exception(
                            "Unable to update the current Cura extruder profile.  Key:{}, Value:{}".format(key, value))
                        continue


class CuraSettings(SlicerSettings):
    ExtruderNumberSearchRegex = r"([\w\W]*)_(\d+)$"

    def __init__(self, version="unknown"):
        super(CuraSettings, self).__init__(SlicerSettings.SlicerTypeCura, version)
        self.axis_speed_display_settings = 'mm-sec'
        self.layer_height = None
        self.smooth_spiralized_contours = False
        self.machine_extruder_count = 1

    def get_extruders(self, slicer_type):
        extruders = []
        for extruder in self.extruders:
            extruders.append(extruder.get_extruder(self, slicer_type))
        return extruders

    def get_speed_tolerance(self):
        return 0.1 / 60.0 / 2.0

    def get_gcode_generation_settings(self, slicer_type="cura"):
        settings = OctolapseGcodeSettings()
        settings.layer_height = self.layer_height
        settings.vase_mode = False
        if self.smooth_spiralized_contours is not None:
            # we might not need to include a check for surface mode
            settings.vase_mode = self.smooth_spiralized_contours
        # Get All Extruder Settings
        settings.extruders = self.get_extruders(slicer_type)
        return settings

    @staticmethod
    def get_speed_mm_min(speed, multiplier=None, speed_name=None):
        if speed is None or len("{}".format(speed).strip()) == 0:
            return None
        # Convert speed to mm/min
        speed = float(speed) * 60.0
        # round to .1
        return utility.round_to(speed, 0.1)

    def update_settings_from_gcode(self, settings_dict, printer_profile):

        # get the version if it's in the settings dict
        version = "unknown"
        if 'version' in settings_dict:
            version = settings_dict["version"]

        # clear out the extruders
        self.extruders = []
        # extract the extruder count if it can be found
        num_extruders = 1
        if 'machine_extruder_count' in settings_dict:
            num_extruders = int(settings_dict["machine_extruder_count"])

        if num_extruders > 8:
            num_extruders = 8

        # add the appropriate number of extruders according to the settings
        for i in range(0, num_extruders):
            new_extruder = CuraExtruder()
            new_extruder.version = version
            self.extruders.append(new_extruder)

        for key, value in settings_dict.items():
            try:
                # first see if this is an extruder setting.  To do that let's look for an underscore then a number
                # at the end of the setting value, remove it

                matches = re.search(CuraSettings.ExtruderNumberSearchRegex, key)
                if matches and len(matches.groups()) == 2:
                    extruder_setting_name = matches.groups()[0]
                    extruder_index = int(matches.groups()[1])
                else:
                    extruder_setting_name = key
                    extruder_index = 0

                if -1 < extruder_index < 8 and extruder_index < num_extruders and extruder_setting_name in [
                    "speed_z_hop",
                    "retraction_amount",
                    "retraction_hop",
                    "retraction_hop_enabled",
                    "retraction_enable",
                    "retraction_speed",
                    "retraction_retract_speed",
                    "retraction_prime_speed",
                    "speed_travel",
                    "max_feedrate_z_override"
                ]:
                    # convert the type as needed
                    if extruder_setting_name in ['retraction_hop_enabled','retraction_enable']:
                        value = None if value is None else bool(value)
                    else:
                        value = None if value is None else float(value)
                    # get the current extruder
                    extruder = self.extruders[extruder_index]
                    # for fun, make sure the setting exists in the extruder class
                    class_item = getattr(extruder, extruder_setting_name, '{octolapse_no_property_found}')
                    # Remove python 2 support
                    if not (
                        # Remove python 2 support
                        # isinstance(class_item, six.string_types) and class_item == '{octolapse_no_property_found}'
                        isinstance(class_item, str) and class_item == '{octolapse_no_property_found}'
                    ):
                        extruder.__dict__[extruder_setting_name] = value
                    continue
                class_item = getattr(self, key, '{octolapse_no_property_found}')
                # Remove python 2 support
                # if not (isinstance(class_item, six.string_types) and class_item == '{octolapse_no_property_found}'):
                if not (isinstance(class_item, str) and class_item == '{octolapse_no_property_found}'):
                    if key == 'version':
                        self.version = value
                    elif isinstance(class_item, Settings):
                        class_item.update(value)
                    else:
                        self.__dict__[key] = self.try_convert_value(class_item, value, key)
            except ValueError:
                logger.exception("An error occurred while updating cura settings from the extracted gcode settings")
                continue

    def update(self, iterable, **kwargs):
        try:
            item_to_iterate = iterable
            if not isinstance(iterable, Iterable):
                item_to_iterate = iterable.__dict__
            for key, value in item_to_iterate.items():
                class_item = getattr(self, key, '{octolapse_no_property_found}')
                # Remove python 2 support
                # if not (isinstance(class_item, six.string_types) and class_item == '{octolapse_no_property_found}'):
                if not (isinstance(class_item, str) and class_item == '{octolapse_no_property_found}'):
                    if key == "extruders":
                        self.extruders = []
                        for extruder in value:
                            new_extruder = CuraExtruder()
                            new_extruder.update(extruder)
                            self.extruders.append(new_extruder)
                    elif isinstance(class_item, Settings):
                        class_item.update(value)
                    elif isinstance(class_item, StaticSettings):
                        # don't update any static settings, those come from the class itself!
                        continue
                    else:
                        self.__dict__[key] = self.try_convert_value(class_item, value, key)
        except Exception as e:
            raise e


class Simplify3dExtruder(SlicerExtruder):
    def __init__(self):
        super(Simplify3dExtruder, self).__init__()
        self.retraction_distance = None
        self.retraction_vertical_lift = None
        self.retraction_speed = None
        self.extruder_use_retract = False

    def get_extruder(self, slicer_settings):
        extruder = OctolapseExtruderGcodeSettings()
        extruder.retraction_length = self.get_retraction_distance()
        extruder.retraction_speed = self.get_retract_speed(slicer_settings)
        extruder.deretraction_speed = self.get_deretract_speed(slicer_settings)
        extruder.x_y_travel_speed = slicer_settings.get_x_y_axis_movement_speed()
        extruder.z_lift_height = self.get_retraction_vertical_lift()
        extruder.z_lift_speed = slicer_settings.get_z_axis_movement_speed()
        extruder.retract_before_move = (
            self.extruder_use_retract and extruder.retraction_length is not None and extruder.retraction_length > 0
        )
        extruder.lift_when_retracted = (
            extruder.retract_before_move and extruder.z_lift_height is not None and extruder.z_lift_height > 0
        )
        return extruder

    def get_retraction_distance(self):
        return None if self.retraction_distance is None else float(self.retraction_distance)

    def get_retraction_vertical_lift(self):
        return None if self.retraction_vertical_lift is None else float(self.retraction_vertical_lift)

    def get_retract_speed(self, slicer_settings):
        return slicer_settings.get_speed_mm_min(self.retraction_speed)

    def get_deretract_speed(self, slicer_settings):
        return self.get_retract_speed(slicer_settings)

    def update(self, iterable, **kwargs):
        item_to_iterate = iterable
        if not isinstance(iterable, Iterable):
            item_to_iterate = iterable.__dict__
        for key, value in item_to_iterate.items():
            class_item = getattr(self, key, '{octolapse_no_property_found}')
            # Remove python 2 support
            # if not (isinstance(class_item, six.string_types) and class_item == '{octolapse_no_property_found}'):
            if not (isinstance(class_item, str) and class_item == '{octolapse_no_property_found}'):
                try:
                    if key in ['extruder_use_retract']:
                        self.__dict__[key] = None if value is None else bool(value)
                    else:
                        self.__dict__[key] = None if value is None else float(value)
                except ValueError as e:
                    logger.exception(
                        "Unable to update the current Cura extruder profile.  Key:{}, Value:{}".format(key, value))
                    continue


class Simplify3dSettings(SlicerSettings):

    def __init__(self, version="unknown"):
        super(Simplify3dSettings, self).__init__(SlicerSettings.SlicerTypeSimplify3D, version)
        self.x_y_axis_movement_speed = None
        self.z_axis_movement_speed = None
        self.spiral_vase_mode = False
        self.layer_height = None
        # simplify has a fixed speed tolerance
        self.axis_speed_display_settings = 'mm-min'

    def get_extruders(self):
        extruders = []
        for extruder in self.extruders:
            extruders.append(extruder.get_extruder(self))
        return extruders

    def get_speed_tolerance(self):
        return 1

    def get_gcode_generation_settings(self, slicer_type=None):
        """Returns OctolapseSlicerSettings"""
        settings = OctolapseGcodeSettings()
        settings.vase_mode = self.spiral_vase_mode
        settings.layer_height = self.layer_height
        settings.extruders = self.get_extruders()
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

    def get_x_y_axis_movement_speed(self):
        return self.get_speed_mm_min(self.x_y_axis_movement_speed)

    def get_z_axis_movement_speed(self):
        return self.get_speed_mm_min(self.z_axis_movement_speed)

    def update_settings_from_gcode(self, settings_dict, printer_profile):
        # per print settings extraction functions
        def _x_y_axis_movement_speed():
            return settings_dict["rapid_xy_speed"]

        def _z_axis_movement_speed():
            return settings_dict["rapid_z_speed"]

        # update non-extruder settings
        self.x_y_axis_movement_speed = _x_y_axis_movement_speed()
        self.z_axis_movement_speed = _z_axis_movement_speed()
        self.spiral_vase_mode = settings_dict['spiral_vase_mode']
        self.layer_height = settings_dict['layer_height']
        # clear existing extruders
        self.extruders = []
        # get the toolhead numbers, which is a list of ints that determine the T gcode number for each extruder
        # Note that toolhead_numbers is a 0 based index
        toolhead_numbers = settings_dict["extruder_tool_number"]
        # Simplify 3D has a very odd method of defining extruders.  You can define any number of
        # extruders and assign them to a tool number (0 based).  Multiple extruders can use the same tool number.
        # Due to this there are some limitations to how Octolaspe can implement multi-extruder setups in
        # simplify.
        #
        # First, we need to check for duplicate indexes.  If we find any, throw an error
        duplicate_extruder_toolhead_numbers = set([x for x in toolhead_numbers if toolhead_numbers.count(x) > 1])
        if len(duplicate_extruder_toolhead_numbers) > 0:
            raise OctolapseException(
                ["settings","slicer","simplify3d","duplicate_toolhead_numbers"],
                toolhead_numbers = ','.join([str(x) for x in duplicate_extruder_toolhead_numbers])
            )
        #

        # get the number of extruders
        num_extruders = len(toolhead_numbers)
        # make sure we have enough extruders
        if num_extruders != 1 and num_extruders != printer_profile.num_extruders:
            raise OctolapseException(
                ["settings", "slicer", "simplify3d", "extruder_count_mismatch"],
                configured_extruder_count=printer_profile.num_extruders, detected_extruder_count=num_extruders
            )
        max_extruder_count = 8
        if num_extruders > max_extruder_count:
            raise OctolapseException(
                ["settings", "slicer", "simplify3d", "max_extruder_count_exceeded"],
                simplify_extruder_count=num_extruders, max_extruder_count=max_extruder_count
            )

        # ensure that the max(toolhead_number) is correct given the number of extruders and zero_based_extruder
        zero_based_extruder = (
            (printer_profile.num_extruders > 1 and printer_profile.zero_based_extruder) or
            (printer_profile.num_extruders == 1 and max(toolhead_numbers) == 0)
        )

        expected_max_toolhead_number = num_extruders - 1 if zero_based_extruder else num_extruders
        max_toolhead_number = max(toolhead_numbers)
        if num_extruders > 1 and expected_max_toolhead_number != max_toolhead_number:
            raise OctolapseException(
                ["settings", "slicer", "simplify3d", "unexpected_max_toolhead_number"],
                expected_max_toolhead_number=expected_max_toolhead_number, max_toolhead_number=max_toolhead_number
            )

        # create num_extruders extruders for this profile
        for i in range(0, num_extruders):
            extruder = Simplify3dExtruder()
            self.extruders.append(extruder)

        # extract all per-extruder settings for each toolhead
        for toolhead_index in range(num_extruders):
            # get the extruder for the toolhead
            extruder = self.extruders[toolhead_index]
            # per defined extruder settings extraction functions

            def _retraction_distance(index):
                return settings_dict["extruder_retraction_distance"][index]

            def _retraction_vertical_lift(index):
                return settings_dict["extruder_retraction_z_lift"][index]

            def _retraction_speed(index):
                return settings_dict["extruder_retraction_speed"][index]

            def _extruder_use_retract(index):
                return settings_dict["extruder_use_retract"][index]

            # set all extruder based settings
            extruder.retraction_distance = _retraction_distance(toolhead_index)
            extruder.retraction_vertical_lift = _retraction_vertical_lift(toolhead_index)
            extruder.retraction_speed = _retraction_speed(toolhead_index)
            extruder.extruder_use_retract = _extruder_use_retract(toolhead_index)

    def update(self, iterable, **kwargs):
        try:
            item_to_iterate = iterable
            if not isinstance(iterable, Iterable):
                item_to_iterate = iterable.__dict__
            for key, value in item_to_iterate.items():
                class_item = getattr(self, key, '{octolapse_no_property_found}')
                # Remove python 2 support
                # if not (isinstance(class_item, six.string_types) and class_item == '{octolapse_no_property_found}'):
                if not (isinstance(class_item, str) and class_item == '{octolapse_no_property_found}'):
                    if key == "extruders":
                        self.extruders = []
                        for extruder in value:
                            new_extruder = Simplify3dExtruder()
                            new_extruder.update(extruder)
                            self.extruders.append(new_extruder)
                    elif isinstance(class_item, Settings):
                        class_item.update(value)
                    elif isinstance(class_item, StaticSettings):
                        # don't update any static settings, those come from the class itself!
                        continue
                    else:
                        self.__dict__[key] = self.try_convert_value(class_item, value, key)
        except Exception as e:
            raise e


class Slic3rPeExtruder(SlicerExtruder):
    def __init__(self):
        super(Slic3rPeExtruder, self).__init__()
        self.retract_length = None
        self.retract_lift = None
        self.retract_speed = None
        self.deretract_speed = None

    def get_retract_length(self):
        if self.retract_length is None:
            return None
        else:
            return utility.round_to(float(self.retract_length), 0.00001)

    def get_retract_before_move(self):
        retract_length = self.get_retract_length()
        if (
            retract_length is not None and
            retract_length > 0
        ):
            return True
        else:
            return False

    def get_retract_lift_height(self):
        if self.retract_lift is None:
            return None
        return utility.round_to(float(self.retract_lift), 0.001)

    def get_lift_when_retracted(self):
        get_retract_before_move = self.get_retract_before_move()
        retract_lift_height = self.get_retract_lift_height()
        if (
            get_retract_before_move
            and retract_lift_height is not None
            and retract_lift_height > 0
        ):
            return True
        return False

    def get_retract_speed(self):

        if self.retract_speed is None or len("{}".format(self.retract_speed).strip()) == 0:
            return None
        else:
            return Slic3rPeSettings.get_speed_from_setting(self.retract_speed, round_to=1)

    def get_deretract_speed(self):
        retract_speed = self.get_retract_speed()
        deretract_speed = self.deretract_speed
        if deretract_speed is None or len("{}".format(deretract_speed).strip()) == 0:
            return None
        deretract_speed = float(deretract_speed)
        if deretract_speed == 0:
            return retract_speed
        else:
            return Slic3rPeSettings.get_speed_from_setting(deretract_speed, round_to=1)

    def get_extruder(self, slicer_settings):
        extruder = OctolapseExtruderGcodeSettings()
        extruder.retract_before_move = self.get_retract_before_move()
        extruder.retraction_length = self.get_retract_length()
        extruder.retraction_speed = self.get_retract_speed()
        extruder.deretraction_speed = self.get_deretract_speed()
        extruder.lift_when_retracted = self.get_lift_when_retracted()
        extruder.z_lift_height = self.get_retract_lift_height()
        extruder.x_y_travel_speed = slicer_settings.get_travel_speed()
        extruder.first_layer_travel_speed = slicer_settings.get_travel_speed()
        extruder.z_lift_speed = slicer_settings.get_travel_speed()
        return extruder

    def update(self, iterable, **kwargs):
            item_to_iterate = iterable
            if not isinstance(iterable, Iterable):
                item_to_iterate = iterable.__dict__
            for key, value in item_to_iterate.items():
                class_item = getattr(self, key, '{octolapse_no_property_found}')
                # Remove python 2 support
                # if not (isinstance(class_item, six.string_types) and class_item == '{octolapse_no_property_found}'):
                if not (isinstance(class_item, str) and class_item == '{octolapse_no_property_found}'):
                    try:
                        self.__dict__[key] = None if value is None else float(value)
                    except ValueError as e:
                        logger.exception(
                            "Unable to update the current Slic3r extruder profile.  Key:{}, Value:{}".format(key, value))
                        continue


class Slic3rPeSettings(SlicerSettings):
    def __init__(self, version="unknown"):
        super(Slic3rPeSettings, self).__init__(SlicerSettings.SlicerTypeSlic3rPe, version)
        self.axis_speed_display_units = 'mm-sec'
        self.layer_height = None
        self.spiral_vase = False
        self.travel_speed = None

    def get_extruders(self):
        extruders = []
        for extruder in self.extruders:
            extruders.append(extruder.get_extruder(self))
        return extruders

    def get_speed_mm_min(self, speed, multiplier=None, setting_name=None):
        if speed is None:
            return None
        speed = float(speed)
        if self.axis_speed_display_units == "mm-sec":
            speed = speed * 60.0
        return speed

    def get_gcode_generation_settings(self, slicer_type=None):
        settings = OctolapseGcodeSettings()
        # get print settings
        settings.layer_height = self.layer_height
        settings.vase_mode = self.spiral_vase if self.spiral_vase is not None else False
        # Get All Extruder Settings
        settings.extruders = self.get_extruders()
        return settings

    def get_z_travel_speed(self):
        return self.get_travel_speed()

    @staticmethod
    def parse_percent(parse_string):
        try:
            if parse_string is None:
                return None
            # Remove python 2 support
            # if isinstance(parse_string, six.string_types):
            if isinstance(parse_string, str):
                percent_index = "{}".format(parse_string).strip().find('%')
                if percent_index < 1:
                    return None
                try:
                    percent = float("{}".format(parse_string).encode(u'utf-8').decode().translate({ord(c):None for c in '%'})) / 100.0
                    return percent
                except ValueError:
                    return None
            return None
        except Exception as e:
            raise e

    @staticmethod
    def get_speed_from_setting(
        speed_setting, round_to=0.01
    ):
        if speed_setting is None or len("{}".format(speed_setting).strip()) == 0:
            return None

        return utility.round_to(float(speed_setting) * 60.0, round_to)

    def get_travel_speed(self):
        return self.get_speed_from_setting(
            self.travel_speed
        )

    def update_settings_from_gcode(self, settings_dict, printer_profile):
        try:
            # clear out the extruders
            self.extruders = []
            for key, value in settings_dict.items():
                # first see if this is an extruder setting
                if isinstance(value, list) and key in [
                    "retract_length",
                    "retract_lift",
                    "retract_speed",
                    "deretract_speed"
                ]:
                    # expand the extruders list if necessary
                    while len(value) > len(self.extruders):
                        self.extruders.append(Slic3rPeExtruder())
                    extruder_index = 0
                    for extruder_value in value:
                        extruder = self.extruders[extruder_index]
                        class_item = getattr(extruder, key, '{octolapse_no_property_found}')
                        if not (
                            # Remove python 2 support
                            # isinstance(class_item, six.string_types) and class_item == '{octolapse_no_property_found}'
                            isinstance(class_item, str) and class_item == '{octolapse_no_property_found}'
                        ):
                            # All of the extruder values are floats
                            extruder.__dict__[key] = float(extruder_value)
                        extruder_index += 1
                    continue
                class_item = getattr(self, key, '{octolapse_no_property_found}')
                # Remove python 2 support
                #if not (isinstance(class_item, six.string_types) and class_item == '{octolapse_no_property_found}'):
                if not (isinstance(class_item, str) and class_item == '{octolapse_no_property_found}'):
                    if key == 'version':
                        self.version = value["version"]
                    elif isinstance(class_item, Settings):
                        class_item.update(value)
                    else:
                        self.__dict__[key] = self.try_convert_value(class_item, value, key)
        except Exception as e:
            raise e

    @classmethod
    def try_convert_value(cls, destination, value, key):
        # Remove python 2 support
        # if value is None or (isinstance(value, six.string_types) and value == 'None'):
        if value is None or (isinstance(value, str) and value == 'None'):
            return None

        return super(Slic3rPeSettings, cls).try_convert_value(destination, value, key)

    def update(self, iterable, **kwargs):
        try:
            item_to_iterate = iterable
            if not isinstance(iterable, Iterable):
                item_to_iterate = iterable.__dict__
            for key, value in item_to_iterate.items():
                class_item = getattr(self, key, '{octolapse_no_property_found}')
                # Remove python 2 support
                #if not (isinstance(class_item, six.string_types) and class_item == '{octolapse_no_property_found}'):
                if not (isinstance(class_item, str) and class_item == '{octolapse_no_property_found}'):
                    if key == "extruders":
                        self.extruders = []
                        for extruder in value:
                            new_extruder = Slic3rPeExtruder()
                            new_extruder.update(extruder)
                            self.extruders.append(new_extruder)
                    elif isinstance(class_item, Settings):
                        class_item.update(value)
                    elif isinstance(class_item, StaticSettings):
                        # don't update any static settings, those come from the class itself!
                        continue
                    else:
                        self.__dict__[key] = self.try_convert_value(class_item, value, key)
        except Exception as e:
            raise e


class OtherSlicerExtruder(SlicerExtruder):
    def __init__(self):
        super(OtherSlicerExtruder, self).__init__()
        self.retract_length = None
        self.z_hop = None
        self.retract_speed = None
        self.deretract_speed = None
        self.lift_when_retracted = False
        self.retract_before_move = False
        self.travel_speed = None
        self.z_travel_speed = None

    def get_travel_speed(self, slicer_settings):
        return slicer_settings.get_speed_mm_min(self.travel_speed)

    def get_z_travel_speed(self, slicer_settings):
        return slicer_settings.get_speed_mm_min(self.z_travel_speed)

    def get_retract_speed(self, slicer_settings):
        return slicer_settings.get_speed_mm_min(self.retract_speed)

    def get_deretract_speed(self, slicer_settings):
        return slicer_settings.get_speed_mm_min(self.deretract_speed)

    def get_extruder(self, slicer_settings):
        extruder = OctolapseExtruderGcodeSettings()
        extruder.retract_before_move = self.retract_before_move
        extruder.retraction_length = self.retract_length
        extruder.retraction_speed = self.get_retract_speed(slicer_settings)
        extruder.deretraction_speed = self.get_deretract_speed(slicer_settings)
        extruder.lift_when_retracted = self.lift_when_retracted
        extruder.z_lift_height = self.z_hop
        extruder.x_y_travel_speed = self.get_travel_speed(slicer_settings)
        extruder.first_layer_travel_speed = self.get_travel_speed(slicer_settings)
        extruder.z_lift_speed = self.get_z_travel_speed(slicer_settings)
        return extruder

    def update(self, iterable, **kwargs):
            item_to_iterate = iterable
            if not isinstance(iterable, Iterable):
                item_to_iterate = iterable.__dict__
            for key, value in item_to_iterate.items():
                class_item = getattr(self, key, '{octolapse_no_property_found}')
                # Remove python 2 support
                # if not (isinstance(class_item, six.string_types) and class_item == '{octolapse_no_property_found}'):
                if not (isinstance(class_item, str) and class_item == '{octolapse_no_property_found}'):
                    try:
                        if key in ['retract_before_move','lift_when_retracted']:
                            self.__dict__[key] = None if value is None else bool(value)
                        else:
                            self.__dict__[key] = None if value is None else float(value)
                    except ValueError as e:
                        logger.exception(
                            "Unable to update the current Slic3r extruder profile.  Key:{}, Value:{}".format(key, value))
                        continue


class OtherSlicerSettings(SlicerSettings):
    def __init__(self, version="unknown"):
        super(OtherSlicerSettings, self).__init__(SlicerSettings.SlicerTypeOther, version)
        self.speed_tolerance = 1
        self.axis_speed_display_units = 'mm-min'
        self.vase_mode = False
        self.layer_height = None

    def update_settings_from_gcode(self, settings_dict, printer_profile):
        raise Exception("Cannot update 'Other Slicer' from gcode file!  Please select another slicer type to use this "
                        "function.")

    def get_extruders(self):
        extruders = []
        for extruder in self.extruders:
            extruders.append(extruder.get_extruder(self))
        return extruders

    def get_speed_tolerance(self):
        if self.axis_speed_display_units == 'mm-sec':
            return self.speed_tolerance * 60.0
        return self.speed_tolerance

    def get_gcode_generation_settings(self, slicer_type=None):
        """Returns OctolapseSlicerSettings"""
        settings = OctolapseGcodeSettings()
        settings.layer_height = self.layer_height
        settings.vase_mode = self.vase_mode
        settings.extruders = self.get_extruders()
        return settings

    def get_speed_mm_min(self, speed, multiplier=None, setting_name=None):
        if speed is None:
            return None
        speed = float(speed)
        if self.axis_speed_display_units == "mm-sec":
            speed = speed * 60.0
        # Todo - Look at this, we need to round prob.
        return speed

    def update(self, iterable, **kwargs):
        try:
            item_to_iterate = iterable
            if not isinstance(iterable, Iterable):
                item_to_iterate = iterable.__dict__
            for key, value in item_to_iterate.items():
                class_item = getattr(self, key, '{octolapse_no_property_found}')
                # Remove python 2 support
                # if not (isinstance(class_item, six.string_types) and class_item == '{octolapse_no_property_found}'):
                if not (isinstance(class_item, str) and class_item == '{octolapse_no_property_found}'):
                    if key == "extruders":
                        self.extruders = []
                        for extruder in value:
                            new_extruder = OtherSlicerExtruder()
                            new_extruder.update(extruder)
                            self.extruders.append(new_extruder)
                    elif isinstance(class_item, Settings):
                        class_item.update(value)
                    elif isinstance(class_item, StaticSettings):
                        # don't update any static settings, those come from the class itself!
                        continue
                    else:
                        self.__dict__[key] = self.try_convert_value(class_item, value, key)
        except Exception as e:
            raise e
