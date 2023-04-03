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
    Octolapse.TriggerProfileViewModel = function (values) {

        var self = this;
        self.profileTypeName = ko.observable("Trigger");
        self.guid = ko.observable(values.guid);
        self.name = ko.observable(values.name);
        self.description = ko.observable(values.description);
        self.trigger_type = ko.observable(values.trigger_type);
        // Pre-calculated trigger options
        self.smart_layer_trigger_type = ko.observable(values.smart_layer_trigger_type);
        self.smart_layer_snap_to_print_high_quality = ko.observable(values.smart_layer_snap_to_print_high_quality);
        self.smart_layer_snap_to_print_smooth = ko.observable(values.smart_layer_snap_to_print_smooth);

        self.smart_layer_disable_z_lift = ko.observable(values.smart_layer_disable_z_lift);
        self.allow_smart_snapshot_commands = ko.observable(values.allow_smart_snapshot_commands);
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

        /*
        * Position Restrictions
        * */
        self.position_restrictions_enabled = ko.observable(values.position_restrictions_enabled);
        var position_restrictions = [];
        for (var index = 0; index < values.position_restrictions.length; index++) {
            position_restrictions.push(
                ko.observable(values.position_restrictions[index]));
        }
        self.position_restrictions = ko.observableArray(position_restrictions);

        // Temporary variables to hold new layer position restrictions
        self.new_position_restriction_type = ko.observable('required');
        self.new_position_restriction_shape = ko.observable('rect');
        self.new_position_restriction_x = ko.observable(0);
        self.new_position_restriction_y = ko.observable(0);
        self.new_position_restriction_x2 = ko.observable(1);
        self.new_position_restriction_y2 = ko.observable(1);
        self.new_position_restriction_r = ko.observable(1);
        self.new_calculate_intersections = ko.observable(false);
        // Hold the parent dialog.
        self.dialog = null;
        self.get_trigger_subtype_options = ko.pureComputed( function () {
                if (self.trigger_type() == 'smart') {
                    var options = [];
                    for (var index = 0; index < Octolapse.Triggers.profileOptions.trigger_subtype_options.length; index++) {
                        var curItem = Octolapse.Triggers.profileOptions.trigger_subtype_options[index];
                        if (curItem.value == 'timer') {
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
            if (!self.dialog.IsValid())
            {
                return;
            }

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
            //console.log("Removing restriction at index: " + index);
            self.position_restrictions.splice(index, 1);
        };

        self.updateFromServer = function(values) {
            self.name(values.name);
            self.description(values.description);
            self.trigger_type(values.trigger_type);
            self.smart_layer_snap_to_print_high_quality(values.smart_layer_snap_to_print_high_quality);
            self.smart_layer_snap_to_print_smooth(values.smart_layer_snap_to_print_smooth);
            self.smart_layer_trigger_type(values.smart_layer_trigger_type);
            self.smart_layer_disable_z_lift(values.smart_layer_disable_z_lift);
            self.allow_smart_snapshot_commands(values.allow_smart_snapshot_commands);
            self.trigger_subtype(values.trigger_subtype);
            self.timer_trigger_seconds(values.timer_trigger_seconds);
            self.layer_trigger_height(values.layer_trigger_height);
            self.extruder_state_requirements_enabled(values.extruder_state_requirements_enabled);
            self.trigger_on_extruding(values.trigger_on_extruding);
            self.trigger_on_extruding_start(values.trigger_on_extruding_start);
            self.trigger_on_primed(values.trigger_on_primed);
            self.trigger_on_retracting_start(values.trigger_on_retracting_start);
            self.trigger_on_retracting(values.trigger_on_retracting);
            self.trigger_on_partially_retracted(values.trigger_on_partially_retracted);
            self.trigger_on_retracted(values.trigger_on_retracted);
            self.trigger_on_deretracting_start(values.trigger_on_deretracting_start);
            self.trigger_on_deretracting(values.trigger_on_deretracting);
            self.trigger_on_deretracted(values.trigger_on_deretracted);
            self.require_zhop(values.require_zhop);
            self.position_restrictions_enabled(values.position_restrictions_enabled);
            var position_restrictions = [];
            for (var index = 0; index < values.position_restrictions.length; index++) {
                position_restrictions.push(
                    ko.observable(values.position_restrictions[index]));
            }
            self.position_restrictions(position_restrictions);
        };

        self.automatic_configuration = new Octolapse.ProfileLibraryViewModel(
            values.automatic_configuration,
            Octolapse.Triggers.profileOptions.server_profiles,
            self.profileTypeName(),
            self,
            self.updateFromServer
        );

        self.toJS = function()
        {
            // need to remove the parent link from the automatic configuration to prevent a cyclic copy
            var parent = self.automatic_configuration.parent;
            var dialog = self.dialog;
            self.dialog = null;
            self.automatic_configuration.parent = null;
            var copy = ko.toJS(self);
            self.dialog = dialog;
            self.automatic_configuration.parent = parent;
            return copy;
        };

        self.on_opened = function(dialog)
        {
            self.dialog = dialog;
        };
        self.on_closed = function(){
            self.automatic_configuration.on_closed();
        };

        self.automatic_configuration.is_confirming.subscribe(function(value){
            //console.log("IsClickable" + value.toString());
            Octolapse.Triggers.setIsClickable(!value);
        });
    };


    Octolapse.TriggerProfileValidationRules = {

            rules: {

            octolapse_trigger_name: "required",
            octolapse_trigger_new_position_restriction_x: { lessThan: "#octolapse_trigger_new_position_restriction_x2:visible" },
            octolapse_trigger_new_position_restriction_x2: { greaterThan: "#octolapse_trigger_new_position_restriction_x:visible" },
            octolapse_trigger_new_position_restriction_y: { lessThan: "#octolapse_trigger_new_position_restriction_y2:visible" },
            octolapse_trigger_new_position_restriction_y2: { greaterThan: "#octolapse_trigger_new_position_restriction_y:visible" },
        },
        messages: {
            octolapse_trigger_name: "Please enter a name for your profile",
            octolapse_trigger_new_position_restriction_x : { lessThan: "Must be less than the 'X2' field." },
            octolapse_trigger_new_position_restriction_x2: { greaterThan: "Must be greater than the 'X' field." },
            octolapse_trigger_new_position_restriction_y: { lessThan: "Must be less than the 'Y2." },
            octolapse_trigger_new_position_restriction_y2: { greaterThan: "Must be greater than the 'Y' field." },
        }
    };
});


