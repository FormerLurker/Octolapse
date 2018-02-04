/// Create our printers view model
$(function () {

    Octolapse.MainSettingsViewModel = function (parameters) {
        // Create a reference to this object
        var self = this;
        
        // Add this object to our Octolapse namespace
        Octolapse.SettingsMain = this;
        // Assign the Octoprint settings to our namespace
        self.global_settings = parameters[0];

        // Settings values
        self.is_octolapse_enabled = ko.observable();
        self.auto_reload_latest_snapshot = ko.observable();
        self.show_navbar_icon = ko.observable();
        self.show_position_state_changes = ko.observable();
        self.show_position_changes = ko.observable();
        self.show_extruder_state_changes = ko.observable();
        self.show_trigger_state_changes = ko.observable();
        

        // Informational Values
        self.platform = ko.observable();

        
        self.onBeforeBinding = function () {
            
        };
        // Get the dialog element
        self.onAfterBinding = function () {
            settings = self.global_settings.settings.plugins.octolapse;
            self.is_octolapse_enabled(settings.is_octolapse_enabled());
            self.auto_reload_latest_snapshot(settings.auto_reload_latest_snapshot());
            
            self.show_navbar_icon(settings.show_navbar_icon())
            self.show_position_state_changes(settings.show_position_state_changes())
            self.show_position_changes(settings.show_position_changes())
            self.show_extruder_state_changes(settings.show_extruder_state_changes())
            self.show_trigger_state_changes(settings.show_trigger_state_changes())
            self.platform(settings.platform());
            
            self.$addEditDialog = $("#octolapse_edit_settings_main_dialog");
        }
        /*
            Show and hide the settings tabs based on the enabled parameter
        */
        self.setSettingsVisibility = function (isVisible) {
            if (isVisible) {
                //console.log("Showing Settings")
            }
                
            else {
                //console.log("Hiding settings")
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

        };
        
        self.update = function(settings) {
            self.is_octolapse_enabled(settings.is_octolapse_enabled);
            self.auto_reload_latest_snapshot(settings.auto_reload_latest_snapshot);
            self.show_navbar_icon(settings.show_navbar_icon);
            self.show_position_state_changes(settings.show_position_state_changes);
            self.show_position_changes(settings.show_position_changes);
            self.show_extruder_state_changes(settings.show_extruder_state_changes);
            self.show_trigger_state_changes(settings.show_trigger_state_changes);
            
            // Set the tab-button/tab visibility
            self.setSettingsVisibility(settings.is_octolapse_enabled);
        }
        
        
        self.showEditMainSettingsPopup = function () {
            //console.log("showing main settings")
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
                ,"auto_reload_latest_snapshot": self.auto_reload_latest_snapshot()
                , "show_navbar_icon": self.show_navbar_icon()
                , "show_position_state_changes": self.show_position_state_changes()
                , "show_position_changes": self.show_position_changes()
                , "show_extruder_state_changes": self.show_extruder_state_changes()
                , "show_trigger_state_changes": self.show_trigger_state_changes()
                , "client_id" : Octolapse.Globals.client_id
            };
            //console.log("Saving main settings.")
            $.ajax({
                url: "/plugin/octolapse/saveMainSettings",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (settings) {
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
            self.auto_reload_latest_snapshot(true)
            self.show_navbar_icon(true)
            self.show_position_state_changes(false)
            self.show_position_changes(false)
            self.show_extruder_state_changes(false)
            self.show_trigger_state_changes(false)
        };
    }
    // Bind the settings view model to the plugin settings element
    OCTOPRINT_VIEWMODELS.push([
        Octolapse.MainSettingsViewModel
        , ["settingsViewModel"]
        , ["#octolapse_main_tab"]
    ]);
});

