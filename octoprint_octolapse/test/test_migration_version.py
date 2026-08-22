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

from octoprint.util.version import get_comparable_version

__metaclass__ = type


import unittest
class TestOctolapsePlugin(unittest.TestCase):
    def setUp(self):
        """How do I do this???"""

    def test_version(self):
        # The problem:
        # Version numbers like V0.4.0rc1 < V0.4.0.rc1.devxxx  The dev stuff messed it up!
        # When comparing version numbers:
        # V0.4.0 > v0.4.0rc... Always
        # 0.4.0rc... > 0.4.0rc.dev...
        # 0.4.0rc2... > 0.4.0rc1...

        # test stripping off commit level version info
        test_version = get_comparable_version('0.4.0rc1+u.dec65f5')
        # make sure identical version numbers are considered to be equal
        assert (
            get_comparable_version('0.4.0rc1') == get_comparable_version('0.4.0rc1')
        )

        # make sure V prefixes are ignored version numbers are considered to be equal
        assert (
            get_comparable_version('v0.4.0rc1') == get_comparable_version('0.4.0rc1')
        )
        assert (
            get_comparable_version('V0.4.0rc1') == get_comparable_version('0.4.0rc1')
        )
        assert (
            get_comparable_version('0.4.0rc1') == get_comparable_version('v0.4.0rc1')
        )
        assert (
            get_comparable_version('0.4.0rc1') == get_comparable_version('V0.4.0rc1')
        )
        assert not (
            get_comparable_version('v0.4.0rc1') < get_comparable_version('0.4.0rc1')
        )

        # make sure that rc is always greater than rcX.devX
        assert (
             get_comparable_version('0.4.0rc1.dev1') < get_comparable_version('0.4.0rc1')
        )
        assert not (
            get_comparable_version('0.4.0rc1.dev1') > get_comparable_version('0.4.0rc1')
        )
        assert not (
            get_comparable_version('0.4.0rc1.dev1') == get_comparable_version('0.4.0rc1')
        )
        assert (
            get_comparable_version('0.4.0rc1') > get_comparable_version('0.4.0rc1.dev1')
        )
        assert not (
            get_comparable_version('0.4.0rc1') < get_comparable_version('0.4.0rc1.dev1')
        )
        assert not (
            get_comparable_version('0.4.0rc1') == get_comparable_version('0.4.0rc1.dev1')
        )


        # Make sure that release versions are always greater than non-release versions
        assert (
            get_comparable_version('0.4.0') > get_comparable_version('0.4.0rc1')
        )
        assert not (
            get_comparable_version('0.4.0') < get_comparable_version('0.4.0rc1')
        )
        assert not (
            get_comparable_version('0.4.0') == get_comparable_version('0.4.0rc1')
        )
        assert (
            get_comparable_version('0.4.0rc1') < get_comparable_version('0.4.0')
        )
        assert not (
            get_comparable_version('0.4.0rc1') > get_comparable_version('0.4.0')
        )
        assert not (
            get_comparable_version('0.4.0rc1') == get_comparable_version('0.4.0')
        )

        # make sure that higher tag versions are always considered newer than lower ones
        assert (
            get_comparable_version('0.4.1') > get_comparable_version('0.4.0')
        )
        assert not (
            get_comparable_version('0.4.1') < get_comparable_version('0.4.0')
        )
        assert not(
            get_comparable_version('0.4.1') == get_comparable_version('0.4.0')
        )
        assert (
            get_comparable_version('0.4.0') < get_comparable_version('0.4.1')
        )
        assert not (
            get_comparable_version('0.4.0') > get_comparable_version('0.4.1')
        )
        assert not (
            get_comparable_version('0.4.0') == get_comparable_version('0.4.1')
        )


        # make sure that clean versions are always considered older than dirty versions
        assert (
            get_comparable_version('v0.4.0rc1.dev5+11.g3ffd305.dirty') > get_comparable_version("v0.4.0rc1.dev5+11.g3ffd305")
        )
        assert not (
            get_comparable_version('v0.4.0rc1.dev5+11.g3ffd305.dirty') < get_comparable_version("v0.4.0rc1.dev5+11.g3ffd305")
        )
        assert not (
            get_comparable_version('v0.4.0rc1.dev5+11.g3ffd305.dirty') == get_comparable_version("v0.4.0rc1.dev5+11.g3ffd305")
        )
        assert (
            get_comparable_version("v0.4.0rc1.dev5+11.g3ffd305") < get_comparable_version('v0.4.0rc1.dev5+11.g3ffd305.dirty')
        )
        assert not (
            get_comparable_version("v0.4.0rc1.dev5+11.g3ffd305") > get_comparable_version('v0.4.0rc1.dev5+11.g3ffd305.dirty')
        )
        assert not (
            get_comparable_version("v0.4.0rc1.dev5+11.g3ffd305") == get_comparable_version('v0.4.0rc1.dev5+11.g3ffd305.dirty')
        )


        # make sure that versions with more commits are higher than those with lower
        assert (
            get_comparable_version('v0.4.0rc1.dev5+11.g3ffd305.dirty') > get_comparable_version("v0.4.0rc1.dev5+10.g3ffd305.dirty")
        )
        assert not (
            get_comparable_version('v0.4.0rc1.dev5+11.g3ffd305.dirty') < get_comparable_version("v0.4.0rc1.dev5+10.g3ffd305.dirty")
        )
        assert not (
            get_comparable_version('v0.4.0rc1.dev5+11.g3ffd305.dirty') == get_comparable_version("v0.4.0rc1.dev5+10.g3ffd305.dirty")
        )
        assert (
            get_comparable_version("v0.4.0rc1.dev5+10.g3ffd305.dirty") < get_comparable_version('v0.4.0rc1.dev5+11.g3ffd305.dirty')
        )
        assert not (
            get_comparable_version("v0.4.0rc1.dev5+10.g3ffd305.dirty") > get_comparable_version('v0.4.0rc1.dev5+11.g3ffd305.dirty')
        )
        assert not (
            get_comparable_version("v0.4.0rc1.dev5+10.g3ffd305.dirty") == get_comparable_version('v0.4.0rc1.dev5+11.g3ffd305.dirty')
        )



        # When there is not development info within the version, PEP 440 sorts a numeric local segment above an
        # alphabetical one, so the build with a known commit count wins.
        assert (
            get_comparable_version('v0.4.0rc1.dev5+u.g3ffd305') < get_comparable_version("v0.4.0rc1.dev5+10.g3ffd305")
        )
        assert (
            get_comparable_version("v0.4.0rc1.dev5+10.g3ffd305") > get_comparable_version('v0.4.0rc1.dev5+u.g3ffd305')
        )

        # when there is full tag information (i.e. installed from a release), it is older
        assert (
            get_comparable_version('v0.4.0rc1.dev5') < get_comparable_version("v0.4.0rc1.dev5+10.g3ffd305")
        )
        assert not (
            get_comparable_version('v0.4.0rc1.dev5') > get_comparable_version("v0.4.0rc1.dev5+10.g3ffd305")
        )
        assert not (
            get_comparable_version('v0.4.0rc1.dev5') == get_comparable_version("v0.4.0rc1.dev5+10.g3ffd305")
        )
        assert (
            get_comparable_version("v0.4.0rc1.dev5+10.g3ffd305") > get_comparable_version('v0.4.0rc1.dev5')
        )
        assert not (
            get_comparable_version("v0.4.0rc1.dev5+10.g3ffd305") < get_comparable_version('v0.4.0rc1.dev5')
        )
        assert not (
            get_comparable_version("v0.4.0rc1.dev5+10.g3ffd305") == get_comparable_version('v0.4.0rc1.dev5')
        )

        assert (
            get_comparable_version("v0.4.0rc1.dev2") < get_comparable_version('v0.4.0rc1.dev3')
        )

        assert (
            get_comparable_version('v0.4.0rc1.dev3') > get_comparable_version("v0.4.0rc1.dev2")
        )

        assert (
            get_comparable_version('v0.4.0') > get_comparable_version("v0.4.0rc1.dev2")
        )
        assert (
             get_comparable_version("v0.4.0rc1.dev2") < get_comparable_version('v0.4.0')
        )
