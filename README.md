padpyght
========
An open source gamepad visualizer inspired by PadLight.

Usage
-----
Download and unzip the release package, and run `padpyght.exe`.

It will present you with a list of connected gamepads and available padpyght skins.
Select one of each, then click the "run" button.
If it's your first time running with that combination of gamepad and skin, the program will ask you to map the controls.
*Pay attention to the title of the window during this!*
The window title will tell you what to do, while the visualization animates each action.
If you make a mistake, you can revisit this mapper from the initial selection screen by clicking "remap" instead of "run."

Once in visualization mode, NumPad + and - will resize the window by 10% at a time.

Run from source
---------------
Command line: `python2 -m padpyght [skin name] [joypad number]`

If you have [PGU](http://code.google.com/p/pgu/) installed, you can omit both
arguments (simply `python2 -m padpyght`) for a GUI which will let you choose the
joystick and skin to use from lists.

If you haven't yet interactively mapped the given skin's inputs to the given
joypad's physical buttons, you will be asked to do so before the visualizer
starts (if the graphical representation isn't clear enough, please watch the
window's title or command prompt for what it's expecting you to do), after which
it will immediately begin visualization as normal.

Use + and - on the number pad to change the window size during visualization.

Build packages
--------------
To build release packages, simply type `make` and find the resulting `padpyght-win32.zip` and `padpyght-linux.tar.gz` in the `dist/` directory.
It requires that PyInstaller, Python, PyGame, and PGU be installed, and that you have all of these things installed in Wine as well.
If you don't want to use Wine (if you don't care about making Windows binaries, or perhaps if you're using MSYS or similar from Windows and have no need to run Wine), just run `make linux` instead of the default target.

NOTE
----
There are a few tutorials I've seen on the internet for how to use padpyght (thanks so much, by the way, if you've made one of these!), written/recorded before a major rewrite of this project occurred in August 2015.  If you're following one of these and you get lost, the pre-rewrite version may help you temporarily: https://github.com/lifning/padpyght/tree/legacy - but note that you'll be missing some of the newer features, such as interactive control mapping.

TODO
----
- Add trigger-clicks (i.e. Gamecube shoulders) and re-add stick-clicks
- Expose skin.ini-to-json converter in UI somehow
- Find someone with a Mac
