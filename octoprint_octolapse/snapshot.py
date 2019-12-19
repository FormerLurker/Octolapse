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
import shutil
import six
import os
from csv import DictWriter
from time import sleep
import requests
from PIL import ImageFile
import sys
# PIL is in fact in setup.py.
from requests.auth import HTTPBasicAuth
from threading import Thread, Event
from tempfile import mkdtemp
from uuid import uuid4
from time import time
from PIL import Image

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
    METADATA_FIELDS = ['snapshot_number', 'file_name', 'time_taken']


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
            snapshot_job = WebcamSnapshotJob(snapshot_job_info, settings)
        snapshot_job.daemon = True
        snapshot_job.start()
        snapshot_job.join()
        # Copy the image into memory so that we can delete the original file.
        with Image.open(snapshot_job_info.full_path) as image_file:
            return image_file.copy()
    finally:
        # Cleanup.
        shutil.rmtree(temp_snapshot_dir)


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
        self.DataDirectory = data_directory
        self.TimelapseJobInfo = utility.TimelapseJobInfo(timelapse_job_info)
        self.SnapshotsTotal = 0
        self.ErrorsTotal = 0
        self.SendGcodeArrayCallback = send_gcode_array_callback
        self.OnNewThumbnailAvailableCallback = on_new_thumbnail_available_callback
        self.on_post_processing_error_callback = on_post_processing_error_callback

    def take_snapshots(self):
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
                    self.TimelapseJobInfo, self.DataDirectory, camera_info.snapshot_attempt, current_camera, 'before-snapshot'
                )
                thread = ExternalScriptSnapshotJob(before_snapshot_job_info, 'before-snapshot')
                thread.daemon = True
                before_snapshot_threads.append(
                    thread
                )

            snapshot_job_info = SnapshotJobInfo(
                self.TimelapseJobInfo, self.DataDirectory, camera_info.snapshot_attempt, current_camera, 'snapshot'
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

            after_snapshot_job_info = SnapshotJobInfo(
                self.TimelapseJobInfo, self.DataDirectory, camera_info.snapshot_attempt, current_camera, 'after-snapshot'
            )
            # post_snapshot threads
            if current_camera.on_after_snapshot_script:
                thread = ExternalScriptSnapshotJob(after_snapshot_job_info, 'after-snapshot')
                thread.daemon = True
                after_snapshot_threads.append(
                    thread
                )

        if len(before_snapshot_threads) > 0:
            logger.info("Starting %d before snapshot threads", len(before_snapshot_threads))

        # start the pre-snapshot threads
        for t in before_snapshot_threads:
            t.start()

        # join the pre-snapshot threads
        for t in before_snapshot_threads:
            snapshot_job_info = t.join()
            assert (isinstance(snapshot_job_info, SnapshotJobInfo))
            if t.snapshot_thread_error:
                snapshot_job_info.success = False
                snapshot_job_info.error = t.snapshot_thread_error
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
                logger.info("Sending snapshot gcode array to %s.", current_camera.name)
                # just send the gcode now so it all goes in order
                self.SendGcodeArrayCallback(
                    Commands.string_to_gcode_array(current_camera.gcode_camera_script), current_camera.timeout_ms/1000.0
                )

        for t, snapshot_job_info, event in snapshot_threads:
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

            info = self.CameraInfos[snapshot_job_info.camera_guid]
            info.snapshot_attempt += 1
            if snapshot_job_info.success:
                info.snapshot_count += 1
                self.SnapshotsTotal += 1
            else:
                info.errors_count += 1
                self.ErrorsTotal += 1

            results.append(snapshot_job_info)

        if len(snapshot_threads) > 0:
            logger.info("Snapshot threads complete, but may be post-processing.")

        if len(after_snapshot_threads) > 0:
            logger.info("Starting %d after snapshot threads.", len(after_snapshot_threads))

        # start the after-snapshot threads
        for t in after_snapshot_threads:
            t.start()

        # join the after-snapshot threads
        for t in after_snapshot_threads:
            snapshot_job_info = t.join()
            assert (isinstance(snapshot_job_info, SnapshotJobInfo))
            info = self.CameraInfos[snapshot_job_info.camera_guid]
            if t.snapshot_thread_error:
                snapshot_job_info.success = False
                snapshot_job_info.error = t.snapshot_thread_error
            else:
                snapshot_job_info.success = True
            results.append(snapshot_job_info)

        if len(after_snapshot_threads) > 0:
            logger.info("After snapshot threads complete.")

        logger.info("Snapshot acquisition completed in %.3f seconds.", time()-start_time)

        return results

    def clean_snapshots(self, snapshot_directory, job_directory):
        # get snapshot directory
        logger.info("Cleaning snapshots from: %s", snapshot_directory)

        path = os.path.dirname(snapshot_directory + os.sep)
        job_path = os.path.dirname(job_directory + os.sep)
        if os.path.isdir(path):
            try:
                shutil.rmtree(path)
                logger.info("Snapshots cleaned.")
                if not os.listdir(job_path):
                    shutil.rmtree(job_path)
                    logger.info("The job directory was empty, removing.")
            except Exception:
                # Todo:  What exceptions do I catch here?
                exception_type = sys.exc_info()[0]
                value = sys.exc_info()[1]
                message = (
                    "Snapshot - Clean - Unable to clean the snapshot "
                    "path at {0}.  It may already have been cleaned.  "
                    "Info:  ExceptionType:{1}, Exception Value:{2}"
                ).format(path, exception_type, value)
                logger.info(message)
        else:
            logger.info("Snapshot - No need to clean snapshots: they have already been removed.")

    def clean_all_snapshots(self):
        #TODO:  FIX THIS.  IT NEEDS TO REMOVE ALL SUBDIRECTORIES IN THE SNAPSHOT FOLDER.
        # get snapshot directory
        snapshot_directory = utility.get_snapshot_temp_directory(
            self.DataDirectory)
        logger.info("Cleaning snapshots from: %s", snapshot_directory)

        path = os.path.dirname(snapshot_directory + os.sep)
        if os.path.isdir(path):
            try:
                shutil.rmtree(path)
                logger.info("Snapshots cleaned.")
            except:
                # Todo:  What exceptions to catch here?
                exception_type = sys.exc_info()[0]
                value = sys.exc_info()[1]
                message = (
                    "Snapshot - Clean - Unable to clean the snapshot "
                    "path at {0}.  It may already have been cleaned.  "
                    "Info:  ExceptionType:{1}, Exception Value:{2}"
                ).format(path, exception_type, value)
                logger.info(message)
        else:
            logger.info("Snapshot - No need to clean snapshots: they have already been removed.")


class ImagePostProcessing(object):
    def __init__(self, snapshot_job_info, on_new_thumbnail_available_callback=None,
                 on_post_processing_error_callback=None, request=None):
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
            if os.path.isfile(self.snapshot_job_info.full_path):
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
            if not os.path.exists(self.snapshot_job_info.directory):
                os.makedirs(self.snapshot_job_info.directory)
            with open(self.snapshot_job_info.full_path, 'wb+') as snapshot_file:
                for chunk in self.request.iter_content(chunk_size=512 * 1024):
                    if chunk:
                        snapshot_file.write(chunk)

                logger.debug("Snapshot - Snapshot saved to disk for the %s camera at %s",
                             self.snapshot_job_info.camera.name, self.snapshot_job_info.full_path)
        except Exception as e:
            logger.exception("An unexpected exception occurred while saving a snapshot from a request for "
                             "the %s camera.", self.snapshot_job_info.camera.name)
            raise SnapshotError(
                'snapshot-save-error',
                "An unexpected exception occurred.",
                cause=e
            )

    def write_metadata(self):
        metadata_path = os.path.join(self.snapshot_job_info.directory, SnapshotMetadata.METADATA_FILE_NAME)

        try:
            if not os.path.exists(self.snapshot_job_info.directory):
                os.makedirs(self.snapshot_job_info.directory)

            with open(metadata_path, 'a') as metadata_file:
                dictwriter = DictWriter(metadata_file, SnapshotMetadata.METADATA_FIELDS)
                dictwriter.writerow({
                    'snapshot_number': "{}".format(self.snapshot_job_info.snapshot_number),
                    'file_name': self.snapshot_job_info.file_name,
                    'time_taken': "{}".format(time()),
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
            snapshot_full_path = self.snapshot_job_info.full_path

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
                self.snapshot_job_info.DataDirectory, self.snapshot_job_info.camera.guid
            )
            shutil.copy(self.snapshot_job_info.full_path, latest_snapshot_path)

            # create a thumbnail of the image
            basewidth = 500
            with Image.open(latest_snapshot_path) as img:
                wpercent = (basewidth / float(img.size[0]))
                hsize = int((float(img.size[1]) * float(wpercent)))
                img.thumbnail([basewidth, hsize], Image.ANTIALIAS)
                img.save(
                    utility.get_latest_snapshot_thumbnail_download_path(
                        self.snapshot_job_info.DataDirectory, self.snapshot_job_info.camera.guid
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
        # implemented that makes sure we've waited at least self.DelaySeconds seconds before continuing.
        t0 = time()
        # record the number of sleep attempts for debug purposes
        sleep_tries = 0
        delay_seconds = self.snapshot_job_info.DelaySeconds - (time() - t0)

        logger.info(
            "Snapshot Delay - Waiting %s second(s) after executing the snapshot script for the %s camera.",
            self.snapshot_job_info.DelaySeconds, self.snapshot_job_info.camera.name
        )

        while delay_seconds >= 0.001:
            sleep_tries += 1  # increment the sleep try counter
            sleep(delay_seconds)  # sleep the calculated amount
            delay_seconds = self.snapshot_job_info.DelaySeconds - (time() - t0)

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
        if self.ScriptPath is None or len(self.ScriptPath) == 0:
            self.snapshot_thread_error = "No script path was provided.  Please enter a script " \
                                         "path and try again.".format(self.ScriptPath)
            return
        if not os.path.exists(self.ScriptPath):
            self.snapshot_thread_error = "The provided script path ({0}) does not exist.  Please check your script " \
                                         "path and try again.".format(self.ScriptPath)
            return
        # execute the script and send the parameters
        if self.script_type == 'snapshot':
            if self.snapshot_job_info.DelaySeconds < 0.001:
                logger.debug(
                    "Snapshot Delay - No pre snapshot delay configured for the %s camera.",
                    self.snapshot_job_info.camera.name)
            else:
                self.apply_camera_delay()
        try:
            self.execute_script()
        except SnapshotError as e:
            self.snapshot_thread_error = str(e)
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
                "{}".format(self.snapshot_job_info.SnapshotNumber),
                "{}".format(self.snapshot_job_info.DelaySeconds),
                self.snapshot_job_info.DataDirectory,
                self.snapshot_job_info.directory,
                self.snapshot_job_info.file_name,
                self.snapshot_job_info.full_path
            )
        elif self.script_type == "after-snapshot":
            cmd = script.CameraScriptAfterSnapshot(
                self.ScriptPath,
                self.snapshot_job_info.camera.name,
                "{}".format(self.snapshot_job_info.SnapshotNumber),
                "{}".format(self.snapshot_job_info.DelaySeconds),
                self.snapshot_job_info.DataDirectory,
                self.snapshot_job_info.directory,
                self.snapshot_job_info.file_name,
                self.snapshot_job_info.full_path
            )
        else:
            cmd = script.CameraScriptSnapshot(
                self.ScriptPath,
                self.snapshot_job_info.camera.name,
                "{}".format(self.snapshot_job_info.SnapshotNumber),
                "{}".format(self.snapshot_job_info.DelaySeconds),
                self.snapshot_job_info.DataDirectory,
                self.snapshot_job_info.directory,
                self.snapshot_job_info.file_name,
                self.snapshot_job_info.full_path
            )
        cmd.run()
        if not cmd.success():
            raise SnapshotError(
                '{0}_script_error'.format(self.script_type),
                "The snapshot script returned an error.  Check plugin_octolapse.log for details."
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
        self.Address = self.snapshot_job_info.camera.webcam_settings.address
        if isinstance(self.Address, six.string_types):
            self.Address = self.Address.strip()
        self.Username = self.snapshot_job_info.camera.webcam_settings.username
        self.Password = self.snapshot_job_info.camera.webcam_settings.password
        self.IgnoreSslError = self.snapshot_job_info.camera.webcam_settings.ignore_ssl_error
        url = camera.format_request_template(
            self.snapshot_job_info.camera.webcam_settings.address,
            self.snapshot_job_info.camera.webcam_settings.snapshot_request_template,
            ""
        )
        self.download_started_event = download_started_event
        if self.download_started_event:
            self.download_started_event.clear()
        self.Url = url
        self.stream_download = self.snapshot_job_info.camera.webcam_settings.stream_download

    def run(self):

        if self.snapshot_job_info.DelaySeconds < 0.001:
            logger.debug(
                "Snapshot Delay - No pre snapshot delay configured for the %s camera.",
                self.snapshot_job_info.camera.name)
        else:
            self.apply_camera_delay()

        r = None
        start_time = time()
        try:
            download_start_time = time()
            if len(self.Username) > 0:
                logger.debug(
                    "Snapshot Download - Authenticating and downloading for the %s camera from %s.",
                    self.snapshot_job_info.camera.name,
                    self.Url)

                r = requests.get(
                    self.Url,
                    auth=HTTPBasicAuth(self.Username, self.Password),
                    verify=not self.IgnoreSslError,
                    timeout=float(self.snapshot_job_info.TimeoutSeconds),
                    stream=self.stream_download
                )
            else:
                logger.debug(
                    "Snapshot - downloading for the %s camera from %s.",
                    self.snapshot_job_info.camera.name,
                    self.Url)

                r = requests.get(
                    self.Url,
                    verify=not self.IgnoreSslError,
                    timeout=float(self.snapshot_job_info.TimeoutSeconds),
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
                .format(self.snapshot_job_info.camera.name, self.snapshot_job_info.TimeoutSeconds)
            )
            logger.error(message)
            self.snapshot_thread_error = SnapshotError(
                'snapshot-download-error',
                message,
                cause=e
            )
        except (requests.ConnectTimeout, requests.ReadTimeout) as e:
            message = "An timeout occurred downloading a snapshot for the {0} camera in {1:.3f} seconds.".format(
                self.snapshot_job_info.camera.name, self.snapshot_job_info.TimeoutSeconds
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
    def __init__(self, timelapse_job_info, data_directory, snapshot_number, current_camera, job_type):
        self.camera = current_camera
        self.directory = os.path.join(data_directory, "snapshots", timelapse_job_info.JobGuid, current_camera.guid)
        self.file_name = utility.get_snapshot_filename(
            timelapse_job_info.PrintFileName, timelapse_job_info.PrintStartTime, snapshot_number
        )
        self.snapshot_number = snapshot_number
        self.camera_guid = current_camera.guid
        self.success = False
        self.error = ""
        self.DelaySeconds = current_camera.delay / 1000.0
        self.TimeoutSeconds = current_camera.timeout_ms / 1000.0
        self.SnapshotNumber = snapshot_number
        self.DataDirectory = data_directory
        self.SnapshotTranspose = current_camera.snapshot_transpose
        self.job_type = job_type

    @property
    def full_path(self):
        return os.path.join(self.directory, self.file_name)


class CameraInfo(object):
    def __init__(self):
        self.snapshot_attempt = 0
        self.snapshot_count = 0
        self.errors_count = 0
