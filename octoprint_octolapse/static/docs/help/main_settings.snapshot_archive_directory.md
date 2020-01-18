This folder will be used to store an archived copy of all timelapse images if archiving is enabled within the rendering profile.  The archive will be created either after rendering is completed, or after the timelapse is completed if rendering is not enabled.  You can download any archived timelapses within the Octolapse tab.  Click the test button to verify that Octolapse has the appropriate permissions to access, and if necessary create this directory.

### Default Value
If the folder is left empty, Octolapse will use the plugin data directory.  In windows, this directory is typically:

```
{UserDirectory}/AppData/OctoPrint/data/octolapse/snapshot_archive
```
where ```{UserDirectory}``` is the user folder under which OctoPrint was installed.  In my system this is located within ```C:\users\USERNAME```.

If you are using OctoPi, the directory is typically:

```
/home/pi/.octoprint/data/octolapse/snapshot_archive
```

If you know where this folder is under macOS, pleeas let me know.

### Absolute Path
The provided folder must be an absolute path.  In windows this looks like the following:

```
c:\some\path\here
```

In Unix, Linux, and macOS, an absolute path looks like this:
```
/this/is/an/absolute/path
```

**Important Note**: Keeping snapshot images requires a LOT of space.  If you run out of disk space during a print, your print may fail.  Always make sure you have enough free space before starting a timelapse!

### Folder Premissions
Octolapse requires the ability to create and delete files and directories within any selected folders.  You can test permissions by clicking the **Test** button to the right of the directory.
