Octolapse.create_cura_viewmodel = function (profile_observables) {
    var self = this;
    self.get_axis_speed_display_units = function () {
        return 'mm-sec';
    };
    self.get_speed_tolerance = function () {
        // tolerance of 0.1 mm/min / 2
        return 0.1 / 60.0 / 2;
    };

    self.round_to_increment_mm_min = 0.00000166667;
    self.round_to_increment_mm_sec = 0.0001;
    self.round_to_increment_length = 0.0001;
    self.round_to_increment_num_layers = 1;

    self.rounding_extender_options = {
        axis_speed_unit:{
            round_to_increment_mm_min: self.round_to_increment_mm_min,
            round_to_increment_mm_sec:self.round_to_increment_mm_sec,
            current_units_observable: self.get_axis_speed_display_units}};
    // Options for the round_to_increment extender for lengths
    self.round_to_increment_options_lengths = {
        round_to_increment:{round_to_increment: self.round_to_increment_length}
    };
    self.round_to_increment_options_num_layers = {
        round_to_increment:{round_to_increment: self.round_to_increment_num_layers}
    };


    // Initialize profile variables from observables
    self.retraction_distance = ko.observable(profile_observables.retract_length).extend(self.round_to_increment_options_lengths);
    self.z_hop_height = ko.observable(profile_observables.z_hop).extend(self.round_to_increment_options_lengths);

    self.retraction_retract_speed = ko.observable(
        Octolapse.convertAxisSpeedUnit(profile_observables.retract_speed, self.get_axis_speed_display_units(), profile_observables.axis_speed_display_units, self.round_to_increment_mm_sec)).extend(self.rounding_extender_options);

    self.retraction_prime_speed = ko.observable(
        Octolapse.convertAxisSpeedUnit(profile_observables.detract_speed, self.get_axis_speed_display_units(), profile_observables.axis_speed_display_units, self.round_to_increment_mm_sec)).extend(self.rounding_extender_options);
    self.travel_speed = ko.observable(
        Octolapse.convertAxisSpeedUnit(profile_observables.movement_speed, self.get_axis_speed_display_units(), profile_observables.axis_speed_display_units, self.round_to_increment_mm_sec)).extend(self.rounding_extender_options);
    self.inner_wall_speed = ko.observable(
        Octolapse.convertAxisSpeedUnit(profile_observables.perimeter_speed,self.get_axis_speed_display_units(),profile_observables.axis_speed_display_units, self.round_to_increment_mm_sec)).extend(self.rounding_extender_options);
    self.outer_wall_speed = ko.observable(
        Octolapse.convertAxisSpeedUnit(profile_observables.external_perimeter_speed,self.get_axis_speed_display_units(),profile_observables.axis_speed_display_units, self.round_to_increment_mm_sec)).extend(self.rounding_extender_options);
    self.top_bottom_speed = ko.observable(
        Octolapse.convertAxisSpeedUnit(profile_observables.top_solid_infill_speed,self.get_axis_speed_display_units(),profile_observables.axis_speed_display_units, self.round_to_increment_mm_sec)).extend(self.rounding_extender_options);
    self.infill_speed = ko.observable(
        Octolapse.convertAxisSpeedUnit(profile_observables.infill_speed, self.get_axis_speed_display_units(), profile_observables.axis_speed_display_units, self.round_to_increment_mm_sec)).extend(self.rounding_extender_options);
    self.print_speed = ko.observable(
        Octolapse.convertAxisSpeedUnit(profile_observables.print_speed, self.get_axis_speed_display_units(), profile_observables.axis_speed_display_units, self.round_to_increment_mm_sec)).extend(self.rounding_extender_options);
    self.initial_layer_print_speed = ko.observable(
        Octolapse.convertAxisSpeedUnit(profile_observables.first_layer_speed, self.get_axis_speed_display_units(), profile_observables.axis_speed_display_units, self.round_to_increment_mm_sec)).extend(self.rounding_extender_options);
    self.initial_layer_travel_speed = ko.observable(
        Octolapse.convertAxisSpeedUnit(profile_observables.first_layer_travel_speed, self.get_axis_speed_display_units(), profile_observables.axis_speed_display_units, self.round_to_increment_mm_sec)).extend(self.rounding_extender_options);
    self.skirt_brim_speed = ko.observable(
        Octolapse.convertAxisSpeedUnit(profile_observables.skirt_brim_speed, self.get_axis_speed_display_units(), profile_observables.axis_speed_display_units, self.round_to_increment_mm_sec)).extend(self.rounding_extender_options);
    self.maximum_z_speed = ko.observable(
        Octolapse.convertAxisSpeedUnit(profile_observables.maximum_z_speed, self.get_axis_speed_display_units(), profile_observables.axis_speed_display_units, self.round_to_increment_mm_sec)).extend(self.rounding_extender_options);

    self.num_slow_layers = ko.observable(profile_observables.num_slow_layers).extend(self.round_to_increment_options_num_layers);
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
        return self.retraction_prime_speed();
    };
    self.get_movement_speed = function () {
        return self.travel_speed();
    };
    self.get_z_hop = function () {
        return self.z_hop_height();
    };
    self.get_z_hop_speed = function () {
        var maximum_z_speed = self.maximum_z_speed()
        if ((maximum_z_speed || 0) == 0 || maximum_z_speed > self.travel_speed())
            return self.travel_speed();

        return maximum_z_speed;
    };
    self.get_maximum_z_speed = function () {
        return self.maximum_z_speed();
    };
    self.get_print_speed = function () {
        return self.print_speed();
    };
    self.get_perimeter_speed = function () {
        return self.inner_wall_speed();
    };
    self.get_small_perimeter_speed = function () {
        return self.inner_wall_speed();
    };
    self.get_external_perimeter_speed = function () {
        return self.outer_wall_speed();
    };
    self.get_infill_speed = function () {
        return self.infill_speed();
    };
    self.get_solid_infill_speed = function () {
        return self.infill_speed();
    };
    self.get_top_solid_infill_speed = function () {
        return self.top_bottom_speed();
    };
    self.get_support_speed = function () {
        return self.print_speed();
    };
    self.get_bridge_speed = function () {
        return self.outer_wall_speed();
    };
    self.get_gap_fill_speed = function () {
        return self.print_speed();
    };
    self.get_print_speed = function () {
        return self.print_speed();
    }
    self.get_first_layer_speed = function () {
        return self.initial_layer_print_speed();
    };
    self.get_first_layer_travel_speed = function () {
        return self.initial_layer_travel_speed();
    };
    self.get_skirt_brim_speed = function () {
        return self.skirt_brim_speed();
    };
    self.get_num_slow_layers = function () {
        return self.num_slow_layers();
    }
    // Get a list of speeds for use with feature detection
    self.getSlicerSpeedList = function () {
        return [
            {speed: Octolapse.roundToIncrement(self.print_speed() * 60.0, 0.1), type: "Normal Print"},
            {speed: Octolapse.roundToIncrement(self.retraction_retract_speed() * 60.0, 0.1), type: "Retract"},
            {speed: Octolapse.roundToIncrement(self.retraction_prime_speed() * 60.0, 0.1), type: "Prime"},
            {speed: Octolapse.roundToIncrement(self.infill_speed() * 60.0, 0.1), type: "Infill"},
            {speed: Octolapse.roundToIncrement(self.outer_wall_speed() * 60.0, 0.1), type: "Outer Wall"},
            {speed: Octolapse.roundToIncrement(self.inner_wall_speed() * 60.0, 0.1), type: "Inner Wall"},
            {speed: Octolapse.roundToIncrement(self.top_bottom_speed() * 60.0, 0.1), type: "Top/Bottom"},
            {speed: Octolapse.roundToIncrement(self.travel_speed() * 60.0, 0.1), type: "Travel"},
            {speed: Octolapse.roundToIncrement(self.initial_layer_print_speed() * 60.0, 0.1), type: "Initial Layer"},
            {
                speed: Octolapse.roundToIncrement(self.initial_layer_travel_speed() * 60.0, 0.1),
                type: "Initial Layer Travel"
            },
            {speed: Octolapse.roundToIncrement(self.skirt_brim_speed() * 60.0, 0.1), type: "Skirt/Brim"},
            {speed: Octolapse.roundToIncrement(self.get_z_hop_speed() * 60.0, 0.1), type: "Z Travel"},
        ];
    };

};
