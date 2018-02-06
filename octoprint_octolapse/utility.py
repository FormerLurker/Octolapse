# coding=utf-8
import ntpath
import math
import time
import os
import re
import sys
import errno
import tempfile
FLOAT_MATH_EQUALITY_RANGE = 0.000001

def getfloat(value,default):
	try:
		return float(value)
	except ValueError:
		return float(default)
def getnullablefloat(value,default):
	if(value is None):
		return None
	try:
		return float(value)
	except ValueError:
		if(default is None):
			return None
		return float(default)

def getint(value,default):
	try:
		return int(value)
	except ValueError:
		return default
def getnullablebool(value,default):
	if(value is None):
			return None
	try:
		return bool(value)
	except ValueError:
		if(default is None):
			return None
		return default

def getbool(value,default):
	try:
		return bool(value)
	except ValueError:
		return default
def getstring(value,default):
	if value is not None and len(value) > 0:
		return value
	return default

def getbitrate(value,default):
	if(value is None):
		return default
	# add a global for the regex so we can use a pre-complied version
	if ('octoprint_ffmpeg_bitrate_regex' not in globals() or octoprint_ffmpeg_bitrate_regex is None) :
		octoprint_ffmpeg_bitrate_regex = re.compile("^\d+[KkMm]$",re.IGNORECASE)
	# get any matches
	matches = octoprint_ffmpeg_bitrate_regex.match(value)
	if(matches is None):
		return default
	return value

	

def getobject(value,default):
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
	 return abs(a-b) <= abs_tol
def round_to(n, precision):
    correction = 0.5 if n >= 0 else -0.5
    return int( n/precision+correction ) * precision

def GetTempSnapshotDirectoryTemplate():
	return "{0}{1}{2}{3}".format("{DATADIRECTORY}",os.sep,"tempsnapshots",os.sep )
def GetSnapshotDirectory(dataDirectory):
	return "{0}{1}{2}{3}".format(dataDirectory,os.sep,"snapshots",os.sep )

def GetSnapshotFilenameTemplate():
	return "{0}{1}{2}".format("{FILENAME}_{PRINTSTARTTIME}",os.sep,"{FILENAME}")

def GetRenderingDirectoryFromDataDirectory(dataDirectory):
	return GetRenderingDirectoryTemplate().replace("{DATADIRECTORY}",dataDirectory)

def GetSnapshotDownloadPath(dataDirectory, fileName):
	return "{0}{1}{2}{3}{4}".format(dataDirectory,os.sep,"snapshots",os.sep,fileName)

def GetLatestSnapshotDownloadPath(dataDirectory):
	return "{0}{1}".format(GetSnapshotDirectory(dataDirectory),"latest_snapshot.jpeg")

def GetLatestSnapshotThumbnailDownloadPath(dataDirectory):
	return "{0}{1}".format(GetSnapshotDirectory(dataDirectory),"latest_snapshot_thumbnail_300px.jpeg")

def GetImagesDownloadPath(baseFolder, fileName):
	return "{0}{1}data{2}{3}{4}{5}".format(baseFolder,os.sep,os.sep,"Images",os.sep,fileName)
def GetErrorImageDownloadPath(baseFolder):
	return GetImagesDownloadPath(baseFolder, "no-image-available.png")
def GetNoSnapshotImagesDownloadPath(baseFolder):
	return GetImagesDownloadPath(baseFolder, "no_snapshot.png")
def GetErrorImageDownloadPath(baseFolder):
	return GetImagesDownloadPath(baseFolder, "no-image-available.png")
def GetRenderingDirectoryTemplate():
	return "{0}{1}{2}{3}".format("{DATADIRECTORY}",os.sep,"timelapses",os.sep )

def GetRenderingBaseFilenameTemplate():
	return "{FILENAME}_{DATETIMESTAMP}"

def GetRenderingBaseFilename(printName, printStartTime, printEndTime = None):
	fileTemplate = GetRenderingBaseFilenameTemplate()
	dateStamp = "{0:d}".format(math.trunc(round(time.time(),2)*100))
	fileTemplate = fileTemplate.replace("{FILENAME}",getstring(printName,""))
	fileTemplate = fileTemplate.replace("{DATETIMESTAMP}","{0:d}".format(math.trunc(round(time.time(),2)*100)))
	fileTemplate = fileTemplate.replace("{PRINTSTARTTIME}","{0:d}".format(math.trunc(round(printStartTime,2)*100)))
	if(printEndTime is not None):
		fileTemplate = fileTemplate.replace("{PRINTENDTIME}","{0:d}".format(math.trunc(round(printEndTime,2)*100)))
	
	return fileTemplate

def GetSnapshotFilename(printName, printStartTime, snapshotNumber):
	fileTemplate = GetSnapshotFilenameTemplate()
	dateStamp = "{0:d}".format(math.trunc(round(time.time(),2)*100))
	fileTemplate = fileTemplate.replace("{FILENAME}",getstring(printName,""))
	fileTemplate = fileTemplate.replace("{DATETIMESTAMP}","{0:d}".format(math.trunc(round(time.time(),2)*100)))
	fileTemplate = fileTemplate.replace("{PRINTSTARTTIME}","{0:d}".format(math.trunc(round(printStartTime,2)*100)))
	return "{0}{1}.{2}".format(fileTemplate,FormatSnapshotNumber(snapshotNumber) , "jpg")

SnapshotNumberFormat = "%06d"
def FormatSnapshotNumber(number):
	# we may get a templated field here for the snapshot number, so check to make sure it is an int first
	if(isinstance(number,int)):
		return SnapshotNumberFormat % number
	# not an int, return the original field
	return number

def GetSnapshotTempDirectory(dataDirectory, printName, printStartTime, printEndTime = None):
	directoryTemplate = GetTempSnapshotDirectoryTemplate()
	directoryTemplate = directoryTemplate.replace("{FILENAME}",getstring(printName,""))
	directoryTemplate = directoryTemplate.replace("{PRINTSTARTTIME}","{0:d}".format(math.trunc(round(printStartTime,2)*100)))
	if(printEndTime is not None):
		directoryTemplate = directoryTemplate.replace("{PRINTENDTIME}","{0:d}".format(math.trunc(round(printEndTime,2)*100)))
	directoryTemplate = directoryTemplate.replace("{DATADIRECTORY}",dataDirectory)
		
	return directoryTemplate
def GetRenderingDirectory(dataDirectory, printName, printStartTime, outputExtension, printEndTime = None):
	directoryTemplate = GetRenderingDirectoryTemplate()
	directoryTemplate = directoryTemplate.replace("{FILENAME}",getstring(printName,""))
	directoryTemplate = directoryTemplate.replace("{OUTPUTFILEEXTENSION}",getstring(outputExtension,""))
	directoryTemplate = directoryTemplate.replace("{PRINTSTARTTIME}","{0:d}".format(math.trunc(round(printStartTime,2)*100)))
	if(printEndTime is not None):
		directoryTemplate = directoryTemplate.replace("{PRINTENDTIME}","{0:d}".format(math.trunc(round(printEndTime,2)*100)))
	directoryTemplate = directoryTemplate.replace("{DATADIRECTORY}",dataDirectory)
		
	return directoryTemplate

def SecondsToHHMMSS(seconds):
    hours = seconds // (60*60)
    seconds %= (60*60)
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
		if(octoprintPrinter is not None):
			current_job = octoprintPrinter.get_current_job()
			if current_job is not None and "file" in current_job:
				current_job_file = current_job["file"]
				if "path" in current_job_file and "origin" in current_job_file:
					current_file_path = current_job_file["path"]
					return GetFilenameFromFullPath(current_file_path)
		return ""

def IsInBounds(boundingBox, x=None, y=None, z=None ):
	"""Determines if the given X,Y,Z coordinate is within the bounding box of the printer, as determined by the octoprint configuration"""
	minX = boundingBox['min_x']
	maxX = boundingBox['max_x']
	minY = boundingBox['min_y']
	maxY = boundingBox['max_y']
	minZ = boundingBox['min_z']
	maxZ = boundingBox['max_z']

	xIsInBounds = x is None or (x >= minX and x <= maxX)
	yIsInBounds = y is None or (y >= minY and y <= maxY)
	zIsInBounds = z is None or (z >= minZ and z <= maxZ)

	return xIsInBounds and yIsInBounds and zIsInBounds

def GetClosestInBoundsPosition(boundingBox, x=None, y=None,z=None):

	minX = boundingBox['min_x']
	maxX = boundingBox['max_x']
	minY = boundingBox['min_y']
	maxY = boundingBox['max_y']
	minZ = boundingBox['min_z']
	maxZ = boundingBox['max_z']
	if(x is not None):
		if(x > maxX):
			x = maxX
		elif(x < minX):
			x = minX

	if(y is not None):
		if(y > maxY):
			y = maxY
		elif(y < minY):
			y = minY

	if(z is not None):
		if(z > maxZ):
			z = maxZ
		elif(z < minZ):
			z = minZ
	return {'X':x,'Y':y,'Z':z}

def GetBoundingBox(octolapsePrinterProfile, octoprintPrinterProfile):
	# get octolapse min and max
	minX = octolapsePrinterProfile.min_x
	maxX = octolapsePrinterProfile.max_x
	minY = octolapsePrinterProfile.min_y
	maxY = octolapsePrinterProfile.max_y
	minZ = octolapsePrinterProfile.min_z
	maxZ = octolapsePrinterProfile.max_z

	volume = octoprintPrinterProfile["volume"]
	customBox = volume["custom_box"]
	if(minX is None):
		if(customBox != False):
			minX = customBox["x_min"]
		else:
			minX = 0
	if(maxX is None):
		if(customBox != False):
			maxX = customBox["x_max"]
		else:
			maxX = volume["width"];
			
	if(minY is None):
		if(customBox != False):
			minY = customBox["y_min"]
		else:
			minY = 0
	if(maxY is None):
		if(customBox != False):
			maxY = customBox["y_max"]
		else:
			maxY = volume["depth"];

	if(minZ is None):
		if(customBox != False):
			minZ = customBox["z_min"]
		else:
			minZ = 0
	if(maxZ is None):
		if(customBox != False):
			maxZ = customBox["z_max"]
		else:
			maxZ = volume["height"];

	return {
		"min_x" : minX,
		"max_x" : maxX,
		"min_y" : minY,
		"max_y" : maxY,
		"min_z" : minZ,
		"max_z" : maxZ
		}
	
#def IsXInBounds(x, printerProfile,octolapsePrinterProfile):
#	"""Determines if the given X coordinate is within the bounding box of the printer, as determined by the octoprint configuration"""
#	isInBounds = True
#	if (x is not None):
#		if(printerProfile["volume"]["custom_box"] != False):
#			customBox = printerProfile["volume"]["custom_box"]
#			if(x < customBox["x_min"] or x > customBox["x_max"]):
#				isInBounds = False
#		else:
#			volume = printerProfile["volume"]
#			if(x < 0 or x > volume["width"]):
#				isInBounds = False

#	return isInBounds

#def IsYInBounds(y, printerProfile,octolapsePrinterProfile):
#	"""Determines if the given X coordinate is within the bounding box of the printer, as determined by the octoprint configuration"""
#	isInBounds = True
#	if (y is not None):
#		if(printerProfile["volume"]["custom_box"] != False):
#			customBox = printerProfile["volume"]["custom_box"]
#			if(y < customBox["y_min"] or y > customBox["y_max"]):
#				isInBounds = False
#		else:
#			volume = printerProfile["volume"]
#			if(y < 0 or y > volume["depth"]):
#				isInBounds = False
#	return isInBounds

#def IsZInBounds(z, printerProfile,octolapsePrinterProfile):
#	"""Determines if the given X coordinate is within the bounding box of the printer, as determined by the octoprint configuration"""
#	isInBounds = True
#	if(z is not None):
#		if(printerProfile["volume"]["custom_box"] != False):
#			customBox = printerProfile["volume"]["custom_box"]
#			if(z < customBox["z_min"] or z > customBox["z_max"]):
#				isInBounds = False
#		else:
#			volume = printerProfile["volume"]
#			if(z < 0 or z > volume["height"]):
#				isInBounds = False
#	return isInBounds
