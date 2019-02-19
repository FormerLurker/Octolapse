/*
##################################################################################
# Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
# Copyright (C) 2017  Brad Hochgesang
##################################################################################
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see the following:
# https://github.com/FormerLurker/Octolapse/blob/master/LICENSE
#
# You can contact the author either through the git-hub repository, or at the
# following email address: FormerLurker@pm.me
##################################################################################
*/
$(function () {
        Octolapse.StatusViewModel = function () {
            // Create a reference to this object
            var self = this;
            // Add this object to our Octolapse namespace
            Octolapse.Status = this;
            // Assign the Octoprint settings to our namespace

            self.is_timelapse_active = ko.observable(false);
            self.is_taking_snapshot = ko.observable(false);
            self.is_rendering = ko.observable(false);
            self.current_snapshot_time = ko.observable(0);
            self.total_snapshot_time = ko.observable(0);
            self.snapshot_count = ko.observable(0);
            self.snapshot_error = ko.observable(false);
            self.waiting_to_render = ko.observable();
            self.current_printer_profile_guid = ko.observable();
            self.current_stabilization_profile_guid = ko.observable();
            self.current_snapshot_profile_guid = ko.observable();
            self.current_rendering_profile_guid = ko.observable();
            self.current_debug_profile_guid = ko.observable();
            self.current_settings_showing = ko.observable(true);
            self.profiles = ko.observable({
                'printers': ko.observableArray([{name: "Unknown", guid: "", has_been_saved_by_user: false}]),
                'stabilizations': ko.observableArray([{name: "Unknown", guid: ""}]),
                'snapshots': ko.observableArray([{name: "Unknown", guid: ""}]),
                'renderings': ko.observableArray([{name: "Unknown", guid: ""}]),
                'cameras': ko.observableArray([{name: "Unknown", guid: "", enabled: false}]),
                'debug_profiles': ko.observableArray([{name: "Unknown", guid: ""}])
            });
            self.is_real_time = ko.observable(true);
            self.current_camera_guid = ko.observable();
            self.stabilization_requires_snapshot_profile = ko.observable();
            self.PositionState = new Octolapse.positionStateViewModel();
            self.Position = new Octolapse.positionViewModel();
            self.ExtruderState = new Octolapse.extruderStateViewModel();
            self.TriggerState = new Octolapse.triggersStateViewModel();
            self.SnapshotPlanState = new Octolapse.snapshotPlanStateViewModel();
            self.IsTabShowing = false;
            self.IsLatestSnapshotDialogShowing = false;
            self.current_print_volume = null;

            self.showLatestSnapshotDialog = function () {

                var $SnapshotDialog = $("#octolapse_latest_snapshot_dialog");
                // configure the modal hidden event.  Isn't it funny that bootstrap's own shortening of their name is BS?
                $SnapshotDialog.on("hidden.bs.modal", function () {
                    //console.log("Snapshot dialog hidden.");
                    self.IsLatestSnapshotDialogShowing = false;
                });
                // configure the dialog shown event

                $SnapshotDialog.on("shown.bs.modal", function () {
                    //console.log("Snapshot dialog shown.");
                    self.IsLatestSnapshotDialogShowing = true;
                    self.updateLatestSnapshotImage(true);
                });

                // configure the dialog show event
                $SnapshotDialog.on("show.bs.modal", function () {
                    //console.log("Snapshot dialog showing.");
                    self.IsLatestSnapshotDialogShowing = true;

                });

                // cancel button click handler
                $SnapshotDialog.find('.cancel').one('click', function () {
                    //console.log("Hiding snapshot dialog.");
                    self.IsLatestSnapshotDialogShowing = false;
                    $SnapshotDialog.modal("hide");
                });


                self.IsLatestSnapshotDialogShowing = true;
                self.erasePreviousSnapshotImages('octolapse_snapshot_image_container');
                $SnapshotDialog.modal();

            };

            self.SETTINGS_VISIBLE_KEY = "settings_visible";

            self.onBeforeBinding = function () {
                var settingsVisible = Octolapse.getLocalStorage(self.SETTINGS_VISIBLE_KEY);
                //console.log("Local Storage for " + self.SETTINGS_VISIBLE_KEY + ": " + settingsVisible);

                if(settingsVisible == null || settingsVisible.toLowerCase() === "true")
                {
                    self.current_settings_showing(true);
                }
                else
                {
                    self.current_settings_showing(false);
                }

            };

            self.onAfterBinding = function () {
                    self.current_settings_showing.subscribe(function (newData) {
                    //console.log("Setting local storage (" + self.SETTINGS_VISIBLE_KEY + ") to " + newData);
                    Octolapse.setLocalStorage(self.SETTINGS_VISIBLE_KEY,newData)
                });


            }

            self.hasOneCameraEnabled = ko.pureComputed(function(){
                var hasConfigIssue = true;
                for (var i = 0; i < self.profiles().cameras().length; i++)
                {
                    if(self.profiles().cameras()[i].enabled)
                    {
                        return true
                    }
                }
                return false;

            },this);

            self.hasPrinterSelected = ko.pureComputed(function(){
                return ! (Octolapse.Status.current_printer_profile_guid() == null || Octolapse.Status.current_printer_profile_guid()=="");
            },this);

            self.has_configured_printer_profile = ko.pureComputed(function(){
                //console.log("detecting configured printers.")
                var current_printer = self.getCurrentProfileByGuid(self.profiles().printers(),Octolapse.Status.current_printer_profile_guid());
                if (current_printer != null)
                    return current_printer.has_been_saved_by_user;
                return true;
            },this);

            self.current_stabilization_requires_snapshot_profile = function(){
                var current_stabilization = self.getCurrentProfileByGuid(self.profiles().stabilizations(),Octolapse.Status.current_stabilization_profile_guid());
                if (current_stabilization != null)
                    return current_stabilization.requires_snapshot_profile;
                return true;
            };

            self.is_current_stabilization_real_time = function(){
                var current_stabilization = self.getCurrentProfileByGuid(self.profiles().stabilizations(),Octolapse.Status.current_stabilization_profile_guid());
                if (current_stabilization  != null)
                    //console.log(current_stabilization.stabilization_type);
                    return current_stabilization.stabilization_type === "real-time";
                return true;
            };

            self.getCurrentProfileByGuid = function(profiles, guid){
                if (guid != null) {
                    for (var i = 0; i < profiles.length; i++) {
                        if (profiles[i].guid == guid) {
                            return profiles[i]
                        }
                    }
                }
                return null;
            };

            self.hasConfigIssues = ko.computed(function(){
                var hasConfigIssues = !self.hasOneCameraEnabled() || !self.hasPrinterSelected() || !self.has_configured_printer_profile();
                return hasConfigIssues;
            },this);

            self.onTabChange = function (current, previous) {
                if (current != null && current === "#tab_plugin_octolapse") {
                    //console.log("Octolapse Tab is showing");
                    self.IsTabShowing = true;
                    self.updateLatestSnapshotThumbnail(true);

                }
                else if (previous != null && previous === "#tab_plugin_octolapse") {
                    //console.log("Octolapse Tab is not showing");
                    self.IsTabShowing = false;
                }
            };
            /*
                Snapshot client animation preview functions
            */
            self.refreshLatestImage = function (targetId, isThumbnail) {
                isThumbnail = isThumbnail || false;
                //console.log("Refreshing Snapshot Thumbnail");
                if (isThumbnail)
                    self.updateLatestSnapshotThumbnail(true);
                else
                    self.updateLatestSnapshotImage(true);
            };

            self.startSnapshotAnimation = function (targetId) {
                //console.log("Refreshing Snapshot Thumbnail");
                // Hide and show the play/refresh button
                if (Octolapse.Globals.auto_reload_latest_snapshot()) {
                    $('#' + targetId + ' .snapshot_refresh_container a.start-animation').fadeOut();
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
                    if (Octolapse.Globals.auto_reload_latest_snapshot()) {
                        $('#' + targetId + ' .snapshot_refresh_container a.start-animation').fadeIn();
                    }
                }, 1)

            };

            self.updateLatestSnapshotThumbnail = function (force) {
                force = force || false;
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
                self.updateSnapshotAnimation('octolapse_snapshot_thumbnail_container', getLatestSnapshotThumbnailUrl(self.current_camera_guid())
                    + "&time=" + new Date().getTime());

            };

            self.erasePreviousSnapshotImages = function (targetId, eraseCurrentImage) {
                eraseCurrentImage = eraseCurrentImage || false;
                if (eraseCurrentImage) {
                    $('#' + targetId + ' .snapshot_container .latest-snapshot img').each(function () {
                        $(this).remove();
                    });
                }
                $('#' + targetId + ' .snapshot_container .previous-snapshots img').each(function () {
                    $(this).remove();
                });
            };

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
                        var srcAttr = $latestSnapshot.attr('src');
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
                        var $element = $previousSnapshots.first();
                        $element.remove();

                        numSnapshots--;
                    }

                    // Set the total animation duration based on the number of snapshots
                    $previousSnapshotContainer.removeClass().addClass('previous-snapshots snapshot-animation-duration-' + numSnapshots);

                    // TODO: Do we need to do this??  Find out
                    $previousSnapshots = $previousSnapshotContainer.find("img");
                    var numPreviousSnapshots = $previousSnapshots.length;
                    var newestImageIndex = numPreviousSnapshots - 1;
                    //console.log("Updating classes for previous " + numPreviousSnapshots + " images.");
                    for (var previousImageIndex = 0; previousImageIndex < numPreviousSnapshots; previousImageIndex++) {
                        $element = $($previousSnapshots.eq(previousImageIndex));
                        $element.removeClass();
                        if (previousImageIndex === newestImageIndex) {
                            //console.log("Updating classes for the newest image.");
                            $element.addClass("newest");
                        }
                        else {
                            $element.addClass("hidden");
                        }
                        var previousImageDelayClass = "effect-delay-" + previousImageIndex;
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
                    $newSnapshot.addClass('latest');
                    $latestSnapshot.appendTo($latestSnapshotContainer)

                });

                // set the class
                $newSnapshot.addClass('latest');
                // set the src and start to load
                $newSnapshot.attr('src', newSnapshotAddress)
            };

            self.updateLatestSnapshotImage = function (force) {
                force = force || false;
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
                //console.log("Requesting image for camera:" + Octolapse.Status.current_camera_guid())
                self.updateSnapshotAnimation('octolapse_snapshot_image_container', getLatestSnapshotUrl(Octolapse.Status.current_camera_guid()) + "&time=" + new Date().getTime());

            };

            self.toggleInfoPanel = function (panelType){
                $.ajax({
                    url: "./plugin/octolapse/toggleInfoPanel",
                    type: "POST",
                    data: JSON.stringify({panel_type: panelType}),
                    contentType: "application/json",
                    dataType: "json",
                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                        alert("Unable to toggle the panel.  Status: " + textStatus + ".  Error: " + errorThrown);
                    }
                });
            };

            /**
             * @return {string}
             */
            self.getTriggerStateTemplate = function (type) {
                switch (type) {
                    case "gcode":
                        return "gcode-trigger-status-template";
                    case "layer":
                        return "layer-trigger-status-template";
                    case "timer":
                        return "timer-trigger-status-template";
                    default:
                        return "trigger-status-template"
                }
            };

            self.getStateSummaryText = ko.pureComputed(function () {
                if(!self.is_timelapse_active()) {
                    if(self.waiting_to_render())
                        return "Octolapse is waiting for print to complete.";
                    if( self.is_rendering())
                        return "Octolapse is rendering a timelapse.";
                    if(!Octolapse.Globals.enabled())
                        return 'Octolapse is disabled.';
                    return 'Octolapse is enabled and idle.';
                }
                if(!Octolapse.Globals.enabled())
                    return 'Octolapse is disabled.';
                if(!self.PositionState.is_initialized())
                    return 'Octolapse is waiting for more information from the server.';
                if( self.PositionState.hasPositionStateErrors())
                    return 'Octolapse is waiting to initialize.';
                if( self.is_taking_snapshot())
                    return "Octolapse is taking a snapshot.";
                return "Octolapse is waiting to take snapshot.";

            }, self);

            self.getTimelapseStateText =  ko.pureComputed(function () {
                //console.log("GettingTimelapseStateText")
                if(!self.is_timelapse_active())
                    return 'Octolapse is not running';
                if(!self.PositionState.is_initialized())
                    return 'Waiting for update from server.  You may have to turn on the "Position State Info Panel" from the "Current Settings" below to receive an update.';
                if( self.PositionState.hasPositionStateErrors())
                    return 'Waiting to initialize';
                return 'Octolapse is initialized and running';
            }, self);

            self.getTimelapseStateColor =  ko.pureComputed(function () {
                if(!self.is_timelapse_active())
                    return '';
                if(!self.PositionState.is_initialized() || self.PositionState.hasPositionStateErrors())
                    return 'orange';
                return 'greenyellow';
            }, self);

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

            self.updateState = function(state)
            {

                //console.log("octolapse.status.js - Updating State")
                if (state.stabilization_type != null)
                    self.is_real_time(state.stabilization_type == "real-time");

                if (state.position != null) {
                    self.Position.update(state.position);
                }
                if (state.position_state != null) {
                    self.PositionState.update(state.position_state);
                }
                if (state.extruder != null) {
                    self.ExtruderState.update(state.extruder);
                }
                if (state.trigger_state != null) {
                    self.TriggerState.update(state.trigger_state);
                }
                if (state.snapshot_plan != null) {
                    self.SnapshotPlanState.update(state.snapshot_plan);
                }

            };

            self.update = function (settings) {
                self.is_timelapse_active(settings.is_timelapse_active);
                self.snapshot_count(settings.snapshot_count);
                self.is_taking_snapshot(settings.is_taking_snapshot);
                self.is_rendering(settings.is_rendering);
                self.total_snapshot_time(settings.total_snapshot_time);
                self.current_snapshot_time(settings.current_snapshot_time);
                self.waiting_to_render(settings.waiting_to_render);
                //console.log("Updating Profiles");
                self.profiles().printers(settings.profiles.printers);
                self.profiles().stabilizations(settings.profiles.stabilizations);
                self.profiles().snapshots(settings.profiles.snapshots);
                self.profiles().renderings(settings.profiles.renderings);
                self.profiles().cameras(settings.profiles.cameras);
                self.profiles().debug_profiles(settings.profiles.debug_profiles);
                self.current_printer_profile_guid(settings.profiles.current_printer_profile_guid);
                self.current_stabilization_profile_guid(settings.profiles.current_stabilization_profile_guid);
                self.current_snapshot_profile_guid(settings.profiles.current_snapshot_profile_guid);
                self.current_rendering_profile_guid(settings.profiles.current_rendering_profile_guid);
                self.current_debug_profile_guid(settings.profiles.current_debug_profile_guid);
                // Only update the current camera guid if there is no value
                if(self.current_camera_guid() == null)
                    self.current_camera_guid(settings.profiles.current_camera_profile_guid);

                self.is_real_time(self.is_current_stabilization_real_time());
                self.stabilization_requires_snapshot_profile(
                    self.current_stabilization_requires_snapshot_profile()
                );
            };

            self.onTimelapseStart = function () {
                self.TriggerState.removeAll();
                self.PositionState.is_initialized(false);
            };

            self.onTimelapseStop = function () {
                self.is_timelapse_active(false);
                self.is_taking_snapshot(false);
                self.waiting_to_render(true);
            };

            self.stopTimelapse = function () {
                if (Octolapse.Globals.is_admin()) {
                    //console.log("octolapse.status.js - ButtonClick: StopTimelapse");
                    if (confirm("Warning: You cannot restart octolapse once it is stopped until the next print.  Do you want to stop Octolapse?")) {
                        $.ajax({
                            url: "./plugin/octolapse/stopTimelapse",
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
                date.setSeconds(this.total_snapshot_time());
                return date.toISOString().substr(11, 8);
            };

            self.navbarClicked = function () {
                $("#tab_plugin_octolapse_link").find("a").click();
            };

            self.nameSort = function (observable) {
                //console.log("Sorting profiles on primary tab.")
                return observable().sort(
                    function (left, right) {
                        var leftName = left.name.toLowerCase();
                        var rightName = right.name.toLowerCase();
                        return leftName === rightName ? 0 : (leftName < rightName ? -1 : 1);
                    });
            };

            // Printer Profile Settings
            self.printers_sorted = ko.computed(function() { return self.nameSort(self.profiles().printers) });
            self.openCurrentPrinterProfile = function () {
                //console.log("Opening current printer profile from tab.")
                Octolapse.Printers.showAddEditDialog(self.current_printer_profile_guid(), false);
            };
            self.defaultPrinterChanged = function (obj, event) {
                if (Octolapse.Globals.is_admin()) {
                    if (event.originalEvent) {
                        // Get the current guid
                        var guid = $("#octolapse_tab_printer_profile").val();
                        //console.log("Default Printer is changing to " + guid);
                        Octolapse.Printers.setCurrentProfile(guid);
                        return true;
                    }
                }
            };

            // Stabilization Profile Settings
            self.stabilizations_sorted = ko.computed(function() { return self.nameSort(self.profiles().stabilizations) });
            self.openCurrentStabilizationProfile = function () {
                //console.log("Opening current stabilization profile from tab.")
                Octolapse.Stabilizations.showAddEditDialog(self.current_stabilization_profile_guid(), false);
            };
            self.defaultStabilizationChanged = function (obj, event) {
                if (Octolapse.Globals.is_admin()) {
                    if (event.originalEvent) {
                        // Get the current guid
                        var guid = $("#octolapse_tab_stabilization_profile").val();
                        //console.log("Default stabilization is changing to " + guid + " from " + self.current_stabilization_profile_guid());
                        Octolapse.Stabilizations.setCurrentProfile(guid);
                        return true;
                    }
                }
            };

            // Snapshot Profile Settings
            self.snapshots_sorted = ko.computed(function() { return self.nameSort(self.profiles().snapshots) });
            self.openCurrentSnapshotProfile = function () {
                //console.log("Opening current snapshot profile from tab.")
                Octolapse.Snapshots.showAddEditDialog(self.current_snapshot_profile_guid(), false);
            };
            self.defaultSnapshotChanged = function (obj, event) {
                if (Octolapse.Globals.is_admin()) {
                    if (event.originalEvent) {
                        // Get the current guid
                        var guid = $("#octolapse_tab_snapshot_profile").val();
                        //console.log("Default Snapshot is changing to " + guid);
                        Octolapse.Snapshots.setCurrentProfile(guid);
                        return true;
                    }
                }
            };

            // Rendering Profile Settings
            self.renderings_sorted = ko.computed(function() { return self.nameSort(self.profiles().renderings) });
            self.openCurrentRenderingProfile = function () {
                //console.log("Opening current rendering profile from tab.")
                Octolapse.Renderings.showAddEditDialog(self.current_rendering_profile_guid(), false);
            };
            self.defaultRenderingChanged = function (obj, event) {
                if (Octolapse.Globals.is_admin()) {
                    if (event.originalEvent) {
                        // Get the current guid
                        var guid = $("#octolapse_tab_rendering_profile").val();
                        //console.log("Default Rendering is changing to " + guid);
                        Octolapse.Renderings.setCurrentProfile(guid);
                        return true;
                    }
                }
            };

            // Camera Profile Settings
            self.cameras_sorted = ko.computed(function() { return self.nameSort(self.profiles().cameras) });

            self.openCameraProfile = function (guid) {
                //console.log("Opening current camera profile from tab.")
                Octolapse.Cameras.showAddEditDialog(guid, false);
            };

            self.addNewCameraProfile = function () {
                //console.log("Opening current camera profile from tab.")
                Octolapse.Cameras.showAddEditDialog(null, false);
            };

            self.toggleCamera = function (guid) {
                //console.log("Opening current camera profile from tab.")
                Octolapse.Cameras.getProfileByGuid(guid).toggleCamera();
            };
            self.snapshotCameraChanged = function(obj, event) {
                // Update the current camera profile
                var guid = $("#octolapse_current_snapshot_camera").val();
                //console.log("Updating current snapshot camera preview: " + guid)
                if(event.originalEvent) {
                    if (Octolapse.Globals.is_admin()) {
                        var data = {'guid': guid};
                        $.ajax({
                            url: "./plugin/octolapse/setCurrentCameraProfile",
                            type: "POST",
                            data: JSON.stringify(data),
                            contentType: "application/json",
                            dataType: "json",
                            success: function (result) {
                                // Set the current profile guid observable.  This will cause the UI to react to the change.
                                //console.log("current profile guid updated: " + result.guid)
                            },
                            error: function (XMLHttpRequest, textStatus, errorThrown) {
                                alert("Unable to set the current camera profile!.  Status: " + textStatus + ".  Error: " + errorThrown);
                            }
                        });
                    }
                }

                //console.log("Updating the latest snapshot from: " + Octolapse.Status.current_camera_guid() + " to " + guid);
                Octolapse.Status.current_camera_guid(guid);
                self.erasePreviousSnapshotImages('octolapse_snapshot_image_container',true);
                self.erasePreviousSnapshotImages('octolapse_snapshot_thumbnail_container',true);
                self.updateLatestSnapshotThumbnail(self.current_camera_guid());
                self.updateLatestSnapshotImage(self.current_camera_guid());
            };

            // Debug Profile Settings
            self.debug_sorted = ko.computed(function() { return self.nameSort(self.profiles().debug_profiles) });
            self.openCurrentDebugProfile = function () {
                //console.log("Opening current debug profile from tab.")
                Octolapse.DebugProfiles.showAddEditDialog(self.current_debug_profile_guid(), false);
            };
            self.defaultDebugProfileChanged = function (obj, event) {
                if (Octolapse.Globals.is_admin()) {
                    if (event.originalEvent) {
                        // Get the current guid
                        var guid = $("#octolapse_tab_debug_profile").val();
                        //console.log("Default Debug Profile is changing to " + guid);
                        Octolapse.DebugProfiles.setCurrentProfile(guid);
                        return true;
                    }
                }
            };

        };
        /*
            Status Tab viewmodels
        */
        Octolapse.positionStateViewModel = function () {
            var self = this;
            self.gcode = ko.observable("");
            self.x_homed = ko.observable(false);
            self.y_homed = ko.observable(false);
            self.z_homed = ko.observable(false);
            self.is_layer_change = ko.observable(false);
            self.is_height_change = ko.observable(false);
            self.is_in_position = ko.observable(false);
            self.in_path_position = ko.observable(false);
            self.is_zhop = ko.observable(false);
            self.is_relative = ko.observable(null);
            self.is_extruder_relative = ko.observable(null);
            self.layer = ko.observable(0);
            self.height = ko.observable(0).extend({numeric: 2});
            self.last_extruder_height = ko.observable(0).extend({numeric: 2});
            self.has_position_error = ko.observable(false);
            self.position_error = ko.observable(false);
            self.is_metric = ko.observable(null);
            self.is_initialized = ko.observable(false);

            self.update = function (state) {
                this.gcode(state.gcode);
                this.x_homed(state.x_homed);
                this.y_homed(state.y_homed);
                this.z_homed(state.z_homed);
                this.is_layer_change(state.is_layer_change);
                this.is_height_change(state.is_height_change);
                this.is_in_position(state.is_in_position);
                this.in_path_position(state.in_path_position);
                this.is_zhop(state.is_zhop);
                this.is_relative(state.is_relative);
                this.is_extruder_relative(state.is_extruder_relative);
                this.layer(state.layer);
                this.height(state.height);
                this.last_extruder_height(state.last_extruder_height);
                this.has_position_error(state.has_position_error);
                this.position_error(state.position_error);
                this.is_metric(state.is_metric);
                this.is_initialized(true);
            };

            self.getCheckedIconClass = function (value, trueClass, falseClass, nullClass) {
                return ko.computed({
                    read: function () {
                        if (value == null)
                            return nullClass;
                        else if (value)
                            return trueClass;
                        else
                            return falseClass;
                    }
                });
            };


            self.getColor = function (value, trueColor, falseColor, nullColor) {
                return ko.computed({
                    read: function () {
                        if (value == null)
                            return nullColor;
                        else if(!value)
                            return falseColor;
                        if (value)
                            return trueColor;
                    }
                });
            };

            self.hasPositionStateErrors = ko.pureComputed(function(){
                if (Octolapse.Status.is_timelapse_active() && self.is_initialized())

                    if (!(self.x_homed() && self.y_homed() && self.z_homed())
                        || self.is_relative() == null
                        || self.is_extruder_relative() == null
                        || !self.is_metric()
                        || self.has_position_error())
                        return true;
                return false;
            },self);

            self.getYHomedStateText = ko.pureComputed(function () {
                if (self.y_homed())
                    return "Homed";
                else
                    return "Not homed";
            }, self);
            self.getZHomedStateText = ko.pureComputed(function () {
                if (self.z_homed())
                    return "Homed";
                else
                    return "Not homed";
            }, self);
            self.getIsZHopStateText = ko.pureComputed(function () {
                if (self.is_zhop())
                    return "Zhop detected";
                else
                    return "Not a zhop";
            }, self);

            self.getis_in_positionStateText = ko.pureComputed(function () {
                if (self.is_in_position())
                    return "In position";
                else if (self.in_path_position())
                    return "In path position";
                else
                    return "Not in position";
            }, self);

            self.getis_metricStateText = ko.pureComputed(function () {
                if (self.is_metric())
                    return "Metric";
                else if (self.is_metric() === null)
                    return "Unknown";
                else
                    return "Not Metric";
            }, self);
            self.getIsExtruderRelativeStateText = ko.pureComputed(function () {
                if (self.is_extruder_relative() == null)
                    return "Not Set";
                else if (self.is_extruder_relative())
                    return "Relative";
                else
                    return "Absolute";
            }, self);

            self.getExtruderModeText = ko.pureComputed(function () {
                if (self.is_extruder_relative() == null)
                    return "Mode";
                else if (self.is_extruder_relative())
                    return "Relative";
                else
                    return "Absolute";
            }, self);
            self.getXYZModeText = ko.pureComputed(function () {
                if (self.is_relative() == null)
                    return "Mode";
                else if (self.is_relative())
                    return "Relative";
                else
                    return "Absolute";
            }, self);
            self.getIsRelativeStateText = ko.pureComputed(function () {
                if (self.is_relative() == null)
                    return "Not Set";
                else if (self.is_relative())
                    return "Relative";
                else
                    return "Absolute";
            }, self);

            self.getHasPositionErrorStateText = ko.pureComputed(function () {
                if (self.has_position_error())
                    return "A position error was detected";
                else
                    return "No current position errors";
            }, self);
            self.getis_layer_changeStateText = ko.pureComputed(function () {
                if (self.is_layer_change())
                    return "Layer change detected";
                else
                    return "Not changing layers";
            }, self);
        };
        Octolapse.positionViewModel = function () {
            var self = this;
            self.f = ko.observable(0).extend({numeric: 2});
            self.x = ko.observable(0).extend({numeric: 2});
            self.x_offset = ko.observable(0).extend({numeric: 2});
            self.y = ko.observable(0).extend({numeric: 2});
            self.y_offset = ko.observable(0).extend({numeric: 2});
            self.z = ko.observable(0).extend({numeric: 2});
            self.z_offset = ko.observable(0).extend({numeric: 2});
            self.e = ko.observable(0).extend({numeric: 2});
            self.e_offset = ko.observable(0).extend({numeric: 2});
            self.features = ko.observableArray([]);
            self.update = function (state) {
                this.f(state.f);
                this.x(state.x);
                this.x_offset(state.x_offset);
                this.y(state.y);
                this.y_offset(state.y_offset);
                this.z(state.z);
                this.z_offset(state.z_offset);
                this.e(state.e);
                this.e_offset(state.e_offset);
                this.features(state.features);
                //console.log(this.Features());
                //self.plotPosition(state.x, state.y, state.z);
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
            self.extrusion_length_total = ko.observable(0).extend({numeric: 2});
            self.extrusion_length = ko.observable(0).extend({numeric: 2});
            self.retraction_length = ko.observable(0).extend({numeric: 2});
            self.deretraction_length = ko.observable(0).extend({numeric: 2});
            self.is_extruding_start = ko.observable(false);
            self.is_extruding = ko.observable(false);
            self.is_primed = ko.observable(false);
            self.is_retracting_start = ko.observable(false);
            self.is_retracting = ko.observable(false);
            self.is_retracted = ko.observable(false);
            self.is_partially_retracted = ko.observable(false);
            self.is_deretracting_start = ko.observable(false);
            self.is_deretracting = ko.observable(false);
            self.is_deretracted = ko.observable(false);
            self.has_changed = ko.observable(false);

            self.update = function (state) {
                this.extrusion_length_total(state.extrusion_length_total);
                this.extrusion_length(state.extrusion_length);
                this.retraction_length(state.retraction_length);
                this.deretraction_length(state.deretraction_length);
                this.is_extruding_start(state.is_extruding_start);
                this.is_extruding(state.is_extruding);
                this.is_primed(state.is_primed);
                this.is_retracting_start(state.is_retracting_start);
                this.is_retracting(state.is_retracting);
                this.is_retracted(state.is_retracted);
                this.is_partially_retracted(state.is_partially_retracted);
                this.is_deretracting_start(state.is_deretracting_start);
                this.is_deretracting(state.is_deretracting);
                this.is_deretracted(state.is_deretracted);
                this.has_changed(state.has_changed);
            };

            self.getRetractionStateIconClass = ko.pureComputed(function () {
                if (self.is_retracting()) {
                    if (self.is_partially_retracted() && !self.is_retracted())
                        return "fa-angle-up";
                    else if (self.is_retracted() && !self.is_partially_retracted())
                        return "fa-angle-double-up";
                }
                return "fa-times-circle";
            }, self);
            self.getRetractionStateText = ko.pureComputed(function () {

                if (self.is_retracting()) {
                    var text = "";


                    if (self.is_partially_retracted() && !self.is_retracted()) {
                        if (self.is_retracting_start())
                            text += "Start: ";
                        text += self.retraction_length() + "mm";
                        return text;
                    }
                    else if (self.is_retracted() && !self.is_partially_retracted()) {
                        if (self.is_retracting_start())
                            return "Retracted Start: " + self.retraction_length() + "mm";
                        else
                            return "Retracted: " + self.retraction_length() + "mm";
                    }
                }
                return "None";
            }, self);
            self.getDeretractionIconClass = ko.pureComputed(function () {

                if (self.is_retracting() && self.is_deretracting())
                    return "fa-exclamation-circle";
                if (self.is_deretracting() && self.is_deretracting_start)
                    return "fa-level-down";
                if (self.is_deretracting())
                    return "fa-long-arrow-down";
                return "fa-times-circle";
            }, self);
            self.getDeretractionStateText = ko.pureComputed(function () {

                var text = "";
                if (self.is_retracting() && self.is_deretracting())
                    text = "Error";
                else if (self.is_deretracted()) {
                    text = "Deretracted: " + self.deretraction_length() + "mm";
                }
                else if (self.is_deretracting()) {
                    if (self.is_deretracting_start())
                        text += "Start: ";
                    text += self.deretraction_length() + "mm";
                }
                else
                    text = "None";
                return text;
            }, self);


            self.getExtrudingStateIconClass = ko.pureComputed(function () {

                if (self.is_extruding_start() && !self.is_extruding())
                    return "exclamation-circle";

                if (self.is_primed())
                    return "fa-arrows-h";
                if (self.is_extruding_start())
                    return "fa-play-circle-o";
                if (self.is_extruding())
                    return "fa-play";
                return "fa-times-circle";
            }, self);
            self.getExtrudingStateText = ko.pureComputed(function () {
                if (self.is_extruding_start() && !self.is_extruding())
                    return "Error";
                if (self.is_primed())
                    return "Primed";
                if (self.is_extruding_start())
                    return "Start: " + self.extrusion_length() + "mm";
                if (self.is_extruding())
                    return self.extrusion_length() + "mm";
                return "None";
            }, self);
        };
        Octolapse.triggersStateViewModel = function () {
            var self = this;

            // State variables
            self.name = ko.observable();
            self.triggers = ko.observableArray();
            self.HasBeenCreated = false;
            self.create = function (trigger) {
                var newTrigger = null;
                switch (trigger.type) {
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
                }
                self.triggers.push(newTrigger);
            };

            self.removeAll = function () {
                self.triggers.removeAll();
            };

            self.update = function (states) {
                //console.log("Updating trigger states")
                self.name(states.name);
                var triggers = states.triggers;
                for (var sI = 0; sI < triggers.length; sI++) {
                    var state = triggers[sI];
                    var foundState = false;
                    for (var i = 0; i < self.triggers().length; i++) {
                        var currentTrigger = self.triggers()[i];
                        if (state.type === currentTrigger.type()) {
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

        };
        Octolapse.genericTriggerStateViewModel = function (state) {
            //console.log("creating generic trigger state view model");
            var self = this;
            self.type = ko.observable(state.type);
            self.name = ko.observable(state.name);
            self.is_triggered = ko.observable(state.is_triggered);
            self.is_waiting = ko.observable(state.is_waiting);
            self.is_waiting_on_zhop = ko.observable(state.is_waiting_on_zhop);
            self.is_waiting_on_extruder = ko.observable(state.is_waiting_on_extruder);
            self.require_zhop = ko.observable(state.require_zhop);
            self.trigger_count = ko.observable(state.trigger_count).extend({compactint: 1});
            self.is_homed = ko.observable(state.is_homed);
            self.is_in_position = ko.observable(state.is_in_position);
            self.in_path_position = ko.observable(state.Isin_path_position);
            self.is_feature_allowed = ko.observable(state.is_feature_allowed);
            self.is_waiting_on_feature = ko.observable(state.is_waiting_on_feature);
            self.update = function (state) {
                self.type(state.type);
                self.name(state.name);
                self.is_triggered(state.is_triggered);
                self.is_waiting(state.is_waiting);
                self.is_waiting_on_zhop(state.is_waiting_on_zhop);
                self.is_waiting_on_extruder(state.is_waiting_on_extruder);
                self.require_zhop(state.require_zhop);
                self.trigger_count(state.trigger_count);
                self.is_homed(state.is_homed);
                self.is_in_position(state.is_in_position);
                self.in_path_position(state.in_path_position);
                self.is_feature_allowed(state.is_feature_allowed);
                self.is_waiting_on_feature(state.is_waiting_on_feature);
            };
            self.triggerBackgroundIconClass = ko.pureComputed(function () {
                if (!self.is_homed())
                    return "bg-not-homed";
                else if (!self.is_triggered() && Octolapse.PrinterStatus.isPaused())
                    return " bg-paused";
                else
                    return "";
            }, self);
            /* style related computed functions */
            self.triggerStateText = ko.pureComputed(function () {
                //console.log("Calculating trigger state text.");
                if (!self.is_homed())
                    return "Idle until all axes are homed";
                else if (self.is_triggered())
                    return "Triggering a snapshot";
                else if (Octolapse.PrinterStatus.isPaused())
                    return "The trigger is paused";
                else if (self.is_waiting()) {
                    // Create a list of things we are waiting on
                    var waitText = "Waiting";
                    var waitList = [];
                    if (self.is_waiting_on_zhop())
                        waitList.push("zhop");
                    if (self.is_waiting_on_extruder())
                        waitList.push("extruder");
                    if (!self.is_in_position() && !self.in_path_position())
                        waitList.push("position");
                    if (self.is_waiting_on_feature())
                        waitList.push("feature");
                    if (waitList.length > 1) {
                        waitText += " for " + waitList.join(" and ");
                        waitText += " to trigger";
                    }
                    else if (waitList.length === 1)
                        waitText += " for " + waitList[0] + " to trigger";
                    return waitText;
                }

                else
                    return "Waiting to trigger";

            }, self);
            self.triggerIconClass = ko.pureComputed(function () {
                if (!self.is_homed())
                    return "not-homed";
                if (self.is_triggered())
                    return "trigger";
                if (Octolapse.PrinterStatus.isPaused())
                    return "paused";
                if (self.is_waiting())
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
        };
        Octolapse.gcodeTriggerStateViewModel = function (state) {
            //console.log("creating gcode trigger state view model");
            var self = this;
            self.type = ko.observable(state.type);
            self.name = ko.observable(state.name);
            self.is_triggered = ko.observable(state.is_triggered);
            self.is_waiting = ko.observable(state.is_waiting);
            self.is_waiting_on_zhop = ko.observable(state.is_waiting_on_zhop);
            self.is_waiting_on_extruder = ko.observable(state.is_waiting_on_extruder);
            self.snapshot_command = ko.observable(state.snapshot_command);
            self.require_zhop = ko.observable(state.require_zhop);
            self.trigger_count = ko.observable(state.trigger_count).extend({compactint: 1});
            self.is_homed = ko.observable(state.is_homed);
            self.is_in_position = ko.observable(state.is_in_position);
            self.in_path_position = ko.observable(state.Isin_path_position);
            self.is_waiting_on_feature = ko.observable(state.is_waiting_on_feature);
            self.update = function (state) {
                self.type(state.type);
                self.name(state.name);
                self.is_triggered(state.is_triggered);
                self.is_waiting(state.is_waiting);
                self.is_waiting_on_zhop(state.is_waiting_on_zhop);
                self.is_waiting_on_extruder(state.is_waiting_on_extruder);
                self.snapshot_command(state.snapshot_command);
                self.require_zhop(state.require_zhop);
                self.trigger_count(state.trigger_count);
                self.is_homed(state.is_homed);
                self.is_in_position(state.is_in_position);
                self.in_path_position(state.in_path_position);
                self.is_waiting_on_feature(state.is_waiting_on_feature);
            };

            self.triggerBackgroundIconClass = ko.pureComputed(function () {
                if (!self.is_homed())
                    return "bg-not-homed";
                else if (!self.is_triggered() && Octolapse.PrinterStatus.isPaused())
                    return " bg-paused";
                else
                    return "";
            }, self);

            /* style related computed functions */
            self.triggerStateText = ko.pureComputed(function () {
                if (!self.is_homed())
                    return "Idle until all axes are homed";
                else if (self.is_triggered())
                    return "Triggering a snapshot";
                else if (Octolapse.PrinterStatus.isPaused())
                    return "Paused";
                else if (self.is_waiting()) {
                    // Create a list of things we are waiting on
                    var waitText = "Waiting";
                    var waitList = [];
                    if (self.is_waiting_on_zhop())
                        waitList.push("zhop");
                    if (self.is_waiting_on_extruder())
                        waitList.push("extruder");
                    if (!self.is_in_position() && !self.in_path_position())
                        waitList.push("position");
                    if (self.is_waiting_on_feature())
                        waitList.push("feature");
                    if (waitList.length > 1) {
                        waitText += " for " + waitList.join(" and ");
                        waitText += " to trigger";
                    }
                    else if (waitList.length === 1)
                        waitText += " for " + waitList[0] + " to trigger";
                    return waitText;
                }

                else
                    return "Looking for snapshot gcode";

            }, self);
            self.triggerIconClass = ko.pureComputed(function () {
                if (!self.is_homed())
                    return "not-homed";
                if (self.is_triggered())
                    return "trigger";
                if (Octolapse.PrinterStatus.isPaused())
                    return "paused";
                if (self.is_waiting())
                    return "wait";
                else
                    return "fa-inverse";
            }, self);

            self.getInfoText = ko.pureComputed(function () {
                return "Triggering on gcode command: " + self.snapshot_command();


            }, self);
            self.getInfoIconText = ko.pureComputed(function () {
                return self.snapshot_command()
            }, self);

        };
        Octolapse.layerTriggerStateViewModel = function (state) {
            //console.log("creating layer trigger state view model");
            var self = this;
            self.type = ko.observable(state.type);
            self.name = ko.observable(state.name);
            self.is_triggered = ko.observable(state.is_triggered);
            self.is_waiting = ko.observable(state.is_waiting);
            self.is_waiting_on_zhop = ko.observable(state.is_waiting_on_zhop);
            self.is_waiting_on_extruder = ko.observable(state.is_waiting_on_extruder);
            self.current_increment = ko.observable(state.current_increment);
            self.is_layer_change = ko.observable(state.is_layer_change);
            self.is_layer_change_wait = ko.observable(state.is_layer_change_wait);
            self.is_height_change = ko.observable(state.is_height_change);
            self.is_height_change_wait = ko.observable(state.is_height_change_wait);
            self.height_increment = ko.observable(state.height_increment).extend({numeric: 2});
            self.require_zhop = ko.observable(state.require_zhop);
            self.trigger_count = ko.observable(state.trigger_count).extend({compactint: 1});
            self.is_homed = ko.observable(state.is_homed);
            self.layer = ko.observable(state.layer);
            self.is_in_position = ko.observable(state.is_in_position);
            self.in_path_position = ko.observable(state.Isin_path_position);
            self.is_waiting_on_feature = ko.observable(state.is_waiting_on_feature);
            self.update = function (state) {
                self.type(state.type);
                self.name(state.name);
                self.is_triggered(state.is_triggered);
                self.is_waiting(state.is_waiting);
                self.is_waiting_on_zhop(state.is_waiting_on_zhop);
                self.is_waiting_on_extruder(state.is_waiting_on_extruder);
                self.current_increment(state.current_increment);
                self.is_layer_change(state.is_layer_change);
                self.is_layer_change_wait(state.is_layer_change_wait);
                self.is_height_change(state.is_height_change);
                self.is_height_change_wait(state.is_height_change_wait);
                self.height_increment(state.height_increment);
                self.require_zhop(state.require_zhop);
                self.trigger_count(state.trigger_count);
                self.is_homed(state.is_homed);
                self.layer(state.layer);
                self.is_in_position(state.is_in_position);
                self.in_path_position(state.in_path_position);
                self.is_waiting_on_feature(state.is_waiting_on_feature);
            };
            self.triggerBackgroundIconClass = ko.pureComputed(function () {
                if (!self.is_homed())
                    return "bg-not-homed";
                else if (!self.is_triggered() && Octolapse.PrinterStatus.isPaused())
                    return " bg-paused";
            }, self);

            /* style related computed functions */
            self.triggerStateText = ko.pureComputed(function () {
                if (!self.is_homed())
                    return "Idle until all axes are homed";
                else if (self.is_triggered())
                    return "Triggering a snapshot";
                else if (Octolapse.PrinterStatus.isPaused())
                    return "Paused";
                else if (self.is_waiting()) {
                    // Create a list of things we are waiting on
                    //console.log("Generating wait state text for LayerTrigger");
                    var waitText = "Waiting";
                    var waitList = [];
                    if (self.is_waiting_on_zhop())
                        waitList.push("zhop");
                    if (self.is_waiting_on_extruder())
                        waitList.push("extruder");
                    if (!self.is_in_position() && !self.in_path_position())
                    {
                        waitList.push("position");
                        //console.log("Waiting on position.");
                    }
                    if (self.is_waiting_on_feature())
                        waitList.push("feature");
                    if (waitList.length > 1) {
                        waitText += " for " + waitList.join(" and ");
                        waitText += " to trigger";
                    }

                    else if (waitList.length === 1)
                        waitText += " for " + waitList[0] + " to trigger";
                    return waitText;
                }
                else if (self.height_increment() > 0) {
                    var heightToTrigger = self.height_increment() * self.current_increment();
                    return "Triggering when height reaches " + heightToTrigger.toFixed(1) + " mm";
                }
                else
                    return "Triggering on next layer change";

            }, self);

            self.triggerIconClass = ko.pureComputed(function () {
                if (!self.is_homed())
                    return "not-homed";
                if (self.is_triggered())
                    return "trigger";
                if (Octolapse.PrinterStatus.isPaused())
                    return "paused";
                if (self.is_waiting())
                    return " wait";
                else
                    return " fa-inverse";
            }, self);

            self.getInfoText = ko.pureComputed(function () {
                var val = 0;
                if (self.height_increment() > 0)

                    val = self.height_increment() + " mm";

                else
                    val = "layer";
                return "Triggering every " + Octolapse.ToCompactInt(val);


            }, self);
            self.getInfoIconText = ko.pureComputed(function () {
                var val = 0;
                if (self.height_increment() > 0)
                    val = self.current_increment();
                else
                    val = self.layer();
                return Octolapse.ToCompactInt(val);
            }, self);

        };
        Octolapse.timerTriggerStateViewModel = function (state) {
            //console.log("creating timer trigger state view model");
            var self = this;
            self.type = ko.observable(state.type);
            self.name = ko.observable(state.name);
            self.is_triggered = ko.observable(state.is_triggered);
            self.is_waiting = ko.observable(state.is_waiting);
            self.is_waiting_on_zhop = ko.observable(state.is_waiting_on_zhop);
            self.is_waiting_on_extruder = ko.observable(state.is_waiting_on_extruder);
            self.seconds_to_trigger = ko.observable(state.seconds_to_trigger);
            self.interval_seconds = ko.observable(state.interval_seconds);
            self.trigger_start_time = ko.observable(state.trigger_start_time).extend({time: null});
            self.pause_time = ko.observable(state.pause_time).extend({time: null});
            self.require_zhop = ko.observable(state.require_zhop);
            self.trigger_count = ko.observable(state.trigger_count);
            self.is_homed = ko.observable(state.is_homed);
            self.is_in_position = ko.observable(state.is_in_position);
            self.in_path_position = ko.observable(state.Isin_path_position);
            self.is_waiting_on_feature = ko.observable(state.is_waiting_on_feature);
            self.update = function (state) {
                self.type(state.type);
                self.name(state.name);
                self.is_triggered(state.is_triggered);
                self.is_waiting(state.is_waiting);
                self.is_waiting_on_zhop(state.is_waiting_on_zhop);
                self.is_waiting_on_extruder(state.is_waiting_on_extruder);
                self.require_zhop(state.require_zhop);
                self.seconds_to_trigger(state.seconds_to_trigger);
                self.trigger_start_time(state.trigger_start_time);
                self.pause_time(state.pause_time);
                self.interval_seconds(state.interval_seconds);
                self.trigger_count(state.trigger_count);
                self.is_homed(state.is_homed);
                self.is_in_position(state.is_in_position);
                self.in_path_position(state.in_path_position);
                self.is_waiting_on_feature(state.is_waiting_on_feature);
            };


            /* style related computed functions */
            self.triggerStateText = ko.pureComputed(function () {
                if (!self.is_homed())
                    return "Idle until all axes are homed";
                else if (self.is_triggered())
                    return "Triggering a snapshot";
                else if (Octolapse.PrinterStatus.isPaused())
                    return "Paused";
                else if (self.is_waiting()) {
                    // Create a list of things we are waiting on
                    var waitText = "Waiting";
                    var waitList = [];
                    if (self.is_waiting_on_zhop())
                        waitList.push("zhop");
                    if (self.is_waiting_on_extruder())
                        waitList.push("extruder");
                    if (!self.is_in_position() && !self.in_path_position())
                        waitList.push("position");
                    if (self.is_waiting_on_feature())
                        waitList.push("feature");
                    if (waitList.length > 1) {
                        waitText += " for " + waitList.join(" and ");
                        waitText += " to trigger";
                    }
                    else if (waitList.length === 1)
                        waitText += " for " + waitList[0] + " to trigger";
                    return waitText;
                }

                else
                    return "Triggering in " + self.seconds_to_trigger() + " seconds";

            }, self);
            self.triggerBackgroundIconClass = ko.pureComputed(function () {
                if (!self.is_homed())
                    return "bg-not-homed";
                else if (!self.is_triggered() && Octolapse.PrinterStatus.isPaused())
                    return " bg-paused";
            }, self);
            self.triggerIconClass = ko.pureComputed(function () {
                if (!self.is_homed())
                    return "not-homed";
                if (self.is_triggered())
                    return "trigger";
                if (Octolapse.PrinterStatus.isPaused())
                    return "paused";
                if (self.is_waiting())
                    return " wait";
                else
                    return " fa-inverse";
            }, self);
            self.getInfoText = ko.pureComputed(function () {
                return "Triggering every " + Octolapse.ToTimer(self.interval_seconds());
            }, self);
            self.getInfoIconText = ko.pureComputed(function () {
                return "Triggering every " + Octolapse.ToTimer(self.interval_seconds());
            }, self);
        };

        OCTOPRINT_VIEWMODELS.push([
            Octolapse.StatusViewModel
            , []
            , ["#octolapse_tab", "#octolapse_navbar"]
        ]);
    }
);
