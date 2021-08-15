#!/usr/bin/python
#-*-coding:utf-8-*-
#vim: set enc=utf8:
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

#
# This function interpolates the r,g,b-values in a dictionary-palette
# from begin to end. Can also be used from end to begin, after my knowledge
#
def rgbi( rgbs, begin, end ):

	# Initialize the color-values
	red_begin = rgbs[begin][0]
	red_end = rgbs[end][0]
	green_begin = rgbs[begin][1]
	green_end = rgbs[end][1]	
	blue_begin = rgbs[begin][2]
	blue_end = rgbs[end][2]

	# Calculate the deltas
	colorspan = fabs(end - begin)
	inci = ((end - begin) / colorspan)
	incr = ((red_end - red_begin) / colorspan)
	incg = ((green_end - green_begin) / colorspan)
	incb = ((blue_end - blue_begin) / colorspan)
		
	# Initialize the variables
	r = red_begin
	g = green_begin
	b = blue_begin

	# Are we going up or down?
	if end > begin:
		thelist = range(begin, end, int(inci))
	else:
		thelist = range(end, begin, int(inci))

	# Iterate
	for i in thelist:
		rgbs[i] = ( int(r), int(g), int(b) )
		r += incr
		g += incg
		b += incb

#
# This function creates the default BIP-palette
#
def create_defpal():
	# 0 til 3
	defpal = {0: (0,0,0), 1: (20,20,20), 2: (34,34,34), 3: (0,0,0) }
	# 3 til 31
	defpal[31] = (63,63,63)
	rgbi( defpal, 3, 31 )
	# 32 til 63
	defpal[32] = (63,63,63)
	defpal[63] = (63,0,0)
	rgbi( defpal, 32, 63 )
	# 64 til 95
	defpal[64] = (63,0,0)
	defpal[95] = (63,63,0)
	rgbi( defpal, 64, 95 )	
	# 96 til 127
	defpal[96] = (63,63,0)
	defpal[127] = (0,32,32)
	rgbi( defpal, 96, 127 )
	# 128 til 159
	defpal[128] = (0,32,32)
	defpal[159] = (20,20,63)
	rgbi( defpal, 128, 159 )
	# 160 til 191
	defpal[160] = (20,20,63)
	defpal[191] = (63,63,50)
	rgbi( defpal, 160, 191 )	
	# 192 til 223
	defpal[192] = (63,63,50)
	defpal[223] = (32,0,0)
	rgbi( defpal, 192, 223 )		
	# 224 til 239
	defpal[224] = (32,0,0)
	defpal[239] = (52,52,63)
	rgbi( defpal, 224, 239 )			
	# 240 til 255
	defpal[240] = (52,52,63)
	defpal[255] = (0,0,0)
	rgbi( defpal, 240, 255 )
	# multiply each color with 4 (standard pcx-pal-stuff)
	for i in range(0,256):
		rgb = defpal[i]
		defpal[i] = (rgb[0]<<2,rgb[1]<<2,rgb[2]<<2)
	return defpal

#
# This funcion basically loads a bip-image-file
# It takes a filename and returns a converted surface (hopefully)
# A BIP-file is either an image (always 32x32 8bpp), a palette or both
# Since it only returns surfaces, palettes are returned as a surface
# with all the 256 colors, plotted from the topleft corner.
#
def load_bip( filename ):
	
	def bip_error( comment, filename=filename ):
		print('Error in BIP!')
		print('Filename: ',filename)
		print(comment)
		raise SystemExit
		
	bip = pygame.Surface( (32, 32) )#.convert()
	# Åpner
	f = open(filename, 'rb')
	# Leser
	s = f.read()
	# Lukker
	f.close()
	# Er det virkelig en bip?
	if not s[0] == 'B':
		bip_error( filename, "Not a BIP (first byte is not a 'B')" )
	# s[1] og s[2] er ver og ver_string
	# s[3] og s[4] er animdelay (ubrukt)
	# Hva slags bip-fil har vi med å gjøre?
	biptype = ord(s[5])
	if biptype == 1:
		# - image only -
		if os.path.getsize( filename ) < (6 + 32*32):
			bip_error( filename, "To small" )
		defpal = create_defpal()
		plass = 6
		for y in range(0,32):
			for x in range(0,32):
				bip.set_at( (x,y), defpal[ord(s[plass])] )
				plass += 1
	elif biptype == 2:
		# - palette only -
		if os.path.getsize( filename ) < (6 + 256*3):
			bip_error( filename, "To small" )
		# Load the palette
		plass = 6
		bippal = []		
		for cnum in range(0,256):
			bippal.append( (ord(s[plass])<<2, ord(s[plass+1])<<2, ord(s[plass+2])<<2) )
			plass += 3
		# Create a surface based on the palette
		i = 0
		try:
			for y in range(0,32):
				for x in range(0,32):
					bip.set_at( (x,y), bippal[i] )
					i += 1
		except IndexError:
			pass			
	elif biptype == 3:
		# - image and palette -
		if os.path.getsize( filename ) < (6 + 32*32 + 256*3):
			bip_error( filename, "To small" )
		plass = 6+(32*32)
		bippal = []		
		for cnum in range(0,256):
			bippal.append( (ord(s[plass])<<2, ord(s[plass+1])<<2, ord(s[plass+2])<<2) )
			plass += 3
		plass = 6
		for y in range(0,32):
			for x in range(0,32):
				bip.set_at( (x,y), bippal[ord(s[plass])] )
				plass += 1
	else:
		bip_error( filename, "Unknown BIP-type (byte 5)" )
	return bip

#
# This funcion basically loads a bim-image-file
# It takes a filename and returns a converted surface (hopefully)
# A BIM-file is always an image (32x32 8bpp)
#
def load_bim( filename ):
	bim = pygame.Surface( (32, 32) )#.convert()
	# Åpner
	f = open(filename, 'rb')
	# Leser
	s = f.read()
	# Lukker
	f.close()
	# Er det virkelig en bim?
	if os.path.getsize( filename ) < (32*32):
		print('Error with BIM!')
		print('Filename: ', filename)
		print('To small!')
		raise SystemExit
	defpal = create_defpal()
	plass = 0
	for y in range(0,32):
		for x in range(0,32):
			bim.set_at( (x,y), defpal[ord(s[plass])] )
			plass += 1
	return bim
	
