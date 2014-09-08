# standard library modules, , ,
import argparse
import logging
import sys
import pkg_resources

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
from . import list
from . import uninstall

from lib import logging_setup

# settings, , load and save settings, internal
from lib import settings

def logLevelFromVerbosity(v):
    return max(1, logging.INFO - v * (logging.ERROR-logging.NOTSET) / 5)

def main():
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(metavar='{install, update, version, link, link-target, target, build, init, publish, login, logout}')

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
        help='specify subsystems to debug: use in conjunction with -v to '+
             'increase the verbosity only for specified subsystems'
    )
    parser.add_argument('-t', '--target', dest='target',
        default=settings.getProperty('build', 'target'),
        help='Set the build and dependency resolution target (targetname[,versionspec_or_url])'
    )

    def addParser(name, module, description):
        parser = subparser.add_parser(name, description=description)
        module.addOptions(parser)
        parser.set_defaults(command=module.execCommand)

    addParser('version', version, 'Bump the module version, or (with no arguments) display the current version.')
    addParser('link', link, 'Symlink a component.')
    addParser('link-target', link_target, 'Symlink a target.')
    addParser('install', install, 'Install dependencies for the current module, or a specific module.')
    addParser('update', update, 'Update dependencies for the current module, or a specific module.')
    addParser('target', target, 'Set or display the target device.')
    addParser('build', build, 'Build the current component.')
    addParser('debug', debug, 'Attach a debugger to the current target.  Requires target support.')
    addParser('init', init, 'Create a new component.')
    addParser('publish', publish, 'Publish a component or target to the public registry.')
    addParser('login', login, 'Authorize for access to private github repositories and publishing to the yotta registry.')
    addParser('logout', logout, 'Remove saved authorization token for the current user.')
    addParser('list', list, 'List the dependencies of the current module.')
    addParser('uninstall', uninstall, 'Remove a specific dependency of the current module.')

    # short synonyms, subparser.choices is a dictionary, so use update() to
    # merge in the keys from another dictionary
    subparser.choices.update({
            'up':subparser.choices['update'],
            'in':subparser.choices['install'],
            'ln':subparser.choices['link'],
             'v':subparser.choices['version'],
            'ls':subparser.choices['list'],
        'unlink':subparser.choices['uninstall'],
            'rm':subparser.choices['uninstall']
    })

    args = parser.parse_args() 

    loglevel = logLevelFromVerbosity(args.verbosity)
    logging_setup.init(level=loglevel, enable_subsystems=args.debug)
    
    # finally, do stuff!
    status = args.command(args)

    sys.exit(status or 0)

