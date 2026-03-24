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
$(function() {
   Octolapse.RaspiCamV2ViewModel = function (parent) {
        var self = this;
        self.data = ko.observable();
        self.data.parent = parent;
        self.data.color_effects_id = '9963807';
        self.data.color_effects_cb_cr_id = '9963818';
        self.data.scene_mode_id = '10094874';
        self.data.auto_exposure_id = '10094849';
        self.data.exposure_time_absolute_id = '10094850';
        self.data.exposure_dynamic_framerate_id = '10094851';
        self.data.auto_exposure_bias_id = '10094851';
        self.data.iso_sentitivity_auto_id = '10094872';

        self.color_effects = function(){
           return self.data.parent.data.controls_dict[self.data.color_effects_id];
        };

        self.color_effects_cb_cr = function(){
            return self.data.parent.data.controls_dict[self.data.color_effects_cb_cr_id];
        };

        self.scene_mode = function(){
            return self.data.parent.data.controls_dict[self.data.scene_mode_id];
        };

        self.auto_exposure = function(){
            return self.data.parent.data.controls_dict[self.data.auto_exposure_id];
        };

        self.exposure_time_absolute = function(){
            return self.data.parent.data.controls_dict[self.data.exposure_time_absolute_id];
        };

        self.exposure_dynamic_framerate = function(){
            return self.data.parent.data.controls_dict[self.data.exposure_dynamic_framerate_id];
        };

        self.auto_exposure_bias = function(){
            return self.data.parent.data.controls_dict[self.data.auto_exposure_bias_id];
        };

        self.iso_sentitivity_auto = function(){
            return self.data.parent.data.controls_dict[self.data.iso_sentitivity_auto_id];
        };

        self.on_after_binding = function(){
            if (!self.data.parent.data.controls_dict)
                return;

            self.auto_exposure_enabled = ko.pureComputed(function(){
                return self.scene_mode().value().toString() == "0";
            });

            self.manual_exposure_controls_enabled = ko.pureComputed(function(){
                return self.auto_exposure_enabled() && self.auto_exposure().value().toString() == "1";
            });

            self.auto_exposure_controls_enabled = ko.pureComputed(function(){
                return self.auto_exposure_enabled() && self.auto_exposure().value().toString() == "0";
            });

            self.scene_or_auto_exposure_enabled = ko.pureComputed(function(){
                return self.scene_mode().value().toString() != "0" || self.auto_exposure_controls_enabled();
            });

            self.is_sensitivity_enabled = ko.pureComputed(function(){
                return self.scene_or_auto_exposure_enabled() && self.iso_sentitivity_auto().value().toString() == "0";
            });

            self.exposure_time_absolute().value.subscribe(function(newValue){
                if (newValue > 1000)
                    return 1000;
            });

            self.color_effects_cb_cr_enabled = ko.pureComputed(function(){
               switch (self.color_effects().value().toString())
               {
                    case "15":
                    case "10":
                    case "2":
                    case "3":
                        return true;
               }
               return false;
            });

        };

   };
});
