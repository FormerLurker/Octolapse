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
    Octolapse.ProfilesViewModel = function(settings) {
        // Create all observables and a reference to this instance for event handlers.
        var self = this;

        self.profiles = ko.observableArray();
        self.profileTypeName = ko.observable(settings.profileTypeName);
        self.default_profile = ko.observable();
        self.current_profile_guid = ko.observable();
        self.profileOptions = null;
        self.profileViewModelCreate = settings.profileViewModelCreateFunction;
        self.addEditTemplateName = settings.addEditTemplateName;
        self.profileValidationRules = settings.profileValidationRules;
        self.bindingElementId = settings.bindingElementId;
        self.addUpdatePath = settings.addUpdatePath;
        self.removeProfilePath = settings.removeProfilePath;
        self.setCurrentProfilePath = settings.setCurrentProfilePath;

        // Created a sorted observable
        self.profiles_sorted = ko.computed(function() { return Octolapse.nameSort(self.profiles) });
        /*
            Octoprint Viewmodel Events
        */
        // Adds or updats a profile via ajax
        self.addUpdateProfile = function(profile, onSuccess) {
            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array
            var isNewProfile = profile().guid() === "";
            var data = { "client_id": Octolapse.Globals.client_id, 'profile': ko.toJS(profile), 'profileType': self.profileTypeName() };
            $.ajax({
                url: "./plugin/octolapse/" + self.addUpdatePath,
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (newProfile) {

                    newProfile = new self.profileViewModelCreate(newProfile); // Create our profile viewmodel
                    if (isNewProfile) {
                        //console.log("Adding new profile");
                        if (self.profiles().length === 0)
                            self.current_profile_guid(newProfile.guid());
                        self.profiles.push(newProfile); // Since it's new, just add it.
                        // If there is only one profile, it's been set as the default profile
                        //console.log("There are currently " + self.profiles().length.toString() + " profiles.");
                    }
                    else {
                        // Since this is an existing element, we must replace the original with the  new one.
                        // First get the original one
                        var currentProfile = self.getProfileByGuid(newProfile.guid());
                        // Now replace with the new one!
                        self.profiles.replace(currentProfile, newProfile);

                    }
                    // Initiate the onSuccess callback.  Typically this would close an edit/add dialog, but
                    // maybe later we will want to do something else?  This will make it easier.
                    if (onSuccess != null) {
                        onSuccess(this, { "newProfile": newProfile });
                    }

                },
                error: function(XMLHttpRequest, textStatus, errorThrown) {
                    alert("Unable to add/update the " + settings.profileTypeName() +" profile!.  Status: " + textStatus + ".  Error: " + errorThrown);
                }
            });
        };
        //Remove an existing profile from the server settings, then if successful remove it from the observable array.
        self.removeProfile = function (guid) {
            currentProfile = self.getProfileByGuid(guid)
            if (confirm("Are you sure you want to permanently erase the profile:'" + currentProfile.name() + "'?")) {
                var data = { "client_id": Octolapse.Globals.client_id,'guid': ko.toJS(guid), 'profileType': self.profileTypeName() };
                $.ajax({
                    url: "./plugin/octolapse/" + self.removeProfilePath,
                    type: "POST",
                    data: JSON.stringify(data),
                    contentType: "application/json",
                    dataType: "json",
                    success: function (returnValue) {
                        if(returnValue.success)
                            self.profiles.remove(self.getProfileByGuid(guid));
                        else
                            alert("Unable to remove the " + currentProfile.name() +" profile!.  Error: " + returnValue.error);

                        // close modal dialog.

                    },
                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                        alert("Unable to remove the " + currentProfile.name() + " profile!.  Status: " + textStatus + ".  Error: " + errorThrown);
                    }
                });
            }
        };
        //Mark a profile as the current profile.
        self.setCurrentProfile = function(guid) {
            currentProfile = self.getProfileByGuid(guid)
            var data = { "client_id" : Octolapse.Globals.client_id,'guid': ko.toJS(guid), 'profileType': self.profileTypeName() };
            $.ajax({
                url: "./plugin/octolapse/" + self.setCurrentProfilePath,
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function(result) {
                    // Set the current profile guid observable.  This will cause the UI to react to the change.
                    //console.log("current profile guid updated: " + result.guid)
                    self.current_profile_guid(result.guid);
                },
                error: function(XMLHttpRequest, textStatus, errorThrown) {
                    alert("Unable to set the current " + currentProfile.name() +" profile!.  Status: " + textStatus + ".  Error: " + errorThrown);
                }
            });
        };
        /*
            Profile Create/Retrieve
        */
        // Creates a copy of an existing profile from the supplied guid.  If no guid is supplied (null or empty), it returns a new profile based on the default_profile settings
        self.getNewProfile = function(guid) {
            var newProfile = null;
            if (guid == null) {
                newProfile = new self.profileViewModelCreate(ko.toJS(self.default_profile())); // Create our profile viewmodel
            }
            else {
                newProfile = new self.profileViewModelCreate(ko.toJS(self.getProfileByGuid(guid))); // Create our profile viewmodel
            }
            return newProfile;
        };
        // retrieves a profile fome the profiles array by GUID.
        // This isn't a particularly fast thing, so don't do it too often.
        self.getProfileByGuid = function(guid) {
            var index = Octolapse.arrayFirstIndexOf(self.profiles(),
                function(item) {
                    var itemGuid = item.guid();
                    return itemGuid === guid
                }
            );
            if (index < 0) {
                alert("Could not find a " + self.profileTypeName() +" profile with the guid:" + guid + "!");
                return null;
            }
            return self.profiles()[index];
        };
        // Returns the current profile (the one with current_profile_guid = guid)
        self.currentProfile = function() {
            var guid = self.current_profile_guid();
            var index = Octolapse.arrayFirstIndexOf(self.profiles(),
                function(item) {
                    var itemGuid = item.guid();
                    var matchFound = itemGuid === guid;
                    if (matchFound)
                        return matchFound
                }
            );
            if (index < 0) {
                return null;
            }
            return self.profiles()[index];
        };

        self.currentProfileName = function() {
            var profile =self.currentProfile();
            if(profile == null)
                return "No default profile selected";
            return profile.name();
        };

        self.getResetProfile = function(currentProfile) {
            var defaultProfileClone = new self.profileViewModelCreate(ko.toJS(self.default_profile));
            defaultProfileClone.name(currentProfile.name());
            defaultProfileClone.guid(currentProfile.guid());
            return defaultProfileClone;
        };

        self.toggle = Octolapse.Toggle;

        self.showAddEditDialog = function(guid, isCopy) {
            console.log("octolapse.profiles.js - Showing add edit dialog.")
            isCopy = isCopy || false;
            var title = null;
            var addEditObservable = ko.observable();
            var warning = null;
            // get and configure the  profile
            if (guid == null) {
                title = "Add New " + settings.profileTypeName +" Profile";
                newProfile = self.getNewProfile();
                newProfile.name("New " + self.profileTypeName());
                newProfile.guid("");
            }
            else {
                var newProfile = self.getNewProfile(guid);
                if (isCopy === true)
                {
                    newProfile.guid("");
                    newProfile.name(newProfile.name() + " - Copy");
                    title = _.sprintf("New " + settings.profileTypeName + " \"%(name)s\"", { name: newProfile.name() });
                }
                else
                {
                    title = _.sprintf("Edit " + settings.profileTypeName + " \"%(name)s\"", { name: newProfile.name() });
                }
                //console.log("Checking for active timelapse")
                warning = null;
                if(Octolapse.Status.is_timelapse_active())
                {
                     if(newProfile.profileTypeName() == 'Debug')
                     {
                        warning = "A timelapse is active.  All debug settings will IMMEDIATELY take effect, except for 'Test Mode' which will not take effect until the next print.";
                     }
                     else
                        warning = "A timelapse is active.  Any changes made here will NOT take effect until the next print.";
                }
            }

            // Save the model into the addEditObservable
            addEditObservable(newProfile);

            Octolapse.Settings.showAddEditDialog({ "profileObservable": addEditObservable, "title": title, "templateName": self.addEditTemplateName, "validationRules": JSON.parse(JSON.stringify(self.profileValidationRules)), 'warning':warning },this);
        };
        /*
            Set data prior to bindings
        */
        ko.applyBindings(self, document.getElementById(self.bindingElementId));
    };
    Octolapse.restoreDefaultSettings = function () {
        if (confirm("You will lose ALL of your octolapse settings by restoring the defaults!  Are you SURE?")) {
            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array
            $.ajax({
                url: "./plugin/octolapse/restoreDefaults",
                type: "POST",
                contentType: "application/json",
                success: function () {
                    //load settings from the provided data
                    alert("The default settings have been restored.  Please reload your browser window to load the new default settings.");

                },
                error: function (XMLHttpRequest, textStatus, errorThrown) {
                    alert("Unable to restore the default settings.  Status: " + textStatus + ".  Error: " + errorThrown);
                }
            });
        }


    }
});


