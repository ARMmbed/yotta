# standard library modules, , ,
import argparse
import logging
import os
import re

# Component, , represents an installed component, internal
from lib import component
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
    c = component.Component(os.getcwd())
    if not c:
        logging.debug(str(c.error))
        logging.error('The current directory does not contain a valid component.')
        return 1
    fsutils.rmF(os.path.join(c.modulesPath(), args.component))

