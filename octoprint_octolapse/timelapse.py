# coding=utf-8
from .trigger import *
from .utility import *
from .snapshot import CaptureSnapshot,SnapshotInfo
from .settings import OctolapseSettings, Printer, Stabilization, Camera, Rendering, Snapshot, DebugProfile
from .render import Render
from .gcode import *
from octoprint.events import eventManager, Events
import shutil
class Timelapse(object):


	def __init__(self,octolapseSettings, dataFolder, timelapseFolder):
		self.Settings = octolapseSettings
		self.DataFolder = dataFolder
		self.DefaultTimelapseDirectory =  timelapseFolder 
		self.PrintStartTime = None
		self.PrintEndTime = None
		self.FfMpegPath = None

		self.Snapshot = None
		self.Gcode = None
		self.Printer = None
		self.CaptureSnapshot = None
		self.Position = None
		self.SnapshotCount = 0
		self.Triggers = []
		self.State = TimelapseState.Idle
		self.SnapshotGcodes = None
		self.CommandIndex = -1
		self.SavedCommand = None
		self.PositionRequestAttempts = 0
		
		self.Responses = Responses() # Used to decode responses from the 3d printer
		self.Commands = Commands() # used to parse and generate gcode 
		
	def StartTimelapse(self,octoprintPrinter, octoprintPrinterProfile, ffmpegPath):
		self.Reset()
		self.OctoprintPrinter = octoprintPrinter
		self.OctoprintPrinterProfile = octoprintPrinterProfile
		self.FfMpegPath = ffmpegPath
		self.PrintStartTime=time.time()
		self.Snapshot = Snapshot(self.Settings.CurrentSnapshot())
		self.Gcode = Gcode(self.Settings,octoprintPrinterProfile)
		self.Printer = Printer(self.Settings.CurrentPrinter())
		self.Rendering = Rendering(self.Settings.CurrentRendering())
		
		self.CaptureSnapshot = CaptureSnapshot(self.Settings,  self.DataFolder, printStartTime=time.time())
		self.Position = Position(self.Settings,octoprintPrinterProfile)
		self.State = TimelapseState.WaitingForTrigger
		# create the triggers for this print
		snapshot = self.Settings.CurrentSnapshot()
		# If the gcode trigger is enabled, add it
		if(self.Snapshot.gcode_trigger_enabled):
			#Add the trigger to the list
			self.Triggers.append(GcodeTrigger(self.Settings))
		# If the layer trigger is enabled, add it
		if(snapshot.layer_trigger_enabled):
			self.Triggers.append(LayerTrigger(self.Settings))
		# If the layer trigger is enabled, add it
		if(snapshot.timer_trigger_enabled):
			self.Triggers.append(TimerTrigger(self.Settings))

	def Reset(self):
		self.State = TimelapseState.Idle
		self.Triggers = []
		self.CommandIndex = -1
		self.SnapshotCount = 0
		self.PrintEndTime = None
		self.PrintStartTime = None
		self.SnapshotGcodes = None
		self.SavedCommand = None
		self.Triggers = []

	def ResetSnapshot(self):
		self.State = TimelapseState.WaitingForTrigger
		self.CommandIndex = -1
		self.SnapshotGcodes = None
		self.SavedCommand = None

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

	def GcodeQueuing(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		# update the position tracker so that we know where all of the axis are.
		# We will need this later when generating snapshot gcode so that we can return to the previous
		# position

		if(self.State == TimelapseState.Idle):
			return

		self.Position.Update(cmd)
		# Don't do anything further to any commands unless we are taking a timelapse , or if octolapse paused the print.

		#Apply any debug assert commands
		self.ApplyCommands(cmd)

		# return if we're not taking our timelapse
		if(not self.IsTimelapseActive()):
			return None


		# if we have sent an m114 command
		if(self.State > TimelapseState.WaitingForTrigger ):
			# suppress any commands we don't, under any cirumstances, to execute while we're taking a snapshot
			if(cmd in ['M105']):
				return None, # suppress the command
			#	# we need to suppress any M114 commands that we haven't sent
			if(self.State > TimelapseState.RequestingReturnPosition):
				if(cmd not in self.SnapshotGcodes.GcodeCommands):
					self.Settings.CurrentDebugProfile().LogWarning("Snapshot Queue Monitor - The received command {0} is not in our snapshot commands, suppressing.".format(cmd));
					return None , # suppress the command
				# Check to see if the current command is the next one on our queue.
				if(cmd == self.SnapshotGcodes.GcodeCommands[self.CommandIndex]):
					
					if(self.CommandIndex == self.SnapshotGcodes.SnapshotIndex):
						# we will be requesting the position in the next command, set the proper state.
						self.State = TimelapseState.RequestingSnapshotPosition
						# report having found the snapshot command index
						self.Settings.CurrentDebugProfile().LogSnapshotGcodeEndcommand("Snapshot command queued.")

					# increment the current command index

					if(self.CommandIndex < self.SnapshotGcodes.EndIndex()):
						self.CommandIndex += 1
					elif(self.CommandIndex > self.SnapshotGcodes.EndIndex() and self.State == TimelapseState.SendingReturnGcode):
						self.Settings.CurrentDebugProfile().LogSnapshotGcodeEndcommand("End Snapshot Return Gcode Command Found, ending the snapshot.")
						self.EndSnapshot()
						
				else:
					self.Settings.CurrentDebugProfile().LogWarning("Snapshot Queue Monitor - The current command index {0} does not equal the snapshot index {1}, or the queuing command {2} does not equal the the snapshot command {3}.".format(self.CommandIndex,snapshotIndex, cmd, snapshotCommand))

			return None  # leave the comand alone
		
		currentTrigger = self.IsTriggering(cmd)
		isPrinterSnapshotCommand = self.IsSnapshotCommand(cmd)
		if(currentTrigger is not None and self.State == TimelapseState.WaitingForTrigger): #We're triggering
			# we don't want to execute the current command.  We have saved it for later.
			# but we don't want to send the snapshot command to the printer, or any of the SupporessedSavedCommands (gcode.py)
			if(isPrinterSnapshotCommand or cmd in self.Commands.SuppressedSavedCommands):
				self.SavedCommand = None # this will suppress the command since it won't be added to our snapshot commands list
			else:
				self.SavedCommand = cmd; # this will cause the command to be added to the end of our snapshot commands

			# pausing the print after setting these two flags to true will a position request, which will trigger a snapshot
			self.State = TimelapseState.RequestingReturnPosition
			self.OctoprintPrinter.pause_print()
			self.SendPositionRequestGcode(True)
			return None,

		if(isPrinterSnapshotCommand ):
			# in all cases do not return the snapshot command to the printer.  It is NOT a real gcode and could cause errors.
			return None,

		return None
	def GcodeSent(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		if(self.State == TimelapseState.Idle):
			return

		if(self.IsTimelapseActive()):
			self.Settings.CurrentDebugProfile().LogSentGcode("Sent to printer: Command Type:{0}, gcode:{1}, cmd: {2}".format(cmd_type, gcode, cmd))
		else:
			return
		
		# If we are waiting for the positon 
		if(self.State == TimelapseState.SendingSnapshotGcode):
			
			# make sure this command is in our snapshot gcode list, else ignore
			if(cmd not in self.SnapshotGcodes.GcodeCommands):
				return
			
			# Get the move command index and command
			snapshotMoveIndex = self.SnapshotGcodes.SnapshotMoveIndex
			moveCommand = self.SnapshotGcodes.GcodeCommands[snapshotMoveIndex]
			if(cmd == moveCommand):
				self.State = TimelapseState.MoveCommandSent
				self.Settings.CurrentDebugProfile().LogSnapshotGcodeEndcommand("Move command sent, looking for snapshot position.")
				# make sure that we set the RequestingSnapshotPosition flag so that the position request we detected will be captured the PositionUpdated event.
				

	def IsSnapshotCommand(self, command):
		commandName = GetGcodeFromString(command)
		snapshotCommandName = GetGcodeFromString(self.Printer.snapshot_command)
		return commandName == snapshotCommandName

	def IsTriggering(self,cmd):

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
		if(isReturn):
			self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Gcode sending for snapshot return position (M400, M114).")
			self.State = TimelapseState.RequestingReturnPosition
		else:
			self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Gcode sending for snapshot position (M400, M114).")
			self.State = TimelapseState.RequestingSnapshotPosition

		self.OctoprintPrinter.commands("M114");

	def PositionReceived(self, payload):
		isReturn = None
		# octoprint sends a position requests when we pause, which can mess our $H1t up, so ignore it
		if(payload["reason"] == "pause"): # lucky for us there is a reason attached.  I'd LOVE to be able to attach a reason (or any note) to a command and have it returned!
			self.Settings.CurrentDebugProfile().LogPrintStateChange("Ignored position that was originally requested by Octoprint.")
			return
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
			return

		x=payload["x"]
		y=payload["y"]
		z=payload["z"]
		e=payload["e"]
		previousX = self.Position.XPrevious
		previousY = self.Position.YPrevious
		previousZ = self.Position.ZPrevious
		
		if(isReturn):
			#todo:  Do we need to re-request the position like we do for the return?  Maybe...
			printerTolerance = self.Printer.printer_position_confirmation_tolerance
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
			self.CommandIndex=0

			# create the GCode for the timelapse and store it
			isRelative = self.Position.IsRelative
			isExtruderRelative = self.Position.IsExtruderRelative()
			extruder = self.Position.Extruder
			self.SnapshotGcodes = self.Gcode.CreateSnapshotGcode(x,y,z,isRelative, isExtruderRelative, extruder,savedCommand=self.SavedCommand)
			# make sure we acutally received gcode
			if(self.SnapshotGcodes is None):
				self.Settings.CurrentDebugProfile().LogError("No snapshot gcode was created for this snapshot.  Aborting this snapshot.")
				self.ResetSnapshot();
				return;

			self.State = TimelapseState.SendingSnapshotGcode

			# send our commands to the printer
			self.OctoprintPrinter.commands(self.SnapshotGcodes.SnapshotCommands());
		else:
			# snapshot position information received
			self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Snapshot position received, checking position:  Received: x:{0},y:{1},z:{2},e:{3}, Expected: x:{4},y:{5}".format(x,y,z,e,self.SnapshotGcodes.X,self.SnapshotGcodes.Y))

			printerTolerance = self.Printer.printer_position_confirmation_tolerance
			if((utility.isclose(self.SnapshotGcodes.X, x,abs_tol=printerTolerance))
				and (utility.isclose( self.SnapshotGcodes.Y, y,abs_tol=printerTolerance))
			):
				self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("The snapshot position is correct, taking snapshot.")
				self.State = TimelapseState.TakingSnapshot
				self.TakeSnapshot()
			else:
				self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("The snapshot position is incorrect.")
				self.ResendSnapshotPositionRequest()
	def ResendSnapshotPositionRequest(self):

		# rety 20 times with a .25 second delay between attempts
		maxRetryAttempts = self.Snapshot.position_request_retry_attemps
		requestDelaySeconds = self.Snapshot.position_request_retry_delay_ms / 1000.0
		self.PositionRequestAttempts += 1
		# todo:  make the retry attempts a setting, as well as the request delay
		
		if(self.PositionRequestAttempts > maxRetryAttempts):
			self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("The maximum number of position discovery attempts ({0}) has been reached for this snapshot.  Aborting this snapshot.".format(maxRetryAttempts))
			# we're giving up and no longer requesting a snapshot position.
			self.State = TimelapseState.SendingReturnGcode
			self.SendSnapshotReturnCommands()
			return 

		self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Re-requesting our present location with a delay of {0} seconds. Try number {1} of {2}".format(requestDelaySeconds,  self.PositionRequestAttempts, maxRetryAttempts))
		t = threading.Timer( requestDelaySeconds, self.SendPositionRequestGcode, [False])
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
		self.LogSnapshotDownload("Failed to download the snapshot.  Reason:{0}".format(reason))

	def OnSnapshotComplete(self, *args, **kwargs):
		self.Settings.CurrentDebugProfile().LogSnapshotDownload("Snapshot Completed.")
		self.SendSnapshotReturnCommands()

	def SendSnapshotReturnCommands(self):
		self.Settings.CurrentDebugProfile().LogSnapshotDownload("Sending Snapshot Return Commands.")
		self.State = TimelapseState.SendingReturnGcode
		self.OctoprintPrinter.commands(self.SnapshotGcodes.ReturnCommands());

	# RENDERING Functions and Events
	def PrintEnded(self):
		self.PrintEndTime = time.time()
		self.RenderTimelapse()

	def RenderTimelapse(self):
		# make sure we have a non null TimelapseSettings object.  We may have terminated the timelapse for some reason
		if(self.Rendering.enabled):
			self.Settings.CurrentDebugProfile().LogInfo("Started Rendering Timelapse");
			timelapseRenderJob = Render(self.Settings,self.DataFolder,self.DefaultTimelapseDirectory,  self.FfMpegPath,1,onStart = self.OnRenderStart,onFail=self.OnRenderFail, onSuccess = self.OnRenderSuccess, onAlways = self.OnRenderingComplete, onAfterSyncFail = self.OnSynchronizeRenderingFail, onAfterSycnSuccess = self.OnSynchronizeRenderingComplete)
			timelapseRenderJob.Process(utility.CurrentlyPrintingFileName(self.OctoprintPrinter), self.PrintStartTime, self.PrintEndTime)
		
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

	# Synchronize renderings with the default plugin
	def OnSynchronizeRenderingComplete(self, *args, **kwargs):
		finalFilename = args[0]
		baseFileName = args[1]
		# Notify the user of success and refresh the default timelapse control
		payload = dict(gcode="unknown",
				movie=finalFilename,
				movie_basename=baseFileName ,
				movie_prefix="from Octolapse")
		eventManager().fire(Events.MOVIE_DONE, payload)
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
		eventManager().fire(Events.MOVIE_FAILED, payload)

	def ApplyCommands(self, cmd):

		# see if the command is our debug command
		command = Command()
		command = self.Commands.GetCommand(cmd)
		if(command is not None):
			if(command.Command == Commands.Debug_Assert.Command):
				# make sure our assert conditions are true or throw an exception
				command.Parse(cmd)
				snapshot = command.Parameters["Snapshot"]
				gcodeTrigger = command.Parameters["GcodeTrigger"]
				gcodeTriggerWait = command.Parameters["GcodeTriggerWait"]
				timerTrigger = command.Parameters["TimerTrigger"]
				timerTriggerWait = command.Parameters["TimerTriggerWait"]
				layerTrigger = command.Parameters["LayerTrigger"]
				layerTriggerWait = command.Parameters["LayerTriggerWait"]
				for trigger in self.Triggers:
					if(isinstance(trigger,GcodeTrigger)):
						if(gcodeTrigger is not None):
							assert trigger.IsTriggered == gcodeTrigger
						if(gcodeTriggerWait is not None):
							assert trigger.IsWaiting == gcodeTriggerWait
					if(isinstance(trigger,TimerTrigger)):
						if(timerTrigger is not None):
							assert trigger.IsTriggered == timerTrigger
						if(timerTriggerWait is not None):
							assert trigger.IsWaiting == timerTriggerWait
					if(isinstance(trigger,LayerTrigger)):
						if(layerTrigger is not None):
							assert trigger.IsTriggered == layerTrigger
						if(layerTriggerWait is not None):
							assert trigger.IsWaiting == layerTriggerWait
class TimelapseState(object):
	Idle = 1
	WaitingForTrigger = 2
	RequestingReturnPosition = 3
	SendingSnapshotGcode = 4
	MoveCommandSent = 5
	TakingSnapshot = 6
	RequestingSnapshotPosition = 7
	SendingReturnGcode = 8
	
	


