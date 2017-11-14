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


class CaptureSnapshot(object):

	def __init__(self, profile,printer,octoprintLogger):
		self.Profile = profile
		self.Printer = printer
		self.Logger = octoprintLogger
		self.PrintStartTime = time.time()
		self.PrintEndTime = time.time()

	def SetPrintStartTime(self,time):
		self.PrintStartTime = time

	def SetPrintEndTime(self,time):
		self.PrinEndtTime = time

	def Snap(self,printerFileName):
		self.Logger.info("Snapshot - Snapshot")
		# strip off the extension
		printerFileName = os.path.splitext(printerFileName)[0]
		info = SnapshotInfo()
		# set the file name
		info.FileName = self.GetSnapshotFileName(printerFileName)
		info.DirectoryName = self.GetSnapshotDirectoryName(printerFileName)
		DownloadSnapshotAsync(info.DirectoryName, info.FileName, self.Profile.camera.address, self.Logger, username = self.Profile.camera.username, password = self.Profile.camera.password,ignoreSslErrors = self.Profile.camera.ignore_ssl_error )

		return info


	def GetSnapshotFileName(self,printerFileName):
		dateStamp = "{0:d}".format(trunc(round(time.time(),3)*1000))
		filename = self.Profile.snapshot.output_filename
		if(not filename):
			filename = "snapshot_{DATETIMESTAMP}.{OUTPUTFILEEXTENSION}"
		filename = filename.replace("{FILENAME}",utility.getstring(printerFileName,""))
		filename = filename.replace("{DATETIMESTAMP}","{0:d}".format(trunc(round(time.time(),3)*1000)))
		filename = filename.replace("{OUTPUTFILEEXTENSION}",utility.getstring(self.Profile.snapshot.output_format,""))
		filename = filename.replace("{PRINTSTARTTIME}","{0:d}".format(trunc(round(self.PrintStartTime,3)*1000)))
		filename = filename.replace("{PRINTENDTIME}","{0:d}".format(trunc(round(self.PrintEndTime,3)*1000)))
		return filename


	def GetSnapshotDirectoryName(self,printerFileName):
		directoryName = self.Profile.snapshot.output_directory
		if(not directoryName):
			directoryName = "./snapshots/{FILENAME}/{PRINTSTARTTIME}"

		directoryName = directoryName.replace("{FILENAME}",utility.getstring(printerFileName,""))
		directoryName = directoryName.replace("{DATETIMESTAMP}","{0:d}".format(trunc(round(time.time(),3)*1000)))
		directoryName = directoryName.replace("{OUTPUTFILEEXTENSION}",utility.getstring(self.Profile.snapshot.output_format,""))
		directoryName = directoryName.replace("{PRINTSTARTTIME}","{0:d}".format(trunc(round(self.PrintStartTime,3)*1000)))
		directoryName = directoryName.replace("{PRINTENDTIME}","{0:d}".format(trunc(round(self.PrintEndTime,3)*1000)))
		return directoryName
def DownloadSnapshotAsync(directoryName, fileName, url, logger, username = None, password = None, ignoreSslErrors = False):
		download_thread = threading.Thread(target=DownloadSnapshot, args=(directoryName, fileName, url, logger, username, password, ignoreSslErrors))
		logger.info("Snapshot - started async download.".format(url,dir))
		download_thread.start()

def DownloadSnapshot(directoryName, fileName, url, logger, username, password, ignoreSslErrors):
		try:
			dir = "{0:s}{1:s}".format(directoryName, fileName)
			r=None
			if(len(username)>0):
				logger.info("Snapshot - Authenticating and downloading from {0:s} to {1:s}.".format(url,dir))
				r=requests.get(url, auth=HTTPBasicAuth(username, password),verify = not ignoreSslErrors)
			else:
				logger.info("Snapshot - downloading from {0:s} to {1:s}.".format(url,dir))
				r=requests.get(url,verify = not ignoreSslErrors)

			if r.status_code == requests.codes.ok:
				try:
					os.makedirs(os.path.dirname(dir))
				except:
					logger.info("Snapshot - The directory for the download file {0:s} already exists.".format(dir))
				with iopen(dir, 'wb') as file:
					for chunk in r.iter_content(1024):
						if chunk:
							file.write(chunk)
					logger.info("Snapshot Written")
			else:
				logger.Warning("Snapshot - failed with status code:{0}".format(r.status_code))
				return False

		except Exception as e:
			
			logger.info("Snapshot - Downloading Error:{0:s}".format(e))
			return None

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
