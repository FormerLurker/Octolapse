from .extruder import *
from .gcode import *
from .settings import *
import time

class GcodeTrigger(object):
	"""Used to monitor gcode for a specified command."""
	def __init__(self, extruderTriggers, command):
		self.Extruder = Extruder()
		self.IsTriggered = False
		self.Command = command
		self.IsTriggered = False
		self.__GcodeTriggerWait = False
		self.ExtruderTriggers = extruderTriggers

	def Reset():
		self.IsTriggered = False
		self.HasSeenCode = False
		self.Extruder.Reset()
	def Update(self, position,commandName):
		"""If the provided command matches the trigger command, sets IsTriggered to true, else false"""
		self.IsTriggered = False
		self.Extruder.Update(position.E)
		#print("Octolapse - TriggerCheck:{0:s} -  {1:s}".format(commandName,self.Command))
		if (commandName == self.Command):
			print("Octolapse - Snap Command Found")
			self.__GcodeTriggerWait = True
		if(self.__GcodeTriggerWait == True):
			if(self.Extruder.IsTriggered(self.ExtruderTriggers)):
				self.IsTriggered = True
				self.__GcodeTriggerWait = False
				print("Octolapse - Triggered!!!!!!!!!!!!!!!!!!!!!!!")
			else:
				print("Octolapse - Triggered, waiting for exturder ")

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
		self.IsHeightChange = False
		# private flags
		self.__LayerChangeWait = False
		self.__HeightChangeWait = False

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
		self.Extruder.Reset()

				
	def Update(self, position):
		"""Updates the layer monitor position.  x, y and z may be absolute, but e must always be relative"""

		self.IsLayerChange = False
		self.IsHeightChanged = False
		self.IsTriggered = False
		# Update the extruder monitor
		# This must be done every time, so do it first
		self.Extruder.Update(position.E)

		# save any previous values that will be needed later
		self.__HeightPrevious = self.Height
		self.__ZDeltaPrevious = self.ZDelta
		
		# determine if we've reached ZMin
		if(position.Z <= self.ZMin):
			self.HasReachedZMin = True

		# calculate Height
		if self.Extruder.IsExtruding and self.HasReachedZMin and position.Z > self.Height:
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
		if(self.HeightIncrement is not None and self.HeightIncrement> 0 and self.IsLayerChange and self.Height // self.HeightIncrement > self.HeightIncrement):
			self.HeightIncrement += 1
			self.IsHeightChange  = True
		else:
			self.IsHeightChange = False

		if(HeightIncrement is not None and HeightIncrement > 0):
			if(self.IsHeightChange):
				self.__HeightChangeWait = True
			if(self.__HeightChangeWait and self.Extruder.IsTriggered(self.ExtruderTriggers)):
				self.__HeightChangeWait = False
				self.IsTriggered = self.IsHeightChange
		else:
			if(self.IsLayerChange):
				self.__LayerChangeWait = True
			if(self.__LayerChangeWait and self.Extruder.IsTriggered(self.ExtruderTriggers)):
				self.__LayerChangeWait = False
				self.IsTriggered = self.IsLayerChange

class TimerTrigger(object):
	
	def __init__(self,extruderTriggers,intervalSeconds):
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

	def Update(self,position):

		# reset the state flags
		self.IsTriggered = False

		# record the current time to keep things consistant
		currentTime = time.time()
		# update the exturder
		self.Extruder.Update(position.E)
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
		self.Extruder.Reset()
