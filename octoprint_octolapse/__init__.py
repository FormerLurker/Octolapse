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


from __future__ import absolute_import

import json
import os
import shutil
from distutils.version import LooseVersion

import flask
import octoprint.plugin
import octoprint.server
# Octoprint Imports
# used to send messages to the web client for notifying it of new timelapses
from octoprint.events import eventManager, Events
from octoprint.server import admin_permission
from octoprint.server.util.flask import restricted_access

import octoprint_octolapse.camera as camera
import octoprint_octolapse.render as render
import octoprint_octolapse.utility as utility
from octoprint_octolapse.gcode_parser import Commands
from octoprint_octolapse.render import RenderingCallbackArgs
from octoprint_octolapse.settings import OctolapseSettings, Printer, Stabilization, Camera, Rendering, Snapshot, \
    DebugProfile
from octoprint_octolapse.timelapse import Timelapse, TimelapseState


# Octolapse imports


class OctolapsePlugin(octoprint.plugin.SettingsPlugin,
                      octoprint.plugin.AssetPlugin,
                      octoprint.plugin.TemplatePlugin,
                      octoprint.plugin.StartupPlugin,
                      octoprint.plugin.EventHandlerPlugin,
                      octoprint.plugin.BlueprintPlugin):
    TIMEOUT_DELAY = 1000

    def __init__(self):
        self.Settings = None  # type: OctolapseSettings
        self.Timelapse = None  # type: Timelapse
        self.IsRenderingSynchronized = False

    # Blueprint Plugin Mixin Requests

    @octoprint.plugin.BlueprintPlugin.route("/downloadTimelapse/<filename>", methods=["GET"])
    @restricted_access
    @admin_permission.require(403)
    def download_timelapse_request(self, filename):
        """Restricted access function to download a timelapse"""
        return self.get_download_file_response(self.get_timelapse_folder() + filename, filename)

    @octoprint.plugin.BlueprintPlugin.route("/snapshot/<filename>", methods=["GET"])
    def snapshot_request(self, filename):
        """Public access function to get the latest snapshot image"""
        if filename == 'latest-snapshot.jpeg':
            # get the latest snapshot image
            mime_type = 'image/jpeg'
            filename = utility.get_latest_snapshot_download_path(
                self.get_plugin_data_folder())
            if not os.path.isfile(filename):
                # we haven't captured any images, return the built in png.
                mime_type = 'image/png'
                filename = utility.get_no_snapshot_image_download_path(
                    self._basefolder)
        elif filename == 'latest_snapshot_thumbnail_300px.jpeg':
            # get the latest snapshot image
            mime_type = 'image/jpeg'
            filename = utility.get_latest_snapshot_thumbnail_download_path(
                self.get_plugin_data_folder())
            if not os.path.isfile(filename):
                # we haven't captured any images, return the built in png.
                mime_type = 'image/png'
                filename = utility.get_no_snapshot_image_download_path(
                    self._basefolder)
        else:
            # we don't recognize the snapshot type
            mime_type = 'image/png'
            filename = utility.get_error_image_download_path(self._basefolder)

        # not getting the latest image
        return flask.send_file(filename, mimetype=mime_type, cache_timeout=-1)

    @octoprint.plugin.BlueprintPlugin.route("/downloadSettings", methods=["GET"])
    @restricted_access
    @admin_permission.require(403)
    def download_settings_request(self):
        return self.get_download_file_response(self.get_settings_file_path(), "Settings.json")

    @octoprint.plugin.BlueprintPlugin.route("/stopTimelapse", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def stop_timelapse_request(self):

        self.Timelapse.stop_snapshots()
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/saveMainSettings", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def save_main_settings_request(self):
        request_values = flask.request.get_json()
        self.Settings.is_octolapse_enabled = request_values["is_octolapse_enabled"]
        self.Settings.auto_reload_latest_snapshot = request_values["auto_reload_latest_snapshot"]
        self.Settings.auto_reload_frames = request_values["auto_reload_frames"]
        self.Settings.show_navbar_icon = request_values["show_navbar_icon"]
        self.Settings.show_navbar_when_not_printing = request_values["show_navbar_when_not_printing"]
        self.Settings.show_position_state_changes = request_values["show_position_state_changes"]
        self.Settings.show_position_changes = request_values["show_position_changes"]
        self.Settings.show_extruder_state_changes = request_values["show_extruder_state_changes"]
        self.Settings.show_trigger_state_changes = request_values["show_trigger_state_changes"]
        self.Settings.show_real_snapshot_time = request_values["show_real_snapshot_time"]

        # save the updated settings to a file.
        self.save_settings()

        self.send_state_loaded_message()
        data = {'success': True}
        return json.dumps(data), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/setEnabled", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def set_enabled(self):
        request_values = flask.request.get_json()
        enable_octolapse = request_values["is_octolapse_enabled"]

        if (
            self.Timelapse is not None and
            self.Timelapse.is_timelapse_active() and
            self.Settings.is_octolapse_enabled and
            not enable_octolapse
        ):
            self.send_plugin_message(
                "disabled-running",
                "Octolapse will remain active until the current print ends."
                "  If you wish to stop the active timelapse, click 'Stop Timelapse'."
            )

        # save the updated settings to a file.
        self.Settings.is_octolapse_enabled = enable_octolapse
        self.save_settings()
        self.send_state_loaded_message()
        data = {'success': True}
        return json.dumps(data), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/toggleInfoPanel", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def toggle_info_panel(self):
        request_values = flask.request.get_json()
        panel_type = request_values["panel_type"]

        if panel_type == "show_position_state_changes":
            self.Settings.show_position_state_changes = not self.Settings.show_position_state_changes
        elif panel_type == "show_position_changes":
            self.Settings.show_position_changes = not self.Settings.show_position_changes
        elif panel_type == "show_extruder_state_changes":
            self.Settings.show_extruder_state_changes = not self.Settings.show_extruder_state_changes
        elif panel_type == "show_trigger_state_changes":
            self.Settings.show_trigger_state_changes = not self.Settings.show_trigger_state_changes
        else:
            return json.dumps({'error': "Unknown panel_type."}), 500, {'ContentType': 'application/json'}

        # save the updated settings to a file.
        self.save_settings()

        self.send_state_loaded_message()
        data = {'success': True}
        return json.dumps(data), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/loadMainSettings", methods=["POST"])
    def load_main_settings_request(self):
        data = {'success': True}
        data.update(self.Settings.get_main_settings_dict())
        return json.dumps(data), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/loadState", methods=["POST"])
    def load_state_request(self):
        if self.Settings is None:
            raise Exception(
                "Unable to load values from Octolapse.Settings, it hasn't been initialized yet.  Please wait a few "
                "minutes and try again.  If the problem persists, please check plugin_octolapse.log for exceptions.")
        if self.Timelapse is None:
            raise Exception(
                "Unable to load values from Octolapse.Timelapse, it hasn't been initialized yet.  Please wait a few "
                "minutes and try again.  If the problem persists, please check plugin_octolapse.log for exceptions.")
        self.send_state_loaded_message()
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/addUpdateProfile", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def add_update_profile_request(self):
        request_values = flask.request.get_json()
        profile_type = request_values["profileType"]
        profile = request_values["profile"]
        client_id = request_values["client_id"]
        updated_profile = self.Settings.add_update_profile(profile_type, profile)
        # save the updated settings to a file.
        self.save_settings()
        self.send_settings_changed_message(client_id)
        return json.dumps(updated_profile.to_dict()), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/removeProfile", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def remove_profile_request(self):
        request_values = flask.request.get_json()
        profile_type = request_values["profileType"]
        guid = request_values["guid"]
        client_id = request_values["client_id"]
        if not self.Settings.remove_profile(profile_type, guid):
            return (
                json.dumps({'success': False, 'error': "Cannot delete the default profile."}),
                200,
                {'ContentType': 'application/json'}
            )
        # save the updated settings to a file.
        self.save_settings()
        self.send_settings_changed_message(client_id)
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/setCurrentProfile", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def set_current_profile_request(self):
        request_values = flask.request.get_json()
        profile_type = request_values["profileType"]
        guid = request_values["guid"]
        client_id = request_values["client_id"]
        self.Settings.set_current_profile(profile_type, guid)
        self.save_settings()
        self.send_settings_changed_message(client_id)
        return json.dumps({'success': True, 'guid': request_values["guid"]}), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/restoreDefaults", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def restore_defaults_request(self):
        request_values = flask.request.get_json()
        client_id = request_values["client_id"]
        try:
            self.load_settings(force_defaults=True)
            data = {'success': True}
            data.update(self.Settings.to_dict())
            self.send_settings_changed_message(client_id)

            return json.dumps(data), 200, {'ContentType': 'application/json'}
        except Exception as e:
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))
        return json.dumps({'success': False}), 500, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/loadSettings", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def load_settings_request(self):
        data = {'success': True}
        data.update(self.Settings.to_dict())
        return json.dumps(data), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/applyCameraSettings", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def apply_camera_settings_request(self):
        request_values = flask.request.get_json()
        profile = request_values["profile"]
        camera_profile = Camera(profile)
        self.apply_camera_settings(camera_profile)

        return json.dumps({'success': True}, 200, {'ContentType': 'application/json'})

    @octoprint.plugin.BlueprintPlugin.route("/testCamera", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def test_camera_request(self):
        request_values = flask.request.get_json()
        profile = request_values["profile"]
        camera_profile = Camera(profile)
        results = camera.test_camera(camera_profile)
        if results[0]:
            return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
        else:
            return json.dumps({'success': False, 'error': results[1]}), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/validateRenderingTemplate", methods=["POST"])
    def validate_rendering_template(self):
        template = flask.request.form['output_template']
        result = render.is_rendering_template_valid(
            template,
            self.Settings.rendering_file_templates,
            self.get_plugin_data_folder()
        )
        if result[0]:
            valid = "true"
        else:
            valid = result[1]
        return "\"{0}\"".format(valid), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/rendering/watermark", methods=["GET"])
    @restricted_access
    @admin_permission.require(403)
    def get_available_watermarks(self):
        # TODO(Shadowen): Retrieve watermarks_directory_name from config.yaml.
        watermarks_directory_name = "watermarks"
        full_watermarks_dir = os.path.join(self.get_plugin_data_folder(), watermarks_directory_name)
        files = []
        if os.path.exists(full_watermarks_dir):
            files = [os.path.join(self.get_plugin_data_folder(), watermarks_directory_name, f) for f in os.listdir(full_watermarks_dir)]
        data = {'filepaths': files}
        return json.dumps(data), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/rendering/watermark/upload", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def upload_watermark(self):
        # TODO(Shadowen): Receive chunked uploads properly.
        # It seems like this function is called once PER CHUNK rather than when the entire upload has completed.

        # Parse the request.
        image_filename = flask.request.values['image.name']
        # The path where the watermark file was saved by the uploader.
        watermark_temp_path = flask.request.values['image.path']
        self._logger.debug("Receiving uploaded watermark {}.".format(image_filename))

        # Move the watermark from the (temp) upload location to a permanent location.
        # Maybe it could be uploaded directly there, but I don't know how to do that.
        # TODO(Shadowen): Retrieve watermarks_directory_name from config.yaml.
        watermarks_directory_name = "watermarks"
        # Ensure the watermarks directory exists.
        full_watermarks_dir = os.path.join(self.get_plugin_data_folder(), watermarks_directory_name)
        if not os.path.exists(full_watermarks_dir):
            self._logger.info("Creating watermarks directory at {}.".format(full_watermarks_dir))
            os.makedirs(full_watermarks_dir)

        # Move the image.
        watermark_destination_path = os.path.join(full_watermarks_dir, image_filename)
        if os.path.exists(watermark_destination_path):
            if os.path.isdir(watermark_destination_path):
                self._logger.error("Tried to upload watermark to {} but already contains a directory! Aborting!".format(
                    watermark_destination_path))
                return json.dumps({'error': 'Bad file name.'}, 501, {'ContentType': 'application/json'})
            else:
                # TODO(Shadowen): Maybe offer a config.yaml option for this.
                self._logger.warning("Tried to upload watermark to {} but file already exists! Overwriting...".format(
                    watermark_destination_path))
                os.remove(watermark_destination_path)
        self._logger.info("Moving watermark from {} to {}.".format(watermark_temp_path, watermark_destination_path))
        shutil.move(watermark_temp_path, watermark_destination_path)

        return json.dumps({}, 200, {'ContentType': 'application/json'})

    @octoprint.plugin.BlueprintPlugin.route("/rendering/watermark/delete", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def delete_watermark(self):
        """Delete the watermark given in the HTTP POST name field."""
        # Parse the request.
        filepath = flask.request.get_json()['path']
        self._logger.debug("Deleting watermark {}.".format(filepath))

        if not os.path.exists(filepath):
            self._logger.error("Tried to delete watermark at {} but file doesn't exists!".format(filepath))
            return json.dumps({'error': 'No such file.'}, 501, {'ContentType': 'application/json'})

        def is_subdirectory(a, b):
            """Returns true if a is (or is in) a subdirectory of b."""
            real_a = os.path.join(os.path.realpath(a), '')
            real_b = os.path.join(os.path.realpath(b), '')
            return os.path.commonprefix([real_a, real_b]) == real_a

        # TODO(Shadowen): Retrieve watermarks_directory_name from config.yaml.
        watermarks_directory_name = "watermarks"
        # Ensure the file we are trying to delete is in the watermarks folder.
        watermarks_directory = os.path.join(self.get_plugin_data_folder(), watermarks_directory_name)
        if not is_subdirectory(watermarks_directory, filepath):
            self._logger.error("Tried to delete watermark at {} but file doesn't exists!".format(filepath))
            return json.dumps({'error': "Cannot delete file outside watermarks folder."}, 400,
                              {'ContentType': 'application/json'})

        os.remove(filepath)
        return json.dumps({'success': "Deleted {} successfully.".format(filepath)}), 200, {
            'ContentType': 'application/json'}

    # blueprint helpers
    @staticmethod
    def get_download_file_response(file_path, download_filename):
        if os.path.isfile(file_path):

            def single_chunk_generator(download_file):
                while True:
                    chunk = download_file.read(1024)
                    if not chunk:
                        break
                    yield chunk

            file_to_download = open(file_path, 'rb')
            response = flask.Response(flask.stream_with_context(
                single_chunk_generator(file_to_download)))
            response.headers.set('Content-Disposition',
                                 'attachment', filename=download_filename)
            response.headers.set('Content-Type', 'application/octet-stream')
            return response
        return json.dumps({'success': False}), 404, {'ContentType': 'application/json'}

    def apply_camera_settings(self, camera_profile):
        camera_control = camera.CameraControl(
            camera_profile,
            self.on_apply_camera_settings_success,
            self.on_apply_camera_settings_fail,
            self.on_apply_camera_settings_complete
        )
        camera_control.apply_settings()

    def get_timelapse_folder(self):
        return utility.get_rendering_directory_from_data_directory(self.get_plugin_data_folder())

    def get_default_settings_path(self):
        return "{0}{1}data{1}settings_default.json".format(self._basefolder, os.sep)

    def get_settings_file_path(self):
        return "{0}{1}settings.json".format(self.get_plugin_data_folder(), os.sep)

    def get_log_file_path(self):
        return self._settings.get_plugin_logfile_path()

    def load_settings(self, force_defaults=False):
        # if the settings file does not exist, create one from the default settings
        create_new_settings = False
        if not os.path.isfile(self.get_settings_file_path()) or force_defaults:
            # create new settings from default setting file
            with open(self.get_default_settings_path()) as defaultSettingsJson:
                data = json.load(defaultSettingsJson)
                # if a settings file does not exist, create one ??
                new_settings = OctolapseSettings(self.get_log_file_path(), data, self._plugin_version)
                if self.Settings is not None:
                    self.Settings.update(new_settings.to_dict())
                else:
                    self.Settings = new_settings
            self.Settings.current_debug_profile().log_settings_load(
                "Creating new settings file from defaults.")
            create_new_settings = True
        else:
            # Load settings from file
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_settings_load(
                    "Loading existings settings file from: {0}.".format(self.get_settings_file_path()))
            else:
                self._logger.info("Loading existing settings file from: {0}.".format(
                    self.get_settings_file_path())
                )
            with open(self.get_settings_file_path()) as settingsJson:
                data = json.load(settingsJson)
            if self.Settings is None:
                #  create a new settings object
                self.Settings = OctolapseSettings(self.get_log_file_path(), data, self._plugin_version)
                self.Settings.current_debug_profile().log_settings_load("Settings loaded.")
            else:
                # update an existing settings object
                self.Settings.current_debug_profile().log_settings_load(
                    "Settings loaded.  Updating existing settings object."
                )
                self.Settings.update(data)
        # Extract any settings from octoprint that would be useful to our users.
        self.copy_octoprint_default_settings(
            apply_to_current_profile=create_new_settings)

        if create_new_settings:
            # No file existed, so we must have created default settings.  Save them!
            self.save_settings()
        return self.Settings.to_dict()

    def copy_octoprint_default_settings(self, apply_to_current_profile=False):
        try:
            # move some octoprint defaults if they exist for the webcam
            # specifically the address, the bitrate and the ffmpeg directory.
            # Attempt to get the camera address and snapshot template from Octoprint settings
            snapshot_url = self._settings.settings.get(["webcam", "snapshot"])
            from urlparse import urlparse
            # we are doing some templating so we have to try to separate the
            # camera base address from the querystring.  This will probably not work
            # for all cameras.
            try:
                o = urlparse(snapshot_url)
                camera_address = o.scheme + "://" + o.netloc + o.path
                self.Settings.current_debug_profile().log_settings_load(
                    "Setting octolapse camera address to {0}.".format(camera_address))
                snapshot_action = urlparse(snapshot_url).query
                snapshot_request_template = "{camera_address}?" + snapshot_action
                self.Settings.current_debug_profile().log_settings_load(
                    "Setting octolapse camera snapshot template to {0}.".format(snapshot_request_template))
                self.Settings.DefaultCamera.address = camera_address
                self.Settings.DefaultCamera.snapshot_request_template = snapshot_request_template
                if apply_to_current_profile:
                    for profile in self.Settings.cameras.values():
                        profile.address = camera_address
                        profile.snapshot_request_template = snapshot_request_template
            except Exception as e:
                # cannot send a popup yet,because no clients will be connected.  We should write a routine that
                # checks to make sure Octolapse is correctly configured if it is enabled and send some kind of
                # message on client connect. self.SendPopupMessage("Octolapse was unable to extract the default
                # camera address from Octoprint.  Please configure your camera address and snapshot template before
                # using Octolapse.")

                self.Settings.current_debug_profile().log_exception(e)

            bitrate = self._settings.settings.get(["webcam", "bitrate"])
            self.Settings.DefaultRendering.bitrate = bitrate
            if apply_to_current_profile:
                for profile in self.Settings.renderings.values():
                    profile.bitrate = bitrate
        except Exception as e:
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))

    def save_settings(self):
        # Save setting from file
        settings_dict = self.Settings.to_dict()
        self.Settings.current_debug_profile().log_settings_save(
            "Saving Settings.")

        with open(self.get_settings_file_path(), 'w') as outfile:
            json.dump(settings_dict, outfile)
        self.Settings.current_debug_profile().log_settings_save(
            "Settings saved.".format(settings_dict))

        return None

    # def on_settings_initialized(self):

    def get_current_printer_profile(self):
        """Get the plugin's current printer profile"""
        return self._printer_profile_manager.get_current()

    # EVENTS
    #########
    def get_settings_defaults(self):
        return dict(load=None)

    def on_settings_load(self):
        settings_dict = None
        # try:
        #     octoprint.plugin.SettingsPlugin.on_settings_load(self)
        #     settings_dict = self.Settings.to_dict()
        # except Exception, e:
        #     if self.Settings is not None:
        #         self.Settings.current_debug_profile().log_exception(e)
        #     else:
        #         self._logger.critical(utility.exception_to_string(e))

        return settings_dict

    def get_status_dict(self):
        try:
            is_timelapse_active = False
            snapshot_count = 0
            total_snapshot_time = 0
            is_taking_snapshot = False
            is_rendering = False
            timelapse_state = TimelapseState.Idle
            is_waiting_to_render = False
            profiles_dict = self.Settings.get_profiles_dict()
            debug_dict = profiles_dict["debug_profiles"]
            if self.Timelapse is not None:
                snapshot_count = self.Timelapse.SnapshotCount

                total_snapshot_time = self.Timelapse.SecondsAddedByOctolapse
                is_timelapse_active = self.Timelapse.is_timelapse_active()
                if is_timelapse_active:
                    profiles_dict = self.Timelapse.CurrentProfiles

                # Always get the current debug settings, else they won't update from the tab while a timelapse is
                # running.
                profiles_dict["current_debug_profile_guid"] = self.Settings.current_debug_profile_guid
                profiles_dict["debug_profiles"] = debug_dict
                is_rendering = self.Timelapse.get_is_rendering()
                is_taking_snapshot = TimelapseState.TakingSnapshot == self.Timelapse.State
                timelapse_state = self.Timelapse.State
                is_waiting_to_render = (not is_rendering) and self.Timelapse.State == TimelapseState.WaitingToRender
            return {'snapshot_count': snapshot_count,
                    'total_snapshot_time': total_snapshot_time,
                    'current_snapshot_time': 0,
                    'is_timelapse_active': is_timelapse_active,
                    'is_taking_snapshot': is_taking_snapshot,
                    'is_rendering': is_rendering,
                    'waiting_to_render': is_waiting_to_render,
                    'state': timelapse_state,
                    'profiles': profiles_dict
                    }
        except Exception as e:
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))
        return None

    def get_template_configs(self):
        self._logger.info("Octolapse - is loading template configurations.")
        return [dict(type="settings", custom_bindings=True)]

    def create_timelapse_object(self):
        self.Timelapse = Timelapse(
            self.Settings,
            self._printer,
            self.get_plugin_data_folder(),
            self._settings.settings.getBaseFolder("timelapse"),
            on_print_started=self.on_print_start,
            on_print_start_failed=self.on_print_start_failed,
            on_render_start=self.on_render_start,
            on_render_end=self.on_render_end,
            on_snapshot_start=self.on_snapshot_start,
            on_snapshot_end=self.on_snapshot_end,
            on_timelapse_stopping=self.on_timelapse_stopping,
            on_timelapse_stopped=self.on_timelapse_stopped,
            on_timelapse_end=self.on_timelapse_end,
            on_state_changed=self.on_timelapse_state_changed,
            on_timelapse_start=self.on_timelapse_start,
            on_snapshot_position_error=self.on_snapshot_position_error,
            on_position_error=self.on_position_error,
            on_plugin_message_sent=self.on_plugin_message_sent
        )

    def on_after_startup(self):
        try:
            self.load_settings()
            # create our initial timelapse object
            # create our timelapse object

            self.create_timelapse_object()
            self.Settings.current_debug_profile().log_info("Octolapse - loaded and active.")
        except Exception as e:
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))
            raise

    # Event Mixin Handler

    def on_event(self, event, payload):

        try:
            # If we haven't loaded our settings yet, return.
            if self.Settings is None or self.Timelapse is None:
                return

            self.Settings.current_debug_profile().log_print_state_change(
                "Printer event received:{0}.".format(event))

            if event == Events.PRINT_STARTED:
                # warn and cancel print if not printing locally
                if not self.Settings.is_octolapse_enabled:
                    return

                if (
                    payload["origin"] != "local"
                ):
                    self.Timelapse.end_timelapse("FAILED")
                    self.send_popup_error(
                        "Octolapse does not work when printing from SD the card.  Disable octolapse if you want to "
                        "print from the SD card.  Cancelling print")
                    self.Settings.current_debug_profile().log_print_state_change(
                        "Octolapse cannot start the timelapse when printing from SD."
                    )
                    self._printer.cancel_print()
                    return
            if event == Events.PRINTER_STATE_CHANGED:
                self.send_state_changed_message({"Status": self.get_status_dict()})
            if event == Events.CONNECTIVITY_CHANGED:
                self.send_state_changed_message({"Status": self.get_status_dict()})
            if event == Events.CLIENT_OPENED:
                self.send_state_changed_message({"Status": self.get_status_dict()})
            if event == Events.POSITION_UPDATE:
                self.Timelapse.on_position_received(payload)
            elif event == Events.DISCONNECTING:
                self.on_printer_disconnecting()
            elif event == Events.DISCONNECTED:
                self.on_printer_disconnected()
            elif event == Events.PRINT_PAUSED:
                self.on_print_paused()
            elif event == Events.HOME:
                self.Settings.current_debug_profile().log_print_state_change(
                    "homing to payload:{0}.".format(payload))
            elif event == Events.PRINT_RESUMED:
                self.on_print_resumed()
            elif event == Events.PRINT_FAILED:
                self.on_print_failed()
            elif event == Events.PRINT_CANCELLING:
                self.on_print_cancelling()
            elif event == Events.PRINT_CANCELLED:
                self.on_print_canceled()
            elif event == Events.PRINT_DONE:
                self.on_print_completed()
        except Exception as e:
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))

    def on_print_resumed(self):
        self.Settings.current_debug_profile().log_print_state_change("Print Resumed.")
        self.Timelapse.on_print_resumed()

    def on_print_paused(self):
        self.Timelapse.on_print_paused()

    def on_print_start(self, tags):
        self.Settings.current_debug_profile().log_print_state_change(
            "Print start detected, attempting to start timelapse."
        )

        if not self.Settings.is_octolapse_enabled:
            self.Settings.current_debug_profile().log_print_state_change("Octolapse is disabled.")
            return

        # determine the file source
        printer_data = self._printer.get_current_data()
        current_job = printer_data.get("job", None)
        if not current_job:
            message = "An unexpected error occurred:" \
                      "  Octolapse was unable to acquire job start information from Octoprint." \
                      "  Please see octolapse_log for details.  Cancelling Print."
            self.on_print_cancelled(message, True)

            log_message = "Failed to get current job data on_print_start:" \
                          "  Current printer data: {0}".format(printer_data)
            self.Settings.current_debug_profile().log_error(log_message)
            return

        current_file = current_job.get("file", None)
        if not current_file:
            message = "An unexpected error occurred:" \
                      "  Octolapse was unable to acquire file information from the current job." \
                      "  Please see octolapse_log for details.  Cancelling Print."

            self.on_print_cancelled(message, True)
            log_message = "Failed to get current file data on_print_start:" \
                          "  Current job data: {0}".format(current_job)
            self.Settings.current_debug_profile().log_error(log_message)
            return

        current_origin = current_file.get("origin", "unknown")
        if not current_origin:
            message = "An unexpected error occurred:" \
                      "  Octolapse was unable to acquire the current origin information from the current file." \
                      "  Please see octolapse_log for details.  Cancelling Print."
            self.on_print_cancelled(message, True)
            log_message = "Failed to get current origin data on_print_start:" \
                "Current file data: {0}".format(current_file)

            self.Settings.current_debug_profile().log_error(log_message)
            return

        if current_origin != "local":
            message = "Octolapse only works when printing locally.  The current source ({0}) is incompatible.  " \
                      "Disable octolapse if you want to print from the SD card." \
                      "  Cancelling print".format(current_origin)
            self.on_print_cancelled(message, True)
            log_message = "Unable to start Octolapse when printing from {0}.  Cancelling print.".format(current_origin)
            self.Settings.current_debug_profile().log_warning(log_message)
            return

        if self.Timelapse.State != TimelapseState.Initializing:
            message = "Unable to start the timelapse when not in the Initializing state. StateId: " \
                      "{0}".format(self.Timelapse.State)
            self.on_print_cancelled(message, True)
            return

        result = self.start_timelapse()
        if not result["success"]:
            message = "Unable to start the timelapse.  Canceling print.  {0}: {1}".format("Error", result["error"])
            self.on_print_cancelled(message, result["error"])
            return

        if result["warning"]:
            self.send_popup_message(result["warning"])

        self.Settings.current_debug_profile().log_print_state_change(
            "Print Started - Timelapse Started.")
        if (self.Settings.current_camera().apply_settings_before_print
            and self.Settings.current_camera().camera_type == "webcam"
        ):
            self.apply_camera_settings(self.Settings.current_camera())

    def on_print_cancelled(self, message, is_error):
        self._printer.cancel_print()
        self.Settings.current_debug_profile().log_print_state_change(message)
        if is_error:
            self.send_popup_error(message)
        else:
            self.send_popup_message(message)

    def on_print_start_failed(self, message):
        self.send_popup_error(message)
        self._printer.cancel_print()

    def start_timelapse(self):
        # check for version 1.3.7 min
        if not (LooseVersion(octoprint.server.VERSION) > LooseVersion("1.3.8")):
            return {'success': False,
                    'error': "Octolapse requires Octoprint v1.3.9 rc3 or above, but version v{0} is installed."
                             "  Please update Octoprint to use Octolapse.".format(octoprint.server.DISPLAY_VERSION),
                    'warning': False}
        try:
            ffmpeg_path = self._settings.settings.get(["webcam", "ffmpeg"])
            if self.Settings.current_rendering().enabled and ffmpeg_path == "":
                self.Settings.current_debug_profile().log_error(
                    "A timelapse was started, but there is no ffmpeg path set!")
                return {'success': False,
                        'error': "No ffmpeg path is set.  Please configure this setting within the Octoprint settings "
                                 "pages located at Features->Webcam & Timelapse under Timelapse Recordings->Path to "
                                 "FFMPEG.",
                        'warning': False}
        except Exception as e:
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))
            return {'success': False,
                    'error': "An exception occurred while trying to acquire the ffmpeg path from Octoprint.  Please "
                             "configure this setting within the Octoprint settings pages located at Features->Webcam "
                             "& Timelapse under Timelapse Recordings->Path to FFMPEG.",
                    'warning': False}
        if not os.path.isfile(ffmpeg_path):
            # todo:  throw some kind of exception
            return {'success': False,
                    'error': "The ffmpeg {0} does not exist.  Please configure this setting within the Octoprint "
                             "settings pages located at Features->Webcam & Timelapse under Timelapse Recordings->Path "
                             "to FFMPEG.".format(ffmpeg_path), 'warning': False}
        try:
            g90_influences_extruder = self._settings.settings.get(["feature", "g90InfluencesExtruder"])

        except Exception as e:
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))
            return {'success': False,
                    'error': "Unable to extract the OctoPrint setting - g90_influences_extruder.", 'warning': False}

        # Check the rendering filename template
        if not render.is_rendering_template_valid(
            self.Settings.current_rendering().output_template,
            self.Settings.rendering_file_templates,
            self.get_plugin_data_folder()
        ):
            return {
                'success': False,
                'error': "The rendering file template is invalid.  Please correct the token"
                         " within the current rendering profile.",
                'warning': False}

        octoprint_printer_profile = self._printer_profile_manager.get_current()
        # check for circular bed.  If it exists, we can't continue:
        if octoprint_printer_profile["volume"]["formFactor"] == "circle":
            return {
                'success': False, 'error': "This plugin does not yet support circular beds, sorry.", 'warning': False
            }

        # make sure that at least one profile is available
        if len(self.Settings.printers) == 0:
            return {'success': False, 'error': "There are no printer profiles.  Cannot start timelapse.  "
                                               "Please create a printer profile in the octolapse settings pages and "
                                               "restart the print."}
        # check to make sure a printer is selected
        if self.Settings.current_printer() is None:
            return {'success': False, 'error': "No default printer profile was selected.  Cannot start timelapse.  "
                                               "Please select a printer profile in the octolapse settings pages and "
                                               "restart the print."}

        # make sure at least one trigger is enabled
        current_snapshot = self.Settings.current_snapshot()
        if not (
            current_snapshot.layer_trigger_enabled or
            current_snapshot.timer_trigger_enabled or
            current_snapshot.gcode_trigger_enabled
        ):
            return {
                'success': False,
                'error': "No triggers are enabled in the current snapshot profile.  Cannot start timelapse."
            }

        if self.Settings.current_camera().camera_type == "webcam":
            # test the camera and see if it works.
            results = camera.test_camera(self.Settings.current_camera())
            if not results[0]:
                return {'success': False, 'warning': False,
                        'error': "The current camera profile did not pass testing.  You can "
                                 "adjust and test your camera in the profile settings page."}

        self.Timelapse.start_timelapse(
            self.Settings, octoprint_printer_profile, ffmpeg_path, g90_influences_extruder)

        if octoprint_printer_profile["volume"]["origin"] != "lowerleft":
            return {'success': True,
                    'warning': "This plugin has not yet been tested on printers with origins that are not in the lower "
                               "left.  Use at your own risk."}

        return {'success': True, 'warning': False}

    def send_popup_message(self, msg):
        self.send_plugin_message("popup", msg)

    def send_popup_error(self, msg):
        self.send_plugin_message("popup-error", msg)

    def send_state_changed_message(self, state):
        data = {
            "type": "state-changed"
        }
        data.update(state)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_settings_changed_message(self, client_id=""):
        data = {
            "type": "settings-changed",
            "client_id": client_id,
            "Status": self.get_status_dict(),
            "MainSettings": self.Settings.get_main_settings_dict()
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_plugin_message(self, message_type, msg):
        self._plugin_manager.send_plugin_message(
            self._identifier, dict(type=message_type, msg=msg))

    def send_render_start_message(self, msg):
        data = {
            "type": "render-start", "msg": msg, "Status": self.get_status_dict(),
            "MainSettings": self.Settings.get_main_settings_dict()
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_render_failed_message(self, msg):
        data = {
            "type": "render-failed", "msg": msg, "Status": self.get_status_dict(),
            "MainSettings": self.Settings.get_main_settings_dict()
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_render_end_message(self, success, synchronized, message="Octolapse is finished rendering a timelapse."):

        data = {
            "type": "render-end",
            "msg": message,
            "Status": self.get_status_dict(),
            "MainSettings": self.Settings.get_main_settings_dict(),
            "is_synchronized": synchronized,
            'success': success
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_render_complete_message(self):
        self._plugin_manager.send_plugin_message(self._identifier, dict(
            type="render-complete", msg="Octolapse has completed a rendering."))

    def on_timelapse_start(self, *args, **kwargs):
        state_data = self.Timelapse.to_state_dict()
        data = {
            "type": "timelapse-start", "msg": "Octolapse has started a timelapse.", "Status": self.get_status_dict(),
            "MainSettings": self.Settings.get_main_settings_dict()
        }
        data.update(state_data)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def on_timelapse_end(self, *args, **kwargs):
        self.send_state_changed_message({"Status": self.get_status_dict()})

    def on_position_error(self, message):
        state_data = self.Timelapse.to_state_dict()
        data = {
            "type": "position-error", "msg": message, "Status": self.get_status_dict(),
            "MainSettings": self.Settings.get_main_settings_dict()
        }
        data.update(state_data)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def on_plugin_message_sent(self, message_type, message):
        if message_type == "error":
            self.send_popup_error(message)
        else:
            self.send_plugin_message(message_type, message)

    def on_snapshot_position_error(self, message):
        state_data = self.Timelapse.to_state_dict()
        data = {
            "type": "out-of-bounds", "msg": message, "Status": self.get_status_dict(),
            "MainSettings": self.Settings.get_main_settings_dict()
        }
        data.update(state_data)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_state_loaded_message(self):
        data = {
            "type": "state-loaded",
            "msg": "The current state has been loaded.",
            "MainSettings": self.Settings.get_main_settings_dict(),
            "Status": self.get_status_dict(),
        }
        data.update(self.Timelapse.to_state_dict())
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def on_timelapse_complete(self):
        state_data = self.Timelapse.to_state_dict()
        data = {
            "type": "timelapse-complete", "msg": "Octolapse has completed the timelapse.",
            "Status": self.get_status_dict(), "MainSettings": self.Settings.get_main_settings_dict()
        }
        data.update(state_data)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def on_snapshot_start(self):
        state_data = self.Timelapse.to_state_dict()

        data = {
            "type": "snapshot-start", "msg": "Octolapse is taking a snapshot.", "Status": self.get_status_dict(),
            "MainSettings": self.Settings.get_main_settings_dict()
        }
        data.update(state_data)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def on_snapshot_end(self, *args, **kwargs):
        payload = args[0]

        status_dict = self.get_status_dict()
        success = payload["success"]
        error = payload["error"]
        data = {
            "type": "snapshot-complete", "msg": "Octolapse has completed the current snapshot.", "Status": status_dict,
            "MainSettings": self.Settings.get_main_settings_dict(), 'success': success, 'error': error

        }
        state_data = self.Timelapse.to_state_dict()
        data.update(state_data)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def on_apply_camera_settings_success(self, *args, **kwargs):
        setting_value = args[0]
        setting_name = args[1]
        template = args[2]
        self.Settings.current_debug_profile().log_camera_settings_apply(
            "Camera Settings - Successfully applied {0} to the {1} setting.  Template:{2}".format(setting_value,
                                                                                                  setting_name,
                                                                                                  template))

    def on_apply_camera_settings_fail(self, *args, **kwargs):
        setting_value = args[0]
        setting_name = args[1]
        template = args[2]
        error_message = args[3]
        self.Settings.current_debug_profile().log_camera_settings_apply(
            "Camera Settings - Unable to apply {0} to the {1} settings!  Template:{2}, Details:{3}"
                .format(setting_value, setting_name, template, error_message))

    def on_apply_camera_settings_complete(self, *args, **kwargs):
        self.Settings.current_debug_profile().log_camera_settings_apply(
            "Camera Settings - Completed")

    def on_print_failed(self):
        self.Timelapse.on_print_failed()
        self.Settings.current_debug_profile().log_print_state_change("Print failed.")

    def on_printer_disconnecting(self):
        self.Timelapse.on_print_disconnecting()
        self.Settings.current_debug_profile().log_print_state_change("Printer disconnecting.")

    def on_printer_disconnected(self):
        self.Timelapse.on_print_disconnected()
        self.Settings.current_debug_profile().log_print_state_change("Printer disconnected.")

    def on_print_cancelling(self):
        self.Settings.current_debug_profile().log_print_state_change("Print cancelling.")
        self.Timelapse.on_print_cancelling()

    def on_print_canceled(self):
        self.Settings.current_debug_profile().log_print_state_change("Print cancelled.")
        self.Timelapse.on_print_canceled()

    def on_print_completed(self):
        self.Timelapse.on_print_completed()
        self.Settings.current_debug_profile().log_print_state_change("Print completed.")

    def on_timelapse_stopping(self):

        self.send_plugin_message(
            "timelapse-stopping", "Waiting for a snapshot to complete before stopping the timelapse.")

    def on_timelapse_stopped(self, message, error):
        state_data = self.Timelapse.to_state_dict()

        if message is None:
            message = "Octolapse has been stopped for the remainder of the print.  Snapshots will be rendered after " \
                      "the print is complete. "

        if error:
            message_type = "timelapse-stopped-error"
        else:
            message_type = "timelapse-stopped"
        data = {
            "type": message_type,
            "msg": message,
            "Status": self.get_status_dict(),
            "MainSettings": self.Settings.get_main_settings_dict()
        }
        data.update(state_data)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def on_gcode_queuing(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        try:
            # only handle commands sent while printing
            if self.Timelapse is not None:
                return self.Timelapse.on_gcode_queuing(cmd, cmd_type, gcode, kwargs["tags"])
        except Exception as e:
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))

    def on_gcode_sending(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        try:
            if self.Timelapse is not None and self.Timelapse.is_timelapse_active():
                self.Timelapse.on_gcode_sending(cmd, cmd_type, gcode, kwargs["tags"])
        except Exception as e:
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))

    def on_gcode_sent(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        try:
            if self.Timelapse is not None and self.Timelapse.is_timelapse_active():
                self.Timelapse.on_gcode_sent(cmd, cmd_type, gcode, kwargs["tags"])
        except Exception as e:
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))

    def on_gcode_received(self, comm, line, *args, **kwargs):
        try:
            if self.Timelapse is not None and self.Timelapse.is_timelapse_active():
                self.Timelapse.on_gcode_received(comm, line, *args, **kwargs)
        except Exception as e:
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))
        return line

    def on_timelapse_state_changed(self, *args, **kwargs):
        state_change_dict = args[0]
        self.send_state_changed_message(state_change_dict)

    def on_render_start(self, *args, **kwargs):
        """Called when a timelapse has started being rendered.  Calls any callbacks OnRenderStart callback set in the
        constructor. """
        payload = args[0]
        assert (isinstance(payload, RenderingCallbackArgs))
        # Set a flag marking that we have not yet synchronized with the default Octoprint plugin, in case we do this
        # later.
        self.IsRenderingSynchronized = False
        # Generate a notification message
        msg = "Octolapse captured {0} frames in {1} seconds, and has started rendering your timelapse file.".format(
            payload.SnapshotCount, utility.seconds_to_hhmmss(payload.SecondsAddedToPrint))

        if payload.Synchronize:
            will_sync_message = "This timelapse will synchronized with the default timelapse module, and will be " \
                                "available within the default timelapse plugin as '{0}' after rendering is " \
                                "complete.".format(payload.get_synchronization_filename())
        else:
            will_sync_message = "Due to your rendering settings, this timelapse will NOT be synchronized with the " \
                                "default timelapse module.  You will be able to find on your octoprint server" \
                                " here:<br/>{0}".format(payload.get_rendering_path())

        message = "{0}{1}".format(msg, will_sync_message)
        # send a message to the client
        self.send_render_start_message(message)

    def on_render_end(self, *args, **kwargs):
        """Called after all rendering and synchronization attemps are complete."""
        payload = args[0]
        assert (isinstance(payload, RenderingCallbackArgs))
        if payload.HasError:
            self.send_plugin_message("synchronize-failed", payload.ErrorMessage)
        else:
            if payload.Synchronize:
                # create a message that makes sense, since Octoprint will display its own popup message that already
                # contains text

                message = "from Octolapse has been synchronized and is now available within the default timelapse" \
                          "plugin tab as '{0}'.  Octolapse ".format(payload.get_synchronization_filename())
                # Here we create a special payload to notify the default timelapse plugin of a new timelapse
                octoprint_payload = dict(gcode="unknown",
                                         movie=payload.get_synchronization_path(),
                                         movie_basename=payload.get_synchronization_filename(),
                                         movie_prefix=message,
                                         returncode=payload.ReturnCode,
                                         reason=payload.Reason)
                # notify Octoprint using the event manager.  Is there a way to do this that is more in the
                # spirit of the API?
                eventManager().fire(Events.MOVIE_DONE, octoprint_payload)
                # we've either successfully rendered or rendered and synchronized
                self.send_render_end_message(True, True)
            else:
                message = "Octolapse has completed rendering a timelapse.  Due to your rendering settings," \
                          " the timelapse was not synchronized with the OctoPrint plugin." \
                          "  You should be able to find your video within your octoprint " \
                          " server here:<br/> '{0}'".format(payload.get_rendering_path())
                self.send_render_end_message(True, False, message)

    # ~~ AssetPlugin mixin
    def get_assets(self):
        self._logger.info("Octolapse is loading assets.")
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return dict(
            js=[
                "js/jquery.validate.min.js", "js/octolapse.js", "js/octolapse.settings.js",
                "js/octolapse.settings.main.js", "js/octolapse.profiles.js", "js/octolapse.profiles.printer.js",
                "js/octolapse.profiles.stabilization.js", "js/octolapse.profiles.snapshot.js",
                "js/octolapse.profiles.rendering.js", "js/octolapse.profiles.camera.js",
                "js/octolapse.profiles.debug.js", "js/octolapse.status.js"
            ],
            css=["css/octolapse.css"],
            less=["less/octolapse.less"])

    # ~~ software update hook
    def get_update_information(self):
        # get the checkout type from the software updater
        prerelease_channel = None
        is_prerelease = False
        # get this for reference.  Eventually I'll have to use it!
        # is the software update set to prerelease?

        if self._settings.settings.get(["plugins", "softwareupdate", "checks", "octoprint", "prerelease"]):
            # If it's a prerelease, look at the channel and configure the proper branch for Octolapse
            prerelease_channel = self._settings.settings.get(
                ["plugins", "softwareupdate", "checks", "octoprint", "prerelease_channel"]
            )
            if prerelease_channel == "rc/maintenance":
                is_prerelease = True
                prerelease_channel = "rc/maintenance"
            elif prerelease_channel == "rc/devel":
                is_prerelease = True
                prerelease_channel = "rc/devel"


        octolapse_info = dict(
            displayName="Octolapse",
            displayVersion=self._plugin_version,
            # version check: github repository
            type="github_release",
            user="FormerLurker",
            repo="Octolapse",
            current=self._plugin_version,
            branch="master",
            prerelease=is_prerelease,
            pip="https://github.com/FormerLurker/Octolapse/archive/{target_version}.zip",
            stable_branch=dict(branch="master", commitish=["master"], name="Stable"),
            prerelease_branches=[
                dict(
                    branch="rc/maintenance",
                    commitish=["rc/maintenance"],  # maintenance RCs
                    name="Maintenance RCs"
                ),
                dict(
                    branch="rc/devel",
                    commitish=["rc/maintenance", "rc/devel"],  # devel & maintenance RCs
                    name="Devel RCs"
                )
            ],
        )

        if prerelease_channel is not None:
            octolapse_info["prerelease_channel"] = prerelease_channel
        # return the update config
        return dict(
            octolapse=octolapse_info
        )

    def get_timelapse_extensions(*args, **kwargs):
        return ["mpg", "mpeg", "mp4", "m4v", "mkv", "gif", "avi", "flv", "vob"]

# If you want your plugin to be registered within OctoPrin#t under a different
# name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here.  Same goes for the
# other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties.  See the
# documentation for that.
__plugin_name__ = "Octolapse"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = OctolapsePlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.on_gcode_queuing,
        "octoprint.comm.protocol.gcode.sent": __plugin_implementation__.on_gcode_sent,
        "octoprint.comm.protocol.gcode.sending": __plugin_implementation__.on_gcode_sending,
        "octoprint.comm.protocol.gcode.received": __plugin_implementation__.on_gcode_received,
        "octoprint.timelapse.extensions": __plugin_implementation__.get_timelapse_extensions
    }
