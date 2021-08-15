#!/usr/bin/python
#-*-coding:utf-8-*-
#vim: set enc=utf8:
#
# author:   Alexander Rødseth <rodseth@gmail.com>
# date:     July 2004
#

from pygame.locals import *
from burnlib.common import addpath

class Keybindings(dict):

    def __init__(self, filename="keybindings"):
        self.data = open(addpath(filename)).read()
        self.lines = self.data.split("\n")
        self.keynames = {}
        for line in self.lines:
            elements = line.split()
            if elements and (elements[0].find("#") != 0):
                keyname = elements[0]
                keycode = self.get_keycode(keyname)
                command = elements[1:]
                self[keycode] = command
                self.keynames[keycode] = keyname

    def get_keycode(self, keyname):
        if keyname == "lmouse":
            return (1, 0, 0)
        elif keyname == "mmouse":
            return (0, 1, 0)
        elif keyname == "rmouse":
            return (0, 0, 1)
        keycode = 0
        try:
            keycode = eval("K_" + keyname)
        except NameError:
            try:
                keycode = eval("K_" + keyname.upper())
            except NameError:
                print("Unable to find keycode for key:", keyname)
                return
        return keycode

    def get_keyname(self, keycode):
        return self.keynames[keycode]
