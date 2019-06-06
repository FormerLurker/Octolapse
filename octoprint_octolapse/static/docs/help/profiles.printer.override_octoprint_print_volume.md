Octolapse can either use the current printer profile volume configured within OctoPrint, or you can customize the volume here.  This does not affect the function of OctoPrint, only the Octolapse plugin.

It is very important to have the correct print volume.  Octolapse bases most of it's movements on the size of your printer's volume.  If the volume is incorrect, Octolapse may take snapshots in the wrong place, run into endstops, or z-hop into the top of the z-axis.

When entering a print volume, keep in mind that some printers use auto-leveling, which can slightly change the reported bed coordinates.  If you have problems with out-of-bounds positions, either expand the volume, or move your snapshot position away from the edge of the bed.
