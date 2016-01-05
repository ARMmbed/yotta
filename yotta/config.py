# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import json
import logging
import sys

# validate, , validate things, internal
from .lib import validate
# utils, , miscellaneous utilities, internal
from .lib.utils import islast
# --config option, , , internal
from . import options

def addOptions(parser):
    options.config.addTo(parser)
    options.plain.addTo(parser)

def execCommand(args, following_args):
    c = validate.currentDirectoryModule()
    if not c:
        return 1

    if not args.target:
        logging.error('No target has been set, use "yotta target" to set one.')
        return 1

    target, errors = c.satisfyTarget(args.target, additional_config=args.config)
    if errors:
        for error in errors:
            logging.error(error)
        return 1

    config = target.getMergedConfig()

    if not args.plain:
        # then display blame information with nice colours :)
        dumpWithBlame(config, target.getConfigBlame())
        sys.stdout.write('\n')
    else:
        print(json.dumps(config, indent=2, separators=(',', ': ')))

def dumpWithBlame(config, blame, indent=''):
    # colorama, BSD 3-Clause license, cross-platform terminal colours, pip install colorama
    import colorama
    DIM       = colorama.Style.DIM       #pylint: disable=no-member
    RESET_ALL = colorama.Style.RESET_ALL #pylint: disable=no-member
    RESET_COL = colorama.Fore.RESET      #pylint: disable=no-member
    # true/false = green/red:
    GREEN     = colorama.Fore.GREEN      #pylint: disable=no-member
    RED       = colorama.Fore.RED        #pylint: disable=no-member
    # numbers = blue
    BLUE      = colorama.Fore.BLUE       #pylint: disable=no-member
    # strings = magenta
    MAGENTA   = colorama.Fore.MAGENTA    #pylint: disable=no-member

    sys.stdout.write('{')
    if len(config):
        sys.stdout.write('\n')
        for (k, val), last in islast(config.items()):
            sys.stdout.write(indent+'  ')
            sys.stdout.write('"' + k + '": ')
            if isinstance(val, dict):
                dumpWithBlame(val, blame.get(k, {}), indent+'  ')
                if not last:
                    sys.stdout.write(',')
            else:
                if val is True:
                    sys.stdout.write(GREEN + 'true' + RESET_COL)
                elif val is False:
                    sys.stdout.write(RED + 'false' + RESET_COL)
                elif isinstance(val, int) or isinstance(val, float):
                    sys.stdout.write(BLUE + str(val) + RESET_COL)
                else:
                    # must be a string
                    sys.stdout.write('"'+MAGENTA + str(val) + RESET_COL+'"')
                if not last:
                    sys.stdout.write(',')
                if k in blame:
                    sys.stdout.write(' '+DIM+'// ' + blame[k])
            sys.stdout.write(RESET_ALL + '\n')
        sys.stdout.write(indent)
    sys.stdout.write('}')
