# This file is subject to the terms and conditions defined in
# file called 'LICENSE', which is part of this source code package.

# coding=utf-8
from __future__ import absolute_import
import octoprint.plugin
import uuid
import time
import os
import sys
import traceback
import json
from pprint import pformat
import flask
from octoprint.server.util.flask import restricted_access, check_lastmodified, check_etag
from octoprint.server import admin_permission
import requests
import itertools
import shutil
import copy
import threading


# Octoprint Imports
# used to send messages to the web client for notifying it of new timelapses
from octoprint.events import eventManager, Events

# Octolapse imports

from octoprint_octolapse.settings import OctolapseSettings, Printer, Stabilization, Camera, Rendering, Snapshot, DebugProfile
from octoprint_octolapse.timelapse import Timelapse, TimelapseState
import octoprint_octolapse.camera as camera
from octoprint_octolapse.command import Commands
import octoprint_octolapse.utility as utility


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
    def downloadTimelapse(self, filename):
        """Restricted access function to download a timelapse"""
        return self.GetDownloadFileResponse(self.TimelapseFolderPath() + filename, filename)

    @octoprint.plugin.BlueprintPlugin.route("/snapshot/<filename>", methods=["GET"])
    def snapshot(self, filename):
        """Public access function to get the latest snapshot image"""
        if filename == 'latest-snapshot.jpeg':
            # get the latest snapshot image
            mimeType = 'image/jpeg'
            filename = utility.get_latest_snapshot_download_path(
                self.get_plugin_data_folder())
            if not os.path.isfile(filename):
                # we haven't captured any images, return the built in png.
                mimeType = 'image/png'
                filename = utility.get_no_snapshot_image_download_path(
                    self._basefolder)
        elif filename == 'latest_snapshot_thumbnail_300px.jpeg':
            # get the latest snapshot image
            mimeType = 'image/jpeg'
            filename = utility.get_latest_snapshot_thumbnail_download_path(
                self.get_plugin_data_folder())
            if not os.path.isfile(filename):
                # we haven't captured any images, return the built in png.
                mimeType = 'image/png'
                filename = utility.get_no_snapshot_image_download_path(
                    self._basefolder)
        else:
            # we don't recognize the snapshot type
            mimeType = 'image/png'
            filename = utility.get_error_image_download_path(self._basefolder)

        # not getting the latest image
        return flask.send_file(filename, mimetype=mimeType, cache_timeout=-1)

    @octoprint.plugin.BlueprintPlugin.route("/downloadSettings", methods=["GET"])
    @restricted_access
    @admin_permission.require(403)
    def downloadSettings(self):
        return self.GetDownloadFileResponse(self.SettingsFilePath(), "Settings.json")

    @octoprint.plugin.BlueprintPlugin.route("/stopTimelapse", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def stopTimelapse(self):

        self.Timelapse.stop_snapshots()
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/saveMainSettings", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def saveMainSettings(self):
        requestValues = flask.request.get_json()
        clientId = requestValues["client_id"]
        self.Settings.is_octolapse_enabled = requestValues["is_octolapse_enabled"]
        self.Settings.auto_reload_latest_snapshot = requestValues["auto_reload_latest_snapshot"]
        self.Settings.auto_reload_frames = requestValues["auto_reload_frames"]
        self.Settings.show_navbar_icon = requestValues["show_navbar_icon"]
        self.Settings.show_navbar_when_not_printing = requestValues["show_navbar_when_not_printing"]
        self.Settings.show_position_state_changes = requestValues["show_position_state_changes"]
        self.Settings.show_position_changes = requestValues["show_position_changes"]
        self.Settings.show_extruder_state_changes = requestValues["show_extruder_state_changes"]
        self.Settings.show_trigger_state_changes = requestValues["show_trigger_state_changes"]

        # save the updated settings to a file.
        self.SaveSettings()

        self.SendStateLoadedMessage()
        data = {'success': True}
        return json.dumps(data), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/loadMainSettings", methods=["POST"])
    def loadMainSettings(self):
        data = {'success': True}
        data.update(self.Settings.get_main_settings_dict())
        return json.dumps(data), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/loadState", methods=["POST"])
    def loadState(self):
        if self.Settings is None:
            raise Exception(
                "Unable to load values from Octolapse.Settings, it hasn't been initialized yet.  Please wait a few minutes and try again.  If the problem persists, please check plugin_octolapse.log for exceptions.")
        if self.Timelapse is None:
            raise Exception(
                "Unable to load values from Octolapse.Timelapse, it hasn't been initialized yet.  Please wait a few minutes and try again.  If the problem persists, please check plugin_octolapse.log for exceptions.")
        self.SendStateLoadedMessage()
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/addUpdateProfile", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def addUpdateProfile(self):
        requestValues = flask.request.get_json()
        profileType = requestValues["profileType"]
        profile = requestValues["profile"]
        client_id = requestValues["client_id"]
        updatedProfile = self.Settings.add_update_profile(profileType, profile)
        # save the updated settings to a file.
        self.SaveSettings()
        self.SendSettingsChangedMessage(client_id)
        return json.dumps(updatedProfile.to_dict()), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/removeProfile", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def removeProfile(self):
        requestValues = flask.request.get_json()
        profileType = requestValues["profileType"]
        guid = requestValues["guid"]
        client_id = requestValues["client_id"]
        self.Settings.remove_profile(profileType, guid)
        # save the updated settings to a file.
        self.SaveSettings()
        self.SendSettingsChangedMessage(client_id)
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/setCurrentProfile", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def setCurrentProfile(self):
        requestValues = flask.request.get_json()
        profileType = requestValues["profileType"]
        guid = requestValues["guid"]
        client_id = requestValues["client_id"]
        self.Settings.set_current_profile(profileType, guid)
        self.SaveSettings()
        self.SendSettingsChangedMessage(client_id)
        return json.dumps({'success': True, 'guid': requestValues["guid"]}), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/restoreDefaults", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def restoreDefaults(self):
        requestValues = flask.request.get_json()
        client_id = requestValues["client_id"]
        try:
            self.LoadSettings(forceDefaults=True)
            data = {'success': True}
            data.update(self.Settings.to_dict())
            self.SendSettingsChangedMessage(client_id)

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
    def loadSettings(self):
        data = {'success': True}
        data.update(self.Settings.to_dict())
        return json.dumps(data), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/applyCameraSettings", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def applyCameraSettingsRequest(self):
        requestValues = flask.request.get_json()
        profile = requestValues["profile"]
        cameraProfile = Camera(profile)
        self.ApplyCameraSettings(cameraProfile)

        return json.dumps({'success': True}, 200, {'ContentType': 'application/json'})

    @octoprint.plugin.BlueprintPlugin.route("/testCamera", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def testCamera(self):
        requestValues = flask.request.get_json()
        profile = requestValues["profile"]
        cameraProfile = Camera(profile)
        results = camera.test_camera(cameraProfile)
        if results[0]:
            return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
        else:
            return json.dumps({'success': False, 'error': results[1]}), 200, {'ContentType': 'application/json'}

    # blueprint helpers
    def GetDownloadFileResponse(self, filePath, downloadFileName):
        if os.path.isfile(filePath):

            def single_chunk_generator(downloadFile):
                while True:
                    chunk = downloadFile.read(1024)
                    if not chunk:
                        break
                    yield chunk

            downloadFile = open(filePath, 'rb')
            response = flask.Response(flask.stream_with_context(
                single_chunk_generator(downloadFile)))
            response.headers.set('Content-Disposition',
                                 'attachment', filename=downloadFileName)
            response.headers.set('Content-Type', 'application/octet-stream')
            return response
        return json.dumps({'success': False}), 404, {'ContentType': 'application/json'}

    def ApplyCameraSettings(self, cameraProfile):
        cameraControl = camera.CameraControl(
            cameraProfile, self.OnCameraSettingsSuccess, self.OnCameraSettingsFail, self.OnCameraSettingsCompelted)
        cameraControl.apply_settings()

    def TimelapseFolderPath(self):
        return utility.get_rendering_directory_from_data_directory(self.get_plugin_data_folder())

    def DefaultSettingsFilePath(self):
        return "{0}{1}data{1}settings_default.json".format(self._basefolder, os.sep)

    def SettingsFilePath(self):
        return "{0}{1}settings.json".format(self.get_plugin_data_folder(), os.sep)

    def LogFilePath(self):
        return self._settings.get_plugin_logfile_path()

    def LoadSettings(self, forceDefaults=False):
        # if the settings file does not exist, create one from the default settings
        createNewSettings = False
        if not os.path.isfile(self.SettingsFilePath()) or forceDefaults:
            # create new settings from default setting file
            with open(self.DefaultSettingsFilePath()) as defaultSettingsJson:
                data = json.load(defaultSettingsJson)
                # if a settings file does not exist, create one ??
                newSettings = OctolapseSettings(self.LogFilePath(), data)
                if (self.Settings is not None):
                    self.Settings.update(newSettings.to_dict())
                else:
                    self.Settings = createNewSettings
            self.Settings.current_debug_profile().log_settings_load(
                "Creating new settings file from defaults.")
            createNewSettings = True
        else:
            # Load settings from file
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_settings_load(
                    "Loading existings settings file from: {0}.".format(self.SettingsFilePath()))
            else:
                self._logger.info("Loading existing settings file from: {0}.".format(
                    self.SettingsFilePath()))
            with open(self.SettingsFilePath()) as settingsJson:
                data = json.load(settingsJson)
            if self.Settings == None:
                #  create a new settings object
                self.Settings = OctolapseSettings(self.LogFilePath(), data)
                self.Settings.current_debug_profile().log_settings_load(
                    "Settings loaded.  Created new settings object: {0}.".format(data))
            else:
                # update an existing settings object
                self.Settings.current_debug_profile().log_settings_load(
                    "Settings loaded.  Updating existing settings object: {0}.".format(data))
                self.Settings.update(data)
        # Extract any settings from octoprint that would be useful to our users.
        self.CopyOctoprintDefaultSettings(
            applyToCurrentProfiles=createNewSettings)

        if createNewSettings:
            # No file existed, so we must have created default settings.  Save them!
            self.SaveSettings()
        return self.Settings.to_dict()

    def CopyOctoprintDefaultSettings(self, applyToCurrentProfiles=False):
        try:
            # move some octoprint defaults if they exist for the webcam
            # specifically the address, the bitrate and the ffmpeg directory.
            # Attempt to get the camera address and snapshot template from Octoprint settings
            snapshotUrl = self._settings.settings.get(["webcam", "snapshot"])
            from urlparse import urlparse
            # we are doing some templating so we have to try to separate the
            # camera base address from the querystring.  This will probably not work
            # for all cameras.
            try:
                o = urlparse(snapshotUrl)
                cameraAddress = o.scheme + "://" + o.netloc + o.path
                self.Settings.current_debug_profile().log_settings_load(
                    "Setting octolapse camera address to {0}.".format(cameraAddress))
                snapshotAction = urlparse(snapshotUrl).query
                snapshotRequestTemplate = "{camera_address}?" + snapshotAction
                self.Settings.current_debug_profile().log_settings_load(
                    "Setting octolapse camera snapshot template to {0}.".format(snapshotRequestTemplate))
                self.Settings.DefaultCamera.address = cameraAddress
                self.Settings.DefaultCamera.snapshot_request_template = snapshotRequestTemplate
                if applyToCurrentProfiles:
                    for profile in self.Settings.cameras.values():
                        profile.address = cameraAddress
                        profile.snapshot_request_template = snapshotRequestTemplate
            except Exception, e:
                # cannot send a popup yet,because no clients will be connected.  We should write a routine that checks
                # to make sure Octolapse is correctly configured if it is enabled and send some kind of message on client
                # connect.
                # self.SendPopupMessage("Octolapse was unable to extract the default camera address from Octoprint.  Please configure your camera address and snapshot template before using Octolapse.")

                self.Settings.current_debug_profile().log_exception(e)

            bitrate = self._settings.settings.get(["webcam", "bitrate"])
            self.Settings.DefaultRendering.bitrate = bitrate
            if applyToCurrentProfiles:
                for profile in self.Settings.renderings.values():
                    profile.bitrate = bitrate
        except Exception, e:
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))

    def SaveSettings(self):
        # Save setting from file
        settings = self.Settings.to_dict()
        self.Settings.current_debug_profile().log_settings_save(
            "Saving Settings.".format(settings))

        with open(self.SettingsFilePath(), 'w') as outfile:
            json.dump(settings, outfile)
        self.Settings.current_debug_profile().log_settings_save(
            "Settings saved: {0}".format(settings))
        return None

    # def on_settings_initialized(self):

    def CurrentPrinterProfile(self):
        """Get the plugin's current printer profile"""
        return self._printer_profile_manager.get_current()

    # EVENTS
    #########
    def get_settings_defaults(self):
        return dict(load=None)

    def on_settings_load(self):
        settingsDict = None
        try:
            octoprint.plugin.SettingsPlugin.on_settings_load(self)
            settingsDict = self.Settings.to_dict()
        except Exception, e:
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))

        return settingsDict

    def GetStatusDict(self):
        try:
            isTimelapseActive = False
            snapshotCount = 0
            secondsAddedByOctolapse = 0
            isTakingSnapshot = False
            isRendering = False
            timelapseState = TimelapseState.Idle
            activeSnapshotTriggerName = "None"
            isWaitingToRender = False
            if self.Timelapse is not None:
                snapshotCount = self.Timelapse.SnapshotCount
                secondsAddedByOctolapse = self.Timelapse.SecondsAddedByOctolapse
                isTimelapseActive = self.Timelapse.is_timelapse_active()
                isRendering = self.Timelapse.IsRendering
                isTakingSnapshot = self.Timelapse.State >= TimelapseState.RequestingReturnPosition and self.Timelapse.State < TimelapseState.WaitingToRender
                timelapseState = self.Timelapse.State
                isWaitingToRender = self.Timelapse.State == TimelapseState.WaitingToRender
            return {'snapshot_count': snapshotCount,
                    'seconds_added_by_octolapse': secondsAddedByOctolapse,
                    'is_timelapse_active': isTimelapseActive,
                    'is_taking_snapshot': isTakingSnapshot,
                    'is_rendering': isRendering,
                    'waiting_to_render': isWaitingToRender,
                    'state': timelapseState
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

    def CreateTimelapseObject(self):
        self.Timelapse = Timelapse(self.get_plugin_data_folder(), self._settings.getBaseFolder("timelapse"),
                                   on_render_start=self.OnRenderStart, on_render_complete=self.OnRenderComplete,
                                   on_render_fail=self.OnRenderFail, on_render_synchronize_fail=self.OnRenderSynchronizeFail,
                                   on_render_synchronize_complete=self.OnRenderSynchronizeComplete,
                                   on_render_end=self.OnRenderEnd,
                                   on_snapshot_start=self.OnSnapshotStart, on_snapshot_end=self.OnSnapshotEnd,
                                   on_timelapse_stopping=self.OnTimelapseStopping,
                                   on_timelapse_stopped=self.OnTimelapseStopped,
                                   on_state_changed=self.OnTimelapseStateChanged, on_timelapse_start=self.OnTimelapseStart,
                                   on_snapshot_position_error=self.OnSnapshotPositionError,
                                   on_position_error=self.OnPositionError)

    def on_after_startup(self):
        try:
            self.LoadSettings()
            # create our initial timelapse object
            # create our timelapse object

            self.CreateTimelapseObject()
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
                self.OnPrintStart()
                self.Settings.current_debug_profile().log_print_state_change("State Change to Printing")
            if event == Events.PRINT_STARTED:
                # eventId = self._printer.get_state_id()
                # if the origin is not local, and the timelapse is running, stop it now, we can't lapse from SD :(
                if payload["origin"] != "local" and self.Timelapse is not None and self.Timelapse.is_timelapse_active():
                    self.Timelapse.end_timelapse()
                    self.SendPopupMessage(
                        "Octolapse does not work when printing from SD the card.  The timelapse has been stopped.")
                    self.Settings.current_debug_profile().log_print_state_change(
                        "Octolapse cannot start the timelapse when printing from SD.  Origin:{0}".format(origin))
            elif self.Timelapse == None:
                self.Settings.current_debug_profile().log_print_state_change(
                    "No timelapse object exists and this is not a print start event, exiting.")
                return
            elif event == Events.PRINT_PAUSED:
                self.OnPrintPause()
            elif event == Events.HOME:
                self.Settings.current_debug_profile().log_print_state_change(
                    "homing to payload:{0}.".format(event))
            elif event == Events.PRINT_RESUMED:
                self.OnPrintResumed()
            elif event == Events.PRINT_FAILED:
                self.OnPrintFailed()
            elif event == Events.PRINT_CANCELLED:
                self.OnPrintCancelled()
            elif event == Events.PRINT_DONE:
                self.OnPrintCompleted()
            elif event == Events.POSITION_UPDATE:
                self.Timelapse.on_position_received(payload)
        except Exception as e:
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))

    def OnPrintResumed(self):
        self.Settings.current_debug_profile().log_print_state_change("Print Resumed.")
        self.Timelapse.on_print_resumed()

    def OnPrintPause(self):
        self.Timelapse.on_print_paused()

    def OnPrintStart(self):
        if not self.Settings.is_octolapse_enabled:
            self.Settings.current_debug_profile().log_print_state_change("Octolapse is disabled.")
            return

        if self.Timelapse.State != TimelapseState.Idle:
            self.Settings.current_debug_profile().log_print_state_change(
                "Octolapse is not idling.  CurrentState:{0}".format(self.Timelapse.State))
            return

        result = self.StartTimelapse()
        if not result["success"]:
            self.Settings.current_debug_profile().log_print_state_change(
                "Unable to start the timelapse. Error:{0}".format(result["error"]))
            return

        if result["warning"] != False:
            self.SendPopupMessage(result["warning"])

        self.Settings.current_debug_profile().log_print_state_change(
            "Print Started - Timelapse Started.")
        if self.Settings.current_camera().apply_settings_before_print:
            self.ApplyCameraSettings(self.Settings.current_camera())

    def StartTimelapse(self):

        ffmpegPath = ""
        try:
            ffmpegPath = self._settings.settings.get(["webcam", "ffmpeg"])
            if self.Settings.current_rendering().enabled and ffmpegPath == "":
                self.Settings.current_debug_profile().log_error(
                    "A timelapse was started, but there is no ffmpeg path set!")
                return {'success': False,
                        'error': "No ffmpeg path is set.  Please configure this setting within the Octoprint settings pages located at Features->Webcam & Timelapse under Timelapse Recordings->Path to FFMPEG.",
                        'warning': False}
        except Exception, e:
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))
            return {'success': False,
                    'error': "An exception occurred while trying to acquire the ffmpeg path from Octoprint.  Please configure this setting within the Octoprint settings pages located at Features->Webcam & Timelapse under Timelapse Recordings->Path to FFMPEG.",
                    'warning': False}
        if not os.path.isfile(ffmpegPath):
            # todo:  throw some kind of exception
            return {'success': False,
                    'error': "The ffmpeg {0} does not exist.  Please configure this setting within the Octoprint settings pages located at Features->Webcam & Timelapse under Timelapse Recordings->Path to FFMPEG.".format(
                        ffmpegPath), 'warning': False}
        g90InfluencesExtruder = False
        try:
            g90InfluencesExtruder = self._settings.settings.get(
                ["feature", "g90InfluencesExtruder"])

        except Exception, e:
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))

        octoprintPrinterProfile = self._printer_profile_manager.get_current()
        # check for circular bed.  If it exists, we can't continue:
        if octoprintPrinterProfile["volume"]["formFactor"] == "circle":
            return {'success': False, 'error': "Octolapse does not yet support circular beds, sorry.", 'warning': False}

        self.Timelapse.start_timelapse(
            self.Settings, self._printer, octoprintPrinterProfile, ffmpegPath, g90InfluencesExtruder)

        if octoprintPrinterProfile["volume"]["origin"] != "lowerleft":
            return {'success': True,
                    'warning': "Octolapse has not been tested on printers with origins that are not in the lower left.  Use at your own risk."}

        return {'success': True, 'warning': False}

    def SendPopupMessage(self, msg):
        self.SendPluginMessage("popup", msg)

    def SendStateChangedMessage(self, state):
        data = {
            "type": "state-changed"
        }
        data.update(state)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def SendSettingsChangedMessage(self, client_id):
        data = {
            "type": "settings-changed", "client_id": client_id
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def SendPluginMessage(self, type, msg):
        self._plugin_manager.send_plugin_message(
            self._identifier, dict(type=type, msg=msg))

    def SendRenderStartMessage(self, msg):
        data = {
            "type": "render-start", "msg": msg, "Status": self.GetStatusDict(),
            "MainSettings": self.Settings.get_main_settings_dict()
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def SendRenderFailedMessage(self, msg):
        data = {
            "type": "render-failed", "msg": msg, "Status": self.GetStatusDict(),
            "MainSettings": self.Settings.get_main_settings_dict()
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def SendRenderEndMessage(self, success):
        data = {
            "type": "render-end", "msg": "Octolapse is finished rendering a timelapse.", "Status": self.GetStatusDict(),
            "MainSettings": self.Settings.get_main_settings_dict(), "is_synchronized": self.IsRenderingSynchronized,
            'success': success
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def SendRenderCompleteMessage(self):
        self._plugin_manager.send_plugin_message(self._identifier, dict(
            type="render-complete", msg="Octolapse has completed a rendering."))

    def OnTimelapseStart(self, *args, **kwargs):
        stateData = self.Timelapse.to_state_dict()
        data = {
            "type": "timelapse-start", "msg": "Octolapse has started a timelapse.", "Status": self.GetStatusDict(),
            "MainSettings": self.Settings.get_main_settings_dict()
        }
        data.update(stateData)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def OnPositionError(self, message):
        stateData = self.Timelapse.to_state_dict()
        data = {
            "type": "position-error", "msg": message, "Status": self.GetStatusDict(),
            "MainSettings": self.Settings.get_main_settings_dict()
        }
        data.update(stateData)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def OnSnapshotPositionError(self, message):
        stateData = self.Timelapse.to_state_dict()
        data = {
            "type": "out-of-bounds", "msg": message, "Status": self.GetStatusDict(),
            "MainSettings": self.Settings.get_main_settings_dict()
        }
        data.update(stateData)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def SendStateLoadedMessage(self):
        data = {
            "type": "state-loaded", "msg": "The current state has been loaded.", "Status": self.GetStatusDict(),
            "MainSettings": self.Settings.get_main_settings_dict()

        }
        data.update(self.Timelapse.to_state_dict())
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def OnTimelapseComplete(self):
        stateData = self.Timelapse.to_state_dict()
        data = {
            "type": "timelapse-complete", "msg": "Octolapse has completed the timelapse.",
            "Status": self.GetStatusDict(), "MainSettings": self.Settings.get_main_settings_dict()
        }
        data.update(stateData)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def OnSnapshotStart(self):
        stateData = self.Timelapse.to_state_dict()

        data = {
            "type": "snapshot-start", "msg": "Octolapse is taking a snapshot.", "Status": self.GetStatusDict(),
            "MainSettings": self.Settings.get_main_settings_dict()
        }
        data.update(stateData)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def OnSnapshotEnd(self, *args, **kwargs):
        payload = args[0]

        statusDict = self.GetStatusDict()
        success = payload["success"]
        error = payload["error"]
        data = {
            "type": "snapshot-complete", "msg": "Octolapse has completed the current snapshot.", "Status": statusDict,
            "MainSettings": self.Settings.get_main_settings_dict(), 'success': success, 'error': error

        }
        stateData = self.Timelapse.to_state_dict()
        data.update(stateData)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def OnCameraSettingsSuccess(self, *args, **kwargs):
        settingValue = args[0]
        settingName = args[1]
        template = args[2]
        self.Settings.current_debug_profile().log_camera_settings_apply(
            "Camera Settings - Successfully applied {0} to the {1} setting.  Template:{2}".format(settingValue,
                                                                                                  settingName,
                                                                                                  template))

    def OnCameraSettingsFail(self, *args, **kwargs):
        settingValue = args[0]
        settingName = args[1]
        template = args[2]
        errorMessage = args[3]
        self.Settings.current_debug_profile().log_camera_settings_apply(
            "Camera Settings - Unable to apply {0} to the {1} settings!  Template:{2}, Details:{3}".format(settingValue,
                                                                                                           settingName,
                                                                                                           template,
                                                                                                           errorMessage))

    def OnCameraSettingsCompelted(self, *args, **kwargs):
        self.Settings.current_debug_profile().log_camera_settings_apply(
            "Camera Settings - Completed")

    def OnPrintFailed(self):
        self.EndTimelapse()
        self.Settings.current_debug_profile().log_print_state_change("Print Failed.")

    def OnPrintCancelled(self):
        self.EndTimelapse(cancelled=True)
        self.Settings.current_debug_profile().log_print_state_change("Print Cancelled.")

    def OnPrintCompleted(self):
        self.EndTimelapse()
        self.Settings.current_debug_profile().log_print_state_change("Print Completed.")

    def OnPrintEnd(self):
        # tell the timelapse that the print ended.
        self.EndTimelapse()
        self.Settings.current_debug_profile().log_print_state_change("Print Ended.")

    def EndTimelapse(self, cancelled=False):
        if self.Timelapse is not None:
            self.Timelapse.end_timelapse(cancelled=cancelled)
            self.OnTimelapseComplete()

    def OnTimelapseStopping(self):
        self.SendPluginMessage(
            "timelapse-stopping", "Waiting for a snapshot to complete before stopping the timelapse.")

    def OnTimelapseStopped(self):
        self.SendPluginMessage(
            "timelapse-stopped",
            "Octolapse has been stopped for the remainder of the print.  Snapshots will be rendered after the print is complete.")

    def GcodeQueuing(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        try:
            # only handle commands sent while printing
            if self.Timelapse is not None and self.Timelapse.is_timelapse_active():
                return self.Timelapse.on_gcode_queuing(cmd, cmd_type, gcode)

        except Exception, e:
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))

    def GcodeSent(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        try:
            if self.Timelapse is not None and self.Timelapse.is_timelapse_active():
                self.Timelapse.on_gcode_sent(cmd, cmd_type, gcode)
        except Exception, e:
            if self.Settings is not None:
                self.Settings.current_debug_profile().log_exception(e)
            else:
                self._logger.critical(utility.exception_to_string(e))

    def OnTimelapseStateChanged(self, *args, **kwargs):
        stateChangeDict = args[0]
        self.SendStateChangedMessage(stateChangeDict)

    def OnRenderStart(self, *args, **kwargs):
        """Called when a timelapse has started being rendered.  Calls any callbacks OnRenderStart callback set in the constructor."""
        payload = args[0]
        # Set a flag marking that we have not yet synchronized with the default Octoprint plugin, in case we do this later.
        self.IsRenderingSynchronized = False
        # Generate a notification message
        msg = "Octolapse captured {0} frames in {1} seconds, and has started rending your timelapse file.".format(
            payload.SnapshotCount, utility.seconds_to_hhmmss(payload.SecondsAddedToPrint))
        willSyncMessage = ""

        if payload.Synchronize:
            willSyncMessage = "  This timelapse will synchronized with the default timelapse module, and will be available within the default timelapse plugin as '{0}' after rendering is complete.".format(
                payload.RenderingFileName)
        else:
            willSyncMessage = "  Due to your rendering settings, this timelapse will NOT be synchronized with the default timelapse module.  You will be able to find on your octoprint server here: {0}".format(
                payload.RenderingFullPath)

        message = "{0}{1}".format(msg, willSyncMessage)
        # send a message to the client
        self.SendRenderStartMessage(message)

    def OnRenderFail(self, *args, **kwargs):
        """Called after a timelapse rendering attempt has failed.  Calls any callbacks onMovieFailed callback set in the constructor."""
        payload = args[0]
        # Octoprint Event Manager Code
        self.SendRenderFailedMessage(
            "Octolapse has failed to render a timelapse.  {0}".format(payload.Reason))

    def OnRenderComplete(self, *args, **kwargs):
        self.SendRenderCompleteMessage()

    def OnRenderSynchronizeFail(self, *args, **kwargs):
        """Called when a synchronization attempt with the default app fails."""
        payload = args[0]
        message = "Octolapse has failed to syncronize the default timelapse plugin.  {0}  You should be able to find your video within your octoprint server here: '{1}'".format(
            payload.Reason, payload.RenderingFullPath)
        # Octoprint Event Manager Code
        self.SendPluginMessage("synchronize-failed", message)

    def OnRenderSynchronizeComplete(self, *args, **kwargs):
        """Called when a synchronization attempt goes well!  Notifies Octoprint of the new timelapse!"""
        payload = args[0]

        self.IsRenderingSynchronized = True

        # create a message that makes sense, since Octoprint will display its own popup message that already contains text
        # Todo:  Enter the text here so we can easily see what our message should be to fit into the boilerplate text.
        message = "from Octolapse has been synchronized and is now available within the default timelapse plugin tab as '{0}'.  Octolapse ".format(
            payload.RenderingFileName)
        # Here we create a special payload to notify the default timelapse plugin of a new timelapse

        octoprintPayload = dict(gcode="unknown",
                                movie=payload.RenderingFullPath,
                                movie_basename=payload.RenderingFileName,
                                movie_prefix=message,
                                returncode=payload.ReturnCode,
                                reason=payload.Reason)
        # notify Octoprint using the event manager.  Is there a way to do this that is more in the spirit of the API?
        eventManager().fire(Events.MOVIE_DONE, octoprintPayload)
        self.SendRenderEndMessage(True)

    def OnRenderEnd(self, *args, **kwargs):
        """Called after all rendering and synchronization attemps are complete."""
        payload = args[0]
        success = args[1]
        if not self.IsRenderingSynchronized:
            self.SendRenderEndMessage(success)

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

    # ~~ Softwareupdate hook
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
        "octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.GcodeQueuing,
        "octoprint.comm.protocol.gcode.sent": __plugin_implementation__.GcodeSent
    }
