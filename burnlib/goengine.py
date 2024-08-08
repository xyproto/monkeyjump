#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: set enc=utf8:
#
# author:   Alexander Rødseth <rodseth@gmail.com>
# date:     May 2005
#

from burnlib.imageengine import Graphics
from burnlib.imageengine import Control
from burnlib.analyze import Analyzer
from sys import exit as sysexit
from os.path import splitext
import os
import subprocess
import pygame
from pygame.locals import RLEACCEL
from burnlib.common import addpath
from burnlib.popen2 import popen2

class GoGrid(Control):

    def __init__(self, screenpos=(0, 0), buffersize=(128, 128),
                 gridsize=(19, 19), bpp=32, borderwidth=2, gnugoconf="gnugocmd.conf", SPECIFIC_THEMEDIR="themes/uligo"):

        if isinstance(gridsize, int):
            gridsize = (gridsize, gridsize)

        self.BOARD = gridsize[0]

        with open(addpath(gnugoconf)) as gnugo_cmd_file:
            gnugocmd = gnugo_cmd_file.read().strip()
        self.to_gnugo, self.from_gnugo = popen2(gnugocmd)
        self._gtpnr = 1
        self.gridwidth = gridsize[0]
        self.gtp(f"boardsize {gridsize[0]}")
        self.gtp("clear_board")

        self._level = 9

        self._b_captures = 0
        self._w_captures = 0

        Control.__init__(self, screenpos, buffersize, bpp, borderwidth, self.BOARD, SPECIFIC_THEMEDIR)

        self._fgcolor = (64, 128, 255, 255)
        self._bgcolor = (150, 50, 0, 255)
        self.pixels = {}

        if self.setSize(gridsize):
            self.topleftCursor()
            self.drawAll()

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
        cmd = f"{self._gtpnr} {command}\n"
        if verbose:
            print(f"Sending command: {cmd}")
        self.to_gnugo.write(cmd)
        self.to_gnugo.flush()
        response = []
        while True:
            line = self.from_gnugo.readline().strip()
            response.append(line)
            if line.startswith("=") or line.startswith("?"):
                break
        response_str = "\n".join(response)
        if verbose:
            print(f"Received response: {response_str}")
        self._gtpnr += 1
        return response_str

    def gnugowhite(self):
        response = self.gtp("genmove white")
        lines = response.split("\n")
        if len(lines) > 1 and lines[-1].startswith("="):
            gnugopos = lines[-1].strip().split()[1]  # Get the move from the response
        else:
            gnugopos = lines[-1].strip()
        print(f"Move generated by GnuGo: {gnugopos}")  # Log the move
        pygame.event.clear()
        if gnugopos not in ["PASS", "resign"]:
            self.playhere("W", gnugopos)
            self.gnugo_gamelogic()

    def gnugoblack(self):
        response = self.gtp("genmove black")
        lines = response.split("\n")
        if len(lines) > 1 and lines[-1].startswith("="):
            gnugopos = lines[-1].strip().split()[1]  # Get the move from the response
        else:
            gnugopos = lines[-1].strip()
        print(f"Move generated by GnuGo: {gnugopos}")  # Log the move
        pygame.event.clear()
        if gnugopos not in ["PASS", "resign"]:
            self.playhere("B", gnugopos)
            self.gnugo_gamelogic()

    def showboard(self):
        response = self.gtp("showboard")
        print(response)

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
        self._x = self._width // 2
        self._y = self._height // 2
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
        """ controlsize is not in grid-coordinates, but in screen-coordinates """

        if controlsize[0] < self._width and controlsize[1] < self._height:
            print("Controlsize less than imagesize not implemented")
            return

        self.__init__(self._screenpos, controlsize, self._bpp,
                      self._borderwidth)

        if self.setSize(self._gridsize):
            self.drawAll()

    def setSize(self, gridsize):
        """ width and height is the gridwidth and gridheight """
        width, height = gridsize
        self._gridsize = gridsize
        if width > self.gfx_width or height > self.gfx_height:
            print("Too small image compared to gridsize")
            return False
        self._xmax = width - 1
        self._ymax = height - 1
        self._width = width
        self._height = height
        self._cellwidth = self.gfx_width / float(self._width)
        self._cellheight = self.gfx_height / float(self._height)
        if self._cellwidth <= 0 or self._cellheight <= 0:
            print("Size < 0 doesn't work very well with Pygame...")
            return False
        if not self._cellwidth % 2 and not self._cellheight % 2:
            self._optimal = True
        else:
            self._optimal = False
        return True

    def make_transp(self, image):
        """ This function simply takes the topleft color-value and uses it to make
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
        if surfsize != mysize:
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
        graphics = Graphics(**surfprops)
        for pos, color in self.pixels.items():
            graphics.quickpixel(pos, color)
        return graphics.getSurf()

    def savetransp(self, fn):
        """ Saves an image to a file, and makes it transparent as well """
        self.save(fn, True)

    def save(self, fn, transp=False):
        """ Saves an image to a file """
        print(f"Saving {fn}...")
        ext = splitext(fn)[1].lower()
        if ext in [".bmp", ".tga"]:
            try:
                if transp:
                    pygame.image.save(self.make_transp(self.getSurf()), fn)
                else:
                    pygame.image.save(self.getSurf(), fn)
            except pygame.error:
                print(f"Pygame was unable to save ({fn}).")
        else:
            print(f"Unknown file format ({ext}).")

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

    # Screenspace methods
    def pickupcolor(self):
        self.setFgColor(*self.get(self._x, self._y))

    def getCellSize(self):
        return int(self._cellwidth), int(self._cellheight)

    def drawPixel(self, pos):
        sx, sy, sw, sh = self.getScreenRect(pos[0], pos[1])
        of = sw // 8
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
            r, g, b, a = self.pixels[pos]
            self._graphics.magicellipse(sx, sy, sw, sh, r, g, b, a)
        else:
            r, g, b, a = self._bgcolor
            self._graphics.magicellipse(sx, sy, sw, sh, r, g, b, a)

    def drawAll(self):
        self._graphics.clear(self._bgcolor)
        for pos in self.pixels.keys():
            sx, sy, sw, sh = self.getScreenRect(pos[0], pos[1])
            of = sw // 8
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
            a = color[3] // 2

        sw, sh = self.getCellSize()
        sx, sy = self.g2s(self._x, self._y)
        if sw < 4 or sh < 4:
            sx = int(sx + sw / 2.0)
            sy = int(sy + sh / 2.0)

            of = sw // 8
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
            woff = sw // 4
            hoff = sh // 4

            of = woff // 2

            if self.BOARD == 5:
                of += 2
            elif self.BOARD == 9:
                of -= 8
            elif self.BOARD == 19:
                of -= 2
            else:
                of -= 2

            self._graphics.ellipse(sx + woff - of, sy + hoff - of, sw - woff * 2, sh - hoff * 2, r, g, b, a, 1)

    def cursorMoved(self):
        self.drawPixelHere()
        self.drawPixelLast()
        self.drawCursor()
        self.saveLastPosition()

    def colorChanged(self):
        self.drawPixelHere()
        self.drawCursor()

    def put(self, x, y, r, g, b, a):
        self.pixels[(x, y)] = (r, g, b, a)

    def get(self, x, y):
        if (x, y) in self.pixels:
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
            self.togglecolor(0, 0, 0)
            self.gnugo_gamelogic()
        elif self.illegal_ok:
            print("Illegal move, but here you go.")
            self.togglecolor(0, 0, 0)
        else:
            return False
        return True

    def togglewhite(self):
        if self.saymove("W").find("illegal move") == -1:
            self.togglecolor(255, 255, 255)
            self.gnugo_gamelogic()
        elif self.illegal_ok:
            print("Illegal move, but here you go.")
            self.togglecolor(255, 255, 255)
        else:
            return False
        return True

    def toggleillegal(self):
        self.illegal_ok = not self.illegal_ok

    def refresh_now(self):
        self.drawAll()
        self._graphics.refresh_screen()

    def status(self):
        self.showlastmove()
        self.gtp("estimate_score")
        print("level", self._level)

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
        print("level", self._level)

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

    def undo(self):
        result = self.gtp("undo")
        if "cannot undo" not in result:
            self.gnugo2pixels()

    def multigtp(self, cmd):
        lines = []
        first = True
        cmd = f"{self._gtpnr} {cmd}\n"
        print(f"Sending command: {cmd}")
        self.to_gnugo.write(cmd)
        self.to_gnugo.flush()
        while True:
            s = self.from_gnugo.readline().strip()
            if first:
                s = s[2 + len(str(self._gtpnr)):]
                first = False
            lines.append(s)
            if self.from_gnugo.read(1) == "\n":
                break
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
        if self.history:
            self.next()
        else:
            self.loadsgf()

    def guessorplace(self):
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
        for _ in range(100):
            self.myplay("black")
            self.refresh_now()
            self.gtp("estimate_score")
            self.gnugowhite()
            self.refresh_now()
        print("Done with 100")

    def next(self):
        self.guesscounter = 0
        self.boardhistory[self.history_index] = self.pixels.copy()
        self.cursorhistory[self.history_index] = self._x, self._y
        self.capturehistory[self.history_index] = self._b_captures, self._w_captures
        self.history_index += 1
        try:
            colorpos = self.history[self.history_index]
        except IndexError:
            self.history_index -= 1
            return
        playercolor = colorpos[0]
        pos = colorpos[1:]
        if playercolor == "W":
           self.gtp(f"play white {pos}")
        else:
           self.gtp(f"play black {pos}")
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
        sd = {}
        tokens = settings.split("]")
        name = ""
        for token in tokens:
            token = token.strip()
            if token:
                if (token[0] in "ABCDEFGHIJKLMNOPQRSTUVWXYZ") and (token.count("[") == 1):
                    name, data = token.split("[")
                    sd[name] = [data]
                elif token[0] == "[":
                    sd[name].append(token.split("[")[1])
        for key, value in sd.items():
            if len(value) == 1:
                sd[key] = value[0]
            try:
                sd[key] = int(sd[key])
            except (TypeError, ValueError):
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
        print("filename now", filename)
        if filename.find("file:/") == 0:
            filename = filename[filename.find("/"):]
        self.fullclear()
        self.gtp("clear_board")
        with open(filename) as sgf_file:
            sgfdata = sgf_file.read().split(";")
        if not sgfdata[0].strip()[0] == "(":
            print(f"Unable to load {filename}, because it doesn't start with '('")
            return
        if not sgfdata[-1].strip()[-1] == ")":
            print(f"Unable to load {filename}, because it doesn't end with ')'")
            return
        settings = self.settings2dict(sgfdata[1])
        print("Settings", settings)

        withi = False
        for precolor in ["AB", "AW"]:
            if precolor in settings:
                for move in settings[precolor]:
                    if "i" in move:
                        withi = True
                        break
            if withi:
                break

        for precolor in ["AB", "AW"]:
            if precolor in settings:
                if len(settings[precolor]) == 2 and len(settings[precolor][0]) == 1:
                    self.sgfmove(settings[precolor], precolor, withi)
                else:
                    for move in settings[precolor]:
                        self.sgfmove(move, precolor, withi)

        moves = [x.strip() for x in sgfdata[2:]]
        if moves:
            try:
                moves[-1] = moves[-1][:-1]
            except IndexError:
                print("Unable to remove the ')' at the end. Oh well.")
        if not withi:
            withi = any("i" in move for move in moves)
        self.history = []
        for move in moves:
            tempmove = ""
            if "B[" in move:
                tempmove = move[move.find("B["):]
            elif "W[" in move:
                tempmove = move[move.find("W["):]
            else:
                continue
            tempmove = tempmove[:tempmove.find("]")]
            color = tempmove[0]
            try:
                colorpos = color + self.convertpos(tempmove[2:4], "sgf", "gnugo", withi)
            except (ValueError, IndexError):
                continue
            self.history.append(colorpos)
        self.guesscounter = 0
        self.history_index = -1
        self.boardhistory = {}
        self.cursorhistory = {}
        self.capturehistory = {}

        self.drawAll()
        self.refresh_now()
        print("Moves", self.history)

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
                print(f"You managed to guess the next move in {self.guesscounter} clicks! :-)")
            self.next()
        else:
            self.guesscounter += 1

    def mousepos(self, posx, posy):
        self._x, self._y = map(int, self.s2g(posx, posy))
        self.cursorMoved()

    def savesgf(self, filename):
        self.gtp(f"printsgf {filename}")

    def liststones(self):
        print(self.gtp("list_stones black"))
        print(self.gtp("list_stones white"))

    def pixels2gnugo(self):
        self.gtp("clear_board")
        for x in range(self.gridwidth):
            for y in range(self.gridwidth):
                if (x, y) in self.pixels:
                    letter = self._graphics.letters[x]
                    number = (y * -1) + self.gridwidth
                    pos = letter + str(number)
                    if self.pixels[(x, y)] == (0, 0, 0, 0):
                        self.gtp(f"play black {pos}")
                    else:
                        self.gtp(f"play white {pos}")

    def analyze(self):
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
        black = playcolor == "black"

        movenum = len(self.pixels)
        playnow = movenum < 30

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
                print(f"My move :-), {gnugopos}")
                self.playhere("B" * black + "W" * (not black), gnugopos)
                pygame.event.clear()
                self.gnugo_gamelogic()
                self.pixels2gnugo()
                return

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
        assert fromtype in ["numpos", "sgf", "gnugo"]
        assert totype in ["numpos", "sgf", "gnugo"]

        if withi:
            atot = "abcdefghijklmnopqrs"
        else:
            atot = "abcdefghjklmnopqrst"

        if fromtype == "numpos":
            x, y = data
        elif fromtype == "gnugo":
            pos = data.strip()
            x = self._graphics.letters.index(pos[0])
            y = ((int(pos[1:]) - 1) * -1) + (self.gridwidth - 1)
        elif fromtype == "sgf":
            x = atot.index(data[0])
            if withi:
                y = atot.index(data[1])
            else:
                y = (atot.index(data[1]) * -1) + (self.gridwidth - 1)

        assert x in range(self.BOARD)
        assert y in range(self.BOARD)

        if totype == "numpos":
            return (x, y)
        elif totype == "gnugo":
            letter = self._graphics.letters[x]
            number = (y - (self.gridwidth - 1)) * -1 + 1
            data = letter + str(number)
            return data
        elif totype == "sgf":
            if withi:
                number = y
            else:
                number = (self.gridwidth - 1) - y
            data = atot[x] + atot[number]
            return data

    def getliberties(self, numpos):
        """Uses GnuGo for finding the number of liberties at a given
           numerical position in the form (x, y)."""
        pos = self.convertpos(numpos, "numpos", "gnugo")
        try:
            return int(self.gtp(f"countlib {pos}"))
        except ValueError:
            print("VALUEERROR", pos)

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
        b = lambda pos: self.playhere("B", pos)
        w = lambda pos: self.playhere("W", pos)
        list(map(b, self.gtp("list_stones black").split()))
        list(map(w, self.gtp("list_stones white").split()))
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
        self.gtp(f"level {level}")

    def time(self, main_time, byo_yomi_time, byo_yomi_stones):
        self.gtp(f"time_settings {main_time} {byo_yomi_time} {byo_yomi_stones}")

    def playhere(self, playercolor, pos):
        """Usually called in connection with GnuGo making a move"""
        if "illegal move" in pos:
            print(f"Illegal move: {pos}")
            return

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
        try:
            black_captures_response = self.gtp("captures black")
            white_captures_response = self.gtp("captures white")
            b = int(black_captures_response.split()[-1])
            w = int(white_captures_response.split()[-1])
        except ValueError as e:
            print(f"Error: could not get captures black or captures white from the GTP engine: {e}")
            print(f"Black captures response: {black_captures_response}")
            print(f"White captures response: {white_captures_response}")
            return
        if b != self._b_captures:
            self.gnugo2pixels()
            self._b_captures = b
        elif w != self._w_captures:
            self.gnugo2pixels()
            self._w_captures = w

    def saymove(self, color):
        letter = self._graphics.letters[self._x]
        number = (self._y * -1) + self.BOARD
        pos = letter + str(number)
        if color == "B":
            return self.gtp(f"play black {pos}")
        else:
            return self.gtp(f"play white {pos}")

    def togglecolor(self, r, g, b):
        self.setFgColor(int(r), int(g), int(b), 0)
        self.toggle()

    def toggle(self):
        """ Toggles the selected pixel on and off """
        if self.pixelHere():
            if self.getHere() == self.getFgColor():
                self.removePixel()
                self.pixels2gnugo()
            else:
                self.plot()
                self.pixels2gnugo()
        else:
            self.plot()

    def left(self):
        """ Moves the imagecursor to the left """
        self._x -= 1
        if self._x < 0:
            self._x = self._xmax
        self.cursorMoved()

    def right(self):
        """ Moves the imagecursor to the right """
        self._x += 1
        if self._x > self._xmax:
            self._x = 0
        self.cursorMoved()

    def up(self):
        """ Moves the imagecursor up """
        self._y -= 1
        if self._y < 0:
            self._y = self._ymax
        self.cursorMoved()

    def down(self):
        """ Moves the imagecursor down """
        self._y += 1
        if self._y > self._ymax:
            self._y = 0
        self.cursorMoved()
