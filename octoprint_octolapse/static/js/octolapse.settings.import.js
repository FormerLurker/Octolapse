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

    Octolapse.SettingsImportViewModel = function () {
        // Create a reference to this object
        var self = this;
        self.options = {};
        // variables
        self.import_method = ko.observable();
        self.import_text = ko.observable("");
        self.import_file_path = ko.observable();
        // Options
        self.options.import_types = ko.observable();
        self.options.import_methods = ko.observable();
        // control refs
        self.$dialog = null;
        self.$importFileUploadElement = null;
        self.$progressBar = null;
        self.current_upload_data = null;
        self.initialize = function () {
            self.initSettingsFileUpload();
        };

        self.update = function (settings) {
            self.options.import_methods(settings.global_options.import_options.settings_import_methods);
        };

        self.importSettings = function () {
            if (self.import_method() == 'text') {
                //console.log("Importing Settings from Text");
                var data = {
                    'import_method': self.import_method(),
                    'import_text': self.import_text(),
                    'client_id': Octolapse.Globals.client_id
                };
                $.ajax({
                    url: "./plugin/octolapse/importSettings",
                    type: "POST",
                    data: JSON.stringify(data),
                    contentType: "application/json",
                    dataType: "json",
                    success: function (data) {
                        var message = data.msg;
                        if (!data.success) {
                            var options = {
                                title: 'Unable To Import Settings',
                                text: message,
                                type: 'error',
                                hide: false,
                                addclass: "octolapse",
                                desktop: {
                                    desktop: false
                                }
                            };
                            Octolapse.displayPopupForKey(options, "settings_import_error", ["settings_import_error"]);
                            return;
                        }
                        self.import_text("");
                        var settings = JSON.parse(data.settings);

                        Octolapse.Settings.updateSettings(settings);
                        Octolapse.Globals.main_settings.update(settings.main_settings);
                        // maybe add a success popup?
                        var options = {
                            title: 'Settings Imported',
                            text: message,
                            type: 'success',
                            hide: true,
                            addclass: "octolapse",
                            desktop: {
                                desktop: false
                            }
                        };
                        Octolapse.displayPopup(options);
                        self.closeSettingsImportPopup();
                        Octolapse.Settings.checkForProfileUpdates();
                    },
                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                        var message = "Unable to import the provided settings:(  Status: " + textStatus + ".  Error: " + errorThrown;
                        var options = {
                            title: 'Settings Import Error',
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
            } else {
                //console.log("Importing Settings from File");
                if (self.current_upload_data != null) {
                    self.current_upload_data.submit();
                    self.current_upload_data = null;
                }
            }
        };

        self.submitFileData = null;
        self.hasImportSettingsFile = function () {
            return self.current_upload_data != null;
        };

        self.initSettingsFileUpload = function () {
            // Set up the file upload button.
            self.$importFileUploadElement = $('#octolapse_settings_import_path_upload');
            var $progressBarContainer = $('#octolapse_upload_settings_progress');
            self.$progressBar = $progressBarContainer.find('.progress-bar');
            self.$importFileUploadElement.fileupload({
                dataType: "json",
                maxNumberOfFiles: 1,
                autoUpload: false,
                //headers: OctoPrint.getRequestHeaders(),
                // Need to chunk large image files or else OctoPrint/Flask will reject them.
                // TODO: Octoprint limits file upload size on a per-endpoint basis.
                // http://docs.octoprint.org/en/master/plugins/hooks.html#octoprint-server-http-bodysize
                // maxChunkSize: 100000,
                formData: {client_id: Octolapse.Globals.client_id},
                dropZone: "#octolapse_settings_import_dialog .octolapse_dropzone",
                add: function (e, data) {
                    //console.log("Adding file");
                    self.$progressBar.text("");
                    self.$progressBar.removeClass('failed').animate({'width': '0%'}, {'queue': false});
                    self.current_upload_data = data;
                    self.$dialog.validator.form();
                    self.import_file_path(data.files[0].name);
                    //self.$importFileUploadElement.data('data-is-valid',true);
                    //self.submitFileData = function(){
                    //    data.submit();
                    //};
                },
                progressall: function (e, data) {
                    // TODO: Get a better progress bar implementation.
                    //console.log("Uploading Progress");
                    var progress = parseInt(data.loaded / data.total * 100, 10);
                    self.$progressBar.text(progress + "%");
                    self.$progressBar.animate({'width': progress + '%'}, {'queue': false});
                },

                done: function (e, data) {
                    //console.log("Upload Done");
                    var message = data.result.msg;
                    if (!data.result.success) {
                        var options = {
                            title: 'Unable To Import Settings',
                            text: message,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse",
                            desktop: {
                                desktop: false
                            }
                        };
                        Octolapse.displayPopupForKey(options, "settings_import_error", ["settings_import_error"]);
                        return;
                    }
                    var settings = JSON.parse(data.result.settings);

                    Octolapse.Settings.updateSettings(settings);
                    Octolapse.Globals.main_settings.update(settings.main_settings);
                    self.$progressBar.text("");
                    self.$progressBar.animate({'width': '0%'}, {'queue': false});
                    self.closeSettingsImportPopup();
                    // maybe add a success popup?
                    var options = {
                        title: 'Settings Imported',
                        text: message,
                        type: 'success',
                        hide: true,
                        addclass: "octolapse",
                        desktop: {
                            desktop: false
                        }
                    };
                    Octolapse.displayPopup(options);
                    Octolapse.Settings.checkForProfileUpdates();
                },
                fail: function (e, data) {
                    //console.log("Upload Failed");
                    self.$progressBar.text("Failed...").addClass('failed');
                    self.$progressBar.animate({'width': '100%'}, {'queue': false});
                },
                complete: function (e) {
                    //console.log("Upload Complete");
                    self.import_file_path("");
                }
            });
        };

        self.showSettingsImportPopup = function () {
            //console.log("showing import settings")
            self.$dialog = this;
            self.$dialog.$editDialog = $("#octolapse_settings_import_dialog");
            self.$dialog.$editForm = $("#octolapse_settings_import_form");
            self.$dialog.$cancelButton = self.$dialog.$editDialog.find("a.cancel");
            self.$dialog.$closeIcon = $("a.close", self.$dialog.$editDialog);
            self.$dialog.$saveButton = self.$dialog.$editDialog.find("button.save");
            self.$dialog.$summary = self.$dialog.$editForm.find("#settings_import_validation_summary");
            self.$dialog.$errorCount = self.$dialog.$summary.find(".error-count");
            self.$dialog.$errorList = self.$dialog.$summary.find("ul.error-list");
            self.$dialog.$modalBody = self.$dialog.$editDialog.find(".modal-body");
            self.$dialog.$modalHeader = self.$dialog.$editDialog.find(".modal-header");
            self.$dialog.$modalFooter = self.$dialog.$editDialog.find(".modal-footer");
            self.$dialog.rules = {
                rules: Octolapse.SettingsImportValidationRules.rules,
                messages: Octolapse.SettingsImportValidationRules.messages,
                ignore: ".ignore_hidden_errors:hidden, .ignore_hidden_errors.hiding",
                errorPlacement: function (error, element) {
                    var error_id = $(element).attr("name");
                    var $field_error = self.$dialog.$editDialog.find(".error_label_container[data-error-for='" + error_id + "']");
                    $field_error.html(error);
                },
                highlight: function (element, errorClass) {
                    var error_id = $(element).attr("name");
                    var $field_error = self.$dialog.$editDialog.find(".error_label_container[data-error-for='" + error_id + "']");
                    $field_error.removeClass("checked");
                    $field_error.addClass(errorClass);
                },
                unhighlight: function (element, errorClass) {
                    var error_id = self.$dialog.$editDialog.find(element).attr("name");
                    var $field_error = $(".error_label_container[data-error-for='" + error_id + "']");
                    $field_error.addClass("checked");
                    $field_error.removeClass(errorClass);
                },
                invalidHandler: function () {
                    self.$dialog.$errorCount.empty();
                    self.$dialog.$summary.show();
                    var numErrors = self.$dialog.validator.numberOfInvalids();
                    if (numErrors === 1)
                        self.$dialog.$errorCount.text("1 field is invalid");
                    else
                        self.$dialog.$errorCount.text(numErrors + " fields are invalid");
                },
                errorContainer: "#settings_import_validation_summary",
                success: function (label) {
                    label.html("&nbsp;");
                    label.parent().addClass('checked');
                    $(label).parent().parent().parent().removeClass('error');
                },
                onfocusout: function (element, event) {
                    setTimeout(function () {
                        if (self.$dialog.validator) {
                            self.$dialog.validator.form();
                        }
                    }, 250);
                },
                onclick: function (element, event) {
                    setTimeout(function () {
                        self.$dialog.validator.form();
                        self.resize();
                    }, 250);
                }
            };
            self.resize = function () {
                /*self.$dialog.$editDialog.css("top","0px").css(
                    'margin-top',
                    Math.max(0 - self.$dialog.$editDialog.height() / 2, 0)
                );*/
            };
            self.$dialog.validator = null;
            //console.log("Adding validator to main setting dialog.")
            self.$dialog.$editDialog.on("hide.bs.modal", function () {
                if (!self.can_hide)
                    return false;
                // Clear out error summary
                self.$dialog.$errorCount.empty();
                self.$dialog.$errorList.empty();
                self.$dialog.$summary.hide();
                // Destroy the validator if it exists, both to save on resources, and to clear out any leftover junk.
                if (self.$dialog.validator != null) {
                    self.$dialog.validator.destroy();
                    self.$dialog.validator = null;
                }
            });

            self.$dialog.$editDialog.on("shown.bs.modal", function () {
                //console.log("Octolapse import dialog is shown.");
                Octolapse.Help.bindHelpLinks("#octolapse_settings_import_dialog");
                // Create all of the validation rules

                self.$dialog.validator = self.$dialog.$editForm.validate(self.$dialog.rules);
                //self.$dialog.validator.form();
                // Remove any click event bindings from the cancel button
                self.$dialog.$cancelButton.unbind("click");
                // Called when the user clicks the cancel button in any add/update dialog
                self.$dialog.$cancelButton.bind("click", self.closeSettingsImportPopup);
                self.$dialog.$closeIcon.bind("click", self.closeSettingsImportPopup);
                // Remove any click event bindings from the save button
                self.$dialog.$saveButton.unbind("click");
                // Called when a user clicks the save button on any add/update dialog.

                self.$dialog.$saveButton.bind("click", function () {
                    //console.log("Save button clicked.");
                    if (self.$dialog.$editForm.valid()) {
                        //console.log("Importing Settings.");
                        // the form is valid, add or update the profile
                        self.importSettings();
                    } else {
                        // Search for any hidden elements that are invalid
                        //console.log("Checking ofr hidden field error");
                        var $fieldErrors = self.$dialog.$editForm.find('.error_label_container.error');
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
                        $(self.$dialog.$editDialog).addClass('shake');
                        // set a timeout so the dialog stops shaking
                        setTimeout(function () {
                            $(self.$dialog.$editDialog).removeClass('shake');
                        }, 500);
                    }

                });

                // see if the current viewmodel has an on_opened function
                if (typeof self.on_opened === 'function') {
                    // call the function
                    self.on_opened();
                }
            });
            self.$dialog.$editDialog.modal({
                    backdrop: 'static',

                    maxHeight: function () {
                        return Math.max(
                            window.innerHeight -
                            self.$dialog.$modalHeader.outerHeight() -
                            self.$dialog.$modalFooter.outerHeight() - 66,
                            200
                        );
                    }
                }
            );
        };
        self.can_hide = false;
        self.closeSettingsImportPopup = function () {
            if (self.$dialog != null) {
                self.can_hide = true;
                self.$dialog.$editDialog.modal("hide");
            }
        };

        self.on_opened = function () {
            //console.log("Opening settings import dialog.")
            if (self.$importFileUploadElement === null)
                return;
            self.$importFileUploadElement.empty();
            self.import_file_path("");
            self.$progressBar.text("");
            self.$progressBar.animate({'width': '0%'}, {'queue': false});
        };

        Octolapse.SettingsImportValidationRules = {
            rules: {
                octolapse_settings_import_path_upload: {uploadFileRequired: [self.hasImportSettingsFile]},
            },
            messages: {}
        };


    };
});

