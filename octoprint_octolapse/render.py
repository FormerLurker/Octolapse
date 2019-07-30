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
from __future__ import unicode_literals
import math
import os
import shutil
import six
import sys
import threading
from six.moves import queue
from six import string_types
import time
import json
from csv import DictReader
# sarge was added to the additional requirements for the plugin
import datetime
from tempfile import mkdtemp

import sarge
from PIL import Image, ImageDraw, ImageFont

import octoprint_octolapse.utility as utility
from octoprint_octolapse.snapshot import SnapshotMetadata


# create the module level logger
from octoprint_octolapse.log import LoggingConfigurator
logging_configurator = LoggingConfigurator()
logger = logging_configurator.get_logger(__name__)


def is_rendering_template_valid(template, options):
    # make sure we have all the replacements we need
    option_dict = {}
    for option in options:
        option_dict[option] = "F"  # use any valid file character, F seems ok
    try:
        filename = template.format(**option_dict)
    except KeyError as e:
        return False, "The following token is invalid: {{{0}}}".format(e.args[0])
    except IndexError as e:
        return False, "Integers as tokens are not allowed."
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
    except IndexError as e:
        return False, "Integers as tokens are not allowed."
    except ValueError:
        return False, "A value error occurred when replacing the provided tokens."

    return True, ""


def preview_overlay(rendering_profile, image=None):
    if rendering_profile.overlay_font_path is None or len(rendering_profile.overlay_font_path.strip()) == 0:
        # we don't have any overlay path, return
        return None

    overlay_text_color = rendering_profile.get_overlay_text_color()
    overlay_outline_color = rendering_profile.get_overlay_outline_color()
    overlay_outline_width = rendering_profile.overlay_outline_width
    if image is None:
        image_color = (0,0,0,255)
        if isinstance(overlay_text_color, list):
            image_color = tuple(255 - c for c in overlay_text_color)
        # Create an image with background color inverse to the text color.
        image = Image.new('RGB', (640, 480), color=image_color)

    try:
        font = ImageFont.truetype(rendering_profile.overlay_font_path, size=50)
    except IOError as e:
        logger.exception("An error occurred while opening the selected font")
        raise e

    def draw_center(i, t, overlay_text_color, dx=0, dy=0):
        """Draws the text centered in the image, offsets by (dx, dy)."""
        text_image = Image.new('RGBA', i.size, (255, 255, 255, 0))
        d = ImageDraw.Draw(text_image)
        iw, ih = i.size
        tw, th = d.textsize(t, font=font)

        d.text(xy=(iw / 2 - tw / 2 + dx, ih / 2 - th / 2 + dy), text=t,
               fill=tuple(overlay_text_color), font=font)
        return Image.alpha_composite(i.convert('RGBA'), text_image).convert('RGB')

    # copy the overlay text color list
    image_text_color = list(overlay_text_color)
    # set image text color to opaque
    image_text_color[3] = 255
    image = draw_center(image, "Preview", image_text_color, dy=-20)
    image = draw_center(image, "Click to refresh", image_text_color, dy=20)

    format_vars = {'snapshot_number': 1234,
                   'file_name': 'image.jpg',
                   'time_taken': time.time(),
                   'current_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),
                   'time_elapsed': "{}".format(datetime.timedelta(seconds=round(9001)))}
    image = TimelapseRenderJob.add_overlay(image,
                                           text_template=rendering_profile.overlay_text_template,
                                           format_vars=format_vars,
                                           font_path=rendering_profile.overlay_font_path,
                                           font_size=rendering_profile.overlay_font_size,
                                           overlay_location=rendering_profile.overlay_text_pos,
                                           overlay_text_alignment=rendering_profile.overlay_text_alignment,
                                           overlay_text_valign=rendering_profile.overlay_text_valign,
                                           overlay_text_halign=rendering_profile.overlay_text_halign,
                                           text_color=overlay_text_color,
                                           outline_color=overlay_outline_color,
                                           outline_width=overlay_outline_width)
    return image


class RenderJobInfo(object):
    def __init__(
        self, timelapse_job_info, data_directory, current_camera, rendering, ffmpeg_path, job_number=0, jobs_remaining=0
    ):
        self.timelapse_job_info = timelapse_job_info
        self.job_id = timelapse_job_info.JobGuid
        self.job_number = job_number
        self.jobs_remaining = jobs_remaining
        self.camera = current_camera
        self.job_directory = os.path.join(data_directory, "snapshots", timelapse_job_info.JobGuid)
        self.snapshot_directory = os.path.join(data_directory, "snapshots", timelapse_job_info.JobGuid, current_camera.guid)
        self.snapshot_filename_format = os.path.basename(
            utility.get_snapshot_filename(
                timelapse_job_info.PrintFileName, timelapse_job_info.PrintStartTime, utility.SnapshotNumberFormat
            )
        )
        self.pre_roll_snapshot_filename_format = utility.get_pre_roll_snapshot_filename(
            timelapse_job_info.PrintFileName, timelapse_job_info.PrintStartTime, utility.SnapshotNumberFormat
        )
        self.output_tokens = self._get_output_tokens(data_directory)
        self.rendering = rendering.clone()
        self.ffmpeg_path = ffmpeg_path
        self.cleanup_after_complete = rendering.cleanup_after_render_complete
        self.cleanup_after_fail = rendering.cleanup_after_render_fail

    def _get_output_tokens(self, data_directory):
        job_info = self.timelapse_job_info
        assert(isinstance(job_info, utility.TimelapseJobInfo))

        return {
            "FAILEDFLAG": "FAILED" if job_info.PrintEndState != "COMPLETED" else "",
            "FAILEDSEPARATOR": "_" if job_info.PrintEndState != "COMPLETED" else "",
            "FAILEDSTATE": "" if job_info.PrintEndState == "COMPLETED" else job_info.PrintEndState,
            "PRINTSTATE": job_info.PrintEndState,
            "GCODEFILENAME": job_info.PrintFileName,
            "PRINTENDTIME": time.strftime("%Y%m%d%H%M%S", time.localtime(job_info.PrintEndTime)),
            "PRINTENDTIMESTAMP": "{0:d}".format(math.trunc(round(job_info.PrintEndTime, 2) * 100)),
            "PRINTSTARTTIME": time.strftime("%Y%m%d%H%M%S", time.localtime(job_info.PrintStartTime)),
            "PRINTSTARTTIMESTAMP": "{0:d}".format(math.trunc(round(job_info.PrintStartTime, 2) * 100)),
            "DATETIMESTAMP": "{0:d}".format(math.trunc(round(time.time(), 2) * 100)),
            "DATADIRECTORY": data_directory,
            "SNAPSHOTCOUNT": 0,
            "FPS": 0,
        }


class RenderingProcessor(threading.Thread):
    def __init__(
        self, rendering_task_queue, data_directory, octoprint_timelapse_folder,
        on_prerender_start, on_start, on_success, on_error, on_end
    ):
        super(RenderingProcessor, self).__init__()
        self.lock = threading.Lock()

        self.rendering_task_queue = rendering_task_queue
        # make a local copy of everything.
        self.data_directory = data_directory
        self.octoprint_timelapse_folder = octoprint_timelapse_folder
        self.on_prerender_start = on_prerender_start
        self.on_start = on_start
        self.on_success = on_success
        self.on_error = on_error
        self.on_end = on_end
        self.cameras = []
        self.print_state = "unknown"
        self.time_added = 0
        #self.daemon = True
        self.job_count = 0
        self._is_processing = False

    def is_processing(self):
        with self.lock:
            return self._is_processing

    def run(self):
        while True:
            try:
                logger.verbose("Looking for rendering tasks.")
                job_info = self.rendering_task_queue.get(timeout=5)
                assert(isinstance(job_info, RenderJobInfo))
                self.job_count += 1
                with self.lock:
                    self._is_processing = True

                job_info.job_number = self.job_count
                job_info.jobs_remaining = self.rendering_task_queue.qsize()
                job = TimelapseRenderJob(
                    job_info.rendering,
                    job_info,
                    self.octoprint_timelapse_folder,
                    job_info.ffmpeg_path,
                    job_info.rendering.thread_count,
                    job_info.rendering.cleanup_after_render_complete,
                    job_info.rendering.cleanup_after_render_fail,
                    self.on_prerender_start,
                    self.on_render_start,
                    self.on_render_error,
                    self.on_render_success
                )
                # send the rendering start message
                try:
                    job.process()
                ## What exceptions can happen here?
                except Exception as e:
                    logger.exception("Failed to process the rendering job")
                    raise e
                finally:
                    self.rendering_task_queue.task_done()

                if self.rendering_task_queue.qsize() == 0:
                    with self.lock:
                        self._is_processing = False
                    logger.info("Sending render end message")
                    self.on_render_end()

            except queue.Empty:
                if self._is_processing:
                    self._is_processing = False
            except Exception as e:
                logger.exception(e)
                raise e

    def on_prerender_start(self, payload):
        logger.info("Sending prerender start message")
        self.on_prerender_start(payload)

    def on_render_start(self, payload):
        logger.info("Sending render start message")
        self.on_start(payload)

    def on_render_error(self, payload, error):
        logger.info("Sending render fail message")
        self.on_error(payload, error)

    def on_render_success(self, payload):
        logger.info("Sending render complete message")
        self.on_success(payload)

    def on_render_end(self):
        logger.info("Sending render end message")
        self.on_end()


class TimelapseRenderJob(object):
    render_job_lock = threading.RLock()

    def __init__(
        self,
        rendering,
        render_job_info,
        octoprint_timelapse_folder,
        ffmpeg_path,
        threads,
        cleanup_on_success,
        cleanup_on_fail,
        on_prerender_start,
        on_render_start,
        on_render_error,
        on_render_success
    ):
        self._rendering = rendering

        self.render_job_info = render_job_info

        self._octoprintTimelapseFolder = octoprint_timelapse_folder
        self._fps = None
        self._snapshot_metadata = None
        self._imageCount = None
        self._threads = threads
        self._ffmpeg = None
        self._images_removed = 0
        if ffmpeg_path is not None:
            self._ffmpeg = ffmpeg_path.strip()
            if sys.platform == "win32" and not (self._ffmpeg.startswith('"') and self._ffmpeg.endswith('"')):
                self._ffmpeg = "\"{0}\"".format(self._ffmpeg)
        ###########
        # callbacks
        ###########
        self._thread = None
        self.cleanAfterSuccess = cleanup_on_success
        self.cleanAfterFail = cleanup_on_fail
        self._synchronize = False
        # full path of the input
        self.temp_rendering_dir = None
        self._output_directory = ""
        self._output_filename = ""
        self._output_extension = ""
        self._rendering_output_file_path = ""
        self._synchronized_directory = ""
        self._synchronized_filename = ""
        self._synchronize = self._rendering.sync_with_timelapse
        # render script errors
        self.before_render_error = None
        self.after_render_error = None
        # callbacks
        self.on_prerender_start = on_prerender_start
        self.on_render_start = on_render_start
        self.on_render_error = on_render_error
        self.on_render_success = on_render_success

    def process(self):
        return self._render()

    def _pre_render(self):
        # remove frames from the timelapse as specified by the snapshots_to_skip_beginning and
        # snapshot_to_skip_end settings
        self._remove_frames()

        # count the remaining snapshots
        self._count_snapshots()

        # read any metadata produced by the timelapse process
        # this is used to create text overlays
        self._read_snapshot_metadata()

        # If there aren't enough images, report an error
        # First see if there were enough images, but they were removed because of the the
        # snapshots_to_skip_beginning and snapshot_to_skip_end settings
        if self._images_removed > 1 and self._imageCount < 2:
            raise RenderError(
                'insufficient-images',
                "Not enough snapshots were found to generate a timelapse for the '{0}' camera profile.  {1} snapshot "
                "were removed during pre-processing.".format(self.render_job_info.camera.name, self._images_removed)
            )
        if self._imageCount == 0:
            raise RenderError(
                'insufficient-images',
                "No snapshots were available for the '{0}' camera profile.".format(self.render_job_info.camera.name)
              )
        if self._imageCount == 1:
            raise RenderError('insufficient-images',
                              "Only 1 frame was available, cannot make a timelapse with a single frame.")
        # calculate the FPS
        self._calculate_fps()
        if self._fps < 1:
            raise RenderError('insufficient-images', "The calculated FPS is below 1, which is not allowed. "
                                                     "Please check the rendering settings for Min and Max FPS "
                                                     "as well as the number of snapshots captured.")

        # set the outputs - output directory, output filename, output extension
        self._set_outputs()

    def _pre_render_script(self):
        try:
            script = self.render_job_info.camera.on_before_render_script.strip()
            if not script:
                return
            try:
                script_args = [
                    script,
                    self.render_job_info.camera.name,
                    self.render_job_info.snapshot_directory,
                    self.render_job_info.snapshot_filename_format,
                    os.path.join(self.render_job_info.snapshot_directory, self.render_job_info.snapshot_filename_format)
                ]

                logger.info(
                    "Running the following before-render script command: %s \"%s\" \"%s\" \"%s\" \"%s\"",
                    script_args[0],
                    script_args[1],
                    script_args[2],
                    script_args[3],
                    script_args[4]
                )
                cmd = utility.POpenWithTimeout()
                return_code = cmd.run(script_args, None)
                console_output = cmd.stdout
                error_message = cmd.stderr
            except utility.POpenWithTimeout.ProcessError as e:
                raise RenderError(
                    'before_render_script_error',
                    "A script occurred while executing executing the before-render script",
                    cause=e
                )
            if error_message:
                if error_message.endswith("\r\n"):
                    error_message = error_message[:-2]
                logger.error(
                    "Error output was returned from the before-rendering script: %s\nThe console output for the "
                    "error:  \n    %s",
                    error_message,
                    console_output
                )
            if not return_code == 0:
                if error_message:
                    error_message = "The before-render script failed with the following error message: {0}" \
                        .format(error_message)
                else:
                    error_message = (
                        "The before-render script returned {0},"
                        " which indicates an error.".format(return_code)
                    )
                raise RenderError('before_render_script_error', error_message)
        except RenderError as e:
            self.before_render_error = e

    def _post_render_script(self):
        try:
            script = self.render_job_info.camera.on_after_render_script.strip()
            if not script:
                return
            try:
                script_args = [
                    script,
                    self.render_job_info.camera.name,
                    self.render_job_info.snapshot_directory,
                    self.render_job_info.snapshot_filename_format,
                    os.path.join(
                        self.render_job_info.snapshot_directory, self.render_job_info.snapshot_filename_format
                    ),
                    self._output_directory,
                    self._output_filename,
                    self._output_extension,
                    self._rendering_output_file_path,
                    self._synchronized_directory,
                    self._synchronized_filename,

                ]

                logger.info(
                    'Running the following after-render script command: %s "%s" "%s" "%s" "%s" "%s" "%s" "%s" '
                    '"%s" "%s" "%s"',

                    script_args[0],
                    script_args[1],
                    script_args[2],
                    script_args[3],
                    script_args[4],
                    script_args[5],
                    script_args[6],
                    script_args[7],
                    script_args[8],
                    script_args[9],
                    script_args[10]
                )

                cmd = utility.POpenWithTimeout()
                return_code = cmd.run(script_args, None)
                console_output = cmd.stdout
                error_message = cmd.stderr
            except utility.POpenWithTimeout.ProcessError as e:
                raise RenderError(
                    'after_render_script_error',
                    "A script occurred while executing executing the after-render script",
                    cause=e
                )
            if error_message:
                if error_message.endswith("\r\n"):
                    error_message = error_message[:-2]
                logger.error(
                    "Error output was returned from the after-rendering script: %s",
                    error_message
                )
            if not return_code == 0:
                if error_message:
                    error_message = "The after-render script failed with the following error message: {0}" \
                        .format(error_message)
                else:
                    error_message = (
                        "The after-render script returned {0},"
                        " which indicates an error.".format(return_code)
                    )
                raise RenderError('after_render_script_error', error_message)
        except RenderError as e:
            self.after_render_error = e

    def _remove_frames(self):
        start_count = self._rendering.snapshots_to_skip_beginning
        end_count = self._rendering.snapshot_to_skip_end
        # get the path to the snapshot
        path = self.render_job_info.snapshot_directory
        # make sure the path exists
        if not os.path.exists(self.render_job_info.snapshot_directory):
            # there is nothing we can do here.  Return
            return

        # see if there are start frames to remove
        if start_count > 0:
            # iterate a sorted list of snapshot files starting from the first snapshots taken
            for index, filename in enumerate(sorted(os.listdir(path))):
                # only remove jpeg files
                if not filename.lower().endswith(".jpg"):
                    continue
                # break if we've removed enough files
                if start_count < 1:
                    break
                # create a path to the current file
                file_path = os.path.join(path, filename)
                os.remove(file_path)
                self._images_removed += 1
                start_count -= 1

            logger.info(
                "%d snapshots were removed from the beginning of the timelapse.",
                self._rendering.snapshots_to_skip_beginning
            )

        # see if there are end frames to remove
        if end_count > 0:
            # iterate a sorted list of snapshot files starting from the last snapshots taken
            for index, filename in enumerate(sorted(os.listdir(path), reverse=True)):
                # only remove jpeg files
                if not filename.lower().endswith(".jpg"):
                    continue
                # break if we've removed enough files
                if end_count < 1:
                    break
                # create a path to the current file
                file_path = os.path.join(path, filename)
                os.remove(file_path)
                self._images_removed += 1
                end_count -= 1

            logger.info(
                "%d snapshots were removed from the end of the timelapse.",
                self._rendering.snapshot_to_skip_end
            )

    def _count_snapshots(self):
        self._imageCount = 0
        if os.path.exists(self.render_job_info.snapshot_directory):
            for file in os.listdir(
                os.path.dirname(os.path.join(
                    self.render_job_info.snapshot_directory, self.render_job_info.snapshot_filename_format)
                )
            ):
                if file.endswith(".jpg"):
                    self._imageCount += 1

        self.render_job_info.output_tokens["SNAPSHOTCOUNT"] = "{0}".format(self._imageCount)
        logger.info("Found %s images via a manual search.", self._imageCount)

    def _read_snapshot_metadata(self):
        # get the metadata path
        metadata_path = os.path.join(self.render_job_info.snapshot_directory, SnapshotMetadata.METADATA_FILE_NAME)
        # make sure the metadata file exists
        if not os.path.isfile(metadata_path):
            # nothing to do here.  Exit
            return
        # see if the metadata file exists
        logger.info('Reading snapshot metadata from %s', metadata_path)
        skip_beginning = self._rendering.snapshots_to_skip_beginning
        skip_end = self._rendering.snapshot_to_skip_end
        try:
            with open(metadata_path, 'r') as metadata_file:
                # read the metadaata and convert it to a dict
                dictreader = DictReader(metadata_file, SnapshotMetadata.METADATA_FIELDS)
                # convert the dict to a list
                metadata_list = list(dictreader)
                # remove metadata for any removed frames due to the
                # snapshots_to_skip_beginning and snapshot_to_skip_end settings
                self._snapshot_metadata = metadata_list[skip_beginning:len(metadata_list)-skip_end]

                # add the snapshot count to the output tokens
                self.render_job_info.output_tokens["SNAPSHOTCOUNT"] = "{0}".format(self._imageCount)
                return
        except IOError as e:
            logger.exception("No metadata exists, skipping metadata processing.")
            # If we fail to read the metadata, it could be that no snapshots were taken.
            # Let's not throw an error and just render without the metadata
            pass

    def _calculate_fps(self):
        self._fps = self._rendering.fps

        if self._rendering.fps_calculation_type == 'duration':

            self._fps = utility.round_to(
                float(self._imageCount) / float(self._rendering.run_length_seconds), 0.001)
            if self._fps > self._rendering.max_fps:
                self._fps = self._rendering.max_fps
            elif self._fps < self._rendering.min_fps:
                self._fps = self._rendering.min_fps
            message = (
                "FPS Calculation Type:%s, Fps:%s, NumFrames:%s, "
                "DurationSeconds:%s, Max FPS:%s, Min FPS:%s"
            )
            logger.info(
                message,
                self._rendering.fps_calculation_type,
                self._fps,
                self._imageCount,
                self._rendering.run_length_seconds,
                self._rendering.max_fps,
                self._rendering.min_fps
            )
        else:
            logger.info("FPS Calculation Type:%s, Fps:%s", self._rendering.fps_calculation_type, self._fps)
        # Add the FPS to the output tokens
        self.render_job_info.output_tokens["FPS"] = "{0}".format(int(math.ceil(self._fps)))

    def _set_outputs(self):
        self._output_directory = "{0}{1}{2}{3}".format(
            self.render_job_info.output_tokens["DATADIRECTORY"], os.sep, "timelapse", os.sep
        )
        try:
            self._output_filename = self._rendering.output_template.format(**self.render_job_info.output_tokens)
        except ValueError as e:
            logger.exception("Failed to format the rendering output template.")
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

    def create_callback_payload(self, return_code, reason):
        return RenderingCallbackArgs(
            reason,
            return_code,
            self.render_job_info.job_id,
            self.render_job_info.job_directory,
            self.render_job_info.snapshot_directory,
            self._output_directory,
            self._output_filename,
            self._output_extension,
            self._synchronized_directory,
            self._synchronized_filename,
            self._synchronize,
            self._imageCount,
            self.render_job_info.job_number,
            self.render_job_info.jobs_remaining,
            self.render_job_info.camera.name,
            self.before_render_error,
            self.after_render_error

        )

    def _render(self):
        """Rendering runnable."""
        # set an error variable to None, we will return None if there are no problems
        r_error = None
        try:
            self.on_prerender_start(self.create_callback_payload(0,"Prerender is starting."))

            self._pre_render_script()

            self._pre_render()

            logger.info("Starting render.")
            self.on_render_start(self.create_callback_payload(0, "Starting to render timelapse."))

            # Temporary directory to store intermediate results of rendering.
            self.temp_rendering_dir = mkdtemp(prefix='octolapse_render')

            if self._ffmpeg is None:
                raise RenderError('ffmpeg_path', "Cannot create movie, path to ffmpeg is unset. "
                                                 "Please configure the ffmpeg path within the "
                                                 "'Features->Webcam & Timelapse' settings tab.")

            if self._rendering.bitrate is None:
                raise RenderError('no-bitrate', "Cannot create movie, desired bitrate is unset. "
                                                "Please set the bitrate within the Octolapse rendering profile.")

            try:
                logger.info("Creating the directory at %s", self._output_directory)

                if not os.path.exists(self._output_directory):
                    os.makedirs(self._output_directory)
            except Exception as e:
                raise RenderError('create-render-path',
                                  "Render - An exception was thrown when trying to "
                                  "create the rendering path at: {0}.  Please check "
                                  "the logs (plugin_octolapse.log) for details.".format(self._output_directory),
                                  cause=e)

            watermark_path = None
            if self._rendering.enable_watermark:
                watermark_path = self._rendering.selected_watermark
                if watermark_path == '':
                    logger.error("Watermark was enabled but no watermark file was selected.")
                    watermark_path = None
                elif not os.path.exists(watermark_path):
                    logger.error("Render - Watermark file does not exist.")
                    watermark_path = None
                elif sys.platform == "win32":
                    # Because ffmpeg hiccups on windows' drive letters and backslashes we have to give the watermark
                    # path a special treatment. Yeah, I couldn't believe it either...
                    watermark_path = watermark_path.replace(
                        "\\", "/").replace(":", "\\\\:")

            # Do image preprocessing.  This relies on the original file name, so no renaming before running
            # this function
            self._preprocess_images(self.temp_rendering_dir)

            # rename the images
            self._rename_images(self.temp_rendering_dir)

            # Add pre and post roll.
            self._apply_pre_post_roll(self.temp_rendering_dir)

            # prepare ffmpeg command
            command_str = self._create_ffmpeg_command_string(
                os.path.join(self.temp_rendering_dir, self.render_job_info.snapshot_filename_format),
                self._rendering_output_file_path,
                watermark=watermark_path
            )
            logger.info("Running ffmpeg with command string: %s", command_str)

            with self.render_job_lock:
                try:
                    p = sarge.run(
                        command_str, stdout=sarge.Capture(), stderr=sarge.Capture())
                except Exception as e:
                    raise RenderError('rendering-exception', "ffmpeg failed during rendering of movie. "
                                                             "Please check plugin_octolapse.log for details.",
                                      cause=e)
                if p.returncode != 0:
                    return_code = p.returncode
                    stderr_text = p.stderr.text
                    raise RenderError('return-code', "Could not render movie, got return code %r: %s" % (
                        return_code, stderr_text))

            # run any post rendering scripts
            self._post_render_script()

            # Delete preprocessed images.
            if self.cleanAfterSuccess:
                shutil.rmtree(self.temp_rendering_dir)

            if self._synchronize:
                # Move the timelapse to the Octoprint timelapse folder.
                try:
                    # get the timelapse folder for the Octoprint timelapse plugin
                    synchronization_path = "{0}{1}.{2}".format(
                        self._synchronized_directory, self._synchronized_filename, self._output_extension
                    )
                    message = (
                        "Synchronizing timelapse with the built in "
                        "timelapse plugin, copying %s to %s"
                    )
                    logger.info(message, self._rendering_output_file_path, synchronization_path)
                    shutil.move(self._rendering_output_file_path, synchronization_path)
                    # we've renamed the output due to a sync, update the member
                except Exception as e:
                    raise RenderError('synchronizing-exception',
                                      "Octolapse has failed to synchronize the default timelapse plugin due"
                                      " to an unexpected exception.  Check plugin_octolapse.log for more "
                                      " information.  You should be able to find your video within your "
                                      " OctoPrint  server here:<br/> '{0}'".format(self._rendering_output_file_path),
                                      cause=e)
        except Exception as e:
            logger.exception("Rendering Error")
            if isinstance(e, RenderError):
                r_error = e
            else:
                r_error = RenderError('render-error',
                                      "Unknown render error. Please check plugin_octolapse.log for more details.",
                                      e)
            if self.cleanAfterFail:
                # Delete preprocessed images.
                if self.temp_rendering_dir is not None:
                    shutil.rmtree(self.temp_rendering_dir)
        if r_error is None:
            self.on_render_success(self.create_callback_payload(0, "Timelapse rendering is complete."))
        else:
            self.on_render_error(self.create_callback_payload(0, "The render process failed."), r_error)

    def _preprocess_images(self, preprocessed_directory):
        logger.info("Starting preprocessing of images.")
        if self._snapshot_metadata is None:
            logger.info("Snapshot metadata file missing; skipping preprocessing.")
            # Just copy images over.
            for i in range(self._imageCount):
                file_path = os.path.join(
                    self.render_job_info.snapshot_directory, self.render_job_info.snapshot_filename_format % i)
                if os.path.exists(file_path):
                    output_path = os.path.join(preprocessed_directory, self.render_job_info.snapshot_filename_format % i)
                    output_dir = os.path.dirname(output_path)
                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir)
                    shutil.move(file_path, output_path)
                else:
                    logger.error("The snapshot at %s does not exist.  Skipping.", file_path)
            return
        first_timestamp = float(self._snapshot_metadata[0]['time_taken'])
        for index, data in enumerate(self._snapshot_metadata):
            # TODO:  MAKE SURE THIS WORKS IF THERE ARE ANY ERRORS
            # Variables the user can use in overlay_text_template.format().
            format_vars = {}

            # Extra metadata according to SnapshotMetadata.METADATA_FIELDS.
            format_vars['snapshot_number'] = snapshot_number = int(data['snapshot_number'])
            format_vars['file_name'] = data['file_name']
            format_vars['time_taken_s'] = time_taken = float(data['time_taken'])

            # Verify that the file actually exists.
            file_path = os.path.join(
                self.render_job_info.snapshot_directory,
                self.render_job_info.snapshot_filename_format % snapshot_number
            )
            if os.path.exists(file_path):
                # Calculate time elapsed since the beginning of the print.
                format_vars['current_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time_taken))
                format_vars['time_elapsed'] = "{}".format(
                    datetime.timedelta(seconds=round(time_taken - first_timestamp))
                )

                # Open the image in Pillow and do preprocessing operations.
                image = Image.open(file_path)
                image = self.add_overlay(image,
                                 text_template=self._rendering.overlay_text_template,
                                 format_vars=format_vars,
                                 font_path=self._rendering.overlay_font_path,
                                 font_size=self._rendering.overlay_font_size,
                                 overlay_location=self._rendering.overlay_text_pos,
                                 overlay_text_alignment=self._rendering.overlay_text_alignment,
                                 overlay_text_valign=self._rendering.overlay_text_valign,
                                 overlay_text_halign=self._rendering.overlay_text_halign,
                                 text_color=self._rendering.get_overlay_text_color(),
                                 outline_color=self._rendering.get_overlay_outline_color(),
                                 outline_width=self._rendering.overlay_outline_width)
                # Save processed image.
                output_path = os.path.join(
                    preprocessed_directory, self.render_job_info.snapshot_filename_format % snapshot_number)
                if not os.path.exists(os.path.dirname(output_path)):
                    os.makedirs(os.path.dirname(output_path))
                image.save(output_path)
            else:
                file_path = os.path.join(
                    self.render_job_info.snapshot_directory,
                    self.render_job_info.snapshot_filename_format % (
                        index + self._rendering.snapshots_to_skip_beginning
                    )
                )
                if os.path.exists(file_path):
                    output_path = os.path.join(
                        preprocessed_directory,
                        self.render_job_info.snapshot_filename_format % (
                            index +  self._rendering.snapshots_to_skip_beginning
                        )
                    )
                    output_dir = os.path.dirname(output_path)
                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir)
                    shutil.move(file_path, output_path)
                else:
                    logger.error("The snapshot at %s does not exist.  Skipping.", file_path)

        logger.info("Preprocessing success!")

    def _rename_images(self, preprocessed_directory):
        # First, we need to rename our files, but we have to change the file name so that it won't overwrite any existing files
        image_index = 0
        for filename in sorted(os.listdir(preprocessed_directory)):
            # make sure the file is a jpg image
            if filename.lower().endswith(".jpg"):
                output_path = os.path.join(
                    preprocessed_directory,
                    "{0}.tmp".format(self.render_job_info.snapshot_filename_format % image_index)
                )
                file_path = os.path.join(preprocessed_directory, filename)
                shutil.move(file_path, output_path)
                image_index += 1

        # now loop back through all of the files and remove the .tmp extension
        for filename in os.listdir(preprocessed_directory):
            if filename.endswith(".tmp"):
                output_path = os.path.join(preprocessed_directory, filename[:-4])
                file_path = os.path.join(preprocessed_directory, filename)
                shutil.move(file_path, output_path)


    @staticmethod
    def add_overlay(image, text_template, format_vars, font_path, font_size, overlay_location, overlay_text_alignment,
                    overlay_text_valign, overlay_text_halign, text_color, outline_color, outline_width):
        """Adds an overlay to an image with the given parameters. The image is not mutated.
        :param image: A Pillow RGB image.
        :returns The image with the overlay added."""

        text_color_tuple = tuple(text_color)
        outline_color_tuple = tuple(outline_color)
        # No text to draw.
        if not text_template:
            return image
        text = text_template.format(**format_vars)

        # Retrieve the correct font.
        if not font_path:
            raise RenderError('overlay-font', "No overlay font was specified when attempting to add overlay.")
        font = ImageFont.truetype(font_path, size=font_size)

        # Create the image to draw on.
        text_image = Image.new('RGBA', image.size, (255, 255, 255, 0))
        d = ImageDraw.Draw(text_image)

        # Process the text position to improve the alignment.
        if isinstance(overlay_location, string_types):
            overlay_location = json.loads(overlay_location)
        x, y = tuple(overlay_location)
        # valign.
        if overlay_text_valign == 'top':
            pass
        elif overlay_text_valign == 'middle':
            textsize = d.multiline_textsize(text, font=font, spacing=0)
            y += image.size[1] / 2 - textsize[1] / 2
        elif overlay_text_valign == 'bottom':
            textsize = d.multiline_textsize(text, font=font, spacing=0)
            y += image.size[1] - textsize[1]
        else:
            raise RenderError('overlay-text-valign',
                              "An invalid overlay text valign ({0}) was specified.".format(overlay_text_valign))
        # halign.
        if overlay_text_halign == 'left':
            pass
        elif overlay_text_halign == 'center':
            textsize = d.multiline_textsize(text, font=font, spacing=0)
            x += image.size[0] / 2 - textsize[0] / 2
        elif overlay_text_halign == 'right':
            textsize = d.multiline_textsize(text, font=font, spacing=0)
            x += image.size[0] - textsize[0]
        else:
            raise RenderError('overlay-text-halign',
                              "An invalid overlay text halign ({0}) was specified.".format(overlay_text_halign))

        # Draw overlay text outline
        # create outline text
        for adj in range(outline_width):
            # move right
            d.multiline_text(xy=(x - adj, y), text=text, font=font, fill=outline_color_tuple)
            # move left
            d.multiline_text(xy=(x + adj, y), text=text, font=font, fill=outline_color_tuple)
            # move up
            d.multiline_text(xy=(x, y + adj), text=text, font=font, fill=outline_color_tuple)
            # move down
            d.multiline_text(xy=(x, y - adj), text=text, font=font, fill=outline_color_tuple)
            # diagnal left up
            d.multiline_text(xy=(x - adj, y + adj), text=text, font=font, fill=outline_color_tuple)
            # diagnal right up
            d.multiline_text(xy=(x + adj, y + adj), text=text, font=font, fill=outline_color_tuple)
            # diagnal left down
            d.multiline_text(xy=(x - adj, y - adj), text=text, font=font, fill=outline_color_tuple)
            # diagnal right down
            d.multiline_text(xy=(x + adj, y - adj), text=text, font=font, fill=outline_color_tuple)

        # Draw overlay text.
        d.multiline_text(xy=(x, y), text=text, fill=text_color_tuple, font=font, align=overlay_text_alignment)


        return Image.alpha_composite(image.convert('RGBA'), text_image).convert('RGB')

    def _apply_pre_post_roll(self, image_dir):
        # Here we will be adding pre and post roll frames.
        # This routine assumes that images exist, that the first image has number 0, and that
        # there are no missing images
        logger.info("Starting pre/post roll.")
        # start with pre-roll.
        pre_roll_frames = int(self._rendering.pre_roll_seconds * self._fps)
        if pre_roll_frames > 0:
            # We will be adding images starting with -1 and decrementing 1 until we've added the
            # correct number of frames.

            # create a variable to hold the new path of the first image
            first_image_path = os.path.join(image_dir, self.render_job_info.snapshot_filename_format % 0)

            # rename all of the current files. The snapshot number should be
            # incremented by the number of pre-roll frames. Start with the last
            # image and work backwards to avoid overwriting files we've already moved
            for image_number in range(pre_roll_frames):
                new_image_path = os.path.join(
                    image_dir,
                    self.render_job_info.pre_roll_snapshot_filename_format % (0, image_number)
                )
                shutil.copy(first_image_path, new_image_path)
        # finish with post
        post_roll_frames = int(self._rendering.post_roll_seconds * self._fps)
        if post_roll_frames > 0:
            last_frame_index = self._imageCount - 1
            last_image_path = os.path.join(image_dir, self.render_job_info.snapshot_filename_format % last_frame_index)
            for post_roll_index in range(post_roll_frames):
                new_image_path = os.path.join(
                    image_dir,
                    self.render_job_info.pre_roll_snapshot_filename_format % (last_frame_index, post_roll_index)
                )
                shutil.copy(last_image_path, new_image_path)

        if pre_roll_frames > 0:
            # pre or post roll frames were added, so we need to rename all of our images
            self._rename_images(image_dir)
        logger.info("Pre/post roll generated successfully.")

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

    def _create_ffmpeg_command_string(self, input_file_format, output_file, watermark=None, pix_fmt="yuv420p"):
        """
        Create ffmpeg command string based on input parameters.
        Arguments:
            input_file_format (str): Absolute path to input files including file mask
            output_file (str): Absolute path to output file
            watermark (str): Path to watermark to apply to lower left corner.
            pix_fmt (str): Pixel format to use for output. Default of yuv420p should usually fit the bill.
        Returns:
            (str): Prepared command string to render `input` to `output` using ffmpeg.
        """

        v_codec = self._get_vcodec_from_output_format(self._rendering.output_format)

        command = [self._ffmpeg, '-framerate', "{}".format(self._fps), '-loglevel', 'error', '-i',
                   '"{}"'.format(input_file_format)]
        command.extend(
            ['-threads', "{}".format(self._threads), '-r', "{}".format(self._fps), '-y', '-b', "{}".format(self._rendering.bitrate), '-vcodec', v_codec])

        filter_string = self._create_filter_string(watermark=watermark, pix_fmt=pix_fmt)

        if filter_string is not None:
            logger.debug("Applying video filter chain: %s".format(filter_string))
            command.extend(["-vf", sarge.shell_quote(filter_string)])

        # finalize command with output file
        logger.debug("Rendering movie to %s".format(output_file))
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
        filter_names = ['f' + "{}".format(x) for x in range(len(filters))] + ['out']
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


class RenderError(Exception):
    def __init__(self, type, message, cause=None):
        super(Exception, self).__init__()
        self.type = type
        self.cause = cause if cause is not None else None
        self.message = message

    def __str__(self):
        if self.cause is None:
            return "{}: {}".format(self.type, self.message, "{}".format(self.cause))

        return "{}: {}.  Inner Exception: {}".format(self.type, self.message, "{}".format(self.cause))


class RenderingCallbackArgs(object):
    def __init__(
        self,
        reason,
        return_code,
        job_id,
        job_directory,
        snapshot_directory,
        rendering_directory,
        rendering_filename,
        rendering_extension,
        synchronized_directory,
        synchronized_filename,
        synchronize,
        snapshot_count,
        job_number,
        jobs_remaining,
        camera_name,
        before_render_error,
        after_render_error
    ):
        self.Reason = reason
        self.ReturnCode = return_code
        self.JobId = job_id
        self.JobDirectory = job_directory
        self.SnapshotDirectory = snapshot_directory
        self.RenderingDirectory = rendering_directory
        self.RenderingFilename = rendering_filename
        self.RenderingExtension = rendering_extension
        self.SynchronizedDirectory = synchronized_directory
        self.SynchronizedFilename = synchronized_filename
        self.Synchronize = synchronize
        self.SnapshotCount = snapshot_count
        self.JobNumber = job_number
        self.JobsRemaining = jobs_remaining
        self.CameraName = camera_name
        self.BeforeRenderError = before_render_error
        self.AfterRenderError = after_render_error

    def get_rendering_filename(self):
        return "{0}.{1}".format(self.RenderingFilename, self.RenderingExtension)

    def get_synchronization_filename(self):
        return "{0}.{1}".format(self.SynchronizedFilename, self.RenderingExtension)

    def get_rendering_path(self):
        return "{0}{1}".format(self.RenderingDirectory, self.get_rendering_filename())

    def get_synchronization_path(self):
        return "{0}{1}".format(self.SynchronizedDirectory, self.get_synchronization_filename())
