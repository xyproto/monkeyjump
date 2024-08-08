#!/usr/bin/env python3
# -*-coding:utf-8-*-
# vim: set enc=utf8:
#
# author:   Alexander Rødseth <rodseth@gmail.com>
# date:     May 2004
#
# todo: palett-pixlene kan dobles
#
# bip 
#
# This is a small library for loading a strange gfx-format belonging to
# a drawing-program I've created in the past (Burn)
#
# Alexander Rodseth
# int19h@online.no
#
# 1 mar 2002
# Added load_bip, rgbi, create_defpal and load_all_bip
#

# Imports
import pygame
import os
from fnmatch import filter
from math import fabs

# Functions

def rgbi(rgbs, begin, end):
    """ This function interpolates the r,g,b-values in a dictionary-palette
    from begin to end. Can also be used from end to begin, after my knowledge
    """

    red_begin = rgbs[begin][0]
    red_end = rgbs[end][0]
    green_begin = rgbs[begin][1]
    green_end = rgbs[end][1]
    blue_begin = rgbs[begin][2]
    blue_end = rgbs[end][2]

    colorspan = fabs(end - begin)
    inci = ((end - begin) / colorspan)
    incr = ((red_end - red_begin) / colorspan)
    incg = ((green_end - green_begin) / colorspan)
    incb = ((blue_end - blue_begin) / colorspan)

    r = red_begin
    g = green_begin
    b = blue_begin

    if end > begin:
        thelist = range(begin, end, int(inci))
    else:
        thelist = range(end, begin, int(inci))

    for i in thelist:
        rgbs[i] = (int(r), int(g), int(b))
        r += incr
        g += incg
        b += incb

def create_defpal():
    """ This function creates the default BIP-palette """
    defpal = {0: (0,0,0), 1: (20,20,20), 2: (34,34,34), 3: (0,0,0)}
    defpal[31] = (63,63,63)
    rgbi(defpal, 3, 31)
    defpal[32] = (63,63,63)
    defpal[63] = (63,0,0)
    rgbi(defpal, 32, 63)
    defpal[64] = (63,0,0)
    defpal[95] = (63,63,0)
    rgbi(defpal, 64, 95)    
    defpal[96] = (63,63,0)
    defpal[127] = (0,32,32)
    rgbi(defpal, 96, 127)
    defpal[128] = (0,32,32)
    defpal[159] = (20,20,63)
    rgbi(defpal, 128, 159)
    defpal[160] = (20,20,63)
    defpal[191] = (63,63,50)
    rgbi(defpal, 160, 191)    
    defpal[192] = (63,63,50)
    defpal[223] = (32,0,0)
    rgbi(defpal, 192, 223)        
    defpal[224] = (32,0,0)
    defpal[239] = (52,52,63)
    rgbi(defpal, 224, 239)            
    defpal[240] = (52,52,63)
    defpal[255] = (0,0,0)
    rgbi(defpal, 240, 255)
    for i in range(0,256):
        rgb = defpal[i]
        defpal[i] = (rgb[0]<<2,rgb[1]<<2,rgb[2]<<2)
    return defpal

def load_bip(filename):
    """ This function basically loads a bip-image-file
    It takes a filename and returns a converted surface (hopefully)
    A BIP-file is either an image (always 32x32 8bpp), a palette or both
    Since it only returns surfaces, palettes are returned as a surface
    with all the 256 colors, plotted from the top-left corner.
    """
    
    def bip_error(comment, filename=filename):
        print('Error in BIP!')
        print('Filename:', filename)
        print(comment)
        raise SystemExit
    
    bip = pygame.Surface((32, 32))
    with open(filename, 'rb') as f:
        s = f.read()
    if s[0] != ord('B'):
        bip_error(filename, "Not a BIP (first byte is not a 'B')")
    biptype = s[5]
    if biptype == 1:
        if os.path.getsize(filename) < (6 + 32*32):
            bip_error(filename, "Too small")
        defpal = create_defpal()
        plass = 6
        for y in range(32):
            for x in range(32):
                bip.set_at((x,y), defpal[s[plass]])
                plass += 1
    elif biptype == 2:
        if os.path.getsize(filename) < (6 + 256*3):
            bip_error(filename, "Too small")
        plass = 6
        bippal = []        
        for cnum in range(256):
            bippal.append((s[plass]<<2, s[plass+1]<<2, s[plass+2]<<2))
            plass += 3
        i = 0
        try:
            for y in range(32):
                for x in range(32):
                    bip.set_at((x,y), bippal[i])
                    i += 1
        except IndexError:
            pass            
    elif biptype == 3:
        if os.path.getsize(filename) < (6 + 32*32 + 256*3):
            bip_error(filename, "Too small")
        plass = 6+(32*32)
        bippal = []        
        for cnum in range(256):
            bippal.append((s[plass]<<2, s[plass+1]<<2, s[plass+2]<<2))
            plass += 3
        plass = 6
        for y in range(32):
            for x in range(32):
                bip.set_at((x,y), bippal[s[plass]])
                plass += 1
    else:
        bip_error(filename, "Unknown BIP-type (byte 5)")
    return bip

def load_bim(filename):
    """ This function basically loads a bim-image-file
    It takes a filename and returns a converted surface (hopefully)
    A BIM-file is always an image (32x32 8bpp)
    """
    
    bim = pygame.Surface((32, 32))
    with open(filename, 'rb') as f:
        s = f.read()
    if os.path.getsize(filename) < (32*32):
        print('Error with BIM!')
        print('Filename:', filename)
        print('Too small!')
        raise SystemExit
    defpal = create_defpal()
    plass = 0
    for y in range(32):
        for x in range(32):
            bim.set_at((x,y), defpal[s[plass]])
            plass += 1
    return bim
