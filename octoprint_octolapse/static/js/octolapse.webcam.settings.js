/*
##################################################################################
# Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
# Copyright (C) 2019  Brad Hochgesang
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
    Octolapse.WebcamSettingsPopupViewModel = function (values) {
        var self = this;
        self.webcam_settings = new Octolapse.WebcamSettingsViewModel(null, null);
        if (values != null)
            self.webcam_settings.updateWebcamSettings(values);

        self.openWebcamSettingsDialog = function()
        {

            var dialog = this;
            // Show the settings dialog
            dialog.$webcamSettingsDialog = $("#octolapse_webcam_settings_dialog");
            dialog.$webcamSettingsForm = dialog.$webcamSettingsDialog.find("#octolapse_webcam_settings_form");
            dialog.$webcamStreamImg = dialog.$webcamSettingsDialog.find("#octolapse_webcam_settings_stream");
            dialog.$cancelButton = $("a.cancel", dialog.$webcamSettingsDialog);
            dialog.$saveButton = $("a.save", dialog.$webcamSettingsDialog);
            dialog.$defaultButton = $("a.set-defaults", dialog.$webcamSettingsDialog);
            dialog.$modalBody = dialog.$webcamSettingsDialog.find(".modal-body");
            dialog.$modalHeader = dialog.$webcamSettingsDialog.find(".modal-header");
            dialog.$modalFooter = dialog.$webcamSettingsDialog.find(".modal-footer");
            dialog.$cancelButton.unbind("click");
            // Called when the user clicks the cancel button in any add/update dialog
            dialog.$cancelButton.bind("click", function () {
                // Hide the dialog
                self.webcam_settings.cancelWebcamChanges();
            });

            dialog.$saveButton.unbind("click");
            // Called when the user clicks the cancel button in any add/update dialog
            dialog.$saveButton.bind("click", function () {
                // Save the settings.
                self.saveWebcamSettings();
            });

            dialog.$defaultButton.unbind("click");
            // Called when the user clicks the cancel button in any add/update dialog
            dialog.$defaultButton.bind("click", function () {
                // Hide the dialog
                self.webcam_settings.restoreWebcamDefaults();
            });

            dialog.$webcamSettingsDialog.on("hidden.bs.modal", function () {
                // Clear out error summary
                dialog.$webcamStreamImg.attr("src","");
            });

            dialog.$webcamSettingsDialog.on("show.bs.modal", function () {
                dialog.$webcamStreamImg.attr("src",self.webcam_settings.stream_url());
            });

            dialog.$webcamSettingsDialog.on("shown.bs.modal", function () {
                dialog.$webcamSettingsDialog.css({
                    width: '940px',
                    'margin-left': function () {
                        return -($(this).width() / 2);
                    }
                });

            });
            dialog.$webcamSettingsDialog.modal({
                maxHeight: function() {
                    return Math.max(
                      window.innerHeight - dialog.$modalHeader.outerHeight()-dialog.$modalFooter.outerHeight()-25,
                      200
                    );
                }
            });
        };

        self.saveWebcamSettings = function(){

            console.log("Undoing webcam changes.");
            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array
            var data = {
                'guid': self.webcam_settings.guid(),
                'webcam_settings': {
                    'brightness': self.webcam_settings.brightness(),
                    'contrast': self.webcam_settings.contrast(),
                    'saturation': self.webcam_settings.saturation(),
                    'white_balance_auto': self.webcam_settings.white_balance_auto(),
                    'gain': self.webcam_settings.gain(),
                    'powerline_frequency': self.webcam_settings.powerline_frequency(),
                    'white_balance_temperature':  self.webcam_settings.white_balance_temperature(),
                    'sharpness': self.webcam_settings.sharpness(),
                    'backlight_compensation_enabled': self.webcam_settings.backlight_compensation_enabled(),
                    'exposure_type': self.webcam_settings.exposure_type(),
                    'exposure': self.webcam_settings.exposure(),
                    'exposure_auto_priority_enabled': self.webcam_settings.exposure_auto_priority_enabled(),
                    'pan': self.webcam_settings.pan(),
                    'tilt': self.webcam_settings.tilt(),
                    'autofocus_enabled': self.webcam_settings.autofocus_enabled(),
                    'focus': self.webcam_settings.focus(),
                    'zoom': self.webcam_settings.zoom(),
                    'led1_mode': self.webcam_settings.led1_mode(),
                    'led1_frequency': self.webcam_settings.led1_frequency(),
                    'jpeg_quality': self.webcam_settings.jpeg_quality(),
                }
            };
            $.ajax({
                url: "./plugin/octolapse/saveWebcamSettings",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (results) {
                    if(!results.success) {
                        var options = {
                            title: 'Error Saving Camera Settings',
                            text: results.error,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "camera_settings_error",["camera_settings_failed"]);
                    }
                    else
                    {
                        self.webcam_settings.closeWebcamSettingsDialog();
                    }
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    var options = {
                        title: 'Error Saving Camera Settings',
                        text: "Status: " + textStatus + ".  Error: " + errorThrown,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse"
                    };
                    Octolapse.displayPopupForKey(options,"camera_settings_error",["camera_settings_failed"]);
                }
            });
        };

        self.showWebcamSettings = function() {
                // Load the current webcam settings
                // On success, show the dialog
                 // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array
                var data = {
                    'guid': Octolapse.Status.current_camera_guid()
                };

                $.ajax({
                    url: "./plugin/octolapse/getWebcamImagePreferences",
                    type: "POST",
                    data: JSON.stringify(data),
                    contentType: "application/json",
                    dataType: "json",
                    success: function (results) {
                        if(results.success) {
                            // Update the current settings that we just received
                            values = results.camera_profile;
                            self.webcam_settings.updateWebcamSettings(values);
                            self.openWebcamSettingsDialog();
                        }
                        else
                        {
                            var options = {
                                title: 'Error Loading Webcam Settings',
                                text: results.error,
                                type: 'error',
                                hide: false,
                                addclass: "octolapse"
                            };
                            Octolapse.displayPopupForKey(options,"camera_settings_failure",["camera_settings_failure"]);
                        }
                    },
                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                        var options = {
                            title: 'Error Loading Webcam Settings',
                            text: "Status: " + textStatus + ".  Error: " + errorThrown,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options,"camera_settings_failure",["camera_settings_failure"]);
                    }
                });
            };


    };
    Octolapse.MjpegStreamerOptionsViewModel = function ()
    {
        var self = this;
        self.camera_powerline_frequency_options = ko.observable();
        self.camera_exposure_type_options = ko.observable();
        self.camera_led_1_mode_options = ko.observable();

        self.update = function(values){
            self.camera_powerline_frequency_options(values.camera_powerline_frequency_options);
            self.camera_exposure_type_options(values.camera_exposure_type_options);
            self.camera_led_1_mode_options(values.camera_led_1_mode_options);
        };
    };

    Octolapse.MjpegStreamerViewModel = function ()
    {
        var self = this;
        self.options = new Octolapse.MjpegStreamerOptionsViewModel();
        self.update = function(values)
        {
            self.options.update(values.options);
        };
    };
    Octolapse.WebcamSettingsViewModel = function (values, camera_stream_visible_observable) {
        var self = this;

        if (camera_stream_visible_observable == null)
            self.camera_stream_visible = ko.observable(true);
        else
            self.camera_stream_visible = camera_stream_visible_observable;
        self.throttle_ms = 250;
        self.guid = ko.observable('');
        self.name = ko.observable('unknown');
        self.visible = ko.observable(false);
        self.stream_template = ko.observable('');
        self.snapshot_request_template = ko.observable();
        self.address = ko.observable('');
        self.username = ko.observable();
        self.password = ko.observable();
        self.ignore_ssl_error = ko.observable();
        self.timeout_ms = ko.observable();
        // Need to subscribe to changes for these camera settings observables
        self.white_balance_auto = ko.observable(0);

        self.powerline_frequency = ko.observable('');

        self.backlight_compensation_enabled = ko.observable(false);

        self.exposure_type = ko.observable(0);

        self.exposure_auto_priority_enabled = ko.observable(0);

        self.autofocus_enabled = ko.observable(0);

        self.led1_mode = ko.observable(0);

        // Need to throttle our slider controls
        // Brightness
        self.brightness = ko.observable(0);
        self.throttled_brightness = ko.computed(self.brightness).extend({ rateLimit: { timeout: self.throttle_ms, method: "notifyWhenChangesStop" } });

        // Contrast
        self.contrast = ko.observable(0);
        self.throttled_contrast = ko.computed(self.contrast).extend({ rateLimit: { timeout: self.throttle_ms, method: "notifyWhenChangesStop" } });

        // Saturation
        self.saturation = ko.observable(0);
        self.throttled_saturation = ko.computed(self.saturation).extend({ rateLimit: { timeout: self.throttle_ms, method: "notifyWhenChangesStop" } });

        // Gain
        self.gain = ko.observable(0);
        self.throttled_gain = ko.computed(self.gain).extend({ rateLimit: { timeout: self.throttle_ms, method: "notifyWhenChangesStop" } });

        // Sharpness
        self.sharpness = ko.observable(0);
        self.throttled_sharpness = ko.computed(self.sharpness).extend({ rateLimit: { timeout: self.throttle_ms, method: "notifyWhenChangesStop" } });

        // White Balance Temperature
        self.white_balance_temperature = ko.observable(0);
        self.throttled_white_balance_temperature = ko.computed(self.white_balance_temperature).extend({ rateLimit: { timeout: self.throttle_ms, method: "notifyWhenChangesStop" } });

        // Exposure
        self.exposure = ko.observable(0);
        self.throttled_exposure = ko.computed(self.exposure).extend({ rateLimit: { timeout: self.throttle_ms, method: "notifyWhenChangesStop" } });

        // Pan
        self.pan = ko.observable(0);
        self.throttled_pan = ko.computed(self.pan).extend({ rateLimit: { timeout: self.throttle_ms, method: "notifyWhenChangesStop" } });

        // Tilt
        self.tilt = ko.observable(0);
        self.throttled_tilt = ko.computed(self.tilt).extend({ rateLimit: { timeout: self.throttle_ms, method: "notifyWhenChangesStop" } });

        // Zoom
        self.zoom = ko.observable(0);
        self.throttled_zoom = ko.computed(self.zoom).extend({ rateLimit: { timeout: self.throttle_ms, method: "notifyWhenChangesStop" } });

        // Focus
        self.focus = ko.observable(0);
        self.throttled_focus = ko.computed(self.focus).extend({ rateLimit: { timeout: self.throttle_ms, method: "notifyWhenChangesStop" } });

        // Led 1 frequency
        self.led1_frequency = ko.observable(0);
        self.throttled_led1_frequency = ko.computed(self.led1_frequency).extend({ rateLimit: { timeout: self.throttle_ms, method: "notifyWhenChangesStop" } });

        // JPEG Quality
        self.jpeg_quality = ko.observable(0);
        self.throttled_jpeg_quality = ko.computed(self.jpeg_quality).extend({ rateLimit: { timeout: self.throttle_ms, method: "notifyWhenChangesStop" } });

        // MJpegStreamer
        self.mjpegstreamer = new Octolapse.MjpegStreamerViewModel()

        self.stream_url = ko.computed(function(){
            if(!self.camera_stream_visible())
                return '';
            console.log("Calculating stream url.");
            var url = self.stream_template();
            if (url != "")
                url = url.replace("{camera_address}", self.address());
            return url;
        },this);

        self.subscriptions = [];

        self.unsubscribe_to_settings_changes = function()
        {
            console.log("Unsubscribing to camera settings changes");
            for(var i in self.subscriptions)
            {
                self.subscriptions[i].dispose();
            }
            self.subscriptions = [];
        };

        self.subscribe_to_settings_changes = function(){
            console.log("Subscribing to camera settings changes");
            self.subscriptions.push(self.white_balance_auto.subscribe(function (val) {
                self.applyWebcamSetting('white_balance_auto', val);
            }, self));
            self.subscriptions.push(self.powerline_frequency.subscribe(function (val) {
                self.applyWebcamSetting('powerline_frequency', val);
            }, self));
            self.subscriptions.push(self.backlight_compensation_enabled.subscribe(function (val) {
                self.applyWebcamSetting('backlight_compensation_enabled', val);
            }, self));
            self.subscriptions.push(self.exposure_type.subscribe(function (val) {
                self.applyWebcamSetting('exposure_type', val);
            }, self));
            self.subscriptions.push(self.exposure_auto_priority_enabled.subscribe(function (val) {
                self.applyWebcamSetting('exposure_auto_priority_enabled', val);
            }, self));
            self.subscriptions.push(self.autofocus_enabled.subscribe(function (val) {
                self.applyWebcamSetting('autofocus_enabled', val);
            }, self));
            self.subscriptions.push(self.led1_mode.subscribe(function (val) {
                self.applyWebcamSetting('led1_mode', val);
            }, self));
            self.subscriptions.push(self.throttled_brightness.subscribe(function (val) {
                self.applyWebcamSetting('brightness', val);
            }, self));
            self.subscriptions.push(self.throttled_contrast.subscribe(function (val) {
                self.applyWebcamSetting('contrast', val);
            }, self));
            self.subscriptions.push(self.throttled_saturation.subscribe(function (val) {
                self.applyWebcamSetting('saturation', val);
            }, self));
            self.subscriptions.push(self.throttled_gain.subscribe(function (val) {
                self.applyWebcamSetting('gain', val);
            }, self));
            self.subscriptions.push(self.throttled_sharpness.subscribe(function (val) {
                self.applyWebcamSetting('sharpness', val);
            }, self));
            self.subscriptions.push(self.throttled_white_balance_temperature.subscribe(function (val) {
                self.applyWebcamSetting('white_balance_temperature', val);
            }, self));
            self.subscriptions.push(self.throttled_exposure.subscribe(function (val) {
                self.applyWebcamSetting('exposure', val);
            }, self));
            self.subscriptions.push(self.throttled_pan.subscribe(function (val) {
                self.applyWebcamSetting('pan', val);
            }, self));
            self.subscriptions.push(self.throttled_tilt.subscribe(function (val) {
                self.applyWebcamSetting('tilt', val);
            }, self));

            self.subscriptions.push(self.throttled_zoom.subscribe(function (val) {
                self.applyWebcamSetting('zoom', val);
            }, self));

            self.subscriptions.push(self.throttled_focus.subscribe(function (val) {
                self.applyWebcamSetting('focus', val);
            }, self));

            self.subscriptions.push(self.throttled_led1_frequency.subscribe(function (val) {
                self.applyWebcamSetting('led1_frequency', val);
            }, self));

            self.subscriptions.push(self.throttled_jpeg_quality.subscribe(function (val) {
                self.applyWebcamSetting('jpeg_quality', val);
            }, self));
        }
        // I found this awesome binding handler created by Michael Rouse, available at https://codepen.io/mwrouse/pen/wWwvmN


        self.cancelWebcamChanges = function(){
            if (self.guid() == null || self.guid() == "")
                return;
            console.log("Undoing webcam changes.");
            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array

            var data = {
                'guid': self.guid(),
                'type': 'by_guid'
            };
            $.ajax({
                url: "./plugin/octolapse/applyCameraSettings",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (results) {
                    if(!results.success) {
                        var options = {
                            title: 'Error Cancelling Webcam Settings',
                            text: results.error,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "camera_settings_error",["camera_settings_error"]);
                    }
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    var options = {
                        title: 'Error Cancelling Webcam Settings',
                        text: "Status: " + textStatus + ".  Error: " + errorThrown,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse"
                    };
                    Octolapse.displayPopupForKey(options,"camera_settings_error",["camera_settings_error"]);
                }
            });
            self.closeWebcamSettingsDialog();
        };

        self.restoreWebcamDefaults = function(){

            console.log("Loading default webcam values.");
            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array
            var data = {
                'guid': self.guid()
            };
            $.ajax({
                url: "./plugin/octolapse/loadWebcamDefaults",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (results) {
                    if(!results.success) {
                        var options = {
                            title: 'Error Loading Webcam Defaults',
                            text: results.error,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "camera_settings_error",["camera_settings_error"]);
                    }
                    else {
                        self.updateWebcamSettings(results.defaults, true);
                    }
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    var options = {
                        title: 'Error Loading Webcam Defaults',
                        text: "Status: " + textStatus + ".  Error: " + errorThrown,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse"
                    };
                    Octolapse.displayPopupForKey(options,"camera_settings_error",["camera_settings_error"]);
                }
            });
        };

        self.closeWebcamSettingsDialog = function()
        {
            $("#octolapse_webcam_settings_dialog").modal("hide");
        };

        self.updateWebcamSettings = function(values)
        {

            self.unsubscribe_to_settings_changes();
            if ("mjpegstreamer" in values.webcam_settings)
            {
                self.mjpegstreamer.update(values.webcam_settings.mjpegstreamer);
            }
            if ("guid" in values)
                self.guid(values.guid);
            if ("name" in values)
                self.name(values.name);
            if ("address" in values.webcam_settings)
                self.address(values.webcam_settings.address);
            if ('snapshot_request_template' in values.webcam_settings)
                self.snapshot_request_template(values.webcam_settings.snapshot_request_template);
            if ("username" in values.webcam_settings)
                self.username(values.webcam_settings.username);
            if ("password" in values.webcam_settings)
                self.password(values.webcam_settings.password);
            if ("ignore_ssl_error" in values.webcam_settings)
                self.ignore_ssl_error(values.webcam_settings.ignore_ssl_error);
            if ("timeout_ms" in values)
                self.timeout_ms(values.timeout_ms);
            if ("stream_template" in values.webcam_settings)
                self.stream_template(values.webcam_settings.stream_template);
            if ("brightness" in values.webcam_settings)
                self.brightness(values.webcam_settings.brightness);
            if ("contrast" in values.webcam_settings)
                self.contrast(values.webcam_settings.contrast);
            if ("saturation" in values.webcam_settings)
                self.saturation(values.webcam_settings.saturation);
            if ("white_balance_auto" in values.webcam_settings)
                self.white_balance_auto(values.webcam_settings.white_balance_auto);
            if ("powerline_frequency" in values.webcam_settings)
                self.gain(values.webcam_settings.gain);
            if ("powerline_frequency" in values.webcam_settings)
                self.powerline_frequency(values.webcam_settings.powerline_frequency);
            if ("white_balance_temperature" in values.webcam_settings)
                self.white_balance_temperature(values.webcam_settings.white_balance_temperature);
            if ("sharpness" in values.webcam_settings)
                self.sharpness(values.webcam_settings.sharpness);
            if ("backlight_compensation_enabled" in values.webcam_settings)
                self.backlight_compensation_enabled(values.webcam_settings.backlight_compensation_enabled);
            if ("exposure_type" in values.webcam_settings)
                self.exposure_type(values.webcam_settings.exposure_type);
            if ("exposure" in values.webcam_settings)
                self.exposure(values.webcam_settings.exposure);
            if ("exposure_auto_priority_enabled" in values.webcam_settings)
                self.exposure_auto_priority_enabled(values.webcam_settings.exposure_auto_priority_enabled);
            if ("pan" in values.webcam_settings)
                self.pan(values.webcam_settings.pan);
            if ("tilt" in values.webcam_settings)
                self.tilt(values.webcam_settings.tilt);
            if ("autofocus_enabled" in values.webcam_settings)
                self.autofocus_enabled(values.webcam_settings.autofocus_enabled);
            if ("focus" in values.webcam_settings)
                self.focus(values.webcam_settings.focus);
            if ("zoom" in values.webcam_settings)
                self.zoom(values.webcam_settings.zoom);
            if ("led1_mode" in values.webcam_settings)
                self.led1_mode(values.webcam_settings.led1_mode);
            if ("led1_frequency" in values.webcam_settings)
                self.led1_frequency(values.webcam_settings.led1_frequency);
            if ("jpeg_quality" in values.webcam_settings)
                self.jpeg_quality(values.webcam_settings.jpeg_quality);

            setTimeout(function(){ self.subscribe_to_settings_changes(); }, self.throttle_ms * 2);

        };

        self.applyWebcamSetting = function (setting_name, value) {

            console.log("Changing Camera Setting " + setting_name + " to " + value.toString() + ".");
            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array

            var data = {
                'server_type': 'MJPG-Streamer',
                'name': self.name(),
                'address': self.address(),
                'username': self.username(),
                'password': self.password(),
                'ignore_ssl_error': self.ignore_ssl_error(),
                'timeout_ms': self.timeout_ms(),
                'setting_name':setting_name,
                'value':value
            };

            $.ajax({
                url: "./plugin/octolapse/applyWebcamSetting",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (results) {
                    if(!results.success) {
                        var options = {
                            title: 'Error Applying Webcam Settings',
                            text: results.error,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "camera_settings_error",["camera_settings_error"]);
                    }
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    var options = {
                        title: 'Error Applying Webcam Settings',
                        text: "Status: " + textStatus + ".  Error: " + errorThrown,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse"
                    };
                    Octolapse.displayPopupForKey(options,"camera_settings_error",["camera_settings_error"]);
                }
            });
        };

        if (values != null)
            self.updateWebcamSettings(values);
    }
});
