# coding=utf-8
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import sys
import platform

# Versioneer import with fallback
try:
    import versioneer
    cmdclass = versioneer.get_cmdclass()
except (ImportError, AttributeError):
    print("Warning: versioneer not available, using fallback version")
    cmdclass = {}
    def get_version():
        return "0.4.51"
    def get_cmdclass():
        return {}
    class _versioneer:
        get_version = staticmethod(get_version)
        get_cmdclass = staticmethod(get_cmdclass)
    versioneer = _versioneer

# Compiler options
compiler_opts = {
    'extra_compile_args': [],
    'extra_link_args': [],
    'define_macros': [('DEBUG_chardet', '1'), ('IS_PYTHON_EXTENSION', '1')]
}

# Platform-specific compiler flags
if sys.platform == 'win32':
    compiler_opts['extra_compile_args'].extend(['/std:c++14', '/permissive-'])
elif sys.platform == 'darwin':
    compiler_opts['extra_compile_args'].extend(['-std=c++14', '-mmacosx-version-min=10.9'])
else:
    compiler_opts['extra_compile_args'].append('-std=c++14')

class build_ext_subclass(build_ext):
    def build_extensions(self):
        # Detect compiler type
        compiler_type = self.compiler.compiler_type if hasattr(self.compiler, 'compiler_type') else 'unix'
        
        print(f"Compiling Octolapse Parser Extension with {compiler_type}.")

        for ext in self.extensions:
            ext.extra_compile_args.extend(compiler_opts['extra_compile_args'])
            ext.extra_link_args.extend(compiler_opts['extra_link_args'])
            ext.define_macros.extend(compiler_opts['define_macros'])
        
        build_ext.build_extensions(self)

# Update cmdclass with our custom build_ext
cmdclass['build_ext'] = build_ext_subclass

def package_data_dirs(source, sub_folders):
    dirs = [source]
    for folder in sub_folders:
        dirs.append(source + '/' + folder)
    
    ret = []
    for d in dirs:
        for dirname, _, files in os.walk(d):
            for filename in files:
                filepath = os.path.join(dirname, filename)
                ret.append(filepath[len(source)+1:])
    return ret

def get_requirements(requirements_path):
    requirements = []
    with open(requirements_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and line != '.':
                requirements.append(line)
    return requirements

import os
requirements = get_requirements('requirements.txt')

setup(
    name="Octolapse",
    version=versioneer.get_version(),
    cmdclass=cmdclass,
    description="Create a stabilized timelapse of your 3D prints.",
    long_description="Octolapse is designed to make stabilized timelapses of your prints with as little hassle as possible, and it's extremely configurable.",
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: System :: Monitoring'
    ],
    author="Brad Hochgesang",
    author_email="FormerLurker@pm.me",
    url="https://github.com/FormerLurker/Octolapse/",
    license="GNU Affero General Public License v3",
    packages=["octoprint_octolapse",
              "octoprint_octolapse_setuptools"],
    package_data={
        "octoprint_octolapse": package_data_dirs(
            'octoprint_octolapse',
            ['data', 'static', 'templates']
        )
    },
    include_package_data=True,
    zip_safe=False,
    install_requires=requirements,
    extras_require={
        'develop': [
            'mock>=2.0.0',
        ]
    },
    entry_points={
        "octoprint.plugin": [
            "octolapse = octoprint_octolapse"
        ]
    },
    ext_modules=[
        Extension(
            'GcodePositionProcessor',
            sources=[
                'octoprint_octolapse/data/lib/c/gcode_parser.cpp',
                'octoprint_octolapse/data/lib/c/extruder.cpp',
                'octoprint_octolapse/data/lib/c/gcode_position.cpp',
                'octoprint_octolapse/data/lib/c/position.cpp',
                'octoprint_octolapse/data/lib/c/stabilization.cpp',
                'octoprint_octolapse/data/lib/c/stabilization_smart_layer.cpp',
                'octoprint_octolapse/data/lib/c/stabilization_smart_gcode.cpp',
                'octoprint_octolapse/data/lib/c/stabilization_results.cpp',
                'octoprint_octolapse/data/lib/c/trigger_position.cpp',
                'octoprint_octolapse/data/lib/c/snapshot_plan.cpp',
                'octoprint_octolapse/data/lib/c/snapshot_plan_step.cpp',
                'octoprint_octolapse/data/lib/c/parsed_command.cpp',
                'octoprint_octolapse/data/lib/c/parsed_command_parameter.cpp',
                'octoprint_octolapse/data/lib/c/gcode_comment_processor.cpp',
                'octoprint_octolapse/data/lib/c/gcode_position_processor.cpp',
                'octoprint_octolapse/data/lib/c/python_helpers.cpp',
                'octoprint_octolapse/data/lib/c/logging.cpp',
                'octoprint_octolapse/data/lib/c/utilities.cpp',
            ],
            include_dirs=['octoprint_octolapse/data/lib/c'],
            language='c++',
        )
    ]
)
