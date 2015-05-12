# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
from __future__ import print_function
import argparse
import logging
import os

# Registry Access, , access packages in the registry, internal
from .lib import registry_access
from .lib import version

def addOptions(parser):
    parser.add_argument(
        'type', choices=['module', 'target', 'both'], nargs='?', default='both',
        help="What to search (software modules, build targets, or both)"
    )
    parser.add_argument(
        'query', type=str, nargs=1, default='',
        help='Search query text. All items that contain the specified words '+
             'in their description, name, or keywords will be returned.'
    )
    parser.add_argument(
        '-k', '--keyword', default=[], action='append', dest='kw',
        help='Additional keywords to constrain the search. All specified '+
             'keywords must exist in an item\'s keywords list for it to '+
             'be returned.'
    )
    parser.add_argument(
        '-l', '--limit', default=10, type=int,
        help='Limit the number of results returned.'
    )

def lengthLimit(s, l):
    if len(s) > l:
        return s[:l-3] + '...'
    return s

def execCommand(args, following_args):
    # the registry currently returns many versions of the same module, the
    # sorting and unique-ing here is to pick only the latest version to display
    # to the user (note that modules and targets may have the same name but be
    # different things, however, which is why the uniquing key includes the
    # type)
    count = 0
    for result in registry_access.search(query=args.query, keywords=args.kw, registry=args.registry):
        count += 1
        if count > args.limit:
            break
        if args.type == 'both' or args.type == result['type']:
            description = result['description'] if 'description' in result else '<no description>'
            print('%s %s: %s' % (result['name'], result['version'], lengthLimit(description, 160)))
    # exit status: success if we found something, otherwise fail
    if count:
        return 0
    else:
        return 1

