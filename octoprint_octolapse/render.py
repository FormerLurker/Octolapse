# coding=utf-8

# This file is subject to the terms and conditions defined in
# file called 'LICENSE', which is part of this source code package.


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

    def __init__(
            self, settings, snapshot, rendering, dataDirectory,
            octoprintTimelapseFolder, ffmpegPath, threadCount,
            timeAdded=0, onRenderStart=None, onRenderFail=None,
            onRenderSuccess=None, onRenderComplete=None, onAfterSyncFail=None,
            onAfterSycnSuccess=None, onComplete=None):
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
        snapshotDirectory = utility.GetSnapshotTempDirectory(
            self.DataDirectory)
        snapshotFileNameTemplate = utility.GetSnapshotFilename(
            printName, printStartTime, utility.SnapshotNumberFormat)
        # get the output file and directory info
        outputDirectory = utility.GetRenderingDirectory(
            self.DataDirectory, printName, printStartTime, self.Rendering.output_format, printEndTime)

        outputFilename = utility.GetRenderingBaseFilename(
            printName, printStartTime, printEndTime)

        job = TimelapseRenderJob(
            self.Rendering,
            self.Settings.CurrentDebugProfile(),
            printName,
            snapshotDirectory,
            snapshotFileNameTemplate,
            outputDirectory,
            outputFilename,
            self.OctoprintTimelapseFolder,
            self.FfmpegPath,
            self.ThreadCount,
            timeAdded=self.TimeAdded,
            on_render_start=self.OnRenderStart,
            on_render_fail=self.OnRenderFail,
            on_render_success=self.OnRenderSuccess,
            on_render_complete=self.OnRenderComplete,
            on_after_sync_fail=self.OnAfterSyncFail,
            on_after_sync_success=self.OnAfterSycnSuccess,
            on_complete=self.OnComplete,
            cleanAfterSuccess=self.Snapshot.cleanup_after_render_complete,
            cleanAfterFail=self.Snapshot.cleanup_after_render_complete
        )

        job.process()


class RenderInfo(object):
    def __init__(self):
        self.FileName = ""
        self.Directory = ""


class TimelapseRenderJob(object):

    render_job_lock = threading.RLock()
#, capture_glob="{prefix}*.jpg", capture_format="{prefix}%d.jpg", output_format="{prefix}{postfix}.mpg",

    def __init__(
            self, rendering, debug, printFileName,
            capture_dir, capture_template, output_dir,
            output_name, octoprintTimelapseFolder,
            ffmpegPath, threads, timeAdded=0,
            on_render_start=None, on_render_fail=None,
            on_render_success=None, on_render_complete=None,
            on_after_sync_success=None, on_after_sync_fail=None,
            on_complete=None, cleanAfterSuccess=False,
            cleanAfterFail=False):
        self._rendering = Rendering(rendering)
        self._debug = debug
        self._printFileName = printFileName
        self._capture_dir = capture_dir
        self._capture_file_template = capture_template
        self._output_dir = output_dir
        self._output_file_name = output_name
        self._octoprintTimelapseFolder = octoprintTimelapseFolder
        self._fps = None
        self._imageCount = None
        self._secondsAddedToPrint = timeAdded
        self._threads = threads
        self._ffmpeg = ffmpegPath

        ###########
        # callbacks
        ###########
        self._render_start_callback = on_render_start
        self._render_fail_callback = on_render_fail
        self._render_success_callback = on_render_success
        self._render_complete_callback = on_render_complete
        self._after_sync_success_callback = on_after_sync_success
        self._after_sync_fail_callback = on_after_sync_fail
        self._on_complete_callback = on_complete

        self._thread = None
        self.cleanAfterSuccess = cleanAfterSuccess
        self.cleanAfterFail = cleanAfterFail
        self._input = ""
        self._output = ""
        self._synchronize = False
        self._baseOutputFileName = ""

    def process(self):
        """Processes the job."""
        # do our file operations first, this seems to crash rendering if we do it inside the thread.  Of course.
        self._input = os.path.join(self._capture_dir,
                                   self._capture_file_template)
        self._output = os.path.join(self._output_dir,
                                    self._output_file_name)

        self._baseOutputFileName = utility.GetFilenameFromFullPath(
            self._output)
        self._synchronize = (
            self._rendering.sync_with_timelapse and self._rendering.output_format == "mp4")

        self._thread = threading.Thread(target=self._render,
                                        name="TimelapseRenderJob_{name}".format(name=self._printFileName))
        self._thread.daemon = True
        self._thread.start()

    def _pre_render(self):

        try:
            self._countImages()
            if self._imageCount == 0:
                self._debug.LogRenderFail(
                    "No images were captured, or they have been removed.")
                return False
            if self._imageCount == 1:
                self._debug.LogRenderFail(
                    "Only 1 frame was captured, cannot make a timelapse with a single frame.")
                return False
            # calculate the FPS
            self._calculateFps()
            if self._fps < 1:
                self._debug.LogError(
                    "The calculated FPS is below 1, which is not allowed. "
                    "Please check the rendering settings for Min and Max FPS "
                    "as well as the number of snapshots captured."
                )
                return False
            # apply pre and post roll
            self._applyPrePostRoll(
                self._capture_dir, self._capture_file_template, self._fps, self._imageCount)
            return True
        except Exception as e:
            self._debug.LogException(e)
        return False

    def _calculateFps(self):
        self._fps = self._rendering.fps

        if self._rendering.fps_calculation_type == 'duration':

            self._fps = utility.round_to(
                float(self._imageCount)/float(self._rendering.run_length_seconds), 1)
            if self._fps > self._rendering.max_fps:
                self._fps = self._rendering.max_fps
            elif self._fps < self._rendering.min_fps:
                self._fps = self._rendering.min_fps
            message = (
                "FPS Calculation Type:{0}, Fps:{1}, NumFrames:{2}, "
                "DurationSeconds:{3}, Max FPS:{4}, Min FPS:{5}"
            ).format(
                self._rendering.fps_calculation_type,
                self._fps,
                self._imageCount,
                self._rendering.run_length_seconds,
                self._rendering.max_fps,
                self._rendering.min_fps
            )
            self._debug.LogRenderStart(message)
        else:
            message = "FPS Calculation Type:{0}, Fps:{0}"
            message = message.format(self._rendering.fps_calculation_type, self._fps)
            self._debug.LogRenderStart(message)

    def _countImages(self):
        """get the number of frames"""

        # we need to start with index 0, apparently.  Before I thought it was 1!
        imageIndex = 0
        while(True):
            foundFile = False
            imagePath = "{0}{1}".format(
                self._capture_dir, self._capture_file_template) % imageIndex

            if os.path.isfile(imagePath):
                imageIndex += 1
            else:
                break
        # since we're starting at 0 and incrementing after a file is found, the index here will be our count.
        self._debug.LogRenderStart("Found {0} images.".format(imageIndex))
        self._imageCount = imageIndex

    def _applyPrePostRoll(self, snapshotDirectory, snapshotFileNameTemplate, fps, imageCount):
        try:
            # start with pre-roll, since it will require a bunch of renaming
            preRollFrames = int(self._rendering.pre_roll_seconds * fps)
            if preRollFrames > 0:

                # create a variable to hold the new path of the first image
                firstImagePath = ""
                # rename all of the current files. The snapshot number should be
                # incremented by the number of pre-roll frames. Start with the last
                # image and work backwards to avoid overwriting files we've already moved
                for imageNumber in range(imageCount-1, -1, -1):
                    currentImagePath = "{0}{1}".format(
                        snapshotDirectory, snapshotFileNameTemplate) % imageNumber
                    newImagePath = "{0}{1}".format(
                        snapshotDirectory, snapshotFileNameTemplate) % (imageNumber+preRollFrames)
                    if imageNumber == 0:
                        firstImagePath = newImagePath
                    shutil.move(currentImagePath, newImagePath)
                # get the path of the first image
                # copy the first frame as many times as we need
                for imageIndex in range(preRollFrames):
                    # imageNumber = imageIndex + 1  I don't think we need this, because we're starting with 0
                    newImagePath = "{0}{1}".format(
                        snapshotDirectory, snapshotFileNameTemplate) % (imageIndex)
                    shutil.copy(firstImagePath, newImagePath)
            # finish with post roll since it's pretty easy
            postRollFrames = int(self._rendering.post_roll_seconds * fps)
            if postRollFrames > 0:
                lastFrameIndex = imageCount + preRollFrames - 1
                lastImagePath = "{0}{1}".format(
                    snapshotDirectory, snapshotFileNameTemplate) % (lastFrameIndex)
                for imageIndex in range(postRollFrames):
                    imageNumber = (imageIndex) + imageCount + preRollFrames
                    newImagePath = "{0}{1}".format(
                        snapshotDirectory, snapshotFileNameTemplate) % (imageNumber)
                    shutil.copy(lastImagePath, newImagePath)
            return True
        except Exception as e:
            self._debug.LogException(e)
        return False
    #####################
    # Event Notification
    #####################

    def _createCallbackPayload(self, returnCode, reason):
        return RenderingCallbackArgs(
            reason=reason,
            returnCode=returnCode,
            snapshotDirectory=self._capture_dir,
            renderingFullPath=self._output,
            renderingFileName=self._baseOutputFileName,
            synchronize=self._synchronize,
            snapshotCount=self._imageCount,
            secondsAddedToPrint=self._secondsAddedToPrint
        )

    def _on_render_start(self):
        payload = self._createCallbackPayload(0, "The rendering has started.")
        self._notify_callback(self._render_start_callback, payload)

    def _on_render_fail(self, returnCode, message):
        # we've failed, inform the client
        payload = self._createCallbackPayload(0, message)
        self._notify_callback(self._render_fail_callback, payload)
        # Time to end the rendering, inform the client.
        self._on_complete(False)

    def _on_render_success(self):
        payload = self._createCallbackPayload(
            0, "The rendering was successful.")
        self._notify_callback(self._render_success_callback, payload)

    def _on_render_complete(self):
        payload = self._createCallbackPayload(
            0, "The rendering process has completed.")
        self._notify_callback(self._render_complete_callback, payload)

    def _on_after_sync_success(self):
        payload = self._createCallbackPayload(
            0, "Synchronization was successful.")
        self._notify_callback(self._after_sync_success_callback, payload)

    def _on_after_sync_fail(self):
        payload = self._createCallbackPayload(0, "Synchronization has failed.")
        self._notify_callback(self._after_sync_fail_callback, payload)

    def _on_complete(self, success):
        payload = self._createCallbackPayload(0, "Synchronization has failed.")
        self._notify_callback(self._on_complete_callback,  payload, success)

    def _render(self):
        """Rendering runnable."""
        success = False

        try:
            # I've had bad luck doing this inside of the thread
            if not self._pre_render():
                if self._imageCount == 0:
                    self._on_render_fail(0, "No frames were captured.")
                elif self._imageCount == 1:
                    self._on_render_fail(
                        0, "Only 1 frame was captured.  Cannot render a timelapse from a single image.")
                else:
                    message = (
                        "Rendering failed during the pre-render phase. "
                        "Please check the logs (plugin_octolapse.log) for details."
                    )
                    self._on_render_fail(-1, message)
                return

            # notify any listeners that we are rendering.
            self._on_render_start()

            if self._ffmpeg is None:
                message = (
                    "Cannot create movie, path to ffmpeg is unset. "
                    "Please configure the ffmpeg path within the "
                    "'Features->Webcam & Timelapse' settings tab."
                )
                self._debug.LogRenderFail(message)
                self._on_render_fail(0, message)
                return
            elif self._rendering.bitrate is None:
                message = (
                    "Cannot create movie, desired bitrate is unset. "
                    "Please set the bitrate within the Octolapse rendering profile."
                )
                self._debug.LogRenderFail(message)
                self._on_render_fail(0, message)
                return

            # add the file extension
            self._output = self._output + "." + self._rendering.output_format
            try:
                self._debug.LogRenderStart(
                    "Creating the directory at {0}".format(self._output_dir))
                if not os.path.exists(self._output_dir:
                    os.makedirs(self._output_dir)
            except Exception as e:
                self._debug.LogException(e)
                message = (
                    "Render - An exception was thrown when trying to "
                    "create the rendering path at: {0}.  Please check "
                    "the logs (plugin_octolapse.log) for details."
                ).format(self._output_dir)
                self._on_render_fail(-1, message)
                return

            if not os.path.exists(self._input % 0:
                message = 'Cannot create a movie, no frames captured.'
                self._debug.LogRenderFail(message)
                self._on_render_fail(0, message)
                return

            watermark = None
            if self._rendering.watermark:
                watermark = os.path.join(os.path.dirname(
                    __file__), "static", "img", "watermark.png")
                if sys.platform == "win32":
                    # Because ffmpeg hiccups on windows' drive letters and backslashes we have to give the watermark
                    # path a special treatment. Yeah, I couldn't believe it either...
                    watermark = watermark.replace(
                        "\\", "/").replace(":", "\\\\:")

            # prepare ffmpeg command
            command_str = self._create_ffmpeg_command_string(
                self._ffmpeg,
                self._fps,
                self._rendering.bitrate,
                self._threads,
                self._input,
                self._output,
                self._rendering.output_format,
                hflip=self._rendering.flip_h,
                vflip=self._rendering.flip_v,
                rotate=self._rendering.rotate_90,
                watermark=watermark
            )
            self._debug.LogRenderStart(
                "Running ffmpeg with command string: {0}".format(command_str))

            with self.render_job_lock:
                try:
                    p = sarge.run(
                        command_str, stdout=sarge.Capture(), stderr=sarge.Capture())
                    if p.returncode == 0:
                        self._on_render_success()
                        success = True
                    else:
                        returncode = p.returncode
                        stdout_text = p.stdout.text
                        stderr_text = p.stderr.text
                        message = "Could not render movie, got return code %r: %s" % (
                            returncode, stderr_text)
                        self._debug.LogRenderFail(message)
                        self._on_render_fail(p.returncode, message)
                        return
                except Exception as e:
                    self._debug.LogException(e)
                    message = (
                        "Could not render movie due to unknown error. "
                        "Please check plugin_octolapse.log for details."
                    )
                    self._on_render_fail(-1, message)
                    return

                self._on_render_complete()
                cleanSnapshots = (
                    success and self.cleanAfterSuccess) or self.cleanAfterFail
                if cleanSnapshots:
                    self._CleanSnapshots()

                finalFileName = self._baseOutputFileName
                if self._synchronize:
                    finalFileName = "{0}{1}{2}".format(
                        self._octoprintTimelapseFolder, os.sep,
                        self._baseOutputFileName + "." + self._rendering.output_format
                    )
                    # Move the timelapse to the Octoprint timelapse folder.
                    try:
                        # get the timelapse folder for the Octoprint timelapse plugin
                        message = (
                            "Syncronizing timelapse with the built in "
                            "timelapse plugin, copying {0} to {1}"
                        ).format(self._output, finalFileName)
                        self._debug.LogRenderSync()
                        shutil.move(self._output, finalFileName)
                        # we've renamed the output due to a sync, update the member
                        self._output = finalFileName
                        self._on_after_sync_success()
                    except Exception, e:
                        self._debug.LogException(e)
                        self._on_after_sync_fail()
                        return

        except Exception as e:
            self._debug.LogException(e)
            message = (
                "An unexpected exception occurred while "
                "rendering a timelapse.  Please check "
                "plugin_octolapse.log for details."
            )
            self._on_render_fail(-1, message)
            return
        self._on_complete(True)

    def _CleanSnapshots(self):

        # get snapshot directory
        self._debug.LogSnapshotClean(
            "Cleaning snapshots from: {0}".format(self._capture_dir))

        path = os.path.dirname(self._capture_dir + os.sep)
        if os.path.isdir(path):
            try:
                shutil.rmtree(path)
                self._debug.LogSnapshotClean("Snapshots cleaned.")
            except Exception as e:
                self._debug.LogException(e)
        else:
            self._debug.LogSnapshotClean(
                "Snapshot - No need to clean snapshots: they have already been removed.")

    @classmethod
    def _create_ffmpeg_command_string(
            cls, ffmpeg, fps, bitrate, threads,
            input, output, outputFormat='vob',
            hflip=False, vflip=False,
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

        # See unit tests in test/timelapse/test_timelapse_renderjob.py

        logger = logging.getLogger(__name__)
        ffmpeg = ffmpeg.strip()

        if sys.platform == "win32" and not (ffmpeg.startswith('"') and ffmpeg.endswith('"'):
            ffmpeg = "\"{0}\"".format(ffmpeg)
        command = [
            ffmpeg, '-framerate', str(fps), '-loglevel', 'error', '-i', '"{}"'.format(
                input), '-vcodec', 'mpeg2video',
            '-threads', str(threads), '-r', "25", '-y', '-b', str(bitrate),
            '-f', str(outputFormat)]

        filter_string = cls._create_filter_string(hflip=hflip,
                                                  vflip=vflip,
                                                  rotate=rotate,
                                                  watermark=watermark)

        if filter_string is not None:
            logger.debug(
                "Applying videofilter chain: {}".format(filter_string))
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

        # See unit tests in test/timelapse/test_timelapse_renderjob.py

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
            watermark_filter = "movie={} [wm]; [{{input_name}}][wm] overlay=10:main_h-overlay_h-10".format(
                watermark)

        filter_string = None
        if len(filters) > 0:
            if watermark_filter is not None:
                filter_string = "[in] {} [postprocessed]; {} [out]".format(
                    ",".join(filters), watermark_filter.format(input_name="postprocessed")
                )
            else:
                filter_string = "[in] {} [out]".format(",".join(filters))
        elif watermark_filter is not None:
            filter_string = watermark_filter.format(input_name="in") + " [out]"

        return filter_string

    def _notify_callback(self, callback, *args, **kwargs):
        """Notifies registered callbacks of type `callback`."""
        if callback is not None and callable(callback:
            callback(*args, **kwargs)


class RenderingCallbackArgs(object):
    def __init__(
            self, snapshotDirectory="", renderingFullPath="",
            renderingFileName="", returnCode=0, reason="",
            synchronize=False, snapshotCount=0, secondsAddedToPrint=0):
        self.SnapshotDirectory = snapshotDirectory
        self.RenderingFullPath = renderingFullPath
        self.RenderingFileName = renderingFileName
        self.ReturnCode = returnCode
        self.Reason = reason
        self.Synchronize = synchronize
        self.SnapshotCount = snapshotCount
        self.SecondsAddedToPrint = secondsAddedToPrint

