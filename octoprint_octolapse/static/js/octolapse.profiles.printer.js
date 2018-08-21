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
        self.perimeter_speed = ko.observable(values.perimeter_speed);
        self.small_perimeter_speed = ko.observable(values.small_perimeter_speed);
        self.external_perimeter_speed = ko.observable(values.external_perimeter_speed);
        self.infill_speed = ko.observable(values.infill_speed);
        self.solid_infill_speed = ko.observable(values.solid_infill_speed);
        self.top_solid_infill_speed = ko.observable(values.top_solid_infill_speed);
        self.support_speed = ko.observable(values.support_speed);
        self.bridge_speed = ko.observable(values.bridge_speed);
        self.gap_fill_speed = ko.observable(values.gap_fill_speed);
        self.first_layer_speed = ko.observable(values.first_layer_speed);
        self.speed_tolerance = ko.observable(values.speed_tolerance);
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

        self.getNonUniqueSpeeds = ko.pureComputed(function () {
            // Add all speeds to an array
            var duplicate_map = {};
            var duplicates = {};
            var speed_array = [
                {speed: self.movement_speed(), type: "Movement Speed"},
                {speed: self.retract_speed(), type: "Retraction Speed"},
                {speed: self.detract_speed(), type: "Detraction Speed"},
                {speed: self.z_hop_speed(), type: "Z Movement Speed"},
                {speed: self.perimeter_speed(), type: "Perimeter Speed"},
                {speed: self.small_perimeter_speed(), type: "Small Perimeter Speed"},
                {speed: self.external_perimeter_speed(), type: "External Perimeter Speed"},
                {speed: self.infill_speed(), type: "Infill Speed"},
                {speed: self.solid_infill_speed(), type: "Solid Infill Speed"},
                {speed: self.top_solid_infill_speed(), type: "Top Solid Infill Speed"},
                {speed: self.support_speed(), type: "Support Speed"},
                {speed: self.bridge_speed(), type: "Bridge Speed"},
                {speed: self.gap_fill_speed(), type: "Gap Fill Speed"},
                {speed: self.first_layer_speed(), type: "First Layer Speed"}
            ];

            for (var index = 0, size = speed_array.length; index < size; index++) {
                //console.log("Finding duplicates...");
                var cur_speed = speed_array[index];
                if(!cur_speed.speed)
                    continue;
                if (duplicate_map[cur_speed.speed]) {
                    // Add the duplicate we found
                    duplicates[cur_speed.type] = cur_speed.speed;
                    // Add the original item, since it is also a duplicate
                    duplicates[duplicate_map[cur_speed.speed]] = duplicate_map[cur_speed.speed];
                }
                duplicate_map[cur_speed.speed] = cur_speed.type;
            }

            return Object.keys(duplicates);
        });

        self.getMissingSpeeds = ko.pureComputed(function () {
            // Add all speeds to an array
            var missingSpeeds = [];
            var speed_array = [
                {speed: self.movement_speed(), type: "Movement Speed"},
                {speed: self.retract_speed(), type: "Retraction Speed"},
                {speed: self.detract_speed(), type: "Detraction Speed"},
                {speed: self.z_hop_speed(), type: "Z Movement Speed"},
                {speed: self.perimeter_speed(), type: "Perimeter Speed"},
                {speed: self.small_perimeter_speed(), type: "Small Perimeter Speed"},
                {speed: self.external_perimeter_speed(), type: "External Perimeter Speed"},
                {speed: self.infill_speed(), type: "Infill Speed"},
                {speed: self.solid_infill_speed(), type: "Solid Infill Speed"},
                {speed: self.top_solid_infill_speed(), type: "Top Solid Infill Speed"},
                {speed: self.support_speed(), type: "Support Speed"},
                {speed: self.bridge_speed(), type: "Bridge Speed"},
                {speed: self.gap_fill_speed(), type: "Gap Fill Speed"},
                {speed: self.first_layer_speed(), type: "First Layer Speed"}
            ];

            for (var index = 0, size = speed_array.length; index < size; index++) {
                var cur_speed = speed_array[index];
                if(!cur_speed.speed)
                    missingSpeeds.push(cur_speed.type);
            }

            return missingSpeeds;
        });

        self.axisSpeedDisplayUnitsChanged = function (obj, event) {

            if (Octolapse.Globals.is_admin()) {
                if (event.originalEvent) {
                    // Get the current guid
                    var newUnit = $("#octolapse_axis_speed_display_unit_options").val();
                    var previousUnit = self.axis_speed_display_units();
                    var precision = 3;
                    var precision_multiplier = Math.pow(10, precision);
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
                                // Convert all from mm-min to mm-sec
                                self.retract_speed(Math.round(self.retract_speed()/60.0 * precision_multiplier) /precision_multiplier);
                                self.detract_speed(Math.round(self.detract_speed()/60.0 * precision_multiplier) /precision_multiplier);
                                self.movement_speed(Math.round(self.movement_speed()/60.0 * precision_multiplier) /precision_multiplier);
                                self.z_hop_speed(Math.round(self.z_hop_speed()/60.0 * precision_multiplier) /precision_multiplier);
                                // Optional values
                                if(self.perimeter_speed())
                                    self.perimeter_speed(Math.round(self.perimeter_speed()/60.0 * precision_multiplier) /precision_multiplier);
                                if(self.small_perimeter_speed())
                                    self.small_perimeter_speed(Math.round(self.small_perimeter_speed()/60.0 * precision_multiplier) /precision_multiplier);
                                if(self.external_perimeter_speed())
                                    self.external_perimeter_speed(Math.round(self.external_perimeter_speed()/60.0 * precision_multiplier) /precision_multiplier);
                                if(self.infill_speed())
                                    self.infill_speed(Math.round(self.infill_speed()/60.0 * precision_multiplier) /precision_multiplier);
                                if(self.solid_infill_speed())
                                    self.solid_infill_speed(Math.round(self.solid_infill_speed()/60.0 * precision_multiplier) /precision_multiplier);
                                if(self.top_solid_infill_speed())
                                    self.top_solid_infill_speed(Math.round(self.top_solid_infill_speed()/60.0 * precision_multiplier) /precision_multiplier);
                                if(self.support_speed())
                                    self.support_speed(Math.round(self.support_speed()/60.0 * precision_multiplier) /precision_multiplier);
                                if(self.bridge_speed())
                                    self.bridge_speed(Math.round(self.bridge_speed()/60.0 * precision_multiplier) /precision_multiplier);
                                if(self.gap_fill_speed())
                                    self.gap_fill_speed(Math.round(self.gap_fill_speed()/60.0 * precision_multiplier) /precision_multiplier);
                                if(self.first_layer_speed())
                                    self.first_layer_speed(Math.round(self.first_layer_speed()/60.0 * precision_multiplier) /precision_multiplier);
                                self.speed_tolerance(Math.round(self.speed_tolerance()/60.0 * precision_multiplier) /precision_multiplier);

                            }
                            else
                                return false;
                            break;
                        case "mm-sec":
                            if(newUnit === "mm-min")
                            {
                                self.retract_speed(Math.round(self.retract_speed()*60.0 * precision_multiplier) / precision_multiplier);
                                self.detract_speed(Math.round(self.detract_speed()*60.0 * precision_multiplier) / precision_multiplier);
                                self.movement_speed(Math.round(self.movement_speed()*60.0 * precision_multiplier) / precision_multiplier);
                                self.z_hop_speed(Math.round(self.z_hop_speed()*60.0 * precision_multiplier) / precision_multiplier);
                                // Optional values
                                if(self.perimeter_speed())
                                    self.perimeter_speed(Math.round(self.perimeter_speed()*60.0 * precision_multiplier) /precision_multiplier);
                                if(self.small_perimeter_speed())
                                    self.small_perimeter_speed(Math.round(self.small_perimeter_speed()*60.0 * precision_multiplier) /precision_multiplier);
                                if(self.external_perimeter_speed())
                                    self.external_perimeter_speed(Math.round(self.external_perimeter_speed()*60.0 * precision_multiplier) /precision_multiplier);
                                if(self.infill_speed())
                                    self.infill_speed(Math.round(self.infill_speed()*60.0 * precision_multiplier) /precision_multiplier);
                                if(self.solid_infill_speed())
                                    self.solid_infill_speed(Math.round(self.solid_infill_speed()*60.0 * precision_multiplier) /precision_multiplier);
                                if(self.top_solid_infill_speed())
                                    self.top_solid_infill_speed(Math.round(self.top_solid_infill_speed()*60.0 * precision_multiplier) /precision_multiplier);
                                if(self.support_speed())
                                    self.support_speed(Math.round(self.support_speed()*60.0 * precision_multiplier) /precision_multiplier);
                                if(self.bridge_speed())
                                    self.bridge_speed(Math.round(self.bridge_speed()*60.0 * precision_multiplier) /precision_multiplier);
                                if(self.gap_fill_speed())
                                    self.gap_fill_speed(Math.round(self.gap_fill_speed()*60.0 * precision_multiplier) /precision_multiplier);
                                if(self.first_layer_speed())
                                    self.first_layer_speed(Math.round(self.first_layer_speed()*60.0 * precision_multiplier) /precision_multiplier);
                                self.speed_tolerance(Math.round(self.speed_tolerance()*60.0 * precision_multiplier) /precision_multiplier);

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
