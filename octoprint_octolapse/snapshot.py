# coding=utf-8
import os
import sys
import time
import utility
import requests
import threading
from requests.auth import HTTPBasicAuth
from io import open as iopen
from urlparse import urlsplit
from math import trunc
from .settings import *
import traceback
import shutil
import camera

class CaptureSnapshot(object):

	def __init__(self, settings):
		self.Settings = settings
		self.Printer = self.Settings.CurrentPrinter()
		self.Snapshot = self.Settings.CurrentSnapshot()
		self.Camera = self.Settings.CurrentCamera()
		self.Debug= self.Settings.debug
		self.PrintStartTime = time.time()
		self.PrintEndTime = time.time()

	def SetPrintStartTime(self,time):
		self.PrintStartTime = time

	def SetPrintEndTime(self,time):
		self.PrinEndtTime = time

	def Snap(self,printerFileName,snapshotNumber):
		
		
		info = SnapshotInfo()
		# set the file name
		info.FileName = utility.GetFilenameFromTemplate(self.Snapshot.output_filename, printerFileName, self.PrintStartTime, self.Snapshot.output_format, snapshotNumber)
		info.DirectoryName = utility.GetDirectoryFromTemplate(self.Snapshot.output_directory,printerFileName,self.PrintStartTime, self.Snapshot.output_format)
		# TODO:  make the snapshot timeout a separate setting
		url = camera.FormatRequestTemplate(self.Camera.address, self.Camera.snapshot_request_template,"")
		#DownloadSnapshot(info.DirectoryName, info.FileName, url, self.Debug, timeoutSeconds = self.Snapshot.delay/1000.0*2, username = self.Camera.username, password = self.Camera.password,ignoreSslErrors = self.Camera.ignore_ssl_error )
		SnapshotJob(self.Settings, info.DirectoryName, info.FileName, url, snapshotNumber, timeoutSeconds = self.Snapshot.delay/1000.0*2).Process()
		return info

	def CleanSnapshots(self,printerFileName, event):
		if(event == 'before_print' and self.Snapshot.cleanup_before_print):
			self._CleanSnapshots(printerFileName)
		elif(event == 'after_print' and self.Snapshot.cleanup_after_print):
			self._CleanSnapshots(printerFileName)
		elif(event == 'after_fail' and self.Snapshot.cleanup_after_fail):
			self._CleanSnapshots(printerFileName)
		elif(event == 'after_cancel' and self.Snapshot.cleanup_after_cancel):
			self._CleanSnapshots(printerFileName)
		elif(event == 'before_close' and self.Snapshot.cleanup_before_close):
			self._CleanSnapshots(printerFileName)
		elif(event == 'after_render_complete' and self.Snapshot.cleanup_after_render_complete):
			self._CleanSnapshots(printerFileName)
		elif(event == 'after_render_fail' and self.Snapshot.cleanup_after_render_fail):
			self._CleanSnapshots(printerFileName)
	def _CleanSnapshots(self,printerFileName):
		# get snapshot directory
		self.Debug.LogSnapshotClean("Cleaning")
		if(printerFileName is None):
			path = self.Snapshot.output_directory
		else:
			path = utility.GetDirectoryFromTemplate(self.Snapshot.output_directory,printerFileName,self.PrintStartTime, self.Snapshot.output_format)
		path = os.path.dirname(path)
		if(os.path.isdir(path)):
			try:
				shutil.rmtree(path)
			except:
				type = sys.exc_info()[0]
				value = sys.exc_info()[1]
				self.Debug.LogWarning("Snapshot - Clean - Unable to clean the snapshot path at {0}.  It may already have been cleaned.  Info:  ExceptionType:{1}, Exception Value:{2}".format(path,type,value))
		else:
			self.Debug.LogWarning("Snapshot - No need to clean snapshots: they have already been removed.")
	
def requests_image(file_url,path):
    suffix_list = ['jpg', 'gif', 'png', 'tif', 'svg',]
    file_name =  urlsplit(file_url)[2].split('/')[-1]
    file_suffix = file_name.split('.')[1]
    i = requests.get(file_url)
    if file_suffix in suffix_list and i.status_code == requests.codes.ok:
        with iopen(file_name, 'wb') as file:
            file.write(i.content)
    else:
        return False
class SnapshotJob(object):
	snapshot_job_lock = threading.RLock()
	
	def __init__(self,settings, directoryName, fileName, url,  snapshotNumber, timeoutSeconds=5):
		camera = settings.CurrentCamera()
		self.Address = camera.address
		self.Username = camera.username
		self.Password = camera.password
		self.IgnoreSslError = camera.ignore_ssl_error

		self.Debug = settings.debug
		self.DirectoryName = directoryName
		self.FileName = fileName
		self.Url = url
		self.TimeoutSeconds = timeoutSeconds
		self.SnapshotNumber = snapshotNumber
	def Process(self):
		self._thread = threading.Thread(target=self._process,
		                                name="SnapshotDownloadJob_{name}".format(name = self.SnapshotNumber))
		self._thread.daemon = True
		self._thread.start()
	def _process(self):
		with self.snapshot_job_lock:
			dir = "{0:s}{1:s}".format(self.DirectoryName, self.FileName)
			r=None
			try:
				if(len(self.Username)>0):
					self.Debug.LogSnapshotDownload("Snapshot Download - Authenticating and downloading from {0:s} to {1:s}.".format(self.Url,dir))
					r=requests.get(self.Url, auth=HTTPBasicAuth(self.Username, self.Password),verify = not self.IgnoreSslError,timeout=float(self.TimeoutSeconds))
				else:
					self.Debug.LogSnapshotDownload("Snapshot - downloading from {0:s} to {1:s}.".format(self.Url,dir))
					r=requests.get(self.Url,verify = not self.IgnoreSUslError,timeout=float(self.TimeoutSeconds))
			except:
				type = sys.exc_info()[0]
				value = sys.exc_info()[1]
				self.Debug.LogError("Download - An exception of type:{0} was raised during snapshot download:Error:{1}".format(type, value))
				return
			if r.status_code == requests.codes.ok:
				try:
					path = os.path.dirname(dir)
					if not os.path.exists(path):
						os.makedirs(path)
				except:
					type = sys.exc_info()[0]
					value = sys.exc_info()[1]
					self.Debug.LogWarning("Download - An exception was thrown when trying to save a snapshot to: {0} , ExceptionType:{1}, Exception Value:{2}".format(os.path.dirname(dir),type,value))
					return
				try:
					with iopen(dir, 'wb') as file:
						for chunk in r.iter_content(1024):
							if chunk:
								file.write(chunk)
						self.Debug.LogSnapshotSave("Snapshot - Snapshot saved to disk at {0}".format(dir))
				except:
					type = sys.exc_info()[0]
					value = sys.exc_info()[1]
					self.Debug.LogError("Snapshot - An exception of type:{0} was raised while saving the retrieved shapshot to disk: Error:{1} Traceback:{2}".format(type, value, traceback.format_exc()))
					return
			else:
				self.Debug.LogWarning("Snapshot - failed with status code:{0}".format(r.status_code))
class SnapshotInfo(object):
	def __init__(self):
		self.FileName = ""
		self.DirectoryName = ""

		# call the snapshot command
			
		#
		#if(len(self.Snapshot.snapshot_camera_username) > 0):
		#	cmd = "{0:s} --output_directory {1:s} --output_file_name {2:s} --user_name {3:s} --password {4:s} --snapshot_address {5:s}"
		#	cmd = cmd.format(self.Snapshot.script_path, info.DirectoryName, info.FileName, self.Snapshot.snapshot_camera_username, self.Snapshot.snapshot_camera_password, self.Snapshot.snapshot_camera_address)
		#else:
		#	cmd = "{0:s} --output_directory {1:s} --output_file_name {2:s} --snapshot_address {5:s} "
		#	cmd = cmd.format(self.Snapshot.script_path, info.DirectoryName, info.FileName, self.Snapshot.snapshot_camera_username, self.Snapshot.snapshot_camera_password, self.Snapshot.snapshot_camera_address)

		#self.Logger.info("Octolapse - Executing snap script at: {0:s}".format(cmd))
		#r = os.system(cmd)




		#def DownloadSnapshotAsync(self,directoryName, fileName, url, debug, timeoutSeconds, username = None, password = None, ignoreSslErrors = False):
	#		download_thread = threading.Thread(target=DownloadSnapshot, args=(directoryName, fileName, url, debug, timeoutSeconds, username, password, ignoreSslErrors))
	#		self.Debug.LogSnapshotDownload("Snapshot - started async download.".format(url,dir))
	#		download_thread.start()

#def DownloadSnapshot(directoryName, fileName, url, debug, timeoutSeconds, username, password, ignoreSslErrors):
#			dir = "{0:s}{1:s}".format(directoryName, fileName)
#			r=None
#			try:
#				if(len(username)>0):
#					debug.LogSnapshotDownload("Snapshot Download - Authenticating and downloading from {0:s} to {1:s}.".format(url,dir))
#					r=requests.get(url, auth=HTTPBasicAuth(username, password),verify = not ignoreSslErrors,timeout=float(timeoutSeconds))
#				else:
#					debug.LogSnapshotDownload("Snapshot - downloading from {0:s} to {1:s}.".format(url,dir))
#					r=requests.get(url,verify = not ignoreSslErrors,timeout=float(timeoutSeconds))
#			except:
#				type = sys.exc_info()[0]
#				value = sys.exc_info()[1]
#				debug.LogError("Download - An exception of type:{0} was raised during snapshot download:Error:{1} Traceback:{2}".format(type, value, traceback.format_exc()))
#				return
#			if r.status_code == requests.codes.ok:
#				try:
#					path = os.path.dirname(dir)
#					if not os.path.exists(path):
#						os.makedirs(path)
#				except:
#					type = sys.exc_info()[0]
#					value = sys.exc_info()[1]
#					debug.LogWarning("Download - An exception was thrown when trying to save a snapshot to: {0} , ExceptionType:{1}, Exception Value:{2}".format(os.path.dirname(dir),type,value))
#					return
#				try:
#					with iopen(dir, 'wb') as file:
#						for chunk in r.iter_content(1024):
#							if chunk:
#								file.write(chunk)
#						debug.LogSnapshotSave("Snapshot - Snapshot saved to disk at {0}".format(dir))
#				except:
#					type = sys.exc_info()[0]
#					value = sys.exc_info()[1]
#					debug.LogError("Snapshot - An exception of type:{0} was raised while saving the retrieved shapshot to disk: Error:{1} Traceback:{2}".format(type, value, traceback.format_exc()))
#					return
#			else:
#				debug.LogWarning("Snapshot - failed with status code:{0}".format(r.status_code))
