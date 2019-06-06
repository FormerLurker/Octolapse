

There are several smart layer types that are available:

#### Fastest 
Gets the closest position.  This WILL leave very noticable defects on your print when using this mode.  However, it can be VERY useful if you are printing an ooze shield, or want to stabilize on top of a wipe tower.  The key is to adjust the stabilization point so that Octolapse always triggers on an unimportant piece.
#### Fast
Gets the closest position, including the fastest extrusion movement on the current layer, optionally EXCLUDING extrusions with feedrates that are below or equal to a supplied speed threshold.  If only one extrusion speed is detected on a given layer, and no speed threshold is provided, returns the same position that the 'compatibility' type would return.  You can get good results with this option IF you select the proper speed threshold and adjust your slicer to ensure that no critical parts will be printed at any faster speed (say infill).
#### Compatibility
Attempts to return a high quality position if possible (see position rankings below).  If it cannot, it will return the next best position available (including extrusions) to ensure that a snapshot is taken on every layer.  Use this trigger if you're concerned with quality, but you want Octolapse to trigger on every layer no matter what.  This mode is also more likely to work with some lesser tested slicers and slicer settings.  This mode WILL take a snapshot while extruding if it has found no alternative.
#### Normal Quality
Attempts to return a high quality (see position rankings below).  Returns a lesser quality position if no good quality position is found.  Will not take a snapshot during extrusion.
#### High Quality
Gets a close High quality position (see position rankings below) and automatically balance time and quality   This mode requires an additional parameter called the 'Distance Threshold Percent', which means that it will choose a lower quality snapshot point ONLY if it gives you a speed improvement that is greater than or equal to the provided percentage.  For example, if Octolapse has found a high quality position that is 200mm away from the stabilization point, and your distance threshold is set to 10%, it would return the high quality position unless the closer one is 180mm away or nearer.  It repeats this process down the quality rankings (see below), but will NEVER take a snapshot while extruding.
#### Best Quality
Gets the best quality position available.  Skips snapshots if no quality position can be found.  If you have retraction disabled this mode will probably not take any snapshots at all!

**Important Note** The Normal, High and Best quality smart triggers will NOT work properly with vase mode.  You won't get many (any?) snapshots, and your quality will be severely impacted.  If you are printing a vase, consider using the 'snap to print' option, which is much faster, and has a lower impact on vases in general.


### Position Rankings by Quality

Here is how Octolapse ranks positions (from best to worst) when choosing a point to start taking a snapshot:

* lifted_retracted_travel - The best time to take a snapshot.  Your printer is fully lifted, fully retracted, and is traveling.
* lifting_retracted_travel - Your printer is fully retracted, and is traveling while lifting at the same time.
* retracted_travel - Your printer is rully retracted and traveling.
* retracted_lifted - Your printer is fully retracted and fully lifted.
* retracted_lifting - Your printer is fully retracted, and is lifting.
* retraction - Your printer has just completed a retraction.  This can be a good time to take a snapshot.  Most of the smart trigger types will return a position without looking for a closer one at this point.  Only the 'fastest', and sometimes the 'fast' option will keep searching for a closer position if a higher quality position was already found.
* lifted_travel - Your printer is lifted fully, and traveling.
* lifting_travel - Your printer is lifting and traveling at the same time (Cura does this I believe)
* travel - Your printer is traveling.
* lifted - Your printer is fully lifted (according to the z-hop distance setting in your slicer).
* lifting - Your printer is raising the Z axis.  Though not a great place to take a snapshot, it's better than while extruding.
* extrusion - Your printer is extruding.  This is usually the worst time to take a snapshot.
* unknown - Octolapse doesn't know, or doesn't care what type of position this is.  Snapshots are never taken from unknown positions

If you believe there are other scenarios that need to be handled, or that the order of any of the items above is incorrect, please let me know.  This is a work in progress, and I believe there will be lots of tweaks in the future.
