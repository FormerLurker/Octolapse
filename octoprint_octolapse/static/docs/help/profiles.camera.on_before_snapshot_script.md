This script will be called after the printer has stabilized, but before any snapshots are taken.  It might be useful to turn on lighting, to send a notification, or other things I haven't even thought of.

The *Test* button will run this script with the **Snapshot Timeout**, but during a live print there is no timeout.  This is to prevent scripts from running for an unusual amount of time when testing.

The following parameters, in order, are currently supplied to this script:

* Snapshot Number - an integer value that increments after each successful snapshot
* Delay Seconds - the camera delay in seconds
* Data Directory - the path to the Octolapse data folder
* Snapshot Directory - The path to the current camera's snapshot folder for the current print job.
* Snapshot File Name - The expected file name of the snapshot after it has been taken
* Snapshot Full Path - the full path and filename of the expected snapshot.

Note that the directories above may not exist, and there will be no file at the 'Snapshot Full Path' when this script is executed.
