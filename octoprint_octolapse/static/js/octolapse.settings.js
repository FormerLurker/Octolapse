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
        // Create an empty add/edit profile so that the initial binding to the empty template works without errors.
        Octolapse.Settings.AddEditProfile = ko.observable({
            "templateName": "empty-template",
            "profileObservable": ko.observable()
        });
        // Assign the Octoprint settings to our namespace
        Octolapse.Settings.global_settings = parameters[0];

        self.loginState = parameters[1];


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
                Create our snapshots view model
            */
            var snapshotSettings =
                {
                    'current_profile_guid': null,
                    'profiles': [],
                    'default_profile': null,
                    'profileOptions': {},
                    'profileViewModelCreateFunction': Octolapse.SnapshotProfileViewModel,
                    'profileValidationRules': Octolapse.SnapshotProfileValidationRules,
                    'bindingElementId': 'octolapse_snapshot_tab',
                    'addEditTemplateName': 'snapshot-template',
                    'profileTypeName': 'Snapshot',
                    'addUpdatePath': 'addUpdateProfile',
                    'removeProfilePath': 'removeProfile',
                    'setCurrentProfilePath': 'setCurrentProfile'
                };
            Octolapse.Snapshots = new Octolapse.ProfilesViewModel(snapshotSettings);
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

        // Update all octolapse settings
        self.updateSettings = function (settings) {
            //console.log("Settings Received:");
            //console.log(settings);
            // SettingsMain
            Octolapse.SettingsMain.update(settings);

            // Printers
            Octolapse.Printers.profiles([]);
            Octolapse.Printers.default_profile(settings.default_printer_profile);
            Octolapse.Printers.profileOptions = {
                'slicer_type_options': settings.slicer_type_options,
                'e_axis_default_mode_options': settings.e_axis_default_mode_options,
                'g90_influences_extruder_options': settings.g90_influences_extruder_options,
                'xyz_axes_default_mode_options': settings.xyz_axes_default_mode_options,
                'units_default_options': settings.units_default_options,
                'axis_speed_display_unit_options': settings.axis_speed_display_unit_options
            };
            Octolapse.Printers.current_profile_guid(settings.current_printer_profile_guid);
            settings.printers.forEach(function (item, index) {
                Octolapse.Printers.profiles.push(new Octolapse.PrinterProfileViewModel(item));
            });

            Octolapse.Stabilizations.profiles([]);
            Octolapse.Stabilizations.default_profile(settings.default_stabilization_profile);
            Octolapse.Stabilizations.profileOptions = {'stabilization_type_options': settings.stabilization_type_options}
            Octolapse.Stabilizations.current_profile_guid(settings.current_stabilization_profile_guid);
            settings.stabilizations.forEach(function (item, index) {
                Octolapse.Stabilizations.profiles.push(new Octolapse.StabilizationProfileViewModel(item));
            });

            // Snapshots
            Octolapse.Snapshots.profiles([]);
            Octolapse.Snapshots.default_profile(settings.default_snapshot_profile);
            Octolapse.Snapshots.profileOptions ={
                'trigger_types': settings.trigger_types,
                'snapshot_extruder_trigger_options': settings.snapshot_extruder_trigger_options,
                'position_restriction_shapes': settings.position_restriction_shapes,
                'position_restriction_types': settings.position_restriction_types
            }
            Octolapse.Snapshots.current_profile_guid(settings.current_snapshot_profile_guid);
            settings.snapshots.forEach(function (item, index) {
                Octolapse.Snapshots.profiles.push(new Octolapse.SnapshotProfileViewModel(item));
            });

            // Renderings
            Octolapse.Renderings.profiles([]);
            Octolapse.Renderings.default_profile(settings.default_rendering_profile);
            Octolapse.Renderings.profileOptions = {
                'rendering_fps_calculation_options': settings.rendering_fps_calculation_options,
                'rendering_output_format_options': settings.rendering_output_format_options,
                'rendering_file_templates': settings.rendering_file_templates,
                'overlay_text_templates': settings.overlay_text_templates,
                'overlay_text_alignment_options': settings.overlay_text_alignment_options,
                'overlay_text_valign_options': settings.overlay_text_valign_options,
                'overlay_text_halign_options': settings.overlay_text_halign_options,
            }
            Octolapse.Renderings.current_profile_guid(settings.current_rendering_profile_guid);
            settings.renderings.forEach(function (item, index) {
                var o = new Octolapse.RenderingProfileViewModel(item);
                Octolapse.Renderings.profiles.push(o);
            });

            // Cameras
            Octolapse.Cameras.profiles([]);
            Octolapse.Cameras.default_profile(settings.default_camera_profile);
            Octolapse.Cameras.profileOptions = {
                'camera_powerline_frequency_options': settings.camera_powerline_frequency_options,
                'camera_exposure_type_options': settings.camera_exposure_type_options,
                'camera_led_1_mode_options': settings.camera_led_1_mode_options,
                'snapshot_transpose_options': settings.snapshot_transpose_options,
                'camera_type_options': settings.camera_type_options

            }

            settings.cameras.forEach(function (item, index) {
                Octolapse.Cameras.profiles.push(new Octolapse.CameraProfileViewModel(item));
            });

            // Debug
            Octolapse.DebugProfiles.profiles([]);
            Octolapse.DebugProfiles.default_profile(settings.current_debug_profile_guid);
            Octolapse.DebugProfiles.profileOptions = {'debug_profile_options': settings.debug_profile_options}
            Octolapse.DebugProfiles.current_profile_guid(settings.current_debug_profile_guid);
            settings.debug_profiles.forEach(function (item, index) {
                Octolapse.DebugProfiles.profiles.push(new Octolapse.DebugProfileViewModel(item));
            });

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
                            Octolapse.Globals.update(newSettings);
                            alert("The default settings have been restored.  It is recommended that you restart the OctoPrint server now.");
                        },
                        error: function (XMLHttpRequest, textStatus, errorThrown) {
                            alert("Unable to restore the default settings.  Status: " + textStatus + ".  Error: " + errorThrown);
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
                    //console.log("Settings have been loaded.");
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    alert("Octolapse was unable to load the current settings.  Status: " + textStatus + ".  Error: " + errorThrown);
                }
            });

        };

        self.clearSettings = function (){
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
            // Snapshots
            Octolapse.Snapshots.profiles([]);
            Octolapse.Snapshots.default_profile(null);
            Octolapse.Snapshots.current_profile_guid(null);
            Octolapse.Snapshots.profileOptions = {};
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
        }
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
                case "snapshot-template":
                    Octolapse.Snapshots.addUpdateProfile(profile.profileObservable, self.hideAddEditDialog());
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
                    alert("Cannot save the object, the template (" + profile.templateName + ") is unknown!");
                    break;
            }

        };

        /*
            Modal Dialog Functions
        */
        // hide the modal dialog
        self.hideAddEditDialog = function (sender, event) {
            $("#octolapse_add_edit_profile_dialog").modal("hide");
        };
        // show the modal dialog
        self.showAddEditDialog = function (options, sender) {
            // Create all the variables we want to store for callbacks
            //console.log("octolapse.settings.js - Showing add edit dialog.");
            var dialog = this;
            dialog.sender = sender;
            dialog.profileObservable = options.profileObservable;
            dialog.templateName = options.templateName;
            dialog.$addEditDialog = $("#octolapse_add_edit_profile_dialog");
            dialog.$addEditForm = dialog.$addEditDialog.find("#octolapse_add_edit_profile_form");
            dialog.$cancelButton = $("a.cancel", dialog.$addEditDialog);
            dialog.$saveButton = $("a.save", dialog.$addEditDialog);
            dialog.$defaultButton = $("a.set-defaults", dialog.$addEditDialog);
            dialog.$dialogTitle = $("h3.modal-title", dialog.$addEditDialog);
            dialog.$dialogWarningContainer = $("div.dialog-warning", dialog.$addEditDialog);
            dialog.$dialogWarningText = $("span", dialog.$dialogWarningContainer);
            dialog.$summary = dialog.$addEditForm.find("#add_edit_validation_summary");
            dialog.$errorCount = dialog.$summary.find(".error-count");
            dialog.$errorList = dialog.$summary.find("ul.error-list");
            dialog.$modalBody = dialog.$addEditDialog.find(".modal-body");

            // Create all of the validation rules
            var rules = {
                rules: options.validationRules.rules,
                messages: options.validationRules.messages,
                ignore: ".ignore_hidden_errors:hidden",
                errorPlacement: function (error, element) {
                    var error_id = $(element).attr("id");
                    var $field_error = $(".error_label_container[data-error-for='" + error_id + "']");
                    //console.log("Placing Error, element:" + error_id + ", Error: " + $(error).html());
                    $field_error.html(error);
                },
                unhighlight: function (element, errorClass) {
                    //$(element).parent().parent().removeClass(errorClass);
                    var error_id = $(element).attr("id");
                    var $field_error = $(".error_label_container[data-error-for='" + error_id + "']");
                    //console.log("Unhighlighting error for element:" + error_id + ", ErrorClass: " + errorClass);
                    $field_error.addClass("checked");
                    $field_error.removeClass(errorClass);
                },
                highlight: function (element, errorClass) {
                    //$(element).parent().parent().addClass(errorClass);
                    var error_id = $(element).attr("id");
                    var $field_error = $(".error_label_container[data-error-for='" + error_id + "']");
                    //console.log("Highlighting error for element:" + error_id + ", ErrorClass: " + errorClass);
                    $field_error.removeClass("checked");
                    $field_error.addClass(errorClass);
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
                    dialog.validator.form();
                    /*
                    return;

                    var also_validate = $(element).attr("data-also-validate");
                    if(also_validate)
                    {
                        var fields_to_validate = also_validate.split(" ");
                        fields_to_validate.forEach(function(item){
                           $("#"+item).valid();
                        });
                    }

                    $.validator.defaults.onfocusout.call(this, element, event);
                    //
                    */
                }

            };
            dialog.validator = null;
            // configure the modal hidden event.  Isn't it funny that bootstrap's own shortenting of their name is BS?
            dialog.$addEditDialog.on("hidden.bs.modal", function () {
                // Clear out error summary
                dialog.$errorCount.empty();
                dialog.$errorList.empty();
                dialog.$summary.hide();
                // Destroy the validator if it exists, both to save on resources, and to clear out any leftover junk.
                if (dialog.validator != null) {
                    dialog.validator.destroy();
                    dialog.validator = null;
                }
            });
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
                    onShow();
                }
            });
            // Configure the shown event
            dialog.$addEditDialog.on("shown.bs.modal", function () {
                dialog.validator = dialog.$addEditForm.validate(rules);
                dialog.validator.form()
                // Remove any click event bindings from the cancel button
                dialog.$cancelButton.unbind("click");
                // Called when the user clicks the cancel button in any add/update dialog
                dialog.$cancelButton.bind("click", function () {
                    // Hide the dialog
                    self.hideAddEditDialog();
                });

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
            });
            // Open the add/edit profile dialog
            dialog.$addEditDialog.modal();
        };



    };
    // Bind the settings view model to the plugin settings element
    OCTOPRINT_VIEWMODELS.push([
        Octolapse.SettingsViewModel
        , ["settingsViewModel", "loginStateViewModel"]
        , ["#octolapse_plugin_settings", "#octolapse_settings_nav", "#octolapse_about_tab"]
    ]);


});





