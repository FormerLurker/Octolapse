This script will be executed after the printer position as stabilized and after any camera delay that you have configured.  Normally a delay is not needed for a DSLR, but might be necessary in some situations.

The following parameters, in order, are sent to the script.
```
Snapshot Number - an integer value that increments after each successful snapshot
Delay Seconds - the camera delay in seconds
Data Directory - the path to the Octolapse data folder
Snapshot Directory - The path to the current camera's snapshot folder for the current print job.  This directory may not exist, so be sure to create it before using the path!
Snapshot File Name - The expected file name of the snapshot after it has been taken
Snapshot Full Path - the full path and filename of the expected snapshot.  If this file exists after the script has returned, Octolapse will treat it like any other snapshot, and will apply transposition, record metadata (for rendering overlays), and will generate a thumbnail that will be sent to the client.
```

[See this beta guide](https://github.com/FormerLurker/Octolapse/wiki/V0.4---Configuring-an-External-Camera) for setting up a DSLR camera on Linux using [gPhoto2](http://gphoto.org/).  I have also gotten this to work on Windows using [digiCamControl](http://digicamcontrol.com/), but have not finished up the guide for that part yet.
