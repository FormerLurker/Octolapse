/// Create our stabilizations view model
$(function () {
    
    Octolapse.SnapshotProfileViewModel = function(values) {
        self = this
        self.name = ko.observable(values.name);
        self.guid = ko.observable(values.guid);
        self.gcode_trigger_enabled =                ko.observable(values.gcode_trigger_enabled);
        self.gcode_trigger_require_zhop =           ko.observable(values.gcode_trigger_require_zhop);
        self.gcode_trigger_on_extruding =           ko.observable(values.gcode_trigger_on_extruding);
        self.gcode_trigger_on_extruding_start =     ko.observable(values.gcode_trigger_on_extruding_start);
        self.gcode_trigger_on_primed =              ko.observable(values.gcode_trigger_on_primed);
        self.gcode_trigger_on_retracting_start =    ko.observable(values.gcode_trigger_on_retracting_start);
        self.gcode_trigger_on_retracting =          ko.observable(values.gcode_trigger_on_retracting);
        self.gcode_trigger_on_partially_retracted = ko.observable(values.gcode_trigger_on_partially_retracted);
        self.gcode_trigger_on_retracted =           ko.observable(values.gcode_trigger_on_retracted);
        self.gcode_trigger_on_detracting_start =    ko.observable(values.gcode_trigger_on_detracting_start);
        self.gcode_trigger_on_detracting =          ko.observable(values.gcode_trigger_on_detracting);
        self.gcode_trigger_on_detracted =           ko.observable(values.gcode_trigger_on_detracted);

        self.timer_trigger_enabled =                ko.observable(values.timer_trigger_enabled);
        self.timer_trigger_seconds =                ko.observable(values.timer_trigger_seconds);
        self.timer_trigger_require_zhop =           ko.observable(values.timer_trigger_require_zhop);
        self.timer_trigger_on_extruding =           ko.observable(values.timer_trigger_on_extruding);
        self.timer_trigger_on_extruding_start =     ko.observable(values.timer_trigger_on_extruding_start);
        self.timer_trigger_on_primed =              ko.observable(values.timer_trigger_on_primed);
        self.timer_trigger_on_retracting_start =    ko.observable(values.timer_trigger_on_retracting_start);
        self.timer_trigger_on_retracting =          ko.observable(values.timer_trigger_on_retracting);
        self.timer_trigger_on_partially_retracted = ko.observable(values.timer_trigger_on_partially_retracted);
        self.timer_trigger_on_retracted =           ko.observable(values.timer_trigger_on_retracted);
        self.timer_trigger_on_detracting_start =    ko.observable(values.timer_trigger_on_detracting_start);
        self.timer_trigger_on_detracting =          ko.observable(values.timer_trigger_on_detracting);
        self.timer_trigger_on_detracted =           ko.observable(values.timer_trigger_on_detracted);

        self.layer_trigger_enabled =                ko.observable(values.layer_trigger_enabled);
        self.layer_trigger_height =                 ko.observable(values.layer_trigger_height);
        self.layer_trigger_require_zhop =           ko.observable(values.layer_trigger_require_zhop);
        self.layer_trigger_on_extruding =           ko.observable(values.layer_trigger_on_extruding);
        self.layer_trigger_on_extruding_start =     ko.observable(values.layer_trigger_on_extruding_start);
        self.layer_trigger_on_primed =              ko.observable(values.layer_trigger_on_primed);
        self.layer_trigger_on_retracting_start =    ko.observable(values.layer_trigger_on_retracting_start);
        self.layer_trigger_on_retracting =          ko.observable(values.layer_trigger_on_retracting);
        self.layer_trigger_on_partially_retracted = ko.observable(values.layer_trigger_on_partially_retracted);
        self.layer_trigger_on_retracted =           ko.observable(values.layer_trigger_on_retracted);
        self.layer_trigger_on_detracting_start =    ko.observable(values.layer_trigger_on_detracting_start);
        self.layer_trigger_on_detracting =          ko.observable(values.layer_trigger_on_detracting);
        self.layer_trigger_on_detracted =           ko.observable(values.layer_trigger_on_detracted);

        self.position_request_retry_attemps = ko.observable(values.position_request_retry_attemps);
        self.position_request_retry_delay_ms = ko.observable(values.position_request_retry_delay_ms);
        self.archive = ko.observable(values.archive);
        self.delay = ko.observable(values.delay);
        self.retract_before_move = ko.observable(values.retract_before_move);
        self.output_format = ko.observable(values.output_format);
        self.output_filename = ko.observable(values.output_filename);
        self.output_directory = ko.observable(values.output_directory);
        self.cleanup_before_print = ko.observable(values.cleanup_before_print);
        self.cleanup_after_print = ko.observable(values.cleanup_after_print);
        self.cleanup_after_cancel = ko.observable(values.cleanup_after_cancel);
        self.cleanup_after_fail = ko.observable(values.cleanup_after_fail);
        self.cleanup_before_close = ko.observable(values.cleanup_before_close);
        self.cleanup_after_render_complete = ko.observable(values.cleanup_after_render_complete);
        self.cleanup_after_render_fail = ko.observable(values.cleanup_after_render_fail);
        self.custom_script_enabled = ko.observable(values.custom_script_enabled);
        self.script_path = ko.observable(values.script_path);
    }
    Octolapse.SnapshotProfileValidationRules = {
        rules: {
            name: "required",
            script_path: "required"
        },
        messages: {
            name: "Please enter a name for your profile",
            script_path: "Please enter a path to your custom script"
        }
    };
});


