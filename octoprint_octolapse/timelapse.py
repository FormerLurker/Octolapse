# coding=utf-8

# This file is subject to the terms and conditions defined in
# file called 'LICENSE', which is part of this source code package.

import time

import octoprint_octolapse.utility as utility
from octoprint_octolapse.command import *
from octoprint_octolapse.gcode import SnapshotGcodeGenerator
from octoprint_octolapse.position import Position
from octoprint_octolapse.render import Render
from octoprint_octolapse.settings import (Printer, Rendering, Snapshot)
from octoprint_octolapse.snapshot import CaptureSnapshot
from octoprint_octolapse.trigger import Triggers


class Timelapse(object):

    def __init__(
            self, data_folder, timelapse_folder,
            on_snapshot_start=None, on_snapshot_end=None,
            on_render_start=None, on_render_complete=None,
            on_render_fail=None, on_render_synchronize_fail=None,
            on_render_synchronize_complete=None, on_render_end=None,
            on_timelapse_stopping=None, on_timelapse_stopped=None,
            on_state_changed=None, on_timelapse_start=None,
            on_snapshot_position_error=None, on_position_error=None):
        # config variables - These don't change even after a reset
        self.Settings = None
        self.DataFolder = data_folder
        self.DefaultTimelapseDirectory = timelapse_folder
        self.OnRenderStartCallback = on_render_start
        self.OnRenderCompleteCallback = on_render_complete
        self.OnRenderFailCallback = on_render_fail
        self.OnRenderingSynchronizeFailCallback = on_render_synchronize_fail
        self.OnRenderingSynchronizeCompleteCallback = on_render_synchronize_complete
        self.OnRenderEndCallback = on_render_end
        self.OnSnapshotStartCallback = on_snapshot_start
        self.OnSnapshotCompleteCallback = on_snapshot_end
        self.TimelapseStoppingCallback = on_timelapse_stopping
        self.TimelapseStoppedCallback = on_timelapse_stopped
        self.OnStateChangedCallback = on_state_changed
        self.OnTimelapseStartCallback = on_timelapse_start
        self.OnSnapshotPositionErrorCallback = on_snapshot_position_error
        self.OnPositionErrorCallback = on_position_error
        self.Responses = Responses()  # Used to decode responses from the 3d printer
        self.Commands = Commands()  # used to parse and generate gcode
        self.Triggers = None
        # Settings that may be different after StartTimelapse is called
        self.OctoprintPrinter = None
        self.OctoprintPrinterProfile = None
        self.PrintStartTime = None
        self.FfMpegPath = None
        self.Snapshot = None
        self.Gcode = None
        self.Printer = None
        self.CaptureSnapshot = None
        self.Position = None
        self.HasSentInitialStatus = False
        self.Rendering = None
        self.State = TimelapseState.Idle
        self.IsTestMode = False
        # State Tracking that should only be reset when starting a timelapse
        self.IsRendering = False
        self.HasBeenCancelled = False
        self.HasBeenStopped = False
        self.TimelapseStopRequested = False
        self.SavedCommand = None
        # State tracking variables
        self.RequiresLocationDetectionAfterHome = False

        self._reset()

    # public functions
    def start_timelapse(
            self, settings, octoprint_printer, octoprint_printer_profile, ffmpeg_path, g90_influences_extruder):
        # we must supply the settings first!  Else reset won't work properly.
        self.Settings = settings

        self._reset()
        self.HasSentInitialStatus = False
        self.RequiresLocationDetectionAfterHome = False
        self.OctoprintPrinter = octoprint_printer
        self.OctoprintPrinterProfile = octoprint_printer_profile
        self.FfMpegPath = ffmpeg_path
        self.PrintStartTime = time.time()
        self.Snapshot = Snapshot(self.Settings.current_snapshot())
        self.Gcode = SnapshotGcodeGenerator(
            self.Settings, octoprint_printer_profile)
        self.Printer = Printer(self.Settings.current_printer())
        self.Rendering = Rendering(self.Settings.current_rendering())
        self.CaptureSnapshot = CaptureSnapshot(
            self.Settings, self.DataFolder, print_start_time=self.PrintStartTime)
        self.Position = Position(
            self.Settings, octoprint_printer_profile, g90_influences_extruder)
        self.State = TimelapseState.WaitingForTrigger
        self.IsTestMode = self.Settings.current_debug_profile().is_test_mode
        self.Triggers = Triggers(settings)
        self.Triggers.create()
        # send an initial state message
        self._on_timelapse_start()

    def to_state_dict(self):
        try:

            position_dict = None
            position_state_dict = None
            extruder_dict = None
            trigger_state = None
            if self.Settings is not None:

                if self.Settings.show_position_changes and self.Position is not None:
                    position_dict = self.Position.to_position_dict()
                if self.Settings.show_position_state_changes and self.Position is not None:
                    position_state_dict = self.Position.to_state_dict()
                if self.Settings.show_extruder_state_changes and self.Position is not None:
                    extruder_dict = self.Position.Extruder.to_dict()
                if self.Settings.show_trigger_state_changes and self.Triggers is not None:
                    trigger_state = {
                        "Name": self.Triggers.Name,
                        "Triggers": self.Triggers.state_to_list()
                    }
            state_dict = {
                "Extruder": extruder_dict,
                "Position": position_dict,
                "PositionState": position_state_dict,
                "TriggerState": trigger_state
            }
            return state_dict
        except Exception as e:
            self.Settings.CurrentDebugProfile().log_exception(e)
        # if we're here, we've reached and logged an error.
        return {
            "Extruder": None,
            "Position": None,
            "PositionState": None,
            "TriggerState": None
        }

    def stop_snapshots(self):
        # Stops octolapse from taking any further snapshots.
        # Any existing snapshots will render after the print is ends.

        # we don't need to end the timelapse if it hasn't started
        if self.State == TimelapseState.WaitingForTrigger or self.TimelapseStopRequested:
            self.State = TimelapseState.WaitingToRender
            self.TimelapseStopRequested = False
            if self.TimelapseStoppedCallback is not None:
                self.TimelapseStoppedCallback()
            return True

        # if we are here, we're delaying the request until after the snapshot
        self.TimelapseStopRequested = True
        if self.TimelapseStoppingCallback is not None:
            self.TimelapseStoppingCallback()

    def end_timelapse(self, cancelled=False, force=False):
        try:
            if not self.State == TimelapseState.Idle:
                if not force:
                    if TimelapseState.WaitingForTrigger < self.State < TimelapseState.WaitingToRender:
                        if cancelled:
                            self.HasBeenCancelled = True
                        else:
                            self.HasBeenStopped = True
                        return
                self._render_timelapse()
                self._reset()
        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)

    def on_print_paused(self):
        try:
            if self.State == TimelapseState.Idle:
                return
            elif self.State < TimelapseState.WaitingToRender:
                self.Settings.current_debug_profile().log_print_state_change("Print Paused.")
                self.Triggers.pause()
        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)

    def on_print_resumed(self):
        try:
            if self.State == TimelapseState.Idle:
                return
            elif self.State < TimelapseState.WaitingToRender:
                self.Triggers.resume()
        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)

    def is_timelapse_active(self):
        try:
            if (
                self.Settings is None
                or self.State == TimelapseState.Idle
                or self.State == TimelapseState.WaitingToRender
                or self.Triggers.count() < 1
            ):
                return False
            return True
        except Exception as e:
            self.Settings.CurrentDebugProfile().log_exception(e)
        return False

    def on_gcode_queuing(self, cmd, cmd_type, gcode):
        try:
            self.Settings.current_debug_profile().log_gcode_queuing(
                "Queuing Command: Command Type:{0}, gcode:{1}, cmd: {2}".format(cmd_type, gcode, cmd))
            # update the position tracker so that we know where all of the axis are.
            # We will need this later when generating snapshot gcode so that we can return to the previous
            # position
            cmd = cmd.upper().strip()
            # create our state change dictionaries
            position_change_dict = None
            position_state_change_dict = None
            extruder_change_dict = None
            trigger_change_list = None
            self.Position.update(cmd)
            if self.Position.has_position_error(0):
                self._on_position_error()
            # capture any changes, if neccessary, to the position, position state and extruder state
            # Note:  We'll get the trigger state later
            if (self.Settings.show_position_changes
                    and (self.Position.has_position_changed() or not self.HasSentInitialStatus)):
                position_change_dict = self.Position.to_position_dict()
            if (self.Settings.show_position_state_changes
                    and (self.Position.has_state_changed() or not self.HasSentInitialStatus)):
                position_state_change_dict = self.Position.to_state_dict()
            if (self.Settings.show_extruder_state_changes
                    and (self.Position.Extruder.has_changed() or not self.HasSentInitialStatus)):
                extruder_change_dict = self.Position.Extruder.to_dict()
            # get the position state in case it has changed
            # if there has been a position or extruder state change, inform any listener
            is_snapshot_gcode_command = self._is_snapshot_command(cmd)
            # check to see if we've just completed a home command
            if (self.State == TimelapseState.WaitingForTrigger
                    and (self.Position.requires_location_detection(1)) and self.OctoprintPrinter.is_printing()):
                # Undo the last position update, we will be resending the command
                self.Position.undo_update()
                self.State = TimelapseState.AcquiringLocation
                if self.IsTestMode:
                    cmd = self.Commands.get_test_mode_command_string(cmd)
                self.SavedCommand = cmd
                cmd = None,
                message = (
                    "A position altering requires that we acquire a "
                    "location, pausing print and undoing the last "
                    "position update.  New Position: {0}"
                ).format(self.Position.get_position_string())
                self.Settings.current_debug_profile().log_print_state_change(message)
                self._pause_print()
            elif (self.State == TimelapseState.WaitingForTrigger
                  and self.OctoprintPrinter.is_printing()
                  and not self.Position.has_position_error(0)):
                self.Triggers.update(self.Position, cmd)

                # If our triggers have changed, update our dict
                if self.Settings.show_trigger_state_changes and self.Triggers.has_changed():
                    trigger_change_list = self.Triggers.changes_to_list()

                if self.is_triggering():
                    # Undo the last position update, we're not going to be using it!
                    self.Position.undo_update()
                    # Store the current position (our previous position), since this will be our snapshot position
                    self.Position.save_position()
                    # we don't want to execute the current command.  We have saved it for later.
                    # but we don't want to send the snapshot command to the printer, or any of
                    # the SupporessedSavedCommands (gcode.py)
                    if is_snapshot_gcode_command or cmd in self.Commands.SuppressedSavedCommands:
                        # this will suppress the command since it won't be added to our snapshot commands list
                        self.SavedCommand = None
                    else:
                        if self.IsTestMode:
                            cmd = self.Commands.get_test_mode_command_string(cmd)
                        # this will cause the command to be added to the end of our snapshot commands
                        self.SavedCommand = cmd
                    # pause the printer to start the snapshot
                    self.State = TimelapseState.RequestingReturnPosition

                    # Pausing the print here will immediately trigger an M400 and a location request
                    self._pause_print()  # send M400 and position request
                    # send a notification to the client that the snapshot is starting
                    if self.OnSnapshotStartCallback is not None:
                        self.OnSnapshotStartCallback()
                    # suppress the command
                    cmd = None,

            elif TimelapseState.WaitingForTrigger < self.State <= TimelapseState.SendingReturnGcode:
                # Don't do anything further to any commands unless we are
                # taking a timelapse , or if octolapse paused the print.
                # suppress any commands we don't, under any cirumstances,
                # to execute while we're taking a snapshot

                if cmd in self.Commands.SuppressedSnapshotGcodeCommands:
                    cmd = None,  # suppress the command

            if is_snapshot_gcode_command:
                # in all cases do not return the snapshot command to the printer.
                # It is NOT a real gcode and could cause errors.
                cmd = None,

            # notify any callbacks
            self._on_state_changed(
                position_change_dict, position_state_change_dict, extruder_change_dict, trigger_change_list)
            self.HasSentInitialStatus = True

            if cmd != (None,):
                return self._get_command_for_octoprint(cmd)
            # if we are here we need to suppress the command
        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)
            raise

        return cmd

    def is_triggering(self):
        try:
            # make sure we're in a state that could want to check for triggers
            if not self.State == TimelapseState.WaitingForTrigger:
                return None
            # see if the PREVIOUS command triggered (that means current gcode gets sent if the trigger[0]
            # is triggering
            current_trigger = self.Triggers.get_first_triggering(1)

            if current_trigger is not None:  # We're triggering
                self.Settings.current_debug_profile().log_triggering("A snapshot is triggering")
                # notify any callbacks
                return True
        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)
            # no need to re-raise here, the trigger just won't happen
        return False

    def on_gcode_sent(self, cmd, cmd_type, gcode):
        self.Settings.current_debug_profile().log_gcode_sent(
            "Sent to printer: Command Type:{0}, gcode:{1}, cmd: {2}".format(cmd_type, gcode, cmd))

    def on_position_received(self, payload):
        # if we cancelled the print, we don't want to do anything.
        if self.HasBeenCancelled:
            self.end_timelapse(force=True)
            return

        x = payload["x"]
        y = payload["y"]
        z = payload["z"]
        e = payload["e"]
        if self.State == TimelapseState.AcquiringLocation:
            self.Settings.current_debug_profile().log_print_state_change(
                "Snapshot home position received by Octolapse.")
            self._on_home_position_received(x, y, z, e)
        elif self.State == TimelapseState.SendingSavedHomeLocationCommand:
            self.Settings.current_debug_profile().log_print_state_change(
                "Snapshot home saved command position received by Octolapse.")
            self._on_home_saved_command_position_received(x, y, z, e)
        elif self.State == TimelapseState.RequestingReturnPosition:
            self.Settings.current_debug_profile().log_print_state_change(
                "Snapshot return position received by Octolapse.")
            self._on_return_position_received(x, y, z, e)
        elif self.State == TimelapseState.SendingSnapshotGcode:
            self.Settings.current_debug_profile().log_print_state_change(
                "Snapshot position received by Octolapse.")
            self._on_snapshot_position_received(x, y, z, e)
        elif self.State == TimelapseState.SendingReturnGcode:
            self._on_resume_print_position_received(x, y, z, e)
        else:
            self.Settings.current_debug_profile().log_print_state_change(
                "Position received by Octolapse while paused, but was declined.")
            return False, "Declined - Incorrect State"

    # internal functions
    ####################
    def _get_command_for_octoprint(self, cmd):

        if cmd is None or cmd == (None,):
            return cmd

        if self.IsTestMode and self.State >= TimelapseState.WaitingForTrigger:
            return self.Commands.alter_for_test_mode(cmd)
        # if we were given a list, return it.
        if isinstance(cmd, list):
            return cmd
        # if we were given a command return None (don't change the command at all)
        return None

    def _on_state_changed(
            self, position_change_dict, position_state_change_dict, extruder_change_dict, trigger_change_list):
        """Notifies any callbacks about any changes contained in the dictionaries.
        If you send a dict here the client will get a message, so check the
        settings to see if they are subscribed to notifications before populating the dictinaries!"""
        trigger_changes_dict = None
        try:

            # Notify any callbacks
            if (self.OnStateChangedCallback is not None
                and (position_change_dict is not None
                     or position_state_change_dict is not None
                     or extruder_change_dict is not None
                     or trigger_change_list is not None)):

                if trigger_change_list is not None and len(trigger_change_list) > 0:
                    trigger_changes_dict = {
                        "Name": self.Triggers.Name,
                        "Triggers": trigger_change_list
                    }
                change_dict = {
                    "Extruder": extruder_change_dict,
                    "Position": position_change_dict,
                    "PositionState": position_state_change_dict,
                    "TriggerState": trigger_changes_dict
                }

                if (change_dict["Extruder"] is not None
                        or change_dict["Position"] is not None
                        or change_dict["PositionState"] is not None
                        or change_dict["TriggerState"] is not None):
                    self.OnStateChangedCallback(change_dict)
        except Exception as e:
            # no need to re-raise, callbacks won't be notified, however.
            self.Settings.current_debug_profile().log_exception(e)

    def _is_snapshot_command(self, command):
        command_name = get_gcode_from_string(command)
        snapshot_command_name = get_gcode_from_string(self.Printer.snapshot_command)
        return command_name == snapshot_command_name

    def _is_trigger_waiting(self):
        # make sure we're in a state that could want to check for triggers
        if not self.State == TimelapseState.WaitingForTrigger:
            return None
        # Loop through all of the active currentTriggers
        waiting_trigger = self.Triggers.get_first_waiting()
        if waiting_trigger is not None:
            return True
        return False

    def _on_home_position_received(self, x, y, z, e):
        try:
            self.Position.update_position(
                x=x, y=y, z=z, e=e, force=True, calculate_changes=True)
        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)
            # we need to abandon the snapshot completely, reset and resume
        self.State = TimelapseState.SendingSavedHomeLocationCommand
        # if a saved command exists, execute it and get the current location
        if self.SavedCommand is not None:
            if self.Position.command_requires_location_detection(self.SavedCommand):
                self.RequiresLocationDetectionAfterHome = True
                self.Settings.current_debug_profile().log_snapshot_resume_position(
                    "The saved command requires position detection.  "
                    "This will execute after the saved command is executed "
                    "and the position will be updated if it changes."
                )
            self.OctoprintPrinter.commands(self.SavedCommand)
            self.SavedCommand = ""
            self.OctoprintPrinter.commands("M400")
            self.OctoprintPrinter.commands(
                "M114; Octolapse - SavedCommandPause")
        else:
            # there is no saved command, we should be good!
            self.State = TimelapseState.WaitingForTrigger
            self._resume_print()

    def _on_home_saved_command_position_received(self, x, y, z, e):
        # just sent so we can resume after the commands were sent.
        # Todo:  do this in the gcode sent function instead of sending an m400/m114 combo
        try:
            if self.RequiresLocationDetectionAfterHome:
                if not self.Position.is_at_current_position(x, y, None):
                    message = (
                        "The position has changed after receiving "
                        "the home location saved command.  Updating.  "
                        "New Position: x:{0},y:{1},z:{2},e:{3}, "
                        "Previous Position: x:{4},y:{5},z:{6}"
                    ).format(x, y, z, e, self.Position.x(), self.Position.y(), self.Position.z())
                    self.Settings.current_debug_profile().log_snapshot_resume_position(message)
                    self.Position.update_position(
                        x=x, y=y, z=z, e=e, force=True, calculate_changes=True)
                else:
                    message = (
                        "The saved command required a position update, "
                        "but the position has not changed more than the tolerance."
                    ).format(x, y, z, e, self.Position.x(), self.Position.y(), self.Position.z())
                    self.Settings.current_debug_profile().log_snapshot_resume_position(message)
        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)

        self.State = TimelapseState.WaitingForTrigger
        self.RequiresLocationDetectionAfterHome = False
        self._resume_print()

    def _on_return_position_received(self, x, y, z, e):
        try:
            self.ReturnPositionReceivedTime = time.time()
            # todo:  Do we need to re-request the position like we do for the return?  Maybe...
            # If we are requesting a return position we have NOT yet executed the command that triggered the snapshot.
            # Because of this we need to compare the position we received to the previous position, not the current one.
            if not self.Position.is_at_saved_position(x, y, z):
                message = (
                    "The snapshot return position recieved from the "
                    "printer does not match the position expected by "
                    "Octolapse.  received (x:{0},y:{1},z:{2}), Expected"
                    " (x:{3},y:{4},z:{5})"
                ).format(x, y, z, self.Position.x(), self.Position.y(), self.Position.z())
                self.Settings.current_debug_profile().log_warning(message)
                self.Position.update_position(x=x, y=y, z=z, force=True)
            else:
                # return position information received
                self.Settings.current_debug_profile().log_snapshot_return_position(
                    "Snapshot return position received - x:{0},y:{1},z:{2},e:{3}".format(x, y, z, e))
            # make sure the SnapshotCommandIndex = 0
            # Todo: ensure this is unnecessary
            self.CommandIndex = 0

            # create the GCode for the timelapse and store it
            self.SnapshotGcodes = self.Gcode.create_snapshot_gcode(
                x, y, z, self.Position.f(), self.Position.is_relative(),
                self.Position.is_extruder_relative(), self.Position.Extruder,
                self.Position.distance_to_zlift(), saved_command=self.SavedCommand
            )
            # make sure we actually received gcode
            if self.SnapshotGcodes is None:
                self._reset_snapshot()
                self._resume_print()
                self._on_snapshot_position_error()
                return False, "Error - No Snapshot Gcode"
            elif self.Gcode.HasSnapshotPositionErrors:
                # there is a position error, but gcode was generated.  Just report it to the user.
                self._on_snapshot_position_error()

            self.State = TimelapseState.SendingSnapshotGcode

            snapshot_commands = self.SnapshotGcodes.get_snapshot_commands()

            # send our commands to the printer
            # these commands will go through queuing, no reason to track position
            self.OctoprintPrinter.commands(snapshot_commands)
        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)
            # we need to abandon the snapshot completely, reset and resume
            self._reset_snapshot()
            self._resume_print()

    def _on_snapshot_position_received(self, x, y, z, e):
        try:
            # snapshot position information received
            message = (
                "Snapshot position received, checking position:  "
                "Received: x:{0},y:{1},z:{2},e:{3}, Expected: x:{4},y:{5},z:{6}"
            ).format(x, y, z, e, self.Position.x(), self.Position.y(), self.Position.z())
            self.Settings.current_debug_profile().log_snapshot_return_position(message)
            # see if the CURRENT position is the same as the position we received from the printer
            # AND that it is equal to the snapshot position
            if not self.Position.is_at_current_position(x, y, None):
                message = (
                    "The snapshot position is incorrect.  "
                    "Received: x:{0},y:{1},z:{2},e:{3}, Expected: x:{4},y:{5},z:{6}"
                ).format(x, y, z, e, self.Position.x(), self.Position.y(), self.Position.z())
                self.Settings.current_debug_profile().log_warning(message)
            # our snapshot gcode will NOT be offset
            elif not self.Position.is_at_current_position(
                    self.SnapshotGcodes.X, self.SnapshotGcodes.Y, None):
                message = (
                    "The snapshot gcode position is incorrect.  "
                    "x:{0},y:{1},z:{2},e:{3}, Expected: x:{4},y:{5},z:{6}"
                ).format(x, y, z, e, self.SnapshotGcodes.X, self.SnapshotGcodes.Y, self.Position.z())
                self.Settings.current_debug_profile().log_error(message)

            self.Settings.current_debug_profile().log_snapshot_return_position(
                "The snapshot position is correct, taking snapshot.")
            self.State = TimelapseState.TakingSnapshot
            self._take_snapshot()
        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)
            # our best bet of fixing things up here is just to return to the previous position.
            self._send_return_commands()

    def _on_position_error(self):
        message = self.Position.position_error(0)
        self.Settings.current_debug_profile().log_error(message)
        if self.OnPositionErrorCallback is not None:
            self.OnPositionErrorCallback(message)

    def _on_snapshot_position_error(self):
        if self.Printer.abort_out_of_bounds:
            message = "No snapshot gcode was created for this snapshot.  Aborting this snapshot.  Details: {0}".format(
                self.Gcode.SnapshotPositionErrors)
        else:
            message = "The snapshot position has been updated due to an out-of-bounds error.  Details: {0}".format(
                self.Gcode.SnapshotPositionErrors)
        self.Settings.current_debug_profile().log_error(message)
        if self.OnSnapshotPositionErrorCallback is not None:
            self.OnSnapshotPositionErrorCallback(message)

    def _on_resume_print_position_received(self, x, y, z, e):
        snapshot_success = False
        snapshot_error = "Unknown Error"
        try:
            if not self.Position.is_at_current_position(x, y, None):
                message = (
                    "Save Command Position is incorrect.  "
                    "Received: x:{0},y:{1},z:{2},e:{3}, Expected: x:{4},y:{5},z:{6}"
                ).format(x, y, z, e, self.Position.x(), self.Position.y(), self.Position.z())
                self.Settings.current_debug_profile().log_error(message)
            else:
                message = (
                    "Save Command Position is correct.  "
                    "Received: x:{0},y:{1},z:{2},e:{3}, Expected: x:{4},y:{5},z:{6}"
                ).format(x, y, z, e, self.Position.x(), self.Position.y(), self.Position.z())
                self.Settings.current_debug_profile().log_snapshot_resume_position(message)

            self.SecondsAddedByOctolapse += time.time() - self.ReturnPositionReceivedTime

            # before resetting the snapshot, see if it was a success
            snapshot_success = self.SnapshotSuccess
            snapshot_error = self.SnapshotError
            # end the snapshot
            self._reset_snapshot()

            # If we've requested that the timelapse stop, stop it now
            if self.TimelapseStopRequested:
                self.stop_snapshots()
        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)
            # do not re-raise, we are better off trying to resume the print here.
        self._resume_print()
        self._on_trigger_snapshot_complete(snapshot_success, snapshot_error)

    def _on_trigger_snapshot_complete(self, snapshot_success, snapshot_error=""):
        if self.OnSnapshotCompleteCallback is not None:
            payload = {
                "success": snapshot_success,
                "error": snapshot_error,
                "snapshot_count": self.SnapshotCount,
                "seconds_added_by_octolapse": self.SecondsAddedByOctolapse
            }
            self.OnSnapshotCompleteCallback(payload)

    def _pause_print(self):
        self.OctoprintPrinter.pause_print()

    def _resume_print(self):
        self.OctoprintPrinter.resume_print()
        if self.HasBeenStopped or self.HasBeenCancelled:
            self.end_timelapse(force=True)

    def _take_snapshot(self):
        self.Settings.current_debug_profile().log_snapshot_download("Taking Snapshot.")
        try:
            self.CaptureSnapshot.snap(
                utility.get_currently_printing_filename(self.OctoprintPrinter), self.SnapshotCount,
                on_complete=self._on_snapshot_complete, on_success=self._on_snapshot_success,
                on_fail=self._on_snapshot_fail
            )
        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)
            # try to recover by sending the return command
            self._send_return_commands()

    def _on_snapshot_success(self, *args, **kwargs):
        # Increment the number of snapshots received
        self.SnapshotCount += 1
        self.SnapshotSuccess = True

    def _on_snapshot_fail(self, *args, **kwargs):
        reason = args[0]
        message = "Failed to download the snapshot.  Reason: {0}".format(
            reason)
        self.Settings.current_debug_profile().log_snapshot_download(message)
        self.SnapshotSuccess = False
        self.SnapshotError = message

    def _on_snapshot_complete(self, *args, **kwargs):
        self.Settings.current_debug_profile().log_snapshot_download("Snapshot Completed.")
        self._send_return_commands()

    def _send_return_commands(self):
        try:
            # if the print has been cancelled, quit now.
            if self.HasBeenCancelled:
                self.end_timelapse(force=True)
                return
            # Expand the current command to include the return commands
            if self.SnapshotGcodes is None:
                self.Settings.current_debug_profile().log_error(
                    "The snapshot gcode generator has no value.")
                self.end_timelapse(force=True)
                return
            return_commands = self.SnapshotGcodes.get_return_commands()
            if return_commands is None:
                self.Settings.current_debug_profile().log_error(
                    "No return commands were generated!")
                # How do we handle this?  we probably need to cancel the print or something....
                # Todo:  What to do if no return commands are generated?  We should never let this happen.
                # Make sure this is true.
                self.end_timelapse(force=True)
                return

            # set the state so that the final received position will trigger a resume.
            self.State = TimelapseState.SendingReturnGcode
            # these commands will go through queuing, no need to update the position
            self.OctoprintPrinter.commands(return_commands)
        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)
            # need to re-raise, can't fix this here, but at least it will be logged
            # properly
            raise

    def _render_timelapse(self):
        # make sure we have a non null TimelapseSettings object.  We may have terminated the timelapse for some reason
        if self.Rendering.enabled:
            self.Settings.current_debug_profile().log_render_start("Started Rendering Timelapse")
            # we are rendering, set the state before starting the rendering job.

            self.IsRendering = True
            timelapse_render_job = Render(
                self.Settings, self.Snapshot, self.Rendering, self.DataFolder,
                self.DefaultTimelapseDirectory, self.FfMpegPath, 1,
                time_added=self.SecondsAddedByOctolapse, on_render_start=self._on_render_start,
                on_render_fail=self._on_render_fail, on_render_success=self._on_render_success,
                on_render_complete=self.on_render_complete, on_after_sync_fail=self._on_synchronize_rendering_fail,
                on_after_sync_success=self._on_synchronize_rendering_complete, on_complete=self._on_render_end
            )
            timelapse_render_job.process(utility.get_currently_printing_filename(
                self.OctoprintPrinter), self.PrintStartTime, time.time())

            return True
        return False

    def _on_render_start(self, *args, **kwargs):
        self.Settings.current_debug_profile().log_render_start(
            "Started rendering/synchronizing the timelapse.")
        payload = args[0]
        # notify the caller
        if self.OnRenderStartCallback is not None:
            self.OnRenderStartCallback(payload)

    def _on_render_fail(self, *args, **kwargs):
        self.IsRendering = False
        self.Settings.current_debug_profile().log_render_fail(
            "The timelapse rendering failed.")

        if self.Snapshot.cleanup_after_render_fail:
            self.CaptureSnapshot.clean_snapshots(utility.get_snapshot_temp_directory(self.DataFolder))

        # Notify Octoprint
        payload = args[0]

        if self.OnRenderFailCallback is not None:
            self.OnRenderFailCallback(payload)

    def _on_render_success(self, *args, **kwargs):
        self.Settings.current_debug_profile().log_render_complete(
            "Rendering completed successfully.")
        payload = args[0]

        if self.Snapshot.cleanup_after_render_complete:
            self.CaptureSnapshot.clean_snapshots(utility.get_snapshot_temp_directory(self.DataFolder))

        # TODO:  Notify the user that the rendering is completed if we are not synchronizing with octoprint

    def on_render_complete(self, *args, **kwargs):
        self.Settings.current_debug_profile().log_render_complete(
            "Completed rendering the timelapse.")
        self.IsRendering = False

        payload = args[0]
        if self.OnRenderCompleteCallback is not None:
            self.OnRenderCompleteCallback(payload)

    def _on_synchronize_rendering_fail(self, *args, **kwargs):
        payload = args[0]
        self.Settings.current_debug_profile().log_render_sync(
            "Synchronization with the default timelapse plugin failed.  Reason: {0}", payload.Reason)

        if self.OnRenderingSynchronizeFailCallback is not None:
            self.OnRenderingSynchronizeFailCallback(payload)

    def _on_synchronize_rendering_complete(self, *args, **kwargs):
        self.Settings.current_debug_profile().log_render_sync(
            "Synchronization with the default timelapse plugin was successful.")
        payload = args[0]
        if self.OnRenderingSynchronizeCompleteCallback is not None:
            self.OnRenderingSynchronizeCompleteCallback(payload)

    def _on_render_end(self, *args, **kwargs):
        self.IsRendering = False
        self.Settings.current_debug_profile().log_render_complete("Completed rendering.")
        payload = args[0]
        success = args[1]

        if self.OnRenderEndCallback is not None:
            self.OnRenderEndCallback(payload, success)

    def _on_timelapse_start(self):
        if self.OnTimelapseStartCallback is None:
            return
        self.OnTimelapseStartCallback()

    def _reset(self):
        self.State = TimelapseState.Idle
        self.HasSentInitialStatus = False
        if self.Triggers is not None:
            self.Triggers.reset()
        self.CommandIndex = -1
        self.SnapshotCount = 0
        self.PrintStartTime = None
        self.SnapshotGcodes = None
        self.SavedCommand = None
        self.PositionRequestAttempts = 0
        self.IsTestMode = False
        # time tracking - how much time did we add to the print?
        self.SecondsAddedByOctolapse = 0
        self.ReturnPositionReceivedTime = None
        # A list of callbacks who want to be informed when a timelapse ends
        self.TimelapseStopRequested = False
        self.SnapshotSuccess = False
        self.SnapshotError = ""
        self.HasBeenCancelled = False
        self.HasBeenStopped = False

    def _reset_snapshot(self):
        self.State = TimelapseState.WaitingForTrigger
        self.CommandIndex = -1
        self.SnapshotGcodes = None
        self.SavedCommand = None
        self.PositionRequestAttempts = 0
        self.SnapshotSuccess = False
        self.SnapshotError = ""


class TimelapseState(object):
    Idle = 1
    WaitingForTrigger = 2
    AcquiringLocation = 3
    SendingSavedHomeLocationCommand = 4
    RequestingReturnPosition = 5
    SendingSnapshotGcode = 6
    TakingSnapshot = 7
    SendingReturnGcode = 8
    WaitingToRender = 9
