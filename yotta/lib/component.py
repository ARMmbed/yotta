# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import os
import logging
from collections import OrderedDict

# access, , get components, internal
import access
import access_common
# pool, , shared thread pool, internal
#from pool import pool
# vcs, , represent version controlled directories, internal
import vcs
# fsutils, , misc filesystem utils, internal
import fsutils
# Pack, , common parts of Components/Targets, internal
import pack
# Target, , represent an installed target, internal
import target
# sourceparse, , parse version source urls, internal
import sourceparse

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

def _truthyConfValue(v):
    ''' Determine yotta-config truthiness. In yotta config land truthiness is
        different to python or json truthiness (in order to map nicely only
        preprocessor and CMake definediness):

          json      -> python -> truthy/falsey
          false     -> False  -> Falsey
          null      -> None   -> Falsey
          undefined -> None   -> Falsey
          0         -> 0      -> Falsey
          ""        -> ""     -> Truthy (different from python)
          "0"       -> "0"    -> Truthy
          {}        -> {}     -> Truthy (different from python)
          []        -> []     -> Truthy (different from python)
          everything else is truthy
    '''
    if v is False:
        return False
    elif v is None:
        return False
    elif v == 0:
        return False
    else:
        # everything else is truthy!
        return True

# API
class Component(pack.Pack):
    def __init__(self, path, installed_linked=False, latest_suitable_version=None, test_dependency=False):
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
        self.installed_dependencies = False
        self.dependencies_failed = False
        self.is_test_dependency = test_dependency

    def getDependencySpecs(self, target=None):
        ''' Returns [DependencySpec]

            These are returned in the order that they are listed in the
            component description file: this is so that dependency resolution
            proceeds in a predictable way.
        '''
        deps = []

        deps += [pack.DependencySpec(x[0], x[1], False) for x in self.description.get('dependencies', {}).items()]
        target_deps = self.description.get('targetDependencies', {})
        if target is not None:
            for conf_key, target_conf_deps in target_deps.items():
                if _truthyConfValue(target.getConfigValue(conf_key)) or conf_key in target.getSimilarTo_Deprecated():
                    logger.debug(
                        'Adding target-dependent dependency specs for target config %s to component %s' %
                        (conf_key, self.getName())
                    )
                    deps += [pack.DependencySpec(x[0], x[1], False) for x in target_conf_deps.items()]


        deps += [pack.DependencySpec(x[0], x[1], True) for x in self.description.get('testDependencies', {}).items()]
        target_deps = self.description.get('testTargetDependencies', {})
        if target is not None:
            for conf_key, target_conf_deps in target_deps.items():
                if _truthyConfValue(target.getConfigValue(conf_key)) or conf_key in target.getSimilarTo_Deprecated():
                    logger.debug(
                        'Adding test-target-dependent dependency specs for target config %s to component %s' %
                        (conf_key, self.getName())
                    )
                    deps += [pack.DependencySpec(x[0], x[1], True) for x in target_conf_deps.items()]

        # remove duplicates (use the first occurrence)
        seen = set()
        r = []
        for dep in deps:
            if not dep.name in seen:
                r.append(dep)
                seen.add(dep.name)

        return r

    def hasDependency(self, name, target=None):
        ''' Check if this module has any dependencies with the specified name
            in its dependencies list, or in target dependencies for the
            specified target
        '''
        if name in self.description.get('dependencies', {}).keys():
            return True

        target_deps = self.description.get('targetDependencies', {})
        if target is not None:
            for conf_key, target_conf_deps in target_deps.items():
                if _truthyConfValue(target.getConfigValue(conf_key)) or conf_key in target.getSimilarTo_Deprecated():
                    if name in target_conf_deps:
                        return True
        return False


    def getDependencies(self,
        available_components = None,
                 search_dirs = None,
                      target = None,
              available_only = False,
                        test = False,
                    warnings = True
        ):
        ''' Returns {component_name:component}
        '''
        if search_dirs is None:
            search_dirs = [self.modulesPath()]
        available_components = self.ensureOrderedDict(available_components)

        components, errors = self.__getDependenciesWithProvider(
            available_components = available_components,
                     search_dirs = search_dirs,
                          target = target,
                update_installed = False,
                        provider = self.provideInstalled,
                            test = test
        )
        if warnings:
            for error in errors:
                logger.warning(error)
        if available_only:
            components = OrderedDict((k, v) for k, v in components.items() if v)
        return components

    def __getDependenciesWithProvider(self,
                      available_components = None,
                               search_dirs = None,
                                    target = None,
                          update_installed = False,
                                  provider = None,
                                      test = False
   ):
        ''' Get installed components using "provider" to find (and possibly
            install) components.

            See documentation for __getDependenciesRecursiveWithProvider

            returns (components, errors)
        '''
        errors = []
        modules_path = self.modulesPath()
        def satisfyDep(dspec):
            try:
                r = provider(
                  dspec,
                  available_components,
                  search_dirs,
                  modules_path,
                  update_installed,
                  self.getName()
                )
                if r and not sourceparse.parseSourceURL(dspec.version_req).semanticSpecMatches(r.getVersion()):
                    logger.debug('%s does not meet specification %s required by %s' % (r.getName(), dspec.version_req, self.getName()))
                    r.setError('does not meet specification %s required by %s' % (dspec.version_req, self.getName()))
                return r
            except access_common.Unavailable as e:
                errors.append(e)
                self.dependencies_failed = True
            except vcs.VCSError as e:
                errors.append(e)
                self.dependencies_failed = True
        specs = self.getDependencySpecs(target=target)
        if not test:
            # filter out things that aren't test dependencies if necessary:
            specs = [x for x in specs if not x.is_test_dependency]
        #dependencies = pool.map(
        dependencies = map(
            satisfyDep, specs
        )
        self.installed_dependencies = True
        # stable order is important!
        return (OrderedDict([((d and d.getName()) or specs[i].name, d) for i, d in enumerate(dependencies)]), errors)


    def __getDependenciesRecursiveWithProvider(self,
                               available_components = None,
                                        search_dirs = None,
                                             target = None,
                                     traverse_links = False,
                                   update_installed = False,
                                           provider = None,
                                               test = False,
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
                            dependency_spec,
                            available_components,
                            search_dirs,
                            working_directory,
                            update_if_installed
                          )
                test:
                    True, False, 'toplevel': should test-only dependencies be
                    included (yes, no, or only at this level, not recursively)
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
        assert(test in [True, False, 'toplevel'])
        search_dirs.append(self.modulesPath())
        logger.debug('process %s\nsearch dirs:%s' % (self.getName(), search_dirs))
        if self.isTestDependency():
            logger.debug("won't provide test dependencies recursively for test dependency %s", self.getName())
            test = False
        components, errors = self.__getDependenciesWithProvider(
            available_components = available_components,
                     search_dirs = search_dirs,
                update_installed = update_installed,
                          target = target,
                        provider = provider,
                            test = test
        )
        _processed.add(self.getName())
        if errors:
            errors = ['Failed to satisfy dependencies of %s:' % self.path] + errors
        need_recursion = [x for x in filter(recursionFilter, components.values())]
        available_components.update(components)
        logger.debug('processed %s\nneed recursion: %s\navailable:%s\nsearch dirs:%s' % (self.getName(), need_recursion, available_components, search_dirs))
        if test == 'toplevel':
            test = False
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
                                test = test,
                          _processed = _processed
            )
            available_components.update(dep_components)
            components.update(dep_components)
            errors += dep_errors
        return (components, errors)

    def provideInstalled(self,
                        dspec,
         available_components,
                  search_dirs,
            working_directory,
          update_if_installed,
                  dep_of_name
        ):
        r = access.satisfyFromAvailable(dspec.name, available_components)
        if r:
            if r.isTestDependency() and not dspec.is_test_dependency:
                logger.debug('test dependency subsequently occurred as real dependency: %s', r.getName())
                r.setTestDependency(False)
            return r
        r = access.satisfyVersionFromSearchPaths(dspec.name, dspec.version_req, search_dirs, update_if_installed)
        if r:
            r.setTestDependency(dspec.is_test_dependency)
            return r
        # return a module initialised to the path where we would have
        # installed this module, so that it's possible to use
        # getDependenciesRecursive to find a list of failed dependencies,
        # as well as just available ones
        # note that this Component object may still be valid (usable to
        # attempt a build), if a different version was previously installed
        # on disk at this location (which means we need to check if the
        # existing version is linked)
        default_path = os.path.join(self.modulesPath(), dspec.name)
        r = Component(
                               default_path,
             test_dependency = dspec.is_test_dependency,
            installed_linked = fsutils.isLink(default_path)
        )
        return r

    def getDependenciesRecursive(self,
                 available_components = None,
                            processed = None,
                          search_dirs = None,
                               target = None,
                       available_only = False,
                                 test = False
        ):
        ''' Get available and already installed components, don't check for
            remotely available components. See also
            satisfyDependenciesRecursive()

            Returns {component_name:component}
        '''
        components, errors = self.__getDependenciesRecursiveWithProvider(
           available_components = available_components,
                    search_dirs = search_dirs,
                         target = target,
                 traverse_links = True,
               update_installed = False,
                       provider = self.provideInstalled,
                           test = test
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
                          target = None,
                            test = False
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

                test:
                    True, False, or 'toplevel: should test-only dependencies be
                    installed? (yes, no, or only for this module, not its
                    dependencies).

        '''
        def provider(
            dspec,
            available_components,
            search_dirs,
            working_directory,
            update_if_installed,
            dep_of_name=None
        ):
            r = access.satisfyFromAvailable(dspec.name, available_components)
            if r:
                if r.isTestDependency() and not dspec.is_test_dependency:
                    logger.debug('test dependency subsequently occurred as real dependency: %s', r.getName())
                    r.setTestDependency(False)
                return r
            r = access.satisfyVersionFromSearchPaths(dspec.name, dspec.version_req, search_dirs, update_if_installed)
            if r:
                r.setTestDependency(dspec.is_test_dependency)
                return r
            # before resorting to install this module, check if we have an
            # existing linked module (which wasn't picked up because it didn't
            # match the version specification) - if we do, then we shouldn't
            # try to install, but should return that anyway:
            default_path = os.path.join(self.modulesPath(), dspec.name)
            if fsutils.isLink(default_path):
                r = Component(
                                       default_path,
                     test_dependency = dspec.is_test_dependency,
                    installed_linked = fsutils.isLink(default_path)
                )
                if r:
                    assert(r.installedLinked())
                    return r
                else:
                    logger.error('linked module %s is invalid: %s', dspec.name, r.getError())
                    return r

            r = access.satisfyVersionByInstalling(dspec.name, dspec.version_req, self.modulesPath())
            if not r:
                logger.error('could not install %s' % dspec.name)
            if r is not None:
                r.setTestDependency(dspec.is_test_dependency)
            return r

        return self.__getDependenciesRecursiveWithProvider(
           available_components = available_components,
                    search_dirs = search_dirs,
                         target = target,
                 traverse_links = traverse_links,
               update_installed = update_installed,
                       provider = provider,
                           test = test
        )

    def satisfyTarget(self, target_name_and_version, update_installed=False):
        ''' Ensure that the specified target name (and optionally version,
            github ref or URL) is installed in the targets directory of the
            current component
        '''
        application_dir = None
        if self.isApplication():
            application_dir = self.path
        return target.getDerivedTarget(
            target_name_and_version,
            self.targetsPath(),
            application_dir = application_dir,
            update_installed = update_installed
        )

    def installedDependencies(self):
        ''' Return true if satisfyDependencies has been called.

            Note that this is slightly different to when all of the
            dependencies are actually satisfied, but can be used as if it means
            that.
        '''
        return self.installed_dependencies

    def isApplication(self):
        ''' Return true if this module is an application instead of a reusable
            library '''
        return bool(len(self.getBinaries()))

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

    def setTestDependency(self, status):
        self.is_test_dependency = status

    def isTestDependency(self):
        return self.is_test_dependency

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
        return spec

    def removeDependency(self, component):
        if not component in self.description.get('dependencies', {}):
            logger.error('%s is not listed as a dependency', component)
            return False
        del self.description['dependencies'][component]
        return True

    def getTestFilterCommand(self):
        ''' return the test-output filtering command (array of strings) that
            this module defines, if any. '''
        if 'scripts' in self.description and 'testReporter' in self.description['scripts']:
            return self.description['scripts']['testReporter']
        else:
            return None
