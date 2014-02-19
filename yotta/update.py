# standard library modules, , ,
import argparse
import logging
import os

# Component, , represents an installed component, internal
from lib import component


def addOptions(parser):
    parser.add_argument('component', default=None, nargs='?',
        help='If specified, update (and if necessary install) this component '+
             'instead of updating the dependencies of the current component.'
    )


def execCommand(args):
    if args.component is None:
        updateDeps(args)
    else:
        updateComponent(args)


def updateDeps(args):
    c = component.Component(os.getcwd())
    if not c:
        logging.debug(str(c.error))
        logging.error('The current directory does not contain a valid component.')
        return 1
    
    components, errors = c.satisfyDependenciesRecursive(update_installed=True)
    for error in errors:
        logging.error(error)

def updateComponent(args):
    raise NotImplementedError

