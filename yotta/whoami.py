# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import argparse

# Registry Access, , access modules in the registry, internal
from .lib import registry_access

def addOptions(parser):
    # the registry URL to provide login info for
    parser.add_argument('--registry', dest='registry', help=argparse.SUPPRESS)

def execCommand(args, following_args):
    email_address = registry_access.whoami(args.registry)
    if email_address is not None:
        print(email_address)
        return 0
    else:
        print('not logged in')
        return 1


