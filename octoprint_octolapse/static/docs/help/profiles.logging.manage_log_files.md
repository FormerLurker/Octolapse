#### Log Files in Octolapse

Octolapse stores one current logfile, named plugin_octolapse.log.  Once a day the current log file gets backed up with a date extension (for example, plugin_octolapse.log.2020-01-01).  Octolapse keeps up to three logfile backups, and will delete any older backup logs.

#### Clear Log

This button allows you to clear the current log file, which is very useful if you are trying to create log data for a specific issue, but your log file is already huge.  This button does not actually erase the current log, but rather rolls the current log data into another backup log file, erasing any data in the current backup if one exists.

#### Clear All Logs
This button will clear the current logfile, just like the **Clear Log** button, but will then delete any backup logs.  This is useful for freeing up space if your logfiles are huge.

#### Download Log
This button will download the most recent logfile (plugin_octolapse.log).  If you want an older logfile (remember, Octolapse stores up to three backup log files), navigate to Octoprint Settings (wrench/spanner icon)->Logs and look for plugin_octolapse.log.DATE_GOES_HERE).
