#!/usr/bin/python
#-*-coding:utf-8-*-
#vim: set enc=utf8:
#
# author:   Alexander Rødseth <rodseth@gmail.com>
# date:     May 2005
#
# TODO: Use the test-modules that comes with Python and red-green-refactor

from burnlib.goengine import GoGrid
from burnlib.analyze import Analyzer

class TestAll:

    def __init__(self):
        self.g = GoGrid()
        self.testconvert()

    def testconvert(self):
        # (0, 0) er A19!

        # Try converting to and from the same type
        assert("aa" == self.g.convertpos("aa", fromtype="sgf", totype="sgf"))
        assert("mm" == self.g.convertpos("mm", fromtype="sgf", totype="sgf"))
        assert("M7" == self.g.convertpos("M7", fromtype="gnugo", totype="gnugo"))
        assert((7, 8) == self.g.convertpos((7, 8), fromtype="numpos", totype="numpos"))
        
        hasi = True
        try:
            assert("ei" == self.g.convertpos("ei", fromtype="sgf", totype="sgf"))
        except ValueError:
            hasi = False
        if hasi:
            assert(not "convert from sgf to sgf accepts 'i'!")

        # Try other conversions
        assert("C17" == self.g.convertpos((2, 2), fromtype="numpos", totype="gnugo"))
        assert("cr" == self.g.convertpos((2, 2), fromtype="numpos", totype="sgf"))
        assert("C17" == self.g.convertpos("cr", fromtype="sgf", totype="gnugo"))
        assert("C1" == self.g.convertpos("ca", fromtype="sgf", totype="gnugo"))

        print("conversion seems to be working")


if __name__ == "burnlib.teststuff":
    t = TestAll()
