Octolapse.create_slic3r_pe_viewmodel = function (profile_observables) {
    var self = this;
    self.get_axis_speed_display_units = function () {
        return "mm-sec"
    };
    self.get_speed_tolerance = function () {
        // 0.005 mm/min in mm-sec
        return 0.01 / 60.0 / 2.0;
    };

    self.round_to_increment_mm_min = 0.00000166667;
    self.round_to_increment_mm_sec = 0.0001;
    self.round_to_percent = 0.0001;
    self.round_to_increment_retraction_length = 0.000001;
    self.round_to_increment_lift_z = 0.0001;

    // Options for the round_to_increment extender for lengths
    self.round_to_increment_options_retraction_length = {
        round_to_increment:{round_to_increment: self.round_to_increment_retraction_length}
    };

    // Options for the round_to_increment extender for lengths
    self.round_to_increment_options_lift_z = {
        round_to_increment:{round_to_increment: self.round_to_increment_lift_z}
    };
    self.rounding_extender_options = {
        axis_speed_unit:{
            round_to_increment_mm_min: self.round_to_increment_mm_min,
            round_to_increment_mm_sec:self.round_to_increment_mm_sec,
            current_units_observable: self.get_axis_speed_display_units}};

    self.rounding_extender_percent_options = {
        axis_speed_unit:{
            round_to_increment_mm_min: self.round_to_increment_mm_min,
            round_to_increment_mm_sec:self.round_to_increment_mm_sec,
            current_units_observable: self.get_axis_speed_display_units,
            round_to_percent: self.round_to_percent,
            return_text: true}};

    // Initialize profile variables from observables
    // Lengths
    self.retract_length = ko.observable(profile_observables.retract_length).extend(self.round_to_increment_options_retraction_length);
    self.z_hop = ko.observable(profile_observables.z_hop).extend(self.round_to_increment_options_lift_z);

    // Speeds
    self.retract_speed = ko.observable(
        Octolapse.convertAxisSpeedUnit(
            profile_observables.retract_speed, self.get_axis_speed_display_units(), profile_observables.axis_speed_display_units, self.round_to_increment_mm_sec)).extend(self.rounding_extender_options);
    self.detract_speed = ko.observable(
        Octolapse.convertAxisSpeedUnit(
            profile_observables.detract_speed, self.get_axis_speed_display_units(), profile_observables.axis_speed_display_units, self.round_to_increment_mm_sec)).extend(self.rounding_extender_options);
    self.movement_speed = ko.observable(
        Octolapse.convertAxisSpeedUnit(
            profile_observables.movement_speed, self.get_axis_speed_display_units(), profile_observables.axis_speed_display_units, self.round_to_increment_mm_sec)).extend(self.rounding_extender_options);
    self.perimeter_speed = ko.observable(
        Octolapse.convertAxisSpeedUnit(
            profile_observables.perimeter_speed, self.get_axis_speed_display_units(), profile_observables.axis_speed_display_units, self.round_to_increment_mm_sec)).extend(self.rounding_extender_options);
    self.infill_speed = ko.observable(
        Octolapse.convertAxisSpeedUnit(
            profile_observables.infill_speed, self.get_axis_speed_display_units(), profile_observables.axis_speed_display_units, self.round_to_increment_mm_sec)).extend(self.rounding_extender_options);
    self.support_speed = ko.observable(
        Octolapse.convertAxisSpeedUnit(
            profile_observables.support_speed, self.get_axis_speed_display_units(), profile_observables.axis_speed_display_units, self.round_to_increment_mm_sec)).extend(self.rounding_extender_options);
    self.bridge_speed = ko.observable(
        Octolapse.convertAxisSpeedUnit(
            profile_observables.bridge_speed, self.get_axis_speed_display_units(), profile_observables.axis_speed_display_units, self.round_to_increment_mm_sec)).extend(self.rounding_extender_options);
    self.gap_fill_speed = ko.observable(
        Octolapse.convertAxisSpeedUnit(
            profile_observables.gap_fill_speed, self.get_axis_speed_display_units(), profile_observables.axis_speed_display_units, self.round_to_increment_mm_sec)).extend(self.rounding_extender_options);

    // Speeds/Percents
    var small_perimeter_speed = profile_observables.small_perimeter_speed_text || (
        Octolapse.convertAxisSpeedUnit(
            profile_observables.small_perimeter_speed,
            self.get_axis_speed_display_units(),
            profile_observables.axis_speed_display_units, self.round_to_increment_mm_sec)
    );
    self.small_perimeter_speed_text = ko.observable((small_perimeter_speed || "").toString()).extend(self.rounding_extender_percent_options);

    var external_perimeter_speed = profile_observables.external_perimeter_speed_text || (
        Octolapse.convertAxisSpeedUnit(
            profile_observables.external_perimeter_speed,
            self.get_axis_speed_display_units(),
            profile_observables.axis_speed_display_units, self.round_to_increment_mm_sec)
    );
    self.external_perimeter_speed_text = ko.observable((external_perimeter_speed || "").toString()).extend(self.rounding_extender_percent_options);

    var solid_infill_speed = profile_observables.solid_infill_speed_text || (
        Octolapse.convertAxisSpeedUnit(
            profile_observables.solid_infill_speed,
            self.get_axis_speed_display_units(),
            profile_observables.axis_speed_display_units, self.round_to_increment_mm_sec)
    );
    self.solid_infill_speed_text = ko.observable((solid_infill_speed || "").toString()).extend(self.rounding_extender_percent_options);

    var top_solid_infill_speed = profile_observables.top_solid_infill_speed_text || (
        Octolapse.convertAxisSpeedUnit(
            profile_observables.top_solid_infill_speed,
            self.get_axis_speed_display_units(),
            profile_observables.axis_speed_display_units, self.round_to_increment_mm_sec)
    );
    self.top_solid_infill_speed_text = ko.observable((top_solid_infill_speed || "").toString()).extend(self.rounding_extender_percent_options);

    var first_layer_speed = profile_observables.first_layer_speed_text || (
        Octolapse.convertAxisSpeedUnit(
            profile_observables.first_layer_speed,
            self.get_axis_speed_display_units(),
            profile_observables.axis_speed_display_units, self.round_to_increment_mm_sec)
    );
    self.first_layer_speed_text = ko.observable((first_layer_speed || "").toString()).extend(self.rounding_extender_percent_options);
    /*
        Create a getter for each profile variable (settings.py - printer class)
    */
    self.get_retract_length = function () {
        return self.retract_length();
    };
    self.get_retract_speed = function () {
        return self.retract_speed();
    };
    self.get_detract_speed = function () {
        if(self.detract_speed() === 0)
            return self.retract_speed();

        return self.detract_speed();
    };
    self.get_movement_speed = function () {
        return self.movement_speed();
    };
    self.get_z_hop = function () {
        return self.z_hop();
    };
    self.get_z_hop_speed = function () {
        return self.movement_speed();
    };
    self.get_maximum_z_speed = function () {
        return null;
    };
    self.get_print_speed = function () {
        return null;
    };
    self.get_perimeter_speed = function () {
        return self.perimeter_speed();
    };
    self.get_small_perimeter_speed = function () {
        var value = self.small_perimeter_speed_text();
        if (Octolapse.isPercent(value)) {
            var percent = Octolapse.parsePercent(value);
            if (percent != null && self.perimeter_speed() != null)
                return self.perimeter_speed() * percent / 100.0;
        }
        else {
            return Octolapse.parseFloat(value);
        }
        return null;
    };
    self.get_small_perimeter_speed_multiplier = function () {
        var value = self.small_perimeter_speed_text();
        if (!Octolapse.isPercent(value))
            return null;
        return Octolapse.parsePercent(value);
    }
    self.get_external_perimeter_speed = function () {
        var value = self.external_perimeter_speed_text();
        if (Octolapse.isPercent(value)) {
            var percent = Octolapse.parsePercent(value);
            if (percent != null && self.perimeter_speed() != null)
                return self.perimeter_speed() * percent / 100.0;
        }
        else {
            return Octolapse.parseFloat(value);
        }
        return null;
    };
    self.get_external_perimeter_speed_multiplier = function () {
        var value = self.external_perimeter_speed_text();
        if (!Octolapse.isPercent(value))
            return null;
        return Octolapse.parsePercent(value);
    }

    self.get_infill_speed = function () {
        return self.infill_speed();
    };
    self.get_solid_infill_speed = function () {
        var value = self.solid_infill_speed_text();
        if (Octolapse.isPercent(value)) {
            var percent = Octolapse.parsePercent(value);
            if (percent != null && self.infill_speed() != null)
                return self.infill_speed() * percent / 100.0;
        }
        else {
            return Octolapse.parseFloat(value);
        }
        return null;
    };
    self.get_solid_infill_speed_multiplier = function () {
        var value = self.solid_infill_speed_text();
        if (!Octolapse.isPercent(value))
            return null;
        return Octolapse.parsePercent(value);
    }
    self.get_top_solid_infill_speed = function () {
        var value = self.top_solid_infill_speed_text();
        if (Octolapse.isPercent(value)) {
            var percent = Octolapse.parsePercent(value);
            if (percent != null && self.get_solid_infill_speed() != null)
                return self.get_solid_infill_speed() * percent / 100.0;
        }
        else {
            return Octolapse.parseFloat(value);
        }
        return null;
    };
    self.get_top_solid_infill_speed_multiplier = function () {
        var value = self.top_solid_infill_speed_text();
        if (!Octolapse.isPercent(value))
            return null;
        return Octolapse.parsePercent(value);
    }

    self.get_support_speed = function () {
        return self.support_speed();
    };
    self.get_bridge_speed = function () {
        return self.bridge_speed();
    };
    self.get_gap_fill_speed = function () {
        return self.gap_fill_speed();
    };
    self.get_first_layer_speed = function () {
        var value = self.first_layer_speed_text();
        if (Octolapse.isPercent(value))
            return null;

        return Octolapse.parseFloat(value);
    };
    self.get_first_layer_speed_multiplier = function () {
        var value = self.first_layer_speed_text();
        if (!Octolapse.isPercent(value))
            return null;
        return Octolapse.parsePercent(value);
    };

    self.get_first_layer_travel_speed = function () {
        return self.movement_speed();
    };

    self.get_small_perimeter_speed_text = function () {
        return self.small_perimeter_speed_text();
    };
    self.get_external_perimeter_speed_text = function () {
        return self.external_perimeter_speed_text();
    };
    self.get_solid_infill_speed_text = function () {
        return self.solid_infill_speed_text();
    };
    self.get_top_solid_infill_speed_text = function () {
        return self.top_solid_infill_speed_text();
    };
    self.get_first_layer_speed_text = function () {
        return self.first_layer_speed_text();
    };

    self.get_num_slow_layers = function () {
        return 1;
    }
    // Get a list of speeds for use with feature detection

    self.getSlicerSpeedList = function () {
        var inc = 0.01;
        var ret_det_inc = 1;
        var speed_list = [
            {speed: Octolapse.roundToIncrement(self.get_retract_speed(), ret_det_inc) * 60, type: "Retraction"},
            {speed: Octolapse.roundToIncrement(self.get_detract_speed(), ret_det_inc) * 60, type: "Detraction"},
            {speed: Octolapse.roundToIncrement(self.get_perimeter_speed() * 60, inc), type: "Perimeters"},
            {speed: Octolapse.roundToIncrement(self.get_small_perimeter_speed() * 60, inc), type: "Small Perimeters"},
            {
                speed: Octolapse.roundToIncrement(self.get_external_perimeter_speed() * 60, inc),
                type: "External Perimeters"
            },
            {speed: Octolapse.roundToIncrement(self.get_infill_speed() * 60, inc), type: "Infill"},
            {speed: Octolapse.roundToIncrement(self.get_solid_infill_speed() * 60, inc), type: "Solid Infill"},
            {speed: Octolapse.roundToIncrement(self.get_top_solid_infill_speed() * 60, inc), type: "Top Solid Infill"},
            {speed: Octolapse.roundToIncrement(self.get_support_speed() * 60, inc), type: "Supports"},
            {speed: Octolapse.roundToIncrement(self.get_bridge_speed() * 60, inc), type: "Bridges"},
            {speed: Octolapse.roundToIncrement(self.get_gap_fill_speed() * 60, inc), type: "Gaps"},
            {speed: Octolapse.roundToIncrement(self.get_movement_speed() * 60, inc), type: "Movement"}
        ];

        if (self.get_first_layer_speed_multiplier() == null)
            speed_list.push({speed: self.get_first_layer_speed(), type: "First Layer"})
        else {
            Array.prototype.push.apply(speed_list, [
                {
                    speed: Octolapse.roundToIncrement(self.get_perimeter_speed() * self.get_first_layer_speed_multiplier() / 100.0 * 60, inc),
                    type: "First Layer Perimeters"
                },
                {
                    speed: Octolapse.roundToIncrement(self.get_small_perimeter_speed() * self.get_first_layer_speed_multiplier() * 60 / 100.0, inc),
                    type: "First Layer Small Perimeters"
                },
                {
                    speed: Octolapse.roundToIncrement(self.get_external_perimeter_speed() * self.get_first_layer_speed_multiplier() * 60 / 100.0, inc),
                    type: "First Layer External Perimeters"
                },
                {
                    speed: Octolapse.roundToIncrement(self.get_infill_speed() * self.get_first_layer_speed_multiplier() * 60 / 100.0, inc),
                    type: "First Layer Infill"
                },
                {
                    speed: Octolapse.roundToIncrement(self.get_solid_infill_speed() * self.get_first_layer_speed_multiplier() * 60 / 100.0, inc),
                    type: "First Layer Solid Infill"
                },
                {
                    speed: Octolapse.roundToIncrement(self.get_top_solid_infill_speed() * self.get_first_layer_speed_multiplier() * 60 / 100.0, inc),
                    type: "First Layer Top Solid Infill"
                },
                {
                    speed: Octolapse.roundToIncrement(self.get_support_speed() * self.get_first_layer_speed_multiplier() * 60 / 100.0, inc),
                    type: "First Layer Supports"
                },
                {
                    speed: Octolapse.roundToIncrement(self.get_gap_fill_speed() * self.get_first_layer_speed_multiplier() * 60 / 100.0, inc),
                    type: "First Layer Gaps"
                }
            ]);
        }

        return speed_list;
    };
};
