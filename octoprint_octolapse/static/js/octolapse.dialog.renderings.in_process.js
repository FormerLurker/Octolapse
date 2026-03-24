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
    Octolapse.RenderProgressTypes = {
        "pending": "Pending",
        "preparing": "Preparing",
        "pre_render_script": "Script - Before",
        "adding_overlays": "Adding Overlays",
        "rename_images": "Renaming Images",
        'pre_post_roll': "Pre/Post Roll",
        "rendering": "Rendering",
        "archiving": "Archiving",
        "post_render_script": "Script - After",
        "cleanup": "Cleaning Up"
    };

    Octolapse.InProcessRenderingListItem = function (values) {
        var self = this;
        self.id = values.job_guid + values.camera_guid;
        self.job_guid = values.job_guid;
        self.print_start_time = values.print_start_time;
        self.print_start_time_text = Octolapse.toLocalDateString(values.print_start_time);
        self.print_end_time = values.print_end_time;
        self.print_end_time_text = Octolapse.toLocalDateString(values.print_end_time);
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
        self.progress = ko.observable(values.progress);
        self.progress_percent = ko.observable(null);
        self.sort_order = self.progress === "pending" ? 0 : 1;

        self.progress_text = ko.pureComputed(function(){
            var progress = self.progress();
            if (progress in Octolapse.RenderProgressTypes) {
                if (self.progress_percent() !== null) {
                    return Octolapse.RenderProgressTypes[progress] + " " + self.progress_percent().toFixed(1).toString() + "%";
                }
                return Octolapse.RenderProgressTypes[progress];
            }
            return progress;
        });

    };

   Octolapse.OctolapseDialogRenderingInProcess = function () {
        var self = this;
        self.dialog_id = "octolapse_dialog_rendering_in_process";
        self.dialog_options = {
            title: "Renderings - In Progress",
            validation_enabled: false,
            help_enabled: true,
            help_title: 'Renderings - In process',
            help_link: 'dialog.renderings.in_process.md'
        };
        self.template_id= "octolapse-rendering-in-process-template";

        self.dialog = new Octolapse.OctolapseDialog(self.dialog_id, self.template_id, self.dialog_options);

        self.on_after_binding = function(){
            self.dialog.on_after_binding();
            self.initialize();
        };

        self.load = function() {
            if (!Octolapse.Globals.is_admin()) {
                self.in_process_renderings.set([]);
                return;
            }
            $.ajax({
                url: "./plugin/octolapse/loadInProcessRenderings",
                type: "POST",
                contentType: "application/json",
                success: function (results) {
                    self.update(results);
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    self.in_process_renderings.set([]);
                    var options = {
                        title: 'Error Loading In Progress Renderings',
                        text: "Status: " + textStatus + ".  Error: " + errorThrown,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse"
                    };
                    Octolapse.displayPopupForKey(options, "file_load", ["file_load"]);
                }
            });
        };

        self.open = function(open_to_tab){
            self.dialog.show();
        };
        // List Items
        self.in_process_renderings_id = "octolapse-in-process-renderings";
        self.in_process_renderings_size = ko.observable(0);
        self.in_process_renderings_size_formatted = ko.pureComputed(function(){
            return Octolapse.toFileSizeString(self.in_process_renderings_size());
        });
        self.is_empty = ko.pureComputed(function(){
            return self.in_process_renderings.list_items().length == 0;
        });

        // Configure list helper
        self.to_list_item = function(item){
            var new_value = new Octolapse.InProcessRenderingListItem(item);
            return new Octolapse.ListItemViewModel(
                self, new_value.id, null, null, false, new_value
            );
        };
        // load the file browser files
        self.is_admin = ko.observable(false);

        var list_view_options = {
            to_list_item: self.to_list_item,
            sortable: false,
            sort_column: 'print_end_time',
            sort_direction: 'descending',
            no_items_template_id: 'octolapse-rendering-in-process-no-items',
            top_right_pagination_template_id: 'octolapse-rendering-in-process-file-size',
            sort_column: 'progress',
            pagination_row_auto_hide: false,
            columns: [
                new Octolapse.ListViewColumn('Print', 'print_file_name', {class: 'rendering-print-name', sortable:false}),
                new Octolapse.ListViewColumn('Status', 'print_end_state', {class: 'rendering-print-end-state', sortable:false}),
                new Octolapse.ListViewColumn('Size', 'file_size_text', {class: 'rendering-size', sortable:false, sort_column_id: "file_size"}),
                new Octolapse.ListViewColumn('Date', 'print_start_time_text', {class: 'rendering-date', sortable:false, sort_column_id: "print_start_time"}),
                new Octolapse.ListViewColumn('Camera', 'camera_name', {class: 'rendering-camera-name', sortable:false}),
                new Octolapse.ListViewColumn('Rendering', 'rendering_name', {class: 'rendering-name', sortable:false}),
                new Octolapse.ListViewColumn('Progress', 'progress', {class: 'rendering-progress text-center', sortable: false, sort_column_id: 'sort_order', template_id: 'octolapse-rendering-progress'})
            ]
        };

        self.in_process_renderings = new Octolapse.ListViewModel(self, self.in_process_renderings_id, list_view_options);

        self.count = ko.pureComputed(function(){
            return self.in_process_renderings.list_items().length;
        });

        self.initialize = function(){
            self.is_admin(Octolapse.Globals.is_admin());
            Octolapse.Globals.is_admin.subscribe(function(newValue){
                self.is_admin(newValue);
            });
        };

        self.get_key = function(job_guid, camera_guid){
            return job_guid + camera_guid;
        };

        self.update = function(values){
            if (values.in_process){
                var in_process =  values.in_process;
                if (in_process.renderings) {
                    // Update all renderings if provided
                    self.in_process_renderings.set(in_process.renderings);
                    self.in_process_renderings_size(in_process.size ? in_process.size : 0);
                }
                else if (in_process.change_type && in_process.rendering) {
                    var in_process_rendering_change = in_process.rendering;
                    var in_process_rendering_change_type = in_process.change_type;
                    if (in_process_rendering_change_type === "added") {
                        self.in_process_renderings.add(in_process_rendering_change);
                        self.in_process_renderings_size(self.in_process_renderings_size() + in_process_rendering_change["file_size"]);
                    } else if (in_process_rendering_change_type === "removed") {
                        // Find the in_process rendering and remove it
                        var removed = self.in_process_renderings.remove(
                            self.get_key(in_process_rendering_change.job_guid, in_process_rendering_change.camera_guid)
                        );
                        if (removed) {
                            self.in_process_renderings_size(self.in_process_renderings_size() - in_process_rendering_change["file_size"]);
                        }
                    } else if (in_process_rendering_change_type === "changed") {
                        // Find the in_process rendering and remove it
                        var replaced = self.in_process_renderings.replace(in_process_rendering_change);
                        if (replaced) {
                            self.in_process_renderings_size(
                                self.in_process_renderings_size() - replaced.value.file_size + in_process_rendering_change["file_size"]);
                        }
                    } else if (in_process_rendering_change_type === "progress") {
                        var progress_percent = in_process.progress_percent;
                        var progress_rendering = self.in_process_renderings.get(
                            self.get_key(in_process_rendering_change.job_guid, in_process_rendering_change.camera_guid)
                        );

                        if (progress_rendering) {
                            progress_rendering.value.progress(in_process_rendering_change.progress);
                            progress_rendering.value.progress_percent(progress_percent);
                        }

                    }
                }
                else
                {
                    console.error("A 'Failed Rendering' update was received, but there was no data to process.");
                }
            }
        };

    };

});
