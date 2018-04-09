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
$(function() {
    Octolapse.DebugProfileViewModel = function (values) {
        var self = this;
        self.profileTypeName = ko.observable("Debug")
        self.guid = ko.observable(values.guid);
        self.name = ko.observable(values.name);
        self.description = ko.observable(values.description);
        self.enabled = ko.observable(values.enabled);
        self.is_test_mode = ko.observable(values.is_test_mode);
        self.log_to_console = ko.observable(values.log_to_console);
        self.position_change = ko.observable(values.position_change);
        self.position_command_received = ko.observable(values.position_command_received);
        self.extruder_change = ko.observable(values.extruder_change);
        self.extruder_triggered = ko.observable(values.extruder_triggered);
        self.trigger_create = ko.observable(values.trigger_create);
        self.trigger_wait_state = ko.observable(values.trigger_wait_state);
        self.trigger_triggering = ko.observable(values.trigger_triggering);
        self.trigger_triggering_state = ko.observable(values.trigger_triggering_state);
        self.trigger_layer_change = ko.observable(values.trigger_layer_change);
        self.trigger_height_change = ko.observable(values.trigger_height_change);
        self.trigger_zhop = ko.observable(values.trigger_zhop);
        self.trigger_time_unpaused = ko.observable(values.trigger_time_unpaused);
        self.trigger_time_remaining = ko.observable(values.trigger_time_remaining);
        self.snapshot_gcode = ko.observable(values.snapshot_gcode);
        self.snapshot_gcode_endcommand = ko.observable(values.snapshot_gcode_endcommand);
        self.snapshot_position = ko.observable(values.snapshot_position);
        self.snapshot_position_return = ko.observable(values.snapshot_position_return);
        self.snapshot_position_resume_print = ko.observable(values.snapshot_position_resume_print);
        self.snapshot_save = ko.observable(values.snapshot_save);
        self.snapshot_download = ko.observable(values.snapshot_download);
        self.render_start = ko.observable(values.render_start);
        self.render_complete = ko.observable(values.render_complete);
        self.render_fail = ko.observable(values.render_fail);
        self.render_sync = ko.observable(values.render_sync);
        self.snapshot_clean = ko.observable(values.snapshot_clean);
        self.settings_save = ko.observable(values.settings_save);
        self.settings_load = ko.observable(values.settings_load);
        self.print_state_changed = ko.observable(values.print_state_changed);
        self.camera_settings_apply = ko.observable(values.camera_settings_apply);
        self.gcode_sent_all = ko.observable(values.gcode_sent_all);
        self.gcode_queuing_all = ko.observable(values.gcode_queuing_all);
        self.gcode_received_all = ko.observable(values.gcode_received_all);

    };
    Octolapse.DebugProfileValidationRules = {
        rules: {
            name: "required"
        },
        messages: {
            name: "Please enter a name for your profile"
        }
    };
});


