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
    Octolapse.OctolapseTimelapseFilesDialog = function () {
        var self = this;

        self.dialog_id = "octolapse_timelapse_files_dialog";
        self.open_to_tab = null;

        self.timelapse_tab_button_id = "octolapse_timelapse_videos_tab_button";
        self.snapshot_archive_tab_button_id = "octolapse_snapshot_archive_tab_button";
        self.dialog_options = {
            title: "Timelapse Files",
        };
        self.template_id= "octolapse-timelapse-files-dialog-template";
        self.dialog = new Octolapse.OctolapseDialog(self.dialog_id, self.template_id, self.dialog_options);

        self.archive_browser = new Octolapse.OctolapseFileBrowser(
            'octolapse-archive-browser',
            self,
            {
                file_type: 'snapshot_archive',
                resize: self.dialog.resize,
                allow_delete: true,
                allow_delete_all: true,
                custom_actions_template_id: 'octolapse-snapshot-archive-custom-actions',
                actions_class: 'file-browser-snapshot-archive-action'
            }
        );

        self.timelapse_browser = new Octolapse.OctolapseFileBrowser(
            'octolapse-timelapse-browser',
            self,
            {
                file_type: 'timelapse_octolapse',
                resize: self.dialog.resize,
                allow_delete: true,
                allow_delete_all: true
            }
        );

        self.load = function(){
            self.timelapse_browser.load();
            self.archive_browser.load();
        };

        self.files_changed = function(file_info, action){
            if (file_info.type === "snapshot_archive")
            {
                self.archive_browser.files_changed(file_info, action);
            }
            else if (file_info.type === "timelapse_octolapse" || file_info.type === "timelapse_octoprint")
            {
                self.timelapse_browser.files_changed(file_info, action)
            }
        };

        self.on_after_binding = function(){
            self.dialog.on_after_binding();
            self.archive_browser.initialize();
            self.timelapse_browser.initialize();
        };

        self.open = function(open_to_tab){
            self.dialog.show();
            var button_id = null;
            if (open_to_tab==="timelapse")
            {
                button_id = self.timelapse_tab_button_id;
            }
            else if (open_to_tab==="snapshot_archive")
            {
                button_id = self.snapshot_archive_tab_button_id;
            }
            else
            {
                console.error("An unknown timelapse_files tab was requested for opening.");
                return;
            }
            if (button_id)
            {
                $("#"+self.dialog_id).find("#"+button_id).click();
            }

        };

        self.add_archive_to_unfinished_rendering = function(item) {
            var data = {
                'archive_name': item.id
            };
            $.ajax({
                url: "./plugin/octolapse/addArchiveToUnfinishedRenderings",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (results) {
                    if (results.success) {
                        var options = {
                            title: 'Archive Added',
                            text: "The archive was added to the unfinished rendering list.  You can render the archive by clicking the unfinished renderings button.",
                            type: 'success',
                            hide: true,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "add-archive-to-unfinished-renderings", ["add-archive-to-unfinished-renderings"]);
                    }
                    else {
                        var options = {
                            title: 'Error Adding Archive',
                            text: results.error,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "add-archive-to-unfinished-renderings",["add-archive-to-unfinished-renderings"]);
                    }
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    var options = {
                        title: 'Error Adding Archive',
                        text: "Status: " + textStatus + ".  Error: " + errorThrown,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse"
                    };
                    Octolapse.displayPopupForKey(options, "add-archive-to-unfinished-renderings",["add-archive-to-unfinished-renderings"]);
                }
            });
        };

    };
});
