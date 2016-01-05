# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import logging
import os

# colorama, BSD 3-Clause license, color terminal output, pip install colorama
import colorama

# fsutils, , misc filesystem utils, internal
from .lib import fsutils
# validate, , validate things, internal
from .lib import validate
# folders, , get places to install things, internal
from .lib import folders

def addOptions(parser):
    parser.add_argument('link_target', default=None, nargs='?',
        help='Link a globally installed (or globally linked) target into '+
             'the current target\'s dependencies. If ommited, globally '+
             'link the current target.'
    )

def execCommand(args, following_args):
    if args.link_target:
        c = validate.currentDirectoryModule()
        if not c:
            return 1
        err = validate.targetNameValidationError(args.link_target)
        if err:
            logging.error(err)
            return 1
        fsutils.mkDirP(os.path.join(os.getcwd(), 'yotta_targets'))
        src = os.path.join(folders.globalTargetInstallDirectory(), args.link_target)
        dst = os.path.join(os.getcwd(), 'yotta_targets', args.link_target)
        # if the target is already installed, rm it
        fsutils.rmRf(dst)
    else:
        t = validate.currentDirectoryTarget()
        if not t:
            return 1
        fsutils.mkDirP(folders.globalTargetInstallDirectory())
        src = os.getcwd()
        dst = os.path.join(folders.globalTargetInstallDirectory(), t.getName())

    if args.link_target:
        realsrc = fsutils.realpath(src)
        if src == realsrc:
            logging.warning(
              ('%s -> %s -> ' % (dst, src)) + colorama.Fore.RED + 'BROKEN' + colorama.Fore.RESET #pylint: disable=no-member
            )
        else:
            logging.info('%s -> %s -> %s' % (dst, src, realsrc))
    else:
        logging.info('%s -> %s' % (dst, src))
    fsutils.symlink(src, dst)


