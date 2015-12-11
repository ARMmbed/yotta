# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library options
from argparse import Action

# logging setup, , setup the logging system, internal
from yotta.lib import logging_setup

class PlainAction(Action):
    def __init__(self, *args, **kwargs):
        kwargs['nargs'] = 0
        kwargs['metavar'] = None
        self.dest = kwargs['dest']
        super(PlainAction, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, True)
        logging_setup.setPlain(True)

def addTo(parser):
    parser.add_argument('--plain', dest='plain', action=PlainAction,
        default=None, help="Use a simple output format with no colours"
    )

