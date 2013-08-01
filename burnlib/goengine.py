#!/usr/bin/python
#-*-coding:utf-8-*-
#vim: set enc=utf8:
#
# author:   Alexander Rødseth <alexanro@stud.ntnu.no>
# date:     May 2005
#

from burnlib.imageengine import Graphics
from burnlib.imageengine import Control
from burnlib.analyze import Analyzer
from sys import exit as sysexit
from os.path import splitext
import os
import pygame
from pygame.locals import RLEACCEL
from burnlib.common import addpath

class GoGrid(Control):

    def __init__(self, screenpos=(0, 0), buffersize=(128, 128),
            gridsize=(19, 19), bpp=32, borderwidth=2, filename="gnugocmd.conf"):

        #print "GoGrid size", gridsize

        if type(gridsize) == type(int()):
            gridsize = (gridsize, gridsize)

        self.BOARD = gridsize[0]

        gnugocmd = open(addpath(filename)).read().strip()
        self.to_gnugo, self.from_gnugo = os.popen2(gnugocmd)
        self._gtpnr = 1
        self.gridwidth = gridsize[0]
        self.gtp("boardsize " + str(gridsize[0]))
        self.gtp("clear_board")

        self._level = 9

        self._b_captures = 0
        self._w_captures = 0

        Control.__init__(self, screenpos, buffersize, bpp, borderwidth, self.BOARD)

        self._fgcolor = (64, 128, 255, 255)
        self._bgcolor = (150, 50, 0, 255)
        self.pixels = {}

        # Set the size and draw, if possible
        if self.setSize(gridsize):
            self.topleftCursor()
            self.drawAll()
        #else:
        #    assert(not "Illegal size of GoGrid, in __init__")

        # For quick "previous" functionality
        self.guesscounter = 0

        self.history = []
        self.history_index = -1
        self.boardhistory = {}
        self.cursorhistory = {}
        self.capturehistory = {}

        self.filename = ""
        self.lastplayed = "W"

        self.lastmove = None

        self.illegal_ok = False


    def gtp(self, command):
        verbose = True
        cmd = str(self._gtpnr) + " " + command
        if verbose:
            print cmd
        self.to_gnugo.write(cmd + "\n")
        self.to_gnugo.flush()
        status = self.from_gnugo.read(1)
        value = status
        while not status == "\n":
            status = self.from_gnugo.read(1)
            value += status
        assert(self.from_gnugo.read(1) == "\n")
        if verbose:
            print value
        self._gtpnr += 1
        return value[1 + len(str(self._gtpnr)):]
    
    def showboard(self):
        cmd = str(self._gtpnr) + " " + "showboard"
        print cmd
        self.to_gnugo.write(cmd + "\n")
        self.to_gnugo.flush()
        s = ""
        # y is not used, it's just a counter
        for y in xrange(self.gridwidth + 4):
            byte = self.from_gnugo.read(1)
            s += byte
            while not byte == "\n":
                byte = self.from_gnugo.read(1)
                s += byte
        print s
        self._gtpnr += 1

    def showlastmove(self):
        self._x, self._y = self.lastmove
        self.cursorMoved()

    def fullclear(self):
        self.clear_history()
        self.clear()
        self.pixels2gnugo()

    def clear(self):
        self.pixels = {}
        self.centerCursor()
        self.drawAll()

    def clear_history(self):
        self.history = []
        self.history_index = -1
        self.boardhistory = {}
        self.cursorhistory = {}
        self.capturehistory = {}

    def grow(self, realpercentage):
        newwidth = int(self._buffersize[0] * realpercentage)
        newheight = int(self._buffersize[1] * realpercentage)
        self.resize((newwidth, newheight))
    
    def centerCursor(self):
        """ Set the cursor-position based on the gridsize """
        self._x = self._width / 2
        self._y = self._height / 2
        self._oldx = self._x
        self._oldy = self._y

    def topleftCursor(self):
        """ Set the cursor-position based on the gridsize """
        self._x = 15
        self._y = 3
        self._oldx = self._x
        self._oldy = self._y

    def jumppos(self, xstring, ystring):
        """ Jump to Go-koordinates """
        self._x = int(xstring) - 1
        self._y = int(ystring) - 1
        self._oldx = self._x
        self._oldy = self._y
        self.drawAll()
    
    def resize(self, controlsize):
        """
        controlsize is not in grid-coordinates, but in screen-coordinates
        """

        # Check the size
        if (controlsize[0] < self._width) and (controlsize[1] < self._height):
            print "Controlsize less than imagesize not implemented"
            return

        # Re-initialize the graphics, deleting the screen-contents,
        # but not the grid-contents
        self.__init__(self._screenpos, controlsize, self._bpp,
                self._borderwidth)

        # Set the size and draw, if possible
        if self.setSize(self._gridsize):
            self.drawAll()
        #else:
        #    assert(not "Illegal size of GoGrid, in resize")

    def setSize(self, gridsize):
        """ width and height is the gridwidth and gridheight """
        width, height = gridsize
        self._gridsize = gridsize
        if width > self.gfx_width or height > self.gfx_height:
            print "Too small image compared to gridsize"
            return False
        self._xmax = width - 1
        self._ymax = height - 1
        self._width = width
        self._height = height
        self._cellwidth = (self.gfx_width / float(self._width))
        self._cellheight = (self.gfx_height / float(self._height))
        if (self._cellwidth <= 0) or (self._cellheight <= 0):
            print "Size < 0 doesn't work very well with Pygame..."
            return False
        if not (self._cellwidth % 2) and not (self._cellheight % 2):
            #print "Optimal size"
            self._optimal = True
        else:
            #print "Non-optimal size"
            self._optimal = False
            # return False
        return True
        
    def make_transp(self, image):
        """
        This function simply takes the topleft color-value and uses it to make
        that specific color transparent for the whole image.
        """
        colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, RLEACCEL)
        return image

    def setSurf(self, surf):
        self.pixels.clear()
        surf = surf.convert()
        surfsize = surf.get_size()
        mysize = (self._width, self._height)
        if not surfsize == mysize:
            self.setSize(surf.get_size())
            self.centerCursor()
        for y in range(surf.get_height()):
            for x in range(surf.get_width()):
                self.pixels[(x, y)] = surf.get_at((x, y))
        self.drawAll()

    def getSurf(self):
        surfprops = {}
        surfprops["size"] = (self._width, self._height)
        surfprops["bpp"] = self._graphics.getBpp()
        surfprops["screen"] = False
        surfprops["BOARD"] = self.BOARD
        #print "getSurf BOARD", self.BOARD
        graphics = Graphics(**surfprops)
        for pos, color in self.pixels.items():
            graphics.quickpixel(pos, color)
        return graphics.getSurf()

    def savetransp(self, fn):
        """ Saves an image to a file, and makes it transparent as well """
        self.save(fn, True)
    
    def save(self, fn, transp=False):
        """ Saves an image to a file """
        print "Saving %s..." % fn
        ext = splitext(fn)[1].lower()
        if ext in [".bmp", ".tga"]:
            try:
                if transp:
                    pygame.image.save(self.make_transp(self.getSurf()), fn)
                else:
                    pygame.image.save(self.getSurf(), fn)
            except pygame.error:
                print "Pygame was unable to save (%s)." % fn
        else:
            print "Unknown file format (%s)." % ext

    def g2s(self, x, y):
        """ Gridspace to screenspace """
        sx = int(x * self._cellwidth)
        sy = int(y * self._cellheight)
        return (sx, sy)

    def g2s_x(self, x):
        """ Gridspace to screenspace """
        return int(x * self._cellwidth)

    def g2s_y(self, y):
        """ Gridspace to screenspace """
        return int(y * self._cellheight)

    def s2g(self, x, y):
        """ Screenspace to gridspace """
        gx = x / self._cellwidth
        gy = y / self._cellheight
        return (gx, gy)

    def getScreenRect(self, gx, gy):
        """ Find the screenrect based on the grid coordinates """
        sx, sy = self.g2s(gx, gy)
        sw = self.g2s_x(gx + 1) - sx
        sh = self.g2s_y(gy + 1) - sy
        return (sx, sy, sw, sh)

    def getBgColor(self):
        return self._bgcolor

    def setBgColor(self, r, g, b, a):
        self._bgcolor = (r, g, b, a)

    def setFgColor(self, r, g, b, a):
        self._fgcolor = (r, g, b, a)

    def getFgColor(self):
        return self._fgcolor

    # ***********************
    # * Screenspace methods *
    # ***********************

    def pickupcolor(self):
        self.setFgColor(*self.get(self._x, self._y))

    def getCellSize(self):
        return int(self._cellwidth), int(self._cellheight)

    def drawPixel(self, pos):
        # Find the ScreenRect of the pixel
        sx, sy, sw, sh = self.getScreenRect(pos[0], pos[1])

        # TEMPORARY (trial and error-based)
        of = sw / 8
        if self.BOARD == 5:
            of += 2
        elif self.BOARD == 9:
            of -= 8
        elif self.BOARD == 19:
            of -= 2
        else:
            of -= 2
        sx -= of
        sy -= of
        
        if pos in self.pixels.keys():
            # If the pixel exists, draw it with the color it has
            r, g, b, a = self.pixels[pos]
            #self._graphics.box(sx, sy, sw, sh, r, g, b, a)
            self._graphics.magicellipse(sx, sy, sw, sh, r, g, b, a)
        else:
            # If the pixel doesn't exist, draw it with the backgroundcolor
            r, g, b, a = self._bgcolor
            #self._graphics.box(sx, sy, sw, sh, r, g, b, a)
            self._graphics.magicellipse(sx, sy, sw, sh, r, g, b, a)
    
    def drawAll(self):
        #w, h = self.getCellSize()
        # Clear
        self._graphics.clear(self._bgcolor)
        # Pixels
        for pos in self.pixels.keys():
            sx, sy, sw, sh = self.getScreenRect(pos[0], pos[1])

            # TEMPORARY (trial and error-based)
            of = sw / 8
            if self.BOARD == 5:
                of += 2
            elif self.BOARD == 9:
                of -= 8
            elif self.BOARD == 19:
                of -= 2
            else:
                of -= 2
            sx -= of
            sy -= of
            
            r, g, b, a = self.pixels[pos]
            self._graphics.magicellipse(sx, sy, sw, sh, r, g, b, a)
        self.drawCursor()

    def drawPixelHere(self):
        self.drawPixel((self._x, self._y))

    def drawPixelLast(self):
        self.drawPixel((self._oldx, self._oldy))

    def saveLastPosition(self):
        self._oldx = self._x
        self._oldy = self._y

    def drawCursor(self):
        r, g, b, a = (32, 64, 128, 255)
        color = self.get(self._x, self._y)
        if color:
            cr, cg, cb = color[0:3]
            if cr > (cg + cb):
                r = 0
                g = 255
                b = 255
            elif cb > (cr + cg):
                r = 255
                g = 255
                b = 0
            elif cg > (cr + cg):
                r = 255
                g = 0
                b = 255
            elif (cg + cr + cb) > 600:
                r = 255
                g = 0
                b = 0
            elif (cg + cr + cb) < 900:
                r = 255
                g = 0
                b = 0
            else:
                r = 255 - cr
                g = 255 - cg
                b = 255 - cb
            a = color[3] / 2
        # Cursor
        sw, sh = self.getCellSize()
        sx, sy = self.g2s(self._x, self._y)
        if (sw < 4) or (sh < 4):
            #print "pixelcursor!"
            sx = int(sx + sw / 2.0)
            sy = int(sy + sh / 2.0)

            # TEMPORARY (trial and error-based)
            of = sw / 8
            if self.BOARD == 5:
                of += 2
            elif self.BOARD == 9:
                of -= 8
            elif self.BOARD == 19:
                of -= 2
            else:
                of -= 2
            sx -= of
            sy -= of
            
            self._graphics.pixel(sx, sy, r, g, b, a)
        else:
            woff = sw / 4
            hoff = sh / 4

            of = woff / 2

            # TEMPORARY (trial and error-based)
            if self.BOARD == 5:
                of += 2
            elif self.BOARD == 9:
                of -= 8
            elif self.BOARD == 19:
                of -= 2
            else:
                of -= 2

            #self._graphics.rect(x + woff, y + hoff, w - woff * 2, h - hoff * 2, r, g, b, a, 1)
            self._graphics.ellipse(sx + woff - of, sy + hoff - of, sw - woff * 2, sh - hoff * 2, r, g, b, a, 1)
    
    def cursorMoved(self):
        self.drawPixelHere()
        self.drawPixelLast()
        self.drawCursor()
        self.saveLastPosition()

    def colorChanged(self):
        self.drawPixelHere()
        self.drawCursor()

    # *********************
    # * Gridspace methods *
    # *********************

    def put(self, x, y, r, g, b, a):
        self.pixels[(x,y)] = (r, g, b, a)

    def get(self, x, y):
        if (x,y) in self.pixels:
            return self.pixels[(x, y)]
        else:
            return False

    def plot(self):
        r, g, b, a = self._fgcolor
        self.put(self._x, self._y, r, g, b, a)
        self.colorChanged()

    def removePixel(self):
        if self.pixelHere():
            del self.pixels[(self._x, self._y)]
        self.colorChanged()

    def pixelHere(self):
        return (self._x, self._y) in self.pixels.keys()

    def getHere(self):
        return self.get(self._x, self._y)

    def toggleblack(self):
        if self.saymove("B").find("illegal move") == -1:
            # a legal move
            self.togglecolor(0, 0, 0)
            self.gnugo_gamelogic()
        elif self.illegal_ok:
            print "Illegal move, but here you go."
            self.togglecolor(0, 0, 0)
        else:
            return False
        return True

    def togglewhite(self):
        if self.saymove("W").find("illegal move") == -1:
            # a legal move
            self.togglecolor(255, 255, 255)
            self.gnugo_gamelogic()
        elif self.illegal_ok:
            print "Illegal move, but here you go."
            self.togglecolor(255, 255, 255)
        else:
            return False
        return True

    def toggleillegal(self):
        self.illegal_ok = not self.illegal_ok

    def gnugowhite(self):
        #print "GnuGo is thinking..."
        gnugopos = self.gtp("genmove white").strip()
        pygame.event.clear()
        #print gnugopos
        if gnugopos not in ["PASS", "resign"]:
            self.playhere("W", gnugopos)
            self.gnugo_gamelogic()
#            self.refresh_now()

    def refresh_now(self):
        self.drawAll()
        self._graphics.refresh_screen()

    def status(self):
        self.showlastmove()
        self.gtp("estimate_score")
        print "level", self._level

    def nextlevel(self):
        self._level += 3 
        if self._level > 9:
            self._level = 0
        self.level(str(self._level))

    def newaswhite(self, mode=""):
        self.fullclear()
        self.nextlevel()
        if mode == "experimental":
            self.myplay("black")
        else:
            self.gnugoblack()
        print "level", self._level

    def playblackorwhite(self, mode="", color="black"):
        if color == "black":
            if self.toggleblack():
                self.refresh_now()
                self.showboard()
                if mode == "experimental":
                    self.myplay("white")
                else:
                    self.gnugowhite()
        else:
            if self.togglewhite():
                self.refresh_now()
                self.showboard()
                if mode == "experimental":
                    self.myplay("black")
                else:
                    self.gnugoblack()
    
    def playblack(self, mode=""):
        self.playblackorwhite(mode, "black")

    def playwhite(self, mode=""):
        self.playblackorwhite(mode, "white")

    def quit(self, exitcode="0"):
        self.showboard()
        self.gtp("quit")
        sysexit(int(exitcode))

    def gnugoblack(self):
        #print "GnuGo is thinking..."
        gnugopos = self.gtp("genmove black").strip()
        pygame.event.clear()
        #print gnugopos
        if gnugopos not in ["PASS", "resign"]:
            self.playhere("B", gnugopos)
            self.gnugo_gamelogic()

    def undo(self):
        result = self.gtp("undo")
        if "cannot undo" not in result:
            self.gnugo2pixels()

    def multigtp(self, cmd):
        lines = []
        first = True
        cmd = str(self._gtpnr) + " " + cmd
        print cmd
        self.to_gnugo.write(cmd + "\n")
        self.to_gnugo.flush()
        neste = ""
        while neste != "\n":
            # 1. Read until \n
            s = neste 
            byte = self.from_gnugo.read(1)
            while not byte == "\n":
                #lastbyte = byte
                s += byte
                byte = self.from_gnugo.read(1)
            print s
            if first:
                s = s[2 + len(str(self._gtpnr)):]
                first = False
            lines.append(s)
            # 2. Is the next byte not a "\n"?
            neste = self.from_gnugo.read(1)
        self._gtpnr += 1
        return lines

    def futurewhite(self):
        self.gtp("genmove white")
        lines = self.multigtp("top_moves")
        moves = lines[0].split()[::2]
        self.gtp("undo")
        for pos in moves:
            self.playhere("x", pos)

    def nextorload(self):
        """
        Go to the next move if there is a move history
          (good for playing through games)
        Place a black stone if there is not
          (good for practicing tsumego)
        """
        if self.history:
            self.next()
        else:
            self.loadsgf()

    def guessorplace(self):
        """
         Guess the next move if there is a move history
           (good for playing through games)
         Reload the sgf if there is not
           (good for practicing tsumego)
        """
        if self.history:
            self.playguess()
        else:
            if self.lastplayed == "B":
                if self.togglewhite():
                    self.lastplayed = "W"
            elif self.lastplayed == "W":
                if self.toggleblack():
                    self.lastplayed = "B"

    def play100moves(self):
        for x in xrange(100):
            self.myplay("black")
            self.refresh_now()
            self.gtp("estimate_score")
            self.gnugowhite()
            self.refresh_now()
        print "Done with 100"

    def next(self):
        self.guesscounter = 0
        self.boardhistory[self.history_index] = self.pixels.copy()
        self.cursorhistory[self.history_index] = self._x, self._y
        self.capturehistory[self.history_index] = self._b_captures, self._w_captures
        self.history_index += 1
        try:
            colorpos = self.history[self.history_index]
        except IndexError:
            #print "Empty history", self.history, self.history_index
            self.history_index -= 1
            return
        playercolor = colorpos[0]
        pos = colorpos[1:]
        if playercolor == "W":
           self.gtp("play white " + pos)
        else:
           self.gtp("play black " + pos)
        self.playhere(playercolor, pos)
        self.gnugo_gamelogic()
        self.drawAll()

    def previous(self):
        if self.history_index > -1:
            self.history_index -= 1
            self.pixels = self.boardhistory[self.history_index].copy()
            self._x, self._y = self.cursorhistory[self.history_index]
            self._b_captures, self._w_captures =  self.capturehistory[self.history_index]
            self.pixels2gnugo()
            self.drawAll()
            self.cursorMoved()

    def settings2dict(self, settings):
        #print settings
        sd = {}
        tokens = settings.split("]")
        name = ""
        for token in tokens:
            token = token.strip()
            if token:
                if (token[0] in "ABCDEFGHIJKLMNOPQRSTUVWXYZ") and (token.count("[") == 1):
                    #print "Type-token", token
                    name, data = token.split("[")
                    sd[name] = [data]
                elif token[0] == "[":
                    #print "Data-token", token
                    sd[name].append(token.split("[")[1])
                #else:
                #    print "Invalid token:", token
        #print sd
        # Refine the data
        for key, value in sd.items():
            if len(value) == 1:
                sd[key] = value[0]
            try:
                sd[key] = int(sd[key])
            except TypeError:
                pass
            except ValueError:
                pass
        return sd

    def sgfmove(self, move, precolor="AB", withi=False):
        try:
            x, y = self.convertpos(move, "sgf", "numpos", withi)
        except ValueError:
            return
        self._x, self._y = x, y
        self._oldx, self._oldy = self._x, self._y
        if precolor == "AB":
            self.toggleblack()
        else:
            self.togglewhite()
        self._x, self._y = self._oldx, self._oldy


    def loadsgf(self, filename=""):
        if self.filename and not filename:
            filename = self.filename
        elif filename:
            self.filename = filename
        else:
            return
        print "filename now", filename
        if filename.find("file:/") == 0:
            filename = filename[filename.find("/"):]
        self.fullclear()
        self.gtp("clear_board")
        sgfdata = open(filename).read().split(";")
        if not sgfdata[0].strip()[0] == "(":
            print "Unable to load %s, because it doesn't start with '('"%(filename)
            return
        if not sgfdata[-1].strip()[-1] == ")":
            print "Unable to load %s, because it doesn't end with ')'"%(filename)
            return
        # Make the dictionary with the sgf-settings
        settings = self.settings2dict(sgfdata[1])
        print "Settings", settings

        # TODO: A better check
        # Is "i" a position in the list of moves?
        withi = False
        for precolor in ["AB", "AW"]:
            if precolor in settings:
                for move in settings[precolor]:
                    if "i" in move:
                        withi = True
                        break
            if withi == True:
                break
        
        # Place the preset stones
        for precolor in ["AB", "AW"]:
            if precolor in settings:
                if (len(settings[precolor]) == 2) and (len(settings[precolor][0]) == 1):
                    #only one move in the list
                    self.sgfmove(settings[precolor], precolor, withi)
                else:
                    for move in settings[precolor]:
                        self.sgfmove(move, precolor, withi)

        # Make a list of moves and remove whitespace
        moves = map(lambda x:x.strip(), sgfdata[2:])
        if moves:
            # Remove the ')' at the end of the last move
            try:
                moves[-1] = moves[-1][:-1]
            except IndexError:
                print "Unable to remove the ')' at the end. Oh well."
        # is "i" a part of a move?
        # TODO: Better check for i or not
        if not withi:
            withi = bool([True for move in moves if "i" in move])
        # Convert the moves from B[aa] format to BA1 format (without I)
        self.history = []
        # This is also done if there are no moves in "moves", which is fine
        for move in moves:
            tempmove = ""
            if "B[" in move:
                tempmove = move[move.find("B["):]
            elif "W[" in move:
                tempmove = move[move.find("W["):]
            else:
                continue
            tempmove = tempmove[:tempmove.find("]")]
            #print "tempmove", tempmove
            color = tempmove[0]
            try:
                colorpos = color + self.convertpos(tempmove[2:4], "sgf", "gnugo", withi)
            except ValueError:
                #print "VALUEERROR", "tempmove", tempmove, "colorpos", colorpos
                continue
            except IndexError:
                continue
            #print "append", colorpos
            self.history.append(colorpos)
        self.guesscounter = 0
        self.history_index = -1
        self.boardhistory = {}
        self.cursorhistory = {}
        self.capturehistory = {}

        self.drawAll()
        self.refresh_now()
        print "Moves", self.history

    def playguess(self):
        x, y = self.g2s(self._x, self._y)
        self._graphics.rect(x + 4, y + 4, 16, 16, 255, 0, 0, 255, 1)
        try:
            colorpos = self.history[self.history_index + 1]
        except IndexError:
            return
        pos = colorpos[1:]
        letter = self._graphics.letters[self._x]
        number = (self._y * -1) + self.gridwidth
        guesspos = letter + str(number)
        if pos == guesspos:
            if self.guesscounter > 1:
                print "You managed to guess the next move in", self.guesscounter, "clicks! :-)"
            self.next()
        else:
            self.guesscounter += 1

    def mousepos(self, posx, posy):
        self._x, self._y = map(int, self.s2g(posx, posy))
        self.cursorMoved()

    def savesgf(self, filename):
        self.gtp("printsgf " + filename)

    def liststones(self):
        print self.gtp("list_stones black")
        print self.gtp("list_stones white")

    def pixels2gnugo(self):
        self.gtp("clear_board")
        for x in xrange(self.gridwidth):
            for y in xrange(self.gridwidth):
                if (x, y) in self.pixels:
                    letter = self._graphics.letters[x]
                    number = (y * -1) + self.gridwidth
                    pos = letter + str(number)
                    if self.pixels[(x, y)] == (0, 0, 0, 0):
                        self.gtp("play black " + pos)
                    else:
                        self.gtp("play white " + pos)

    def analyze(self):
        """
        Uses image-manipulation techniques for finding a nice spot to place a black stone.
        """
        a = Analyzer(self)

        redsurface, redexclude = a.blackliberties()
        self.showwait(redsurface, 500)

        greensurface, greenexclude = a.voidliberties()
        self.showwait(greensurface, 500)

        bluesurface, blueexclude = a.whiteliberties()
        self.showwait(bluesurface, 500)

        surface = a.combine(redsurface, greensurface, bluesurface)
        self.showwait(surface, 500)

        redblur = a.blur4(redsurface, redexclude)
        self.showwait(redblur, 500)

        greenblur = a.blur4(greensurface, greenexclude)
        self.showwait(greenblur, 500)

        blueblur = a.blur4(bluesurface, blueexclude)
        self.showwait(blueblur, 500)

        stoneblur = a.combine(redblur, greenblur, blueblur)
        self.showwait(stoneblur, 500)

        moreblur, pos = a.blurmore(stoneblur, 100, divnum=5.0)
        self.showwait(moreblur, 500)

        self.playhere("B", self.convertpos(pos, "numpos", "gnugo"))
        self.gnugo_gamelogic()
        self.pixels2gnugo()

        self.drawAll()

    def myplay(self, playcolor="black"):
        if playcolor == "black":
            black = True
        else:
            black = False

        movenum = len(self.pixels)
        #playnow = movenum % int(1 + 10 * (movenum / 40.0) ** 1.3) == 0
        #playnow = movenum % int(1 + 3 * (movenum / 40.0) ** 1.0001) == 0
        #playnow = movenum % 3 != 0
        #playnow = movenum < 30

        #if movenum < 50:
        #    playnow = (movenum + 2) % 3 != 0 
        #else:
        #    playnow = (movenum + 2) % 3 == 0 
        playnow = (movenum < 30)
        
        if playnow:
            a = Analyzer(self)
            redsurface, redexclude = a.blackliberties()
            greensurface, greenexclude = a.voidliberties()
            bluesurface, blueexclude = a.whiteliberties()
            redblur = a.blur4(redsurface, redexclude)
            greenblur = a.blur4(greensurface, greenexclude)
            blueblur = a.blur4(bluesurface, blueexclude)
            stoneblur = a.combine(redblur, greenblur, blueblur)
            moreblur, pos = a.blurmore(stoneblur, 30, divnum=5.0)

            if pos and (pos not in self.pixels):
                gnugopos = self.convertpos(pos, "numpos", "gnugo")
                print "My move :-),", gnugopos
                # The formula below uses "B" if black is True(1), and "W" if False(0)
                self.playhere("B" * black + "W" * (not black), gnugopos)
                pygame.event.clear()
                self.gnugo_gamelogic()
                self.pixels2gnugo()
                return

        # Use GnuGo if none of the moves were appropriate
        if black:
            self.gnugoblack()
        else:
            self.gnugowhite()

    def showwait(self, surface, wait):
        self._graphics.show_surface(surface)
        pygame.time.wait(wait)

    def convertpos(self, data, fromtype="gnugo", totype="numpos", withi=False):
        """Converts between different types of coordinates.
           Type can be: numpos, sgf or gnugo
           "numpos" is like this: (3, 5)
              (counted from 0)
           "sgf" is like this: bq 
              (a letter, including i, represents a coordinate)
           "gnugo" is like this: D5
              (the letter, excluding i, represents a coordinate)
        """
        # Check the input
        assert(fromtype in ["numpos", "sgf", "gnugo"])
        assert(totype in ["numpos", "sgf", "gnugo"])

        # A to T, excluding I (from sgf)
        if withi:
            atot = "abcdefghijklmnopqrs"
        else:
            atot = "abcdefghjklmnopqrst"
        
        # Convert the input to xy-format
        if fromtype == "numpos":
            x, y = data
        elif fromtype == "gnugo":
            #print "from gnugo, data:", data
            pos = data.strip()
            # subtract 1
            x = self._graphics.letters.index(pos[0])
            # subtract 1, since gnugo starts at 1, then flip the scale
            y = ((int(pos[1:]) - 1) * -1) + (self.gridwidth - 1)
            #print "from gnugo, xy:", (x, y)
        elif fromtype == "sgf":
            #print "from sgf, data:", data
            x = atot.index(data[0])
            #print "x is", x, "atot is", atot
            if withi:
                y = atot.index(data[1])
            else:
                # flip the scale
                y = (atot.index(data[1]) * -1) + (self.gridwidth - 1)
            #print "from sgf, xy:", (x, y)

        # This is good to have
        assert(x in xrange(self.BOARD))
        assert(y in xrange(self.BOARD))

        # Convert the xy-format to the correct output
        if totype == "numpos":
            return (x, y)
        elif totype == "gnugo":
            #print "to gnugo, xy:", (x, y)
            letter = self._graphics.letters[x]
            # flip the scale, then add one
            number = (y - (self.gridwidth - 1)) * -1 + 1
            data = letter + str(number)
            #print "to gnugo, data:", data
            return data
        elif totype == "sgf":
            #print "to sgf, xy:", (x, y)
            if withi:
                number = y
            else:
                # flip the scale
                number = (self.gridwidth - 1) - y
            data = atot[x] + atot[number]
            #print "to sgf, data:", data
            return data

    def getliberties(self, numpos):
        """Uses GnuGo for finding the number of liberties at a given
           numerical position in the form (x, y)."""
        pos = self.convertpos(numpos, "numpos", "gnugo")
        try:
            return int(self.gtp("countlib " + pos))
        except ValueError:
            print "VALUEERROR", pos

    def gnugoinfo(self):
        self.gtp("name")
        self.gtp("version")
        self.gtp("protocol_version")
        self.gtp("query_boardsize")
        self.gtp("get_komi")
        self.gtp("get_handicap")
        self.gtp("time_left")

    def gnugo2pixels(self):
        x = self._x
        y = self._y
        self.clear()
        b = lambda pos:self.playhere("B", pos)
        w = lambda pos:self.playhere("W", pos)
        map(b, self.gtp("list_stones black").split())
        map(w, self.gtp("list_stones white").split())
        self._x = x
        self._y = y
        self.cursorMoved()

    def passblack(self):
        self.gtp("play black PASS")
        self.gnugowhite()

    def passwhite(self):
        self.gtp("play white PASS")
        self.gnugoblack()

    def level(self, level):
        self.gtp("level " + level)

    def time(self, main_time, byo_yomi_time, byo_yomi_stones):
        self.gtp("time_settings %s %s %s" % (main_time, byo_yomi_time, byo_yomi_stones))

    def playhere(self, playercolor, pos):
        """Usually called in connection with GnuGo making a move"""
        x, y = self.convertpos(pos, "gnugo", "numpos")
        self.lastmove = x, y
        self._x = x
        self._y = y
        self._oldx = self._x
        self._oldy = self._y
        self.drawAll()
        if playercolor == "B":
            self.togglecolor(0, 0, 0)
        elif playercolor == "W":
            self.togglecolor(255, 255, 255)
        else:
            self.togglecolor(128, 128, 128)

    def gnugo_gamelogic(self):
        """ Use the game-logic of GnuGo, import the stones """
        b = int(self.gtp("captures black"))
        w = int(self.gtp("captures white"))
        if not b == self._b_captures:
            self.gnugo2pixels()
            self._b_captures = b
        elif not w == self._w_captures:
            self.gnugo2pixels()
            self._w_captures = w

    def saymove(self, color):
        letter = self._graphics.letters[self._x]
        number = (self._y * -1) + self.BOARD
        pos = letter + str(number)
        if color == "B":
            return self.gtp("play black " + pos)
        else:
            return self.gtp("play white " + pos)

    def togglecolor(self, r, g, b):
        self.setFgColor(int(r), int(g), int(b), 0)
        self.toggle()

    def toggle(self):
        # TODO: Gjør sånn at farger som ikke er svarte eller hvite ikke har noe å si
        """ Toggles the selected pixel on and off """
        if self.pixelHere():
            if self.getHere() == self.getFgColor():
                #print "pixel with fgcolor -> no pixel"
                self.removePixel()
                self.pixels2gnugo()
            else:
                #print "pixel without fgcolor -> pixel with fgcolor"
                self.plot()
                self.pixels2gnugo()
        else:
            #print "no pixel -> pixel with fgcolor"
            self.plot()

    def left(self):
        """ Moves the imagecursor to the left """
        self._x -= 1
        if self._x < 0:
            self._x = self._xmax
            #self.up()
        self.cursorMoved()
    
    def right(self):
        """ Moves the imagecursor to the right """
        self._x += 1
        if self._x > self._xmax:
            self._x = 0
            #self.down()
        self.cursorMoved()

    def up(self):
        """ Moves the imagecursor up """
        self._y -= 1
        if self._y < 0:
            self._y = self._ymax
            #self.left()
        self.cursorMoved()

    def down(self):
        """ Moves the imagecursor down """
        self._y += 1
        if self._y > self._ymax:
            self._y = 0
            #self.right()
        self.cursorMoved()
