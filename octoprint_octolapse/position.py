import re
from .gcode import Commands, Command

class Position(object):

	def __init__(self,octoprintPrinterProfile, octoprintLogger,isRelative = False, isExtruderRelative = True):
		self.Printer = octoprintPrinterProfile
		self.Logger = octoprintLogger
		self.X = None
		self.XPrevious = None
		self.Y = None
		self.YPrevious = None
		self.Z = None
		self.ZPrevious = None
		self.E = None
		self.EPrevious = None
		self.IsRelative = isRelative
		self.__IsRelative_initial = isRelative
		self.IsExtruderRelative = isExtruderRelative
		self.__IsExtruderRelative_Initial = isExtruderRelative
		if(isExtruderRelative):
			self.E = 0
			self.EPrevious = 0
		if(isRelative):
			self.X = 0
			self.XPrevious = 0
			self.Y = 0
			self.YPrevious = 0
			self.Z = 0
			self.ZPrevious = 0
		self.HasHomedAxis = False
		self.Commands = Commands()
		self.HasPositionError = False
		self.PositionError = None

	def XRelative(self):
		if(self.X is None):
			return None
		if(self.XPrevious is None):
			return self.X
		else:
			return self.X-self.XPrevious
	def YRelative(self):
		if(self.Y is None):
			return None
		if(self.YPrevious is None):
			return self.Y
		else:
			return self.Y-self.YPrevious
	def ZRelative(self):
		if(self.Z is None):
			return None
		if(self.ZPrevious is None):
			return self.Z
		else:
			return self.Z-self.ZPrevious
	def ERelative(self):
		if(self.E is None):
			return None
		if(self.EPrevious is None):
			return self.E
		else:
			return self.E-self.EPrevious
	def Reset(self):
		self.X = None
		self.XPrevious = None
		self.Y = None
		self.YPrevious = None
		self.Z = None
		self.ZPrevious = None
		self.E = None
		self.EPrevious = None
		self.HasHomedAxis = False
		self.HasPositionError = False
		self.PositionError = None
		self.IsExtruderRelative = self.__IsExtruderRelative_Initial
		
		if(self.IsExtruderRelative):
			self.E = 0
			self.EPrevious = 0

		self.IsRelative = self.__IsRelative_initial
		if(self.IsRelative):
			self.X = 0
			self.XPrevious = 0
			self.Y = 0
			self.YRelative = 0
			self.YPrevious = 0
			self.Z = 0
			self.ZRelative = 0
			self.ZPrevious = 0

	def Update(self,gcode):
		# disect the gcode and use it to update our position
		command = self.Commands.GetCommand(gcode)
		if(command is not None):
			if(command.Command in ["G0","G1"]):
				#Movement
				parsedCommand = command.Parse(gcode)
				x = parsedCommand["X"]
				y = parsedCommand["Y"]
				z = parsedCommand["Z"]
				e = parsedCommand["E"]
				
				self.Logger.info("Position - {0} - {1} Move - X:{2:s},Y:{3:s},Z:{4:s},E:{5:s}".format(command.Command,"Relative" if self.IsRelative else "Absolute", x,y,z,e))
				if(self.HasPositionError and not self.IsRelative):
					self.HasPositionError = False
					self.PositionError = ""
					self.Logger.info("Position - Absolute coordinates received, position error corrected")
				self.UpdatePosition(x,y,z,e)
				self.Logger.info("Position - Current Absolute Position - X:{0},Y:{1},Z:{2},E:{3}"
					 .format(self.X, self.Y, self.Z, self.E))
			elif(command.Command == "G28"):
				previousRelativeValue = self.IsRelative
				self.IsRelative = False
				self.UpdatePosition(x=0,y=0,z=0,e=0)
				self.HasHomedAxis = True
				self.HasPositionError = False
				self.PositionError = None
				self.IsRelative = previousRelativeValue
				self.Logger.info("Position - G28 - Go To Origin - Resseting position to 0,0,0")
			elif(command.Command == "G90"):
				if(self.IsRelative):
					self.Logger.info("Position - G90 - Switching to Absolute Coordinates")
				self.IsRelative = False
			elif(command.Command == "G91"):
				if(not self.IsRelative):
					self.Logger.info("Position - G90 - Switching to Relative Coordinates")
				self.IsRelative = True
			elif(command.Command == "M83"):
				if(self.IsExtruderRelative):
					self.Logger.info("Position - M83 - Switching Extruder to Absolute Coordinates")
				self.IsExtruderRelative = false
			elif(command.Command == "M82"):
				if(not self.IsExtruderRelative):
					self.Logger.info("Position - M82 - Switching Extruder to Relative Coordinates")
				self.IsExtruderRelative = True
			elif(command.Command == "G92"):
				parsedCommand = command.Parse(gcode)
				previousRelativeValue = self.IsRelative
				self.IsRelative = False
				x = parsedCommand["X"]
				y = parsedCommand["Y"]
				z = parsedCommand["Z"]
				e = parsedCommand["E"]
				if(x is None and y is None and z is None and e is None):
					self.UpdatePosition(x=0,y=0,z=0,e=0)
				else:
					self.UpdatePosition(x=x,y=y,z=z,e=e)
				self.IsRelative = previousRelativeValue
				self.Logger.info("Position - G92 - Resettings extruder to {0}.",e)
				self.E
		if(not self.HasHomedAxis):
			self.Reset()

	def UpdatePosition(self,x=None,y=None,z=None,e=None):
				
		if(self.HasPositionError):
			self.Logger.Error(self.PositionError)
			return
		if(
			(
				(self.X is None and x is not None) or (self.Y is None and y is not None) or (self.Z is None and z is not None)
			) 
			and self.IsRelative
		):
			self.HasPositionError = True
			self.PositionError = "Position - Unable to track printer position.  Received relative coordinates, but are unaware of the previous position!"
			self.Logger.Error(self.PositionError)
			return
		# Update the previous positions if values were supplied
		if(x is not None):
			x = float(x)
			self.XPrevious = self.X
			if(self.IsRelative):
				self.X += x
			else:
				self.X = x

		if(y is not None):
			y = float(y)
			self.YPrevious = self.Y
			if(self.IsRelative):
				self.Y += y
			else:
				self.Y = y

		if(z is not None):
			z = float(z)
			self.ZPrevious = self.Z
			if(self.IsRelative):
				self.Z += z
			else:
				self.Z = z

		if(e is not None):
			e = float(e)
			self.EPrevious = self.E
			if(self.IsExtruderRelative):
				if(self.E is None):
					self.E = 0
				self.E += e
			else:
				self.E = e

		if(not self.IsInBounds()):
			self.HasPositionError = True
			self.PositionError = "Position - Coordinates x{0} y{1} z{2} are out of the printer area!  Cannot resume position tracking until the axis is homed, or until absolute coordinates are received.".format(self.X,self.Y,self.Z)
			self.Logger.error(self.PositionError)
	def IsInBounds(self ):
		
		if(self.Printer["volume"]["custom_box"] != False):
			customBox = self.Printer["volume"]["custom_box"]
			
			if(self.X is None or self.X < customBox["x_min"] or self.Z > customBox["x_max"]):
				self.X = None
			if(self.Y is None or self.Y < customBox["y_min"] or self.Z > customBox["y_max"]):
				self.Y = None	
			if(self.Z is None or self.Z < customBox["z_min"] or self.Z > customBox["z_max"]):
				self.Z = None
		else:
			volume = self.Printer["volume"]
			if(self.X is None or self.X < 0 or self.Z > volume.height):
				self.X = None
			if(self.Y is None or self.Y < 0 or self.Y > volume.height):
				self.Y = None
			if(self.Z is None or self.Z < 0 or self.Z > volume.height):
				self.Z = None
			
		return not (self.X is None or self.Y is None or self.Z is None)
