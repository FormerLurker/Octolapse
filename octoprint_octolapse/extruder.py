import utility
class Extruder(object):
	"""The extruder monitor only works with relative extruder values"""
	def __init__(self,octoprintLogger):
		self.Logger = octoprintLogger
		self.ExtrusionLengthTotal = 0.0
		self.__ExtrusionLengthTotalPrevious = 0.0
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
		self.ExtrusionLengthTotal = 0.0
		self.__ExtrusionLengthTotalPrevious = 0.0
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
	def Update(self,position):
		e = position.ERelative()
		if(e is None or abs(e)< utility.FLOAT_MATH_EQUALITY_RANGE):
			e = 0.0
		

		self.__E =e
		# Record the previous values
		self.__ExtrusionLengthTotalPrevious = self.ExtrusionLengthTotal
		self.__RetractionLengthPrevious = self.RetractionLength 
		self.__IsExtrudingPrevious = self.IsExtruding
		
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
		self.IsExtruding = True if self.__RetractionLengthPrevious == 0 and self.__E > self.__RetractionLengthPrevious else False
		self.IsExtrudingStart = True if not self.__IsExtrudingPrevious and self.IsExtruding else False
		self.IsPrimed = True if self.__RetractionLengthPrevious - self.__E == 0 else False
		self.IsRetracted = True if self.__RetractionLengthPrevious > 0 and self.RetractionLength > 0 else False
		self.IsRetracting = True if self.__RetractionLengthPrevious == 0 and self.RetractionLength > 0 else False
		self.IsDetracting = True if self.__RetractionLengthPrevious>0 and self.RetractionLength - self.__E == 0 else False
		
	def IsTriggered(self, options):

		extrudingTriggered		= (options.OnExtruding and self.IsExtruding)
		extrudingStartTriggered	= (options.OnExtrudingStart and self.IsExtrudingStart)
		primedTriggered			= (options.OnPrimed and self.IsPrimed)
		retractingTriggered		= (options.OnRetracting and self.IsRetracting)
		retractedTriggered		= (options.OnRetracted and self.IsRetracted)
		detractedTriggered		= (options.OnDetracting and self.IsDetracting)
		isTriggered				= extrudingTriggered or extrudingStartTriggered or primedTriggered or retractingTriggered or retractedTriggered or detractedTriggered
		#self.Logger.info("Extruder - Trigger State - E:{0}, Retraction:{1} IsExtruding:{2}-{3}, IsExtrudingStart:{4}-{5}, IsPrimed:{6}-{7}, IsRetracting:{8}-{9}, IsRetracted:{10}-{11}, IsDetracting:{12}-{13}, IsTriggered:{14}"
		#	.format( self.__E
		#		, self.RetractionLength
		#		, self.IsExtruding
		#		, extrudingTriggered
		#		, self.IsExtrudingStart
		#		, extrudingStartTriggered
		#		, self.IsPrimed
		#		, primedTriggered
		#		, self.IsRetracting
		#		, retractingTriggered
		#		, self.IsRetracted
		#		, retractedTriggered
		#		, self.IsDetracting
		#		, detractedTriggered
		#		, isTriggered))
		return isTriggered



class ExtruderTriggers(object):
	def __init__(self,onExtruding,OnExtrudingStart,OnPrimed,OnRetracting,OnRetracted,OnDetracting):
		self.OnExtruding = onExtruding
		self.OnExtrudingStart = OnExtrudingStart
		self.OnPrimed = OnPrimed
		self.OnRetracting = OnRetracting
		self.OnRetracted = OnRetracted
		self.OnDetracting = OnDetracting

		
