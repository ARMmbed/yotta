# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import os
import logging
from collections import OrderedDict

# access, , get components, internal
from yotta.lib import access
from yotta.lib import access_common
# pool, , shared thread pool, internal
#from pool import pool
# vcs, , represent version controlled directories, internal
from yotta.lib import vcs
# fsutils, , misc filesystem utils, internal
from yotta.lib import fsutils
# Pack, , common parts of Components/Targets, internal
from yotta.lib import pack

# !!! FIXME: should components lock their description file while they exist?
# If not there are race conditions where the description file is modified by
# another process (or in the worst case replaced by a symlink) after it has
# been opened and before it is re-written


# Constants
Modules_Folder = 'yotta_modules'
Targets_Folder = 'yotta_targets'
Component_Description_File = 'module.json'
Component_Description_File_Fallback = 'package.json'
Component_Definitions_File = 'defines.json'
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
    def __init__(
            self,
            path,
            installed_linked = False,
            latest_suitable_version = None,
            test_dependency = False,
            inherit_shrinkwrap = None
        ):
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
        self.description = OrderedDict()
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
            latest_suitable_version = latest_suitable_version,
                 inherit_shrinkwrap = inherit_shrinkwrap
        )
        if self.description and inherit_shrinkwrap is not None:
            # when inheriting a shrinkwrap, check that this module is
            # listed in the shrinkwrap, otherwise emit a warning:
            if next((x for x in inherit_shrinkwrap.get('modules', []) if x['name'] == self.getName()), None) is None:
                logger.warning("%s missing from shrinkwrap", self.getName())
        if warn_deprecated_filename:
            logger.warning(
                "Component %s uses deprecated %s file, use %s instead." % (
                    self.getName(),
                    Component_Description_File_Fallback,
                    Component_Description_File
                )
            )
        if 'bin' in self.description and 'lib' in self.description:
            self.error = 'Both "lib" and "bin" are specified in module.json: '+\
                'only one is allowed. If this is an executable module, then '+\
                'it should not specify a "lib" subdirectory, and if this is '+\
                'a re-usable library module, it should not specify a "bin" '+\
                'subdirectory'
            self.description = OrderedDict()
        # specified in the description
        self.installed_dependencies = False
        self.dependencies_failed = False
        self.is_test_dependency = test_dependency
        # read definitions for applications
        self.defines = {}
        defines_path = os.path.join(path, Component_Definitions_File)
        if os.path.isfile(defines_path):
            if not self.isApplication():
                # only applications can have definitions
                logger.warning("%s ignored in library module '%s'" % (Component_Definitions_File, self.getName()))
            else:
                # TODO: define a schema for this file
                self.defines = pack.tryReadJSON(defines_path, None)

    def getDependencySpecs(self, target=None):
        ''' Returns [DependencySpec]

            These are returned in the order that they are listed in the
            component description file: this is so that dependency resolution
            proceeds in a predictable way.
        '''
        deps = []

        def specForDependency(name, version_spec, istest):
            shrinkwrap = self.getShrinkwrapMapping()
            shrinkwrap_version_req = None
            if name in shrinkwrap:
                # exact version, and pull from registry:
                shrinkwrap_version_req = shrinkwrap[name]
                logger.debug(
                    'respecting %s shrinkwrap version %s for %s', self.getName(), shrinkwrap_version_req, name
                )
            return pack.DependencySpec(
                                         name,
                                         version_spec,
                                         istest,
                shrinkwrap_version_req = shrinkwrap_version_req,
                     specifying_module = self.getName()
            )

        deps += [specForDependency(x[0], x[1], False) for x in self.description.get('dependencies', {}).items()]
        target_deps = self.description.get('targetDependencies', {})
        if target is not None:
            for conf_key, target_conf_deps in target_deps.items():
                if _truthyConfValue(target.getConfigValue(conf_key)) or conf_key in target.getSimilarTo_Deprecated():
                    logger.debug(
                        'Adding target-dependent dependency specs for target config %s to component %s' %
                        (conf_key, self.getName())
                    )
                    deps += [specForDependency(x[0], x[1], False) for x in target_conf_deps.items()]


        deps += [specForDependency(x[0], x[1], True) for x in self.description.get('testDependencies', {}).items()]
        target_deps = self.description.get('testTargetDependencies', {})
        if target is not None:
            for conf_key, target_conf_deps in target_deps.items():
                if _truthyConfValue(target.getConfigValue(conf_key)) or conf_key in target.getSimilarTo_Deprecated():
                    logger.debug(
                        'Adding test-target-dependent dependency specs for target config %s to component %s' %
                        (conf_key, self.getName())
                    )
                    deps += [specForDependency(x[0], x[1], True) for x in target_conf_deps.items()]

        # remove duplicates (use the first occurrence)
        seen = set()
        r = []
        for dep in deps:
            if not dep.name in seen:
                r.append(dep)
                seen.add(dep.name)

        return r

    def hasDependency(self, name, target=None, test_dependencies=False):
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

        if test_dependencies:
            if name in self.description.get('testDependencies', {}).keys():
                return True

            if target is not None:
                test_target_deps = self.description.get('testTargetDependencies', {})
                for conf_key, target_conf_deps in test_target_deps.items():
                    if _truthyConfValue(target.getConfigValue(conf_key)) or conf_key in target.getSimilarTo_Deprecated():
                        if name in target_conf_deps:
                            return True
        return False

    def hasDependencyRecursively(self, name, target=None, test_dependencies=False):
        ''' Check if this module, or any of its dependencies, have a
            dependencies with the specified name in their dependencies, or in
            their targetDependencies corresponding to the specified target.

            Note that if recursive dependencies are not installed, this test
            may return a false-negative.
        '''
        # checking dependencies recursively isn't entirely straightforward, so
        # use the existing method to resolve them all before checking:
        dependencies = self.getDependenciesRecursive(
                               target = target,
                                 test = test_dependencies
        )
        return (name in dependencies)


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
        # sourceparse, , parse version source urls, internal
        from yotta.lib import sourceparse
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
                  self
                )
                if r and not sourceparse.parseSourceURL(dspec.versionReq()).semanticSpecMatches(r.getVersion()):
                    shrinkwrap_msg = ''
                    if dspec.isShrinkwrapped():
                        shrinkwrap_msg = 'shrinkwrap on '
                    msg = 'does not meet specification %s required by %s%s' % (
                        dspec.versionReq(), shrinkwrap_msg, self.getName()
                    )
                    logger.debug('%s %s', r.getName(), msg)
                    r.setError(msg)
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
             update_installed,
                       dep_of
        ):
        #logger.info('%s provideInstalled: %s', dep_of.getName(), dspec.name)
        r = access.satisfyFromAvailable(dspec.name, available_components)
        if r:
            if r.isTestDependency() and not dspec.is_test_dependency:
                logger.debug('test dependency subsequently occurred as real dependency: %s', r.getName())
                r.setTestDependency(False)
            return r
        update_if_installed = False
        if update_installed is True:
            update_if_installed = True
        elif update_installed:
            update_if_installed = dspec.name in update_installed
        r = access.satisfyVersionFromSearchPaths(
            dspec.name,
            dspec.versionReq(),
            search_dirs,
            update_if_installed,
            inherit_shrinkwrap = dep_of.getShrinkwrap()
        )
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
            installed_linked = fsutils.isLink(default_path),
          inherit_shrinkwrap = dep_of.getShrinkwrap()
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
                    False (default), True, or set(): whether to check the
                    available versions of installed components, and update if a
                    newer version is available. If this is a set(), only update
                    things in the specified set.

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
            update_installed,
            dep_of=None
        ):
            r = access.satisfyFromAvailable(dspec.name, available_components)
            if r:
                if r.isTestDependency() and not dspec.is_test_dependency:
                    logger.debug('test dependency subsequently occurred as real dependency: %s', r.getName())
                    r.setTestDependency(False)
                return r
            update_if_installed = False
            if update_installed is True:
                update_if_installed = True
            elif update_installed:
                update_if_installed = dspec.name in update_installed
            r = access.satisfyVersionFromSearchPaths(
                dspec.name,
                dspec.versionReq(),
                search_dirs,
                update_if_installed,
                inherit_shrinkwrap = dep_of.getShrinkwrap()
            )
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
                    installed_linked = fsutils.isLink(default_path),
                  inherit_shrinkwrap = dep_of.getShrinkwrap()
                )
                if r:
                    assert(r.installedLinked())
                    return r
                else:
                    logger.error('linked module %s is invalid: %s', dspec.name, r.getError())
                    return r

            r = access.satisfyVersionByInstalling(
                dspec.name,
                dspec.versionReq(),
                self.modulesPath(),
                inherit_shrinkwrap = dep_of.getShrinkwrap()
            )
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

    def satisfyTarget(self, target_name_and_version, update_installed=False, additional_config=None, install_missing=True):
        ''' Ensure that the specified target name (and optionally version,
            github ref or URL) is installed in the targets directory of the
            current component

            returns (derived_target, errors)
        '''
        # Target, , represent an installed target, internal
        from yotta.lib import target
        application_dir = None
        if self.isApplication():
            application_dir = self.path
        return target.getDerivedTarget(
                                target_name_and_version,
                                self.targetsPath(),
              install_missing = install_missing,
              application_dir = application_dir,
             update_installed = update_installed,
            additional_config = additional_config,
                   shrinkwrap = self.getShrinkwrap()
        )

    def getTarget(self, target_name_and_version, additional_config=None):
        ''' Return a derived target object representing the selected target: if
            the target is not installed, or is invalid then the returned object
            will test false in a boolean context.

            Returns derived_target

            Errors are not displayed.
        '''
        derived_target, errors = self.satisfyTarget(
                               target_name_and_version,
           additional_config = additional_config,
             install_missing = False
        )
        if len(errors):
            return None
        else:
            return derived_target

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
            this is used when automatically generating CMakeLists

            Note that currently modules may define only a single executable
            binary or library to be built by the automatic build system, by
            specifying `"bin": "dir-to-be-built-into-binary"`, or `"lib":
            "dir-to-be-built-into-library"`, and the bin/lib will always have
            the same name as the module. The default behaviour if nothing is
            specified is for the 'source' directory to be built into a library.

            The module.json syntax may allow for other combinations in the
            future (and callers of this function should not rely on it
            returning only a single item). For example, a "bin": {"dirname":
            "exename"} syntax might be supported, however currently more
            complex builds must be controlled by custom CMakeLists.
        '''
        # the module.json syntax is a subset of the package.json syntax: a
        # single string that defines the source directory to use to build an
        # executable with the same name as the component. This may be extended
        # to include the rest of the npm syntax in future (map of source-dir to
        # exe name).
        if 'bin' in self.description:
            return {os.path.normpath(self.description['bin']): self.getName()}
        else:
            return {}

    def getLibs(self, explicit_only=False):
        ''' Return a dictionary of libraries to compile: {"dirname":"libname"},
            this is used when automatically generating CMakeLists.

            If explicit_only is not set, then in the absence of both 'lib' and
            'bin' sections in the module.json file, the "source" directory
            will be returned.

            Note that currently modules may define only a single executable
            binary or library to be built by the automatic build system, by
            specifying `"bin": "dir-to-be-built-into-binary"`, or `"lib":
            "dir-to-be-built-into-library"`, and the bin/lib will always have
            the same name as the module. The default behaviour if nothing is
            specified is for the 'source' directory to be built into a library.

            The module.json syntax may allow for other combinations in the
            future (and callers of this function should not rely on it
            returning only a single item). For example, a "bin": {"dirname":
            "exename"} syntax might be supported, however currently more
            complex builds must be controlled by custom CMakeLists.
        '''
        if 'lib' in self.description:
            return {os.path.normpath(self.description['lib']): self.getName()}
        elif 'bin' not in self.description and not explicit_only:
            return {'source': self.getName()}
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

    def getDefines(self):
        return self.defines
