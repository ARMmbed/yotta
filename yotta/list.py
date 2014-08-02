# standard library modules, , ,
import argparse
import logging
import os

# colorama, BSD 3-Clause license, cross-platform terminal colours, pip install colorama 
import colorama

# Component, , represents an installed component, internal
from lib import component
# Target, , represents an installed target, internal
from lib import target


def addOptions(parser):
    parser.add_argument('--all', '-a', dest='show_all', default=False, action='store_true',
        help='Show all dependencies (including repeats)'
    )

def execCommand(args):
    wd = os.getcwd()
    c = component.Component(wd)

    if not c:
        logging.debug(str(c.getError()))
        logging.error('The current directory does not contain a valid component.')
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

def printComponentDepsRecursive(component, all_components, target, all, indent=u'', tee=u''):
    mods_path = component.modulesPath()
    deps = component.getDependencies(
            available_components = all_components,
                          target = target
    )

    line = indent[:-2] + tee + component.getName() + ' ' + colorama.Style.DIM + str(component.getVersion()) + colorama.Style.RESET_ALL
    if component.installedLinked():
        line += colorama.Style.BRIGHT + colorama.Fore.GREEN + ' -> ' + colorama.Style.DIM + component.path + colorama.Style.RESET_ALL 

    print line

    for (name, dep), last in islast(filter(lambda x: all or (not x[1]) or x[1].path == os.path.join(mods_path, x[0]), deps.items(), )):
        if last:
            next_indent = indent + u'  '
            tee = u'\u2517\u2500 '
            next_tee = u'\u2517\u2500 '
        else:
            next_indent = indent + u'\u2503 '
            tee = u'\u2523\u2500 '
            next_tee = u'\u2520\u2500 '
        if not dep:
            print indent + tee + name + colorama.Style.BRIGHT + colorama.Fore.RED + ' missing' + colorama.Style.RESET_ALL 
        elif dep.path == os.path.join(mods_path, name):
            printComponentDepsRecursive(dep, all_components, target, all, next_indent, next_tee)
        else:
            print indent + tee + colorama.Style.DIM + name + colorama.Style.RESET_ALL 

