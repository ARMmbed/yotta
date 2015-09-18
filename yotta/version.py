# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import argparse
import logging
import os

# version, , represent versions and specifications, internal
from .lib import version
# Component, , represents an installed component, internal
from .lib import component
# Target, , represents an installed target, internal
from .lib import target
# vcs, , represent version controlled directories, internal
from .lib import vcs

def addOptions(parser):
    def patchType(s):
        if s.lower() in ('major', 'minor', 'patch'):
            return s.lower()
        try:
            return version.Version(s)
        except:
            raise argparse.ArgumentTypeError(
                '"%s" is not a valid version (expected patch, major, minor, or something like 1.2.3)' % s
            )
    parser.add_argument('action', type=patchType, nargs='?', help='[patch | minor | major | <version>]')


def execCommand(args, following_args):
    wd = os.getcwd()
    c = component.Component(wd)
    # skip testing for target if we already found a component
    t = None if c else target.Target(wd)
    if not (c or t):
        logging.debug(str(c.getError()))
        logging.debug(str(t.getError()))
        logging.error('The current directory does not contain a valid module or target.')
        return 1
    else:
        # only needed separate objects in order to display errors
        p = (c or t)

    if args.action:
        try:
            if not p.vcsIsClean():
                logging.error('The working directory is not clean')
                return 1

            v = p.getVersion()
            if args.action in ('major', 'minor', 'patch'):
                v.bump(args.action)
            else:
                v = args.action
            logging.info('@%s' % v)
            p.setVersion(v)

            p.writeDescription()

            p.commitVCS(tag='v'+str(v))
        except vcs.VCSError as e:
            logging.error(e)
    else:
        logging.info(str(p.getVersion()))

