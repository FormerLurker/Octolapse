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
import octoprint_octolapse.utility as utility
from octoprint_octolapse.settings import OctolapseGcodeSettings
# remove unused import
# from octoprint_octolapse.gcode_processor import GcodeProcessor, Pos, Extruder
from octoprint_octolapse.gcode_processor import GcodeProcessor, Pos
# create the module level logger
from octoprint_octolapse.log import LoggingConfigurator
logging_configurator = LoggingConfigurator()
logger = logging_configurator.get_logger(__name__)

class Position(utility.JsonSerializable):
    def __init__(self, printer_profile, trigger_profile, overridable_printer_profile_settings):
        # This key is used to call the unique gcode_position object for Octolapse.
        # This way multiple position trackers can be used at the same time with no
        # ill effects.
        self.g90_influences_extruder = overridable_printer_profile_settings["g90_influences_extruder"]
        self.overridable_printer_profile_settings = overridable_printer_profile_settings

        # create location detection commands
        self._location_detection_commands = []
        if printer_profile.auto_position_detection_commands is not None:
            trimmed_commands = printer_profile.auto_position_detection_commands.strip()
            if len(trimmed_commands) > 0:
                self._location_detection_commands = [
                    x.strip().upper()
                    for x in
                    printer_profile.auto_position_detection_commands.split(',')
                ]
        if "G28" not in self._location_detection_commands:
            self._location_detection_commands.append("G28")
        if "G29" not in self._location_detection_commands:
            self._location_detection_commands.append("G29")

        # remove support for G161 and G162 until they are better understood
        # if "G161" not in self._location_detection_commands:
        #     self._location_detection_commands.append("G161")
        # if "G162" not in self._location_detection_commands:
        #     self._location_detection_commands.append("G162")
        self._gcode_generation_settings = printer_profile.get_current_state_detection_settings()
        cpp_position_args = printer_profile.get_position_args(overridable_printer_profile_settings)

        GcodeProcessor.initialize_position_processor(cpp_position_args)

        self._auto_detect_position = printer_profile.auto_detect_position
        self._priming_height = printer_profile.priming_height
        self._position_restrictions = None if trigger_profile is None else trigger_profile.position_restrictions

        self._has_restricted_position = False if trigger_profile is None else (
            len(trigger_profile.position_restrictions) > 0 and trigger_profile.position_restrictions_enabled
        )

        self._gcode_generation_settings = printer_profile.get_current_state_detection_settings()
        assert (isinstance(self._gcode_generation_settings, OctolapseGcodeSettings))
        self._priming_height = printer_profile.priming_height
        self._minimum_layer_height = printer_profile.minimum_layer_height

        self.current_pos = GcodeProcessor.get_current_position()
        self.previous_pos = GcodeProcessor.get_previous_position()
        self.undo_pos = GcodeProcessor.get_current_position()

    def update_position(self, x, y, z, e, f):
        GcodeProcessor.update_position(self.current_pos, x, y, z, e, f)

    def to_position_dict(self):
        ret_dict = self.current_pos.to_dict()
        return ret_dict

    def to_state_dict(self):
        return self.current_pos.to_state_dict()

    def command_requires_location_detection(self, cmd):
        if self._auto_detect_position:
            if cmd in self._location_detection_commands:
                return True
        return False

    def undo_update(self):
        GcodeProcessor.undo()
        # set pos to the previous pos and pop the current position
        if self.undo_pos is None:
            raise Exception("Cannot undo updates when there is less than one position in the position queue.")

        previous_position = self.current_pos
        self.current_pos = self.previous_pos
        self.previous_pos = self.undo_pos
        self.undo_pos = None
        return previous_position

    def update(self, gcode, file_line_number=None):
        # Move the current position to the previous and the previous to the undo position
        # then copy previous to current
        if self.undo_pos is None:
            self.undo_pos = Pos()
        old_undo_pos = self.undo_pos
        self.undo_pos = self.previous_pos
        self.previous_pos = self.current_pos
        self.current_pos = old_undo_pos

        Pos.copy(self.previous_pos, self.current_pos)

        # process the gcode and update our current position
        GcodeProcessor.update(gcode, self.current_pos)

        # fill in the file line number if it is supplied.
        if file_line_number is not None:
            self.current_pos.file_line_number = file_line_number

        previous = self.previous_pos
        current = self.current_pos

        # reset the position restriction in_path_position state since it only works
        # for one gcode at a time.
        current.in_path_position = False
        if not self._has_restricted_position:
            # If we don't have restricted positions, we are always in position!
            current.is_in_position = True
        elif current.has_xy_position_changed:
            # calculate position restrictions
            if (
                current.x is None or
                current.y is None or
                previous.x is None or
                previous.y is None
            ):
                current.is_in_position = False
            else:
                # If we're using restricted positions, calculate intersections and determine if we are in position
                can_calculate_intersections = current.parsed_command.cmd in ["G0", "G1"]
                _is_in_position, _intersections = self.calculate_path_intersections(
                    self._position_restrictions,
                    current.x,
                    current.y,
                    previous.x,
                    previous.y,
                    can_calculate_intersections
                )
                current.is_in_position = _is_in_position
                if not _is_in_position:
                    current.in_path_position = _intersections

    #def process_g2_g3(self, cmd):
    #    parameters = self.current_pos.parsed_command.parameters
    #    # Movement Type
    #    if cmd == "G2":
    #        movement_type = "clockwise"
    #        #self._logger.log_position_command_received("Received G2 - Clockwise Arc")
    #    else:
    #        movement_type = "counter-clockwise"
    #        #self._logger.log_position_command_received("Received G3 - Counter-Clockwise Arc")
#
    #    x = parameters["X"] if "X" in parameters else None
    #    y = parameters["Y"] if "Y" in parameters else None
    #    i = parameters["I"] if "I" in parameters else None
    #    j = parameters["J"] if "J" in parameters else None
    #    r = parameters["R"] if "R" in parameters else None
    #    e = parameters["E"] if "E" in parameters else None
    #    f = parameters["F"] if "F" in parameters else None
#
    #    # If we're moving on the X/Y plane only, mark this position as travel only
    #    self.current_pos.is_xy_travel = e is None
#
    #    can_update_position = False
    #    if r is not None and (i is not None or j is not None):
    #        # todo:  deal with logging!  Doesn't work in multiprocessing because of pickle
    #        pass
    #        #self._logger.log_error("Received {0} - but received R and either I or J, which is not allowed.".format(cmd))
    #    elif i is not None or j is not None:
    #        # IJ Form
    #        if x is not None and y is not None:
    #            # not a circle, the position has changed
    #            can_update_position = True
    #            #self._logger.log_info("Cannot yet calculate position restriction intersections when G2/G3.")
    #    elif r is not None:
    #        # R Form
    #        if x is None and y is None:
    #            # Todo: deal with logging, doesn't work in multiprocessing or with pickle
    #            pass
    #            #self._logger.log_error("Received {0} - but received R without x or y, which is not allowed.".format(cmd))
    #        else:
    #            can_update_position = True
    #            #self._logger.log_info("Cannot yet calculate position restriction intersections when G2/G3.")
#
    #    if can_update_position:
    #        self.current_pos.update_position(x, y, None, e, f)
#
    #        message = "Position Change - {0} - {1} {2} Arc From(X:{3},Y:{4},Z:{5},E:{6}) - To(X:{7},Y:{8}," \
    #                  "Z:{9},E:{10})"
    #        if self.previous_pos is None:
    #            message = message.format(
    #                self.current_pos.parsed_command.gcode, "Relative" if self.current_pos.is_relative else "Absolute",
    #                movement_type, "None", "None", "None", "None", self.current_pos.x, self.current_pos.y,
    #                self.current_pos.z, self.current_pos.e
    #            )
    #        else:
    #            message = message.format(
    #                self.current_pos.parsed_command.gcode, "Relative" if self.current_pos.is_relative else "Absolute",
    #                movement_type,
    #                self.previous_pos.x,
    #                self.previous_pos.y, self.previous_pos.z, self.previous_pos.e, self.current_pos.x,
    #                self.current_pos.y, self.current_pos.z, self.current_pos.e)
    #        #self._logger.log_position_change(message)
#
    #def process_g10(self):
    #    parameters = self.current_pos.parsed_command.parameters
    #    if "P" not in parameters:
    #        e = (
    #            0 if self.current_pos.firmware_retraction_length is None
    #            else -1.0 * self.current_pos.firmware_retraction_length
    #        )
    #        previous_extruder_relative = self.current_pos.is_extruder_relative
    #        previous_relative = self.current_pos.is_relative
#
    #        self.current_pos.is_relative = True
    #        self.current_pos.is_extruder_relative = True
    #        self.current_pos.update_position(None, None, self.current_pos.firmware_z_lift, e,
    #                                         self.current_pos.firmware_retraction_feedrate)
    #        self.current_pos.is_relative = previous_relative
    #        self.current_pos.is_extruder_relative = previous_extruder_relative
#
    #def process_g11(self):
    #    lift_distance = 0 if self.current_pos.firmware_z_lift is None else -1.0 * self.current_pos.firmware_z_lift
    #    e = 0 if self.current_pos.firmware_retraction_length is None else self.current_pos.firmware_retraction_length
#
    #    if self.current_pos.firmware_unretraction_feedrate is not None:
    #        f = self.current_pos.firmware_unretraction_feedrate
    #    else:
    #        f = self.current_pos.firmware_retraction_feedrate
#
    #    if self.current_pos.firmware_unretraction_additional_length:
    #        e = e + self.current_pos.firmware_unretraction_additional_length
#
    #    previous_extruder_relative = self.current_pos.is_extruder_relative
    #    previous_relative = self.current_pos.is_relative
#
    #    self.current_pos.is_relative = True
    #    self.current_pos.is_extruder_relative = True
#
    #    # Todo:  verify this next line
    #    self.current_pos.update_position(None, None, lift_distance, e, f)
    #    self.current_pos.is_relative = previous_relative
    #    self.current_pos.is_extruder_relative = previous_extruder_relative

    #def process_g20(self):
    #    # change units to inches
    #    if self.current_pos.is_metric is None or self.current_pos.is_metric:
    #        self.current_pos.is_metric = False
#
    #def process_g21(self):
    #    # change units to millimeters
    #    if self.current_pos.is_metric is None or not self.current_pos.is_metric:
    #        self.current_pos.is_metric = True

    #def process_m207(self):
    #    parameters = self.current_pos.parsed_command.parameters
    #    # Firmware Retraction Tracking
    #    if "S" in parameters:
    #        self.current_pos.firmware_retraction_length = parameters["S"]
    #    if "R" in parameters:
    #        self.current_pos.firmware_unretraction_additional_length = parameters["R"]
    #    if "F" in parameters:
    #        self.current_pos.firmware_retraction_feedrate = parameters["F"]
    #    if "T" in parameters:
    #        self.current_pos.firmware_unretraction_feedrate = parameters["T"]
    #    if "Z" in parameters:
    #        self.current_pos.firmware_z_lift = parameters["Z"]
#
    #def process_m208(self):
    #    parameters = self.current_pos.parsed_command.parameters
    #    # Firmware Retraction Tracking
    #    if "S" in parameters:
    #        self.current_pos.firmware_unretraction_additional_length = parameters["S"]
    #    if "F" in parameters:
    #        self.current_pos.firmware_unretraction_feedrate = parameters["F"]

    # Eventually this code will support the G161 and G162 commands
    # Hold this code for the future
    # Not ready to be released as of now.
    # def _g161_received(self, pos):
    #     # Home
    #     pos.has_received_home_command = True
    #     x = True if "X" in pos.parsed_command.parameters else None
    #     y = True if "Y" in pos.parsed_command.parameters else None
    #     z = True if "Z" in pos.parsed_command.parameters else None
    #     f = True if "F" in pos.parsed_command.parameters else None
    #     # ignore the W parameter, it's used in Prusa firmware to indicate a home without mesh bed leveling
    #     # w = parameters["W"] if "W" in parameters else None
    #
    #     x_homed = False
    #     y_homed = False
    #     z_homed = False
    #     if x is not None:
    #         x_homed = True
    #     if y is not None:
    #         y_homed = True
    #     if z is not None:
    #         z_homed = True
    #
    #     if f is not None:
    #         pos.F = f
    #
    #     # if there are no x,y or z parameters, we're homing all axes
    #     if x is None and y is None and z is None:
    #         x_homed = True
    #         y_homed = True
    #         z_homed = True
    #
    #     home_strings = []
    #     if x_homed:
    #         pos.x_homed = True
    #         pos.X = self._origin["x"] if not self._auto_detect_position else None
    #         if pos.X is None:
    #             home_strings.append("Homing X to Unknown Origin.")
    #         else:
    #             home_strings.append("Homing X to {0}.".format(
    #                 get_formatted_coordinate(pos.X)))
    #     if y_homed:
    #         pos.y_homed = True
    #         pos.Y = self._origin["y"] if not self._auto_detect_position else None
    #         if pos.Y is None:
    #             home_strings.append("Homing Y to Unknown Origin.")
    #         else:
    #             home_strings.append("Homing Y to {0}.".format(
    #                 get_formatted_coordinate(pos.Y)))
    #     if z_homed:
    #         pos.z_homed = True
    #         pos.Z = self._origin["z"] if not self._auto_detect_position else None
    #         if pos.Z is None:
    #             home_strings.append("Homing Z to Unknown Origin.")
    #         else:
    #             home_strings.append("Homing Z to {0}.".format(
    #                 get_formatted_coordinate(pos.Z)))
    #
    #     self._logger.log_position_command_received(
    #         "Received G161 - ".format(" ".join(home_strings)))
    #
    # def _g162_received(self, pos):
    #     # Home
    #     pos.has_received_home_command = True
    #     x = True if "X" in pos.parsed_command.parameters else None
    #     y = True if "Y" in pos.parsed_command.parameters else None
    #     z = True if "Z" in pos.parsed_command.parameters else None
    #     f = True if "F" in pos.parsed_command.parameters else None
    #
    #     x_homed = False
    #     y_homed = False
    #     z_homed = False
    #     if x is not None:
    #         x_homed = True
    #     if y is not None:
    #         y_homed = True
    #     if z is not None:
    #         z_homed = True
    #
    #     if f is not None:
    #         pos.F = f
    #
    #     # if there are no x,y or z parameters, we're homing all axes
    #     if x is None and y is None and z is None:
    #         x_homed = True
    #         y_homed = True
    #         z_homed = True
    #
    #     home_strings = []
    #     if x_homed:
    #         pos.x_homed = True
    #         pos.X = self._origin["x"] if not self._auto_detect_position else None
    #         if pos.X is None:
    #             home_strings.append("Homing X to Unknown Origin.")
    #         else:
    #             home_strings.append("Homing X to {0}.".format(
    #                 get_formatted_coordinate(pos.X)))
    #     if y_homed:
    #         pos.y_homed = True
    #         pos.Y = self._origin["y"] if not self._auto_detect_position else None
    #         if pos.Y is None:
    #             home_strings.append("Homing Y to Unknown Origin.")
    #         else:
    #             home_strings.append("Homing Y to {0}.".format(
    #                 get_formatted_coordinate(pos.Y)))
    #     if z_homed:
    #         pos.z_homed = True
    #         pos.Z = self._origin["z"] if not self._auto_detect_position else None
    #         if pos.Z is None:
    #             home_strings.append("Homing Z to Unknown Origin.")
    #         else:
    #             home_strings.append("Homing Z to {0}.".format(
    #                 get_formatted_coordinate(pos.Z)))
    #
    #     self._logger.log_position_command_received(
    #         "Received G162 - ".format(" ".join(home_strings)))

    def calculate_path_intersections(self, restrictions, x, y, previous_x, previous_y, can_calculate_intersections):

        if self.calculate_is_in_position(
            restrictions,
            x,
            y,
            utility.FLOAT_MATH_EQUALITY_RANGE
        ):
            return True, None

        if previous_x is None or previous_y is None:
            return False, False

        if not can_calculate_intersections:
            return False, None

        return False, self.calculate_in_position_intersection(
            restrictions,
            x,
            y,
            previous_x,
            previous_y,
            utility.FLOAT_MATH_EQUALITY_RANGE
        )

    @staticmethod
    def calculate_in_position_intersection(restrictions, x, y, previous_x, previous_y, tolerance):
        intersections = []
        for restriction in restrictions:
            cur_intersections = restriction.get_intersections(x, y, previous_x, previous_y)
            if cur_intersections:
                for cur_intersection in cur_intersections:
                    intersections.append(cur_intersection)

        if len(intersections) == 0:
            return False

        for intersection in intersections:
            if Position.calculate_is_in_position(restrictions, intersection[0], intersection[1], tolerance):
                return {
                    'intersection': intersection
                }
        return False

    @staticmethod
    def calculate_is_in_position(restrictions, x, y, tolerance):
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
            if restriction.is_in_position(x, y, tolerance):
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

    @staticmethod
    def _extruder_state_triggered(option, state):
        if option is None:
            return None
        if option and state:
            return True
        if not option and state:
            return False
        return None

    def is_extruder_triggered(self, options):
        return self._is_extruder_triggered(self.current_pos, options)

    def is_previous_extruder_triggered(self, options):
        return self._is_extruder_triggered(self.previous_pos, options)

    @staticmethod
    def _is_extruder_triggered(pos, options):
        assert(isinstance(pos, Pos))
        extruder = pos.get_current_extruder()
        # if there are no extruder trigger options, return true.
        if options is None:
            return True

        # Matches the supplied extruder trigger options to the current
        # extruder state.  Returns true if triggering, false if not.

        extruding_start_triggered = Position._extruder_state_triggered(
            options.on_extruding_start, extruder.is_extruding_start
        )
        extruding_triggered = Position._extruder_state_triggered(
            options.on_extruding, extruder.is_extruding
        )
        primed_triggered = Position._extruder_state_triggered(
            options.on_primed, extruder.is_primed
        )
        retracting_start_triggered = Position._extruder_state_triggered(
            options.on_retracting_start, extruder.is_retracting_start
        )
        retracting_triggered = Position._extruder_state_triggered(
            options.on_retracting, extruder.is_retracting
        )
        partially_retracted_triggered = Position._extruder_state_triggered(
            options.on_partially_retracted, extruder.is_partially_retracted
        )
        retracted_triggered = Position._extruder_state_triggered(
            options.on_retracted, extruder.is_retracted
        )
        deretracting_start_triggered = Position._extruder_state_triggered(
            options.on_deretracting_start, extruder.is_deretracting_start
        )
        deretracting_triggered = Position._extruder_state_triggered(
            options.on_deretracting, extruder.is_deretracting
        )
        deretracted_triggered = Position._extruder_state_triggered(
            options.on_deretracted, extruder.is_deretracted
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
        'on_extruding_start',
        'on_extruding',
        'on_primed',
        'on_retracting_start',
        'on_retracting',
        'on_partially_retracted',
        'on_retracted',
        'on_deretracting_start',
        'on_deretracting',
        'on_deretracted'
    ]

    def __init__(
        self, on_extruding_start, on_extruding, on_primed, on_retracting_start, on_retracting, on_partially_retracted,
        on_retracted, on_deretracting_start, on_deretracting, on_deretracted
    ):
        # To trigger on an extruder state, set to True.
        # To prevent triggering on an extruder state, set to False.
        # To ignore the extruder state, set to None
        self.on_extruding_start = on_extruding_start
        self.on_extruding = on_extruding
        self.on_primed = on_primed
        self.on_retracting_start = on_retracting_start
        self.on_retracting = on_retracting
        self.on_partially_retracted = on_partially_retracted
        self.on_retracted = on_retracted
        self.on_deretracting_start = on_deretracting_start
        self.on_deretracting = on_deretracting
        self.on_deretracted = on_deretracted

    def are_all_triggers_ignored(self):
        if (
            self.on_extruding_start is None
            and self.on_extruding is None
            and self.on_primed is None
            and self.on_retracting_start is None
            and self.on_retracting is None
            and self.on_partially_retracted is None
            and self.on_retracted is None
            and self.on_deretracting_start is None
            and self.on_deretracting is None
            and self.on_deretracted is None
        ):
            return True
        return False
