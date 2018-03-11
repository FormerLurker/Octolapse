/*
This file is subject to the terms and conditions defined in
    a file called 'LICENSE', which is part of this source code package.
*/
$(function() {
    Octolapse.ProfilesViewModel = function(settings) {
        // Create all observables and a reference to this instance for event handlers.
        var self = this;

        self.profiles = ko.observableArray();
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
        self.profileTypeName = settings.profileTypeName;
        // Created a sorted observable
        self.profiles_sorted = ko.computed(function() { return Octolapse.nameSort(self.profiles) });
        /*
            Octoprint Viewmodel Events
        */
        // Adds or updats a profile via ajax
        self.addUpdateProfile = function(profile, onSuccess) {
            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array
            var isNewProfile = profile().guid() === "";
            var data = { "client_id": Octolapse.Globals.client_id, 'profile': ko.toJS(profile), 'profileType': self.profileTypeName };
            $.ajax({
                url: "/plugin/octolapse/" + self.addUpdatePath,
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function (newProfile) {

                    newProfile = new self.profileViewModelCreate(newProfile); // Create our profile viewmodel
                    if (isNewProfile) {
                        //console.log("Adding new profile");
                        if (self.profiles().length == 0)
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
                    alert("Unable to add/update the " + settings.profileTypeName +" profile!.  Status: " + textStatus + ".  Error: " + errorThrown);
                }
            });
        };
        //Remove an existing profile from the server settings, then if successful remove it from the observable array.
        self.removeProfile = function (guid) {
            if (confirm("Are you sure you want to permanently erase the profile:'" + settings.profileTypeName + "'?")) {
                var data = { "client_id": Octolapse.Globals.client_id,'guid': ko.toJS(guid), 'profileType': self.profileTypeName };
                $.ajax({
                    url: "/plugin/octolapse/" + self.removeProfilePath,
                    type: "POST",
                    data: JSON.stringify(data),
                    contentType: "application/json",
                    dataType: "json",
                    success: function (returnValue) {
                        if(returnValue.success)
                            self.profiles.remove(self.getProfileByGuid(guid));
                        else
                            alert("Unable to remove the " + settings.profileTypeName +" profile!.  Error: " + returnValue.error);

                        // close modal dialog.

                    },
                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                        alert("Unable to remove the " + settings.profileTypeName + " profile!.  Status: " + textStatus + ".  Error: " + errorThrown);
                    }
                });
            }
        };
        //Mark a profile as the current profile.
        self.setCurrentProfile = function(guid) {
            var data = { "client_id" : Octolapse.Globals.client_id,'guid': ko.toJS(guid), 'profileType': self.profileTypeName };
            $.ajax({
                url: "/plugin/octolapse/" + self.setCurrentProfilePath,
                type: "POST",
                data: JSON.stringify(data),
                contentType: "application/json",
                dataType: "json",
                success: function(result) {
                    // Set the current profile guid observable.  This will cause the UI to react to the change.
                    self.current_profile_guid(result.guid);
                },
                error: function(XMLHttpRequest, textStatus, errorThrown) {
                    alert("Unable to remove the " + settings.profileTypeName +" profile!.  Status: " + textStatus + ".  Error: " + errorThrown);
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
                alert("Could not find a " + settings.profileTypeName +" with the guid:" + guid + "!");
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
                return "No default profile selected"
            return profile.name();
        };

        // TODO:  This is not yet implemented in the new settings.  Well, it's implemented, but there's no button yet.  Add that button, test and (hopefully) remember to remove this comment
        self.getResetProfile = function(currentProfile) {
            var defaultProfileClone = new self.profileViewModelCreate(ko.toJS(self.default_profile));
            defaultProfileClone.name(currentProfile.name());
            defaultProfileClone.guid(currentProfile.guid());
            return defaultProfileClone;
        };

        // Todo: Evaluate this function.  It must be made to work with validation so that invalid fields are automatically unhidden.
        self.toggle = Octolapse.Toggle;

        self.showAddEditDialog = function(guid, isCopy=false) {

            var title = null;
            var addEditObservable = ko.observable();
            // get and configure the  profile
            if (guid == null) {
                title = "Add New " + settings.profileTypeName +" Profile";
                addEditObservable(self.getNewProfile());
                addEditObservable().name("New " + settings.profileTypeName);
                addEditObservable().guid("");
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
                addEditObservable(newProfile);

            }
            // Open the modal
            Octolapse.Settings.showAddEditDialog({ "profileObservable": addEditObservable, "title": title, "templateName": self.addEditTemplateName, "validationRules": JSON.parse(JSON.stringify(self.profileValidationRules)) },this);
        };
        /*
            Set data prior to bindings
        */
        // Add all of the profiles from the octoprint settings viewmodel.
        settings.profiles.forEach(function(item, index) {
            self.profiles.push(new self.profileViewModelCreate(item));
        });
        // Add any profile specific options and/or static viewmodel data
        self.profileOptions = settings.profileOptions;
        // Set the current profile guid
        self.current_profile_guid(settings.current_profile_guid);
        // Set the default profile used to pre-populate new profiles and (eventually)
        self.default_profile(settings.default_profile);
        // This must be the very last line!  Well, at least it probably should be
        ko.applyBindings(self, document.getElementById(self.bindingElementId));
    };
    Octolapse.restoreDefaultSettings = function (onSuccess) {
        if (confirm("You will lose ALL of your octolapse settings by restoring the defaults!  Are you SURE?")) {
            // If no guid is supplied, this is a new profile.  We will need to know that later when we push/update our observable array
            $.ajax({
                url: "/plugin/octolapse/restoreDefaults",
                type: "POST",
                contentType: "application/json",
                success: function (newSettings) {
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


