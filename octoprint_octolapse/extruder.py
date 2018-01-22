from octoprint_octolapse.settings import *
import octoprint_octolapse.utility as utility

class ExtruderState(object):
	def __init__(self, state = None):
		self.E = 0 if state is None else state.E
		self.ExtrusionLength = 0.0 if state is None else state.ExtrusionLength
		self.ExtrusionLengthTotal = 0.0 if state is None else state.ExtrusionLengthTotal
		self.RetractionLength = 0.0 if state is None else state.RetractionLength
		self.DetractionLength = 0.0 if state is None else state.DetractionLength
		self.ExtrusionLength = 0.0 if state is None else state.ExtrusionLength
		self.IsExtrudingStart = False if state is None else state.IsExtrudingStart
		self.IsExtruding = False if state is None else state.IsExtruding
		self.IsPrimed = False if state is None else state.IsPrimed
		self.IsRetractingStart = False if state is None else state.IsRetractingStart
		self.IsRetracting = False if state is None else state.IsRetracting
		self.IsRetracted = False if state is None else state.IsRetracted
		self.IsPartiallyRetracted = False if state is None else state.IsPartiallyRetracted
		self.IsDetractingStart = False if state is None else state.IsDetractingStart
		self.IsDetracting = False if state is None else state.IsDetracting
		self.IsDetracted = False if state is None else state.IsDetracted
		self.HasChanged = False if state is None else state.HasChanged
		
class Extruder(object):
	"""The extruder monitor only works with relative extruder values"""
	def __init__(self,octolapseSettings):
		self.Settings = octolapseSettings
		self.PrinterRetractionLength = self.Settings.CurrentPrinter().retract_length
		
		self.Reset()
		
	def Reset(self):
		self.StateHistory = []
		self.HasChanged = False

	def IsExtruding(self):
		if(len(self.StateHistory)>0):
			return self.StateHistory[0].IsExtruding
		return False

	def IsExtrudingStart(self):
		if(len(self.StateHistory)>0):
			return self.StateHistory[0].IsExtrudingStart
		return False

	def IsRetracted(self):
		if(len(self.StateHistory)>0):
			return self.StateHistory[0].IsRetracted
		return False

	def UndoUpdate(self):
		if(len(self.StateHistory)>0):
			del self.StateHistory[0]
	# Update the extrusion monitor.  E (extruder delta) must be relative, not absolute!
	def Update(self,eRelative):
		if(eRelative is None):
			return

		e = float(eRelative)
		if(e is None or abs(e)< utility.FLOAT_MATH_EQUALITY_RANGE):
			e = 0.0

		state = None
		previousState = None
		numStates = len(self.StateHistory)>0
		if(numStates>0):
			state = ExtruderState(self.StateHistory[0])
			if(numStates > 1):
				previousState = self.StateHistory[0]

		if(state is None):
			state = ExtruderState()
		if(previousState is None):
			previousState = ExtruderState()

		state.E =e
		# Update ExtrusionTotal,RetractionLength and ExtrusionLength
		
		state.ExtrusionLengthTotal += e
		state.RetractionLength -= e

		if(state.RetractionLength <= utility.FLOAT_MATH_EQUALITY_RANGE):
			# we can use the negative retraction length to calculate our extrusion length!
			state.ExtrusionLength = abs(state.RetractionLength)
			# set the retraction length to 0 since we are etruding
			state.RetractionLength = 0
		else:
			state.ExtrusionLength = 0

		# calculate detraction length
		if(previousState.RetractionLength > state.RetractionLength):
			state.DetractionLength = previousState.RetractionLength - state.RetractionLength
		else:
			state.DetractionLength = 0
		# round our lengths to the nearest .05mm to avoid some floating point math errors

		
		self.UpdateState(state,previousState)
		# Add the current position, remove positions if we have more than 5 from the end
		self.StateHistory.insert(0,state)
		while (len(self.StateHistory)> 5):
			del self.StateHistory[5]

	# If any values are edited manually (ExtrusionLengthTotal,ExtrusionLength, RetractionLength, __ExtrusionLengthTotalPrevious,__RetractionLengthPrevious,__IsExtrudingPrevious,
	# calling this will cause the state flags to recalculate
	def UpdateState(self,pos,previousPos):
		# Todo:  Properly deal with floating compare
		self.HasChanged = False
		# If we were not previously extruding, but are now
		#utility.round_to(pos.ExtrusionLength,0.0001) 

		pos.IsExtrudingStart = True if utility.round_to(pos.ExtrusionLength,0.0001) > 0 and utility.round_to(previousPos.ExtrusionLength,0.0001) == 0 else False
		pos.IsExtruding = True if (utility.round_to(previousPos.ExtrusionLength,0.0001) > 0) and utility.round_to(pos.ExtrusionLength,0.0001) > 0 else False
		pos.IsPrimed = True if utility.round_to(previousPos.RetractionLength,0.0001) == 0 and utility.round_to(pos.ExtrusionLength,0.0001) == 0 and utility.round_to(pos.RetractionLength,0.0001) == 0else False
		pos.IsRetractingStart = True if utility.round_to(previousPos.RetractionLength,0.0001) == 0 and utility.round_to(pos.RetractionLength,0.0001) > 0 else False
		pos.IsRetracting = True if (utility.round_to(previousPos.RetractionLength,0.0001) > 0 and utility.round_to(pos.RetractionLength,0.0001) > utility.round_to(previousPos.RetractionLength,0.0001)) else False
		pos.IsPartiallyRetracted = True if utility.round_to(previousPos.RetractionLength,0.0001)>0 and utility.round_to(previousPos.RetractionLength,0.0001) < utility.round_to(self.PrinterRetractionLength,0.0001) else False
		pos.IsRetracted = True if utility.round_to(previousPos.RetractionLength,0.0001) > 0 and utility.round_to(previousPos.RetractionLength,0.0001) >= utility.round_to(self.PrinterRetractionLength,0.0001) else False
		pos.IsDetractingStart = True if utility.round_to(pos.DetractionLength,0.0001) > 0 and utility.round_to(previousPos.DetractionLength,0.0001) == 0 else False
		pos.IsDetracting = True if utility.round_to(previousPos.DetractionLength,0.0001) > 0 and utility.round_to(pos.DetractionLength,0.0001) > 0 else False
		pos.IsDetracted = True if utility.round_to(previousPos.RetractionLength,0.0001) == 0 and utility.round_to(previousPos.DetractionLength,0.0001) > 0 and utility.round_to(previousPos.ExtrusionLength,0.0001) == 0 else False

		if(
			previousPos.RetractionLength != pos.RetractionLength 
			or previousPos.IsExtrudingStart != pos.IsExtrudingStart
			or previousPos.IsExtruding != pos.IsExtruding
			or previousPos.IsPrimed != pos.IsPrimed
			or previousPos.IsRetractingStart != pos.IsRetractingStart
			or previousPos.IsRetracting != pos.IsRetracting
			or previousPos.IsPartiallyRetracted != pos.IsPartiallyRetracted
			or previousPos.IsRetracted != pos.IsRetracted
			or previousPos.IsDetractingStart != pos.IsDetractingStart
			or previousPos.IsDetracting != pos.IsDetracting
			or previousPos.IsDetracted != pos.IsDetracted
		):
			self.HasChanged = True

		if(self.HasChanged):
			self.Settings.CurrentDebugProfile().LogExtruderChange("Extruder Changed: E:{0}, Retraction:{1} IsExtruding:{2}-{3}, IsExtrudingStart:{4}-{5}, IsPrimed:{6}-{7}, IsRetractingStart:{8}-{9}, IsRetracting:{10}-{11}, IsPartiallyRetracted:{12}-{13}, IsRetracted:{14}-{15}, IsDetractingStart:{16}-{17}, IsDetracting:{18}-{19}, IsDetracted:{20}-{21}"
			.format( pos.E
				, pos.RetractionLength
				, previousPos.IsExtruding
				, pos.IsExtruding
				, previousPos.IsExtrudingStart
				, pos.IsExtrudingStart
				, previousPos.IsPrimed
				, pos.IsPrimed
				, previousPos.IsRetractingStart
				, pos.IsRetractingStart
				, previousPos.IsRetracting
				, pos.IsRetracting
				, previousPos.IsPartiallyRetracted 
				, pos.IsPartiallyRetracted
				, previousPos.IsRetracted
				, pos.IsRetracted
				, previousPos.IsDetractingStart
				, pos.IsDetractingStart
				, previousPos.IsDetracting
				, pos.IsDetracting
				, previousPos.IsDetracted
				, pos.IsDetracted))


	def ExtruderStateTriggered(self, option, state):
		if(option is None):
			return None
		if(option and state):
			return True
		if(not option and state):
			return False
		return None

	def IsTriggered(self, options):
		if(len(self.StateHistory)<1):
			return False

		state = self.StateHistory[0]
		"""Matches the supplied extruder trigger options to the current extruder state.  Returns true if triggering, false if not."""
		extrudingStartTriggered		= self.ExtruderStateTriggered(options.OnExtrudingStart ,state.IsExtrudingStart)
		extrudingTriggered			= self.ExtruderStateTriggered(options.OnExtruding, state.IsExtruding)
		primedTriggered				= self.ExtruderStateTriggered(options.OnPrimed, state.IsPrimed)
		retractingStartTriggered	= self.ExtruderStateTriggered(options.OnRetractingStart, state.IsRetractingStart)
		retractingTriggered			= self.ExtruderStateTriggered(options.OnRetracting, state.IsRetracting)
		partiallyRetractedTriggered	= self.ExtruderStateTriggered(options.OnPartiallyRetracted, state.IsPartiallyRetracted)
		retractedTriggered			= self.ExtruderStateTriggered(options.OnRetracted, state.IsRetracted)
		detractingStartTriggered	= self.ExtruderStateTriggered(options.OnDetractingStart, state.IsDetractingStart)
		detractingTriggered			= self.ExtruderStateTriggered(options.OnDetracting, state.IsDetracting)
		detractedTriggered			= self.ExtruderStateTriggered(options.OnDetracted, state.IsDetracted)

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
			.format( state.E
				, state.RetractionLength
				, state.IsExtruding
				, extrudingTriggered
				, state.IsExtrudingStart
				, extrudingStartTriggered
				, state.IsPrimed
				, primedTriggered
				, state.IsRetracting
				, retractingTriggered
				, state.IsRetracted
				, retractedTriggered
				, state.IsDetracting
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

