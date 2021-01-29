# -*- coding: utf-8 -*-

import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "monkeyjump",
    version = "0.5",
    author = "Alexander F. Rødseth",
    author_email = "rodseth@gmail.com",
    description = ("Minimalistic GUI with keybindings for GnuGo and other GTP applications."),
    license = "GPL2",
    keywords = "go gnugo pygame python game gtp board",
    url = "https://github.com/xyproto/monkeyjump",
    packages=['burnlib'],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Games",
        "License :: OSI Approved :: GPL 2",
    ],
)
