# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library options
from argparse import Action, SUPPRESS


class RegistryAction(Action):
    def __init__(self, *args, **kwargs):
        kwargs['nargs'] = 1
        self.dest = kwargs['dest']
        super(RegistryAction, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values[0])

def addTo(parser):
    parser.add_argument(
        '--registry', default=None, dest='registry', help=SUPPRESS,
        action=RegistryAction
    )
