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
        self.gcode_trigger_position_restrictions = ko.observableArray([]);
        for (var index = 0; index < values.gcode_trigger_position_restrictions.length; index++) {
            self.gcode_trigger_position_restrictions.push(ko.observable(values.gcode_trigger_position_restrictions[index]));
        }
        // Temporary variables to hold new gcode position restrictions
        self.new_gcode_position_restriction_type = ko.observable('required')
        self.new_gcode_position_restriction_shape = ko.observable('rect')
        self.new_gcode_position_restriction_x = ko.observable(0)
        self.new_gcode_position_restriction_y = ko.observable(0)
        self.new_gcode_position_restriction_x2 = ko.observable(1)
        self.new_gcode_position_restriction_y2 = ko.observable(1)
        self.new_gcode_position_restriction_r = ko.observable(1)

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
        self.timer_trigger_position_restrictions = ko.observableArray([]);
        for (var index = 0; index < values.timer_trigger_position_restrictions.length; index++) {
            self.timer_trigger_position_restrictions.push(ko.observable(values.timer_trigger_position_restrictions[index]));
        }
        // Temporary variables to hold new timer position restrictions
        self.new_timer_position_restriction_type = ko.observable('required')
        self.new_timer_position_restriction_shape = ko.observable('rect')
        self.new_timer_position_restriction_x = ko.observable(0)
        self.new_timer_position_restriction_y = ko.observable(0)
        self.new_timer_position_restriction_x2 = ko.observable(1)
        self.new_timer_position_restriction_y2 = ko.observable(1)
        self.new_timer_position_restriction_r = ko.observable(1)

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
        self.layer_trigger_position_restrictions = ko.observableArray([]);
        for (var index = 0; index < values.layer_trigger_position_restrictions.length; index++) {
            self.layer_trigger_position_restrictions.push(ko.observable(values.layer_trigger_position_restrictions[index]));
        }
        // Temporary variables to hold new layer position restrictions
        self.new_layer_position_restriction_type = ko.observable('required')
        self.new_layer_position_restriction_shape = ko.observable('rect')
        self.new_layer_position_restriction_x = ko.observable(0)
        self.new_layer_position_restriction_y = ko.observable(0)
        self.new_layer_position_restriction_x2 = ko.observable(1)
        self.new_layer_position_restriction_y2 = ko.observable(1)
        self.new_layer_position_restriction_r = ko.observable(1)

        
        self.retract_before_move = ko.observable(values.retract_before_move);
        self.cleanup_after_render_complete = ko.observable(values.cleanup_after_render_complete);
        self.cleanup_after_render_fail = ko.observable(values.cleanup_after_render_fail);


        self.addPositionRestriction = function (type) {
            //console.log("Adding " + type + " position restriction.");
            var restriction = null;
            switch (type) {
                case "layer":
                    {
                        restriction = ko.observable({
                            "Type": self.new_layer_position_restriction_type(),
                            "Shape": self.new_layer_position_restriction_shape(),
                            "X": self.new_layer_position_restriction_x(),
                            "Y": self.new_layer_position_restriction_y(),
                            "X2": self.new_layer_position_restriction_x2(),
                            "Y2": self.new_layer_position_restriction_y2(),
                            "R": self.new_layer_position_restriction_r()
                        });
                        self.layer_trigger_position_restrictions.push(restriction);
                    }
                    break;
                case "timer":
                    {
                        restriction = ko.observable({
                            "Type": self.new_timer_position_restriction_type(),
                            "Shape": self.new_timer_position_restriction_shape(),
                            "X": self.new_timer_position_restriction_x(),
                            "Y": self.new_timer_position_restriction_y(),
                            "X2": self.new_timer_position_restriction_x2(),
                            "Y2": self.new_timer_position_restriction_y2(),
                            "R": self.new_timer_position_restriction_r()
                        });
                        self.timer_trigger_position_restrictions.push(restriction);
                    }
                    break;
                case "gcode":
                    {
                        restriction = ko.observable({
                            "Type": self.new_gcode_position_restriction_type(),
                            "Shape": self.new_gcode_position_restriction_shape(),
                            "X": self.new_gcode_position_restriction_x(),
                            "Y": self.new_gcode_position_restriction_y(),
                            "X2": self.new_gcode_position_restriction_x2(),
                            "Y2": self.new_gcode_position_restriction_y2(),
                            "R": self.new_gcode_position_restriction_r()
                        });
                        self.gcode_trigger_position_restrictions.push(restriction);
                    }
                    break;
                default:
                    console.log("Unknown position restriction type");
            }
            
            
        };
        self.removePositionRestriction = function (type, index) {
            console.log("Removing " + type + " restriction at index: " + index());

            switch (type) {
                case "layer":
                    {
                        self.layer_trigger_position_restrictions.splice(index(), 1);
                    }
                    break;
                case "timer":
                    {
                        self.timer_trigger_position_restrictions.splice(index(), 1);
                    }
                    break;
                case "gcode":
                    {
                        self.gcode_trigger_position_restrictions.splice(index(), 1);
                    }
                    break;
                default:
                    console.log("Unknown position restriction type");
            }

            
        }

    };
    Octolapse.SnapshotProfileValidationRules = {
        rules: {
            /*Layer Position Restrictions*/
            new_layer_position_restriction_x: { lessThan: "#octolapse_new_layer_position_restriction_x2:visible" },
            new_layer_position_restriction_x2: { greaterThan: "#octolapse_new_layer_position_restriction_x:visible" },
            new_layer_position_restriction_y: { lessThan: "#octolapse_new_layer_position_restriction_y2:visible" },
            new_layer_position_restriction_y2: { greaterThan: "#octolapse_new_layer_position_restriction_y:visible" },
            /*Timer Position Restrictions*/
            new_timer_position_restriction_x: { lessThan: "#octolapse_new_timer_position_restriction_x2:visible" },
            new_timer_position_restriction_x2: { greaterThan: "#octolapse_new_timer_position_restriction_x:visible" },
            new_timer_position_restriction_y: { lessThan: "#octolapse_new_timer_position_restriction_y2:visible" },
            new_timer_position_restriction_y2: { greaterThan: "#octolapse_new_timer_position_restriction_y:visible" },
            /*Gcode Position Restrictions*/
            new_gcode_position_restriction_x: { lessThan: "#octolapse_new_gcode_position_restriction_x2:visible" },
            new_gcode_position_restriction_x2: { greaterThan: "#octolapse_new_gcode_position_restriction_x:visible" },
            new_gcode_position_restriction_y: { lessThan: "#octolapse_new_gcode_position_restriction_y2:visible" },
            new_gcode_position_restriction_y2: { greaterThan: "#octolapse_new_gcode_position_restriction_y:visible" },
        },
        messages: {
            name: "Please enter a name for your profile",
            /*Layer Position Restrictions*/
            new_layer_position_restriction_x : { lessThan: "Must be less than the 'X2' field." },
            new_layer_position_restriction_x2: { greaterThan: "Must be greater than the 'X' field." },
            new_layer_position_restriction_y: { lessThan: "Must be less than the 'Y2." },
            new_layer_position_restriction_y2: { greaterThan: "Must be greater than the 'Y' field." },
            /*Timer Position Restrictions*/
            new_timer_position_restriction_x: { lessThan: "Must be less than the 'X2' field." },
            new_timer_position_restriction_x2: { greaterThan: "Must be greater than the 'X' field." },
            new_timer_position_restriction_y: { lessThan: "Must be less than the 'Y2." },
            new_timer_position_restriction_y2: { greaterThan: "Must be greater than the 'Y' field." },
            /*Gcode Position Restrictions*/
            new_gcode_position_restriction_x: { lessThan: "Must be less than the 'X2' field." },
            new_gcode_position_restriction_x2: { greaterThan: "Must be greater than the 'X' field." },
            new_gcode_position_restriction_y: { lessThan: "Must be less than the 'Y2." },
            new_gcode_position_restriction_y2: { greaterThan: "Must be greater than the 'Y' field." },
        }
    };
});


