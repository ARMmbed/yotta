# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
from __future__ import print_function
import re
import logging
import os

# colorama, BSD 3-Clause license, cross-platform terminal colours, pip install colorama
import colorama

# settings, , load and save settings, internal
from yotta.lib import settings
# Target, , represents an installed target, internal
from yotta.lib import target
# Component, , represents an installed component, internal
from yotta.lib import component
# fsutils, , misc filesystem utils, internal
from yotta.lib import fsutils

# OK this is a pretty terrible validation regex... should find a proper module
# to do this
Target_RE = re.compile('^('+
    '[a-z]+[a-z0-9+-]*('+
        ',[a-zA-Z0-9-]+/[a-zA-Z0-9-]+' +'|'+ '([a-zA-Z0-9_-]*@)?[a-zA-Z0-9_+-]+://.*' + '|' + '[a-z0-9.-]*'+
    ')?'+
')$')


def addOptions(parser):
    parser.add_argument('set_target', default=None, nargs='?',
        # targetname,versionspec_or_url is supported too
        help='set the build target to this (targetname[@versionspec_or_url])'
    )
    parser.add_argument('-g', '--global', dest='save_global',
        default=False, action='store_true',
        help='set globally (in the per-user settings) instead of locally to this directory'
    )
    parser.add_argument('-n', '--no-install', dest='no_install',
        default=False, action='store_true',
        help='do not immediately download the target description'
    )


def displayCurrentTarget(args):
    if not args.plain:
        DIM    = colorama.Style.DIM       #pylint: disable=no-member
        BRIGHT = colorama.Style.BRIGHT    #pylint: disable=no-member
        GREEN  = colorama.Fore.GREEN      #pylint: disable=no-member
        RED    = colorama.Fore.RED        #pylint: disable=no-member
        RESET  = colorama.Style.RESET_ALL #pylint: disable=no-member
    else:
        DIM = BRIGHT = GREEN = RED = RESET = u''

    line = u''

    c = component.Component(os.getcwd())
    if c.isApplication():
        app_path = c.path
    else:
        app_path = None

    derived_target, errors = target.getDerivedTarget(
        args.target, c.targetsPath(), application_dir=app_path, install_missing=False, shrinkwrap=c.getShrinkwrap()
    )
    for error in errors:
        logging.error(error)

    if derived_target is None:
        line = BRIGHT + RED + args.target + u' missing' + RESET
    else:
        for t in derived_target.hierarchy:
            if len(line):
                line += '\n'
            if t:
                line += t.getName() + DIM + u' ' + str(t.getVersion()) + RESET
                if t.installedLinked():
                    line += GREEN + BRIGHT + u' -> ' + RESET + GREEN + fsutils.realpath(t.path)
            else:
                line += BRIGHT + RED + t.getName() + DIM + u' ' + str(t.getVersion()) + BRIGHT + u' missing'
            line += RESET
        base_spec = t.baseTargetSpec()
        if base_spec:
            # if the last target in the hierarchy has a base spec, then the
            # hierarchy is incomplete:
            line += '\n' + BRIGHT + RED + base_spec.name + u' ' + base_spec.versionReq() + u' missing'

    if u'unicode' in str(type(line)):
        # python 2.7
        print(line.encode('utf-8'))
    else:
        print(line)
    return len(errors)


def execCommand(args, following_args):
    if args.set_target is None:
        return displayCurrentTarget(args)
    else:
        from yotta.lib import sourceparse
        from yotta.lib import validate

        name, spec = sourceparse.parseTargetNameAndSpec(args.set_target)
        if not re.match(validate.Target_Name_Regex, name):
            logging.error('Invalid target name: "%s" should use only a-z 0-9 - and +, and start with a letter.' % name)
            return 1
        if not sourceparse.isValidSpec(spec):
            logging.error('Could not parse target version specification: "%s"' % spec)
            return 1

        # separating the target name and spec is still done with a comma
        # internally (for now at least), although @ is the recommended way to
        # set it:
        t = '%s,%s' % (name, spec)

        settings.setProperty('build', 'target', t, not args.save_global)
        settings.setProperty('build', 'targetSetExplicitly', True, not args.save_global)
        if not args.no_install:
            # if we have a module in the current directory, try to make sure
            # this target is installed
            c = component.Component(os.getcwd())
            if c:
                target, errors = c.satisfyTarget(t)
                for err in errors:
                    logging.error(err)
                if len(errors):
                    logging.error('NOTE: use "yotta link-target" to test a locally modified target prior to publishing.')
                    return 1
        return 0
