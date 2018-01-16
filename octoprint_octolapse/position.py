
# coding=utf-8
import re
from octoprint_octolapse.command import Commands, Command
from octoprint_octolapse.extruder import Extruder
from octoprint_octolapse.settings import *
import octoprint_octolapse.utility as utility
class Position(object):

	def __init__(self,octolapseSettings, octoprintPrinterProfile, g90InfluencesExtruder):
		self.Settings = octolapseSettings
		self.Printer = self.Settings.CurrentPrinter()
		self.OctoprintPrinterProfile = octoprintPrinterProfile

		self.Reset()
		
		self.Extruder = Extruder(octolapseSettings)
		self.G90InfluencesExtruder = g90InfluencesExtruder

		if(self.Printer.z_hop is None):
			self.Printer.z_hop = 0
		
		self.Commands = Commands()
	
	def Reset(self):

		self.F = None
		self.FPrevious = None
		self.X = None
		self.XOffset = 0
		self.XPrevious = None
		self.XHomedPrevious = False
		self.XHomed = False

		self.Y = None
		self.YOffset = 0
		self.YPrevious = None
		self.YHomedPrevious = False
		self.YHomed = False

		self.Z = None
		self.ZOffset = 0
		self.ZPrevious = None
		self.ZHomedPrevious = False
		self.ZHomed = False
		
		self.E = 0
		self.EOffset = 0
		self.EPrevious = 0

		self.HasPositionError = False
		self.PositionError = None
		self.IsRelative = False
		self.IsExtruderRelative = True
		
		# State Tracking Vars
		self.LastExtrusionHeight = None
		self.Height = None
		self.HeightPrevious = None
		self.ZDelta = None
		self.ZDeltaPrevious = None
		self.Layer = 0
		# State Flags
		self.IsLayerChange = False
		self.IsZHopStart = False
		self.IsZHop = False
		self.IsZHopCompleting = False

	def Update(self,gcode):
		command = self.Commands.GetCommand(gcode)
		
		# Movement detected, set the previous values
		# disect the gcode and use it to update our position
		# save any previous values that will be needed later
		self.XHomedPrevious = self.XHomed
		self.YHomedPrevious = self.YHomed
		self.ZHomedPrevious = self.ZHomed
		self.FPrevious = self.F
		if(self.IsZHopStart):
			self.IsZHop = True
		elif(self.IsZHopCompleting):
			self.IsZHop = False
			self.IsZHopCompleting = False
		self.HeightPrevious = self.Height
		self.ZDeltaPrevious = self.ZDelta

		# reset state variables
		self.IsLayerChange = False
		self.HasPositionChanged = False
		self.IsZHopStart = False

		# apply the command to the position tracker
		if(command is not None):
			if(command.Command in ["G0","G1"]):
				#Movement
				self.XPrevious = self.X
				self.YPrevious = self.Y
				self.ZPrevious = self.Z
				self.EPrevious = self.E
				if(command.Parse()):
					self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received {0}".format(command.Name))
					x = command.Parameters["X"].Value
					y = command.Parameters["Y"].Value
					z = command.Parameters["Z"].Value
					e = command.Parameters["E"].Value
					f = command.Parameters["F"].Value

					if(x is not None or y is not None or z is not None or f is not None):
						
						if(self.HasPositionError and not self.IsRelative):
							self.HasPositionError = False
							self.PositionError = ""
						self.UpdatePosition(x,y,z,e=None,f=f)
						
					if(e is not None):
						if(self.IsExtruderRelative is not None):
							if(self.HasPositionError and not self.IsExtruderRelative):
								self.HasPositionError = False
								self.PositionError = ""
							self.UpdatePosition(x=None,y=None,z=None,e=e, f=None)
						else:
							self.Settings.CurrentDebugProfile().LogError("Position - Unable to update the extruder position, no extruder coordinate system has been selected (absolute/relative).")
					message = "Position Change - {0} - {1} Move From(X:{2:s},Y:{3:s},Z:{4:s},E:{5:s}) - To(X:{6},Y:{7},Z:{8},E:{9})"
					message = message.format(command.Command,"Relative" if self.IsRelative else "Absolute", x,y,z,e,self.X, self.Y, self.Z, self.E)
					self.Settings.CurrentDebugProfile().LogPositionChange(message)
				else:
					self.Settings.CurrentDebugProfile().LogError("Position - Unable to parse the gcode command: {0}".format(gcode))
				#########################################################
				# Update the extruder monitor if there was movement
				self.Extruder.Update(self.ERelative())

				# If we've not reached z min, leave!
				if(not self.HasHomedAxis()):
					self.Settings.CurrentDebugProfile().LogPositionZminReached("Position - Axis not homed.")
				else:
					# calculate LastExtrusionHeight and Height
					if (self.Extruder.IsExtruding or self.Extruder.IsExtrudingStart):
						if(self.Height is None or self.Z > self.Height):
							self.Height = self.Z
						self.LastExtrusionHeight = self.Z

						self.Settings.CurrentDebugProfile().LogPositionHeightChange("Position - Reached New Height:{0}.".format(self.Height))

					# calculate ZDelta
					if(self.Height is not None):
						if(self.HeightPrevious is not None):
							self.ZDelta = self.Height - self.HeightPrevious
						else:
							self.ZDelta = self.Height

					# calculate layer change
					if(self.ZDelta is not None and (self.ZDelta > 0 or self.Layer == 0)):
						self.IsLayerChange = True
						self.Layer += 1
						self.Settings.CurrentDebugProfile().LogPositionLayerChange("Position - Layer:{0}.".format(self.Layer))
					else:
						self.IsLayerChange = False

					# Calculate ZHop based on last extrusion height
					if(self.LastExtrusionHeight is not None):
						# calculate lift, taking into account floating point rounding
						lift = self.Z - self.LastExtrusionHeight
						printerTolerance = self.Printer.printer_position_confirmation_tolerance
						if(utility.isclose(lift,self.Printer.z_hop,printerTolerance)):
							lift = self.Printer.z_hop
						isLifted = self.Printer.z_hop > 0.0 and lift >= self.Printer.z_hop and (not self.Extruder.IsExtruding or self.Extruder.IsExtrudingStart)

						if(isLifted):
							if(not self.IsZHop):
								self.IsZHopStart = True
						else:
							if(self.IsZHop):
								self.IsZHopCompleting = True

					if(self.IsZHopStart):
						self.Settings.CurrentDebugProfile().LogPositionZHop("Position - ZhopStart:{0}".format(self.Printer.z_hop))
					if(self.IsZHop):
						self.Settings.CurrentDebugProfile().LogPositionZHop("Position - Zhop:{0}".format(self.Printer.z_hop))
					if(self.IsZHopCompleting):
						self.Settings.CurrentDebugProfile().LogPositionZHop("Position - IsZHopCompleting:{0}".format(self.Printer.z_hop))
				#########################################################
			elif(command.Command == "G28"):
				# test homing of only X,Y or Z
				
				if(command.Parse()):
					x = command.Parameters["X"].Value
					y = command.Parameters["Y"].Value
					z = command.Parameters["Z"].Value
					if(x is not None):
						x = 0
						self.XHomed = True
					if(y is not None):
						y = 0
						self.YHomed = True
					if(z is not None):
						z = 0
						self.ZHomed = True
					if(x is None and y is None and z is None):
						x = 0
						y = 0
						z = 0
						self.XHomed = True
						self.YHomed = True
						self.ZHomed = True

					self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received G28 - Homing to {0}".format(self.GetFormattedCoordinates(x,y,z,self.E)))
					self.UpdatePosition(x=x,y=y,z=z,e=None,force = True)
					
					self.HasPositionError = False
					self.PositionError = None
				else:
					self.Settings.CurrentDebugProfile().LogError("Position - Unable to parse the Gcode:{0}".format(gcode))
			elif(command.Command == "G90"):
				# change x,y,z to absolute
				if(self.IsRelative):
					self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received G90 - Switching to absolute x,y,z coordinates.")
					self.IsRelative = False
				else:
					self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received G90 - Already using absolute x,y,z coordinates.")

				# for some firmwares we need to switch the extruder to absolute coordinates as well
				if (self.G90InfluencesExtruder):
					if(self.IsExtruderRelative):
						self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received G90 - Switching to absolute extruder coordinates")
						self.IsExtruderRelative = False
					else:
						self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received G90 - Already using absolute extruder coordinates")
			elif(command.Command == "G91"):
				# change x,y,z to relative
				if(not self.IsRelative):
					self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received G91 - Switching to relative x,y,z coordinates")
					self.IsRelative = True
				else:
					self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received G91 - Already using relative x,y,z coordinates")

				# for some firmwares we need to switch the extruder to absolute coordinates as well
				if (self.G90InfluencesExtruder):
					if(not self.IsExtruderRelative):
						self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received G91 - Switching to relative extruder coordinates")
						self.IsExtruderRelative = True
					else:
						self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received G91 - Already using relative extruder coordinates")
			elif(command.Command == "M83"):
				if(self.IsExtruderRelative is None or not self.IsExtruderRelative):
					self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received M83 - Switching Extruder to Relative Coordinates")
					self.IsExtruderRelative = True
			elif(command.Command == "M82"):
				
				if(self.IsExtruderRelative is None or self.IsExtruderRelative):
					self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received M82 - Switching Extruder to Absolute Coordinates")
					self.IsExtruderRelative = False
			elif(command.Command == "G92"):
				if(command.Parse()):
					previousRelativeValue = self.IsRelative
					previousExtruderRelativeValue = self.IsExtruderRelative
					x = command.Parameters["X"].Value
					y = command.Parameters["Y"].Value
					z = command.Parameters["Z"].Value
					e = command.Parameters["E"].Value
					resetAll = False
					if(x is None and y is None and z is None and e is None):
						self.XOffset = self.X
						self.YOffset = self.Y
						self.ZOffset = self.Z
						self.EOffset = self.E
					# set the offsets if they are provided
					if(x is not None and self.X is not None and self.XHomed):
						self.XOffset = self.X - utility.getfloat(x,0)
					if(y is not None and self.Y is not None and self.YHomed):
						self.YOffset = self.Y - utility.getfloat(y,0)
					if(z is not None and self.Z is not None and self.ZHomed):
						self.ZOffset = self.Z - utility.getfloat(z,0)
					if(e is not None and self.E is not None):
						self.EOffset = self.E - utility.getfloat(e,0)
					self.Settings.CurrentDebugProfile().LogPositionCommandReceived("Received G92 - Set Position.  Command:{0}, XOffset:{1}, YOffset:{2}, ZOffset:{3}, EOffset:{4}".format(gcode, self.XOffset,self.YOffset,self.ZOffset, self.EOffset))
				else:
					self.Settings.CurrentDebugProfile().LogError("Position - Unable to parse the Gcode:{0}".format(gcode))
			if(self.X != self.XPrevious
				or self.Y != self.YPrevious
				or self.Z != self.ZPrevious
				or self.ERelative() != 0
			):
				self.HasPositionChanged = True;

	def UpdatePosition(self,x=None,y=None,z=None,e=None,f=None,force=False):
		if(f is not None):
			self.F = float(f)
		if(force):
			# Force the coordinates in as long as they are provided.
			#
			if(x is not None):
				x = float(x)
				x = x+self.XOffset
				self.X = x 
				if(self.XPrevious is None):
					self.XPrevious = x
			if(y is not None):
				y = float(y)
				y = y+self.YOffset
				self.Y = y
				if(self.YPrevious is None):
					self.YPrevious = y
			if(z is not None):
				z = float(z)
				z = z + self.ZOffset
				self.Z = z
				if(self.ZPrevious is None):
					self.ZPrevious = z
			if(e is not None):
				e = float(e)
				e = e + self.EOffset
				self.E = e
				if(self.EPrevious is None):
					self.EPrevious = e
		else:
			

			# Update the previous positions if values were supplied
			if(x is not None and self.XHomed):
				x = float(x)
				if(self.IsRelative):
					if(self.X is None):
						self.X = 0
						self.XPrevious = 0

					self.X += x
				else:
					self.X = x + self.XOffset

			if(y is not None and self.YHomed):
				y = float(y)
				if(self.IsRelative):
					if(self.Y is None):
						self.Y = 0
						self.YPrevious = 0
					self.Y += y
				else:
					self.Y = y + self.YOffset

			if(z is not None and self.ZHomed):
				z = float(z)
				if(self.IsRelative):
					if(self.Z is None):
						self.Z = 0
						self.ZPrevious = 0
					self.Z += z
				else:
					self.Z = z + self.ZOffset
		
			if(e is not None):
				e = float(e)
				if(self.IsExtruderRelative):
					if(self.E is None):
						self.E = 0
						self.EPrevious = 0
					self.E += e
				else:
					self.E = e + self.EOffset

			if(not utility.IsInBounds(self.X, self.Y, self.Z, self.OctoprintPrinterProfile)):
				self.HasPositionError = True
				self.PositionError = "Position - Coordinates {0} are out of the printer area!  Cannot resume position tracking until the axis is homed, or until absolute coordinates are received.".format(self.GetFormattedCoordinates(self.X,self.Y,self.Z,self.E))
				self.Settings.CurrentDebugProfile().LogError(self.PositionError)
			else:
				self.HasPositionError = False
				self.PositionError = None
		


	def HasHomedAxis(self):
		return (self.XHomed
				and self.YHomed
			    and self.ZHomed)
	def HasHomedAxisPrevious(self):
		return (self.XHomedPrevious
				and self.YHomedPrevious
			    and self.ZHomedPrevious)

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

	def IsAtPreviousPosition(self, x,y,z=None, applyOffset = True):
		printerTolerance = self.Printer.printer_position_confirmation_tolerance
		if(applyOffset):
			x = x + self.XOffset
			y = y + self.YOffset
			if(z is not None):
				z = z + self.ZOffset

		if( (self.XPrevious is None or utility.isclose(self.XPrevious, x,abs_tol=printerTolerance))
			and (self.YPrevious is None or utility.isclose(self.YPrevious, y,abs_tol=printerTolerance))
			and (z is None or self.ZPrevious is None or utility.isclose(self.ZPrevious, z,abs_tol=printerTolerance))
			):
			return True
		return False
	def IsAtCurrentPosition(self, x,y,z=None, applyOffset = True):
		printerTolerance = self.Printer.printer_position_confirmation_tolerance
		if(applyOffset):
			x = x + self.XOffset
			y = y + self.YOffset
			if(z is not None):
				z = z + self.ZOffset
				 
		if( (self.X is None or utility.isclose(self.X, x,abs_tol=printerTolerance))
			and (self.Y is None or utility.isclose(self.Y, y,abs_tol=printerTolerance))
			and (self.Z is None or z is None or utility.isclose(self.Z, z,abs_tol=printerTolerance))
			):
			return True
		return False
	
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

