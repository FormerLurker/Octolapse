# coding=utf-8
from __future__ import absolute_import
import octoprint.plugin
import uuid
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
from .render import Render
import shutil
from .camera import CameraControl
class OctolapsePlugin(	octoprint.plugin.SettingsPlugin,
						octoprint.plugin.AssetPlugin,
						octoprint.plugin.TemplatePlugin,
						octoprint.plugin.StartupPlugin,
						octoprint.plugin.EventHandlerPlugin):
	TIMEOUT_DELAY = 1000
	IsStarted = False
	def __init__(self):
		self.CameraControl = None
		self.Camera = None
		self.OctolapseGcode = None
		self.CaptureSnapshot = None
		self.PrintStartTime = time.time()
		self.Settings = None
		self.Triggers = []
		self.Position = None
		self.IsPausedByOctolapse = False
		self.PositionGcodes = None
		self.SnapshotGcodes = None
		self.ReturnGcode = None
		self.SavedCommand = None
		self.SnapshotCount = 0
		self._IsTriggering = False
		self.Render = None
		self.IsRendering = False
		self.HasRendered = False
		self.Responses = Responses();
		self.Commands = Commands();
		self.PositionCommandIndex = 0;
		self.SnapshotCommandIndex = 0;
		self.RequestingPosition = False
		self.WaitForPosition = False
		self.SendingSnapshotCommands = False
		self.WaitForSnapshot = False
		self.SendingSavedCommand = False
		
	def reload_settings(self):
		
		self.Settings.Update(self._settings)
		self.Settings.Save(self._settings)
		self._settings.save(True)
		
	##~~ After Startup
	def on_after_startup(self):

		self.Settings = OctolapseSettings(self._logger,self._settings)
		self._logger.info("Octolapse - loaded and active.")
		IsStarted = True

	
	def on_settings_save(self,data):
		
		
		octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
		
		return None
		#self._logger.info("Octolapse - Octoprint settings converted to octolapse settings: {0}".format(settings.GetSettingsForOctoprint(self._logger,self.Settings)))
	##~~ SettingsPlugin mixin
	
		
	def get_settings_defaults(self):
		self.Settings = OctolapseSettings(self._logger)
		defaultSettings = self.Settings.ToOctoprintSettings()
		self.Settings.debug.LogSettingsLoad("Loading default settings: {0}".format(defaultSettings))
		return defaultSettings
	def get_template_configs(self):
		self._logger.info("Octolapse - is loading template configurations.")
		return [dict(type="settings", custom_bindings=True)]
	def CurrentPrinterProfile(self):
		return self._printer_profile_manager.get_current()
	## EventHandlerPlugin mixin
	def on_event(self, event, payload):

		if(self.Settings is None or not self.Settings.is_octolapse_enabled):
			return
		if (event == Events.PRINT_PAUSED):
			if(not self.IsPausedByOctolapse):
				self.OnPrintPause()
			else:
				self.OnPrintPausedByOctolapse()
		elif (event == Events.PRINT_RESUMED):
			self.OnPrintResumed()
		elif (event == Events.PRINT_STARTED):
			self.OnPrintStart()
		elif (event == Events.PRINT_FAILED):
			self.OnPrintFailed()
		elif (event == Events.PRINT_CANCELLED):
			self.OnPrintCancelled()
		elif (event == Events.PRINT_DONE):
			self._logger.info("Octolapse - Print Done")
			self.OnPrintCompleted()
		elif (event == Events.SETTINGS_UPDATED):
			self._logger.info("Detected settings save, reloading and cleaning settings.")
			self.reload_settings()
			
	def ClearTriggers(self):
		self.Triggers[:] = []
	def OnPrintResumed(self):
		
		self.Settings.debug.LogPrintStateChange("Print Resumed.")
	def OnPrintPause(self):
		self.Settings.debug.LogPrintStateChange("Print Paused.")
		if(self.Triggers is not None and len(self.Triggers)>0):
			for trigger in self.Triggers:
				if(type(trigger) == TimerTrigger):
					trigger.Pause()
	def OnPrintPausedByOctolapse(self):
		self.Settings.debug.LogPrintStateChange("Print Paused by Octolapse.")
		
	def OnPrintStart(self):
		self.ResetSnapshotState()
		self.Settings.debug.LogPrintStateChange("Octolapse - Print Started.")
		self.CameraControl = CameraControl(self.Settings)
		self.OctolapseGcode = Gcode(self.Settings,self.CurrentPrinterProfile())
		self.CaptureSnapshot = CaptureSnapshot(self.Settings)
		if(not self.IsRendering):
			self.CaptureSnapshot.CleanSnapshots(None,'before-print')
		self.ClearTriggers()
		self.Position = Position(self.Settings,self.CurrentPrinterProfile())
		self.Render = Render(self.Settings,1,self.OnRenderStart,self.OnRenderFail,self.OnRenderComplete,None)
		self.SnapshotCount = 0
		self.CaptureSnapshot.SetPrintStartTime(time.time())
		self.CaptureSnapshot.SetPrintEndTime(None)
		self.IsPausedByOctolapse = False
		self.WaitForSnapshot = False
		self.HasRendered = False
		# create the triggers for this print
		snapshot = self.Settings.CurrentSnapshot()
		# If the gcode trigger is enabled, add it
		if(snapshot.gcode_trigger_enabled):
			#Add the trigger to the list
			self.Triggers.append(GcodeTrigger(self.Settings))
		# If the layer trigger is enabled, add it
		if(snapshot.layer_trigger_enabled):
			#Configure the extruder triggers
			
			self.Triggers.append(LayerTrigger(self.Settings))
		# If the layer trigger is enabled, add it
		if(snapshot.timer_trigger_enabled):
			#Configure the extruder triggers
			
			self.Triggers.append(TimerTrigger(self.Settings))
		if(self.Settings.CurrentCamera().apply_settings_before_print):
			self.CameraControl.ApplySettings()
	def OnPrintFailed(self):
		self.Settings.debug.LogPrintStateChange("Print Failed.")
		if(not self.IsRendering and not self.HasRendered):
			self.IsRendering = True
			self.Settings.debug.LogInfo("Started Rendering Timelapse");
			
			self.Render.Process(self.CurrentlyPrintingFileName(),  self.CaptureSnapshot.PrintStartTime, self.CaptureSnapshot.PrintEndTime);
		if(not self.IsRendering):
			self.CaptureSnapshot.CleanSnapshots(self.CurrentlyPrintingFileName(),'after-failed')
		self.OnPrintEnd()
	def OnPrintCancelled(self):
		self.Settings.debug.LogPrintStateChange("Print Cancelled.")
		if(not self.IsRendering and not self.HasRendered):
			self.IsRendering = True
			self.Settings.debug.LogInfo("Started Rendering Timelapse");
			self.Render.Process(self.CurrentlyPrintingFileName(),  self.CaptureSnapshot.PrintStartTime, self.CaptureSnapshot.PrintEndTime);
		if(not self.IsRendering):
			self.CaptureSnapshot.CleanSnapshots(self.CurrentlyPrintingFileName(),'after-cancel')
		self.OnPrintEnd()
	def OnPrintCompleted(self):
		self.CaptureSnapshot.SetPrintEndTime(time.time())
		if(not self.IsRendering and not self.HasRendered):
			self.Settings.debug.LogInfo("Started Rendering Timelapse");
			self.IsRendering = True
			self.Render.Process(self.CurrentlyPrintingFileName(),  self.CaptureSnapshot.PrintStartTime, self.CaptureSnapshot.PrintEndTime);
		self.Settings.debug.LogPrintStateChange("Print Completed!")
		if(not self.IsRendering):
			self.CaptureSnapshot.CleanSnapshots(self.CurrentlyPrintingFileName(),'after-print')
		self.OnPrintEnd()
	def OnPrintEnd(self):
		self.ClearTriggers()
		self.Position = None
	def OnRenderStart(self, *args, **kwargs):
		self.Settings.debug.LogRenderStart("Starting.")
	def OnRenderComplete(self, *args, **kwargs):
		self.HasRendered = True
		filePath = args[0]
		self.Settings.debug.LogRenderComplete("Completed rendering {0}.".format(args[0]))
		rendering = self.Settings.CurrentRendering()
		if(rendering.sync_with_timelapse):
			self.Settings.debug.LogRenderSync("Syncronizing timelapse with the built in timelapse plugin, copying {0} to {1}".format(filePath,rendering.octoprint_timelapse_directory ))
			try:
				shutil.move(filePath,rendering.octoprint_timelapse_directory)
			except:
				type = sys.exc_info()[0]
				value = sys.exc_info()[1]
				self.Settings.debug.LogError("Could move the timelapse at {0} to the octoprint timelaspse directory as {1}. Error Type:{2}, Details:{3}".format(filePath,rendering.octoprint_timelapse_directory,type,value))
		

		self.IsRendering = False
		self.CaptureSnapshot.CleanSnapshots(self.CurrentlyPrintingFileName(),'after_render_complete')
	def OnRenderFail(self, *args, **kwargs):
		self.IsRendering = False
		self.CaptureSnapshot.CleanSnapshots(self.CurrentlyPrintingFileName(),'after_render_fail')
		self.Settings.debug.LogRenderFail("Failed.")
	def CurrentlyPrintingFileName(self):
		if(self._printer is not None):
			current_job = self._printer.get_current_job()
			if current_job is not None and "file" in current_job:
				current_job_file = current_job["file"]
				if "path" in current_job_file and "origin" in current_job_file:
					current_file_path = current_job_file["path"]
					return utility.GetFilenameFromFullPath(current_file_path)
		return ""
	def GcodeQueuing(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		# update the position tracker so that we know where all of the axis are.
		# We will need this later when generating snapshot gcode so that we can return to the previous
		# position
		#

		# check for assert commands
		if(self.Settings is not None):
			
			self.Settings.debug.ApplyCommands(cmd, triggers=self.Triggers, isSnapshot=self.IsPausedByOctolapse)

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
			return cmd
		currentTrigger = trigger.IsTriggering(self.Triggers,self.Position, cmd, self.Settings.debug)
		if(currentTrigger is not None):
			#We're triggering
			
			# build an array of commands to take the snapshot
			if(not self.IsPausedByOctolapse):
				
				self.ResetSnapshotState()
				self.SavedCommand = cmd;
				self.IsPausedByOctolapse = True
				self._printer.pause_print()
				
				self.SendPositionRequestGcode()
				return None
		

		if( trigger.IsSnapshotCommand(cmd,self.Settings.CurrentPrinter().snapshot_command)):
			cmd = None
		return cmd
	def GcodeSent(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		if(self.Settings is None
			or not self.Settings.is_octolapse_enabled
			or self.Triggers is None
			or len(self.Triggers)<1
			or self._printer is None):
			return
		if(self.RequestingPosition and not self.WaitForPosition):
			
			positionCommand =self.PositionGcodes.GcodeCommands[self.PositionCommandIndex]
			self.Settings.debug.LogSnapshotDownload("Looking for position command index {0}.  Command Sent:{1}, Command Expected:{2}".format(self.PositionCommandIndex, cmd, positionCommand))
			if(cmd == positionCommand):
				self.Settings.debug.LogSnapshotDownload("Found the position command.")
				if(self.PositionCommandIndex >= self.PositionGcodes.EndIndex() and not self.WaitForPosition):
					self.WaitForPosition= True
					self.Settings.debug.LogSnapshotDownload("Waiting for position response.")
				else:
					self.PositionCommandIndex += 1
		elif(self.SendingSnapshotCommands and self.SnapshotCommandIndex <= self.SnapshotGcodes.SnapshotIndex ):
			snapshotCommand = self.SnapshotGcodes.GcodeCommands[self.SnapshotCommandIndex]
			self.Settings.debug.LogSnapshotDownload("Looking for snapshot command index {0}.  Command Sent:{1}, Command Expected:{2}".format(self.SnapshotCommandIndex, cmd, snapshotCommand))
			if(cmd == snapshotCommand):
				if(self.SnapshotCommandIndex == self.SnapshotGcodes.SnapshotIndex and not self.WaitForSnapshot):
					self.WaitForSnapshot = True
					self.Settings.debug.LogSnapshotGcodeEndcommand("End Snapshot Gcode Command Found, waiting for snapshot.")
				
				self.SnapshotCommandIndex += 1
		elif(self.SendingSnapshotCommands and self.SnapshotCommandIndex >= self.SnapshotGcodes.SnapshotIndex ):
			snapshotCommand = self.SnapshotGcodes.GcodeCommands[self.SnapshotCommandIndex]
			if(cmd == snapshotCommand ):
				if(self.SnapshotCommandIndex >= self.SnapshotGcodes.EndIndex()):
					self.Settings.debug.LogSnapshotDownload("Sent the final snapshot command.  Resetting state.")
					self.SendingSnapshotCommands = False
					self.WaitForSnapshot = False
					self.SendingSavedCommand = True
					self.SendSavedCommand()
					self.Settings.debug.LogSnapshotDownload("Sending the saved command.")
				self.SnapshotCommandIndex += 1
		elif(self.SendingSavedCommand):
			self.Settings.debug.LogSnapshotDownload("Looking for saved command.  Command Sent:{0}, Command Expected:{1}".format( cmd, self.SavedCommand))
			if(cmd == self.SavedCommand):
				self.Settings.debug.LogSnapshotDownload("Resuming the print.")
				self.ResetSnapshotState()
				self._printer.resume_print()
	def GcodeReceived(self, comm, line, *args, **kwargs):
		if(self.IsPausedByOctolapse):
			if(self.WaitForSnapshot):
				self.WaitForSnapshot = False
				self.Settings.debug.LogSnapshotGcodeEndcommand("End wait for snapshot:{0}".format(line))
				self.TakeSnapshot()
			elif(self.WaitForPosition):
				self.Settings.debug.LogSnapshotGcodeEndcommand("Trying to parse received line for position:{0}".format(line))
				self.ReceivePositionForSnapshotReturn(line)
			else:
				self.Settings.debug.LogSnapshotGcodeEndcommand("Received From Printer:{0}".format(line))
		return line
	def ResetSnapshotState(self):
		self.IsPausedByOctolapse = False

		self.SnapshotGcodes = None
		self.PositionGcodes = None
		self.SavedCommand = None
		self.RequestingPosition = False
		self.WaitForPosition = False
		self.SendingSnapshotCommands = False
		self.WaitForSnapshot = False
		self.SendingSavedCommand = False
		self.SnapshotCommandIndex=0
		self.PositionCommandIndex=0
		

	def SendPositionRequestGcode(self):
		# Send commands to move to the snapshot position
		self.Settings.debug.LogSnapshotPositionReturn("Requesting position for snapshot return.")
		self.PositionGcodes = self.OctolapseGcode.CreatePositionGcode()
		self.Settings.debug.LogInfo(self.PositionGcodes)
		self.RequestingPosition = True
		self.PositionCommandIndex=0
		self._printer.commands(self.PositionGcodes.GcodeCommands);
	def ReceivePositionForSnapshotReturn(self, line):
		parsedResponse = self.Responses.M114.Parse(line)
		self.Settings.debug.LogSnapshotPositionReturn("Snapshot return position received - response:{0}, parsedResponse:{1}".format(line,parsedResponse))
		if(parsedResponse != False):

			x=float(parsedResponse["X"])
			y=float(parsedResponse["Y"])
			z=float(parsedResponse["Z"])
			e=float(parsedResponse["E"])

			previousX = self.Position.X
			previousY = self.Position.Y
			previousZ = self.Position.Z
			if(utility.isclose(previousX, x,abs_tol=1e-8)
				and utility.isclose(previousY, y,abs_tol=1e-8)
				and utility.isclose(previousZ, z,abs_tol=1e-8)
				):
				self.Settings.debug.LogSnapshotPositionReturn("Snapshot return position received - x:{0},y:{1},z:{2},e:{3}".format(x,y,z,e))
			else:
				self.Settings.debug.LogWarning("The position recieved from the printer does not match the position expected by Octolapse.  Expected (x:{0},y:{1},z:{2}), Received (x:{3},y:{4},z:{5})".format(x,y,z,previousX,previousY,previousZ))

			self.Position.UpdatePosition(x,y,z,e)
			self.RequestingPosition = False
			self.WaitForPosition = False
			self.SendSnapshotGcode()

	def SendSnapshotGcode(self):
		self.SnapshotCommandIndex=0
		self.SnapshotGcodes = self.OctolapseGcode.CreateSnapshotGcode(self.Position,self.Position.Extruder)

		if(self.SnapshotGcodes is None):
			self.Settings.debug.LogError("No snapshot gcode was created for this snapshot.  Aborting this snapshot.")
			self.ResetSnapshotState();
			return;
		
		self.SendingSnapshotCommands = True
		self._printer.commands(self.SnapshotGcodes.GcodeCommands);
		
	def SendSavedCommand(self):
		SendingSavedCommand = True
		self._printer.commands(self.SavedCommand);

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
			self.Settings.debug.LogError("Failed to retrieve the snapshot module!  It might work again later.")

	
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
		"octoprint.comm.protocol.gcode.received": __plugin_implementation__.GcodeReceived,

	}

