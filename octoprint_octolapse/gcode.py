import re
import collections
import string
import operator

class SnapshotGcode(object):
	def __init__(self):
		self.Commands = []
		self.X = None
		self.Y = None

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
        safeDict = SafeDict()
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
	    ,regex="'(?i)^G91'"
	    ,displayTemplate="G91 - Relative Coordinates{Comment}"
        ,parameters = [])

	CommandsDictionary = {
	    G0.Command:G0,
	    G1.Command:G1,
	    G28.Command:G28,
        G90.Command:G90,
        G91.Command:G91
    }

	def GetCommand(self, code):
		command = GetGcodeFromString(code)
		if (command in self.CommandsDictionary.keys()):
			return self.CommandsDictionary[command]
		return None

def GetGcodeFromString(commandString):
	command = commandString.strip().split(' ', 1)[0].upper()
	ix = command.find(";")
	if(ix>-1):
		command = command[0:ix]
	return command

class Responses(object):
    def __init__(self,name, command, regex, template):
        self.M114 = Command(
	        name="Get Position"
	        ,command="M114"
	        ,regex="(?i)^X:([-+]?[0-9.]+) Y:([-+]?[0-9.]+) Z:([-+]?[0-9.]+) E:([-+]?[0-9.]+)"
	        ,displayTemplate="Position: X={0}, Y={1}, Z={2}, E={3}"
        )

class SafeDict(dict):
    def __init__(self, **entries):
        self.__dict__.update(entries)
        index = 0

        for key in self.keys():
            self.keys[index] = str(key)
            index += 1
            
    def __missing__(self, key):
        return '{' + key + '}'
	
class GCode(object):
	
	CurrentXPathIndex = 0
	CurrentYPathIndex = 0
	def __init__(self,printer,profile,octoprint_printer_profile,octoprintLogger):
		self.Logger = octoprintLogger
		self.Printer = printer
		self.Profile = profile
		self.OctoprintPrinterProfile = octoprint_printer_profile
		self.CurrentXPathIndex = 0
		self.CurrentYPathIndex = 0
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
		return ((max-min)*(percent/100.0))+min
	def IsXInBounds(self,x):
		
		if(self.OctoprintPrinterProfile["volume"]["custom_box"] == True and (x<self.OctoprintPrinterProfile["volume"]["custom_box"]["x_min"] or x > self.OctoprintPrinterProfile["volume"]["custom_box"]["x_max"])):
			self.Logger.error('The X coordinate {0} was outside the bounds of the printer!  The print area is currently set to a custom box within the octoprint printer profile settings.'.format(x))
			return False
		elif(x<0 or x > self.OctoprintPrinterProfile["volume"]["width"]):
			self.Logger.error('The X coordinate {0} was outside the bounds of the printer!'.format(x))
			return False
		return True	
			
	def IsYInBounds(self,y):
		hasError = False
		if(self.OctoprintPrinterProfile["volume"]["custom_box"] == True and (y<self.OctoprintPrinterProfile["volume"]["custom_box"]["y_min"] or y > self.OctoprintPrinterProfile["volume"]["custom_box"]["y_max"])):
			self.Logger.error('The Y coordinate {0} was outside the bounds of the printer!  The print area is currently set to a custom box within the octoprint printer profile settings.'.format(y))
			return False
		elif(y<0 or y > self.OctoprintPrinterProfile["volume"]["depth"]):
			self.Logger.error('The Y coordinate {0} was outside the bounds of the printer!'.format(y))
			return False

		return True
			
	def IsZInBounds(self,z):
		hasError = False
		if(self.OctoprintPrinterProfile["volume"]["custom_box"] == True and (z < self.OctoprintPrinterProfile["volume"]["custom_box"]["z_min"] or z > self.OctoprintPrinterProfile["volume"]["custom_box"]["z_max"])):
			self.Logger.error('The Z coordinate {0} was outside the bounds of the printer!  The print area is currently set to a custom box within the octoprint printer profile settings.'.format(z))
			return False
		elif(z<0 or z > self.OctoprintPrinterProfile["volume"]["height"]):
			self.Logger.error('The Z coordinate {0} was outside the bounds of the printer!'.format(z))
			return False
		return True
	def GetXCoordinateForSnapshot(self):
		xCoord = 0
		if (self.Profile.stabilization.x_type == "fixed_coordinate"):
			xCoord = self.Profile.stabilization.x_fixed_coordinate
		elif (self.Profile.stabilization.x_type == "relative"):
			if(self.OctoprintPrinterProfile["volume"]["formFactor"] == "circle"):
				raise ValueError('Cannot calculate relative coordinates within a circular bed (yet...), sorry')
			xCoord = self.GetBedRelativeX(self.Profile.stabilization.x_relative)
		elif (self.Profile.stabilization.x_type == "fixed_path"):
			# if there are no paths return the fixed coordinate
			if(len(self.Profile.stabilization.x_fixed_path) == 0):
				xCoord = self.Profile.stabilization.x_fixed_coordinate
			# if we have reached the end of the path
			elif(self.CurrentXPathIndex >= len(self.Profile.stabilization.x_fixed_path)):
				#If we are looping through the paths, reset the index to 0
				if(self.Profile.stabilization.x_fixed_path_loop):
						self.CurrentXPathIndex = 0
				else:
					self.CurrentXPathIndex = len(self.Profile.stabilization.x_fixed_path)
			xCoord = self.Profile.stabilization.x_fixed_path[self.CurrentXPathIndex]
			self.CurrentXPathIndex += 1
		elif (self.Profile.stabilization.x_type == "relative_path"):
			if(self.OctoprintPrinterProfile["volume"]["formFactor"] == "circle"):
				raise ValueError('Cannot calculate relative coordinates within a circular bed (yet...), sorry')
			# if there are no paths return the fixed coordinate
			if(len(self.Profile.stabilization.x_relative_path) == 0):
				xCoord = self.GetBedRelativeX(self.Profile.stabilization.x_relative)
			# if we have reached the end of the path
			elif(self.CurrentXPathIndex >= len(self.Profile.stabilization.x_relative_path)):
				#If we are looping through the paths, reset the index to 0
				if(self.Profile.stabilization.x_relative_path_loop):
						self.CurrentXPathIndex = 0
				else:
					self.CurrentXPathIndex = len(self.Profile.stabilization.x_relative_path)
			xRel = self.Profile.stabilization.x_relative_path[self.CurrentXPathIndex]
			self.CurrentXPathIndex += 1
			xCoord = self.GetBedRelativeX(xRel)
		else:
			raise NotImplementedError
		if(not self.IsXInBounds(xCoord)):
			return None
		return xCoord	
	def GetYCoordinateForSnapshot(self):
		yCoord = 0
		if (self.Profile.stabilization.y_type == "fixed_coordinate"):
			yCoord = self.Profile.stabilization.y_fixed_coordinate
		elif (self.Profile.stabilization.y_type == "relative"):
			if(self.OctoprintPrinterProfile["volume"]["formFactor"] == "circle"):
				raise ValueError('Cannot calculate relative coordinates within a circular bed (yet...), sorry')
			yCoord = self.GetBedRelativeY(self.Profile.stabilization.y_relative)
		elif (self.Profile.stabilization.y_type == "fixed_path"):
			# if there are no paths return the fixed coordinate
			if(len(self.Profile.stabilization.y_fixed_path) == 0):
				yCoord = self.Profile.stabilization.y_fixed_coordinate
			# if we have reached the end of the path
			elif(self.CurrentYPathIndex >= len(self.Profile.stabilization.y_fixed_path)):
				#If we are looping through the paths, reset the index to 0
				if(self.Profile.stabilization.y_fixed_path_loop):
						self.CurrentYPathIndex = 0
				else:
					self.CurrentYPathIndex = len(self.Profile.stabilization.y_fixed_path)
			yCoord = self.Profile.stabilization.y_fixed_path[self.CurrentYPathIndex]
			self.CurrentYPathIndex += 1
		elif (self.Profile.stabilization.y_type == "relative_path"):
			if(self.OctoprintPrinterProfile["volume"]["formFactor"] == "circle"):
				raise ValueError('Cannot calculate relative coordinates within a circular bed (yet...), sorry')
			# if there are no paths return the fixed coordinate
			if(len(self.Profile.stabilization.y_relative_path) == 0):
				yCoord =  self.GetBedRelativeY(self.Profile.stabilization.y_relative)
			# if we have reached the end of the path
			elif(self.CurrentYPathIndex >= len(self.Profile.stabilization.y_relative_path)):
				#If we are looping through the paths, reset the index to 0
				if(self.Profile.stabilization.y_relative_path_loop):
						self.CurrentYPathIndex = 0
				else:
					self.CurrentYPathIndex = len(self.Profile.stabilization.y_relative_path)
			yRel = self.Profile.stabilization.y_relative_path[self.CurrentYPathIndex]
			self.CurrentYPathIndex += 1
			yCoord =  self.GetBedRelativeY(yRel)
		else:
			raise NotImplementedError

		if(not self.IsYInBounds(yCoord)):
			return None
		return yCoord
	def GetSnapshotGcode(self, position, extruder):
		newSnapshotGcode = SnapshotGcode()
		hasRetracted = False

		isRelativeLocal = position.IsRelative
		
		# switch to absolute coordinates if we're not already in that mode
		if(position.IsRelative):
			newSnapshotGcode.Commands.append(self.GetSetAbsolutePositionGcode())
			isRelativeLocal = False

		# retract if necessary
		if(self.Profile.snapshot.retract_before_move and not extruder.IsRetracted):
			newSnapshotGcode.Commands.append(self.GetRetractGCode())
			hasRetracted = True
		# get the X and Y coordinates of the snapshot
		newSnapshotGcode.X = self.GetXCoordinateForSnapshot()
		newSnapshotGcode.Y = self.GetYCoordinateForSnapshot()

		# Can we hop or is the print too tall?
		canZHop = self.Printer.z_hop > 0 and self.IsZInBounds(position.Z + self.Printer.z_hop)
		# if we can ZHop, do
		if(canZHop):
			if(not isRelativeLocal):
				newSnapshotGcode.Commands.append(self.GetSetRelativePositionGcode())
				isRelativeLocal = True
			newSnapshotGcode.Commands.append(self.GetRelativeZLiftGcode())
			newSnapshotGcode.Commands.append(self.GetSetAbsolutePositionGcode())
			isRelativeLocal = False

		if (newSnapshotGcode.X is None or newSnapshotGcode.Y is None):
			# either x or y is out of bounds.
			return None
		newSnapshotGcode.Commands.append(self.GetMoveGcode(newSnapshotGcode.X,newSnapshotGcode.Y))
		newSnapshotGcode.Commands.append(self.GetDelayGcode())
		#Move back to previous position
		if(position.XPrevious is not None and position.YPrevious is not None):
			newSnapshotGcode.Commands.append(self.GetMoveGcode(position.XPrevious,position.YPrevious))
		# If we can hop we have already done so, so now time to lower the Z axis:
		if(canZHop):
			if(not isRelativeLocal):
				newSnapshotGcode.Commands.append(self.GetSetRelativePositionGcode())
				isRelativeLocal = True
			newSnapshotGcode.Commands.append(self.GetRelativeZLowerGcode())
			newSnapshotGcode.Commands.append(self.GetSetAbsolutePositionGcode())
			isRelativeLocal = False
		# detract
		if(hasRetracted):
			newSnapshotGcode.Commands.append(self.GetDetractGcode())

		# set to relative or absolute based on the unmodified position state
		if(position.IsRelative and not isRelativeLocal):
			newSnapshotGcode.Commands.append(self.GetSetRelativePositionGcode())
		elif (not position.IsRelative and isRelativeLocal):
			newSnapshotGcode.Commands.append(self.GetSetAbsolutePositionGcode())
			
		return newSnapshotGcode
	#
	def GetSetAbsolutePositionGcode(self):
		return "G90"
	def GetSetRelativePositionGcode(self):
		return "G91"

	def GetDelayGcode(self):
		return "G4 P{0:d}".format(self.Profile.snapshot.delay)
	
	def GetMoveGcode(self,x,y):
		return "G0 X{0:.3f} Y{1:.3f} F{2:.3f}".format(x,y,self.Printer.movement_speed)

	def GetRelativeZLiftGcode(self):
		return "G0 Z{0:.3f} F{1:.3f}".format(self.Printer.z_hop, self.Printer.movement_speed)
	def GetRelativeZLowerGcode(self):
		return "G0 Z{0:.3f} F{1:.3f}".format(-1.0*self.Printer.z_hop, self.Printer.movement_speed)


	def GetRetractGcode(self):
		return "G1 E{0:.3f} F{1:.3f}".format(self.Printer.retract_length,self.Printer.retract_speed)
	#
	def GetDetractGcode(self):
		return "G1 E{0:.3f} F{1:.3f}".format(-1* self.Printer.retract_length,self.Printer.retract_speed)
	def GetResetLineNumberGcode(self,lineNumber):
		return "M110 N{0:d}".format(lineNumber)
