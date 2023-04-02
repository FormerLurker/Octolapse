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
import math
import uuid
import ntpath
import os
import re
import subprocess
import sys
import time
import urllib
import traceback
import threading
import json
import shutil
import errno
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
# Todo:  Determin if this is still necessary.
try:
    from slugify import Slugify
except ImportError:
    from octoprint.vendor.awesome_slugify import Slugify
_SLUGIFY = Slugify()
_SLUGIFY.safe_chars = "-_.()[] "

# create the module level logger
from octoprint_octolapse.log import LoggingConfigurator
logging_configurator = LoggingConfigurator()
logger = logging_configurator.get_logger(__name__)

from threading import Timer
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
    r"^\d+[KkMm]$", re.IGNORECASE)


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





def sanitize_filename(filename):
    if filename is None:
        return None
    if u"/" in filename or u"\\" in filename:
        raise ValueError("name must not contain / or \\")

    result = _SLUGIFY(filename).replace(u" ", u"_")
    if result and result != u"." and result != u".." and result[0] == u".":
        # hidden files under *nix
        result = result[1:]
    return result


def split_all(path):
    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path:  # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts


def get_directory_from_full_path(path):
    return os.path.dirname(path)


def get_filename_from_full_path(path):
    basename = ntpath.basename(path)
    head, tail = ntpath.split(basename)
    file_name = tail or ntpath.basename(head)
    split_filename = os.path.splitext(file_name)
    if len(split_filename) > 0:
        return split_filename[0]
    return ""


def remove_extension_from_filename(filename):
    return os.path.splitext(filename)[0]


def get_extension_from_full_path(path):
    return get_extension_from_filename(ntpath.basename(path))


def get_extension_from_filename(filename):
    head, tail = ntpath.split(filename)
    file_name = tail or ntpath.basename(head)
    split_filename = os.path.splitext(file_name)
    if len(split_filename) > 1:
        extension = split_filename[1]
        if len(split_filename) > 1:
            return extension[1:]
    return ""


def get_collision_free_filepath(path):
    filename = get_filename_from_full_path(path)
    directory = get_directory_from_full_path(path)
    extension = get_extension_from_full_path(path)

    original_filename = filename
    file_number = 0
    # Check to see if the file exists, if it does add a number to the end and continue
    while os.path.isfile(
        os.path.join(
            directory,
            "{0}.{1}".format(filename, extension)
        )
    ):
        file_number += 1
        filename = "{0}_{1}".format(original_filename, file_number)

    return os.path.join(directory, "{0}.{1}".format(filename, extension))


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


def round_to(n, precision):
    return int(n / precision + (0.5 if n >= 0 else -0.5)) * precision


def round_to_value(value, rounding_increment=0.0000001):
    return round(value / rounding_increment) * rounding_increment


def round_up(value):
    return -(-value // 1.0)


_snapshot_archive_default_directory = "snapshot_archive"


def get_default_snapshot_archive_directory_name():
    return _snapshot_archive_default_directory


_temporary_snapshot_subdirectory = "octolapse_snapshots_tmp"


def get_temporary_snapshot_directory(temporary_directory):
    return os.path.join(temporary_directory, _temporary_snapshot_subdirectory)


def get_temporary_snapshot_job_path(temporary_directory, job_guid):
    return os.path.join(
            get_temporary_snapshot_directory(temporary_directory),
            job_guid)


def get_temporary_snapshot_job_camera_path(temporary_directory, job_guid, camera_guid):
    return os.path.join(
            get_temporary_snapshot_job_path(temporary_directory, job_guid),
            camera_guid)


_temporary_rendering_subdirectory = "octolapse_rendering_tmp"


def get_temporary_rendering_directory(temporary_directory):
    return os.path.join(temporary_directory, _temporary_rendering_subdirectory)


_temporary_archive_subdirectory = "octolapse_archive_tmp"
def get_temporary_archive_directory(temporary_directory):
    return os.path.join(temporary_directory, _temporary_archive_subdirectory)


def get_temporary_archive_path(temporary_directory):
    file_name = "{0}.zip".format(uuid.uuid4())
    return os.path.join(get_temporary_archive_directory(temporary_directory), file_name)


snapshot_archive_extension = "zip"


def get_snapshot_archive_filename(rendering_filename):
    return "{0}.{1}".format(rendering_filename, snapshot_archive_extension)


no_archive_filename = "no-archive.octolapse"


def create_no_archive_file(temporary_directory, job_guid, camera_guid):
    camera_job_directory = get_temporary_snapshot_job_camera_path(temporary_directory, job_guid, camera_guid)
    # create the directory if it does not exist
    if not os.path.isdir(camera_job_directory):
        os.makedirs(camera_job_directory)

    # create the no archive file path
    no_archive_file_path = os.path.join(camera_job_directory, no_archive_filename)
    # create the file
    with open(no_archive_file_path, mode='w'):
        pass  # nothing to do, just create the file


def has_no_archive_file(temporary_directory, job_guid, camera_guid):
    camera_job_directory = get_temporary_snapshot_job_camera_path(temporary_directory, job_guid, camera_guid)
    no_archive_file_path = os.path.join(camera_job_directory, no_archive_filename)
    return os.path.isfile(no_archive_file_path)

def get_latest_snapshot_download_path(temporary_directory, camera_guid, base_folder=None):
    if (not camera_guid or camera_guid == "undefined") and base_folder:
        return get_images_download_path(base_folder, "no-camera-selected.png")
    return os.path.join(get_temporary_snapshot_directory(temporary_directory), "latest_{0}.jpeg".format(camera_guid))


def get_latest_snapshot_thumbnail_download_path(temporary_directory, camera_guid, base_folder=None):
    if (not camera_guid or camera_guid == "undefined") and base_folder:
        return get_images_download_path(base_folder, "no-camera-selected.png")
    return os.path.join(get_temporary_snapshot_directory(temporary_directory), "latest_thumb_{0}.jpeg".format(camera_guid))


def get_images_download_path(base_folder, file_name):
    return os.path.join(base_folder, "data", "Images", file_name)


def get_error_image_download_path(base_folder):
    return get_images_download_path(base_folder, "no-image-available.png")


def get_no_snapshot_image_download_path(base_folder):
    return get_images_download_path(base_folder, "no_snapshot.png")


def get_rendering_base_filename_template():
    return "{FILENAME}_{DATETIMESTAMP}"


def get_rendering_base_filename(print_name, print_start_time, print_end_time=None):
    file_template = get_rendering_base_filename_template()
    file_template = file_template.replace("{FILENAME}", get_string(print_name, ""))
    file_template = file_template.replace(
        "{DATETIMESTAMP}", time.strftime("%Y%m%d%H%M%S", time.localtime(time.time())))
    file_template = file_template.replace(
        "{PRINTSTARTTIME}",
        "UNKNOWN" if not print_start_time else time.strftime("%Y%m%d%H%M%S", time.localtime(print_start_time))
    )
    file_template = file_template.replace(
        "{PRINTENDTIME}",
        "UNKNOWN" if not print_end_time else time.strftime("%Y%m%d%H%M%S", time.localtime(print_end_time))
    )

    return file_template


snapshot_file_extensions = ["jpg"]


default_snapshot_extension = snapshot_file_extensions[0]


def is_valid_snapshot_extension(extension):
    return extension.lower() in snapshot_file_extensions


temporary_extension = "tmp"


def is_valid_temporary_extension(extension):
    return extension.lower() == temporary_extension


def get_snapshot_filename(print_name, snapshot_number):
    return "{0}{1}.{2}".format(
        print_name,
        format_snapshot_number(snapshot_number),
        default_snapshot_extension
    )


def get_pre_roll_snapshot_filename(print_name, snapshot_number):
    return "{0}{1}_{2}.{3}".format(
        print_name,
        format_snapshot_number(snapshot_number),
        format_snapshot_number(snapshot_number),
        "jpg")

SnaphotNumberDigits = 6
SnapshotNumberFormat = "%0{0}d".format(SnaphotNumberDigits)


def get_snapshot_number_from_path(path):
    try:
        if path.upper().endswith(".JPG") and len(path) > SnaphotNumberDigits + 4:
            return int(path[len(path)-SnaphotNumberDigits-4:len(path)-4])
    except ValueError:
        pass
    return -1


def format_snapshot_number(number):
    # we may get a templated field here for the snapshot number, so check to make sure it is an int first
    if isinstance(number, int):
        return SnapshotNumberFormat % number
    # not an int, return the original field
    return number


def seconds_to_hhmmss(seconds):
    hours = seconds // (60 * 60)
    seconds %= (60 * 60)
    minutes = seconds // 60
    seconds %= 60
    return "%02i:%02i:%02i" % (hours, minutes, seconds)


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


def get_system_fonts(base_directory):
    """Retrieves a list of fonts for any operating system. Note that this may not be a complete list of fonts
       discoverable on the system.
       :returns A list of filepaths to fonts available on the system."""

    font_paths = []
    font_names = set()
    # first add all of our supplied fonts
    default_font_path = os.path.join(base_directory, "data", "fonts", "DejaVu")
    logger.info("Searching for default fonts at: %s", default_font_path)
    for f in os.listdir(default_font_path):
        font_path = os.path.join(default_font_path, f)
        logger.verbose("Checking for font at path: %s", f)
        if os.path.isfile(font_path) and f.endswith(".ttf"):
            logger.debug("Found font at path: %s", f)
            font_names.add(f)
            font_paths.append(os.path.join(default_font_path, f))

    if sys.platform == "linux" or sys.platform == "linux2" or sys.platform == "darwin":
        # Linux and OS X.
        # Try 1 - fails for some
        # linux_font_paths = subprocess.check_output("fc-list --format %{file}\\n".split()).split('\n')
        # Try 2 - fails for others....
        # linux_font_paths = str(subprocess.check_output(["fc-list", "--format", "%{file}\n"]), 'UTF-8').split('\n')

        fc_list_output = subprocess.check_output(["fc-list", "--format", "%{file}\n"], universal_newlines=True)
        if isinstance(fc_list_output, bytes):
            fc_list_output = fc_list_output.decode("UTF-8")

        logger.verbose("Searching for fonts within:\n %s", fc_list_output)

        linux_font_paths = list(filter(None, fc_list_output.split('\n')))
        for f in linux_font_paths:
            logger.verbose("Checking for font at path: %s", f)
            font_name = os.path.basename(f)
            if not font_name in font_names:
                logger.debug("Font found at path: %s", f)
                font_names.add(font_name)
                font_paths.append(f)
    elif sys.platform == "win32" or sys.platform == "cygwin":
        # Windows.
        windows_font_path = os.path.join(os.environ['WINDIR'], "fonts")
        logger.info("Searching for windows fonts at: %s", windows_font_path)
        for f in os.listdir(windows_font_path):
            if f.endswith(".ttf"):
                if not f in font_names:
                    logger.debug("Font found at path: %s", f)
                    font_names.add(f)
                    font_paths.append(os.path.join(os.environ['WINDIR'], "fonts", f))
    else:
        logger.info("Don't know how to search for fonts on a Mac, sorry.")
        pass

    # sort the fonts
    font_paths.sort(key=(lambda b: os.path.basename(b).lower()))
    return font_paths


def get_directory_size(root, recurse=False):
    total_size = 0
    try:
        if not os.path.isdir(root):
            return 0
        for name in os.listdir(root):
            file_path = os.path.join(root, name)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
            elif recurse and os.path.isdir(file_path):
                total_size += get_directory_size(file_path, recurse)
    except EnvironmentError as e:
        if e.errno != errno.ENOENT:
            raise
        logger.exception(e)
    return total_size


def get_file_creation_date(path):
    if sys.platform == "win32":
        # getctime always returns the creation date of a file, exactly what we want.
        # in Linux this could be the st_ctime, which is always later than or equal to the
        # modification date, so only trust this for windows.
        return os.path.getctime(path)
    # get file statistics
    stat = os.stat(path)
    if hasattr(stat, 'st_birthtime'):
        # Not all OSs support st_birthtime, which is an actual creation date
        return stat.st_birthtime

    # for any other OS get the last content modification date.
    return stat.st_mtime


# MUCH faster than the standard shutil.copy
def fast_copy(src, dst, buffer_size=1024 * 1024 * 1):
    #    Optimize the buffer for small files
    file_size = os.path.getsize(src)

    buffer_size = min(buffer_size, file_size)
    if buffer_size == 0:
        buffer_size = 1024

    with open(src, 'rb') as fin:
        with open(dst, 'wb') as fout:
            shutil.copyfileobj(fin, fout, buffer_size)


# function to walk a directory and return all contained subdirectories
def walk_directories(root):
    for name in os.listdir(root):
        if os.path.isdir(os.path.join(root, name)):
            yield name


# an iterable function to walk all files in a given directory and return a list of files with metadata
def walk_files(root, filter_function=None):
    '''Iterable function, returns a list of dicts, each including name, extension, size, and date (creation date if
    possible, else modified date)).  Can be filtered to only include files with extensions in the provided set. '''
    for name in os.listdir(root):
        file_path = os.path.join(root, name)
        if os.path.isfile(file_path):
            extension = get_extension_from_filename(name)

            if filter_function and not filter_function(root, name, extension):
                continue
            yield {
                'name': name,
                'extension': extension,
                'size': os.path.getsize(file_path),
                'date': get_file_creation_date(file_path)
            }


FILE_TYPE_SNAPSHOT_ARCHIVE = "snapshot_archive"
FILE_TYPE_TIMELAPSE_OCTOLAPSE = "timelapse_octolapse"
FILE_TYPE_TIMELAPSE_OCTOPRINT = "timelapse_octoprint"


def get_file_info(file_path):
    name = os.path.basename(file_path)
    extension = get_extension_from_filename(name)
    return {
        'name': name,
        'extension': extension,
        'size': os.path.getsize(file_path) if os.path.isfile(file_path) else 0,
        'date': get_file_creation_date(file_path)
    }


# Handle windows specific stuff (TODO: need to move other code here too)
def is_windows():
    return sys.platform.startswith('win')


# Handle windows errors that do not exist on Linux (why???)
# Windows Exceptions in Linux
try:
    from exceptions import WindowsError
except ImportError:
    class WindowsError(OSError): pass


ERROR_WINDOWS_DIRECTORY_NOT_EMPTY = 145
ERROR_WINDOWS_DIRECTORY_NOT_EMPTY_RETRIES = 10
ERROR_WINDOWS_DIRECTORY_NOT_EMPTY_RETRY_MS = 1.0/1000.0


def rmtree(path):
    """
    Windows doesn't seem to be able to reliably immediately delete a path.  It often works after waiting
    for a small amount of time.  I added retry to this function so that it works more reliably on windows.
    :param path:
    :return:
    """
    num_tries = 0
    while True:
        try:
            shutil.rmtree(path)
            break
        except WindowsError as e:
            if not e.winerror != ERROR_WINDOWS_DIRECTORY_NOT_EMPTY:
                raise e
            num_tries += 1
            if num_tries < ERROR_WINDOWS_DIRECTORY_NOT_EMPTY_RETRIES:
                time.sleep(ERROR_WINDOWS_DIRECTORY_NOT_EMPTY_RETRY_MS)
            else:
                raise e


ERROR_WINDOWS_FILE_IS_IN_USE = 32
ERROR_WINDOWS_FILE_IS_IN_USE_RETRIES = 10
ERROR_WINDOWS_FILE_IS_IN_USE_RETRY_SECONDS = 1.0/1000.0


def remove(path):
    """For some reason closed files are sometimes open if you try to remove them immediately after a file operation.
       This happens occationally when using Pillow to save images.  I added this function so that windows can retry
       a delete before failing with an exception.
    """
    num_tries = 0
    while True:
        try:
            os.remove(path)
            break
        except WindowsError as e:
            if e.winerror != ERROR_WINDOWS_FILE_IS_IN_USE:
                raise e
            num_tries += 1
            if num_tries < ERROR_WINDOWS_FILE_IS_IN_USE_RETRIES:
                time.sleep(ERROR_WINDOWS_FILE_IS_IN_USE_RETRY_SECONDS)
            else:
                raise e

def move(src, dst):
    """For some reason closed files are sometimes open if you try to remove them immediately after a file operation.
       This happens occationally when using Pillow to save images.  I added this function so that windows can retry
       a delete before failing with an exception.
    """
    num_tries = 0
    while True:
        try:
            shutil.move(src, dst)
            break
        except WindowsError as e:
            if e.winerror != ERROR_WINDOWS_FILE_IS_IN_USE:
                raise e
            num_tries += 1
            if num_tries < ERROR_WINDOWS_FILE_IS_IN_USE_RETRIES:
                time.sleep(ERROR_WINDOWS_FILE_IS_IN_USE_RETRY_SECONDS)
            else:
                raise e


class TimelapseJobInfo(object):
    timelapse_info_file_name = "timelapse_info.json"

    @staticmethod
    def is_timelapse_info_file(file_name):
        return file_name.lower() == TimelapseJobInfo.timelapse_info_file_name

    def __init__(
        self, job_info=None, job_guid=None, print_start_time=None, print_end_time=None,
        print_end_state="INCOMPLETE", print_file_name="UNKNOWN", print_file_extension=None
     ):
        if job_info is None:
            self.JobGuid = None if job_guid is None else "{}".format(job_guid)
            self.PrintStartTime = print_start_time
            self.PrintEndTime = print_end_time
            self.PrintEndState = print_end_state
            self.PrintFileName = print_file_name
            self.PrintFileExtension = print_file_extension
        else:
            self.JobGuid = job_info.JobGuid
            self.PrintStartTime = job_info.PrintStartTime
            self.PrintEndTime = job_info.PrintEndTime
            self.PrintEndState = job_info.PrintEndState
            self.PrintFileName = job_info.PrintFileName
            self.PrintFileExtension = job_info.PrintFileExtension

    @staticmethod
    def load(data_folder, print_job_guid, camera_guid=None):
        file_directory = get_temporary_snapshot_job_path(data_folder, print_job_guid)
        file_path = os.path.join(file_directory, TimelapseJobInfo.timelapse_info_file_name)
        try:
            with open(file_path, 'r') as timelapse_info:
                data = json.load(timelapse_info)
                return TimelapseJobInfo.from_dict(data)
        except (OSError, IOError, ValueError) as e:
            logger.exception("Unable to load TimelapseJobInfo from %s.", file_path)
            info = TimelapseJobInfo()
            info.PrintEndState = "UNKNOWN"
            info.JobGuid = print_job_guid
            if camera_guid is not None:
                snapshot_path = os.path.join(file_directory, camera_guid)
                if os.path.exists(snapshot_path):
                    # look for a jpg from which to extract the print name
                    for name in os.listdir(snapshot_path):
                        camera_file_path = os.path.join(snapshot_path, name)
                        extension = get_extension_from_filename(name)

                        if (
                            os.path.isfile(camera_file_path) and
                            is_valid_snapshot_extension(extension) and
                            name.endswith(".{0}".format(extension))
                        ):
                            if len(name) > 10:
                                test_image_number_string = name[len(name)-10:len(name)-4]
                                try:
                                    int(test_image_number_string)
                                    info.PrintFileName = name[0:len(name)-10]
                                    break
                                except ValueError:
                                    pass
                            info.PrintFileName = name[0:len(name) - 4]
                            break
            return info

    def save(self, temporary_directory):
        file_directory = get_temporary_snapshot_job_path(temporary_directory, self.JobGuid)
        file_path = os.path.join(file_directory, TimelapseJobInfo.timelapse_info_file_name)
        if not os.path.exists(file_directory):
            os.makedirs(file_directory)
        with open(file_path, 'w') as timelapse_info:
            json.dump(self.to_dict(), timelapse_info)

    def to_dict(self):
        return {
            "job_guid": self.JobGuid,
            "print_start_time": self.PrintStartTime,
            "print_end_time": self.PrintEndTime,
            "print_end_state": self.PrintEndState,
            "print_file_name": self.PrintFileName,
            "print_file_extension": self.PrintFileExtension
        }

    @staticmethod
    def from_dict(dict_obj):
        return TimelapseJobInfo(
            job_guid=dict_obj["job_guid"],
            print_start_time=dict_obj["print_start_time"],
            print_end_time=dict_obj["print_end_time"],
            print_end_state=dict_obj["print_end_state"],
            print_file_name=dict_obj["print_file_name"],
            print_file_extension=dict_obj["print_file_extension"],
        )


if sys.version_info < (3, 0):
    def unquote(value):
        return urllib.unquote(value)
else:
    def unquote(value):
        return urllib.parse.unquote(value)


class RecurringTimerThread(threading.Thread):
    def __init__(self, interval_seconds, callback, cancel_event, first_run_delay_seconds=None):
        threading.Thread.__init__(self)
        self._interval_seconds = interval_seconds
        self._callback = callback
        self._cancel_event = cancel_event
        self._trigger = threading.Event()
        self._first_run_delay_seconds = first_run_delay_seconds

    def run(self):
        if self._first_run_delay_seconds is not None:
            time.sleep(self._first_run_delay_seconds)
            self._callback()
        while not self._cancel_event.wait(self._interval_seconds):
            self._callback()


class SafeDict(dict):
    def __missing__(self, key):
        return '{' + key + '}'


# retry utility adapted from https://www.peterbe.com/plog/best-practice-with-retries-with-requests
def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


class JsonSerializable(object):

    def __str__(self):
        return json.dumps(self, default=JsonSerializable.json_dumper,
                          sort_keys=True)

    @staticmethod
    def json_dumper(obj):
        to_json = getattr(obj, "to_json", None)
        if callable(to_json):
            return obj.to_json()
        to_dict = getattr(obj, "to_dict", None)
        if callable(to_dict):
            return obj.to_dict()
        return obj.__dict__

