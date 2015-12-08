# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library options
from argparse import Action

class Noninteractive(Action):
    def __init__(self, *args, **kwargs):
        kwargs['nargs'] = 0
        kwargs['metavar'] = None
        self.dest = kwargs['dest']
        super(Noninteractive, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, False)

def addTo(parser):
    parser.add_argument('--noninteractive', '-n', dest='interactive',
        action=Noninteractive, default=True,
        help="Do not wait for user interaction (for example to log in), fail instead."
    )

