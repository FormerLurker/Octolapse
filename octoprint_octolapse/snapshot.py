
# coding=utf-8
import os
import sys
import time
from PIL import Image

import requests
import threading
from requests.auth import HTTPBasicAuth
from io import open as iopen
from urlparse import urlsplit
from math import trunc
from octoprint_octolapse.settings import *
import traceback
import shutil

import uuid
import octoprint_octolapse.utility as utility
import octoprint_octolapse.camera as camera

def StartSnapshotJob(job):
	job.Process();



class CaptureSnapshot(object):

	def __init__(self, settings,dataDirectory, printStartTime, printEndTime=None):
		self.Settings = settings
		self.Printer = self.Settings.CurrentPrinter()
		self.Snapshot = self.Settings.CurrentSnapshot()
		self.Camera = self.Settings.CurrentCamera()
		self.PrintStartTime = printStartTime
		self.PrintEndTime = printEndTime
		self.DataDirectory = dataDirectory
	
	def Snap(self,printerFileName,snapshotNumber,onComplete=None,onSuccess=None, onFail=None):
		info = SnapshotInfo(printerFileName, self.PrintStartTime)
		# set the file name.  It will be a guid + the file extension
		snapshotGuid = str(uuid.uuid4())
		info.FileName = "{0}.{1}".format(snapshotGuid,"jpg")
		info.DirectoryName = utility.GetSnapshotTempDirectory(self.DataDirectory, printerFileName, self.PrintStartTime)
		url = camera.FormatRequestTemplate(self.Camera.address, self.Camera.snapshot_request_template,"")
		#TODO:  TURN THE SNAPSHOT REQUIRE TIMEOUT INTO A SETTING
		newSnapshotJob = SnapshotJob(self.Settings,self.DataDirectory, info, url, snapshotGuid, timeoutSeconds = 1, onComplete = onComplete, onSuccess=onSuccess, onFail = onFail)

		if(self.Snapshot.delay == 0):
			self.Settings.CurrentDebugProfile().LogSnapshotDownload("Starting Snapshot Download Job Immediately.")
			newSnapshotJob.Process()
		else:
			delaySeconds = self.Snapshot.delay/1000.0
			self.Settings.CurrentDebugProfile().LogSnapshotDownload("Starting Snapshot Download Job in {0} seconds.".format(delaySeconds))
			t = threading.Timer( delaySeconds, StartSnapshotJob, [newSnapshotJob])
			t.start()

	def CleanSnapshots(self, printerFileName):
		
		# get snapshot directory
		snapshotDirectory = utility.GetSnapshotTempDirectory(self.DataDirectory, printerFileName,printStartTime)
		self._debug.LogSnapshotClean("Cleaning snapshots from: {0}".format(snapshotDirectory))
		

		path = os.path.dirname(snapshotDirectory + os.sep)
		if(os.path.isdir(path)):
			try:
				shutil.rmtree(path)
				self._debug.LogSnapshotClean("Snapshots cleaned.")
			except:
				type = sys.exc_info()[0]
				value = sys.exc_info()[1]
				self._debug.LogSnapshotClean("Snapshot - Clean - Unable to clean the snapshot path at {0}.  It may already have been cleaned.  Info:  ExceptionType:{1}, Exception Value:{2}".format(path,type,value))
		else:
			self._debug.LogSnapshotClean("Snapshot - No need to clean snapshots: they have already been removed.")	
class SnapshotJob(object):
	snapshot_job_lock = threading.RLock()
	
	def __init__(self,settings, dataDirectory, snapshotInfo, url,  snapshotGuid, timeoutSeconds=5, onComplete = None, onSuccess = None, onFail = None):
		cameraSettings = settings.CurrentCamera()
		self.DataDirectory = dataDirectory
		self.Address = cameraSettings.address
		self.Username = cameraSettings.username
		self.Password = cameraSettings.password
		self.IgnoreSslError = cameraSettings.ignore_ssl_error
		self.Settings = settings;
		self.SnapshotInfo = snapshotInfo;
		self.Url = url
		self.TimeoutSeconds = timeoutSeconds
		self.SnapshotGuid = snapshotGuid
		self._on_complete = onComplete
		self._on_success = onSuccess
		self._on_fail = onFail
	def Process(self):
		#TODO:  REPLACE THE SNAPSHOT NUMBER WITH A GUID HERE
		self._thread = threading.Thread(target=self._process, name="SnapshotDownloadJob_{name}".format(name = self.SnapshotGuid))
		self._thread.daemon = True
		self._thread.start()
	def _process(self):
		with self.snapshot_job_lock:
			success = False
			failReason = "unknown"
			dir = "{0:s}{1}{2:s}".format(self.SnapshotInfo.DirectoryName,os.sep, self.SnapshotInfo.FileName)
			r=None
			try:
				if(len(self.Username)>0):
					self.Settings.CurrentDebugProfile().LogSnapshotDownload("Snapshot Download - Authenticating and downloading from {0:s} to {1:s}.".format(self.Url,dir))
					r=requests.get(self.Url, auth=HTTPBasicAuth(self.Username, self.Password),verify = not self.IgnoreSslError,timeout=float(self.TimeoutSeconds))
				else:
					self.Settings.CurrentDebugProfile().LogSnapshotDownload("Snapshot - downloading from {0:s} to {1:s}.".format(self.Url,dir))
					r=requests.get(self.Url,verify = not self.IgnoreSslError,timeout=float(self.TimeoutSeconds))

				if r.status_code == requests.codes.ok:
					try:
						# make the directory
						path = os.path.dirname(dir)
						if not os.path.exists(path):
							os.makedirs(path)
						# try to download the file.
						try:
							with iopen(dir, 'wb') as file:
								for chunk in r.iter_content(1024):
									if chunk:
										file.write(chunk)
								self.Settings.CurrentDebugProfile().LogSnapshotSave("Snapshot - Snapshot saved to disk at {0}".format(dir))
								success = True

								# create a copy to be used for the full sized latest snapshot image.
								latestSnapshotPath = utility.GetLatestSnapshotDownloadPath(self.DataDirectory)
								shutil.copy(self.SnapshotInfo.GetTempFullPath(),latestSnapshotPath)
								# create a thumbnail of the image
								try:
									# without this I get errors during load (happens in resize, where the image is actually loaded)
									from PIL import ImageFile
									ImageFile.LOAD_TRUNCATED_IMAGES = True
									#######################################

									basewidth = 300
									img = Image.open(latestSnapshotPath)
									wpercent = (basewidth/float(img.size[0]))
									hsize = int((float(img.size[1])*float(wpercent)))
									img = img.resize((basewidth,hsize), Image.ANTIALIAS)
									img.save(utility.GetLatestSnapshotThumbnailDownloadPath(self.DataDirectory),"JPEG")
								except Exception as e:
									#If we can't create the thumbnail, just log
									self.Settings.CurrentDebugProfile().LogException(e)
						except Exception as e:
							#If we can't create the thumbnail, just log
							self.Settings.CurrentDebugProfile().LogException(e)
							failReason = "Snapshot Download - An unexpected exception occurred.  Check the log file (plugin_octolapse.log) for details."
					except Exception as e:
						#If we can't create the thumbnail, just log
						self.Settings.CurrentDebugProfile().LogException(e)
						failReason = "Snapshot Download - An unexpected exception occurred.  Check the log file (plugin_octolapse.log) for details."
				else:
					failReason = "Snapshot Download - failed with status code:{0}".format(r.status_code)
			except Exception as e:
				#If we can't create the thumbnail, just log
				self.Settings.CurrentDebugProfile().LogException(e)
				failReason = "Snapshot Download - An unexpected exception occurred.  Check the log file (plugin_octolapse.log) for details."

			if(success):
				self._notify_callback("success", self.SnapshotInfo)
			else:
				self._notify_callback("fail", failReason)

			self._notify_callback("complete")
				
	def _notify_callback(self, callback, *args, **kwargs):
		"""Notifies registered callbacks of type `callback`."""
		name = "_on_{}".format(callback)
		method = getattr(self, name, None)
		if method is not None and callable(method):
			method(*args, **kwargs)
class SnapshotInfo(object):
	def __init__(self, printerFileName, printStartTime):
		self._printerFileName = printerFileName
		self._printStartTime = printStartTime
		self.FileName = ""
		self.DirectoryName = ""
		
	def GetTempFullPath(self):
		return "{0}{1}{2}".format(self.DirectoryName, os.sep, self.FileName)
	def GetFullPath(self, snapshotNumber):
		return  "{0}{1}".format(self.DirectoryName, utility.GetSnapshotFilename(self._printerFileName, self._printStartTime, snapshotNumber))
