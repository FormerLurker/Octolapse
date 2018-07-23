# coding=utf-8
##################################################################################
# Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
# Copyright (C) 2017  Brad Hochgesang
##################################################################################
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see the following:
# https://github.com/FormerLurker/Octolapse/blob/master/LICENSE
#
# You can contact the author either through the git-hub repository, or at the
# following email address: FormerLurker@pm.me
##################################################################################

import itertools
import logging
import math
import os
import shutil
import sys
import threading
import time
# sarge was added to the additional requirements for the plugin
import uuid
from datetime import datetime, timedelta
from tempfile import mkdtemp

import sarge
from PIL import Image, ImageDraw, ImageFont

import octoprint_octolapse.utility as utility
from octoprint_octolapse.settings import Rendering


def is_rendering_template_valid(template, options):
    # make sure we have all the replacements we need
    option_dict = {}
    for option in options:
        option_dict[option] = "F"  # use any valid file character, F seems ok
    try:
        filename = template.format(**option_dict)
    except KeyError as e:
        return False, "The following token is invalid: {{{0}}}".format(e.args[0])
    except ValueError:
        return False, "A value error occurred when replacing the provided tokens."

    temp_directory = mkdtemp()
    file_path = "{0}{1}.{2}".format(temp_directory, filename, "mp4")
    # see if the filename is valid
    if not os.access(file_path, os.W_OK):
        try:
            open(file_path, 'w').close()
            os.unlink(file_path)
        except (IOError, OSError):
            return False, "The resulting filename is not a valid filename.  Most likely an invalid character was used."

    shutil.rmtree(temp_directory)

    return True, ""


def is_overlay_text_template_valid(template, options):
    # make sure we have all the replacements we need
    option_dict = {}
    for option in options:
        option_dict[option] = "F"  # use any valid file character, F seems ok
    try:
        template.format(**option_dict)
    except KeyError as e:
        return False, "The following token is invalid: {{{0}}}".format(e.args[0])
    except ValueError:
        return False, "A value error occurred when replacing the provided tokens."

    return True, ""

class Render(object):
    @staticmethod
    def create_render_job(
        settings,
        snapshot,
        rendering,
        data_directory,
        octoprint_timelapse_folder,
        ffmpeg_path,
        thread_count,
        job_id,
        print_name,
        print_start_time,
        print_end_time,
        print_state,
        time_added,
        on_render_start,
        on_complete
    ):
        # Get the capture file and directory info
        snapshot_directory = utility.get_snapshot_temp_directory(data_directory)
        snapshot_file_name_template = utility.get_snapshot_filename(
            print_name, print_start_time, utility.SnapshotNumberFormat)
        output_tokens = Render._get_output_tokens(data_directory, print_state, print_name, print_start_time,
                                                  print_end_time)

        job = TimelapseRenderJob(
            job_id,
            rendering,
            settings.current_debug_profile(),
            print_name,
            snapshot_directory,
            snapshot_file_name_template,
            output_tokens,
            octoprint_timelapse_folder,
            ffmpeg_path,
            thread_count,
            time_added,
            on_render_start,
            on_complete,
            snapshot.cleanup_after_render_complete,
            snapshot.cleanup_after_render_complete
        )
        return job.process

    @staticmethod
    def _get_output_tokens(data_directory, print_state, print_name, print_start_time, print_end_time):
        return {
            "FAILEDFLAG": "FAILED" if print_state != "COMPLETED" else "",
            "FAILEDSEPARATOR": "_" if print_state != "COMPLETED" else "",
            "FAILEDSTATE": "" if print_state == "COMPLETED" else print_state,
            "PRINTSTATE": print_state,
            "GCODEFILENAME": print_name,
            "PRINTENDTIME": time.strftime("%Y%m%d%H%M%S", time.localtime(print_end_time)),
            "PRINTENDTIMESTAMP": "{0:d}".format(math.trunc(round(print_end_time, 2) * 100)),
            "PRINTSTARTTIME": time.strftime("%Y%m%d%H%M%S", time.localtime(print_start_time)),
            "PRINTSTARTTIMESTAMP": "{0:d}".format(math.trunc(round(print_start_time, 2) * 100)),
            "DATETIMESTAMP": "{0:d}".format(math.trunc(round(time.time(), 2) * 100)),
            "DATADIRECTORY": data_directory,
            "SNAPSHOTCOUNT": 0,
            "FPS": 0,
        }


class TimelapseRenderJob(object):
    render_job_lock = threading.RLock()

    # , capture_glob="{prefix}*.jpg", capture_format="{prefix}%d.jpg", output_format="{prefix}{postfix}.mpg",

    def __init__(
        self,
        job_id,
        rendering,
        debug,
        print_filename,
        capture_dir,
        capture_template,
        output_tokens,
        octoprint_timelapse_folder,
        ffmpeg_path,
        threads,
        time_added,
        on_render_start,
        on_complete,
        clean_after_success,
        clean_after_fail
    ):
        self._rendering = Rendering(rendering)
        self._debug = debug
        self._printFileName = print_filename
        self._capture_dir = capture_dir
        self._capture_file_template = capture_template
        self._output_tokens = output_tokens
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
        self._on_complete_callback = on_complete

        self._thread = None
        self.cleanAfterSuccess = clean_after_success
        self.cleanAfterFail = clean_after_fail
        self._synchronize = False
        # full path of the input
        self._input = ""
        self._output_directory = ""
        self._output_filename = ""
        self._output_extension = ""
        self._rendering_output_file_path = ""
        self._synchronized_directory = ""
        self._synchronized_filename = ""
        self._job_id = job_id
        self.error_type = ""
        self.has_error = ""
        self.error_message = ""

    def process(self):
        """Processes the job."""
        # do our file operations first, this seems to crash rendering if we do it inside the thread.  Of course.
        self._input = os.path.join(self._capture_dir,
                                   self._capture_file_template)

        self._synchronize = self._rendering.sync_with_timelapse
        self._thread = threading.Thread(target=self._render,
                                        name=self._job_id)
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

            # set the outputs - output directory, output filename, output extension
            self._set_outputs()

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
        # Add the FPS to the output tokens
        self._output_tokens["FPS"] = "{0}".format(int(math.ceil(self._fps)))

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
        # add the snapshot count to the output tokens
        self._output_tokens["SNAPSHOTCOUNT"] = "{0}".format(self._imageCount)

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

    def _set_outputs(self):
        self._output_directory = "{0}{1}{2}{3}".format(
            self._output_tokens["DATADIRECTORY"], os.sep, "timelapse", os.sep
        )
        try:
            self._output_filename = self._rendering.output_template.format(**self._output_tokens)
        except ValueError as e:
            self._debug.log_exception(e)
            self._output_filename = "RenderingFilenameTemplateError"
        self._output_extension = self._get_extension_from_output_format(self._rendering.output_format)

        # check for a rendered timelapse file collision
        original_output_filename = self._output_filename
        file_number = 0
        while os.path.isfile(
            "{0}{1}.{2}".format(
                self._output_directory,
                self._output_filename,
                self._output_extension)
        ):
            file_number += 1
            self._output_filename = "{0}_{1}".format(original_output_filename, file_number)

        self._rendering_output_file_path = "{0}{1}.{2}".format(
            self._output_directory, self._output_filename, self._output_extension
        )

        synchronized_output_filename = original_output_filename
        # check for a synchronized timelapse file collision
        file_number = 0
        while os.path.isfile("{0}{1}{2}.{3}".format(
            self._octoprintTimelapseFolder,
            os.sep,
            synchronized_output_filename,
            self._output_extension
        )):
            file_number += 1
            synchronized_output_filename = "{0}_{1}".format(original_output_filename, file_number)

        self._synchronized_directory = "{0}{1}".format(self._octoprintTimelapseFolder, os.sep)
        self._synchronized_filename = synchronized_output_filename

    #####################
    # Event Notification
    #####################

    def _create_callback_payload(self, return_code, reason):
        return RenderingCallbackArgs(
            reason,
            return_code,
            self._capture_dir,
            self._output_directory,
            self._output_filename,
            self._output_extension,
            self._synchronized_directory,
            self._synchronized_filename,
            self._synchronize,
            self._imageCount,
            self._secondsAddedToPrint,
            self.has_error,
            self.error_type,
            self.error_message
        )

    def _on_start(self):
        payload = self._create_callback_payload(0, "The rendering has started.")
        self._render_start_callback(self._job_id, payload)

    def _on_complete(self):
        payload = self._create_callback_payload(0, "Timelapse rendering is complete.")
        self._on_complete_callback(self._job_id, payload)

    def _render(self):
        """Rendering runnable."""
        self.has_error = False

        self.error_message = ""
        self.error_type = ""
        try:
            # I've had bad luck doing this inside of the thread
            if not self._pre_render():
                if self._imageCount == 0:
                    self.error_message = "No frames were captured."
                    self.error_type = "no_frames_captured"
                    self.has_error = True
                elif self._imageCount == 1:
                    self.error_message = "Only 1 frame was captured.  Cannot render a timelapse from a single image."
                    self.error_type = "one_frame_captured"
                    self.has_error = True
                else:
                    self.error_message = (
                        "Rendering failed during the pre-render phase. "
                        "Please check the logs (plugin_octolapse.log) for details."
                    )
                    self.error_type = "pre_render"
                    self.has_error = True

            if not self.has_error:

                # notify any listeners that we are rendering.
                self._on_start()

                if self._ffmpeg is None:
                    self.error_message = (
                        "Cannot create movie, path to ffmpeg is unset. "
                        "Please configure the ffmpeg path within the "
                        "'Features->Webcam & Timelapse' settings tab."
                    )
                    self.error_type = "ffmpeg_path"
                    self.has_error = True

            if not self.has_error:
                if self._rendering.bitrate is None:
                    self.error_message = (
                        "Cannot create movie, desired bitrate is unset. "
                        "Please set the bitrate within the Octolapse rendering profile."
                    )
                    self.error_type = "no-bitrate"
                    self.has_error = True

            if not self.has_error:
                try:
                    self._debug.log_render_start(
                        "Creating the directory at {0}".format(self._output_directory))
                    if not os.path.exists(self._output_directory):
                        os.makedirs(self._output_directory)
                except Exception as e:
                    self._debug.log_exception(e)
                    self.error_message = (
                        "Render - An exception was thrown when trying to "
                        "create the rendering path at: {0}.  Please check "
                        "the logs (plugin_octolapse.log) for details."
                    ).format(self._output_directory)
                    self.error_type = "create-render-path"
                    self.has_error = True

            if not self.has_error:
                if not os.path.exists(self._input % 0):
                    self.error_message = 'Cannot create a movie, no frames captured.'
                    self.error_type = "no_frames_captured"
                    self.has_error = True

            if not self.has_error:
                watermark_path = None
                if self._rendering.enable_watermark:
                    watermark_path = self._rendering.selected_watermark
                    if watermark_path == '':
                        self.error_message = "Render - Watermark was enabled but no watermark file was selected."
                        self.error_type = "watermark-path"
                        self.has_error = True
                    if not os.path.exists(watermark_path):
                        self.error_message = "Render - Watermark file does not exist."
                        self.error_type = "watermark-non-existent"
                        self.has_error = True

                    if sys.platform == "win32":
                        # Because ffmpeg hiccups on windows' drive letters and backslashes we have to give the watermark
                        # path a special treatment. Yeah, I couldn't believe it either...
                        watermark_path = watermark_path.replace(
                            "\\", "/").replace(":", "\\\\:")

            # Make a temporary directory to store preprocessed images.
            preprocessed_images_dir = mkdtemp()
            preprocessed_filepath_template = os.path.join(preprocessed_images_dir, self._capture_file_template)
            dir = os.path.dirname(preprocessed_filepath_template)
            if not os.path.exists(dir):
                os.makedirs(dir)
            if not self.has_error:
                self._debug.log_render_start("Starting Pillow preprocessing.")
                # Do Pillow preprocessing.
                self._preprocess_images(preprocessed_filepath_template)

            if not self.has_error:
                vcodec = self._get_vcodec_from_output_format(self._rendering.output_format)

                # prepare ffmpeg command
                command_str = self._create_ffmpeg_command_string(
                    self._ffmpeg,
                    self._fps,
                    self._rendering.bitrate,
                    self._threads,
                    preprocessed_filepath_template,
                    self._rendering_output_file_path,
                    self._rendering.output_format,
                    watermark=watermark_path,
                    v_codec=vcodec
                )
                self._debug.log_render_start(
                    "Running ffmpeg with command string: {0}".format(command_str))

                with self.render_job_lock:
                    try:
                        p = sarge.run(
                            command_str, stdout=sarge.Capture(), stderr=sarge.Capture())
                        if p.returncode != 0:
                            return_code = p.returncode
                            stderr_text = p.stderr.text
                            self.error_message = "Could not render movie, got return code %r: %s" % (
                                return_code, stderr_text)
                            self.error_type = "return-code"
                            self.has_error = True
                    except Exception as e:
                        self._debug.log_exception(e)
                        self.error_message = (
                            "Could not render movie due to unknown error. "
                            "Please check plugin_octolapse.log for details."
                        )
                        self.error_type = "rendering-exception"
                        self.has_error = True

            if (not self.has_error and self.cleanAfterSuccess) or (self.has_error and self.cleanAfterFail):
                # Delete preprocessed images.
                shutil.rmtree(preprocessed_images_dir)

            if not self.has_error:
                if self._synchronize:

                    # Move the timelapse to the Octoprint timelapse folder.
                    try:
                        # get the timelapse folder for the Octoprint timelapse plugin
                        synchronization_path = "{0}{1}.{2}".format(
                            self._synchronized_directory, self._synchronized_filename, self._output_extension
                        )
                        message = (
                            "Synchronizing timelapse with the built in "
                            "timelapse plugin, copying {0} to {1}"
                        ).format(self._rendering_output_file_path, synchronization_path)
                        self._debug.log_render_sync(message)
                        shutil.move(self._rendering_output_file_path, synchronization_path)
                        # we've renamed the output due to a sync, update the member
                    except Exception, e:
                        self._debug.log_exception(e)

                        self.error_message = "Octolapse has failed to synchronize the default timelapse plugin due" \
                                             " to an unexpected exception.  Check plugin_octolapse.log for more " \
                                             " information.  You should be able to find your video within your " \
                                             " OctoPrint  server here:<br/> '{0}'" \
                            .format(self._rendering_output_file_path)

                        self.has_error = True
                        self.error_type = "synchronizing-exception"
        except Exception as e:
            self._debug.log_exception(e)
            self.error_message = (
                "An unexpected exception occurred while "
                "rendering a timelapse.  Please check "
                "plugin_octolapse.log for details."
            )
            self.has_error = True
            self.error_type = "unexpected-exception"

        self._on_complete()

    def _preprocess_images(self, processed_filepath):
        first_timestamp = None
        for i in itertools.count():
            input_path = "{0}{1}".format(self._capture_dir, self._capture_file_template) % i
            if not os.path.isfile(input_path):
                break
            # Get file creation time, or failing that, last file modification time.
            timestamp = os.path.getctime(input_path) or os.path.getmtime(input_path)
            if first_timestamp is None:
                first_timestamp = timestamp
            current_time = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            time_elapsed = str(timedelta(seconds=round(timestamp - first_timestamp)))

            image = Image.open(input_path)
            # Draw overlay text.
            if self._rendering.overlay_text_template:
                font = ImageFont.load_default()
                d = ImageDraw.Draw(image)
                text = self._rendering.overlay_text_template.format(current_time=current_time, time_elapsed=time_elapsed)
                d.text((10, 10), text=text, font=font, fill=(255, 255, 255, 128))

            # Save processed image.
            image.save(processed_filepath % i)


    @staticmethod
    def _get_extension_from_output_format(output_format):
        EXTENSIONS = {"avi": "avi",
                      "flv": "flv",
                      "h264": "mp4",
                      "vob": "vob",
                      "mp4": "mp4",
                      "mpeg": "mpeg",
                      "gif": "gif"}
        return EXTENSIONS.get(output_format.lower(), "mp4")

    @staticmethod
    def _get_vcodec_from_output_format(output_format):
        VCODECS = {"avi": "mpeg4",
                   "flv": "flv1",
                   "gif": "gif",
                   "h264": "h264",
                   "mp4": "mpeg4",
                   "mpeg": "mpeg2video",
                   "vob": "mpeg2video"}
        return VCODECS.get(output_format.lower(), "mpeg2video")

    @classmethod
    def _create_ffmpeg_command_string(
        cls, ffmpeg, fps, bitrate, threads,
        input_file, output_file, output_format='vob', watermark=None, pix_fmt="yuv420p",
        v_codec="mpeg2video"
    ):
        """
        Create ffmpeg command string based on input parameters.
        Arguments:
            ffmpeg (str): Path to ffmpeg
            fps (int): Frames per second for output
            bitrate (str): Bitrate of output
            threads (int): Number of threads to use for rendering
            input_file (str): Absolute path to input files including file mask
            output_file (str): Absolute path to output file
            watermark (str): Path to watermark to apply to lower left corner.
            pix_fmt (str): Pixel format to use for output. Default of yuv420p should usually fit the bill.
            v_codec (str): The video codec to use when encoding the video.
        Returns:
            (str): Prepared command string to render `input` to `output` using ffmpeg.
        """

        logger = logging.getLogger(__name__)
        ffmpeg = ffmpeg.strip()

        if sys.platform == "win32" and not (ffmpeg.startswith('"') and ffmpeg.endswith('"')):
            ffmpeg = "\"{0}\"".format(ffmpeg)
        command = [ffmpeg, '-framerate', str(fps), '-loglevel', 'error', '-i', '"{}"'.format(input_file)]
        command.extend(['-threads', str(threads), '-r', "25", '-y', '-b', str(bitrate), '-vcodec', v_codec])

        filter_string = cls._create_filter_string(watermark=watermark, pix_fmt=pix_fmt)

        if filter_string is not None:
            logger.debug("Applying video filter chain: {}".format(filter_string))
            command.extend(["-vf", sarge.shell_quote(filter_string)])

        # finalize command with output file
        logger.debug("Rendering movie to {}".format(output_file))
        command.append('"{}"'.format(output_file))

        return " ".join(command)

    @classmethod
    def _create_filter_string(cls, watermark=None, pix_fmt="yuv420p"):
        """
        Creates an ffmpeg filter string based on input parameters.
        Arguments:
            watermark (str): Path to watermark to apply to lower left corner.
            pix_fmt (str): Pixel format to use, defaults to "yuv420p" which should usually fit the bill
        Returns:
            (str): filter string
        """

        filters = []

        # apply pixel format
        filters.append('[{{prev_filter}}] format={} [{{next_filter}}]'.format(pix_fmt))

        # add watermark if configured
        if watermark is not None:
            filters.append(
                'movie={} [wm]; [{{prev_filter}}][wm] overlay=10:main_h-overlay_h-10 [{{next_filter}}]'.format(
                    watermark))

        # Apply string format to each filter to chain them together.
        filter_names = ['f' + str(x) for x in range(len(filters))] + ['out']
        for i, previous_filter_name, next_filter_name in zip(range(len(filters)), filter_names, filter_names[1:]):
            filters[i] = filters[i].format(prev_filter=previous_filter_name, next_filter=next_filter_name)
        # Build the final filter string.
        filter_string = "; ".join(filters)

        return filter_string

    @staticmethod
    def _notify_callback(callback, *args, **kwargs):
        """Notifies registered callbacks of type `callback`."""
        if callback is not None and callable(callback):
            callback(*args, **kwargs)


class RenderingCallbackArgs(object):
    def __init__(
        self,
        reason,
        return_code,
        snapshot_directory,
        rendering_directory,
        rendering_filename,
        rendering_extension,
        synchronized_directory,
        synchronized_filename,
        synchronize,
        snapshot_count,
        seconds_added_to_print,
        has_error,
        error_type,
        error_message
    ):
        self.Reason = reason
        self.ReturnCode = return_code
        self.SnapshotDirectory = snapshot_directory
        self.RenderingDirectory = rendering_directory
        self.RenderingFilename = rendering_filename
        self.RenderingExtension = rendering_extension
        self.SynchronizedDirectory = synchronized_directory
        self.SynchronizedFilename = synchronized_filename
        self.Synchronize = synchronize
        self.SnapshotCount = snapshot_count
        self.SecondsAddedToPrint = seconds_added_to_print
        self.HasError = has_error
        self.ErrorType = error_type
        self.ErrorMessage = error_message

    def get_rendering_filename(self):
        return "{0}.{1}".format(self.RenderingFilename, self.RenderingExtension)

    def get_synchronization_filename(self):
        return "{0}.{1}".format(self.SynchronizedFilename, self.RenderingExtension)

    def get_rendering_path(self):
        return "{0}{1}".format(self.RenderingDirectory, self.get_rendering_filename())

    def get_synchronization_path(self):
        return "{0}{1}".format(self.SynchronizedDirectory, self.get_synchronization_filename())
