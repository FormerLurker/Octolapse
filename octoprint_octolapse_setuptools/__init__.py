# coding=utf-8
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

from distutils import version
import functools


@functools.total_ordering
class NumberedVersion(version.LooseVersion):
    # This is the current plugin version, not including any versioneer info,
    # which could be earlier or later
    CurrentVersion = "0.4.5"
    # This is the CurrentVersion last time the settings were migrated.
    CurrentSettingsVersion = "0.4.3"
    '''
        Prerelease tags will ALWAYS compare as less than a version with the same initial tags if the prerelease tag
        exists.
    '''
    def __init__(self, vstring=None, pre_release_tags=['rc'], development_tags=['dev']):
        # trim vstring
        if vstring != None:
            vstring = vstring.strip()
        self.pre_release_tags = pre_release_tags
        self.development_tags = development_tags
        self.original_string = vstring
        self._tag_version = []
        self._pre_release_version = []
        self._development_version = []
        self._commit_version = []
        self.commit_version_string = ''
        self.is_pre_release = False
        self.is_development = False
        self.has_commit_info = False
        self.commits_ahead = 0
        self.commit_guid = ''
        self.is_dirty = False

        # strip off any leading V or v
        if len(vstring) > 0 and vstring[0].upper() == "V":
            vstring = vstring[1:]

        # find any pluses that contain commit level info
        if '+' in vstring:
            index = vstring.find('+')
            # make sure there is info after the '+'
            if index < len(vstring) - 1:
                self.commit_version_string = vstring[index+1:]
            # strip off the plus symbox from the vstring
            vstring = vstring[:index]
        version.LooseVersion.__init__(self, vstring)

    def parse(self, vstring):
        version.LooseVersion.parse(self, vstring)
        # save the version without commit level info
        # set index = 0
        index = 0
        tag_length = len(self.version)
        # determine tag version
        for i in range(index, tag_length):
            index = i
            seg = self.version[i]
            if seg in self.pre_release_tags:
                self.is_pre_release = True
                break
            self._tag_version.append(seg)
        # determine pre release version
        for i in range(index + 1, tag_length):
            index = i
            seg = self.version[i]
            if seg in self.development_tags:
                self.is_development = True
                index += 1 # skip the dev bit
                break
            self._pre_release_version.append(seg)
        # determine development version
        for i in range(index, tag_length):
            index = i
            seg = self.version[i]
            self._development_version.append(seg)

        if len(self.commit_version_string) > 0:
            self.commits_ahead = None # we don't know how many commits we have yet
            # We have commit version info, let's add it to our version
            prel_segments = self.commit_version_string.split('.')
            # get num commits ahead
            if len(prel_segments) > 0:
                if prel_segments[0] != 'u':
                    try:
                        self.commits_ahead = int(prel_segments[0])
                    except ValueError:
                        # If you can't parse this, commits_ahead will be None
                        pass
            # get commit guid
            if len(prel_segments) > 1:
                guid = prel_segments[1]
                if len(guid) == 8:
                    self.commit_guid = guid
                    self.has_commit_info = True

            # find out if the current version is 'dirty' yuck!
            if len(prel_segments) > 2:
                self.is_dirty = prel_segments[2] == 'dirty'

        # add the new segments
        if self.has_commit_info:
            # add the commit level stuff to the version segments
            # Add the commit info separator (+)
            self._commit_version.append("+")
            # next, add the number of commits we are ahead
            self._commit_version.append("u" if self.commits_ahead is None else self.commits_ahead)
            # next add the guid
            self._commit_version.append(self.commit_guid)
            # if the version is dirty, add that segment
            if self.is_dirty:
                self._commit_version.append("dirty")
            self.version.extend(self._commit_version)

    def __repr__(self):
        return "{cls} ('{vstring}', {prerel_tags})" \
            .format(cls=self.__class__.__name__, vstring=str(self), prerel_tags=list(self.prerel_tags.keys()))

    def __str__(self):
        return self.original_string

    def __lt__(self, other):
        """
        Compare versions and return True if the current version is less than other
        """
        # first compare tags using LooseVersion
        cur_version = self._tag_version
        other_version = other._tag_version
        if cur_version < other_version:
            return True
        if cur_version > other_version:
            return False

        # cur_version == other_version, compare pre-release
        if self.is_pre_release and not other.is_pre_release:
            # the current version is a pre-release, but other is not.
            return True

        if other.is_pre_release and not self.is_pre_release:
            # other is a pre-release, but the current version is not.
            return False

        cur_version = self.pre_release_tags
        other_version = other.pre_release_tags
        if cur_version < other_version:
            return True
        if cur_version > other_version:
            return False

        # now compare development versions
        if self.is_development and not other.is_development:
            # the current version is development, but other is not.
            return True

        if other.is_development and not self.is_development:
            # other is a development, but the current version is not.
            return False
        # Both versions are development, compare dev versions

        cur_version = self._development_version
        other_version = other._development_version
        if cur_version < other_version:
            return True
        if cur_version > other_version:
            return False

        # Development versions are the same, now compare commit info
        # First, if either version has no 'commits_ahead', they are considered equal, return false
        if self.commits_ahead is None or other.commits_ahead is None:
            return False

        if self.commits_ahead < other.commits_ahead:
            return True
        if other.commits_ahead < self.commits_ahead:
            return False

        # we are the same number of commits ahead, so just check dirty (dirty > not dirty)
        if other.is_dirty and not self.is_dirty:
            return True
        return False

    def __eq__(self, other):
        return not (self < other) and not (self > other)

    def __gt__(self, other):
        """
            Compare versions and return True if the current version is greater than other
        """
        # first compare tags using LooseVersion
        cur_version = self._tag_version
        other_version = other._tag_version
        if cur_version > other_version:
            return True
        if cur_version < other_version:
            return False

        # cur_version == other_version, compare pre-release
        if self.is_pre_release and not other.is_pre_release:
            # the current version is a pre-release, but other is not.
            return False

        if other.is_pre_release and not self.is_pre_release:
            # other is a pre-release, but the current version is not.
            return True

        cur_version = self.pre_release_tags
        other_version = other.pre_release_tags
        if cur_version > other_version:
            return True
        if cur_version < other_version:
            return False

        # now compare development versions
        if self.is_development and not other.is_development:
            # the current version is development, but other is not.
            return False

        if other.is_development and not self.is_development:
            # other is a development, but the current version is not.
            return True
        # Both versions are development, compare dev versions
        cur_version = self._development_version
        other_version = other._development_version
        if cur_version > other_version:
            return True
        if cur_version < other_version:
            return False

        # Development versions are the same, now compare commit info
        # First, if either version has no 'commits_ahead', they are considered equal, return false
        if self.commits_ahead is None or other.commits_ahead is None:
            return False

        if self.commits_ahead > other.commits_ahead:
            return True
        if other.commits_ahead > self.commits_ahead:
            return False

        # we are the same number of commits ahead, so just check dirty (dirty > not dirty)
        if self.is_dirty and not other.is_dirty:
            return True
        return False

    @staticmethod
    def clean_version(version):
        if version is None or len(version) == 0:
            return "0+unknown"

        version = version.lower()

        if version[0] == "v":
            version = version[1:]

        return version



