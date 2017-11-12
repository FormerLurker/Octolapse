# coding=utf-8
from __future__ import absolute_import
import octoprint.plugin
import time
import os
import sys
from .settings import OctolapseSettings
from .gcode import *
from .snapshot import *
from octoprint.events import eventManager, Events
from .trigger import *

class OctolapsePlugin(	octoprint.plugin.SettingsPlugin,
						octoprint.plugin.AssetPlugin,
						octoprint.plugin.TemplatePlugin,
						octoprint.plugin.StartupPlugin,
						octoprint.plugin.EventHandlerPlugin):

	IsStarted = False
	def __init__(self):
		self.OctolapseGcode = None
		self.Snapshot = None
		self.PrintStartTime = time.time()
		self.Settings = None
		self.Trigger = None
	##~~ After Startup
	def on_after_startup(self):
		self.reload_settings()
		self._logger.info("Octolapse - loaded and active.")
		IsStarted = True
	##~~ SettingsPlugin mixin

	def reload_settings(self):
		self.Settings = OctolapseSettings(self._settings)
		self.OctolapseGcode = GCode(self.Settings.printer, self.Settings.CurrentProfile(),self.CurrentPrinterProfile())
		self.Snapshot = Snapshot(self.Settings.CurrentProfile(),self._logger)
		self.Triggers = None
		self.Position = None

		

	def on_settings_save(self, data):
		octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
		self.reload_settings()

	def get_settings_defaults(self):
		defaultSettings = settings.GetOctoprintDefaultSettings()
		self._logger.debug("Octolapse - creating default settings.")
		return defaultSettings

	def get_template_configs(self):
		self._logger.info("Octolapse - is loading template configurations.")
		return [dict(type="settings", custom_bindings=False)]

	def CurrentPrinterProfile(self):
		return self._printer_profile_manager.get_current()

	
	## EventHandlerPlugin mixin
	def on_event(self, event, payload):

		if event == Events.CONNECTED:
			self._logger.info("Octolapse - Printer Connected")
		elif event == Events.PRINT_PAUSED:
			if(self.Trigger is not None and type(self.Trigger) == TimerTrigger):
				self.Trigger.Pause()
		elif event == Events.PRINT_RESUMED:
			self._logger.info("Octolapse - Print Resumed")
		elif event == Events.PRINT_STARTED:
			self.Snapshot.SetPrintStartTime(time.time())
			self._logger.info("Octolapse - Print Started")
			self.Position = Position()
			# create the triggers for this print
			triggerType = self.Settings.CurrentProfile.Snapshot.TriggerType == 'gcode'
			extruderTriggers = ExtruderTriggers()
			if(triggerType == 'gcode'):
				self.Trigger = GcodeTrigger(extruderTriggers)
			elif(triggerType == 'layer'):
				self.Trigger = LayerTrigger(extruderTriggers,0.5)
			elif(triggerType == "timer"):
				self.Trigger = TimerTrigger(extruderTriggers)


		elif event in (Events.PRINT_FAILED, Events.PRINT_CANCELLED):
			self._logger.info("Octolapse - Print Failed or Cancelled")
			self.Snapshot.SetPrintEndTime(time.time())
			self.Snapshot.SetPrintStartTime(None)
			self.Position = None
			self.Trigger = None
		elif event == Events.PRINT_DONE:
			self.Snapshot.SetPrintStartTime(None)
			self.Snapshot.SetPrintEndTime(time.time())
			self._logger.info("Octolapse - Print Done")
			self.Position = None
			self.Trigger = None
					
	##~~ AssetPlugin mixin
	def get_assets(self):
		self._logger.info("Octolapse is loading assets.")
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(js = ["js/octolapse.js"],
			css = ["css/octolapse.css"],
			less = ["less/octolapse.less"],
			sh = ["scripts/snapshot.sh","scripts/snapshot.bat"])

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

	def CurrentlyPrintingFileName(self):
		if(self._printer is not None):
			current_job = self._printer.get_current_job()
			if current_job is not None and "file" in current_job:
				current_job_file = current_job["file"]
				if "path" in current_job_file and "origin" in current_job_file:
					current_file_path = current_job_file["path"]
					return current_file_path
		return ""
	
	def GcodeQueuing(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		if (self._printer is None or self.Trigger is None or not self._printer.is_printing()):
			return

		snapshotEndCode = "M292; Octolapse - EndSnapshot"
		snapshotCommands = []
		if(self._printer is not None and self._printer.is_printing()):
			snapshotTriggerType = self.Settings.CurrentProfile().snapshot.trigger_type
			self.Position.Update(gcode)
			isTriggered = False
			self.Trigger.Update(self.Settings.printer.snapshot_command,self.Position.E)
			if(self.Trigger.IsTriggered):
				snapshotGcode = self.OctolapseGcode.GetSnapshotGcode()
				command_line = 1
				for command in snapshotGcode.Commands:
					## log and build in a snapshot command type
					self._logger.info('Line {0:d}: {1:s}'.format(command_line,command))
					command_line += 1
					snapshotCommands.append((command,))
				snapshotCommands.append((snapshotEndCode,"EndSnapshot"))
				comm_instance._log("Octolapse: snapshot gcode queuing at position x:{0:f} y:{1:f}".format(snapshotGcode.X,snapshotGcode.Y))
				cmd = snapshotCommands
		return cmd
	
	printer_extruder_position = 0;

	WaitingForSnapshotResponse = False;
	def GcodeSent(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		if(cmd_type == "EndSnapshot"):
			comm_instance._log("Octolapse: snapshot gcode sent")
			self.WaitingForSnapshotResponse = True;

	def GcodeReceived(self, comm_instance, line, *args, **kwargs):
		if(self.WaitingForSnapshotResponse==True):
			self.reload_settings()
			comm_instance._log("Octolapse: Taking Snapshot")
			snapshot = self.Snapshot
			if(snapshot is not None):
				
				snapshot.Snap(self.CurrentlyPrintingFileName())
				comm_instance._log("Octolapse: Snapshot Finished")
				self._logger.info("Octolapse - Received line from printer: {0:s}.".format(line))
				self.WaitingForSnapshotResponse = False
			else:
				self._logger.error("Failed to retrieve the snapshot module!  It might work again later.")

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

