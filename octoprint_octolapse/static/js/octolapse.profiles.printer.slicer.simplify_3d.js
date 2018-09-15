Octolapse.create_simplify_3d_viewmodel = function (profile_observables) {
    var self = this;
    self.get_axis_speed_display_units = function () {
        return 'mm-min';
    };
    self.get_speed_tolerance = function () {
        return 1;
    };

    self.round_to_increment_percent = 1;
    self.round_to_increment_speed_mm_min = 0.1;
    self.round_to_increment_length = 0.01;
    self.percent_value_default = 100.0;

    // Options for the round_to_increment extender for lengths
    self.round_to_increment_options_length = {
        round_to_increment:{round_to_increment: self.round_to_increment_length}
    };
    // Options for the round_to_increment extender for percents
    self.round_to_increment_options_percent = {
        round_to_increment:{round_to_increment: self.round_to_increment_percent}
    };
    // Options for the round_to_increment extender for speeds
    self.rounding_extender_options_speed = {
        axis_speed_unit:{
            round_to_increment_mm_min: self.round_to_increment_speed_mm_min,
            round_to_increment_mm_sec: self.round_to_increment_speed_mm_min/60,
            current_units_observable: self.get_axis_speed_display_units}};

    // Initialize profile variables from observables
    // Lengths
    self.retraction_distance = ko.observable(Octolapse.roundToIncrement(profile_observables.retract_length, self.round_to_increment_length))
        .extend(self.round_to_increment_options_length);
    self.retraction_vertical_lift = ko.observable(Octolapse.roundToIncrement(profile_observables.z_hop, self.round_to_increment_length))
        .extend(self.round_to_increment_options_length);
    // Speeds
    self.retraction_retract_speed = ko.observable(Octolapse.convertAxisSpeedUnit(profile_observables.retract_speed, self.get_axis_speed_display_units(), profile_observables.axis_speed_display_units, self.round_to_increment_speed_mm_min, 'mm-min'))
        .extend(self.rounding_extender_options_speed);
    self.default_printing_speed = ko.observable(Octolapse.convertAxisSpeedUnit(profile_observables.print_speed, self.get_axis_speed_display_units(), profile_observables.axis_speed_display_units, self.round_to_increment_speed_mm_min, 'mm-min'))
        .extend(self.rounding_extender_options_speed);
    self.xy_axis_movement_speed = ko.observable(Octolapse.convertAxisSpeedUnit(profile_observables.movement_speed, self.get_axis_speed_display_units(), profile_observables.axis_speed_display_units, self.round_to_increment_speed_mm_min, 'mm-min'))
        .extend(self.rounding_extender_options_speed);
    self.z_axis_movement_speed = ko.observable(Octolapse.convertAxisSpeedUnit(profile_observables.z_hop_speed, self.get_axis_speed_display_units(), profile_observables.axis_speed_display_units, self.round_to_increment_speed_mm_min, 'mm-min'))
        .extend(self.rounding_extender_options_speed);
    // Percents
    self.first_layer_speed_multiplier = ko.observable(profile_observables.first_layer_speed_multiplier || self.percent_value_default).extend(self.round_to_increment_options_percent);
    self.above_raft_speed_multiplier = ko.observable(profile_observables.above_raft_speed_multiplier || self.percent_value_default).extend(self.round_to_increment_options_percent);
    self.prime_pillar_speed_multiplier = ko.observable(profile_observables.prime_pillar_speed_multiplier || self.percent_value_default).extend(self.round_to_increment_options_percent);
    self.ooze_shield_speed_multiplier = ko.observable(profile_observables.ooze_shield_speed_multiplier || self.percent_value_default).extend(self.round_to_increment_options_percent);
    self.outline_speed_multiplier = ko.observable(profile_observables.outline_speed_multiplier || self.percent_value_default).extend(self.round_to_increment_options_percent);
    self.solid_infill_speed_multiplier = ko.observable(profile_observables.solid_infill_speed_multiplier || self.percent_value_default).extend(self.round_to_increment_options_percent);
    self.support_structure_speed_multiplier = ko.observable(profile_observables.support_structure_speed_multiplier || self.percent_value_default).extend(self.round_to_increment_options_percent);
    self.bridging_speed_multiplier = ko.observable(profile_observables.bridging_speed_multiplier || self.percent_value_default).extend(self.round_to_increment_options_percent);

    /*
        Create a getter for each profile variable (settings.py - printer class)
    */
    self.get_retract_length = function () {
        return self.retraction_distance();
    };
    self.get_retract_speed = function () {
        return self.retraction_retract_speed();
    };
    self.get_detract_speed = function () {
        return self.retraction_retract_speed();
    };
    self.get_movement_speed = function () {
        return self.xy_axis_movement_speed();
    };
    self.get_z_hop = function () {
        return self.retraction_vertical_lift();
    };
    self.get_z_hop_speed = function () {
        return self.z_axis_movement_speed();
    };
    self.get_print_speed = function () {
        return self.default_printing_speed();
    };
    self.get_perimeter_speed = function () {
        if (self.default_printing_speed() == null || self.outline_speed_multiplier() == null)
            return null;
        var perimeter_speed_multiplier = 100.0 - ((100 - self.outline_speed_multiplier()) / 2.0)
        return Octolapse.roundToIncrement(self.default_printing_speed() * (perimeter_speed_multiplier / 100.0), self.get_speed_tolerance());
    };
    self.get_small_perimeter_speed = function () {
        if (self.default_printing_speed() == null || self.outline_speed_multiplier() == null)
            return null;
        var perimeter_speed_multiplier = 100.0 - ((100 - self.outline_speed_multiplier()) / 2.0)
        return Octolapse.roundToIncrement(self.default_printing_speed() * (perimeter_speed_multiplier / 100.0), self.get_speed_tolerance());
    };
    self.get_external_perimeter_speed = function () {
        if (self.default_printing_speed() == null || self.outline_speed_multiplier() == null)
            return null;
        return Octolapse.roundToIncrement(self.default_printing_speed() * (self.outline_speed_multiplier() / 100.0), self.get_speed_tolerance());
    };
    self.get_infill_speed = function () {
        return self.default_printing_speed();
    };
    self.get_solid_infill_speed = function () {
        if (self.default_printing_speed() == null || self.solid_infill_speed_multiplier() == null)
            return null;
        return Octolapse.roundToIncrement(self.default_printing_speed() * (self.solid_infill_speed_multiplier() / 100.0), self.get_speed_tolerance());
    };
    self.get_top_solid_infill_speed = function () {
        if (self.default_printing_speed() == null || self.solid_infill_speed_multiplier() == null)
            return null;
        return Octolapse.roundToIncrement(self.default_printing_speed() * (self.solid_infill_speed_multiplier() / 100.0), self.get_speed_tolerance());
    };
    self.get_support_speed = function () {
        if (self.default_printing_speed() == null || self.support_structure_speed_multiplier() == null)
            return null;
        return Octolapse.roundToIncrement(self.default_printing_speed() * (self.support_structure_speed_multiplier() / 100.0), self.get_speed_tolerance());
    };
    self.get_bridge_speed = function () {
        if (self.default_printing_speed() == null || self.bridging_speed_multiplier() == null)
            return null;
        return Octolapse.roundToIncrement(self.default_printing_speed() * (self.bridging_speed_multiplier() / 100.0), self.get_speed_tolerance());
    };
    self.get_gap_fill_speed = function () {
        return self.default_printing_speed();
    };
    self.get_print_speed = function () {
        return self.default_printing_speed();
    }
    self.get_first_layer_speed = function () {
        if (self.default_printing_speed() == null || self.first_layer_speed_multiplier() == null)
            return null;
        return Octolapse.roundToIncrement(self.default_printing_speed() * (self.first_layer_speed_multiplier() / 100.0), self.get_speed_tolerance());
    };
    self.get_first_layer_travel_speed = function () {
        return self.xy_axis_movement_speed();
    };
    self.get_skirt_brim_speed = function () {
        return self.default_printing_speed();
    };
    self.get_first_layer_speed_multiplier = function () {
        return self.first_layer_speed_multiplier();
    };
    self.get_above_raft_speed_multiplier = function () {
        return self.above_raft_speed_multiplier();
    };
    self.get_prime_pillar_speed_multiplier = function () {
        return self.prime_pillar_speed_multiplier();
    };
    self.get_ooze_shield_speed_multiplier = function () {
        return self.ooze_shield_speed_multiplier();
    };
    self.get_outline_speed_multiplier = function () {
        return self.outline_speed_multiplier();
    };
    self.get_solid_infill_speed_multiplier = function () {
        return self.solid_infill_speed_multiplier();
    };
    self.get_support_structure_speed_multiplier = function () {
        return self.support_structure_speed_multiplier();
    };
    self.get_bridging_speed_multiplier = function () {
        return self.bridging_speed_multiplier();
    };

    self.get_above_raft_speed = function () {
        if (self.default_printing_speed() == null || self.above_raft_speed_multiplier() == null)
            return null;
        return Octolapse.roundToIncrement(self.default_printing_speed() * (self.above_raft_speed_multiplier() / 100.0), self.get_speed_tolerance());
    };
    self.get_ooze_shield_speed = function () {
        if (self.default_printing_speed() == null || self.ooze_shield_speed_multiplier() == null)
            return null;
        return Octolapse.roundToIncrement(self.default_printing_speed() * (self.ooze_shield_speed_multiplier() / 100.0), self.get_speed_tolerance());
    };
    self.get_prime_pillar_speed = function () {
        if (self.default_printing_speed() == null || self.prime_pillar_speed_multiplier() == null)
            return null;
        return Octolapse.roundToIncrement(self.default_printing_speed() * (self.prime_pillar_speed_multiplier() / 100.0), self.get_speed_tolerance());
    };

    self.get_num_slow_layers = function () {
        return 1;
    }

    self.roundSpeedForUniqueCheck = function (speed) {
        if (speed == null)
            return null;
        speed -= 0.1;
        var rounded_value = Octolapse.roundToIncrement(speed, 1);
        return rounded_value;
    }
    // Get a list of speeds for use with feature detection
    self.getSlicerSpeedList = function () {
        return [
            {speed: self.roundSpeedForUniqueCheck(self.get_retract_speed()), type: "Retraction"},
            {speed: self.roundSpeedForUniqueCheck(self.get_first_layer_speed()), type: "First Layer"},
            {speed: self.roundSpeedForUniqueCheck(self.get_above_raft_speed()), type: "Above Raft"},
            {speed: self.roundSpeedForUniqueCheck(self.get_prime_pillar_speed()), type: "Prime Pillar"},
            {speed: self.roundSpeedForUniqueCheck(self.get_ooze_shield_speed()), type: "Ooze Shield"},
            {speed: self.roundSpeedForUniqueCheck(self.get_print_speed()), type: "Default Printing"},
            {speed: self.roundSpeedForUniqueCheck(self.get_external_perimeter_speed()), type: "Exterior Outlines"},
            {speed: self.roundSpeedForUniqueCheck(self.get_perimeter_speed()), type: "Interior Outlines"},
            {speed: self.roundSpeedForUniqueCheck(self.get_solid_infill_speed()), type: "Solid Infill"},
            {speed: self.roundSpeedForUniqueCheck(self.get_support_speed()), type: "Support Structure"},
            {speed: self.roundSpeedForUniqueCheck(self.get_movement_speed()), type: "X/Y Movement"},
            {speed: self.roundSpeedForUniqueCheck(self.get_z_hop_speed()), type: "Z Movement"},
            {speed: self.roundSpeedForUniqueCheck(self.get_bridge_speed()), type: "Bridging"},

        ];
    };

};
