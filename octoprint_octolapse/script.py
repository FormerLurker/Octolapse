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
import subprocess
import threading
import psutil
import os
import sys
import platform

# create the module level logger
from octoprint_octolapse.log import LoggingConfigurator
logging_configurator = LoggingConfigurator()
logger = logging_configurator.get_logger(__name__)

if sys.version_info >= (3, 2):
    def fsdecode(filename):
        return os.fsdecode(filename)
else:
    fs_encoding = sys.getfilesystemencoding()
    fs_errors = 'surrogateescape' if platform.system() != "Windows" else 'strict'

    def fsdecode(filename):
        if isinstance(filename, bytes):
            return filename.decode(fs_encoding, fs_errors)
        else:
            return filename


class POpenWithTimeout(object):

    class ProcessError(Exception):
        def __init__(self, error_type, message, cause=None):
            super(POpenWithTimeout.ProcessError, self).__init__()
            self.error_type = error_type
            self.cause = cause if cause is not None else None
            self.message = message

        def __str__(self):
            if self.cause is None:
                return "{}: {}".format(self.error_type, self.message)
            if isinstance(self.cause, list):
                if len(self.cause) > 1:
                    error_string = "{}: {} - Inner Exceptions".format(self.error_type, self.message)
                    error_count = 1
                    for cause in self.cause:
                        error_string += "{}    {}: {} Exception - {}".format(os.linesep, error_count, type(cause).__name__, cause)
                        error_count += 1
                    return error_string
                elif len(self.cause) == 1:
                    return "{}: {} - Inner Exception: {}".format(self.error_type, self.message, self.cause[0])
            return "{}: {} - Inner Exception: {}".format(self.error_type, self.message, self.cause)

    lock = threading.Lock()

    def __init__(self):
        self.name = "Unknown"
        self.proc = None
        self.stdout = ''
        self.stderr = ''
        self.error_message = None
        self.completed = False
        self._exception = None
        self._subprocess_kill_exceptions = []
        self._kill_exceptions = None
        self.exception = None
        self.timeout_seconds = None
        self.return_code = -100
        self._timed_out = False
        self._was_killed = False
        self._success = False

    def success(self):
        return self._success

    def kill(self):
        if self.proc is None:
            return
        try:
            process = psutil.Process(self.proc.pid)
            for proc in process.children(recursive=True):
                try:
                    proc.kill()
                except psutil.NoSuchProcess:
                    # the process must have completed
                    pass
                except (psutil.Error,psutil.AccessDenied, psutil.ZombieProcess) as e:
                    logger.exception("An error occurred while killing the '%s' process.", self.name)
                    self._kill_exceptions.append(e)
            process.kill()
            self._was_killed = True
            logger.warning("The '%s' process has been killed.", self.name)
        except psutil.NoSuchProcess:
            # the process must have completed
            pass
        except (psutil.Error, psutil.AccessDenied, psutil.ZombieProcess) as e:
            logger.exception("An error occurred while killing the '%s' process.", self.name)
            self._kill_exceptions = e
        finally:
            self.read_output_from_proc()

    def set_exceptions(self):
        if (
            self._exception is None
            and (self._subprocess_kill_exceptions is None or len(self._subprocess_kill_exceptions) == 0)
            and self._kill_exceptions is None
        ):
            return None
        causes = []
        error_type = None
        error_message = None
        if self._exception is not None:
            error_type = 'script-execution-error'
            error_message = 'An error occurred curing the execution of a custom script.'
            causes.append(self._exception)
        if self._kill_exceptions is not None:
            if error_type is None:
                error_type = 'script-kill-error'
                error_message = 'A custom script timed out, and an error occurred while terminating the process.'
            causes.append(self._kill_exceptions)
        if len(self._subprocess_kill_exceptions) > 0:
            if error_type is None:
                error_type = 'script-subprocess-kill-error'
                error_message = 'A custom script timed out, and an error occurred while terminating one of its ' \
                                'subprocesses.'
            for cause in self._subprocess_kill_exceptions:
                causes.append(cause)
        self.exception = POpenWithTimeout.ProcessError(
            error_type,
            error_message,
            cause=causes)

    def read_output_from_proc(self):
        if self.proc:
            # self.proc could be none!
            (exc_stdout, exc_stderr) = self.proc.communicate()
            self.stdout = fsdecode(exc_stdout)
            self.stderr = fsdecode(exc_stderr)

            # Clean stderr and stdout, removing duplicate and ending line breaks, which make the log hard to
            # read and the log file bigger.

            # Clean stderr
            if self.stderr:
                if self.stderr.endswith(os.linesep):
                    self.stderr = self.stderr[:-1 * len(os.linesep)]
                self.stderr = self.stderr.replace("{0}{0}".format(os.linesep, os.linesep), os.linesep)

            # Clean stdout
            if self.stdout:
                if self.stdout.endswith(os.linesep):
                    self.stdout = self.stdout[:-1*len(os.linesep)]
                self.stdout = self.stdout.replace("{0}{0}".format(os.linesep, os.linesep), os.linesep)

    def log_command(self, args, timeout_seconds):
        if len(args) < 1 or args[0] is None:
            script_path = ""
        else:
            script_path = args[0].strip()
        if len(args) > 1:
            arguments_list = ["\"{0}\"".format(arg) for arg in args[1:]]
            script_text = "\"{0}\" {1}".format(script_path, " ".join(arguments_list))
        else:
            script_text = "\"{0}\"".format(script_path)
        if timeout_seconds is not None:
            logger.debug("Executing %s: %s", self.name, script_text)
        else:
            timeout_seconds_string = "no"
            if timeout_seconds:
                timeout_seconds_string = "a {0} second".format(timeout_seconds)
            else:
                timeout_seconds_string = "no"
            logger.debug(
                "Executing %s with %s timeout: %s", self.name, timeout_seconds_string, script_text)

    def log_console_and_errors(self):
        # log
        if self.stdout:
            logger.debug(
                "Console output (stdout) for '%s':%s",
                self.name,
                # add a tab after all line breaks
                self.stdout.replace(os.linesep, "{0}\t".format(os.linesep))
            )

        if self.stderr:
            logger.error(
                "Error output (stderr) for '%s':%s\t%s",
                self.name,
                os.linesep,
                # add a tab after all line breaks
                self.stderr.replace(os.linesep, "{0}\t".format(os.linesep))
            )

    # run a command with the provided args, timeout in timeout_seconds
    def run(self, args, timeout_seconds=None):
        self.log_command(args, timeout_seconds)
        self._run(args, timeout_seconds=timeout_seconds)
        self.log_console_and_errors()
        return self.return_code

    def _run(self, args, timeout_seconds=None):
        if len(args) < 1 or args[0] is None:
            self.error_message = "No script path was provided for {0}.  Please enter a script path and try again.".format(self.name)
            logger.error(self.error_message)
            return
        script_path = args[0].strip()
        if len(script_path) == 0:
            self.error_message = "No script path was provided for {0}.  Please enter a script path and try again.".format(self.name)
            logger.error(self.error_message)
            return

        if not os.path.exists(script_path):
            self.error_message = "The script at path '{0}' could not be found for  for {1}.  Please check your script" \
                                 " path and try again.".format(script_path, self.name)
            logger.error(self.error_message)
            return

        self.timeout_seconds = timeout_seconds
        # Create, start and run the process and fill in stderr and stdout
        def execute_process(args):
            # get the lock so that we can start the process without encountering a timeout
            self.lock.acquire()
            has_error = False
            try:
                # don't start the process if we've already timed out
                if not self.completed:
                    self.proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                else:
                    logger.error("The '%s' process was completed by the caller before it could be started.", self.name)
                    return
            except (OSError, subprocess.CalledProcessError) as e:
                logger.exception("An error occurred while executing '%s'", self.name)
                self._exception = e
            finally:
                self.lock.release()

            self.read_output_from_proc()
            try:
                self.lock.acquire()
                if not self.completed:
                    self.completed = True
            finally:
                self.lock.release()

        thread = threading.Thread(target=execute_process, args=[args])
        thread.daemon = True
        # start the thread
        thread.start()
        # join the thread with a timeout
        thread.join(timeout=self.timeout_seconds)
        # check to see if the thread is alive
        if thread.is_alive():
            self.lock.acquire()
            try:
                if not self.completed:
                    self._timed_out = self.timeout_seconds is not None
                    if self.proc is not None:
                        logger.error("The '%s' process has timed out before completing.  Attempting to kill the "
                                       "process.", self.name)
                        self.kill()

                    self.completed = True
            except AttributeError:
                # It's possible that the process is killed AFTER we check for self.proc is None
                # catch that here and pass
                pass
            finally:
                self.lock.release()

        # read and set the return code if possible.
        self.set_return_code()
        # now set the success value
        self._success = not (self._timed_out or self._was_killed or self._exception is not None or self.stderr or self.return_code != 0)
        # set the error message
        self.set_error_message()

    def set_return_code(self):
        if self.proc:
            self.return_code = self.proc.returncode

    def set_error_message(self):
        if self._timed_out:
            if self.stderr:
                self.error_message = "The '{0}' timed out in {1} seconds.  Errors were returned from the process, " \
                                     "see plugin_octolapse.log for details.".format(
                    self.name, self.timeout_seconds)
            else:
                self.error_message = "The '{0}' timed out in {1} seconds.".format(self.name, self.timeout_seconds)
            return

        if self._exception is not None:
            if self.stderr:
                self.error_message = "The '{0}' raised an exception and returned error output.  See " \
                                     "plugin_octolapse.log for details.".format(self.name)
            else:
                self.error_message = "The '{0}' raised an exception.  See plugin_octolapse.log for details.".format(self.name)
            return

        if self.return_code != 0:
            if self.stderr:
                self.error_message = "The '{0}' reported errors and returned a value of {1}, which indicates an " \
                                     "error.  See plugin_octolapse.log for details.".format(self.name, self.return_code)
            else:
                self.error_message = "The'{0}' returned a value of {1}, which indicates an error.".format(
                    self.name, self.return_code)

        if self.proc is None:
            self.error_message = "The '{0}' process does not exist.  This is unusual, and indicates a bug or other " \
                                 "unexpected issue.  Check plugin_octolapse.log.".format(self.name)

        if self.stderr:
            # if we have no error and a null proc, report this.
            self.error_message = (
                "The '{0}' process returned errors.  See plugin_octolapse.log for details".format(self.name)
            )


class POpenWithTimeoutAsync(object):

    class ProcessError(Exception):
        def __init__(self, error_type, message, cause=None):
            super(POpenWithTimeoutAsync.ProcessError, self).__init__()
            self.error_type = error_type
            self.cause = cause if cause is not None else None
            self.message = message

        def __str__(self):
            if self.cause is None:
                return "{}: {}".format(self.error_type, self.message)
            if isinstance(self.cause, list):
                if len(self.cause) > 1:
                    error_string = "{}: {} - Inner Exceptions".format(self.error_type, self.message)
                    error_count = 1
                    for cause in self.cause:
                        error_string += "{}    {}: {} Exception - {}".format(os.linesep, error_count, type(cause).__name__, cause)
                        error_count += 1
                    return error_string
                elif len(self.cause) == 1:
                    return "{}: {} - Inner Exception: {}".format(self.error_type, self.message, self.cause[0])
            return "{}: {} - Inner Exception: {}".format(self.error_type, self.message, self.cause)

    lock = threading.Lock()

    def __init__(self, on_stdout_line_received=None, on_stderr_line_received=None):
        self.name = "Unknown"
        self.proc = None
        self.stdout_lines = []
        self.stderr_lines = []
        self.error_message = None
        self.completed = False
        self._exception = None
        self._subprocess_kill_exceptions = []
        self._kill_exceptions = None
        self.exception = None
        self.timeout_seconds = None
        self.return_code = -100
        self._timed_out = False
        self._was_killed = False
        self._success = False
        self.stdout_line_received_callback = on_stdout_line_received
        self.stderr_line_received_callback = on_stderr_line_received

    def success(self):
        return self._success

    def kill(self):
        if self.proc is None:
            return
        try:
            process = psutil.Process(self.proc.pid)
            for proc in process.children(recursive=True):
                try:
                    proc.kill()
                except psutil.NoSuchProcess:
                    # the process must have completed
                    pass
                except (psutil.Error,psutil.AccessDenied, psutil.ZombieProcess) as e:
                    logger.exception("An error occurred while killing the '%s' process.", self.name)
                    self._kill_exceptions.append(e)
            process.kill()
            self._was_killed = True
            logger.warning("The '%s' process has been killed.", self.name)
        except psutil.NoSuchProcess:
            # the process must have completed
            pass
        except (psutil.Error, psutil.AccessDenied, psutil.ZombieProcess) as e:
            logger.exception("An error occurred while killing the '%s' process.", self.name)
            self._kill_exceptions = e

    def set_exceptions(self):
        if (
            self._exception is None
            and (self._subprocess_kill_exceptions is None or len(self._subprocess_kill_exceptions) == 0)
            and self._kill_exceptions is None
        ):
            return None
        causes = []
        error_type = None
        error_message = None
        if self._exception is not None:
            error_type = 'script-execution-error'
            error_message = 'An error occurred curing the execution of a custom script.'
            causes.append(self._exception)
        if self._kill_exceptions is not None:
            if error_type is None:
                error_type = 'script-kill-error'
                error_message = 'A custom script timed out, and an error occurred while terminating the process.'
            causes.append(self._kill_exceptions)
        if len(self._subprocess_kill_exceptions) > 0:
            if error_type is None:
                error_type = 'script-subprocess-kill-error'
                error_message = 'A custom script timed out, and an error occurred while terminating one of its ' \
                                'subprocesses.'
            for cause in self._subprocess_kill_exceptions:
                causes.append(cause)
        self.exception = POpenWithTimeoutAsync.ProcessError(
            error_type,
            error_message,
            cause=causes)

    def read_output_from_proc(self):
        if self.proc:
            # self.proc could be none!
            (exc_stdout, exc_stderr) = self.proc.communicate()
            self.stdout = fsdecode(exc_stdout)
            self.stderr = fsdecode(exc_stderr)

            # Clean stderr and stdout, removing duplicate and ending line breaks, which make the log hard to
            # read and the log file bigger.

            # Clean stderr
            if self.stderr:
                if self.stderr.endswith(os.linesep):
                    self.stderr = self.stderr[:-1 * len(os.linesep)]
                self.stderr = self.stderr.replace("{0}{0}".format(os.linesep, os.linesep), os.linesep)

            # Clean stdout
            if self.stdout:
                if self.stdout.endswith(os.linesep):
                    self.stdout = self.stdout[:-1*len(os.linesep)]
                self.stdout = self.stdout.replace("{0}{0}".format(os.linesep, os.linesep), os.linesep)

    def log_command(self, args, timeout_seconds):
        command_string = subprocess.list2cmdline(args)
        if timeout_seconds is not None:
            logger.debug("Executing %s: %s", self.name, command_string)
        else:
            if timeout_seconds:
                timeout_seconds_string = "a {0} second".format(timeout_seconds)
            else:
                timeout_seconds_string = "No Timeout"
            logger.debug(
                "Executing %s with %s timeout: %s", self.name, timeout_seconds_string, command_string)

    @staticmethod
    def _read_std_line(line, type_name, callback):
        if not line:
            return None
        line = fsdecode(line)
        # remove extra line breaks, so that each line is actually a single line.  Should work for windows too.
        if line.endswith('\n'):
            line = line[:-1 * len(os.linesep)]
        if line.endswith('\r'):
            line = line[:-1 * len(os.linesep)]

        logger.info("%s: %s", type_name, line)
        if callback:
            callback(line)
        return line

    def _read_stdout_lines(self, proc):
        try:
            while proc.returncode is None:
                line = proc.stdout.readline()
                line = POpenWithTimeoutAsync._read_std_line(line, 'stdout', self.stdout_line_received_callback)
                if line:
                    self.stdout_lines.append(line)
                proc.poll()
        except Exception as e:
            logger.exception("An error occurred while reading stdout.")
            raise e

    def _read_stderr_lines(self, proc):
        try:
            while proc.returncode is None:
                line = proc.stderr.readline()
                line = POpenWithTimeoutAsync._read_std_line(line, 'stderr', self.stderr_line_received_callback)
                if line:
                    self.stderr_lines.append(line)
                proc.poll()
        except Exception as e:
            logger.exception("An error occurred while reading stderr.")
            raise e
    # run a command with the provided args, timeout in timeout_seconds
    def run(self, args, timeout_seconds=None):
        self.log_command(args, timeout_seconds)
        self._run(args, timeout_seconds=timeout_seconds)
        return self.return_code

    def _run(self, args, timeout_seconds=None):
        if len(args) < 1 or args[0] is None:
            self.error_message = "No script path was provided for {0}.  Please enter a script path and try again.".format(self.name)
            logger.error(self.error_message)
            return
        script_path = args[0].strip()
        if len(script_path) == 0:
            self.error_message = "No script path was provided for {0}.  Please enter a script path and try again.".format(self.name)
            logger.error(self.error_message)
            return

        if not os.path.exists(script_path):
            self.error_message = "The script at path '{0}' could not be found for  for {1}.  Please check your script" \
                                 " path and try again.".format(script_path, self.name)
            logger.error(self.error_message)
            return

        self.timeout_seconds = timeout_seconds
        # Create, start and run the process and fill in stderr and stdout
        def execute_process(args):
            # get the lock so that we can start the process without encountering a timeout
            with self.lock:
                try:
                    # don't start the process if we've already timed out
                    if not self.completed:
                        self.proc = subprocess.Popen(
                            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
                        )
                        # create threads to read stdin and stdout
                        stdout_reader = threading.Thread(target=self._read_stdout_lines, args=[self.proc])
                        stdout_reader.daemon = True
                        stderr_reader = threading.Thread(target=self._read_stderr_lines, args=[self.proc])
                        stderr_reader.daemon = True
                        stdout_reader.start()
                        stderr_reader.start()
                        self.proc.wait()
                        stdout_reader.join()
                        stderr_reader.join()
                    else:
                        logger.error("The '%s' process was completed by the caller before it could be started.", self.name)
                        return
                except (OSError, subprocess.CalledProcessError) as e:
                    logger.exception("An error occurred while executing '%s'", self.name)
                    self._exception = e
                    return

        thread = threading.Thread(target=execute_process, args=[args])
        thread.daemon = True
        # start the thread
        thread.start()
        # join the thread with a timeout
        thread.join(timeout=self.timeout_seconds)
        # check to see if the thread is alive
        if thread.is_alive():
            self.lock.acquire()
            try:
                if not self.completed:
                    self._timed_out = self.timeout_seconds is not None
                    if self.proc is not None:
                        logger.error("The '%s' process has timed out before completing.  Attempting to kill the "
                                       "process.", self.name)
                        self.kill()

                    self.completed = True
            except AttributeError:
                # It's possible that the process is killed AFTER we check for self.proc is None
                # catch that here and pass
                pass
            finally:
                self.lock.release()

        # read and set the return code if possible.
        self.set_return_code()
        # now set the success value
        self._success = not (
            self._timed_out or
            self._was_killed or
            self._exception is not None or
            len(self.stderr_lines) > 0
            or self.return_code != 0
        )
        # set the error message
        self.set_error_message()

    def set_return_code(self):
        if self.proc:
            self.return_code = self.proc.returncode

    def set_error_message(self):
        if self._timed_out:
            if self.stderr:
                self.error_message = "The '{0}' timed out in {1} seconds.  Errors were returned from the process, " \
                                     "see plugin_octolapse.log for details.".format(
                    self.name, self.timeout_seconds)
            else:
                self.error_message = "The '{0}' timed out in {1} seconds.".format(self.name, self.timeout_seconds)
            return

        if self._exception is not None:
            if self.stderr:
                self.error_message = "The '{0}' raised an exception and returned error output.  See " \
                                     "plugin_octolapse.log for details.".format(self.name)
            else:
                self.error_message = "The '{0}' raised an exception.  See plugin_octolapse.log for details.".format(self.name)
            return

        if self.return_code != 0:
            if len(self.stderr_lines) > 0:
                self.error_message = "The '{0}' reported errors and returned a value of {1}, which indicates an " \
                                     "error.  See plugin_octolapse.log for details.".format(self.name, self.return_code)
            else:
                self.error_message = "The'{0}' returned a value of {1}, which indicates an error.".format(
                    self.name, self.return_code)
            return

        if self.proc is None:
            if len(self.stderr_lines) > 0:
                self.error_message = (
                    "The '{0}' process does not exist, but returned errors.  This is unusual, and"
                    " indicates a bug or other unexpected issue.  Check plugin_octolapse.log.".format(self.name)
                )
            else:
                self.error_message = (
                    "The '{0}' process does not exist.  This is unusual, and indicates a bug or other "
                     "unexpected issue.  Check plugin_octolapse.log.".format(self.name)
                )
            return

        if len(self.stderr_lines) > 0:
            # if we have no error and a null proc, report this.
            self.error_message = (
                "The '{0}' process returned errors.  See plugin_octolapse.log for details".format(self.name)
            )
            return


class CameraScriptSnapshot(POpenWithTimeout):
    def __init__(self, script_path, camera_name, snapshot_number, delay_seconds, data_directory, snapshot_directory,
                 snapshot_filename, snapshot_full_path, timeout_seconds=None):
        super(CameraScriptSnapshot, self).__init__()
        self.name = "{0} - Snapshot Camera Script".format(camera_name)
        self.script_path = script_path
        self.timeout_seconds = timeout_seconds
        self.camera_name = camera_name
        self.snapshot_number = snapshot_number
        self.delay_seconds = delay_seconds
        self.data_directory = data_directory
        self.snapshot_directory = snapshot_directory
        self.snapshot_filename = snapshot_filename
        self.snapshot_full_path = snapshot_full_path

    def get_args(self):
        return [
            self.script_path,
            "{}".format(self.snapshot_number),
            "{}".format(self.delay_seconds),
            self.data_directory,
            self.snapshot_directory,
            self.snapshot_filename,
            self.snapshot_full_path,
            self.camera_name
        ]

    def run(self):
        return super(CameraScriptSnapshot, self).run(self.get_args(), self.timeout_seconds)


class CameraScriptBeforeAfterSnapshot(POpenWithTimeout):
    def __init__(self, script_path, camera_name, snapshot_number, delay_seconds, data_directory, snapshot_directory, snapshot_filename, snapshot_full_path, timeout_seconds=None):
        super(CameraScriptBeforeAfterSnapshot, self).__init__()
        self.name = "Before/After Snapshot Script"
        self.script_path = script_path
        self.timeout_seconds = timeout_seconds
        self.camera_name = camera_name
        self.snapshot_number = snapshot_number
        self.delay_seconds = delay_seconds
        self.data_directory = data_directory
        self.snapshot_directory = snapshot_directory
        self.snapshot_filename = snapshot_filename
        self.snapshot_full_path = snapshot_full_path

    def get_args(self):
        return [
            self.script_path,
            "{}".format(self.snapshot_number),
            "{}".format(self.delay_seconds),
            self.data_directory,
            self.snapshot_directory,
            self.snapshot_filename,
            self.snapshot_full_path,
            self.camera_name
        ]

    def run(self):
        return super(CameraScriptBeforeAfterSnapshot, self).run(self.get_args(), self.timeout_seconds)


class CameraScriptBeforeSnapshot(CameraScriptBeforeAfterSnapshot):
    def __init__(self, script_path, camera_name, snapshot_number, delay_seconds, data_directory, snapshot_directory, snapshot_filename, snapshot_full_path, timeout_seconds=None):
        super(CameraScriptBeforeSnapshot, self).__init__(script_path, camera_name, snapshot_number, delay_seconds, data_directory, snapshot_directory, snapshot_filename, snapshot_full_path, timeout_seconds)
        self.name = "{0} - Before Snapshot Camera Script".format(camera_name)


class CameraScriptAfterSnapshot(CameraScriptBeforeAfterSnapshot):
    def __init__(self, script_path, camera_name, snapshot_number, delay_seconds, data_directory, snapshot_directory, snapshot_filename, snapshot_full_path, timeout_seconds=None):
        super(CameraScriptAfterSnapshot, self).__init__(script_path, camera_name, snapshot_number, delay_seconds, data_directory, snapshot_directory, snapshot_filename, snapshot_full_path, timeout_seconds)
        self.name = "{0} - After Snapshot Camera Script".format(camera_name)


class CameraScriptBeforeAfterPrint(POpenWithTimeout):
    def __init__(self, script_path, camera_name, timeout_seconds=None):
        super(CameraScriptBeforeAfterPrint, self).__init__()
        self.script_path = script_path
        self.timeout_seconds = timeout_seconds
        self.camera_name = camera_name

    def get_args(self):
        return [
            self.script_path,
            self.camera_name
        ]

    def run(self):
        return super(CameraScriptBeforeAfterPrint, self).run(self.get_args(), self.timeout_seconds)


class CameraScriptBeforePrint(CameraScriptBeforeAfterPrint):
    def __init__(self, script_path, camera_name, timeout_seconds=None):
        super(CameraScriptBeforePrint, self).__init__(script_path, camera_name, timeout_seconds)
        self.name = "{0} - Before Print Camera Script".format(camera_name)


class CameraScriptAfterPrint(CameraScriptBeforeAfterPrint):
    def __init__(self, script_path, camera_name, timeout_seconds=None):
        super(CameraScriptAfterPrint, self).__init__(script_path, camera_name, timeout_seconds)
        self.name = "{0} - After Print Camera Script".format(camera_name)


class CameraScriptBeforeRender(POpenWithTimeout):
    def __init__(self, script_path, camera_name, snapshot_directory, snapshot_filename_format, snapshot_path_format,
                 timeout_seconds=None):
        super(CameraScriptBeforeRender, self).__init__()
        self.name = "{0} - Before Render Camera Script".format(camera_name)
        self.script_path = script_path
        self.timeout_seconds = timeout_seconds
        self.camera_name = camera_name
        self.snapshot_directory = snapshot_directory
        self.snapshot_filename_format = snapshot_filename_format
        self.snapshot_path_format = snapshot_path_format

    def get_args(self):
        return [
            self.script_path,
            self.camera_name,
            self.snapshot_directory,
            self.snapshot_filename_format,
            self.snapshot_path_format,
        ]

    def run(self):
        return super(CameraScriptBeforeRender, self).run(self.get_args(), self.timeout_seconds)


class CameraScriptAfterRender(POpenWithTimeout):
    def __init__(self, script_path, camera_name, snapshot_directory, snapshot_filename_format, snapshot_path_format,
                 timelapse_directory, timelapse_filename, timelapse_extension, timelapse_full_path,
                 timeout_seconds=None):
        super(CameraScriptAfterRender, self).__init__()
        self.name = "{0} - After Render Camera Script".format(camera_name)
        self.script_path = script_path
        self.timeout_seconds = timeout_seconds
        self.camera_name = camera_name
        self.snapshot_directory = snapshot_directory
        self.snapshot_filename_format = snapshot_filename_format
        self.snapshot_path_format = snapshot_path_format
        self.timelapse_directory = timelapse_directory
        self.timelapse_filename = timelapse_filename
        self.timelapse_extension = timelapse_extension
        self.timelapse_full_path = timelapse_full_path

    def get_args(self):
        return [
            self.script_path,
            self.camera_name,
            self.snapshot_directory,
            self.snapshot_filename_format,
            self.snapshot_path_format,
            self.timelapse_directory,
            self.timelapse_filename,
            self.timelapse_extension,
            self.timelapse_full_path
        ]

    def run(self):
        return super(CameraScriptAfterRender, self).run(self.get_args(), self.timeout_seconds)
