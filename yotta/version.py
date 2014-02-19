# standard library modules, , ,
import argparse
import logging
import os

# version, , represent versions and specifications, internal
from lib import version
# Component, , represents an installed component, internal
from lib import component


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
    parser.add_argument('action', type=patchType, help='[patch | minor | major | <version>]')


def execCommand(args):
    c = component.Component(os.getcwd())
    if not c:
        logging.debug(str(c.error))
        logging.error('The current directory does not contain a valid component.')
        return 1
    
    if not c.vcsIsClean():
        logging.error('The working directory is not clean')
        return 1

    v = c.getVersion()
    if args.action in ('major', 'minor', 'patch'):
        v.bump(args.action)
    else:
        v = args.action
    logging.info('@%s' % v)
    c.setVersion(v)

    c.writeDescription()

    c.commitVCS(tag='v'+str(v))


