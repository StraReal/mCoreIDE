I made this to program my Makeblock mbot while avoiding using the mblock IDE (terrible), and since the board used by the mbot is not a standard Arduino ONE, but a custom version of it, called mCore, the Arduino IDE has trouble uploading to it.
So, I made this simple repo to work around that.

Create a vars.json and just put one single "user" entry, which should be your PC user folder (or the one with the makeblock library installation. You need to install that first.)

Make a sketch.ino file with the Arduino code (examples in the examples folder), run uploadsketch.py and the Arduino code will be loaded (I made this lazily so it only works on COM3, probably an easy fix but idk).

The code should be uploaded onto the board, and by running serialconsole.py you can send and receive signals over any baud (default is 57600).

There are many things that are needed and can be added, so if you take this as basis and fix them send a PR, I'll accept it.