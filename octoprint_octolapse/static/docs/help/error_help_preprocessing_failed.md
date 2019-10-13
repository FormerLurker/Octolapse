Preprocessing failed.  This is usually due to incorrect printer profile settings, but can be caused by other issues.

### Steps to Solve

#### Try using a pre-configured printer profile
If you upgraded Octolapse from v0.3.4, or if you created your own custom printer profile you might have some incorrect printer profile settings.  Open your printer profile and see if you can find your printer in the **Make and Model** dropdown boxes.  These profiles have been pre-configured, and should work properly in most cases.  Note that some of these profiles are still in beta, so use caution.

#### Change your default axis modes
Octolapse needs to know your printer's default axis modes.  Older versions of Octolapse required explicit gcodes to set these axis modes (G90/G91 or M82/M83), and if these codes are missing from your gcode files, octolapse may not work.  As a workaround, you can default these axis modes to absolute, as is done in all of the current pre-configured octolapse profiles.  

Open your printer profile and set your **X/Y/Z Axis mode** to **Default To Absolute**.  Then change the **E Axis Mode** to **Default To Absolute**.

#### Increase your priming height
In order to properly detect the first layer, Octolapse has a setting in the printer profile called **Priming Height** within the **Layer Change Detection** settings.  If the **Priming Height** is set to a value lower than your layer height, Octolapse may not take any snapshots.

Try increasing this value to 1.0 and see if any snapshots are taken.

#### Double check your print volume
Make sure your printer volume is correct by opening your Octolapse printer profile, and looking for the **Build Volume and Origin** section.  Check the box next to **Override Octoprint Printer Profile**, select the shape of your bed, and enter in the appropriate area and origin type.

Note:  Most delta printers have a circular bed with a center origin.  Most (but not all) cartesian printers will have a rectangular bed with a front left origin.  Some printers will also require a custom bounded box in order for Octolapse to be able to take snapshots in all possible positions.

#### Remove any position restrictions
Octolapse supports preventing snapshots within certain areas/regions of the print.  If Octolapse is not taking any snapshots, it's possible that this is the reason.

To clear out any snapshot area restrictions for your printer, open your printer profile and disable **Restrict Snapshot Area** by unchecking **Enabled**.  It may already be disabled.

To clear out any trigger position restrictions, open your current trigger profile.  Position restrictions are only currently available when using the 'Real-Time Triggers' **Trigger Type**.  Look for **Position Restriction** and uncheck the box next to **Enable Position Restrictions** to remove all position restrictions.

#### If all else fails
If you have tried everything, and nothing seems to work, maybe you've found a bug?  Consider
<a href="https://github.com/FormerLurker/Octolapse/wiki/Report-a-Bug" title="Report a bug" target="_blank">creating an issue</a> in the Octolapse github repository.
