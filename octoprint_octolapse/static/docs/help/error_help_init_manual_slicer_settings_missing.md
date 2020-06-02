Octolapse was started, but some required slicer settings do not exist in your Octolapse printer profile.  This most likely indicates that you upgraded Octolapse, but there was some problem migrating your settings.  Fortunately this is usually an easy problem to solve

## Steps to Solve

The easiest way to fix this issue is to enable **Automatic Slicer Configuration**.  This feature does not work in all situations, however, so you might need to manually enter your settings.

### Solution 1: Use Automatic Slicer Configuration
If you are using Cura, Slic3r, Slic3r PE, PrusaSlicer or Simplify 3D, Octolapse can extract your slicer settings automatically.  If you are using a different slicer, see the **I'm using another slicer** section below.

#### Cura
Cura does not output slicer settings by default.  <a href="https://github.com/FormerLurker/Octolapse/wiki/V0.4---Automatic-Slicer-Configuration#if-you-are-using-cura-follow-these-steps" title="View the cura automatic slicer settings guide in a new window" target="_blank">See this guide</a> for enabling automatic slicer settings when using Cura.

#### Slice3r, Slic3r PE, Prusa Slicer, or Simplify 3D
Octolapse should work out of the box for these slicers.  Simply open your Octolapse printer profile and select **Automatic Configuration** from the **Slicer Type** dropdown box and save your changes.

#### I'm using another slicer
You are using a slicer that is not specifically supported by Octolapse.  [Use Manual Slicer Settings](#solution-2-use-manual-slicer-settings) below for information on how to manually enter your slicer settings into Octolapse.

If you would like for your slicer to work with **Automatic Slicer Configuration** feature, consider  <a href="https://github.com/FormerLurker/Octolapse/wiki/V0.4---Request-A-New-Feature" title="Request a Feature" target="_blank">creating a feature request</a> in the Octolapse github repository.  Make sure you read the wiki page explaining how to create a new issue.  Also, be sure to include some sample gcode, the exact slicer version, and a link to the slicer's homepage if possible.

### Solution 2: Use Manual Slicer Settings
You can manually enter the missing slicer settings into Ocotlapse.  First, open your Octolapse printer profile.  The missing settings should have a red error message below them.  You will then need to copy your slicer settings **EXACTLY** from your slicer to Octolapse.  If you are using the **Other Slicer** type, be very careful that you select the correct **Speed Display Units** (either mm/min or mm/sec) when entering any slicer speeds.  Any mistakes made while copying your slicer settings can reduce your print quality, and may even prevent Octolapse from working entirely.
