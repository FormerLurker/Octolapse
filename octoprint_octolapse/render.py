
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
from octoprint_octolapse.settings import Rendering
class Render(object):

	def __init__(self, settings, snapshot, rendering, dataDirectory, octoprintTimelapseFolder, ffmpegPath, threadCount
			  ,timeAdded = 0
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
		self.Snapshot = snapshot
		self.Rendering = rendering
		self.ThreadCount = threadCount
		self.TimeAdded = timeAdded
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
		snapshotDirectory = utility.GetSnapshotTempDirectory(self.DataDirectory, printName,printStartTime)
		snapshotFileNameTemplate  = utility.GetSnapshotFilename(printName, printStartTime, utility.SnapshotNumberFormat)
		# get the output file and directory info
		outputDirectory = utility.GetRenderingDirectory(self.DataDirectory, printName,printStartTime, self.Rendering.output_format,printEndTime)

		outputFilename = utility.GetRenderingBaseFilename(printName, printStartTime,printEndTime)
		
		job = TimelapseRenderJob(
							self.Rendering
							,self.Settings.CurrentDebugProfile()
							, printName
						   , snapshotDirectory
						   , snapshotFileNameTemplate
						   , outputDirectory
						   , outputFilename
						   , self.OctoprintTimelapseFolder
						   , self.FfmpegPath
						   , self.ThreadCount
						   , timeAdded = self.TimeAdded
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
	def __init__(self
			  , rendering
			  , debug
			  , printFileName
			  , capture_dir
			  , capture_template
			  , output_dir
			  , output_name
			  , octoprintTimelapseFolder
			  ,  ffmpegPath
			  , threads
			  , timeAdded = 0
			  , on_render_start=None
			  , on_render_fail=None
			  , on_render_success=None
			  , on_render_complete=None
			  , on_after_sync_success = None
			  , on_after_sync_fail = None
			  , on_complete = None
			  , cleanAfterSuccess = False
			  , cleanAfterFail = False
			  , syncWithTimelapse = False):
		self._rendering = Rendering(rendering)
		self._debug = debug;
		self._printFileName = printFileName
		self._capture_dir = capture_dir
		self._capture_file_template = capture_template
		self._output_dir = output_dir
		self._output_file_name = output_name
		self._octoprintTimelapseFolder = octoprintTimelapseFolder
		self._fps = None
		self._imageCount = None
		self._timeAdded = timeAdded
		self._threads = threads
		self._ffmpeg = ffmpegPath
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
		# do our file operations first, this seems to crash rendering if we do it inside the thread.  Of course.
		self._pre_render();
		self._thread = threading.Thread(target=self._render,
		                                name="TimelapseRenderJob_{name}".format(name = self._printFileName))
		self._thread.daemon = True
		self._thread.start()

	def _pre_render(self):
		#
		self._imageCount = self._countImages(self._capture_dir, self._capture_file_template)
		if(self._imageCount == 0):
			self._renderFail(output, baseOutputFileName, "No images were captured.")
			return;
		self._fps = self._rendering.fps

		if(self._rendering.fps_calculation_type == 'duration'):
			
			self._fps = float(self._imageCount)/float(self._rendering.run_length_seconds)
			if(self._fps > self._rendering.max_fps):
				self._fps = self._rendering.max_fps
			elif(self._fps < self._rendering.min_fps):
				self._fps = self._rendering.min_fps
			self._debug.LogRenderStart("FPS Calculation Type:{0}, Fps:{1}, NumFrames:{2}, DurationSeconds:{3}, Max FPS:{4}, Min FPS:{5}".format(self._rendering.fps_calculation_type,self._fps, self._imageCount,self._rendering.run_length_seconds,self._rendering.max_fps,self._rendering.min_fps))
		else:
			self._debug.LogRenderStart("FPS Calculation Type:{0}, Fps:{0}".format(self._rendering.fps_calculation_type,self._fps))


		# apply pre-post roll
		# Apply the pre-roll and post-roll
		
		self._applyPrePostRoll(self._capture_dir, self._capture_file_template, self._fps, self._imageCount)

	def _renderFail(self, output, baseOutputFileName, message):
		self._notify_callback("render_fail", output, baseOutputFileName,0,message)
		self._debug.LogRenderFail(message);

	def _render(self):
		"""Rendering runnable."""
		success = False
		# create variables we will need for callbacks and processing
		input = os.path.join(self._capture_dir,
								self._capture_file_template)
		output = os.path.join(self._output_dir,
								self._output_file_name)

		baseOutputFileName = utility.GetFilenameFromFullPath(output)
		synchronize = self.syncWithTimelapse and self._rendering.output_format == "mp4"
		try:
			
			
			# notify any listeners that we are rendering.

			self._notify_callback("render_start", output, baseOutputFileName,synchronize, self._imageCount, self._timeAdded)

			if self._ffmpeg is None:
				self._renderFail(output, baseOutputFileName, "Cannot create movie, path to ffmpeg is unset")
				return
			if self._rendering.bitrate is None:
				self._renderFail(output, baseOutputFileName, "Cannot create movie, desired bitrate is unset")
				return

			# add the file extension
			output = output + "." + self._rendering.output_format
			try:
				#path = os.path.dirname(self._output_dir)
				self._logger.warn("Creating the directory at {0}".format(self._output_dir))
				if not os.path.exists(self._output_dir):
					os.makedirs(self._output_dir)
			except:
				type = sys.exc_info()[0]
				value = sys.exc_info()[1]
				self._renderFail(output, baseOutputFileName, "Render - An exception was thrown when trying to create the rendering path at: {0} , ExceptionType:{1}, Exception Value:{2}".format(self._output_dir,type,value))
				return	
			# will it render with only one frame?
			for i in range(1,2):
				if os.path.exists(input % i):
					break
			else:
				self._renderFail(output, baseOutputFileName, 'Cannot create a movie, no frames captured.')
				return

			watermark = None
			if self._rendering.watermark:
				watermark = os.path.join(os.path.dirname(__file__), "static", "img", "watermark.png")
				if sys.platform == "win32":
					# Because ffmpeg hiccups on windows' drive letters and backslashes we have to give the watermark
					# path a special treatment. Yeah, I couldn't believe it either...
					watermark = watermark.replace("\\", "/").replace(":", "\\\\:")

			# prepare ffmpeg command
			command_str = self._create_ffmpeg_command_string(self._ffmpeg, self._fps, self._rendering.bitrate, self._threads, input, output, self._rendering.output_format,
															 hflip=self._rendering.flip_h, vflip=self._rendering.flip_v, rotate=self._rendering.rotate_90, watermark=watermark )
		
			with self.render_job_lock:
			
				try:
				
					#self._logger.warn("command_str:{0}".format(command_str)) * Useful for debugging
					
					p = sarge.run(command_str, stdout=sarge.Capture(), stderr=sarge.Capture())
					if p.returncode == 0:
						self._notify_callback("render_success", output,baseOutputFileName)
						success = True
					else:
						returncode = p.returncode
						stdout_text = p.stdout.text
						stderr_text = p.stderr.text
						self._renderFail(output, baseOutputFileName, "Could not render movie, got return code %r: %s" % (returncode, stderr_text))
				except:
					self._renderFail(output, baseOutputFileName, "Could not render movie due to unknown error")
				finally:
					self._notify_callback("render_complete", output, baseOutputFileName,0,'unknown')
				cleanSnapshots = (success and self.cleanAfterSuccess) or self.cleanAfterFail
				if(cleanSnapshots):
					self._CleanSnapshots()

				finalFileName = baseOutputFileName
				if(synchronize):
					finalFileName = "{0}{1}{2}".format(self._octoprintTimelapseFolder,  os.sep, baseOutputFileName + "." + self._rendering.output_format)
					# Move the timelapse to the Octoprint timelapse folder.
					try:
						# get the timelapse folder for the Octoprint timelapse plugin
						self._debug.LogRenderSync("Syncronizing timelapse with the built in timelapse plugin, copying {0} to {1}".format(output,finalFileName))
						shutil.move(output,finalFileName)
						self._notify_callback("after_sync_success", finalFileName, baseOutputFileName)
					except Exception, e:
						self._debug.LogException(e)
						self._notify_callback("after_sync_fail", finalFileName,baseOutputFileName)

				self._notify_callback("complete", finalFileName, baseOutputFileName,synchronize, success)
		except TypeError, e:
			self.Settings.CurrentDebugProfile().LogException(e)
			self._renderFail(output, baseOutputFileName, 'An unexpected exception occurred.  Please check plugin_octolapse.log for details.')
	def _countImages(self, snapshotDirectory, snapshotFileNameTemplate):
		"""get the number of frames"""
		self._debug.LogRenderStart("Searching for frames.")
		# we need to start with index 1.
		imageIndex = 1
		while(True):
			foundFile = False
			imagePath = "{0}{1}".format(snapshotDirectory,snapshotFileNameTemplate) % imageIndex
				
			if(os.path.isfile(imagePath)):
				imageIndex += 1
			else:
				break
		imageCount = imageIndex - 1
		self._debug.LogRenderStart("Found {0} images.".format(imageCount))
		return imageCount

	def _applyPrePostRoll(self, snapshotDirectory, snapshotFileNameTemplate, fps, imageCount):
		# start with pre-roll, since it will require a bunch of renaming
		preRollFrames = int(utility.round_to(self._rendering.pre_roll_seconds * fps,1))
		if(preRollFrames > 0):

			# create a variable to hold the new path of the first image
			firstImagePath = ""
			# rename all of the current files.  The snapshot number should be incremented by the number of pre-roll frames
			for imageIndex in xrange(1,imageCount + 1):
				currentImagePath = "{0}{1}".format(snapshotDirectory, snapshotFileNameTemplate) % imageIndex
				newImagePath = "{0}{1}".format(snapshotDirectory, snapshotFileNameTemplate) % (imageIndex+preRollFrames)
				if(imageIndex == 1):
					firstImagePath = newImagePath

				shutil.move(currentImagePath,newImagePath)	

			# get the path of the first image
			# copy the first frame as many times as we need
			for imageIndex in xrange(preRollFrames,0,-1):
				newImagePath = "{0}{1}".format(snapshotDirectory,snapshotFileNameTemplate) % (imageIndex)
				shutil.copy(firstImagePath,newImagePath)	
		# finish with post roll since it's pretty easy
		postRollFrames =  int(utility.round_to(self._rendering.post_roll_seconds * fps,1))
		if(postRollFrames > 0):
			lastImagePath = "{0}{1}".format(snapshotDirectory, snapshotFileNameTemplate) % (imageCount + preRollFrames)
			for imageIndex in xrange(1,postRollFrames+1):
				newImagePath = "{0}{1}".format(snapshotDirectory,snapshotFileNameTemplate) % (imageIndex + imageCount + preRollFrames)
				shutil.copy(lastImagePath,newImagePath)


	def _CleanSnapshots(self):
		
		# get snapshot directory
		self._debug.LogSnapshotClean("Cleaning snapshots from: {0}".format(self._capture_dir))

		path = os.path.dirname(self._capture_dir + os.sep)
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




