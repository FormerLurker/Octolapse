There are currently five options for controling the X axis during a stabilization:
* Disabled - The snapshot will be taken wherever the axis happens to be when the snapshot is triggered.  Note that disabled has an interesting effect when using the smart layer trigger in conjunction with the 'snap to print' option within the trigger settings.
* Fixed Coordinate - The snapshot will be taken exactly at the absolute coordinate provided.
* List of Fixed Coordinates - The snapshot will be taken at each position provided in order.  See Stabilization Paths for details.
* Relative Coordinate - The snapshot will be taken at at a position relative to bed size.  These coordinates depend on the print volume.  See Printer Profile Settings for more details.
* List of Relative Coordinates - The snapshot will be taken at each relative coordinate in order.  Each coordinate is separated by a comma.  See Stabilization Paths for details.
