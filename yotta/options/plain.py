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

class ColourfulAction(PlainAction):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, False)
        logging_setup.setPlain(False)


def addTo(parser):
    parser.add_argument('--plain', dest='plain', action=PlainAction,
        default=logging_setup.plainOutputByDefault(), nargs=0, help="Use a simple output format with no colours."
    )
    parser.add_argument('--colourful', dest='plain', action=ColourfulAction,
        default=(not logging_setup.plainOutputByDefault()), nargs=0, help="Force colourful output, even if the output is not to a tty."
    )

