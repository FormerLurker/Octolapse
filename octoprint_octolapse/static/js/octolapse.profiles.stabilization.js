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
    Octolapse.StabilizationProfileViewModel = function (values) {
        var self = this;
        self.profileTypeName = ko.observable("Stabilization");
        self.guid = ko.observable(values.guid);
        self.name = ko.observable(values.name);
        self.description = ko.observable(values.description);
        self.stabilization_type = ko.observable(values.stabilization_type);
        // Pre-calculated stabilization options
        self.lock_to_corner_type = ko.observable(values.lock_to_corner_type);
        self.lock_to_corner_favor_axis = ko.observable(values.lock_to_corner_favor_axis);
        self.lock_to_corner_disable_z_lift = ko.observable(values.lock_to_corner_disable_z_lift);
        self.lock_to_corner_disable_retract = ko.observable(values.lock_to_corner_disable_retract);
        self.fastest_speed = ko.observable(values.fastest_speed);
        //  Real-time stabilization options
        self.x_type = ko.observable(values.x_type);
        self.x_fixed_coordinate = ko.observable(values.x_fixed_coordinate);
        self.x_fixed_path = ko.observable(values.x_fixed_path);
        self.x_fixed_path_loop = ko.observable(values.x_fixed_path_loop);
        self.x_fixed_path_invert_loop = ko.observable(values.x_fixed_path_invert_loop);
        self.x_relative = ko.observable(values.x_relative);
        self.x_relative_print = ko.observable(values.x_relative_print);
        self.x_relative_path = ko.observable(values.x_relative_path);
        self.x_relative_path_loop = ko.observable(values.x_relative_path_loop);
        self.x_relative_path_invert_loop = ko.observable(values.x_relative_path_invert_loop);
        self.y_type = ko.observable(values.y_type);
        self.y_fixed_coordinate = ko.observable(values.y_fixed_coordinate);
        self.y_fixed_path = ko.observable(values.y_fixed_path);
        self.y_fixed_path_loop = ko.observable(values.y_fixed_path_loop);
        self.y_fixed_path_invert_loop = ko.observable(values.y_fixed_path_invert_loop);
        self.y_relative = ko.observable(values.y_relative);
        self.y_relative_print = ko.observable(values.y_relative_print);
        self.y_relative_path = ko.observable(values.y_relative_path);
        self.y_relative_path_loop = ko.observable(values.y_relative_path_loop);
        self.y_relative_path_invert_loop = ko.observable(values.y_relative_path_invert_loop);
        // Variables formerly belonging to the snapshot profile (now removed)
        self.trigger_type = ko.observable(values.trigger_type);
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
        self.feature_restrictions_enabled = ko.observable(values.feature_restrictions_enabled);
        self.feature_trigger_on_deretract = ko.observable(values.feature_trigger_on_deretract);
        self.feature_trigger_on_retract = ko.observable(values.feature_trigger_on_retract);
        self.feature_trigger_on_movement = ko.observable(values.feature_trigger_on_movement);
        self.feature_trigger_on_z_movement = ko.observable(values.feature_trigger_on_z_movement);
        self.feature_trigger_on_perimeters = ko.observable(values.feature_trigger_on_perimeters);
        self.feature_trigger_on_small_perimeters = ko.observable(values.feature_trigger_on_small_perimeters);
        self.feature_trigger_on_external_perimeters = ko.observable(values.feature_trigger_on_external_perimeters);
        self.feature_trigger_on_infill = ko.observable(values.feature_trigger_on_infill);
        self.feature_trigger_on_solid_infill = ko.observable(values.feature_trigger_on_solid_infill);
        self.feature_trigger_on_top_solid_infill = ko.observable(values.feature_trigger_on_top_solid_infill);
        self.feature_trigger_on_supports = ko.observable(values.feature_trigger_on_supports);
        self.feature_trigger_on_bridges = ko.observable(values.feature_trigger_on_bridges);
        self.feature_trigger_on_gap_fills = ko.observable(values.feature_trigger_on_gap_fills);
        self.feature_trigger_on_first_layer = ko.observable(values.feature_trigger_on_first_layer);
        self.feature_trigger_on_first_layer_travel = ko.observable(values.feature_trigger_on_first_layer_travel);
        self.feature_trigger_on_skirt_brim = ko.observable(values.feature_trigger_on_skirt_brim);
        self.feature_trigger_on_normal_print_speed = ko.observable(values.feature_trigger_on_normal_print_speed);
        self.feature_trigger_on_above_raft = ko.observable(values.feature_trigger_on_above_raft);
        self.feature_trigger_on_ooze_shield = ko.observable(values.feature_trigger_on_ooze_shield);
        self.feature_trigger_on_prime_pillar = ko.observable(values.feature_trigger_on_prime_pillar);
        self.feature_trigger_on_wipe = ko.observable(values.feature_trigger_on_wipe);
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

        self.get_trigger_type_options = ko.pureComputed( function () {
                if (self.stabilization_type() !== 'real-time') {
                    var options = [];
                    for (var index = 0; index < Octolapse.Stabilizations.profileOptions.trigger_types.length; index++) {
                        var curItem = Octolapse.Stabilizations.profileOptions.trigger_types[index];
                        if (curItem.value !== 'layer') {
                            continue;
                        }
                        options.push(curItem);
                    }
                    return options;
                }
                return Octolapse.Stabilizations.profileOptions.trigger_types;
            }, this);


        self.get_xy_stabilization_type_options = ko.pureComputed( function () {
                if (self.stabilization_type() === 'minimize-travel') {
                    var options = [];
                    for (var index = 0; index < Octolapse.Stabilizations.profileOptions.real_time_xy_stabilization_type_options.length; index++) {
                        var curItem = Octolapse.Stabilizations.profileOptions.real_time_xy_stabilization_type_options[index];
                        if (curItem.value === 'disabled') {
                            continue;
                        }
                        options.push(curItem);
                    }
                    return options;
                }
                return Octolapse.Stabilizations.profileOptions.real_time_xy_stabilization_type_options;
            }, this);

        self.print_quality_settings_available = ko.pureComputed( function () {
            return (
                self.trigger_on_zhop_only_available() ||
                self.extruder_trigger_requirements_available() ||
                self.feature_detection_available() ||
                self.position_restrictions_available()
            );
        }, this);

        self.trigger_on_zhop_only_available = ko.pureComputed( function () {
            return self.stabilization_type() === 'real-time';
        }, this);

        self.extruder_trigger_requirements_available = ko.pureComputed( function () {
            return self.stabilization_type() === 'real-time';
        }, this);

        self.feature_detection_available = ko.pureComputed( function () {
            return self.stabilization_type() === 'real-time';
        }, this);

        self.position_restrictions_available = ko.pureComputed( function () {
            return self.stabilization_type() === 'real-time';
        }, this);

        // Functions previously belonging to the snapshot profile
        self.feature_template_id = ko.pureComputed(function () {
            var current_printer = Octolapse.Printers.currentProfile();
            if (current_printer == null)
                return 'snapshot-missing-printer-feature-template';
            var current_slicer_type = Octolapse.Printers.currentProfile().slicer_type();
            switch (current_slicer_type) {
                case "other":
                    return "snapshot-other-slicer-feature-template";
                case "slic3r-pe":
                    return "snapshot-sli3er-pe-feature-template";
                case "cura":
                    return "snapshot-cura-feature-template";
                case "simplify-3d":
                    return "snapshot-simplify-3d-feature-template";
                case "automatic":
                    return "snapshot-automatic-slicer-feature-template";
                default:
                    return "snapshot-other-slicer-feature-template";
            }
        });
        self.nonUniqueSpeedList = ko.observable([]);
        self.missingSpeedsList = ko.observable([]);

        self.getPrinterFeatures = function () {
            //console.log("getting feature list");
            var current_printer = Octolapse.Printers.currentProfile();
            if (current_printer == null) {
                self.nonUniqueSpeedList([]);
                self.missingSpeedsList([]);
                return;
            }

            var data = null;
            switch (current_printer.slicer_type()) {
                case 'cura':
                    data = ko.toJS(current_printer.slicers.cura);
                    break;
                case 'other':
                    data = ko.toJS(current_printer.slicers.other);
                    break;
                case 'simplify-3d':
                    data = ko.toJS(current_printer.slicers.simplify_3d);
                    break;
                case 'slic3r-pe':
                    data = ko.toJS(current_printer.slicers.slic3r_pe);
                    break;
            }
            if (data != null) {
                $.ajax({
                    url: "./plugin/octolapse/getPrintFeatures",
                    type: "POST",
                    tryCount: 0,
                    retryLimit: 3,
                    contentType: "application/json",
                    data: JSON.stringify({
                            'slicer_settings': data,
                            'slicer_type': current_printer.slicer_type()
                        }
                    ),
                    dataType: "json",
                    success: function (result) {
                        //console.log("print features received");
                        //console.log(result);
                        self.nonUniqueSpeedList(result['non-unique-speeds']);
                        self.missingSpeedsList(result['missing-speeds']);
                    },
                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                        return false;
                    }
                });
            }
        };
        // Trigger a change of the slicer print feature error messages
        self.getPrinterFeatures();

        self.addPositionRestriction = function () {
            //console.log("Adding " + type + " position restriction.");
            var restriction = ko.observable({
                "type": self.new_position_restriction_type(),
                "shape": self.new_position_restriction_shape(),
                "x": self.new_position_restriction_x(),
                "t": self.new_position_restriction_y(),
                "x2": self.new_position_restriction_x2(),
                "t2": self.new_position_restriction_y2(),
                "r": self.new_position_restriction_r(),
                "calculate_intersections": self.new_calculate_intersections()
            });
            self.position_restrictions.push(restriction);
        };

        self.removePositionRestriction = function (index) {
            //console.log("Removing " + type + " restriction at index: " + index());
            self.position_restrictions.splice(index(), 1);
        };
    };


    Octolapse.StabilizationProfileValidationRules = {
        rules: {
            name: "required"
            , stabilization_type: "required"
            , lock_to_corner_type: "required"
            , lock_to_corner_favor_axis: "required"
            , x_type: "required"
            , x_fixed_coordinate: {number: true, required: true}
            , x_fixed_path: {required: true, csvFloat: true}
            , x_relative: {required: true, number: true, min: 0.0, max: 100.0}
            , x_relative_path: {required: true, csvRelative: true}
            , y_type: "required"
            , y_fixed_coordinate: {number: true, required: true}
            , y_fixed_path: {required: true, csvFloat: true}
            , y_relative: {required: true, number: true, min: 0.0, max: 100.0}
            , y_relative_path: {required: true, csvRelative: true},
            // Rules formerly belonging to snapshot profile
            /*Layer Position Restrictions*/
            new_position_restriction_x: { lessThan: "#octolapse_new_position_restriction_x2:visible" },
            new_position_restriction_x2: { greaterThan: "#octolapse_new_position_restriction_x:visible" },
            new_position_restriction_y: { lessThan: "#octolapse_new_position_restriction_y2:visible" },
            new_position_restriction_y2: { greaterThan: "#octolapse_new_position_restriction_y:visible" },
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


