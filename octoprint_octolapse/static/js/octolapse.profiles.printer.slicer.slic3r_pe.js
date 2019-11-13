Octolapse.Slic3rPeExtruderViewModel = function (values, extruder_index) {
    var self=this;
    self.index = extruder_index;
    self.retract_length = ko.observable(null);
    self.retract_lift = ko.observable(null);
    self.retract_speed = ko.observable(null);
    self.deretract_speed = ko.observable(null);

    if (values && values.extruders.length > self.index) {
        var extruder = values.extruders[self.index];
        if (!extruder)
            return;
        self.retract_length(extruder.retract_length);
        self.retract_lift(extruder.retract_lift);
        self.retract_speed(extruder.retract_speed);
        self.deretract_speed(extruder.deretract_speed);
    }
};


Octolapse.Slic3rPeViewModel = function (values, num_extruders_observable) {
    var self = this;
    // Observables

    self.num_extruders_observable = num_extruders_observable;
    var extruders = [];
    for (var index = 0; index < self.num_extruders_observable(); index++)
    {
        extruders.push(new Octolapse.Slic3rPeExtruderViewModel(values, index));
    }
    self.extruders = ko.observableArray(extruders);
    self.travel_speed = ko.observable(values.travel_speed);
    self.layer_height = ko.observable(values.layer_height);
    self.spiral_vase = ko.observable(values.spiral_vase || false);
    // Constants
    self.speed_tolerance = 0.01 / 60.0 / 2.0;
    self.axis_speed_display_units = 'mm-sec';

    self.round_to_increment_mm_min = 0.00000166667;
    self.round_to_increment_mm_sec = 0.0001;
    self.round_to_percent = 0.0001;
    self.round_to_increment_retraction_length = 0.000001;
    self.round_to_increment_lift_z = 0.0001;

    self.num_extruders_observable.subscribe(function() {
        var num_extruders = self.num_extruders_observable();
        if (num_extruders < 1) {
            num_extruders = 1;
        }
        else if (num_extruders > 16){
            num_extruders = 16;
        }
        var extruders = self.extruders();
        while(extruders.length < num_extruders)
        {
            var new_extruder = new Octolapse.Slic3rPeExtruderViewModel(null, extruders.length-1);
            extruders.push(new_extruder);
        }
        while(extruders.length > num_extruders)
        {
             extruders.pop();
        }
        self.extruders(extruders);

    });
};
