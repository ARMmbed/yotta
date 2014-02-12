# standard library modules, , ,
import json
import os
from collections import OrderedDict

# access, , get components, internal
import access
import access_common
# pool, , shared thread pool, internal
from pool import pool

# NOTE: at the moment this module provides very little validation of the
# contents of the description file: indeed if you replace the name of your
# component with an object it won't matter. We should probably at least check
# the type and format of the name (check for path-illegal characters) & version
# (check it's a valid version)


# Internals
def _readPackageJSON(path):
    with open(path, 'r') as f:
        # using an ordered dictionary for objects so that we preserve the order
        # of dependencies
        return json.load(f, object_pairs_hook=OrderedDict)


# API
class Component:
    def __init__(self, path):
        ''' How to use a Component:
           
            Initialise it with the directory into which the component has been
            downloaded, (or with a symlink that points to a directory
            containing the component)
           
            Check that 'if component:' is true, which indicates that the
            download is indeed a valid component.
           
            Check that component.getVersion() returns the version you think
            you've downloaded, if it doesn't be sure to make a fuss.
           
            Use component.getDependencies() to get the names of the
            dependencies of the component
           
           
            ... eventually it will also be possible to use components to tag &
            commit new versions, etc.
           
           
            The component file format is currently assumed to be identical to
            NPM's package.json
        '''
        self.error = None
        self.path = path
        self.dependencies_attempted = False
        self.dependencies_failed = False
        try:
            self.component_info = _readPackageJSON(os.path.join(path, 'package.json'))
            # !!! TODO: validate other stuff in the package, like that it has a
            # valid name & version
        except Exception, e:
            self.component_info = None
            self.error = e

    def getDependencies(self):
        ''' Returns [(component name, version requirement)]
            e.g. ('ARM-RD/yottos', '*')

            These are returned in the order that they are listed in the
            component description file: this is so that dependency resolution
            proceeds in a predictable way.
        '''
        return self.component_info['dependencies'].items()
    
    def getVersion(self):
        ''' Return the version string as specified by the package file.
            This will always be a real version: 1.2.3, not a hash or a URL.

            Note that a component installed through a URL still provides a real
            version - so if the first component to depend on some component C
            depends on it via a URI, and a second component depends on a
            specific version 1.2.3, dependency resolution will only succeed if
            the version of C obtained from the URL happens to be 1.2.3
        '''
        return self.component_info['version']
    
    def getError(self):
        ''' If this isn't a valid component, return some sort of explanation
            about why that is. '''
        return self.error

    def satisfyDependencies(self, available_components):
        ''' Retrieve and install all the dependencies of this component, or
            satisfy them from a collection of available_components.

            Returns (components, errors)
        '''
        errors = []
        def satisfyDep((name, ver_req)):
            try:
                # !!! TODO: validate that the installed component has the same
                # name and version as we expected, and at least warn if it
                # doesn't
                return access.satisfyVersion(name, ver_req, self.path, available_components)
            except access_common.ComponentUnavailable, e:
                errors.append(e)
                self.dependencies_failed = True
        dependencies = pool.map(
            satisfyDep, self.getDependencies()
        )
        self.dependencies_satisfied = True
        return (set(dependencies), errors)

    def satisfyDependenciesRecursive(self, available_components=None):
        ''' Retrieve and install all the dependencies of this component and its
            dependencies, recursively, or satisfy them from a collection of
            available_components.

            Returns (components, errors)
        '''
        if available_components is None:
            available_components = set()
        components, errors = self.satisfyDependencies(available_components)
        need_recursion = filter(lambda d: d and not d.dependenciesAttempted(), components)
        # NB: can't perform this step in parallel, since the available
        # components list must be updated in order
        for c in need_recursion:
            dep_components, dep_errors = c.satisfyDependenciesRecursive(available_components | components)
            components |= dep_components
            errors += dep_errors
        return (components, errors)

    def dependenciesAttempted(self):
        ''' Return true if satisfyDependencies has been called. 

            Note that this is slightly different to when all of the
            dependencies are actually satisfied, but can be used as if it means
            that.
        '''
        return self.dependencies_attempted

    def __repr__(self):
        return "%s %s at %s" % (self.component_info['name'], self.component_info['version'], self.path)

    # provided for truthiness testing, we test true only if we successfully
    # read a package file
    def __nonzero__(self):
        return bool(self.component_info)

