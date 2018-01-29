/// Create our printers view model
$(function () {
    Octolapse.extruderStateViewModel = function () {
        self = this;
        // State variables
        self.ExtrusionLengthTotal = ko.observable(0).extend({ numeric: 2 });
        self.ExtrusionLength = ko.observable(0).extend({ numeric: 2 });
        self.RetractionLength = ko.observable(0).extend({ numeric: 2 });
        self.DetractionLength = ko.observable(0).extend({ numeric: 2 });
        self.IsExtrudingStart = ko.observable(false);
        self.IsExtruding = ko.observable(false);
        self.IsPrimed = ko.observable(false);
        self.IsRetractingStart = ko.observable(false);
        self.IsRetracting = ko.observable(false);
        self.IsRetracted = ko.observable(false);
        self.IsPartiallyRetracted = ko.observable(false);
        self.IsDetractingStart = ko.observable(false);
        self.IsDetracting = ko.observable(false);
        self.IsDetracted = ko.observable(false);
        self.HasChanged = ko.observable(false);

        self.update = function (state) {
            this.ExtrusionLengthTotal(state.ExtrusionLengthTotal);
            this.ExtrusionLength(state.ExtrusionLength);
            this.RetractionLength(state.RetractionLength);
            this.DetractionLength(state.DetractionLength);
            this.IsExtrudingStart(state.IsExtrudingStart);
            this.IsExtruding(state.IsExtruding);
            this.IsPrimed(state.IsPrimed);
            this.IsRetractingStart(state.IsRetractingStart);
            this.IsRetracting(state.IsRetracting);
            this.IsRetracted(state.IsRetracted);
            this.IsPartiallyRetracted(state.IsPartiallyRetracted);
            this.IsDetractingStart(state.IsDetractingStart);
            this.IsDetracting(state.IsDetracting);
            this.IsDetracted(state.IsDetracted);
            this.HasChanged(state.HasChanged);
        }
    }
    Octolapse.positionStateViewModel = function () {
        self = this;
        self.GCode = ko.observable("");
        self.F = ko.observable(0).extend({ numeric: 2 });
        self.X = ko.observable(0).extend({ numeric: 2 });
        self.XOffset = ko.observable(0).extend({ numeric: 2 });
        self.XHomed = ko.observable(false);
        self.Y = ko.observable(0).extend({ numeric: 2 });
        self.YOffset = ko.observable(0).extend({ numeric: 2 });
        self.YHomed = ko.observable(false);
        self.Z = ko.observable(0).extend({ numeric: 2 });
        self.ZOffset = ko.observable(0);
        self.ZHomed = ko.observable(false);
        self.E = ko.observable(0).extend({ numeric: 2 });
        self.EOffset = ko.observable(0).extend({ numeric: 2 });
        self.IsRelative = ko.observable(false);
        self.IsExtruderRelative = ko.observable(false);
        self.LastExtrusionHeight = ko.observable(0).extend({ numeric: 2 });
        self.IsLayerChange = ko.observable(false);
        self.IsZHop = ko.observable(false);
        self.HasPositionError = ko.observable(false);
        self.PositionError = ko.observable(false);
        self.HasPositionChanged = ko.observable(false);
        self.HasStateChanged = ko.observable(false);
        self.IsLayerChange = ko.observable(false);
        self.Layer = ko.observable(0).extend({ numeric: 2 });
        self.Height = ko.observable(0).extend({ numeric: 2 });

        self.update = function (state) {
            this.GCode(state.GCode);
            this.F(state.F);
            this.X(state.X);
            this.XOffset(state.XOffset);
            this.XHomed(state.XHomed);
            this.Y(state.Y);
            this.YOffset(state.YOffset);
            this.YHomed(state.YHomed);
            this.Z(state.Z);
            this.ZOffset(state.ZOffset);
            this.ZHomed(state.ZHomed);
            this.E(state.E);
            this.EOffset(state.EOffset);
            this.IsRelative(state.IsRelative);
            this.IsExtruderRelative(state.IsExtruderRelative);
            this.LastExtrusionHeight(state.LastExtrusionHeight);
            this.IsLayerChange(state.IsLayerChange);
            this.IsZHop(state.IsZHop);
            this.HasPositionError(state.HasPositionError);
            this.PositionError(state.PositionError);
            this.HasPositionChanged(state.HasPositionChanged);
            this.HasStateChanged(state.HasStateChanged);
            this.IsLayerChange(state.IsLayerChange);
            this.Layer(state.Layer);
            this.Height(state.Height);
        };
    }
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

        self.ExtruderState = new Octolapse.extruderStateViewModel();
        self.PositionState = new Octolapse.positionStateViewModel();
        

        

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
        self.updateExtruderState  = function (state) {
            // State variables
            self.ExtruderState.update(state)
        }
        self.updatePositionState = function (state) {
            // State variables
            self.PositionState.update(state)
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
            Octolapse.navbar_enabled(settings.show_navbar_icon);
            Octolapse.show_position_state_changes(settings.show_position_state_changes);
            Octolapse.show_extruder_state_changes(settings.show_extruder_state_changes);


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
                case "main-settings-changed":
                    if (Octolapse.client_id != data.client_id) {
                        console.log('octolapse.status.js - main-settings-changed');
                        // Bind the global values associated with these settings
                        Octolapse.enabled(data.is_octolapse_enabled)
                        Octolapse.navbar_enabled(data.show_navbar_icon);
                        Octolapse.show_position_state_changes(data.show_position_state_changes);
                        Octolapse.show_extruder_state_changes(data.show_extruder_state_changes);

                    }
                    break;
                case "settings-changed":
                    if (Octolapse.client_id != data.client_id) {
                        console.log('octolapse.status.js - settings-changed - loading status');
                        self.loadStatus();
                    }
                    break;
                case "state-changed":
                    console.log('octolapse.status.js - extruder-state-changed');
                    if(data.Position != null)
                        self.updatePositionState(data.Position);
                    if(data.Extruder != null)
                        self.updateExtruderState(data.Extruder);
                    break;
                case "state-changed":
                    console.log('octolapse.status.js - position-state-changed');
                    self.updatePositionState(data);
                    break;
                case "state-changed":
                    console.log('octolapse.status.js - state-changed');
                    self.UpdateStateDisplay(data)
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
