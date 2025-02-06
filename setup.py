# coding=utf-8
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import sys
import versioneer
import configparser  # Ändere hier den Import

########################################################################################################################
# The plugin's identifier, has to be unique
plugin_identifier = "octolapse"
plugin_package = "octoprint_octolapse"
plugin_name = "Octolapse"
fallback_version = "1.0.0"
plugin_version = versioneer.get_versions()["version"]

plugin_cmdclass = versioneer.get_cmdclass()
plugin_description = """Create stabilized timelapses of your 3d prints. Highly customizable, loads of presets, lots of fun."""
plugin_author = "Brad Hochgesang"
plugin_author_email = "FormerLurker@pm.me"
plugin_url = "https://github.com/FormerLurker/Octolapse"
plugin_license = "AGPLv3"
plugin_requires = ["pillow>=9.3,<11", "sarge", "six", "OctoPrint>=1.4.0", "psutil", "file_read_backwards", "setuptools>=6.0", "awesome-slugify>=1.6.5,<1.7"]

# --------------------------------------------------------------------------------------------------------------------
# More advanced options that you usually shouldn't have to touch follow after this point

plugin_additional_data = [
    'data/*.json',
    'data/images/*.png',
    'data/images/*.jpeg',
    'data/lib/c/*.cpp',
    'data/lib/c/*.h',
    'data/webcam_types/*',
    'data/fonts/*'
]
plugin_additional_packages = ['octoprint_octolapse_setuptools']
plugin_ignored_packages = []

# C++ Extension compiler options
DEBUG = False
compiler_opts = {
    'extra_compile_args': ['-O3', '-std=c++11'],
    'extra_link_args': [],
    'define_macros': [('IS_PYTHON_EXTENSION', '1')]
}

if DEBUG:
    compiler_opts = {
        'extra_compile_args': [],
        'extra_link_args': [],
        'define_macros': [('DEBUG_chardet', '1'), ('IS_PYTHON_EXTENSION', '1')]
    }

class build_ext_subclass(build_ext):
    def build_extensions(self):
        print("Compiling Octolapse Parser Extension with {0}.".format(self.compiler))

        for ext in self.extensions:
            ext.extra_compile_args.extend(compiler_opts['extra_compile_args'])
            ext.extra_link_args.extend(compiler_opts['extra_link_args'])
            ext.define_macros.extend(compiler_opts['define_macros'])
        build_ext.build_extensions(self)

        for extension in self.extensions:
            print(f"Build Extensions for {extension.name} - extra_compile_args: {extension.extra_compile_args} - extra_link_args: {extension.extra_link_args} - define_macros: {extension.define_macros}")

# Define the C++ Extension
plugin_ext_sources = [
    'octoprint_octolapse/data/lib/c/gcode_position_processor.cpp',
    'octoprint_octolapse/data/lib/c/gcode_parser.cpp',
    'octoprint_octolapse/data/lib/c/gcode_position.cpp',
    'octoprint_octolapse/data/lib/c/parsed_command.cpp',
    'octoprint_octolapse/data/lib/c/parsed_
