/*
##################################################################################
# Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
# Copyright (C) 2019  Brad Hochgesang
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
    Octolapse.OctolapseInProcessInProcessRenderingViewModel = function(values)
    {
        var self=  this;
        self.job_guid = values.job_guid;
        self.print_start_time = Octolapse.toLocalDateString(values.print_start_time);
        self.print_end_time = Octolapse.toLocalDateString(values.print_end_time);
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
        self.file_size = ko.observable(values.file_size);
        self.file_size_formatted = ko.pureComputed(function(){
            return Octolapse.toFileSizeString(self.file_size())
        });
        self.progress = ko.observable(values.progress);
    };
    Octolapse.OctolapseUnfinishedRenderingViewModel = function(values) {
        var self= this;
        self.job_guid = values.job_guid;
        self.print_start_time = Octolapse.toLocalDateString(values.print_start_time);
        self.print_end_time = Octolapse.toLocalDateString(values.print_end_time);
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
        self.file_size = ko.observable(values.file_size);
        self.file_size_formatted = ko.pureComputed(function(){
            return Octolapse.toFileSizeString(self.file_size())
        });
        self.render_profile_override_guid = ko.observable(null);
        self.camera_profile_override_guid = ko.observable(null);

        self.getRenderingOptionCaption = function(){
            if (!self.rendering_guid)
            {
                return "Current Profile";
            }
            else
            {
                return "Original - " + self.rendering_name;
            }
        };

        self.setRenderingProfileOptionDescriptionAsTitle = function(option, item) {
            var descrption = "";
            if (!item)
                descrption = self.rendering_description;
            else
            {
                descrption = item.description;
            }
            ko.applyBindingsToNode(option, {attr: {title: descrption}}, item);
        };

        self.getCameraOptionCaption = function(){
            if (!self.camera_profile_guid)
            {
                return "Current Default Settings";
            }
            else
            {
                return "Original - " + self.camera_name;
            }
        };

    };

    Octolapse.OctolapseRenderingDialog = function () {
        var self = this;
        self.unfinished_renderings = ko.observableArray([]);
        self.unfinished_renderings_size = ko.observable(0);
        self.unfinished_renderings_size_formatted = ko.pureComputed(function(){
            return Octolapse.toFileSizeString(self.unfinished_renderings_size())
        });
        self.in_process_renderings = ko.observableArray([]);
        self.in_process_renderings_size = ko.observable(0);
        self.in_process_renderings_size_formatted = ko.pureComputed(function(){
            return Octolapse.toFileSizeString(self.in_process_renderings_size());
        });
        self.render_profile_override_guid = ko.observable(null);
        self.camera_profile_override_guid = ko.observable(null);
        self.dialog_id = "octolapse_rendering_dialog";
        self.open_to_tab = null;

        self.in_process_tab_button_id = "octolapse_rendering_dialog_in_process_button";
        self.unfinished_tab_button_id = "octolapse_rendering_dialog_unfinished_button";

        self.dialog_options = {
            title: "Incomplete Rendering",
        };
        self.template_id= "octolapse-rendering-dialog-template";
        self.dialog = new Octolapse.OctolapseDialog(self.dialog_id, self.template_id, self.dialog_options);

        self.has_unfinished_renderings = ko.pureComputed(function(){
            return self.unfinished_renderings().length > 0
        });
        self.has_in_process_renderings = ko.pureComputed(function(){
            return self.in_process_renderings().length > 0
        });

        self.on_after_binding = function(){
            self.dialog.on_after_binding();
        };

        self.open = function(open_to_tab){
            self.open_to_tab = open_to_tab;
            self.dialog.show();
            var button_id = null;

            if (self.open_to_tab == "in-process")
            {
                button_id = self.in_process_tab_button_id;
            }
            else if (self.open_to_tab=="failed")
            {
                button_id = self.unfinished_tab_button_id;
            }
            else if (self.unfinished_renderings().length == 0 && self.in_process_renderings().length > 0)
            {
                button_id = self.in_process_tab_button_id;
            }
            else if (self.unfinished_renderings().length > 0 && self.in_process_renderings().length == 0)
            {
                button_id = self.unfinished_tab_button_id;
            }
            if (button_id)
            {
                $("#"+self.dialog_id).find("#"+button_id).click();
            }
            self.open_to_tab = null;
        };

        self.get_unfinished_rendering = function(job_guid, camera_guid)
        {
            for (var index = 0; index < self.unfinished_renderings().length; index++)
            {
                var rendering = self.unfinished_renderings()[index];
                if (rendering.job_guid === job_guid && rendering.camera_guid === camera_guid)
                {
                    return rendering;
                }
            }
            return null;
        };
        self.get_in_process_rendering = function(job_guid, camera_guid)
        {
            for (var index = 0; index < self.in_process_renderings().length; index++)
            {
                var rendering = self.in_process_renderings()[index];
                if (rendering.job_guid === job_guid && rendering.camera_guid === camera_guid)
                {
                    return rendering;
                }
            }
            return null;
        };
        self.update = function(values)
        {
            if (values.unfinished_renderings)
            {
                var unfinished = values.unfinished_renderings.unfinished;
                if (unfinished) {
                    var unfinished_renderings = [];
                    for (var index = 0; index < unfinished.length; index++) {
                        var rendering = unfinished[index];
                        unfinished_renderings.push(new Octolapse.OctolapseUnfinishedRenderingViewModel(rendering));
                    }
                    self.unfinished_renderings(unfinished_renderings);
                }
                var unfinished_size = values.unfinished_renderings.unfinished_size;
                if (unfinished_size)
                {
                    self.unfinished_renderings_size(unfinished_size);
                }
                var unfinished_rendering_change = values.unfinished_renderings.unfinished_rendering_change;
                var unfinished_rendering_change_type = values.unfinished_renderings.unfinished_rendering_change_type;
                if (unfinished_rendering_change && unfinished_rendering_change_type)
                {
                    if (unfinished_rendering_change_type === "added")
                    {
                        self.unfinished_renderings.push(new Octolapse.OctolapseUnfinishedRenderingViewModel(unfinished_rendering_change))
                        self.unfinished_renderings_size(self.unfinished_renderings_size() + unfinished_rendering_change["file_size"])
                    }
                    else if (unfinished_rendering_change_type === "removed")
                    {
                        // Find the unfinished rendering and remove it
                        var rendering = self.get_unfinished_rendering(
                            unfinished_rendering_change.job_guid,
                            unfinished_rendering_change.camera_guid
                        );
                        if (rendering)
                        {
                            self.unfinished_renderings.remove(rendering);
                            self.unfinished_renderings_size(self.unfinished_renderings_size() - unfinished_rendering_change["file_size"])
                        }

                    }
                    else if (unfinished_rendering_change_type === "changed")
                    {
                        // Find the unfinished rendering and remove it
                        var rendering = self.get_unfinished_rendering(
                            unfinished_rendering_change.job_guid,
                            unfinished_rendering_change.camera_guid
                        );
                        if (rendering)
                        {
                            self.unfinished_renderings.replace(rendering, new Octolapse.OctolapseUnfinishedRenderingViewModel(unfinished_rendering_change));
                            self.unfinished_renderings_size(self.unfinished_renderings_size() - rendering.file_size() + unfinished_rendering_change["file_size"])
                        }
                    }
                }
            }
            if (values.in_process_renderings)
            {
                var in_process = values.in_process_renderings.in_process;
                if (in_process) {
                    var in_process_renderings = [];
                    for (var index = 0; index < in_process.length; index++) {
                        var rendering = in_process[index];
                        in_process_renderings.push(new Octolapse.OctolapseInProcessInProcessRenderingViewModel(rendering));
                    }
                    self.in_process_renderings(in_process_renderings);
                }
                var in_process_size = values.in_process_renderings.in_process_size;
                if (in_process_size)
                {
                    self.in_process_renderings_size(in_process_size);
                }

                var in_process_rendering_change = values.in_process_renderings.in_process_rendering_change;
                var in_process_rendering_change_type = values.in_process_renderings.in_process_rendering_change_type;
                if (in_process_rendering_change && in_process_rendering_change_type)
                {
                    if (in_process_rendering_change_type === "added")
                    {
                        self.in_process_renderings.push(new Octolapse.OctolapseInProcessInProcessRenderingViewModel(in_process_rendering_change));
                        self.in_process_renderings_size(self.in_process_renderings_size() + in_process_rendering_change["file_size"]);
                    }
                    else if (in_process_rendering_change_type === "removed")
                    {
                        // Find the in_process rendering and remove it
                        var rendering = self.get_in_process_rendering(
                            in_process_rendering_change.job_guid,
                            in_process_rendering_change.camera_guid
                        );
                        if (rendering)
                        {
                            self.in_process_renderings.remove(rendering);
                            self.in_process_renderings_size(self.in_process_renderings_size() - in_process_rendering_change["file_size"]);
                        }

                    }
                    else if (in_process_rendering_change_type === "changed")
                    {
                        // Find the in_process rendering and remove it
                        var rendering = self.get_in_process_rendering(
                            in_process_rendering_change.job_guid,
                            in_process_rendering_change.camera_guid
                        );
                        if (rendering)
                        {
                            self.in_process_renderings.replace(rendering, new Octolapse.OctolapseInProcessInProcessRenderingViewModel(in_process_rendering_change));
                            self.in_process_renderings_size(self.in_process_renderings_size() - rendering.file_size() + in_process_rendering_change["file_size"])
                        }
                    }
                }
            }
        };

        self.delete_all = function()
        {
            Octolapse.showConfirmDialog(
            "unfinished_rendering",
            "Delete All Unfinished Renderings",
            "All unfinished renderings will be deleted.  Are you sure?",
            function(){
               $.ajax({
                    url: "./plugin/octolapse/deleteAllUnfinishedRenderings",
                    type: "POST",
                    contentType: "application/json",
                    success: function (results) {
                        var options = {
                            title: 'Unfinished Renderings Deleted',
                            text: "All unfinished renderings were deleted.",
                            type: 'success',
                            hide: true,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "unfinished_rendering",["unfinished_rendering"]);
                        self.unfinished_renderings([]);
                        self.unfinished_renderings_size(0);
                    },
                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                        var options = {
                            title: 'Error Deleting Unfinished Renderings',
                            text: "Status: " + textStatus + ".  Error: " + errorThrown,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "unfinished_rendering",["unfinished_rendering"]);
                    }
                });
            });
        };

        self.render_all = function()
        {
            var data = {
                'render_profile_override_guid': self.render_profile_override_guid() || null,
                'camera_profile_override_guid': self.camera_profile_override_guid() || null
            };
            Octolapse.showConfirmDialog(
            "unfinished_rendering",
            "Render All Unfinished Renderings",
            "All unfinished renderings will be rendered, which could take a long time.  Are you sure?",
            function(){
               $.ajax({
                    url: "./plugin/octolapse/renderAllUnfinishedRenderings",
                    type: "POST",
                    data: JSON.stringify(data),
                    contentType: "application/json",
                    dataType: "json",
                    success: function (results) {
                        var options = {
                            title: 'Unfinished Renderings Deleted',
                            text: "All unfinished renderings were deleted.",
                            type: 'success',
                            hide: true,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "unfinished_rendering",["unfinished_rendering"]);
                        self.unfinished_renderings([]);
                        self.unfinished_renderings_size(0);
                    },
                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                        var options = {
                            title: 'Error Deleting Unfinished Renderings',
                            text: "Status: " + textStatus + ".  Error: " + errorThrown,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "unfinished_rendering",["unfinished_rendering"]);
                    }
                });
            });
        };

        self.render = function(rendering)
        {
            var data = {
                'job_guid': rendering.job_guid,
                'camera_guid': rendering.camera_guid,
                'render_profile_override_guid': rendering.render_profile_override_guid() || null,
                'camera_profile_override_guid': rendering.camera_profile_override_guid() || null
            };
            $.ajax({
                    url: "./plugin/octolapse/renderUnfinishedRendering",
                    type: "POST",
                    data: JSON.stringify(data),
                    contentType: "application/json",
                    dataType: "json",
                    success: function (results) {
                        var options = {
                            title: 'Unfinished Rendering Queued',
                            text: "The unfinished rendering added to the rendering queue.",
                            type: 'success',
                            hide: true,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "unfinished_rendering",["unfinished_rendering"]);
                        self.unfinished_renderings.remove(rendering);
                        self.unfinished_renderings_size(self.unfinished_renderings_size() - rendering.file_size());
                    },
                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                        var options = {
                            title: 'Error Deleting Unfinished Rendering',
                            text: "Status: " + textStatus + ".  Error: " + errorThrown,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "unfinished_rendering",["unfinished_rendering"]);
                    }
                });
        };

        self.delete = function(rendering)
        {
            var data = {
                'job_guid': rendering.job_guid,
                'camera_guid': rendering.camera_guid,
            };

            Octolapse.showConfirmDialog(
            "unfinished_rendering",
            "Delete Unfinished Rendering",
            "The selected rendering will be deleted.  Are you sure?",
            function(){
               $.ajax({
                    url: "./plugin/octolapse/deleteUnfinishedRendering",
                    type: "POST",
                    data: JSON.stringify(data),
                    contentType: "application/json",
                    dataType: "json",
                    success: function (results) {
                        var options = {
                            title: 'Unfinished Rendering Deleted',
                            text: "The unfinished rendering was deleted.",
                            type: 'success',
                            hide: true,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "unfinished_rendering",["unfinished_rendering"]);
                        self.unfinished_renderings.remove(rendering);
                        self.unfinished_renderings_size(self.unfinished_renderings_size() - rendering.file_size());
                    },
                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                        var options = {
                            title: 'Error Deleting Unfinished Rendering',
                            text: "Status: " + textStatus + ".  Error: " + errorThrown,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "unfinished_rendering",["unfinished_rendering"]);
                    }
                });
            });
        };

    };
});
