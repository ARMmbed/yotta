# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import argparse

# Github Access, , access repositories on github, internal
from .lib import auth, registry_access

def addOptions(parser):
    # set the registry URL to save an API key for (this argument is also a
    # top-level one, use a different dest here so we can distinguish)
    parser.add_argument('--registry', dest='_registry', help=argparse.SUPPRESS)

def execCommand(args, following_args):
    registry = args._registry or args.registry
    auth.deauthorize()
    registry_access.deauthorize(registry)

