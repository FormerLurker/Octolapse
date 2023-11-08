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
    Octolapse.LoggingProfileViewModel = function (values) {
        var self = this;
        self.profileTypeName = ko.observable("Logging");
        self.guid = ko.observable(values.guid);
        self.name = ko.observable(values.name);
        self.description = ko.observable(values.description);
        self.enabled = ko.observable(values.enabled);
        self.log_to_console = ko.observable(values.log_to_console);
        self.log_all_errors = ko.observable(values.log_all_errors);
        self.enabled_loggers = ko.observableArray();
        for (var index = 0; index < values.enabled_loggers.length; index++) {
            var curItem = values.enabled_loggers[index];
            self.enabled_loggers.push({'name': curItem.name, 'log_level': curItem.log_level});
        }

        self.logger_name_add = ko.observable();
        self.logger_level_add = ko.observable();
        self.default_log_level = values.default_log_level;

        self.get_enabled_logger_index_by_name = function (name) {
            for (var index = 0; index < self.enabled_loggers().length; index++) {
                var logger = self.enabled_loggers()[index];
                if (logger.name === name) {
                    return index;
                }
            }
            return -1;
        };
        self.available_loggers = ko.computed(function () {
            var available_loggers = [];
            for (var logger_index = 0; logger_index < Octolapse.LoggingProfiles.profileOptions.all_logger_names.length; logger_index++) {
                var logger_name = Octolapse.LoggingProfiles.profileOptions.all_logger_names[logger_index];
                var found_logger_index = self.get_enabled_logger_index_by_name(logger_name);
                if (found_logger_index === -1) {
                    available_loggers.push({'name': logger_name, 'log_level': self.default_log_level});
                }
            }
            return available_loggers;
        });

        self.loggerNameSort = function (observable) {
            return observable().sort(
                function (left, right) {
                    var leftName = left.name.toLowerCase();
                    var rightName = right.name.toLowerCase();
                    return leftName === rightName ? 0 : (leftName < rightName ? -1 : 1);
                });
        };
        self.available_loggers_sorted = ko.computed(function () {
            return self.loggerNameSort(self.available_loggers);
        });

        self.removeLogger = function (logger) {
            //console.log("removing logger.");
            self.enabled_loggers.remove(logger);
        };

        self.addLogger = function () {
            //console.log("Adding logger");
            var index = self.get_enabled_logger_index_by_name(self.logger_name_add());
            if (index === -1) {
                self.enabled_loggers.push({'name': self.logger_name_add(), 'log_level': self.logger_level_add()});
                self.scrollToBottom();
            }
        };

        // When adding loggers automatically scrolling to the bottom of the page
        // makes the control much more user friendly if you want to add several loggers.
        // TODO:  Scroll down only the width of a new control, which will be necessary if we add more controls below the logger controls.
        self.scrollToBottom = function () {
            var logging_container = document.getElementById("octolapse_add_edit_profile_model_body");
            logging_container.scrollTop = logging_container.scrollHeight;
        };

        self.updateFromServer = function (values) {
            self.name(values.name);
            self.description(values.description);
            self.enabled(values.enabled);
            self.log_to_console(values.log_to_console);
            self.log_all_errors(values.log_all_errors);
            self.enabled_loggers([]);
            for (var index = 0; index < values.enabled_loggers.length; index++) {
                var curItem = values.enabled_loggers[index];
                self.enabled_loggers.push({'name': curItem.name, 'log_level': curItem.log_level});
            }
        };

        self.clearLog = function (clear_all) {
            var title;
            var message;
            if (clear_all) {
                title = "Clear All Logs";
                message = "All octolapse log files will be cleared and deleted.  Are you sure?";
            } else {
                title = "Clear Log";
                message = "The most recent octolapse log file will be cleared.  Are you sure?";
            }
            Octolapse.showConfirmDialog(
                "clear_log",
                title,
                message,
                function () {
                    if (clear_all) {
                        title = "Logs Cleared";
                        message = "All octolapse log files have been cleared.";
                    } else {
                        title = "Most Recent Log Cleared";
                        message = "The most recent octolapse log file has been cleared.";
                    }
                    var data = {
                        clear_all: clear_all
                    };
                    $.ajax({
                        url: "./plugin/octolapse/clearLog",
                        type: "POST",
                        data: JSON.stringify(data),
                        contentType: "application/json",
                        dataType: "json",
                        success: function (data) {
                            var options = {
                                title: title,
                                text: message,
                                type: 'success',
                                hide: true,
                                addclass: "octolapse",
                                desktop: {
                                    desktop: false
                                }
                            };
                            Octolapse.displayPopupForKey(options, "log_file_cleared", "log_file_cleared");
                        },
                        error: function (XMLHttpRequest, textStatus, errorThrown) {
                            var message = "Unable to clear the log.:(  Status: " + textStatus + ".  Error: " + errorThrown;
                            var options = {
                                title: 'Clear Log Error',
                                text: message,
                                type: 'error',
                                hide: false,
                                addclass: "octolapse",
                                desktop: {
                                    desktop: false
                                }
                            };
                            Octolapse.displayPopupForKey(options, "log_file_cleared", "log_file_cleared");
                        }
                    });
                }
            );

        };

        self.automatic_configuration = new Octolapse.ProfileLibraryViewModel(
            values.automatic_configuration,
            Octolapse.LoggingProfiles.profileOptions.server_profiles,
            self.profileTypeName(),
            self,
            self.updateFromServer
        );

        self.toJS = function () {
            // need to remove the parent link from the automatic configuration to prevent a cyclic copy
            var parent = self.automatic_configuration.parent;
            self.automatic_configuration.parent = null;
            var copy = ko.toJS(self);
            self.automatic_configuration.parent = parent;
            return copy;
        };
        self.on_closed = function () {
            self.automatic_configuration.on_closed();
        };

        self.automatic_configuration.is_confirming.subscribe(function (value) {
            //console.log("IsClickable" + value.toString());
            Octolapse.LoggingProfiles.setIsClickable(!value);
        });

    };
    Octolapse.LoggingProfileValidationRules = {
        rules: {
            name: "required"
        },
        messages: {
            name: "Please enter a name for your profile"
        }
    };
});


