# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import argparse
import logging
import os

# Component, , represents an installed component, internal
from yotta.lib import component
# access, , get components, internal
from yotta.lib import access
# access, , get components, internal
from yotta.lib import access_common

# folders, , get places to install things, internal
from yotta.lib import folders
# --config option, , , internal
from yotta import options

def addOptions(parser):
    options.config.addTo(parser)
    parser.add_argument('component', default=None, nargs='?',
        help='If specified, install this module instead of installing '+
             'the dependencies of the current module.'
    )
    parser.add_argument('--test-dependencies', dest='install_test_deps',
        choices=('none', 'all', 'own'), default='own',
        help='Control the installation of dependencies necessary for building tests.'
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--global', '-g', dest='act_globally', default=False, action='store_true',
        help='Install globally instead of in the current working directory.'
    )

    # Deprecated options, these now do nothing! --save behavior is the default,
    # and --save-target has been removed.
    group.add_argument('--save', dest='save', action='store_true',
        default=False, help=argparse.SUPPRESS
    )
    group.add_argument('--save-target', dest='save_target',
        action='store_true', default=False, help=argparse.SUPPRESS
    )


def execCommand(args, following_args):
    if not hasattr(args, 'install_test_deps'):
        vars(args)['install_test_deps'] = 'none'
    if getattr(args, 'save', None):
        logging.warning('the --save option is now the default and is ignored. It will be removed soon.')
    if getattr(args, 'save_target', None):
        logging.warning('the --save-target is now ignored. It will be removed soon.')
    cwd = os.getcwd()
    c = component.Component(cwd)
    if args.component is None:
        return installDeps(args, c)
    elif c or c.exists():
        return installComponentAsDependency(args, c)
    else:
        return installComponent(args)

def checkPrintStatus(errors, components, top_component, target):
    status = 0
    for error in errors:
        logging.error(error)
        status = 1
    for c in list(components.values()) + [top_component]:
        if c and c.getError():
            logging.error('%s %s', c.getName(), c.getError())
            status = 1
    leaf_target = None
    if target and target.hierarchy:
        for t in target.hierarchy:
            if not leaf_target:
                leaf_target = t
            if t and t.getError():
                if t is leaf_target:
                    logging.error('target %s %s', t.getName(), t.getError())
                else:
                    logging.error('base target %s of %s %s', t.getName(), leaf_target.getName(), t.getError())
                status = 1
    return status


def installDeps(args, current_component):
    # settings, , load and save settings, internal
    from yotta.lib import settings

    logging.debug('install deps for %s' % current_component)
    if not current_component:
        logging.debug(str(current_component.getError()))
        logging.error('The current directory does not contain a valid module.')
        return 1
    # warn if the target hasn't been explicitly specified when running a build:
    # this is likely user-error
    if not settings.getProperty('build', 'targetSetExplicitly') and not \
        getattr(args, '_target_set_explicitly', False):
        logging.warning(
            'The build target has not been set, so the default (%s) is being ' +
            'used. You can use `yotta target <targetname>` to set the build ' +
            'target. See http://yottadocs.mbed.com/tutorial/targets.html for '
            'more information on using targets.',
            args.target
        )
    target, errors = current_component.satisfyTarget(args.target, additional_config=args.config)
    if errors:
        for error in errors:
            logging.error(error)
        return 1
    if args.act_globally:
        # the npm behaviour here would be to install the working directory
        # module into the global modules dir
        raise NotImplementedError()
    else:
        # satisfyDependenciesRecursive will always prefer to install
        # dependencies in the yotta_modules directory of the top-level module,
        # so it's safe to set traverse_links here when we're only *installing*
        # modules (not updating them). This will never result in
        # Spooky-Action-Through-A-Symlink.
        components, errors = current_component.satisfyDependenciesRecursive(
                          target = target,
                  traverse_links = True,
            available_components = [(current_component.getName(), current_component)],
                            test = {'own':'toplevel', 'all':True, 'none':False}[args.install_test_deps]
        )
        return checkPrintStatus(errors, components, current_component, target)



def installComponentAsDependency(args, current_component):
    logging.debug('install component %s as dependency of %s' % (args.component, current_component))
    if not current_component:
        logging.debug(str(current_component.getError()))
        logging.error('The current directory does not contain a valid module.')
        return -1
    target, errors = current_component.satisfyTarget(args.target, additional_config=args.config)
    if errors:
        for error in errors:
            logging.error(error)
        return 1
    modules_dir = current_component.modulesPath()

    from yotta.lib import sourceparse
    # check if we have both a name and specification
    component_name, component_spec = sourceparse.parseModuleNameAndSpec(args.component)
    logging.info('%s, %s', component_name, component_spec)

    if component_name == current_component.getName():
        logging.error('will not install module %s as a dependency of itself', component_name)
        return -1
    try:
        installed = access.satisfyVersion(
                component_name,
                component_spec,
                     available = {current_component.getName():current_component},
                  search_paths = [modules_dir],
             working_directory = modules_dir
        )
    except access_common.AccessException as e:
        logging.error(e)
        return 1


    # We always add the component to the dependencies of the current component
    # (if it is not already present), and write that back to disk. Without
    # writing to disk the dependency wouldn't be usable.
    if installed and not current_component.hasDependency(component_name):
        vs = sourceparse.parseSourceURL(component_spec)
        if vs.source_type == 'registry':
            saved_spec = current_component.saveDependency(installed)
        else:
            saved_spec = current_component.saveDependency(installed, component_spec)

        current_component.writeDescription()
        logging.info('dependency %s: %s written to module.json', component_name, saved_spec)
    else:
        logging.info('dependency %s is already present in module.json', component_name)

    # !!! should only install dependencies necessary for the one thing that
    # we're installing (but existing components should be made available to
    # satisfy dependencies)
    components, errors = current_component.satisfyDependenciesRecursive(
                      target = target,
        available_components = [(current_component.getName(), current_component)],
                        test = {'own':'toplevel', 'all':True, 'none':False}[args.install_test_deps]

    )
    return checkPrintStatus(errors, components, current_component, target)


def installComponent(args):
    path = folders.globalInstallDirectory() if args.act_globally else os.getcwd()
    logging.debug('install component %s to %s' % (args.component, path))

    from yotta.lib import sourceparse
    # check if we have both a name and specification
    component_name, component_spec = sourceparse.parseModuleNameAndSpec(args.component)

    try:
        access.satisfyVersion(
                  component_name,
                  component_spec,
                       available = dict(),
                    search_paths = [path],
               working_directory = path
        )
    except access_common.AccessException as e:
        logging.error('%s', e)
        return 1
    os.chdir(component_name)
    return installDeps(args, component.Component(os.getcwd()))
