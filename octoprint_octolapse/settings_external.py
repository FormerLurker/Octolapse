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
from distutils.version import LooseVersion
import requests
import uuid
import tempfile
import json
import six

# create the module level logger
from octoprint_octolapse.log import LoggingConfigurator
logging_configurator = LoggingConfigurator()
logger = logging_configurator.get_logger(__name__)


class ExternalSettings(object):

    @staticmethod
    def get_available_profiles(current_octolapse_version, default_profiles_path=None):
        try:
            profiles_dict = ExternalSettings._get_profiles_from_server(current_octolapse_version)

            if default_profiles_path:
                ExternalSettings._save_available_profiles(profiles_dict, default_profiles_path)
                pass
            return profiles_dict["profiles"]
        except ExternalSettingsError as e:
            logger.exception("Could not retrieve the settings file from the server!  Using cached version.")
        profiles_dict = ExternalSettings._load_available_profiles(default_profiles_path)
        if profiles_dict and "profiles" in profiles_dict:
            return profiles_dict["profiles"]

        return None

    @staticmethod
    def _save_available_profiles(profiles_dict, file_path):
        # use a temporary file so that if there is an error creating the json the
        with open(file_path, "w") as f:
            json.dump(profiles_dict, f)

    @staticmethod
    def _load_available_profiles(file_path):
        # use a temporary file so that if there is an error creating the json the
        with open(file_path, "r") as f:
            return json.load(f)

    @staticmethod
    def _get_profiles_from_server(current_octolapse_version):
        # get the best settings version, or raise an error if we can't get one
        settings_version = ExternalSettings._get_best_settings_version(current_octolapse_version)
        # construct the URL for the current version
        url = (
            "https://raw.githubusercontent.com/FormerLurker/Octolapse-Profiles/master/{0}/profiles.json?nonce={1}"
                .format(settings_version, uuid.uuid4().hex)
        )
        r = requests.get(url, timeout=float(5))
        if r.status_code != requests.codes.ok:
            message = (
                "An invalid status code or {0} was returned while getting available profiles."
                    .format(r.status_code)
            )
            raise ExternalSettingsError('invalid-status-code', message)
        if 'content-length' in r.headers and r.headers["content-length"] == 0:
            message = "No profile data was returned."
            raise ExternalSettingsError('no-data', message)
        # if we're here, we've had great success!
        return r.json()

    @staticmethod
    def _get_profile_for_keys(profiles, key_values, profile_type):
        if profile_type in profiles:
            profiles = profiles[profile_type]["values"]
            profile = None
            for key in key_values:
                if key in profiles:
                    profile = profiles[key]
                    if "values" not in profile:
                        return profile
                    else:
                        profiles = profile["values"]
        return None


    @staticmethod
    def check_for_updates(available_profiles, updatable_profiles):
        profiles_to_update = {
            "printer": [],
            "stabilization": [],
            "trigger": [],
            "rendering": [],
            "camera": [],
            "debug": [],

        }
        updates_available = False
        # loop through printer profiles
        if (
            updatable_profiles is not None and
            available_profiles is not None
        ):
            # loop through the updatable profile dicts
            for profile_type, value in six.iteritems(updatable_profiles):
                # loop through the profiles
                for updatable_profile in value:
                    # get the available profile for the updatable profile keys
                    key_values = [x["value"] for x in updatable_profile["key_values"]]
                    available_profile = ExternalSettings._get_profile_for_keys(
                        available_profiles, key_values, profile_type
                    )
                    if available_profile is None:
                        continue
                    # if we have new model and the version is greater than the update version
                    # and we're not suppressing updates for this version, add the profile
                    # to our update list
                    if (
                        updatable_profile["version"] is None or
                        (
                            LooseVersion(available_profile["version"]) > LooseVersion(updatable_profile["version"]) and
                            (
                                updatable_profile["suppress_update_notification_version"] is None or
                                (
                                    LooseVersion(available_profile["version"]) >
                                    LooseVersion(updatable_profile["suppress_update_notification_version"])
                                )
                            )
                        )
                    ):
                        updates_available = True
                        profiles_to_update[profile_type].append(updatable_profile)

        if not updates_available:
            return False
        return profiles_to_update

    @staticmethod
    def get_profile(current_octolapse_version, profile_type, key_values):
        # get the best settings version, or raise an error if we can't get one
        settings_version = ExternalSettings._get_best_settings_version(current_octolapse_version)
        # construct the URL for the current version
        keys = [x["value"] for x in key_values]
        url = ExternalSettings._get_url_for_profile(settings_version, profile_type, keys)
        r = requests.get(url, timeout=float(5))
        if r.status_code != requests.codes.ok:
            message = (
                "An invalid status code or {0} was returned while getting available profiles."
                .format(r.status_code)
            )
            raise ExternalSettingsError('invalid-status-code', message)
        if 'content-length' in r.headers and r.headers["content-length"] == 0:
            message = "No profile data was returned."
            raise ExternalSettingsError('no-data', message)
        # if we're here, we've had great success!
        return r.json()

    @staticmethod
    def _get_url_for_profile(settings_version, profile_type, key_values):
        # build up keys string
        keys_string = "/".join(key_values)
        return(
            "https://raw.githubusercontent.com/FormerLurker/Octolapse-Profiles/master/{0}/{1}/"
            "{2}/profile.json?nonce={3} ".format(settings_version, profile_type.lower(), keys_string, uuid.uuid4().hex)
        )

    @staticmethod
    def _get_best_settings_version(current_version):
        # load the available versions
        versions = ExternalSettings._get_versions()["versions"]
        versions.sort(key=LooseVersion)
        settings_version = None
        for version in versions:
            if LooseVersion(version) >= LooseVersion(current_version):
                settings_version = version
                break

        if settings_version is None:
            message = "No available settings were found for the current version ((0)) of Octolapse.  This is probably " \
                      "a development or alpha version.  Try back soon!".format(version)
            raise ExternalSettingsError('no-version-found', message)
        return settings_version

    @staticmethod
    def _check_profile_type(profile_type):
        if profile_type not in [
            'printer'
        ]:
            message = "The requested profile type {0} does not exist on the server.!".format(profile_type)
            raise ExternalSettingsError('no-version-found', message)

    @staticmethod
    def _get_versions():
        # load the available versions
        r = requests.get(
            (
                "https://raw.githubusercontent.com/FormerLurker/Octolapse-Profiles/master/versions.json?nonce={0}"
                .format(uuid.uuid4().hex)
             ),
            timeout=float(5)
        )
        if r.status_code != requests.codes.ok:
            message = (
                "An invalid status code or {0} was returned while getting available profile versions."
                .format(r.status_code)
            )
            raise ExternalSettingsError('invalid-status-code', message)
        if 'content-length' in r.headers and r.headers["content-length"] == 0:
            message = "No Octolapse version data was returned while requesting profiles"
            raise ExternalSettingsError('no-data', message)
        # if we're here, we've had great success!
        return r.json()


class ExternalSettingsError(Exception):
    def __init__(self, error_type, message, cause=None):
        super(ExternalSettingsError, self).__init__()
        self.error_type = error_type
        self.cause = cause if cause is not None else None
        self.message = message

    def __str__(self):
        if self.cause is None:
            return "{0}: {1}".format(self.error_type, self.message)
        return "{0}: {1} - Inner Exception: {2}".format(self.error_type, self.message, "{}".format(self.cause))
