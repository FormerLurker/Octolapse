This gcode script will be executed before any other *After Snapshot* bash/batch scripts.  Octolapse will wait for each script to complete for a given camera before continuing.  The order of each script's execution relative to other cameras, however, is unpredictable.

Scripts can be multi-line, can contain comments, and will be sent in order.
