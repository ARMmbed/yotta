# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import argparse
import logging
import os

# colorama, BSD 3-Clause license, cross-platform terminal colours, pip install colorama 
import colorama

# validate, , validate things, internal
from lib import validate
# Target, , represents an installed target, internal
from lib import target
# access, , get components (and check versions), internal
from lib import access
from lib import access_common

def addOptions(parser):
    parser.add_argument('--all', '-a', dest='show_all', default=False, action='store_true',
        help='Show all dependencies (including repeats)'
    )

def execCommand(args):
    wd = os.getcwd()

    c = validate.currentDirectoryModule()
    if not c:
        return 1

    if not args.target:
        logging.error('No target has been set, use "yotta target" to set one.')
        return 1

    target, errors = c.satisfyTarget(args.target)
    if errors:
        for error in errors:
            logging.error(error)
        return 1

    dependencies = c.getDependenciesRecursive(
                      target = target,
        available_components = [(c.getName(), c)]
    )
    printComponentDepsRecursive(c, dependencies, target, args.show_all)



def islast(generator):
    next_x = None
    first = True
    for x in generator:
        if not first:
            yield (next_x, False)
        next_x = x
        first = False
    if not first:
        yield (next_x, True)

def putln(x):
    print x.encode('utf-8')

def printComponentDepsRecursive(component, all_components, target, all, indent=u'', tee=u''):
    mods_path = component.modulesPath()
    deps = component.getDependencies(
            available_components = all_components,
                          target = target
    )
    specs = dict(component.getDependencySpecs(target=target))

    line = indent[:-2] + tee + component.getName() + ' ' + colorama.Style.DIM + str(component.getVersion()) + colorama.Style.RESET_ALL
    if component.installedLinked():
        line += colorama.Style.BRIGHT + colorama.Fore.GREEN + ' -> ' + colorama.Style.DIM + component.path + colorama.Style.RESET_ALL 

    putln(line)
    

    print_deps = filter(lambda x: all or (not x[1]) or x[1].path == os.path.join(mods_path, x[0]) or x[1].installedLinked(), deps.items())

    for (name, dep), last in islast(print_deps):
        if last:
            next_indent = indent + u'  '
            tee = u'\u2517\u2500 '
            next_tee = u'\u2517\u2500 '
        else:
            next_indent = indent + u'\u2503 '
            tee = u'\u2523\u2500 '
            next_tee = u'\u2520\u2500 '
        if not dep:
            putln(indent + tee + name + u' ' + specs[name] + colorama.Style.BRIGHT + colorama.Fore.RED + ' missing' + colorama.Style.RESET_ALL)
        else:
            spec = access.remoteComponentFor(name, specs[name], 'modules').versionSpec()
            if not spec:
                spec_descr = u''
            elif spec.match(dep.getVersion()):
                spec_descr = u' ' + str(spec)
            else:
                spec_descr = u' ' + colorama.Style.RESET_ALL + colorama.Style.BRIGHT + colorama.Fore.RED + str(spec)

            if dep.path == os.path.join(mods_path, name):
                printComponentDepsRecursive(dep, all_components, target, all, next_indent, next_tee)
            else:
                putln(indent + tee + colorama.Style.DIM + name + spec_descr + colorama.Style.RESET_ALL)

