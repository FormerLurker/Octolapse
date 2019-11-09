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

    Octolapse.MainSettingsViewModel = function (parameters) {
        // Create a reference to this object
        var self = this;

        // Add this object to our Octolapse namespace
        Octolapse.SettingsMain = this;
        // Assign the Octoprint settings to our namespace
        self.global_settings = parameters[0];

        // Settings values
        self.is_octolapse_enabled = ko.observable();
        self.auto_reload_latest_snapshot = ko.observable();
        self.auto_reload_frames = ko.observable();
        self.show_navbar_icon = ko.observable();
        self.show_navbar_when_not_printing = ko.observable();
        self.cancel_print_on_startup_error = ko.observable();
        self.show_printer_state_changes = ko.observable();
        self.show_position_changes = ko.observable();
        self.show_extruder_state_changes = ko.observable();
        self.show_trigger_state_changes = ko.observable();
        self.show_snapshot_plan_information = ko.observable();
        self.preview_snapshot_plans = ko.observable();
        self.preview_snapshot_plan_autoclose = ko.observable();
        self.preview_snapshot_plan_seconds = ko.observable();
        self.automatic_updates_enabled = ko.observable();
        self.automatic_update_interval_days = ko.observable();
        // Informational Values
        self.platform = ko.observable();


        self.onBeforeBinding = function () {

        };
        // Get the dialog element
        self.onAfterBinding = function () {



        };

        self.update = function (settings) {
            //console.log("Updating Main Settings")
            self.is_octolapse_enabled(settings.is_octolapse_enabled);
            self.auto_reload_latest_snapshot(settings.auto_reload_latest_snapshot);
            self.auto_reload_frames(settings.auto_reload_frames);
            self.show_navbar_icon(settings.show_navbar_icon);
            self.show_navbar_when_not_printing(settings.show_navbar_when_not_printing);
            self.show_printer_state_changes(settings.show_printer_state_changes);
            self.show_position_changes(settings.show_position_changes);
            self.show_extruder_state_changes(settings.show_extruder_state_changes);
            self.show_trigger_state_changes(settings.show_trigger_state_changes);
            self.show_snapshot_plan_information(settings.show_snapshot_plan_information);
            self.preview_snapshot_plans(settings.preview_snapshot_plans);
            self.preview_snapshot_plan_autoclose(settings.preview_snapshot_plan_autoclose);
            self.preview_snapshot_plan_seconds(settings.preview_snapshot_plan_seconds);

            self.cancel_print_on_startup_error(settings.cancel_print_on_startup_error);
            self.automatic_update_interval_days(settings.automatic_update_interval_days);
            self.automatic_updates_enabled(settings.automatic_updates_enabled);

            //self.platform(settings.platform());

        };

        self.toggleOctolapse = function(){

            var previousEnabledValue = !Octolapse.Globals.enabled();
            var data = {
                "is_octolapse_enabled": Octolapse.Globals.enabled()
            };
            //console.log("Toggling octolapse.")
            $.ajax({
                url: "./plugin/octolapse/setEnabled",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function () {

                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    var message = "Unable to enable/disable Octolapse.  Status: " + textStatus + ".  Error: " + errorThrown;
                    var options = {
                        title: 'Enable/Disable Error',
                        text: message,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse",
                        desktop: {
                            desktop: true
                        }
                    };
                    Octolapse.displayPopup(options);

                    Octolapse.Globals.enabled(previousEnabledValue);
                }
            });
            return true;
        };

        // hide the modal dialog
        self.can_hide = false;
        self.hideDialog = function () {
            self.can_hide = true;
            $("#octolapse_edit_settings_main_dialog").modal("hide");
        };

        self.showEditMainSettingsPopup = function () {
            //console.log("showing main settings")
            self.is_octolapse_enabled(Octolapse.Globals.enabled());
            self.auto_reload_latest_snapshot(Octolapse.Globals.auto_reload_latest_snapshot());
            self.auto_reload_frames(Octolapse.Globals.auto_reload_frames());
            self.show_navbar_icon(Octolapse.Globals.navbar_enabled());
            self.show_navbar_when_not_printing(Octolapse.Globals.show_navbar_when_not_printing());
            self.show_printer_state_changes(Octolapse.Globals.show_printer_state_changes());
            self.show_position_changes(Octolapse.Globals.show_position_changes());
            self.show_extruder_state_changes(Octolapse.Globals.show_extruder_state_changes());
            self.show_trigger_state_changes(Octolapse.Globals.show_trigger_state_changes());
            self.show_snapshot_plan_information(Octolapse.Globals.show_snapshot_plan_information());
            self.preview_snapshot_plans(Octolapse.Globals.preview_snapshot_plans());
            self.preview_snapshot_plan_autoclose(Octolapse.Globals.preview_snapshot_plan_autoclose());
            self.preview_snapshot_plan_seconds(Octolapse.Globals.preview_snapshot_plan_seconds());
            self.automatic_update_interval_days(Octolapse.Globals.automatic_update_interval_days());
            self.automatic_updates_enabled(Octolapse.Globals.automatic_updates_enabled());

            self.cancel_print_on_startup_error(Octolapse.Globals.cancel_print_on_startup_error());

            var dialog = this;
            dialog.$editDialog = $("#octolapse_edit_settings_main_dialog");
            dialog.$editForm = $("#octolapse_edit_main_settings_form");
            dialog.$cancelButton = $(".cancel", dialog.$editDialog);
            dialog.$closeIcon = $("a.close", dialog.$editDialog);
            dialog.$saveButton = $(".save", dialog.$editDialog);
            dialog.$defaultButton = $(".set-defaults", dialog.$editDialog);
            dialog.$summary = dialog.$editForm.find("#edit_validation_summary");
            dialog.$errorCount = dialog.$summary.find(".error-count");
            dialog.$errorList = dialog.$summary.find("ul.error-list");
            dialog.$modalBody = dialog.$editDialog.find(".modal-body");
            dialog.$modalHeader = dialog.$editDialog.find(".modal-header");
            dialog.$modalFooter = dialog.$editDialog.find(".modal-footer");
            dialog.rules = {
                rules: Octolapse.MainSettingsValidationRules.rules,
                messages: Octolapse.MainSettingsValidationRules.messages,
                ignore: ".ignore_hidden_errors:hidden, .ignore_hidden_errors.hiding",
                errorPlacement: function (error, element) {
                    var $field_error = $(element).parent().parent().find(".error_label_container");
                    $field_error.html(error);
                    $field_error.removeClass("checked");

                },
                highlight: function (element, errorClass) {
                    //$(element).parent().parent().addClass(errorClass);
                    var $field_error = $(element).parent().parent().find(".error_label_container");
                    $field_error.removeClass("checked");
                    $field_error.addClass(errorClass);
                },
                unhighlight: function (element, errorClass) {
                    //$(element).parent().parent().removeClass(errorClass);
                    var $field_error = $(element).parent().parent().find(".error_label_container");
                    $field_error.addClass("checked");
                    $field_error.removeClass(errorClass);
                },
                invalidHandler: function () {
                    dialog.$errorCount.empty();
                    dialog.$summary.show();
                    var numErrors = dialog.validator.numberOfInvalids();
                    if (numErrors === 1)
                        dialog.$errorCount.text("1 field is invalid");
                    else
                        dialog.$errorCount.text(numErrors + " fields are invalid");
                },
                errorContainer: "#edit_validation_summary",
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
                    //setTimeout(() => dialog.validator.form(), 250);
                    setTimeout(function() {
                        dialog.validator.form();
                        dialog.resize();
                    }, 250);
                }
            };
            dialog.resize = function(){
                /*
                dialog.$editDialog.css("top","0px").css(
                    'margin-top',
                    Math.max(0 - dialog.$editDialog.height() / 2, 0)
                );*/
            };
            dialog.validator = null;

            dialog.$editDialog.on("hide.bs.modal", function () {
                if (!self.can_hide)
                    return false;
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
            dialog.$editDialog.on("shown.bs.modal", function () {
                self.can_hide = false;
                // bind any help links
                Octolapse.Help.bindHelpLinks("#octolapse_edit_settings_main_dialog");
                // Create all of the validation rules

                dialog.validator = dialog.$editForm.validate(dialog.rules);

                // Remove any click event bindings from the cancel button
                dialog.$cancelButton.unbind("click");
                dialog.$closeIcon.unbind("click");
                // Called when the user clicks the cancel button in any add/update dialog
                dialog.$cancelButton.bind("click", self.hideDialog);
                dialog.$closeIcon.bind("click", self.hideDialog);

                // remove any click event bindings from the defaults button
                dialog.$defaultButton.unbind("click");
                dialog.$defaultButton.bind("click", function () {
                    // Set the options to the current settings
                    self.is_octolapse_enabled(true);
                    self.auto_reload_latest_snapshot(true);
                    self.auto_reload_frames(5);
                    self.show_navbar_icon(true);
                    self.show_navbar_when_not_printing(false);
                    self.show_printer_state_changes(false);
                    self.show_position_changes(false);
                    self.show_extruder_state_changes(false);
                    self.show_trigger_state_changes(false);
                    self.show_snapshot_plan_information(false);
                    self.preview_snapshot_plans(false);
                    self.preview_snapshot_plan_autoclose(false);
                    self.preview_snapshot_plan_seconds(false);
                    self.automatic_update_interval_days(7);
                    self.automatic_updates_enabled(true);

                });

                // Remove any click event bindings from the save button
                dialog.$saveButton.unbind("click");
                // Called when a user clicks the save button on any add/update dialog.
                dialog.$saveButton.bind("click", function ()
                {
                    if (dialog.$editForm.valid()) {
                        // the form is valid, add or update the profile
                        var data = {
                            "is_octolapse_enabled": self.is_octolapse_enabled()
                            , "auto_reload_latest_snapshot": self.auto_reload_latest_snapshot()
                            , "auto_reload_frames": self.auto_reload_frames()
                            , "show_navbar_icon": self.show_navbar_icon()
                            , "show_navbar_when_not_printing": self.show_navbar_when_not_printing()
                            , "show_printer_state_changes": self.show_printer_state_changes()
                            , "show_position_changes": self.show_position_changes()
                            , "show_extruder_state_changes": self.show_extruder_state_changes()
                            , "show_trigger_state_changes": self.show_trigger_state_changes()
                            , "show_snapshot_plan_information": self.show_snapshot_plan_information()
                            , "preview_snapshot_plans": self.preview_snapshot_plans()
                            , "preview_snapshot_plan_autoclose": self.preview_snapshot_plan_autoclose()
                            , "preview_snapshot_plan_seconds": self.preview_snapshot_plan_seconds()
                            , "automatic_update_interval_days": self.automatic_update_interval_days()
                            , "automatic_updates_enabled": self.automatic_updates_enabled()
                            , "cancel_print_on_startup_error": self.cancel_print_on_startup_error()
                            , "client_id": Octolapse.Globals.client_id
                        };
                        //console.log("Saving main settings.")
                        $.ajax({
                            url: "./plugin/octolapse/saveMainSettings",
                            type: "POST",
                            data: JSON.stringify(data),
                            contentType: "application/json",
                            dataType: "json",
                            success: function () {
                                self.hideDialog();
                            },
                            error: function (XMLHttpRequest, textStatus, errorThrown) {
                                var message = "Unable to save the main settings.  Status: " + textStatus + ".  Error: " + errorThrown;
                                var options = {
                                    title: 'Main Settings Save Error',
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
                    else
                    {
                        // Search for any hidden elements that are invalid
                        //console.log("Checking ofr hidden field error");
                        var $fieldErrors = dialog.$editForm.find('.error_label_container.error');
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
                        $(dialog.$editDialog).addClass('shake');
                        // set a timeout so the dialog stops shaking
                        setTimeout(function () { $(dialog.$editDialog).removeClass('shake'); }, 500);
                    }

                });
                // Resize the dialog
                dialog.resize();
            });
            dialog.$editDialog.modal({
                backdrop: 'static',
                maxHeight: function() {
                    return Math.max(
                      window.innerHeight - dialog.$modalHeader.outerHeight()-dialog.$modalFooter.outerHeight()-66,
                      200
                    );
                }
            });

        };

        Octolapse.MainSettingsValidationRules = {
            rules: {

            },
            messages: {

            }
        };
    };
    // Bind the settings view model to the plugin settings element
    OCTOPRINT_VIEWMODELS.push([
        Octolapse.MainSettingsViewModel
        , ["settingsViewModel"]
        , ["#octolapse_main_tab"]
    ]);
});

