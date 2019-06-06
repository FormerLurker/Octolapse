This brand new (Alpha) feature is very interesting.  Without this option, Octolapse only looks at the coordinates AFTER GCode is executed to determine if the point is within the position restriction.  When this option is enabled, Octolapse will look at the path of travel from the current position to the final position after executing the current GCode command.  Octolapse will calculate all intersections with any position restrictions, and will determine if any of these points are pass your position restriction tests.  If so, Octolapse will break up the current GCode commands into 2, and will take a snapshot starting from the intersection point.  

Octolapse searches the first in-position intersection point at the moment, since it seems efficient and simple.

Here is an example using absolute X and Y, and relative E coordinates:
Previous GCode Command:  G1 X0.000 Y10.000
Current X,Y position: 0,10
Current Position Restriction:  'Must Be Inside' Rectangle from (5,5) to (15,15) with 'Calculate Intersections' enabled.
Current GCode command (not yet sent to printer):  G1 X25.000 Y10.000 E1.00000
Two intersection points are available:  5,10 and 20,10
Since both 5,10 and 20,10 are in position (not overlapping any forbidden areas), Octolapse will break the current GCode command into 2.  Assuming Octolapse finds the position 5,10 first the following two GCode commands will be created:

G1 X5.000 Y10.000 E0.40000
G1 X25.000 Y10.000 E0.60000

Octolapse will execute the first command before any snapshot commands are sent, and will send the second command after all of the snapshot GCodes are executed, including changes to absolute/relative mode, speed, etc.

This option is GREAT if you want to take snapshots only around a very small area of you print, say one with only infill under a solid surface.  It does use a lot of processing power, so it might be best to limit this option to better hardware.  If you run into problems with stuttering, either upgrade your hardware, reduce the complexity of your GCode (turning detail too high can cause problems on any print done over a serial connection!), or turning this option off.  See performance considerations for more details (If I've created that page yet).
