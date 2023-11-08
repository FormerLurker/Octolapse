This folder will be used to store snapshots, including any failed or unfinished renderings.  It will also store temporary images used to render a final timelapse, and a temporary rendering until it is moved to the timelapse folder.  Click the test button to verify that Octolapse has the appropriate permissions to access, and if necessary create this directory.

**Important Note**: Due to the way Octolapse constructs timelapses, this folder may require a lot of storage.  If you run out of disk space during a print, your print may fail.  Always make sure you have enough free space before starting a timelapse!

### Default Value
If the folder is left empty, Octolapse will use the plugin data directory.  In windows, this directory is typically:

```
{UserDirectory}/AppData/OctoPrint/data/octolapse/tmp
```
where ```{UserDirectory}``` is the user folder under which OctoPrint was installed.  In my system this is located within ```C:\users\USERNAME```.

If you are using OctoPi, the directory is typically:

```
/home/pi/.octoprint/data/octolapse/tmp
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

### Folder Premissions
Octolapse requires the ability to create and delete files and directories within any selected folders.  You can test permissions by clicking the **Test** button to the right of the directory.
