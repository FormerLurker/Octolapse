from subprocess import CalledProcessError
from distutils.version import LooseVersion
import json
import sys
import os
from octoprint_octolapse.settings import \
    OctolapseSettings, PrinterProfile, StabilizationProfile, RenderingProfile, CameraProfile, DebugProfile, \
    Slic3rPeSettings, Simplify3dSettings, CuraSettings, OtherSlicerSettings

# create the module level logger
from octoprint_octolapse.log import LoggingConfigurator
logging_configurator = LoggingConfigurator()
logger = logging_configurator.get_logger(__name__)


def migrate_settings(current_version, settings_dict, log_file_path, default_settings_directory):

    if LooseVersion(settings_dict["version"]) <= LooseVersion("0.3.3rc3.dev0"):
        settings_dict = migrate_pre_0_3_3_rc3_dev(current_version, settings_dict, log_file_path, os.path.join(default_settings_directory,'settings_default_0_3_4.json'))
    elif LooseVersion(settings_dict["version"]) <= LooseVersion("0.3.5rc1.dev0"):
        settings_dict = migrate_pre_0_3_5_rc1_dev(current_version, settings_dict, log_file_path,  os.path.join(default_settings_directory + 'settings_default.json'))

    return settings_dict


def migrate_post_0_3_5(current_version, settings_dict, log_file_path, default_settings_path):
    # This  is a reminder that the 'version' setting moved to Settings.main_settings.version
    # so you don't forget :)
    raise NotImplementedError("You haven't created this migration yet.")

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
            'rendering': RenderingProfile().to_dict(),
            'camera': CameraProfile().to_dict(),
            'debug': DebugProfile().to_dict(),
        }
    }

    # add all profiles
    for printer in settings_dict['printers']:
        #
        speed_units = printer['axis_speed_display_units']
        printer['slicers'] = {}
        slicer_type = printer["slicer_type"]
        # Migrate all slicer settings based on the current slicer type
        if slicer_type == "cura":
            # cura settings
            speed_multiplier = 1 if speed_units == "mm-sec" else 1.0 / 60.0
            cura = CuraSettings()
            cura.retraction_amount = None if "retract_length" not in printer or printer["retract_length"] is None else float(printer["retract_length"])
            cura.retraction_retract_speed = None if "retract_speed" not in printer or printer["retract_speed"] is None else float(printer["retract_speed"]) * speed_multiplier
            cura.retraction_prime_speed = None if "detract_speed" not in printer or printer["detract_speed"] is None else float(printer["detract_speed"]) * speed_multiplier
            cura.speed_print = None if "print_speed" not in printer or printer["print_speed"] is None else float(printer["print_speed"]) * speed_multiplier
            cura.speed_infill = None if "infill_speed" not in printer or printer["infill_speed"] is None else float(printer["infill_speed"]) * speed_multiplier
            cura.speed_wall_0 = None if "external_perimeter_speed" not in printer or printer["external_perimeter_speed"] is None else float(printer["external_perimeter_speed"]) * speed_multiplier
            cura.speed_wall_x = None if "perimeter_speed" not in printer or printer["perimeter_speed"] is None else float(printer["perimeter_speed"]) * speed_multiplier
            cura.speed_topbottom = None if "top_solid_infill_speed" not in printer or printer["top_solid_infill_speed"] is None else float(printer["top_solid_infill_speed"]) * speed_multiplier
            cura.speed_travel = None if "movement_speed" not in printer or printer["movement_speed"] is None else float(printer["movement_speed"]) * speed_multiplier
            cura.speed_print_layer_0 = None if "first_layer_speed" not in printer or printer["first_layer_speed"] is None else float(printer["first_layer_speed"]) * speed_multiplier
            cura.speed_travel_layer_0 = None if "first_layer_travel_speed" not in printer or printer["first_layer_travel_speed"] is None else float(printer["first_layer_travel_speed"]) * speed_multiplier
            cura.skirt_brim_speed = None if "skirt_brim_speed" not in printer or printer["skirt_brim_speed"] is None else float(printer["skirt_brim_speed"]) * speed_multiplier
            cura.max_feedrate_z_override = None if "maximum_z_speed" not in printer or printer["maximum_z_speed"] is None else float(printer["maximum_z_speed"]) * speed_multiplier
            cura.speed_slowdown_layers = None if "num_slow_layers" not in printer or printer["num_slow_layers"] is None else int(printer["num_slow_layers"])
            cura.retraction_hop = None if "z_hop" not in printer or printer["z_hop"] is None else float(printer["z_hop"])
            printer['slicers']['cura'] = cura
        elif slicer_type == "other":
            ## other slicer settings
            speed_multiplier = 1 if speed_units == "mm-min" else 60.0
            other = OtherSlicerSettings()
            other.retract_length = None if "retract_length" not in printer or printer["retract_length"] is None else float(printer["retract_length"])
            other.z_hop = None if "z_hop" not in printer or printer["z_hop"] is None else float(printer["z_hop"])
            other.travel_speed = None if "movement_speed" not in printer or printer["movement_speed"] is None else float(printer["movement_speed"]) * speed_multiplier
            other.first_layer_travel_speed = None if "first_layer_travel_speed" not in printer or printer["first_layer_travel_speed"] is None else float(printer["first_layer_travel_speed"]) * speed_multiplier
            other.retract_speed = None if "retract_speed" not in printer or printer["retract_speed"] is None else float(printer["retract_speed"]) * speed_multiplier
            other.deretract_speed = None if "detract_speed" not in printer or printer["detract_speed"] is None else float(printer["detract_speed"]) * speed_multiplier
            other.print_speed = None if "print_speed" not in printer or printer["print_speed"] is None else float(printer["print_speed"]) * speed_multiplier
            other.first_layer_print_speed = None if "first_layer_speed" not in printer or printer["first_layer_speed"] is None else float(printer["first_layer_speed"]) * speed_multiplier
            other.z_travel_speed = None if "z_hop_speed" not in printer or printer["z_hop_speed"] is None else float(printer["z_hop_speed"]) * speed_multiplier
            other.perimeter_speed = None if "perimeter_speed" not in printer or printer["perimeter_speed"] is None else float(printer["perimeter_speed"]) * speed_multiplier
            other.small_perimeter_speed = None if "small_perimeter_speed" not in printer or printer["small_perimeter_speed"] is None else float(printer["small_perimeter_speed"]) * speed_multiplier
            other.external_perimeter_speed = None if "external_perimeter_speed" not in printer or printer["external_perimeter_speed"] is None else float(printer["external_perimeter_speed"]) * speed_multiplier
            other.infill_speed = None if "infill_speed" not in printer or printer["infill_speed"] is None else float(printer["infill_speed"]) * speed_multiplier
            other.solid_infill_speed = None if "solid_infill_speed" not in printer or printer["solid_infill_speed"] is None else float(printer["solid_infill_speed"]) * speed_multiplier
            other.top_solid_infill_speed = None if "top_solid_infill_speed" not in printer or printer["top_solid_infill_speed"] is None else float(printer["top_solid_infill_speed"]) * speed_multiplier
            other.support_speed = None if "support_speed" not in printer or printer["support_speed"] is None else float(printer["support_speed"]) * speed_multiplier
            other.bridge_speed = None if "bridge_speed" not in printer or printer["bridge_speed"] is None else float(printer["bridge_speed"]) * speed_multiplier
            other.gap_fill_speed = None if "gap_fill_speed" not in printer or printer["gap_fill_speed"] is None else float(printer["gap_fill_speed"]) * speed_multiplier
            other.skirt_brim_speed = None if "skirt_brim_speed" not in printer or printer["skirt_brim_speed"] is None else float(printer["skirt_brim_speed"]) * speed_multiplier
            other.above_raft_speed = None if "above_raft_speed" not in printer or printer["above_raft_speed"] is None else float(printer["above_raft_speed"]) * speed_multiplier
            other.ooze_shield_speed = None if "ooze_shield_speed" not in printer or printer["ooze_shield_speed"] is None else float(printer["ooze_shield_speed"]) * speed_multiplier
            other.prime_pillar_speed = None if "prime_pillar_speed" not in printer or printer["prime_pillar_speed"] is None else float(printer["prime_pillar_speed"]) * speed_multiplier
            other.num_slow_layers = None if "num_slow_layers" not in printer or printer["num_slow_layers"] is None else int(printer["num_slow_layers"])
            other.speed_tolerance = 1*speed_multiplier  if "speed_tolerance" not in printer or printer["speed_tolerance"] is None else float(printer["speed_tolerance"]) * speed_multiplier
            other.axis_speed_display_units = speed_units
            printer['slicers']['other'] = other
        elif slicer_type == "simplify-3d":
            ## Simplify 3d settings
            simlify3d = Simplify3dSettings()
            speed_multiplier = 1 if speed_units == "mm-min" else 60.0
            simlify3d.retraction_distance = None if "retract_length" not in printer or printer["retract_length"] is None else float(printer["retract_length"])
            simlify3d.retraction_vertical_lift = None if "z_hop" not in printer or printer["z_hop"] is None else float(printer["z_hop"])
            simlify3d.retraction_speed = None if "retract_speed" not in printer or printer["retract_speed"] is None else float(printer["retract_speed"]) * speed_multiplier
            simlify3d.first_layer_speed_multiplier = None if "first_layer_speed_multiplier" not in printer or printer["first_layer_speed_multiplier"] is None else float(printer["first_layer_speed_multiplier"])
            simlify3d.above_raft_speed_multiplier = None if "above_raft_speed_multiplier" not in printer or printer["above_raft_speed_multiplier"] is None else float(printer["above_raft_speed_multiplier"])
            simlify3d.prime_pillar_speed_multiplier = None if "prime_pillar_speed_multiplier" not in printer or printer["prime_pillar_speed_multiplier"] is None else float(printer["prime_pillar_speed_multiplier"])
            simlify3d.ooze_shield_speed_multiplier = None if "ooze_shield_speed_multiplier" not in printer or printer["ooze_shield_speed_multiplier"] is None else float(printer["ooze_shield_speed_multiplier"])
            simlify3d.default_printing_speed = None if "print_speed" not in printer or printer["print_speed"] is None else float(printer["print_speed"]) * speed_multiplier
            simlify3d.outline_speed_multiplier = None if "outline_speed_multiplier" not in printer or printer["outline_speed_multiplier"] is None else float(printer["outline_speed_multiplier"])
            simlify3d.solid_infill_speed_multiplier = None if "solid_infill_speed_multiplier" not in printer or printer["solid_infill_speed_multiplier"] is None else float(printer["solid_infill_speed_multiplier"])
            simlify3d.support_structure_speed_multiplier = None if "support_structure_speed_multiplier" not in printer or printer["support_structure_speed_multiplier"] is None else float(printer["support_structure_speed_multiplier"])
            simlify3d.x_y_axis_movement_speed = None if "movement_speed" not in printer or printer["movement_speed"] is None else float(printer["movement_speed"]) * speed_multiplier
            simlify3d.z_axis_movement_speed = None if "z_hop_speed" not in printer or printer["z_hop_speed"] is None else float(printer["z_hop_speed"]) * speed_multiplier
            simlify3d.bridging_speed_multiplier = None if "bridging_speed_multiplier" not in printer or printer["bridging_speed_multiplier"] is None else float(printer["bridging_speed_multiplier"])
            simlify3d.axis_speed_display_settings = 'mm-min'
            printer['slicers']['simplify_3d'] = simlify3d
        elif slicer_type == "slic3r-pe":
            # slicer PE settings
            slic3rpe = Slic3rPeSettings()
            speed_multiplier = 1 if speed_units == "mm-sec" else 1.0 / 60.0
            slic3rpe.retract_length = None if "retract_length" not in printer or printer["retract_length"] is None else float(printer["retract_length"])
            slic3rpe.retract_lift = None if "z_hop" not in printer or printer["z_hop"] is None else float(printer["z_hop"])
            slic3rpe.deretract_speed = None if "detract_speed" not in printer or printer["detract_speed"] is None else float(printer["detract_speed"]) * speed_multiplier
            slic3rpe.retract_speed = None if "retract_speed" not in printer or printer["retract_speed"] is None else float(printer["retract_speed"]) * speed_multiplier
            slic3rpe.perimeter_speed = None if "perimeter_speed" not in printer or printer["perimeter_speed"] is None else float(printer["perimeter_speed"]) * speed_multiplier
            slic3rpe.small_perimeter_speed = '' if "small_perimeter_speed_text" not in printer or printer["small_perimeter_speed_text"] is None else unicode(printer["small_perimeter_speed_text"],"utf-8")
            slic3rpe.external_perimeter_speed = '' if "external_perimeter_speed_text" not in printer or printer["external_perimeter_speed_text"] is None else unicode(printer["external_perimeter_speed_text"],"utf-8")
            slic3rpe.infill_speed = None if "infill_speed" not in printer or printer["infill_speed"] is None else float(printer["infill_speed"]) * speed_multiplier
            slic3rpe.solid_infill_speed = '' if "solid_infill_speed_text" not in printer or printer["solid_infill_speed_text"] is None else unicode(printer["solid_infill_speed_text"],"utf-8")
            slic3rpe.top_solid_infill_speed = '' if "top_solid_infill_speed_text" not in printer or printer["top_solid_infill_speed_text"] is None else unicode(printer["top_solid_infill_speed_text"],"utf-8")
            slic3rpe.support_material_speed = None if "support_speed" not in printer or printer["support_speed"] is None else float(printer["support_speed"]) * speed_multiplier
            slic3rpe.bridge_speed = None if "bridge_speed" not in printer or printer["bridge_speed"] is None else float(printer["bridge_speed"]) * speed_multiplier
            slic3rpe.gap_fill_speed = None if "gap_fill_speed" not in printer or printer["gap_fill_speed"] is None else float(printer["gap_fill_speed"]) * speed_multiplier
            slic3rpe.travel_speed = None if "movement_speed" not in printer or printer["movement_speed"] is None else float(printer["movement_speed"]) * speed_multiplier
            slic3rpe.first_layer_speed = '' if "first_layer_speed_text" not in printer or printer["first_layer_speed_text"] is None else unicode(printer["first_layer_speed_text"],"utf-8")
            slic3rpe.axis_speed_display_units = 'mm-sec'
            printer['slicers']['slic3r_pe'] = slic3rpe

        profiles['printers'][printer['guid']] = printer

    for stabilization in settings_dict['stabilizations']:
        stabilization["stabilization_type"] = StabilizationProfile.STABILIZATION_TYPE_REAL_TIME
        profiles['stabilizations'][stabilization['guid']] = stabilization

    for snapshot in settings_dict['snapshots']:

        position_restrictions = snapshot["position_restrictions"]
        snapshot["position_restrictions"] = []
        for restriction in position_restrictions:
            new_restriction = {
                "x2": restriction["X2"],
                "shape": restriction["Shape"],
                "r": restriction["R"],
                "calculate_intersections": restriction["CalculateIntersections"],
                "y": restriction["Y"],
                "x": restriction["X"],
                "y2": restriction["Y2"],
                "type": restriction["Type"],
            }
            snapshot["position_restrictions"].append(new_restriction)

        trigger_on_deretracting_start = snapshot["trigger_on_detracting_start"]
        del snapshot["trigger_on_detracting_start"]
        snapshot["trigger_on_deretracting_start"] = trigger_on_deretracting_start

        trigger_on_deretracting = snapshot["trigger_on_detracting"]
        del snapshot["trigger_on_detracting"]
        snapshot["trigger_on_deretracting"] = trigger_on_deretracting

        trigger_on_deretracted = snapshot["trigger_on_detracted"]
        del snapshot["trigger_on_detracted"]
        snapshot["trigger_on_deretracted"] = trigger_on_deretracted

        feature_trigger_on_deretract = snapshot["feature_trigger_on_detract"]
        del snapshot["feature_trigger_on_detract"]
        snapshot["feature_trigger_on_deretract"] = feature_trigger_on_deretract

        profiles['snapshots'][snapshot['guid']] = snapshot

    current_updated_snapshot_profile = settings_dict["profiles"]['snapshots'][settings_dict['current_rendering_profile_guid']]
    for rendering in settings_dict['renderings']:
        rendering.cleanup_after_render_complete = settings_dict['cleanup_after_render_complete']
        rendering.cleanup_after_render_fail = settings_dict['cleanup_after_render_fail']
        profiles['renderings'][rendering['guid']] = rendering

    for camera in settings_dict['cameras']:
        camera['webcam_settings'] = {
            "white_balance_temperature": camera['white_balance_temperature'],
            "sharpness": camera['sharpness'],
            "focus": camera['focus'],
            "backlight_compensation_enabled": camera['backlight_compensation_enabled'],
            "snapshot_request_template": camera['snapshot_request_template'],
            "stream_template": camera['stream_template'],
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
        del camera['stream_template'],
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
