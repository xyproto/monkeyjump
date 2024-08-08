#!/usr/bin/env python3

import subprocess


def popen2(cmd):
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=True,
    )
    return process.stdin, process.stdout
