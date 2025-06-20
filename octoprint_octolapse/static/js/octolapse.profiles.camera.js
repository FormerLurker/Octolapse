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

    Octolapse.CameraProfileViewModel = function (values) {
        var self = this;
        //console.log("Creating camera profile settings viewmodel");
        self.profileTypeName = ko.observable("Camera");
        self.guid = ko.observable(values.guid);
        self.name = ko.observable(values.name);
        self.enabled = ko.observable(values.enabled);
        self.description = ko.observable(values.description);
        self.camera_type = ko.observable(values.camera_type);
        self.on_before_snapshot_gcode = ko.observable(values.on_before_snapshot_gcode);
        self.gcode_camera_script = ko.observable(values.gcode_camera_script);
        self.on_after_snapshot_gcode = ko.observable(values.on_after_snapshot_gcode);
        self.on_print_start_script = ko.observable(values.on_print_start_script);
        self.on_before_snapshot_script = ko.observable(values.on_before_snapshot_script);
        self.external_camera_snapshot_script = ko.observable(values.external_camera_snapshot_script);
        self.on_after_snapshot_script = ko.observable(values.on_after_snapshot_script);
        self.on_before_render_script = ko.observable(values.on_before_render_script);
        self.on_after_render_script = ko.observable(values.on_after_render_script);
        self.on_print_end_script = ko.observable(values.on_print_end_script);
        self.delay = ko.observable(values.delay);
        self.timeout_ms = ko.observable(values.timeout_ms);
        self.enable_custom_image_preferences = ko.observable(values.enable_custom_image_preferences);
        self.apply_settings_before_print = ko.observable(values.apply_settings_before_print);
        self.apply_settings_at_startup = ko.observable(values.apply_settings_at_startup);
        self.apply_settings_when_disabled = ko.observable(values.apply_settings_when_disabled);
        self.snapshot_transpose = ko.observable(values.snapshot_transpose);
        self.webcam_settings = new Octolapse.WebcamSettingsViewModel();
        self.webcam_settings_popup = new Octolapse.WebcamSettingsPopupViewModel("octolapse_camera_image_preferences_popup");
        self.webcam_settings_popup.webcam_settings.updateWebcamSettings(values.webcam_settings);
        self.is_dialog_open = ko.observable(false);

        self.is_testing_custom_image_preferences = ko.observable(false);

        self.applySettingsToCamera = function (settings_type) {
            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array
            var data = {
                'profile': self.toJS(self),
                'type': "from_new_profile",
                'settings_type':settings_type
            };
            $.ajax({
                url: "./plugin/octolapse/applyCameraSettings",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (results) {
                    if(results.success) {
                        var options = {
                            title: 'Success',
                            text: 'Camera settings were applied with no errors.',
                            type: 'success',
                            hide: true,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "camera_settings_success", ["camera_settings_success"]);
                    }
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    var options = {
                        title: 'Error',
                        text: "Unable to update the camera settings!  Status: " + textStatus + ".  Error: " + errorThrown,
                        type: 'error',
                        hide: true,
                        addclass: "octolapse"
                    };
                    Octolapse.displayPopupForKey(options,"camera_settings_success", ["camera_settings_success"]);

                }
            });
        };

        self.toggleCamera = function(callback){
            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array
            //console.log("Running camera request.");
            var data = { 'guid': self.guid(), "client_id": Octolapse.Globals.client_id };
            $.ajax({
                url: "./plugin/octolapse/toggleCamera",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (results) {
                    if (results.success) {
                        self.enabled(results.enabled);
                        if (callback)
                        {
                            callback(results.enabled);
                        }
                    }
                    else {
                        var options = {
                            title: 'Toggle Camera Error',
                            text: results.error,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse",
                            desktop: {
                                desktop: false
                            }
                        };
                        Octolapse.displayPopup(options);
                    }
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    var message = "Unable to toggle the camera:(  Status: " + textStatus + ".  Error: " + errorThrown;
                    var options = {
                        title: 'Toggle Camera Error',
                        text: message,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse",
                        desktop: {
                            desktop: false
                        }
                    };
                    Octolapse.displayPopup(options);
                }
            });
        };


        self.testCamera = function () {
            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array
            //console.log("Running camera request.");
            var data = { 'profile': self.toJS(self) };
            $.ajax({
                url: "./plugin/octolapse/testCamera",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (results) {
                    if (results.success){

                        var success_options = {
                            title: 'Camera Test Success',
                            text: 'A request for a snapshot came back OK.  The camera seems to be working!',
                            type: 'success',
                            hide: true,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(success_options, "camera_settings_success", ["camera_settings_success"]);
                    }
                    else {
                        var fail_options = {
                            title: 'Camera Test Failed',
                            text: 'Errors were detected - ' + results.error,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(fail_options, "camera_settings_failed",["camera_settings_failed"]);
                    }
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {

                    var options = {
                        title: 'Camera Test Failed',
                        text: "Status: " + textStatus + ".  Error: " + errorThrown,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse"
                    };
                    Octolapse.displayPopupForKey(options, "camera_settings_failed",["camera_settings_failed"]);
                }
            });
        };

        self.testCameraScript = function(script_type)
        {
            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array
            //console.log("Running camera request.");
            var message = "Testing the " + script_type + " script with " + (self.timeout_ms() / 1000.0).toFixed(2) + " second timeout.  Please do not attempt" +
                " to run any further tests until this script has finished.  If your script times out, try increasing your 'Snapshot Timeout'.";
            var testing_popup = {
                title: "Testing Camera Script",
                text: message,
                type: "info",
                hide: false,
                addclass: "octolapse"
            };
            Octolapse.displayPopupForKey(testing_popup, "camera_script_test", ["camera_script_test"]);

            var data = { 'profile': self.toJS(self), 'script_type': script_type };
            $.ajax({
                url: "./plugin/octolapse/testCameraScript",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (results) {
                    if (results.success){
                        var title = "Camera Script Success";
                        var message_type='success';
                        var message = "The script appears to work!  No errors or error codes were returned.";
                        var hide = true;
                        if (script_type == 'snapshot') {
                            if (results.snapshot_created)
                            {
                                 message = "The script appears to work, and a snapshot was found!  No errors or error codes were returned.";
                            }
                            else
                            {
                                 title = "Partial Camera Script Success";
                                 message = "The script appears to work, but no snapshot was found in the target folder.  This is OK if you are leaving images on your DSLR's internal memory.  Otherwise this could be a problem.";
                                 message_type = "warning";
                                 hide = false;
                            }
                        }
                        var success_options = {
                            title: title,
                            text: message,
                            type: message_type,
                            hide: hide,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(success_options, "camera_script_test", ["camera_script_test"]);
                    }
                    else {
                        var fail_options = {
                            title: 'Camera Script Failed',
                            text: 'Errors were detected - ' + results.error,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(fail_options, "camera_script_test",["camera_script_test"]);
                    }
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {

                    var options = {
                        title: 'Camera Script Test Failed',
                        text: "Unable to perform the test, or an unexpected error occurred.  Please check the log file for details.  Status: " + textStatus + ".  Error: " + errorThrown,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse"
                    };
                    Octolapse.displayPopupForKey(options, "camera_script_test",["camera_script_test"]);
                }
            });
        };

        self.toggleCustomImagePreferences = function () {
            if (self.enable_custom_image_preferences()) {
                self.enable_custom_image_preferences(false);
            }
            else {
                self.tryEnableCustomImagePreferences();
            }

        };

        self.showWebcamSettings = function() {
            var profile = self.toJS();
            self.webcam_settings_popup.showWebcamSettingsForProfile(profile, function(webcam_settings) {
                //console.log("Applying new settings to camera profile.");
                if (webcam_settings)
                {
                    profile.webcam_settings = webcam_settings;
                    self.webcam_settings.updateWebcamSettings(profile);
                }
            });
        };

        self.tryEnableCustomImagePreferences = function(){
            self.is_testing_custom_image_preferences(true);
            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array
            //console.log("Running camera request.");
            var data = { 'profile': self.toJS(self) };
            $.ajax({
                url: "./plugin/octolapse/testCameraSettingsApply",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (results) {
                    if (results.success){
                        self.enable_custom_image_preferences(true);
                    }
                    else {
                        self.enable_custom_image_preferences(false);
                        var options = {
                            title: 'Unable To Enable Custom Preferences',
                            text: results.error,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "camera_settings_failed",["camera_settings_failed"]);
                    }
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {

                    var options = {
                        title: 'Unable To Apply Custom Preferences',
                        text: "An unexpected error occurred.  Status: " + textStatus + ".  Error: " + errorThrown,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse"
                    };
                    Octolapse.displayPopupForKey(options, "camera_settings_failed",["camera_settings_failed"]);
                },
                complete: function (){
                    self.is_testing_custom_image_preferences(false);
                }
            });
        };

        self.on_opened = function(dialog) {
            //console.log("Opening camera profile");
            self.is_dialog_open(true);
        };

        self.on_closed = function(){
            //console.log("Closing camera profile");
            self.is_dialog_open(false);
            self.automatic_configuration.on_closed();
        };

        self.updateFromServer = function(values) {
            self.name(values.name);
            self.enabled(values.enabled);
            self.description(values.description);
            self.camera_type(values.camera_type);
            self.on_before_snapshot_gcode = ko.observable(values.on_before_snapshot_gcode);
            self.gcode_camera_script = ko.observable(values.gcode_camera_script);
            self.on_after_snapshot_gcode = ko.observable(values.on_after_snapshot_gcode);
            self.on_before_snapshot_gcode = ko.observable(values.on_before_snapshot_gcode);
            self.enable_custom_image_preferences(values.enable_custom_image_preferences);
            self.delay(values.delay);
            self.timeout_ms(values.timeout_ms);
            self.apply_settings_before_print(values.apply_settings_before_print);
            self.apply_settings_at_startup(values.apply_settings_at_startup);
            self.snapshot_transpose(values.snapshot_transpose);
            if (typeof values.apply_settings_when_disabled != 'undefined')
            {
                self.apply_settings_when_disabled(values.apply_settings_when_disabled);
            }
            // Clear any settings that we don't want to update, unless they aren't important.
            self.on_print_start_script("");
            self.on_before_snapshot_script("");
            self.external_camera_snapshot_script("");
            self.on_after_snapshot_script("");
            self.on_before_render_script("");
            self.on_after_render_script("");
            self.on_print_end_script("");
            self.webcam_settings.updateWebcamSettings(values);
        };

        self.automatic_configuration = new Octolapse.ProfileLibraryViewModel(
            values.automatic_configuration,
            Octolapse.Cameras.profileOptions.server_profiles,
            self.profileTypeName(),
            self,
            self.updateFromServer
        );

        self.toJS = function()
        {
            // need to remove the parent link from the automatic configuration to prevent a cyclic copy
            var parent = self.automatic_configuration.parent;
            self.automatic_configuration.parent = null;
            var webcam_settings_popup = self.webcam_settings_popup;
            self.webcam_settings_popup = null;
            var copy = ko.toJS(self);
            self.automatic_configuration.parent = parent;
            self.webcam_settings_popup = webcam_settings_popup;
            return copy;
        };

        self.automatic_configuration.is_confirming.subscribe(function(value){
            //console.log("IsClickable" + value.toString());
            Octolapse.Cameras.setIsClickable(!value);
        });

        // update the webcam settings
        self.webcam_settings.updateWebcamSettings(values);
    };

    Octolapse.CameraProfileValidationRules = {
        rules: {
            octolapse_camera_camera_type: { required: true },
            octolapse_camera_snapshot_request_template: { octolapseSnapshotTemplate: true },
            octolapse_camera_stream_template: { octolapseSnapshotTemplate: true },
        },
        messages: {
            octolapse_camera_name: "Please enter a name for your profile"
        }
    };


});


