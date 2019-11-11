Your gcode file, created from Simplify3D, contains a different number of defined extruders than the number of extruders defined in your printer profile.

To solve this problem first make sure your Octolapse printer profile has the correct number of extruders configured.  If your printer has multiple physical extruders, or supports multiple materials (like the Prusa MMU1 and MMU2), make sure your Octolapse printer profile has the **Firmware Settings->Number of Extruders/Materials** setting correct.  You may have to enter extruder offsets if your printer has multiple physical extruders.  Also, the **First Extruder is 0** setting must be correct.  If your printer uses the **T0** command to select the first extruder, check this box.  If your printer uses **T1** as the first extruder, uncheck this box.

Next, open Simplify3D and edit your process.  Click on the **Extruder** tab and make sure you have one extruder in your **Extruder List** for each extruder/material.  Make sure you set a unique tool index for each extruder.  If you checked the **First Extruder is 0** option above, make sure your first extruder is at index 0, or 1 if **First Extruder is 0** is unchecked.
 
Now, reslice your model using the new process settings and try again!
