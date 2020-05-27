The smart trigger has only one option:  Layer/Height.

Real time triggers also allow 'Gcode' and 'Timer' triggers.
#### Layer/Height
This trigger will take a snapshot on every layer change, or at most once for the provided trigger height.
#### Gcode
Take a snapshot every time a snapshot command is encountered.  The following two commands will work by default:
* ```@OCTOLAPSE TAKE-SNAPSHOT``` - This is a newly added snapshot command.  It will never be sent to your printer by Octoprint, even if Octolapse is disabled.  However, if you are printing from SD (Octolapse will not work when printing from SD), depending on your firmware, you may encounter errors.
* ```snap``` - This is a legacy command, and was added for compatibility reasons.  It will still work, but it may be removed in a future version.

You can also use any custom command you desire by setting the **Alternative Snapshot Command** within your Octolapse printer profile.  By default, this command is set to **G4 P1**, which is a popular custom command.

Note:  The snapshot command will not be sent to your printer, so make sure that whatever command you use is not one that is required for either your printer or Octolapse to work.  For example, do NOT use ```M114```, ```M400```, ```G90```, etc.

#### Timer (Real Time Only)
Take a snapshot on a timed interval.
