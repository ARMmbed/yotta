# standard library modules, , ,
import argparse
import logging
import os

# Component, , represents an installed component, internal
from lib import component




def addOptions(parser):
    parser.add_argument('module', default=None, nargs='?',
        help='If specified, install this module instead of installing '+
             'the dependencies of the current module.'
    )


def execCommand(args):
    if args.module is None:
        installDeps(args)
    else:
        installComponent(args)


def installDeps(args):
    c = component.Component(os.getcwd())
    if not c:
        logging.debug(str(c.error))
        logging.error('The current directory does not contain a valid component.')
        return 1
    
    c.satisfyDependenciesRecursive()


def installComponent(args):
    raise NotImplementedError()
