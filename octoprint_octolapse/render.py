import os
import sys
import time

class Render(object):

	def __init__(self,profile, printer_file_name):
		self.Profile = profile
		self.PrinterFileName = printer_file_name

	def TakeSnapshot(self,printerFileName):
		info = SnapshotInfo()
		# set the file name
		info.SnapshotFileName = GetFileName()
		
		# call the snapshot command
		try:
			r = os.system("{0:s} --ffmpeg_path {2:s} --output_directory {3:s} --output_file_name {4:s} --user_name {5:s} --password {6:s} --snapshot_address {7:s} ".format(
					self.Profile.snapshot.script_path, self.Profile.snapshot.ffmpeg_path, self.Profile.snapshot.output_directory, info.SnapshotFileName, self.Profile.printer.user_name, self.Profile.printer.password ))
		except:
			e = sys.exc_info()[0]
			self._logger.exception("Error executing command ID %s: %s" % (cmd_id, e))
			return None
		return info


	def GetFileName(self):
		return self.Profile.file_options.output_filename.replace("{FILENAME}",self.PrinterFileName).replace("{DATETIMESTAMP}",time.time()).replace("",self.Profile.rendering.output_format)

class RenderInfo(object):
	def __init__(self):
		self.FileName = ""






