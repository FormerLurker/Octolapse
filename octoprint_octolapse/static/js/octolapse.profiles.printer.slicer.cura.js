Octolapse.CuraViewmodel = function (values) {
    var self = this;

    // Create Observables
    self.retraction_amount = ko.observable(values.retraction_amount);
    self.retraction_retract_speed = ko.observable(values.retraction_retract_speed);
    self.retraction_prime_speed = ko.observable(values.retraction_prime_speed);
    self.speed_travel = ko.observable(values.speed_travel);
    self.max_feedrate_z_override = ko.observable(values.max_feedrate_z_override);
    self.speed_z_hop = ko.observable(values.speed_z_hop);
    self.retraction_hop = ko.observable(values.retraction_hop);
    self.retraction_hop_enabled = ko.observable(values.retraction_hop_enabled);
    self.retraction_enable = ko.observable(values.retraction_enable);
    self.layer_height = ko.observable(values.layer_height);
    self.smooth_spiralized_contours = ko.observable(values.smooth_spiralized_contours);
    self.magic_mesh_surface_mode = ko.observable(values.magic_mesh_surface_mode);
    // Create constants
    self.speed_tolerance = 0.1 / 60.0 / 2.0;
    self.round_to_increment_mm_min = 0.00000166667;
    self.round_to_increment_mm_sec = 0.0001;
    self.round_to_increment_length = 0.0001;
    self.round_to_increment_num_layers = 1;

    self.get_all_speed_settings = function()
    {
        return [
            self.retraction_retract_speed,
            self.retraction_prime_speed,
            self.speed_travel,
            self.max_feedrate_z_override,
        ]
    }
};
