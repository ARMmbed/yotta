# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
from __future__ import print_function

# Registry Access, , access packages in the registry, internal
from .lib import registry_access
from .lib import settings

# colorama, BSD 3-Clause license, cross-platform terminal colours, pip install colorama
import colorama

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
    success = False
    if not args.plain:
        DIM    = colorama.Style.DIM       #pylint: disable=no-member
        BRIGHT = colorama.Style.BRIGHT    #pylint: disable=no-member
        GREEN  = colorama.Fore.GREEN      #pylint: disable=no-member
        BLUE   = colorama.Fore.BLUE       #pylint: disable=no-member
        RESET  = colorama.Style.RESET_ALL #pylint: disable=no-member
    else:
        DIM = BRIGHT = GREEN = RED = RESET = u''
    count = 0
    for result in registry_access.search(query=args.query, keywords=args.kw, registry=args.registry):
        count += 1
        success= True
        if count > args.limit:
            break
        if args.type == 'both' or args.type == result['type']:
            description = result['description'] if 'description' in result else '<no description>'
            print('%s%s %s%s%s: %s' % (GREEN, result['name'], RESET+DIM, result['version'], RESET, lengthLimit(description, 160)))
    for repo in filter(lambda s: 'type' in s and s['type'] == 'registry', settings.get('sources') or []) :
        count = 0
        print('')
        print('additional results from %s:' % repo['url'])
        for result in registry_access.search(query=args.query, keywords=args.kw, registry=repo['url']):
            count += 1
            success= True
            if count > args.limit:
                break
            if args.type == 'both' or args.type == result['type']:
                description = result['description'] if 'description' in result else '<no description>'
                print('  %s%s %s%s%s: %s' % (GREEN, result['name'], RESET+DIM, result['version'], RESET, lengthLimit(description, 160)))
    # exit status: success if we found something, otherwise fail
    return 0 if success else 1

