The smart trigger has only one option:  Layer/Height.

Real time triggers also allow 'Gcode' and 'Timer' triggers.

* Layer/Height - take a snapshot on every layer change, or at most once for the provided trigger height.
* Timer (Real Time Only) - Take a snapshot on a timed interval.  Don't set this value too low!
* Gcode (Real Time Only) - Take a snapshot every time command ```@OCTOLAPSE TAKE-SNAPSHOT``` is encountered within your gcode file.  You can also use any custom command you desire by setting the **Alternative Snapshot Command** within your Octolapse printer profile.
