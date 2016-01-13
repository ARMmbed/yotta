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
# --registry option, , , internal
from . import options

def addOptions(parser):
    # accept top-level registry option at subcommand level too
    options.registry.addTo(parser)
    options.noninteractive.addTo(parser)
    options.plain.addTo(parser)

    # pass the API key for logging into this registry (it will be saved, and
    # used for future requests to this registry)
    parser.add_argument('--apikey', '-k', dest='apikey', help=argparse.SUPPRESS)
    # --github can be used to force login with github instead of mbed, the
    # default): github login is necessary for pulling things from private
    # github repositories. You shouldn't normally need to do this, as you will
    # be prompted for github login automatically when required, but this is
    # useful if you want to pre-cache login information for any reason.
    parser.add_argument('--github', dest='github_login', action='store_true',
        default=False, help='force login with GitHub instead of mbed. You '+
        "shouldn't normally need to use this switch, as you will be prompted "+
        "for GitHub login automatically if required."
    )

def execCommand(args, following_args):
    registry = args.registry
    if args.apikey:
        registry_access.setAPIKey(registry, args.apikey)
    try:
        provider = None
        if args.github_login:
            provider = 'github'
        return auth.authorizeUser(registry, provider=provider, interactive=args.interactive)
    except auth.AuthTimedOut as e:
        logging.error("Login failed: %s", e)
        return 1

