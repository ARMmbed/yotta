# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import logging

# validate, , validate things, internal
from .lib import validate

def addOptions(parser):
    parser.add_argument('component', default=None, nargs='?',
        help='If specified, update (and if necessary install) this module '+
             'instead of updating the dependencies of the current module.'
    )
    parser.add_argument('-l', '--update-linked', dest='update_linked',
        action='store_true', default=False,
        help='Traverse linked modules, and update dependencies found there too.'
    )



def execCommand(args, following_args):
    if args.component is None:
        updateDeps(args)
    else:
        updateComponent(args)


def updateDeps(args):
    c = validate.currentDirectoryModule()
    if not c:
        return 1
    logging.debug('update for %s' % c)
    if not args.target:
        logging.error('No target has been set, use "yotta target" to set one.')
        return 1
    target, errors = c.satisfyTarget(args.target, update_installed=True)
    if errors:
        for error in errors:
            logging.error(error)
        return 1

    components, errors = c.satisfyDependenciesRecursive(
                          target = target,
                update_installed = True,
                  traverse_links = args.update_linked,
            available_components = [(c.getName(), c)]
        )
    for error in errors:
        logging.error(error)

def updateComponent(args):
    raise NotImplementedError

