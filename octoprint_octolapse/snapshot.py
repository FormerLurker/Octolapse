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

import shutil
import threading
import os
from io import open as i_open
from PIL import ImageFile, Image
from time import sleep, time

import requests
from PIL import Image
# PIL is in fact in setup.py.
from requests.auth import HTTPBasicAuth

import octoprint_octolapse.camera as camera
from octoprint_octolapse.settings import *


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

    def create_snapshot_job(self, printer_file_name, snapshot_number, snapshot_guid, task_queue, on_complete, on_success, on_fail):
        info = SnapshotInfo(printer_file_name, self.PrintStartTime)
        # set the file name.  It will be a guid + the file extension
        info.FileName = "{0}.{1}".format(snapshot_guid, "jpg")
        info.DirectoryName = utility.get_snapshot_temp_directory(
            self.DataDirectory)
        url = camera.format_request_template(
            self.Camera.address, self.Camera.snapshot_request_template, "")
        # TODO:  TURN THE SNAPSHOT REQUIRE TIMEOUT INTO A SETTING
        new_snapshot_job = SnapshotJob(
            self.Settings, self.DataDirectory, snapshot_number, info, url,
            snapshot_guid, task_queue, self.Camera.delay, self.SnapshotTimeout, on_complete=on_complete,
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


class SnapshotJob(object):
    snapshot_job_lock = threading.RLock()

    def __init__(
            self, settings, data_directory, snapshot_number,
            snapshot_info, url, snapshot_guid, task_queue,
            delay_ms, timeout_seconds, on_complete, on_success, on_fail
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
        self.SnapshotGuid = snapshot_guid
        self.OnCompleteCallback = on_complete
        self.OnSuccessCallback = on_success
        self.OnFailCallback = on_fail
        self.task_queue = task_queue
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
        with self.snapshot_job_lock:

            if self.DelaySeconds < 0.001:
                self.Settings.current_debug_profile().log_snapshot_download(
                    "Starting Snapshot Download Job Immediately.")
            else:

                # Pre-Snapshot Delay - Some users had issues just using sleep.  In one examined instance the time.sleep
                # function was being called to sleep 0.250 S, but waited 0.005 S.  To deal with this a sleep loop was
                # implemented that makes sure we've waited at least self.DelaySeconds seconds before continuing.

                # record the time we started sleeping
                t0 = time()
                # start the loop by setting is_sleeping to true
                is_sleeping = True
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
            snapshot_directory = "{0:s}{1:s}".format(
                self.SnapshotInfo.DirectoryName, self.SnapshotInfo.FileName)
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

            if not self.HasError:
                # this call renames the snapshot so that it is
                # sequential (prob could just sort by create date
                # instead, todo). returns true on success.
                self.HasError = not self._move_rename_snapshot_sequential()

            # create a thumbnail and save the current snapshot as the most recent snapshot image
            if not self.HasError:

                try:
                    # without this I get errors during load (happens in resize, where the image is actually loaded)
                    ImageFile.LOAD_TRUNCATED_IMAGES = True
                    #######################################

                    # create a copy to be used for the full sized latest snapshot image.
                    latest_snapshot_path = utility.get_latest_snapshot_download_path(
                        self.DataDirectory
                    )
                    shutil.copy(self.SnapshotInfo.get_full_path(
                        self.SnapshotNumber), latest_snapshot_path)
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
            self.task_queue.get()
            self.task_queue.task_done()


    def _move_rename_snapshot_sequential(self):
        # get the save path
        # get the current file name
        new_snapshot_name = self.SnapshotInfo.get_full_path(self.SnapshotNumber)
        self.Settings.current_debug_profile().log_snapshot_save(
            "Renaming snapshot {0} to {1}".format(self.SnapshotInfo.get_temp_full_path(), new_snapshot_name))
        # create the output directory if it does not exist
        try:
            temp_snapshot_path = os.path.dirname(new_snapshot_name)
            latest_snapshot_path = utility.get_snapshot_directory(
                self.DataDirectory)
            if not os.path.exists(temp_snapshot_path):
                os.makedirs(temp_snapshot_path)
            if not os.path.exists(latest_snapshot_path):
                os.makedirs(latest_snapshot_path)
            # rename the current file
            shutil.move(self.SnapshotInfo.get_temp_full_path(), new_snapshot_name)
            self.SnapshotSuccess = True
            return True
        except Exception as e:
            self.Settings.current_debug_profile().log_exception(e)

        return False


class SnapshotInfo(object):
    def __init__(self, printer_file_name, print_start_time):
        self._printerFileName = printer_file_name
        self._printStartTime = print_start_time
        self.FileName = ""
        self.DirectoryName = ""

    def get_temp_full_path(self):
        return "{0}{1}{2}".format(self.DirectoryName, os.sep, self.FileName)

    def get_full_path(self, snapshot_number):
        return "{0}{1}".format(
            self.DirectoryName,
            utility.get_snapshot_filename(
                self._printerFileName,
                self._printStartTime,
                snapshot_number
            )
        )
