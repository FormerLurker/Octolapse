If your printer has more than one nozzle, and you have firmware offsets for each nozzle stored in your firmware, you will need to configure this in the Octolapse printer profile.  Octolapse uses these offsets to determine where your printhead is over the bed, which taking the position of each extruder into account.

Check your slicer settings and make sure the offsets aren't entered in there first.  In general if your slicer is adjusting the gcode to account for the offsets, you can leave all of the offsets in Octolapse at 0.

Octolapse can read the offsets from certain gcodes (G10 and M218), but ONLY if these gcodes appear in your gcode file for every extruder.  I recommend manually entering the offsets if at all possible just in case.  

Note that if your printer has a single nozzle but supports multiple materials (like the Prusa MMU), you should check the **Shared Extruder** option.  After that no extruder offsets will need to be entered.

