$(function () {
    function OctolapseSettingsViewModel(parameters) {
        var self = this;
        self.global_settings = parameters[0];

        self.is_octolapse_enabled = ko.observable();

        self.current_printer_guid = ko.observable();
        self.printers = ko.observableArray();

        self.current_stabilization_guid = ko.observable();
        self.stabilizations = ko.observableArray();

        self.current_snapshot_guid = ko.observable();
        self.snapshots = ko.observableArray();

        self.current_rendering_guid = ko.observable();
        self.renderings = ko.observableArray();

        self.current_camera_guid = ko.observable();
        self.cameras = ko.observableArray();
        // Dropdowns
        self.printer_dropdown = ko.observable();

        self.onBeforeBinding = function () {
            self.settings = self.global_settings.settings.plugins.octolapse;

            self.is_octolapse_enabled(self.settings.is_octolapse_enabled);
            self.current_printer_guid(self.settings.current_printer_guid);
            self.current_stabilization_guid(self.settings.current_stabilization_guid);
            self.current_snapshot_guid(self.settings.current_snapshot_guid);
            self.current_rendering_guid(self.settings.current_rendering_guid);
            self.current_camera_guid(self.settings.current_camera_guid);

            self.printers(self.settings.printers);
            self.stabilizations(self.settings.stabilizations);
            self.snapshots(self.settings.snapshots);
            self.renderings(self.settings.renderings);
            self.cameras(self.settings.cameras);

            

        }
        self.addPrinter = function () {
            var newGuid = "NewPrinterGuid_" + (self.global_settings.settings.plugins.octolapse.printers().length + 1);

            self.global_settings.settings.plugins.octolapse.printers.push({
                name: ko.observable("New Printer " +
                    (self.global_settings.settings.plugins.octolapse.printers().length + 1)),
                guid: ko.observable(newGuid),
                retract_length: ko.observable(2),
                retract_speed: ko.observable(3600),
                movement_speed: ko.observable(7200),
                is_e_relative: ko.observable(true),
                z_hop: ko.observable(0.5),
                z_min: ko.observable(0.2),
                snapshot_command: ko.observable('snap')
            });
            self.settings.current_printer_guid(newGuid);
        };

        self.removePrinter = function (definition) {
            self.global_settings.settings.plugins.octolapse.printers.remove(definition);
        };
        /*
        self.current_printer_guid.subscribe(function (newValue) {
            self.global_settings.settings.plugins.octolapse.current_printer_guid(newValue);
            console.log("Change current printer guid!");
        }, self);*/
    };

    // This is how our plugin registers itself with the application, by adding some configuration
    // information to the global variable OCTOPRINT_VIEWMODELS
    OCTOPRINT_VIEWMODELS.push([
        // This is the constructor to call for instantiating the plugin
        OctolapseSettingsViewModel,

        // This is a list of dependencies to inject into the plugin, the order which you request
        // here is the order in which the dependencies will be injected into your view model upon
        // instantiation via the parameters argument
        ["settingsViewModel"],

        // Finally, this is the list of selectors for all elements we want this view model to be bound to.
        ["#octolapse_settings"]
    ]);
});


$(document).ready(function () {
    console.log("Octolapse Ready!");
});




