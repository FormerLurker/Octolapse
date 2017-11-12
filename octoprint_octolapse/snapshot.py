import os
import sys
import time
import utility
import requests
from requests.auth import HTTPBasicAuth
from io import open as iopen
from urlparse import urlsplit


class Snapshot(object):

	def __init__(self,profile,logger):
		self.Profile = profile
		self.Logger = logger
		self.PrintStartTime = time.time()
		self.PrintEndTime = time.time()

	def SetPrintStartTime(self,time):
		self.PrintStartTime = time

	def SetPrintEndTime(self,time):
		self.PrinEndtTime = time

	def Snap(self,printerFileName):
		# strip off the extension
		printerFileName = os.path.splitext(printerFileName)[0]

		info = SnapshotInfo()
		# set the file name
		info.FileName = self.GetSnapshotFileName(printerFileName)
		info.DirectoryName = self.GetSnapshotDirectoryName(printerFileName)
		# call the snapshot command
			
		#
		#if(len(self.Profile.snapshot.snapshot_camera_username) > 0):
		#	cmd = "{0:s} --output_directory {1:s} --output_file_name {2:s} --user_name {3:s} --password {4:s} --snapshot_address {5:s}"
		#	cmd = cmd.format(self.Profile.snapshot.script_path, info.DirectoryName, info.FileName, self.Profile.snapshot.snapshot_camera_username, self.Profile.snapshot.snapshot_camera_password, self.Profile.snapshot.snapshot_camera_address)
		#else:
		#	cmd = "{0:s} --output_directory {1:s} --output_file_name {2:s} --snapshot_address {5:s} "
		#	cmd = cmd.format(self.Profile.snapshot.script_path, info.DirectoryName, info.FileName, self.Profile.snapshot.snapshot_camera_username, self.Profile.snapshot.snapshot_camera_password, self.Profile.snapshot.snapshot_camera_address)

		#self.Logger.info("Octolapse - Executing snap script at: {0:s}".format(cmd))

		try:
			#r = os.system(cmd)
			dir = "{0:s}{1:s}".format(info.DirectoryName, info.FileName)
			r=None
			if(len(self.Profile.camera.username)>0):
				self.Logger.info("Octolapse is authenticating and downloading from {0:s} to {1:s}".format(self.Profile.camera.address,dir))
				r=requests.get(self.Profile.camera.address, auth=HTTPBasicAuth(self.Profile.camera.username, self.Profile.camera.password),verify = not self.Profile.camera.ignore_ssl_error)
			else:
				self.Logger.info("Octolapse is downloading from {0:s} to {1:s}".format(self.Profile.camera.address,dir))
				r=requests.get(self.Profile.camera.address,verify = not self.Profile.camera.ignore_ssl_error)

			if r.status_code == requests.codes.ok:
				os.makedirs(os.path.dirname(dir))
				with iopen(dir, 'wb') as file:
					file.write(r.content)
			else:
				return False

		except Exception as e:
			print(e)
			self.Logger.info("Octolapse - Error downloading snapshot:{0:s}".format(e))
			return None
		return info


	def GetSnapshotFileName(self,printerFileName):
		filename = self.Profile.snapshot.output_filename
		if(not filename):
			filename = "snapshot_{DATETIMESTAMP}.{OUTPUTFILEEXTENSION}"
		filename = filename.replace("{FILENAME}",utility.getstring(printerFileName,""))
		filename = filename.replace("{DATETIMESTAMP}",str(int(time.time())))
		filename = filename.replace("{OUTPUTFILEEXTENSION}",utility.getstring(self.Profile.snapshot.output_format,""))
		filename = filename.replace("{PRINTSTARTTIME}","{0:.0f}".format(self.PrintStartTime))
		filename = filename.replace("{PRINTENDTIME}","{0:0.0f}".format(self.PrintEndTime))
		return filename


	def GetSnapshotDirectoryName(self,printerFileName):
		directoryName = self.Profile.snapshot.output_directory
		if(not directoryName):
			directoryName = "./snapshots/{FILENAME}/{PRINTSTARTTIME}"

		directoryName = directoryName.replace("{FILENAME}",utility.getstring(printerFileName,""))
		directoryName = directoryName.replace("{DATETIMESTAMP}",str(int(time.time())))
		directoryName = directoryName.replace("{OUTPUTFILEEXTENSION}",utility.getstring(self.Profile.snapshot.output_format,""))
		directoryName = directoryName.replace("{PRINTSTARTTIME}","{0:0.0f}".format(self.PrintStartTime))
		directoryName = directoryName.replace("{PRINTENDTIME}","{0:0.0f}".format(self.PrintEndTime))
		return directoryName


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







