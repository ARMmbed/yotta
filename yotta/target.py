# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
from __future__ import print_function
import re
import logging

# settings, , load and save settings, internal
from .lib import settings


# OK this is a pretty terrible validation regex... should find a proper module
# to do this
Target_RE = re.compile('^('+
    '[a-z0-9-]+,?('+
        '[a-zA-Z0-9-]+/[a-zA-Z0-9-]+' +'|'+ '([a-zA-Z0-9_-]*@)?[a-zA-Z0-9_+-]+://.*' + '|' + '[a-z0-9.-]*'+
    ')?'+
')$')


def addOptions(parser):
    parser.add_argument('set_target', default=None, nargs='?',
        help='set the build target to this (targetname[,versionspec_or_url])'
    )
    parser.add_argument('-g', '--global', dest='save_global',
        default=False, action='store_true',
        help='set globally (in the per-user settings) instead of locally to this directory'
    )

    # FIXME: need help that lists possible targets, and we need a walkthrough
    # guide to forking a new target for an existing board
    #
    # (the description of a target should have a list of things that it's
    #  similar to, e.g. objectador is similar to EFM32gg990f, #  EFM32gg,
    #  Cortex-M3, ARMv8, ARM)

    # FIXME: per-program target setting (per-program settings files?)
    #parser.add_argument('--global', '-g', dest='act_globally', default=False, action='store_true',
    #    help='Install globally instead of in the current working directory.'
    #)


def execCommand(args, following_args):
    if args.set_target is None:
        print(args.target)
    else:
        if not Target_RE.match(args.set_target):
            logging.error('''Invalid target: "%s"''' % args.set_target)#, targets must be one of:
            #
            #    a valid name (lowercase letters, numbers, and hyphen)
            #    a github ref (owner/project)
            #    a valid url
            #
            #Note that to use a local directory as a target you can use
            #
            #    # in the directory containing the target package:
            #    yotta link target
            #
            #    # then in the directory of the application to use the target:
            #    yotta link target {targetname}
            #    yotta target {targetname}
            #
            #''')
        else:
            if args.set_target.find(',') == -1:
                target = args.set_target + ',*'
            else:
                target = args.set_target
            settings.setProperty('build', 'target', target, not args.save_global)
