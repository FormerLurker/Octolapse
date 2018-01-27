/// Create our printers view model
$(function () {
    
    Octolapse.StatusViewModel = function (parameters) {
        // Create a reference to this object
        var self = this

        // Add this object to our Octolapse namespace
        Octolapse.Status = this;
        // Assign the Octoprint settings to our namespace
        self.loginState = parameters[0];
        self.is_timelapse_active = ko.observable(false);
        self.is_taking_snapshot = ko.observable(false);
        self.is_rendering = ko.observable(false);
        self.seconds_added_by_octolapse = ko.observable(0);
        self.snapshot_count = ko.observable(0);        
        self.snapshot_error = ko.observable(false);
        self.snapshot_error_message = ko.observable("");
        Octolapse.is_admin = ko.observable(false)

        // Create observables for global UI binding, meaning we are accessing these
        // variables from different parts of the UI
        Octolapse.enabled = ko.observable();
        Octolapse.navbar_enabled = ko.observable();

        self.onBeforeBinding = function () {
            Octolapse.is_admin(self.loginState.isAdmin());
            
                
        };
        self.onAfterBinding = function () {
            self.loadStatus();
            
        }
        self.onUserLoggedIn = function (user) {
            console.log("octolapse.status.js - User Logged In.  User: " + user)
            Octolapse.is_admin(self.loginState.isAdmin());
        }
        self.onUserLoggedOut = function () {
            console.log("octolapse.status.js - User Logged Out")
            Octolapse.is_admin(false);
        }
        
        self.update = function (settings) {
            self.is_timelapse_active(settings.is_timelapse_active);
            self.snapshot_count(settings.snapshot_count);
            self.is_taking_snapshot(settings.is_taking_snapshot);
            self.is_rendering(settings.is_rendering);
            self.seconds_added_by_octolapse(settings.seconds_added_by_octolapse);
            // variables from different parts of the UI
            Octolapse.enabled(settings.is_octolapse_enabled);
            Octolapse.navbar_enabled(settings.show_navbar_icon);
        }
        self.loadStatus = function () {

            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array
            $.ajax({
                url: "/plugin/octolapse/loadStatus",
                type: "POST",
                contentType: "application/json",
                dataType: "json",
                success: function (newSettings) {
                    self.update(newSettings);
                    console.log("octolapse.status.js - Status have been loaded.");
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    alert("Octolapse - Unable to load the current status.  Status: " + textStatus + ".  Error: " + errorThrown);
                }
            });

        };
        // Receive messages from the server
        self.onDataUpdaterPluginMessage = function (plugin, data) {
            if (plugin != "octolapse") {
                return;
            }
            // Todo, handle this with
            switch (data.type) {
                case "settings-changed":
                    if (Octolapse.client_id != data.client_id) {
                        console.log('octolapse.status.js - settings-changed - loading status');
                        self.loadStatus();
                    }
                    break;
                case "status-changed":
                    console.log('octolapse.status.js - status-changed');
                    self.update(data);
                    break;
                case "popup":
                    console.log('octolapse.status.js - popup');
                    var options = {
                        title: 'Octolapse Notice',
                        text: data.msg,
                        type: 'notice',
                        hide: true,
                        desktop: {
                            desktop: true
                        }
                    };
                    Octolapse.displayPopup(options);
                    break;
                case "timelapse-start":
                    console.log('octolapse.status.js - timelapse-start');
                    self.is_timelapse_active(true);
                    self.is_taking_snapshot(false);
                    self.is_rendering(false);
                    self.snapshot_count(0);
                    self.seconds_added_by_octolapse(0)
                    self.snapshot_error(false);
                    self.snapshot_error_message("");
                    break;
                case "timelapse-complete":
                    console.log('octolapse.status.js - timelapse-complete');
                    self.is_timelapse_active(false);
                    self.is_taking_snapshot(false);
                    break;
                case "snapshot-start":
                    console.log('octolapse.status.js - snapshot-start');
                    self.is_taking_snapshot(true);
                    self.snapshot_error(false);
                    self.snapshot_error_message("");
                    break;
                case "snapshot-complete":
                    console.log('octolapse.status.js - snapshot-complete');
                    self.snapshot_count(data.snapshot_count)
                    self.seconds_added_by_octolapse(data.seconds_added_by_octolapse)
                    self.snapshot_error(!data.success);
                    self.snapshot_error_message(data.error);
                    self.is_taking_snapshot(false);
                    break;
                case "render-start":
                    console.log('octolapse.status.js - render-start');
                    self.snapshot_count(data.snapshot_count)
                    self.seconds_added_by_octolapse(data.seconds_added_by_octolapse)
                    self.is_rendering(true);
                    var options = {
                        title: 'Octolapse Rendering Started',
                        text: data.msg,
                        type: 'notice',
                        hide: true,
                        desktop: {
                            desktop: true
                        }
                    };
                    Octolapse.displayPopup(options);
                    break;
                case "render-failed":
                    console.log('octolapse.status.js - render-failed');
                    var options = {
                        title: 'Octolapse Rendering Failed',
                        text: data.msg,
                        type: 'error',
                        hide: false,
                        desktop: {
                            desktop: true
                        }
                    };
                    Octolapse.displayPopup(options);
                    break;
                case "render-complete":
                    console.log('octolapse.status.js - render-complete');
                    break;
                case "render-end":
                    console.log('octolapse.status.js - render-end');
                    self.is_rendering(false);
                    // Make sure we aren't synchronized, else there's no reason to display a popup
                    if (!data.is_synchronized && data.success) {
                        var options = {
                            title: 'Octolapse Rendering Complete',
                            text: data.msg,
                            type: 'success',
                            hide: false,
                            desktop: {
                                desktop: true
                            }
                        };
                        Octolapse.displayPopup(options);
                    }
                    break;
                case "synchronize-failed":
                    console.log('octolapse - synchronize-failed');
                    var options = {
                        title: 'Octolapse Synchronization Failed',
                        text: data.msg,
                        type: 'error',
                        hide: false,
                        desktop: {
                            desktop: true
                        }
                    };
                    Octolapse.displayPopup(options);
                    break;
                case "timelapse-stopping":
                    console.log('octolapse.status.js - timelapse-stoping');
                    self.is_timelapse_active(false);
                    var options = {
                        title: 'Octolapse Timelapse Stopping',
                        text: data.msg,
                        type: 'notice',
                        hide: true,
                        desktop: {
                            desktop: true
                        }
                    };
                    Octolapse.displayPopup(options);
                    break;
                case "timelapse-stopped":
                    console.log('octolapse.status.js - timelapse-stopped');
                    self.is_timelapse_active(false);
                    self.is_taking_snapshot(false);
                    var options = {
                        title: 'Octolapse Timelapse Stopped',
                        text: data.msg,
                        type: 'notice',
                        hide: true,
                        desktop: {
                            desktop: true
                        }
                    };
                    Octolapse.displayPopup(options);
                    break;
                default:
                    console.log('octolapse.status.js - passing on message from server.  DataType:' + data.type);
                    break;
            }
        };
        self.stopTimelapse = function () {
            if (Octolapse.is_admin()) {
                console.log("octolapse.status.js - ButtonClick: StopTimelapse");
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
        , ["loginStateViewModel"]
        , ["#octolapse_tab","#octolapse_navbar"]
    ]);
});
