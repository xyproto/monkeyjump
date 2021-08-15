#!/usr/bin/python
#-*-coding:utf-8-*-
#vim: set enc=utf8:
#
# author:   Alexander Rødseth <rodseth@gmail.com>
# date:     May 2005
#

import pygame
from pygame.locals import *
import math
from functools import reduce


class Analyzer(object):

    def __init__(self, goboard):
        self.goboard = goboard 
        self._blackwhiteempty()
        self._blackliberties = {}
        self._whiteliberties = {}

    def has_space(self, pos):
        """Checks if a position is uncluttered."""
        if pos in self.black:
            return False
        elif pos in self.white:
            return False
        for x in [1, -1]:
            for y in [1, -1]:
                if (pos[0] + x, pos[1] + y) in self.black:
                    return False
                elif (pos[0] + x, pos[1] + y) in self.white:
                    return False
        return True

    def find_friends(self, pos):
        """Find the friends-score"""
        friends = 0
        for x in [1, -1, 2, -2, 3, -3, 4, -4]:
            for y in [1, -1, 2, -2, 3, -3, 4, -4]:
                checkpos = (pos[0] + x, pos[1] + y)
                if checkpos in self.black:
                    #distance = math.sqrt(abs(pos[0] - x) ** 2 + abs(pos[1] - y) ** 2)
                    #distance = abs(x) + abs(y)
                    #friends += 10 - (distance / 6.0)
                    #friends += (((distance * -3.0) + 3) * (self._blackliberties[checkpos] / 10.0))
                    if (abs(x) > 2) or (abs(y) > 2):
                        friends += 0.5
                    else:
                        friends += 1
                    
        return friends

    def find_enemies(self, pos):
        """Find the number of enemies."""
        enemies = 0
        for x in [1, -1, 2, -2, 3, -3, 4, -4]:
            for y in [1, -1, 2, -2, 3, -3, 4, -4]:
                checkpos = (pos[0] + x, pos[1] + y)
                if checkpos in self.white:
                    #distance = math.sqrt(abs(pos[0] - x) ** 2 + abs(pos[1] - y) ** 2)
                    #distance = abs(x) + abs(y)
                    #enemies += 10 - (distance / 6.0)
                    #enemies += (((distance * -3.0) + 3) * (self._whiteliberties[checkpos] / 10.0))
                    if (abs(x) > 2) or (abs(y) > 2):
                        enemies += 0.5
                    else:
                        enemies += 1
        return enemies

    def _blackwhiteempty(self):
        """Helper function for getting hold of the black, white and empty fields on a goboard."""
        pixels = self.goboard.pixels
        # Get all coordinates for the black stones
        self.black = [poscolor[0] for poscolor in list(pixels.items()) if poscolor[1][0] == 0]
        # Get all coordinates for the white stones
        self.white = [poscolor[0] for poscolor in list(pixels.items()) if poscolor[1][0] == 255]
        # Get all coordinates for the empty points
        self.empty = []
        for x in range(self.goboard.gridwidth):
            for y in range(self.goboard.gridwidth):
                if (x, y) not in pixels:
                    self.empty.append((x, y))

    def blurmore(self, surface, repeat=3, exclude=[], divnum=5.0):
        """blur4 a surface, several times, until the best point is found.
           repeat is the maximum number of iterations."""

        #origbias = 2.1
        #cornerbias = 3.2
        #spacebias = 5.0
        #friendbias = 0.7
        #enemybias = 0.7

        #origbias = 2.1
        #cornerbias = 2.9
        #spacebias = 9.0
        #friendbias = 2.0
        #enemybias = 1.0

        #origbias = 2.5
        #cornerbias = 2.7
        #spacebias = 8.0
        #friendbias = 3.0
        #enemybias = 2.0

#        origbias = 2.4
#        cornerbias = 3.0
#        spacebias = 7.9
#        friendbias = 1.1
#        enemybias = 0.9
#        threshold = 580

#        origbias = 2.4
#        cornerbias = 3.7
#        spacebias = 7.9
#        friendbias = 1.1
#        enemybias = 0.9
#        threshold = 585

        origbias = 2.4
        cornerbias = 1.0
        spacebias = 7.9
        friendbias = 1.5
        enemybias = 0.9
        threshold = 590
        sidebias = 20.0

        gpos = None
        oldgpos = None
        bestcount = 0
        for i in range(repeat):
            surface = self.blur4(surface, exclude, divnum)
            if gpos:
                oldgpos = gpos
            greenest = 0
            gpos = None
            oldbestcount = bestcount
            bestcount = 0
            w = self.goboard.gridwidth
            #niceorder = reduce(lambda x, y: x + y, zip(range(w)[-1:0:-2], range(w)[::2]))
            #niceorder = reduce(lambda x, y: x + y, zip(range(w)[:w/2], range(w)[-1:(w/2)-1:-1]))[::-1]
            #niceorder = reduce(lambda x, y: x + y, zip(range(w)[-1:(w/2)-1:-1], range(w)[:w/2]))
            #niceorder = reduce(lambda x, y: x + y, zip(range(w)[:w/2], range(w)[-1:(w/2)-1:-1]))[::-1]
            #niceorder = reduce(lambda x, y: x + y, zip(range(w)[-1:(w/2)-1:-1], range(w)[:w/2]))[::-1]
            niceorder = reduce(lambda x, y: x + y, list(zip(list(range(w))[:w/2], list(range(w))[-1:(w/2)-1:-1])))
#            log = open("biaslog.txt", "w")
            for x in niceorder:
                for y in niceorder:
#                    log.write("point: " + str((x, y)) + "\n")
                    color = surface.get_at((x, y))[0:3]
#                    log.write("\tcolor: " + str(color) + "\n")
                    g = (255 - (color[0] * -1.0) * 0.1 + color[1] * 0.8 + (255 - (color[2] * -1.0) * 0.1)) / 3.0
                    g *= origbias
#                    log.write("\toriginal g: " + str(g) + "\n")
                    if cornerbias:
                        c = w/2
                        # h² = k² + k²
                        distance = math.sqrt(abs(c - x) ** 2 + abs(c - y) ** 2)
                        g += distance * cornerbias
#                    log.write("\tg after cornerbias: " + str(g) + "\n")
                    if sidebias:
                        c = w/2
                        horiz = abs(c - x) / float(c)
                        verti = abs(c - y) / float(c)
                        g += max(horiz, verti) * sidebias
                    if spacebias:
                        if self.has_space((x, y)):
                            g += spacebias
                        else:
                            g -= spacebias
#                    log.write("\tg after spacebias: " + str(g) + "\n")
                    if friendbias:
                        friends = self.find_friends((x, y))
                        if friends == 0:
                            g -= friendbias * 5
                        elif friends == 1:
                            g += friendbias * 5
                        elif friends == 2:
                            g += friendbias * 2
                        elif friends == 3:
                            g += friendbias
                        elif friends > 3:
                            g -= friendbias * friends
#                        log.write("\tg after friendbias: " + str(g) + "\n\n")
                    if enemybias:
                        enemies = self.find_enemies((x, y))
                        g -= enemybias ** enemies
#                        log.write("\tg after enemybias: " + str(g) + "\n\n")
                    if g > greenest:
                        greenest = g
                        gpos = (x, y)
                    elif g == greenest:
                        bestcount += 1
            value = greenest / (bestcount + 1)
            print("gpos", gpos, "value", value)

#            if ((value < 500) or ((oldbestcount < bestcount) or (greenest < threshold))) and oldgpos:
            if value < threshold:
                if not oldgpos:
                    continue
                gpos = oldgpos
                bestcount = oldbestcount
                print("Finished!")
                print("GPOS", gpos, "VALUE", greenest, "BESTCOUNT", bestcount)
                surface.set_at(gpos, (255, 255, 255))
        #        log.write("\n\nSELECTED: " + str(gpos) + "\n\n")
                return surface, gpos
        # If the loop finished without returning, return None as move
        # Not anymore
        return surface, gpos

    def blur4(self, surface, exclude=[], divnum=5.0):
        """ blur4(surface, except, divnum=5.0) -> surface
	  * blurrer pixlene i surface, ved å ta gjennomsnittet av denne, N, W, E, S pixlene
	  * der except er en liste over koordinater som ikke skal leses eller skrives til
	  * der divnum er hva man skal dele på når man tar gjennomsnittet av steinene
        """
        w = self.goboard.gridwidth
        newsurface = pygame.Surface((w, w))
        for x in range(w):
            for y in range(w):
                if (x, y) in exclude:
                    continue
                color = surface.get_at((x, y))
                r = 0
                g = 0
                b = 0
                for pos in [(x, y), (x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]:
                    if pos in exclude:
                        continue
                    elif pos[0] < 0:
                        continue
                    elif pos[0] >= w:
                        continue
                    elif pos[1] < 0:
                        continue
                    elif pos[1] >= w:
                        continue
                    tr, tg, tb, ta = surface.get_at(pos)
                    r += tr
                    g += tg
                    b += tb
                r /= divnum
                g /= divnum
                b /= divnum
                try:
                    newsurface.set_at((x, y), (int(r), int(g), int(b)))
                except TypeError:
                    print("set_at", (x, y), (r, g, b))
        return newsurface

    def medianblur4(self, surface, exclude, divnum=4.0):
        """ medianblur4(surface, except, divnum=4.0) -> surface
	  * blurrer pixlene i surface, ved å ta medianen av N, W, E, S pixlene
	  * der except er en liste over koordinater som ikke skal leses eller skrives til
	  * der divnum er hva man skal dele på når man tar gjennomsnittet av steinene
        """
        return surface

    def combine(self, redsurface, greensurface, bluesurface):
        """ combine(redsurface, greensurface, bluesurface) -> surface
	  * der en surface godt kan være None
        """
        w = self.goboard.gridwidth
        surface = pygame.Surface((w, w))
        for x in range(w):
            for y in range(w):
                r = redsurface.get_at((x, y))[0]
                g = greensurface.get_at((x, y))[1]
                b = bluesurface.get_at((x, y))[2]
                surface.set_at((x, y), (r, g, b))
        return surface

    def blackliberties(self):
        """blackliberties(goboard) -> surface, except
	  * finner svarte liberties
	  * lager et bilde av svarte liberties
	  * returnerer en liste over hvite koordinater
        """
        # Create a dictionary with numpos-coordinates as key, and liberties as value
        self._blackliberties = {}
        for numpos in self.black:
            #print "numpos", numpos
            self._blackliberties[numpos] = self.goboard.getliberties(numpos)
        #print blackliberties
        try:
            maxlib = max(self._blackliberties.values())
        except ValueError:
            maxlib = 1
        #print "Maximum black liberties found"

        surface = pygame.Surface((self.goboard.gridwidth, self.goboard.gridwidth))

        # Create the image of the black liberties
        for numpos, liberties in list(self._blackliberties.items()):
            color = (int((liberties / float(maxlib)) * 255.0), 0, 0)
            #print "color", color
            surface.set_at(numpos, color)

        # Exclude the white positions
        exclude = self.white[:]

        return (surface, exclude)

    def whiteliberties(self):
        """whiteliberties(goboard) -> surface, except
	  * finner hvite liberties
	  * lager et bilde av hvite liberties
	  * returnerer en liste over svarte koordinater
        """
        # Create a dictionary with numpos-coordinates as key, and liberties as value
        self._whiteliberties = {}
        for numpos in self.white:
            #print "numpos", numpos
            self._whiteliberties[numpos] = self.goboard.getliberties(numpos)
        #print whiteliberties
        try:
            maxlib = max(self._whiteliberties.values())
        except ValueError:
            maxlib = 1
        #print "Maximum white liberties found"

        surface = pygame.Surface((self.goboard.gridwidth, self.goboard.gridwidth))

        # Create the image of the black liberties
        for numpos, liberties in list(self._whiteliberties.items()):
            color = (0, 0, int((liberties / float(maxlib)) * 255.0))
            #print "color", color
            surface.set_at(numpos, color)

        # Exclude the black positions
        exclude = self.black[:]

        return (surface, exclude)

    def voidliberties(self):
        """ voidliberties(goboard) -> surface, except
	  * finner liberties for de tomme punktene
	  * lager et bilde av voidliberties
	  * returnerer en liste over svarte og hvite koordinater
        """
        # Are the edges counted as less liberties for the empty spaces?
        edgy = True
        # Create a dictionary with numpos-coordinates as key, and liberties as value
        voidliberties = {}
        for numpos in self.empty:
            #print "numpos", numpos
            x, y = numpos
            liberties = 4
            for list in [self.black, self.white]:
                for pos in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]:
                    if pos[0] < 0:
                        if edgy:
                            liberties -= 1
                    elif pos[1] < 0:
                        if edgy:
                            liberties -= 1
                    elif pos[0] >= self.goboard.gridwidth:
                        if edgy:
                            liberties -= 1
                    elif pos[1] >= self.goboard.gridwidth:
                        if edgy:
                            liberties -= 1
                    elif pos in list:
                        liberties -= 1
            voidliberties[numpos] = liberties
        #print voidliberties
        maxlib = 4 # an extra to avoid black colors
        #print "Maximum empty liberties found"

        surface = pygame.Surface((self.goboard.gridwidth, self.goboard.gridwidth))

        # Create the image of the black liberties
        for numpos, liberties in list(voidliberties.items()):
            color = (0, int((liberties / float(maxlib)) * 255.0), 0)
            #print "color", color
            try:
                surface.set_at(numpos, color)
            except TypeError:
                print("TYPEERROR", "color", color)

        # Exclude the black positions
        exclude = self.black[:]

        return (surface, exclude)
