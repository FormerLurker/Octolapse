# coding=utf-8

import sys
import threading
import uuid

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
    def __init__(self, camera, on_success=None, on_fail=None, on_complete=None, timeout_seconds=2.0):
        self.Camera = camera
        self.TimeoutSeconds = timeout_seconds
        self.OnSuccess = on_success
        self.OnFail = on_fail
        self.OnComplete = on_complete

    def apply_settings(self):
        camera_settings_requests = [
            {
                'template': self.Camera.brightness_request_template,
                'value': self.Camera.brightness,
                'name': 'brightness'
            },
            {
                'template': self.Camera.contrast_request_template,
                'value': self.Camera.contrast,
                'name': 'contrast'
            },
            {
                'template': self.Camera.saturation_request_template,
                'value': self.Camera.saturation,
                'name': 'saturation'
            },
            {
                'template': self.Camera.white_balance_auto_request_template,
                'value': 1 if self.Camera.white_balance_auto else 0,
                'name': 'auto white balance'
            },
            {
                'template': self.Camera.powerline_frequency_request_template,
                'value': self.Camera.powerline_frequency,
                'name': 'powerline frequency'
            },
            {
                'template': self.Camera.sharpness_request_template,
                'value': self.Camera.sharpness,
                'name': 'sharpness'
            },
            {
                'template': self.Camera.backlight_compensation_enabled_request_template,
                'value': 1 if self.Camera.backlight_compensation_enabled else 0,
                'name': 'set backlight compensation enabled'
            },
            {
                'template': self.Camera.exposure_type_request_template,
                'value': self.Camera.exposure_type,
                'name': 'exposure type'
            },
            {
                'template': self.Camera.pan_request_template,
                'value': self.Camera.pan,
                'name': 'pan'
            },
            {
                'template': self.Camera.tilt_request_template,
                'value': self.Camera.tilt,
                'name': 'tilt'
            },
            {
                'template': self.Camera.autofocus_enabled_request_template,
                'value': 1 if self.Camera.autofocus_enabled else 0,
                'name': 'set autofocus enabled'
            },
            {
                'template': self.Camera.zoom_request_template,
                'value': self.Camera.zoom,
                'name': 'zoom'
            },
            {
                'template': self.Camera.led1_mode_request_template,
                'value': self.Camera.led1_mode,
                'name': 'led 1 mode'
            },
            {
                'template': self.Camera.led1_frequency_request_template,
                'value': self.Camera.led1_frequency,
                'name': 'led 1 frequency'
            },
            {
                'template': self.Camera.jpeg_quality_request_template,
                'value': self.Camera.jpeg_quality,
                'name': 'jpeg quality'
            }
        ]

        if not self.Camera.white_balance_auto:
            camera_settings_requests.append({
                'template': self.Camera.white_balance_temperature_request_template,
                'value': self.Camera.white_balance_temperature,
                'name': 'white balance temperature'
            })

        # These settings only work when the exposure type is set to manual, I think.
        if self.Camera.exposure_type == 1:
            camera_settings_requests.extend([
                {
                    'template': self.Camera.exposure_request_template,
                    'value': self.Camera.exposure,
                    'name': 'exposure'
                },
                {
                    'template': self.Camera.exposure_auto_priority_enabled_request_template,
                    'value': 1 if self.Camera.exposure_auto_priority_enabled else 0,
                    'name': 'set auto priority enabled'
                },
                {
                    'template': self.Camera.gain_request_template,
                    'value': self.Camera.gain,
                    'name': 'gain'
                }
            ])

        if not self.Camera.autofocus_enabled:
            camera_settings_requests.append({
                'template': self.Camera.focus_request_template,
                'value': self.Camera.focus,
                'name': 'focus'
            })

        # TODO:  Move the static timeout value to settings
        for request in camera_settings_requests:
            CameraSettingJob(
                self.Camera, request,
                self.TimeoutSeconds,
                on_success=self.OnSuccess,
                on_fail=self.OnFail,
                on_complete=self.OnComplete
            ).process_async()


class CameraSettingJob(object):
    # camera_job_lock = threading.RLock()

    def __init__(self, camera, camera_settings_request, timeout, on_success=None, on_fail=None, on_complete=None):
        camera = camera
        self.Request = camera_settings_request
        self.Address = camera.address
        self.Username = camera.username
        self.Password = camera.password
        self.IgnoreSslError = camera.ignore_ssl_error
        self.TimeoutSeconds = timeout
        self._on_success = on_success
        self._on_fail = on_fail
        self._on_complete = on_complete
        self._thread = None

    def process_async(self):
        self._thread = threading.Thread(
            target=self._process, name="CameraSettingChangeJob_{name}".format(name=str(uuid.uuid4())))
        self._thread.daemon = True
        self._thread.start()

    def _process(self):
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
                error_messages.append(
                    "Camera - Updated Settings - {0}:{1}, status code received was not OK.  "
                    "StatusCode:{2}, URL:{3}".format(
                        setting_name, value, r.status_code, url))
        except (SSLError, Exception):
            # Todo:  Figure out which exceptions to catch here
            exception_type = sys.exc_info()[0]
            value = sys.exc_info()[1]
            error_messages.append(
                "Camera Settings Apply- An exception of type:{0} was raised while adjusting camera {1} at the "
                "following URL:{2}, Error:{3}".format(
                    exception_type, setting_name, url, value))

        if success:
            self._notify_callback("success", value, setting_name, template)
        else:
            self._notify_callback(
                "fail", value, setting_name, template, error_messages)

        self._notify_callback("complete")

    def _notify_callback(self, callback, *args, **kwargs):
        """Notifies registered callbacks of type `callback`."""
        name = "_on_{}".format(callback)
        method = getattr(self, name, None)
        if method is not None and callable(method):
            method(*args, **kwargs)
