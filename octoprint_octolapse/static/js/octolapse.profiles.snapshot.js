/*
    This file is subject to the terms and conditions defined in
    a file called 'LICENSE', which is part of this source code package.
*/
$(function () {

    Octolapse.SnapshotProfileViewModel = function (values) {
        var self = this;
        self.guid = ko.observable(values.guid);
        self.name = ko.observable(values.name);
        self.description = ko.observable(values.description);

        /*
            Gcode Trigger Settings
        */
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
        /*
            Timer Trigger Settings
        */
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
        /*
            Layer/Height Trigger Settings
        */
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

        /*
        * Position Restrictions
        * */
        self.position_restrictions = ko.observableArray([]);
        for (var index = 0; index < values.position_restrictions.length; index++) {
            self.position_restrictions.push(
                ko.observable(values.position_restrictions[index]));
        }
        // Temporary variables to hold new layer position restrictions
        self.new_position_restriction_type = ko.observable('required');
        self.new_position_restriction_shape = ko.observable('rect');
        self.new_position_restriction_x = ko.observable(0);
        self.new_position_restriction_y = ko.observable(0);
        self.new_position_restriction_x2 = ko.observable(1);
        self.new_position_restriction_y2 = ko.observable(1);
        self.new_position_restriction_r = ko.observable(1);
        self.new_calculate_intersections = ko.observable(false);

        self.lift_before_move = ko.observable(values.lift_before_move);
        self.retract_before_move = ko.observable(values.retract_before_move);
        self.cleanup_after_render_complete = ko.observable(values.cleanup_after_render_complete);
        self.cleanup_after_render_fail = ko.observable(values.cleanup_after_render_fail);


        self.addPositionRestriction = function () {
            //console.log("Adding " + type + " position restriction.");
            var restriction = ko.observable({
                "Type": self.new_position_restriction_type(),
                "Shape": self.new_position_restriction_shape(),
                "X": self.new_position_restriction_x(),
                "Y": self.new_position_restriction_y(),
                "X2": self.new_position_restriction_x2(),
                "Y2": self.new_position_restriction_y2(),
                "R": self.new_position_restriction_r(),
                "CalculateIntersections": self.new_calculate_intersections()
            });
            self.position_restrictions.push(restriction);
        };

        self.removePositionRestriction = function (index) {
            //console.log("Removing " + type + " restriction at index: " + index());
            self.position_restrictions.splice(index(), 1);

        };
    }
    Octolapse.SnapshotProfileValidationRules = {
        rules: {
            /*Layer Position Restrictions*/
            new_position_restriction_x: { lessThan: "#octolapse_position_restriction_x2:visible" },
            new_position_restriction_x2: { greaterThan: "#octolapse_position_restriction_x:visible" },
            new_position_restriction_y: { lessThan: "#octolapse_position_restriction_y2:visible" },
            new_position_restriction_y2: { greaterThan: "#octolapse_position_restriction_y:visible" },
            layer_trigger_enabled: {check_one: ".octolapse_trigger_enabled"},
            gcode_trigger_enabled: {check_one: ".octolapse_trigger_enabled"},
            timer_trigger_enabled: {check_one: ".octolapse_trigger_enabled"},
        },
        messages: {
            name: "Please enter a name for your profile",
            /*Layer Position Restrictions*/
            new_position_restriction_x : { lessThan: "Must be less than the 'X2' field." },
            new_position_restriction_x2: { greaterThan: "Must be greater than the 'X' field." },
            new_position_restriction_y: { lessThan: "Must be less than the 'Y2." },
            new_position_restriction_y2: { greaterThan: "Must be greater than the 'Y' field." },
            layer_trigger_enabled: {check_one: "No triggers are enabled.  You must enable at least one trigger."},
            gcode_trigger_enabled: {check_one: "No triggers are enabled.  You must enable at least one trigger."},
            timer_trigger_enabled: {check_one: "No triggers are enabled.  You must enable at least one trigger."},
        }
    };
});


