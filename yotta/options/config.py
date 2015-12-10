# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library options
from argparse import Action, ArgumentError


class ConfigAction(Action):
    def __init__(self, *args, **kwargs):
        kwargs['nargs'] = 1
        self.dest = kwargs['dest']
        super(ConfigAction, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        # delay importing target module until this option is used, as the
        # import would otherwise be unnecessary, and drag the target module
        # into being synchrously imported into main
        from yotta.lib import target
        error, config = target.loadAdditionalConfig(values[0])
        if error:
            raise ArgumentError(self, error)
        else:
            setattr(namespace, self.dest, config)

def addTo(parser):
    parser.add_argument(
        '--config', default=None, dest='config', help=
        "Specify the path to a JSON configuration file to extend the build "+
        "configuration provided by the target. This is most useful for "+
        "ensuring test coverage of the ways that different targets will "+
        "cause the module to build without building for different targets",
        metavar="path/to/config.json",
        action=ConfigAction
    )
