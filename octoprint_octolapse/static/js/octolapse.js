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

                    if(options.toggle_observable) {
                        Octolapse.toggleContentFunction($elm, options, false);
                    }


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

     // Create Helpers
    Octolapse.convertAxisSpeedUnit = function (speed, newUnit, previousUnit, tolerance, tolerance_unit){
        if (speed == null)
            return null;
        if(tolerance_unit != newUnit)
        {
            switch (newUnit){
                case "mm-min":
                    tolerance = tolerance * 60.0;
                case "mm-sec":
                    tolerance = tolerance / 60.0;
            }
        }
        if(newUnit == previousUnit)
            return Octolapse.roundToIncrement(speed, tolerance);

        switch (newUnit){
            case "mm-min":
                return Octolapse.roundToIncrement(speed*60.0, tolerance);
            case "mm-sec":
                return Octolapse.roundToIncrement(speed/60.0, tolerance);
        }
        return null;
    };


    // rounding to an increment
    Octolapse.roundToIncrement = function (num, increment) {
        if (increment == 0)
            return 0;
        if (num == null)
            return null;

        if (num != parseFloat(num))
            return num;

        var div = Math.round(num / increment);
        var value = increment * div

        // Find the number of decimals in the increment
        var numDecimals = 0;
        if ((increment % 1) != 0)
            numDecimals = increment.toString().split(".")[1].length;

        // tofixed can only support 20 decimals, reduce if necessary
        if(numDecimals > 20) {
            //console.log("Too much precision for tofixed:" + numDecimals + " - Reducing to 20");
            numDecimals = 20;
        }
        // truncate value to numDecimals decimals
        value = parseFloat(value.toFixed(numDecimals).toString())

        return value;
    }

    Octolapse.Popups = {};
    Octolapse.displayPopupForKey = function (options, key) {
        if (key in Octolapse.Popups) {
            Octolapse.Popups[key].remove();
        }
        Octolapse.Popups[key] = new PNotify(options);
    };

    Octolapse.ConfirmDialogs = {};
    Octolapse.showConfirmDialog = function(key, title, text, onConfirm, onCancel)
    {
        if (key in Octolapse.ConfirmDialogs) {
            Octolapse.ConfirmDialogs[key].remove();
        }
        Octolapse.ConfirmDialogs[key] = (
            new PNotify({
                title: title,
                text: text,
                icon: 'fa fa-question',
                hide: false,
                addclass: "octolapse",
                confirm: {
                    confirm: true
                },
                buttons: {
                    closer: false,
                    sticker: false
                },
                history: {
                    history: false
                }
            })
        ).get().on('pnotify.confirm', onConfirm).on('pnotify.cancel', onCancel);
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

    Octolapse.isPercent = function(value){

        if(typeof value != 'string')
            return false;
        if (!value)
            return false;
        var value = value.trim();
        if(value.length > 1 && value[value.length-1] == "%")
            value = value.substr(0,value.length-2);
        else
            return false;

        return Octolapse.isFloat(value)
    };
    Octolapse.isFloat = function(value){
        if (!value)
            return false;
        return !isNaN(parseFloat(value))
    };

    Octolapse.parseFloat = function(value){
        var ret = parseFloat(value);
        if(!isNaN(ret))
            return ret;
        return null;
    };

    Octolapse.parsePercent = function(value){
        var value = value.trim();
        if(value.length > 1 && value[value.length-1] == "%")
            value = value.substr(0,value.length-1);
        else
            return null;
        return Octolapse.parseFloat(value)
    }

    $.validator.addMethod('slic3rPEFloatOrPercent',
        function (value) {
            if (!value)
                return true;
            if(!Octolapse.isPercent(value) && !Octolapse.isFloat(value))
            {
                return false;
            }
            return true;
        }, 'Please enter a decimal or a percent.');

    $.validator.addMethod('slic3rPEFloatOrPercentSteps',
        function (value) {
            if (!value)
                return true;
            if(Octolapse.isPercent(value))
                value = Octolapse.parsePercent(value);
            else if(Octolapse.isFloat(value))
                value = Octolapse.parseFloat(value);
            var rounded_value = Octolapse.roundToIncrement(value, 0.0001);
            if (rounded_value == value)
                return true;
            return false

        }, 'Please enter a multiple of 0.0001.');

    // Add a custom validator for positive
    $.validator.addMethod('integerPositive',
        function (value) {
            try {
                var r = /^\d+$/.test(value); // Check the number against a regex to ensure it contains only digits.
                var n = +value; // Try to convert to number.
                return r && !isNaN(n) && n > 0 && n % 1 == 0;
            } catch (e) {
                return false;
            }
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

    Octolapse.round_axis_speed_unit = function (val, options) {
        var round_to_increment_mm_min = options.round_to_increment_mm_min;
        var round_to_increment_mm_sec = options.round_to_increment_mm_sec;
        var current_units_observable = options.current_units_observable;
        var round_to_percent = options.round_to_percent;
        var return_text = options.return_text || false;

        if (val == null)
            return null;

        // Check to see if it is a percent
        var is_percent = Octolapse.isPercent(val)
        if(is_percent)
        {
            if(round_to_percent)
            {
                val = Octolapse.parsePercent(val);
            }
            else
                return null;
        }
        else
            val = Octolapse.parseFloat(val)

        if (val == null || isNaN(val))
            return null;
        try{
            var round_to_increment = round_to_increment_mm_min;
            if (is_percent) {
                round_to_increment = round_to_percent
            }
            else if (current_units_observable() == 'mm-sec') {
                round_to_increment = round_to_increment_mm_sec;
            }
            var rounded = Octolapse.roundToIncrement(val, round_to_increment);
            if(is_percent && return_text)
                return rounded.toString() + "%";
            else if (return_text)
                return rounded.toString();
            return rounded;
        }
        catch (e){
            console.log("Error rounding axis_speed_unit");
        }

    };

    ko.extenders.axis_speed_unit = function (target, options) {
        //console.log("rounding to axis speed units");
        var result = ko.pureComputed({
            read: target,
            write: function (newValue) {
                var current = target();
                var valueToWrite = Octolapse.round_axis_speed_unit(newValue, options);
                //only write if it changed
                if (valueToWrite !== current) {
                    target(valueToWrite);
                } else {
                    //if the rounded value is the same, but a different value was written, force a notification for the current field
                    if (newValue !== current) {
                        target.notifySubscribers(valueToWrite);
                    }
                }

            }
        }).extend({ notify: 'always' });

        result(target());

        return result;
    };

    ko.extenders.round_to_increment = function (target, options) {
        //console.log("rounding to axis speed units");
        var round_to_increment = options.round_to_increment;
        var result = ko.pureComputed({
            read: target,
            write: function (newValue) {
                var current = target();
                var valueToWrite = Octolapse.roundToIncrement(newValue, round_to_increment);
                //only write if it changed
                if (valueToWrite !== current) {
                    target(valueToWrite);
                } else {
                    //if the rounded value is the same, but a different value was written, force a notification for the current field
                    if (newValue !== current) {
                        target.notifySubscribers(valueToWrite);
                    }
                }

            }
        }).extend({ notify: 'always' });

        result(target());

        return result;
    };

    ko.extenders.numeric = function (target, precision) {
        var result = ko.dependentObservable({
            read: function () {
                var val = target();
                val = Octolapse.parseFloat(val)
                if (val == null)
                    return val;
                try{
                    // safari doesn't seem to like toFixed with a precision > 20
                    if(precision > 20)
                        precision = 20;
                    return val.toFixed(precision);
                }
                catch (e){
                    console.log("Error converting toFixed");
                }

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
        self.cancel_print_on_startup_error = ko.observable(true);

        self.version = ko.observable("unknown");
        // Create a guid to uniquely identify this client.
        self.client_id = Octolapse.guid();
        // Have we loaded the state yet?
        self.HasLoadedState = false;


        self.onBeforeBinding = function () {
            self.is_admin(self.loginState.isAdmin());
        };

        self.startup_complete = false;
        self.onStartupComplete = function () {
            //console.log("Startup Complete")
            self.getInitialState();
            self.startup_complete = true;

        };
        self.onDataUpdaterReconnect = function () {
            //console.log("Reconnected Client")
            self.getInitialState();

        };

        self.getInitialState = function(){
            //console.log("Getting initial state");
            if(!self.startup_complete && self.is_admin()) {
                //console.log("octolapse.js - Loading settings for current user after startup.");
                Octolapse.Settings.loadSettings();
            }
            self.loadState();
            // reset snapshot error state
            Octolapse.Status.snapshot_error(false);
            //console.log("Finished loading initial state.");

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
                    self.initial_state_loaded = true;
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {

                    //console.log("Octolapse was unable to retrieve the current state, trying again in 5 seconds");
                    setTimeout(self.getInitialState, 5000);
                    // Todo:  update the UI to show we're waiting for our state!
                }
            });
        };


        self.onUserLoggedIn = function (user) {
            self.is_admin(self.loginState.isAdmin());
            if(self.is_admin() && self.startup_complete) {
                //console.log("octolapse.js - User Logged In after startup - Loading settings.  User: " + user.name);
                Octolapse.Settings.loadSettings();
            }
            //else
            //    console.log("octolapse.js - User Logged In before startup - waiting to load settings.  User: " + user.name);
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

            if (ko.isObservable(settings.cancel_print_on_startup_error))
                self.cancel_print_on_startup_error(settings.cancel_print_on_startup_error());
            else
                self.cancel_print_on_startup_error(settings.cancel_print_on_startup_error)



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
                            Octolapse.showConfirmDialog(
                                "reload-settings",
                                "Reload Settings",
                                "A settings change was detected from another client.  Reload settings?",
                                function(){
                                    Octolapse.Settings.loadSettings();
                                });
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
                            title: 'Error',
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
                case "print-start-error":
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
                        Octolapse.displayPopupForKey(options,"print-start-error")
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
                        Octolapse.Status.snapshot_error(false);
                    }
                    break;
                case "timelapse-complete":
                    {
                        //console.log('octolapse.js - timelapse-complete');
                        self.updateState(data)
                    }
                    break;
                case "camera-settings-error":
                    // If only the camera image acquisition failed, use the camera error message
                    var options = {
                        title: 'Octolapse - Camera Settings Error',
                        text: data.msg,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse"
                    };
                    Octolapse.displayPopupForKey(options, "snapshot_error");
                    break;
                case "snapshot-start":
                    {
                        //console.log('octolapse.js - snapshot-start');
                        self.updateState(data);
                        Octolapse.Status.snapshot_error(false);
                    }
                    break;
                case "snapshot-complete":
                    {
                        //console.log('octolapse.js - snapshot-complete');
                        //console.log(data);
                        self.updateState(data);

                        Octolapse.Status.snapshot_error(data.error || data.snapshot_error);
                        if(!data.snapshot_success)
                        {
                            // If only the camera image acquisition failed, use the camera error message
                            Octolapse.Status.snapshot_error(true);
                            var options = {
                                title: 'Octolapse - Camera Error',
                                text: data.snapshot_error,
                                type: 'error',
                                hide: false,
                                addclass: "octolapse"
                            };
                            Octolapse.displayPopupForKey(options, "snapshot_error")
                        }
                        else if(!data.success)
                        {
                            var options = {
                                title: 'Octolapse - Stabilization Error',
                                text: data.error,
                                type: 'error',
                                hide: false,
                                addclass: "octolapse"
                            };
                            Octolapse.displayPopupForKey(options, "stabilization_error")
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
                        Octolapse.Status.snapshot_error(false);

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
                case "render-failed":{
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
                case "before-after-render-error": {
                    // If only the camera image acquisition failed, use the camera error message
                    var options = {
                        title: 'Octolapse - Before/After Render Script Error',
                        text: data.msg,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse"
                    };
                    Octolapse.displayPopupForKey(options, "before_after_render_script_error");
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
                        Octolapse.Status.snapshot_error(false);
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
