Octolapse.Simplify3dViewModel = function (values) {
    var self = this;

    // Observables
    self.retraction_distance = ko.observable(values.retraction_distance);
    self.retraction_vertical_lift = ko.observable(values.retraction_vertical_lift);
    self.retraction_speed = ko.observable(values.retraction_speed);
    self.x_y_axis_movement_speed = ko.observable(values.x_y_axis_movement_speed);
    self.z_axis_movement_speed = ko.observable(values.z_axis_movement_speed);
    self.extruder_use_retract = ko.observable(values.extruder_use_retract);
    self.spiral_vase_mode = ko.observable(values.spiral_vase_mode);
    self.layer_height = ko.observable(values.layer_height);
    self.get_all_speed_settings = function()
    {
        return [
            self.retraction_speed,
            self.x_y_axis_movement_speed,
            self.z_axis_movement_speed,
        ]
    };
    // Constants
    self.speed_tolerance = values.speed_tolerance
    self.axis_speed_display_settings = 'mm-min'
    self.round_to_increment_percent = 1;
    self.round_to_increment_speed_mm_min = 0.1;
    self.round_to_increment_length = 0.01;
    self.percent_value_default = 100.0;

};
