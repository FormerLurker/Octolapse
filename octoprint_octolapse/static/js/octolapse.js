
$(function () {
    Octolapse = this;
    // Finds the first index of an array with the matching predicate
    Octolapse.arrayFirstIndexOf = function (array, predicate, predicateOwner) {
        for (var i = 0, j = array.length; i < j; i++) {
            if (predicate.call(predicateOwner, array[i])) {
                return i;
            }
        }
        return -1;
    }
    // Creates a pseudo-guid
    Octolapse.guid = function () {
        function s4() {
            return Math.floor((1 + Math.random()) * 0x10000)
                .toString(16)
                .substring(1);
        }
        return s4() + s4() + '-' + s4() + '-' + s4() + '-' +
            s4() + '-' + s4() + s4() + s4();
    }

    // Retruns an observable sorted by name(), case insensitive
    Octolapse.nameSort = function (observable) {
        return observable().sort(
            function (left, right) {
                leftName = left.name().toLowerCase();
                rightName = right.name().toLowerCase();
                return leftName == rightName ? 0 : (leftName < rightName ? -1 : 1);
            });
    };
    // Toggles an element based on the data-toggle attribute.  Expects list of elements containing a selector, onClass and offClass.
    // It will apply the on or off class to the result of each selector, which should return exactly one result.
    Octolapse.toggle = function (caller, args) {
        var elements = args.elements;
        elements.forEach(function (item, index) {
            element = $(item.selector);
            onClass = item.onClass;
            offClass = item.offClass;
            if (element.hasClass(onClass)) {
                element.removeClass(onClass);
                element.addClass(offClass);
            } else {
                element.removeClass(offClass);
                element.addClass(onClass);
            }
        });
    };
    // Apply the toggle click event to every element within our settings that has the .toggle class

    Octolapse.displayPopup = function (options) {

        octolapsePopup = new PNotify(options);
    };
    Octolapse.ToggleElement = function (element) {
        var args = $(this).attr("data-toggle");
        Octolapse.toggle(this, JSON.parse(args));
    };
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
            return (i <= j) ? true : false;
        });
    $.validator.addMethod('greaterThanOrEqual',
        function (value, element, param) {
            var i = parseFloat(value);
            var j = parseFloat($(param).val());
            return (i >= j) ? true : false;
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
                val = target()
                if (val == null)
                    return Octolapse.NullNumericText
                return val.toFixed(precision);
            },
            write: target
        });

        result.raw = target;
        return result;
    };
    Octolapse.ToTime = function (seconds) {
        if (val == null)
            return Octolapse.NullTimeText
        var utcSeconds = seconds;
        var d = new Date(0); // The 0 there is the key, which sets the date to the epoch
        d.setUTCSeconds(utcSeconds);
        var time = d.getHours() + ":"
            + d.getMinutes() + ":"
            + d.getSeconds();
        return time;
    }

    Octolapse.ToTimer = function (seconds) {
        if (seconds == null)
            return "";
        if (seconds <= 0)
            return "0:00";

        hours = Math.floor(seconds / 3600);
        if (hours > 0) {
            return ("" + hours).slice(-2) + " Hrs"
        }
        
        seconds %= 3600;
        minutes = Math.floor(seconds / 60);
        seconds = seconds % 60;
        return ("0" + minutes).slice(-2) + ":" + ("0" + seconds).slice(-2);;
        
    }

    Octolapse.ToCompactInt = function (value) {
        var newValue = value;
        if (value >= 1000) {
            var suffixes = ["", "k", "m", "b", "t"];
            var suffixNum = Math.floor(("" + value).length / 3);
            var shortValue = '';
            for (var precision = 2; precision >= 1; precision--) {
                shortValue = parseFloat((suffixNum != 0 ? (value / Math.pow(1000, suffixNum)) : value).toPrecision(precision));
                var dotLessShortValue = (shortValue + '').replace(/[^a-zA-Z 0-9]+/g, '');
                if (dotLessShortValue.length <= 2) { break; }
            }
            if (shortValue % 1 != 0) shortNum = shortValue.toFixed(1);
            newValue = shortValue + suffixes[suffixNum];
        }
        return newValue;
    }


    Octolapse.NullTimeText = "none";
    ko.extenders.time = function (target, options) {
        var result = ko.dependentObservable({
            read: function () {
                val = target()
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
        Octolapse.PrinterStatus = parameters[1]
        // Global Values
        self.show_position_state_changes = ko.observable(false)
        self.show_position_changes = ko.observable(false)
        self.show_extruder_state_changes = ko.observable(false)
        self.show_trigger_state_changes = ko.observable(false)

        self.is_admin = ko.observable(false)
        self.enabled = ko.observable(false);
        self.navbar_enabled = ko.observable(false);
        // Create a guid to uniquely identify this client.
        self.client_id = Octolapse.guid()

        self.onBeforeBinding = function () {
            self.is_admin(self.loginState.isAdmin());
        };
        self.onAfterBinding = function () {
            self.loadState();
        };

        self.loadState = function () {
            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array
            $.ajax({
                url: "/plugin/octolapse/loadState",
                type: "POST",
                ccontentType: "application/json",
                dataType: "json",
                success: function (newSettings) {
                    console.log("Main Settings have been loaded.  Waiting for message");
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    alert("Unable to load the main settings tab.  Status: " + textStatus + ".  Error: " + errorThrown);
                }
            });
        };
        self.onUserLoggedIn = function (user) {
            console.log("octolapse.status.js - User Logged In.  User: " + user)
            self.is_admin(self.loginState.isAdmin());
        }
        self.onUserLoggedOut = function () {
            console.log("octolapse.status.js - User Logged Out")
            self.is_admin(false);
        }
        self.updateState = function (state) {
            if (state.Position != null) {
                console.log('octolapse.js - state-changed - Position');
                Octolapse.Status.updatePosition(state.Position);
            }
            if (state.PositionState != null) {
                console.log('octolapse.js - state-changed - Position State');
                Octolapse.Status.updatePositionState(state.PositionState);
            }
            if (state.Extruder != null) {
                console.log('octolapse.js - state-changed - Extruder State');
                Octolapse.Status.updateExtruderState(state.Extruder);
            }
            if (state.TriggerState != null) {
                console.log('octolapse.js - state-changed - Trigger State');
                Octolapse.Status.updateTriggerStates(state.TriggerState);
            }
            if (state.MainSettings != null) {
                console.log('octolapse.js - state-changed - Trigger State');
                Octolapse.SettingsMain.update(state.MainSettings);
                Octolapse.Globals.update(state.MainSettings);

            }
            if (state.Status != null) {
                console.log('octolapse.js - state-changed - Trigger State');
                Octolapse.Status.update(state.Status);
            }
        };
        self.update = function (settings) {
            // enabled
            if (ko.isObservable(settings.is_octolapse_enabled))
                self.enabled(settings.is_octolapse_enabled())
            else
                self.enabled(settings.is_octolapse_enabled)
            // navbar_enabled
            if (ko.isObservable(settings.show_navbar_icon))
                self.navbar_enabled(settings.show_navbar_icon())
            else
                self.navbar_enabled(settings.show_navbar_icon)

            if (ko.isObservable(settings.show_position_state_changes))
                self.show_position_state_changes(settings.show_position_state_changes())
            else
                self.show_position_state_changes(settings.show_position_state_changes)

            if (ko.isObservable(settings.show_position_changes))
                self.show_position_changes(settings.show_position_changes())
            else
                self.show_position_changes(settings.show_position_changes)

            if (ko.isObservable(settings.show_extruder_state_changes))
                self.show_extruder_state_changes(settings.show_extruder_state_changes())
            else
                self.show_extruder_state_changes(settings.show_extruder_state_changes)

            if (ko.isObservable(settings.show_trigger_state_changes))
                self.show_trigger_state_changes(settings.show_trigger_state_changes())
            else
                self.show_trigger_state_changes(settings.show_trigger_state_changes)

        };
        // Handle Plugin Messages from Server
        self.onDataUpdaterPluginMessage = function (plugin, data) {
            if (plugin != "octolapse") {
                return;
            }
            switch (data.type) {
                case "settings-changed":
                    // (update the main settings)
                    if (self.client_id != data.client_id) {
                        Octolapse.Status.loadStatus();
                        if (self.is_admin()) {
                            console.log('octolapse - settings-changed, reloading');
                            Octolapse.Settings.loadSettings();
                            var options = {
                                title: 'Octolapse',
                                text: "A profile change was detected from another client.",
                                type: 'notice',
                                hide: true,
                                desktop: {
                                    desktop: true
                                }
                            };
                            Octolapse.displayPopup(options);
                        }
                    }
                    else {
                        console.log('octolapse.js - settings-changed, ignoring - came from self or not signed in.');
                    }
                    break;
                case "state-loaded":
                    console.log('octolapse.js - state-changed');
                    self.updateState(data);
                    break;
                case "state-changed":
                    console.log('octolapse.js - state-changed');
                    self.updateState(data);
                    break;
                case "popup":
                    console.log('octolapse.js - popup');
                    var options = {
                        title: 'Octolapse Notice',
                        text: data.msg,
                        type: 'notice',
                        hide: true,
                        desktop: {
                            desktop: true
                        }
                    };
                    Octolapse.displayPopup(options);
                    break;
                case "timelapse-start":
                    console.log('octolapse.js - timelapse-start');
                    /*
                    Octolapse.Status.is_timelapse_active(true);
                    Octolapse.Status.is_taking_snapshot(false);
                    Octolapse.Status.is_rendering(false);
                    Octolapse.Status.snapshot_count(0);
                    Octolapse.Status.seconds_added_by_octolapse(0)
                    Octolapse.Status.snapshot_error(false);
                    Octolapse.Status.snapshot_error_message("");
                    */
                    self.updateState(data);
                    break;
                case "timelapse-complete":
                    console.log('octolapse.js - timelapse-complete');
                    Octolapse.Status.is_timelapse_active(false);
                    Octolapse.Status.is_taking_snapshot(false);
                    Octolapse.Status.ClearAllStates();
                    break;
                case "snapshot-start":
                    console.log('octolapse.js - snapshot-start');
                    Octolapse.Status.is_taking_snapshot(true);
                    Octolapse.Status.snapshot_error(false);
                    Octolapse.Status.snapshot_error_message("");
                    break;
                case "snapshot-complete":
                    console.log('octolapse.js - snapshot-complete');
                    Octolapse.Status.snapshot_count(data.snapshot_count)
                    Octolapse.Status.seconds_added_by_octolapse(data.seconds_added_by_octolapse)
                    Octolapse.Status.snapshot_error(!data.success);
                    Octolapse.Status.snapshot_error_message(data.error);
                    Octolapse.Status.is_taking_snapshot(false);
                    break;
                case "render-start":
                    console.log('octolapse.js - render-start');
                    Octolapse.Status.snapshot_count(data.snapshot_count)
                    Octolapse.Status.seconds_added_by_octolapse(data.seconds_added_by_octolapse)
                    Octolapse.Status.is_rendering(true);
                    var options = {
                        title: 'Octolapse Rendering Started',
                        text: data.msg,
                        type: 'notice',
                        hide: true,
                        desktop: {
                            desktop: true
                        }
                    };
                    Octolapse.displayPopup(options);
                    break;
                case "render-failed":
                    console.log('octolapse.js - render-failed');
                    var options = {
                        title: 'Octolapse Rendering Failed',
                        text: data.msg,
                        type: 'error',
                        hide: false,
                        desktop: {
                            desktop: true
                        }
                    };
                    Octolapse.displayPopup(options);
                    break;
                case "render-complete":
                    console.log('octolapse.js - render-complete');
                    break;
                case "render-end":
                    console.log('octolapse.js - render-end');
                    Octolapse.Status.is_rendering(false);
                    // Make sure we aren't synchronized, else there's no reason to display a popup
                    if (!data.is_synchronized && data.success) {
                        var options = {
                            title: 'Octolapse Rendering Complete',
                            text: data.msg,
                            type: 'success',
                            hide: false,
                            desktop: {
                                desktop: true
                            }
                        };
                        Octolapse.displayPopup(options);
                    }
                    break;
                case "synchronize-failed":
                    console.log('octolapse.js - synchronize-failed');
                    var options = {
                        title: 'Octolapse Synchronization Failed',
                        text: data.msg,
                        type: 'error',
                        hide: false,
                        desktop: {
                            desktop: true
                        }
                    };
                    Octolapse.displayPopup(options);
                    break;
                case "timelapse-stopping":
                    console.log('octolapse.js - timelapse-stoping');
                    Octolapse.Status.is_timelapse_active(false);
                    var options = {
                        title: 'Octolapse Timelapse Stopping',
                        text: data.msg,
                        type: 'notice',
                        hide: true,
                        desktop: {
                            desktop: true
                        }
                    };
                    Octolapse.displayPopup(options);
                    break;
                case "timelapse-stopped":
                    console.log('octolapse.js - timelapse-stopped');
                    Octolapse.Status.is_timelapse_active(false);
                    Octolapse.Status.is_taking_snapshot(false);
                    var options = {
                        title: 'Octolapse Timelapse Stopped',
                        text: data.msg,
                        type: 'notice',
                        hide: true,
                        desktop: {
                            desktop: true
                        }
                    };
                    Octolapse.displayPopup(options);
                    break;
                default:
                    console.log('Octolapse.js - passing on message from server.  DataType:' + data.type);
                    break;
            }
        };
    }
    OCTOPRINT_VIEWMODELS.push([
        OctolapseViewModel
        , ["loginStateViewModel", "printerStateViewModel"]
        , ["#octolapse"]
    ]);



});
