# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import argparse
import logging
import sys
import pkg_resources
from functools import reduce

# subcommand modules, , add subcommands, internal
from . import version
from . import link
from . import link_target
from . import install
from . import update
from . import target
from . import build
from . import init
from . import publish
from . import debug
from . import login
from . import logout
from . import list as list_command
from . import uninstall
from . import owners
from . import licenses
from . import clean
from . import search

# logging setup, , setup the logging system, internal
from .lib import logging_setup
# detect, , detect things about the system, internal
from .lib import detect

def logLevelFromVerbosity(v):
    return max(1, logging.INFO - v * (logging.ERROR-logging.NOTSET) // 5)

def splitList(l, at_value):
    r = [[]]
    for x in l:
        if x == at_value:
            r.append(list())
        else:
            r[-1].append(x)
    return r


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description='Build software using re-usable components.\n'+
        'For more detailed help on each subcommand, run: yotta <subcommand> --help'
    )
    subparser = parser.add_subparsers(metavar='<subcommand>')

    parser.add_argument('--version', dest='show_version', action='version',
            version=pkg_resources.require("yotta")[0].version,
        help='display the version'
    )
    parser.add_argument('-v', '--verbose', dest='verbosity', action='count',
        default=0,
        help='increase verbosity: can be used multiple times'
    )
    parser.add_argument('-d', '--debug', dest='debug', action='append',
        metavar='SUBSYS',
        help=argparse.SUPPRESS
        #help='specify subsystems to debug: use in conjunction with -v to '+
        #     'increase the verbosity only for specified subsystems'
    )

    parser.add_argument('-t', '--target', dest='target',
        default=detect.defaultTarget(),
        help='Set the build and dependency resolution target (targetname[,versionspec_or_url])'
    )

    def addParser(name, module, description, help=None):
        if help is None:
            help = description
        parser = subparser.add_parser(
            name, description=description, help=help,
            formatter_class=argparse.RawTextHelpFormatter
        )
        module.addOptions(parser)
        parser.set_defaults(command=module.execCommand)

    addParser('search', search,
        'Search for open-source modules and targets that have been published '+
        'to the yotta registry (with yotta publish). See help for `yotta '+
        'install --save` for installing modules, and for `yotta target` for '+
        'switching targets.'
    )
    addParser('init', init, 'Create a new module.')
    addParser('install', install, 'Install dependencies for the current module, or a specific module.')
    addParser('build', build,
        'Build the current module. Options can be passed to the underlying '+\
        'build tool by passing them after --, e.g. to do a parallel build '+\
        'when make is the build tool, run `yotta build -- -j`',
        'Build the current module.'
    )
    addParser('version', version, 'Bump the module version, or (with no arguments) display the current version.')
    addParser('link', link, 'Symlink a module.')
    addParser('link-target', link_target, 'Symlink a target.')
    addParser('update', update, 'Update dependencies for the current module, or a specific module.')
    addParser('target', target, 'Set or display the target device.')
    addParser('debug', debug, 'Attach a debugger to the current target.  Requires target support.')
    addParser('publish', publish, 'Publish a module or target to the public registry.')
    addParser('login', login, 'Authorize for access to private github repositories and publishing to the yotta registry.')
    addParser('logout', logout, 'Remove saved authorization token for the current user.')
    addParser('list', list_command, 'List the dependencies of the current module.')
    addParser('uninstall', uninstall, 'Remove a specific dependency of the current module.')
    addParser('owners', owners, 'Add/remove/display the owners of a module or target.')
    addParser('licenses', licenses, 'List the licenses of the current module and its dependencies.')
    addParser('clean', clean, 'Remove files created by yotta and the build.')

    # short synonyms, subparser.choices is a dictionary, so use update() to
    # merge in the keys from another dictionary
    subparser.choices.update({
            'up':subparser.choices['update'],
            'in':subparser.choices['install'],
            'ln':subparser.choices['link'],
             'v':subparser.choices['version'],
            'ls':subparser.choices['list'],
        'unlink':subparser.choices['uninstall'],
            'rm':subparser.choices['uninstall'],
         'owner':subparser.choices['owners'],
          'lics':subparser.choices['licenses']
    })
    
    # split the args into those before and after any '--'
    # argument - subcommands get raw access to arguments following '--', and
    # may pass them on to (for example) the build tool being used
    split_args = splitList(sys.argv, '--')
    following_args = reduce(lambda x,y: x + ['--'] + y, split_args[1:], [])[1:]

    # when args are passed directly we need to strip off the program name
    # (hence [:1])
    args = parser.parse_args(split_args[0][1:])

    loglevel = logLevelFromVerbosity(args.verbosity)
    logging_setup.init(level=loglevel, enable_subsystems=args.debug)
    
    # finally, do stuff!
    if 'command' not in args:
        parser.print_usage()
        sys.exit(0)

    status = args.command(args, following_args)

    sys.exit(status or 0)

