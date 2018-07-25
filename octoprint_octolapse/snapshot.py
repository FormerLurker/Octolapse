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

import os
import shutil
from csv import DictWriter
from io import open as i_open
from subprocess import Popen, CalledProcessError, PIPE
from time import sleep, time
from threading import Thread
import requests
from PIL import Image
from PIL import ImageFile
# PIL is in fact in setup.py.
from requests.auth import HTTPBasicAuth

import octoprint_octolapse.camera as camera
from octoprint_octolapse.settings import *

METADATA_FILE_NAME = 'metadata.csv'
METADATA_FIELDS = ['snapshot_number', 'file_name', 'time_taken']


class CaptureSnapshot(object):

    def __init__(self, settings, data_directory, print_start_time, print_end_time=None):
        self.Settings = settings
        self.Printer = self.Settings.current_printer()
        self.Snapshot = self.Settings.current_snapshot()
        self.Camera = self.Settings.current_camera()
        self.PrintStartTime = print_start_time
        self.PrintEndTime = print_end_time
        self.DataDirectory = data_directory
        self.SnapshotTimeout = 5

    def create_snapshot_job(self, printer_file_name, snapshot_number, on_complete, on_success, on_fail):
        info = SnapshotInfo(printer_file_name, self.PrintStartTime)
        info.DirectoryName = utility.get_snapshot_temp_directory(
            self.DataDirectory)
        url = camera.format_request_template(
            self.Camera.address, self.Camera.snapshot_request_template, "")
        # TODO:  TURN THE SNAPSHOT REQUIRE TIMEOUT INTO A SETTING
        new_snapshot_job = SnapshotJob(
            self.Settings, self.DataDirectory, snapshot_number, info, url,
            self.Camera.delay, self.SnapshotTimeout, on_complete=on_complete,
            on_success=on_success, on_fail=on_fail
        )

        return new_snapshot_job.process

    def create_snapshot_script_job(
        self, script_type, script_path, printer_file_name, snapshot_number, on_complete=None, on_success=None, on_fail=None
    ):
        info = SnapshotInfo(printer_file_name, self.PrintStartTime)
        info.DirectoryName = utility.get_snapshot_temp_directory(
            self.DataDirectory)
        url = camera.format_request_template(
            self.Camera.address, self.Camera.snapshot_request_template, "")
        # TODO:  TURN THE SNAPSHOT REQUIRE TIMEOUT INTO A SETTING
        new_snapshot_job = ExternalScriptCameraJob(
            script_type, script_path, self.Settings, self.DataDirectory, snapshot_number, info,
            self.Camera.delay, self.SnapshotTimeout, on_complete=on_complete,
            on_success=on_success, on_fail=on_fail
        )

        return new_snapshot_job.process

    def clean_snapshots(self, snapshot_directory):

        # get snapshot directory
        self.Settings.current_debug_profile().log_snapshot_clean(
            "Cleaning snapshots from: {0}".format(snapshot_directory))

        path = os.path.dirname(snapshot_directory + os.sep)
        if os.path.isdir(path):
            try:
                shutil.rmtree(path)
                self.Settings.current_debug_profile().log_snapshot_clean("Snapshots cleaned.")
            except Exception:
                # Todo:  What exceptions do I catch here?
                exception_type = sys.exc_info()[0]
                value = sys.exc_info()[1]
                message = (
                    "Snapshot - Clean - Unable to clean the snapshot "
                    "path at {0}.  It may already have been cleaned.  "
                    "Info:  ExceptionType:{1}, Exception Value:{2}"
                ).format(path, exception_type, value)
                self.Settings.current_debug_profile().log_snapshot_clean(message)
        else:
            self.Settings.current_debug_profile().log_snapshot_clean(
                "Snapshot - No need to clean snapshots: they have already been removed."
            )

    def clean_all_snapshots(self):

        # get snapshot directory
        snapshot_directory = utility.get_snapshot_temp_directory(
            self.DataDirectory)
        self.Settings.current_debug_profile().log_snapshot_clean(
            "Cleaning snapshots from: {0}".format(snapshot_directory))

        path = os.path.dirname(snapshot_directory + os.sep)
        if os.path.isdir(path):
            try:
                shutil.rmtree(path)
                self.Settings.current_debug_profile().log_snapshot_clean("Snapshots cleaned.")
            except:
                # Todo:  What exceptions to catch here?
                exception_type = sys.exc_info()[0]
                value = sys.exc_info()[1]
                message = (
                    "Snapshot - Clean - Unable to clean the snapshot "
                    "path at {0}.  It may already have been cleaned.  "
                    "Info:  ExceptionType:{1}, Exception Value:{2}"
                ).format(path, exception_type, value)
                self.Settings.current_debug_profile().log_snapshot_clean(message)
        else:
            self.Settings.current_debug_profile().log_snapshot_clean(
                "Snapshot - No need to clean snapshots: they have already been removed."
            )


class ExternalScriptCameraJob(object):

    def __init__(
        self, script_type, script_path, settings, data_directory, snapshot_number,
        snapshot_info, delay_ms, timeout_seconds, on_complete, on_success, on_fail
    ):

        self.ScriptType = script_type
        self.ScriptPath = script_path
        self.DelaySeconds = delay_ms / 1000.0
        camera_settings = settings.current_camera()
        self.SnapshotNumber = snapshot_number
        self.DataDirectory = data_directory
        self.Address = camera_settings.address
        self.Username = camera_settings.username
        self.Password = camera_settings.password
        self.IgnoreSslError = camera_settings.ignore_ssl_error
        self.SnapshotTranspose = camera_settings.snapshot_transpose
        self.Settings = settings
        self.SnapshotInfo = snapshot_info
        self.TimeoutSeconds = timeout_seconds
        self.OnCompleteCallback = on_complete
        self.OnSuccessCallback = on_success
        self.OnFailCallback = on_fail
        self.HasError = False
        self.ErrorMessage = ""
        self.ErrorType = ""

    def on_success(self):
        if self.OnSuccessCallback is not None:
            self.OnSuccessCallback()

    def on_fail(self):
        if self.OnFailCallback is not None:
            self.OnFailCallback(self.ErrorMessage)

    def on_complete(self):
        if self.OnCompleteCallback is not None:
            self.OnCompleteCallback()

    def process(self):
        # execute the script and send the parameters
        self.HasError = False
        self.ErrorMessage = "unknown"

        self.Settings.current_debug_profile().log_snapshot_download(
            "Snapshot - running external {0} script.".format(self.ScriptType))
        self.execute_script()

        if not self.HasError and self.ScriptType == "snapshot":
            # process any delay after the script has executed if this is a snapshot script.
            if self.DelaySeconds < 0.001:
                self.Settings.current_debug_profile().log_snapshot_download(
                    "Snapshot Delay - No post snapshot delay configured.")
            else:
                # start the post script delay
                # record the time we started sleeping
                t0 = time()
                # record the number of sleep attempts for debug purposes
                sleep_tries = 0
                delay_seconds = self.DelaySeconds - (time() - t0)

                self.Settings.current_debug_profile().log_snapshot_download(
                    "Snapshot Delay - Waiting {0} second(s) after executing the snapshot script."
                        .format(self.DelaySeconds))

                while delay_seconds >= 0.001:
                    sleep_tries += 1  # increment the sleep try counter

                    sleep(delay_seconds)  # sleep the calculated amount

                    delay_seconds = self.DelaySeconds - (time() - t0)

        # go ahead and report success or fail for the timelapse routine
        if not self.HasError:
            self.on_success()
        else:
            self.on_fail()
        self.on_complete()

        self.Settings.current_debug_profile().log_snapshot_download(
            "Snapshot {0} script Job completed, signaling task queue.".format(self.ScriptType))

    def execute_script(self):
        try:
            download_full_path = self.SnapshotInfo.get_full_path(self.SnapshotNumber)
            download_directory, download_filename = os.path.split(download_full_path)

            self.Settings.current_debug_profile().log_info(
                "Running the following snapshot script command: " +
                " {0} {1} {2} {3} {4} {5} {6}"
                .format(
                    self.ScriptPath,
                    str(self.SnapshotNumber),
                    str(self.DelaySeconds),
                    self.DataDirectory,
                    download_directory,
                    download_filename,
                    download_full_path
                )
            )
            script_args = [
                self.ScriptPath,
                str(self.SnapshotNumber),
                str(self.DelaySeconds),
                self.DataDirectory,
                download_directory,
                download_filename,
                download_full_path
            ]

            (return_code, error_message) = self.run_command_with_timeout(script_args,self.TimeoutSeconds)

            if error_message is not None:
                self.Settings.current_debug_profile().log_error(
                    "Error output was returned from the snapshot script: {0}".format(error_message))
            if not return_code == 0:
                self.ErrorMessage = (
                    "Snapshot Script Error - The {0} script returned {1}, which indicates an error.  Please check" +
                    "your script and try again.".format(self.ScriptType, return_code)
                )
                self.HasError = True

            # Make sure the expected snapshot exists.  If it doesn't, don't create any metadata
            if not os.path.isfile(download_full_path):
                with open(os.path.join(download_directory, METADATA_FILE_NAME), 'a') as metadata_file:
                    dictwriter = DictWriter(metadata_file, METADATA_FIELDS)
                    dictwriter.writerow({
                        'snapshot_number': str(self.SnapshotNumber),
                        'file_name': download_filename,
                        'time_taken': str(time()),
                    })
        except CalledProcessError as e:
            # If we can't create the thumbnail, just log
            self.Settings.current_debug_profile().log_exception(e)
            self.ErrorMessage = (
                "Snapshot Script Error - An unexpected exception occurred executing the {0} script.  "
                "Check the log file (plugin_octolapse.log) for details.".format(self.ScriptType)
            )
            self.HasError = True

    def run_command_with_timeout(self, args, timeout_sec):
        """Execute `cmd` in a subprocess and enforce timeout `timeout_sec` seconds.

        Return subprocess exit code on natural completion of the subprocess.
        Raise an exception if timeout expires before subprocess completes."""
        proc = Popen(args)
        proc_thread = Thread(target=proc.communicate)
        proc_thread.start()
        proc_thread.join(timeout_sec)
        if proc_thread.is_alive():
            # Process still running - kill it and raise timeout error
            try:
                proc.kill()
                timeout_error = "The process timed out in {0} seconds and was killed.".format(timeout_sec)
            except OSError as e:
                timeout_error = "The process timed out in {0} seconds and was killed and an os exception was" \
                                "raised: {1}.".format(timeout_sec, utility.exception_to_string(e))
            # not sure if proc.returncode would have a value here...
            return 1, timeout_error

        # Process completed naturally - return exit code
        return proc.returncode, None


class SnapshotJob(object):

    def __init__(
        self, settings, data_directory, snapshot_number,
        snapshot_info, url, delay_ms, timeout_seconds, on_complete, on_success, on_fail
    ):

        self.DelaySeconds = delay_ms / 1000.0
        camera_settings = settings.current_camera()
        self.SnapshotNumber = snapshot_number
        self.DataDirectory = data_directory
        self.Address = camera_settings.address
        self.Username = camera_settings.username
        self.Password = camera_settings.password
        self.IgnoreSslError = camera_settings.ignore_ssl_error
        self.SnapshotTranspose = camera_settings.snapshot_transpose
        self.Settings = settings
        self.SnapshotInfo = snapshot_info
        self.Url = url
        self.TimeoutSeconds = timeout_seconds
        self.OnCompleteCallback = on_complete
        self.OnSuccessCallback = on_success
        self.OnFailCallback = on_fail
        self.HasError = False
        self.ErrorMessage = ""
        self.ErrorType = ""

    def on_success(self):
        self.OnSuccessCallback()

    def on_fail(self):
        self.OnFailCallback(self.ErrorMessage)

    def on_complete(self):
        self.OnCompleteCallback()

    def process(self):

        if self.DelaySeconds < 0.001:
            self.Settings.current_debug_profile().log_snapshot_download(
                "Starting Snapshot Download Job Immediately.")
        else:

            # Pre-Snapshot Delay - Some users had issues just using sleep.  In one examined instance the time.sleep
            # function was being called to sleep 0.250 S, but waited 0.005 S.  To deal with this a sleep loop was
            # implemented that makes sure we've waited at least self.DelaySeconds seconds before continuing.

            # record the time we started sleeping
            t0 = time()
            # record the number of sleep attempts for debug purposes
            sleep_tries = 0
            delay_seconds = self.DelaySeconds - (time() - t0)

            self.Settings.current_debug_profile().log_snapshot_download(
                "Snapshot Delay - Waiting {0} second(s) before acquiring a snapshot."
                    .format(self.DelaySeconds))

            while delay_seconds >= 0.001:
                sleep_tries += 1  # increment the sleep try counter

                sleep(delay_seconds)  # sleep the calculated amount

                delay_seconds = self.DelaySeconds - (time() - t0)

            self.Settings.current_debug_profile().log_snapshot_download(
                "Snapshot Delay - Waited {0} times for {1} seconds total."
                    .format(sleep_tries, time() - t0))

        self.HasError = False
        self.ErrorMessage = "unknown"
        snapshot_directory = self.SnapshotInfo.get_full_path(self.SnapshotNumber)
        r = None
        try:
            if len(self.Username) > 0:
                message = (
                    "Snapshot Download - Authenticating and "
                    "downloading from {0:s} to {1:s}."
                ).format(self.Url, snapshot_directory)
                self.Settings.current_debug_profile().log_snapshot_download(message)
                r = requests.get(
                    self.Url,
                    auth=HTTPBasicAuth(self.Username, self.Password),
                    verify=not self.IgnoreSslError,
                    timeout=float(self.TimeoutSeconds)
                )
            else:
                self.Settings.current_debug_profile().log_snapshot_download(
                    "Snapshot - downloading from {0:s} to {1:s}.".format(self.Url, snapshot_directory))
                r = requests.get(
                    self.Url, verify=not self.IgnoreSslError,
                    timeout=float(self.TimeoutSeconds)
                )
        except Exception as e:
            # If we can't create the thumbnail, just log
            self.Settings.current_debug_profile().log_exception(e)
            self.ErrorMessage = (
                "Snapshot Download - An unexpected exception occurred.  "
                "Check the log file (plugin_octolapse.log) for details."
            )
            self.HasError = True

        if not self.HasError:
            if r.status_code == requests.codes.ok:
                try:
                    # make the directory
                    path = os.path.dirname(snapshot_directory)
                    if not os.path.exists(path):
                        os.makedirs(path)
                    # try to download the file.
                except Exception as e:
                    # If we can't create the thumbnail, just log
                    self.Settings.current_debug_profile().log_exception(e)
                    self.ErrorMessage = (
                        "Snapshot Download - An unexpected exception occurred.  "
                        "Check the log file (plugin_octolapse.log) for details."
                    )
                    self.HasError = True
            else:
                self.ErrorMessage = "Snapshot Download - failed with status code:{0}".format(
                    r.status_code)
                self.HasError = True

        if not self.HasError:
            try:
                with i_open(snapshot_directory, 'wb') as snapshot_file:
                    for chunk in r.iter_content(1024):
                        if chunk:
                            snapshot_file.write(chunk)
                    self.Settings.current_debug_profile().log_snapshot_save(
                        "Snapshot - Snapshot saved to disk at {0}".format(snapshot_directory))
                # Write metadata about the snapshot.
                with open(os.path.join(path, METADATA_FILE_NAME), 'a') as metadata_file:
                    dictwriter = DictWriter(metadata_file, METADATA_FIELDS)
                    dictwriter.writerow({
                        'snapshot_number': str(self.SnapshotNumber),
                        'file_name': os.path.basename(snapshot_directory),
                        'time_taken': str(time()),
                    })
            except Exception as e:
                # If we can't create the thumbnail, just log
                self.Settings.current_debug_profile().log_exception(e)
                self.ErrorMessage = (
                    "Snapshot Download - An unexpected exception occurred.  "
                    "Check the log file (plugin_octolapse.log) for details."
                )
                self.HasError = True

        # go ahead and report success or fail for the timelapse routine
        if not self.HasError:
            self.on_success()
        else:
            self.on_fail()

        # transpose image if this is enabled.
        if not self.HasError:
            try:
                transpose_method = None
                if self.SnapshotTranspose is not None and self.SnapshotTranspose != "":
                    if self.SnapshotTranspose == 'flip_left_right':
                        transpose_method = Image.FLIP_LEFT_RIGHT
                    elif self.SnapshotTranspose == 'flip_top_bottom':
                        transpose_method = Image.FLIP_TOP_BOTTOM
                    elif self.SnapshotTranspose == 'rotate_90':
                        transpose_method = Image.ROTATE_90
                    elif self.SnapshotTranspose == 'rotate_180':
                        transpose_method = Image.ROTATE_180
                    elif self.SnapshotTranspose == 'rotate_270':
                        transpose_method = Image.ROTATE_270
                    elif self.SnapshotTranspose == 'transpose':
                        transpose_method = Image.TRANSPOSE

                    if transpose_method is not None:
                        im = Image.open(snapshot_directory)
                        im = im.transpose(transpose_method)
                        im.save(snapshot_directory)
            except IOError as e:
                # If we can't create the thumbnail, just log
                self.Settings.current_debug_profile().log_exception(e)
                self.ErrorMessage = (
                    "Snapshot transpose - An unexpected IOException occurred.  "
                    "Check the log file (plugin_octolapse.log) for details."
                )
                self.HasError = True

        # create a thumbnail and save the current snapshot as the most recent snapshot image
        if not self.HasError:
            try:
                # without this I get errors during load (happens in resize, where the image is actually loaded)
                ImageFile.LOAD_TRUNCATED_IMAGES = True
                #######################################

                # create a copy to be used for the full sized latest snapshot image.
                latest_snapshot_path = utility.get_latest_snapshot_download_path(self.DataDirectory)
                shutil.copy(self.SnapshotInfo.get_full_path(self.SnapshotNumber), latest_snapshot_path)

                # create a thumbnail of the image
                basewidth = 300
                img = Image.open(latest_snapshot_path)
                wpercent = (basewidth / float(img.size[0]))
                hsize = int((float(img.size[1]) * float(wpercent)))
                img = img.resize((basewidth, hsize), Image.ANTIALIAS)
                img.save(utility.get_latest_snapshot_thumbnail_download_path(
                    self.DataDirectory), "JPEG")
            except Exception as e:
                # If we can't create the thumbnail, just log
                self.Settings.current_debug_profile().log_exception(e)
                self.ErrorMessage = (
                    "Create latest snapshot and thumbnail - An unexpected exception occurred.  "
                    "Check the log file (plugin_octolapse.log) for details."
                )
                self.HasError = True

        self.on_complete()
        self.Settings.current_debug_profile().log_snapshot_download(
            "Snapshot Download Job completed, signaling task queue.")


class SnapshotInfo(object):
    def __init__(self, printer_file_name, print_start_time):
        self._printerFileName = printer_file_name
        self._printStartTime = print_start_time
        self.DirectoryName = ""

    def get_full_path(self, snapshot_number):
        return os.path.join(self.DirectoryName,
                            utility.get_snapshot_filename(self._printerFileName, self._printStartTime, snapshot_number))
