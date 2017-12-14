# coding=utf-8
import re
import collections
import string
import operator
from .settings import *
import utility
import sys

# global functions
def GetGcodeFromString(commandString):
	command = commandString.strip().split(' ', 1)[0].upper()
	ix = command.find(";")
	if(ix>-1):
		command = command[0:ix]
	return command
class PositionGcode(object):
	
	def __init__(self):
		self.GcodeCommands = []

	def EndIndex(self):
		return len(self.GcodeCommands)-1
class SnapshotGcode(object):
	def default(self, o):
		return o.__dict__

	def __init__(self):
		self.GcodeCommands = []
		self.X = None
		self.ReturnX = None
		self.Y = None
		self.ReturnY = None
		self.Z = None
		self.ReturnZ = None
		self.SnapshotIndex = -1
		self.DwellIndex = -1
	def EndIndex(self):
		return len(self.GcodeCommands)-1
	def SetSnapshotIndex(self):
		self.SnapshotIndex = self.EndIndex()

	def SetDwellIndex(self):
		self.DwellIndex = self.EndIndex()

	def SnapshotCommands(self):
		if(len(self.GcodeCommands)>0):
			return self.GcodeCommands[0:self.SnapshotIndex+1]
		return []

	def ReturnCommands(self):
		if(len(self.GcodeCommands)> self.SnapshotIndex+1):
			return self.GcodeCommands[self.SnapshotIndex+1:]
		return []
class CommandParameter(object):
    def __init__(self,name=None,group=None,value=None,parameter=None,order=None):
        if(parameter is None):
            self.Name = name
            self.Value = value
            self.Group = group
            self.Order = order
        else:
            self.Name = parameter.Name
            self.Value = parameter.Value
            self.Group = parameter.Group
            self.Order = parameter.Order
class CommandParameters(collections.MutableMapping):
	def __init__(self, *args, **kwargs):
		self.store = dict()
		self.update(dict(*args, **kwargs))  # use the free update to set keys

	def __getitem__(self,key):
		if(self.__keytransform__(key) in self.store.keys()):
			return self.store[self.__keytransform__(key)]
		return None

	def __setitem__(self,key,value):
		order = len(self.store) + 1
		if(type(value) in [float,int]):
			if(self.__keytransform__(key) not in self.store):
				self.store[self.__keytransform__(key)] = CommandParameter(name=key,value=value,order = order)
			else:
				self.store[self.__keytransform__(key)].Value = value
		elif(isinstance(value,CommandParameter)):
			if(value.Order is None):
				value.Order = order
			self.store[self.__keytransform__(key)] = value

	def __delitem__(self, key):
		del self.store[self.__keytransform__(key)]

	def __iter__(self):
		return iter(self.store)

	def __len__(self):
		return len(self.store)

	def __keytransform__(self, key):
		return key
class Command(object):
    def __init__(self,name=None, command=None, regex=None, displayTemplate=None, commentTemplate="{Comment}",commentSeperator=";",comment=None, parameters=None):
        if(type(command) is Command):
            self.Name = command.Name
            self.Command = command.Command
            self.Regex = command.Regex
            self.DisplayTemplate = command.DisplayTemplate
            self.Parameters = command.Parameters
            self.Comment = command.Comment
            self.CommentTemplate = command.CommentTemplate
            self.CommentSeparator = command.CommentSeparator
        else:
            self.Name = name
            self.Command = command
            self.Regex = regex
            self.DisplayTemplate = displayTemplate
            self.Parameters = CommandParameters()
            if(parameters is not None):
                if(type(parameters) is CommandParameter):
                    self.Parameters[parameters.Name] = parameters
                
                elif(isinstance(parameters, list)):
                    order = 1
                    for parameter in parameters:
                        if(parameter.Order is None):
                            parameter.Order = order
                            order+=1
                        self.Parameters[parameter.Name] = parameter
                else:
                    self.Parameters = parameters    
            self.Comment = comment
            self.CommentTemplate = commentTemplate
            self.CommentSeparator = commentSeperator
            
        if(regex is not None):
            self.__compiled = re.compile(regex,re.IGNORECASE)

    def DisplayString(self):
        if(self.DisplayTemplate is None):
            return self.Gcode()
        output = self.DisplayTemplate
        safeDict = utility.SafeDict()
        for key in self.Parameters:
            value = self.Parameters[key].Value
            safeDict.clear()
            if(value is None):
                value = "None"
            
            safeDict[key] = value
            output = string.Formatter().vformat(output, (), safeDict)
        # swap {comment} with the comment templatethe comment template
        safeDict.clear()
        safeDict["CommentTemplate"]= self.CommentTemplate
        output = string.Formatter().vformat(output, (), safeDict)

        if(self.Comment is not None):
            safeDict.clear()
            safeDict["CommentSeparator"] = self.CommentSeparator
            safeDict["Comment"] = self.Comment
            output = string.Formatter().vformat(output, (), safeDict)
        else:
            safeDict["CommentSeparator"] = ""
            safeDict["Comment"] = ""
            output = string.Formatter().vformat(output, (), safeDict)
            
        return output


    def Gcode(self):
        command = self.Command
        for parameter in (sorted(self.Parameters.values(),key=operator.attrgetter('Order'))):
            if(parameter.Value is not None):
                command += " " + parameter.Name + str(parameter.Value)
        if(self.Comment is not None):
           comment = self.Comment.strip()
           if(len(comment)>0):
               command += ";"+comment
        return command

    def Parse(self,gcode):
        matches = self.__compiled.match(gcode)
        # get the comments
        ix = gcode.find(";")
        if(ix>-1 and ix+1 < len(gcode)):
            self.Comment = gcode[ix+1]
        if(matches):
            
            params = {}
            if(self.Parameters is not None and len(self.Parameters.keys())>0):
                for key in self.Parameters:
                    param = self.Parameters[key]
                    params[param.Name] = matches.group(param.Group)
                return params
            else:
                return True
        else:
            return False  
class Commands(object):
	SuppressedSavedCommands = ["M105"]
	G0 = Command(
	name="Rapid Linear Move"
	,command="G0"
	,regex="(?i)^[gG0]{1,3}(?:\s+x(?P<x>-?[0-9.]{1,15})|\s+y(?P<y>-?[0-9.]{1,15})|\s+z(?P<z>-?[0-9.]{1,15})|\s+e(?P<e>-?[0-9.]{1,15})|\s+f?(?P<f>-?[0-9.]{1,15}))*$"
	,displayTemplate="Position: X={X}, Y={Y}, Z={Z}, E={E}, F={F}, Comment={CommentTemplate}"
	,commentTemplate="{Comment}"
	,commentSeperator=";"
	,parameters = [ CommandParameter(name="X",group=1),
					CommandParameter(name="Y",group=2),
					CommandParameter(name="Z",group=3),
					CommandParameter(name="E",group=4),
					CommandParameter(name="F",group=5)
					]
		)
	G1 = Command(
	name="Linear Move"
	,command="G1"
	,regex="(?i)^[gG1]{1,3}(?:\s+x(?P<x>-?[0-9.]{1,15})|\s+y(?P<y>-?[0-9.]{1,15})|\s+z(?P<z>-?[0-9.]{1,15})|\s+e(?P<e>-?[0-9.]{1,15})|\s+f?(?P<f>-?[0-9.]{1,15}))*$"
	,displayTemplate="Position: X={X}, Y={Y}, Z={Z}, E={E}, F={F}{CommentTemplate}"
	,parameters = [CommandParameter("X",group=1),
					CommandParameter("Y",group=2),
					CommandParameter("Z",group=3),
					CommandParameter("E",group=4),
					CommandParameter("F",group=5)
					]
		)
	G92 = Command(
	name="Set Absolute Position"
	,command="G92"
	,regex="(?i)^[gG92]{1,3}(?:\s+x(?P<x>-?[0-9.]{1,15})|\s+y(?P<y>-?[0-9.]{1,15})|\s+z(?P<z>-?[0-9.]{1,15})|\s+e(?P<e>-?[0-9.]{1,15}))*$"
	,displayTemplate="New Absolute Position: X={X}, Y={Y}, Z={Z}, E={E}{CommentTemplate}"
	,parameters = [CommandParameter("X",group=1),
					CommandParameter("Y",group=2),
					CommandParameter("Z",group=3),
					CommandParameter("E",group=4)
					]
		)
	M82 = Command(
		name="Set Extruder Relative Mode"
		,command="M82"
		,regex="(?i)^M82"
		,displayTemplate="M82 - Set Extruder Relative Mode{Comment}"
		,parameters = [])
	M83 = Command(
		name="Set Extruder Absolute Mode"
		,command="M83"
		,regex="(?i)^M83"
		,displayTemplate="M83 - Set Extruder Absolute Mode{Comment}"
		,parameters = [])
	G28 = Command(
		name="Go To Origin"
		,command="G28"
		,regex="(?i)^G28"
		,displayTemplate="G28 - Go to Origin{Comment}"
		,parameters = [])
	G90 = Command(
		name="Absolute Coordinates"
		,command="G90"
		,regex="(?i)^G90"
		,displayTemplate="G90 - Absolute Coordinates{Comment}"
		,parameters = [])
	G91 = Command(
	    name="Relative Coordinates"
	    ,command="G91"
	    ,regex="'(?i)^G91"
	    ,displayTemplate="G91 - Relative Coordinates{Comment}"
        ,parameters = [])
	M114 = Command(
		name="Get Position"
		,command="M114"
		,regex="(?i)^M114"
		,displayTemplate="M114 - Relative Coordinates{Comment}"
		)
	Debug_Assert = Command(
	    name="Debug - Assert"
	    ,command="OCTOLAPSE_ASSERT"
	    ,regex="(?i)^(?:\s*Octolapse_Assert)(?:\s+snapshot:(?P<Snapshot>-?(true|false))|\s+gcodetrigger:(?P<GcodeTrigger>-?(true|false))|\s+timertrigger:(?P<TimerTrigger>-?(true|false))|\s+layertrigger:(?P<LayerTrigger>-?(true|false))|\s+gcodetriggerwait:(?P<GcodeTriggerWait>-?(true|false))|\s+timertriggerwait:(?P<TimerTriggerWait>-?(true|false))|\s+layertriggerwait:(?P<LayerTriggerWait>-?(true|false)))*$"
	,displayTemplate="Octolapse Assert: Snapshot={Snapshot}, GcodeTrigger={GcodeTrigger}, LayerTrigger={LayerTrigger}, GcodeTriggerWait={GcodeTriggerWait}, TimerTriggerWait={TimerTriggerWait}, LayerTriggerWait={LayerTriggerWait}{CommentTemplate}"
	,parameters = [CommandParameter("Snapshot",group=1),
					CommandParameter("GcodeTrigger",group=2),
					CommandParameter("TimerTrigger",group=3),
					CommandParameter("LayerTrigger",group=4),
					CommandParameter("GcodeTriggerWait",group=5),
					CommandParameter("TimerTriggerWait",group=6),
					CommandParameter("LayerTriggerWait",group=7)
					]
		)

	CommandsDictionary = {
	    G0.Command:G0,
		G1.Command:G1,
		G92.Command:G92,
		M82.Command:M82,
		M83.Command:M83,
	    G28.Command:G28,
        G90.Command:G90,
        G91.Command:G91,
		M114.Command:M114,
		Debug_Assert.Command:Debug_Assert
    }
	
	def GetCommand(self, code):
		command = GetGcodeFromString(code)
		if (command in self.CommandsDictionary.keys()):
			return self.CommandsDictionary[command]
		return None
class Responses(object):
    def __init__(self):
        self.M114 = Command(
	        name="Get Position"
	        ,command="M114"
	        ,regex="(?i).*?X:([-0-9.]+) Y:([-0-9.]+) Z:([-0-9.]+) E:([-0-9.]+).*?"
	        ,displayTemplate="Position: X={0}, Y={1}, Z={2}, E={3}"
			,parameters = [
				CommandParameter("X",group=1),
				CommandParameter("Y",group=2),
				CommandParameter("Z",group=3),
				CommandParameter("E",group=4)
			]
        )

class Gcode(object):	
	CurrentXPathIndex = 0
	CurrentYPathIndex = 0
	def __init__(self,octolapseSettings,octoprint_printer_profile):
		self.Settings = octolapseSettings
		self.StabilizationPaths = self.Settings.CurrentStabilization().GetStabilizationPaths()
		self.Snapshot = self.Settings.CurrentSnapshot()
		self.Printer = self.Settings.CurrentPrinter()
		self.OctoprintPrinterProfile = octoprint_printer_profile
		
	def IsXInBounds(self,x):
		
		customBox = self.OctoprintPrinterProfile["volume"]["custom_box"]
		if( customBox is not None and customBox != False  and (x<self.OctoprintPrinterProfile["volume"]["custom_box"]["x_min"] or x > self.OctoprintPrinterProfile["volume"]["custom_box"]["x_max"])):
			self.Settings.CurrentDebugProfile().LogError('The X coordinate {0} was outside the bounds of the printer!  The print area is currently set to a custom box within the octoprint printer profile settings.'.format(x))
			return False
		elif(x<0 or x > self.OctoprintPrinterProfile["volume"]["width"]):
			self.Settings.CurrentDebugProfile().LogError('The X coordinate {0} was outside the bounds of the printer!'.format(x))
			return False
		return True	
	def IsYInBounds(self,y):
		hasError = False
		customBox = self.OctoprintPrinterProfile["volume"]["custom_box"]
		self.Settings.CurrentDebugProfile().LogInfo("CustomBox:{0}".format(customBox))
		if(customBox != False):
			yMin = float(customBox["y_min"])
			yMax = float(customBox["y_max"])
			self.Settings.CurrentDebugProfile().LogInfo("Testing coordinates for custom print area: y:{0}, y_min:{1}, y_max:{2}:".format(y,yMin,yMax))
			if((y<yMin or y > yMax)):
				self.Settings.CurrentDebugProfile().LogError('The Y coordinate {0} was outside the bounds of the printer!  The print area is currently set to a custom box within the octoprint printer profile settings.'.format(y))
				return False
		elif(y<0 or y > self.OctoprintPrinterProfile["volume"]["depth"]):
			self.Settings.CurrentDebugProfile().LogError('The Y coordinate {0} was outside the bounds of the printer!'.format(y))
			return False

		return True		
	def IsZInBounds(self,z):
		hasError = False
		customBox = self.OctoprintPrinterProfile["volume"]["custom_box"]
		if( customBox is not None and customBox != False  and (z < self.OctoprintPrinterProfile["volume"]["custom_box"]["z_min"] or z > self.OctoprintPrinterProfile["volume"]["custom_box"]["z_max"])):
			self.Settings.CurrentDebugProfile().LogError('The Z coordinate {0} was outside the bounds of the printer!  The print area is currently set to a custom box within the octoprint printer profile settings.'.format(z))
			return False
		elif(z<0 or z > self.OctoprintPrinterProfile["volume"]["height"]):
			self.Settings.CurrentDebugProfile().LogError('The Z coordinate {0} was outside the bounds of the printer!'.format(z))
			return False
		return True

	def GetSnapshotPosition(self,xPos,yPos):
		xPath = self.StabilizationPaths["X"]
		xPath.CurrentPosition = xPos
		yPath = self.StabilizationPaths["Y"]
		yPath.CurrentPosition = yPos

		coords = dict(X=self.GetSnapshotCoordinate(xPath), Y=self.GetSnapshotCoordinate(yPath))

		if(not self.IsXInBounds(coords["X"])):
			coords["X"] = None
		if(not self.IsYInBounds(coords["Y"])):
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
			if(path.InvertLoop):
				path.Index = len(path.Path)-1
				path.Increment = -1
			else:
				path.Index = 0
		elif(path.Index < 0):
			if(path.InvertLoop):
				path.Index = 0
				path.Increment = 1
			else:
				path.Index = len(path.Path)-1

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
			return self.GetRelativeCoordinate(percent,0,self.OctoprintPrinterProfile["volume"].width)
	def GetBedRelativeY(self,percent):
		if(self.OctoprintPrinterProfile["volume"]["custom_box"] != False):
			return self.GetRelativeCoordinate(percent,self.OctoprintPrinterProfile["volume"]["custom_box"]["y_min"],self.OctoprintPrinterProfile["volume"]["custom_box"]["y_max"])
		else:
			return self.GetRelativeCoordinate(percent,0,self.OctoprintPrinterProfile["volume"].depth)
	def GetBedRelativeZ(self,percent):
		if(self.OctoprintPrinterProfile["volume"]["custom_box"] != False):
			return self.GetRelativeCoordinate(percent,self.OctoprintPrinterProfile["volume"]["custom_box"]["z_min"],self.OctoprintPrinterProfile["volume"]["custom_box"]["x_max"])
		else:
			return self.GetRelativeCoordinate(percent,0,self.OctoprintPrinterProfile["volume"].height)
	def GetRelativeCoordinate(self,percent,min,max):
		return ((float(max)-float(min))*(percent/100.0))+float(min)


	def CreatePositionGcode(self):
		newPositionGcode = PositionGcode()
		# add commands to fetch the current position
		newPositionGcode.GcodeCommands.append(self.GetWaitForCurrentMovesToFinishGcode())  # Cant use m400 without something after it, and we can't wait for it in the usual way...
		newPositionGcode.GcodeCommands.append(self.GetPositionGcode())
		return newPositionGcode

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
		
		canZHop =  self.Printer.z_hop > 0 and self.IsZInBounds(z + self.Printer.z_hop)
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
		# removing the M400.  I think it messes stuff up sometimes.
		#newSnapshotGcode.GcodeCommands.append(self.GetWaitForCurrentMovesToFinishGcode())
		# Dwell with time 0 so that we wait until the move is finished before retrieving the position
		newSnapshotGcode.GcodeCommands.append("{0}".format(self.GetWaitForCurrentMovesToFinishGcode()));
		newSnapshotGcode.SetDwellIndex()
		# Get the final position after moving.  When we get a response from the, we'll know that the snapshot is ready to be taken
		newSnapshotGcode.GcodeCommands.append(self.GetPositionGcode())
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
		return " F{0:.3f}".format(speed)

		
