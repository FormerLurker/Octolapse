# coding=utf-8

# This file is subject to the terms and conditions defined in
# file called 'LICENSE', which is part of this source code package.


import logging
import os
import shutil
import sys
import threading
# sarge was added to the additional requirements for the plugin
import sarge

import octoprint_octolapse.utility as utility
from octoprint_octolapse.settings import Rendering


class Render(object):

    def __init__(
            self, settings, snapshot, rendering, data_directory,
            octoprint_timelapse_folder, ffmpeg_path, thread_count,
            time_added=0, on_render_start=None, on_render_fail=None,
            on_render_success=None, on_render_complete=None, on_after_sync_fail=None,
            on_after_sync_success=None, on_complete=None):
        self.Settings = settings
        self.DataDirectory = data_directory
        self.OctoprintTimelapseFolder = octoprint_timelapse_folder
        self.FfmpegPath = ffmpeg_path
        self.Snapshot = snapshot
        self.Rendering = rendering
        self.ThreadCount = thread_count
        self.TimeAdded = time_added
        self.OnRenderStart = on_render_start
        self.OnRenderFail = on_render_fail
        self.OnRenderSuccess = on_render_success
        self.OnRenderComplete = on_render_complete
        self.OnAfterSyncFail = on_after_sync_fail
        self.OnAfterSycnSuccess = on_after_sync_success
        self.OnComplete = on_complete
        self.TimelapseRenderJobs = []

    def process(self, print_name, print_start_time, print_end_time):
        self.Settings.current_debug_profile().log_render_start("Rendering is starting.")
        # Get the capture file and directory info
        snapshot_directory = utility.get_snapshot_temp_directory(
            self.DataDirectory)
        snapshot_file_name_template = utility.get_snapshot_filename(
            print_name, print_start_time, utility.SnapshotNumberFormat)
        # get the output file and directory info
        output_directory = utility.get_rendering_directory(
            self.DataDirectory, print_name, print_start_time, self.Rendering.output_format, print_end_time)

        output_filename = utility.get_rendering_base_filename(
            print_name, print_start_time, print_end_time)

        job = TimelapseRenderJob(
            self.Rendering,
            self.Settings.current_debug_profile(),
            print_name,
            snapshot_directory,
            snapshot_file_name_template,
            output_directory,
            output_filename,
            self.OctoprintTimelapseFolder,
            self.FfmpegPath,
            self.ThreadCount,
            time_added=self.TimeAdded,
            on_render_start=self.OnRenderStart,
            on_render_fail=self.OnRenderFail,
            on_render_success=self.OnRenderSuccess,
            on_render_complete=self.OnRenderComplete,
            on_after_sync_fail=self.OnAfterSyncFail,
            on_after_sync_success=self.OnAfterSycnSuccess,
            on_complete=self.OnComplete,
            clean_after_success=self.Snapshot.cleanup_after_render_complete,
            clean_after_fail=self.Snapshot.cleanup_after_render_complete
        )

        job.process()


class RenderInfo(object):
    def __init__(self):
        self.FileName = ""
        self.Directory = ""


class TimelapseRenderJob(object):
    render_job_lock = threading.RLock()

    # , capture_glob="{prefix}*.jpg", capture_format="{prefix}%d.jpg", output_format="{prefix}{postfix}.mpg",

    def __init__(
            self, rendering, debug, print_filename,
            capture_dir, capture_template, output_dir,
            output_name, octoprint_timelapse_folder,
            ffmpeg_path, threads, time_added=0,
            on_render_start=None, on_render_fail=None,
            on_render_success=None, on_render_complete=None,
            on_after_sync_success=None, on_after_sync_fail=None,
            on_complete=None, clean_after_success=False,
            clean_after_fail=False):
        self._rendering = Rendering(rendering)
        self._debug = debug
        self._printFileName = print_filename
        self._capture_dir = capture_dir
        self._capture_file_template = capture_template
        self._output_dir = output_dir
        self._output_file_name = output_name
        self._octoprintTimelapseFolder = octoprint_timelapse_folder
        self._fps = None
        self._imageCount = None
        self._secondsAddedToPrint = time_added
        self._threads = threads
        self._ffmpeg = ffmpeg_path

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
        self.cleanAfterSuccess = clean_after_success
        self.cleanAfterFail = clean_after_fail
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

        self._baseOutputFileName = utility.get_filename_from_full_path(
            self._output)
        self._synchronize = (
            self._rendering.sync_with_timelapse and self._rendering.output_format in ["mp4"])

        self._thread = threading.Thread(target=self._render,
                                        name="TimelapseRenderJob_{name}".format(name=self._printFileName))
        self._thread.daemon = True
        self._thread.start()

    def _pre_render(self):

        try:
            self._count_images()
            if self._imageCount == 0:
                self._debug.log_render_fail(
                    "No images were captured, or they have been removed.")
                return False
            if self._imageCount == 1:
                self._debug.log_render_fail(
                    "Only 1 frame was captured, cannot make a timelapse with a single frame.")
                return False
            # calculate the FPS
            self._calculate_fps()
            if self._fps < 1:
                self._debug.log_error(
                    "The calculated FPS is below 1, which is not allowed. "
                    "Please check the rendering settings for Min and Max FPS "
                    "as well as the number of snapshots captured."
                )
                return False
            # apply pre and post roll
            self._apply_pre_post_roll(
                self._capture_dir, self._capture_file_template, self._fps, self._imageCount)
            return True
        except Exception as e:
            self._debug.log_exception(e)
        return False

    def _calculate_fps(self):
        self._fps = self._rendering.fps

        if self._rendering.fps_calculation_type == 'duration':

            self._fps = utility.round_to(
                float(self._imageCount) / float(self._rendering.run_length_seconds), 1)
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
            self._debug.log_render_start(message)
        else:
            message = "FPS Calculation Type:{0}, Fps:{0}"
            message = message.format(self._rendering.fps_calculation_type, self._fps)
            self._debug.log_render_start(message)

    def _count_images(self):
        """get the number of frames"""

        # we need to start with index 0, apparently.  Before I thought it was 1!
        image_index = 0
        while True:
            image_path = "{0}{1}".format(
                self._capture_dir, self._capture_file_template) % image_index

            if os.path.isfile(image_path):
                image_index += 1
            else:
                break
        # since we're starting at 0 and incrementing after a file is found, the index here will be our count.
        self._debug.log_render_start("Found {0} images.".format(image_index))
        self._imageCount = image_index

    def _apply_pre_post_roll(self, snapshot_directory, snapshot_filename_template, fps, image_count):
        try:
            # start with pre-roll, since it will require a bunch of renaming
            pre_roll_frames = int(self._rendering.pre_roll_seconds * fps)
            if pre_roll_frames > 0:

                # create a variable to hold the new path of the first image
                first_image_path = ""
                # rename all of the current files. The snapshot number should be
                # incremented by the number of pre-roll frames. Start with the last
                # image and work backwards to avoid overwriting files we've already moved
                for image_number in range(image_count - 1, -1, -1):
                    current_image_path = "{0}{1}".format(
                        snapshot_directory, snapshot_filename_template) % image_number
                    new_image_path = "{0}{1}".format(
                        snapshot_directory, snapshot_filename_template) % (image_number + pre_roll_frames)
                    if image_number == 0:
                        first_image_path = new_image_path
                    shutil.move(current_image_path, new_image_path)
                # get the path of the first image
                # copy the first frame as many times as we need
                for image_index in range(pre_roll_frames):
                    # imageNumber = imageIndex + 1  I don't think we need this, because we're starting with 0
                    new_image_path = "{0}{1}".format(
                        snapshot_directory, snapshot_filename_template) % image_index
                    shutil.copy(first_image_path, new_image_path)
            # finish with post roll since it's pretty easy
            post_roll_frames = int(self._rendering.post_roll_seconds * fps)
            if post_roll_frames > 0:
                last_frame_index = image_count + pre_roll_frames - 1
                last_image_path = "{0}{1}".format(
                    snapshot_directory, snapshot_filename_template) % last_frame_index
                for image_index in range(post_roll_frames):
                    image_number = image_index + image_count + pre_roll_frames
                    new_image_path = "{0}{1}".format(
                        snapshot_directory, snapshot_filename_template) % image_number
                    shutil.copy(last_image_path, new_image_path)
            return True
        except Exception as e:
            self._debug.log_exception(e)
        return False

    #####################
    # Event Notification
    #####################

    def _create_callback_payload(self, return_code, reason):
        return RenderingCallbackArgs(
            reason=reason,
            return_code=return_code,
            snapshot_directory=self._capture_dir,
            rendering_full_path=self._output,
            rendering_filename=self._baseOutputFileName,
            synchronize=self._synchronize,
            snapshot_count=self._imageCount,
            seconds_added_to_print=self._secondsAddedToPrint
        )

    def _on_render_start(self):
        payload = self._create_callback_payload(0, "The rendering has started.")
        self._notify_callback(self._render_start_callback, payload)

    def _on_render_fail(self, return_code, message):
        # we've failed, inform the client
        payload = self._create_callback_payload(return_code, message)
        self._notify_callback(self._render_fail_callback, payload)
        # Time to end the rendering, inform the client.
        self._on_complete(False)

    def _on_render_success(self):
        payload = self._create_callback_payload(
            0, "The rendering was successful.")
        self._notify_callback(self._render_success_callback, payload)

    def _on_render_complete(self):
        payload = self._create_callback_payload(
            0, "The rendering process has completed.")
        self._notify_callback(self._render_complete_callback, payload)

    def _on_after_sync_success(self):
        payload = self._create_callback_payload(
            0, "Synchronization was successful.")
        self._notify_callback(self._after_sync_success_callback, payload)

    def _on_after_sync_fail(self):
        payload = self._create_callback_payload(0, "Synchronization has failed.")
        self._notify_callback(self._after_sync_fail_callback, payload)

    def _on_complete(self, success):
        payload = self._create_callback_payload(0, "Synchronization has failed.")
        self._notify_callback(self._on_complete_callback, payload, success)

    def _render(self):
        """Rendering runnable."""

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
                self._debug.log_render_fail(message)
                self._on_render_fail(0, message)
                return
            elif self._rendering.bitrate is None:
                message = (
                    "Cannot create movie, desired bitrate is unset. "
                    "Please set the bitrate within the Octolapse rendering profile."
                )
                self._debug.log_render_fail(message)
                self._on_render_fail(0, message)
                return

            # add the file extension
            self._output = self._output + "." + self._rendering.output_format
            try:
                self._debug.log_render_start(
                    "Creating the directory at {0}".format(self._output_dir))
                if not os.path.exists(self._output_dir):
                    os.makedirs(self._output_dir)
            except Exception as e:
                self._debug.log_exception(e)
                message = (
                    "Render - An exception was thrown when trying to "
                    "create the rendering path at: {0}.  Please check "
                    "the logs (plugin_octolapse.log) for details."
                ).format(self._output_dir)
                self._on_render_fail(-1, message)
                return

            if not os.path.exists(self._input % 0):
                message = 'Cannot create a movie, no frames captured.'
                self._debug.log_render_fail(message)
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

            vcodec = self._get_vcodec_from_extension(self._rendering.output_format)
            # prepare ffmpeg command
            command_str = self._create_ffmpeg_command_string(
                self._ffmpeg,
                self._fps,
                self._rendering.bitrate,
                self._threads,
                self._input,
                self._output,
                self._rendering.output_format,
                h_flip=self._rendering.flip_h,
                v_flip=self._rendering.flip_v,
                rotate=self._rendering.rotate_90,
                watermark=watermark,
                v_codec=vcodec
            )
            self._debug.log_render_start(
                "Running ffmpeg with command string: {0}".format(command_str))

            with self.render_job_lock:
                try:
                    p = sarge.run(
                        command_str, stdout=sarge.Capture(), stderr=sarge.Capture())
                    if p.returncode == 0:
                        self._on_render_success()
                    else:
                        return_code = p.returncode
                        stderr_text = p.stderr.text
                        message = "Could not render movie, got return code %r: %s" % (
                            return_code, stderr_text)
                        self._debug.log_render_fail(message)
                        self._on_render_fail(p.returncode, message)
                        return
                except Exception as e:
                    self._debug.log_exception(e)
                    message = (
                        "Could not render movie due to unknown error. "
                        "Please check plugin_octolapse.log for details."
                    )
                    self._on_render_fail(-1, message)
                    return

                self._on_render_complete()

                if self._synchronize:
                    final_filename = "{0}{1}{2}".format(
                        self._octoprintTimelapseFolder, os.sep,
                        self._baseOutputFileName + "." + self._rendering.output_format
                    )
                    # Move the timelapse to the Octoprint timelapse folder.
                    try:
                        # get the timelapse folder for the Octoprint timelapse plugin
                        message = (
                            "Syncronizing timelapse with the built in "
                            "timelapse plugin, copying {0} to {1}"
                        ).format(self._output, final_filename)
                        self._debug.log_render_sync(message)
                        shutil.move(self._output, final_filename)
                        # we've renamed the output due to a sync, update the member
                        self._output = final_filename
                        self._on_after_sync_success()
                    except Exception, e:
                        self._debug.log_exception(e)
                        self._on_after_sync_fail()
                        return

        except Exception as e:
            self._debug.log_exception(e)
            message = (
                "An unexpected exception occurred while "
                "rendering a timelapse.  Please check "
                "plugin_octolapse.log for details."
            )
            self._on_render_fail(-1, message)
            return
        self._on_complete(True)

    @staticmethod
    def _get_vcodec_from_extension(extension):
        default_codec = "mpeg2video"

        if extension in ["mpeg", "vob"]:
            return "mpeg2video"
        elif extension in ["mp4", "avi"]:
            return "mpeg4"
        elif extension == "flv":
            return "flv1"
        else:
            return default_codec

    @classmethod
    def _create_ffmpeg_command_string(
            cls, ffmpeg, fps, bitrate, threads,
            input_file, output_file, output_format='vob',
            h_flip=False, v_flip=False,
            rotate=False, watermark=None, pix_fmt="yuv420p",
            v_codec="mpeg2video"):
        """
        Create ffmpeg command string based on input parameters.
        Arguments:
            ffmpeg (str): Path to ffmpeg
            fps (int): Frames per second for output
            bitrate (str): Bitrate of output
            threads (int): Number of threads to use for rendering
            input_file (str): Absolute path to input files including file mask
            output_file (str): Absolute path to output file
            h_flip (bool): Perform horizontal flip on input material.
            v_flip (bool): Perform vertical flip on input material.
            rotate (bool): Perform 90° CCW rotation on input material.
            watermark (str): Path to watermark to apply to lower left corner.
            pix_fmt (str): Pixel format to use for output. Default of yuv420p should usually fit the bill.
        Returns:
            (str): Prepared command string to render `input` to `output` using ffmpeg.
        """

        # See unit tests in test/timelapse/test_timelapse_renderjob.py

        logger = logging.getLogger(__name__)
        ffmpeg = ffmpeg.strip()

        if sys.platform == "win32" and not (ffmpeg.startswith('"') and ffmpeg.endswith('"')):
            ffmpeg = "\"{0}\"".format(ffmpeg)
        command = [
            ffmpeg, '-framerate', str(fps), '-loglevel', 'error', '-i', '"{}"'.format(
                input_file), '-vcodec', v_codec,
            '-threads', str(threads), '-r', "25", '-y', '-b', str(bitrate),
            '-f', str(output_format)]

        filter_string = cls._create_filter_string(hflip=h_flip,
                                                  vflip=v_flip,
                                                  rotate=rotate,
                                                  watermark=watermark,
                                                  pix_fmt=pix_fmt)

        if filter_string is not None:
            logger.debug(
                "Applying video filter chain: {}".format(filter_string))
            command.extend(["-vf", sarge.shell_quote(filter_string)])

        # finalize command with output file
        logger.debug("Rendering movie to {}".format(output_file))
        command.append('"{}"'.format(output_file))

        return " ".join(command)

    @classmethod
    def _create_filter_string(cls, hflip=False, vflip=False, rotate=False, watermark=None, pix_fmt="yuv420p"):
        """
        Creates an ffmpeg filter string based on input parameters.
        Arguments:
            hflip (bool): Perform horizontal flip on input material.
            vflip (bool): Perform vertical flip on input material.
            rotate (bool): Perform 90° CCW rotation on input material.
            watermark (str): Path to watermark to apply to lower left corner.
            pix_fmt (str): Pixel format to use, defaults to "yuv420p" which should usually fit the bill
        Returns:
            (str or None): filter string or None if no filters are required
        """

        # See unit tests in test/timelapse/test_timelapse_renderjob.py

        # apply pixel format
        filters = ["format={}".format(pix_fmt)]

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

    @staticmethod
    def _notify_callback(callback, *args, **kwargs):
        """Notifies registered callbacks of type `callback`."""
        if callback is not None and callable(callback):
            callback(*args, **kwargs)


class RenderingCallbackArgs(object):
    def __init__(
            self, snapshot_directory="", rendering_full_path="",
            rendering_filename="", return_code=0, reason="",
            synchronize=False, snapshot_count=0, seconds_added_to_print=0):
        self.SnapshotDirectory = snapshot_directory
        self.RenderingFullPath = rendering_full_path
        self.RenderingFileName = rendering_filename
        self.ReturnCode = return_code
        self.Reason = reason
        self.Synchronize = synchronize
        self.SnapshotCount = snapshot_count
        self.SecondsAddedToPrint = seconds_added_to_print
