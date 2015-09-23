# Copyright 2014 ARM Limited
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
    parser.add_argument('component', default=None, nargs='?',
        help='Link a globally installed (or globally linked) module into '+
             'the current module\'s dependencies. If ommited, globally '+
             'link the current module.'
    )

def execCommand(args, following_args):
    c = validate.currentDirectoryModule()
    if not c:
        return 1
    if args.component:
        fsutils.mkDirP(os.path.join(os.getcwd(), 'yotta_modules'))
        src = os.path.join(folders.globalInstallDirectory(), args.component)
        dst = os.path.join(os.getcwd(), 'yotta_modules', args.component)
        # if the component is already installed, rm it
        fsutils.rmRf(dst)
    else:
        fsutils.mkDirP(folders.globalInstallDirectory())

        src = os.getcwd()
        dst = os.path.join(folders.globalInstallDirectory(), c.getName())

    if args.component:
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

