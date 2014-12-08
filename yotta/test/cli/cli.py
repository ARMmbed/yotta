#!/usr/bin/env python
# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import sys
import subprocess
import os

def run(arguments, cwd='.'):
    yottadir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..')
    runyotta = [
        sys.executable,
        '-c',
        "import sys; sys.path.insert(0, '%s'); import yotta; yotta.main()" % yottadir
    ]
    child = subprocess.Popen(
          args = runyotta + arguments,
           cwd = cwd,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
         stdin = subprocess.PIPE
    )
    out, err = child.communicate()
    return out.decode('utf-8'), err.decode('utf-8'), child.returncode



