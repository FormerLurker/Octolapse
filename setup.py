# coding=utf-8
from distutils.core import Extension
from distutils.command.build_ext import build_ext
import sys
import os
########################################################################################################################
# The plugin's identifier, has to be unique
plugin_identifier = "octolapse"
# The plugin's python package, should be "octoprint_<plugin identifier>", has to be unique
plugin_package = "octoprint_octolapse"
# The plugin's human readable name. Can be overwritten within OctoPrint's internal data via __plugin_name__ in the
# plugin module
plugin_name = "Octolapse"
# The plugin's version. Can be overwritten within OctoPrint's internal data via __plugin_version__ in the plugin module
plugin_version = "0.3.5rc1.dev0"
# The plugin's description. Can be overwritten within OctoPrint's internal data via __plugin_description__ in the plugin
# module
plugin_description = """Create stabilized timelapses of your 3d prints.  Highly customizable, loads of presets, lots of fun."""
# The plugin's author. Can be overwritten within OctoPrint's internal data via __plugin_author__ in the plugin module
plugin_author = "Brad Hochgesang"
# The plugin's author's mail address.
plugin_author_email = "FormerLurker@pm.me"

# The plugin's homepage URL. Can be overwritten within OctoPrint's internal data via __plugin_url__ in the plugin module
plugin_url = "https://github.com/FormerLurker/Octolapse"

# The plugin's license. Can be overwritten within OctoPrint's internal data via __plugin_license__ in the plugin module
plugin_license = "AGPLv3"

# Any additional requirements besides OctoPrint should be listed here
plugin_requires = ["pillow", "sarge", "six", "OctoPrint>1.3.8", "psutil", "file_read_backwards", "setuptools>=6.0"]


# TODO:  Get fontconfig to work
#from sys import platform
#if platform == "linux" or platform == "linux2":
#    plugin_requires.append("enum34")
#    plugin_requires.append("fontconfig")

# --------------------------------------------------------------------------------------------------------------------
# More advanced options that you usually shouldn't have to touch follow after this point
# --------------------------------------d------------------------------------------------------------------------------

# Additional package data to install for this plugin. The subfolders "templates", "static" and "translations" will
# already be installed automatically if they exist. Note that if you add something here you'll also need to update
# MANIFEST.in to match to ensure that python setup.py sdist produces a source distribution that contains all your
# files. This is sadly due to how python's setup.py works, see also http://stackoverflow.com/a/14159430/2028598
plugin_additional_data = ['data/*.json', 'data/images/*.png', 'data/images/*.jpeg','data/lib/c/*.cpp','data/lib/c/*.h']
# Any additional python packages you need to install with your plugin that are not contained in <plugin_package>.*
plugin_additional_packages = []

# Any python packages within <plugin_package>.* you do NOT want to install with your plugin
plugin_ignored_packages = []

# Additional parameters for the call to setuptools.setup. If your plugin wants to register additional entry points,
# define dependency links or other things like that, this is the place to go. Will be merged recursively with the
# default setup parameters as provided by octoprint_setuptools.create_plugin_setup_parameters using
# octoprint.util.dict_merge.
#
# Example: plugin_requires = ["someDependency==dev"] additional_setup_parameters = {"dependency_links": [
#   "https://github.com/someUser/someRepo/archive/master.zip#egg=someDependency-dev"]}

copt = {
    'msvc': ['/Ox', '/fp:fast', '/GS', '/GL', '/analyze', '/Gy', '/Oi', '/MD', '/EHsc', '/Ot'],
    'mingw32': ['-fopenmp', '-O3', '-ffast-math', '-march=native'],
    'gcc': ['-O3']
}

lopt = {
    'mingw32': ['-fopenmp'],
    #'msvc': ['/DEBUG']
}


class build_ext_subclass( build_ext ):
    def build_extensions(self):
        c = self.compiler.compiler_type
        print("Compiling Octolapse Parser Extension with {0}".format(c))
        if c in copt:
            for e in self.extensions:
                e.extra_compile_args = copt[c]
        if c in lopt:
            for e in self.extensions:
                e.extra_link_args = lopt[c]
        build_ext.build_extensions(self)

## Build our c++ parser extension
plugin_ext_sources = [
    'octoprint_octolapse/data/lib/c/GcodePositionProcessor.cpp',
    'octoprint_octolapse/data/lib/c/GcodeParser.cpp',
    'octoprint_octolapse/data/lib/c/GcodePosition.cpp',
    'octoprint_octolapse/data/lib/c/ParsedCommand.cpp',
    'octoprint_octolapse/data/lib/c/ParsedCommandParameter.cpp',
    'octoprint_octolapse/data/lib/c/Position.cpp',
    'octoprint_octolapse/data/lib/c/PythonHelpers.cpp',
    'octoprint_octolapse/data/lib/c/SnapshotPlan.cpp',
    'octoprint_octolapse/data/lib/c/SnapshotPlanStep.cpp',
    'octoprint_octolapse/data/lib/c/Stabilization.cpp',
    'octoprint_octolapse/data/lib/c/StabilizationResults.cpp',
    'octoprint_octolapse/data/lib/c/StabilizationSnapToPrint.cpp',
    'octoprint_octolapse/data/lib/c/Logging.cpp'
]
cpp_gcode_parser = Extension(
    'GcodePositionProcessor',
    sources=plugin_ext_sources,
    language="c++"
)


additional_setup_parameters = {
    "ext_modules": [cpp_gcode_parser],
    "cmdclass": {"build_ext": build_ext_subclass}
}

########################################################################################################################

from setuptools import setup

try:
    import octoprint_setuptools
except:
    print("Could not import OctoPrint's setuptools, are you sure you are running that under "
          "the same python installation that OctoPrint is installed under?")
    import sys

    sys.exit(-1)

setup_parameters = octoprint_setuptools.create_plugin_setup_parameters(
    identifier=plugin_identifier,
    package=plugin_package,
    name=plugin_name,
    version=plugin_version,
    description=plugin_description,
    author=plugin_author,
    mail=plugin_author_email,
    url=plugin_url,
    license=plugin_license,
    requires=plugin_requires,
    additional_packages=plugin_additional_packages,
    ignored_packages=plugin_ignored_packages,
    additional_data=plugin_additional_data,

)

if len(additional_setup_parameters):
    from octoprint.util import dict_merge
    setup_parameters = dict_merge(setup_parameters, additional_setup_parameters)

setup(**setup_parameters)
