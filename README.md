padpyght
========
An open source gamepad visualizer inspired by PadLight.

Usage
-----
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

NOTE
----
There are a few tutorials I've seen on the internet for how to use padpyght (thanks so much, by the way, if you've made one of these!), written/recorded before a major rewrite of this project occurred in August 2015.  If you're following one of these and you get lost, the pre-rewrite version may help you temporarily: https://github.com/lifning/padpyght/tree/legacy - but note that you'll be missing some of the newer features, such as interactive control mapping.

TODO
----
- Add trigger-clicks (i.e. Gamecube shoulders) and re-add stick-clicks
- Expose skin.ini-to-json converter in UI somehow
- Installer for Windows users unfamiliar with Python
