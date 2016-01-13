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

_enabled_subsystems = []
_level = 0
_plain = False

def init(level=0, enable_subsystems=[], plain=False):
    global _enabled_subsystems
    global _level
    global _plain
    _enabled_subsystems = enable_subsystems
    _level = int(round(level))
    _plain = plain
    # once logging.something has been called you have to remove all logging
    # handlers before re-configing...
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)

    # set new handler with our formatter
    handler = logging.StreamHandler()
    if _plain:
        handler.setFormatter(PlainFormatter())
    else:
        handler.setFormatter(FancyFormatter())
    root.addHandler(handler)

    setLevel(_level)

def setPlain(plain):
    global _plain
    _plain = plain
    init(level=_level, enable_subsystems=_enabled_subsystems, plain=plain)

def setEnabledModules(subsystems):
    global _enabled_subsystems
    _enabled_subsystems = subsystems
    setLevel(_level)

def setLevel(level):
    global _level
    _level = level
    # set appropriate levels on subsystem loggers - maybe selective logging
    # should use filters instead?
    if _enabled_subsystems and len(_enabled_subsystems):
        logging.getLogger().setLevel(logging.INFO)
        for subsys in _enabled_subsystems:
            logging.getLogger(subsys).setLevel(level)
    else:
        logging.getLogger().setLevel(level)


