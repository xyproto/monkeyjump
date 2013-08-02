#!/usr/bin/python
#-*-coding:utf-8-*-
#vim: set enc=utf8:
#
# author:   Alexander Rødseth <rodseth@gmail.com>
# date:     July 2004
#

# Common utilities
import os.path
import sys

def addpath(filename):
    # Find out where we are
    dirname = os.path.dirname(os.path.abspath(os.path.join(os.path.curdir, sys.argv[0])))
    # Join the path with the relative filename and return
    return os.path.join(dirname, filename)
