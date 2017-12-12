# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import uuid
import time
import os
import sys
import json
from pprint import pformat
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
		self.IsPrinting = False
		
		
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

	def SettingsFilePath(self):
		return "{0}{1}settings.json".format(self.get_plugin_data_folder(),os.sep)

	def LogFilePath(self):
		return self._settings.get_plugin_logfile_path();
	def LoadSettings(self):
		try:
			# if the settings file does not exist, create one from the default settings
			
			createNewSettings = False

			if(not os.path.isfile(self.SettingsFilePath())):
				# create new settings from defaults
				self.Settings = OctolapseSettings(self.LogFilePath())
				self.Settings.CurrentDebugProfile().LogSettingsLoad("Creating new settings file from defaults.")			
				createNewSettings = True
			else:
				# Load settings from file
				if(self.Settings is not None):
					self.Settings.CurrentDebugProfile().LogSettingsLoad("Loading existings settings file from: {0}.".format(self.SettingsFilePath()))
				else:
					self._logger.info("Loading existing settings file from: {0}.".format(self.SettingsFilePath()))
				with open(self.SettingsFilePath()) as settingsJson:
					data = json.load(settingsJson);
				if(self.Settings == None):
					#  create a new settings object
					self.Settings = OctolapseSettings(self.LogFilePath(), data);
					self.Settings.CurrentDebugProfile().LogSettingsLoad("Settings loaded.  Created new settings object: {0}.".format(data))			
				else:
					# update an existing settings object
					self.Settings.CurrentDebugProfile().LogSettingsLoad("Settings loaded.  Updating existing settings object: {0}.".format(data))			
					self.Settings.Update(data)	
			# Extract any settings from octoprint that would be useful to our users.
			self.CopyOctoprintDefaultSettings(applyToCurrentProfiles=createNewSettings)

			if(createNewSettings):
				# No file existed, so we must have created default settings.  Save them!
				self.SaveSettings()
			return self.Settings.ToDict();
		except TypeError,e:
			self._logger.exception("Could not load octolapse settings.  Details: {0}".format(e))
	def CopyOctoprintDefaultSettings(self, applyToCurrentProfiles = False):
		# move some octoprint defaults if they exist for the webcam
		# specifically the address, the bitrate and the ffmpeg directory.
		webcamSettings = self._settings.settings.get(["webcam"])

		# Attempt to get the camera address and snapshot template from Octoprint settings
		if("snapshot" in webcamSettings ):
			snapshotUrl = webcamSettings["snapshot"]
			from urlparse import urlparse
			# we are doing some templating so we have to try to separate the
			# camera base address from the querystring.  This will probably not work
			# for all cameras.
			try:
				o = urlparse(snapshotUrl)
				cameraAddress = o.scheme + "://" + o.netloc + o.path
				self.Settings.CurrentDebugProfile().LogInfo("Setting octolapse camera address to {0}.".format(cameraAddress))
				snapshotAction = urlparse(snapshotUrl).query
				snapshotRequestTemplate = "{camera_address}?" + snapshotAction;
				self.Settings.CurrentDebugProfile().LogInfo("Setting octolapse camera snapshot template to {0}.".format(snapshotRequestTemplate))
				self.Settings.DefaultCamera.address = cameraAddress
				self.Settings.DefaultCamera.snapshot_request_template = snapshotRequestTemplate
				if(applyToCurrentProfiles):
					self.Settings.CurrentCamera().address = cameraAddress;
					self.Settings.CurrentCamera().snapshot_request_template = snapshotRequestTemplate
			except TypeError, e:
				self.Settings.CurrentDebugProfile().LogError("Unable to parse the snapshot address from Octoprint's settings, using system default. Details: {0}".format(e))

		# Attempt to set the bitrate
		if("bitrate" in webcamSettings):
			bitrate = webcamSettings["bitrate"]
			self.Settings.DefaultCamera.bitrate = bitrate
			if(applyToCurrentProfiles):
				self.Settings.CurrentCamera().bitrate = bitrate

	def SaveSettings(self):
		# Save setting from file
		settings = self.Settings.ToDict();
		self.Settings.CurrentDebugProfile().LogSettingsSave("Saving Settings.".format(settings))
		
		with open(self.SettingsFilePath(), 'w') as outfile:
			json.dump(settings, outfile)
		self.Settings.CurrentDebugProfile().LogSettingsSave("Settings saved: {0}".format(settings))
		return None

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
			'WaitForSnapshotReturnPosition': False, # If true, we have sent a position request to the 3d printer, but haven't yet received a response
			'ApplyingCameraSettings': False, # are we trying to adjust the camera?  
			'SendingSnapshotCommands': False, # If true, we are in the process of sending gcode to the printer to take a snapshot
			'WaitForSnapshotPosition': False, # If true, we have sent all the gcode necessary to move to the snapshot position and are waiting for a response so that we can take the snapshot.
			'SendingReturnCommands': False,
			'SendingSavedCommand': False, # If true, we are sending the command that triggered the snapshot.  It's been saved to 'SavedCommand'

			#Snapshot Gcode
			'PositionGcodes': None, # gcode to retrieve a position from the printer.  Used before creating snapshot gcode
			'SnapshotGcodes': None, # gcode used to move the printer to the snapshot position and to return to the previous position.  Stores index of the snapshot gcode.
			'SavedCommand': None, # The command that triggered the snapshot.  It will be saved and sent after the SnapshotGcodes are sent.
			
			#Snapshot Gcode Execution Tracking
			'SnapshotCommandIndex':  0,
			'PositionCommandIndex': 0
		}

	def PrintSnapshotState(self):
		output = "";
		for entry in SnapshotState:
			output+= entry
	def CreateTimelaspeSettings(self):
		
		self.ResetSnapshotState()
		webcam = self._settings.settings.get(["webcam"])
		ffmpegPath = ""
		if("ffmpeg" in webcam):
			ffmpegPath = webcam["ffmpeg"]
		if(self.Settings.CurrentRendering().enabled and ffmpegPath == ""):
			return {'success':False, 'error':"No ffmpeg path is set.  Please configure this setting within the Octoprint settings pages located at Features->Webcam & Timelapse under Timelapse Recordings->Path to FFMPEG."}

		if(not os.path.isfile(ffmpegPath)):
			return {'success':False, 'error':"The ffmpeg {0} does not exist.  Please configure this setting within the Octoprint settings pages located at Features->Webcam & Timelapse under Timelapse Recordings->Path to FFMPEG.".format(ffmpegPath)}
		self.TimelapseSettings = {
			'CameraControl': CameraControl(self.Settings, self.OnCameraSettingsSuccess, self.OnCameraSettingsFail, self.OnCameraSettingsCompelted),
			'OctolapseGcode': Gcode(self.Settings,self.CurrentPrinterProfile()),
			'Printer': Printer(self.Settings.CurrentPrinter()),
			'CaptureSnapshot': CaptureSnapshot(self.Settings,  self.get_plugin_data_folder(), printStartTime=time.time()),
			'Position': Position(self.Settings,self.CurrentPrinterProfile()),
			'Render': Render(self.Settings,self.get_plugin_data_folder(),self._settings.getBaseFolder("timelapse"),  ffmpegPath,1,onStart = self.OnRenderStart,onFail=self.OnRenderFail, onSuccess = self.OnRenderSuccess, onAlways = self.OnRenderingComplete, onAfterSyncFail = self.OnSyncronizeRenderingFail, onAfterSycnSuccess = self.OnSyncronizeRenderingComplete),
			'SnapshotCount': 0,
			'CurrentPrintFileName': utility.CurrentlyPrintingFileName(self._printer),
			'Triggers': [],
			'IsRendering': False,
			'SnapshotRequestCount': 0
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

		return {'success':True}

	def ResetTimelapseSettings(self):
		if(self.TimelapseSettings is not None):
			if(self.TimelapseSettings["SnapshotRequestCount"] == 0 and not self.TimelapseSettings["IsRendering"]):
				self.TimelapseSettings = None
				self.ResetSnapshotState()
	## EVENTS
	#########
	def get_settings_defaults(self):
		return dict(load=None)
	
	def on_settings_load(self):
		octoprint.plugin.SettingsPlugin.on_settings_load(self)
		return self.LoadSettings()
	
	def get_template_configs(self):
		self._logger.info("Octolapse - is loading template configurations.")
		return [dict(type="settings", custom_bindings=True)]

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
			if(not self.SnapshotState is not None and (self.SnapshotState['IsPausedByOctolapse'] or self.SnapshotState['ApplyingCameraSettings'])):
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
		self.IsPrinting = True
		settingsCreatedResult = self.CreateTimelaspeSettings()
		if(not settingsCreatedResult["success"]):
			# display a warning
			self.Settings.CurrentDebugProfile().LogWarning("Unable to create timelapse settings: {0}".format(settingsCreatedResult["error"]))
			# cancel the print
			self._printer.cancel_print()
			return
		
		if(self.Settings.CurrentCamera().apply_settings_before_print):
			self.SnapshotState['ApplyingCameraSettings'] = True
			self._printer.pause_print();
			self.TimelapseSettings['CameraControl'].ApplySettings()

	def OnCameraSettingsSuccess(self, *args, **kwargs):
		numSettings = args[0]
		self.Settings.CurrentDebugProfile().LogCameraSettingsApply("Camera Settings - Successfully applied all {0} camera settings.".format(numSettings))

	def OnCameraSettingsFail(self, *args, **kwargs):
		numSettings = args[0]
		errorMessages = args[1]
		self.Settings.CurrentDebugProfile().LogCameraSettingsApply("Camera Settings - {0} of {1} settings failed.  Details:".format(len(errorMessages), numSettings))
		for message in errorMessages:
			self.Settings.CurrentDebugProfile().LogCameraSettingsApply(message)
		
	def OnCameraSettingsCompelted(self, *args, **kwargs):
		self.Settings.CurrentDebugProfile().LogCameraSettingsApply("Camera Settings - Completed")
		self.SnapshotState['ApplyingCameraSettings'] = False
		self._printer.resume_print()

	def OnPrintFailed(self):
		self.Settings.CurrentDebugProfile().LogPrintStateChange("Print Failed.")
		self.OnPrintEnd()
	def OnPrintCancelled(self):
		self.Settings.CurrentDebugProfile().LogPrintStateChange("Print Cancelled.")
		self.OnPrintEnd()
	def OnPrintCompleted(self):
		self.Settings.CurrentDebugProfile().LogPrintStateChange("Print Completed.")
		self.TimelapseSettings['CaptureSnapshot'].PrintEndTime = time.time()
		self.Settings.CurrentDebugProfile().LogPrintStateChange("Print Completed!")
		self.OnPrintEnd()
	def OnPrintEnd(self):
		self.RenderTimelapse()
		self.Settings.CurrentDebugProfile().LogInfo("Print Ended.");
		
	def IsTimelapseActive(self):
		if (# wait for the snapshot command to finish sending, or wait for the snapshot delay in case of timeouts)
			self.Settings is None
			or self.TimelapseSettings is None
			or self.SnapshotState is None
			or not self.IsPrinting
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

		#Apply any debug assert commands
		if(self.Settings is not None):
			self.Settings.CurrentDebugProfile().ApplyCommands(cmd, self.TimelapseSettings, self.SnapshotState)

		if(not self.IsTimelapseActive()):
			return cmd

		
		if(self.SnapshotState['IsPausedByOctolapse']):
			return cmd
		
		currentTrigger = trigger.IsTriggering(self.TimelapseSettings['Triggers'],self.TimelapseSettings['Position'], cmd, self.Settings.CurrentDebugProfile())
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
				return None,
		
		# in all cases do not return the snapshot command to the printer.  It is NOT a real gcode and could cause errors.
		if( trigger.IsSnapshotCommand(cmd,self.Settings.CurrentPrinter().snapshot_command)):
			return None,
		return None
	def GcodeSent(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		if(not self.IsTimelapseActive()):
			return
			
		if(self.SnapshotState['RequestingPosition'] and not self.SnapshotState['WaitForSnapshotReturnPosition']):
			positionCommand =self.SnapshotState['PositionGcodes'].GcodeCommands[self.SnapshotState['PositionCommandIndex']]
			self.Settings.CurrentDebugProfile().LogSnapshotDownload("Looking for position command index {0}.  Command Sent:{1}, Command Expected:{2}".format(self.SnapshotState['PositionCommandIndex'], cmd, positionCommand))
			if(cmd == positionCommand  and not self.SnapshotState['WaitForSnapshotReturnPosition']):
				self.Settings.CurrentDebugProfile().LogSnapshotDownload("Found the position command.")
				if(self.SnapshotState['PositionCommandIndex'] >= self.SnapshotState['PositionGcodes'].EndIndex() and not self.SnapshotState['WaitForSnapshotReturnPosition']):
					self.SnapshotState['WaitForSnapshotReturnPosition']= True
					self.SnapshotState['RequestingPosition'] = False
					self.Settings.CurrentDebugProfile().LogSnapshotDownload("Waiting for position response.")
				self.SnapshotState['PositionCommandIndex'] += 1

		elif(self.SnapshotState['SendingSnapshotCommands'] and not self.SnapshotState['WaitForSnapshotPosition']):
			snapshotCommand = self.SnapshotState['SnapshotGcodes'].GcodeCommands[self.SnapshotState['SnapshotCommandIndex']]
			self.Settings.CurrentDebugProfile().LogSnapshotDownload("Looking for SnapshotGcode command index {0}.  Command Sent:{1}, Command Expected:{2}".format(self.SnapshotState['SnapshotCommandIndex'], cmd, snapshotCommand))
			if(cmd == snapshotCommand and not self.SnapshotState['WaitForSnapshotPosition']):
				if(self.SnapshotState['SnapshotCommandIndex'] >= self.SnapshotState['SnapshotGcodes'].SnapshotIndex):
					self.SnapshotState['SendingSnapshotCommands'] = False
					self.SnapshotState['WaitForSnapshotPosition'] = True
					self.Settings.CurrentDebugProfile().LogSnapshotGcodeEndcommand("End Snapshot Gcode Command Found, waiting for snapshot.")
				self.SnapshotState['SnapshotCommandIndex'] += 1
			
		elif(self.SnapshotState['SendingReturnCommands']):
			snapshotCommand = self.SnapshotState['SnapshotGcodes'].GcodeCommands[self.SnapshotState['SnapshotCommandIndex']]
			self.Settings.CurrentDebugProfile().LogSnapshotDownload("Looking for return SnapshotGcode command index {0}.  Command Sent:{1}, Command Expected:{2}".format(self.SnapshotState['SnapshotCommandIndex'], cmd, snapshotCommand))
			if(cmd == snapshotCommand):
				if(self.SnapshotState['SnapshotCommandIndex'] >= self.SnapshotState['SnapshotGcodes'].EndIndex()):
					self.Settings.CurrentDebugProfile().LogSnapshotGcodeEndcommand("End return gcode command found, sending saved command.")
					self.SnapshotState['SendingReturnCommands'] = False
					self.Settings.CurrentDebugProfile().LogSnapshotGcodeEndcommand("Before Sending Saved Command.")
					self.SnapshotState['SendingSavedCommand'] = True
					self.Settings.CurrentDebugProfile().LogSnapshotGcodeEndcommand("After Sending Saved Command.")
					self.SendSavedCommand()
				self.SnapshotState['SnapshotCommandIndex'] += 1

		elif(self.SnapshotState['SendingSavedCommand']):
			self.Settings.CurrentDebugProfile().LogSnapshotDownload("Looking for saved command.  Command Sent:{0}, Command Expected:{1}".format( cmd, self.SnapshotState['SavedCommand']))
			if(cmd == self.SnapshotState['SavedCommand']):
				self.Settings.CurrentDebugProfile().LogSnapshotDownload("Save Command Received.")
				self.EndSnapshot()
		self.Settings.CurrentDebugProfile().LogSentGcode("Sent to printer: Command Type:{0}, gcode:{1}, cmd: {2}".format(cmd_type, gcode, cmd))

	def GcodeReceived(self, comm, line, *args, **kwargs):
		
		if(self.SnapshotState is not None and self.SnapshotState['IsPausedByOctolapse']):
			#TODO:  Remove this logging after debug
			#self.Settings.CurrentDebugProfile().LogWarning("Paused - GcodeReceived: {0}, SnapshotState:{1}".format(line, pformat(self.SnapshotState)))
			if(self.SnapshotState['WaitForSnapshotPosition']):
				self.Settings.CurrentDebugProfile().LogSnapshotGcodeEndcommand("End wait for snapshot position:{0}".format(line))
				self.ReceivePositionOfSnapshot(line)
				
			elif(self.SnapshotState['WaitForSnapshotReturnPosition']):
				self.Settings.CurrentDebugProfile().LogSnapshotGcodeEndcommand("End wait for snapshot return position:{0}".format(line))
				self.ReceivePositionForSnapshotReturn(line)
			else:
				self.Settings.CurrentDebugProfile().LogSnapshotGcodeEndcommand("Received From Printer:{0}".format(line))
		return line

	def SendPositionRequestGcode(self):
		# Send commands to move to the snapshot position
		self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Requesting position for snapshot return.")
		self.SnapshotState['PositionGcodes'] = self.TimelapseSettings['OctolapseGcode'].CreatePositionGcode()
		for line in self.SnapshotState["PositionGcodes"].GcodeCommands:
			self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn(line)
		self.SnapshotState['RequestingPosition'] = True
		self.SnapshotState['PositionCommandIndex']=0
		self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("This occurred right BEFORE position request gcode was sent.")
		self._printer.commands(self.SnapshotState['PositionGcodes'].GcodeCommands);
		self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("This occurred right AFTER  position request gcode was sent.")
	def ReceivePositionForSnapshotReturn(self, line):
		parsedResponse = self.Responses.M114.Parse(line)
		if(parsedResponse != False):
			self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Snapshot return position received - response:{0}, parsedResponse:{1}".format(line,parsedResponse))
			x=float(parsedResponse["X"])
			y=float(parsedResponse["Y"])
			z=float(parsedResponse["Z"])
			e=float(parsedResponse["E"])

			previousX = self.TimelapseSettings['Position'].X
			previousY = self.TimelapseSettings['Position'].Y
			previousZ = self.TimelapseSettings['Position'].Z
			if(
				(previousX is None or utility.isclose(previousX, x,abs_tol=1e-8))
				and (previousY is None or utility.isclose(previousY, y,abs_tol=1e-8))
				and (previousZ is None or utility.isclose(previousZ, z,abs_tol=1e-8))
				):
				self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Snapshot return position received - x:{0},y:{1},z:{2},e:{3}".format(x,y,z,e))
			else:
				self.Settings.CurrentDebugProfile().LogWarning("The position recieved from the printer does not match the position expected by Octolapse.  received (x:{0},y:{1},z:{2}), Expected (x:{3},y:{4},z:{5})".format(x,y,z,previousX,previousY,previousZ))

			self.TimelapseSettings['Position'].UpdatePosition(x,y,z,e)
			self.SnapshotState['WaitForSnapshotReturnPosition'] = False
			self.SendSnapshotGcode()
		else:
			self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Received reponse is not the expected position response: Received: {0}".format(line))

	def ReceivePositionOfSnapshot(self, line):
		parsedResponse = self.Responses.M114.Parse(line)
		if(parsedResponse != False):

			self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Snapshot position verification received - response:{0}, parsedResponse:{1}".format(line,parsedResponse))
			self.SnapshotState['WaitForSnapshotPosition'] = False
			x=float(parsedResponse["X"])
			y=float(parsedResponse["Y"])
			z=float(parsedResponse["Z"])
			e=float(parsedResponse["E"])

			returnX = self.SnapshotState['SnapshotGcodes'].ReturnX
			returnY = self.SnapshotState['SnapshotGcodes'].ReturnY
			returnZ = self.SnapshotState['SnapshotGcodes'].ReturnZ
			if(
				(utility.isclose(returnX, x,abs_tol=1e-8))
				and (utility.isclose(returnY, y,abs_tol=1e-8))
				and (utility.isclose(returnZ, z,abs_tol=1e-8))
			):
				self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Snapshot verification position received - x:{0},y:{1},z:{2},e:{3}".format(x,y,z,e))
			else:
				self.Settings.CurrentDebugProfile().LogWarning("The snapshot verification position recieved from the printer does not match the position expected by Octolapse.  received (x:{0},y:{1},z:{2}), Expected (x:{3},y:{4},z:{5})".format(x,y,z,returnX,returnY,returnZ))

			self.TimelapseSettings['Position'].UpdatePosition(x,y,z,e)
			
			self.TakeSnapshot()
		else:
			self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Received reponse is not the expected position response: Received: {0}".format(line))

	def SendSnapshotGcode(self):
		self.SnapshotState['SnapshotCommandIndex']=0
		self.SnapshotState['SnapshotGcodes'] = self.TimelapseSettings['OctolapseGcode'].CreateSnapshotGcode(self.TimelapseSettings['Position'],self.TimelapseSettings['Position'].Extruder)

		if(self.SnapshotState['SnapshotGcodes'] is None):
			self.Settings.CurrentDebugProfile().LogError("No snapshot gcode was created for this snapshot.  Aborting this snapshot.")
			self.AbortSnapshot()
			return;
		
		self.SnapshotState['SendingSnapshotCommands'] = True
		self._printer.commands(self.SnapshotState['SnapshotGcodes'].SnapshotCommands());

	def SendReturnGcode(self):
		self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Sending Snapshot Return Code")
		if(self.SnapshotState['SnapshotGcodes'] is None):
			self.Settings.CurrentDebugProfile().LogError("Cannot return to original position, no snapshot gcode available.  Aborting print, otherwise we'll print a pile of spaghetti.  Sorry :(")
			# We have to stop the print, this is a critical error.
			self._printer.cancel_print()
			return;
		
		self.SnapshotState['SendingReturnCommands'] = True
		self._printer.commands(self.SnapshotState['SnapshotGcodes'].ReturnCommands())

	def AbortSnapshot(self, message):
		"""Stops the current snapshot, but continues.  Eventually this will display a user notification"""
		# Todo:  Display a message for the user
		
		# End the current snapshot
		self.EndSnapshot()

	def EndSnapshot(self):
		# Cleans up the variables and resumes the print once the snapshot is finished, and the extruder is in the proper position 
		isPaused = self.SnapshotState["IsPausedByOctolapse"]
		# reset the snapshot variables
		self.ResetSnapshotState();

		# if the print is paused, resume!
		self.Settings.CurrentDebugProfile().LogSnapshotDownload("Resuming Print.")
		self._printer.resume_print()

	def StopTimelapse(self, message):
		"""Stops the current timelapse and clears out the variables"""
		self.ResetSnapshotState();
		self.ResetTimelapseSettings();
		
	def SendSavedCommand(self):
		SendingSavedCommand = True
		savedCommnd = self.SnapshotState['SavedCommand'];
		if( not trigger.IsSnapshotCommand(savedCommnd,self.Settings.CurrentPrinter().snapshot_command)):
			self.Settings.CurrentDebugProfile().LogSnapshotDownload("Sending the saved command: {0}.".format(savedCommnd))
			self._printer.commands(savedCommnd)
		else:
			self.Settings.CurrentDebugProfile().LogSnapshotDownload("No saved command to send, it was our snapshot gcode.")
			self.EndSnapshot()

			

			
		# TODO:  test to see if we need this
		# It's possible that a rendering is waiting to be generated if we were waiting for a snapshot to complete.
		#if(self.TimelapseSettings["SnapshotRequestCount"] == 0 and self.TimelapseSettings['IsRendering'] == True):
		#	self.RenderTimelapse()
	def TakeSnapshot(self):
		# Increment the number of outstanding snapshot requests
		self.TimelapseSettings["SnapshotRequestCount"] += 1
		
		snapshot = self.TimelapseSettings['CaptureSnapshot']
		try:
			snapshot.Snap(self.TimelapseSettings['CurrentPrintFileName'],self.TimelapseSettings['SnapshotCount'],onComplete = self.OnSnapshotComplete, onSuccess = self.OnSnapshotSuccess, onFail = self.OnSnapshotFail)
		except:
			a = sys.exc_info() # Info about unknown error that caused exception.                                              
			errorMessage = "    {0}".format(a)
			b = [ str(p) for p in a ]
			errorMessage += "\n    {0}".format(b)
			self.Settings.CurrentDebugProfile().LogError('Unknown error detected:{0}'.format(errorMessage))
		
	def OnSnapshotSuccess(self, *args, **kwargs):
		if(self.TimelapseSettings == None):
			self.Settings.self.Settings.CurrentDebugProfile().LogError("There are no timelapse settings, cannot rename the snapshot!")
			EndSnapshot()
			return
		# Increment the number of snapshots received
		self.TimelapseSettings['SnapshotCount'] += 1
		# get the save path
		snapshotInfo = args[0]
		# get the current file name
		newSnapshotName = snapshotInfo.GetFullPath(self.TimelapseSettings['SnapshotCount'])
		self.Settings.CurrentDebugProfile().LogSnapshotSave("Renaming snapshot {0} to {1}".format(snapshotInfo.GetTempFullPath(),newSnapshotName))
		# create the output directory if it does not exist
		try:
			path = os.path.dirname(newSnapshotName)
			if not os.path.exists(path):
				os.makedirs(path)
		except:
			type = sys.exc_info()[0]
			value = sys.exc_info()[1]
			self.Settings.CurrentDebugProfile().LogWarning("An exception was thrown when trying to create a directory for the downloaded snapshot: {0}  , ExceptionType:{1}, Exception Value:{2}".format(os.path.dirname(dir),type,value))
			return

		# rename the current file
		try:

			shutil.move(snapshotInfo.GetTempFullPath(),newSnapshotName)
		except:
			type = sys.exc_info()[0]
			value = sys.exc_info()[1]
			self.Settings.CurrentDebugProfile().LogError("Could rename the snapshot {0} to {1}!   Error Type:{2}, Details:{3}".format(shapshotInfo.GetTempFullPath(), newSnapshotName,type,value))
	def OnSnapshotFail(self, *args, **kwargs):
		reason = args[0]
		self.LogSnapshotDownload("Failed to download the snapshot.  Reason:{0}".format(reason))
	def OnSnapshotComplete(self, *args, **kwargs):
		self.Settings.CurrentDebugProfile().LogSnapshotDownload("Snapshot Completed.")
		#TODO:  Do we need this anymore?  Maybe not :)
		self.TimelapseSettings["SnapshotRequestCount"] -= 1
		self.SendReturnGcode()
		

	# RENDERING Functions and Events
	def RenderTimelapse(self):
		# make sure we have a non null TimelapseSettings object.  We may have terminated the timelapse for some reason
		if(self.TimelapseSettings is not None):
			self.TimelapseSettings['IsRendering'] = True
			if(not self.TimelapseSettings["SnapshotRequestCount"] == 0):
				self.Settings.CurrentDebugProfile().LogRenderStart("Waiting for {0} download(s) to complete before starting timelapse generation.".format(self.TimelapseSettings["SnapshotRequestCount"]))
			else:
				if(self.TimelapseSettings["Render"].Rendering.enabled):
					self.Settings.CurrentDebugProfile().LogInfo("Started Rendering Timelapse");
					self.TimelapseSettings['Render'].Process(self.TimelapseSettings['CurrentPrintFileName'], self.TimelapseSettings['CaptureSnapshot'].PrintStartTime, self.TimelapseSettings['CaptureSnapshot'].PrintEndTime)
				# in every case reset the timelapse settings.  we want all of the settings to be reset and the current timelapse ended.  The rendering will take place in the background.
				self.TimelapseSettings["IsRendering"] = False
				self.IsPrinting = False
				self.ResetTimelapseSettings();
		else:
			self.Settings.CurrentDebugProfile().LogWarning("The timelapse was terminated before it could be created.")
	def OnRenderStart(self, *args, **kwargs):
		self.Settings.CurrentDebugProfile().LogRenderStart("Started rendering the timelapse.")
		finalFilename = args[0]
		baseFileName = args[1]
		#Notify Octoprint
		payload = dict(gcode="unknown",movie=finalFilename,movie_basename=baseFileName,movie_prefix="from Octolapse")
		eventManager().fire(Events.MOVIE_RENDERING, payload)
	def OnRenderSuccess(self, *args, **kwargs):
		finalFilename = args[0]
		baseFileName = args[1]
		self.Settings.CurrentDebugProfile().LogRenderComplete("Rendering completed successfully.")
	def OnRenderingComplete(self, *args, **kwargs):
		self.Settings.CurrentDebugProfile().LogRenderComplete("Completed rendering, ending timelapse.")
	def OnRenderFail(self, *args, **kwargs):
		self.Settings.CurrentDebugProfile().LogRenderFail("The timelapse rendering failed.")

		#Notify Octoprint
		finalFilename = args[0]
		baseFileName = args[1]
		returnCode = args[2]
		reason = args[3]
		
		payload = dict(gcode="unknown",
				movie=finalFilename,
				movie_basename=baseFileName ,
				returncode=returnCode,
				reason = reason)
		eventManager().fire(Events.MOVIE_FAILED, payload)
	def OnSyncronizeRenderingComplete(self, *args, **kwargs):
		finalFilename = args[0]
		baseFileName = args[1]
		# Notify the user of success and refresh the default timelapse control
		payload = dict(gcode="unknown",
				movie=finalFilename,
				movie_basename=baseFileName ,
				movie_prefix="from Octolapse")
		eventManager().fire(Events.MOVIE_DONE, payload)
	def OnSyncronizeRenderingFail(self, *args, **kwargs):
		finalFilename = args[0]
		baseFileName = args[1]
		# Notify the user of success and refresh the default timelapse control
		payload = dict(gcode="unknown",
				movie=finalFilename,
				movie_basename=baseFileName ,
				movie_prefix="from Octolapse",
				returncode=0,
				reason="See the octolapse log for details.")
		eventManager().fire(Events.MOVIE_FAILED, payload)
	
	##~~ AssetPlugin mixin
	def get_assets(self):
		self._logger.info("Octolapse is loading assets.")
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(
			js = [
				"js/jquery.validate.min.js"
				,"js/octolapse.js"
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

