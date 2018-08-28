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
            auto_position_detection_commands: { csvString: true },
            printer_profile_other_slicer_retract_length: {required: true},
            printer_profile_slicer_other_z_hop: {required: true},
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
        self.slicer_type = ko.observable(values.slicer_type);
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

        self.create_helpers = function(values){
            var self = this;
            self.create_other_slicer_viewmodel = function(profile_observables){
                var self = this;
                self.speed_tolerance = ko.observable(profile_observables.speed_tolerance);
                self.axis_speed_display_units = ko.observable(profile_observables.axis_speed_display_units);

                self.retract_length = ko.observable(profile_observables.retract_length);
                self.retract_speed = ko.observable(Octolapse.roundToIncrement(profile_observables.retract_speed, self.speed_tolerance()));
                self.detract_speed = ko.observable(Octolapse.roundToIncrement(profile_observables.detract_speed, self.speed_tolerance()));
                self.movement_speed = ko.observable(Octolapse.roundToIncrement(profile_observables.movement_speed, self.speed_tolerance()));
                self.print_speed = ko.observable(Octolapse.roundToIncrement(profile_observables.print_speed, self.speed_tolerance()));
                self.z_hop = ko.observable(profile_observables.z_hop);
                self.z_hop_speed = ko.observable(Octolapse.roundToIncrement(profile_observables.z_hop_speed, self.speed_tolerance()));
                self.perimeter_speed = ko.observable(Octolapse.roundToIncrement(profile_observables.perimeter_speed, self.speed_tolerance()));
                self.small_perimeter_speed = ko.observable(Octolapse.roundToIncrement(profile_observables.small_perimeter_speed, self.speed_tolerance()));
                self.external_perimeter_speed = ko.observable(Octolapse.roundToIncrement(profile_observables.external_perimeter_speed, self.speed_tolerance()));
                self.infill_speed = ko.observable(Octolapse.roundToIncrement(profile_observables.infill_speed, self.speed_tolerance()));
                self.solid_infill_speed = ko.observable(Octolapse.roundToIncrement(profile_observables.solid_infill_speed, self.speed_tolerance()));
                self.top_solid_infill_speed = ko.observable(Octolapse.roundToIncrement(profile_observables.top_solid_infill_speed, self.speed_tolerance()));
                self.support_speed = ko.observable(Octolapse.roundToIncrement(profile_observables.support_speed, self.speed_tolerance()));
                self.bridge_speed = ko.observable(Octolapse.roundToIncrement(profile_observables.bridge_speed, self.speed_tolerance()));
                self.gap_fill_speed = ko.observable(Octolapse.roundToIncrement(profile_observables.gap_fill_speed, self.speed_tolerance()));
                self.first_layer_speed = ko.observable(Octolapse.roundToIncrement(profile_observables.first_layer_speed, self.speed_tolerance()));
                self.first_layer_travel_speed = ko.observable(Octolapse.roundToIncrement(profile_observables.first_layer_travel_speed, self.speed_tolerance()));
                self.skirt_brim_speed = ko.observable(Octolapse.roundToIncrement(profile_observables.skirt_brim_speed, self.speed_tolerance()));

                self.above_raft_speed = ko.observable(Octolapse.roundToIncrement(profile_observables.above_raft_speed, self.speed_tolerance()));
                self.ooze_shield_speed = ko.observable(Octolapse.roundToIncrement(profile_observables.ooze_shield_speed, self.speed_tolerance()));
                self.prime_pillar_speed = ko.observable(Octolapse.roundToIncrement(profile_observables.prime_pillar_speed, self.speed_tolerance()));

                /*
                    Create a getter for each profile variable (settings.py - printer class)
                */
                self.get_retract_length = function(){
                   return self.retract_length();
                };
                self.get_retract_speed = function(){
                   return self.retract_speed();
                };
                self.get_detract_speed = function(){
                   return self.detract_speed();
                };
                self.get_movement_speed = function(){
                   return self.movement_speed();
                };
                self.get_z_hop = function(){
                   return self.z_hop();
                };
                self.get_z_hop_speed = function(){
                   return self.z_hop_speed();
                };
                self.get_maximum_z_speed = function(){
                    return null;
                };
                self.get_print_speed = function(){
                    return self.print_speed();
                };
                self.get_perimeter_speed = function(){
                   return self.perimeter_speed();
                };
                self.get_small_perimeter_speed = function(){
                   return self.small_perimeter_speed();
                };
                self.get_external_perimeter_speed = function(){
                   return self.external_perimeter_speed();
                };
                self.get_infill_speed = function(){
                   return self.infill_speed();
                };
                self.get_solid_infill_speed = function(){
                   return self.solid_infill_speed();
                };
                self.get_top_solid_infill_speed = function(){
                   return self.top_solid_infill_speed();
                };
                self.get_support_speed = function(){
                   return self.support_speed();
                };
                self.get_bridge_speed = function(){
                   return self.bridge_speed();
                };
                self.get_gap_fill_speed = function(){
                   return self.gap_fill_speed();
                };
                self.get_first_layer_speed = function(){
                   return self.first_layer_speed();
                };
                self.get_first_layer_travel_speed = function(){
                   return self.first_layer_travel_speed();
                };
                self.get_skirt_brim_speed = function(){
                   return self.skirt_brim_speed();
                };

                self.get_above_raft_speed = function(){
                   return self.above_raft_speed();
                };
                self.get_ooze_shield_speed = function(){
                   return self.ooze_shield_speed();
                };
                self.get_prime_pillar_speed = function(){
                   return self.prime_pillar_speed();
                };

                self.get_speed_tolerance = function(){
                   return self.speed_tolerance();
                };
                self.get_axis_speed_display_units = function(){
                   return self.axis_speed_display_units();
                };
                // get the time component of the axis speed units (min/mm)
                self.getAxisSpeedTimeUnit = ko.pureComputed(function () {
                    if (self.axis_speed_display_units() === "mm-min")
                        return 'min';
                    if (self.axis_speed_display_units() === "mm-sec")
                        return 'sec';
                    return '?';
                }, self);

                // Get a list of speeds for use with feature detection
                self.getSlicerSpeedList = function(){
                    return [
                        {speed: self.movement_speed(), type: "Movement"},
                        {speed: self.z_hop_speed(), type: "Z Movement"},
                        {speed: self.retract_speed(), type: "Retraction"},
                        {speed: self.detract_speed(), type: "Detraction"},
                        {speed: self.print_speed(), type: "Print"},

                        {speed: self.perimeter_speed(), type: "Perimeter"},
                        {speed: self.small_perimeter_speed(), type: "Small Perimeter"},
                        {speed: self.external_perimeter_speed(), type: "External Perimeter"},
                        {speed: self.infill_speed(), type: "Infill"},
                        {speed: self.solid_infill_speed(), type: "Solid Infill"},
                        {speed: self.top_solid_infill_speed(), type: "Top Solid Infill"},
                        {speed: self.support_speed(), type: "Support"},
                        {speed: self.bridge_speed(), type: "Bridge"},
                        {speed: self.gap_fill_speed(), type: "Gap Fill"},
                        {speed: self.first_layer_speed(), type: "First Layer"},
                        {speed: self.first_layer_travel_speed(), type: "First Layer Travel"},
                        {speed: self.above_raft_speed(), type: "Above Raft"},
                        {speed: self.ooze_shield_speed(), type: "Ooze Shield"},
                        {speed: self.prime_pillar_speed(), type: "Prime Pillar"},
                        {speed: self.prime_pillar_speed(), type: "Skirt/Brim"}

                    ];
                };

                self.axisSpeedDisplayUnitsChanged = function (obj, event) {

                    if (Octolapse.Globals.is_admin()) {
                        if (event.originalEvent) {
                            // Get the current guid
                            var newUnit = $("#octolapse_axis_speed_display_unit_options").val();
                            var previousUnit = self.get_axis_speed_display_units();
                            if(newUnit === previousUnit) {
                                //console.log("Axis speed display units, no change detected!")
                                return false;

                            }
                            //console.log("Changing axis speed from " + previousUnit + " to " + newUnit)
                            // in case we want to have more units in the future, check all cases
                            // Convert all from mm-min to mm-sec
                            self.speed_tolerance(Octolapse.convertAxisSpeedUnit(self.get_speed_tolerance(),newUnit,previousUnit, 0.001, previousUnit));
                            self.retract_speed(Octolapse.convertAxisSpeedUnit(self.get_retract_speed(),newUnit,previousUnit, self.get_speed_tolerance(), previousUnit));
                            self.detract_speed(Octolapse.convertAxisSpeedUnit(self.get_detract_speed(),newUnit,previousUnit, self.get_speed_tolerance(), previousUnit));
                            self.movement_speed(Octolapse.convertAxisSpeedUnit(self.get_movement_speed(),newUnit,previousUnit, self.get_speed_tolerance(), previousUnit));
                            self.z_hop_speed(Octolapse.convertAxisSpeedUnit(self.get_z_hop_speed(),newUnit,previousUnit, self.get_speed_tolerance(), previousUnit));

                            // Optional values
                            self.print_speed(Octolapse.convertAxisSpeedUnit(self.get_print_speed(),newUnit,previousUnit, self.get_speed_tolerance(), previousUnit));
                            self.perimeter_speed(Octolapse.convertAxisSpeedUnit(self.get_perimeter_speed(),newUnit,previousUnit, self.get_speed_tolerance(), previousUnit));
                            self.small_perimeter_speed(Octolapse.convertAxisSpeedUnit(self.get_small_perimeter_speed(),newUnit,previousUnit, self.get_speed_tolerance(), previousUnit));
                            self.external_perimeter_speed(Octolapse.convertAxisSpeedUnit(self.get_external_perimeter_speed(),newUnit,previousUnit, self.get_speed_tolerance(), previousUnit));
                            self.infill_speed(Octolapse.convertAxisSpeedUnit(self.get_infill_speed(),newUnit,previousUnit, self.get_speed_tolerance(), previousUnit));
                            self.solid_infill_speed(Octolapse.convertAxisSpeedUnit(self.get_solid_infill_speed(),newUnit,previousUnit, self.get_speed_tolerance(), previousUnit));
                            self.top_solid_infill_speed(Octolapse.convertAxisSpeedUnit(self.get_top_solid_infill_speed(),newUnit,previousUnit, self.get_speed_tolerance(), previousUnit));
                            self.support_speed(Octolapse.convertAxisSpeedUnit(self.get_support_speed(),newUnit,previousUnit, self.get_speed_tolerance(), previousUnit));
                            self.bridge_speed(Octolapse.convertAxisSpeedUnit(self.get_bridge_speed(),newUnit,previousUnit, self.get_speed_tolerance(), previousUnit));

                            self.gap_fill_speed(Octolapse.convertAxisSpeedUnit(self.get_gap_fill_speed(),newUnit,previousUnit, self.get_speed_tolerance(), previousUnit));
                            self.first_layer_speed(Octolapse.convertAxisSpeedUnit(self.get_first_layer_speed(),newUnit,previousUnit, self.get_speed_tolerance(), previousUnit));
                            self.first_layer_travel_speed(Octolapse.convertAxisSpeedUnit(self.get_first_layer_travel_speed(),newUnit,previousUnit, self.get_speed_tolerance(), previousUnit));
                            self.skirt_brim_speed(Octolapse.convertAxisSpeedUnit(self.get_skirt_brim_speed(),newUnit,previousUnit, self.get_speed_tolerance(), previousUnit));

                            self.above_raft_speed(Octolapse.convertAxisSpeedUnit(self.get_above_raft_speed(),newUnit,previousUnit, self.get_speed_tolerance(), previousUnit));
                            self.ooze_shield_speed(Octolapse.convertAxisSpeedUnit(self.get_ooze_shield_speed(),newUnit,previousUnit, self.get_speed_tolerance(), previousUnit));
                            self.prime_pillar_speed(Octolapse.convertAxisSpeedUnit(self.get_prime_pillar_speed(),newUnit,previousUnit, self.get_speed_tolerance(), previousUnit));
                            return true;
                        }
                    }
                };
            };
            self.other_slicer_viewmodel = new self.create_other_slicer_viewmodel(values);

            self.create_slic3r_pe_viewmodel = function(profile_observables){
                var self = this;
                self.get_axis_speed_display_units = function(){
                   return "mm-sec"
                };
                self.get_speed_tolerance = function(){
                   return 0.01;
                };
                // Initialize profile variables from observables
                self.retract_length = ko.observable(profile_observables.retract_length);
                self.z_hop = ko.observable(profile_observables.z_hop);

                self.retract_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.retract_speed,self.get_axis_speed_display_units(),profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                self.detract_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.detract_speed,self.get_axis_speed_display_units(),profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                self.movement_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.movement_speed,self.get_axis_speed_display_units(),profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                self.perimeter_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.perimeter_speed,
                        self.get_axis_speed_display_units(),
                        profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                self.small_perimeter_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.small_perimeter_speed,
                        self.get_axis_speed_display_units(),
                        profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                self.external_perimeter_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.external_perimeter_speed,
                        self.get_axis_speed_display_units(),
                        profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                self.infill_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.infill_speed,self.get_axis_speed_display_units(),profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                self.solid_infill_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.solid_infill_speed,self.get_axis_speed_display_units(),profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                self.top_solid_infill_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.top_solid_infill_speed,
                        self.get_axis_speed_display_units(),
                        profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                self.support_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.support_speed,self.get_axis_speed_display_units(),profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                self.bridge_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.bridge_speed,self.get_axis_speed_display_units(),profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                self.gap_fill_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.gap_fill_speed,self.get_axis_speed_display_units(),profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                self.first_layer_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.first_layer_speed,self.get_axis_speed_display_units(),profile_observables.axis_speed_display_units, self.get_speed_tolerance()));

                /*
                    Create a getter for each profile variable (settings.py - printer class)
                */
                self.get_retract_length = function(){
                   return self.retract_length();
                };
                self.get_retract_speed = function(){
                   return self.retract_speed();
                };
                self.get_detract_speed = function(){
                   return self.detract_speed();
                };
                self.get_movement_speed = function(){
                   return self.movement_speed();
                };
                self.get_z_hop = function(){
                   return self.z_hop();
                };
                self.get_z_hop_speed = function(){
                   return self.movement_speed();
                };
                self.get_maximum_z_speed = function(){
                    return null;
                };
                self.get_print_speed = function(){
                    return null;
                };
                self.get_perimeter_speed = function(){
                   return self.perimeter_speed();
                };
                self.get_small_perimeter_speed = function(){
                   return self.small_perimeter_speed();
                };
                self.get_external_perimeter_speed = function(){
                   return self.external_perimeter_speed();
                };
                self.get_infill_speed = function(){
                   return self.infill_speed();
                };
                self.get_solid_infill_speed = function(){
                   return self.solid_infill_speed();
                };
                self.get_top_solid_infill_speed = function(){
                   return self.top_solid_infill_speed();
                };
                self.get_support_speed = function(){
                   return self.support_speed();
                };
                self.get_bridge_speed = function(){
                   return self.bridge_speed();
                };
                self.get_gap_fill_speed = function(){
                   return self.gap_fill_speed();
                };
                self.get_first_layer_speed = function(){
                   return self.first_layer_speed();
                };
                self.get_first_layer_travel_speed = function(){
                   return self.movement_speed();
                };
                self.get_skirt_brim_speed = function(){
                   return self.first_layer_speed();
                };

                // Get a list of speeds for use with feature detection
                self.getSlicerSpeedList = function(){
                    return [
                        {speed: self.retract_speed(), type: "Retraction"},
                        {speed: self.detract_speed(), type: "Detraction"},
                        {speed: self.perimeter_speed(), type: "Perimeters"},
                        {speed: self.small_perimeter_speed(), type: "Small Perimeters"},
                        {speed: self.external_perimeter_speed(), type: "External Perimeters"},
                        {speed: self.infill_speed(), type: "Infill"},
                        {speed: self.solid_infill_speed(), type: "Solid Infill"},
                        {speed: self.top_solid_infill_speed(), type: "Top Solid Infill"},
                        {speed: self.support_speed(), type: "Supports"},
                        {speed: self.bridge_speed(), type: "Bridges"},
                        {speed: self.gap_fill_speed(), type: "Gaps"},
                        {speed: self.movement_speed(), type: "Movement"},
                        {speed: self.first_layer_speed(), type: "First Layer"}
                    ];
                };
            };
            self.slic3r_pe_viewmodel = new self.create_slic3r_pe_viewmodel(values);

            self.create_cura_viewmodel = function(profile_observables){
                var self = this;
                self.get_axis_speed_display_units = function(){
                   return 'mm-sec';
                };
                self.get_speed_tolerance = function(){
                   return 0.00005;
                };
                // Initialize profile variables from observables
                self.retraction_distance = ko.observable(profile_observables.retract_length);
                self.z_hop_height = ko.observable(profile_observables.z_hop);
                self.retraction_retract_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.retract_speed,self.get_axis_speed_display_units(),profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                self.retraction_prime_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.detract_speed,self.get_axis_speed_display_units(),profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                self.travel_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.movement_speed,self.get_axis_speed_display_units(),profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                self.inner_wall_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.perimeter_speed,
                        self.get_axis_speed_display_units(),
                        profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                self.outer_wall_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.external_perimeter_speed,
                        self.get_axis_speed_display_units(),
                        profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                self.top_bottom_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.top_solid_infill_speed,
                        self.get_axis_speed_display_units(),
                        profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                self.infill_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.infill_speed,self.get_axis_speed_display_units(),profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                self.print_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.print_speed,self.get_axis_speed_display_units(),profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                self.initial_layer_print_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.first_layer_speed,self.get_axis_speed_display_units(),profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                self.initial_layer_travel_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.first_layer_travel_speed,self.get_axis_speed_display_units(),profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                self.skirt_brim_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.skirt_brim_speed,self.get_axis_speed_display_units(),profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                self.maximum_z_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.maximum_z_speed,self.get_axis_speed_display_units(),profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                /*
                    Create a getter for each profile variable (settings.py - printer class)
                */
                self.get_retract_length = function(){
                   return self.retraction_distance();
                };
                self.get_retract_speed = function(){
                   return self.retraction_retract_speed();
                };
                self.get_detract_speed = function(){
                   return self.retraction_prime_speed();
                };
                self.get_movement_speed = function(){
                   return self.travel_speed();
                };
                self.get_z_hop = function(){
                   return self.z_hop_height();
                };
                self.get_z_hop_speed = function(){
                    if( ( self.maximum_z_speed() || 0) == 0)
                        return self.travel_speed();

                    return Math.min(self.maximum_z_speed(), self.travel_speed())
                };
                self.get_maximum_z_speed = function(){
                    return self.maximum_z_speed();
                };
                self.get_print_speed = function(){
                    return self.print_speed();
                };
                self.get_perimeter_speed = function(){
                   return self.inner_wall_speed();
                };
                self.get_small_perimeter_speed = function(){
                   return self.inner_wall_speed();
                };
                self.get_external_perimeter_speed = function(){
                   return self.outer_wall_speed();
                };
                self.get_infill_speed = function(){
                   return self.infill_speed();
                };
                self.get_solid_infill_speed = function(){
                   return self.infill_speed();
                };
                self.get_top_solid_infill_speed = function(){
                   return self.top_bottom_speed();
                };
                self.get_support_speed = function(){
                   return self.print_speed();
                };
                self.get_bridge_speed = function(){
                   return self.outer_wall_speed();
                };
                self.get_gap_fill_speed = function(){
                   return self.print_speed();
                };
                self.get_print_speed = function(){
                    return self.print_speed();
                }
                self.get_first_layer_speed = function(){
                   return self.initial_layer_print_speed();
                };
                self.get_first_layer_travel_speed = function(){
                   return self.initial_layer_travel_speed();
                };
                self.get_skirt_brim_speed = function(){
                   return self.skirt_brim_speed();
                };

                // Get a list of speeds for use with feature detection
                self.getSlicerSpeedList = function(){
                    return [
                        {speed: self.print_speed(), type: "Normal Print"},
                        {speed: self.retraction_retract_speed(), type: "Retract"},
                        {speed: self.retraction_prime_speed(), type: "Prime"},
                        {speed: self.infill_speed(), type: "Infill"},
                        {speed: self.outer_wall_speed(), type: "Outer Wall"},
                        {speed: self.inner_wall_speed(), type: "Inner Wall"},
                        {speed: self.top_bottom_speed(), type: "Top/Bottom"},
                        {speed: self.travel_speed(), type: "Travel"},
                        {speed: self.initial_layer_print_speed(), type: "Initial Layer"},
                        {speed: self.initial_layer_travel_speed(), type: "Initial Layer Travel"},
                        {speed: self.skirt_brim_speed(), type: "Skirt/Brim"},
                        {speed: self.get_z_hop_speed(), type: "Z Travel"},
                    ];
                };

            };
            self.cura_viewmodel = new self.create_cura_viewmodel(values);

            self.create_simplify_3d_viewmodel = function(profile_observables){
                var self = this;
                self.get_axis_speed_display_units = function(){
                   return 'mm-min';
                };
                self.get_speed_tolerance = function(){
                   return 0.5;
                };
                // Initialize profile variables from observables
                self.retraction_distance = ko.observable(profile_observables.retract_length);
                self.retraction_vertical_lift = ko.observable(profile_observables.z_hop);
                self.retraction_retract_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.retract_speed,self.get_axis_speed_display_units(),profile_observables.axis_speed_display_units, self.get_speed_tolerance()));

                self.first_layer_speed_multiplier = ko.observable(profile_observables.first_layer_speed_multiplier || 100.0);
                self.above_raft_speed_multiplier = ko.observable(profile_observables.above_raft_speed_multiplier || 100.0);
                self.prime_pillar_speed_multiplier = ko.observable(profile_observables.prime_pillar_speed_multiplier || 100.0);
                self.ooze_shield_speed_multiplier = ko.observable(profile_observables.ooze_shield_speed_multiplier || 100.0);

                self.default_printing_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.print_speed,self.get_axis_speed_display_units(),profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                self.outline_speed_multiplier = ko.observable(profile_observables.outline_speed_multiplier || 100.0);
                self.solid_infill_speed_multiplier = ko.observable(profile_observables.solid_infill_speed_multiplier || 100.0);
                self.support_structure_speed_multiplier = ko.observable(profile_observables.support_structure_speed_multiplier || 100.0);
                self.xy_axis_movement_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.movement_speed,self.get_axis_speed_display_units(),profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                self.z_axis_movement_speed = ko.observable(
                    Octolapse.convertAxisSpeedUnit(
                        profile_observables.z_hop_speed,self.get_axis_speed_display_units(),profile_observables.axis_speed_display_units, self.get_speed_tolerance()));
                self.bridging_speed_multiplier = ko.observable(profile_observables.bridging_speed_multiplier || 100.0);

                /*
                    Create a getter for each profile variable (settings.py - printer class)
                */
                self.get_retract_length = function(){
                   return self.retraction_distance();
                };
                self.get_retract_speed = function(){
                   return self.retraction_retract_speed();
                };
                self.get_detract_speed = function(){
                   return self.retraction_retract_speed();
                };
                self.get_movement_speed = function(){
                   return self.xy_axis_movement_speed();
                };
                self.get_z_hop = function(){
                   return self.retraction_vertical_lift();
                };
                self.get_z_hop_speed = function(){
                    return self.z_axis_movement_speed();
                };
                self.get_print_speed = function(){
                    return self.default_printing_speed();
                };
                self.get_perimeter_speed = function(){
                    if(self.default_printing_speed()==null || self.outline_speed_multiplier() == null)
                        return null;
                    var perimeter_speed_multiplier = 100.0 - ((100 - self.outline_speed_multiplier())/2.0)
                    return Octolapse.roundToIncrement(self.default_printing_speed() * (perimeter_speed_multiplier / 100.0), self.get_speed_tolerance());
                };
                self.get_small_perimeter_speed = function(){
                    if(self.default_printing_speed()==null || self.outline_speed_multiplier() == null)
                        return null;
                    var perimeter_speed_multiplier = 100.0 - ((100 - self.outline_speed_multiplier())/2.0)
                    return Octolapse.roundToIncrement(self.default_printing_speed() * (perimeter_speed_multiplier / 100.0), self.get_speed_tolerance());
                };
                self.get_external_perimeter_speed = function(){
                    if(self.default_printing_speed()==null || self.outline_speed_multiplier() == null)
                        return null;
                    return Octolapse.roundToIncrement(self.default_printing_speed() * (self.outline_speed_multiplier() / 100.0), self.get_speed_tolerance());
                };
                self.get_infill_speed = function(){
                   return self.default_printing_speed();
                };
                self.get_solid_infill_speed = function(){
                    if(self.default_printing_speed()==null || self.solid_infill_speed_multiplier() == null)
                        return null;
                    return Octolapse.roundToIncrement(self.default_printing_speed() * (self.solid_infill_speed_multiplier() / 100.0), self.get_speed_tolerance());
                };
                self.get_top_solid_infill_speed = function(){
                   if(self.default_printing_speed()==null || self.solid_infill_speed_multiplier() == null)
                        return null;
                    return Octolapse.roundToIncrement(self.default_printing_speed() * (self.solid_infill_speed_multiplier() / 100.0), self.get_speed_tolerance());
                };
                self.get_support_speed = function(){
                    if(self.default_printing_speed()==null || self.support_structure_speed_multiplier() == null)
                        return null;
                    return Octolapse.roundToIncrement(self.default_printing_speed() * (self.support_structure_speed_multiplier() / 100.0), self.get_speed_tolerance());
                };
                self.get_bridge_speed = function(){
                    if(self.default_printing_speed()==null || self.bridging_speed_multiplier() == null)
                        return null;
                    return Octolapse.roundToIncrement(self.default_printing_speed() * (self.bridging_speed_multiplier() / 100.0), self.get_speed_tolerance());
                };
                self.get_gap_fill_speed = function(){
                   return self.default_printing_speed();
                };
                self.get_print_speed = function(){
                    return self.default_printing_speed();
                }
                self.get_first_layer_speed = function(){
                    if(self.default_printing_speed()==null || self.first_layer_speed_multiplier() == null)
                        return null;
                    return Octolapse.roundToIncrement(self.default_printing_speed() * (self.first_layer_speed_multiplier() / 100.0), self.get_speed_tolerance());
                };
                self.get_first_layer_travel_speed = function(){
                   return self.xy_axis_movement_speed();
                };
                self.get_skirt_brim_speed = function(){
                   return self.default_printing_speed();
                };
                self.get_first_layer_speed_multiplier = function(){
                   return self.first_layer_speed_multiplier();
                };
                self.get_above_raft_speed_multiplier = function(){
                   return self.above_raft_speed_multiplier();
                };
                self.get_prime_pillar_speed_multiplier = function(){
                   return self.prime_pillar_speed_multiplier();
                };
                self.get_ooze_shield_speed_multiplier = function(){
                   return self.ooze_shield_speed_multiplier();
                };
                self.get_outline_speed_multiplier = function(){
                   return self.outline_speed_multiplier();
                };
                self.get_solid_infill_speed_multiplier = function(){
                   return self.solid_infill_speed_multiplier();
                };
                self.get_support_structure_speed_multiplier = function(){
                   return self.support_structure_speed_multiplier();
                };
                self.get_bridging_speed_multiplier = function(){
                   return self.bridging_speed_multiplier();
                };

                self.get_above_raft_speed = function(){
                    if(self.default_printing_speed()==null || self.above_raft_speed_multiplier() == null)
                        return null;
                    return Octolapse.roundToIncrement(self.default_printing_speed() * (self.above_raft_speed_multiplier() / 100.0), self.get_speed_tolerance());
                };
                self.get_ooze_shield_speed = function(){
                    if(self.default_printing_speed()==null || self.ooze_shield_speed_multiplier() == null)
                        return null;
                    return Octolapse.roundToIncrement(self.default_printing_speed() * (self.ooze_shield_speed_multiplier() / 100.0), self.get_speed_tolerance());
                };
                self.get_prime_pillar_speed = function(){
                    if(self.default_printing_speed()==null || self.prime_pillar_speed_multiplier() == null)
                        return null;
                    return Octolapse.roundToIncrement(self.default_printing_speed() * (self.prime_pillar_speed_multiplier() / 100.0), self.get_speed_tolerance());
                };

                // Get a list of speeds for use with feature detection
                self.getSlicerSpeedList = function(){
                    return [
                        {speed: self.get_retract_speed(), type: "Retraction"},
                        {speed: self.get_first_layer_speed(), type: "First Layer"},
                        {speed: self.get_above_raft_speed(), type: "Above Raft"},
                        {speed: self.get_prime_pillar_speed(), type: "Prime Pillar"},
                        {speed: self.get_ooze_shield_speed(), type: "Ooze Shield"},
                        {speed: self.get_print_speed(), type: "Default Printing"},
                        {speed: self.get_external_perimeter_speed(), type: "Exterior Outlines"},
                        {speed: self.get_perimeter_speed(), type: "Interior Outlines"},
                        {speed: self.get_solid_infill_speed(), type: "Solid Infill"},
                        {speed: self.get_support_speed(), type: "Support Structure"},
                        {speed: self.get_movement_speed(), type: "X/Y Movement"},
                        {speed: self.get_z_hop_speed(), type: "Z Movement"},
                        {speed: self.get_bridge_speed(), type: "Bridging"},

                    ];
                };

            };
            self.simplify_3d_viewmodel = new self.create_simplify_3d_viewmodel(values);
        };
        self.helpers = new self.create_helpers(values);
        /*
            Create a computed for each profile variable (settings.py - printer class)
        */
        self.retract_length = ko.pureComputed(function(){
           return self.getCurrentSlicerVariables(self.slicer_type()).get_retract_length();
        });
        self.retract_speed = ko.pureComputed(function(){
           return self.getCurrentSlicerVariables(self.slicer_type()).get_retract_speed();
        });
        self.detract_speed = ko.pureComputed(function(){
           return self.getCurrentSlicerVariables(self.slicer_type()).get_detract_speed();
        });
        self.movement_speed = ko.pureComputed(function(){
           return self.getCurrentSlicerVariables(self.slicer_type()).get_movement_speed();
        });
        self.z_hop = ko.pureComputed(function(){
           return self.getCurrentSlicerVariables(self.slicer_type()).get_z_hop();
        });
        self.z_hop_speed = ko.pureComputed(function(){
           return self.getCurrentSlicerVariables(self.slicer_type()).get_z_hop_speed();
        });
        self.maximum_z_speed = ko.pureComputed(function(){
           var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_maximum_z_speed !== undefined)
                return slicer.get_maximum_z_speed();
            return null;
        });
        self.print_speed = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_print_speed !== undefined)
                return slicer.get_print_speed();
            return null;
        });
        self.perimeter_speed = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_perimeter_speed !== undefined)
                return slicer.get_perimeter_speed();
            return null;
        });
        self.small_perimeter_speed = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_small_perimeter_speed !== undefined)
                return slicer.get_small_perimeter_speed();
            return null;
        });
        self.external_perimeter_speed = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_external_perimeter_speed !== undefined)
                return slicer.get_external_perimeter_speed();
            return null;
        });
        self.infill_speed = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_infill_speed !== undefined)
                return slicer.get_infill_speed();
            return null;
        });
        self.solid_infill_speed = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_solid_infill_speed !== undefined)
                return slicer.get_solid_infill_speed();
            return null;
        });
        self.top_solid_infill_speed = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_top_solid_infill_speed !== undefined)
                return slicer.get_top_solid_infill_speed();
            return null;
        });
        self.support_speed = ko.pureComputed(function(){
           var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_support_speed !== undefined)
                return slicer.get_support_speed();
            return null;
        });
        self.bridge_speed = ko.pureComputed(function(){
           var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_bridge_speed !== undefined)
                return slicer.get_bridge_speed();
            return null;
        });
        self.gap_fill_speed = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_gap_fill_speed !== undefined)
                return slicer.get_gap_fill_speed();
            return null;
        });
        self.first_layer_speed = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_first_layer_speed !== undefined)
                return slicer.get_first_layer_speed();
            return null;
        });
        self.first_layer_travel_speed = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_first_layer_travel_speed !== undefined)
                return slicer.get_first_layer_travel_speed();
            return null;
        });
        self.skirt_brim_speed = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_skirt_brim_speed !== undefined)
                return slicer.get_skirt_brim_speed();
            return null;
        });
        self.above_raft_speed = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_above_raft_speed !== undefined)
                return slicer.get_above_raft_speed();
            return null;
        });
        self.ooze_shield_speed = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_ooze_shield_speed !== undefined)
                return slicer.get_ooze_shield_speed();
            return null;
        });
        self.prime_pillar_speed = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_prime_pillar_speed !== undefined)
                return slicer.get_prime_pillar_speed();
            return null;
        });

        self.speed_tolerance = ko.pureComputed(function(){
           return self.getCurrentSlicerVariables(self.slicer_type()).get_speed_tolerance();
        });
        self.axis_speed_display_units = ko.pureComputed(function(){
           return self.getCurrentSlicerVariables(self.slicer_type()).get_axis_speed_display_units();
        });
        self.first_layer_speed_multiplier = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_first_layer_speed_multiplier !== undefined)
                return slicer.get_first_layer_speed_multiplier();
            return null;
        });
        self.above_raft_speed_multiplier = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_above_raft_speed_multiplier !== undefined)
                return slicer.get_above_raft_speed_multiplier();
            return null;
        });
        self.prime_pillar_speed_multiplier = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_prime_pillar_speed_multiplier !== undefined)
                return slicer.get_prime_pillar_speed_multiplier();
            return null;
        });
        self.ooze_shield_speed_multiplier = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_ooze_shield_speed_multiplier !== undefined)
                return slicer.get_ooze_shield_speed_multiplier();
            return null;
        });
        self.outline_speed_multiplier = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_outline_speed_multiplier !== undefined)
                return slicer.get_outline_speed_multiplier();
            return null;
        });
        self.solid_infill_speed_multiplier = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_solid_infill_speed_multiplier !== undefined)
                return slicer.get_solid_infill_speed_multiplier();
            return null;
        });
        self.support_structure_speed_multiplier = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_support_structure_speed_multiplier !== undefined)
                return slicer.get_support_structure_speed_multiplier();
            return null;
        });
        self.bridging_speed_multiplier = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_bridging_speed_multiplier !== undefined)
                return slicer.get_bridging_speed_multiplier();
            return null;
        });

        self.slicer_speed_list = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.getSlicerSpeedList !== undefined)
                return slicer.getSlicerSpeedList();
            return [];
        });

        self.getNonUniqueSpeeds = ko.pureComputed(function () {
            // Add all speeds to an array
            var duplicate_map = {};
            var duplicates = {};

            var speed_array = self.slicer_speed_list();

            for (var index = 0, size = speed_array.length; index < size; index++) {
                var cur_speed = speed_array[index];
                if(!cur_speed.speed)
                    continue;
                if(duplicate_map[cur_speed.speed])
                    duplicate_map[cur_speed.speed].push(cur_speed.type);
                else
                    duplicate_map[cur_speed.speed] = [cur_speed.type];
            }
            var output = []
            for (var key in duplicate_map) {
                var dup_item = duplicate_map[key];
                var is_first = true;
                var num_items = dup_item.length
                if(num_items > 1) {
                    var cur_output_string = key.toString() + " " + self.axis_speed_display_units() + ": ";

                    for (var index = 0; index < num_items; index ++) {
                        if (!is_first)
                            cur_output_string += ", ";
                        cur_output_string += dup_item[index];
                        is_first = false;
                    }
                    cur_output_string += "";
                    output.push(cur_output_string);
                }
            }
            return output;
        });

        self.getMissingSpeedsList = ko.pureComputed(function () {
                    // Add all speeds to an array
            var missingSpeeds = [];

            var speed_array = self.slicer_speed_list();
            for (var index = 0, size = speed_array.length; index < size; index++) {
                var cur_speed = speed_array[index];
                if(!cur_speed.speed)
                    missingSpeeds.push(cur_speed.type);
            }

            return missingSpeeds;
        });

        self.getCurrentSlicerVariables = function() {
            switch(self.slicer_type())
            {
                case 'other':
                    return self.helpers.other_slicer_viewmodel;
                case 'slic3r-pe':
                    return self.helpers.slic3r_pe_viewmodel;
                case 'cura':
                    return self.helpers.cura_viewmodel;
                case 'simplify-3d':
                    return self.helpers.simplify_3d_viewmodel;
            }
        }

        self.toJS = function()
        {
            console.log("converting printer profile to js.");
            var copy = ko.toJS(self);
            delete copy.helpers;
            return copy;
        };

    };


});
