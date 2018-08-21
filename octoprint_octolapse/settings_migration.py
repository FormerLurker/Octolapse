from distutils.version import LooseVersion
import json
from octoprint_octolapse.settings import OctolapseSettings


def migrate_settings(current_version, settings_dict, log_file_path, default_settings_path):

    if LooseVersion(settings_dict["version"]) <= LooseVersion("0.3.3rc3.dev0"):
        # versions prior to or equal to 0.3.3rc3.dev0 need to have the snapshot profiles reset to the defaults

        # get the default settings
        new_settings = OctolapseSettings(log_file_path, get_default_settings(default_settings_path), current_version)

        # remove the existing renderings
        settings_dict["snapshots"] = []

        for key, snapshot in new_settings.snapshots.items():
            settings_dict["snapshots"].append(snapshot.to_dict())

        # update the version
        settings_dict["version"] = current_version
        # return the dict
        return settings_dict

def get_default_settings(default_settings_path):
    with open(default_settings_path) as defaultSettingsJson:
        data = json.load(defaultSettingsJson)
        # if a settings file does not exist, create one ??
        return data;
