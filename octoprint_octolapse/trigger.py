# coding=utf-8
from .position import *
from .gcode import *
from .settings import *

import utility
import time




class GcodeTrigger(object):
	"""Used to monitor gcode for a specified command."""
	def __init__(self, octolapseSettings ):
		self.Settings = octolapseSettings
		self.Printer = self.Settings.CurrentPrinter()
		self.Snapshot = self.Settings.CurrentSnapshot()
		self.IsTriggered = False
		self.IsWaiting = False
		self.RequireZHop = self.Snapshot.gcode_trigger_require_zhop
		self.ExtruderTriggers = ExtruderTriggers(self.Snapshot.gcode_trigger_on_extruding
				,self.Snapshot.gcode_trigger_on_extruding_start
				,self.Snapshot.gcode_trigger_on_primed
				,self.Snapshot.gcode_trigger_on_retracting
				,self.Snapshot.gcode_trigger_on_retracted
				,self.Snapshot.gcode_trigger_on_detracting)
		self.Settings.CurrentDebugProfile().LogTriggerCreate("Creating Gcode Trigger - Gcode Command:{0}, RequireZHop:{1}".format(self.Printer.snapshot_command, self.Snapshot.gcode_trigger_require_zhop))
		self.Settings.CurrentDebugProfile().LogTriggerCreate("Extruder Triggers - On Extruding:{0}, On Extruding Start:{1}, On Primed:{2}, On Retracting:{3}, On Retracted:{4}, On Detracting:{5}"
				.format(self.Snapshot.gcode_trigger_on_extruding
					,self.Snapshot.gcode_trigger_on_extruding_start
					,self.Snapshot.gcode_trigger_on_primed
					,self.Snapshot.gcode_trigger_on_retracting
					,self.Snapshot.gcode_trigger_on_retracted
					,self.Snapshot.gcode_trigger_on_detracting)
			)
	def Reset(self):
		self.IsTriggered = False
		self.HasSeenCode = False
		self.IsWaiting = False
	def Update(self, position,commandName):
		"""If the provided command matches the trigger command, sets IsTriggered to true, else false"""
		self.IsTriggered = False
		# Don't update the trigger if we don't have a homed axis
		if(not position.HasHomedAxis):
			self.IsTriggered = False
			return

		if (self.IsSnapshotCommand(commandName)):
			self.IsWaiting = True
		if(self.IsWaiting == True):
			if(position.Extruder.IsTriggered(self.ExtruderTriggers)):
				if(self.RequireZHop and not position.IsZHop):
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
				self.Snapshot.layer_trigger_on_extruding
				,self.Snapshot.layer_trigger_on_extruding_start
				,self.Snapshot.layer_trigger_on_primed
				,self.Snapshot.layer_trigger_on_retracting
				,self.Snapshot.layer_trigger_on_retracted
				,self.Snapshot.layer_trigger_on_detracting)
		# Configuration Variables
		self.RequireZHop = self.Snapshot.layer_trigger_require_zhop
		self.HeightIncrement = self.Snapshot.layer_trigger_height
		if(self.HeightIncrement == 0):
			self.HeightIncrement = None
		# State Tracking Vars
		self.IsWaiting = False
		self.IsTriggered = False
		self.IsHeightChange = False
		# private flags
		self.__LayerChangeWait = False
		self.__HeightChangeWait = False
		self.Settings.CurrentDebugProfile().LogTriggerCreate("Creating Layer Trigger - TriggerHeight:{0} (none = layer change), RequiresZHop:{1}".format(self.Snapshot.layer_trigger_height, self.Snapshot.layer_trigger_require_zhop))
		self.Settings.CurrentDebugProfile().LogTriggerCreate("Extruder Triggers - On Extruding:{0}, On Extruding Start:{1}, On Primed:{2}, On Retracting:{3}, On Retracted:{4}, On Detracting:{5}"
				.format(
					self.Snapshot.layer_trigger_on_extruding
					,self.Snapshot.layer_trigger_on_extruding_start
					,self.Snapshot.layer_trigger_on_primed
					,self.Snapshot.layer_trigger_on_retracting
					,self.Snapshot.layer_trigger_on_retracted
					,self.Snapshot.layer_trigger_on_detracting)
			)
			

	def Reset(self):
		"""Resets all state tracking variables and flags.  Does not change the settings (ZMin, HeightIncrement)"""
		self.IsWaiting = False
		self.IsTriggered = False
		self.IsHeightChange = False
		# private flags
		self.__LayerChangeWait = False
		self.__HeightChangeWait = False

	def Update(self, position):
		"""Updates the layer monitor position.  x, y and z may be absolute, but e must always be relative"""
		self.IsTriggered = False
		# Don't update the trigger if we don't have a homed axis
		if(not position.HasHomedAxis):
			self.IsTriggered = False
			return

		# calculate height increment changed
		if(self.HeightIncrement is not None and self.HeightIncrement> 0 and position.IsLayerChange and position.Height // self.HeightIncrement > self.HeightIncrement):
			self.HeightIncrement += 1
			self.IsHeightChange  = True
			self.Settings.CurrentDebugProfile().LogTriggerHeightChange("Layer Trigger - Height Increment:{0}".format(self.HeightIncrement))
		else:
			self.IsHeightChange = False

		# see if we've encountered a layer or height change
		if(self.HeightIncrement is not None and self.HeightIncrement > 0):
			if(self.IsHeightChange):
				self.__HeightChangeWait = True
				
		else:
			if(position.IsLayerChange):
				self.__LayerChangeWait = True

		
		# see if the extruder is triggering
		isExtruderTriggering = position.Extruder.IsTriggered(self.ExtruderTriggers)

		if(self.__HeightChangeWait or self.__LayerChangeWait):
			self.IsWaiting = True
			if(not isExtruderTriggering):
				if(self.__HeightChangeWait):
					self.Settings.CurrentDebugProfile().LogTriggerWaitState("LayerTrigger - Height change triggering, waiting on extruder.")
				elif (self.__LayerChangeWait):
					self.Settings.CurrentDebugProfile().LogTriggering("LayerTrigger - Layer change triggering, waiting on extruder.")
			else:
				if(self.RequireZHop and not position.IsZHop):
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
				self.Snapshot.timer_trigger_on_extruding
				,self.Snapshot.timer_trigger_on_extruding_start
				,self.Snapshot.timer_trigger_on_primed
				,self.Snapshot.timer_trigger_on_retracting
				,self.Snapshot.timer_trigger_on_retracted
				,self.Snapshot.timer_trigger_on_detracting)
		self.IntervalSeconds = self.Snapshot.timer_trigger_seconds
		self.RequireZHop = self.Snapshot.timer_trigger_require_zhop
		self.LastTriggerTime = None
		self.IntervalSeconds = self.Snapshot.timer_trigger_seconds
		self.TriggeredCount = 0
		self.IsTriggered = False
		self.IsWaiting = False
		self.PauseTime = None

		self.Settings.CurrentDebugProfile().LogTriggerCreate("Creating Timer Trigger - Seconds:{0}, RequireZHop:{1}".format(self.Snapshot.timer_trigger_seconds, self.Snapshot.timer_trigger_require_zhop))
		self.Settings.CurrentDebugProfile().LogTriggerCreate("Extruder Triggers - On Extruding:{0}, On Extruding Start:{1}, On Primed:{2}, On Retracting:{3}, On Retracted:{4}, On Detracting:{5}"
				.format(
					self.Snapshot.timer_trigger_on_extruding
					,self.Snapshot.timer_trigger_on_extruding_start
					,self.Snapshot.timer_trigger_on_primed
					,self.Snapshot.timer_trigger_on_retracting
					,self.Snapshot.timer_trigger_on_retracted
					,self.Snapshot.timer_trigger_on_detracting)
			)
			#Configure the extruder triggers
	def Pause(self):
		self.PauseTime = time.time()
		
	def PrintStarted(self):
		self.PrintStartTime = time.time()

	def Update(self,position):

		self.IsTriggered = False
		# Don't update the trigger if we don't have a homed axis
		if(not position.HasHomedAxis):
			self.IsTriggered = False
			return


		# record the current time to keep things consistant
		currentTime = time.time()

		# if the last trigger time is null, set it now.
		if(self.LastTriggerTime is None):
			self.LastTriggerTime = currentTime

		if(self.PauseTime is not None):
			newLastTriggerTime = currentTime - (self.PauseTime - self.LastTriggerTime)
			self.Settings.CurrentDebugProfile().LogTimerTriggerUnpaused("Time Trigger - Unpausing.  LastTriggerTime:{0}, PauseTime:{1}, CurrentTime:{2}, NewTriggerTime:{3} ".format(self.LastTriggerTime, self.PauseTime, currentTime, newLastTriggerTime))
			# Keep the proper interval if the print is paused
			self.LastTriggerTime = newLastTriggerTime 
			self.PauseTime = None

		self.Settings.CurrentDebugProfile().LogTriggerTimeRemaining('TimerTrigger - {0} second interval, {1} seconds elapsed, {2} seconds to trigger'.format(self.IntervalSeconds,int(currentTime-self.LastTriggerTime), int(self.IntervalSeconds- (currentTime-self.LastTriggerTime))))
		# see if enough time has elapsed since the last trigger 
		if(currentTime - self.LastTriggerTime > self.IntervalSeconds):
			
			# see if the exturder is in the right position
			if(position.Extruder.IsTriggered(self.ExtruderTriggers)):
				if(self.RequireZHop and not position.IsZHop):
					self.Settings.CurrentDebugProfile().LogTriggerWaitState("GcodeTrigger - Waiting on ZHop.")
				else:
					# triggered!  Update the counter
					self.TriggeredCount += 1
					# Update the last trigger time.
					self.LastTriggerTime = currentTime
					# return true
					self.IsTriggered = True
					self.Settings.CurrentDebugProfile().LogTriggering('TimerTrigger - Triggering.')
					self.IsWaiting = False
			else:
				self.IsWaiting = True
				self.Settings.CurrentDebugProfile().LogTriggerWaitState('TimerTrigger - Triggering, waiting for extruder')

	# used to reset the triggers, if we want to do that for any reason.
	def Reset(self):
		self.IsTriggered=False
		self.LastTriggerTime = None
		self.IsWaiting = False
		
