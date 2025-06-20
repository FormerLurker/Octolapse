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

from __future__ import absolute_import
from __future__ import unicode_literals
# Create the root logger.  Note that it MUST be created before any imports that use the
# plugin_octolapse.log.LoggingConfigurator, since it is a singleton and we want to be
# the first to create it so that the name is correct.
import octoprint_octolapse.log as log
logging_configurator = log.LoggingConfigurator()
root_logger = logging_configurator.get_root_logger()
# so that we can
logger = logging_configurator.get_logger("__init__")
# be sure to configure the logger after we import all of our modules
import tornado
import errno
from octoprint.server import util, app
from octoprint.server.util.tornado import LargeResponseHandler, RequestlessExceptionLoggingMixin, CorsSupportMixin
import sys
import base64
import json
import os
# remove unused imports
#from flask import request, send_file, jsonify, Response, stream_with_context, send_from_directory, current_app, Flask
from flask import request, jsonify
import threading
import uuid
# remove unused imports
# import six
import time
# Remove python 2 support
# from six.moves import queue
import queue as queue
from tempfile import mkdtemp
from distutils.version import LooseVersion
from io import BytesIO
import octoprint.plugin
import octoprint.filemanager
from octoprint.events import Events
from octoprint.server.util.flask import restricted_access
# remove unused import
# import octoprint_octolapse.stabilization_preprocessing
import octoprint_octolapse.camera as camera
import octoprint_octolapse.render as render
import octoprint_octolapse.snapshot as snapshot
import octoprint_octolapse.utility as utility
import octoprint_octolapse.error_messages as error_messages
from octoprint_octolapse.migration import migrate_files, get_version_from_settings_index
# remove unused import
# from octoprint_octolapse.position import Position
from octoprint_octolapse.stabilization_gcode import SnapshotGcodeGenerator
from octoprint_octolapse.gcode_commands import Commands
# remove unused import
# from octoprint_octolapse.render import TimelapseRenderJob, RenderingCallbackArgs
from octoprint_octolapse.settings import OctolapseSettings, PrinterProfile, StabilizationProfile, TriggerProfile, \
    CameraProfile, RenderingProfile, LoggingProfile, SlicerSettings, CuraSettings, OtherSlicerSettings, \
    Simplify3dSettings, Slic3rPeSettings, SettingsJsonEncoder, MjpgStreamer, MainSettings
from octoprint_octolapse.timelapse import Timelapse, TimelapseState, TimelapseStartException
from octoprint_octolapse.stabilization_preprocessing import StabilizationPreprocessingThread
from octoprint_octolapse.messenger_worker import MessengerWorker, PluginMessage
from octoprint_octolapse.settings_external import ExternalSettings, ExternalSettingsError
from octoprint_octolapse.render import RenderError, RenderingProcessor, RenderingCallbackArgs, RenderJobInfo
#import octoprint_octolapse_setuptools as octoprint_octolapse_setuptools
#import octoprint_octolapse_setuptools.github_release as github_release
# remove python 2 compatibility
#try:
#    # noinspection PyCompatibility
#    from urlparse import urlparse as urlparse
#except ImportError:
#    # noinspection PyUnresolvedReferences
#    from urllib.parse import urlparse as urlparse
from urllib.parse import urlparse as urlparse
# configure all imported loggers
logging_configurator.configure_loggers()


def configure_debug_mode():
    # Conditional imports for OctoPrint or Python debug mode
    # detect debug mode
    if hasattr(sys, 'gettotalrefcount') or "--debug" in sys.argv:
        logger.info("Debug mode detected.")
        # import python 3 specific debug modules
        logger.info("Python %s detected.", sys.version)
        if sys.version_info > (3, 0):
            import faulthandler
            faulthandler.enable()
            logger.info("Faulthandler enabled.")
    else:
        logger.info("Release mode detected.")


# configure debug mode
configure_debug_mode()


class OctolapsePlugin(
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.ShutdownPlugin,
    octoprint.plugin.EventHandlerPlugin,
    octoprint.plugin.BlueprintPlugin,
    octoprint.plugin.WizardPlugin,
):
    TIMEOUT_DELAY = 1000
    PREPROCESSING_CANCEL_TIMEOUT_SECONDS = 5
    PREPROCESSING_NOTIFICATION_PERIOD_SECONDS = 1

    if LooseVersion(octoprint.server.VERSION) >= LooseVersion("1.4"):
        import octoprint.access.permissions as permissions
        admin_permission = permissions.Permissions.ADMIN
    else:
        import flask_principal
        admin_permission = flask_principal.Permission(flask_principal.RoleNeed('admin'))

    def __init__(self):
        super(OctolapsePlugin, self).__init__()
        self._octolapse_settings = None  # type: OctolapseSettings
        self._timelapse = None  # type: Timelapse
        self.gcode_preprocessor = None
        self._stabilization_preprocessor_thread = None
        self._preprocessing_cancel_event = threading.Event()

        self._plugin_message_queue = queue.Queue()
        self._message_worker = None
        # this variable is used to make sure that cancelling old stabilizations (perhaps on browsers that have errored
        # out somehow) don't cancel any current print.
        self.preprocessing_job_guid = None
        self.saved_timelapse_settings = None
        self.saved_snapshot_plans = None
        self.saved_parsed_command = None
        self.saved_preprocessing_quality_issues = ""
        self.saved_missed_snapshots = 0
        self.snapshot_plan_preview_autoclose = False
        self.snapshot_plan_preview_close_time = 0
        self.autoclose_snapshot_preview_thread_lock = threading.Lock()
        # automatic update thread
        self.automatic_update_thread = None
        self.automatic_updates_notification_thread = None
        self.automatic_update_lock = threading.RLock()
        self.automatic_update_cancel = threading.Event()
        # contains a list of all profiles with available updates
        # holds a list of all available profiles on the server for the current version
        self.available_profiles = None
        # rendering processor and task queue
        self._rendering_task_queue = queue.Queue(maxsize=0)
        self._rendering_processor = None

    def get_sorting_key(self, context=None):
        return 1

    def get_current_logging_profile_function(self):
        if self._octolapse_settings is not None:
            return self._octolapse_settings.profiles.current_logging_profile

    def get_current_octolapse_settings(self):
        # returns a guaranteed up-to-date settings object
        return self._octolapse_settings

    @octoprint.plugin.BlueprintPlugin.route("/clearLog", methods=["POST"])
    @restricted_access
    def clear_log_request(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            clear_all = request_values["clear_all"]
            if clear_all:
                logger.info("Clearing all log files.")
            else:
                logger.info("Rolling over most recent log.")

            logging_configurator.do_rollover(clear_all=clear_all)
            return jsonify({"success": True})

    @staticmethod
    def file_name_allowed(name):
        # Don't allow any subdirectory access
        if name != os.path.basename(name):
            return False
        return True

    def get_file_directory(self, file_type, name):
        extension = utility.get_extension_from_filename(name)
        directory = None
        allowed = False
        if file_type == 'snapshot_archive':
            directory = self._octolapse_settings.main_settings.get_snapshot_archive_directory(
                self.get_plugin_data_folder()
            )
            if extension in RenderingProfile.get_archive_formats():
                allowed = True
        else:
            has_directory = False
            if file_type == 'timelapse_octolapse':
                has_directory = True
                directory = self._octolapse_settings.main_settings.get_timelapse_directory(
                    self.get_octoprint_timelapse_location()
                )
            elif file_type == 'timelapse_octoprint':
                has_directory = True
                directory = self.get_octoprint_timelapse_location()

            if has_directory and extension in set(self.get_timelapse_extensions()):
                allowed = True
        if not allowed:
            return None
        return directory

    # Callback handler for /getSnapshot
    # uses the OctolapseLargeResponseHandler
    def get_snapshot_request(self, request_handler):
        download_file_path = None
        # get the args
        file_type = request_handler.get_query_arguments('file_type')[0]
        guid = request_handler.get_query_arguments('camera_guid')[0]

        if self._timelapse is not None:
            temporary_folder = self._timelapse.get_current_temporary_folder()
        else:
            temporary_folder = self._octolapse_settings.main_settings.get_temporary_directory(
                self.get_plugin_data_folder()
            )
        """Public access function to get the latest snapshot image"""
        if file_type == 'snapshot':
            # get the latest snapshot image
            filename = utility.get_latest_snapshot_download_path(
                temporary_folder, guid, self._basefolder)
            # if not os.path.isfile(filename):
            #     # we haven't captured any images, return the built in png.
            #     filename = utility.get_no_snapshot_image_download_path(
            #         self._basefolder)
        elif file_type == 'thumbnail':
            # get the latest snapshot image
            filename = utility.get_latest_snapshot_thumbnail_download_path(
                temporary_folder, guid, self._basefolder)
            # if not os.path.isfile(filename):
            #     # we haven't captured any images, return the built in png.
            #     filename = utility.get_no_snapshot_image_download_path(
            #         self._basefolder)
        else:
            # we don't recognize the snapshot type
            filename = utility.get_error_image_download_path(self._basefolder)

        if not os.path.isfile(filename):
            raise tornado.web.HTTPError(404)
        return filename

    # Callback Handler for /downloadFile
    # uses the OctolapseLargeResponseHandler
    def download_file_request(self, request_handler):

        def clean_temp_folder(file_path=None, file_directory=None):
            # delete the temp file and directory
            if file_path:
                os.unlink(file_path)
            if file_directory and os.path.isdir(file_directory):
                if not os.listdir(file_directory):
                    utility.rmtree(file_directory)

        download_file_path = None
        # get the args
        file_type = request_handler.get_query_arguments('type')[0]
        if file_type == 'profile':
            # get the parameters
            profile_type = request_handler.get_query_arguments("profile_type")[0]
            guid = request_handler.get_query_arguments("guid")[0]
            # get the profile settings
            profile_json = self._octolapse_settings.get_profile_export_json(profile_type, guid)

            # create a temp file
            temp_directory = mkdtemp()
            temp_file_path = os.path.join(temp_directory, "profile_setting_json.json")

            # write the settings file
            with open(temp_file_path, "w") as settings_file:
                settings_file.write(profile_json)

            request_handler.after_request_internal = clean_temp_folder
            request_handler.after_request_internal_args = {
                'file_path': temp_file_path,
                'file_directory': temp_directory
            }
            # set the download file name and full path
            request_handler.download_file_name = "{0}_Profile.json".format(profile_type)
            full_path = temp_file_path
        elif file_type == 'log':
            full_path = self.get_log_file_path()
        elif file_type == 'settings':
            full_path = self.get_settings_file_path()
        elif file_type == 'failed_rendering':
            job_guid = request_handler.get_query_arguments("job_guid")[0]
            camera_guid = request_handler.get_query_arguments("camera_guid")[0]

            temp_directory = self._octolapse_settings.main_settings.get_temporary_directory(
                self.get_plugin_data_folder()
            )

            temp_archive_directory = utility.get_temporary_archive_directory(temp_directory)
            temp_archive_path = utility.get_temporary_archive_path(temp_directory)

            file_name = self._rendering_processor.archive_unfinished_job(
                temp_directory,
                job_guid,
                camera_guid,
                temp_archive_path,
                is_download=True
            )
            if file_name:
                request_handler.download_file_name = file_name

            request_handler.after_request_internal = clean_temp_folder
            request_handler.after_request_internal_args = {
                'file_path': temp_archive_path,
                'file_directory': temp_archive_directory
            }
            full_path = temp_archive_path
        elif file_type in ['timelapse_octolapse', 'snapshot_archive', 'timelapse_octoprint']:
            #file_name = utility.unquote(request_handler.get_query_arguments('name')[0])
            file_name = request_handler.get_query_arguments('name')[0]
            # Don't allow any subdirectory access
            if not OctolapsePlugin.file_name_allowed(file_name):
                raise tornado.web.HTTPError(500)

            directory = self.get_file_directory(file_type, file_name)
            if not directory:
                raise tornado.web.HTTPError(500)

            # make sure the file exists
            full_path = os.path.join(directory, file_name)

        if not os.path.isfile(full_path):
            raise tornado.web.HTTPError(404)
        return full_path

    @octoprint.plugin.BlueprintPlugin.route("/deleteFile", methods=["POST"])
    @restricted_access
    def delete_file_request(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            # get the parameters
            request_values = request.get_json()
            file_type = request_values["type"]
            file_name = utility.unquote(request_values["id"])
            file_size = request_values["size"]
            client_id = request_values["client_id"]

            directory = self.get_file_directory(file_type, file_name)
            if not directory:
                return jsonify({
                    'success': False,
                    'error': 'The requested file type is not allowed.'
                }), 403

            if not OctolapsePlugin.file_name_allowed(file_name):
                return jsonify({
                    'success': False,
                    'error': 'The requested file type is not allowed.'
                }), 403

            # get the full file path
            full_path = os.path.join(directory, file_name)
            # make sure the file exists
            if not os.path.isfile(full_path):
                return jsonify({
                    'success': False,
                    'error': 'The requested file does not exist.'
                }), 404
            # remove the file
            utility.remove(full_path)
            file_info = {
                "type": file_type,
                "name": file_name,
                "size": file_size
            }
            self.send_files_changed_message(file_info, 'removed', client_id)
            return jsonify({
                'success': True
            })

    @octoprint.plugin.BlueprintPlugin.route("/stopTimelapse", methods=["POST"])
    @restricted_access
    def stop_timelapse_request(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            self._timelapse.stop_snapshots()
            return jsonify({'success': True})

    @octoprint.plugin.BlueprintPlugin.route("/previewStabilization", methods=["POST"])
    @restricted_access
    def preview_stabilization(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            # make sure we aren't printing
            if not self._printer.is_ready():
                error = "Cannot preview the stabilization because the printer is either printing or is a non-operational " \
                        "state, or is disconnected.  Check the 'State' of your printer on the left side of the screen " \
                        "and make sure it is connected and operational"
                logger.error(error)
                return jsonify({'success': False, 'error': error})
            with self._printer.job_on_hold():
                # get the current stabilization
                current_stabilization = self._octolapse_settings.profiles.current_stabilization()
                assert(isinstance(current_stabilization, StabilizationProfile))
                # get the current trigger
                current_trigger = self._octolapse_settings.profiles.current_trigger()
                assert (isinstance(current_trigger, TriggerProfile))
                # get the current printer
                current_printer = self._octolapse_settings.profiles.current_printer()
                if current_printer is None:
                    error = "Cannot preview the stabilization because no printer profile is selected.  Please select " \
                            "and configure a printer profile and try again."
                    logger.error(error)
                    return jsonify({'success': False, 'error': error}), 200, {'ContentType': 'application/json'}
                assert (isinstance(current_printer, PrinterProfile))
                # if both the X and Y axis are disabled, or the trigger is a smart trigger with snap to print enabled, return
                # an error.
                if (
                    current_stabilization.x_type == StabilizationProfile.STABILIZATION_AXIS_TYPE_DISABLED and
                    current_stabilization.y_type == StabilizationProfile.STABILIZATION_AXIS_TYPE_DISABLED
                ):
                    error = "Cannot preview the stabilization because both the X and Y axis are disabled.  Please enable at " \
                            "least one stabilized axis and try again."
                    logger.error(error)
                    return jsonify({'success': False, 'error': error})

                if (
                        current_trigger.trigger_type == TriggerProfile.TRIGGER_TYPE_SMART and
                        current_trigger.smart_layer_trigger_type == TriggerProfile.SMART_TRIGGER_TYPE_SNAP_TO_PRINT
                ):
                    error = "Cannot preview the stabilization when using a snap-to-print trigger."
                    logger.error(error)
                    return jsonify({'success': False, 'error': error})

                gcode_array = Commands.string_to_gcode_array(current_printer.home_axis_gcode)
                if len(gcode_array) < 1:
                    error = "Cannot preview stabilization.  The home axis gcode script in your printer profile does not " \
                            "contain any valid gcodes.  Please add a script to home your printer to the printer profile and " \
                            "try again."
                    logger.error(error)
                    return jsonify({'success': False, 'error': error})


                overridable_printer_profile_settings = current_printer.get_overridable_profile_settings(
                    self.get_octoprint_g90_influences_extruder(),
                    self.get_octoprint_printer_profile()
                )
                # create a snapshot gcode generator object
                gcode_generator = SnapshotGcodeGenerator(
                    self._octolapse_settings, overridable_printer_profile_settings
                )

                # get the stabilization point
                stabilization_point = gcode_generator.get_snapshot_position(None, None)
                if stabilization_point is None and stabilization_point["x"] is None and stabilization_point["y"] is None:
                    error = "No stabilization points were returned.  Cannot preview stabilization."
                    logger.error(error)
                    return jsonify({'success': False, 'error': error})

                # get the movement feedrate from the Octoprint printer profile, or use 6000 as a default

                default_feedrate = 6000

                feedrate_x = default_feedrate
                feedrate_y = default_feedrate
                octoprint_printer_profile = self.get_octoprint_printer_profile()
                axes = octoprint_printer_profile.get("axes", None)
                if axes is not None:
                    x_axis = axes.get("x", {"speed": default_feedrate})
                    feedrate_x = x_axis.get("speed", default_feedrate)
                    y_axis = axes.get("y", {"speed": default_feedrate})
                    feedrate_y = y_axis.get("speed", default_feedrate)

                feedrate = min(feedrate_x, feedrate_y)
                # create the gcode necessary to move the extruder to the stabilization position and add it to the gcode array
                gcode_array.append(
                    SnapshotGcodeGenerator.get_gcode_travel(stabilization_point["x"], stabilization_point["y"], feedrate)
                )

                # send the gcode to the printer
                self._printer.commands(gcode_array, tags={"preview-stabilization"})
                return jsonify({'success': True})

    @octoprint.plugin.BlueprintPlugin.route("/saveMainSettings", methods=["POST"])
    @restricted_access
    def save_main_settings_request(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            client_id = request_values["client_id"]

            # make sure to test the provided directories first
            main_settings_test = MainSettings(__version__, __git_version__)
            main_settings_test.update(request_values)
            success, results = main_settings_test.test_directories(
                self.get_plugin_data_folder(),
                self.get_octoprint_timelapse_location()
            )
            if not success:
                data = {
                    'success': False,
                    'error': "The provided directories did not pass testing.  Could not save settings."
                }
            else:
                self._octolapse_settings.main_settings.update(request_values)
                # save the updated settings to a file.
                self.save_settings()
                # inform the rendering processor of the temporary directory, since it may have changed
                success, results = self._rendering_processor.update_directories()
                # inform any clients who are listening that they need to update their state.
                self.send_state_changed_message(None, client_id)
                if success:
                    if (
                        results["temporary_directory_changed"] or
                        results["snapshot_archive_directory_changed"] or
                        results["timelapse_directory_changed"]
                    ):
                        self.send_directories_changed_message(results)

                    data = {
                        "success": True
                    }
                else:
                    data = {
                        'success': False,
                        'error': "The provided directories did not pass testing.  Could not save settings."
                    }

            return jsonify(data)

    @octoprint.plugin.BlueprintPlugin.route("/setEnabled", methods=["POST"])
    @restricted_access
    def set_enabled(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            client_id = request_values["client_id"]
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
            self.send_state_changed_message(None, client_id)
            data = {
                'success': True,
                'enabled': enable_octolapse
            }
            return jsonify(data)

    @octoprint.plugin.BlueprintPlugin.route("/setTestMode", methods=["POST"])
    @restricted_access
    def set_test_mode_request(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            client_id = request_values["client_id"]
            test_mode_enabled = request_values["test_mode_enabled"]
            if (
                self._timelapse is not None and
                self._timelapse.is_timelapse_active()
            ):
                self.send_plugin_message(
                    "test-mode-changed-running",
                    "Test mode has been changed, but Octolapse is currently active.  The new setting will take effect"
                    " after the current print ends"
                )
            # save the updated settings to a file.
            self._octolapse_settings.main_settings.test_mode_enabled = test_mode_enabled
            self.save_settings()
            self.send_state_changed_message(None, client_id)
            data = {
                'success': True,
                'enabled': test_mode_enabled
            }
            return jsonify(data)

    @octoprint.plugin.BlueprintPlugin.route("/setPreviewSnapshotPlans", methods=["POST"])
    @restricted_access
    def set_preview_snapshot_plans_request(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            client_id = request_values["client_id"]
            preview_snapshot_plans_enabled = request_values["preview_snapshot_plans_enabled"]
            # save the updated settings to a file.
            self._octolapse_settings.main_settings.preview_snapshot_plans = preview_snapshot_plans_enabled
            self.save_settings()
            self.send_state_changed_message(None, client_id)
            data = {
                'success': True,
                'enabled': preview_snapshot_plans_enabled
            }
            return jsonify(data)

    @octoprint.plugin.BlueprintPlugin.route("/toggleInfoPanel", methods=["POST"])
    @restricted_access
    def toggle_info_panel(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            client_id = request_values["client_id"]
            panel_type = request_values["panel_type"]
            enabled = None
            if panel_type == "show_printer_state_changes":
                enabled = not self._octolapse_settings.main_settings.show_printer_state_changes
                self._octolapse_settings.main_settings.show_printer_state_changes = enabled
            elif panel_type == "show_position_changes":
                enabled = not self._octolapse_settings.main_settings.show_position_changes
                self._octolapse_settings.main_settings.show_position_changes = enabled
            elif panel_type == "show_extruder_state_changes":
                enabled = not self._octolapse_settings.main_settings.show_extruder_state_changes
                self._octolapse_settings.main_settings.show_extruder_state_changes = enabled
            elif panel_type == "show_trigger_state_changes":
                enabled = not self._octolapse_settings.main_settings.show_trigger_state_changes
                self._octolapse_settings.main_settings.show_trigger_state_changes = enabled
            elif panel_type == "show_snapshot_plan_information":
                enabled = not self._octolapse_settings.main_settings.show_snapshot_plan_information
                self._octolapse_settings.main_settings.show_snapshot_plan_information = enabled
            else:
                return jsonify({'error': "Unknown panel_type."}), 500

            # save the updated settings to a file.
            self.save_settings()

            # inform any clients who are listening that they need to update their state.
            self.send_state_changed_message(None, client_id)
            data = {
                'success': True,
                'enabled': enabled
            }
            return jsonify(data)

    @octoprint.plugin.BlueprintPlugin.route("/addUpdateProfile", methods=["POST"])
    @restricted_access
    def add_update_profile_request(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            try:
                request_values = request.get_json()
                profile_type = request_values["profileType"]
                profile = request_values["profile"]
                client_id = request_values["client_id"]
                updated_profile = self._octolapse_settings.profiles.add_update_profile(profile_type, profile)
                # save the updated settings to a file.
                self.save_settings()
                self.send_settings_changed_message(client_id)
                return updated_profile.to_json(), 200, {'ContentType': 'application/json'}
            except Exception as e:
                logger.exception("Error encountered in /addUpdateProfile.")
            return jsonify({}), 500

    @octoprint.plugin.BlueprintPlugin.route("/removeProfile", methods=["POST"])
    @restricted_access
    def remove_profile_request(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            profile_type = request_values["profileType"]
            guid = request_values["guid"]
            client_id = request_values["client_id"]
            if not self._octolapse_settings.profiles.remove_profile(profile_type, guid):
                return (
                    jsonify({
                        'success': False,
                        'error': "Cannot delete the default profile."
                    })
                )
            # save the updated settings to a file.
            self.save_settings()
            self.send_settings_changed_message(client_id)
            return jsonify({'success': True})

    @octoprint.plugin.BlueprintPlugin.route("/setCurrentProfile", methods=["POST"])
    @restricted_access
    def set_current_profile_request(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            profile_type = request_values["profileType"]
            guid = request_values["guid"]
            client_id = request_values["client_id"]
            self._octolapse_settings.profiles.set_current_profile(profile_type, guid)
            self.save_settings()
            self.send_settings_changed_message(client_id)
            return jsonify({'success': True, 'guid': request_values["guid"]})

    @octoprint.plugin.BlueprintPlugin.route("/setCurrentCameraProfile", methods=["POST"])
    @restricted_access
    def set_current_camera_profile(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            # this setting will only determine which profile will be the default within
            # the snapshot preview if a new instance is loaded.  Save the settings, but
            # do not notify other clients
            request_values = request.get_json()
            guid = request_values["guid"]
            self._octolapse_settings.profiles.current_camera_profile_guid = guid
            self.save_settings()
            return jsonify({'success': True, 'guid': request_values["guid"]})

    @octoprint.plugin.BlueprintPlugin.route("/restoreDefaults", methods=["POST"])
    @restricted_access
    def restore_defaults_request(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            client_id = request_values["client_id"]
            try:
                self.load_settings(force_defaults=True)
                self.send_settings_changed_message(client_id)
                # TODO:  Check for updates after settings restore, but send request from client.
                return self._octolapse_settings.to_json(), 200, {'ContentType': 'application/json'}
            except Exception as e:
                logger.exception("Failed to restore the defaults in /restoreDefaults.")
            return jsonify({'success': False}), 500

    @octoprint.plugin.BlueprintPlugin.route("/loadMainSettings", methods=["POST"])
    def load_main_settings_request(self):
        data = {'success': True}
        data.update(self._octolapse_settings.main_settings.to_dict())
        return jsonify(data)

    @octoprint.plugin.BlueprintPlugin.route("/loadState", methods=["POST"])
    def load_state_request(self):
        # TODO:  add a timer to wait for the settings to load!
        if self._octolapse_settings is None:
            message = "Unable to load values from Octolapse.Settings, it hasn't been initialized yet.  Please wait a few minutes and try again.  If the problem persists, please check plugin_octolapse.log for exceptions."
            logger.error(message)
            return jsonify({"error": True, "error_message": message}), 500
        # TODO:  add a timer to wait for the timelapse to be initialized
        if self._timelapse is None:
            message = "Unable to load values from Octolapse.Timelapse, it hasn't been initialized yet.  Please wait a few minutes and try again.  If the problem persists, please check plugin_octolapse.log for exceptions."
            return jsonify({"error": True, "error_message": message}), 500
        data = self.get_state_request_dict()
        return jsonify(data)

    def get_state_request_dict(self):
        state_date = None
        if self._timelapse is not None:
            state_data = self._timelapse.to_state_dict(include_timelapse_start_data=True)
        data = {
            "main_settings": self._octolapse_settings.main_settings.to_dict(),
            "status": self.get_status_dict(include_profiles=True),
            "state": state_data,
            "success": True
        }
        if self.preprocessing_job_guid and self.saved_snapshot_plans:
            data["snapshot_plan_preview"] = self.get_snapshot_plan_preview_dict()
        return data

    @octoprint.plugin.BlueprintPlugin.route("/loadSettingsAndState", methods=["POST"])
    @restricted_access
    def load_settings_and_state_request(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            try:
                if self._octolapse_settings is None:
                    message = "Unable to load values from Octolapse.Settings, it hasn't been initialized yet. Please " \
                              "wait a few minutes and try again.  If the problem persists, please check " \
                              "plugin_octolapse.log for exceptions. "
                    logger.error(message)
                    return jsonify({"error": True, "error_message": message}), 500
                # TODO:  add a timer to wait for the timelapse to be initialized
                if self._timelapse is None:
                    message = "Unable to load values from Octolapse.Timelapse, it hasn't been initialized yet. Please" \
                              " wait a few minutes and try again.  If the problem persists, please check " \
                              "plugin_octolapse.log for exceptions. "
                    return jsonify({"error": True, "error_message": message}), 500
                data = self.get_state_request_dict()
                data["settings"] = self._octolapse_settings
                return json.dumps(data, cls=SettingsJsonEncoder), 200, {'ContentType': 'application/json'}
            except Exception as e:
                logger.exception("An unexpected exception occurred while loading the settings and state.")
                raise e

    @octoprint.plugin.BlueprintPlugin.route("/updateProfileFromServer", methods=["POST"])
    @restricted_access
    def update_profile_from_server(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            logger.info("Attempting to update the current profile from the server")
            request_values = request.get_json()
            profile_type = request_values["type"]
            key_values = request_values["key_values"]
            profile_dict = request_values["profile"]
            try:
                server_profile_dict = ExternalSettings.get_profile(self._plugin_version, profile_type, key_values)
            except ExternalSettingsError as e:
                logger.exception("An error occurred while retrieving profiles from the profile server.")
                return jsonify(
                    {
                        "success": False,
                        "message": e.message
                    }
                ), 500

            # update the profile
            updated_profile = self._octolapse_settings.profiles.update_from_server_profile(
                profile_type, profile_dict, server_profile_dict
            )
            return jsonify(
                {
                    "success": True,
                    "profile_json": updated_profile.to_json()
                }
            )

    @octoprint.plugin.BlueprintPlugin.route("/checkForProfileUpdates", methods=["POST"])
    @restricted_access
    def check_for_profile_updates_request(self):
        request_values = request.get_json()
        is_silent_test = request_values["is_silent_test"]
        # if this is a silent update, make sure automatic updates are enabled
        if is_silent_test and not self._octolapse_settings.main_settings.automatic_updates_enabled:
            return jsonify({
                "success": True,
                "available_profile_count": 0
            })
        # ignore suppression only if this is not a silent test, which is performed when the client is done
        # loading
        ignore_suppression = not is_silent_test
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            logger.info("Attempting to update all current profile from the server")
            available_profiles = self.check_for_updates(ignore_suppression=ignore_suppression)
            available_profile_count = 0
            if available_profiles:
                # remove python 2 support
                # for key, profile_type in six.iteritems(available_profiles):
                for key, profile_type in available_profiles.items():
                    available_profile_count += len(profile_type)
            return jsonify({
                "success": True,
                "available_profile_count": available_profile_count
            })

    @octoprint.plugin.BlueprintPlugin.route("/updateProfilesFromServer", methods=["POST"])
    @restricted_access
    def update_profiles_from_server(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            logger.info("Attempting to update all current profile from the server")
            request_values = request.get_json()
            client_id = request_values["client_id"]
            profiles_to_update = self.check_for_updates(True)

            with self.automatic_update_lock:
                if not profiles_to_update:
                    return jsonify({
                        "num_updated": 0
                    })
                num_profiles = 0
                # remove python 2 support
                # for profile_type, updatable_profiles in six.iteritems(profiles_to_update):
                for profile_type, updatable_profiles in profiles_to_update.items():
                    # now iterate through the printer profiles
                    for updatable_profile in updatable_profiles:
                        current_profile = self._octolapse_settings.profiles.get_profile(
                            profile_type, updatable_profile["guid"]
                        )
                        try:
                            server_profile_dict = ExternalSettings.get_profile(
                                self._plugin_version, profile_type,
                                updatable_profile["key_values"]
                            )
                        except ExternalSettingsError as e:
                            logger.exception("An error occurred while getting a profile from the profile server.")
                            return jsonify(
                                {
                                    "message": e.message
                                }
                            ), 500

                        # update the profile

                        updated_profile = self._octolapse_settings.profiles.update_from_server_profile(
                            profile_type, current_profile.to_dict(), server_profile_dict
                        )
                        current_profile.update(updated_profile)
                        num_profiles += 1

                self.save_settings()
                self.send_settings_changed_message(client_id)
                return jsonify({
                    "settings": self._octolapse_settings.to_json(),
                    "num_updated": num_profiles
                })

    @octoprint.plugin.BlueprintPlugin.route("/suppressServerUpdates", methods=["POST"])
    @restricted_access
    def suppress_server_updates(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            logger.info("Suppressing updates for all current updatable profiles.")
            request_values = request.get_json()
            client_id = request_values["client_id"]

            with self.automatic_update_lock:
                has_updated = False
                # remove python 2 support
                # for profile_type, updatable_profiles in six.iteritems(self._octolapse_settings.profiles.get_updatable_profiles_dict()):
                for profile_type, updatable_profiles in self._octolapse_settings.profiles.get_updatable_profiles_dict().items():
                    # now iterate through the printer profiles
                    for updatable_profile in updatable_profiles:
                        current_profile = self._octolapse_settings.profiles.get_profile(
                            profile_type, updatable_profile["guid"]
                        )
                        # get the server profile info
                        server_profile = ExternalSettings.get_available_profile_for_profile(
                            self.available_profiles, current_profile, profile_type
                        )
                        if server_profile is not None:
                            has_updated = True
                            current_profile.suppress_updates(server_profile)
                if has_updated:
                    self.save_settings()
                    self.send_settings_changed_message(client_id)
            return self._octolapse_settings.to_json(), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/importSettings", methods=["POST"])
    @restricted_access
    def import_settings(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            logger.info("Importing settings from file")
            import_method = 'file'
            import_text = ''
            client_id = ''
            # get the json request values
            request_values = request.get_json()
            message = ""

            if request_values is not None:
                import_method = request_values["import_method"]
                import_text = request_values["import_text"]
                client_id = request_values["client_id"]

            try:
                if import_method == "file":
                    logger.debug("Importing settings from file.")
                    # Parse the request.
                    settings_path = request.values['octolapse_settings_import_path_upload.path']
                    client_id = request.values['client_id']
                    self._octolapse_settings = self._octolapse_settings.import_settings_from_file(
                        settings_path,
                        self._plugin_version,
                        __git_version__,
                        self.get_default_settings_folder(),
                        self.get_plugin_data_folder(),
                        self.available_profiles
                    )
                    message = "Your settings have been updated from the supplied file."
                elif import_method == "text":
                    logger.debug("Importing settings from text.")
                    # convert the settings json to a python object
                    self._octolapse_settings = self._octolapse_settings.import_settings_from_text(
                        import_text,
                        self._plugin_version,
                        __git_version__,
                        self.get_default_settings_folder(),
                        self.get_plugin_data_folder(),
                        self.available_profiles
                    )
                    message = "Your settings have been updated from the uploaded text."
                else:
                    raise Exception("Unknown Import Method")
            except Exception as e:
                logger.exception("An error occurred in import_settings_request.")
                message = "Unable to import the provided settings, see plugin_octolapse.log for more information."
                if type(e) is OctolapseSettings.IncorrectSettingsVersionException:
                    message = e.message

                return jsonify(
                    {
                        "success": False,
                        "msg": message
                    }
                )

            # if we're this far we need to save the settings.
            self.save_settings()

            # send a state changed message
            self.send_settings_changed_message(client_id)

            return jsonify(
                {
                    "success": True,
                    "settings": self._octolapse_settings.to_json(),
                    "msg": message
                }
            )

    @octoprint.plugin.BlueprintPlugin.route("/getMjpgStreamerControls", methods=["POST"])
    @restricted_access
    def get_mjpg_streamer_controls(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            profile = request_values["profile"]
            server_type = profile["server_type"]
            camera_name = profile["name"]
            address = profile["address"]
            username = profile["username"]
            password = profile["password"]
            ignore_ssl_error = profile["ignore_ssl_error"]

            guid = None if "guid" not in profile else profile["guid"]
            try:
                success, errors, webcam_settings = camera.CameraControl.get_webcam_settings(
                    server_type,
                    camera_name,
                    address,
                    username,
                    password,
                    ignore_ssl_error
                )
            except Exception as e:
                logger.exception("An exception occurred while retrieving the current camera settings.")
                raise e

            if not success:
                return jsonify({'success': False, 'error': errors}), 500

            if guid and guid in self._octolapse_settings.profiles.cameras:
                # Create a new camera profile and update from the supplied profile.
                camera_profile = CameraProfile()
                camera_profile.update(profile)
                matches = False
                if server_type == MjpgStreamer.server_type:
                    if camera_profile.webcam_settings.mjpg_streamer.controls_match_server(
                        webcam_settings["webcam_settings"]["mjpg_streamer"]["controls"]
                    ):
                        matches = True

                if len(camera_profile.webcam_settings.mjpg_streamer.controls) == 0:
                    # get the existing settings since we don't want to use the defaults
                    camera_profile.webcam_settings.mjpg_streamer.controls = {}
                    camera_profile.webcam_settings.mjpg_streamer.update(
                        webcam_settings["webcam_settings"]["mjpg_streamer"]
                    )

                    # see if we know about the camera type
                    webcam_type = camera.CameraControl.get_webcam_type(
                        self._basefolder,
                        MjpgStreamer.server_type,
                        webcam_settings["webcam_settings"]["mjpg_streamer"]["controls"]
                    )
                    # turn the controls into a dict
                    webcam_settings = {
                        "webcam_settings": {
                            "type": webcam_type,
                            "mjpg_streamer": {
                                "controls": camera_profile.webcam_settings.mjpg_streamer.controls
                            }
                        },
                        "new_preferences_available": False
                    }
                else:
                    webcam_settings = {
                        "webcam_settings": {
                            "mjpg_streamer": {
                                "controls": camera_profile.webcam_settings.mjpg_streamer.controls
                            }
                        },
                        "new_preferences_available": (
                            not matches and len(webcam_settings["webcam_settings"]["mjpg_streamer"]["controls"]) > 0
                        )
                    }
            # if we're here, we should be good, extract and return the camera settings
            return json.dumps(
                {
                    'success': True, 'settings': webcam_settings
                }, cls=SettingsJsonEncoder), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/getWebcamImagePreferences", methods=["POST"])
    @restricted_access
    def get_webcam_image_preferences(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            guid = request_values["guid"]
            replace = request_values["replace"]
            if guid not in self._octolapse_settings.profiles.cameras:
                return (
                    jsonify({
                        'success': False,
                        'error': 'The requested camera profile does not exist.  Cannot adjust settings.'
                    }), 404
                )
            profile = self._octolapse_settings.profiles.cameras[guid]
            if not profile.camera_type == 'webcam':
                return jsonify({
                    'success': False,
                    'error': 'The selected camera is not a webcam.  Cannot adjust settings.'
                }), 500

            camera_profile = self._octolapse_settings.profiles.cameras[guid].clone()

            success, errors, webcam_settings = camera.CameraControl.get_webcam_settings(
                camera_profile.webcam_settings.server_type,
                camera_profile.name,
                camera_profile.webcam_settings.address,
                camera_profile.webcam_settings.username,
                camera_profile.webcam_settings.password,
                camera_profile.webcam_settings.ignore_ssl_error
            )

            if not success:
                return jsonify({
                    'success': False, 'error': errors
                }), 500

            # Check to see if we need to update our existing camera image settings.  We only want to do this
            # if the control set has changed (minus the actual value)

            if camera_profile.webcam_settings.server_type == MjpgStreamer.server_type:
                matches = False
                if camera_profile.webcam_settings.mjpg_streamer.controls_match_server(
                    webcam_settings["webcam_settings"]["mjpg_streamer"]["controls"]
                ):
                    matches = True

                if replace or len(camera_profile.webcam_settings.mjpg_streamer.controls) == 0:
                    # get the existing settings since we don't want to use the defaults
                    camera_profile.webcam_settings.mjpg_streamer.controls = {}
                    camera_profile.webcam_settings.mjpg_streamer.update(
                        webcam_settings["webcam_settings"]["mjpg_streamer"]
                    )
                    # see if we know about the camera type
                    webcam_type = camera.CameraControl.get_webcam_type(
                        self._basefolder,
                        MjpgStreamer.server_type,
                        webcam_settings["webcam_settings"]["mjpg_streamer"]["controls"]
                    )
                    camera_profile.webcam_settings.type = webcam_type
                    webcam_settings = {
                        "name": camera_profile.name,
                        "guid": camera_profile.guid,
                        "new_preferences_available": False,
                        "webcam_settings": camera_profile.webcam_settings
                    }
                else:
                    webcam_settings = {
                        "name": camera_profile.name,
                        "guid": camera_profile.guid,
                        "new_preferences_available": (
                            not matches and len(webcam_settings["webcam_settings"]["mjpg_streamer"]["controls"]) > 0
                        ),
                        "webcam_settings": camera_profile.webcam_settings
                    }
            else:
                return jsonify({
                    'success': False,
                    'error': 'The webcam you are using is not streaming via mjpg-streamer, which is the only server '
                             'supported currently. '
                }), 500
            # if we're here, we should be good, extract and return the camera settings
            return json.dumps({
                    'success': True, 'settings': webcam_settings
                }, cls=SettingsJsonEncoder), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/getWebcamType", methods=["POST"])
    @restricted_access
    def get_webcam_type(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            server_type = request_values["server_type"]
            camera_name = request_values["camera_name"]
            address = request_values["address"]
            username = request_values["username"]
            password = request_values["password"]
            ignore_ssl_error = request_values["ignore_ssl_error"]
            success, errors, webcam_settings = camera.CameraControl.get_webcam_settings(
                server_type,
                camera_name,
                address,
                username,
                password,
                ignore_ssl_error
            )
            if not success:
                return jsonify({
                    'success': False,
                    'error': errors
                }), 500,

            if server_type == MjpgStreamer.server_type:
                webcam_type = camera.CameraControl.get_webcam_type(
                    self._basefolder, server_type, webcam_settings["webcam_settings"]["mjpg_streamer"]["controls"]
                )
            else:
                webcam_type = False

            # if we're here, we should be good, extract and return the camera settings
            return json.dumps({
                'success': True, 'type': webcam_type
            }, cls=SettingsJsonEncoder), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/testCameraSettingsApply", methods=["POST"])
    @restricted_access
    def test_camera_settings_apply(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            profile = request_values["profile"]
            camera_profile = CameraProfile.create_from(profile)
            success, errors = camera.CameraControl.test_web_camera_image_preferences(camera_profile)
            return jsonify({
                'success': success,
                'error': errors
            })

    @octoprint.plugin.BlueprintPlugin.route("/applyCameraSettings", methods=["POST"])
    @restricted_access
    def apply_camera_settings_request(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            request_type = request_values["type"]
            # Get the settings we need to run apply cameras ettings
            if request_type == "by_guid":
                guid = request_values["guid"]
                # get the current camera profile
                if guid not in self._octolapse_settings.profiles.cameras:
                    return jsonify({
                        'success': False,
                        'error': 'The requested camera profile does not exist.  Cannot adjust settings.'
                    }), 404
                camera_profile = self._octolapse_settings.profiles.cameras[guid]
            elif request_type == "ui-settings-update":
                # create a new profile from the profile dict
                webcam_settings = request_values["settings"]
                camera_profile = CameraProfile()
                camera_profile.name = webcam_settings["name"]
                camera_profile.guid = webcam_settings["guid"]
                camera_profile.webcam_settings.update(webcam_settings)
            else:
                return jsonify({
                    'success': False,
                    'error': 'Unknown request type: {0}.'.format(request_type)
                }), 500

            # Make sure the current profile is a webcam
            if not camera_profile.camera_type == 'webcam':
                return jsonify({
                    'success': False,
                    'error': 'The selected camera is not a webcam.  Cannot adjust settings.'
                }), 500

            # Apply the settings
            try:
                success, error = self.apply_camera_settings([camera_profile])
            except camera.CameraError as e:
                logger.exception("Failed to apply webcam settings in /applyCameraSettings.")
                return jsonify({
                    'success': False,
                    'error': "Octolapse was unable to apply image preferences to your webcam.  See plugin_octolapse.log for details. "
                 })

            return jsonify({
                'success': success,
                'error': error
            })

    @octoprint.plugin.BlueprintPlugin.route("/saveWebcamSettings", methods=["POST"])
    @restricted_access
    def save_webcam_settings(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            guid = request_values["guid"]
            webcam_settings = request_values["webcam_settings"]

            # get the current camera profile
            if guid not in self._octolapse_settings.profiles.cameras:
                return jsonify({
                    'success': False,
                    'error': 'The requested camera profile does not exist.  Cannot adjust settings.'
                }), 404
            profile = self._octolapse_settings.profiles.cameras[guid]
            if not profile.camera_type == 'webcam':
                return jsonify({
                    'success': False,
                    'error': 'The selected camera is not a webcam.  Cannot adjust settings.'
                }), 500

            camera_profile = self._octolapse_settings.profiles.cameras[guid]
            camera_profile.webcam_settings.update(webcam_settings)
            self.save_settings()

            try:
                success, error = camera.CameraControl.apply_camera_settings([camera_profile])
            except camera.CameraError as e:
                logger.exception("Failed to save webcam settings in /saveWebcamSettings.")
                return jsonify({
                    'success': False,
                    'error': e.message
                })

            return jsonify({
                'success': success,
                'error': error
            })

    @octoprint.plugin.BlueprintPlugin.route("/loadWebcamDefaults", methods=["POST"])
    @restricted_access
    def load_webcam_defaults(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            server_type = request_values["server_type"]
            camera_name = request_values["camera_name"]
            address = request_values["address"]
            username = request_values["username"]
            password = request_values["password"]
            ignore_ssl_error = request_values["ignore_ssl_error"]

            success, errors, defaults = camera.CameraControl.load_webcam_defaults(
                server_type,
                camera_name,
                address,
                username,
                password,
                ignore_ssl_error
            )
            ret_val = {
                'webcam_settings': {
                    'mjpg_streamer': {
                        'controls': defaults
                    }
                }
            }
            return jsonify({
                'success': success,
                'defaults': ret_val,
                'error': errors
            })

    @octoprint.plugin.BlueprintPlugin.route("/applyWebcamSetting", methods=["POST"])
    @restricted_access
    def apply_webcam_setting_request(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            server_type = request_values["server_type"]
            camera_name = request_values["camera_name"]
            address = request_values["address"]
            username = request_values["username"]
            password = request_values["password"]
            ignore_ssl_error = request_values["ignore_ssl_error"]
            setting = request_values["setting"]

            # apply a single setting to the camera
            try:
                success, error = camera.CameraControl.apply_webcam_setting(
                    server_type,
                    setting,
                    camera_name,
                    address,
                    username,
                    password,
                    ignore_ssl_error,
                )
                if not success:
                    logger.error(error)
            except camera.CameraError as e:
                logger.exception("Failed to apply webcam settings in /applyWebcamSetting")
                return jsonify({
                    'success': False,
                    'error': e.message
                })
            error_string = ""
            if not success:
                error_string = error.message
            return jsonify({
                'success': success,
                'error': error_string
            })

    @octoprint.plugin.BlueprintPlugin.route("/testCamera", methods=["POST"])
    @restricted_access
    def test_camera_request(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            profile = request_values["profile"]
            camera_profile = CameraProfile.create_from(profile)
            success, errors = camera.CameraControl.test_web_camera(camera_profile)
            return jsonify({
                'success': success,
                'error': errors
            })

    @octoprint.plugin.BlueprintPlugin.route("/testCameraScript", methods=["POST"])
    @restricted_access
    def test_camera_script_request(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            success = False
            errors = None
            snapshot_created = False
            try:
                request_values = request.get_json()
                profile = request_values["profile"]
                script_type = request_values["script_type"]
                camera_profile = CameraProfile.create_from(profile)
                success, errors, snapshot_created = camera.CameraControl.test_script(camera_profile, script_type, self._basefolder)
            except Exception as e:
                logger.exception("An unexpected error occurred while executing the {0} script.".format(script_type))
                raise e
            return jsonify({
                'success': success,
                'error': errors,
                'snapshot_created': snapshot_created
            })

    @octoprint.plugin.BlueprintPlugin.route("/testDirectory", methods=["POST"])
    @restricted_access
    def test_directory_request(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            directory_type = request_values["type"]
            directory = request_values["directory"].strip()
            test_profile = MainSettings(self._plugin_version, __git_version__,)

            success = False
            errors = "An unknown directory type was requested for testing."
            directory_path = None
            if directory_type == "snapshot-archive":
                if len(directory) == 0:
                    directory = test_profile.get_snapshot_archive_directory(
                        self.get_plugin_data_folder()
                    )
                success, errors = MainSettings.test_directory(
                    directory
                )
            elif directory_type == "temporary":
                if len(directory) == 0:
                    directory = test_profile.get_temporary_directory(
                        self.get_plugin_data_folder()
                    )
                success, errors = MainSettings.test_directory(
                    directory
                )
            elif directory_type == "timelapse":
                if len(directory) == 0:
                    directory = test_profile.get_timelapse_directory(
                        self.get_octoprint_timelapse_location()
                    )
                success, errors = MainSettings.test_directory(
                    directory
                )

            return jsonify({
                'success': success,
                'error': errors,
            })

    @octoprint.plugin.BlueprintPlugin.route("/cancelPreprocessing", methods=["POST"])
    @restricted_access
    def cancel_preprocessing_request(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            preprocessing_job_guid = request_values["preprocessing_job_guid"]
            if (
                self.preprocessing_job_guid is None
                or preprocessing_job_guid != str(self.preprocessing_job_guid)
            ):
                # return without doing anything, this job is already over
                return jsonify({
                    'success': True
                })

            logger.info("Cancelling Preprocessing for /cancelPreprocessing.")
            # todo:  Check the current printing session and make sure it matches before canceling the print!
            self.reset_preprocessing()
            self._timelapse.release_job_on_hold_lock(reset=True)
            if self._printer.is_printing():
                self._printer.cancel_print(tags={'octolapse-startup-failed'})
            self.send_snapshot_preview_complete_message()
            return jsonify({
                'success': True
            })

    @octoprint.plugin.BlueprintPlugin.route("/acceptSnapshotPlanPreview", methods=["POST"])
    @restricted_access
    def accept_snapshot_plan_preview_request(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            preprocessing_job_guid = request_values["preprocessing_job_guid"]
            if (
                preprocessing_job_guid is not None and
                str(self.preprocessing_job_guid) == preprocessing_job_guid
            ):
                self.accept_snapshot_plan_preview(preprocessing_job_guid)
                return jsonify({
                    'success': True
                })
            return jsonify({
                'success': False
            })

    @octoprint.plugin.BlueprintPlugin.route("/toggleCamera", methods=["POST"])
    @restricted_access
    def toggle_camera(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            guid = request_values["guid"]
            client_id = request_values["client_id"]
            new_value = not self._octolapse_settings.profiles.cameras[guid].enabled
            self._octolapse_settings.profiles.cameras[guid].enabled = new_value
            self.save_settings()
            self.send_settings_changed_message(client_id)
            return jsonify({
                'success': True,
                'enabled': new_value,
            })

    @octoprint.plugin.BlueprintPlugin.route("/validateSnapshotCommand", methods=["POST"])
    @restricted_access
    def validate_snapshot_command(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            snapshot_command = request_values["snapshot_command"]
            valid = "true" if self._timelapse.validate_snapshot_command(snapshot_command) else ""
            return "\"{0}\"".format(valid), 200, {'ContentType': 'application/json'}

    @octoprint.plugin.BlueprintPlugin.route("/validateRenderingTemplate", methods=["POST"])
    @restricted_access
    def validate_rendering_template(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            template = request.form['octolapse_rendering_output_template']
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
    @restricted_access
    def validate_overlay_text_template(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            template = request.form['octolapse_rendering_overlay_text_template']
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
    def get_available_fonts(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            font_list = []
            try:
                font_list = utility.get_system_fonts(self._basefolder)
            except Exception as e:
                logger.exception("Unable to retrieve system fonts.")
                raise e
            return jsonify({
                "fonts": font_list
            })

    @octoprint.plugin.BlueprintPlugin.route("/rendering/previewOverlay", methods=["POST"])
    def preview_overlay(self):
        preview_image = None
        camera_image = None
        request_values = request.get_json()
        try:
            # Take a snapshot from the first active camera.
            active_cameras = self._octolapse_settings.profiles.active_cameras()

            for active_camera in active_cameras:
                if active_camera.camera_type != 'webcam':
                    continue
                try:
                    camera_image = snapshot.take_in_memory_snapshot(self._octolapse_settings, active_camera)
                except Exception as e:
                    logger.exception("Failed to take a snapshot. Falling back to solid color.")

            # Extract the profile from the request.
            try:
                rendering_profile = RenderingProfile().create_from(request_values)
            except Exception as e:
                logger.exception('Preview overlay request did not provide valid Rendering profile.')
                return jsonify({
                    'error': 'Request did not contain valid Rendering profile. Check octolapse log for details.'
                }), 400

            # Render a preview image.
            preview_image = render.preview_overlay(rendering_profile, image=camera_image)

            if preview_image is None:
                return jsonify({
                    'success': False
                }), 404

            # Use a buffer to base64 encode the image.
            img_io = BytesIO()
            preview_image.save(img_io, 'JPEG')
            img_io.seek(0)
            base64_encoded_image = base64.b64encode(img_io.getvalue())

            # Return a response. We have to return JSON because jQuery only knows how to parse JSON.
            return jsonify({
                'image': base64_encoded_image
            })
        finally:
            # cleanup
            if camera_image is not None:
                camera_image.close()
            if preview_image is not None:
                preview_image.close()

    @octoprint.plugin.BlueprintPlugin.route("/rendering/watermark", methods=["GET"])
    @restricted_access
    def get_available_watermarks(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
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
            return jsonify(data)

    @octoprint.plugin.BlueprintPlugin.route("/rendering/watermark/upload", methods=["POST"])
    @restricted_access
    def upload_watermark(self):
        # TODO(Shadowen): Receive chunked uploads properly.
        # It seems like this function is called once PER CHUNK rather than when the entire upload has completed.
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            # Parse the request.
            image_filename = request.values['image.name']
            # The path where the watermark file was saved by the uploader.
            watermark_temp_path = request.values['image.path']
            logger.debug("Receiving uploaded watermark %s.", image_filename)

            # Move the watermark from the (temp) upload location to a permanent location.
            # Maybe it could be uploaded directly there, but I don't know how to do that.
            # TODO(Shadowen): Retrieve watermarks_directory_name from config.yaml.
            watermarks_directory_name = "watermarks"
            # Ensure the watermarks directory exists.
            full_watermarks_dir = os.path.join(self.get_plugin_data_folder(), watermarks_directory_name)
            if not os.path.exists(full_watermarks_dir):
                logger.info("Creating watermarks directory at %s.".format(full_watermarks_dir))
                try:
                    os.makedirs(full_watermarks_dir)
                except OSError as e:
                    if e.errno == errno.EEXIST:
                        pass
                    else:
                        raise

            # Move the image.
            watermark_destination_path = os.path.join(full_watermarks_dir, image_filename)
            if os.path.exists(watermark_destination_path):
                if os.path.isdir(watermark_destination_path):
                    logger.error(
                        "Tried to upload watermark to %s but already contains a directory! Aborting!",
                        watermark_destination_path
                    )
                    return jsonify({
                        'error': 'Bad file name.'
                    }), 501
                else:
                    # TODO(Shadowen): Maybe offer a config.yaml option for this.
                    logger.warning(
                        "Tried to upload watermark to %s but file already exists! Overwriting...",
                        watermark_destination_path
                    )
                    utility.remove(watermark_destination_path)
            logger.info(
                "Moving watermark from %s to %s.",
                watermark_temp_path,
                watermark_destination_path
            )
            utility.move(watermark_temp_path, watermark_destination_path)

            return jsonify({}), 200

    @octoprint.plugin.BlueprintPlugin.route("/rendering/watermark/delete", methods=["POST"])
    @restricted_access
    def delete_watermark(self):
        """Delete the watermark given in the HTTP POST name field."""
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            # Parse the request.
            filepath = request.get_json()['path']
            logger.debug("Deleting watermark %s.", filepath)
            if not os.path.exists(filepath):
                logger.error("Tried to delete watermark at %s but file doesn't exists!", filepath)
                return jsonify({
                    'error': 'No such file.'
                }), 501

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
                logger.error(
                    "Tried to delete watermark at %s but file doesn't exists!",
                    filepath
                )
                return jsonify({
                    'error': "Cannot delete file outside watermarks folder."
                }), 400
            utility.remove(filepath)
            return jsonify({
                'success': "Deleted {} successfully.".format(filepath)
            })

    @octoprint.plugin.BlueprintPlugin.route("/loadFailedRenderings", methods=["POST"])
    @restricted_access
    def load_failed_renderings_request(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            failed_jobs = self._rendering_processor.get_failed()
            return jsonify({
                "failed": {
                    "renderings": failed_jobs["failed"],
                    "size": failed_jobs["failed_size"],
                }
            })

    @octoprint.plugin.BlueprintPlugin.route("/loadInProcessRenderings", methods=["POST"])
    @restricted_access
    def load_in_process_renderings_request(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            in_process_jobs = self._rendering_processor.get_in_process()
            return jsonify({
                "in_process": {
                    "renderings": in_process_jobs["in_process"],
                    "size": in_process_jobs["in_process_size"],
                }
            })

    @octoprint.plugin.BlueprintPlugin.route("/deleteAllFailedRenderings", methods=["POST"])
    @restricted_access
    def delete_all_failed_renderings_request(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            failed_jobs = self._rendering_processor.get_failed()
            failed_renderings = failed_jobs["failed"]
            for failed_rendering in failed_renderings:
                self.delete_rendering_job(
                    failed_rendering["job_guid"],
                    failed_rendering["camera_guid"]
                )
            return jsonify({
                "success": True
            })

    @octoprint.plugin.BlueprintPlugin.route("/deleteFailedRendering", methods=["POST"])
    @restricted_access
    def delete_failed_rendering_request(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            job_guid = request_values["job_guid"]
            camera_guid = request_values["camera_guid"]
            self.delete_rendering_job(
                job_guid,
                camera_guid
            )
            return jsonify({
                "success": True
            })

    @octoprint.plugin.BlueprintPlugin.route("/renderAllFailedRenderings", methods=["POST"])
    @restricted_access
    def render_all_failed_renderings_request(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            render_profile_override_guid = request_values["render_profile_override_guid"]
            camera_profile_override_guid = request_values["camera_profile_override_guid"]
            rendering_profile = None
            camera_profile = None
            if (
                render_profile_override_guid and
                render_profile_override_guid in self._octolapse_settings.profiles.renderings
            ):
                rendering_profile = self._octolapse_settings.profiles.renderings[render_profile_override_guid]

            if (
                camera_profile_override_guid and
                camera_profile_override_guid in self._octolapse_settings.profiles.cameras
            ):
                camera_profile = self._octolapse_settings.profiles.cameras[camera_profile_override_guid].clone()

            failed_jobs = self._rendering_processor.get_failed()
            failed_renderings = failed_jobs["failed"]
            for failed_rendering in failed_renderings:
                self.add_rendering_job(
                    failed_rendering["job_guid"],
                    failed_rendering["camera_guid"],
                    self._octolapse_settings.main_settings.get_temporary_directory(self.get_plugin_data_folder()),
                    rendering_profile=rendering_profile,
                    camera_profile=camera_profile
                )
            return jsonify({
                "success": True
            })

    @octoprint.plugin.BlueprintPlugin.route("/renderFailedRendering", methods=["POST"])
    @restricted_access
    def render_failed_rendering_request(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            job_guid = request_values["job_guid"]
            camera_guid = request_values["camera_guid"]
            render_profile_override_guid = request_values["render_profile_override_guid"]
            camera_profile_override_guid = request_values["camera_profile_override_guid"]
            rendering_profile = None
            camera_profile = None
            if (
                render_profile_override_guid and
                render_profile_override_guid in self._octolapse_settings.profiles.renderings
            ):
                rendering_profile = self._octolapse_settings.profiles.renderings[render_profile_override_guid]

            if (
                camera_profile_override_guid and
                camera_profile_override_guid in self._octolapse_settings.profiles.cameras
            ):
                camera_profile = self._octolapse_settings.profiles.cameras[camera_profile_override_guid].clone()

            self.add_rendering_job(
                job_guid,
                camera_guid,
                self._octolapse_settings.main_settings.get_temporary_directory(self.get_plugin_data_folder()),
                rendering_profile=rendering_profile,
                camera_profile=camera_profile
            )

            return jsonify({
                "success": True
            })

    @octoprint.plugin.BlueprintPlugin.route("/addArchiveToUnfinishedRenderings", methods=["POST"])
    @restricted_access
    def add_archive_to_unfinished_renderings(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            snapshot_archive_name = utility.unquote(request_values["archive_name"])

            # make sure the extension is correct
            if not snapshot_archive_name.lower().endswith(".{0}".format(utility.snapshot_archive_extension)):
                return jsonify({
                    "success": False,
                    "error": "The selected archive is not a valid snapshot archive file."
                })

            # get the zip file path
            snapshot_archive_directory = self._octolapse_settings.main_settings.get_snapshot_archive_directory(
                self.get_plugin_data_folder()
            )
            snapshot_archive_path = os.path.join(snapshot_archive_directory, snapshot_archive_name)
            # attempt to import the zip file
            try:
                results = self._rendering_processor.import_snapshot_archive(snapshot_archive_path, prevent_archive=True)
            except Exception as e:
                logger.exception("Unable to import the snapshot archive.")
                raise e

            if not results["success"]:
                error = error_messages.get_error(results["error_keys"])
                logger.info(error["description"])
                return jsonify({
                    "success": False,
                    "errors": [error]
                })

            return jsonify({
                "success": True
            })

    @octoprint.plugin.BlueprintPlugin.route("/importSnapshots", methods=["POST"])
    @restricted_access
    def import_snapshots_request(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            # get the zip file path
            # example of getting the path.  Use the button name + path
            # settings_path = request.values['octolapse_settings_import_path_upload.path']
            snapshot_archive_path = request.values['octolapse_snapshot_upload.path']
            snapshot_archive_name = request.values['octolapse_snapshot_upload.name']
            # get the extension
            extension = utility.get_extension_from_filename(snapshot_archive_name)
            if extension not in RenderingProfile.get_archive_formats():
                return jsonify({
                    "success": False,
                    "error": "The file type is not allowed for upload."
                }), 403

            # get the archive folder
            target_folder = self._octolapse_settings.main_settings.get_snapshot_archive_directory(
                self.get_plugin_data_folder()
            )
            target_path = utility.get_collision_free_filepath(os.path.join(target_folder, snapshot_archive_name))
            utility.move(snapshot_archive_path, target_path)

            file_info = utility.get_file_info(target_path)
            file_info["type"] = utility.FILE_TYPE_SNAPSHOT_ARCHIVE
            self.send_files_changed_message(
                file_info,
                'added',
                None
            )

            return jsonify({
                "success": True
            })

    @octoprint.plugin.BlueprintPlugin.route("/getFiles", methods=["POST"])
    @restricted_access
    def get_files_request(self):
        with OctolapsePlugin.admin_permission.require(http_exception=403):
            request_values = request.get_json()
            file_type = request_values["type"]
            files = []

            if file_type == utility.FILE_TYPE_SNAPSHOT_ARCHIVE:
                def filter_archives(path, name, extension):
                    return extension in RenderingProfile.get_archive_formats()

                files = [
                    file for file in utility.walk_files(
                        self._octolapse_settings.main_settings.get_snapshot_archive_directory(
                            self.get_plugin_data_folder()
                        ),
                        filter_archives
                    )
                ]
            elif file_type == utility.FILE_TYPE_TIMELAPSE_OCTOLAPSE:
                def filter_octolapse_timelapse(path, name, extension):
                    return extension in set(self.get_timelapse_extensions())

                files = [
                    file for file in utility.walk_files(
                        self._octolapse_settings.main_settings.get_timelapse_directory(
                            self.get_octoprint_timelapse_location()
                        ),
                        filter_octolapse_timelapse
                    )
                ]
            elif file_type == utility.FILE_TYPE_TIMELAPSE_OCTOPRINT:
                def filter_octoprint_timelapse(path, name, extension):
                    return extension in set(self.get_timelapse_extensions())
                files = [
                    file for file in utility.walk_files(
                        self.get_octoprint_timelapse_location()
                    )
                ]

            return jsonify({
                "files": files
            })

    def apply_camera_settings(self, camera_profiles, retries=3, backoff_factor=0.3, no_wait=False):

        if camera_profiles is None:
            camera_profiles = self._octolapse_settings.profiles.active_cameras()

        success, errors = camera.CameraControl.apply_camera_settings(
            camera_profiles, retries=retries, backoff_factor=backoff_factor, no_wait=no_wait
        )
        if not success and not no_wait:
            logger.error(errors)
            return False, errors
        else:
            return True, None

    @staticmethod
    def get_default_settings_filename():
        return "settings_default_current.json"

    def get_default_settings_folder(self):
        return os.path.join(self._basefolder, 'data')

    def get_settings_file_path(self):
        return os.path.join(self.get_plugin_data_folder(), "settings.json")

    def get_log_file_path(self):
        return self._settings.get_plugin_logfile_path()

    def configure_loggers(self):
        logging_configurator.configure_loggers(
            self.get_log_file_path(), self._octolapse_settings.profiles.current_logging_profile()
        )

    def load_settings(self, force_defaults=False):

        if force_defaults:
            settings_file_path = None
        else:
            settings_file_path = self.get_settings_file_path()
        # wait for any pending update checks to finish
        with self.automatic_update_lock:
            # create new settings from default setting file
            new_settings, defaults_loaded = OctolapseSettings.load(
                settings_file_path,
                self._plugin_version,
                __git_version__,
                self.get_default_settings_folder(),
                self.get_default_settings_filename(),
                self.get_plugin_data_folder(),
                available_profiles=self.available_profiles
            )
        self._octolapse_settings = new_settings
        self.configure_loggers()

        # Extract any settings from octoprint that would be useful to our users.
        self.copy_octoprint_default_settings(
            apply_to_current_profile=defaults_loaded)

        self.save_settings()

        return self._octolapse_settings.to_dict()

    def copy_octoprint_default_settings(self, apply_to_current_profile=False):
        try:
            # move some octoprint defaults if they exist for the webcam
            # specifically the address, the bitrate and the ffmpeg directory.
            # Attempt to get the camera address and snapshot template from Octoprint settings
            snapshot_url = self._settings.global_get(["webcam", "snapshot"])
            webcam_stream_url = self._settings.global_get(["webcam", "stream"])
            # we are doing some templating so we have to try to separate the
            # camera base address from the querystring.  This will probably not work
            # for all cameras.
            try:
                # adjust the snapshot url
                if snapshot_url:
                    o = urlparse(snapshot_url)
                    camera_address = o.scheme + "://" + o.netloc + o.path
                    logger.info("Setting octolapse camera address to %s.", camera_address)
                    snapshot_action = urlparse(snapshot_url).query
                    snapshot_request_template = "{camera_address}?" + snapshot_action
                    logger.info("Setting octolapse camera snapshot template to %s.",
                                snapshot_request_template.replace('{', '{{').replace('}', '}}'))  # but why???
                    self._octolapse_settings.profiles.defaults.camera.webcam_settings.address = camera_address
                    self._octolapse_settings.profiles.defaults.camera.webcam_settings.snapshot_request_template = snapshot_request_template
                    if apply_to_current_profile:
                        logger.info("Applying the default snapshot url to the Octolapse camera profiles.")
                        for profile in self._octolapse_settings.profiles.cameras.values():
                            profile.webcam_settings.address = camera_address
                            profile.webcam_settings.snapshot_request_template = snapshot_request_template
                else:
                    logger.warning("No snapshot url was set in the Octoprint settings, unable to apply defaults.")
                # adjust the webcam stream url
                webcam_stream_template = webcam_stream_url
                if webcam_stream_template:
                    logger.info("Setting octolapse defalt streaming url to %s.", webcam_stream_url)
                    self._octolapse_settings.profiles.defaults.camera.webcam_settings.stream_template = webcam_stream_template
                    if apply_to_current_profile:
                        logger.info("Applying the default streaming url to the Octolapse camera profiles.")
                        for profile in self._octolapse_settings.profiles.cameras.values():
                            profile.webcam_settings.stream_template = webcam_stream_template
                else:
                    logger.warning("No streaming url was set in the Octoprint settings, unable to apply defaults.")

            except Exception as e:
                # cannot send a popup yet,because no clients will be connected.  We should write a routine that
                # checks to make sure Octolapse is correctly configured if it is enabled and send some kind of
                # message on client connect. self.SendPopupMessage("Octolapse was unable to extract the default
                # camera address from Octoprint.  Please configure your camera address and snapshot template before
                # using Octolapse.")
                logger.exception("Unable to copy the default webcam settings from OctoPrint.")

            bitrate = self._settings.global_get(["webcam", "bitrate"])
            if bitrate:
                self._octolapse_settings.profiles.defaults.rendering.bitrate = bitrate
                logger.info("Setting the default octolapse rendering bitrate to the Octoprint default of %s.", bitrate)
                if apply_to_current_profile and bitrate:
                    logger.info("Applying default bitrate to the Octolapse rendering profiles.")
                    for profile in self._octolapse_settings.profiles.renderings.values():
                        profile.bitrate = bitrate
            else:
                logger.warning("No rendering bitrate was set in the Octoprint settings.  Unable to apply the defaults.")
        except Exception as e:
            logger.exception("Unable to copy default settings from OctoPrint.")

    def save_settings(self):
        # Save setting from file
        try:
            # set the git-version
            self._octolapse_settings.main_settings.git_version = __git_version__
            self._octolapse_settings.save(self.get_settings_file_path())
            self.configure_loggers()
        except Exception as e:
            logger.exception("Failed to save settings.")
            raise e
        return None

    # def on_settings_initialized(self):
    def get_current_printer_profile(self):
        """Get the plugin's current printer profile"""
        return self._printer_profile_manager.get_current()

    def queue_plugin_message(self, plugin_message):
        self._plugin_message_queue.put(plugin_message)

    # EVENTS
    #########
    def get_settings_defaults(self):
        return dict(version=self._plugin_version, load=None, restore_default_settings=None)

    def get_settings_version(self):
        # This needs to be incremented for each file migration.  What a pain.  Currently set for V0.4.0rc1
        return 3

    def on_settings_migrate(self, target, current):
        # If we don't have a current version, look at the current settings file for the most recent version.
        if current is None:
            current_version = 'unknown'
            if os.path.isfile(self.get_settings_file_path()):
                current_version = OctolapseSettings.get_plugin_version_from_file(
                    self.get_settings_file_path()
                )
            if current_version == 'unknown':
                current_version = None
        else:
            current_version = get_version_from_settings_index(current)

        has_migrated = migrate_files(current_version, self._plugin_version, self.get_plugin_data_folder())
        if has_migrated:
            logger.info("Octolapse has migrated files from version index %d to %s", current, self._plugin_version)

    def get_status_dict(self, include_profiles=False):
        try:
            is_timelapse_active = False
            snapshot_count = 0
            snapshot_failed_count = 0
            is_taking_snapshot = False
            is_rendering = False
            current_timelapse_state = TimelapseState.Idle
            is_waiting_to_render = False
            profiles_dict = None
            is_test_mode_active = False
            unfinished_renderings = None
            in_process_renderings = None
            if self._timelapse is not None:
                snapshot_count, snapshot_failed_count = self._timelapse.get_snapshot_count()
                is_timelapse_active = self._timelapse.is_timelapse_active()
                if is_timelapse_active:
                    is_test_mode_active = self._timelapse.get_is_test_mode_active()
                # Always get the current logging settings, else they won't update from the tab while a timelapse is
                # running.
                if include_profiles:
                    if is_timelapse_active:
                        profiles_dict = self._timelapse.get_current_settings().profiles.get_profiles_dict()
                    else:
                        profiles_dict = self._octolapse_settings.profiles.get_profiles_dict()
                    profiles_dict["current_logging_profile_guid"] = (
                        self._octolapse_settings.profiles.current_logging_profile_guid
                    )
                    profiles_dict["logging_profiles"] = profiles_dict["logging"]
                    # always get the latest current camera profile guid.
                    profiles_dict["current_camera_profile_guid"] = (
                        self._octolapse_settings.profiles.current_camera_profile_guid
                    )
                is_rendering = False
                if self._rendering_processor:
                    is_rendering = self._rendering_processor.is_processing()
                current_timelapse_state = self._timelapse.get_current_state()
                is_taking_snapshot = TimelapseState.TakingSnapshot == current_timelapse_state

                is_waiting_to_render = (not is_rendering) and current_timelapse_state == TimelapseState.WaitingToRender
            return {
                'snapshot_count': snapshot_count,
                'snapshot_failed_count': snapshot_failed_count,
                'is_timelapse_active': is_timelapse_active,
                'is_taking_snapshot': is_taking_snapshot,
                'is_rendering': is_rendering,
                'is_test_mode_active': is_test_mode_active,
                'waiting_to_render': is_waiting_to_render,
                'state': current_timelapse_state,
                'profiles': profiles_dict,
                'unfinished_renderings': unfinished_renderings,
                'in_process_renderings': in_process_renderings
            }
        except Exception as e:
            logger.exception("Failed to create status dict.")
            raise e

    def get_template_configs(self):
        logger.info("Octolapse - is loading template configurations.")
        return [dict(type="settings", custom_bindings=True)]

    def create_timelapse_object(self):
        self._timelapse = Timelapse(
            self.get_current_octolapse_settings,
            self._printer,
            self.get_plugin_data_folder(),
            self.get_default_settings_folder(),
            self._settings,
            on_print_started=self.on_print_start,
            on_print_start_failed=self.on_print_start_failed,
            on_snapshot_start=self.on_snapshot_start,
            on_snapshot_end=self.on_snapshot_end,
            on_new_thumbnail_available=self.on_new_thumbnail_available,
            on_post_processing_error_callback=self.on_post_processing_error_callback,
            on_timelapse_stopping=self.on_timelapse_stopping,
            on_timelapse_stopped=self.on_timelapse_stopped,
            on_timelapse_end=self.on_timelapse_end,
            on_state_changed=self.on_timelapse_state_changed,
            on_snapshot_position_error=self.on_snapshot_position_error,
            on_rendering_start=self.add_rendering_job
        )

    def get_available_server_profiles_path(self):
        return os.path.join(self.get_plugin_data_folder(), "server_profiles.json".format())

    def _update_available_server_profiles(self):
        # load all available profiles from the server
        have_profiles_changed = False

        available_profiles = ExternalSettings.get_available_profiles(
            self._plugin_version, self.get_available_server_profiles_path()
        )
        if available_profiles:
            have_profiles_changed = self.available_profiles != available_profiles
            self.available_profiles = available_profiles
            # update the profile options within the octolapse settings
            self._octolapse_settings.profiles.options.update_server_options(available_profiles)

        return have_profiles_changed

    def start_automatic_updates(self):
           # create a function to do all of the updates
            def _update():
                if not self._octolapse_settings.main_settings.automatic_updates_enabled:
                    return
                logger.info("Checking for profile updates.")
                self.check_for_updates(notify=True)

            update_interval = 60 * 60 * 24 * self._octolapse_settings.main_settings.automatic_update_interval_days

            with self.automatic_update_lock:
                if self.automatic_update_thread is not None:
                    self.automatic_update_cancel.set()
                    self.automatic_update_cancel.clear()
                    self.automatic_update_thread.join()

                self.automatic_update_thread = utility.RecurringTimerThread(
                    update_interval, _update, self.automatic_update_cancel
                )
                self.automatic_update_thread.daemon = True

            # load available server profiles before starting the automatic server profile update
            self.load_available_server_profiles()
            self.automatic_update_thread.start()

    def load_available_server_profiles(self):
        with self.automatic_update_lock:
            if self._update_available_server_profiles():
                # notify the clients of the makes and models changes
                data = {
                    'type': 'external_profiles_list_changed',
                    'server_profiles': self.available_profiles
                }
                self._plugin_manager.send_plugin_message(self._identifier, data)
            if not self.available_profiles:
                logger.warning("No server profiles are available.")
                return

    # create function to update all existing automatic profiles
    def check_for_updates(self, force_updates=False, notify=False, ignore_suppression=False):
        self.load_available_server_profiles()
        with self.automatic_update_lock:
            if not self.available_profiles:
                logger.warning("Can't check for profile updates when no server profiles are available.")
                return

            profiles_to_update = ExternalSettings.check_for_updates(
                self.available_profiles,
                self._octolapse_settings.profiles.get_updatable_profiles_dict(),
                force_updates,
                ignore_suppression
            )
            if profiles_to_update:
                if notify:
                    num_available = 0
                    # remove python 2 support
                    # for key, profile_type in six.iteritems(profiles_to_update):
                    for key, profile_type in profiles_to_update.items():
                        num_available += len(profile_type)
                    data = {
                        "type": "updated-profiles-available",
                        "available_profile_count": num_available
                    }
                    self._plugin_manager.send_plugin_message(self._identifier, data)
                logger.info("Profile updates are available.")
            else:
                logger.info("No profile updates are available.")

            return profiles_to_update

    def notify_updates(self):
        if not self._octolapse_settings.main_settings.automatic_updates_enabled:
            return

        if self.automatic_updates_available:
            logger.info("Profile updates are available from the server.")
            # create an automatic updates available message

    def on_startup(self, host, port):
        try:
            # tell the logging configuator what our logfile path is
            logger.info("Configuring file logger.")
            logging_configurator.configure_loggers(log_file_path=self.get_log_file_path())
            logger.info("Started logging to file.")

            # load settings
            self.load_settings()

            # configure our loggers
            self.configure_loggers()

            # create our timelapse object
            self.create_timelapse_object()

            # create our message worker
            self._message_worker = MessengerWorker(
                self._plugin_message_queue, self._plugin_manager, self._identifier, update_period_seconds=1
            )

            # start the message worker
            self._message_worker.start()

            # apply camera settings if necessary
            startup_cameras = self._octolapse_settings.profiles.after_startup_cameras()

            # note that errors here will ONLY show up in the log.
            if len(startup_cameras) > 0:
                self.apply_camera_settings(camera_profiles=startup_cameras, retries=9, backoff_factor=0.1, no_wait=True)

            # start automatic updates
            self.start_automatic_updates()

            # start the rendering processor
            self._rendering_processor = RenderingProcessor(
                self._rendering_task_queue,
                self._data_folder,
                self._octolapse_settings.main_settings.version,
                __git_version__,
                self.get_default_settings_folder(),
                self._settings,
                self.get_current_octolapse_settings,
                self.on_render_start,
                self.on_render_success,
                self.on_render_progress,
                self.on_render_error,
                self.on_render_end,
                self.send_failed_renderings_changed_message,
                self.send_in_process_renderings_changed_message,
                self.send_unfinished_renderings_loaded_message
            )
            self._rendering_processor.daemon = True
            self._rendering_processor.start()

            # log the loaded state
            logger.info("Octolapse - loaded and active.")
        except Exception as e:
            logger.exception("An unexpected error occurred on startup.")
            raise e

    def on_shutdown(self):
        logger.info("Octolapse is shutting down.")

    # Event Mixin Handler
    def on_event(self, event, payload):
        try:
            # If we haven't loaded our settings yet, return.
            if self._octolapse_settings is None or self._timelapse is None or self._timelapse.get_current_state() == TimelapseState.Idle:
                return
            if event == Events.PRINTER_STATE_CHANGED:
                self.send_state_changed_message({"status": self.get_status_dict()})
            elif event == Events.CONNECTIVITY_CHANGED:
                self.send_state_changed_message({"status": self.get_status_dict()})
            elif event == Events.CLIENT_OPENED:
                self.send_state_changed_message({"status": self.get_status_dict()})
            elif event == Events.DISCONNECTING:
                self.on_printer_disconnecting()
            elif event == Events.DISCONNECTED:
                self.on_printer_disconnected()
            elif event == Events.PRINT_PAUSED:
                self.on_print_paused()
            elif event == Events.HOME:
                logger.info("homing to payload: %s.", payload)
            elif event == Events.PRINT_RESUMED:
                logger.info("Print Resumed.")
                self.on_print_resumed()
            elif event == Events.PRINT_FAILED:
                self.on_print_failed()
                self.on_print_end()
            elif event == Events.PRINT_CANCELLING:
                self.on_print_cancelling()
            elif event == Events.PRINT_CANCELLED:
                self.on_print_canceled()
            elif event == Events.PRINT_DONE:
                self.on_print_completed()
                self.on_print_end()
            elif event == Events.SETTINGS_UPDATED:
                # See if the ffmpeg directory changed.
                ffmpeg_directory = self._settings.global_get(["webcam", "ffmpeg"])
                if self._rendering_processor.set_ffmpeg_directory(ffmpeg_directory):
                    logger.info("FFMPEG directory changed to %s, updating the rendering processor", ffmpeg_directory)
        except Exception as e:
            logger.exception("An error occurred while handling an OctoPrint event.")
            raise e

    def on_print_resumed(self):
        self._timelapse.on_print_resumed()

    def on_print_paused(self):
        self._timelapse.on_print_paused()

    def on_print_start(self, parsed_command):
        logger.info(
            "Print start detected, attempting to start timelapse."
        )
        # check for problems starting the timelapse
        try:
            results = self.test_timelapse_config()
            if not results["success"]:
                self.on_print_start_failed(results["error"], parsed_command=parsed_command)
                return

            # get all of the settings we need
            timelapse_settings = self.get_timelapse_settings()
            if not timelapse_settings["success"]:
                errors = timelapse_settings["errors"]
                if len(errors) == 0:
                    errors = timelapse_settings["warnings"]
                self.on_print_start_failed(errors, parsed_command=parsed_command)
                return

            if len(timelapse_settings["warnings"]) > 0:
                self.send_plugin_errors("warning", timelapse_settings["warnings"], parsed_command=parsed_command)

            settings_clone = timelapse_settings["settings"]
            current_trigger_clone = settings_clone.profiles.current_trigger()
            if current_trigger_clone.trigger_type in TriggerProfile.get_precalculated_trigger_types():
                # pre-process the stabilization
                # this is done in another process, so we'll have to exit and wait for the results
                self.pre_process_stabilization(
                    timelapse_settings, parsed_command
                )
                # exit and allow the timelapse pre-processing routine to complete.
            elif self.start_timelapse(timelapse_settings):
                self._timelapse.release_job_on_hold_lock(parsed_command=parsed_command)

        except Exception as e:
            error = error_messages.get_error(["init", "timelapse_start_exception"])
            logger.exception("Unable to start the timelapse.")
            self.on_print_start_failed([error], parsed_command=parsed_command)

    def test_timelapse_config(self):
        logger.debug("Testing timelapse configuration.")

        logger.verbose("Verify that Octolapse is enabled.")
        if not self._octolapse_settings.main_settings.is_octolapse_enabled:
            logger.error("Octolapse is not enabled.  Cannot start timelapse.")
            error = error_messages.get_error(["init","octolapse_is_disabled"])
            logger.error(error["description"])
            return {"success": False, "error": error}

        logger.verbose("Ensure that we have at least one printer profile.")
        # make sure that at least one profile is available
        if len(self._octolapse_settings.profiles.printers) == 0:
            logger.error("No printer profiles exist.  Cannot start timelapse.")
            error = error_messages.get_error(["init", "no_printer_profile_exists"])
            return {"success": False, "error": error}

        # make sure we have an active printer (a selected profile)
        logger.verbose("Ensure one printer profile is active and selected.")
        if self._octolapse_settings.profiles.current_printer() is None:
            logger.error("There is no currently selected printer profile.  Cannot start timelapse.")
            error = error_messages.get_error(["init", "no_printer_profile_selected"])
            logger.error(error["description"])
            return {"success": False, "error": error}

        # see if the printer profile has been configured
        logger.verbose("Ensure the current printer profile has been configured or that the configuration is automatic.")
        if (
            not self._octolapse_settings.profiles.current_printer().has_been_saved_by_user and
            not self._octolapse_settings.profiles.current_printer().slicer_type == "automatic"
        ):
            logger.error("The selected printer profile is not configured, or the slicer type is not automatic.  Cannot start timelapse.")
            error = error_messages.get_error(["init", "printer_not_configured"])
            logger.error(error["description"])
            return {"success": False, "error": error}

        # determine the file source
        logger.verbose("Ensure data exists about the current job.")
        printer_data = self._printer.get_current_data()
        current_job = printer_data.get("job", None)
        if not current_job:
            logger.error("Data about the current job could not be found.  Cannot start timelapse.")
            error = error_messages.get_error(["init", "no_current_job_data_found"])
            log_message = "Failed to get current job data on_print_start:" \
                          "  Current printer data: {0}".format(printer_data)
            logger.error(log_message)
            return {"success": False, "error": error}

        logger.verbose("Ensure current job has an associated file.")
        current_file = current_job.get("file", None)
        if not current_file:
            logger.error("The current job has no associated file.  Cannot start timelapse.")
            error = error_messages.get_error(["init", "no_current_job_file_data_found"])
            log_message = "Failed to get current file data on_print_start:" \
                          "  Current job data: {0}".format(current_job)
            logger.error(log_message)
            # ERROR_REPLACEMENT
            return {"success": False, "error": error}

        logger.verbose("Ensure origin information is available for the current job.")
        current_origin = current_file.get("origin", "unknown")
        if not current_origin:
            logger.error("File origin information does not exist within the current job info.  Cannot start timelapse.")
            error = error_messages.get_error(["init", "unknown_file_origin"])
            log_message = "Failed to get current origin data on_print_start:" \
                "Current file data: {0}".format(current_file)
            # ERROR_REPLACEMENT
            logger.error(log_message)
            return {"success": False, "error": error}

        logger.verbose("Ensure the file is being printed locally (not from SD).")
        if current_origin != "local":
            logger.error("Octolapse does not support printing from SD.  Cannot start timelapse.")
            error = error_messages.get_error(["init", "cant_print_from_sd"])
            log_message = "Unable to start Octolapse when printing from {0}.".format(current_origin)
            logger.error(log_message)
            # ERROR_REPLACEMENT
            return {"success": False, "error": error}

        logger.verbose("Ensure that Octolapse is in the correct state (Initializing).")
        if self._timelapse.get_current_state() != TimelapseState.Initializing:
            logger.error("Octolapse is not in the correct state.  Cannot start timelapse.")
            error = error_messages.get_error(["init", "incorrect_printer_state"])
            log_message = "Octolapse was in the wrong state at print start.  StateId: {0}".format(
                self._timelapse.get_current_state())
            logger.error(log_message)
            # ERROR_REPLACEMENT
            return {"success": False, "error": error}

        # test all cameras and look for at least one enabled camera
        logger.verbose("Testing all enabled cameras.")
        found_camera = False
        for current_camera in self._octolapse_settings.profiles.active_cameras():
            if current_camera.enabled:
                found_camera = True
                if current_camera.camera_type == "webcam":
                    # test the camera and see if it works.
                    success, camera_test_errors = camera.CameraControl.test_web_camera(
                        current_camera, is_before_print_test=True)
                    if not success:
                        error = error_messages.get_error(["init", "camera_init_test_failed"], error=camera_test_errors)
                        return {"success": False, "error": error}

        if not found_camera:
            logger.error("No enabled cameras could be found, please enable at least one camera profile and ensure it passes tests.")
            error = error_messages.get_error(["init", "no_enabled_cameras"])
            return {"success": False, "error": error}

        logger.verbose("Attempting to apply any existing custom camera preferences, if any are set.")
        success, camera_settings_apply_errors = camera.CameraControl.apply_camera_settings(
            self._octolapse_settings.profiles.before_print_start_webcameras()
        )
        if not success:
            logger.error("Unable to apply custom camera preferences, failed to start timelapse.")
            error = error_messages.get_error(
                ["init", "camera_settings_apply_failed"],
                error=camera_settings_apply_errors)
            return {"success": False, "error": error}

        # run before print start camera scripts
        logger.verbose("Running 'before print' camera scripts, if any exist.")
        success, before_print_start_camera_script_errors = camera.CameraControl.run_on_print_start_script(
            self._octolapse_settings.profiles.cameras
        )
        if not success:
            logger.error("Errors were encountered running 'before print' camera scripts.  Failed to start timelapse.")
            error = error_messages.get_error(
                ["init", "before_print_start_camera_script_apply_failed"],
                error=before_print_start_camera_script_errors)
            return {"success": False, "error": error}

        # check for version 1.3.8 min
        logger.verbose("Ensure we are running at least OctoPrint version 1.3.8.")
        if not (LooseVersion(octoprint.server.VERSION) > LooseVersion("1.3.8")):
            logger.error("The current octoprint version is older than V1.3.8, and is not supported.  Failed to start "
                         "timelapse.")
            error = error_messages.get_error(
                ["init", "incorrect_octoprint_version"], installed_version=octoprint.server.DISPLAY_VERSION
            )
            return {"success": False, "error": error}

        # Check the rendering filename template
        logger.verbose("Validating the rendering file template.")
        if not render.is_rendering_template_valid(
            self._octolapse_settings.profiles.current_rendering().output_template,
            self._octolapse_settings.profiles.options.rendering['rendering_file_templates'],
        ):
            logger.error("The rendering file template is invalid.  Cannot start timelapse.")
            error = error_messages.get_error(["init", "rendering_file_template_invalid"])
            return {"success": False, "error": error}

        # test the main settings directories
        logger.verbose("Verify that the folder structure is valid.")
        success, errors = self._octolapse_settings.main_settings.test_directories(
            self.get_plugin_data_folder(),
            self.get_octoprint_timelapse_location()
        )
        if not success:
            logger.error("The Octolapse folder structure is invalid.  Cannot start timelapse.")
            error_folders = ",".join([x["name"] for x in errors])
            error = error_messages.get_error(["init", "directory_test_failed"], failed_directories=error_folders)
            return {"success": False, "error": error}

        # test rendering overlay font path
        logger.verbose("Verify the overlay font path is correct, if rendering overlays are being used.")
        current_rendering_profile = self._octolapse_settings.profiles.current_rendering()
        if (
            current_rendering_profile.overlay_text_template and
            not os.path.isfile(current_rendering_profile.overlay_font_path)
        ):
            logger.error("The rendering overlay template font path is invalid.  Cannot start timelapse.")
            error = error_messages.get_error(
                ["init", "overlay_font_path_not_found"],
                overlay_font_path=current_rendering_profile.overlay_font_path)
            return {"success": False, "error": error}
        logger.debug("Timelapse configuration is valid!")
        return {"success": True}

    def get_octoprint_timelapse_location(self):
        return self._settings.settings.getBaseFolder("timelapse")

    def get_octoprint_g90_influences_extruder(self):
        return self._settings.global_get(["feature", "g90InfluencesExtruder"])

    def get_octoprint_printer_profile(self):
        return self._printer_profile_manager.get_current()

    def get_timelapse_settings(self):
        # Create a copy of the settings to send to the Timelapse object.
        # We make this copy here so that editing settings vis the GUI won't affect the
        # current timelapse.
        logger.debug("Getting timelapse settings.")
        settings_clone = self._octolapse_settings.clone()
        current_printer_clone = settings_clone.profiles.current_printer()
        return_value = {
            "success": False,
            "errors": [],
            "warnings": [],
            "settings": None,
            "overridable_printer_profile_settings": None,
            "ffmpeg_path": None,
            "gcode_file_path": None,
            "error_code": None,
            "error_message": None,
            "help_link": None
        }

        path = utility.get_currently_printing_file_path(self._printer)
        if path is not None:
            gcode_file_path = self._file_manager.path_on_disk(octoprint.filemanager.FileDestinations.LOCAL, path)
        else:
            error = error_messages.get_error(["init", "no_gcode_filepath_found"])
            logger.error(error["description"])
            return_value["errors"].append(error)
            return return_value

        # check the ffmpeg path
        try:
            ffmpeg_path = self._settings.global_get(["webcam", "ffmpeg"])
            if (
                self._octolapse_settings.profiles.current_rendering().enabled and
                (ffmpeg_path == "" or ffmpeg_path is None)
            ):
                error = error_messages.get_error(["init", "ffmpeg_path_not_set"])
                logger.error(error["description"])
                return_value["errors"].append(error)
                return return_value
        except Exception as e:
            logger.exception("An exception occurred while retrieving the ffmpeg/avconv path from octoprint.")
            error = error_messages.get_error(["init", "ffmpeg_path_retrieve_exception"])
            return_value["errors"].append(error)
            return return_value

        if not os.path.isfile(ffmpeg_path):
            error = error_messages.get_error(["init", "ffmpeg_not_found_at_path"])
            logger.error(error["description"])
            return_value["errors"].append(error)
            return return_value

        if current_printer_clone.slicer_type == 'automatic':
            # extract any slicer settings if possible.  This must be done before any calls to the printer profile
            # info that includes slicer setting
            try:
                success, error_type, error_list = current_printer_clone.get_gcode_settings_from_file(gcode_file_path)
            except error_messages.OctolapseException as e:
                logger.error(str(e))
                return_value["errors"].append(e.to_dict())
                return return_value
            if success:
                # Save the profile changes
                # get the extracted slicer settings
                extracted_slicer_settings = current_printer_clone.get_current_slicer_settings()
                # Apply the extracted settings to to the live settings
                self._octolapse_settings.profiles.current_printer().get_slicer_settings_by_type(
                    current_printer_clone.slicer_type
                ).update(extracted_slicer_settings.to_dict())
                self._octolapse_settings.profiles.current_printer().has_been_saved_by_user = True
                # save the live settings
                self.save_settings()
                printer_profile = self._octolapse_settings.profiles.current_printer().clone()
                printer_profile.slicer_type = PrinterProfile.slicer_type = 'automatic'
                settings_saved = True
                updated_profile_json = printer_profile.to_json()
                self.send_slicer_settings_detected_message(settings_saved, updated_profile_json)
            else:
                if self._octolapse_settings.main_settings.cancel_print_on_startup_error:
                    if error_type == "no-settings-detected":
                        error = error_messages.get_error(["init", "automatic_slicer_no_settings_found"])
                        logger.error(error["description"])
                        return_value["errors"].append(error)
                        return return_value
                    else:
                        error = error_messages.get_error(
                            ["init", "automatic_slicer_settings_missing"], missing_settings=",".join(error_list)
                        )
                        logger.error(error["description"])
                        return_value["errors"].append(error)
                        return return_value
                else:
                    if error_type == "no-settings-detected":
                        error = error_messages.get_error(
                            ["init", "automatic_slicer_no_settings_found_continue_printing"]
                        )
                        logger.error(error["description"])
                        return_value["warnings"].append(error)
                        return return_value
                    else:
                        error = error_messages.get_error(
                            ["init", "automatic_slicer_settings_missing_continue_printing"],
                            missing_settings=",".join(error_list)
                        )
                        logger.error(error["description"])
                        return_value["warnings"].append(error)
                        return return_value
        else:
            # see if the current printer profile is missing any required settings
            # it is important to check here in case automatic slicer settings extraction
            # isn't used.
            slicer_settings = settings_clone.profiles.current_printer().get_current_slicer_settings()
            missing_settings = slicer_settings.get_missing_gcode_generation_settings(
                slicer_type=settings_clone.profiles.current_printer().slicer_type
            )
            if len(missing_settings) > 0:
                error = error_messages.get_error(
                    ["init", "manual_slicer_settings_missing"],
                    missing_settings=",".join(missing_settings)
                )
                logger.error(error["description"])
                return_value["errors"].append(error)
                return return_value

        slicer_settings_clone = settings_clone.profiles.current_printer().get_current_slicer_settings()
        current_printer_clone = settings_clone.profiles.current_printer()
        # Make sure the printer profile has the correct number of extruders defined
        if len(slicer_settings_clone.extruders) > current_printer_clone.num_extruders:
            error = error_messages.get_error(
                ["init", "too_few_extruders_defined"],
                printer_num_extruders=current_printer_clone.num_extruders,
                gcode_num_extruders=len(slicer_settings_clone.extruders)
            )
            logger.error(error["description"])
            return_value["errors"].append(error)
            return return_value

        # make sure there are enough extruder offsets
        if (
            not current_printer_clone.shared_extruder and
            current_printer_clone.num_extruders < len(current_printer_clone.extruder_offsets)
        ):
            error = error_messages.get_error(
                ["init", "too_few_extruder_offsets_defined"],
                num_extruders=current_printer_clone.num_extruders,
                num_extruder_offsets=len(current_printer_clone.extruder_offsets)
            )
            logger.error(error["description"])
            return_value["errors"].append(error)
            return return_value

        overridable_printer_profile_settings = current_printer_clone.get_overridable_profile_settings(
            self.get_octoprint_g90_influences_extruder(), self.get_octoprint_printer_profile()
        )
        return_value["success"] = True
        return_value["settings"] = settings_clone
        return_value["overridable_printer_profile_settings"] = overridable_printer_profile_settings
        return_value["ffmpeg_path"] = ffmpeg_path
        return_value["gcode_file_path"] = gcode_file_path
        logger.debug("Timelapse settings retrieved.")
        return return_value

    def start_timelapse(self, timelapse_settings, snapshot_plans=None):

        try:
            self._timelapse.start_timelapse(
                timelapse_settings["settings"],
                timelapse_settings["overridable_printer_profile_settings"],
                timelapse_settings["gcode_file_path"],
                snapshot_plans=snapshot_plans
            )
        except TimelapseStartException as e:
            logger.exception("Unable to start the timelapse.  Error Details: %s", e.message)
            self.on_print_start_failed([error_messages.get_error(['init', e.type])])
            return False
        except Exception as e:
            message = "An unexpected exception occurred while starting the timelapse.  See plugin_octolapse.log for " \
                      "details. "
            logger.exception(message)
            self.on_print_start_failed([error_messages.get_error(['init', 'unexpected_exception'])])
            return False

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

        logger.info("Print Started - Timelapse Started.")

        self.on_timelapse_start()
        return True

    def on_print_start_failed(self, errors, parsed_command=None):
        if not isinstance(errors, list):
            errors = [errors]

        cancel_print = self._octolapse_settings.main_settings.cancel_print_on_startup_error
        is_warning = not cancel_print

        if len(errors) == 1:
            error = errors[0]
            if "options" in error:
                options = error["options"]
                if "is_warning" in options:
                    is_warning = options["is_warning"]
                if "cancel_print" in options:
                    cancel_print = options["cancel_print"]

        if cancel_print:
            parsed_command = None  # don't send any commands, we've cancelled.
            self._printer.cancel_print(tags={'octolapse-startup-failed'})

        if is_warning:
            self.send_plugin_errors("print-start-warning", errors=errors)
        else:
            self.send_plugin_errors("print-start-error", errors=errors)

        # see if there is a job lock, if you find one release it, and don't wait for signals.
        self._timelapse.release_job_on_hold_lock(force=True, reset=True, parsed_command=parsed_command)

    def on_preprocessing_failed(self, errors):
        message_type = "gcode-preprocessing-failed"
        self.send_plugin_errors(message_type, errors)

    def pre_process_stabilization(
        self, timelapse_settings,  parsed_command
    ):
        logger.debug(
            "Pre-Processing trigger detected, starting pre-processing thread."
        )
        if self._stabilization_preprocessor_thread is not None:
            self._stabilization_preprocessor_thread.join()
            self._stabilization_preprocessor_thread = None

        self._stabilization_preprocessor_thread = StabilizationPreprocessingThread(
            timelapse_settings,
            self.send_pre_processing_progress_message,
            self.on_pre_processing_start,
            self.pre_preocessing_complete,
            self._preprocessing_cancel_event,
            parsed_command,
            notification_period_seconds=self.PREPROCESSING_NOTIFICATION_PERIOD_SECONDS,

        )
        self._stabilization_preprocessor_thread.daemon = True
        self._stabilization_preprocessor_thread.start()

    def pre_preocessing_complete(self, success, is_cancelled, snapshot_plans, seconds_elapsed,
                                 gcodes_processed, lines_processed, missed_snapshots, quality_issues,
                                 processing_issues, timelapse_settings, parsed_command):
        if not success:
            # An error occurred
            self.pre_processing_failed(processing_issues)
        else:
            if is_cancelled:
                self._timelapse.preprocessing_finished(None)
                self.pre_processing_cancelled()
            else:
                self.pre_processing_success(
                    timelapse_settings, parsed_command, snapshot_plans, seconds_elapsed,
                    gcodes_processed, lines_processed, quality_issues, missed_snapshots
                )
        # complete, exit loop

    def reset_preprocessing(self):
        if self.preprocessing_job_guid is not None:
            self._preprocessing_cancel_event.clear()
            self.preprocessing_job_guid = None
            self.saved_timelapse_settings = None
            self.saved_snapshot_plans = None
            self.saved_parsed_command = None
            self.snapshot_plan_preview_autoclose = False
            self.snapshot_plan_preview_close_time = 0
            self.saved_preprocessing_quality_issues = ""
            self.saved_missed_snapshots = 0
            self._timelapse.release_job_on_hold_lock(reset=True)

    def pre_processing_cancelled(self):
        # signal complete to the UI (will close the progress popup
        self.send_pre_processing_progress_message(
            100, 0, 0, 0, 0)
        self.preprocessing_job_guid = None

    def pre_processing_failed(self, preprocessing_issues):

        if self._printer.is_printing():
            self.on_preprocessing_failed(
                errors=preprocessing_issues
            )
        # cancel the print
        self._printer.cancel_print(tags={'preprocessing-cancelled'})
        # inform the timelapse object that preprocessing has failed
        self._timelapse.preprocessing_finished(None)
        # close the UI progress popup
        self.send_pre_processing_progress_message(
            100, 0, 0, 0, 0)
        self.preprocessing_job_guid = None

    def pre_processing_success(
        self, timelapse_settings, parsed_command, snapshot_plans, total_seconds,
        gcodes_processed, lines_processed, quality_issues, missed_snapshots
    ):
        # inform the timelapse object that preprocessing is complete and successful by sending it the first gcode
        # which was saved when pring start was detected
        self.send_pre_processing_progress_message(100, total_seconds, 0, gcodes_processed, lines_processed)
        self.saved_timelapse_settings = timelapse_settings
        self.saved_snapshot_plans = snapshot_plans
        self.saved_preprocessing_quality_issues = quality_issues
        self.saved_missed_snapshots = missed_snapshots
        self.saved_parsed_command = parsed_command
        if timelapse_settings["settings"].main_settings.preview_snapshot_plan_autoclose:
            self.snapshot_plan_preview_autoclose = True
            self.snapshot_plan_preview_close_time = (
                time.time() + timelapse_settings["settings"].main_settings.preview_snapshot_plan_seconds
            )
            # start a timer thread to automatically close the preview
            def autoclose_snapshot_preview(preprocessing_job_guid):
                while True:
                    # if we aren't autoclosing any longer, return
                    if (
                        str(self.preprocessing_job_guid) != str(preprocessing_job_guid) or
                        self.snapshot_plan_preview_close_time == 0
                    ):
                        return

                    elif time.time() > self.snapshot_plan_preview_close_time:
                        # close all of the snapshot preview popups
                        self.send_snapshot_preview_complete_message()
                        # start the print
                        self.accept_snapshot_plan_preview(self.preprocessing_job_guid)
                        return
                    time.sleep(1)
            autoclose_thread = threading.Thread(target=autoclose_snapshot_preview, args=[self.preprocessing_job_guid])
            autoclose_thread.daemon = True
            autoclose_thread.start()
        else:
            self.snapshot_plan_preview_autoclose = False
            self.snapshot_plan_preview_close_time = 0

        if timelapse_settings["settings"].main_settings.preview_snapshot_plans:
            self.send_snapshot_plan_preview()
        else:
            self.start_preprocessed_timelapse()

    def send_snapshot_plan_preview(self):
        data = {
            "type": "snapshot-plan-preview",
            "snapshot_plan_preview": self.get_snapshot_plan_preview_dict()
        }

        self._plugin_manager.send_plugin_message(self._identifier, data)

    def get_snapshot_plan_preview_dict(self):
        # set a print job guid so we know if we should cancel this print later or not
        autoclose = self.snapshot_plan_preview_autoclose
        autoclose_seconds = int(self.snapshot_plan_preview_close_time - time.time())

        if autoclose_seconds < 0:
            autoclose_seconds = 0

        snapshot_plans = []
        total_travel_distance = 0
        total_saved_travel_distance = 0
        octoprint_printer_profile = self.get_octoprint_printer_profile()
        current_printer_profile = self.saved_timelapse_settings["settings"].profiles.current_printer()
        overridable_printer_profile_settings = current_printer_profile.get_overridable_profile_settings(
            self.get_octoprint_g90_influences_extruder(),
            octoprint_printer_profile
        )
        printer_volume = overridable_printer_profile_settings["volume"]
        for plan in self.saved_snapshot_plans:
            snapshot_plans.append(plan.to_dict())
            total_travel_distance += plan.travel_distance
            total_saved_travel_distance += plan.saved_travel_distance

        data = {
        "preprocessing_job_guid": str(self.preprocessing_job_guid),
            "snapshot_plans": {
                "snapshot_plans": snapshot_plans,
                "printer_volume": printer_volume,
                "total_travel_distance": total_travel_distance,
                "total_saved_travel_distance": total_saved_travel_distance,
                "current_plan_index": 0,
                "current_file_line": 0,
                "autoclose": autoclose,
                "autoclose_seconds": autoclose_seconds,
                "quality_issues": self.saved_preprocessing_quality_issues,
                "missed_snapshots": self.saved_missed_snapshots
            }
        }

        return data

    def accept_snapshot_plan_preview(self, preprocessing_job_guid=None):
        # use a lock
        with self.autoclose_snapshot_preview_thread_lock:
            if preprocessing_job_guid is not None and self.preprocessing_job_guid is not None:
                preprocessing_job_guid = str(self.preprocessing_job_guid)

            if (
                self.preprocessing_job_guid is None or
                preprocessing_job_guid != str(self.preprocessing_job_guid) or
                self.saved_timelapse_settings is None or
                self.saved_snapshot_plans is None or
                self.saved_parsed_command is None
            ):
                self.on_print_start_failed(error_messages.get_error(["init", "unable_to_accept_snapshot_plan"]))
                return

            logger.info("Accepting the saved snapshot plan")
            self.preprocessing_job_guid = None
            if not self.start_preprocessed_timelapse():
                # an error message will have been returned to the client, just return.
                return
            self.send_snapshot_preview_complete_message()

    def start_preprocessed_timelapse(self):
        # initialize the timelapse obeject
        self.preprocessing_job_guid = None
        if(
            self.saved_timelapse_settings is None or
            self.saved_snapshot_plans is None or
            self.saved_parsed_command is None
        ):
            logger.error("Unable to start the preprocessed timelapse, some required items could not be found.")
            self.reset_preprocessing()
            self._timelapse.release_job_on_hold_lock(reset=True)
            return
        if not self.start_timelapse(self.saved_timelapse_settings, self.saved_snapshot_plans):
            return False

        self._timelapse.preprocessing_finished(self.saved_parsed_command)
        return True

    def on_pre_processing_start(self):
        # set a print job guid so we know if we should cancel this print later or not
        self.preprocessing_job_guid = uuid.uuid4()
        data = {
            "type": "gcode-preprocessing-start",
            "preprocessing_job_guid": str(self.preprocessing_job_guid)
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_pre_processing_progress_message(
        self, percent_progress, seconds_elapsed, seconds_to_complete, gcodes_processed, lines_processed
    ):
        data = {
            "type": "gcode-preprocessing-update",
            "preprocessing_job_guid": str(self.preprocessing_job_guid),
            "percent_progress": percent_progress,
            "seconds_elapsed": seconds_elapsed,
            "seconds_to_complete": seconds_to_complete,
            "gcodes_processed": gcodes_processed,
            "lines_processed": lines_processed
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)
        # sleep for just a bit to allow the plugin message time to be sent and for cancel messages to arrive
        # the real answer for this is to figure out how to allow threading in the C++ code
        time.sleep(0.017)

    def send_popup_message(self, msg):
        self.send_plugin_message("popup", msg)

    def send_popup_error(self, msg):
        self.send_plugin_message("popup-error", msg)

    def send_state_changed_message(self, state, client_id=None):
        data = {
            "type": "state-changed",
            "state": state,
            "client_id": client_id
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_files_changed_message(self, file_info, action, client_id):
        data = {
            "type": "file-changed",
            "file": file_info,
            "action": action,
            "client_id": client_id
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_snapshot_preview_complete_message(self):
        data = {"type": "snapshot-plan-preview-complete"}
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_settings_changed_message(self, client_id):
        data = {
            "type": "settings-changed",
            "client_id": client_id
            #"status": self.get_status_dict(),
            #"main_settings": self._octolapse_settings.main_settings.to_dict()
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_slicer_settings_detected_message(self, settings_saved, printer_profile_json):
        data = {
            "type": "slicer_settings_detected",
            "saved": settings_saved,
            "printer_profile_json": printer_profile_json
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_plugin_errors(self, message_type, errors):
        self._plugin_manager.send_plugin_message(
            self._identifier, dict(type=message_type, errors=errors))

    def send_plugin_message(self, message_type, msg ):
        self._plugin_manager.send_plugin_message(
            self._identifier, dict(type=message_type, msg=msg))

    def send_directories_changed_message(self, changed_directories):
        data = {
            "type": "directories-changed",
            "directories": changed_directories
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_unfinished_renderings_loaded_message(self):
        failed_jobs = self._rendering_processor.get_failed()
        in_process = self._rendering_processor.get_in_process()
        data = {
            "type": "unfinished-renderings-loaded",
            "status": {
                "unfinished_renderings": {
                    "failed": {
                        "renderings": failed_jobs["failed"],
                        "size": failed_jobs["failed_size"],
                    },
                    "in_process": {
                        "renderings": in_process["in_process"],
                        "size": in_process["in_process_size"],
                    }
                }
            }
        }

        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_failed_renderings_changed_message(self, rendering, change_type):
        data = {
            "type": "unfinished-renderings-changed",
            "status": {
                "unfinished_renderings": {
                    "failed":
                    {
                        "rendering": rendering,
                        "change_type": change_type
                    }
                }
            }
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_in_process_renderings_changed_message(self, rendering, change_type):
        data = {
            "type": "unfinished-renderings-changed",
            "status": {
                "unfinished_renderings": {
                    "in_process":
                    {
                        "rendering": rendering,
                        "change_type": change_type
                    }
                }
            }
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_render_start_message(self, msg, job):
        status = self.get_status_dict()
        status["unfinished_renderings"] = {
            'in_process': {
                "rendering": job,
                "change_type": "changed"
            }
        }
        data = {
            "type": "render-start",
            "msg": msg,
            "status": status,
            "main_settings": self._octolapse_settings.main_settings.to_dict(),
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_post_render_failed_message(self, msg):
        data = {
            "type": "post-render-failed",
            "msg": msg,
            "status": self.get_status_dict(),
            "main_settings": self._octolapse_settings.main_settings.to_dict()
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_render_failed_message(self, msg, job):
        status = self.get_status_dict()
        status["unfinished_renderings"] = {
            'in_process': {
                "rendering": job,
                "change_type": "removed"
            }
        }

        data = {
            "type": "render-failed",
            "msg": msg,
            "status": status,
            "main_settings": self._octolapse_settings.main_settings.to_dict()
        }


        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_render_end_message(self):
        data = {
            "type": "render-end",
            "status": self.get_status_dict(),
            "main_settings": self._octolapse_settings.main_settings.to_dict()
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_render_success_message(self, message, job):
        status = self.get_status_dict()
        status["unfinished_renderings"] = {
            'in_process': {
                "rendering": job,
                "change_type": "removed"
            }
        }
        data = {
            "type": "render-complete",
            "msg": message,
            "status": status,
            "main_settings": self._octolapse_settings.main_settings.to_dict()
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def send_render_progress_message(self, progress, job):
        data = {
            "type": "render-progress",
            "status": {
                "unfinished_renderings": {
                    'in_process': {
                        "rendering": job,
                        "progress_percent": progress,
                        "change_type": "progress"
                    }
                }
            }
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def on_timelapse_start(self):
        data = {
            "type": "timelapse-start",
            "msg": "Octolapse has started a timelapse.",
            "status": self.get_status_dict(include_profiles=True),
            "main_settings": self._octolapse_settings.main_settings.to_dict(),
            "state": self._timelapse.to_state_dict(include_timelapse_start_data=True)
        }
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def on_timelapse_end(self):
        state_data = self._timelapse.to_state_dict()
        data = {
            "type": "timelapse-complete", "msg": "Octolapse has completed a timelapse.",
            "status": self.get_status_dict(include_profiles=True),
            "main_settings": self._octolapse_settings.main_settings.to_dict()
        }
        data.update(state_data)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def on_snapshot_position_error(self, message):
        state_data = self._timelapse.to_state_dict()
        data = {
            "type": "out-of-bounds", "msg": message, "status": self.get_status_dict(),
            "main_settings": self._octolapse_settings.main_settings.to_dict()
        }
        data.update(state_data)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def on_snapshot_start(self):
        data = {
            "type": "snapshot-start",
            "msg": "Octolapse is taking a snapshot.",
            "status": self.get_status_dict(),
            "main_settings": self._octolapse_settings.main_settings.to_dict(),
            "state": self._timelapse.to_state_dict(include_timelapse_start_data=False)
        }
        self.queue_plugin_message(PluginMessage(data, "snapshot-start"))

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
            "type": "snapshot-complete",
            "msg": "Octolapse has completed the current snapshot.",
            "status": status_dict,
            "state": self._timelapse.to_state_dict(),
            "main_settings": self._octolapse_settings.main_settings.to_dict(),
            'success': success,
            'error': error,
            "snapshot_success": snapshot_success,
            "snapshot_error": snapshot_error
        }
        self.queue_plugin_message(PluginMessage(data, "snapshot-complete"))

    def on_new_thumbnail_available(self, guid):
        data = {
            "guid": guid
        }
        self.queue_plugin_message(PluginMessage(data, "new-thumbnail-available"))

    def on_post_processing_error_callback(self, guid, exc):
        status_dict = self.get_status_dict()
        error = str(exc)
        data = {
            # "type": "snapshot-complete",
            "msg": error,
            "status": status_dict,
            "state": self._timelapse.to_state_dict(),
            "main_settings": self._octolapse_settings.main_settings.to_dict(),
        }
        self.queue_plugin_message(PluginMessage(data, "snapshot-post-proocessing-failed"))

    def on_print_failed(self):
        self._timelapse.on_print_failed()
        logger.info("Print failed.")

    def on_printer_disconnecting(self):
        self.reset_preprocessing()
        # stop any preprocessing scripts if they are called
        self._timelapse.release_job_on_hold_lock()
        # tell the timelapse object that we are cancelling
        self._timelapse.on_print_disconnecting()
        logger.info("Printer disconnecting.")

    def on_printer_disconnected(self):
        self._timelapse.on_print_disconnected()
        self._timelapse.release_job_on_hold_lock(reset=True)
        logger.info("Printer disconnected.")

    def on_print_cancelling(self):
        logger.info("Print cancelling.")

        self.reset_preprocessing()
        # stop any preprocessing scripts if they are called
        self._timelapse.release_job_on_hold_lock()
        # tell the timelapse object that we are cancelling
        self._timelapse.on_print_cancelling()


    def on_print_canceled(self):
        logger.info("Print cancelled.")
        self._timelapse.on_print_canceled()
        self._timelapse.release_job_on_hold_lock(reset=True)

    def on_print_completed(self):
        self._timelapse.on_print_completed()
        # run on print start scripts
        logger.info("Print completed successfullly.")

    def on_print_end(self):
        # run on print start scripts
        camera.CameraControl.run_on_print_end_script(self._octolapse_settings.profiles.cameras)
        logger.info("The print has ended.")

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
            "status": self.get_status_dict(include_profiles=True),
            "main_settings": self._octolapse_settings.main_settings.to_dict()
        }
        data.update(state_data)
        self._plugin_manager.send_plugin_message(self._identifier, data)

    # noinspection PyUnusedLocal
    def on_gcode_queuing(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        try:
            if self._timelapse is not None:
                return self._timelapse.on_gcode_queuing(cmd, cmd_type, gcode, kwargs["tags"])
        except Exception as e:
            logger.exception("on_gcode_queuing failed..")

    # noinspection PyUnusedLocal
    def on_gcode_sending(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        try:
            if self._timelapse is not None:
                self._timelapse.on_gcode_sending(cmd, kwargs["tags"])
        except Exception as e:
            logger.exception("on_gcode_sending failed.")

    # noinspection PyUnusedLocal
    def on_gcode_sent(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        try:
            if self._timelapse is not None:
                self._timelapse.on_gcode_sent(cmd, cmd_type, gcode, kwargs["tags"])
        except Exception as e:
            logger.exception("on_gcode_sent failed.")

    # noinspection PyUnusedLocal
    def on_gcode_received(self, comm, line, *args, **kwargs):
        try:
            if self._timelapse is not None:
                self._timelapse.on_gcode_received(line)
        except Exception as e:
            logger.exception("on_gcode_received failed.")
        return line

    def on_timelapse_state_changed(self, *args):
        state_change_dict = {
            "state": args[0]
        }
        self.queue_plugin_message(PluginMessage(state_change_dict, "state-changed", rate_limit_seconds=1))

    def _get_rendering_settings(self):
        return {
            "ffmpeg_path": self._settings.global_get(["webcam", "ffmpeg"]),
            "timelapse_directory": self.get_octoprint_timelapse_location(),
        }

    def _get_current_rendering_profile(self):
        return self.get_current_octolapse_settings().profiles.current_rendering().clone()

    def add_rendering_job(self, job_guid, camera_guid, temporary_folder, rendering_profile=None, camera_profile=None):
        logger.info("Adding new rendering job.  JobGuid: %s, CameraGuid: %s", job_guid, camera_guid)
        parameters = {
            "job_guid": job_guid,
            "camera_guid": camera_guid,
            "action": "add",
            "rendering_profile": rendering_profile,
            "camera_profile": camera_profile,
            "temporary_directory": temporary_folder
        }
        self._rendering_task_queue.put(parameters)

    def delete_rendering_job(self, job_guid, camera_guid):
        logger.info("Deleting unfinished rendering job.  JobGuid: %s, CameraGuid: %s", job_guid, camera_guid)
        parameters = {
            "job_guid": job_guid,
            "camera_guid": camera_guid,
            "action": "remove_unfinished",
            "delete": True
        }
        self._rendering_task_queue.put(parameters)

    def on_render_start(self, payload, job):
        """Called when a timelapse has started being rendered.  Calls any callbacks OnRenderStart callback set in the
        constructor. """
        assert (isinstance(payload, RenderingCallbackArgs))
        # Generate a notification message
        msg = "Octolapse is rendering {0} frames for the {1} camera.".format(
            payload.SnapshotCount, payload.CameraName)
        if payload.JobsRemaining > 1:
            msg += "  {0} jobs remaining. ".format(payload.JobsRemaining)

        msg += "After rendering is completed, the finished video will be available both within the stock timelapse " \
               "tab, and within the Octolapse tab. "

        self.send_render_start_message(msg, job)

    def on_render_success(self, payload, job):
        """Called after all rendering is complete."""
        assert (isinstance(payload, RenderingCallbackArgs))
        if payload.BeforeRenderError or payload.AfterRenderError:
            pre_post_render_message = "Rendering completed and was successful for the '{0}' camera, but there were " \
                                      "some script errors: ".format(payload.CameraName)
            if payload.BeforeRenderError:
                pre_post_render_message += "{0}Before Render Script - {1}".format(os.linesep, payload.BeforeRenderError.message)
            if payload.AfterRenderError:
                pre_post_render_message += "{0}After Render Script - {1}".format(os.linesep, payload.AfterRenderError.message)
            self.send_post_render_failed_message(pre_post_render_message)

        if payload.RenderingEnabled:
            # This timelapse won't be moved into the octoprint timelapse plugin folder.
            message = "Octolapse has completed rendering a timelapse for camera '{0}'.  Your video can be found by  " \
                      "clicking 'Videos and Images' within the Octolapse tab.".format(payload.CameraName)
            if payload.ArchivePath and os.path.isfile(payload.ArchivePath):
                message += "  An archive of your snapshots can be found within the 'Saved Snapshots' tab of the " \
                           "'Videos and Images' dialog."
        else:
            message = (
                "Octolapse has completed creating an archive of your snapshots for camera '{0}'.  Your archive "
                "is available within the 'Saved Snapshots' tab of the 'Videos and Images' dialog."
                .format(payload.CameraName)
            )
        self.send_render_success_message(message, job)

        output_file_name = "{0}.{1}".format(payload.RenderingFilename, payload.RenderingExtension)
        gcode_filename = "{0}.{1}".format(payload.GcodeFilename, payload.GcodeFileExtension)
        # Todo:  Make sure this path is correct
        output_file_path = payload.get_rendering_path()

        # Notify the plugin that a timelapse has been added, if it exists
        if os.path.isfile(output_file_path):
            file_info = utility.get_file_info(output_file_path)
            file_info["type"] = utility.FILE_TYPE_TIMELAPSE_OCTOLAPSE
            self.send_files_changed_message(
                file_info,
                'added',
                None
            )
            # Notify anyone who cares that Octolapse has finished rendering a movie
            self.send_movie_done_event(gcode_filename, output_file_path, output_file_name)

        archive_path = payload.ArchivePath
        # we need to make sure the archive path exists again, since some plugin might have deleted it.
        if archive_path and os.path.isfile(archive_path):
            # Notify the plugin that an archive was created
            file_info = utility.get_file_info(archive_path)
            file_info["type"] = utility.FILE_TYPE_SNAPSHOT_ARCHIVE
            self.send_files_changed_message(
                file_info,
                'added',
                None
            )
            # Notify anyone who cares that Octolapse has finished creating a snapshot archive
            self.send_snapshot_archive_done_event(gcode_filename, archive_path, os.path.basename(archive_path))

    def on_render_progress(self, payload, job):
        self.send_render_progress_message(payload, job)

    def send_movie_done_event(self, gcode_filename, movie_path, movie_basename):
        event = Events.PLUGIN_OCTOLAPSE_MOVIE_DONE
        custom_payload = dict(
            gcode=gcode_filename,
            movie=movie_path,
            movie_basename=movie_basename
        )
        self._event_bus.fire(event, payload=custom_payload)

    def send_snapshot_archive_done_event(self, gcode_filename, archive_path, archive_basename):
        event = Events.PLUGIN_OCTOLAPSE_SNAPSHOT_ARCHIVE_DONE
        custom_payload = dict(
            gcode=gcode_filename,
            archive=archive_path,
            archive_basename=archive_basename
        )
        self._event_bus.fire(event, payload=custom_payload)

    def on_render_error(self, payload, error, job):
        """Called after all rendering is complete."""
        if payload:
            assert (isinstance(payload, RenderingCallbackArgs))
            if payload.BeforeRenderError or payload.AfterRenderError:
                pre_post_render_message = "There were problems running the before/after rendering script: "
                if payload.BeforeRenderError:
                    pre_post_render_message += " The before script failed with the following error:" \
                                     "  {0}".format(payload.BeforeRenderError)
                if payload.AfterRenderError:
                    pre_post_render_message += " The after script failed with the following error:" \
                                               "  {0}".format(payload.AfterRenderError)
                self.send_render_failed_message(pre_post_render_message, job)
            if error is not None:
                message = "Rendering failed for camera '{0}'.  {1}".format(payload.CameraName, error)
                self.send_render_failed_message(message, job)
        else:
            message = "Rendering failed.  {0}".format(error)
            self.send_render_failed_message(message, job)

    def on_render_end(self):
        self.send_render_end_message()

    # ~~ AssetPlugin mixin
    def get_assets(self):
        logger.info("Octolapse is loading assets.")
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return dict(
            js=[
                "js/jquery.minicolors.min.js",
                "js/showdown.min.js",
                "js/jquery.validate.min.js",
                "js/octolapse.js",
                "js/octolapse.settings.js",
                "js/octolapse.settings.main.js",
                "js/octolapse.settings.import.js",
                "js/octolapse.profiles.js",
                "js/octolapse.profiles.printer.js",
                "js/octolapse.profiles.printer.slicer.cura.js",
                "js/octolapse.profiles.printer.slicer.other.js",
                "js/octolapse.profiles.printer.slicer.simplify_3d.js",
                "js/octolapse.profiles.printer.slicer.slic3r_pe.js",
                "js/octolapse.profiles.stabilization.js",
                "js/octolapse.profiles.trigger.js",
                "js/octolapse.profiles.rendering.js",
                "js/octolapse.profiles.camera.js",
                "js/octolapse.profiles.camera.webcam.js",
                "js/octolapse.profiles.camera.webcam.mjpg_streamer.js",
                "js/octolapse.profiles.logging.js",
                "js/octolapse.status.js",
                "js/octolapse.status.snapshotplan.js",
                "js/octolapse.status.snapshotplan_preview.js",
                "js/octolapse.help.js",
                "js/octolapse.profiles.library.js",
                "js/webcams/mjpg_streamer/raspi_cam_v2.js",
                "js/octolapse.dialog.js",
                "js/octolapse.dialog.renderings.unfinished.js",
                "js/octolapse.dialog.renderings.in_process.js",
                "js/octolapse.file_browser.js",
                "js/octolapse.helpers.js",
                "js/octolapse.dialog.timelapse_files.js"
            ],
            css=["css/jquery.minicolors.css", "css/octolapse.css"],
            less=["less/octolapse.less"]
        )

    octolapse_update_info = dict(
        displayName="Octolapse",
        # version check: github repository
        type="github_release",
        user="FormerLurker",
        repo="Octolapse",
        pip="https://github.com/FormerLurker/Octolapse/archive/{target_version}.zip",
        stable_branch=dict(branch="master", commitish=["master"], name="Stable"),
        release_compare='custom',
        prerelease_branches=[
            dict(
                branch="rc/maintenance",
                commitish=["master", "rc/maintenance"],  # maintenance RCs
                name="Maintenance RCs"
            ),
            dict(
                branch="rc/devel",
                commitish=["master", "rc/maintenance", "rc/devel"],  # devel & maintenance RCs
                name="Devel RCs"
            )
        ],
    )

    def get_release_info(self):
        # Starting with V1.5.0 prerelease branches are supported!
        if LooseVersion(octoprint.server.VERSION) < LooseVersion("1.5.0"):
            # get the checkout type from the software updater
            prerelease_channel = None
            is_prerelease = False
            # get this for reference.  Eventually I'll have to use it!
            # is the software update set to prerelease?
            if self._settings.global_get(["plugins", "softwareupdate", "checks", "octoprint", "prerelease"]):
                # If it's a prerelease, look at the channel and configure the proper branch for Arc Welder
                prerelease_channel = self._settings.global_get(
                    ["plugins", "softwareupdate", "checks", "octoprint", "prerelease_channel"]
                )
                if prerelease_channel == "rc/maintenance":
                    is_prerelease = True
                    prerelease_channel = "rc/maintenance"
                elif prerelease_channel == "rc/devel":
                    is_prerelease = True
                    prerelease_channel = "rc/devel"
            OctolapsePlugin.octolapse_update_info["prerelease"] = is_prerelease
            if prerelease_channel is not None:
                OctolapsePlugin.octolapse_update_info["prerelease_channel"] = prerelease_channel

        OctolapsePlugin.octolapse_update_info["displayVersion"] = self._plugin_version
        OctolapsePlugin.octolapse_update_info["current"] = self._plugin_version
        return dict(
            octolapse=OctolapsePlugin.octolapse_update_info
        )

    # ~~ software update hook
    def get_update_information(self):
        return self.get_release_info()

    # noinspection PyUnusedLocal
    def get_timelapse_extensions(self, *args, **kwargs):
        allowed_extensions = ["mpg", "mpeg", "mp4", "m4v", "mkv", "gif", "avi", "flv", "vob"]
        if sys.version_info < (3,0):
            return [i.encode('ascii', 'replace') for i in allowed_extensions]

        return allowed_extensions

    def bodysize_hook(self, current_max_body_sizes, *args, **kwargs):
        max_settings_upload_mb = 5
        # TODO - Add max_snapshot_upload_mb setting to config.yaml
        max_snapshot_upload_mb = 1024  # 1GB
        return [
            ("POST", "/importSettings", 1024*1024*max_settings_upload_mb),
            ("POST", "/importSnapshots", 1024*1024*max_snapshot_upload_mb)

        ]

    def register_custom_events(*args, **kwargs):
        return ["movie_done", "snapshot_archive_done"]

    def register_custom_routes(self, server_routes, *args, **kwargs):
        # version specific permission validator
        if LooseVersion(octoprint.server.VERSION) >= LooseVersion("1.4"):
            admin_validation_chain = [
                util.tornado.access_validation_factory(app, util.flask.admin_validator),
            ]
        else:
            # the concept of granular permissions does not exist in this version of Octoprint.  Fallback to the
            # admin role
            def admin_permission_validator(flask_request):
                user = util.flask.get_flask_user_from_request(flask_request)
                if user is None or not user.is_authenticated() or not user.is_admin():
                    raise tornado.web.HTTPError(403)
            permission_validator = admin_permission_validator
            admin_validation_chain = [util.tornado.access_validation_factory(app, permission_validator), ]


        return [
            (
                r"/downloadFile",
                OctolapseLargeResponseHandler,
                dict(
                    request_callback=self.download_file_request,
                    as_attachment=True,
                    access_validation=util.tornado.validation_chain(*admin_validation_chain)
                )

            ),
            (
                r"/getSnapshot",
                OctolapseLargeResponseHandler,
                dict(
                    request_callback=self.get_snapshot_request,
                    as_attachment=False
                )
            )
        ]

__plugin_name__ = "Octolapse"
__plugin_pythoncompat__ = ">=3.7,<4"

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
        "octoprint.timelapse.extensions": __plugin_implementation__.get_timelapse_extensions,
        "octoprint.server.http.bodysize": __plugin_implementation__.bodysize_hook,
        "octoprint.events.register_custom_events": __plugin_implementation__.register_custom_events,
        "octoprint.server.http.routes": __plugin_implementation__.register_custom_routes
    }


class OctolapseLargeResponseHandler(LargeResponseHandler):
    def initialize(
        self, request_callback, as_attachment=False, access_validation=None, default_filename=None,
        on_before_request=None, on_after_request=None
    ):
        super(OctolapseLargeResponseHandler, self).initialize(
            '', default_filename=default_filename, as_attachment=as_attachment, allow_client_caching=False,
            access_validation=access_validation, path_validation=None, etag_generator=None,
            name_generator=self.name_generator, mime_type_guesser=None)
        self.download_file_name = None
        self._before_request_callback = on_before_request
        self._request_callback = request_callback
        self._after_request_callback = on_after_request
        self.after_request_internal = None
        self.after_request_internal_args = None

    def name_generator(self, path):
        if self.download_file_name is not None:
            return self.download_file_name

    def prepare(self):
        if self._before_request_callback:
            self._before_request_callback()

    def get(self, include_body=True):
        if self._access_validation is not None:
            self._access_validation(self.request)

        if "cookie" in self.request.arguments:
            self.set_cookie(self.request.arguments["cookie"][0], "true", path="/")
        full_path = self._request_callback(self)
        self.root = utility.get_directory_from_full_path(full_path)

        # if the file does not exist, return a 404
        if not os.path.isfile(full_path):
            raise tornado.web.HTTPError(404)

        # return the file
        return tornado.web.StaticFileHandler.get(self, full_path, include_body=include_body)

    def on_finish(self):
            if self.after_request_internal:
                self.after_request_internal(**self.after_request_internal_args)

            if self._after_request_callback:
                self._after_request_callback()



from ._version import get_versions
__version__ = get_versions()['version']
__git_version__ = get_versions()['full-revisionid']
del get_versions
