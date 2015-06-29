# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import argparse

# Github Access, , access repositories on github, internal
from .lib import github_access
# Registry Access, , access modules in the registry, internal
from .lib import registry_access

def addOptions(parser):
    # set the registry URL to save an API key for
    parser.add_argument('--registry', dest='registry', help=argparse.SUPPRESS)
    # pass the API key for logging into this registry (it will be saved, and
    # used for future requests to this registry)
    parser.add_argument('--apikey', '-k', dest='apikey', help=argparse.SUPPRESS)

def execCommand(args, following_args):
    if args.apikey:
        registry_access.setAPIKey(args.registry, args.apikey)

    github_access.authorizeUser(args.registry)

