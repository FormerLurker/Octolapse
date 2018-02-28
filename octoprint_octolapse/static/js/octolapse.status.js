/*
    This file is subject to the terms and conditions defined in
    a file called 'LICENSE', which is part of this source code package.
*/
$(function () {


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
        self.waiting_to_render = ko.observable();

        self.PositionState = new Octolapse.positionStateViewModel();
        self.Position = new Octolapse.positionViewModel();
        self.ExtruderState = new Octolapse.extruderStateViewModel();
        self.TriggerState = new Octolapse.triggersStateViewModel();

        self.IsTabShowing = false;
        self.IsLatestSnapshotDialogShowing = false;

        self.showLatestSnapshotDialog = function () {

            self.IsLatestSnapshotDialogShowing = true;
            self.erasePreviousSnapshotImages('octolapse_snapshot_image_container');
            self.$SnapshotDialog.modal();

        };
        // cancel button click handler
        self.cancelLatestSnapshotDialog = function () {
            self.IsLatestSnapshotDialogShowing = false;
            self.$SnapshotDialog.modal("hide");
        };

        self.onAfterBinding = function () {
            self.$SnapshotDialog = $("#octolapse_latest_snapshot_dialog");
            // configure the modal hidden event.  Isn't it funny that bootstrap's own shortenting of their name is BS?
            self.$SnapshotDialog.on("hidden.bs.modal", function () {
                //console.log("Snapshot dialog hidden.");
                self.IsLatestSnapshotDialogShowing = false;
            });
            // configure the dialog shown event

            self.$SnapshotDialog.on("shown.bs.modal", function () {
                //console.log("Snapshot dialog shown.");
                self.IsLatestSnapshotDialogShowing = true;
                self.updateLatestSnapshotImage(force = true);
            });

            // configure the dialog show event
            self.$SnapshotDialog.on("show.bs.modal", function () {
                //console.log("Snapshot dialog showing.");
                self.IsLatestSnapshotDialogShowing = true;
            });


        }

        self.onTabChange = function (current, previous) {
            if (current != null && current == "#tab_plugin_octolapse") {
                //console.log("Octolapse Tab is showing");
                self.IsTabShowing = true;
                self.updateLatestSnapshotThumbnail(true);

            }
            else if (previous != null && previous == "#tab_plugin_octolapse") {
                //console.log("Octolapse Tab is not showing");
                self.IsTabShowing = false;
            }
        }
        /*
            Snapshot client animation preview functions
        */
        self.refreshLatestImage = function (targetId, isThumbnail = false) {
            //console.log("Refreshing Snapshot Thumbnail");
            var $target = $('#' + targetId + ' .snapshot_refresh_container a.refresh');

            
            if (isThumbnail)
                self.updateLatestSnapshotThumbnail(force = true);
            else
                self.updateLatestSnapshotImage(force = true);
        }
        self.startSnapshotAnimation = function (targetId, fadeButton = false) {

            //console.log("Refreshing Snapshot Thumbnail");
            // Hide and show the play/refresh button
            if (fadeButton && Octolapse.Globals.auto_reload_latest_snapshot()) {
                var $target = $('#' + targetId + ' .snapshot_refresh_container a.start-animation');
            }


            //console.log("Starting animation on " + targetId);
            // Get the images
            var $images = $('#' + targetId + ' .snapshot_container .previous-snapshots img');
            // Remove any existing visible class
            $images.each(function (index, element) {
                $(element).removeClass('visible');
            });
            // Set a delay to unblock
            setTimeout(function () {
                // Remove any hidden class and add visible to trigger the animation.
                $images.each(function (index, element) {
                    $(element).removeClass('hidden');
                    $(element).addClass('visible');
                });
            }, 1)

        }

        self.updateLatestSnapshotThumbnail = function (force = false) {
            //console.log("Trying to update the latest snapshot thumbnail.");
            if (!force) {
                if (!self.IsTabShowing) {
                    //console.log("The tab is not showing, not updating the thumbnail.  Clearing the image history.");
                    return
                }
                else if (!Octolapse.Globals.auto_reload_latest_snapshot()) {
                    //console.log("Not updating the thumbnail, auto-reload is disabled.");
                    return
                }
            }
            self.updateSnapshotAnimation('octolapse_snapshot_thumbnail_container', getLatestSnapshotThumbnailUrl() + "&time=" + new Date().getTime());

        }


        self.erasePreviousSnapshotImages = function (targetId, eraseCurrentImage = false) {
            if (eraseCurrentImage) {
                $('#' + targetId + ' .snapshot_container .latest-snapshot img').each(function (index, element) {
                    $(this).remove();
                });
            }
            $('#' + targetId + ' .snapshot_container .previous-snapshots img').each(function (index, element) {
                $(this).remove();
            });
        }
        // takes the list of images, update the frames in the target accordingly and starts any animations
        self.IsAnimating = false;
        self.updateSnapshotAnimation = function (targetId, newSnapshotAddress) {
            //console.log("Updating animation for target id: " + targetId);
            // Get the snapshot_container within the target
            var $target = $('#' + targetId + ' .snapshot_container');
            // Get the latest image
            var $latestSnapshotContainer = $target.find('.latest-snapshot');
            var $latestSnapshot = $latestSnapshotContainer.find('img');
            if (Octolapse.Globals.auto_reload_latest_snapshot()) {
                // Get the previous snapshot container
                var $previousSnapshotContainer = $target.find('.previous-snapshots');

                // Add the latest image to the previous snapshots list
                if ($latestSnapshot.length > 0) {
                    srcAttr = $latestSnapshot.attr('src')
                    // If the image has a src, and that src is not empty
                    if (typeof srcAttr !== typeof undefined && srcAttr !== false && srcAttr.length > 0) {
                        //console.log("Moving the latest image into the previous image container");
                        $latestSnapshot.appendTo($previousSnapshotContainer);
                    }
                    else {
                        $latestSnapshot.remove();
                    }
                }

                // Get all of the images within the $previousSnapshotContainer, included the latest image we copied in
                var $previousSnapshots = $previousSnapshotContainer.find("img");

                var numSnapshots = $previousSnapshots.length;

                while (numSnapshots > parseInt(Octolapse.Globals.auto_reload_frames())) {
                    //console.log("Removing overflow previous images according to Auto Reload Frames setting.");
                    $element = $previousSnapshots.first();
                    $element.remove();

                    numSnapshots--;
                }

                // Set the total animation duration based on the number of snapshots
                $previousSnapshotContainer.removeClass().addClass('previous-snapshots snapshot-animation-duration-' + numSnapshots)

                // TODO: Do we need to do this??  Find out
                $previousSnapshots = $previousSnapshotContainer.find("img");
                numPreviousSnapshots = $previousSnapshots.length
                var newestImageIndex = numPreviousSnapshots - 1
                //console.log("Updating classes for previous " + numPreviousSnapshots + " images.");
                for (var previousImageIndex = 0; previousImageIndex < numPreviousSnapshots; previousImageIndex++) {
                    $element = $($previousSnapshots.eq(previousImageIndex));
                    $element.removeClass()
                    if (previousImageIndex == newestImageIndex) {
                        //console.log("Updating classes for the newest image.");
                        $element.addClass("newest");
                    }
                    else {
                        $element.addClass("hidden");
                    }
                    previousImageDelayClass = "effect-delay-" + previousImageIndex;
                    //console.log("Updating classes for the previous image delay " + previousImageDelayClass+ ".");
                    $element.addClass(previousImageDelayClass);


                }

            }
            

            // create the newest image
            var $newSnapshot = $(document.createElement('img'));
            // append the image to the container

            //console.log("Adding the new snapshot image to the latest snapshot container.");
            // create on load event for the newest image
            if (Octolapse.Globals.auto_reload_latest_snapshot()) {
                // Add the new snapshot to the container
                $newSnapshot.appendTo($latestSnapshotContainer);
                $newSnapshot.one('load', function () {
                    self.IsAnimating = false;
                    self.startSnapshotAnimation(targetId);
                });
                // create an error handler for the newest image
                
            }
            else {
                
                $newSnapshot.one('load', function () {
                    // Hide the latest image
                    $latestSnapshot.fadeOut(250, function () {
                        // Remove the latest image
                        $latestSnapshot.remove();
                        // Set the new snapshot to hidden initially
                        $newSnapshot.css('display', 'none');
                        // Add the new snapshot to the container
                        $newSnapshot.appendTo($latestSnapshotContainer);
                        // fade it in.  Ahhh..
                        $newSnapshot.fadeIn(250);
                    });
                });
                

            }
            $newSnapshot.one('error', function () {
                //console.log("An error occurred loading the newest image, reverting to previous image.");
                // move the latest preview image back into the newest image section
                self.IsAnimating = false;
                $latestSnapshot.removeClass();
                $newSnapshot.addClass('latest')
                $latestSnapshot.appendTo($latestSnapshotContainer)

            });

            // set the class
            $newSnapshot.addClass('latest')
            // set the src and start to load
            $newSnapshot.attr('src', newSnapshotAddress)
        }


        self.updateLatestSnapshotImage = function (force = false) {
            //console.log("Trying to update the latest snapshot image.");
            if (!force) {
                if (!Octolapse.Globals.auto_reload_latest_snapshot()) {
                    //console.log("Auto-Update latest snapshot image is disabled.");
                    return
                }
                else if (!self.IsLatestSnapshotDialogShowing) {
                    //console.log("The full screen dialog is not showing, not updating the latest snapshot.");
                    return
                }
            }
            self.updateSnapshotAnimation('octolapse_snapshot_image_container', getLatestSnapshotUrl() + "&time=" + new Date().getTime());

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
        self.getStatusText = ko.pureComputed(function () {
            if (self.is_timelapse_active())
                return 'Octolapse - Running';
            if (self.is_rendering())
                return 'Octolapse - Rendering';
            if (self.waiting_to_render())
                return 'Octolapse - Waiting to Render';
            if (Octolapse.Globals.enabled())
                return 'Octolapse';
            return 'Octolapse - Disabled';
        }, self);


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
            self.is_timelapse_active(settings.is_timelapse_active);
            self.snapshot_count(settings.snapshot_count);
            self.is_taking_snapshot(settings.is_taking_snapshot);
            self.is_rendering(settings.is_rendering);
            self.seconds_added_by_octolapse(settings.seconds_added_by_octolapse);
            self.waiting_to_render(settings.waiting_to_render);
        };
        self.onTimelapseStart = function () {
            self.TriggerState.removeAll();
        }
        self.onTimelapseStop = function () {
            self.is_timelapse_active(false);
            self.is_taking_snapshot(false);
            self.waiting_to_render(true);
        }


        self.stopTimelapse = function () {
            if (Octolapse.Globals.is_admin()) {
                //console.log("octolapse.status.js - ButtonClick: StopTimelapse");
                if (confirm("Warning: You cannot restart octolapse once it is stopped until the next print.  Do you want to stop Octolapse?")) {
                    $.ajax({
                        url: "/plugin/octolapse/stopTimelapse",
                        type: "POST",
                        contentType: "application/json",
                        success: function (data) {
                            //console.log("octolapse.status.js - stopTimelapse - success" + data);
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

    /*
        Status Tab viewmodels
    */
    Octolapse.positionStateViewModel = function () {
        var self = this;
        self.GCode = ko.observable("");
        self.XHomed = ko.observable(false);
        self.YHomed = ko.observable(false);
        self.ZHomed = ko.observable(false);
        self.IsLayerChange = ko.observable(false);
        self.IsHeightChange = ko.observable(false);
        self.IsZHop = ko.observable(false);
        self.IsRelative = ko.observable(null);
        self.IsExtruderRelative = ko.observable(null);
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

        self.getCheckedIconClass = function (value) {
            return ko.computed({
                read: function () {
                    if (value == null)
                        return "fa-question";
                    else if (value)
                        return "fa-check";
                    else
                        return "fa-times-circle";
                }
            });
        };

        self.getPossitionErrorColor = ko.pureComputed(function () {
            if (this.HasPositionError())
                return "Red";
            else
                return "";
        }, self);

        self.getXHomedStateText = ko.pureComputed(function () {
            if (self.XHomed())
                return "Homed";
            else
                return "Not homed";
        }, self);
        self.getYHomedStateText = ko.pureComputed(function () {
            if (self.YHomed())
                return "Homed";
            else
                return "Not homed";
        }, self);
        self.getZHomedStateText = ko.pureComputed(function () {
            if (self.ZHomed())
                return "Homed";
            else
                return "Not homed";
        }, self);
        self.getIsZHopStateText = ko.pureComputed(function () {
            if (self.IsZHop())
                return "Zhop detected";
            else
                return "Not a zhop";
        }, self);
        self.getIsExtruderRelativeStateText = ko.pureComputed(function () {
            if (self.IsExtruderRelative() == null)
                return "Not Set";
            else if (self.IsExtruderRelative())
                return "Relative";
            else
                return "Absolute";
        }, self);

        self.getIsRelativeStateText = ko.pureComputed(function () {
            if (self.IsRelative() == null)
                return "Not Set";
            else if (self.IsRelative())
                return "Relative";
            else
                return "Absolute";
        }, self);

        self.getHasPositionErrorStateText = ko.pureComputed(function () {
            if (self.HasPositionError())
                return "A position error was detected";
            else
                return "No current position errors";
        }, self);
        self.getIsLayerChangeStateText = ko.pureComputed(function () {
            if (self.IsLayerChange())
                return "Layer change detected";
            else
                return "Not changing layers";
        }, self);
    };
    Octolapse.positionViewModel = function () {
        var self = this;
        self.F = ko.observable(0).extend({ numeric: 2 });
        self.X = ko.observable(0).extend({ numeric: 2 });
        self.XOffset = ko.observable(0).extend({ numeric: 2 });
        self.Y = ko.observable(0).extend({ numeric: 2 });
        self.YOffset = ko.observable(0).extend({ numeric: 2 });
        self.Z = ko.observable(0).extend({ numeric: 2 });
        self.ZOffset = ko.observable(0).extend({ numeric: 2 });
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
            //self.plotPosition(state.X, state.Y, state.Z);
        };
        /*
        self.plotPosition = function(x, y,z)
        {
            //console.log("Plotting Position")
            var canvas = document.getElementById("octolapse_position_canvas");
            canvas.width = 250;
            canvas.height = 200;
            var ctx = canvas.getContext("2d");
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillRect(x + 2, x - 2,4, 4);
            
        }*/
    };
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
        };

        self.getRetractionStateIconClass = ko.pureComputed(function () {
            if (self.IsRetracting()) {
                if (self.IsPartiallyRetracted() && !self.IsRetracted())
                    return "fa-angle-up";
                else if (self.IsRetracted() && !self.IsPartiallyRetracted())
                    return "fa-angle-double-up";
            }
            return "fa-times-circle";
        }, self);
        self.getRetractionStateText = ko.pureComputed(function () {

            if (self.IsRetracting()) {
                text = "";


                if (self.IsPartiallyRetracted() && !self.IsRetracted()) {
                    if (self.IsRetractingStart())
                        text += "Start: ";
                    text += self.RetractionLength() + "mm";
                    return text;
                }
                else if (self.IsRetracted() && !self.IsPartiallyRetracted()) {
                    if (self.IsRetractingStart())
                        return "Retracted Start: " + self.RetractionLength() + "mm";
                    else
                        return "Retracted: " + self.RetractionLength() + "mm";
                }
            }
            return "None";
        }, self);
        self.getDetractionIconClass = ko.pureComputed(function () {

            if (self.IsRetracting() && self.IsDetracting())
                return "fa-exclamation-circle";
            if (self.IsDetracting() && self.IsDetractingStart)
                return "fa-level-down";
            if (self.IsDetracting())
                return "fa-long-arrow-down";
            return "fa-times-circle";
        }, self);
        self.getDetractionStateText = ko.pureComputed(function () {

            var text = "";
            if (self.IsRetracting() && self.IsDetracting())
                text = "Error";
            else if (self.IsDetracted()) {
                text = "Detracted: " + self.DetractionLength() + "mm";
            }
            else if (self.IsDetracting()) {
                if (self.IsDetractingStart())
                    text += "Start: ";
                text += self.DetractionLength() + "mm";
            }
            else
                text = "None";
            return text;
        }, self);


        self.getExtrudingStateIconClass = ko.pureComputed(function () {

            if (self.IsExtrudingStart() && !self.IsExtruding())
                return "exclamation-circle";

            if (self.IsPrimed())
                return "fa-arrows-h";
            if (self.IsExtrudingStart())
                return "fa-play-circle-o";
            if (self.IsExtruding())
                return "fa-play";
            return "fa-times-circle";
        }, self);
        self.getExtrudingStateText = ko.pureComputed(function () {
            if (self.IsExtrudingStart() && !self.IsExtruding())
                return "Error";
            if (self.IsPrimed())
                return "Primed";
            if (self.IsExtrudingStart())
                return "Start: " + self.ExtrusionLength() + "mm";
            if (self.IsExtruding())
                return self.ExtrusionLength() + "mm";
            return "None";
        }, self);
    };
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
            for (var sI = 0; sI < triggers.length; sI++) {
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
        self.RequireZHop = ko.observable(state.RequireZHop);
        self.TriggeredCount = ko.observable(state.TriggeredCount).extend({ compactint: 1 });
        self.IsHomed = ko.observable(state.IsHomed);
        self.IsInPosition = ko.observable(state.IsInPosition);
        self.update = function (state) {
            self.Type(state.Type);
            self.Name(state.Name);
            self.IsTriggered(state.IsTriggered);
            self.IsWaiting(state.IsWaiting);
            self.IsWaitingOnZHop(state.IsWaitingOnZHop);
            self.IsWaitingOnExtruder(state.IsWaitingOnExtruder);
            self.RequireZHop(state.RequireZHop);
            self.TriggeredCount(state.TriggeredCount);
            self.IsHomed(state.IsHomed);
            self.IsInPosition(state.IsInPosition);
        }
        self.triggerBackgroundIconClass = ko.pureComputed(function () {
            if (!self.IsHomed())
                return "bg-not-homed";
            else if (!self.IsTriggered() && Octolapse.PrinterStatus.isPaused())
                return " bg-paused";
            else
                return "";
        }, self);
        /* style related computed functions */
        self.triggerStateText = ko.pureComputed(function () {
            if (!self.IsHomed())
                return "Idle until axis are homed"
            else if (self.IsTriggered())
                return "Triggering a snapshot";
            else if (Octolapse.PrinterStatus.isPaused())
                return "The trigger is paused";
            else if (self.IsWaiting()) {
                // Create a list of things we are waiting on
                waitText = "Waiting"
                waitList = [];
                if (self.IsWaitingOnZHop())
                    waitList.push("zhop");
                if (self.IsWaitingOnExtruder())
                    waitList.push("extruder");
                if (!self.IsInPosition())
                    waitList.push("position");
                if (waitList.length > 1) {
                    waitText += " for " + waitList.join(" and ");
                    waitText += " to trigger";
                }
                else if (waitList.length == 1)
                    waitText += " for " + waitList[0] + " to trigger";;
                return waitText;
            }

            else
                return "Waiting to trigger";


            return classes;
        }, self);
        self.triggerIconClass = ko.pureComputed(function () {
            if (!self.IsHomed())
                return "not-homed";
            if (self.IsTriggered())
                return "trigger";
            if (Octolapse.PrinterStatus.isPaused())
                return "paused";
            if (self.IsWaiting())
                return "wait";
            else
                return "fa-inverse";
        }, self);

        self.getInfoText = ko.pureComputed(function () {
            return "No info for this trigger";
        }, self);
        self.getInfoIconText = ko.pureComputed(function () {
            return "";
        }, self);
    }
    Octolapse.gcodeTriggerStateViewModel = function (state) {
        var self = this;
        self.Type = ko.observable(state.Type);
        self.Name = ko.observable(state.Name);
        self.IsTriggered = ko.observable(state.IsTriggered);
        self.IsWaiting = ko.observable(state.IsWaiting);
        self.IsWaitingOnZHop = ko.observable(state.IsWaitingOnZHop);
        self.IsWaitingOnExtruder = ko.observable(state.IsWaitingOnExtruder);
        self.SnapshotCommand = ko.observable(state.SnapshotCommand);
        self.RequireZHop = ko.observable(state.RequireZHop);
        self.TriggeredCount = ko.observable(state.TriggeredCount).extend({ compactint: 1 });
        self.IsHomed = ko.observable(state.IsHomed);
        self.IsInPosition = ko.observable(state.IsInPosition);
        self.update = function (state) {
            self.Type(state.Type);
            self.Name(state.Name);
            self.IsTriggered(state.IsTriggered);
            self.IsWaiting(state.IsWaiting);
            self.IsWaitingOnZHop(state.IsWaitingOnZHop);
            self.IsWaitingOnExtruder(state.IsWaitingOnExtruder);
            self.SnapshotCommand(state.SnapshotCommand);
            self.RequireZHop(state.RequireZHop);
            self.TriggeredCount(state.TriggeredCount);
            self.IsHomed(state.IsHomed);
            self.IsInPosition(state.IsInPosition);
        }

        self.triggerBackgroundIconClass = ko.pureComputed(function () {
            if (!self.IsHomed())
                return "bg-not-homed";
            else if (!self.IsTriggered() && Octolapse.PrinterStatus.isPaused())
                return " bg-paused";
            else
                return "";
        }, self);

        /* style related computed functions */
        self.triggerStateText = ko.pureComputed(function () {
            if (!self.IsHomed())
                return "Idle until axis are homed"
            else if (self.IsTriggered())
                return "Triggering a snapshot";
            else if (Octolapse.PrinterStatus.isPaused())
                return "Paused";
            else if (self.IsWaiting()) {
                // Create a list of things we are waiting on
                waitText = "Waiting"
                waitList = [];
                if (self.IsWaitingOnZHop())
                    waitList.push("zhop")
                if (self.IsWaitingOnExtruder())
                    waitList.push("extruder")
                if (!self.IsInPosition())
                    waitList.push("position");
                if (waitList.length > 1) {
                    waitText += " for " + waitList.join(" and ");
                    waitText += " to trigger";
                }
                else if (waitList.length == 1)
                    waitText += " for " + waitList[0] + " to trigger";
                return waitText;
            }

            else
                return "Looking for snapshot gcode";


            return classes;
        }, self);
        self.triggerIconClass = ko.pureComputed(function () {
            if (!self.IsHomed())
                return "not-homed";
            if (self.IsTriggered())
                return "trigger";
            if (Octolapse.PrinterStatus.isPaused())
                return "paused";
            if (self.IsWaiting())
                return "wait";
            else
                return "fa-inverse";
        }, self);

        self.getInfoText = ko.pureComputed(function () {
            return "Triggering on gcode command: " + self.SnapshotCommand();


        }, self);
        self.getInfoIconText = ko.pureComputed(function () {
            return self.SnapshotCommand()
        }, self);

    }
    Octolapse.layerTriggerStateViewModel = function (state) {
        var self = this;
        self.Type = ko.observable(state.Type);
        self.Name = ko.observable(state.Name);
        self.IsTriggered = ko.observable(state.IsTriggered);
        self.IsWaiting = ko.observable(state.IsWaiting);
        self.IsWaitingOnZHop = ko.observable(state.IsWaitingOnZHop);
        self.IsWaitingOnExtruder = ko.observable(state.IsWaitingOnExtruder);
        self.CurrentIncrement = ko.observable(state.CurrentIncrement);
        self.IsLayerChange = ko.observable(state.IsLayerChange);
        self.IsLayerChangeWait = ko.observable(state.IsLayerChangeWait);
        self.IsHeightChange = ko.observable(state.IsHeightChange);
        self.IsHeightChangeWait = ko.observable(state.IsHeightChangeWait);
        self.HeightIncrement = ko.observable(state.HeightIncrement).extend({ numeric: 2 });
        self.RequireZHop = ko.observable(state.RequireZHop);
        self.TriggeredCount = ko.observable(state.TriggeredCount).extend({ compactint: 1 });
        self.IsHomed = ko.observable(state.IsHomed);
        self.Layer = ko.observable(state.Layer);
        self.IsInPosition = ko.observable(state.IsInPosition);
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
            self.HeightIncrement(state.HeightIncrement)
            self.RequireZHop(state.RequireZHop)
            self.TriggeredCount(state.TriggeredCount);
            self.IsHomed(state.IsHomed);
            self.Layer(state.Layer);
            self.IsInPosition(state.IsInPosition);
        }
        self.triggerBackgroundIconClass = ko.pureComputed(function () {
            if (!self.IsHomed())
                return "bg-not-homed";
            else if (!self.IsTriggered() && Octolapse.PrinterStatus.isPaused())
                return " bg-paused";
        }, self);

        /* style related computed functions */
        self.triggerStateText = ko.pureComputed(function () {
            if (!self.IsHomed())
                return "Idle until axis are homed"
            else if (self.IsTriggered())
                return "Triggering a snapshot";
            else if (Octolapse.PrinterStatus.isPaused())
                return "The trigger is paused";
            else if (self.IsWaiting()) {
                // Create a list of things we are waiting on
                //console.log("Generating wait state text for LayerTrigger");
                waitText = "Waiting"
                waitList = [];
                if (self.IsWaitingOnZHop())
                    waitList.push("zhop")
                if (self.IsWaitingOnExtruder())
                    waitList.push("extruder")
                if (!self.IsInPosition()) {
                    waitList.push("position");
                    console.log("Waiting on position.");
                }
                if (waitList.length > 1) {
                    waitText += " for " + waitList.join(" and ");
                    waitText += " to trigger";
                }
                    
                else if (waitList.length == 1)
                    waitText += " for " + waitList[0] + " to trigger";
                return waitText;
            }
            else if (self.HeightIncrement() > 0) {
                heightToTrigger = self.HeightIncrement() * self.CurrentIncrement();
                return "Triggering when height reaches " + heightToTrigger.toFixed(1) + " mm";
            }
            else
                return "Triggering on next layer change";

        }, self);

        self.triggerIconClass = ko.pureComputed(function () {
            if (!self.IsHomed())
                return "not-homed";
            if (self.IsTriggered())
                return "trigger";
            if (Octolapse.PrinterStatus.isPaused())
                return "paused";
            if (self.IsWaiting())
                return " wait";
            else
                return " fa-inverse";
        }, self);

        self.getInfoText = ko.pureComputed(function () {
            var val = 0;
            if (self.HeightIncrement() > 0)

                val = self.HeightIncrement() + " mm";

            else
                val = "layer"
            return "Triggering every " + Octolapse.ToCompactInt(val);


        }, self);
        self.getInfoIconText = ko.pureComputed(function () {
            var val = 0;
            if (self.HeightIncrement() > 0)
                val = self.CurrentIncrement();
            else
                val = self.Layer();
            return Octolapse.ToCompactInt(val);
        }, self);

    }
    Octolapse.timerTriggerStateViewModel = function (state) {
        var self = this;
        self.Type = ko.observable(state.Type);
        self.Name = ko.observable(state.Name);
        self.IsTriggered = ko.observable(state.IsTriggered);
        self.IsWaiting = ko.observable(state.IsWaiting);
        self.IsWaitingOnZHop = ko.observable(state.IsWaitingOnZHop);
        self.IsWaitingOnExtruder = ko.observable(state.IsWaitingOnExtruder);
        self.SecondsToTrigger = ko.observable(state.SecondsToTrigger);
        self.IntervalSeconds = ko.observable(state.IntervalSeconds);
        self.TriggerStartTime = ko.observable(state.TriggerStartTime).extend({ time: null });
        self.PauseTime = ko.observable(state.PauseTime).extend({ time: null });
        self.RequireZHop = ko.observable(state.RequireZHop);
        self.TriggeredCount = ko.observable(state.TriggeredCount);
        self.IsHomed = ko.observable(state.IsHomed);
        self.IsInPosition = ko.observable(state.IsInPosition);
        self.update = function (state) {
            self.Type(state.Type);
            self.Name(state.Name);
            self.IsTriggered(state.IsTriggered);
            self.IsWaiting(state.IsWaiting);
            self.IsWaitingOnZHop(state.IsWaitingOnZHop);
            self.IsWaitingOnExtruder(state.IsWaitingOnExtruder);
            self.RequireZHop(state.RequireZHop);
            self.SecondsToTrigger(state.SecondsToTrigger);
            self.TriggerStartTime(state.TriggerStartTime);
            self.PauseTime(state.PauseTime);
            self.IntervalSeconds(state.IntervalSeconds);
            self.TriggeredCount(state.TriggeredCount);
            self.IsHomed(state.IsHomed);
            self.IsInPosition(state.IsInPosition);
        }


        /* style related computed functions */
        self.triggerStateText = ko.pureComputed(function () {
            if (!self.IsHomed())
                return "Idle until axis are homed"
            else if (self.IsTriggered())
                return "Triggering a snapshot";
            else if (Octolapse.PrinterStatus.isPaused())
                return "Paused"
            else if (self.IsWaiting()) {
                // Create a list of things we are waiting on
                waitText = "Waiting"
                waitList = [];
                if (self.IsWaitingOnZHop())
                    waitList.push("zhop")
                if (self.IsWaitingOnExtruder())
                    waitList.push("extruder")
                if (!self.IsInPosition())
                    waitList.push("position");
                if (waitList.length > 1) {
                    waitText += " for " + waitList.join(" and ");
                    waitText += " to trigger";
                }
                else if (waitList.length == 1)
                    waitText += " for " + waitList[0] + " to trigger";
                return waitText;
            }

            else
                return "Triggering in " + self.SecondsToTrigger() + " seconds";

            return classes;
        }, self);
        self.triggerBackgroundIconClass = ko.pureComputed(function () {
            if (!self.IsHomed())
                return "bg-not-homed";
            else if (!self.IsTriggered() && Octolapse.PrinterStatus.isPaused())
                return " bg-paused";
        }, self);
        self.triggerIconClass = ko.pureComputed(function () {
            if (!self.IsHomed())
                return "not-homed";
            if (self.IsTriggered())
                return "trigger";
            if (Octolapse.PrinterStatus.isPaused())
                return "paused";
            if (self.IsWaiting())
                return " wait";
            else
                return " fa-inverse";
        }, self);
        self.getInfoText = ko.pureComputed(function () {
            return "Triggering every " + Octolapse.ToTimer(self.IntervalSeconds());
        }, self);
        self.getInfoIconText = ko.pureComputed(function () {
            return "Triggering every " + Octolapse.ToTimer(self.IntervalSeconds());
        }, self);
    }

    // Bind the settings view model to the plugin settings element
    OCTOPRINT_VIEWMODELS.push([
        Octolapse.StatusViewModel
        , []
        , ["#octolapse_tab", "#octolapse_navbar"]
    ]);
});
