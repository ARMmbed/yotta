# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import argparse
import logging

# auth, , authenticate users, internal
from .lib import auth
# Registry Access, , access modules in the registry, internal
from .lib import registry_access

def addOptions(parser):
    # set the registry URL to save an API key for (this argument is also a
    # top-level one, use a different dest here so we can distinguish)
    parser.add_argument('--registry', dest='_registry', help=argparse.SUPPRESS)
    # pass the API key for logging into this registry (it will be saved, and
    # used for future requests to this registry)
    parser.add_argument('--apikey', '-k', dest='apikey', help=argparse.SUPPRESS)

def execCommand(args, following_args):
    registry = args._registry or args.registry
    if args.apikey:
        registry_access.setAPIKey(registry, args.apikey)

    try:
        return auth.authorizeUser(registry, provider=None, interactive=args.interactive)
    except auth.AuthTimedOut as e:
        logging.error("Login failed: %s", e)
        return 1

