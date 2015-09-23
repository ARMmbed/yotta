# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import logging
import os

# colorama, BSD 3-Clause license, cross-platform terminal colours, pip install colorama
import colorama


# !!! workaround colorama + posh-git bug, where ANSI emulation is incorrectly
# disabled:
restore_env_term = None
if os.environ.get('POSH_GIT', False) and 'TERM' in os.environ:
    restore_env_term = os.environ['TERM']
    del os.environ['TERM']

# colorama replaces stdout and stderr with objects that do switch colour
# sequences to the appropriate windows ones, we do most of our stdout through
# logging, so setup that proxying here:
colorama.init()

if restore_env_term is not None:
    os.environ['TERM'] = restore_env_term


class FancyFormatter(logging.Formatter):
    #pylint: disable=no-member
    def __init__(self):
        super(FancyFormatter, self).__init__()

    def levelStyle(self, record):
        if record.levelno <= logging.DEBUG:
            return colorama.Style.DIM + colorama.Fore.RESET #pylint: disable=no-member
        elif record.levelno >= logging.CRITICAL:
            return colorama.Style.BRIGHT + colorama.Fore.RED #pylint: disable=no-member
        elif record.levelno >= logging.ERROR:
            return colorama.Style.BRIGHT + colorama.Fore.RED #pylint: disable=no-member
        elif record.levelno >= logging.WARNING:
            return colorama.Style.BRIGHT + colorama.Fore.YELLOW #pylint: disable=no-member
        return colorama.Style.NORMAL + colorama.Fore.GREEN #pylint: disable=no-member

    def messageStyle(self, record):
        if record.levelno <= logging.DEBUG:
            return colorama.Style.DIM + colorama.Fore.RESET #pylint: disable=no-member
        elif record.levelno >= logging.CRITICAL:
            return colorama.Style.BRIGHT + colorama.Fore.RED #pylint: disable=no-member
        elif record.levelno >= logging.ERROR:
            return colorama.Style.NORMAL + colorama.Fore.RED #pylint: disable=no-member
        elif record.levelno >= logging.WARNING:
            return colorama.Style.NORMAL + colorama.Fore.YELLOW #pylint: disable=no-member
        return colorama.Style.NORMAL + colorama.Fore.RESET #pylint: disable=no-member

    def format(self, record):
        s = ''
        s += self.levelStyle(record)
        s += record.levelname.lower()
        s += colorama.Fore.RESET + ':' #pylint: disable=no-member
        if record.levelno <= logging.DEBUG:
            s += record.name + ': '
        else:
            s += ' '
        s += self.messageStyle(record)
        s += record.getMessage()

        s += colorama.Style.RESET_ALL #pylint: disable=no-member
        return s

class PlainFormatter(logging.Formatter):
    def __init__(self):
        super(PlainFormatter, self).__init__()

    def format(self, record):
        return record.levelname.lower() + ': ' + record.getMessage()

def init(level=0, enable_subsystems=[], plain=False):
    level = int(round(level))
    # once logging.something has been called you have to remove all logging
    # handlers before re-configing...
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)

    # set new handler with our formatter
    handler = logging.StreamHandler()
    if plain:
        handler.setFormatter(PlainFormatter())
    else:
        handler.setFormatter(FancyFormatter())
    root.addHandler(handler)

    # set appropriate levels on subsystem loggers - maybe selective logging
    # should use filters instead?
    if enable_subsystems and len(enable_subsystems):
        for subsys in enable_subsystems:
            logging.getLogger(subsys).setLevel(level)
    else:
        logging.getLogger().setLevel(level)
