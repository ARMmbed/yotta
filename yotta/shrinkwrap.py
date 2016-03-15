# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


def addOptions(parser):
    pass

def execCommand(args, following_args):
    # standard library modules
    import logging

    # validate, , validate things, internal
    from yotta.lib import validate
    # ordered_json, , order-preserving json handling, internal
    from yotta.lib import ordered_json
    # fsutils, , filesystem utils, internal
    from yotta.lib.fsutils import rmF
    # list, , the yotta list subcommand, internal
    from yotta import list as yotta_list

    # first remove any existing shrinkwrap:
    rmF('yotta-shrinkwrap.json')

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
                        test = 'toplevel'
    )

    dependency_list = yotta_list.resolveDependencyGraph(target, c, installed_modules, test='toplevel')

    errors = checkDependenciesForShrinkwrap(dependency_list)
    if len(errors):
        logging.error("Dependency errors prevent shrinkwrap creation:")
        for error in errors:
            logging.error(error)
        logging.error("Perhaps you need to `yotta install` first?")
        return 1

    with open('yotta-shrinkwrap.json', 'w') as f:
        f.write(ordered_json.dumps(prepareShrinkwarp(dependency_list, target.hierarchy)))


def checkDependenciesForShrinkwrap(dependency_list):
    ''' return a list of errors encountered (e.g. dependency missing or
        specification not met
    '''
    # sourceparse, , parse version specifications, internall
    from yotta.lib import sourceparse
    errors = []
    # first gather the available versions of things:
    available_versions = {}
    for mod in dependency_list.get('modules', []):
        available_versions[mod['name']] = mod['version']
    # now check that the available versions satisfy all of the specifications
    # from other modules:
    for mod in dependency_list.get('modules', []):
        for spec_info in mod.get('specifications', []):
            name = spec_info['name']
            spec = spec_info['version']
            if spec_info.get('testOnly', False):
                # test-only specifications are ignored for shrinkwrap
                continue
            if not name in available_versions:
                errors.append('dependency %s (required by %s) is missing' % (
                    name, mod['name']
                ))
            else:
                available_version = available_versions[name]
                parsed_spec = sourceparse.parseSourceURL(spec)
                if not parsed_spec.semanticSpecMatches(available_version):
                    errors.append('%s@%s does not meet specification %s required by %s' % (
                        name, available_version, parsed_spec.semanticSpec(), mod['name']
                    ))

    return errors


def prepareShrinkwarp(dependency_list, target_list):
    modules_shrinkwrap = filterForShrinkwrap(dependency_list)
    targets_shrinkwrap = targetsShrinkwrap(target_list)
    modules_shrinkwrap.update(targets_shrinkwrap)
    return modules_shrinkwrap

def targetsShrinkwrap(target_list):
    return {
        'targets': [
            {'name':t.getName(), 'version':str(t.getVersion())} for t in target_list if t
        ]
    }

def filterForShrinkwrap(dependency_list):
    def filterModule(mod):
        return { k: mod[k] for k in ('name', 'version') if k in mod }

    dependency_list['modules'] = [
        filterModule(mod) for mod in dependency_list['modules'] if not mod.get('testOnly', False)
    ]

    return dependency_list
