# coding=utf-8
import ntpath
import math
import time
import os
FLOAT_MATH_EQUALITY_RANGE = 0.000001

def getfloat(value,default,key=None):
	try:
		return float(value)
	except ValueError:
		return float(default)

def getint(value,default,key=None):
	try:
		return int(value)
	except ValueError:
		return default

def getbool(value,default,key=None):
	try:
		return bool(value)
	except ValueError:
		return default
def getstring(value,default):
	if value is not None and len(value) > 0:
		return value
	return default
#def getstring(value,default,key=None):
#	if(key is not None):
#		if(key in value):
#			return getstring(value,default)
#
#	if value is not None and len(value) > 0:
#		return value
#	return default


def getobject(value,default,key=None):
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
	

def GetFilenameFromTemplate(fileTemplate, printName, printStartTime, outputExtension, snapshotNumber=None, printEndTime = None):

	dateStamp = "{0:d}".format(math.trunc(round(time.time(),2)*100))
	fileTemplate = fileTemplate.replace("{FILENAME}",getstring(printName,""))
	fileTemplate = fileTemplate.replace("{DATETIMESTAMP}","{0:d}".format(math.trunc(round(time.time(),2)*100)))
	fileTemplate = fileTemplate.replace("{OUTPUTFILEEXTENSION}",getstring(outputExtension,""))
	fileTemplate = fileTemplate.replace("{PRINTSTARTTIME}","{0:d}".format(math.trunc(round(printStartTime,2)*100)))
	if(snapshotNumber is not None):
		if(isinstance(snapshotNumber,int) or isinstance(snapshotNumber,float)):
			fileTemplate = fileTemplate.replace("{SNAPSHOTNUMBER}","{0:05d}".format(snapshotNumber))
		else:
			fileTemplate = fileTemplate.replace("{SNAPSHOTNUMBER}",snapshotNumber)
	if(printEndTime is not None):
		fileTemplate = fileTemplate.replace("{PRINTENDTIME}","{0:d}".format(math.trunc(round(printEndTime,2)*100)))
	
	return fileTemplate

def GetDirectoryFromTemplate(directoryTemplate, printName, printStartTime, outputExtension,printEndTime = None):
	directoryTemplate = directoryTemplate.replace("{FILENAME}",getstring(printName,""))
	directoryTemplate = directoryTemplate.replace("{OUTPUTFILEEXTENSION}",getstring(outputExtension,""))
	directoryTemplate = directoryTemplate.replace("{PRINTSTARTTIME}","{0:d}".format(math.trunc(round(printStartTime,2)*100)))
	if(printEndTime is not None):
		directoryTemplate = directoryTemplate.replace("{PRINTENDTIME}","{0:d}".format(math.trunc(round(printEndTime,2)*100)))
	return directoryTemplate
