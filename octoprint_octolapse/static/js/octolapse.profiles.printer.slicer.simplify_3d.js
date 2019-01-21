Octolapse.Simplify3dViewModel = function (values) {
    var self = this;

    // Observables
    self.retraction_distance = ko.observable(values.retraction_distance);
    self.retraction_vertical_lift = ko.observable(values.retraction_vertical_lift);
    self.retraction_speed = ko.observable(values.retraction_speed);
    self.first_layer_speed_multiplier = ko.observable(values.first_layer_speed_multiplier);
    self.above_raft_speed_multiplier = ko.observable(values.above_raft_speed_multiplier);
    self.prime_pillar_speed_multiplier = ko.observable(values.prime_pillar_speed_multiplier);
    self.ooze_shield_speed_multiplier = ko.observable(values.ooze_shield_speed_multiplier);
    self.default_printing_speed = ko.observable(values.default_printing_speed);
    self.outline_speed_multiplier = ko.observable(values.outline_speed_multiplier);
    self.solid_infill_speed_multiplier = ko.observable(values.solid_infill_speed_multiplier);
    self.support_structure_speed_multiplier = ko.observable(values.support_structure_speed_multiplier);
    self.x_y_axis_movement_speed = ko.observable(values.x_y_axis_movement_speed);
    self.z_axis_movement_speed = ko.observable(values.z_axis_movement_speed);
    self.bridging_speed_multiplier = ko.observable(values.bridging_speed_multiplier);

    self.get_all_speed_settings = function()
    {
        return [
            self.retraction_speed,
            self.first_layer_speed_multiplier,
            self.above_raft_speed_multiplier,
            self.prime_pillar_speed_multiplier,
            self.ooze_shield_speed_multiplier,
            self.default_printing_speed,
            self.outline_speed_multiplier,
            self.solid_infill_speed_multiplier,
            self.support_structure_speed_multiplier,
            self.x_y_axis_movement_speed,
            self.z_axis_movement_speed,
            self.bridging_speed_multiplier
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
