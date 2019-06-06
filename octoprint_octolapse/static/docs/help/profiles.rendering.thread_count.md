Determines how many threads are used to render the resulting video.  In general, the higher this number is the faster rendering will go.  However, if you exceed the number of cores on your CPU this can actually hurt performance.

I recommend that you not use a value higher than NUMBER-OF-CORES - 1.  For example, if you have a 4 core computer, setting this number to 3 is relatively safe.  If you set it to 4 you might have problems running Octoprint while rendering (though printing while rendering is not recommended).
