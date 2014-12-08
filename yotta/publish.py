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


def addOptions(parser):
    # no options
    pass


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
    
    if not p.vcsIsClean():
        logging.error('The working directory is not clean. Commit before publishing!')
        return 1

    error = p.publish()
    if error:
        logging.error(error)
        return 1
    
    # tag the version published as 'latest'
    # !!! can't do this, as can't move tags in git?
    #p.commitVCS(tag='latest')
    logging.info('published latest version: %s', p.getVersion())
