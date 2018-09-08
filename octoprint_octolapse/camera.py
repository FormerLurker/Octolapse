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

import sys
import threading
import uuid
import utility
from threading import Thread
from subprocess import CalledProcessError
# This file is subject to the terms and conditions defined in
# file called 'LICENSE', which is part of this source code package.
import requests
# Todo:  Do we need to add this to setup.py?
from requests.auth import HTTPBasicAuth
from requests.exceptions import SSLError
from octoprint_octolapse.settings import Camera


def format_request_template(camera_address, template, value):
    return template.format(camera_address=camera_address, value=value)

#def test_external_camera_snapshot_script(camera_profile):


def test_web_camera(camera_profile, timeout_seconds=2):
    url = format_request_template(
        camera_profile.address, camera_profile.snapshot_request_template, "")
    try:
        if len(camera_profile.username) > 0:
            r = requests.get(url, auth=HTTPBasicAuth(camera_profile.username, camera_profile.password),
                             verify=not camera_profile.ignore_ssl_error, timeout=float(timeout_seconds))
        else:
            r = requests.get(
                url, verify=not camera_profile.ignore_ssl_error, timeout=float(timeout_seconds))
        if r.status_code == requests.codes.ok:
            if 'content-length' in r.headers and r.headers["content-length"] == 0:
                raise CameraError(
                    'request-contained-no-data',
                    "The request contained no data for the '{0}' camera profile."
                    .format(camera_profile.name)
                )
            elif "image/jpeg" not in r.headers["content-type"].lower():
                raise CameraError(
                    'not-an-image',
                    "The returned daata was not an image for the '{0}' camera profile."
                    .format(camera_profile.name)
                )
            elif camera_profile.apply_settings_before_print:
                test_web_camera_image_preferences(camera_profile, timeout_seconds)
        else:
            raise CameraError(
                'invalid-status-code',
                "An invalid status code or {0} was returned from the '{1}' camera profile."
                .format(r.status_code, camera_profile.name)
            )

    except SSLError as e:
        raise CameraError(
            'ssl-error',
            "An SSL occurred while testing the '{0}' camera profile.".format(camera_profile.name),
            cause=e
        )


def test_web_camera_image_preferences(camera_profile, timeout_seconds=2):
    assert (isinstance(camera_profile, Camera))
    # first see what kind of server we have
    url = format_request_template(
        camera_profile.address, camera_profile.snapshot_request_template, "")
    try:
        if len(camera_profile.username) > 0:
            r = requests.get(url, auth=HTTPBasicAuth(camera_profile.username, camera_profile.password),
                             verify=not camera_profile.ignore_ssl_error, timeout=float(timeout_seconds))
        else:
            r = requests.get(url, verify=not camera_profile.ignore_ssl_error, timeout=float(timeout_seconds))

        webcam_server_type = get_webcam_server_type_from_request(r)

    except SSLError as e:
        raise CameraError(
            'ssl-error',
            "An SSL occurred while testing the '{0}' camera profile.".format(camera_profile.name),
            cause=e
        )
    except Exception as e:
        raise CameraError(
            'unknown-exception',
            "'An unexpected exception occured while testing the '{0}' camera profile.".format(camera_profile.name),
            cause=e
        )

    if webcam_server_type == "MJPG-Streamer":
        test_mjpgstreamer_control(camera_profile, timeout_seconds)
    elif webcam_server_type == "yawcam":
        raise CameraError(
            'unsupported-server-type',
            "You cannot use Yawcam with custom image preferences enabled.  Please disable custom image prefences for "
            "the  '{0}' camera profile. "
            .format(webcam_server_type, camera_profile.name)
        )
    else:
        raise CameraError(
            'unknown-server-type',
            "An unknown webcam server type '{0}' is being used for the '{1}' camera profile.  Currently only MJPEGStreamer is supported.  Unable to apply custom image preferences."
            .format(webcam_server_type, camera_profile.name)
        )


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
    url = camera_profile.address + "?action=command&id=-1"
    try:
        if len(camera_profile.username) > 0:
            r = requests.get(url, auth=HTTPBasicAuth(camera_profile.username, camera_profile.password),
                             verify=not camera_profile.ignore_ssl_error, timeout=float(timeout_seconds))
        else:
            r = requests.get(
                url, verify=not camera_profile.ignore_ssl_error, timeout=float(timeout_seconds))

        webcam_server_type = get_webcam_server_type_from_request(r)
        if webcam_server_type != "MJPG-Streamer":
            raise CameraError(
                'unknown-server-type',
                "An unknown webcam server type '{0}' is being used for the '{1}' camera profile.  Currently only "
                "MJPEGStreamer is supported.  Unable to apply custom image preferences. "
                    .format(webcam_server_type, camera_profile.name)
            )
        if r.status_code == 501:
            raise CameraError(
                "mjpegstreamer-control-error",
                "The server denied access to the MJPG-Streamer control.html for the '{0}' camera profile.  <a " \
                "href=\"https://github.com/FormerLurker/Octolapse/wiki/Troubleshooting#why" \
                "-cant-i-change-contrast-zoom-focus-etc\" target = \"_blank\">Please see " \
                "this link to correct this error.</a>, or disable 'Custom Image Preferences'.".format(camera_profile.name)
            )
        if r.status_code != requests.codes.ok:
            raise CameraError(
                'webcam_settings_apply_error',
                "Status code received ({0}) was not OK.  Please disable 'Custom Image Preferences' for the {1} camera profile and try again."
                .format(r.status_code, camera_profile.name)
            )
    except SSLError as e:
        raise CameraError(
            'webcam_settings_ssl_error',
            "An SSL error was raised while testing custom image preferences for the '{0}' camera profile."
            .format(camera_profile.name),
            cause=e
        )
    except CameraError as e:
        # re raise the error
        raise e
    except Exception as e:
        raise CameraError(
            'webcam_settings_apply_error',
            "An unexpected error was raised while testing custom image preferences for the '{0}' camera profile."
            .format(camera_profile.name),
            cause=e
        )


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
            raise CameraError(
                'unknown-server-type',
                "An unknown webcam server '{0}' was detected while applying the {1} setting to the '{2}' camera "
                "profile.  Currently only MJPEGStreamer is supported.  Unable to apply custom image preferences. "
                .format(webcam_server_type, setting_name, camera_name)
            )
        if r.status_code == 501:
            raise CameraError(
                "mjpegstreamer-control-error",
                "Access was denied to the MJPG-Streamer control.html while applying the {0} setting to the '{1}' "
                "camera profile.  <a href=\"https://github.com/FormerLurker/Octolapse/wiki/Troubleshooting#why-cant-i"
                "-change-contrast-zoom-focus-etc\" target = \"_blank\">Please see this link to correct this "
                "error.</a>, or disable 'Custom Image Preferences'.".format(setting_name, camera_name)
            )
        if r.status_code != requests.codes.ok:
            raise CameraError(
                'webcam_settings_apply_error',
                "Recived a status code of ({0}) while applying the {1} settings to the {2} camera profile.  Please "
                "disable 'Custom Image Preferences' for this profile and try again."
                .format(setting_name, r.status_code, camera_name)
            )
    except CameraError as e:
        raise e
    except SSLError as e:
        raise CameraError(
            'ssl_error',
            "An SSL error was raised while applying the {0} setting to the '{1}' camera profile."
            .format(setting_name, camera_name),
            cause=e
        )
    except Exception as e:
        raise CameraError(
            'webcam_settings_apply_error',
            "An unexpected error was raised while applying the {0} setting to the '{1}' camera profile."
            .format(setting_name, camera_name),
            cause=e
        )


def get_web_camera_image_preference_requests(camera_profile):
    camera_settings_requests = [
        {
            'template': camera_profile.brightness_request_template,
            'value': camera_profile.brightness,
            'name': 'brightness'
        },
        {
            'template': camera_profile.contrast_request_template,
            'value': camera_profile.contrast,
            'name': 'contrast'
        },
        {
            'template': camera_profile.saturation_request_template,
            'value': camera_profile.saturation,
            'name': 'saturation'
        },
        {
            'template': camera_profile.white_balance_auto_request_template,
            'value': 1 if camera_profile.white_balance_auto else 0,
            'name': 'auto white balance'
        },
        {
            'template': camera_profile.powerline_frequency_request_template,
            'value': camera_profile.powerline_frequency,
            'name': 'powerline frequency'
        },
        {
            'template': camera_profile.sharpness_request_template,
            'value': camera_profile.sharpness,
            'name': 'sharpness'
        },
        {
            'template': camera_profile.backlight_compensation_enabled_request_template,
            'value': 1 if camera_profile.backlight_compensation_enabled else 0,
            'name': 'set backlight compensation enabled'
        },
        {
            'template': camera_profile.exposure_type_request_template,
            'value': camera_profile.exposure_type,
            'name': 'exposure type'
        },
        {
            'template': camera_profile.pan_request_template,
            'value': camera_profile.pan,
            'name': 'pan'
        },
        {
            'template': camera_profile.tilt_request_template,
            'value': camera_profile.tilt,
            'name': 'tilt'
        },
        {
            'template': camera_profile.autofocus_enabled_request_template,
            'value': 1 if camera_profile.autofocus_enabled else 0,
            'name': 'set autofocus enabled'
        },
        {
            'template': camera_profile.zoom_request_template,
            'value': camera_profile.zoom,
            'name': 'zoom'
        },
        {
            'template': camera_profile.led1_mode_request_template,
            'value': camera_profile.led1_mode,
            'name': 'led 1 mode'
        },
        {
            'template': camera_profile.led1_frequency_request_template,
            'value': camera_profile.led1_frequency,
            'name': 'led 1 frequency'
        },
        {
            'template': camera_profile.jpeg_quality_request_template,
            'value': camera_profile.jpeg_quality,
            'name': 'jpeg quality'
        }
    ]

    if not camera_profile.white_balance_auto:
        camera_settings_requests.append({
            'template': camera_profile.white_balance_temperature_request_template,
            'value': camera_profile.white_balance_temperature,
            'name': 'white balance temperature'
        })

    # These settings only work when the exposure type is set to manual, I think.
    if camera_profile.exposure_type == 1:
        camera_settings_requests.extend([
            {
                'template': camera_profile.exposure_request_template,
                'value': camera_profile.exposure,
                'name': 'exposure'
            },
            {
                'template': camera_profile.exposure_auto_priority_enabled_request_template,
                'value': 1 if camera_profile.exposure_auto_priority_enabled else 0,
                'name': 'set auto priority enabled'
            },
            {
                'template': camera_profile.gain_request_template,
                'value': camera_profile.gain,
                'name': 'gain'
            }
        ])

    if not camera_profile.autofocus_enabled:
        camera_settings_requests.append({
            'template': camera_profile.focus_request_template,
            'value': camera_profile.focus,
            'name': 'focus'
        })

    return camera_settings_requests


class CameraControl(object):
    def __init__(self, cameras):
        self.Cameras = cameras
        self.Errors = []

    def apply_settings(self, force, settings_type):

        errors = []
        threads = []
        if settings_type is None or settings_type == 'web-request':
            threads += self._get_web_request_threads(force=force)
        if settings_type is None or settings_type == 'script':
            threads += self._get_script_threads(force=force)
        for thread in threads:
            thread.start()

        for thread in threads:
            success, camera_name, error = thread.join()
            if not success:
                errors.append(error)

        return len(errors) == 0, errors

    def _get_web_request_threads(self, force):
        threads = []
        for current_camera in self.Cameras:
            if not force and (not current_camera.enabled or not current_camera.apply_settings_before_print):
                continue
            camera_settings_requests = get_web_camera_image_preference_requests(current_camera)

            for request in camera_settings_requests:
                threads.append(CameraSettingWebRequestThread(current_camera, request))
        return threads

    def _get_script_threads(self, force):
        threads = []
        for current_camera in self.Cameras:
            if not force and (not current_camera.enabled or not current_camera.on_print_start_script):
                continue
            threads.append(CameraSettingScriptThread(current_camera))
        return threads


class CameraSettingScriptThread(Thread):
    def __init__(self, camera):
        super(CameraSettingScriptThread, self).__init__()
        self.Camera = camera
        self.Error = None

    def run(self):
        try:
            script = self.Camera.on_print_start_script.strip()
            if not script:
                raise CameraError('no_camera_script_path', "The Camera Initialization script is empty")
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
                raise CameraError(
                    'camera_initialization_error',
                    "An OS Error error occurred while executing the custom camera initialization script",
                    cause=e
                )

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
                raise CameraError('camera_initialization_error', error_message)
        except CameraError as e:
            self.Error = e

    def join(self, timeout=None):
        super(CameraSettingScriptThread, self).join(timeout=timeout)
        return self.Error is None, self.Camera.name, self.Error


class CameraSettingWebRequestThread(Thread):

    def __init__(self, camera, camera_settings_request):
        super(CameraSettingWebRequestThread, self).__init__()
        camera = camera
        self.CameraName = camera.name
        self.Request = camera_settings_request
        self.Address = camera.address
        self.Username = camera.username
        self.Password = camera.password
        self.IgnoreSslError = camera.ignore_ssl_error
        self.TimeoutSeconds = camera.timeout_ms / 1000.0
        self.Error = None
        self._thread = None

    def run(self):
        try:
            apply_camera_image_preference(
                self.Request, self.Address, self.Username, self.Password, self.IgnoreSslError, self.TimeoutSeconds,
                self.CameraName
            )
        except (CameraError) as e:
            self.Error = e

    def join(self, timeout=None):
        super(CameraSettingWebRequestThread, self).join(timeout=timeout)
        return self.Error is None, self.CameraName, self.Error


class CameraError(Exception):
    def __init__(self, error_type, message, cause=None):
        super(CameraError, self).__init__()
        self.error_type = error_type
        self.cause = cause if cause is not None else None
        self.message = message

    def __str__(self):
        if self.cause is None:
            return "{}: {}".format(self.error_type, self.message, str(self.cause))
        return "{}: {} - Inner Exception: {}".format(self.error_type, self.message, str(self.cause))
