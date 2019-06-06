This script is executed after ALL cameras have completed (or failed) taking a snapshot.  The parameters are the same as for the Before Snapshot Script

* Snapshot Number - an integer value that increments after each successful snapshot
* Delay Seconds - the camera delay in seconds
* Data Directory - the path to the Octolapse data folder
* Snapshot Directory - The path to the current camera's snapshot folder for the current print job.  This directory may not  exist, so be sure to create it before using the path!
* Snapshot File Name - The expected file name of the snapshot after it has been taken.
* Snapshot Full Path - the full path and filename of the expected snapshot.

Note that the directories above may not exist, and there may be no file at the 'Snapshot Full Path' when this script is executed.
