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
# following email address: FormerLurker@protonmail.com
##################################################################################
*/
$(function() {
    Octolapse.CameraProfileViewModel = function (values) {
        var self = this;

        self.guid = ko.observable(values.guid);
        self.name = ko.observable(values.name);
        self.description = ko.observable(values.description);
        self.delay = ko.observable(values.delay);
        self.apply_settings_before_print = ko.observable(values.apply_settings_before_print);
        self.address = ko.observable(values.address);
        self.snapshot_request_template = ko.observable(values.snapshot_request_template);
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

        self.applySettingsToCamera = function () {
            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array
            var data = { 'profile': ko.toJS(self) };
            $.ajax({
                url: "/plugin/octolapse/applyCameraSettings",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function () {
                    alert("The settings are being applied.  It may take a few seconds for the settings to be visible within the stream.  Be sure to save the profile if you intend to keep any unsaved changes.");

                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    alert("Unable to update the camera settings!  Status: " + textStatus + ".  Error: " + errorThrown);
                }
            });
        };

        self.testCamera = function () {
            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array
            //console.log("Running camera request.");
            var data = { 'profile': ko.toJS(self) };
            $.ajax({
                url: "/plugin/octolapse/testCamera",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (results) {
                    if (results.success)
                        alert("A request for a snapshot came back OK.  The camera seems to be working!");
                    else {
                        alert(results.error);
                    }

                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    alert("The camera test failed :(  Status: " + textStatus + ".  Error: " + errorThrown);
                }
            });
        };
    };
    Octolapse.CameraProfileValidationRules = {
        rules: {
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


