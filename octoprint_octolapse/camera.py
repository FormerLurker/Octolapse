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


def format_request_template(camera_address, template, value):
    return template.format(camera_address=camera_address, value=value)


def test_camera(camera_profile, timeout_seconds=2):
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
                fail_reason = "Camera Test failed - The request contained no data"
            elif "image/jpeg" not in r.headers["content-type"].lower():
                fail_reason = "Camera test failed - The returned data was not an image"
            else:
                return True, ""
        else:
            fail_reason = "Camera Test Failed - An invalid status code was returned from the camera:{0}".format(
                r.status_code)
    except (SSLError, Exception):
        # ToDo:  catch only expected exceptions.  Needs testing to figure out which ones these are.
        exception_type = sys.exc_info()[0]
        value = sys.exc_info()[1]
        fail_reason = "Camera Test Failed - An exception of type:{0} was raised during the test!  Error:{1}".format(
            exception_type, value)
    return False, fail_reason

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
            camera_settings_requests = [
                {
                    'template': current_camera.brightness_request_template,
                    'value': current_camera.brightness,
                    'name': 'brightness'
                },
                {
                    'template': current_camera.contrast_request_template,
                    'value': current_camera.contrast,
                    'name': 'contrast'
                },
                {
                    'template': current_camera.saturation_request_template,
                    'value': current_camera.saturation,
                    'name': 'saturation'
                },
                {
                    'template': current_camera.white_balance_auto_request_template,
                    'value': 1 if current_camera.white_balance_auto else 0,
                    'name': 'auto white balance'
                },
                {
                    'template': current_camera.powerline_frequency_request_template,
                    'value': current_camera.powerline_frequency,
                    'name': 'powerline frequency'
                },
                {
                    'template': current_camera.sharpness_request_template,
                    'value': current_camera.sharpness,
                    'name': 'sharpness'
                },
                {
                    'template': current_camera.backlight_compensation_enabled_request_template,
                    'value': 1 if current_camera.backlight_compensation_enabled else 0,
                    'name': 'set backlight compensation enabled'
                },
                {
                    'template': current_camera.exposure_type_request_template,
                    'value': current_camera.exposure_type,
                    'name': 'exposure type'
                },
                {
                    'template': current_camera.pan_request_template,
                    'value': current_camera.pan,
                    'name': 'pan'
                },
                {
                    'template': current_camera.tilt_request_template,
                    'value': current_camera.tilt,
                    'name': 'tilt'
                },
                {
                    'template': current_camera.autofocus_enabled_request_template,
                    'value': 1 if current_camera.autofocus_enabled else 0,
                    'name': 'set autofocus enabled'
                },
                {
                    'template': current_camera.zoom_request_template,
                    'value': current_camera.zoom,
                    'name': 'zoom'
                },
                {
                    'template': current_camera.led1_mode_request_template,
                    'value': current_camera.led1_mode,
                    'name': 'led 1 mode'
                },
                {
                    'template': current_camera.led1_frequency_request_template,
                    'value': current_camera.led1_frequency,
                    'name': 'led 1 frequency'
                },
                {
                    'template': current_camera.jpeg_quality_request_template,
                    'value': current_camera.jpeg_quality,
                    'name': 'jpeg quality'
                }
            ]

            if not current_camera.white_balance_auto:
                camera_settings_requests.append({
                    'template': current_camera.white_balance_temperature_request_template,
                    'value': current_camera.white_balance_temperature,
                    'name': 'white balance temperature'
                })

            # These settings only work when the exposure type is set to manual, I think.
            if current_camera.exposure_type == 1:
                camera_settings_requests.extend([
                    {
                        'template': current_camera.exposure_request_template,
                        'value': current_camera.exposure,
                        'name': 'exposure'
                    },
                    {
                        'template': current_camera.exposure_auto_priority_enabled_request_template,
                        'value': 1 if current_camera.exposure_auto_priority_enabled else 0,
                        'name': 'set auto priority enabled'
                    },
                    {
                        'template': current_camera.gain_request_template,
                        'value': current_camera.gain,
                        'name': 'gain'
                    }
                ])

            if not current_camera.autofocus_enabled:
                camera_settings_requests.append({
                    'template': current_camera.focus_request_template,
                    'value': current_camera.focus,
                    'name': 'focus'
                })

            for request in camera_settings_requests:
                threads.append(CameraSettingWebRequestThread(current_camera, request))
        return threads

    def _get_script_threads(self, force):
        threads = []
        for current_camera in self.Cameras:
            if not force and (not current_camera.enabled or not current_camera.camera_initialize_script):
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
            script = self.Camera.camera_initialize_script.strip()
            if not script:
                raise CameraError('no_camera_script_path', "The Camera Initialization script is empty")
            try:
                script_args = [
                    script,
                    self.Camera.name
                ]
                (return_code, console_output, error_message) = utility.run_command_with_timeout(
                    script_args, self.Camera.timeout_ms / 1000.0
                )
            except OSError as e:
                raise CameraError(
                    'camera_initialization_error',
                    "An OS Error error occurred while executing the custom camera initialization script",
                    cause=e
                )
            except CalledProcessError as e:

                # If we can't create the thumbnail, just log
                error_message = (
                    "An unexpected exception occurred executing the camera initialization script."
                )
                raise CameraError('camera_initialization_error', error_message, cause=e)

            if error_message is not None:
                if error_message.endswith("\r\n"):
                    error_message = error_message[:-2]
                self.Settings.current_debug_profile().log_error(
                    "Error output was returned from the custom camera initialization script: {0}".format(error_message))
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
        self.TimeoutSeconds = camera.timeout_ms/1000.0
        self.Error = None
        self._thread = None

    def run(self):
        try:
            # with self.camera_job_lock:
            error_messages = []
            success = False
            template = self.Request['template']
            value = self.Request['value']
            setting_name = self.Request['name']
            url = format_request_template(self.Address, template, value)
            try:
                if len(self.Username) > 0:
                    r = requests.get(url, auth=HTTPBasicAuth(self.Username, self.Password),
                                     verify=not self.IgnoreSslError, timeout=float(self.TimeoutSeconds))
                else:
                    r = requests.get(url, verify=not self.IgnoreSslError,
                                     timeout=float(self.TimeoutSeconds))

                if r.status_code == requests.codes.ok:
                    success = True
                else:
                    raise CameraError(
                        'webcam_settings_apply_error',
                        "Status code received was not OK.  Setting:{0}, Value:{1},"
                        "StatusCode:{2}, URL:{3}".format(setting_name, value, r.status_code, url)
                    )
            except SSLError as e:
                raise CameraError(
                    'webcam_settings_apply_error',
                    "An SSL error was raised while applying camera settings.  Setting:{0}, Value:{1}, "
                    "URL:{2}".format(setting_name, value, url),
                    cause=e
                )
            except Exception as e:
                raise CameraError(
                    'webcam_settings_apply_error',
                    "An unexpected error was raised while applying camera settings.  Setting:{0}, Value:{1}, "
                    "URL:{2}".format(setting_name, value, url),
                    cause=e
                )
        except CameraError as e:
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
