/// Create our printers view model
$(function () {
    
    Octolapse.StatusViewModel = function (parameters) {
        // Create a reference to this object
        var self = this

        // Add this object to our Octolapse namespace
        Octolapse.Status = this;
        // Assign the Octoprint settings to our namespace
        self.global_settings = parameters[0];
        self.is_timelapse_active = ko.observable();
        self.is_taking_snapshot = ko.observable();
        self.is_rendering = ko.observable();
        self.seconds_added_by_octolapse = ko.observable();
        self.snapshot_count = ko.observable();        
        self.snapshot_error = ko.observable(false);
        self.snapshot_error_message = ko.observable("");

        self.onBeforeBinding = function () {
            
            settings = ko.toJS(self.global_settings.settings.plugins.octolapse);
            self.is_timelapse_active(settings.is_timelapse_active);
            self.snapshot_count(settings.snapshot_count);
            self.is_taking_snapshot(settings.is_taking_snapshot);
            self.is_rendering(settings.is_rendering);
            self.seconds_added_by_octolapse(settings.seconds_added_by_octolapse);
                

        };
        // Receive messages from the server
        self.onDataUpdaterPluginMessage = function (plugin, data) {
            if (plugin != "octolapse") {
                return;
            }
            // Todo, handle this with
            switch (data.type) {
                case "timelapse-start":
                    console.log('Octolapse.state.js - timelapse-start');
                    self.is_timelapse_active(true);
                    self.is_taking_snapshot(false);
                    self.is_rendering(false);
                    self.snapshot_count(0);
                    self.seconds_added_by_octolapse(0)
                    self.snapshot_error(false);
                    self.snapshot_error_message("");
                    break;
                case "timelapse-complete":
                    console.log('Octolapse.state.js - timelapse-complete');
                    self.is_timelapse_active(false);
                    break;
                case "snapshot-start":
                    console.log('Octolapse.state.js - snapshot-start');
                    self.is_taking_snapshot(true);
                    self.snapshot_error(false);
                    self.snapshot_error_message("");
                    break;
                case "snapshot-complete":
                    console.log('Octolapse.state.js - snapshot-complete');
                    self.snapshot_count(data.snapshot_count)
                    self.seconds_added_by_octolapse(data.seconds_added_by_octolapse)
                    self.snapshot_error(!data.success);
                    self.snapshot_error_message(data.error);
                    self.is_taking_snapshot(false);
                    break;
                case "render-start":
                    console.log('Octolapse.state.js - render-start');
                    self.snapshot_count(data.snapshot_count)
                    self.seconds_added_by_octolapse(data.seconds_added_by_octolapse)
                    self.is_rendering(true);
                    break;
            
                case "render-complete":
                    console.log('Octolapse.state.js - render-complete');
                    break;
                case "render-end":
                    console.log('Octolapse.state.js - render-end');
                    self.is_rendering(false);
                    break;
                case "timelapse-stopping":
                    console.log('Octolapse.state.js - timelapse-stoping');
                    self.is_timelapse_active(false);
                    Octolapse.displayPopup(data.msg);
                    break;
                case "timelapse-stopped":
                    console.log('Octolapse.state.js - timelapse-stopped');
                    self.is_timelapse_active(false);
                    self.is_taking_snapshot(flase);
                    Octolapse.displayPopup(data.msg);
                    break;
                default:
                    console.log('Octolapse.state.js - passing on message from server.  DataType:' + data.type);
                    break;
            }
        };
        self.stopTimelapse = function () {
            console.log("tab - ButtonClick: StopTimelapse");
            if (confirm("Warning: You cannot restart octolapse once it is stopped until the next print.  Do you want to stop Octolapse?")) {
                $.ajax({
                    url: "/plugin/octolapse/stopTimelapse",
                    type: "POST",
                    contentType: "application/json",
                    success: function (data) {
                        console.log("tab - response: stopTimelapse, Data:" + data);
                    },
                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                        alert("Unable to stop octolapse!.  Status: " + textStatus + ".  Error: " + errorThrown);
                    }
                });
            }
        };

        self.snapshotTime = function () {
            var date = new Date(null);
            date.setSeconds(self.seconds_added_by_octolapse());
            var result = date.toISOString().substr(11, 8);
            return result;
        }
        self.navbarClicked = function () {
            $("#tab_plugin_octolapse_link a").click();
        }
        
    }
    // Bind the settings view model to the plugin settings element
    OCTOPRINT_VIEWMODELS.push([
        Octolapse.StatusViewModel
        , ["settingsViewModel"]
        , ["#octolapse_tab","#octolapse_navbar"]
    ]);
});
