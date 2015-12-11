# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

from .lib import lazyregex #pylint: disable=unused-import
from .lib import errors #pylint: disable=unused-import

# NOTE: argcomplete must be first!
# argcomplete, pip install argcomplete, tab-completion for argparse, Apache-2
import argcomplete

# standard library modules, , ,
import argparse
import sys
import os

# globalconf, share global arguments between modules, internal
import yotta.lib.globalconf as globalconf

# hook to support coverage information when yotta runs itself during tests:
if 'COVERAGE_PROCESS_START' in os.environ:
    import coverage
    coverage.process_startup()


def splitList(l, at_value):
    r = [[]]
    for x in l:
        if x == at_value:
            r.append(list())
        else:
            r[-1].append(x)
    return r

# Override the argparse default version action so that we can avoid importing
# pkg_resources (which is slowww) unless someone has actually asked for the
# version
class FastVersionAction(argparse.Action):
    def __call__(self, parser, args, values, option_string=None):
        import pkg_resources
        sys.stdout.write(pkg_resources.require("yotta")[0].version + '\n') #pylint: disable=not-callable
        sys.exit(0)

def main():
    # standard library modules, , ,
    import logging
    from functools import reduce

    # logging setup, , setup the logging system, internal
    from .lib import logging_setup
    # options, , common argument parser options, internal
    import yotta.options as options

    logging_setup.init(level=logging.INFO, enable_subsystems=None, plain=False)

    # we override many argparse things to make options more re-usable across
    # subcommands, and allow lazy loading of subcommand modules:
    parser = options.parser.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description='Build software using re-usable components.\n'+
        'For more detailed help on each subcommand, run: yotta <subcommand> --help'
    )
    subparser = parser.add_subparsers(dest='subcommand_name', metavar='<subcommand>')

    parser.add_argument('--version', nargs=0, action=FastVersionAction,
        help='display the version'
    )

    # add re-usable top-level options which subcommands may also accept
    options.verbosity.addTo(parser)
    options.debug.addTo(parser)
    options.plain.addTo(parser)
    options.noninteractive.addTo(parser)
    options.registry.addTo(parser)
    options.target.addTo(parser)
    options.config.addTo(parser)

    def addParser(name, module_name, description, help=None):
        if help is None:
            help = description
        def onParserAdded(parser):
            import importlib
            module = importlib.import_module('.' + module_name, 'yotta')
            module.addOptions(parser)
            parser.set_defaults(command=module.execCommand)
        subparser.add_parser_async(
            name, description=description, help=help,
            formatter_class=argparse.RawTextHelpFormatter,
            callback=onParserAdded
        )

    addParser('search', 'search',
        'Search for open-source modules and targets that have been published '+
        'to the yotta registry (with yotta publish). See help for `yotta '+
        'install` for installing modules, and for `yotta target` for '+
        'switching targets.',
        'Search for published modules and targets'
    )
    addParser('init', 'init', 'Create a new module.')
    addParser('install', 'install',
        'Add a specific module as a dependency, and download it, or install all '+
        'dependencies for the current module.'
    )
    addParser('build', 'build',
        'Build the current module. Options can be passed to the underlying '+
        'build tool by passing them after --, e.g. to do a verbose build '+
        'which will display each command as it is run, use:\n'+
        '  yotta build -- -v\n\n'+
        'The programs or libraries to build can be specified (by default '+
        'only the libraries needed by the current module and the current '+
        "module's own tests are built). For example, to build the tests of "+
        'all dependencies, run:\n  yotta build all_tests\n\n',
        'Build the current module.'
    )
    addParser('version', 'version', 'Bump the module version, or (with no arguments) display the current version.')
    addParser('link', 'link',
        'Symlink a module to be used in another module. Use "yotta link" '+
        '(with no arguments) to link the current module globally. Or use '+
        '"yotta link module-name" To use a module that was previously linked '+
        'globally in the current module.',
        'Symlink a module'
    )
    addParser('link-target', 'link_target',
        'Symlink a target to be used in another module. Use "yotta link-target" '+
        '(with no arguments) to link the current target globally. Or use '+
        '"yotta link-target target-name" To use a target that was previously linked '+
        'globally in the current module.',
        'Symlink a target'
    )
    addParser('update', 'update', 'Update dependencies for the current module, or a specific module.')
    addParser('target', 'target', 'Set or display the target device.')
    addParser('debug', 'debug', 'Attach a debugger to the current target.  Requires target support.')
    addParser('test', 'test_subcommand',
        'Run the tests for the current module on the current target. A build '+
        'will be run first, and options to the build subcommand are also '+
        'accepted by test.\nThis subcommand requires the target to provide a '+
        '"test" script that will be used to run each test. Modules may also '+
        'define a "testReporter" script, which will be piped the output from '+
        'each test, and may produce a summary.',
        'Run the tests for the current module on the current target. Requires target support.'
    )
    addParser('publish', 'publish', 'Publish a module or target to the public registry.')
    addParser('unpublish', 'unpublish', 'Un-publish a recently published module or target.')
    addParser('login', 'login', 'Authorize for access to private github repositories and publishing to the yotta registry.')
    addParser('logout', 'logout', 'Remove saved authorization token for the current user.')
    addParser('whoami', 'whoami', 'Display who the currently logged in user is (if any).')
    addParser('list', 'list', 'List the dependencies of the current module, or the inherited targets of the current target.')
    addParser('outdated', 'outdated', 'Display information about dependencies which have newer versions available.')
    addParser('uninstall', 'uninstall', 'Remove a specific dependency of the current module, both from module.json and from disk.')
    addParser('remove', 'remove',
        'Remove the downloaded version of a dependency module or target, or '+
        'un-link a linked module or target (see yotta link --help for details '+
        'of linking). This command does not modify your module.json file.',
        'Remove or unlink a dependency without removing it from module.json.'
    )
    addParser('owners', 'owners', 'Add/remove/display the owners of a module or target.')
    addParser('licenses', 'licenses', 'List the licenses of the current module and its dependencies.')
    addParser('clean', 'clean', 'Remove files created by yotta and the build.')
    addParser('config', 'config', 'Display the target configuration info.')

    # short synonyms, subparser.choices is a dictionary, so use update() to
    # merge in the keys from another dictionary
    short_commands = {
                'up':subparser.choices['update'],
                'in':subparser.choices['install'],
                'ln':subparser.choices['link'],
                 'v':subparser.choices['version'],
                'ls':subparser.choices['list'],
                'rm':subparser.choices['remove'],
            'unlink':subparser.choices['remove'],
     'unlink-target':subparser.choices['remove'],
             'owner':subparser.choices['owners'],
              'lics':subparser.choices['licenses'],
               'who':subparser.choices['whoami']
    }
    subparser.choices.update(short_commands)

    # split the args into those before and after any '--'
    # argument - subcommands get raw access to arguments following '--', and
    # may pass them on to (for example) the build tool being used
    split_args = splitList(sys.argv, '--')
    following_args = reduce(lambda x,y: x + ['--'] + y, split_args[1:], [])[1:]

    # complete all the things :)
    argcomplete.autocomplete(
         parser,
        exclude = list(short_commands.keys()) + ['-d', '--debug', '-v', '--verbose']
    )

    # when args are passed directly we need to strip off the program name
    # (hence [:1])
    args = parser.parse_args(split_args[0][1:])

    # set global arguments that are shared everywhere and never change
    globalconf.set('interactive', args.interactive)
    globalconf.set('plain', args.plain)

    # finally, do stuff!
    if 'command' not in args:
        parser.print_usage()
        sys.exit(0)

    try:
        status = args.command(args, following_args)
    except KeyboardInterrupt:
        logging.warning('interrupted')
        status = -1

    sys.exit(status or 0)
