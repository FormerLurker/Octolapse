class Extruder(object):
	"""The extruder monitor only works with relative extruder values"""
	def __init__(self):
		
		self.ExtrusionLengthTotal = 0.0,
		self.__ExtrusionLengthTotalPrevious = 0.0,
		self.Extruded = 0.0
		self.RetractionLength = 0.0
		self.__RetractionLengthPrevious = 0.0
		self.ExtrusionLength = 0.0
		self.IsExtrudingStart = False
		self.IsExtruding = False
		self.__IsExtrudingPrevious = False
		self.IsPrimed = False
		self.IsRetracting = False
		self.IsRetracted = False
		self.IsDetracting = False
		self.HasChanged = False
		self.__E = 0.0
		
	def Reset(self):
		self.ExtrusionLengthTotal = 0.0,
		self.__ExtrusionLengthTotalPrevious = 0.0,
		self.Extruded = 0.0
		self.RetractionLength = 0.0
		self.__RetractionLengthPrevious = 0.0
		self.ExtrusionLength = 0.0
		self.IsExtrudingStart = False
		self.IsExtruding = False
		self.__IsExtrudingPrevious = False
		self.IsPrimed = False
		self.IsRetracting = False
		self.IsRetracted = False
		self.IsDetracting = False
		self.HasChanged = False
		self.__E = 0.0

	# Update the extrusion monitor.  E (extruder delta) must be relative, not absolute!
	def Update(self,e):
		self.__E = e
		# Record the previous values
		self.__ExtrusionLengthTotalPrevious = self.ExtrusionLengthTotal
		self.__RetractionLengthPrevious = self.__RetractionLengthPrevious 
		self.__IsExtrudingPrevious = self.IsExtruding

		# Update ExtrusionTotal,RetractionLength and ExtrusionLength
		self.ExtrusionLengthTotal += __E;
		amountExtruded = self.__E + self.__RetractionLengthPrevious
		if(amountExtruded > 0):
			self.ExtrusionLength += amountExtruded
		else:
			self.RetractionLength += amountExtruded

		self.UpdateState()

	# If any values are edited manually (ExtrusionLengthTotal,ExtrusionLength, RetractionLength, __ExtrusionLengthTotalPrevious,__RetractionLengthPrevious,__IsExtrudingPrevious,
	# calling this will cause the state flags to recalculate
	def UpdateState(self):
		self.IsExtruding = True if self.__RetractionLengthPrevious == 0 and self.__E > self.__RetractionLengthPrevious else False
		self.IsExtrudingStart = True if not self.__IsExtrudingPrevious and self.IsExtruding else False
		self.IsPrimed = True if self.__RetractionLengthPrevious + self.__E == 0 else False
		self.IsRetracting = True if self.__RetractionLengthPrevious == 0 and self.RetractionLength < 0 else False
		self.IsRetracted = True if self.RetractionLength < 0 else False
		self.IsDetracting = True if (self.__RetractionLengthPrevious<0 and self.__e + self.__RetractionLengthPrevious == 0) else False
		
	def IsTriggered(self, options):
		if (options.OnExtruding and self.IsExtruding
			or options.OnExtrudingStart and self.IsExtrudingStart
			or options.OnPrimed and self.IsPriment
			or options.OnRetracting and self.IsRetracting
			or options.OnRetracted and self.IsRetracted
			or options.OnDetracting and self.IsDetracting):
			return True
		return False


class ExtruderTriggers(object):
	def __init__(self):
		self.OnExtruding = True
		self.OnExtrudingStart = True
		self.OnPrimed = False
		self.OnRetracting = False
		self.OnRetracted = True
		self.OnDetracting = True

		
