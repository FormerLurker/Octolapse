This error indicates that you are using the **Smart Gcode** trigger, but no snapshot commands were found within your gcode file.

To fix this command, open your Octolapse printer profile and look at the **Snapshot Command** setting.  Then open your gcode file and make sure that this command exists within the file.  Usually the snapshot command is added within layer change scripts inside of your slicer.
