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
$(function() {
    Octolapse.ProfileLibraryViewModel = function(
        values, profiles, profile_type, parent, auto_config_enabled, update_callback
    ) {
        var self = this;
        self.profiles = profiles;
        self.parent = parent;
        self.profile_type = profile_type;
        self.auto_config_enabled = auto_config_enabled;
        self.update_callback = update_callback;
        // Variables used to revert changes on cancel, and to allow updates without triggering confirmation popups
        // or performing server updates
        self.old_key = null;
        self.old_is_custom = null;
        self.ignore_is_custom_change = false;
        self.ignore_key_change = false;
        // profile observables
        self.version = ko.observable(values.version);
        self.suppress_update_notification_version = ko.observable(values.suppress_update_notification_version);
        self.is_custom = ko.observable(values.is_custom);
        // Create the key observable and attach a confirmation popup extender
        self.key = ko.observable(values.key).extend({
            confirmable: {
                key: 'confirm-load-server-profile',
                message: 'This will overwrite your current settings.  Are you sure?',
                title: 'Update Profile From Server',
                on_before_confirm: function(newValue, oldValue)
                {
                    // Record our previous custom value in case we need to revert to the previous value
                    self.old_is_custom = self.is_custom();
                    // no need to save the old key, it will be provided in later callbacks
                },
                ignore: function(newValue, oldValue) {
                    // ignore the popup if we are ignoring key changes
                    return self.ignore_key_change || !newValue;
                },
                auto_confirm: function(newValue, oldValue)
                {
                    return oldValue && oldValue != 'custom' && newValue && newValue != 'custom';
                },
                on_confirmed: function(newValue, oldValue) {
                    self.ignore_is_custom_change = true;
                    self.is_custom(false);
                    self.ignore_is_custom_change = false;
                },
                on_cancel: function(newValue, oldValue)
                {
                    // Revert the key and is_custom setting to their previous value
                    // No other changes will have been made to the profile at this point
                    if(newValue) {
                        self.ignore_key_change = true;
                        self.key(self.old_key);
                        self.ignore_key_change = false;
                        self.ignore_is_custom_change = true;
                        self.is_custom(self.old_is_custom);
                        self.ignore_is_custom_change = false;
                    }
                },
                on_complete: function(newValue, oldValue, wasConfirmed, wasIgnored, )
                {
                    // we don't want to do anything if we're ignoring key changes
                    if (self.ignore_key_change)
                        return;

                    // only update the profile if the new value is not null or custom
                    var should_update_profile = wasConfirmed || (newValue && newValue !== 'custom');

                    if(should_update_profile) {
                        self.updateProfileFromLibrary({
                            on_failed: function () {
                                self.ignore_is_custom_change = true;
                                self.is_custom(old_is_custom);
                                self.ignore_is_custom_change = false;
                                self.ignore_key_change = true;
                                self.key(oldValue);
                                self.ignore_key_change = false;
                            }
                        });
                    }
                }
            }
        });
        self.original_key = self.key();
        self.original_name = parent.name();
        self.automatic_changed_to_custom = ko.observable(false);
        // Subscribe to changes for is_custom
        self.is_custom.subscribe(function(newValue){
            if (newValue && !self.ignore_is_custom_change ){
                var old_key = self.key();
                self.ignore_key_change = true;
                self.key(null);
                self.ignore_key_change = false;
                // If we've switched from an automatically configured profile to a custom profile, display this
                // temporarily to inform the user.
                if (old_key && old_key != 'custom')
                    self.automatic_changed_to_custom(true);
                else
                    self.automatic_changed_to_custom(false);
            }
        });

        // Turn the server profiles into an array of key/value pairs
        self.server_profiles = ko.pureComputed(function() {
            console.log("Getting server profile list.");
            var profiles = [];
            for (key in self.profiles) {
                var current_profiles = self.profiles[key];
                var profile = {
                    'name': current_profiles.name,
                    'value': key
                };
                profiles.push(profile);
            }
            if (profiles.length === 0)
            {
                var profile = {
                    'name': self.original_name,
                    'value': self.original_key
                };
                profiles.push(profile);
            }
            return Octolapse.nameSort(profiles);
        });
        // returns true if there are available server profiles.  Used to hide the
        // configuration in the case that no profiles are available
        self.has_server_profiles = ko.pureComputed(function(){
            return self.profiles && Object.keys(self.profiles).length > 0;
        },this);
        self.can_update_from_server = ko.pureComputed(function(){
            return self.key() && self.key() !== "custom"
        },this);
        self.updating_from_server = ko.pureComputed(function(){
            return self.can_update_from_server() && !self.is_custom();
        },this);
        
        self.on_closed = function(){
            Octolapse.closePopupsForKeys(['profile-library-update', 'confirm-load-server-profile']);
        };
        
        self.updateProfileFromLibrary = function(options){
            var on_failed = options.on_failed;

            // Create our profile data to send to the server for updates.
            // copy our parent node to a temp variable
            var parent = self.parent;
            // remove the parent node for a bit to prevent a circular update
            self.parent = null;
            var profile_js;
            if(parent.toJS)
                profile_js = parent.toJS();
            else
                profile_js = ko.toJS(parent);
            // reattach the parent node
            self.parent = parent;

            var data = {
                'type': self.profile_type,
                'profile': profile_js,
                'identifiers': {
                    'key': self.key()
                }
            };
            $.ajax({
                url: "./plugin/octolapse/updateProfileFromServer",
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (data) {
                    var updated_profile = JSON.parse(data.profile_json);
                    // Update automatic configuration settings
                    var automatic_configuration = updated_profile.automatic_configuration;
                    self.version(automatic_configuration.version);
                    self.suppress_update_notification_version(null);
                    self.ignore_key_change = true;
                    self.key(automatic_configuration.key);
                    self.ignore_key_change = false;
                    self.ignore_is_custom_change = true;
                    self.is_custom(false);
                    self.ignore_is_custom_change = false;
                    self.automatic_changed_to_custom(false);
                    // Update the parent data
                    self.update_callback(updated_profile);
        
                    var message = "Your " + self.profile_type + "settings have been updated.  Click 'save' to apply the changes.";
                    var options = {
                        title: 'Profile Updated',
                        text: message,
                        type: 'success',
                        hide: true,
                        addclass: "octolapse",
                        desktop: {
                            desktop: true
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
                            desktop: true
                        }
                    };
                    Octolapse.displayPopupForKey(
                        options,"profile-library-update","profile-library-update"
                    );
                }
            });
        };

    };
});
    
