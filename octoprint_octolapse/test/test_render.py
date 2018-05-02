# coding=utf-8
##################################################################################
# Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
# Copyright (C) 2017  Brad Hochgesang
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
import unittest
import uuid
from Queue import Queue
from shutil import rmtree
from tempfile import mkdtemp, NamedTemporaryFile

from PIL import Image

from octoprint_octolapse.render import TimelapseRenderJob, Render, Rendering
from octoprint_octolapse.settings import OctolapseSettings
from octoprint_octolapse.utility import get_snapshot_filename, SnapshotNumberFormat


class TestRender(unittest.TestCase):
    @staticmethod
    def createSnapshotDir(n, capture_template):
        """Create n random snapshots in a named temporary folder. Return the absolute path to the directory.
        The user is responsible for deleting the directory when done."""
        # Make the temp folder.
        dir = mkdtemp() + '/'
        # Make sure any nested folders specified by the capture template exist.
        os.makedirs(os.path.dirname("{0}{1}".format(dir, capture_template) % 0))
        # Make images and save them with the correct names.
        for i in range(n):
            image = Image.new('RGB', size=(50, 50), color=(155, 0, 0))
            image_path = "{0}{1}".format(dir, capture_template) % i
            image.save(image_path, 'JPEG')
        return dir

    @staticmethod
    def createWatermark():
        """Create a watermark image in a temp file. The file will be deleted when the handle is garbage collected.
        Returns the (temporary) file handle."""
        # Make the temp file.
        watermark_file = NamedTemporaryFile()
        # Make an images and save it to the temp file.
        image = Image.new('RGB', size=(50, 50), color=(155, 0, 0))
        image.save(watermark_file, 'JPEG')
        return watermark_file

    def createRenderingJob(self, rendering):
        self.job = TimelapseRenderJob(job_id=self.rendering_job_id,
                                      rendering=rendering,
                                      debug=self.octolapse_settings.current_debug_profile(),
                                      print_filename=self.print_name,
                                      capture_dir=self.snapshot_dir_path,
                                      capture_template=self.capture_template,
                                      output_tokens=Render._get_output_tokens(self.data_directory, "COMPLETED",
                                                                              self.print_name,
                                                                              self.print_start_time,
                                                                              self.print_end_time),
                                      octoprint_timelapse_folder=self.octoprint_timelapse_folder,
                                      ffmpeg_path=self.ffmpeg_path,
                                      threads=1,
                                      rendering_task_queue=self.render_task_queue,
                                      time_added=0,
                                      on_render_start=lambda job_id, payload: None,
                                      on_complete=lambda job_id, payload: None,
                                      clean_after_success=True,
                                      clean_after_fail=True)

    def setUp(self):
        self.rendering_job_id = "job_id"
        self.octolapse_settings = OctolapseSettings(NamedTemporaryFile().name)

        self.print_name = "print_name"
        self.print_start_time = 0
        self.print_end_time = 100

        # Create fake snapshots.
        self.capture_template = get_snapshot_filename(self.print_name, self.print_start_time, SnapshotNumberFormat)
        self.snapshot_dir_path = TestRender.createSnapshotDir(10, self.capture_template)
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
        # Create the job.
        self.createRenderingJob(rendering=None)

        # Start the job.
        self.job.process()

        # Wait for the job to finish.
        self.job._thread.join()

    def test_watermark(self):
        # Create the job.
        r = Rendering(guid=uuid.uuid4(), name="Render with Watermark")
        r.update({"watermark": True})
        self.createRenderingJob(rendering=r)

        # Start the job.
        self.job.process()

        # Wait for the job to finish.
        self.job._thread.join()
