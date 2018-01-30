/// Create our printers view model
$(function () {
    
    Octolapse.positionStateViewModel = function () {
        var self = this;
        self.GCode = ko.observable("");
        self.XHomed = ko.observable(false);
        self.YHomed = ko.observable(false);
        self.ZHomed = ko.observable(false);
        self.IsLayerChange = ko.observable(false);
        self.IsHeightChange = ko.observable(false);
        self.IsZHop = ko.observable(false);
        self.IsRelative = ko.observable(false);
        self.IsExtruderRelative = ko.observable(false);
        self.Layer = ko.observable(0);
        self.Height = ko.observable(0).extend({ numeric: 2 });
        self.LastExtrusionHeight = ko.observable(0).extend({ numeric: 2 });
        self.HasPositionError = ko.observable(false);
        self.PositionError = ko.observable(false);
        self.update = function (state) {
            this.GCode(state.GCode);
            this.XHomed(state.XHomed);
            this.YHomed(state.YHomed);
            this.ZHomed(state.ZHomed);
            this.IsLayerChange(state.IsLayerChange);
            this.IsHeightChange(state.IsHeightChange);
            this.IsZHop(state.IsZHop);
            this.IsRelative(state.IsRelative);
            this.IsExtruderRelative(state.IsExtruderRelative);
            this.Layer(state.Layer);
            this.Height(state.Height);
            this.LastExtrusionHeight(state.LastExtrusionHeight);
            this.HasPositionError(state.HasPositionError);
            this.PositionError(state.PositionError);
        };
    }
    Octolapse.positionViewModel = function () {
        var self = this;
        self.F = ko.observable(0).extend({ numeric: 2 });
        self.X = ko.observable(0).extend({ numeric: 2 });
        self.XOffset = ko.observable(0).extend({ numeric: 2 });
        self.Y = ko.observable(0).extend({ numeric: 2 });
        self.YOffset = ko.observable(0).extend({ numeric: 2 });
        self.Z = ko.observable(0).extend({ numeric: 2 });
        self.ZOffset = ko.observable(0);
        self.E = ko.observable(0).extend({ numeric: 2 });
        self.EOffset = ko.observable(0).extend({ numeric: 2 });
        self.update = function (state) {
            this.F(state.F);
            this.X(state.X);
            this.XOffset(state.XOffset);
            this.Y(state.Y);
            this.YOffset(state.YOffset);
            this.Z(state.Z);
            this.ZOffset(state.ZOffset);
            this.E(state.E);
            this.EOffset(state.EOffset);
        };
    }
    Octolapse.extruderStateViewModel = function () {
        var self = this;
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
    Octolapse.triggersStateViewModel = function () {
        var self = this;

        // State variables
        self.Name = ko.observable();
        self.Triggers = ko.observableArray();
        self.HasBeenCreated = false;
        self.create = function (trigger) {
            var newTrigger = null
            switch (state.Type) {
                case "gcode":
                    newTrigger = new Octolapse.gcodeTriggerStateViewModel(trigger);
                    break;
                case "layer":
                    newTrigger = new Octolapse.layerTriggerStateViewModel(trigger);
                    break;
                case "timer":
                    newTrigger = new Octolapse.timerTriggerStateViewModel(trigger);
                    break;
                default:
                    newTrigger = new Octolapse.genericTriggerStateViewModel(trigger);
                    break;
            };
            self.Triggers.push(newTrigger);
        };
        self.removeAll = function () {
            self.Triggers.removeAll();
        }
        self.update = function (states) {
            self.Name(states.Name)
            triggers = states.Triggers
            for (var sI = 0; sI < triggers.length; sI++)
            {
                state = triggers[sI];
                var foundState = false;
                for (var i = 0; i < self.Triggers().length; i++) {
                    currentTrigger = self.Triggers()[i];
                    if (state.Type == currentTrigger.Type()) {
                        currentTrigger.update(state);
                        foundState = true;
                        break;
                    }
                }
                if (!foundState) {
                    self.create(state);
                }
            }
        };
        
    }
    Octolapse.genericTriggerStateViewModel = function (state) {
        var self = this;
        self.Type = ko.observable(state.Type);
        self.Name = ko.observable(state.Name);
        self.IsTriggered = ko.observable(state.IsTriggered);
        self.IsWaiting = ko.observable(state.IsWaiting);
        self.IsWaitingOnZHop = ko.observable(state.IsWaitingOnZHop);
        self.IsWaitingOnExtruder = ko.observable(state.IsWaitingOnExtruder);
        self.update = function (state) {
            self.Type(state.Type);
            self.Name(state.Name);
            self.IsTriggered(state.IsTriggered);
            self.IsWaiting(state.IsWaiting);
            self.IsWaitingOnZHop(state.IsWaitingOnZHop);
            self.IsWaitingOnExtruder(state.IsWaitingOnExtruder);
        }
    }
    Octolapse.gcodeTriggerStateViewModel = function (state) {
        var self = this;
        self.Type = ko.observable(state.Type);
        self.Name = ko.observable(state.Name);
        self.IsTriggered = ko.observable(state.IsTriggered);
        self.IsWaiting = ko.observable(state.IsWaiting);
        self.IsWaitingOnZHop = ko.observable(state.IsWaitingOnZHop);
        self.IsWaitingOnExtruder = ko.observable(state.IsWaitingOnExtruder);
        self.update = function (state) {
            self.Type(state.Type);
            self.Name(state.Name);
            self.IsTriggered(state.IsTriggered);
            self.IsWaiting(state.IsWaiting);
            self.IsWaitingOnZHop(state.IsWaitingOnZHop);
            self.IsWaitingOnExtruder(state.IsWaitingOnExtruder);
        }
    }
    Octolapse.layerTriggerStateViewModel = function (state) {
        var self = this;
        self.Type = ko.observable(state.Type)
        self.Name = ko.observable(state.Name)
        self.IsTriggered = ko.observable(state.IsTriggered)
        self.IsWaiting = ko.observable(state.IsWaiting)
        self.IsWaitingOnZHop = ko.observable(state.IsWaitingOnZHop)
        self.IsWaitingOnExtruder = ko.observable(state.IsWaitingOnExtruder)

        self.CurrentIncrement = ko.observable(state.CurrentIncrement)
        self.IsLayerChange = ko.observable(state.IsLayerChange)
        self.IsLayerChangeWait = ko.observable(state.IsLayerChangeWait)
        self.IsHeightChange = ko.observable(state.IsHeightChange)
        self.IsHeightChangeWait = ko.observable(state.IsHeightChangeWait)

        self.update = function (state) {
            self.Type(state.Type);
            self.Name(state.Name);
            self.IsTriggered(state.IsTriggered);
            self.IsWaiting(state.IsWaiting);
            self.IsWaitingOnZHop(state.IsWaitingOnZHop);
            self.IsWaitingOnExtruder(state.IsWaitingOnExtruder);
            self.CurrentIncrement(state.CurrentIncrement);
            self.IsLayerChange(state.IsLayerChange);
            self.IsLayerChangeWait(state.IsLayerChangeWait);
            self.IsHeightChange(state.IsHeightChange);
            self.IsHeightChangeWait(state.IsHeightChangeWait);
        }
    }
    Octolapse.timerTriggerStateViewModel = function (state) {
        var self = this;
        self.Type = ko.observable(state.Type);
        self.Name = ko.observable(state.Name);
        self.IsTriggered = ko.observable(state.IsTriggered);
        self.IsWaiting = ko.observable(state.IsWaiting);
        self.IsWaitingOnZHop = ko.observable(state.IsWaitingOnZHop);
        self.IsWaitingOnExtruder = ko.observable(state.IsWaitingOnExtruder);
        self.SecondsToTrigger = ko.observable(state.SecondsToTrigger).extend({ numeric: 2 });
        self.IntervalSeconds = ko.observable(state.IntervalSeconds).extend({ numeric: 2 });
        self.TriggerStartTime = ko.observable(state.TriggerStartTime).extend({ time: null });
        self.PauseTime = ko.observable(state.PauseTime).extend({ time: null });
        self.update = function (state) {
            self.Type(state.Type);
            self.Name(state.Name);
            self.IsTriggered(state.IsTriggered);
            self.IsWaiting(state.IsWaiting);
            self.IsWaitingOnZHop(state.IsWaitingOnZHop);
            self.IsWaitingOnExtruder(state.IsWaitingOnExtruder);

            self.SecondsToTrigger(state.SecondsToTrigger);
            self.IntervalSeconds(state.IntervalSeconds);
            self.TriggerStartTime(state.TriggerStartTime);
            self.PauseTime(state.PauseTime);
        }
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

        self.PositionState = new Octolapse.positionStateViewModel();
        self.Position = new Octolapse.positionViewModel();
        self.ExtruderState = new Octolapse.extruderStateViewModel();
        self.TriggerState = new Octolapse.triggersStateViewModel();

        self.ClearAllStates = function () {
            self.TriggerState.removeAll()
        }
        self.GetTriggerStateTemplate = function (type) {
            switch (type) {
                case "gcode":
                    return "gcode-trigger-status-template";
                case "layer":
                    return "layer-trigger-status-template";
                case "timer":
                    return "timer-trigger-status-template"
                default:
                    return "trigger-status-template"
            }
        };
        
        
        self.updatePositionState = function (state) {
            // State variables
            self.PositionState.update(state);
        };
        self.updatePosition = function (state) {
            // State variables
            self.Position.update(state);
        };
        self.updateExtruderState = function (state) {
            // State variables
            self.ExtruderState.update(state);
        };
        
        self.updateTriggerStates = function (states) {
            self.TriggerState.update(states);
        };
        self.update = function (settings) {
            this.is_timelapse_active(settings.is_timelapse_active);
            this.snapshot_count(settings.snapshot_count);
            this.is_taking_snapshot(settings.is_taking_snapshot);
            this.is_rendering(settings.is_rendering);
            this.seconds_added_by_octolapse(settings.seconds_added_by_octolapse);

            
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
                            console.log("octolapse.status.js - stopTimelapse - success" + data);
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
            date.setSeconds(this.seconds_added_by_octolapse());
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
