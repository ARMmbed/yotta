# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import logging

# validate, , validate things, internal
from .lib import validate

def addOptions(parser):
    pass

def execCommand(args, following_args):
    p = validate.currentDirectoryModuleOrTarget()
    if not p:
        return 1

    error = p.unpublish(args.registry)
    if error:
        logging.error(error)
        return 1

    logging.info('unpublished version: %s', p.getVersion())
    return 0
