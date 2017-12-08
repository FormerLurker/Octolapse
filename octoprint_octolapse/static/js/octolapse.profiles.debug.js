
/// Create our stabilizations view model
$(function() {
    Octolapse.DebugProfileViewModel = function(values) {
        self = this
        self.name = ko.observable(values.name);
        self.guid = ko.observable(values.guid);
        self.enabled = ko.observable(values.enabled);
        self.position_change = ko.observable(values.position_change);
        self.position_command_received = ko.observable(values.position_command_received);
        self.extruder_change = ko.observable(values.extruder_change);
        self.extruder_triggered = ko.observable(values.extruder_triggered);
        self.trigger_create = ko.observable(values.trigger_create);
        self.trigger_wait_state = ko.observable(values.trigger_wait_state);
        self.trigger_triggering = ko.observable(values.trigger_triggering);
        self.trigger_triggering_state = ko.observable(values.trigger_triggering_state);
        self.trigger_layer_zmin_reached = ko.observable(values.trigger_layer_zmin_reached);
        self.trigger_layer_change = ko.observable(values.trigger_layer_change);
        self.trigger_height_change = ko.observable(values.trigger_height_change);
        self.trigger_zhop = ko.observable(values.trigger_zhop);
        self.trigger_time_unpaused = ko.observable(values.trigger_time_unpaused);
        self.trigger_time_remaining = ko.observable(values.trigger_time_remaining);
        self.snapshot_gcode = ko.observable(values.snapshot_gcode);
        self.snapshot_gcode_endcommand = ko.observable(values.snapshot_gcode_endcommand);
        self.snapshot_position = ko.observable(values.snapshot_position);
        self.snapshot_position_return = ko.observable(values.snapshot_position_return);
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
    }
    Octolapse.DebugProfileValidationRules = {
        rules: {
            name: "required"
        },
        messages: {
            name: "Please enter a name for your profile",
        }
    };
});


