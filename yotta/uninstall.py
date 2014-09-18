# standard library modules, , ,
import argparse
import logging
import os
import re

# fsutils, , misc filesystem utils, internal
from lib import fsutils
# validate, , validate things, internal
from lib import validate


def addOptions(parser):
    parser.add_argument('component',
        help='Name of the dependency to remove'
    )

def execCommand(args):
    err = validate.componentNameValidationError(args.component)
    if err:
        logger.error(err)
        return 1
    c = validate.currentDirectoryModule()
    if not c:
        return 1
    fsutils.rmF(os.path.join(c.modulesPath(), args.component))

