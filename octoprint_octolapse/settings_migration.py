from distutils.version import LooseVersion
import json
import sys
import os
from octoprint_octolapse.settings import OctolapseSettings, PrinterProfile, StabilizationProfile, SnapshotProfile, RenderingProfile, CameraProfile, DebugProfile


def migrate_settings(current_version, settings_dict, log_file_path, default_settings_directory):

    if LooseVersion(settings_dict["version"]) <= LooseVersion("0.3.3rc3.dev0"):
        return migrate_pre_0_3_3_rc3_dev(current_version, settings_dict, log_file_path, os.path.join(default_settings_directory,'settings_default_0_3_4.json'))
    elif LooseVersion(settings_dict["version"]) <= LooseVersion("0.3.5rc1.dev0"):
        return migrate_pre_0_3_5_rc1_dev(current_version, settings_dict, log_file_path,  os.path.join(default_settings_directory + 'settings_default.json'))
    return settings_dict


def migrate_pre_0_3_3_rc3_dev(current_version, settings_dict, log_file_path, default_settings_path):
    # versions prior to or equal to 0.3.3rc3.dev0 need to have the snapshot profiles reset to the defaults

    # get the default settings
    new_settings = OctolapseSettings(log_file_path, get_default_settings(default_settings_path), current_version)

    # remove the existing renderings
    settings_dict["snapshots"] = []

    for key, snapshot in new_settings.snapshots.items():
        settings_dict["snapshots"].append(snapshot.to_dict())

    # set the default snapshot profile guid so that it is selected by default
    settings_dict["current_snapshot_profile_guid"] = new_settings.current_snapshot_profile_guid

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

    # update the version
    settings_dict["version"] = current_version
    # return the dict
    return settings_dict

def migrate_pre_0_3_5_rc1_dev(current_version, settings_dict, log_file_path, default_settings_path):

    # Create new settings areas
    profiles = {
        'current_printer_profile_guid': settings_dict['current_printer_profile_guid'],
        'current_stabilization_profile_guid': settings_dict['current_stabilization_profile_guid'],
        'current_snapshot_profile_guid': settings_dict['current_snapshot_profile_guid'],
        'current_rendering_profile_guid': settings_dict['current_rendering_profile_guid'],
        'current_camera_profile_guid': settings_dict['current_camera_profile_guid'],
        'current_debug_profile_guid': settings_dict['current_debug_profile_guid'],
        'printers': {},
        'stabilizations': {},
        'snapshots': {},
        'renderings': {},
        'cameras': {},
        'debug': {},
        'defaults': {
            'printer':PrinterProfile().to_dict(),
            'stabilization':StabilizationProfile().to_dict(),
            'snapshot': SnapshotProfile().to_dict(),
            'rendering': RenderingProfile().to_dict(),
            'camera': CameraProfile().to_dict(),
            'debug': DebugProfile().to_dict(),
        }
    }

    # add all profiles
    for printer in settings_dict['printers']:
        profiles['printers'][printer['guid']] = printer

    for stabilization in settings_dict['stabilizations']:
        profiles['stabilizations'][stabilization['guid']] = stabilization

    for snapshot in settings_dict['snapshots']:
        profiles['snapshots'][snapshot['guid']] = snapshot

    for rendering in settings_dict['renderings']:
        profiles['renderings'][rendering['guid']] = rendering

    for camera in settings_dict['cameras']:
        profiles['cameras'][camera['guid']] = camera

    for debug in settings_dict['debug_profiles']:
        profiles['debug'][debug['guid']] = debug

    main_settings = {
        'show_navbar_icon': settings_dict['show_navbar_icon'],
        'show_navbar_when_not_printing': settings_dict['show_navbar_when_not_printing'],
        'is_octolapse_enabled': settings_dict['is_octolapse_enabled'],
        'auto_reload_latest_snapshot': settings_dict['auto_reload_latest_snapshot'],
        'auto_reload_frames': settings_dict['auto_reload_frames'],
        'show_position_state_changes': settings_dict['show_position_state_changes'],
        'show_position_changes': settings_dict['show_position_changes'],
        'show_extruder_state_changes': settings_dict['show_extruder_state_changes'],
        'show_trigger_state_changes': settings_dict['show_trigger_state_changes'],
        'show_real_snapshot_time': settings_dict['show_real_snapshot_time'],
        'cancel_print_on_startup_error': settings_dict['cancel_print_on_startup_error'],
        'platform': sys.platform
    }

    # return the new dict
    return {
        'version': current_version,
        'main_settings': main_settings,
        'profiles': profiles
    }


def get_default_settings(default_settings_path):
    with open(default_settings_path) as defaultSettingsJson:
        data = json.load(defaultSettingsJson)
        # if a settings file does not exist, create one ??
        return data;
