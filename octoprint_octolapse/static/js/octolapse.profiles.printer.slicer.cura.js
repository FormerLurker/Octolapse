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
Octolapse.CuraExtruderViewModel = function (values, extruder_index) {
    var self=this;
    self.index = extruder_index;
    self.speed_z_hop = ko.observable(null);
    self.max_feedrate_z_override = ko.observable(null);
    self.retraction_amount = ko.observable(null);
    self.retraction_hop = ko.observable(null);
    self.retraction_hop_enabled = ko.observable(false);
    self.retraction_enable = ko.observable(false);
    self.retraction_speed = ko.observable(null);
    self.retraction_retract_speed = ko.observable(null);
    self.retraction_prime_speed = ko.observable(null);
    self.speed_travel = ko.observable(null);

    if (values && values.extruders.length > self.index) {
        var extruder = values.extruders[self.index];
        if (!extruder)
            return;
        self.speed_z_hop(extruder.speed_z_hop);
        self.max_feedrate_z_override(extruder.max_feedrate_z_override);
        self.retraction_amount(extruder.retraction_amount);
        self.retraction_hop(extruder.retraction_hop);
        self.retraction_hop_enabled(extruder.retraction_hop_enabled || false);
        self.retraction_enable(extruder.retraction_enable || false);
        self.retraction_speed(extruder.retraction_speed);
        self.retraction_retract_speed(extruder.retraction_retract_speed);
        self.retraction_prime_speed(extruder.retraction_prime_speed);
        self.speed_travel(extruder.speed_travel);
    }
};

Octolapse.CuraViewmodel = function (values, num_extruders_observable) {
    var self = this;
    // Observables
    self.num_extruders_observable = num_extruders_observable;
    var extruders = [];
    for (var index = 0; index < self.num_extruders_observable(); index++)
    {
        extruders.push(new Octolapse.CuraExtruderViewModel(values, index));
    }
    self.extruders = ko.observableArray(extruders);
    self.layer_height = ko.observable(values.layer_height);
    self.smooth_spiralized_contours = ko.observable(values.smooth_spiralized_contours || false);
    // Create constants
    self.speed_tolerance = 0.1 / 60.0 / 2.0;
    self.round_to_increment_mm_min = 0.00000166667;
    self.round_to_increment_mm_sec = 0.0001;
    self.round_to_increment_length = 0.0001;
    self.round_to_increment_num_layers = 1;

    self.num_extruders_observable.subscribe(function() {
        var num_extruders = self.num_extruders_observable();
        if (num_extruders < 1) {
            num_extruders = 1;
        }
        else if (num_extruders > 16){
            num_extruders = 16;
        }

        var extruders = self.extruders();
        while(extruders.length < num_extruders)
        {
            var new_extruder = new Octolapse.CuraExtruderViewModel(null, extruders.length-1);
            extruders.push(new_extruder);
        }
        while(extruders.length > num_extruders)
        {
             extruders.pop();
        }
        self.extruders(extruders);

    });
};
