Select the font that will be used to generate an overlay in your timelapse.  One font is pre-packaged and included with Octolapse.

## Fonts in Windows
If you are using windows, your system fonts should also be included.  Not all fonts are compatible with Pillow (used to create the overlay), so if your preview fails you might want to select a different font. 

## Fonts in Linux
IMPORTANT NOTE:  If you are using OctoPi, or any flavor of Linux, you need Fontconfig installed so that Octolapse can find fonts other than the single font packaged with Octolapse.

To install fontconfig:

1. connect to a terminal screen and sign in.
2. run the following command to update any existing applications:
```
sudo apt-get update
```
3. install fontconfig with the following command:
```
sudo apt-get install fontconfig
```
4. reboot your system for the changes to take effect.

## Fonts in Mac OS
I do not know how to retrieve the system fonts in Mac OS and have no way to test it currently.  However, I think the pre-packaged font should still work.  If you run into problems generating a text overlay with OctoPrint running on a Mac (not just your browser, but where OctoPrint is installed), please let me know.  Also, if you have python code to find all/some of the system fonts, please let me know!
