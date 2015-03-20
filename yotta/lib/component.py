# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import json
import os
import logging
import os.path as path
from collections import OrderedDict
import subprocess

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

# !!! FIXME: should components lock their description file while they exist?
# If not there are race conditions where the description file is modified by
# another process (or in the worst case replaced by a symlink) after it has
# been opened and before it is re-written


# Constants
Modules_Folder = 'yotta_modules'
Targets_Folder = 'yotta_targets'
Component_Description_File = 'module.json'
Component_Description_File_Fallback = 'package.json'
Registry_Namespace = 'modules' 
Schema_File = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'schema', 'module.json')

logger = logging.getLogger('components')
VVVERBOSE_DEBUG = logging.DEBUG - 8

# API
class Component(pack.Pack):
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
        logger.log(VVVERBOSE_DEBUG, "Component: " +  path +  ' installed_linked=' + str(installed_linked))
        warn_deprecated_filename = False
        if (not os.path.exists(os.path.join(path, Component_Description_File))) and \
           os.path.exists(os.path.join(path, Component_Description_File_Fallback)):
            warn_deprecated_filename = True
            description_filename = Component_Description_File_Fallback
        else:
            description_filename = Component_Description_File
        super(Component, self).__init__(
                                      path,
               description_filename = description_filename,
                   installed_linked = installed_linked,
                    schema_filename = Schema_File,
            latest_suitable_version = latest_suitable_version
        )
        if warn_deprecated_filename:
            logger.warning(
                "Component %s uses deprecated %s file, use %s instead." % (
                    self.getName(),
                    Component_Description_File_Fallback,
                    Component_Description_File
                )
            )
        self.installed_previously = installed_previously
        self.installed_dependencies = False
        self.dependencies_failed = False

    def getDependencySpecs(self, target=None):
        ''' Returns [(component name, version requirement)]
            e.g. ('ARM-RD/yottos', '*')

            These are returned in the order that they are listed in the
            component description file: this is so that dependency resolution
            proceeds in a predictable way.
        '''
        if 'dependencies' not in self.description and 'targetDependencies' not in self.description:
            logger.debug("component %s has no dependencies" % self.getName())
            return tuple()
        deps = []
        if 'dependencies' in self.description:
            deps += self.description['dependencies'].items()
        if target and 'targetDependencies' in self.description:
            for t in target.dependencyResolutionOrder():
                if t in self.description['targetDependencies']:
                    logger.debug(
                        'Adding target-dependent dependency specs for target %s (similar to %s) to component %s' %
                        (target, t, self.getName())
                    )
                    deps += self.description['targetDependencies'][t].items()
        return deps

    def getDependencies(self,
        available_components = None,
                 search_dirs = None,
                      target = None,
              available_only = False
        ):
        ''' Returns {component_name:component}
        '''
        available_components = self.ensureOrderedDict(available_components)        
        if search_dirs is None:
            search_dirs = []
        r = OrderedDict()
        modules_path = self.modulesPath()
        for name, ver_req in self.getDependencySpecs(target=target):
            if name in available_components:
                logger.debug('found dependency %s of %s in available components' % (name, self.getName()))
                r[name] = available_components[name]
            elif not available_only:
                for d in search_dirs + [modules_path]:
                    logger.debug('looking for dependency %s of %s in %s' % (name, self.getName(), d))
                    component_path = path.join(d, name)
                    c = Component(
                        component_path,
                        installed_previously=True,
                        installed_linked=fsutils.isLink(component_path)
                    )
                    if c:
                        logger.debug('found dependency %s of %s in %s' % (name, self.getName(), d))
                        break
                # if we didn't find a valid component in the search path, we
                # use the component initialised with the last place checked
                # (the modules path)
                if not c:
                    logger.warning('failed to find dependency %s of %s' % (name, self.getName()))
                r[name] = c
        return r

    def __getDependenciesWithProvider(self,
                      available_components = None,
                               search_dirs = None,
                                    target = None,
                          update_installed = False,
                                  provider = None
   ):
        ''' Get installed components using "provider" to find (and possibly
            install) components.

            See documentation for __getDependenciesRecursiveWithProvider

            returns (components, errors)
        '''
        errors = []
        modules_path = self.modulesPath()
        def satisfyDep(name_and_ver_req):
            (name, ver_req) = name_and_ver_req
            try:
                return provider(
                  name,
                  ver_req,
                  available_components,
                  search_dirs,
                  modules_path,
                  update_installed
                )
            except access_common.ComponentUnavailable as e:
                errors.append(e)
                self.dependencies_failed = True
            except vcs.VCSError as e:
                errors.append(e)
                self.dependencies_failed = True
        specs = self.getDependencySpecs(target)
        #dependencies = pool.map(
        dependencies = map(
            satisfyDep, specs
        )
        self.installed_dependencies = True
        # stable order is important!
        return (OrderedDict([((d and d.getName()) or specs[i][0], d) for i, d in enumerate(dependencies)]), errors)


    def __getDependenciesRecursiveWithProvider(self,
                               available_components = None,
                                        search_dirs = None,
                                             target = None,
                                     traverse_links = False,
                                   update_installed = False,                                     
                                           provider = None,
                                         _processed = None
    ):
        ''' Get installed components using "provider" to find (and possibly
            install) components.

            This function is called with different provider functions in order
            to retrieve a list of all of the dependencies, or install all
            dependencies.

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

                target:
                    None (default), or a Target object. If specified the target
                    name and it's similarTo list will be used in resolving
                    dependencies. If None, then only target-independent
                    dependencies will be installed

                traverse_links:
                    False (default) or True: whether to recurse into linked
                    dependencies. You normally want to set this to "True" when
                    getting a list of dependencies, and False when installing
                    them (unless the user has explicitly asked dependencies to
                    be installed in linked components).

                provider: None (default) or function:
                          provider(
                            name,
                            version_req,
                            available_components,
                            search_dirs,
                            working_directory,
                            update_if_installed
                          )
        '''
        def recursionFilter(c):
            if not c:
                logger.debug('do not recurse into failed component')
                # don't recurse into failed components
                return False
            if c.getName() in _processed:
                logger.debug('do not recurse into already processed component: %s' % c)
                return False
            if c.installedLinked() and not traverse_links:
                return False
            return True
        available_components = self.ensureOrderedDict(available_components)
        if search_dirs is None:
            search_dirs = []
        if _processed is None:
            _processed = set()
        search_dirs.append(self.modulesPath())
        logger.debug('process %s\nsearch dirs:%s' % (self.getName(), search_dirs))
        components, errors = self.__getDependenciesWithProvider(
            available_components = available_components,
                     search_dirs = search_dirs,
                update_installed = update_installed,
                          target = target,
                        provider = provider
        )
        _processed.add(self.getName())
        if errors:
            errors = ['Failed to satisfy dependencies of %s:' % self.path] + errors
        need_recursion = filter(recursionFilter, components.values()) 
        available_components.update(components)
        logger.debug('processed %s\nneed recursion: %s\navailable:%s\nsearch dirs:%s' % (self.getName(), need_recursion, available_components, search_dirs))
        # NB: can't perform this step in parallel, since the available
        # components list must be updated in order
        for c in need_recursion:
            dep_components, dep_errors = c.__getDependenciesRecursiveWithProvider(
                available_components = available_components,
                         search_dirs = search_dirs,
                              target = target,
                      traverse_links = traverse_links,
                    update_installed = update_installed,
                            provider = provider,
                          _processed = _processed
            )
            available_components.update(dep_components)
            components.update(dep_components)
            errors += dep_errors
        return (components, errors)
        

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
        def provideInstalled(name,
                      version_req,
             available_components,
                      search_dirs,
                working_directory,
              update_if_installed
        ):
            r = None
            try:
                r = access.satisfyVersionFromAvailble(name, version_req, available_components)
            except access_common.SpecificationNotMet as e:
                logger.error('%s (when trying to find dependencies for %s)' % (str(e), self.getName()))
            if r:
                return r
            r = access.satisfyVersionFromSearchPaths(name, version_req, search_dirs, update_if_installed)
            if r:
                return r
            # return an in invalid component, so that it's possible to use
            # getDependenciesRecursive to find a list of failed dependencies,
            # as well as just available ones
            r = Component(os.path.join(self.modulesPath(), name))
            assert(not r)
            return r

        components, errors = self.__getDependenciesRecursiveWithProvider(
           available_components = available_components,
                    search_dirs = search_dirs,
                         target = target,
                 traverse_links = True,
               update_installed = False,
                       provider = provideInstalled
        )
        for error in errors:
            logger.error(error)
        if available_only:
            components = OrderedDict((k, v) for k, v in components.items() if v)
        return components

    def modulesPath(self):
        return os.path.join(self.path, Modules_Folder)

    def targetsPath(self):
        return os.path.join(self.path, Targets_Folder)

    def satisfyDependenciesRecursive(
                            self,
            available_components = None,
                     search_dirs = None,
                update_installed = False,
                  traverse_links = False,
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

                traverse_links:
                    False (default) or True: whether to recurse into linked
                    dependencies when updating/installing.

                target:
                    None (default), or a Target object. If specified the target
                    name and it's similarTo list will be used in resolving
                    dependencies. If None, then only target-independent
                    dependencies will be installed

        '''
        def provider(
            name,
            version_req,
            available_components,
            search_dirs,
            working_directory,
            update_if_installed
        ):
            r = None
            try:
                r = access.satisfyVersionFromAvailble(name, version_req, available_components)
            except access_common.SpecificationNotMet as e:
                logger.error('%s (when trying to find dependencies for %s)' % (str(e), self.getName()))
            if r:
                return r
            r = access.satisfyVersionFromSearchPaths(name, version_req, search_dirs, update_if_installed)
            if r:
                return r
            r = access.satisfyVersionByInstalling(name, version_req, self.modulesPath())
            if not r:
                logger.error('could not install %s' % name)
            return r

        return self.__getDependenciesRecursiveWithProvider(
           available_components = available_components,
                    search_dirs = search_dirs,
                         target = target,
                 traverse_links = traverse_links,
               update_installed = update_installed,
                       provider = provider
        )

    def satisfyTarget(self, target_name_and_version, update_installed=False):
        ''' Ensure that the specified target name (and optionally version,
            github ref or URL) is installed in the targets directory of the
            current component
        '''
        logger.debug('satisfy target: %s' % target_name_and_version);
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
        except access_common.ComponentUnavailable as e:
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

    def getBinaries(self):
        ''' Return a dictionary of binaries to compile: {"dirname":"exename"},
            this is used when automatically generating CMakeLists '''
        # the module.json syntax is a subset of the package.json syntax: a
        # single string that defines the source directory to use to build an
        # executable with the same name as the component. This may be extended
        # to include the rest of the npm syntax in future (map of source-dir to
        # exe name).
        if 'bin' in self.description:
            return {self.description['bin']: self.getName()}
        else:
            return {}
    
    def licenses(self):
        ''' Return a list of licenses that apply to this module. (Strings,
            which may be SPDX identifiers)
        '''
        if 'license' in self.description:
            return [self.description['license']]
        else:
            return [x['type'] for x in self.description['licenses']]

    def getExtraIncludes(self):
        ''' Some components must export whole directories full of headers into
            the search path. This is really really bad, and they shouldn't do
            it, but support is provided as a concession to compatibility.
        '''
        if 'extraIncludes' in self.description:
            return [os.path.normpath(x) for x in self.description['extraIncludes']]
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
            return [os.path.normpath(x) for x in self.description['extraSysIncludes']]
        else:
            return []

    def getRegistryNamespace(self):
        return Registry_Namespace

    def __saveSpecForComponent(self, component):
        version = component.getVersion()
        if version.isTip():
            spec = '*'
        elif version.major() == 0:
            # for 0.x.x versions, when we save a dependency we don't use ^0.x.x
            # a that would peg to the exact version - instead we use ~ to peg
            # to the same minor version
            spec = '~' + str(version)
        else:
            spec = '^' + str(version)
        return spec

    def saveDependency(self, component, spec=None):
        if not 'dependencies' in self.description:
            self.description['dependencies'] = OrderedDict()
        if spec is None:
            spec = self.__saveSpecForComponent(component)
        self.description['dependencies'][component.getName()] = spec

    def saveTargetDependency(self, target, component, spec=None):
        if not 'targetDependencies' in self.description:
            self.description['targetDependencies'] = OrderedDict()
        if not target.getName() in self.description['targetDependencies']:
            self.description['targetDependencies'][target.getName()] = OrderedDict()
        if spec is None:
            spec = self.__saveSpecForComponent(component)
        self.description['targetDependencies'][target.getName()][component.getName()] = spec
