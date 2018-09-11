from distutils.version import LooseVersion
import json
from octoprint_octolapse.settings import OctolapseSettings


def migrate_settings(current_version, settings_dict, log_file_path, default_settings_path):

    if LooseVersion(settings_dict["version"]) <= LooseVersion("0.3.3rc3.dev0"):
        return migrate_pre_0_3_3_rc3_dev(current_version, settings_dict, log_file_path, default_settings_path)

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


def get_default_settings(default_settings_path):
    with open(default_settings_path) as defaultSettingsJson:
        data = json.load(defaultSettingsJson)
        # if a settings file does not exist, create one ??
        return data;
