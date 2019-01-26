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
            minimum_layer_height: { lessThanOrEqual: "#printer_profile_priming_height" },
            priming_height: { greaterThanOrEqual: "#printer_profile_minimum_layer_height" },
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
            minimum_layer_height: { lessThanOrEqual: "Must be less than or equal to the ''Priming Height'' field." },
            priming_height: { greaterThanOrEqual: "Must be greater than or equal to the ''Minimum Layer Height'' field." },
            auto_position_detection_commands: { csvString:"Please enter a series of gcode commands (without parameters) separated by commas, or leave this field blank." }
        }
    };
    Octolapse.OctolapseGcodeSettings = function(values)
    {
        var self = this;
        self.retraction_length = ko.observable(values.retraction_length);
        self.retraction_speed = ko.observable(values.retraction_speed);
        self.deretraction_speed = ko.observable(values.deretraction_speed);
        self.x_y_travel_speed = ko.observable(values.x_y_travel_speed);
        self.first_layer_travel_speed = ko.observable(values.first_layer_travel_speed);
        self.z_lift_height = ko.observable(values.z_lift_height);
        self.z_lift_speed = ko.observable(values.z_lift_speed);
    };

    Octolapse.AutomaticSlicerViewModel = function(values)
    {
        var self = this;
        self.continue_on_failure = ko.observable(values.continue_on_failure);
        self.disable_automatic_save = ko.observable(values.disable_automatic_save);
    };

    Octolapse.Slicers = function(values)
    {
        //console.log("Creating Slicers");
        var self = this;
        self.automatic = new Octolapse.AutomaticSlicerViewModel(values.automatic);
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
        // Saved by user flag, sent from server
        self.saved_by_user_flag = ko.observable(values.has_been_saved_by_user);
        self.gcode_generation_settings = new Octolapse.OctolapseGcodeSettings(values.gcode_generation_settings);
        self.slicers = new Octolapse.Slicers(values.slicers);
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
        self.minimum_layer_height = ko.observable(values.minimum_layer_height);
        self.e_axis_default_mode = ko.observable(values.e_axis_default_mode);
        self.g90_influences_extruder = ko.observable(values.g90_influences_extruder);
        self.xyz_axes_default_mode = ko.observable(values.xyz_axes_default_mode);
        self.units_default = ko.observable(values.units_default);
        self.axis_speed_display_units = ko.observable(values.axis_speed_display_units);
        self.default_firmware_retractions = ko.observable(values.default_firmware_retractions);
        self.default_firmware_retractions_zhop = ko.observable(values.default_firmware_retractions_zhop);
        self.suppress_snapshot_command_always = ko.observable(values.suppress_snapshot_command_always);
        self.nonUniqueSpeedList = ko.observable([]);
        self.missingSpeedsList = ko.observable([]);
        self.printFeaturesList = ko.observable([]);

        self.dialog = null;
        self.isValid = function(){
            if (self.dialog != null)
                return self.dialog.IsValid();
            return false;
        }
        self.onShow = function(parent) {
            // Get a reference to the parent dialog.
            self.dialog = parent;
        };
        self.getPrinterFeatures = function () {
            //console.log("getting feature list");
            if (!self.isValid())
                return;
            var data = null;
            switch(self.slicer_type())
            {
                case 'cura':
                    data = ko.toJS(self.slicers.cura);
                    break;
                case 'other':
                    data = ko.toJS(self.slicers.other);
                    break;
                case 'simplify-3d':
                    data = ko.toJS(self.slicers.simplify_3d);
                    break;
                case 'slic3r-pe':
                    data = ko.toJS(self.slicers.slic3r_pe);
                    break;
            }
            if (data != null)
            {
                $.ajax({
                    url: "./plugin/octolapse/getPrintFeatures",
                    type: "POST",
                    tryCount: 0,
                    retryLimit: 3,
                    contentType: "application/json",
                    data: JSON.stringify({
                            'slicer_settings': data,
                            'slicer_type': self.slicer_type()
                        }
                    ),
                    dataType: "json",
                    success: function (result) {
                        //console.log("print features received");
                        //console.log(result);
                        self.nonUniqueSpeedList(result['non-unique-speeds']);
                        self.missingSpeedsList(result['missing-speeds']);
                        self.printFeaturesList(result['all-features']);
                    },
                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                        return false;
                    }
                });
            }
        };

        self.subscribeToFeatureChanges = function(observables)
        {
            //console.log("subscribing slicer settings to getPrinterFeatures");
            for (var i = 0; i < observables.length; i++) {

                observables[i].subscribe(self.getPrinterFeatures);
            }
        };

        self.slicer_type.subscribe(self.getPrinterFeatures);
        self.subscribeToFeatureChanges(self.slicers.cura.get_all_speed_settings());
        self.subscribeToFeatureChanges(self.slicers.other.get_all_speed_settings());
        self.subscribeToFeatureChanges(self.slicers.simplify_3d.get_all_speed_settings());
        self.subscribeToFeatureChanges(self.slicers.slic3r_pe.get_all_speed_settings());
        // Trigger a change of the slicer error messages
       self.getPrinterFeatures();


        self.toJS = function()
        {
            var copy = ko.toJS(self);
            delete copy.helpers;
            return copy;
        };

    };


});
