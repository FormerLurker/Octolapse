Octolapse.CuraViewmodel = function (values) {
    var self = this;

    // Create Observables
    self.retraction_amount = ko.observable(values.retraction_amount)
    self.retraction_retract_speed = ko.observable(values.retraction_retract_speed)
    self.retraction_prime_speed = ko.observable(values.retraction_prime_speed)
    self.speed_print = ko.observable(values.speed_print)
    self.speed_infill = ko.observable(values.speed_infill)
    self.speed_wall_0 = ko.observable(values.speed_wall_0)
    self.speed_wall_x = ko.observable(values.speed_wall_x)
    self.speed_topbottom = ko.observable(values.speed_topbottom)
    self.speed_travel = ko.observable(values.speed_travel)
    self.speed_print_layer_0 = ko.observable(values.speed_print_layer_0)
    self.speed_travel_layer_0 = ko.observable(values.speed_travel_layer_0)
    self.skirt_brim_speed = ko.observable(values.skirt_brim_speed)
    self.max_feedrate_z_override = ko.observable(values.max_feedrate_z_override)
    self.speed_slowdown_layers = ko.observable(values.speed_slowdown_layers)
    self.retraction_hop = ko.observable(values.retraction_hop)

    // Create constants
    self.speed_tolerance = 0.1 / 60.0 / 2.0
    self.round_to_increment_mm_min = 0.00000166667;
    self.round_to_increment_mm_sec = 0.0001;
    self.round_to_increment_length = 0.0001;
    self.round_to_increment_num_layers = 1;

    self.get_all_speed_settings = function()
    {
        return [
            self.retraction_retract_speed,
            self.retraction_prime_speed,
            self.speed_print,
            self.speed_infill,
            self.speed_wall_0,
            self.speed_wall_x,
            self.speed_topbottom,
            self.speed_travel,
            self.speed_print_layer_0,
            self.speed_travel_layer_0,
            self.skirt_brim_speed,
            self.max_feedrate_z_override,
            self.speed_slowdown_layers,
        ]
    }
};
