# coding=utf-8
##################################################################################
# Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
# Copyright (C) 2019  Brad Hochgesang
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
import concurrent
import logging
import octoprint_octolapse.utility as utility
import datetime as datetime
import os

class Logger(object):
    Logger = None
    FormatString = '%(asctime)s - %(levelname)s - %(message)s'
    ConsoleFormatString = '{asctime} - {levelname} - {message}'
    Logging_Executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def __init__(self, log_file_path, get_debug_function):
        self.log_file_path = log_file_path
        self.get_debug_function = get_debug_function
        if Logger.Logger is None:
            Logger.Logger = self.get_logger()

    def get_logger(self):
        _logger = logging.getLogger(
            "octoprint.plugins.octolapse")

        directory = os.path.dirname(self.log_file_path)
        import distutils.dir_util
        distutils.dir_util.mkpath(directory)
        
        if not os.path.isfile(self.log_file_path):
            open(self.log_file_path, 'w').close()

        from octoprint.logging.handlers import CleaningTimedRotatingFileHandler
        octoprint_logging_handler = CleaningTimedRotatingFileHandler(
            self.log_file_path, when="D", backupCount=3)

        octoprint_logging_handler.setFormatter(
            logging.Formatter("%(asctime)s %(message)s"))
        octoprint_logging_handler.setLevel(logging.DEBUG)
        _logger.addHandler(octoprint_logging_handler)
        _logger.propagate = False
        # we are controlling our logging via settings, so set to debug so that nothing is filtered
        _logger.setLevel(logging.DEBUG)

        return _logger

    def _has_debug_profile(self):
        return self.get_debug_function is not None
        
    def _is_enabled(self):
        if self.get_debug_function is None:
            return True
        
        return self.get_debug_function()().enabled
    
    def _log_to_console(self):
        if self.get_debug_function is None:
            return True

        return self.get_debug_function()().log_to_console
    
    def log_console(self, level_name, message, force=False):
        if self._log_to_console() or force:
            print(Logger.ConsoleFormatString.format(asctime=str(
                datetime.datetime.now()), levelname=level_name, message=message))

    def log_info(self, message):
        if self._is_enabled():
            Logger.Logging_Executor.submit(self.Logger.info, message)
            self.log_console('info', message)

    def log_warning(self, message):
        if self._is_enabled():
            Logger.Logging_Executor.submit(self.Logger.warning, message)
            self.log_console('warn', message)

    def log_exception(self, exception):
        message = utility.exception_to_string(exception)
        Logger.Logging_Executor.submit(self.Logger.error, message)
        self.log_console('error', message)

    def log_error(self, message):
        Logger.Logging_Executor.submit(self.Logger.error, message)
        self.log_console('error', message)

    def log_position_change(self, message):
        if self._has_debug_profile() or self.get_debug_function()().position_change:
            self.log_info(message)

    def log_position_command_received(self, message):
        if self._has_debug_profile() or self.get_debug_function()().position_command_received:
            self.log_info(message)

    def log_extruder_change(self, message):
        if self._has_debug_profile() or self.get_debug_function()().extruder_change:
            self.log_info(message)

    def log_extruder_triggered(self, message):
        if self._has_debug_profile() or self.get_debug_function()().extruder_triggered:
            self.log_info(message)

    def log_trigger_create(self, message):
        if self._has_debug_profile() or self.get_debug_function()().trigger_create:
            self.log_info(message)

    def log_trigger_wait_state(self, message):
        if self._has_debug_profile() or self.get_debug_function()().trigger_wait_state:
            self.log_info(message)

    def log_triggering(self, message):
        if self._has_debug_profile() or self.get_debug_function()().trigger_triggering:
            self.log_info(message)

    def log_triggering_state(self, message):
        if self._has_debug_profile() or self.get_debug_function()().trigger_triggering_state:
            self.log_info(message)

    def log_trigger_height_change(self, message):
        if self._has_debug_profile() or self.get_debug_function()().trigger_height_change:
            self.log_info(message)

    def log_position_layer_change(self, message):
        if self._has_debug_profile() or self.get_debug_function()().position_change:
            self.log_info(message)

    def log_position_height_change(self, message):
        if self._has_debug_profile() or self.get_debug_function()().position_change:
            self.log_info(message)

    def log_position_zhop(self, message):
        if self._has_debug_profile() or self.get_debug_function()().trigger_zhop:
            self.log_info(message)

    def log_timer_trigger_unpaused(self, message):
        if self._has_debug_profile() or self.get_debug_function()().trigger_time_unpaused:
            self.log_info(message)

    def log_trigger_time_remaining(self, message):
        if self._has_debug_profile() or self.get_debug_function()().trigger_time_remaining:
            self.log_info(message)

    def log_snapshot_gcode(self, message):
        if self._has_debug_profile() or self.get_debug_function()().snapshot_gcode:
            self.log_info(message)

    def log_snapshot_gcode_end_command(self, message):
        if self._has_debug_profile() or self.get_debug_function()().snapshot_gcode_endcommand:
            self.log_info(message)

    def log_snapshot_position(self, message):
        if self._has_debug_profile() or self.get_debug_function()().snapshot_position:
            self.log_info(message)

    def log_snapshot_return_position(self, message):
        if self._has_debug_profile() or self.get_debug_function()().snapshot_position_return:
            self.log_info(message)

    def log_snapshot_resume_position(self, message):
        if self._has_debug_profile() or self.get_debug_function()().snapshot_position_resume_print:
            self.log_info(message)

    def log_snapshot_save(self, message):
        if self._has_debug_profile() or self.get_debug_function()().snapshot_save:
            self.log_info(message)

    def log_snapshot_download(self, message):
        if self._has_debug_profile() or self.get_debug_function()().snapshot_download:
            self.log_info(message)

    def log_render_start(self, message):
        if self._has_debug_profile() or self.get_debug_function()().render_start:
            self.log_info(message)

    def log_render_complete(self, message):
        if self._has_debug_profile() or self.get_debug_function()().render_complete:
            self.log_info(message)

    def log_render_fail(self, message):
        if self._has_debug_profile() or self.get_debug_function()().render_fail:
            self.log_info(message)

    def log_render_sync(self, message):
        if self._has_debug_profile() or self.get_debug_function()().render_sync:
            self.log_info(message)

    def log_snapshot_clean(self, message):
        if self._has_debug_profile() or self.get_debug_function()().snapshot_clean:
            self.log_info(message)

    def log_settings_save(self, message):
        if self._has_debug_profile() or self.get_debug_function()().settings_save:
            self.log_info(message)

    def log_settings_load(self, message):
        if self._has_debug_profile() or self.get_debug_function()().settings_load:
            self.log_info(message)

    def log_print_state_change(self, message):
        if self._has_debug_profile() or self.get_debug_function()().print_state_changed:
            self.log_info(message)

    def log_camera_settings_apply(self, message):
        if self._has_debug_profile() or self.get_debug_function()().camera_settings_apply:
            self.log_info(message)

    def log_gcode_sent(self, message):
        if self._has_debug_profile() or self.get_debug_function()().gcode_sent_all:
            self.log_info(message)

    def log_gcode_queuing(self, message):
        if self._has_debug_profile() or self.get_debug_function()().gcode_queuing_all:
            self.log_info(message)

    def log_gcode_received(self, message):
        if self._has_debug_profile() or self.get_debug_function()().gcode_received_all:
            self.log_info(message)
