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
Octolapse = {};
 Octolapse.Printers = { 'current_profile_guid': function () {return null;}}
OctolapseViewModel = {};

$(function () {
    // Finds the first index of an array with the matching predicate
    Octolapse.IsShowingSettingsChangedPopup = false;

    Octolapse.toggleContentFunction = function ($elm, options, updateObservable)
    {
        if(options.toggle_observable){
            //console.log("Toggling element.");
            if(updateObservable) {
                options.toggle_observable(!options.toggle_observable());
                //console.log("Observable updated - " + options.toggle_observable())
            }
            if (options.toggle_observable()) {
                if (options.class_showing) {
                    $elm.children('[class^="icon-"]').addClass(options.class_showing);
                    $elm.children('[class^="fa"]').addClass(options.class_showing);
                }
                if (options.class_hiding) {
                    $elm.children('[class^="icon-"]').removeClass(options.class_hiding);
                    $elm.children('[class^="fa"]').removeClass(options.class_hiding);
                }
                if(options.container) {
                    if (options.parent) {
                        $elm.parents(options.parent).find(options.container).stop().slideDown('fast', options.onComplete);
                    } else {
                        $(options.container).stop().slideDown('fast', options.onComplete);
                    }
                }
            }
            else
             {
                 if (options.class_hiding) {
                     $elm.children('[class^="icon-"]').addClass(options.class_hiding);
                     $elm.children('[class^="fa"]').addClass(options.class_hiding);
                 }
                if (options.class_showing) {
                    $elm.children('[class^="icon-"]').removeClass(options.class_showing);
                    $elm.children('[class^="fa"]').removeClass(options.class_showing);
                }
                if(options.container) {
                    if (options.parent) {
                        $elm.parents(options.parent).find(options.container).stop().slideUp('fast', options.onComplete);
                    } else {
                        $(options.container).stop().slideUp('fast', options.onComplete);
                    }
                }
            }
        }
        else {
            if (options.class) {
                $elm.children('[class^="icon-"]').toggleClass(options.class_hiding + ' ' + options.class_showing);
                $elm.children('[class^="fa"]').toggleClass(options.class_hiding + ' ' + options.class_showing);
            }
            if (options.container) {
                if (options.parent) {
                    $elm.parents(options.parent).find(options.container).stop().slideToggle('fast', options.onComplete);
                } else {
                    $(options.container).stop().slideToggle('fast', options.onComplete);
                }
            }
        }

    };

    Octolapse.toggleContent = {
            init: function(element, valueAccessor) {
                var $elm = $(element),
                    options = $.extend({
                        class_showing: null,
                        class_hiding: null,
                        container: null,
                        parent: null,
                        toggle_observable: null,
                        onComplete: function() {
                            $(document).trigger("slideCompleted");
                        }
                    }, valueAccessor());

                    if(options.toggle_observable)
                        Octolapse.toggleContentFunction($elm,options, false);


                $elm.on("click", function(e) {
                    e.preventDefault();
                    Octolapse.toggleContentFunction($elm,options, true);


                });
            }
        };
    ko.bindingHandlers.octolapseToggle = Octolapse.toggleContent ;

    Octolapse.arrayFirstIndexOf = function (array, predicate, predicateOwner) {
        for (var i = 0, j = array.length; i < j; i++) {
            if (predicate.call(predicateOwner, array[i])) {
                return i;
            }
        }
        return -1;
    };
    // Creates a pseudo-guid
    Octolapse.guid = function () {
        function s4() {
            return Math.floor((1 + Math.random()) * 0x10000)
                .toString(16)
                .substring(1);
        }
        return s4() + s4() + '-' + s4() + '-' + s4() + '-' +
            s4() + '-' + s4() + s4() + s4();
    };
    Octolapse.HasTakenFirstSnapshot = false;
    // Returns an observable sorted by name(), case insensitive
    Octolapse.nameSort = function (observable) {
        return observable().sort(
            function (left, right) {
                var leftName = left.name().toLowerCase();
                var rightName = right.name().toLowerCase();
                return leftName === rightName ? 0 : (leftName < rightName ? -1 : 1);
            });
    };
    // Toggles an element based on the data-toggle attribute.  Expects list of elements containing a selector, onClass and offClass.
    // It will apply the on or off class to the result of each selector, which should return exactly one result.
    Octolapse.toggle = function (caller, args) {
        var elements = args.elements;
        elements.forEach(function (item) {
            var element = $(item.selector);
            var onClass = item.onClass;
            var offClass = item.offClass;
            if (element.hasClass(onClass)) {
                element.removeClass(onClass);
                element.addClass(offClass);
            } else {
                element.removeClass(offClass);
                element.addClass(onClass);
            }
        });
    };

    // Cookies (only for UI display purposes, not for any tracking
    Octolapse.COOKIE_EXPIRE_DAYS = 30;

    Octolapse.setLocalStorage = function (name, value) {
        localStorage.setItem("octolapse_"+name,value)
    }
    Octolapse.getLocalStorage = function (name, value) {
        return localStorage.getItem("octolapse_"+name)
    }

    Octolapse.displayPopup = function (options) {
        new PNotify(options);
    };

    Octolapse.Popups = {};
    Octolapse.displayPopupForKey = function (options, key) {
        if (key in Octolapse.Popups) {
            Octolapse.Popups[key].remove();
        }
        Octolapse.Popups[key] = new PNotify(options);
    };

    Octolapse.ToggleElement = function (element) {
        var args = $(this).attr("data-toggle");
        Octolapse.toggle(this, JSON.parse(args));
    };

    // Add custom validator for csv strings (no inner whitespace)
    $.validator.addMethod('csvString', function (value) {
        var csvStringRegex = /^(\s*[A-Z]\d+\s*(?:$|,))+$/gim;
        var csvStringComponentRegex = /[A-Z]\d+/gim;
        //console.log("Validating csvString: " + value);
        // We will allow 0 length trimmed strings
        if (value.length > 0) {
            if (!value.match(csvStringRegex))
                return false;
            var values = value.split(",");
            for (var index = 0; index < values.length; index++) {
                if (!values[index].match(csvStringComponentRegex))
                    return false;
            }
        }
        return true;
    }, 'Please enter a list of strings separated by commas.');


    $.validator.addMethod("check_one", function(value, elem, param)
        {
            //console.log("Validating trigger checks");
            $(param).val()
                if($(param + ":checkbox:checked").length > 0){
                   return true;
                }else {
                   return false;
                }
        }
    );

    // Add custom validator for csv floats
    $.validator.addMethod('csvFloat', function (value) {
        return /^(\s*-?\d+(\.\d+)?)(\s*,\s*-?\d+(\.\d+)?)*\s*$/.test(value);
    }, 'Please enter a list of decimals separated by commas.');
    // Add a custom validator for csv floats between 0 and 100
    $.validator.addMethod('csvRelative', function (value) {
        return /^(\s*\d{0,2}(\.\d+)?|100(\.0+)?)(\s*,\s*\d{0,2}(\.\d+)?|100(\.0+)?)*\s*$/.test(value);
    }, 'Please enter a list of decimals between 0.0 and 100.0 separated by commas.');
    // Add a custom validator for integers
    $.validator.addMethod('integer',
        function (value) {
            return /^-?\d+$/.test(value);
        }, 'Please enter an integer value.');
    // Add a custom validator for positive
    $.validator.addMethod('integerPositive',
        function (value) {
            return /^\d+$/.test(value);
        }, 'Please enter a positive integer value.');
    $.validator.addMethod('ffmpegBitRate',
        function (value) {
            return /^\d+[KkMm]$/.test(value);
        }, 'Enter a bitrate, K for kBit/s and M for MBit/s.  Example: 1000K');
    $.validator.addMethod('lessThanOrEqual',
        function (value, element, param) {
            var i = parseFloat(value);
            var j = parseFloat($(param).val());
            return (i <= j);
        });
    $.validator.addMethod('greaterThanOrEqual',
        function (value, element, param) {
            var i = parseFloat(value);
            var j = parseFloat($(param).val());
            return (i >= j);
        });
    $.validator.addMethod('lessThan',
        function (value, element, param) {
            var i = parseFloat(value);
            var $target = $(param);

            // I we didn't find a target, return true
            if ($target.length === 0)
                return true;
            var j = parseFloat($target.val());
            return (i < j);
        });
    $.validator.addMethod('greaterThan',
        function (value, element, param) {
            var i = parseFloat(value);
            var $target = $(param);

            // I we didn't find a target, return true
            if ($target.length === 0)
                return true;
            var j = parseFloat($target.val());
            return (i > j);
        });
    $.validator.addMethod('octolapseSnapshotTemplate',
        function (value, element) {
            var testUrl = value.toUpperCase().replace("{CAMERA_ADDRESS}", 'http://w.com/');
            return jQuery.validator.methods.url.call(this, testUrl, element);
        });
    $.validator.addMethod('octolapseCameraRequestTemplate',
        function (value, element) {
            var testUrl = value.toUpperCase().replace("{CAMERA_ADDRESS}", 'http://w.com/').replace("{value}", "1");
            return jQuery.validator.methods.url.call(this, testUrl, element);
        });
    $.validator.addMethod('octolapseRenderingTemplate',
        function (value, element) {
            var data = {"rendering_template":value};
            $.ajax({
                url: "./plugin/octolapse/validateRenderingTemplate",
                type: "POST",
                tryCount: 0,
                retryLimit: 3,
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (result) {
                    if(result.success)
                        return true;
                    return false;
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    alert("Octolapse could not validate the rendering template.");
                    return false;
                }
            });

        });

    jQuery.extend(jQuery.validator.messages, {
        name: "Please enter a name.",
        required: "This field is required.",
        url: "Please enter a valid URL.",
        number: "Please enter a valid number.",
        equalTo: "Please enter the same value again.",
        maxlength: jQuery.validator.format("Please enter no more than {0} characters."),
        minlength: jQuery.validator.format("Please enter at least {0} characters."),
        rangelength: jQuery.validator.format("Please enter a value between {0} and {1} characters long."),
        range: jQuery.validator.format("Please enter a value between {0} and {1}."),
        max: jQuery.validator.format("Please enter a value less than or equal to {0}."),
        min: jQuery.validator.format("Please enter a value greater than or equal to {0}."),
        octolapseCameraRequestTemplate: "The value is not a url.  You may use {camera_address} or {value} tokens.",
        octolapseSnapshotTemplate: "The value is not a url.  You may use {camera_address} to refer to the web camera address."
    });
    // Knockout numeric binding
    Octolapse.NullNumericText = "none";
    ko.extenders.numeric = function (target, precision) {
        var result = ko.dependentObservable({
            read: function () {
                val = target();
                if (val == null)
                    return Octolapse.NullNumericText;
                return val.toFixed(precision);
            },
            write: target
        });

        result.raw = target;
        return result;
    };
    /**
     * @return {string}
     */
    Octolapse.ToTime = function (seconds) {
        if (val == null)
            return Octolapse.NullTimeText;
        var utcSeconds = seconds;
        var d = new Date(0); // The 0 there is the key, which sets the date to the epoch
        d.setUTCSeconds(utcSeconds);
        return d.getHours() + ":"
            + d.getMinutes() + ":"
            + d.getSeconds();
    };

    /**
     * @return {string}
     */
    Octolapse.ToTimer = function (seconds) {
        if (seconds == null)
            return "";
        if (seconds <= 0)
            return "0:00";

        var hours = Math.floor(seconds / 3600);
        if (hours > 0) {
            return ("" + hours).slice(-2) + " Hrs"
        }

        seconds %= 3600;
        var minutes = Math.floor(seconds / 60);
        seconds = seconds % 60;
        return ("0" + minutes).slice(-2) + ":" + ("0" + seconds).slice(-2);
    };

    Octolapse.ToCompactInt = function (value) {
        var newValue = value;
        if (value >= 1000) {
            var suffixes = ["", "k", "m", "b", "t"];
            var suffixNum = Math.floor(("" + value).length / 3);
            var shortValue = '';
            for (var precision = 2; precision >= 1; precision--) {
                shortValue = parseFloat((suffixNum !== 0 ? (value / Math.pow(1000, suffixNum)) : value).toPrecision(precision));
                var dotLessShortValue = (shortValue + '').replace(/[^a-zA-Z 0-9]+/g, '');
                if (dotLessShortValue.length <= 2) { break; }
            }

            if (shortValue % 1 !== 0) shortValue = shortValue.toFixed(1);

            newValue = shortValue + suffixes[suffixNum];
        }
        return newValue;
    };


    Octolapse.NullTimeText = "none";
    ko.extenders.time = function (target, options) {
        var result = ko.dependentObservable({
            read: function () {
                val = target();
                return Octolapse.ToTime(val)
            },
            write: target
        });

        result.raw = target;
        return result;
    };

    OctolapseViewModel = function (parameters) {
        var self = this;
        Octolapse.Globals = self;

        self.loginState = parameters[0];
        Octolapse.PrinterStatus = parameters[1];
        // Global Values
        self.show_position_state_changes = ko.observable(false);
        self.show_position_changes = ko.observable(false);
        self.show_extruder_state_changes = ko.observable(false);
        self.show_trigger_state_changes = ko.observable(false);
        self.auto_reload_latest_snapshot = ko.observable(false);
        self.auto_reload_frames = ko.observable(5);
        self.is_admin = ko.observable(false);
        self.enabled = ko.observable(false);
        self.navbar_enabled = ko.observable(false);
        self.show_navbar_when_not_printing = ko.observable(false);
        self.show_real_snapshot_time = ko.observable(false);

        self.version = ko.observable("unknown");
        // Create a guid to uniquely identify this client.
        self.client_id = Octolapse.guid();
        // Have we loaded the state yet?
        self.HasLoadedState = false;


        self.onBeforeBinding = function () {
            self.is_admin(self.loginState.isAdmin());
        };
        self.onStartupComplete = function () {
            //console.log("Startup Complete")
            self.getInitialState();

        };
        self.onDataUpdaterReconnect = function () {
            //console.log("Reconnected Client")
            self.getInitialState();

        };

        self.getInitialState = function(){
            self.loadState();
            // reset snapshot error state
            Octolapse.Status.snapshot_error(false);
            Octolapse.Status.snapshot_error_message("");
        }

        self.loadState = function () {
            //console.log("octolapse.js - Loading State");
            $.ajax({
                url: "./plugin/octolapse/loadState",
                type: "POST",
                tryCount: 0,
                retryLimit: 3,
                ccontentType: "application/json",
                dataType: "json",
                success: function (result) {
                    //console.log("The state has been loaded.  Waiting for message");

                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {

                    //console.log("Octolapse was unable to retrieve the current state, trying again in 5 seconds");
                    setTimeout(self.getInitialState, 5000);
                    // Todo:  update the UI to show we're waiting for our state!
                }
            });
        };
        self.onUserLoggedIn = function (user) {
            //console.log("octolapse.js - User Logged In.  User: " + user);
            self.is_admin(self.loginState.isAdmin());
            if(self.is_admin())
                Octolapse.Settings.loadSettings();
        };
        self.onUserLoggedOut = function () {
            //console.log("octolapse.js - User Logged Out");
            self.is_admin(false);
            Octolapse.Settings.clearSettings();
        };

        self.updateState = function (state) {
            //console.log(state);
            if (state.Position != null) {
                //console.log('octolapse.js - state-changed - Position');
                Octolapse.Status.updatePosition(state.Position);
            }
            if (state.PositionState != null) {
                //console.log('octolapse.js - state-changed - Position State');
                Octolapse.Status.updatePositionState(state.PositionState);
            }
            if (state.Extruder != null) {
                //console.log('octolapse.js - state-changed - Extruder State');
                Octolapse.Status.updateExtruderState(state.Extruder);
            }
            if (state.TriggerState != null) {
                //console.log('octolapse.js - state-changed - Trigger State');
                Octolapse.Status.updateTriggerStates(state.TriggerState);

            }
            if (state.MainSettings != null) {
                //console.log('octolapse.js - state-changed - Trigger State');
                // Do not update the main settings unless they are saved.
                //Octolapse.SettingsMain.update(state.MainSettings);
                // detect changes to auto_reload_latest_snapshot
                var cur_auto_reload_latest_snapshot = Octolapse.Globals.auto_reload_latest_snapshot();

                Octolapse.Globals.update(state.MainSettings);
                Octolapse.SettingsMain.setSettingsVisibility(Octolapse.Globals.enabled());
                if (cur_auto_reload_latest_snapshot !== Octolapse.Globals.auto_reload_latest_snapshot()) {
                    //console.log('octolapse.js - Octolapse.Globals.auto_reload_latest_snapshot changed, erasing previous snapshot images');
                    Octolapse.Status.erasePreviousSnapshotImages('octolapse_snapshot_image_container');
                    Octolapse.Status.erasePreviousSnapshotImages('octolapse_snapshot_thumbnail_container');
                }

            }
            if (state.Status != null) {
                //console.log('octolapse.js - state-changed - Trigger State');
                Octolapse.Status.update(state.Status);
            }
            if (!self.HasLoadedState) {
                Octolapse.Status.updateLatestSnapshotImage(true);
                Octolapse.Status.updateLatestSnapshotThumbnail(true);
            }

            self.HasLoadedState = true;
        };
        self.update = function (settings) {
            // enabled
            if (ko.isObservable(settings.is_octolapse_enabled))
                self.enabled(settings.is_octolapse_enabled());
            else
                self.enabled(settings.is_octolapse_enabled);

            if (ko.isObservable(settings.version))
                self.version(settings.version());
            else
                self.version(settings.version);

            // self.auto_reload_latest_snapshot
            if (ko.isObservable(settings.auto_reload_latest_snapshot))
                self.auto_reload_latest_snapshot(settings.auto_reload_latest_snapshot());
            else
                self.auto_reload_latest_snapshot(settings.auto_reload_latest_snapshot);
            //auto_reload_frames
            if (ko.isObservable(settings.auto_reload_frames))
                self.auto_reload_frames(settings.auto_reload_frames());
            else
                self.auto_reload_frames(settings.auto_reload_frames);
            // navbar_enabled
            if (ko.isObservable(settings.show_navbar_icon))
                self.navbar_enabled(settings.show_navbar_icon());
            else
                self.navbar_enabled(settings.show_navbar_icon);

            if (ko.isObservable(settings.show_navbar_when_not_printing))
                self.show_navbar_when_not_printing(settings.show_navbar_when_not_printing());
            else
                self.show_navbar_when_not_printing(settings.show_navbar_when_not_printing);


            if (ko.isObservable(settings.show_position_state_changes))
                self.show_position_state_changes(settings.show_position_state_changes());
            else
                self.show_position_state_changes(settings.show_position_state_changes);

            if (ko.isObservable(settings.show_position_changes))
                self.show_position_changes(settings.show_position_changes());
            else
                self.show_position_changes(settings.show_position_changes);

            if (ko.isObservable(settings.show_extruder_state_changes))
                self.show_extruder_state_changes(settings.show_extruder_state_changes());
            else
                self.show_extruder_state_changes(settings.show_extruder_state_changes);

            if (ko.isObservable(settings.show_trigger_state_changes))
                self.show_trigger_state_changes(settings.show_trigger_state_changes());
            else
                self.show_trigger_state_changes(settings.show_trigger_state_changes)

            if (ko.isObservable(settings.show_real_snapshot_time))
                self.show_real_snapshot_time(settings.show_real_snapshot_time());
            else
                self.show_real_snapshot_time(settings.show_real_snapshot_time)


        };
        // Handle Plugin Messages from Server
        self.onDataUpdaterPluginMessage = function (plugin, data) {
            if (plugin !== "octolapse") {
                return;
            }
            switch (data.type) {
                case "settings-changed":
                    {
                        // Was this from us?
                        if (self.client_id !== data.client_id && self.is_admin())
                        {
                            if (!Octolapse.IsShowingSettingsChangedPopup)
                            {
                                Octolapse.IsShowingSettingsChangedPopup = true;
                                if (confirm("A settings change was detected from another client.  Reload settings?"))
                                {
                                    Octolapse.Settings.loadSettings();
                                }
                                Octolapse.IsShowingSettingsChangedPopup = false;
                            }
                        }
                        self.updateState(data);
                    }
                    break;
                case "state-loaded":
                    {
                        //console.log('octolapse.js - state-loaded');
                        self.updateState(data);
                    }
                    break;
                case "state-changed":
                    {
                        //console.log('octolapse.js - state-changed');
                        self.updateState(data);
                    }
                    break;
                case "popup":
                    {
                        //console.log('octolapse.js - popup');
                        var options = {
                            title: 'Octolapse Notice',
                            text: data.msg,
                            type: 'notice',
                            hide: true,
                            addclass: "octolapse",
                            desktop: {
                                desktop: true
                            }
                        };
                        Octolapse.displayPopup(options);
                    }
                    break;
                case "popup-error":
                    {
                        //console.log('octolapse.js - popup-error');
                        self.updateState(data);
                        var options = {
                            title: 'Octolapse Startup Failed',
                            text: data.msg,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse",
                            desktop: {
                                desktop: true
                            }
                        };
                        Octolapse.displayPopup(options);
                        break;
                    }
                case "timelapse-start":
                    {
                        //console.log('octolapse.js - timelapse-start');
                        // Erase any previous images
                        Octolapse.HasTakenFirstSnapshot = false;
                        // let the status tab know that a timelapse is starting
                        Octolapse.Status.onTimelapseStart();
                        self.updateState(data);
                    }
                    break;
                case "timelapse-complete":
                    {
                        //console.log('octolapse.js - timelapse-complete');
                        self.updateState(data)
                    }
                    break;
                case "snapshot-start":
                    {
                        //console.log('octolapse.js - snapshot-start');
                        self.updateState(data);
                        Octolapse.Status.snapshot_error(false);
                        Octolapse.Status.snapshot_error_message("");
                    }
                    break;
                case "snapshot-complete":
                    {
                        //console.log('octolapse.js - snapshot-complete');
                        //console.log(data);
                        self.updateState(data);
                        if(!data.snapshot_success && data.success)
                        {
                            // If only the camera image acquisition failed, use the camera error message
                            Octolapse.Status.snapshot_error(!data.snapshot_success);
                            Octolapse.Status.snapshot_error_message(data.snapshot_error);
                        }
                        else {
                            Octolapse.Status.snapshot_error(!data.success);
                            Octolapse.Status.snapshot_error_message(data.error);
                        }
                        if (!Octolapse.HasTakenFirstSnapshot) {
                            Octolapse.HasTakenFirstSnapshot = true;
                            Octolapse.Status.erasePreviousSnapshotImages('octolapse_snapshot_image_container',true);
                            Octolapse.Status.erasePreviousSnapshotImages('octolapse_snapshot_thumbnail_container', true);
                            Octolapse.Status.updateLatestSnapshotThumbnail(true);
                            Octolapse.Status.updateLatestSnapshotImage();
                        }
                        else
                        {
                            Octolapse.Status.updateLatestSnapshotThumbnail();
                            Octolapse.Status.updateLatestSnapshotImage();
                        }
                    }
                    break;
                case "render-start":
                    {
                        //console.log('octolapse.js - render-start');
                        self.updateState(data);

                        var options = {
                            title: 'Octolapse Rendering Started',
                            text: data.msg,
                            type: 'notice',
                            hide: true,
                            addclass: "octolapse",
                            desktop: {
                                desktop: true
                            }
                        };
                        Octolapse.displayPopup(options);
                    }
                    break;
                case "render-failed":
                    {
                        //console.log('octolapse.js - render-failed');
                        self.updateState(data);
                        var options = {
                            title: 'Octolapse Rendering Failed',
                            text: data.msg,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse",
                            desktop: {
                                desktop: true
                            }
                        };
                        Octolapse.displayPopup(options);
                        break;
                    }
                case "render-complete":
                    {
                        //console.log('octolapse.js - render-complete');
                    }
                    break;
                case "render-end":
                    {
                        //console.log('octolapse.js - render-end');
                        self.updateState(data);
                        if (!data.is_synchronized) {
                            // Make sure we aren't synchronized, else there's no reason to display a popup
                            if (!data.is_synchronized && data.success) {
                                var options = {
                                    title: 'Octolapse Rendering Complete',
                                    text: data.msg,
                                    type: 'success',
                                    hide: false,
                                    addclass: "octolapse",
                                    desktop: {
                                        desktop: true
                                    }
                                };
                                Octolapse.displayPopup(options);
                            }
                        }

                    }
                    break;
                case "synchronize-failed":
                    {
                        //console.log('octolapse.js - synchronize-failed');
                        var options = {
                            title: 'Octolapse Synchronization Failed',
                            text: data.msg,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse",
                            desktop: {
                                desktop: true
                            }
                        };
                        Octolapse.displayPopup(options);
                    }
                    break;
                case "timelapse-stopping":
                    {
                        //console.log('octolapse.js - timelapse-stoping');
                        Octolapse.Status.is_timelapse_active(false);
                        var options = {
                            title: 'Octolapse Timelapse Stopping',
                            text: data.msg,
                            type: 'notice',
                            hide: true,
                            addclass: "octolapse",
                            desktop: {
                                desktop: true
                            }
                        };
                        Octolapse.displayPopup(options);
                    }
                    break;
                case "timelapse-stopped":
                    {
                        //console.log('octolapse.js - timelapse-stopped');
                        Octolapse.Status.onTimelapseStop();

                        var options = {
                            title: 'Octolapse Timelapse Stopped',
                            text: data.msg,
                            type: 'notice',
                            hide: true,
                            addclass: "octolapse",
                            desktop: {
                                desktop: true
                            }
                        };
                        Octolapse.displayPopup(options);
                    }
                    break;
                case "disabled-running":
                    {
                        var options = {
                            title: 'Octolapse Disabled for Next Print',
                            text: data.msg,
                            type: 'notice',
                            hide: true,
                            addclass: "octolapse",
                            desktop: {
                                desktop: true
                            }
                        };
                        Octolapse.displayPopup(options);
                    }
                break;
                case "timelapse-stopped-error":
                    {
                        //console.log('octolapse.js - timelapse-stopped-error');
                        Octolapse.Status.onTimelapseStop();
                        var options = {
                            title: 'Octolapse Timelapse Stopped',
                            text: data.msg,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopup(options);
                    }
                    break;
                case "out-of-bounds":
                    {
                        //console.log("An out-of-bounds snapshot position was detected.")
                        var options = {
                            title: 'Octolapse - Out Of Bounds',
                            text: data.msg ,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options,"out-of-bounds");
                    }
                    break;
                case "position-error":
                    {
                        //console.log("An out-of-bounds snapshot position was detected.")
                        var options = {
                            title: 'Octolapse - Position Error',
                            text: data.msg,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(options, "position-error");
                    }
                    break;
                case "warning":
                    //console.log("A warning was sent to the plugin.")
                        var options = {
                            title: 'Octolapse - Warning',
                            text: data.msg,
                            type: 'notice',
                            hide: true,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopup(options, "warning");
                default:
                    {
                        //console.log('Octolapse.js - passing on message from server.  DataType:' + data.type);
                    }
            }
        };


    };
    OCTOPRINT_VIEWMODELS.push([
        OctolapseViewModel
        , ["loginStateViewModel", "printerStateViewModel"]
        , ["#octolapse"]
    ]);



});
