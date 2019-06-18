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

    Octolapse.AutomaticPrinterConfigurationViewModel = function(values, parent) {
        var self = this;
        self.parent = parent;
        self.make = ko.observable(values.make);
        self.model = ko.observable(values.model);
        self.version = ko.observable(values.version);
        self.suppress_update_notification_version = ko.observable(values.suppress_update_notification_version);
        self.make = ko.observable(values.make);
        self.original_make = values.make;
        self.other_make = ko.observable(values.other_make);
        self.ignore_is_custom_change = false;
        self.ignore_model_changes = false;
        self.ignore_make_changes = false;
        // tracks if the is_custom value triggered a server profile update
        self.is_custom_triggered_update = false;
        self.original_model = values.model;
        self.is_custom = ko.observable(values.is_custom);
        self.old_is_custom = null;
        self.automatic_changed_to_custom = ko.observable(false);
        self.model = ko.observable(values.model).extend({
            confirmable: {
                key: 'confirm-load-server-profile',
                message: 'This will overwrite your current settings.  Are you sure?',
                title: 'Update Profile From Server',
                on_before_confirm: function(newValue, oldValue)
                {
                    // Record our previous custom value in case we need to revert to the previous value
                    self.old_is_custom = self.is_custom();
                    // no need to save the old key, it will be provided in later callbacks
                },
                ignore: function(newValue, oldValue) {
                    // ignore the popup if we are ignoring key changes
                    return self.ignore_model_changes || !newValue || newValue == 'custom';
                },
                auto_confirm: function(newValue, oldValue)
                {
                    return !self.is_custom() && oldValue && oldValue != 'custom' && newValue && newValue != 'custom';
                },
                on_confirmed: function(newValue, oldValue) {
                    // We've updated from the server, we are no longer custom!
                    self.ignore_is_custom_change = true;
                    self.is_custom(false);
                    self.ignore_is_custom_change = false;
                },
                on_cancel: function(newValue, oldValue)
                {
                    // Revert the key and is_custom setting to their previous value
                    // No other changes will have been made to the profile at this point
                    if(newValue) {
                        self.ignore_model_changes = true;
                        self.model(self.original_model);
                        self.ignore_model_changes = false;
                        self.ignore_is_custom_change = true;
                        self.is_custom(self.old_is_custom);
                        self.ignore_is_custom_change = false;
                    }
                },
                on_complete: function(newValue, oldValue, wasConfirmed)
                {
                    // we don't want to do anything if we're ignoring key changes
                    if (self.ignore_model_changes)
                        return;

                    // only update the profile if the new value is not null or custom
                    var should_update_profile = wasConfirmed && (newValue && newValue !== 'custom');

                    if(should_update_profile) {
                        self.updateProfileFromLibrary({
                            on_failed: function () {
                                self.ignore_is_custom_change = true;
                                self.is_custom(old_is_custom);
                                self.ignore_is_custom_change = false;
                                self.ignore_model_changes = true;
                                self.make(oldValue);
                                self.ignore_model_changes = false;
                                // We need to mark this in case of failure, else is_custom might not revert properly
                                self.is_custom_triggered_update = false;
                            }
                        });
                    }
                }
            }
        });

        self.other_model = ko.observable(values.other_model);

        self.is_custom.subscribe(function(newValue){
            if (self.ignore_is_custom_change)
                return;

            // If we've switched from an automatically configured profile to a custom profile, display this
            // temporarily to inform the user.
            if (newValue) {
                if (self.model && self.model() != 'custom')
                    self.automatic_changed_to_custom(true);
                else
                    self.automatic_changed_to_custom(false);
            }
            else {
                // If we've disabled the custom profile setting, update the profile from the server.
                if (self.make() && self.make() != 'custom' && self.model() && self.model() != 'custom')
                {
                    // normally model changes trigger server updates, but this is a special
                    // case.  If the user has a non custom make and model selected,
                    // switching is_custom off should trigger a server update
                    // track is by setting self.is_custom_triggered_update = true;
                    self.ignore_is_custom_change=true;
                    self.is_custom(true);
                    self.ignore_is_custom_change=false;
                    self.is_custom_triggered_update = true;
                    var current_model = self.model();
                    self.ignore_model_changes = true;
                    self.model(null);
                    self.ignore_model_changes = false;
                    self.model(current_model);
                }
            }
        });

        self.make.subscribe(function(newValue) {
            console.log("Make changed");
            // Clear the model
            if(newValue==='custom') {
                self.model('custom');
            }
            else{
                self.model(null);
            }
            self.version(null);
            self.suppress_update_notification_version(null);
            self.ignore_is_custom_change = true;
            self.is_custom(false);
            self.ignore_is_custom_change = false;
        });

        self.makes = ko.pureComputed(function(){
            console.log("Getting printer makes.");
            var makes = [];
            if (self.make() !== 'custom' && !Octolapse.Printers.profileOptions.makes_and_models)
            {
                var make = {
                    name: self.original_make,
                    value: self.original_make
                };
                makes.push(make);
            }
            else
            {
                for (key in Octolapse.Printers.profileOptions.makes_and_models)
                {
                    var current_make = Octolapse.Printers.profileOptions.makes_and_models[key];
                    var make = {
                        'name': current_make.name,
                        'value': key
                    };
                    makes.push(make);
                }
            }
            var other_make = {
                'name': 'Custom',
                'value': 'custom'
            };
            makes.push(other_make);
            return makes;
        },this);

        self.models = ko.pureComputed(function(){
            console.log("Getting printer models.");
            var models = [];
            var model = null;
            if (self.make() !== 'custom' && !Octolapse.Printers.profileOptions.makes_and_models)
            {
                model= {
                    name: self.original_model,
                    value: self.original_model
                };
                models.push(model);

            }
            else if (
                Octolapse.Printers.profileOptions.makes_and_models &&
                (self.make() && self.make() in Octolapse.Printers.profileOptions.makes_and_models)
            ){
                var models_dict = Octolapse.Printers.profileOptions.makes_and_models[self.make()].models;
                for (key in models_dict) {
                    var current_model = models_dict[key];
                    model = {
                        'name': current_model.name,
                        'value': key
                    };
                    models.push(model);
                }
            }
            var other_model = {
                'name': 'Custom',
                'value': 'custom'
            };
            models.push(other_model);
            return models;
        },this);

        self.can_update_from_repo = ko.pureComputed(function(){
            return (
                self.make() && self.make() !== "custom" &&
                self.model() && self.model() !== "custom"
            );
        },this);
        
        self.updateProfileFromLibrary = function(on_failed){
            var data = {
                'type': 'printer',
                'profile': parent.toJS(),
                'identifiers': {
                    'make': self.make(),
                    'model': self.model()
                }
            };
            $.ajax({
                url: "./plugin/octolapse/updateProfileFromServer",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (data) {
                    var updated_profile = JSON.parse(data.profile_json);
                    // Update automatic configuration settings
                    self.version(updated_profile.automatic_configuration.version);
                    self.suppress_update_notification_version(null);
                    self.ignore_make_changes = true;
                    self.make(updated_profile.automatic_configuration.make);
                    self.ignore_make_changes = false;
                    self.original_make = updated_profile.automatic_configuration.make;
                    self.other_make("");
                    self.ignore_model_changes = true;
                    self.model(updated_profile.automatic_configuration.model);
                    self.ignore_model_changes = false;
                    self.original_model = updated_profile.automatic_configuration.model;
                    self.other_model("");
                    self.automatic_changed_to_custom(false);
                    if(!self.is_custom_triggered_update) {
                        self.ignore_is_custom_change = true;
                        self.is_custom(false);
                        self.ignore_is_custom_change = false;
                    }
                    else{
                        self.is_custom_triggered_update = false;
                    }
                    // Update the parent data
                    self.parent.updateFromServerProfile(updated_profile);

                    var message = "Your printer settings have been updated.  Click 'save' to apply the changes.";
                    var options = {
                        title: 'Printer Settings Updated',
                        text: message,
                        type: 'success',
                        hide: true,
                        addclass: "octolapse",
                        desktop: {
                            desktop: true
                        }
                    };
                    Octolapse.displayPopupForKey(
                        options,"printer-profile-update","printer-profile-update"
                    );
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    if(on_failed)
                        on_failed();
                    var message = "Octolapse was unable to update your printer profile.  See" +
                                  " plugin_octolapse.log for details.  Status: " + textStatus +
                                  ".  Error: " + errorThrown;
                    var options = {
                        title: 'Unable to Update',
                        text: message,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse",
                        desktop: {
                            desktop: true
                        }
                    };
                    Octolapse.displayPopupForKey(
                        options,"printer-profile-update","printer-profile-update"
                    );
                }
            });
        };

        self.on_closed = function(){
            Octolapse.closePopupsForKeys(['printer-profile-update', 'confirm-is-automatic']);
        }
    };
    
    Octolapse.PrinterProfileViewModel = function (values) {
        var self = this;
        self.profileTypeName = ko.observable("Printer");
        self.guid = ko.observable(values.guid);
        self.name = ko.observable(values.name);
        self.description = ko.observable(values.description);
        self.automatic_configuration = new Octolapse.AutomaticPrinterConfigurationViewModel(
            values.automatic_configuration, self
        );
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
        self.restrict_snapshot_area = ko.observable(values.restrict_snapshot_area);
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

        // Update the current profile from server profile values
        self.updateFromServerProfile = function(server_profile){
            self.name(server_profile.name);
            self.description(server_profile.description);
            self.has_been_saved_by_user(true);
            self.snapshot_command(server_profile.snapshot_command);
            self.auto_detect_position(server_profile.auto_detect_position);
            self.auto_position_detection_commands(server_profile.auto_position_detection_commands);
            self.origin_x(server_profile.origin_x);
            self.origin_y(server_profile.origin_y);
            self.origin_z(server_profile.origin_z);
            self.abort_out_of_bounds(server_profile.abort_out_of_bounds);
            self.override_octoprint_print_volume(server_profile.override_octoprint_print_volume);
            self.min_x(server_profile.min_x);
            self.max_x(server_profile.max_x);
            self.min_y(server_profile.min_y);
            self.max_y(server_profile.max_y);
            self.min_z(server_profile.min_z);
            self.max_z(server_profile.max_z);
            self.restrict_snapshot_area(server_profile.restrict_snapshot_area);
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
            var parent = self.automatic_configuration.parent;
            self.automatic_configuration.parent = null;
            var copy = ko.toJS(self);
            delete copy.helpers;
            self.automatic_configuration.parent = parent;
            return copy;

        };

    };


});
