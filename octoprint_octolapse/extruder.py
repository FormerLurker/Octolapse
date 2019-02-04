# coding=utf-8
##################################################################################
# Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
# Copyright (C) 2017  Brad Hochgesang
##################################################################################
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see the following:
# https://github.com/FormerLurker/Octolapse/blob/master/LICENSE
#
# You can contact the author either through the git-hub repository, or at the
# following email address: FormerLurker@pm.me
##################################################################################

from collections import deque

import octoprint_octolapse.utility as utility
from octoprint_octolapse.settings import PrinterProfile, OctolapseGcodeSettings

class ExtruderState(object):
    __slots__ = [
        'E',
        'ExtrusionLength',
        'ExtrusionLengthTotal',
        'RetractionLength',
        'DeretractionLength',
        'IsExtrudingStart',
        'IsExtruding',
        'IsPrimed',
        'IsRetractingStart',
        'IsRetracting',
        'IsRetracted',
        'IsPartiallyRetracted',
        'IsDeretractingStart',
        'IsDeretracting',
        'IsDeretracted',
        'HasChanged'
    ]

    def __init__(self, state=None):
        self.E = 0 if state is None else state.E
        self.ExtrusionLength = 0.0 if state is None else state.ExtrusionLength
        self.ExtrusionLengthTotal = 0.0 if state is None else state.ExtrusionLengthTotal
        self.RetractionLength = 0.0 if state is None else state.RetractionLength
        self.DeretractionLength = 0.0 if state is None else state.DeretractionLength
        self.IsExtrudingStart = False if state is None else state.IsExtrudingStart
        self.IsExtruding = False if state is None else state.IsExtruding
        self.IsPrimed = False if state is None else state.IsPrimed
        self.IsRetractingStart = False if state is None else state.IsRetractingStart
        self.IsRetracting = False if state is None else state.IsRetracting
        self.IsRetracted = False if state is None else state.IsRetracted
        self.IsPartiallyRetracted = False if state is None else state.IsPartiallyRetracted
        self.IsDeretractingStart = False if state is None else state.IsDeretractingStart
        self.IsDeretracting = False if state is None else state.IsDeretracting
        self.IsDeretracted = False if state is None else state.IsDeretracted
        self.HasChanged = False if state is None else state.HasChanged

    @staticmethod
    def copy_to(source, target):
        target.E = source.E
        target.ExtrusionLength = source.ExtrusionLength
        target.ExtrusionLengthTotal = source.ExtrusionLengthTotal
        target.RetractionLength = source.RetractionLength
        target.DeretractionLength = source.DeretractionLength
        target.IsExtrudingStart = source.IsExtrudingStart
        target.IsExtruding = source.IsExtruding
        target.IsPrimed = source.IsPrimed
        target.IsRetractingStart = source.IsRetractingStart
        target.IsRetracting = source.IsRetracting
        target.IsRetracted = source.IsRetracted
        target.IsPartiallyRetracted = source.IsPartiallyRetracted
        target.IsDeretractingStart = source.IsDeretractingStart
        target.IsDeretracting = source.IsDeretracting
        target.IsDeretracted = source.IsDeretracted
        target.HasChanged = source.HasChanged
        return target

    def is_state_equal(self, extruder):
        if (
            self.IsExtrudingStart != extruder.IsExtrudingStart
            or self.IsExtruding != extruder.IsExtruding
            or self.IsPrimed != extruder.IsPrimed
            or self.IsRetractingStart != extruder.IsRetractingStart
            or self.IsRetracting != extruder.IsRetracting
            or self.IsRetracted != extruder.IsRetracted
            or self.IsPartiallyRetracted != extruder.IsPartiallyRetracted
            or self.IsDeretractingStart != extruder.IsDeretractingStart
            or self.IsDeretracting != extruder.IsDeretracting
            or self.IsDeretracted != extruder.IsDeretracted
        ):
            return False
        return True

    def to_dict(self):
        return {
            "E": self.E,
            "ExtrusionLength": self.ExtrusionLength,
            "ExtrusionLengthTotal": self.ExtrusionLengthTotal,
            "RetractionLength": self.RetractionLength,
            "DeretractionLength": self.DeretractionLength,
            "IsExtrudingStart": self.IsExtrudingStart,
            "IsExtruding": self.IsExtruding,
            "IsPrimed": self.IsPrimed,
            "IsRetractingStart": self.IsRetractingStart,
            "IsRetracting": self.IsRetracting,
            "IsRetracted": self.IsRetracted,
            "IsPartiallyRetracted": self.IsPartiallyRetracted,
            "IsDeretractingStart": self.IsDeretractingStart,
            "IsDeretracting": self.IsDeretracting,
            "IsDeretracted": self.IsDeretracted,
            "HasChanged": self.HasChanged
        }


class Extruder(object):
    """The extruder monitor only works with relative extruder values"""

    def __init__(self, octolapse_settings):
        self.Settings = octolapse_settings

        self.gcode_generation_settings = self.Settings.profiles.current_printer().get_current_state_detection_settings()
        assert (isinstance(self.gcode_generation_settings, OctolapseGcodeSettings))

        self.PrinterRetractionLength = self.gcode_generation_settings.retraction_length
        self.PrinterTolerance = self.Settings.profiles.current_printer().printer_position_confirmation_tolerance
        self.max_states = 5
        self.StateHistory = deque(maxlen=self.max_states)
        self.reset()

        self.current_state = ExtruderState()
        self.previous_state = ExtruderState()
        #self.free_state = None
        # add the first two states in reverse dorder
        self.add_state(self.previous_state)
        self.add_state(self.current_state)


    def reset(self):
        self.StateHistory.clear()

    def get_state(self, index=0):
        if len(self.StateHistory) > index:
            return self.StateHistory[index]
        return None

    def add_state(self, state):
        #if len(self.StateHistory) == self.max_states:
        #    self.free_state = self.StateHistory.popleft()
        self.StateHistory.appendleft(state)

    def to_dict(self, index=0):
        state = self.get_state(index)
        if state is not None:
            return state.to_dict()
        return None

    #######################################
    # Access ExtruderStates and calculated
    # values from from StateHistory
    #######################################

    def length_to_retract(self):
        # if we don't have any history, we want to retract
        retract_length = self.PrinterRetractionLength - self.current_state.RetractionLength

        # Don't round the retraction length
        # retractLength = utility.round_to(retract_length, self.PrinterTolerance)

        if retract_length < 0:
            # This means we are beyond fully retracted, return 0
            self.Settings.Logger.log_warning("extruder.py - A 'length_to_retract' was requested, "
                                                              "but the extruder is beyond the configured retraction "
                                                              "length.")
            retract_length = 0
        elif retract_length > self.PrinterRetractionLength:
            self.Settings.Logger.log_error("extruder.py - A 'length_to_retract' was requested, "
                                                            "but was found to be greater than the retraction "
                                                            "length.")
            # for some reason we are over the retraction length.  Return 0
            retract_length = self.PrinterRetractionLength

        if abs(retract_length) < utility.FLOAT_MATH_EQUALITY_RANGE:
            return 0.0
        # return the calculated retraction length
        return retract_length

    def undo_update(self):
        if len(self.StateHistory) < 2:
            return None
        return self.StateHistory.popleft()

    # Update the extrusion monitor.  E (extruder delta) must be relative, not absolute!
    def update(self, e_relative, update_state=True):
        if e_relative is None:
            return
        if not isinstance(e_relative, float):
            e_relative = float(e_relative)

        e_relative = utility.round_to_value(e_relative, utility.FLOAT_MATH_EQUALITY_RANGE)

        self.previous_state = ExtruderState.copy_to(self.current_state, self.previous_state)
        self.current_state = ExtruderState(self.previous_state)

        ## for performance reasons we're reusing any states that were popped from the StateList
        #if self.free_state is not None:
        #    self.current_state = ExtruderState.copy_to(self.previous_state, self.free_state)
        #    self.free_state = None
        #else:
        #    # If we don't have any popped states, create a new one
        #    self.current_state = ExtruderState(self.previous_state)

        self.current_state.E = e_relative

        if update_state:
            # we want to update the state before adding it to the queue
            # do that here

            # Update RetractionLength and ExtrusionLength
            self.current_state.RetractionLength = utility.round_to_value(self.current_state.RetractionLength - e_relative, utility.FLOAT_MATH_EQUALITY_RANGE)

            # do not round the retraction length
            # state.RetractionLength = utility.round_to(state.RetractionLength, self.PrinterTolerance)

            if self.current_state.RetractionLength <= utility.FLOAT_MATH_EQUALITY_RANGE:
                # we can use the negative retraction length to calculate our extrusion length!
                self.current_state.ExtrusionLength = abs(self.current_state.RetractionLength)
                # set the retraction length to 0 since we are extruding
                self.current_state.RetractionLength = 0
            else:
                self.current_state.ExtrusionLength = 0
            # Update extrusion length
                self.current_state.ExtrusionLengthTotal = utility.round_to_value(self.current_state.ExtrusionLengthTotal + self.current_state.ExtrusionLength, utility.FLOAT_MATH_EQUALITY_RANGE)

            # calculate deretraction length
            if self.previous_state.RetractionLength > self.current_state.RetractionLength:

                self.current_state.DeretractionLength = utility.round_to_value(self.previous_state.RetractionLength - self.current_state.RetractionLength,utility.FLOAT_MATH_EQUALITY_RANGE)
            else:
                self.current_state.DeretractionLength = 0

            # round our lengths to avoid some floating point math errors
            # we don't have to round here.  We could implement some greater or close
            self.current_state.IsExtrudingStart = True if self.current_state.ExtrusionLength > 0 and self.previous_state.ExtrusionLength == 0else False
            self.current_state.IsExtruding = True if self.current_state.ExtrusionLength > 0 else False
            self.current_state.IsPrimed = True if self.current_state.ExtrusionLength == 0 and self.current_state.RetractionLength else False
            self.current_state.IsRetractingStart = True if self.previous_state.RetractionLength == 0 and self.current_state.RetractionLength > 0 else False
            self.current_state.IsRetracting = True if self.current_state.RetractionLength > self.previous_state.RetractionLength else False
            self.current_state.IsPartiallyRetracted = True if (0 < self.current_state.RetractionLength < self.PrinterRetractionLength) else False
            self.current_state.IsRetracted = True if self.current_state.RetractionLength >= self.PrinterRetractionLength else False
            self.current_state.IsDeretractingStart = True if self.current_state.DeretractionLength > 0 and self.previous_state.DeretractionLength == 0 else False
            self.current_state.IsDeretracting = True if self.current_state.DeretractionLength > self.previous_state.DeretractionLength else False
            self.current_state.IsDeretracted = True if self.previous_state.RetractionLength > 0 and self.current_state.RetractionLength == 0 else False

            if not self.current_state.is_state_equal(self.previous_state):
                self.current_state.HasChanged = True
            else:
                self.current_state.HasChanged = False
                
            # Add the current position, remove positions if we have more than 5 from the end
        self.add_state(self.current_state)

    @staticmethod
    def _extruder_state_triggered(option, state):
        if option is None:
            return None
        if option and state:
            return True
        if not option and state:
            return False
        return None

    def is_triggered(self, options):
        # if there are no extruder trigger options, return true.
        if options is None:
            return True


        # Matches the supplied extruder trigger options to the current
        # extruder state.  Returns true if triggering, false if not.

        extruding_start_triggered = self._extruder_state_triggered(
            options.OnExtrudingStart, self.current_state.IsExtrudingStart
        )
        extruding_triggered = self._extruder_state_triggered(
            options.OnExtruding, self.current_state.IsExtruding
        )
        primed_triggered = self._extruder_state_triggered(
            options.OnPrimed, self.current_state.IsPrimed
        )
        retracting_start_triggered = self._extruder_state_triggered(
            options.OnRetractingStart, self.current_state.IsRetractingStart
        )
        retracting_triggered = self._extruder_state_triggered(
            options.OnRetracting, self.current_state.IsRetracting
        )
        partially_retracted_triggered = self._extruder_state_triggered(
            options.OnPartiallyRetracted, self.current_state.IsPartiallyRetracted
        )
        retracted_triggered = self._extruder_state_triggered(
            options.OnRetracted, self.current_state.IsRetracted
        )
        deretracting_start_triggered = self._extruder_state_triggered(
            options.OnDeretractingStart, self.current_state.IsDeretractingStart
        )
        deretracting_triggered = self._extruder_state_triggered(
            options.OnDeretracting, self.current_state.IsDeretracting
        )
        deretracted_triggered = self._extruder_state_triggered(
            options.OnDeretracted, self.current_state.IsDeretracted
        )

        ret_value = False
        is_triggering_prevented = (
            (extruding_start_triggered is not None and not extruding_start_triggered)
            or (extruding_triggered is not None and not extruding_triggered)
            or (primed_triggered is not None and not primed_triggered)
            or (retracting_start_triggered is not None and not retracting_start_triggered)
            or (retracting_triggered is not None and not retracting_triggered)
            or (partially_retracted_triggered is not None and not partially_retracted_triggered)
            or (retracted_triggered is not None and not retracted_triggered)
            or (deretracting_start_triggered is not None and not deretracting_start_triggered)
            or (deretracting_triggered is not None and not deretracting_triggered)
            or (deretracted_triggered is not None and not deretracted_triggered))

        if (not is_triggering_prevented
            and
            (
                (extruding_start_triggered is not None and extruding_start_triggered)
                or (extruding_triggered is not None and extruding_triggered)
                or (primed_triggered is not None and primed_triggered)
                or (retracting_start_triggered is not None and retracting_start_triggered)
                or (retracting_triggered is not None and retracting_triggered)
                or (partially_retracted_triggered is not None and partially_retracted_triggered)
                or (retracted_triggered is not None and retracted_triggered)
                or (deretracting_start_triggered is not None and deretracting_start_triggered)
                or (deretracting_triggered is not None and deretracting_triggered)
                or (deretracted_triggered is not None and deretracted_triggered)
                or (options.are_all_triggers_ignored()))):
            ret_value = True

        return ret_value


class ExtruderTriggers(object):
    __slots__ = [
        'OnExtrudingStart',
        'OnExtruding',
        'OnPrimed',
        'OnRetractingStart',
        'OnRetracting',
        'OnPartiallyRetracted',
        'OnRetracted',
        'OnDeretractingStart',
        'OnDeretracting',
        'OnDeretracted'
    ]
    def __init__(
            self, on_extruding_start, on_extruding, on_primed,
            on_retracting_start, on_retracting, on_partially_retracted,
            on_retracted, on_deretracting_start, on_deretracting, on_deretracted):
        # To trigger on an extruder state, set to True.
        # To prevent triggering on an extruder state, set to False.
        # To ignore the extruder state, set to None
        self.OnExtrudingStart = on_extruding_start
        self.OnExtruding = on_extruding
        self.OnPrimed = on_primed
        self.OnRetractingStart = on_retracting_start
        self.OnRetracting = on_retracting
        self.OnPartiallyRetracted = on_partially_retracted
        self.OnRetracted = on_retracted
        self.OnDeretractingStart = on_deretracting_start
        self.OnDeretracting = on_deretracting
        self.OnDeretracted = on_deretracted

    def are_all_triggers_ignored(self):
        if (
            self.OnExtrudingStart is None
            and self.OnExtruding is None
            and self.OnPrimed is None
            and self.OnRetractingStart is None
            and self.OnRetracting is None
            and self.OnPartiallyRetracted is None
            and self.OnRetracted is None
            and self.OnDeretractingStart is None
            and self.OnDeretracting is None
            and self.OnDeretracted is None
        ):
            return True
        return False
