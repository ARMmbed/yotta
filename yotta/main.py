# standard library modules, , ,
import argparse
import logging
import sys

# subcommand modules, , add subcommands, internal
from . import version
from . import link
from . import link_target
from . import install
from . import update
from . import target
from . import build

# settings, , load and save settings, internal
from lib import settings

def logLevelFromVerbosity(v):
    return max(1, logging.INFO - v * (logging.ERROR-logging.NOTSET) / 5)

def main():
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(metavar='{install, update, link, target}')

    parser.add_argument('-v', '--verbose', dest='verbosity', action='count', default=0)
    parser.add_argument('-t', '--target', dest='target',
        default=settings.getProperty('build', 'target'),
        help='Set the build target (targetname[,versionspec_or_url])'
    )

    version_parser = subparser.add_parser('version', description='bump the module version')
    version.addOptions(version_parser)
    version_parser.set_defaults(command=version.execCommand)

    link_parser = subparser.add_parser('link', description='symlink a component')
    link.addOptions(link_parser)
    link_parser.set_defaults(command=link.execCommand)

    link_target_parser = subparser.add_parser('link-target', description='symlink a target')
    link_target.addOptions(link_target_parser)
    link_target_parser.set_defaults(command=link_target.execCommand)

    install_parser = subparser.add_parser(
        'install', description='install dependencies for the current module, or a specific module'
    )
    install.addOptions(install_parser)
    install_parser.set_defaults(command=install.execCommand)

    update_parser = subparser.add_parser(
        'update', description='update dependencies for the current module, or a specific module'
    )
    update.addOptions(update_parser)
    update_parser.set_defaults(command=update.execCommand)

    target_parser = subparser.add_parser('target', description='set or display the target device')
    target.addOptions(target_parser)
    target_parser.set_defaults(command=target.execCommand)

    build_parser = subparser.add_parser('build', description='Build the current component.')
    build.addOptions(build_parser)
    build_parser.set_defaults(command=build.execCommand)

    # short synonyms, subparser.choices is a dictionary, so use update() to
    # merge in the keys from another dictionary
    subparser.choices.update({
        'up':subparser.choices['update'],
        'in':subparser.choices['install'],
        'ln':subparser.choices['link'],
       'tgt':subparser.choices['target'],
    })

    args = parser.parse_args()

    # once logging.something has been called you have to remove all logging
    # handlers before re-configing...
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    logging.basicConfig(
        level=logLevelFromVerbosity(args.verbosity),
        format='%(message)s'
    )

    status = args.command(args)

    sys.exit(status or 0)

