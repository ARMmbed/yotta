# standard library modules, , ,
import argparse
import os
import errno
import logging

# Component, , represents an installed component, internal
from lib import component
# folders, , get places to install things, internal
from . import folders

def _mkDirP(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def addOptions(parser):
    parser.add_argument('component', default=None, nargs='?',
        help='Link a globally installed (or globally linked) component into'+
             'the current component\'s dependencies. If ommited, globally'+
             'link the current component.'
    )

def execCommand(args):
    c = component.Component(os.getcwd())
    if not c:
        logging.debug(str(c.error))
        logging.error('The current directory does not contain a valid component.')
        return 1
    if args.component:
        _mkDirP(os.path.join(os.getcwd(), 'yotta_modules'))
        src = os.path.join(folders.globalInstallDirectory(), args.component)
        dst = os.path.join(os.getcwd(), 'yotta_modules', args.component)
    else:
        _mkDirP(folders.globalInstallDirectory())
        src = os.getcwd()
        dst = os.path.join(folders.globalInstallDirectory(), c.getName())
    logging.info('%s -> %s' % (src, dst))
    # !!! FIXME: recent windowses do support symlinks, but os.symlink doesn't
    # work on windows, so use something else
    os.symlink(src, dst)

