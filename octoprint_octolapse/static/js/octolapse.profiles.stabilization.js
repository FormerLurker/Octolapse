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
$(function() {
    Octolapse.StabilizationProfileViewModel = function (values) {
        var self = this;
        self.profileTypeName = ko.observable("Stabilization")
        self.guid = ko.observable(values.guid);
        self.name = ko.observable(values.name);
        self.description = ko.observable(values.description);
        self.x_type = ko.observable(values.x_type);
        self.x_fixed_coordinate = ko.observable(values.x_fixed_coordinate);
        self.x_fixed_path = ko.observable(values.x_fixed_path);
        self.x_fixed_path_loop = ko.observable(values.x_fixed_path_loop);
        self.x_fixed_path_invert_loop = ko.observable(values.x_fixed_path_invert_loop);
        self.x_relative = ko.observable(values.x_relative);
        self.x_relative_print = ko.observable(values.x_relative_print);
        self.x_relative_path = ko.observable(values.x_relative_path);
        self.x_relative_path_loop = ko.observable(values.x_relative_path_loop);
        self.x_relative_path_invert_loop = ko.observable(values.x_relative_path_invert_loop);
        self.y_type = ko.observable(values.y_type);
        self.y_fixed_coordinate = ko.observable(values.y_fixed_coordinate);
        self.y_fixed_path = ko.observable(values.y_fixed_path);
        self.y_fixed_path_loop = ko.observable(values.y_fixed_path_loop);
        self.y_fixed_path_invert_loop = ko.observable(values.y_fixed_path_invert_loop);
        self.y_relative = ko.observable(values.y_relative);
        self.y_relative_print = ko.observable(values.y_relative_print);
        self.y_relative_path = ko.observable(values.y_relative_path);
        self.y_relative_path_loop = ko.observable(values.y_relative_path_loop);
        self.y_relative_path_invert_loop = ko.observable(values.y_relative_path_invert_loop);
    };

    Octolapse.StabilizationProfileValidationRules = {
        rules: {
            name: "required"
            ,x_type: "required"
            ,x_fixed_coordinate: { number: true, required: true }
            , x_fixed_path: { required: true, csvFloat: true}
            , x_relative: { required: true, number: true,min:0.0, max:100.0 }
            , x_relative_path: { required: true, csvRelative: true }
            , y_type: "required"
            , y_fixed_coordinate: { number: true, required: true }
            , y_fixed_path: { required: true, csvFloat: true }
            , y_relative: { required: true, number: true, min: 0.0, max: 100.0 }
            , y_relative_path: { required: true, csvRelative: true }

        },
        messages: {
            name: "Please enter a name for your profile"
        }
    };
});


