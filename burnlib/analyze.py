#!/usr/bin/env python3

from functools import reduce
from pygame.locals import *
import math
import pygame


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
                    if abs(x) > 2 or abs(y) > 2:
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
                    if abs(x) > 2 or abs(y) > 2:
                        enemies += 0.5
                    else:
                        enemies += 1
        return enemies

    def _blackwhiteempty(self):
        """Helper function for getting hold of the black, white and empty fields on a goboard."""
        pixels = self.goboard.pixels
        self.black = [poscolor[0] for poscolor in pixels.items() if poscolor[1][0] == 0]
        self.white = [
            poscolor[0] for poscolor in pixels.items() if poscolor[1][0] == 255
        ]
        self.empty = []
        for x in range(self.goboard.gridwidth):
            for y in range(self.goboard.gridwidth):
                if (x, y) not in pixels:
                    self.empty.append((x, y))

    def blurmore(self, surface, repeat=3, exclude=[], divnum=5.0):
        """blur4 a surface, several times, until the best point is found.
        repeat is the maximum number of iterations."""

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
            niceorder = reduce(
                lambda x, y: x + y,
                zip(range(w)[: w // 2], range(w)[-1 : (w // 2) - 1 : -1]),
            )

            for x in niceorder:
                for y in niceorder:
                    color = surface.get_at((x, y))[0:3]
                    g = (
                        255
                        - (color[0] * -1.0) * 0.1
                        + color[1] * 0.8
                        + (255 - (color[2] * -1.0) * 0.1)
                    ) / 3.0
                    g *= origbias
                    if cornerbias:
                        c = w / 2
                        distance = math.sqrt(abs(c - x) ** 2 + abs(c - y) ** 2)
                        g += distance * cornerbias
                    if sidebias:
                        c = w / 2
                        horiz = abs(c - x) / float(c)
                        verti = abs(c - y) / float(c)
                        g += max(horiz, verti) * sidebias
                    if spacebias:
                        if self.has_space((x, y)):
                            g += spacebias
                        else:
                            g -= spacebias
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
                    if enemybias:
                        enemies = self.find_enemies((x, y))
                        g -= enemybias**enemies
                    if g > greenest:
                        greenest = g
                        gpos = (x, y)
                    elif g == greenest:
                        bestcount += 1
            value = greenest / (bestcount + 1)
            print("gpos", gpos, "value", value)

            if value < threshold:
                if not oldgpos:
                    continue
                gpos = oldgpos
                bestcount = oldbestcount
                print("Finished!")
                print("GPOS", gpos, "VALUE", greenest, "BESTCOUNT", bestcount)
                surface.set_at(gpos, (255, 255, 255))
                return surface, gpos
        return surface, gpos

    def blur4(self, surface, exclude=[], divnum=5.0):
        """blur4(surface, except, divnum=5.0) -> surface
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

    def combine(self, redsurface, greensurface, bluesurface):
        """combine(redsurface, greensurface, bluesurface) -> surface
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
        self._blackliberties = {}
        for numpos in self.black:
            self._blackliberties[numpos] = self.goboard.getliberties(numpos)
        try:
            maxlib = max(self._blackliberties.values())
        except ValueError:
            maxlib = 1

        surface = pygame.Surface((self.goboard.gridwidth, self.goboard.gridwidth))

        for numpos, liberties in self._blackliberties.items():
            color = (int((liberties / float(maxlib)) * 255.0), 0, 0)
            surface.set_at(numpos, color)

        exclude = self.white[:]

        return (surface, exclude)

    def whiteliberties(self):
        """whiteliberties(goboard) -> surface, except
        * finner hvite liberties
        * lager et bilde av hvite liberties
        * returnerer en liste over svarte koordinater
        """
        self._whiteliberties = {}
        for numpos in self.white:
            self._whiteliberties[numpos] = self.goboard.getliberties(numpos)
        try:
            maxlib = max(self._whiteliberties.values())
        except ValueError:
            maxlib = 1

        surface = pygame.Surface((self.goboard.gridwidth, self.goboard.gridwidth))

        for numpos, liberties in self._whiteliberties.items():
            color = (0, 0, int((liberties / float(maxlib)) * 255.0))
            surface.set_at(numpos, color)

        exclude = self.black[:]

        return (surface, exclude)

    def voidliberties(self):
        """voidliberties(goboard) -> surface, except
        * finner liberties for de tomme punktene
        * lager et bilde av voidliberties
        * returnerer en liste over svarte og hvite koordinater
        """
        edgy = True
        voidliberties = {}
        for numpos in self.empty:
            x, y = numpos
            liberties = 4
            for lst in [self.black, self.white]:
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
                    elif pos in lst:
                        liberties -= 1
            voidliberties[numpos] = liberties

        maxlib = 4

        surface = pygame.Surface((self.goboard.gridwidth, self.goboard.gridwidth))

        for numpos, liberties in voidliberties.items():
            color = (0, int((liberties / float(maxlib)) * 255.0), 0)
            try:
                surface.set_at(numpos, color)
            except TypeError:
                print("TYPEERROR", "color", color)

        exclude = self.black[:]

        return (surface, exclude)
