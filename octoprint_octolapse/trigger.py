
# coding=utf-8
from octoprint_octolapse.position import *
from octoprint_octolapse.extruder import ExtruderTriggers
from octoprint_octolapse.gcode import *
from octoprint_octolapse.command import *
from octoprint_octolapse.settings import *
import octoprint_octolapse.utility 
import time
import sys
class Triggers(object):
	def __init__(self, settings):
		self.Reset()
		self.Settings = settings
		self.Name = "Unknown"
	def Count(self):
		try:
			return len(self._triggers)
		except Exception, e:
			self.Settings.CurrentDebugProfile().LogException(e)
			
	def Reset(self):
		self._triggers = []
		self.Snapshot = None
	def Create(self):
		try:
			self.Reset()
			self.Printer = self.Settings.CurrentPrinter()
			self.Snapshot = self.Settings.CurrentSnapshot()
			self.Name = self.Snapshot.name
			# create the triggers
			# If the gcode trigger is enabled, add it
			if(self.Snapshot.gcode_trigger_enabled):
				#Add the trigger to the list
				self._triggers.append(GcodeTrigger(self.Settings))
			# If the layer trigger is enabled, add it
			if(self.Snapshot.layer_trigger_enabled):
				self._triggers.append(LayerTrigger(self.Settings))
			# If the layer trigger is enabled, add it
			if(self.Snapshot.timer_trigger_enabled):
				self._triggers.append(TimerTrigger(self.Settings))
		except Exception as e:
			self.Settings.CurrentDebugProfile().LogException(e)

	def Resume(self):
		try:
			for trigger in self._triggers:
				if(type(trigger) == TimerTrigger):
					trigger.Resume()
		except Exception, e:
			self.Settings.CurrentDebugProfile().LogException(e)
	def Pause(self):
		try:
			for trigger in self._triggers:
				if(type(trigger) == TimerTrigger):
					trigger.Pause()
		except Exception, e:
			self.Settings.CurrentDebugProfile().LogException(e)
	def Update(self, position, cmd):
		"""Update all triggers and return any that are triggering"""
		try:
			# Loop through all of the active currentTriggers
			for currentTrigger in self._triggers:
				# determine what type the current trigger is and update appropriately
				if(isinstance(currentTrigger,GcodeTrigger)):
					currentTrigger.Update(position,cmd)
				elif(isinstance(currentTrigger,TimerTrigger)):
					currentTrigger.Update(position)
				elif(isinstance(currentTrigger,LayerTrigger)):
					currentTrigger.Update(position)

				# Make sure there are no position errors (unknown position, out of bounds, etc)
				if(position.HasPositionError()):
					self.Settings.CurrentDebugProfile().LogError("A trigger has a position error:{0}".format(position.PositionError))
				# see if the current trigger is triggering, indicting that a snapshot should be taken
		except Exception, e:
			self.Settings.CurrentDebugProfile().LogException(e)

		return None
	def GetFirstTriggering(self):
		try:
			# Loop through all of the active currentTriggers
			for currentTrigger in self._triggers:
				if(currentTrigger.IsTriggered(0)):
					return currentTrigger
		except Exception, e:
			self.Settings.CurrentDebugProfile().LogException(e)

	def GetFirstWaiting(self):
		try:
			# Loop through all of the active currentTriggers
			for currentTrigger in self._triggers:
				if(currentTrigger.IsWaiting(0)):
					return currentTrigger
		except Exception, e:
			self.Settings.CurrentDebugProfile().LogException(e)
	def HasChanged(self):
		try:
			# Loop through all of the active currentTriggers
			for currentTrigger in self._triggers:
				if(currentTrigger.HasChanged(0)):
					return True
		except Exception, e:
			self.Settings.CurrentDebugProfile().LogException(e)
			return None
		return False
	def StateToList(self):
		stateList = []
		try:
			# Loop through all of the active currentTriggers
			for currentTrigger in self._triggers:
				stateList.append(currentTrigger.ToDict(0))
		except Exception, e:
			self.Settings.CurrentDebugProfile().LogException(e)
			return None
		return stateList
	def ChangesToList(self):
		changeList = []
		try:
			# Loop through all of the active currentTriggers
			for currentTrigger in self._triggers:
				if(currentTrigger.HasChanged(0)):
					changeList.append(currentTrigger.ToDict(0))
		except Exception, e:
			self.Settings.CurrentDebugProfile().LogException(e)
			return None
		return changeList
class TriggerState(object):
	def __init__(self, state = None):
		self.IsTriggered = False if state is None else state.IsTriggered
		self.IsWaiting = False if state is None else state.IsWaiting
		self.IsWaitingOnZHop = False if state is None else state.IsWaitingOnZHop
		self.IsWaitingOnExtruder = False if state is None else state.IsWaitingOnExtruder
		self.HasChanged = False if state is None else state.HasChanged
		self.IsHomed = False if state is None else state.IsHomed
	def ToDict(self, trigger):
		return {
				"IsTriggered": self.IsTriggered
				,"IsWaiting": self.IsWaiting
				,"IsWaitingOnZHop": self.IsWaitingOnZHop
				,"IsWaitingOnExtruder": self.IsWaitingOnExtruder
				,"HasChanged": self.HasChanged
				,"RequireZHop": trigger.RequireZHop
				,"IsHomed" : self.IsHomed
				,"TriggeredCount" : trigger.TriggeredCount
			}
	def ResetState(self):
		self.IsTriggered = False
		self.HasChanged = False
		
		
	def IsEqual(self,state):
		if(state is not None
			and self.IsTriggered == state.IsTriggered
			and self.IsWaiting == state.IsWaiting
			and self.IsWaitingOnZHop == state.IsWaitingOnZHop
			and self.IsWaitingOnExtruder == state.IsWaitingOnExtruder
			and self.IsHomed == state.IsHomed):
			return True
		return False

class Trigger(object):
	def __init__(self, octolapseSettings,maxStates=5):
		self.Settings = octolapseSettings
		self.Printer = Printer(self.Settings.CurrentPrinter())
		self.Snapshot = Snapshot(self.Settings.CurrentSnapshot())
		self.Type = 'Trigger'
		self._stateHistory = []
		self._maxStates = maxStates
		self.ExtruderTriggers = None
		self.TriggeredCount = 0
	def Name(self):
		return self.Snapshot.name + " Trigger"
	
	def AddState(self,state):
		self._stateHistory.insert(0,state)
		while (len(self._stateHistory)> self._maxStates):
			del self._stateHistory[self._maxStates]
	
	def Count(self):
		return len(self._stateHistory)
	def GetState(self, index):
		if(self.Count()>index):
			return self._stateHistory[index]
		return None
	def IsTriggered(self, index):
		state = self.GetState(index)
		if(state is None):
			return False
		return state.IsTriggered
	def IsWaiting(self, index):
		state = self.GetState(index)
		if(state is None):
			return
		return state.IsWaiting
	def HasChanged(self, index):
		state = self.GetState(index)
		if(state is None):
			return
		return state.HasChanged
	def ToDict(self, index):
		state = self.GetState(index)
		if(state is None):
			return None
		stateDict = state.ToDict(self)
		stateDict.update({"Name" : self.Name(), "Type" : self.Type})
		return stateDict
class GcodeTriggerState(TriggerState):
	def ToDict(self, trigger):
		superDict = super(GcodeTriggerState,self).ToDict(trigger)
		currentDict = {
				"SnapshotCommand": trigger.SnapshotCommand
			}
		currentDict.update(superDict)
		return currentDict

class GcodeTrigger(Trigger):
	"""Used to monitor gcode for a specified command."""
	def __init__(self, octolapseSettings ):
		# call parent constructor
		super(GcodeTrigger,self).__init__(octolapseSettings)
		self.SnapshotCommand = GetGcodeFromString(self.Printer.snapshot_command)
		self.Type = "gcode"
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
		# add an initial state
		self.AddState(GcodeTriggerState())
	def Update(self, position,commandName):
		"""If the provided command matches the trigger command, sets IsTriggered to true, else false"""
		try:
			# get the last state to use as a starting point for the update
			# if there is no state, this will return the default state
			state = self.GetState(0)
			if(state is None):
				# create a new object, it's our first state!
				state = GcodeTriggerState()
			else:
				# create a copy so we aren't working on the original
				state = GcodeTriggerState(state)
			# reset any variables that must be reset each update
			state.ResetState()
			# Don't update the trigger if we don't have a homed axis
			# Make sure to use the previous value so the homing operation can complete
			if(not position.HasHomedAxis(1)):
				state.IsTriggered = False
				state.IsHomed = False
				return
			state.IsHomed = True

			if (self.IsSnapshotCommand(commandName)):
				state.IsWaiting = True
			if(state.IsWaiting == True):
				if(position.Extruder.IsTriggered(self.ExtruderTriggers)):
					if(self.RequireZHop and not position.IsZHop(1)):
						state.IsWaitingOnZHop = True
						self.Settings.CurrentDebugProfile().LogTriggerWaitState("GcodeTrigger - Waiting on ZHop.")
					else:
						state.IsTriggered = True
						state.IsWaiting = False
						state.IsWaitingOnZHop = False
						state.IsWaitingOnExtruder = False
						self.TriggeredCount += 1
					
						self.Settings.CurrentDebugProfile().LogTriggering("GcodeTrigger - Waiting for extruder to trigger.")
				else:
					state.IsWaitingOnExtruder = True
					self.Settings.CurrentDebugProfile().LogTriggerWaitState("GcodeTrigger - Waiting for extruder to trigger.")

			# calculate changes and set the current state
			state.HasChanged = not state.IsEqual(self.GetState(0))

			# add the state to the history
			self.AddState(state)
		except Exception as e:
			self.Settings.CurrentDebugProfile().LogException(e)
	def IsSnapshotCommand(self, command):
		commandName = GetGcodeFromString(command)
		return commandName == self.SnapshotCommand

class LayerTriggerState(TriggerState):
	def __init__(self, state = None):
		# call parent constructor
		super(LayerTriggerState,self).__init__()
		self.CurrentIncrement = 0 if state is None else state.CurrentIncrement
		self.IsLayerChangeWait = False if state is None else state.IsLayerChangeWait
		self.IsHeightChange = False if state is None else state.IsHeightChange
		self.IsHeightChangeWait = False if state is None else state.IsHeightChangeWait
	def ToDict(self, trigger):
		superDict = super(LayerTriggerState,self).ToDict(trigger)
		currentDict = {
				"CurrentIncrement": self.CurrentIncrement,
				"IsLayerChangeWait": self.IsLayerChangeWait,
				"IsHeightChange": self.IsHeightChange,
				"IsHeightChangeWait": self.IsHeightChangeWait,
				"HeightIncrement": trigger.HeightIncrement
			}
		currentDict.update(superDict)
		return currentDict
	def ResetState(self):
		super(LayerTriggerState,self).ResetState()
		self.IsHeightChange = False
		self.IsLayerChange = False
	def IsEqual(self,state):
		if (super(LayerTriggerState,self).IsEqual(state)
				and self.CurrentIncrement == state.CurrentIncrement 
				and self.IsLayerChangeWait == state.IsLayerChangeWait
				and self.IsHeightChange == state.IsHeightChange
				and self.IsHeightChangeWait == state.IsHeightChangeWait
				
			):
			return True
		return False
	
class LayerTrigger(Trigger):
	
	def __init__( self,octolapseSettings):
		super(LayerTrigger,self).__init__(octolapseSettings)
		self.Type = "layer"
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
		self.AddState(LayerTriggerState())

	def Update(self, position):
		"""Updates the layer monitor position.  x, y and z may be absolute, but e must always be relative"""
		try:
			# get the last state to use as a starting point for the update
			# if there is no state, this will return the default state
			state = self.GetState(0)
			if(state is None):
				# create a new object, it's our first state!
				state = LayerTriggerState()
			else:
				# create a copy so we aren't working on the original
				state = LayerTriggerState(state)

			# reset any variables that must be reset each update
			state.ResetState()
			# Don't update the trigger if we don't have a homed axis
			# Make sure to use the previous value so the homing operation can complete
			if(not position.HasHomedAxis(1)):
				state.IsTriggered = False
				state.IsHomed = False
				return
			state.IsHomed = True

			# calculate height increment changed
		
			if(self.HeightIncrement is not None and self.HeightIncrement> 0 and position.IsLayerChange(1)
				and state.CurrentIncrement * self.HeightIncrement <= position.Height(1)):
				state.CurrentIncrement += 1
				state.IsHeightChange  = True

				self.Settings.CurrentDebugProfile().LogTriggerHeightChange("Layer Trigger - Height Increment:{0}, Current Increment".format(self.HeightIncrement, state.CurrentIncrement))

			# see if we've encountered a layer or height change
			if(self.HeightIncrement is not None and self.HeightIncrement > 0):
				if(state.IsHeightChange):
					state.IsHeightChangeWait = True
					state.IsWaiting = True
				
			else:
				if(position.IsLayerChange(1)):
					state.IsLayerChangeWait = True
					state.IsLayerChange = True
					state.IsWaiting = True

		
			# see if the extruder is triggering
			isExtruderTriggering = position.Extruder.IsTriggered(self.ExtruderTriggers)

			if(state.IsHeightChangeWait or state.IsLayerChangeWait or state.IsWaiting):
				state.IsWaiting = True
				if(not isExtruderTriggering):
					state.IsWaitingOnExtruder = True
					if(state.IsHeightChangeWait):
						self.Settings.CurrentDebugProfile().LogTriggerWaitState("LayerTrigger - Height change triggering, waiting on extruder.")
					elif (state.IsLayerChangeWait):
						self.Settings.CurrentDebugProfile().LogTriggering("LayerTrigger - Layer change triggering, waiting on extruder.")
				else:
					if(self.RequireZHop and not position.IsZHop(1)):
						state.IsWaitingOnZHop = True
						self.Settings.CurrentDebugProfile().LogTriggerWaitState("LayerTrigger - Triggering - Waiting on ZHop.")
						return
					if(state.IsHeightChangeWait):
						self.Settings.CurrentDebugProfile().LogTriggering("LayerTrigger - Height change triggering.")
					elif (state.IsLayerChangeWait):
						self.Settings.CurrentDebugProfile().LogTriggering("LayerTrigger - Layer change triggering.")

				
					self.TriggeredCount += 1
					state.IsTriggered = True
					state.IsLayerChangeWait = False
					state.IsLayerChange = False
					state.IsHeightChangeWait = False
					state.IsWaiting = False
					state.IsWaitingOnZHop = False
					state.IsWaitingOnExtruder = False
			
			# calculate changes and set the current state
			state.HasChanged = not state.IsEqual(self.GetState(0))
			# add the state to the history
			self.AddState(state)
		except Exception as e:
			self.Settings.CurrentDebugProfile().LogException(e)
			
class TimerTriggerState(TriggerState):
	def __init__(self, state = None):
		# call parent constructor
		super(TimerTriggerState,self).__init__()
		self.SecondsToTrigger = None if state is None else state.SecondsToTrigger
		self.TriggerStartTime = None if state is None else state.TriggerStartTime
		self.PauseTime = None if state is None else state.PauseTime
	def ToDict(self, trigger):
		superDict = super(TimerTriggerState,self).ToDict(trigger)
		currentDict = {
				"SecondsToTrigger": self.SecondsToTrigger
				,"TriggerStartTime": self.TriggerStartTime
				,"PauseTime": self.PauseTime
				,"IntervalSeconds": trigger.IntervalSeconds
			}
		currentDict.update(superDict)
		return currentDict
	def IsEqual(self,state):
		if (super(TimerTriggerState,self).IsEqual(state)
				and self.SecondsToTrigger == state.SecondsToTrigger
				and self.TriggerStartTime == state.TriggerStartTime
				and self.PauseTime == state.PauseTime
			):
			return True
		return False
class TimerTrigger(Trigger):
	
	def __init__(self,octolapseSettings):
		super(TimerTrigger,self).__init__(octolapseSettings)
		self.Type = "timer"
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
		# add initial state
		initialState = TimerTriggerState()
		self.AddState(initialState)
	def Pause(self):
		try:
			state = self.GetState(0)
			if(state is None):
				return
			state.PauseTime = time.time()
		except Exception as e:
			self.Settings.CurrentDebugProfile().LogException(e)

	def Resume(self):
		try:
			state = self.GetState(0)
			if(state is None):
				return
			if(state.PauseTime is not None):
				currentTime = time.time()
				newLastTriggerTime = currentTime - (state.PauseTime - state.TriggerStartTime)
				self.Settings.CurrentDebugProfile().LogTimerTriggerUnpaused("Time Trigger - Unpausing.  LastTriggerTime:{0}, PauseTime:{1}, CurrentTime:{2}, NewTriggerTime:{3} ".format(state.TriggerStartTime, state.PauseTime, currentTime, newLastTriggerTime))
				# Keep the proper interval if the print is paused
				state.TriggerStartTime = newLastTriggerTime 
				state.PauseTime = None
		except Exception as e:
			self.Settings.CurrentDebugProfile().LogException(e)

	def PrintStarted(self):
		state = self.TriggerState(self.GetState(0))
		state.PrintStartTime = time.time()
		# the state has definitely changed if we are here.
		state.HasChanged = True
		# add the state to the history
		self.AddState(state)

	def Update(self,position):
		try:
			# get the last state to use as a starting point for the update
			# if there is no state, this will return the default state
			state = self.GetState(0)
			if(state is None):
				# create a new object, it's our first state!
				state = TimerTriggerState()
			else:
				# create a copy so we aren't working on the original
				state = TimerTriggerState(state)
			# reset any variables that must be reset each update
			state.ResetState()
			state.IsTriggered = False

			# Don't update the trigger if we don't have a homed axis
			# Make sure to use the previous value so the homing operation can complete
			if(not position.HasHomedAxis(1)):
				state.IsTriggered = False
				state.IsHomed = False
				return
			state.IsHomed = True

			# record the current time to keep things consistant
			currentTime = time.time()

			# if the trigger start time is null, set it now.
			if(state.TriggerStartTime is None):
				state.TriggerStartTime = currentTime

			self.Settings.CurrentDebugProfile().LogTriggerTimeRemaining('TimerTrigger - {0} second interval, {1} seconds elapsed, {2} seconds to trigger'.format(self.IntervalSeconds,int(currentTime-state.TriggerStartTime), int(self.IntervalSeconds- (currentTime-state.TriggerStartTime))))

			# how many seconds to trigger
			secondsToTrigger = self.IntervalSeconds - (currentTime - state.TriggerStartTime)
			state.SecondsToTrigger = utility.round_to(secondsToTrigger,1)
			# see if enough time has elapsed since the last trigger 
			if(state.SecondsToTrigger <= 0):
				state.IsWaiting = True
				# see if the exturder is in the right position
				if(position.Extruder.IsTriggered(self.ExtruderTriggers)):
					if(self.RequireZHop and not position.IsZHop(1)):
						self.Settings.CurrentDebugProfile().LogTriggerWaitState("TimerTrigger - Waiting on ZHop.")
						state.IsWaitingOnZHop = True
					else:
						# Is Triggering
						self.TriggeredCount += 1
						state.IsTriggered = True
						state.TriggerStartTime = None
						state.IsWaitingOnZHop = False
						state.IsWaitingOnExtruder = False
						# Log trigger
						self.Settings.CurrentDebugProfile().LogTriggering('TimerTrigger - Triggering.')
					
				else:
					self.Settings.CurrentDebugProfile().LogTriggerWaitState('TimerTrigger - Triggering, waiting for extruder')
					state.IsWaitingOnExtruder = True
			# calculate changes and set the current state
			state.HasChanged = not state.IsEqual(self.GetState(0))
			# add the state to the history
			self.AddState(state)
		except Exception as e:
			self.Settings.CurrentDebugProfile().LogException(e)
