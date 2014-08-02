# standard library modules, , ,
import argparse
import logging
import os

# Component, , represents an installed component, internal
from lib import component
# Target, , represents an installed target, internal
from lib import target


def addOptions(parser):
    pass


def execCommand(args):
    wd = os.getcwd()
    c = component.Component(wd)

    if not c:
        logging.debug(str(c.getError()))
        logging.error('The current directory does not contain a valid component.')
        return 1

    if not args.target:
        logging.error('No target has been set, use "yotta target" to set one.')
        return 1

    target, errors = c.satisfyTarget(args.target)
    if errors:
        for error in errors:
            logging.error(error)
        return 1

    components = c.getDependenciesRecursive(
                      target = target,
        available_components = [(c.getName(), c)]
    )

    for v in components.values():
        logging.info(str(v))

