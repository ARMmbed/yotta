# standard library modules, , ,
import json
import os
import logging
import os.path as path
from collections import OrderedDict

# access, , get components, internal
import access
import access_common
# pool, , shared thread pool, internal
from pool import pool
# version, , represent versions and specifications, internal
import version
# vcs, , represent version controlled directories, internal
import vcs
# fsutils, , misc filesystem utils, internal
import fsutils
# Pack, , common parts of Components/Targets, internal
import pack


# NOTE: at the moment this module provides very little validation of the
# contents of the description file: indeed if you replace the name of your
# component with an object it won't matter. We should probably at least check
# the type and format of the name (check for path-illegal characters) & version
# (check it's a valid version)

# !!! FIXME: should components lock their description file while they exist?
# If not there are race conditions where the description file is modified by
# another process (or in the worst case replaced by a symlink) after it has
# been opened and before it is re-written


# Constants
Modules_Folder = 'yotta_modules'
Targets_Folder = 'yotta_targets'
Component_Description_File = 'package.json'
# !!! FIXME: change /package to /component
Registry_Namespace = 'package' 


# API
class Component(pack.Pack):
    description_filename = Component_Description_File

    def __init__(self, path, installed_previously=False, installed_linked=False, latest_suitable_version=None):
        ''' How to use a Component:
           
            Initialise it with the directory into which the component has been
            downloaded, (or with a symlink that points to a directory
            containing the component)
           
            Check that 'if component:' is true, which indicates that the
            download is indeed a valid component.
           
            Check that component.getVersion() returns the version you think
            you've downloaded.

            Use component.getDependencySpecs() to get the names of the
            dependencies of the component, or component.getDependencies() to
            get Component objects (which may not be valid unless the
            dependencies have been installed) for each of the dependencies.
           
        '''
        super(Component, self).__init__(path, installed_linked=installed_linked)
        self.installed_previously = installed_previously
        self.installed_dependencies = False
        self.dependencies_failed = False
        self.latest_suitable_version = latest_suitable_version
        # !!! TODO: validate self.description, possibly add a
        # description_schema class variable used when loading...

    def getDependencySpecs(self, target=None):
        ''' Returns [(component name, version requirement)]
            e.g. ('ARM-RD/yottos', '*')

            These are returned in the order that they are listed in the
            component description file: this is so that dependency resolution
            proceeds in a predictable way.
        '''
        if 'dependencies' not in self.description:
            logging.debug("component %s has no dependencies" % self.getName())
            return tuple()
        deps = self.description['dependencies'].items()
        if target and 'targetDependencies' in self.description:
            for t in target.dependencyResolutionOrder():
                if t in self.description['targetDependencies']:
                    logging.debug(
                        'Adding target-dependent dependency specs for target %s (similar to %s) to component %s' %
                        (target, t, self.getName())
                    )
                    deps += self.description['targetDependencies'][t].items()
                    break
        return deps

    def getDependencies(self,
        available_components = None,
                 search_dirs = None,
                      target = None,
              available_only = False
        ):
        ''' Returns {component_name:component}
        '''
        if available_components is None:
            available_components = OrderedDict()
        if search_dirs is None:
            search_dirs = []
        r = OrderedDict()
        modules_path = self.modulesPath()
        for name, ver_req in self.getDependencySpecs(target=target):
            if name in available_components:
                logging.debug('found dependency %s of %s in available components' % (name, self.getName()))
                r[name] = available_components[name]
            elif not available_only:
                for d in search_dirs + [modules_path]:
                    logging.debug('looking for dependency %s of %s in %s' % (name, self.getName(), d))
                    component_path = path.join(d, name)
                    c = Component(
                        component_path,
                        installed_previously=True,
                        installed_linked=fsutils.isLink(component_path)
                    )
                    if c:
                        logging.debug('found dependency %s of %s in %s' % (name, self.getName(), d))
                        break
                # if we didn't find a valid component in the search path, we
                # use the component initialised with the last place checked
                # (the modules path)
                if not c:
                    logging.warning('failed to find dependency %s of %s' % (name, self.getName()))
                r[name] = c
        return r

    def getDependenciesRecursive(self,
                 available_components = None,
                            processed = None,
                          search_dirs = None,
                               target = None,
                       available_only = False
        ):
        ''' Get available and already installed components, don't check for
            remotely available components. See also
            satisfyDependenciesRecursive()

            Returns {component_name:component}
        '''
        def recursionFilter(c):
            if not c:
                # don't recurse into failed components
                return False
            if c.getName() in processed:
                return False
            return True
        if available_components is None:
            available_components = OrderedDict()
        if processed is None:
            processed = set()
        if search_dirs is None:
            search_dirs = []
        search_dirs.append(self.modulesPath())
        components = self.getDependencies(
                available_components,
                         search_dirs,
                              target,
                      available_only
        )
        processed.add(self.getName())
        need_recursion = filter(recursionFilter, components.values())
        available_components.update(components)
        for c in need_recursion:
            dep_components = c.getDependenciesRecursive(
                available_components,
                           processed,
                         search_dirs,
                              target,
                      available_only
            )
            available_components.update(dep_components)
            components.update(dep_components)
        return components

    def modulesPath(self):
        return os.path.join(self.path, Modules_Folder)

    def targetsPath(self):
        return os.path.join(self.path, Targets_Folder)

    def outdated(self):
        ''' Return a truthy object if a newer suitable version is available,
            otherwise return None.
            (in fact the object returned is a ComponentVersion that can be used
             to get the newer version)
        '''
        if self.latest_suitable_version and self.latest_suitable_version > self.version:
            return self.latest_suitable_version
        else:
            return None

    def satisfyDependencies(
                            self,
            available_components,
                     search_dirs = None,
                update_installed = False,
                          target = None
        ):
        ''' Retrieve and install all the dependencies of this component, or
            satisfy them from a collection of available_components.

            Returns (components, errors)
        '''
        errors = []
        modules_path = self.modulesPath()
        def satisfyDep((name, ver_req)):
            try:
                # !!! TODO: validate that the installed component has the same
                # name and version as we expected, and at least warn if it
                # doesn't
                component = access.satisfyVersion(
                    name,
                    ver_req,
                    available_components,
                    search_dirs,
                    modules_path,
                    update_installed=('Update' if update_installed else None)
                )
                return component
            except access_common.ComponentUnavailable, e:
                errors.append(e)
                self.dependencies_failed = True
        #dependencies = pool.map(
        dependencies = map(
            satisfyDep, self.getDependencySpecs(target)
        )
        self.installed_dependencies = True
        # stable order is important!
        return (OrderedDict([(d.description['name'], d) for d in dependencies if d]), errors)

    def satisfyDependenciesRecursive(
                            self,
            available_components = None,
                     search_dirs = None,
                update_installed = False,
                          target = None
        ):
        ''' Retrieve and install all the dependencies of this component and its
            dependencies, recursively, or satisfy them from a collection of
            available_components or from disk.

            Returns
            =======
                (components, errors)

                components: dictionary of name:Component
                errors: sequence of errors


            Parameters
            ==========

                available_components:
                    None (default) or a dictionary of name:component. This is
                    searched before searching directories or fetching remote
                    components

                search_dirs:
                    None (default), or sequence of directories to search for
                    already installed, (but not yet loaded) components. Used so
                    that manually installed or linked components higher up the
                    dependency tree are found by their users lower down.

                    These directories are searched in order, and finally the
                    current directory is checked.
                
                update_installed:
                    False (default), or True: whether to check the available
                    versions of installed components, and update if a newer
                    version is available.
                
                target:
                    None (default), or a Target object. If specified the target
                    name and it's similarTo list will be used in resolving
                    dependencies. If None, then only target-independent
                    dependencies will be installed

        '''
        def recursionFilter(c):
            if not c:
                logging.debug('do not recurse into failed component')
                # don't recurse into failed components
                return False
            if c.getName() in available_components:
                logging.debug('do not recurse into already installed component: %s' % c)
                # don't recurse into components added at a higher level: this
                # ensures that dependencies are installed as high up the tree
                # as possible
                return False
            if c.installed_linked:
                return False
            if update_installed:
                logging.debug('%s:%s' % (
                    self.getName(),
                    ('new','dependencies installed')[c.installedDependencies()]
                ))
                return c.outdated() or not c.installedDependencies()
            else:
                # if we don't want to update things that were already installed
                # (install mode, rather than update mode) then don't recurse
                # into things that were already on disk
                logging.debug('%s:%s:%s' % (
                    self.getName(),
                    ('new','installed previously')[c.installedPreviously()],
                    ('new','dependencies installed')[c.installedDependencies()]
                ))
                return not (c.installedPreviously() or c.installedDependencies())
        if available_components is None:
            available_components = OrderedDict()
        if search_dirs is None:
            search_dirs = []
        search_dirs.append(self.modulesPath())
        components, errors = self.satisfyDependencies(
            available_components,
                     search_dirs,
                update_installed = update_installed,
                          target = target
        )
        if errors:
            errors = ['Failed to satisfy dependencies of %s:' % self.path] + errors
        need_recursion = filter(recursionFilter, components.values())
        available_components.update(components)
        # NB: can't perform this step in parallel, since the available
        # components list must be updated in order
        for c in need_recursion:
            dep_components, dep_errors = c.satisfyDependenciesRecursive(
                available_components, search_dirs, update_installed, target
            )
            available_components.update(dep_components)
            errors += dep_errors
        logging.info('%s@%s' % (self.getName(), self.getVersion()))
        return (components, errors)

    def satisfyTarget(self, target_name_and_version, update_installed=False):
        ''' Ensure that the specified target name (and optionally version,
            github ref or URL) is installed in the targets directory of the
            current component
        '''
        errors = []
        targets_path = self.targetsPath()
        target = None
        try:
            target_name, target_version_req = target_name_and_version.split(',', 1)
            target = access.satisfyTarget(
                target_name,
                target_version_req,
                targets_path,
                update_installed=('Update' if update_installed else None)
            )
        except access_common.TargetUnavailable, e:
            errors.append(e)
        return (target, errors)

    def installedPreviously(self):
        ''' Return true if this component was created with
            installed_previously=True
        '''
        return self.installed_previously

    def installedDependencies(self):
        ''' Return true if satisfyDependencies has been called. 

            Note that this is slightly different to when all of the
            dependencies are actually satisfied, but can be used as if it means
            that.
        '''
        return self.installed_dependencies

    def getExtraIncludes(self):
        ''' Some components must export whole directories full of headers into
            the search path. This is really really bad, and they shouldn't do
            it, but support is provided as a concession to compatibility.
        '''
        if 'extraIncludes' in self.description:
            return self.description['extraIncludes']
        else:
            return []
    
    def getExtraSysIncludes(self):
        ''' Some components (e.g. libc) must export directories of header files
            into the system include search path. They do this by adding a
            'extraSysIncludes' : [ array of directories ] field in their
            package description. This function returns the list of directories
            (or an empty list), if it doesn't exist.
        '''
        if 'extraSysIncludes' in self.description:
            return self.description['extraSysIncludes']
        else:
            return []

    def getRegistryNamespace(self):
        return Registry_Namespace
