/// Create our printers view model
$(function() {
    Octolapse.PrinterProfileValidationRules = {
        rules: {
            name: "required"
        },
        messages: {
            name: "Please enter a name for your profile",
            retract_length: "Please enter a retraction length",
            retract_speed: "Please enter a retraction speed",
            detract_speed: "Please enter a detraction speed",
            movement_speed: "Please enter a movement speed",
            z_hop: "Please enter a height for z-hop",
            snapshot_command: "Please enter a custom command that will trigger snapshots"
        }
    };

    Octolapse.PrinterProfileViewModel = function(values) {
        self = this
        self.name = ko.observable(values.name);
        self.guid = ko.observable(values.guid);
        self.retract_length = ko.observable(values.retract_length);
        self.retract_speed = ko.observable(values.retract_speed);
        self.detract_speed = ko.observable(values.detract_speed);
        self.movement_speed = ko.observable(values.movement_speed);
        self.z_hop = ko.observable(values.z_hop);
        self.snapshot_command = ko.observable(values.snapshot_command);
        self.printer_position_confirmation_tolerance = ko.observable(values.printer_position_confirmation_tolerance);
    }
});
