# coding=utf-8
from .position import *
from .gcode import *
from .settings import *
import utility
import time


def IsTriggering(triggers,position,cmd,debug):

	# check the command to see if it's a debug assrt

	# Loop through all of the active currentTriggers
	for currentTrigger in triggers:
		# determine what type the current trigger is and update appropriately
		if(isinstance(currentTrigger,GcodeTrigger)):
			currentTrigger.Update(position,cmd)
		elif(isinstance(currentTrigger,TimerTrigger)):
			currentTrigger.Update(position)
		elif(isinstance(currentTrigger,LayerTrigger)):
			currentTrigger.Update(position)
		# see if the current trigger is triggering, indicting that a snapshot should be taken
		if(currentTrigger.IsTriggered):
			# Make sure there are no position errors (unknown position, out of bounds, etc)
			if(not position.HasPositionError):
				#Triggering!
				return currentTrigger
			else:
				debug.LogError("A position error prevented a trigger!")
	return None
def IsSnapshotCommand(command, snapshotCommand):
		commandName = GetGcodeFromString(command)
		snapshotCommandName = GetGcodeFromString(snapshotCommand)
		return commandName == snapshotCommandName
class GcodeTrigger(object):
	"""Used to monitor gcode for a specified command."""
	def __init__(self, extruderTriggers, debugSettings,command,requireZHop):
		
		self.Debug = debugSettings
		self.IsTriggered = False
		self.Command = command
		self.IsTriggered = False
		self.IsWaiting = False
		self.ExtruderTriggers = extruderTriggers
		self.RequireZHop = requireZHop
	
	def Reset(self):
		self.IsTriggered = False
		self.HasSeenCode = False
		self.IsWaiting = False
	def Update(self, position,commandName):
		"""If the provided command matches the trigger command, sets IsTriggered to true, else false"""
		self.IsTriggered = False
		if (IsSnapshotCommand(commandName,self.Command)):
			self.IsWaiting = True
		if(self.IsWaiting == True):

			if(position.Extruder.IsTriggered(self.ExtruderTriggers)):
				if(self.RequireZHop and not position.IsZHop):
					self.Debug.LogTriggerWaitState("GcodeTrigger - Waiting on ZHop.")
				else:
					self.IsTriggered = True
					self.IsWaiting = False
					self.Debug.LogTriggering("GcodeTrigger - Waiting for extruder to trigger.")
			else:
				self.Debug.LogTriggerWaitState("GcodeTrigger - Waiting for extruder to trigger.")

class LayerTrigger(object):
	
	def __init__( self,extruderTriggers, debugSettings, requireZHop, heightIncrement ):
		#utilities and profiles
		self.Debug = debugSettings
		self.ExtruderTriggers = extruderTriggers
		# Configuration Variables
		
		
		self.RequireZHop = requireZHop

		
		self.HeightIncrement = heightIncrement
		if(heightIncrement == 0):
			self.HeightIncrement = None
		
		# State Tracking Vars
		self.IsWaiting = False
		self.IsTriggered = False
		self.IsHeightChange = False
		# private flags
		self.__LayerChangeWait = False
		self.__HeightChangeWait = False

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
		
		

		# calculate height increment changed
		if(self.HeightIncrement is not None and self.HeightIncrement> 0 and position.IsLayerChange and position.Height // self.HeightIncrement > self.HeightIncrement):
			self.HeightIncrement += 1
			self.IsHeightChange  = True
			self.Debug.LogTriggerHeightChange("Layer Trigger - Height Increment:{0}".format(self.HeightIncrement))
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
					self.Debug.LogTriggerWaitState("LayerTrigger - Height change triggering, waiting on extruder.")
				elif (self.__LayerChangeWait):
					self.Debug.LogTriggering("LayerTrigger - Layer change triggering, waiting on extruder.")
			else:
				if(self.RequireZHop and not position.IsZHop):
					self.Debug.LogTriggerWaitState("LayerTrigger - Triggering - Waiting on ZHop.")
					return
				if(self.__HeightChangeWait):
					self.Debug.LogTriggering("LayerTrigger - Height change triggering.")
				elif (self.__LayerChangeWait):
					self.Debug.LogTriggering("LayerTrigger - Layer change triggering.")
				self.__LayerChangeWait = False
				self.__HeightChangeWait = False
				self.IsTriggered = True
				self.IsWaiting = False

class TimerTrigger(object):
	
	def __init__(self,extruderTriggers,debugSettings,intervalSeconds,requireZHop):
		self.Debug = debugSettings
		self.ExtruderTriggers = extruderTriggers
		self.IntervalSeconds = intervalSeconds
		self.RequireZHop = requireZHop
		self.LastTriggerTime = None
		self.IntervalSeconds = intervalSeconds
		self.TriggeredCount = 0
		self.IsTriggered = False
		self.IsWaiting = False
		self.PauseTime = None
	def Pause(self):
		self.PauseTime = time.time()
		
	def PrintStarted(self):
		self.PrintStartTime = time.time()

	def Update(self,position):

		# reset the state flags
		self.IsTriggered = False

		# record the current time to keep things consistant
		currentTime = time.time()

		# if the last trigger time is null, set it now.
		if(self.LastTriggerTime is None):
			self.LastTriggerTime = currentTime

		if(self.PauseTime is not None):
			newLastTriggerTime = currentTime - (self.PauseTime - self.LastTriggerTime)
			self.Debug.LogTimerTriggerUnpaused("Time Trigger - Unpausing.  LastTriggerTime:{0}, PauseTime:{1}, CurrentTime:{2}, NewTriggerTime:{3} ".format(self.LastTriggerTime, self.PauseTime, currentTime, newLastTriggerTime))
			# Keep the proper interval if the print is paused
			self.LastTriggerTime = newLastTriggerTime 
			self.PauseTime = None

		self.Debug.LogTriggerTimeRemaining('TimerTrigger - {0} second interval, {1} seconds elapsed, {2} seconds to trigger'.format(self.IntervalSeconds,int(currentTime-self.LastTriggerTime), int(self.IntervalSeconds- (currentTime-self.LastTriggerTime))))
		# see if enough time has elapsed since the last trigger 
		if(currentTime - self.LastTriggerTime > self.IntervalSeconds):
			
			# see if the exturder is in the right position
			if(position.Extruder.IsTriggered(self.ExtruderTriggers)):
				if(self.RequireZHop and not position.IsZHop):
					self.Debug.LogTriggerWaitState("GcodeTrigger - Waiting on ZHop.")
				else:
					# triggered!  Update the counter
					self.TriggeredCount += 1
					# Update the last trigger time.
					self.LastTriggerTime = currentTime
					# return true
					self.IsTriggered = True
					self.Debug.LogTriggering('TimerTrigger - Triggering.')
					self.IsWaiting = False
			else:
				self.IsWaiting = True
				self.Debug.LogTriggerWaitState('TimerTrigger - Triggering, waiting for extruder')

	# used to reset the triggers, if we want to do that for any reason.
	def Reset(self):
		self.IsTriggered=False
		self.LastTriggerTime = None
		self.IsWaiting = False
		
