Add all snapshots to an archive after rendering.  On OctoPi these snapshots will be located in:
```
/home/pi/.octoprint/data/octolapse/snapshot_archive/
```
On windows it will be located in:
```
{user_folder}\AppData\Roaming\OctoPrint\data\octolapse\snapshot_archive\
```
Note that the user folder can change depending on the system.  On mine, it's ```c:\users\USER_NAME_HERE```.  Also, the ```AppData``` folder is often hidden, so make sure 'View Hidden Items' is enabled inside of your user folder.

I hope to add a file browser soon so that searching for the directory won't be a problem.

**WARNING** - This will take a lot of space.  Use caution, and be sure to purge your snapshots often.
