# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# yotta internal modules:
from . import list as yotta_list
from .lib import ordered_json
# validate, , validate things, internal
from .lib import validate

def addOptions(parser):
    pass

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

    installed_modules = c.getDependenciesRecursive(
                      target = target,
        available_components = [(c.getName(), c)],
                        test = True
    )

    dependency_list = yotta_list.resolveDependencyGraph(target, c, installed_modules)

    # !!! TODO: missing dependencies, or unmet specifications should cause failure

    with open('yotta-shrinkwrap.json', 'w') as f:
        f.write(ordered_json.dumps(filterForShrinkwrap(dependency_list)))

def filterForShrinkwrap(dependency_list):
    def filterModule(mod):
        return { k: mod[k] for k in ('name', 'version') if k in mod }

    dependency_list['modules'] = [
        filterModule(mod) for mod in dependency_list['modules']
    ]

    return dependency_list
