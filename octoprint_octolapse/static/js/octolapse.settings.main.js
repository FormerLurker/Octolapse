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
$(function () {

    Octolapse.MainSettingsViewModel = function() {
        var self = this;
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
        self.snapshot_archive_directory = ko.observable();
        self.timelapse_directory = ko.observable();
        self.temporary_directory = ko.observable();
        self.test_mode_enabled = ko.observable();
        // rename this so that it never gets updated when saved
        self.octolapse_version = ko.observable("unknown");
        self.settings_version = ko.observable("unknown");
        self.octolapse_git_version = ko.observable(null);
        // Computed Observables
        self.preview_snapshot_plan_seconds_text = ko.pureComputed(function(){
            if (!self.preview_snapshot_plan_seconds())
                return "unknown";
            return self.preview_snapshot_plan_seconds().toString();
        });

        self.github_link = ko.pureComputed(function(){
            var git_version = self.octolapse_git_version();
            if (!git_version)
                return null;
            // If this is a commit, link to the commit
            if (self.octolapse_version().includes("+"))
            {
                return  'https://github.com/FormerLurker/Octolapse/commit/' + Octolapse.Globals.main_settings.octolapse_git_version();
            }
            // This is a release, link to the tag
            return 'https://github.com/FormerLurker/Octolapse/releases/tag/v' + self.octolapse_version();
        });

        self.update = function (settings, defaults) {
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
            self.snapshot_archive_directory(settings.snapshot_archive_directory);
            self.timelapse_directory(settings.timelapse_directory);
            self.temporary_directory(settings.temporary_directory);
            self.settings_version(settings.settings_version);
            self.test_mode_enabled(settings.test_mode_enabled);
            self.octolapse_version(settings.version || settings.octolapse_version || null);
            self.octolapse_git_version(settings.git_version || settings.octolapse_git_version || null);

            if (defaults)
                self.defaults = settings.defaults;
        };

        self.toggleOctolapse = function(){

            var newValue = !self.is_octolapse_enabled();
            var data = {
                "is_octolapse_enabled": newValue,
                "client_id": Octolapse.Globals.client_id
            };
            //console.log("Toggling octolapse.")
            $.ajax({
                url: "./plugin/octolapse/setEnabled",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (results) {
                    // update the global value and the local value
                    self.is_octolapse_enabled(newValue);
                    Octolapse.Globals.main_settings.is_octolapse_enabled(newValue);
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
                            desktop: false
                        }
                    };
                    Octolapse.displayPopup(options);
                }
            });
            return true;
        };

        self.toggleTestMode = function(){

            var newValue = !self.test_mode_enabled();
            var data = {
                "test_mode_enabled": newValue,
                "client_id": Octolapse.Globals.client_id
            };
            //console.log("Toggling test mode.")
            $.ajax({
                url: "./plugin/octolapse/setTestMode",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (results) {
                    // update the global value and the local value
                    self.test_mode_enabled(newValue);
                    Octolapse.Globals.main_settings.test_mode_enabled(newValue);
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    var message = "Unable to enable/disable test mode.  Status: " + textStatus + ".  Error: " + errorThrown;
                    var options = {
                        title: 'Enable/Disable Test Mode Error',
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
            return true;
        };

        self.toggleSnapshotPlanPreview = function(){

            var newValue = !self.preview_snapshot_plans();
            var data = {
                "preview_snapshot_plans_enabled": newValue,
                "client_id": Octolapse.Globals.client_id
            };
            //console.log("Toggling test mode.")
            $.ajax({
                url: "./plugin/octolapse/setPreviewSnapshotPlans",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (results) {
                    // update the global value and the local value
                    self.preview_snapshot_plans(newValue);
                    Octolapse.Globals.main_settings.preview_snapshot_plans(newValue);
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    var message = "Unable to enable/disable preview snapshot plans.  Status: " + textStatus + ".  Error: " + errorThrown;
                    var options = {
                        title: 'Enable/Disable Preview Snapshot Plans Error',
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
            return true;
        };

        self.testDirectory = function(type, directory){

            var data = {
                "type": type,
                "directory": directory
            };
            //console.log("Toggling octolapse.")
            $.ajax({
                url: "./plugin/octolapse/testDirectory",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (results) {
                    if (results.success){

                        var success_options = {
                            title: 'Directory Test Passed',
                            text: 'The selected directory passed all tests and is ready to be used!',
                            type: 'success',
                            hide: true,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(success_options, "directory_test", ["directory_test"]);
                    }
                    else {
                        var fail_options = {
                            title: 'Directory Test Failed',
                            text: 'Errors were detected - ' + results.error,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(fail_options, "camera_settings_failed",["camera_settings_failed"]);
                    }
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    var message = "Unable to test the directory.  Status: " + textStatus + ".  Error: " + errorThrown;
                    var options = {
                        title: 'Enable/Disable Error',
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
            return true;
        };

        self.toJS = function()
        {
            // need to remove the parent link from the automatic configuration to prevent a cyclic copy
            var dialog = self.dialog;
            self.dialog = null;
            var js = ko.toJS(self);
            self.dialog = dialog;
            return js;
        };

        Octolapse.MainSettingsValidationRules = {
            rules: {

            },
            messages: {

            }
        };
    };
    Octolapse.MainSettingsEditViewModel = function () {
        // Create a reference to this object
        var self = this;

        // Settings values
        self.dialog = {};
        // Informational Values
        self.platform = ko.observable();

        self.main_settings = new Octolapse.MainSettingsViewModel();
        self.defaults = {};
/*
        self.onBeforeBinding = function () {

        };
        // Get the dialog element
        self.onAfterBinding = function () {

        };
*/
        // hide the modal dialog
        self.can_hide = false;
        self.hideDialog = function () {
            self.can_hide = true;
            $("#octolapse_edit_settings_main_dialog").modal("hide");
        };

        self.showEditMainSettingsPopup = function () {
            //console.log("showing main settings")
            self.dialog.$editDialog = $("#octolapse_edit_settings_main_dialog");
            self.dialog.$editForm = $("#octolapse_edit_main_settings_form");
            self.dialog.$cancelButton = $(".cancel", self.dialog.$editDialog);
            self.dialog.$closeIcon = $("a.close", self.dialog.$editDialog);
            self.dialog.$saveButton = $(".save", self.dialog.$editDialog);
            self.dialog.$defaultButton = $(".set-defaults", self.dialog.$editDialog);
            self.dialog.$summary = self.dialog.$editForm.find("#edit_validation_summary");
            self.dialog.$errorCount = self.dialog.$summary.find(".error-count");
            self.dialog.$errorList = self.dialog.$summary.find("ul.error-list");
            self.dialog.$modalBody = self.dialog.$editDialog.find(".modal-body");
            self.dialog.$modalHeader = self.dialog.$editDialog.find(".modal-header");
            self.dialog.$modalFooter = self.dialog.$editDialog.find(".modal-footer");
            self.dialog.rules = {
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
                    self.dialog.$errorCount.empty();
                    self.dialog.$summary.show();
                    var numErrors = self.dialog.validator.numberOfInvalids();
                    if (numErrors === 1)
                        self.dialog.$errorCount.text("1 field is invalid");
                    else
                        self.dialog.$errorCount.text(numErrors + " fields are invalid");
                },
                errorContainer: "#edit_validation_summary",
                success: function (label) {
                    label.html("&nbsp;");
                    label.parent().addClass('checked');
                    $(label).parent().parent().parent().removeClass('error');
                },
                onfocusout: function (element, event) {
                      setTimeout(function() {
                        if (self.dialog.validator)
                        {
                            self.dialog.validator.form();
                        }
                    }, 250);
                },
                onclick: function (element, event) {
                    //setTimeout(() => self.dialog.validator.form(), 250);
                    setTimeout(function() {
                        self.dialog.validator.form();
                        self.dialog.resize();
                    }, 250);
                }
            };
            self.dialog.resize = function(){
            };
            self.dialog.validator = null;

            self.dialog.$editDialog.on("hide.bs.modal", function () {
                if (!self.can_hide)
                    return false;
                // Clear out error summary
                self.dialog.$errorCount.empty();
                self.dialog.$errorList.empty();
                self.dialog.$summary.hide();
                // Destroy the validator if it exists, both to save on resources, and to clear out any leftover junk.
                if (self.dialog.validator != null) {
                    self.dialog.validator.destroy();
                    self.dialog.validator = null;
                }
            });
            self.dialog.$editDialog.on("show.bs.modal", function () {
                self.main_settings.update(Octolapse.Globals.main_settings.toJS());
            });
            self.dialog.$editDialog.on("shown.bs.modal", function () {
                self.can_hide = false;
                // bind any help links
                Octolapse.Help.bindHelpLinks("#octolapse_edit_settings_main_dialog");
                // Create all of the validation rules

                self.dialog.validator = self.dialog.$editForm.validate(self.dialog.rules);

                // Remove any click event bindings from the cancel button
                self.dialog.$cancelButton.unbind("click");
                self.dialog.$closeIcon.unbind("click");
                // Called when the user clicks the cancel button in any add/update dialog
                self.dialog.$cancelButton.bind("click", self.hideDialog);
                self.dialog.$closeIcon.bind("click", self.hideDialog);

                // remove any click event bindings from the defaults button
                self.dialog.$defaultButton.unbind("click");
                self.dialog.$defaultButton.bind("click", function () {
                    // Set the options to the current settings
                    if (self.defaults)
                        self.main_settings.update(self.defaults);
                });

                // Remove any click event bindings from the save button
                self.dialog.$saveButton.unbind("click");
                // Called when a user clicks the save button on any add/update self.dialog.
                self.dialog.$saveButton.bind("click", function ()
                {
                    if (self.dialog.$editForm.valid()) {
                        // the form is valid, add or update the profile
                        var data = self.main_settings.toJS();
                        data["client_id"] = Octolapse.Globals.client_id;
                        //console.log("Saving main settings.")
                        $.ajax({
                            url: "./plugin/octolapse/saveMainSettings",
                            type: "POST",
                            data: JSON.stringify(data),
                            contentType: "application/json",
                            dataType: "json",
                            success: function (results) {
                                if (results.success)
                                {
                                    self.hideDialog();
                                    Octolapse.Globals.main_settings.update(data);
                                }
                                else {
                                    var options = {
                                        title: 'Main Settings Save Error',
                                        text: results.error,
                                        type: 'error',
                                        hide: false,
                                        addclass: "octolapse",
                                        desktop: {
                                            desktop: false
                                        }
                                    };
                                    Octolapse.displayPopupForKey(options, "settings-error", ["settings-error"]);
                                }

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
                                        desktop: false
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
                        var $fieldErrors = self.dialog.$editForm.find('.error_label_container.error');
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
                        $(self.dialog.$editDialog).addClass('shake');
                        // set a timeout so the dialog stops shaking
                        setTimeout(function () { $(self.dialog.$editDialog).removeClass('shake'); }, 500);
                    }

                });
                // Resize the dialog
                self.dialog.resize();
            });
            self.dialog.$editDialog.modal({
                backdrop: 'static',
                maxHeight: function() {
                    return Math.max(
                      window.innerHeight - self.dialog.$modalHeader.outerHeight()-self.dialog.$modalFooter.outerHeight()-66,
                      200
                    );
                }
            });

        };


    };

    // Bind the settings view model to the plugin settings element
    OCTOPRINT_VIEWMODELS.push([
        Octolapse.MainSettingsViewModel
        , ["settingsViewModel"]
        , ["#octolapse_main_tab"]
    ]);
});

