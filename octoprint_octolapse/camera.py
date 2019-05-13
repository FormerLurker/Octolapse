# coding=utf-8
##################################################################################
# Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
# Copyright (C) 2017  Brad Hochgesang
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
import json
import octoprint_octolapse.utility as utility
from threading import Thread
# This file is subject to the terms and conditions defined in
# file called 'LICENSE', which is part of this source code package.
import requests
# Todo:  Do we need to add this to setup.py?
from requests.auth import HTTPBasicAuth
from requests.exceptions import SSLError
from octoprint_octolapse.settings import CameraProfile, MjpegStreamerStaticSettings

# create the module level logger
from octoprint_octolapse.log import LoggingConfigurator
logging_configurator = LoggingConfigurator()
logger = logging_configurator.get_logger(__name__)


def format_request_template(camera_address, template, value):
    return template.format(camera_address=camera_address, value=value)


def test_web_camera(camera_profile, timeout_seconds=2, is_before_print_test=False):
    url = format_request_template(
        camera_profile.webcam_settings.address, camera_profile.webcam_settings.snapshot_request_template, "")
    try:
        if len(camera_profile.webcam_settings.username) > 0:
            r = requests.get(url, auth=HTTPBasicAuth(camera_profile.webcam_settings.username, camera_profile.webcam_settings.password),
                             verify=not camera_profile.webcam_settings.ignore_ssl_error, timeout=float(timeout_seconds))
        else:
            r = requests.get(
                url, verify=not camera_profile.webcam_settings.ignore_ssl_error, timeout=float(timeout_seconds))
        if r.status_code == requests.codes.ok:
            if 'content-length' in r.headers and r.headers["content-length"] == 0:
                message = "The request contained no data for the '{0}' camera profile.".format(camera_profile.name)
                logger.error(message)
                raise CameraError('request-contained-no-data', message)
            elif "image/jpeg" not in r.headers["content-type"].lower():
                message = (
                    "The returned daata was not an image for the '{0}' camera profile.".format(camera_profile.name)
                )
                logger.error(message)
                raise CameraError('not-an-image',message)
            elif not is_before_print_test or camera_profile.apply_settings_before_print:
                test_web_camera_image_preferences(camera_profile, timeout_seconds)
        else:
            message = (
                "An invalid status code or {0} was returned from the '{1}' camera profile."
                .format(r.status_code, camera_profile.name)
            )
            logger.error(message)
            raise CameraError('invalid-status-code', message)

    except SSLError as e:
        message = "An SSL occurred while testing the '{0}' camera profile.".format(camera_profile.name)
        logger.exception(message)
        raise CameraError('ssl-error', message, cause=e)
    except requests.ConnectionError as e:
        message = (
            "Unable to connect to the provided snapshot URL of {0} for the '{1}' camera profile."
            .format(url, camera_profile.name)
        )
        logger.exception(message)
        raise CameraError('connection-error', message, cause=e)

    except requests.ConnectTimeout as e:
        message = "The connection to {0} timed out for the '{1}' camera profile.".format(url, camera_profile.name)
        logger.exception(message)
        raise CameraError('connection-timeout', message, cause=e)

    except requests.ReadTimeout as e:
        message = (
            "A read timeout occurred while connecting to {0} for the '{1}' camera profile."
            .format(url, camera_profile.name)
        )
        logger.exception(message)
        raise CameraError('read-timeout', message, cause=e)

    except requests.exceptions.InvalidSchema as e:
        message = (
            "An invalid schema was detected while connecting to {0} for the '{1}' camera profile."
            .format(url, camera_profile.name)
        )
        logger.exception(message)
        raise CameraError('invalid-schema', message, cause=e)
    except requests.exceptions.MissingSchema as e:
        message = (
            "A missing schema error was detected while connecting to {0} for the '{1}' camera profile."
            .format(url, camera_profile.name)
        )
        logger.exception(message)
        raise CameraError('missing-schema', message, cause=e)


def test_web_camera_image_preferences(camera_profile, timeout_seconds=2):
    assert (isinstance(camera_profile, CameraProfile))
    # first see what kind of server we have
    url = format_request_template(
        camera_profile.webcam_settings.address, camera_profile.webcam_settings.snapshot_request_template, "")
    try:
        if len(camera_profile.webcam_settings.username) > 0:
            r = requests.get(url, auth=HTTPBasicAuth(camera_profile.webcam_settings.username, camera_profile.webcam_settings.password),
                             verify=not camera_profile.webcam_settings.ignore_ssl_error, timeout=float(timeout_seconds))
        else:
            r = requests.get(url, verify=not camera_profile.webcam_settings.ignore_ssl_error, timeout=float(timeout_seconds))

        webcam_server_type = get_webcam_server_type_from_request(r)

    except SSLError as e:
        message = (
            "An SSL occurred while testing the '{0}' camera profile.  Look for the 'Camera Profile->Advanced Camera "
            "Opotions->Security->Ignore SSL Errors setting for a possible solution.".format(camera_profile.name)
        )
        logger.exception(message)
        raise CameraError('ssl-error', message, cause=e)
    except requests.ConnectionError as e:
        message = "Unable to connect to '{0}' for the '{1}' camera profile.  Please double check your 'Base Address' " \
                  "and 'Snapshot Address Template' settings.".format(url, camera_profile.name)
        logger.exception(message)
        raise CameraError('connection-error', message, cause=e)
    except Exception as e:
        message = "'An unexpected exception occured while testing the '{0}' camera profile.".format(camera_profile.name)
        logger.exception(message)
        raise CameraError('unknown-exception', message, cause=e)

    if webcam_server_type == "MJPG-Streamer":
        test_mjpgstreamer_control(camera_profile, timeout_seconds)
    elif webcam_server_type == "yawcam":
        message = "You cannot use Yawcam with custom image preferences enabled.  Please disable custom image " \
                  "prefences for the  '{0}' camera profile. ".format(webcam_server_type, camera_profile.name)
        logger.error(message)
        raise CameraError('unsupported-server-type', message)
    else:
        message = "An unknown webcam server type '{0}' is being used for the '{1}' camera profile.  Currently only " \
                  "MJPEGStreamer is supported.  Unable to apply custom image preferences.".format(webcam_server_type,
                                                                                                  camera_profile.name)
        logger.error(message)
        raise CameraError('unknown-server-type', message)


def get_webcam_server_type_from_request(r):
    webcam_server_type = "unknown"
    if "server" in r.headers:
        if r.headers["server"].startswith('MJPG-Streamer'):
            webcam_server_type = "MJPG-Streamer"
        elif r.headers["server"].startswith('yawcam'):
            webcam_server_type = "yawcam"
        else:
            webcam_server_type = r.headers["server"]

    return webcam_server_type


def test_mjpgstreamer_control(camera_profile, timeout_seconds=2):
    url = camera_profile.webcam_settings.address + "?action=command&id=-1"
    try:
        if len(camera_profile.webcam_settings.username) > 0:
            r = requests.get(url, auth=HTTPBasicAuth(camera_profile.webcam_settings.username, camera_profile.webcam_settings.password),
                             verify=not camera_profile.webcam_settings.ignore_ssl_error, timeout=float(timeout_seconds))
        else:
            r = requests.get(
                url, verify=not camera_profile.webcam_settings.ignore_ssl_error, timeout=float(timeout_seconds))

        webcam_server_type = get_webcam_server_type_from_request(r)
        if webcam_server_type != "MJPG-Streamer":
            message = "An unknown webcam server type '{0}' is being used for the '{1}' camera profile.  Currently " \
                      "only MJPEGStreamer is supported.  Unable to apply custom image preferences.".format(
                        webcam_server_type, camera_profile.name)
            logger.error(message)
            raise CameraError('unknown-server-type', message)
        if r.status_code == 501:
            message = "The server denied access to the MJPG-Streamer control.htm for the '{0}' camera profile.  <a " \
                      "href=\"https://github.com/FormerLurker/Octolapse/wiki/Troubleshooting#why-cant-i-change" \
                      "-contrast-zoom-focus-etc\" target = \"_blank\">Please see this link to correct this " \
                      "error.</a>, or disable the 'Enable And Apply Preferences at Startup' and " \
                      "'Enable And Apply Preferences Before Print' options.".format(camera_profile.name)
            logger.error(message)
            raise CameraError("mjpegstreamer-control-error", message)
        if r.status_code != requests.codes.ok:
            message = "Status code received ({0}) was not OK.  Double check your webcam 'Base Addresss' address and " \
                      "your 'Snapshot Address Template'.  Or, disable the 'Enable And Apply Preferences at Startup' " \
                      "and 'Enable And Apply Preferences Before Print' options for the {1} camera " \
                      "profile and try again.".format(r.status_code, camera_profile.name)
            logger.error(message)
            raise CameraError('webcam_settings_apply_error', message)
    except SSLError as e:
        message = (
            "An SSL error was raised while testing custom image preferences for the '{0}' camera profile."
            .format(camera_profile.name)
        )
        logger.error(message)
        raise CameraError('webcam_settings_ssl_error', message, cause=e)
    except CameraError as e:
        # Don't log exceptions that we raised.  They will be logged (hopefully) by the raiser.
        # re raise the error
        raise e
    except Exception as e:
        message = (
            "An unexpected error was raised while testing custom image preferences for the '{0}' camera profile."
            .format(camera_profile.name)
        )
        logger.exception(message)
        raise CameraError('webcam_settings_apply_error', message, cause=e)


def apply_camera_image_preference(
    request, address, username, password, ignore_ssl_errors, timeout_seconds, camera_name
):
    template = request['template']
    value = request['value']
    setting_name = request['name']
    url = format_request_template(address, template, value)
    try:
        if len(username) > 0:
            r = requests.get(url, auth=HTTPBasicAuth(username, password),
                             verify=not ignore_ssl_errors, timeout=float(timeout_seconds))
        else:
            r = requests.get(url, verify=not ignore_ssl_errors,
                             timeout=float(timeout_seconds))

        webcam_server_type = get_webcam_server_type_from_request(r)
        if webcam_server_type != "MJPG-Streamer":
            message = "An unknown webcam server '{0}' was detected while applying the {1} setting to the '{2}' camera " \
                      "profile.  Currently only MJPEGStreamer is supported.  Unable to apply custom image " \
                      "preferences. ".format(webcam_server_type, setting_name, camera_name)
            logger.error(message)
            raise CameraError('unknown-server-type', message)
        if r.status_code == 501:
            message = "Access was denied to the MJPG-Streamer control.html while applying the {0} setting to the '{" \
                      "1}' camera profile.  <a " \
                      "href=\"https://github.com/FormerLurker/Octolapse/wiki/Troubleshooting#why-cant-i-change" \
                      "-contrast-zoom-focus-etc\" target = \"_blank\">Please see this link to correct this " \
                      "error.</a>, disable the 'Enable And Apply Preferences at Startup' " \
                      "and 'Enable And Apply Preferences Before Print' options '.".format(setting_name, camera_name)
            logger.error(message)
            raise CameraError("mjpegstreamer-control-error", message)
        if r.status_code != requests.codes.ok:
            message = "Recived a status code of ({0}) while applying the {1} settings to the {2} camera profile.  " \
                      "Double check your 'Base Address' and 'Snapshot Address Template' within your camera profile " \
                      "settings.  Or disable 'Custom Image Preferences' for this profile and try again.".format(
                        r.status_code, setting_name, camera_name)
            logger.error(message)
            raise CameraError('webcam_settings_apply_error', message)
    except CameraError as e:
        raise e
    except SSLError as e:
        message = (
            "An SSL error was raised while applying the {0} setting to the '{1}' camera profile."
            .format(setting_name, camera_name)
        )
        logger.error(message)
        raise CameraError('ssl_error', message, cause=e)
    except Exception as e:
        message = (
            "An unexpected error was raised while applying the {0} setting to the '{1}' camera profile."
            .format(setting_name, camera_name)
        )
        logger.error(message)
        raise CameraError('webcam_settings_apply_error', message, cause=e)


def get_mjpegstreamer_input_json(
    request, address, username, password, ignore_ssl_errors, timeout_seconds, camera_name
):
    template = request['template']
    value = request['value']
    setting_name = request['name']
    url = format_request_template(address, template, value)
    try:
        if len(username) > 0:
            r = requests.get(url, auth=HTTPBasicAuth(username, password),
                             verify=not ignore_ssl_errors, timeout=float(timeout_seconds))
        else:
            r = requests.get(url, verify=not ignore_ssl_errors,
                             timeout=float(timeout_seconds))

        if r.status_code == 501:
            message = "Access was denied to the MJPG-Streamer control.html while applying the {0} setting to the '{" \
                      "1}' camera profile.  <a " \
                      "href=\"https://github.com/FormerLurker/Octolapse/wiki/Troubleshooting#why-cant-i-change" \
                      "-contrast-zoom-focus-etc\" target = \"_blank\">Please see this link to correct this " \
                      "error.</a>, or disable the 'Enable And Apply Preferences at Startup' " \
                      "and 'Enable And Apply Preferences Before Print' options.".format(setting_name, camera_name)
            logger.error(message)
            raise CameraError("mjpegstreamer-control-error", message)
        if r.status_code != requests.codes.ok:
            message = (
                "Recived a status code of ({0}) while applying the {1} settings to the {2} camera profile.  Double "
                "check your 'Base Address' and 'Snapshot Address Template' within your camera profile settings.  Or "
                "disable the 'Enable And Apply Preferences at Startup' and 'Enable And Apply Preferences Before Print"  
                "'options  for this profile and try again."
                .format(r.status_code, setting_name, camera_name)
            )
            logger.error(message)
            raise CameraError('webcam_settings_apply_error', message)

        data = json.loads(r.text)
        return data
    except SSLError as e:
        message = (
            "An SSL error was raised while applying the {0} setting to the '{1}' camera profile."
            .format(setting_name, camera_name)
        )
        logger.exception(message)
        raise CameraError('ssl_error', message, cause=e)
    except Exception as e:
        message = (
            "An unexpected error was raised while applying the {0} setting to the '{1}' camera profile."
            .format(setting_name, camera_name)
        )
        logger.exception(message)
        raise CameraError('webcam_settings_apply_error', message, cause=e)


def get_mjpegstreamer_image_preferences_requests(camera_profile):
    camera_settings_requests = [
        {
            'template': camera_profile.webcam_settings.mjpegstreamer.brightness_request_template,
            'value': camera_profile.webcam_settings.brightness,
            'name': 'brightness'
        },
        {
            'template': camera_profile.webcam_settings.mjpegstreamer.contrast_request_template,
            'value': camera_profile.webcam_settings.contrast,
            'name': 'contrast'
        },
        {
            'template': camera_profile.webcam_settings.mjpegstreamer.saturation_request_template,
            'value': camera_profile.webcam_settings.saturation,
            'name': 'saturation'
        },
        {
            'template': camera_profile.webcam_settings.mjpegstreamer.white_balance_auto_request_template,
            'value': 1 if camera_profile.webcam_settings.white_balance_auto else 0,
            'name': 'auto white balance'
        },
        {
            'template': camera_profile.webcam_settings.mjpegstreamer.powerline_frequency_request_template,
            'value': camera_profile.webcam_settings.powerline_frequency,
            'name': 'powerline frequency'
        },
        {
            'template': camera_profile.webcam_settings.mjpegstreamer.sharpness_request_template,
            'value': camera_profile.webcam_settings.sharpness,
            'name': 'sharpness'
        },
        {
            'template': camera_profile.webcam_settings.mjpegstreamer.backlight_compensation_enabled_request_template,
            'value': 1 if camera_profile.webcam_settings.backlight_compensation_enabled else 0,
            'name': 'set backlight compensation enabled'
        },
        {
            'template': camera_profile.webcam_settings.mjpegstreamer.exposure_type_request_template,
            'value': camera_profile.webcam_settings.exposure_type,
            'name': 'exposure type'
        },
        {
            'template': camera_profile.webcam_settings.mjpegstreamer.pan_request_template,
            'value': camera_profile.webcam_settings.pan,
            'name': 'pan'
        },
        {
            'template': camera_profile.webcam_settings.mjpegstreamer.tilt_request_template,
            'value': camera_profile.webcam_settings.tilt,
            'name': 'tilt'
        },
        {
            'template': camera_profile.webcam_settings.mjpegstreamer.autofocus_enabled_request_template,
            'value': 1 if camera_profile.webcam_settings.autofocus_enabled else 0,
            'name': 'set autofocus enabled'
        },
        {
            'template': camera_profile.webcam_settings.mjpegstreamer.zoom_request_template,
            'value': camera_profile.webcam_settings.zoom,
            'name': 'zoom'
        },
        {
            'template': camera_profile.webcam_settings.mjpegstreamer.led1_mode_request_template,
            'value': camera_profile.webcam_settings.led1_mode,
            'name': 'led 1 mode'
        },
        {
            'template': camera_profile.webcam_settings.mjpegstreamer.led1_frequency_request_template,
            'value': camera_profile.webcam_settings.led1_frequency,
            'name': 'led 1 frequency'
        },
        {
            'template': camera_profile.webcam_settings.mjpegstreamer.jpeg_quality_request_template,
            'value': camera_profile.webcam_settings.jpeg_quality,
            'name': 'jpeg quality'
        }
    ]

    if not camera_profile.webcam_settings.white_balance_auto:
        camera_settings_requests.append({
            'template': camera_profile.webcam_settings.mjpegstreamer.white_balance_temperature_request_template,
            'value': camera_profile.webcam_settings.white_balance_temperature,
            'name': 'white balance temperature'
        })

    # These settings only work when the exposure type is set to manual, I think.
    if camera_profile.webcam_settings.exposure_type == 1:
        camera_settings_requests.extend([
            {
                'template': camera_profile.webcam_settings.mjpegstreamer.exposure_request_template,
                'value': camera_profile.webcam_settings.exposure,
                'name': 'exposure'
            },
            {
                'template': camera_profile.webcam_settings.mjpegstreamer.exposure_auto_priority_enabled_request_template,
                'value': 1 if camera_profile.webcam_settings.exposure_auto_priority_enabled else 0,
                'name': 'set auto priority enabled'
            },
            {
                'template': camera_profile.webcam_settings.mjpegstreamer.gain_request_template,
                'value': camera_profile.webcam_settings.gain,
                'name': 'gain'
            }
        ])

    if not camera_profile.webcam_settings.autofocus_enabled:
        camera_settings_requests.append({
            'template': camera_profile.webcam_settings.mjpegstreamer.focus_request_template,
            'value': camera_profile.webcam_settings.focus,
            'name': 'focus'
        })

    return camera_settings_requests


def get_mjpegstreamer_image_preferences_request(setting_name, setting_value):

    templates = MjpegStreamerStaticSettings()

    camera_settings_request = None
    if setting_name == 'brightness':
        camera_settings_request = {
            'template': templates.brightness_request_template,
            'value': setting_value,
            'name': 'brightness'
        }
    elif setting_name == 'contrast':
        camera_settings_request = {
            'template': templates.contrast_request_template,
            'value': setting_value,
            'name': 'contrast'
        }
    elif setting_name == 'saturation':
        camera_settings_request = {
            'template': templates.saturation_request_template,
            'value': setting_value,
            'name': 'saturation'
        }
    elif setting_name == 'white_balance_auto':
        camera_settings_request = {
            'template': templates.white_balance_auto_request_template,
            'value': 1 if setting_value else 0,
            'name': 'auto white balance'
        }
    elif setting_name == 'powerline_frequency':
        camera_settings_request = {
            'template': templates.powerline_frequency_request_template,
            'value': setting_value,
            'name': 'powerline frequency'
        }
    elif setting_name == 'sharpness':
        camera_settings_request = {
            'template': templates.sharpness_request_template,
            'value': setting_value,
            'name': 'sharpness'
        }
    elif setting_name == 'backlight_compensation_enabled':
        camera_settings_request = {
            'template': templates.backlight_compensation_enabled_request_template,
            'value': 1 if setting_value else 0,
            'name': 'set backlight compensation enabled'
        }
    elif setting_name == 'exposure_type':
        camera_settings_request = {
            'template': templates.exposure_type_request_template,
            'value': setting_value,
            'name': 'exposure type'
        }
    elif setting_name == 'pan':
        camera_settings_request = {
            'template': templates.pan_request_template,
            'value': setting_value,
            'name': 'pan'
        }
    elif setting_name == 'tilt':
        camera_settings_request = {
            'template': templates.tilt_request_template,
            'value': setting_value,
            'name': 'tilt'
        }
    elif setting_name == 'autofocus_enabled':
        camera_settings_request = {
            'template': templates.autofocus_enabled_request_template,
            'value': 1 if setting_value else 0,
            'name': 'set autofocus enabled'
        }
    elif setting_name == 'zoom':
        camera_settings_request = {
            'template': templates.zoom_request_template,
            'value': setting_value,
            'name': 'zoom'
        }
    elif setting_name == 'led1_mode':
        camera_settings_request = {
            'template': templates.led1_mode_request_template,
            'value': setting_value,
            'name': 'led 1 mode'
        }
    elif setting_name == 'led1_frequency':
        camera_settings_request = {
            'template': templates.led1_frequency_request_template,
            'value': setting_value,
            'name': 'led 1 frequency'
        }
    elif setting_name == 'jpeg_quality':
        camera_settings_request = {
            'template': templates.jpeg_quality_request_template,
            'value': setting_value,
            'name': 'jpeg quality'
        }
    elif setting_name == 'white_balance_temperature':
        camera_settings_request = {
            'template': templates.white_balance_temperature_request_template,
            'value': setting_value,
            'name': 'white balance temperature'
        }
    elif setting_name == 'exposure':
        camera_settings_request = {
                'template': templates.exposure_request_template,
                'value': setting_value,
                'name': 'exposure'
            }
    elif setting_name == 'exposure_auto_priority_enabled':
        camera_settings_request = {
                'template': templates.exposure_auto_priority_enabled_request_template,
                'value': 1 if setting_value else 0,
                'name': 'set auto priority enabled'
            }
    elif setting_name == 'gain':
        camera_settings_request = {
            'template': templates.gain_request_template,
            'value': setting_value,
            'name': 'gain'
        }
    elif setting_name == 'focus':
        camera_settings_request = {
            'template': templates.focus_request_template,
            'value': setting_value,
            'name': 'focus'
        }

    return camera_settings_request


class CameraControl(object):
    def __init__(self, cameras):
        self.Cameras = cameras
        self.errors = []

    @classmethod
    def apply_webcam_setting(
        cls, server_type, setting_name, setting_value, camera_profile=None, name=None, address=None, username=None, password=None,
        ignore_ssl_error=None, timeout_ms=None
    ):
        request = None
        if server_type == 'MJPG-Streamer':
            request = get_mjpegstreamer_image_preferences_request(setting_name, setting_value)
        else:
            message = "Cannot apply camera settings to the server type:{0}".format(server_type)
            logger.error(message)
            raise CameraError('server_type_not_found', message)

        if request is None:
            message = "Could not find the setting:{0}".format(setting_name)
            logger.error(message)
            raise CameraError('setting_name_not_found', message)

        thread = CameraSettingWebRequestThread(
            request, camera=camera_profile, name=name, address=address, username=username, password=password,
            ignore_ssl_error=ignore_ssl_error, timeout_ms=timeout_ms

        )
        thread.start()

        success, camera_name, error = thread.join()

        return success, error

    @classmethod
    def apply_webcam_settings(cls, camera_profile=None, name=None, address=None, username=None, password=None,
        ignore_ssl_error=None, timeout_ms=None, defaults=None):
        errors = []
        has_started_thread = False
        if camera_profile != None:
            logger.info("Applying all webcam image settings to the {} camera.", camera_profile.name)
            threads = cls._get_web_request_threads(True, camera_profiles=[camera_profile])
        else:
            threads = cls._get_web_request_threads(
                True, name=name, address=address, username=username, password=password,
                ignore_ssl_error=ignore_ssl_error, timeout_ms=timeout_ms, defaults=defaults
            )
            if len(threads) > 0:
                logger.info("Applying all webcam image settings.")
        for thread in threads:
            if not has_started_thread:
                has_started_thread = True
            thread.start()

        for thread in threads:
            success, camera_name, error = thread.join()
            if not success:
                errors.append(error)

        return len(errors) == 0, " - ".join(errors)

    def apply_settings(self, force, settings_type):

        errors = []
        threads = []
        has_webcam_settings = False
        has_script_settings = False

        if settings_type is None or settings_type == 'web-request':
            webcam_threads = self._get_web_request_threads( force, camera_profiles=self.Cameras)
            if len(webcam_threads) > 0:
                has_webcam_settings = True
            threads += webcam_threads

        if settings_type is None or settings_type == 'script':
            script_threads = self._get_script_threads(force, self.Cameras)
            if len(script_threads) > 0:
                has_script_settings = True
            threads += script_threads

        if has_webcam_settings and not has_script_settings:
            logger.info("Applying all webcam image settings.")
        elif not has_webcam_settings and has_script_settings:
            logger.info("Running all 'Before Print Start' scripts.")
        elif has_webcam_settings and has_script_settings:
            logger.info("Running all webcam image settings and running all 'Before Print Start' scripts.")

        for thread in threads:
            thread.start()

        for thread in threads:
            success, camera_name, error = thread.join()
            if not success:
                # No need to log here, the error should be logged within the thread.
                errors.append(error)

        success = len(errors) == 0

        if success:
            if has_webcam_settings and not has_script_settings:
                logger.info("All webcam image settings applied successfully.")
            elif not has_webcam_settings and has_script_settings:
                logger.info("All 'Before Print Start' executed successfully.")
            elif has_webcam_settings and has_script_settings:
                logger.info("All webcam image settings applied and 'Before Print Start' executed successfully.")

        return success, errors

    @classmethod
    def _get_web_request_threads(
        cls, force, camera_profiles=None, name=None, address=None, username=None, password=None, ignore_ssl_error=None,
        timeout_ms=None, defaults=None
    ):
        threads = []
        if camera_profiles is not None:
            for current_camera in camera_profiles:
                if current_camera.camera_type != 'webcam':
                    continue
                if not force and (not current_camera.enabled or not current_camera.apply_settings_before_print):
                    continue
                camera_settings_requests = get_mjpegstreamer_image_preferences_requests(current_camera)

                for request in camera_settings_requests:
                    threads.append(CameraSettingWebRequestThread(request, camera=current_camera))
        else:
            for key, value in defaults.items():
                request = get_mjpegstreamer_image_preferences_request(key, value)
                threads.append(
                    CameraSettingWebRequestThread(
                        request, name=name, address=address, username=username, password=password,
                        ignore_ssl_error=ignore_ssl_error, timeout_ms=None
                    )
                )
        return threads

    @classmethod
    def _get_script_threads(cls, force, cameras):
        threads = []
        for current_camera in cameras:
            if not force and (not current_camera.enabled or not current_camera.on_print_start_script):
                continue
            threads.append(CameraSettingScriptThread(current_camera))
        return threads

    @classmethod
    def get_settings_from_camera(
        cls, server_type, settings_type, camera_profile=None, name=None, address=None, username=None, password=None,
        ignore_ssl_error=None, timeout_ms=None
    ):
        if server_type == 'MJPG-Streamer':
            templates = MjpegStreamerStaticSettings()
            file_name = 'input_0.json'
            request = {
                'template': templates.file_request_template,
                'value': file_name,
                'name': 'input_0.json'
            }
            if camera_profile is not None:
                data = get_mjpegstreamer_input_json(
                    request, camera_profile.webcam_settings.address, camera_profile.webcam_settings.username,
                    camera_profile.webcam_settings.password, camera_profile.webcam_settings.ignore_ssl_error,
                    camera_profile.timeout_ms / 1000.0, camera_profile.name
                )
            else:
                data = get_mjpegstreamer_input_json(
                    request, address, username, password, ignore_ssl_error, timeout_ms / 1000.0, name
                )

            defaults_lookup = {
                'Brightness': {'name': 'brightness', 'value': None},
                'Contrast': {'name': 'contrast', 'value': None},
                'Saturation': {'name': 'saturation', 'value': None},
                'White Balance Temperature, Auto': {'name': 'white_balance_auto', 'value': None},
                'Gain': {'name': 'gain', 'value': None},
                'Power Line Frequency': {'name': 'powerline_frequency', 'value':None},
                'White Balance Temperature': {'name': 'white_balance_temperature', 'value': None},
                'Sharpness': {'name': 'sharpness', 'value': None},
                'Backlight Compensation': {'name': 'backlight_compensation_enabled', 'value': None},
                'Exposure, Auto': {'name': 'exposure_type', 'value': None},
                'Exposure (Absolute)': {'name': 'exposure', 'value': None},
                'Exposure, Auto Priority': {'name': 'exposure_auto_priority_enabled', 'value': None},
                'Pan (Absolute)': {'name': 'pan', 'value': None},
                'Tilt (Absolute)': {'name': 'tilt', 'value': None},
                'Focus (absolute)': {'name': 'autofocus_enabled', 'value': None},
                'Focus, Auto': {'name': 'focus', 'value': None},
                'Zoom, Absolute': {'name': 'zoom', 'value': None},
                'JPEG quality': {'name': 'led1_mode', 'value': None},
                'led1_frequency': {'name': 'led1_frequency', 'value': None},
                'jpeg_quality': {'name': 'jpeg_quality', 'value': None}
            }
            
            for item in data["controls"]:
                key = item["name"]
                if key in defaults_lookup:
                    lookup_item = defaults_lookup[key]
                    if settings_type == 'defaults':
                        lookup_item["value"] = int(item["default"])
                    elif settings_type == 'current_values':
                        lookup_item["value"] = int(item["value"])
                    else:
                        message = "Unable to find the setting type {0}".format(settings_type)
                        logger.error(message)
                        raise CameraError("unknown_webcam_setting_type", message)
                    min_val = int(item["min"])
                    max_val = int(item["max"])
                    if min_val > lookup_item["value"] or lookup_item["value"] > max_val:

                        if lookup_item["name"] == "zoom" and  min_val <= 100 <= max_val:
                            # set zoom to 100% by default if possible
                            lookup_item["value"] = 100
                        else:
                            step = int(item["step"])
                            range = max_val - min_val
                            steps = round(range/2.0/step)
                            lookup_item["value"] = min_val + (steps * step)

            return {value['name']: value['value'] for key, value in defaults_lookup.items()}


class CameraSettingScriptThread(Thread):
    def __init__(self, camera):
        super(CameraSettingScriptThread, self).__init__()
        self.Camera = camera
        self.camera_name = camera.name
        self.error = None

    def run(self):
        try:
            script = self.Camera.on_print_start_script.strip()
            logger.info(
                "Executing the 'Before Print Starts' script at %s for the '%s' camera.", script, self.camera_name
            )
            if not script:
                message = "The Camera Initialization script is empty"
                logger.error(message)
                raise CameraError('no_camera_script_path', message)
            try:
                script_args = [
                    script,
                    self.Camera.name
                ]
                cmd = utility.POpenWithTimeout()
                return_code = cmd.run(script_args, None)
                console_output = cmd.stdout
                error_message = cmd.stderr
            except utility.POpenWithTimeout.ProcessError as e:
                message = "An OS Error error occurred while executing the custom camera initialization script"
                logger.exception(message)
                raise CameraError('camera_initialization_error', message, cause=e)

            if error_message is not None:
                if error_message.endswith("\r\n"):
                    error_message = error_message[:-2]
            if not return_code == 0:
                if error_message is not None:
                    error_message = "The custom camera initialization script failed with the following error message: {0}" \
                        .format(error_message)
                else:
                    error_message = (
                        "The custom camera initialization script returned {0},"
                        " which indicates an error.".format(return_code)
                    )
                logger.exception(error_message)
            elif error_message is not None:
                logger.warn(
                    "The console returned an error while running the script at %s for the '%s' camera.  Details:%s",
                    script, self.camera_name, error_message
                )
            else:
                logger.info(
                    "The 'Before Print Starts' script for the %s camera completed successfully.", self.camera_name
                )
                raise CameraError('camera_initialization_error', error_message)
        except CameraError as e:
            self.error = e

    def join(self, timeout=None):
        super(CameraSettingScriptThread, self).join(timeout=timeout)
        return self.error is None, self.Camera.name, self.error.message


class CameraSettingWebRequestThread(Thread):

    def __init__(
        self, camera_settings_request, camera=None, name=None, address=None, username=None, password=None,
        ignore_ssl_error=None, timeout_ms=None
    ):
        super(CameraSettingWebRequestThread, self).__init__()

        self.request = camera_settings_request
        if camera is not None:
            camera = camera
            self.camera_name = camera.name
            self.address = camera.webcam_settings.address
            self.username = camera.webcam_settings.username
            self.password = camera.webcam_settings.password
            self.ignore_ssl_error = camera.webcam_settings.ignore_ssl_error
            self.timeout_seconds = camera.timeout_ms / 1000.0
        else:
            self.camera_name = name
            self.address = address
            self.username = username
            self.password = password
            self.ignore_ssl_error = ignore_ssl_error
            self.timeout_seconds = timeout_ms / 1000.0

        self.error = None
        self._thread = None

    def run(self):
        try:
            logger.debug(
                "Setting %s to %s for the '%s' webcam", self.request["name"], self.request["value"], self.camera_name
            )
            apply_camera_image_preference(
                self.request, self.address, self.username, self.password, self.ignore_ssl_error, self.timeout_seconds,
                self.camera_name
            )
            logger.debug(
                "The %s setting was applied successfully to the '%s' camera", self.request["name"], self.camera_name
            )
        except CameraError as e:
            self.error = e

    def join(self, timeout=None):
        super(CameraSettingWebRequestThread, self).join(timeout=timeout)
        return self.error is None, self.camera_name, self.error


class CameraError(Exception):
    def __init__(self, error_type, message, cause=None):
        super(CameraError, self).__init__()
        self.error_type = error_type
        self.cause = cause if cause is not None else None
        self.message = message

    def __str__(self):
        if self.cause is None:
            return "{0}: {1}".format(self.error_type, self.message)
        return "{0}: {1} - Inner Exception: {2}".format(self.error_type, self.message, "{}".format(self.cause))
