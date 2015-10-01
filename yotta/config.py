# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import json
import logging

# validate, , validate things, internal
from .lib import validate

def addOptions(parser):
    pass

def execCommand(args, following_args):
    c = validate.currentDirectoryModule()
    if not c:
        return 1

    if not args.target:
        logging.error('No target has been set, use "yotta target" to set one.')
        return 1

    target, errors = c.satisfyTarget(args.target)
    if errors:
        for error in errors:
            logging.error(error)
        return 1

    config = target.getMergedConfig()

    print(json.dumps(config, indent=2, separators=(',', ': ')))

