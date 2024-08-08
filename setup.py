#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from setuptools import setup

def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname), encoding='utf-8') as f:
        return f.read()

setup(
    name="monkeyjump",
    version="1.0.0",
    author="Alexander F. Rødseth",
    author_email="rodseth@gmail.com",
    description="Minimalistic GUI with keybindings for GnuGo and other GTP applications.",
    license="GPL2",
    keywords="go gnugo pygame python game gtp board",
    url="https://github.com/xyproto/monkeyjump",
    packages=['burnlib'],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Games/Entertainment/Board Games",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires='>=3.12',
)
