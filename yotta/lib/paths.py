# Copyright 2014-2017 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

import os

# this module to provide tools for path manipulation and caching
BUILD_OUTPUT_KEY = 'folder'
PARSER_OUTPUT_FOLDER_KWARGS = dict
Modules_Folder = 'yotta_modules'
Targets_Folder = 'yotta_targets'


def add_parser_argument(parser):
    parser.add_argument(
        '-o',
        '--output-folder',
        dest='output_folder',
        default=None,
        help=(
            'Customise the build directory (default: ./build/<target>)'
            'Must be inside the project directory.'
        ),
        metavar='path/to/output/folder'
    )


def get_configured_output_path(args, target=None):
    '''common method for setting/loading/defaulting a build output path'''
    from yotta.lib import settings

    args = vars(args)
    current = os.getcwd()
    from_settings = settings.getProperty('build', BUILD_OUTPUT_KEY)

    # load from command line or local config
    path = args.get('output_folder') or from_settings

    # else organise directories by target name in cwd
    if not path and target:
        path = os.path.join(current, 'build', target.getName())

    path = os.path.relpath(path, start=current)

    if not os.path.abspath(path).startswith(current):
        raise ValueError(
            'The build output directory must be a subdirectory to this project'
            ' (requested: %s)'
            % path
        )

    if path != from_settings:
        settings.setProperty('build', BUILD_OUTPUT_KEY, path, True)
    return path
