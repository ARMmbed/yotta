# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import argparse

# Github Access, , access repositories on github, internal
from .lib import github_access, registry_access

def addOptions(parser):
    # set the registry URL to save an API key for
    parser.add_argument('--registry', dest='registry', help=argparse.SUPPRESS)

def execCommand(args, following_args):
    if args.registry is None:
        github_access.deauthorize()
    registry_access.deauthorize(args.registry)

