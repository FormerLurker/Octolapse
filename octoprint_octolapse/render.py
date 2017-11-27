# coding=utf-8
import logging
import os
import threading
import time
import fnmatch
import datetime
import sys

import utility
import sarge
class Render(object):

	def __init__(self, settings, threadCount, onStart=None, onFail = None, onSuccess=None, onAlways = None):
		self.Settings = settings
		self.Debug = self.Settings.debug
		self.Snapshot = self.Settings.CurrentSnapshot()
		self.Rendering = self.Settings.CurrentRendering();
		self.ThreadCount = threadCount
		self.OnStart = onStart
		self.OnFail = onFail
		self.OnSuccess = onSuccess
		self.OnAlways = onAlways
		self.TimelapseRenderJobs = []
	def Process(self, printName, printStartTime, printEndTime):
		self.Debug.LogRenderStart("Starting.")
		# Get the capture file and directory info
		snapshotDirectory = utility.GetDirectoryFromTemplate(self.Snapshot.output_directory,printName,printStartTime, self.Snapshot.output_format)
		snapshotFileNameTemplate  = utility.GetFilenameFromTemplate(self.Snapshot.output_filename, printName, printStartTime, self.Snapshot.output_format, "%05d")
		# get the output file and directory info
		outputDirectory = utility.GetDirectoryFromTemplate(self.Rendering.output_directory,printName,printStartTime, self.Rendering.output_format,printEndTime)
		#self.Debug.LogInfo("OutputDirectory: {0}, Template:{1}, PrintName:{2}, printStartTime:{3}, outputFormat:{4}, printEndTime:{5}".format(outputDirectory,self.Rendering.output_directory,printName,printStartTime, self.Rendering.output_format,printEndTime))
		outputFilename = utility.GetFilenameFromTemplate(self.Rendering.output_filename, printName, printStartTime, self.Rendering.output_format, "",printEndTime)
		
		# get the number of frames
		foundFile = False
		imageIndex = 0

		fps = self.Rendering.fps
		if(self.Rendering.fps_calculation_type == 'duration'):
			imageIndex = 0
			while(foundFile):
				foundFile = False
				imagePath = "{0}{1}".format(outputDirectory, outputFileName) % imageIndex
				if(os.path.isfile(fname)):
					foundFile = True
					imageIndex += 1

			fps = float(imageIndex)/float(self.Rendering.run_length_seconds)
			if(fps > self.Rendering.max_fps):
				fps = self.Rendering.max_fps
			elif(fps < self.Rendering.min_fps):
				fps = self.Rendering.min_fps
			self.Debug.LogInfo("FPS Calculation Type:{0}, Fps:{1}, NumFrames:{2}, DurationSeconds:{3}".format(self.Rendering.fps_calculation_type,fps, imageIndex,self.Rendering.run_length_seconds))
		else:
			self.Debug.LogInfo("FPS Calculation Type:{0}, Fps:{0}".format(self.Rendering.fps_calculation_type,imageIndex,fps))
		job = TimelapseRenderJob(printName,
							snapshotDirectory
						   , snapshotFileNameTemplate
						   , outputDirectory
						   , outputFilename
						   , self.Rendering.output_format
						   , self.Rendering.ffmpeg_path
						   , self.Rendering.bitrate
						   , self.Rendering.flip_h
						   , self.Rendering.flip_v
						   , self.Rendering.rotate_90
						   , self.Rendering.watermark
						   , fps 
						   , threads= self.ThreadCount
						   , on_start= self.OnStart
						   , on_success = self.OnSuccess
						   , on_fail = self.OnFail
						   , on_always = self.OnAlways)
		job.process()

	
class RenderInfo(object):
	def __init__(self):
		self.FileName = ""
		self.Directory = ""

class TimelapseRenderJob(object):

	render_job_lock = threading.RLock()
#, capture_glob="{prefix}*.jpg", capture_format="{prefix}%d.jpg", output_format="{prefix}{postfix}.mpg",
	def __init__(self, printFileName, capture_dir, capture_template, output_dir, output_name, outputFormat, ffmpegPath, bitrate, flipH, flipV, rotate90, watermark,fps, threads,on_start=None, on_success=None, on_fail=None, on_always=None):
		self._printFileName = printFileName
		self._capture_dir = capture_dir
		self._capture_file_template = capture_template
		self._output_dir = output_dir
		self._output_file_name = output_name
		self._outputFormat = outputFormat
		self._fps = fps
		
		self._threads = threads
		self._ffmpeg = ffmpegPath
		self._bitrate = bitrate
		self._flip_h = flipH
		self._flip_v = flipV
		self._rotate_90 = rotate90
		self._watermark = watermark
		self._on_start = on_start
		self._on_success = on_success
		self._on_fail = on_fail
		self._on_always = on_always
		self._thread = None
		self._logger = logging.getLogger(__name__)

	def process(self):
		"""Processes the job."""

		self._thread = threading.Thread(target=self._render,
		                                name="TimelapseRenderJob_{name}".format(name = self._printFileName))
		self._thread.daemon = True
		self._thread.start()

	def _render(self):
		"""Rendering runnable."""

		
		if self._ffmpeg is None:
			self._logger.warn("Cannot create movie, path to ffmpeg is unset")
			return
		if self._bitrate is None:
			self._logger.warn("Cannot create movie, desired bitrate is unset")
			return

		input = os.path.join(self._capture_dir,
		                     self._capture_file_template)
		output = os.path.join(self._output_dir,
		                      self._output_file_name)

		try:
			#path = os.path.dirname(self._output_dir)
			self._logger.warn("Creating the directory at {0}".format(self._output_dir))
			if not os.path.exists(self._output_dir):
				os.makedirs(self._output_dir)
		except:
			type = sys.exc_info()[0]
			value = sys.exc_info()[1]
			self._logger.warn("Render - An exception was thrown when trying to save a create the rendering path at: {0} , ExceptionType:{1}, Exception Value:{2}".format(self._output_dir,type,value))
			return	

		self._logger.warn("Render - capture_dir:{0}, _capture_file_template:{1}, output_dir:{2}, _output_file_name:{3}, input path:{4}, output path:{5}".format(self._capture_dir, self._capture_file_template, self._output_dir, self._output_file_name,input,output))
		for i in range(4):
			if os.path.exists(input % i):
				break
		else:
			self._logger.warn("Cannot create a movie, no frames captured")
			self._notify_callback("fail", output, returncode=0, stdout="", stderr="", reason="no_frames")
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
		self._logger.debug("Executing command: {}".format(command_str))

		with self.render_job_lock:
			try:
				self._notify_callback("start", output)
				#self._logger.warn("command_str:{0}".format(command_str)) * Useful for debugging
					
				p = sarge.run(command_str, stdout=sarge.Capture(), stderr=sarge.Capture())
				if p.returncode == 0:
					self._notify_callback("success", output)
				else:
					returncode = p.returncode
					stdout_text = p.stdout.text
					stderr_text = p.stderr.text
					self._logger.warn("Could not render movie, got return code %r: %s" % (returncode, stderr_text))
					self._notify_callback("fail", output, returncode=returncode, stdout=stdout_text, stderr=stderr_text, reason="returncode")
			except:
				self._logger.exception("Could not render movie due to unknown error")
				self._notify_callback("fail", output, reason="unknown")
			finally:
				self._notify_callback("always", output)

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




