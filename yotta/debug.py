# standard library modules, , ,
import os
import logging

# Component, , represents an installed component, internal
from lib import component
# CMakeGen, , generate build files, internal
from lib import cmakegen


def addOptions(parser):
    parser.add_argument('program', default=None,
        help='name of the program to be debugged'
    )


def execCommand(args):
    cwd = os.getcwd()
    c = component.Component(cwd)
    if not c:
        logging.debug(str(c.error))
        logging.error('The current directory does not contain a valid component.')
        return 1

    target, errors = c.satisfyTarget(args.target)
    if errors:
        for error in errors:
            logging.error(error)
        return 1

    builddir = os.path.join(cwd, 'build', target.getName())
    
    # !!! FIXME: the program should be specified by the description of the
    # current project (or a default value for the program should)
    errcode = None
    for error in target.debug(builddir, args.program):
        logging.error(error)
        errcode = 1

    return errcode


