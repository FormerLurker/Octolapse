# coding=utf-8
import re
import collections
import string
import operator
from octoprint_octolapse.settings import *
import octoprint_octolapse.utility as utility
import sys

class SnapshotGcode(object):
	
	def __init__(self):
		self.GcodeCommands = []
		self.X = None
		self.ReturnX = None
		self.Y = None
		self.ReturnY = None
		self.Z = None
		self.ReturnZ = None
		self.SnapshotIndex = -1
		self.SnapshotMoveIndex = -1

	def EndIndex(self):
		return len(self.GcodeCommands)-1
	def SetSnapshotIndex(self):
		self.SnapshotIndex = self.EndIndex()
	def SetSnapshotMoveIndex(self):
		self.SnapshotMoveIndex = self.EndIndex()

	def SnapshotCommands(self):
		if(len(self.GcodeCommands)>0):
			return self.GcodeCommands[0:self.SnapshotIndex+1]
		return []

	def ReturnCommands(self):
		if(len(self.GcodeCommands)> self.SnapshotIndex+1):
			return self.GcodeCommands[self.SnapshotIndex+1:]
		return []

class SnapshotGcodeGenerator(object):	
	CurrentXPathIndex = 0
	CurrentYPathIndex = 0
	def __init__(self,octolapseSettings,octoprint_printer_profile):
		self.Settings = octolapseSettings
		self.StabilizationPaths = self.Settings.CurrentStabilization().GetStabilizationPaths()
		self.Snapshot = self.Settings.CurrentSnapshot()
		self.Printer = self.Settings.CurrentPrinter()
		self.OctoprintPrinterProfile = octoprint_printer_profile

	def GetSnapshotPosition(self,xPos,yPos):
		xPath = self.StabilizationPaths["X"]
		xPath.CurrentPosition = xPos
		yPath = self.StabilizationPaths["Y"]
		yPath.CurrentPosition = yPos

		coords = dict(X=self.GetSnapshotCoordinate(xPath), Y=self.GetSnapshotCoordinate(yPath))

		if(not utility.IsXInBounds(coords["X"],self.OctoprintPrinterProfile)):
			coords["X"] = None
		if(not utility.IsYInBounds(coords["Y"],self.OctoprintPrinterProfile)):
			coords["Y"] = None

		return coords

	def GetSnapshotCoordinate(self, path):
		if(path.Type == 'disabled'):
			return path.CurrentPosition
		
		# Get the current coordinate from the path
		coord = path.Path[path.Index]
		# move our index forward or backward
		path.Index += path.Increment
		
		if(path.Index >= len(path.Path)):
			if(path.Loop):
				if(path.InvertLoop):
					if(len(path.Path)>1):
						path.Index = len(path.Path)-2
					else:
						path.Index = 0
					path.Increment = -1
				else:
					path.Index = 0
			else:
				path.Index = len(path.Path)-1
		elif(path.Index < 0):
			if(path.Loop):
				if(path.InvertLoop):
					if(len(path.Path)>1):
						path.Index = 1
					else:
						path.Index = 0
					path.Increment = 1
				else:
					path.Index = len(path.Path)-1
			else:
				path.Index = 0

		if(path.CoordinateSystem == "absolute"):
			return coord
		elif(path.CoordinateSystem == "bed_relative"):
			if(self.OctoprintPrinterProfile["volume"]["formFactor"] == "circle"):
				raise ValueError('Cannot calculate relative coordinates within a circular bed (yet...), sorry')
			return 	self.GetBedRelativeCoordinate(path.Axis,coord)

	def GetBedRelativeCoordinate(self,axis,coord):
		relCoord = None
		if(axis == "X"):
			relCoord = self.GetBedRelativeX(coord)
		elif(axis == "Y"):
			relCoord = self.GetBedRelativeY(coord)
		elif(axis == "Z"):
			relCoord = self.GetBedRelativeZ(coord)

		return relCoord
	def GetBedRelativeX(self,percent):
		if(self.OctoprintPrinterProfile["volume"]["custom_box"] != False):
			return self.GetRelativeCoordinate(percent,self.OctoprintPrinterProfile["volume"]["custom_box"]["x_min"],self.OctoprintPrinterProfile["volume"]["custom_box"]["x_max"])
		else:
			return self.GetRelativeCoordinate(percent,0,self.OctoprintPrinterProfile["volume"]["width"])
	def GetBedRelativeY(self,percent):
		if(self.OctoprintPrinterProfile["volume"]["custom_box"] != False):
			return self.GetRelativeCoordinate(percent,self.OctoprintPrinterProfile["volume"]["custom_box"]["y_min"],self.OctoprintPrinterProfile["volume"]["custom_box"]["y_max"])
		else:
			return self.GetRelativeCoordinate(percent,0,self.OctoprintPrinterProfile["volume"]["depth"])
	def GetBedRelativeZ(self,percent):
		if(self.OctoprintPrinterProfile["volume"]["custom_box"] != False):
			return self.GetRelativeCoordinate(percent,self.OctoprintPrinterProfile["volume"]["custom_box"]["z_min"],self.OctoprintPrinterProfile["volume"]["custom_box"]["x_max"])
		else:
			return self.GetRelativeCoordinate(percent,0,self.OctoprintPrinterProfile["volume"]["height"])
	def GetRelativeCoordinate(self,percent,min,max):
		return ((float(max)-float(min))*(percent/100.0))+float(min)

	def CreateSnapshotGcode(self, x,y,z, isRelative, isExtruderRelative, extruder, savedCommand = None):
		if(x is None or y is None or z is None):
			return None
		commandIndex = 0

		newSnapshotGcode = SnapshotGcode()
		# Create code to move from the current extruder position to the snapshot position
		# get the X and Y coordinates of the snapshot
		snapshotPosition = self.GetSnapshotPosition(x,y)
		newSnapshotGcode.X = snapshotPosition["X"]
		newSnapshotGcode.Y = snapshotPosition["Y"]
		hasRetracted = False
		#todo:  make sure the relative values are from the previous command!  It's possible that we've triggered when switching
		#from relative to absolute!
		previousIsRelative = isRelative
		currentIsRelative = previousIsRelative
		previousExtruderRelative = isExtruderRelative
		currentExtruderRelative = previousExtruderRelative
		# retract if necessary
		if(self.Snapshot.retract_before_move and not extruder.IsRetracted):
			if(not currentExtruderRelative):
				newSnapshotGcode.GcodeCommands.append(self.GetSetExtruderRelativePositionGcode())
				currentExtruderRelative = True
			newSnapshotGcode.GcodeCommands.append(self.GetRetractGcode())
			hasRetracted = True
		
		# Can we hop or is the print too tall?
		
		canZHop =  self.Printer.z_hop > 0 and utility.IsZInBounds(z + self.Printer.z_hop,self.OctoprintPrinterProfile )
		# if we can ZHop, do
		if(canZHop):
			if(not currentIsRelative):
				newSnapshotGcode.GcodeCommands.append(self.GetSetRelativePositionGcode())
				currentIsRelative = True
			newSnapshotGcode.GcodeCommands.append(self.GetRelativeZLiftGcode())
			

		if (newSnapshotGcode.X is None or newSnapshotGcode.Y is None):
			# either x or y is out of bounds.
			return None

		#Move back to the snapshot position - make sure we're in absolute mode for this
		if(currentIsRelative):
			newSnapshotGcode.GcodeCommands.append(self.GetSetAbsolutePositionGcode())
			currentIsRelative = False
		newSnapshotGcode.GcodeCommands.append(self.GetMoveGcode(newSnapshotGcode.X,newSnapshotGcode.Y))
		newSnapshotGcode.SetSnapshotMoveIndex()
		# Dwell with time 0 so that we wait until the move is finished before retrieving the position
		#newSnapshotGcode.GcodeCommands.append(self.GetWaitForCurrentMovesToFinishGcode());
		
		# Get the final position after moving.  When we get a response from the, we'll know that the snapshot is ready to be taken
		#newSnapshotGcode.GcodeCommands.append(self.GetPositionGcode())
		# mark the snapshot command index
		newSnapshotGcode.SetSnapshotIndex()

		# create return gcode
		#record our previous position for posterity
		newSnapshotGcode.ReturnX = x
		newSnapshotGcode.ReturnY = y
		newSnapshotGcode.ReturnZ = z

		#Move back to previous position - make sure we're in absolute mode for this (hint: we already are right now)
		if(currentIsRelative):
			newSnapshotGcode.GcodeCommands.append(self.GetSetAbsolutePositionGcode())
			currentIsRelative = False
			
		if(x is not None and y is not None):
			newSnapshotGcode.GcodeCommands.append(self.GetMoveGcode(x,y))
		# If we can hop we have already done so, so now time to lower the Z axis:
		if(canZHop):
			if(not currentIsRelative):
				newSnapshotGcode.GcodeCommands.append(self.GetSetRelativePositionGcode())
				currentIsRelative = True
			newSnapshotGcode.GcodeCommands.append(self.GetRelativeZLowerGcode())
		# detract
		if(hasRetracted):
			if(not currentExtruderRelative):
				newSnapshotGcode.GcodeCommands.append.GetSetExtruderRelativePositionGcode()
				currentExtruderRelative = True
			newSnapshotGcode.GcodeCommands.append(self.GetDetractGcode())

		# reset the coordinate systems for the extruder and axis
		if(previousIsRelative != currentIsRelative):
			if(currentIsRelative):
				newSnapshotGcode.GcodeCommands.append(self.GetSetAbsolutePositionGcode())
			else:
				newSnapshotGcode.GcodeCommands.append(self.GetSetRelativePositionGcode())
			currentIsRelative = previousIsRelative

		if(previousExtruderRelative != currentExtruderRelative):
			if(previousExtruderRelative):
				newSnapshotGcode.GcodeCommands.append(self.GetSetExtruderRelativePositionGcode())
			else:
				newSnapshotGcode.GcodeCommands.append(self.GetSetExtruderAbslutePositionGcode())
		# What the hell was this for?!
		#newSnapshotGcode.GcodeCommands[-1] = "{0}".format(newSnapshotGcode.GcodeCommands[-1])
		# add the saved command, if there is one
		if(savedCommand is not None):
			newSnapshotGcode.GcodeCommands.append(savedCommand)

		self.Settings.CurrentDebugProfile().LogSnapshotGcode("Snapshot Command Index:{0}, Gcode:".format(newSnapshotGcode.SnapshotIndex))
		for str in newSnapshotGcode.GcodeCommands:
			self.Settings.CurrentDebugProfile().LogSnapshotGcode("    {0}".format(str))
			
		self.Settings.CurrentDebugProfile().LogSnapshotPosition("Snapshot Position: (x:{0:f},y:{1:f})".format(newSnapshotGcode.X,newSnapshotGcode.Y))
		self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Return Position: (x:{0:f},y:{1:f})".format(newSnapshotGcode.ReturnX,newSnapshotGcode.ReturnY))

		return newSnapshotGcode

	def GetSetExtruderRelativePositionGcode(self):
		return "M83"
	def GetSetExtruderAbslutePositionGcode(self):
		return "M82"
	def GetSetAbsolutePositionGcode(self):
		return "G90"
	def GetSetRelativePositionGcode(self):
		return "G91"
	
	def GetDelayGcode(self, delay):
		return "G4 P{0:d}".format(delay)
	def GetMoveGcode(self,x,y):
		return "G1 X{0:.3f} Y{1:.3f}{2}".format(x,y,self.GetF(self.Printer.movement_speed))
	def GetRelativeZLiftGcode(self):
		return "G1 Z{0:.3f}{1}".format(self.Printer.z_hop, self.GetF(self.Printer.movement_speed))
	def GetRelativeZLowerGcode(self):
		return "G1 Z{0:.3f}{1}".format(-1.0*self.Printer.z_hop, self.GetF(self.Printer.movement_speed))
	def GetRetractGcode(self):
		return "G1 E{0:.3f}{1}".format(-1*self.Printer.retract_length,self.GetF(self.Printer.retract_speed))
	def GetDetractGcode(self):
		return "G1 E{0:.3f}{1}".format( self.Printer.retract_length,self.GetF(self.Printer.retract_speed))
	def GetResetLineNumberGcode(self,lineNumber):
		return "M110 N{0:d}".format(lineNumber)
	def GetWaitForCurrentMovesToFinishGcode(self):
		return "M400";
	def GetPositionGcode(self):
		return "M114";

	def GetF(self, speed):
		if(speed<1):
			return ""
		return " F{0}".format(int(speed))

