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
from subprocess import CalledProcessError
import os as os
import shutil
import six
import os
from csv import DictWriter
from io import open as i_open
from time import sleep
import requests
from PIL import ImageFile
import sys
# PIL is in fact in setup.py.
from requests.auth import HTTPBasicAuth
from threading import Thread, Timer, Event
from tempfile import mkdtemp
from uuid import uuid4
from time import time
from PIL import Image

# create the module level logger
import octoprint_octolapse.camera as camera
import octoprint_octolapse.utility as utility
from octoprint_octolapse.gcode_parser import Commands
from octoprint_octolapse.utility import TimelapseJobInfo
from octoprint_octolapse.log import LoggingConfigurator
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
            TimelapseJobInfo(job_guid=uuid4(), print_start_time=time(), print_file_name='overlay_preview'),
            temp_snapshot_dir, 0, current_camera)
        if current_camera.camera_type == "external-script":
            snapshot_job = ExternalScriptSnapshotJob(snapshot_job_info, settings)
        else:
            snapshot_job = WebcamSnapshotJob(snapshot_job_info, settings)
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
                 , on_new_thumbnail_available_callback):
        self.Settings = settings
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
                    self.TimelapseJobInfo, self.DataDirectory, camera_info.snapshot_count, current_camera
                )
                before_snapshot_threads.append(
                    ExternalScriptSnapshotJob(before_snapshot_job_info, self.Settings, 'before-snapshot')
                )

            snapshot_job_info = SnapshotJobInfo(
                self.TimelapseJobInfo, self.DataDirectory, camera_info.snapshot_count, current_camera
            )
            if current_camera.camera_type == "external-script":
                thread = ExternalScriptSnapshotJob(
                    snapshot_job_info,
                    self.Settings,
                    'snapshot',
                    on_new_thumbnail_available_callback=self.OnNewThumbnailAvailableCallback
                )
                snapshot_threads.append((thread, snapshot_job_info, None))
            elif current_camera.camera_type == "webcam":
                download_started_event = Event()
                thread = WebcamSnapshotJob(
                    snapshot_job_info,
                    self.Settings,
                    download_started_event=download_started_event,
                    on_new_thumbnail_available_callback=self.OnNewThumbnailAvailableCallback
                )
                snapshot_threads.append((thread, snapshot_job_info, download_started_event))

            after_snapshot_job_info = SnapshotJobInfo(
                self.TimelapseJobInfo, self.DataDirectory, camera_info.snapshot_count, current_camera
            )
            # post_snapshot threads
            if current_camera.on_after_snapshot_script:
                after_snapshot_threads.append(
                    ExternalScriptSnapshotJob(after_snapshot_job_info, self.Settings, 'after-snapshot')
                )

        if len(before_snapshot_threads) > 0:
            logger.info("Starting %d before snapshot threads", len(before_snapshot_threads))

        # start the pre-snapshot threads
        for t in before_snapshot_threads:
            t.start()

        # join the pre-snapshot threads
        for t in before_snapshot_threads:
            result = t.join()
            assert (isinstance(result, SnapshotJobInfo))
            info = self.CameraInfos[result.camera_guid]
            if not result.success:
                info.errors_count += 1
                self.ErrorsTotal += 1
            results.append(result)

        if len(before_snapshot_threads) > 0:
            logger.info("Before snapshot threads finished.")

        if len(snapshot_threads) > 0:
            logger.info("Starting %d snapshot threads.", len(snapshot_threads))
        # start the snapshot threads, then wait for all threads to signal before continuing
        for t in snapshot_threads:
            t[0].start()

        # now send any gcode for gcode cameras
        for current_camera in self.Cameras:
            if current_camera.camera_type == "printer-gcode":
                logger.info("Sending snapshot gcode array to %s.", current_camera.name)
                # just send the gcode now so it all goes in order
                self.SendGcodeArrayCallback(
                    Commands.string_to_gcode_array(current_camera.gcode_camera_script), current_camera.timeout_ms/1000.0
                )

        for t, snapshot_job_info, event in snapshot_threads:
            if event:
                event.wait()
                if t.download_error:
                    snapshot_job_info.success = False
                    snapshot_job_info.error = t.download_error
                else:
                    snapshot_job_info.success = True
            else:
                snapshot_job_info = t.join()
            info = self.CameraInfos[snapshot_job_info.camera_guid]
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
            result = t.join()
            assert (isinstance(result, SnapshotJobInfo))
            info = self.CameraInfos[result.camera_guid]
            if not result.success:
                info.errors_count += 1
                self.ErrorsTotal += 1
            results.append(result)

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
    def __init__(self, snapshot_job_info, on_new_thumbnail_available_callback=None, request=None):
        self.snapshot_job_info = snapshot_job_info
        self.on_new_thumbnail_available_callback = on_new_thumbnail_available_callback
        self.request = request

    def process(self):
        try:
            logger.debug("Post-processing snapshot for %s.", self.snapshot_job_info.camera.name)
            if self.request is not None:
                self.save_image_from_request()
                self.request.close()
            # Post Processing and Meta Data Creation
            self.write_metadata()
            self.transpose_image()
            self.create_thumbnail()
            if self.on_new_thumbnail_available_callback is not None:
                self.on_new_thumbnail_available_callback(self.snapshot_job_info.camera.guid)
        finally:
            logger.debug("Post-processing snapshot for %s complete.", self.snapshot_job_info.camera.name)

    def save_image_from_request(self):
        try:
            if not os.path.exists(self.snapshot_job_info.directory):
                os.makedirs(self.snapshot_job_info.directory)
            with open(self.snapshot_job_info.full_path, 'wb+') as snapshot_file:
                for chunk in self.request.iter_content(chunk_size=512 * 1024):
                    if chunk:
                        snapshot_file.write(chunk)

                logger.debug("Snapshot - Snapshot saved to disk at %s", self.snapshot_job_info.full_path)
        except Exception as e:
            raise SnapshotError(
                'snapshot-save-error',
                "An unexpected exception occurred.",
                cause=e
            )

    def write_metadata(self):
        try:
            with open(os.path.join(self.snapshot_job_info.directory, SnapshotMetadata.METADATA_FILE_NAME), 'a') as metadata_file:
                dictwriter = DictWriter(metadata_file, SnapshotMetadata.METADATA_FIELDS)
                dictwriter.writerow({
                    'snapshot_number': "{}".format(self.snapshot_job_info.snapshot_number),
                    'file_name': self.snapshot_job_info.file_name,
                    'time_taken': "{}".format(time()),
                })
        except Exception as e:
            raise SnapshotError(
                'snapshot-metadata-error',
                "Snapshot Download - An unexpected exception occurred while writing snapshot metadata.  "
                "Check the log file (plugin_octolapse.log) for details.",
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
                    im = Image.open(snapshot_full_path)
                    im = im.transpose(transpose_method)
                    im.save(snapshot_full_path)
        except IOError as e:
            raise SnapshotError(
                'snapshot-transpose-error',
                "Snapshot transpose - An unexpected IOException occurred while transposing the image.  "
                "Check the log file (plugin_octolapse.log) for details.",
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
            img = Image.open(latest_snapshot_path)
            wpercent = (basewidth / float(img.size[0]))
            hsize = int((float(img.size[1]) * float(wpercent)))
            img.thumbnail([basewidth, hsize], Image.ANTIALIAS)
            img.save(
                utility.get_latest_snapshot_thumbnail_download_path(
                    self.snapshot_job_info.DataDirectory, self.snapshot_job_info.camera.guid
                ),
                "JPEG"
            )

            #img = img.resize((basewidth, hsize), Image.ANTIALIAS)
            #img.save(utility.get_latest_snapshot_thumbnail_download_path(
            #    self.snapshot_job_info.DataDirectory, self.snapshot_job_info.camera.guid), "JPEG"
            #)
        except Exception as e:

            # If we can't create the thumbnail, just log
            raise SnapshotError(
                'snapshot-thumbnail-create-error',
                "Create Thumbnail - An unexpected exception occurred while creating a snapshot thumbnail.  "
                "Check the log file (plugin_octolapse.log) for details.",
                cause=e
            )


class SnapshotThread(Thread):
    def __init__(self, snapshot_job_info, settings, on_new_thumbnail_available_callback=None):
        super(SnapshotThread, self).__init__()
        self.snapshot_job_info = snapshot_job_info
        self.Settings = settings
        self.on_new_thumbnail_available_callback = on_new_thumbnail_available_callback
        self.post_processing_errors = None
        self.download_error = None

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
            "Snapshot Delay - Waiting %s second(s) after executing the snapshot script.",
            self.snapshot_job_info.DelaySeconds
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
            if request is not None or os.path.isfile(self.snapshot_job_info.full_path):
                def post_process(post_processor):
                    post_processor.process()
                image_post_processor = ImagePostProcessing(self.snapshot_job_info, self.on_new_thumbnail_available_callback, request=request)
                if not block and not request:
                    processing_thread = Thread(target=post_process, args=[image_post_processor])
                    processing_thread.start()
                else:
                    image_post_processor.process()
        except SnapshotError as e:
            self.post_processing_errors = e
        except Exception as e:
            logger.exception(e)
            message = "An unexpected exception occurred while post-processing images.  See plugin.octolapse.log for details"
            raise SnapshotError('post-processing-error', message, cause=e)
        finally:
            if request:
                request.close()


class ExternalScriptSnapshotJob(SnapshotThread):
    def __init__(self, snapshot_job_info, settings, script_type, on_new_thumbnail_available_callback=None):
        super(ExternalScriptSnapshotJob, self).__init__(
            snapshot_job_info,
            settings,
            on_new_thumbnail_available_callback=on_new_thumbnail_available_callback
        )
        assert (isinstance(snapshot_job_info, SnapshotJobInfo))
        if script_type == 'before-snapshot':
            self.ScriptPath = snapshot_job_info.camera.on_before_snapshot_script
        elif script_type == 'snapshot':
            self.ScriptPath = snapshot_job_info.camera.external_camera_snapshot_script
        elif script_type == 'after-snapshot':
            self.ScriptPath = snapshot_job_info.camera.on_after_snapshot_script

        self.script_type = script_type

    def run(self):
        try:
            logger.info("Snapshot - running %s script.", self.script_type)
            # execute the script and send the parameters
            if self.script_type == 'snapshot':
                if self.snapshot_job_info.DelaySeconds < 0.001:
                    logger.info("Snapshot Delay - No pre snapshot delay configured.")
                else:
                    self.apply_camera_delay()

            self.execute_script()

            if self.script_type == 'snapshot':
                # Make sure the expected snapshot exists before we start working with the snapshot file.
                self.post_process(block=self.on_new_thumbnail_available_callback is None)

            self.snapshot_job_info.success = True

        except SnapshotError as e:
            self.snapshot_job_info.error = "{}".format(e)
        finally:
            logger.info("The %s script job completed, signaling task queue.", self.script_type)

    def execute_script(self):
        logger.info(
            "Running the following %s script command with a timeout of %s: %s %s %s %s %s %s %s",
            self.script_type,
            self.snapshot_job_info.TimeoutSeconds,
            self.ScriptPath,
            "{}".format(self.snapshot_job_info.SnapshotNumber),
            "{}".format(self.snapshot_job_info.DelaySeconds),
            self.snapshot_job_info.DataDirectory,
            self.snapshot_job_info.directory,
            self.snapshot_job_info.file_name,
            self.snapshot_job_info.full_path
        )
        script_args = [
            self.ScriptPath,
            "{}".format(self.snapshot_job_info.SnapshotNumber),
            "{}".format(self.snapshot_job_info.DelaySeconds),
            self.snapshot_job_info.DataDirectory,
            self.snapshot_job_info.directory,
            self.snapshot_job_info.file_name,
            self.snapshot_job_info.full_path
        ]

        try:
            cmd = utility.POpenWithTimeout()
            return_code = cmd.run(script_args, self.snapshot_job_info.TimeoutSeconds)
            console_output = cmd.stdout
            error_message = cmd.stderr
        except utility.POpenWithTimeout.ProcessError as e:
            raise SnapshotError(
                '{0}_script_error'.format(self.script_type),
                "An OS Error error occurred while executing the {0} script".format(self.script_type),
                cause=e
            )

        if error_message and error_message.endswith("\r\n"):
            error_message = error_message[:-2]

        if not return_code == 0:
            if error_message:
                error_message = "The {0} script failed with the following error message: {1}"\
                    .format(self.script_type, error_message)
            else:
                error_message = (
                    "The {0} script returned {1},"
                    " which indicates an error.".format(self.script_type, return_code)
                )
            raise SnapshotError('{0}_script_error'.format(self.script_type), error_message)
        elif error_message:
            logger.error(
                "Error output was returned from the %s script: %s",
                self.script_type,
                error_message
            )


class WebcamSnapshotJob(SnapshotThread):

    def __init__(self, snapshot_job_info, settings, download_started_event=None, on_new_thumbnail_available_callback=None):
        super(WebcamSnapshotJob, self).__init__(
            snapshot_job_info,
            settings,
            on_new_thumbnail_available_callback=on_new_thumbnail_available_callback
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

    def run(self):
        try:
            if self.snapshot_job_info.DelaySeconds < 0.001:
                logger.debug("Starting Snapshot Download Job Immediately.")
            else:
                # Pre-Snapshot Delay
                self.apply_camera_delay()
        except Exception as e:
            logger.exception(e)
            message="An error occurred while applying the snapshot delay.  See plugin.octolapse.log for details."
            self.download_error = SnapshotError("snapshot-delay-error", message, e)
            if self.download_started_event:
                self.download_started_event.set()
            return

        r = None
        start_time = time()
        try:
            download_start_time = time()
            if len(self.Username) > 0:
                logger.debug("Snapshot Download - Authenticating and downloading from %s.", self.Url)

                r = requests.get(
                    self.Url,
                    auth=HTTPBasicAuth(self.Username, self.Password),
                    verify=not self.IgnoreSslError,
                    timeout=float(self.snapshot_job_info.TimeoutSeconds),
                    stream=True
                )
            else:
                logger.debug("Snapshot - downloading from %s.", self.Url)

                r = requests.get(
                    self.Url,
                    verify=not self.IgnoreSslError,
                    #timeout=float(self.snapshot_job_info.TimeoutSeconds),
                    timeout=float(self.snapshot_job_info.TimeoutSeconds),
                    stream=True
                )
            r.raise_for_status()
            logger.debug("Snapshot - downloaded started in %.3f seconds.", time() - download_start_time)
        except Exception as e:
            message = "An error occurred downloading a snapshot for the {0} camera.".format(
                self.snapshot_job_info.camera.name
            )
            try:
                if r:
                    r.close()
            except Exception as c:
                logger.exception(c)
            self.download_error = SnapshotError(
                'snapshot-download-error',
                message,
                cause=e
            )
            return
        finally:
            if self.download_started_event:
                self.download_started_event.set()

        # start post processing
        try:
            self.post_process(request=r, block=self.on_new_thumbnail_available_callback is None)
            self.snapshot_job_info.success = True
        finally:
            logger.info("Snapshot Download Job completed in %.3f seconds.", time()-start_time)


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
    def __init__(self, timelapse_job_info, data_directory, snapshot_number, current_camera):
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

    @property
    def full_path(self):
        return os.path.join(self.directory, self.file_name)


class CameraInfo(object):
    def __init__(self):
        self.snapshot_count = 0
        self.errors_count = 0
