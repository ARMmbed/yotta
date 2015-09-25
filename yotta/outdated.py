# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules
import logging

# colorama, BSD 3-Clause license, cross-platform terminal colours, pip install colorama
import colorama

# validate, , validate things, internal
from .lib import validate
# access, , get components, internal
from .lib import access

def addOptions(parser):
    pass

def execCommand(args, following_args):
    c = validate.currentDirectoryModule()
    if not c:
        return 1

    target, errors = c.satisfyTarget(args.target)
    if errors:
        for error in errors:
            logging.error(error)
        return 1

    dependencies = c.getDependenciesRecursive(
                      target = target,
        available_components = [(c.getName(), c)],
                        test = True
    )

    return displayOutdated(dependencies, use_colours=(not args.plain))

def displayOutdated(modules, use_colours):
    ''' print information about outdated modules,
        return 0 if there is nothing to be done and nonzero otherwise
    '''
    if use_colours:
        DIM    = colorama.Style.DIM       #pylint: disable=no-member
        BRIGHT = colorama.Style.BRIGHT    #pylint: disable=no-member
        YELLOW = colorama.Fore.YELLOW     #pylint: disable=no-member
        RED    = colorama.Fore.RED        #pylint: disable=no-member
        GREEN  = colorama.Fore.GREEN      #pylint: disable=no-member
        RESET  = colorama.Style.RESET_ALL #pylint: disable=no-member
    else:
        DIM = BRIGHT = YELLOW = RED = RESET = u''

    status = 0

    for name, m in modules.items():
        if m.isTestDependency():
            continue
        latest_v = access.latestSuitableVersion(name, '*', registry='modules', quiet=True)
        if not m:
            m_version = u' ' + RESET + BRIGHT + RED + u"missing" + RESET
        else:
            m_version = DIM + u'@%s' % (m.version)
        if not latest_v:
            print(u'%s%s%s not available from the registry%s' % (RED, name, m_version, RESET))
            status = 2
            continue
        elif not m or m.version < latest_v:
            if m:
                if m.version.major() < latest_v.major():
                    # major versions being outdated might be deliberate, so not
                    # that bad:
                    colour = GREEN
                elif m.version.minor() < latest_v.minor():
                    # minor outdated versions is moderately bad
                    colour = YELLOW
                else:
                    # patch-outdated versions is really bad, because there should
                    # be no reason not to update:
                    colour = RED
            else:
                colour = RED
            print(u'%s%s%s latest: %s%s%s' % (name, m_version, RESET, colour, latest_v.version, RESET))
            if not status:
                status = 1
    return status


