# coding=utf-8

# This file is subject to the terms and conditions defined in
# file called 'LICENSE', which is part of this source code package.
import time
from octoprint_octolapse.command import *
from octoprint_octolapse.extruder import ExtruderTriggers
from octoprint_octolapse.settings import *


def is_in_position(restrictions, x, y):
    # we need to know if there is at least one required position
    has_required_position = False
    # isInPosition will be used to determine if we return
    # true where we have at least one required type
    in_position = False

    # loop through each restriction
    for restriction in restrictions:
        if restriction.Type == "required":
            # we have at least on required position, so at least one point must be in
            # position for us to return true
            has_required_position = True
        if restriction.is_in_position(x, y):
            if restriction.Type == "forbidden":
                # if we're in a forbidden position, return false now
                return False
            else:
                # we're in position in at least one required position restriction
                in_position = True

    if has_required_position:
        # if at least one position restriction is required
        return in_position

    # if we're here then we only have forbidden restrictions, but the point
    # was not within the restricted area(s)
    return True


class Triggers(object):
    def __init__(self, settings):
        self.Snapshot = None
        self._triggers = []
        self.reset()
        self.Settings = settings
        self.Name = "Unknown"
        self.Printer = None

    def count(self):
        try:
            return len(self._triggers)
        except Exception, e:
            self.Settings.current_debug_profile().log_exception(e)

    def reset(self):
        self.Snapshot = None
        self._triggers = []

    def create(self):
        try:
            self.reset()
            self.Printer = self.Settings.current_printer()
            self.Snapshot = self.Settings.current_snapshot()
            self.Name = self.Snapshot.name
            # create the triggers
            # If the gcode trigger is enabled, add it
            if self.Snapshot.gcode_trigger_enabled:
                # Add the trigger to the list
                self._triggers.append(GcodeTrigger(self.Settings))
            # If the layer trigger is enabled, add it
            if self.Snapshot.layer_trigger_enabled:
                self._triggers.append(LayerTrigger(self.Settings))
            # If the layer trigger is enabled, add it
            if self.Snapshot.timer_trigger_enabled:
                self._triggers.append(TimerTrigger(self.Settings))
        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)

    def resume(self):
        try:
            for trigger in self._triggers:
                if type(trigger) == TimerTrigger:
                    trigger.resume()
        except Exception, e:
            self.Settings.current_debug_profile().log_exception(e)

    def pause(self):
        try:
            for trigger in self._triggers:
                if type(trigger) == TimerTrigger:
                    trigger.pause()
        except Exception, e:
            self.Settings.current_debug_profile().log_exception(e)

    def update(self, position, cmd):
        """Update all triggers and return any that are triggering"""
        try:
            # Loop through all of the active currentTriggers
            for currentTrigger in self._triggers:
                # determine what type the current trigger is and update appropriately
                if isinstance(currentTrigger, GcodeTrigger):
                    currentTrigger.update(position, cmd)
                elif isinstance(currentTrigger, TimerTrigger):
                    currentTrigger.update(position)
                elif isinstance(currentTrigger, LayerTrigger):
                    currentTrigger.update(position)

                # Make sure there are no position errors (unknown position, out of bounds, etc)
                if position.has_position_error(0):
                    self.Settings.current_debug_profile().log_error(
                        "A trigger has a position error:{0}".format(position.position_error(0)))
                # see if the current trigger is triggering, indicting that a snapshot should be taken
        except Exception, e:
            self.Settings.current_debug_profile().log_exception(e)

        return None

    def get_first_triggering(self, index):
        if len(self._triggers) < 1:
            return False
        try:
            # Loop through all of the active currentTriggers
            for currentTrigger in self._triggers:
                if currentTrigger.is_triggered(index):
                    return currentTrigger
        except Exception, e:
            self.Settings.current_debug_profile().log_exception(e)
            return False

    def get_first_waiting(self):
        try:
            # Loop through all of the active currentTriggers
            for currentTrigger in self._triggers:
                if currentTrigger.is_waiting(0):
                    return currentTrigger
        except Exception, e:
            self.Settings.current_debug_profile().log_exception(e)

    def has_changed(self):
        try:
            # Loop through all of the active currentTriggers
            for currentTrigger in self._triggers:
                if currentTrigger.has_changed(0):
                    return True
        except Exception, e:
            self.Settings.current_debug_profile().log_exception(e)
            return None
        return False

    def state_to_list(self):
        state_list = []
        try:
            # Loop through all of the active currentTriggers
            for currentTrigger in self._triggers:
                state_list.append(currentTrigger.to_dict(0))
        except Exception, e:
            self.Settings.current_debug_profile().log_exception(e)
            return None
        return state_list

    def changes_to_list(self):
        change_list = []
        try:
            # Loop through all of the active currentTriggers
            for currentTrigger in self._triggers:
                if currentTrigger.has_changed(0):
                    change_list.append(currentTrigger.to_dict(0))
        except Exception, e:
            self.Settings.current_debug_profile().log_exception(e)
            return None
        return change_list


class TriggerState(object):
    def __init__(self, state=None):
        self.IsTriggered = False if state is None else state.IsTriggered
        self.IsWaiting = False if state is None else state.IsWaiting
        self.IsWaitingOnZHop = False if state is None else state.IsWaitingOnZHop
        self.IsWaitingOnExtruder = False if state is None else state.IsWaitingOnExtruder
        self.IsInPosition = False if state is None else state.IsInPosition
        self.HasChanged = False if state is None else state.HasChanged
        self.IsHomed = False if state is None else state.IsHomed

    def to_dict(self, trigger):
        return {
            "IsTriggered": self.IsTriggered,
            "IsWaiting": self.IsWaiting,
            "IsWaitingOnZHop": self.IsWaitingOnZHop,
            "IsWaitingOnExtruder": self.IsWaitingOnExtruder,
            "IsInPosition": self.IsInPosition,
            "HasChanged": self.HasChanged,
            "RequireZHop": trigger.RequireZHop,
            "IsHomed": self.IsHomed,
            "TriggeredCount": trigger.TriggeredCount
        }

    def reset_state(self):
        self.IsTriggered = False
        self.HasChanged = False
        self.IsInPosition = False

    def is_equal(self, state):
        if (state is not None
                and self.IsTriggered == state.IsTriggered
                and self.IsWaiting == state.IsWaiting
                and self.IsWaitingOnZHop == state.IsWaitingOnZHop
                and self.IsWaitingOnExtruder == state.IsWaitingOnExtruder
                and self.IsHomed == state.IsHomed):
            return True
        return False


class Trigger(object):
    def __init__(self, octolapse_settings, max_states=5):
        self.Settings = octolapse_settings
        self.Printer = Printer(self.Settings.current_printer())
        self.Snapshot = Snapshot(self.Settings.current_snapshot())

        self.Type = 'Trigger'
        self._stateHistory = []
        self._maxStates = max_states
        self.ExtruderTriggers = None
        self.TriggeredCount = 0
        self.HasRestrictedPosition = False

    def name(self):
        return self.Snapshot.name + " Trigger"

    def add_state(self, state):
        self._stateHistory.insert(0, state)
        while len(self._stateHistory) > self._maxStates:
            del self._stateHistory[self._maxStates - 1]

    def count(self):
        return len(self._stateHistory)

    def get_state(self, index):
        if self.count() > index:
            return self._stateHistory[index]
        return None

    def is_triggered(self, index):
        state = self.get_state(index)
        if state is None:
            return False
        return state.IsTriggered

    def is_in_position(self, index):
        state = self.get_state(index)
        if state is None:
            return False
        return state.IsInPosition

    def is_waiting(self, index):
        state = self.get_state(index)
        if state is None:
            return
        return state.IsWaiting

    def has_changed(self, index):
        state = self.get_state(index)
        if state is None:
            return
        return state.HasChanged

    def to_dict(self, index):
        state = self.get_state(index)
        if state is None:
            return None
        state_dict = state.to_dict(self)
        state_dict.update({"Name": self.name(), "Type": self.Type})
        return state_dict


class GcodeTriggerState(TriggerState):
    def to_dict(self, trigger):
        super_dict = super(GcodeTriggerState, self).to_dict(trigger)
        current_dict = {
            "SnapshotCommand": trigger.SnapshotCommand
        }
        current_dict.update(super_dict)
        return current_dict


class GcodeTrigger(Trigger):
    """Used to monitor gcode for a specified command."""

    def __init__(self, octolapse_settings):
        # call parent constructor
        super(GcodeTrigger, self).__init__(octolapse_settings)
        self.SnapshotCommand = GetGcodeFromString(
            self.Printer.snapshot_command)
        self.Type = "gcode"
        self.RequireZHop = self.Snapshot.gcode_trigger_require_zhop
        self.HasRestrictedPosition = len(
            self.Snapshot.gcode_trigger_position_restrictions) > 0

        self.ExtruderTriggers = ExtruderTriggers(
            self.Snapshot.gcode_trigger_on_extruding_start,
            self.Snapshot.gcode_trigger_on_extruding,
            self.Snapshot.gcode_trigger_on_primed,
            self.Snapshot.gcode_trigger_on_retracting_start,
            self.Snapshot.gcode_trigger_on_retracting,
            self.Snapshot.gcode_trigger_on_partially_retracted,
            self.Snapshot.gcode_trigger_on_retracted,
            self.Snapshot.gcode_trigger_on_detracting_start,
            self.Snapshot.gcode_trigger_on_detracting,
            self.Snapshot.gcode_trigger_on_detracted
        )

        # Logging
        message = "Creating Gcode Trigger - Gcode Command:{0}, RequireZHop:{1}"
        message = message.format(self.Printer.snapshot_command, self.Snapshot.gcode_trigger_require_zhop)
        self.Settings.current_debug_profile().log_trigger_create(message)

        message = (
            "Extruder Triggers - OnExtrudingStart:{0}, OnExtruding:{1}, OnPrimed:{2}, "
            "OnRetractingStart:{3} OnRetracting:{4}, OnPartiallyRetracted:{5}, OnRetracted:{6}, "
            "ONDetractingStart:{7}, OnDetracting:{8}, OnDetracted:{9}"
        ).format(
            self.Snapshot.gcode_trigger_on_extruding_start,
            self.Snapshot.gcode_trigger_on_extruding,
            self.Snapshot.gcode_trigger_on_primed,
            self.Snapshot.gcode_trigger_on_retracting_start,
            self.Snapshot.gcode_trigger_on_retracting,
            self.Snapshot.gcode_trigger_on_partially_retracted,
            self.Snapshot.gcode_trigger_on_retracted,
            self.Snapshot.gcode_trigger_on_detracting_start,
            self.Snapshot.gcode_trigger_on_detracting,
            self.Snapshot.gcode_trigger_on_detracted
        )
        self.Settings.current_debug_profile().log_trigger_create(message)
        # add an initial state
        self.add_state(GcodeTriggerState())

    def update(self, position, command_name):
        """If the provided command matches the trigger command, sets IsTriggered to true, else false"""
        try:
            # get the last state to use as a starting point for the update
            # if there is no state, this will return the default state
            state = self.get_state(0)
            if state is None:
                # create a new object, it's our first state!
                state = GcodeTriggerState()
            else:
                # create a copy so we aren't working on the original
                state = GcodeTriggerState(state)
            # reset any variables that must be reset each update
            state.reset_state()
            # Don't update the trigger if we don't have a homed axis
            # Make sure to use the previous value so the homing operation can complete
            if not position.has_homed_position(0):
                state.IsTriggered = False
                state.IsHomed = False
            else:
                state.IsHomed = True
                # check to see if we are in the proper position to take a snapshot
                if self.HasRestrictedPosition:
                    state.IsInPosition = is_in_position(self.Snapshot.gcode_trigger_position_restrictions,
                                                        position.x(0),
                                                        position.y(0))
                else:
                    state.IsInPosition = True

                if self.is_snapshot_command(command_name):
                    state.IsWaiting = True
                if state.IsWaiting:
                    if position.Extruder.is_triggered(self.ExtruderTriggers, index=0):
                        if self.RequireZHop and not position.is_zhop(0):
                            state.IsWaitingOnZHop = True
                            self.Settings.current_debug_profile().log_trigger_wait_state(
                                "GcodeTrigger - Waiting on ZHop.")
                        elif not self.is_in_position(0):
                            # Make sure the previous X,Y is in position
                            self.Settings.current_debug_profile().log_trigger_wait_state(
                                "GcodeTrigger - Waiting on Position.")
                        else:
                            state.IsTriggered = True
                            state.IsWaiting = False
                            state.IsWaitingOnZHop = False
                            state.IsWaitingOnExtruder = False
                            self.TriggeredCount += 1

                            self.Settings.current_debug_profile().log_triggering(
                                "GcodeTrigger - Waiting for extruder to trigger.")
                    else:
                        state.IsWaitingOnExtruder = True
                        self.Settings.current_debug_profile().log_trigger_wait_state(
                            "GcodeTrigger - Waiting for extruder to trigger.")

            # calculate changes and set the current state
            state.HasChanged = not state.is_equal(self.get_state(0))

            # add the state to the history
            self.add_state(state)
        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)

    def is_snapshot_command(self, command):
        command_name = GetGcodeFromString(command)
        return command_name == self.SnapshotCommand


class LayerTriggerState(TriggerState):
    def __init__(self, state=None):
        # call parent constructor
        super(LayerTriggerState, self).__init__()
        self.CurrentIncrement = 0 if state is None else state.CurrentIncrement
        self.IsLayerChangeWait = False if state is None else state.IsLayerChangeWait
        self.IsHeightChange = False if state is None else state.IsHeightChange
        self.IsHeightChangeWait = False if state is None else state.IsHeightChangeWait
        self.Layer = 0 if state is None else state.Layer
        self.IsLayerChange = False

    def to_dict(self, trigger):
        super_dict = super(LayerTriggerState, self).to_dict(trigger)
        current_dict = {
            "CurrentIncrement": self.CurrentIncrement,
            "IsLayerChangeWait": self.IsLayerChangeWait,
            "IsHeightChange": self.IsHeightChange,
            "IsHeightChangeWait": self.IsHeightChangeWait,
            "HeightIncrement": trigger.HeightIncrement,
            "Layer": self.Layer
        }
        current_dict.update(super_dict)
        return current_dict

    def reset_state(self):
        super(LayerTriggerState, self).reset_state()
        self.IsHeightChange = False
        self.IsLayerChange = False

    def is_equal(self, state):
        if (super(LayerTriggerState, self).is_equal(state)
                and self.CurrentIncrement == state.CurrentIncrement
                and self.IsLayerChangeWait == state.IsLayerChangeWait
                and self.IsHeightChange == state.IsHeightChange
                and self.IsHeightChangeWait == state.IsHeightChangeWait
                and self.Layer == state.Layer):
            return True
        return False


class LayerTrigger(Trigger):

    def __init__(self, octolapse_settings):
        super(LayerTrigger, self).__init__(octolapse_settings)
        self.Type = "layer"
        self.ExtruderTriggers = ExtruderTriggers(
            self.Snapshot.layer_trigger_on_extruding_start,
            self.Snapshot.layer_trigger_on_extruding,
            self.Snapshot.layer_trigger_on_primed,
            self.Snapshot.layer_trigger_on_retracting_start,
            self.Snapshot.layer_trigger_on_retracting,
            self.Snapshot.layer_trigger_on_partially_retracted,
            self.Snapshot.layer_trigger_on_retracted,
            self.Snapshot.layer_trigger_on_detracting_start,
            self.Snapshot.layer_trigger_on_detracting,
            self.Snapshot.layer_trigger_on_detracted
        )
        # Configuration Variables
        self.RequireZHop = self.Snapshot.layer_trigger_require_zhop
        self.HeightIncrement = self.Snapshot.layer_trigger_height
        if self.HeightIncrement == 0:
            self.HeightIncrement = None
        self.HasRestrictedPosition = len(
            self.Snapshot.layer_trigger_position_restrictions) > 0
        # debug output
        message = (
            "Creating Layer Trigger - TriggerHeight:{0} (none = layer change), RequiresZHop:{1}"
        ).format(
            self.Snapshot.layer_trigger_height,
            self.Snapshot.layer_trigger_require_zhop
        )
        self.Settings.current_debug_profile().log_trigger_create(message)

        message = (
            "Extruder Triggers - OnExtrudingStart:{0}, "
            "OnExtruding:{1}, OnPrimed:{2}, OnRetractingStart:{3} "
            "OnRetracting:{4}, OnPartiallyRetracted:{5}, "
            "OnRetracted:{6}, ONDetractingStart:{7}, "
            "OnDetracting:{8}, OnDetracted:{9}"
        ).format(
            self.Snapshot.layer_trigger_on_extruding_start,
            self.Snapshot.layer_trigger_on_extruding,
            self.Snapshot.layer_trigger_on_primed,
            self.Snapshot.layer_trigger_on_retracting_start,
            self.Snapshot.layer_trigger_on_retracting,
            self.Snapshot.layer_trigger_on_partially_retracted,
            self.Snapshot.layer_trigger_on_retracted,
            self.Snapshot.layer_trigger_on_detracting_start,
            self.Snapshot.layer_trigger_on_detracting,
            self.Snapshot.layer_trigger_on_detracted
        )
        self.Settings.current_debug_profile().log_trigger_create(message)
        self.add_state(LayerTriggerState())

    def update(self, position):
        """Updates the layer monitor position.  x, y and z may be absolute, but e must always be relative"""
        try:
            # get the last state to use as a starting point for the update
            # if there is no state, this will return the default state
            state = self.get_state(0)
            if state is None:
                # create a new object, it's our first state!
                state = LayerTriggerState()
            else:
                # create a copy so we aren't working on the original
                state = LayerTriggerState(state)

            # reset any variables that must be reset each update
            state.reset_state()
            # Don't update the trigger if we don't have a homed axis
            # Make sure to use the previous value so the homing operation can complete
            if not position.has_homed_position(0):
                state.IsTriggered = False
                state.IsHomed = False
            else:
                state.IsHomed = True

                # calculate height increment changed

                if (self.HeightIncrement is not None
                        and self.HeightIncrement > 0
                        and position.is_layer_change(0)
                        and state.CurrentIncrement * self.HeightIncrement <= position.height(0)):
                    state.CurrentIncrement += 1
                    state.IsHeightChange = True

                    message = (
                        "Layer Trigger - Height Increment:{0}, Current Increment"
                    ).format(self.HeightIncrement, state.CurrentIncrement)
                    self.Settings.current_debug_profile().log_trigger_height_change(message)

                # see if we've encountered a layer or height change
                if self.HeightIncrement is not None and self.HeightIncrement > 0:
                    if state.IsHeightChange:
                        state.IsHeightChangeWait = True
                        state.IsWaiting = True

                else:
                    if position.is_layer_change(0):
                        state.Layer = position.layer(0)
                        state.IsLayerChangeWait = True
                        state.IsLayerChange = True
                        state.IsWaiting = True

                # check to see if we are in the proper position to take a snapshot
                if self.HasRestrictedPosition:
                    state.IsInPosition = is_in_position(self.Snapshot.layer_trigger_position_restrictions,
                                                        position.x(0),
                                                        position.y(0))
                else:
                    state.IsInPosition = True

                # see if the extruder is triggering
                is_extruder_triggering = position.Extruder.is_triggered(
                    self.ExtruderTriggers, index=0)

                if state.IsHeightChangeWait or state.IsLayerChangeWait or state.IsWaiting:
                    state.IsWaiting = True
                    if not is_extruder_triggering:
                        state.IsWaitingOnExtruder = True
                        if state.IsHeightChangeWait:
                            self.Settings.current_debug_profile().log_trigger_wait_state(
                                "LayerTrigger - Height change triggering, waiting on extruder.")
                        elif state.IsLayerChangeWait:
                            self.Settings.current_debug_profile().log_trigger_wait_state(
                                "LayerTrigger - Layer change triggering, waiting on extruder.")
                    else:
                        if self.RequireZHop and not position.is_zhop(0):
                            state.IsWaitingOnZHop = True
                            self.Settings.current_debug_profile().log_trigger_wait_state(
                                "LayerTrigger - Triggering - Waiting on ZHop.")
                        elif not self.is_in_position(0):
                            # Make sure the previous X,Y is in position
                            self.Settings.current_debug_profile().log_trigger_wait_state(
                                "LayerTrigger - Waiting on Position.")
                        else:
                            if state.IsHeightChangeWait:
                                self.Settings.current_debug_profile().log_triggering(
                                    "LayerTrigger - Height change triggering.")
                            elif state.IsLayerChangeWait:
                                self.Settings.current_debug_profile().log_triggering(
                                    "LayerTrigger - Layer change triggering.")
                            self.TriggeredCount += 1
                            state.IsTriggered = True
                            state.IsLayerChangeWait = False
                            state.IsLayerChange = False
                            state.IsHeightChangeWait = False
                            state.IsWaiting = False
                            state.IsWaitingOnZHop = False
                            state.IsWaitingOnExtruder = False
            # calculate changes and set the current state
            state.HasChanged = not state.is_equal(self.get_state(0))
            # add the state to the history
            self.add_state(state)
        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)


class TimerTriggerState(TriggerState):
    def __init__(self, state=None):
        # call parent constructor
        super(TimerTriggerState, self).__init__()
        self.SecondsToTrigger = None if state is None else state.SecondsToTrigger
        self.TriggerStartTime = None if state is None else state.TriggerStartTime
        self.PauseTime = None if state is None else state.PauseTime

    def to_dict(self, trigger):
        super_dict = super(TimerTriggerState, self).to_dict(trigger)
        current_dict = {
            "SecondsToTrigger": self.SecondsToTrigger,
            "TriggerStartTime": self.TriggerStartTime,
            "PauseTime": self.PauseTime,
            "IntervalSeconds": trigger.IntervalSeconds
        }
        current_dict.update(super_dict)
        return current_dict

    def is_equal(self, state):
        if (super(TimerTriggerState, self).is_equal(state)
                and self.SecondsToTrigger == state.SecondsToTrigger
                and self.TriggerStartTime == state.TriggerStartTime
                and self.PauseTime == state.PauseTime):
            return True
        return False


class TimerTrigger(Trigger):

    def __init__(self, octolapse_settings):
        super(TimerTrigger, self).__init__(octolapse_settings)
        self.Type = "timer"
        self.ExtruderTriggers = ExtruderTriggers(
            self.Snapshot.timer_trigger_on_extruding_start,
            self.Snapshot.timer_trigger_on_extruding,
            self.Snapshot.timer_trigger_on_primed,
            self.Snapshot.timer_trigger_on_retracting_start,
            self.Snapshot.timer_trigger_on_retracting,
            self.Snapshot.timer_trigger_on_partially_retracted,
            self.Snapshot.timer_trigger_on_retracted,
            self.Snapshot.timer_trigger_on_detracting_start,
            self.Snapshot.timer_trigger_on_detracting,
            self.Snapshot.timer_trigger_on_detracted
        )
        self.IntervalSeconds = self.Snapshot.timer_trigger_seconds
        self.RequireZHop = self.Snapshot.timer_trigger_require_zhop
        self.HasRestrictedPosition = len(
            self.Snapshot.timer_trigger_position_restrictions) > 0

        # Log output
        message = (
            "Creating Timer Trigger - Seconds:{0}, RequireZHop:{1}"
        ).format(
            self.Snapshot.timer_trigger_seconds,
            self.Snapshot.timer_trigger_require_zhop
        )
        self.Settings.current_debug_profile().log_trigger_create(message)

        message = (
            "Extruder Triggers - OnExtrudingStart:{0}, "
            "OnExtruding:{1}, OnPrimed:{2}, OnRetractingStart:{3} "
            "OnRetracting:{4}, OnPartiallyRetracted:{5}, "
            "OnRetracted:{6}, ONDetractingStart:{7}, "
            "OnDetracting:{8}, OnDetracted:{9}"
        ).format(
            self.Snapshot.timer_trigger_on_extruding_start,
            self.Snapshot.timer_trigger_on_extruding,
            self.Snapshot.timer_trigger_on_primed,
            self.Snapshot.timer_trigger_on_retracting_start,
            self.Snapshot.timer_trigger_on_retracting,
            self.Snapshot.timer_trigger_on_partially_retracted,
            self.Snapshot.timer_trigger_on_retracted,
            self.Snapshot.timer_trigger_on_detracting_start,
            self.Snapshot.timer_trigger_on_detracting,
            self.Snapshot.timer_trigger_on_detracted
        )

        self.Settings.current_debug_profile().log_trigger_create(message)
        # add initial state
        initial_state = TimerTriggerState()
        self.add_state(initial_state)

    def pause(self):
        try:
            state = self.get_state(0)
            if state is None:
                return
            state.PauseTime = time.time()
        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)

    def resume(self):
        try:
            state = self.get_state(0)
            if state is None:
                return
            if state.PauseTime is not None and state.TriggerStartTime is not None:
                current_time = time.time()
                new_last_trigger_time = current_time - \
                    (state.PauseTime - state.TriggerStartTime)
                message = (
                    "Time Trigger - Unpausing.  LastTriggerTime:{0}, "
                    "PauseTime:{1}, CurrentTime:{2}, NewTriggerTime:{3}"
                ).format(
                    state.TriggerStartTime,
                    state.PauseTime, current_time,
                    new_last_trigger_time
                )
                self.Settings.current_debug_profile().log_timer_trigger_unpaused(message)
                # Keep the proper interval if the print is paused
                state.TriggerStartTime = new_last_trigger_time
                state.PauseTime = None
        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)

    def update(self, position):
        try:
            # get the last state to use as a starting point for the update
            # if there is no state, this will return the default state
            state = self.get_state(0)
            if state is None:
                # create a new object, it's our first state!
                state = TimerTriggerState()
            else:
                # create a copy so we aren't working on the original
                state = TimerTriggerState(state)
            # reset any variables that must be reset each update
            state.reset_state()
            state.IsTriggered = False

            # Don't update the trigger if we don't have a homed axis
            # Make sure to use the previous value so the homing operation can complete
            if not position.has_homed_position(0):
                state.IsTriggered = False
                state.IsHomed = False
            else:
                state.IsHomed = True

                # record the current time to keep things consistant
                current_time = time.time()

                # if the trigger start time is null, set it now.
                if state.TriggerStartTime is None:
                    state.TriggerStartTime = current_time

                message = (
                    "TimerTrigger - {0} second interval, "
                    "{1} seconds elapsed, {2} seconds to trigger"
                ).format(
                    self.IntervalSeconds,
                    int(current_time - state.TriggerStartTime),
                    int(self.IntervalSeconds - (current_time - state.TriggerStartTime))
                )
                self.Settings.current_debug_profile().log_trigger_time_remaining(message)

                # how many seconds to trigger
                seconds_to_trigger = self.IntervalSeconds - \
                    (current_time - state.TriggerStartTime)
                state.SecondsToTrigger = utility.round_to(seconds_to_trigger, 1)

                # check to see if the X/Y axes are in the proper position to take a snapshot
                if self.HasRestrictedPosition:
                    state.IsInPosition = is_in_position(self.Snapshot.timer_trigger_position_restrictions,
                                                        position.x(0),
                                                        position.y(0))
                else:
                    state.IsInPosition = True

                # see if enough time has elapsed since the last trigger
                if state.SecondsToTrigger <= 0:
                    state.IsWaiting = True

                    # see if the exturder is in the right position
                    if position.Extruder.is_triggered(self.ExtruderTriggers, index=0):
                        if self.RequireZHop and not position.is_zhop(0):
                            self.Settings.current_debug_profile().log_trigger_wait_state(
                                "TimerTrigger - Waiting on ZHop.")
                            state.IsWaitingOnZHop = True
                        elif not self.is_in_position(0):
                            # Make sure the previous X,Y is in position
                            self.Settings.current_debug_profile().log_trigger_wait_state(
                                "TimerTrigger - Waiting on Position.")
                        else:
                            # Is Triggering
                            self.TriggeredCount += 1
                            state.IsTriggered = True
                            state.IsWaiting = False
                            state.TriggerStartTime = None
                            state.IsWaitingOnZHop = False
                            state.IsWaitingOnExtruder = False
                            # Log trigger
                            self.Settings.current_debug_profile().log_triggering('TimerTrigger - Triggering.')

                    else:
                        self.Settings.current_debug_profile().log_trigger_wait_state(
                            'TimerTrigger - Triggering, waiting for extruder')
                        state.IsWaitingOnExtruder = True
            # calculate changes and set the current state
            state.HasChanged = not state.is_equal(self.get_state(0))
            # add the state to the history
            self.add_state(state)
        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)
