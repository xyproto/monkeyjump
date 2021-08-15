#!/usr/bin/python
#-*-coding:utf-8-*-
#vim: set enc=utf8:
#
# author:   Alexander Rødseth <rodseth@gmail.com>
# date:     mar 2002
#
# apf
#
# This is a small library for loading a strange gfx-format belonging to
# some graphics-programs I've created earlier. Dispite the wierd format,
# I didn't care to draw all those sprites again... (apf)
#
# The code has quite a few norwegian comments lying around that I haven't
# bothered to translate to english yet... oh well =)
#
# Alexander Rodseth
# int19h@online.no
#
#
# 1 mar 2002
# Added load_all_apf, join_apf and join_images
#
# 28 feb 2002
# Created the basic apf-loading function load_apf
#
#

# Imports

import pygame
import os
from fnmatch import filter

# Constants

#
# Some values used for 4-bit color conversion.
# They should be quite ok, but I'm not sure if they are 100% correct
#
c4bit = [[] * 3] * 16
c4bit[0] = (0,0,0)
c4bit[1] = (0,0,127)
c4bit[2] = (0,127,0)
c4bit[3] = (0,127,127)
c4bit[4] = (127,0,0)
c4bit[5] = (127,0,127)
c4bit[6] = (127,127,0)
c4bit[7] = (127,127,127)
c4bit[8] = (63,63,63)
c4bit[9] = (0,0,255)
c4bit[10] = (0,255,0)
c4bit[11] = (0,255,255)
c4bit[12] = (255,0,0)
c4bit[13] = (255,0,255)
c4bit[14] = (255,255,0)
c4bit[15] = (255,255,255)

# Functions

#
# This function basically loads an apf-image-file
# It takes a filename and returns a converted surface (hopefully)
#
def load_apf( filename, width=16, height=16 ):
	apf = pygame.Surface((width,height))#.convert()
	# Åpne en apf-fil
	f = open(filename)
	# Leser inn hele fila
	s = f.read()
	f.close()
	# Splitter opp alle linjene til en array og fjern de siste blanke
	s = s.rstrip().split('\n')
	# Hvis det finnes noen linje i fila (denne sjekken er egentlig ikke
	# helt nodvendig, men den koster ingen ting
	if len(s) > 0:
		try:
			# For hver linje i s
			for pixel in s:
				# Er linja tom, prov neste
				if pixel == '':
					continue
				# Splitt opp linja i x, y og farge, strip forst
				pixel = pixel.strip().split(',')
				# Plott pixelen med korrekt 4-bit farge, i rgb-format
				color = c4bit[int(pixel[2])]
				apf.set_at((int(pixel[0]),int(pixel[1])),color)
		except IndexError:
			print("Couldn't load",filename)
			print("The size given is ",width,"x",height)
			print("The .apf tried plotting a pixel at (", end=' ')
			print(int(pixel[0]),",",int(pixel[1]),")!")
			raise SystemExit
	# !!Burde forandre i henhold til width og height!!
	return apf

#
# This function takes four filenames, loads the apf-files and joins
# the resulting images into a new surface, twice the width and height
#
def join_apf( fn1, fn2, fn3, fn4, dirname='apf', width=16, height=16 ):
	# Lag en surface som har dobbel hoyde og bredde
	joined = pygame.Surface( (width<<1, height<<1) )#.convert()
	apf = load_apf( os.path.join( dirname, fn1 ), width, height )
	joined.blit( apf, (0, 0) )
	apf = load_apf( os.path.join( dirname, fn2 ), width, height )
	joined.blit( apf, (width, 0) )
	apf = load_apf( os.path.join( dirname, fn3 ), width, height )
	joined.blit( apf, (0, height) )
	apf = load_apf( os.path.join( dirname, fn4 ), width, height )
	joined.blit( apf, (width, height) )
	return joined

#
# This function takes a list of surfaces and create one big surface
# according to the "right" and "bottom" parameters
#
def join_images( list, right, bottom, width=32, height=32 ):
	# Lag en surface som er stor nok
	alle = pygame.Surface( (right, bottom) )#.convert()
	tell = 0
	# Try-except er en grei måte å "breake" ut av en nested for-loop
	try:
		for y in range( 0, bottom, height ):
			for x in range( 0, right, width ):
				myrect = alle.blit( list[tell], (x,y) )
				tell += 1
	except IndexError:
		pass
	return alle
