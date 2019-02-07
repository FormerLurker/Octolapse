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
import time
import datetime
from file_read_backwards import FileReadBackwards
import re


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
        forward_processors = [x for x in filtered_processors if x.file_process_type in ['forward', 'both']]
        reverse_processors = [x for x in filtered_processors if x.file_process_type in ['reverse', 'both']]

        # process any forward items
        self.process_forwards(forward_processors, target_file_path)
        self.process_reverse(reverse_processors, target_file_path)

        self.end_time = time.time()
        self.notify_progress(end_progress=True)
        return self.get_processor_results()

    def process_forwards(self, processors, target_file_path):
        # open the file for streaming
        line_number = 0
        # we're using binary read to avoid file.tell() issues with windows
        with open(target_file_path, 'rb') as f:
            while True:
                if len(processors) < 1:
                    break

                line = f.readline()
                if line == '':
                    break

                line_number += 1
                # get the current file position
                self.current_file_position = f.tell()

                has_incomplete_processor = False
                for processor in processors:
                    processor.process_line(line, line_number, 'forward')
                    if not processor.is_complete('forward'):
                        has_incomplete_processor = True

                # previously we wanted to remove any completed processors
                if not has_incomplete_processor:
                    return

                #if processor_completed:
                #    processors[:] = [x for x in processors if not x.is_complete('forward')]

                self.notify_progress()

    def process_reverse(self, processors, target_file_path):
        # open the file for streaming
        line_number = 0
        with FileReadBackwards(target_file_path, encoding="utf-8") as frb:
            while True:
                if len(processors) < 1:
                    break

                line = frb.readline()

                if line == '':
                    break

                line_number += 1
                # get the current file position
                #self.current_file_position = f.tell()

                has_incomplete_processor = False
                for processor in processors:
                    processor.process_line(line, line_number, 'reverse')
                    if not processor.is_complete('reverse'):
                        has_incomplete_processor = True

                # previously we wanted to remove any completed processors
                if not has_incomplete_processor:
                    return

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
        raise NotImplementedError('You must override get_regexes')

    def process_line(self, line, line_number, process_type):
        raise NotImplementedError('You must override process_line')

    def get_results(self):
        raise NotImplementedError('You must override get_results')

    def can_process(self):
        raise NotImplementedError('You must override can_process')

    def on_before_start(self):
        raise NotImplementedError('You must override on_before_start')

    def on_apply_filter(self, filter_tags=None):
        raise NotImplementedError('You must override on_apply_filter')

    def is_complete(self):
        raise NotImplementedError('You must override is_complete')

    @staticmethod
    def get_comment(self, line):
        assert (isinstance(line, str) or isinstance(line, unicode))
        match_position = line.find(';')
        if match_position > -1 and len(line) > match_position + 1:
            return line[match_position + 1:].strip()
        return None


class GcodeSettingsProcessor(GcodeProcessor):

    def __init__(self, name, file_procdss_type, max_forward_lines_to_process, max_reverse_lines_to_process):
        super(GcodeSettingsProcessor, self).__init__(name, 'settings_processor')
        # other slicer specific vars
        self.file_process_type = file_procdss_type
        self.file_process_category = 'settings'
        self.max_forward_lines_to_process = max_forward_lines_to_process
        self.max_reverse_lines_to_process = max_reverse_lines_to_process
        self.forward_lines_processed = 0
        self.reverse_lines_processed = 0
        self.all_settings_dictionary = self.get_settings_dictionary()
        self.results = {}
        self.active_settings_dictionary = {}
        self.regex_definitions = self.get_regex_definitions()

    def reset(self):
        self.forward_lines_processed = 0
        self.reverse_lines_processed = 0
        self.active_settings_dictionary = {}
        self.results = {}

    def get_regex_definitions(self):
        raise NotImplementedError('You must override get_regex_definitions')
    
    @staticmethod
    def get_settings_dictionary():
        raise NotImplementedError('You must override get_settings_dictionary')

    def on_before_start(self):
        # reset everything
        self.reset()

    def on_apply_filter(self, filter_tags=None):
        # copy any matching settings definitions
        for key, setting in self.all_settings_dictionary.items():
            if (
                filter_tags is None
                or len(filter_tags) == 0
                or (setting.tags is not None and len(setting.tags) > 0 and not setting.tags.isdisjoint(filter_tags))
            ):
                self.active_settings_dictionary[key] = SettingsDefinition(
                    setting.name, setting.parsing_function, setting.tags
                )

    def can_process(self):
        return len(self.active_settings_dictionary) > 0

    def is_complete(self, process_type):
        if (
            (process_type == "forward" and self.forward_lines_processed >= self.max_forward_lines_to_process)
            or (process_type == "reverse" and self.reverse_lines_processed >= self.max_reverse_lines_to_process)
            or len(self.active_settings_dictionary) == 0
            or len(self.regex_definitions) == 0
        ):
            return True
        return False

    def process_line(self, line, line_number, process_type):
        line = line.replace('\r', '').replace('\n', '')
        if process_type == "forward":
            self.forward_lines_processed += 1
        elif process_type == "reverse":
            self.reverse_lines_processed += 1

        for regex_definition in self.regex_definitions:
            if regex_definition.match_once and regex_definition.has_matched:
                continue
            match = re.search(regex_definition.regex, line)
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
        key, val = matches.group("key", "val")
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
        str_array = parse_string.split(',')
        results = []
        for float_string in str_array:
            try:
                results.append(ParsingFunctions.parse_int(float_string))
            except ValueError:
                results.append(None)
        return results

    @staticmethod
    def parse_int_pipe_separated_value(parse_string):
        str_array = parse_string.split('|')
        results = []
        for float_string in str_array:
            try:
                results.append(ParsingFunctions.parse_int(float_string))
            except ValueError:
                results.append(None)
        return results

    @staticmethod
    def parse_float_pipe_separated_value(parse_string):
        str_array = parse_string.split('|')
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
        return map(str.strip, parse_string.split(','))

    @staticmethod
    def parse_float_csv(parse_string):
        str_array = parse_string.split(',')
        results = []
        for float_string in str_array:
            try:
                results.append(ParsingFunctions.parse_float(float_string))
            except ValueError:
                results.append(None)
        return results

    @staticmethod
    def parse_bool_csv(parse_string):
        str_array = parse_string.split(',')
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
        if lower_string in ('1', 'yes', 'y', 'true', 't'):
            return True
        elif lower_string in ('0', 'no', 'n', 'false', 'f'):
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
        if parse_string in ('1'):
            return True
        elif parse_string in ('0', '-1'):
            return False
        # didn't match any of our true/false values
        return None

    @staticmethod
    def parse_bool_csv(parse_string):
        str_array = parse_string.split(',')
        results = []
        for float_string in str_array:
            try:
                results.append(Simplify3dParsingFunctions.parse_bool(float_string))
            except ValueError:
                results.append(None)
        return results

    @staticmethod
    def parse_profile_version_datetime(parse_string):
        return datetime.datetime.strptime(parse_string.strip(), "%Y-%m-%d %H:%M:%S")

    @staticmethod
    def try_parse_gcode_create_date(parse_string):
        try:
            return datetime.datetime.strptime(parse_string, "%b %d, %Y at %I:%M:%S %p")
        except:
            return None

    @staticmethod
    def parse_toolhead_offsets(parse_string):
        str_array = parse_string.split('|')
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
        mm_start = parse_string.find('mm')
        if mm_start > -1:
            mm_string = parse_string[0: mm_start].strip()
            return float(mm_string)

    @staticmethod
    def parse_filament_used(parse_string):
        # separate the two values
        str_array = parse_string.split(' ')
        if len(str_array) == 2:
            mm_used = Slic3rParsingFunctions.parse_mm(str_array[0])
            cm3_used = Slic3rParsingFunctions.parse_cm3(str_array[1].encode('utf-8').translate(None, '()'))
            return {
                'mm': mm_used,
                'cm3': cm3_used
            }

    @staticmethod
    def parse_hhmmss(parse_string):
        # separate the two values
        str_array = parse_string.split(' ')
        if len(str_array) == 3:
            hh = Slic3rParsingFunctions.parse_int(str_array[0].encode('utf-8').translate(None, 'h'))
            mm = Slic3rParsingFunctions.parse_int(str_array[1].encode('utf-8').translate(None, 'm'))
            ss = Slic3rParsingFunctions.parse_int(str_array[2].encode('utf-8').translate(None, 's'))
            return {
                'hours': hh,
                'minutes': mm,
                'seconds': ss,
            }

    @staticmethod
    def parse_bed_shape(parse_string):
        str_array = parse_string.split(',')
        flx = None
        fly = None
        frx = None
        fry = None
        rlx = None
        rly = None
        rrx = None
        rry = None

        if len(str_array) == 4:
            fl = str_array[0].split('x')
            if len(fl) == 2:
                flx = Slic3rParsingFunctions.parse_float(fl[0])
                fly = Slic3rParsingFunctions.parse_float(fl[1])
            fr = str_array[0].split('x')
            if len(fr) == 2:
                frx = Slic3rParsingFunctions.parse_float(fr[0])
                fry = Slic3rParsingFunctions.parse_float(fr[1])
            rl = str_array[0].split('x')
            if len(rl) == 2:
                rlx = Slic3rParsingFunctions.parse_float(rl[0])
                rly = Slic3rParsingFunctions.parse_float(rl[1])
            rr = str_array[0].split('x')
            if len(rr) == 2:
                rrx = Slic3rParsingFunctions.parse_float(rr[0])
                rry = Slic3rParsingFunctions.parse_float(rr[1])

        return {
            'front_left': {'x': flx, 'y': fly},
            'front_right': {'x': frx, 'y': fry},
            'rear_left': {'x': rlx, 'y': rly},
            'rear_right': {'x': rrx, 'y': rry},
        }

    @staticmethod
    def parse_xy(parse_string):
        xy = parse_string[0].split('x')
        if len(xy) == 2:
            return {
                'x': Slic3rParsingFunctions.parse_float(xy[0]),
                'y': Slic3rParsingFunctions.parse_float(xy[1])
            }
        return None

    @staticmethod
    def parse_version(parse_string):
        # get version
        on_string = ' on '
        at_string = ' at '
        on_index = parse_string.find(on_string)
        at_index = parse_string.find(at_string)
        version_number = 'unknown'
        version_date = None
        version_time = None

        if on_index > -1:
            version_number = parse_string[0: on_index]
            if at_index > -1:
                version_date = parse_string[on_index + len(on_string):at_index].strip()
                version_time = parse_string[at_index + len(at_string):].strip()

        return {
            'version_number': version_number,
            'version_date': version_date,
            'version_time': version_time,
        }

    @staticmethod
    def parse_cm3(parse_string):
        # remove mm from string
        mm_start = parse_string.find('cm3')
        if mm_start > -1:
            mm_string = parse_string[0: mm_start].strip()
            return float(mm_string)

    @staticmethod
    def parse_percent(parse_string):
        percent_index = parse_string.find('%')
        if percent_index > -1:
            return None
        try:
            percent = float(str(parse_string).translate(None, '%'))
            return {
                'percent': percent
            }
        except ValueError:
            return None
        except Exception as e:
            raise e

    @staticmethod
    def parse_percent_or_mm(parse_string):
        percent_index = parse_string.find('%')
        try:
            if percent_index > -1:
                percent = float(str(parse_string).encode('utf-8').translate(None, '%'))
                return {
                    'percent': percent
                }
            else:
                return {
                    'mm': float(parse_string)
                }
        except ValueError:
            return None


class CuraParsingFunctions(ParsingFunctions):

    @staticmethod
    def parse_filament_used(parse_string):
        # separate the two values
        str_array = parse_string.split(' ')
        if len(str_array) == 2:
            mm_used = Slic3rParsingFunctions.parse_mm(str_array[0])
            cm3_used = Slic3rParsingFunctions.parse_cm3(str_array[1].encode('utf-8').translate(None, '()'))
            return {
                'mm': mm_used,
                'cm3': cm3_used
            }


    @staticmethod
    def parse_version(parse_string):
        # get version
        on_string = ' on '
        at_string = ' at '
        on_index = parse_string.find(on_string)
        at_index = parse_string.find(at_string)
        version_number = 'unknown'
        version_date = None
        version_time = None

        if on_index > -1:
            version_number = parse_string[0: on_index]
            if at_index > -1:
                version_date = parse_string[on_index + len(on_string):at_index].strip()
                version_time = parse_string[at_index + len(at_string):].strip()

        return {
            'version_number': version_number,
            'version_date': version_date,
            'version_time': version_time,
        }


class SettingsDefinition(object):
    def __init__(self, name, parsing_function, tags, ignore_key=False):
        self.name = name
        self.parsing_function = parsing_function
        self.tags = set()
        if tags is not None:
            self.tags = set(tags)
        self.ignore_key = ignore_key


class RegexDefinition(object):
    def __init__(self, name, regex, match_function=None, match_once=False):
        self.name = name
        self.regex_string = regex
        self.regex = re.compile(self.regex_string)
        self.match_function = match_function
        self.match_once = match_once
        self.has_matched = False


    def try_match(self):
        return not (self.match_once and self.has_matched)


#############################################
# Gcode settings processors
# Extends GcodeProcessor
#############################################
class Slic3rSettingsProcessor(GcodeSettingsProcessor):
    def __init__(self, search_direction="both", max_forward_search=50, max_reverse_search=400):
        super(Slic3rSettingsProcessor, self).__init__('slic3r-pe', search_direction, max_forward_search, max_reverse_search)

    def get_regex_definitions(self):
        return [
            RegexDefinition("general_setting", "^; (?P<key>[^,]*?) = (?P<val>.*)", self.default_matching_function),
            RegexDefinition("version", "^; generated by (?P<ver>.*) on (?P<year>[0-9]?[0-9]?[0-9]?[0-9])-(?P<mon>[0-9]?[0-9])-(?P<day>[0-9]?[0-9]) at (?P<hour>[0-9]?[0-9]):(?P<min>[0-9]?[0-9]):(?P<sec>[0-9]?[0-9])$", self.version_matched, True),
        ]

    @staticmethod
    def get_settings_dictionary():
        return {
            # Octolapse Settings
            'retract_length': SettingsDefinition('retract_length', Slic3rParsingFunctions.parse_float,['octolapse_setting']),
            'retract_lift': SettingsDefinition('retract_lift', Slic3rParsingFunctions.parse_float, ['octolapse_setting']),
            'deretract_speed': SettingsDefinition('deretract_speed', Slic3rParsingFunctions.parse_float, ['octolapse_setting']),
            'retract_speed': SettingsDefinition('retract_speed', Slic3rParsingFunctions.parse_float, ['octolapse_setting']),
            'perimeter_speed': SettingsDefinition('perimeter_speed', Slic3rParsingFunctions.parse_float, ['octolapse_setting']),
            'small_perimeter_speed': SettingsDefinition('small_perimeter_speed', Slic3rParsingFunctions.parse_percent_or_mm, ['octolapse_setting']),
            'external_perimeter_speed': SettingsDefinition('external_perimeter_speed', Slic3rParsingFunctions.parse_percent_or_mm, ['octolapse_setting']),
            'infill_speed': SettingsDefinition('infill_speed', Slic3rParsingFunctions.parse_float,['octolapse_setting']),
            'solid_infill_speed': SettingsDefinition('solid_infill_speed', Slic3rParsingFunctions.parse_percent_or_mm,['octolapse_setting']),
            'top_solid_infill_speed': SettingsDefinition('top_solid_infill_speed',Slic3rParsingFunctions.parse_percent_or_mm,['octolapse_setting']),
            'support_material_speed': SettingsDefinition('support_material_speed', Slic3rParsingFunctions.parse_float, ['octolapse_setting']),
            'bridge_speed': SettingsDefinition('bridge_speed', Slic3rParsingFunctions.parse_float, ['octolapse_setting']),
            'gap_fill_speed': SettingsDefinition('gap_fill_speed', Slic3rParsingFunctions.parse_float,['octolapse_setting']),
            'travel_speed': SettingsDefinition('travel_speed', Slic3rParsingFunctions.parse_float, ['octolapse_setting']),
            'first_layer_speed': SettingsDefinition('first_layer_speed', Slic3rParsingFunctions.parse_percent_or_mm,['octolapse_setting']),
            # this setting is not yet used
            'retract_before_travel': SettingsDefinition('retract_before_travel', Slic3rParsingFunctions.parse_float,['octolapse_setting']),
            # this speed is not yet used
            'max_print_speed': SettingsDefinition('max_print_speed', Slic3rParsingFunctions.parse_float, ['octolapse_setting']),
            'version': SettingsDefinition('version', None, ['slicer_info', 'octolapse_setting'], True),
            # End Octolapse Settings - The rest are included in case they become useful for Octolapse or another project

            'external perimeters extrusion width': SettingsDefinition('external_perimeters_extrusion_width', Slic3rParsingFunctions.parse_mm, ['misc']),
            'perimeters extrusion width': SettingsDefinition('perimeters_extrusion_width', Slic3rParsingFunctions.parse_mm, ['misc']),
            'infill extrusion width': SettingsDefinition('infill_extrusion_width', Slic3rParsingFunctions.parse_mm, ['misc']),
            'solid infill extrusion width': SettingsDefinition('solid_infill_extrusion_width', Slic3rParsingFunctions.parse_mm, ['misc']),
            'top infill extrusion width': SettingsDefinition('top_infill_extrusion_width', Slic3rParsingFunctions.parse_mm,['misc']),
            'first layer extrusion width': SettingsDefinition('first_layer_extrusion_width', Slic3rParsingFunctions.parse_mm,['misc']),
            'filament used': SettingsDefinition('filament_used', Slic3rParsingFunctions.parse_filament_used, ['misc']),
            'total filament cost': SettingsDefinition('total_filament_cost', Slic3rParsingFunctions.parse_float, ['misc']),
            'estimated printing time': SettingsDefinition('estimated_printing_time', Slic3rParsingFunctions.parse_hhmmss,['misc']),
            'avoid_crossing_perimeters': SettingsDefinition('avoid_crossing_perimeters', Slic3rParsingFunctions.parse_bool,['misc']),
            'bed_shape': SettingsDefinition('bed_shape', Slic3rParsingFunctions.parse_bed_shape, ['misc']),
            'bed_temperature': SettingsDefinition('bed_temperature', Slic3rParsingFunctions.parse_float, ['misc']),
            'before_layer_gcode': SettingsDefinition('before_layer_gcode', Slic3rParsingFunctions.get_string, ['misc']),
            'between_objects_gcode': SettingsDefinition('between_objects_gcode', Slic3rParsingFunctions.get_string, ['misc']),
            'bridge_acceleration': SettingsDefinition('bridge_acceleration', Slic3rParsingFunctions.parse_float, ['misc']),
            'bridge_fan_speed': SettingsDefinition('bridge_fan_speed', Slic3rParsingFunctions.parse_float, ['misc']),
            'brim_width': SettingsDefinition('brim_width', Slic3rParsingFunctions.parse_float, ['misc']),
            'complete_objects': SettingsDefinition('complete_objects', Slic3rParsingFunctions.parse_bool, ['misc']),
            'cooling': SettingsDefinition('cooling', Slic3rParsingFunctions.parse_bool, ['misc']),
            'cooling_tube_length': SettingsDefinition('cooling_tube_length', Slic3rParsingFunctions.parse_float, ['misc']),
            'cooling_tube_retraction': SettingsDefinition('cooling_tube_retraction', Slic3rParsingFunctions.parse_float, ['misc']),
            'default_acceleration': SettingsDefinition('default_acceleration', Slic3rParsingFunctions.parse_float, ['misc']),
            'disable_fan_first_layers': SettingsDefinition('disable_fan_first_layers', Slic3rParsingFunctions.parse_bool, ['misc']),
            'duplicate_distance': SettingsDefinition('duplicate_distance', Slic3rParsingFunctions.parse_float, ['misc']),
            'end_filament_gcode': SettingsDefinition('end_filament_gcode', Slic3rParsingFunctions.get_string, ['misc']),
            'end_gcode': SettingsDefinition('end_gcode', Slic3rParsingFunctions.get_string, ['misc']),
            'extruder_clearance_height': SettingsDefinition('extruder_clearance_height', Slic3rParsingFunctions.parse_float, ['misc']),
            'extruder_clearance_radius': SettingsDefinition('extruder_clearance_radius', Slic3rParsingFunctions.parse_float, ['misc']),
            'extruder_colour': SettingsDefinition('extruder_colour', Slic3rParsingFunctions.get_string, ['misc']),
            'extruder_offset': SettingsDefinition('extruder_offset', Slic3rParsingFunctions.parse_xy, ['misc']),
            'extrusion_axis': SettingsDefinition('extrusion_axis', Slic3rParsingFunctions.get_string, ['misc']),
            'extrusion_multiplier': SettingsDefinition('extrusion_multiplier', Slic3rParsingFunctions.parse_float, ['misc']),
            'fan_always_on': SettingsDefinition('fan_always_on', Slic3rParsingFunctions.parse_bool, ['misc']),
            'fan_below_layer_time': SettingsDefinition('fan_below_layer_time', Slic3rParsingFunctions.parse_float, ['misc']),
            'filament_colour': SettingsDefinition('filament_colour', Slic3rParsingFunctions.get_string, ['misc']),
            'filament_cost': SettingsDefinition('filament_cost', Slic3rParsingFunctions.parse_float, ['misc']),
            'filament_density': SettingsDefinition('filament_density', Slic3rParsingFunctions.parse_float, ['misc']),
            'filament_diameter': SettingsDefinition('filament_diameter', Slic3rParsingFunctions.parse_float, ['misc']),
            'filament_loading_speed': SettingsDefinition('filament_loading_speed', Slic3rParsingFunctions.parse_float, ['misc']),
            'filament_max_volumetric_speed': SettingsDefinition('filament_max_volumetric_speed', Slic3rParsingFunctions.parse_float, ['misc']),
            'filament_notes': SettingsDefinition('filament_notes', Slic3rParsingFunctions.get_string, ['misc']),
            'filament_ramming_parameters': SettingsDefinition('filament_ramming_parameters', Slic3rParsingFunctions.get_string, ['misc']),
            'filament_soluble': SettingsDefinition('filament_soluble', Slic3rParsingFunctions.parse_bool, ['misc']),
            'filament_toolchange_delay': SettingsDefinition('filament_toolchange_delay', Slic3rParsingFunctions.parse_float, ['misc']),
            'filament_type': SettingsDefinition('filament_type', Slic3rParsingFunctions.get_string, ['misc']),
            'filament_unloading_speed': SettingsDefinition('filament_unloading_speed', Slic3rParsingFunctions.parse_float, ['misc']),
            'first_layer_acceleration': SettingsDefinition('first_layer_acceleration', Slic3rParsingFunctions.parse_float, ['misc']),
            'first_layer_bed_temperature': SettingsDefinition('first_layer_bed_temperature', Slic3rParsingFunctions.parse_float, ['misc']),
            'first_layer_extrusion_width': SettingsDefinition('first_layer_extrusion_width', Slic3rParsingFunctions.parse_float, ['misc']),
            'first_layer_temperature': SettingsDefinition('first_layer_temperature', Slic3rParsingFunctions.parse_float, ['misc']),
            'gcode_comments': SettingsDefinition('gcode_comments', Slic3rParsingFunctions.parse_bool, ['misc']),
            'gcode_flavor': SettingsDefinition('gcode_flavor', Slic3rParsingFunctions.get_string, ['misc']),
            'infill_acceleration': SettingsDefinition('infill_acceleration', Slic3rParsingFunctions.parse_float, ['misc']),
            'infill_first': SettingsDefinition('infill_first', Slic3rParsingFunctions.parse_bool, ['misc']),
            'layer_gcode': SettingsDefinition('layer_gcode', Slic3rParsingFunctions.get_string, ['misc']),
            'max_fan_speed': SettingsDefinition('max_fan_speed', Slic3rParsingFunctions.parse_float, ['misc']),
            'max_layer_height': SettingsDefinition('max_layer_height', Slic3rParsingFunctions.parse_float, ['misc']),
            'max_print_height': SettingsDefinition('max_print_height', Slic3rParsingFunctions.parse_float, ['misc']),
            'max_volumetric_extrusion_rate_slope_negative': SettingsDefinition('max_volumetric_extrusion_rate_slope_negative', Slic3rParsingFunctions.parse_float, ['misc']),
            'max_volumetric_extrusion_rate_slope_positive': SettingsDefinition('max_volumetric_extrusion_rate_slope_positive', Slic3rParsingFunctions.parse_float, ['misc']),
            'max_volumetric_speed': SettingsDefinition('max_volumetric_speed', Slic3rParsingFunctions.parse_float, ['misc']),
            'min_fan_speed': SettingsDefinition('min_fan_speed', Slic3rParsingFunctions.parse_float, ['misc']),
            'min_layer_height': SettingsDefinition('min_layer_height', Slic3rParsingFunctions.parse_float, ['misc']),
            'min_print_speed': SettingsDefinition('min_print_speed', Slic3rParsingFunctions.parse_float, ['misc']),
            'min_skirt_length': SettingsDefinition('min_skirt_length', Slic3rParsingFunctions.parse_float, ['misc']),
            'notes': SettingsDefinition('notes', Slic3rParsingFunctions.get_string, ['misc']),
            'nozzle_diameter': SettingsDefinition('nozzle_diameter', Slic3rParsingFunctions.parse_float, ['misc']),
            'only_retract_when_crossing_perimeters': SettingsDefinition('only_retract_when_crossing_perimeters', Slic3rParsingFunctions.parse_bool, ['misc']),
            'ooze_prevention': SettingsDefinition('ooze_prevention', Slic3rParsingFunctions.parse_bool, ['misc']),
            'output_filename_format': SettingsDefinition('output_filename_format', Slic3rParsingFunctions.get_string, ['misc']),
            'parking_pos_retraction': SettingsDefinition('parking_pos_retraction', Slic3rParsingFunctions.parse_float, ['misc']),
            'perimeter_acceleration': SettingsDefinition('perimeter_acceleration', Slic3rParsingFunctions.parse_float, ['misc']),
            'post_process': SettingsDefinition('post_process', Slic3rParsingFunctions.get_string, ['misc']),
            'printer_notes': SettingsDefinition('printer_notes', Slic3rParsingFunctions.get_string, ['misc']),
            'resolution': SettingsDefinition('resolution', Slic3rParsingFunctions.parse_float, ['misc']),
            'retract_before_wipe': SettingsDefinition('retract_before_wipe', Slic3rParsingFunctions.parse_percent_or_mm, ['misc']),
            'retract_layer_change': SettingsDefinition('retract_layer_change', Slic3rParsingFunctions.parse_bool, ['misc']),
            'retract_length_toolchange': SettingsDefinition('retract_length_toolchange', Slic3rParsingFunctions.parse_float, ['misc']),
            'retract_lift_above': SettingsDefinition('retract_lift_above', Slic3rParsingFunctions.parse_float, ['misc']),
            'retract_lift_below': SettingsDefinition('retract_lift_below', Slic3rParsingFunctions.parse_float, ['misc']),
            'retract_restart_extra': SettingsDefinition('retract_restart_extra', Slic3rParsingFunctions.parse_float, ['misc']),
            'retract_restart_extra_toolchange': SettingsDefinition('retract_restart_extra_toolchange', Slic3rParsingFunctions.parse_float, ['misc']),
            'single_extruder_multi_material': SettingsDefinition('single_extruder_multi_material', Slic3rParsingFunctions.parse_bool, ['misc']),
            'skirt_distance': SettingsDefinition('skirt_distance', Slic3rParsingFunctions.parse_float, ['misc']),
            'skirt_height': SettingsDefinition('skirt_height', Slic3rParsingFunctions.parse_float, ['misc']),
            'skirts': SettingsDefinition('skirts', Slic3rParsingFunctions.parse_bool, ['misc']),
            'slowdown_below_layer_time': SettingsDefinition('slowdown_below_layer_time', Slic3rParsingFunctions.parse_float, ['misc']),
            'spiral_vase': SettingsDefinition('spiral_vase', Slic3rParsingFunctions.parse_bool, ['misc']),
            'standby_temperature_delta': SettingsDefinition('standby_temperature_delta', Slic3rParsingFunctions.parse_float, ['misc']),
            'start_filament_gcode': SettingsDefinition('start_filament_gcode', Slic3rParsingFunctions.get_string, ['misc']),
            'start_gcode': SettingsDefinition('start_gcode', Slic3rParsingFunctions.get_string, ['misc']),
            'temperature': SettingsDefinition('temperature', Slic3rParsingFunctions.parse_float, ['misc']),
            'threads': SettingsDefinition('threads', Slic3rParsingFunctions.parse_int, ['misc']),
            'toolchange_gcode': SettingsDefinition('toolchange_gcode', Slic3rParsingFunctions.get_string, ['misc']),
            'use_firmware_retraction': SettingsDefinition('use_firmware_retraction', Slic3rParsingFunctions.parse_bool, ['misc']),
            'use_relative_e_distances': SettingsDefinition('use_relative_e_distances', Slic3rParsingFunctions.parse_bool, ['misc']),
            'use_volumetric_e': SettingsDefinition('use_volumetric_e', Slic3rParsingFunctions.parse_bool, ['misc']),
            'variable_layer_height': SettingsDefinition('variable_layer_height', Slic3rParsingFunctions.parse_bool, ['misc']),
            'wipe': SettingsDefinition('wipe', Slic3rParsingFunctions.parse_bool, ['misc']),
            'wipe_tower': SettingsDefinition('wipe_tower', Slic3rParsingFunctions.parse_bool, ['misc']),
            'wipe_tower_bridging': SettingsDefinition('wipe_tower_bridging', Slic3rParsingFunctions.parse_float, ['misc']),
            'wipe_tower_rotation_angle': SettingsDefinition('wipe_tower_rotation_angle', Slic3rParsingFunctions.parse_float, ['misc']),
            'wipe_tower_width': SettingsDefinition('wipe_tower_width', Slic3rParsingFunctions.parse_float, ['misc']),
            'wipe_tower_x': SettingsDefinition('wipe_tower_x', Slic3rParsingFunctions.parse_float, ['misc']),
            'wipe_tower_y': SettingsDefinition('wipe_tower_y', Slic3rParsingFunctions.parse_float, ['misc']),
            'wiping_volumes_extruders': SettingsDefinition('wiping_volumes_extruders', Slic3rParsingFunctions.parse_float_csv, ['misc']),
            'wiping_volumes_matrix': SettingsDefinition('wiping_volumes_matrix', Slic3rParsingFunctions.parse_float, ['misc']),
            'z_offset': SettingsDefinition('z_offset', Slic3rParsingFunctions.parse_float, ['misc']),
            'clip_multipart_objects': SettingsDefinition('clip_multipart_objects', Slic3rParsingFunctions.parse_float, ['misc']),
            'dont_support_bridges': SettingsDefinition('dont_support_bridges', Slic3rParsingFunctions.parse_bool, ['misc']),
            'elefant_foot_compensation': SettingsDefinition('elefant_foot_compensation', Slic3rParsingFunctions.parse_bool, ['misc']),
            'extrusion_width': SettingsDefinition('extrusion_width', Slic3rParsingFunctions.parse_float, ['misc']),
            'first_layer_height': SettingsDefinition('first_layer_height', Slic3rParsingFunctions.parse_float, ['misc']),
            'infill_only_where_needed': SettingsDefinition('infill_only_where_needed', Slic3rParsingFunctions.parse_bool, ['misc']),
            'interface_shells': SettingsDefinition('interface_shells', Slic3rParsingFunctions.parse_int, ['misc']),
            'layer_height': SettingsDefinition('layer_height', Slic3rParsingFunctions.parse_float, ['misc']),
            'raft_layers': SettingsDefinition('raft_layers', Slic3rParsingFunctions.parse_int, ['misc']),
            'seam_position': SettingsDefinition('seam_position', Slic3rParsingFunctions.get_string, ['misc']),
            'support_material': SettingsDefinition('support_material', Slic3rParsingFunctions.parse_bool, ['misc']),
            'support_material_angle': SettingsDefinition('support_material_angle', Slic3rParsingFunctions.parse_float, ['misc']),
            'support_material_buildplate_only': SettingsDefinition('support_material_buildplate_only', Slic3rParsingFunctions.parse_bool, ['misc']),
            'support_material_contact_distance': SettingsDefinition('support_material_contact_distance', Slic3rParsingFunctions.parse_float, ['misc']),
            'support_material_enforce_layers': SettingsDefinition('support_material_enforce_layers', Slic3rParsingFunctions.parse_int, ['misc']),
            'support_material_extruder': SettingsDefinition('support_material_extruder', Slic3rParsingFunctions.parse_int, ['misc']),
            'support_material_extrusion_width': SettingsDefinition('support_material_extrusion_width', Slic3rParsingFunctions.parse_float, ['misc']),
            'support_material_interface_contact_loops': SettingsDefinition('support_material_interface_contact_loops', Slic3rParsingFunctions.parse_int, ['misc']),
            'support_material_interface_extruder': SettingsDefinition('support_material_interface_extruder', Slic3rParsingFunctions.parse_int, ['misc']),
            'support_material_interface_layers': SettingsDefinition('support_material_interface_layers', Slic3rParsingFunctions.parse_int, ['misc']),
            'support_material_interface_spacing': SettingsDefinition('support_material_interface_spacing', Slic3rParsingFunctions.parse_float, ['misc']),
            'support_material_interface_speed': SettingsDefinition('support_material_interface_speed',Slic3rParsingFunctions.parse_percent_or_mm,['misc']),
            'support_material_pattern': SettingsDefinition('support_material_pattern', Slic3rParsingFunctions.get_string, ['misc']),
            'support_material_spacing': SettingsDefinition('support_material_spacing', Slic3rParsingFunctions.parse_float, ['misc']),
            'support_material_synchronize_layers': SettingsDefinition('support_material_synchronize_layers', Slic3rParsingFunctions.parse_bool, ['misc']),
            'support_material_threshold': SettingsDefinition('support_material_threshold', Slic3rParsingFunctions.parse_float, ['misc']),
            'support_material_with_sheath': SettingsDefinition('support_material_with_sheath', Slic3rParsingFunctions.parse_bool, ['misc']),
            'support_material_xy_spacing': SettingsDefinition('support_material_xy_spacing', Slic3rParsingFunctions.parse_percent_or_mm, ['misc']),
            'xy_size_compensation': SettingsDefinition('xy_size_compensation', Slic3rParsingFunctions.parse_bool, ['misc']),
            'bottom_solid_layers': SettingsDefinition('bottom_solid_layers', Slic3rParsingFunctions.parse_int, ['misc']),
            'bridge_angle': SettingsDefinition('bridge_angle', Slic3rParsingFunctions.parse_float, ['misc']),
            'bridge_flow_ratio': SettingsDefinition('bridge_flow_ratio', Slic3rParsingFunctions.parse_float, ['misc']),
            'ensure_vertical_shell_thickness': SettingsDefinition('ensure_vertical_shell_thickness', Slic3rParsingFunctions.parse_bool, ['misc']),
            'external_fill_pattern': SettingsDefinition('external_fill_pattern', Slic3rParsingFunctions.get_string, ['misc']),
            'external_perimeter_extrusion_width': SettingsDefinition('external_perimeter_extrusion_width', Slic3rParsingFunctions.parse_float, ['misc']),
            'external_perimeters_first': SettingsDefinition('external_perimeters_first', Slic3rParsingFunctions.parse_percent_or_mm, ['misc']),
            'extra_perimeters': SettingsDefinition('extra_perimeters', Slic3rParsingFunctions.parse_int, ['misc']),
            'fill_angle': SettingsDefinition('fill_angle', Slic3rParsingFunctions.parse_float, ['misc']),
            'fill_density': SettingsDefinition('fill_density', Slic3rParsingFunctions.parse_percent, ['misc']),
            'fill_pattern': SettingsDefinition('fill_pattern', Slic3rParsingFunctions.get_string, ['misc']),
            'infill_every_layers': SettingsDefinition('infill_every_layers', Slic3rParsingFunctions.parse_bool, ['misc']),
            'infill_extruder': SettingsDefinition('infill_extruder', Slic3rParsingFunctions.parse_int, ['misc']),
            'infill_extrusion_width': SettingsDefinition('infill_extrusion_width', Slic3rParsingFunctions.parse_float, ['misc']),
            'infill_overlap': SettingsDefinition('infill_overlap', Slic3rParsingFunctions.parse_percent, ['misc']),
            'overhangs': SettingsDefinition('overhangs', Slic3rParsingFunctions.parse_bool, ['misc']),
            'perimeter_extruder': SettingsDefinition('perimeter_extruder', Slic3rParsingFunctions.parse_int, ['misc']),
            'perimeter_extrusion_width': SettingsDefinition('perimeter_extrusion_width', Slic3rParsingFunctions.parse_float, ['misc']),
            'perimeters': SettingsDefinition('perimeters', Slic3rParsingFunctions.parse_int, ['misc']),
            'solid_infill_below_area': SettingsDefinition('solid_infill_below_area', Slic3rParsingFunctions.parse_bool, ['misc']),
            'solid_infill_every_layers': SettingsDefinition('solid_infill_every_layers', Slic3rParsingFunctions.parse_bool, ['misc']),
            'solid_infill_extruder': SettingsDefinition('solid_infill_extruder', Slic3rParsingFunctions.parse_int, ['misc']),
            'solid_infill_extrusion_width': SettingsDefinition('solid_infill_extrusion_width', Slic3rParsingFunctions.parse_float, ['misc']),
            'thin_walls': SettingsDefinition('thin_walls', Slic3rParsingFunctions.parse_bool, ['misc']),
            'top_infill_extrusion_width': SettingsDefinition('top_infill_extrusion_width', Slic3rParsingFunctions.parse_float, ['misc']),
            'top_solid_layers': SettingsDefinition('top_solid_layers', Slic3rParsingFunctions.parse_int, ['misc']),
        }

    def version_matched(self, matches):
        if "version" in self.active_settings_dictionary:
            setting = self.active_settings_dictionary["version"]
            if setting is not None:
                version, year, month, day, hour, min, sec = matches.group("ver","year", "mon", "day", "hour", "min", "sec")
                self.results["version"] = {
                    "version": version,
                    "date": "{year}-{month}-{day} {hour}:{min}:{sec}".format(
                        year=year, month=month, day=day, hour=hour, min=min, sec=sec
                    )
                }
                self.active_settings_dictionary.pop('version')


class Simplify3dSettingsProcessor(GcodeSettingsProcessor):
    def __init__(self, search_direction="forward", max_forward_search=400, max_reverse_search=0):
        super(Simplify3dSettingsProcessor, self).__init__('simplify-3d', search_direction, max_forward_search, max_reverse_search)

    def get_regex_definitions(self):
        return [
            RegexDefinition("general_setting", "^;\s\s\s(?P<key>.*?),(?P<val>.*)$", self.default_matching_function),
            RegexDefinition("printer_models_override", "^;\s\s\sprinterModelsOverride$", self.printer_modesl_override_matched, True),
            RegexDefinition("version", ";\sG\-Code\sgenerated\sby\sSimplify3D\(R\)\sVersion\s(?P<ver>.*)$", self.version_matched, True),
            RegexDefinition("gocde_date", "^; (?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s(?P<day>[0-9]?[0-9]), (?P<year>[0-9]?[0-9]?[0-9]?[0-9]) at (?P<hour>[0-9]?[0-9]):(?P<min>[0-9]?[0-9]):(?P<sec>[0-9]?[0-9])\s(?P<period>AM|PM)$", self.gcode_date_matched, True)
        ]

    @staticmethod
    def get_settings_dictionary():
        return {
            # Octolapse Settings
            'primaryExtruder': SettingsDefinition('primary_extruder', Simplify3dParsingFunctions.parse_int,['extruder', 'octolapse_setting']),
            'extruderRetractionDistance': SettingsDefinition('extruder_retraction_distance',Simplify3dParsingFunctions.parse_float_csv,['extruder', 'octolapse_setting']),
            'extruderRetractionZLift': SettingsDefinition('extruder_retraction_z_lift',Simplify3dParsingFunctions.parse_float_csv,['extruder', 'octolapse_setting']),
            'extruderRetractionSpeed': SettingsDefinition('extruder_retraction_speed',Simplify3dParsingFunctions.parse_float_csv,['extruder', 'octolapse_setting']),
            'firstLayerUnderspeed': SettingsDefinition('first_layer_underspeed', Simplify3dParsingFunctions.parse_float,['octolapse_setting']),
            'aboveRaftSpeedMultiplier': SettingsDefinition('above_raft_speed_multiplier',Simplify3dParsingFunctions.parse_float,['octolapse_setting']),
            'primePillarSpeedMultiplier': SettingsDefinition('prime_pillar_speed_multiplier',Simplify3dParsingFunctions.parse_float,['octolapse_setting']),
            'oozeShieldSpeedMultiplier': SettingsDefinition('ooze_shield_speed_multiplier',Simplify3dParsingFunctions.parse_float,['octolapse_setting']),
            'defaultSpeed': SettingsDefinition('default_speed', Simplify3dParsingFunctions.parse_float,['octolapse_setting']),
            'outlineUnderspeed': SettingsDefinition('outline_underspeed', Simplify3dParsingFunctions.parse_float,['octolapse_setting']),
            'solidInfillUnderspeed': SettingsDefinition('solid_infill_underspeed',Simplify3dParsingFunctions.parse_float, ['octolapse_setting']),
            'supportUnderspeed': SettingsDefinition('support_underspeed', Simplify3dParsingFunctions.parse_float,['octolapse_setting']),
            'rapidXYspeed': SettingsDefinition('rapid_xy_speed', Simplify3dParsingFunctions.parse_float,['octolapse_setting']),
            'rapidZspeed': SettingsDefinition('rapid_z_speed', Simplify3dParsingFunctions.parse_float,['octolapse_setting']),
            'bridgingSpeedMultiplier': SettingsDefinition('bridging_speed_multiplier',Simplify3dParsingFunctions.parse_float,['octolapse_setting']),
            'extruderUseRetract': SettingsDefinition('extruder_use_retract', Simplify3dParsingFunctions.parse_bool_csv,['extruder', 'octolapse_setting']),
            'spiralVaseMode': SettingsDefinition('spiral_vase_mode', Simplify3dParsingFunctions.parse_bool, ['octolapse_setting']),
            # End Octolapse Settings - The rest is included in case it is ever useful for Octolapse of another project!
            'version': SettingsDefinition('version', Simplify3dParsingFunctions.strip_string, ['slicer_info'], True),
            'gcodeDate': SettingsDefinition('gcode_date', Simplify3dParsingFunctions.strip_string, ['gcode_info'], True),
            # IMPORTANT NOTE - printerModelsOverride does NOT have a comma if it's empty
            'printerModelsOverride': SettingsDefinition('printer_models_override', Simplify3dParsingFunctions.parse_printer_models_override, ['misc']),
            'processName': SettingsDefinition('process_name', Simplify3dParsingFunctions.strip_string, ['misc']),
            'applyToModels': SettingsDefinition('apply_to_models', Simplify3dParsingFunctions.parse_string_csv, ['misc']),
            'profileName':SettingsDefinition('profile_name', Simplify3dParsingFunctions.strip_string, ['profile']),
            'profileVersion':SettingsDefinition('profile_version', Simplify3dParsingFunctions.parse_profile_version_datetime, ['profile']),
            'baseProfile':SettingsDefinition('profile_base', Simplify3dParsingFunctions.strip_string, ['profile']),
            'printMaterial': SettingsDefinition('print_material', Simplify3dParsingFunctions.strip_string, ['material']),
            'printQuality':SettingsDefinition('print_quality', Simplify3dParsingFunctions.strip_string, ['misc']),
            'printExtruders':SettingsDefinition('print_extruders', Simplify3dParsingFunctions.parse_string_csv, ['extruder']),
            'extruderName': SettingsDefinition('extruder_names',  Simplify3dParsingFunctions.parse_string_csv, ['extruder']),
            'extruderToolheadNumber': SettingsDefinition('extruder_tool_number', Simplify3dParsingFunctions.parse_string_csv, ['extruder']),
            'extruderDiameter': SettingsDefinition('extrueder_diameter',  Simplify3dParsingFunctions.parse_float_csv, ['extruder']),
            'extruderAutoWidth': SettingsDefinition('extruder_auto_width', Simplify3dParsingFunctions.parse_bool_csv, ['extruder']),
            'extruderWidth': SettingsDefinition('extruder_width', Simplify3dParsingFunctions.parse_float_csv, ['extruder']),
            'extrusionMultiplier': SettingsDefinition('extrusion_multiplier', Simplify3dParsingFunctions.parse_float_csv, ['extruder']),
            'extruderExtraRestartDistance': SettingsDefinition('extruder_extra_restart_distance', Simplify3dParsingFunctions.parse_float_csv, ['extruder']),
            'extruderUseCoasting': SettingsDefinition('extruder_use_coasting', Simplify3dParsingFunctions.parse_bool_csv, ['extruder']),
            'extruderCoastingDistance': SettingsDefinition('extruder_coasting_distance', Simplify3dParsingFunctions.parse_float_csv, ['extruder']),
            'extruderUseWipe': SettingsDefinition('extruder_use_wipe', Simplify3dParsingFunctions.parse_bool_csv, ['extruder']),
            'extruderWipeDistance': SettingsDefinition('extruder_wipe_distance', Simplify3dParsingFunctions.parse_float_csv, ['extruder']),
            'layerHeight': SettingsDefinition('layer_height', Simplify3dParsingFunctions.parse_float, ['misc']),
            'topSolidLayers': SettingsDefinition('top_solid_layers', Simplify3dParsingFunctions.parse_int, ['misc']),
            'bottomSolidLayers': SettingsDefinition('bottom_solid_layers', Simplify3dParsingFunctions.parse_int, ['misc']),
            'perimeterOutlines': SettingsDefinition('perimeter_outlines', Simplify3dParsingFunctions.parse_int, ['misc']),
            'printPerimetersInsideOut': SettingsDefinition('print_perimeters_inside_out',  Simplify3dParsingFunctions.parse_bool, ['misc']),
            'startPointOption': SettingsDefinition('start_print_options', Simplify3dParsingFunctions.parse_int, ['misc']),
            'startPointOriginX': SettingsDefinition('start_point_origin_x', Simplify3dParsingFunctions.parse_float, ['misc']),
            'startPointOriginY': SettingsDefinition('start_point_origin_y', Simplify3dParsingFunctions.parse_float, ['misc']),
            'sequentialIslands': SettingsDefinition('sequential_islands', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'firstLayerHeightPercentage': SettingsDefinition('first_layer_height_percentage', Simplify3dParsingFunctions.parse_int, ['misc']),
            'firstLayerWidthPercentage': SettingsDefinition('first_layer_width_percentage', Simplify3dParsingFunctions.parse_int, ['misc']),
            'useRaft': SettingsDefinition('use_raft', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'raftExtruder': SettingsDefinition('raft_extruder', Simplify3dParsingFunctions.parse_int, ['misc']),
            'raftTopLayers': SettingsDefinition('raft_top_layers', Simplify3dParsingFunctions.parse_int, ['misc']),
            'raftBaseLayers':  SettingsDefinition('raft_base_layers', Simplify3dParsingFunctions.parse_int, ['misc']),
            'raftOffset': SettingsDefinition('raft_offset', Simplify3dParsingFunctions.parse_float, ['misc']),
            'raftSeparationDistance': SettingsDefinition('raft_separation_distance', Simplify3dParsingFunctions.parse_float, ['misc']),
            'raftTopInfill': SettingsDefinition('raft_top_infill', Simplify3dParsingFunctions.parse_int, ['misc']),
            'useSkirt':  SettingsDefinition('use_skirt', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'skirtExtruder': SettingsDefinition('skirt_extruder', Simplify3dParsingFunctions.parse_int, ['misc']),
            'skirtLayers': SettingsDefinition('skirt_layers', Simplify3dParsingFunctions.parse_int, ['misc']),
            'skirtOutlines': SettingsDefinition('skirt_outlines', Simplify3dParsingFunctions.parse_int, ['misc']),
            'skirtOffset': SettingsDefinition('skirt_offset', Simplify3dParsingFunctions.parse_float, ['misc']),
            'usePrimePillar': SettingsDefinition('use_prime_pillar', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'primePillarExtruder': SettingsDefinition('prime_pillar_extruder',  Simplify3dParsingFunctions.parse_int, ['misc']),
            'primePillarWidth': SettingsDefinition('prime_pillar_width', Simplify3dParsingFunctions.parse_float, ['misc']),
            'primePillarLocation': SettingsDefinition('prime_pillar_location', Simplify3dParsingFunctions.parse_int, ['misc']),
            'useOozeShield': SettingsDefinition('use_ooze_shield', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'oozeShieldExtruder': SettingsDefinition('ooze_shield_extruder',  Simplify3dParsingFunctions.parse_int, ['misc']),
            'oozeShieldOffset': SettingsDefinition('ooze_shield_offset', Simplify3dParsingFunctions.parse_float, ['misc']),
            'oozeShieldOutlines': SettingsDefinition('ooze_shield_outlines', Simplify3dParsingFunctions.parse_int, ['misc']),
            'oozeShieldSidewallShape': SettingsDefinition('ooze_shield_sidewall_shape', Simplify3dParsingFunctions.parse_int, ['misc']),
            'oozeShieldSidewallAngle': SettingsDefinition('ooze_shield_sidewall_angle', Simplify3dParsingFunctions.parse_int, ['misc']),
            'infillExtruder':  SettingsDefinition('infill_extruder',  Simplify3dParsingFunctions.parse_int, ['misc']),
            'internalInfillPattern': SettingsDefinition('internal_infill_pattern',  Simplify3dParsingFunctions.strip_string, ['misc']),
            'externalInfillPattern': SettingsDefinition('external_infill_pattern', Simplify3dParsingFunctions.strip_string, ['misc']),
            'infillPercentage': SettingsDefinition('infill_percentage', Simplify3dParsingFunctions.parse_int, ['misc']),
            'outlineOverlapPercentage': SettingsDefinition('outline_overlap_percentage', Simplify3dParsingFunctions.parse_int, ['misc']),
            'infillExtrusionWidthPercentage': SettingsDefinition('infill_extrusion_width_percentage',  Simplify3dParsingFunctions.parse_int, ['misc']),
            'minInfillLength': SettingsDefinition('min_infill_length', Simplify3dParsingFunctions.parse_float, ['misc']),
            'infillLayerInterval': SettingsDefinition('infill_layer_interval', Simplify3dParsingFunctions.parse_int, ['misc']),
            'internalInfillAngles': SettingsDefinition('internal_infill_angles', Simplify3dParsingFunctions.parse_int_csv, ['misc']),
            'overlapInternalInfillAngles': SettingsDefinition('overlap_internal_infill_angles', Simplify3dParsingFunctions.parse_int, ['misc']),
            'externalInfillAngles': SettingsDefinition('external_infill_angles', Simplify3dParsingFunctions.parse_int_csv, ['misc']),
            'generateSupport': SettingsDefinition('generate_support',  Simplify3dParsingFunctions.parse_bool, ['misc']),
            'supportExtruder': SettingsDefinition('support_extruder',  Simplify3dParsingFunctions.parse_int, ['misc']),
            'supportInfillPercentage': SettingsDefinition('support_infill_percentage', Simplify3dParsingFunctions.parse_int, ['misc']),
            'supportExtraInflation': SettingsDefinition('support_extra_inflation',  Simplify3dParsingFunctions.parse_float, ['misc']),
            'supportBaseLayers': SettingsDefinition('support_base_layers',  Simplify3dParsingFunctions.parse_int, ['misc']),
            'denseSupportExtruder': SettingsDefinition('dense_support_extruder', Simplify3dParsingFunctions.parse_int, ['misc']),
            'denseSupportLayers': SettingsDefinition('dense_support_layers',  Simplify3dParsingFunctions.parse_int, ['misc']),
            'denseSupportInfillPercentage': SettingsDefinition('dense_support_infill_percentage',  Simplify3dParsingFunctions.parse_int, ['misc']),
            'supportLayerInterval': SettingsDefinition('support_layer_interval',  Simplify3dParsingFunctions.parse_int, ['misc']),
            'supportHorizontalPartOffset': SettingsDefinition('support_horizontal_part_offset',  Simplify3dParsingFunctions.parse_float, ['misc']),
            'supportUpperSeparationLayers': SettingsDefinition('support_upper_separation_layers', Simplify3dParsingFunctions.parse_int, ['misc']),
            'supportLowerSeparationLayers': SettingsDefinition('support_lower_separation_layers', Simplify3dParsingFunctions.parse_int, ['misc']),
            'supportType': SettingsDefinition('support_type', Simplify3dParsingFunctions.parse_int, ['misc']),
            'supportGridSpacing': SettingsDefinition('support_grid_spacing', Simplify3dParsingFunctions.parse_float, ['misc']),
            'maxOverhangAngle': SettingsDefinition('max_overhead_angle', Simplify3dParsingFunctions.parse_int, ['misc']),
            'supportAngles': SettingsDefinition('support_angles', Simplify3dParsingFunctions.parse_int_csv, ['misc']),
            'temperatureName': SettingsDefinition('temperature_name', Simplify3dParsingFunctions.parse_string_csv, ['misc']),
            'temperatureNumber': SettingsDefinition('temperature_number', Simplify3dParsingFunctions.parse_int_csv, ['misc']),
            'temperatureSetpointCount': SettingsDefinition('temperature_setpoint_count', Simplify3dParsingFunctions.parse_int_csv, ['misc']),
            'temperatureSetpointLayers': SettingsDefinition('temperature_setpoint_layers',  Simplify3dParsingFunctions.parse_int_csv, ['misc']),
            'temperatureSetpointTemperatures': SettingsDefinition('temperature_setpoint_temperatures',  Simplify3dParsingFunctions.parse_int_csv, ['misc']),
            'temperatureStabilizeAtStartup': SettingsDefinition('temperature_stabilize_at_startup',  Simplify3dParsingFunctions.parse_bool_csv, ['misc']),
            'temperatureHeatedBed': SettingsDefinition('temperature_heated_bed',  Simplify3dParsingFunctions.parse_bool_csv, ['misc']),
            'temperatureRelayBetweenLayers': SettingsDefinition('temperature_relay_between_layers', Simplify3dParsingFunctions.parse_bool_csv, ['misc']),
            'temperatureRelayBetweenLoops': SettingsDefinition('temperature_relay_between_loops', Simplify3dParsingFunctions.parse_bool_csv, ['misc']),
            'fanLayers': SettingsDefinition('fan_layers', Simplify3dParsingFunctions.parse_int_csv, ['misc']),
            'fanSpeeds': SettingsDefinition('fan_speeds', Simplify3dParsingFunctions.parse_int_csv, ['misc']),
            'blipFanToFullPower': SettingsDefinition('blip_fan_to_full_power',  Simplify3dParsingFunctions.parse_bool, ['misc']),
            'adjustSpeedForCooling': SettingsDefinition('adjust_speed_for_cooling',  Simplify3dParsingFunctions.parse_bool, ['misc']),
            'minSpeedLayerTime': SettingsDefinition('min_speed_layer_time',  Simplify3dParsingFunctions.parse_float, ['misc']),
            'minCoolingSpeedSlowdown': SettingsDefinition('min_cooling_speed_slowdown',  Simplify3dParsingFunctions.parse_int, ['misc']),
            'increaseFanForCooling': SettingsDefinition('increase_fan_for_cooling',  Simplify3dParsingFunctions.parse_bool, ['misc']),
            'minFanLayerTime': SettingsDefinition('min_fan_layer_time',  Simplify3dParsingFunctions.parse_float, ['misc']),
            'maxCoolingFanSpeed': SettingsDefinition('max_cooling_fan_speed', Simplify3dParsingFunctions.parse_int, ['misc']),
            'increaseFanForBridging': SettingsDefinition('increase_fan_for_bridging', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'bridgingFanSpeed': SettingsDefinition('bridging_fan_speed',  Simplify3dParsingFunctions.parse_int, ['misc']),
            'use5D': SettingsDefinition('use_5d',  Simplify3dParsingFunctions.parse_bool, ['misc']),
            'relativeEdistances': SettingsDefinition('relative_e_distances',  Simplify3dParsingFunctions.parse_bool, ['misc']),
            'allowEaxisZeroing': SettingsDefinition('allow_e_axis_zeroing', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'independentExtruderAxes': SettingsDefinition('independent_extruder_axes', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'includeM10123': SettingsDefinition('include_m_101_102_103_commands', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'stickySupport': SettingsDefinition('sticky_support', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'applyToolheadOffsets': SettingsDefinition('apply_toolhead_offsets', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'gcodeXoffset': SettingsDefinition('gcode_x_offset', Simplify3dParsingFunctions.parse_float, ['misc']),
            'gcodeYoffset': SettingsDefinition('gcode_y_offset', Simplify3dParsingFunctions.parse_float, ['misc']),
            'gcodeZoffset': SettingsDefinition('gcode_z_offset', Simplify3dParsingFunctions.parse_float, ['misc']),
            'overrideMachineDefinition': SettingsDefinition('override_machine_definition', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'machineTypeOverride': SettingsDefinition('machine_type_override', Simplify3dParsingFunctions.parse_int, ['misc']),
            'strokeXoverride': SettingsDefinition('stroke_x_override', Simplify3dParsingFunctions.parse_float, ['printer_volume']),
            'strokeYoverride': SettingsDefinition('stroke_y_override', Simplify3dParsingFunctions.parse_float, ['printer_volume']),
            'strokeZoverride': SettingsDefinition('stroke_z_override', Simplify3dParsingFunctions.parse_float, ['printer_volume']),
            'originOffsetXoverride': SettingsDefinition('origin_offset_x_override', Simplify3dParsingFunctions.parse_float, ['misc']),
            'originOffsetYoverride': SettingsDefinition('origin_offset_y_override', Simplify3dParsingFunctions.parse_float, ['misc']),
            'originOffsetZoverride': SettingsDefinition('origin_offset_z_override', Simplify3dParsingFunctions.parse_float, ['misc']),
            'homeXdirOverride': SettingsDefinition('home_x_direction_override',  Simplify3dParsingFunctions.parse_bool, ['misc']),
            'homeYdirOverride': SettingsDefinition('home_y_direction_override', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'homeZdirOverride': SettingsDefinition('home_z_direction_override', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'flipXoverride': SettingsDefinition('flip_x_override', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'flipYoverride': SettingsDefinition('flip_y_override', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'flipZoverride': SettingsDefinition('flip_z_override', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'toolheadOffsets': SettingsDefinition('toolhead_offsets', Simplify3dParsingFunctions.parse_toolhead_offsets, ['misc']),
            'overrideFirmwareConfiguration': SettingsDefinition('override_firmware_configuration', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'firmwareTypeOverride': SettingsDefinition('firmware_type_override', Simplify3dParsingFunctions.strip_string, ['misc']),
            'GPXconfigOverride': SettingsDefinition('gpx_config_override',  Simplify3dParsingFunctions.strip_string, ['misc']),
            'baudRateOverride': SettingsDefinition('baud_rate_override',  Simplify3dParsingFunctions.parse_int, ['misc']),
            'overridePrinterModels': SettingsDefinition('override_printer_models', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'startingGcode': SettingsDefinition('starting_gcode', Simplify3dParsingFunctions.parse_string_csv, ['misc']),
            'layerChangeGcode': SettingsDefinition('layer_change_gcode', Simplify3dParsingFunctions.parse_string_csv, ['misc']),
            'retractionGcode': SettingsDefinition('retraction_gcode', Simplify3dParsingFunctions.parse_string_csv, ['misc']),
            'toolChangeGcode': SettingsDefinition('tool_change_gcode', Simplify3dParsingFunctions.parse_string_csv, ['misc']),
            'endingGcode': SettingsDefinition('ending_gcode', Simplify3dParsingFunctions.parse_string_csv, ['misc']),
            'exportFileFormat': SettingsDefinition('export_file_format', Simplify3dParsingFunctions.strip_string, ['misc']),
            'celebration': SettingsDefinition('celebration',Simplify3dParsingFunctions.parse_bool, ['misc']),
            'celebrationSong': SettingsDefinition('celebration_song', Simplify3dParsingFunctions.strip_string, ['misc']),
            'postProcessing': SettingsDefinition('post_processing', Simplify3dParsingFunctions.parse_string_csv, ['misc']),
            'minBridgingArea': SettingsDefinition('min_bridging_area', Simplify3dParsingFunctions.parse_float, ['misc']),
            'bridgingExtraInflation': SettingsDefinition('bridging_extra_inflation', Simplify3dParsingFunctions.parse_float, ['misc']),
            'bridgingExtrusionMultiplier': SettingsDefinition('bridging_extrusion_multiplier', Simplify3dParsingFunctions.parse_float, ['misc']),
            'useFixedBridgingAngle': SettingsDefinition('use_fixed_bridging_angle', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'fixedBridgingAngle': SettingsDefinition('fixed_bridging_angle', Simplify3dParsingFunctions.parse_int, ['misc']),
            'applyBridgingToPerimeters': SettingsDefinition('apply_bridging_to_perimeters', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'filamentDiameters': SettingsDefinition('filament_diameters', Simplify3dParsingFunctions.parse_float_pipe_separated_value, ['misc']),
            'filamentPricesPerKg': SettingsDefinition('filament_prices_per_kg',  Simplify3dParsingFunctions.parse_float_pipe_separated_value, ['misc']),
            'filamentDensities': SettingsDefinition('filament_densities', Simplify3dParsingFunctions.parse_float_pipe_separated_value, ['misc']),
            'useMinPrintHeight': SettingsDefinition('use_min_print_height', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'minPrintHeight': SettingsDefinition('min_print_height', Simplify3dParsingFunctions.parse_float, ['misc']),
            'useMaxPrintHeight': SettingsDefinition('use_max_print_height', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'maxPrintHeight': SettingsDefinition('max_print_height', Simplify3dParsingFunctions.parse_float, ['misc']),
            'useDiaphragm': SettingsDefinition('use_diaphragm', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'diaphragmLayerInterval': SettingsDefinition('diaphragm_layer_interval', Simplify3dParsingFunctions.parse_int, ['misc']),
            'robustSlicing': SettingsDefinition('robust_slicing', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'mergeAllIntoSolid': SettingsDefinition('merge_all_into_solid', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'onlyRetractWhenCrossingOutline': SettingsDefinition('only_retract_when_crossing_outline', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'retractBetweenLayers': SettingsDefinition('retract_between_layers', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'useRetractionMinTravel': SettingsDefinition('use_retraction_min_travel', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'retractionMinTravel': SettingsDefinition('retraction_min_travel', Simplify3dParsingFunctions.parse_float, ['misc']),
            'retractWhileWiping': SettingsDefinition('retract_while_wiping', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'onlyWipeOutlines': SettingsDefinition('only_wipe_outlines', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'avoidCrossingOutline': SettingsDefinition('avoid_crossing_outline', Simplify3dParsingFunctions.parse_bool, ['misc']),
            'maxMovementDetourFactor': SettingsDefinition('max_movement_detour_factor', Simplify3dParsingFunctions.parse_float, ['misc']),
            'toolChangeRetractionDistance': SettingsDefinition('tool_change_retraction_distance', Simplify3dParsingFunctions.parse_float, ['misc']),
            'toolChangeExtraRestartDistance': SettingsDefinition('tool_change_extra_restart_distance', Simplify3dParsingFunctions.parse_float, ['misc']),
            'toolChangeRetractionSpeed': SettingsDefinition('tool_change_retraction_speed', Simplify3dParsingFunctions.parse_float, ['misc']),
            'externalThinWallType': SettingsDefinition('external_thin_wall_type', Simplify3dParsingFunctions.parse_int, ['misc']),
            'internalThinWallType': SettingsDefinition('internal_thin_wall_type', Simplify3dParsingFunctions.parse_int, ['misc']),
            'thinWallAllowedOverlapPercentage': SettingsDefinition('thin_wall_allowed_overlap_percentage', Simplify3dParsingFunctions.parse_int, ['misc']),
            'singleExtrusionMinLength': SettingsDefinition('single_extrusion_min_length',  Simplify3dParsingFunctions.parse_float, ['misc']),
            'singleExtrusionMinPrintingWidthPercentage': SettingsDefinition('single_extrusion_min_printing_width_percentage', Simplify3dParsingFunctions.parse_int, ['misc']),
            'singleExtrusionMaxPrintingWidthPercentage': SettingsDefinition('single_extrusion_max_printing_width_percentage', Simplify3dParsingFunctions.parse_int, ['misc']),
            'singleExtrusionEndpointExtension': SettingsDefinition('single_extrusion_endpoint_extension', Simplify3dParsingFunctions.parse_float, ['misc']),
            'horizontalSizeCompensation': SettingsDefinition('horizontal_size_compensation', Simplify3dParsingFunctions.parse_float, ['misc']),
        }

    def get_results(self):
        return self.results

    def version_matched(self, matches):
        if "version" in self.active_settings_dictionary:
            setting = self.active_settings_dictionary["version"]
            if setting is not None:
                version = matches.group("ver")
                self.results["version"] = version
                self.active_settings_dictionary.pop('version')

    def gcode_date_matched(self, matches):
        if "gcodeDate" in self.active_settings_dictionary:
            setting = self.active_settings_dictionary["gcodeDate"]
            if setting is not None:
                month, day, year, hour, min, sec, period = matches.group("month", "day", "year", "hour", "min", "sec",
                                                                         "period")
                self.results["gcode_date"] = "{year}-{month}-{day} {hour}:{min}:{sec} {period}".format(
                    year=year, month=month, day=day, hour=hour, min=min, sec=sec, period=period
                )
                self.active_settings_dictionary.pop('gcodeDate')

    def printer_modesl_override_matched(self, matches):
        if "printerModelsOverride" in self.active_settings_dictionary:
            setting = self.active_settings_dictionary["printerModelsOverride"]
            if setting is not None:
                self.results[setting.name] = None
                self.active_settings_dictionary.pop('printerModelsOverride')


class CuraSettingsProcessor(GcodeSettingsProcessor):
    def __init__(self, search_direction="both", max_forward_search=400, max_reverse_search=0):
        super(CuraSettingsProcessor, self).__init__('cura', search_direction, max_forward_search, max_reverse_search)

    def get_regex_definitions(self):
        return [
            RegexDefinition("general_setting", "^; (?P<key>[^,]*?) = (?P<val>.*)", self.default_matching_function),
            RegexDefinition("version", "^;Generated\swith\sCura_SteamEngine\s(?P<ver>.*)$",self.version_matched,True),
            RegexDefinition("filament_used_meters", "^;Filament\sused:\s(?P<meters>.*)m$", self.filament_used_meters_matched, True),
            RegexDefinition("firmware_flavor", "^;FLAVOR:(?P<flavor>.*)$", self.firmware_flavor_matched, True),
            RegexDefinition("layer_height", "^;Layer\sheight:\s(?P<height>.*)$", self.layer_height_matched, True),
        ]

    @staticmethod
    def get_settings_dictionary():
        return {
            # Octolapse Settings
            'max_feedrate_z_override': SettingsDefinition('max_feedrate_z_override', CuraParsingFunctions.parse_float,['octolapse_setting']),
            'retraction_amount': SettingsDefinition('retraction_amount', CuraParsingFunctions.parse_float, ['octolapse_setting']),
            'retraction_hop': SettingsDefinition('retraction_hop', CuraParsingFunctions.parse_int,['octolapse_setting']),
            'retraction_hop_enabled': SettingsDefinition('retraction_hop_enabled', CuraParsingFunctions.parse_bool,['octolapse_setting']),
            'retraction_prime_speed': SettingsDefinition('retraction_prime_speed', CuraParsingFunctions.parse_int,['octolapse_setting']),
            'retraction_retract_speed': SettingsDefinition('retraction_retract_speed', CuraParsingFunctions.parse_int,['octolapse_setting']),
            'retraction_speed': SettingsDefinition('retraction_speed', CuraParsingFunctions.parse_int,['octolapse_setting']),
            'skirt_brim_speed': SettingsDefinition('skirt_brim_speed', CuraParsingFunctions.parse_float,['octolapse_setting']),
            'speed_infill': SettingsDefinition('speed_infill', CuraParsingFunctions.parse_int, ['octolapse_setting']),
            # Note that the below speed doesn't represent the initial layer or travel speed.  See speed_print_layer_0
            # however, a test will need to be performed.
            'speed_layer_0': SettingsDefinition('speed_layer_0', CuraParsingFunctions.parse_float,['octolapse_setting']),
            'speed_print': SettingsDefinition('speed_print', CuraParsingFunctions.parse_int, ['octolapse_setting']),
            'speed_slowdown_layers': SettingsDefinition('speed_slowdown_layers', CuraParsingFunctions.parse_int,['octolapse_setting']),
            'speed_topbottom': SettingsDefinition('speed_topbottom', CuraParsingFunctions.parse_float,['octolapse_setting']),
            'speed_travel': SettingsDefinition('speed_travel', CuraParsingFunctions.parse_int, ['octolapse_setting']),
            'speed_travel_layer_0': SettingsDefinition('speed_travel_layer_0', CuraParsingFunctions.parse_float,['octolapse_setting']),
            'speed_wall': SettingsDefinition('speed_wall', CuraParsingFunctions.parse_float, ['octolapse_setting']),
            'speed_wall_0': SettingsDefinition('speed_wall_0', CuraParsingFunctions.parse_float, ['octolapse_setting']),
            'speed_wall_x': SettingsDefinition('speed_wall_x', CuraParsingFunctions.parse_float, ['octolapse_setting']),
            'retraction_enable': SettingsDefinition('retraction_enable', CuraParsingFunctions.parse_bool, ['octolapse_setting']),
            'version': SettingsDefinition('version', CuraParsingFunctions.strip_string, ['octolapse_setting']),
            'speed_print_layer_0': SettingsDefinition('speed_print_layer_0', CuraParsingFunctions.parse_float,
                                                      ['octolapse_setting']),
            # End Octolapse Settings - The rest is included in case it is ever helpful for Octolapse or for other projects!
            'flavor': SettingsDefinition('flavor', CuraParsingFunctions.strip_string, ['misc']),
            'layer_height': SettingsDefinition('layer_height', CuraParsingFunctions.parse_float, ['misc']),
            'filament_used_meters': SettingsDefinition('layer_height', CuraParsingFunctions.parse_float, ['misc']),
            'acceleration_enabled': SettingsDefinition('acceleration_enabled', CuraParsingFunctions.parse_bool, ['misc']),
            'acceleration_infill': SettingsDefinition('acceleration_infill', CuraParsingFunctions.parse_int, ['misc']),
            'acceleration_ironing': SettingsDefinition('acceleration_ironing', CuraParsingFunctions.parse_int, ['misc']),
            'acceleration_layer_0': SettingsDefinition('acceleration_layer_0', CuraParsingFunctions.parse_int, ['misc']),
            'acceleration_prime_tower': SettingsDefinition('acceleration_prime_tower', CuraParsingFunctions.parse_int, ['misc']),
            'acceleration_print': SettingsDefinition('acceleration_print', CuraParsingFunctions.parse_int, ['misc']),
            'acceleration_print_layer_0': SettingsDefinition('acceleration_print_layer_0', CuraParsingFunctions.parse_int, ['misc']),
            'acceleration_roofing': SettingsDefinition('acceleration_roofing', CuraParsingFunctions.parse_int, ['misc']),
            'acceleration_skirt_brim': SettingsDefinition('acceleration_skirt_brim', CuraParsingFunctions.parse_int, ['misc']),
            'acceleration_support': SettingsDefinition('acceleration_support', CuraParsingFunctions.parse_int, ['misc']),
            'acceleration_support_bottom': SettingsDefinition('acceleration_support_bottom', CuraParsingFunctions.parse_int, ['misc']),
            'acceleration_support_infill': SettingsDefinition('acceleration_support_infill', CuraParsingFunctions.parse_int, ['misc']),
            'acceleration_support_interface': SettingsDefinition('acceleration_support_interface', CuraParsingFunctions.parse_int, ['misc']),
            'acceleration_support_roof': SettingsDefinition('acceleration_support_roof', CuraParsingFunctions.parse_int, ['misc']),
            'acceleration_topbottom': SettingsDefinition('acceleration_topbottom', CuraParsingFunctions.parse_int, ['misc']),
            'acceleration_travel': SettingsDefinition('acceleration_travel', CuraParsingFunctions.parse_int, ['misc']),
            'acceleration_travel_layer_0': SettingsDefinition('acceleration_travel_layer_0', CuraParsingFunctions.parse_float, ['misc']),
            'acceleration_wall': SettingsDefinition('acceleration_wall', CuraParsingFunctions.parse_int, ['misc']),
            'acceleration_wall_0': SettingsDefinition('acceleration_wall_0', CuraParsingFunctions.parse_int, ['misc']),
            'acceleration_wall_x': SettingsDefinition('acceleration_wall_x', CuraParsingFunctions.parse_int, ['misc']),
            'adaptive_layer_height_enabled': SettingsDefinition('adaptive_layer_height_enabled', CuraParsingFunctions.parse_bool, ['misc']),
            'adaptive_layer_height_threshold': SettingsDefinition('adaptive_layer_height_threshold', CuraParsingFunctions.parse_float, ['misc']),
            'adaptive_layer_height_variation': SettingsDefinition('adaptive_layer_height_variation', CuraParsingFunctions.parse_float, ['misc']),
            'adaptive_layer_height_variation_step': SettingsDefinition('adaptive_layer_height_variation_step', CuraParsingFunctions.parse_float, ['misc']),
            'adhesion_extruder_nr': SettingsDefinition('adhesion_extruder_nr', CuraParsingFunctions.parse_int, ['misc']),
            'adhesion_type': SettingsDefinition('adhesion_type', CuraParsingFunctions.strip_string, ['misc']),
            'alternate_carve_order': SettingsDefinition('alternate_carve_order', CuraParsingFunctions.parse_bool, ['misc']),
            'alternate_extra_perimeter': SettingsDefinition('alternate_extra_perimeter', CuraParsingFunctions.parse_bool, ['misc']),
            'anti_overhang_mesh': SettingsDefinition('anti_overhang_mesh', CuraParsingFunctions.parse_bool, ['misc']),
            'bottom_layers': SettingsDefinition('bottom_layers', CuraParsingFunctions.parse_int, ['misc']),
            'bottom_skin_expand_distance': SettingsDefinition('bottom_skin_expand_distance', CuraParsingFunctions.parse_float, ['misc']),
            'bottom_skin_preshrink': SettingsDefinition('bottom_skin_preshrink', CuraParsingFunctions.parse_float, ['misc']),
            'bottom_thickness': SettingsDefinition('bottom_thickness', CuraParsingFunctions.parse_float, ['misc']),
            'bridge_enable_more_layers': SettingsDefinition('bridge_enable_more_layers', CuraParsingFunctions.parse_bool, ['misc']),
            'bridge_fan_speed': SettingsDefinition('bridge_fan_speed', CuraParsingFunctions.parse_int, ['misc']),
            'bridge_fan_speed_2': SettingsDefinition('bridge_fan_speed_2', CuraParsingFunctions.parse_int, ['misc']),
            'bridge_fan_speed_3': SettingsDefinition('bridge_fan_speed_3', CuraParsingFunctions.parse_int, ['misc']),
            'bridge_settings_enabled': SettingsDefinition('bridge_settings_enabled', CuraParsingFunctions.parse_bool, ['misc']),
            'bridge_skin_density': SettingsDefinition('bridge_skin_density', CuraParsingFunctions.parse_int, ['misc']),
            'bridge_skin_density_2': SettingsDefinition('bridge_skin_density_2', CuraParsingFunctions.parse_int, ['misc']),
            'bridge_skin_density_3': SettingsDefinition('bridge_skin_density_3', CuraParsingFunctions.parse_int, ['misc']),
            'bridge_skin_material_flow': SettingsDefinition('bridge_skin_material_flow', CuraParsingFunctions.parse_int, ['misc']),
            'bridge_skin_material_flow_2': SettingsDefinition('bridge_skin_material_flow_2', CuraParsingFunctions.parse_int, ['misc']),
            'bridge_skin_material_flow_3': SettingsDefinition('bridge_skin_material_flow_3', CuraParsingFunctions.parse_int, ['misc']),
            'bridge_skin_speed': SettingsDefinition('bridge_skin_speed', CuraParsingFunctions.parse_float, ['misc']),
            'bridge_skin_speed_2': SettingsDefinition('bridge_skin_speed_2', CuraParsingFunctions.parse_float, ['misc']),
            'bridge_skin_speed_3': SettingsDefinition('bridge_skin_speed_3', CuraParsingFunctions.parse_float, ['misc']),
            'bridge_skin_support_threshold': SettingsDefinition('bridge_skin_support_threshold', CuraParsingFunctions.parse_int, ['misc']),
            'bridge_wall_coast': SettingsDefinition('bridge_wall_coast', CuraParsingFunctions.parse_int, ['misc']),
            'bridge_wall_material_flow': SettingsDefinition('bridge_wall_material_flow', CuraParsingFunctions.parse_int, ['misc']),
            'bridge_wall_min_length': SettingsDefinition('bridge_wall_min_length', CuraParsingFunctions.parse_int, ['misc']),
            'bridge_wall_speed': SettingsDefinition('bridge_wall_speed', CuraParsingFunctions.parse_float, ['misc']),
            'brim_line_count': SettingsDefinition('brim_line_count', CuraParsingFunctions.parse_int, ['misc']),
            'brim_outside_only': SettingsDefinition('brim_outside_only', CuraParsingFunctions.parse_bool, ['misc']),
            'brim_replaces_support': SettingsDefinition('brim_replaces_support', CuraParsingFunctions.parse_bool, ['misc']),
            'brim_width': SettingsDefinition('brim_width', CuraParsingFunctions.parse_float, ['misc']),
            'carve_multiple_volumes': SettingsDefinition('carve_multiple_volumes', CuraParsingFunctions.parse_bool, ['misc']),
            'center_object': SettingsDefinition('center_object', CuraParsingFunctions.parse_bool, ['misc']),
            'coasting_enable': SettingsDefinition('coasting_enable', CuraParsingFunctions.parse_bool, ['misc']),
            'coasting_min_volume': SettingsDefinition('coasting_min_volume', CuraParsingFunctions.parse_float, ['misc']),
            'coasting_speed': SettingsDefinition('coasting_speed', CuraParsingFunctions.parse_int, ['misc']),
            'coasting_volume': SettingsDefinition('coasting_volume', CuraParsingFunctions.parse_float, ['misc']),
            'conical_overhang_angle': SettingsDefinition('conical_overhang_angle', CuraParsingFunctions.parse_int, ['misc']),
            'conical_overhang_enabled': SettingsDefinition('conical_overhang_enabled', CuraParsingFunctions.parse_bool, ['misc']),
            'connect_infill_polygons': SettingsDefinition('connect_infill_polygons', CuraParsingFunctions.parse_bool, ['misc']),
            'connect_skin_polygons': SettingsDefinition('connect_skin_polygons', CuraParsingFunctions.parse_bool, ['misc']),
            'cool_fan_enabled': SettingsDefinition('cool_fan_enabled', CuraParsingFunctions.parse_bool, ['misc']),
            'cool_fan_full_at_height': SettingsDefinition('cool_fan_full_at_height', CuraParsingFunctions.parse_float, ['misc']),
            'cool_fan_full_layer': SettingsDefinition('cool_fan_full_layer', CuraParsingFunctions.parse_int, ['misc']),
            'cool_fan_speed': SettingsDefinition('cool_fan_speed', CuraParsingFunctions.parse_float, ['misc']),
            'cool_fan_speed_0': SettingsDefinition('cool_fan_speed_0', CuraParsingFunctions.parse_int, ['misc']),
            'cool_fan_speed_max': SettingsDefinition('cool_fan_speed_max', CuraParsingFunctions.parse_float, ['misc']),
            'cool_fan_speed_min': SettingsDefinition('cool_fan_speed_min', CuraParsingFunctions.parse_float, ['misc']),
            'cool_lift_head': SettingsDefinition('cool_lift_head', CuraParsingFunctions.parse_bool, ['misc']),
            'cool_min_layer_time': SettingsDefinition('cool_min_layer_time', CuraParsingFunctions.parse_int, ['misc']),
            'cool_min_layer_time_fan_speed_max': SettingsDefinition('cool_min_layer_time_fan_speed_max', CuraParsingFunctions.parse_int, ['misc']),
            'cool_min_speed': SettingsDefinition('cool_min_speed', CuraParsingFunctions.parse_int, ['misc']),
            'cross_infill_pocket_size': SettingsDefinition('cross_infill_pocket_size', CuraParsingFunctions.parse_float, ['misc']),
            'cutting_mesh': SettingsDefinition('cutting_mesh', CuraParsingFunctions.parse_bool, ['misc']),
            'default_material_bed_temperature': SettingsDefinition('default_material_bed_temperature', CuraParsingFunctions.parse_int, ['misc']),
            'default_material_print_temperature': SettingsDefinition('default_material_print_temperature', CuraParsingFunctions.parse_int, ['misc']),
            'draft_shield_dist': SettingsDefinition('draft_shield_dist', CuraParsingFunctions.parse_int, ['misc']),
            'draft_shield_enabled': SettingsDefinition('draft_shield_enabled', CuraParsingFunctions.parse_bool, ['misc']),
            'draft_shield_height': SettingsDefinition('draft_shield_height', CuraParsingFunctions.parse_int, ['misc']),
            'draft_shield_height_limitation': SettingsDefinition('draft_shield_height_limitation', CuraParsingFunctions.strip_string, ['misc']),
            'expand_skins_expand_distance': SettingsDefinition('expand_skins_expand_distance', CuraParsingFunctions.parse_float, ['misc']),
            'extruder_prime_pos_abs': SettingsDefinition('extruder_prime_pos_abs', CuraParsingFunctions.parse_bool, ['misc']),
            'extruder_prime_pos_x': SettingsDefinition('extruder_prime_pos_x', CuraParsingFunctions.parse_int, ['misc']),
            'extruder_prime_pos_y': SettingsDefinition('extruder_prime_pos_y', CuraParsingFunctions.parse_int, ['misc']),
            'extruder_prime_pos_z': SettingsDefinition('extruder_prime_pos_z', CuraParsingFunctions.parse_int, ['misc']),
            'extruders_enabled_count': SettingsDefinition('extruders_enabled_count', CuraParsingFunctions.parse_int, ['misc']),
            'fill_outline_gaps': SettingsDefinition('fill_outline_gaps', CuraParsingFunctions.parse_bool, ['misc']),
            'fill_perimeter_gaps': SettingsDefinition('fill_perimeter_gaps', CuraParsingFunctions.strip_string, ['misc']),
            'filter_out_tiny_gaps': SettingsDefinition('filter_out_tiny_gaps', CuraParsingFunctions.parse_bool, ['misc']),
            'flow_rate_extrusion_offset_factor': SettingsDefinition('flow_rate_extrusion_offset_factor', CuraParsingFunctions.parse_int, ['misc']),
            'flow_rate_max_extrusion_offset': SettingsDefinition('flow_rate_max_extrusion_offset', CuraParsingFunctions.parse_int, ['misc']),
            'gantry_height': SettingsDefinition('gantry_height', CuraParsingFunctions.parse_int, ['misc']),
            'gradual_infill_step_height': SettingsDefinition('gradual_infill_step_height', CuraParsingFunctions.parse_float, ['misc']),
            'gradual_infill_steps': SettingsDefinition('gradual_infill_steps', CuraParsingFunctions.parse_int, ['misc']),
            'gradual_support_infill_step_height': SettingsDefinition('gradual_support_infill_step_height', CuraParsingFunctions.parse_int, ['misc']),
            'gradual_support_infill_steps': SettingsDefinition('gradual_support_infill_steps', CuraParsingFunctions.parse_int, ['misc']),
            'infill_before_walls': SettingsDefinition('infill_before_walls', CuraParsingFunctions.parse_bool, ['misc']),
            'infill_enable_travel_optimization': SettingsDefinition('infill_enable_travel_optimization', CuraParsingFunctions.parse_bool, ['misc']),
            'infill_extruder_nr': SettingsDefinition('infill_extruder_nr', CuraParsingFunctions.parse_int, ['misc']),
            'infill_line_distance': SettingsDefinition('infill_line_distance', CuraParsingFunctions.parse_float, ['misc']),
            'infill_line_width': SettingsDefinition('infill_line_width', CuraParsingFunctions.parse_float, ['misc']),
            'infill_mesh': SettingsDefinition('infill_mesh', CuraParsingFunctions.parse_bool, ['misc']),
            'infill_mesh_order': SettingsDefinition('infill_mesh_order', CuraParsingFunctions.parse_int, ['misc']),
            'infill_multiplier': SettingsDefinition('infill_multiplier', CuraParsingFunctions.parse_int, ['misc']),
            'infill_offset_x': SettingsDefinition('infill_offset_x', CuraParsingFunctions.parse_int, ['misc']),
            'infill_offset_y': SettingsDefinition('infill_offset_y', CuraParsingFunctions.parse_int, ['misc']),
            'infill_overlap': SettingsDefinition('infill_overlap', CuraParsingFunctions.parse_int, ['misc']),
            'infill_overlap_mm': SettingsDefinition('infill_overlap_mm', CuraParsingFunctions.parse_float, ['misc']),
            'infill_pattern': SettingsDefinition('infill_pattern', CuraParsingFunctions.strip_string, ['misc']),
            'infill_sparse_density': SettingsDefinition('infill_sparse_density', CuraParsingFunctions.parse_int, ['misc']),
            'infill_sparse_thickness': SettingsDefinition('infill_sparse_thickness', CuraParsingFunctions.parse_float, ['misc']),
            'infill_support_angle': SettingsDefinition('infill_support_angle', CuraParsingFunctions.parse_int, ['misc']),
            'infill_support_enabled': SettingsDefinition('infill_support_enabled', CuraParsingFunctions.parse_bool, ['misc']),
            'infill_wall_line_count': SettingsDefinition('infill_wall_line_count', CuraParsingFunctions.parse_int, ['misc']),
            'infill_wipe_dist': SettingsDefinition('infill_wipe_dist', CuraParsingFunctions.parse_float, ['misc']),
            'initial_layer_line_width_factor': SettingsDefinition('initial_layer_line_width_factor', CuraParsingFunctions.parse_float, ['misc']),
            'ironing_enabled': SettingsDefinition('ironing_enabled', CuraParsingFunctions.parse_bool, ['misc']),
            'ironing_flow': SettingsDefinition('ironing_flow', CuraParsingFunctions.parse_float, ['misc']),
            'ironing_inset': SettingsDefinition('ironing_inset', CuraParsingFunctions.parse_float, ['misc']),
            'ironing_line_spacing': SettingsDefinition('ironing_line_spacing', CuraParsingFunctions.parse_float, ['misc']),
            'ironing_only_highest_layer': SettingsDefinition('ironing_only_highest_layer', CuraParsingFunctions.parse_bool, ['misc']),
            'ironing_pattern': SettingsDefinition('ironing_pattern', CuraParsingFunctions.strip_string, ['misc']),
            'jerk_enabled': SettingsDefinition('jerk_enabled', CuraParsingFunctions.parse_bool, ['misc']),
            'jerk_infill': SettingsDefinition('jerk_infill', CuraParsingFunctions.parse_int, ['misc']),
            'jerk_ironing': SettingsDefinition('jerk_ironing', CuraParsingFunctions.parse_int, ['misc']),
            'jerk_layer_0': SettingsDefinition('jerk_layer_0', CuraParsingFunctions.parse_int, ['misc']),
            'jerk_prime_tower': SettingsDefinition('jerk_prime_tower', CuraParsingFunctions.parse_int, ['misc']),
            'jerk_print': SettingsDefinition('jerk_print', CuraParsingFunctions.parse_int, ['misc']),
            'jerk_print_layer_0': SettingsDefinition('jerk_print_layer_0', CuraParsingFunctions.parse_int, ['misc']),
            'jerk_roofing': SettingsDefinition('jerk_roofing', CuraParsingFunctions.parse_int, ['misc']),
            'jerk_skirt_brim': SettingsDefinition('jerk_skirt_brim', CuraParsingFunctions.parse_int, ['misc']),
            'jerk_support': SettingsDefinition('jerk_support', CuraParsingFunctions.parse_int, ['misc']),
            'jerk_support_bottom': SettingsDefinition('jerk_support_bottom', CuraParsingFunctions.parse_int, ['misc']),
            'jerk_support_infill': SettingsDefinition('jerk_support_infill', CuraParsingFunctions.parse_int, ['misc']),
            'jerk_support_interface': SettingsDefinition('jerk_support_interface', CuraParsingFunctions.parse_int, ['misc']),
            'jerk_support_roof': SettingsDefinition('jerk_support_roof', CuraParsingFunctions.parse_int, ['misc']),
            'jerk_topbottom': SettingsDefinition('jerk_topbottom', CuraParsingFunctions.parse_int, ['misc']),
            'jerk_travel': SettingsDefinition('jerk_travel', CuraParsingFunctions.parse_int, ['misc']),
            'jerk_travel_layer_0': SettingsDefinition('jerk_travel_layer_0', CuraParsingFunctions.parse_float, ['misc']),
            'jerk_wall': SettingsDefinition('jerk_wall', CuraParsingFunctions.parse_int, ['misc']),
            'jerk_wall_0': SettingsDefinition('jerk_wall_0', CuraParsingFunctions.parse_int, ['misc']),
            'jerk_wall_x': SettingsDefinition('jerk_wall_x', CuraParsingFunctions.parse_int, ['misc']),
            'layer_0_z_overlap': SettingsDefinition('layer_0_z_overlap', CuraParsingFunctions.parse_float, ['misc']),
            'layer_height_0': SettingsDefinition('layer_height_0', CuraParsingFunctions.parse_float, ['misc']),
            'layer_start_x': SettingsDefinition('layer_start_x', CuraParsingFunctions.parse_float, ['misc']),
            'layer_start_y': SettingsDefinition('layer_start_y', CuraParsingFunctions.parse_float, ['misc']),
            'limit_support_retractions': SettingsDefinition('limit_support_retractions', CuraParsingFunctions.parse_bool, ['misc']),
            'line_width': SettingsDefinition('line_width', CuraParsingFunctions.parse_float, ['misc']),
            'machine_acceleration': SettingsDefinition('machine_acceleration', CuraParsingFunctions.parse_int, ['misc']),
            'machine_buildplate_type': SettingsDefinition('machine_buildplate_type', CuraParsingFunctions.strip_string, ['misc']),
            'machine_center_is_zero': SettingsDefinition('machine_center_is_zero', CuraParsingFunctions.parse_bool, ['misc']),
            'machine_depth': SettingsDefinition('machine_depth', CuraParsingFunctions.parse_int, ['misc']),
            'machine_endstop_positive_direction_x': SettingsDefinition('machine_endstop_positive_direction_x', CuraParsingFunctions.parse_bool, ['misc']),
            'machine_endstop_positive_direction_y': SettingsDefinition('machine_endstop_positive_direction_y', CuraParsingFunctions.parse_bool, ['misc']),
            'machine_endstop_positive_direction_z': SettingsDefinition('machine_endstop_positive_direction_z', CuraParsingFunctions.parse_bool, ['misc']),
            'machine_extruder_count': SettingsDefinition('machine_extruder_count', CuraParsingFunctions.parse_int, ['misc']),
            'machine_feeder_wheel_diameter': SettingsDefinition('machine_feeder_wheel_diameter', CuraParsingFunctions.parse_float, ['misc']),
            'machine_filament_park_distance': SettingsDefinition('machine_filament_park_distance', CuraParsingFunctions.parse_int, ['misc']),
            'machine_firmware_retract': SettingsDefinition('machine_firmware_retract', CuraParsingFunctions.parse_bool, ['misc']),
            'machine_gcode_flavor': SettingsDefinition('machine_gcode_flavor', CuraParsingFunctions.strip_string, ['misc']),
            'machine_heat_zone_length': SettingsDefinition('machine_heat_zone_length', CuraParsingFunctions.parse_int, ['misc']),
            'machine_heated_bed': SettingsDefinition('machine_heated_bed', CuraParsingFunctions.parse_bool, ['misc']),
            'machine_height': SettingsDefinition('machine_height', CuraParsingFunctions.parse_int, ['misc']),
            'machine_max_acceleration_e': SettingsDefinition('machine_max_acceleration_e', CuraParsingFunctions.parse_int, ['misc']),
            'machine_max_acceleration_x': SettingsDefinition('machine_max_acceleration_x', CuraParsingFunctions.parse_int, ['misc']),
            'machine_max_acceleration_y': SettingsDefinition('machine_max_acceleration_y', CuraParsingFunctions.parse_int, ['misc']),
            'machine_max_acceleration_z': SettingsDefinition('machine_max_acceleration_z', CuraParsingFunctions.parse_int, ['misc']),
            'machine_max_feedrate_e': SettingsDefinition('machine_max_feedrate_e', CuraParsingFunctions.parse_int, ['misc']),
            'machine_max_feedrate_x': SettingsDefinition('machine_max_feedrate_x', CuraParsingFunctions.parse_int, ['misc']),
            'machine_max_feedrate_y': SettingsDefinition('machine_max_feedrate_y', CuraParsingFunctions.parse_int, ['misc']),
            'machine_max_feedrate_z': SettingsDefinition('machine_max_feedrate_z', CuraParsingFunctions.parse_int, ['misc']),
            'machine_max_jerk_e': SettingsDefinition('machine_max_jerk_e', CuraParsingFunctions.parse_float, ['misc']),
            'machine_max_jerk_xy': SettingsDefinition('machine_max_jerk_xy', CuraParsingFunctions.parse_int, ['misc']),
            'machine_max_jerk_z': SettingsDefinition('machine_max_jerk_z', CuraParsingFunctions.parse_float, ['misc']),
            'machine_min_cool_heat_time_window': SettingsDefinition('machine_min_cool_heat_time_window', CuraParsingFunctions.parse_float, ['misc']),
            'machine_minimum_feedrate': SettingsDefinition('machine_minimum_feedrate', CuraParsingFunctions.parse_float, ['misc']),
            'machine_name': SettingsDefinition('machine_name', CuraParsingFunctions.strip_string, ['misc']),
            'machine_nozzle_cool_down_speed': SettingsDefinition('machine_nozzle_cool_down_speed', CuraParsingFunctions.parse_float, ['misc']),
            'machine_nozzle_expansion_angle': SettingsDefinition('machine_nozzle_expansion_angle', CuraParsingFunctions.parse_int, ['misc']),
            'machine_nozzle_head_distance': SettingsDefinition('machine_nozzle_head_distance', CuraParsingFunctions.parse_int, ['misc']),
            'machine_nozzle_heat_up_speed': SettingsDefinition('machine_nozzle_heat_up_speed', CuraParsingFunctions.parse_float, ['misc']),
            'machine_nozzle_id': SettingsDefinition('machine_nozzle_id', CuraParsingFunctions.strip_string, ['misc']),
            'machine_nozzle_size': SettingsDefinition('machine_nozzle_size', CuraParsingFunctions.parse_float, ['misc']),
            'machine_nozzle_temp_enabled': SettingsDefinition('machine_nozzle_temp_enabled', CuraParsingFunctions.parse_bool, ['misc']),
            'machine_nozzle_tip_outer_diameter': SettingsDefinition('machine_nozzle_tip_outer_diameter', CuraParsingFunctions.parse_int, ['misc']),
            'machine_shape': SettingsDefinition('machine_shape', CuraParsingFunctions.strip_string, ['misc']),
            'machine_show_variants': SettingsDefinition('machine_show_variants', CuraParsingFunctions.parse_bool, ['misc']),
            'machine_steps_per_mm_e': SettingsDefinition('machine_steps_per_mm_e', CuraParsingFunctions.parse_int, ['misc']),
            'machine_steps_per_mm_x': SettingsDefinition('machine_steps_per_mm_x', CuraParsingFunctions.parse_int, ['misc']),
            'machine_steps_per_mm_y': SettingsDefinition('machine_steps_per_mm_y', CuraParsingFunctions.parse_int, ['misc']),
            'machine_steps_per_mm_z': SettingsDefinition('machine_steps_per_mm_z', CuraParsingFunctions.parse_int, ['misc']),
            'machine_use_extruder_offset_to_offset_coords': SettingsDefinition('machine_use_extruder_offset_to_offset_coords', CuraParsingFunctions.parse_bool, ['misc']),
            'machine_width': SettingsDefinition('machine_width', CuraParsingFunctions.parse_int, ['misc']),
            'magic_fuzzy_skin_enabled': SettingsDefinition('magic_fuzzy_skin_enabled', CuraParsingFunctions.parse_bool, ['misc']),
            'magic_fuzzy_skin_point_density': SettingsDefinition('magic_fuzzy_skin_point_density', CuraParsingFunctions.parse_float, ['misc']),
            'magic_fuzzy_skin_point_dist': SettingsDefinition('magic_fuzzy_skin_point_dist', CuraParsingFunctions.parse_float, ['misc']),
            'magic_fuzzy_skin_thickness': SettingsDefinition('magic_fuzzy_skin_thickness', CuraParsingFunctions.parse_float, ['misc']),
            'magic_mesh_surface_mode': SettingsDefinition('magic_mesh_surface_mode', CuraParsingFunctions.strip_string, ['misc']),
            'magic_spiralize': SettingsDefinition('magic_spiralize', CuraParsingFunctions.parse_bool, ['misc']),
            'material_adhesion_tendency': SettingsDefinition('material_adhesion_tendency', CuraParsingFunctions.parse_int, ['misc']),
            'material_bed_temp_prepend': SettingsDefinition('material_bed_temp_prepend', CuraParsingFunctions.parse_bool, ['misc']),
            'material_bed_temp_wait': SettingsDefinition('material_bed_temp_wait', CuraParsingFunctions.parse_bool, ['misc']),
            'material_bed_temperature': SettingsDefinition('material_bed_temperature', CuraParsingFunctions.parse_int, ['misc']),
            'material_bed_temperature_layer_0': SettingsDefinition('material_bed_temperature_layer_0', CuraParsingFunctions.parse_int, ['misc']),
            'material_diameter': SettingsDefinition('material_diameter', CuraParsingFunctions.parse_float, ['misc']),
            'material_extrusion_cool_down_speed': SettingsDefinition('material_extrusion_cool_down_speed', CuraParsingFunctions.parse_float, ['misc']),
            'material_final_print_temperature': SettingsDefinition('material_final_print_temperature', CuraParsingFunctions.parse_int, ['misc']),
            'material_flow': SettingsDefinition('material_flow', CuraParsingFunctions.parse_int, ['misc']),
            'material_flow_dependent_temperature': SettingsDefinition('material_flow_dependent_temperature', CuraParsingFunctions.parse_bool, ['misc']),
            'material_flow_layer_0': SettingsDefinition('material_flow_layer_0', CuraParsingFunctions.parse_int, ['misc']),
            'material_initial_print_temperature': SettingsDefinition('material_initial_print_temperature', CuraParsingFunctions.parse_int, ['misc']),
            'material_print_temp_prepend': SettingsDefinition('material_print_temp_prepend', CuraParsingFunctions.parse_bool, ['misc']),
            'material_print_temp_wait': SettingsDefinition('material_print_temp_wait', CuraParsingFunctions.parse_bool, ['misc']),
            'material_print_temperature': SettingsDefinition('material_print_temperature', CuraParsingFunctions.parse_int, ['misc']),
            'material_print_temperature_layer_0': SettingsDefinition('material_print_temperature_layer_0', CuraParsingFunctions.parse_int, ['misc']),
            'material_shrinkage_percentage': SettingsDefinition('material_shrinkage_percentage', CuraParsingFunctions.parse_int, ['misc']),
            'material_standby_temperature': SettingsDefinition('material_standby_temperature', CuraParsingFunctions.parse_int, ['misc']),
            'material_surface_energy': SettingsDefinition('material_surface_energy', CuraParsingFunctions.parse_int, ['misc']),
            'max_skin_angle_for_expansion': SettingsDefinition('max_skin_angle_for_expansion', CuraParsingFunctions.parse_int, ['misc']),
            'mesh_position_x': SettingsDefinition('mesh_position_x', CuraParsingFunctions.parse_int, ['misc']),
            'mesh_position_y': SettingsDefinition('mesh_position_y', CuraParsingFunctions.parse_int, ['misc']),
            'mesh_position_z': SettingsDefinition('mesh_position_z', CuraParsingFunctions.parse_int, ['misc']),
            'meshfix_extensive_stitching': SettingsDefinition('meshfix_extensive_stitching', CuraParsingFunctions.parse_bool, ['misc']),
            'meshfix_keep_open_polygons': SettingsDefinition('meshfix_keep_open_polygons', CuraParsingFunctions.parse_bool, ['misc']),
            'meshfix_maximum_resolution': SettingsDefinition('meshfix_maximum_resolution', CuraParsingFunctions.parse_float, ['misc']),
            'meshfix_maximum_travel_resolution': SettingsDefinition('meshfix_maximum_travel_resolution', CuraParsingFunctions.parse_float, ['misc']),
            'meshfix_union_all': SettingsDefinition('meshfix_union_all', CuraParsingFunctions.parse_bool, ['misc']),
            'meshfix_union_all_remove_holes': SettingsDefinition('meshfix_union_all_remove_holes', CuraParsingFunctions.parse_bool, ['misc']),
            'min_infill_area': SettingsDefinition('min_infill_area', CuraParsingFunctions.parse_int, ['misc']),
            'min_skin_width_for_expansion': SettingsDefinition('min_skin_width_for_expansion', CuraParsingFunctions.parse_float, ['misc']),
            'minimum_polygon_circumference': SettingsDefinition('minimum_polygon_circumference', CuraParsingFunctions.parse_float, ['misc']),
            'mold_angle': SettingsDefinition('mold_angle', CuraParsingFunctions.parse_int, ['misc']),
            'mold_enabled': SettingsDefinition('mold_enabled', CuraParsingFunctions.parse_bool, ['misc']),
            'mold_roof_height': SettingsDefinition('mold_roof_height', CuraParsingFunctions.parse_float, ['misc']),
            'mold_width': SettingsDefinition('mold_width', CuraParsingFunctions.parse_int, ['misc']),
            'multiple_mesh_overlap': SettingsDefinition('multiple_mesh_overlap', CuraParsingFunctions.parse_float, ['misc']),
            'ooze_shield_angle': SettingsDefinition('ooze_shield_angle', CuraParsingFunctions.parse_int, ['misc']),
            'ooze_shield_dist': SettingsDefinition('ooze_shield_dist', CuraParsingFunctions.parse_int, ['misc']),
            'ooze_shield_enabled': SettingsDefinition('ooze_shield_enabled', CuraParsingFunctions.parse_bool, ['misc']),
            'optimize_wall_printing_order': SettingsDefinition('optimize_wall_printing_order', CuraParsingFunctions.parse_bool, ['misc']),
            'outer_inset_first': SettingsDefinition('outer_inset_first', CuraParsingFunctions.parse_bool, ['misc']),
            'prime_blob_enable': SettingsDefinition('prime_blob_enable', CuraParsingFunctions.parse_bool, ['misc']),
            'prime_tower_circular': SettingsDefinition('prime_tower_circular', CuraParsingFunctions.parse_bool, ['misc']),
            'prime_tower_enable': SettingsDefinition('prime_tower_enable', CuraParsingFunctions.parse_bool, ['misc']),
            'prime_tower_flow': SettingsDefinition('prime_tower_flow', CuraParsingFunctions.parse_int, ['misc']),
            'prime_tower_line_width': SettingsDefinition('prime_tower_line_width', CuraParsingFunctions.parse_float, ['misc']),
            'prime_tower_min_volume': SettingsDefinition('prime_tower_min_volume', CuraParsingFunctions.parse_int, ['misc']),
            'prime_tower_position_x': SettingsDefinition('prime_tower_position_x', CuraParsingFunctions.parse_float, ['misc']),
            'prime_tower_position_y': SettingsDefinition('prime_tower_position_y', CuraParsingFunctions.parse_float, ['misc']),
            'prime_tower_size': SettingsDefinition('prime_tower_size', CuraParsingFunctions.parse_int, ['misc']),
            'prime_tower_wipe_enabled': SettingsDefinition('prime_tower_wipe_enabled', CuraParsingFunctions.parse_bool, ['misc']),
            'print_sequence': SettingsDefinition('print_sequence', CuraParsingFunctions.strip_string, ['misc']),
            'raft_acceleration': SettingsDefinition('raft_acceleration', CuraParsingFunctions.parse_int, ['misc']),
            'raft_airgap': SettingsDefinition('raft_airgap', CuraParsingFunctions.parse_float, ['misc']),
            'raft_base_acceleration': SettingsDefinition('raft_base_acceleration', CuraParsingFunctions.parse_int, ['misc']),
            'raft_base_fan_speed': SettingsDefinition('raft_base_fan_speed', CuraParsingFunctions.parse_int, ['misc']),
            'raft_base_jerk': SettingsDefinition('raft_base_jerk', CuraParsingFunctions.parse_int, ['misc']),
            'raft_base_line_spacing': SettingsDefinition('raft_base_line_spacing', CuraParsingFunctions.parse_float, ['misc']),
            'raft_base_line_width': SettingsDefinition('raft_base_line_width', CuraParsingFunctions.parse_float, ['misc']),
            'raft_base_speed': SettingsDefinition('raft_base_speed', CuraParsingFunctions.parse_float, ['misc']),
            'raft_base_thickness': SettingsDefinition('raft_base_thickness', CuraParsingFunctions.parse_float, ['misc']),
            'raft_fan_speed': SettingsDefinition('raft_fan_speed', CuraParsingFunctions.parse_int, ['misc']),
            'raft_interface_acceleration': SettingsDefinition('raft_interface_acceleration', CuraParsingFunctions.parse_int, ['misc']),
            'raft_interface_fan_speed': SettingsDefinition('raft_interface_fan_speed', CuraParsingFunctions.parse_int, ['misc']),
            'raft_interface_jerk': SettingsDefinition('raft_interface_jerk', CuraParsingFunctions.parse_int, ['misc']),
            'raft_interface_line_spacing': SettingsDefinition('raft_interface_line_spacing', CuraParsingFunctions.parse_float, ['misc']),
            'raft_interface_line_width': SettingsDefinition('raft_interface_line_width', CuraParsingFunctions.parse_float, ['misc']),
            'raft_interface_speed': SettingsDefinition('raft_interface_speed', CuraParsingFunctions.parse_float, ['misc']),
            'raft_interface_thickness': SettingsDefinition('raft_interface_thickness', CuraParsingFunctions.parse_float, ['misc']),
            'raft_jerk': SettingsDefinition('raft_jerk', CuraParsingFunctions.parse_int, ['misc']),
            'raft_margin': SettingsDefinition('raft_margin', CuraParsingFunctions.parse_int, ['misc']),
            'raft_smoothing': SettingsDefinition('raft_smoothing', CuraParsingFunctions.parse_int, ['misc']),
            'raft_speed': SettingsDefinition('raft_speed', CuraParsingFunctions.parse_float, ['misc']),
            'raft_surface_acceleration': SettingsDefinition('raft_surface_acceleration', CuraParsingFunctions.parse_int, ['misc']),
            'raft_surface_fan_speed': SettingsDefinition('raft_surface_fan_speed', CuraParsingFunctions.parse_int, ['misc']),
            'raft_surface_jerk': SettingsDefinition('raft_surface_jerk', CuraParsingFunctions.parse_int, ['misc']),
            'raft_surface_layers': SettingsDefinition('raft_surface_layers', CuraParsingFunctions.parse_int, ['misc']),
            'raft_surface_line_spacing': SettingsDefinition('raft_surface_line_spacing', CuraParsingFunctions.parse_float, ['misc']),
            'raft_surface_line_width': SettingsDefinition('raft_surface_line_width', CuraParsingFunctions.parse_float, ['misc']),
            'raft_surface_speed': SettingsDefinition('raft_surface_speed', CuraParsingFunctions.parse_float, ['misc']),
            'raft_surface_thickness': SettingsDefinition('raft_surface_thickness', CuraParsingFunctions.parse_float, ['misc']),
            'relative_extrusion': SettingsDefinition('relative_extrusion', CuraParsingFunctions.parse_bool, ['misc']),
            'remove_empty_first_layers': SettingsDefinition('remove_empty_first_layers', CuraParsingFunctions.parse_bool, ['misc']),
            'retract_at_layer_change': SettingsDefinition('retract_at_layer_change', CuraParsingFunctions.parse_bool, ['misc']),
            'retraction_combing': SettingsDefinition('retraction_combing', CuraParsingFunctions.strip_string, ['misc']),
            'retraction_combing_max_distance': SettingsDefinition('retraction_combing_max_distance', CuraParsingFunctions.parse_int, ['misc']),
            'retraction_count_max': SettingsDefinition('retraction_count_max', CuraParsingFunctions.parse_int, ['misc']),
            'retraction_extra_prime_amount': SettingsDefinition('retraction_extra_prime_amount', CuraParsingFunctions.parse_int, ['misc']),
            'retraction_extrusion_window': SettingsDefinition('retraction_extrusion_window', CuraParsingFunctions.parse_float, ['misc']),
            'retraction_hop_after_extruder_switch': SettingsDefinition('retraction_hop_after_extruder_switch', CuraParsingFunctions.parse_bool, ['misc']),
            'retraction_hop_only_when_collides': SettingsDefinition('retraction_hop_only_when_collides', CuraParsingFunctions.parse_bool, ['misc']),
            'retraction_min_travel': SettingsDefinition('retraction_min_travel', CuraParsingFunctions.parse_float, ['misc']),
            'roofing_extruder_nr': SettingsDefinition('roofing_extruder_nr', CuraParsingFunctions.parse_int, ['misc']),
            'roofing_layer_count': SettingsDefinition('roofing_layer_count', CuraParsingFunctions.parse_int, ['misc']),
            'roofing_line_width': SettingsDefinition('roofing_line_width', CuraParsingFunctions.parse_float, ['misc']),
            'roofing_pattern': SettingsDefinition('roofing_pattern', CuraParsingFunctions.strip_string, ['misc']),
            'skin_alternate_rotation': SettingsDefinition('skin_alternate_rotation', CuraParsingFunctions.parse_bool, ['misc']),
            'skin_line_width': SettingsDefinition('skin_line_width', CuraParsingFunctions.parse_float, ['misc']),
            'skin_no_small_gaps_heuristic': SettingsDefinition('skin_no_small_gaps_heuristic', CuraParsingFunctions.parse_bool, ['misc']),
            'skin_outline_count': SettingsDefinition('skin_outline_count', CuraParsingFunctions.parse_int, ['misc']),
            'skin_overlap': SettingsDefinition('skin_overlap', CuraParsingFunctions.parse_int, ['misc']),
            'skin_overlap_mm': SettingsDefinition('skin_overlap_mm', CuraParsingFunctions.parse_float, ['misc']),
            'skin_preshrink': SettingsDefinition('skin_preshrink', CuraParsingFunctions.parse_float, ['misc']),
            'skirt_brim_line_width': SettingsDefinition('skirt_brim_line_width', CuraParsingFunctions.parse_float, ['misc']),
            'skirt_brim_minimal_length': SettingsDefinition('skirt_brim_minimal_length', CuraParsingFunctions.parse_int, ['misc']),
            'skirt_gap': SettingsDefinition('skirt_gap', CuraParsingFunctions.parse_int, ['misc']),
            'skirt_line_count': SettingsDefinition('skirt_line_count', CuraParsingFunctions.parse_int, ['misc']),
            'slicing_tolerance': SettingsDefinition('slicing_tolerance', CuraParsingFunctions.strip_string, ['misc']),
            'smooth_spiralized_contours': SettingsDefinition('smooth_spiralized_contours', CuraParsingFunctions.parse_bool, ['misc']),
            'spaghetti_flow': SettingsDefinition('spaghetti_flow', CuraParsingFunctions.parse_int, ['misc']),
            'spaghetti_infill_enabled': SettingsDefinition('spaghetti_infill_enabled', CuraParsingFunctions.parse_bool, ['misc']),
            'spaghetti_infill_extra_volume': SettingsDefinition('spaghetti_infill_extra_volume', CuraParsingFunctions.parse_int, ['misc']),
            'spaghetti_infill_stepped': SettingsDefinition('spaghetti_infill_stepped', CuraParsingFunctions.parse_bool, ['misc']),
            'spaghetti_inset': SettingsDefinition('spaghetti_inset', CuraParsingFunctions.parse_float, ['misc']),
            'spaghetti_max_height': SettingsDefinition('spaghetti_max_height', CuraParsingFunctions.parse_float, ['misc']),
            'spaghetti_max_infill_angle': SettingsDefinition('spaghetti_max_infill_angle', CuraParsingFunctions.parse_int, ['misc']),
            'speed_equalize_flow_enabled': SettingsDefinition('speed_equalize_flow_enabled', CuraParsingFunctions.parse_bool, ['misc']),
            'speed_equalize_flow_max': SettingsDefinition('speed_equalize_flow_max', CuraParsingFunctions.parse_int, ['misc']),
            'speed_ironing': SettingsDefinition('speed_ironing', CuraParsingFunctions.parse_float, ['misc']),
            'speed_prime_tower': SettingsDefinition('speed_prime_tower', CuraParsingFunctions.parse_int, ['misc']),
            'speed_roofing': SettingsDefinition('speed_roofing', CuraParsingFunctions.parse_float, ['misc']),
            'speed_support': SettingsDefinition('speed_support', CuraParsingFunctions.parse_int, ['misc']),
            'speed_support_bottom': SettingsDefinition('speed_support_bottom', CuraParsingFunctions.parse_float, ['misc']),
            'speed_support_infill': SettingsDefinition('speed_support_infill', CuraParsingFunctions.parse_int, ['misc']),
            'speed_support_interface': SettingsDefinition('speed_support_interface', CuraParsingFunctions.parse_float, ['misc']),
            'speed_support_roof': SettingsDefinition('speed_support_roof', CuraParsingFunctions.parse_float, ['misc']),
            'start_layers_at_same_position': SettingsDefinition('start_layers_at_same_position', CuraParsingFunctions.parse_bool, ['misc']),
            'sub_div_rad_add': SettingsDefinition('sub_div_rad_add', CuraParsingFunctions.parse_float, ['misc']),
            'support_angle': SettingsDefinition('support_angle', CuraParsingFunctions.parse_int, ['misc']),
            'support_bottom_density': SettingsDefinition('support_bottom_density', CuraParsingFunctions.parse_int, ['misc']),
            'support_bottom_distance': SettingsDefinition('support_bottom_distance', CuraParsingFunctions.parse_float, ['misc']),
            'support_bottom_enable': SettingsDefinition('support_bottom_enable', CuraParsingFunctions.parse_bool, ['misc']),
            'support_bottom_extruder_nr': SettingsDefinition('support_bottom_extruder_nr', CuraParsingFunctions.parse_int, ['misc']),
            'support_bottom_height': SettingsDefinition('support_bottom_height', CuraParsingFunctions.parse_int, ['misc']),
            'support_bottom_line_distance': SettingsDefinition('support_bottom_line_distance', CuraParsingFunctions.parse_float, ['misc']),
            'support_bottom_line_width': SettingsDefinition('support_bottom_line_width', CuraParsingFunctions.parse_float, ['misc']),
            'support_bottom_pattern': SettingsDefinition('support_bottom_pattern', CuraParsingFunctions.strip_string, ['misc']),
            'support_bottom_stair_step_height': SettingsDefinition('support_bottom_stair_step_height', CuraParsingFunctions.parse_float, ['misc']),
            'support_bottom_stair_step_width': SettingsDefinition('support_bottom_stair_step_width', CuraParsingFunctions.parse_float, ['misc']),
            'support_brim_enable': SettingsDefinition('support_brim_enable', CuraParsingFunctions.parse_bool, ['misc']),
            'support_brim_line_count': SettingsDefinition('support_brim_line_count', CuraParsingFunctions.parse_int, ['misc']),
            'support_brim_width': SettingsDefinition('support_brim_width', CuraParsingFunctions.parse_float, ['misc']),
            'support_conical_angle': SettingsDefinition('support_conical_angle', CuraParsingFunctions.parse_int, ['misc']),
            'support_conical_enabled': SettingsDefinition('support_conical_enabled', CuraParsingFunctions.parse_bool, ['misc']),
            'support_conical_min_width': SettingsDefinition('support_conical_min_width', CuraParsingFunctions.parse_float, ['misc']),
            'support_connect_zigzags': SettingsDefinition('support_connect_zigzags', CuraParsingFunctions.parse_bool, ['misc']),
            'support_enable': SettingsDefinition('support_enable', CuraParsingFunctions.parse_bool, ['misc']),
            'support_extruder_nr': SettingsDefinition('support_extruder_nr', CuraParsingFunctions.parse_int, ['misc']),
            'support_extruder_nr_layer_0': SettingsDefinition('support_extruder_nr_layer_0', CuraParsingFunctions.parse_int, ['misc']),
            'support_fan_enable': SettingsDefinition('support_fan_enable', CuraParsingFunctions.parse_bool, ['misc']),
            'support_infill_angle': SettingsDefinition('support_infill_angle', CuraParsingFunctions.parse_int, ['misc']),
            'support_infill_extruder_nr': SettingsDefinition('support_infill_extruder_nr', CuraParsingFunctions.parse_int, ['misc']),
            'support_infill_rate': SettingsDefinition('support_infill_rate', CuraParsingFunctions.parse_int, ['misc']),
            'support_infill_sparse_thickness': SettingsDefinition('support_infill_sparse_thickness', CuraParsingFunctions.parse_float, ['misc']),
            'support_initial_layer_line_distance': SettingsDefinition('support_initial_layer_line_distance', CuraParsingFunctions.parse_float, ['misc']),
            'support_interface_density': SettingsDefinition('support_interface_density', CuraParsingFunctions.parse_int, ['misc']),
            'support_interface_enable': SettingsDefinition('support_interface_enable', CuraParsingFunctions.parse_bool, ['misc']),
            'support_interface_extruder_nr': SettingsDefinition('support_interface_extruder_nr', CuraParsingFunctions.parse_int, ['misc']),
            'support_interface_height': SettingsDefinition('support_interface_height', CuraParsingFunctions.parse_int, ['misc']),
            'support_interface_line_width': SettingsDefinition('support_interface_line_width', CuraParsingFunctions.parse_float, ['misc']),
            'support_interface_pattern': SettingsDefinition('support_interface_pattern', CuraParsingFunctions.strip_string, ['misc']),
            'support_interface_skip_height': SettingsDefinition('support_interface_skip_height', CuraParsingFunctions.parse_float, ['misc']),
            'support_join_distance': SettingsDefinition('support_join_distance', CuraParsingFunctions.parse_float, ['misc']),
            'support_line_distance': SettingsDefinition('support_line_distance', CuraParsingFunctions.parse_float, ['misc']),
            'support_line_width': SettingsDefinition('support_line_width', CuraParsingFunctions.parse_float, ['misc']),
            'support_mesh': SettingsDefinition('support_mesh', CuraParsingFunctions.parse_bool, ['misc']),
            'support_mesh_drop_down': SettingsDefinition('support_mesh_drop_down', CuraParsingFunctions.parse_bool, ['misc']),
            'support_minimal_diameter': SettingsDefinition('support_minimal_diameter', CuraParsingFunctions.parse_float, ['misc']),
            'support_offset': SettingsDefinition('support_offset', CuraParsingFunctions.parse_float, ['misc']),
            'support_pattern': SettingsDefinition('support_pattern', CuraParsingFunctions.strip_string, ['misc']),
            'support_roof_density': SettingsDefinition('support_roof_density', CuraParsingFunctions.parse_int, ['misc']),
            'support_roof_enable': SettingsDefinition('support_roof_enable', CuraParsingFunctions.parse_bool, ['misc']),
            'support_roof_extruder_nr': SettingsDefinition('support_roof_extruder_nr', CuraParsingFunctions.parse_int, ['misc']),
            'support_roof_height': SettingsDefinition('support_roof_height', CuraParsingFunctions.parse_int, ['misc']),
            'support_roof_line_distance': SettingsDefinition('support_roof_line_distance', CuraParsingFunctions.parse_float, ['misc']),
            'support_roof_line_width': SettingsDefinition('support_roof_line_width', CuraParsingFunctions.parse_float, ['misc']),
            'support_roof_pattern': SettingsDefinition('support_roof_pattern', CuraParsingFunctions.strip_string, ['misc']),
            'support_skip_some_zags': SettingsDefinition('support_skip_some_zags', CuraParsingFunctions.parse_bool, ['misc']),
            'support_skip_zag_per_mm': SettingsDefinition('support_skip_zag_per_mm', CuraParsingFunctions.parse_int, ['misc']),
            'support_supported_skin_fan_speed': SettingsDefinition('support_supported_skin_fan_speed', CuraParsingFunctions.parse_int, ['misc']),
            'support_top_distance': SettingsDefinition('support_top_distance', CuraParsingFunctions.parse_float, ['misc']),
            'support_tower_diameter': SettingsDefinition('support_tower_diameter', CuraParsingFunctions.parse_float, ['misc']),
            'support_tower_roof_angle': SettingsDefinition('support_tower_roof_angle', CuraParsingFunctions.parse_int, ['misc']),
            'support_tree_angle': SettingsDefinition('support_tree_angle', CuraParsingFunctions.parse_int, ['misc']),
            'support_tree_branch_diameter': SettingsDefinition('support_tree_branch_diameter', CuraParsingFunctions.parse_int, ['misc']),
            'support_tree_branch_diameter_angle': SettingsDefinition('support_tree_branch_diameter_angle', CuraParsingFunctions.parse_int, ['misc']),
            'support_tree_branch_distance': SettingsDefinition('support_tree_branch_distance', CuraParsingFunctions.parse_int, ['misc']),
            'support_tree_collision_resolution': SettingsDefinition('support_tree_collision_resolution', CuraParsingFunctions.parse_float, ['misc']),
            'support_tree_enable': SettingsDefinition('support_tree_enable', CuraParsingFunctions.parse_bool, ['misc']),
            'support_tree_wall_count': SettingsDefinition('support_tree_wall_count', CuraParsingFunctions.parse_int, ['misc']),
            'support_tree_wall_thickness': SettingsDefinition('support_tree_wall_thickness', CuraParsingFunctions.parse_float, ['misc']),
            'support_type': SettingsDefinition('support_type', CuraParsingFunctions.strip_string, ['misc']),
            'support_use_towers': SettingsDefinition('support_use_towers', CuraParsingFunctions.parse_bool, ['misc']),
            'support_wall_count': SettingsDefinition('support_wall_count', CuraParsingFunctions.parse_int, ['misc']),
            'support_xy_distance': SettingsDefinition('support_xy_distance', CuraParsingFunctions.parse_float, ['misc']),
            'support_xy_distance_overhang': SettingsDefinition('support_xy_distance_overhang', CuraParsingFunctions.parse_float, ['misc']),
            'support_xy_overrides_z': SettingsDefinition('support_xy_overrides_z', CuraParsingFunctions.strip_string, ['misc']),
            'support_z_distance': SettingsDefinition('support_z_distance', CuraParsingFunctions.parse_float, ['misc']),
            'support_zag_skip_count': SettingsDefinition('support_zag_skip_count', CuraParsingFunctions.parse_int, ['misc']),
            'switch_extruder_prime_speed': SettingsDefinition('switch_extruder_prime_speed', CuraParsingFunctions.parse_int, ['misc']),
            'switch_extruder_retraction_amount': SettingsDefinition('switch_extruder_retraction_amount', CuraParsingFunctions.parse_int, ['misc']),
            'switch_extruder_retraction_speed': SettingsDefinition('switch_extruder_retraction_speed', CuraParsingFunctions.parse_int, ['misc']),
            'switch_extruder_retraction_speeds': SettingsDefinition('switch_extruder_retraction_speeds', CuraParsingFunctions.parse_int, ['misc']),
            'top_bottom_extruder_nr': SettingsDefinition('top_bottom_extruder_nr', CuraParsingFunctions.parse_int, ['misc']),
            'top_bottom_pattern': SettingsDefinition('top_bottom_pattern', CuraParsingFunctions.strip_string, ['misc']),
            'top_bottom_pattern_0': SettingsDefinition('top_bottom_pattern_0', CuraParsingFunctions.strip_string, ['misc']),
            'top_bottom_thickness': SettingsDefinition('top_bottom_thickness', CuraParsingFunctions.parse_float, ['misc']),
            'top_layers': SettingsDefinition('top_layers', CuraParsingFunctions.parse_int, ['misc']),
            'top_skin_expand_distance': SettingsDefinition('top_skin_expand_distance', CuraParsingFunctions.parse_float, ['misc']),
            'top_skin_preshrink': SettingsDefinition('top_skin_preshrink', CuraParsingFunctions.parse_float, ['misc']),
            'top_thickness': SettingsDefinition('top_thickness', CuraParsingFunctions.parse_float, ['misc']),
            'travel_avoid_distance': SettingsDefinition('travel_avoid_distance', CuraParsingFunctions.parse_float, ['misc']),
            'travel_avoid_other_parts': SettingsDefinition('travel_avoid_other_parts', CuraParsingFunctions.parse_bool, ['misc']),
            'travel_avoid_supports': SettingsDefinition('travel_avoid_supports', CuraParsingFunctions.parse_bool, ['misc']),
            'travel_compensate_overlapping_walls_0_enabled': SettingsDefinition('travel_compensate_overlapping_walls_0_enabled', CuraParsingFunctions.parse_bool, ['misc']),
            'travel_compensate_overlapping_walls_enabled': SettingsDefinition('travel_compensate_overlapping_walls_enabled', CuraParsingFunctions.parse_bool, ['misc']),
            'travel_compensate_overlapping_walls_x_enabled': SettingsDefinition('travel_compensate_overlapping_walls_x_enabled', CuraParsingFunctions.parse_bool, ['misc']),
            'travel_retract_before_outer_wall': SettingsDefinition('travel_retract_before_outer_wall', CuraParsingFunctions.parse_bool, ['misc']),
            'wall_0_extruder_nr': SettingsDefinition('wall_0_extruder_nr', CuraParsingFunctions.parse_int, ['misc']),
            'wall_0_inset': SettingsDefinition('wall_0_inset', CuraParsingFunctions.parse_int, ['misc']),
            'wall_0_wipe_dist': SettingsDefinition('wall_0_wipe_dist', CuraParsingFunctions.parse_float, ['misc']),
            'wall_extruder_nr': SettingsDefinition('wall_extruder_nr', CuraParsingFunctions.parse_int, ['misc']),
            'wall_line_count': SettingsDefinition('wall_line_count', CuraParsingFunctions.parse_int, ['misc']),
            'wall_line_width': SettingsDefinition('wall_line_width', CuraParsingFunctions.parse_float, ['misc']),
            'wall_line_width_0': SettingsDefinition('wall_line_width_0', CuraParsingFunctions.parse_float, ['misc']),
            'wall_line_width_x': SettingsDefinition('wall_line_width_x', CuraParsingFunctions.parse_float, ['misc']),
            'wall_min_flow': SettingsDefinition('wall_min_flow', CuraParsingFunctions.parse_int, ['misc']),
            'wall_min_flow_retract': SettingsDefinition('wall_min_flow_retract', CuraParsingFunctions.parse_bool, ['misc']),
            'wall_overhang_angle': SettingsDefinition('wall_overhang_angle', CuraParsingFunctions.parse_int, ['misc']),
            'wall_overhang_speed_factor': SettingsDefinition('wall_overhang_speed_factor', CuraParsingFunctions.parse_int, ['misc']),
            'wall_thickness': SettingsDefinition('wall_thickness', CuraParsingFunctions.parse_float, ['misc']),
            'wall_x_extruder_nr': SettingsDefinition('wall_x_extruder_nr', CuraParsingFunctions.parse_int, ['misc']),
            'wireframe_bottom_delay': SettingsDefinition('wireframe_bottom_delay', CuraParsingFunctions.parse_int, ['misc']),
            'wireframe_drag_along': SettingsDefinition('wireframe_drag_along', CuraParsingFunctions.parse_int, ['misc']),
            'wireframe_enabled': SettingsDefinition('wireframe_enabled', CuraParsingFunctions.parse_bool, ['misc']),
            'wireframe_fall_down': SettingsDefinition('wireframe_fall_down', CuraParsingFunctions.parse_int, ['misc']),
            'wireframe_flat_delay': SettingsDefinition('wireframe_flat_delay', CuraParsingFunctions.parse_int, ['misc']),
            'wireframe_flow': SettingsDefinition('wireframe_flow', CuraParsingFunctions.parse_int, ['misc']),
            'wireframe_flow_connection': SettingsDefinition('wireframe_flow_connection', CuraParsingFunctions.parse_int, ['misc']),
            'wireframe_flow_flat': SettingsDefinition('wireframe_flow_flat', CuraParsingFunctions.parse_int, ['misc']),
            'wireframe_height': SettingsDefinition('wireframe_height', CuraParsingFunctions.parse_int, ['misc']),
            'wireframe_nozzle_clearance': SettingsDefinition('wireframe_nozzle_clearance', CuraParsingFunctions.parse_int, ['misc']),
            'wireframe_printspeed': SettingsDefinition('wireframe_printspeed', CuraParsingFunctions.parse_int, ['misc']),
            'wireframe_printspeed_bottom': SettingsDefinition('wireframe_printspeed_bottom', CuraParsingFunctions.parse_int, ['misc']),
            'wireframe_printspeed_down': SettingsDefinition('wireframe_printspeed_down', CuraParsingFunctions.parse_int, ['misc']),
            'wireframe_printspeed_flat': SettingsDefinition('wireframe_printspeed_flat', CuraParsingFunctions.parse_int, ['misc']),
            'wireframe_printspeed_up': SettingsDefinition('wireframe_printspeed_up', CuraParsingFunctions.parse_int, ['misc']),
            'wireframe_roof_drag_along': SettingsDefinition('wireframe_roof_drag_along', CuraParsingFunctions.parse_float, ['misc']),
            'wireframe_roof_fall_down': SettingsDefinition('wireframe_roof_fall_down', CuraParsingFunctions.parse_int, ['misc']),
            'wireframe_roof_inset': SettingsDefinition('wireframe_roof_inset', CuraParsingFunctions.parse_int, ['misc']),
            'wireframe_roof_outer_delay': SettingsDefinition('wireframe_roof_outer_delay', CuraParsingFunctions.parse_float, ['misc']),
            'wireframe_straight_before_down': SettingsDefinition('wireframe_straight_before_down', CuraParsingFunctions.parse_int, ['misc']),
            'wireframe_strategy': SettingsDefinition('wireframe_strategy', CuraParsingFunctions.strip_string, ['misc']),
            'wireframe_top_delay': SettingsDefinition('wireframe_top_delay', CuraParsingFunctions.parse_int, ['misc']),
            'wireframe_top_jump': SettingsDefinition('wireframe_top_jump', CuraParsingFunctions.parse_float, ['misc']),
            'wireframe_up_half_speed': SettingsDefinition('wireframe_up_half_speed', CuraParsingFunctions.parse_float, ['misc']),
            'xy_offset': SettingsDefinition('xy_offset', CuraParsingFunctions.parse_int, ['misc']),
            'xy_offset_layer_0': SettingsDefinition('xy_offset_layer_0', CuraParsingFunctions.parse_int, ['misc']),
            'z_seam_corner': SettingsDefinition('z_seam_corner', CuraParsingFunctions.strip_string, ['misc']),
            'z_seam_relative': SettingsDefinition('z_seam_relative', CuraParsingFunctions.parse_bool, ['misc']),
            'z_seam_type': SettingsDefinition('z_seam_type', CuraParsingFunctions.strip_string, ['misc']),
            'z_seam_x': SettingsDefinition('z_seam_x', CuraParsingFunctions.parse_float, ['misc']),
            'z_seam_y': SettingsDefinition('z_seam_y', CuraParsingFunctions.parse_int, ['misc']),
            'zig_zaggify_infill': SettingsDefinition('zig_zaggify_infill', CuraParsingFunctions.parse_bool, ['misc']),
            'zig_zaggify_support': SettingsDefinition('zig_zaggify_support', CuraParsingFunctions.parse_bool, ['misc']),

        }

    def get_results(self):
        return self.results

    def version_matched(self, matches):
        if 'version' in self.active_settings_dictionary:
            version = matches.group("ver")
            self.results["version"] = version
            self.active_settings_dictionary.pop('version')

    def filament_used_meters_matched(self, matches):
        if 'filament_used_meters' in self.active_settings_dictionary:
            filament_used = matches.group("meters")
            self.results["filament_used_meters"] = float(filament_used)
            self.active_settings_dictionary.pop('filament_used_meters')

    def firmware_flavor_matched(self, matches):
        if 'firmware_flavor' in self.active_settings_dictionary:
            filament_used = matches.group("flavor")
            self.results["firmware_flavor"] = float(filament_used)
            self.active_settings_dictionary.pop('firmware_flavor')

    def layer_height_matched(self, matches):
        if 'layer_height' in self.active_settings_dictionary:
            filament_used = matches.group("flavor")
            self.results["layer_height"] = float(filament_used)
            self.active_settings_dictionary.pop('height')


class GcodeFileLineProcessor(GcodeProcessor):

    Position = None

    def __init__(
        self,
        name,
        matching_function,
        max_forward_lines_to_process=None,
        include_gcode=True,
        include_comments=True
    ):
        super(GcodeFileLineProcessor, self).__init__(name, 'gcode_file_line_processor')
        # other slicer specific vars
        self.file_process_type = 'forward'
        self.file_process_category = 'gcode-file-line'
        self.max_forward_lines_to_process = max_forward_lines_to_process
        self.forward_lines_processed = 0
        self.results = {}
        self.include_comments = include_comments
        self.include_gcode = include_gcode
        self.matching_function = matching_function
        if not self.include_comments and not self.include_gcode:
            raise ValueError("Both include_gcode and include_comments are false.  One or both must be true.")

        # get the regex last
        self.regex_definitions = self.get_regex_definitions()

    def reset(self):
        self.forward_lines_processed = 0
        self.results = {}

    def get_regex_definitions(self):
        regexes = []
        if self.include_gcode and self.include_comments:
            regexes.append(
                RegexDefinition("entire_line", "^(?P<gcode>[^;]*)[;]?(?P<comment>.*$)", self.matching_function)
            )
        elif self.include_gcode:
            regexes.append(
                RegexDefinition("gcode_only", "(?P<gcode>[^;]*)", self.matching_function)
            )
        elif self.include_comments:
            regexes.append(
                RegexDefinition("comment_only", "(?<=;)(?P<comment>.*$)", self.matching_function)
            )
        return regexes

    def on_before_start(self):
        # reset everything
        self.reset()

    def on_apply_filter(self, filter_tags=None):
        pass

    def can_process(self):
        return True

    def is_complete(self, process_type):
        if (
            (
                process_type == "forward"
                and self.max_forward_lines_to_process is not None
                and self.forward_lines_processed >= self.max_forward_lines_to_process
            )
            or len(self.regex_definitions) == 0
        ):
            return True
        return False

    def process_line(self, line, line_number, process_type):
        line = line.replace('\r', '').replace('\n', '')
        if process_type == "forward":
            self.forward_lines_processed += 1

        for regex_definition in self.regex_definitions:
            if regex_definition.match_once and regex_definition.has_matched:
                continue
            match = re.search(regex_definition.regex, line)
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
        raise NotImplementedError("You must implement the default_matching_function")

    def get_results(self):
        return self.results

