# coding=utf-8
import time
import shutil
import os
import threading

from octoprint_octolapse.trigger import GcodeTrigger, TimerTrigger, LayerTrigger
import octoprint_octolapse.utility as utility
from octoprint_octolapse.snapshot import CaptureSnapshot,SnapshotInfo
from octoprint_octolapse.settings import OctolapseSettings, Printer, Stabilization, Camera, Rendering, Snapshot, DebugProfile
from octoprint_octolapse.render import Render
from octoprint_octolapse.gcode import SnapshotGcodeGenerator, SnapshotGcode
from octoprint_octolapse.command import *
from octoprint_octolapse.position import Position

class Timelapse(object):
	
	def __init__(self,octolapseSettings, dataFolder, timelapseFolder, onMovieRendering = None,onMovieDone = None, onMovieFailed = None ):
		# config variables - These don't change even after a reset
		self.Settings = octolapseSettings
		self.DataFolder = dataFolder
		self.DefaultTimelapseDirectory =  timelapseFolder
		self.OnMovieRenderingCallback = onMovieRendering
		self.OnMovieDoneCallback = onMovieDone
		self.OnMovieFailedCallback = onMovieFailed
		self.Responses = Responses() # Used to decode responses from the 3d printer
		self.Commands = Commands() # used to parse and generate gcode
		
		# Settings that may be different after StartTimelapse is called
		self.FfMpegPath = None
		self.Snapshot = None
		self.Gcode = None
		self.Printer = None
		self.CaptureSnapshot = None
		self.Position = None
		
		# State tracking variables
		self.Reset()
		
	def StartTimelapse(self,octoprintPrinter, octoprintPrinterProfile, ffmpegPath,g90InfluencesExtruder):
		self.Reset()
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
		self.SnapshotGcodeErrorMaxAttempts = 10
		self.IsTestMode = self.Settings.CurrentDebugProfile().is_test_mode
		# create the triggers
		# If the gcode trigger is enabled, add it
		if(self.Snapshot.gcode_trigger_enabled):
			#Add the trigger to the list
			self.Triggers.append(GcodeTrigger(self.Settings))
		# If the layer trigger is enabled, add it
		if(self.Snapshot.layer_trigger_enabled):
			self.Triggers.append(LayerTrigger(self.Settings))
		# If the layer trigger is enabled, add it
		if(self.Snapshot.timer_trigger_enabled):
			self.Triggers.append(TimerTrigger(self.Settings))

	def Reset(self):
		
		self.State = TimelapseState.Idle
		self.Triggers = []
		self.CommandIndex = -1
		self.SnapshotCount = 0
		self.PrintStartTime = None
		self.PrintEndTime = None
		self.SnapshotGcodes = None
		self.SavedCommand = None
		self.PositionRequestAttempts = 0
		self.SnapshotGcodeError = False
		self.SnapshotGcodeErrorAttempts = 0
		self.IsTestMode = False

	def ResetSnapshot(self):
		self.State = TimelapseState.WaitingForTrigger
		self.CommandIndex = -1
		self.SnapshotGcodes = None
		self.SavedCommand = None
		self.SnapshotGcodeError = False
		self.PositionRequestAttempts = 0
		self.SnapshotGcodeErrorAttempts = 0

	def PrintPaused(self):
		if(self.State == TimelapseState.Idle):
			return
		elif(self.State == TimelapseState.WaitingForTrigger):
			self.Settings.CurrentDebugProfile().LogPrintStateChange("Print Paused.")
			if(self.Triggers is not None):
				for trigger in self.Triggers:
					if(type(trigger) == TimerTrigger):
						trigger.Pause()

	def IsTimelapseActive(self):
		if(
			self.State == TimelapseState.Idle
			or not self.Settings.is_octolapse_enabled
			or len(self.Triggers)<1
		):
			return False
		return True
	def ReturnGcodeCommandToOctoprint(self, cmd):
		if(self.IsTestMode and self.State == TimelapseState.WaitingForTrigger):
			return self.Commands.AlterCommandForTestMode(cmd)
		return None
	def GcodeQueuing(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		# update the position tracker so that we know where all of the axis are.
		# We will need this later when generating snapshot gcode so that we can return to the previous
		# position
		if (cmd is not None):
			cmd = cmd.upper().strip()

		self.Position.Update(cmd)
		# Don't do anything further to any commands unless we are taking a timelapse , or if octolapse paused the print.

		# if there was a gcode error
		if(self.SnapshotGcodeError):
			if(cmd not in (command.upper().strip() for command in self.SnapshotGcodes.GcodeCommands)):
				return (None,)
			else:
				return self.ReturnGcodeCommandToOctoprint(cmd)				

		# if we have sent an m114 command
		if(self.State > TimelapseState.WaitingForTrigger ):
			# suppress any commands we don't, under any cirumstances, to execute while we're taking a snapshot
			if(cmd in self.Commands.SuppressedSnapshotGcodeCommands):
				return (None,) # suppress the command
			#	# we need to suppress any M114 commands that we haven't sent
			if(self.State > TimelapseState.RequestingReturnPosition
				and self.State != TimelapseState.RequestingSnapshotPosition):
				if(cmd not in (command.upper().strip() for command in self.SnapshotGcodes.GcodeCommands)):
					self.Settings.CurrentDebugProfile().LogWarning("Snapshot Queue Monitor - The received command {0} is not in our snapshot commands, suppressing.".format(cmd));
					return (None ,) # suppress the command
				# Check to see if the current command is the next one on our queue.
				currentSnapshotCommand =self.SnapshotGcodes.GcodeCommands[self.CommandIndex].upper().strip()
				if(cmd == currentSnapshotCommand):
					if(self.CommandIndex == self.SnapshotGcodes.SnapshotMoveIndex):
						self.State = TimelapseState.SendingMoveCommand
					elif(self.CommandIndex == self.SnapshotGcodes.SnapshotIndex):
						# we will be requesting the position in the next command, set the proper state.
						self.State = TimelapseState.RequestingSnapshotPosition
						# report having found the snapshot command index
						self.Settings.CurrentDebugProfile().LogSnapshotGcodeEndcommand("Snapshot command queued.")

					# increment the current command index

					if(self.CommandIndex < self.SnapshotGcodes.EndIndex()):
						self.CommandIndex += 1
					elif(self.CommandIndex == self.SnapshotGcodes.EndIndex() and self.State == TimelapseState.SendingReturnGcode):
						self.Settings.CurrentDebugProfile().LogSnapshotGcodeEndcommand("End Snapshot Return Gcode Command Found, ending the snapshot.")
						self.EndSnapshot()
						
				else:
					self.Settings.CurrentDebugProfile().LogWarning("Snapshot Queue Monitor - The current command index {0} does not equal the snapshot index {1}, or the queuing command {2} does not equal the the snapshot command {3}. Ignoring.".format(self.CommandIndex,self.SnapshotGcodes.SnapshotIndex, cmd, currentSnapshotCommand))
					# set the snapshot gcode error state to True
					#self.SnapshotGcodeError = True
					#self.CommandIndex += 1
				

			return self.ReturnGcodeCommandToOctoprint(cmd)
		
		isPrinterSnapshotCommand = self.IsSnapshotCommand(cmd)
		if(self.State == TimelapseState.WaitingForTrigger):
			currentTrigger = self.IsTriggering(cmd)
			if(currentTrigger is not None):#We're triggering
				self.State = TimelapseState.RequestingReturnPosition
				# we don't want to execute the current command.  We have saved it for later.
				# but we don't want to send the snapshot command to the printer, or any of the SupporessedSavedCommands (gcode.py)
				if(isPrinterSnapshotCommand or cmd in (command.upper().strip() for command in self.Commands.SuppressedSavedCommands)):
					self.SavedCommand = None # this will suppress the command since it won't be added to our snapshot commands list
				else:
					self.SavedCommand = cmd; # this will cause the command to be added to the end of our snapshot commands
				# pause the printer to start the snapshot
				self.State = TimelapseState.RequestingReturnPosition
				self.OctoprintPrinter.pause_print()
				#self.SendPositionRequestGcode(True) # We're going to use the location provided automatically when we pause octoprint
				return (None,)

		if(isPrinterSnapshotCommand ):
			# in all cases do not return the snapshot command to the printer.  It is NOT a real gcode and could cause errors.
			return (None,)

		return self.ReturnGcodeCommandToOctoprint(cmd)

	def GcodeSent(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		
		if (cmd is not None):
			cmd = cmd.upper().strip()

		self.Settings.CurrentDebugProfile().LogSentGcode("Sent to printer: Command Type:{0}, gcode:{1}, cmd: {2}".format(cmd_type, gcode, cmd))
		
		# Handle error state as well as possible
		if(self.SnapshotGcodeError):
			if(self.State > TimelapseState.RequestingReturnPosition):
				if(cmd in (command.upper().strip() for command in self.SnapshotGcodes.GcodeCommands)):
					if(self.CommandIndex >= self.SnapshotGcodes.EndIndex()):
						self.EndSnapshot()
						return None
					self.Settings.CurrentDebugProfile().LogWarning("Attempting to gracefully end the snapshot after an error.  The received command {0} is not in our snapshot commands, suppressing.".format(cmd));
					self.CommandIndex += 1
				else:
					self.SnapshotGcodeErrorAttempts += 1

				if(self.SnapshotGcodeErrorAttempts > self.SnapshotGcodeErrorMaxAttempts):
					self.EndSnapshot()
			else:
				self.EndSnapshot()

		# If we are waiting for the positon 
		if(self.State == TimelapseState.SendingMoveCommand):
			# make sure this command is in our snapshot gcode list, else ignore
			if(cmd in (command.upper().strip() for command in self.SnapshotGcodes.GcodeCommands)):
				# Get the move command index and command
				snapshotMoveIndex = self.SnapshotGcodes.SnapshotMoveIndex
				moveCommand = self.SnapshotGcodes.GcodeCommands[snapshotMoveIndex]
				if(cmd == moveCommand.upper().strip()):
					self.CommandIndex = snapshotMoveIndex + 1
					self.State = TimelapseState.MoveCommandSent
					self.Settings.CurrentDebugProfile().LogSnapshotGcodeEndcommand("Move command sent.  Requesting snapshot position")
					self.SendPositionRequestGcode(False)
					# make sure that we set the RequestingSnapshotPosition flag so that the position request we detected will be captured the PositionUpdated event.
		return None

	def IsSnapshotCommand(self, command):
		commandName = GetGcodeFromString(command)
		snapshotCommandName = GetGcodeFromString(self.Printer.snapshot_command)
		return commandName == snapshotCommandName

	def IsTriggering(self,cmd):
		# make sure we're in a state that could want to check for triggers
		if(not self.State == TimelapseState.WaitingForTrigger):
			return None
		# check the command to see if it's a debug assrt

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
					#Triggering!
					return currentTrigger
				else:
					self.Settings.CurrentDebugProfile().LogError("A position error prevented a trigger!")
		return None

	def SendPositionRequestGcode(self, isReturn):
		# Send commands to move to the snapshot position
		#if(isReturn):
		#	self.State = TimelapseState.RequestingReturnPosition
		#	self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Gcode sending for snapshot return position (M114).")
		#	self.OctoprintPrinter.commands(["M114"]);
		#else:
			self.State = TimelapseState.RequestingSnapshotPosition
			self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Gcode sending for snapshot position (M400, M114).")
			self.OctoprintPrinter.commands(["M400","M114"]);
		

	def PositionReceived(self, payload):
		isReturn = None
		# octoprint sends a position requests when we pause, which can mess our $H1t up, so ignore it
		if(payload["reason"] == "pause"): # lucky for us there is a reason attached.  I'd LOVE to be able to attach a reason (or any note) to a command and have it returned!
			self.Settings.CurrentDebugProfile().LogPrintStateChange("Ignored position that was originally requested by Octoprint.")
			isReturn = True
			#return False, "Declined - Octoprint Pause Position Request"
		if(self.State == TimelapseState.RequestingReturnPosition):
			# if we are getting the return position, set our snapshot state flag and set isReturn = true
			isReturn = True
			self.Settings.CurrentDebugProfile().LogPrintStateChange("Snapshot return position received by Octolapse.")
		elif(self.State == TimelapseState.RequestingSnapshotPosition):
			# if we are getting the snapshot position, set our snapshot state flag and set isReturn = false
			isReturn = False
			self.Settings.CurrentDebugProfile().LogPrintStateChange("Snapshot position received by Octolapse.")
		else:
			self.Settings.CurrentDebugProfile().LogPrintStateChange("Position received by Octolapse while paused, but was declined.")
			return False, "Declined - Incorrect State"

		x=payload["x"]
		y=payload["y"]
		z=payload["z"]
		e=payload["e"]
				
		if(isReturn):
			#todo:  Do we need to re-request the position like we do for the return?  Maybe...
			printerTolerance = self.Printer.printer_position_confirmation_tolerance
			# If we are requesting a return position we have NOT yet executed the command that triggered the snapshot.
			# Because of this we need to compare the position we received to the previous position, not the current one.
			if( not self.Position.IsAtPreviousPosition(x,y,z) ):
				self.Settings.CurrentDebugProfile().LogWarning("The snapshot return position recieved from the printer does not match the position expected by Octolapse.  received (x:{0},y:{1},z:{2}), Expected (x:{3},y:{4},z:{5})".format(x,y,z,self.Position.XPrevious,self.Position.YPrevious,self.Position.ZPrevious))
				self.Position.UpdatePosition(x=x,y=y,z=z,force=True)
				 
			# return position information received
			self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Snapshot return position received - x:{0},y:{1},z:{2},e:{3}".format(x,y,z,e))

			# make sure the SnapshotCommandIndex = 0
			# Todo: ensure this is unnecessary
			self.CommandIndex=0

			# create the GCode for the timelapse and store it
			isRelative = self.Position.IsRelative
			isExtruderRelative = self.Position.IsExtruderRelative
			extruder = self.Position.Extruder
			self.SnapshotGcodes = self.Gcode.CreateSnapshotGcode(x,y,z,isRelative, isExtruderRelative, extruder,savedCommand=self.SavedCommand)
			# make sure we acutally received gcode
			if(self.SnapshotGcodes is None):
				self.Settings.CurrentDebugProfile().LogError("No snapshot gcode was created for this snapshot.  Aborting this snapshot.")
				self.ResetSnapshot();
				return False, "Error - No Snapshot Gcode";

			self.State = TimelapseState.SendingSnapshotGcode

			# send our commands to the printer
			self.OctoprintPrinter.commands(self.SnapshotGcodes.SnapshotCommands());
			return True, "Snapshot Commands Sent"
		else:
			# snapshot position information received
			self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Snapshot position received, checking position:  Received: x:{0},y:{1},z:{2},e:{3}, Expected: x:{4},y:{5},z:{6}".format(x,y,z,e,self.SnapshotGcodes.X,self.SnapshotGcodes.Y, self.Position.Z))
			printerTolerance = self.Printer.printer_position_confirmation_tolerance
			# see if the CURRENT position is the same as the position we received from the printer
			# AND that it is equal to the snapshot position
			if(self.Position.IsAtCurrentPosition(x,y,None)
				and self.Position.IsAtCurrentPosition(self.SnapshotGcodes.X,self.SnapshotGcodes.Y,applyOffset = False)): # our snapshot gcode will NOT be offset
				self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("The snapshot position is correct, taking snapshot.")
				self.State = TimelapseState.TakingSnapshot
				self.TakeSnapshot()
				return True, "Snapshot Taken"
			else:
				self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("The snapshot position is incorrect.")
				self.ResendSnapshotPositionRequest()
				return False, "Incorrect Snapshot Position, Retrying"

	def ResendSnapshotPositionRequest(self):
		# get the number of times to retry, and how long to delay before requesting the new position
		maxRetryAttempts = self.Snapshot.position_request_retry_attemps
		requestDelaySeconds = self.Snapshot.position_request_retry_delay_ms / 1000.0
		self.PositionRequestAttempts += 1
		# todo:  make the retry attempts a setting, as well as the request delay
		
		if(self.PositionRequestAttempts > maxRetryAttempts):
			self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("The maximum number of position discovery attempts ({0}) has been reached for this snapshot.  Aborting this snapshot.".format(maxRetryAttempts))
			# we're giving up and no longer requesting a snapshot position.
			self.State = TimelapseState.SendingReturnGcode
			self.SendSnapshotReturnCommands()
			return False
		self.SendDelayedSnapshotPositionRequest(requestDelaySeconds, self.SendPositionRequestGcode)
		self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Re-requesting our present location with a delay of {0} seconds. Try number {1} of {2}".format(requestDelaySeconds,  self.PositionRequestAttempts, maxRetryAttempts))

		return True

	def SendDelayedSnapshotPositionRequest(self, requestDelaySeconds, positionRequestGcode):
		t = threading.Timer( requestDelaySeconds,positionRequestGcode , [False])
		t.start()

	def EndSnapshot(self):
		# Cleans up the variables and resumes the print once the snapshot is finished, and the extruder is in the proper position 
		
		# reset the snapshot variables
		self.ResetSnapshot();
		# if the print is paused, resume!
		if(self.OctoprintPrinter.is_paused()):
			self.Settings.CurrentDebugProfile().LogSnapshotDownload("Resuming Print.")
			self.OctoprintPrinter.resume_print()
		
	def TakeSnapshot(self):
		self.Settings.CurrentDebugProfile().LogSnapshotDownload("Taking Snapshot.")
		try:
			
			self.CaptureSnapshot.Snap(utility.CurrentlyPrintingFileName(self.OctoprintPrinter),self.SnapshotCount,onComplete = self.OnSnapshotComplete, onSuccess = self.OnSnapshotSuccess, onFail = self.OnSnapshotFail)
		except:
			a = sys.exc_info() # Info about unknown error that caused exception.                                              
			errorMessage = "    {0}".format(a)
			b = [ str(p) for p in a ]
			errorMessage += "\n    {0}".format(b)
			self.Settings.CurrentDebugProfile().LogError('Unknown error detected:{0}'.format(errorMessage))
		
	def OnSnapshotSuccess(self, *args, **kwargs):
		# Increment the number of snapshots received
		self.SnapshotCount += 1
		# get the save path
		snapshotInfo = args[0]
		# get the current file name
		newSnapshotName = snapshotInfo.GetFullPath(self.SnapshotCount)
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
			self.Settings.CurrentDebugProfile().LogError("Could rename the snapshot {0} to {1}!   Error Type:{2}, Details:{3}".format(snapshotInfo.GetTempFullPath(), newSnapshotName,type,value))

	def OnSnapshotFail(self, *args, **kwargs):
		reason = args[0]
		self.Settings.CurrentDebugProfile().LogWarning("Failed to download the snapshot.  Reason:{0}".format(reason))
		return reason

	def OnSnapshotComplete(self, *args, **kwargs):
		self.Settings.CurrentDebugProfile().LogSnapshotDownload("Snapshot Completed.")
		self.SendSnapshotReturnCommands()
		
	def SendSnapshotReturnCommands(self):
		self.Settings.CurrentDebugProfile().LogSnapshotDownload("Sending Snapshot Return Commands.")
		self.State = TimelapseState.SendingReturnGcode
		self.OctoprintPrinter.commands(self.SnapshotGcodes.ReturnCommands());

	# RENDERING Functions and Events
	def EndTimelapse(self):
		if(self.State != TimelapseState.Idle):
			self.PrintEndTime = time.time()
			self.RenderTimelapse()
			self.Reset();

	def RenderTimelapse(self):
		# make sure we have a non null TimelapseSettings object.  We may have terminated the timelapse for some reason
		if(self.Rendering.enabled):
			self.Settings.CurrentDebugProfile().LogInfo("Started Rendering Timelapse");
			self.CreateRenderTimelapseJob()
			return True
		return False

	def CreateRenderTimelapseJob(self):
		timelapseRenderJob = Render(self.Settings,self.DataFolder,self.DefaultTimelapseDirectory,  self.FfMpegPath,1
							  ,onRenderStart = self.OnRenderStart
							  ,onRenderFail=self.OnRenderFail
							  ,onRenderSuccess = self.OnRenderSuccess
							  ,onRenderComplete = self.OnRenderComplete
							  ,onAfterSyncFail = self.OnSynchronizeRenderingFail
							  ,onAfterSycnSuccess = self.OnSynchronizeRenderingComplete
							  ,onComplete = self.OnRenderTimelapseJobComplete)
		timelapseRenderJob.Process(utility.CurrentlyPrintingFileName(self.OctoprintPrinter), self.PrintStartTime, self.PrintEndTime)

	def OnRenderStart(self, *args, **kwargs):
		self.Settings.CurrentDebugProfile().LogRenderStart("Started rendering/synchronizing the timelapse.")
		finalFilename = args[0]
		baseFileName = args[1]
		#Notify Octoprint
		payload = dict(gcode="unknown",movie=finalFilename,movie_basename=baseFileName,movie_prefix="from Octolapse")
		self.OnMovieRendering(payload)

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
		self.OnMovieFailed(payload)
		
	def OnRenderSuccess(self, *args, **kwargs):
		finalFilename = args[0]
		baseFileName = args[1]
		#TODO:  Notify the user that the rendering is completed if we are not synchronizing with octoprint
		self.Settings.CurrentDebugProfile().LogRenderComplete("Rendering completed successfully.")

	def OnRenderComplete(self, *args, **kwargs):
		self.Settings.CurrentDebugProfile().LogRenderComplete("Completed rendering, ending timelapse.")
	
	# Synchronize renderings with the default plugin
	def OnSynchronizeRenderingComplete(self, *args, **kwargs):
		finalFilename = args[0]
		baseFileName = args[1]
		# Notify the user of success and refresh the default timelapse control
		payload = dict(gcode="unknown",
				movie=finalFilename,
				movie_basename=baseFileName ,
				movie_prefix="from Octolapse")
		self.OnMovieDone(payload)

	def OnSynchronizeRenderingFail(self, *args, **kwargs):
		finalFilename = args[0]
		baseFileName = args[1]
		# Notify the user of success and refresh the default timelapse control
		payload = dict(gcode="unknown",
				movie=finalFilename,
				movie_basename=baseFileName ,
				movie_prefix="from Octolapse",
				returncode=0,
				reason="See the octolapse log for details.")
		self.OnMovieFailed(payload)

	def OnRenderTimelapseJobComplete(self, *args, **kwargs):
		self.Settings.CurrentDebugProfile().LogRenderComplete("Completed the rendering/sync job.")

	def OnMovieRendering(self,payload):
		"""Called when a timelapse has started being rendered.  Calls any callbacks onMovieRendering callback set in the constructor."""
		if(self.OnMovieRenderingCallback is not None):
			self.OnMovieRenderingCallback(payload)

	def OnMovieDone(self, payload):
		"""Called after a timelapse has been rendered.  Calls any callbacks onMovieRendered callback set in the constructor."""
		if(self.OnMovieDoneCallback is not None):
			self.OnMovieDoneCallback(payload)

	def OnMovieFailed(self,payload):
		"""Called after a timelapse rendering attempt has failed.  Calls any callbacks onMovieFailed callback set in the constructor."""
		if(self.OnMovieFailedCallback is not None):
			self.OnMovieFailedCallback(payload)

class TimelapseState(object):
	Idle = 1
	WaitingForTrigger = 2
	RequestingReturnPosition = 4
	SendingSnapshotGcode = 5
	SendingMoveCommand = 6
	MoveCommandSent = 7
	RequestingSnapshotPosition = 8
	TakingSnapshot = 9
	SendingReturnGcode = 10
	
	


