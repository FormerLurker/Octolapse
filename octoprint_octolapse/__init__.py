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
		self.__EndSnapshotCommands = []
		self.LastSnapshotRequestTime = None
		self.IsSnapshotQueued = False
		self.IsPausedByOctolapse = False
		self.SnapshotCount = 0
	##~~ After Startup
	def on_after_startup(self):
		self.reload_settings()
		self._logger.info("Octolapse - loaded and active.")
		IsStarted = True
		
	##~~ SettingsPlugin mixin

	def reload_settings(self):
		self.Settings = OctolapseSettings(self._settings)
		self.Position = Position(self.CurrentPrinterProfile(),self._logger,self.Settings.printer.is_e_relative)
		self.OctolapseGcode = GCode(self.Settings.printer, self.Settings.CurrentProfile(),self.CurrentPrinterProfile(),self._logger)
		self.CaptureSnapshot = CaptureSnapshot(self.Settings.CurrentProfile(), self.Settings.printer,self._logger)
		self.ClearTriggers()

		
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
			self._logger.info("Octolapse - Print Paused")
			if(not self.IsPausedByOctolapse):
				self.OnPrintPause()
		elif event == Events.PRINT_RESUMED:
			self.IsPausedByOctolapse = False
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
		self.Position.Reset()

	def OnPrintPause(self):
		if(self.Triggers is not None and len(self.Triggers)>0):
			for trigger in self.Triggers:
				if(type(trigger) == TimerTrigger):
					trigger.Pause()
	
	def OnPrintStart(self):

		self.reload_settings()
		self.SnapshotCount = 0
		self.CaptureSnapshot.SetPrintStartTime(time.time())
		self.CaptureSnapshot.SetPrintEndTime(None)
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
			self._logger.info("Creating Layer Trigger - ZMin:{0}, TriggerHeight:{0} (none = layer change".format(snapshot.layer_trigger_zmin,snapshot.layer_trigger_height))
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
			self.Triggers.append(LayerTrigger(layerExtruderTriggers,self._logger,snapshot.layer_trigger_zmin, self.Settings.printer.z_hop, snapshot.layer_trigger_height))
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
		#self.TakeSnapshot()
		self.CaptureSnapshot.SetPrintEndTime(time.time())
		for trigger in self.Triggers:
			trigger.Reset()

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
		if (# wait for the snapshot command to finish sending, or wait for the snapshot delay in case of timeouts)
			self.Settings is None
			or not self.Settings.is_octolapse_enabled
			or self.Triggers is None
			or len(self.Triggers)<1
			or self._printer is None
			or not self._printer.is_printing()):
			return cmd

		snapshotCommands = []

		# update the position tracker so that we know where all of the axis are.
		# We will need this later when generating snapshot gcode so that we can return to the previous
		# position
		self.Position.Update(cmd)

		# If we have any triggers, update them and check for snapshot triggers
		if(len(self.Triggers)>0):

			# Loop through all of the active currentTriggers
			for currentTrigger in self.Triggers:
				# determine what type the current trigger is and update appropriately
				if(isinstance(currentTrigger,GcodeTrigger)):
					currentTrigger.Update(self.Position,cmd)
				elif(isinstance(currentTrigger,TimerTrigger)):
					currentTrigger.Update(self.Position)
				elif(isinstance(currentTrigger,LayerTrigger)):
					currentTrigger.Update(self.Position)
				# see if the current trigger is triggering, indicting that a snapshot should be taken
				if(currentTrigger.IsTriggered):
					# Make sure there are no position errors (unknown position, out of bounds, etc)
					if(not self.Position.HasPositionError):
						# get the gcode for the snapshot
						snapshotGcode = self.OctolapseGcode.GetSnapshotGcode(self.Position,currentTrigger.Extruder)
						# build an array of commands to take the snapshot
						if(snapshotGcode is not None and snapshotGcode.Commands is not None and len(snapshotGcode.Commands)>0):
							# create an array to hold the commands	
							snapshotCommands = []
							# loop through each command and append them to our array
							for command in snapshotGcode.Commands:
								## log and build in a snapshot command type
								#self._logger.info('Line {0:d}: {1:s}'.format(command_line,command))
								snapshotCommands.append(command)
							# If the command is NOT a snapshot command (default=snap), append it to the list of commands
							if(cmd is not None and not trigger.IsSnapshotCommand(cmd,self.Settings.printer.snapshot_command) ):
								snapshotCommands.append(cmd)
							# find the last command in the array
							lastCommandIndex = len(snapshotCommands)-1
							#set the last snapshot command
							endSnapshotCommand = snapshotCommands[lastCommandIndex] + ";ENDOCTOLAPSE"
							#replace the current final command with the new command that includes our comment to make it unique (hopefully)
							snapshotCommands[lastCommandIndex] = endSnapshotCommand
							self.__EndSnapshotCommands.append(endSnapshotCommand)
							self.SnapshotCount += 1
							comm_instance._log("Octolapse: Taking snapshot {0} at x:{1:f} y:{2:f}.".format(self.SnapshotCount,snapshotGcode.X,snapshotGcode.Y))
							self._logger.info("Octolapse: snapshot gcode queuing at position x:{0:f} y:{1:f}.  Sending snapshot commands:".format(snapshotGcode.X,snapshotGcode.Y))							
							for str in snapshotCommands:
								self._logger.info("    {0}".format(str))
							return snapshotCommands
						else:
							_logger.error("Cannot take a snapshot, there are no snapshot gcode commands to execute!  Check your profile settings or re-install.")
					else:
						_logger.error("Cannot take a snapshot, there are position tracking errors:{0}".format(self.Position.PositionError))

		if( trigger.IsSnapshotCommand(cmd,self.Settings.printer.snapshot_command)):
			cmd = None

		return cmd
	
	
	def GcodeSent(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		
		isEndSnapshotCommand = False
		
		if(is_sequence(cmd)):
			for commandString in cmd:
				if(commandString in self.__EndSnapshotCommands):
					cmdIndex = self.__EndSnapshotCommands.index(commandString)
					del(self.__EndSnapshotCommands[cmdIndex])
					isEndSnapshotCommand = True
		else:
			if(cmd in self.__EndSnapshotCommands):
					cmdIndex = self.__EndSnapshotCommands.index(cmd)
					del(self.__EndSnapshotCommands[cmdIndex])
					isEndSnapshotCommand = True

		if(isEndSnapshotCommand):
			#pause here for some MS??  We'll see..
			self.TakeSnapshot()
			self._logger.info('Snapshot Triggered')	
			comm_instance._log("Octolapse: Snapshot Triggered")
		else:
			self._logger.info('GcodeSent - Did not find the end snapshot command(s):{0} in {1}'.format(self.__EndSnapshotCommands, cmd))

	def TakeSnapshot(self):
		snapshot = self.CaptureSnapshot
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

	def GcodeReceived(self, comm_instance, line, *args, **kwargs):
		
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
		"octoprint.comm.protocol.gcode.sent": __plugin_implementation__.GcodeSent

	}

