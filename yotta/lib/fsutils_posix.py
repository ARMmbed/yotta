# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import os

def isLink(path):
    return os.path.islink(path)

def tryReadLink(path):
    try:
        return os.readlink(path)
    except OSError as e:
        return None

def _symlink(source, link_name):
    os.symlink(source, link_name)

def realpath(path):
    return os.path.realpath(path)
