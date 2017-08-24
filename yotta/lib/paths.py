# Copyright 2014-2017 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import os

# settings, , load and save settings, internal
from yotta.lib import settings

# this module to provide tools for path manipulation and caching

BUILD_OUTPUT_KEY = 'folder'
PARSER_OUTPUT_FOLDER_KWARGS = dict


def add_parser_argument(parser):
    parser.add_argument(
        '-o',
        '--output-folder',
        dest='output_folder',
        default=None,
        help='Specify a build output folder instead of ./build/<target>',
        metavar='path/to/output/folder'
    )


def get_configured_output_path(args, target=None):
    '''common method for setting/loading/defaulting a build output path'''
    args = vars(args)

    # load from command line or local config
    path = args.get('output_folder') or settings.getProperty('build', BUILD_OUTPUT_KEY)

    # else organise directories by target name in cwd
    if not path and target:
        path = os.path.join(os.getcwd(), 'build', target.getName())

    path = os.path.abspath(path)
    # could skip this if path==current ... is performance super important here?
    settings.setProperty('build', BUILD_OUTPUT_KEY, path, True)
    return path
