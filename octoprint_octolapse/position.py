# coding=utf-8
import re
from .gcode import Commands, Command
from .settings import *
import utility
class Position(object):

	def __init__(self,octoprintPrinterProfile, debugSettings,zMin,zHop, isRelative = False, isExtruderRelative = True):
		self.Printer = octoprintPrinterProfile
		self.Debug = debugSettings
		self.X = None
		self.XPrevious = None
		self.Y = None
		self.YPrevious = None
		self.Z = None
		self.ZPrevious = None
		self.E = None
		self.EPrevious = None
		self.IsRelative = isRelative
		self.Extruder = Extruder(debugSettings)
		self.__IsRelative_initial = isRelative
		self.IsExtruderRelative = isExtruderRelative
		self.__IsExtruderRelative_Initial = isExtruderRelative
		self.ZMin = zMin
		self.ZHop = zHop

		#StateTracking Vars
		self.Height = 0
		self.HeightPrevious = 0
		self.ZDelta = None
		self.DeltaPrevious = None
		self.Layer = 0
		self.HasReachedZMin = False

		# State Flags
		self.IsLayerChange = False
		self.IsZHop = False

		if(self.ZHop is None):
			self.ZHop = 0
		
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
		# State Tracking Vars
		self.Height = 0
		self.HeightPrevious = 0
		self.ZDelta = None
		self.ZDeltaPrevious = None
		self.Layer = 0
		self.HasReachedZMin = False
		# State Flags
		self.IsLayerChange = False

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
	def LogPosition():
		if(self.IsPositionChange):
			message = "Position Change - {0} - {1} Move From(X:{2:s},Y:{3:s},Z:{4:s},E:{5:s}) - To(X:{6},Y:{7},Z:{8},E:{9})"
			message = message.format(command.Command,"Relative" if self.IsRelative else "Absolute", x,y,z,e,self.X, self.Y, self.Z, self.E)
			self.Debug.LogPositionChange(message)
	def Update(self,gcode):
		# disect the gcode and use it to update our position
		self.HasPositionChanged = False
		self.XPrevious = self.X
		self.YPrevious = self.Y
		self.ZPrevious = self.Z
		self.EPrevious = self.E
		# reset state variables
		self.IsLayerChange = False

		self.IsZHop = False
		# save any previous values that will be needed later
		self.HeightPrevious = self.Height
		self.ZDeltaPrevious = self.ZDelta

		command = self.Commands.GetCommand(gcode)
		if(command is not None):
			if(command.Command in ["G0","G1"]):
				#Movement
				parsedCommand = command.Parse(gcode)
				if(parsedCommand):
					x = parsedCommand["X"]
					y = parsedCommand["Y"]
					z = parsedCommand["Z"]
					e = parsedCommand["E"]
					self.Debug.LogPositionCommandReceived("Received {0}".format(command.Name))
					if(self.HasPositionError and not self.IsRelative):
						self.HasPositionError = False
						self.PositionError = ""
					self.UpdatePosition(x,y,z,e)
				else:
					self.Debug.LogError("Position - Unable to parse the gcode command: {0}".format(gcode))
			elif(command.Command == "G28"):
				self.Debug.LogPositionCommandReceived("Received G28 - Homing to {0}".format(self.GetFormattedCoordinates(0,0,0,self.E)))
				previousRelativeValue = self.IsRelative
				previousExtruderRelativeValue = self.IsExtruderRelative
				self.IsExtruderRelative = False
				self.IsRelative = False
				self.HasHomedAxis = True
				self.UpdatePosition(x=0,y=0,z=0,e=0)
				self.HasPositionError = False
				self.PositionError = None
				self.IsRelative = previousRelativeValue
				self.IsExtruderRelative = previousExtruderRelativeValue 
			elif(command.Command == "G90"):
				if(self.IsRelative):
					self.Debug.LogPositionCommandReceived("Received G90 - Switching to Absolute Coordinates.")
				else:
					self.Debug.LogPositionCommandReceived("Received G90 - Already in absolute coordinates.")
				self.IsRelative = False
			elif(command.Command == "G91"):
				if(not self.IsRelative):
					self.Debug.LogPositionCommandReceived("Received G91 - Switching to Relative Coordinates")
				else:
					self.Debug.LogPositionCommandReceived("Received G91 - Already using relative Coordinates")
				self.IsRelative = True
			elif(command.Command == "M83"):
				if(self.IsExtruderRelative):
					self.Debug.LogPositionCommandReceived("Received M83 - Switching Extruder to Relative Coordinates")
				self.IsExtruderRelative = True
			elif(command.Command == "M82"):
				if(not self.IsExtruderRelative):
					self.Debug.LogPositionCommandReceived("Received M82 - Switching Extruder to Absolute Coordinates")
				self.IsExtruderRelative = False
			elif(command.Command == "G92"):
				self.Debug.LogPositionCommandReceived("Received G92 - Switching Extruder to Absolute Coordinates")
				parsedCommand = command.Parse(gcode)
				if(parsedCommand):
					previousRelativeValue = self.IsRelative
					previousExtruderRelativeValue = self.IsExtruderRelative
					self.IsRelative = False
					self.IsExtruderRelative = False
					x = parsedCommand["X"]
					y = parsedCommand["Y"]
					z = parsedCommand["Z"]
					e = parsedCommand["E"]
					
					if(x is None and y is None and z is None and e is None):
						self.UpdatePosition(x=0,y=0,z=0,e=0)
					else:
						self.UpdatePosition(x=x,y=y,z=z,e=e)
					self.IsRelative = previousRelativeValue
					self.IsExtruderRelative = previousExtruderRelativeValue
				else:
					self.Debug.LogError("Position - Unable to parse the Gcode:{0}".format(gcode))
			if(self.X != self.XPrevious
				or self.Y != self.YPrevious
				or self.Z != self.ZPrevious
				or self.ERelative() != 0
			):
				self.HasPositionChanged = True;
				self.Debug.LogPositionChange("Position Change - {0} move from - {1} - to- {2}".format("Relative" if self.IsRelative else "Absolute", self.GetFormattedCoordinates(self.XPrevious,self.YPrevious,self.ZPrevious,self.EPrevious),self.GetFormattedCoordinates(self.X, self.Y, self.Z, self.E)))

		# Update the extruder monitor
		self.Extruder.Update(self)
		# track any layer/height increment changes

		# determine if we've reached ZMin
		if(not self.HasReachedZMin and self.Z <= self.ZMin and self.Extruder.IsExtruding):
			self.HasReachedZMin = True
			self.Debug.LogPositionZminReached("Position - Reached ZMin:{0}.".format(self.ZMin))
		# If we've not reached z min, leave!
		if(not self.HasReachedZMin):
			self.Debug.LogPositionZminReached("Position - ZMin not reached.")
		else:
			# calculate Height
			if self.Extruder.IsExtruding and self.HasReachedZMin and self.Z > self.Height:
				self.Height = self.Z
				self.Debug.LogPositionHeightChange("Position - Reached New Height:{0}.".format(self.Height))

			# calculate ZDelta
			self.ZDelta = self.Height - self.HeightPrevious

			# calculate layer change
			if(self.ZDelta > 0):
				self.IsLayerChange = True
				self.Layer += 1
				self.Debug.LogPositionLayerChange("Position - Layer:{0}.".format(self.Layer))
			else:
				self.IsLayerChange = False

			# Is this a ZHOp?
			self.Debug.LogInfo("Zhop:{0}, ZRelative:{1}, Extruder-IsExtruding:{2}, Extruder-IsRetracted:{3}, Extruder-IsRetracting:{4}".format(
				self.ZHop, self.ZRelative(), self.Extruder.IsExtruding, self.Extruder.IsRetracted, self.Extruder.IsRetracting
			))
			self.IsZHop = self.ZHop > 0.0 and self.ZRelative() >= self.ZHop and (not self.Extruder.IsExtruding)
			if(self.IsZHop):
				self.Debug.LogPositionZHop("Position - Zhop:{0}".format(self.ZHop))
		

	def GetFormattedCoordinates(self,x,y,z,e):
		xString = "None"
		if(x is not None):
			xString = "{0:.4f}".format(float(x))

		yString = "None"
		if(y is not None):
			yString = "{0:.4f}".format(float(y))

		zString = "None"
		if(z is not None):
			zString = "{0:.4f}".format(float(z))

		eString = "None"
		if(e is not None):
			eString = "{0:.5f}".format(float(e))

		return "(X:{0},Y:{1},Z:{2},E:{3})".format(xString,yString,zString,eString)

	def UpdatePosition(self,x=None,y=None,z=None,e=None):
		if(not self.HasHomedAxis):
			return

		if(self.HasPositionError):
			self.Debug.LogError(self.PositionError)
			return
		if(
			(
				(self.X is None and x is not None) or (self.Y is None and y is not None) or (self.Z is None and z is not None)
			) 
			and self.IsRelative
		):
			self.HasPositionError = True
			self.PositionError = "Position - Unable to track printer position.  Received relative coordinates, but are unaware of the previous position!"
			self.Debug.LogError(self.PositionError)
			return
		# Update the previous positions if values were supplied
		if(x is not None):
			x = float(x)
			#self.XPrevious = self.X
			if(self.IsRelative):
				self.X += x
			else:
				self.X = x

		if(y is not None):
			y = float(y)
			#self.YPrevious = self.Y
			if(self.IsRelative):
				self.Y += y
			else:
				self.Y = y

		if(z is not None):
			z = float(z)
			#self.ZPrevious = self.Z
			if(self.IsRelative):
				self.Z += z
			else:
				self.Z = z

		if(e is not None):
			e = float(e)
			#self.EPrevious = self.E
			if(self.IsExtruderRelative):
				if(self.E is None):
					self.E = 0
				self.E += e
			else:
				self.E = e

		if(not self.IsInBounds()):
			self.HasPositionError = True
			self.PositionError = "Position - Coordinates {0} are out of the printer area!  Cannot resume position tracking until the axis is homed, or until absolute coordinates are received.".format(self.GetFormattedCoordinates(self.X,self.Y,self.Z,self.E))
			self.Debug.LogError(self.PositionError)
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
class Extruder(object):
	"""The extruder monitor only works with relative extruder values"""
	def __init__(self,debugSettings):
		self.Debug = debugSettings
		self.ExtrusionLengthTotal = 0.0
		self.__ExtrusionLengthTotalPrevious = 0.0
		self.Extruded = 0.0
		self.RetractionLength = 0.0
		self.__RetractionLengthPrevious = 0.0
		self.ExtrusionLength = 0.0
		self.IsExtrudingStart = False
		self.__IsExtrudingStartPrevious = False
		self.IsExtruding = False
		self.__IsExtrudingPrevious = False
		self.IsPrimed = False
		self.__IsPrimedtPrevious = False
		self.IsRetracting = False
		self.__IsRetractingPrevious = False
		self.IsRetracted = False
		self.__IsRetractedPrevious = False
		self.IsDetracting = False
		self.__IsDetractingPrevious = False
		self.HasChanged = False
		self.__E = 0.0
		
	def Reset(self):
		self.ExtrusionLengthTotal = 0.0
		self.__ExtrusionLengthTotalPrevious = 0.0
		self.RetractionLength = 0.0
		self.__RetractionLengthPrevious = 0.0
		self.ExtrusionLength = 0.0
		self.IsExtrudingStart = False
		self.__IsExtrudingStartPrevious = False
		self.IsExtruding = False
		self.__IsExtrudingPrevious = False
		self.IsPrimed = False
		self.__IsPrimedtPrevious = False
		self.IsRetracting = False
		self.__IsRetractingPrevious = False
		self.IsRetracted = False
		self.__IsRetractedPrevious = False
		self.IsDetracting = False
		self.__IsDetractingPrevious = False
		self.HasChanged = False
		self.__E = 0.0

	# Update the extrusion monitor.  E (extruder delta) must be relative, not absolute!
	def Update(self,position):
		e = position.ERelative()
		if(e is None or abs(e)< utility.FLOAT_MATH_EQUALITY_RANGE):
			e = 0.0
		

		self.__E =e
		# Record the previous values
		self.__ExtrusionLengthTotalPrevious = self.ExtrusionLengthTotal
		self.__RetractionLengthPrevious = self.RetractionLength 
		self.__IsExtrudingStartPrevious = self.IsExtrudingStart
		self.__IsExtrudingPrevious = self.IsExtruding
		self.__IsPrimedtPrevious = self.IsPrimed 
		self.__IsRetractingPrevious = self.IsRetracting
		self.__IsRetractedPrevious = self.IsRetracted
		self.__IsDetractingPrevious = self.IsDetracting


		# Update ExtrusionTotal,RetractionLength and ExtrusionLength
		
		self.ExtrusionLengthTotal += self.__E
		amountExtruded = self.__E + self.__RetractionLengthPrevious
		self.RetractionLength -= amountExtruded
		
		if(self.RetractionLength <= utility.FLOAT_MATH_EQUALITY_RANGE):
			self.RetractionLength = 0
		
		self.UpdateState()
		
	# If any values are edited manually (ExtrusionLengthTotal,ExtrusionLength, RetractionLength, __ExtrusionLengthTotalPrevious,__RetractionLengthPrevious,__IsExtrudingPrevious,
	# calling this will cause the state flags to recalculate
	def UpdateState(self):
		self.HasChanged = False
		self.IsExtruding = True if self.__RetractionLengthPrevious == 0 and self.__E > self.__RetractionLengthPrevious else False
		self.IsExtrudingStart = True if not self.__IsExtrudingPrevious and self.IsExtruding else False
		self.IsPrimed = True if self.__RetractionLengthPrevious - self.__E == 0 else False
		self.IsRetracted = True if self.__RetractionLengthPrevious > 0 and self.RetractionLength > 0 else False
		self.IsRetracting = True if self.__RetractionLengthPrevious == 0 and self.RetractionLength > 0 else False
		self.IsDetracting = True if self.__RetractionLengthPrevious>0 and self.RetractionLength - self.__E == 0 else False

		if(
			self.__RetractionLengthPrevious != self.RetractionLength 
			or self.__IsExtrudingStartPrevious != self.IsExtrudingStart
			or self.__IsExtrudingPrevious != self.IsExtruding
			or self.__IsPrimedtPrevious != self.IsPrimed 
			or self.__IsRetractingPrevious != self.IsRetracting
			or self.__IsRetractedPrevious != self.IsRetracted
			or self.__IsDetractingPrevious != self.IsDetracting
		):
			self.HasChange = True

		if(self.HasChanged):
			self.Debug.LogExtruderChange("Extruder Changed: E:{0}, Retraction:{1} IsExtruding:{2}-{3}, IsExtrudingStart:{4}-{5}, IsPrimed:{6}-{7}, IsRetracting:{8}-{9}, IsRetracted:{10}-{11}, IsDetracting:{12}-{13}, IsTriggered:{14}"
			.format( self.__E
				, self.RetractionLength
				, self.IsExtruding
				, extrudingTriggered
				, self.IsExtrudingStart
				, extrudingStartTriggered
				, self.IsPrimed
				, primedTriggered
				, self.IsRetracting
				, retractingTriggered
				, self.IsRetracted
				, retractedTriggered
				, self.IsDetracting
				, detractedTriggered
				, isTriggered))

	def IsTriggered(self, options):

		extrudingTriggered		= (options.OnExtruding and self.IsExtruding)
		extrudingStartTriggered	= (options.OnExtrudingStart and self.IsExtrudingStart)
		primedTriggered			= (options.OnPrimed and self.IsPrimed)
		retractingTriggered		= (options.OnRetracting and self.IsRetracting)
		retractedTriggered		= (options.OnRetracted and self.IsRetracted)
		detractedTriggered		= (options.OnDetracting and self.IsDetracting)
		isTriggered				= extrudingTriggered or extrudingStartTriggered or primedTriggered or retractingTriggered or retractedTriggered or detractedTriggered
		if(isTriggered):
			self.Debug.LogExtruderTriggered("Triggered E:{0}, Retraction:{1} IsExtruding:{2}-{3}, IsExtrudingStart:{4}-{5}, IsPrimed:{6}-{7}, IsRetracting:{8}-{9}, IsRetracted:{10}-{11}, IsDetracting:{12}-{13}, IsTriggered:{14}"
			.format( self.__E
				, self.RetractionLength
				, self.IsExtruding
				, extrudingTriggered
				, self.IsExtrudingStart
				, extrudingStartTriggered
				, self.IsPrimed
				, primedTriggered
				, self.IsRetracting
				, retractingTriggered
				, self.IsRetracted
				, retractedTriggered
				, self.IsDetracting
				, detractedTriggered
				, isTriggered))

		return isTriggered

class ExtruderTriggers(object):
	def __init__(self,onExtruding,OnExtrudingStart,OnPrimed,OnRetracting,OnRetracted,OnDetracting):
		self.OnExtruding = onExtruding
		self.OnExtrudingStart = OnExtrudingStart
		self.OnPrimed = OnPrimed
		self.OnRetracting = OnRetracting
		self.OnRetracted = OnRetracted
		self.OnDetracting = OnDetracting
