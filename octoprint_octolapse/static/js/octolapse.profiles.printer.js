/*
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
*/
$(function() {
    Octolapse.PrinterProfileValidationRules = {
        rules: {
            octolapse_printer_min_x: { lessThanOrEqual: "#octolapse_printer_max_x" },
            octolapse_printer_max_x: { greaterThanOrEqual: "#octolapse_printer_min_x"},
            octolapse_printer_min_y: { lessThanOrEqual: "#octolapse_printer_max_y" },
            octolapse_printer_max_y: { greaterThanOrEqual: "#octolapse_printer_min_y" },
            octolapse_printer_min_z: { lessThanOrEqual: "#octolapse_printer_max_z" },
            octolapse_printer_max_z: { greaterThanOrEqual: "#octolapse_printer_min_z" },
            octolapse_printer_snapshot_min_x: { lessThanOrEqual: "#octolapse_printer_snapshot_max_x" },
            octolapse_printer_snapshot_max_x: { greaterThanOrEqual: "#octolapse_printer_snapshot_min_x"},
            octolapse_printer_snapshot_min_y: { lessThanOrEqual: "#octolapse_printer_snapshot_max_y" },
            octolapse_printer_snapshot_max_y: { greaterThanOrEqual: "#octolapse_printer_snapshot_min_y" },
            octolapse_printer_snapshot_min_z: { lessThanOrEqual: "#octolapse_printer_snapshot_max_z" },
            octolapse_printer_snapshot_max_z: { greaterThanOrEqual: "#octolapse_printer_snapshot_min_z" },
            octolapse_printer_minimum_layer_height: { lessThanOrEqual: "#octolapse_printer_priming_height" },
            octolapse_printer_priming_height: { greaterThanOrEqual: "#octolapse_printer_minimum_layer_height" },
            octolapse_printer_auto_position_detection_commands: { csvString: true },
            octolapse_printer_snapshot_command: {octolapsePrinterSnapshotCommand: true},
            octolapse_other_slicer_retract_length: {required: true},
            octolapse_other_slicer_z_hop: {required: true},
            octolapse_other_slicer_vase_mode: {ifCheckedEnsureNonNull: ["#octolapse_other_slicer_layer_height"] },
            octolapse_other_slicer_layer_height: {ifOtherCheckedEnsureNonNull: '#octolapse_other_slicer_vase_mode'},
            octolapse_cura_smooth_spiralized_contours: {ifCheckedEnsureNonNull: ["#octolapse_cura_layer_height"] },
            octolapse_cura_layer_height: {ifOtherCheckedEnsureNonNull: '#octolapse_cura_smooth_spiralized_contours'},
            octolapse_cura_4_2_smooth_spiralized_contours: {ifCheckedEnsureNonNull: ["#octolapse_cura_4_2_layer_height"] },
            octolapse_cura_4_2_layer_height: {ifOtherCheckedEnsureNonNull: '#octolapse_cura_4_2_smooth_spiralized_contours'},
            octolapse_simplify_3d_vase_mode: {ifCheckedEnsureNonNull: ["#octolapse_simplify_3d_layer_height"] },
            octolapse_simplify_3d_layer_height: {ifOtherCheckedEnsureNonNull: '#octolapse_simplify_3d_vase_mode'},
            octolapse_slic3r_pe_spiral_vase: {ifCheckedEnsureNonNull: ["#octolapse_slic3r_pe_layer_height"] },
            octolapse_slic3r_pe_layer_height: {ifOtherCheckedEnsureNonNull: '#octolapse_slic3r_pe_spiral_vase'}

        },
        messages: {
            octolapse_printer_name: "Please enter a name for your profile",
            octolapse_printer_min_x : { lessThanOrEqual: "Must be less than or equal to the 'X - Width Max' field." },
            octolapse_printer_max_x : { greaterThanOrEqual: "Must be greater than or equal to the ''X - Width Min'' field." },
            octolapse_printer_min_y : { lessThanOrEqual: "Must be less than or equal to the 'Y - Width Max' field." },
            octolapse_printer_max_y : { greaterThanOrEqual: "Must be greater than or equal to the ''Y - Width Min'' field." },
            octolapse_printer_min_z : { lessThanOrEqual: "Must be less than or equal to the 'Z - Width Max' field." },
            octolapse_printer_max_z: { greaterThanOrEqual: "Must be greater than or equal to the ''Z - Width Min'' field." },
            octolapse_printer_snapshot_min_x : { lessThanOrEqual: "Must be less than or equal to the ''Snapshot Max X'' field." },
            octolapse_printer_snapshot_max_x : { greaterThanOrEqual: "Must be greater than or equal to the ''Snapshot Min X'' field." },
            octolapse_printer_snapshot_min_y : { lessThanOrEqual: "Must be less than or equal to the 'Snapshot Max Y' field." },
            octolapse_printer_snapshot_max_y : { greaterThanOrEqual: "Must be greater than or equal to the ''Snapshot Min Y'' field." },
            octolapse_printer_snapshot_min_z : { lessThanOrEqual: "Must be less than or equal to the 'Snapshot Max Z' field." },
            octolapse_printer_snapshot_max_z: { greaterThanOrEqual: "Must be greater than or equal to the ''Snapshot Min Z'' field." },
            octolapse_printer_minimum_layer_height: { lessThanOrEqual: "Must be less than or equal to the ''Priming Height'' field." },
            octolapse_printer_priming_height: { greaterThanOrEqual: "Must be greater than or equal to the ''Minimum Layer Height'' field." },
            octolapse_printer_auto_position_detection_commands: { csvString:"Please enter a series of gcode commands (without parameters) separated by commas, or leave this field blank." },
            octolapse_cura_smooth_spiralized_contours: {ifCheckedEnsureNonNull: "If vase mode is selected, you must enter a layer height."},
            octolapse_cura_layer_height: {ifOtherCheckedEnsureNonNull: 'Vase mode is selected, you must enter a layer height.'},
            octolapse_cura_4_2_smooth_spiralized_contours: {ifCheckedEnsureNonNull: "If vase mode is selected, you must enter a layer height."},
            octolapse_cura_4_2_layer_height: {ifOtherCheckedEnsureNonNull: 'Vase mode is selected, you must enter a layer height.'},
            octolapse_other_slicer_vase_mode: {ifCheckedEnsureNonNull: "If vase mode is selected, you must enter a layer height."},
            octolapse_other_slicer_layer_height: {ifOtherCheckedEnsureNonNull: 'Vase mode is selected, you must enter a layer height.'},
            octolapse_simplify_3d_vase_mode: {ifCheckedEnsureNonNull: "If vase mode is selected, you must enter a layer height."},
            octolapse_simplify_3d_layer_height: {ifOtherCheckedEnsureNonNull: 'Vase mode is selected, you must enter a layer height.'},
            octolapse_slic3r_pe_vase_mode: {ifCheckedEnsureNonNull: "If vase mode is selected, you must enter a layer height."},
            octolapse_slic3r_pe_layer_height: {ifOtherCheckedEnsureNonNull: 'Vase mode is selected, you must enter a layer height.'}
        }
    };

    Octolapse.ExtruderOffset = function(values)
    {
        var self = this;
        self.x = ko.observable(0);
        self.y = ko.observable(0);
        if (values)
        {
            self.x(values.x);
            self.y(values.y);
        }
    };

    Octolapse.Slicers = function(values, num_extruders_observable) {
        //console.log("Creating Slicers");
        var self = this;
        self.cura = new Octolapse.CuraViewmodel(values.cura, num_extruders_observable);
        self.other = new Octolapse.OtherSlicerViewModel(values.other, num_extruders_observable);
        self.simplify_3d = new Octolapse.Simplify3dViewModel(values.simplify_3d, num_extruders_observable);
        self.slic3r_pe = new Octolapse.Slic3rPeViewModel(values.slic3r_pe, num_extruders_observable);

    };

    Octolapse.PrinterProfileViewModel = function (values) {
        var self = this;
        self.profileTypeName = ko.observable("Printer");
        self.guid = ko.observable(values.guid);
        self.name = ko.observable(values.name);
        self.description = ko.observable(values.description);
        self.num_extruders = ko.observable(values.num_extruders);
        self.shared_extruder = ko.observable(values.shared_extruder);
        self.extruder_offsets = ko.observableArray([]);
        for(var index = 0; index < values.extruder_offsets.length; index++)
        {
            var offset = new Octolapse.ExtruderOffset(values.extruder_offsets[index]);
            self.extruder_offsets.push(offset);
        }
        self.default_extruder = ko.observable(values.default_extruder);
        self.zero_based_extruder = ko.observable(values.zero_based_extruder);
        self.slicers = new Octolapse.Slicers(values.slicers, self.num_extruders);
        // has_been_saved_by_user profile setting, computed and always returns true
        // This will switch has_been_saved_by_user from false to true
        // after any user save
        self.has_been_saved_by_user = ko.observable(true);
        self.slicer_type = ko.observable(values.slicer_type);
        self.snapshot_command = ko.observable(values.snapshot_command);
        self.auto_detect_position = ko.observable(values.auto_detect_position);
        self.auto_position_detection_commands = ko.observable(values.auto_position_detection_commands);
        self.origin_type = ko.observable(values.origin_type);
        self.home_x = ko.observable(values.home_x);
        self.home_y = ko.observable(values.home_y);
        self.home_z = ko.observable(values.home_z);
        self.override_octoprint_profile_settings = ko.observable(values.override_octoprint_profile_settings);
        self.bed_type = ko.observable(values.bed_type);
        self.diameter_xy = ko.observable(values.diameter_xy);

        self.width = ko.observable(values.width);
        self.depth= ko.observable(values.depth);
        self.height = ko.observable(values.height);
        self.custom_bounding_box = ko.observable(values.custom_bounding_box);

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

        self.dialog = null;

        self.num_extruders.subscribe(function() {
            var num_extruders = self.num_extruders();
            if (num_extruders < 1) {
                num_extruders = 1;
            }
            else if (num_extruders > 16){
                num_extruders = 16;
            }

            var has_changed = false;
            while(self.extruder_offsets().length < num_extruders)
            {
                has_changed = true;
                self.extruder_offsets.push(new Octolapse.ExtruderOffset());
            }
            while(self.extruder_offsets().length > num_extruders)
            {
                has_changed = true;
                self.extruder_offsets.pop();
            }
            if (has_changed) {
                self.dialog.bind_validation();
                self.dialog.bind_help_links();
            }
        });

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
            self.num_extruders(server_profile.num_extruders);
            self.shared_extruder(server_profile.shared_extruder);
            self.extruder_offsets(server_profile.extruder_offsets);
            self.zero_based_extruder(server_profile.zero_based_extruder);
            self.snapshot_command(server_profile.snapshot_command);
            self.auto_detect_position(server_profile.auto_detect_position);
            self.auto_position_detection_commands(server_profile.auto_position_detection_commands);
            self.origin_type(server_profile.origin_type);
            self.home_x(server_profile.home_x);
            self.home_y(server_profile.home_y);
            self.home_z(server_profile.home_z);
            self.override_octoprint_profile_settings(server_profile.override_octoprint_profile_settings);
            self.bed_type(server_profile.bed_type);
            self.diameter_xy(server_profile.diameter_xy);
            self.width(server_profile.width);
            self.depth(server_profile.depth);
            self.height(server_profile.height);
            self.custom_bounding_box(server_profile.custom_bounding_box);
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

        self.on_opened = function(dialog)
        {
            self.dialog = dialog;
        };
        self.on_closed = function()
        {
            self.automatic_configuration.on_closed();
        };

        self.toJS = function()
        {
            var dialog = self.dialog;
            self.dialog = null;
            var copy = ko.toJS(self);
            self.dialog = dialog;
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
