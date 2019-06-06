Some printers prime at some height above the print bed.  This confuses Octolapse's layer trigger into believing that layer 1 is at this priming height.  The priming height must be set HIGHER than your layer height but AT OR BELOW the height at which your printer primes.  The default profiles use 0.75mm as a default since this is usually well above the maximum layer height, and well below the height at which your printer primes.

Note that some printers prime directly on the bed (Prusa MK2/MK3 as an example), usually at a slightly higher level than your first layer height.  This can cause a snapshot to be taken BEFORE the prime when using a layer/height trigger.  If this is a problem, you can set the priming height to match the priming layer height exactly providing that the priming is taking place ABOVE your first layer height.  Generally this doesn't cause a problem, though.

Note that some printers prime outside of the normal printing area (like the Mk2/Mk3).  If your printer is like this, look into the 'Restrict Snapshot Area' setting within the printer profile to prevent Octolapse from taking snapshots while priming.

