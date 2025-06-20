# coding=utf-8
##################################################################################
# Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
# Copyright (C) 2023  Brad Hochgesang
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
# remove unused imports
# import six
import octoprint_octolapse.utility as utility
import octoprint_octolapse.script as script
from threading import Thread
import time
import uuid
import shutil
# This file is subject to the terms and conditions defined in
# file called 'LICENSE', which is part of this source code package.
import requests
import os
import errno
# Todo:  Do we need to add this to setup.py?
# remove unused import
# from requests.auth import HTTPBasicAuth
from requests.exceptions import SSLError
from octoprint_octolapse.settings import CameraProfile, MjpgStreamerControl, MjpgStreamer
from tempfile import mkdtemp

# create the module level logger
from octoprint_octolapse.log import LoggingConfigurator
logging_configurator = LoggingConfigurator()
logger = logging_configurator.get_logger(__name__)


def format_request_template(camera_address, template, value):
    return template.format(camera_address=camera_address, value=value)


class CameraControl(object):

    camera_types = None
    camera_types_path = "webcam_types"
    camera_types_file = "camera_types.json"

    @staticmethod
    def _load_camera_types(data_path):
        # load all of the known camera types to allow custom control pages
        # custom pages aren't necessary, but they are much nicer to use
        # if they are available

        # we only need to load this once, so see if this is already complete
        if CameraControl.camera_types is not None:
            return
        camera_types = {
            "server_types": {}
        }
        # construct the path to the camera types file.  We'll reuse this later
        camera_type_path = os.path.join(data_path, "data", CameraControl.camera_types_path)
        # construct the file path to the camera types json file
        file_path = os.path.join(camera_type_path, CameraControl.camera_types_file)
        # load the list of available camera json files
        with open(file_path, 'r') as camera_files:
            camera_files = json.load(camera_files)

        server_types = camera_files["server_types"]
        # loop through each server type
        # remove python 2 compatibility
        # for key, server_type in six.iteritems(server_types):
        for key, server_type in server_types.items():
            camera_types["server_types"][key] = {'cameras': {}}
            # load all of the individual camera type info files for the current server
            for file_name in server_type["file_names"]:
                # construct the file path
                file_path = os.path.join(camera_type_path, server_type["directory"], file_name)
                # load the file
                with open(file_path, 'r') as camera_info_file:
                    # extract the data from the json file
                    camera = json.load(camera_info_file)
                    # if the current server type is mjpgstreamer, convert the controls array to dict
                    # of MjpgStreamerControl objects
                    controls = {}
                    if key == MjpgStreamer.server_type:
                        for index in range(len(camera["controls"])):
                            control = camera["controls"][index]
                            control_setting = MjpgStreamerControl()
                            control_setting.update(control)
                            control_setting.order = index
                            controls[control_setting.id] = control_setting
                        camera["controls"] = controls
                    # add the camera to our server type dictionary
                    camera_types["server_types"][key]["cameras"][camera["key"]] = camera

        CameraControl.camera_types = camera_types

    @staticmethod
    def get_webcam_type(data_path, server_type, data):

        # attempt to get the current camera type for the given server type and supplied data
        # first make sure our camera types are loaded
        # This will only happen once since the _load_camera_types function will return if it's already loaded
        CameraControl._load_camera_types(data_path)

        # return false if there is no data for the given server type
        if CameraControl.camera_types is None or server_type not in CameraControl.camera_types["server_types"]:
            return False

        # if the server type is mjpg-streamer, convert the data to a dict of
        if server_type == MjpgStreamer.server_type:
            controls = {}
            if isinstance(data, list):
                for control in data:
                    control_setting = MjpgStreamerControl()
                    control_setting.update(control)
                    controls[control_setting.id] = control_setting
            elif isinstance(data, dict):
                # remove python 2 compatibility
                # for key, control in six.iteritems(data):
                for key, control in data.items():
                    control_setting = MjpgStreamerControl()
                    control_setting.update(control)
                    controls[key] = control_setting
            else:
                message = "The webcam preferences supplied by the server are of an unknown type: {0}".format(
                    type(data)
                )
                logger.exception(CameraError("unknown-data-type", message))
                return False
            data = controls

        # get the available cameras for the given server type:
        cameras = CameraControl.camera_types["server_types"][server_type]["cameras"]

        # iterate the cameras dictionary for the given server type if possible
        # remove python 2 compatibility
        # for key, camera in six.iteritems(cameras):
        for key, camera in cameras.items():
            # see if the current camera type matches the given data
            if CameraControl._is_webcam_type(server_type, camera, data):
                return {
                    "key": camera["key"],
                    "name": camera["name"],
                    "make": camera["make"],
                    "model": camera["model"],
                    "template": camera["template"],
                }

        # no hits, the user will have to make due with the universal controls for now
        return False

    @staticmethod
    def _is_webcam_type(server_type, camera, data):
        if server_type == MjpgStreamer.server_type:
            # get the controls from the camera settings
            controls = camera["controls"]
            # create an MJPGStreamer settings object
            settings = MjpgStreamer()
            # update the settings from the camera data
            settings.update(camera)
            # check for a match
            if settings.controls_match_server(data):
                return True

        return False

    @staticmethod
    def apply_camera_settings(cameras, retries=3, backoff_factor=0.1, no_wait=False):
        errors = []

        # make sure the supplied cameras are enabled and either webcams or script cameras
        cameras = [x for x in cameras if x.camera_type in [
            CameraProfile.camera_type_webcam
        ]]

        # create the threads
        threads = []
        for current_camera in cameras:
            thread = None

            if current_camera.webcam_settings.server_type == MjpgStreamer.server_type:
                thread = MjpgStreamerSettingsThread(profile=current_camera, retries=retries, backoff_factor=backoff_factor)
                thread.daemon = True

            if thread:
                threads.append(thread)

        # start the threads
        for thread in threads:
            thread.start()

        if not no_wait:
            # join the threads, but timeout in a reasonable way
            for thread in threads:
                thread.join(requests.packages.urllib3.util.retry.Retry.BACKOFF_MAX)
                if not thread.success:
                    for error in thread.errors:
                        errors.append(error)
            return len(errors) == 0, CameraControl._get_errors_string(errors)
        return True, ""

    @staticmethod
    def run_on_print_start_script(cameras):
        # build the arg list
        args_list = []
        # remove python 2 compatibility
        # for key, camera in six.iteritems(cameras):
        for key, camera in cameras.items():
            script_path = camera.on_print_start_script.strip()
            if not script_path or not camera.enabled:
                # skip any cameras where there is no on print start script or the camera is disabled
                continue
            script_args = [camera.name]
            script_type = 'on print start'

            args = {
                'camera': camera,
                'script_path': script_path,
                'script_args': script_args,
                'script_type': script_type
            }
            args_list.append(args)

        if len(args_list) > 0:
            return CameraControl._run_camera_scripts(args_list)

        return True, None

    @staticmethod
    def run_on_print_end_script(cameras):
        # build the arg list
        args_list = []
        # remove python 2 compatibility
        # for key, camera in six.iteritems(cameras):
        for key, camera in cameras.items():
            script_path = camera.on_print_end_script.strip()
            if not script_path or not camera.enabled:
                # skip any cameras where there is no on print start script or the camera is disabled
                continue
            script_args = [camera.name]
            script_type = 'on print end'

            args = {
                'camera': camera,
                'script_path': script_path,
                'script_args': script_args,
                'script_type': script_type
            }
            args_list.append(args)

        if len(args_list) > 0:
            return CameraControl._run_camera_scripts(args_list)
        return True, None

    @staticmethod
    def _run_camera_scripts(args_list, timeout_seconds=5):
        errors = []

        # create the threads
        threads = []
        for args in args_list:
            thread = CameraSettingScriptThread(
                args['camera'],
                args['script_path'],
                args['script_args'],
                args['script_type']
            )
            thread.daemon = True
            threads.append(thread)

        # start the threads
        for thread in threads:
            thread.start()
        start_time = time.time()
        timeout_time = start_time + timeout_seconds
        # join the threads, but timeout in a reasonable way
        for thread in threads:
            timeout_sec = timeout_time - time.time()
            if timeout_sec < 0:
                timeout_sec = 0.001
            thread.join(timeout_sec)
            if thread.error:
                errors.append(thread.error)

        return len(errors) == 0, CameraControl._get_errors_string(errors)


    @staticmethod
    def _get_errors_string(errors):
        if len(errors) == 0:
            return ""
        unknown_errors_count = 0
        safe_errors = []
        for error in errors:
            if isinstance(error, CameraError):
                safe_errors.append(error.message)
            else:
                unknown_errors_count += 1

        camera_errors = " - ".join(safe_errors)
        unknown_errors = ""
        if unknown_errors_count > 0:
            unknown_errors = "{} unknown errors, check plugin.octolapse.log for details.".format(unknown_errors_count)
        return "{}{}".format(camera_errors, unknown_errors)

    @staticmethod
    def apply_webcam_setting(
        server_type,
        setting,
        camera_name,
        address,
        username,
        password,
        ignore_ssl_error
    ):
        if server_type == 'mjpg-streamer':
            thread = MjpgStreamerSettingThread(
                setting,
                address,
                username,
                password,
                ignore_ssl_error,
                camera_name
            )
            thread.daemon = True
            thread.start()
            thread.join()
            return thread.success, thread.errors
        else:
            message = "Cannot apply camera settings to the server type:{0}".format(server_type)
            logger.error(message)
            return False, [CameraError("unknown-server-type",message)]

    @staticmethod
    def get_webcam_settings(
        server_type,
        camera_name,
        address,
        username,
        password,
        ignore_ssl_error,
        retries=3,
        backoff_factor=0.1
    ):
        try:
            errors = []
            controls = None

            if server_type == 'mjpg-streamer':
                thread = MjpgStreamerControlThread(
                    address=address,
                    username=username,
                    password=password,
                    ignore_ssl_error=ignore_ssl_error,
                    camera_name=camera_name,
                    retries=retries,
                    backoff_factor=backoff_factor
                )
                thread.daemon = True
                thread.start()
                thread.join()
                if thread.errors:
                    for error in thread.errors:
                        errors.append(error)

                if len(errors)>0:
                    return len(errors) == 0, CameraControl._get_errors_string(errors), None

                controls = thread.controls
                # clean up default values
                if not controls:
                    raise CameraError(
                        "no-settings-found",
                        "No image preference controls could be returned from MjpgStreamer."
                    )

                # turn this into a dictionary
                control_dict = {}
                for index in range(len(controls)):
                    control = controls[index]
                    control.order = index
                    control_dict[control.id] = control

                return True, "", {
                    "webcam_settings": {
                        "mjpg_streamer": {
                            "controls": control_dict
                        }
                    }
                }
            else:
                raise CameraError(
                    "unknown-server",
                    "The streaming server type does not currently support custom image preferences."
                )
        except CameraError as e:
            return False, CameraControl._get_errors_string([e]), None

    @staticmethod
    def get_webcam_server_type_from_request(r):
        webcam_server_type = "unknown"
        if "server" in r.headers:
            if r.headers["server"].startswith('MJPG-Streamer'):
                webcam_server_type = "mjpg-streamer"
            elif r.headers["server"].startswith('yawcam'):
                webcam_server_type = "yawcam"
            else:
                webcam_server_type = r.headers["server"]

        return webcam_server_type

    @staticmethod
    def _test_mjpg_streamer_control(camera_profile, timeout_seconds=2):
        url = camera_profile.webcam_settings.address + "?action=command&id=-1"
        try:
            s = requests.Session()
            s.verify = not camera_profile.webcam_settings.ignore_ssl_error
            if len(camera_profile.webcam_settings.username) > 0:
                s.auth = (
                    camera_profile.webcam_settings.username,
                    camera_profile.webcam_settings.password
                )

            r = utility.requests_retry_session(session=s).request("GET", url, timeout=timeout_seconds)

            #if len(camera_profile.webcam_settings.username) > 0:
            #    r = requests.get(url, auth=HTTPBasicAuth(camera_profile.webcam_settings.username,
            #                                             camera_profile.webcam_settings.password),
            #                     verify=not camera_profile.webcam_settings.ignore_ssl_error,
            #                     timeout=float(timeout_seconds))
            #else:
            #    r = requests.get(
            #        url, verify=not camera_profile.webcam_settings.ignore_ssl_error, timeout=float(timeout_seconds))

            webcam_server_type = CameraControl.get_webcam_server_type_from_request(r)
            if webcam_server_type != "mjpg-streamer":
                message = "An unknown webcam server type '{0}' is being used for the '{1}' camera profile.  Currently " \
                          "only MJPEGStreamer is supported.  Unable to apply custom image preferences.".format(
                    webcam_server_type, camera_profile.name)
                logger.error(message)
                raise CameraError('unknown-server-type', message)
            if r.status_code == 501:
                message = "The server denied access to the mjpg-streamer control.htm for the '{0}' camera profile.  <a " \
                          "href=\"https://github.com/FormerLurker/Octolapse/wiki/V0.4---Enabling-Camera-Controls\" target = \"_blank\">Please see this link to correct this " \
                          "error.</a>, or disable the 'Enable And Apply Preferences at Startup' and " \
                          "'Enable And Apply Preferences Before Print' options.".format(camera_profile.name)
                logger.error(message)
                raise CameraError("mjpg_streamer_control_error", message)
            if r.status_code != requests.codes.ok:
                message = "Status code received ({0}) was not OK.  Double check your webcam 'Base Addresss' address and " \
                          "your 'Snapshot Address'.  Or, disable the 'Enable And Apply Preferences at Startup' " \
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
        except Exception as e:
            message = (
                "An unexpected error was raised while testing custom image preferences for the '{0}' camera profile."
                    .format(camera_profile.name)
            )
            logger.exception(message)
            raise CameraError('webcam_settings_apply_error', message, cause=e)

    @staticmethod
    def test_web_camera_image_preferences(camera_profile, timeout_seconds=2):
        try:
            CameraControl._test_web_camera_image_preferences(camera_profile, timeout_seconds)
        except CameraError as e:
            return False, CameraControl._get_errors_string([e])
        return True, ""

    @staticmethod
    def _test_web_camera_image_preferences(camera_profile, timeout_seconds=2):
        assert (isinstance(camera_profile, CameraProfile))
        # first see what kind of server we have
        url = format_request_template(
            camera_profile.webcam_settings.address, camera_profile.webcam_settings.snapshot_request_template, "")

        try:
            s = requests.Session()
            s.verify = not camera_profile.webcam_settings.ignore_ssl_error
            if len(camera_profile.webcam_settings.username) > 0:
                s.auth = (
                    camera_profile.webcam_settings.username,
                    camera_profile.webcam_settings.password
                )

            r = utility.requests_retry_session(session=s).request("GET", url, timeout=timeout_seconds)


        #    if len(camera_profile.webcam_settings.username) > 0:
        #        r = requests.get(url, auth=HTTPBasicAuth(camera_profile.webcam_settings.username,
        #                                                 camera_profile.webcam_settings.password),
        #                         verify=not camera_profile.webcam_settings.ignore_ssl_error,
        #                         timeout=float(timeout_seconds))
        #    else:
        #        r = requests.get(url, verify=not camera_profile.webcam_settings.ignore_ssl_error,
        #                         timeout=float(timeout_seconds))

            webcam_server_type = CameraControl.get_webcam_server_type_from_request(r)

        except SSLError as e:
            message = (
                "An SSL occurred while testing the '{0}' camera profile.  Look for the 'Camera Profile->Advanced Camera "
                "Opotions->Security->Ignore SSL Errors setting for a possible solution.".format(camera_profile.name)
            )
            logger.exception(message)
            raise CameraError('ssl-error', message, cause=e)
        except requests.ConnectionError as e:
            message = "Unable to connect to '{0}' for the '{1}' camera profile.  Please double check your 'Base Address' " \
                      "and 'Snapshot Address' settings.".format(url, camera_profile.name)
            logger.exception(message)
            raise CameraError('connection-error', message, cause=e)
        except Exception as e:
            message = "'An unexpected exception occured while testing the '{0}' camera profile.".format(
                camera_profile.name)
            logger.exception(message)
            raise CameraError('unknown-exception', message, cause=e)

        if webcam_server_type == "mjpg-streamer":

            CameraControl._test_mjpg_streamer_control(camera_profile, timeout_seconds)
        elif webcam_server_type == "yawcam":
            message = "You cannot use Yawcam with custom image preferences enabled.  Please disable custom image " \
                      "prefences for the  '{0}' camera profile. ".format(webcam_server_type, camera_profile.name)
            logger.error(message)
            raise CameraError('unsupported-server-type', message)
        else:
            message = "An unknown webcam server type '{0}' is being used for the '{1}' camera profile.  Currently only " \
                      "MJPEGStreamer is supported.  Unable to apply custom image preferences.".format(
                webcam_server_type,
                camera_profile.name)
            logger.error(message)
            raise CameraError('unknown-server-type', message)

    @staticmethod
    def test_web_camera(camera_profile, timeout_seconds=2, is_before_print_test=False):
        try:
            CameraControl._test_web_camera(camera_profile, timeout_seconds, is_before_print_test)
        except CameraError as e:
            return False, CameraControl._get_errors_string([e])
        return True, ""

    @staticmethod
    def _test_web_camera(camera_profile, timeout_seconds=2, is_before_print_test=False):
        url = format_request_template(
            camera_profile.webcam_settings.address, camera_profile.webcam_settings.snapshot_request_template, "")
        try:
            s = requests.Session()
            s.verify = not camera_profile.webcam_settings.ignore_ssl_error
            if len(camera_profile.webcam_settings.username) > 0:
                s.auth = (
                    camera_profile.webcam_settings.username,
                    camera_profile.webcam_settings.password
                )
            retry_session = utility.requests_retry_session(session=s)
            r = retry_session.get(url, stream=True, timeout=timeout_seconds)

            body = []
            start_time = time.time()
            for chunk in r.iter_content(1024):
                body.append(chunk)
                if time.time() > (start_time + timeout_seconds):
                    message = (
                        "A read timeout occurred while connecting to {0} for the '{1}' camera profile.  Are you using the video stream URL by mistake?"
                            .format(url, camera_profile.name)
                    )
                    logger.exception(message)
                    raise CameraError('read-timeout', message)
            #if len(camera_profile.webcam_settings.username) > 0:
            #    r = requests.get(url, auth=HTTPBasicAuth(camera_profile.webcam_settings.username,
            #                                             camera_profile.webcam_settings.password),
            #                     verify=not camera_profile.webcam_settings.ignore_ssl_error,
            #                     timeout=float(timeout_seconds))
            #else:
            #    r = requests.get(
            #        url, verify=not camera_profile.webcam_settings.ignore_ssl_error, timeout=float(timeout_seconds))
            if r.status_code == requests.codes.ok:
                if 'content-length' in r.headers and r.headers["content-length"] == 0:
                    message = "The request contained no data for the '{0}' camera profile.".format(camera_profile.name)
                    logger.error(message)
                    raise CameraError('request-contained-no-data', message)
                elif "image/jpeg" not in r.headers["content-type"].lower():
                    message = (
                        "The returned data was not an image for the '{0}' camera profile.".format(camera_profile.name)
                    )
                    logger.error(message)
                    raise CameraError('not-an-image', message)
                elif (
                    is_before_print_test and
                    camera_profile.enable_custom_image_preferences and
                    camera_profile.apply_settings_before_print
                ):
                    CameraControl._test_web_camera_image_preferences(camera_profile, timeout_seconds)
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

    @staticmethod
    def test_script(camera_profile, script_type, base_folder):
        snapshot_created = None
        if script_type == 'snapshot':
            success, error, snapshot_created = CameraControl._test_camera_snapshot_script(camera_profile, script_type, base_folder)
        elif script_type in ['before-snapshot', 'after-snapshot']:
            success, error = CameraControl._test_camera_before_after_snapshot_script(
                camera_profile, script_type, base_folder
            )
        elif script_type in ['before-print', 'after-print']:
            success, error = CameraControl._test_print_script(camera_profile, script_type, base_folder)
        elif script_type == 'before-render':
            success, error = CameraControl._test_before_render_script(camera_profile, script_type, base_folder)
        elif script_type == 'after-render':
            success, error = CameraControl._test_after_render_script(camera_profile, script_type, base_folder)
        else:
            return False, "An unknown script type of {0} was sent.  Cannot test script".format(script), None

        return success, error, snapshot_created

    @staticmethod
    def _test_camera_snapshot_script(camera_profile, script_type, base_folder):
        """Test a script camera."""
        # create a temp directory for use with this test
        temp_directory = mkdtemp()

        try:
            camera_name = camera_profile.name
            snapshot_number = 0
            delay_seconds = camera_profile.delay
            data_directory = temp_directory
            snapshot_directory = os.path.join(
                data_directory, "{}".format(uuid.uuid4()), "{}".format(uuid.uuid4())
            )
            snapshot_filename = utility.get_snapshot_filename(
                "test_snapshot", snapshot_number
            )
            snapshot_full_path = os.path.join(snapshot_directory, snapshot_filename)
            timeout_seconds = camera_profile.timeout_ms / 1000.0

            script_path = camera_profile.external_camera_snapshot_script

            cmd = script_job = script.CameraScriptSnapshot(
                script_path,
                camera_name,
                snapshot_number,
                delay_seconds,
                data_directory,
                snapshot_directory,
                snapshot_filename,
                snapshot_full_path,
                timeout_seconds=timeout_seconds
            )
            cmd.run()
            # check to see if the snapshot image was created
            success = cmd.success()
            snapshot_created = os.path.exists(snapshot_full_path)
            return cmd.success(), cmd.error_message, snapshot_created
        finally:
            utility.rmtree(temp_directory)

    @staticmethod
    def _test_camera_before_after_snapshot_script(camera_profile, script_type, base_folder):
        """Test a script camera."""
        # create a temp directory for use with this test
        temp_directory = mkdtemp()

        try:
            camera_name = camera_profile.name
            snapshot_number = 0
            delay_seconds = camera_profile.delay
            data_directory = temp_directory
            snapshot_directory = os.path.join(
                data_directory, "{}".format(uuid.uuid4()), "{}".format(uuid.uuid4())
            )
            snapshot_filename = utility.get_snapshot_filename(
                "test_snapshot", snapshot_number
            )
            snapshot_full_path = os.path.join(snapshot_directory, snapshot_filename)
            timeout_seconds = camera_profile.timeout_ms / 1000.0

            # setup test depending on the script_type
            script_path = ""
            if script_type == 'before-snapshot':
                script_path = camera_profile.on_before_snapshot_script
            elif script_type == 'after-snapshot':
                script_path = camera_profile.on_after_snapshot_script
                # we need to add an image to the temp folder, in case the script operates on the image
                test_image_path = os.path.join(base_folder, "data", "Images", "test-snapshot-image.jpg")
                target_directory = os.path.dirname(snapshot_full_path)
                if not os.path.exists(target_directory):
                    try:
                        os.makedirs(target_directory)
                    except OSError as e:
                        if e.errno == errno.EEXIST:
                            pass
                        else:
                            raise
                shutil.copy(test_image_path, snapshot_full_path)

            if script_type == 'before-snapshot':
                cmd = script.CameraScriptBeforeSnapshot(
                    script_path,
                    camera_name,
                    snapshot_number,
                    delay_seconds,
                    data_directory,
                    snapshot_directory,
                    snapshot_filename,
                    snapshot_full_path,
                    timeout_seconds=timeout_seconds
                )
            else:
                cmd = script.CameraScriptAfterSnapshot(
                    script_path,
                    camera_name,
                    snapshot_number,
                    delay_seconds,
                    data_directory,
                    snapshot_directory,
                    snapshot_filename,
                    snapshot_full_path,
                    timeout_seconds=timeout_seconds
                )
            cmd.run()
            return cmd.success(), cmd.error_message
        finally:
            utility.rmtree(temp_directory)

    @staticmethod
    def _test_print_script(camera_profile, script_type, base_folder):
        timeout_seconds = camera_profile.timeout_ms / 1000.0
        # build the arg list
        if script_type == "before-print":
            script_path = camera_profile.on_print_start_script.strip()
        else:
            script_path = camera_profile.on_print_end_script.strip()

        if script_type == "before-print":
            cmd = script.CameraScriptBeforePrint(
                script_path,
                camera_profile.name,
                timeout_seconds=timeout_seconds
            )
        else:
            cmd = script.CameraScriptAfterPrint(
                script_path,
                camera_profile.name,
                timeout_seconds=timeout_seconds
            )
        cmd.run()
        return cmd.success(), cmd.error_message

    @staticmethod
    def _test_before_render_script(camera_profile, script_type, base_folder):
        timeout_seconds = camera_profile.timeout_ms / 1000.0
        # create a temp folder for the rendered file and the snapshots
        temp_directory = mkdtemp()

        try:
            # create 10 snapshots
            test_image_path = os.path.join(base_folder, "data", "Images", "test-snapshot-image.jpg")
            snapshot_directory = os.path.join(
                temp_directory, "{}".format(uuid.uuid4()), "{}".format(uuid.uuid4())
            )
            if not os.path.exists(snapshot_directory):
                try:
                    os.makedirs(snapshot_directory)
                except OSError as e:
                    if e.errno == errno.EEXIST:
                        pass
                    else:
                        raise

            for snapshot_number in range(10):
                snapshot_file_name = utility.get_snapshot_filename(
                    'test', snapshot_number
                )
                target_snapshot_path = os.path.join(snapshot_directory, snapshot_file_name)
                shutil.copy(test_image_path, target_snapshot_path)

            snapshot_filename_format = os.path.basename(
                utility.get_snapshot_filename(
                    "render_script_test", utility.SnapshotNumberFormat
                )
            )
            script_path = camera_profile.on_before_render_script.strip()

            if script_path is None or len(script_path) == 0:
                return False, "No script path was provided.  Please enter a script path and try again."

            if not os.path.isfile(script_path):
                return False, "The script path '{0}' does not exist.  Please enter a valid script path and try again.".format(script_path)

            console_output = ""
            error_message = ""

            cmd = script.CameraScriptBeforeRender(
                script_path,
                camera_profile.name,
                snapshot_directory,
                snapshot_filename_format,
                os.path.join(snapshot_directory, snapshot_filename_format),
                timeout_seconds=timeout_seconds
            )
            cmd.run()
            return cmd.success(), cmd.error_message
        finally:
            utility.rmtree(temp_directory)

    @staticmethod
    def _test_after_render_script(camera_profile, script_type, base_folder):

        # create a temp folder for the rendered file and the snapshots
        temp_directory = mkdtemp()
        timeout_seconds = camera_profile.timeout_ms / 1000.0
        try:
            # create 10 snapshots
            test_image_path = os.path.join(base_folder, "data", "Images", "test-snapshot-image.jpg")
            snapshot_directory = os.path.join(
                temp_directory, "{}".format(uuid.uuid4()), "{}".format(uuid.uuid4())
            )
            if not os.path.exists(snapshot_directory):
                try:
                    os.makedirs(snapshot_directory)
                except OSError as e:
                    if e.errno == errno.EEXIST:
                        pass
                    else:
                        raise

            for snapshot_number in range(10):
                snapshot_file_name = utility.get_snapshot_filename(
                    'test', snapshot_number
                )
                target_snapshot_path = os.path.join(snapshot_directory, snapshot_file_name)
                shutil.copy(test_image_path, target_snapshot_path)

            snapshot_filename_format = os.path.basename(
                utility.get_snapshot_filename(
                    "render_script_test", utility.SnapshotNumberFormat
                )
            )


            script_path = camera_profile.on_after_render_script.strip()
            rendering_path = os.path.join(temp_directory, "timelapse", "test_rendering.mp4")

            output_filepath = utility.get_collision_free_filepath(rendering_path)
            output_filename = utility.get_filename_from_full_path(rendering_path)
            output_directory = utility.get_directory_from_full_path(rendering_path)
            output_extension = utility.get_extension_from_full_path(rendering_path)

            if script_path is None or len(script_path) == 0:
                return False, "No script path was provided.  Please enter a script path and try again."

            if not os.path.exists(script_path):
                return False, "The script path '{0}' does not exist.  Please enter a valid script path and try again.".format(
                    script_path)

            cmd = script.CameraScriptAfterRender(
                script_path,
                camera_profile.name,
                snapshot_directory,
                snapshot_filename_format,
                os.path.join(snapshot_directory, snapshot_filename_format),
                output_directory,
                output_filename,
                output_extension,
                rendering_path,
                timeout_seconds=timeout_seconds
            )
            cmd.run()
            return cmd.success(), cmd.error_message
        finally:
            utility.rmtree(temp_directory)

    @staticmethod
    def load_webcam_defaults(
        server_type,
        camera_name,
        address,
        username,
        password,
        ignore_ssl_error,
        retries=3,
        backoff_factor=0.1):

        if server_type == MjpgStreamer.server_type:

            # load the settings for the camera
            success, errors, settings = CameraControl.get_webcam_settings(
                server_type,
                camera_name,
                address,
                username,
                password,
                ignore_ssl_error,
                retries=retries,
                backoff_factor=backoff_factor
            )
            if not success:
                return False, errors
            # set the control values to the defaults
            controls = settings["webcam_settings"]["mjpg_streamer"]["controls"]
            # remove python 2 compatibility
            # for key, control in six.iteritems(controls):
            for key, control in controls.items():
                control.value = control.default
                controls[key] = control.to_dict()

            # apply the defaults
            thread = MjpgStreamerSettingsThread(
                controls=controls,
                address=address,
                username=username,
                password=password,
                ignore_ssl_error=ignore_ssl_error,
                camera_name=camera_name,
                retries=retries,
                backoff_factor=backoff_factor
            )
            thread.daemon = True
            thread.start()
            thread.join()

            return len(thread.errors) == 0, CameraControl._get_errors_string(thread.errors), controls

        else:
            error = "Unable to load default settings for the server type {server_type}.  Currently only mjpg-streamer" \
                    " is supported. ".format(server_type)
            return False, [error], None


class MjpgStreamerThread(Thread):
    def __init__(
        self,
        profile=None,
        address=None,
        username=None,
        password=None,
        ignore_ssl_error=False,
        camera_name=None,
        retries=3,
        backoff_factor=0.1
    ):
        super(MjpgStreamerThread, self).__init__()
        if profile:
            self.address = profile.webcam_settings.address
            self.username = profile.webcam_settings.username
            self.password = profile.webcam_settings.password
            self.ignore_ssl_error = profile.webcam_settings.ignore_ssl_error
            self.camera_name = profile.name
        else:
            self.address = address
            self.username = username
            self.password = password
            self.ignore_ssl_error = ignore_ssl_error
            self.camera_name = camera_name
        # remove python 2 compatibility
        # if isinstance(self.address, six.string_types):
        if isinstance(self.address, str):
            self.address = self.address.strip()
        self.retries = retries
        self.backoff_factor=backoff_factor
        self.errors = []
        self.success = False


class MjpgStreamerControlThread(MjpgStreamerThread):
    def __init__(
        self,
        profile=None,
        address=None,
        username=None,
        password=None,
        ignore_ssl_error=False,
        camera_name=None,
        retries=3,
        backoff_factor=0.1
    ):
        super(MjpgStreamerControlThread, self).__init__(
            profile=profile,
            address=address,
            username=username,
            password=password,
            ignore_ssl_error=ignore_ssl_error,
            camera_name=camera_name,
            retries=retries,
            backoff_factor=backoff_factor
        )
        self.controls = None

    def run(self):
        try:
            self.controls = self.get_controls_from_server()
        except CameraError as e:
            logger.exception("An unexpected error occurred while running the MjpgStreamerControlThread.")
            self.errors.append(e)

    def get_controls_from_server(self):
        input_file = self.get_file("input.json")
        control_settings = []
        if "controls" in input_file:
            # turn the control json into MjpgStreamerSetting
            for index in range(len(input_file["controls"])):
                control = input_file["controls"][index]
                control_setting = MjpgStreamerControl()
                control_setting.update(control)
                control_setting.order = index
                control_settings.append(control_setting)
        return control_settings

    def get_file(self, file_name):

        url = "{camera_address}{file_name}".format(camera_address=self.address, file_name=file_name)
        try:
            s = requests.Session()
            s.verify = not self.ignore_ssl_error
            if len(self.username) > 0:
                s.auth = (self.username, self.password)

            r = utility.requests_retry_session(session=s, retries=self.retries,
                                               backoff_factor=self.backoff_factor).request("GET", url)
            #if len(self.username) > 0:
            #    r = requests.get(url, auth=HTTPBasicAuth(self.username, self.password),
            #                     verify=not self.ignore_ssl_error, timeout=float(self.timeout_seconds))
            #else:
            #    r = requests.get(url, verify=not self.ignore_ssl_error,
            #                     timeout=float(self.timeout_seconds))
        except SSLError as e:
            message = (
                "An SSL error was raised while retrieving the {0} file for the '{1}' camera profile."
                    .format(file_name, self.camera_name)
            )
            raise CameraError('ssl_error', message, cause=e)
        except requests.ConnectionError as e:
            message = (
                "Unable to connect to the camera to '{0}' to retrieve controls for the {1} camera profile."
                    .format(url, self.camera_name)
            )
            raise CameraError("connection_error", message, cause=e)
        except Exception as e:
            message = (
                "An unexpected error was raised while retrieving the {0} file for the '{1}' camera profile."
                    .format(file_name, self.camera_name)
            )
            raise CameraError('unexpected_error', message, cause=e)

        if r.status_code == 501:
            message = "Access was denied to the mjpg-streamer {0} file for the " \
                      "'{1}' camera profile.".format(file_name, self.camera_name)
            raise CameraError("access_denied", message)
        if r.status_code == 404:
            message = "Unable to find the camera at the supplied base address for the " \
                      "'{0}' camera profile.".format(self.camera_name)
            raise CameraError("file_not_found", message)
        if r.status_code != requests.codes.ok:
            message = (
                "Recived a status code of ({0}) while retrieving the {1} file from the {2} camera profile."
                .format(r.status_code, file_name, self.camera_name)
            )
            raise CameraError('unexpected_status_code', message)
        try:
            data = json.loads(r.text, strict=False)
        except ValueError as e:
            raise CameraError('json_error', "Unable to read the input.json file from mjpg-streamer.  Please chack "
                                            "your base address and try again.", cause=e)
        return data


class MjpgStreamerSettingsThread(MjpgStreamerThread):
    def __init__(
        self,
        profile=None,
        controls=None,
        address=None,
        username=None,
        password=None,
        ignore_ssl_error=False,
        camera_name=None,
        retries=3,
        backoff_factor=0.1
    ):
        super(MjpgStreamerSettingsThread, self).__init__(
            profile=profile,
            address=address,
            username=username,
            password=password,
            ignore_ssl_error=ignore_ssl_error,
            camera_name=camera_name,
            retries=retries,
            backoff_factor=backoff_factor
        )
        if profile:
            mjpg_streamer = profile.webcam_settings.mjpg_streamer.clone()
            self.controls = mjpg_streamer.controls
        else:
            self.controls = controls

    def run(self):
        try:
            self.apply_mjpg_streamer_settings()
        except CameraError as e:
            self.errors.append(e)

    def apply_mjpg_streamer_settings(self):
        threads = []
        has_started_thread = False
        logger.info("Applying all webcam image settings to the %s camera.", self.camera_name)

        controls_list = []

        # remove python 2 compatibility
        # for key, control in six.iteritems(self.controls):
        for key, control in self.controls.items():
            controls_list.append(control)

        # Sort the controls.  They need to be sent in order.
        if len(controls_list) > 0:
            if isinstance(controls_list[0], dict):
                controls_list.sort(key=lambda x: x["order"], reverse=False)
            else:
                controls_list.sort(key=lambda x: x.order, reverse=False)

        for control in controls_list:

            thread = MjpgStreamerSettingThread(
                control,
                self.address,
                self.username,
                self.password,
                self.ignore_ssl_error,
                self.camera_name,
                retries=self.retries,
                backoff_factor=self.backoff_factor
            )
            thread.daemon = True
            threads.append(thread)

        if len(threads) > 0:
            logger.info("Applying all webcam image settings for the %s camera.", self.camera_name)
        for thread in threads:
            if not has_started_thread:
                has_started_thread = True
            thread.start()
            thread.join()
            errors = thread.errors
            self.success = thread.success
            if not self.success:
                for error in errors:
                    self.errors.append(error)
                break  # Do not continue applying settings if one fails.
        self.success = len(self.errors) == 0


class MjpgStreamerSettingThread(MjpgStreamerThread):
    def __init__(
        self,
        control,
        address,
        username,
        password,
        ignore_ssl_error,
        camera_name,
        retries=3,
        backoff_factor=0.1
     ):
        super(MjpgStreamerSettingThread, self).__init__(
            address=address,
            username=username,
            password=password,
            ignore_ssl_error=ignore_ssl_error,
            camera_name=camera_name,
            retries=retries,
            backoff_factor=backoff_factor
        )
        self.control = control

    def run(self):
        try:
            self.apply_mjpg_streamer_setting()
            self.success = len(self.errors) == 0
        except CameraError as e:
            self.errors.append(e)
        except Exception as e:
            self.errors.append(e)
            raise e

    def apply_mjpg_streamer_setting(self):

        if isinstance(self.control, dict):
            id = self.control["id"]
            group = self.control["group"]
            value = self.control["value"]
            name = self.control["name"]
        else:
            id = self.control.id
            group = self.control.group
            value = self.control.value
            name = self.control.name

        querystring = "?action={action}&dest={dest}&plugin={plugin}&id={id}&group={group}&value={value}".format(
            action="command",
            dest=0,
            plugin=0,
            id=id,
            group=group,
            value=value
        )

        url = "{address}{querystring}".format(
            address=self.address,
            querystring=querystring
        )
        logger.debug("Changing %s to %s for %s.  Request: %s", name, str(value), self.camera_name, url)
        try:
            # old version without session
            #if len(self.username) > 0:
            #    r = requests.get(url, auth=HTTPBasicAuth(self.username, self.password),
            #                     verify=not self.ignore_ssl_error, timeout=float(self.timeout_seconds))
            #else:
            #    r = requests.get(url, verify=not self.ignore_ssl_error,
            #                     timeout=float(self.timeout_seconds))

            s = requests.Session()
            s.verify = not self.ignore_ssl_error
            if len(self.username) > 0:
                s.auth = (self.username, self.password)

            r = utility.requests_retry_session(session=s, retries=self.retries, backoff_factor=self.backoff_factor).request("GET", url)

            webcam_server_type = CameraControl.get_webcam_server_type_from_request(r)
            if webcam_server_type != "mjpg-streamer":
                message = "An unknown webcam server '{0}' was detected while applying the {1} setting to the '{2}' camera " \
                          "profile.  Currently only MJPEGStreamer is supported.  Unable to apply custom image " \
                          "preferences. ".format(webcam_server_type, name, self.camera_name)
                logger.error(message)
                raise CameraError('unknown-server-type', message)
            if r.status_code == 501:
                message = "Access was denied to the mjpg-streamer control.html while applying the {0} setting to the '{" \
                          "1}' camera profile.  <a " \
                          "href=\"https://github.com/FormerLurker/Octolapse/wiki/V0.4---Enabling-Camera-Controls\" target = \"_blank\">Please see this link to correct this " \
                          "error.</a>, disable the 'Enable And Apply Preferences at Startup' " \
                          "and 'Enable And Apply Preferences Before Print' options '.".format(name,
                                                                                              self.camera_name)
                logger.error(message)
                raise CameraError("mjpg_streamer_control_error", message)
            if r.status_code != requests.codes.ok:
                message = (
                    "Recived a status code of ({0}) while applying the {1} settings to the {2} camera profile.  "
                    "Double check your 'Base Address' and 'Snapshot Address' within your camera profile "
                    "settings.  Or disable 'Custom Image Preferences' for this profile and try again.".format(
                        r.status_code, name, self.camera_name
                    )
                )
                logger.error(message)
                raise CameraError('webcam_settings_apply_error', message)
        except CameraError as e:
            raise e
        except SSLError as e:
            message = (
                "An SSL error was raised while applying the {0} setting to the '{1}' camera profile."
                .format(name, self.camera_name)
            )
            logger.exception(message)
            raise CameraError('ssl_error', message, cause=e)
        except Exception as e:
            message = (
                "An unexpected error was raised while applying the {0} setting to the '{1}' camera profile."
                .format(name, self.camera_name)
            )
            logger.exception(message)
            raise CameraError('webcam_settings_apply_error', message, cause=e)


class CameraSettingScriptThread(Thread):
    def __init__(self, camera, script_path, script_args, script_type):
        super(CameraSettingScriptThread, self).__init__()
        self.Camera = camera
        self.camera_name = camera.name
        self.script_path = script_path.strip()
        self.script_type = script_type
        self.script_args = script_args
        self.console_output = ""
        self.error = None

    def run(self):
        if self.script_type == "before-print":
            cmd = script.CameraScriptBeforePrint(
                self.script_path,
                self.camera_name
            )
        else:
            cmd = script.CameraScriptAfterPrint(
                self.script_path,
                self.camera_name
            )
        cmd.run()
        if not cmd.success():
            self.error = CameraError('error_message_returned', cmd.error_message)


class CameraError(Exception):
    def __init__(self, error_type, message, cause=None):
        super(CameraError, self).__init__()
        self.error_type = error_type
        self.cause = cause if cause is not None else None
        self.message = message

    def __str__(self):
        if self.cause is None:
            return "{0}: {1}".format(self.error_type, self.message)
        return "{0}: {1} - Inner Exception: {2}".format(
            self.error_type,
            self.message,
            "{} - {}".format(type(self.cause), self.cause)
        )
