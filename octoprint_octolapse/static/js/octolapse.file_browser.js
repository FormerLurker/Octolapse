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
    Octolapse.FileViewModel = function(values) {
        var self = this;
        self.extension = values.extension;
        self.size = values.size;
        self.size_formatted = Octolapse.toFileSizeString(values.size, 1);
        self.date = values.date;
        self.date_formatted = Octolapse.toLocalDateTimeString(values.date);
        self.get_download_url = function(list_item){
            var parent = list_item.data.parent;
            return './plugin/octolapse/downloadFile?type=' + parent.file_type + '&name=' + list_item.id;
        };
    };

    Octolapse.OctolapseFileBrowser = function (id, parent, options) {
        var self = this;
        self.data = ko.observable();
        self.data.parent = parent;
        self.file_browser_id = id;
        self.options = options;
        self.dialog_id = "octolapse_file_browsing_dialog";
        self.file_type = options.file_type;
        self.no_files_text = options.no_files_text || "There are no files available.";
        self.custom_actions_template_id = options.custom_actions_template_id || null;
        self.files_not_loaded_template_id = options.files_not_loaded_template_id || "octolapse-file-browser-not-loaded";
        self.actions_class = options.actions_class || "file-browser-action";
        self.has_loaded = ko.observable(false);
        self.total_file_size = ko.observable(0);
        self.total_file_size_text = ko.pureComputed(function(){
            return Octolapse.toFileSizeString(self.total_file_size(),1);
        });
        self.to_list_item = function(item){
            return new Octolapse.ListItemViewModel(
                self, encodeURI(item.name), item.name, item.name, false, new Octolapse.FileViewModel(item)
            );
        };
        // load the file browser files
        self.is_admin = ko.observable(false);
        self.pagination_row_auto_hide = ko.observable(false);

        var list_view_options = {
            to_list_item: self.to_list_item,
            selection_enabled: self.is_admin,
            select_all_enabled: self.is_admin,
            sort_column: 'date_formatted',
            sort_direction: 'descending',
            pagination_row_auto_hide: self.pagination_row_auto_hide,
            top_left_pagination_template_id: 'octolapse-file-browser-delete-selected',
            top_right_pagination_template_id: 'octolapse-file-browser-file-size',
            select_header_template_id: 'octolapse-list-select-header-dropdown-template',
            selection_class: 'list-item-selection-dropdown',
            selection_header_class: 'list-item-selection-header-dropdown',
            no_items_template_id: 'octolapse-file-browser-no-items',
            custom_row_template_id: 'octolapse-file-browser-custom-row',
            columns: [
                new Octolapse.ListViewColumn('Name', 'name', {class: 'file-browser-name', sortable:true}),
                new Octolapse.ListViewColumn('Size', 'size_formatted', {class: 'file-browser-size', sortable:true, sort_column_id: "size"}),
                new Octolapse.ListViewColumn('Date', 'date_formatted', {class: 'file-browser-date', sortable:true, sort_column_id: "date"}),
                new Octolapse.ListViewColumn('Action', null, {class: self.actions_class, template_id:'octolapse-file-browser-action', visible_observable: self.is_admin})
            ]
        };

        self.files = new Octolapse.ListViewModel(self, self.file_browser_id, list_view_options);

        self.initialize = function(){
            self.is_admin(Octolapse.Globals.is_admin);
            Octolapse.Globals.is_admin.subscribe(function(newValue){
                self.is_admin(newValue);
                self.pagination_row_auto_hide(!newValue);
            });
        };

        self.load = function(){
            if (!Octolapse.Globals.is_admin()) {
                self.files.set([]);
            }
            var data = {
                'type': self.file_type
            };
            $.ajax({
                url: "./plugin/octolapse/getFiles",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (results) {
                    // Build the list items
                    self.has_loaded(true);
                    var total_size = 0;
                    self.files.set(results.files, function(added_item){
                        total_size += added_item.value.size;
                    });
                    self.total_file_size(total_size);
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    var options = {
                        title: 'Error Loading Files',
                        text: "Status: " + textStatus + ".  Error: " + errorThrown,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse"
                    };
                    Octolapse.displayPopupForKey(options, "file_load",["file_load"]);
                }
            });
        };

        self.files_changed = function(file_info, action){
            if (action === "removed")
            {
                self.files.remove(encodeURI(file_info.name));
                self.total_file_size(self.total_file_size() - file_info.size);
            }
            else if (action === "added")
            {
                self.files.add(file_info);
                self.total_file_size(self.total_file_size() + file_info.size);
            }
            else if (action === "reload")
            {
                self.load();
            }
        };

        self._delete_file = function(file, on_success, on_error){
            if (file.disabled())
            {
                if (on_error) {
                    on_error(XMLHttpRequest, textStatus, errorThrown);
                }
            }
            file.disabled(true);
            var data = {
                'type': self.file_type,
                'id': file.id,
                'size': file.value.size,
                'client_id': Octolapse.Globals.client_id
            };
            $.ajax({
                url: "./plugin/octolapse/deleteFile",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (results) {
                    self.files.remove(file.id);
                    self.total_file_size(self.total_file_size() - file.value.size);
                    if (on_success){
                        on_success(file.id);
                    }
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    if (on_error) {
                        on_error(XMLHttpRequest, textStatus, errorThrown);
                    }
                    file.disabled(false);
                }
            });
        };

        self.delete_file = function(file){
          var message = "Are you sure you want to permanently delete this file?";
            Octolapse.showConfirmDialog(
                "file-delete",
                "Delete Files",
                message,
                function(){
                    self._delete_file(
                        file,
                        null,
                        function() {
                            var options = {
                                title: 'Error Deleting File',
                                text: "Octolapse could not delete the file.",
                                type: 'error',
                                hide: false,
                                addclass: "octolapse"
                            };
                            Octolapse.displayPopupForKey(options, "file-delete", ["file-delete"]);
                        });
                });
        };

        self._delete_selected = function(){
            var selected_files = self.files.selected();
            if (selected_files.length == 0)
                return;
            var num_errors = 0;
            var num_deleted = 0;
            var current_index = 0;
            var delete_success = function(id){
                num_deleted += 1;
                delete_file_end();
            };
            var delete_failed = function(XMLHttpRequest, textStatus, errorThrown){
                num_errors += 1;
                delete_file_end();
            };
            var delete_file_end = function(){
                current_index += 1;
                if (current_index < selected_files.length)
                {
                    delete_file();
                }
                else
                {
                    var options = null;
                    if (num_deleted === 1 && num_errors === 0)
                    {
                        return;
                    }
                    if (num_deleted > 1 && num_errors == 0)
                    {
                        var options = {
                            title: 'Files Deleted',
                            text: "All selected files were deleted.",
                            type: 'success',
                            hide: true,
                            addclass: "octolapse"
                        };
                    }
                    else if (num_deleted == 0)
                    {
                        var options = {
                            title: 'Error Deleting File',
                            text: "Octolapse could not delete the selected files.",
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                    }
                    else
                    {
                        var options = {
                            title: 'Some Files Not Deleted',
                            text: "Octolapse could not delete all of the selected files. " +
                                num_deleted.toString() + " of " + num_errors.toString() + " files were deleted.",
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                    }

                    Octolapse.displayPopupForKey(options, "file-delete",["file-delete"]);
                }
            };

            var delete_file = function() {
                self._delete_file(selected_files[current_index], delete_success, delete_failed);
            };

            delete_file();
        };

        self.delete_selected = function(){
            var message = "This will permanently delete " + self.files.selected_count() + " files.  Are you sure?";
            Octolapse.showConfirmDialog(
                "file-delete",
                "Delete Selected Files",
                message,
                function(){
                    self._delete_selected();
                }
            );
        };

        self._downloading_icon_class = "fa fa-spinner fa-spin disabled";
        self._downloding_icon_error_class = "fa fa-exclamation-triangle text-error";
        self._download_icon_class = "fa fa-lg fa-download";
        self._download_icon_title = "Click to download.";
        self._downloading_icon_title = "Downloading your file, please wait.";
        self._download_error_icon_title = "An error occurred while downloading your file.  Click to retry.";
        self.download = function(data, e)
        {
            // Get the url
            var url = data.value.get_download_url(data);
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
