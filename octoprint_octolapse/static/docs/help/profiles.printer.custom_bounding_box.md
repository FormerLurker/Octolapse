Some printer have different coordinates than their build width/length/height would imply.  It is important that Octolapse understand your exact build volume coordinate system in order to properly move your extruder during stabilization, and to prevent Z-Lifting above the printable area.

For example, the Prusa MK2 has a build volume of 250x210x200, but the Y axis includes a 3mm space reserved for priming.  The actual Y axis is 213 MM wide, where Y is between -3 and 210.  For this reason a custom bounding box is necessary for these printers.
