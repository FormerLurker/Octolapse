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
    Octolapse.FailedRenderingListItem = function (values) {
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

        self.get_download_url = function(){
            return './plugin/octolapse/downloadFile?type=failed_rendering&job_guid=' + self.job_guid
                + '&camera_guid=' + self.camera_guid;
        };
    };

   Octolapse.OctolapseDialogRenderingUnfinished = function () {
        var self = this;
        self.dialog_id = "octolapse_dialog_rendering_unfinished";

        self.dialog_options = {
            title: "Unfinished Renderings",
            validation_enabled: false,
            help_enabled: true,
            help_title: 'Unfinished Renderings',
            help_link: 'dialog.renderings.unfinished.md'
        };
        self.template_id= "octolapse-rendering-failed-template";

        self.dialog = new Octolapse.OctolapseDialog(self.dialog_id, self.template_id, self.dialog_options);

        self.on_after_binding = function(){
            self.dialog.on_after_binding();
            self.initialize();
        };

        self.load = function() {
            if (!Octolapse.Globals.is_admin()) {
                self.failed_renderings.set([]);
                return;
            }
            $.ajax({
                url: "./plugin/octolapse/loadFailedRenderings",
                type: "POST",
                contentType: "application/json",
                success: function (results) {
                    self.update(results);
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    self.failed_renderings.set([]);
                    var options = {
                        title: 'Error Loading Unfinished Renderings',
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

        self.update = function(values){
            if (values.failed)
            {
                // Update the size if it has been provided
                var failed_renderings = values.failed;
                if (failed_renderings.renderings)
                {
                    // Perform a complete refresh if necessary
                    self.failed_renderings.set(failed_renderings.renderings);
                    self.failed_renderings_size(failed_renderings.size ? failed_renderings.size : 0);
                }
                else if (failed_renderings.change_type && failed_renderings.rendering)
                {
                    // see if there is a change type
                    var failed_rendering_change = failed_renderings.rendering;
                    var failed_rendering_change_type = failed_renderings.change_type;

                    if (failed_rendering_change_type === "added")
                    {
                        self.failed_renderings.add(failed_rendering_change);
                        self.failed_renderings_size(self.failed_renderings_size() + failed_rendering_change["file_size"]);
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
                            );
                        }
                    }
                    else if (failed_rendering_change_type === "changed")
                    {
                        var replaced = self.failed_renderings.replace(failed_rendering_change);
                        if (replaced) {
                            self.failed_renderings_size(
                                self.failed_renderings_size() -
                                replaced.failed_renderings.file_size +
                                failed_rendering_change["file_size"]);
                        }
                    }
                }
                else
                {
                    console.error("An 'Unfinished Rendering' update was received, but there was no data to process.");
                }
            }
        };

        self.failed_renderings_id = "octolapse-unfinished-renderings";
        self.failed_renderings_size = ko.observable(0);
        self.failed_renderings_size_formatted = ko.pureComputed(function () {
            return Octolapse.toFileSizeString(self.failed_renderings_size());
        });
        self.render_profile_override_guid = ko.observable(null);
        self.camera_profile_override_guid = ko.observable(null);
        self.is_empty = ko.pureComputed(function(){
            return self.failed_renderings.list_items().length === 0;
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
            selection_enabled: self.is_admin,
            select_all_enabled: self.is_admin,
            sort_column: 'print_start_time_text',
            sort_direction: 'descending',
            top_left_pagination_template_id: 'octolapse-rendering-failed-selected-actions',
            top_right_pagination_template_id: 'octolapse-rendering-failed-file-size',
            pagination_row_auto_hide: false,
            no_items_template_id: 'octolapse-rendering-failed-no-items',
            select_header_template_id: 'octolapse-list-select-header-dropdown-template',
            selection_class: 'list-item-selection-dropdown',
            selection_header_class: 'list-item-selection-header-dropdown',
            pagination_style: 'narrow',
            columns: [
                new Octolapse.ListViewColumn('Print', 'print_file_name', {class: 'rendering-print-name', sortable:true}),
                new Octolapse.ListViewColumn('Status', 'print_end_state', {class: 'rendering-print-end-state', sortable:true}),
                new Octolapse.ListViewColumn('Size', 'file_size_text', {class: 'rendering-size', sortable:true, sort_column_id: "file_size"}),
                new Octolapse.ListViewColumn('Date', 'print_start_time_text', {class: 'rendering-date', sortable:true, sort_column_id: "print_start_time"}),
                new Octolapse.ListViewColumn('Camera', 'camera_name', {class: 'rendering-camera-name', sortable:true, template_id: 'octolapse-rendering-failed-camera-profile'}),
                new Octolapse.ListViewColumn('Rendering', 'rendering_name', {class: 'rendering-name', sortable:true, template_id: 'octolapse-rendering-failed-render-profile'}),
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

        self.count = ko.pureComputed(function(){
            return self.failed_renderings.list_items().length;
        });

        self._delete = function(item, on_success, on_error){
            if (item.disabled())
                return;
            item.disabled(true);
            var data = {
                'job_guid': item.value.job_guid,
                'camera_guid': item.value.camera_guid,
            };
            $.ajax({
                url: "./plugin/octolapse/deleteFailedRendering",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (results) {
                    var removed = self.failed_renderings.remove(item);
                    if (removed) {
                        self.failed_renderings_size(self.failed_renderings_size() - removed.file_size);
                    }
                    if (on_success){
                        on_success(item.id);
                    }
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    item.disabled(false);
                    if (on_error) {
                        on_error(XMLHttpRequest, textStatus, errorThrown);
                    }
                }
            });
        };

        self.delete = function(item){
            Octolapse.showConfirmDialog(
            "failed_rendering",
            "Delete Failed Rendering",
            "The selected rendering will be deleted.  Are you sure?",
            function(){
                self._delete(
                    item,
                    function(XMLHttpRequest, textStatus, errorThrown) {
                        var options = {
                            title: 'Unfinished Rendering Deleted',
                            text: "The unfinished rendering was deleted successfully.",
                            type: 'success',
                            hide: true,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "file-delete",["file-delete"]);
                    }
                );
            });
        };

        self._delete_selected = function(){
            var selected_files = self.failed_renderings.selected();

            if (selected_files.length == 0)
                return;
            var num_errors = 0;
            var num_deleted = 0;
            var current_index = 0;
            var delete_success = function(id){
                num_deleted += 1;
                delete_end();
            };
            var delete_failed = function(XMLHttpRequest, textStatus, errorThrown){
                num_errors += 1;
                delete_end();
            };

            var delete_end = function(){
                current_index += 1;
                if (current_index < selected_files.length)
                {
                    delete_item();
                }
                else
                {
                    var options = null;
                    if (num_deleted > 0 && num_errors == 0)
                    {
                        var options = {
                            title: 'Unfinished Renderings Deleted',
                            text: "All selected unfinished renderings were deleted.",
                            type: 'success',
                            hide: true,
                            addclass: "octolapse"
                        };
                    }
                    else if (num_deleted == 0)
                    {
                        var options = {
                            title: 'Error Deleting Unfinished Renderings',
                            text: "Octolapse could not delete the selected unfinished renderings.",
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                    }
                    else
                    {
                        var options = {
                            title: 'Some Unfinished Renderings Not Deleted',
                            text: "Octolapse could not delete all of the selected unfinished renderings. " +
                                num_deleted.toString() + " of " + num_errors.toString() + " files were deleted.",
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                    }

                    Octolapse.displayPopupForKey(options, "file-delete",["file-delete"]);
                }
            };

            var delete_item = function() {
                var item = selected_files[current_index];
                self._delete(item, delete_success, delete_failed);
            };

            delete_item();
        };

        self.delete_selected = function(){
            Octolapse.showConfirmDialog(
            "failed_rendering",
            "Delete Selected Unfinished Renderings",
            "All selected unfinished renderings will be deleted.  Are you sure?",
            function(){
               self._delete_selected();
            });
        };

        self._render = function(item, on_success, on_error){
            if (item.disabled())
                return;
            item.disabled(true);
            var data = {
                'id': item.id,
                'job_guid': item.value.job_guid,
                'camera_guid': item.value.camera_guid,
                'render_profile_override_guid': item.value.render_profile_override_guid() || null,
                'camera_profile_override_guid': item.value.camera_profile_override_guid() || null
            };
            $.ajax({
                url: "./plugin/octolapse/renderFailedRendering",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (results) {
                    var removed = self.failed_renderings.remove(item.id);
                    if (removed) {
                        self.failed_renderings_size(self.failed_renderings_size() - item.value.file_size);
                    }
                    if (on_success){
                        on_success(item.id);
                    }
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    item.disabled(false);
                    if (on_error) {
                        on_error(XMLHttpRequest, textStatus, errorThrown);
                    }
                }
            });

        };

        self.render = function(item){
            self._render(
                item,
                function(){
                    var options = {
                        title: 'Added to Rendering Queue',
                        text: "An unfinished rendering rendering was added to the rendering queue.",
                        type: 'success',
                        hide: true,
                        addclass: "octolapse"
                    };
                    Octolapse.displayPopupForKey(options, "render_message",["render_message"]);
                },
                function(){
                    var options = {
                        title: 'Error Deleting Unfinished Rendering',
                        text: "Status: " + textStatus + ".  Error: " + errorThrown,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse"
                    };
                    Octolapse.displayPopupForKey(options, "render_message",["render_message"]);
                });

        };

        self._render_selected = function(){
            var selected_unfinished_renderings = self.failed_renderings.selected();

            if (selected_unfinished_renderings.length == 0)
                return;
            var num_errors = 0;
            var num_rendered = 0;
            var current_index = 0;
            var render_success = function(id){
                num_rendered += 1;
                render_end();
            };
            var render_failed = function(XMLHttpRequest, textStatus, errorThrown){
                num_errors += 1;
                render_end();
            };

            var render_end = function(){
                current_index += 1;
                if (current_index < selected_unfinished_renderings.length)
                {
                    render_item();
                }
                else
                {
                    var options = null;
                    if (num_rendered > 0 && num_errors == 0)
                    {
                        var options = {
                            title: 'Unfinished Renderings Queued',
                            text: "All selected items were queued for rendering.",
                            type: 'success',
                            hide: true,
                            addclass: "octolapse"
                        };
                    }
                    else if (num_rendered == 0)
                    {
                        var options = {
                            title: 'Error Queueing Unfinished Renderings',
                            text: "Octolapse could not queue the selected unfinished renderings.",
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                    }
                    else
                    {
                        var options = {
                            title: 'Some Unfinished Renderings Not Queued',
                            text: "Octolapse could not queue all of the selected items for renderings. " +
                                num_rendered.toString() + " of " + num_errors.toString() + " files were queued.",
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                    }

                    Octolapse.displayPopupForKey(options, "render_message",["render_message"]);
                }
            };

            var render_item = function() {
                var item = selected_unfinished_renderings[current_index];
                self._render(item, render_success, render_failed);
            };

            render_item();
        };

        self.render_selected = function(){
            Octolapse.showConfirmDialog(
            "failed_rendering",
            "Render All Selected",
            "All selected items will be rendered, which could take a long time.  Are you sure?",
            function(){
                self._render_selected();
            });
        };

        self._downloading_icon_class = "fa fa-spinner fa-spin disabled";
        self._downloding_icon_error_class = "fa fa-exclamation-triangle text-error";
        self._download_icon_class = "fa fa-lg fa-download";
        self._download_icon_title = "Click to download.";
        self._downloading_icon_title = "Downloading your file, please wait.";
        self._download_error_icon_title = "An error occurred while downloading your file.";
        self.download = function(data, e)
        {
            // Get the url
            var url = data.item.value.get_download_url();
            // Get the icon that was clicked
            var $icon = $(e.target);
            // If the icon is disabled, exit since it is already downloading.
            if ($icon.hasClass('disabled'))
                return;
            var icon_classes = self._download_icon_class;
            var icon_title = self._download_icon_title;
            var options = {
                on_start: function(event, url){
                    $icon.attr('class', self._downloading_icon_class);
                    $icon.attr('title', self._downloading_icon_title);
                },
                on_end: function(e, url){
                    if ($icon)
                    {
                        $icon.attr('class', icon_classes);
                        $icon.attr('title', icon_title);
                    }
                },
                on_error: function(message)
                {
                    icon_classes = self._downloding_icon_error_class;
                    icon_title = self._download_error_icon_title + '  Error: ' + message;
                }
            };
            Octolapse.download(url, e, options);
        };
    };

});
