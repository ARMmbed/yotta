# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library options
from argparse import Action, SUPPRESS

# logging setup, , setup the logging system, internal
from yotta.lib import logging_setup

class DebugSubsystemsAction(Action):
    def __init__(self, *args, **kwargs):
        self.subsystems = []
        kwargs['nargs'] = 1
        super(DebugSubsystemsAction, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        self.subsystems += values
        logging_setup.setEnabledModules(self.subsystems)

def addTo(parser):
    parser.add_argument('-d', '--debug', action=DebugSubsystemsAction,
        metavar='SUBSYS',
        help=SUPPRESS
        #help='specify subsystems to debug: use in conjunction with -v to '+
        #     'increase the verbosity only for specified subsystems'
    )

