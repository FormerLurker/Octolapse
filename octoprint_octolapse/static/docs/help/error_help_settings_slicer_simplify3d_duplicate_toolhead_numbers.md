Your gcode file, created from Simplify3D, contains multiple extruders referencing the same toolhead index.  Though this is allowable in Simplify3D, this is not supported in Octolapse.  You have two options:

1.  Make sure each extruder configured in your current Simplify3D process is using a unique *Extruder Toolhead Index*.
2.  Disable Octolapse.
