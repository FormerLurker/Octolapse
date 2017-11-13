import re
from .gcode import Commands, Command

class Position(object):

	def __init__(self,octoprintPrinterProfile, isRelative = False):
		self.Printer = octoprintPrinterProfile
		self.X = None
		self.__XPrevious = None
		self.Y = None
		self.__YPrevious = None
		self.Z = None
		self.__ZPrevious = None
		self.E = None
		self.__EPrevious = None
		self.IsRelative = isRelative
		self.HasHomedAxis = False
		self.Commands = Commands()

	def Reset(self):
		self.X = None
		self.__XPrevious = None
		self.Y = None
		self.__YPrevious = None
		self.Z = None
		self.__ZPrevious = None
		self.E = None
		self.__EPrevious = None
		self.HasHomedAxis = False

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
				#print ("X:{0:s},Y:{1:s},Z:{2:s},E:{3:s}".format(x,y,z,e))
				self.UpdatePosition(x,y,z,e)
			elif(command.Command == "G28"):
				#print ("Go To Origin: Resseting to 0,0,0");
				previousRelativeValue = self.IsRelative
				self.IsRelative = False
				self.UpdatePosition(x=0,y=0,z=0)
				self.HasHomedAxis = True
				self.IsRelative = previousRelativeValue
			elif(command.Command == "G90"):
				self.IsRelative = False
			elif(command.Command == "G91"):
				self.IsRelative = True
		if(not self.HasHomedAxis):
			self.Reset()

	def UpdatePosition(self,x=None,y=None,z=None,e=None):
		"""Updates the positions based on the IsRelative parmeter.  Always reports absolute location"""
		"""# note, the E value will be treated as relative even if IsRelative = False"""

		
		# Update the previous positions if values were supplied
		if(x is not None):
			x = float(x)
			self.__XPrevious = self.X
			if(self.IsRelative):
				self.X += x
			else:
				self.X = x

		if(y is not None):
			y = float(y)
			self.__YPrevious = self.Y
			if(self.IsRelative):
				self.Y += y
			else:
				self.Y = y

		if(z is not None):
			z = float(z)
			self.__ZPrevious = self.Z
			if(self.IsRelative):
				self.Z += z
			else:
				self.Z = z

		if(e is not None):
			e = float(e)
			self.__EPrevious = self.E
			if(self.IsRelative):
				self.E += e
			else:
				self.E = e
	def IsInBounds(self, position):
		
		if(self.OctoprintPrinterProfile["volume"]["custom_box"] != False):
			customBox = self.OctoprintPrinterProfile["volume"]["custom_box"]
			if(position.Z < customBox["z_min"] or position.Z > customBox["z_max"]):
				return False
		else:
			volume = self.OctoprintPrinterProfile["volume"]
			if(position.Z < 0):
				return False
			if(position.Z > volume.height):
				return False
		return True
