Determines the overlay text. Leave blank to disable the overlay text. You can use the following replacement tokens: {snapshot_number}, {current_time}, {time_elapsed}, {layer}, {height}, {x}, {y}, {z}, {e}, {f}, {x_snapshot}, {y_snapshot}, {gcode_file}, {gcode_file_name}, {gcode_file_extension}, {print_end_state}, {current_time:"FORMAT_STRING"}, {elapsed_time:"FORMAT_STRING"}

### Notes on token values

x, y, z, e, and f all show the position of the extruder right before it is stabilized.  x_snapshot and y_snapshot show the position after the stabilization is completed.

x, y, z, e, x_snapshot, and y_snapshot are all in absolute coordinates.  All floating point values will display with three decimals except for e and e_snapshot, which will show 5.  Feedrates (f) will be shown as integers.

The gcode_file token will return the full file name, including the extension.  The gcode_file_name token will return the name without the .gcode extension, and the gcode_file_extension token will return only the extension (typically .gcode).

The print_end_state token will return one of the following states:  COMPLETED, CANCELED, DISCONNECTED, DISCONNECTING, FAILED

For details about the {current_time:"FORMAT_STRING"} and {elapsed_time:"FORMAT_STRING"} tokens, please click on the help icons (blue question mark) next to those tokens in the rendering profile page.

If you'd like to see a replacement token that is not listed, please create an issue on the [octolapse repository](https://github.com/FormerLurker/Octolapse/issues) to suggest more options.


