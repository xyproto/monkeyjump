#!/usr/bin/env python3

from pathlib import Path


def addpath(filename):
    # Find the absolute path of the current working directory
    current_dir = Path.cwd().resolve()
    # Join the path with the relative filename and return
    return current_dir / filename
