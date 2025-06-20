An invalid rendering filename template has been detected in your current rendering profile.  To fix this open up your current rendering settings by navigating to the Octolapse tab, expanding the **Current Run Configuration** section, and clicking the edit pen to the right of the rendering profile drop down box.  Make sure the **Customize Profile** checkbox is checked.  Next, scroll to the **Files and Performance** section and find the **Filename Template** setting.  There should be an error indicator next to this box.  Enter this value in that box to fix the error:

```
{FAILEDFLAG}{FAILEDSEPARATOR}{GCODEFILENAME}_{PRINTENDTIME}
```
