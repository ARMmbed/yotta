# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import os
import logging

# validate, , validate things, internal
from yotta.lib import validate
# settings, , load and save settings, internal
from yotta.lib import settings
# paths
from yotta.lib import paths
# --config option, , , internal
from yotta import options


def addOptions(parser):
    options.config.addTo(parser)
    parser.add_argument('program', default=None, nargs='?',
        help='name of the program to be debugged'
    )


def execCommand(args, following_args):
    cwd = os.getcwd()

    c = validate.currentDirectoryModule()
    if not c:
        return 1

    target, errors = c.satisfyTarget(args.target, additional_config=args.config)
    if errors:
        for error in errors:
            logging.error(error)
        return 1

    builddir = os.path.join(os.getcwd(), paths.DEFAULT_BUILD_DIR, target.getName())

    if args.program is None:
        if c.isApplication():
            # if no program was specified, default to the name of the executable
            # module (if this is an executable module)
            args.program = c.getName()
        else:
            logging.error('This module describes a library not an executable, so you must name an executable to debug.')
            return 1

    errcode = c.runScript('preDebug', {"YOTTA_PROGRAM":args.program})
    if errcode:
        return errcode

    error = target.debug(builddir, args.program)
    if error:
        logging.error(error)
        errcode = 1

    return errcode


