/// Create our printers view model
$(function () {

    Octolapse.MainSettingsViewModel = function (parameters) {
        // Create a reference to this object
        var self = this
        
        // Add this object to our Octolapse namespace
        Octolapse.SettingsMain = this;
        // Assign the Octoprint settings to our namespace
        self.global_settings = parameters[0];

        // Settings values
        self.is_octolapse_enabled = ko.observable();
        self.show_navbar_icon = ko.observable();

        // Informational Values
        self.platform = ko.observable();

        
        self.onBeforeBinding = function () {
            settings = self.global_settings.settings.plugins.octolapse;
            self.is_octolapse_enabled(settings.is_octolapse_enabled());
            self.show_navbar_icon(settings.show_navbar_icon())
            self.platform(settings.platform());

            // Bind the global values associated with these settings
            Octolapse.enabled(settings.is_octolapse_enabled())
            Octolapse.navbar_enabled(settings.show_navbar_icon());
        };
        // Get the dialog element
        self.onAfterBinding = function () {
            self.$addEditDialog = $("#octolapse_edit_settings_main_dialog");
        }
        /*
            Show and hide the settings tabs based on the enabled parameter
        */
        self.setSettingsVisibility = function (isVisible) {
            if (isVisible)
                console.log("Showing Settings")
            else {
                console.log("Hiding settings")
                $('#octolapse_settings div.tab-content .hide-disabled').each(function (index, element) {
                    // Clear any active tabs
                    $(element).removeClass('active');
                });
            }
            $('#octolapse_settings ul.nav .hide-disabled').each(function (index, element) {
                if (isVisible)
                    $(element).show();
                else
                    $(element).hide();
                $(element).removeClass('active');
            });
            
            

            // Set the main tab to the active tab
        };
        self.loadSettings = function () {
            
            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array
            $.ajax({
                url: "/plugin/octolapse/loadMainSettings",
                type: "POST",
                ccontentType: "application/json",
                dataType: "json",
                success: function (newSettings) {
                    self.update(newSettings);
                    console.log("Main Settings have been loaded.");
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    alert("Unable to load the main settings tab.  Status: " + textStatus + ".  Error: " + errorThrown);
                }
            });
        }
        self.update = function(settings) {
            self.is_octolapse_enabled(settings.is_octolapse_enabled);
            self.show_navbar_icon(settings.show_navbar_icon)
            // Set the tab-button/tab visibility
            self.setSettingsVisibility(settings.is_octolapse_enabled);
        }
        
        
        self.showEditMainSettingsPopup = function () {
            console.log("showing main settings")
            // Set the options to the current settings
            //self.is_octolapse_enabled(Octolapse.enabled())
            //self.show_navbar_icon(Octolapse.navbar_enabled())
            // Open the add/edit profile dialog
            self.$addEditDialog.modal();
        }
        // cancel button click handler
        self.cancelDialog = function () {
            // hide the modal
            self.$addEditDialog.modal("hide");
            
        }
        self.saveMainSettings = function () {
            var data = {
                "is_octolapse_enabled": self.is_octolapse_enabled()
                , "show_navbar_icon": self.show_navbar_icon()
                , "client_id" : Octolapse.client_id
            };
            console.log("Saving main settings.")
            $.ajax({
                url: "/plugin/octolapse/saveMainSettings",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (settings) {
                    self.update(settings);
                    self.$addEditDialog.modal("hide");
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    alert("Unable to save the main settings.  Status: " + textStatus + ".  Error: " + errorThrown);
                }
            });
        };
        self.resetMainSettings = function () {
            // Set the options to the current settings
            self.is_octolapse_enabled(true)
            self.show_navbar_icon(true)
        };
        
        
    }

    // Bind the settings view model to the plugin settings element
    OCTOPRINT_VIEWMODELS.push([
        Octolapse.MainSettingsViewModel
        , ["settingsViewModel"]
        , ["#octolapse_main_tab"]
    ]);
});

