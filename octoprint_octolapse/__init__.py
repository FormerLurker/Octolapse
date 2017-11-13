# coding=utf-8
from __future__ import absolute_import
import octoprint.plugin
import time
import os
import sys
from .settings import OctolapseSettings
from .gcode import *
from .snapshot import CaptureSnapshot,SnapshotInfo
from .position import *
from octoprint.events import eventManager, Events
from .trigger import *
import itertools

class OctolapsePlugin(	octoprint.plugin.SettingsPlugin,
						octoprint.plugin.AssetPlugin,
						octoprint.plugin.TemplatePlugin,
						octoprint.plugin.StartupPlugin,
						octoprint.plugin.EventHandlerPlugin):

	IsStarted = False
	def __init__(self):
		self.OctolapseGcode = None
		self.CaptureSnapshot = None
		self.PrintStartTime = time.time()
		self.Settings = None
		self.Triggers = []
		self.WaitingForSnapshotResponse = False;
		self.SnapshotCommandsSending = False
		self.Position = None
		self.__EndSnapshotCommand = "M114; Octolapse - EndSnapshot"
	##~~ After Startup
	def on_after_startup(self):
		self.reload_settings()
		self._logger.info("Octolapse - loaded and active.")
		IsStarted = True
		
	##~~ SettingsPlugin mixin

	def reload_settings(self):
		self.Position = Position(self.CurrentPrinterProfile())
		self.Settings = OctolapseSettings(self._settings)
		self.OctolapseGcode = GCode(self.Settings.printer, self.Settings.CurrentProfile(),self.CurrentPrinterProfile())
		self.CaptureSnapshot = CaptureSnapshot(self.Settings.CurrentProfile(), self.Settings.printer,self._logger)
		self.ClearTriggers()

		
	def on_settings_save(self, data):
		octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
		self.reload_settings()

	def get_settings_defaults(self):
		defaultSettings = settings.GetOctoprintDefaultSettings()
		self._logger.debug("Octolapse - creating default settings.")
		return defaultSettings

	def get_template_configs(self):
		self._logger.info("Octolapse - is loading template configurations.")
		return [dict(type="settings", custom_bindings=True)]

	def CurrentPrinterProfile(self):
		return self._printer_profile_manager.get_current()

	
	## EventHandlerPlugin mixin
	def on_event(self, event, payload):
		
		if event == Events.PRINT_PAUSED:
			self._logger.info("Octolapse - Print Paused")
			self.OnPrintPause()
		elif event == Events.PRINT_STARTED:
			self._logger.info("Octolapse - Print Started")
			self.OnPrintStart()
		elif event in (Events.PRINT_FAILED, Events.PRINT_CANCELLED):
			self._logger.info("Octolapse - Print Failed or Cancelled")
			self.OnPrintEnd()
		elif event == Events.PRINT_DONE:
			self._logger.info("Octolapse - Print Done")
			self.OnPrintEnd()
		#elif event == Events.PRINT_RESUMED:
		#	self._logger.info("Octolapse - Print Resumed")
		#elif event == Events.CONNECTED:
		#	self._logger.info("Octolapse - Printer Connected")

	def ClearTriggers(self):
		self.Triggers[:] = []
		self.Position.Reset()
		self.WaitingForSnapshotResponse = False;

	def OnPrintPause(self):
		if(self.Triggers is not None and len(self.Triggers)>0):
			for trigger in self.Triggers:
				if(type(trigger) == TimerTrigger):
					trigger.Pause()
	
	def OnPrintStart(self):

		self.reload_settings()
		
		self.CaptureSnapshot.SetPrintStartTime(time.time())
		self.CaptureSnapshot.SetPrintEndTime(None)
		# create the triggers for this print
		snapshot = self.Settings.CurrentProfile().snapshot
		# If the gcode trigger is enabled, add it
		if(snapshot.gcode_trigger_enabled):
			#Configure the extruder triggers
			gcodeExtruderTriggers = ExtruderTriggers(snapshot.gcode_trigger_on_extruding
											,snapshot.gcode_trigger_on_extruding_start
											,snapshot.gcode_trigger_on_primed
											,snapshot.gcode_trigger_on_retracting
											,snapshot.gcode_trigger_on_retracted
											,snapshot.gcode_trigger_on_detracting)
			#Add the trigger to the list
			self.Triggers.append(GcodeTrigger(gcodeExtruderTriggers,self.Settings.printer.snapshot_command))
		# If the layer trigger is enabled, add it
		if(snapshot.layer_trigger_enabled):
			#Configure the extruder triggers
			layerExtruderTriggers = ExtruderTriggers(snapshot.layer_trigger_on_extruding
											,snapshot.layer_trigger_on_extruding_start
											,snapshot.layer_trigger_on_primed
											,snapshot.layer_trigger_on_retracting
											,snapshot.layer_trigger_on_retracted
											,snapshot.layer_trigger_on_detracting)
			self.Triggers.append(LayerTrigger(layerExtruderTriggers,snapshot.layer_trigger_zmin, snapshot.layer_trigger_height))
		# If the layer trigger is enabled, add it
		if(snapshot.timer_trigger_enabled):
			#Configure the extruder triggers
			timerExtruderTriggers = ExtruderTriggers(snapshot.timer_trigger_on_extruding
											,snapshot.timer_trigger_on_extruding_start
											,snapshot.timer_trigger_on_primed
											,snapshot.timer_trigger_on_retracting
											,snapshot.timer_trigger_on_retracted
											,snapshot.timer_trigger_on_detracting)
			self.Triggers.append(TimerTrigger(timerExtruderTriggers,snapshot.timer_trigger_seconds))

	def OnPrintEnd(self):
		self.ClearTriggers()
		if(self.SnapshotCommandsSending):
			self.TakeSnapshot()
		self.SnapshotCommandsSending = False
		self.WaitingForSnapshotResponse = False
		self.CaptureSnapshot.SetPrintEndTime(time.time())

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
		# preconditions
		if (self.SnapshotCommandsSending == True
			or self.Settings is None
			or not self.Settings.is_octolapse_enabled
			or self.Triggers is None
			or len(self.Triggers)<1
			or self._printer is None
			or not self._printer.is_printing()):
			return

		snapshotCommands = []
		# determine if the plugin is enabled, if we have active triggere, and that we're printing
		
		#self._logger.info('Octolapse Debug - Intercepted GCode: {0:s}'.format(gcode))
		# update the position tracker so that we know where all of the axis are.
		# We will need this later when generating snapshot gcode so that we can return to the previous
		# position

		
		self.Position.Update(cmd)

		# Loop through all of the active triggers
		for trigger in self.Triggers:
			
			if(isinstance(trigger,GcodeTrigger)):
				trigger.Update(self.Position,cmd)
			elif(isinstance(trigger,TimerTrigger)):
				trigger.Update(self.Position);
			elif(isinstance(trigger,LayerTrigger)):
				trigger.Update(self.Position);

			if(trigger.IsTriggered):
				snapshotGcode = self.OctolapseGcode.GetSnapshotGcode(self.Position,trigger.Extruder)
				command_line = 1
				for command in snapshotGcode.Commands:
					## log and build in a snapshot command type
					self._logger.info('Line {0:d}: {1:s}'.format(command_line,command))
					command_line += 1
					snapshotCommands.append((command,))
				snapshotCommands.append(self.__EndSnapshotCommand,)
				comm_instance._log("Octolapse: snapshot gcode queuing at position x:{0:f} y:{1:f}".format(snapshotGcode.X,snapshotGcode.Y))
				snapshotCommands.append((cmd,cmd_type))
				cmd = snapshotCommands
				self.SnapshotCommandsSending = True
				break
		return cmd
	
	
	def GcodeSent(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		if (self.Settings is None
			or not self.Settings.is_octolapse_enabled
			or self.Triggers is None
			or len(self.Triggers)<1
			or self._printer is None
			or not self._printer.is_printing()):
			return
		if(cmd == self.__EndSnapshotCommand):
			#pause here for some MS??  We'll see..
			self.TakeSnapshot()
			self._logger.info('Octolapse - Snapshot Saved')	
			comm_instance._log("Octolapse: Snapshot Saved")
			self.SnapshotCommandsSending = False
			#self.WaitingForSnapshotResponse = True;

	def TakeSnapshot(self):
		snapshot = self.CaptureSnapshot
		if(snapshot is not None):
			try:
				snapshot.Snap(self.CurrentlyPrintingFileName())
			except:
					
				a = sys.exc_info() # Info about unknown error that caused exception.                                              
				errorMessage = "    {0}".format(a)
				b = [ str(p) for p in a ]
				errorMessage += "\n    {0}".format(b)
				self._logger.error('Unknown error detected:{0}'.format(errorMessage))
			
			self.SnapshotCommandsSending = False
		else:
			self._logger.info("Failed to retrieve the snapshot module!  It might work again later.")

	def GcodeReceived(self, comm_instance, line, *args, **kwargs):
		if (self.Settings is None
			or not self.Settings.is_octolapse_enabled
			or self.Triggers is None
			or len(self.Triggers)<1
			or self._printer is None
			or not self._printer.is_printing()):
			return line

		if(self.WaitingForSnapshotResponse==True):
			self.WaitingForSnapshotResponse = False
		return line

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

