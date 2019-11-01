from distutils.version import LooseVersion
import json
import sys
import os
import six
import copy
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

def migrate_settings(current_version, settings_dict, default_settings_directory, data_directory):
    # extract the settings version
    # note that the version moved from settings.version to settings.main_settings.version
    version = get_version(settings_dict)
    if version == 'unknown':
        raise Exception("Could not find the settings version.")

    # create a copy of the settings
    original_settings_copy = copy.deepcopy(settings_dict)

    # create a flag to indicate that we've updated settings
    has_updated = False

    if LooseVersion(version) <= LooseVersion("0.3.3rc3.dev0"):
        has_updated = True
        settings_dict = migrate_pre_0_3_3_rc3_dev(current_version, settings_dict, os.path.join(default_settings_directory, 'settings_default_0.3.3rc3.dev0.json'))

    if LooseVersion(version) < LooseVersion("0.4.0rc1.dev0"):
        has_updated = True
        settings_dict = migrate_pre_0_3_5_rc1_dev(current_version, settings_dict, os.path.join(default_settings_directory, 'settings_default_0.4.0rc1.dev0.json'))

    if LooseVersion(version) < LooseVersion("0.4.0rc1.dev2"):
        has_updated = True
        settings_dict = migrate_pre_0_4_0_rc1_dev2(current_version, settings_dict, os.path.join(default_settings_directory, 'settings_default_0.4.0rc1.dev2.json'))

    if LooseVersion(version) < LooseVersion("0.4.0rc1.dev3"):
        has_updated = True
        settings_dict = migrate_pre_0_4_0_rc1_dev3(current_version, settings_dict, os.path.join(default_settings_directory, 'settings_default_0.4.0rc1.dev3.json'))

    # If we've updated the settings, save a backup of the old settings and update the version
    if has_updated:
        with open(get_settings_backup_name(version, data_directory), "w+") as f:
            json.dump(original_settings_copy, f)
        settings_dict["main_settings"]["version"] = current_version

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

    # add all of the new triggers (the non-real time triggers)
    for key, default_profile in six.iteritems(default_settings["profiles"]["triggers"]):
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

    # UPGRADE THE DEBUG PROFILES - remove and replace the debug profiles, they are too different to salvage
    for key, default_profile in six.iteritems(default_settings['profiles']['debug']):
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
        for key, profile in six.iteritems(profiles[profile_type]):
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
    for key, trigger in six.iteritems(triggers):
        # remove all triggers
        settings_dict["profiles"]["triggers"][key] = trigger

    # set the current trigger
    settings_dict["profiles"]["current_trigger_profile_guid"] = default_settings["profiles"]["current_trigger_profile_guid"]

    settings_dict["main_settings"]["version"] = "0.4.0rc1.dev2"
    return settings_dict

def migrate_pre_0_4_0_rc1_dev3(current_version, settings_dict, default_settings_path):
    # adjust each slicer profile to account for the new multiple extruder settings
    printers = settings_dict["profiles"]["printers"]
    for key, printer in six.iteritems(printers):
        ## Adjust gcode generation settings
        gen = printer["gcode_generation_settings"]
        extruder = {
            "retract_before_move": gen['retract_before_move'],
            "retraction_length": gen['retraction_length'],
            "retraction_speed": gen['retraction_speed'],
            "deretraction_speed": gen['deretraction_speed'],
            "lift_when_retracted": gen['lift_when_retracted'],
            "z_lift_height": gen['z_lift_height'],
            "x_y_travel_speed": gen['x_y_travel_speed'],
            "first_layer_travel_speed": gen['first_layer_travel_speed'],
            "z_lift_speed": gen['z_lift_speed'],
        }
        gen["extruders"] = [extruder]
        del gen["retract_before_move"]
        del gen["retraction_length"]
        del gen["retraction_speed"]
        del gen["deretraction_speed"]
        del gen["lift_when_retracted"]
        del gen["z_lift_height"]
        del gen["x_y_travel_speed"]
        del gen["first_layer_travel_speed"]
        del gen["z_lift_speed"]

        # Adjust slicer settings
        slicers = printer["slicers"]
        # Adjust Cura Settings
        cura = slicers["cura"]
        cura_extruder = {
            "version": cura["version"],
            "speed_z_hop": cura["speed_z_hop"],
            "max_feedrate_z_override": cura["max_feedrate_z_override"],
            "retraction_amount": cura["retraction_amount"],
            "retraction_hop": cura["retraction_hop"],
            "retraction_hop_enabled": cura["retraction_hop_enabled"],
            "retraction_enable": cura["retraction_enable"],
            "retraction_speed": cura["retraction_speed"],
            "retraction_retract_speed": cura["retraction_retract_speed"],
            "retraction_prime_speed": cura["retraction_prime_speed"],
            "speed_travel": cura["speed_travel"],
        }
        cura["machine_extruder_count"] = 1
        cura["extruders"] = [cura_extruder]
        del cura["speed_z_hop"]
        del cura["max_feedrate_z_override"]
        del cura["retraction_amount"]
        del cura["retraction_hop"]
        del cura["retraction_hop_enabled"]
        del cura["retraction_enable"]
        del cura["retraction_speed"]
        del cura["retraction_retract_speed"]
        del cura["retraction_prime_speed"]
        del cura["speed_travel"]

        # Adjust Other Slicer Settings
        other = slicers["other"]
        other_extruder = {
            "retract_length": other["retract_length"],
            "z_hop": other["z_hop"],
            "retract_speed": other["retract_speed"],
            "deretract_speed": other["deretract_speed"],
            "lift_when_retracted": other["lift_when_retracted"],
            "travel_speed": other["travel_speed"],
            "z_travel_speed": other["z_travel_speed"],
            "retract_before_move": other["retract_before_move"]
        }
        other["extruders"] = [other_extruder]
        del other["retract_length"]
        del other["z_hop"]
        del other["retract_speed"]
        del other["deretract_speed"]
        del other["lift_when_retracted"]
        del other["retract_before_move"]
        del other["travel_speed"]
        del other["z_travel_speed"]

        # Adjust Simplify3D Settings
        simplify = slicers["simplify_3d"]
        simplify_extruder = {
            'retraction_distance': simplify["retraction_distance"],
            'retraction_vertical_lift': simplify["retraction_vertical_lift"],
            'retraction_speed': simplify["retraction_speed"],
            'extruder_use_retract': simplify["extruder_use_retract"]
        }
        simplify["extruders"] = [simplify_extruder]
        del simplify["retraction_distance"]
        del simplify["retraction_vertical_lift"]
        del simplify["retraction_speed"]
        del simplify["extruder_use_retract"]

        # Adjust Slic3r Settings
        slic3r_pe = slicers["slic3r_pe"]
        del slic3r_pe["retract_before_travel"]
        slic3r_extruder = {
            "retract_length": slic3r_pe["retract_length"],
            "retract_lift": slic3r_pe["retract_lift"],
            "retract_speed": slic3r_pe["retract_speed"],
            "deretract_speed": slic3r_pe["deretract_speed"],
        }
        slic3r_pe["extruders"] = [slic3r_extruder]
        del slic3r_pe["retract_length"]
        del slic3r_pe["retract_lift"]
        del slic3r_pe["retract_speed"]
        del slic3r_pe["deretract_speed"]

    settings_dict["main_settings"]["version"] = "0.4.0rc1.dev3"
    return settings_dict

def get_default_settings(default_settings_path):
    with open(default_settings_path) as defaultSettingsJson:
        data = json.load(defaultSettingsJson)
        # if a settings file does not exist, create one ??
        return data
