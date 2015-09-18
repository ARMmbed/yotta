# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import logging

# validate, , validate things, internal
from .lib import validate

def addOptions(parser):
    # no options
    pass

def execCommand(args, following_args):
    p = validate.currentDirectoryModuleOrTarget()
    if not p:
        return 1

    if not p.vcsIsClean():
        logging.error('The working directory is not clean. Commit before publishing!')
        return 1

    error = p.publish(args.registry)
    if error:
        logging.error(error)
        return 1

    # tag the version published as 'latest'
    # !!! can't do this, as can't move tags in git?
    #p.commitVCS(tag='latest')
    logging.info('published latest version: %s', p.getVersion())
    return 0
