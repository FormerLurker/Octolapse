/// Create our printers view model
$(function() {
    Octolapse.PrinterProfileValidationRules = {
        rules: {
           
        },
        messages: {
            name: "Please enter a name for your profile"
        }
        
    };

    Octolapse.PrinterProfileViewModel = function (values) {
        var self = this;
        self.guid = ko.observable(values.guid);
        self.name = ko.observable(values.name);
        self.description = ko.observable(values.description);
        self.retract_length = ko.observable(values.retract_length);
        self.retract_speed = ko.observable(values.retract_speed);
        self.detract_speed = ko.observable(values.detract_speed);
        self.movement_speed = ko.observable(values.movement_speed);
        self.z_hop = ko.observable(values.z_hop);
        self.z_hop_speed = ko.observable(values.z_hop_speed);
        self.snapshot_command = ko.observable(values.snapshot_command);
        self.printer_position_confirmation_tolerance = ko.observable(values.printer_position_confirmation_tolerance);
        self.auto_detect_origin = ko.observable(values.auto_detect_origin);
        self.origin_x = ko.observable(values.origin_x);
        self.origin_y = ko.observable(values.origin_y);
        self.origin_z = ko.observable(values.origin_z);
        self.abort_out_of_bounds = ko.observable(values.abort_out_of_bounds);
        self.min_x = ko.observable(values.min_x);
        self.max_x = ko.observable(values.max_x);
        self.min_y = ko.observable(values.min_y);
        self.max_y = ko.observable(values.max_y);
        self.min_z = ko.observable(values.min_z);
        self.max_z = ko.observable(values.max_z);

    };
});
