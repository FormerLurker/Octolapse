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
    // Functions to create a dialog with custom validation and callbacks
    Octolapse.OctolapseDialog = function (dialog_id, template_id, options) {
        var self = this;
        self.dialog_id = ko.observable(dialog_id);
        self.template_id = ko.observable(template_id);
        self.title = ko.observable("Octolapse Dialog");
        self.dialog_selector = "#" + dialog_id;
        self.is_open = false;
        // Callbacks
        self.on_opened = null;
        self.on_closed = null;
        self.on_resize = null;
        // Buttons
        // cancel
        self.cancel_button_visible = ko.observable(true);
        self.cancel_button_title = ko.observable("Cancel and close the dialog.");
        self.cancel_button_text = ko.observable("Cancel");

        // Configure Help
        self.help_enabled = ko.observable();
        self.help_link = ko.observable();
        self.help_tooltip = ko.observable();
        self.help_title = ko.observable();

        self.set_help = function(enabled, link, tooltip, title)
        {
            self.help_enabled(enabled);
            self.help_link(link || "");
            self.help_tooltip(tooltip || "Click for help with this.");
            self.help_title(title || "Help");
        };

        self.set_help(
            !!options.help_enabled,
            options.help_link,
            options.help_tooltip,
            options.help_title
        );

        self.on_cancel_button_clicked = function() {
            self.close();
        };
        self.cancel_button_clicked = function() {
            if (self.on_cancel_button_clicked)
            {
                self.on_cancel_button_clicked();
            }
        };
        // option
        self.option_button_visible = ko.observable(false);
        self.option_button_title = ko.observable("Option");
        self.option_button_text = ko.observable("Option");
        self.option_button_clicked = function() {
            if(self.on_option_button_clicked)
            {
                self.on_option_button_clicked();
            }
        };
        // ok
        self.ok_button_visible = ko.observable(false);
        self.ok_button_title = ko.observable("OK");
        self.ok_button_text = ko.observable("OK");
        self.ok_button_clicked = function() {
            if(self.on_ok_button_clicked)
            {
                self.on_ok_button_clicked();
            }
        };
        // Must be called after the viewmodels are bound, else the dialog won't open
        self.on_after_binding = function() {
            // Set jquery variables
            self.$dialog = this;
            self.$editDialog = $(self.dialog_selector);
            self.$editForm = self.$editDialog.find("form");
            self.$cancelButton = self.$editDialog.find("button.cancel");
            self.$closeIcon = $("a.close", self.$editDialog);
            self.$optionButton = self.$editDialog.find("button.option");
            self.$okButton = self.$editDialog.find("button.ok");
            self.$summary = self.$editForm.find(".validation_summary");
            self.$errorCount = self.$summary.find(".error-count");
            self.$errorList = self.$summary.find("ul.error-list");
            self.$modalBody = self.$editDialog.find(".modal-body");
            self.$modalHeader = self.$editDialog.find(".modal-header");
            self.$modalFooter = self.$editDialog.find(".modal-footer");
            // Called before a dialog is closed
            self.$editDialog.on("hide.bs.modal", function () {
                if (!self.can_hide)
                    return false;
                // Clear out error summary
                self.$errorCount.empty();
                self.$errorList.empty();
                self.$summary.hide();
                self.unbind_validator();
            });

            // Called after a dialog is hidden
            self.$editDialog.on("hidden.bs.modal", function () {
                self.is_open = false;
                // see if the current viewmodel has an on_closed function
                if (typeof self.on_closed === 'function') {
                    // call the function
                    self.on_closed();
                }
            });

            // Called after a dialog is shown.
            self.$editDialog.on("shown.bs.modal", function () {
                //console.log("Octolapse import dialog is shown.");
                Octolapse.Help.bindHelpLinks(self.dialog_selector);
                // Create all of the validation rules

                self.bind_validator();
                // Button Configuration
                // Cancel and Close
                self.$closeIcon.bind("click", self.cancel_button_clicked);
                self.is_open = true;
                // see if the current viewmodel has an on_opened function
                if (typeof self.on_opened === 'function') {
                    // call the function
                    self.on_opened();
                }
            });

            // Validation Options
            self.validation_enabled = true;

            if (options) {
                // Configure Title
                self.title(options.title);

                // Configure Validation
                self.validation_enabled = options.validation_enabled !== undefined ? options.validation_enabled : self.validation_enabled;
                self.validation_options.rules = options.rules ? options.rules : self.rules;
                self.validation_options.messages = options.messages ? options.messages : self.messages;

                // Configure Callbacks
                self.on_opened = options.on_opened ? options.on_opened : self.on_opened;
                self.on_closed = options.on_closed ? options.on_closed : self.on_closed;
                self.on_resize = options.on_resize ? options.on_resize : self.on_resize;

                // Configure Buttons
                // Cancel
                self.cancel_button_visible(
                    options.cancel_button_visible !== undefined ? options.cancel_button_visible : self.cancel_button_visible()
                );
                self.cancel_button_title(
                    options.cancel_button_title ? options.cancel_button_title : self.cancel_button_title()
                );
                self.cancel_button_text(
                    options.cancel_button_text ? options.cancel_button_text : self.cancel_button_text()
                );
                self.on_cancel_button_clicked = options.on_cancel_button_clicked ? options.on_cancel_button_clicked : self.on_cancel_button_clicked;
                // Option
                self.option_button_visible(
                    options.option_button_visible !== undefined ? options.option_button_visible : self.option_button_visible()
                );
                self.option_button_title(
                    options.option_button_title ? options.option_button_title : self.option_button_title()
                );
                self.option_button_text(
                    options.option_button_text ? options.option_button_text : self.option_button_text()
                );
                self.on_option_button_clicked = self.option_button_clicked;
                // OK
                self.ok_button_visible(
                    options.ok_button_visible !== undefined ? options.ok_button_visible : self.ok_button_visible()
                );
                self.ok_button_title(
                    options.ok_button_title ? options.ok_button_title : self.ok_button_title()
                );
                self.ok_button_text(
                    options.ok_button_text ? options.ok_button_text : self.ok_button_text()
                );
                self.on_ok_button_clicked = self.ok_button_clicked;
            }
        };

        self.validation_options = {
            ignore: ".ignore_hidden_errors:hidden, .ignore_hidden_errors.hiding",
            errorPlacement: function (error, element) {
                var error_id = $(element).attr("name");
                var $field_error = self.$editDialog.find(".error_label_container[data-error-for='" + error_id + "']");
                $field_error.html(error);
            },
            highlight: function (element, errorClass) {
                var error_id = $(element).attr("name");
                var $field_error = self.$editDialog.find(".error_label_container[data-error-for='" + error_id + "']");
                $field_error.removeClass("checked");
                $field_error.addClass(errorClass);
            },
            unhighlight: function (element, errorClass) {
                var error_id = self.$editDialog.find(element).attr("name");
                var $field_error = $(".error_label_container[data-error-for='" + error_id + "']");
                $field_error.addClass("checked");
                $field_error.removeClass(errorClass);
            },
            invalidHandler: function () {
                self.$errorCount.empty();
                self.$summary.show();
                var numErrors = self.validator.numberOfInvalids();
                if (numErrors === 1)
                    self.$errorCount.text("1 field is invalid");
                else
                    self.$errorCount.text(numErrors + " fields are invalid");
            },
            errorContainer: "#settings_import_validation_summary",
            success: function (label) {
                label.html("&nbsp;");
                label.parent().addClass('checked');
                $(label).parent().parent().parent().removeClass('error');
            },
            onfocusout: function (element, event) {
                setTimeout(function () {
                    if (self.validator) {
                        self.validator.form();
                    }
                }, 250);
            },
            onclick: function (element, event) {
                setTimeout(function () {
                    self.validator.form();
                    //self.resize();
                }, 250);
            }
        };

        self.resize = function () {
            // create as callback
            if (self.on_resize) {
                self.on_resize();
            }
            else{
                $(window).trigger('resize');
            }
        };

        self.validator = null;
        self.unbind_validator = function () {
            // Destroy the validator if it exists, both to save on resources, and to clear out any leftover junk.
            if (self.validator != null) {
                self.validator.destroy();
                self.validator = null;
            }
        };
        self.bind_validator = function () {
            self.unbind_validator();
            if (self.validation_enabled) {
                self.validator = self.$editForm.validate(self.validation_options);
            }
        };
        //console.log("Adding validator to main setting dialog.")
        // Close the dialog.
        self.can_hide = false;
        self.close = function () {
            self.can_hide = true;
            self.$editDialog.modal("hide");
        };

        self.ok = function() {
            if (self.validation_enabled) {
                if (self.$editForm.valid()) {
                    //console.log("Importing Settings.");
                    // the form is valid, add or update the profile
                    self.ok_button_clicked();
                } else {
                    // Search for any hidden elements that are invalid
                    //console.log("Checking ofr hidden field error");
                    var $fieldErrors = self.$editForm.find('.error_label_container.error');
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
                    $(self.$editDialog).addClass('shake');
                    // set a timeout so the dialog stops shaking
                    setTimeout(function () {
                        $(self.$editDialog).removeClass('shake');
                    }, 500);
                }
            }
            else {
                if (self.ok_button_clicked)
                {
                    self.ok_button_clicked();
                }
            }
        };

        // Open the dialog.
        self.show = function () {
            // Only open the dialog if it is not already open.
            if (!self.is_open) {
                if (self.$editDialog.length !== 1)
                {
                    console.error("No dialog has been found to open.  Is the dialog id correct?");
                }
                self.$editDialog.modal({
                        backdrop: 'static',
                        resize: true,
                        maxHeight: function() {
                            return Math.max(
                              window.innerHeight - self.$modalHeader.outerHeight()-self.$modalFooter.outerHeight()-66,
                              200
                            );
                        }
                    }
                );
            }
            else{
                console.error("Cannot open a dialog that is already open.");
            }
        };

        self.get_help_link_element = function(){
            return $(self.dialog_selector + " a.octolapse_dialog_help");
        };
    };
});
