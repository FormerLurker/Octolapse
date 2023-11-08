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
Octolapse = {};
Octolapse.Printers = {
    'current_profile_guid': function () {
        return null;
    }
};
OctolapseViewModel = {};
//UI_API_KEY = "";
Octolapse.Help = null;

$(function () {
    // Finds the first index of an array with the matching predicate
    Octolapse.IsShowingSettingsChangedPopup = false;

    Octolapse.toggleContentFunction = function ($elm, options, updateObservable) {

        if (options.toggle_observable) {
            //console.log("Toggling element.");
            if (updateObservable) {
                options.toggle_observable(!options.toggle_observable());
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
                if (options.container) {
                    if (options.parent) {
                        $elm.parents(options.parent).find(options.container).stop().slideDown('fast', options.onComplete);
                    } else {
                        $(options.container).stop().slideDown('fast', options.onComplete);
                    }
                }
            } else {
                if (options.class_hiding) {
                    $elm.children('[class^="icon-"]').addClass(options.class_hiding);
                    $elm.children('[class^="fa"]').addClass(options.class_hiding);
                }
                if (options.class_showing) {
                    $elm.children('[class^="icon-"]').removeClass(options.class_showing);
                    $elm.children('[class^="fa"]').removeClass(options.class_showing);
                }
                if (options.container) {
                    if (options.parent) {
                        $elm.parents(options.parent).find(options.container).stop().slideUp('fast', options.onComplete);
                    } else {
                        $(options.container).stop().slideUp('fast', options.onComplete);
                    }
                }
            }
        } else {
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
        init: function (element, valueAccessor) {
            var $elm = $(element),
                options = $.extend({
                    class_showing: null,
                    class_hiding: null,
                    container: null,
                    parent: null,
                    toggle_observable: null,
                    onComplete: function () {
                        $(document).trigger("slideCompleted");
                    }
                }, valueAccessor());

            if (options.toggle_observable) {
                Octolapse.toggleContentFunction($elm, options, false);
            }


            $elm.on("click", function (e) {
                e.preventDefault();
                Octolapse.toggleContentFunction($elm, options, true);

            });
        }
    };
    ko.bindingHandlers.octolapseToggle = Octolapse.toggleContent;

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
    Octolapse.observableNameSort = function (observable) {
        return observable().sort(
            function (left, right) {
                var leftName = left.name().toLowerCase();
                var rightName = right.name().toLowerCase();
                return leftName === rightName ? 0 : (leftName < rightName ? -1 : 1);
            }
        );
    };

    Octolapse.nameSort = function (array_to_sort) {
        return array_to_sort.sort(
            function (left, right) {
                var leftName = left.name.toLowerCase();
                var rightName = right.name.toLowerCase();
                return leftName === rightName ? 0 : (leftName < rightName ? -1 : 1);
            }
        );
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

    Octolapse.progressBar = function (cancel_callback, initial_text) {
        var self = this;
        self.notice = null;
        self.$progress = null;
        self.$progressText = null;
        self.initial_text = initial_text;
        self.popup_margin = 15;
        self.popup_width_with_margin = 400;
        self.popup_width = self.popup_width_with_margin - self.popup_margin*2;

        self.close = function () {
            if (self.loader != null)
                self.loader.remove();
        };

        self.update = function (percent_complete, progress_text) {
            self.notice.find(".remove_button").remove();

            if (self.$progress == null)
                return null;
            if (percent_complete < 0)
                percent_complete = 0;
            if (percent_complete > 100)
                percent_complete = 100;
            if (percent_complete === 100) {
                //console.log("Received 100% complete progress message, removing progress bar.");
                self.loader.remove();
                return null;
            }
            var percent_complete_text = percent_complete.toFixed(1);
            self.$progress.width(percent_complete_text + "%").attr("aria-valuenow", percent_complete_text).find("span").html(percent_complete_text + "%");
            self.$progressText.text(progress_text);
            return self;
        };
        self.loader = null;
        // create the pnotify loader
        self.loader = new PNotify({
            title: "Preprocessing Gcode File",
            text: '<div class="progress progress-striped active" style="margin:0">\
      <div class="progress-bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0"></div>\
    </div><div><span class="progress-text"></span></div>',
            icon: 'fa fa-cog fa-spin',
            width: self.popup_width.toString() + "px",
            confirm: {
                confirm: Octolapse.Globals.is_admin(),
                buttons: [{
                    text: 'Cancel',
                    click: cancel_callback
                }, {
                    text: 'Close',
                    addClass: 'remove_button',
                    click: cancel_callback
                }]
            },
            buttons: {
                closer: false,
                sticker: false
            },
            hide: false,
            history: {
                history: false
            },
            before_open: function (notice) {
                self.notice = notice.get();
                self.$progress = self.notice.find("div.progress-bar");
                self.$progressText = self.notice.find("span.progress-text");
                self.notice.find(".remove_button").remove();
                self.update(0, self.initial_text);
            }
        });

        return self;

    };
    // Cookies (only for UI display purposes, not for any tracking
    Octolapse.COOKIE_EXPIRE_DAYS = 30;

    Octolapse.setLocalStorage = function (name, value) {
        localStorage.setItem("octolapse_" + name, value);
    };

    Octolapse.getLocalStorage = function (name, value) {
        return localStorage.getItem("octolapse_" + name);
    };

    Octolapse.replaceAll = function (str, find, replace) {
        return str.replace(new RegExp(find, 'g'), replace);
    };

    Octolapse.displayPopup = function (options) {
        new PNotify(options);
    };

    // Create Helpers
    Octolapse.convertAxisSpeedUnit = function (speed, newUnit, previousUnit, tolerance, tolerance_unit) {
        if (speed == null)
            return null;
        if (tolerance_unit !== newUnit) {
            switch (newUnit) {
                case "mm-min":
                    tolerance = tolerance * 60.0;
                    break;
                case "mm-sec":
                    tolerance = tolerance / 60.0;
                    break;
            }
        }
        if (newUnit === previousUnit)
            return Octolapse.roundToIncrement(speed, tolerance);

        switch (newUnit) {
            case "mm-min":
                return Octolapse.roundToIncrement(speed * 60.0, tolerance);
            case "mm-sec":
                return Octolapse.roundToIncrement(speed / 60.0, tolerance);
        }
        return null;
    };


    // rounding to an increment
    Octolapse.roundToIncrement = function (num, increment) {
        if (increment === 0)
            return 0;
        if (num == null)
            return null;

        if (num !== parseFloat(num))
            return num;

        var div = Math.round(num / increment);
        var value = increment * div;

        // Find the number of decimals in the increment
        var numDecimals = 0;
        if ((increment % 1) !== 0)
            numDecimals = increment.toString().split(".")[1].length;

        // tofixed can only support 20 decimals, reduce if necessary
        if (numDecimals > 20) {
            //console.log("Too much precision for tofixed:" + numDecimals + " - Reducing to 20");
            numDecimals = 20;
        }
        // truncate value to numDecimals decimals
        value = parseFloat(value.toFixed(numDecimals).toString());

        return value;
    };

    Octolapse.Popups = {};
    Octolapse.displayPopupForKey = function (options, popup_key, remove_keys) {
        Octolapse.closePopupsForKeys(remove_keys);
        var popup = new PNotify(options);
        Octolapse.Popups[popup_key] = popup;
        return popup;
    };

    Octolapse.closePopupsForKeys = function (remove_keys) {
        if (!$.isArray(remove_keys)) {
            remove_keys = [remove_keys];
        }
        for (var index = 0; index < remove_keys.length; index++) {
            var key = remove_keys[index];
            if (key in Octolapse.Popups) {
                var notice = Octolapse.Popups[key];
                if (notice.state === "opening") {
                    notice.options.animation = "none";
                }
                notice.remove();
                delete Octolapse.Popups[key];
            }
        }
    };

    Octolapse.removeKeyForClosedPopup = function (key) {
        if (key in Octolapse.Popups) {
            var notice = Octolapse.Popups[key];
            delete Octolapse.Popups[key];
        }
    };

    Octolapse.checkPNotifyDefaultConfirmButtons = function () {
        // check to see if exactly two default pnotify confirm buttons exist.
        // If we keep running into problems we might need to inspect the buttons to make sure they
        // really are the defaults.
        if (PNotify.prototype.options.confirm.buttons.length !== 2) {
            // Someone removed the confirmation buttons, darnit!  Report the error and re-add the buttons.
            var message = "Octolapse detected the removal or addition of PNotify default confirmation buttons, " +
                "which should not be done in a shared environment.  Some plugins may show strange behavior.  Please " +
                "report this error at https://github.com/FormerLurker/Octolapse/issues.  Octolapse will now clear " +
                "and re-add the default PNotify buttons.";
            console.error(message);

            // Reset the buttons in case extra buttons were added.
            PNotify.prototype.options.confirm.buttons = [];

            var buttons = [
                {
                    text: "Ok",
                    addClass: "",
                    promptTrigger: true,
                    click: function (b, a) {
                        b.remove();
                        b.get().trigger("pnotify.confirm", [b, a]);
                    }
                },
                {
                    text: "Cancel",
                    addClass: "",
                    promptTrigger: true,
                    click: function (b) {
                        b.remove();
                        b.get().trigger("pnotify.cancel", b);
                    }
                }
            ];
            PNotify.prototype.options.confirm.buttons = buttons;
        }
    };

    Octolapse.ConfirmDialogs = {};
    Octolapse.closeConfirmDialogsForKeys = function (remove_keys) {
        if (!$.isArray(remove_keys)) {
            remove_keys = [remove_keys];
        }
        for (var index = 0; index < remove_keys.length; index++) {
            var key = remove_keys[index];
            if (key in Octolapse.ConfirmDialogs) {

                Octolapse.ConfirmDialogs[key].remove();
                delete Octolapse.ConfirmDialogs[key];
            }
        }
    };

    Octolapse.showConfirmDialog = function (key, title, text, onConfirm, onCancel, onComplete, onOption, optionButtonText) {
        Octolapse.closeConfirmDialogsForKeys([key]);
        // Make sure that the default pnotify buttons exist
        Octolapse.checkPNotifyDefaultConfirmButtons();
        options = {
            title: title,
            text: text,
            icon: 'fa fa-question',
            hide: false,
            addclass: "octolapse",
            confirm: {
                confirm: true,
            },
            buttons: {
                closer: false,
                sticker: false
            },
            history: {
                history: false
            }
        };
        if (onOption && optionButtonText) {
            var confirmButtons = [
                {
                    text: "Ok",
                    addClass: "",
                    promptTrigger: true,
                    click: function (b, a) {
                        b.remove();
                        b.get().trigger("pnotify.confirm", [b, a]);
                    }
                },
                {
                    text: optionButtonText,
                    click: function () {
                        if (onOption)
                            onOption();
                        if (onComplete)
                            onComplete();
                        Octolapse.closeConfirmDialogsForKeys([key]);
                    }
                },
                {
                    text: "Cancel",
                    addClass: "",
                    promptTrigger: true,
                    click: function (b) {
                        b.remove();
                        b.get().trigger("pnotify.cancel", b);
                    }
                }
            ];
            options.confirm.buttons = confirmButtons;
        }
        Octolapse.ConfirmDialogs[key] = (
            new PNotify(options)
        ).get().on('pnotify.confirm', function () {
            if (onConfirm)
                onConfirm();
            if (onComplete) {
                onComplete();
            }
        }).on('pnotify.cancel', function () {
            if (onCancel)
                onCancel();
            if (onComplete) {
                onComplete();
            }
        });
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

    $.validator.addMethod("uploadFileRequired", function (value, element, callback) {
        //console.log("Validating upload file.");
        if (callback != null)
            return callback[0]();
        return element.files.length > 0 && element.files[0].size > 0;

    }, "You must select a file.");

    $.validator.addMethod("check_one", function (value, elem, param) {
        //console.log("Validating trigger checks");
        $(param).val();
        return $(param + ":checkbox:checked").length > 0;
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

    Octolapse.isPercent = function (value) {
        //console.log("is percent - Octolapse")
        if (typeof value !== 'string')
            return false;
        if (!value)
            return false;
        value = value.trim();
        if (!(value.length > 1 && value[value.length - 1] === "%"))
            return false;
        value = value.substr(0, value.length - 1);
        return Octolapse.isFloat(value);
    };
    Octolapse.isFloat = function (value) {
        if (!value)
            return false;
        return !isNaN(value) && !isNaN(parseFloat(value));
    };

    Octolapse.parseFloat = function (value) {
        var ret = parseFloat(value);
        if (!isNaN(ret))
            return ret;
        return null;
    };

    Octolapse.parsePercent = function (value) {
        value = value.trim();
        if (value.length > 1 && value[value.length - 1] === "%")
            value = value.substr(0, value.length - 1);
        else
            return null;
        return Octolapse.parseFloat(value);
    };

    $.validator.addMethod('slic3rPEFloatOrPercent',
        function (value) {
            if (!value)
                return true;
            if (!Octolapse.isPercent(value) && !Octolapse.isFloat(value)) {
                return false;
            }
            return true;
        }, 'Please enter a decimal or a percent.');

    $.validator.addMethod('slic3rPEFloatOrPercentSteps',
        function (value) {
            if (!value)
                return true;
            if (Octolapse.isPercent(value))
                value = Octolapse.parsePercent(value);
            else if (Octolapse.isFloat(value))
                value = Octolapse.parseFloat(value);
            var rounded_value = Octolapse.roundToIncrement(value, 0.0001);
            if (rounded_value === value)
                return true;
            return false;

        }, 'Please enter a multiple of 0.0001.');

    // Add a custom validator for positive
    $.validator.addMethod('integerPositive',
        function (value) {
            try {
                var r = /^\d+$/.test(value); // Check the number against a regex to ensure it contains only digits.
                var n = +value; // Try to convert to number.
                return r && !isNaN(n) && n > 0 && n % 1 === 0;
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

    // Validator that returns true if the value is not null and all
    // selectors values are also not null
    $.validator.addMethod('ifCheckedEnsureNonNull',
        function (value, element, param) {
            //console.log("ifCheckedEnsureNonNull");
            if (value === "on")
                for (var index = 0; index < param.length; index++) {
                    // Get the target selector
                    var $target = $(param[index]);
                    // If we found no target return false
                    if ($target.length === 0)
                        return false;
                    var targetVal = $target.val();
                    if (targetVal == null || targetVal === '')
                        return false;
                }
            return true;
        });

    // Validator that returns true if the value is not null and all
    // selectors values are also not null
    $.validator.addMethod('ifOtherCheckedEnsureNonNull',
        function (value, element, param) {
            // see if the target is checked
            var target_checked = $(param + ":checkbox:checked").length > 0;
            if (target_checked)
                return value != null && value !== '';
            return true;
        });

    $.validator.addMethod('octolapseSnapshotTemplate',
        function (value, element) {
            var testUrl = value.toUpperCase().replace("{CAMERA_ADDRESS}", 'http://w.com/');
            var is_valid = (
                $.validator.methods.url.call(this, testUrl, element) ||
                $.validator.methods.url.call(this, "http://w.com" + testUrl, element)
            );
            return is_valid;
        });

    $.validator.addMethod('octolapseCameraRequestTemplate',
        function (value, element) {
            var testUrl = value.toUpperCase().replace("{CAMERA_ADDRESS}", 'http://w.com/').replace("{value}", "1");
            var is_valid = (
                $.validator.methods.url.call(this, testUrl, element) ||
                $.validator.methods.url.call(this, "http://w.com" + testUrl, element)
            );
            return is_valid;
        });

    $.validator.addMethod('octolapseRenderingTemplate',
        function (value, element) {
            var data = { "rendering_template": value };
            $.ajax({
                url: "./plugin/octolapse/validateRenderingTemplate",
                type: "POST",
                tryCount: 0,
                retryLimit: 3,
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (result) {
                    if (result.success)
                        return true;
                    return false;
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    var message = "Octolapse could not validate the rendering template.";

                    var options = {
                        title: 'Rendering Template Error',
                        text: message,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse",
                        desktop: {
                            desktop: false
                        }
                    };
                    Octolapse.displayPopup(options);
                    return false;
                }
            });

        });

    $.validator.addMethod('octolapsePrinterSnapshotCommand', function (value, element, param) {
        if (value === "")
            return true;
        var data = { "snapshot_command": value };
        var rpcParam = {
            url: "./plugin/octolapse/validateSnapshotCommand",
            type: "POST",
            data: JSON.stringify(data),
            dataType: "json",
            contentType: "application/json",
        };
        return $.validator.methods.remote.call(this, value, element, rpcParam, 'octolapsePrinterSnapshotCommand');
    }, "Must be empty, or must contain at least one non-whitespace character that is not part of a gcode comment.");

    jQuery.extend($.validator.messages, {
        name: "Please enter a name.",
        required: "This field is required.",
        url: "Please enter a valid URL.",
        number: "Please enter a valid number.",
        equalTo: "Please enter the same value again.",
        maxlength: $.validator.format("Please enter no more than {0} characters."),
        minlength: $.validator.format("Please enter at least {0} characters."),
        rangelength: $.validator.format("Please enter a value between {0} and {1} characters long."),
        range: $.validator.format("Please enter a value between {0} and {1}."),
        max: $.validator.format("Please enter a value less than or equal to {0}."),
        min: $.validator.format("Please enter a value greater than or equal to {0}."),
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
        var is_percent = Octolapse.isPercent(val);
        if (is_percent) {
            if (round_to_percent) {
                val = Octolapse.parsePercent(val);
            } else
                return null;
        } else
            val = Octolapse.parseFloat(val);

        if (val == null || isNaN(val))
            return null;
        try {
            var round_to_increment = round_to_increment_mm_min;
            if (is_percent) {
                round_to_increment = round_to_percent;
            } else if (current_units_observable() === 'mm-sec') {
                round_to_increment = round_to_increment_mm_sec;
            }
            var rounded = Octolapse.roundToIncrement(val, round_to_increment);
            if (is_percent && return_text)
                return rounded.toString() + "%";
            else if (return_text)
                return rounded.toString();
            return rounded;
        } catch (e) {
            console.error("Error rounding axis_speed_unit");
        }

    };

    Octolapse.streamLoading = {};
    Octolapse.streamLoading.on_error = function (e) {
        var element = e.target;
        var options = e.data.options;
        $(element).hide();
        $(options.loading_selector).hide();
        if (options.src !== "") {
            console.error("Stream Error.");
            $(options.error_selector).html("<div><p>Error loading the stream at: <a href='" + options.src + "' target='_blank'>" + options.src + "</a></p><p>Check the 'Stream Address Template' setting in your camera profile.</p></div>").fadeIn(1000);
        } else {
            // This should not happen!
            console.error("Stream Error, but src is empty.");
            $(options.error_selector).html("<div><p>No stream url was provided.  Check the 'Stream Address Template' setting.</p></div>").fadeIn(1000);
        }
    };
    Octolapse.streamLoading.on_loaded = function (e) {
        var element = e.target;
        var options = e.data.options;

        if (options.src === "") {
            // If the src is empty, that means we have closed the stream, or we have no stream src.
            // When we close the stream we set it to an empty image to prevent the error
            // handler from being called.  However, assume this is an error.
            //console.log("Stream closed, or we have no stream address.");
            $(options.loading_selector).hide();
            $(element).hide();
            $(options.error_selector).html("<div><p>No stream url was provided.  Check the 'Stream Address Template' setting.</p></div>").fadeIn(1000);
            return;
        }
        // If we are here, we have a valid stream that is loaded.
        var max_height = options.max_height || 333;
        var max_width = options.max_width || 588;
        $(element).width('auto').height('auto');
        //console.log("Stream Loaded.");
        // get the width and height of the stream element
        var stream_width = $(element).width();
        var stream_height = $(element).height();
        // See if the image is greater than the max
        if (stream_width > max_width || stream_height > max_height) {
            //console.log("Resizing Stream.");
            var ratioX = max_width / stream_width;
            var ratioY = max_height / stream_height;
            var ratio = Math.min(ratioX, ratioY);
            var newWidth = stream_width * ratio;
            var newHeight = stream_height * ratio;

            $(element).width(newWidth).height(newHeight);
        }
        $(options.error_selector).hide();
        $(options.loading_selector).hide();
        $(element).show();
        //console.log("Stream shown.");
    };
    ko.bindingHandlers.streamLoading = {
        update: function (element, valueAccessor) {

            // close the stream if one exists
            var options = valueAccessor();

            var current_src = $(element).attr('src');
            var new_src = options.src;
            if (options.src === "")
                new_src = "data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=";
            //console.log("Camera stream is updating from old_src: " + current_src + " to new src: " + new_src + " for id: ??.");
            $(element).unbind("load").one("load", { options: options }, Octolapse.streamLoading.on_loaded);
            $(element).unbind("error").one("error", { options: options }, Octolapse.streamLoading.on_error);
            $(options.loading_selector).html("<div><p>Loading webcam stream at: " + options.src + "</p></div>").show();
            $(element).hide();
            $(options.error_selector).hide();
            $(element).attr('src', new_src);
            //console.log("Finished updating camera stream.");

        }
    };

    ko.bindingHandlers.octolapseSliderValue = {
        // Init, runs on initialization
        init: function (element, valueAccessor, allBindings, viewModel, bindingContext) {
            if (ko.isObservable(valueAccessor()) && (element instanceof HTMLInputElement) && (element.type === "range")) {
                // Add event listener to the slider, this will update the observable on input (just moving the slider),
                // Otherwise, you have to move the slider then release it for the value to change
                element.addEventListener('input', function () {
                    // Update the observable
                    if (ko.unwrap(valueAccessor()) !== element.value) {
                        valueAccessor()(element.value);

                        // Trigger the change event, awesome fix that makes
                        // changing a dropdown and a range slider function the same way
                        element.dispatchEvent(new Event('change'));
                    }
                }); // End event listener
            }
        }, // End init
        // Update, runs whenever observables for this binding change(and on initialization)
        update: function (element, valueAccessor, allBindings, viewModel, bindingContext) {
            // Make sure the parameter passed is an observable
            if (ko.isObservable(valueAccessor()) && (element instanceof HTMLInputElement) && (element.type === "range")) {
                // Update the slider value (so if the value changes programatically, the slider will update)
                if (element.value !== ko.unwrap(valueAccessor())) {
                    element.value = ko.unwrap(valueAccessor());
                    element.dispatchEvent(new Event('input'));
                }
            }
        } // End update
    }; // End octolapseSliderValue

    // Got this cool snippit from the knockoutjs.com site!
    // I added some jquery to disable elements so that no clicking can be done during the fade out
    ko.bindingHandlers.slideVisible = {
        init: function (element, valueAccessor) {
            // Initially set the element to be instantly visible/hidden depending on the value
            var value = valueAccessor();
            $(element).toggle(ko.unwrap(value)); // Use "unwrapObservable" so we can handle values that may or may not be observable
        },
        update: function (element, valueAccessor) {
            // Whenever the value subsequently changes, slowly fade the element in or out
            var value = valueAccessor();
            if (ko.unwrap(value)) {
                $(element).find(".ignore_hidden_errors").removeClass("hiding");
                $(element).removeClass("octolapse_unclickable").stop(true, true).slideDown();
            } else {
                $(element).find(".ignore_hidden_errors").addClass("hiding");
                $(element).addClass("octolapse_unclickable").stop(true, true).slideUp();
            }
        }
    };

    ko.subscribable.fn.octolapseSubscribeChanged = function (callback) {
        var savedValue = this.peek();
        return this.subscribe(function (latestValue) {
            var oldValue = savedValue;
            savedValue = latestValue;
            callback(latestValue, oldValue);
        });
    };

    ko.extenders.confirmable = function (target, options) {
        var self = this;
        self.message = "Are you sure?";
        self.title = "Confirm";
        self.dialog_key = 'confirmation';
        self.on_before_changed_callback = null;
        self.before_confirm_callback = null;
        self.cancel_callback = null;
        self.confirmed_callbacked = null;
        self.complete_callback = null;
        // If this callback returns true, the confirmable value will
        // change and no other callbacks will be called.
        self.ignore_callback = null;
        // If this is true, no popup will be shown, but the value will change and
        // confirmed_callback will be called, unless ignored_callback returns true
        self.auto_confirm_callback = null;
        self.new_value = null;
        self.current_value = null;
        self.is_ignored = null;
        self.is_confirmed = null;
        self.get_options = function (options) {
            if (!options)
                return;
            if (options.message)
                self.message = options.message;
            if (options.title)
                self.title = options.title;
            if (options.key)
                self.dialog_key = options.key;
            if (options.on_before_changed)
                self.on_before_changed_callback = options.on_before_changed;
            if (options.on_before_confirm)
                self.before_confirm_callback = options.on_before_confirm;
            if (options.on_cancel)
                self.cancel_callback = options.on_cancel;
            if (options.on_confirmed)
                self.confirmed_callbacked = options.on_confirmed;
            if (options.on_complete)
                self.complete_callback = options.on_complete;
            if (options.ignore)
                self.ignore_callback = options.ignore;
            if (options.auto_confirm)
                self.auto_confirm_callback = options.auto_confirm;
        };

        self.get_options(options);

        self.on_before_changed = function () {
            if (self.on_before_changed_callback) {
                self.on_before_changed_callback(self.new_value, self.current_value);
            }
        };

        self.on_before_confirm = function () {
            if (self.before_confirm_callback) {
                options = self.before_confirm_callback(self.new_value, self.current_value);
                if (options) {
                    self.get_options(options);
                }
            }
        };

        self.on_cancel = function () {
            if (self.cancel_callback)
                self.cancel_callback(self.new_value, self.current_value);
        };

        self.on_confirmed = function () {
            if (self.confirmed_callbacked)
                self.confirmed_callbacked(self.new_value, self.current_value);
        };

        self.on_complete = function () {
            if (self.complete_callback)
                self.complete_callback(self.new_value, self.current_value, self.is_confirmed, self.is_ignored);
        };

        var result = ko.computed({
            read: target,  //always return the original observables value
            write: function (new_value) {
                self.is_confirmed = false;
                self.new_value = new_value;
                self.current_value = target();
                self.on_before_changed();
                self.is_ignored = self.ignore_callback && self.ignore_callback(new_value, self.current_value);
                if (!is_ignored) {
                    var auto_confirm = (
                        self.auto_confirm_callback &&
                        self.auto_confirm_callback(new_value, self.current_value)
                    );
                    if (auto_confirm) {
                        self.on_confirmed();
                        target(new_value);
                        self.is_confirmed = true;
                        self.on_complete();
                    } else {
                        self.on_before_confirm();
                        var current_value = target();
                        Octolapse.showConfirmDialog(
                            self.dialog_key,
                            self.title,
                            self.message,
                            function () {
                                self.on_confirmed();
                                target(new_value);
                                self.is_confirmed = true;
                                self.on_complete();
                            }, function () {
                                self.on_cancel();
                                target.notifySubscribers(current_value);
                                self.on_complete();
                            }
                        );
                    }

                } else {
                    target(new_value);
                }

            }
        }).extend({ notify: 'always' });
        //return the new computed observable
        return result;
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
                val = Octolapse.parseFloat(val);
                if (val == null)
                    return val;
                try {
                    // safari doesn't seem to like toFixed with a precision > 20
                    if (precision > 20)
                        precision = 20;
                    return val.toFixed(precision);
                } catch (e) {
                    console.error("Error converting toFixed");
                }

            },
            write: target
        });

        result.raw = target;
        return result;
    };

    var byte = 1024;
    Octolapse.toFileSizeString = function (bytes, precision) {
        precision = precision || 0;

        if (Math.abs(bytes) < byte) {
            return bytes + ' B';
        }
        var units = ['kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
        var u = -1;
        do {
            bytes /= byte;
            ++u;
        } while (Math.abs(bytes) >= byte && u < units.length - 1);
        return bytes.toFixed(precision) + ' ' + units[u];
    };

    Octolapse.pad = function pad(n, width, z) {
        z = z || '0';
        return (String(z).repeat(width) + String(n)).slice(String(n).length);
    };

    Octolapse.toLocalDateString = function (unix_timestamp) {
        if (unix_timestamp) {
            return (new Date(unix_timestamp * 1000)).toLocaleDateString();
        }
        return "UNKNOWN";
    };

    Octolapse.toLocalDateTimeString = function (unix_timestamp) {
        if (unix_timestamp) {
            var date = new Date(unix_timestamp * 1000);
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
        return "UNKNOWN";
    };

    Octolapse.ToTime = function (seconds) {
        if (seconds == null)
            return Octolapse.NullTimeText;
        var utcSeconds = seconds;
        var d = new Date(0); // The 0 there is the key, which sets the date to the epoch
        d.setUTCSeconds(utcSeconds);
        return Octolapse.pad(d.getHours(), 2, "0") + ":"
            + Octolapse.pad(d.getMinutes(), 2, "0") + ":"
            + Octolapse.pad(d.getSeconds(), 2, "0");
    };

    Octolapse.ToTimer = function (seconds) {
        if (seconds == null)
            return "";
        if (seconds <= 0)
            return "0:00";

        seconds = Math.round(seconds);

        var hours = Math.floor(seconds / 3600).toString();
        if (hours > 0) {
            return ("" + hours).slice(-2) + " Hrs";
        }

        seconds %= 3600;
        var minutes = Math.floor(seconds / 60).toString();
        seconds = (seconds % 60).toString();
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
                if (dotLessShortValue.length <= 2) {
                    break;
                }
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
                return Octolapse.ToTime(val);
            },
            write: target
        });

        result.raw = target;
        return result;
    };

    Octolapse.createObjectURL = window.webkitURL ? window.webkitURL.createObjectURL : window.URL && window.URL.createObjectURL ? window.URL.createObjectURL : null;
    Octolapse.revokeObjectURL = window.webkitURL ? window.webkitURL.revokeObjectURL : window.URL && window.URL.revokeObjectURL ? window.URL.revokeObjectURL : null;

    Octolapse.download = function (url, event, options) {
        var on_start = options.on_start;
        var on_load = options.on_load;
        var on_error = options.on_error;
        var on_abort = options.on_abort;
        var on_progress = options.on_progress;
        var on_end = options.on_end;

        if (on_start) {
            // If we can't download in the preferred way, make sure to report that to on_start
            on_start(Octolapse.createObjectURL != null, event, url);
        }

        if (!(Octolapse.createObjectURL && Octolapse.revokeObjectURL)) {
            // Fallback Download
            var a = document.createElement('a');
            a.href = url;
            a.download = "";
            a.click();
            if (on_end) {
                on_end(event, url);
            }
            return;
        }

        var request = new XMLHttpRequest();
        request.responseType = 'blob';
        request.open('GET', url);
        request.addEventListener('load', function (e) {
            var contentDispo = this.getResponseHeader('Content-Disposition');
            var filename = "";
            if (e.target.status === 200) {
                if (contentDispo) {
                    // https://stackoverflow.com/a/23054920/
                    filename = contentDispo.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)[1].replace(/['"]/g, '');
                }
                var file_href = Octolapse.createObjectURL(e.target.response);
                var a = document.createElement('a');
                a.href = file_href;
                a.download = filename;
                a.click();
                Octolapse.revokeObjectURL(file_href);
                if (on_load) {
                    on_load(e, filename);
                }
            } else {
                if (on_error) {
                    var error_message = e.target.status.toString() + " (" + e.target.statusText + ")";
                    var console_error_message = "Unable to download an octolapse file from '" + url + "': " +
                        error_message;
                    console.error(console_error_message);
                    on_error(error_message, null, null, null, null);
                }
            }

            if (on_end) {
                on_end(event, url);
            }
        });
        request.addEventListener('error', function (
            message, source, lineno, colno, error
        ) {
            console.error("Unable to download a file from '" + url + "'.  Error Details:  " + (
                message ? message.toString() : "unknown"
            ));
            if (on_error) {
                on_error(message, source, lineno, colno, error);
            }
            if (on_end) {
                on_end(event, url);
            }
        });
        request.addEventListener('abort', function (e) {
            if (on_abort) {
                on_abort(e);
            }
            if (on_end) {
                on_end(event, url);
            }
        });
        request.addEventListener('progress', function (e) {
            if (on_progress) {
                on_progress(e);
            }
        });
        request.send();
    };

    OctolapseViewModel = function (parameters) {
        var self = this;
        Octolapse.Globals = self;
        Octolapse.Help = new OctolapseHelp();
        self.loginState = parameters[0];
        Octolapse.PrinterStatus = parameters[1];
        self.OctoprintTimelapse = parameters[2];
        // Main settings
        self.main_settings = new Octolapse.MainSettingsViewModel();
        self.version_text = ko.pureComputed(function () {
            if (self.main_settings.octolapse_version() && self.main_settings.octolapse_version !== "unknown") {
                return "v" + self.main_settings.octolapse_version();
            }
            return "unknown";
        });
        self.is_admin = ko.observable(false);
        self.toggleAdmin = function () {
            self.is_admin(!self.is_admin());
        };
        self.preprocessing_job_guid = "";
        // Create a guid to uniquely identify this client.
        self.client_id = Octolapse.guid();
        // Have we loaded the state yet?
        self.has_loaded_state = ko.observable(false);

        self.pre_processing_progress = null;

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

        self.getInitialState = function () {
            //console.log("Getting initial state");
            if (self.is_admin()) {
                //console.log("octolapse.js - Loading settings for admin current user after startup.");
                Octolapse.Settings.loadSettings(function () {
                    // Settings are loaded, show the UI
                    self.has_loaded_state(true);
                    //  Check for updates
                    Octolapse.Settings.checkForProfileUpdates(true);
                    Octolapse.Status.load_files();
                });
            } else {
                self.loadState(function () {
                    //console.log("octolapse.js - Loading state for non-admin user after startup.");
                    // Settings are loaded, show the UI
                    self.has_loaded_state(true);
                });
            }

            // reset snapshot error state
            Octolapse.Status.snapshot_error(false);
            //console.log("Finished loading initial state.");

        };

        self.loadState = function (success_callback) {
            //console.log("octolapse.js - Loading State");
            $.ajax({
                url: "./plugin/octolapse/loadState",
                type: "POST",
                tryCount: 0,
                retryLimit: 3,
                contentType: "application/json",
                dataType: "json",
                success: function (result) {
                    //console.log("The state has been loaded.");
                    self.initial_state_loaded = true;
                    self.updateState(result);
                    if (success_callback) {
                        success_callback();
                    }
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
            if (self.is_admin() && self.startup_complete) {
                //console.log("octolapse.js - User Logged In after startup - Loading settings.  User: " + user.name);
                Octolapse.Settings.loadSettings();
                Octolapse.Status.load_files();
            }

        };

        self.onUserLoggedOut = function () {
            //console.log("octolapse.js - User Logged Out");
            self.is_admin(false);
            Octolapse.Settings.clearSettings();
        };

        self.onEventPrinterStateChanged = function (payload) {
            //console.log("Octolapse.js - Received print state change.");
            if (payload.state_id === "CANCELLING") {
                //console.log("Octolapse.js - Printer is cancelling.");
                // We need to close any progress diagogs
                if (self.pre_processing_progress != null) {
                    self.pre_processing_progress.close();
                }
            }
        };

        self.updateState = function (data) {
            //console.log("octolapse.js - updateState");
            if (data.state != null) {

                Octolapse.Status.updateState(data.state);
            }
            if (data.main_settings != null) {
                //console.log('octolapse.js - Main settings changed');
                // detect changes to auto_reload_latest_snapshot
                var cur_auto_reload_latest_snapshot = Octolapse.Globals.main_settings.auto_reload_latest_snapshot();

                Octolapse.Globals.main_settings.update(data.main_settings);
                if (cur_auto_reload_latest_snapshot !== Octolapse.Globals.main_settings.auto_reload_latest_snapshot()) {
                    //console.log('octolapse.js - Octolapse.Globals.main_settings.auto_reload_latest_snapshot changed, erasing previous snapshot images');
                    Octolapse.Status.erasePreviousSnapshotImages('octolapse_snapshot_image_container');
                    Octolapse.Status.erasePreviousSnapshotImages('octolapse_snapshot_thumbnail_container');
                }

            }
            if (data.status != null) {
                //console.log("octolapse.js - Updating Status");
                Octolapse.Status.update(data.status);
            }
            if (data.snapshot_plan_preview) {
                var plans = data.snapshot_plan_preview;
                self.preprocessing_job_guid = plans.preprocessing_job_guid;
                Octolapse.Status.previewSnapshotPlans(plans.snapshot_plans);
            }
            /*
            if (!self.HasLoadedState) {
                Octolapse.Status.updateLatestSnapshotImage(true);
                Octolapse.Status.updateLatestSnapshotThumbnail(true);
            }
            */
        };

        self.acceptSnapshotPlanPreview = function () {
            //console.log("Accepting snapshot plan preview.");
            var data = { "preprocessing_job_guid": self.preprocessing_job_guid };
            $.ajax({
                url: "./plugin/octolapse/acceptSnapshotPlanPreview",
                type: "POST",
                tryCount: 0,
                retryLimit: 3,
                contentType: "application/json",
                data: JSON.stringify(data),
                dataType: "json",
                success: function (result) {
                    if (result.success) {
                        Octolapse.Status.SnapshotPlanPreview.closeSnapshotPlanPreviewDialog();
                    } else {
                        var options = {
                            title: 'Error Accepting Plan',
                            text: result.error,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse",
                            desktop: {
                                desktop: false
                            }
                        };
                        Octolapse.displayPopup(options);
                    }
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    var message = "Could not accept the snapshot plan.  Status: " + textStatus + ".  Error: " + errorThrown;
                    var options = {
                        title: 'Error Cancelling Process',
                        text: message,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse",
                        desktop: {
                            desktop: false
                        }
                    };
                    Octolapse.displayPopup(options);
                    return false;
                }
            });
        };

        self.cancelPreprocessing = function () {
            //console.log("Cancelling preprocessing")
            var data = { "cancel": true, "preprocessing_job_guid": self.preprocessing_job_guid };
            $.ajax({
                url: "./plugin/octolapse/cancelPreprocessing",
                type: "POST",
                tryCount: 0,
                retryLimit: 3,
                contentType: "application/json",
                data: JSON.stringify(data),
                dataType: "json",
                success: function (result) {
                    if (self.pre_processing_progress != null) {
                        self.pre_processing_progress.close();
                    }
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    var message = "Could not cancel preprocessing.  Status: " + textStatus + ".  Error: " + errorThrown;
                    var options = {
                        title: 'Error Cancelling Process',
                        text: message,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse",
                        desktop: {
                            desktop: false
                        }
                    };
                    Octolapse.displayPopup(options);
                    return false;
                }
            });
        };

        // Handle Plugin Messages from Server
        self.onDataUpdaterPluginMessage = function (plugin, data) {
            if (plugin !== "octolapse") {
                return;
            }
            //console.log("Message received.  Type:" + data.type);
            //console.log(data);
            switch (data.type) {
                case "snapshot-plan-preview":
                    //console.log("Previewing snapshot plans.");
                    self.updateState(data);

                    break;
                case "snapshot-plan-preview-complete":
                    // create the cancel popup
                    //console.log("The snapshot preview is complete.  Closing the preview dialog.");
                    Octolapse.Status.SnapshotPlanPreview.closeSnapshotPlanPreviewDialog();
                    break;
                case "gcode-preprocessing-start":
                    // create the cancel popup
                    //console.log("Creating a progress bar.");
                    self.preprocessing_job_guid = data.preprocessing_job_guid;
                    self.pre_processing_progress = Octolapse.progressBar(self.cancelPreprocessing, "Initializing...");
                    break;
                case "gcode-preprocessing-update":
                    //console.log("Octolapse received pre-processing update processing message.");

                    // TODO: CHANGE THIS TO A PROGRESS INDICATOR
                    var percent_finished = data.percent_progress;
                    var seconds_elapsed = data.seconds_elapsed;
                    var seconds_to_complete = data.seconds_to_complete;
                    var gcodes_processed = data.gcodes_processed;
                    var lines_processed = data.lines_processed;

                    if (self.pre_processing_progress == null) {
                        //console.log("The pre-processing progress bar is missing, creating the progress bar.");
                        //console.log("Creating progress bar");
                        self.pre_processing_progress = Octolapse.progressBar(self.cancelPreprocessing);
                    }
                    if (self.pre_processing_progress != null) {
                        var progress_text =
                            "Remaining:" + Octolapse.ToTimer(seconds_to_complete)
                            + "  Elapsed:" + Octolapse.ToTimer(seconds_elapsed)
                            + "  Line:" + lines_processed.toString();
                        //console.log("Receiving Progress - Percent Complete:" + percent_finished + " " + progress_text);
                        self.pre_processing_progress = self.pre_processing_progress.update(
                            percent_finished, progress_text
                        );
                    }

                    break;
                case "gcode-preprocessing-failed":
                    // clear the job guid
                    //console.log("Gcode preprocessing failed.");
                    self.preprocessing_job_guid = null;
                    self.updateState(data);

                    var options = {
                        title: 'Gcode Processing Failed',
                        type: 'error',
                        hide: false,
                        addclass: "octolapse",
                        desktop: {
                            desktop: false
                        }
                    };
                    Octolapse.Help.showPopupForErrors(
                        options,
                        "gcode-preprocessing-failed",
                        ["gcode-preprocessing-failed"],
                        data.errors
                    );
                    break;

                case "updated-profiles-available":
                    if (self.is_admin()) {
                        Octolapse.Settings.showProfileUpdateConfirmation(data.available_profile_count);
                    }
                    break;
                case "external_profiles_list_changed":
                    Octolapse.Settings.UpdateAvailableServerProfiles(data.server_profiles);
                    var msg_options = {
                        title: 'New Server Profiles Available',
                        text: "New profiles were found in the octolapse profile repository.  These can be imported when adding/editing a profile.",
                        type: 'notice',
                        hide: true,
                        addclass: "octolapse",
                        desktop: {
                            desktop: false
                        }
                    };
                    Octolapse.displayPopupForKey(msg_options, "new-profiles-available", "new-profiles-available");
                    break;
                case "settings-changed": {
                    // See if the settings changed request came from the current client. If so, ignore it
                    if (self.client_id !== data.client_id) {
                        if (self.is_admin()) {
                            Octolapse.Settings.loadSettings();
                        } else {
                            Octolapse.Globals.loadState();
                        }
                    } else {
                        Octolapse.Globals.loadState();
                    }
                }
                    break;
                case "slicer_settings_detected":
                    if (data.saved) {
                        //console.log("Slicer settings detected and saved.");
                        if (data.printer_profile_json != null) {
                            var new_profile = JSON.parse(data.printer_profile_json);
                            var current_profile = Octolapse.Printers.getProfileByGuid(new_profile.guid);
                            if (current_profile != null) {
                                Octolapse.Printers.profiles.replace(current_profile, new Octolapse.PrinterProfileViewModel(new_profile));
                            } else {
                                console.error("Octolapse.js - Unable to find the updated printer profile from the current profiles!");
                            }
                            //Octolapse.Printers.replace(currentProfile, newProfile);
                        }

                    }
                    break;
                case "state-changed": {
                    //console.log('octolapse.js - state-changed');
                    if (data.state) {
                        self.updateState(data);
                    } else if (data.client_id !== self.client_id) {
                        // The update contains no state.  See if it originated from a client
                        self.loadState();
                    }
                }
                    break;
                case "popup": {
                    //console.log('octolapse.js - popup');
                    var popup_options = {
                        title: 'Octolapse Notice',
                        text: data.msg,
                        type: 'notice',
                        hide: true,
                        addclass: "octolapse",
                        desktop: {
                            desktop: false
                        }
                    };
                    Octolapse.displayPopup(popup_options);
                }
                    break;
                case "popup-error": {
                    //console.log('octolapse.js - popup-error');
                    self.updateState(data);
                    var popupErrorOptions = {
                        title: 'Error',
                        text: data.msg,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse",
                        desktop: {
                            desktop: false
                        }
                    };
                    Octolapse.displayPopup(popupErrorOptions);
                    break;
                }
                case "print-start-error": {
                    //console.log('octolapse.js - print-start-error');
                    self.updateState(data);
                    self.preprocessing_job_guid = null;
                    var printStartPopupoptions = {
                        title: 'Octolapse Startup Failed',
                        text: data.msg,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse",
                        desktop: {
                            desktop: false
                        }
                    };
                    Octolapse.Help.showPopupForErrors(printStartPopupoptions, "print-start-error", ["print-start-error"], data["errors"]);
                    break;
                }
                case "print-start-warning": {
                    //console.log('octolapse.js - print-start-error');
                    self.updateState(data);
                    self.preprocessing_job_guid = null;
                    var printStartPopupoptions = {
                        title: 'Octolapse Cannot Start',
                        text: data.msg,
                        type: 'warning',
                        hide: false,
                        addclass: "octolapse",
                        desktop: {
                            desktop: false
                        }
                    };
                    Octolapse.Help.showPopupForErrors(printStartPopupoptions, "print-start-error", ["print-start-error"], data["errors"]);
                    break;
                }
                case "timelapse-start": {
                    //console.log('octolapse.js - timelapse-start');
                    // Erase any previous images
                    Octolapse.HasTakenFirstSnapshot = false;
                    // let the status tab know that a timelapse is starting
                    Octolapse.Status.onTimelapseStart();
                    self.updateState(data);
                    Octolapse.Status.snapshot_error(false);
                }
                    break;
                case "timelapse-complete": {
                    //console.log('octolapse.js - timelapse-complete');
                    Octolapse.Status.snapshot_error(false);
                    self.updateState(data);

                }
                    break;
                case "camera-settings-error":
                    // If only the camera image acquisition failed, use the camera error message
                    var cameraSettingsErrorPopup = {
                        title: 'Octolapse - Camera Settings Error',
                        text: data.msg,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse"
                    };
                    Octolapse.displayPopupForKey(cameraSettingsErrorPopup, "snapshot_error", ["snapshot_error"]);
                    break;
                case "snapshot-start": {
                    //console.log('octolapse.js - snapshot-start');
                    self.updateState(data);
                    Octolapse.Status.snapshot_error(false);
                }
                    break;
                case "snapshot-complete": {
                    //console.log('octolapse.js - snapshot-complete');
                    //console.log(data);
                    self.updateState(data);

                    var hasError = !(data.success && data.snapshot_success);
                    Octolapse.Status.snapshot_error(hasError);
                    if (hasError) {
                        // If only the camera image acquisition failed, use the camera error message
                        if (!data.success) {
                            var snapshotCompleteSuccessPopupOptions = {
                                title: "Stabilization Error",
                                text: data.error,
                                type: 'error',
                                hide: false,
                                addclass: "octolapse"
                            };
                            Octolapse.displayPopupForKey(snapshotCompleteSuccessPopupOptions, "stabilization_error", ["stabilization_error"]);
                        }
                        if (!data.snapshot_success) {
                            var snapshotCompleteErrorPopupOptions = {
                                title: "Camera Error",
                                text: data.snapshot_error,
                                type: 'error',
                                hide: false,
                                addclass: "octolapse"
                            };
                            Octolapse.displayPopupForKey(snapshotCompleteErrorPopupOptions, "camera_error", ["camera_error"]);
                        }


                    }

                }
                    break;
                case "snapshot-post-proocessing-failed": {
                    self.updateState(data);
                    Octolapse.Status.snapshot_error(true);
                    // If only the camera image acquisition failed, use the camera error message

                    if (!data.snapshot_success) {
                        var postProcessingFailedPopupOptions = {
                            title: "Camera Processing Error",
                            text: data.message,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse"
                        };
                        Octolapse.displayPopupForKey(postProcessingFailedPopupOptions, "camera_error", ["camera_error"]);
                    }
                }
                    break;
                case "new-thumbnail-available":
                    if (data.guid === $("#octolapse_current_snapshot_camera").val()) {
                        //console.log("New thumbnails available");
                        if (!Octolapse.HasTakenFirstSnapshot) {
                            Octolapse.HasTakenFirstSnapshot = true;
                            Octolapse.Status.erasePreviousSnapshotImages('octolapse_snapshot_image_container', true);
                            Octolapse.Status.erasePreviousSnapshotImages('octolapse_snapshot_thumbnail_container', true);
                            Octolapse.Status.updateLatestSnapshotThumbnail(true, false);
                            Octolapse.Status.updateLatestSnapshotImage();
                        } else {
                            Octolapse.Status.updateLatestSnapshotThumbnail();
                            Octolapse.Status.updateLatestSnapshotImage();
                        }
                    }
                    break;
                case "directories-changed": {
                    //console.log('octolapse.js - directories changed.');
                    var directories = data.directories;
                    if (directories.temporary_directory_changed) {
                        // Load unfinished
                        Octolapse.Status.dialog_rendering_unfinished.load();
                    }
                    if (directories.snapshot_archive_directory_changed) {
                        // Load snapshot archive
                        Octolapse.Status.timelapse_files_dialog.archive_browser.load();
                    }
                    if (directories.timelapse_directory_changed) {
                        // load timelapses
                        Octolapse.Status.timelapse_files_dialog.timelapse_browser.load();
                    }
                }
                    break;
                case "unfinished-renderings-loaded": {
                    //console.log('octolapse.js - unfinished-renderings-loaded');
                    self.updateState(data);
                }
                    break;
                case "unfinished-renderings-changed": {
                    //console.log('octolapse.js - unfinished-renderings-changed');
                    self.updateState(data);
                }
                    break;
                case "render-start": {
                    //console.log('octolapse.js - render-start');
                    self.updateState(data);
                    /*
                    Octolapse.Status.snapshot_error(false);
                    var options = {
                        title: 'Octolapse Rendering Started',
                        text: data.msg,
                        type: 'notice',
                        hide: true,
                        addclass: "octolapse",
                        desktop: {
                            desktop: false
                        }
                    };
                    Octolapse.displayPopupForKey(options,"render_message", ["render_message"]);*/
                }
                    break;
                case "render-failed": {
                    //console.log('octolapse.js - render-failed');
                    self.updateState(data);
                    var renderFailedPopupOptions = {
                        title: 'Octolapse Rendering Failed',
                        text: data.msg,
                        type: 'error',
                        hide: true,
                        addclass: "octolapse",
                        desktop: {
                            desktop: false
                        }
                    };
                    Octolapse.displayPopup(renderFailedPopupOptions);
                    break;
                }
                case "post-render-failed": {
                    //console.log('octolapse.js - post-render-failed');
                    self.updateState(data);
                    var postRenderFailedPopupOptions = {
                        title: 'Octolapse Post-Rendering Failed',
                        text: data.msg,
                        type: 'error',
                        hide: true,
                        addclass: "octolapse",
                        desktop: {
                            desktop: false
                        }
                    };
                    Octolapse.displayPopup(postRenderFailedPopupOptions);
                    break;
                }
                case "render-progress":
                    //console.log('octolapse.js - render-progress');
                    self.updateState(data);
                    break;
                case "render-complete":
                    self.updateState(data);
                    self.OctoprintTimelapse.requestData();
                    //console.log('octolapse.js - render-complete');
                    /*
                    var options = {
                        title: 'Octolapse Rendering Complete',
                        text: data.msg,
                        type: 'success',
                        hide: true,
                        addclass: "octolapse",
                        desktop: {
                            desktop: false
                        }
                    };
                    Octolapse.displayPopupForKey(options,"render_complete",["render_complete", "render_message"]);*/
                    break;
                case "render-end": {
                    //console.log('octolapse.js - render-end');
                    self.updateState(data);
                }
                    break;
                case "timelapse-stopping": {
                    //console.log('octolapse.js - timelapse-stoping');
                    Octolapse.Status.is_timelapse_active(false);
                    var timelapseStoppingPopupOptions = {
                        title: 'Octolapse Timelapse Stopping',
                        text: data.msg,
                        type: 'notice',
                        hide: true,
                        addclass: "octolapse",
                        desktop: {
                            desktop: false
                        }
                    };
                    Octolapse.displayPopup(timelapseStoppingPopupOptions);
                }
                    break;
                case "timelapse-stopped": {
                    //console.log('octolapse.js - timelapse-stopped');
                    Octolapse.Status.onTimelapseStop();
                    Octolapse.Status.snapshot_error(false);
                    var timelapseStoppedPopupOptions = {
                        title: 'Octolapse Timelapse Stopped',
                        text: data.msg,
                        type: 'notice',
                        hide: true,
                        addclass: "octolapse",
                        desktop: {
                            desktop: false
                        }
                    };
                    Octolapse.displayPopup(timelapseStoppedPopupOptions);
                }
                    break;
                case "disabled-running": {
                    var disabledButRunningPopupOptions = {
                        title: 'Octolapse Disabled for Next Print',
                        text: data.msg,
                        type: 'notice',
                        hide: true,
                        addclass: "octolapse",
                        desktop: {
                            desktop: false
                        }
                    };
                    Octolapse.displayPopupForKey(disabledButRunningPopupOptions, "settings-change-not-applied", ["settings-change-not-applied"]);
                }
                    break;
                case "test-mode-changed-running": {
                    var testModeChangedWhileRunningPopupOptions = {
                        title: 'Test Mode Changed, Octolapse Running',
                        text: data.msg,
                        type: 'notice',
                        hide: true,
                        addclass: "octolapse",
                        desktop: {
                            desktop: false
                        }
                    };
                    Octolapse.displayPopupForKey(testModeChangedWhileRunningPopupOptions, "settings-change-not-applied", ["settings-change-not-applied"]);
                }
                    break;
                case "timelapse-stopped-error": {
                    //console.log('octolapse.js - timelapse-stopped-error');
                    Octolapse.Status.onTimelapseStop();
                    var timelapseStoppedErrorPopupOptions = {
                        title: 'Octolapse Timelapse Stopped',
                        text: data.msg,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse"
                    };
                    Octolapse.displayPopup(timelapseStoppedErrorPopupOptions);
                }
                    break;
                case "out-of-bounds": {
                    //console.log("An out-of-bounds snapshot position was detected.")
                    var outOfBoundsErrorPopupOptions = {
                        title: 'Octolapse - Out Of Bounds',
                        text: data.msg,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse"
                    };
                    Octolapse.displayPopupForKey(outOfBoundsErrorPopupOptions, "out-of-bounds", ["out-of-bounds"]);
                }
                    break;
                case "position-error": {
                    //console.log("An out-of-bounds snapshot position was detected.")
                    // This should never be called.  May need to remove!
                    var positionErrorPopupOptions = {
                        title: 'Octolapse - Position Error',
                        text: data.msg,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse"
                    };
                    Octolapse.displayPopupForKey(positionErrorPopupOptions, "position-error", ["position-error"]);
                }
                    break;
                case "file-changed": {
                    if (data.client_id !== self.client_id) {
                        Octolapse.Status.files_changed(data.file, data.action);
                    }
                }
                    break;
                case "warning":
                    //console.log("A warning was sent to the plugin.")
                    var warningPopupOptions = {
                        title: 'Octolapse - Warning',
                        text: data.msg,
                        type: 'notice',
                        hide: true,
                        addclass: "octolapse"
                    };
                    Octolapse.displayPopup(warningPopupOptions, "warning");
                    break;

                default: {
                    //console.log('Octolapse.js - passing on message from server.  DataType:' + data.type);
                }
            }
        };


    };
    OCTOPRINT_VIEWMODELS.push([
        OctolapseViewModel
        , ["loginStateViewModel", "printerStateViewModel", "timelapseViewModel"]
        , ["#octolapse"]
    ]);

});
