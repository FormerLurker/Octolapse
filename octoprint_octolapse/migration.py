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
from octoprint_octolapse_setuptools import NumberedVersion

import json
import sys
import os
# remove unused using
# import six
import copy
import shutil
# create the module level logger
from octoprint_octolapse.log import LoggingConfigurator
logging_configurator = LoggingConfigurator()
logger = logging_configurator.get_logger(__name__)


def get_version(settings_dict):
    version = 'unknown'
    if 'version' in settings_dict:
        version = settings_dict["version"]
    elif 'main_settings' in settings_dict and 'version' in settings_dict["main_settings"]:
        version = settings_dict["main_settings"]["version"]
    return version


def get_settings_version(settings_dict):
    settings_version = None
    if 'main_settings' in settings_dict and 'settings_version' in settings_dict["main_settings"]:
        settings_version = settings_dict["main_settings"]["settings_version"]
    return settings_version


# when adding a file migration, the version number in __init__.py.get_settings_version needs to be incremented
# and the current version needs to be set.  Only do this if you add a file migration!
settings_version_translation = [
    '0.4.0rc1.dev2',  # the version here is ambiguous, but this is only used for file migrations
    '0.4.0rc1.dev3',
    '0.4.0rc1.dev4',
    '0.4.0rc1'  # <-- the current file migration version is set to 3, which is THIS version index.
]


def get_version_from_settings_index(index):
    if index > len(settings_version_translation) - 1 or index < 0:
        return None
    return settings_version_translation[index]


def migrate_files(current_version, target_version, data_directory):
    # look up the version names
    has_updated = False
    if current_version is None:
        return False
    if NumberedVersion(current_version) < NumberedVersion("0.4.0rc1.dev3"):
        if migrate_files_pre_0_4_0_rc1_dev3(current_version, data_directory):
            has_updated = True
    return has_updated


def migrate_files_pre_0_4_0_rc1_dev3(current_version, data_directory):

    src = os.path.join(data_directory, "snapshots")
    if not os.path.isdir(src):
        return False
    # create a new directory called tmp
    tmp = os.path.join(data_directory, "tmp")
    if not os.path.isdir(tmp):
        os.mkdir(tmp)
    # make sure a directory called octolapse_snapshots_tmp does not exist in the tmp folder
    dst = os.path.join(tmp, "octolapse_snapshots_tmp")
    if os.path.isdir(dst):
        return False
    # copy all of the files from the snapshots folder to the new directory
    shutil.copytree(src, dst)
    # delete the files within the old directory and remove the folder.
    shutil.rmtree(src)
    return True


def migrate_settings(current_version, settings_dict, default_settings_directory, data_directory):
    # extract the settings version
    # note that the version moved from settings.version to settings.main_settings.version
    version = get_version(settings_dict)
    settings_version = get_settings_version(settings_dict)

    if version == 'unknown':
        raise Exception("Could not find version information within the settings json, cannot perform migration.")

    if version == "0+unknown":
        raise Exception("An unknown settings version was detected, cannot perform migration.")

    # create a copy of the settings
    original_settings_copy = copy.deepcopy(settings_dict)

    # create a flag to indicate that we've updated settings
    has_updated = False

    if settings_version is None and NumberedVersion(version) <= NumberedVersion("0.3.3rc3.dev0"):
        has_updated = True
        settings_dict = migrate_pre_0_3_3_rc3_dev(current_version, settings_dict, os.path.join(default_settings_directory, 'settings_default_0.3.3rc3.dev0.json'))

    if settings_version is None and NumberedVersion(version) < NumberedVersion("0.4.0rc1.dev0"):
        has_updated = True
        settings_dict = migrate_pre_0_3_5_rc1_dev(current_version, settings_dict, os.path.join(default_settings_directory, 'settings_default_0.4.0rc1.dev0.json'))

    if settings_version is None and NumberedVersion(version) < NumberedVersion("0.4.0rc1.dev2"):
        has_updated = True
        settings_dict = migrate_pre_0_4_0_rc1_dev2(current_version, settings_dict, os.path.join(default_settings_directory, 'settings_default_0.4.0rc1.dev2.json'))

    if settings_version is None and NumberedVersion(version) < NumberedVersion("0.4.0rc1.dev3"):
        has_updated = True
        settings_dict = migrate_pre_0_4_0_rc1_dev3(current_version, settings_dict, os.path.join(default_settings_directory, 'settings_default_0.4.0rc1.dev3.json'))

    if settings_version is None and NumberedVersion(version) < NumberedVersion("0.4.0rc1.dev4"):
        has_updated = True
        settings_dict = migrate_pre_0_4_0_rc1_dev4(current_version, settings_dict, os.path.join(default_settings_directory, 'settings_default_0.4.0rc1.dev4.json'))

    # Start using main_settings.settings_version for migrations
    # this value will start off as None
    if settings_version is None:
        has_updated = True
        settings_dict = migrate_pre_0_4_0(current_version, settings_dict, os.path.join(default_settings_directory, 'settings_default_0.4.0.json'))

    if settings_version is not None and NumberedVersion(settings_version) < NumberedVersion("0.4.3"):  # None < 0.4.0
        has_updated = True
        settings_dict = migrate_pre_0_4_0(current_version, settings_dict,
                                          os.path.join(default_settings_directory, 'settings_default_0.4.3.json'))

    # Add other migrations here in the future...

    # if we have updated, create a backup of the current settings
    if has_updated:
        with open(get_settings_backup_name(version, data_directory), "w+") as f:
            json.dump(original_settings_copy, f)

    # Ensure that the version and settings_version within the settings.json file is up to date
    settings_dict["main_settings"]["version"] = current_version
    settings_dict["main_settings"]["settings_version"] = NumberedVersion.CurrentSettingsVersion

    return settings_dict


def get_settings_backup_name(version, default_settings_directory):
    return os.path.join(default_settings_directory, "settings_backup_{0}.json".format(version))


def migrate_post_0_3_5(current_version, settings_dict, log_file_path, default_settings_path):
    # This  is a reminder that the 'version' setting moved to Settings.main_settings.version
    # so you don't forget :)
    raise NotImplementedError("You haven't created this migration yet.")


def migrate_pre_0_3_3_rc3_dev(current_version, settings_dict, default_settings_path):
    # versions prior to or equal to 0.3.3rc3.dev0 need to have the snapshot profiles reset to the defaults

    # get the default settings
    with open(default_settings_path) as settingsJson:
        default_settings = json.load(settingsJson)

    # remove the existing renderings
    settings_dict["snapshots"] = []

    for snapshot in default_settings["snapshots"]:
        settings_dict["snapshots"].append(snapshot)

    # set the default snapshot profile guid so that it is selected by default
    settings_dict["current_snapshot_profile_guid"] = default_settings["current_snapshot_profile_guid"]

    # migrate the camera settings so that if there is no enabled column
    if (
        len(settings_dict["cameras"]) > 0
        and "enabled" not in settings_dict["cameras"][0]
    ):
        # we need to migrate the cameras and enable only the current camera
        for camera in settings_dict["cameras"]:
            if camera["guid"] == settings_dict["current_camera_profile_guid"]:
                camera["enabled"] = True
            else:
                camera["enabled"] = False

    # add any new settings to each profile
    profile_default_types = [
        {
            "profile_type": "printers",
            "default_profile_name": "default_printer_profile"
        },
        {
            "profile_type": "stabilizations",
            "default_profile_name": "default_stabilization_profile"
        },
        {
            "profile_type": "snapshots",
            "default_profile_name": "default_snapshot_profile"
        },
        {
            "profile_type": "cameras",
            "default_profile_name": "default_camera_profile"
        },
        {
            "profile_type": "renderings",
            "default_profile_name": "default_rendering_profile"
        },
        {
            "profile_type": "debug_profiles",
            "default_profile_name": "default_debug_profile"
        },
    ]
    for profile_default in profile_default_types:
        profile_type = profile_default["profile_type"]
        default_profile_name = profile_default["default_profile_name"]
        for index, profile in enumerate(settings_dict[profile_type]):
            defaults_copy = copy.deepcopy(default_settings[default_profile_name])
            defaults_copy.update(profile)
            settings_dict[profile_type][index] = defaults_copy

    # update the version
    settings_dict["version"] = "0.3.3rc3.dev0"
    # return the dict
    return settings_dict


def migrate_pre_0_3_5_rc1_dev(current_version, settings_dict, default_settings_path):

    with open(default_settings_path) as settingsJson:
        default_settings = json.load(settingsJson)

    # Create new settings areas
    profiles = {
        'current_printer_profile_guid': settings_dict.get('current_printer_profile_guid',None),
        'current_stabilization_profile_guid': None,
        'current_trigger_profile_guid': None,
        'current_rendering_profile_guid': settings_dict['current_rendering_profile_guid'],
        'current_camera_profile_guid': settings_dict['current_camera_profile_guid'],
        'current_debug_profile_guid': None,
        'printers': {},
        'stabilizations': {},
        'triggers': {},
        'renderings': {},
        'cameras': {},
        'debug': {},
    }

    #  UPGRADE PRINTER PROFILES
    for printer in settings_dict['printers']:
        #
        speed_units = printer['axis_speed_display_units']
        printer['slicers'] = {}
        slicer_type = printer["slicer_type"]
        # Migrate all slicer settings based on the current slicer type
        if slicer_type == "cura":
            # cura settings
            speed_multiplier = 1 if speed_units == "mm-sec" else 1.0 / 60.0
            cura = {}
            cura["retraction_amount"] = None if "retract_length" not in printer or printer["retract_length"] is None else float(printer["retract_length"])
            cura["retraction_retract_speed"] = None if "retract_speed" not in printer or printer["retract_speed"] is None else float(printer["retract_speed"]) * speed_multiplier
            cura["retraction_prime_speed"] = None if "detract_speed" not in printer or printer["detract_speed"] is None else float(printer["detract_speed"]) * speed_multiplier
            cura["speed_travel"] = None if "movement_speed" not in printer or printer["movement_speed"] is None else float(printer["movement_speed"]) * speed_multiplier
            cura["max_feedrate_z_override"] = None if "maximum_z_speed" not in printer or printer["maximum_z_speed"] is None else float(printer["maximum_z_speed"]) * speed_multiplier
            cura["retraction_hop"] = None if "z_hop" not in printer or printer["z_hop"] is None else float(printer["z_hop"])
            cura["retraction_enable"] = False if cura["retraction_amount"] is None or cura["retraction_amount"] <= 0 else True
            cura["retraction_hop_enabled"] = False if not cura["retraction_enable"] or not cura["retraction_hop"] or float(cura["retraction_hop"]) < 0 else True
            printer['slicers']['cura'] = cura
        elif slicer_type == "other":
            ## other slicer settings
            speed_multiplier = 1  #  if speed_units == "mm-min" else 60.0
            other = {}
            other["retract_length"] = None if "retract_length" not in printer or printer["retract_length"] is None else float(printer["retract_length"])
            other["z_hop"] = None if "z_hop" not in printer or printer["z_hop"] is None else float(printer["z_hop"])
            other["travel_speed"] = None if "movement_speed" not in printer or printer["movement_speed"] is None else float(printer["movement_speed"]) * speed_multiplier
            other["retract_speed"] = None if "retract_speed" not in printer or printer["retract_speed"] is None else float(printer["retract_speed"]) * speed_multiplier
            other["deretract_speed"] = None if "detract_speed" not in printer or printer["detract_speed"] is None else float(printer["detract_speed"]) * speed_multiplier
            other["z_travel_speed"] = None if "z_hop_speed" not in printer or printer["z_hop_speed"] is None else float(printer["z_hop_speed"]) * speed_multiplier
            other["speed_tolerance"] = 1*speed_multiplier  if "speed_tolerance" not in printer or printer["speed_tolerance"] is None else float(printer["speed_tolerance"]) * speed_multiplier
            other["axis_speed_display_units"] = speed_units
            printer['slicers']['other'] = other
        elif slicer_type == "simplify-3d":
            ## Simplify 3d settings
            simlify3d = {}
            speed_multiplier = 1 if speed_units == "mm-min" else 60.0
            simlify3d["retraction_distance"] = None if "retract_length" not in printer or printer["retract_length"] is None else float(printer["retract_length"])
            simlify3d["retraction_vertical_lift"] = None if "z_hop" not in printer or printer["z_hop"] is None else float(printer["z_hop"])
            simlify3d["retraction_speed"] = None if "retract_speed" not in printer or printer["retract_speed"] is None else float(printer["retract_speed"]) * speed_multiplier
            simlify3d["x_y_axis_movement_speed"] = None if "movement_speed" not in printer or printer["movement_speed"] is None else float(printer["movement_speed"]) * speed_multiplier
            simlify3d["z_axis_movement_speed"] = None if "z_hop_speed" not in printer or printer["z_hop_speed"] is None else float(printer["z_hop_speed"]) * speed_multiplier
            simlify3d["axis_speed_display_settings"] = 'mm-min'
            # now set to automatic settings extraction!
            printer['slicer_type'] = 'automatic'
            printer['slicers']['simplify_3d'] = simlify3d
        elif slicer_type == "slic3r-pe":
            slic3rpe = {}
            # slicer PE settings
            speed_multiplier = 1 if speed_units == "mm-sec" else 1.0 / 60.0
            slic3rpe["retract_length"] = None if "retract_length" not in printer or printer["retract_length"] is None else float(printer["retract_length"])
            slic3rpe["retract_lift"] = None if "z_hop" not in printer or printer["z_hop"] is None else float(printer["z_hop"])
            slic3rpe["deretract_speed"] = None if "detract_speed" not in printer or printer["detract_speed"] is None else float(printer["detract_speed"]) * speed_multiplier
            slic3rpe["retract_speed"] = None if "retract_speed" not in printer or printer["retract_speed"] is None else float(printer["retract_speed"]) * speed_multiplier
            slic3rpe["travel_speed"] = None if "movement_speed" not in printer or printer["movement_speed"] is None else float(printer["movement_speed"]) * speed_multiplier
            slic3rpe["axis_speed_display_units"] = 'mm-sec'
            printer['slicer_type'] = 'automatic'
            printer['slicers']['slic3r_pe'] = slic3rpe

        printer["custom_bounding_box"] = True
        printer["override_octoprint_profile_settings"] = printer["override_octoprint_print_volume"]
        profiles['printers'][printer['guid']] = printer

    # set the current printer profile guid
    profiles['current_printer_profile_guid'] = settings_dict['current_printer_profile_guid']
    # UPGRADE STABILIZATION PROFILES - Nothing much has changed.  Copy the existing profiles and add 'disabled' profile
    # restore default stabilizations
    for existing_profile in settings_dict['stabilizations']:
        profiles['stabilizations'][existing_profile["guid"]] = copy.deepcopy(existing_profile)
    # set the current stabilization profile
    profiles['current_stabilization_profile_guid'] = settings_dict['current_stabilization_profile_guid']
    # add the 'disabled' stabilization profile
    disabled_stabilization_guid = 'a1137d9a-70b6-4941-95fb-74c49e0ae9b8'
    profiles["stabilizations"][disabled_stabilization_guid] = copy.deepcopy(default_settings["profiles"]["stabilizations"][disabled_stabilization_guid])

    # UPGRADE TRIGGER PROFILES - previously called snapshot profiles
    profiles["current_trigger_profile_guid"] = (
        default_settings["profiles"]["current_trigger_profile_guid"]
    )
    # upgrade the trigger profiles
    for existing_profile in settings_dict["snapshots"]:
        # first copy all of the settings into the new profiles dict
        new_profile = copy.deepcopy(existing_profile)
        # set the current trigger type, which is now called the trigger subtype
        new_profile["trigger_subtype"] = existing_profile["trigger_type"]
        # set the trigger type, which will always be real-time
        new_profile["trigger_type"] = "real-time"
        # update the extruder trigger requirements
        new_profile["trigger_on_retracted"] = "trigger_on"
        new_profile["trigger_on_retracting_start"] =  ""
        new_profile["trigger_on_extruding"] = "trigger_on"
        new_profile["trigger_on_extruding_start"] = "trigger_on"
        new_profile["trigger_on_partially_retracted"] = "forbidden"
        new_profile["trigger_on_primed"] = "trigger_on"
        new_profile["trigger_on_deretracting"] = "forbidden"
        new_profile["trigger_on_retracting"] = ""
        new_profile["trigger_on_deretracted"] = "forbidden"
        new_profile["trigger_on_deretracting_start"] = ""
        # add the new preofile
        profiles["triggers"][existing_profile["guid"]] = new_profile

    # set the current trigger profile
    profiles['current_trigger_profile_guid'] = settings_dict['current_snapshot_profile_guid']


    # Remove python 2 support
    # for key, default_profile in six.iteritems(default_settings["profiles"]["triggers"]):
    # add all of the new triggers (the non-real time triggers)
    for key, default_profile in default_settings["profiles"]["triggers"].items():
        if default_profile["trigger_type"] != 'real-time':
            # add this setting, it's new!
            profiles["triggers"][key] = default_profile

    # UPGRADE THE RENDERING PROFILES, a few settings have moved from the former snapshot profile
    # extract some info from the previous snapshot profile to use as the default values for the rendering profile
    current_snapshot_guid = settings_dict["current_snapshot_profile_guid"]
    current_snapshot_profile = None
    for snapshot_profile in settings_dict["snapshots"]:
        if snapshot_profile["guid"] == current_snapshot_guid:
            current_snapshot_profile = snapshot_profile
            break

    if current_snapshot_profile is not None:
        # we found a snapshot profile that has these new rendering profile settings.  Save them
        cleanup_after_render_complete = current_snapshot_profile['cleanup_after_render_complete']
        cleanup_after_render_fail = current_snapshot_profile['cleanup_after_render_fail']
    else:
        # no default snapshot profile found, this is unexpected, but could happen
        # extract the new rendering profile settings from our new default rendering profile
        default_rendering_profile = default_settings["profiles"]["defaults"]["rendering"]
        cleanup_after_render_complete = default_rendering_profile['cleanup_after_render_complete']
        cleanup_after_render_fail = default_rendering_profile['cleanup_after_render_fail']

    ## apply the new settings to each rendering profile
    for rendering in settings_dict['renderings']:
        rendering["cleanup_after_render_complete"] = cleanup_after_render_complete
        rendering["cleanup_after_render_fail"] = cleanup_after_render_fail
        profiles['renderings'][rendering["guid"]] = rendering

    # UPGRADE CAMERA PROFILES.  The structure has changed quite a bit.
    default_camera_profile = default_settings["profiles"]["defaults"]["camera"]
    for camera in settings_dict['cameras']:
        if camera["camera_type"] == "external-script":
            camera["camera_type"] = "script"
        elif camera["camera_type"] == "printer-gcode":
            camera["camera_type"] = "gcode"
        camera['webcam_settings'] = {
            "white_balance_temperature": camera['white_balance_temperature'],
            "sharpness": camera['sharpness'],
            "focus": camera['focus'],
            "backlight_compensation_enabled": camera['backlight_compensation_enabled'],
            "snapshot_request_template": camera['snapshot_request_template'],
            "stream_template": default_camera_profile['webcam_settings']['stream_template'],
            "led1_mode": camera['led1_mode'],
            "ignore_ssl_error": camera['ignore_ssl_error'],
            "tilt": camera['tilt'],
            "exposure_auto_priority_enabled": camera['exposure_auto_priority_enabled'],
            "exposure_type": camera['exposure_type'],
            "pan": camera['pan'],
            "username": camera['username'],
            "saturation": camera['saturation'],
            "autofocus_enabled": camera['autofocus_enabled'],
            "white_balance_auto": camera['white_balance_auto'],
            "led1_frequency": camera['led1_frequency'],
            "contrast": camera['contrast'],
            "gain": camera['gain'],
            "address": camera['address'],
            "password": camera['password'],
            "exposure": camera['exposure'],
            "brightness": camera['brightness'],
            "zoom": camera['zoom'],
            "jpeg_quality": camera['jpeg_quality'],
            "powerline_frequency": camera['powerline_frequency'],
        }

        del camera['white_balance_temperature'],
        del camera['sharpness'],
        del camera['focus'],
        del camera['backlight_compensation_enabled'],
        del camera['snapshot_request_template'],
        del camera['led1_mode'],
        del camera['ignore_ssl_error'],
        del camera['tilt'],
        del camera['exposure_auto_priority_enabled'],
        del camera['exposure_type'],
        del camera['pan'],
        del camera['username'],
        del camera['saturation'],
        del camera['autofocus_enabled'],
        del camera['white_balance_auto'],
        del camera['led1_frequency'],
        del camera['contrast'],
        del camera['gain'],
        del camera['address'],
        del camera['password'],
        del camera['exposure'],
        del camera['brightness'],
        del camera['zoom'],
        del camera['jpeg_quality'],
        del camera['powerline_frequency'],
        profiles['cameras'][camera['guid']] = camera

    # Remove python 2 support
    # for key, default_profile in six.iteritems(default_settings['profiles']['debug']):

    # UPGRADE THE DEBUG PROFILES - remove and replace the debug profiles, they are too different to salvage
    for key, default_profile in default_settings['profiles']['debug'].items():
        profiles['debug'][key] = default_profile
    # set the default debug profile
    profiles["current_debug_profile_guid"] = default_settings['profiles']['current_debug_profile_guid']

    # UPGRADE THE MAIN SETTINGS - use the defaults if no value is provided
    default_main_settings = default_settings["main_settings"]
    main_settings = {
        'show_navbar_icon': settings_dict.get('show_navbar_icon',default_main_settings["show_navbar_icon"]),
        'show_navbar_when_not_printing': settings_dict.get('show_navbar_when_not_printing',default_main_settings["show_navbar_when_not_printing"]),
        'is_octolapse_enabled': settings_dict.get('is_octolapse_enabled',default_main_settings["is_octolapse_enabled"]),
        'auto_reload_latest_snapshot': settings_dict.get('auto_reload_latest_snapshot',default_main_settings["auto_reload_latest_snapshot"]),
        'auto_reload_frames': settings_dict.get('auto_reload_frames',default_main_settings["auto_reload_frames"]),
        'show_printer_state_changes': settings_dict.get('show_position_state_changes',default_main_settings["show_printer_state_changes"]),
        'show_position_changes': settings_dict.get('show_position_changes',default_main_settings["show_position_changes"]),
        'show_extruder_state_changes': settings_dict.get('show_extruder_state_changes',default_main_settings["show_extruder_state_changes"]),
        'show_trigger_state_changes': settings_dict.get('show_trigger_state_changes',default_main_settings["show_trigger_state_changes"]),
        'cancel_print_on_startup_error': settings_dict.get('cancel_print_on_startup_error', default_main_settings["cancel_print_on_startup_error"]),
        "show_snapshot_plan_information": default_main_settings["show_snapshot_plan_information"],
        'platform': sys.platform,
        'version': "0.4.0rc1.dev0"
    }

    # ADD ALL NEW VALUES TO THE NEW SETTINGS - Update any leftover settings.  Note that chages will only be made if
    # the current 'profiles' do not contain some of the new default settings.
    profile_default_types = [
        {
            "profile_type": "printers",
            "default_profile_name": "printer",
        },
        {
            "profile_type": "stabilizations",
            "default_profile_name": "stabilization",
        },
        {
            "profile_type": "triggers",
            "default_profile_name": "trigger",
        },
        {
            "profile_type": "cameras",
            "default_profile_name": "camera",
        },
        {
            "profile_type": "renderings",
            "default_profile_name": "rendering",
        },
        {
            "profile_type": "debug",
            "default_profile_name": "debug",
        },
    ]

    for profile_default in profile_default_types:
        profile_type = profile_default["profile_type"]
        default_profile_name = profile_default["default_profile_name"]
        # Remove python 2 support
        # for key, profile in six.iteritems(profiles[profile_type]):
        for key, profile in profiles[profile_type].items():
            defaults_copy = copy.deepcopy(default_settings["profiles"]["defaults"][default_profile_name])
            defaults_copy.update(profile)
            profiles[profile_type][key] = defaults_copy


    # return the new upgraded settings dict
    return {
        'main_settings': main_settings,
        'profiles': profiles
    }


def migrate_pre_0_4_0_rc1_dev2(current_version, settings_dict, default_settings_path):
    default_settings = get_default_settings(default_settings_path)
    # remove all triggers
    settings_dict["profiles"]["triggers"] = {}
    # add the default triggers
    triggers = default_settings["profiles"]["triggers"]
    # Remove python 2 support
    # for key, trigger in six.iteritems(triggers):
    for key, trigger in triggers.items():
        # Add default triggers
        settings_dict["profiles"]["triggers"][key] = trigger

    # set the current trigger
    settings_dict["profiles"]["current_trigger_profile_guid"] = default_settings["profiles"]["current_trigger_profile_guid"]

    settings_dict["main_settings"]["version"] = "0.4.0rc1.dev2"
    return settings_dict


def migrate_pre_0_4_0_rc1_dev3(current_version, settings_dict, default_settings_path):
    # adjust each slicer profile to account for the new multiple extruder settings
    printers = settings_dict["profiles"]["printers"]
    default_settings = get_default_settings(default_settings_path)
    # Remove python 2 support
    # for key, printer in six.iteritems(printers):
    for key, printer in printers.items():

        # Adjust gcode generation settings
        if "gcode_generation_settings" in printer:
            gen = printer["gcode_generation_settings"]
            extruder = {
                "retract_before_move": gen.get('retract_before_move', None),
                "retraction_length": gen.get('retraction_length', None),
                "retraction_speed": gen.get('retraction_speed', None),
                "deretraction_speed": gen.get('deretraction_speed', None),
                "lift_when_retracted": gen.get('lift_when_retracted', None),
                "z_lift_height": gen.get('z_lift_height', None),
                "x_y_travel_speed": gen.get('x_y_travel_speed', None),
                "first_layer_travel_speed": gen.get('first_layer_travel_speed', None),
                "z_lift_speed": gen.get('z_lift_speed', None)
            }
            gen["extruders"] = [extruder]
            gen.pop("retract_before_move", None)
            gen.pop("retraction_length", None)
            gen.pop("retraction_speed", None)
            gen.pop("deretraction_speed", None)
            gen.pop("lift_when_retracted", None)
            gen.pop("z_lift_height", None)
            gen.pop("x_y_travel_speed", None)
            gen.pop("first_layer_travel_speed", None)
            gen.pop("z_lift_speed", None)

        # Adjust slicer settings
        slicers = printer["slicers"]
        # Adjust Cura Settings
        if "cura" in slicers:
            cura = slicers["cura"]
            cura_extruder = {
                "version": cura.get("version", None),
                "speed_z_hop": cura.get("speed_z_hop", None),
                "max_feedrate_z_override": cura.get("max_feedrate_z_override", None),
                "retraction_amount": cura.get("retraction_amount", None),
                "retraction_hop": cura.get("retraction_hop", None),
                "retraction_hop_enabled": cura.get("retraction_hop_enabled", None),
                "retraction_enable": cura.get("retraction_enable", None),
                "retraction_speed": cura.get("retraction_speed", None),
                "retraction_retract_speed": cura.get("retraction_retract_speed", None),
                "retraction_prime_speed": cura.get("retraction_prime_speed", None),
                "speed_travel": cura.get("speed_travel", None),
            }
            cura["machine_extruder_count"] = 1
            cura["extruders"] = [cura_extruder]
            cura.pop("speed_z_hop", None)
            cura.pop("max_feedrate_z_override", None)
            cura.pop("retraction_amount", None)
            cura.pop("retraction_hop", None)
            cura.pop("retraction_hop_enabled", None)
            cura.pop("retraction_enable", None)
            cura.pop("retraction_speed", None)
            cura.pop("retraction_retract_speed", None)
            cura.pop("retraction_prime_speed", None)
            cura.pop("speed_travel", None)

        if "other" in slicers:
            # Adjust Other Slicer Settings
            other = slicers["other"]
            retract_length = other.get("retract_length", None)
            retract_before_move = other.get("retract_before_move", None)
            z_hop = other.get("z_hop", None)
            lift_when_retracted = other.get("lift_when_retracted", None)
            retract_before_move = (
                retract_length > 0 if retract_before_move is None else retract_before_move
            )
            lift_when_retracted = (
                retract_before_move and z_hop > 0 if lift_when_retracted is None else lift_when_retracted
            )

            other_extruder = {
                "retract_length": retract_length,
                "z_hop": z_hop,
                "retract_speed": other.get("retract_speed", None),
                "deretract_speed": other.get("deretract_speed", None),
                "lift_when_retracted": lift_when_retracted,
                "travel_speed": other.get("travel_speed", None),
                "z_travel_speed": other.get("z_travel_speed", None),
                "retract_before_move": retract_before_move
            }
            other["extruders"] = [other_extruder]
            other.pop("retract_length", None)
            other.pop("z_hop", None)
            other.pop("retract_speed", None)
            other.pop("deretract_speed", None)
            other.pop("travel_speed", None)
            other.pop("z_travel_speed", None)
            other.pop("lift_when_retracted", None)
            other.pop("retract_before_move", None)

        if "simplify_3d" in slicers:
            # Adjust Simplify3D Settings
            simplify = slicers["simplify_3d"]
            simplify_extruder = {
                'retraction_distance': simplify.get("retraction_distance", None),
                'retraction_vertical_lift': simplify.get("retraction_vertical_lift", None),
                'retraction_speed': simplify.get("retraction_speed", None),
                'extruder_use_retract': simplify.get("extruder_use_retract", None),
            }
            simplify.pop("extruders", None)
            simplify.pop("retraction_distance", None)
            simplify.pop("retraction_vertical_lift", None)
            simplify.pop("retraction_speed", None)
            simplify.pop("extruder_use_retract", None)

        if "slic3r_pe" in slicers:
            # Adjust Slic3r Settings
            slic3r_pe = slicers["slic3r_pe"]
            if "retract_before_travel" in slic3r_pe:
                del slic3r_pe["retract_before_travel"]
            slic3r_extruder = {
                "retract_length": slic3r_pe.get("retract_length", None),
                "retract_lift": slic3r_pe.get("retract_lift", None),
                "retract_speed": slic3r_pe.get("retract_speed", None),
                "deretract_speed": slic3r_pe.get("deretract_speed", None),
            }
            slic3r_pe["extruders"] = [slic3r_extruder]
            slic3r_pe.pop("retract_length", None)
            slic3r_pe.pop("retract_lift", None)
            slic3r_pe.pop("retract_speed", None)
            slic3r_pe.pop("deretract_speed", None)

    renderings = settings_dict["profiles"]["renderings"]
    # Remove python 2 support
    # for key, render in six.iteritems(renderings):
    for key, render in renderings.items():
        render["archive_snapshots"] = not render.get("cleanup_after_render_complete", True)
        render.pop("cleanup_after_render_complete",None)
        render.pop("cleanup_after_render_fail",None)
        render.pop("snapshot_to_skip_end", None)
        render.pop("snapshots_to_skip_end", None)
        render.pop("snapshots_to_skip_beginning", None)

    triggers = settings_dict["profiles"]["triggers"]
    # Remove python 2 support
    #for key, trigger in six.iteritems(triggers):
    for key, trigger in triggers.items():
        if "trigger_type" in trigger and trigger["trigger_type"] == 'smart-layer':
            trigger["trigger_type"] = "smart"

    # Reset the debug profiles to the defaults
    if "debug" in settings_dict["profiles"]:
        del settings_dict["profiles"]["debug"]
    if "current_debug_profile_guid" in settings_dict["profiles"]:
        del settings_dict["profiles"]["current_debug_profile_guid"]
    settings_dict["profiles"]["logging"] = default_settings["profiles"]["logging"]
    settings_dict["profiles"]["current_logging_profile_guid"] = default_settings["profiles"]["current_logging_profile_guid"]

    # set the version
    settings_dict["main_settings"]["version"] = "0.4.0rc1.dev3"
    return settings_dict


def migrate_pre_0_4_0_rc1_dev4(current_version, settings_dict, default_settings_path):
    settings_dict["main_settings"]["version"] = "0.4.0rc1.dev4"
    return settings_dict

def migrate_pre_0_4_0(current_version, settings_dict, default_settings_path):
    # Switch to Settings Version for migration starting at "0.4.0"
    default_settings = get_default_settings(default_settings_path)

    # reset stabilizations
    settings_dict["profiles"]["stabilizations"] = default_settings["profiles"]["stabilizations"]
    settings_dict["profiles"]["current_stabilization_profile_guid"] = default_settings["profiles"][
        "current_stabilization_profile_guid"]

    # reset renderings
    settings_dict["profiles"]["renderings"] = default_settings["profiles"]["renderings"]
    settings_dict["profiles"]["current_rendering_profile_guid"] = default_settings["profiles"][
        "current_rendering_profile_guid"]

    # Add 'Smart - Gcode' trigger
    smart_gcode_trigger = default_settings["profiles"]["triggers"].get("b838fe36-1459-4867-8243-ab7604cf0e2d", None)
    if smart_gcode_trigger is not None:
        settings_dict["profiles"]["triggers"]["b838fe36-1459-4867-8243-ab7604cf0e2d"] = smart_gcode_trigger

    # Add the script camera debug logging profile
    script_camera_debug_logging = default_settings["profiles"]["logging"].get(
        "fa759ab9-bc02-4fd0-8d12-a7c5c89591c1", None
    )
    if smart_gcode_trigger is not None:
        settings_dict["profiles"]["logging"]["fa759ab9-bc02-4fd0-8d12-a7c5c89591c1"] = script_camera_debug_logging

    return settings_dict

def migrate_pre_0_4_3(current_version, settings_dict, default_settings_path):
    # Switch to Settings Version for migration starting at "0.4.0"
    default_settings = get_default_settings(default_settings_path)

    # add the allow_smart_snapshot_commands setting to all triggers with the value True
    for trigger in settings_dict["profiles"]["triggers"]:
        trigger["allow_smart_snapshot_commands"] = True
    return settings_dict


def get_default_settings(default_settings_path):
    with open(default_settings_path) as defaultSettingsJson:
        data = json.load(defaultSettingsJson)
        # if a settings file does not exist, create one ??
        return data
