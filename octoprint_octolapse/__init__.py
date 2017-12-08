# coding=utf-8
from __future__ import absolute_import
import json
import octoprint.plugin
import uuid
import time
import os
import sys
import flask
import requests
from .settings import OctolapseSettings, Printer, Stabilization, Camera, Rendering, Snapshot, DebugProfile
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
import copy
class OctolapsePlugin(	octoprint.plugin.SettingsPlugin,
						octoprint.plugin.AssetPlugin,
						octoprint.plugin.TemplatePlugin,
						octoprint.plugin.StartupPlugin,
						octoprint.plugin.EventHandlerPlugin,
						octoprint.plugin.BlueprintPlugin):
	TIMEOUT_DELAY = 1000
	IsStarted = False
	def __init__(self):
		self.Settings = None
		self.TimelapseSettings = None # Holds all settings that we will use to create a timelapse.  Created when the print starts, destroyed after the print and rendering completes
		self.SnapshotState = None # Holds all state and gcode required to take a snapshot.
		self.Responses = Responses() # Used to decode responses from the 3d printer
		self.Commands = Commands() # used to parse and generate gcode 
		self.SettingsFilePath = None
		
	#Blueprint Plugin Mixin Requests	
	@octoprint.plugin.BlueprintPlugin.route("/setEnabled", methods=["POST"])
	def setEnabled(self):
		requestValues = flask.request.get_json();
		self.Settings.is_octolapse_enabled = requestValues["enabled"];
		# save the updated settings to a file.
		self.SaveSettings()
		return json.dumps({'enabled':self.Settings.is_octolapse_enabled}), 200, {'ContentType':'application/json'} 
	
	# addUpdateProfile Request
	@octoprint.plugin.BlueprintPlugin.route("/addUpdateProfile", methods=["POST"])
	def addUpdateProfile(self):
		requestValues = flask.request.get_json()
		self.Settings.CurrentDebugProfile().LogError(requestValues);
		profileType = requestValues["profileType"];
		profile = requestValues["profile"]
		updatedProfile = self.Settings.addUpdateProfile(profileType, profile)
		# save the updated settings to a file.
		self.SaveSettings()
		return json.dumps(updatedProfile.ToDict()), 200, {'ContentType':'application/json'} ;
	@octoprint.plugin.BlueprintPlugin.route("/removeProfile", methods=["POST"])
	def removeProfile(self):
		requestValues = flask.request.get_json();
		profileType = requestValues["profileType"];
		guid = requestValues["guid"]
		self.Settings.removeProfile(profileType, guid)
		# save the updated settings to a file.
		self.SaveSettings()
		return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 

	@octoprint.plugin.BlueprintPlugin.route("/setCurrentProfile", methods=["POST"])
	def setCurrentProfile(self):
		requestValues = flask.request.get_json();
		profileType = requestValues["profileType"];
		guid = requestValues["guid"]
		self.Settings.setCurrentProfile(profileType, guid)
		self.SaveSettings()
		return json.dumps({'success':True, 'guid':requestValues["guid"]}), 200, {'ContentType':'application/json'} 
	
	def LoadSettings(self):
		# if the settings file does not exist, create one from the default settings
		if(not os.path.isfile(self.SettingsFilePath)):
			# create new settings from defaults
			self.Settings = OctolapseSettings(self._logger)
			# save the defaults
			self.SaveSettings();
		else:
			# Load settings from file
			data = json.load(open(self.SettingsFilePath));

			if(self.Settings == None):
				#  create a new settings object
				self.Settings = OctolapseSettings(self._logger,data);
			else:
				# update an existing settings object
				self.Settings.Update(data);
			
	def SaveSettings(self):
		# Save setting from file
		self._logger.warn("Saving settings.")
		settings = self.Settings.ToDict();
		with open(self.SettingsFilePath, 'w') as outfile:
			json.dump(settings, outfile)
		return None

	def get_settings_defaults(self):
		return dict(load=None)

	def on_settings_load(self):
		self.SettingsFilePath = "{0}{1}settings.json".format(self._basefolder,os.sep)
		self.LoadSettings()
		return self.Settings.ToDict();

	#def on_settings_initialized(self):
		
	
	def CurrentPrinterProfile(self):
		"""Get the plugin's current printer profile"""
		return self._printer_profile_manager.get_current()

	def ResetSnapshotState(self):
		"""Resets the snapshot state.  This should be called before starting to take a snapshot due to a trigger"""
		self.SnapshotState = {
			#State Flags
			'IsPausedByOctolapse': False, # Did octolapse pause the print in order to take a snapshot?
			'RequestingPosition': False, # Are we in the middle of a position request?
			'WaitForPosition': False, # If true, we have sent a position request to the 3d printer, but haven't yet received a response
			'SendingSnapshotCommands': False, # If true, we are in the process of sending gcode to the printer to take a snapshot
			'WaitForSnapshot': False, # If true, we have sent all the gcode necessary to move to the snapshot position and are waiting for a response so that we can take the snapshot.
			'SendingSavedCommand': False, # If true, we are sending the command that triggered the snapshot.  It's been saved to 'SavedCommand'

			#Snapshot Gcode
			'PositionGcodes': None, # gcode to retrieve a position from the printer.  Used before creating snapshot gcode
			'SnapshotGcodes': None, # gcode used to move the printer to the snapshot position and to return to the previous position.  Stores index of the snapshot gcode.
			'SavedCommand': None, # The command that triggered the snapshot.  It will be saved and sent after the SnapshotGcodes are sent.
			
			#Snapshot Gcode Execution Tracking
			'SnapshotCommandIndex':  0,
			'PositionCommandIndex': 0
		}
	def CreateTimelaspeSettings(self):
		self.ResetSnapshotState()
		self.TimelapseSettings = {
			'CameraControl': CameraControl(self.Settings),
			'OctolapseGcode': Gcode(self.Settings,self.CurrentPrinterProfile()),
			'Printer': Printer(self.Settings.CurrentPrinter()),
			'CaptureSnapshot': CaptureSnapshot(self.Settings,printStartTime=time.time()),
			'Position': Position(self.Settings,self.CurrentPrinterProfile()),
			'Render': Render(self.Settings,1,self.OnRenderStart,self.OnRenderFail,self.OnRenderComplete,None),
			'SnapshotCount': 0,
			'CurrentPrintFileName': utility.CurrentlyPrintingFileName(self._printer),
			'Triggers': [],
			'IsRendering': False
			}
		# create the triggers for this print
		snapshot = self.Settings.CurrentSnapshot()
		# If the gcode trigger is enabled, add it
		if(snapshot.gcode_trigger_enabled):
			#Add the trigger to the list
			self.TimelapseSettings['Triggers'].append(GcodeTrigger(self.Settings))
		# If the layer trigger is enabled, add it
		if(snapshot.layer_trigger_enabled):
			self.TimelapseSettings['Triggers'].append(LayerTrigger(self.Settings))
		# If the layer trigger is enabled, add it
		if(snapshot.timer_trigger_enabled):
			self.TimelapseSettings['Triggers'].append(TimerTrigger(self.Settings))

	def get_template_configs(self):
		self._logger.info("Octolapse - is loading template configurations.")
		return [dict(type="settings", custom_bindings=True)]

	## EVENTS
	#########
	# After Startup
	def on_after_startup(self):

		self._logger.info("Octolapse - loaded and active.")
		IsStarted = True
	# Event Mixin Handler
	def on_event(self, event, payload):
		# If we're not enabled, get outta here!
		if(self.Settings is None or not self.Settings.is_octolapse_enabled):
			return
		self._logger.info("Printer event received:{0}.".format(event))
		if (event == Events.PRINT_PAUSED):
			# If octolapse has paused the print, we are taking a snapshot
			if(not self.SnapshotState is not None and self.SnapshotState['IsPausedByOctolapse']):
				self.OnPrintPausedByOctolapse() # octolapse pause
			else:
				self.OnPrintPause() # regular pause
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
			
			
	def OnPrintResumed(self):
		self.Settings.CurrentDebugProfile().LogPrintStateChange("Print Resumed.")

	def OnPrintPause(self):
		self.Settings.CurrentDebugProfile().LogPrintStateChange("Print Paused.")
		if(self.TimelapseSettings['Triggers'] is not None and len(self.TimelapseSettings['Triggers'])>0):
			for trigger in self.TimelapseSettings['Triggers']:
				if(type(trigger) == TimerTrigger):
					trigger.Pause()

	def OnPrintPausedByOctolapse(self):
		self.Settings.CurrentDebugProfile().LogPrintStateChange("Print Paused by Octolapse.")
			
	def OnPrintStart(self):
		self.Settings.CurrentDebugProfile().LogPrintStateChange("Print Started.")
		self.CreateTimelaspeSettings()
		# Clean snapshots
		if(not self.TimelapseSettings['IsRendering']):
			self.TimelapseSettings['CaptureSnapshot'].CleanSnapshots(None,'before-print')
		if(self.Settings.CurrentCamera().apply_settings_before_print):
			self.TimelapseSettings['CameraControl'].ApplySettings()
	def OnPrintFailed(self):
		self.Settings.CurrentDebugProfile().LogPrintStateChange("Print Failed.")
		if(not self.TimelapseSettings['IsRendering']):
			self.TimelapseSettings['IsRendering'] = True
			self.Settings.CurrentDebugProfile().LogInfo("Started Rendering Timelapse");
			self.TimelapseSettings['Render'].Process(self.TimelapseSettings['CurrentPrintFileName'],  self.TimelapseSettings['CaptureSnapshot'].PrintStartTime, self.TimelapseSettings['CaptureSnapshot'].PrintEndTime);
		if(not self.TimelapseSettings['IsRendering']):
			self.TimelapseSettings['CaptureSnapshot'].CleanSnapshots(self.TimelapseSettings['CurrentPrintFileName'],'after-failed')
		self.OnPrintEnd()
	def OnPrintCancelled(self):
		self.Settings.CurrentDebugProfile().LogPrintStateChange("Print Cancelled.")
		if(not self.TimelapseSettings['IsRendering']):
			self.TimelapseSettings['IsRendering'] = True
			self.Settings.CurrentDebugProfile().LogInfo("Started Rendering Timelapse");
			self.TimelapseSettings['Render'].Process(self.TimelapseSettings['CurrentPrintFileName'],  self.TimelapseSettings['CaptureSnapshot'].PrintStartTime, self.TimelapseSettings['CaptureSnapshot'].PrintEndTime);
		if(not self.TimelapseSettings['IsRendering']):
			self.TimelapseSettings['CaptureSnapshot'].CleanSnapshots(self.TimelapseSettings['CurrentPrintFileName'],'after-cancel')
		self.OnPrintEnd()
	def OnPrintCompleted(self):
		self.Settings.CurrentDebugProfile().LogPrintStateChange("Print Completed.")
		self.TimelapseSettings['CaptureSnapshot'].PrintEndTime = time.time()
		if(not self.TimelapseSettings['IsRendering']):
			self.Settings.CurrentDebugProfile().LogInfo("Started Rendering Timelapse");
			self.TimelapseSettings['IsRendering'] = True
			self.TimelapseSettings['Render'].Process(self.TimelapseSettings['CurrentPrintFileName'],  self.TimelapseSettings['CaptureSnapshot'].PrintStartTime, self.TimelapseSettings['CaptureSnapshot'].PrintEndTime);
		self.Settings.CurrentDebugProfile().LogPrintStateChange("Print Completed!")
		if(not self.TimelapseSettings['IsRendering']):
			self.TimelapseSettings['CaptureSnapshot'].CleanSnapshots(self.TimelapseSettings['CurrentPrintFileName'],'after-print')
		self.OnPrintEnd()
	def OnPrintEnd(self):
		self.Settings.CurrentDebugProfile().LogInfo("Print Ended.");

	# RENDERING EVENTS
	def OnRenderStart(self, *args, **kwargs):
		self.Settings.CurrentDebugProfile().LogRenderStart("Starting.")

	def OnRenderComplete(self, *args, **kwargs):
		filePath = args[0]
		self.Settings.CurrentDebugProfile().LogRenderComplete("Completed rendering {0}.".format(args[0]))
		# using the live settings here, so the user can change them while printing
		if(self.Settings.CurrentRendering().sync_with_timelapse):
			self.Settings.CurrentDebugProfile().LogRenderSync("Syncronizing timelapse with the built in timelapse plugin, copying {0} to {1}".format(filePath,self.TimelapseSettings['Render'].octoprint_timelapse_directory ))
			try:
				shutil.move(filePath,self.TimelapseSettings['Render'].octoprint_timelapse_directory)
			except:
				type = sys.exc_info()[0]
				value = sys.exc_info()[1]
				self.Settings.CurrentDebugProfile().LogError("Could move the timelapse at {0} to the octoprint timelaspse directory as {1}. Error Type:{2}, Details:{3}".format(filePath,self.TimelapseSettings['Render'].octoprint_timelapse_directory,type,value))
		self.TimelapseSettings['IsRendering'] = False
		self.TimelapseSettings['CaptureSnapshot'].CleanSnapshots(self.TimelapseSettings['CurrentPrintFileName'],'after_render_complete')
	def OnRenderFail(self, *args, **kwargs):
		self.TimelapseSettings['IsRendering'] = False
		self.TimelapseSettings['CaptureSnapshot'].CleanSnapshots(self.TimelapseSettings['CurrentPrintFileName'],'after_render_fail')
		self.Settings.CurrentDebugProfile().LogRenderFail("Failed.")

	def IsTimelapseActive(self):
		if (# wait for the snapshot command to finish sending, or wait for the snapshot delay in case of timeouts)
			self.Settings is None
			or self.TimelapseSettings is None
			or not self.Settings.is_octolapse_enabled
			or self.TimelapseSettings['Triggers'] is None
			or len(self.TimelapseSettings['Triggers'])<1
			or self._printer is None
			):
			return False
		return True
	def GcodeQueuing(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		# update the position tracker so that we know where all of the axis are.
		# We will need this later when generating snapshot gcode so that we can return to the previous
		# position
		#
		if(self.TimelapseSettings is not None):
			self.TimelapseSettings['Position'].Update(cmd)

		# Don't do anything further to any commands unless we are taking a timelapse , or if octolapse paused the print.
		
		if(not self.IsTimelapseActive()):
			return cmd

		#Apply any debug assert commands
		self.Settings.debug.ApplyCommands(cmd, triggers=self.TimelapseSettings['Triggers'], isSnapshot=self.SnapshotState['IsPausedByOctolapse'])

		if(self.SnapshotState['IsPausedByOctolapse']):
			return cmd
		
		currentTrigger = trigger.IsTriggering(self.TimelapseSettings['Triggers'],self.TimelapseSettings['Position'], cmd, self.Settings.debug)
		if(currentTrigger is not None):
			#We're triggering
			
			# build an array of commands to take the snapshot
			if(not self.SnapshotState['IsPausedByOctolapse']):
				
				self.ResetSnapshotState()
				self.SnapshotState['SavedCommand'] = cmd;
				self.SnapshotState['IsPausedByOctolapse'] = True
				self._printer.pause_print()
				
				self.SendPositionRequestGcode()

				# we don't want to execute the current command.  We have saved it for later.
				return None
		
		# in all cases do not return the snapshot command to the printer.  It is NOT a real gcode and could cause errors.
		if( trigger.IsSnapshotCommand(cmd,self.Settings.CurrentPrinter().snapshot_command)):
			cmd = None

		return cmd

	def GcodeSent(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		if(not self.IsTimelapseActive() ):
			return
		if(self.SnapshotState['RequestingPosition'] and not self.SnapshotState['WaitForPosition']):
			positionCommand =self.SnapshotState['PositionGcodes'].GcodeCommands[self.SnapshotState['PositionCommandIndex']]
			self.Settings.CurrentDebugProfile().LogSnapshotDownload("Looking for position command index {0}.  Command Sent:{1}, Command Expected:{2}".format(self.SnapshotState['PositionCommandIndex'], cmd, positionCommand))
			if(cmd == positionCommand):
				self.Settings.CurrentDebugProfile().LogSnapshotDownload("Found the position command.")
				if(self.SnapshotState['PositionCommandIndex'] >= self.SnapshotState['PositionGcodes'].EndIndex() and not self.SnapshotState['WaitForPosition']):
					self.SnapshotState['WaitForPosition']= True
					self.Settings.CurrentDebugProfile().LogSnapshotDownload("Waiting for position response.")
				else:
					self.SnapshotState['PositionCommandIndex'] += 1

		elif(self.SnapshotState['SendingSnapshotCommands'] and self.SnapshotState['SnapshotCommandIndex'] <= self.SnapshotState['SnapshotGcodes'].SnapshotIndex ):
			snapshotCommand = self.SnapshotState['SnapshotGcodes'].GcodeCommands[self.SnapshotState['SnapshotCommandIndex']]
			self.Settings.CurrentDebugProfile().LogSnapshotDownload("Looking for snapshot command index {0}.  Command Sent:{1}, Command Expected:{2}".format(self.SnapshotState['SnapshotCommandIndex'], cmd, snapshotCommand))
			if(cmd == snapshotCommand):
				if(self.SnapshotState['SnapshotCommandIndex'] == self.SnapshotState['SnapshotGcodes'].SnapshotIndex and not self.SnapshotState['WaitForSnapshot']):
					self.SnapshotState['WaitForSnapshot'] = True
					self.Settings.CurrentDebugProfile().LogSnapshotGcodeEndcommand("End Snapshot Gcode Command Found, waiting for snapshot.")
				self.SnapshotState['SnapshotCommandIndex'] += 1

		elif(self.SnapshotState['SendingSnapshotCommands'] and self.SnapshotState['SnapshotCommandIndex'] >= self.SnapshotState['SnapshotGcodes'].SnapshotIndex ):
			snapshotCommand = self.SnapshotState['SnapshotGcodes'].GcodeCommands[self.SnapshotState['SnapshotCommandIndex']]
			if(cmd == snapshotCommand ):
				if(self.SnapshotState['SnapshotCommandIndex'] >= self.SnapshotState['SnapshotGcodes'].EndIndex()):
					self.Settings.CurrentDebugProfile().LogSnapshotDownload("Sent the final snapshot command.  Resetting state.")
					self.SnapshotState['SendingSnapshotCommands'] = False
					self.SnapshotState['WaitForSnapshot'] = False
					self.SnapshotState['SendingSavedCommand'] = True
					self.SendSavedCommand()
					self.Settings.CurrentDebugProfile().LogSnapshotDownload("Sending the saved command.")
				self.SnapshotState['SnapshotCommandIndex'] += 1

		elif(self.SnapshotState['SendingSavedCommand']):
			self.Settings.CurrentDebugProfile().LogSnapshotDownload("Looking for saved command.  Command Sent:{0}, Command Expected:{1}".format( cmd, self.SnapshotState['SavedCommand']))
			if(cmd == self.SnapshotState['SavedCommand']):
				self.Settings.CurrentDebugProfile().LogSnapshotDownload("Resuming the print.")
				self.ResetSnapshotState()
				self._printer.resume_print()

	def GcodeReceived(self, comm, line, *args, **kwargs):
		if(not self.IsTimelapseActive() ):
			return line

		if(self.SnapshotState['IsPausedByOctolapse']):
			if(self.SnapshotState['WaitForSnapshot']):
				self.SnapshotState['WaitForSnapshot'] = False
				self.Settings.CurrentDebugProfile().LogSnapshotGcodeEndcommand("End wait for snapshot:{0}".format(line))
				self.TakeSnapshot()
			elif(self.SnapshotState['WaitForPosition']):
				self.Settings.CurrentDebugProfile().LogSnapshotGcodeEndcommand("Trying to parse received line for position:{0}".format(line))
				self.ReceivePositionForSnapshotReturn(line)
			else:
				self.Settings.CurrentDebugProfile().LogSnapshotGcodeEndcommand("Received From Printer:{0}".format(line))
		return line

	def SendPositionRequestGcode(self):
		# Send commands to move to the snapshot position
		self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Requesting position for snapshot return.")
		self.SnapshotState['PositionGcodes'] = self.TimelapseSettings['OctolapseGcode'].CreatePositionGcode()
		self.Settings.CurrentDebugProfile().LogInfo(self.SnapshotState['PositionGcodes'])
		self.SnapshotState['RequestingPosition'] = True
		self.SnapshotState['PositionCommandIndex']=0
		self._printer.commands(self.SnapshotState['PositionGcodes'].GcodeCommands);

	def ReceivePositionForSnapshotReturn(self, line):
		parsedResponse = self.Responses.M114.Parse(line)
		self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Snapshot return position received - response:{0}, parsedResponse:{1}".format(line,parsedResponse))
		if(parsedResponse != False):

			x=float(parsedResponse["X"])
			y=float(parsedResponse["Y"])
			z=float(parsedResponse["Z"])
			e=float(parsedResponse["E"])

			previousX = self.TimelapseSettings['Position'].X
			previousY = self.TimelapseSettings['Position'].Y
			previousZ = self.TimelapseSettings['Position'].Z
			if(utility.isclose(previousX, x,abs_tol=1e-8)
				and utility.isclose(previousY, y,abs_tol=1e-8)
				and utility.isclose(previousZ, z,abs_tol=1e-8)
				):
				self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Snapshot return position received - x:{0},y:{1},z:{2},e:{3}".format(x,y,z,e))
			else:
				self.Settings.CurrentDebugProfile().LogWarning("The position recieved from the printer does not match the position expected by Octolapse.  Expected (x:{0},y:{1},z:{2}), Received (x:{3},y:{4},z:{5})".format(x,y,z,previousX,previousY,previousZ))

			self.TimelapseSettings['Position'].UpdatePosition(x,y,z,e)
			self.SnapshotState['RequestingPosition'] = False
			self.SnapshotState['WaitForPosition'] = False
			self.SendSnapshotGcode()

	def SendSnapshotGcode(self):
		self.SnapshotState['SnapshotCommandIndex']=0
		self.SnapshotState['SnapshotGcodes'] = self.TimelapseSettings['OctolapseGcode'].CreateSnapshotGcode(self.TimelapseSettings['Position'],self.TimelapseSettings['Position'].Extruder)

		if(self.SnapshotState['SnapshotGcodes'] is None):
			self.Settings.CurrentDebugProfile().LogError("No snapshot gcode was created for this snapshot.  Aborting this snapshot.")
			self.ResetSnapshotState();
			return;
		
		self.SnapshotState['SendingSnapshotCommands'] = True
		self._printer.commands(self.SnapshotState['SnapshotGcodes'].GcodeCommands);
		
	def SendSavedCommand(self):
		SendingSavedCommand = True
		self._printer.commands(self.SnapshotState['SavedCommand']);

	def TakeSnapshot(self):
		snapshot = self.TimelapseSettings['CaptureSnapshot']
		self.TimelapseSettings['SnapshotCount'] += 1
		if(snapshot is not None):
			try:
				snapshot.Snap(self.TimelapseSettings['CurrentPrintFileName'],self.TimelapseSettings['SnapshotCount'])
			except:
					
				a = sys.exc_info() # Info about unknown error that caused exception.                                              
				errorMessage = "    {0}".format(a)
				b = [ str(p) for p in a ]
				errorMessage += "\n    {0}".format(b)
				self._logger.error('Unknown error detected:{0}'.format(errorMessage))
			
		else:
			self.Settings.CurrentDebugProfile().LogError("Failed to retrieve the snapshot module!  It might work again later.")

	
	##~~ AssetPlugin mixin
	def get_assets(self):
		self._logger.info("Octolapse is loading assets.")
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(
			js = [
				"js/octolapse.js"
				,"js/octolapse.profiles.js"
				,"js/octolapse.profiles.printer.js"
				,"js/octolapse.profiles.stabilization.js"
				,"js/octolapse.profiles.snapshot.js"
				,"js/octolapse.profiles.rendering.js"
				,"js/octolapse.profiles.camera.js"
				,"js/octolapse.profiles.debug.js"
			],
			css = ["css/octolapse.css"],
			less = ["less/octolapse.less"])

	##~~ Softwareupdate hook
	def get_update_information(self):
		# Define the configuration for your plugin to use with the Software Update
		# Plugin here.  See
		# https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
		# for details.
		self._logger.info("Octolapse is getting update information.")
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

