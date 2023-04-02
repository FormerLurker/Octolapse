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

_octolapse_errors = {
    'preprocessor': {
        'cpp_quality_issues': {
            "1": {
                'name': "Using Fast Trigger",
                'help_link': "quality_issues_fast_trigger.md",
                'cpp_name': "stabilization_quality_issue_fast_trigger",
                'description': "You are using the 'Fast' smart trigger.  This could lead to quality issues.  If you are "
                               "having print quality issues, consider using a 'high quality' or 'snap to print' smart "
                               "trigger. "
            },
            "2": {
                'name': "Low Quality Snap-to-print",
                'help_link': "quality_issues_low_quality_snap_to_print.md",
                'cpp_name': "stabilization_quality_issue_snap_to_print_low_quality",
                'description': "In most cases using the 'High Quality' snap to print option will improve print quality, "
                               "unless you are printing with vase mode enabled. "
            },
            "3": {
                'name': "No Print Features Detected",
                'help_link': "quality_issues_no_print_features_detected.md",
                'cpp_name': "stabilization_quality_issue_no_print_features",
                'description': "No print features were found in your gcode file.  This can reduce print quality "
                               "significantly.  If you are using Slic3r or PrusaSlicer, please enable 'Verbose G-code' in "
                               "'Print Settings'->'Output Options'->'Output File'. "
            }
        },
        'cpp_processing_errors': {
            "1": {
                'name': "XYZ Axis Mode Unknown",
                'help_link': "error_help_preprocessor_axis_mode_xyz_unknown.md",
                'cpp_name': "stabilization_processing_issue_type_xyz_axis_mode_unknown",
                'is_fatal': True,
                'description': "The XYZ axis mode was not set."
            },
            "2": {
                'name': "E axis Mode Unknown",
                'help_link': "error_help_preprocessor_axis_mode_e_unknown.md",
                'cpp_name': "stabilization_processing_issue_type_e_axis_mode_unknown",
                'is_fatal': True,
                'description': "The E axis mode was not set"
            },
            "3": {
                'name': "No Definite Position",
                'help_link': "error_help_preprocessor_no_definite_position.md",
                'cpp_name': "stabilization_processing_issue_type_no_definite_position",
                'is_fatal': False,
                'description': "Unable to find a definite position."
            },
            "4": {
                'name': "Printer Not Primed",
                'help_link': "error_help_preprocessor_printer_not_primed.md",
                'cpp_name': "stabilization_processing_issue_type_printer_not_primed",
                'is_fatal': True,
                'description': "Priming was not detected."
            },
            "5": {
                'name': "No Metric Units",
                'help_link': "error_help_preprocessor_no_metric_units.md",
                'cpp_name': "stabilization_processing_issue_type_no_metric_units",
                'is_fatal': True,
                'description': "Gcode unites are not in millimeters."
            },
            "6": {
                'name': "No Snapshot Commands Found",
                'help_link': "error_help_preprocessor_no_snapshot_commands_found.md",
                'cpp_name': "stabilization_processing_issue_type_no_snapshot_commands_found",
                'is_fatal': True,
                'description': "No snapshot commands were found.  Current Snapshot Commands: @OCTOLAPSE "
                               "TAKE-SNAPSHOT{snapshot_command_gcode} "
            }
        },
        'preprocessor_errors': {
            'incorrect_trigger_type': {
                'name': "Incorrect Trigger Type",
                'help_link': "error_help_preprocessor_incorrect_trigger_type.md",
                'description': "The current trigger is not a pre-calculated trigger."
            },
            'unhandled_exception': {
                'name': "Gcode Preprocessor Error",
                'help_link': "error_help_preprocessor_unhandled_exception.md",
                'description': "An unhandled exception occurred while preprocessing your gcode file."
            },
            'unknown_trigger_type': {
                'name': "Unknown Trigger Type",
                'help_link': "error_help_preprocessor_unknown_trigger_type.md",
                'description': "The current preprocessor type {preprocessor_type} is unknown."
            },
            'no_snapshot_plans_returned': {
                'name': "No Snapshot Plans Returned",
                'help_link': "error_help_preprocessor_no_snapshot_plans_returned.md",
                'description': "No snapshots were found in your gcode file."
            }
        }
    },
    'timelapse': {
        'cannot_aquire_job_lock': {
            "name": "Unable To Acquire Job Lock",
            "description": "Unable to start timelapse, failed to acquire a job lock.  Print start failed.",
            'help_link': "error_help_timelapse_cannot_aquire_job_lock.md"
        }
    },
    'init': {
        'm114_not_supported':{
            "name": "Printer Not Supported",
            "description": "Your printer does not support the M114 command, and is incompatible with Octolapse",
            'help_link': "error_help_init_m114_not_supported.md"
        },
        'unexpected_exception':
        {
            "name": "Unexpected Exception",
            "description": "An unexpected exception was raised while starting Octolapse.  Check plugin_octolapse.log for more details.",
            'help_link': "error_help_init_unexpected_exception.md"
        },
        'cant_print_from_sd': {
            "name": "Can't start from SD",
            "description": "Octolapse cannot be used when printing from the SD card.  Your print will continue.  "
                           "Disable the plugin from within the Octolapse tab to prevent this message from displaying.",
            'help_link': "error_help_init_cant_print_from_sd.md",
            'options': {
                'is_warning': True,
                'cancel_print': False
            }
        },
        'octolapse_is_disabled': {
            "name": "Octolapse is Disabled",
            "description": "Octolapse is disabled.  Cannot start timelapse.",
            'help_link': "error_help_init_octolapse_is_disabled.md"
        },
        'printer_not_configured': {
            "name": "Printer Not Configured",
            "description": "Your Octolapse printer profile has not been configured.  To fix this error go to the "
                           "Octolapse tab, edit your selected printer via the 'gear' icon, and save your changes.",
            'help_link': "error_help_init_printer_not_configured.md"
        },
        'no_current_job_data_found': {
            "name": "No Print Job Data Found",
            "description": "Octolapse was unable to acquire job start information from Octoprint."
                           "  Please see plugin_octolapse.log for details.",
            'help_link': "error_help_init_no_current_job_data_found.md"
        },
        'no_current_job_file_data_found': {
            "name": "No Print Job File Data Found",
            "description": "Octolapse was unable to acquire file information from the current job."
                           " Please see plugin_octolapse.log for details.",
            'help_link': "error_help_init_no_current_job_file_data_found.md"
        },
        'unknown_file_origin': {
            "name": "Unknown File Origin",
            "description": "Octolapse cannot tell if you are printing from an SD card or streaming via Octoprint."
                           "  Please see plugin_octolapse.log for details.",
            'help_link': "error_help_init_unknown_file_origin.md"
        },
        'incorrect_printer_state': {
            "name": "Incorrect Printer State",
            "description": "Unable to start the timelapse when not in the Initializing state."
                           "  Please see plugin_octolapse.log for details.",
            'help_link': "error_help_init_incorrect_print_start_state.md"
        },
        'camera_init_test_failed': {
            "name": "Camera Test Failed",
            "description": "At least one camera failed testing.  Details: {error}",
            'help_link': "error_help_init_camera_init_test_failed.md"
        },
        'no_enabled_cameras': {
            "name": "No Cameras Are Enabled",
            "description": "At least one camera must be enabled to use Octolapse.",
            'help_link': "error_help_init_no_enabled_cameras.md"
        },
        'camera_settings_apply_failed': {
            "name": "Unable To Apply Camera Settings",
            "description": "Octolapse could not apply custom image preferences or could not run a camera startup "
                           "script. Details: {error}",
            'help_link': "error_help_init_camera_settings_apply_failed.md"
        },
        'before_print_start_camera_script_apply_failed': {
            "name": "Before Print Start Camera Script Failed",
            "description": "There were errors running on print start camera scripts. Details: {error}",
            'help_link': "error_help_init_before_print_start_camera_script_apply_failed.md"
        },
        'incorrect_octoprint_version': {
            "name": "Please Upgrade Octoprint",
            "description": "Octolapse requires Octoprint v1.3.9 rc3 or above, but version v{installed_version} is "
                           "installed.  Please update Octoprint to use Octolapse.",
            'help_link': "error_help_init_incorrect_octoprint_version.md"
        },
        'rendering_file_template_invalid': {
            "name": "Invalid Rendering Template",
            "description": "The rendering file template is invalid.  Please correct the template"
                           " within the current rendering profile.",
            'help_link': "error_help_init_rendering_file_template_invalid.md"
        },
        'no_printer_profile_exists': {
            "name": "No Printer Profiles Exist",
            "description": "There are no printer profiles.  Cannot start timelapse.  "
                           "Please create a printer profile in the octolapse settings pages and "
                           "restart the print.",
            'help_link': "error_help_init_no_printer_profile_exists.md"
        },
        'no_printer_profile_selected': {
            "name": "No Printer Profile Selected",
            "description": "No default printer profile was selected.  Cannot start timelapse.  "
                           "Please select a printer profile in the octolapse settings pages and "
                           "restart the print.",
            'help_link': "error_help_init_no_printer_profile_selected.md"
        },
        'no_gcode_filepath_found': {
            "name": "No Gcode Filepath Found",
            "description": "No gcode filpath was found for the current print.",
            'help_link': "error_help_init_no_gcode_filepath_found.md"
        },
        'ffmpeg_path_not_set': {
            "name": "Ffmpeg Path Not Set",
            "description": "No ffmpeg path was set in the Octoprint settings.",
            'help_link': "error_help_init_ffmpeg_path_not_set.md"
        },
        'ffmpeg_path_retrieve_exception': {
            "name": "Ffmpeg Path Not Set",
            "description": "An exception was thrown while retrieving the ffmpeg file path from Octoprint Settings.",
            'help_link': "error_help_init_ffmpeg_path_retrieve_exception.md"
        },
        'ffmpeg_not_found_at_path': {
            "name": "Ffmpeg Not Found at Path",
            "description": "Ffmpeg was not found at the specified path.",
            'help_link': "error_help_init_ffmpeg_not_found_at_path.md"
        },
        'automatic_slicer_no_settings_found': {
            "name": "Slicer Settings Not Found",
            "description": "No slicer settings were not found in your gcode file.",
            'help_link': "error_help_init_automatic_slicer_no_settings_found.md"
        },
        'automatic_slicer_settings_missing': {
            "name": "Slicer Settings Missing",
            "description": "Some slicer settings were missing from your gcode file.  "
                           "Missing Settings: {missing_settings}",
            'help_link': "error_help_init_automatic_slicer_settings_missing.md"
        },
        'automatic_slicer_no_settings_found_continue_printing': {
            "name": "Slicer Settings Not Found",
            "description": "No slicer settings were not found in your gcode file. Continue on failure is enabled so "
                           "your print will continue, but the timelapse has been aborted.",
            'help_link': "error_help_init_automatic_slicer_no_settings_found.md"
        },
        'automatic_slicer_settings_missing_continue_printing': {
            "name": "Slicer Settings Missing",
            "description": "Some slicer settings were missing from your gcode file.  Continue on failure is enabled "
                           "so your print will continue, but the timelapse has been aborted. Missing Settings: {"
                           "missing_settings}",
            'help_link': "error_help_init_automatic_slicer_settings_missing.md"
        },
        'manual_slicer_settings_missing': {
            "name": "Manual Slicer Settings Missing",
            "description": "Your printer profile is missing some required slicer settings.  Either enter the settings"
                           " in your printer profile, or switch to 'automatic' slicer settings.  Missing Settings:"
                           " {missing_settings}",
            'help_link': "error_help_init_manual_slicer_settings_missing.md"
        },
        'timelapse_start_exception': {
            "name": "Error Starting Timelapse",
            "description": "An unexpected error occurred while starting the timelapse.  See plugin_octolapse.log for "
                           "details.",
            'help_link': "error_help_init_timelapse_start_exception.md"
        },
        'too_few_extruders_defined': {
            "name": "Extruder Count Error",
            "description": "Your printer profile has fewer extruders ({printer_num_extruders}) defined than your gcode file ({gcode_num_extruders}).",
            'help_link': "error_help_init_too_few_extruders_defined.md"
        },
        'too_few_extruder_offsets_defined': {
            "name": "Extruder Count Error",
            "description": "Your printer profile has fewer extruder offsets ({num_extruder_offsets}) defined than extruders ({num_extruders}).",
            'help_link': "error_help_init_too_few_extruders_offsets_defined.md"
        },
        'unable_to_accept_snapshot_plan': {
            "name": "Extruder Count Error",
            "description": "Unable to accept the snapshot plan.  Either it has already been accepted/cancellled, or an unexpected error occurred.",
            'help_link': "error_help_init_unable_to_accept_snapshot_plan.md"
        },
        'directory_test_failed': {
            "name": "Directory Tests Failed",
            "description": "The following Octolapse directories failed testing:  {failed_directories}.",
            'help_link': "error_help_init_directory_test_failed.md"
        },
        "overlay_font_path_not_found": {
            "name": "Rendering Overlay Font Not Found",
            "description": "The current rendering profile has a rendering overlay, but the selected font could not be found in the following location:  {overlay_font_path}.",
            'help_link': "error_help_init_overlay_font_path_not_found.md"
        }


    },
    'settings': {
        'slicer': {
            'simplify3d': {
                "duplicate_toolhead_numbers": {
                    "name": "Duplicate Toolhead Numbers",
                    "description": "Multiple extruders are defined with the same toolhead number in simplify, "
                                   "which is not supported by Octolapse.  Duplicated toolhead numbers: "
                                   "{toolhead_numbers}",
                    "help_link": "error_help_settings_slicer_simplify3d_duplicate_toolhead_numbers.md"
                },
                "extruder_count_mismatch": {
                    "name": "Extruder Count Mismatch",
                    "description": "Your printer profile is configured with {configured_extruder_count} extruders, "
                                   "but Simpify 3D is configured with {detected_extruder_count} extruders.",
                    "help_link": "error_help_settings_slicer_simplify3d_extruder_count_mismatch.md"
                },
                "max_extruder_count_exceeded": {
                    "name": "Max Extruder Count Exceeded",
                    "description":  "Octolapse detected {simplify_extruder_count} extruders in your Simplify 3D "
                                    "gcode file, but can only support {max_extruder_count} extruders.",
                    "help_link": "error_help_settings_slicer_simplify3d_max_extruder_count_exceeded.md"
                },
                "unexpected_max_toolhead_number": {
                    "name": "Incorrect Max Toolhead Number",
                    "description": "The maximum toolhead number expected was T{expected_max_toolhead_number}, but "
                                   "Simplify 3D was configured with a max toolhead of {max_toolhead_number}.",
                    "help_link": "error_help_settings_slicer_simplify3d_unexpected_max_toolhead_number.md"
                }
            }
        }
    },
    'rendering': {
        'archive': {
            'import': {
                'no_files_found': {
                    "name": "No Files Were Found",
                    "description": "No files were found within the archive.",
                    "help_link": "error_help_rendering_archive_import_no_files_found.md"
                },
                'zip_file_too_large': {
                    "name": "The Archive is Too Large",
                    "description": "The zip archive is too large to import.",
                    "help_link": "error_help_rendering_archive_import_zip_file_too_large.md"
                },
                'zip_file_corrupt': {
                    "name": "The Archive is Corrupt",
                    "description": "The zip archive is too large to import.",
                    "help_link": "error_help_rendering_archive_import_zip_file_corrupt.md"
                }
            }
        }
    }
}

_error_not_found = {
    "name": "Unknown Error",
    "description": "An unknown error was raised, but the provided key could not be found in the "
                   "ErrorMessages dict.  Keys: {keys}",
    "help_link": "error_help_error_not_found.md"
}

_error_not_a_valid_error_dict = {
    "name": "Unknown Error",
    "description": "An unknown error was raised, but the provided key could not be found in the "
                   "ErrorMessages dict.  Keys: {keys}",
    "help_link": "error_help_not_a_valid_error_dict.md"
}


def get_error(keys,  **kwargs):
    current_error_dict = _octolapse_errors
    for key in keys:
        try:
            current_error_dict = current_error_dict[key]
        except KeyError:
            error = _error_not_found.copy()
            error["description"] = error["description"].format(keys=keys)
            return error
    if not all(k in current_error_dict for k in ["name", "description", "help_link"]):
        error = _error_not_a_valid_error_dict.copy()
        error["description"] = error["description"].format(keys=keys)
        return error
    # copy the error so we don't mess up the original dict
    error = current_error_dict.copy()
    # try to format with any kwargs
    try:
        error["description"] = error["description"].format(**kwargs)
    except KeyError:
        pass

    return error

class OctolapseException(Exception):
    def __init__(self, keys, cause=None, **kwargs):
        super(Exception, self).__init__()
        self.keys = keys
        self.cause = cause if cause is not None else None
        self.error = get_error(keys, **kwargs)
        self.name = self.error["name"]
        self.description = self.error["description"]
        self.help_link = self.error["help_link"]

    def __str__(self):
        if self.cause is None:
            return self.description
        return "{0} - Inner Exception: {1}".format(
            self.description,
            "{} - {}".format(type(self.cause), self.cause)
        )

    def to_dict(self):
        return {
            "name": self.name,
            "description": str(self),
            "help_link": self.help_link
        }



