# Copyright 2014-2016 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import os
import logging

# validate, , validate things, internal
from yotta.lib import validate
# --config option, , , internal
from yotta import options


def addOptions(parser):
    options.config.addTo(parser)
    parser.add_argument('program', default=None, nargs='?',
        help='name of the program to be started'
    )


def execCommand(args, following_args):
    cwd = os.getcwd()

    c = validate.currentDirectoryModule()
    if not c:
        return 1

    if not c.isApplication():
        logging.error('This module describes a library not an executable. Only executables can be started.')
        return 1

    target, errors = c.satisfyTarget(args.target, additional_config=args.config)
    if errors:
        for error in errors:
            logging.error(error)
        return 1

    builddir = os.path.join(cwd, 'build', target.getName())

    if args.program is None:
        # if no program was specified, default to the name of the executable
        # module (if this is an executable module)
        args.program = c.getName()

    errcode = c.runScript('preStart', {"YOTTA_PROGRAM":args.program})
    if errcode:
        return errcode

    error = target.start(builddir, args.program, following_args)
    if error:
        logging.error(error)
        errcode = 1

    return errcode


