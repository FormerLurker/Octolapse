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
            snapshot_min_x: { lessThanOrEqual: "#octolapse_printer_snapshot_max_x" },
            snapshot_max_x: { greaterThanOrEqual: "#octolapse_printer_snapshot_min_x"},
            snapshot_min_y: { lessThanOrEqual: "#octolapse_printer_snapshot_max_y" },
            snapshot_max_y: { greaterThanOrEqual: "#octolapse_printer_snapshot_min_y" },
            snapshot_min_z: { lessThanOrEqual: "#octolapse_printer_snapshot_max_z" },
            snapshot_max_z: { greaterThanOrEqual: "#octolapse_printer_snapshot_min_z" },
            minimum_layer_height: { lessThanOrEqual: "#printer_profile_priming_height" },
            priming_height: { greaterThanOrEqual: "#printer_profile_minimum_layer_height" },
            auto_position_detection_commands: { csvString: true },
            printer_profile_other_slicer_retract_length: {required: true},
            printer_profile_slicer_other_z_hop: {required: true},
            slicer_cura_smooth_spiralized_contours: {ifCheckedEnsureNonNull: ["#slicer_cura_layer_height"] },
            slicer_other_vase_mode: {ifCheckedEnsureNonNull: ["#slicer_other_slicer_layer_height"] },
            slicer_simplify_3d_vase_mode: {ifCheckedEnsureNonNull: ["#slicer_simplify_3d_layer_height"] },
            slicer_slic3r_pe_vase_mode: {ifCheckedEnsureNonNull: ["#slicer_slic3r_pe_layer_height"] },
            slicer_cura_layer_height: {ifOtherCheckedEnsureNonNull: '#slicer_cura_smooth_spiralized_contours'},
            slicer_other_slicer_layer_height: {ifOtherCheckedEnsureNonNull: '#slicer_other_vase_mode'},
            slicer_simplify_3d_layer_height: {ifOtherCheckedEnsureNonNull: '#slicer_simplify_3d_vase_mode'},
            slicer_slic3r_pe_layer_height: {ifOtherCheckedEnsureNonNull: '#slicer_slic3r_pe_vase_mode'}

        },
        messages: {
            name: "Please enter a name for your profile",
            min_x : { lessThanOrEqual: "Must be less than or equal to the 'X - Width Max' field." },
            max_x : { greaterThanOrEqual: "Must be greater than or equal to the ''X - Width Min'' field." },
            min_y : { lessThanOrEqual: "Must be less than or equal to the 'Y - Width Max' field." },
            max_y : { greaterThanOrEqual: "Must be greater than or equal to the ''Y - Width Min'' field." },
            min_z : { lessThanOrEqual: "Must be less than or equal to the 'Z - Width Max' field." },
            max_z: { greaterThanOrEqual: "Must be greater than or equal to the ''Z - Width Min'' field." },
            snapshot_min_x : { lessThanOrEqual: "Must be less than or equal to the ''Snapshot Max X'' field." },
            snapshot_max_x : { greaterThanOrEqual: "Must be greater than or equal to the ''Snapshot Min X'' field." },
            snapshot_min_y : { lessThanOrEqual: "Must be less than or equal to the 'Snapshot Max Y' field." },
            snapshot_max_y : { greaterThanOrEqual: "Must be greater than or equal to the ''Snapshot Min Y'' field." },
            snapshot_min_z : { lessThanOrEqual: "Must be less than or equal to the 'Snapshot Max Z' field." },
            snapshot_max_z: { greaterThanOrEqual: "Must be greater than or equal to the ''Snapshot Min Z'' field." },
            minimum_layer_height: { lessThanOrEqual: "Must be less than or equal to the ''Priming Height'' field." },
            priming_height: { greaterThanOrEqual: "Must be greater than or equal to the ''Minimum Layer Height'' field." },
            auto_position_detection_commands: { csvString:"Please enter a series of gcode commands (without parameters) separated by commas, or leave this field blank." },
            slicer_cura_smooth_spiralized_contours: {ifCheckedEnsureNonNull: "If vase mode is selected, you must enter a layer height."},
            slicer_other_vase_mode: {ifCheckedEnsureNonNull: "If vase mode is selected, you must enter a layer height."},
            slicer_simplify_3d_vase_mode: {ifCheckedEnsureNonNull: "If vase mode is selected, you must enter a layer height."},
            slicer_slic3r_pe_vase_mode: {ifCheckedEnsureNonNull: "If vase mode is selected, you must enter a layer height."},
            slicer_cura_layer_height: {ifOtherCheckedEnsureNonNull: 'Vase mode is selected, you must enter a layer height.'},
            slicer_other_slicer_layer_height: {ifOtherCheckedEnsureNonNull: 'Vase mode is selected, you must enter a layer height.'},
            slicer_simplify_3d_layer_height: {ifOtherCheckedEnsureNonNull: 'Vase mode is selected, you must enter a layer height.'},
            slicer_slic3r_pe_layer_height: {ifOtherCheckedEnsureNonNull: 'Vase mode is selected, you must enter a layer height.'}
        }
    };

    Octolapse.OctolapseGcodeSettings = function(values){
        var self = this;
        self.retraction_length = ko.observable(values.retraction_length);
        self.retraction_speed = ko.observable(values.retraction_speed);
        self.deretraction_speed = ko.observable(values.deretraction_speed);
        self.x_y_travel_speed = ko.observable(values.x_y_travel_speed);
        self.z_lift_height = ko.observable(values.z_lift_height);
        self.z_lift_speed = ko.observable(values.z_lift_speed);
    };

    Octolapse.Slicers = function(values) {
        //console.log("Creating Slicers");
        var self = this;
        self.cura = new Octolapse.CuraViewmodel(values.cura);
        self.other = new Octolapse.OtherSlicerViewModel(values.other);
        self.simplify_3d = new Octolapse.Simplify3dViewModel(values.simplify_3d);
        self.slic3r_pe = new Octolapse.Slic3rPeViewModel(values.slic3r_pe);
    };

    Octolapse.PrinterProfileViewModel = function (values) {
        var self = this;
        self.profileTypeName = ko.observable("Printer");
        self.guid = ko.observable(values.guid);
        self.name = ko.observable(values.name);
        self.description = ko.observable(values.description);
        /*
        self.automatic_configuration = new Octolapse.AutomaticPrinterConfigurationViewModel(
            values.automatic_configuration, self
        );
        */

        self.gcode_generation_settings = new Octolapse.OctolapseGcodeSettings(values.gcode_generation_settings);
        self.slicers = new Octolapse.Slicers(values.slicers);
        // has_been_saved_by_user profile setting, computed and always returns true
        // This will switch has_been_saved_by_user from false to true
        // after any user save
        self.has_been_saved_by_user = ko.observable(values.has_been_saved_by_user);
        self.slicer_type = ko.observable(values.slicer_type);
        self.snapshot_command = ko.observable(values.snapshot_command);
        self.auto_detect_position = ko.observable(values.auto_detect_position);
        self.auto_position_detection_commands = ko.observable(values.auto_position_detection_commands);
        self.origin_type = ko.observable(values.origin_type);
        self.origin_x = ko.observable(values.origin_x);
        self.origin_y = ko.observable(values.origin_y);
        self.origin_z = ko.observable(values.origin_z);
        self.abort_out_of_bounds = ko.observable(values.abort_out_of_bounds);
        self.override_octoprint_profile_settings = ko.observable(values.override_octoprint_profile_settings);
        self.bed_type = ko.observable(values.bed_type);
        self.diameter_xy = ko.observable(values.diameter_xy);
        self.min_x = ko.observable(values.min_x);
        self.max_x = ko.observable(values.max_x);
        self.min_y = ko.observable(values.min_y);
        self.max_y = ko.observable(values.max_y);
        self.min_z = ko.observable(values.min_z);
        self.max_z = ko.observable(values.max_z);
        self.restrict_snapshot_area = ko.observable(values.restrict_snapshot_area);
        self.snapshot_diameter_xy = ko.observable(values.snapshot_diameter_xy);
        self.snapshot_min_x = ko.observable(values.snapshot_min_x);
        self.snapshot_max_x = ko.observable(values.snapshot_max_x);
        self.snapshot_min_y = ko.observable(values.snapshot_min_y);
        self.snapshot_max_y = ko.observable(values.snapshot_max_y);
        self.snapshot_min_z = ko.observable(values.snapshot_min_z);
        self.snapshot_max_z = ko.observable(values.snapshot_max_z);
        self.priming_height = ko.observable(values.priming_height);
        self.minimum_layer_height = ko.observable(values.minimum_layer_height);
        self.e_axis_default_mode = ko.observable(values.e_axis_default_mode);
        self.g90_influences_extruder = ko.observable(values.g90_influences_extruder);
        self.xyz_axes_default_mode = ko.observable(values.xyz_axes_default_mode);
        self.units_default = ko.observable(values.units_default);
        self.axis_speed_display_units = ko.observable(values.axis_speed_display_units);
        self.default_firmware_retractions = ko.observable(values.default_firmware_retractions);
        self.default_firmware_retractions_zhop = ko.observable(values.default_firmware_retractions_zhop);
        self.suppress_snapshot_command_always = ko.observable(values.suppress_snapshot_command_always);
        self.gocde_axis_compatibility_mode_enabled = ko.observable(values.gocde_axis_compatibility_mode_enabled);
        self.home_axis_gcode = ko.observable(values.home_axis_gcode);

        self.origin_type_options = ko.pureComputed(function(){
            var options = [];
            if (self.bed_type() == 'circular')
            {
               for (var index in Octolapse.Printers.profileOptions.origin_type_options)
               {
                   var option = Octolapse.Printers.profileOptions.origin_type_options[index];
                   if (option.value == 'center')
                   {
                       options.push(option);
                   }
               }
            }
            else
            {
                options = Octolapse.Printers.profileOptions.origin_type_options;
            }
           return Octolapse.nameSort(options);
        });
        // Update the current profile from server profile values
        self.updateFromServer = function(server_profile){
            self.name(server_profile.name);
            self.description(server_profile.description);
            self.has_been_saved_by_user(true);
            self.snapshot_command(server_profile.snapshot_command);
            self.auto_detect_position(server_profile.auto_detect_position);
            self.auto_position_detection_commands(server_profile.auto_position_detection_commands);
            self.origin_type(server_profile.origin_type);
            self.origin_x(server_profile.origin_x);
            self.origin_y(server_profile.origin_y);
            self.origin_z(server_profile.origin_z);
            self.abort_out_of_bounds(server_profile.abort_out_of_bounds);
            self.override_octoprint_profile_settings(server_profile.override_octoprint_profile_settings);
            self.bed_type(server_profile.bed_type);
            self.diameter_xy(server_profile.diameter_xy);
            self.min_x(server_profile.min_x);
            self.max_x(server_profile.max_x);
            self.min_y(server_profile.min_y);
            self.max_y(server_profile.max_y);
            self.min_z(server_profile.min_z);
            self.max_z(server_profile.max_z);
            self.restrict_snapshot_area(server_profile.restrict_snapshot_area);
            self.snapshot_diameter_xy(server_profile.snapshot_diameter_xy);
            self.snapshot_min_x(server_profile.snapshot_min_x);
            self.snapshot_max_x(server_profile.snapshot_max_x);
            self.snapshot_min_y(server_profile.snapshot_min_y);
            self.snapshot_max_y(server_profile.snapshot_max_y);
            self.snapshot_min_z(server_profile.snapshot_min_z);
            self.snapshot_max_z(server_profile.snapshot_max_z);
            self.priming_height(server_profile.priming_height);
            self.minimum_layer_height(server_profile.minimum_layer_height);
            self.e_axis_default_mode(server_profile.e_axis_default_mode);
            self.g90_influences_extruder(server_profile.g90_influences_extruder);
            self.xyz_axes_default_mode(server_profile.xyz_axes_default_mode);
            self.units_default(server_profile.units_default);
            self.axis_speed_display_units(server_profile.axis_speed_display_units);
            self.default_firmware_retractions(server_profile.default_firmware_retractions);
            self.default_firmware_retractions_zhop(server_profile.default_firmware_retractions_zhop);
            self.suppress_snapshot_command_always(server_profile.suppress_snapshot_command_always);
            self.gocde_axis_compatibility_mode_enabled(server_profile.gocde_axis_compatibility_mode_enabled);
            self.home_axis_gcode(server_profile.home_axis_gcode);
        };

        self.on_closed = function()
        {
            self.automatic_configuration.on_closed();
        };

        self.toJS = function()
        {
            // need to remove the parent link from the automatic configuration to prevent a cyclic copy
            var copy = ko.toJS(self);
            delete copy.helpers;
            return copy;

        };

        self.automatic_configuration = new Octolapse.ProfileLibraryViewModel(
            values.automatic_configuration,
            Octolapse.Printers.profileOptions.server_profiles,
            self.profileTypeName(),
            self,
            self.updateFromServer
        );

        self.automatic_configuration.is_confirming.subscribe(function(value){
            //console.log("IsClickable" + value.toString());
            Octolapse.Printers.setIsClickable(!value);
        });

    };


});
