
# coding=utf-8
import logging
import os
import threading
import time
import fnmatch
import datetime
import sys
import shutil
import octoprint_octolapse.utility as utility
import sarge

class Render(object):

	def __init__(self, settings, dataDirectory, octoprintTimelapseFolder, ffmpegPath, threadCount
			  ,onRenderStart=None
			  ,onRenderFail = None
			  ,onRenderSuccess=None
			  ,onRenderComplete=None
			  ,onAfterSyncFail = None
			  ,onAfterSycnSuccess = None
			  ,onComplete = None ):
		self.Settings = settings
		self.DataDirectory = dataDirectory
		self.OctoprintTimelapseFolder = octoprintTimelapseFolder
		self.FfmpegPath = ffmpegPath
		self.Snapshot = self.Settings.CurrentSnapshot()
		self.Rendering = self.Settings.CurrentRendering();
		self.ThreadCount = threadCount
		self.OnRenderStart = onRenderStart
		self.OnRenderFail = onRenderFail
		self.OnRenderSuccess = onRenderSuccess
		self.OnRenderComplete = onRenderComplete
		self.OnAfterSyncFail = onAfterSyncFail
		self.OnAfterSycnSuccess = onAfterSycnSuccess
		self.OnComplete = onComplete
		self.TimelapseRenderJobs = []

	def Process(self, printName, printStartTime, printEndTime):
		self.Settings.CurrentDebugProfile().LogRenderStart("Rendering is starting.")
		# Get the capture file and directory info
		snapshotDirectory = utility.GetDirectoryFromTemplate(self.Snapshot.output_directory,self.DataDirectory, printName,printStartTime, self.Snapshot.output_format)
		snapshotFileNameTemplate  = utility.GetSnapshotFilenameFromTemplate(self.Snapshot.output_filename, printName, printStartTime, self.Snapshot.output_format, "%05d")
		# get the output file and directory info
		outputDirectory = utility.GetDirectoryFromTemplate(self.Rendering.output_directory,self.DataDirectory, printName,printStartTime, self.Rendering.output_format,printEndTime)

		outputFilename = utility.GetRenderingFilenameFromTemplate(self.Rendering.output_filename, printName, printStartTime, self.Rendering.output_format,printEndTime)
		
		
		# get the number of frames
		foundFile = True
		imageIndex = 0

		fps = self.Rendering.fps
		if(self.Rendering.fps_calculation_type == 'duration'):
			imageIndex = 1
			while(foundFile):
				foundFile = False
				imagePath = "{0}{1}".format(snapshotDirectory, snapshotFileNameTemplate) % imageIndex
				
				if(os.path.isfile(imagePath)):
					foundFile = True
					imageIndex += 1
					self.Settings.CurrentDebugProfile().LogRenderStart("Found image:{0}".format(imagePath))
				else:
					self.Settings.CurrentDebugProfile().LogRenderStart("Could not find image:{0}, search complete.".format(imagePath))
			imageCount = imageIndex - 1
			self.Settings.CurrentDebugProfile().LogRenderStart("Found {0} images.".format(imageCount))
			fps = float(imageCount)/float(self.Rendering.run_length_seconds)
			if(fps > self.Rendering.max_fps):
				fps = self.Rendering.max_fps
			elif(fps < self.Rendering.min_fps):
				fps = self.Rendering.min_fps
			self.Settings.CurrentDebugProfile().LogRenderStart("FPS Calculation Type:{0}, Fps:{1}, NumFrames:{2}, DurationSeconds:{3}, Max FPS:{4}, Min FPS:{5}".format(self.Rendering.fps_calculation_type,fps, imageCount,self.Rendering.run_length_seconds,self.Rendering.max_fps,self.Rendering.min_fps))
		else:
			self.Settings.CurrentDebugProfile().LogRenderStart("FPS Calculation Type:{0}, Fps:{0}".format(self.Rendering.fps_calculation_type,imageIndex,fps))
		job = TimelapseRenderJob(
							self.Settings.CurrentDebugProfile()
							, printName
						   , snapshotDirectory
						   , snapshotFileNameTemplate
						   , outputDirectory
						   , outputFilename
						   , self.Rendering.output_format
						   , self.OctoprintTimelapseFolder
						   , self.FfmpegPath
						   , self.Rendering.bitrate
						   , self.Rendering.flip_h
						   , self.Rendering.flip_v
						   , self.Rendering.rotate_90
						   , self.Rendering.watermark
						   , fps 
						   , threads= self.ThreadCount
						   , on_render_start= self.OnRenderStart
						   , on_render_fail = self.OnRenderFail
						   , on_render_success = self.OnRenderSuccess
						   , on_render_complete = self.OnRenderComplete
						   , on_after_sync_fail = self.OnAfterSyncFail
						   , on_after_sync_success = self.OnAfterSycnSuccess
						   , on_complete = self.OnComplete
						   , cleanAfterSuccess = self.Snapshot.cleanup_after_render_complete
						   , cleanAfterFail = self.Snapshot.cleanup_after_render_complete
						   , syncWithTimelapse = self.Rendering.sync_with_timelapse)
		job.process()

	
class RenderInfo(object):
	def __init__(self):
		self.FileName = ""
		self.Directory = ""

class TimelapseRenderJob(object):

	render_job_lock = threading.RLock()
#, capture_glob="{prefix}*.jpg", capture_format="{prefix}%d.jpg", output_format="{prefix}{postfix}.mpg",
	def __init__(self, debug, printFileName, capture_dir, capture_template, output_dir, output_name, outputFormat, octoprintTimelapseFolder,  ffmpegPath, bitrate, flipH, flipV, rotate90, watermark,fps
			  , threads,on_render_start=None, on_render_fail=None, on_render_success=None, on_render_complete=None, on_after_sync_success = None, on_after_sync_fail = None, on_complete = None
			  , cleanAfterSuccess = False
			  , cleanAfterFail = False
			  , syncWithTimelapse = False):
		self._debug = debug;
		self._printFileName = printFileName
		self._capture_dir = capture_dir
		self._capture_file_template = capture_template
		self._output_dir = output_dir
		self._output_file_name = output_name
		self._outputFormat = outputFormat
		self._octoprintTimelapseFolder = octoprintTimelapseFolder
		self._fps = fps
		
		self._threads = threads
		self._ffmpeg = ffmpegPath
		self._bitrate = bitrate
		self._flip_h = flipH
		self._flip_v = flipV
		self._rotate_90 = rotate90
		self._watermark = watermark
		self._on_render_start = on_render_start
		self._on_render_fail = on_render_fail
		self._on_render_success = on_render_success
		self._on_render_complete = on_render_complete
		self._on_after_sync_success = on_after_sync_success
		self._on_after_sync_fail = on_after_sync_fail
		self._on_complete = on_complete
		self._thread = None
		self._logger = logging.getLogger(__name__)
		self.cleanAfterSuccess = cleanAfterSuccess 
		self.cleanAfterFail = cleanAfterFail 
		self.syncWithTimelapse = syncWithTimelapse

	def process(self):
		"""Processes the job."""
		self._thread = threading.Thread(target=self._render,
		                                name="TimelapseRenderJob_{name}".format(name = self._printFileName))
		self._thread.daemon = True
		self._thread.start()

	def _render(self):
		"""Rendering runnable."""
		if self._ffmpeg is None:
			self._debug.LogWarning("Cannot create movie, path to ffmpeg is unset")
			return
		if self._bitrate is None:
			self._debug.LogWarning("Cannot create movie, desired bitrate is unset")
			return

		input = os.path.join(self._capture_dir,
		                     self._capture_file_template)
		output = os.path.join(self._output_dir,
		                      self._output_file_name)

		baseOutputFileName = utility.GetFilenameFromFullPath(output)
		try:
			#path = os.path.dirname(self._output_dir)
			self._logger.warn("Creating the directory at {0}".format(self._output_dir))
			if not os.path.exists(self._output_dir):
				os.makedirs(self._output_dir)
		except:
			type = sys.exc_info()[0]
			value = sys.exc_info()[1]
			self._debug.LogError("Render - An exception was thrown when trying to save a create the rendering path at: {0} , ExceptionType:{1}, Exception Value:{2}".format(self._output_dir,type,value))
			return	

		for i in range(4):
			if os.path.exists(input % i):
				break
		else:
			self._debug.LogWarning("Cannot create a movie, no frames captured")
			self._notify_callback("fail", output, baseOutputFileName,0,'no_frames')
			return

		watermark = None
		if self._watermark:
			watermark = os.path.join(os.path.dirname(__file__), "static", "img", "watermark.png")
			if sys.platform == "win32":
				# Because ffmpeg hiccups on windows' drive letters and backslashes we have to give the watermark
				# path a special treatment. Yeah, I couldn't believe it either...
				watermark = watermark.replace("\\", "/").replace(":", "\\\\:")

		# prepare ffmpeg command
		command_str = self._create_ffmpeg_command_string(self._ffmpeg, self._fps, self._bitrate, self._threads, input, output, self._outputFormat,
		                                                 hflip=self._flip_h, vflip=self._flip_v, rotate=self._rotate_90, watermark=watermark )
		success = False
		with self.render_job_lock:
			try:
				self._notify_callback("render_start", output, baseOutputFileName)
				#self._logger.warn("command_str:{0}".format(command_str)) * Useful for debugging
					
				p = sarge.run(command_str, stdout=sarge.Capture(), stderr=sarge.Capture())
				if p.returncode == 0:
					self._notify_callback("render_success", output,baseOutputFileName)
					success = True
				else:
					returncode = p.returncode
					stdout_text = p.stdout.text
					stderr_text = p.stderr.text
					self._debug.LogWarning("Could not render movie, got return code %r: %s" % (returncode, stderr_text))
					self._notify_callback("render_fail", output, baseOutputFileName, returncode,stderr_text)
			except:
				self._debug.LogError("Could not render movie due to unknown error")
				# clean after fail
				self._notify_callback("render_fail", output, baseOutputFileName,0,'unknown')
			finally:
				self._notify_callback("render_complete", output, baseOutputFileName,0,'unknown')
			cleanSnapshots = (success and self.cleanAfterSuccess) or self.cleanAfterFail
			if(cleanSnapshots):
				self._CleanSnapshots()

		
			if(self.syncWithTimelapse):
				finalFileaName = "{0}{1}{2}".format(self._octoprintTimelapseFolder,  os.sep, baseOutputFileName)
				# Move the timelapse to the Octoprint timelapse folder.
				try:
					# get the timelapse folder for the Octoprint timelapse plugin
					self._debug.LogRenderSync("Syncronizing timelapse with the built in timelapse plugin, copying {0} to {1}".format(output,finalFileaName))
					shutil.move(output,finalFileaName)
					self._notify_callback("after_sync_success", finalFileaName, baseOutputFileName)
				except:
					type = sys.exc_info()[0]
					value = sys.exc_info()[1]
					message = "Could move the timelapse at {0} to the octoprint timelaspse directory.  Details: Error Type:{1}, Details:{2}".format(finalFileaName,type,value)
					self._debug.LogError(message)
					self._notify_callback("after_sync_fail", finalFileaName, baseOutputFileName, message)
				
			self._notify_callback("complete")

	def _CleanSnapshots(self):
		
		# get snapshot directory
		self._debug.LogSnapshotClean("Cleaning snapshots from: {0}".format(self._capture_dir))

		
		path = os.path.dirname(self._capture_dir)
		if(os.path.isdir(path)):
			try:
				shutil.rmtree(path)
				self._debug.LogSnapshotClean("Snapshots cleaned.")
			except:
				type = sys.exc_info()[0]
				value = sys.exc_info()[1]
				self._debug.LogWarning("Snapshot - Clean - Unable to clean the snapshot path at {0}.  It may already have been cleaned.  Info:  ExceptionType:{1}, Exception Value:{2}".format(path,type,value))
		else:
			self._debug.LogWarning("Snapshot - No need to clean snapshots: they have already been removed.")	

	@classmethod
	def _create_ffmpeg_command_string(cls, ffmpeg, fps, bitrate, threads, input, output, outputFormat = 'vob',hflip=False, vflip=False,
	                                  rotate=False, watermark=None, pixfmt="yuv420p"):
		"""
		Create ffmpeg command string based on input parameters.
		Arguments:
		    ffmpeg (str): Path to ffmpeg
		    fps (int): Frames per second for output
		    bitrate (str): Bitrate of output
		    threads (int): Number of threads to use for rendering
		    input (str): Absolute path to input files including file mask
		    output (str): Absolute path to output file
		    hflip (bool): Perform horizontal flip on input material.
		    vflip (bool): Perform vertical flip on input material.
		    rotate (bool): Perform 90° CCW rotation on input material.
		    watermark (str): Path to watermark to apply to lower left corner.
		    pixfmt (str): Pixel format to use for output. Default of yuv420p should usually fit the bill.
		Returns:
		    (str): Prepared command string to render `input` to `output` using ffmpeg.
		"""

		### See unit tests in test/timelapse/test_timelapse_renderjob.py

		logger = logging.getLogger(__name__)
		ffmpeg = ffmpeg.strip()

		if (sys.platform == "win32" and not (ffmpeg.startswith('"') and ffmpeg.endswith('"'))):
			ffmpeg = "\"{0}\"".format(ffmpeg)
		command = [
			ffmpeg, '-framerate', str(fps), '-loglevel', 'error', '-i', '"{}"'.format(input), '-vcodec', 'mpeg2video',
			'-threads', str(threads), '-r', "25", '-y', '-b', str(bitrate),
			'-f', str(outputFormat)]

		filter_string = cls._create_filter_string(hflip=hflip,
		                                          vflip=vflip,
		                                          rotate=rotate,
		                                          watermark=watermark)

		if filter_string is not None:
			logger.debug("Applying videofilter chain: {}".format(filter_string))
			command.extend(["-vf", sarge.shell_quote(filter_string)])

		# finalize command with output file
		logger.debug("Rendering movie to {}".format(output))
		command.append('"{}"'.format(output))

		return " ".join(command)

	@classmethod
	def _create_filter_string(cls, hflip=False, vflip=False, rotate=False, watermark=None, pixfmt="yuv420p"):
		"""
		Creates an ffmpeg filter string based on input parameters.
		Arguments:
		    hflip (bool): Perform horizontal flip on input material.
		    vflip (bool): Perform vertical flip on input material.
		    rotate (bool): Perform 90° CCW rotation on input material.
		    watermark (str): Path to watermark to apply to lower left corner.
		    pixfmt (str): Pixel format to use, defaults to "yuv420p" which should usually fit the bill
		Returns:
		    (str or None): filter string or None if no filters are required
		"""

		### See unit tests in test/timelapse/test_timelapse_renderjob.py

		# apply pixel format
		filters = ["format={}".format(pixfmt)]

		# flip video if configured
		if hflip:
			filters.append('hflip')
		if vflip:
			filters.append('vflip')
		if rotate:
			filters.append('transpose=2')

		# add watermark if configured
		watermark_filter = None
		if watermark is not None:
			watermark_filter = "movie={} [wm]; [{{input_name}}][wm] overlay=10:main_h-overlay_h-10".format(watermark)

		filter_string = None
		if len(filters) > 0:
			if watermark_filter is not None:
				filter_string = "[in] {} [postprocessed]; {} [out]".format(",".join(filters),
				                                                           watermark_filter.format(input_name="postprocessed"))
			else:
				filter_string = "[in] {} [out]".format(",".join(filters))
		elif watermark_filter is not None:
			filter_string = watermark_filter.format(input_name="in") + " [out]"

		return filter_string

	def _notify_callback(self, callback, *args, **kwargs):
		"""Notifies registered callbacks of type `callback`."""
		name = "_on_{}".format(callback)
		method = getattr(self, name, None)
		if method is not None and callable(method):
			method(*args, **kwargs)




