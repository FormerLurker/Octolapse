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
# following email address: FormerLurker@protonmail.com
##################################################################################
*/
$(function() {
    Octolapse.RenderingProfileViewModel = function (values) {
        var self = this;
        self.profileTypeName = ko.observable("Render")
        self.guid = ko.observable(values.guid);
        self.name = ko.observable(values.name);
        self.description = ko.observable(values.description);
        self.enabled = ko.observable(values.enabled);
        self.fps_calculation_type = ko.observable(values.fps_calculation_type);
        self.run_length_seconds = ko.observable(values.run_length_seconds);
        self.fps = ko.observable(values.fps);
        self.max_fps = ko.observable(values.max_fps);
        self.min_fps = ko.observable(values.min_fps);
        self.output_format = ko.observable(values.output_format);
        self.sync_with_timelapse = ko.observable(values.sync_with_timelapse);
        self.bitrate = ko.observable(values.bitrate);
        self.flip_h = ko.observable(values.flip_h);
        self.flip_v = ko.observable(values.flip_v);
        self.rotate_90 = ko.observable(values.rotate_90);
        self.watermark = ko.observable(values.watermark);
        self.post_roll_seconds = ko.observable(values.post_roll_seconds);
        self.pre_roll_seconds = ko.observable(values.pre_roll_seconds);
        self.output_template = ko.observable(values.output_template);

    };
    Octolapse.RenderingProfileValidationRules = {
        rules: {
            bitrate: { required: true, ffmpegBitRate: true },
            output_template: {
                remote: {
                    url: "./plugin/octolapse/validateRenderingTemplate",
                    type:"post"
                }
            },
            min_fps: { lessThanOrEqual: '#octolapse_rendering_max_fps' },
            max_fps: { greaterThanOrEqual: '#octolapse_rendering_min_fps' }
        },
        messages: {
            name: "Please enter a name for your profile",
            min_fps: { lessThanOrEqual: 'Must be less than or equal to the maximum fps.' },
            max_fps: { greaterThanOrEqual: 'Must be greater than or equal to the minimum fps.' },
            output_template: { octolapseRenderingTemplate: 'Either there is an invalid token in the rendering template, or the resulting file name is not valid.' }
        }
    };
});


