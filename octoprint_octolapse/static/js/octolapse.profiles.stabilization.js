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
    Octolapse.StabilizationProfileViewModel = function (values) {
        var self = this;
        self.profileTypeName = ko.observable("Stabilization");
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
        self.wait_for_moves_to_finish = ko.observable(values.wait_for_moves_to_finish);

        self.updateFromServer = function(values) {
            self.name(values.name);
            self.description(values.description);
            self.x_type(values.x_type);
            self.x_fixed_coordinate(values.x_fixed_coordinate);
            self.x_fixed_path(values.x_fixed_path);
            self.x_fixed_path_loop(values.x_fixed_path_loop);
            self.x_fixed_path_invert_loop(values.x_fixed_path_invert_loop);
            self.x_relative(values.x_relative);
            self.x_relative_print(values.x_relative_print);
            self.x_relative_path(values.x_relative_path);
            self.x_relative_path_loop(values.x_relative_path_loop);
            self.x_relative_path_invert_loop(values.x_relative_path_invert_loop);
            self.y_type(values.y_type);
            self.y_fixed_coordinate(values.y_fixed_coordinate);
            self.y_fixed_path(values.y_fixed_path);
            self.y_fixed_path_loop(values.y_fixed_path_loop);
            self.y_fixed_path_invert_loop(values.y_fixed_path_invert_loop);
            self.y_relative(values.y_relative);
            self.y_relative_print(values.y_relative_print);
            self.y_relative_path(values.y_relative_path);
            self.y_relative_path_loop(values.y_relative_path_loop);
            self.y_relative_path_invert_loop(values.y_relative_path_invert_loop);
            if (typeof values.wait_for_moves_to_finish !== 'undefined') {
                self.wait_for_moves_to_finish(values.wait_for_moves_to_finish);
            }
        };

        self.automatic_configuration = new Octolapse.ProfileLibraryViewModel(
            values.automatic_configuration,
            Octolapse.Stabilizations.profileOptions.server_profiles,
            self.profileTypeName(),
            self,
            self.updateFromServer
        );

        self.toJS = function()
        {
            // need to remove the parent link from the automatic configuration to prevent a cyclic copy
            var parent = self.automatic_configuration.parent;
            self.automatic_configuration.parent = null;
            var copy = ko.toJS(self);
            self.automatic_configuration.parent = parent;
            return copy;
        };

        self.on_closed = function(){
            self.automatic_configuration.on_closed();
        };

        self.automatic_configuration.is_confirming.subscribe(function(value){
            //console.log("IsClickable" + value.toString());
            Octolapse.Stabilizations.setIsClickable(!value);
        });
    };


    Octolapse.StabilizationProfileValidationRules = {
        rules: {
            octolapse_stabilization_name: "required"
            , octolapse_stabilization_stabilization_type: "required"
            , octolapse_stabilization_x_type: "required"
            , octolapse_stabilization_x_fixed_coordinate: {number: true, required: true}
            , octolapse_stabilization_x_fixed_path: {required: true, csvFloat: true}
            , octolapse_stabilization_x_relative: {required: true, number: true, min: 0.0, max: 100.0}
            , octolapse_stabilization_x_relative_path: {required: true, csvRelative: true}
            , octolapse_stabilization_y_type: "required"
            , octolapse_stabilization_y_fixed_coordinate: {number: true, required: true}
            , octolapse_stabilization_y_fixed_path: {required: true, csvFloat: true}
            , octolapse_stabilization_y_relative: {required: true, number: true, min: 0.0, max: 100.0}
            , octolapse_stabilization_y_relative_path: {required: true, csvRelative: true},
        },
        messages: {
            octolapse_stabilization_name: "Please enter a name for your profile",
        }
    };
});


