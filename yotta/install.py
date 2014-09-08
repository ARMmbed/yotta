# standard library modules, , ,
import argparse
import logging
import os
import re

# Component, , represents an installed component, internal
from lib import component
# access, , get components, internal
from lib import access

# folders, , get places to install things, internal
from . import folders

def addOptions(parser):
    parser.add_argument('component', default=None, nargs='?',
        help='If specified, install this component instead of installing '+
             'the dependencies of the current component.'
    )
    parser.add_argument('-l', '--install-linked', dest='install_linked',
        action='store_true', default=False,
        help='Traverse linked components, and install dependencies needed there too.'
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--global', '-g', dest='act_globally', default=False, action='store_true',
        help='Install globally instead of in the current working directory.'
    )
    group.add_argument('--save', dest='save', action='store_true',
        default=False,
        help='Add the specified component to dependencies in module.json'
    )
    group.add_argument('--save-target', dest='save_target',
        action='store_true', default=False,
        help='Add the specified component to targetDependencies in module.json'
    )


def execCommand(args):
    cwd = os.getcwd()
    c = component.Component(cwd)
    if args.component is None:
        installDeps(args, c)
    elif c or c.exists():
        installComponentAsDependency(args, c)
    else:
        installComponent(args)


def installDeps(args, current_component):
    logging.debug('install deps for %s' % current_component)
    if args.save:
        logging.error('must specify a component name when using --save')
        return 1
    if args.save_target:
        logging.error('must specify a component name when using --save-target')
        return 1
    if not current_component:
        logging.debug(str(current_component.getError()))
        logging.error('The current directory does not contain a valid component.')
        return 1
    if not args.target:
        logging.error('No target has been set, use "yotta target" to set one.')
        return 1
    target, errors = current_component.satisfyTarget(args.target)
    if errors:
        for error in errors:
            logging.error(error)
        return 1
    if args.act_globally:
        # the npm behaviour here would be to install the working directory
        # module into the global modules dir
        raise NotImplementedError()
    else:
        install_linked = False
        if 'install_linked' in args:
            install_linked = args.install_linked
        components, errors = current_component.satisfyDependenciesRecursive(
                          target = target,
                  traverse_links = install_linked,
            available_components = [(current_component.getName(), current_component)]
        )
        for error in errors:
            logging.error(error)



def installComponentAsDependency(args, current_component):
    logging.debug('install component %s as dependency of %s' % (args.component, current_component))
    if not current_component:
        logging.debug(str(current_component.getError()))
        logging.error('The current directory does not contain a valid component.')
        return -1
    target, errors = current_component.satisfyTarget(args.target)
    if errors:
        for error in errors:
            logging.error(error)
        return 1
    #!!! FIXME: non-registry component spec support (see also installComponent
    # below), for these the original source should be included in the version
    # spec, too
    component_name = args.component
    modules_dir = os.path.join(os.getcwd(), 'node_modules')
    installed = access.satisfyVersion(
            component_name,
                       '*',
                 available = {current_component.getName():current_component},
              search_paths = [modules_dir],
         working_directory = modules_dir
    )
    # always add the component to the dependencies of the current component
    # - but don't write the dependency file back to disk if we're not meant to
    # save it
    if installed and args.save:
        current_component.saveDependency(installed)
        current_component.writeDescription()
    elif installed and args.save_target:
        current_component.saveTargetDependency(target, installed) 
        current_component.writeDescription()
    else:
        current_component.saveDependency(installed)
    # !!! should only install dependencies necessary for the one thing that
    # we're installing (but existing components should be made available to
    # satisfy dependencies)
    components, errors = current_component.satisfyDependenciesRecursive(
                      target = target,
        available_components = [(current_component.getName(), current_component)]
    )
    for error in errors:
        logging.error(error)


def installComponent(args):
    path = folders.globalInstallDirectory() if args.act_globally else os.getcwd()
    logging.debug('install component %s to %s' % (args.component, path))
    if args.save:
        logging.error('cannot --save unless the current directory is a component')
        return 1
    if args.save_target:
        logging.error('cannot --save-target unless the current directory is a component')
        return 1
    
    # !!! FIXME: should support other URL specs, spec matching should be in
    # access module
    github_ref_match = re.compile('[a-zA-Z0-9-]*/([a-zA-Z0-9-]*)').match(args.component)
    if github_ref_match:
        component_name = github_ref_match.group(1)
        access.satisfyVersion(
                  component_name,
                  args.component,
                       available = dict(),
                    search_paths = [path],
               working_directory = path
        )
    else:
        component_name = args.component
        access.satisfyVersion(
                  component_name,
                             '*',
                       available = dict(),
                    search_paths = [path],
               working_directory = path
        )
    os.chdir(component_name)
    installDeps(args, component.Component(os.getcwd()))
