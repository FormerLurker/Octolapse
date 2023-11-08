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
    Octolapse.ProfileLibraryViewModel = function(
        values, profiles, profile_type, parent, update_callback
    ){
        var self = this;
        self.options_caption = "Not Selected";
        self.is_initialized = false;
        // Available profile and key information
        if (profiles)
        {
            self.profiles = profiles;

        }
        else{
            self.profiles = {
                "keys": [],
                "values": {}
            };
        }
        self.available_keys = self.profiles.keys;
        self.key_values_with_index = ko.observableArray([]);
        self.key_values = [];
        // Create default key values (all null options)
        for (var index=0; index < self.available_keys.length; index++)
        {
            var key_value;
            var has_null_value = false;
            if (!values.key_values || !values.key_values[index] || has_null_value) {
                key_value = {name: self.options_caption, value: "null"};
                has_null_value = true;
            }
            else
                key_value = values.key_values[index];

            self.key_values.push(key_value);
        }

        self.options = ko.observableArray([]);
        self.ignore_key_change = false;

        // A link to the parent, which is using the viewmodel
        self.data = ko.observable();
        self.data.parent = parent;

        // The type of profile
        self.profile_type = profile_type;

        // A callback to update the profile when updates are requested.
        self.update_callback = update_callback;

        // Variables used to revert changes on cancel, and to allow updates without triggering confirmation popups
        // or performing server updates
        self.old_is_custom = null;
        self.ignore_is_custom_change = false;

        // profile observables
        self.version = ko.observable(values.version).extend({numeric: 1});
        self.is_beta = ko.pureComputed(function(){
            var version = parseFloat(self.version());
            if (version)
            {
                return version < 1.0;
            }
            return false;
        });
        self.suppress_update_notification_version = ko.observable(values.suppress_update_notification_version);
        self.is_custom = ko.observable(values.is_custom);
        // Create the key observable and attach a confirmation popup extender
        self.original_name = parent.name();
        self.automatic_changed_to_custom = ko.observable(false);

        self.selectedOptionChanged = function (selected_option) {
            self.updateKeyValuesForIndexedKey(selected_option);
            if (!selected_option)
                return;
            // Get index from selected option
            var option_index = self.getIndexFromIndexedKey(selected_option);

            // Fill the observable array with new items
            self.getOptionsForKeyIndex(option_index+1);
            var option_key = self.getKeyFromIndexedKey(selected_option);
            if (option_index + 1 < self.available_keys.length && self.is_initialized)
            {
                self.key_values_with_index()[option_index+1]((option_index+1).toString()+ "-null");
            }
        };

        self.can_update_from_server = ko.pureComputed(function(){
            for (index in self.key_values_with_index())
            {
                var indexed_key = self.key_values_with_index()[index]();
                if (!indexed_key)
                    return false;
                var key = self.getKeyFromIndexedKey(indexed_key);
                if (key == "null")
                    return false;
            }
            return self.options().length>0;
        },self);

        self.updating_from_server = ko.pureComputed(function(){
            return self.can_update_from_server() && !self.is_custom();
        },self);

        self.is_confirming = ko.observable(false);

        // Create options
        self.createOptions = function () {
            for (var index = 0; index < self.available_keys.length; index++) {
                //console.log("Creating profile library keys.");
                self.options.push(ko.observableArray([]));
                var current_key_value = null;
                if (self.key_values && self.key_values.length > index)
                    current_key_value = self.key_values[index];
                var key;
                if (index < self.available_keys.length - 1) {
                    key = ko.observable(current_key_value);
                    key.subscribe(self.selectedOptionChanged);
                } else {
                    key = ko.observable(current_key_value).extend({
                        confirmable: {
                            key: 'confirm-load-server-profile',
                            message: 'This will overwrite your current settings.  Are you sure?',
                            title: 'Update Profile From Server',
                            on_before_changed: function (newValue, oldValue) {
                                self.updateKeyValuesForIndexedKey(newValue);
                            },
                            on_before_confirm: function (newValue, oldValue) {
                                // Record our previous custom value in case we need to revert to the previous value
                                self.old_is_custom = self.is_custom();
                                // We are going to confirm now
                                self.is_confirming(true);
                            },
                            ignore: function (newValue, oldValue) {
                                if(!newValue)
                                    return true;
                                // ignore the popup if we are ignoring key changes
                                var key = self.getKeyFromIndexedKey(newValue);
                                return self.ignore_key_change || key=="null";
                            },
                            auto_confirm: function (newValue, oldValue) {
                                if (!newValue)
                                    return false;
                                key = self.getKeyFromIndexedKey(newValue);
                                return key == 'null';
                            },
                            on_confirmed: function (newValue, oldValue) {

                                self.ignore_is_custom_change = true;
                                self.ignore_is_custom_change = false;
                            },
                            on_cancel: function (newValue, oldValue) {
                                // Revert the key and is_custom setting to their previous value
                                // No other changes will have been made to the profile at this point
                                if (newValue) {
                                    self.ignore_key_change = true;
                                    self.ignore_key_change = false;
                                    self.ignore_is_custom_change = true;
                                    self.is_custom(self.old_is_custom);
                                    self.ignore_is_custom_change = false;
                                    self.is_confirming(false);
                                }
                            },
                            on_complete: function (newValue, oldValue, wasConfirmed, wasIgnored) {
                                // Todo:  What is wasIgnored doing here?  Probably need to deal with it.
                                // we don't want to do anything if we're ignoring key changes
                                if (self.ignore_key_change)
                                    return;

                                // only update the profile if the new value is not null or custom
                                var should_update_profile = wasConfirmed && (newValue);

                                if (should_update_profile) {
                                    self.updateProfileFromLibrary({
                                        on_failed: function () {
                                            self.ignore_is_custom_change = true;
                                            self.is_custom(true);
                                            self.ignore_is_custom_change = false;
                                            self.is_confirming(false);
                                        }
                                    });
                                }
                            }
                        }
                    });
                }
                self.key_values_with_index.push(key);
            }
        };

        self.createOptions();

        self.getIndexFromIndexedKey = function(option){
            return parseInt(option.substring(0,option.indexOf("-")));
        };

        self.getKeyFromIndexedKey = function(option){
            return option.substring(option.indexOf("-")+1,option.length);
        };

        self.createIndexedKey = function(key,index) {
            return index.toString() + "-" + key;
        };

        self.createOptionFromIndexedKey = function(indexed_key) {
            // change the key_value for the current key_value_with_index
            // This is necessary to keep the two items in sync
            // first we have to find this object from the options
            var option = self.getOptionForIndexedKey(indexed_key);
            var key = self.getKeyFromIndexedKey(indexed_key);
            return {
                "name": option.name,
                "value": key
            };
        };

        self.updateKeyValuesForIndexedKey = function(indexed_key) {
            // We can't do this if the indexed_key is null, so just return.
            // We take care of this when the options observbleArrays are cleared
            if(!indexed_key)
                return;
            // change the key_value for the current key_value_with_index
            // This is necessary to keep the two items in sync
            // first we have to find this object from the options
            var index = self.getIndexFromIndexedKey(indexed_key);
            var option = self.getOptionForIndexedKey(indexed_key);
            if (!option)
                return;
            var key = self.getKeyFromIndexedKey(indexed_key);
            var option_value;
            if (key == "null")
            {
                option_value = {
                    "name": self.options_caption,
                    "value": "null"
                };
            }
            else
            {
                option_value = {
                    "name": option.name,
                    "value": key
                };
            }

            self.key_values[index] = option_value;
            // Clear any key values that are higher up.
            /*
            for (option_index = index; index < self.key_values.length - 1; index++)
                self.key_values[index] = null;*/

        };

        self.createIndexedOption = function(name,key,index) {
            return {"name": name, "value": self.createIndexedKey(key,index) };
        };
        self.getOptionForIndexedKey = function(key){
            var index = self.getIndexFromIndexedKey(key);
            var options = self.options()[index]();
            for (var option_index in options) {
                var option = options[option_index];
                if (option.value === key)
                    return option;
            }
            return null;
        };

        self.getOptionsForKeyIndex = function(key_index) {
            self.ignore_key_change = true;
            if(key_index > self.options().length-1)
            {
                console.error("Cannot update option key index " + key_index.toString() + ".  It is out of bounds.");
                return;
            }
            //console.log("Updating server profile for " + key_index.toString());
            // clear the current options
            self.options()[key_index].removeAll();
            // get the current observableArray and clear it
            var options = self.options()[key_index];
            var current_parent = self.profiles;
            for (var value_index=0; value_index < key_index; value_index++)
            {
                var current_option_value = self.key_values_with_index()[value_index]();
                if (current_option_value) {
                    var key = self.getKeyFromIndexedKey(current_option_value);
                    if (!(key in current_parent.values)) {
                        options.unshift(self.createIndexedOption(self.options_caption,"null", key_index));
                        return;
                    }
                    current_parent = current_parent.values[key];
                }
                else if (index == 0)
                {
                    break;
                }
                else
                {
                    return;
                }

            }
            // create the key value pairs from the current parent
            for (var key in current_parent.values) {

                var current_option = current_parent.values[key];
                options.push(self.createIndexedOption(current_option.name,key,key_index));
            }
            if (options().length === 0)
            {
                options.push(self.createIndexedOption(self.original_key[index],self.original_key[index], key_index));
            }
            options.sort(function(left, right) {
                return left.name == right.name ? 0 : (left.name < right.name ? -1 : 1);
            });
            options.unshift(self.createIndexedOption(self.options_caption,"null", key_index));
            self.ignore_key_change = false;
        };

        self.getKeyValuesArray = function(){
            var key_values_array = [];
            for (var index = 0; index < self.available_keys.length; index++)
            {
                key_values_array.push(self.getKeyFromIndexedKey(self.key_values_with_index()[index]()));
            }
            return key_values_array;
        };

        self.setKeyValuesWithIndexArray = function(keys, prevent_update) {
            if (!keys)
                return;
            for(var index = 0; index < self.available_keys.length; index++)
            {
                if (prevent_update && index == self.available_keys.length-1)
                    self.ignore_key_change = true;
                if (index < keys.length){
                    var indexed_key_value = {name:self.options_caption, value: "0-null"};
                    if (keys[index])
                        indexed_key_value = self.createIndexedKey(keys[index].value, index);
                    self.key_values_with_index()[index](indexed_key_value);
                }
                else
                    self.key_values_with_index()[index](null);

                self.ignore_key_change = false;
            }
        };

        // fill the first dropdown
        self.getOptionsForKeyIndex(0);
        // Set the option values from the server profile
        self.setKeyValuesWithIndexArray(self.key_values, true);

        // Subscribe to changes for is_custom
        self.is_custom.subscribe(function(newValue){
            if(self.ignore_is_custom_change)
                return;
            if (newValue){
                //var old_key = self.key();
                self.ignore_key_change = true;
               // self.key(null);
                self.ignore_key_change = false;
                // If we've switched from an automatically configured profile to a custom profile, display this
                // temporarily to inform the user.
                self.automatic_changed_to_custom(true);
            }
            else {
                self.automatic_changed_to_custom(false);
                // display a confirmation popup, then update the profile if confirmed, else revert to the previous
                // settings
                self.is_confirming(true);
                Octolapse.showConfirmDialog(
                    'confirm-load-server-profile',
                    'Update Profile From Server',
                    'This will overwrite your current settings.  Are you sure?',
                    function() {
                        self.updateProfileFromLibrary({
                            on_failed: function () {
                                self.ignore_is_custom_change = true;
                                self.is_custom(true);
                                self.ignore_is_custom_change = false;
                            }
                        });
                    }, function () {
                        self.ignore_is_custom_change = true;
                        self.is_custom(true);
                        self.ignore_is_custom_change = false;
                    }, function() {
                        self.is_confirming(false);
                    }
                );
            }
        });

        // returns true if there are available server profiles.  Used to hide the
        // configuration in the case that no profiles are available
        self.has_server_profiles = ko.pureComputed(function(){
            return self.profiles && self.profiles.values && Object.keys(self.profiles.values).length > 0;
        },self);
        self.is_option_visible = function (indexed_key)
        {
            if(!indexed_key)
                return false;

            var key = self.getKeyFromIndexedKey(indexed_key);
            return key != 'null';

        };
        self.on_closed = function(){
            Octolapse.closePopupsForKeys(['profile-library-update']);
            Octolapse.closeConfirmDialogsForKeys(['confirm-load-server-profile']);
        };

        self.updateProfileFromLibrary = function(options){
            var on_failed = options.on_failed;
            // Create our profile data to send to the server for updates.
            // copy our parent node to a temp variable
            var parent = self.data.parent;
            var profile_js;
            if(parent.toJS)
                profile_js = parent.toJS();
            else
                profile_js = ko.toJS(parent);
            // reattach the parent node

            var data = {
                'type': self.profile_type,
                'profile': profile_js,
                'key_values':  ko.toJS(self.key_values)
            };
            $.ajax({
                url: "./plugin/octolapse/updateProfileFromServer",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (data) {
                    if (!data.success)
                    {
                        if(on_failed)
                            on_failed();
                        var message = "Octolapse was unable to update your " + self.profile_type + " profile." +
                                      "  Message: " + data.message + "  See plugin_octolapse.log for more details.";
                        var options = {
                            title: 'Unable to Update',
                            text: message,
                            type: 'error',
                            hide: false,
                            addclass: "octolapse",
                            desktop: {
                                desktop: false
                            }
                        };
                        Octolapse.displayPopupForKey(
                            options,"profile-library-update","profile-library-update"
                        );
                        return;
                    }
                    var updated_profile = JSON.parse(data.profile_json);
                    // Update automatic configuration settings
                    var automatic_configuration = updated_profile.automatic_configuration;
                    self.version(automatic_configuration.version);
                    self.suppress_update_notification_version(null);
                    self.key_values = automatic_configuration.key_values;
                    self.setKeyValuesWithIndexArray(automatic_configuration.key_values, true);
                    self.ignore_is_custom_change = true;
                    self.ignore_is_custom_change = false;
                    self.automatic_changed_to_custom(false);
                    self.is_confirming(false);
                    self.ignore_is_custom_change = true;
                    self.is_custom(false);
                    self.ignore_is_custom_change = false;
                    // Update the parent data
                    self.update_callback(updated_profile);

                    var message = "Your " + self.profile_type.toLowerCase() + " settings have been updated.  Click 'save' to apply the changes.";
                    var options = {
                        title: 'Profile Updated',
                        text: message,
                        type: 'success',
                        hide: true,
                        addclass: "octolapse",
                        desktop: {
                            desktop: false
                        }
                    };
                    Octolapse.displayPopupForKey(
                        options,"profile-library-update","profile-library-update"
                    );
                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    if(on_failed)
                        on_failed();
                    var message = "Octolapse was unable to update your " + self.profile_type + " profile.  See" +
                                  " plugin_octolapse.log for details.  Status: " + textStatus +
                                  ".  Error: " + errorThrown;
                    var options = {
                        title: 'Unable to Update',
                        text: message,
                        type: 'error',
                        hide: false,
                        addclass: "octolapse",
                        desktop: {
                            desktop: false
                        }
                    };
                    Octolapse.displayPopupForKey(
                        options,"profile-library-update","profile-library-update"
                    );
                }
            });
        };
        self.is_initialized = true;
    };
});

