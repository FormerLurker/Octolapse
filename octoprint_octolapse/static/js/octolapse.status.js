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
        
        self.is_timelapse_active = ko.observable(false);
        self.is_taking_snapshot = ko.observable(false);
        self.is_rendering = ko.observable(false);
        self.seconds_added_by_octolapse = ko.observable(0);
        self.snapshot_count = ko.observable(0);        
        self.snapshot_error = ko.observable(false);
        self.snapshot_error_message = ko.observable("");

        self.ExtruderState = new Octolapse.extruderStateViewModel();
        self.PositionState = new Octolapse.positionStateViewModel();
        
        
        self.onAfterBinding = function () {
            self.loadStatus();
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
            Octolapse.Globals.update(settings);
            
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
        
        self.stopTimelapse = function () {
            if (Octolapse.Globals.is_admin()) {
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
        , []
        , ["#octolapse_tab","#octolapse_navbar"]
    ]);
});
