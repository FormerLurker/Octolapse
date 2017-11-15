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
from .utility import *

class OctolapsePlugin(	octoprint.plugin.SettingsPlugin,
						octoprint.plugin.AssetPlugin,
						octoprint.plugin.TemplatePlugin,
						octoprint.plugin.StartupPlugin,
						octoprint.plugin.EventHandlerPlugin):
	TIMEOUT_DELAY = 1000
	IsStarted = False
	def __init__(self):
		self.OctolapseGcode = None
		self.CaptureSnapshot = None
		self.PrintStartTime = time.time()
		self.Settings = None
		self.Triggers = []
		self.Position = None
		self.__EndSnapshotCommand = None
		self.__EndCommand = None
		self.IsPausedByOctolapse = False
		self.SnapshotGcode = None
		self.LastSnapshotRequestTime = None
		self.IsSnapshotQueued = False
		
		self.SnapshotCount = 0
		self._SavedCommand = None
		self._IsTriggering = False
		
	##~~ After Startup
	def on_after_startup(self):
		self.reload_settings()
		self._logger.info("Octolapse - loaded and active.")
		IsStarted = True
		
	##~~ SettingsPlugin mixin

	def reload_settings(self):
		self.Settings = OctolapseSettings(self._settings)
		
		
		
	def on_settings_save(self, data):
		octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
		self.reload_settings()

	def get_settings_defaults(self):
		defaultSettings = settings.GetOctoprintDefaultSettings()
		self._logger.info("Octolapse - creating default settings.")
		return defaultSettings

	def get_template_configs(self):
		self._logger.info("Octolapse - is loading template configurations.")
		return [dict(type="settings", custom_bindings=True)]

	def CurrentPrinterProfile(self):
		return self._printer_profile_manager.get_current()

	
	## EventHandlerPlugin mixin
	def on_event(self, event, payload):
		
		if event == Events.PRINT_PAUSED:
			
			if(not self.IsPausedByOctolapse):
				self._logger.info("Octolapse - Print Paused")
				self.OnPrintPause()
			else:
				self._logger.info("Octolapse - Snapshot pause complete.")
				self.SendSnapshotGcode()
		elif event == Events.PRINT_RESUMED:
			self.IsPausedByOctolapse = False
			self.__EndSnapshotCommand = None
			self.__EndCommand = None
			self.SnapshotGcode = None
			self._logger.info("Octolapse - Print Resumed")
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

	def OnPrintPause(self):
		if(self.Triggers is not None and len(self.Triggers)>0):
			for trigger in self.Triggers:
				if(type(trigger) == TimerTrigger):
					trigger.Pause()
	
	def OnPrintStart(self):

		self.reload_settings()
		self.OctolapseGcode = GCode(self.Settings.printer, self.Settings.CurrentProfile(),self.CurrentPrinterProfile(),self._logger)
		self.CaptureSnapshot = CaptureSnapshot(self.Settings.CurrentProfile(), self.Settings.printer,self._logger)
		self.ClearTriggers()
		self.Position = Position(self.CurrentPrinterProfile(),self._logger,self.Settings.printer.is_e_relative)
		self.SnapshotCount = 0
		self.CaptureSnapshot.SetPrintStartTime(time.time())
		self.CaptureSnapshot.SetPrintEndTime(None)
		self.__EndSnapshotCommand = None
		self.__EndCommand = None
		self.IsPausedByOctolapse = False
		# create the triggers for this print
		snapshot = self.Settings.CurrentProfile().snapshot
		# If the gcode trigger is enabled, add it
		if(snapshot.gcode_trigger_enabled):
			#Configure the extruder triggers
			self._logger.info("Creating Gcode Trigger - Gcode Command:{0},".format(self.Settings.printer.snapshot_command))
			self._logger.info("Extruder Triggers - On Extruding:{0}, On Extruding Start:{1}, On Primed:{2}, On Retracting:{3}, On Retracted:{4}, On Detracting:{5}"
				.format(snapshot.gcode_trigger_on_extruding
					,snapshot.gcode_trigger_on_extruding_start
					,snapshot.gcode_trigger_on_primed
					,snapshot.gcode_trigger_on_retracting
					,snapshot.gcode_trigger_on_retracted
					,snapshot.gcode_trigger_on_detracting)
			)
			gcodeExtruderTriggers = ExtruderTriggers(snapshot.gcode_trigger_on_extruding
				,snapshot.gcode_trigger_on_extruding_start
				,snapshot.gcode_trigger_on_primed
				,snapshot.gcode_trigger_on_retracting
				,snapshot.gcode_trigger_on_retracted
				,snapshot.gcode_trigger_on_detracting)
			#Add the trigger to the list
			self.Triggers.append(
				GcodeTrigger(
					gcodeExtruderTriggers,self._logger,self.Settings.printer.snapshot_command
			))
		# If the layer trigger is enabled, add it
		if(snapshot.layer_trigger_enabled):
			#Configure the extruder triggers
			self._logger.info("Creating Layer Trigger - ZMin:{0}, TriggerHeight:{1} (none = layer change), RequiresZHop:{2}".format(snapshot.layer_trigger_zmin,snapshot.layer_trigger_height, snapshot.layer_trigger_require_zhop))
			self._logger.info("Extruder Triggers - On Extruding:{0}, On Extruding Start:{1}, On Primed:{2}, On Retracting:{3}, On Retracted:{4}, On Detracting:{5}"
				.format(
					snapshot.layer_trigger_on_extruding
					,snapshot.layer_trigger_on_extruding_start
					,snapshot.layer_trigger_on_primed
					,snapshot.layer_trigger_on_retracting
					,snapshot.layer_trigger_on_retracted
					,snapshot.layer_trigger_on_detracting)
			)
			layerExtruderTriggers = ExtruderTriggers(
				snapshot.layer_trigger_on_extruding
				,snapshot.layer_trigger_on_extruding_start
				,snapshot.layer_trigger_on_primed
				,snapshot.layer_trigger_on_retracting
				,snapshot.layer_trigger_on_retracted
				,snapshot.layer_trigger_on_detracting)
			self.Triggers.append(LayerTrigger(layerExtruderTriggers,self._logger,snapshot.layer_trigger_zmin, self.Settings.printer.z_hop, snapshot.layer_trigger_require_zhop, snapshot.layer_trigger_height))
		# If the layer trigger is enabled, add it
		if(snapshot.timer_trigger_enabled):
			#Configure the extruder triggers
			self._logger.info("Creating Timer Trigger - Seconds:{0},".format(snapshot.timer_trigger_seconds))
			self._logger.info("Extruder Triggers - On Extruding:{0}, On Extruding Start:{1}, On Primed:{2}, On Retracting:{3}, On Retracted:{4}, On Detracting:{5}"
				.format(
					snapshot.timer_trigger_on_extruding
					,snapshot.timer_trigger_on_extruding_start
					,snapshot.timer_trigger_on_primed
					,snapshot.timer_trigger_on_retracting
					,snapshot.timer_trigger_on_retracted
					,snapshot.timer_trigger_on_detracting)
			)
			#Configure the extruder triggers
			timerExtruderTriggers = ExtruderTriggers(
				snapshot.timer_trigger_on_extruding
				,snapshot.timer_trigger_on_extruding_start
				,snapshot.timer_trigger_on_primed
				,snapshot.timer_trigger_on_retracting
				,snapshot.timer_trigger_on_retracted
				,snapshot.timer_trigger_on_detracting)
			self.Triggers.append(TimerTrigger(timerExtruderTriggers,self._logger,snapshot.timer_trigger_seconds))

	def OnPrintEnd(self):
		self.ClearTriggers()
		self.Position = None
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
		# update the position tracker so that we know where all of the axis are.
		# We will need this later when generating snapshot gcode so that we can return to the previous
		# position
		# 
		if(self.Position is not None):
			self.Position.Update(cmd)
		# preconditions
		if (# wait for the snapshot command to finish sending, or wait for the snapshot delay in case of timeouts)
			self.Settings is None
			or not self.Settings.is_octolapse_enabled
			or self.Triggers is None
			or len(self.Triggers)<1
			or self._printer is None
			or self.IsPausedByOctolapse
			):
			self._logger.info("GcodeQueuing - Skipping trigger checks for {0} - ".format(cmd))
			return cmd
		currentTrigger = trigger.IsTriggering(self.Triggers,self.Position, cmd)
		if(currentTrigger is not None):
			self._logger.info("GcodeQueuing - Triggering")
			#We're triggering
			self.SnapshotGcode = self.OctolapseGcode.GetSnapshotGcode(self.Position,currentTrigger.Extruder)
			# build an array of commands to take the snapshot
			if(self.SnapshotGcode is not None):
				self._logger.info("Octolapse - Pausing print to capture timelapse")
				self.SnapshotGcode.SavedCommand = cmd
				self.IsPausedByOctolapse = True
				self._printer.pause_print()
				return None
			else:
				_logger.error("Cannot take a snapshot, there are no snapshot gcode commands to execute!  Check your profile settings or re-install.")

		if( trigger.IsSnapshotCommand(cmd,self.Settings.printer.snapshot_command)):
			cmd = None
		return cmd
	
	
	def GcodeSent(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		if(self._printer.is_paused()):
			self._logger.info('GcodeSent - Examining command:{0} and comparing to the EndSnapshotCommand:{1} and EndReturnCommand:{2}'.format(cmd,self.__EndSnapshotCommand, self.__EndCommand))
		
		if(self.__EndSnapshotCommand is not None and self.__EndSnapshotCommand == cmd):
			# end snapshot command found, take the snapshot!
			
			self._logger.info('GcodeSent - Taking Snapshot')
			self.TakeSnapshot()	
			
		if(self.__EndCommand is not None and self.__EndCommand == cmd):
			self._logger.info('GcodeSent - Returned to previous position, resuming print')
			self._printer.resume_print()
	


		
	def SendSnapshotGcode(self):
		if(self.SnapshotGcode is None):
			self._logger.error("Octolapse - Cannot send snapshot Gcode, no gcode returned")
		self._logger.info("Octolapse - Moving to x:{0:f} y:{1:f} for snapshot.  Sending:".format(self.SnapshotGcode.X,self.SnapshotGcode.Y))
		self.__EndSnapshotCommand = self.SnapshotGcode.StartCommands[-1] #+ ";End-Octolapse-Snapshot-Start"
		#self.SnapshotGcode.StartCommands[-1] = self.__EndSnapshotCommand
		for str in self.SnapshotGcode.StartCommands:
			self._logger.info("    {0}".format(str))

		self._printer.commands(self.SnapshotGcode.StartCommands);

		# Start the return journey!

		
		#self.SnapshotGcode.ReturnCommands[-1] = self.__EndCommand
		self._logger.info("Octolapse - Returning to previous coordinates x:{0:f} y:{1:f}.  Sending:".format(self.SnapshotGcode.ReturnX,self.SnapshotGcode.ReturnY))
		for str in self.SnapshotGcode.ReturnCommands:
			self._logger.info("    {0}".format(str))
		self._printer.commands(self.SnapshotGcode.ReturnCommands)
		
		self._logger.info("Octolapse - Sending saved command {0}".format(self.SnapshotGcode.SavedCommand))
		self.__EndCommand = self.SnapshotGcode.SavedCommand
		self._printer.commands(self.SnapshotGcode.SavedCommand);
		
		
		
		
	def TakeSnapshot(self):
		snapshot = self.CaptureSnapshot
		self.SnapshotCount += 1
		if(snapshot is not None):
			try:
				snapshot.Snap(self.CurrentlyPrintingFileName(),self.SnapshotCount)
			except:
					
				a = sys.exc_info() # Info about unknown error that caused exception.                                              
				errorMessage = "    {0}".format(a)
				b = [ str(p) for p in a ]
				errorMessage += "\n    {0}".format(b)
				self._logger.error('Unknown error detected:{0}'.format(errorMessage))
			
		else:
			self._logger.info("Failed to retrieve the snapshot module!  It might work again later.")

	
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
		"octoprint.comm.protocol.gcode.sent": __plugin_implementation__.GcodeSent

	}

