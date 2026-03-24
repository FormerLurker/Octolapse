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
# Convert all string literals to unicode for Python 2 compatibility
from __future__ import unicode_literals
import os
import time
import datetime
from file_read_backwards import FileReadBackwards
import re
# remove unused usings
# import six
# import string
# create the module level logger
from octoprint_octolapse.log import LoggingConfigurator
logging_configurator = LoggingConfigurator()
logger = logging_configurator.get_logger(__name__)


class GcodeFileProcessor(object):
    def __init__(self, processors, notification_period_seconds, on_update_progress):
        assert(isinstance(processors, list))
        self.processors = processors
        self.update_progress_callback = on_update_progress
        self.notification_period_seconds = notification_period_seconds
        self.current_file_position = 0
        self.file_size_bytes = 0
        self._last_notification_time = None
        self.start_time = None
        self.end_time = None

    def process_file(self, target_file_path, filter_tags=None):

        # get the start time so we can time the process
        self.start_time = time.time()
        self.end_time = None

        # Don't process any lines if there are no processors
        self.current_file_position = 0
        self.file_size_bytes = os.path.getsize(target_file_path)

        # Set the time of our last notification the the current time.
        # We will periodically call on_update_progress to report our
        # current parsing progress
        self._last_notification_time = time.time()

        # trigger start and filter events for all processors
        for processor in self.processors:
            # call the on_before_start functions
            processor.on_before_start()
            # Call the apply filter function
            processor.on_apply_filter(filter_tags)

        # see if there are any rules in the processors
        filtered_processors = []
        for processor in self.processors:
            if processor.can_process():
                filtered_processors.append(processor)

        if len(filtered_processors) == 0:
            return None

        # create a list of forward, reverse and full processors
        forward_processors = [x for x in filtered_processors if x.file_process_type in [u'forward', u'both']]
        reverse_processors = [x for x in filtered_processors if x.file_process_type in [u'reverse', u'both']]

        # process any forward items
        complete = self.process_forwards(forward_processors, target_file_path)
        if not complete:
            complete = self.process_reverse(reverse_processors, target_file_path)

        self.end_time = time.time()
        if complete:
            logger.info("Settings preprocessing finished in %f seconds", self.end_time - self.start_time)
        else:
            logger.info("Settings preprocessing finished in %f seconds, but could not detect all settings", self.end_time - self.start_time)
        self.notify_progress(end_progress=True)
        return self.get_processor_results()

    def process_forwards(self, processors, target_file_path):
        # open the file for streaming
        line_number = 0
        slicer_type_detected = False
        # we're using binary read to avoid file.tell() issues with windows
        with open(target_file_path, 'r') as f:
            while True:
                if len(processors) < 1:
                    break

                line = f.readline()
                if line == '':
                    break

                line_number += 1
                # get the current file position
                self.current_file_position = f.tell()

                for processor in reversed(processors):
                    processor.process_line(line, line_number, 'forward')
                    if processor.max_search_reached(u'forward'):
                        processors.remove(processor)
                    elif processor.is_complete():
                        return True
                if not slicer_type_detected:
                    for processor in processors:
                        if processor.is_slicer_type_detected:
                            # remove the other processors
                            processors = [processor]
                            slicer_type_detected = True
                            break

                self.notify_progress()
        return False

    def process_reverse(self, processors, target_file_path):
        # open the file for streaming
        slicer_type_detected = False
        line_number = 0
        with FileReadBackwards(target_file_path, encoding="utf-8") as frb:
            while True:
                if len(processors) < 1:
                    break

                line = frb.readline()

                if line == '':
                    break

                line_number += 1
                # getting the current file position is not possible
                # with the reverse processor.  Need to write one that works for this purpose.
                #self.current_file_position = f.tell()

                for processor in reversed(processors):
                    processor.process_line(line, line_number, u'reverse')
                    if processor.max_search_reached(u'reverse'):
                        processors.remove(processor)
                    elif processor.is_complete():
                        return True

                if not slicer_type_detected:
                    for processor in processors:
                        if processor.is_slicer_type_detected:
                            # remove the other processors
                            processors = [processor]
                            slicer_type_detected = True
                            continue
        return False

    def notify_progress(self, end_progress=False):
        if self.update_progress_callback is None:
            return
        if end_progress:
            self.update_progress_callback(100, self.end_time - self.start_time)
        elif (
            self.update_progress_callback is not None and
            self._last_notification_time is not None and
            time.time() - self._last_notification_time >= self.notification_period_seconds
        ):
            self.update_progress_callback(self.get_percent_finished(), time.time() - self.start_time)
            self._last_notification_time = time.time()

    def get_percent_finished(self):
        if self.file_size_bytes == 0:
            return 0
        return float(self.current_file_position)/float(self.file_size_bytes) * 100.0

    def get_processor_results(self):
        results = {}
        for processor in self.processors:
            if processor.file_process_category not in results:
                results[processor.file_process_category] = {}

            results[processor.file_process_category][processor.name] = processor.get_results()

        return results

    @staticmethod
    def json_convert(o):
        if isinstance(o, datetime.datetime):
            return o.__str__()


class GcodeProcessor(object):
    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.file_process_type = 'full'
        self.file_process_category = 'none'

    def get_regex_definitions(self):
        raise NotImplementedError(u'You must override get_regexes')

    def process_line(self, line, line_number, process_type):
        raise NotImplementedError(u'You must override process_line')

    def get_results(self):
        raise NotImplementedError(u'You must override get_results')

    def can_process(self):
        raise NotImplementedError(u'You must override can_process')

    def on_before_start(self):
        raise NotImplementedError(u'You must override on_before_start')

    def on_apply_filter(self, filter_tags=None):
        raise NotImplementedError(u'You must override on_apply_filter')

    def is_complete(self):
        raise NotImplementedError(u'You must override is_complete')

    @staticmethod
    def get_comment(self, line):
        # Remove python 2 support
        # assert (isinstance(line, six.string_types))
        assert (isinstance(line, str))
        match_position = line.find(u';')
        if match_position > -1 and len(line) > match_position + 1:
            return line[match_position + 1:].strip()
        return None


class GcodeSettingsProcessor(GcodeProcessor):

    def __init__(self, name, file_procdss_type, max_forward_lines_to_process, max_reverse_lines_to_process):
        super(GcodeSettingsProcessor, self).__init__(name, u'settings_processor')
        # other slicer specific vars
        self.file_process_type = file_procdss_type
        self.file_process_category = u'settings'
        self.max_forward_lines_to_process = max_forward_lines_to_process
        self.max_reverse_lines_to_process = max_reverse_lines_to_process
        self.forward_lines_processed = 0
        self.reverse_lines_processed = 0
        self.all_settings_dictionary = self.get_settings_dictionary()
        self.results = {}
        self.active_settings_dictionary = {}
        self.all_regex_definitions = self.get_regex_definitions()
        self.active_regex_definitions = []
        self.is_slicer_type_detected = False

    def reset(self):
        self.forward_lines_processed = 0
        self.reverse_lines_processed = 0
        self.active_settings_dictionary = {}
        self.results = {}

    def get_regex_definitions(self):
        raise NotImplementedError(u'You must override get_regex_definitions')

    @staticmethod
    def get_settings_dictionary():
        raise NotImplementedError(u'You must override get_settings_dictionary')

    def on_before_start(self):
        # reset everything
        self.reset()

    def on_apply_filter(self, filter_tags=None):
        self.active_settings_dictionary = {}
        self.active_regex_definitions = {}
        # copy any matching settings definitions
        # Remove python 2 support
        # for key, setting in six.iteritems(self.all_settings_dictionary):
        for key, setting in self.all_settings_dictionary.items():
            if (
                filter_tags is None
                or len(filter_tags) == 0
                or (setting.tags is not None and len(setting.tags) > 0 and not setting.tags.isdisjoint(filter_tags))
            ):
                self.active_settings_dictionary[key] = SettingsDefinition(
                    setting.name, setting.parsing_function, setting.tags
                )
        # apply regex filters
        # Remove python 2 support
        # for key, regex in six.iteritems(self.all_regex_definitions):
        for key, regex in self.all_regex_definitions.items():
            if (
                filter_tags is None
                or len(filter_tags) == 0
                or (regex.tags is not None and len(regex.tags) > 0 and not regex.tags.isdisjoint(filter_tags))
            ):
                self.active_regex_definitions[regex.name] = regex

    def can_process(self):
        return len(self.active_settings_dictionary) > 0

    def is_complete(self):
        return (
            len(self.active_settings_dictionary) == 0
            or len(self.active_regex_definitions) == 0
        )

    def max_search_reached(self, process_type):
        return (
            (process_type == u"forward" and self.forward_lines_processed >= self.max_forward_lines_to_process)
            or (process_type == u"reverse" and self.reverse_lines_processed >= self.max_reverse_lines_to_process)
        )

    def process_line(self, line, line_number, process_type):
        line = line.strip()
        if process_type == u"forward":
            self.forward_lines_processed += 1
        elif process_type == u"reverse":
            self.reverse_lines_processed += 1

        logger.verbose("Process type: %s, line: %s, gcode: %s", process_type, line_number, line)
        # Remove python 2 support
        # for key, regex_definition in six.iteritems(self.active_regex_definitions):
        for key, regex_definition in self.active_regex_definitions.items():
            if regex_definition.match_once and regex_definition.has_matched:
                continue
            try:
                match = re.search(regex_definition.regex, line)
            except Exception as e:
                logger.exception(u"Unable to match via regex.")
                raise e
            if not match:
                continue
            regex_definition.has_matched = True
            self.process_match(match, line, regex_definition)
            break

    def process_match(self, matches, line_text, regex):

        # see if we have a matched key
        if regex.match_function is not None:
            regex.match_function(matches)
        else:
            self.default_matching_function(matches)

    def default_matching_function(self, matches):
        # get the key value pair
        key, val = matches.group(u"key", u"val")
        # see if the key matches an active setting
        if key in self.active_settings_dictionary:
            settings_definition = self.active_settings_dictionary[key]

            # if by chance we have a key match that should be ignored, skip
            if settings_definition.ignore_key:
                return

            if settings_definition is not None:
                self.results[settings_definition.name] = settings_definition.parsing_function(val)
                # pop the matched key
                self.active_settings_dictionary.pop(key)

        # todo:  Capture unknown settings

    def get_results(self):
        return self.results


#############################################
# Standard parsing functions
#############################################
class ParsingFunctions(object):

    @staticmethod
    def parse_float(parse_string):
        try:
            return float(parse_string)
        except ValueError:
            return None

    @staticmethod
    def parse_int(parse_string):
        try:
            return int(parse_string)
        except ValueError:
            return None

    @staticmethod
    def parse_int_csv(parse_string):
        str_array = parse_string.split(u',')
        results = []
        for float_string in str_array:
            try:
                results.append(ParsingFunctions.parse_int(float_string))
            except ValueError:
                results.append(None)
        return results

    @staticmethod
    def parse_int_pipe_separated_value(parse_string):
        str_array = parse_string.split(u'|')
        results = []
        for float_string in str_array:
            try:
                results.append(ParsingFunctions.parse_int(float_string))
            except ValueError:
                results.append(None)
        return results

    @staticmethod
    def parse_float_pipe_separated_value(parse_string):
        str_array = parse_string.split(u'|')
        results = []
        for float_string in str_array:
            try:
                results.append(ParsingFunctions.parse_float(float_string))
            except ValueError:
                results.append(None)
        return results

    @staticmethod
    def strip_string(parse_string):
        return parse_string.strip()

    @staticmethod
    def get_string(parse_string):
        return parse_string

    @staticmethod
    def parse_string_csv(parse_string):
        return map(str.strip, parse_string.split(u','))

    @staticmethod
    def parse_string_semicolon_separated_value(parse_string):
        return map(str.strip, parse_string.split(u';'))

    @staticmethod
    def parse_float_csv(parse_string):
        str_array = parse_string.split(u',')
        results = []
        for float_string in str_array:
            try:
                results.append(ParsingFunctions.parse_float(float_string))
            except ValueError:
                results.append(None)
        return results

    @staticmethod
    def parse_bool_csv(parse_string):
        str_array = parse_string.split(u',')
        results = []
        for float_string in str_array:
            try:
                results.append(ParsingFunctions.parse_bool(float_string))
            except ValueError:
                results.append(None)
        return results

    @staticmethod
    def parse_bool(parse_string):
        lower_string = parse_string.lower()
        if lower_string in (u'1', u'yes', u'y', u'true', u't'):
            return True
        elif lower_string in (u'0', u'no', u'n', u'false', u'f'):
            return False
        # didn't match any of our true/false values
        return None


#############################################
# Parsing Function Overriders for Specific
# slicers
# Extends ParsingFunctions
#############################################
class Simplify3dParsingFunctions(ParsingFunctions):

    @staticmethod
    def parse_bool(parse_string):
        if parse_string in (u'1'):
            return True
        elif parse_string in (u'0', u'-1'):
            return False
        # didn't match any of our true/false values
        return None

    @staticmethod
    def parse_bool_csv(parse_string):
        str_array = parse_string.split(u',')
        results = []
        for float_string in str_array:
            try:
                results.append(Simplify3dParsingFunctions.parse_bool(float_string))
            except ValueError:
                results.append(None)
        return results

    @staticmethod
    def parse_profile_version_datetime(parse_string):
        return datetime.datetime.strptime(parse_string.strip(), u"%Y-%m-%d %H:%M:%S")

    @staticmethod
    def try_parse_gcode_create_date(parse_string):
        try:
            return datetime.datetime.strptime(parse_string, u"%b %d, %Y at %I:%M:%S %p")
        except:
            return None

    @staticmethod
    def parse_toolhead_offsets(parse_string):
        str_array = parse_string.split(u'|')
        results = []
        for float_string in str_array:
            try:
                results.append(Simplify3dParsingFunctions.parse_float_csv(float_string))
            except ValueError:
                results.append(None)
        return results

    @staticmethod
    def parse_printer_models_override(parse_string):
        # I don't know how this works!
        # just return the stripped string
        return parse_string.strip()


class Slic3rParsingFunctions(ParsingFunctions):
    @staticmethod
    def parse_mm(parse_string):
        # remove mm from string
        mm_start = parse_string.find(u'mm')
        if mm_start > -1:
            mm_string = parse_string[0: mm_start].strip()
            return float(mm_string)

    @staticmethod
    def parse_filament_used(parse_string):
        # separate the two values
        str_array = parse_string.split(u' ')
        if len(str_array) == 2:
            mm_used = Slic3rParsingFunctions.parse_mm(str_array[0])
            cm3_used = Slic3rParsingFunctions.parse_cm3(str_array[1].encode(u'utf-8').decode().translate({"()": None}))
            return {
                u'mm': mm_used,
                u'cm3': cm3_used
            }

    @staticmethod
    def parse_hhmmss(parse_string):
        # separate the two values
        str_array = parse_string.split(u' ')
        if len(str_array) == 3:
            hh = Slic3rParsingFunctions.parse_int(str_array[0].encode(u'utf-8').decode().translate({ord(c):None for c in 'h'}))
            mm = Slic3rParsingFunctions.parse_int(str_array[1].encode(u'utf-8').decode().translate({ord(c):None for c in 'm'}))
            ss = Slic3rParsingFunctions.parse_int(str_array[2].encode(u'utf-8').decode().translate({ord(c):None for c in 's'}))
            return {
                u'hours': hh,
                u'minutes': mm,
                u'seconds': ss,
            }

    @staticmethod
    def parse_bed_shape(parse_string):
        str_array = parse_string.split(u',')
        flx = None
        fly = None
        frx = None
        fry = None
        rlx = None
        rly = None
        rrx = None
        rry = None

        if len(str_array) == 4:
            fl = str_array[0].split(u'x')
            if len(fl) == 2:
                flx = Slic3rParsingFunctions.parse_float(fl[0])
                fly = Slic3rParsingFunctions.parse_float(fl[1])
            fr = str_array[0].split(u'x')
            if len(fr) == 2:
                frx = Slic3rParsingFunctions.parse_float(fr[0])
                fry = Slic3rParsingFunctions.parse_float(fr[1])
            rl = str_array[0].split(u'x')
            if len(rl) == 2:
                rlx = Slic3rParsingFunctions.parse_float(rl[0])
                rly = Slic3rParsingFunctions.parse_float(rl[1])
            rr = str_array[0].split(u'x')
            if len(rr) == 2:
                rrx = Slic3rParsingFunctions.parse_float(rr[0])
                rry = Slic3rParsingFunctions.parse_float(rr[1])

        return {
            u'front_left': {u'x': flx, u'y': fly},
            u'front_right': {u'x': frx, u'y': fry},
            u'rear_left': {u'x': rlx, u'y': rly},
            u'rear_right': {u'x': rrx, u'y': rry},
        }

    @staticmethod
    def parse_xy_csv(parse_string):
        offsets_array = parse_string.split(',')
        offsets = []
        for offset in offsets_array:
            xy = offset.split('x')
            if len(xy) == 2:
                offsets.append({
                    u'x': Slic3rParsingFunctions.parse_float(xy[0]),
                    u'y': Slic3rParsingFunctions.parse_float(xy[1])
                })

        return offsets

    @staticmethod
    def parse_version(parse_string):
        # get version
        on_string = u' on '
        at_string = u' at '
        on_index = parse_string.find(on_string)
        at_index = parse_string.find(at_string)
        version_number = u'unknown'
        version_date = None
        version_time = None

        if on_index > -1:
            version_number = parse_string[0: on_index]
            if at_index > -1:
                version_date = parse_string[on_index + len(on_string):at_index].strip()
                version_time = parse_string[at_index + len(at_string):].strip()

        return {
            u'version_number': version_number,
            u'version_date': version_date,
            u'version_time': version_time,
        }

    @staticmethod
    def parse_cm3(parse_string):
        # remove mm from string
        mm_start = parse_string.find(u'cm3')
        if mm_start > -1:
            mm_string = parse_string[0: mm_start].strip()
            return float(mm_string)

    @staticmethod
    def parse_percent(parse_string):
        percent_index = parse_string.find(u'%')
        if percent_index < 1:
            return None
        try:
            return float(parse_string.encode(u'utf-8').decode().translate({ord(c):None for c in '%'}))
        except ValueError:
            return 0

    @staticmethod
    def parse_percent_csv(parse_string):
        percents_array = parse_string.split(',')
        percents = []
        for percent in percents_array:
            percent_index = percent.find(u'%')
            if percent_index < 1:
                percents.append(None)
            try:
                percents.append(percent.encode(u'utf-8').decode().translate({ord(c):None for c in '%'}))
            except ValueError:
                percents.append(0)
        return percents

    @staticmethod
    def parse_percent_or_mm(parse_string):
        percent_index = parse_string.find(u'%')
        try:
            if percent_index > -1:
                percent = float(parse_string.encode(u'utf-8').decode().translate({ord(c):None for c in '%'}))
                return {
                    u'percent': percent
                }
            else:
                return {
                    u'mm': float(parse_string)
                }
        except ValueError:
            return None


class CuraParsingFunctions(ParsingFunctions):

    @staticmethod
    def parse_filament_used(parse_string):
        # separate the two values
        str_array = parse_string.split(u' ')
        if len(str_array) == 2:
            mm_used = Slic3rParsingFunctions.parse_mm(str_array[0])
            cm3_used = Slic3rParsingFunctions.parse_cm3(str_array[1].encode(u'utf-8').decode().translate({'()': None}))
            return {
                u'mm': mm_used,
                u'cm3': cm3_used
            }

    @staticmethod
    def parse_version(parse_string):
        # get version
        on_string = u' on '
        at_string = u' at '
        on_index = parse_string.find(on_string)
        at_index = parse_string.find(at_string)
        version_number = u'unknown'
        version_date = None
        version_time = None

        if on_index > -1:
            version_number = parse_string[0: on_index]
            if at_index > -1:
                version_date = parse_string[on_index + len(on_string):at_index].strip()
                version_time = parse_string[at_index + len(at_string):].strip()

        return {
            u'version_number': version_number,
            u'version_date': version_date,
            u'version_time': version_time,
        }


class SettingsDefinition(object):
    def __init__(self, name, parsing_function, tags, ignore_key=False):
        self.name = name
        self.parsing_function = parsing_function
        self.tags = set()
        self.tags = set(tags) if tags is not None else set()
        self.ignore_key = ignore_key


class RegexDefinition(object):
    def __init__(self, name, regex, match_function=None, match_once=False, tags=[]):
        self.name = name
        self.regex_string = regex
        self.regex = re.compile(self.regex_string)
        self.match_function = match_function
        self.match_once = match_once
        self.has_matched = False
        self.tags = set(tags) if tags is not None else set()



    def try_match(self):
        return not (self.match_once and self.has_matched)


#############################################
# Gcode settings processors
# Extends GcodeProcessor
#############################################
class Slic3rSettingsProcessor(GcodeSettingsProcessor):
    def __init__(self, search_direction=u"both", max_forward_search=50, max_reverse_search=263):
        super(Slic3rSettingsProcessor, self).__init__(u'slic3r-pe', search_direction, max_forward_search, max_reverse_search)

    def get_regex_definitions(self):
        return {
            "general_setting": RegexDefinition(u"general_setting", u"^; (?P<key>[^,]*?) = (?P<val>.*)", self.default_matching_function, tags=[u'octolapse_setting']),
            "version": RegexDefinition(u"version", u"^; generated by (?P<ver>.*) on (?P<year>[0-9]?[0-9]?[0-9]?[0-9])-(?P<mon>[0-9]?[0-9])-(?P<day>[0-9]?[0-9]) at (?P<hour>[0-9]?[0-9]):(?P<min>[0-9]?[0-9]):(?P<sec>[0-9]?[0-9])$", self.version_matched, True, tags=[u'octolapse_setting']),
        }

    @staticmethod
    def get_settings_dictionary():
        return {
            # Octolapse Settings
            u'retract_length': SettingsDefinition(u'retract_length', Slic3rParsingFunctions.parse_float_csv,[u'octolapse_setting']),
            u'retract_lift': SettingsDefinition(u'retract_lift', Slic3rParsingFunctions.parse_float_csv, [u'octolapse_setting']),
            u'deretract_speed': SettingsDefinition(u'deretract_speed', Slic3rParsingFunctions.parse_float_csv, [u'octolapse_setting']),
            u'retract_speed': SettingsDefinition(u'retract_speed', Slic3rParsingFunctions.parse_float_csv, [u'octolapse_setting']),
            u'travel_speed': SettingsDefinition(u'travel_speed', Slic3rParsingFunctions.parse_float, [u'octolapse_setting']),
            u'first_layer_speed': SettingsDefinition(u'first_layer_speed', Slic3rParsingFunctions.parse_percent_or_mm,[u'octolapse_setting']),
            # this speed is not yet used

            u'layer_height': SettingsDefinition(u'layer_height', Slic3rParsingFunctions.parse_float, [u'octolapse_setting']),
            u'spiral_vase': SettingsDefinition(u'spiral_vase', Slic3rParsingFunctions.parse_bool, [u'octolapse_setting']),
            u'version': SettingsDefinition(u'version', None, [u'slicer_info', 'octolapse_setting'], True),

            # End Octolapse Settings - The rest are included in case they become useful for Octolapse or another project
            # This setting appears to be calculated and unnecessary
            u'retract_before_travel': SettingsDefinition(u'retract_before_travel', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'single_extruder_multi_material': SettingsDefinition(u'single_extruder_multi_material',
                                                                  Slic3rParsingFunctions.parse_bool, [u'misc']),
            u'max_print_speed': SettingsDefinition(u'max_print_speed', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'perimeter_speed': SettingsDefinition(u'perimeter_speed', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'small_perimeter_speed': SettingsDefinition(u'small_perimeter_speed', Slic3rParsingFunctions.parse_percent_or_mm, [u'misc']),
            u'external_perimeter_speed': SettingsDefinition(u'external_perimeter_speed', Slic3rParsingFunctions.parse_percent_or_mm, [u'misc']),
            u'infill_speed': SettingsDefinition(u'infill_speed', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'solid_infill_speed': SettingsDefinition(u'solid_infill_speed', Slic3rParsingFunctions.parse_percent_or_mm, [u'misc']),
            u'top_solid_infill_speed': SettingsDefinition(u'top_solid_infill_speed', Slic3rParsingFunctions.parse_percent_or_mm, [u'misc']),
            u'support_material_speed': SettingsDefinition(u'support_material_speed', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'bridge_speed': SettingsDefinition(u'bridge_speed', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'gap_fill_speed': SettingsDefinition(u'gap_fill_speed', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'retract_before_wipe': SettingsDefinition(u'retract_before_wipe', Slic3rParsingFunctions.parse_percent_csv, [u'misc']),
            u'wipe': SettingsDefinition(u'wipe', Slic3rParsingFunctions.parse_bool_csv, [u'misc']),
            u'external perimeters extrusion width': SettingsDefinition(u'external_perimeters_extrusion_width', Slic3rParsingFunctions.parse_mm, [u'misc']),
            u'perimeters extrusion width': SettingsDefinition(u'perimeters_extrusion_width', Slic3rParsingFunctions.parse_mm, [u'misc']),
            u'infill extrusion width': SettingsDefinition(u'infill_extrusion_width', Slic3rParsingFunctions.parse_mm, [u'misc']),
            u'solid infill extrusion width': SettingsDefinition(u'solid_infill_extrusion_width', Slic3rParsingFunctions.parse_mm, [u'misc']),
            u'top infill extrusion width': SettingsDefinition(u'top_infill_extrusion_width', Slic3rParsingFunctions.parse_mm,[u'misc']),
            u'first layer extrusion width': SettingsDefinition(u'first_layer_extrusion_width', Slic3rParsingFunctions.parse_mm,[u'misc']),
            u'filament used': SettingsDefinition(u'filament_used', Slic3rParsingFunctions.parse_filament_used, [u'misc']),
            u'total filament cost': SettingsDefinition(u'total_filament_cost', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'estimated printing time': SettingsDefinition(u'estimated_printing_time', Slic3rParsingFunctions.parse_hhmmss,[u'misc']),
            u'avoid_crossing_perimeters': SettingsDefinition(u'avoid_crossing_perimeters', Slic3rParsingFunctions.parse_bool,[u'misc']),
            u'bed_shape': SettingsDefinition(u'bed_shape', Slic3rParsingFunctions.parse_bed_shape, [u'misc']),
            u'bed_temperature': SettingsDefinition(u'bed_temperature', Slic3rParsingFunctions.parse_int_csv, [u'misc']),
            u'before_layer_gcode': SettingsDefinition(u'before_layer_gcode', Slic3rParsingFunctions.get_string, [u'misc']),
            u'between_objects_gcode': SettingsDefinition(u'between_objects_gcode', Slic3rParsingFunctions.get_string, [u'misc']),
            u'bridge_acceleration': SettingsDefinition(u'bridge_acceleration', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'bridge_fan_speed': SettingsDefinition(u'bridge_fan_speed', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'brim_width': SettingsDefinition(u'brim_width', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'complete_objects': SettingsDefinition(u'complete_objects', Slic3rParsingFunctions.parse_bool, [u'misc']),
            u'cooling': SettingsDefinition(u'cooling', Slic3rParsingFunctions.parse_bool_csv, [u'misc']),
            u'cooling_tube_length': SettingsDefinition(u'cooling_tube_length', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'cooling_tube_retraction': SettingsDefinition(u'cooling_tube_retraction', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'default_acceleration': SettingsDefinition(u'default_acceleration', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'disable_fan_first_layers': SettingsDefinition(u'disable_fan_first_layers', Slic3rParsingFunctions.parse_int_csv, [u'misc']),
            u'duplicate_distance': SettingsDefinition(u'duplicate_distance', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'end_filament_gcode': SettingsDefinition(u'end_filament_gcode', Slic3rParsingFunctions.get_string, [u'misc']),
            u'end_gcode': SettingsDefinition(u'end_gcode', Slic3rParsingFunctions.get_string, [u'misc']),
            u'extruder_clearance_height': SettingsDefinition(u'extruder_clearance_height', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'extruder_clearance_radius': SettingsDefinition(u'extruder_clearance_radius', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'extruder_colour': SettingsDefinition(u'extruder_colour', Slic3rParsingFunctions.parse_string_semicolon_separated_value, [u'misc']),
            u'extruder_offset': SettingsDefinition(u'extruder_offset', Slic3rParsingFunctions.parse_xy_csv, [u'misc']),
            u'extrusion_axis': SettingsDefinition(u'extrusion_axis', Slic3rParsingFunctions.get_string, [u'misc']),
            u'extrusion_multiplier': SettingsDefinition(u'extrusion_multiplier', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'fan_always_on': SettingsDefinition(u'fan_always_on', Slic3rParsingFunctions.parse_bool_csv, [u'misc']),
            u'fan_below_layer_time': SettingsDefinition(u'fan_below_layer_time', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'filament_colour': SettingsDefinition(u'filament_colour', Slic3rParsingFunctions.parse_string_semicolon_separated_value, [u'misc']),
            u'filament_cooling_final_speed': SettingsDefinition(u'filament_cooling_final_speed', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'filament_cooling_initial_speed': SettingsDefinition(u'filament_cooling_initial_speed', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'filament_cooling_moves': SettingsDefinition(u'filament_cooling_moves', Slic3rParsingFunctions.parse_int_csv, [u'misc']),

            u'filament_cost': SettingsDefinition(u'filament_cost', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'filament_density': SettingsDefinition(u'filament_density', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'filament_diameter': SettingsDefinition(u'filament_diameter', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'filament_load_time': SettingsDefinition(u'filament_load_time', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'filament_loading_speed': SettingsDefinition(u'filament_loading_speed', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'filament_loading_speed_start': SettingsDefinition(u'filament_loading_speed_start', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'filament_max_volumetric_speed': SettingsDefinition(u'filament_max_volumetric_speed', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'filament_minimal_purge_on_wipe_tower': SettingsDefinition(u'filament_minimal_purge_on_wipe_tower', Slic3rParsingFunctions.parse_float_csv, [u'misc']),

            u'filament_notes': SettingsDefinition(u'filament_notes', Slic3rParsingFunctions.get_string, [u'misc']),
            u'filament_ramming_parameters': SettingsDefinition(u'filament_ramming_parameters', Slic3rParsingFunctions.get_string, [u'misc']),
            u'filament_settings_id': SettingsDefinition(u'filament_settings_id', Slic3rParsingFunctions.parse_string_semicolon_separated_value, [u'misc']),
            u'filament_soluble': SettingsDefinition(u'filament_soluble', Slic3rParsingFunctions.parse_bool_csv, [u'misc']),
            u'filament_toolchange_delay': SettingsDefinition(u'filament_toolchange_delay', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'filament_type': SettingsDefinition(u'filament_type', Slic3rParsingFunctions.parse_string_semicolon_separated_value, [u'misc']),
            u'filament_unload_time': SettingsDefinition(u'filament_unload_time', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'filament_unloading_speed': SettingsDefinition(u'filament_unloading_speed', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'filament_unloading_speed_start': SettingsDefinition(u'filament_unloading_speed_start', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'first_layer_acceleration': SettingsDefinition(u'first_layer_acceleration', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'first_layer_bed_temperature': SettingsDefinition(u'first_layer_bed_temperature', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'first_layer_extrusion_width': SettingsDefinition(u'first_layer_extrusion_width', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'first_layer_temperature': SettingsDefinition(u'first_layer_temperature', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'gcode_comments': SettingsDefinition(u'gcode_comments', Slic3rParsingFunctions.parse_bool, [u'misc']),
            u'gcode_flavor': SettingsDefinition(u'gcode_flavor', Slic3rParsingFunctions.get_string, [u'misc']),
            u'infill_acceleration': SettingsDefinition(u'infill_acceleration', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'infill_first': SettingsDefinition(u'infill_first', Slic3rParsingFunctions.parse_bool, [u'misc']),
            u'layer_gcode': SettingsDefinition(u'layer_gcode', Slic3rParsingFunctions.get_string, [u'misc']),
            u'max_fan_speed': SettingsDefinition(u'max_fan_speed', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'max_layer_height': SettingsDefinition(u'max_layer_height', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'max_print_height': SettingsDefinition(u'max_print_height', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'max_volumetric_extrusion_rate_slope_negative': SettingsDefinition(u'max_volumetric_extrusion_rate_slope_negative', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'max_volumetric_extrusion_rate_slope_positive': SettingsDefinition(u'max_volumetric_extrusion_rate_slope_positive', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'max_volumetric_speed': SettingsDefinition(u'max_volumetric_speed', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'min_fan_speed': SettingsDefinition(u'min_fan_speed', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'min_layer_height': SettingsDefinition(u'min_layer_height', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'min_print_speed': SettingsDefinition(u'min_print_speed', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'min_skirt_length': SettingsDefinition(u'min_skirt_length', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'notes': SettingsDefinition(u'notes', Slic3rParsingFunctions.get_string, [u'misc']),
            u'nozzle_diameter': SettingsDefinition(u'nozzle_diameter', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'only_retract_when_crossing_perimeters': SettingsDefinition(u'only_retract_when_crossing_perimeters', Slic3rParsingFunctions.parse_bool, [u'misc']),
            u'ooze_prevention': SettingsDefinition(u'ooze_prevention', Slic3rParsingFunctions.parse_bool, [u'misc']),
            u'output_filename_format': SettingsDefinition(u'output_filename_format', Slic3rParsingFunctions.get_string, [u'misc']),
            u'parking_pos_retraction': SettingsDefinition(u'parking_pos_retraction', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'perimeter_acceleration': SettingsDefinition(u'perimeter_acceleration', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'post_process': SettingsDefinition(u'post_process', Slic3rParsingFunctions.get_string, [u'misc']),
            u'printer_notes': SettingsDefinition(u'printer_notes', Slic3rParsingFunctions.get_string, [u'misc']),
            u'resolution': SettingsDefinition(u'resolution', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'retract_layer_change': SettingsDefinition(u'retract_layer_change', Slic3rParsingFunctions.parse_bool_csv, [u'misc']),
            u'retract_length_toolchange': SettingsDefinition(u'retract_length_toolchange', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'retract_lift_above': SettingsDefinition(u'retract_lift_above', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'retract_lift_below': SettingsDefinition(u'retract_lift_below', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'retract_restart_extra': SettingsDefinition(u'retract_restart_extra', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'retract_restart_extra_toolchange': SettingsDefinition(u'retract_restart_extra_toolchange', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'single_extruder_multi_material_priming': SettingsDefinition(u'single_extruder_multi_material_priming', Slic3rParsingFunctions.parse_bool, [u'misc']),
            u'skirt_distance': SettingsDefinition(u'skirt_distance', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'skirt_height': SettingsDefinition(u'skirt_height', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'skirts': SettingsDefinition(u'skirts', Slic3rParsingFunctions.parse_bool, [u'misc']),
            u'slowdown_below_layer_time': SettingsDefinition(u'slowdown_below_layer_time', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'standby_temperature_delta': SettingsDefinition(u'standby_temperature_delta', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'start_filament_gcode': SettingsDefinition(u'start_filament_gcode', Slic3rParsingFunctions.get_string, [u'misc']),
            u'start_gcode': SettingsDefinition(u'start_gcode', Slic3rParsingFunctions.get_string, [u'misc']),
            u'temperature': SettingsDefinition(u'temperature', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'threads': SettingsDefinition(u'threads', Slic3rParsingFunctions.parse_int, [u'misc']),
            u'toolchange_gcode': SettingsDefinition(u'toolchange_gcode', Slic3rParsingFunctions.get_string, [u'misc']),
            u'use_firmware_retraction': SettingsDefinition(u'use_firmware_retraction', Slic3rParsingFunctions.parse_bool, [u'misc']),
            u'use_relative_e_distances': SettingsDefinition(u'use_relative_e_distances', Slic3rParsingFunctions.parse_bool, [u'misc']),
            u'use_volumetric_e': SettingsDefinition(u'use_volumetric_e', Slic3rParsingFunctions.parse_bool, [u'misc']),
            u'variable_layer_height': SettingsDefinition(u'variable_layer_height', Slic3rParsingFunctions.parse_bool, [u'misc']),

            u'wipe_tower': SettingsDefinition(u'wipe_tower', Slic3rParsingFunctions.parse_bool, [u'misc']),
            u'wipe_tower_bridging': SettingsDefinition(u'wipe_tower_bridging', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'wipe_tower_rotation_angle': SettingsDefinition(u'wipe_tower_rotation_angle', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'wipe_tower_width': SettingsDefinition(u'wipe_tower_width', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'wipe_tower_x': SettingsDefinition(u'wipe_tower_x', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'wipe_tower_y': SettingsDefinition(u'wipe_tower_y', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'wiping_volumes_extruders': SettingsDefinition(u'wiping_volumes_extruders', Slic3rParsingFunctions.parse_float_csv, [u'misc']),
            u'wiping_volumes_matrix': SettingsDefinition(u'wiping_volumes_matrix', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'z_offset': SettingsDefinition(u'z_offset', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'clip_multipart_objects': SettingsDefinition(u'clip_multipart_objects', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'dont_support_bridges': SettingsDefinition(u'dont_support_bridges', Slic3rParsingFunctions.parse_bool, [u'misc']),
            u'elefant_foot_compensation': SettingsDefinition(u'elefant_foot_compensation', Slic3rParsingFunctions.parse_bool, [u'misc']),
            u'extrusion_width': SettingsDefinition(u'extrusion_width', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'first_layer_height': SettingsDefinition(u'first_layer_height', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'infill_only_where_needed': SettingsDefinition(u'infill_only_where_needed', Slic3rParsingFunctions.parse_bool, [u'misc']),
            u'interface_shells': SettingsDefinition(u'interface_shells', Slic3rParsingFunctions.parse_int, [u'misc']),
            u'raft_layers': SettingsDefinition(u'raft_layers', Slic3rParsingFunctions.parse_int, [u'misc']),
            u'seam_position': SettingsDefinition(u'seam_position', Slic3rParsingFunctions.get_string, [u'misc']),
            u'support_material': SettingsDefinition(u'support_material', Slic3rParsingFunctions.parse_bool, [u'misc']),
            u'support_material_angle': SettingsDefinition(u'support_material_angle', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'support_material_buildplate_only': SettingsDefinition(u'support_material_buildplate_only', Slic3rParsingFunctions.parse_bool, [u'misc']),
            u'support_material_contact_distance': SettingsDefinition(u'support_material_contact_distance', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'support_material_enforce_layers': SettingsDefinition(u'support_material_enforce_layers', Slic3rParsingFunctions.parse_int, [u'misc']),
            u'support_material_extruder': SettingsDefinition(u'support_material_extruder', Slic3rParsingFunctions.parse_int, [u'misc']),
            u'support_material_extrusion_width': SettingsDefinition(u'support_material_extrusion_width', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'support_material_interface_contact_loops': SettingsDefinition(u'support_material_interface_contact_loops', Slic3rParsingFunctions.parse_int, [u'misc']),
            u'support_material_interface_extruder': SettingsDefinition(u'support_material_interface_extruder', Slic3rParsingFunctions.parse_int, [u'misc']),
            u'support_material_interface_layers': SettingsDefinition(u'support_material_interface_layers', Slic3rParsingFunctions.parse_int, [u'misc']),
            u'support_material_interface_spacing': SettingsDefinition(u'support_material_interface_spacing', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'support_material_interface_speed': SettingsDefinition(u'support_material_interface_speed',Slic3rParsingFunctions.parse_percent_or_mm,[u'misc']),
            u'support_material_pattern': SettingsDefinition(u'support_material_pattern', Slic3rParsingFunctions.get_string, [u'misc']),
            u'support_material_spacing': SettingsDefinition(u'support_material_spacing', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'support_material_synchronize_layers': SettingsDefinition(u'support_material_synchronize_layers', Slic3rParsingFunctions.parse_bool, [u'misc']),
            u'support_material_threshold': SettingsDefinition(u'support_material_threshold', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'support_material_with_sheath': SettingsDefinition(u'support_material_with_sheath', Slic3rParsingFunctions.parse_bool, [u'misc']),
            u'support_material_xy_spacing': SettingsDefinition(u'support_material_xy_spacing', Slic3rParsingFunctions.parse_percent_or_mm, [u'misc']),
            u'xy_size_compensation': SettingsDefinition(u'xy_size_compensation', Slic3rParsingFunctions.parse_bool, [u'misc']),
            u'bottom_solid_layers': SettingsDefinition(u'bottom_solid_layers', Slic3rParsingFunctions.parse_int, [u'misc']),
            u'bridge_angle': SettingsDefinition(u'bridge_angle', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'bridge_flow_ratio': SettingsDefinition(u'bridge_flow_ratio', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'ensure_vertical_shell_thickness': SettingsDefinition(u'ensure_vertical_shell_thickness', Slic3rParsingFunctions.parse_bool, [u'misc']),
            u'external_fill_pattern': SettingsDefinition(u'external_fill_pattern', Slic3rParsingFunctions.get_string, [u'misc']),
            u'external_perimeter_extrusion_width': SettingsDefinition(u'external_perimeter_extrusion_width', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'external_perimeters_first': SettingsDefinition(u'external_perimeters_first', Slic3rParsingFunctions.parse_percent_or_mm, [u'misc']),
            u'extra_perimeters': SettingsDefinition(u'extra_perimeters', Slic3rParsingFunctions.parse_int, [u'misc']),
            u'fill_angle': SettingsDefinition(u'fill_angle', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'fill_density': SettingsDefinition(u'fill_density', Slic3rParsingFunctions.parse_percent, [u'misc']),
            u'fill_pattern': SettingsDefinition(u'fill_pattern', Slic3rParsingFunctions.get_string, [u'misc']),
            u'infill_every_layers': SettingsDefinition(u'infill_every_layers', Slic3rParsingFunctions.parse_bool, [u'misc']),
            u'infill_extruder': SettingsDefinition(u'infill_extruder', Slic3rParsingFunctions.parse_int, [u'misc']),
            u'infill_extrusion_width': SettingsDefinition(u'infill_extrusion_width', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'infill_overlap': SettingsDefinition(u'infill_overlap', Slic3rParsingFunctions.parse_percent, [u'misc']),
            u'overhangs': SettingsDefinition(u'overhangs', Slic3rParsingFunctions.parse_bool, [u'misc']),
            u'perimeter_extruder': SettingsDefinition(u'perimeter_extruder', Slic3rParsingFunctions.parse_int, [u'misc']),
            u'perimeter_extrusion_width': SettingsDefinition(u'perimeter_extrusion_width', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'perimeters': SettingsDefinition(u'perimeters', Slic3rParsingFunctions.parse_int, [u'misc']),
            u'solid_infill_below_area': SettingsDefinition(u'solid_infill_below_area', Slic3rParsingFunctions.parse_bool, [u'misc']),
            u'solid_infill_every_layers': SettingsDefinition(u'solid_infill_every_layers', Slic3rParsingFunctions.parse_bool, [u'misc']),
            u'solid_infill_extruder': SettingsDefinition(u'solid_infill_extruder', Slic3rParsingFunctions.parse_int, [u'misc']),
            u'solid_infill_extrusion_width': SettingsDefinition(u'solid_infill_extrusion_width', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'thin_walls': SettingsDefinition(u'thin_walls', Slic3rParsingFunctions.parse_bool, [u'misc']),
            u'top_infill_extrusion_width': SettingsDefinition(u'top_infill_extrusion_width', Slic3rParsingFunctions.parse_float, [u'misc']),
            u'top_solid_layers': SettingsDefinition(u'top_solid_layers', Slic3rParsingFunctions.parse_int, [u'misc']),
        }

    def version_matched(self, matches):
        if "version" in self.active_settings_dictionary:
            setting = self.active_settings_dictionary["version"]
            if setting is not None:
                version, year, month, day, hour, min, sec = matches.group("ver", "year", "mon", "day", "hour", "min", "sec")
                self.results["version"] = {
                    "version": version,
                    "date": "{year}-{month}-{day} {hour}:{min}:{sec}".format(
                        year=year, month=month, day=day, hour=hour, min=min, sec=sec
                    )
                }
                self.active_settings_dictionary.pop(u'version')
                self.active_regex_definitions.pop('version')
                self.is_slicer_type_detected = True


class Simplify3dSettingsProcessor(GcodeSettingsProcessor):
    def __init__(self, search_direction="forward", max_forward_search=295, max_reverse_search=0):
        super(Simplify3dSettingsProcessor, self).__init__(u'simplify-3d', search_direction, max_forward_search, max_reverse_search)

    def get_regex_definitions(self):
        return {
            "general_setting": RegexDefinition("general_setting", r"^;\s\s\s(?P<key>.*?),(?P<val>.*)$", self.default_matching_function, tags=[u'octolapse_setting']),
            "printer_models_override": RegexDefinition("printer_models_override", r"^;\s\s\sprinterModelsOverride$", self.printer_modesl_override_matched, True),
            "version": RegexDefinition("version", r";\sG\-Code\sgenerated\sby\sSimplify3D\(R\)\sVersion\s(?P<ver>.*)$", self.version_matched, True, tags=[u'octolapse_setting']),
            "gocde_date": RegexDefinition("gocde_date", r"^; (?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s(?P<day>[0-9]?[0-9]), (?P<year>[0-9]?[0-9]?[0-9]?[0-9]) at (?P<hour>[0-9]?[0-9]):(?P<min>[0-9]?[0-9]):(?P<sec>[0-9]?[0-9])\s(?P<period>AM|PM)$", self.gcode_date_matched, True)
        }

    @staticmethod
    def get_settings_dictionary():
        return {
            # Octolapse Settings
            u'extruderToolheadNumber': SettingsDefinition(u'extruder_tool_number', Simplify3dParsingFunctions.parse_int_csv, [u'octolapse_setting']),
            u'primaryExtruder': SettingsDefinition(u'primary_extruder', Simplify3dParsingFunctions.parse_int,[u'extruder',u'octolapse_setting']),
            u'extruderRetractionDistance': SettingsDefinition(u'extruder_retraction_distance',Simplify3dParsingFunctions.parse_float_csv,[u'extruder', u'octolapse_setting']),
            u'extruderRetractionZLift': SettingsDefinition(u'extruder_retraction_z_lift',Simplify3dParsingFunctions.parse_float_csv,[u'extruder', u'octolapse_setting']),
            u'extruderRetractionSpeed': SettingsDefinition(u'extruder_retraction_speed',Simplify3dParsingFunctions.parse_float_csv,[u'extruder', u'octolapse_setting']),
            u'rapidXYspeed': SettingsDefinition(u'rapid_xy_speed', Simplify3dParsingFunctions.parse_float,[u'octolapse_setting']),
            u'rapidZspeed': SettingsDefinition(u'rapid_z_speed', Simplify3dParsingFunctions.parse_float,[u'octolapse_setting']),
            u'extruderUseRetract': SettingsDefinition(u'extruder_use_retract', Simplify3dParsingFunctions.parse_bool_csv,[u'extruder', u'octolapse_setting']),
            u'spiralVaseMode': SettingsDefinition(u'spiral_vase_mode', Simplify3dParsingFunctions.parse_bool, [u'octolapse_setting']),
            u'layerHeight': SettingsDefinition(u'layer_height', Simplify3dParsingFunctions.parse_float, [u'octolapse_setting']),
            # End Octolapse Settings - The rest is included in case it is ever useful for Octolapse of another project!
            u'bridgingSpeedMultiplier': SettingsDefinition(u'bridging_speed_multiplier', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'firstLayerUnderspeed': SettingsDefinition(u'first_layer_underspeed', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'aboveRaftSpeedMultiplier': SettingsDefinition(u'above_raft_speed_multiplier', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'primePillarSpeedMultiplier': SettingsDefinition(u'prime_pillar_speed_multiplier', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'oozeShieldSpeedMultiplier': SettingsDefinition(u'ooze_shield_speed_multiplier', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'defaultSpeed': SettingsDefinition(u'default_speed', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'outlineUnderspeed': SettingsDefinition(u'outline_underspeed', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'solidInfillUnderspeed': SettingsDefinition(u'solid_infill_underspeed', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'supportUnderspeed': SettingsDefinition(u'support_underspeed', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'version': SettingsDefinition(u'version', Simplify3dParsingFunctions.strip_string, [u'slicer_info'], True),
            u'gcodeDate': SettingsDefinition(u'gcode_date', Simplify3dParsingFunctions.strip_string, [u'gcode_info'], True),
            # IMPORTANT NOTE - printerModelsOverride does NOT have a comma if it's empty
            u'printerModelsOverride': SettingsDefinition(u'printer_models_override', Simplify3dParsingFunctions.parse_printer_models_override, [u'misc']),
            u'processName': SettingsDefinition(u'process_name', Simplify3dParsingFunctions.strip_string, [u'misc']),
            u'applyToModels': SettingsDefinition(u'apply_to_models', Simplify3dParsingFunctions.parse_string_csv, [u'misc']),
            u'profileName':SettingsDefinition(u'profile_name', Simplify3dParsingFunctions.strip_string, [u'profile']),
            u'profileVersion':SettingsDefinition(u'profile_version', Simplify3dParsingFunctions.parse_profile_version_datetime, [u'profile']),
            u'baseProfile':SettingsDefinition(u'profile_base', Simplify3dParsingFunctions.strip_string, [u'profile']),
            u'printMaterial': SettingsDefinition(u'print_material', Simplify3dParsingFunctions.strip_string, [u'material']),
            u'printQuality':SettingsDefinition(u'print_quality', Simplify3dParsingFunctions.strip_string, [u'misc']),
            u'printExtruders':SettingsDefinition(u'print_extruders', Simplify3dParsingFunctions.parse_string_csv, [u'extruder']),
            u'extruderName': SettingsDefinition(u'extruder_names',  Simplify3dParsingFunctions.parse_string_csv, [u'extruder']),
            u'extruderDiameter': SettingsDefinition(u'extrueder_diameter',  Simplify3dParsingFunctions.parse_float_csv, [u'extruder']),
            u'extruderAutoWidth': SettingsDefinition(u'extruder_auto_width', Simplify3dParsingFunctions.parse_bool_csv, [u'extruder']),
            u'extruderWidth': SettingsDefinition(u'extruder_width', Simplify3dParsingFunctions.parse_float_csv, [u'extruder']),
            u'extrusionMultiplier': SettingsDefinition(u'extrusion_multiplier', Simplify3dParsingFunctions.parse_float_csv, [u'extruder']),
            u'extruderExtraRestartDistance': SettingsDefinition(u'extruder_extra_restart_distance', Simplify3dParsingFunctions.parse_float_csv, [u'extruder']),
            u'extruderUseCoasting': SettingsDefinition(u'extruder_use_coasting', Simplify3dParsingFunctions.parse_bool_csv, [u'extruder']),
            u'extruderCoastingDistance': SettingsDefinition(u'extruder_coasting_distance', Simplify3dParsingFunctions.parse_float_csv, [u'extruder']),
            u'extruderUseWipe': SettingsDefinition(u'extruder_use_wipe', Simplify3dParsingFunctions.parse_bool_csv, [u'extruder']),
            u'extruderWipeDistance': SettingsDefinition(u'extruder_wipe_distance', Simplify3dParsingFunctions.parse_float_csv, [u'extruder']),
            u'topSolidLayers': SettingsDefinition(u'top_solid_layers', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'bottomSolidLayers': SettingsDefinition(u'bottom_solid_layers', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'perimeterOutlines': SettingsDefinition(u'perimeter_outlines', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'printPerimetersInsideOut': SettingsDefinition(u'print_perimeters_inside_out',  Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'startPointOption': SettingsDefinition(u'start_print_options', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'startPointOriginX': SettingsDefinition(u'start_point_origin_x', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'startPointOriginY': SettingsDefinition(u'start_point_origin_y', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'sequentialIslands': SettingsDefinition(u'sequential_islands', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'firstLayerHeightPercentage': SettingsDefinition(u'first_layer_height_percentage', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'firstLayerWidthPercentage': SettingsDefinition(u'first_layer_width_percentage', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'useRaft': SettingsDefinition(u'use_raft', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'raftExtruder': SettingsDefinition(u'raft_extruder', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'raftTopLayers': SettingsDefinition(u'raft_top_layers', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'raftBaseLayers':  SettingsDefinition(u'raft_base_layers', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'raftOffset': SettingsDefinition(u'raft_offset', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'raftSeparationDistance': SettingsDefinition(u'raft_separation_distance', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'raftTopInfill': SettingsDefinition(u'raft_top_infill', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'useSkirt':  SettingsDefinition(u'use_skirt', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'skirtExtruder': SettingsDefinition(u'skirt_extruder', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'skirtLayers': SettingsDefinition(u'skirt_layers', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'skirtOutlines': SettingsDefinition(u'skirt_outlines', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'skirtOffset': SettingsDefinition(u'skirt_offset', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'usePrimePillar': SettingsDefinition(u'use_prime_pillar', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'primePillarExtruder': SettingsDefinition(u'prime_pillar_extruder',  Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'primePillarWidth': SettingsDefinition(u'prime_pillar_width', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'primePillarLocation': SettingsDefinition(u'prime_pillar_location', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'useOozeShield': SettingsDefinition(u'use_ooze_shield', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'oozeShieldExtruder': SettingsDefinition(u'ooze_shield_extruder',  Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'oozeShieldOffset': SettingsDefinition(u'ooze_shield_offset', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'oozeShieldOutlines': SettingsDefinition(u'ooze_shield_outlines', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'oozeShieldSidewallShape': SettingsDefinition(u'ooze_shield_sidewall_shape', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'oozeShieldSidewallAngle': SettingsDefinition(u'ooze_shield_sidewall_angle', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'infillExtruder':  SettingsDefinition(u'infill_extruder',  Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'internalInfillPattern': SettingsDefinition(u'internal_infill_pattern',  Simplify3dParsingFunctions.strip_string, [u'misc']),
            u'externalInfillPattern': SettingsDefinition(u'external_infill_pattern', Simplify3dParsingFunctions.strip_string, [u'misc']),
            u'infillPercentage': SettingsDefinition(u'infill_percentage', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'outlineOverlapPercentage': SettingsDefinition(u'outline_overlap_percentage', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'infillExtrusionWidthPercentage': SettingsDefinition(u'infill_extrusion_width_percentage',  Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'minInfillLength': SettingsDefinition(u'min_infill_length', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'infillLayerInterval': SettingsDefinition(u'infill_layer_interval', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'internalInfillAngles': SettingsDefinition(u'internal_infill_angles', Simplify3dParsingFunctions.parse_int_csv, [u'misc']),
            u'overlapInternalInfillAngles': SettingsDefinition(u'overlap_internal_infill_angles', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'externalInfillAngles': SettingsDefinition(u'external_infill_angles', Simplify3dParsingFunctions.parse_int_csv, [u'misc']),
            u'generateSupport': SettingsDefinition(u'generate_support',  Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'supportExtruder': SettingsDefinition(u'support_extruder',  Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'supportInfillPercentage': SettingsDefinition(u'support_infill_percentage', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'supportExtraInflation': SettingsDefinition(u'support_extra_inflation',  Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'supportBaseLayers': SettingsDefinition(u'support_base_layers',  Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'denseSupportExtruder': SettingsDefinition(u'dense_support_extruder', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'denseSupportLayers': SettingsDefinition(u'dense_support_layers',  Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'denseSupportInfillPercentage': SettingsDefinition(u'dense_support_infill_percentage',  Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'supportLayerInterval': SettingsDefinition(u'support_layer_interval',  Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'supportHorizontalPartOffset': SettingsDefinition(u'support_horizontal_part_offset',  Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'supportUpperSeparationLayers': SettingsDefinition(u'support_upper_separation_layers', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'supportLowerSeparationLayers': SettingsDefinition(u'support_lower_separation_layers', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'supportType': SettingsDefinition(u'support_type', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'supportGridSpacing': SettingsDefinition(u'support_grid_spacing', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'maxOverhangAngle': SettingsDefinition(u'max_overhead_angle', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'supportAngles': SettingsDefinition(u'support_angles', Simplify3dParsingFunctions.parse_int_csv, [u'misc']),
            u'temperatureName': SettingsDefinition(u'temperature_name', Simplify3dParsingFunctions.parse_string_csv, [u'misc']),
            u'temperatureNumber': SettingsDefinition(u'temperature_number', Simplify3dParsingFunctions.parse_int_csv, [u'misc']),
            u'temperatureSetpointCount': SettingsDefinition(u'temperature_setpoint_count', Simplify3dParsingFunctions.parse_int_csv, [u'misc']),
            u'temperatureSetpointLayers': SettingsDefinition(u'temperature_setpoint_layers',  Simplify3dParsingFunctions.parse_int_csv, [u'misc']),
            u'temperatureSetpointTemperatures': SettingsDefinition(u'temperature_setpoint_temperatures',  Simplify3dParsingFunctions.parse_int_csv, [u'misc']),
            u'temperatureStabilizeAtStartup': SettingsDefinition(u'temperature_stabilize_at_startup',  Simplify3dParsingFunctions.parse_bool_csv, [u'misc']),
            u'temperatureHeatedBed': SettingsDefinition(u'temperature_heated_bed',  Simplify3dParsingFunctions.parse_bool_csv, [u'misc']),
            u'temperatureRelayBetweenLayers': SettingsDefinition(u'temperature_relay_between_layers', Simplify3dParsingFunctions.parse_bool_csv, [u'misc']),
            u'temperatureRelayBetweenLoops': SettingsDefinition(u'temperature_relay_between_loops', Simplify3dParsingFunctions.parse_bool_csv, [u'misc']),
            u'fanLayers': SettingsDefinition(u'fan_layers', Simplify3dParsingFunctions.parse_int_csv, [u'misc']),
            u'fanSpeeds': SettingsDefinition(u'fan_speeds', Simplify3dParsingFunctions.parse_int_csv, [u'misc']),
            u'blipFanToFullPower': SettingsDefinition(u'blip_fan_to_full_power',  Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'adjustSpeedForCooling': SettingsDefinition(u'adjust_speed_for_cooling',  Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'minSpeedLayerTime': SettingsDefinition(u'min_speed_layer_time',  Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'minCoolingSpeedSlowdown': SettingsDefinition(u'min_cooling_speed_slowdown',  Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'increaseFanForCooling': SettingsDefinition(u'increase_fan_for_cooling',  Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'minFanLayerTime': SettingsDefinition(u'min_fan_layer_time',  Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'maxCoolingFanSpeed': SettingsDefinition(u'max_cooling_fan_speed', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'increaseFanForBridging': SettingsDefinition(u'increase_fan_for_bridging', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'bridgingFanSpeed': SettingsDefinition(u'bridging_fan_speed',  Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'use5D': SettingsDefinition(u'use_5d',  Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'relativeEdistances': SettingsDefinition(u'relative_e_distances',  Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'allowEaxisZeroing': SettingsDefinition(u'allow_e_axis_zeroing', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'independentExtruderAxes': SettingsDefinition(u'independent_extruder_axes', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'includeM10123': SettingsDefinition(u'include_m_101_102_103_commands', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'stickySupport': SettingsDefinition(u'sticky_support', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'applyToolheadOffsets': SettingsDefinition(u'apply_toolhead_offsets', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'gcodeXoffset': SettingsDefinition(u'gcode_x_offset', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'gcodeYoffset': SettingsDefinition(u'gcode_y_offset', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'gcodeZoffset': SettingsDefinition(u'gcode_z_offset', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'overrideMachineDefinition': SettingsDefinition(u'override_machine_definition', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'machineTypeOverride': SettingsDefinition(u'machine_type_override', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'strokeXoverride': SettingsDefinition(u'stroke_x_override', Simplify3dParsingFunctions.parse_float, [u'printer_volume']),
            u'strokeYoverride': SettingsDefinition(u'stroke_y_override', Simplify3dParsingFunctions.parse_float, [u'printer_volume']),
            u'strokeZoverride': SettingsDefinition(u'stroke_z_override', Simplify3dParsingFunctions.parse_float, [u'printer_volume']),
            u'originOffsetXoverride': SettingsDefinition(u'origin_offset_x_override', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'originOffsetYoverride': SettingsDefinition(u'origin_offset_y_override', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'originOffsetZoverride': SettingsDefinition(u'origin_offset_z_override', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'homeXdirOverride': SettingsDefinition(u'home_x_direction_override',  Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'homeYdirOverride': SettingsDefinition(u'home_y_direction_override', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'homeZdirOverride': SettingsDefinition(u'home_z_direction_override', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'flipXoverride': SettingsDefinition(u'flip_x_override', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'flipYoverride': SettingsDefinition(u'flip_y_override', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'flipZoverride': SettingsDefinition(u'flip_z_override', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'toolheadOffsets': SettingsDefinition(u'toolhead_offsets', Simplify3dParsingFunctions.parse_toolhead_offsets, [u'misc']),
            u'overrideFirmwareConfiguration': SettingsDefinition(u'override_firmware_configuration', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'firmwareTypeOverride': SettingsDefinition(u'firmware_type_override', Simplify3dParsingFunctions.strip_string, [u'misc']),
            u'GPXconfigOverride': SettingsDefinition(u'gpx_config_override',  Simplify3dParsingFunctions.strip_string, [u'misc']),
            u'baudRateOverride': SettingsDefinition(u'baud_rate_override',  Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'overridePrinterModels': SettingsDefinition(u'override_printer_models', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'startingGcode': SettingsDefinition(u'starting_gcode', Simplify3dParsingFunctions.parse_string_csv, [u'misc']),
            u'layerChangeGcode': SettingsDefinition(u'layer_change_gcode', Simplify3dParsingFunctions.parse_string_csv, [u'misc']),
            u'retractionGcode': SettingsDefinition(u'retraction_gcode', Simplify3dParsingFunctions.parse_string_csv, [u'misc']),
            u'toolChangeGcode': SettingsDefinition(u'tool_change_gcode', Simplify3dParsingFunctions.parse_string_csv, [u'misc']),
            u'endingGcode': SettingsDefinition(u'ending_gcode', Simplify3dParsingFunctions.parse_string_csv, [u'misc']),
            u'exportFileFormat': SettingsDefinition(u'export_file_format', Simplify3dParsingFunctions.strip_string, [u'misc']),
            u'celebration': SettingsDefinition(u'celebration',Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'celebrationSong': SettingsDefinition(u'celebration_song', Simplify3dParsingFunctions.strip_string, [u'misc']),
            u'postProcessing': SettingsDefinition(u'post_processing', Simplify3dParsingFunctions.parse_string_csv, [u'misc']),
            u'minBridgingArea': SettingsDefinition(u'min_bridging_area', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'bridgingExtraInflation': SettingsDefinition(u'bridging_extra_inflation', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'bridgingExtrusionMultiplier': SettingsDefinition(u'bridging_extrusion_multiplier', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'useFixedBridgingAngle': SettingsDefinition(u'use_fixed_bridging_angle', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'fixedBridgingAngle': SettingsDefinition(u'fixed_bridging_angle', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'applyBridgingToPerimeters': SettingsDefinition(u'apply_bridging_to_perimeters', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'filamentDiameters': SettingsDefinition(u'filament_diameters', Simplify3dParsingFunctions.parse_float_pipe_separated_value, [u'misc']),
            u'filamentPricesPerKg': SettingsDefinition(u'filament_prices_per_kg',  Simplify3dParsingFunctions.parse_float_pipe_separated_value, [u'misc']),
            u'filamentDensities': SettingsDefinition(u'filament_densities', Simplify3dParsingFunctions.parse_float_pipe_separated_value, [u'misc']),
            u'useMinPrintHeight': SettingsDefinition(u'use_min_print_height', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'minPrintHeight': SettingsDefinition(u'min_print_height', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'useMaxPrintHeight': SettingsDefinition(u'use_max_print_height', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'maxPrintHeight': SettingsDefinition(u'max_print_height', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'useDiaphragm': SettingsDefinition(u'use_diaphragm', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'diaphragmLayerInterval': SettingsDefinition(u'diaphragm_layer_interval', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'robustSlicing': SettingsDefinition(u'robust_slicing', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'mergeAllIntoSolid': SettingsDefinition(u'merge_all_into_solid', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'onlyRetractWhenCrossingOutline': SettingsDefinition(u'only_retract_when_crossing_outline', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'retractBetweenLayers': SettingsDefinition(u'retract_between_layers', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'useRetractionMinTravel': SettingsDefinition(u'use_retraction_min_travel', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'retractionMinTravel': SettingsDefinition(u'retraction_min_travel', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'retractWhileWiping': SettingsDefinition(u'retract_while_wiping', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'onlyWipeOutlines': SettingsDefinition(u'only_wipe_outlines', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'avoidCrossingOutline': SettingsDefinition(u'avoid_crossing_outline', Simplify3dParsingFunctions.parse_bool, [u'misc']),
            u'maxMovementDetourFactor': SettingsDefinition(u'max_movement_detour_factor', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'toolChangeRetractionDistance': SettingsDefinition(u'tool_change_retraction_distance', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'toolChangeExtraRestartDistance': SettingsDefinition(u'tool_change_extra_restart_distance', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'toolChangeRetractionSpeed': SettingsDefinition(u'tool_change_retraction_speed', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'externalThinWallType': SettingsDefinition(u'external_thin_wall_type', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'internalThinWallType': SettingsDefinition(u'internal_thin_wall_type', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'thinWallAllowedOverlapPercentage': SettingsDefinition(u'thin_wall_allowed_overlap_percentage', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'singleExtrusionMinLength': SettingsDefinition(u'single_extrusion_min_length',  Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'singleExtrusionMinPrintingWidthPercentage': SettingsDefinition(u'single_extrusion_min_printing_width_percentage', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'singleExtrusionMaxPrintingWidthPercentage': SettingsDefinition(u'single_extrusion_max_printing_width_percentage', Simplify3dParsingFunctions.parse_int, [u'misc']),
            u'singleExtrusionEndpointExtension': SettingsDefinition(u'single_extrusion_endpoint_extension', Simplify3dParsingFunctions.parse_float, [u'misc']),
            u'horizontalSizeCompensation': SettingsDefinition(u'horizontal_size_compensation', Simplify3dParsingFunctions.parse_float, [u'misc']),
        }

    def get_results(self):
        return self.results

    def version_matched(self, matches):
        if "version" in self.active_settings_dictionary:
            setting = self.active_settings_dictionary["version"]
            if setting is not None:
                version = matches.group("ver")
                self.results["version"] = version
                self.active_settings_dictionary.pop(u'version')
                self.active_regex_definitions.pop('version')
                self.is_slicer_type_detected = True

    def gcode_date_matched(self, matches):
        if "gcodeDate" in self.active_settings_dictionary:
            setting = self.active_settings_dictionary["gcodeDate"]
            if setting is not None:
                month, day, year, hour, min, sec, period = matches.group("month", "day", "year", "hour", "min", "sec",
                                                                         "period")
                self.results["gcode_date"] = "{year}-{month}-{day} {hour}:{min}:{sec} {period}".format(
                    year=year, month=month, day=day, hour=hour, min=min, sec=sec, period=period
                )
                self.active_settings_dictionary.pop(u'gcodeDate')
                self.active_regex_definitions.pop('gocde_date')

    def printer_modesl_override_matched(self, matches):
        if "printerModelsOverride" in self.active_settings_dictionary:
            setting = self.active_settings_dictionary["printerModelsOverride"]
            if setting is not None:
                self.results[setting.name] = None
                self.active_settings_dictionary.pop(u'printerModelsOverride')
                self.active_regex_definitions.pop('printer_models_override')


class CuraSettingsProcessor(GcodeSettingsProcessor):
    def __init__(self, search_direction="both", max_forward_search=550, max_reverse_search=550):
        super(CuraSettingsProcessor, self).__init__(u'cura', search_direction, max_forward_search, max_reverse_search)

    def get_regex_definitions(self):
        return {
            "general_setting": RegexDefinition(u"general_setting", u"^; (?P<key>[^,]*?) = (?P<val>.*)", self.default_matching_function, tags=[u'octolapse_setting']),
            "version": RegexDefinition(u"version", r"^;Generated\swith\sCura_SteamEngine\s(?P<ver>.*)$", self.version_matched,True, tags=[u'octolapse_setting']),
            "filament_used_meters": RegexDefinition(r"filament_used_meters", r"^;Filament\sused:\s(?P<meters>.*)m$", self.filament_used_meters_matched, True),
            "firmware_flavor": RegexDefinition(u"firmware_flavor", u"^;FLAVOR:(?P<flavor>.*)$", self.firmware_flavor_matched, True),
            "layer_height": RegexDefinition(r"layer_height", r"^;Layer\sheight:\s(?P<height>.*)$", self.layer_height_matched, True),
        }

    @staticmethod
    def get_settings_dictionary():
        return {
            # Octolapse Settings
            # controls z speed for cura version < 4.2
            u'max_feedrate_z_override': SettingsDefinition(u'max_feedrate_z_override', CuraParsingFunctions.parse_float,[u'octolapse_setting']),
            # controls z speed for cura version >= 4.2
            u'speed_z_hop': SettingsDefinition(u'speed_z_hop', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_amount': SettingsDefinition(u'retraction_amount', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_hop': SettingsDefinition(u'retraction_hop', CuraParsingFunctions.parse_float,[u'octolapse_setting']),
            u'retraction_hop_enabled': SettingsDefinition(u'retraction_hop_enabled', CuraParsingFunctions.parse_bool,[u'octolapse_setting']),
            u'retraction_prime_speed': SettingsDefinition(u'retraction_prime_speed', CuraParsingFunctions.parse_float,[u'octolapse_setting']),
            u'retraction_retract_speed': SettingsDefinition(u'retraction_retract_speed', CuraParsingFunctions.parse_float,[u'octolapse_setting']),
            u'retraction_speed': SettingsDefinition(u'retraction_speed', CuraParsingFunctions.parse_float, [u'octolapse_setting']),

            # Note that the below speed doesn't represent the initial layer or travel speed.  See speed_print_layer_0
            # however, a test will need to be performed.
            u'speed_travel': SettingsDefinition(u'speed_travel', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_enable': SettingsDefinition(u'retraction_enable', CuraParsingFunctions.parse_bool, [u'octolapse_setting']),
            u'version': SettingsDefinition(u'version', CuraParsingFunctions.strip_string, [u'octolapse_setting']),
            u'layer_height': SettingsDefinition(u'layer_height', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'smooth_spiralized_contours': SettingsDefinition(u'smooth_spiralized_contours', CuraParsingFunctions.parse_bool, [u'octolapse_setting']),
            u'machine_extruder_count': SettingsDefinition(u'machine_extruder_count', CuraParsingFunctions.parse_int, [u'octolapse_setting']),
            # Extruder Specific Settings
            # speed_z_hop - Cura 5.1-
            u'max_feedrate_z_override_0': SettingsDefinition(u'max_feedrate_z_override_0', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'max_feedrate_z_override_1': SettingsDefinition(u'max_feedrate_z_override_1', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'max_feedrate_z_override_2': SettingsDefinition(u'max_feedrate_z_override_2', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'max_feedrate_z_override_3': SettingsDefinition(u'max_feedrate_z_override_3', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'max_feedrate_z_override_4': SettingsDefinition(u'max_feedrate_z_override_4', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'max_feedrate_z_override_5': SettingsDefinition(u'max_feedrate_z_override_5', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'max_feedrate_z_override_6': SettingsDefinition(u'max_feedrate_z_override_6', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'max_feedrate_z_override_7': SettingsDefinition(u'max_feedrate_z_override_7', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            # speed_z_hop - Cura 4.2+
            u'speed_z_hop_0': SettingsDefinition(u'speed_z_hop_0', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'speed_z_hop_1': SettingsDefinition(u'speed_z_hop_1', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'speed_z_hop_2': SettingsDefinition(u'speed_z_hop_2', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'speed_z_hop_3': SettingsDefinition(u'speed_z_hop_3', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'speed_z_hop_4': SettingsDefinition(u'speed_z_hop_4', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'speed_z_hop_5': SettingsDefinition(u'speed_z_hop_5', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'speed_z_hop_6': SettingsDefinition(u'speed_z_hop_6', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'speed_z_hop_7': SettingsDefinition(u'speed_z_hop_7', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            # retraction_amount
            u'retraction_amount_0': SettingsDefinition(u'retraction_amount_0', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_amount_1': SettingsDefinition(u'retraction_amount_1', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_amount_2': SettingsDefinition(u'retraction_amount_2', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_amount_3': SettingsDefinition(u'retraction_amount_3', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_amount_4': SettingsDefinition(u'retraction_amount_4', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_amount_5': SettingsDefinition(u'retraction_amount_5', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_amount_6': SettingsDefinition(u'retraction_amount_6', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_amount_7': SettingsDefinition(u'retraction_amount_7', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            # retraction_hop
            u'retraction_hop_0': SettingsDefinition(u'retraction_hop_0', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_hop_1': SettingsDefinition(u'retraction_hop_1', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_hop_2': SettingsDefinition(u'retraction_hop_2', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_hop_3': SettingsDefinition(u'retraction_hop_3', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_hop_4': SettingsDefinition(u'retraction_hop_4', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_hop_5': SettingsDefinition(u'retraction_hop_5', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_hop_6': SettingsDefinition(u'retraction_hop_6', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_hop_7': SettingsDefinition(u'retraction_hop_7', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            # retraction_hop_enabled
            u'retraction_hop_enabled_0': SettingsDefinition(u'retraction_hop_enabled_0', CuraParsingFunctions.parse_bool, [u'octolapse_setting']),
            u'retraction_hop_enabled_1': SettingsDefinition(u'retraction_hop_enabled_1', CuraParsingFunctions.parse_bool, [u'octolapse_setting']),
            u'retraction_hop_enabled_2': SettingsDefinition(u'retraction_hop_enabled_2', CuraParsingFunctions.parse_bool, [u'octolapse_setting']),
            u'retraction_hop_enabled_3': SettingsDefinition(u'retraction_hop_enabled_3', CuraParsingFunctions.parse_bool, [u'octolapse_setting']),
            u'retraction_hop_enabled_4': SettingsDefinition(u'retraction_hop_enabled_4', CuraParsingFunctions.parse_bool, [u'octolapse_setting']),
            u'retraction_hop_enabled_5': SettingsDefinition(u'retraction_hop_enabled_5', CuraParsingFunctions.parse_bool, [u'octolapse_setting']),
            u'retraction_hop_enabled_6': SettingsDefinition(u'retraction_hop_enabled_6', CuraParsingFunctions.parse_bool, [u'octolapse_setting']),
            u'retraction_hop_enabled_7': SettingsDefinition(u'retraction_hop_enabled_7', CuraParsingFunctions.parse_bool, [u'octolapse_setting']),
            # retraction_prime_speed
            u'retraction_prime_speed_0': SettingsDefinition(u'retraction_prime_speed_0', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_prime_speed_1': SettingsDefinition(u'retraction_prime_speed_1', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_prime_speed_2': SettingsDefinition(u'retraction_prime_speed_2', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_prime_speed_3': SettingsDefinition(u'retraction_prime_speed_3', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_prime_speed_4': SettingsDefinition(u'retraction_prime_speed_4', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_prime_speed_5': SettingsDefinition(u'retraction_prime_speed_5', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_prime_speed_6': SettingsDefinition(u'retraction_prime_speed_6', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_prime_speed_7': SettingsDefinition(u'retraction_prime_speed_7', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            # retraction_retract_speed
            u'retraction_retract_speed_0': SettingsDefinition(u'retraction_retract_speed_0', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_retract_speed_1': SettingsDefinition(u'retraction_retract_speed_1', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_retract_speed_2': SettingsDefinition(u'retraction_retract_speed_2', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_retract_speed_3': SettingsDefinition(u'retraction_retract_speed_3', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_retract_speed_4': SettingsDefinition(u'retraction_retract_speed_4', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_retract_speed_5': SettingsDefinition(u'retraction_retract_speed_5', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_retract_speed_6': SettingsDefinition(u'retraction_retract_speed_6', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_retract_speed_7': SettingsDefinition(u'retraction_retract_speed_7', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            # retraction_speed
            u'retraction_speed_0': SettingsDefinition(u'retraction_speed_0', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_speed_1': SettingsDefinition(u'retraction_speed_1', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_speed_2': SettingsDefinition(u'retraction_speed_2', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_speed_3': SettingsDefinition(u'retraction_speed_3', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_speed_4': SettingsDefinition(u'retraction_speed_4', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_speed_5': SettingsDefinition(u'retraction_speed_5', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_speed_6': SettingsDefinition(u'retraction_speed_6', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'retraction_speed_7': SettingsDefinition(u'retraction_speed_7', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            # retraction_enable
            u'retraction_enable_0': SettingsDefinition(u'retraction_enable_0', CuraParsingFunctions.parse_bool, [u'octolapse_setting']),
            u'retraction_enable_1': SettingsDefinition(u'retraction_enable_1', CuraParsingFunctions.parse_bool, [u'octolapse_setting']),
            u'retraction_enable_2': SettingsDefinition(u'retraction_enable_2', CuraParsingFunctions.parse_bool, [u'octolapse_setting']),
            u'retraction_enable_3': SettingsDefinition(u'retraction_enable_3', CuraParsingFunctions.parse_bool, [u'octolapse_setting']),
            u'retraction_enable_4': SettingsDefinition(u'retraction_enable_4', CuraParsingFunctions.parse_bool, [u'octolapse_setting']),
            u'retraction_enable_5': SettingsDefinition(u'retraction_enable_5', CuraParsingFunctions.parse_bool, [u'octolapse_setting']),
            u'retraction_enable_6': SettingsDefinition(u'retraction_enable_6', CuraParsingFunctions.parse_bool, [u'octolapse_setting']),
            u'retraction_enable_7': SettingsDefinition(u'retraction_enable_7', CuraParsingFunctions.parse_bool, [u'octolapse_setting']),
            # speed_travel
            u'speed_travel_0': SettingsDefinition(u'speed_travel_0', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'speed_travel_1': SettingsDefinition(u'speed_travel_1', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'speed_travel_2': SettingsDefinition(u'speed_travel_2', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'speed_travel_3': SettingsDefinition(u'speed_travel_3', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'speed_travel_4': SettingsDefinition(u'speed_travel_4', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'speed_travel_5': SettingsDefinition(u'speed_travel_5', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'speed_travel_6': SettingsDefinition(u'speed_travel_6', CuraParsingFunctions.parse_float, [u'octolapse_setting']),
            u'speed_travel_7': SettingsDefinition(u'speed_travel_7', CuraParsingFunctions.parse_float, [u'octolapse_setting']),

            # End Octolapse Settings - The rest is included in case it is ever helpful for Octolapse or for other projects!
            u'magic_mesh_surface_mode': SettingsDefinition(u'magic_mesh_surface_mode',
                                                           CuraParsingFunctions.strip_string, [u'misc']),
            u'speed_infill': SettingsDefinition(u'speed_infill', CuraParsingFunctions.parse_float, [u'misc']),
            u'skirt_brim_speed': SettingsDefinition(u'skirt_brim_speed', CuraParsingFunctions.parse_float, [u'misc']),

            u'flavor': SettingsDefinition(u'flavor', CuraParsingFunctions.strip_string, [u'misc']),
            u'speed_layer_0': SettingsDefinition(u'speed_layer_0', CuraParsingFunctions.parse_float, [u'misc']),
            u'speed_print': SettingsDefinition(u'speed_print', CuraParsingFunctions.parse_int, [u'misc']),
            u'speed_slowdown_layers': SettingsDefinition(u'speed_slowdown_layers', CuraParsingFunctions.parse_int, [u'misc']),
            u'speed_topbottom': SettingsDefinition(u'speed_topbottom', CuraParsingFunctions.parse_float, [u'misc']),
            u'speed_travel_layer_0': SettingsDefinition(u'speed_travel_layer_0', CuraParsingFunctions.parse_float, [u'misc']),
            u'speed_wall': SettingsDefinition(u'speed_wall', CuraParsingFunctions.parse_float, [u'misc']),
            u'speed_wall_0': SettingsDefinition(u'speed_wall_0', CuraParsingFunctions.parse_float, [u'misc']),
            u'speed_wall_x': SettingsDefinition(u'speed_wall_x', CuraParsingFunctions.parse_float, [u'misc']),
            u'retraction_combing': SettingsDefinition(u'retraction_combing', CuraParsingFunctions.strip_string, [u'misc']),
            u'speed_print_layer_0': SettingsDefinition(u'speed_print_layer_0', CuraParsingFunctions.parse_float, [u'misc']),
            u'filament_used_meters': SettingsDefinition(u'layer_height', CuraParsingFunctions.parse_float, [u'misc']),
            u'acceleration_enabled': SettingsDefinition(u'acceleration_enabled', CuraParsingFunctions.parse_bool, [u'misc']),
            u'acceleration_infill': SettingsDefinition(u'acceleration_infill', CuraParsingFunctions.parse_int, [u'misc']),
            u'acceleration_ironing': SettingsDefinition(u'acceleration_ironing', CuraParsingFunctions.parse_int, [u'misc']),
            u'acceleration_layer_0': SettingsDefinition(u'acceleration_layer_0', CuraParsingFunctions.parse_int, [u'misc']),
            u'acceleration_prime_tower': SettingsDefinition(u'acceleration_prime_tower', CuraParsingFunctions.parse_int, [u'misc']),
            u'acceleration_print': SettingsDefinition(u'acceleration_print', CuraParsingFunctions.parse_int, [u'misc']),
            u'acceleration_print_layer_0': SettingsDefinition(u'acceleration_print_layer_0', CuraParsingFunctions.parse_int, [u'misc']),
            u'acceleration_roofing': SettingsDefinition(u'acceleration_roofing', CuraParsingFunctions.parse_int, [u'misc']),
            u'acceleration_skirt_brim': SettingsDefinition(u'acceleration_skirt_brim', CuraParsingFunctions.parse_int, [u'misc']),
            u'acceleration_support': SettingsDefinition(u'acceleration_support', CuraParsingFunctions.parse_int, [u'misc']),
            u'acceleration_support_bottom': SettingsDefinition(u'acceleration_support_bottom', CuraParsingFunctions.parse_int, [u'misc']),
            u'acceleration_support_infill': SettingsDefinition(u'acceleration_support_infill', CuraParsingFunctions.parse_int, [u'misc']),
            u'acceleration_support_interface': SettingsDefinition(u'acceleration_support_interface', CuraParsingFunctions.parse_int, [u'misc']),
            u'acceleration_support_roof': SettingsDefinition(u'acceleration_support_roof', CuraParsingFunctions.parse_int, [u'misc']),
            u'acceleration_topbottom': SettingsDefinition(u'acceleration_topbottom', CuraParsingFunctions.parse_int, [u'misc']),
            u'acceleration_travel': SettingsDefinition(u'acceleration_travel', CuraParsingFunctions.parse_int, [u'misc']),
            u'acceleration_travel_layer_0': SettingsDefinition(u'acceleration_travel_layer_0', CuraParsingFunctions.parse_float, [u'misc']),
            u'acceleration_wall': SettingsDefinition(u'acceleration_wall', CuraParsingFunctions.parse_int, [u'misc']),
            u'acceleration_wall_0': SettingsDefinition(u'acceleration_wall_0', CuraParsingFunctions.parse_int, [u'misc']),
            u'acceleration_wall_x': SettingsDefinition(u'acceleration_wall_x', CuraParsingFunctions.parse_int, [u'misc']),
            u'adaptive_layer_height_enabled': SettingsDefinition(u'adaptive_layer_height_enabled', CuraParsingFunctions.parse_bool, [u'misc']),
            u'adaptive_layer_height_threshold': SettingsDefinition(u'adaptive_layer_height_threshold', CuraParsingFunctions.parse_float, [u'misc']),
            u'adaptive_layer_height_variation': SettingsDefinition(u'adaptive_layer_height_variation', CuraParsingFunctions.parse_float, [u'misc']),
            u'adaptive_layer_height_variation_step': SettingsDefinition(u'adaptive_layer_height_variation_step', CuraParsingFunctions.parse_float, [u'misc']),
            u'adhesion_extruder_nr': SettingsDefinition(u'adhesion_extruder_nr', CuraParsingFunctions.parse_int, [u'misc']),
            u'adhesion_type': SettingsDefinition(u'adhesion_type', CuraParsingFunctions.strip_string, [u'misc']),
            u'alternate_carve_order': SettingsDefinition(u'alternate_carve_order', CuraParsingFunctions.parse_bool, [u'misc']),
            u'alternate_extra_perimeter': SettingsDefinition(u'alternate_extra_perimeter', CuraParsingFunctions.parse_bool, [u'misc']),
            u'anti_overhang_mesh': SettingsDefinition(u'anti_overhang_mesh', CuraParsingFunctions.parse_bool, [u'misc']),
            u'bottom_layers': SettingsDefinition(u'bottom_layers', CuraParsingFunctions.parse_int, [u'misc']),
            u'bottom_skin_expand_distance': SettingsDefinition(u'bottom_skin_expand_distance', CuraParsingFunctions.parse_float, [u'misc']),
            u'bottom_skin_preshrink': SettingsDefinition(u'bottom_skin_preshrink', CuraParsingFunctions.parse_float, [u'misc']),
            u'bottom_thickness': SettingsDefinition(u'bottom_thickness', CuraParsingFunctions.parse_float, [u'misc']),
            u'bridge_enable_more_layers': SettingsDefinition(u'bridge_enable_more_layers', CuraParsingFunctions.parse_bool, [u'misc']),
            u'bridge_fan_speed': SettingsDefinition(u'bridge_fan_speed', CuraParsingFunctions.parse_int, [u'misc']),
            u'bridge_fan_speed_2': SettingsDefinition(u'bridge_fan_speed_2', CuraParsingFunctions.parse_int, [u'misc']),
            u'bridge_fan_speed_3': SettingsDefinition(u'bridge_fan_speed_3', CuraParsingFunctions.parse_int, [u'misc']),
            u'bridge_settings_enabled': SettingsDefinition(u'bridge_settings_enabled', CuraParsingFunctions.parse_bool, [u'misc']),
            u'bridge_skin_density': SettingsDefinition(u'bridge_skin_density', CuraParsingFunctions.parse_int, [u'misc']),
            u'bridge_skin_density_2': SettingsDefinition(u'bridge_skin_density_2', CuraParsingFunctions.parse_int, [u'misc']),
            u'bridge_skin_density_3': SettingsDefinition(u'bridge_skin_density_3', CuraParsingFunctions.parse_int, [u'misc']),
            u'bridge_skin_material_flow': SettingsDefinition(u'bridge_skin_material_flow', CuraParsingFunctions.parse_int, [u'misc']),
            u'bridge_skin_material_flow_2': SettingsDefinition(u'bridge_skin_material_flow_2', CuraParsingFunctions.parse_int, [u'misc']),
            u'bridge_skin_material_flow_3': SettingsDefinition(u'bridge_skin_material_flow_3', CuraParsingFunctions.parse_int, [u'misc']),
            u'bridge_skin_speed': SettingsDefinition(u'bridge_skin_speed', CuraParsingFunctions.parse_float, [u'misc']),
            u'bridge_skin_speed_2': SettingsDefinition(u'bridge_skin_speed_2', CuraParsingFunctions.parse_float, [u'misc']),
            u'bridge_skin_speed_3': SettingsDefinition(u'bridge_skin_speed_3', CuraParsingFunctions.parse_float, [u'misc']),
            u'bridge_skin_support_threshold': SettingsDefinition(u'bridge_skin_support_threshold', CuraParsingFunctions.parse_int, [u'misc']),
            u'bridge_wall_coast': SettingsDefinition(u'bridge_wall_coast', CuraParsingFunctions.parse_int, [u'misc']),
            u'bridge_wall_material_flow': SettingsDefinition(u'bridge_wall_material_flow', CuraParsingFunctions.parse_int, [u'misc']),
            u'bridge_wall_min_length': SettingsDefinition(u'bridge_wall_min_length', CuraParsingFunctions.parse_int, [u'misc']),
            u'bridge_wall_speed': SettingsDefinition(u'bridge_wall_speed', CuraParsingFunctions.parse_float, [u'misc']),
            u'brim_line_count': SettingsDefinition(u'brim_line_count', CuraParsingFunctions.parse_int, [u'misc']),
            u'brim_outside_only': SettingsDefinition(u'brim_outside_only', CuraParsingFunctions.parse_bool, [u'misc']),
            u'brim_replaces_support': SettingsDefinition(u'brim_replaces_support', CuraParsingFunctions.parse_bool, [u'misc']),
            u'brim_width': SettingsDefinition(u'brim_width', CuraParsingFunctions.parse_float, [u'misc']),
            u'carve_multiple_volumes': SettingsDefinition(u'carve_multiple_volumes', CuraParsingFunctions.parse_bool, [u'misc']),
            u'center_object': SettingsDefinition(u'center_object', CuraParsingFunctions.parse_bool, [u'misc']),
            u'coasting_enable': SettingsDefinition(u'coasting_enable', CuraParsingFunctions.parse_bool, [u'misc']),
            u'coasting_min_volume': SettingsDefinition(u'coasting_min_volume', CuraParsingFunctions.parse_float, [u'misc']),
            u'coasting_speed': SettingsDefinition(u'coasting_speed', CuraParsingFunctions.parse_int, [u'misc']),
            u'coasting_volume': SettingsDefinition(u'coasting_volume', CuraParsingFunctions.parse_float, [u'misc']),
            u'conical_overhang_angle': SettingsDefinition(u'conical_overhang_angle', CuraParsingFunctions.parse_int, [u'misc']),
            u'conical_overhang_enabled': SettingsDefinition(u'conical_overhang_enabled', CuraParsingFunctions.parse_bool, [u'misc']),
            u'connect_infill_polygons': SettingsDefinition(u'connect_infill_polygons', CuraParsingFunctions.parse_bool, [u'misc']),
            u'connect_skin_polygons': SettingsDefinition(u'connect_skin_polygons', CuraParsingFunctions.parse_bool, [u'misc']),
            u'cool_fan_enabled': SettingsDefinition(u'cool_fan_enabled', CuraParsingFunctions.parse_bool, [u'misc']),
            u'cool_fan_full_at_height': SettingsDefinition(u'cool_fan_full_at_height', CuraParsingFunctions.parse_float, [u'misc']),
            u'cool_fan_full_layer': SettingsDefinition(u'cool_fan_full_layer', CuraParsingFunctions.parse_int, [u'misc']),
            u'cool_fan_speed': SettingsDefinition(u'cool_fan_speed', CuraParsingFunctions.parse_float, [u'misc']),
            u'cool_fan_speed_0': SettingsDefinition(u'cool_fan_speed_0', CuraParsingFunctions.parse_int, [u'misc']),
            u'cool_fan_speed_max': SettingsDefinition(u'cool_fan_speed_max', CuraParsingFunctions.parse_float, [u'misc']),
            u'cool_fan_speed_min': SettingsDefinition(u'cool_fan_speed_min', CuraParsingFunctions.parse_float, [u'misc']),
            u'cool_lift_head': SettingsDefinition(u'cool_lift_head', CuraParsingFunctions.parse_bool, [u'misc']),
            u'cool_min_layer_time': SettingsDefinition(u'cool_min_layer_time', CuraParsingFunctions.parse_int, [u'misc']),
            u'cool_min_layer_time_fan_speed_max': SettingsDefinition(u'cool_min_layer_time_fan_speed_max', CuraParsingFunctions.parse_int, [u'misc']),
            u'cool_min_speed': SettingsDefinition(u'cool_min_speed', CuraParsingFunctions.parse_int, [u'misc']),
            u'cross_infill_pocket_size': SettingsDefinition(u'cross_infill_pocket_size', CuraParsingFunctions.parse_float, [u'misc']),
            u'cutting_mesh': SettingsDefinition(u'cutting_mesh', CuraParsingFunctions.parse_bool, [u'misc']),
            u'default_material_bed_temperature': SettingsDefinition(u'default_material_bed_temperature', CuraParsingFunctions.parse_int, [u'misc']),
            u'default_material_print_temperature': SettingsDefinition(u'default_material_print_temperature', CuraParsingFunctions.parse_int, [u'misc']),
            u'draft_shield_dist': SettingsDefinition(u'draft_shield_dist', CuraParsingFunctions.parse_int, [u'misc']),
            u'draft_shield_enabled': SettingsDefinition(u'draft_shield_enabled', CuraParsingFunctions.parse_bool, [u'misc']),
            u'draft_shield_height': SettingsDefinition(u'draft_shield_height', CuraParsingFunctions.parse_int, [u'misc']),
            u'draft_shield_height_limitation': SettingsDefinition(u'draft_shield_height_limitation', CuraParsingFunctions.strip_string, [u'misc']),
            u'expand_skins_expand_distance': SettingsDefinition(u'expand_skins_expand_distance', CuraParsingFunctions.parse_float, [u'misc']),
            u'extruder_prime_pos_abs': SettingsDefinition(u'extruder_prime_pos_abs', CuraParsingFunctions.parse_bool, [u'misc']),
            u'extruder_prime_pos_x': SettingsDefinition(u'extruder_prime_pos_x', CuraParsingFunctions.parse_int, [u'misc']),
            u'extruder_prime_pos_y': SettingsDefinition(u'extruder_prime_pos_y', CuraParsingFunctions.parse_int, [u'misc']),
            u'extruder_prime_pos_z': SettingsDefinition(u'extruder_prime_pos_z', CuraParsingFunctions.parse_int, [u'misc']),
            u'extruders_enabled_count': SettingsDefinition(u'extruders_enabled_count', CuraParsingFunctions.parse_int, [u'misc']),
            u'fill_outline_gaps': SettingsDefinition(u'fill_outline_gaps', CuraParsingFunctions.parse_bool, [u'misc']),
            u'fill_perimeter_gaps': SettingsDefinition(u'fill_perimeter_gaps', CuraParsingFunctions.strip_string, [u'misc']),
            u'filter_out_tiny_gaps': SettingsDefinition(u'filter_out_tiny_gaps', CuraParsingFunctions.parse_bool, [u'misc']),
            u'flow_rate_extrusion_offset_factor': SettingsDefinition(u'flow_rate_extrusion_offset_factor', CuraParsingFunctions.parse_int, [u'misc']),
            u'flow_rate_max_extrusion_offset': SettingsDefinition(u'flow_rate_max_extrusion_offset', CuraParsingFunctions.parse_int, [u'misc']),
            u'gantry_height': SettingsDefinition(u'gantry_height', CuraParsingFunctions.parse_int, [u'misc']),
            u'gradual_infill_step_height': SettingsDefinition(u'gradual_infill_step_height', CuraParsingFunctions.parse_float, [u'misc']),
            u'gradual_infill_steps': SettingsDefinition(u'gradual_infill_steps', CuraParsingFunctions.parse_int, [u'misc']),
            u'gradual_support_infill_step_height': SettingsDefinition(u'gradual_support_infill_step_height', CuraParsingFunctions.parse_int, [u'misc']),
            u'gradual_support_infill_steps': SettingsDefinition(u'gradual_support_infill_steps', CuraParsingFunctions.parse_int, [u'misc']),
            u'infill_before_walls': SettingsDefinition(u'infill_before_walls', CuraParsingFunctions.parse_bool, [u'misc']),
            u'infill_enable_travel_optimization': SettingsDefinition(u'infill_enable_travel_optimization', CuraParsingFunctions.parse_bool, [u'misc']),
            u'infill_extruder_nr': SettingsDefinition(u'infill_extruder_nr', CuraParsingFunctions.parse_int, [u'misc']),
            u'infill_line_distance': SettingsDefinition(u'infill_line_distance', CuraParsingFunctions.parse_float, [u'misc']),
            u'infill_line_width': SettingsDefinition(u'infill_line_width', CuraParsingFunctions.parse_float, [u'misc']),
            u'infill_mesh': SettingsDefinition(u'infill_mesh', CuraParsingFunctions.parse_bool, [u'misc']),
            u'infill_mesh_order': SettingsDefinition(u'infill_mesh_order', CuraParsingFunctions.parse_int, [u'misc']),
            u'infill_multiplier': SettingsDefinition(u'infill_multiplier', CuraParsingFunctions.parse_int, [u'misc']),
            u'infill_offset_x': SettingsDefinition(u'infill_offset_x', CuraParsingFunctions.parse_int, [u'misc']),
            u'infill_offset_y': SettingsDefinition(u'infill_offset_y', CuraParsingFunctions.parse_int, [u'misc']),
            u'infill_overlap': SettingsDefinition(u'infill_overlap', CuraParsingFunctions.parse_int, [u'misc']),
            u'infill_overlap_mm': SettingsDefinition(u'infill_overlap_mm', CuraParsingFunctions.parse_float, [u'misc']),
            u'infill_pattern': SettingsDefinition(u'infill_pattern', CuraParsingFunctions.strip_string, [u'misc']),
            u'infill_sparse_density': SettingsDefinition(u'infill_sparse_density', CuraParsingFunctions.parse_int, [u'misc']),
            u'infill_sparse_thickness': SettingsDefinition(u'infill_sparse_thickness', CuraParsingFunctions.parse_float, [u'misc']),
            u'infill_support_angle': SettingsDefinition(u'infill_support_angle', CuraParsingFunctions.parse_int, [u'misc']),
            u'infill_support_enabled': SettingsDefinition(u'infill_support_enabled', CuraParsingFunctions.parse_bool, [u'misc']),
            u'infill_wall_line_count': SettingsDefinition(u'infill_wall_line_count', CuraParsingFunctions.parse_int, [u'misc']),
            u'infill_wipe_dist': SettingsDefinition(u'infill_wipe_dist', CuraParsingFunctions.parse_float, [u'misc']),
            u'initial_layer_line_width_factor': SettingsDefinition(u'initial_layer_line_width_factor', CuraParsingFunctions.parse_float, [u'misc']),
            u'ironing_enabled': SettingsDefinition(u'ironing_enabled', CuraParsingFunctions.parse_bool, [u'misc']),
            u'ironing_flow': SettingsDefinition(u'ironing_flow', CuraParsingFunctions.parse_float, [u'misc']),
            u'ironing_inset': SettingsDefinition(u'ironing_inset', CuraParsingFunctions.parse_float, [u'misc']),
            u'ironing_line_spacing': SettingsDefinition(u'ironing_line_spacing', CuraParsingFunctions.parse_float, [u'misc']),
            u'ironing_only_highest_layer': SettingsDefinition(u'ironing_only_highest_layer', CuraParsingFunctions.parse_bool, [u'misc']),
            u'ironing_pattern': SettingsDefinition(u'ironing_pattern', CuraParsingFunctions.strip_string, [u'misc']),
            u'jerk_enabled': SettingsDefinition(u'jerk_enabled', CuraParsingFunctions.parse_bool, [u'misc']),
            u'jerk_infill': SettingsDefinition(u'jerk_infill', CuraParsingFunctions.parse_int, [u'misc']),
            u'jerk_ironing': SettingsDefinition(u'jerk_ironing', CuraParsingFunctions.parse_int, [u'misc']),
            u'jerk_layer_0': SettingsDefinition(u'jerk_layer_0', CuraParsingFunctions.parse_int, [u'misc']),
            u'jerk_prime_tower': SettingsDefinition(u'jerk_prime_tower', CuraParsingFunctions.parse_int, [u'misc']),
            u'jerk_print': SettingsDefinition(u'jerk_print', CuraParsingFunctions.parse_int, [u'misc']),
            u'jerk_print_layer_0': SettingsDefinition(u'jerk_print_layer_0', CuraParsingFunctions.parse_int, [u'misc']),
            u'jerk_roofing': SettingsDefinition(u'jerk_roofing', CuraParsingFunctions.parse_int, [u'misc']),
            u'jerk_skirt_brim': SettingsDefinition(u'jerk_skirt_brim', CuraParsingFunctions.parse_int, [u'misc']),
            u'jerk_support': SettingsDefinition(u'jerk_support', CuraParsingFunctions.parse_int, [u'misc']),
            u'jerk_support_bottom': SettingsDefinition(u'jerk_support_bottom', CuraParsingFunctions.parse_int, [u'misc']),
            u'jerk_support_infill': SettingsDefinition(u'jerk_support_infill', CuraParsingFunctions.parse_int, [u'misc']),
            u'jerk_support_interface': SettingsDefinition(u'jerk_support_interface', CuraParsingFunctions.parse_int, [u'misc']),
            u'jerk_support_roof': SettingsDefinition(u'jerk_support_roof', CuraParsingFunctions.parse_int, [u'misc']),
            u'jerk_topbottom': SettingsDefinition(u'jerk_topbottom', CuraParsingFunctions.parse_int, [u'misc']),
            u'jerk_travel': SettingsDefinition(u'jerk_travel', CuraParsingFunctions.parse_int, [u'misc']),
            u'jerk_travel_layer_0': SettingsDefinition(u'jerk_travel_layer_0', CuraParsingFunctions.parse_float, [u'misc']),
            u'jerk_wall': SettingsDefinition(u'jerk_wall', CuraParsingFunctions.parse_int, [u'misc']),
            u'jerk_wall_0': SettingsDefinition(u'jerk_wall_0', CuraParsingFunctions.parse_int, [u'misc']),
            u'jerk_wall_x': SettingsDefinition(u'jerk_wall_x', CuraParsingFunctions.parse_int, [u'misc']),
            u'layer_0_z_overlap': SettingsDefinition(u'layer_0_z_overlap', CuraParsingFunctions.parse_float, [u'misc']),
            u'layer_height_0': SettingsDefinition(u'layer_height_0', CuraParsingFunctions.parse_float, [u'misc']),
            u'layer_start_x': SettingsDefinition(u'layer_start_x', CuraParsingFunctions.parse_float, [u'misc']),
            u'layer_start_y': SettingsDefinition(u'layer_start_y', CuraParsingFunctions.parse_float, [u'misc']),
            u'limit_support_retractions': SettingsDefinition(u'limit_support_retractions', CuraParsingFunctions.parse_bool, [u'misc']),
            u'line_width': SettingsDefinition(u'line_width', CuraParsingFunctions.parse_float, [u'misc']),
            u'machine_acceleration': SettingsDefinition(u'machine_acceleration', CuraParsingFunctions.parse_int, [u'misc']),
            u'machine_buildplate_type': SettingsDefinition(u'machine_buildplate_type', CuraParsingFunctions.strip_string, [u'misc']),
            u'machine_center_is_zero': SettingsDefinition(u'machine_center_is_zero', CuraParsingFunctions.parse_bool, [u'misc']),
            u'machine_depth': SettingsDefinition(u'machine_depth', CuraParsingFunctions.parse_int, [u'misc']),
            u'machine_endstop_positive_direction_x': SettingsDefinition(u'machine_endstop_positive_direction_x', CuraParsingFunctions.parse_bool, [u'misc']),
            u'machine_endstop_positive_direction_y': SettingsDefinition(u'machine_endstop_positive_direction_y', CuraParsingFunctions.parse_bool, [u'misc']),
            u'machine_endstop_positive_direction_z': SettingsDefinition(u'machine_endstop_positive_direction_z', CuraParsingFunctions.parse_bool, [u'misc']),
            u'machine_feeder_wheel_diameter': SettingsDefinition(u'machine_feeder_wheel_diameter', CuraParsingFunctions.parse_float, [u'misc']),
            u'machine_filament_park_distance': SettingsDefinition(u'machine_filament_park_distance', CuraParsingFunctions.parse_int, [u'misc']),
            u'machine_firmware_retract': SettingsDefinition(u'machine_firmware_retract', CuraParsingFunctions.parse_bool, [u'misc']),
            u'machine_gcode_flavor': SettingsDefinition(u'machine_gcode_flavor', CuraParsingFunctions.strip_string, [u'misc']),
            u'machine_heat_zone_length': SettingsDefinition(u'machine_heat_zone_length', CuraParsingFunctions.parse_int, [u'misc']),
            u'machine_heated_bed': SettingsDefinition(u'machine_heated_bed', CuraParsingFunctions.parse_bool, [u'misc']),
            u'machine_height': SettingsDefinition(u'machine_height', CuraParsingFunctions.parse_int, [u'misc']),
            u'machine_max_acceleration_e': SettingsDefinition(u'machine_max_acceleration_e', CuraParsingFunctions.parse_int, [u'misc']),
            u'machine_max_acceleration_x': SettingsDefinition(u'machine_max_acceleration_x', CuraParsingFunctions.parse_int, [u'misc']),
            u'machine_max_acceleration_y': SettingsDefinition(u'machine_max_acceleration_y', CuraParsingFunctions.parse_int, [u'misc']),
            u'machine_max_acceleration_z': SettingsDefinition(u'machine_max_acceleration_z', CuraParsingFunctions.parse_int, [u'misc']),
            u'machine_max_feedrate_e': SettingsDefinition(u'machine_max_feedrate_e', CuraParsingFunctions.parse_int, [u'misc']),
            u'machine_max_feedrate_x': SettingsDefinition(u'machine_max_feedrate_x', CuraParsingFunctions.parse_int, [u'misc']),
            u'machine_max_feedrate_y': SettingsDefinition(u'machine_max_feedrate_y', CuraParsingFunctions.parse_int, [u'misc']),
            u'machine_max_feedrate_z': SettingsDefinition(u'machine_max_feedrate_z', CuraParsingFunctions.parse_int, [u'misc']),
            u'machine_max_jerk_e': SettingsDefinition(u'machine_max_jerk_e', CuraParsingFunctions.parse_float, [u'misc']),
            u'machine_max_jerk_xy': SettingsDefinition(u'machine_max_jerk_xy', CuraParsingFunctions.parse_int, [u'misc']),
            u'machine_max_jerk_z': SettingsDefinition(u'machine_max_jerk_z', CuraParsingFunctions.parse_float, [u'misc']),
            u'machine_min_cool_heat_time_window': SettingsDefinition(u'machine_min_cool_heat_time_window', CuraParsingFunctions.parse_float, [u'misc']),
            u'machine_minimum_feedrate': SettingsDefinition(u'machine_minimum_feedrate', CuraParsingFunctions.parse_float, [u'misc']),
            u'machine_name': SettingsDefinition(u'machine_name', CuraParsingFunctions.strip_string, [u'misc']),
            u'machine_nozzle_cool_down_speed': SettingsDefinition(u'machine_nozzle_cool_down_speed', CuraParsingFunctions.parse_float, [u'misc']),
            u'machine_nozzle_expansion_angle': SettingsDefinition(u'machine_nozzle_expansion_angle', CuraParsingFunctions.parse_int, [u'misc']),
            u'machine_nozzle_head_distance': SettingsDefinition(u'machine_nozzle_head_distance', CuraParsingFunctions.parse_int, [u'misc']),
            u'machine_nozzle_heat_up_speed': SettingsDefinition(u'machine_nozzle_heat_up_speed', CuraParsingFunctions.parse_float, [u'misc']),
            u'machine_nozzle_id': SettingsDefinition(u'machine_nozzle_id', CuraParsingFunctions.strip_string, [u'misc']),
            u'machine_nozzle_size': SettingsDefinition(u'machine_nozzle_size', CuraParsingFunctions.parse_float, [u'misc']),
            u'machine_nozzle_temp_enabled': SettingsDefinition(u'machine_nozzle_temp_enabled', CuraParsingFunctions.parse_bool, [u'misc']),
            u'machine_nozzle_tip_outer_diameter': SettingsDefinition(u'machine_nozzle_tip_outer_diameter', CuraParsingFunctions.parse_int, [u'misc']),
            u'machine_shape': SettingsDefinition(u'machine_shape', CuraParsingFunctions.strip_string, [u'misc']),
            u'machine_show_variants': SettingsDefinition(u'machine_show_variants', CuraParsingFunctions.parse_bool, [u'misc']),
            u'machine_steps_per_mm_e': SettingsDefinition(u'machine_steps_per_mm_e', CuraParsingFunctions.parse_int, [u'misc']),
            u'machine_steps_per_mm_x': SettingsDefinition(u'machine_steps_per_mm_x', CuraParsingFunctions.parse_int, [u'misc']),
            u'machine_steps_per_mm_y': SettingsDefinition(u'machine_steps_per_mm_y', CuraParsingFunctions.parse_int, [u'misc']),
            u'machine_steps_per_mm_z': SettingsDefinition(u'machine_steps_per_mm_z', CuraParsingFunctions.parse_int, [u'misc']),
            u'machine_use_extruder_offset_to_offset_coords': SettingsDefinition(u'machine_use_extruder_offset_to_offset_coords', CuraParsingFunctions.parse_bool, [u'misc']),
            u'machine_width': SettingsDefinition(u'machine_width', CuraParsingFunctions.parse_int, [u'misc']),
            u'magic_fuzzy_skin_enabled': SettingsDefinition(u'magic_fuzzy_skin_enabled', CuraParsingFunctions.parse_bool, [u'misc']),
            u'magic_fuzzy_skin_point_density': SettingsDefinition(u'magic_fuzzy_skin_point_density', CuraParsingFunctions.parse_float, [u'misc']),
            u'magic_fuzzy_skin_point_dist': SettingsDefinition(u'magic_fuzzy_skin_point_dist', CuraParsingFunctions.parse_float, [u'misc']),
            u'magic_fuzzy_skin_thickness': SettingsDefinition(u'magic_fuzzy_skin_thickness', CuraParsingFunctions.parse_float, [u'misc']),
            u'magic_spiralize': SettingsDefinition(u'magic_spiralize', CuraParsingFunctions.parse_bool, [u'misc']),
            u'material_adhesion_tendency': SettingsDefinition(u'material_adhesion_tendency', CuraParsingFunctions.parse_int, [u'misc']),
            u'material_bed_temp_prepend': SettingsDefinition(u'material_bed_temp_prepend', CuraParsingFunctions.parse_bool, [u'misc']),
            u'material_bed_temp_wait': SettingsDefinition(u'material_bed_temp_wait', CuraParsingFunctions.parse_bool, [u'misc']),
            u'material_bed_temperature': SettingsDefinition(u'material_bed_temperature', CuraParsingFunctions.parse_int, [u'misc']),
            u'material_bed_temperature_layer_0': SettingsDefinition(u'material_bed_temperature_layer_0', CuraParsingFunctions.parse_int, [u'misc']),
            u'material_diameter': SettingsDefinition(u'material_diameter', CuraParsingFunctions.parse_float, [u'misc']),
            u'material_extrusion_cool_down_speed': SettingsDefinition(u'material_extrusion_cool_down_speed', CuraParsingFunctions.parse_float, [u'misc']),
            u'material_final_print_temperature': SettingsDefinition(u'material_final_print_temperature', CuraParsingFunctions.parse_int, [u'misc']),
            u'material_flow': SettingsDefinition(u'material_flow', CuraParsingFunctions.parse_int, [u'misc']),
            u'material_flow_dependent_temperature': SettingsDefinition(u'material_flow_dependent_temperature', CuraParsingFunctions.parse_bool, [u'misc']),
            u'material_flow_layer_0': SettingsDefinition(u'material_flow_layer_0', CuraParsingFunctions.parse_int, [u'misc']),
            u'material_initial_print_temperature': SettingsDefinition(u'material_initial_print_temperature', CuraParsingFunctions.parse_int, [u'misc']),
            u'material_print_temp_prepend': SettingsDefinition(u'material_print_temp_prepend', CuraParsingFunctions.parse_bool, [u'misc']),
            u'material_print_temp_wait': SettingsDefinition(u'material_print_temp_wait', CuraParsingFunctions.parse_bool, [u'misc']),
            u'material_print_temperature': SettingsDefinition(u'material_print_temperature', CuraParsingFunctions.parse_int, [u'misc']),
            u'material_print_temperature_layer_0': SettingsDefinition(u'material_print_temperature_layer_0', CuraParsingFunctions.parse_int, [u'misc']),
            u'material_shrinkage_percentage': SettingsDefinition(u'material_shrinkage_percentage', CuraParsingFunctions.parse_int, [u'misc']),
            u'material_standby_temperature': SettingsDefinition(u'material_standby_temperature', CuraParsingFunctions.parse_int, [u'misc']),
            u'material_surface_energy': SettingsDefinition(u'material_surface_energy', CuraParsingFunctions.parse_int, [u'misc']),
            u'max_skin_angle_for_expansion': SettingsDefinition(u'max_skin_angle_for_expansion', CuraParsingFunctions.parse_int, [u'misc']),
            u'mesh_position_x': SettingsDefinition(u'mesh_position_x', CuraParsingFunctions.parse_int, [u'misc']),
            u'mesh_position_y': SettingsDefinition(u'mesh_position_y', CuraParsingFunctions.parse_int, [u'misc']),
            u'mesh_position_z': SettingsDefinition(u'mesh_position_z', CuraParsingFunctions.parse_int, [u'misc']),
            u'meshfix_extensive_stitching': SettingsDefinition(u'meshfix_extensive_stitching', CuraParsingFunctions.parse_bool, [u'misc']),
            u'meshfix_keep_open_polygons': SettingsDefinition(u'meshfix_keep_open_polygons', CuraParsingFunctions.parse_bool, [u'misc']),
            u'meshfix_maximum_resolution': SettingsDefinition(u'meshfix_maximum_resolution', CuraParsingFunctions.parse_float, [u'misc']),
            u'meshfix_maximum_travel_resolution': SettingsDefinition(u'meshfix_maximum_travel_resolution', CuraParsingFunctions.parse_float, [u'misc']),
            u'meshfix_union_all': SettingsDefinition(u'meshfix_union_all', CuraParsingFunctions.parse_bool, [u'misc']),
            u'meshfix_union_all_remove_holes': SettingsDefinition(u'meshfix_union_all_remove_holes', CuraParsingFunctions.parse_bool, [u'misc']),
            u'min_infill_area': SettingsDefinition(u'min_infill_area', CuraParsingFunctions.parse_int, [u'misc']),
            u'min_skin_width_for_expansion': SettingsDefinition(u'min_skin_width_for_expansion', CuraParsingFunctions.parse_float, [u'misc']),
            u'minimum_polygon_circumference': SettingsDefinition(u'minimum_polygon_circumference', CuraParsingFunctions.parse_float, [u'misc']),
            u'mold_angle': SettingsDefinition(u'mold_angle', CuraParsingFunctions.parse_int, [u'misc']),
            u'mold_enabled': SettingsDefinition(u'mold_enabled', CuraParsingFunctions.parse_bool, [u'misc']),
            u'mold_roof_height': SettingsDefinition(u'mold_roof_height', CuraParsingFunctions.parse_float, [u'misc']),
            u'mold_width': SettingsDefinition(u'mold_width', CuraParsingFunctions.parse_int, [u'misc']),
            u'multiple_mesh_overlap': SettingsDefinition(u'multiple_mesh_overlap', CuraParsingFunctions.parse_float, [u'misc']),
            u'ooze_shield_angle': SettingsDefinition(u'ooze_shield_angle', CuraParsingFunctions.parse_int, [u'misc']),
            u'ooze_shield_dist': SettingsDefinition(u'ooze_shield_dist', CuraParsingFunctions.parse_int, [u'misc']),
            u'ooze_shield_enabled': SettingsDefinition(u'ooze_shield_enabled', CuraParsingFunctions.parse_bool, [u'misc']),
            u'optimize_wall_printing_order': SettingsDefinition(u'optimize_wall_printing_order', CuraParsingFunctions.parse_bool, [u'misc']),
            u'outer_inset_first': SettingsDefinition(u'outer_inset_first', CuraParsingFunctions.parse_bool, [u'misc']),
            u'prime_blob_enable': SettingsDefinition(u'prime_blob_enable', CuraParsingFunctions.parse_bool, [u'misc']),
            u'prime_tower_circular': SettingsDefinition(u'prime_tower_circular', CuraParsingFunctions.parse_bool, [u'misc']),
            u'prime_tower_enable': SettingsDefinition(u'prime_tower_enable', CuraParsingFunctions.parse_bool, [u'misc']),
            u'prime_tower_flow': SettingsDefinition(u'prime_tower_flow', CuraParsingFunctions.parse_int, [u'misc']),
            u'prime_tower_line_width': SettingsDefinition(u'prime_tower_line_width', CuraParsingFunctions.parse_float, [u'misc']),
            u'prime_tower_min_volume': SettingsDefinition(u'prime_tower_min_volume', CuraParsingFunctions.parse_int, [u'misc']),
            u'prime_tower_position_x': SettingsDefinition(u'prime_tower_position_x', CuraParsingFunctions.parse_float, [u'misc']),
            u'prime_tower_position_y': SettingsDefinition(u'prime_tower_position_y', CuraParsingFunctions.parse_float, [u'misc']),
            u'prime_tower_size': SettingsDefinition(u'prime_tower_size', CuraParsingFunctions.parse_int, [u'misc']),
            u'prime_tower_wipe_enabled': SettingsDefinition(u'prime_tower_wipe_enabled', CuraParsingFunctions.parse_bool, [u'misc']),
            u'print_sequence': SettingsDefinition(u'print_sequence', CuraParsingFunctions.strip_string, [u'misc']),
            u'raft_acceleration': SettingsDefinition(u'raft_acceleration', CuraParsingFunctions.parse_int, [u'misc']),
            u'raft_airgap': SettingsDefinition(u'raft_airgap', CuraParsingFunctions.parse_float, [u'misc']),
            u'raft_base_acceleration': SettingsDefinition(u'raft_base_acceleration', CuraParsingFunctions.parse_int, [u'misc']),
            u'raft_base_fan_speed': SettingsDefinition(u'raft_base_fan_speed', CuraParsingFunctions.parse_int, [u'misc']),
            u'raft_base_jerk': SettingsDefinition(u'raft_base_jerk', CuraParsingFunctions.parse_int, [u'misc']),
            u'raft_base_line_spacing': SettingsDefinition(u'raft_base_line_spacing', CuraParsingFunctions.parse_float, [u'misc']),
            u'raft_base_line_width': SettingsDefinition(u'raft_base_line_width', CuraParsingFunctions.parse_float, [u'misc']),
            u'raft_base_speed': SettingsDefinition(u'raft_base_speed', CuraParsingFunctions.parse_float, [u'misc']),
            u'raft_base_thickness': SettingsDefinition(u'raft_base_thickness', CuraParsingFunctions.parse_float, [u'misc']),
            u'raft_fan_speed': SettingsDefinition(u'raft_fan_speed', CuraParsingFunctions.parse_int, [u'misc']),
            u'raft_interface_acceleration': SettingsDefinition(u'raft_interface_acceleration', CuraParsingFunctions.parse_int, [u'misc']),
            u'raft_interface_fan_speed': SettingsDefinition(u'raft_interface_fan_speed', CuraParsingFunctions.parse_int, [u'misc']),
            u'raft_interface_jerk': SettingsDefinition(u'raft_interface_jerk', CuraParsingFunctions.parse_int, [u'misc']),
            u'raft_interface_line_spacing': SettingsDefinition(u'raft_interface_line_spacing', CuraParsingFunctions.parse_float, [u'misc']),
            u'raft_interface_line_width': SettingsDefinition(u'raft_interface_line_width', CuraParsingFunctions.parse_float, [u'misc']),
            u'raft_interface_speed': SettingsDefinition(u'raft_interface_speed', CuraParsingFunctions.parse_float, [u'misc']),
            u'raft_interface_thickness': SettingsDefinition(u'raft_interface_thickness', CuraParsingFunctions.parse_float, [u'misc']),
            u'raft_jerk': SettingsDefinition(u'raft_jerk', CuraParsingFunctions.parse_int, [u'misc']),
            u'raft_margin': SettingsDefinition(u'raft_margin', CuraParsingFunctions.parse_int, [u'misc']),
            u'raft_smoothing': SettingsDefinition(u'raft_smoothing', CuraParsingFunctions.parse_int, [u'misc']),
            u'raft_speed': SettingsDefinition(u'raft_speed', CuraParsingFunctions.parse_float, [u'misc']),
            u'raft_surface_acceleration': SettingsDefinition(u'raft_surface_acceleration', CuraParsingFunctions.parse_int, [u'misc']),
            u'raft_surface_fan_speed': SettingsDefinition(u'raft_surface_fan_speed', CuraParsingFunctions.parse_int, [u'misc']),
            u'raft_surface_jerk': SettingsDefinition(u'raft_surface_jerk', CuraParsingFunctions.parse_int, [u'misc']),
            u'raft_surface_layers': SettingsDefinition(u'raft_surface_layers', CuraParsingFunctions.parse_int, [u'misc']),
            u'raft_surface_line_spacing': SettingsDefinition(u'raft_surface_line_spacing', CuraParsingFunctions.parse_float, [u'misc']),
            u'raft_surface_line_width': SettingsDefinition(u'raft_surface_line_width', CuraParsingFunctions.parse_float, [u'misc']),
            u'raft_surface_speed': SettingsDefinition(u'raft_surface_speed', CuraParsingFunctions.parse_float, [u'misc']),
            u'raft_surface_thickness': SettingsDefinition(u'raft_surface_thickness', CuraParsingFunctions.parse_float, [u'misc']),
            u'relative_extrusion': SettingsDefinition(u'relative_extrusion', CuraParsingFunctions.parse_bool, [u'misc']),
            u'remove_empty_first_layers': SettingsDefinition(u'remove_empty_first_layers', CuraParsingFunctions.parse_bool, [u'misc']),
            u'retract_at_layer_change': SettingsDefinition(u'retract_at_layer_change', CuraParsingFunctions.parse_bool, [u'misc']),
            u'retraction_combing_max_distance': SettingsDefinition(u'retraction_combing_max_distance', CuraParsingFunctions.parse_int, [u'misc']),
            u'retraction_count_max': SettingsDefinition(u'retraction_count_max', CuraParsingFunctions.parse_int, [u'misc']),
            u'retraction_extra_prime_amount': SettingsDefinition(u'retraction_extra_prime_amount', CuraParsingFunctions.parse_int, [u'misc']),
            u'retraction_extrusion_window': SettingsDefinition(u'retraction_extrusion_window', CuraParsingFunctions.parse_float, [u'misc']),
            u'retraction_hop_after_extruder_switch': SettingsDefinition(u'retraction_hop_after_extruder_switch', CuraParsingFunctions.parse_bool, [u'misc']),
            u'retraction_hop_only_when_collides': SettingsDefinition(u'retraction_hop_only_when_collides', CuraParsingFunctions.parse_bool, [u'misc']),
            u'retraction_min_travel': SettingsDefinition(u'retraction_min_travel', CuraParsingFunctions.parse_float, [u'misc']),
            u'roofing_extruder_nr': SettingsDefinition(u'roofing_extruder_nr', CuraParsingFunctions.parse_int, [u'misc']),
            u'roofing_layer_count': SettingsDefinition(u'roofing_layer_count', CuraParsingFunctions.parse_int, [u'misc']),
            u'roofing_line_width': SettingsDefinition(u'roofing_line_width', CuraParsingFunctions.parse_float, [u'misc']),
            u'roofing_pattern': SettingsDefinition(u'roofing_pattern', CuraParsingFunctions.strip_string, [u'misc']),
            u'skin_alternate_rotation': SettingsDefinition(u'skin_alternate_rotation', CuraParsingFunctions.parse_bool, [u'misc']),
            u'skin_line_width': SettingsDefinition(u'skin_line_width', CuraParsingFunctions.parse_float, [u'misc']),
            u'skin_no_small_gaps_heuristic': SettingsDefinition(u'skin_no_small_gaps_heuristic', CuraParsingFunctions.parse_bool, [u'misc']),
            u'skin_outline_count': SettingsDefinition(u'skin_outline_count', CuraParsingFunctions.parse_int, [u'misc']),
            u'skin_overlap': SettingsDefinition(u'skin_overlap', CuraParsingFunctions.parse_int, [u'misc']),
            u'skin_overlap_mm': SettingsDefinition(u'skin_overlap_mm', CuraParsingFunctions.parse_float, [u'misc']),
            u'skin_preshrink': SettingsDefinition(u'skin_preshrink', CuraParsingFunctions.parse_float, [u'misc']),
            u'skirt_brim_line_width': SettingsDefinition(u'skirt_brim_line_width', CuraParsingFunctions.parse_float, [u'misc']),
            u'skirt_brim_minimal_length': SettingsDefinition(u'skirt_brim_minimal_length', CuraParsingFunctions.parse_int, [u'misc']),
            u'skirt_gap': SettingsDefinition(u'skirt_gap', CuraParsingFunctions.parse_int, [u'misc']),
            u'skirt_line_count': SettingsDefinition(u'skirt_line_count', CuraParsingFunctions.parse_int, [u'misc']),
            u'slicing_tolerance': SettingsDefinition(u'slicing_tolerance', CuraParsingFunctions.strip_string, [u'misc']),
            u'spaghetti_flow': SettingsDefinition(u'spaghetti_flow', CuraParsingFunctions.parse_int, [u'misc']),
            u'spaghetti_infill_enabled': SettingsDefinition(u'spaghetti_infill_enabled', CuraParsingFunctions.parse_bool, [u'misc']),
            u'spaghetti_infill_extra_volume': SettingsDefinition(u'spaghetti_infill_extra_volume', CuraParsingFunctions.parse_int, [u'misc']),
            u'spaghetti_infill_stepped': SettingsDefinition(u'spaghetti_infill_stepped', CuraParsingFunctions.parse_bool, [u'misc']),
            u'spaghetti_inset': SettingsDefinition(u'spaghetti_inset', CuraParsingFunctions.parse_float, [u'misc']),
            u'spaghetti_max_height': SettingsDefinition(u'spaghetti_max_height', CuraParsingFunctions.parse_float, [u'misc']),
            u'spaghetti_max_infill_angle': SettingsDefinition(u'spaghetti_max_infill_angle', CuraParsingFunctions.parse_int, [u'misc']),
            u'speed_equalize_flow_enabled': SettingsDefinition(u'speed_equalize_flow_enabled', CuraParsingFunctions.parse_bool, [u'misc']),
            u'speed_equalize_flow_max': SettingsDefinition(u'speed_equalize_flow_max', CuraParsingFunctions.parse_int, [u'misc']),
            u'speed_ironing': SettingsDefinition(u'speed_ironing', CuraParsingFunctions.parse_float, [u'misc']),
            u'speed_prime_tower': SettingsDefinition(u'speed_prime_tower', CuraParsingFunctions.parse_int, [u'misc']),
            u'speed_roofing': SettingsDefinition(u'speed_roofing', CuraParsingFunctions.parse_float, [u'misc']),
            u'speed_support': SettingsDefinition(u'speed_support', CuraParsingFunctions.parse_int, [u'misc']),
            u'speed_support_bottom': SettingsDefinition(u'speed_support_bottom', CuraParsingFunctions.parse_float, [u'misc']),
            u'speed_support_infill': SettingsDefinition(u'speed_support_infill', CuraParsingFunctions.parse_int, [u'misc']),
            u'speed_support_interface': SettingsDefinition(u'speed_support_interface', CuraParsingFunctions.parse_float, [u'misc']),
            u'speed_support_roof': SettingsDefinition(u'speed_support_roof', CuraParsingFunctions.parse_float, [u'misc']),
            u'start_layers_at_same_position': SettingsDefinition(u'start_layers_at_same_position', CuraParsingFunctions.parse_bool, [u'misc']),
            u'sub_div_rad_add': SettingsDefinition(u'sub_div_rad_add', CuraParsingFunctions.parse_float, [u'misc']),
            u'support_angle': SettingsDefinition(u'support_angle', CuraParsingFunctions.parse_int, [u'misc']),
            u'support_bottom_density': SettingsDefinition(u'support_bottom_density', CuraParsingFunctions.parse_int, [u'misc']),
            u'support_bottom_distance': SettingsDefinition(u'support_bottom_distance', CuraParsingFunctions.parse_float, [u'misc']),
            u'support_bottom_enable': SettingsDefinition(u'support_bottom_enable', CuraParsingFunctions.parse_bool, [u'misc']),
            u'support_bottom_extruder_nr': SettingsDefinition(u'support_bottom_extruder_nr', CuraParsingFunctions.parse_int, [u'misc']),
            u'support_bottom_height': SettingsDefinition(u'support_bottom_height', CuraParsingFunctions.parse_int, [u'misc']),
            u'support_bottom_line_distance': SettingsDefinition(u'support_bottom_line_distance', CuraParsingFunctions.parse_float, [u'misc']),
            u'support_bottom_line_width': SettingsDefinition(u'support_bottom_line_width', CuraParsingFunctions.parse_float, [u'misc']),
            u'support_bottom_pattern': SettingsDefinition(u'support_bottom_pattern', CuraParsingFunctions.strip_string, [u'misc']),
            u'support_bottom_stair_step_height': SettingsDefinition(u'support_bottom_stair_step_height', CuraParsingFunctions.parse_float, [u'misc']),
            u'support_bottom_stair_step_width': SettingsDefinition(u'support_bottom_stair_step_width', CuraParsingFunctions.parse_float, [u'misc']),
            u'support_brim_enable': SettingsDefinition(u'support_brim_enable', CuraParsingFunctions.parse_bool, [u'misc']),
            u'support_brim_line_count': SettingsDefinition(u'support_brim_line_count', CuraParsingFunctions.parse_int, [u'misc']),
            u'support_brim_width': SettingsDefinition(u'support_brim_width', CuraParsingFunctions.parse_float, [u'misc']),
            u'support_conical_angle': SettingsDefinition(u'support_conical_angle', CuraParsingFunctions.parse_int, [u'misc']),
            u'support_conical_enabled': SettingsDefinition(u'support_conical_enabled', CuraParsingFunctions.parse_bool, [u'misc']),
            u'support_conical_min_width': SettingsDefinition(u'support_conical_min_width', CuraParsingFunctions.parse_float, [u'misc']),
            u'support_connect_zigzags': SettingsDefinition(u'support_connect_zigzags', CuraParsingFunctions.parse_bool, [u'misc']),
            u'support_enable': SettingsDefinition(u'support_enable', CuraParsingFunctions.parse_bool, [u'misc']),
            u'support_extruder_nr': SettingsDefinition(u'support_extruder_nr', CuraParsingFunctions.parse_int, [u'misc']),
            u'support_extruder_nr_layer_0': SettingsDefinition(u'support_extruder_nr_layer_0', CuraParsingFunctions.parse_int, [u'misc']),
            u'support_fan_enable': SettingsDefinition(u'support_fan_enable', CuraParsingFunctions.parse_bool, [u'misc']),
            u'support_infill_angle': SettingsDefinition(u'support_infill_angle', CuraParsingFunctions.parse_int, [u'misc']),
            u'support_infill_extruder_nr': SettingsDefinition(u'support_infill_extruder_nr', CuraParsingFunctions.parse_int, [u'misc']),
            u'support_infill_rate': SettingsDefinition(u'support_infill_rate', CuraParsingFunctions.parse_int, [u'misc']),
            u'support_infill_sparse_thickness': SettingsDefinition(u'support_infill_sparse_thickness', CuraParsingFunctions.parse_float, [u'misc']),
            u'support_initial_layer_line_distance': SettingsDefinition(u'support_initial_layer_line_distance', CuraParsingFunctions.parse_float, [u'misc']),
            u'support_interface_density': SettingsDefinition(u'support_interface_density', CuraParsingFunctions.parse_int, [u'misc']),
            u'support_interface_enable': SettingsDefinition(u'support_interface_enable', CuraParsingFunctions.parse_bool, [u'misc']),
            u'support_interface_extruder_nr': SettingsDefinition(u'support_interface_extruder_nr', CuraParsingFunctions.parse_int, [u'misc']),
            u'support_interface_height': SettingsDefinition(u'support_interface_height', CuraParsingFunctions.parse_int, [u'misc']),
            u'support_interface_line_width': SettingsDefinition(u'support_interface_line_width', CuraParsingFunctions.parse_float, [u'misc']),
            u'support_interface_pattern': SettingsDefinition(u'support_interface_pattern', CuraParsingFunctions.strip_string, [u'misc']),
            u'support_interface_skip_height': SettingsDefinition(u'support_interface_skip_height', CuraParsingFunctions.parse_float, [u'misc']),
            u'support_join_distance': SettingsDefinition(u'support_join_distance', CuraParsingFunctions.parse_float, [u'misc']),
            u'support_line_distance': SettingsDefinition(u'support_line_distance', CuraParsingFunctions.parse_float, [u'misc']),
            u'support_line_width': SettingsDefinition(u'support_line_width', CuraParsingFunctions.parse_float, [u'misc']),
            u'support_mesh': SettingsDefinition(u'support_mesh', CuraParsingFunctions.parse_bool, [u'misc']),
            u'support_mesh_drop_down': SettingsDefinition(u'support_mesh_drop_down', CuraParsingFunctions.parse_bool, [u'misc']),
            u'support_minimal_diameter': SettingsDefinition(u'support_minimal_diameter', CuraParsingFunctions.parse_float, [u'misc']),
            u'support_offset': SettingsDefinition(u'support_offset', CuraParsingFunctions.parse_float, [u'misc']),
            u'support_pattern': SettingsDefinition(u'support_pattern', CuraParsingFunctions.strip_string, [u'misc']),
            u'support_roof_density': SettingsDefinition(u'support_roof_density', CuraParsingFunctions.parse_int, [u'misc']),
            u'support_roof_enable': SettingsDefinition(u'support_roof_enable', CuraParsingFunctions.parse_bool, [u'misc']),
            u'support_roof_extruder_nr': SettingsDefinition(u'support_roof_extruder_nr', CuraParsingFunctions.parse_int, [u'misc']),
            u'support_roof_height': SettingsDefinition(u'support_roof_height', CuraParsingFunctions.parse_int, [u'misc']),
            u'support_roof_line_distance': SettingsDefinition(u'support_roof_line_distance', CuraParsingFunctions.parse_float, [u'misc']),
            u'support_roof_line_width': SettingsDefinition(u'support_roof_line_width', CuraParsingFunctions.parse_float, [u'misc']),
            u'support_roof_pattern': SettingsDefinition(u'support_roof_pattern', CuraParsingFunctions.strip_string, [u'misc']),
            u'support_skip_some_zags': SettingsDefinition(u'support_skip_some_zags', CuraParsingFunctions.parse_bool, [u'misc']),
            u'support_skip_zag_per_mm': SettingsDefinition(u'support_skip_zag_per_mm', CuraParsingFunctions.parse_int, [u'misc']),
            u'support_supported_skin_fan_speed': SettingsDefinition(u'support_supported_skin_fan_speed', CuraParsingFunctions.parse_int, [u'misc']),
            u'support_top_distance': SettingsDefinition(u'support_top_distance', CuraParsingFunctions.parse_float, [u'misc']),
            u'support_tower_diameter': SettingsDefinition(u'support_tower_diameter', CuraParsingFunctions.parse_float, [u'misc']),
            u'support_tower_roof_angle': SettingsDefinition(u'support_tower_roof_angle', CuraParsingFunctions.parse_int, [u'misc']),
            u'support_tree_angle': SettingsDefinition(u'support_tree_angle', CuraParsingFunctions.parse_int, [u'misc']),
            u'support_tree_branch_diameter': SettingsDefinition(u'support_tree_branch_diameter', CuraParsingFunctions.parse_int, [u'misc']),
            u'support_tree_branch_diameter_angle': SettingsDefinition(u'support_tree_branch_diameter_angle', CuraParsingFunctions.parse_int, [u'misc']),
            u'support_tree_branch_distance': SettingsDefinition(u'support_tree_branch_distance', CuraParsingFunctions.parse_int, [u'misc']),
            u'support_tree_collision_resolution': SettingsDefinition(u'support_tree_collision_resolution', CuraParsingFunctions.parse_float, [u'misc']),
            u'support_tree_enable': SettingsDefinition(u'support_tree_enable', CuraParsingFunctions.parse_bool, [u'misc']),
            u'support_tree_wall_count': SettingsDefinition(u'support_tree_wall_count', CuraParsingFunctions.parse_int, [u'misc']),
            u'support_tree_wall_thickness': SettingsDefinition(u'support_tree_wall_thickness', CuraParsingFunctions.parse_float, [u'misc']),
            u'support_type': SettingsDefinition(u'support_type', CuraParsingFunctions.strip_string, [u'misc']),
            u'support_use_towers': SettingsDefinition(u'support_use_towers', CuraParsingFunctions.parse_bool, [u'misc']),
            u'support_wall_count': SettingsDefinition(u'support_wall_count', CuraParsingFunctions.parse_int, [u'misc']),
            u'support_xy_distance': SettingsDefinition(u'support_xy_distance', CuraParsingFunctions.parse_float, [u'misc']),
            u'support_xy_distance_overhang': SettingsDefinition(u'support_xy_distance_overhang', CuraParsingFunctions.parse_float, [u'misc']),
            u'support_xy_overrides_z': SettingsDefinition(u'support_xy_overrides_z', CuraParsingFunctions.strip_string, [u'misc']),
            u'support_z_distance': SettingsDefinition(u'support_z_distance', CuraParsingFunctions.parse_float, [u'misc']),
            u'support_zag_skip_count': SettingsDefinition(u'support_zag_skip_count', CuraParsingFunctions.parse_int, [u'misc']),
            u'switch_extruder_prime_speed': SettingsDefinition(u'switch_extruder_prime_speed', CuraParsingFunctions.parse_int, [u'misc']),
            u'switch_extruder_retraction_amount': SettingsDefinition(u'switch_extruder_retraction_amount', CuraParsingFunctions.parse_int, [u'misc']),
            u'switch_extruder_retraction_speed': SettingsDefinition(u'switch_extruder_retraction_speed', CuraParsingFunctions.parse_int, [u'misc']),
            u'switch_extruder_retraction_speeds': SettingsDefinition(u'switch_extruder_retraction_speeds', CuraParsingFunctions.parse_int, [u'misc']),
            u'top_bottom_extruder_nr': SettingsDefinition(u'top_bottom_extruder_nr', CuraParsingFunctions.parse_int, [u'misc']),
            u'top_bottom_pattern': SettingsDefinition(u'top_bottom_pattern', CuraParsingFunctions.strip_string, [u'misc']),
            u'top_bottom_pattern_0': SettingsDefinition(u'top_bottom_pattern_0', CuraParsingFunctions.strip_string, [u'misc']),
            u'top_bottom_thickness': SettingsDefinition(u'top_bottom_thickness', CuraParsingFunctions.parse_float, [u'misc']),
            u'top_layers': SettingsDefinition(u'top_layers', CuraParsingFunctions.parse_int, [u'misc']),
            u'top_skin_expand_distance': SettingsDefinition(u'top_skin_expand_distance', CuraParsingFunctions.parse_float, [u'misc']),
            u'top_skin_preshrink': SettingsDefinition(u'top_skin_preshrink', CuraParsingFunctions.parse_float, [u'misc']),
            u'top_thickness': SettingsDefinition(u'top_thickness', CuraParsingFunctions.parse_float, [u'misc']),
            u'travel_avoid_distance': SettingsDefinition(u'travel_avoid_distance', CuraParsingFunctions.parse_float, [u'misc']),
            u'travel_avoid_other_parts': SettingsDefinition(u'travel_avoid_other_parts', CuraParsingFunctions.parse_bool, [u'misc']),
            u'travel_avoid_supports': SettingsDefinition(u'travel_avoid_supports', CuraParsingFunctions.parse_bool, [u'misc']),
            u'travel_compensate_overlapping_walls_0_enabled': SettingsDefinition(u'travel_compensate_overlapping_walls_0_enabled', CuraParsingFunctions.parse_bool, [u'misc']),
            u'travel_compensate_overlapping_walls_enabled': SettingsDefinition(u'travel_compensate_overlapping_walls_enabled', CuraParsingFunctions.parse_bool, [u'misc']),
            u'travel_compensate_overlapping_walls_x_enabled': SettingsDefinition(u'travel_compensate_overlapping_walls_x_enabled', CuraParsingFunctions.parse_bool, [u'misc']),
            u'travel_retract_before_outer_wall': SettingsDefinition(u'travel_retract_before_outer_wall', CuraParsingFunctions.parse_bool, [u'misc']),
            u'wall_0_extruder_nr': SettingsDefinition(u'wall_0_extruder_nr', CuraParsingFunctions.parse_int, [u'misc']),
            u'wall_0_inset': SettingsDefinition(u'wall_0_inset', CuraParsingFunctions.parse_int, [u'misc']),
            u'wall_0_wipe_dist': SettingsDefinition(u'wall_0_wipe_dist', CuraParsingFunctions.parse_float, [u'misc']),
            u'wall_extruder_nr': SettingsDefinition(u'wall_extruder_nr', CuraParsingFunctions.parse_int, [u'misc']),
            u'wall_line_count': SettingsDefinition(u'wall_line_count', CuraParsingFunctions.parse_int, [u'misc']),
            u'wall_line_width': SettingsDefinition(u'wall_line_width', CuraParsingFunctions.parse_float, [u'misc']),
            u'wall_line_width_0': SettingsDefinition(u'wall_line_width_0', CuraParsingFunctions.parse_float, [u'misc']),
            u'wall_line_width_x': SettingsDefinition(u'wall_line_width_x', CuraParsingFunctions.parse_float, [u'misc']),
            u'wall_min_flow': SettingsDefinition(u'wall_min_flow', CuraParsingFunctions.parse_int, [u'misc']),
            u'wall_min_flow_retract': SettingsDefinition(u'wall_min_flow_retract', CuraParsingFunctions.parse_bool, [u'misc']),
            u'wall_overhang_angle': SettingsDefinition(u'wall_overhang_angle', CuraParsingFunctions.parse_int, [u'misc']),
            u'wall_overhang_speed_factor': SettingsDefinition(u'wall_overhang_speed_factor', CuraParsingFunctions.parse_int, [u'misc']),
            u'wall_thickness': SettingsDefinition(u'wall_thickness', CuraParsingFunctions.parse_float, [u'misc']),
            u'wall_x_extruder_nr': SettingsDefinition(u'wall_x_extruder_nr', CuraParsingFunctions.parse_int, [u'misc']),
            u'wireframe_bottom_delay': SettingsDefinition(u'wireframe_bottom_delay', CuraParsingFunctions.parse_int, [u'misc']),
            u'wireframe_drag_along': SettingsDefinition(u'wireframe_drag_along', CuraParsingFunctions.parse_int, [u'misc']),
            u'wireframe_enabled': SettingsDefinition(u'wireframe_enabled', CuraParsingFunctions.parse_bool, [u'misc']),
            u'wireframe_fall_down': SettingsDefinition(u'wireframe_fall_down', CuraParsingFunctions.parse_int, [u'misc']),
            u'wireframe_flat_delay': SettingsDefinition(u'wireframe_flat_delay', CuraParsingFunctions.parse_int, [u'misc']),
            u'wireframe_flow': SettingsDefinition(u'wireframe_flow', CuraParsingFunctions.parse_int, [u'misc']),
            u'wireframe_flow_connection': SettingsDefinition(u'wireframe_flow_connection', CuraParsingFunctions.parse_int, [u'misc']),
            u'wireframe_flow_flat': SettingsDefinition(u'wireframe_flow_flat', CuraParsingFunctions.parse_int, [u'misc']),
            u'wireframe_height': SettingsDefinition(u'wireframe_height', CuraParsingFunctions.parse_int, [u'misc']),
            u'wireframe_nozzle_clearance': SettingsDefinition(u'wireframe_nozzle_clearance', CuraParsingFunctions.parse_int, [u'misc']),
            u'wireframe_printspeed': SettingsDefinition(u'wireframe_printspeed', CuraParsingFunctions.parse_int, [u'misc']),
            u'wireframe_printspeed_bottom': SettingsDefinition(u'wireframe_printspeed_bottom', CuraParsingFunctions.parse_int, [u'misc']),
            u'wireframe_printspeed_down': SettingsDefinition(u'wireframe_printspeed_down', CuraParsingFunctions.parse_int, [u'misc']),
            u'wireframe_printspeed_flat': SettingsDefinition(u'wireframe_printspeed_flat', CuraParsingFunctions.parse_int, [u'misc']),
            u'wireframe_printspeed_up': SettingsDefinition(u'wireframe_printspeed_up', CuraParsingFunctions.parse_int, [u'misc']),
            u'wireframe_roof_drag_along': SettingsDefinition(u'wireframe_roof_drag_along', CuraParsingFunctions.parse_float, [u'misc']),
            u'wireframe_roof_fall_down': SettingsDefinition(u'wireframe_roof_fall_down', CuraParsingFunctions.parse_int, [u'misc']),
            u'wireframe_roof_inset': SettingsDefinition(u'wireframe_roof_inset', CuraParsingFunctions.parse_int, [u'misc']),
            u'wireframe_roof_outer_delay': SettingsDefinition(u'wireframe_roof_outer_delay', CuraParsingFunctions.parse_float, [u'misc']),
            u'wireframe_straight_before_down': SettingsDefinition(u'wireframe_straight_before_down', CuraParsingFunctions.parse_int, [u'misc']),
            u'wireframe_strategy': SettingsDefinition(u'wireframe_strategy', CuraParsingFunctions.strip_string, [u'misc']),
            u'wireframe_top_delay': SettingsDefinition(u'wireframe_top_delay', CuraParsingFunctions.parse_int, [u'misc']),
            u'wireframe_top_jump': SettingsDefinition(u'wireframe_top_jump', CuraParsingFunctions.parse_float, [u'misc']),
            u'wireframe_up_half_speed': SettingsDefinition(u'wireframe_up_half_speed', CuraParsingFunctions.parse_float, [u'misc']),
            u'xy_offset': SettingsDefinition(u'xy_offset', CuraParsingFunctions.parse_int, [u'misc']),
            u'xy_offset_layer_0': SettingsDefinition(u'xy_offset_layer_0', CuraParsingFunctions.parse_int, [u'misc']),
            u'z_seam_corner': SettingsDefinition(u'z_seam_corner', CuraParsingFunctions.strip_string, [u'misc']),
            u'z_seam_relative': SettingsDefinition(u'z_seam_relative', CuraParsingFunctions.parse_bool, [u'misc']),
            u'z_seam_type': SettingsDefinition(u'z_seam_type', CuraParsingFunctions.strip_string, [u'misc']),
            u'z_seam_x': SettingsDefinition(u'z_seam_x', CuraParsingFunctions.parse_float, [u'misc']),
            u'z_seam_y': SettingsDefinition(u'z_seam_y', CuraParsingFunctions.parse_int, [u'misc']),
            u'zig_zaggify_infill': SettingsDefinition(u'zig_zaggify_infill', CuraParsingFunctions.parse_bool, [u'misc']),
            u'zig_zaggify_support': SettingsDefinition(u'zig_zaggify_support', CuraParsingFunctions.parse_bool, [u'misc']),

        }

    def get_results(self):
        return self.results

    def version_matched(self, matches):
        if u'version' in self.active_settings_dictionary:
            version = matches.group(u"ver")
            self.results[u"version"] = version
            self.active_settings_dictionary.pop(u'version')
            self.active_regex_definitions.pop('version')
            self.is_slicer_type_detected = True

    def filament_used_meters_matched(self, matches):
        if u'filament_used_meters' in self.active_settings_dictionary:
            filament_used = matches.group(u"meters")
            self.results[u"filament_used_meters"] = float(filament_used)
            self.active_settings_dictionary.pop(u'filament_used_meters')
            self.active_regex_definitions.pop('filament_used_meters')

    def firmware_flavor_matched(self, matches):
        if u'firmware_flavor' in self.active_settings_dictionary:
            firmware_flavor = matches.group(u"flavor")
            self.results[u"firmware_flavor"] = float(firmware_flavor)
            self.active_settings_dictionary.pop(u'firmware_flavor')
            self.active_regex_definitions.pop('firmware_flavor')

    def layer_height_matched(self, matches):
        if u'layer_height' in self.active_settings_dictionary:
            layer_height = matches.group(u"height")
            self.results[u"layer_height"] = float(layer_height)
            self.active_settings_dictionary.pop(u'layer_height')
            self.active_regex_definitions.pop('layer_height')


# class GcodeFileLineProcessor(GcodeProcessor):
#
#     Position = None
#
#     def __init__(
#         self,
#         name,
#         matching_function,
#         max_forward_lines_to_process=None,
#         include_gcode=True,
#         include_comments=True
#     ):
#         super(GcodeFileLineProcessor, self).__init__(name, u'gcode_file_line_processor')
#         # other slicer specific vars
#         self.file_process_type = u'forward'
#         self.file_process_category = u'gcode-file-line'
#         self.max_forward_lines_to_process = max_forward_lines_to_process
#         self.forward_lines_processed = 0
#         self.results = {}
#         self.include_comments = include_comments
#         self.include_gcode = include_gcode
#         self.matching_function = matching_function
#         if not self.include_comments and not self.include_gcode:
#             raise ValueError(u"Both include_gcode and include_comments are false.  One or both must be true.")
#
#         # get the regex last
#         self.regex_definitions = self.get_regex_definitions()
#
#     def reset(self):
#         self.forward_lines_processed = 0
#         self.results = {}
#
#     def get_regex_definitions(self):
#         regexes = []
#         if self.include_gcode and self.include_comments:
#             regexes.append(
#                 RegexDefinition(u"entire_line", u"^(?P<gcode>[^;]*)[;]?(?P<comment>.*$)", self.matching_function)
#             )
#         elif self.include_gcode:
#             regexes.append(
#                 RegexDefinition(u"gcode_only", u"(?P<gcode>[^;]*)", self.matching_function)
#             )
#         elif self.include_comments:
#             regexes.append(
#                 RegexDefinition(u"comment_only", u"(?<=;)(?P<comment>.*$)", self.matching_function)
#             )
#         return regexes
#
#     def on_before_start(self):
#         # reset everything
#         self.reset()
#
#     def on_apply_filter(self, filter_tags=None):
#         pass
#
#     def can_process(self):
#         return True
#
#     def is_complete(self, process_type):
#         if (
#             (
#                 process_type == u"forward"
#                 and self.max_forward_lines_to_process is not None
#                 and self.forward_lines_processed >= self.max_forward_lines_to_process
#             )
#             or len(self.regex_definitions) == 0
#         ):
#             return True
#         return False
#
#     def process_line(self, line, line_number, process_type):
#         line = line.replace(u'\r', '').replace(u'\n', u'')
#         if process_type == "forward":
#             self.forward_lines_processed += 1
#
#         for regex_definition in self.regex_definitions:
#             if regex_definition.match_once and regex_definition.has_matched:
#                 continue
#             match = re.search(regex_definition.regex, line)
#             if not match:
#                 continue
#             regex_definition.has_matched = True
#             self.process_match(match, line, regex_definition)
#             break
#
#     def process_match(self, matches, line_text, regex):
#         # see if we have a matched key
#         if regex.match_function is not None:
#             regex.match_function(matches)
#         else:
#             self.default_matching_function(matches)
#
#     def default_matching_function(self, matches):
#         raise NotImplementedError(u"You must implement the default_matching_function")
#
#     def get_results(self):
#         return self.results
#
