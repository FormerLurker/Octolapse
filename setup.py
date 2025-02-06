# coding=utf-8
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import sys
import versioneer

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

# Ensure OctoPrint's setuptools is available
try:
    import octoprint_setuptools
except ImportError:
    print("Could not import OctoPrint's setuptools, are you sure you are running under the correct Python environment?")
    sys.exit(-1)

# Generate the setup parameters
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

# Merge additional setup parameters
if len(additional_setup_parameters):
    from octoprint.util import dict_merge
    setup_parameters = dict_merge(setup_parameters, additional_setup_parameters)

# Run the setup function
setup(**setup_parameters)
