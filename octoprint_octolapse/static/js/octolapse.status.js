/*
##################################################################################
# Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
# Copyright (C) 2023  Brad Hochgesang
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

        Octolapse.CurrentSettingViewModel = function(type, values)
        {
            var self = this;
            // defaults
            self.guid = values.guid;
            self.name = values.name;
            self.description = values.description;
            if (type === "printer")
            {
                self.has_been_saved_by_user = values.has_been_saved_by_user;
            }
            else if (type === "stabilization")
            {
                self.wait_for_moves_to_finish = values.wait_for_moves_to_finish;
            }
            else if (type ==="trigger")
            {
                self.trigger_type = values.trigger_type;
            }
            else if (type === "camera")
            {
                self.enabled = ko.observable(values.enabled);
                self.enable_custom_image_preferences = values.enable_custom_image_preferences;
            }
        };

        Octolapse.StatusViewModel = function () {
            // Create a reference to this object
            var self = this;
            // Add this object to our Octolapse namespace
            Octolapse.Status = this;
            // Assign the Octoprint settings to our namespace
            self.is_timelapse_active = ko.observable(false);
            self.is_taking_snapshot = ko.observable(false);
            self.is_rendering = ko.observable(false);
            self.snapshot_count = ko.observable(0);
            self.snapshot_failed_count = ko.observable(0);
            self.snapshot_error = ko.observable(false);
            self.waiting_to_render = ko.observable();
            self.current_printer_profile_guid = ko.observable();
            self.current_stabilization_profile_guid = ko.observable();
            self.current_trigger_profile_guid = ko.observable();
            self.current_snapshot_profile_guid = ko.observable();
            self.current_rendering_profile_guid = ko.observable();
            self.current_logging_profile_guid = ko.observable();
            self.current_settings_showing = ko.observable(true);
            self.profiles = ko.observable({
                'printers': ko.observableArray([new Octolapse.CurrentSettingViewModel("printer", {name: "Unknown", guid: "", description:"",has_been_saved_by_user: false})]),
                'stabilizations': ko.observableArray([new Octolapse.CurrentSettingViewModel("stabilization", {name: "Unknown", guid: "", description:""})]),
                'triggers': ko.observableArray([new Octolapse.CurrentSettingViewModel("trigger", {name: "Unknown", guid: "", description:""})]),
                'snapshots': ko.observableArray([new Octolapse.CurrentSettingViewModel("snapshot", {name: "Unknown", guid: "", description:""})]),
                'renderings': ko.observableArray([new Octolapse.CurrentSettingViewModel("rendering", {name: "Unknown", guid: "", description:""})]),
                'cameras': ko.observableArray([new Octolapse.CurrentSettingViewModel("camera", {name: "Unknown", guid: "", description:"", enabled: false})]),
                'logging_profiles': ko.observableArray([new Octolapse.CurrentSettingViewModel("logging_profile", {name: "Unknown", guid: "", description:""})])
            });
            self.is_real_time = ko.observable(true);
            self.is_test_mode_active = ko.observable(false);
            self.wait_for_moves_to_finish = ko.observable(false);
            self.current_camera_guid = ko.observable(null);
            self.dialog_rendering_unfinished = new Octolapse.OctolapseDialogRenderingUnfinished();
            self.dialog_rendering_in_process = new Octolapse.OctolapseDialogRenderingInProcess();
            self.timelapse_files_dialog = new Octolapse.OctolapseTimelapseFilesDialog();
            self.PrinterState = new Octolapse.printerStateViewModel();
            self.Position = new Octolapse.positionViewModel();
            self.ExtruderState = new Octolapse.extruderStateViewModel();
            self.TriggerState = new Octolapse.TriggersStateViewModel();
            self.SnapshotPlanState = new Octolapse.snapshotPlanStateViewModel();
            self.webcam_settings_popup = new Octolapse.WebcamSettingsPopupViewModel("octolapse_tab_custom_image_preferences_popup");
            self.SnapshotPlanPreview = new Octolapse.SnapshotPlanPreviewPopupViewModel({
                on_closed: function(){
                    self.SnapshotPlanState.is_preview = false;
                }
            });
            self.IsLatestSnapshotDialogShowing = false;
            self.current_print_volume = null;
            self.current_camera_enabled = ko.observable(false);
            self.show_play_button = ko.observable(false);
            self.camera_image_states = {};
            self.current_camera_state_text = ko.observable("");
            self.canEditSettings = ko.pureComputed(function(){
                // Get the current camera profile
                var current_camera = self.getCurrentProfileByGuid(self.profiles().cameras(),self.current_camera_guid());
                    if (current_camera != null)
                    {
                        return current_camera.enable_custom_image_preferences;
                    }
                return false;
            });

            self.showWebcamSettings = function(){
                self.webcam_settings_popup.showWebcamSettingsForGuid(self.current_camera_guid());
            };

            self.openTimelapseFilesDialog = function() {
                self.timelapse_files_dialog.open();
            };

            self.getEnabledButtonText = ko.pureComputed(function(){
                if (Octolapse.Globals.main_settings.is_octolapse_enabled())
                {
                    if (self.is_timelapse_active())
                        return "Plugin Enabled and Running";
                    else
                        return "Plugin Enabled";
                }
                else{
                    return "Plugin Disabled";
                }
            });

            self.open_rendering_text = ko.pureComputed(function(){
                if(!self.dialog_rendering_unfinished.is_empty())
                    return "Failed Renderings";
                return "Renderings";
            });

            self.unfinished_renderings_changed = function(data){
                if (data.failed)
                {
                    self.dialog_rendering_unfinished.update(data.failed);
                }
                if (data.in_process)
                {
                    self.dialog_rendering_in_process.update(data.in_process);
                }
            };

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
                $SnapshotDialog.find('.cancel').one('click', function(){
                    closeSnapshotDialog($SnapshotDialog);
                });

                /*$SnapshotDialog.find('#octolapse_snapshot_image_container').one('click', function() {
                    closeSnapshotDialog($SnapshotDialog);
                } );*/

                function closeSnapshotDialog($dialog) {
                    //console.log("Hiding snapshot dialog.");
                    self.IsLatestSnapshotDialogShowing = false;
                    $dialog.modal("hide");
                }


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
                    Octolapse.setLocalStorage(self.SETTINGS_VISIBLE_KEY, newData);
                });
                self.dialog_rendering_in_process.on_after_binding();
                self.dialog_rendering_unfinished.on_after_binding();
                self.timelapse_files_dialog.on_after_binding();
                Octolapse.Help.bindHelpLinks("#octolapse_tab");
            };

            // Update the current tab state
            self.updateState = function(state){
                //console.log("octolapse.status.js - Updating State")
                if (state.trigger_type != null)
                    self.is_real_time(state.trigger_type === "real-time");

                if (state.position != null) {
                    self.Position.update(state.position);
                }
                if (state.printer_state != null) {
                    self.PrinterState.update(state.printer_state);
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

            self.create_current_settings_profile = function(type, values){
                var profiles = [];
                if (values)
                {
                    for (var index=0; index < values.length; index++)
                    {
                        profiles.push(new Octolapse.CurrentSettingViewModel(type, values[index]));
                    }
                }
                return profiles;
            };

            self.load_files = function(){
                //console.log("ocotlapse.status.js - loading dialog files.");
                self.timelapse_files_dialog.load();
                self.dialog_rendering_in_process.load();
                self.dialog_rendering_unfinished.load();
            };

            self.files_changed = function(file_info, action){
                self.timelapse_files_dialog.files_changed(file_info, action);
            };

            self.update = function (settings) {
                //console.log("octolapse.status.js - Updating main settings.");
                if (settings.is_timelapse_active !== undefined)
                    self.is_timelapse_active(settings.is_timelapse_active);
                if (settings.snapshot_count !== undefined)
                    self.snapshot_count(settings.snapshot_count);
                if (settings.snapshot_failed_count !== undefined)
                    self.snapshot_failed_count(settings.snapshot_failed_count);
                if (settings.is_taking_snapshot !== undefined)
                    self.is_taking_snapshot(settings.is_taking_snapshot);
                if (settings.is_rendering !== undefined)
                    self.is_rendering(settings.is_rendering);
                if (settings.waiting_to_render !== undefined)
                    self.waiting_to_render(settings.waiting_to_render);
                if (settings.is_test_mode_active !== undefined)
                    self.is_test_mode_active(settings.is_test_mode_active);

                //console.log("Updating Profiles");
                if (settings.profiles) {
                    self.profiles().printers(self.create_current_settings_profile("printer", settings.profiles.printers));
                    self.profiles().stabilizations(self.create_current_settings_profile("stabilization", settings.profiles.stabilizations));
                    self.profiles().triggers(self.create_current_settings_profile("trigger", settings.profiles.triggers));
                    self.profiles().renderings(self.create_current_settings_profile("rendering", settings.profiles.renderings));
                    self.profiles().cameras(self.create_current_settings_profile("camera", settings.profiles.cameras));
                    self.profiles().logging_profiles(self.create_current_settings_profile("logging_profile", settings.profiles.logging_profiles));
                    self.current_printer_profile_guid(settings.profiles.current_printer_profile_guid);
                    self.current_stabilization_profile_guid(settings.profiles.current_stabilization_profile_guid);
                    self.current_trigger_profile_guid(settings.profiles.current_trigger_profile_guid);
                    self.current_snapshot_profile_guid(settings.profiles.current_snapshot_profile_guid);
                    self.current_rendering_profile_guid(settings.profiles.current_rendering_profile_guid);
                    self.current_logging_profile_guid(settings.profiles.current_logging_profile_guid);
                }
                if (settings.unfinished_renderings)
                {
                    self.dialog_rendering_in_process.update(settings.unfinished_renderings);
                    self.dialog_rendering_unfinished.update(settings.unfinished_renderings);
                }

                self.is_real_time(self.getCurrentTriggerProfileIsRealTime());
                self.current_camera_guid(self.getInitialCameraSelection());
                self.set_current_camera_enabled();
            };

            self.current_stabilization_profile_guid.subscribe(function(newValue){
                var current_stabilization_profile = null;
                for (var i = 0; i < self.profiles().stabilizations().length; i++) {
                    var stabilization_profile = self.profiles().stabilizations()[i];
                    if (stabilization_profile.guid == self.current_stabilization_profile_guid()) {
                        current_stabilization_profile = stabilization_profile;
                        break;
                    }
                }
                if (current_stabilization_profile)
                    self.wait_for_moves_to_finish(current_stabilization_profile.wait_for_moves_to_finish);
                else
                    self.wait_for_moves_to_finish(false);
            });



            // Subscribe to current camera guid changes
            self.current_camera_guid.subscribe(function(newValue){
                self.snapshotCameraChanged();
            });

            self.getInitialCameraSelection = function (){
                // See if the previous camera is in the list.  If so, select it.
                var guid = Octolapse.getLocalStorage('previous-camera-guid');

                for (var i = 0; i < self.profiles().cameras().length; i++)
                {
                    var camera_profile = self.profiles().cameras()[i];
                    if(camera_profile.guid == guid)
                    {
                        self.current_camera_guid(camera_profile.guid);
                        return camera_profile.guid;
                    }
                }
                // This guid doesn't exist, get the first enabled camera
                for (var i = 0; i < self.profiles().cameras().length; i++)
                {
                    var camera_profile = self.profiles().cameras()[i];
                    if(camera_profile.enabled)
                    {
                        self.current_camera_guid(camera_profile.guid);
                        return camera_profile.guid;
                    }
                }
                // No enabled camera, just get the first camera
                if(self.profiles().cameras().length>0)
                    return self.profiles().cameras()[0].guid;
                // Just set it to null, no camera available.
                return null;

            };

            self.hasOneCameraEnabled = ko.pureComputed(function(){
                for (var i = 0; i < self.profiles().cameras().length; i++)
                {
                    if(self.profiles().cameras()[i].enabled())
                    {
                        return true;
                    }
                }
                return false;

            },this);

            self.hasPrinters = ko.pureComputed(function() {
                return self.profiles().printers().length > 0;
            });

            self.hasPrinterSelected = ko.pureComputed(function(){
                return ! (Octolapse.Status.current_printer_profile_guid() == null || Octolapse.Status.current_printer_profile_guid()=="");
            },this);

            self.has_configured_printer_profile = ko.pureComputed(function(){
                //console.log("detecting configured printers.")
                var current_printer = self.getCurrentProfileByGuid(self.profiles().printers(),Octolapse.Status.current_printer_profile_guid());
                if (current_printer != null)
                    return self.is_timelapse_active() || current_printer.slicer_type == 'automatic' || current_printer.has_been_saved_by_user;
                return true;
            },this);

            self.getCurrentTriggerProfileIsRealTime = function(){
                var current_trigger = self.getCurrentProfileByGuid(self.profiles().triggers(),Octolapse.Status.current_trigger_profile_guid());
                if (current_trigger  != null)
                    //console.log(current_trigger.trigger_type);
                    return current_trigger.trigger_type === "real-time";
                return true;
            };

            self.getCurrentProfileByGuid = function(profiles, guid){
                if (guid != null) {
                    for (var i = 0; i < profiles.length; i++) {
                        if (profiles[i].guid == guid) {
                            return profiles[i];
                        }
                    }
                }
                return null;
            };

            self.hasConfigIssues = ko.computed(function(){
                var hasConfigIssues = !self.hasOneCameraEnabled() || !self.hasPrinterSelected() || !self.has_configured_printer_profile();
                return hasConfigIssues;
            },this);

            /*
                Snapshot client animation preview functions
            */
            self.refreshLatestImage = function (targetId, isThumbnail) {
                isThumbnail = isThumbnail || false;
                //console.log("Refreshing Snapshot Thumbnail");
                if (isThumbnail)
                    self.updateLatestSnapshotThumbnail(true, true);
                else
                    self.updateLatestSnapshotImage(true, true);
            };

            self.startSnapshotAnimation = function (targetId) {
                if (targetId in self.IsAnimating && self.IsAnimating[targetId]) {
                    return;
                }
                //console.log("Starting Snapshot Animation for" + targetId);
                // Hide and show the play/refresh button
                if (Octolapse.Globals.main_settings.auto_reload_latest_snapshot()) {
                    var $startAnimationButton = $('#' + targetId + ' .octolapse-snapshot-button-overlay a.play');
                    self.IsAnimating[targetId] = true;
                    $startAnimationButton.fadeOut({
                        start: function () {
                            setTimeout( function() {
                                var $images = $('#' + targetId + ' .snapshot-container .previous-snapshots img');
                                var $current = $('#' + targetId + ' .snapshot-container .latest-snapshot img');
                                // Hide all images in reverse order
                                if ($images.length > 0)
                                {
                                    $current.css("opacity","0");
                                    animate_snapshots($images, $current, $images.length-1, -1, 0, 25);
                                }
                                else
                                {
                                    $current.css("opacity","1");
                                    $startAnimationButton.fadeIn();
                                    self.IsAnimating[targetId] = false;
                                    return;
                                }
                                function animate_snapshots($images, $current, index, step, opacity, delay) {
                                    if (
                                        (step > 0 && index < $images.length) ||
                                        (step < 0 && index > 0)
                                    )
                                    {
                                        setTimeout(function () {
                                            $images.eq(index).css("opacity",opacity.toString());
                                            animate_snapshots($images, $current, index+step, step, opacity, delay);
                                        }, delay);
                                    }
                                    else if(step > 0)
                                    {
                                        if($current) {
                                            $current.css("opacity","1");
                                            $startAnimationButton.fadeIn();
                                            self.IsAnimating[targetId] = false;
                                        }
                                    }
                                    else
                                    {
                                        // fade out the current image
                                        animate_snapshots($images, $current, 0, 1, 1, 100);
                                    }

                                }
                            }, 100);

                        }
                    });
                }
            };

            self.updateLatestSnapshotThumbnail = function (force, updateIfDisabled) {
                if (!updateIfDisabled && !self.current_camera_enabled())
                    return;
                force = force || false;
                //console.log("Trying to update the latest snapshot thumbnail.");
                if (!force) {
                    if (!Octolapse.Globals.main_settings.auto_reload_latest_snapshot()) {
                        //console.log("Not updating the thumbnail, auto-reload is disabled.");
                        return;
                    }
                }

                var snapshotUrl = null;
                if (self.current_camera_guid())
                {
                    snapshotUrl = getLatestSnapshotThumbnailUrl(self.current_camera_guid())+ "&time=" + new Date().getTime();
                }

                self.updateSnapshotAnimation('octolapse_snapshot_thumbnail_container', snapshotUrl);
            };

            self.updateLatestSnapshotImage = function (force) {
                force = force || false;
                //console.log("Trying to update the latest snapshot image.");
                if (!force) {
                    if (!Octolapse.Globals.main_settings.auto_reload_latest_snapshot()) {
                        //console.log("Auto-Update latest snapshot image is disabled.");
                        return;
                    }
                    else if (!self.IsLatestSnapshotDialogShowing) {
                        //console.log("The full screen dialog is not showing, not updating the latest snapshot.");
                        return;
                    }
                }
                var snapshotUrl = null;
                if (self.current_camera_guid())
                {
                    snapshotUrl = getLatestSnapshotUrl(self.current_camera_guid())+ "&time=" + new Date().getTime();
                }
                self.updateSnapshotAnimation('octolapse_snapshot_image_container', snapshotUrl);
            };

            self.erasePreviousSnapshotImages = function (targetId, eraseCurrentImage) {
                eraseCurrentImage = eraseCurrentImage || false;
                if (eraseCurrentImage) {
                    $('#' + targetId + ' .snapshot-container .latest-snapshot img').each(function () {
                        $(this).remove();
                    });
                }
                $('#' + targetId + ' .snapshot-container .previous-snapshots img').each(function () {
                    $(this).remove();
                });
            };

            // takes the list of images, update the frames in the target accordingly and starts any animations
            self.IsAnimating = {};

            self.updateSnapshotAnimation = function (targetId, newSnapshotAddress) {
                //console.log("Updating animation for target id: " + targetId);
                // Get the snapshot-container within the target
                var $target = $('#' + targetId + ' .snapshot-container');
                // Get the latest image
                var $latestSnapshotContainer = $target.find('.latest-snapshot');
                var $latestSnapshot = $latestSnapshotContainer.find('img');
                var $fullscreenControl = $target.find("a.octolapse-fullscreen");

                if (Octolapse.Globals.main_settings.auto_reload_latest_snapshot()) {
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
                    self.show_play_button(numSnapshots>0);
                    while (numSnapshots > parseInt(Octolapse.Globals.main_settings.auto_reload_frames())) {
                        //console.log("Removing overflow previous images according to Auto Reload Frames setting.");
                        var $element = $previousSnapshots.first();
                        $element.remove();

                        numSnapshots--;
                    }
                    $previousSnapshots = $previousSnapshotContainer.find("img");
                    var numPreviousSnapshots = $previousSnapshots.length;
                    var newestImageIndex = numPreviousSnapshots - 1;
                    //console.log("Updating classes for previous " + numPreviousSnapshots + " images.");
                    for (var previousImageIndex = 0; previousImageIndex < numPreviousSnapshots; previousImageIndex++) {
                        $element = $($previousSnapshots.eq(previousImageIndex));
                        //console.log("Updating classes for the previous image delay " + previousImageDelayClass+ ".");
                        $element.css('z-index', previousImageIndex.toString());
                    }
                }
                else
                {
                    self.show_play_button(false);
                }
                // create the newest image
                var $newSnapshot = $(document.createElement('img'));

                self.current_camera_state_text("");
                $fullscreenControl.hide();
                // Set the error handler
                var error_message = "No snapshots have been taken with the current camera.  A preview of your" +
                    " timelapse will start to appear here as snapshots are taken by Octolapse.";
                var on_snapshot_load_error = function(){
                    //console.error("An error occurred loading the newest image, reverting to previous image.");
                    // move the latest preview image back into the newest image section
                    $latestSnapshot.removeClass();
                    $latestSnapshot.appendTo($latestSnapshotContainer);
                    self.current_camera_state_text(error_message);

                };

                if (!newSnapshotAddress)
                {
                    error_message = "No camera is selected.  Choose a camera in the dropdown below.";
                    on_snapshot_load_error(error_message);
                    return;
                }

                $newSnapshot.one('error', on_snapshot_load_error);

                //console.log("Adding the new snapshot image to the latest snapshot container.");
                // create on load event for the newest image
                if (Octolapse.Globals.main_settings.auto_reload_latest_snapshot()) {
                    // Add the new snapshot to the container
                    $newSnapshot.appendTo($latestSnapshotContainer);
                    if ((!(targetId in self.IsAnimating) || !self.IsAnimating[targetId]))
                    {
                        $newSnapshot.one('load', function () {
                            self.startSnapshotAnimation(targetId);
                            $fullscreenControl.show();
                        });
                    }
                    else {
                        // We could have a race condition here.  Need to ensure the opacity of this element is
                        // set to 1 after any animations are finished.
                        $newSnapshot.css("opacity","0");
                    }
                }
                else {
                    $newSnapshot.one('load', function () {
                        $fullscreenControl.show();
                        // Hide the latest image
                        if ($latestSnapshot.length == 1)
                        {
                            $latestSnapshot.fadeOut(250, function () {
                                // Remove the latest image
                                if($latestSnapshot.length)
                                    $latestSnapshot.remove();
                                // Set the new snapshot to hidden initially
                                $newSnapshot.css('display', 'none');
                                // Add the new snapshot to the container
                                $newSnapshot.appendTo($latestSnapshotContainer);
                                // fade it in.  Ahhh..
                                $newSnapshot.fadeIn(250);
                            });
                        }
                        else
                        {
                            // Set the new snapshot to hidden initially
                            $newSnapshot.css('display', 'none');
                            // Add the new snapshot to the container
                            $newSnapshot.appendTo($latestSnapshotContainer);
                            // fade it in.  Ahhh..
                            $newSnapshot.fadeIn(250);
                        }
                    });
                }
                // set the src and start to load
                $newSnapshot.attr('src', newSnapshotAddress);
            };

            self.toggleInfoPanel = function (observable, panelType){
                data = {
                    panel_type: panelType,
                    client_id: Octolapse.Globals.client_id
                };
                $.ajax({
                    url: "./plugin/octolapse/toggleInfoPanel",
                    type: "POST",
                    data: JSON.stringify(data),
                    contentType: "application/json",
                    dataType: "json",
                    success: function(result){
                        if (result.success)
                        {
                            observable(result.enabled);
                        }
                    },
                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                        var message = "Unable to toggle the panel.  Status: " + textStatus + ".  Error: " + errorThrown;
                        var options = {
                            title: 'Info Panel Toggle Error',
                            text: message,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse",
                            desktop: {
                                desktop: false
                            }
                        };
                        Octolapse.displayPopup(options);
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
                        return "trigger-status-template";
                }
            };

            self.getStateSummaryText = ko.pureComputed(function () {
                if(!self.is_timelapse_active()) {
                    if(self.waiting_to_render())
                        return "Octolapse is waiting for print to complete.";
                    if( self.is_rendering())
                        return "Octolapse is rendering a timelapse.";
                    if(!Octolapse.Globals.main_settings.is_octolapse_enabled())
                        return 'Octolapse is disabled.';
                    return 'Octolapse is enabled and idle.';
                }
                if(!Octolapse.Globals.main_settings.is_octolapse_enabled())
                    return 'Octolapse is disabled.';
                if(Octolapse.Status.is_real_time())
                {
                    if(! self.PrinterState.is_initialized())
                        return 'Octolapse is waiting for more information from the server.';
                    if( self.PrinterState.hasPrinterStateErrors())
                        return 'Octolapse is waiting to initialize.';
                }
                if( self.is_taking_snapshot())
                    return "Octolapse is taking a snapshot.";
                return "Octolapse is waiting to take snapshot.";

            }, self);

            self.getStatusText = ko.pureComputed(function () {
                if (self.is_timelapse_active() || self.is_rendering())
                    return '';
                if (self.waiting_to_render())
                    return 'Timelapse Canceled';
                return '';
            }, self);

            self.previewSnapshotPlans = function(data){
                //console.log("Updating snapshot plan state with a preview of the snapshot plans");
                self.SnapshotPlanState.is_preview = true;
                self.SnapshotPlanState.update(data);
                self.SnapshotPlanPreview.openDialog();

            };

            self.onTimelapseStart = function () {
                self.TriggerState.removeAll();
                self.PrinterState.is_initialized(false);
            };

            self.onTimelapseStop = function () {
                self.is_timelapse_active(false);
                self.is_taking_snapshot(false);
                self.waiting_to_render(true);
            };

            self.stopTimelapse = function () {
                if (Octolapse.Globals.is_admin()) {
                    //console.log("octolapse.status.js - ButtonClick: StopTimelapse");
                    var message = "Warning: You cannot restart octolapse once it is stopped until the next print." +
                        "  Do you want to stop Octolapse?";
                    if (confirm(message)) {
                        $.ajax({
                            url: "./plugin/octolapse/stopTimelapse",
                            type: "POST",
                            contentType: "application/json",
                            success: function (data) {
                                //console.log("octolapse.status.js - stopTimelapse - success" + data);
                            },
                            error: function (XMLHttpRequest, textStatus, errorThrown) {
                                var message = "Unable to stop octolapse!.  Status: " + textStatus + ".  Error: " + errorThrown;
                                var options = {
                                    title: 'Stop Timelapse Error',
                                    text: message,
                                    type: 'error',
                                    hide: false,
                                    addclass: "octolapse",
                                    desktop: {
                                        desktop: false
                                    }
                                };
                                Octolapse.displayPopup(options);
                            }
                        });
                    }
                }
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

            // Octolapse settings link
            self.openOctolapseSettings = function(profile_type) {
                $('a#navbar_show_settings').click();
                $('li#settings_plugin_octolapse_link a').click();
                if(profile_type)
                {
                    var query= "#octolapse_settings_nav a[data-profile-type='"+profile_type+"']";
                    $(query).click();
                }
            };
            // Printer Profile Settings
            self.printers_sorted = ko.computed(function() { return self.nameSort(self.profiles().printers); });

            self.openCurrentPrinterProfile = function () {
                //console.log("Opening current printer profile from tab.")
                Octolapse.Printers.showAddEditDialog(self.current_printer_profile_guid(), false);
            };
            self.createNewPrinterProfile = function () {
                //console.log("Opening current printer profile from tab.")
                Octolapse.Printers.showAddEditDialog(null, false);
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
            self.stabilizations_sorted = ko.computed(function() { return self.nameSort(self.profiles().stabilizations); });
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


            // Trigger Profile Settings
            self.triggers_sorted = ko.computed(function() { return self.nameSort(self.profiles().triggers); });
            self.openCurrentTriggerProfile = function () {
                //console.log("Opening current trigger profile from tab.")
                Octolapse.Triggers.showAddEditDialog(self.current_trigger_profile_guid(), false);
            };
            self.defaultTriggerChanged = function (obj, event) {
                if (Octolapse.Globals.is_admin()) {
                    if (event.originalEvent) {
                        // Get the current guid
                        var guid = $("#octolapse_tab_trigger_profile").val();
                        //console.log("Default trigger is changing to " + guid + " from " + self.current_trigger_profile_guid());
                        Octolapse.Triggers.setCurrentProfile(guid);
                        return true;
                    }
                }
            };

            // Rendering Profile Settings
            self.renderings_sorted = ko.computed(function() { return self.nameSort(self.profiles().renderings); });
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
            self.cameras_sorted = ko.computed(function() { return self.nameSort(self.profiles().cameras); });
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
                Octolapse.Cameras.getProfileByGuid(guid).toggleCamera(function(value){
                    self.getCurrentProfileByGuid(self.profiles().cameras(), guid).enabled(value);
                });
            };
            self.set_current_camera_enabled = function() {
                var current_camera = null;
                for (var i = 0; i < self.profiles().cameras().length; i++) {
                    var camera_profile = self.profiles().cameras()[i];
                    if (camera_profile.guid == self.current_camera_guid()) {
                        current_camera = camera_profile;
                        break;
                    }
                }
                if (current_camera)
                    self.current_camera_enabled(current_camera.enabled());
                else
                    self.current_camera_enabled(true);
            };
            self.snapshotCameraChanged = function() {
                if (self.current_camera_guid()) {
                    // Set the local storage guid here.
                    Octolapse.setLocalStorage('previous-camera-guid', self.current_camera_guid());
                    self.current_camera_enabled(true);
                }

                self.set_current_camera_enabled();
                // Update the current camera profile
                var guid = self.current_camera_guid();
                //console.log("Updating the latest snapshot from: " + Octolapse.Status.current_camera_guid() + " to " + guid);
                self.erasePreviousSnapshotImages('octolapse_snapshot_image_container',true);
                self.erasePreviousSnapshotImages('octolapse_snapshot_thumbnail_container',true);
                self.updateLatestSnapshotThumbnail(true, true);
                self.updateLatestSnapshotImage(true);
            };

            // Logging Profile Settings
            self.logging_profiles_sorted = ko.computed(function() { return self.nameSort(self.profiles().logging_profiles); });
            self.openCurrentLoggingProfile = function () {
                //console.log("Opening current logging profile from tab.")
                Octolapse.LoggingProfiles.showAddEditDialog(self.current_logging_profile_guid(), false);
            };
            self.defaultLoggingProfileChanged = function (obj, event) {
                if (Octolapse.Globals.is_admin()) {
                    if (event.originalEvent) {
                        // Get the current guid
                        var guid = $("#octolapse_tab_logging_profile").val();
                        //console.log("Default Logging Profile is changing to " + guid);
                        Octolapse.LoggingProfiles.setCurrentProfile(guid);
                        return true;
                    }
                }
            };

            self.setDescriptionAsTitle = function(option, item) {
                if (!item)
                    return;
                ko.applyBindingsToNode(option, {attr: {title: item.description}}, item);
            };

            self.getPrinterProfileTitle = ko.computed(function () {
                var currentProfile = self.getCurrentProfileByGuid(self.profiles().printers(),Octolapse.Status.current_printer_profile_guid());
                if (currentProfile == null)
                    return "";
                return currentProfile.description;
            });
            self.getStabilizationProfileTitle = ko.computed(function () {
                var currentProfile = self.getCurrentProfileByGuid(self.profiles().stabilizations(),Octolapse.Status.current_stabilization_profile_guid());
                if (currentProfile == null)
                    return "";
                return currentProfile.description;
            });
            self.getTriggerProfileTitle = ko.computed(function () {
                var currentProfile = self.getCurrentProfileByGuid(self.profiles().triggers(),Octolapse.Status.current_trigger_profile_guid());
                if (currentProfile == null)
                    return "";
                return currentProfile.description;
            });
            self.getRenderingProfileTitle = ko.computed(function () {
                var currentProfile = self.getCurrentProfileByGuid(self.profiles().renderings(),Octolapse.Status.current_rendering_profile_guid());
                if (currentProfile == null)
                    return "";
                return currentProfile.description;
            });
            self.getLoggingProfileTitle = ko.computed(function () {
                var currentProfile = self.getCurrentProfileByGuid(self.profiles().logging_profiles(),Octolapse.Status.current_logging_profile_guid());
                if (currentProfile == null)
                    return "";
                return currentProfile.description;
            });

        };
        /*
            Status Tab viewmodels
        */
        Octolapse.printerStateViewModel = function () {
            var self = this;
            self.gcode = ko.observable("");
            self.x_homed = ko.observable(false);
            self.y_homed = ko.observable(false);
            self.z_homed = ko.observable(false);
            self.has_definite_position = ko.observable(false);
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
            self.is_metric = ko.observable(null);
            self.is_initialized = ko.observable(false);
            self.is_printer_primed = ko.observable(false);

            self.update = function (state) {
                self.gcode(state.gcode);
                self.x_homed(state.x_homed);
                self.y_homed(state.y_homed);
                self.z_homed(state.z_homed);
                self.has_definite_position(state.has_definite_position);
                self.is_layer_change(state.is_layer_change);
                self.is_height_change(state.is_height_change);
                self.is_in_position(state.is_in_position);
                self.in_path_position(state.in_path_position);
                self.is_zhop(state.is_zhop);
                self.is_relative(state.is_relative);
                self.is_extruder_relative(state.is_extruder_relative);
                self.layer(state.layer);
                self.height(state.height);
                self.last_extruder_height(state.last_extruder_height);
                self.is_metric(state.is_metric);
                self.is_printer_primed(state.is_printer_primed);
                self.is_initialized(true);
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

            self.hasPrinterStateErrors = ko.pureComputed(function(){
                if (Octolapse.Status.is_timelapse_active() && self.is_initialized())

                    if (!(self.x_homed() && self.y_homed() && self.z_homed())
                        || self.is_relative() == null
                        || self.is_extruder_relative() == null
                        || !self.is_metric()
                    )
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

            self.getHasDefinitePositionText = ko.pureComputed(function(){
               if (self.has_definite_position())
                   return "Current position is definite";
               else
                   return "Current position is not fully known.";
            });

            self.getIsInPositionStateText = ko.pureComputed(function () {
                if (self.is_in_position())
                    return "In position";
                else if (self.in_path_position())
                    return "In path position";
                else
                    return "Not in position";
            }, self);

            self.getIsMetricStateText = ko.pureComputed(function () {
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
            self.getIsLayerChangeStateText = ko.pureComputed(function () {
                if (self.is_layer_change())
                    return "Layer change detected";
                else
                    return "Not changing layers";
            }, self);

            self.getIsPrinterPrimedStateTitle = ko.pureComputed(function(){
                if(self.is_printer_primed())
                    return "Primed";
                else
                    return "Not Primed";
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
            };

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
                return "fa-times";
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
                    return "fa-exclamation";
                if (self.is_deretracting() && self.is_deretracting_start)
                    return "fa-level-down";
                if (self.is_deretracting())
                    return "fa-arrow-down";
                return "fa-times";
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
                    return "fa-minus";
                if (self.is_extruding_start())
                    return "fa-play-circle-o";
                if (self.is_extruding())
                    return "fa-play";
                return "fa-times";
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

        Octolapse.TriggersStateViewModel = function () {
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
            self.has_definite_position = ko.observable(state.has_definite_position);
            self.is_in_position = ko.observable(state.is_in_position);
            self.in_path_position = ko.observable(state.Isin_path_position);
            self.update = function (state) {
                self.type(state.type);
                self.name(state.name);
                self.is_triggered(state.is_triggered);
                self.is_waiting(state.is_waiting);
                self.is_waiting_on_zhop(state.is_waiting_on_zhop);
                self.is_waiting_on_extruder(state.is_waiting_on_extruder);
                self.require_zhop(state.require_zhop);
                self.trigger_count(state.trigger_count);
                self.has_definite_position(state.has_definite_position);
                self.is_in_position(state.is_in_position);
                self.in_path_position(state.in_path_position);
            };
            self.triggerBackgroundIconClass = ko.pureComputed(function () {
                if (!self.has_definite_position())
                    return "bg-unknown-position";
                else if (!self.is_triggered() && Octolapse.PrinterStatus.isPaused())
                    return " bg-paused";
                else
                    return "";
            }, self);
            /* style related computed functions */
            self.triggerStateText = ko.pureComputed(function () {
                //console.log("Calculating trigger state text.");
                if (!self.has_definite_position())
                    return "Idle until a definite position is found";
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
                if (!self.has_definite_position())
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
            self.has_definite_position = ko.observable(state.has_definite_position);
            self.is_in_position = ko.observable(state.is_in_position);
            self.in_path_position = ko.observable(state.Isin_path_position);
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
                self.has_definite_position(state.has_definite_position);
                self.is_in_position(state.is_in_position);
                self.in_path_position(state.in_path_position);
            };

            self.getSnapshotCommands =  ko.pureComputed(function () {
                commands = ["@OCTOLAPSE TAKE-SNAPSHOT", "SNAP"];
                if (self.snapshot_command().length > 0)
                {
                    commands.push(self.snapshot_command());
                }
                return commands;
            }, self);

            /* style related computed functions */
            self.triggerStateText = ko.pureComputed(function () {
                if (!self.has_definite_position())
                    return "Idle until the printer's position is known.";
                else if (self.is_triggered())
                    return "Triggering a snapshot.";
                else if (Octolapse.PrinterStatus.isPaused())
                    return "The trigger is paused.";
                else if (self.is_waiting()) {
                    var waitText = "Waiting for";
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
                    if (waitList.length > 0) {
                        if (waitList.length === 1) {
                            waitText += waitList[0];
                        }
                        else if (waitList.length > 1) {
                            var commaSeparated = waitList.slice(0, waitList.length - 2);
                            waitText += commaSeparated.join(", ");
                            if (waitList.length > 2)
                                waitText += ", ";
                            waitText += waitList[waitList.length-1];
                        }
                        waitText += " to trigger.";
                    }
                    return waitText;
                }
                else{
                    return "Waiting for a snapshot command.";
                }
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
            self.has_definite_position = ko.observable(state.has_definite_position);
            self.is_in_position = ko.observable(state.is_in_position);
            self.in_path_position = ko.observable(state.in_path_position);

            self.require_zhop = ko.observable(state.require_zhop);
            self.trigger_count = ko.observable(state.trigger_count).extend({compactint: 1});
            self.layer = ko.observable(state.layer);

            self.update = function (state) {
                self.type(state.type);
                self.name(state.name);
                // Config Info
                self.require_zhop(state.require_zhop);
                self.height_increment(state.height_increment);
                // Layer and current increment
                self.layer(state.layer);
                self.current_increment(state.current_increment);
                self.trigger_count(state.trigger_count);
                // Triggering/Waiting Status
                self.is_triggered(state.is_triggered);
                self.is_waiting(state.is_waiting);
                self.is_layer_change(state.is_layer_change);
                self.is_layer_change_wait(state.is_layer_change_wait);
                self.is_height_change(state.is_height_change);
                self.is_height_change_wait(state.is_height_change_wait);
                self.is_waiting_on_zhop(state.is_waiting_on_zhop);
                self.is_waiting_on_extruder(state.is_waiting_on_extruder);
                self.has_definite_position(state.has_definite_position);
                self.is_in_position(state.is_in_position);
                self.in_path_position(state.in_path_position);
                // Layer/Height change Info
            };

            /* style related computed functions */
            self.triggerStateText = ko.pureComputed(function () {
                if (!self.has_definite_position())
                    return "Idle until the printer's position is known.";
                else if (self.is_triggered())
                    return "Triggering a snapshot.";
                else if (Octolapse.PrinterStatus.isPaused())
                    return "The trigger is paused.";
                else if (self.is_waiting()) {
                    var waitText = "Waiting for";
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
                    if (waitList.length > 0) {
                        if (waitList.length === 1) {
                            waitText += waitList[0];
                        }
                        else if (waitList.length > 1) {
                            var commaSeparated = waitList.slice(0, waitList.length - 2);
                            waitText += commaSeparated.join(", ");
                            if (waitList.length > 2)
                                waitText += ", ";
                            waitText += waitList[waitList.length-1];
                        }
                        waitText += " to trigger.";
                    }
                    return waitText;
                }
                else if (self.height_increment() != null && self.height_increment() > 0) {
                    var heightToTrigger = self.height_increment() * (self.current_increment() + 1);
                    return "Triggering when height reaches " + Octolapse.roundToIncrement(heightToTrigger,0.01).toString() + "mm.";
                }
                else
                    return "Triggering on next layer change.";

            }, self);

            self.triggerTypeText = ko.pureComputed(function(){
                if (self.height_increment() === 0) {
                    return "Layer";
                }
                return "Height";
            });

            self.currentTriggerIncrement = ko.pureComputed(function(){
                if (self.height_increment() === 0) {
                    return self.layer;
                }
                return Octolapse.roundToIncrement(self.current_increment(),0.01).toString()  + "mm";
            });

            self.triggerOnText = ko.pureComputed(function () {
                if (self.height_increment !== null || self.height_increment() === 0)
                {
                    return "Every Layer";
                }

                return "Every " + Octolapse.roundToIncrement(self.height_increment(),0.01).toString()  + "mm";
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
            self.has_definite_position = ko.observable(state.has_definite_position);
            self.is_in_position = ko.observable(state.is_in_position);
            self.in_path_position = ko.observable(state.Isin_path_position);
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
                self.has_definite_position(state.has_definite_position);
                self.is_in_position(state.is_in_position);
                self.in_path_position(state.in_path_position);
            };

            /* style related computed functions */
            self.triggerStateText = ko.pureComputed(function () {
                if (!self.has_definite_position())
                    return "Idle until the printer's position is known.";
                else if (self.is_triggered())
                    return "Triggering a snapshot.";
                else if (Octolapse.PrinterStatus.isPaused())
                    return "The trigger is paused.";
                else if (self.is_waiting()) {
                    var waitText = "Waiting for";
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
                    if (waitList.length > 0) {
                        if (waitList.length === 1) {
                            waitText += waitList[0];
                        }
                        else if (waitList.length > 1) {
                            var commaSeparated = waitList.slice(0, waitList.length - 2);
                            waitText += commaSeparated.join(", ");
                            if (waitList.length > 2)
                                waitText += ", ";
                            waitText += waitList[waitList.length-1];
                        }
                        waitText += " to trigger.";
                    }
                    return waitText;
                }
                else
                    return "Triggering in " + self.secondsToTrigger() + ".";

            }, self);

            self.secondsInterval = ko.pureComputed(function () {
                return Octolapse.ToTimer(self.interval_seconds());
            }, self);

            self.secondsToTrigger = ko.pureComputed(function () {
                return Octolapse.ToTimer(self.seconds_to_trigger());
            }, self);

        };

        OCTOPRINT_VIEWMODELS.push([
            Octolapse.StatusViewModel
            , []
            , ["#octolapse_tab", "#octolapse_navbar"]
        ]);
    }
);
