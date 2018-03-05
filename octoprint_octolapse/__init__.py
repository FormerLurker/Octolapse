# This file is subject to the terms and conditions defined in
# file called 'LICENSE', which is part of this source code package.

# coding=utf-8
from __future__ import absolute_import

import json
import os

import flask
import octoprint.plugin
# Octoprint Imports
# used to send messages to the web client for notifying it of new timelapses
from octoprint.events import eventManager, Events
from octoprint.server import admin_permission
from octoprint.server.util.flask import restricted_access, check_lastmodified, check_etag

import octoprint_octolapse.camera as camera
import octoprint_octolapse.utility as utility
from octoprint_octolapse.command import Commands
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
        self.Settings = None
        self.Timelapse = None
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
        self.Settings.remove_profile(profile_type, guid)
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
        except Exception, e:
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
            camera_profile, self.on_apply_camera_settings_success, self.on_apply_camera_settings_fail, self.on_apply_camera_settings_complete)
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
                new_settings = OctolapseSettings(self.get_log_file_path(), data)
                if self.Settings is not None:
                    self.Settings.update(new_settings.to_dict())
                else:
                    self.Settings = create_new_settings
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
                    self.get_settings_file_path()))
            with open(self.get_settings_file_path()) as settingsJson:
                data = json.load(settingsJson)
            if self.Settings is None:
                #  create a new settings object
                self.Settings = OctolapseSettings(self.get_log_file_path(), data)
                self.Settings.current_debug_profile().log_settings_load(
                    "Settings loaded.  Created new settings object: {0}.".format(data))
            else:
                # update an existing settings object
                self.Settings.current_debug_profile().log_settings_load(
                    "Settings loaded.  Updating existing settings object: {0}.".format(data))
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
            except Exception, e:
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
        except Exception, e:
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))

    def save_settings(self):
        # Save setting from file
        settings_dict = self.Settings.to_dict()
        self.Settings.current_debug_profile().log_settings_save(
            "Saving Settings.".format(settings_dict))

        with open(self.get_settings_file_path(), 'w') as outfile:
            json.dump(settings_dict, outfile)
        self.Settings.current_debug_profile().log_settings_save(
            "Settings saved: {0}".format(settings_dict))
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
        try:
            octoprint.plugin.SettingsPlugin.on_settings_load(self)
            settings_dict = self.Settings.to_dict()
        except Exception, e:
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))

        return settings_dict

    def get_status_dict(self):
        try:
            is_timelapse_active = False
            snapshot_count = 0
            seconds_added_by_octolapse = 0
            is_taking_snapshot = False
            is_rendering = False
            timelapse_state = TimelapseState.Idle
            is_waiting_to_render = False
            if self.Timelapse is not None:
                snapshot_count = self.Timelapse.SnapshotCount
                seconds_added_by_octolapse = self.Timelapse.SecondsAddedByOctolapse
                is_timelapse_active = self.Timelapse.is_timelapse_active()
                is_rendering = self.Timelapse.IsRendering
                is_taking_snapshot = \
                    TimelapseState.RequestingReturnPosition <= self.Timelapse.State < TimelapseState.WaitingToRender
                timelapse_state = self.Timelapse.State
                is_waiting_to_render = self.Timelapse.State == TimelapseState.WaitingToRender
            return {'snapshot_count': snapshot_count,
                    'seconds_added_by_octolapse': seconds_added_by_octolapse,
                    'is_timelapse_active': is_timelapse_active,
                    'is_taking_snapshot': is_taking_snapshot,
                    'is_rendering': is_rendering,
                    'waiting_to_render': is_waiting_to_render,
                    'state': timelapse_state
                    }
        except Exception, e:
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))
        return None

    def get_template_configs(self):
        self._logger.info("Octolapse - is loading template configurations.")
        return [dict(type="settings", custom_bindings=True)]

    def create_timelapse_object(self):
        self.Timelapse = Timelapse(self.get_plugin_data_folder(),
                                   self._settings.getBaseFolder("timelapse"),
                                   on_render_start=self.on_render_start,
                                   on_render_complete=self.on_render_complete,
                                   on_render_fail=self.on_render_fail,
                                   on_render_synchronize_fail=self.on_render_synchronize_fail,
                                   on_render_synchronize_complete=self.on_render_synchronize_complete,
                                   on_render_end=self.on_render_end,
                                   on_snapshot_start=self.on_snapshot_start,
                                   on_snapshot_end=self.on_snapshot_end,
                                   on_timelapse_stopping=self.on_timelapse_stopping,
                                   on_timelapse_stopped=self.on_timelapse_stopped,
                                   on_state_changed=self.on_timelapse_state_changed,
                                   on_timelapse_start=self.on_timelapse_start,
                                   on_snapshot_position_error=self.on_snapshot_position_error,
                                   on_position_error=self.on_position_error)

    def on_after_startup(self):
        try:
            self.load_settings()
            # create our initial timelapse object
            # create our timelapse object

            self.create_timelapse_object()
            self.Settings.current_debug_profile().log_info("Octolapse - loaded and active.")
        except Exception, e:
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))
            raise

    # Event Mixin Handler

    def on_event(self, event, payload):
        # If we haven't loaded our settings yet, return.
        if self.Settings is None:
            return
        try:
            self.Settings.current_debug_profile().log_print_state_change(
                "Printer event received:{0}.".format(event))

            # for printing events use Printer State Change, because it gets sent before Print_Started
            # unfortunately, now we have to know that it
            if event == Events.PRINTER_STATE_CHANGED and payload["state_id"] == "PRINTING":
                self.on_print_start()
                self.Settings.current_debug_profile().log_print_state_change("State Change to Printing")
            if event == Events.PRINT_STARTED:
                # eventId = self._printer.get_state_id()
                # if the origin is not local, and the timelapse is running, stop it now, we can't lapse from SD :(
                if payload["origin"] != "local" and self.Timelapse is not None and self.Timelapse.is_timelapse_active():
                    self.Timelapse.end_timelapse()
                    self.send_popup_message(
                        "Octolapse does not work when printing from SD the card.  The timelapse has been stopped.")
                    self.Settings.current_debug_profile().log_print_state_change(
                        "Octolapse cannot start the timelapse when printing from SD.  Origin:{0}"
                        .format(payload["origin"]))
            elif self.Timelapse is None:
                self.Settings.current_debug_profile().log_print_state_change(
                    "No timelapse object exists and this is not a print start event, exiting.")
                return
            elif event == Events.PRINT_PAUSED:
                self.on_print_paused()
            elif event == Events.HOME:
                self.Settings.current_debug_profile().log_print_state_change(
                    "homing to payload:{0}.".format(event))
            elif event == Events.PRINT_RESUMED:
                self.on_print_resumed()
            elif event == Events.PRINT_FAILED:
                self.on_print_failed()
            elif event == Events.PRINT_CANCELLED:
                self.on_print_canceled()
            elif event == Events.PRINT_DONE:
                self.on_print_completed()
            elif event == Events.POSITION_UPDATE:
                self.Timelapse.on_position_received(payload)
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

    def on_print_start(self):
        if not self.Settings.is_octolapse_enabled:
            self.Settings.current_debug_profile().log_print_state_change("Octolapse is disabled.")
            return

        if self.Timelapse.State != TimelapseState.Idle:
            self.Settings.current_debug_profile().log_print_state_change(
                "Octolapse is not idling.  CurrentState:{0}".format(self.Timelapse.State))
            return

        result = self.start_timelapse()
        if not result["success"]:
            self.Settings.current_debug_profile().log_print_state_change(
                "Unable to start the timelapse. Error:{0}".format(result["error"]))
            return

        if result["warning"]:
            self.send_popup_message(result["warning"])

        self.Settings.current_debug_profile().log_print_state_change(
            "Print Started - Timelapse Started.")
        if self.Settings.current_camera().apply_settings_before_print:
            self.apply_camera_settings(self.Settings.current_camera())

    def start_timelapse(self):

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
        except Exception, e:
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
                             "to FFMPEG.".format( ffmpeg_path), 'warning': False}
        g90_influences_extruder = False
        try:
            g90_influences_extruder = self._settings.settings.get(
                ["feature", "g90InfluencesExtruder"])

        except Exception, e:
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))

        octoprint_printer_profile = self._printer_profile_manager.get_current()
        # check for circular bed.  If it exists, we can't continue:
        if octoprint_printer_profile["volume"]["formFactor"] == "circle":
            return {'success': False, 'error': "Octolapse does not yet support circular beds, sorry.", 'warning': False}

        self.Timelapse.start_timelapse(
            self.Settings, self._printer, octoprint_printer_profile, ffmpeg_path, g90_influences_extruder)

        if octoprint_printer_profile["volume"]["origin"] != "lowerleft":
            return {'success': True,
                    'warning': "Octolapse has not been tested on printers with origins that are not in the lower "
                               "left.  Use at your own risk."}

        return {'success': True, 'warning': False}

    def send_popup_message(self, msg):
        self.send_plugin_message("popup", msg)

    def send_state_changed_message(self, state):
        data = {
            "type": "state-changed"
        }
        data.update(state)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_settings_changed_message(self, client_id):
        data = {
            "type": "settings-changed", "client_id": client_id
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

    def send_render_end_message(self, success):
        data = {
            "type": "render-end",
            "msg": "Octolapse is finished rendering a timelapse.",
            "Status": self.get_status_dict(),
            "MainSettings": self.Settings.get_main_settings_dict(),
            "is_synchronized": self.IsRenderingSynchronized,
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

    def on_position_error(self, message):
        state_data = self.Timelapse.to_state_dict()
        data = {
            "type": "position-error", "msg": message, "Status": self.get_status_dict(),
            "MainSettings": self.Settings.get_main_settings_dict()
        }
        data.update(state_data)
        self._plugin_manager.send_plugin_message(self._identifier, data)

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
            "type": "state-loaded", "msg": "The current state has been loaded.", "Status": self.get_status_dict(),
            "MainSettings": self.Settings.get_main_settings_dict()

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
        self.end_timelapse()
        self.Settings.current_debug_profile().log_print_state_change("Print Failed.")

    def on_print_canceled(self):
        self.end_timelapse(cancelled=True)
        self.Settings.current_debug_profile().log_print_state_change("Print Cancelled.")

    def on_print_completed(self):
        self.end_timelapse()
        self.Settings.current_debug_profile().log_print_state_change("Print Completed.")

    def on_print_end(self):
        # tell the timelapse that the print ended.
        self.end_timelapse()
        self.Settings.current_debug_profile().log_print_state_change("Print Ended.")

    def end_timelapse(self, cancelled=False):
        if self.Timelapse is not None:
            self.Timelapse.end_timelapse(cancelled=cancelled)
            self.on_timelapse_complete()

    def on_timelapse_stopping(self):
        self.send_plugin_message(
            "timelapse-stopping", "Waiting for a snapshot to complete before stopping the timelapse.")

    def on_timelapse_stopped(self):
        self.send_plugin_message(
            "timelapse-stopped",
            "Octolapse has been stopped for the remainder of the print.  Snapshots will be rendered after the print "
            "is complete.")

    def on_gcode_queuing(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        try:
            # only handle commands sent while printing
            if self.Timelapse is not None and self.Timelapse.is_timelapse_active():
                return self.Timelapse.on_gcode_queuing(cmd, cmd_type, gcode)

        except Exception, e:
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))

    def on_gcode_sent(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        try:
            if self.Timelapse is not None and self.Timelapse.is_timelapse_active():
                self.Timelapse.on_gcode_sent(cmd, cmd_type, gcode)
        except Exception, e:
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))

    def on_timelapse_state_changed(self, *args, **kwargs):
        state_change_dict = args[0]
        self.send_state_changed_message(state_change_dict)

    def on_render_start(self, *args, **kwargs):
        """Called when a timelapse has started being rendered.  Calls any callbacks OnRenderStart callback set in the
        constructor. """
        payload = args[0]
        # Set a flag marking that we have not yet synchronized with the default Octoprint plugin, in case we do this
        # later.
        self.IsRenderingSynchronized = False
        # Generate a notification message
        msg = "Octolapse captured {0} frames in {1} seconds, and has started rending your timelapse file.".format(
            payload.SnapshotCount, utility.seconds_to_hhmmss(payload.SecondsAddedToPrint))

        if payload.Synchronize:
            will_sync_message = "This timelapse will synchronized with the default timelapse module, and will be " \
                              "available within the default timelapse plugin as '{0}' after rendering is " \
                              "complete.".format(payload.RenderingFileName)
        else:
            will_sync_message = "Due to your rendering settings, this timelapse will NOT be synchronized with the " \
                              "default timelapse module.  You will be able to find on your octoprint server here: " \
                              "{0}".format(payload.RenderingFullPath)

        message = "{0}{1}".format(msg, will_sync_message)
        # send a message to the client
        self.send_render_start_message(message)

    def on_render_fail(self, *args, **kwargs):
        """Called after a timelapse rendering attempt has failed.  Calls any callbacks onMovieFailed callback set in
        the constructor. """
        payload = args[0]
        # Octoprint Event Manager Code
        self.send_render_failed_message(
            "Octolapse has failed to render a timelapse.  {0}".format(payload.Reason))

    def on_render_complete(self, *args, **kwargs):
        self.send_render_complete_message()

    def on_render_synchronize_fail(self, *args, **kwargs):
        """Called when a synchronization attempt with the default app fails."""
        payload = args[0]
        message = "Octolapse has failed to syncronize the default timelapse plugin.  {0}  You should be able to find " \
                  "your video within your octoprint server here: '{1}'"\
                  .format(payload.Reason, payload.RenderingFullPath)
        # Octoprint Event Manager Code
        self.send_plugin_message("synchronize-failed", message)

    def on_render_synchronize_complete(self, *args, **kwargs):
        """Called when a synchronization attempt goes well!  Notifies Octoprint of the new timelapse!"""
        payload = args[0]

        self.IsRenderingSynchronized = True

        # create a message that makes sense, since Octoprint will display its own popup message that already contains
        # text
        # Todo:  Enter the text here so we can easily see what our message should be to fit into the boilerplate text.
        message = "from Octolapse has been synchronized and is now available within the default timelapse plugin tab " \
                  "as '{0}'.  Octolapse ".format(payload.RenderingFileName)
        # Here we create a special payload to notify the default timelapse plugin of a new timelapse

        octoprint_payload = dict(gcode="unknown",
                                 movie=payload.RenderingFullPath,
                                 movie_basename=payload.RenderingFileName,
                                 movie_prefix=message,
                                 returncode=payload.ReturnCode,
                                 reason=payload.Reason)
        # notify Octoprint using the event manager.  Is there a way to do this that is more in the spirit of the API?
        eventManager().fire(Events.MOVIE_DONE, octoprint_payload)
        self.send_render_end_message(True)

    def on_render_end(self, *args, **kwargs):
        """Called after all rendering and synchronization attemps are complete."""
        # payload = args[0]
        success = args[1]
        if not self.IsRenderingSynchronized:
            self.send_render_end_message(success)

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
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here.  See
        # https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
        # for details.
        self._logger.info("Octolapse is getting update information.")
        return dict(octolapse=dict(displayName="Octolapse Plugin",
                                   displayVersion=self._plugin_version,
                                   # version check: github repository
                                   type="github_release",
                                   user="FormerLurker",
                                   repo="Octolapse",
                                   current=self._plugin_version,
                                   # update method: pip
                                   pip="https://github.com/FormerLurker/Octolapse/archive/{target_version}.zip"))


# If you want your plugin to be registered within OctoPrint under a different
# name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here.  Same goes for the
# other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties.  See the
# documentation for that.
__plugin_name__ = "Octolapse Plugin"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = OctolapsePlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.on_gcode_queuing,
        "octoprint.comm.protocol.gcode.sent": __plugin_implementation__.on_gcode_sent
    }
