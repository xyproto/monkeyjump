#!/usr/bin/python
#-*-coding:utf-8-*-
#vim: set enc=utf8:
#
# author:   Alexander Rødseth <rodseth@gmail.com>
#
# changes:  July 2004
#           April 2005
#           July 2013
#

import pygame
from pygame.locals import *
#import apf
#import bip
from burnlib.common import addpath
import os.path

"""
TODO:

* Create the undo version of all effects that can have an "opposite" operation
* Implement load and save (especially for SVG)
* Get large and tiny images to work
* Create a mode-indicator control (based on a label control?)
* Create a palette-control
* Create a label-control
* Create a textbox-control
* Create a singnal-system for the controls
* Create a super-control
* Create a button-control
* Use color instead of r, g, b, a
* Refactor out the Go-related code to a separate file

"""

def fullscreen_control(graphics, ControlClass, *args, **kw):
    #assert(issubclass(ControlClass, Control) and "ControlClass must be a subclass of Control")
    kw["screenpos"] = (0, 0)
    kw["buffersize"] = graphics.getSize()
    kw["borderwidth"] = 0
    return ControlClass(*args, **kw)

class Graphics(object):

    instanciated = False

    def __init__(self, size=(640, 480), bpp=16, screen=True, fullscreen=False, BOARD=19, SPECIFIC_THEMEDIR="themes/uligo"):

        #print "Graphics size", BOARD
        
        self.RES = size
        self.BPP = bpp
        self._boxes = []

        flags = DOUBLEBUF
        if fullscreen:
            flags = FULLSCREEN

        # Is this just a buffer or _the_ screen
        self._is_screen = screen
        if screen:
            if not Graphics.instanciated:
                Graphics.instanciated = True
                # This one initializes too much!
                #pygame.init()
                # A function
                setmode = pygame.display.set_mode
                self.screen = setmode(self.RES, flags, self.BPP)
                self.screen.set_alpha(None)
                self.buffer = self.screen #pygame.Surface(self.RES)
            #else:
            #    assert(not "Can only create the screen-graphics once")
        else:
            self.buffer = pygame.Surface(self.RES)

        pygame.display.set_caption("Loading...")

        # A function
        self.quickpixel = self.buffer.set_at

        # Load images
        self.board = pygame.image.load(addpath(os.path.join(SPECIFIC_THEMEDIR, "board.png")))
        w, h = self.buffer.get_size()
        self.board = pygame.transform.scale(self.board, (w, h))
        # not perfect, not based on anythin other than hunch, but it sortof works
        margin = 27 + int(19 + BOARD * -1.8)
        self.margin = margin
        # calculate the bottom/right margin
        leftover = w - (((BOARD - 1) * (w / float(BOARD)) + margin) - margin)
        botmargin = leftover - margin
        # Draw the lines on the board
        xspace = w / float(BOARD)
        # one xnum per vertical line
        for xnum in range(BOARD):
            x = int(xnum * xspace) + margin
            pygame.draw.line(self.board, (0, 0, 0), (x, margin), (x, h - botmargin), 1)
        yspace = h / float(BOARD)
        # one ynum per horizontal line
        for ynum in range(BOARD):
            y = int(ynum * yspace) + margin
            pygame.draw.line(self.board, (0, 0, 0), (margin, y), (w - botmargin, y), 1)
        # Draw the letters on the board
        pygame.font.init()
        #myfont = pygame.font.Font("/usr/share/fonts/truetype/dustin/Balker.ttf", 12)
        self.myfont = pygame.font.SysFont(None, 12)
        self.letters = ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T"]
        self.letters = self.letters[:BOARD + 1]
        for i, l in enumerate(self.letters):
            halfletterwidth = 2
            x = int(i * xspace) + margin - halfletterwidth
            bgcolor = (200, 200, 0, 255)
            fontimage = self.myfont.render(l, False, (0, 0, 0, 255), bgcolor)
            fontimage.set_colorkey(bgcolor)
            self.board.blit(fontimage, (x, 0))
        numbers = list(map(str, list(range(BOARD, 0, -1))))
        for i, n in enumerate(numbers):
            halfletterheight = 5
            y = int(i * yspace) + margin - halfletterheight
            bgcolor = (200, 200, 0, 255)
            fontimage = self.myfont.render(n, False, (0, 0, 0, 255), bgcolor)
            fontimage.set_colorkey(bgcolor)
            fw = fontimage.get_width()
            self.board.blit(fontimage, (8 - fw, y))
        # Draw the starpoints on the board
        if BOARD == 19:
            starpoints = 3, 9, 15
            notpoints = ()
        elif BOARD == 9:
            starpoints = 2, 4, 6
            notpoints = (2, 4), (4, 2), (6, 4), (4, 6)
        elif BOARD == 5:
            starpoints = 2,
            notpoints = ()
        else:
            starpoints = ()
            notpoints = ()
        if starpoints:
            if len(starpoints) == 1:
                center = starpoints[0]
            else:
                center = starpoints[int(len(starpoints) / 2.0 + 0.5)]
            for x in starpoints:
                for y in starpoints:
                    if (x, y) not in notpoints:
                        pos = (int(xspace * x) + margin, int(yspace * y) + margin)
                        pygame.draw.circle(self.board, (0, 0, 0), pos, 4, 0)

        self.black = pygame.image.load(addpath(os.path.join(SPECIFIC_THEMEDIR, "black.png")))
        self.white = pygame.image.load(addpath(os.path.join(SPECIFIC_THEMEDIR, "white.png")))

    def refresh_screen(self):
        screen = pygame.display.get_surface()
        screen.blit(self.buffer, (0, 0))
        pygame.display.update()

    def getSurf(self):
        return self.buffer

    def show_surface(self, surface):
        """Shows a surface all over."""
        width, height = self.RES
        buffer = pygame.transform.scale(surface, (width, height))
        self._boxes.append(self.buffer.blit(buffer, (0, 0)))
        self.refresh_screen()

    def blit(self, graphics, pos):
        """ Blits another Graphics-object onto itself """
        self._boxes.append(self.buffer.blit(graphics.buffer, pos))

    def blitControl(self, control):
        """
        All controls have a .getGraphics(), a .getPos() and a .getSize()
        Use it to get the surface, and blit it
        """
        if not isinstance(control, Control):
            print(control, "is not a Control!")
            return
        borderwidth = control.getBorderwidth() 
        if control.hasBorder():
            x, y = control.getPos()
            w, h = control.getSize()
            self.rect(    x - borderwidth, y - borderwidth,
                    w + 2 * borderwidth, h + 2 * borderwidth,
                    255, 200, 64, 255,
                    borderwidth)
        self.blit(control.getGraphics(), control.getPos())
    
    def pixel(self, x, y, r, g, b, a):
        self.buffer.set_at((x, y), (r, g, b, a))

    def clear(self, color):
        self.buffer.fill(color)
        self.buffer.blit(self.board, (0, 0))

    def clearControl(self, control):
        if not isinstance(control, Control):
            print(control, "is not a Control!")
            return
        borderwidth = control.getBorderwidth() + 1
        x, y = control.getPos()
        if control.hasBorder():
            x -= borderwidth
            y -= borderwidth
        w, h = control.getSize()
        if control.hasBorder():
            w += 2 * borderwidth
            h += 2 * borderwidth
        # Backgroundcolor instead?
        r, g, b, a = (0, 0, 0, 255)
        self.box(x, y, w, h, r, g, b, a)

    def box(self, x, y, w, h, r, g, b, a):
        self._boxes.append(self.buffer.fill((r, g, b, a), (x, y, w, h)))
        #self._boxes.append(pygame.draw.rect(self.buffer, (r, g, b, a),
        #(x, y, w, h), 0))

    def magicellipse(self, x, y, w, h, r, g, b, a):
        #print "magicellipse"
        # alpha is unused for now
        if r == 255 and g == 255 and b == 255:
            image = pygame.transform.scale(self.white, (w - 2, h - 2))
            self._boxes.append(self.buffer.blit(image, (x, y)))
        elif r == 0 and g == 0 and b == 0:
            image = pygame.transform.scale(self.black, (w - 2, h - 2))
            self._boxes.append(self.buffer.blit(image, (x, y)))
        else:
            self._boxes.append(self.buffer.blit(self.board, (x, y), (x, y, w - 2, h - 2)))

    def ellipse(self, x, y, w, h, r, g, b, a, bw):
        #print "ellipse"
        self._boxes.append(pygame.draw.ellipse(self.buffer, (r, g, b, a), (x, y, w, h), bw))

    def rect(self, x, y, w, h, r, g, b, a, bw):
        self._boxes.append(pygame.draw.rect(self.buffer, (r, g, b, a), (x, y, w, h), bw))

    def refresh(self):
        if self._is_screen:
            self.screen.blit(self.buffer, (0, 0))
            pygame.display.update(self._boxes)
            self._boxes = []
        #else:
        #    assert(not "Trying to refresh a buffer")

    def getWidth(self):
        return self.RES[0]

    def getHeight(self):
        return self.RES[1]

    def getSize(self):
        return self.RES

    def getBpp(self):
        return self.BPP

class Control(object):
    """ A general control """

    def __init__(self, screenpos=(0, 0), buffersize=(20, 20), bpp=32,
            borderwidth=2, BOARD=19, SPECIFIC_THEMEDIR="themes/uligo"):

        # Set internal variables
        self._screenpos = screenpos
        self._buffersize = buffersize
        self._bpp = bpp
        self._borderwidth = borderwidth

        #print "Control BOARD", BOARD

        # Create a backbuffer based on internal variables
        self._graphics = Graphics(self._buffersize, self._bpp, False, BOARD=BOARD, SPECIFIC_THEMEDIR=SPECIFIC_THEMEDIR)

        # Todo: rename these here and in PixelGrid
        self.gfx_width = self._graphics.getWidth()
        self.gfx_height = self._graphics.getHeight()

    def getGraphics(self):
        return self._graphics

    def getPos(self):
        return self._screenpos

    def getSize(self):
        return self._buffersize

    def setPos(self, pos):
        self._screenpos = pos

    def hasBorder(self):
        return (self._borderwidth > 0)

    def setBorderwidth(self, borderwidth):
        self._borderwidth = borderwidth

    def getBorderwidth(self):
        return self._borderwidth
