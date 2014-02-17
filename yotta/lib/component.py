# standard library modules, , ,
import json
import os
from collections import OrderedDict
import logging

# access, , get components, internal
import access
import access_common
# pool, , shared thread pool, internal
from pool import pool
# version, , represent versions and specifications, internal
import version
# vcs, , represent version controlled directories, internal
import vcs

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

# Internals
def _readPackageJSON(path):
    with open(path, 'r') as f:
        # using an ordered dictionary for objects so that we preserve the order
        # of dependencies
        return json.load(f, object_pairs_hook=OrderedDict)

def _writePackageJSON(path, obj):
    with open(path, 'w') as f:
        json.dump(obj, f, indent=2, separators=(',', ': '))

# API
class Component:
    def __init__(self, path, installed_previously=False, installed_linked=False):
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
           
           
            The component file format is currently assumed to be identical to
            NPM's package.json
        '''
        self.error = None
        self.path = path
        self.installed_previously = installed_previously
        self.installed_linked = False
        self.installed_dependencies = False
        self.dependencies_failed = False
        self.version = None
        self.vcs = None
        try:
            self.component_info = _readPackageJSON(os.path.join(path, 'package.json'))
            self.version = version.Version(self.component_info['version'])
            # !!! TODO: validate other stuff in the package, like that it has a
            # valid name & version
        except Exception, e:
            self.component_info = None
            self.error = e
        self.vcs = vcs.getVCS(path)

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

    def getName(self):
        return self.component_info['name']
    
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
        modules_path = os.path.join(self.path, Modules_Folder)
        def satisfyDep((name, ver_req)):
            try:
                # !!! TODO: validate that the installed component has the same
                # name and version as we expected, and at least warn if it
                # doesn't
                return access.satisfyVersion(name, ver_req, modules_path, available_components)
            except access_common.ComponentUnavailable, e:
                errors.append(e)
                self.dependencies_failed = True
        dependencies = pool.map(
            satisfyDep, self.getDependencies()
        )
        self.installed_dependencies = True
        return ({d.component_info['name']: d for d in dependencies if d}, errors)

    def satisfyDependenciesRecursive(self, available_components=None, update_installed=False):
        ''' Retrieve and install all the dependencies of this component and its
            dependencies, recursively, or satisfy them from a collection of
            available_components.

            Returns (components, errors)
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
            if update_installed:
                logging.debug('%s:%s' % (
                    self.getName(),
                    ('new','dependencies installed')[c.installedDependencies()]
                ))
                return not c.installedDependencies()
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
            available_components = dict()
        components, errors = self.satisfyDependencies(available_components)
        need_recursion = filter(recursionFilter, components.values())
        available_components.update(components)
        # NB: can't perform this step in parallel, since the available
        # components list must be updated in order
        for c in need_recursion:
            dep_components, dep_errors = c.satisfyDependenciesRecursive(
                available_components, update_installed
            )
            available_components.update(dep_components)
            errors += dep_errors
        logging.info('%s@%s' % (self.getName(), self.getVersion()))
        return (components, errors)

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

    def getVersion(self):
        return self.version
    
    def setVersion(self, version):
        self.version = version
        self.component_info['version'] = str(self.version)

    def writeDescription(self):
        ''' Write the current (possibly modified) component description to a
            package description file in the component directory.
        '''
        _writePackageJSON(os.path.join(self.path, 'package.json'), self.component_info)
        if self.vcs:
            self.vcs.markForCommit('package.json')

    def vcsIsClean(self):
        ''' Return true if the component directory is not version controlled,
            or if it is version controlled with a supported system and is in a
            clean state
        '''
        if not self.vcs:
            return True
        return self.vcs.isClean()

    def commitVCS(self, tag=None):
        ''' Commit the current working directory state (or do nothing if the
            working directory is not version controlled)
        '''
        if not self.vcs:
            return
        self.vcs.commit(message='version %s' % tag, tag=tag)

    def __repr__(self):
        return "%s %s at %s" % (self.component_info['name'], self.component_info['version'], self.path)

    # provided for truthiness testing, we test true only if we successfully
    # read a package file
    def __nonzero__(self):
        return bool(self.component_info)

