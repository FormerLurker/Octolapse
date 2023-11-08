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
    Octolapse.MjpgStreamerControlViewModel = function (values) {
        var self = this;
        self.name = ko.observable(values.name);
        self.id = ko.observable(values.id);
        self.type = ko.observable(values.type);
        self.min = ko.observable(values.min);
        self.max = ko.observable(values.max);
        self.step = ko.observable(values.step);
        self.default = ko.observable(values.default);
        self.value = ko.observable(values.value).extend({ rateLimit: { timeout: 250, method: "notifyAtFixedRate" } });
        self.dest = ko.observable(values.dest);
        self.flags = ko.observable(values.flags);
        self.group = ko.observable(values.group);
        self.menu = ko.observable(values.menu);
        self.order = ko.observable(values.order);
        self.get_template_id_for_control = function () {
            switch (self.type()) {
                case "1":
                    // Some check boxes are reported as type 2.  So if Max=1 and Min=0 and Step = 1
                    // return the check box template
                    if (self.min() == "0" && self.max() == "1" && self.step() == "1") {
                        return "mjpg-streamer-checkbox-control-template";
                    }
                    return "mjpg-streamer-numeric-control-template";
                case "2":
                    return "mjpg-streamer-checkbox-control-template";
                case "3":
                    return "mjpg-streamer-dropdown-control-template";
                case "6":
                    return "mjpg-streamer-label-control-template";
                case "9":
                    return "mjpg-streamer-numeric-control-template";
                default:
                    return "mjpg-streamer-unknown-control-unknown";
            }
        };
        self.get_options = ko.pureComputed(function () {
            var options = [];
            for (var key in self.menu()) {
                var name = self.menu()[key];
                if (!name || name.trim() === "")
                    name = "Unknown (value=" + key + ")";
                var option = {
                    "name": name,
                    "value": parseInt(key)
                };
                options.push(option);
            }
            return Octolapse.nameSort(options);
        });

        if (self.type() == "2" || (self.min() == "0" && self.max() == "1" && self.step() == "1"))
        {
            var checked = self.value() != "0";
            self.checkbox_checked = ko.observable(checked);
            self.checkbox_checked.subscribe(function(newValue){
                if(newValue)
                    self.value("1");
                else
                    self.value("0");
            });
        }

        self.help_url = ko.pureComputed(function() {
            return 'profiles.camera.webcam_settings.mjpg-streamer.options.' + self.id() + '.md';
        });

        self.help_not_found = ko.pureComputed(function(){
            return "This is an unknown camera setting control.  Please submit an issue [here](http://github.com/formerlurker/octolapse/issues/new) if you'd like a help file added to support this control.  Please include the make and model of your camera, and include following data - Id:" + self.id() + ", Name:" + self.name();
        });

        self.slider_label = ko.pureComputed(function() {
            return self.name();// + " (" + self.min().toString() + "-" + self.max().toString() + ")";
        });

        self.checkbox_title = ko.pureComputed(function() {
            return "Enable or disable " + self.name() + ".";
        });

    };

    Octolapse.MjpgStreamerViewModel = function (values) {
        var self = this;
        self.controls = ko.observableArray([]);
        self.data = ko.observable();
        self.data.controls_dict = {};
        self.camera_type_key = ko.observable();
        self.data.custom_camera_viewmodel = null;

        self.create_viewmodel_for_camera_type_key = function(camera_type_key){
            switch(camera_type_key)
            {
                case "raspi_cam_v2":
                    self.data.custom_camera_viewmodel = new Octolapse.RaspiCamV2ViewModel(self);
                    break;
                default:
                    self.data.custom_camera_viewmodel = null;
            }
        };

        self.bind_viewmodel_for_camera_type = function(){
            if (self.data.custom_camera_viewmodel)
                self.data.custom_camera_viewmodel.on_after_binding();
        };

        self.update = function(values, type, use_custom_webcam_settings_page) {
            if (!values)
                return;
            var controls = [];
            self.data.controls_dict = {};
            // return if we have no controls
            if (!values.controls)
                return;
            // set the custom viewmodel, if one is available
            var key = null;
            if (type && use_custom_webcam_settings_page)
                key = type.key;

            self.create_viewmodel_for_camera_type_key(key);

            var sortedControls = self.getSortedControlArray(values.controls);
            for (var index in sortedControls) {
                var control = new Octolapse.MjpgStreamerControlViewModel(sortedControls[index]);
                if ("id" in control) {
                    self.data.controls_dict[control.id()] = control;
                    controls.push(control);
                }
            }
            self.controls(controls);
            self.bind_viewmodel_for_camera_type();
        };

        self.getSortedControlArray = function (control_dict) {
            // first turn the controlDict into an array
            var control_array =[];
            for (var key in control_dict)
            {
                var control = control_dict[key];
                control_array.push(control);
            }
            return control_array.sort(
                function (left, right) {
                    var leftOrder = left.order || 0;
                    var rightOrder = right.order || 0;
                    return leftOrder === rightOrder ? 0 : (leftOrder < rightOrder ? -1 : 1);
                }
            );
        };

        self.update(values);

    };
});
