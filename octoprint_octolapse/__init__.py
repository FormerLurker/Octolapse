# coding=utf-8
from __future__ import absolute_import
import octoprint.plugin
import time
import os
import sys
from .settings import OctolapseSettings
from .gcode import GCode

class OctolapsePlugin(octoprint.plugin.SettingsPlugin,
                      octoprint.plugin.AssetPlugin,
                      octoprint.plugin.TemplatePlugin,
			octoprint.plugin.StartupPlugin):

	
	def __init__(self):
		self.OctolapseGcode = GCode()
	##~~ After Startup
	def on_after_startup(self):
		self._logger.info("Octolapse has been loaded and is active.")
	##~~ SettingsPlugin mixin
	def get_settings_defaults(self):
		defaultSettings = settings.GetOctoprintDefaultSettings()
		self._logger.info("Octolapse is creating default settings:")
		return defaultSettings

	def get_template_configs(self):
		self._logger.info("Octolapse is loading template configurations.")
		return [dict(type="settings", custom_bindings=False)]

	def CurrentPrinterProfile(self):
		return self._printer_profile_manager.get_current()

	def Settings(self):
		if(hasattr(self, '_settings') and self._settings is not None):
			return OctolapseSettings(self._settings)
		return OctolapseSettings(None)

	def CurrentProfile(self):
		if(hasattr(self, '_settings') and self._settings is not None):
			return OctolapseSettings(self._settings).CurrentProfile()
		return OctolapseSettings(None).CurrentProfile()

	##~~ AssetPlugin mixin

	def get_assets(self):
		self._logger.info("Octolapse is loading assets.")
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(js = ["js/octolapse.js"],
			css = ["css/octolapse.css"],
			less = ["less/octolapse.less"])

	##~~ Softwareupdate hook

	def get_update_information(self):
		# Define the configuration for your plugin to use with the Software Update
		# Plugin here.  See
		# https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
		# for details.
		self._logger.info("Octolapse is geting update information.")
		return dict(octolapse = dict(displayName="Octolapse Plugin",
				displayVersion=self._plugin_version,
				# version check: github repository
				type="github_release",
				user="FormerLurker",
				repo="Octolapse",
				current=self._plugin_version,
				# update method: pip
				pip="https://github.com/FormerLurker/Octolapse/archive/{target_version}.zip"))

	
	

	printer_is_absolute = False
	printer_max_z = 0
	printer_current_layer = 0
	sending_snapshot = False
	
	def GcodeQueuing(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		snapshotEndCode = "M292; Octolapse - EndSnapshot"
		snapshotCommands = []
		if(self._printer is not None and self._printer.is_printing()):
			snapshotTriggerType = self.CurrentProfile().snapshot.trigger_type
			if snapshotTriggerType == settings.PROFILE_SNAPSHOT_GCODE_TYPE:
				snapshotCommand = self.Settings().printer.snapshot_command
				if(cmd == snapshotCommand):
					commands = 	self.OctolapseGcode.GetSnapshotGcodeArray(self.Settings().printer, self.CurrentProfile(),self.CurrentPrinterProfile())
					self._logger.info("Octolapse has detected a snapshot gcode.  Adding following gcode:")
					command_line = 1
					for command in commands:
						## log and build in a snapshot command type
						self._logger.info('Line {0:d}: {1:s}'.format(command_line,command))
						command_line += 1
						snapshotCommands.append((command,))

					self._logger.info('Line {0:d}: {1:s}'.format(command_line,snapshotEndCode))
					snapshotCommands.append((snapshotEndCode,"EndSnapshot"))
					comm_instance._log("Octolapse: snapshot gcode queuing")
					cmd = snapshotCommands
		return cmd
	
	printer_extruder_position = 0;

	WaitingForSnapshotResponse = False;
	def GcodeSent(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		if(cmd_type == "EndSnapshot"):
			comm_instance._log("Octolapse: snapshot gcode sent")
			self._logger.info("Octolapse - All timelapse gcode sent to the printer.  Waiting for a response.")
			self.WaitingForSnapshotResponse = True;

	def GcodeReceived(self, comm_instance, line, *args, **kwargs):
		if(self.WaitingForSnapshotResponse==True):
			comm_instance._log("Octolapse: Taking Snapshot")
			time.sleep(5)
			comm_instance._log("Octolapse: Snapshot Finished")
			self._logger.info("Octolapse - Received line from printer: {0:s}.".format(line))
			self.WaitingForSnapshotResponse = False
		return line


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
		"octoprint.comm.protocol.gcode.sent": __plugin_implementation__.GcodeSent,
		"octoprint.comm.protocol.gcode.received": __plugin_implementation__.GcodeReceived
	}

