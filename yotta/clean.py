# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import os

# validate, , validate things, internal
from .lib import validate

# fsutils, , misc filesystem utils, internal
from .lib import fsutils

def addOptions(parser):
    pass

def execCommand(args, following_args):
    c = validate.currentDirectoryModule()
    if not c:
        return 1

    fsutils.rmRf(os.path.join(c.path, 'build'))

