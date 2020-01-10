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
   Octolapse.OctolapseRenderingDialog = function () {
        var self = this;


        self.dialog_id = "octolapse_dialog_rendering";

        self.in_process_tab_button_id = "octolapse_rendering_dialog_in_process_button";
        self.failed_tab_button_id = "octolapse_rendering_dialog_failed_button";

        self.dialog_options = {
            title: "Rendering Information",
            validation_enabled: false
        };
        self.template_id= "octolapse-rendering-dialog-template";

        self.failed = new Octolapse.FailedRenderingViewModel();
        self.in_process = new Octolapse.InProcessRenderingViewModel();

        self.dialog = new Octolapse.OctolapseDialog(self.dialog_id, self.template_id, self.dialog_options);

        self.on_after_binding = function(){
            self.dialog.on_after_binding();
            self.failed.initialize();
            self.in_process.initialize();
        };

        self.load = function() {
            self.load_failed();
            self.load_in_process();
        };

        self.load_failed = function() {
            if (!Octolapse.Globals.is_admin()) {
                self.failed.set([]);
                return;
            }
            $.ajax({
                url: "./plugin/octolapse/loadFailedRenderings",
                type: "POST",
                contentType: "application/json",
                success: function (results) {
                    self.failed.update(results.failed);
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    self.failed.set([]);
                    var options = {
                        title: 'Error Loading Failed Renderings',
                        text: "Status: " + textStatus + ".  Error: " + errorThrown,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse"
                    };
                    Octolapse.displayPopupForKey(options, "file_load", ["file_load"]);
                }
            });
        };

        self.load_in_process = function() {
            if (!Octolapse.Globals.is_admin()) {
                self.in_process.set([]);
                return;
            }
            $.ajax({
                url: "./plugin/octolapse/loadInProcessRenderings",
                type: "POST",
                contentType: "application/json",
                success: function (results) {
                    self.in_process.update(results.in_process);
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    self.in_process.set([]);
                    var options = {
                        title: 'Error Loading In Process Renderings',
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
            var button_id = null;
            if (open_to_tab == "in-process")
            {
                button_id = self.in_process_tab_button_id;
            }
            else if (open_to_tab=="failed")
            {
                button_id = self.failed_tab_button_id;
            }
            else if (self.failed.is_empty() && !self.in_process.is_empty())
            {
                button_id = self.in_process_tab_button_id;
            }
            else if (!self.failed.is_empty() > 0 && self.in_process.is_empty)
            {
                button_id = self.failed_tab_button_id;
            }
            if (button_id)
            {
                $("#"+self.dialog_id).find("#"+button_id).click();
            }
        };

        self.update = function(values){
            if (values.unfinished_renderings)
            {
                var unfinished_renderings = values.unfinished_renderings;
                if (unfinished_renderings.failed)
                    self.failed.update(unfinished_renderings.failed);
                if (unfinished_renderings.in_process)
                    self.in_process.update(unfinished_renderings.in_process);
            }

        };

    };

});
