# coding=utf-8
##################################################################################
# Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
# Copyright (C) 2019  Brad Hochgesang
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
import logging
import datetime as datetime
import os
import functools
import types
import six
import copy
from octoprint.logging.handlers import AsyncLogHandlerMixin, CleaningTimedRotatingFileHandler

# custom log level - VERBOSE
VERBOSE = 5
logging.addLevelName(VERBOSE, "VERBOSE")


def verbose(self, msg, *args, **kwargs):
    if self.isEnabledFor(VERBOSE):
        self.log(VERBOSE, msg, *args, **kwargs)


logging.Logger.verbose = verbose
# end custom log level - VERBOSE


#def _get_message_and_format(record):
#    """ Replacement 'get_message' function for logger that calls the string.format using the message args"""
#    # get msg and args from the record
#
#    if record.args:
#        msg = str(record.msg)
#        args = record.args
#        # turn the args into a tuple
#        if not isinstance(args, tuple):
#            args = (args,)
#        # format the message (not kwargs...)
#        ## todo, get to work with kwargs maybe?
#        return msg.format(*args)
#    return record.msg
#
#
#def _handle_wrapper(function):
#    """Wrap handle to use our custom get_message function"""
#    @functools.wraps(function)
#    def handle(record):
#        record.getMessage = types.MethodType(_get_message_and_format, record)
#        return function(record)
#    return handle


def format_log_time(time_seconds):
    log_time = datetime.datetime.fromtimestamp(time_seconds)
    t = datetime.datetime.strftime(log_time, "%Y-%m-%d %H:%M:%S,{0:03}".format(int(log_time.microsecond/1000)))
    return t


class OctolapseFormatter(logging.Formatter):
    def __init__(self, fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt=None):
        super(OctolapseFormatter, self).__init__(fmt=fmt, datefmt=datefmt)

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            return format_log_time(record.created)
        return s


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class OctolapseConsoleHandler(logging.StreamHandler):
    def __init__(self, *args, **kwargs):
        super(OctolapseConsoleHandler, self).__init__(*args, **kwargs)


class OctolapseFileHandler(CleaningTimedRotatingFileHandler):
    def __init__(self, *args, **kwargs):
        super(OctolapseFileHandler, self).__init__(*args, **kwargs)

@six.add_metaclass(Singleton)
class LoggingConfigurator(object):

    def __init__(self):
        self.logging_formatter = OctolapseFormatter()
        self._root_logger_name = 'octolapse'
        self._root_logger = self._get_root_logger(self._root_logger_name)

        self._level = logging.DEBUG
        self._file_handler = None
        self._console_handler = None
        self.child_loggers = set()

    def _get_root_logger(self, name):
        """Get a logger instance that uses new-style string formatting"""
        log = logging.getLogger(name)
        log.setLevel(logging.NOTSET)
        #if not hasattr(log, "_formatted_messages"):
        #    log.handle = _handle_wrapper(log.handle)
        #log._formatted_messages = True
        log.propagate = False
        return log

    def get_logger_names(self):
        logger_names = []
        for logger_name in self.child_loggers:
            logger_names.append(logger_name)
        return logger_names

    def get_root_logger(self):
        return self._root_logger

    def get_logger(self, name):
        if name == self._root_logger_name:
            return self._root_logger

        if name.startswith('octoprint_octolapse.'):
            name = name[20:]

        full_name = 'octolapse.' + name

        self.child_loggers.add(full_name)
        child = self._root_logger.getChild(name)
        #if not hasattr(child, "_formatted_messages"):
        #    child.handle = _handle_wrapper(child.handle)
        #child._formatted_messages = True
        return child

    def _remove_handlers(self):
        if self._file_handler is not None:
            self._root_logger.removeHandler(self._file_handler)
            self._file_handler = None

        if self._console_handler is not None:
            self._root_logger.removeHandler(self._console_handler)
            self._console_handler = None

    def _add_file_handler(self, log_file_path, log_level):
        self._file_handler = OctolapseFileHandler(log_file_path, when="D", backupCount=3)
        self._file_handler.setFormatter(self.logging_formatter)
        self._file_handler.setLevel(log_level)
        self._root_logger.addHandler(self._file_handler)

    def _add_console_handler(self, log_level):
        self._console_handler = OctolapseConsoleHandler()
        self._console_handler.setFormatter(self.logging_formatter)
        self._console_handler.setLevel(log_level)
        self._root_logger.addHandler(self._console_handler)

    def configure_loggers(self, log_file_path=None, debug_settings=None):
        default_log_level = logging.DEBUG
        log_to_console = True
        if debug_settings is not None:
            default_log_level = debug_settings.default_log_level
            log_to_console = debug_settings.log_to_console

        # clear any handlers from the root logger
        self._remove_handlers()
        # set the log level
        self._root_logger.setLevel(logging.NOTSET)

        if debug_settings is None or debug_settings.enabled:
            if log_file_path is not None:
                # ensure that the logging path and file exist
                directory = os.path.dirname(log_file_path)
                import distutils.dir_util
                distutils.dir_util.mkpath(directory)
                if not os.path.isfile(log_file_path):
                    open(log_file_path, 'w').close()

                # add the file handler
                self._add_file_handler(log_file_path, logging.NOTSET)

            # if we are logging to console, add the console logging handler
            if log_to_console:
                self._add_console_handler(logging.NOTSET)
            for logger_full_name in self.child_loggers:

                if logger_full_name.startswith("octolapse."):
                    logger_name = logger_full_name[10:]
                else:
                    logger_name = logger_full_name
                if debug_settings is not None:
                    current_logger = self._root_logger.getChild(logger_name)
                    found_enabled_logger = None
                    for enabled_logger in debug_settings.enabled_loggers:
                        if enabled_logger.name == logger_full_name:
                            found_enabled_logger = enabled_logger
                            break

                    if found_enabled_logger is not None:
                        current_logger.setLevel(found_enabled_logger.log_level)
                    else:
                        # log level critical + 1 will not log anything
                        current_logger.setLevel(logging.CRITICAL + 1)
                else:
                    current_logger = self._root_logger.getChild(logger_name)
                    current_logger.setLevel(default_log_level)
