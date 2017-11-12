from .extruder import *
import time

class GcodeTrigger(object):
	"""Used to monitor gcode for a specified command."""
	def __init__(self, command,extruderTriggers):
		self.Extruder = Extruder()
		
		self.IsTriggered = False
		self.Command = command
		self.IsTriggered = False
		self.HasSeenCode = False
		self.ExtruderTriggers = extruderTriggers

	def Reset():
		self.IsTriggered = False
		self.HasSeenCode = False

	def Update(self, command, e):
		"""If the provided command matches the trigger command, sets IsTriggered to true, else false"""
		self.IsTriggered = False
		command = gcode.GetGcodeFromString(command)
		if (command == self.Command):
			self.HasSeenCode = True

		if(self.HasSeenCode == True and self.Extruder.IsTriggered(self.ExtruderTriggers)):
			IsTriggered = True
			self.HasSeenCode = False

class LayerTrigger(object):
	
	def __init__( self,extruderTriggers, zMin, heightIncrement = None ):
		#utilities and profiles
		self.Extruder = Extruder()
		self.ExtruderTriggers = extruderTriggers
		# Configuration Variables
		self.ZMin = zMin
		self.HeightIncrement = heightIncrement
		# State Tracking Vars
		self.Height = 0
		self.__HeightPrevious = 0
		self.ZDelta = None
		self.__ZDeltaPrevious = None
		self.Layer = 0
		self.HasReachedZMin = False
		self.MaxHeightIncrement = None
		# State Flags
		self.IsLayerChange = False
		self.HasHeightIncrementChanged = False

	def Reset(self):
		"""Resets all state tracking variables and flags.  Does not change the settings (ZMin, HeightIncrement)"""
		# State Tracking Vars
		self.Height = 0
		self.__HeightPrevious = 0
		self.ZDelta = None
		self.__ZDeltaPrevious = None
		self.Layer = 0
		self.HasReachedZMin = False
		self.MaxHeightIncrement = 0
		# State Flags
		self.IsLayerChange = False
		self.IsHeightChanged = False

	def IsTriggered(self):
		if(self.HeightIncrement is None):
			return self.IsLayerChange
		else:
			return self.IsHeightChanged
			
	def Update(self, e):
		"""Updates the layer monitor position.  x, y and z may be absolute, but e must always be relative"""

		# Update the extruder monitor
		# This must be done every time, so do it first
		self.Extruder.Update(e)

		# set the current position type, if supplied
		if(isRelative is not None):
			position.IsRelative = isRelative
		# update any positions that may have changed
		position.Update(position.X,position.Y,position.Z,position.E)

		# save any previous values that will be needed later
		self.__HeightPrevious = self.Height
		self.__ZDeltaPrevious = self.ZDelta


		# determine if we've reached ZMin
		if(position.Z <= self.ZMin):
			self.HasReachedZMin = True

		# calculate Height
		if self.Extruder.IsTriggered(self.ExtruderTriggers) and self.HasReachedZMin and position.Z > self.Height:
			self.Height = position.Z

		# calculate ZDelta
		self.ZDelta = self.Height - self.__HeightPrevious

		# calculate layer change
		if(self.__HeightPrevious < self.Height):
			self.IsLayerChange = True
			self.Layer += 1
		else:
			self.IsLayerChange = False

		# calculate height increment changed
		if(self.HeightIncrement is not null and self.HeightIncrement> 0 and self.IsLayerChange and self.Height // self.HeightIncrement > self.HeightIncrement):
			self.HeightIncrement += 1
			self.HasHeightIncrementChanged = True
		else:
			self.HasHeightIncrementChanged = False

class TimerTrigger(object):
	
	def __init__(self,intervalSeconds,extruderTriggers):
		self.ExtruderTriggers = extruderTriggers
		self.IntervalSeconds = intervalSeconds
		self.Extruder = Extruder()
		self.LastTriggerTime = None
		self.IntervalSeconds = 60.0
		self.TriggeredCount = 0
		self.IsTriggered = False
		self.PauseTime = None
	def Pause(self):
		self.PauseTime = time.time()
		
	def PrintStarted(self):
		self.PrintStartTime = time.time()

	def Update(self,e):
		# record the current time to keep things consistant
		currentTime = time.time()
		# update the exturder
		self.Extruder.Update(e)
		# if the last trigger time is null, set it now.
		if(self.LastTriggerTime is None):
			self.LastTriggerTime = currentTime

		if(self.PauseTime is not None):
			# Keep the proper interval if the print is paused
			self.LastTriggerTime = currentTime - (self.PauseTime - self.LastTriggerTime)
		
		# see if enough time has elapsed since the last trigger 
		if(currentTime - lastTriggerTime > self.IntervalSeconds):
			# see if the exturder is in the right position
			if(self.Extruder.IsTriggered(self.ExtruderTriggers)):
				# triggered!  Update the counter
				self.TriggeredCount += 1
				# Update the last trigger time.
				self.LastTriggerTime = currentTime
				# return true
				IsTriggered = True
	# used to reset the triggers, if we want to do that for any reason.
	def Reset(self):
		self.IsTriggered=False
		LastTriggerTime = None
