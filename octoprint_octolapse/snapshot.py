# coding=utf-8
##################################################################################
# Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
# Copyright (C) 2023  Brad Hochgesang
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
# remove unused usings
# import six
import os
import json
from csv import DictWriter
from time import sleep
import requests

# Recent versions of Pillow changed the case of the import
# Why!?
try:
    from pil import ImageFile
except ImportError:
    from PIL import ImageFile

from requests.auth import HTTPBasicAuth
from threading import Thread, Event
from tempfile import mkdtemp
from uuid import uuid4
from time import time
# Recent versions of Pillow changed the case of the import
# Why!?
try:
    from pil import Image
except ImportError:
    from PIL import Image

import errno
# create the module level logger
import octoprint_octolapse.camera as camera
import octoprint_octolapse.utility as utility
from octoprint_octolapse.gcode_commands import Commands
from octoprint_octolapse.utility import TimelapseJobInfo
from octoprint_octolapse.log import LoggingConfigurator
import octoprint_octolapse.script as script
logging_configurator = LoggingConfigurator()
logger = logging_configurator.get_logger(__name__)


class SnapshotMetadata(object):
    METADATA_FILE_NAME = 'metadata.csv'
    METADATA_FIELDS = [
        'snapshot_number', 'file_name', 'time_taken', 'layer', 'height', 'x', 'y', 'z', 'e', 'f',
        'x_snapshot', 'y_snapshot'
    ]

    @staticmethod
    def is_metadata_file(file_name):
        return file_name.lower() == SnapshotMetadata.METADATA_FILE_NAME

def take_in_memory_snapshot(settings, current_camera):
    """Takes a snapshot from the given camera in a temporary directory, loads the image into memory, and then deletes the file."""

    temp_snapshot_dir = None
    try:
        temp_snapshot_dir = mkdtemp()

        snapshot_job_info = SnapshotJobInfo(
            TimelapseJobInfo(job_guid=uuid4(),
                             print_start_time=time(),
                             print_file_name='overlay_preview',
                             ),
            temp_snapshot_dir, 0, current_camera, 'in-memory')
        if current_camera.camera_type == "script":
            snapshot_job = ExternalScriptSnapshotJob(snapshot_job_info, settings)
        else:
            snapshot_job = WebcamSnapshotJob(snapshot_job_info)
        snapshot_job.daemon = True
        snapshot_job.start()
        snapshot_job.join()
        # Copy the image into memory so that we can delete the original file.
        with Image.open(snapshot_job_info.snapshot_full_path) as image_file:
            return image_file.copy()
    finally:
        # Cleanup.
        utility.rmtree(temp_snapshot_dir)


class CaptureSnapshot(object):

    def __init__(self, settings, data_directory, cameras, timelapse_job_info, send_gcode_array_callback
                 , on_new_thumbnail_available_callback, on_post_processing_error_callback):
        self.Cameras = []
        for current_camera in cameras:
            self.Cameras.append(current_camera)

        self.CameraInfos = {}
        for current_camera in self.Cameras:
            self.CameraInfos.update(
                {"{}".format(current_camera.guid): CameraInfo()}
            )
        self.temporary_directory = settings.main_settings.get_temporary_directory(data_directory)
        self.TimelapseJobInfo = utility.TimelapseJobInfo(timelapse_job_info)
        self.SnapshotsTotal = 0
        self.ErrorsTotal = 0
        self.SendGcodeArrayCallback = send_gcode_array_callback
        self.OnNewThumbnailAvailableCallback = on_new_thumbnail_available_callback
        self.on_post_processing_error_callback = on_post_processing_error_callback

    def take_snapshots(self, metadata={}, no_wait=False):
        logger.info("Starting snapshot acquisition")
        start_time = time()

        before_snapshot_threads = []
        snapshot_threads = []
        after_snapshot_threads = []
        results = []

        for current_camera in self.Cameras:
            camera_info = self.CameraInfos["{}".format(current_camera.guid)]

            # pre_snapshot threads
            if current_camera.on_before_snapshot_script:
                before_snapshot_job_info = SnapshotJobInfo(
                    self.TimelapseJobInfo,
                    self.temporary_directory,
                    camera_info.snapshot_attempt,
                    current_camera,
                    'before-snapshot',
                    metadata=metadata
                )
                thread = ExternalScriptSnapshotJob(before_snapshot_job_info, 'before-snapshot')
                thread.daemon = True
                before_snapshot_threads.append(
                    thread
                )

            snapshot_job_info = SnapshotJobInfo(
                self.TimelapseJobInfo,
                self.temporary_directory,
                camera_info.snapshot_attempt,
                current_camera,
                'snapshot',
                metadata=metadata
            )
            if current_camera.camera_type == "script":
                thread = ExternalScriptSnapshotJob(
                    snapshot_job_info,
                    'snapshot',
                    on_new_thumbnail_available_callback=self.OnNewThumbnailAvailableCallback,
                    on_post_processing_error_callback=self.on_post_processing_error_callback
                )
                thread.daemon = True
                snapshot_threads.append((thread, snapshot_job_info, None))
            elif current_camera.camera_type == "webcam":
                download_started_event = Event()
                thread = WebcamSnapshotJob(
                    snapshot_job_info,
                    download_started_event=download_started_event,
                    on_new_thumbnail_available_callback=self.OnNewThumbnailAvailableCallback,
                    on_post_processing_error_callback=self.on_post_processing_error_callback
                )
                thread.daemon = True
                snapshot_threads.append((thread, snapshot_job_info, download_started_event))

            # post_snapshot threads
            if current_camera.on_after_snapshot_script:
                after_snapshot_job_info = SnapshotJobInfo(
                    self.TimelapseJobInfo,
                    self.temporary_directory,
                    camera_info.snapshot_attempt,
                    current_camera,
                    'after-snapshot',
                    metadata=metadata
                )
                thread = ExternalScriptSnapshotJob(after_snapshot_job_info, 'after-snapshot')
                thread.daemon = True
                after_snapshot_threads.append(
                    thread
                )

        # Now that the before snapshot threads are prepared, send any before snapshot gcodes
        for current_camera in self.Cameras:
            if current_camera.on_before_snapshot_gcode:
                on_before_snapshot_gcode = Commands.string_to_gcode_array(current_camera.on_before_snapshot_gcode)
                if len(on_before_snapshot_gcode) > 0:
                    logger.info("Sending on_before_snapshot_gcode for the %s camera.", current_camera.name)
                    self.SendGcodeArrayCallback(
                        on_before_snapshot_gcode,
                        current_camera.timeout_ms / 1000.0,
                        wait_for_completion=not no_wait,
                        tags={'before-snapshot-gcode'}
                    )

        if len(before_snapshot_threads) > 0:
            logger.info("Starting %d before snapshot threads", len(before_snapshot_threads))

        # start the pre-snapshot threads
        for t in before_snapshot_threads:
            t.start()

        # join the pre-snapshot threads
        for t in before_snapshot_threads:
            if not no_wait:
                snapshot_job_info = t.join()
                assert (isinstance(snapshot_job_info, SnapshotJobInfo))
                if t.snapshot_thread_error:
                    snapshot_job_info.success = False
                    snapshot_job_info.error = t.snapshot_thread_error
                else:
                    snapshot_job_info.success = True
            else:
                snapshot_job_info.success = True
            results.append(snapshot_job_info)

        if len(before_snapshot_threads) > 0:
            logger.info("Before snapshot threads finished.")

        if len(snapshot_threads) > 0:
            logger.info("Starting %d snapshot threads.", len(snapshot_threads))
        # start the snapshot threads, then wait for all threads to signal before continuing
        for t in snapshot_threads:
            t[0].start()

        # now send any gcode for gcode cameras
        for current_camera in self.Cameras:
            if current_camera.camera_type == "gcode":
                script_sent = False
                if current_camera.gcode_camera_script:
                    gcode_camera_script = Commands.string_to_gcode_array(current_camera.gcode_camera_script)
                    if len(gcode_camera_script) > 0:
                        logger.info("Sending snapshot gcode array to %s.", current_camera.name)
                        # just send the gcode now so it all goes in order
                        self.SendGcodeArrayCallback(
                            Commands.string_to_gcode_array(current_camera.gcode_camera_script),
                            current_camera.timeout_ms/1000.0,
                            wait_for_completion=not no_wait
                        )
                        script_sent = True
                    if not script_sent:
                        logger.warning("The gcode camera '%s' is enabled, but failed to produce any snapshot gcode.", current_camera.name)

        for t, snapshot_job_info, event in snapshot_threads:
            if not no_wait:
                if event:
                    event.wait()
                else:
                    snapshot_job_info = t.join()
                if t.snapshot_thread_error:
                    snapshot_job_info.success = False
                    snapshot_job_info.error = t.snapshot_thread_error
                elif t.post_processing_error:
                    snapshot_job_info.success = False
                    snapshot_job_info.error = t.post_processing_error
                else:
                    snapshot_job_info.success = True
            else:
                snapshot_job_info.success = True

            info = self.CameraInfos[snapshot_job_info.camera_guid]
            info.snapshot_attempt += 1
            if snapshot_job_info.success:
                info.snapshot_count += 1
                self.SnapshotsTotal += 1
            else:
                info.errors_count += 1
                self.ErrorsTotal += 1
            info.save(self.temporary_directory, self.TimelapseJobInfo.JobGuid, snapshot_job_info.camera_guid)
            results.append(snapshot_job_info)

        if len(snapshot_threads) > 0:
            logger.info("Snapshot threads complete, but may be post-processing.")

        if len(after_snapshot_threads) > 0:
            logger.info("Starting %d after snapshot threads.", len(after_snapshot_threads))

        # Now that the after snapshot threads are prepared, send any after snapshot gcodes
        for current_camera in self.Cameras:
            if current_camera.on_after_snapshot_gcode:
                on_after_snapshot_gcode = Commands.string_to_gcode_array(current_camera.on_after_snapshot_gcode)
                if len(on_after_snapshot_gcode) > 0:
                    logger.info("Sending on_after_snapshot_gcode for the %s camera.", current_camera.name)
                    self.SendGcodeArrayCallback(
                        on_after_snapshot_gcode,
                        current_camera.timeout_ms / 1000.0,
                        wait_for_completion=not no_wait,
                        tags={'after-snapshot-gcode'}
                    )

        # start the after-snapshot threads
        for t in after_snapshot_threads:
            t.start()

        # join the after-snapshot threads
        for t in after_snapshot_threads:
            if not no_wait:
                snapshot_job_info = t.join()
                assert (isinstance(snapshot_job_info, SnapshotJobInfo))
                info = self.CameraInfos[snapshot_job_info.camera_guid]
                if t.snapshot_thread_error:
                    snapshot_job_info.success = False
                    snapshot_job_info.error = t.snapshot_thread_error
                else:
                    snapshot_job_info.success = True
            else:
                snapshot_job_info.success = True
            results.append(snapshot_job_info)

        if len(after_snapshot_threads) > 0:
            logger.info("After snapshot threads complete.")

        logger.info("Snapshot acquisition completed in %.3f seconds.", time()-start_time)

        return results


class ImagePostProcessing(object):
    def __init__(self, snapshot_job_info, on_new_thumbnail_available_callback=None,
                 on_post_processing_error_callback=None, request=None):
        assert(isinstance(snapshot_job_info, SnapshotJobInfo))
        self.snapshot_job_info = snapshot_job_info
        self.on_new_thumbnail_available_callback = on_new_thumbnail_available_callback
        self.on_post_processing_error_callback = on_post_processing_error_callback
        self.request = request

    def process(self):
        try:
            logger.debug("Post-processing snapshot for the %s camera.", self.snapshot_job_info.camera.name)
            if self.request is not None:
                self.save_image_from_request()
                self.request.close()
            # Post Processing and Meta Data Creation
            # Always write metadata
            self.write_metadata()
            # only process image manipulation if the image exists
            if os.path.isfile(self.snapshot_job_info.snapshot_full_path):
                self.transpose_image()
                self.create_thumbnail()
                if self.on_new_thumbnail_available_callback is not None:
                    self.on_new_thumbnail_available_callback(self.snapshot_job_info.camera.guid)
            else:
                logger.debug(
                    "Snapshot #%d does not exist for the %s camera.",
                    self.snapshot_job_info.snapshot_number,
                    self.snapshot_job_info.camera.name)
        except SnapshotError as e:
            if self.on_post_processing_error_callback is not None:
                self.on_post_processing_error_callback(e)

        finally:
            logger.debug("Post-processing snapshot for the %s camera complete.", self.snapshot_job_info.camera.name)

    def save_image_from_request(self):
        try:
            if not os.path.exists(self.snapshot_job_info.snapshot_directory):
                try:
                    os.makedirs(self.snapshot_job_info.snapshot_directory)
                except OSError as e:
                    if e.errno == errno.EEXIST:
                        pass
                    else:
                        raise
            with open(self.snapshot_job_info.snapshot_full_path, 'wb+') as snapshot_file:
                for chunk in self.request.iter_content(chunk_size=512 * 1024):
                    if chunk:
                        snapshot_file.write(chunk)

                logger.debug("Snapshot - Snapshot saved to disk for the %s camera at %s",
                             self.snapshot_job_info.camera.name, self.snapshot_job_info.snapshot_full_path)
        except Exception as e:
            logger.exception("An unexpected exception occurred while saving a snapshot from a request for "
                             "the %s camera.", self.snapshot_job_info.camera.name)
            raise SnapshotError(
                'snapshot-save-error',
                "An unexpected exception occurred.",
                cause=e
            )

    def write_metadata(self):
        metadata_path = os.path.join(self.snapshot_job_info.snapshot_directory, SnapshotMetadata.METADATA_FILE_NAME)

        try:
            if not os.path.exists(self.snapshot_job_info.snapshot_directory):
                try:
                    os.makedirs(self.snapshot_job_info.snapshot_directory)
                except OSError as e:
                    if e.errno == errno.EEXIST:
                        pass
                    else:
                        raise

            with open(metadata_path, 'a') as metadata_file:
                dictwriter = DictWriter(metadata_file, SnapshotMetadata.METADATA_FIELDS)
                dictwriter.writerow({
                    'snapshot_number': "{}".format(self.snapshot_job_info.snapshot_number),
                    'file_name': self.snapshot_job_info.snapshot_file_name,
                    'time_taken': "{}".format(time()),
                    'layer': "{}".format(None if "layer" not in self.snapshot_job_info.metadata else self.snapshot_job_info.metadata["layer"]),
                    'height': "{}".format(None if "height" not in self.snapshot_job_info.metadata else self.snapshot_job_info.metadata["height"]),
                    'x': "{}".format(None if "x" not in self.snapshot_job_info.metadata else self.snapshot_job_info.metadata["x"]),
                    'y': "{}".format(None if "y" not in self.snapshot_job_info.metadata else self.snapshot_job_info.metadata["y"]),
                    'z': "{}".format(None if "z" not in self.snapshot_job_info.metadata else self.snapshot_job_info.metadata["z"]),
                    'e': "{}".format(None if "e" not in self.snapshot_job_info.metadata else self.snapshot_job_info.metadata["e"]),
                    'f': "{}".format(None if "f" not in self.snapshot_job_info.metadata else self.snapshot_job_info.metadata["f"]),
                    'x_snapshot': "{}".format(None if "x_snapshot" not in self.snapshot_job_info.metadata else self.snapshot_job_info.metadata["x_snapshot"]),
                    'y_snapshot': "{}".format(None if "y_snapshot" not in self.snapshot_job_info.metadata else self.snapshot_job_info.metadata["y_snapshot"]),
                })
        except Exception as e:
            logger.exception("An unexpected exception occurred while saving snapshot metadata for "
                             "the %s camera.", self.snapshot_job_info.camera.name)
            raise SnapshotError(
                'snapshot-metadata-error',
                "Snapshot Download - An unexpected exception occurred while writing snapshot metadata for the {0} "
                "camera.  Check the log file (plugin_octolapse.log) for details.".format(
                    self.snapshot_job_info.camera.name),
                cause=e
            )

    def transpose_image(self):
        try:
            transpose_setting = self.snapshot_job_info.camera.snapshot_transpose
            transpose_method = None
            snapshot_full_path = self.snapshot_job_info.snapshot_full_path

            if transpose_setting is not None and transpose_setting != "":
                if transpose_setting == 'flip_left_right':
                    transpose_method = Image.FLIP_LEFT_RIGHT
                elif transpose_setting == 'flip_top_bottom':
                    transpose_method = Image.FLIP_TOP_BOTTOM
                elif transpose_setting == 'rotate_90':
                    transpose_method = Image.ROTATE_90
                elif transpose_setting == 'rotate_180':
                    transpose_method = Image.ROTATE_180
                elif transpose_setting == 'rotate_270':
                    transpose_method = Image.ROTATE_270
                elif transpose_setting == 'transpose':
                    transpose_method = Image.TRANSPOSE

                if transpose_method is not None:
                    with Image.open(snapshot_full_path) as img:
                        img = img.transpose(transpose_method)
                        img.save(snapshot_full_path)
        except IOError as e:
            logger.exception("An unexpected exception occurred while transposing an image for "
                             "the %s camera.", self.snapshot_job_info.camera.name)
            raise SnapshotError(
                'snapshot-transpose-error',
                "Snapshot transpose - An unexpected IOException occurred while transposing the image for the {0} "
                "camera.  Check the log file (plugin_octolapse.log) for details.".format(
                    self.snapshot_job_info.camera.name),
                cause=e
            )

    def create_thumbnail(self):
        try:
            # without this I get errors during load (happens in resize, where the image is actually loaded)
            ImageFile.LOAD_TRUNCATED_IMAGES = True
            #######################################

            # create a copy to be used for the full sized latest snapshot image.
            latest_snapshot_path = utility.get_latest_snapshot_download_path(
                self.snapshot_job_info.temporary_directory, self.snapshot_job_info.camera.guid
            )

            utility.fast_copy(self.snapshot_job_info.snapshot_full_path, latest_snapshot_path)

            # create a thumbnail of the image
            basewidth = 500
            with Image.open(latest_snapshot_path) as img:
                wpercent = (basewidth / float(img.size[0]))
                hsize = int((float(img.size[1]) * float(wpercent)))
                img.thumbnail([basewidth, hsize], Image.LANCZOS)
                img.save(
                    utility.get_latest_snapshot_thumbnail_download_path(
                        self.snapshot_job_info.temporary_directory, self.snapshot_job_info.camera.guid
                    ),
                    "JPEG"
                )
        except Exception as e:
            logger.exception("An unexpected exception occurred while creating a snapshot thumbnail for "
                             "the %s camera.", self.snapshot_job_info.camera.name)
            # If we can't create the thumbnail, just log
            raise SnapshotError(
                'snapshot-thumbnail-create-error',
                "Create Thumbnail - An unexpected exception occurred while creating a snapshot thumbnail for the"
                " {0} camera.  Check the log file (plugin_octolapse.log) for details.".format(
                    self.snapshot_job_info.camera.name
                ),
                cause=e
            )


class SnapshotThread(Thread):
    def __init__(self, snapshot_job_info, on_new_thumbnail_available_callback=None,
                 on_post_processing_error_callback=None):
        super(SnapshotThread, self).__init__()
        self.snapshot_job_info = snapshot_job_info
        self.on_new_thumbnail_available_callback = on_new_thumbnail_available_callback
        self.on_post_processing_error_callback = on_post_processing_error_callback
        self.post_processing_error = None
        self.snapshot_thread_error = None

    def join(self, timeout=None):
        super(SnapshotThread, self).join(timeout=timeout)

        return self.snapshot_job_info

    def apply_camera_delay(self):
        # Some users had issues just using sleep.In one examined instance the time.sleep
        # function was being called to sleep 0.250 S, but waited 0.005 S.  To deal with this a sleep loop was
        # implemented that makes sure we've waited at least self.delay_seconds seconds before continuing.
        t0 = time()
        # record the number of sleep attempts for debug purposes
        sleep_tries = 0
        delay_seconds = self.snapshot_job_info.delay_seconds - (time() - t0)

        logger.info(
            "Snapshot Delay - Waiting %s second(s) after executing the snapshot script for the %s camera.",
            self.snapshot_job_info.delay_seconds, self.snapshot_job_info.camera.name
        )

        while delay_seconds >= 0.001:
            sleep_tries += 1  # increment the sleep try counter
            sleep(delay_seconds)  # sleep the calculated amount
            delay_seconds = self.snapshot_job_info.delay_seconds - (time() - t0)

    def post_process(self, request=None, block=False):
        # make sure the snapshot exists before attempting post-processing
        # since it's possible the image isn't on the pi.
        # for example it could be on a DSLR's SD memory
        try:
            def post_process_thread(post_processor):
                post_processor.process()
            image_post_processor = ImagePostProcessing(
                self.snapshot_job_info,
                on_new_thumbnail_available_callback=self.on_new_thumbnail_available_callback,
                on_post_processing_error_callback=self.on_post_processing_error_callback,
                request=request)
            if not block and not request:
                processing_thread = Thread(target=post_process_thread, args=[image_post_processor])
                processing_thread.daemon = True
                processing_thread.start()
            else:
                image_post_processor.process()
        except SnapshotError as e:
            logger.exception("An unexpected exception occurred while post processing an image for "
                             "the %s camera.", self.snapshot_job_info.camera.name)
            self.post_processing_error = e
        except Exception as e:
            message = "An unexpected exception occurred while post-processing images for the {0} camera." \
                      "  See plugin.octolapse.log for details".format(self.snapshot_job_info.camera.name)
            logger.exception(message)
            raise SnapshotError('post-processing-error', message, cause=e)
        finally:
            if request:
                request.close()


class ExternalScriptSnapshotJob(SnapshotThread):
    def __init__(self, snapshot_job_info, script_type, on_new_thumbnail_available_callback=None,
                 on_post_processing_error_callback=None):
        super(ExternalScriptSnapshotJob, self).__init__(
            snapshot_job_info,
            on_new_thumbnail_available_callback=on_new_thumbnail_available_callback,
            on_post_processing_error_callback=on_post_processing_error_callback
        )
        assert (isinstance(snapshot_job_info, SnapshotJobInfo))
        self.ScriptPath = None
        if script_type == 'before-snapshot':
            self.ScriptPath = snapshot_job_info.camera.on_before_snapshot_script
        elif script_type == 'snapshot':
            self.ScriptPath = snapshot_job_info.camera.external_camera_snapshot_script
        elif script_type == 'after-snapshot':
            self.ScriptPath = snapshot_job_info.camera.on_after_snapshot_script

        self.script_type = script_type

    def run(self):
        logger.info("Snapshot - running %s script for the %s camera.",
                    self.script_type, self.snapshot_job_info.camera.name)
        # execute the script and send the parameters
        if self.script_type == 'snapshot':
            if self.snapshot_job_info.delay_seconds < 0.001:
                logger.debug(
                    "Snapshot Delay - No pre snapshot delay configured for the %s camera.",
                    self.snapshot_job_info.camera.name)
            else:
                self.apply_camera_delay()
        try:
            self.execute_script()
        except SnapshotError as e:
            self.snapshot_thread_error = e.message
            return
        except Exception as e:
            message = "An unexpected exception occurred while processing the {0} script for the " \
                      "{1} camera.".format(self.script_type, self.snapshot_job_info.camera.name)
            logger.exception(message)
            self.snapshot_thread_error = message
            raise e
        finally:
            if self.script_type == 'snapshot':
                # perform post processing
                try:
                    self.post_process(block=self.on_new_thumbnail_available_callback is None)
                except SnapshotError as e:
                    self.post_processing_error = e
                except Exception as e:
                    message = "An unexpected error occurred during post processing for the {0} camera".format(
                        self.snapshot_job_info.camera.name)
                    logger.exception(message)
                    self.post_processing_error = SnapshotError(
                        'post-processing-error',
                        message,
                        cause=e
                    )
                    raise e

        logger.info("The %s script job completed, signaling task queue.", self.script_type)

    def execute_script(self):
        if self.script_type == "before-snapshot":
            cmd = script.CameraScriptBeforeSnapshot(
                self.ScriptPath,
                self.snapshot_job_info.camera.name,
                "{}".format(self.snapshot_job_info.snapshot_number),
                "{}".format(self.snapshot_job_info.delay_seconds),
                self.snapshot_job_info.temporary_directory,
                self.snapshot_job_info.snapshot_directory,
                self.snapshot_job_info.snapshot_file_name,
                self.snapshot_job_info.snapshot_full_path
            )
        elif self.script_type == "after-snapshot":
            cmd = script.CameraScriptAfterSnapshot(
                self.ScriptPath,
                self.snapshot_job_info.camera.name,
                "{}".format(self.snapshot_job_info.snapshot_number),
                "{}".format(self.snapshot_job_info.delay_seconds),
                self.snapshot_job_info.temporary_directory,
                self.snapshot_job_info.snapshot_directory,
                self.snapshot_job_info.snapshot_file_name,
                self.snapshot_job_info.snapshot_full_path
            )
        else:
            cmd = script.CameraScriptSnapshot(
                self.ScriptPath,
                self.snapshot_job_info.camera.name,
                "{}".format(self.snapshot_job_info.snapshot_number),
                "{}".format(self.snapshot_job_info.delay_seconds),
                self.snapshot_job_info.temporary_directory,
                self.snapshot_job_info.snapshot_directory,
                self.snapshot_job_info.snapshot_file_name,
                self.snapshot_job_info.snapshot_full_path
            )
        cmd.run()
        if not cmd.success():
            raise SnapshotError(
                '{0}_script_error'.format(self.script_type),
                cmd.error_message
            )


class WebcamSnapshotJob(SnapshotThread):

    def __init__(
        self,
        snapshot_job_info,
        download_started_event=None,
        on_new_thumbnail_available_callback=None,
        on_post_processing_error_callback=None
    ):
        super(WebcamSnapshotJob, self).__init__(
            snapshot_job_info,
            on_new_thumbnail_available_callback=on_new_thumbnail_available_callback,
            on_post_processing_error_callback=on_post_processing_error_callback
        )
        self.address = self.snapshot_job_info.camera.webcam_settings.address
        # Remove python 2 support
        # if isinstance(self.address, six.string_types):
        if isinstance(self.address, str):
            self.address = self.address.strip()
        self.username = self.snapshot_job_info.camera.webcam_settings.username
        self.password = self.snapshot_job_info.camera.webcam_settings.password
        self.ignore_ssl_error = self.snapshot_job_info.camera.webcam_settings.ignore_ssl_error
        url = camera.format_request_template(
            self.snapshot_job_info.camera.webcam_settings.address,
            self.snapshot_job_info.camera.webcam_settings.snapshot_request_template,
            ""
        )
        self.download_started_event = download_started_event
        if self.download_started_event:
            self.download_started_event.clear()
        self.url = url
        self.stream_download = self.snapshot_job_info.camera.webcam_settings.stream_download

    def run(self):

        if self.snapshot_job_info.delay_seconds < 0.001:
            logger.debug(
                "Snapshot Delay - No pre snapshot delay configured for the %s camera.",
                self.snapshot_job_info.camera.name)
        else:
            self.apply_camera_delay()

        r = None
        start_time = time()
        try:
            download_start_time = time()
            if len(self.username) > 0:
                logger.debug(
                    "Snapshot Download - Authenticating and downloading for the %s camera from %s.",
                    self.snapshot_job_info.camera.name,
                    self.url)

                r = requests.get(
                    self.url,
                    auth=HTTPBasicAuth(self.username, self.password),
                    verify=not self.ignore_ssl_error,
                    timeout=float(self.snapshot_job_info.timeout_seconds),
                    stream=self.stream_download
                )
            else:
                logger.debug(
                    "Snapshot - downloading for the %s camera from %s.",
                    self.snapshot_job_info.camera.name,
                    self.url)

                r = requests.get(
                    self.url,
                    verify=not self.ignore_ssl_error,
                    timeout=float(self.snapshot_job_info.timeout_seconds),
                    stream=self.stream_download
                )
            r.raise_for_status()
            if self.stream_download:
                logger.debug(
                    "Snapshot - received streaming response for the %s camera e in %.3f seconds.",
                    self.snapshot_job_info.camera.name,
                    time() - download_start_time)
            else:
                logger.debug(
                    "Snapshot - snapshot downloaded for the %s camera in %.3f seconds.",
                    self.snapshot_job_info.camera.name,
                    time() - download_start_time)
        except requests.ConnectionError as e:
            message = (
                "A connection error occurred while downloading a snapshot for the {0} camera."
                .format(self.snapshot_job_info.camera.name, self.snapshot_job_info.timeout_seconds)
            )
            logger.error(message)
            self.snapshot_thread_error = SnapshotError(
                'snapshot-download-error',
                message,
                cause=e
            )
        except (requests.ConnectTimeout, requests.ReadTimeout) as e:
            message = "An timeout occurred downloading a snapshot for the {0} camera in {1:.3f} seconds.".format(
                self.snapshot_job_info.camera.name, self.snapshot_job_info.timeout_seconds
            )
            logger.error(message)
            self.snapshot_thread_error = SnapshotError(
                'snapshot-download-error',
                message,
                cause=e
            )
        except Exception as e:
            message = "An error occurred downloading a snapshot for the {0} camera.".format(
                self.snapshot_job_info.camera.name
            )
            logger.exception(message)
            try:
                if r:
                    r.close()
            except Exception as c:
                logger.exception(
                    "Unable to close the snapshot download request for the %s camera.",
                    self.snapshot_job_info.camera.name)
            self.snapshot_thread_error = SnapshotError(
                'snapshot-download-error',
                message,
                cause=e
            )
            raise e
        finally:
            if self.download_started_event:
                self.download_started_event.set()
            # start post processing
            try:
                self.post_process(request=r, block=self.on_new_thumbnail_available_callback is None)
            except SnapshotError as e:
                self.post_processing_error = e
            except Exception as e:
                message = "An unexpected error occurred during post processing for the {0} camera".format(
                    self.snapshot_job_info.camera.name)
                logger.exception(message)
                self.post_processing_error = SnapshotError(
                    'post-processing-error',
                    message,
                    cause=e
                )
                raise e
            finally:
                logger.info("Snapshot Download Job completed for the %s camera in %.3f seconds.",
                            self.snapshot_job_info.camera.name,
                            time()-start_time)


class SnapshotError(Exception):
    def __init__(self, error_type, message, cause=None):
        super(SnapshotError, self).__init__()
        self.error_type = error_type
        self.cause = cause if cause is not None else None
        self.message = message

    def __str__(self):
        if self.cause is None:
            return "{}: {}".format(self.error_type, self.message)
        return "{}: {} - Inner Exception: {}".format(self.error_type, self.message, "{}".format(self.cause))


class SnapshotJobInfo(object):
    def __init__(self, timelapse_job_info, temporary_directory, snapshot_number, current_camera, job_type, metadata={}):
        self.camera = current_camera
        self.temporary_directory = temporary_directory
        self.snapshot_directory = utility.get_temporary_snapshot_job_camera_path(
            temporary_directory, timelapse_job_info.JobGuid, current_camera.guid
        )
        self.snapshot_file_name = utility.get_snapshot_filename(
            timelapse_job_info.PrintFileName, snapshot_number
        )
        self.snapshot_full_path = os.path.join(self.snapshot_directory, self.snapshot_file_name)
        self.snapshot_number = snapshot_number
        self.camera_guid = current_camera.guid
        self.success = False
        self.error = ""
        self.delay_seconds = current_camera.delay / 1000.0
        self.timeout_seconds = current_camera.timeout_ms / 1000.0
        self.snapshot_number = snapshot_number
        self.job_type = job_type
        self.metadata = metadata


class CameraInfo(object):
    camera_info_filename = "camera_info.json"

    @staticmethod
    def is_camera_info_file(file_name):
        return file_name.lower() == CameraInfo.camera_info_filename

    def __init__(self):
        self.snapshot_attempt = 0
        self.snapshot_count = 0
        self.errors_count = 0
        self.is_empty = False

    @staticmethod
    def load(data_folder, print_job_guid, camera_guid):
        file_path = os.path.join(
            utility.get_temporary_snapshot_job_camera_path(data_folder, print_job_guid, camera_guid),
            CameraInfo.camera_info_filename
        )
        try:
            with open(file_path, 'r') as camera_info:
                data = json.load(camera_info)
                return CameraInfo.from_dict(data)
        except (OSError, IOError, ValueError) as e:
            logger.exception("Unable to load camera info from %s.", file_path)
            ret_val = CameraInfo()
            ret_val.is_empty = True
            return ret_val

    def save(self, data_folder, print_job_guid, camera_guid):
        file_directory = utility.get_temporary_snapshot_job_camera_path(data_folder, print_job_guid, camera_guid)
        file_path = os.path.join(
            file_directory,
            CameraInfo.camera_info_filename
        )
        if not os.path.exists(file_directory):
            try:
                os.makedirs(file_directory)
            except OSError as e:
                if e.errno == errno.EEXIST:
                    pass
                else:
                    raise
        with open(file_path, 'w') as camera_info:
            json.dump(self.to_dict(), camera_info)

    def to_dict(self):
        return {
            "snapshot_attempt": self.snapshot_attempt,
            "snapshot_count": self.snapshot_count,
            "errors_count": self.errors_count,
        }

    @staticmethod
    def from_dict(dict_obj):
        camera_info = CameraInfo()
        camera_info.snapshot_attempt = dict_obj["snapshot_attempt"]
        camera_info.snapshot_attempt = dict_obj["snapshot_count"]
        camera_info.snapshot_attempt = dict_obj["errors_count"]
        return camera_info
