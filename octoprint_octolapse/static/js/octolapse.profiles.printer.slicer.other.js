Octolapse.create_other_slicer_viewmodel = function (profile_observables) {
    var self = this;
    self.round_to_increment_mm_min = 0.001;
    self.round_to_increment_mm_sec = 0.000001;

    self.axis_speed_display_units = ko.observable(profile_observables.axis_speed_display_units);
    self.retract_length = ko.observable(profile_observables.retract_length).extend({numeric: 4});

    self.z_hop = ko.observable(profile_observables.z_hop).extend({numeric: 4});

    self.rounding_extender_options = {axis_speed_unit:{round_to_increment_mm_min: self.round_to_increment_mm_min,round_to_increment_mm_sec:self.round_to_increment_mm_sec,current_units_observable: self.axis_speed_display_units}};
    self.speed_tolerance = ko.observable(profile_observables.speed_tolerance).extend(self.rounding_extender_options);
    self.movement_speed = ko.observable(profile_observables.movement_speed).extend(self.rounding_extender_options);
    self.retract_speed = ko.observable(profile_observables.retract_speed).extend(self.rounding_extender_options);
    self.detract_speed = ko.observable(profile_observables.detract_speed).extend(self.rounding_extender_options);
    self.print_speed = ko.observable(profile_observables.print_speed).extend(self.rounding_extender_options);
    self.z_hop_speed = ko.observable(profile_observables.z_hop_speed).extend(self.rounding_extender_options);
    self.perimeter_speed = ko.observable(profile_observables.perimeter_speed).extend(self.rounding_extender_options);
    self.small_perimeter_speed = ko.observable(profile_observables.small_perimeter_speed).extend(self.rounding_extender_options);
    self.external_perimeter_speed = ko.observable(profile_observables.external_perimeter_speed).extend(self.rounding_extender_options);
    self.infill_speed = ko.observable(profile_observables.infill_speed).extend(self.rounding_extender_options);
    self.solid_infill_speed = ko.observable(profile_observables.solid_infill_speed).extend(self.rounding_extender_options);
    self.top_solid_infill_speed = ko.observable(profile_observables.top_solid_infill_speed).extend(self.rounding_extender_options);
    self.support_speed = ko.observable(profile_observables.support_speed).extend(self.rounding_extender_options);
    self.bridge_speed = ko.observable(profile_observables.bridge_speed).extend(self.rounding_extender_options);
    self.gap_fill_speed = ko.observable(profile_observables.gap_fill_speed).extend(self.rounding_extender_options);
    self.first_layer_speed = ko.observable(profile_observables.first_layer_speed).extend(self.rounding_extender_options);
    self.first_layer_travel_speed = ko.observable(profile_observables.first_layer_travel_speed).extend(self.rounding_extender_options);
    self.skirt_brim_speed = ko.observable(profile_observables.skirt_brim_speed).extend(self.rounding_extender_options);
    self.above_raft_speed = ko.observable(profile_observables.above_raft_speed).extend(self.rounding_extender_options);
    self.ooze_shield_speed = ko.observable(profile_observables.ooze_shield_speed).extend(self.rounding_extender_options);
    self.prime_pillar_speed = ko.observable(profile_observables.prime_pillar_speed).extend(self.rounding_extender_options);

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
        return self.detract_speed();
    };
    self.get_movement_speed = function () {
        return self.movement_speed();
    };
    self.get_z_hop = function () {
        return self.z_hop();
    };
    self.get_z_hop_speed = function () {
        return self.z_hop_speed();
    };
    self.get_maximum_z_speed = function () {
        return null;
    };
    self.get_print_speed = function () {
        return self.print_speed();
    };
    self.get_perimeter_speed = function () {
        return self.perimeter_speed();
    };
    self.get_small_perimeter_speed = function () {
        return self.small_perimeter_speed();
    };
    self.get_external_perimeter_speed = function () {
        return self.external_perimeter_speed();
    };
    self.get_infill_speed = function () {
        return self.infill_speed();
    };
    self.get_solid_infill_speed = function () {
        return self.solid_infill_speed();
    };
    self.get_top_solid_infill_speed = function () {
        return self.top_solid_infill_speed();
    };
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
        return self.first_layer_speed();
    };
    self.get_first_layer_travel_speed = function () {
        return self.first_layer_travel_speed();
    };
    self.get_skirt_brim_speed = function () {
        return self.skirt_brim_speed();
    };
    self.get_above_raft_speed = function () {
        return self.above_raft_speed();
    };
    self.get_ooze_shield_speed = function () {
        return self.ooze_shield_speed();
    };
    self.get_prime_pillar_speed = function () {
        return self.prime_pillar_speed();
    };
    self.get_speed_tolerance = function () {
        return self.speed_tolerance();
    };
    self.get_axis_speed_display_units = function () {
        return self.axis_speed_display_units();
    };
    // get the time component of the axis speed units (min/mm)
    self.getAxisSpeedTimeUnit = ko.pureComputed(function () {
        if (self.axis_speed_display_units() === "mm-min")
            return 'min';
        if (self.axis_speed_display_units() === "mm-sec")
            return 'sec';
        return '?';
    }, self);
    self.get_num_slow_layers = function () {
        return 0;
    }
    // Get a list of speeds for use with feature detection
    self.getSlicerSpeedList = function () {
        var conv = 1;
        if (self.axis_speed_display_units() === "mm-sec")
            conv = 60;

        var speedTolerance = self.get_speed_tolerance()

        return [
            {speed: Octolapse.roundToIncrement(self.movement_speed() * conv, self.get_speed_tolerance() * conv), type: "Movement"},
            {speed: Octolapse.roundToIncrement(self.z_hop_speed() * conv, self.get_speed_tolerance() * conv), type: "Z Movement"},
            {speed: Octolapse.roundToIncrement(self.retract_speed() * conv, self.get_speed_tolerance() * conv), type: "Retraction"},
            {speed: Octolapse.roundToIncrement(self.detract_speed() * conv, self.get_speed_tolerance() * conv), type: "Detraction"},
            {speed: Octolapse.roundToIncrement(self.print_speed() * conv, self.get_speed_tolerance() * conv), type: "Print"},
            {speed: Octolapse.roundToIncrement(self.perimeter_speed() * conv, self.get_speed_tolerance() * conv), type: "Perimeter"},
            {speed: Octolapse.roundToIncrement(self.small_perimeter_speed() * conv, self.get_speed_tolerance() * conv), type: "Small Perimeter"},
            {speed: Octolapse.roundToIncrement(self.external_perimeter_speed() * conv, self.get_speed_tolerance() * conv), type: "External Perimeter"},
            {speed: Octolapse.roundToIncrement(self.infill_speed() * conv, self.get_speed_tolerance() * conv), type: "Infill"},
            {speed: Octolapse.roundToIncrement(self.solid_infill_speed() * conv, self.get_speed_tolerance() * conv), type: "Solid Infill"},
            {speed: Octolapse.roundToIncrement(self.top_solid_infill_speed() * conv, self.get_speed_tolerance() * conv), type: "Top Solid Infill"},
            {speed: Octolapse.roundToIncrement(self.support_speed() * conv, self.get_speed_tolerance() * conv), type: "Support"},
            {speed: Octolapse.roundToIncrement(self.bridge_speed() * conv, self.get_speed_tolerance() * conv), type: "Bridge"},
            {speed: Octolapse.roundToIncrement(self.gap_fill_speed() * conv, self.get_speed_tolerance() * conv), type: "Gap Fill"},
            {speed: Octolapse.roundToIncrement(self.first_layer_speed() * conv, self.get_speed_tolerance() * conv), type: "First Layer"},
            {speed: Octolapse.roundToIncrement(self.first_layer_travel_speed() * conv, self.get_speed_tolerance() * conv), type: "First Layer Travel"},
            {speed: Octolapse.roundToIncrement(self.above_raft_speed() * conv, self.get_speed_tolerance() * conv), type: "Above Raft"},
            {speed: Octolapse.roundToIncrement(self.ooze_shield_speed() * conv, self.get_speed_tolerance() * conv), type: "Ooze Shield"},
            {speed: Octolapse.roundToIncrement(self.prime_pillar_speed() * conv, self.get_speed_tolerance() * conv), type: "Prime Pillar"},
            {speed: Octolapse.roundToIncrement(self.skirt_brim_speed() * conv, self.get_speed_tolerance() * conv), type: "Skirt/Brim"}

        ];
    };
    self.axisSpeedDisplayUnitsChanged = function (obj, event) {

        if (Octolapse.Globals.is_admin()) {
            if (event.originalEvent) {
                // Get the current guid
                var newUnit = $("#octolapse_axis_speed_display_unit_options").val();
                var previousUnit = self.get_axis_speed_display_units();
                if (newUnit === previousUnit) {
                    //console.log("Axis speed display units, no change detected!")
                    return false;

                }
                //console.log("Changing axis speed from " + previousUnit + " to " + newUnit)
                // in case we want to have more units in the future, check all cases
                // Convert all from mm-min to mm-sec

                var axis_speed_round_to_increment = 0.000001;
                var axis_speed_round_to_unit = 'mm-sec';
                self.speed_tolerance(Octolapse.convertAxisSpeedUnit(self.get_speed_tolerance(), newUnit, previousUnit, axis_speed_round_to_increment, axis_speed_round_to_unit));

                self.retract_speed(Octolapse.convertAxisSpeedUnit(self.get_retract_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.detract_speed(Octolapse.convertAxisSpeedUnit(self.get_detract_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.movement_speed(Octolapse.convertAxisSpeedUnit(self.get_movement_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.z_hop_speed(Octolapse.convertAxisSpeedUnit(self.get_z_hop_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));

                // Optional values
                self.print_speed(Octolapse.convertAxisSpeedUnit(self.get_print_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.perimeter_speed(Octolapse.convertAxisSpeedUnit(self.get_perimeter_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.small_perimeter_speed(Octolapse.convertAxisSpeedUnit(self.get_small_perimeter_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.external_perimeter_speed(Octolapse.convertAxisSpeedUnit(self.get_external_perimeter_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.infill_speed(Octolapse.convertAxisSpeedUnit(self.get_infill_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.solid_infill_speed(Octolapse.convertAxisSpeedUnit(self.get_solid_infill_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.top_solid_infill_speed(Octolapse.convertAxisSpeedUnit(self.get_top_solid_infill_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.support_speed(Octolapse.convertAxisSpeedUnit(self.get_support_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.bridge_speed(Octolapse.convertAxisSpeedUnit(self.get_bridge_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));

                self.gap_fill_speed(Octolapse.convertAxisSpeedUnit(self.get_gap_fill_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.first_layer_speed(Octolapse.convertAxisSpeedUnit(self.get_first_layer_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.first_layer_travel_speed(Octolapse.convertAxisSpeedUnit(self.get_first_layer_travel_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.skirt_brim_speed(Octolapse.convertAxisSpeedUnit(self.get_skirt_brim_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));

                self.above_raft_speed(Octolapse.convertAxisSpeedUnit(self.get_above_raft_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.ooze_shield_speed(Octolapse.convertAxisSpeedUnit(self.get_ooze_shield_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.prime_pillar_speed(Octolapse.convertAxisSpeedUnit(self.get_prime_pillar_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                return true;
            }
        }
    };
};
