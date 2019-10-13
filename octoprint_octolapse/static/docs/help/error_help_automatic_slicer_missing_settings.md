Octolapse was unable to detect some slicer settings within your gcode file.  This usually means that you are using cura, but have used the wrong start gcode script for the cura version you are using.  It could also mean that your settings file was manually edited, and some settings were removed, or that the gcode file is corrupt.

###Steps to Solve

#### I'm using Cura
Cura does not output slicer settings by default.  <a href="https://github.com/FormerLurker/Octolapse/wiki/Automatic-Slicer-Settings#install-the-cura-settings-script" title="View the cura automatic slicer settings guide in a new window" target="_blank">See this guide</a> for enabling automatic slicer settings when using Cura.

#### I'm using Slice3r, Slic3r PE, Prusa Slicer, or Simplify 3D
Octolapse should work out of the box for these slicers.  It's possible that you are using a version that Octolapse does not support.  Please <a href="https://github.com/FormerLurker/Octolapse/issues/new" title="Create an issue in the Octolapse github repository" target="_blank">report this issue here</a>, and be sure to include your gcode file (preferably using <a href="https://github.com/FormerLurker/Octolapse/issues/new" title="Upload you gcode to gist.github.com." target="_blank">gist.github.com</a>), and the exact slicer version.

#### I'm using another slicer
You are using a slicer that is not supported by Octolapse.  See the [Use Manual Slicer Settings](#use-manual-slicer-settings) section below.

If you would like for your slicer to work with **Automatic Slicer Configuration** feature, consider  <a href="https://github.com/FormerLurker/Octolapse/issues/new" title="Create an issue in the Octolapse github repository" target="_blank">creating an issue</a> in the Octolapse github repository.  Be sure to include some sample gcode (preferably using <a href="https://github.com/FormerLurker/Octolapse/issues/new" title="Upload you gcode to gist.github.com." target="_blank">gist.github.com</a>), and the exact slicer version, and a link to the slicer's homepage if possible.

#### Reslice your gocde file
If none of the above suggestions has worked, try re-slicing your gcode file.  It's possible that some corruption has occurred.  Next, upload the gocde to Octoprint, and try to print with the resliced gcode file.

#### Use manual slicer settings
If Octolapse can't extract your slicer settings from your gcode file, you instead provide your slicer settings to Octolapse directly.  First, open up your Octoprint printer profile.  Next, select your slicer type from the **Slicer Type** dropdown box.  If your slicer type dosen't appear in the list, choose **Other Slicer**.  You will then need to copy your slicer settings **EXACTLY** from your slicer to Octolapse.  If you are using the **Other Slicer** type, be very careful that you select the correct **Speed Display Units** (either mm/min or mm/sec) when entering any slicer speeds.  Any mistakes made while copying your slicer settings can reduce your print quality, and may even prevent Octolapse from working entirely.  
