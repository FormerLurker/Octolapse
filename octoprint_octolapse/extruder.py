from octoprint_octolapse.settings import *
import octoprint_octolapse.utility as utility

class Extruder(object):
	"""The extruder monitor only works with relative extruder values"""
	def __init__(self,octolapseSettings):
		self.Settings = octolapseSettings
		self.PrinterRetractionLength = self.Settings.CurrentPrinter().retract_length
		self.Reset()
		
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
		self.IsPrimed = True
		self.__IsPrimedPrevious = True
		self.IsRetractingStart = False
		self.__IsRetractingStartPrevious = False
		self.IsRetracting = False
		self.__IsRetractingPrevious = False
		self.IsRetracted = False
		self.__IsRetractedPrevious = False
		self.IsPartiallyRetracted = False
		self.__IsPartiallyRetractedPrevious = False
		self.IsDetractingStart = False
		self.__IsDetractingStartPrevious = False
		self.IsDetracting = False
		self.__IsDetractingPrevious = False
		self.IsDetracted = False
		self.__IsDetractedPrevious = False
		self.HasChanged = False
		self.__E = 0.0

	# Update the extrusion monitor.  E (extruder delta) must be relative, not absolute!
	def Update(self,eRelative):
		e = float(eRelative)
		if(e is None or abs(e)< utility.FLOAT_MATH_EQUALITY_RANGE):
			e = 0.0
		
		self.__E =e
		# Record the previous values
		self.__ExtrusionLengthTotalPrevious = self.ExtrusionLengthTotal
		self.__RetractionLengthPrevious = self.RetractionLength 
		self.__IsExtrudingStartPrevious = self.IsExtrudingStart
		self.__IsExtrudingPrevious = self.IsExtruding
		self.__IsPrimedPrevious = self.IsPrimed
		self.__IsRetractingStartPrevious = self.IsRetractingStart
		self.__IsRetractingPrevious = self.IsRetracting
		self.__IsPartiallyRetractedPrevious = self.IsPartiallyRetracted
		self.__IsRetractedPrevious = self.IsRetracted
		self.__IsDetractingStartPrevious = self.IsDetractingStart
		self.__IsDetractingPrevious = self.IsDetracting
		self.__IsDetractedPrevious = self.IsDetracted


		# Update ExtrusionTotal,RetractionLength and ExtrusionLength
		
		self.ExtrusionLengthTotal += self.__E
		self.RetractionLength -= self.__E
		
		if(self.RetractionLength <= utility.FLOAT_MATH_EQUALITY_RANGE):
			self.RetractionLength = 0
		
		self.UpdateState()
		
	# If any values are edited manually (ExtrusionLengthTotal,ExtrusionLength, RetractionLength, __ExtrusionLengthTotalPrevious,__RetractionLengthPrevious,__IsExtrudingPrevious,
	# calling this will cause the state flags to recalculate
	def UpdateState(self):
		# Todo:  Properly deal with floating compare
		self.HasChanged = False
		self.IsExtrudingStart = True if self.__E > self.__RetractionLengthPrevious and not self.__IsExtrudingPrevious else False
		self.IsExtruding = True if self.__E > self.__RetractionLengthPrevious else False
		self.IsPrimed = True if self.RetractionLength == 0 and self.__E - self.__RetractionLengthPrevious == 0 else False
		self.IsRetractingStart = True if self.__RetractionLengthPrevious == 0 and self.RetractionLength > 0 else False
		self.IsRetracting = True if self.RetractionLength > 0 and self.__E < 0 else False
		self.IsPartiallyRetracted = True if self.RetractionLength > 0 and self.RetractionLength < self.PrinterRetractionLength else False
		self.IsRetracted = True if self.RetractionLength >= self.PrinterRetractionLength else False
		self.IsDetractingStart = True if self.__RetractionLengthPrevious > self.RetractionLength and not self.__IsDetractingPrevious else False
		self.IsDetracting = True if self.__RetractionLengthPrevious > self.RetractionLength else False
		self.IsDetracted = True if self.RetractionLength == 0 and self.__RetractionLengthPrevious > 0 else False

		if(
			self.__RetractionLengthPrevious != self.RetractionLength 
			or self.__IsExtrudingStartPrevious != self.IsExtrudingStart
			or self.__IsExtrudingPrevious != self.IsExtruding
			or self.__IsPrimedPrevious != self.IsPrimed
			or self.__IsRetractingStartPrevious != self.IsRetractingStart
			or self.__IsRetractingPrevious != self.IsRetracting
			or self.__IsPartiallyRetractedPrevious != self.IsPartiallyRetracted
			or self.__IsRetractedPrevious != self.IsRetracted
			or self.__IsDetractingStartPrevious != self.IsDetractingStart
			or self.__IsDetractingPrevious != self.IsDetracting
			or self.__IsDetractedPrevious != self.IsDetracted
		):
			self.HasChanged = True

		if(self.HasChanged):
			self.Settings.CurrentDebugProfile().LogExtruderChange("Extruder Changed: E:{0}, Retraction:{1} IsExtruding:{2}-{3}, IsExtrudingStart:{4}-{5}, IsPrimed:{6}-{7}, IsRetractingStart:{8}-{9}, IsRetracting:{10}-{11}, IsPartiallyRetracted:{12}-{13}, IsRetracted:{14}-{15}, IsDetractingStart:{16}-{17}, IsDetracting:{18}-{19}, IsDetracted:{20}-{21}"
			.format( self.__E
				, self.RetractionLength
				, self.__IsExtrudingPrevious
				, self.IsExtruding
				, self.__IsExtrudingStartPrevious
				, self.IsExtrudingStart
				, self.__IsPrimedPrevious
				, self.IsPrimed
				, self.__IsRetractingStartPrevious
				, self.IsRetractingStart
				, self.__IsRetractingPrevious
				, self.IsRetracting
				, self.__IsPartiallyRetractedPrevious 
				, self.IsPartiallyRetracted
				, self.__IsRetractedPrevious 
				, self.IsRetracted
				, self.__IsDetractingStartPrevious
				, self.IsDetractingStart
				, self.__IsDetractingPrevious
				, self.IsDetracting
				, self.__IsDetractedPrevious
				, self.IsDetracted))


	def ExtruderStateTriggered(self, option, state):
		if(option is None):
			return None
		if(option and state):
			return True
		if(not option and state):
			return False
		return None

	def IsTriggered(self, options):
		"""Matches the supplied extruder trigger options to the current extruder state.  Returns true if triggering, false if not."""
		extrudingStartTriggered		= self.ExtruderStateTriggered(options.OnExtrudingStart ,self.IsExtrudingStart)
		extrudingTriggered			= self.ExtruderStateTriggered(options.OnExtruding, self.IsExtruding)
		primedTriggered				= self.ExtruderStateTriggered(options.OnPrimed, self.IsPrimed)
		retractingStartTriggered	= self.ExtruderStateTriggered(options.OnRetractingStart, self.IsRetractingStart)
		retractingTriggered			= self.ExtruderStateTriggered(options.OnRetracting, self.IsRetracting)
		partiallyRetractedTriggered	= self.ExtruderStateTriggered(options.OnPartiallyRetracted, self.IsPartiallyRetracted)
		retractedTriggered			= self.ExtruderStateTriggered(options.OnRetracted, self.IsRetracted)
		detractingStartTriggered	= self.ExtruderStateTriggered(options.OnDetractingStart, self.IsDetractingStart)
		detractingTriggered			= self.ExtruderStateTriggered(options.OnDetracting, self.IsDetracting)
		detractedTriggered			= self.ExtruderStateTriggered(options.OnDetracted, self.IsDetracted)

		isTriggered = False
		isTriggeringPrevented = (
			   (extrudingStartTriggered is not None and not extrudingStartTriggered)
			or (extrudingTriggered is not None and not extrudingTriggered)
			or (primedTriggered is not None and not primedTriggered)
			or (retractingStartTriggered is not None and not retractingStartTriggered)
			or (retractingTriggered is not None and not retractingTriggered)
			or (partiallyRetractedTriggered is not None and not partiallyRetractedTriggered)
			or (retractedTriggered is not None and not retractedTriggered)
			or (detractingStartTriggered is not None and not detractingStartTriggered)
			or (detractingTriggered is not None and not detractingTriggered)
			or (detractedTriggered is not None and not detractedTriggered))

		if(not isTriggeringPrevented
			and
			(
				(extrudingStartTriggered is not None and extrudingStartTriggered)
				or (extrudingTriggered is not None and extrudingTriggered)
				or(primedTriggered is not None and primedTriggered)
				or(retractingStartTriggered is not None and retractingStartTriggered)
				or(retractingTriggered is not None and retractingTriggered)
				or(partiallyRetractedTriggered is not None and partiallyRetractedTriggered)
				or(retractedTriggered is not None and retractedTriggered)
				or(detractingStartTriggered is not None and detractingStartTriggered)
				or(detractingTriggered is not None and detractingTriggered)
				or(detractedTriggered is not None and detractedTriggered)
				or(options.AreAllTriggersIgnored()))):
			isTriggered = True

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
	def __init__(self, OnExtrudingStart, onExtruding, OnPrimed, OnRetractingStart, OnRetracting, OnPartiallyRetracted, OnRetracted, OnDetractingStart, OnDetracting, OnDetracted):
		"""To trigger on an extruder state, set to True.  To prevent triggering on an extruder state, set to False.  To ignore the extruder state, set to None"""
		self.OnExtrudingStart = OnExtrudingStart
		self.OnExtruding = onExtruding
		self.OnPrimed = OnPrimed
		self.OnRetractingStart = OnRetractingStart
		self.OnRetracting = OnRetracting
		self.OnPartiallyRetracted = OnPartiallyRetracted
		self.OnRetracted = OnRetracted
		self.OnDetractingStart = OnDetractingStart
		self.OnDetracting = OnDetracting
		self.OnDetracted = OnDetracted

	def AreAllTriggersIgnored(self):
		if(self.OnExtrudingStart is None
		and self.OnExtruding is None
		and self.OnPrimed is None
		and self.OnRetractingStart is None
		and self.OnRetracting is None
		and self.OnPartiallyRetracted is None
		and self.OnRetracted is None
		and self.OnDetractingStart is None
		and self.OnDetracting is None
		and self.OnDetracted  is None):
			return True
		return False

