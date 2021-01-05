The {time_elapsed} token supports an optional format string.  When no format string is provided, it will output in the following way:

* elapsed time >= 1 day - X days, H:MM:SS (5 days, 4:15:05)
* elapsed time < 1 day - H:MM:SS (4:15:05)

If you supply a format string, it will be in the following general format:

{time_elapsed:"FORMAT_STRING_GOES_HERE"}

Make sure you included the quotation marks after the semicolon!  Do not embed any quotes inside of the format string, else it won't work properly.

The format strings are custom since no good built in system exists for this.  Here are all the supported tokens (they are case sensitive!):

* %D = total days
* %d = day component
* %H = Total Hours
* %h = Hours Component
* %M = Total Minutes
* %m = Minutes Component
* %S = Total Seconds
* %s = Seconds Component
* %F = Total Milliseconds
* %f = Milliseconds Component

Here are some examples if we assume the elapsed time is 5 days, 5 hours, 5 minutes and 5.123 seconds:

{time_elapsed:"%d Days %h Hours, %m Minutes, %s Seconds, %f MS"} = 5 Days, 5 Hours, 5 Minutes, 5 Seconds, 123 MS
{time_elapsed:"%D:0.3 Total Days"} = 5.212 Total Days
{time_elapsed:"%M Minutes"} = 7505 Minutes

You can also specify the number of decimals to display, and/or pad the string with leading zeros. This formatting style is taken from python's format function, and behaves pretty much the same.  here is the format

%{token_name}:{minimum_non_decimal_digits}.{number_of_decimal_places}

If *minimum_non_decimal_digits* is less than the actual number of digits, the number will be padded with 0s.  If there are more non-decimal digits than are specified, all are shown.

If you set number_of_decimal_places=0, the decimal will be truncated and shown as 0.  For example, 1.1 will become 1.0.  This is odd, but it's the way it is.

See the following examples assuming total minutes = 55.5555:

* {time_elapsed:"%M:0.1"} - shows the total minutes with 1 decimal place : 55.6
* {time_elapsed:"%M:0.0"} - shows the total minutes with 1 decimal place, but the decimal will always be 0 unfortunately (.0 is the same as .1 unfortunately): 55.6
* {time_elapsed:"%M:1.1"} - the same as M:0.0, : 55.6
* {time_elapsed:"%M:0.2"} - 2 decimal places : 55.56
* {time_elapsed:"%M:4.1"} - 4 non-decimal digits, 2 decimal places : 0055.56

You can mix and match tokens and add your own text:

* {time_elapsed:"%d days, %h:2:%m:2:%s:2 (%S Total Seconds)"} - 5 days, 05:05:05 (450305 Total Seconds)
* {time_elapsed:"%s:0.2 seconds"} - shows the total seconds with 2 decimal points - 450305.12 seconds
