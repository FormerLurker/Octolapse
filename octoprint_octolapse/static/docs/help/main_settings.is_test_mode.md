Test mode can be used to test your timelapse settings without wasting filament or waiting for your printer to warm up.  When test mode is enabled, your printer will not warm up, fans will not be engaged, and filament will not be extruded.

Test mode must be activated BEFORE starting a print. Changing this setting mid-print won't alter any current prints.

Before using test mode, **UNLOAD YOUR FILAMENT**! Even though I attempted to strip all extruder commands, there's a chance that I missed some cases. Please let me know if you see any 'cold extrusion prevented' errors in the terminal window. If you do, please send me your GCode!

#### How to Enable/Disable Test Mode

You can enable or disable test mode in two ways:

1.  Expand the **Current Run Configuration** within the Octolapse tab and click on **Test Mode** to toggle the setting.
2.  Open the Octolapse **Main Settings** by clicking on the <i class="fa fa-gear"></i> (gear) icon within the Octolapse tab, then click on the **Edit Main Settings** button to edit the Octlapse main settings.  You can find and edit **Test Mode** there.  Be sure to save your changes!

#### Important Safety Information

**NEVER** print with your printer unattended, and that includes running Octolapse in test mode.  After starting a test mode print, make sure your extruder and build plate do not warm up, and that your extruder isn't moving.  If your build plate or extruder warms up, or if your extruder gear is turning with test mode enabled, DISCONTINUE THE PRINT and please report the problem in the Octolapse github issues page.
