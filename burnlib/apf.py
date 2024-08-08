#!/usr/bin/env python3

# Imports
import pygame
import os
from fnmatch import filter

# Constants
# Some values used for 4-bit color conversion.
# They should be quite ok, but I'm not sure if they are 100% correct
c4bit = [None] * 16
c4bit[0] = (0, 0, 0)
c4bit[1] = (0, 0, 127)
c4bit[2] = (0, 127, 0)
c4bit[3] = (0, 127, 127)
c4bit[4] = (127, 0, 0)
c4bit[5] = (127, 0, 127)
c4bit[6] = (127, 127, 0)
c4bit[7] = (127, 127, 127)
c4bit[8] = (63, 63, 63)
c4bit[9] = (0, 0, 255)
c4bit[10] = (0, 255, 0)
c4bit[11] = (0, 255, 255)
c4bit[12] = (255, 0, 0)
c4bit[13] = (255, 0, 255)
c4bit[14] = (255, 255, 0)
c4bit[15] = (255, 255, 255)


# Functions
def load_apf(filename, width=16, height=16):
    apf = pygame.Surface((width, height))
    # Open an apf file
    with open(filename) as f:
        # Read the entire file
        s = f.read()
    # Split all lines into an array and remove the last blank
    s = s.rstrip().split("\n")
    if len(s) > 0:
        try:
            # For each line in s
            for pixel in s:
                if pixel == "":
                    continue
                # Split the line into x, y and color, strip first
                pixel = pixel.strip().split(",")
                # Plot the pixel with the correct 4-bit color, in RGB format
                color = c4bit[int(pixel[2])]
                apf.set_at((int(pixel[0]), int(pixel[1])), color)
        except IndexError:
            print(f"Couldn't load {filename}")
            print(f"The size given is {width}x{height}")
            print(
                f"The .apf tried plotting a pixel at ({int(pixel[0])}, {int(pixel[1])})!"
            )
            raise SystemExit
    return apf


def join_apf(fn1, fn2, fn3, fn4, dirname="apf", width=16, height=16):
    joined = pygame.Surface((width * 2, height * 2))
    apf = load_apf(os.path.join(dirname, fn1), width, height)
    joined.blit(apf, (0, 0))
    apf = load_apf(os.path.join(dirname, fn2), width, height)
    joined.blit(apf, (width, 0))
    apf = load_apf(os.path.join(dirname, fn3), width, height)
    joined.blit(apf, (0, height))
    apf = load_apf(os.path.join(dirname, fn4), width, height)
    joined.blit(apf, (width, height))
    return joined


def join_images(lst, right, bottom, width=32, height=32):
    alle = pygame.Surface((right, bottom))
    tell = 0
    try:
        for y in range(0, bottom, height):
            for x in range(0, right, width):
                myrect = alle.blit(lst[tell], (x, y))
                tell += 1
    except IndexError:
        pass
    return alle
