# standard library modules, , ,
import argparse
import logging

# version, , represent versions and specifications, internal
from lib import version


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
    print 'exec version command', args


