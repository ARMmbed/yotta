# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import os

# validate, , validate things, internal
from yotta.lib import validate

# fsutils, , misc filesystem utils, internal
from yotta.lib import fsutils

# paths
from yotta.lib import paths


def addOptions(parser):
    paths.add_parser_argument(parser)


def execCommand(args, following_args):
    paths_to_remove = []

    current = validate.currentDirectoryModule()
    if current:
        paths_to_remove.append(os.path.join(current.path, 'build'))

    specific = paths.get_configured_output_path(args)
    if specific:
        paths_to_remove.append(specific)

    for path in paths_to_remove:
        if os.path.exists(path) and not validate.directoryModule(path):
            print('removing: %s' % path)
            fsutils.rmRf(path)
