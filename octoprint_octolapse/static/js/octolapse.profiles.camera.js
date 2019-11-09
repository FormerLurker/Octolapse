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

    Octolapse.CameraProfileViewModel = function (values) {
        var self = this;
        //console.log("Creating camera profile settings viewmodel");
        self.profileTypeName = ko.observable("Camera");
        self.guid = ko.observable(values.guid);
        self.name = ko.observable(values.name);
        self.enabled = ko.observable(values.enabled);
        self.description = ko.observable(values.description);
        self.camera_type = ko.observable(values.camera_type);
        self.gcode_camera_script = ko.observable(values.gcode_camera_script);
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
        self.snapshot_transpose = ko.observable(values.snapshot_transpose);
        self.camera_stream_closed = false;
        self.camera_stream_visible = ko.pureComputed(function(){
            var visible = (
                self.camera_type() === 'webcam' &&
                self.enable_custom_image_preferences() &&
                !self.camera_stream_closed
            );
            self.webcam_settings.setStreamVisibility(visible);
            return visible;
        });
        self.webcam_settings = new Octolapse.WebcamSettingsViewModel(null);
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

        self.toggleCamera = function(){
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
                    }
                    else {
                        var options = {
                            title: 'Toggle Camera Error',
                            text: results.error,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse",
                            desktop: {
                                desktop: true
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
                            desktop: true
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

        self.toggleCustomImagePreferences = function () {
            if (self.enable_custom_image_preferences()) {
                self.enable_custom_image_preferences(false);
                return;
            }

            if (self.camera_stream_visible()) {
                self.enable_custom_image_preferences(true);
                return;
            }
            self.tryEnableCustomImagePreferences();

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
                        self.updateImagePreferencesFromServer(true);
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

        self.on_closed = function(){
            //console.log("Closing camera profile");
            self.webcam_settings.setStreamVisibility(false);
            self.automatic_configuration.on_closed();
        };

        self.on_cancelled = function(){
            //console.log("Cancelling camera profile");
            if(self.camera_type() == "webcam" && self.enable_custom_image_preferences()) {
                self.webcam_settings.cancelWebcamChanges();
            }
        };

        self.updateFromServer = function(values) {
            self.name(values.name);
            self.enabled(values.enabled);
            self.description(values.description);
            self.camera_type(values.camera_type);
            //self.gcode_camera_script = ko.observable(values.gcode_camera_script);
            self.enable_custom_image_preferences(values.enable_custom_image_preferences);
            self.on_print_start_script(values.on_print_start_script);
            self.on_before_snapshot_script(values.on_before_snapshot_script);
            //self.external_camera_snapshot_script = ko.observable(values.external_camera_snapshot_script);
            //self.on_after_snapshot_script = ko.observable(values.on_after_snapshot_script);
            //self.on_before_render_script = ko.observable(values.on_before_render_script);
            //self.on_after_render_script = ko.observable(values.on_after_render_script);
            self.delay(values.delay);
            self.timeout_ms(values.timeout_ms);
            self.apply_settings_before_print(values.apply_settings_before_print);
            self.apply_settings_at_startup(values.apply_settings_at_startup);
            self.snapshot_transpose(values.snapshot_transpose);
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
            var copy = ko.toJS(self);
            self.automatic_configuration.parent = parent;
            return copy;
        };

        self.automatic_configuration.is_confirming.subscribe(function(value){
            //console.log("IsClickable" + value.toString());
            Octolapse.Cameras.setIsClickable(!value);
        });

        self.updateImagePreferencesFromServer = function(replace) {
            self.webcam_settings.getMjpgStreamerControls(replace, function (results) {
                // Update the current settings that we just received
                if (results.settings.new_preferences_available) {
                    // If new settings are available, offer to update them, but don't do it automatically
                    var message = "Octolapse has detected new camera preferences from your " +
                        "streaming server.  Do you want to overwrite your current image preferences?";
                    Octolapse.showConfirmDialog(
                        "replace-image-preferences",
                        "New Image Preferences Available",
                        message,
                        function () {
                            self.webcam_settings.updateWebcamSettings(results.settings);
                        }
                    );
                }
                else
                {
                    self.webcam_settings.updateWebcamSettings(results.settings);
                }
            }, function(results){
                 self.enable_custom_image_preferences(false);
                 var message = "There was a problem retrieving webcam settings from the server.";
                 if (results && results.error)
                     message = message + " Details: " + results.error;
                 var options = {
                    title: 'Webcam Settings Error',
                    text: message,
                    type: 'error',
                    hide: false,
                    addclass: "octolapse"
                };

                Octolapse.displayPopupForKey(options, "webcam_settings_error",["webcam_settings_error"]);
            });
        };

        self.on_opened = function(dialog) {
            console.log("Opening camera profile");
            if (self.enable_custom_image_preferences())
                self.updateImagePreferencesFromServer(false);
        };

        // update the webcam settings
        self.webcam_settings.updateWebcamSettings(values);

        // Now that the webcam settings are updated, subscribe to address changes
        // so we can update the streaming server controls
        self.webcam_settings.address.subscribe(function(newValue){
            if(self.enable_custom_image_preferences())
                self.updateImagePreferencesFromServer(true);
        });
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


