# coding=utf-8

# This file is subject to the terms and conditions defined in
# file called 'LICENSE', which is part of this source code package.

import shutil
import threading
import os
from io import open as i_open

import requests
from PIL import Image
# PIL is in fact in setup.py.
from requests.auth import HTTPBasicAuth

import octoprint_octolapse.camera as camera
from octoprint_octolapse.settings import *


def start_snapshot_job(job):
    job.process()


class CaptureSnapshot(object):

    def __init__(self, settings, data_directory, print_start_time, print_end_time=None):
        self.Settings = settings
        self.Printer = self.Settings.current_printer()
        self.Snapshot = self.Settings.current_snapshot()
        self.Camera = self.Settings.current_camera()
        self.PrintStartTime = print_start_time
        self.PrintEndTime = print_end_time
        self.DataDirectory = data_directory

    def snap(self, printer_file_name, snapshot_number, on_complete=None, on_success=None, on_fail=None):
        info = SnapshotInfo(printer_file_name, self.PrintStartTime)
        # set the file name.  It will be a guid + the file extension
        snapshot_guid = str(uuid.uuid4())
        info.FileName = "{0}.{1}".format(snapshot_guid, "jpg")
        info.DirectoryName = utility.get_snapshot_temp_directory(
            self.DataDirectory)
        url = camera.format_request_template(
            self.Camera.address, self.Camera.snapshot_request_template, "")
        # TODO:  TURN THE SNAPSHOT REQUIRE TIMEOUT INTO A SETTING
        new_snapshot_job = SnapshotJob(
            self.Settings, self.DataDirectory, snapshot_number, info, url,
            snapshot_guid, timeout_seconds=1, on_complete=on_complete, on_success=on_success, on_fail=on_fail
        )

        if self.Camera.delay == 0:
            self.Settings.current_debug_profile().log_snapshot_download(
                "Starting Snapshot Download Job Immediately.")
            new_snapshot_job.process()
        else:
            delay_seconds = self.Camera.delay / 1000.0
            self.Settings.current_debug_profile().log_snapshot_download(
                "Starting Snapshot Download Job in {0} seconds.".format(delay_seconds))
            t = threading.Timer(
                delay_seconds, start_snapshot_job, [new_snapshot_job])
            t.start()

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
            snapshot_info, url, snapshot_guid, timeout_seconds=5,
            on_complete=None, on_success=None, on_fail=None):
        camera_settings = settings.current_camera()
        self.SnapshotNumber = snapshot_number
        self.DataDirectory = data_directory
        self.Address = camera_settings.address
        self.Username = camera_settings.username
        self.Password = camera_settings.password
        self.IgnoreSslError = camera_settings.ignore_ssl_error
        self.Settings = settings
        self.SnapshotInfo = snapshot_info
        self.Url = url
        self.TimeoutSeconds = timeout_seconds
        self.SnapshotGuid = snapshot_guid
        self._on_complete = on_complete
        self._on_success = on_success
        self._on_fail = on_fail
        self._thread = None

    def process(self):
        # TODO:  REPLACE THE SNAPSHOT NUMBER WITH A GUID HERE
        self._thread = threading.Thread(
            target=self._process, name="SnapshotDownloadJob_{name}".format(name=self.SnapshotGuid))
        self._thread.daemon = True
        self._thread.start()

    def _process(self):
        with self.snapshot_job_lock:

            error = False
            fail_reason = "unknown"
            snapshot_directory = "{0:s}{1}{2:s}".format(
                self.SnapshotInfo.DirectoryName, os.sep, self.SnapshotInfo.FileName)
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
                fail_reason = (
                    "Snapshot Download - An unexpected exception occurred.  "
                    "Check the log file (plugin_octolapse.log) for details."
                )
                error = True

            if not error:
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
                        fail_reason = (
                            "Snapshot Download - An unexpected exception occurred.  "
                            "Check the log file (plugin_octolapse.log) for details."
                        )
                        error = True
                else:
                    fail_reason = "Snapshot Download - failed with status code:{0}".format(
                        r.status_code)
                    error = True

            if not error:
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
                    fail_reason = (
                        "Snapshot Download - An unexpected exception occurred.  "
                        "Check the log file (plugin_octolapse.log) for details."
                    )
                    error = True
            if not error:
                # this call renames the snapshot so that it is
                # sequential (prob could just sort by create date
                # instead, todo). returns true on success.
                error = not self._move_rename_snapshot_sequential()

            if not error:
                self._notify_callback("success", self.SnapshotInfo)
            else:
                self._notify_callback("fail", fail_reason)

            self._notify_callback("complete")
            # do this after we notify of success.  It will likely complete before the client
            # is notified of snapshot changes and if it doesn't, no big deal.  It is better
            # if we start the print back up sooner and fail to deliver a new thumbnail than to not.
            if not error:
                self._save_snapshot_and_thumbnail()

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

    def _save_snapshot_and_thumbnail(self):
        # create a copy to be used for the full sized latest snapshot image.
        latest_snapshot_path = utility.get_latest_snapshot_download_path(
            self.DataDirectory)
        shutil.copy(self.SnapshotInfo.get_full_path(
            self.SnapshotNumber), latest_snapshot_path)
        # create a thumbnail of the image
        try:
            from PIL import ImageFile
            # without this I get errors during load (happens in resize, where the image is actually loaded)
            ImageFile.LOAD_TRUNCATED_IMAGES = True
            #######################################

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

    def _notify_callback(self, callback, *args, **kwargs):
        """Notifies registered callbacks of type `callback`."""
        name = "_on_{}".format(callback)
        method = getattr(self, name, None)
        if method is not None and callable(method):
            method(*args, **kwargs)


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
