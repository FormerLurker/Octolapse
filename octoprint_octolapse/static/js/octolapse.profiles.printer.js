/*
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
*/
$(function() {
    Octolapse.PrinterProfileValidationRules = {
        rules: {
            min_x: { lessThanOrEqual: "#octolapse_printer_max_x" },
            max_x: { greaterThanOrEqual: "#octolapse_printer_min_x"},
            min_y: { lessThanOrEqual: "#octolapse_printer_max_y" },
            max_y: { greaterThanOrEqual: "#octolapse_printer_min_y" },
            min_z: { lessThanOrEqual: "#octolapse_printer_max_z" },
            max_z: { greaterThanOrEqual: "#octolapse_printer_min_z" },
            auto_position_detection_commands: { csvString: true }
        },
        messages: {
            name: "Please enter a name for your profile",
            min_x : { lessThanOrEqual: "Must be less than or equal to the 'X - Width Max' field." },
            max_x : { greaterThanOrEqual: "Must be greater than or equal to the ''X - Width Min'' field." },
            min_y : { lessThanOrEqual: "Must be less than or equal to the 'Y - Width Max' field." },
            max_y : { greaterThanOrEqual: "Must be greater than or equal to the ''Y - Width Min'' field." },
            min_z : { lessThanOrEqual: "Must be less than or equal to the 'Z - Width Max' field." },
            max_z: { greaterThanOrEqual: "Must be greater than or equal to the ''Z - Width Min'' field." },
            auto_position_detection_commands: { csvString:"Please enter a series of gcode commands (without parameters) separated by commas, or leave this field blank." }
        }
    };




    Octolapse.PrinterProfileViewModel = function (values) {
        var self = this;
        self.profileTypeName = ko.observable("Printer")
        self.guid = ko.observable(values.guid);
        self.name = ko.observable(values.name);
        self.description = ko.observable(values.description);
        self.retract_length = ko.observable(values.retract_length);
        self.retract_speed = ko.observable(values.retract_speed);
        self.detract_speed = ko.observable(values.detract_speed);
        self.movement_speed = ko.observable(values.movement_speed);
        self.z_hop = ko.observable(values.z_hop);
        self.z_hop_speed = ko.observable(values.z_hop_speed);
        self.snapshot_command = ko.observable(values.snapshot_command);
        self.printer_position_confirmation_tolerance = ko.observable(values.printer_position_confirmation_tolerance);
        self.auto_detect_position = ko.observable(values.auto_detect_position);
        self.auto_position_detection_commands = ko.observable(values.auto_position_detection_commands);
        self.origin_x = ko.observable(values.origin_x);
        self.origin_y = ko.observable(values.origin_y);
        self.origin_z = ko.observable(values.origin_z);
        self.abort_out_of_bounds = ko.observable(values.abort_out_of_bounds);
        self.override_octoprint_print_volume = ko.observable(values.override_octoprint_print_volume);
        self.min_x = ko.observable(values.min_x);
        self.max_x = ko.observable(values.max_x);
        self.min_y = ko.observable(values.min_y);
        self.max_y = ko.observable(values.max_y);
        self.min_z = ko.observable(values.min_z);
        self.max_z = ko.observable(values.max_z);
        self.priming_height = ko.observable(values.priming_height);
        self.e_axis_default_mode = ko.observable(values.e_axis_default_mode);
        self.g90_influences_extruder = ko.observable(values.g90_influences_extruder);
        self.xyz_axes_default_mode = ko.observable(values.xyz_axes_default_mode);
        self.units_default = ko.observable(values.units_default);
        self.axis_speed_display_units = ko.observable(values.axis_speed_display_units);
        self.default_firmware_retractions = ko.observable(values.default_firmware_retractions);
        self.default_firmware_retractions_zhop = ko.observable(values.default_firmware_retractions_zhop);
        self.suppress_snapshot_command_always = ko.observable(values.suppress_snapshot_command_always);
        // get the time component of the axis speed units (min/mm)
        self.getAxisSpeedTimeUnit = ko.pureComputed(function () {
                if (self.axis_speed_display_units() === "mm-min")
                    return 'min';
                if (self.axis_speed_display_units() === "mm-sec")
                    return 'sec';
                return '?';
            }, self);

        self.axisSpeedDisplayUnitsChanged = function (obj, event) {
            if (Octolapse.Globals.is_admin()) {
                if (event.originalEvent) {
                    // Get the current guid
                    var newUnit = $("#octolapse_axis_speed_display_unit_options").val();
                    var previousUnit = self.axis_speed_display_units();

                    if(newUnit === previousUnit) {
                        //console.log("Axis speed display units, no change detected!")
                        return false;

                    }
                    //console.log("Changing axis speed from " + previousUnit + " to " + newUnit)
                    // in case we want to have more units in the future, check all cases
                    switch (previousUnit)
                    {
                        case "mm-min":
                            if(newUnit === "mm-sec")
                            {
                                self.retract_speed(Math.round(self.retract_speed()/60.0 * 100) / 100);
                                self.detract_speed(Math.round(self.detract_speed()/60.0 * 100) / 100);
                                self.movement_speed(Math.round(self.movement_speed()/60.0 * 100) / 100);
                                self.z_hop_speed(Math.round(self.z_hop_speed()/60.0 * 100) / 100);
                                // Convert all from mm-min to mm-sec
                            }
                            else
                                return false;
                            break;
                        case "mm-sec":
                            if(newUnit === "mm-min")
                            {
                                self.retract_speed(Math.round(self.retract_speed()*60.0 * 100) / 100);
                                self.detract_speed(Math.round(self.detract_speed()*60.0 * 100) / 100);
                                self.movement_speed(Math.round(self.movement_speed()*60.0 * 100) / 100);
                                self.z_hop_speed(Math.round(self.z_hop_speed()*60.0 * 100) / 100);
                            }
                            else
                                return false;
                            break;
                        default:
                            return false;
                    }
                    return true;
                }
            }
        };
    };
});
