# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
from __future__ import print_function
import logging
import os
import json

# colorama, BSD 3-Clause license, cross-platform terminal colours, pip install colorama
import colorama

# validate, , validate things, internal
from .lib import validate
# utils, , miscellaneous utilities, internal
from .lib.utils import islast
# access, , get components (and check versions), internal
from .lib import access
# fsutils, , misc filesystem utils, internal
from .lib import fsutils
# Registry Access, , access packages in the registry, internal
from .lib.registry_access import friendlyRegistryName
# --config option, , , internal
from . import options

def addOptions(parser):
    options.config.addTo(parser)
    parser.add_argument('--all', '-a', dest='show_all', default=False, action='store_true',
        help='Show all dependencies (including repeats, and test-only dependencies)'
    )
    parser.add_argument('--display-origin', '-i', dest='display_origin',
        default=False, action='store_true',
        help='Display where modules were originally downloaded from (implied by --all).'
    )
    parser.add_argument('--json', '-j', dest='json', default=False, action='store_true',
        help='Output json representation of dependencies.'
    )

def execCommand(args, following_args):
    c = validate.currentDirectoryModule()
    if not c:
        return 1

    if not args.target:
        logging.error('No target has been set, use "yotta target" to set one.')
        return 1

    target, errors = c.satisfyTarget(args.target, additional_config=args.config)
    if errors:
        for error in errors:
            logging.error(error)
        return 1

    if args.show_all:
        args.display_origin = True

    dependencies = c.getDependenciesRecursive(
                      target = target,
        available_components = [(c.getName(), c)],
                        test = True
    )
    if args.json:
        putln(formatJsonDeps(target, dependencies, args.show_all))
    else:
        putln(
            ComponentDepsFormatter(
                               target = target,
                 available_components = dependencies,
                                plain = args.plain,
                             list_all = args.show_all,
                       display_origin = args.display_origin
            ).format(
                c, [c.getName()]
            )
        )

def formatJsonDeps(target, available_components, list_all):
    d = {}
    for c in available_components:
        co = available_components[c]
        d[c] = {}
        d[c]['name'] = co.getName()
        d[c]['version'] = str(co.getVersion())
        d[c]['dependencies'] = {}
        for dep in co.getDependencySpecs(target=target):
            depcomp = available_components[dep.name]
            spec = access.remoteComponentFor(dep.name, dep.version_req, 'modules').versionSpec()
            dd = {
                'verspec':dep.version_req,
                   'test':dep.is_test_dependency,
                'missing':not available_components[dep.name],
               'mismatch':not spec.match(depcomp.getVersion()),
                   'link':co.installedLinked()
            }
            d[c]['dependencies'][dep.name]=dd
    return json.dumps(d)

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

class ComponentDepsFormatter(object):
    def __init__(self, target=None, available_components=None, list_all=False, plain=False, display_origin=False):
        # don't even try to do Unicode on windows. Even if we can encode it
        # correctly, the default terminal fonts don't support Unicode
        # characters :(
        self.use_unicode = not ((os.name == 'nt') or plain)
        self.use_colours = not plain
        self.target    = target
        self.list_all  = list_all
        self.available = available_components
        self.display_origin = display_origin
        if plain:
            self.L_Char = u' '
            self.T_Char = u' '
            self.Dash_Char = u' '
            self.Pipe_Char = u' '
        elif self.use_unicode:
            self.L_Char = u'\u2517'
            self.T_Char = u'\u2523'
            self.Dash_Char = u'\u2501'
            self.Pipe_Char = u'\u2503'
        else:
            self.L_Char = u'\\'
            self.T_Char = u'|'
            self.Dash_Char = u'_'
            self.Pipe_Char = u'|'
        super(ComponentDepsFormatter, self).__init__()

    def format(
        self,
        component,
        processed,
        indent=u'',
        tee=u'',
        installed_at=u'',
        test_dep=False,
        spec=None
    ):
        r = u''

        if self.use_colours:
            DIM    = colorama.Style.DIM       #pylint: disable=no-member
            BRIGHT = colorama.Style.BRIGHT    #pylint: disable=no-member
            GREEN  = colorama.Fore.GREEN      #pylint: disable=no-member
            RED    = colorama.Fore.RED        #pylint: disable=no-member
            RESET  = colorama.Style.RESET_ALL #pylint: disable=no-member
        else:
            DIM = BRIGHT = GREEN = RED = RESET = u''

        mods_path = component.modulesPath()
        deps = component.getDependencies(
                available_components = self.available,
                              target = self.target,
                                test = True,
                            warnings = False
        )
        specs = dict([(x.name, x) for x in component.getDependencySpecs(target=self.target)])

        def isTestOnly(name):
            return specs[name].is_test_dependency

        def shouldDisplay(x):
            if self.list_all:
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

        origin_descr = ''
        if self.display_origin:
            origin = component.origin()
            if origin is not None:
                if origin.startswith('github://'):
                    origin_descr = ' (' + origin[9:] + ')'
                else:
                    origin_descr = ' (' + friendlyRegistryName(origin, short=True) + ')'

        line = indent[:-2] + tee + component.getName() + u' ' + DIM + str(component.getVersion()) + origin_descr + RESET

        if spec and not spec.match(component.getVersion()):
            line += u' ' + RESET + BRIGHT + RED + str(spec) + RESET
        if test_dep:
            line += u' ' + DIM + u'(test dependency)' + RESET
        if len(installed_at):
            line += u' ' + DIM + installed_at + RESET
        if component.installedLinked():
            line += GREEN + BRIGHT + u' -> ' + RESET + GREEN + fsutils.realpath(component.path) + RESET

        r += line + '\n'

        deps_here  = [x for x in list(deps.keys()) if (x not in processed)]
        print_deps = [x for x in list(deps.items()) if shouldDisplay(x)]

        processed += [x[0] for x in print_deps]


        for (name, dep), last in islast(print_deps):
            if last:
                next_indent = indent + u'  '
                tee = self.L_Char + self.Dash_Char + u' '
                next_tee = self.L_Char + self.Dash_Char + u' '
            else:
                next_indent = indent + self.Pipe_Char + u' '
                tee = self.T_Char + self.Dash_Char + u' '
                next_tee = self.T_Char + self.Dash_Char + u' '
            test_dep_status = u''
            if isTestOnly(name):
                test_dep_status = u' (test dependency)'

            if not dep:
                r += indent + tee + name + u' ' + specs[name].version_req + test_dep_status + BRIGHT + RED + ' missing' + RESET + '\n'
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
                        r += self.format(
                                       dep,
                                 processed,
                               next_indent,
                                  next_tee,
                                  test_dep = isTestOnly(name),
                                      spec = spec
                        )
                    else:
                        r += self.format(
                                       dep,
                                 processed,
                               next_indent,
                                  next_tee,
                              installed_at = relpathIfSubdir(dep.unresolved_path),
                                  test_dep = isTestOnly(name),
                                      spec = spec
                        )
                else:
                    r += indent + tee + DIM + name + spec_descr + RESET + '\n'
        return r
