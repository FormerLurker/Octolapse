When using the 'Fast' smart trigger type, this option will prevent any snapshots from occurring during extrusion unless the extrusion speed is ABOVE (not equal to) the provided speed.  If used correctly, this can prevent Octolapse from taking snapshots while over exterior perimeters, and decreases travel distances over the 'compatibility', 'normal quality', 'high quality' and 'best quality' smart layer trigger types.

If the speed threshold is not correctly set, your print quality could suffer dramatically.  The speed needs to be FASTER than any important print features (faster than outer perimeter speed, bridges, or any other important parts), but SLOWER than the non-quality related parts (infill, sometimes interior perimeters depending on your printer setup).  Skip this option unless you know what you're doing.

Set to 0 to disable the speed threshold.
