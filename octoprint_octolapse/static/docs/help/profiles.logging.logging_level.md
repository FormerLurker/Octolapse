Octolapse has six logging levels, listed below in order from more to less logging:

* **Verbose** - Logs absolutely everything.  Can result in VERY large log files for some modules, but provides the most information.
* **Debug** - A good level to use if you are trying to debug any problems.  In general, it will provide a reasonable amount of data to debug a problem without overwhelming the logfile.
* **Info** - Provides some general information about what is going on in Octolapse, but not enough to create large logs through normal usage.
* **Warning** - Shows potential problems that are not usually reported to the UI.
* **Error** - Only logs errors and exceptions.  Most errors/exceptions indicate a problem, so this is a good level to use for general printing.  Note that the debug profile contains a shortcut for logging all modules at the **Error** level.  See the **Log All Errors** setting for more info.
* **Critical** - A critical error generally will affect system stability.  These can be out-of-memory or diskspace errors that have the potential to crash the system.  Not all critical errors can be logged, and may be logged by OctoPrint itself.

Note that when a given log level is selected, you will not only receive logs from that level, but from all levels below.  For example, if you use **Debug** logging, you will also be logging Info, Warning, Error AND Critical log messages.  Similarly, if you log at the **Error** level, you will also get Critical log messages.
