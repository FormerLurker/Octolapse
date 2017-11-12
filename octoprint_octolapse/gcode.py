import re
import collections
import string
import operator

class SnapshotGcode(object):
	def __init__(self):
		self.Commands = []
		self.X = 0
		self.Y = 0
		self.Z = 0
		self.Layer = 0

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
        return self.store[self.__keytransform__(key)]

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
        safeDict = SafeDict();
        for key in self.Parameters:
            value = self.Parameters[key].Value
            safeDict.clear()
            if(value is None):
                value = "None"
            
            safeDict[key] = value;
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
    ,regex="(?i)^[gG0]{1,3}(?:\s+x-?(?P<x>[0-9.]{1,15})|\s+y-?(?P<y>[0-9.]{1,15})|\s+z-?(?P<z>[0-9.]{1,15})|\s+e-?(?P<e>[0-9.]{1,15})|\s+f-?(?P<f>[0-9.]{1,15}))*$"
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
    ,regex="^[gG1]{1,3}(?:\s+x-?(?P<x>[0-9.]{1,15})|\s+y-?(?P<y>[0-9.]{1,15})|\s+z-?(?P<z>[0-9.]{1,15})|\s+e-?(?P<e>[0-9.]{1,15})|\s+f-?(?P<f>[0-9.]{1,15}))*$"
    ,displayTemplate="Position: X={X}, Y={Y}, Z={Z}, E={E}, F={F}{CommentTemplate}"
    ,parameters = [CommandParameter("X",group=1),
                    CommandParameter("Y",group=2),
                    CommandParameter("Z",group=3),
                    CommandParameter("E",group=4),
                    CommandParameter("F",group=5)
                    ]
        )
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
        
        code = GetGcodeFromString(code)
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
        index = 0;

        for key in self.keys():
            self.keys[index] = str(key)
            index += 1
            
    def __missing__(self, key):
        return '{' + key + '}'
	
class GCode(object):
	
	CurrentXPathIndex = 0
	CurrentYPathIndex = 0
	def __init__(self,printer,profile,octoprint_printer_profile):
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
	def CheckX(self,x):
		hasError = False
		if(self.OctoprintPrinterProfile["volume"]["custom_box"] == True and (x<self.OctoprintPrinterProfile["volume"]["custom_box"]["x_min"] or x > self.OctoprintPrinterProfile["volume"]["custom_box"]["x_max"])):
			hasError = True
		elif(x<0 or x > self.OctoprintPrinterProfile["volume"]["width"]):
			hasError = True
		if(hasError):
			
			raise ValueError('The X coordinate {0} was outside the bounds of the printer!'.format(x))
	def CheckY(self,y):
		hasError = False
		if(self.OctoprintPrinterProfile["volume"]["custom_box"] == True and (y<self.OctoprintPrinterProfile["volume"]["custom_box"]["y_min"] or y > self.OctoprintPrinterProfile["volume"]["custom_box"]["y_max"])):
			hasError = True
		elif(y<0 or y > self.OctoprintPrinterProfile["volume"]["depth"]):
			hasError = True
		if(hasError):
			raise ValueError('The Y coordinate $s was outside the bounds of the printer!'% (y))
	def CheckZ(self,z):
		hasError = False
		if(self.OctoprintPrinterProfile["volume"]["custom_box"] == True and (z < self.OctoprintPrinterProfile["volume"]["custom_box"]["z_min"] or z > self.OctoprintPrinterProfile["volume"]["custom_box"]["z_max"])):
			hasError = True
		elif(z<0 or z > self.OctoprintPrinterProfile["volume"]["height"]):
			hasError = True
		if(hasError):
			raise ValueError('The Z coordinate $s was outside the bounds of the printer!'% (z))
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
		self.CheckX(xCoord)
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
		self.CheckY(yCoord)
		return yCoord
	def GetSnapshotGcode(self):
		newSnapshotGcode = SnapshotGcode()
		if(self.Profile.snapshot.retract_before_move):
			newSnapshotGcode.Commands.append(GetRetractGCode())
		for cmd in self.Printer.snapshot_gcode:
			if(cmd.lstrip().startswith(self.Printer.snapshot_command)):
				return "; The snapshot gcode cannot contain the snapshot command!";
			newSnapshotGcode.X = self.GetXCoordinateForSnapshot()
			newSnapshotGcode.Y = self.GetYCoordinateForSnapshot()
			newSnapshotGcode.Commands.append(cmd.format(newSnapshotGcode.X, newSnapshotGcode.Y,self.Printer.movement_speed,self.Profile.snapshot.delay))
		if(self.Profile.snapshot.retract_before_move):
			newSnapshotGcode.Commands.append(GetDetractGcode()) 
		return newSnapshotGcode
	#
	def GetRetractGcode(self):
		return "G1 E{0:f} F{1:f}".format(self.Printer.retract_length,self.Printer.retract_speed)
	#
	def GetDetractGcode(self):
		return "G1 E{0:f} F{1:f}".format(-1* self.Printer.retract_length,self.Printer.retract_speed)
