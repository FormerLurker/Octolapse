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
            })
        }

    };

    Octolapse.MjpgStreamerViewModel = function (values) {
        var self = this;
        self.controls = ko.observableArray([]);

        self.update = function(values) {
            if (!values)
                return;
            self.controls([]);
            for (var key in values.controls) {
                control = values.controls[key];
                if ("id" in control) {
                    self.controls.push(new Octolapse.MjpgStreamerControlViewModel(control));
                }
            }
        };
        self.update(values);

    };
});
