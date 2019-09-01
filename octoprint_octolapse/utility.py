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
from __future__ import unicode_literals
import math
import ntpath
import os
import re
import subprocess
import sys
import time
import traceback
import threading
import psutil
from threading import Timer

# create the module level logger
from octoprint_octolapse.log import LoggingConfigurator
logging_configurator = LoggingConfigurator()
logger = logging_configurator.get_logger(__name__)


FLOAT_MATH_EQUALITY_RANGE = 0.0000001

def get_float(value, default):
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return float(default)


def get_nullable_float(value, default):
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        if default is None:
            return None
        return float(default)


def get_int(value, default):
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_bool(value, default):
    if value is None:
        return default
    try:
        return bool(value)
    except ValueError:
        return default


def get_string(value, default):
    if value is not None and len(value) > 0:
        return value
    return default


# global for bitrate regex
octoprint_ffmpeg_bitrate_regex = re.compile(
    "^\d+[KkMm]$", re.IGNORECASE)


def get_bitrate(value, default):
    if value is None:
        return default
    matches = octoprint_ffmpeg_bitrate_regex.match(value)
    if matches is None:
        return default
    return value


def is_sequence(arg):
    return (not hasattr(arg, "strip") and
            hasattr(arg, "__getitem__") or
            hasattr(arg, "__iter__"))


def get_filename_from_full_path(path):

    basename = ntpath.basename(path)
    head, tail = ntpath.split(basename)
    file_name = tail or ntpath.basename(head)
    return os.path.splitext(file_name)[0]


def greater_than_or_close(a, b, abs_tol):
    return a - b > abs_tol


def greater_than(a, b):
    return a - b > FLOAT_MATH_EQUALITY_RANGE


def less_than(a, b):
    return b - a > FLOAT_MATH_EQUALITY_RANGE


def less_than_or_equal(a, b):
    return a < b or is_equal(a, b)


def greater_than_or_equal(a, b):
    return a > b or is_equal(a, b)


def is_equal(a,b):
    return a - b < FLOAT_MATH_EQUALITY_RANGE

def less_than_or_close(a, b, abs_tol):
    return a - b < abs_tol


def is_approximately_zero(a):
    return abs(a) <= FLOAT_MATH_EQUALITY_RANGE


def is_close(a, b, abs_tol=0.01000):
    return abs(a - b) <= abs_tol


def round_to_float_equality_range(n):
    return (n * 10000000 + 0.00000005)//1 / 10000000.0
    #return round(n / 0.0000001) * 0.0000001
    #answer = math.floor(n*10000000)/10000000 if n > 0 else math.ceil(n*10000000)/10000000
    return round(n,8)

    #return answer
    # slow - return round(n,6)


def round_to(n, precision):
    return int(n / precision + (0.5 if n >= 0 else -0.5)) * precision


def round_to_value(value, rounding_increment=0.0000001):
    return round(value / rounding_increment) * rounding_increment


def round_up(value):
    return -(-value // 1.0)


def get_temp_snapshot_driectory_template():
    return "{0}{1}{2}{3}".format("{DATADIRECTORY}", os.sep, "tempsnapshots", os.sep)


def get_snapshot_directory(data_directory):
    return "{0}{1}{2}{3}".format(data_directory, os.sep, "snapshots", os.sep)


def get_snapshot_filename_template():
    return os.path.join("{FILENAME}")


def get_rendering_directory_from_data_directory(data_directory):
    return get_rendering_directory_template().replace("{DATADIRECTORY}", data_directory)


def get_latest_snapshot_download_path(data_directory, camera_guid, base_folder=None):
    if not camera_guid or camera_guid == "undefined" and base_folder :
        return get_images_download_path(base_folder, "no-camera-selected.png")
    return "{0}{1}".format(get_snapshot_directory(data_directory), "latest_{0}.jpeg".format(camera_guid))


def get_latest_snapshot_thumbnail_download_path(data_directory, camera_guid, base_folder=None):
    if not camera_guid or camera_guid == "undefined" and base_folder :
        return get_images_download_path(base_folder, "no-camera-selected.png")
    return "{0}{1}".format(get_snapshot_directory(data_directory), "latest_thumb_{0}.jpeg".format(camera_guid))


def get_images_download_path(base_folder, file_name):
    return "{0}{1}data{2}{3}{4}{5}".format(base_folder, os.sep, os.sep, "Images", os.sep, file_name)


def get_error_image_download_path(base_folder):
    return get_images_download_path(base_folder, "no-image-available.png")


def get_no_snapshot_image_download_path(base_folder):
    return get_images_download_path(base_folder, "no_snapshot.png")


def get_rendering_directory_template():
    return "{0}{1}{2}{3}".format("{DATADIRECTORY}", os.sep, "timelapses", os.sep)


def get_rendering_base_filename_template():
    return "{FILENAME}_{DATETIMESTAMP}"


def get_rendering_filename(template, tokens):
    template.format(**tokens)


def get_rendering_base_filename(print_name, print_start_time, print_end_time=None):
    file_template = get_rendering_base_filename_template()
    file_template = file_template.replace("{FILENAME}", get_string(print_name, ""))
    file_template = file_template.replace(
        "{DATETIMESTAMP}", time.strftime("%Y%m%d%H%M%S", time.localtime(time.time())))
    file_template = file_template.replace(
        "{PRINTSTARTTIME}", time.strftime("%Y%m%d%H%M%S", time.localtime(print_start_time)))
    if print_end_time is not None:
        file_template = file_template.replace(
            "{PRINTENDTIME}", time.strftime("%Y%m%d%H%M%S", time.localtime(print_end_time)))

    return file_template


def get_snapshot_filename(print_name, print_start_time, snapshot_number):
    file_template = get_snapshot_filename_template() \
        .format(FILENAME=get_string(print_name, ""),
                DATETIMESTAMP="{0:d}".format(math.trunc(round(time.time(), 2) * 100)),
                PRINTSTARTTIME="{0:d}".format(math.trunc(round(print_start_time, 2) * 100)))
    return "{0}{1}.{2}".format(file_template, format_snapshot_number(snapshot_number), "jpg")

def get_pre_roll_snapshot_filename(print_name, print_start_time, snapshot_number):
    file_template = get_snapshot_filename_template() \
        .format(FILENAME=get_string(print_name, ""),
                DATETIMESTAMP="{0:d}".format(math.trunc(round(time.time(), 2) * 100)),
                PRINTSTARTTIME="{0:d}".format(math.trunc(round(print_start_time, 2) * 100)))
    return "{0}{1}_{2}.{3}".format(
        file_template,
        format_snapshot_number(snapshot_number),
        format_snapshot_number(snapshot_number),
        "jpg")

SnapshotNumberFormat = "%06d"


def format_snapshot_number(number):
    # we may get a templated field here for the snapshot number, so check to make sure it is an int first
    if isinstance(number, int):
        return SnapshotNumberFormat % number
    # not an int, return the original field
    return number


def get_snapshot_temp_directory(data_directory):
    directory_template = get_temp_snapshot_driectory_template()
    directory_template = directory_template.replace(
        "{DATADIRECTORY}", data_directory)

    return directory_template


def get_rendering_directory(data_directory, print_name, print_start_time, output_extension, print_end_time=None):
    directory_template = get_rendering_directory_template()
    directory_template = directory_template.replace(
        "{FILENAME}", get_string(print_name, ""))
    directory_template = directory_template.replace(
        "{OUTPUTFILEEXTENSION}", get_string(output_extension, ""))
    directory_template = directory_template.replace("{PRINTSTARTTIME}",
                                                    "{0:d}".format(math.trunc(round(print_start_time, 2) * 100)))
    if print_end_time is not None:
        directory_template = directory_template.replace("{PRINTENDTIME}",
                                                        "{0:d}".format(math.trunc(round(print_end_time, 2) * 100)))
    directory_template = directory_template.replace(
        "{DATADIRECTORY}", data_directory)

    return directory_template


def seconds_to_hhmmss(seconds):
    hours = seconds // (60 * 60)
    seconds %= (60 * 60)
    minutes = seconds // 60
    seconds %= 60
    return "%02i:%02i:%02i" % (hours, minutes, seconds)

class SafeDict(dict):
    def __missing__(self, key):
        return '{' + key + '}'

def get_currently_printing_file_path(octoprint_printer):
    if octoprint_printer is not None:
        current_job = octoprint_printer.get_current_job()
        if current_job is not None and "file" in current_job:
            current_job_file = current_job["file"]
            if "path" in current_job_file and "origin" in current_job_file:
                return current_job_file["path"]
    return None


def get_currently_printing_filename(octoprint_printer):
    file_path = get_currently_printing_file_path(octoprint_printer)
    if file_path is not None:
        return get_filename_from_full_path(file_path)
    return ""

# not sure if we need this
# def offset_position_to_coordinate(offset_position, offset):
#     if offset_position is None or offset is None:
#         return None
#     return offset_position + offset

# This function is only used in test code for the time being.  Need to reexamine G92
# to correct issues with the out of bounds detection.
def coordinate_to_offset_position(coordinate, offset):
    if coordinate is None or offset is None:
        return None
    return coordinate - offset


def is_in_bounds(bounding_box, x, y, z):
    # Determines if the given X,Y,Z coordinate is within
    # the bounding box of the printer, as determined by
    # the octoprint configuration
    # if no coordinates are give, return false
    if x is None and y is None and z is None:
        return False
    x_in_bounds = x is None or bounding_box['min_x'] <= x <= bounding_box['max_x']
    y_in_bounds = y is None or bounding_box['min_y'] <= y <= bounding_box['max_y']
    z_in_bounds = z is None or bounding_box['min_z'] <= z <= bounding_box['max_z']
    return x_in_bounds and y_in_bounds and z_in_bounds


def get_closest_in_bounds_position(bounding_box, x=None, y=None, z=None):
    # Todo:  Make sure circular beds work

    if bounding_box["bed_type"] == 'rectangular':
        min_x = bounding_box['min_x']
        max_x = bounding_box['max_x']
        min_y = bounding_box['min_y']
        max_y = bounding_box['max_y']
        min_z = bounding_box['min_z']
        max_z = bounding_box['max_z']

        def clamp(v, v_min, v_max):
            """Limits a value to lie between (or equal to) v_min and v_max."""
            return None if v is None else min(max(v, v_min), v_max)

        c_x = clamp(x, min_x, max_x)
        c_y = clamp(y, min_y, max_y)
        c_z = clamp(z, min_z, max_z)

        return {'X': c_x, 'Y': c_y, 'Z': c_z}
    else:
        raise ValueError("We've not implemented circular bed stuff yet!")


def is_snapshot_command(command_string, snapshot_command):
    # note that self.Printer.snapshot_command is stripped of comments.
    if snapshot_command is not None and len(snapshot_command)>0:
        return command_string.lower() == snapshot_command.lower()
    return False


def get_intersections_circle(x1, y1, x2, y2, c_x, c_y, c_radius):
    # Finds any intersections as well as the closest point on or within the circle to the center (cx, cy)
    intersections = []
    closest = False

    segment_length = math.sqrt(math.pow(x1 - x2, 2) + math.pow(y1 - y2, 2))

    # create direction vector
    if segment_length != 0:
        vector_x = (x2 - x1) / segment_length
        vector_y = (y2 - y1) / segment_length
    else:
        vector_x = 0
        vector_y = 0

    # compute the value t of the closest point to the circle center (cx, cy)
    t = (vector_x * (c_x - x1)) + (vector_y * (c_y - y1))

    # compute the coordinates of the point closest to c
    closest_x = (t * vector_x) + x1
    closest_y = (t * vector_y) + y1

    # get the distance from c
    closest_to_c_dist = math.sqrt(math.pow(closest_x - c_x, 2) + math.pow(closest_y - c_y, 2))

    # is closest within the circle?
    if closest_to_c_dist <= c_radius:
        closest = [closest_x, closest_y]

    # If the closest point is inside the circle (but not on)
    if closest_to_c_dist < c_radius:
        # Distance from closest point to intersection
        intersect_dist = math.sqrt(math.pow(c_radius, 2) - math.pow(closest_to_c_dist, 2))

        # calculate intersection 1
        intersection_1_x = ((t - intersect_dist) * vector_x) + x1
        intersection_1_y = ((t - intersect_dist) * vector_y) + y1
        # does intersection 1 exist
        if(
            math.sqrt(math.pow(x1 - intersection_1_x, 2) + math.pow(y1 - intersection_1_y, 2)) +
            math.sqrt(math.pow(intersection_1_x - x2, 2) + math.pow(intersection_1_y - y2, 2))
            == segment_length
        ):
            intersections.append([intersection_1_x,intersection_1_y])

        # calculate intersection 2
        intersection_2_x = ((t + intersect_dist) * vector_x) + x1
        intersection_2_y = ((t + intersect_dist) * vector_y) + y1
        # does intersection 2 exist
        if(
            math.sqrt(math.pow(x1 - intersection_2_x, 2) + math.pow(y1 - intersection_2_y, 2)) +
            math.sqrt(math.pow(intersection_2_x - x2, 2) + math.pow(intersection_2_y - y2, 2))
            == segment_length
        ):
            intersections.append([intersection_2_x, intersection_2_y])

    if len(intersections) == 0 and closest:
        # make sure closest is on the radius
        a = closest[0] - c_x
        b = closest[1] - c_y
        r = math.sqrt(pow(a, 2) + pow(b, 2))
        if r == c_radius:
            intersections.append(closest)

    if len(intersections) == 0:
        return False

    return intersections


def get_intersections_rectangle(x1, y1, x2, y2, rect_x1, rect_y1, rect_x2, rect_y2):

    left = rect_x1 if rect_x1 < rect_x2 else rect_x2
    right = rect_x2 if rect_x1 < rect_x2 else rect_x1
    bottom = rect_y1 if rect_y1 < rect_y2 else rect_y2
    top = rect_y2 if rect_y1 < rect_y2 else rect_y1

    t0 = 0.0
    t1 = 1.0
    dx = x2 - x1 * 1.0
    dy = y2 - y1 * 1.0

    # if the points aren't fully outside or on the rect, return false
    if (
        left < x1 < right and
        left < x2 < right and
        bottom < y1  < top and
        bottom < y2 < top
    ):
        return False

    for edge in range(0, 4):
        p=None
        q=None
        if edge == 0:
            p = -dx
            q = -(left - x1)
        elif edge == 1:
            p = dx
            q = right - x1
        elif edge == 2:
            p = -dy
            q = -(bottom - y1)
        elif edge == 3:
            p = dy
            q = top - y1

        if p == 0 and q < 0:
            return False

        if p != 0:
            r = q / (p * 1.0)
            if p < 0:
                if r > t1:
                    return False
                elif r > t0:
                    t0 = r
            else:
                if r < t0:
                    return False
                elif r < t1:
                    t1 = r

    intersections = []
    intersection_x1 = x1 + t0 * dx
    intersection_y1 = y1 + t0 * dy
    intersection_x2 = x1 + t1 * dx
    intersection_y2 = y1 + t1 * dy

    if not(left < intersection_x1 < right and bottom < intersection_y1 < top):
        intersections.append([intersection_x1, intersection_y1])
    if not(left < intersection_x2 < right and bottom < intersection_y2 < top):
        intersections.append([intersection_x2, intersection_y2])

    if len(intersections) > 0:
        return intersections
    else:
        return False


def exception_to_string(e):
    trace_back = sys.exc_info()[2]
    if trace_back is None:
        return "{}".format(e)
    tb_lines = traceback.format_exception(e.__class__, e, trace_back)
    return ''.join(tb_lines)


def get_system_fonts(base_directory):
    """Retrieves a list of fonts for any operating system. Note that this may not be a complete list of fonts discoverable on the system.
    :returns A list of filepaths to fonts available on the system."""

    font_paths = []
    font_names = set()
    # first add all of our supplied fonts
    default_font_path = os.path.join(base_directory, "data", "fonts", "DejaVu")
    for f in os.listdir(default_font_path):
        if f.endswith(".ttf"):
            font_names.add(f)
            font_paths.append(os.path.join(default_font_path, f))

    if sys.platform == "linux" or sys.platform == "linux2" or sys.platform == "darwin":
        # Linux and OS X.
        linux_font_paths = subprocess.check_output("fc-list --format %{file}\\n".split()).split('\n')
        for f in linux_font_paths:
            font_name = os.path.basename(f)
            if not font_name in font_names:
                font_names.add(f)
                font_paths.append(f)
    elif sys.platform == "win32" or sys.platform == "cygwin":
        # Windows.
        for f in os.listdir(os.path.join(os.environ['WINDIR'], "fonts")):
            if f.endswith(".ttf"):
                if not f in font_names:
                    font_names.add(f)
                    font_paths.append(os.path.join(os.environ['WINDIR'], f))
    else:
        raise NotImplementedError('Unsupported operating system.')

    def sort_fonts(a, b):
        a_name = os.path.basename(a).lower()
        b_name = os.path.basename(b).lower()
        if a_name > b_name:
            return 1
        elif a_name == b_name:
            return 0
        else:
            return -1
    # sort the fonts
    font_paths.sort(sort_fonts)
    return font_paths



class POpenWithTimeout(object):
    class ProcessError(Exception):
        def __init__(self, error_type, message, cause=None):
            super(POpenWithTimeout.ProcessError, self).__init__()
            self.error_type = error_type
            self.cause = cause if cause is not None else None
            self.message = message

        def __str__(self):
            if self.cause is None:
                return "{}: {}".format(self.error_type, self.message)
            if isinstance(self.cause, list):
                if len(self.cause) > 1:
                    error_string = "{}: {} - Inner Exceptions".format(self.error_type, self.message)
                    error_count = 1
                    for cause in self.cause:
                        error_string += "\n    {}: {} Exception - {}".format(error_count, type(cause).__name__, cause)
                        error_count += 1
                    return error_string
                elif len(self.cause) == 1:
                    return "{}: {} - Inner Exception: {}".format(self.error_type, self.message, self.cause[0])
            return "{}: {} - Inner Exception: {}".format(self.error_type, self.message, self.cause)

    lock = threading.Lock()

    def __init__(self):
        self.proc = None
        self.stdout = ''
        self.stderr = ''
        self.completed = False
        self.exception = None
        self.subprocess_kill_exceptions = []
        self.kill_exceptions = None

    def kill(self):
            if self.proc is None:
                return
            try:
                process = psutil.Process(self.proc.pid)
                for proc in process.children(recursive=True):
                    try:
                        proc.kill()
                    except psutil.NoSuchProcess:
                        # the process must have completed
                        pass
                    except (psutil.Error,psutil.AccessDenied, psutil.ZombieProcess) as e:
                        self.kill_exceptions.append(e)
                process.kill()
            except psutil.NoSuchProcess:
                # the process must have completed
                pass
            except (psutil.Error, psutil.AccessDenied, psutil.ZombieProcess) as e:
                self.kill_exceptions = e

    def get_exceptions(self):
        if (
            self.exception is None
            and (self.subprocess_kill_exceptions is None or len(self.subprocess_kill_exceptions) == 0)
            and self.kill_exceptions is None
        ):
            return None
        causes = []
        error_type = None
        error_message = None
        if self.exception is not None:
            error_type = 'script-execution-error'
            error_message = 'An error occurred curing the execution of a custom script.'
            causes.append(self.exception)
        if self.kill_exceptions is not None:
            if error_type is None:
                error_type = 'script-kill-error'
                error_message = 'A custom script timed out, and an error occurred while terminating the process.'
            causes.append(self.kill_exceptions)
        if len(self.subprocess_kill_exceptions) > 0:
            if error_type is None:
                error_type = 'script-subprocess-kill-error'
                error_message = 'A custom script timed out, and an error occurred while terminating one of its ' \
                                'subprocesses.'
            for cause in self.subprocess_kill_exceptions:
                causes.append(cause)

        return POpenWithTimeout.ProcessError(
            error_type,
            error_message,
            cause=causes)

    # run a command with the provided args, timeout in timeout_seconds
    def run(self, args, timeout_seconds):

        # Create, start and run the process and fill in stderr and stdout
        def execute_process(args):
            # get the lock so that we can start the process without encountering a timeout
            self.lock.acquire()
            try:
                # don't start the process if we've already timed out
                if not self.completed:
                    self.proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                else:
                    return
            except (OSError, subprocess.CalledProcessError) as e:
                self.exception = e
                self.completed = True
                (exc_stdout, exc_stderr) = self.proc.communicate()
                self.stdout = exc_stdout
                self.stderr = exc_stderr
                return
            finally:
                self.lock.release()

            (t_stdout, t_stderr) = self.proc.communicate()
            self.lock.acquire()
            try:
                if not self.completed:
                    self.stdout = t_stdout
                    self.stderr = t_stderr
                    self.completed = True
            finally:
                self.lock.release()

        thread = threading.Thread(target=execute_process, args=[args])
        # start the thread
        thread.start()
        # join the thread with a timeout
        thread.join(timeout=timeout_seconds)
        # check to see if the thread is alive
        if thread.is_alive():
            self.lock.acquire()
            try:
                if not self.completed:
                    if self.proc is not None:
                        self.kill()
                        (p_stdout, p_stderr) = self.proc.communicate()
                        self.stdout = p_stdout
                        self.stderr = p_stderr + '- The snapshot script timed out in {0} seconds.'.format(timeout_seconds)
                    self.completed = True
            except AttributeError:
                # It's possible that the process is killed AFTER we check for self.proc is None
                # catch that here and pass
                pass
            finally:
                self.lock.release()


        if self.proc is not None:
            # raise any exceptions that were caught
            exceptions = self.get_exceptions()
            if exceptions is not None:
                raise exceptions
            return self.proc.returncode
        else:
            self.stderr = 'The process does not exist'
            return -100

def run_command_with_timeout(args, timeout_sec):
    """Execute `cmd` in a subprocess and enforce timeout `timeout_sec` seconds.
    Return subprocess exit code on natural completion of the subprocess.
    Raise an exception if timeout expires before subprocess completes."""


    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if timeout_sec is not None:
        timer = Timer(timeout_sec, proc.kill)

        try:
            timer.start()
            (stdout, stderr) = proc.communicate()
        finally:
            timer.cancel()
    else:
        (stdout, stderr) = proc.communicate()
    # Process completed naturally - return exit code
    return proc.returncode, stdout, stderr


class TimelapseJobInfo(object):
    def __init__(
        self, job_info=None, job_guid=None, print_start_time=None, print_end_time=None,
        print_end_state=None, print_file_name=None
     ):
        if job_info is None:
            self.JobGuid = "{}".format(job_guid)
            self.PrintStartTime = print_start_time
            self.PrintEndTime = print_end_time
            self.PrintEndState = print_end_state
            self.PrintFileName = print_file_name

        else:
            self.JobGuid = job_info.JobGuid
            self.PrintStartTime = job_info.PrintStartTime
            self.PrintEndTime = job_info.PrintEndTime
            self.PrintEndState = job_info.PrintEndState
            self.PrintFileName = job_info.PrintFileName


class RecurringTimerThread(threading.Thread):
    def __init__(self, interval_seconds, callback, cancel_event):
        threading.Thread.__init__(self)
        self.interval_seconds = interval_seconds
        self.callback = callback
        self.stopped = cancel_event

    def run(self):
        while not self.stopped.wait(self.interval_seconds):
            self.callback()
