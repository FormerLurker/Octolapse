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

from octoprint_octolapse.gcode_parser import ParsedCommand
from octoprint_octolapse.position import Position, Pos
import time
import os
import utility
from multiprocessing import Process, Queue
from collections import deque
import queue
import fastgcodeparser


def clear_multiprocess_queue(queue_to_clear):
    try:
        while True:
            queue_to_clear.get_nowait()
    except queue.Empty:
        pass


def spawn_position_preprocessor():
    return PositionPreprocessor()


class PositionPreprocessor(object):
    def __init__(
        self,
        notification_period_seconds=1,
        output_queue_length=2,
        chunk_size=256

    ):
        # queue to hold a list of files to process
        # we can only process one at a time
        self.file_input_queue = Queue(1)
        # queue to hold chunks of parsed gcode from files
        # this will be filled by the gcode file process and consumed by the
        # position process
        self.gcode_output_queue = Queue(output_queue_length)
        # A queue to hole progress updates from the GcodeParsingFileProcess
        self.parse_progress_queue = Queue(1)
        # A queue used to cancel processing
        self.cancel_queue = Queue(1)
        # an output queue used for returning results from the position processor
        self.snapshot_plan_queue = Queue(1)
        # a queue used for sending the current snapshot plan generator and a new position object
        # to the position processor
        self.snapshot_generator_queue = Queue(1)

        # create the gcode parsing file process and start it.  This process will continue to run
        # until the program terminates, or until 'None' is sent to the file_input_queue
        self.parser_process = GcodeParsingFileProcess(
            self.file_input_queue,
            self.gcode_output_queue,
            self.parse_progress_queue,
            self.cancel_queue,
            chunk_size=chunk_size,
            notification_period_seconds=notification_period_seconds
        )
        # start the process
        self.parser_process.start()
        # the GcodeParsingFileProcess will add True to the progress queue once it's initialized
        # so perform a blocking get until it's ready.
        self.parse_progress_queue.get()
        # at this point the GcodeParsingFileProcess is initialized and ready to rock!

        # now start up the position processor
        self.position_process = PositionProcess(
            self.snapshot_generator_queue, self.gcode_output_queue, self.snapshot_plan_queue
        )
        self.position_process.start()
        # the position_process will add True to the snapshot_plan_queue once it's initialized
        # so perform a blocking get so that we know it's ready!
        self.snapshot_plan_queue.get()

        self.running = False

    def clear_all_queues(self):
        clear_multiprocess_queue(self.file_input_queue)
        clear_multiprocess_queue(self.gcode_output_queue)
        clear_multiprocess_queue(self.parse_progress_queue)
        clear_multiprocess_queue(self.cancel_queue)
        clear_multiprocess_queue(self.snapshot_plan_queue)
        clear_multiprocess_queue(self.snapshot_generator_queue)

    def process_file(self, target_file_path, snapshot_plan_generator, position):
        # clear any current queues
        self.clear_all_queues()
        # send the position object and the snapshot_plan_generator to the position_process
        self.snapshot_generator_queue.put((snapshot_plan_generator, position))
        # start the processor by putting a file path in the queue
        self.file_input_queue.put(target_file_path)

    def cancel(self):
        self.cancel_queue.put(True)

    def shutdown(self):
        self.cancel_queue.put(True)
        self.file_input_queue.put(None)
        self.parser_process.join()
        self.snapshot_generator_queue.put(None)
        self.position_process.join()
    def get_progress(self):
        results = None
        if not self.parse_progress_queue.empty():
            try:
                progress = self.parse_progress_queue.get()
                results = progress[0], progress[1], progress[2]
            except queue.Empty:
                pass
        return results

    def get_results(self):
        if self.snapshot_plan_queue.empty():
            return None

        return self.snapshot_plan_queue.get()

    def default_matching_function(self, matches):
        pass


class GcodeParsingFileProcess(Process):

    def __init__(
        self,
        input_queue,
        output_queue,
        progress_queue,
        cancel_queue,
        chunk_size=250,
        notification_period_seconds=1
    ):
        super(GcodeParsingFileProcess, self).__init__()
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.progress_queue = progress_queue
        self.cancel_queue = cancel_queue
        self.is_cancelled = False
        self.notification_period_seconds = notification_period_seconds
        self.start_time = 0
        self.current_line = 0
        self.current_file_position = 0
        self.file_size_bytes = 0
        self.total_file_length = 1
        self.chunk_size = chunk_size
        self.queue = deque(maxlen=chunk_size)
        self.daemon = True
        self._next_notification_time = None

    def run(self):
        # initialize the fastgcodeparser
        fastgcodeparser.ParseGcode("")
        # signal the parent process that initialization is complete
        self.progress_queue.put(True)
        self.process()

    def process(self):
        while True:
            file_path = self.input_queue.get(True)
            self.current_line = 0
            self.is_cancelled = False
            items_added = 0
            if file_path is None:
                self.output_queue.put(None)
                return
            self.start_time = time.time()
            self.file_size_bytes = os.path.getsize(file_path)
            # set the next notification time
            self._next_notification_time = time.time() + self.notification_period_seconds
            # add an initial notification time of 0 percent at line 0
            self.progress_queue.put((0, 0, 0))
            with open(file_path, 'rb') as gcode_file:
                for line in gcode_file:
                    try:
                        fast_cmd = fastgcodeparser.ParseGcode(line)
                        if not fast_cmd:
                            continue
                        self.current_line += 1
                        cmd = ParsedCommand(fast_cmd[0], fast_cmd[1], line)
                        self.queue.append(cmd)
                    except Exception as e:
                        print (e)
                    items_added += 1
                    if items_added == self.chunk_size:
                        if not self.cancel_queue.empty():
                            self.is_cancelled = True
                            items_added = 0
                            break
                        self.output_queue.put(self.queue, True)
                        self.queue = deque(maxlen=self.chunk_size)
                        items_added = 0
                        if self._next_notification_time < time.time():
                            self.update_progress(gcode_file)
                            self._next_notification_time = (
                                self._next_notification_time + self.notification_period_seconds
                            )

            if not self.is_cancelled and items_added > 0:
                self.output_queue.put(self.queue, True)

            self.progress_queue.put((100, time.time() - self.start_time, self.current_line))
            self.output_queue.put(None, True)

    def update_progress(self, gcode_file):
        try:
            # print("Updating progress at " + str(time.time()))
            progress_percent = float(gcode_file.tell()) / float(self.file_size_bytes) * 100.0
            clear_multiprocess_queue(self.progress_queue)
            self.progress_queue.put((progress_percent, time.time() - self.start_time, self.current_line))
        except ValueError:
            print ("A value error occurred when updating progress.")
            pass
        except queue.Empty:
            print ("The progress queue was empty")
            pass


class PositionProcess(Process):

    def __init__(self, process_queue, input_queue, output_queue):
        super(PositionProcess, self).__init__()
        # create a new queue so that the originating process can insert processor objects
        self.process_queue = process_queue
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.daemon = True
        self.snapshot_plans = []
        self.current_line = 0

    def run(self):
        # hack to get the output time correct.  For some reason the fastgcodeparser is initialized here
        # no matter what, so let's wait for it to complete, then send True to the output queue
        # so that we can exclude the init time from our progress update
        # TODO: prevent fastgcodeparser from being imported here somehow
        fastgcodeparser.ParseGcode("")
        self.output_queue.put(True)
        while True:
            # get the processor we are using
            result = self.process_queue.get(True)
            if result is None:
                # sending None to the process queue is a signal to terminate the process
                return
            # make sure we got the appropriate number of results
            assert(len(result) == 2)
            current_processor = result[0]
            # make sure the process we got is a subclass of SnapshotPlanGenerator
            assert (isinstance(current_processor, SnapshotPlanGenerator))
            current_position = result[1]
            # make sure the position we got is an instance of Position
            assert (isinstance(current_position, Position))
            # reset any necessary parameters for the process
            self.current_line = 0
            while True:
                # get the command to parse
                commands = self.input_queue.get(True)
                if commands is None:
                    # sending None to the output_queue is a signal stop processing gcodes

                    # our processor may have some additional data to add since it had no way of knowing that the
                    # gcode file has completed
                    current_processor.on_processing_complete()
                    # add any snapshot plans (or an empty list if there are none) to the output queue here
                    self.output_queue.put(current_processor.snapshot_plans)
                    # break from the inner loop and wait for another process
                    break
                for cmd in commands:
                    self.current_line += 1
                    if cmd.cmd is not None:
                        current_position.update(cmd)
                        current_processor.process_position(current_position.current_pos, self.current_line)


TRAVEL_ACTION = "travel"
SNAPSHOT_ACTION = "snapshot"


class SnapshotPlanStep(object):
    def __init__(self, action, x=None, y=None, z=None, e=None, f=None):
        self.x = x
        self.y = y
        self.z = z
        self.e = e
        self.f = f
        self.action = action

    def to_dict(self):
        return {
            "action": self.action,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "e": self.e,
            "f": self.f,
        }


class SnapshotPlan(object):
    def __init__(self,
                 initial_position,
                 snapshot_positions,
                 return_position,
                 file_line_number,
                 saved_position_file_position,
                 z_lift_height,
                 retraction_length,
                 parsed_command,
                 send_parsed_command='first'):
        self.file_line_number = file_line_number
        self.initial_position = initial_position
        self.snapshot_positions = snapshot_positions
        self.return_position = return_position
        self.steps = []
        self.parsed_command = parsed_command
        self.send_parsed_command = send_parsed_command
        self.saved_position_file_position = saved_position_file_position
        self.lift_amount = z_lift_height
        self.retract_amount = retraction_length

    def add_step(self, step):
        assert (isinstance(step, SnapshotPlanStep))
        self.steps.append(step)

    def to_dict(self):
        return {
            "file_line_number": self.file_line_number,
            "initial_position": self.initial_position.to_dict(),
            "snapshot_positions": [x.to_dict() for x in self.snapshot_positions],
            "return_position": self.return_position.to_dict(),
            "steps": [x.to_dict() for x in self.steps],
            "parsed_command": self.parsed_command.to_dict(),
            "send_parsed_command": self.send_parsed_command,
            "saved_position_file_position": self.saved_position_file_position,
            "lift_amount": self.lift_amount,
            "retract_amount": self.retract_amount,
        }


class SnapshotPlanGenerator(object):
    def __init__(self):
        self.snapshot_plans = []

    def process_position(self, position):
        raise NotImplementedError("You must implement process_position!")


class NearestToCorner(SnapshotPlanGenerator):
    FRONT_LEFT = "front-left"
    FRONT_RIGHT = "front-right"
    BACK_LEFT = "back-left"
    BACK_RIGHT = "back-right"
    FAVOR_X = "x"
    FAVOR_Y = "y"

    # TODO:  remove nearest_to and favor_axis parameters, they can be extracted frm the snapshot profile.
    def __init__(self, printer_profile, stabilization_profile):
        super(NearestToCorner, self).__init__()
        self.is_bound = False
        if printer_profile.restrict_snapshot_area:
            self.is_bound = True
            self.x_min = printer_profile.snapshot_min_x
            self.x_max = printer_profile.snapshot_max_x
            self.y_min = printer_profile.snapshot_min_y
            self.y_max = printer_profile.snapshot_max_y
            self.z_min = printer_profile.snapshot_min_z
            self.z_max = printer_profile.snapshot_max_z

        self.nearest_to = stabilization_profile.lock_to_corner_type

        self.favor_x = stabilization_profile.lock_to_corner_favor_axis == self.FAVOR_X
        snapshot_gcode_settings = printer_profile.get_current_state_detection_settings()
        retraction_length = (
            0 if not snapshot_gcode_settings.retract_before_move else snapshot_gcode_settings.retraction_length
        )
        z_lift_height = (
            0 if not snapshot_gcode_settings.lift_when_retracted else snapshot_gcode_settings.z_lift_height
        )
        self.retraction_distance = 0 if stabilization_profile.lock_to_corner_disable_retract else retraction_length
        self.z_lift_height = 0 if stabilization_profile.lock_to_corner_disable_z_lift else z_lift_height
        self.height_increment = (
            None if stabilization_profile.lock_to_corner_height_increment == 0 else
            stabilization_profile.lock_to_corner_height_increment
        )
        self.is_layer_change_wait = False
        self.current_layer = 0
        self.current_height = 0
        self.saved_position = None
        self.saved_position_line = 0
        self.saved_position_file_position = 0
        self.current_file_position = 0

    def on_processing_complete(self):
        if self.saved_position is not None:
            self.add_saved_plan()

    def add_saved_plan(self):
        # On layer change create a plan
        # TODO:  get rid of newlines and whitespace in the fast gcode parser
        self.saved_position.parsed_command.gcode = self.saved_position.parsed_command.gcode.strip()
        # the initial, snapshot and return positions are the same here
        plan = SnapshotPlan(
            self.saved_position,  # the initial position
            [self.saved_position],  # snapshot positions
            self.saved_position,  # return position
            self.saved_position_line,
            self.saved_position_file_position,
            self.z_lift_height,
            self.retraction_distance,
            self.saved_position.parsed_command,
            send_parsed_command='first'
        )
        plan.add_step(SnapshotPlanStep(SNAPSHOT_ACTION))
        # add the plan to our list of plans
        self.snapshot_plans.append(plan)
        self.current_height = self.saved_position.height
        self.current_layer = self.saved_position.layer
        # set the state for the next layer
        self.saved_position = None
        self.saved_position_line = None
        self.current_file_position = None
        self.is_layer_change_wait = False

    def process_position(self, current_pos, current_line):
        # if we're at a layer change, add the current saved plan
        if current_pos.is_layer_change:
            self.is_layer_change_wait = True

        if not current_pos.is_extruding:
            return

        if self.is_layer_change_wait and self.saved_position is not None:
            self.add_saved_plan()

        # check for errors in position, layer, or height, and make sure we are extruding.
        if (
            current_pos.layer == 0 or current_pos.x is None or current_pos.y is None or current_pos.z is None or
            current_pos.height is None
        ):
            return

        if self.height_increment is not None:
            # todo:  improve this check, it doesn't need to be done on every command if Z hasn't changed
            current_increment = utility.round_to_float_equality_range(current_pos.height - self.current_height)
            if current_increment < self.height_increment:
                return

        if self.is_closer(current_pos):
                # we need to make sure that we copy current_pos, because it's value will change
                # as we update the Position object
                # this was done to substantially increase performance within the position class, which
                # can take a long time to run on slower hardware.
                self.saved_position = Pos(copy_from_pos=current_pos)
                self.saved_position_line = current_line


    def is_closer(self, position):
        # check the bounding box
        if self.is_bound:
            if (
                position.x < self.x_min or
                position.x > self.x_max or
                position.y < self.y_min or
                position.y > self.y_max or
                position.z < self.z_min or
                position.z > self.z_max
            ):
                return False
        # if we have no saved position, this is the closest!
        if self.saved_position is None:
            return True

        # use a local here for speed
        saved_position = self.saved_position
        if self.nearest_to == NearestToCorner.FRONT_LEFT:
            if self.favor_x:
                if position.x > saved_position.x:
                    return False
                elif position.x < saved_position.x:
                    return True
                elif position.y < saved_position.y:
                    return True
            else:
                if position.y > saved_position.y:
                    return False
                if position.y < saved_position.y:
                    return True
                elif position.x < saved_position.x:
                    return True
        elif self.nearest_to == NearestToCorner.FRONT_RIGHT:
            if self.favor_x:
                if position.x < saved_position.x:
                    return False
                if position.x > saved_position.x:
                    return True
                elif position.y < saved_position.y:
                    return True
            else:
                if position.y > saved_position.y:
                    return False
                if position.y < saved_position.y:
                    return True
                elif position.x > saved_position.x:
                    return True
        elif self.nearest_to == NearestToCorner.BACK_LEFT:
            if self.favor_x:
                if position.x > saved_position.x:
                    return False
                if position.x < saved_position.x:
                    return True
                elif position.y > saved_position.y:
                    return True
            else:
                if position.y < saved_position.y:
                    return False
                if position.y > saved_position.y:
                    return True
                elif position.x < saved_position.x:
                    return True
        elif self.nearest_to == NearestToCorner.BACK_RIGHT:
            if self.favor_x:
                if position.x < saved_position.x:
                    return False
                if position.x > saved_position.x:
                    return True
                elif position.y > saved_position.y:
                    return True
            else:
                if position.y < saved_position.y:
                    return False
                if position.y > saved_position.y:
                    return True
                elif position.x > saved_position.x:
                    return True

        return False

