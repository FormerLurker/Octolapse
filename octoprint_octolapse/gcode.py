# coding=utf-8
import re
import collections
import string
import operator
from octoprint_octolapse.settings import *
import octoprint_octolapse.utility as utility
import sys
from octoprint_octolapse.command import Commands

class SnapshotGcode(object):
	CommandsDictionary = Commands()
	def __init__(self, isTestMode):
		self.GcodeCommands = []
		self.__OriginalGcodeCommands = []
		self.X = None
		self.ReturnX = None
		self.Y = None
		self.ReturnY = None
		self.Z = None
		self.ReturnZ = None
		self.SnapshotIndex = -1
		self.IsTestMode = isTestMode
	def Append(self,command):
		self.__OriginalGcodeCommands.append(command)

		if (self.IsTestMode):
			command = self.CommandsDictionary.GetTestModeCommandString(command)
		command = command.upper().strip()
		if(command != ""):
			self.GcodeCommands.append(command)
	def EndIndex(self):
		return len(self.GcodeCommands)-1
	def SetSnapshotIndex(self):
		self.SnapshotIndex = self.EndIndex()

	def GetOriginalReturnCommands(self):
		if(len(self.__OriginalGcodeCommands)> self.SnapshotIndex+1):
			return self.__OriginalGcodeCommands[self.SnapshotIndex+1:]
		return []

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
		self.Snapshot = Snapshot(self.Settings.CurrentSnapshot())
		self.Printer = Printer(self.Settings.CurrentPrinter())
		self.OctoprintPrinterProfile = octoprint_printer_profile
		self.IsTestMode = self.Settings.CurrentDebugProfile().is_test_mode
		
	def Reset(self):
		self.RetractedBySnapshotStartGcode = None
		self.ZhopBySnapshotStartGcode = None
		self.IsRelativeOriginal = None
		self.IsRelativeCurrent = None
		self.IsExtruderRelativeOriginal = None
		self.IsExtruderRelativeCurrent = None
		self.FOriginal = None
		self.FCurrent = None
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
	def CreateSnapshotStartGcode(self,z,f,isRelative, isExtruderRelative, extruder):
		self.Reset()
		self.FOriginal = f
		self.FCurrent = f
		self.RetractedBySnapshotStartGcode = False
		self.ZhopBySnapshotStartGcode = False
		self.IsRelativeOriginal = isRelative
		self.IsRelativeCurrent = isRelative
		self.IsExtruderRelativeOriginal = isExtruderRelative
		self.IsExtruderRelativeCurrent = isExtruderRelative

		newSnapshotGcode = SnapshotGcode(self.IsTestMode)
		# retract if necessary
		if(self.Snapshot.retract_before_move and not extruder.IsRetracted):
			if(not self.IsExtruderRelativeCurrent):
				newSnapshotGcode.Append(self.GetSetExtruderRelativePositionGcode())
				self.IsExtruderRelativeCurrent = True
			if(self.Printer.retract_speed>0 and self.Printer.retract_speed != self.FCurrent):
				newSnapshotGcode.Append(self.GetFeedrateSetGcode(self.Printer.retract_speed));
				self.FCurrent = self.Printer.retract_speed
			newSnapshotGcode.Append(self.GetRetractGcode())
			self.RetractedBySnapshotStartGcode = True
			if(self.FCurrent != self.FOriginal):
				newSnapshotGcode.Append(self.GetFeedrateSetGcode(self.FOriginal));
				self.FCurrent = self.FOriginal
		# Can we hop or is the print too tall?
		
		canZHop =  self.Printer.z_hop > 0 and utility.IsZInBounds(z + self.Printer.z_hop,self.OctoprintPrinterProfile )
		# if we can ZHop, do
		if(canZHop):
			if(not self.IsRelativeCurrent): # must be in relative mode
				newSnapshotGcode.Append(self.GetSetRelativePositionGcode())
				self.IsRelativeCurrent = True
			newSnapshotGcode.Append(self.GetRelativeZLiftGcode())
			self.ZhopBySnapshotStartGcode = True

		return newSnapshotGcode
	def CreateSnapshotGcode(self, x,y,z, savedCommand = None):
		if(x is None or y is None or z is None):
			return None
		commandIndex = 0

		newSnapshotGcode = SnapshotGcode(self.IsTestMode)
		# Create code to move from the current extruder position to the snapshot position
		# get the X and Y coordinates of the snapshot
		snapshotPosition = self.GetSnapshotPosition(x,y)
		newSnapshotGcode.X = snapshotPosition["X"]
		newSnapshotGcode.Y = snapshotPosition["Y"]

		if (newSnapshotGcode.X is None or newSnapshotGcode.Y is None):
			# either x or y is out of bounds.
			return None

		#Move back to the snapshot position - make sure we're in absolute mode for this
		if(self.IsRelativeCurrent): # must be in absolute mode
			newSnapshotGcode.Append(self.GetSetAbsolutePositionGcode())
			self.IsRelativeCurrent = False

		## speed change - Set to movement speed IF we have specified one
		if(self.Printer.movement_speed>0 and self.Printer.movement_speed != self.FCurrent):
			newSnapshotGcode.Append(self.GetFeedrateSetGcode(self.Printer.movement_speed));
			self.FCurrent = self.Printer.retract_speed

		# Move to Snapshot Position
		newSnapshotGcode.Append(self.GetMoveGcode(newSnapshotGcode.X,newSnapshotGcode.Y))
		
		# Wait for current moves to finish before requesting the position
		newSnapshotGcode.Append(self.GetWaitForCurrentMovesToFinishGcode());
		
		# Get the final position after moving.  When we get a response from the, we'll know that the snapshot is ready to be taken
		newSnapshotGcode.Append(self.GetPositionGcode())
		# mark the snapshot command index
		newSnapshotGcode.SetSnapshotIndex()

		# create return gcode
		#record our previous position for posterity
		newSnapshotGcode.ReturnX = x
		newSnapshotGcode.ReturnY = y
		newSnapshotGcode.ReturnZ = z

		#Move back to previous position - make sure we're in absolute mode for this (hint: we already are right now)
		#if(self.IsRelativeCurrent):
		#	newSnapshotGcode.Append(self.GetSetAbsolutePositionGcode())
		#	self.IsRelativeCurrent = False
			
		if(x is not None and y is not None):
			newSnapshotGcode.Append(self.GetMoveGcode(x,y))

		## speed change - Return to the original feedrate IF we have specified a custom speed
		if(self.FCurrent != self.FOriginal):
			newSnapshotGcode.Append(self.GetFeedrateSetGcode(self.FOriginal));
			self.FCurrent = self.FOriginal
		
		
		# If we zhopped in the beginning, lower z
		if(self.ZhopBySnapshotStartGcode):
			if(not self.IsRelativeCurrent):
				newSnapshotGcode.Append(self.GetSetRelativePositionGcode())
				self.IsRelativeCurrent = True
			newSnapshotGcode.Append(self.GetRelativeZLowerGcode())
		# detract
		if(self.RetractedBySnapshotStartGcode):
			if(not self.IsExtruderRelativeCurrent):
				newSnapshotGcode.Append.GetSetExtruderRelativePositionGcode()
				self.IsExtruderRelativeCurrent = True
			if(self.Printer.retract_speed>0 and self.Printer.detract_speed != self.FCurrent):
				newSnapshotGcode.Append(self.GetFeedrateSetGcode(self.Printer.detract_speed));
				self.FCurrent = self.Printer.retract_speed
			newSnapshotGcode.Append(self.GetDetractGcode())
			if(self.FCurrent != self.FOriginal):
				newSnapshotGcode.Append(self.GetFeedrateSetGcode(self.FOriginal));
				self.FCurrent = self.FOriginal
		# reset the coordinate systems for the extruder and axis
		if(self.IsRelativeOriginal != self.IsRelativeCurrent):
			if(self.IsRelativeCurrent):
				newSnapshotGcode.Append(self.GetSetAbsolutePositionGcode())
			else:
				newSnapshotGcode.Append(self.GetSetRelativePositionGcode())
			self.IsRelativeCurrent = self.IsRelativeOriginal

		if(self.IsExtruderRelativeOriginal != self.IsExtruderRelativeCurrent):
			if(self.IsExtruderRelativeOriginal):
				newSnapshotGcode.Append(self.GetSetExtruderRelativePositionGcode())
			else:
				newSnapshotGcode.Append(self.GetSetExtruderAbslutePositionGcode())
		# What the hell was this for?!
		#newSnapshotGcode.GcodeCommands[-1] = "{0}".format(newSnapshotGcode.GcodeCommands[-1])
		# add the saved command, if there is one
		if(savedCommand is not None):
			newSnapshotGcode.Append(savedCommand)

		self.Settings.CurrentDebugProfile().LogSnapshotGcode("SnapshotCommandIndex:{0}, EndIndex{1}, Gcode:".format(newSnapshotGcode.SnapshotIndex, newSnapshotGcode.EndIndex()))
		for str in newSnapshotGcode.GcodeCommands:
			self.Settings.CurrentDebugProfile().LogSnapshotGcode("    {0}".format(str))
			
		self.Settings.CurrentDebugProfile().LogSnapshotPosition("Snapshot Position: (x:{0:f},y:{1:f})".format(newSnapshotGcode.X,newSnapshotGcode.Y))
		self.Settings.CurrentDebugProfile().LogSnapshotPositionReturn("Return Position: (x:{0:f},y:{1:f})".format(newSnapshotGcode.ReturnX,newSnapshotGcode.ReturnY))
		self.Reset()
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
		return "G1 X{0:.3f} Y{1:.3f}".format(x,y)
	def GetRelativeZLiftGcode(self):
		return "G1 Z{0:.3f}".format(self.Printer.z_hop)
	def GetRelativeZLowerGcode(self):
		return "G1 Z{0:.3f}".format(-1.0*self.Printer.z_hop)
	def GetRetractGcode(self):
		return "G1 E{0:.3f}".format(-1*self.Printer.retract_length)
	def GetDetractGcode(self):
		return "G1 E{0:.3f}".format( self.Printer.retract_length)
	def GetResetLineNumberGcode(self,lineNumber):
		return "M110 N{0:d}".format(lineNumber)
	def GetWaitForCurrentMovesToFinishGcode(self):
		return "M400";
	def GetPositionGcode(self):
		return "M114";


	def GetFeedrateSetGcode(self,f):
		return "G1 F{0}".format(int(f))
