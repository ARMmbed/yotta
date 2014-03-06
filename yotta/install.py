# standard library modules, , ,
import argparse
import logging
import os

# Component, , represents an installed component, internal
from lib import component
# access, , get components, internal
from lib import access

# folders, , get places to install things, internal
from . import folders

def addOptions(parser):
    parser.add_argument('component', default=None, nargs='?',
        help='If specified, install this component instead of installing '+
             'the dependencies of the current component.'
    )
    parser.add_argument('--global', '-g', dest='act_globally', default=False, action='store_true',
        help='Install globally instead of in the current working directory.'
    )


def execCommand(args):
    if args.component is None:
        installDeps(args)
    else:
        installComponent(args)


def installDeps(args):
    cwd = os.getcwd()
    c = component.Component(cwd)
    if not c:
        logging.debug(str(c.error))
        logging.error('The current directory does not contain a valid component.')
        return 1
    logging.debug('install for %s' % c)
    if not args.target:
        logging.error('No target has been set, use "yotta target" to set one.')
        return 1
    target, errors = c.satisfyTarget(args.target)
    if errors:
        for error in errors:
            logging.error(error)
        return 1
    if args.act_globally:
        # the npm behaviour here would be to install the working directory
        # module into the global modules dir
        raise NotImplementedError()
    else:
        components, errors = c.satisfyDependenciesRecursive(target=target)
        for error in errors:
            logging.error(error)


def installComponent(args):
    path = folders.globalInstallDirectory() if args.act_globally else os.getcwd()
    logging.debug('install component %s to %s' % (args.component, path))
    
    # !!! FIXME: should support other URL specs than just unadorned names
    access.satisfyVersion(
              args.component,
                         '*',
        available_components = dict(),
                search_paths = [path],
                 working_dir = path
    )

