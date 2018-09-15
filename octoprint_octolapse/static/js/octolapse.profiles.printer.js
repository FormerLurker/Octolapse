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
            slicer_slic3r_pe_small_perimeter_speed: {slic3rPEFloatOrPercent: true, slic3rPEFloatOrPercentSteps: true},
            slicer_slic3r_pe_external_perimeter_speed: {slic3rPEFloatOrPercent: true, slic3rPEFloatOrPercentSteps: true},
            slicer_slic3r_pe_solid_infill_speed: {slic3rPEFloatOrPercent: true, slic3rPEFloatOrPercentSteps: true},
            slicer_slic3r_pe_top_solid_infill_speed: {slic3rPEFloatOrPercent: true, slic3rPEFloatOrPercentSteps: true},
            slicer_slic3r_pe_first_layer_speed: {slic3rPEFloatOrPercent: true, slic3rPEFloatOrPercentSteps: true}
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
        // Saved by user flag, sent from server
        self.saved_by_user_flag = ko.observable(values.has_been_saved_by_user);
        // has_been_saved_by_user profile setting, computed and always returns true
        // This will switch has_been_saved_by_user from false to true
        // after any user save
        self.has_been_saved_by_user = ko.observable(true);
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
            self.other_slicer_viewmodel = new Octolapse.create_other_slicer_viewmodel(values);
            self.slic3r_pe_viewmodel = new Octolapse.create_slic3r_pe_viewmodel(values);
            self.cura_viewmodel = new Octolapse.create_cura_viewmodel(values);
            self.simplify_3d_viewmodel = new Octolapse.create_simplify_3d_viewmodel(values);
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
        self.small_perimeter_speed_multiplier = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_small_perimeter_speed_multiplier !== undefined)
                return slicer.get_small_perimeter_speed_multiplier();
            return null;
        });
        self.external_perimeter_speed_multiplier = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_external_perimeter_speed_multiplier !== undefined)
                return slicer.get_external_perimeter_speed_multiplier();
            return null;
        });
        self.top_solid_infill_speed_multiplier = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_top_solid_infill_speed_multiplier !== undefined)
                return slicer.get_top_solid_infill_speed_multiplier();
            return null;
        });
        self.small_perimeter_speed_text = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_small_perimeter_speed_text !== undefined)
                return slicer.get_small_perimeter_speed_text();
            return null;
        });
        self.external_perimeter_speed_text = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_external_perimeter_speed_text !== undefined)
                return slicer.get_external_perimeter_speed_text();
            return null;
        });
        self.solid_infill_speed_text = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_solid_infill_speed_text !== undefined)
                return slicer.get_solid_infill_speed_text();
            return null;
        });
        self.top_solid_infill_speed_text = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_top_solid_infill_speed_text !== undefined)
                return slicer.get_top_solid_infill_speed_text();
            return null;
        });
        self.first_layer_speed_text = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_first_layer_speed_text !== undefined)
                return slicer.get_first_layer_speed_text();
            return null;
        });
        self.slicer_speed_list = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.getSlicerSpeedList !== undefined)
                return slicer.getSlicerSpeedList();
            return [];
        });
        self.num_slow_layers = ko.pureComputed(function(){
            var slicer = self.getCurrentSlicerVariables(self.slicer_type());
            if (slicer.get_num_slow_layers !== undefined)
                return slicer.get_num_slow_layers();
            return null;
        });
        self.getNonUniqueSpeeds = ko.pureComputed(function () {
            // Add all speeds to an array
            var duplicate_map = {};

            var speed_array = self.slicer_speed_list();

            for (var index = 0, size = speed_array.length; index < size; index++) {
                var cur_speed = speed_array[index];
                if(cur_speed.speed != 0 && !cur_speed.speed)
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
                    if(key == 0)
                        key = "(previous axis speed) 0 ";
                    var cur_output_string = key.toString() + " mm-min: ";

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
                if(cur_speed.speed != 0 && !cur_speed.speed)
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
            var copy = ko.toJS(self);
            delete copy.helpers;
            return copy;
        };

    };


});
