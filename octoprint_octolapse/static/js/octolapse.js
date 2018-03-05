/*
    This file is subject to the terms and conditions defined in
    a file called 'LICENSE', which is part of this source code package.
*/
Octolapse = {};
OctolapseViewModel = {};

$(function () {
    // Finds the first index of an array with the matching predicate
    Octolapse.IsShowingSettingsChangedPopup = false;
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
    // Apply the toggle click event to every element within our settings that has the .toggle class

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

    Octolapse.DisableResumeButton = function(){
        var stateWrapper = $("#state_wrapper");
        stateWrapper.find("#job_pause").attr("disabled", "disabled");
        stateWrapper.find("#job_pause span:nth-of-type(1)").text("Snapshot");
        stateWrapper.find("#job_pause span:nth-of-type(2)").text("Snapshot");
    };
    Octolapse.EnableResumeButton = function () {
        var stateWrapper = $("#state_wrapper");
        stateWrapper.find("#job_pause").attr("disabled", "");
        stateWrapper.find("#job_pause span:nth-of-type(1)").text("Pause");
        stateWrapper.find("#job_pause span:nth-of-type(2)").text("Resume");
    };
    // Add custom validator for csv strings (no inner whitespace)
    const csvStringRegex = /^(\s*[A-Z]\d+\s*(?:$|,))+$/gim;
    const csvStringComponentRegex = /[A-Z]\d+/gim;
    $.validator.addMethod('csvString', function (value) {
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
            if ($target.size() === 0)
                return true;
            var j = parseFloat($target.val());
            return (i < j);
        });
    $.validator.addMethod('greaterThan',
        function (value, element, param) {
            var i = parseFloat(value);
            var $target = $(param);

            // I we didn't find a target, return true
            if ($target.size() === 0)
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
        // Create a guid to uniquely identify this client.
        self.client_id = Octolapse.guid();
        // Have we loaded the state yet?
        self.HasLoadedState = false;


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
                tryCount: 0,
                retryLimit: 3,
                ccontentType: "application/json",
                dataType: "json",
                success: function (result) {
                    //console.log("Main Settings have been loaded.  Waiting for message");

                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {

                    alert("Octolapse could not load the current state.  Please try again in a few minutes, or check plugin_octolapse.log in the 'Logs' menu for exceptions.");
                }
            });
        };
        self.onUserLoggedIn = function (user) {
            //console.log("octolapse.status.js - User Logged In.  User: " + user)
            self.is_admin(self.loginState.isAdmin());
        };
        self.onUserLoggedOut = function () {
            //console.log("octolapse.status.js - User Logged Out")
            self.is_admin(false);
        };
        self.onEventPrintResumed = function (payload) {
            Octolapse.EnableResumeButton()
        };
        self.onEventPrintCancelled = function (payload) {
            Octolapse.EnableResumeButton()
        };
        self.onEventPrintFailed = function (payload) {
            Octolapse.EnableResumeButton()
        };
        self.onEventPrintDone = function (payload) {
            Octolapse.EnableResumeButton()
        };
        self.updateState = function (state) {

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
                            desktop: {
                                desktop: true
                            }
                        };
                        Octolapse.displayPopup(options);
                    }
                    break;
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
                        Octolapse.DisableResumeButton();
                        Octolapse.Status.snapshot_error(false);
                        Octolapse.Status.snapshot_error_message("");
                    }
                    break;
                case "snapshot-complete":
                    {
                        //console.log('octolapse.js - snapshot-complete');

                        self.updateState(data);
                        Octolapse.Status.snapshot_error(!data.success);
                        Octolapse.Status.snapshot_error_message(data.error);
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
                            desktop: {
                                desktop: true
                            }
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
                            hide: false
                        };
                        Octolapse.displayPopupForKey(options,"out-of-bounds");
                    }
                    break;
                case "position-error":
                    {
                        //console.log("An out-of-bounds snapshot position was detected.")
                        var options = {
                            title: 'Octolapse - Out Of Bounds',
                            text: data.msg,
                            type: 'error',
                            hide: false
                        };
                        Octolapse.displayPopupForKey(options, "position-error");
                    }
                    break;
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
