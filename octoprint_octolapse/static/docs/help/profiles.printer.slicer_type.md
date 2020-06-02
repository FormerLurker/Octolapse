### Slicer Type
Octolapse will be easier to configure if you select the slicer you are using.  You have the following options:

* Automatic Configuration - This is the recommended setting
* Cura V4.1 and Below
* Cura V4.2 and Above
* Slic3r Prusa Edition
* Simplify 3D
* Other Slicer (generic slicer)

#### Automatic Configuration
Octolapse will attempt to automatically extract your slicer settings.  Currently Cura, Slic3r PE, Prusa Slicer, and Simplify 3D are supported.  [See this guilde](https://github.com/FormerLurker/Octolapse/wiki/V0.4---Automatic-Slicer-Configuration) for information on how to enable automatic slicer configuration.

**Important Notes**:  Cura requires a script to be added to the start gcode for **Automatic Configuration** to work.  Additionally, automatic settings extraction will NOT work when using multi-material/extruder mode in Slic3r/Slic3rPE/PrusaSlicer.  Finally, Multi-Material/Multi-Extruder support is beta, and should be used with caution.

#### Other Slicer Types
For all other slicers, [See this link](https://github.com/FormerLurker/Octolapse/wiki/v0.4---Creating-And-Configuring-Your-Printer-Profile#slicer-settings) for info on configuring Octolapse with a generic slicer.
