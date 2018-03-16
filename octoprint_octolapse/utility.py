# coding=utf-8

# This file is subject to the terms and conditions defined in
# file called 'LICENSE', which is part of this source code package.

import math
import ntpath
import os
import re
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
    return "{0}{1}{2}".format("{FILENAME}_{PRINTSTARTTIME}", os.sep, "{FILENAME}")


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
    file_template = get_snapshot_filename_template()
    file_template = file_template.replace("{FILENAME}", get_string(print_name, ""))
    file_template = file_template.replace(
        "{DATETIMESTAMP}", "{0:d}".format(math.trunc(round(time.time(), 2) * 100)))
    file_template = file_template.replace("{PRINTSTARTTIME}", "{0:d}".format(
        math.trunc(round(print_start_time, 2) * 100)))
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


def exception_to_string(e):
    trace_back = sys.exc_info()[2]
    if trace_back is None:
        return str(e)
    tb_lines = traceback.format_exception(e.__class__, e, trace_back)
    return ''.join(tb_lines)
