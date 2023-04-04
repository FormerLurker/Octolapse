# coding=utf-8
from setuptools import setup, Extension
from distutils.command.build_ext import build_ext
from distutils.ccompiler import CCompiler
from distutils.unixccompiler import UnixCCompiler
from distutils.msvccompiler import MSVCCompiler
from distutils.bcppcompiler import BCPPCompiler
from distutils.cygwinccompiler import CygwinCCompiler
from distutils.version import LooseVersion
from octoprint_octolapse_setuptools import NumberedVersion
import sys
import versioneer
########################################################################################################################
# The plugin's identifier, has to be unique
plugin_identifier = "octolapse"
# The plugin's python package, should be "octoprint_<plugin identifier>", has to be unique
plugin_package = "octoprint_octolapse"
# The plugin's human readable name. Can be overwritten within OctoPrint's internal data via __plugin_name__ in the
# plugin module
plugin_name = "Octolapse"
# The plugin's fallback version, in case versioneer can't extract the version from _version.py.
# This can happen if the user installs from one of the .zip links in github, not generated with git archive
fallback_version = NumberedVersion.clean_version(NumberedVersion.CurrentVersion)
# Get the cleaned version number from versioneer
plugin_version = NumberedVersion.clean_version(versioneer.get_versions(verbose=True)["version"])

# Depending on the installation method, versioneer might not know the current version
# if plugin_version == "0+unknown" or NumberedVersion(plugin_version) < NumberedVersion(fallback_version):
if plugin_version == "0+unknown":
    plugin_version = fallback_version
    try:
        # This generates version in the following form:
        #   0.4.0rc1+?.GUID_GOES_HERE
        plugin_version += "+u." + versioneer.get_versions()['full-revisionid'][0:7]
    except:
        pass

plugin_cmdclass = versioneer.get_cmdclass()
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
plugin_requires = ["pillow>=9.3,<11", "sarge", "six", "OctoPrint>=1.4.0", "psutil", "file_read_backwards",
                   "setuptools>=6.0", "awesome-slugify>=1.6.5,<1.7"]

import octoprint.server
if LooseVersion(octoprint.server.VERSION) < LooseVersion("1.4"):
    plugin_requires.extend(["flask_principal>=0.4,<1.0"])

# enable faulthandler for python 3.
if (3, 0) < sys.version_info < (3, 3):
    print("Adding faulthandler requirement.")
    plugin_requires.append("faulthandler>=3.1")

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
plugin_additional_data = [
    'data/*.json',
    'data/images/*.png',
    'data/images/*.jpeg',
    'data/lib/c/*.cpp',
    'data/lib/c/*.h',
    'data/webcam_types/*',
    'data/fonts/*'
]
# Any additional python packages you need to install with your plugin that are not contained in <plugin_package>.*
plugin_additional_packages = ['octoprint_octolapse_setuptools']

# Any python packages within <plugin_package>.* you do NOT want to install with your plugin
plugin_ignored_packages = []

# C++ Extension compiler options
# Set debug mode
DEBUG = False
# define compiler flags
compiler_opts = {
    CCompiler.compiler_type: {
        'extra_compile_args': ['-O3', '-std=c++11'],
        'extra_link_args': [],
        'define_macros': [('IS_PYTHON_EXTENSION', '1')]
    },
    MSVCCompiler.compiler_type: {
        'extra_compile_args': ['/O2', '/fp:fast', '/GL', '/analyze', '/Gy', '/MD', '/EHsc'],
        'extra_link_args': [],
        'define_macros': [('IS_PYTHON_EXTENSION', '1')]
    },
    UnixCCompiler.compiler_type: {
        'extra_compile_args': ['-O3', '-std=c++11'],
        'extra_link_args': [],
        'define_macros': [('IS_PYTHON_EXTENSION', '1')]
    },
    BCPPCompiler.compiler_type: {
        'extra_compile_args': ['-O3', '-std=c++11'],
        'extra_link_args': [],
        'define_macros': [('IS_PYTHON_EXTENSION', '1')]
    },
    CygwinCCompiler.compiler_type: {
        'extra_compile_args': ['-O3', '-std=c++11'],
        'extra_link_args': [],
        'define_macros': [('IS_PYTHON_EXTENSION', '1')]
    }
}

if DEBUG:
    compiler_opts = {
        CCompiler.compiler_type: {
            'extra_compile_args': [],
            'extra_link_args': [],
            'define_macros': [('DEBUG_chardet', '1'), ('IS_PYTHON_EXTENSION', '1')]
        },
        MSVCCompiler.compiler_type: {
            'extra_compile_args': ['/EHsc', '/Z7'],
            'extra_link_args': ['/DEBUG'],
            'define_macros': [('IS_PYTHON_EXTENSION', '1')]
        },
        UnixCCompiler.compiler_type: {
            'extra_compile_args': ['-g'],
            'extra_link_args': ['-g'],
            'define_macros': [('IS_PYTHON_EXTENSION', '1')]
        },
        BCPPCompiler.compiler_type: {
            'extra_compile_args': [],
            'extra_link_args': [],
            'define_macros': [('IS_PYTHON_EXTENSION', '1')]
        },
        CygwinCCompiler.compiler_type: {
            'extra_compile_args': [],
            'extra_link_args': [],
            'define_macros': [('IS_PYTHON_EXTENSION', '1')]
        }
    }

class build_ext_subclass(build_ext):
    def build_extensions(self):
        print("Compiling Octolapse Parser Extension with {0}.".format(self.compiler))

        c = self.compiler
        opts = [v for k, v in compiler_opts.items() if c.compiler_type == k]
        for e in self.extensions:
            for o in opts:
                for attrib, value in o.items():
                    getattr(e, attrib).extend(value)
        build_ext.build_extensions(self)

        for extension in self.extensions:
            print("Build Extensions for {0} - extra_compile_args:{1} - extra_link_args:{2} - define_macros:{3}".format(
                extension.name, extension.extra_compile_args, extension.extra_link_args, extension.define_macros)
            )


## Build our c++ parser extension
plugin_ext_sources = [
    'octoprint_octolapse/data/lib/c/gcode_position_processor.cpp',
    'octoprint_octolapse/data/lib/c/gcode_parser.cpp',
    'octoprint_octolapse/data/lib/c/gcode_position.cpp',
    'octoprint_octolapse/data/lib/c/parsed_command.cpp',
    'octoprint_octolapse/data/lib/c/parsed_command_parameter.cpp',
    'octoprint_octolapse/data/lib/c/position.cpp',
    'octoprint_octolapse/data/lib/c/python_helpers.cpp',
    'octoprint_octolapse/data/lib/c/snapshot_plan.cpp',
    'octoprint_octolapse/data/lib/c/snapshot_plan_step.cpp',
    'octoprint_octolapse/data/lib/c/stabilization.cpp',
    'octoprint_octolapse/data/lib/c/stabilization_results.cpp',
    'octoprint_octolapse/data/lib/c/stabilization_smart_layer.cpp',
    'octoprint_octolapse/data/lib/c/stabilization_smart_gcode.cpp',
    'octoprint_octolapse/data/lib/c/logging.cpp',
    'octoprint_octolapse/data/lib/c/utilities.cpp',
    'octoprint_octolapse/data/lib/c/trigger_position.cpp',
    'octoprint_octolapse/data/lib/c/gcode_comment_processor.cpp',
    'octoprint_octolapse/data/lib/c/extruder.cpp'
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
    cmdclass=plugin_cmdclass
)

if len(additional_setup_parameters):
    from octoprint.util import dict_merge
    setup_parameters = dict_merge(setup_parameters, additional_setup_parameters)

setup(**setup_parameters)
