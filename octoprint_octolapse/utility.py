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

import math
import ntpath
import os
import re
import subprocess
import sys
import time
import traceback

FLOAT_MATH_EQUALITY_RANGE = 0.000001


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


def is_close(a, b, abs_tol=0.01000):
    return abs(a - b) <= abs_tol


def round_to(n, precision):
    correction = 0.5 if n >= 0 else -0.5
    return int(n / precision + correction) * precision


def get_temp_snapshot_driectory_template():
    return "{0}{1}{2}{3}".format("{DATADIRECTORY}", os.sep, "tempsnapshots", os.sep)


def get_snapshot_directory(data_directory):
    return "{0}{1}{2}{3}".format(data_directory, os.sep, "snapshots", os.sep)


def get_snapshot_filename_template():
    return os.path.join("{FILENAME}_{PRINTSTARTTIME}", "{FILENAME}")


def get_rendering_directory_from_data_directory(data_directory):
    return get_rendering_directory_template().replace("{DATADIRECTORY}", data_directory)


def get_latest_snapshot_download_path(data_directory):
    return "{0}{1}".format(get_snapshot_directory(data_directory), "latest_snapshot.jpeg")


def get_latest_snapshot_thumbnail_download_path(data_directory):
    return "{0}{1}".format(get_snapshot_directory(data_directory), "latest_snapshot_thumbnail_300px.jpeg")


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


# class SafeDict(dict):
#     def __init__(self, **entries):
#         super(SafeDict, self).__init__(**entries)
#         self.__dict__.update(entries)
#         index = 0
#
#         for key in self.keys():
#             self.keys[index] = str(key)
#             index += 1
#
#     def __missing__(self, key):
#         return '{' + key + '}'


def get_currently_printing_filename(octoprint_printer):
    if octoprint_printer is not None:
        current_job = octoprint_printer.get_current_job()
        if current_job is not None and "file" in current_job:
            current_job_file = current_job["file"]
            if "path" in current_job_file and "origin" in current_job_file:
                current_file_path = current_job_file["path"]
                if current_file_path is not None:
                    return get_filename_from_full_path(current_file_path)
    return ""


def is_in_bounds(bounding_box, x=None, y=None, z=None):
    # Determines if the given X,Y,Z coordinate is within
    # the bounding box of the printer, as determined by
    # the octoprint configuration
    # if no coordinates are give, return false
    if x is None and y is None and z is None:
        return False

    min_x = bounding_box['min_x']
    max_x = bounding_box['max_x']
    min_y = bounding_box['min_y']
    max_y = bounding_box['max_y']
    min_z = bounding_box['min_z']
    max_z = bounding_box['max_z']

    x_in_bounds = x is None or min_x <= x <= max_x
    y_in_bounds = y is None or min_y <= y <= max_y
    z_in_bounds = z is None or min_z <= z <= max_z

    return x_in_bounds and y_in_bounds and z_in_bounds


def get_closest_in_bounds_position(bounding_box, x=None, y=None, z=None):
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


def get_bounding_box(octolapse_printer_profile, octoprint_printer_profile):
    # get octolapse min and max
    if octolapse_printer_profile.override_octoprint_print_volume:
        min_x = octolapse_printer_profile.min_x
        max_x = octolapse_printer_profile.max_x
        min_y = octolapse_printer_profile.min_y
        max_y = octolapse_printer_profile.max_y
        min_z = octolapse_printer_profile.min_z
        max_z = octolapse_printer_profile.max_z
    else:
        volume = octoprint_printer_profile["volume"]
        custom_box = volume["custom_box"]
        # see if we have a custom bounding box
        if custom_box:
            min_x = custom_box["x_min"]
            max_x = custom_box["x_max"]
            min_y = custom_box["y_min"]
            max_y = custom_box["y_max"]
            min_z = custom_box["z_min"]
            max_z = custom_box["z_max"]
        else:
            min_x = 0
            max_x = volume["width"]
            min_y = 0
            max_y = volume["depth"]
            min_z = 0
            max_z = volume["height"]

    return {
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y,
        "min_z": min_z,
        "max_z": max_z
    }


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
        closest = [closest_x, closest_y];

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
        return str(e)
    tb_lines = traceback.format_exception(e.__class__, e, trace_back)
    return ''.join(tb_lines)


def get_system_fonts():
    """Retrieves a list of fonts for any operating system. Note that this may not be a complete list of fonts discoverable on the system.
    :returns A list of filepaths to fonts available on the system."""
    if sys.platform == "linux" or sys.platform == "linux2" or sys.platform == "darwin":
        # Linux and OS X.
        return subprocess.check_output("fc-list --format %{file}\\n".split()).split('\n')
    elif sys.platform == "win32" or sys.platform == "cygwin":
        # Windows.
        return [os.path.join(os.environ['WINDIR'], f) for f in os.listdir(os.path.join(os.environ['WINDIR'], "fonts"))]
    else:
        raise NotImplementedError('Unsupported operating system.')
