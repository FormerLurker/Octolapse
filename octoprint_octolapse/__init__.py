# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import uuid
import time
import os
import sys
import json
import threading
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
			'ApplyingCameraSettings': False, # are we trying to adjust the camera?  
			'SendingSnapshotCommands': False, # If true, we are in the process of sending gcode to the printer to take a snapshot
			'RequestingReturnPosition': False, # If true, we have sent a position request to the 3d printer, but haven't yet received a response
			'RequestingSnapshotPosition': False, # If true, we have sent all the gcode necessary to move to the snapshot position and are waiting for a response so that we can take the snapshot.
			
			#Snapshot Gcode
			'PositionGcodes': None, # gcode to retrieve a position from the printer.  Used before creating snapshot gcode
			'SnapshotGcodes': None, # gcode used to move the printer to the snapshot position and to return to the previous position.  Stores index of the snapshot gcode.
			'SavedCommand': None, # The command that triggered the snapshot.  It will be saved and sent after the SnapshotGcodes are sent.
			
			#Snapshot Gcode Execution Tracking
			'SnapshotCommandIndex':  0,
			'PositionCommandIndex': 0,
			'PositionRequestAttempts':0
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
			'SnapshotPositionRetryAttempts' : self.Settings.CurrentSnapshot().position_request_retry_attemps,
			'SnapshotPositionRetryDelayMs' : self.Settings.CurrentSnapshot().position_request_retry_delay_ms,
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

	def StopTimelapse(self):
		self.IsPrinting = False
		if(self.TimelapseSettings is not None):
			self.TimelapseSettings = None
		if(self.SnapshotState is not None):
			self.SnapshotState = None
	## EVENTS
	#########
	def get_settings_defaults(self):
		return dict(load=None)
	
	def on_settings_load(self):
		octoprint.plugin.SettingsPlugin.on_settings_load(self)
		return self.Settings.ToDict()
	
	def get_template_configs(self):
		self._logger.info("Octolapse - is loading template configurations.")
		return [dict(type="settings", custom_bindings=True)]

	def on_after_startup(self):
		self.LoadSettings()
		self.Settings.CurrentDebugProfile().LogInfo("Octolapse - loaded and active.")
		IsStarted = True
	
	# Event Mixin Handler
	def on_event(self, event, payload):
		# If we're not enabled, get outta here!
		if(self.Settings is None or not self.Settings.is_octolapse_enabled):
			return
		self.Settings.CurrentDebugProfile().LogPrintStateChange("Printer event received:{0}.".format(event))
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
			self.Settings.CurrentDebugProfile().LogPrintStateChange("Octolapse - Print Done")
			self.OnPrintCompleted()
		elif (event == Events.SETTINGS_UPDATED):
			self.Settings.CurrentDebugProfile().LogPrintStateChange("Detected settings save, reloading and cleaning settings.")
		elif(event == Events.POSITION_UPDATE and self.SnapshotState is not None):
			
			if(self.SnapshotState['IsPausedByOctolapse'] ):
				self.PositionReceived(payload)
				
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
		# render the timelapse if it's enabled
		self.RenderTimelapse()
		# in every case reset the timelapse settings.  we want all of the settings to be reset and the current timelapse ended.  The rendering will take place in the background.
		self.StopTimelapse();
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

		if(self.TimelapseSettings is not None):
			self.TimelapseSettings['Position'].Update(cmd)
		# Don't do anything further to any commands unless we are taking a timelapse , or if octolapse paused the print.
		#Apply any debug assert commands
		if(self.Settings is not None):
			self.Settings.CurrentDebugProfile().ApplyCommands(cmd, self.TimelapseSettings, self.SnapshotState)
		# return if we're not taking our timelapse
		if(not self.IsTimelapseActive()):
			return None


		# if we have sent an m114 command
		if(self.SnapshotState['IsPausedByOctolapse']):
			
			# suppress any commands we don't, under any cirumstances, to execute while we're taking a snapshot
			if(cmd in ['M105']):
				return None, # suppress the command
			#elif(self.SnapshotState['RequestingReturnPosition']):
			#	# we need to suppress any M114 commands that we haven't sent
			if(self.SnapshotState["SendingSnapshotCommands"]):
				# suppress any commands that aren't within our list commands
				snapshotCommandIndex = self.SnapshotState['SnapshotCommandIndex']
				snapshotGcodes = self.SnapshotState['SnapshotGcodes']
				snapshotCommand = snapshotGcodes.GcodeCommands[snapshotCommandIndex]
				if(cmd not in snapshotGcodes.GcodeCommands):
					self.Settings.CurrentDebugProfile().LogWarning("Snapshot Queue Monitor - The received command {0} is not in our snapshot commands, suppressing.".format(cmd));
					return None , # suppress the command
				# If the command is the snapshot command, set our state variables
				# we have to do this in queuing, or else octoprint will sometimes snag the event before we know it was sent!  Crazy, and difficult to debug
				snapshotIndex = self.SnapshotState['SnapshotGcodes'].SnapshotIndex
				if(cmd == snapshotCommand):
					if(snapshotCommandIndex == snapshotIndex):
						self.Settings.CurrentDebugProfile().LogSnapshotGcodeEndcommand("End snapshot position request gcode command queued.")
					self.SnapshotState['SnapshotCommandIndex'] += 1
					if(snapshotCommandIndex >= snapshotGcodes.EndIndex() and not self.SnapshotState["RequestingSnapshotPosition"]):
						self.Settings.CurrentDebugProfile().LogSnapshotGcodeEndcommand("End Snapshot Return Gcode Command Found, ending the snapshot.")
						self.EndSnapshot()
						
				else:
					self.Settings.CurrentDebugProfile().LogWarning("Snapshot Queue Monitor - The current command index {0} does not equal the snapshot index {1}, or the queuing command {2} does not equal the the snapshot command {3}.".format(snapshotCommandIndex,snapshotIndex, cmd, snapshotCommand))

			return None  # leave the comand alone
		
		currentTrigger = trigger.IsTriggering(self.TimelapseSettings['Triggers'],self.TimelapseSettings['Position'], cmd, self.Settings.CurrentDebugProfile())
		isPrinterSnapshotCommand = trigger.IsSnapshotCommand(cmd,self.Settings.CurrentPrinter().snapshot_command)
		if(currentTrigger is not None): #We're triggering
			# build an array of commands to take the snapshot
			if(not self.SnapshotState['IsPausedByOctolapse']):
				# start a fresh snapshot!				
				self.ResetSnapshotState()
				# we don't want to execute the current command.  We have saved it for later.
				# but we don't want to send the snapshot command to the printer, or any of the SupporessedSavedCommands (gcode.py)
				if(isPrinterSnapshotCommand or cmd in self.Commands.SuppressedSavedCommands):
					self.SnapshotState['SavedCommand'] = None # this will suppress the command since it won't be added to our snapshot commands list
				else:
					self.SnapshotState['SavedCommand'] = cmd; # this will cause the command to be added to the end of our snapshot commands

				# pausing the print after setting these two flags to true will a position request, which will trigger a snapshot
				self.SnapshotState['IsPausedByOctolapse'] = True
				self.SnapshotState['RequestingReturnPosition'] = True
				self._printer.pause_print()
				self.SendPositionRequestGcode(True)
				return None,
		if(isPrinterSnapshotCommand ):
			# in all cases do not return the snapshot command to the printer.  It is NOT a real gcode and could cause errors.
			return None,

		return None
	def GcodeSent(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):

		if(self.IsTimelapseActive()):
			self.Settings.CurrentDebugProfile().LogSentGcode("Sent to printer: Command Type:{0}, gcode:{1}, cmd: {2}".format(cmd_type, gcode, cmd))
		else:
			return
		# Look for the dwell command.  Once we receive it, we should start looking for a snapshot position (m114)!

		if(self.SnapshotState["SendingSnapshotCommands"]):
			
			snapshotGcodes = self.SnapshotState['SnapshotGcodes']
			# make sure this command is in our snapshot gcode list, else ignore
			if(cmd not in snapshotGcodes.GcodeCommands):
				return
			
			# Get the move command index and command 
			snapshotMoveIndex = snapshotGcodes.SnapshotMoveIndex
			moveCommand = snapshotGcodes.GcodeCommands[snapshotMoveIndex]
			if(cmd == moveCommand):
				self.Settings.CurrentDebugProfile().LogSnapshotGcodeEndcommand("Move command sent, looking for snapshot position.")
				# make sure that we set the RequestingSnapshotPosition flag so that the position request we detected will be captured the PositionUpdated event.
				self.SnapshotState['RequestingSnapshotPosition'] = True


	def SendPositionRequestGcode(self, isReturn):
		# Send commands to move to the snapshot position
		if(isReturn):
			self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Gcode sending for snapshot return position (M400, M114).")
			self.SnapshotState['RequestingReturnPosition'] = True
		else:
			self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Gcode sending for snapshot position (M400, M114).")
			self.SnapshotState['RequestingSnapshotPosition'] = True
		self._printer.commands(["M400","M114"]); # we need to manually request it here
		
	def PositionReceived(self, payload):
		isReturn = None
		# octoprint sends a position requests when we pause, which can mess our $H1t up, so ignore it
		if(payload["reason"] == "pause"): # lucky for us there is a reason attached.  I'd LOVE to be able to attach a reason (or any note) to a command and have it returned!
			self.Settings.CurrentDebugProfile().LogPrintStateChange("Ignored position that was originally requested by Octoprint.")
			return
		if(self.SnapshotState['RequestingReturnPosition']):
			# if we are getting the return position, set our snapshot state flag and set isReturn = true
			
			isReturn = True
			self.Settings.CurrentDebugProfile().LogPrintStateChange("Snapshot return position received by Octolapse.")
		elif(self.SnapshotState['RequestingSnapshotPosition']):
			# if we are getting the snapshot position, set our snapshot state flag and set isReturn = false
			
			isReturn = False
			self.Settings.CurrentDebugProfile().LogPrintStateChange("Snapshot position received by Octolapse.")
		else:
			self.Settings.CurrentDebugProfile().LogPrintStateChange("Position received by Octolapse while paused, but was declined.")
			return

		x=payload["x"]
		y=payload["y"]
		z=payload["z"]
		e=payload["e"]
		previousX = self.TimelapseSettings['Position'].XPrevious
		previousY = self.TimelapseSettings['Position'].YPrevious
		previousZ = self.TimelapseSettings['Position'].ZPrevious
		
		
		
		if(isReturn):
			#todo:  Do we need to re-request the position like we do for the return?  Maybe...
			printerTolerance = self.TimelapseSettings["Printer"].printer_position_confirmation_tolerance
			if( not 
			(previousX is None or utility.isclose(previousX, x,abs_tol=printerTolerance))
			and (previousY is None or utility.isclose(previousY, y,abs_tol=printerTolerance))
			and (previousZ is None or utility.isclose(previousZ, z,abs_tol=printerTolerance))
			):
				self.Settings.CurrentDebugProfile().LogWarning("The snapshot return position recieved from the printer does not match the position expected by Octolapse.  received (x:{0},y:{1},z:{2}), Expected (x:{3},y:{4},z:{5})".format(x,y,z,previousX,previousY,previousZ))
				# return position information received
				self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Snapshot return position received - x:{0},y:{1},z:{2},e:{3}".format(x,y,z,e))

			# make sure the SnapshotCommandIndex = 0
			# Todo: ensure this is unnecessary
			self.SnapshotState['SnapshotCommandIndex']=0
			# create the GCode for the timelapse and store it
			isRelative = self.TimelapseSettings['Position'].IsRelative
			isExtruderRelative = self.TimelapseSettings['Position'].IsExtruderRelative()
			extruder = self.TimelapseSettings['Position'].Extruder
			self.SnapshotState['SnapshotGcodes'] = self.TimelapseSettings['OctolapseGcode'].CreateSnapshotGcode(x,y,z,isRelative, isExtruderRelative, extruder,savedCommand=self.SnapshotState['SavedCommand'])
			# make sure we acutally received gcode
			if(self.SnapshotState['SnapshotGcodes'] is None):
				self.Settings.CurrentDebugProfile().LogError("No snapshot gcode was created for this snapshot.  Aborting this snapshot.")
				self.AbortSnapshot("No Snapshot Gcode was Generated")
				return;

			self.SnapshotState['RequestingReturnPosition'] = False
			self.SnapshotState['SendingSnapshotCommands'] = True
			# send our commands to the printer
			self._printer.commands(self.SnapshotState['SnapshotGcodes'].SnapshotCommands());
		else:
			# snapshot position information received
			snapshotGcodes = self.SnapshotState['SnapshotGcodes']
			self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Snapshot position received, checking position:  Received: x:{0},y:{1},z:{2},e:{3}, Expected: x:{4},y:{5}".format(x,y,z,e,snapshotGcodes.X,snapshotGcodes.Y))

			printerTolerance = self.TimelapseSettings["Printer"].printer_position_confirmation_tolerance
			if((utility.isclose(snapshotGcodes.X, x,abs_tol=printerTolerance))
				and (utility.isclose( snapshotGcodes.Y, y,abs_tol=printerTolerance))
			):
				self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("The snapshot position is correct, taking snapshot.")
				self.SnapshotState['RequestingSnapshotPosition'] = False
				self.TakeSnapshot()
			else:
				self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("The snapshot position is incorrect.")
				self.ResendSnapshotPositionRequest()
				
	def ResendSnapshotPositionRequest(self):

		# rety 20 times with a .25 second delay between attempts
		maxRetryAttempts = self.TimelapseSettings['SnapshotPositionRetryAttempts']
		reRequestDelaySeconds = self.TimelapseSettings['SnapshotPositionRetryDelayMs'] / 1000.0
		self.SnapshotState['PositionRequestAttempts'] += 1
		# todo:  make the retry attempts a setting, as well as the request delay
		
		if(self.SnapshotState['PositionRequestAttempts'] > maxRetryAttempts):
			self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("The maximum number of position discovery attempts ({0}) has been reached for this snapshot.  Aborting this snapshot.".format(maxRetryAttempts))
			# we're giving up and no longer requesting a snapshot position.
			self.SnapshotState['RequestingSnapshotPosition'] = False
			self.SendSnapshotReturnCommands()
			return 

		self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Re-requesting our present location with a delay of {0} seconds. Try number {1} of {2}".format(reRequestDelaySeconds,  self.SnapshotState['PositionRequestAttempts'], maxRetryAttempts))
		t = threading.Timer( reRequestDelaySeconds, self.SendPositionRequestGcode, [False])
		t.start()

	
	def AbortSnapshot(self, message):
		"""Stops the current snapshot, but continues.  Eventually this will display a user notification"""
		# Todo:  Display a message for the user
		
		# End the current snapshot
		self.EndSnapshot()

	def EndSnapshot(self):
		# Cleans up the variables and resumes the print once the snapshot is finished, and the extruder is in the proper position 
		
		# reset the snapshot variables
		self.ResetSnapshotState();
		# if the print is paused, resume!
		if(self._printer.is_paused()):
			self.Settings.CurrentDebugProfile().LogSnapshotDownload("Resuming Print.")
			self._printer.resume_print()
		
	def TakeSnapshot(self):
		# Increment the number of outstanding snapshot requests
		self.TimelapseSettings["SnapshotRequestCount"] += 1
		
		snapshot = self.TimelapseSettings['CaptureSnapshot']
		self.Settings.CurrentDebugProfile().LogSnapshotDownload("Taking Snapshot.")
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
			self.EndSnapshot()
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
		self.SendSnapshotReturnCommands()

	def SendSnapshotReturnCommands(self):
		self.Settings.CurrentDebugProfile().LogSnapshotDownload("Sending Snapshot Return Commands.")
		self._printer.commands(self.SnapshotState['SnapshotGcodes'].ReturnCommands());
		
	# RENDERING Functions and Events
	def RenderTimelapse(self):
		# make sure we have a non null TimelapseSettings object.  We may have terminated the timelapse for some reason
		if(self.TimelapseSettings is not None):
			self.TimelapseSettings['IsRendering'] = True
			if(self.TimelapseSettings["Render"].Rendering.enabled):
				self.Settings.CurrentDebugProfile().LogInfo("Started Rendering Timelapse");
				self.TimelapseSettings['Render'].Process(self.TimelapseSettings['CurrentPrintFileName'], self.TimelapseSettings['CaptureSnapshot'].PrintStartTime, self.TimelapseSettings['CaptureSnapshot'].PrintEndTime)
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
		"octoprint.comm.protocol.gcode.sent": __plugin_implementation__.GcodeSent
	}

