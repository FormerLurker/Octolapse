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
    ko.subscribable.fn.octolapseSubscriptWithTarget = function (handler, target) {
        var self = this;
        var _oldValue;
        self.before_change_subscription = this.subscribe(function (oldValue) {
          _oldValue = oldValue;
        }, null, 'beforeChange');

       self.change_subscription = this.subscribe(function (newValue) {
         handler(target, _oldValue, newValue);
       });

       self.dispose = function(){
           self.before_change_subscription.dispose();
           self.change_subscription.dispose();
       };
       return self;
    };

    Octolapse.WebcamSettingsPopupViewModel = function (id) {
        var self = this;
        self.id = id;
        self.selector = "#" + id;
        self.loading_selector = self.selector + ' div.webcam_settings_preview div.loading';
        self.error_selector = self.selector + ' div.webcam_settings_preview div.error';
        self.dialog = {};

        self.closeWebcamSettingsDialog = function() {
            self.can_hide = true;
            if (self.dialog.$webcamSettingsDialog)
            {
                self.dialog.$webcamSettingsDialog.modal("hide");
            }

        };

        // variable to hold the custom webcam image preferences
        self.webcam_settings = new Octolapse.WebcamSettingsViewModel(self.closeWebcamSettingsDialog);

        self.can_hide = false;

        self.openWebcamSettingsDialog = function(on_closed){
            self.dialog = {};
            self.on_closed_callback = on_closed;
            // Set close callback
            self.dialog.on_closed = function(send_settings) {
                if (self.on_closed_callback)
                {
                    var settings = null;
                    if (send_settings) {
                        settings = ko.toJS(self.webcam_settings);
                    }
                    self.on_closed_callback(settings);
                }
                self.closeWebcamSettingsDialog();
            };
            // Show the settings dialog
            self.dialog.$webcamSettingsDialog = $(self.selector);
            self.dialog.$cancelButton = $(".cancel", self.dialog.$webcamSettingsDialog);
            self.dialog.$closeIcon = $("a.close", self.dialog.$webcamSettingsDialog);
            self.dialog.$saveButton = $(".save", self.dialog.$webcamSettingsDialog);
            self.dialog.$defaultButton = $(".set-defaults", self.dialog.$webcamSettingsDialog);
            self.dialog.$modalBody = self.dialog.$webcamSettingsDialog.find(".modal-body");
            self.dialog.$modalHeader = self.dialog.$webcamSettingsDialog.find(".modal-header");
            self.dialog.$modalFooter = self.dialog.$webcamSettingsDialog.find(".modal-footer");
            self.dialog.$cancelButton.unbind("click");
            // Called when the user clicks the cancel button in any add/update dialog
            self.dialog.$cancelButton.bind("click", function() {
                self.webcam_settings.cancelWebcamChanges(self.dialog.on_closed);
            });
            self.dialog.$closeIcon.unbind("click");
            self.dialog.$closeIcon.bind("click", function() {
                self.webcam_settings.cancelWebcamChanges(self.dialog.on_closed);
            });

            self.dialog.$saveButton.unbind("click");
            // Called when the user clicks the cancel button in any add/update dialog
            self.dialog.$saveButton.bind("click", function () {
                // Save the settings.
                if (self.on_closed_callback) {
                    self.dialog.on_closed(true);
                }
                else
                {
                    self.saveWebcamSettings();
                }
            });

            self.dialog.$defaultButton.unbind("click");
            // Called when the user clicks the cancel button in any add/update dialog
            self.dialog.$defaultButton.bind("click", function () {
                // Hide the dialog
                self.webcam_settings.restoreWebcamDefaults();
            });

            // Prevent hiding unless the event was initiated by the hideAddEditDialog function

            self.dialog.$webcamSettingsDialog.on("hide.bs.modal", function () {
                //console.log("Hiding webcam settings dialog");
                if (!self.can_hide)
                    return false;
                // Clear out error summary
                self.webcam_settings.setStreamVisibility(false);
            });

            self.dialog.$webcamSettingsDialog.on("shown.bs.modal", function () {
                self.can_hide = false;
                self.webcam_settings.setStreamVisibility(true);
                self.dialog.$webcamSettingsDialog.css({
                    width: '940px',
                    'margin-left': function () {
                        return -($(this).width() / 2);
                    }
                });
            });

            self.dialog.$webcamSettingsDialog.modal({
                backdrop: 'static',
                maxHeight: function() {
                    return Math.max(
                      window.innerHeight - self.dialog.$modalHeader.innerHeight()-self.dialog.$modalFooter.innerHeight()-30,
                      200
                    );
                }
            });
        };

        self.saveWebcamSettings = function(){
            //console.log("Undoing webcam changes.");
            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array
            var data = {
                'guid': self.webcam_settings.guid(),
                'webcam_settings': ko.toJS(self.webcam_settings)
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
                        self.closeWebcamSettingsDialog();
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

        self.showWebcamSettingsForProfile = function(profile, on_preferences_changed) {
            // First update the current webcam_settings based on the current profile
            self.webcam_settings.updateWebcamSettings(profile);

            self.webcam_settings.getMjpgStreamerControls(false, function (results) {
                // Update the current settings that we just received
                if (results.settings.new_preferences_available)
                {
                    self.webcam_settings.updateWebcamSettings(results.settings);
                }

                self.openWebcamSettingsDialog(on_preferences_changed);
            }, function(results){
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

        self.showWebcamSettingsForGuid = function(guid) {
            // Load the current webcam settings
            // On success, show the dialog
            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array
            var data = {
                'guid': guid,
                'replace': false
            };
            self.webcam_settings.getImagePreferences(data, function (results) {
                // Update the current settings that we just received
                self.webcam_settings.updateWebcamSettings(results.settings);
                self.openWebcamSettingsDialog();
                if (results.settings.new_preferences_available) {
                    // If new settings are available, offer to update them, but don't do it automatically
                    var message = "Octolapse has detected new camera preferences from your " +
                        "streaming server.  Do you want to overwrite your current image preferences?";
                    Octolapse.showConfirmDialog(
                        "replace-image-preferences",
                        "New Image Preferences Available",
                        message,
                        function () {
                            data = {
                                'guid': self.webcam_settings.guid(),
                                'replace': true
                            };
                            self.webcam_settings.getImagePreferences(data, function (results) {
                                self.webcam_settings.updateWebcamSettings(results.settings);
                            });
                        }
                    );
                }
            }, function(results){
                var message = "There was a problem retrieving webcam settings from the server.";
                 if (results && results.error)
                     message = message + " Details: " + results.error;
                var options = {
                    title: 'Error Loading Webcam Settings',
                    text: message,
                    type: 'error',
                    hide: false,
                    addclass: "octolapse"
                };
                Octolapse.displayPopupForKey(options,"webcam_settings_error",["webcam_settings_error"]);
            });
        };
    };

    Octolapse.WebcamSettingsViewModel = function (close_callback) {
        var self = this;
        self.close_callback = close_callback;
        self.camera_stream_visible = ko.observable(false);
        self.throttle_ms = 250;
        self.guid = ko.observable('');
        self.name = ko.observable('unknown');
        self.stream_template = ko.observable('');
        self.snapshot_request_template = ko.observable();
        self.address = ko.observable('');
        self.username = ko.observable();
        self.password = ko.observable();
        self.ignore_ssl_error = ko.observable();
        self.timeout_ms = ko.observable();
        self.server_type = ko.observable();
        self.type = ko.observable();
        self.stream_download = ko.observable();
        self.mjpg_streamer = new Octolapse.MjpgStreamerViewModel();
        self.use_custom_webcam_settings_page = ko.observable();
        self.webcam_two_column_view = ko.observable(Octolapse.getLocalStorage("webcam_two_column_view") || false);

        self.toggleColumns = function(){
            var two_column_view = !self.webcam_two_column_view();
            self.webcam_two_column_view(two_column_view);
            //console.log("Setting two column view.");
            Octolapse.setLocalStorage("webcam_two_column_view", two_column_view);
        };

        self.getImagePreferences = function(data, success_callback, error_callback){
            $.ajax({
                url: "./plugin/octolapse/getWebcamImagePreferences",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (results) {
                    if(results.success) {
                        success_callback(results);
                    }
                    else
                    {
                        error_callback(results);
                    }
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    error_callback(null);
                }
            });
        };

        self.getMjpgStreamerControls = function(replace, success_callback, error_callback){
            // fetch control settings from the server
            if (!self.server_type() || !self.address())
                return;
            var data = {
                "profile": ko.toJS(self)
            };

            $.ajax({
                url: "./plugin/octolapse/getMjpgStreamerControls",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (results) {
                    if(!results.success) {

                        error_callback(results);
                    }
                    else
                    {
                        success_callback(results);
                    }
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    error_callback();
                }
            });
        };

        self.getToggleCustomCameraSettingsText = ko.pureComputed(function(){
           if(self.use_custom_webcam_settings_page() && self.type())
           {
               return "Switch to Default Page";
           }
           else{
               return "Switch to Custom Page";
           }
        });

        self.toggleCustomCameraSettingsPage = function(prevent_errors, force_custom){
            // fetch control settings from the server
            if (!self.server_type() || !self.address())
            {
                var message = "Cannot detect the camera type.  Either the server type is not supported, or the camera base address is not correct";
                var options = {
                    title: 'Unknown Camera Type',
                    text: message,
                    type: 'error',
                    hide: false,
                    addclass: "octolapse"
                };

                Octolapse.displayPopupForKey(options, "camera_settings_error",["camera_settings_error"]);
                return;
            }

            var data = {
                "server_type": self.server_type(),
                "camera_name": self.name() ? self.name() : "unknown",
                "address": self.address(),
                "username": self.username() ? self.username() : "",
                "password": self.password() ? self.password() : "",
                "ignore_ssl_error": self.ignore_ssl_error() ? self.ignore_ssl_error() : false
            };

            $.ajax({
                url: "./plugin/octolapse/getWebcamType",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (results) {
                    if(!results.success) {
                        data = {
                            "webcam_settings": {
                                "type": null,
                                "use_custom_webcam_settings_page": false,
                                "mjpg_streamer": {
                                    "controls": ko.toJS(self.mjpg_streamer.controls())
                                }
                            }
                        };
                        self.updateWebcamSettings(data);
                        var options = {
                            title: 'Unknown Webcam Type',
                            text: results.error,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                        self.type(null);
                        Octolapse.displayPopupForKey(options, "camera_settings_error",["camera_settings_error"]);
                        return;
                    }
                    // set our camera type info
                    var use_custom_webcam_settings_page = !self.use_custom_webcam_settings_page() || force_custom;
                    if(!results.type)
                        use_custom_webcam_settings_page = false;
                    data = {
                        "webcam_settings": {
                            "type": results.type,
                            "use_custom_webcam_settings_page": use_custom_webcam_settings_page,
                            "mjpg_streamer": {
                                "controls": ko.toJS(self.mjpg_streamer.controls())
                            }
                        }
                    };
                    self.updateWebcamSettings(data);
                    // We meed to rebind the help links here, else they will not show up.
                    Octolapse.Help.bindHelpLinks(".octolapse .webcam_settings");
                    if (!prevent_errors) {
                        var message;
                        var title = "Webcam type found!";
                        var type = "success";
                        if (!results.type) {
                            message = "There is no custom control for your webcam model at the moment!";
                            title = 'Unknown webcam';
                            type = "error";
                        } else if (!use_custom_webcam_settings_page) {
                            title = "Changed to Default View";
                            message = "Successfully switched to the default mjpg-streamer control page.";
                        } else {
                            title = "Webcam type found!";
                            message = "A custom image preference control page exists for this camera!.";
                        }
                        var options = {
                            title: title,
                            text: message,
                            type: type,
                            hide: true,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "camera-detected", ["camera-detected"]);
                    }
                    return;
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    self.type(null);
                    if (!prevent_errors) {
                        var options = {
                            title: 'Unknown Camera Type',
                            text: "Status: " + textStatus + ".  Error: " + errorThrown,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options,"camera_settings_error",["camera_settings_error"]);
                    }
                }
            });
        };

        self.refresh_template_id = ko.observable();

        self.clear_webcam_settings_template = function(){
            self.refresh_template_id(true);
        };

        self.restore_webcam_settings_template = function(){
            self.refresh_template_id(null);
        };

        self.get_webcam_settings_template = ko.pureComputed(function(){
            var value = "webcam-empty-template";
            if (self.refresh_template_id()) {
                return "webcam-empty-template";
            }
            if(self.server_type()) {
                if (self.type() && self.type().template && self.use_custom_webcam_settings_page())
                    value = self.type().template;
                else
                    value = 'webcam-' + self.server_type() + "-template";
            }
            else
                value = 'webcam-other-template';

            return value;
        });

        self.get_webcam_data = ko.pureComputed(function(){
            switch(self.server_type())
            {
                case "mjpg-streamer":
                    return self.mjpg_streamer;
                default:
                    return null;
            }
        });

        self.stream_url = ko.pureComputed(function(){
            if(!self.camera_stream_visible())
                return '';
            //console.log("Calculating stream url.");
            var url = self.stream_template();
            if (url != "")
                url = url.replace("{camera_address}", self.address());
            return url;
        },this);

        self.setStreamVisibility = function(value){
            if (self.camera_stream_visible() != value) {
                if (value){
                    //console.log("Attempting to start the camera stream");
                }
                else{
                    //console.log("Attempting to stop the camera stream");
                }
                self.camera_stream_visible(value);
                //self.stream_url();
            }
        };

        self.subscriptions = [];

        self.unsubscribe_to_settings_changes = function() {
            //console.log("Unsubscribing to camera settings changes");
            for(var i in self.subscriptions)
            {
                self.subscriptions[i].dispose();
            }
            self.subscriptions = [];
        };

        self.subscribe_to_mjpg_streamer_changes = function() {
            self.unsubscribe_to_settings_changes();
            for(var index = 0; index < self.mjpg_streamer.controls().length; index++)
            {
                var control = self.mjpg_streamer.controls()[index];
                self.subscriptions.push(control.value.octolapseSubscriptWithTarget(function (target, oldValue, newValue) {
                    if (oldValue !== newValue)
                    {
                        self.applyWebcamSetting(ko.toJS(target));
                    }
                }, control));
            }
        };

        self.subscribe_to_settings_changes = function(){
            switch(self.server_type()) {
                case "mjpg-streamer":
                    self.subscribe_to_mjpg_streamer_changes();
                    break;
            }
        };
        // I found this awesome binding handler created by Michael Rouse, available at https://codepen.io/mwrouse/pen/wWwvmN

        self.cancelWebcamChanges = function(on_closed_callback){
            //if (on_closed_callback && (self.guid() == null || self.guid() == ""))
            //    on_closed_callback(ko.toJS(self));
            //console.log("Undoing webcam changes.");
            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array

            var data = {
                'guid': self.guid(),
                'type': 'by_guid',
                'settings_type': 'web-request'
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
                    if (on_closed_callback)
                        on_closed_callback(false);
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
                    if (on_closed_callback)
                        on_closed_callback(true);
                }
            });
        };

        self.restoreWebcamDefaults = function(){
            //console.log("Loading default webcam values.");
            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array
            var data = {
                "guid": self.guid(),
                "server_type": self.server_type(),
                "camera_name": self.name() ? self.name() : "unknown",
                "address": self.address(),
                "username": self.username() ? self.username() : "",
                "password": self.password() ? self.password() : "",
                "ignore_ssl_error": self.ignore_ssl_error() ? self.ignore_ssl_error() : false
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

                        self.updateWebcamSettings(results.defaults);
                        if (self.type())
                        {
                            self.get_webcam_settings_template();
                        }
                        var options = {
                            title: 'Webcam Settings',
                            text: "Defaults successfully applied to the '" + self.name() + "' profile.",
                            type: 'success',
                            hide: true,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopup(options);
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

        self.updateWebcamSettings = function(values) {
            // clear the webcam settings template to prevent binding errors if the template changes
            self.clear_webcam_settings_template();
            var webcam_settings = {};
            if ("webcam_settings" in values)
            {
                webcam_settings = values["webcam_settings"];
            }
            if ("server_type" in webcam_settings)
            {
                self.server_type(webcam_settings.server_type);
            }

            if ("guid" in values)
                self.guid(values.guid);
            if ("name" in values)
                self.name(values.name);
            if ("address" in webcam_settings)
                self.address(webcam_settings.address);
            if (
                'snapshot_request_template' in webcam_settings &&
                self.snapshot_request_template() != webcam_settings.snapshot_request_template
            ) {
                self.snapshot_request_template(webcam_settings.snapshot_request_template);
            }
            if ("username" in webcam_settings)
                self.username(webcam_settings.username);
            if ("password" in webcam_settings)
                self.password(webcam_settings.password);
            if ("ignore_ssl_error" in webcam_settings)
                self.ignore_ssl_error(webcam_settings.ignore_ssl_error);
            if ("timeout_ms" in values)
                self.timeout_ms(values.timeout_ms);
            if ("stream_template" in webcam_settings)
                self.stream_template(webcam_settings.stream_template);

            if ("type" in webcam_settings) {
                self.type(webcam_settings.type);
            }

            if ("stream_download" in webcam_settings)
                self.stream_download(webcam_settings.stream_download);

            if("use_custom_webcam_settings_page" in webcam_settings)
            {
                self.use_custom_webcam_settings_page(webcam_settings.use_custom_webcam_settings_page);
            }

            if ("mjpg_streamer" in webcam_settings)
            {
                self.mjpg_streamer.update(webcam_settings.mjpg_streamer, self.type(), self.use_custom_webcam_settings_page());
            }
            // notify subscribers of a possible stream url change.
            //self.stream_url.notifySubscribers();
            // restore the webcam settings template so that the custom controls show
            self.restore_webcam_settings_template();
            setTimeout(function(){
                self.subscribe_to_settings_changes();
                Octolapse.Help.bindHelpLinks(".octolapse .webcam_settings");
            }, self.throttle_ms * 2);

        };

        self.applyWebcamSetting = function (setting) {
            //console.log("Changing Camera Setting " + setting_name + " to " + value.toString() + ".");
            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array

            var data = {
                'server_type': self.server_type(),
                'camera_name': self.name(),
                'address': self.address(),
                'username': self.username(),
                'password': self.password(),
                'ignore_ssl_error': self.ignore_ssl_error(),
                'setting': setting
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

        self.applyWebcamSettings = function(){
            // Get the current webcam settings
            var data = {
                'type': 'ui-settings-update',
                'settings_type': 'web-request',
                'settings': ko.toJS(self),
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

        self.previewStabilization = function() {
            var message = "Your extruder will be moved to the selected stabilization position. \
                           Make sure your bed is clear, and that your 'Home Axis Gcode Script' \
                           is correct before attempting to preview the stabilization point.  \
                           Are you sure you want to continue?";
            Octolapse.showConfirmDialog("preview-stabilization", "Preview Stabilization", message, function(){
                $.ajax({
                    url: "./plugin/octolapse/previewStabilization",
                    type: "POST",
                    dataType: "json",
                    contentType: "application/json",
                    success: function (results) {
                        if (!results.success) {
                            var options = {
                                title: 'Error Previewing Stabilization',
                                text: results.error,
                                type: 'error',
                                hide: true,
                                addclass: "octolapse"
                            };
                            Octolapse.displayPopupForKey(options, "stabilization_preview_error", ["stabilization_preview_error"]);
                        }
                    },
                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                        var options = {
                            title: 'Error Previewing Stabilization',
                            text: "Status: " + textStatus + ".  Error: " + errorThrown,
                            type: 'error',
                            hide: true,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "stabilization_preview_error", ["stabilization_preview_error"]);
                    }
                }); // end ajax call
            },null);
        };

    };
});
