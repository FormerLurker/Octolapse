Octolapse.OtherSlicerViewModel = function (values) {
    var self = this;
    // Create Observables
    self.retract_length = ko.observable(values.retract_length);
    self.z_hop = ko.observable(values.z_hop);
    self.travel_speed = ko.observable(values.travel_speed);
    self.first_layer_travel_speed = ko.observable(values.first_layer_travel_speed);
    self.retract_speed = ko.observable(values.retract_speed);
    self.deretract_speed = ko.observable(values.deretract_speed);
    self.print_speed = ko.observable(values.print_speed);
    self.first_layer_print_speed = ko.observable(values.first_layer_print_speed);
    self.z_travel_speed = ko.observable(values.z_travel_speed);
    self.perimeter_speed = ko.observable(values.perimeter_speed);
    self.small_perimeter_speed = ko.observable(values.small_perimeter_speed);
    self.external_perimeter_speed = ko.observable(values.external_perimeter_speed);
    self.infill_speed = ko.observable(values.infill_speed);
    self.solid_infill_speed = ko.observable(values.solid_infill_speed);
    self.top_solid_infill_speed = ko.observable(values.top_solid_infill_speed);
    self.support_speed = ko.observable(values.support_speed);
    self.bridge_speed = ko.observable(values.bridge_speed);
    self.gap_fill_speed = ko.observable(values.gap_fill_speed);
    self.skirt_brim_speed = ko.observable(values.skirt_brim_speed);
    self.above_raft_speed = ko.observable(values.above_raft_speed);
    self.ooze_shield_speed = ko.observable(values.ooze_shield_speed);
    self.prime_pillar_speed = ko.observable(values.prime_pillar_speed);
    self.num_slow_layers = ko.observable(values.num_slow_layers);
    self.speed_tolerance = ko.observable(values.speed_tolerance);
    self.axis_speed_display_units = ko.observable(values.axis_speed_display_units);

    self.retract_before_move = ko.pureComputed(function () {
        if (self.retract_length() != null && self.retract_length() > 0)
            return true;
        return false;
    }, self);
    self.lift_when_retracted = ko.pureComputed(function () {
        if (self.retract_before_move() && self.z_hop() != null && self.z_hop() > 0)
            return true;
        return false;
    }, self);

    self.get_all_speed_settings = function()
    {
        return [
            self.travel_speed,
            self.first_layer_travel_speed,
            self.retract_speed,
            self.deretract_speed,
            self.print_speed,
            self.first_layer_print_speed,
            self.z_travel_speed,
            self.perimeter_speed,
            self.small_perimeter_speed,
            self.external_perimeter_speed,
            self.infill_speed,
            self.solid_infill_speed,
            self.top_solid_infill_speed,
            self.support_speed,
            self.bridge_speed,
            self.gap_fill_speed,
            self.skirt_brim_speed,
            self.above_raft_speed,
            self.ooze_shield_speed,
            self.prime_pillar_speed,
            self.num_slow_layers,
            self.speed_tolerance,
            self.axis_speed_display_units
        ]
    };

    // Declare constants
    self.round_to_increment_mm_min = 0.001;
    self.round_to_increment_mm_sec = 0.000001;

    // get the time component of the axis speed units (min/mm)
    self.getAxisSpeedTimeUnit = ko.pureComputed(function () {
        if (self.axis_speed_display_units() === "mm-min")
            return 'min';
        if (self.axis_speed_display_units() === "mm-sec")
            return 'sec';
        return '?';
    }, self);



    self.axisSpeedDisplayUnitsChanged = function (obj, event) {

        if (Octolapse.Globals.is_admin()) {
            if (event.originalEvent) {
                // Get the current guid
                var newUnit = $("#octolapse_axis_speed_display_unit_options").val();
                var previousUnit = self.axis_speed_display_units();
                if (newUnit === previousUnit) {
                    //console.log("Axis speed display units, no change detected!")
                    return false;

                }
                //console.log("Changing axis speed from " + previousUnit + " to " + newUnit)
                // in case we want to have more units in the future, check all cases
                // Convert all from mm-min to mm-sec

                var axis_speed_round_to_increment = 0.000001;
                var axis_speed_round_to_unit = 'mm-sec';
                self.speed_tolerance(Octolapse.convertAxisSpeedUnit(self.speed_tolerance(), newUnit, previousUnit, axis_speed_round_to_increment, axis_speed_round_to_unit));

                self.retract_speed(Octolapse.convertAxisSpeedUnit(self.retract_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.deretract_speed(Octolapse.convertAxisSpeedUnit(self.deretract_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.travel_speed(Octolapse.convertAxisSpeedUnit(self.travel_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.z_travel_speed(Octolapse.convertAxisSpeedUnit(self.z_travel_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));

                // Optional values
                self.print_speed(Octolapse.convertAxisSpeedUnit(self.print_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.perimeter_speed(Octolapse.convertAxisSpeedUnit(self.perimeter_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.small_perimeter_speed(Octolapse.convertAxisSpeedUnit(self.small_perimeter_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.external_perimeter_speed(Octolapse.convertAxisSpeedUnit(self.external_perimeter_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.infill_speed(Octolapse.convertAxisSpeedUnit(self.infill_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.solid_infill_speed(Octolapse.convertAxisSpeedUnit(self.solid_infill_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.top_solid_infill_speed(Octolapse.convertAxisSpeedUnit(self.top_solid_infill_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.support_speed(Octolapse.convertAxisSpeedUnit(self.support_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.bridge_speed(Octolapse.convertAxisSpeedUnit(self.bridge_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));

                self.gap_fill_speed(Octolapse.convertAxisSpeedUnit(self.gap_fill_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.first_layer_print_speed(Octolapse.convertAxisSpeedUnit(self.first_layer_print_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.first_layer_travel_speed(Octolapse.convertAxisSpeedUnit(self.first_layer_travel_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.skirt_brim_speed(Octolapse.convertAxisSpeedUnit(self.skirt_brim_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));

                self.above_raft_speed(Octolapse.convertAxisSpeedUnit(self.above_raft_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.ooze_shield_speed(Octolapse.convertAxisSpeedUnit(self.ooze_shield_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                self.prime_pillar_speed(Octolapse.convertAxisSpeedUnit(self.prime_pillar_speed(), newUnit, previousUnit, self.round_to_increment_mm_min, previousUnit));
                return true;
            }
        }
    };
};
