#!/usr/bin/env python3

# Common utilities
import os.path
import sys


def addpath(filename):
    # Find out where we are
    dirname = os.path.dirname(
        os.path.abspath(os.path.join(os.path.curdir, sys.argv[0]))
    )
    # Join the path with the relative filename and return
    return os.path.join(dirname, filename)
