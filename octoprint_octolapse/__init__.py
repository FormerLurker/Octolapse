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

import base64
import json
import os
import shutil
import flask
import octoprint.plugin
import octoprint.server
import octoprint_octolapse.settings_migration as settings_migration
import octoprint_octolapse.log as log
import octoprint.filemanager
import octoprint_octolapse.stabilization_preprocessing
import octoprint_octolapse.camera as camera
import octoprint_octolapse.render as render
import octoprint_octolapse.snapshot as snapshot
import octoprint_octolapse.utility as utility
from distutils.version import LooseVersion
from io import BytesIO
from octoprint.events import eventManager, Events
from octoprint.server import admin_permission
from octoprint.server.util.flask import restricted_access
from octoprint_octolapse.gcode_parser import Commands
from octoprint_octolapse.render import TimelapseRenderJob, RenderingCallbackArgs
from octoprint_octolapse.settings import OctolapseSettings, PrinterProfile, StabilizationProfile, CameraProfile, \
    RenderingProfile, SnapshotProfile, DebugProfile, SlicerPrintFeatures, \
    SlicerSettings, CuraSettings, OtherSlicerSettings, Simplify3dSettings, Slic3rPeSettings
from octoprint_octolapse.timelapse import Timelapse, TimelapseState
try:
    # noinspection PyCompatibility
    from urlparse import urlparse
except ImportError:
    # noinspection PyUnresolvedReferences
    from urllib.parse import urlparse


class OctolapsePlugin(octoprint.plugin.SettingsPlugin,
                      octoprint.plugin.AssetPlugin,
                      octoprint.plugin.TemplatePlugin,
                      octoprint.plugin.StartupPlugin,
                      octoprint.plugin.EventHandlerPlugin,
                      octoprint.plugin.BlueprintPlugin,
                      octoprint.plugin.RestartNeedingPlugin):
    TIMEOUT_DELAY = 1000
    _octolapse_settings = None  # type: OctolapseSettings
    _timelapse = None  # type: Timelapse

    def get_sorting_key(self, context=None):
        return 1

    def get_current_debug_profile_function(self):
        if self._octolapse_settings is not None:
            return self._octolapse_settings.profiles.current_debug_profile

    # Blueprint Plugin Mixin Requests

    @octoprint.plugin.BlueprintPlugin.route("/downloadTimelapse/<filename>", methods=["GET"])
    @restricted_access
    @admin_permission.require(403)
    def download_timelapse_request(self, filename):
        """Restricted access function to download a timelapse"""
        return self.get_download_file_response(self.get_timelapse_folder() + filename, filename)

    @octoprint.plugin.BlueprintPlugin.route("/snapshot", methods=["GET"])
    def snapshot_request(self):
        file_type = flask.request.args.get('file_type')
        guid = flask.request.args.get('camera_guid')

        """Public access function to get the latest snapshot image"""
        if file_type == 'snapshot':
            # get the latest snapshot image
            mime_type = 'image/jpeg'
            filename = utility.get_latest_snapshot_download_path(
                self.get_plugin_data_folder(), guid)
            if not os.path.isfile(filename):
                # we haven't captured any images, return the built in png.
                mime_type = 'image/png'
                filename = utility.get_no_snapshot_image_download_path(
                    self._basefolder)
        elif file_type == 'thumbnail':
            # get the latest snapshot image
            mime_type = 'image/jpeg'
            filename = utility.get_latest_snapshot_thumbnail_download_path(
                self.get_plugin_data_folder(), guid)
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

        self._timelapse.stop_snapshots()
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/saveMainSettings", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def save_main_settings_request(self):
        request_values = flask.request.get_json()
        self._octolapse_settings.main_settings.is_octolapse_enabled = request_values["is_octolapse_enabled"]
        self._octolapse_settings.main_settings.auto_reload_latest_snapshot = (
            request_values["auto_reload_latest_snapshot"]
        )
        self._octolapse_settings.main_settings.auto_reload_frames = request_values["auto_reload_frames"]
        self._octolapse_settings.main_settings.show_navbar_icon = request_values["show_navbar_icon"]
        self._octolapse_settings.main_settings.show_navbar_when_not_printing = (
            request_values["show_navbar_when_not_printing"]
        )
        self._octolapse_settings.main_settings.show_position_state_changes = (
            request_values["show_position_state_changes"]
        )
        self._octolapse_settings.main_settings.show_position_changes = request_values["show_position_changes"]
        self._octolapse_settings.main_settings.show_extruder_state_changes = (
            request_values["show_extruder_state_changes"]
        )
        self._octolapse_settings.main_settings.show_trigger_state_changes = request_values["show_trigger_state_changes"]
        self._octolapse_settings.main_settings.show_real_snapshot_time = request_values["show_real_snapshot_time"]
        self._octolapse_settings.main_settings.cancel_print_on_startup_error = (
            request_values["cancel_print_on_startup_error"]
        )
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
            self._timelapse is not None and
            self._timelapse.is_timelapse_active() and
            self._octolapse_settings.main_settings.is_octolapse_enabled and
            not enable_octolapse
        ):
            self.send_plugin_message(
                "disabled-running",
                "Octolapse will remain active until the current print ends."
                "  If you wish to stop the active timelapse, click 'Stop Timelapse'."
            )

        # save the updated settings to a file.
        self._octolapse_settings.main_settings.is_octolapse_enabled = enable_octolapse
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
            self._octolapse_settings.main_settings.show_position_state_changes = (
                not self._octolapse_settings.main_settings.show_position_state_changes
            )
        elif panel_type == "show_position_changes":
            self._octolapse_settings.main_settings.show_position_changes = (
                not self._octolapse_settings.main_settings.show_position_changes
            )
        elif panel_type == "show_extruder_state_changes":
            self._octolapse_settings.main_settings.show_extruder_state_changes = (
                not self._octolapse_settings.main_settings.show_extruder_state_changes
            )
        elif panel_type == "show_trigger_state_changes":
            self._octolapse_settings.main_settings.show_trigger_state_changes = (
                not self._octolapse_settings.main_settings.show_trigger_state_changes
            )
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
        data.update(self._octolapse_settings.main_settings.to_dict())
        return json.dumps(data), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/loadState", methods=["POST"])
    def load_state_request(self):
        # TODO:  add a timer to wait for the settings to load!
        if self._octolapse_settings is None:
            raise Exception(
                "Unable to load values from Octolapse.Settings, it hasn't been initialized yet.  Please wait a few "
                "minutes and try again.  If the problem persists, please check plugin_octolapse.log for exceptions.")
        # TODO:  add a timer to wait for the timelapse to be initialized
        if self._timelapse is None:
            raise Exception(
                "Unable to load values from Octolapse.Timelapse, it hasn't been initialized yet.  Please wait a few "
                "minutes and try again.  If the problem persists, please check plugin_octolapse.log for exceptions.")
        self.send_state_loaded_message()
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/getPrintFeatures", methods=["POST"])
    def get_print_features(self):
        request_values = flask.request.get_json()
        client_slicer_settings = request_values["slicer_settings"]
        client_slicer_type = request_values["slicer_type"]

        slicer_settings = None
        speed_units = 'mm-min'
        if client_slicer_type == 'cura':
            slicer_settings = CuraSettings.create_from(client_slicer_settings)
            speed_units = 'mm-sec'
        elif client_slicer_type == 'other':
            slicer_settings = OtherSlicerSettings.create_from(client_slicer_settings)
            speed_units = slicer_settings.axis_speed_display_units
        elif client_slicer_type == 'simplify-3d':
            slicer_settings = Simplify3dSettings.create_from(client_slicer_settings)
        elif client_slicer_type == 'slic3r-pe':
            slicer_settings = Slic3rPeSettings.create_from(client_slicer_settings)

        # extract the slicer settings
        data = SlicerPrintFeatures(
            slicer_settings, self._octolapse_settings.profiles.current_snapshot()
        ).get_feature_dict(speed_units)

        if self._octolapse_settings is None:
            raise Exception(
                "Unable to load print features from Octolapse.Settings, it hasn't been initialized yet.  Please wait "
                "a few minutes and try again.  If the problem persists, please check plugin_octolapse.log for "
                "exceptions."
            )

        return json.dumps(data), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/addUpdateProfile", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def add_update_profile_request(self):
        try:
            request_values = flask.request.get_json()
            profile_type = request_values["profileType"]
            profile = request_values["profile"]
            client_id = request_values["client_id"]
            updated_profile = self._octolapse_settings.profiles.add_update_profile(profile_type, profile)
            # save the updated settings to a file.
            self.save_settings()
            self.send_settings_changed_message(client_id)
            return updated_profile.to_json(), 200, {'ContentType': 'application/json'}
        except Exception as e:
            self._logger.error("Error encountered in /addUpdateProfile.")
            self._logger.error(utility.exception_to_string(e))
        return {}, 500, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/removeProfile", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def remove_profile_request(self):
        request_values = flask.request.get_json()
        profile_type = request_values["profileType"]
        guid = request_values["guid"]
        client_id = request_values["client_id"]
        if not self._octolapse_settings.profiles.remove_profile(profile_type, guid):
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
        self._octolapse_settings.profiles.set_current_profile(profile_type, guid)
        self.save_settings()
        self.send_settings_changed_message(client_id)
        return json.dumps({'success': True, 'guid': request_values["guid"]}), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/setCurrentCameraProfile", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def set_current_camera_profile(self):
        # this setting will only determine which profile will be the default within
        # the snapshot preview if a new instance is loaded.  Save the settings, but
        # do not notify other clients
        request_values = flask.request.get_json()
        guid = request_values["guid"]
        self._octolapse_settings.profiles.current_camera_profile_guid = guid
        self.save_settings()
        return json.dumps({'success': True, 'guid': request_values["guid"]}), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/restoreDefaults", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def restore_defaults_request(self):
        request_values = flask.request.get_json()
        client_id = request_values["client_id"]
        try:
            self.load_settings(force_defaults=True)
            self.send_settings_changed_message(client_id)

            return self._octolapse_settings.to_json(), 200, {'ContentType': 'application/json'}
        except Exception as e:
            if self._octolapse_settings is not None:
                self._octolapse_settings.Logger.log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))
        return json.dumps({'success': False}), 500, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/loadSettings", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def load_settings_request(self):
        return self._octolapse_settings.to_json(), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/testCameraSettingsApply", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def test_camera_settings_apply(self):
        request_values = flask.request.get_json()
        profile = request_values["profile"]
        camera_profile = CameraProfile.create_from(profile)
        try:
            camera.test_web_camera_image_preferences(camera_profile)
            return json.dumps({'success': True}, 200, {'ContentType': 'application/json'})
        except camera.CameraError as e:
            return json.dumps({'success': False, 'error': str(e)}, 200, {'ContentType': 'application/json'})

    @octoprint.plugin.BlueprintPlugin.route("/applyCameraSettings", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def apply_camera_settings_request(self):
        request_values = flask.request.get_json()
        profile = request_values["profile"]
        settings_type = request_values["settings_type"]
        camera_profile = CameraProfile.create_from(profile)
        success, errors = self.apply_camera_settings(
            camera_profile=camera_profile, force=True, settings_type=settings_type
        )
        if not success:
            self.send_plugin_message('camera-settings-error', errors)
        return json.dumps({'success': success}, 200, {'ContentType': 'application/json'})

    @octoprint.plugin.BlueprintPlugin.route("/testCamera", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def test_camera_request(self):
        request_values = flask.request.get_json()
        profile = request_values["profile"]
        camera_profile = CameraProfile.create_from(profile)
        try:
            camera.test_web_camera(camera_profile)
            return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
        except camera.CameraError as e:
            self._octolapse_settings.Logger.log_error(e)
            return json.dumps({'success': False, 'error': str(e)}), 200, {'ContentType': 'application/json'}
        except Exception as e:
            self._octolapse_settings.Logger.log_error(e)
            raise e

    @octoprint.plugin.BlueprintPlugin.route("/toggleCamera", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def toggle_camera(self):
        request_values = flask.request.get_json()
        guid = request_values["guid"]
        client_id = request_values["client_id"]
        new_value = not self._octolapse_settings.profiles.cameras[guid].enabled
        self._octolapse_settings.profiles.cameras[guid].enabled = new_value
        self.save_settings()
        self.send_settings_changed_message(client_id)
        return json.dumps({'success': True, 'enabled': new_value}), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/validateRenderingTemplate", methods=["POST"])
    def validate_rendering_template(self):
        template = flask.request.form['output_template']
        result = render.is_rendering_template_valid(
            template,
            self._octolapse_settings.profiles.options.rendering["rendering_file_templates"]
        )
        if result[0]:
            valid = "true"
        else:
            valid = result[1]
        return "\"{0}\"".format(valid), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/validateOverlayTextTemplate", methods=["POST"])
    def validate_overlay_text_template(self):
        template = flask.request.form['overlay_text_template']
        result = render.is_overlay_text_template_valid(
            template,
            self._octolapse_settings.profiles.options.rendering["overlay_text_templates"]
        )
        if result[0]:
            valid = "true"
        else:
            valid = result[1]
        return "\"{0}\"".format(valid), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/rendering/font", methods=["GET"])
    @restricted_access
    @admin_permission.require(403)
    def get_available_fonts(self):
        font_list = utility.get_system_fonts()
        return json.dumps(font_list), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/rendering/previewOverlay", methods=["POST"])
    def preview_overlay(self):
        preview_image = None
        camera_image = None
        try:
            # Take a snapshot from the first active camera.
            active_cameras = self._octolapse_settings.profiles.active_cameras()

            if len(active_cameras) > 0:
                try:
                    camera_image = snapshot.take_in_memory_snapshot(self._octolapse_settings, active_cameras[0])
                except Exception as e:
                    self._logger.warning("Failed to take a snapshot. Falling back to solid color.")
                    self._logger.warning(str(e))

            # Extract the profile from the request.
            try:
                rendering_profile = RenderingProfile().create_from(flask.request.form)
            except Exception as e:
                self._logger.error('Preview overlay request did not provide valid Rendering profile.')
                self._logger.error(str(e))
                return json.dumps({
                    'error': 'Request did not contain valid Rendering profile. Check octolapse log for details.'
                }), 400, {}

            # Render a preview image.
            preview_image = render.preview_overlay(rendering_profile, image=camera_image)

            if preview_image is None:
                return json.dumps({'success': False}), 404, {'ContentType': 'application/json'}

            # Use a buffer to base64 encode the image.
            img_io = BytesIO()
            preview_image.save(img_io, 'JPEG')
            img_io.seek(0)
            base64_encoded_image = base64.b64encode(img_io.getvalue())

            # Return a response. We have to return JSON because jQuery only knows how to parse JSON.
            return json.dumps({'image': base64_encoded_image}), 200, {'ContentType': 'application/json'}
        finally:
            # cleanup
            if camera_image is not None:
                camera_image.close()
            if preview_image is not None:
                preview_image.close()

    @octoprint.plugin.BlueprintPlugin.route("/rendering/watermark", methods=["GET"])
    @restricted_access
    @admin_permission.require(403)
    def get_available_watermarks(self):
        # TODO(Shadowen): Retrieve watermarks_directory_name from config.yaml.
        watermarks_directory_name = "watermarks"
        full_watermarks_dir = os.path.join(self.get_plugin_data_folder(), watermarks_directory_name)
        files = []
        if os.path.exists(full_watermarks_dir):
            files = [
                os.path.join(
                    self.get_plugin_data_folder(), watermarks_directory_name, f
                ) for f in os.listdir(full_watermarks_dir)
            ]
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

    def apply_camera_settings(self, camera_profile=None, force=False, settings_type=None):

        if camera_profile is not None:
            camera_control = camera.CameraControl([camera_profile])
        else:
            camera_control = camera.CameraControl(self._octolapse_settings.profiles.cameras.values())

        success, errors = camera_control.apply_settings(force, settings_type)
        if not success:
            error_message = "There were {0} errors while applying custom camera settings/scripts:".format(len(errors))
            error_message += "\n{0}".format(errors[0])
            if len(errors) > 1:
                error_message += "\n+ {0} more errors.  See plugin_octolapse.log for details.".format(len(errors)-1)
            for error in errors:
                self._octolapse_settings.Logger.log_error(error)
            return False, error_message
        else:
            self._octolapse_settings.Logger.log_camera_settings_apply("Camera settings applied without error.")
            return True, None

    def get_timelapse_folder(self):
        return utility.get_rendering_directory_from_data_directory(self.get_plugin_data_folder())

    def get_default_settings_path(self):
        return os.path.join(self.get_default_settings_folder(), "settings_default.json")

    def get_default_settings_folder(self):
        return os.path.join(self._basefolder, 'data')

    def get_settings_file_path(self):
        return os.path.join(self.get_plugin_data_folder(), "settings.json")

    def get_log_file_path(self):
        return self._settings.get_plugin_logfile_path()

    def load_settings(self, force_defaults=False):
        create_new_settings = False
        settings_upgraded = False
        if not os.path.isfile(self.get_settings_file_path()) or force_defaults:
            # create new settings from default setting file
            new_settings = OctolapseSettings.load(
                self.get_default_settings_path(),
                self.get_log_file_path(),
                self._logger,
                self._plugin_version,
                self.get_current_debug_profile_function
            )
            if self._octolapse_settings is not None:
                self._octolapse_settings.update(new_settings.to_dict())
            else:
                self._octolapse_settings = new_settings
            self._octolapse_settings.Logger.log_settings_load(
                "Creating new settings file from defaults.")
            create_new_settings = True
        else:
            # Load settings from file
            if self._octolapse_settings is not None:
                self._octolapse_settings.Logger.log_settings_load(
                    "Loading existings settings file from: {0}.".format(self.get_settings_file_path()))
            else:
                self._logger.info("Loading existing settings file from: {0}.".format(
                    self.get_settings_file_path())
                )
            # ToDo - Add settings migration calls to OcotlapseSettings.load
            with open(self.get_settings_file_path()) as settingsJson:
                data = json.load(settingsJson)
                # do the settings need to be migrated?
                if "version" in data and LooseVersion(data["version"]) != LooseVersion(self._plugin_version):
                    data = settings_migration.migrate_settings(
                        self._plugin_version, data, self.get_log_file_path(), self.get_default_settings_folder()
                    )
                    # No file existed, so we must have created default settings.  Save them!
                    settings_upgraded = True
                if self._octolapse_settings is None:
                    #  create a new settings object
                    self._octolapse_settings = OctolapseSettings.create_from_iterable(
                        self.get_log_file_path(),
                        self._logger,
                        self._plugin_version,
                        data,
                        get_debug_function=self.get_current_debug_profile_function
                    )
                    self._octolapse_settings.Logger.log_settings_load("Settings loaded.")
                else:
                    # update an existing settings object
                    self._octolapse_settings.Logger.log_settings_load(
                        "Settings loaded.  Updating existing settings object."
                    )
                    self._octolapse_settings.update(data)
        # Extract any settings from octoprint that would be useful to our users.
        self.copy_octoprint_default_settings(
            apply_to_current_profile=create_new_settings)

        if create_new_settings or settings_upgraded:
            # No file existed, so we must have created default settings.  Save them!
            self.save_settings()

        return self._octolapse_settings.to_dict()

    def copy_octoprint_default_settings(self, apply_to_current_profile=False):
        try:
            # move some octoprint defaults if they exist for the webcam
            # specifically the address, the bitrate and the ffmpeg directory.
            # Attempt to get the camera address and snapshot template from Octoprint settings
            snapshot_url = self._settings.global_get(["webcam", "snapshot"])

            # we are doing some templating so we have to try to separate the
            # camera base address from the querystring.  This will probably not work
            # for all cameras.
            try:
                o = urlparse(snapshot_url)
                camera_address = o.scheme + "://" + o.netloc + o.path
                self._octolapse_settings.Logger.log_settings_load(
                    "Setting octolapse camera address to {0}.".format(camera_address))
                snapshot_action = urlparse(snapshot_url).query
                snapshot_request_template = "{camera_address}?" + snapshot_action
                self._octolapse_settings.Logger.log_settings_load(
                    "Setting octolapse camera snapshot template to {0}.".format(snapshot_request_template))
                self._octolapse_settings.profiles.defaults.camera.address = camera_address
                self._octolapse_settings.profiles.defaults.camera.snapshot_request_template = snapshot_request_template
                if apply_to_current_profile:
                    for profile in self._octolapse_settings.profiles.cameras.values():
                        profile.address = camera_address
                        profile.snapshot_request_template = snapshot_request_template
            except Exception as e:
                # cannot send a popup yet,because no clients will be connected.  We should write a routine that
                # checks to make sure Octolapse is correctly configured if it is enabled and send some kind of
                # message on client connect. self.SendPopupMessage("Octolapse was unable to extract the default
                # camera address from Octoprint.  Please configure your camera address and snapshot template before
                # using Octolapse.")

                self._octolapse_settings.Logger.log_exception(e)

            bitrate = self._settings.global_get(["webcam", "bitrate"])
            self._octolapse_settings.profiles.defaults.rendering.bitrate = bitrate
            if apply_to_current_profile:
                for profile in self._octolapse_settings.profiles.renderings.values():
                    profile.bitrate = bitrate
        except Exception as e:
            if self._octolapse_settings is not None:
                self._octolapse_settings.Logger.log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))
            raise e

    def save_settings(self):
        # Save setting from file
        self._octolapse_settings.Logger.log_settings_save(
            "Saving Settings.")
        try:
            settings_dict = self._octolapse_settings.save(self.get_settings_file_path())
            self._octolapse_settings.Logger.log_settings_save(
                "Settings saved.".format(settings_dict))
        except Exception as e:
            if self._octolapse_settings is not None:
                self._octolapse_settings.Logger.log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))
            raise e
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
        return None

    def get_status_dict(self):
        try:
            is_timelapse_active = False
            snapshot_count = 0
            total_snapshot_time = 0
            is_taking_snapshot = False
            is_rendering = False
            current_timelapse_state = TimelapseState.Idle
            is_waiting_to_render = False
            profiles_dict = self._octolapse_settings.profiles.get_profiles_dict()
            debug_dict = profiles_dict["debug"]
            if self._timelapse is not None:
                snapshot_count = self._timelapse.get_snapshot_count()
                total_snapshot_time = self._timelapse.SecondsAddedByOctolapse
                is_timelapse_active = self._timelapse.is_timelapse_active()
                if is_timelapse_active:
                    profiles_dict = self._timelapse.get_current_profiles()

                # Always get the current debug settings, else they won't update from the tab while a timelapse is
                # running.
                profiles_dict["current_debug_profile_guid"] = (
                    self._octolapse_settings.profiles.current_debug_profile_guid
                )
                profiles_dict["debug_profiles"] = debug_dict
                # always get the latest current camera profile guid.
                profiles_dict["current_camera_profile_guid"] = (
                    self._octolapse_settings.profiles.current_camera_profile_guid
                )

                is_rendering = self._timelapse.get_is_rendering()
                current_timelapse_state = self._timelapse.get_current_state()
                is_taking_snapshot = TimelapseState.TakingSnapshot == current_timelapse_state

                is_waiting_to_render = (not is_rendering) and current_timelapse_state == TimelapseState.WaitingToRender
            return {
                'snapshot_count': snapshot_count,
                'total_snapshot_time': total_snapshot_time,
                'current_snapshot_time': 0,
                'is_timelapse_active': is_timelapse_active,
                'is_taking_snapshot': is_taking_snapshot,
                'is_rendering': is_rendering,
                'waiting_to_render': is_waiting_to_render,
                'state': current_timelapse_state,
                'profiles': profiles_dict
            }
        except Exception as e:
            if self._octolapse_settings is not None:
                self._octolapse_settings.Logger.log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))
        return None

    def get_template_configs(self):
        self._logger.info("Octolapse - is loading template configurations.")
        return [dict(type="settings", custom_bindings=True)]

    def create_timelapse_object(self):
        self._timelapse = Timelapse(
            self._octolapse_settings,
            self._printer,
            self.get_plugin_data_folder(),
            self._settings.settings.getBaseFolder("timelapse"),
            on_print_started=self.on_print_start,
            on_print_start_failed=self.on_print_start_failed,
            on_render_start=self.on_render_start,
            on_render_success=self.on_render_success,
            on_render_error=self.on_render_error,
            on_snapshot_start=self.on_snapshot_start,
            on_snapshot_end=self.on_snapshot_end,
            on_new_thumbnail_available=self.on_new_thumbnail_available,
            on_timelapse_stopping=self.on_timelapse_stopping,
            on_timelapse_stopped=self.on_timelapse_stopped,
            on_timelapse_end=self.on_timelapse_end,
            on_state_changed=self.on_timelapse_state_changed,
            on_snapshot_position_error=self.on_snapshot_position_error,
            on_position_error=self.on_position_error,
            on_plugin_message_sent=self.on_plugin_message_sent
        )

    def on_after_startup(self):
        try:
            self.load_settings()
            # create a storage interface

            # create our timelapse object
            self.create_timelapse_object()
            self._octolapse_settings.Logger.log_info("Octolapse - loaded and active.")
        except Exception as e:
            if self._octolapse_settings is not None:
                self._octolapse_settings.Logger.log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))
            raise e

    # Event Mixin Handler

    def on_event(self, event, payload):

        try:
            # If we haven't loaded our settings yet, return.
            if self._octolapse_settings is None or self._timelapse is None:
                return

            self._octolapse_settings.Logger.log_print_state_change(
                "Printer event received:{0}.".format(event))

            if event == Events.PRINT_STARTED:
                # warn and cancel print if not printing locally
                if not self._octolapse_settings.main_settings.is_octolapse_enabled:
                    return

                if (
                    payload["origin"] != "local"
                ):
                    self._timelapse.end_timelapse("FAILED")
                    message = "Octolapse does not work when printing from SD the card."
                    self._octolapse_settings.Logger.log_print_state_change(
                        "Octolapse cannot start the timelapse when printing from SD."
                    )
                    self.on_print_start_failed(message)
                    return
            if event == Events.PRINTER_STATE_CHANGED:
                self.send_state_changed_message({"status": self.get_status_dict()})
            if event == Events.CONNECTIVITY_CHANGED:
                self.send_state_changed_message({"status": self.get_status_dict()})
            if event == Events.CLIENT_OPENED:
                self.send_state_changed_message({"status": self.get_status_dict()})
            elif event == Events.DISCONNECTING:
                self.on_printer_disconnecting()
            elif event == Events.DISCONNECTED:
                self.on_printer_disconnected()
            elif event == Events.PRINT_PAUSED:
                self.on_print_paused()
            elif event == Events.HOME:
                self._octolapse_settings.Logger.log_print_state_change(
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
            if self._octolapse_settings is not None:
                self._octolapse_settings.Logger.log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))

    def on_print_resumed(self):
        self._octolapse_settings.Logger.log_print_state_change("Print Resumed.")
        self._timelapse.on_print_resumed()

    def on_print_paused(self):
        self._timelapse.on_print_paused()

    def on_print_start(self):

        self._octolapse_settings.Logger.log_print_state_change(
            "Print start detected, attempting to start timelapse."
        )

        if not self._octolapse_settings.main_settings.is_octolapse_enabled:
            self._octolapse_settings.Logger.log_print_state_change("Octolapse is disabled.")
            return

        # see if the printer profile has been configured

        if not self._octolapse_settings.profiles.current_printer().has_been_saved_by_user:
            message = "Your Octolapse printer profile has not been configured.  Please copy your slicer settings" \
                      " into your printer profile and try again. "
            self.on_print_start_failed(message)
            return

        # determine the file source
        printer_data = self._printer.get_current_data()
        current_job = printer_data.get("job", None)
        if not current_job:
            message = "Octolapse was unable to acquire job start information from Octoprint." \
                      "  Please see octolapse_log for details.  Cancelling Print."
            self.on_print_start_failed(message)

            log_message = "Failed to get current job data on_print_start:" \
                          "  Current printer data: {0}".format(printer_data)
            self._octolapse_settings.Logger.log_error(log_message)
            return

        current_file = current_job.get("file", None)
        if not current_file:
            message = "Octolapse was unable to acquire file information from the current job." \
                      "  Please see octolapse_log for details."

            self.on_print_start_failed(message)
            log_message = "Failed to get current file data on_print_start:" \
                          "  Current job data: {0}".format(current_job)
            self._octolapse_settings.Logger.log_error(log_message)
            return

        current_origin = current_file.get("origin", "unknown")
        if not current_origin:
            message = "Octolapse was unable to acquire the current origin information from the current file." \
                      "  Please see octolapse_log for details."
            self.on_print_start_failed(message)
            log_message = "Failed to get current origin data on_print_start:" \
                "Current file data: {0}".format(current_file)

            self._octolapse_settings.Logger.log_error(log_message)
            return

        if current_origin != "local":
            message = "Octolapse only works when printing locally.  The current source ({0}) is incompatible.  " \
                      "Disable octolapse if you want to print from the SD card.".format(current_origin)
            self.on_print_start_failed(message)
            log_message = "Unable to start Octolapse when printing from {0}.".format(current_origin)
            self._octolapse_settings.Logger.log_warning(log_message)
            return

        if self._timelapse.get_current_state() != TimelapseState.Initializing:
            message = "Unable to start the timelapse when not in the Initializing state. StateId: " \
                      "{0}".format(self._timelapse.get_current_state())
            self.on_print_start_failed(message)
            return

        # test all cameras and look for at least one enabled camera
        found_camera = False
        for key in self._octolapse_settings.profiles.cameras:
            current_camera = self._octolapse_settings.profiles.cameras[key]
            if current_camera.enabled:
                found_camera = True
                if current_camera.camera_type == "webcam":
                    # test the camera and see if it works.

                    try:
                        camera.test_web_camera(current_camera)
                    except camera.CameraError as e:
                        self._octolapse_settings.Logger.log_exception(e)
                        self.on_print_start_failed(str(e))
                        return
                    except Exception as e:
                        self._octolapse_settings.Logger.log_exception(e)
                        message = "An unknown exception occurred while testing the '{0}' camera profile.  Check " \
                                  "plugin_octolapse.log for details.".format(current_camera.name)
                        self.on_print_start_failed(message)
                        raise e
        if not found_camera:
            message = "There are no enabled cameras.  Enable at least one camera profile and try again."
            self.on_print_start_failed(message)

        success, errors = self.apply_camera_settings(settings_type="web-request")
        if not success:
            message = "Octolapse could not apply custom image perferences to your webcam.  Please see <a " \
                      "href=\"https://github.com/FormerLurker/Octolapse/wiki/Camera-Profiles#custom-image-preferences" \
                      "\" target=\"_blank\">this link</a> for assistance with this error.  Details:" \
                      " {0}".format(errors)
            self.on_print_start_failed(message)
            return

        success, errors = self.apply_camera_settings(settings_type="script")
        if not success:
            message = "There were some errors running your custom camera initialization script.  Please correct your " \
                      "script and try again, or remove the initialization script from your camera profile. Error " \
                      "Details: {0}".format(errors)
            self.on_print_start_failed(message)
            return

        try:
            result = self.start_timelapse()
            if not result["success"]:
                self.on_print_start_failed(result["error"])
                return
            if result["warning"]:
                self.send_popup_message(result["warning"])
        except Exception as e:
            self._octolapse_settings.Logger.log_exception(e)
            self.send_popup_message("An unexpected error occurred while starting the Octolapse!  Please check "
                                    "plugin_octolapse.log for details")
            return

        # send G90/G91 if necessary, note that this must come before M82/M83 because sometimes G90/G91 affects
        # the extruder.
        if self._octolapse_settings.profiles.current_printer().xyz_axes_default_mode == 'force-absolute':
            # send G90
            self._printer.commands(['G90'], tags={"force_xyz_axis"})
        elif self._octolapse_settings.profiles.current_printer().xyz_axes_default_mode == 'force-relative':
            # send G91
            self._printer.commands(['G91'], tags={"force_xyz_axis"})
        # send G90/G91 if necessary
        if self._octolapse_settings.profiles.current_printer().e_axis_default_mode == 'force-absolute':
            # send M82
            self._printer.commands(['M82'], tags={"force_e_axis"})
        elif self._octolapse_settings.profiles.current_printer().e_axis_default_mode == 'force-relative':
            # send M83
            self._printer.commands(['M83'], tags={"force_e_axis"})

        self._octolapse_settings.Logger.log_print_state_change(
            "Print Started - Timelapse Started.")

        self.on_timelapse_start()

    def on_print_start_failed(self, error):
        if self._octolapse_settings.main_settings.cancel_print_on_startup_error:
            message = "Unable to start the timelapse.  Cancelling print.  Error:  {0}".format(error)
            self._printer.cancel_print(tags={'startup-failed'})
        else:
            message = "Unable to start the timelapse.  Continuing print without Octolapse.  Error: {0}".format(error)

        self._octolapse_settings.Logger.log_print_state_change(message)
        self.send_plugin_message("print-start-error", message)

    def start_timelapse(self):
        # check for version 1.3.7 min
        if not (LooseVersion(octoprint.server.VERSION) > LooseVersion("1.3.8")):
            return {'success': False,
                    'error': "Octolapse requires Octoprint v1.3.9 rc3 or above, but version v{0} is installed."
                             "  Please update Octoprint to use Octolapse.".format(octoprint.server.DISPLAY_VERSION),
                    'warning': False}

        # check the ffmpeg path
        try:
            ffmpeg_path = self._settings.global_get(["webcam", "ffmpeg"])
            if (
                self._octolapse_settings.profiles.current_rendering().enabled and
                (ffmpeg_path == "" or ffmpeg_path is None)
            ):
                self._octolapse_settings.Logger.log_error(
                    "A timelapse was started, but there is no ffmpeg path set!")
                return {'success': False,
                        'error': "No ffmpeg path is set.  Please configure this setting within the Octoprint settings "
                                 "pages located at Features->Webcam & Timelapse under Timelapse Recordings->Path to "
                                 "FFMPEG.",
                        'warning': False}
        except Exception as e:
            if self._octolapse_settings is not None:
                self._octolapse_settings.Logger.log_exception(e)
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
            g90_influences_extruder = self._settings.global_get(["feature", "g90_influences_extruder"])

        except Exception as e:
            if self._octolapse_settings is not None:
                self._octolapse_settings.Logger.log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))
            return {'success': False,
                    'error': "Unable to extract the OctoPrint setting - g90_influences_extruder.", 'warning': False}

        # Check the rendering filename template
        if not render.is_rendering_template_valid(
            self._octolapse_settings.profiles.current_rendering().output_template,
            self._octolapse_settings.profiles.options.rendering['rendering_file_templates'],
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
        if len(self._octolapse_settings.profiles.printers) == 0:
            return {'success': False, 'error': "There are no printer profiles.  Cannot start timelapse.  "
                                               "Please create a printer profile in the octolapse settings pages and "
                                               "restart the print."}
        # check to make sure a printer is selected
        if self._octolapse_settings.profiles.current_printer() is None:
            return {'success': False, 'error': "No default printer profile was selected.  Cannot start timelapse.  "
                                               "Please select a printer profile in the octolapse settings pages and "
                                               "restart the print."}
        gcode_file_path = None
        path = utility.get_currently_printing_file_path(self._printer)
        if path is not None:
            gcode_file_path = self._file_manager.path_on_disk(octoprint.filemanager.FileDestinations.LOCAL, path)

        # Create a copy of the settings to send to the Timelapse object.
        # We make this copy here so that editing settings vis the GUI won't affect the
        # current timelapse.
        settings_clone = self._octolapse_settings.clone()
        current_printer_clone = settings_clone.profiles.current_printer()
        has_automatic_settings_issue = False
        automatic_settings_error = None

        if current_printer_clone.slicer_type == 'automatic':
            # extract any slicer settings if possible.  This must be done before any calls to the printer profile
            # info that includes slicer setting
            if gcode_file_path is None:
                return {
                    'success': False,
                    'error': "Octolapse was unable to determine the path of the currently printing file.",
                }
            success, error_type, error_list = current_printer_clone.get_gcode_settings_from_file(gcode_file_path)
            if success:
                settings_saved = False
                if not current_printer_clone.slicers.automatic.disable_automatic_save:
                    # get the extracted slicer settings
                    extracted_slicer_settings = current_printer_clone.get_current_slicer_settings()
                    # Apply the extracted settings to to the live settings
                    self._octolapse_settings.profiles.current_printer().get_slicer_settings_by_type(
                        current_printer_clone.slicer_type
                    ).update(extracted_slicer_settings.to_dict())
                    # save the live settings
                    self.save_settings()
                    settings_saved = True

                self.send_slicer_settings_detected_message(settings_saved)
            else:
                if not current_printer_clone.slicers.automatic.continue_on_failure:
                    # If you are using Cura, see this link:  TODO:  ADD LINK TO CURA FEATURE TEMPLATE AND INSTRUCTIONS
                    if error_type == "no-settings-detected":
                        return {
                            'success': False,
                            'error': "No settings could be extracted from the gcode file.  Please check the gcode "
                                     "file for issues.",
                        }
                    else:
                        return {
                            'success': False,
                            'error': "Some required settings are missing: " + ",".join(error_list),
                        }
                else:
                    has_automatic_settings_issue = True
                    if error_type == "no-settings-detected":
                        automatic_settings_error = "Automatic settings extraction failed - No settings found in gcode"\
                                                   " file - Continue on failure is enabled so your print will"\
                                                   " continue, but the timelapse has been aborted."
                    else:
                        automatic_settings_error = "Automatic settings extraction failed - Required settings could not"\
                                                   " be found : " + ",".join(error_list) + "Continue on failure is" \
                                                   " enabled so your print will continue, but the timelapse has been" \
                                                   " aborted."
        else:
            # see if the current printer profile is missing any required settings
            # it is important to check here in case automatic slicer settings extraction
            # isn't used.
            slicer_settings = settings_clone.profiles.current_printer().get_current_slicer_settings()
            missing_settings = slicer_settings.get_missing_gcode_generation_settings()
            if len(missing_settings) > 0:
                return {
                    'success': False,
                    'error': "Unable to start the print.  Some required slicer settings are missing or corrupt: " +
                             ",".join(missing_settings)
                }

        current_stabilization_clone = settings_clone.profiles.current_stabilization()

        snapshot_plans = None
        if current_stabilization_clone.stabilization_type == StabilizationProfile.STABILIZATION_TYPE_PRE_CALCULATED:
            # pre-process the stabilization
            preprocess_results = self.pre_process_stabilization(
                current_stabilization_clone, current_printer_clone, octoprint_printer_profile, gcode_file_path)
            snapshot_plans = preprocess_results["snapshot_plans"]

        self._timelapse.start_timelapse(
            settings_clone, octoprint_printer_profile, ffmpeg_path, g90_influences_extruder, gcode_file_path,
            snapshot_plans=snapshot_plans)

        warning = ''
        if octoprint_printer_profile["volume"]["origin"] != "lowerleft":
            warning = "This plugin has not yet been tested on printers with origins that are not in the lower " \
                       "left.  Use at your own risk."

        if has_automatic_settings_issue:
            if len(warning) > 0:
                warning = warning + "  "
            warning = warning + automatic_settings_error

        if len(warning) == 0:
            warning = False

        return {'success': True, 'warning': warning}

    def pre_process_stabilization(self, stabilization, printer, octoprint_printer_profile, gcode_file_path):
        snapshot_plan = None
        preprocessor = None
        if (
            stabilization.pre_calculated_stabilization_type ==
            StabilizationProfile.LOCK_TO_PRINT_CORNER_STABILIZATION
        ):
            bounding_box = None
            if printer.restrict_snapshot_area:
                bounding_box = (
                    printer.snapshot_min_x,
                    printer.snapshot_max_x,
                    printer.snapshot_min_y,
                    printer.snapshot_max_y,
                    printer.snapshot_min_z,
                    printer.snapshot_max_z
                )

            snapshot_gcode_settings = printer.gcode_generation_settings
            retraction_length = (
                0 if not snapshot_gcode_settings.retract_before_move else snapshot_gcode_settings.retraction_length
            )
            z_lift_height = (
                0 if not snapshot_gcode_settings.lift_when_retracted else snapshot_gcode_settings.z_lift_height
            )

            preprocessor = octoprint_octolapse.stabilization_preprocessing.NearestToPrintPreprocessor(
                self._octolapse_settings.Logger,
                printer,
                None,
                octoprint_printer_profile,
                False,
                retraction_distance=0 if stabilization.lock_to_corner_disable_retract else retraction_length,
                z_lift_height=0 if stabilization.lock_to_corner_disable_z_lift else z_lift_height,
                nearest_to=stabilization.lock_to_corner_type,
                favor_axis=stabilization.lock_to_corner_favor_axis,
                height_increment=stabilization.lock_to_corner_height_increment,
                bounding_box=bounding_box,
                update_progress_callback=self.send_pre_processing_message
            )

        if preprocessor is not None:
            self.send_pre_processing_message(0)
            snapshot_plan = preprocessor.process_file(gcode_file_path)

        return snapshot_plan

    def send_pre_processing_message(self, percent_finished, time_elapsed=0, lines_processed=0):
        data = {
            "type": "gcode-pre-processing-update",
            "percent_finished": percent_finished,
            "time_elapsed": time_elapsed,
            "lines_processed": lines_processed
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

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
            "status": self.get_status_dict(),
            "main_settings": self._octolapse_settings.main_settings.to_dict()
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_slicer_settings_detected_message(self, settings_saved):
        data = {
            "type": "slicer_settings_detected",
            "saved": settings_saved
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_plugin_message(self, message_type, msg):
        self._plugin_manager.send_plugin_message(
            self._identifier, dict(type=message_type, msg=msg))

    def send_render_start_message(self, msg):
        data = {
            "type": "render-start", "msg": msg, "status": self.get_status_dict(),
            "main_settings": self._octolapse_settings.main_settings.to_dict()
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_render_failed_message(self, msg):
        data = {
            "type": "render-failed", "msg": msg, "status": self.get_status_dict(),
            "main_settings": self._octolapse_settings.main_settings.to_dict()
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_render_end_message(self, success, synchronized, message="Octolapse is finished rendering a timelapse."):

        data = {
            "type": "render-end",
            "msg": message,
            "status": self.get_status_dict(),
            "main_settings": self._octolapse_settings.main_settings.to_dict(),
            "is_synchronized": synchronized,
            'success': success
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_render_complete_message(self):
        self._plugin_manager.send_plugin_message(self._identifier, dict(
            type="render-complete", msg="Octolapse has completed a rendering."))

    def on_timelapse_start(self):
        state_data = self._timelapse.to_state_dict()
        data = {
            "type": "timelapse-start", "msg": "Octolapse has started a timelapse.", "status": self.get_status_dict(),
            "main_settings": self._octolapse_settings.main_settings.to_dict()
        }
        data.update(state_data)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def on_timelapse_end(self):
        state_data = self._timelapse.to_state_dict()
        data = {
            "type": "timelapse-complete", "msg": "Octolapse has completed a timelapse.",
            "status": self.get_status_dict(),
            "main_settings": self._octolapse_settings.main_settings.to_dict()
        }
        data.update(state_data)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def on_position_error(self, message):
        state_data = self._timelapse.to_state_dict()
        data = {
            "type": "position-error", "msg": message, "status": self.get_status_dict(),
            "main_settings": self._octolapse_settings.main_settings.to_dict()
        }
        data.update(state_data)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def on_plugin_message_sent(self, message_type, message):
        if message_type == "error":
            self.send_popup_error(message)
        else:
            self.send_plugin_message(message_type, message)

    def on_snapshot_position_error(self, message):
        state_data = self._timelapse.to_state_dict()
        data = {
            "type": "out-of-bounds", "msg": message, "status": self.get_status_dict(),
            "main_settings": self._octolapse_settings.main_settings.to_dict()
        }
        data.update(state_data)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_state_loaded_message(self):
        data = {
            "type": "state-loaded",
            "msg": "The current state has been loaded.",
            "main_settings": self._octolapse_settings.main_settings.to_dict(),
            "status": self.get_status_dict(),
        }
        data.update(self._timelapse.to_state_dict())
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def on_timelapse_complete(self):
        state_data = self._timelapse.to_state_dict()
        data = {
            "type": "timelapse-complete", "msg": "Octolapse has completed the timelapse.",
            "status": self.get_status_dict(), "main_settings": self._octolapse_settings.main_settings.to_dict()
        }
        data.update(state_data)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def on_snapshot_start(self):
        state_data = self._timelapse.to_state_dict()

        data = {
            "type": "snapshot-start", "msg": "Octolapse is taking a snapshot.", "status": self.get_status_dict(),
            "main_settings": self._octolapse_settings.main_settings.to_dict()
        }
        data.update(state_data)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def on_snapshot_end(self, *args):
        payload = args[0]
        status_dict = self.get_status_dict()
        success = payload["success"]
        error = payload["error"]
        snapshot_success = True
        snapshot_error = ""
        if "snapshot_payload" in payload:
            snapshot_payload = payload["snapshot_payload"]
            if snapshot_payload is not None:
                snapshot_success = snapshot_payload["success"]
                snapshot_error = snapshot_payload["error"]

        data = {
            "type": "snapshot-complete", "msg": "Octolapse has completed the current snapshot.", "status": status_dict,
            "main_settings": self._octolapse_settings.main_settings.to_dict(), 'success': success, 'error': error,
            "snapshot_success": snapshot_success, "snapshot_error": snapshot_error

        }
        state_data = self._timelapse.to_state_dict()
        data.update(state_data)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def on_new_thumbnail_available(self, guid):
        payload = {
            "type": "new-thumbnail-available",
            "guid": guid
        }
        self._plugin_manager.send_plugin_message(self._identifier, payload)

    def on_print_failed(self):
        self._timelapse.on_print_failed()
        self._octolapse_settings.Logger.log_print_state_change("Print failed.")

    def on_printer_disconnecting(self):
        self._timelapse.on_print_disconnecting()
        self._octolapse_settings.Logger.log_print_state_change("Printer disconnecting.")

    def on_printer_disconnected(self):
        self._timelapse.on_print_disconnected()
        self._octolapse_settings.Logger.log_print_state_change("Printer disconnected.")

    def on_print_cancelling(self):
        self._octolapse_settings.Logger.log_print_state_change("Print cancelling.")
        self._timelapse.on_print_cancelling()

    def on_print_canceled(self):
        self._octolapse_settings.Logger.log_print_state_change("Print cancelled.")
        self._timelapse.on_print_canceled()

    def on_print_completed(self):
        self._timelapse.on_print_completed()
        self._octolapse_settings.Logger.log_print_state_change("Print completed.")

    def on_timelapse_stopping(self):

        self.send_plugin_message(
            "timelapse-stopping", "Waiting for a snapshot to complete before stopping the timelapse.")

    def on_timelapse_stopped(self, message, error):
        state_data = self._timelapse.to_state_dict()

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
            "status": self.get_status_dict(),
            "main_settings": self._octolapse_settings.main_settings.to_dict()
        }
        data.update(state_data)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    # noinspection PyUnusedLocal
    def on_gcode_queuing(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        try:
            # only handle commands sent while printing
            if self._timelapse is not None and self._octolapse_settings.profiles.current_printer() is not None:
                # needed to handle non utf-8 characters
                cmd = cmd.encode('ascii', 'ignore')
                return self._timelapse.on_gcode_queuing(cmd, cmd_type, gcode, kwargs["tags"])
        except Exception as e:
            if self._octolapse_settings is not None:
                self._octolapse_settings.Logger.log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))

    # noinspection PyUnusedLocal
    def on_gcode_sending(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        try:
            if self._timelapse is not None and self._octolapse_settings.profiles.current_printer() is not None:
                # needed to handle non utf-8 characters
                cmd = cmd.encode('ascii', 'ignore')
                # we always want to send this event, else we may get stuck waiting for a position request!
                self._timelapse.on_gcode_sending(cmd, kwargs["tags"])
        except Exception as e:
            if self._octolapse_settings is not None:
                self._octolapse_settings.Logger.log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))

    # noinspection PyUnusedLocal
    def on_gcode_sent(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        try:
            if self._timelapse is not None and self._timelapse.is_timelapse_active():
                # needed to handle non utf-8 characters
                cmd = cmd.encode('ascii', 'ignore')
                self._timelapse.on_gcode_sent(cmd, cmd_type, gcode, kwargs["tags"])
        except Exception as e:
            if self._octolapse_settings is not None:
                self._octolapse_settings.Logger.log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))

    # noinspection PyUnusedLocal
    def on_gcode_received(self, comm, line, *args, **kwargs):
        try:
            if self._timelapse is not None and self._timelapse.is_timelapse_active():
                self._timelapse.on_gcode_received(line)
        except Exception as e:
            if self._octolapse_settings is not None:
                self._octolapse_settings.Logger.log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))
        return line

    def on_timelapse_state_changed(self, *args):
        state_change_dict = args[0]
        self.send_state_changed_message(state_change_dict)

    def on_render_start(self, payload):
        """Called when a timelapse has started being rendered.  Calls any callbacks OnRenderStart callback set in the
        constructor. """
        assert (isinstance(payload, RenderingCallbackArgs))
        # Set a flag marking that we have not yet synchronized with the default Octoprint plugin, in case we do this
        # later.
        # Generate a notification message
        job_message = ""
        if payload.TotalJobs > 1:
            job_message = "Rendering {0} of {1} for camera '{2}' - ".format(
                payload.JobNumber, payload.TotalJobs, payload.CameraName
            )

        if payload.SecondsAddedToPrint > 0:
            msg = "Octolapse captured {0} frames in {1} seconds and has started rendering your timelapse file.".format(
                payload.SnapshotCount, utility.seconds_to_hhmmss(payload.SecondsAddedToPrint))
        else:
            msg = "Octolapse captured {0} frames and has started rendering your timelapse file.".format(
                payload.SnapshotCount)

        if payload.Synchronize:
            will_sync_message = "This timelapse will synchronized with the default timelapse module, and will be " \
                                "available within the default timelapse plugin as '{0}' after rendering is " \
                                "complete.".format(payload.get_synchronization_filename())
        else:
            will_sync_message = "Due to your rendering settings, this timelapse will NOT be synchronized with the " \
                                "default timelapse module.  You will be able to find on your octoprint server" \
                                " here:<br/>{0}".format(payload.get_rendering_path())

        message = "{0}{1}{2}".format(job_message, msg, will_sync_message)
        # send a message to the client
        self.send_render_start_message(message)

    def on_render_success(self, payload):
        """Called after all rendering and synchronization attempts are complete."""
        assert (isinstance(payload, RenderingCallbackArgs))
        if payload.BeforeRenderError or payload.AfterRenderError:
            pre_post_render_message = "Rendering completed and was successful, but there were some script errors: "
            if payload.BeforeRenderError:
                pre_post_render_message += " The before script failed with the following error:" \
                                 "  {0}".format(payload.BeforeRenderError)
            if payload.AfterRenderError:
                pre_post_render_message += " The after script failed with the following error:" \
                                           "  {0}".format(payload.AfterRenderError)
            self.send_plugin_message('before-after-render-error', pre_post_render_message)

        if payload.Synchronize:
            # create a message that makes sense, since Octoprint will display its own popup message that already
            # contains text
            message = "from Octolapse for camera '{0}' has been synchronized and is now available within the default " \
                      "timelapse plugin tab as '{1}'.  Octolapse ".format(payload.CameraName,
                                                                          payload.get_synchronization_filename())
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
            message = "Octolapse has completed rendering a timelapse for camera '{0}'.  Due to your rendering " \
                      "settings, the timelapse was not synchronized with the OctoPrint plugin.  You should be able" \
                      " to find your video within your octoprint server here:<br/> '{1}'".format(
                        payload.CameraName,
                        payload.get_rendering_path()
                      )
            self.send_render_end_message(True, False, message)

    def on_render_error(self, payload, error):
        """Called after all rendering and synchronization attempts are complete."""
        assert (isinstance(payload, RenderingCallbackArgs))
        if payload.BeforeRenderError or payload.AfterRenderError:
            pre_post_render_message = "There were problems running the before/after rendering script: "
            if payload.BeforeRenderError:
                pre_post_render_message += " The before script failed with the following error:" \
                                 "  {0}".format(payload.BeforeRenderError)
            if payload.AfterRenderError:
                pre_post_render_message += " The after script failed with the following error:" \
                                           "  {0}".format(payload.AfterRenderError)
            self.send_plugin_message('before-after-render-error', pre_post_render_message)
        message = "Rendering failed for camera '{0}'.  {1}".format(payload.CameraName, error)
        self.send_plugin_message('render-failed', str(message))

    # ~~ AssetPlugin mixin
    def get_assets(self):
        self._logger.info("Octolapse is loading assets.")
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return dict(
            js=[
                "js/jquery.minicolors.min.js",
                "js/jquery.validate.min.js",
                "js/octolapse.js",
                "js/octolapse.settings.js",
                "js/octolapse.settings.main.js",
                "js/octolapse.profiles.js",
                "js/octolapse.profiles.printer.js",
                "js/octolapse.profiles.printer.slicer.cura.js",
                "js/octolapse.profiles.printer.slicer.other.js",
                "js/octolapse.profiles.printer.slicer.simplify_3d.js",
                "js/octolapse.profiles.printer.slicer.slic3r_pe.js",
                "js/octolapse.profiles.stabilization.js",
                "js/octolapse.profiles.snapshot.js",
                "js/octolapse.profiles.rendering.js",
                "js/octolapse.profiles.camera.js",
                "js/octolapse.profiles.debug.js",
                "js/octolapse.status.js"
            ],
            css=["css/jquery.minicolors.css", "css/octolapse.css"],
            less=["less/octolapse.less"])

    # ~~ software update hook
    def get_update_information(self):
        # get the checkout type from the software updater
        prerelease_channel = None
        is_prerelease = False
        # get this for reference.  Eventually I'll have to use it!
        # is the software update set to prerelease?

        if self._settings.global_get(["plugins", "softwareupdate", "checks", "octoprint", "prerelease"]):
            # If it's a prerelease, look at the channel and configure the proper branch for Octolapse
            prerelease_channel = self._settings.global_get(
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
            prerelease=is_prerelease,
            pip="https://github.com/FormerLurker/Octolapse/archive/{target_version}.zip",
            stable_branch=dict(branch="master", commitish=["master"], name="Stable"),
            release_compare='semantic_version',
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

    # noinspection PyUnusedLocal
    def get_timelapse_extensions(self, *args, **kwargs):
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
        "octoprint.comm.protocol.gcode.queuing": (__plugin_implementation__.on_gcode_queuing, -1),
        "octoprint.comm.protocol.gcode.sent": (__plugin_implementation__.on_gcode_sent, -1),
        "octoprint.comm.protocol.gcode.sending": (__plugin_implementation__.on_gcode_sending, -1),
        "octoprint.comm.protocol.gcode.received": (__plugin_implementation__.on_gcode_received, -1),
        "octoprint.timelapse.extensions": __plugin_implementation__.get_timelapse_extensions
    }
