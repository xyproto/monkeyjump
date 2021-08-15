#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#vim: set enc=utf8:
#
# author:   Alexander Rødseth <rodseth@gmail.com>
#
# changes:
#   Wed Apr 20 22:08:08 UTC 2005
#   Tue Sep 27 15:10:06 CEST 2005
#   Mon Oct 10 13:04:56 CEST 2005
#   July 2013
#   August 2013
#

import pygame
from pygame.locals import *
from burnlib.scriptlib import KeyParser
import sys
import os.path

CONFDIR = "conf"
THEMEDIR = "themes"

# The default size of the board (give a number as the first argument to change)
BOARDSIZE = 9

# This looks good
RESOLUTION = (512, 512)

# This looks okay, but the cursor is a few pixels off
# RESOLUTION = (640, 480) 

# This looks bad ATM, since the lines on the board are misaligned
# RESOLUTION = (1024, 768)

# If you run it in a window, you have room for the GnuGo GTP-text as well :-)
FULLSCREEN = False

try:
    import psyco
    psyco.full()
except ImportError:
    pass

def main():
    global CONFDIR
    global THEMEDIR
    global BOARDSIZE
    
    # is the argument the boardsize or a filename?
    arg = " ".join(sys.argv[1:])
    filename = ""
    try:
        BOARDSIZE = int(arg)
    except ValueError:
        filename = arg

    if filename:
        # finding size based on the filename
        # (could include other sizes in the future)
        file = open(filename)
        data = file.read()
        if "SZ[9]" in data:
            BOARDSIZE = 9
        elif "SZ[13]" in data:
            BOARDSIZE = 13
        elif "SZ[19]" in data:
            BOARDSIZE = 19
        file.close()

    kp = KeyParser(os.path.join(CONFDIR, "keybindings.conf"), RESOLUTION, FULLSCREEN, BOARDSIZE, THEMEDIR, CONFDIR)

    windowtitle = 'Monkeyjump'

    # is the argument a filename?
    if filename:
        print("Loading %s..."%filename)
        # load the sgf
        kp.parser.fc("loadsgf", filename)
        print("ok")
        # change the window title
        windowtitle += ' - ' + filename

    # set the window title
    pygame.display.set_caption(windowtitle)

    # limit the type of events allowed
    pygame.event.set_allowed(KEYUP)

    while True:
        pygame.event.pump()
        event = pygame.event.wait()
        if event.type == QUIT:
            break
        elif event.type == KEYUP:
            kp(event.key)
        elif event.type == MOUSEMOTION:
            kp.parser.fc("mousepos", *pygame.mouse.get_pos())
        mousepressed = pygame.mouse.get_pressed()
        # Update the mouse-position if a button is pressed
        if 1 in mousepressed:
            kp.parser.fc("mousepos", *pygame.mouse.get_pos())
        kp(mousepressed)
        kp.refresh()

    pygame.quit()

if __name__ == "__main__":
    main()
