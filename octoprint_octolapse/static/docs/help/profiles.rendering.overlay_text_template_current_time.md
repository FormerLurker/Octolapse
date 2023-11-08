The {current_time} token supports an optional date format string.  It will format the current time according to a string supplied with the token.

Here are some examples if we assume the current date is January 1, 2021 at 12:00 noon:

{current_time:"%m/%d/%Y, %H:%M:%S"} = 01/01/2021, 12:00:00
{current_time:""%H:%M:%S"} = 12:00:00
{current_time:""%I:%M %p"} = 12:00 PM
{current_time:"%B %e, %Y"} = January 1, 2021
{current_time:"%c"} = Fri Jan 1 12:00:00 2021

Note:  The exact output format will depend on your local.

The date formatting is done with the [strftime](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior) function.  You can find a list of the supported format codes [here](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes).


