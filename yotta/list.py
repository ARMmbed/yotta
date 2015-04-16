# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
from __future__ import print_function
import argparse
import logging
import os

# colorama, BSD 3-Clause license, cross-platform terminal colours, pip install colorama 
import colorama

# validate, , validate things, internal
from .lib import validate
# Target, , represents an installed target, internal
from .lib import target
# access, , get components (and check versions), internal
from .lib import access
from .lib import access_common
# fsutils, , misc filesystem utils, internal
from .lib import fsutils

def addOptions(parser):
    parser.add_argument('--all', '-a', dest='show_all', default=False, action='store_true',
        help='Show all dependencies (including repeats, and test-only dependencies)'
    )

def execCommand(args, following_args):
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
        available_components = [(c.getName(), c)],
                        test = True
    )
    printComponentDepsRecursive(c, dependencies, [c.getName()], target, args.show_all)



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
    if u'unicode' in str(type(x)):
        # python 2.7
        print(x.encode('utf-8'))
    else:
        print(x)

def relpathIfSubdir(path):
    relpath = os.path.relpath(path)
    if relpath.startswith('..'):
        return path
    else:
        return relpath

if os.name == 'nt':
    # don't even try to do Unicode on windows. Even if we can encode it
    # correctly, the default terminal fonts don't support Unicode characters :(
    L_Char = u'\\'
    T_Char = u'|'
    Dash_Char = u'_'
    Pipe_Char = u'|'
else:
    L_Char = u'\u2517'
    T_Char = u'\u2523'
    Dash_Char = u'\u2500'
    Pipe_Char = u'\u2503'

def printComponentDepsRecursive(
        component,
        all_components,
        processed,
        target,
        list_all,
        indent=u'',
        tee=u'',
        installed_at=u'',
        test_dep=False
):
    DIM    = colorama.Style.DIM
    BRIGHT = colorama.Style.BRIGHT
    GREEN  = colorama.Fore.GREEN
    RED    = colorama.Fore.RED
    RESET  = colorama.Style.RESET_ALL

    mods_path = component.modulesPath()
    deps = component.getDependencies(
            available_components = all_components,
                          target = target,
                            test = True,
                        warnings = False
    )
    specs = dict([(x.name, x) for x in component.getDependencySpecs(target=target)])

    def isTestOnly(name):
        return specs[name].is_test_dependency

    def shouldDisplay(x):
        if list_all:
            # list everything everywhere (apart from test dependencies of test
            # dependencies, which should be considered irrelevant)
            if component.isTestDependency() and isTestOnly(x[0]):
                return False
            else:
                return True
        if (not isTestOnly(x[0]) or not len(indent)):
            # this is non-test dependency, or a top-level test dependency
            if not x[1]:
                # if it's missing, display it
                return True
            if x[1].path == os.path.join(mods_path, x[0]):
                # if it's installed in this module, display it
                return True
            if x[0] in deps_here:
                # if it's first depended on by this module, then display it
                return True
        # everything else shouldn't be displayed here
        return False


    line = indent[:-2] + tee + component.getName() + u' ' + DIM + str(component.getVersion()) + RESET

    if test_dep:
        line += u' ' + DIM + u'(test dependency)' + RESET
    if len(installed_at):
        line += u' ' + DIM + installed_at + RESET
    if component.installedLinked():
        line += GREEN + BRIGHT + u' -> ' + RESET + GREEN + fsutils.realpath(component.path) + RESET

    putln(line)
    
    deps_here  = [x for x in list(deps.keys()) if (x not in processed)]
    print_deps = [x for x in list(deps.items()) if shouldDisplay(x)]
    
    processed += [x[0] for x in print_deps]
    

    for (name, dep), last in islast(print_deps):
        if last:
            next_indent = indent + u'  '
            tee = L_Char + Dash_Char + u' '
            next_tee = L_Char + Dash_Char + u' '
        else:
            next_indent = indent + Pipe_Char + u' '
            tee = T_Char + Dash_Char + u' '
            next_tee = T_Char + Dash_Char + u' '
        test_dep_status = u''
        if isTestOnly(name):
            test_dep_status = u' (test dependency)'

        if not dep:
            putln(indent + tee + name + u' ' + specs[name].version_req + test_dep_status + BRIGHT + RED + ' missing' + RESET)
        else:
            spec = access.remoteComponentFor(name, specs[name].version_req, 'modules').versionSpec()
            if not spec:
                spec_descr = u''
            elif spec.match(dep.getVersion()):
                spec_descr = u' ' + str(spec)
            else:
                spec_descr = u' ' + RESET + BRIGHT + RED + str(spec)
            spec_descr += test_dep_status

            if name in deps_here:
                # dependencies that are first used here may actually be
                # installed higher up our dependency tree, if they are,
                # illustrate that:
                if dep.path == os.path.join(mods_path, name):
                    printComponentDepsRecursive(
                                   dep,
                        all_components,
                             processed,
                                target,
                              list_all,
                           next_indent,
                              next_tee,
                              test_dep = isTestOnly(name)
                    )
                else:
                    printComponentDepsRecursive(
                                   dep,
                        all_components,
                             processed,
                                target,
                              list_all,
                           next_indent,
                              next_tee,
                          installed_at = relpathIfSubdir(dep.path),
                              test_dep = isTestOnly(name)
                    )
            else:
                putln(indent + tee + DIM + name + spec_descr + RESET)

