/// Create our stabilizations view model
$(function () {
    
    Octolapse.SnapshotProfileViewModel = function (values) {
        var self = this;

        self.guid = ko.observable(values.guid);
        self.name = ko.observable(values.name);
        self.description = ko.observable(values.description);
        self.gcode_trigger_enabled = ko.observable(values.gcode_trigger_enabled);
        self.gcode_trigger_require_zhop = ko.observable(values.gcode_trigger_require_zhop);
        self.gcode_trigger_on_extruding = ko.observable(values.gcode_trigger_on_extruding);
        self.gcode_trigger_on_extruding_start = ko.observable(values.gcode_trigger_on_extruding_start);
        self.gcode_trigger_on_primed = ko.observable(values.gcode_trigger_on_primed);
        self.gcode_trigger_on_retracting_start = ko.observable(values.gcode_trigger_on_retracting_start);
        self.gcode_trigger_on_retracting = ko.observable(values.gcode_trigger_on_retracting);
        self.gcode_trigger_on_partially_retracted = ko.observable(values.gcode_trigger_on_partially_retracted);
        self.gcode_trigger_on_retracted = ko.observable(values.gcode_trigger_on_retracted);
        self.gcode_trigger_on_detracting_start = ko.observable(values.gcode_trigger_on_detracting_start);
        self.gcode_trigger_on_detracting = ko.observable(values.gcode_trigger_on_detracting);
        self.gcode_trigger_on_detracted = ko.observable(values.gcode_trigger_on_detracted);

        self.timer_trigger_enabled = ko.observable(values.timer_trigger_enabled);
        self.timer_trigger_seconds = ko.observable(values.timer_trigger_seconds);
        self.timer_trigger_require_zhop = ko.observable(values.timer_trigger_require_zhop);
        self.timer_trigger_on_extruding = ko.observable(values.timer_trigger_on_extruding);
        self.timer_trigger_on_extruding_start = ko.observable(values.timer_trigger_on_extruding_start);
        self.timer_trigger_on_primed = ko.observable(values.timer_trigger_on_primed);
        self.timer_trigger_on_retracting_start = ko.observable(values.timer_trigger_on_retracting_start);
        self.timer_trigger_on_retracting = ko.observable(values.timer_trigger_on_retracting);
        self.timer_trigger_on_partially_retracted = ko.observable(values.timer_trigger_on_partially_retracted);
        self.timer_trigger_on_retracted = ko.observable(values.timer_trigger_on_retracted);
        self.timer_trigger_on_detracting_start = ko.observable(values.timer_trigger_on_detracting_start);
        self.timer_trigger_on_detracting = ko.observable(values.timer_trigger_on_detracting);
        self.timer_trigger_on_detracted = ko.observable(values.timer_trigger_on_detracted);

        self.layer_trigger_enabled = ko.observable(values.layer_trigger_enabled);
        self.layer_trigger_height = ko.observable(values.layer_trigger_height);
        self.layer_trigger_require_zhop = ko.observable(values.layer_trigger_require_zhop);
        self.layer_trigger_on_extruding = ko.observable(values.layer_trigger_on_extruding);
        self.layer_trigger_on_extruding_start = ko.observable(values.layer_trigger_on_extruding_start);
        self.layer_trigger_on_primed = ko.observable(values.layer_trigger_on_primed);
        self.layer_trigger_on_retracting_start = ko.observable(values.layer_trigger_on_retracting_start);
        self.layer_trigger_on_retracting = ko.observable(values.layer_trigger_on_retracting);
        self.layer_trigger_on_partially_retracted = ko.observable(values.layer_trigger_on_partially_retracted);
        self.layer_trigger_on_retracted = ko.observable(values.layer_trigger_on_retracted);
        self.layer_trigger_on_detracting_start = ko.observable(values.layer_trigger_on_detracting_start);
        self.layer_trigger_on_detracting = ko.observable(values.layer_trigger_on_detracting);
        self.layer_trigger_on_detracted = ko.observable(values.layer_trigger_on_detracted);

        self.delay = ko.observable(values.delay);
        self.retract_before_move = ko.observable(values.retract_before_move);
        self.cleanup_after_render_complete = ko.observable(values.cleanup_after_render_complete);
        self.cleanup_after_render_fail = ko.observable(values.cleanup_after_render_fail);

    };
    Octolapse.SnapshotProfileValidationRules = {
        rules: {
        },
        messages: {
            name: "Please enter a name for your profile"
            
        }
    };
});


