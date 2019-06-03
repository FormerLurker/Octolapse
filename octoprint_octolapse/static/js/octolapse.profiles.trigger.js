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
$(function () {
    Octolapse.TriggerProfileViewModel = function (values) {
        var self = this;
        self.profileTypeName = ko.observable("Trigger");
        self.guid = ko.observable(values.guid);
        self.name = ko.observable(values.name);
        self.description = ko.observable(values.description);
        self.trigger_type = ko.observable(values.trigger_type);
        // Pre-calculated trigger options
        self.snap_to_print_disable_z_lift = ko.observable(values.snap_to_print_disable_z_lift);
        self.fastest_speed = ko.observable(values.fastest_speed);
        self.smart_layer_trigger_type = ko.observable(values.smart_layer_trigger_type);
        self.smart_layer_trigger_speed_threshold = ko.observable(values.smart_layer_trigger_speed_threshold);
        self.smart_layer_trigger_distance_threshold_percent = ko.observable(values.smart_layer_trigger_distance_threshold_percent);
        self.smart_layer_snap_to_print = ko.observable(values.smart_layer_snap_to_print);
        self.smart_layer_disable_z_lift = ko.observable(values.smart_layer_disable_z_lift);
        self.trigger_subtype = ko.observable(values.trigger_subtype);
        /*
            Timer Trigger Settings
        */
        self.timer_trigger_seconds = ko.observable(values.timer_trigger_seconds);
        /*
            Layer/Height Trigger Settings
        */
        self.layer_trigger_height = ko.observable(values.layer_trigger_height);
        /*
        * Position Restrictions
        * */
        self.position_restrictions_enabled = ko.observable(values.position_restrictions_enabled);
        self.position_restrictions = ko.observableArray([]);
        for (var index = 0; index < values.position_restrictions.length; index++) {
            self.position_restrictions.push(
                ko.observable(values.position_restrictions[index]));
        }

        /*
        * Quaity Settiings
        */
        // Extruder State
        self.extruder_state_requirements_enabled = ko.observable(values.extruder_state_requirements_enabled);
        self.trigger_on_extruding = ko.observable(values.trigger_on_extruding);
        self.trigger_on_extruding_start = ko.observable(values.trigger_on_extruding_start);
        self.trigger_on_primed = ko.observable(values.trigger_on_primed);
        self.trigger_on_retracting_start = ko.observable(values.trigger_on_retracting_start);
        self.trigger_on_retracting = ko.observable(values.trigger_on_retracting);
        self.trigger_on_partially_retracted = ko.observable(values.trigger_on_partially_retracted);
        self.trigger_on_retracted = ko.observable(values.trigger_on_retracted);
        self.trigger_on_deretracting_start = ko.observable(values.trigger_on_deretracting_start);
        self.trigger_on_deretracting = ko.observable(values.trigger_on_deretracting);
        self.trigger_on_deretracted = ko.observable(values.trigger_on_deretracted);
        self.require_zhop = ko.observable(values.require_zhop);
        // Temporary variables to hold new layer position restrictions
        self.new_position_restriction_type = ko.observable('required');
        self.new_position_restriction_shape = ko.observable('rect');
        self.new_position_restriction_x = ko.observable(0);
        self.new_position_restriction_y = ko.observable(0);
        self.new_position_restriction_x2 = ko.observable(1);
        self.new_position_restriction_y2 = ko.observable(1);
        self.new_position_restriction_r = ko.observable(1);
        self.new_calculate_intersections = ko.observable(false);

        self.get_trigger_subtype_options = ko.pureComputed( function () {
                if (self.trigger_type() !== 'real-time') {
                    var options = [];
                    for (var index = 0; index < Octolapse.Triggers.profileOptions.trigger_subtype_options.length; index++) {
                        var curItem = Octolapse.Triggers.profileOptions.trigger_subtype_options[index];
                        if (curItem.value !== 'layer') {
                            continue;
                        }
                        options.push(curItem);
                    }
                    return options;
                }
                return Octolapse.Triggers.profileOptions.trigger_subtype_options;
            }, this);

        self.print_quality_settings_available = ko.pureComputed( function () {
            return (
                self.trigger_on_zhop_only_available() ||
                self.extruder_trigger_requirements_available() ||
                self.position_restrictions_available()
            );
        }, this);

        self.trigger_on_zhop_only_available = ko.pureComputed( function () {
            return self.trigger_type() === 'real-time';
        }, this);

        self.extruder_trigger_requirements_available = ko.pureComputed( function () {
            return self.trigger_type() === 'real-time';
        }, this);

        self.position_restrictions_available = ko.pureComputed( function () {
            return self.trigger_type() === 'real-time';
        }, this);

        self.addPositionRestriction = function () {
            //console.log("Adding " + type + " position restriction.");
            var restriction = ko.observable({
                "type": self.new_position_restriction_type(),
                "shape": self.new_position_restriction_shape(),
                "x": self.new_position_restriction_x(),
                "y": self.new_position_restriction_y(),
                "x2": self.new_position_restriction_x2(),
                "y2": self.new_position_restriction_y2(),
                "r": self.new_position_restriction_r(),
                "calculate_intersections": self.new_calculate_intersections()
            });
            self.position_restrictions.push(restriction);
        };

        self.removePositionRestriction = function (index) {
            console.log("Removing restriction at index: " + index);
            self.position_restrictions.splice(index, 1);
        };
    };


    Octolapse.TriggerProfileValidationRules = {

            rules: {

            name: "required",
            new_position_restriction_x: { lessThan: "#octolapse_trigger_new_position_restriction_x2:visible" },
            new_position_restriction_x2: { greaterThan: "#octolapse_trigger_new_position_restriction_x:visible" },
            new_position_restriction_y: { lessThan: "#octolapse_trigger_new_position_restriction_y2:visible" },
            new_position_restriction_y2: { greaterThan: "#octolapse_trigger_new_position_restriction_y:visible" },
            layer_trigger_enabled: {check_one: ".octolapse_trigger_enabled"},
            gcode_trigger_enabled: {check_one: ".octolapse_trigger_enabled"},
            timer_trigger_enabled: {check_one: ".octolapse_trigger_enabled"},
        },
        messages: {
            name: "Please enter a name for your profile",
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


