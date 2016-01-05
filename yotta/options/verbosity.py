# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library options
from argparse import Action, SUPPRESS
import logging

# logging setup, , setup the logging system, internal
from yotta.lib import logging_setup

def logLevelFromVerbosity(v):
    if v >= 4:
        return logging.NOTSET
    elif v == 3:
        return logging.DEBUG
    elif v == 2:
        return logging.DEBUG+3
    elif v == 1:
        return logging.DEBUG+7
    else:
        return logging.INFO

class VerbosityAction(Action):
    def __init__(self, *args, **kwargs):
        self.level = 0
        kwargs['nargs'] = 0
        kwargs['dest'] = SUPPRESS
        super(VerbosityAction, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        self.level += 1
        loglevel = logLevelFromVerbosity(self.level)
        logging_setup.setLevel(loglevel)

def addTo(parser):
    parser.add_argument('-v', '--verbose', action=VerbosityAction,
        default=0,
        help='increase verbosity: can be used multiple times'
    )
