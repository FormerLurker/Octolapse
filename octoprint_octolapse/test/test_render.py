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
import os
import os.path
import random
import re
import subprocess
import unittest
import uuid
from Queue import Queue
from csv import DictWriter
from random import randint
from shutil import rmtree
from tempfile import mkdtemp, NamedTemporaryFile
import errno
# Recent versions of Pillow changed the case of the import
# Why!?
try:
    from pil import Image
except ImportError:
    from PIL import Image

from mock import Mock

from octoprint_octolapse.render import TimelapseRenderJob, Render, Rendering
from octoprint_octolapse.settings import OctolapseSettings
from octoprint_octolapse.snapshot import METADATA_FILE_NAME, METADATA_FIELDS
from octoprint_octolapse.utility import get_snapshot_filename, SnapshotNumberFormat, get_system_fonts


class TestRender(unittest.TestCase):
    @staticmethod
    def createSnapshotDir(n, capture_template=None, size=(50, 50), write_metadata=True):
        """Create n random snapshots in a named temporary folder. Return the absolute path to the directory.
        The user is responsible for deleting the directory when done."""
        # Make the temp folder.
        dir = mkdtemp() + '/'
        # Make sure any nested folders specified by the capture template exist.
        try:
            os.makedirs(os.path.dirname("{0}{1}".format(dir, capture_template) % 0))
        except OSError as e:
            if e.errno == errno.EEXIST:
                pass
            else:
                raise

        # Make images and save them with the correct names.
        random.seed(0)

        with open(os.path.join(dir, METADATA_FILE_NAME) if write_metadata else os.devnull, 'w') as f:
            writer = DictWriter(f, METADATA_FIELDS)
            for i in range(n):
                image = Image.new('RGB', size=size, color=tuple(randint(0, 255) for _ in range(3)))
                image_path = "{0}{1}".format(dir, capture_template) % i
                image.save(image_path, 'JPEG')
                writer.writerow(
                    {'snapshot_number': i, 'file_name': os.path.basename(image_path), 'time_taken': i * 1000})

        return dir

    @staticmethod
    def createWatermark():
        """Create a watermark image in a temp file. The file will be deleted when the handle is garbage collected.
        Returns the (temporary) file handle."""
        # Make the temp file.
        watermark_file = NamedTemporaryFile()
        # Make an image and save it to the temp file.
        image = Image.new('RGB', size=(50, 50), color=(0, 0, 255))
        image.save(watermark_file, 'JPEG')
        return watermark_file

    def createRenderingJob(self, rendering):
        self.on_render_start = Mock(return_value=None)
        self.on_render_success = Mock(return_value=None)
        self.on_render_error = Mock(return_value=None)
        return TimelapseRenderJob(job_id=self.rendering_job_id,
                                  rendering=rendering,
                                  logging=self.octolapse_settings.current_logging_profile(),
                                  print_filename=self.print_name,
                                  capture_dir=self.snapshot_dir_path,
                                  snapshot_filename_format=self.capture_template,
                                  output_tokens=Render._get_output_tokens(self.data_directory, "COMPLETED",
                                                                          self.print_name,
                                                                          self.print_start_time,
                                                                          self.print_end_time),
                                  octoprint_timelapse_folder=self.octoprint_timelapse_folder,
                                  ffmpeg_path=self.ffmpeg_path,
                                  threads=1,
                                  time_added=0,
                                  on_render_start=self.on_render_start,
                                  on_success=self.on_render_success,
                                  on_error=self.on_render_error,
                                  clean_after_success=True,
                                  clean_after_fail=True)

    def doTestCodec(self, name, extension, codec_name):
        """
        Tests a particular codec setup.
        :param name: The internal Octolapse name of the codec.
        :param extension: The file extension we should expect out of this configuration.
        :param codec_name: The expected name that ffprobe should return for this codec.
        """
        self.snapshot_dir_path = TestRender.createSnapshotDir(10, self.capture_template, size=(50, 50))
        # Create the job.
        r = Rendering(guid=uuid.uuid4(), name="Use {} codec".format(name))
        r.update({'output_format': name})
        job = self.createRenderingJob(rendering=r)

        # Start the job.
        job._render()

        # Assertions.
        self.on_render_start.assert_called_once()
        self.on_render_success.assert_called_once()
        self.on_render_error.assert_not_called()
        output_files = os.listdir(self.octoprint_timelapse_folder)
        self.assertEqual(len(output_files), 1,
                         "Incorrect amount of output files detected! Found {}. Expected only timelapse output.".format(
                             output_files))
        output_filename = output_files[0]
        self.assertRegexpMatches(output_filename, re.compile('.*\.{}$'.format(extension), re.IGNORECASE))
        output_filepath = os.path.join(self.octoprint_timelapse_folder, output_filename)
        self.assertGreater(os.path.getsize(output_filepath), 0)
        # Check the codec using ffprobe to make sure it matches what we expect.
        actual_codec = subprocess.check_output(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name",
             "-of", "default=noprint_wrappers=1:nokey=1", output_filepath]).strip()
        self.assertEqual(actual_codec, codec_name)

    def setUp(self):
        self.octolapse_settings = OctolapseSettings(NamedTemporaryFile().name)
        self.rendering_job_id = "job_id"

        self.print_name = "print_name"
        self.print_start_time = 0
        self.print_end_time = 100

        # Create fake snapshots.
        self.capture_template = get_snapshot_filename(self.print_name, SnapshotNumberFormat)
        self.data_directory = mkdtemp()
        self.octoprint_timelapse_folder = mkdtemp()

        self.ffmpeg_path = "ffmpeg"
        self.render_task_queue = Queue(maxsize=1)
        self.render_task_queue.put(self.rendering_job_id)

    def tearDown(self):
        rmtree(self.snapshot_dir_path)
        rmtree(self.data_directory)
        rmtree(self.octoprint_timelapse_folder)

    def test_basicRender(self):
        self.snapshot_dir_path = TestRender.createSnapshotDir(10, self.capture_template, size=(50, 50))
        # Create the job.
        job = self.createRenderingJob(rendering=None)

        # Start the job.
        job._render()

        # Assertions.
        self.on_render_start.assert_called_once()
        self.on_render_success.assert_called_once()
        self.on_render_error.assert_not_called()
        output_files = os.listdir(self.octoprint_timelapse_folder)
        self.assertEqual(len(output_files), 1,
                         "Incorrect amount of output files detected! Found {}. Expected only timelapse output.".format(
                             output_files))
        output_filename = output_files[0]
        self.assertRegexpMatches(output_filename, re.compile('.*\.mp4$', re.IGNORECASE))
        self.assertGreater(os.path.getsize(os.path.join(self.octoprint_timelapse_folder, output_filename)), 0)

    def test_noMetadata(self):
        self.snapshot_dir_path = TestRender.createSnapshotDir(10, self.capture_template, size=(50, 50),
                                                              write_metadata=False)
        # Create the job.
        job = self.createRenderingJob(rendering=None)

        # Start the job.
        job._render()

        # Assertions.
        self.on_render_start.assert_called_once()
        self.on_render_success.assert_called_once()
        self.on_render_error.assert_not_called()
        output_files = os.listdir(self.octoprint_timelapse_folder)
        self.assertEqual(len(output_files), 1,
                         "Incorrect amount of output files detected! Found {}. Expected only timelapse output.".format(
                             output_files))
        output_filename = output_files[0]
        self.assertRegexpMatches(output_filename, re.compile('.*\.mp4$', re.IGNORECASE))
        self.assertGreater(os.path.getsize(os.path.join(self.octoprint_timelapse_folder, output_filename)), 0)

    def test_noffmpeg(self):
        self.snapshot_dir_path = TestRender.createSnapshotDir(10, self.capture_template, size=(50, 50),
                                                              write_metadata=False)
        # Create the job.
        job = self.createRenderingJob(rendering=None)
        job._ffmpeg = None

        # Start the job.
        job._render()

        # Assertions.
        self.on_render_start.assert_called_once()
        self.on_render_success.assert_not_called()
        self.on_render_error.assert_called_once()
        output_files = os.listdir(self.octoprint_timelapse_folder)
        self.assertEqual(len(output_files), 0, "Expected no output files to be generated.".format(output_files))

    def test_watermark(self):
        self.snapshot_dir_path = TestRender.createSnapshotDir(10, self.capture_template, size=(50, 50))
        # Create the job.
        watermark_file = self.createWatermark()
        r = Rendering(guid=uuid.uuid4(), name="Render with Watermark")
        r.update({'enable_watermark': True, 'selected_watermark': watermark_file.name})
        job = self.createRenderingJob(rendering=r)

        # Start the job.
        job._render()

        # Assertions.
        self.on_render_start.assert_called_once()
        self.on_render_success.assert_called_once()
        self.on_render_error.assert_not_called()
        output_files = os.listdir(self.octoprint_timelapse_folder)
        self.assertEqual(len(output_files), 1,
                         "Incorrect amount of output files detected! Found {}. Expected only timelapse output.".format(
                             output_files))
        output_filename = output_files[0]
        self.assertRegexpMatches(output_filename, re.compile('.*\.mp4$', re.IGNORECASE))
        self.assertGreater(os.path.getsize(os.path.join(self.octoprint_timelapse_folder, output_filename)), 0)

    # True parameterized testing in unittest seems pretty complicated.
    # I'll just manually generate tests for items in this list.
    CODECS_AND_EXTENSIONS = {'avi': dict(name='avi', extension='avi', codec_name='mpeg4'),
                             'flv': dict(name='flv', extension='flv', codec_name='flv'),
                             'gif': dict(name='gif', extension='gif', codec_name='gif'),
                             'h264': dict(name='h264', extension='mp4', codec_name='h264'),
                             'mp4': dict(name='mp4', extension='mp4', codec_name='mpeg4'),
                             'mpeg': dict(name='mpeg', extension='mpeg', codec_name='mpeg2video'),
                             'vob': dict(name='vob', extension='vob', codec_name='mpeg2video')}

    def test_avi_codec(self):
        self.doTestCodec(**self.CODECS_AND_EXTENSIONS['avi'])

    def test_flv_codec(self):
        self.doTestCodec(**self.CODECS_AND_EXTENSIONS['flv'])

    def test_gif_codec(self):
        self.doTestCodec(**self.CODECS_AND_EXTENSIONS['gif'])

    def test_h264_codec(self):
        self.doTestCodec(**self.CODECS_AND_EXTENSIONS['h264'])

    def test_mp4_codec(self):
        self.doTestCodec(**self.CODECS_AND_EXTENSIONS['mp4'])

    def test_mpeg_codec(self):
        self.doTestCodec(**self.CODECS_AND_EXTENSIONS['mpeg'])

    def test_vob_codec(self):
        self.doTestCodec(**self.CODECS_AND_EXTENSIONS['vob'])

    def test_overlay(self):
        self.snapshot_dir_path = TestRender.createSnapshotDir(10, self.capture_template, size=(640, 480))
        # Create the job.
        r = Rendering(guid=uuid.uuid4(), name="Render with overlay")
        r.update({'overlay_text_template': "Current Time: {current_time}\nTime elapsed: {time_elapsed}",
                  'overlay_font_path': get_system_fonts()[0]})
        job = self.createRenderingJob(rendering=r)

        # Start the job.
        job._render()

        # Assertions.
        self.on_render_start.assert_called_once()
        self.on_render_success.assert_called_once()
        self.on_render_error.assert_not_called()
        output_files = os.listdir(self.octoprint_timelapse_folder)
        self.assertEqual(len(output_files), 1,
                         "Incorrect amount of output files detected! Found {}. Expected only timelapse output.".format(
                             output_files))
        output_filename = output_files[0]
        self.assertRegexpMatches(output_filename, re.compile('.*\.mp4$', re.IGNORECASE))
        output_filepath = os.path.join(self.octoprint_timelapse_folder, output_filename)
        self.assertGreater(os.path.getsize(output_filepath), 0)

    def test_overlay_invalid_font(self):
        self.snapshot_dir_path = TestRender.createSnapshotDir(10, self.capture_template, size=(640, 480))
        # Create the job.
        r = Rendering(guid=uuid.uuid4(), name="Render with overlay")
        r.update({'overlay_text_template': "Current Time: {current_time}\nTime elapsed: {time_elapsed}",
                  'overlay_font_path': '/dev/null'})
        job = self.createRenderingJob(rendering=r)

        # Start the job.
        job._render()

        # Assertions.
        self.on_render_start.assert_called_once()
        self.on_render_success.assert_not_called()
        self.on_render_error.assert_called_once()
        output_files = os.listdir(self.octoprint_timelapse_folder)
        self.assertEqual(len(output_files), 0, "Expected no output files to be generated.".format(output_files))
