# coding=utf-8
import time
import shutil
import os
import threading

from octoprint_octolapse.trigger import GcodeTrigger, TimerTrigger, LayerTrigger, Triggers
from octoprint_octolapse.snapshot import CaptureSnapshot,SnapshotInfo
from octoprint_octolapse.settings import OctolapseSettings, Printer, Stabilization, Camera, Rendering, Snapshot, DebugProfile
from octoprint_octolapse.render import Render
from octoprint_octolapse.gcode import SnapshotGcodeGenerator, SnapshotGcode
from octoprint_octolapse.command import *
from octoprint_octolapse.position import Position
import octoprint_octolapse.utility as utility

class Timelapse(object):
	
	def __init__(self,octolapseSettings, dataFolder, timelapseFolder
			  , onSnapshotStart = None
			  , onSnapshotEnd = None
			  , onRenderStart = None
			  , onRenderComplete = None
			  , onRenderFail = None
			  , onRenderSynchronizeFail = None
			  , onRenderSynchronizeComplete = None
			  , onRenderEnd = None
			  , onTimelapseStopping = None
			  , onTimelapseStopped = None
			  , onStateChanged = None
			  , onTimelapseStart = None):
		# config variables - These don't change even after a reset
		self.Settings = octolapseSettings
		self.DataFolder = dataFolder
		self.DefaultTimelapseDirectory =  timelapseFolder
		self.OnRenderStartCallback = onRenderStart
		self.OnRenderCompleteCallback = onRenderComplete
		self.OnRenderFailCallback = onRenderFail
		self.OnRenderingSynchronizeFailCallback = onRenderSynchronizeFail
		self.OnRenderingSynchronizeCompleteCallback = onRenderSynchronizeComplete
		self.OnRenderEndCallback = onRenderEnd
		self.OnSnapshotStartCallback = onSnapshotStart
		self.OnSnapshotCompleteCallback = onSnapshotEnd
		self.TimelapseStoppingCallback = onTimelapseStopping
		self.TimelapseStoppedCallback = onTimelapseStopped
		self.OnStateChangedCallback = onStateChanged
		self.OnTimelapseStartCallback = onTimelapseStart
		self.Responses = Responses() # Used to decode responses from the 3d printer
		self.Commands = Commands() # used to parse and generate gcode
		self.Triggers = Triggers(octolapseSettings)
		# Settings that may be different after StartTimelapse is called
		self.FfMpegPath = None
		self.Snapshot = None
		self.Gcode = None
		self.Printer = None
		self.CaptureSnapshot = None
		self.Position = None
		self.HasSentInitialStatus = False
		# State Tracking that should only be reset when starting a timelapse
		self.IsRendering = False
		self.HasBeenCancelled = False
		self.HasBeenStopped = False
		# State tracking variables
		self._reset()

	# public functions		
	def StartTimelapse(self,octoprintPrinter, octoprintPrinterProfile, ffmpegPath,g90InfluencesExtruder):
		self._reset()
		self.HasSentInitialStatus = False
		self.OctoprintPrinter = octoprintPrinter
		self.OctoprintPrinterProfile = octoprintPrinterProfile
		self.FfMpegPath = ffmpegPath
		self.PrintStartTime=time.time()
		self.Snapshot = Snapshot(self.Settings.CurrentSnapshot())
		self.Gcode = SnapshotGcodeGenerator(self.Settings,octoprintPrinterProfile)
		self.Printer = Printer(self.Settings.CurrentPrinter())
		self.Rendering = Rendering(self.Settings.CurrentRendering())
		self.CaptureSnapshot = CaptureSnapshot(self.Settings,  self.DataFolder, printStartTime=self.PrintStartTime)
		self.Position = Position(self.Settings,octoprintPrinterProfile, g90InfluencesExtruder)
		self.State = TimelapseState.WaitingForTrigger
		self.IsTestMode = self.Settings.CurrentDebugProfile().is_test_mode
		self.Triggers.Create()
		# send an initial state message
		self._onTimelapseStart()

	def GetStateDict(self):
		try:

			positionDict = None
			positionStateDict = None
			extruderDict = None
			triggerState = None

			if(self.Settings.show_position_changes and self.Position is not None):
				positionDict=self.Position.ToPositionDict()
			if(self.Settings.show_position_state_changes and self.Position is not None):
				positionStateDict = self.Position.ToStateDict()
			if(self.Settings.show_extruder_state_changes and self.Position is not None):
				extruderDict = self.Position.Extruder.ToDict()
			if(self.Settings.show_trigger_state_changes):
				triggerState = {
				   "Name": self.Triggers.Name,
				   "Triggers": self.Triggers.StateToList()
				   }
			stateDict = {
						"Extruder": extruderDict,
						"Position": positionDict,
						"PositionState": positionStateDict,
						"TriggerState": triggerState
						}
			return stateDict
		except Exception as e:
			self.Settings.CurrentDebugProfile().LogException(e)
		# if we're here, we've reached and logged an error.
		return  {
			"Extruder": None,
			"Position": None,
			"PositionState": None,
			"TriggerState": None
		}
		
	def StopSnapshots(self):
		"""Stops octolapse from taking any further snapshots.  Any existing snapshots will render after the print is ends."""
		# we don't need to end the timelapse if it hasn't started
		if(self.State == TimelapseState.WaitingForTrigger or self.TimelapseStopRequested):
			self.State = TimelapseState.WaitingToRender
			self.TimelapseStopRequested = False
			if(self.TimelapseStoppedCallback is not None):
				self.TimelapseStoppedCallback()
			return True
		
		# if we are here, we're delaying the request until after the snapshot
		self.TimelapseStopRequested = True
		if(self.TimelapseStoppingCallback is not None):
			self.TimelapseStoppingCallback()
	def EndTimelapse(self, cancelled = False, force = False):
		try:
			if(not self.State == TimelapseState.Idle):
				if(not force):
					if(self.State > TimelapseState.WaitingForTrigger and self.State < TimelapseState.WaitingToRender):
						if(cancelled):
							self.HasBeenCancelled = True;
						else:
							self.HasBeenStopped = True;
						return
				self._renderTimelapse()
				self._reset();
			else:
				self.Settings.CurrentDebugProfile().LogError("timelapse.py - An EndTimelapse request was made, but the timelapse was idling!")
		except Exception as e:
			self.Settings.CurrentDebugProfile().LogException(e)
	def PrintPaused(self):
		try:
			if(self.State == TimelapseState.Idle):
				return
			elif(self.State < TimelapseState.WaitingToRender):
				self.Settings.CurrentDebugProfile().LogPrintStateChange("Print Paused.")
				self.Triggers.Pause()
		except Exception as e:
			self.Settings.CurrentDebugProfile().LogException(e)
	def PrintResumed(self):
		try:
			if(self.State == TimelapseState.Idle):
				return
			elif(self.State < TimelapseState.WaitingToRender):
				self.Triggers.Resume()
		except Exception as e:
			self.Settings.CurrentDebugProfile().LogException(e)
	def IsTimelapseActive(self):
		try:
			if(
				self.State == TimelapseState.Idle
				or self.State == TimelapseState.WaitingToRender
				or self.Triggers.Count()<1
			):
				return False
			return True
		except Exception as e:
			self.Settings.CurrentDebugProfile().LogException(e)
		return False
	def GcodeQueuing(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		try:
			self.Settings.CurrentDebugProfile().LogQueuingGcode("Queuing Command: Command Type:{0}, gcode:{1}, cmd: {2}".format(cmd_type, gcode, cmd))
			# update the position tracker so that we know where all of the axis are.
			# We will need this later when generating snapshot gcode so that we can return to the previous
			# position
			cmd = cmd.upper().strip()
			# create our state change dictionaries
			positionChangeDict = None
			positionStateChangeDict = None
			extruderChangeDict = None
			triggerChangeList = None
			self.Position.Update(cmd)
			# capture any changes, if neccessary, to the position, position state and extruder state
			# Note:  We'll get the trigger state later
			if(self.Settings.show_position_changes and (self.Position.HasPositionChanged() or  not self.HasSentInitialStatus)):
				positionChangeDict = self.Position.ToPositionDict();
			if(self.Settings.show_position_state_changes and (self.Position.HasStateChanged()or  not self.HasSentInitialStatus)):
				positionStateChangeDict = self.Position.ToStateDict();
			if(self.Settings.show_extruder_state_changes and (self.Position.Extruder.HasChanged()or  not self.HasSentInitialStatus)):
				extruderChangeDict = self.Position.Extruder.ToDict();
			# get the position state in case it has changed
			# if there has been a position or extruder state change, inform any listener
			isSnapshotGcodeCommand = self._isSnapshotCommand(cmd)

			if(self.State == TimelapseState.WaitingForTrigger and self.OctoprintPrinter.is_printing()):
				self.Triggers.Update(self.Position,cmd)

				# If our triggers have changed, update our dict
				if(self.Settings.show_trigger_state_changes and self.Triggers.HasChanged()):
					triggerChangeList = self.Triggers.ChangesToList()
					

				if(self.GcodeQueuing_IsTriggering(cmd,isSnapshotGcodeCommand)):
					# Undo the last position update, we're not going to be using it!
					self.Position.UndoUpdate()
					# Store the current position (our previous position), since this will be our snapshot position
					self.Position.SavePosition()
					# we don't want to execute the current command.  We have saved it for later.
					# but we don't want to send the snapshot command to the printer, or any of the SupporessedSavedCommands (gcode.py)
					if(isSnapshotGcodeCommand or cmd in self.Commands.SuppressedSavedCommands):
						self.SavedCommand = None # this will suppress the command since it won't be added to our snapshot commands list
					else:
						if(self.IsTestMode):
							cmd = self.Commands.GetTestModeCommandString(cmd)
						self.SavedCommand = cmd; # this will cause the command to be added to the end of our snapshot commands
					# pause the printer to start the snapshot
					self.State = TimelapseState.RequestingReturnPosition
					
					# Pausing the print here will immediately trigger an M400 and a location request
					self._pausePrint() # send M400 and position request
					# send a notification to the client that the snapshot is starting
					if(self.OnSnapshotStartCallback is not None):
						self.OnSnapshotStartCallback()
					# suppress the command
					cmd = None,
				
			elif(self.State > TimelapseState.WaitingForTrigger and self.State < TimelapseState.SendingReturnGcode):
				# Don't do anything further to any commands unless we are taking a timelapse , or if octolapse paused the print.	
				# suppress any commands we don't, under any cirumstances, to execute while we're taking a snapshot
				if(cmd in self.Commands.SuppressedSnapshotGcodeCommands):
					cmd = None, # suppress the command

			if(isSnapshotGcodeCommand ):
				# in all cases do not return the snapshot command to the printer.  It is NOT a real gcode and could cause errors.
				cmd = None,

			# notify any callbacks
			self._onStateChanged(positionChangeDict,positionStateChangeDict,extruderChangeDict,triggerChangeList)
			self.HasSentInitialStatus = True
		
			if (cmd != None,):
				return self._returnGcodeCommandToOctoprint(cmd)
			# if we are here we need to suppress the command
		except Exception as e:
			self.Settings.CurrentDebugProfile().LogException(e)
			raise

		return cmd
	def GcodeQueuing_IsTriggering(self,cmd,isSnapshotGcodeCommand):
		try:
			# make sure we're in a state that could want to check for triggers
			if(not self.State == TimelapseState.WaitingForTrigger):
				return None
		
			currentTrigger = self.Triggers.GetFirstTriggering(0)

			if(currentTrigger is not None):#We're triggering
				self.Settings.CurrentDebugProfile().LogTriggering("A snapshot is triggering")
				# notify any callbacks
				return True
			elif (self._isTriggerWaiting(cmd)):
				self.Settings.CurrentDebugProfile().LogTriggerWaitState("Trigger is Waiting On Extruder.")
		except Exception as e:
			self.Settings.CurrentDebugProfile().LogException(e)
			# no need to re-raise here, the trigger just won't happen
		return False
	def GcodeSent(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		self.Settings.CurrentDebugProfile().LogSentGcode("Sent to printer: Command Type:{0}, gcode:{1}, cmd: {2}".format(cmd_type, gcode, cmd))
	def PositionReceived(self, payload):
		# if we cancelled the print, we don't want to do anything.
		if(self.HasBeenCancelled):
			self.EndTimelapse(force = True)
			return;
		
		x=payload["x"]
		y=payload["y"]
		z=payload["z"]
		e=payload["e"]
		if(self.State == TimelapseState.RequestingReturnPosition):
			self.Settings.CurrentDebugProfile().LogPrintStateChange("Snapshot return position received by Octolapse.")
			self._positionReceived_Return(x,y,z,e)
		elif(self.State == TimelapseState.SendingSnapshotGcode):
			self.Settings.CurrentDebugProfile().LogPrintStateChange("Snapshot position received by Octolapse.")
			self._positionReceived_Snapshot(x,y,z,e)
		elif(self.State == TimelapseState.SendingReturnGcode):
			self._positionReceived_ResumePrint(x,y,z,e)
		else:
			self.Settings.CurrentDebugProfile().LogPrintStateChange("Position received by Octolapse while paused, but was declined.")
			return False, "Declined - Incorrect State"

	# internal functions
	####################
	def _returnGcodeCommandToOctoprint(self, cmd):

		if(cmd is None or cmd == (None,)):
			return cmd

		if(self.IsTestMode and self.State >= TimelapseState.WaitingForTrigger):
			return self.Commands.AlterCommandForTestMode(cmd)
		# if we were given a list, return it.
		if(isinstance(cmd,list)):
			return cmd
		# if we were given a command return None (don't change the command at all)
		return None
	def _onStateChanged(self,positionChangeDict,positionStateChangeDict, extruderChangeDict,triggerChangeList):
		"""Notifies any callbacks about any changes contained in the dictionaries.
		If you send a dict here the client will get a message, so check the
		settings to see if they are subscribed to notifications before populating the dictinaries!"""
		triggerChangesDict = None
		try:
			
			# Notify any callbacks
			if(self.OnStateChangedCallback is not None
				and
				(
					positionChangeDict is not None
					or positionStateChangeDict is not None
					or extruderChangeDict is not None
					or triggerChangeList is not None
				)):
				if(triggerChangeList is not None and len(triggerChangeList) > 0):
					triggerChangesDict = {
							"Name": self.Triggers.Name,
							"Triggers": triggerChangeList
						}
				changeDict = {
					"Extruder": extruderChangeDict,
					"Position": positionChangeDict,
					"PositionState": positionStateChangeDict,
					"TriggerState": triggerChangesDict
					}

				if(changeDict["Extruder"] is not None
					or changeDict["Position"] is not None
					or changeDict["PositionState"] is not None
					or changeDict["TriggerState"] is not None):
					self.OnStateChangedCallback(changeDict)
		except Exception as e:
			# no need to re-raise, callbacks won't be notified, however.
			self.Settings.CurrentDebugProfile().LogException(e)
	def _isSnapshotCommand(self, command):
		commandName = GetGcodeFromString(command)
		snapshotCommandName = GetGcodeFromString(self.Printer.snapshot_command)
		return commandName == snapshotCommandName
	def _isTriggerWaiting(self,cmd):
		# make sure we're in a state that could want to check for triggers
		if(not self.State == TimelapseState.WaitingForTrigger):
			return None
		isWaiting = False;
		# Loop through all of the active currentTriggers
		waitingTrigger = self.Triggers.GetFirstWaiting()
		if(waitingTrigger is not None):
			return True
		return False
	def _positionReceived_Return(self, x,y,z,e):
		try:

			self.ReturnPositionReceivedTime = time.time()
			#todo:  Do we need to re-request the position like we do for the return?  Maybe...
			printerTolerance = self.Printer.printer_position_confirmation_tolerance
			# If we are requesting a return position we have NOT yet executed the command that triggered the snapshot.
			# Because of this we need to compare the position we received to the previous position, not the current one.
			if( not self.Position.IsAtSavedPosition(x,y,z) ):
				self.Settings.CurrentDebugProfile().LogWarning("The snapshot return position recieved from the printer does not match the position expected by Octolapse.  received (x:{0},y:{1},z:{2}), Expected (x:{3},y:{4},z:{5})".format(x,y,z,self.Position.X(),self.Position.Y(),self.Position.Z()))
				self.Position.UpdatePosition(x=x,y=y,z=z,force=True)
			else:
				# return position information received
				self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Snapshot return position received - x:{0},y:{1},z:{2},e:{3}".format(x,y,z,e))
			# make sure the SnapshotCommandIndex = 0
			# Todo: ensure this is unnecessary
			self.CommandIndex=0

			# create the GCode for the timelapse and store it
			isRelative = self.Position.IsRelative()
			isExtruderRelative = self.Position.IsExtruderRelative()

			self.SnapshotGcodes = self.Gcode.CreateSnapshotGcode(x,y,z, self.Position.F(), self.Position.IsRelative(), self.Position.IsExtruderRelative(), self.Position.Extruder, self.Position.DistanceToZLift(), savedCommand=self.SavedCommand)
			# make sure we acutally received gcode
			if(self.SnapshotGcodes is None):
				self.Settings.CurrentDebugProfile().LogSnapshotGcode("No snapshot gcode was created for this snapshot.  Aborting this snapshot.")
				self._resetSnapshot();
				return False, "Error - No Snapshot Gcode";

			self.State = TimelapseState.SendingSnapshotGcode

			snapshotCommands = self.SnapshotGcodes.SnapshotCommands()

			# send our commands to the printer
			# these commands will go through queuing, no reason to track position
			self.OctoprintPrinter.commands(snapshotCommands)
		except Exception as e:
			self.Settings.CurrentDebugProfile().LogException(e)
			# we need to abandon the snapshot completely, reset and resume
			self._resetSnapshot()
			self._resumePrint()
	def _positionReceived_Snapshot(self, x,y,z,e):
		try:
			# snapshot position information received
			self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Snapshot position received, checking position:  Received: x:{0},y:{1},z:{2},e:{3}, Expected: x:{4},y:{5},z:{6}".format(x,y,z,e,self.Position.X(),self.Position.Y(), self.Position.Z()))
			printerTolerance = self.Printer.printer_position_confirmation_tolerance
			# see if the CURRENT position is the same as the position we received from the printer
			# AND that it is equal to the snapshot position
			if(not self.Position.IsAtCurrentPosition(x,y,None)):
				self.Settings.CurrentDebugProfile().LogWarning("The snapshot position is incorrect.  Received: x:{0},y:{1},z:{2},e:{3}, Expected: x:{4},y:{5},z:{6}".format(x,y,z,e,self.Position.X(),self.Position.Y(), self.Position.Z()))
			elif(not self.Position.IsAtCurrentPosition(self.SnapshotGcodes.X,self.SnapshotGcodes.Y,None, applyOffset = False)): # our snapshot gcode will NOT be offset
				self.Settings.CurrentDebugProfile().LogError("The snapshot gcode position is incorrect.  x:{0},y:{1},z:{2},e:{3}, Expected: x:{4},y:{5},z:{6}".format(x,y,z,e,self.SnapshotGcodes.X,self.SnapshotGcodes.Y, self.Position.Z()))

			self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("The snapshot position is correct, taking snapshot.")
			self.State = TimelapseState.TakingSnapshot
			self._takeSnapshot()
		except Exception as e:
			self.Settings.CurrentDebugProfile().LogException(e)
			# our best bet of fixing things up here is just to return to the previous position.
			self._sendReturnCommands()
	def _positionReceived_ResumePrint(self, x,y,z,e):
		try:
			if(not self.Position.IsAtCurrentPosition(x,y,None)):
				self.Settings.CurrentDebugProfile().LogError("Save Command Position is incorrect.  Received: x:{0},y:{1},z:{2},e:{3}, Expected: x:{4},y:{5},z:{6}".format(x,y,z,e,self.Position.X(),self.Position.Y(), self.Position.Z()))
			else:
				self.Settings.CurrentDebugProfile().LogSnapshotPositionResumePrint("Save Command Position is correct.  Received: x:{0},y:{1},z:{2},e:{3}, Expected: x:{4},y:{5},z:{6}".format(x,y,z,e,self.Position.X(),self.Position.Y(), self.Position.Z()))

			self.SecondsAddedByOctolapse += time.time() - self.ReturnPositionReceivedTime

			# before resetting the snapshot, see if it was a success
			snapshotSuccess = self.SnapshotSuccess
			snapshotError = self.SnapshotError
			# end the snapshot
			self._resetSnapshot()

			# If we've requested that the timelapse stop, stop it now
			if(self.TimelapseStopRequested):
				self.StopSnapshots()
		except Exception as e:
			self.Settings.CurrentDebugProfile().LogException(e)
			# do not re-raise, we are better off trying to resume the print here.
		self._resumePrint()
		self._onTriggerSnapshotComplete(snapshotSuccess, snapshotError)
	def _onTriggerSnapshotComplete(self, snapshotSuccess, snapshotError=""):
		if(self.OnSnapshotCompleteCallback is not None):
			payload = {
					"success": snapshotSuccess,
					"error" : snapshotError,
					"snapshot_count" : self.SnapshotCount,
					"seconds_added_by_octolapse" : self.SecondsAddedByOctolapse
				}
			self.OnSnapshotCompleteCallback(payload)
	def _pausePrint(self):
		self.OctoprintPrinter.pause_print()
	def _resumePrint(self):
		self.OctoprintPrinter.resume_print()
		if(self.HasBeenStopped or self.HasBeenCancelled):
			self.EndTimelapse(force = True)
	def _takeSnapshot(self):
		self.Settings.CurrentDebugProfile().LogSnapshotDownload("Taking Snapshot.")
		try:
			self.CaptureSnapshot.Snap(utility.CurrentlyPrintingFileName(self.OctoprintPrinter),self.SnapshotCount,onComplete = self._onSnapshotComplete, onSuccess = self._onSnapshotSuccess, onFail = self._onSnapshotFail)
		except Exception as e:
			self.Settings.CurrentDebugProfile().LogException(e)
			# try to recover by sending the return command
			self._sendReturnCommands()
	def _onSnapshotSuccess(self, *args, **kwargs):
		# Increment the number of snapshots received
		self.SnapshotCount += 1
		# get the save path
		snapshotInfo = args[0]
		# get the current file name
		newSnapshotName = snapshotInfo.GetFullPath(self.SnapshotCount)
		self.Settings.CurrentDebugProfile().LogSnapshotSave("Renaming snapshot {0} to {1}".format(snapshotInfo.GetTempFullPath(),newSnapshotName))
		# create the output directory if it does not exist
		try:
			tempSnapshotPath = os.path.dirname(newSnapshotName)
			latestSnapshotPath = utility.GetSnapshotDirectory(self.DataFolder)
			if not os.path.exists(tempSnapshotPath):
				os.makedirs(tempSnapshotPath)
			if not os.path.exists(latestSnapshotPath):
				os.makedirs(latestSnapshotPath)
		except Exception as e:
			self.Settings.CurrentDebugProfile().LogException(e)
			return
		try:
			
			# rename the current file
			shutil.move(snapshotInfo.GetTempFullPath(),newSnapshotName)
			self.SnapshotSuccess = True
		except:
			type = sys.exc_info()[0]
			value = sys.exc_info()[1]
			message = "Could rename the snapshot {0} to {1}!   Error Type:{2}, Details:{3}".format(snapshotInfo.GetTempFullPath(), newSnapshotName,type,value)
			self.Settings.CurrentDebugProfile().LogSnapshotSave(message)
			self.SnapshotSuccess = False
			self.SnapshotError = message
	def _onSnapshotFail(self, *args, **kwargs):
		reason = args[0]
		message = "Failed to download the snapshot.  Reason:{0}".format(reason)
		self.Settings.CurrentDebugProfile().LogSnapshotDownload(message)
		self.SnapshotSuccess = False
		self.SnapshotError = message
	def _onSnapshotComplete(self, *args, **kwargs):
		self.Settings.CurrentDebugProfile().LogSnapshotDownload("Snapshot Completed.")
		self._sendReturnCommands()
	def _sendReturnCommands(self):
		try:
			# if the print has been cancelled, quit now.
			if(self.HasBeenCancelled):
				self.EndTimelapse(force = True)
				return;
			# Expand the current command to include the return commands
			if(self.SnapshotGcodes is None):
				self.Settings.CurrentDebugProfile().LogError("The snapshot gcode generator has no value.")
				self.EndTimelapse(force = True)
				return;
			returnCommands = self.SnapshotGcodes.ReturnCommands()
			if(returnCommands is None):
				self.Settings.CurrentDebugProfile().LogError("No return commands were generated!")
				## How do we handle this?  we probably need to cancel the print or something....
				# Todo:  What to do if no return commands are generated?  We should never let this happen.  Make sure this is true.
				self.EndTimelapse(force = True)
				return;

			# set the state so that the final received position will trigger a resume.
			self.State = TimelapseState.SendingReturnGcode
			# these commands will go through queuing, no need to update the position
			self.OctoprintPrinter.commands(returnCommands)
		except Exception as e:
			self.Settings.CurrentDebugProfile().LogException(e)
			# need to re-raise, can't fix this here, but at least it will be logged
			# properly
			raise
	def _renderTimelapse(self):
		# make sure we have a non null TimelapseSettings object.  We may have terminated the timelapse for some reason
		if(self.Rendering.enabled):
			self.Settings.CurrentDebugProfile().LogRenderStart("Started Rendering Timelapse");
			# we are rendering, set the state before starting the rendering job.
			
			self.IsRendering = True
			timelapseRenderJob = Render(self.Settings
									,self.Snapshot
									,self.Rendering
								  ,self.DataFolder
								  ,self.DefaultTimelapseDirectory
								  ,self.FfMpegPath
								  ,1
								  ,timeAdded = self.SecondsAddedByOctolapse
								  ,onRenderStart = self._onRenderStart
								  ,onRenderFail=self._onRenderFail
								  ,onRenderSuccess = self._onRenderSuccess
								  ,onRenderComplete = self._onRenderComplete
								  ,onAfterSyncFail = self._onSynchronizeRenderingFail
								  ,onAfterSycnSuccess = self._onSynchronizeRenderingComplete
								  ,onComplete = self._onRenderEnd)
			timelapseRenderJob.Process(utility.CurrentlyPrintingFileName(self.OctoprintPrinter), self.PrintStartTime, time.time())
			
			return True
		return False
	def _onRenderStart(self, *args, **kwargs):
		self.Settings.CurrentDebugProfile().LogRenderStart("Started rendering/synchronizing the timelapse.")
		finalFilename = args[0]
		baseFileName = args[1]
		willSync = args[2]
		snapshotCount = args[3]
		snapshotTimeSeconds = args[4]
		
		payload = dict(
			FinalFileName = finalFilename
			, WillSync = willSync
			, SnapshotCount = snapshotCount
			, SnapshotTimeSeconds = snapshotTimeSeconds)
		# notify the caller
		if(self.OnRenderStartCallback is not None):
			self.OnRenderStartCallback(payload)
	def _onRenderFail(self, *args, **kwargs):
		self.IsRendering = False
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

		if(self.OnRenderFailCallback is not None):
			self.OnRenderFailCallback(payload)
	def _onRenderSuccess(self, *args, **kwargs):
		self.IsRendering = False
		finalFilename = args[0]
		baseFileName = args[1]
		#TODO:  Notify the user that the rendering is completed if we are not synchronizing with octoprint
		self.Settings.CurrentDebugProfile().LogRenderComplete("Rendering completed successfully.")
	def _onRenderComplete(self, *args, **kwargs):
		finalFileName = args[0]
		synchronize = args[1]
		self.Settings.CurrentDebugProfile().LogRenderComplete("Completed rendering the timelapse.")
		if(self.OnRenderCompleteCallback is not None):
			self.OnRenderCompleteCallback();
	def _onSynchronizeRenderingFail(self, *args, **kwargs):
		finalFilename = args[0]
		baseFileName = args[1]
		# Notify the user of success and refresh the default timelapse control
		payload = dict(gcode="unknown",
				movie=finalFilename,
				movie_basename=baseFileName ,
				reason="Error copying the rendering to the Octoprint timelapse folder.  If logging is enabled you can search for 'Synchronization Error' to find the error.  Your timelapse is likely within the octolapse data folder.")

		if(self.OnRenderingSynchronizeFailCallback is not None):
			self.OnRenderingSynchronizeFailCallback(payload)
	def _onSynchronizeRenderingComplete(self, *args, **kwargs):
		finalFilename = args[0]
		baseFileName = args[1]
		# Notify the user of success and refresh the default timelapse control
		payload = dict(gcode="unknown",
				movie=finalFilename,
				movie_basename=baseFileName ,
				movie_prefix="from Octolapse.  Your timelapse has been synchronized and is now available within the default timelapse plugin tab.",
				returncode=0,
				reason="See the octolapse log for details.")
		if(self.OnRenderingSynchronizeCompleteCallback is not None):
			self.OnRenderingSynchronizeCompleteCallback(payload)
	def _onRenderEnd(self, *args, **kwargs):
		self.IsRendering = False

		finalFileName = args[0]
		baseFileName = args[1]
		synchronize = args[2]
		success = args[3]
		self.Settings.CurrentDebugProfile().LogRenderComplete("Completed rendering.")
		moviePrefix = "from Octolapse"
		if(not synchronize):
			moviePrefix = "from Octolapse.  Your timelapse was NOT synchronized (see advanced rendering settings for details), but can be found in octolapse's data directory.  A file browser will be added in a future release (hopefully)"
		payload = dict(movie=finalFileName,
				movie_basename=baseFileName ,
				movie_prefix=moviePrefix,
				success=success)
		if(self.OnRenderEndCallback is not None):
			self.OnRenderEndCallback(payload)
	def _onTimelapseStart(self):
		if(self.OnTimelapseStartCallback is None):
			return
		self.OnTimelapseStartCallback()
	def _reset(self):
		self.State = TimelapseState.Idle
		self.HasSentInitialStatus = False
		self.Triggers.Reset()
		self.CommandIndex = -1
		self.SnapshotCount = 0
		self.PrintStartTime = None
		self.SnapshotGcodes = None
		self.SavedCommand = None
		self.PositionRequestAttempts = 0
		self.IsTestMode = False
		# time tracking - how much time did we add to the print?
		self.SecondsAddedByOctolapse = 0
		self.ReturnPositionReceivedTime = None
		# A list of callbacks who want to be informed when a timelapse ends
		self.TimelapseStopRequested = False
		self.SnapshotSuccess = False
		self.SnapshotError = ""
		self.HasBeenCancelled = False
		self.HasBeenStopped = False
	def _resetSnapshot(self):
		self.State = TimelapseState.WaitingForTrigger
		self.CommandIndex = -1
		self.SnapshotGcodes = None
		self.SavedCommand = None
		self.PositionRequestAttempts = 0
		self.SnapshotSuccess = False
		self.SnapshotError = ""
	
class TimelapseState(object):
	Idle = 1
	WaitingForTrigger = 2
	RequestingReturnPosition = 3
	SendingSnapshotGcode = 4
	TakingSnapshot = 5
	SendingReturnGcode = 6
	WaitingToRender = 7
