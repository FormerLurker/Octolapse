# coding=utf-8

from octoprint_octolapse_setuptools import NumberedVersion

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
        test_version = NumberedVersion('0.4.0rc1+u.dec65f5')
        # make sure identical version numbers are considered to be equal
        assert (
            NumberedVersion('0.4.0rc1') == NumberedVersion('0.4.0rc1')
        )

        # make sure V prefixes are ignored version numbers are considered to be equal
        assert (
            NumberedVersion('v0.4.0rc1') == NumberedVersion('0.4.0rc1')
        )
        assert (
            NumberedVersion('V0.4.0rc1') == NumberedVersion('0.4.0rc1')
        )
        assert (
            NumberedVersion('0.4.0rc1') == NumberedVersion('v0.4.0rc1')
        )
        assert (
            NumberedVersion('0.4.0rc1') == NumberedVersion('V0.4.0rc1')
        )
        assert not (
            NumberedVersion('v0.4.0rc1') < NumberedVersion('0.4.0rc1')
        )

        # make sure that rc is always greater than rcX.devX
        assert (
             NumberedVersion('0.4.0rc1.dev1') < NumberedVersion('0.4.0rc1')
        )
        assert not (
            NumberedVersion('0.4.0rc1.dev1') > NumberedVersion('0.4.0rc1')
        )
        assert not (
            NumberedVersion('0.4.0rc1.dev1') == NumberedVersion('0.4.0rc1')
        )
        assert (
            NumberedVersion('0.4.0rc1') > NumberedVersion('0.4.0rc1.dev1')
        )
        assert not (
            NumberedVersion('0.4.0rc1') < NumberedVersion('0.4.0rc1.dev1')
        )
        assert not (
            NumberedVersion('0.4.0rc1') == NumberedVersion('0.4.0rc1.dev1')
        )


        # Make sure that release versions are always greater than non-release versions
        assert (
            NumberedVersion('0.4.0') > NumberedVersion('0.4.0rc1')
        )
        assert not (
            NumberedVersion('0.4.0') < NumberedVersion('0.4.0rc1')
        )
        assert not (
            NumberedVersion('0.4.0') == NumberedVersion('0.4.0rc1')
        )
        assert (
            NumberedVersion('0.4.0rc1') < NumberedVersion('0.4.0')
        )
        assert not (
            NumberedVersion('0.4.0rc1') > NumberedVersion('0.4.0')
        )
        assert not (
            NumberedVersion('0.4.0rc1') == NumberedVersion('0.4.0')
        )

        # make sure that higher tag versions are always considered newer than lower ones
        assert (
            NumberedVersion('0.4.1') > NumberedVersion('0.4.0')
        )
        assert not (
            NumberedVersion('0.4.1') < NumberedVersion('0.4.0')
        )
        assert not(
            NumberedVersion('0.4.1') == NumberedVersion('0.4.0')
        )
        assert (
            NumberedVersion('0.4.0') < NumberedVersion('0.4.1')
        )
        assert not (
            NumberedVersion('0.4.0') > NumberedVersion('0.4.1')
        )
        assert not (
            NumberedVersion('0.4.0') == NumberedVersion('0.4.1')
        )


        # make sure that clean versions are always considered older than dirty versions
        assert (
            NumberedVersion('v0.4.0rc1.dev5+11.g3ffd305.dirty') > NumberedVersion("v0.4.0rc1.dev5+11.g3ffd305")
        )
        assert not (
            NumberedVersion('v0.4.0rc1.dev5+11.g3ffd305.dirty') < NumberedVersion("v0.4.0rc1.dev5+11.g3ffd305")
        )
        assert not (
            NumberedVersion('v0.4.0rc1.dev5+11.g3ffd305.dirty') == NumberedVersion("v0.4.0rc1.dev5+11.g3ffd305")
        )
        assert (
            NumberedVersion("v0.4.0rc1.dev5+11.g3ffd305") < NumberedVersion('v0.4.0rc1.dev5+11.g3ffd305.dirty')
        )
        assert not (
            NumberedVersion("v0.4.0rc1.dev5+11.g3ffd305") > NumberedVersion('v0.4.0rc1.dev5+11.g3ffd305.dirty')
        )
        assert not (
            NumberedVersion("v0.4.0rc1.dev5+11.g3ffd305") == NumberedVersion('v0.4.0rc1.dev5+11.g3ffd305.dirty')
        )


        # make sure that versions with more commits are higher than those with lower
        assert (
            NumberedVersion('v0.4.0rc1.dev5+11.g3ffd305.dirty') > NumberedVersion("v0.4.0rc1.dev5+10.g3ffd305.dirty")
        )
        assert not (
            NumberedVersion('v0.4.0rc1.dev5+11.g3ffd305.dirty') < NumberedVersion("v0.4.0rc1.dev5+10.g3ffd305.dirty")
        )
        assert not (
            NumberedVersion('v0.4.0rc1.dev5+11.g3ffd305.dirty') == NumberedVersion("v0.4.0rc1.dev5+10.g3ffd305.dirty")
        )
        assert (
            NumberedVersion("v0.4.0rc1.dev5+10.g3ffd305.dirty") < NumberedVersion('v0.4.0rc1.dev5+11.g3ffd305.dirty')
        )
        assert not (
            NumberedVersion("v0.4.0rc1.dev5+10.g3ffd305.dirty") > NumberedVersion('v0.4.0rc1.dev5+11.g3ffd305.dirty')
        )
        assert not (
            NumberedVersion("v0.4.0rc1.dev5+10.g3ffd305.dirty") == NumberedVersion('v0.4.0rc1.dev5+11.g3ffd305.dirty')
        )



        # When there is not development info within the version, the comparison is ambiguous.  Make them equal
        assert (
            NumberedVersion('v0.4.0rc1.dev5+u.g3ffd305') == NumberedVersion("v0.4.0rc1.dev5+10.g3ffd305")
        )
        assert (
            NumberedVersion("v0.4.0rc1.dev5+10.g3ffd305") == NumberedVersion('v0.4.0rc1.dev5+u.g3ffd305')
        )

        # when there is full tag information (i.e. installed from a release), it is older
        assert (
            NumberedVersion('v0.4.0rc1.dev5') < NumberedVersion("v0.4.0rc1.dev5+10.g3ffd305")
        )
        assert not (
            NumberedVersion('v0.4.0rc1.dev5') > NumberedVersion("v0.4.0rc1.dev5+10.g3ffd305")
        )
        assert not (
            NumberedVersion('v0.4.0rc1.dev5') == NumberedVersion("v0.4.0rc1.dev5+10.g3ffd305")
        )
        assert (
            NumberedVersion("v0.4.0rc1.dev5+10.g3ffd305") > NumberedVersion('v0.4.0rc1.dev5')
        )
        assert not (
            NumberedVersion("v0.4.0rc1.dev5+10.g3ffd305") < NumberedVersion('v0.4.0rc1.dev5')
        )
        assert not (
            NumberedVersion("v0.4.0rc1.dev5+10.g3ffd305") == NumberedVersion('v0.4.0rc1.dev5')
        )

        assert (
            NumberedVersion("v0.4.0rc1.dev2") < NumberedVersion('v0.4.0rc1.dev3')
        )

        assert (
            NumberedVersion('v0.4.0rc1.dev3') > NumberedVersion("v0.4.0rc1.dev2")
        )

        assert (
            NumberedVersion('v0.4.0') > NumberedVersion("v0.4.0rc1.dev2")
        )
        assert (
             NumberedVersion("v0.4.0rc1.dev2") < NumberedVersion('v0.4.0')
        )
