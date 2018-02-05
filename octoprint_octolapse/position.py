
# coding=utf-8
import re
from octoprint_octolapse.command import Commands, Command
from octoprint_octolapse.extruder import Extruder
from octoprint_octolapse.settings import *
import octoprint_octolapse.utility as utility

def GetFormattedCoordinates(x,y,z,e):
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

class Pos(object):
	def __init__(self, octoprintPrinterProfile, pos=None):
		self.OctoprintPrinterProfile = octoprintPrinterProfile
		#GCode
		self.GCode = None if pos is None else pos.GCode
		#F
		self.F = None if pos is None else pos.F
		#X
		self.X = None if pos is None else pos.X
		self.XOffset = 0 if pos is None else pos.XOffset
		self.XHomed = False if pos is None else pos.XHomed
		#Y
		self.Y = None if pos is None else pos.Y
		self.YOffset = 0 if pos is None else pos.YOffset
		self.YHomed = False if pos is None else pos.YHomed
		#Z
		self.Z = None if pos is None else pos.Z
		self.ZOffset = 0 if pos is None else pos.ZOffset
		self.ZHomed = False if pos is None else pos.ZHomed
		#E
		self.E = 0 if pos is None else pos.E
		self.EOffset = 0 if pos is None else pos.EOffset
		self.IsRelative = False if pos is None else pos.IsRelative
		self.IsExtruderRelative = True if pos is None else pos.IsExtruderRelative
		self.LastExtrusionHeight = 0 if pos is None else pos.LastExtrusionHeight
		#Layer and Height Tracking
		self.Layer = 0 if pos is None else pos.Layer
		self.Height = 0 if pos is None else pos.Height

		# State Flags
		self.IsLayerChange = False if pos is None else pos.IsLayerChange
		self.IsHeightChange = False if pos is None else pos.IsHeightChange
		self.IsZHop = False if pos is None else pos.IsZHop
		self.HasPositionChanged = False if pos is None else pos.HasPositionChanged
		self.HasStateChanged = False if pos is None else pos.HasStateChanged
		#Error Flags
		self.HasPositionError = False if pos is None else pos.HasPositionError
		self.PositionError = None if pos is None else pos.PositionError
		
	def ResetState(self):
		self.IsLayerChange = False
		self.IsHeightChange = False
		self.IsZHop = False
		self.HasPositionChanged = False 
		self.HasStateChanged = False
	def IsStateEqual(self, pos, tolerance):
		if(
				self.XHomed == pos.XHomed
			and self.YHomed == pos.YHomed
			and self.ZHomed == pos.ZHomed
			and self.IsLayerChange == pos.IsLayerChange
			and self.IsHeightChange == pos.IsHeightChange
			and self.IsZHop == pos.IsZHop
			and self.IsRelative == pos.IsRelative
			and self.IsExtruderRelative == pos.IsExtruderRelative
			and utility.round_to(pos.Layer, tolerance) != utility.round_to(self.Layer, tolerance)
			and utility.round_to(pos.Height, tolerance) != utility.round_to(self.Height, tolerance)
			and utility.round_to(pos.LastExtrusionHeight, tolerance) != utility.round_to(self.LastExtrusionHeight, tolerance)
			and self.HasPositionError == pos.HasPositionError
			and self.PositionError == pos.PositionError):
			return True
		
		return False
	
	def IsPositionEqual(self, pos, tolerance):
		if(	pos.X is not None
			and utility.round_to(pos.X, tolerance) == utility.round_to(self.X, tolerance)
			and pos.Y is not None
			and utility.round_to(pos.Y, tolerance) == utility.round_to(self.Y, tolerance)
			and pos.Z is not None
			and utility.round_to(pos.Z, tolerance) == utility.round_to(self.Z, tolerance)):
			return True
		return False

	def ToStateDict(self):
		return {
			"GCode":self.GCode,
			"XHomed" : self.XHomed,
			"YHomed" : self.YHomed,
			"ZHomed" : self.ZHomed,
			"IsLayerChange" : self.IsLayerChange,
			"IsHeightChange" : self.IsHeightChange,
			"IsZHop" : self.IsZHop,
			"IsRelative":self.IsRelative,
			"IsExtruderRelative":self.IsExtruderRelative,
			"Layer":self.Layer,
			"Height":self.Height,
			"LastExtrusionHeight":self.LastExtrusionHeight,
			"HasPositionError":self.HasPositionError,
			"PositionError":self.PositionError	
		}
	def ToPositionDict(self):
		return {
			"F":self.F,
			"X":self.X,
			"XOffset": self.XOffset,
			"Y":self.Y,
			"YOffset":self.YOffset,
			"Z":self.Z,
			"ZOffset":self.ZOffset,
			"E":self.E,
			"EOffset":self.EOffset,
			
		}
	def ToDict(self):
		return {
			"GCode":self.GCode,
			"F":self.F,
			"X":self.X,
			"XOffset": self.XOffset,
			"XHomed":self.XHomed,
			"Y":self.Y,
			"YOffset":self.YOffset,
			"YHomed":self.YHomed,
			"Z":self.Z,
			"ZOffset":self.ZOffset,
			"ZHomed":self.ZHomed,
			"E":self.E,
			"EOffset":self.EOffset,
			"IsRelative":self.IsRelative,
			"IsExtruderRelative":self.IsExtruderRelative,
			"LastExtrusionHeight":self.LastExtrusionHeight,
			"IsLayerChange":self.IsLayerChange,
			"IsZHop":self.IsZHop,
			"HasPositionError":self.HasPositionError,
			"PositionError":self.PositionError,
			"HasPositionChanged":self.HasPositionChanged,
			"HasStateChanged":self.HasStateChanged,
			"IsLayerChange":self.IsLayerChange,
			"Layer":self.Layer,
			"Height":self.Height
		}
	def UpdatePosition(self, x=None,y=None,z=None,e=None,f=None,force=False):
		if(f is not None):
			self.F = float(f)
		if(force):
			# Force the coordinates in as long as they are provided.
			#
			if(x is not None):
				x = float(x)
				x = x+self.XOffset				
				self.X = x 
			if(y is not None):
				y = float(y)
				y = y+self.YOffset
				self.Y = y
			if(z is not None):
				z = float(z)
				z = z + self.ZOffset
				self.Z = z
				
			if(e is not None):
				e = float(e)
				e = e + self.EOffset
				self.E = e
				
		else:
			

			# Update the previous positions if values were supplied
			if(x is not None and self.XHomed):
				x = float(x)
				if(self.IsRelative):
					if(self.X is not None):
						self.X += x
				else:
					self.X = x + self.XOffset

			if(y is not None and self.YHomed):
				y = float(y)
				if(self.IsRelative):
					if(self.Y is not None):
						self.Y += y
				else:
					self.Y = y + self.YOffset

			if(z is not None and self.ZHomed):
				
				z = float(z)
				if(self.IsRelative):
					if(self.Z is not None):
						self.Z += z
				else:
					self.Z = z + self.ZOffset
		
			if(e is not None):
				
				e = float(e)
				if(self.IsExtruderRelative):
					if(self.E is not None):
						self.EPrevious = self.E
						self.E += e
				else:
					self.EPrevious = self.E
					self.E = e + self.EOffset

			if(not utility.IsInBounds(self.X, self.Y, self.Z, self.OctoprintPrinterProfile)):
				self.HasPositionError = True
				self.PositionError = "Position - Coordinates {0} are out of the printer area!  Cannot resume position tracking until the axis is homed, or until absolute coordinates are received.".format(GetFormattedCoordinates(self.X,self.Y,self.Z,self.E))
			else:
				self.HasPositionError = False
				self.PositionError = None	

class Position(object):

	def __init__(self,octolapseSettings, octoprintPrinterProfile, g90InfluencesExtruder):
		self.Settings = octolapseSettings
		self.Printer = self.Settings.CurrentPrinter()
		self.OctoprintPrinterProfile = octoprintPrinterProfile
		self.PrinterTolerance = self.Printer.printer_position_confirmation_tolerance
		self.Positions = []
		self.Reset()
		
		self.Extruder = Extruder(octolapseSettings)
		self.G90InfluencesExtruder = g90InfluencesExtruder

		if(self.Printer.z_hop is None):
			self.Printer.z_hop = 0
		
		self.Commands = Commands()
	
	def Reset(self):

		self.Positions = []
		
		self.SavedPosition = None

	
	def UpdatePosition(self,x=None,y=None,z=None,e=None,f=None,force=False):
		if(len(self.Positions)==0):
			return
		pos = self.Positions[0]
		pos.UpdatePosition(x,y,z,e,f,force)
	def SavePosition(self,x=None,y=None,z=None,e=None,f=None,force=False):
		if(len(self.Positions)==0):
			return
		self.SavedPosition = Pos(self.Positions[0])
	def ToDict(self):
		positionDict = None
		if(len(self.Positions)>0):
			previousPos = self.Positions[0]
			return previousPos.ToDict()
		return None
	def ToPositionDict(self):
		positionDict = None
		if(len(self.Positions)>0):
			previousPos = self.Positions[0]
			return previousPos.ToPositionDict()
		return None
	def ToStateDict(self):
		positionDict = None
		if(len(self.Positions)>0):
			previousPos = self.Positions[0]
			return previousPos.ToStateDict()
		return None
	def ZDelta(self,pos):
		if(len(self.Positions)>0):
			previousPos = self.Positions[0]
			# calculate ZDelta
			if(pos.Height is not None):
				if(previousPos.Height is None):
					return pos.Height
				else:
					return pos.Height - previousPos.Height
		return 0
	def HasStateChanged(self, index=0):
		if(len(self.Positions)>index):
			return self.Positions[index].HasStateChanged
		return None
	def HasPositionChanged(self, index=0):
		if(len(self.Positions)>index):
			return self.Positions[index].HasPositionChanged
		return None
	def HasPositionError(self, index=0):
		if(len(self.Positions)>index):
			return self.Positions[index].HasPositionError
		return None
	def X(self, index=0):
		if(len(self.Positions)>index):
			return self.Positions[index].X
		return None
	def DistanceToZLift(self, index=0):
		if(len(self.Positions)>index):
			pos = self.Positions[index]
			currentLift = utility.round_to(pos.Z - pos.Height,self.PrinterTolerance)
			if(currentLift < self.Printer.z_hop):
				return self.Printer.z_hop - currentLift
			return 0
		return None
	def Y(self, index=0):
		if(len(self.Positions)>index):
			return self.Positions[index].Y
		return None
	def Z(self, index=0):
		if(len(self.Positions)>index):
			return self.Positions[index].Z
		return None
	def E(self, index=0):
		if(len(self.Positions)>index):
			return self.Positions[index].E
		return None
	def F(self, index=0):
		if(len(self.Positions)>index):
			return self.Positions[index].F
		return None
	def IsZHop(self, index=0):
		if(len(self.Positions)>index):
			return self.Positions[index].IsZHop
		return None
	def IsLayerChange(self, index=0):
		if(len(self.Positions)>index):
			return self.Positions[index].IsLayerChange
		return None
	def Layer(self, index=0):
		if(len(self.Positions)>index):
			return self.Positions[index].Layer
		return None
	def Height(self, index=0):
		if(len(self.Positions)>index):
			return self.Positions[index].Height
		return None
	def IsRelative(self, index=0):
		if(len(self.Positions)>index):
			return self.Positions[index].IsRelative
		return None
	def IsExtruderRelative(self, index=0):
		if(len(self.Positions)>index):
			return self.Positions[index].IsExtruderRelative
		return None
	def UndoUpdate(self):
		if(len(self.Positions)>0):
			del self.Positions[0]
		self.Extruder.UndoUpdate()
	def Update(self,gcode):
		command = self.Commands.GetCommand(gcode)
		# a new position

		pos = None
		previousPos = None
		numPositions = len(self.Positions)
		if(numPositions>0):
			pos = Pos(self.OctoprintPrinterProfile,self.Positions[0])
			if(numPositions>1):
				previousPos = Pos(self.OctoprintPrinterProfile,self.Positions[1])
		if(pos is None):
			pos = Pos( self.OctoprintPrinterProfile)
		if(previousPos is None):
			previousPos = Pos(  self.OctoprintPrinterProfile)

		# reset the current position state (copied from the previous position, or a new position)
		pos.ResetState()
		# set the pos gcode command
		pos.GCode = gcode

		# apply the command to the position tracker
		if(command is not None):
			if(command.Command in ["G0","G1"]):
				#Movement
				if(command.Parse()):
					self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received {0}".format(command.Name))
					x = command.Parameters["X"].Value
					y = command.Parameters["Y"].Value
					z = command.Parameters["Z"].Value
					e = command.Parameters["E"].Value
					f = command.Parameters["F"].Value

					if(x is not None or y is not None or z is not None or f is not None):
						
						if(pos.HasPositionError and not pos.IsRelative):
							pos.HasPositionError = False
							pos.PositionError = ""
						pos.UpdatePosition(x,y,z,e=None,f=f)
						
					if(e is not None):
						if(pos.IsExtruderRelative is not None):
							if(pos.HasPositionError and not pos.IsExtruderRelative):
								pos.HasPositionError = False
								pos.PositionError = ""
							pos.UpdatePosition(x=None,y=None,z=None,e=e, f=None)
						else:
							self.Settings.CurrentDebugProfile().LogError("Position - Unable to update the extruder position, no extruder coordinate system has been selected (absolute/relative).")
					message = "Position Change - {0} - {1} Move From(X:{2},Y:{3},Z:{4},E:{5}) - To(X:{6},Y:{7},Z:{8},E:{9})"
					if(previousPos is None):
						message = message.format(gcode,"Relative" if pos.IsRelative else "Absolute", "None", "None", "None", "None",pos.X, pos.Y, pos.Z, pos.E)
					else:
						message = message.format(gcode,"Relative" if pos.IsRelative else "Absolute", previousPos.X,previousPos.Y,previousPos.Z,previousPos.E,pos.X, pos.Y, pos.Z, pos.E)
					self.Settings.CurrentDebugProfile().LogPositionChange(message)

					
				else:
					self.Settings.CurrentDebugProfile().LogError("Position - Unable to parse the gcode command: {0}".format(gcode))
			elif(command.Command == "G28"):
				# Home
				if(command.Parse()):
					x = command.Parameters["X"].Value
					y = command.Parameters["Y"].Value
					z = command.Parameters["Z"].Value
					if(x is not None):
						pos.XHomed = True
					if(y is not None):
						pos.YHomed = True
					if(z is not None):
						pos.ZHomed = True
					if(x is None and y is None and z is None):
						pos.XHomed = True
						pos.YHomed = True
						pos.ZHomed = True

					self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received G28 - Homing to {0}".format(GetFormattedCoordinates(x,y,z,pos.E)))
					pos.HasPositionError = False
					pos.PositionError = None
				else:
					self.Settings.CurrentDebugProfile().LogError("Position - Unable to parse the Gcode:{0}".format(gcode))
			elif(command.Command == "G90"):
				# change x,y,z to absolute
				if(pos.IsRelative):
					self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received G90 - Switching to absolute x,y,z coordinates.")
					pos.IsRelative = False
				else:
					self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received G90 - Already using absolute x,y,z coordinates.")

				# for some firmwares we need to switch the extruder to absolute coordinates as well
				if (self.G90InfluencesExtruder):
					if(pos.IsExtruderRelative):
						self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received G90 - Switching to absolute extruder coordinates")
						pos.IsExtruderRelative = False
					else:
						self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received G90 - Already using absolute extruder coordinates")
			elif(command.Command == "G91"):
				# change x,y,z to relative
				if(not pos.IsRelative):
					self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received G91 - Switching to relative x,y,z coordinates")
					pos.IsRelative = True
				else:
					self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received G91 - Already using relative x,y,z coordinates")

				# for some firmwares we need to switch the extruder to absolute coordinates as well
				if (self.G90InfluencesExtruder):
					if(not pos.IsExtruderRelative):
						self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received G91 - Switching to relative extruder coordinates")
						pos.IsExtruderRelative = True
					else:
						self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received G91 - Already using relative extruder coordinates")
			elif(command.Command == "M83"):
				# Extruder - Set Relative
				if(pos.IsExtruderRelative is None or not pos.IsExtruderRelative):
					self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received M83 - Switching Extruder to Relative Coordinates")
					pos.IsExtruderRelative = True
			elif(command.Command == "M82"):
				# Extruder - Set Absolute
				if(pos.IsExtruderRelative is None or pos.IsExtruderRelative):
					self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received M82 - Switching Extruder to Absolute Coordinates")
					pos.IsExtruderRelative = False
			elif(command.Command == "G92"):
				# Set Position (offset)
				if(command.Parse()):
					previousRelativeValue = pos.IsRelative
					previousExtruderRelativeValue = pos.IsExtruderRelative
					x = command.Parameters["X"].Value
					y = command.Parameters["Y"].Value
					z = command.Parameters["Z"].Value
					e = command.Parameters["E"].Value
					resetAll = False
					if(x is None and y is None and z is None and e is None):
						pos.XOffset = pos.X
						pos.YOffset = pos.Y
						pos.ZOffset = pos.Z
						pos.EOffset = pos.E
					# set the offsets if they are provided
					if(x is not None and pos.X is not None and pos.XHomed):
						pos.XOffset = pos.X - utility.getfloat(x,0)
					if(y is not None and pos.Y is not None and pos.YHomed):
						pos.YOffset = pos.Y - utility.getfloat(y,0)
					if(z is not None and pos.Z is not None and pos.ZHomed):
						pos.ZOffset = pos.Z - utility.getfloat(z,0)
					if(e is not None and pos.E is not None):
						pos.EOffset = pos.E - utility.getfloat(e,0)
					self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received G92 - Set Position.  Command:{0}, XOffset:{1}, YOffset:{2}, ZOffset:{3}, EOffset:{4}".format(gcode, pos.XOffset,pos.YOffset,pos.ZOffset, pos.EOffset))
				else:
					self.Settings.CurrentDebugProfile().LogError("Position - Unable to parse the Gcode:{0}".format(gcode))

			########################################
			# Update the extruder monitor.
			self.Extruder.Update(self.ERelative(pos))
			########################################
			# If we have a homed axis, detect changes.
			########################################
			hasExtruderChanged = self.Extruder.HasChanged()
			pos.HasPositionChanged = not pos.IsPositionEqual(previousPos,self.PrinterTolerance)
			pos.HasStateChanged = not pos.IsStateEqual(previousPos,self.PrinterTolerance )

			if(self.HasHomedAxis()):
				
				if(hasExtruderChanged or pos.HasPositionChanged):
						
					# calculate LastExtrusionHeight and Height
					if (self.Extruder.IsExtruding()):
						pos.LastExtrusionHeight = pos.Z
						if(pos.Height is None or utility.round_to(pos.Z, self.PrinterTolerance) > previousPos.Height):
							pos.Height = utility.round_to(pos.Z, self.PrinterTolerance)
							self.Settings.CurrentDebugProfile().LogPositionHeightChange("Position - Reached New Height:{0}.".format(pos.Height))
					
						# calculate layer change
						if(utility.round_to(self.ZDelta(pos), self.PrinterTolerance) > 0
							or pos.Layer == 0):
							pos.IsLayerChange = True
							pos.Layer += 1
							self.Settings.CurrentDebugProfile().LogPositionLayerChange("Position - Layer:{0}.".format(pos.Layer))
						else:
							pos.IsLayerChange = False

					# Calculate ZHop based on last extrusion height
					if(pos.LastExtrusionHeight is not None):
						# calculate lift, taking into account floating point rounding
						lift = utility.round_to(pos.Z - pos.LastExtrusionHeight, self.PrinterTolerance)
						if(lift >= self.Printer.z_hop):
							lift = self.Printer.z_hop
						isLifted = self.Printer.z_hop > 0.0 and lift >= self.Printer.z_hop and (not self.Extruder.IsExtruding() or self.Extruder.IsExtrudingStart())

						if(isLifted):
							pos.IsZHop = True

					if(pos.IsZHop):
						self.Settings.CurrentDebugProfile().LogPositionZHop("Position - Zhop:{0}".format(self.Printer.z_hop))
					
		
		# Add the current position, remove positions if we have more than 5 from the end
		self.Positions.insert(0,pos)
		while (len(self.Positions)> 5):
			del self.Positions[5]
	
	def HasHomedAxis(self, index=0):
		if(len(self.Positions)<=index):
			return None
		
		pos = self.Positions[index]

		return (pos.XHomed
				and pos.YHomed
			    and pos.ZHomed
				and pos.X is not None
				and pos.Y is not None
				and pos.Z is not None)
	
	def XRelative(self):
		if(len(self.Positions)<2):
			return None
		pos = self.Positions[0]
		prevoiusPos = self.Positions[1]
		return pos.X-previousPos.X
	def YRelative(self):
		if(len(self.Positions)<2):
			return None
		pos = self.Positions[0]
		prevoiusPos = self.Positions[1]
		return pos.Y-previousPos.Y
	def ZRelative(self):
		if(len(self.Positions)<2):
			return None
		pos = self.Positions[0]
		prevoiusPos = self.Positions[1]
		return pos.Z-previousPos.Z
	def ERelative(self,pos):
		if(len(self.Positions)<1):
			return None
		previousPos = self.Positions[0]
		return pos.E-previousPos.E
	def IsAtPosition(self,x,y,z,pos,tolerance, applyOffset):
		if(applyOffset):
			x = x + pos.XOffset
			y = y + pos.YOffset
			if(z is not None):
				z = z + pos.ZOffset

		if( (pos.X is None or utility.isclose(pos.X , x,abs_tol=tolerance))
			and (pos.Y  is None or utility.isclose(pos.Y, y,abs_tol=tolerance))
			and (z is None or pos.Z is None or utility.isclose(pos.Z, z,abs_tol=tolerance))
			):
			return True
		return False
	def IsAtPreviousPosition(self, x,y,z=None, applyOffset = True):
		if(len(self.Positions)<2):
			return False
		return self.IsAtPosition( x,y,z,self.Positions[1],self.Printer.printer_position_confirmation_tolerance,True)

	def IsAtCurrentPosition(self, x,y,z=None, applyOffset = True):
		if(len(self.Positions)<1):
			return False
		return self.IsAtPosition( x,y,z,self.Positions[0],self.Printer.printer_position_confirmation_tolerance,True)

	def IsAtSavedPosition(self, x,y,z=None, applyOffset = True):
		if(self.SavedPosition is None):
			return False
		return self.IsAtPosition( x,y,z,self.SavedPosition,self.Printer.printer_position_confirmation_tolerance,True)
