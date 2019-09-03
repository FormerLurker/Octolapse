This setting can be used to remove frames from the beginning of the timelapse.  This can be useful in many situations.  For example, if Octolapse is taking a single snapshot while priming, and you won't want that frame to be in the final timelapse, you can remove it by setting this value to 1.

Set to 0 to disable.


Note that Octolapse will still take a snapshot for any removed frames, but they will not be rendered into the final timelapse.  If you want to prevent snapshots entirely from the beginning of the print, consider using the _Restrict Snapshot Area_ feature within the printer profile.  

Note, the first available frame that is NOT removed will be used for the pre-roll frame, if you are adding pre-roll.
