# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import argparse
import logging
import os
import re

# fsutils, , misc filesystem utils, internal
from .lib import fsutils
# validate, , validate things, internal
from .lib import validate


def addOptions(parser):
    parser.add_argument('component',
        help='Name of the dependency to remove'
    )

def execCommand(args, following_args):
    err = validate.componentNameValidationError(args.component)
    if err:
        logging.error(err)
        return 1
    c = validate.currentDirectoryModule()
    if not c:
        return 1
    path = os.path.join(c.modulesPath(), args.component)
    if fsutils.isLink(path):
        fsutils.rmF(path)
    else:
        fsutils.rmRf(path)

