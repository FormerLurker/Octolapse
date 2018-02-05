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


    };
});
