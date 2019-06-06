When enabled Octolapse will assume that your firmware is set to use the same zlift value for retraction/deretraction settings as your Octolapse profile. It is always a good idea to include an M207 and or M208 in your start gcode if you are using firmware retract/deretract so that Octolapse knows what values to use when tracking position.

If this setting ONLY if you are using firmware zlift! If your gcode is performing zlift manually (g0/g1) using absolute coordinates, your nozzle may crash into your part. When in doubt, leave this unchecked!. 
