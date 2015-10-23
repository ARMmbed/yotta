# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
from __future__ import print_function
import itertools

# Registry Access, , access packages in the registry, internal
from .lib import registry_access
from .lib import settings
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
    parser.add_argument(
        '-s', '--short', default=False, action='store_true',
        help='Use short output format.'
    )

def lengthLimit(s, l):
    if len(s) > l:
        return s[:l-3] + '...'
    return s

def formatResult(result, plain=False, short=False, indent=''):
    if not plain:
        # colorama, BSD 3-Clause license, cross-platform terminal colours, pip install colorama
        import colorama
        DIM    = colorama.Style.DIM       #pylint: disable=no-member
        BRIGHT = colorama.Style.BRIGHT    #pylint: disable=no-member
        NORMAL = colorama.Style.NORMAL    #pylint: disable=no-member
        GREEN  = colorama.Fore.GREEN      #pylint: disable=no-member
        BLUE   = colorama.Fore.BLUE       #pylint: disable=no-member
        RED    = colorama.Fore.RED        #pylint: disable=no-member
        YELLOW = colorama.Fore.YELLOW     #pylint: disable=no-member
        RESET  = colorama.Style.RESET_ALL #pylint: disable=no-member
    else:
        DIM = BRIGHT = NORMAL = GREEN = BLUE = RED = YELLOW = RESET = u''

    def formatKeyword(keyword):
        if keyword.endswith('official'):
            return BRIGHT + GREEN + keyword + RESET
        else:
            return BRIGHT + keyword + NORMAL

    def formatAuthor(author):
        if isinstance(author, dict):
            return author.get('name', '<name unknown>') + ' ' + author.get('email', '<email unknown')
        else:
            return author

    # --short:
    # module-name module-version: description description

    # not --short:
    # module-name module-version
    #    description description description
    #    keyword, keyword, keyword
    #    author, author

    v = version.Version(result['version'])
    if v.major() < 1:
        if v.minor() < 1:
            ver_string = RED + result['version'] + RESET
        else:
            ver_string = YELLOW + result['version'] + RESET
    else:
        ver_string = GREEN + result['version'] + RESET

    name_string = BRIGHT+result['name']+NORMAL

    if 'description' in result:
        description = result['description']
        description_colour = ''
    else:
        description = '<description missing>'
        description_colour = RED

    if short:
        description = description_colour + lengthLimit(description, 160).replace('\n', ' ') + RESET
    else:
        description = description_colour + lengthLimit(description, 800).replace('\n', indent+' ').rstrip('\n') + RESET

    if short:
        return indent+u'%s %s: %s%s' % (name_string, ver_string, description, RESET)
    else:
        r = indent+(u'%s %s:\n' % (name_string, ver_string)) +\
            indent+(u'    %s\n' % (description))
        if 'keywords' in result and result['keywords']:
            r += indent+(u'    %s\n' % (', '.join([formatKeyword(k) for k in result['keywords']])))

        if 'author' in result and result['author']:
            authors = [result['author']]
        elif 'maintainers' in result and len(result['maintainers']):
            authors = result['maintainers']
        else:
            authors = []
        if len(authors):
            r += indent+(u'    %s\n' % (DIM + (', '.join([formatAuthor(a) for a in authors])) + RESET))

        return r.rstrip('\n')

def execCommand(args, following_args):
    success = False
    for result in itertools.islice(registry_access.search(query=args.query, keywords=args.kw, registry=args.registry), args.limit):
        success= True
        if args.type == 'both' or args.type == result['type']:
            print(formatResult(result, args.plain, short=args.short))
    for repo in filter(lambda s: 'type' in s and s['type'] == 'registry', settings.get('sources') or []) :
        count = 0
        print('')
        print('additional results from %s:' % repo['url'])
        for result in itertools.islice(registry_access.search(query=args.query, keywords=args.kw, registry=repo['url']), args.limit):
            success= True
            if args.type == 'both' or args.type == result['type']:
                print(formatResult(result, args.plain, indent='  ', short=args.short))
    # exit status: success if we found something, otherwise fail
    return 0 if success else 1

