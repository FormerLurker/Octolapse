This error indicates that you are using the **Smart Gcode** trigger, but no snapshot commands were found within your gcode file.

To fix this command, open your Octolapse printer profile and look at the **Snapshot Command** setting.  Then open your gcode file and make sure that this command exists within the file.  Usually the snapshot command is added within layer change scripts inside of your slicer.

**A note about case and comments**

Snapshot commands are NOT case sensitive in Octolapse V0.4+, so upper case and lower case should both work in either the snapshot command or in your gcode file.  Please note that all comments are stripped from the alternative snapshot command while Octolapse is running.  For example, if you use

```G4 p1 ; THIS IS A SNAPSHOT```

as your snapshot command, Octolapse will strip the comment and will trigger on any occurrence of

```G4 P1```

Since comments are ignored in OctoPrint, Octolapse would also trigger if the following line appears within your gcode file:

```SNAP ; NOTICE HOW THIS IS A DIFFERENT COMMENT!```

In other words, comments are ignored both within the alternative snapshot command, and within the gcode file.
