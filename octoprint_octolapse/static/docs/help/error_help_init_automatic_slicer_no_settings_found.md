You are using **Automatic Slicer Settings**, and Octolapse was unable to detect any slicer settings within your gcode file.  This usually means one of the following things:

1.  You are using Cura, but have not added the settings script to your start gcode.
2.  You are using a printer with multiple extuders or a multi-material printer with a shared nozzle.
3.  You are using an unsupported slicer type.  Automatic Settings are only supported currently when using Cura, PrusaSlicer/Slic3r/Slic3rPE, and Simplify 3D.
4.  It could also mean that your settings file was manually edited, and some settings were removed, or that the gcode file is corrupt.

See the sections below for more detailed help

#### I'm using Cura
Cura does not output slicer settings by default.  <a href="https://github.com/FormerLurker/Octolapse/wiki/V0.4---Automatic-Slicer-Configuration#if-you-are-using-cura-follow-these-steps" title="View the cura automatic slicer settings guide in a new window" target="_blank">See this guide</a> for enabling automatic slicer settings when using Cura.  If you continue to have a problem, see the [Report an Issue](#report-an-issue) section below.

#### I'm using a multi-material or multi-extruder printer
Support for multi-extruder and multi-material printers is beta.  Do not use Octolapse on these printers unless you are comfortable using a beta feature.  There are likely still some issues extracting settings, and could be other undiscovered issues.  Please use caution, as bugs in the software my exist and cause damage and/or failed prints.

I have tested several multi-material prints on my Prusa MMU2, but have NOT tried a multi-extruder system.  If you are brave and would like to test this, please report your findings!

Please report any issues with multi-material/multi-extruder printers by looking at the section below titled [Report an Issue](#report-an-issue).

#### I'm using Simplify 3D
Octolapse should work out of the box for these Simplify 3d.  Please see the [Report an Issue](#report-an-issue) section below for assistance.

#### I'm using another slicer
You are using a slicer that is not supported by Octolapse.  See the [Use Manual Slicer Settings](#use-manual-slicer-settings) section below.

If you would like for your slicer to work with **Automatic Slicer Configuration** feature, consider  <a href="https://github.com/FormerLurker/Octolapse/wiki/V0.4---Request-A-New-Feature" title="Request a Feature" target="_blank">creating a feature request</a> in the Octolapse github repository.  Make sure you read the wiki page explaining how to create a new issue.  Also, be sure to include some sample gcode, the exact slicer version, and a link to the slicer's homepage if possible.

#### Reslice your gocde file
If none of the above suggestions has worked, try re-slicing your gcode file.  It's possible that some corruption has occurred.  Next, upload the gocde to Octoprint, and try to print with the resliced gcode file

#### Use Manual Slicer Settings
If Octolapse can't extract your slicer settings from your gcode file, you instead provide your slicer settings to Octolapse directly.  First, open up your Octoprint printer profile.  Next, select your slicer type from the **Slicer Type** dropdown box.  If your slicer type dosen't appear in the list, choose **Other Slicer**.  You will then need to copy your slicer settings **EXACTLY** from your slicer to Octolapse.  If you are using the **Other Slicer** type, be very careful that you select the correct **Speed Display Units** (either mm/min or mm/sec) when entering any slicer speeds.  Any mistakes made while copying your slicer settings can reduce your print quality, and may even prevent Octolapse from working entirely.

#### Report an Issue
This feature is still experimental, and has a few known issues and limitations.  If you are willing to help me debug your problem (which takes time and effort for both of us), please <a href="https://github.com/FormerLurker/Octolapse/wiki/V0.4---Reporting-An-Issue" title="How to report an issue in the Octolapse github repository" target="_blank">see this guide for reporting an issue</a>.  When you submit your issue, be sure to include your gcode file, and the exact slicer version you used to create your gcode file.
