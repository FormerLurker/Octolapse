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


def getfloat(value, default):
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return float(default)


def getnullablefloat(value, default):
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        if default is None:
            return None
        return float(default)


def getint(value, default):
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def getnullablebool(value, default):
    if value is None:
        return None
    try:
        return bool(value)
    except ValueError:
        if default is None:
            return None
        return default


def getbool(value, default):
    if value is None:
        return default
    try:
        return bool(value)
    except ValueError:
        return default


def getstring(value, default):
    if value is not None and len(value) > 0:
        return value
    return default


def getbitrate(value, default):
    if value is None:
        return default
    # add a global for the regex so we can use a pre-complied version
    if 'octoprint_ffmpeg_bitrate_regex' not in globals() or octoprint_ffmpeg_bitrate_regex is None:
        octoprint_ffmpeg_bitrate_regex = re.compile(
            "^\d+[KkMm]$", re.IGNORECASE)
    # get any matches
    matches = octoprint_ffmpeg_bitrate_regex.match(value)
    if matches is None:
        return default
    return value


def getobject(value, default):
    if value is None:
        return default
    return value


def is_sequence(arg):
    return (not hasattr(arg, "strip") and
            hasattr(arg, "__getitem__") or
            hasattr(arg, "__iter__"))


def GetFilenameFromFullPath(path):
    baseName = ntpath.basename(path)
    head, tail = ntpath.split(baseName)
    fileName = tail or ntpath.basename(head)
    return os.path.splitext(fileName)[0]


def GetExtensionFromFileName(fileName):
    extension = os.path.splitext(filename)[1]
    return extension


def isclose(a, b, abs_tol=0.01000):
    return abs(a - b) <= abs_tol


def round_to(n, precision):
    correction = 0.5 if n >= 0 else -0.5
    return int(n / precision + correction) * precision


def GetTempSnapshotDirectoryTemplate():
    return "{0}{1}{2}{3}".format("{DATADIRECTORY}", os.sep, "tempsnapshots", os.sep)


def GetSnapshotDirectory(dataDirectory):
    return "{0}{1}{2}{3}".format(dataDirectory, os.sep, "snapshots", os.sep)


def GetSnapshotFilenameTemplate():
    return "{0}{1}{2}".format("{FILENAME}_{PRINTSTARTTIME}", os.sep, "{FILENAME}")


def GetRenderingDirectoryFromDataDirectory(dataDirectory):
    return GetRenderingDirectoryTemplate().replace("{DATADIRECTORY}", dataDirectory)


def GetSnapshotDownloadPath(dataDirectory, fileName):
    return "{0}{1}{2}{3}{4}".format(dataDirectory, os.sep, "snapshots", os.sep, fileName)


def GetLatestSnapshotDownloadPath(dataDirectory):
    return "{0}{1}".format(GetSnapshotDirectory(dataDirectory), "latest_snapshot.jpeg")


def GetLatestSnapshotThumbnailDownloadPath(dataDirectory):
    return "{0}{1}".format(GetSnapshotDirectory(dataDirectory), "latest_snapshot_thumbnail_300px.jpeg")


def GetImagesDownloadPath(baseFolder, fileName):
    return "{0}{1}data{2}{3}{4}{5}".format(baseFolder, os.sep, os.sep, "Images", os.sep, fileName)


def GetErrorImageDownloadPath(baseFolder):
    return GetImagesDownloadPath(baseFolder, "no-image-available.png")


def GetNoSnapshotImagesDownloadPath(baseFolder):
    return GetImagesDownloadPath(baseFolder, "no_snapshot.png")


def GetErrorImageDownloadPath(baseFolder):
    return GetImagesDownloadPath(baseFolder, "no-image-available.png")


def GetRenderingDirectoryTemplate():
    return "{0}{1}{2}{3}".format("{DATADIRECTORY}", os.sep, "timelapses", os.sep)


def GetRenderingBaseFilenameTemplate():
    return "{FILENAME}_{DATETIMESTAMP}"


def GetRenderingBaseFilename(printName, printStartTime, printEndTime=None):
    fileTemplate = GetRenderingBaseFilenameTemplate()
    dateStamp = "{0:d}".format(math.trunc(round(time.time(), 2) * 100))
    fileTemplate = fileTemplate.replace("{FILENAME}", getstring(printName, ""))
    fileTemplate = fileTemplate.replace(
        "{DATETIMESTAMP}", time.strftime("%Y%m%d%H%M%S", time.localtime(time.time())))
    fileTemplate = fileTemplate.replace(
        "{PRINTSTARTTIME}", time.strftime("%Y%m%d%H%M%S", time.localtime(printStartTime)))
    if printEndTime is not None:
        fileTemplate = fileTemplate.replace(
            "{PRINTENDTIME}", time.strftime("%Y%m%d%H%M%S", time.localtime(printEndTime)))

    return fileTemplate


def GetSnapshotFilename(printName, printStartTime, snapshotNumber):
    fileTemplate = GetSnapshotFilenameTemplate()
    dateStamp = "{0:d}".format(math.trunc(round(time.time(), 2) * 100))
    fileTemplate = fileTemplate.replace("{FILENAME}", getstring(printName, ""))
    fileTemplate = fileTemplate.replace(
        "{DATETIMESTAMP}", "{0:d}".format(math.trunc(round(time.time(), 2) * 100)))
    fileTemplate = fileTemplate.replace("{PRINTSTARTTIME}", "{0:d}".format(
        math.trunc(round(printStartTime, 2) * 100)))
    return "{0}{1}.{2}".format(fileTemplate, FormatSnapshotNumber(snapshotNumber), "jpg")


SnapshotNumberFormat = "%06d"


def FormatSnapshotNumber(number):
    # we may get a templated field here for the snapshot number, so check to make sure it is an int first
    if isinstance(number, int):
        return SnapshotNumberFormat % number
    # not an int, return the original field
    return number


def GetSnapshotTempDirectory(dataDirectory):
    directoryTemplate = GetTempSnapshotDirectoryTemplate()
    directoryTemplate = directoryTemplate.replace(
        "{DATADIRECTORY}", dataDirectory)

    return directoryTemplate


def GetRenderingDirectory(dataDirectory, printName, printStartTime, outputExtension, printEndTime=None):
    directoryTemplate = GetRenderingDirectoryTemplate()
    directoryTemplate = directoryTemplate.replace(
        "{FILENAME}", getstring(printName, ""))
    directoryTemplate = directoryTemplate.replace(
        "{OUTPUTFILEEXTENSION}", getstring(outputExtension, ""))
    directoryTemplate = directoryTemplate.replace("{PRINTSTARTTIME}",
                                                  "{0:d}".format(math.trunc(round(printStartTime, 2) * 100)))
    if printEndTime is not None:
        directoryTemplate = directoryTemplate.replace("{PRINTENDTIME}",
                                                      "{0:d}".format(math.trunc(round(printEndTime, 2) * 100)))
    directoryTemplate = directoryTemplate.replace(
        "{DATADIRECTORY}", dataDirectory)

    return directoryTemplate


def SecondsToHHMMSS(seconds):
    hours = seconds // (60 * 60)
    seconds %= (60 * 60)
    minutes = seconds // 60
    seconds %= 60
    return "%02i:%02i:%02i" % (hours, minutes, seconds)


class SafeDict(dict):
    def __init__(self, **entries):
        self.__dict__.update(entries)
        index = 0

        for key in self.keys():
            self.keys[index] = str(key)
            index += 1

    def __missing__(self, key):
        return '{' + key + '}'


def CurrentlyPrintingFileName(octoprintPrinter):
    if octoprintPrinter is not None:
        current_job = octoprintPrinter.get_current_job()
        if current_job is not None and "file" in current_job:
            current_job_file = current_job["file"]
            if "path" in current_job_file and "origin" in current_job_file:
                current_file_path = current_job_file["path"]
                return GetFilenameFromFullPath(current_file_path)
    return ""


def IsInBounds(boundingBox, x=None, y=None, z=None):
    # Determines if the given X,Y,Z coordinate is within
    # the bounding box of the printer, as determined by
    # the octoprint configuration
    # if no coordinates are give, return false
    if x is None and y is None and z is None:
        return False

    minX = boundingBox['min_x']
    maxX = boundingBox['max_x']
    minY = boundingBox['min_y']
    maxY = boundingBox['max_y']
    minZ = boundingBox['min_z']
    maxZ = boundingBox['max_z']

    xIsInBounds = x is None or minX <= x <= maxX
    yIsInBounds = y is None or minY <= y <= maxY
    zIsInBounds = z is None or minZ <= z <= maxZ

    return xIsInBounds and yIsInBounds and zIsInBounds


def GetClosestInBoundsPosition(bounding_box, x=None, y=None, z=None):
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


def GetBoundingBox(octolapsePrinterProfile, octoprintPrinterProfile):
    # get octolapse min and max
    if octolapsePrinterProfile.override_octoprint_print_volume:
        minX = octolapsePrinterProfile.min_x
        maxX = octolapsePrinterProfile.max_x
        minY = octolapsePrinterProfile.min_y
        maxY = octolapsePrinterProfile.max_y
        minZ = octolapsePrinterProfile.min_z
        maxZ = octolapsePrinterProfile.max_z
    else:
        volume = octoprintPrinterProfile["volume"]
        customBox = volume["custom_box"]
        # see if we have a custom bounding box
        if customBox != False:
            minX = customBox["x_min"]
            maxX = customBox["x_max"]
            minY = customBox["y_min"]
            maxY = customBox["y_max"]
            minZ = customBox["z_min"]
            maxZ = customBox["z_max"]
        else:
            minX = 0
            maxX = volume["width"]
            minY = 0
            maxY = volume["depth"]
            minZ = 0
            maxZ = volume["height"]

    return {
        "min_x": minX,
        "max_x": maxX,
        "min_y": minY,
        "max_y": maxY,
        "min_z": minZ,
        "max_z": maxZ
    }


def ExceptionToString(e):
    traceBack = sys.exc_info()[2]
    if traceBack is None:
        return str(e)
    tb_lines = traceback.format_exception(e.__class__, e, traceBack)
    return ''.join(tb_lines)
