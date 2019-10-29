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

$(function () {


    // Settings View Model
    Octolapse.SettingsViewModel = function (parameters) {
        // Create a reference to this object
        var self = this;
        // Add this object to our Octolapse namespace
        Octolapse.Settings = this;
        Octolapse.Settings.GlobalOptions = {};
        // Create an empty add/edit profile so that the initial binding to the empty template works without errors.
        Octolapse.Settings.AddEditProfile = ko.observable({
            "templateName": "empty-template",
            "profileObservable": ko.observable()
        });
        // Assign the Octoprint settings to our namespace
        Octolapse.Settings.global_settings = parameters[0];
        Octolapse.Settings.is_loaded = ko.observable(false);
        self.loginState = parameters[1];
        self.show_import_options = ko.observable(false);
        Octolapse.SettingsImport = new Octolapse.SettingsImportViewModel();
        // Called before octoprint binds the viewmodel to the plugin
        self.onBeforeBinding = function () {
            /*
                Create our global settings
            */
            self.settings = self.global_settings.settings.plugins.octolapse;
            var settings = ko.toJS(self.settings); // just get the values

            /**
             * Profiles - These are bound by octolapse.profiles.js
             */
            /*
                Create our printers view model
            */
            var printerSettings =
                {
                    'current_profile_guid': null
                    , 'profiles': []
                    , 'default_profile': null
                    , 'profileOptions': {}
                    , 'profileViewModelCreateFunction': Octolapse.PrinterProfileViewModel
                    , 'profileValidationRules': Octolapse.PrinterProfileValidationRules
                    , 'bindingElementId': 'octolapse_printer_tab'
                    , 'addEditTemplateName': 'printer-template'
                    , 'profileTypeName': 'Printer'
                    , 'addUpdatePath': 'addUpdateProfile'
                    , 'removeProfilePath': 'removeProfile'
                    , 'setCurrentProfilePath': 'setCurrentProfile'
                };
            Octolapse.Printers = new Octolapse.ProfilesViewModel(printerSettings);

            /*
                Create our stabilizations view model
            */
            var stabilizationSettings =
                {
                    'current_profile_guid': null
                    , 'profiles': []
                    , 'default_profile': null
                    , 'profileOptions': {}
                    , 'profileViewModelCreateFunction': Octolapse.StabilizationProfileViewModel
                    , 'profileValidationRules': Octolapse.StabilizationProfileValidationRules
                    , 'bindingElementId': 'octolapse_stabilization_tab'
                    , 'addEditTemplateName': 'stabilization-template'
                    , 'profileTypeName': 'Stabilization'
                    , 'addUpdatePath': 'addUpdateProfile'
                    , 'removeProfilePath': 'removeProfile'
                    , 'setCurrentProfilePath': 'setCurrentProfile'
                };
            Octolapse.Stabilizations = new Octolapse.ProfilesViewModel(stabilizationSettings);
            
            /*
                Create our triggers view model
            */
            var triggerSettings =
                {
                    'current_profile_guid': null
                    , 'profiles': []
                    , 'default_profile': null
                    , 'profileOptions': {}
                    , 'profileViewModelCreateFunction': Octolapse.TriggerProfileViewModel
                    , 'profileValidationRules': Octolapse.TriggerProfileValidationRules
                    , 'bindingElementId': 'octolapse_trigger_tab'
                    , 'addEditTemplateName': 'trigger-template'
                    , 'profileTypeName': 'Trigger'
                    , 'addUpdatePath': 'addUpdateProfile'
                    , 'removeProfilePath': 'removeProfile'
                    , 'setCurrentProfilePath': 'setCurrentProfile'
                };
            Octolapse.Triggers = new Octolapse.ProfilesViewModel(triggerSettings);
            
            /*
                Create our rendering view model
            */
            var renderingSettings =
                {
                    'current_profile_guid': null,
                     'profiles': [],
                     'default_profile': null,
                     'profileOptions': {},
                    'profileViewModelCreateFunction': Octolapse.RenderingProfileViewModel,
                    'profileValidationRules': Octolapse.RenderingProfileValidationRules,
                    'bindingElementId': 'octolapse_rendering_tab',
                    'addEditTemplateName': 'rendering-template',
                    'profileTypeName': 'Rendering',
                    'addUpdatePath': 'addUpdateProfile',
                    'removeProfilePath': 'removeProfile',
                    'setCurrentProfilePath': 'setCurrentProfile'
                };
            Octolapse.Renderings = new Octolapse.ProfilesViewModel(renderingSettings);
            /*
                Create our camera view model
            */
            var cameraSettings =
                {
                    'current_profile_guid': null,
                    'profiles': [],
                    'default_profile': null,
                    'profileOptions': {},
                    'profileViewModelCreateFunction': Octolapse.CameraProfileViewModel,
                    'profileValidationRules': Octolapse.CameraProfileValidationRules,
                    'bindingElementId': 'octolapse_camera_tab',
                    'addEditTemplateName': 'camera-template',
                    'profileTypeName': 'Camera',
                    'addUpdatePath': 'addUpdateProfile',
                    'removeProfilePath': 'removeProfile',
                    'setCurrentProfilePath': 'setCurrentProfile'
                };
            Octolapse.Cameras = new Octolapse.ProfilesViewModel(cameraSettings);

            /*
                Create our debug view model
            */
            var debugSettings =
                {
                    'current_profile_guid': null,
                    'profiles': [],
                    'default_profile': null,
                    'profileOptions': {},
                    'profileViewModelCreateFunction': Octolapse.DebugProfileViewModel,
                    'profileValidationRules': Octolapse.DebugProfileValidationRules,
                    'bindingElementId': 'octolapse_debug_tab',
                    'addEditTemplateName': 'debug-template',
                    'profileTypeName': 'Debug',
                    'addUpdatePath': 'addUpdateProfile',
                    'removeProfilePath': 'removeProfile',
                    'setCurrentProfilePath': 'setCurrentProfile'
                };
            Octolapse.DebugProfiles = new Octolapse.ProfilesViewModel(debugSettings);

        };

        self.onAfterBinding = function (){
            // initialize settings import
            Octolapse.SettingsImport.initialize();
        };

        // Update all octolapse settings
        self.updateSettings = function (settings) {
            //console.log("Settings Received:");
            //console.log(settings);
            // GlobalOptions
            Octolapse.SettingsImport.update(settings);
            // SettingsMain
            Octolapse.SettingsMain.update(settings.main_settings);

            // Printers
            Octolapse.Printers.profiles([]);
            Octolapse.Printers.default_profile(settings.profiles.defaults.printer);
            Octolapse.Printers.profileOptions = settings.profiles.options.printer;
            Octolapse.Printers.current_profile_guid(settings.profiles.current_printer_profile_guid);
            Object.keys(settings.profiles.printers).forEach(function(key) {
                Octolapse.Printers.profiles.push(new Octolapse.PrinterProfileViewModel(settings.profiles.printers[key]));
            });

            // Stabilizations
            Octolapse.Stabilizations.profiles([]);
            Octolapse.Stabilizations.default_profile(settings.profiles.defaults.stabilization);
            Octolapse.Stabilizations.profileOptions = settings.profiles.options.stabilization;
            Octolapse.Stabilizations.current_profile_guid(settings.profiles.current_stabilization_profile_guid);
            Object.keys(settings.profiles.stabilizations).forEach(function(key) {
                Octolapse.Stabilizations.profiles.push(new Octolapse.StabilizationProfileViewModel(settings.profiles.stabilizations[key]));
            });

            // Triggers
            Octolapse.Triggers.profiles([]);
            Octolapse.Triggers.default_profile(settings.profiles.defaults.trigger);
            Octolapse.Triggers.profileOptions = settings.profiles.options.trigger;
            Octolapse.Triggers.current_profile_guid(settings.profiles.current_trigger_profile_guid);
            Object.keys(settings.profiles.triggers).forEach(function(key) {
                Octolapse.Triggers.profiles.push(new Octolapse.TriggerProfileViewModel(settings.profiles.triggers[key]));
            });
            
            // Renderings
            Octolapse.Renderings.profiles([]);
            Octolapse.Renderings.default_profile(settings.profiles.defaults.rendering);
            Octolapse.Renderings.profileOptions = settings.profiles.options.rendering;
            Octolapse.Renderings.current_profile_guid(settings.profiles.current_rendering_profile_guid);
            Object.keys(settings.profiles.renderings).forEach(function(key) {
                Octolapse.Renderings.profiles.push(new Octolapse.RenderingProfileViewModel(settings.profiles.renderings[key]));
            });

            // Cameras
            Octolapse.Cameras.profiles([]);
            Octolapse.Cameras.default_profile(settings.profiles.defaults.camera);
            Octolapse.Cameras.profileOptions = settings.profiles.options.camera;
            //console.log("Creating initial camera profiles.");
            Object.keys(settings.profiles.cameras).forEach(function(key) {
                Octolapse.Cameras.profiles.push(new Octolapse.CameraProfileViewModel(settings.profiles.cameras[key]));
            });

            // Debug
            Octolapse.DebugProfiles.profiles([]);
            Octolapse.DebugProfiles.default_profile(settings.profiles.defaults.debug);
            Octolapse.DebugProfiles.profileOptions = settings.profiles.options.debug;
            Octolapse.DebugProfiles.current_profile_guid(settings.profiles.current_debug_profile_guid);
            //console.log("Creating Debug Profiles")
            Object.keys(settings.profiles.debug).forEach(function(key) {
                Octolapse.DebugProfiles.profiles.push(new Octolapse.DebugProfileViewModel(settings.profiles.debug[key]));
            });

            Octolapse.Settings.is_loaded(true);

        };

        self.getProfileByGuid = function(profiles, guid) {
            var index = Octolapse.arrayFirstIndexOf(profiles(),
                function(item) {
                    var itemGuid = item.guid();
                    var matchFound = itemGuid === guid;
                    if (matchFound)
                        return matchFound
                }
            );
            if (index < 0) {
                return null;
            }
            return profiles()[index];
        };
        /*
            reload the default settings
        */
        self.restoreDefaultSettings = function () {
            Octolapse.showConfirmDialog(
                "restore-defaults",
                "Restore Default Settings",
                "You will lose ALL of your octolapse settings by restoring the defaults!  Are you SURE?",
                function(){
                    var data = {"client_id": Octolapse.Globals.client_id};
                    $.ajax({
                        url: "./plugin/octolapse/restoreDefaults",
                        type: "POST",
                        data: JSON.stringify(data),
                        contentType: "application/json",
                        dataType: "json",
                        success: function (newSettings) {

                            self.updateSettings(newSettings);
                            Octolapse.Globals.update(newSettings.main_settings);
                            var message = "The default settings have been restored.  It is recommended that you restart the OctoPrint server now.";
                            var options = {
                                title: 'Default Settings Restored',
                                text: message,
                                type: 'success',
                                hide: true,
                                addclass: "octolapse",
                                desktop: {
                                    desktop: true
                                }
                            };
                            Octolapse.displayPopup(options);
                        },
                        error: function (XMLHttpRequest, textStatus, errorThrown) {
                            var message = "Unable to restore the default settings.  Status: " + textStatus + ".  Error: " + errorThrown;
                            var options = {
                                title: 'Error Restoring Defaults',
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
                }
            );
        };
        /*
            load all settings default settings
        */
        self.loadSettings = function () {

            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array
            $.ajax({
                url: "./plugin/octolapse/loadSettings",
                type: "POST",
                contentType: "application/json",
                dataType: "json",
                success: function (newSettings) {
                    self.updateSettings(newSettings);
                    Octolapse.Globals.loadState();
                    //console.log("Settings have been loaded.");
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    var message = "Octolapse was unable to load the current settings.  Status: " + textStatus + ".  Error: " + errorThrown;
                    var options = {
                        title: 'Settings Load Error',
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

        self.clearSettings = function (){
            Octolapse.Settings.is_loaded(false);
             // Printers
            Octolapse.Printers.profiles([]);
            Octolapse.Printers.default_profile(null);
            Octolapse.Printers.current_profile_guid(null);
            Octolapse.Printers.profileOptions = {};
            // Stabilizations
            Octolapse.Stabilizations.profiles([]);
            Octolapse.Stabilizations.default_profile(null);
            Octolapse.Stabilizations.current_profile_guid(null);
            Octolapse.Stabilizations.profileOptions = {};
            // Triggers
            Octolapse.Triggers.profiles([]);
            Octolapse.Triggers.default_profile(null);
            Octolapse.Triggers.current_profile_guid(null);
            Octolapse.Triggers.profileOptions = {};
            // Renderings
            Octolapse.Renderings.profiles([]);
            Octolapse.Renderings.default_profile(null);
            Octolapse.Renderings.current_profile_guid(null);
            Octolapse.Renderings.profileOptions = {};
            // Cameras
            Octolapse.Cameras.profiles([]);
            Octolapse.Cameras.default_profile(null);
            Octolapse.Cameras.current_profile_guid(null);
            Octolapse.Cameras.profileOptions = {};
            // Debugs
            Octolapse.DebugProfiles.profiles([]);
            Octolapse.DebugProfiles.default_profile(null);
            Octolapse.DebugProfiles.current_profile_guid(null);
            Octolapse.DebugProfiles.profileOptions = {};
        };

        self.updateProfilesFromServer = function() {

            //console.log("Updating Octolapse profiles from the server.");
            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array
            var data = {
                'client_id': Octolapse.Globals.client_id
            };
            $.ajax({
                url: "./plugin/octolapse/updateProfilesFromServer",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (values) {
                    var message;
                    //console.log("Octolapse profiles updated from the server.");
                    var num_updated = values.num_updated;
                    if (num_updated > 0) {
                        var settings = JSON.parse(values.settings);
                        self.updateSettings(settings);
                        Octolapse.Globals.loadState();
                        message = num_updated.toString() + " Octolapse profiles were updated.";
                    }
                    else
                    {
                        message = "No new updates found.  Your Octolapse profiles are up-to-date."
                    }
                    var options = {
                        title: 'Octolapse Updates',
                        text: message,
                        type: 'success',
                        hide: true,
                        addclass: "octolapse",
                        desktop: {
                            desktop: true
                        }
                    };
                    Octolapse.displayPopupForKey(options, 'update-profile-from-server','update-profile-from-server');
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {

                    var message = "Octolapse was unable to update your profiles to the most recent version the current settings.  Status: " + textStatus + ".  Error: " + errorThrown;
                    console.error(message);
                    var options = {
                        title: 'Profile Update Error',
                        text: message,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse",
                        desktop: {
                            desktop: true
                        }
                    };
                    Octolapse.displayPopupForKey(options, 'update-profile-from-server','update-profile-from-server');
                }
            });
        };

        self.suppressServerUpdates = function() {
            var data = {
                'client_id': Octolapse.Globals.client_id
            };
            $.ajax({
                url: "./plugin/octolapse/suppressServerUpdates",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (newSettings) {
                    self.updateSettings(newSettings);
                    Octolapse.Globals.loadState();
                    var message = "Update notifications have been suppressed.  You can force an update at any time within the main settings page..";
                    var options = {
                        title: 'Updates Suppressed',
                        text: message,
                        type: 'info',
                        hide: true,
                        addclass: "octolapse",
                        desktop: {
                            desktop: true
                        }
                    };
                    Octolapse.displayPopupForKey(options, 'updates-suppressed','updates-suppressed');
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {

                    var message = "Octolapse was unable to supress update notifications.  Status: " + textStatus + ".  Error: " + errorThrown;
                    console.error(message);
                    var options = {
                        title: 'Octolapse Update Error',
                        text: message,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse",
                        desktop: {
                            desktop: true
                        }
                    };
                    Octolapse.displayPopupForKey(options, 'updates-suppressed','updates-suppressed');
                }
            });
        };
        /*
            Profile Add/Update routine for showAddEditDialog
        */
        self.addUpdateProfile = function (profile) {
            switch (profile.templateName) {
                case "printer-template":
                    Octolapse.Printers.addUpdateProfile(profile.profileObservable, self.hideAddEditDialog());
                    break;
                case "stabilization-template":
                    Octolapse.Stabilizations.addUpdateProfile(profile.profileObservable, self.hideAddEditDialog());
                    break;
                case "trigger-template":
                    Octolapse.Triggers.addUpdateProfile(profile.profileObservable, self.hideAddEditDialog());
                    break;
                case "rendering-template":
                    Octolapse.Renderings.addUpdateProfile(profile.profileObservable, self.hideAddEditDialog());
                    break;
                case "camera-template":
                    Octolapse.Cameras.addUpdateProfile(profile.profileObservable, self.hideAddEditDialog());
                    break;
                case "debug-template":
                    Octolapse.DebugProfiles.addUpdateProfile(profile.profileObservable, self.hideAddEditDialog());
                    break;
                default:
                    var message = "Cannot save the object, the template (" + profile.templateName + ") is unknown!";
                    var options = {
                        title: 'Error Saving Changes',
                        text: message,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse",
                        desktop: {
                            desktop: true
                        }
                    };
                    Octolapse.displayPopup(options);
                    break;
            }
        };
        /*
            Modal Dialog Functions
        */
        // hide the modal dialog
        self.can_hide = false;
        self.hideAddEditDialog = function () {
            console.log("Add update dialog will be closed.");
            self.can_hide = true;
            $("#octolapse_add_edit_profile_dialog").modal("hide");
        };
        self.cancelAddEditDialog = function () {
            console.log("Add update dialog cancelled.");
            // Hide the dialog
            self.hideAddEditDialog();
            // see if the current viewmodel has an on_canceled function
            if (typeof self.profileObservable().on_cancelled === 'function') {
                // call the function
                self.profileObservable().on_cancelled();
            }
        };
        // show the modal dialog
        self.showAddEditDialog = function (options, sender) {
            // Create all the variables we want to store for callbacks
            //console.log("octolapse.settings.js - Showing add edit dialog.");
            var dialog = this;
            dialog.can_hide = false;
            dialog.sender = sender;
            dialog.profileObservable = options.profileObservable;
            dialog.templateName = options.templateName;
            dialog.$addEditDialog = $("#octolapse_add_edit_profile_dialog");
            dialog.$addEditForm = dialog.$addEditDialog.find("#octolapse_add_edit_profile_form");
            dialog.$cancelButton = $("button.cancel", dialog.$addEditDialog);
            dialog.$closeIcon = $("a.close", dialog.$addEditDialog);
            dialog.$saveButton = $("button.save", dialog.$addEditDialog);
            dialog.$defaultButton = $("button.set-defaults", dialog.$addEditDialog);
            dialog.$dialogTitle = $("h3.modal-title", dialog.$addEditDialog);
            dialog.$dialogWarningContainer = $("div.dialog-warning", dialog.$addEditDialog);
            dialog.$dialogWarningText = $("span", dialog.$dialogWarningContainer);
            dialog.$summary = dialog.$addEditForm.find("#add_edit_validation_summary");
            dialog.$errorCount = dialog.$summary.find(".error-count");
            dialog.$errorList = dialog.$summary.find("ul.error-list");
            dialog.$modalBody = dialog.$addEditDialog.find(".modal-body");
            dialog.$modalHeader = dialog.$addEditDialog.find(".modal-header");
            dialog.$modalFooter = dialog.$addEditDialog.find(".modal-footer");

            // Create all of the validation rules
            dialog.rules = {
                rules: options.validationRules.rules,
                messages: options.validationRules.messages,
                ignore: ".ignore_hidden_errors:hidden, .ignore_hidden_errors.hiding",
                errorPlacement: function (error, element) {
                    var error_id = $(element).attr("name");
                    var $field_error = dialog.$addEditDialog.find(".error_label_container[data-error-for='" + error_id + "']");
                    $field_error.html(error);
                },
                highlight: function (element, errorClass) {
                    var error_id = $(element).attr("name");
                    var $field_error = dialog.$addEditDialog.find(".error_label_container[data-error-for='" + error_id + "']");
                    $field_error.removeClass("checked");
                    $field_error.addClass(errorClass);
                },
                unhighlight: function (element, errorClass) {
                    var error_id = $(element).attr("name");
                    var $field_error = dialog.$addEditDialog.find(".error_label_container[data-error-for='" + error_id + "']");
                    $field_error.addClass("checked");
                    $field_error.removeClass(errorClass);
                },
                invalidHandler: function () {
                    //console.log("Invalid!");
                    dialog.$errorCount.empty();
                    dialog.$summary.show();
                    var numErrors = dialog.validator.numberOfInvalids();
                    if (numErrors === 1)
                        dialog.$errorCount.text("1 field is invalid");
                    else
                        dialog.$errorCount.text(numErrors + " fields are invalid");
                },
                errorContainer: "#add_edit_validation_summary",
                success: function (label) {
                    label.html("&nbsp;");
                    label.parent().addClass('checked');
                    $(label).parent().parent().parent().removeClass('error');
                },
                onfocusout: function (element, event) {
                    setTimeout(function() {
                        if (dialog.validator)
                        {
                            dialog.validator.form();
                        }

                    }, 250);
                },
                onclick: function (element, event) {
                    setTimeout(function(){
                        dialog.validator.form();
                        dialog.resize();
                    }, 250);
                }
            };
            dialog.resize = function(){
                /*dialog.$addEditDialog.css("top","0px").css(
                    'margin-top',
                    Math.max(0 - dialog.$addEditDialog.height() / 2,0)
                );*/
            };
            dialog.validator = null;

            // Prevent hiding unless the event was initiated by the hideAddEditDialog function
            dialog.$addEditDialog.on("hide.bs.modal", function () {
                console.log("About to hide add edit dialog");
                if (!self.can_hide)
                    return false;
                //return self.can_hide;
                // Clear out error summary
                dialog.$errorCount.empty();
                dialog.$errorList.empty();
                dialog.$summary.hide();
                // Destroy the validator if it exists, both to save on resources, and to clear out any leftover junk.
                dialog.unbind_validation();
                // see if the current viewmodel has an on_closed function
                if (typeof self.profileObservable().on_closed === 'function')
                {
                    // call the function
                    console.log("Closing the profile dialog");
                    self.profileObservable().on_closed();
                }
            });
            // configure the modal hidden event.  Isn't it funny that bootstrap's own shortenting of their name is BS?

            // configure the dialog show event
            dialog.$addEditDialog.on("show.bs.modal", function () {
                Octolapse.Settings.AddEditProfile({
                    "profileObservable": dialog.profileObservable,
                    "templateName": dialog.templateName
                });
                // Adjust the margins, height and position
                // Set title
                dialog.$dialogTitle.text(options.title);
                if(options.warning == null)
                {
                    dialog.$dialogWarningContainer.hide();
                    dialog.$dialogWarningText.text("");
                }
                else
                {
                    dialog.$dialogWarningText.text(options.warning);
                    dialog.$dialogWarningContainer.show();

                }

                dialog.$addEditDialog.css({
                    width: 'auto',
                    'margin-left': function () {
                        return -($(this).width() / 2);
                    }
                });

                // Initialize the profile.
                var onShow = Octolapse.Settings.AddEditProfile().profileObservable().onShow;
                if (typeof onShow == 'function') {
                    onShow(dialog);
                }
            });
            // Configure the shown event
            dialog.$addEditDialog.on("shown.bs.modal", function () {
                console.log("Showing profile settings dialog.");
                self.can_hide = false;
                // Unbind all click events
                dialog.$addEditDialog.unbind('click');
                // bind any help links
                dialog.bind_help_links();

                dialog.IsValid = function()
                {
                    if (dialog.validator != null)
                        return dialog.validator.numberOfInvalids() == 0;
                    return true;
                };
                dialog.bind_validation();
                // Remove any click event bindings from the cancel button
                dialog.$cancelButton.unbind("click");
                dialog.$closeIcon.unbind("click");
                // Called when the user clicks the cancel button in any add/update dialog
                dialog.$cancelButton.bind("click", self.cancelAddEditDialog);
                dialog.$closeIcon.bind("click", self.cancelAddEditDialog);

                // remove any click event bindings from the defaults button
                dialog.$defaultButton.unbind("click");
                dialog.$defaultButton.bind("click", function () {
                    var newProfile = dialog.sender.getResetProfile(Octolapse.Settings.AddEditProfile().profileObservable());
                    Octolapse.Settings.AddEditProfile().profileObservable(newProfile);

                });

                // Remove any click event bindings from the save button
                dialog.$saveButton.unbind("click");
                // Called when a user clicks the save button on any add/update dialog.
                dialog.$saveButton.bind("click", function () {
                    console.log("Save button clicked on add/edit profile");
                    // now see if the form is valid
                    if (dialog.$addEditForm.valid()) {
                        // the form is valid, add or update the profile
                        self.addUpdateProfile(Octolapse.Settings.AddEditProfile());
                    }
                    else {
                        // Search for any hidden elements that are invalid
                        //console.log("Checking ofr hidden field error");
                        var $fieldErrors = dialog.$addEditForm.find('.error_label_container.error');
                        $fieldErrors.each(function (index, element) {
                            // Check to make sure the field is hidden.  If it's not, don't bother showing the parent container.
                            // This can happen if more than one field is invalid in a hidden form
                            var $errorContainer = $(element);
                            if (!$errorContainer.is(":visible")) {
                                //console.log("Hidden error found, showing");
                                var $collapsableContainer = $errorContainer.parents(".collapsible");
                                if ($collapsableContainer.length > 0)
                                // The containers may be nested, show each
                                    $collapsableContainer.each(function (index, container) {
                                        //console.log("Showing the collapsed container");
                                        $(container).show();
                                    });
                            }
                        });

                        // The form is invalid, add a shake animation to inform the user
                        $(dialog.$addEditDialog).addClass('shake');
                        // set a timeout so the dialog stops shaking
                        setTimeout(function () {
                            $(dialog.$addEditDialog).removeClass('shake');
                        }, 500);
                    }

                });

                // Resize the dialog
                dialog.resize();
                // see if the current viewmodel has an on_opened function
                if (typeof self.profileObservable().on_opened === 'function'){
                    // call the function
                    self.profileObservable().on_opened(dialog);
                }

            });
            dialog.unbind_validation = function()
            {
                if (dialog.validator != null) {
                    console.log("octolapse.settings.js - Unbinding validation.");
                    dialog.validator.destroy();
                    dialog.validator = null;
                }
            };
            dialog.bind_validation = function()
            {
                console.log("octolapse.settings.js - Binding validation.");
                dialog.unbind_validation();
                dialog.validator = dialog.$addEditForm.validate(dialog.rules);
                dialog.validator.form();
            };
            dialog.bind_help_links = function()
            {
                Octolapse.Help.bindHelpLinks("#octolapse_add_edit_profile_dialog");
            };
            // Open the add/edit profile dialog
            dialog.$addEditDialog.modal({
                backdrop: 'static',
                resize: true,
                maxHeight: function() {
                    return Math.max(
                      window.innerHeight - dialog.$modalHeader.outerHeight()-dialog.$modalFooter.outerHeight()-66,
                      200
                    );
                }
            });

        };

    };
    // Bind the settings view model to the plugin settings element
    OCTOPRINT_VIEWMODELS.push([
        Octolapse.SettingsViewModel
        , ["settingsViewModel", "loginStateViewModel"]
        , ["#octolapse_plugin_settings", "#octolapse_settings_nav", "#octolapse_about_tab", "#octolapse_settings_title"]
    ]);


});





