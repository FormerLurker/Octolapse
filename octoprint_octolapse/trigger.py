from .extruder import *
from .gcode import *
from .settings import *
import utility

import time


def IsTriggering(triggers,position,cmd):
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
	return None
def IsSnapshotCommand(command, snapshotCommand):
		commandName = GetGcodeFromString(command)
		snapshotCommandName = GetGcodeFromString(snapshotCommand)
		return commandName == snapshotCommandName
class GcodeTrigger(object):
	"""Used to monitor gcode for a specified command."""
	def __init__(self, extruderTriggers, octoprintLogger,command):
		self.Logger = octoprintLogger
		self.Extruder = Extruder(octoprintLogger)
		self.IsTriggered = False
		self.Command = command
		self.IsTriggered = False
		self.WaitingToTrigger = False
		self.ExtruderTriggers = extruderTriggers
	
	def Reset(self):
		self.IsTriggered = False
		self.HasSeenCode = False
		self.Extruder.Reset()
	def Update(self, position,commandName):
		"""If the provided command matches the trigger command, sets IsTriggered to true, else false"""
		self.IsTriggered = False
		self.Extruder.Update(position)
		if (IsSnapshotCommand(commandName,self.Command)):
			self.WaitingToTrigger = True
		if(self.WaitingToTrigger == True):
			if(self.Extruder.IsTriggered(self.ExtruderTriggers)):
				self.IsTriggered = True
				self.WaitingToTrigger = False
				self.Logger.info("GcodeTrigger - Triggering.")
			else:
				self.Logger.info("GcodeTrigger - Triggering, waiting on exturder.")

class LayerTrigger(object):
	
	def __init__( self,extruderTriggers, octoprintLogger,zMin, zHop, requireZhop = False, heightIncrement = None ):
		#utilities and profiles
		self.Logger = octoprintLogger
		self.Extruder = Extruder(octoprintLogger)
		self.ExtruderTriggers = extruderTriggers
		# Configuration Variables
		
		self.ZHop = zHop
		self.RequireZHop = requireZhop
		if(self.ZHop is None):
			self.ZHop = 0
		self.ZMin = zMin
		self.HeightIncrement = heightIncrement
		if(heightIncrement == 0):
			self.HeightIncrement = None
		
		# State Tracking Vars
		self.IsTriggered = False
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
		self.Logger.info("Layer Trigger - Updating Position.")
		self.IsLayerChange = False
		self.IsHeightChanged = False
		self.IsTriggered = False
		# Update the extruder monitor
		# This must be done every time, so do it first
		self.Extruder.Update(position)

		# save any previous values that will be needed later
		self.__HeightPrevious = self.Height
		self.__ZDeltaPrevious = self.ZDelta

		# determine if we've reached ZMin
		if(not self.HasReachedZMin and position.Z <= self.ZMin and self.Extruder.IsExtruding):
			self.HasReachedZMin = True
			self.Logger.info("Layer Trigger - Reached ZMin:{0}.".format(self.ZMin))
		# If we've not reached z min, leave!
		if(not self.HasReachedZMin):
			self.Logger.info("LayerTrigger - ZMin not reached.")
			return;

		# calculate Height
		if self.Extruder.IsExtruding and self.HasReachedZMin and position.Z > self.Height:
			self.Height = position.Z
			self.Logger.info("Layer Trigger - Reached New Height:{0}.".format(self.Height))
		# calculate ZDelta
		self.ZDelta = self.Height - self.__HeightPrevious

		# calculate layer change
		if(self.ZDelta > 0):
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

		# see if we've encountered a layer or height change
		if(self.HeightIncrement is not None and self.HeightIncrement > 0):
			if(self.IsHeightChange):
				self.__HeightChangeWait = True
				
		else:
			if(self.IsLayerChange):
				self.__LayerChangeWait = True

		# Is this a ZHOp?
		isZHop = self.ZHop > 0.0 and position.Z - self.Height >= self.ZHop and (self.Extruder.IsRetracted or self.Extruder.IsDetracting)

		
		# see if the extruder is triggering
		isExtruderTriggering = self.Extruder.IsTriggered(self.ExtruderTriggers)

		if(self.__HeightChangeWait or self.__LayerChangeWait):
			if(not isExtruderTriggering):
				if(self.__HeightChangeWait):
					self.Logger.info("LayerTrigger - Height change triggering, waiting on extruder.")
				elif (self.__LayerChangeWait):
					self.Logger.info("LayerTrigger - Layer change triggering, waiting on extruder.")
			else:
				if(self.RequireZHop and not isZHop):
					self.Logger.info("LayerTrigger - Triggering - Waiting on ZHop.")
					return
				if(self.__HeightChangeWait):
					self.Logger.info("LayerTrigger - Height change triggering, waiting on extruder.")
				elif (self.__LayerChangeWait):
					self.Logger.info("LayerTrigger - Layer change triggering, waiting on extruder.")
				self.__LayerChangeWait = False
				self.__HeightChangeWait = False
				self.IsTriggered = True



class TimerTrigger(object):
	
	def __init__(self,extruderTriggers,octoprintLogger,intervalSeconds):
		self.Logger = octoprintLogger
		self.Extruder = Extruder(octoprintLogger)
		self.ExtruderTriggers = extruderTriggers
		self.IntervalSeconds = intervalSeconds
		
		self.LastTriggerTime = None
		self.IntervalSeconds = intervalSeconds
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
		self.Extruder.Update(position)
		# if the last trigger time is null, set it now.
		if(self.LastTriggerTime is None):
			self.LastTriggerTime = currentTime

		if(self.PauseTime is not None):
			self.Logger.info("TimerTrigger - The print was paused, adjusting the timer to compensate.  LastTriggerTime:{0}, PauseTime:{1}, CurrentTime:{2} ".format(self.LastTriggerTime, self.PauseTime, currentTime))
			# Keep the proper interval if the print is paused
			self.LastTriggerTime = currentTime - (self.PauseTime - self.LastTriggerTime)
			self.Logger.info("TimerTrigger - New LastTriggerTime:{0}".format(self.LastTriggerTime))
			self.PauseTime = None

		self.Logger.info('TimerTrigger - {0} second interval, {1} seconds elapsed, {2} seconds to trigger'.format(self.IntervalSeconds,currentTime-self.LastTriggerTime, self.IntervalSeconds- (currentTime-self.LastTriggerTime)))
		# see if enough time has elapsed since the last trigger 
		if(currentTime - self.LastTriggerTime > self.IntervalSeconds):
			
			# see if the exturder is in the right position
			if(self.Extruder.IsTriggered(self.ExtruderTriggers)):
				# triggered!  Update the counter
				self.TriggeredCount += 1
				# Update the last trigger time.
				self.LastTriggerTime = currentTime
				# return true
				self.IsTriggered = True
				self.Logger.info('TimerTrigger - Triggering.')
			else:
				self.Logger.info('TimerTrigger - Triggering, waiting for extruder')

	# used to reset the triggers, if we want to do that for any reason.
	def Reset(self):
		self.IsTriggered=False
		self.LastTriggerTime = None
		self.Extruder.Reset()
