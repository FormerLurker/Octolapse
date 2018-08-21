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
        self.profileTypeName = ko.observable("Camera")
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
        self.delay = ko.observable(values.delay);
        self.timeout_ms = ko.observable(values.timeout_ms);
        self.apply_settings_before_print = ko.observable(values.apply_settings_before_print);
        self.address = ko.observable(values.address);
        self.snapshot_request_template = ko.observable(values.snapshot_request_template);
        self.snapshot_transpose = ko.observable(values.snapshot_transpose);
        self.ignore_ssl_error = ko.observable(values.ignore_ssl_error);
        self.username = ko.observable(values.username);
        self.password = ko.observable(values.password);
        self.brightness = ko.observable(values.brightness);
        self.brightness_request_template = ko.observable(values.brightness_request_template);
        self.contrast = ko.observable(values.contrast);
        self.contrast_request_template = ko.observable(values.contrast_request_template);
        self.saturation = ko.observable(values.saturation);
        self.saturation_request_template = ko.observable(values.saturation_request_template);
        self.white_balance_auto = ko.observable(values.white_balance_auto);
        self.white_balance_auto_request_template = ko.observable(values.white_balance_auto_request_template);
        self.gain = ko.observable(values.gain);
        self.gain_request_template = ko.observable(values.gain_request_template);
        self.powerline_frequency = ko.observable(values.powerline_frequency);
        self.powerline_frequency_request_template = ko.observable(values.powerline_frequency_request_template);
        self.white_balance_temperature = ko.observable(values.white_balance_temperature);
        self.white_balance_temperature_request_template = ko.observable(values.white_balance_temperature_request_template);
        self.sharpness = ko.observable(values.sharpness);
        self.sharpness_request_template = ko.observable(values.sharpness_request_template);
        self.backlight_compensation_enabled = ko.observable(values.backlight_compensation_enabled);
        self.backlight_compensation_enabled_request_template = ko.observable(values.backlight_compensation_enabled_request_template);
        self.exposure_type = ko.observable(values.exposure_type);
        self.exposure_type_request_template = ko.observable(values.exposure_type_request_template);
        self.exposure = ko.observable(values.exposure);
        self.exposure_request_template = ko.observable(values.exposure_request_template);
        self.exposure_auto_priority_enabled = ko.observable(values.exposure_auto_priority_enabled);
        self.exposure_auto_priority_enabled_request_template = ko.observable(values.exposure_auto_priority_enabled_request_template);
        self.pan = ko.observable(values.pan);
        self.pan_request_template = ko.observable(values.pan_request_template);
        self.tilt = ko.observable(values.tilt);
        self.tilt_request_template = ko.observable(values.tilt_request_template);
        self.autofocus_enabled = ko.observable(values.autofocus_enabled);
        self.autofocus_enabled_request_template = ko.observable(values.autofocus_enabled_request_template);
        self.focus = ko.observable(values.focus);
        self.focus_request_template = ko.observable(values.focus_request_template);
        self.zoom = ko.observable(values.zoom);
        self.zoom_request_template = ko.observable(values.zoom_request_template);
        self.led1_mode = ko.observable(values.led1_mode);
        self.led1_mode_request_template = ko.observable(values.led1_mode_request_template);
        self.led1_frequency = ko.observable(values.led1_frequency);
        self.led1_frequency_request_template = ko.observable(values.led1_frequency_request_template);
        self.jpeg_quality = ko.observable(values.jpeg_quality);
        self.jpeg_quality_request_template = ko.observable(values.jpeg_quality_request_template);

        self.is_testing_custom_image_preferences = ko.observable(false)
        self.applySettingsToCamera = function (settings_type) {
            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array
            var data = {
                'profile': ko.toJS(self),
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
                        Octolapse.displayPopupForKey(options, "camera_settings_success");
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
                    Octolapse.displayPopupForKey(options,"camera_settings_success");

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
                        alert(results.error);
                    }

                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    alert("Unable to toggle the camera:(  Status: " + textStatus + ".  Error: " + errorThrown);
                }
            });
        }

        self.testCamera = function () {
            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array
            //console.log("Running camera request.");
            var data = { 'profile': ko.toJS(self) };
            $.ajax({
                url: "./plugin/octolapse/testCamera",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (results) {
                    if (results.success){

                        var options = {
                            title: 'Camera Test Success',
                            text: 'A request for a snapshot came back OK.  The camera seems to be working!',
                            type: 'success',
                            hide: true,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "camera_settings_success");
                    }
                    else {
                        var options = {
                            title: 'Camera Test Failed',
                            text: 'Errors were detected - ' + results.error,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "camera_settings_failed");
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
                    Octolapse.displayPopupForKey(options, "camera_settings_failed");
                }
            });
        };

        self.toggleApplySettingsBeforePrint = function () {


            if(self.apply_settings_before_print())
            {
                self.apply_settings_before_print(false)
                return;
            }

            self.is_testing_custom_image_preferences(true);
            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array
            //console.log("Running camera request.");
            var data = { 'profile': ko.toJS(self) };
            $.ajax({
                url: "./plugin/octolapse/testCameraSettingsApply",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (results) {
                    if (results.success){
                        self.apply_settings_before_print(true);
                        $('#camera_profile_apply_settings_before_print').prop("checked",true);
                    }
                    else {
                        var options = {
                            title: 'Unable To Enable Custom Preferences',
                            text: results.error,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "camera_settings_failed");
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
                    Octolapse.displayPopupForKey(options, "camera_settings_failed");
                },
                complete: function (){
                    self.is_testing_custom_image_preferences(false);
                }
            });
        };
    };
    Octolapse.CameraProfileValidationRules = {
        rules: {
            camera_type: { required: true },
            exposure_type: { required: true },
            led_1_mode: { required: true},
            powerline_frequency: { required: true},
            snapshot_request_template: { octolapseSnapshotTemplate: true },
            brightness_request_template: { octolapseCameraRequestTemplate: true },
            contrast_request_template: { octolapseCameraRequestTemplate: true },
            saturation_request_template: { octolapseCameraRequestTemplate: true },
            white_balance_auto_request_template: { octolapseCameraRequestTemplate: true },
            gain_request_template: { octolapseCameraRequestTemplate: true },
            powerline_frequency_request_template: { octolapseCameraRequestTemplate: true },
            white_balance_temperature_request_template: { octolapseCameraRequestTemplate: true },
            sharpness_request_template: { octolapseCameraRequestTemplate: true },
            backlight_compensation_enabled_request_template: { octolapseCameraRequestTemplate: true },
            exposure_type_request_template: { octolapseCameraRequestTemplate: true },
            exposure_request_template: { octolapseCameraRequestTemplate: true },
            exposure_auto_priority_enabled_request_template: { octolapseCameraRequestTemplate: true },
            pan_request_template: { octolapseCameraRequestTemplate: true },
            tilt_request_template: { octolapseCameraRequestTemplate: true },
            autofocus_enabled_request_template: { octolapseCameraRequestTemplate: true },
            focus_request_template: { octolapseCameraRequestTemplate: true },
            zoom_request_template: { octolapseCameraRequestTemplate: true },
            led1_mode_request_template: { octolapseCameraRequestTemplate: true },
            led1_frequency_request_template: { octolapseCameraRequestTemplate: true },
            jpeg_quality_request_template: { octolapseCameraRequestTemplate: true }
        },
        messages: {
            name: "Please enter a name for your profile"
        }
    };


});


