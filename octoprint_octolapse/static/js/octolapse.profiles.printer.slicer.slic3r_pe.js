Octolapse.Slic3rPeViewModel = function (values) {
    var self = this;

    // Observables
    self.retract_length = ko.observable(values.retract_length);
    self.retract_lift = ko.observable(values.retract_lift);
    self.retract_speed  = ko.observable(values.retract_speed);
    self.deretract_speed = ko.observable(values.deretract_speed);
    self.travel_speed = ko.observable(values.travel_speed);
    self.layer_height = ko.observable(values.layer_height);
    self.spiral_vase = ko.observable(values.spiral_vase);
    self.retract_before_travel = ko.pureComputed(function () {
        if (self.retract_length() != null && self.retract_length() > 0)
            return true;
        return false;
    }, self);

    // Constants
    self.speed_tolerance = 0.01 / 60.0 / 2.0;
    self.axis_speed_display_units = 'mm-sec';

    self.round_to_increment_mm_min = 0.00000166667;
    self.round_to_increment_mm_sec = 0.0001;
    self.round_to_percent = 0.0001;
    self.round_to_increment_retraction_length = 0.000001;
    self.round_to_increment_lift_z = 0.0001;

};
