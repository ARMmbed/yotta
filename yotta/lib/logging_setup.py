# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import logging

# colorama, BSD 3-Clause license, cross-platform terminal colours, pip install colorama 
import colorama


# colorama replaces stdout and stderr with objects that do switch colour
# sequences to the appropriate windows ones, we do most of our stdout through
# logging, so setup that proxying here:
colorama.init()

class Formatter(logging.Formatter):
    def __init__(self):
        super(Formatter, self).__init__()

    def levelStyle(self, record):
        if record.levelno <= logging.DEBUG:
            return colorama.Style.DIM + colorama.Fore.RESET
        elif record.levelno >= logging.CRITICAL:
            return colorama.Style.BRIGHT + colorama.Fore.RED
        elif record.levelno >= logging.ERROR:
            return colorama.Style.BRIGHT + colorama.Fore.RED
        elif record.levelno >= logging.WARNING:
            return colorama.Style.BRIGHT + colorama.Fore.YELLOW
        return colorama.Style.NORMAL + colorama.Fore.GREEN

    def messageStyle(self, record):
        if record.levelno <= logging.DEBUG:
            return colorama.Style.DIM + colorama.Fore.RESET
        elif record.levelno >= logging.CRITICAL:
            return colorama.Style.BRIGHT + colorama.Fore.RED
        elif record.levelno >= logging.ERROR:
            return colorama.Style.NORMAL + colorama.Fore.RED
        elif record.levelno >= logging.WARNING:
            return colorama.Style.NORMAL + colorama.Fore.YELLOW
        return colorama.Style.NORMAL + colorama.Fore.RESET

    def format(self, record):
        s = ''
        s += self.levelStyle(record)
        s += record.levelname.lower()
        s += colorama.Fore.RESET + ':'
        if record.levelno <= logging.DEBUG:
            s += record.name + ': '
        else:
            s += ' '
        s += self.messageStyle(record)
        s += record.getMessage()

        s += colorama.Style.RESET_ALL
        return s

def init(level=0, enable_subsystems=[]):
    level = int(round(level))
    # once logging.something has been called you have to remove all logging
    # handlers before re-configing...
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)

    # set new handler with our formatter
    handler = logging.StreamHandler()
    handler.setFormatter(Formatter())
    root.addHandler(handler)
    
    # set appropriate levels on subsystem loggers - maybe selective logging
    # should use filters instead?
    if enable_subsystems and len(enable_subsystems):
        for subsys in enable_subsystems:
            logging.getLogger(subsys).setLevel(level)
    else:
        logging.getLogger().setLevel(level)
