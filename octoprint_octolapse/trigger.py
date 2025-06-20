# coding=utf-8
##################################################################################
# Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
# Copyright (C) 2023  Brad Hochgesang
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
from __future__ import unicode_literals
import time
from octoprint_octolapse.position import ExtruderTriggers
from octoprint_octolapse.settings import *

# create the module level logger
from octoprint_octolapse.log import LoggingConfigurator
logging_configurator = LoggingConfigurator()
logger = logging_configurator.get_logger(__name__)


class Triggers(object):
    TRIGGER_TYPE_DEFAULT = 'default'
    TRIGGER_TYPE_IN_PATH = 'in-path'

    def __init__(self, settings):
        self._triggers = []
        self.reset()
        self._settings = settings
        self.name = "Unknown"

    def count(self):
        return len(self._triggers)

    def reset(self):
        self._triggers = []

    def create(self):
        self.reset()
        trigger_profile = self._settings.profiles.current_trigger()
        self.name = trigger_profile.name
        # create the triggers
        # If the gcode trigger is enabled, add it
        if trigger_profile.trigger_subtype == TriggerProfile.GCODE_TRIGGER_TYPE:
            # Add the trigger to the list
            self._triggers.append(GcodeTrigger(self._settings))
        # If the layer trigger is enabled, add it
        elif trigger_profile.trigger_subtype == TriggerProfile.LAYER_TRIGGER_TYPE:
            self._triggers.append(LayerTrigger(self._settings))
        # If the layer trigger is enabled, add it
        elif trigger_profile.trigger_subtype == TriggerProfile.TIMER_TRIGGER_TYPE:
            self._triggers.append(TimerTrigger(self._settings))

    def resume(self):
        for trigger in self._triggers:
            if type(trigger) == TimerTrigger:
                trigger.resume()

    def pause(self):
        for trigger in self._triggers:
            if type(trigger) == TimerTrigger:
                trigger.pause()

    def update(self, position):
        # the previous command (not just the current) MUST have homed positions else
        # we may have some null coordinates.
        #if not position.current_pos.has_definite_position:
        #    return
        ## Note:  I think we need to add waits to handle the above
        """Update all triggers and return any that are triggering"""
        try:
            # Loop through all of the active current_triggers
            for current_trigger in self._triggers:
                # determine what type the current trigger is and update appropriately
                if isinstance(current_trigger, GcodeTrigger):
                    current_trigger.update(position)
                elif isinstance(current_trigger, TimerTrigger):
                    current_trigger.update(position)
                elif isinstance(current_trigger, LayerTrigger):
                    current_trigger.update(position)
                # see if the current trigger is triggering, indicting that a snapshot should be taken
        except Exception as e:
            logger.exception("Failed to update the snapshot triggers.")

        return None

    def get_first_triggering(self, index, trigger_type):
        if len(self._triggers) < 1:
            return False
        # Loop through all of the active current_triggers
        for current_trigger in self._triggers:
            current_triggereing_state = current_trigger.get_state(index)
            if (
                current_triggereing_state.is_triggered and
                current_triggereing_state.trigger_type == trigger_type
            ):
                return current_trigger

        return False

    def get_first_waiting(self):
       # Loop through all of the active current_triggers
        for current_trigger in self._triggers:
            if current_trigger.is_waiting(0):
                return current_trigger

    def has_changed(self):
        # Loop through all of the active current_triggers
        for current_trigger in self._triggers:
            if current_trigger.has_changed(0):
                return True
        return False

    def state_to_list(self):
        state_list = []
        # Loop through all of the active current_triggers
        for current_trigger in self._triggers:
            state_list.append(current_trigger.to_dict(0))

        return state_list

    def changes_to_list(self):
        change_list = []
        # Loop through all of the active current_triggers
        for current_trigger in self._triggers:
            if current_trigger.has_changed(0):
                change_list.append(current_trigger.to_dict(0))

        return change_list


class TriggerState(object):
    def __init__(self, state=None):
        self.is_triggered = False if state is None else state.is_triggered
        self.trigger_type = None if state is None else state.trigger_type
        self.is_in_position = False if state is None else state.is_in_position
        self.in_path_position = False if state is None else state.in_path_position
        self.is_waiting = False if state is None else state.is_waiting
        self.is_home_position_wait = False if state is None else state.is_home_position_wait
        self.is_waiting_on_zhop = False if state is None else state.is_waiting_on_zhop
        self.is_waiting_on_extruder = False if state is None else state.is_waiting_on_extruder
        self.has_changed = False if state is None else state.has_changed
        self.has_definite_position = False if state is None else state.has_definite_position

    def to_dict(self, trigger):
        return {
            "is_triggered": self.is_triggered,
            "trigger_type": self.trigger_type,
            "in_path_position": self.in_path_position,
            "is_in_position": self.is_in_position,
            "is_waiting": self.is_waiting,
            "is_home_position_wait": self.is_home_position_wait,
            "is_waiting_on_zhop": self.is_waiting_on_zhop,
            "is_waiting_on_extruder": self.is_waiting_on_extruder,
            "has_changed": self.has_changed,
            "require_zhop": trigger.require_zhop,
            "has_definite_position": self.has_definite_position,
            "trigger_count": trigger.trigger_count
        }

    def reset_state(self):
        self.is_triggered = False
        self.in_path_position = False
        self.is_in_position = False
        self.trigger_type = None
        self.has_changed = False

    def is_equal(self, state):
        if (state is not None
                and self.is_triggered == state.is_triggered
                and self.trigger_type == state.trigger_type
                and self.is_in_position == state.is_in_position
                and self.in_path_position == state.in_path_position
                and self.is_waiting == state.is_waiting
                and self.is_home_position_wait == state.is_home_position_wait
                and self.is_waiting_on_zhop == state.is_waiting_on_zhop
                and self.is_waiting_on_extruder == state.is_waiting_on_extruder
                and self.has_definite_position == state.has_definite_position):
            return True
        return False


class Trigger(object):

    def __init__(self, octolapse_settings, max_states=5):
        self._settings = octolapse_settings
        self.printer = self._settings.profiles.current_printer()
        self.trigger_profile = self._settings.profiles.current_trigger()
        self.type = 'Trigger'
        self._state_history = []
        self._max_states = max_states
        self.extruder_triggers = None
        self.trigger_count = 0
        self.snapshots_enabled = True

    def update(self, position):
        parsed_command = position.current_pos.parsed_command
        if parsed_command.is_octolapse_command:
            if "STOP-SNAPSHOTS" in parsed_command.parameters:
                self.snapshots_enabled = False
            elif "START-SNAPSHOTS" in parsed_command.parameters:
                self.snapshots_enabled = True

    def name(self):
        return self.trigger_profile.name + " Trigger"

    def add_state(self, state):
        self._state_history.insert(0, state)
        while len(self._state_history) > self._max_states:
            del self._state_history[self._max_states - 1]

    def count(self):
        return len(self._state_history)

    def get_state(self, index):
        if self.count() > index:
            return self._state_history[index]
        return None

    def is_triggered(self, index):
        state = self.get_state(index)
        if state is None:
            return False
        return state.is_triggered

    def triggered_type(self, index):
        state = self.get_state(index)
        if state is None:
            return None
        return state.trigger_type

    def in_path_position(self, index):
        state = self.get_state(index)
        if state is None:
            return None
        return state.in_path_position

    def is_waiting(self, index):
        state = self.get_state(index)
        if state is None:
            return
        return state.is_waiting

    def has_changed(self, index):
        state = self.get_state(index)
        if state is None:
            return
        return state.has_changed

    def to_dict(self, index):
        state = self.get_state(index)
        if state is None:
            return None
        state_dict = state.to_dict(self)
        state_dict.update({"name": self.name(), "type": self.type})
        return state_dict


class GcodeTriggerState(TriggerState):
    def to_dict(self, trigger):
        super_dict = super(GcodeTriggerState, self).to_dict(trigger)
        current_dict = {
            "snapshot_command": trigger.snapshot_command
        }
        current_dict.update(super_dict)
        return current_dict


class GcodeTrigger(Trigger):
    """Used to monitor gcode for a specified command."""

    def __init__(self, octolapse_settings):
        # call parent constructor
        super(GcodeTrigger, self).__init__(octolapse_settings)
        self.type = "gcode"
        self.require_zhop = self.trigger_profile.require_zhop
        self.snapshot_command = octolapse_settings.profiles.current_printer().snapshot_command
        if self.trigger_profile.extruder_state_requirements_enabled:
            self.extruder_triggers = ExtruderTriggers(
                self.trigger_profile.trigger_on_extruding_start,
                self.trigger_profile.trigger_on_extruding,
                self.trigger_profile.trigger_on_primed,
                self.trigger_profile.trigger_on_retracting_start,
                self.trigger_profile.trigger_on_retracting,
                self.trigger_profile.trigger_on_partially_retracted,
                self.trigger_profile.trigger_on_retracted,
                self.trigger_profile.trigger_on_deretracting_start,
                self.trigger_profile.trigger_on_deretracting,
                self.trigger_profile.trigger_on_deretracted
            )
            message = (
                "Extruder Triggers - on_extruding_start:%s, on_extruding:%s, on_primed:%s, "
                "on_retracting_start:%s on_retracting:%s, on_partially_retracted:%s, on_retracted:%s, "
                "ONDeretractingStart:%s, on_deretracting:%s, on_deretracted:%s"
            )
            logger.debug(
                message,
                self.trigger_profile.trigger_on_extruding_start,
                self.trigger_profile.trigger_on_extruding,
                self.trigger_profile.trigger_on_primed,
                self.trigger_profile.trigger_on_retracting_start,
                self.trigger_profile.trigger_on_retracting,
                self.trigger_profile.trigger_on_partially_retracted,
                self.trigger_profile.trigger_on_retracted,
                self.trigger_profile.trigger_on_deretracting_start,
                self.trigger_profile.trigger_on_deretracting,
                self.trigger_profile.trigger_on_deretracted
            )

        # Logging
        message = "Creating Gcode Trigger - Gcode Command:%s, require_zhop:%s"
        logger.info(
            message,
            self.snapshot_command,
            self.trigger_profile.require_zhop
        )

        # add an initial state
        self.add_state(GcodeTriggerState())

    def update(self, position):
        super(GcodeTrigger, self).update(position)
        parsed_command = position.current_pos.parsed_command
        """If the provided command matches the trigger command, sets is_triggered to true, else false"""
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

            # set the trigger position.  It should be the previous position, not the current
            trigger_position = position.previous_pos

            # Don't update the trigger if we don't have a homed axis
            if not trigger_position.has_definite_position:
                state.is_triggered = False
                state.has_definite_position = False
            else:
                state.has_definite_position = trigger_position.has_definite_position
                # check to see if we are in the proper position to take a snapshot

                # set is in position
                state.is_in_position = trigger_position.is_in_position and trigger_position.is_in_bounds
                state.in_path_position = position.current_pos.in_path_position

                if self.printer.is_snapshot_command(parsed_command.gcode):
                    if self.snapshots_enabled:
                        state.is_waiting = True
                    else:
                        logger.info("GcodeTrigger - A snapshot was detected, but snapshots were disabled via "
                                    "@Octolapse stop-snapshots.")
                if state.is_waiting:
                    if position.is_previous_extruder_triggered(self.extruder_triggers):
                        if not trigger_position.has_definite_position:
                            state.is_waiting_for_definite_position = True
                            logger.debug("GcodeTrigger - Triggering - Waiting for a definite previous position.")
                        elif self.require_zhop and not trigger_position.is_zhop:
                            state.is_waiting_on_zhop = True
                            logger.debug("GcodeTrigger - Waiting on ZHop.")
                        elif not trigger_position.is_in_bounds:
                            logger.debug("GcodeTrigger - Waiting for in-bounds position.")
                        elif not state.is_in_position and not state.in_path_position:
                            # Make sure the previous X,Y is in position
                            logger.debug("GcodeTrigger - Waiting on Position.")
                        elif not trigger_position.last_extrusion_height:
                            logger.debug(
                                "GcodeTrigger - Waiting for at least one extrusion on a previous layer."
                            )
                        elif not utility.greater_than_or_equal(
                                trigger_position.z, trigger_position.last_extrusion_height
                        ):
                            # The extruder is below the last extrusion height, do not take a snapshot else we might
                            # run into the part!
                            logger.debug(
                                "GcodeTrigger - Waiting for extruder to move above the highest extrusion point."
                            )
                        elif not self.snapshots_enabled:
                            # Snapshot have been disabled by an octolapse gcode command
                            logger.debug(
                                "GcodeTrigger - Waiting for snapshots to be enabled via @Octolapse start-snapshots "
                                "command. "
                            )
                        else:
                            state.is_triggered = True
                            self.trigger_count += 1
                            if state.is_in_position:
                                state.trigger_type = Triggers.TRIGGER_TYPE_DEFAULT
                            elif state.in_path_position:
                                state.trigger_type = Triggers.TRIGGER_TYPE_IN_PATH
                            else:
                                state.trigger_type = None

                            state.is_waiting = False
                            state.is_waiting_on_zhop = False
                            state.is_waiting_on_extruder = False
                            logger.debug("GcodeTrigger - Waiting for extruder to trigger.")
                    else:
                        state.is_waiting_on_extruder = True
                        logger.debug("GcodeTrigger - Waiting for extruder to trigger.")

            # calculate changes and set the current state
            state.has_changed = not state.is_equal(self.get_state(0))

            # add the state to the history
            self.add_state(state)
        except Exception as e:
            logger.exception("Failed to update the gcode trigger.")


class LayerTriggerState(TriggerState):
    def __init__(self, state=None):
        # call parent constructor
        super(LayerTriggerState, self).__init__()
        self.current_increment = 0 if state is None else state.current_increment
        self.is_layer_change_wait = False if state is None else state.is_layer_change_wait
        self.is_height_change = False if state is None else state.is_height_change
        self.is_height_change_wait = False if state is None else state.is_height_change_wait
        self.layer = 0 if state is None else state.layer
        self.is_layer_change = False

    def to_dict(self, trigger):
        super_dict = super(LayerTriggerState, self).to_dict(trigger)
        current_dict = {
            "current_increment": self.current_increment,
            "is_layer_change_wait": self.is_layer_change_wait,
            "is_height_change": self.is_height_change,
            "is_height_change_wait": self.is_height_change_wait,
            "height_increment": trigger.height_increment,
            "Layer": self.layer
        }
        current_dict.update(super_dict)
        return current_dict

    def reset_state(self):
        super(LayerTriggerState, self).reset_state()
        self.is_height_change = False
        self.is_layer_change = False

    def is_equal(self, state):
        if (super(LayerTriggerState, self).is_equal(state)
                and self.is_home_position_wait == state.is_home_position_wait
                and self.current_increment == state.current_increment
                and self.is_layer_change_wait == state.is_layer_change_wait
                and self.is_height_change == state.is_height_change
                and self.is_height_change_wait == state.is_height_change_wait
                and self.layer == state.layer):
            return True
        return False


class LayerTrigger(Trigger):

    def __init__(self, octolapse_settings):
        super(LayerTrigger, self).__init__(octolapse_settings)
        self.type = "layer"
        if self.trigger_profile.extruder_state_requirements_enabled:
            self.extruder_triggers = ExtruderTriggers(
                TriggerProfile.get_extruder_trigger_value(self.trigger_profile.trigger_on_extruding_start),
                TriggerProfile.get_extruder_trigger_value(self.trigger_profile.trigger_on_extruding),
                TriggerProfile.get_extruder_trigger_value(self.trigger_profile.trigger_on_primed),
                TriggerProfile.get_extruder_trigger_value(self.trigger_profile.trigger_on_retracting_start),
                TriggerProfile.get_extruder_trigger_value(self.trigger_profile.trigger_on_retracting),
                TriggerProfile.get_extruder_trigger_value(self.trigger_profile.trigger_on_partially_retracted),
                TriggerProfile.get_extruder_trigger_value(self.trigger_profile.trigger_on_retracted),
                TriggerProfile.get_extruder_trigger_value(self.trigger_profile.trigger_on_deretracting_start),
                TriggerProfile.get_extruder_trigger_value(self.trigger_profile.trigger_on_deretracting),
                TriggerProfile.get_extruder_trigger_value(self.trigger_profile.trigger_on_deretracted)
            )
            message = (
                "Extruder Triggers - on_extruding_start:%s, "
                "on_extruding:%s, on_primed:%s, on_retracting_start:%s "
                "on_retracting:%s, on_partially_retracted:%s, "
                "on_retracted:%s, ONDeretractingStart:%s, "
                "on_deretracting:%s, on_deretracted:%s"
            )
            logger.info(
                message,
                self.trigger_profile.trigger_on_extruding_start,
                self.trigger_profile.trigger_on_extruding,
                self.trigger_profile.trigger_on_primed,
                self.trigger_profile.trigger_on_retracting_start,
                self.trigger_profile.trigger_on_retracting,
                self.trigger_profile.trigger_on_partially_retracted,
                self.trigger_profile.trigger_on_retracted,
                self.trigger_profile.trigger_on_deretracting_start,
                self.trigger_profile.trigger_on_deretracting,
                self.trigger_profile.trigger_on_deretracted
            )
        # Configuration Variables
        self.require_zhop = self.trigger_profile.require_zhop
        self.height_increment = self.trigger_profile.layer_trigger_height
        if self.height_increment == 0:
            self.height_increment = None
        # debug output
        message = (
            "Creating Layer Trigger - TriggerHeight:%s (none = layer change), RequiresZHop:%s"
        )
        logger.info(
            message,
            self.trigger_profile.layer_trigger_height,
            self.trigger_profile.require_zhop
        )
        self.add_state(LayerTriggerState())

    def update(self, position):
        """Updates the layer monitor position.  x, y and z may be absolute, but e must always be relative"""
        super(LayerTrigger, self).update(position)
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

            # set the trigger position.  It should be the previous position, not the current
            trigger_position = position.previous_pos
            # Don't update the trigger if we don't have a homed axis
            if not trigger_position.has_definite_position:
                state.is_triggered = False
                state.has_definite_position = False
            else:
                state.has_definite_position = True

                # set is in position
                state.is_in_position = trigger_position.is_in_position and trigger_position.is_in_bounds
                # the in path position will be our CURRENT POSITION not the trigger position
                # (which is the previous position)
                state.in_path_position = position.current_pos.in_path_position

                # calculate height increment changed
                if (
                    self.height_increment is not None
                    and self.height_increment > 0
                    and position.current_pos.is_layer_change
                    and (
                        state.current_increment * self.height_increment < trigger_position.height or
                        state.current_increment == 0
                    )
                ):

                    new_increment = int(math.ceil(trigger_position.height/self.height_increment))

                    if new_increment <= state.current_increment:
                        message = (
                            "Layer Trigger - Warning - The height increment was expected to increase, but it did not."
                            " Height Increment:%s, Current Increment:%s, Calculated Increment:%s"
                        )
                        logger.warning(
                            message,
                            self.height_increment,
                            state.current_increment,
                            new_increment
                        )
                    else:
                        state.current_increment = new_increment
                        # if the current increment is below one here, set it to one.  This is not normal, but can happen
                        # if extrusion is detected at height 0.
                        if state.current_increment < 1:
                            state.current_increment = 1

                        state.is_height_change = True
                        logger.info(
                            "Layer Trigger - Height Increment:%s, Current Increment:%s, Height: %s",
                            self.height_increment,
                            state.current_increment,
                            trigger_position.height
                        )

                # see if we've encountered a layer or height change
                if self.height_increment is not None and self.height_increment > 0:
                    if state.is_height_change:
                        state.is_height_change_wait = True
                        state.is_waiting = True

                else:
                    # see if the CURRENT position is a layer change
                    if position.current_pos.is_layer_change:
                        state.layer = trigger_position.layer
                        state.is_layer_change_wait = True
                        state.is_layer_change = True
                        state.is_waiting = True

                if state.is_height_change_wait or state.is_layer_change_wait or state.is_waiting:
                    state.is_waiting = True
                    # see if the extruder is triggering
                    is_extruder_triggering = position.is_previous_extruder_triggered(self.extruder_triggers)
                    if not is_extruder_triggering:
                        state.is_waiting_on_extruder = True
                        if state.is_height_change_wait:
                            logger.debug("LayerTrigger - Height change triggering, waiting on extruder.")
                        elif state.is_layer_change_wait:
                            logger.debug("LayerTrigger - Layer change triggering, waiting on extruder.")
                    else:
                        if not trigger_position.has_definite_position:
                            state.is_waiting_for_definite_position = True
                            logger.debug("LayerTrigger - Triggering - Waiting for a definite previous position.")
                        elif self.require_zhop and not trigger_position.is_zhop:
                            state.is_waiting_on_zhop = True
                            logger.debug("LayerTrigger - Triggering - Waiting on ZHop.")
                        elif not trigger_position.is_in_bounds:
                            logger.debug("GcodeTrigger - Waiting for in-bounds position.")
                        elif not state.is_in_position and not state.in_path_position:
                            # Make sure the previous X,Y is in position
                            logger.debug("LayerTrigger - Waiting on Position.")
                        elif not trigger_position.last_extrusion_height:
                            # this should never be hit, but just in case!
                            logger.debug(
                                "LayerTrigger - Waiting for at least one extrusion on a previous layer."
                            )
                        elif utility.less_than(
                            trigger_position.z, trigger_position.last_extrusion_height
                        ):
                        # The extruder is below the last extrusion height, do not take a snapshot else we might
                        # run into the part!
                            logger.debug(
                                "LayerTrigger - Waiting for extruder to move above the highest extrusion point."
                            )
                        elif not self.snapshots_enabled:
                            # Snapshot have been disabled by an octolapse gcode command
                            logger.debug(
                                "LayerTrigger - Waiting for snapshots to be enabled via @Octolapse start-snapshots "
                                "command. "
                            )
                        else:
                            if state.is_height_change_wait:
                                logger.debug("LayerTrigger - Height change triggering.")
                            elif state.is_layer_change_wait:
                                logger.debug("LayerTrigger - Layer change triggering.")

                            self.trigger_count += 1
                            # set the trigger type
                            if state.is_in_position:
                                state.trigger_type = Triggers.TRIGGER_TYPE_DEFAULT
                            elif state.in_path_position:
                                state.trigger_type = Triggers.TRIGGER_TYPE_IN_PATH
                            else:
                                state.trigger_type = None

                            state.is_triggered = True
                            state.is_layer_change_wait = False
                            state.is_layer_change = False
                            state.is_height_change_wait = False
                            state.is_waiting = False
                            state.is_waiting_on_zhop = False
                            state.is_waiting_on_extruder = False
            # calculate changes and set the current state
            state.has_changed = not state.is_equal(self.get_state(0))
            # add the state to the history
            self.add_state(state)
        except Exception as e:
            logger.exception("Failed to update the layer trigger")


class TimerTriggerState(TriggerState):
    def __init__(self, state=None):
        # call parent constructor
        super(TimerTriggerState, self).__init__()
        self.seconds_to_trigger = None if state is None else state.seconds_to_trigger
        self.trigger_start_time = None if state is None else state.trigger_start_time
        self.pause_time = None if state is None else state.pause_time

    def to_dict(self, trigger):
        super_dict = super(TimerTriggerState, self).to_dict(trigger)
        current_dict = {
            "seconds_to_trigger": self.seconds_to_trigger,
            "trigger_start_time": self.trigger_start_time,
            "pause_time": self.pause_time,
            "interval_seconds": trigger.interval_seconds
        }
        current_dict.update(super_dict)
        return current_dict

    def is_equal(self, state):
        if (super(TimerTriggerState, self).is_equal(state)
                and self.seconds_to_trigger == state.seconds_to_trigger
                and self.trigger_start_time == state.trigger_start_time
                and self.pause_time == state.pause_time):
            return True
        return False


class TimerTrigger(Trigger):

    def __init__(self, octolapse_settings):
        super(TimerTrigger, self).__init__(octolapse_settings)
        self.type = "timer"
        if self.trigger_profile.extruder_state_requirements_enabled:
            self.extruder_triggers = ExtruderTriggers(
                self.trigger_profile.trigger_on_extruding_start,
                self.trigger_profile.trigger_on_extruding,
                self.trigger_profile.trigger_on_primed,
                self.trigger_profile.trigger_on_retracting_start,
                self.trigger_profile.trigger_on_retracting,
                self.trigger_profile.trigger_on_partially_retracted,
                self.trigger_profile.trigger_on_retracted,
                self.trigger_profile.trigger_on_deretracting_start,
                self.trigger_profile.trigger_on_deretracting,
                self.trigger_profile.trigger_on_deretracted
            )
            message = (
                "Extruder Triggers - on_extruding_start:%s, "
                "on_extruding:%s, on_primed:%s, on_retracting_start:%s "
                "on_retracting:%s, on_partially_retracted:%s, "
                "on_retracted:%s, ONDeretractingStart:%s, "
                "on_deretracting:%s, on_deretracted:%s"
            )
            logger.info(
                message,
                self.trigger_profile.trigger_on_extruding_start,
                self.trigger_profile.trigger_on_extruding,
                self.trigger_profile.trigger_on_primed,
                self.trigger_profile.trigger_on_retracting_start,
                self.trigger_profile.trigger_on_retracting,
                self.trigger_profile.trigger_on_partially_retracted,
                self.trigger_profile.trigger_on_retracted,
                self.trigger_profile.trigger_on_deretracting_start,
                self.trigger_profile.trigger_on_deretracting,
                self.trigger_profile.trigger_on_deretracted
            )

        self.interval_seconds = self.trigger_profile.timer_trigger_seconds
        self.require_zhop = self.trigger_profile.require_zhop

        # Log output
        message = (
            "Creating Timer Trigger - Seconds:%s, require_zhop:%s"
        )
        logger.info(
            message,
            self.trigger_profile.timer_trigger_seconds,
            self.trigger_profile.require_zhop
        )

        # add initial state
        initial_state = TimerTriggerState()
        self.add_state(initial_state)

    def pause(self):
        state = self.get_state(0)
        if state is None:
            return
        state.pause_time = time.time()
        logger.info("Timer trigger paused.")

    def resume(self):
        state = self.get_state(0)
        if state is None:
            return
        if state.pause_time is not None and state.trigger_start_time is not None:
            current_time = time.time()
            new_last_trigger_time = current_time - \
                (state.pause_time - state.trigger_start_time)
            message = (
                "Time Trigger - Unpausing.  LastTriggerTime:%s, "
                "pause_time:%s, CurrentTime:%s, NewTriggerTime:%s"
            )
            logger.info(
                message,
                state.trigger_start_time,
                state.pause_time, current_time,
                new_last_trigger_time
            )
            # Keep the proper interval if the print is paused
            state.trigger_start_time = new_last_trigger_time
            state.pause_time = None

    def update(self, position):
        super(TimerTrigger, self).update(position)
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
            state.is_triggered = False

            # set the trigger position.  It should be the previous position, not the current
            trigger_position = position.previous_pos
            # Don't update the trigger if we don't have a homed axis
            if not trigger_position.has_definite_position:
                state.is_triggered = False
                state.has_definite_position = False
            else:
                state.has_definite_position = True

                # record the current time to keep things consistant
                current_time = time.time()

                # set is in position
                state.is_in_position = trigger_position.is_in_position and trigger_position.is_in_bounds
                state.in_path_position = position.current_pos.in_path_position

                # if the trigger start time is null, set it now.
                if state.trigger_start_time is None:
                    state.trigger_start_time = current_time

                message = (
                    "TimerTrigger - %s second interval, "
                    "%s seconds elapsed, %s seconds to trigger"
                )
                logger.debug(
                    message,
                    self.interval_seconds,
                    int(current_time - state.trigger_start_time),
                    int(self.interval_seconds - (current_time - state.trigger_start_time))
                )

                # how many seconds to trigger
                seconds_to_trigger = self.interval_seconds - \
                    (current_time - state.trigger_start_time)
                state.seconds_to_trigger = utility.round_to(seconds_to_trigger, 1)

                # see if enough time has elapsed since the last trigger
                if state.seconds_to_trigger <= 0:
                    state.is_waiting = True

                    # see if the exturder is in the right position
                    if position.is_previous_extruder_triggered(self.extruder_triggers):
                        if not trigger_position.has_definite_position:
                            state.is_waiting_for_definite_position = True
                            logger.debug("TimerTrigger - Triggering - Waiting for a definite previous position.")
                        if self.require_zhop and not trigger_position.is_zhop:
                            logger.debug("TimerTrigger - Waiting on ZHop.")
                            state.is_waiting_on_zhop = True
                        elif not trigger_position.is_in_bounds:
                            logger.debug("TimerTrigger - Waiting for in-bounds position.")
                        elif not state.is_in_position and not state.in_path_position:
                            # Make sure the previous X,Y is in position
                            logger.debug("TimerTrigger - Waiting on Position.")
                        elif not trigger_position.last_extrusion_height:
                            logger.debug(
                                "TimerTrigger - Waiting for at least one extrusion on a previous layer."
                            )
                        elif not utility.greater_than_or_equal(
                            trigger_position.z, trigger_position.last_extrusion_height
                        ):
                        # The extruder is below the last extrusion height, do not take a snapshot else we might
                        # run into the part!
                            logger.debug(
                                "TimerTrigger - Waiting for extruder to move above the highest extrusion point."
                            )
                        elif not self.snapshots_enabled:
                            # Snapshot have been disabled by an octolapse gcode command
                            logger.debug(
                                "TimerTrigger - Waiting for snapshots to be enabled via @Octolapse start-snapshots "
                                "command. "
                            )
                        else:
                            # Is Triggering
                            self.trigger_count += 1
                            state.is_triggered = True
                            # set the trigger teyp
                            if state.is_in_position:
                                state.trigger_type = Triggers.TRIGGER_TYPE_DEFAULT
                                state.is_in_position = True
                            elif state.in_path_position:
                                state.trigger_type = Triggers.TRIGGER_TYPE_IN_PATH
                            else:
                                state.trigger_type = None

                            state.is_waiting = False
                            state.trigger_start_time = None
                            state.is_waiting_on_zhop = False
                            state.is_waiting_on_extruder = False
                            # Log trigger
                            logger.info('TimerTrigger - Triggering.')

                    else:
                        logger.debug('TimerTrigger - Triggering, waiting for extruder')
                        state.is_waiting_on_extruder = True
            # calculate changes and set the current state
            state.has_changed = not state.is_equal(self.get_state(0))
            # add the state to the history
            self.add_state(state)
        except Exception as e:
            logger.excetion("Failed to update the timer trigger")
