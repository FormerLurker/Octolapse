This error means that Octolapse can't determine what units your gcode is using.  There are two ways to fix this error:

1.  Open your Octolapse printer profile settings.  Scroll down to the **Firmware Settings** section and change the **Default Units** option to **Millimeters**.
2.  Open your slicer and add the following gcode to the very top of your start gcode:  G21
