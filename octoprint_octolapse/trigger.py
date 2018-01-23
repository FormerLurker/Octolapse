
# coding=utf-8
from octoprint_octolapse.position import *
from octoprint_octolapse.extruder import ExtruderTriggers
from octoprint_octolapse.gcode import *
from octoprint_octolapse.command import *
from octoprint_octolapse.settings import *
import octoprint_octolapse.utility as utility
import time

class GcodeTrigger(object):
	"""Used to monitor gcode for a specified command."""
	def __init__(self, octolapseSettings ):
		self.Settings = octolapseSettings
		self.Printer = self.Settings.CurrentPrinter()
		self.Snapshot = self.Settings.CurrentSnapshot()
		self.RequireZHop = self.Snapshot.gcode_trigger_require_zhop
		self.ExtruderTriggers = ExtruderTriggers(
				 self.Snapshot.gcode_trigger_on_extruding_start
				,self.Snapshot.gcode_trigger_on_extruding
				,self.Snapshot.gcode_trigger_on_primed
				,self.Snapshot.gcode_trigger_on_retracting_start
				,self.Snapshot.gcode_trigger_on_retracting
				,self.Snapshot.gcode_trigger_on_partially_retracted
				,self.Snapshot.gcode_trigger_on_retracted
				,self.Snapshot.gcode_trigger_on_detracting_start
				,self.Snapshot.gcode_trigger_on_detracting
				,self.Snapshot.gcode_trigger_on_detracted)
		# state tracking variables
		self.Reset()
		
		# Logging		
		self.Settings.CurrentDebugProfile().LogTriggerCreate("Creating Gcode Trigger - Gcode Command:{0}, RequireZHop:{1}".format(self.Printer.snapshot_command, self.Snapshot.gcode_trigger_require_zhop))
		self.Settings.CurrentDebugProfile().LogTriggerCreate("Extruder Triggers - OnExtrudingStart:{0}, OnExtruding:{1}, OnPrimed:{2}, OnRetractingStart:{3} OnRetracting:{4}, OnPartiallyRetracted:{5}, OnRetracted:{6}, ONDetractingStart:{7}, OnDetracting:{8}, OnDetracted:{9}"
				.format(self.Snapshot.gcode_trigger_on_extruding_start
				,self.Snapshot.gcode_trigger_on_extruding
				,self.Snapshot.gcode_trigger_on_primed
				,self.Snapshot.gcode_trigger_on_retracting_start
				,self.Snapshot.gcode_trigger_on_retracting
				,self.Snapshot.gcode_trigger_on_partially_retracted
				,self.Snapshot.gcode_trigger_on_retracted
				,self.Snapshot.gcode_trigger_on_detracting_start
				,self.Snapshot.gcode_trigger_on_detracting
				,self.Snapshot.gcode_trigger_on_detracted)
			)
	def Reset(self):
		self.IsTriggered = False
		self.IsWaiting = False
	def Update(self, position,commandName):
		"""If the provided command matches the trigger command, sets IsTriggered to true, else false"""
		self.IsTriggered = False
		# Don't update the trigger if we don't have a homed axis
		# Make sure to use the previous value so the homing operation can complete
		if(not position.HasHomedAxis(1)):
			self.IsTriggered = False
			return

		if (self.IsSnapshotCommand(commandName)):
			self.IsWaiting = True
		if(self.IsWaiting == True):
			if(position.Extruder.IsTriggered(self.ExtruderTriggers)):
				if(self.RequireZHop and not position.IsZHop(1)):
					self.Settings.CurrentDebugProfile().LogTriggerWaitState("GcodeTrigger - Waiting on ZHop.")
				else:
					self.IsTriggered = True
					self.IsWaiting = False
					self.Settings.CurrentDebugProfile().LogTriggering("GcodeTrigger - Waiting for extruder to trigger.")
			else:
				self.Settings.CurrentDebugProfile().LogTriggerWaitState("GcodeTrigger - Waiting for extruder to trigger.")
	def IsSnapshotCommand(self, command):
		commandName = GetGcodeFromString(command)
		snapshotCommandName = GetGcodeFromString(self.Printer.snapshot_command)
		return commandName == snapshotCommandName
class LayerTrigger(object):
	
	def __init__( self,octolapseSettings):
		self.Settings = octolapseSettings
		#utilities and profiles
		self.Snapshot = self.Settings.CurrentSnapshot()
		self.ExtruderTriggers = ExtruderTriggers(
				self.Snapshot.layer_trigger_on_extruding_start
				,self.Snapshot.layer_trigger_on_extruding
				,self.Snapshot.layer_trigger_on_primed
				,self.Snapshot.layer_trigger_on_retracting_start
				,self.Snapshot.layer_trigger_on_retracting
				,self.Snapshot.layer_trigger_on_partially_retracted
				,self.Snapshot.layer_trigger_on_retracted
				,self.Snapshot.layer_trigger_on_detracting_start
				,self.Snapshot.layer_trigger_on_detracting
				,self.Snapshot.layer_trigger_on_detracted)
		# Configuration Variables
		self.RequireZHop = self.Snapshot.layer_trigger_require_zhop
		self.HeightIncrement = self.Snapshot.layer_trigger_height
		if(self.HeightIncrement == 0):
			self.HeightIncrement = None
		self.Reset()
		# debug output
		self.Settings.CurrentDebugProfile().LogTriggerCreate("Creating Layer Trigger - TriggerHeight:{0} (none = layer change), RequiresZHop:{1}".format(self.Snapshot.layer_trigger_height, self.Snapshot.layer_trigger_require_zhop))
		self.Settings.CurrentDebugProfile().LogTriggerCreate("Extruder Triggers - OnExtrudingStart:{0}, OnExtruding:{1}, OnPrimed:{2}, OnRetractingStart:{3} OnRetracting:{4}, OnPartiallyRetracted:{5}, OnRetracted:{6}, ONDetractingStart:{7}, OnDetracting:{8}, OnDetracted:{9}"
			.format(
				 self.Snapshot.layer_trigger_on_extruding_start
				,self.Snapshot.layer_trigger_on_extruding
				,self.Snapshot.layer_trigger_on_primed
				,self.Snapshot.layer_trigger_on_retracting_start
				,self.Snapshot.layer_trigger_on_retracting
				,self.Snapshot.layer_trigger_on_partially_retracted
				,self.Snapshot.layer_trigger_on_retracted
				,self.Snapshot.layer_trigger_on_detracting_start
				,self.Snapshot.layer_trigger_on_detracting
				,self.Snapshot.layer_trigger_on_detracted
			)
		)
			

	def Reset(self):
		"""Resets all state tracking variables and flags.  Does not change the settings (HeightIncrement)"""
		
		self.CurrentIncrement = 0
		self.IsWaiting = False
		self.IsTriggered = False
		self.IsHeightChange = False
		# private flags
		self.__LayerChangeWait = False
		self.__HeightChangeWait = False

	def Update(self, position):
		"""Updates the layer monitor position.  x, y and z may be absolute, but e must always be relative"""
		self.IsTriggered = False
		self.IsHeightChange = False
		# Don't update the trigger if we don't have a homed axis
		# Make sure to use the previous value so the homing operation can complete
		if(not position.HasHomedAxis(1)):
			return

		# calculate height increment changed
		
		if(self.HeightIncrement is not None and self.HeightIncrement> 0 and position.IsLayerChange(1)
			and self.CurrentIncrement * self.HeightIncrement <= position.Height(1)):
			self.CurrentIncrement += 1
			self.IsHeightChange  = True
			self.Settings.CurrentDebugProfile().LogTriggerHeightChange("Layer Trigger - Height Increment:{0}".format(self.HeightIncrement))

		# see if we've encountered a layer or height change
		if(self.HeightIncrement is not None and self.HeightIncrement > 0):
			if(self.IsHeightChange):
				self.__HeightChangeWait = True
				
		else:
			if(position.IsLayerChange(1)):
				self.__LayerChangeWait = True

		
		# see if the extruder is triggering
		isExtruderTriggering = position.Extruder.IsTriggered(self.ExtruderTriggers)

		if(self.__HeightChangeWait or self.__LayerChangeWait or self.IsWaiting):
			self.IsWaiting = True
			if(not isExtruderTriggering):
				if(self.__HeightChangeWait):
					self.Settings.CurrentDebugProfile().LogTriggerWaitState("LayerTrigger - Height change triggering, waiting on extruder.")
				elif (self.__LayerChangeWait):
					self.Settings.CurrentDebugProfile().LogTriggering("LayerTrigger - Layer change triggering, waiting on extruder.")
			else:
				if(self.RequireZHop and not position.IsZHop(1)):
					self.Settings.CurrentDebugProfile().LogTriggerWaitState("LayerTrigger - Triggering - Waiting on ZHop.")
					return
				if(self.__HeightChangeWait):
					self.Settings.CurrentDebugProfile().LogTriggering("LayerTrigger - Height change triggering.")
				elif (self.__LayerChangeWait):
					self.Settings.CurrentDebugProfile().LogTriggering("LayerTrigger - Layer change triggering.")

				self.__LayerChangeWait = False
				self.__HeightChangeWait = False
				self.IsTriggered = True
				self.IsWaiting = False

class TimerTrigger(object):
	
	def __init__(self,octolapseSettings):
		self.Settings = octolapseSettings

		self.Snapshot = self.Settings.CurrentSnapshot()
		self.ExtruderTriggers = ExtruderTriggers(
				 self.Snapshot.timer_trigger_on_extruding_start
				,self.Snapshot.timer_trigger_on_extruding
				,self.Snapshot.timer_trigger_on_primed
				,self.Snapshot.timer_trigger_on_retracting_start
				,self.Snapshot.timer_trigger_on_retracting
				,self.Snapshot.timer_trigger_on_partially_retracted
				,self.Snapshot.timer_trigger_on_retracted
				,self.Snapshot.timer_trigger_on_detracting_start
				,self.Snapshot.timer_trigger_on_detracting
				,self.Snapshot.timer_trigger_on_detracted)
		self.IntervalSeconds = self.Snapshot.timer_trigger_seconds
		self.RequireZHop = self.Snapshot.timer_trigger_require_zhop
		self.IntervalSeconds = self.Snapshot.timer_trigger_seconds

		# create state variables
		self.Reset();

		# Log output
		self.Settings.CurrentDebugProfile().LogTriggerCreate("Creating Timer Trigger - Seconds:{0}, RequireZHop:{1}".format(self.Snapshot.timer_trigger_seconds, self.Snapshot.timer_trigger_require_zhop))
		self.Settings.CurrentDebugProfile().LogTriggerCreate("Extruder Triggers - OnExtrudingStart:{0}, OnExtruding:{1}, OnPrimed:{2}, OnRetractingStart:{3} OnRetracting:{4}, OnPartiallyRetracted:{5}, OnRetracted:{6}, ONDetractingStart:{7}, OnDetracting:{8}, OnDetracted:{9}"
				.format(
					self.Snapshot.timer_trigger_on_extruding_start
					,self.Snapshot.timer_trigger_on_extruding
					,self.Snapshot.timer_trigger_on_primed
					,self.Snapshot.timer_trigger_on_retracting_start
					,self.Snapshot.timer_trigger_on_retracting
					,self.Snapshot.timer_trigger_on_partially_retracted
					,self.Snapshot.timer_trigger_on_retracted
					,self.Snapshot.timer_trigger_on_detracting_start
					,self.Snapshot.timer_trigger_on_detracting
					,self.Snapshot.timer_trigger_on_detracted)
			)

	def Reset(self):
		"""Reset state tracking information.  Does not reload any settings."""
		self.TriggerStartTime = None
		self.TriggeredCount = 0
		self.IsTriggered = False
		self.IsWaiting = False
		self.PauseTime = None

	def Pause(self):
		self.PauseTime = time.time()
		
	def PrintStarted(self):
		self.PrintStartTime = time.time()

	def Update(self,position):

		self.IsTriggered = False
		# Don't update the trigger if we don't have a homed axis
		# Make sure to use the previous value so the homing operation can complete
		if(not position.HasHomedAxis(1)):
			self.IsTriggered = False
			return


		# record the current time to keep things consistant
		currentTime = time.time()

		# if the trigger start time is null, set it now.
		if(self.TriggerStartTime is None):
			self.TriggerStartTime = currentTime

		if(self.PauseTime is not None):
			newLastTriggerTime = currentTime - (self.PauseTime - self.TriggerStartTime)
			self.Settings.CurrentDebugProfile().LogTimerTriggerUnpaused("Time Trigger - Unpausing.  LastTriggerTime:{0}, PauseTime:{1}, CurrentTime:{2}, NewTriggerTime:{3} ".format(self.TriggerStartTime, self.PauseTime, currentTime, newLastTriggerTime))
			# Keep the proper interval if the print is paused
			self.TriggerStartTime = newLastTriggerTime 
			self.PauseTime = None

		self.Settings.CurrentDebugProfile().LogTriggerTimeRemaining('TimerTrigger - {0} second interval, {1} seconds elapsed, {2} seconds to trigger'.format(self.IntervalSeconds,int(currentTime-self.TriggerStartTime), int(self.IntervalSeconds- (currentTime-self.TriggerStartTime))))
		# see if enough time has elapsed since the last trigger 
		if(currentTime - self.TriggerStartTime > self.IntervalSeconds):
			self.IsWaiting = True
			# see if the exturder is in the right position
			if(position.Extruder.IsTriggered(self.ExtruderTriggers)):
				if(self.RequireZHop and not position.IsZHop(1)):
					self.Settings.CurrentDebugProfile().LogTriggerWaitState("GcodeTrigger - Waiting on ZHop.")
					
				else:
					# triggered!  Update the counter
					self.TriggeredCount += 1
					#Set the trigger start time to 0 so that it resets after the next command
					self.TriggerStartTime = None
					# return true
					self.IsTriggered = True
					self.Settings.CurrentDebugProfile().LogTriggering('TimerTrigger - Triggering.')
					self.IsWaiting = False
			else:
				self.Settings.CurrentDebugProfile().LogTriggerWaitState('TimerTrigger - Triggering, waiting for extruder')


		
