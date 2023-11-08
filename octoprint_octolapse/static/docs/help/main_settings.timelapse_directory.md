This folder is where completed timelapses will be moved after they are rendered.  It will also control which timelapse videos are visible within the **Timelapse** tab of the **Videos and Files** dialog.  Click the test button to verify that Octolapse has the appropriate permissions to access, and if necessary create this directory.

### Default Value
If the folder is left empty, Octolapse will use the default Octoprint timelapse folder.  Also, if left empty your timelapse files will be available within the default timelapse tab in addition to the Octolapse tab.


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
