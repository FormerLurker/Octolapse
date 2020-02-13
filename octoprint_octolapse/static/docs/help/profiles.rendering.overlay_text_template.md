Determines the overlay text. Leave blank to disable the overlay text. You can use the following replacement tokens: {snapshot_number}, {current_time}, {time_elapsed}, {layer}, {height}, {x}, {y}, {z}, {e}, {f}, {x_snapshot}, {y_snapshot}

### Notes on token values

x, y, z, e, and f all show the position of the extruder right before it is stabilized.  x_snapshot and y_snapshot show the position after the stabilization is completed.

x, y, z, e, x_snapshot, and y_snapshot are all in absolute coordinates.  All floating point values will display with three decimals except for e and e_snapshot, which will show 5.  Feedrates (f) will be shown as integers.

If you'd like to see a replacement token that is not listed, please create an issue on the [octolapse repository](https://github.com/FormerLurker/Octolapse/issues) to suggest more options.
