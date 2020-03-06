At least one camera profile has a *Before Print Start Script*.  There were errors running at least one of these scripts.

### How to Debug

One foolproof way to solve this issue is to remove the *Before Print Start Script*.  This won't solve your scripting problem really, but it will allow you to print without disabling the camera, or Octolapse.

I cannot advise you on how to exactly solve all scripting issues since you are most likely using a custom script of some kind.  However, google will probably be your friend while you try to debug your custom script.  I recommend getting your script to work from the command prompt before trying to debug within Octolapse.  If it works from the console, but not within Octolapse, I recommend the following debugging steps:

1. Change your *Logging* profile to *Log Everything*.
2. Edit the *Log Everything* logging profile and click *Clear Log*, which will make the debugging process easier by removing extra log entries.
3. Edit your camera profile and click the test button next to the *Before Print Start Script*.  You may see an error popup after clicking test.
4. Edit the *Log Everything* logging profile and click *Download Log*.  Review the log to see detailed error messages and console output for your script.
