# coding=utf-8
import re
from .gcode import Commands, Command
from .settings import *
import utility
class Position(object):

	def __init__(self,octolapseSettings, octoprintPrinterProfile):
		self.Settings = octolapseSettings
		self.Printer = self.Settings.CurrentPrinter()
		self.OctoprintPrinterProfile = octoprintPrinterProfile
		
		self.X = None
		self.XPrevious = None
		self.Y = None
		self.YPrevious = None
		self.Z = None
		self.ZPrevious = None
		self.E = 0
		self.EPrevious = 0
		self.IsRelative = None
		self.Extruder = Extruder(octolapseSettings)
		self.IsExtruderAlwaysRelative = self.Printer.is_e_relative
		self._IsExtruderRelative = True
		
		#StateTracking Vars
		self.Height = None
		self.HeightPrevious = None
		self.ZDelta = None
		self.DeltaPrevious = None
		self.Layer = 0
		self.HasReachedZMin = False

		# State Flags
		self.IsLayerChange = False
		self.IsZHop = False

		if(self.Printer.z_hop is None):
			self.Printer.z_hop = 0
		
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
		self.IsRelative = None
		self._IsExtruderRelative = None
		if(self.IsExtruderAlwaysRelative):
			self._IsExtruderRelative = True
			self.E=0
			self.EPrevious = 0
		
		# State Tracking Vars
		self.Height = None
		self.HeightPrevious = None
		self.ZDelta = None
		self.ZDeltaPrevious = None
		self.Layer = 0
		self.HasReachedZMin = False
		# State Flags
		self.IsLayerChange = False

	def IsExtruderRelative(self, isRelative=None):
		if(isRelative is not None):
			self._isExtruderRelative = isRelative
		else:
			return  self.IsExtruderAlwaysRelative or (self._isExtruderRelative is not None and self._isExtruderRelative)


		
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
					self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received {0}".format(command.Name))
					x = parsedCommand["X"]
					y = parsedCommand["Y"]
					z = parsedCommand["Z"]
					e = parsedCommand["E"]

					if(x is not None or y is not None or z is not None):
						if(self.IsRelative is not None):
							if(self.HasPositionError and not self.IsRelative):
								self.HasPositionError = False
								self.PositionError = ""
							self.UpdatePosition(x,y,z,e=None)
						else:
							self.Settings.CurrentDebugProfile().LogError("Position - Unable to update the x,y,z axis coordinates, no coordinate system has been selected (absolute/relative).")
					if(e is not None):
						if(self.IsExtruderRelative() is not None):
							if(self.HasPositionError and not self.IsExtruderRelative()):
								self.HasPositionError = False
								self.PositionError = ""
							self.UpdatePosition(x=None,y=None,z=None,e=e)
						else:
							self.Settings.CurrentDebugProfile().LogError("Position - Unable to update the extruder position, no extruder coordinate system has been selected (absolute/relative).")
					message = "Position Change - {0} - {1} Move From(X:{2:s},Y:{3:s},Z:{4:s},E:{5:s}) - To(X:{6},Y:{7},Z:{8},E:{9})"
					message = message.format(command.Command,"Relative" if self.IsRelative else "Absolute", x,y,z,e,self.X, self.Y, self.Z, self.E)
					self.Settings.CurrentDebugProfile().LogPositionChange(message)
				else:
					self.Settings.CurrentDebugProfile().LogError("Position - Unable to parse the gcode command: {0}".format(gcode))
			elif(command.Command == "G28"):
				self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received G28 - Homing to {0}".format(self.GetFormattedCoordinates(0,0,0,self.E)))
				self.UpdatePosition(x=0,y=0,z=0,e=None,force = True)
				self.HasHomedAxis = True
				self.HasPositionError = False
				self.PositionError = None
				
			elif(command.Command == "G90"):
				if(self.IsRelative is None or self.IsRelative):
					self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received G90 - Switching to Absolute Coordinates.")
				else:
					self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received G90 - Already in absolute coordinates.")
				self.IsRelative = False
			elif(command.Command == "G91"):
				if(self.IsRelative is None or not self.IsRelative):
					self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received G91 - Switching to Relative Coordinates")
				else:
					self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received G91 - Already using relative Coordinates")
				self.IsRelative = True
			elif(command.Command == "M83"):
				if(self.IsExtruderRelative() is None or self.IsExtruderRelative()):
					self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received M83 - Switching Extruder to Relative Coordinates")
					self.E = 0
					self.EPrevious = 0
				self.IsExtruderRelative(True);
			elif(command.Command == "M82"):
				if(not self.IsExtruderAlwaysRelative):
					if(self.IsExtruderRelative() is None or not self.IsExtruderRelative()):
						self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received M82 - Switching Extruder to Absolute Coordinates")
					self.IsExtruderRelative(False)
					self.E = 0
					self.EPrevious = 0
					self.UpdatePosition(x=None, y=None, z=None, e=0)
				else:
					self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received M82 - Ignoring, extruder is always relative.")
			elif(command.Command == "G92"):
				self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received G92 - Switching Extruder to Absolute Coordinates")
				parsedCommand = command.Parse(gcode)
				if(parsedCommand):
					previousRelativeValue = self.IsRelative
					previousExtruderRelativeValue = self.IsExtruderRelative()
					
					x = parsedCommand["X"]
					y = parsedCommand["Y"]
					z = parsedCommand["Z"]
					e = parsedCommand["E"]
					self.IsRelative = x is not None or y is not None or z is not None
					
					self.IsExtruderRelative(e is not None)

					if(x is None and y is None and z is None and e is None):
						self.IsRelative = True
						self.IsExtruderRelative(True)
						self.UpdatePosition(x=0,y=0,z=0,e=0)
					else:
						self.UpdatePosition(x=x,y=y,z=z,e=e)

					if(previousRelativeValue is not None):
						self.IsRelative = previousRelativeValue
					if(previousExtruderRelativeValue is not None):
						self.IsExtruderRelative(previousExtruderRelativeValue)
				else:
					self.Settings.CurrentDebugProfile().LogError("Position - Unable to parse the Gcode:{0}".format(gcode))
			if(self.X != self.XPrevious
				or self.Y != self.YPrevious
				or self.Z != self.ZPrevious
				or self.ERelative() != 0
			):
				self.HasPositionChanged = True;
				self.Settings.CurrentDebugProfile().LogPositionChange("Position Change - {0} move from - {1} - to- {2}".format("Relative" if self.IsRelative else "Absolute", self.GetFormattedCoordinates(self.XPrevious,self.YPrevious,self.ZPrevious,self.EPrevious),self.GetFormattedCoordinates(self.X, self.Y, self.Z, self.E)))

		# Update the extruder monitor
		self.Extruder.Update(self)
		# track any layer/height increment changes

		# determine if we've reached ZMin
		if(not self.HasReachedZMin and self.Z <= self.Printer.z_min and self.Extruder.IsExtruding):
			self.HasReachedZMin = True
			self.Settings.CurrentDebugProfile().LogPositionZminReached("Position - Reached ZMin:{0}.".format(self.Printer.z_min))
		# If we've not reached z min, leave!
		if(not self.HasReachedZMin):
			self.Settings.CurrentDebugProfile().LogPositionZminReached("Position - ZMin not reached.")
		else:
			# calculate Height
			if self.Extruder.IsExtruding and self.HasReachedZMin and self.Z > self.Height:
				self.Height = self.Z
				self.Settings.CurrentDebugProfile().LogPositionHeightChange("Position - Reached New Height:{0}.".format(self.Height))

			# calculate ZDelta
			if(self.Height is not None and self.HeightPrevious is not None):
				self.ZDelta = self.Height - self.HeightPrevious

			# calculate layer change
			if(self.ZDelta is not None and self.ZDelta > 0):
				self.IsLayerChange = True
				self.Layer += 1
				self.Settings.CurrentDebugProfile().LogPositionLayerChange("Position - Layer:{0}.".format(self.Layer))
			else:
				self.IsLayerChange = False

			# Is this a ZHOp?
			self.Settings.CurrentDebugProfile().LogInfo("Zhop:{0}, ZRelative:{1}, Extruder-IsExtruding:{2}, Extruder-IsRetracted:{3}, Extruder-IsRetracting:{4}".format(
				self.Printer.z_hop, self.ZRelative(), self.Extruder.IsExtruding, self.Extruder.IsRetracted, self.Extruder.IsRetracting
			))
			if(self.ZRelative() is not None):
				self.IsZHop = self.Printer.z_hop > 0.0 and self.ZRelative() >= self.Printer.z_hop and (not self.Extruder.IsExtruding)
			if(self.IsZHop):
				self.Settings.CurrentDebugProfile().LogPositionZHop("Position - Zhop:{0}".format(self.Printer.z_hop))
		

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

	def UpdatePosition(self,x=None,y=None,z=None,e=None, force = False):

		

		if(force):
			# Force the coordinates in as long as they are provided.
			#
			if(x is not None):
				self.X = x
				if(self.XPrevious is None):
					self.XPrevious = x
			if(y is not None):
				self.Y = y
				if(self.YPrevious is None):
					self.YPrevious = y
			if(z is not None):
				self.Z = z
				if(self.ZPrevious is None):
					self.ZPrevious = z
			return

		if(not self.HasHomedAxis):
			return

		if(self.IsRelative is not None):
			# Update the previous positions if values were supplied
			if(x is not None):
				x = float(x)
				#self.XPrevious = self.X
				if(self.IsRelative is not None):
					if(self.IsRelative):
						if(self.X is None):
							self.X = 0
							self.XPrevious = 0

						self.X += x
					else:
						self.X = x

			if(y is not None):
				y = float(y)
				if(self.IsRelative is not None):
					if(self.IsRelative):
						if(self.Y is None):
							self.Y = 0
							self.YPrevious = 0
						self.Y += y
					else:
						self.Y = y

			if(z is not None):
				z = float(z)
				if(self.IsRelative is not None):
					if(self.IsRelative):
						if(self.Z is None):
							self.Z = 0
							self.ZPrevious = 0
						self.Z += z
					else:
						self.Z = z
		if(self._IsExtruderRelative is not None):
			if(e is not None):
				e = float(e)
				if(self._IsExtruderRelative is not None):
					if(self._IsExtruderRelative):
						if(self.E is None):
							self.E = 0
							self.EPrevious = 0
						self.E += e
					else:
						self.E = e

		if(not self.IsInBounds()):
			self.HasPositionError = True
			self.PositionError = "Position - Coordinates {0} are out of the printer area!  Cannot resume position tracking until the axis is homed, or until absolute coordinates are received.".format(self.GetFormattedCoordinates(self.X,self.Y,self.Z,self.E))
			self.Settings.CurrentDebugProfile().LogError(self.PositionError)
		else:
			self.HasPositionError = False
			self.PositionError = None
	def IsInBounds(self):

		isInBounds = True
	
		if(self.OctoprintPrinterProfile["volume"]["custom_box"] != False):
			customBox = self.OctoprintPrinterProfile["volume"]["custom_box"]
			if(self.X is not None and (self.X < customBox["x_min"] or self.X > customBox["x_max"])):
				self.X = None
				isInBounds = False
			if(self.Y is not None and (self.Y < customBox["y_min"] or self.Y > customBox["y_max"])):
				self.Y = None
				isInBounds = False
			if(self.Z is not None and (self.Z < customBox["z_min"] or self.Z > customBox["z_max"])):
				self.Z = None
				isInBounds = False
		else:
			volume = self.OctoprintPrinterProfile["volume"]
			if(self.X is not None and (self.X < 0 or self.Z > volume.height)):
				self.X = None
				isInBounds = False
			if(self.Y is not None and(self.Y < 0 or self.Y > volume.height)):
				self.Y = None
				isInBounds = False
			if(self.Z is None and (self.Z < 0 or self.Z > volume.height)):
				self.Z = None
				isInBounds = False
		return isInBounds

class Extruder(object):
	"""The extruder monitor only works with relative extruder values"""
	def __init__(self,octolapseSettings):
		self.Settings = octolapseSettings
		
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
			self.Settings.CurrentDebugProfile().LogExtruderChange("Extruder Changed: E:{0}, Retraction:{1} IsExtruding:{2}-{3}, IsExtrudingStart:{4}-{5}, IsPrimed:{6}-{7}, IsRetracting:{8}-{9}, IsRetracted:{10}-{11}, IsDetracting:{12}-{13}, IsTriggered:{14}"
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
			self.Settings.CurrentDebugProfile().LogExtruderTriggered("Triggered E:{0}, Retraction:{1} IsExtruding:{2}-{3}, IsExtrudingStart:{4}-{5}, IsPrimed:{6}-{7}, IsRetracting:{8}-{9}, IsRetracted:{10}-{11}, IsDetracting:{12}-{13}, IsTriggered:{14}"
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
