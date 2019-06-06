When enabled, use relative axis mode for lift/retraction and absolute mode for travel. This is the safest and most tested way for Octolapse to generate the gcode necessary to take a snapshot.

When disabled, Octolapse will send fewer commands to the printer, and will be more compatible with plugins that do not account for relative x/y/z movements (like many layer change detection plugins).

Attention This is an experimental setting, and should remain ENABLED unless you are 100% sure about what you are doing. If you uncheck this setting, and there are errors in the new routine, bad things could happen, like your nozzle crashing into the printed part or (worse yet) your bed. 
