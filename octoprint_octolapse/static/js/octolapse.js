/*$(function () {
    function OctolapseSettingsViewModel(parameters) {
        var self = this;
        self.global_settings = parameters[0];
        //self.settings = ko.observable()
       
        self.settings.is_octolapse_enabled = ko.observable(self.settings.is_octolapse_enabled);
        self.current_profile_name = ko.observable(self.current_profile_name );
        self.is_e_relative = ko.observable(self.is_e_relative)
        self.profiles = ko.observableArray(self.profiles);
        self.printer = ko.observable(self.printer);
    };
    self.onBeforeBinding = function () {
        self.settings = self.global_settings.settings.plugins.octolapse;
     }

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
*/
$(document).ready(function () {
    console.log("Octolapse Ready!");
});
