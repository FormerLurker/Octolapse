# This file is subject to the terms and conditions defined in
# file called 'LICENSE', which is part of this source code package.

from octoprint_octolapse.settings import *
import octoprint_octolapse.utility as utility


class ExtruderState(object):
    def __init__(self, state=None):
        self.E = 0 if state is None else state.E
        self.ExtrusionLength = 0.0 if state is None else state.ExtrusionLength
        self.ExtrusionLengthTotal = 0.0 if state is None else state.ExtrusionLengthTotal
        self.RetractionLength = 0.0 if state is None else state.RetractionLength
        self.DetractionLength = 0.0 if state is None else state.DetractionLength
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

    def IsStateEqual(self, extruder):
        if(
                self.IsExtrudingStart != extruder.IsExtrudingStart
                or self.IsExtruding != extruder.IsExtruding
                or self.IsPrimed != extruder.IsPrimed
                or self.IsRetractingStart != extruder.IsRetractingStart
                or self.IsRetracting != extruder.IsRetracting
                or self.IsRetracted != extruder.IsRetracted
                or self.IsPartiallyRetracted != extruder.IsPartiallyRetracted
                or self.IsDetractingStart != extruder.IsDetractingStart
                or self.IsDetracting != extruder.IsDetracting
                or self.IsDetracted != extruder.IsDetracted):
            return False
        return True

    def ToDict(self):
        return {
            "E": self.E,
            "ExtrusionLength": self.ExtrusionLength,
            "ExtrusionLengthTotal": self.ExtrusionLengthTotal,
            "RetractionLength": self.RetractionLength,
            "DetractionLength": self.DetractionLength,
            "IsExtrudingStart": self.IsExtrudingStart,
            "IsExtruding": self.IsExtruding,
            "IsPrimed": self.IsPrimed,
            "IsRetractingStart": self.IsRetractingStart,
            "IsRetracting": self.IsRetracting,
            "IsRetracted": self.IsRetracted,
            "IsPartiallyRetracted": self.IsPartiallyRetracted,
            "IsDetractingStart": self.IsDetractingStart,
            "IsDetracting": self.IsDetracting,
            "IsDetracted": self.IsDetracted,
            "HasChanged": self.HasChanged
        }


class Extruder(object):
    """The extruder monitor only works with relative extruder values"""

    def __init__(self, octolapseSettings):
        self.Settings = octolapseSettings
        self.PrinterRetractionLength = self.Settings.CurrentPrinter().retract_length
        self.PrinterTolerance = self.Settings.CurrentPrinter(
        ).printer_position_confirmation_tolerance
        self.Reset()
        self.AddState(ExtruderState())

    def Reset(self):
        self.StateHistory = []

    def GetState(self, index=0):
        if(len(self.StateHistory) > index):
            return self.StateHistory[index]
        return None

    def AddState(self, state):
        self.StateHistory.insert(0, state)
        while (len(self.StateHistory) > 5):
            del self.StateHistory[5]

    def ToDict(self, index=0):
        state = GetState(index)
        if(state is not None):
            return state.ToDict()
        return None

    #######################################
    # Access ExtruderStates and calculated
    # values from from StateHistory
    #######################################
    def HasChanged(self, index=0):
        state = self.GetState(index)
        if(state is not None):
            return state.HasChanged
        return False

    def IsExtruding(self, index=0):
        state = self.GetState(index)
        if(state is not None):
            return state.IsExtruding
        return False

    def IsExtrudingStart(self, index=0):
        state = self.GetState(index)
        if(state is not None):
            return state.IsExtrudingStart
        return False

    def IsRetractingStart(self, index=0):
        state = self.GetState(index)
        if(state is not None):
            return state.IsRetractingStart
        return False

    def IsRetracted(self, index=0):
        state = self.GetState(index)
        if(state is not None):
            return state.IsRetracted
        return False

    def ExtrusionLengthTotal(self, index=0):
        state = self.GetState(index)
        if(state is not None):
            return state.ExtrusionLengthTotal
        return False

    def ExtrusionLengthTotal(self, index=0):
        state = self.GetState(index)
        if(state is not None):
            return state.ExtrusionLengthTotal
        return False

    def LengthToRetract(self, index=0):
        state = self.GetState(index)
        if(state is not None):
            retractLength = utility.round_to(
                self.PrinterRetractionLength - self.StateHistory[0].RetractionLength, self.PrinterTolerance)
            if(retractLength <= 0):
                retractLength = 0
            return retractLength
        return self.PrinterRetractionLength

    def UndoUpdate(self):
        state = self.GetState(0)
        if(state is not None):
            del self.StateHistory[0]

    # Update the extrusion monitor.  E (extruder delta) must be relative, not absolute!
    def Update(self, eRelative):
        if(eRelative is None):
            return

        e = float(eRelative)
        if(e is None or abs(e) < utility.FLOAT_MATH_EQUALITY_RANGE):
            e = 0.0

        state = None
        previousState = None
        numStates = len(self.StateHistory)
        if(numStates > 0):
            state = ExtruderState(state=self.StateHistory[0])
            previousState = ExtruderState(state=self.StateHistory[0])
        else:
            state = ExtruderState()
            previousState = ExtruderState()

        state.E = e
        # Update RetractionLength and ExtrusionLength
        state.RetractionLength -= e
        state.RetractionLength = utility.round_to(
            state.RetractionLength, self.PrinterTolerance)
        if(state.RetractionLength <= utility.FLOAT_MATH_EQUALITY_RANGE):
            # we can use the negative retraction length to calculate our extrusion length!
            state.ExtrusionLength = abs(state.RetractionLength)
            # set the retraction length to 0 since we are etruding
            state.RetractionLength = 0
        else:
            state.ExtrusionLength = 0
        # Update extrusion length
        state.ExtrusionLengthTotal += state.ExtrusionLength

        # calculate detraction length
        if(previousState.RetractionLength > state.RetractionLength):
            state.DetractionLength = utility.round_to(
                previousState.RetractionLength - state.RetractionLength, self.PrinterTolerance)
        else:
            state.DetractionLength = 0
        # round our lengths to the nearest .05mm to avoid some floating point math errors

        self._UpdateState(state, previousState)
        # Add the current position, remove positions if we have more than 5 from the end
        self.AddState(state)

    def _UpdateState(self, state, statePrevious):

        state.IsExtrudingStart = True if state.ExtrusionLength > 0 and statePrevious.ExtrusionLength == 0 else False
        state.IsExtruding = True if state.ExtrusionLength > 0 else False
        state.IsPrimed = True if state.ExtrusionLength == 0 and state.RetractionLength == 0 else False
        state.IsRetractingStart = True if statePrevious.RetractionLength == 0 and state.RetractionLength > 0 else False
        state.IsRetracting = True if state.RetractionLength > statePrevious.RetractionLength else False
        state.IsPartiallyRetracted = True if (
            state.RetractionLength > 0 and state.RetractionLength < self.PrinterRetractionLength) else False
        state.IsRetracted = True if state.RetractionLength >= self.PrinterRetractionLength else False
        state.IsDetractingStart = True if state.DetractionLength > 0 and statePrevious.DetractionLength == 0 else False
        state.IsDetracting = True if state.DetractionLength > statePrevious.DetractionLength else False
        state.IsDetracted = True if statePrevious.RetractionLength > 0 and state.RetractionLength == 0 else False

        if(not state.IsStateEqual(statePrevious)):
            state.HasChanged = True
        else:
            state.HasChanged = False
        if(state.HasChanged):
            self.Settings.CurrentDebugProfile().LogExtruderChange("Extruder Changed: E:{0}, Retraction:{1} IsExtruding:{2}-{3}, IsExtrudingStart:{4}-{5}, IsPrimed:{6}-{7}, IsRetractingStart:{8}-{9}, IsRetracting:{10}-{11}, IsPartiallyRetracted:{12}-{13}, IsRetracted:{14}-{15}, IsDetractingStart:{16}-{17}, IsDetracting:{18}-{19}, IsDetracted:{20}-{21}"
                                                                  .format(state.E, state.RetractionLength, statePrevious.IsExtruding, state.IsExtruding, statePrevious.IsExtrudingStart, state.IsExtrudingStart, statePrevious.IsPrimed, state.IsPrimed, statePrevious.IsRetractingStart, state.IsRetractingStart, statePrevious.IsRetracting, state.IsRetracting, statePrevious.IsPartiallyRetracted, state.IsPartiallyRetracted, statePrevious.IsRetracted, state.IsRetracted, statePrevious.IsDetractingStart, state.IsDetractingStart, statePrevious.IsDetracting, state.IsDetracting, statePrevious.IsDetracted, state.IsDetracted))

    def _ExtruderStateTriggered(self, option, state):
        if(option is None):
            return None
        if(option and state):
            return True
        if(not option and state):
            return False
        return None

    def IsTriggered(self, options, index=0):
        state = self.GetState(index)
        if(state is None):
            return False

        """Matches the supplied extruder trigger options to the current extruder state.  Returns true if triggering, false if not."""
        extrudingStartTriggered = self._ExtruderStateTriggered(
            options.OnExtrudingStart, state.IsExtrudingStart)
        extrudingTriggered = self._ExtruderStateTriggered(
            options.OnExtruding, state.IsExtruding)
        primedTriggered = self._ExtruderStateTriggered(
            options.OnPrimed, state.IsPrimed)
        retractingStartTriggered = self._ExtruderStateTriggered(
            options.OnRetractingStart, state.IsRetractingStart)
        retractingTriggered = self._ExtruderStateTriggered(
            options.OnRetracting, state.IsRetracting)
        partiallyRetractedTriggered = self._ExtruderStateTriggered(
            options.OnPartiallyRetracted, state.IsPartiallyRetracted)
        retractedTriggered = self._ExtruderStateTriggered(
            options.OnRetracted, state.IsRetracted)
        detractingStartTriggered = self._ExtruderStateTriggered(
            options.OnDetractingStart, state.IsDetractingStart)
        detractingTriggered = self._ExtruderStateTriggered(
            options.OnDetracting, state.IsDetracting)
        detractedTriggered = self._ExtruderStateTriggered(
            options.OnDetracted, state.IsDetracted)

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
                                                                     .format(state.E, state.RetractionLength, state.IsExtruding, extrudingTriggered, state.IsExtrudingStart, extrudingStartTriggered, state.IsPrimed, primedTriggered, state.IsRetracting, retractingTriggered, state.IsRetracted, retractedTriggered, state.IsDetracting, detractedTriggered, isTriggered))

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
           and self.OnDetracted is None):
            return True
        return False
