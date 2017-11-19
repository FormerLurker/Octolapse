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

class CaptureSnapshot(object):

	def __init__(self, profile,printer,debugSettings):
		self.Profile = profile
		self.Printer = printer
		self.Debug= debugSettings
		self.PrintStartTime = time.time()
		self.PrintEndTime = time.time()

	def SetPrintStartTime(self,time):
		self.PrintStartTime = time

	def SetPrintEndTime(self,time):
		self.PrinEndtTime = time

	def Snap(self,printerFileName,snapshotNumber):
		
		# strip off the extension
		printerFileName = os.path.splitext(printerFileName)[0]
		info = SnapshotInfo()
		# set the file name
		info.FileName = self.GetSnapshotFileName(printerFileName,snapshotNumber)
		info.DirectoryName = self.GetSnapshotDirectoryName(printerFileName)
		# TODO:  make the snapshot timeout a separate setting
		DownloadSnapshot(info.DirectoryName, info.FileName, self.Profile.camera.address, self.Debug, timeoutSeconds = self.Profile.snapshot.delay/1000.0*2, username = self.Profile.camera.username, password = self.Profile.camera.password,ignoreSslErrors = self.Profile.camera.ignore_ssl_error )

		return info


	def GetSnapshotFileName(self,printerFileName,snapshotNumber):
		dateStamp = "{0:d}".format(trunc(round(time.time(),2)*100))
		filename = self.Profile.snapshot.output_filename
		if(not filename):
			filename = "{FILENAME}_{SNAPSHOTNUMBER}.{OUTPUTFILEEXTENSION}"
		filename = filename.replace("{FILENAME}",utility.getstring(printerFileName,""))
		filename = filename.replace("{DATETIMESTAMP}","{0:d}".format(trunc(round(time.time(),2)*100)))
		filename = filename.replace("{SNAPSHOTNUMBER}","{0:05d}".format(snapshotNumber))
		filename = filename.replace("{OUTPUTFILEEXTENSION}",utility.getstring(self.Profile.snapshot.output_format,""))
		filename = filename.replace("{PRINTSTARTTIME}","{0:d}".format(trunc(round(self.PrintStartTime,2)*100)))
		return filename


	def GetSnapshotDirectoryName(self,printerFileName):
		directoryName = self.Profile.snapshot.output_directory
		if(not directoryName):
			directoryName = "./snapshots/{FILENAME}/{PRINTSTARTTIME}"

		directoryName = directoryName.replace("{FILENAME}",utility.getstring(printerFileName,""))
		directoryName = directoryName.replace("{OUTPUTFILEEXTENSION}",utility.getstring(self.Profile.snapshot.output_format,""))
		directoryName = directoryName.replace("{PRINTSTARTTIME}","{0:d}".format(trunc(round(self.PrintStartTime,2)*100)))
		return directoryName
	def DownloadSnapshotAsync(self,directoryName, fileName, url, debug, timeoutSeconds, username = None, password = None, ignoreSslErrors = False):
			download_thread = threading.Thread(target=DownloadSnapshot, args=(directoryName, fileName, url, debug, timeoutSeconds, username, password, ignoreSslErrors))
			self.Debug.LogSnapshotDownload("Snapshot - started async download.".format(url,dir))
			download_thread.start()

def DownloadSnapshot(directoryName, fileName, url, debug, timeoutSeconds, username, password, ignoreSslErrors):
			dir = "{0:s}{1:s}".format(directoryName, fileName)
			r=None
			try:
				if(len(username)>0):
					debug.LogSnapshotDownload("Snapshot Download - Authenticating and downloading from {0:s} to {1:s}.".format(url,dir))
					r=requests.get(url, auth=HTTPBasicAuth(username, password),verify = not ignoreSslErrors,timeout=float(timeoutSeconds))
				else:
					debug.LogSnapshotDownload("Snapshot - downloading from {0:s} to {1:s}.".format(url,dir))
					r=requests.get(url,verify = not ignoreSslErrors,timeout=float(timeoutSeconds))
			except:
				type = sys.exc_info()[0]
				value = sys.exc_info()[1]
				debug.LogError("Download - An exception of type:{0} was raised during snapshot download:Error:{1} Traceback:{2}".format(type, value, traceback.format_exc()))
				return
			if r.status_code == requests.codes.ok:
				try:
					path = os.path.dirname(dir)
					if not os.path.exists(path):
						os.makedirs(path)
				except:
					debug.LogWarning("Download - The directory for the download file {0:s} already exists.".format(os.path.dirname(dir)))
					return
				try:
					with iopen(dir, 'wb') as file:
						for chunk in r.iter_content(1024):
							if chunk:
								file.write(chunk)
						debug.LogSnapshotSave("Snapshot - Snapshot saved to disk at {0}".format(dir))
				except:
					type = sys.exc_info()[0]
					value = sys.exc_info()[1]
					debug.LogError("Snapshot - An exception of type:{0} was raised while saving the retrieved shapshot to disk: Error:{1} Traceback:{2}".format(type, value, traceback.format_exc()))
					return
			else:
				debug.LogWarning("Snapshot - failed with status code:{0}".format(r.status_code))

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

class SnapshotInfo(object):
	def __init__(self):
		self.FileName = ""
		self.DirectoryName = ""

		# call the snapshot command
			
		#
		#if(len(self.Profile.snapshot.snapshot_camera_username) > 0):
		#	cmd = "{0:s} --output_directory {1:s} --output_file_name {2:s} --user_name {3:s} --password {4:s} --snapshot_address {5:s}"
		#	cmd = cmd.format(self.Profile.snapshot.script_path, info.DirectoryName, info.FileName, self.Profile.snapshot.snapshot_camera_username, self.Profile.snapshot.snapshot_camera_password, self.Profile.snapshot.snapshot_camera_address)
		#else:
		#	cmd = "{0:s} --output_directory {1:s} --output_file_name {2:s} --snapshot_address {5:s} "
		#	cmd = cmd.format(self.Profile.snapshot.script_path, info.DirectoryName, info.FileName, self.Profile.snapshot.snapshot_camera_username, self.Profile.snapshot.snapshot_camera_password, self.Profile.snapshot.snapshot_camera_address)

		#self.Logger.info("Octolapse - Executing snap script at: {0:s}".format(cmd))
		#r = os.system(cmd)
