class GCode(object):
	CurrentXPathIndex = 0
	CurrentYPathIndex = 0
	def __init__(self):
		self.CurrentXPathIndex = 0
		self.CurrentYPathIndex = 0

	def GetBedRelativeX(self,percent,printer,profile,printer_profile):
		if(printer_profile["volume"]["custom_box"] != False):
			return self.GetRelativeCoordinate(percent,printer_profile["volume"]["custom_box"]["x_min"],printer_profile["volume"]["custom_box"]["x_max"])
		else:
			return self.GetRelativeCoordinate(percent,0,printer_profile["volume"].width)

	def GetBedRelativeY(self,percent,printer,profile,printer_profile):
		if(printer_profile["volume"]["custom_box"] != False):
			return self.GetRelativeCoordinate(percent,printer_profile["volume"]["custom_box"]["y_min"],printer_profile["volume"]["custom_box"]["y_max"])
		else:
			return self.GetRelativeCoordinate(percent,0,printer_profile["volume"].depth)

	def GetBedRelativeZ(self,percent,printer,profile,printer_profile):
		if(printer_profile["volume"]["custom_box"] != False):
			return self.GetRelativeCoordinate(percent,printer_profile["volume"]["custom_box"]["z_min"],printer_profile["volume"]["custom_box"]["x_max"])
		else:
			return self.GetRelativeCoordinate(percent,0,printer_profile["volume"].height)

	def GetRelativeCoordinate(self,percent,min,max):
		return ((max-min)*(percent/100.0))+min

	def CheckX(self,x,printer_profile):
		hasError = False
		if(printer_profile["volume"]["custom_box"] == True and (x<printer_profile["volume"]["custom_box"]["x_min"] or x > printer_profile.printer_profile["volume"]["custom_box"]["x_max"])):
			hasError = True
		elif(x<0 or x > printer_profile["volume"]["width"]):
			hasError = True
		if(hasError):
			
			raise ValueError('The X coordinate {0} was outside the bounds of the printer!'.format(x))

	def CheckY(self,y,printer_profile):
		hasError = False
		if(printer_profile["volume"]["custom_box"] == True and (y<printer_profile["volume"]["custom_box"]["y_min"] or y > printer_profile["volume"]["custom_box"]["y_max"])):
			hasError = True
		elif(y<0 or y > printer_profile["volume"]["depth"]):
			hasError = True
		if(hasError):
			raise ValueError('The Y coordinate $s was outside the bounds of the printer!'% (y))

	def CheckZ(self,z,printer_profile):
		hasError = False
		if(printer_profile["volume"]["custom_box"] == True and (z < printer_profile["volume"]["custom_box"]["z_min"] or z > printer_profile["volume"]["custom_box"]["z_max"])):
			hasError = True
		elif(z<0 or z > printer_profile["volume"]["height"]):
			hasError = True
		if(hasError):
			raise ValueError('The Z coordinate $s was outside the bounds of the printer!'% (z))
	
	def GetXCoordinateForSnapshot(self, printer, profile,printer_profile):
		xCoord = 0
		if (profile.stabilization.x_type == "fixed_coordinate"):
			xCoord = profile.stabilization.x_fixed_coordinate
		elif (profile.stabilization.x_type == "relative"):
			if(printer_profile["volume"]["formFactor"] == "circle"):
				raise ValueError('Cannot calculate relative coordinates within a circular bed (yet...), sorry')
			xCoord = self.GetBedRelativeX(profile.stabilization.x_relative,printer,profile,printer_profile)
		elif (profile.stabilization.x_type == "fixed_path"):
			# if there are no paths return the fixed coordinate
			if(len(profile.stabilization.x_fixed_path) == 0):
				xCoord = profile.stabilization.x_fixed_coordinate
			# if we have reached the end of the path
			elif(self.CurrentXPathIndex >= len(profile.stabilization.x_fixed_path)):
				#If we are looping through the paths, reset the index to 0
				if(profile.stabilization.x_fixed_path_loop):
						self.CurrentXPathIndex = 0
				else:
					self.CurrentXPathIndex = len(profile.stabilization.x_fixed_path)
			xCoord = profile.stabilization.x_fixed_path[self.CurrentXPathIndex]
			self.CurrentXPathIndex += 1
		elif (profile.stabilization.x_type == "relative_path"):
			if(printer_profile["volume"]["formFactor"] == "circle"):
				raise ValueError('Cannot calculate relative coordinates within a circular bed (yet...), sorry')
			# if there are no paths return the fixed coordinate
			if(len(profile.stabilization.x_relative_path) == 0):
				xCoord = self.GetBedRelativeX(profile.stabilization.x_relative,printer,profile,printer_profile)
			# if we have reached the end of the path
			elif(self.CurrentXPathIndex >= len(profile.stabilization.x_relative_path)):
				#If we are looping through the paths, reset the index to 0
				if(profile.stabilization.x_relative_path_loop):
						self.CurrentXPathIndex = 0
				else:
					self.CurrentXPathIndex = len(profile.stabilization.x_relative_path)
			xRel = profile.stabilization.x_relative_path[self.CurrentXPathIndex]
			self.CurrentXPathIndex += 1
			xCoord = self.GetBedRelativeX(xRel,printer,profile,printer_profile)
		else:
			raise NotImplementedError
		self.CheckX(xCoord,printer_profile)
		return xCoord
		
	def GetYCoordinateForSnapshot(self, printer, profile,printer_profile):
		yCoord = 0
		if (profile.stabilization.y_type == "fixed_coordinate"):
			yCoord = profile.stabilization.y_fixed_coordinate
		elif (profile.stabilization.y_type == "relative"):
			if(printer_profile["volume"]["formFactor"] == "circle"):
				raise ValueError('Cannot calculate relative coordinates within a circular bed (yet...), sorry')
			yCoord = self.GetBedRelativeY(profile.stabilization.y_relative,printer,profile,printer_profile)
		elif (profile.stabilization.y_type == "fixed_path"):
			# if there are no paths return the fixed coordinate
			if(len(profile.stabilization.y_fixed_path) == 0):
				yCoord = profile.stabilization.y_fixed_coordinate
			# if we have reached the end of the path
			elif(self.CurrentYPathIndex >= len(profile.stabilization.y_fixed_path)):
				#If we are looping through the paths, reset the index to 0
				if(profile.stabilization.y_fixed_path_loop):
						self.CurrentYPathIndex = 0
				else:
					self.CurrentYPathIndex = len(profile.stabilization.y_fixed_path)
			yCoord = profile.stabilization.y_fixed_path[self.CurrentYPathIndex]
			self.CurrentYPathIndex += 1
		elif (profile.stabilization.y_type == "relative_path"):
			if(printer_profile["volume"]["formFactor"] == "circle"):
				raise ValueError('Cannot calculate relative coordinates within a circular bed (yet...), sorry')
			# if there are no paths return the fixed coordinate
			if(len(profile.stabilization.y_relative_path) == 0):
				yCoord =  self.GetBedRelativeY(profile.stabilization.y_relative,printer,profile,printer_profile)
			# if we have reached the end of the path
			elif(self.CurrentYPathIndex >= len(profile.stabilization.y_relative_path)):
				#If we are looping through the paths, reset the index to 0
				if(profile.stabilization.y_relative_path_loop):
						self.CurrentYPathIndex = 0
				else:
					self.CurrentYPathIndex = len(profile.stabilization.y_relative_path)
			yRel = profile.stabilization.y_relative_path[self.CurrentYPathIndex]
			self.CurrentYPathIndex += 1
			yCoord =  self.GetBedRelativeY(yRel,printer,profile,printer_profile)
		else:
			raise NotImplementedError
		self.CheckY(yCoord,printer_profile)
		return yCoord


	def GetSnapshotGcodeArray(self,printer,profile,printerProfile):

		gcode = []
		if(profile.snapshot.retract_before_move):
			gcode.append(GetRetractGCode(printer))

		for cmd in printer.snapshot_gcode:
			if(cmd.lstrip().startswith(printer.snapshot_command)):
				return "; The snapshot gcode cannot contain the snapshot command!";
			gcode.append(cmd.format(self.GetXCoordinateForSnapshot(printer,profile,printerProfile),
					   self.GetYCoordinateForSnapshot(printer,profile,printerProfile),
					   printer.movement_speed,
					   profile.snapshot.delay))

		if(profile.snapshot.retract_before_move):
			gcode.append(GetDetractGcode(printer))
		
		return gcode
	#
	def GetRetractGcode(self, printer):
		return "G1 E{0:f} F{1:f}".format(printer.retract_length,printer.retract_speed)
	#
	def GetDetractGcode(self, printer):
		return "G1 E{0:f} F{1:f}".format(-1* printer.retract_length,printer.retract_speed)


