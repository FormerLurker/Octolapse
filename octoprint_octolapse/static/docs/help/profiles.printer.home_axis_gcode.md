Occationally, Octolapse needs to home your XY axis to a known location.  For example, there is an option to preview the snapshot position so that you can focus your camera in the custom image preferences screen.  In order to move to the proper place, your XY axes need to be homed, and put into absolute XY axis mode.

The default script is as follows:
```
G90; Switch to Absolute XYZ
G28 X Y; Home XY Axis
```
and is generally safe for most situations.
