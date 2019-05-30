Octolapse.OtherSlicerViewModel = function (values) {
    var self = this;
    // Create Observables
    self.retract_length = ko.observable(values.retract_length);
    self.z_hop = ko.observable(values.z_hop);
    self.travel_speed = ko.observable(values.travel_speed);
    self.retract_speed = ko.observable(values.retract_speed);
    self.deretract_speed = ko.observable(values.deretract_speed);
    self.z_travel_speed = ko.observable(values.z_travel_speed);
    self.speed_tolerance = ko.observable(values.speed_tolerance);
    self.vase_mode = ko.observable(values.vase_mode);
    self.layer_height = ko.observable(values.layer_height);
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
            self.retract_speed,
            self.deretract_speed,
            self.z_travel_speed,
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
                return true;
            }
        }
    };
};
