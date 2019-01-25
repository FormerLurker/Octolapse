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

    def is_state_equal(self, extruder):
        if (self.IsExtrudingStart != extruder.IsExtrudingStart
                or self.IsExtruding != extruder.IsExtruding
                or self.IsPrimed != extruder.IsPrimed
                or self.IsRetractingStart != extruder.IsRetractingStart
                or self.IsRetracting != extruder.IsRetracting
                or self.IsRetracted != extruder.IsRetracted
                or self.IsPartiallyRetracted != extruder.IsPartiallyRetracted
                or self.IsDeretractingStart != extruder.IsDeretractingStart
                or self.IsDeretracting != extruder.IsDeretracting
                or self.IsDeretracted != extruder.IsDeretracted):
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
        self.StateHistory = deque(maxlen=5)
        self.reset()
        self.add_state(ExtruderState())

    def reset(self):
        self.StateHistory.clear()

    def get_state(self, index=0):
        if len(self.StateHistory) > index:
            return self.StateHistory[index]
        return None

    def add_state(self, state):
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
    def has_changed(self, index=0):
        state = self.get_state(index)
        if state is not None:
            return state.HasChanged
        return False

    def is_primed(self, index=0):
        state = self.get_state(index)
        if state is not None:
            return state.IsPrimed
        return False

    def is_extruding(self, index=0):
        state = self.get_state(index)
        if state is not None:
            return state.IsExtruding
        return False

    def is_extruding_start(self, index=0):
        state = self.get_state(index)
        if state is not None:
            return state.IsExtrudingStart
        return False

    def is_retracting_start(self, index=0):
        state = self.get_state(index)
        if state is not None:
            return state.IsRetractingStart
        return False

    def is_retracting(self, index=0):
        state = self.get_state(index)
        if state is not None:
            return state.IsRetracting
        return False

    def is_partially_retracted(self, index=0):
        state = self.get_state(index)
        if state is not None:
            return state.IsPartiallyRetracted
        return False

    def is_retracted(self, index=0):
        state = self.get_state(index)
        if state is not None:
            return state.IsRetracted
        return False

    def is_deretracting_start(self, index=0):
        state = self.get_state(index)
        if state is not None:
            return state.IsDeretractingStart
        return False

    def is_deretracting(self, index=0):
        state = self.get_state(index)
        if state is not None:
            return state.IsDeretracting
        return False

    def is_deretracted(self, index=0):
        state = self.get_state(index)
        if state is not None:
            return state.IsDeretracted
        return False

    def extrusion_length_total(self, index=0):
        state = self.get_state(index)
        if state is not None:
            return state.ExtrusionLengthTotal
        return False

    def length_to_retract(self, index=0):
        state = self.get_state(index)

        # if we don't have any history, we want to retract
        if state is None:
            self.Settings.Logger.log_error("extruder.py - A 'length_to_retract' was requested, "
                                                            "but the extruder haa no state history!")
            return self.PrinterRetractionLength

        retract_length = self.PrinterRetractionLength - state.RetractionLength

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

        # return the calculated retraction length
        return retract_length

    def undo_update(self):
        if len(self.StateHistory) == 0:
            return None
        return self.StateHistory.popleft()

    # Update the extrusion monitor.  E (extruder delta) must be relative, not absolute!
    def update(self, e_relative, update_state=True):
        if e_relative is None:
            return

        e = float(e_relative)
        if e is None or abs(e) < utility.FLOAT_MATH_EQUALITY_RANGE:
            e = 0.0

        num_states = len(self.StateHistory)
        if num_states > 0:
            state = ExtruderState(state=self.StateHistory[0])
            previous_state = ExtruderState(state=self.StateHistory[0])
        else:
            state = ExtruderState()
            previous_state = ExtruderState()

        state.E = e

        if update_state:
            # we want to update the state before adding it to the queue
            # do that here

            # Update RetractionLength and ExtrusionLength
            state.RetractionLength -= e

            # do not round the retraction length
            # state.RetractionLength = utility.round_to(state.RetractionLength, self.PrinterTolerance)

            if state.RetractionLength <= utility.FLOAT_MATH_EQUALITY_RANGE:
                # we can use the negative retraction length to calculate our extrusion length!
                state.ExtrusionLength = abs(state.RetractionLength)
                # set the retraction length to 0 since we are extruding
                state.RetractionLength = 0
            else:
                state.ExtrusionLength = 0
            # Update extrusion length
            state.ExtrusionLengthTotal += state.ExtrusionLength

            # calculate deretraction length
            if previous_state.RetractionLength > state.RetractionLength:

                state.DeretractionLength = previous_state.RetractionLength - state.RetractionLength

                # do not round the deretraction length
                # state.DeretractionLength = utility.round_to(state.DeretractionLength,self.PrinterTolerance)

            else:
                state.DeretractionLength = 0

            # round our lengths to the nearest .05mm to avoid some floating point math errors
            self._update_state(state, previous_state)
            # Add the current position, remove positions if we have more than 5 from the end
        self.add_state(state)

    def _update_state(self, state, state_previous):

        retraction_length = utility.round_to(state.RetractionLength, self.PrinterTolerance)
        deretraction_length = utility.round_to(state.DeretractionLength, self.PrinterTolerance)
        extrusion_length = utility.round_to(state.ExtrusionLength, self.PrinterTolerance)

        previous_retraction_length = utility.round_to(state_previous.RetractionLength, self.PrinterTolerance)
        previous_deretraction_length = utility.round_to(state_previous.DeretractionLength, self.PrinterTolerance)

        state.IsExtrudingStart = True if extrusion_length > 0 and state_previous.ExtrusionLength == 0 else False
        state.IsExtruding = True if extrusion_length > 0 else False
        state.IsPrimed = True if extrusion_length == 0 and retraction_length == 0 else False
        state.IsRetractingStart = True if previous_retraction_length == 0 and retraction_length > 0 else False
        state.IsRetracting = True if retraction_length > previous_retraction_length else False
        state.IsPartiallyRetracted = True if (0 < retraction_length < self.PrinterRetractionLength) else False
        state.IsRetracted = True if retraction_length >= self.PrinterRetractionLength else False
        state.IsDeretractingStart = True if deretraction_length > 0 and previous_deretraction_length == 0 else False
        state.IsDeretracting = True if deretraction_length > previous_deretraction_length else False
        state.IsDeretracted = True if previous_retraction_length > 0 and retraction_length == 0 else False

        if not state.is_state_equal(state_previous):
            state.HasChanged = True
        else:
            state.HasChanged = False
        if state.HasChanged:
            message = (
                "Extruder Changed: E:{0}, Retraction:{1} IsExtruding:{2}-{3}, "
                "IsExtrudingStart:{4}-{5}, IsPrimed:{6}-{7}, IsRetractingStart:{8}-{9}, "
                "IsRetracting:{10}-{11}, IsPartiallyRetracted:{12}-{13}, "
                "IsRetracted:{14}-{15}, IsDeretractingStart:{16}-{17}, "
                "IsDeretracting:{18}-{19}, IsDeretracted:{20}-{21}"
            ).format(
                state.E,
                state.RetractionLength,
                state_previous.IsExtruding,
                state.IsExtruding,
                state_previous.IsExtrudingStart,
                state.IsExtrudingStart,
                state_previous.IsPrimed,
                state.IsPrimed,
                state_previous.IsRetractingStart,
                state.IsRetractingStart,
                state_previous.IsRetracting,
                state.IsRetracting,
                state_previous.IsPartiallyRetracted,
                state.IsPartiallyRetracted,
                state_previous.IsRetracted,
                state.IsRetracted,
                state_previous.IsDeretractingStart,
                state.IsDeretractingStart,
                state_previous.IsDeretracting,
                state.IsDeretracting,
                state_previous.IsDeretracted,
                state.IsDeretracted
            )

            self.Settings.Logger.log_extruder_change(message)

    @staticmethod
    def _extruder_state_triggered(option, state):
        if option is None:
            return None
        if option and state:
            return True
        if not option and state:
            return False
        return None

    def is_triggered(self, options, index=0):
        # if there are no extruder trigger options, return true.
        if options is None:
            return True

        state = self.get_state(index)
        if state is None:
            return False

        # Matches the supplied extruder trigger options to the current
        # extruder state.  Returns true if triggering, false if not.

        extruding_start_triggered = self._extruder_state_triggered(
            options.OnExtrudingStart, state.IsExtrudingStart
        )
        extruding_triggered = self._extruder_state_triggered(
            options.OnExtruding, state.IsExtruding
        )
        primed_triggered = self._extruder_state_triggered(
            options.OnPrimed, state.IsPrimed
        )
        retracting_start_triggered = self._extruder_state_triggered(
            options.OnRetractingStart, state.IsRetractingStart
        )
        retracting_triggered = self._extruder_state_triggered(
            options.OnRetracting, state.IsRetracting
        )
        partially_retracted_triggered = self._extruder_state_triggered(
            options.OnPartiallyRetracted, state.IsPartiallyRetracted
        )
        retracted_triggered = self._extruder_state_triggered(
            options.OnRetracted, state.IsRetracted
        )
        deretracting_start_triggered = self._extruder_state_triggered(
            options.OnDeretractingStart, state.IsDeretractingStart
        )
        deretracting_triggered = self._extruder_state_triggered(
            options.OnDeretracting, state.IsDeretracting
        )
        deretracted_triggered = self._extruder_state_triggered(
            options.OnDeretracted, state.IsDeretracted
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

        if ret_value:
            message = (
                "Triggered E:{0}, Retraction:{1} IsExtruding:{2}-{3}, "
                "IsExtrudingStart:{4}-{5}, IsPrimed:{6}-{7}, "
                "IsRetracting:{8}-{9}, IsRetracted:{10}-{11}, "
                "IsDeretracting:{12}-{13}, IsTriggered:{14}"
            ).format(
                state.E,
                state.RetractionLength,
                state.IsExtruding,
                extruding_triggered,
                state.IsExtrudingStart,
                extruding_start_triggered,
                state.IsPrimed,
                primed_triggered,
                state.IsRetracting,
                retracting_triggered,
                state.IsRetracted,
                retracted_triggered,
                state.IsDeretracting,
                deretracted_triggered,
                ret_value
            )
            self.Settings.Logger.log_extruder_triggered(message)

        return ret_value


class ExtruderTriggers(object):
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
        if (self.OnExtrudingStart is None
                and self.OnExtruding is None
                and self.OnPrimed is None
                and self.OnRetractingStart is None
                and self.OnRetracting is None
                and self.OnPartiallyRetracted is None
                and self.OnRetracted is None
                and self.OnDeretractingStart is None
                and self.OnDeretracting is None
                and self.OnDeretracted is None):
            return True
        return False
