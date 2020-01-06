/*
##################################################################################
# Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
# Copyright (C) 2020  Brad Hochgesang
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
    Octolapse.FailedRenderingListItem = function (values) {
        var self = this;
        self.id = values.job_guid + values.camera_guid;
        self.job_guid = values.job_guid;
        self.print_start_time = values.print_start_time;
        self.print_start_time_text = Octolapse.toLocalDateString(values.print_start_time);
        /*self.print_end_time = values.print_end_time;
        self.print_end_time_text = Octolapse.toLocalDateString(values.print_end_time);*/
        self.print_end_state = values.print_end_state;
        self.print_file_name = values.print_file_name;
        self.print_file_extension = values.print_file_extension;
        self.job_path = values.job_path;
        self.camera_profile_guid = values.camera_profile_guid;
        self.camera_guid = values.camera_guid;
        self.camera_path = values.camera_path;
        self.camera_name = values.camera_name;
        self.rendering_guid = values.rendering_guid;
        self.rendering_name = values.rendering_name;
        self.rendering_description = values.rendering_description;
        self.file_size = values.file_size;
        self.file_size_text = Octolapse.toFileSizeString(values.file_size,1);
        self.render_profile_override_guid = ko.observable(null);
        self.camera_profile_override_guid = ko.observable(null);

        self.get_rendering_option_caption = function () {
            if (!self.rendering_guid) {
                return "Current Profile";
            } else {
                return "Original - " + self.rendering_name;
            }
        };

        self.set_rendering_profile_option_description_as_title = function (option, item) {
            var descrption = "";
            if (!item)
                descrption = self.rendering_description;
            else {
                descrption = item.description;
            }
            ko.applyBindingsToNode(option, {attr: {title: descrption}}, item);
        };

        self.get_camera_option_caption = function () {
            if (!self.camera_profile_guid) {
                return "Current Default Settings";
            } else {
                return "Original - " + self.camera_name;
            }
        };

        self.get_download_url = function(list_item){
            return '/plugin/octolapse/downloadFile?type=failed_rendering&name=' + list_item.id;
        }
    };

    Octolapse.FailedRenderingViewModel = function () {
        var self = this;
        self.failed_renderings_id = "octolapse-in-process-renderings";
        self.failed_renderings_size = ko.observable(0);
        self.failed_renderings_size_formatted = ko.pureComputed(function () {
            return Octolapse.toFileSizeString(self.failed_renderings_size())
        });
        self.render_profile_override_guid = ko.observable(null);
        self.camera_profile_override_guid = ko.observable(null);
        self.is_empty = ko.pureComputed(function(){
            return self.failed_renderings.list_items().length == 0
        });

        // Configure list helper
        self.to_list_item = function(item){
            var new_value = new Octolapse.FailedRenderingListItem(item);
            return new Octolapse.ListItemViewModel(
                self, new_value.id, null, null, false, new_value
            );
        };
        // load the file browser files
        self.is_admin = ko.observable(false);

        var list_view_options = {
            to_list_item: self.to_list_item,
            selection_enabled: true,
            select_all_enabled: true,
            sort_column: 'date',
            sort_direction: 'descending',
            top_left_pagination_template_id: 'octolapse-file-browser-delete-selected',
            no_items_template_id: 'octolapse-rendering-failed-no-items',
            columns: [
                new Octolapse.ListViewColumn('Print', 'print_file_name', {class: 'rendering-print-name', sortable:true}),
                new Octolapse.ListViewColumn('Status', 'print_end_state', {class: 'rendering-print-end-state', sortable:true}),
                new Octolapse.ListViewColumn('Size', 'file_size_text', {class: 'rendering-size', sortable:true, sort_column_name: "file_size"}),
                new Octolapse.ListViewColumn('Date', 'print_start_time_text', {class: 'rendering-date', sortable:true, sort_column_name: "print_start_time"}),
                new Octolapse.ListViewColumn('Camera', 'date_formatted', {class: 'rendering-camera-name', sortable:true, template_id: 'octolapse-rendering-failed-camera-profile'}),
                new Octolapse.ListViewColumn('Rendering', 'date_formatted', {class: 'rendering-name', sortable:true, template_id: 'octolapse-rendering-failed-render-profile'}),
                new Octolapse.ListViewColumn('Action', null, {class: 'rendering-action text-center', template_id:'octolapse-rendering-failed-action', visible_observable: self.is_admin})
            ]
        };

        self.failed_renderings = new Octolapse.ListViewModel(self, self.failed_renderings_id, list_view_options);

        self.initialize = function(){
            self.is_admin(Octolapse.Globals.is_admin());
            Octolapse.Globals.is_admin.subscribe(function(newValue){
                self.is_admin(newValue);
            });
        };

        self.get_key = function(job_guid, camera_guid){
            return job_guid + camera_guid;
        };

        self.update = function(values) {

            // Update the size if it has been provided
            if (values.renderings)
            {
                // Perform a complete refresh if necessary
                self.failed_renderings.set(values.renderings);
                self.failed_renderings_size(values.size ? values.size : 0);
            }
            else if (values.change_type && values.change_type)
            {
                // see if there is a change type
                var failed_rendering_change = values.rendering;
                var failed_rendering_change_type = values.change_type;

                if (failed_rendering_change_type === "added")
                {
                    self.failed_renderings.add(failed_rendering_change);
                    self.failed_renderings_size(self.failed_renderings_size() + failed_rendering_change["file_size"])
                }
                else if (failed_rendering_change_type === "removed")
                {
                    // Find the failed rendering and remove it
                    var removed = self.failed_renderings.remove(
                        self.get_key(failed_rendering_change.job_guid, failed_rendering_change.camera_guid)
                    );
                    if (removed) {
                        self.failed_renderings_size(
                            self.failed_renderings_size() - failed_rendering_change["file_size"]
                        )
                    }
                }
                else if (failed_rendering_change_type === "changed")
                {
                    var replaced = self.failed_renderings.replace(failed_rendering_change);
                    if (replaced) {
                        self.failed_renderings_size(
                            self.failed_renderings_size() -
                            replaced.values.file_size +
                            failed_rendering_change["file_size"])
                    }
                }
            }
            else
            {
                console.error("A 'Failed Rendering' update was received, but there was no data to process.");
            }

        };

        self.delete = function(item){
            var data = {
                'job_guid': item.value.job_guid,
                'camera_guid': item.value.camera_guid,
            };

            Octolapse.showConfirmDialog(
            "failed_rendering",
            "Delete Failed Rendering",
            "The selected rendering will be deleted.  Are you sure?",
            function(){
               $.ajax({
                    url: "./plugin/octolapse/deleteFailedRendering",
                    type: "POST",
                    data: JSON.stringify(data),
                    contentType: "application/json",
                    dataType: "json",
                    success: function (results) {
                        var options = {
                            title: 'Failed Rendering Deleted',
                            text: "The failed rendering was deleted.",
                            type: 'success',
                            hide: true,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "failed_rendering",["failed_rendering"]);
                        var removed = self.failed_renderings.remove(item);
                        if (removed) {
                            self.failed_renderings_size(self.failed_renderings_size() - rendering.file_size);
                        }
                    },
                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                        var options = {
                            title: 'Error Deleting Failed Rendering',
                            text: "Status: " + textStatus + ".  Error: " + errorThrown,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "failed_rendering",["failed_rendering"]);
                    }
                });
            });
        };

        self.delete_all = function(){
            Octolapse.showConfirmDialog(
            "failed_rendering",
            "Delete All Failed Renderings",
            "All failed renderings will be deleted.  Are you sure?",
            function(){
               $.ajax({
                    url: "./plugin/octolapse/deleteAllFailedRenderings",
                    type: "POST",
                    contentType: "application/json",
                    success: function (results) {
                        var options = {
                            title: 'Failed Renderings Deleted',
                            text: "All failed renderings were deleted.",
                            type: 'success',
                            hide: true,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "failed_rendering",["failed_rendering"]);
                        self.failed_renderings.clear([]);
                        self.failed_renderings_size(0);
                    },
                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                        var options = {
                            title: 'Error Deleting Failed Renderings',
                            text: "Status: " + textStatus + ".  Error: " + errorThrown,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "failed_rendering",["failed_rendering"]);
                    }
                });
            });
        };

        self.render_all = function(){
            var data = {
                'render_profile_override_guid': self.render_profile_override_guid() || null,
                'camera_profile_override_guid': self.camera_profile_override_guid() || null
            };
            Octolapse.showConfirmDialog(
            "failed_rendering",
            "Render All Failed Renderings",
            "All failed renderings will be rendered, which could take a long time.  Are you sure?",
            function(){
               $.ajax({
                    url: "./plugin/octolapse/renderAllFailedRenderings",
                    type: "POST",
                    data: JSON.stringify(data),
                    contentType: "application/json",
                    dataType: "json",
                    success: function (results) {
                        var options = {
                            title: 'Failed Renderings Deleted',
                            text: "All failed renderings were deleted.",
                            type: 'success',
                            hide: true,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "failed_rendering",["failed_rendering"]);
                        self.failed_renderings([]);
                        self.failed_renderings_size(0);
                    },
                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                        var options = {
                            title: 'Error Deleting Failed Renderings',
                            text: "Status: " + textStatus + ".  Error: " + errorThrown,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "failed_rendering",["failed_rendering"]);
                    }
                });
            });
        };

        self.render = function(rendering){
            var data = {
                'job_guid': rendering.value.job_guid,
                'camera_guid': rendering.value.camera_guid,
                'render_profile_override_guid': rendering.value.render_profile_override_guid() || null,
                'camera_profile_override_guid': rendering.value.camera_profile_override_guid() || null
            };
            $.ajax({
                    url: "./plugin/octolapse/renderFailedRendering",
                    type: "POST",
                    data: JSON.stringify(data),
                    contentType: "application/json",
                    dataType: "json",
                    success: function (results) {
                        var options = {
                            title: 'Failed Rendering Queued',
                            text: "The failed rendering was added to the rendering queue.",
                            type: 'success',
                            hide: true,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "failed_rendering",["failed_rendering"]);
                        var removed = self.failed_renderings.remove(rendering);
                        if (removed) {
                            self.failed_renderings_size(self.failed_renderings_size() - rendering.file_size);
                        }
                    },
                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                        var options = {
                            title: 'Error Deleting Failed Rendering',
                            text: "Status: " + textStatus + ".  Error: " + errorThrown,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "failed_rendering",["failed_rendering"]);
                    }
                });
        };
    };
});

