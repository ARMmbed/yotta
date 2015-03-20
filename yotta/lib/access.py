# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import os
import logging

# Component, , represents an installed component, internal
import component
# Target, , represents an installed target, internal
import target
# Access common, , components shared between access modules, internal
import access_common
# Registry Access, , access packages in the registry, internal
import registry_access
# Github Access, , access repositories on github, internal
import github_access
# Git Access, , access repositories via generic git URLs, internal
import git_access
# hg Access, , access repositories via generic mercurial URLs, internal
import hg_access
# version, , represent versions and specifications, internal
import version
# fsutils, , misc filesystem utils, internal
import fsutils
# sourceparse, , parse version source urls, internal
import sourceparse

# Version requirement strings we want to support:
#
# (>,>=,<,<=,)version                         # central repo
# 1.2.x                                       # central repo
# http://...                                  # tarball or zipfile
# owner/repo @((>,>=,<,<=,,)version)          # Github
# hg+(ssh://..., http://...)(#hash-or-tag)    # hg
# * (any version)                             # central repo
#
# Currently should work:
# *
# <,>,>= etc
# 1.2.x
# owner/repo
# git://github.com/user/project(#version)     # Github
# git+(ssh://..., http://...)(#hash-or-tag)   # git
# anything://anything.git                     # git
#


logger = logging.getLogger('access')


def remoteComponentFor(name, version_required, registry='modules'):
    ''' Return a RemoteComponent sublclass for the specified component name and
        source url (or version specification)
        Raises an exception if any arguments are invalid.
    '''

    vs = sourceparse.parseSourceURL(version_required)
    
    if vs.source_type == 'registry':
        if registry not in ('modules', 'targets'):
            raise Exception('no known registry namespace "%s"' % registry)
        return registry_access.RegistryThing.createFromSource(
            vs, name, registry=registry
        )
    elif vs.source_type == 'github':
        return github_access.GithubComponent.createFromSource(vs, name)
    elif vs.source_type == 'git':
        return git_access.GitComponent.createFromSource(vs, name)
    elif vs.source_type == 'hg':
        return hg_access.HGComponent.createFromSource(vs, name)
    else:
        raise Exception('unsupported module source: "%s"' % vs.source_type)
    # !!! FIXME: next: generic http urls to tarballs


def tagOrBranchVersion(spec, tags, branches, diagnostic_name):
    for i, v in enumerate(tags + branches):
        if spec == v.tag:
            if i >= len(tags):
                logger.warning(
                    'Using head of "%s" branch for "%s", not a tagged version' % (
                        v.tag,
                        diagnostic_name
                    )
                )
            return v
    return None

def latestSuitableVersion(name, version_required, registry='modules'):
    ''' Return a RemoteVersion object representing the latest suitable
        version of the named component or target.

        All RemoteVersion objects have a .unpackInto(directory) method.
    '''

    remote_component = remoteComponentFor(name, version_required, registry)

    logger.info('get versions for ' + name)

    if remote_component.remoteType() == 'registry':
        logger.debug('satisfy %s from %s registry' % (name, registry))
        vers = remote_component.availableVersions()
        spec = remote_component.versionSpec()
        v = spec.select(vers)
        logger.debug("%s selected %s from %s", spec, v, vers)
        if not v:
            raise Exception(
                'The %s registry does not provide a version of "%s" matching "%s"' % (
                    registry, name, spec
                )
            )
        return v
    elif remote_component.remoteType() == 'github': 
        logger.debug('satisfy %s from github url' % name)
        spec = remote_component.versionSpec()
        if spec:
            vers = remote_component.availableVersions()
            if not len(vers):
                logger.warning(
                    'Github repository "%s" has no tagged versions, default branch will be used' % (
                        remote_component.repo
                    )
                )
                vers = [remote_component.tipVersion()]
            v = spec.select(vers)
            logger.debug("%s selected %s from %s", spec, v, vers)
            if not v:
                raise Exception(
                    'Github repository "%s" does not provide a version matching "%s"' % (
                        remote_component.repo,
                        remote_component.spec
                    )
                )
            return v
        else:
            # we're fetching a specific tag, or the head of a branch:
            v = tagOrBranchVersion(
                remote_component.tagOrBranchSpec(),
                remote_component.availableTags(),
                remote_component.availableBranches(),
                name
            )
            if v:
                return v
            raise Exception(
                'Github repository "%s" does not have any tags or branches matching "%s"' % (
                    version_required, spec
                )
            )

    elif remote_component.remoteType() in ('git', 'hg'):
        clone_type = remote_component.remoteType()
        logger.debug('satisfy %s from %s url' % (name, clone_type))
        local_clone = remote_component.clone()
        if not local_clone:
            raise Exception(
                'Failed to clone %s URL %s to satisfy dependency %s' % (clone_type, version_required, name)
            )
        spec = remote_component.versionSpec()
        if spec:
            vers = local_clone.availableVersions()
            if not len(vers):
                logger.warning(
                    '%s repository "%s" has no tagged versions, default branch will be used' % (clone_type, version_required)
                )
                vers = [local_clone.tipVersion()]
            v = spec.select(vers)
            logger.debug("%s selected %s from %s", spec, v, vers)
            if not v:
                raise Exception(
                    '%s repository "%s" does not provide a version matching "%s"' % (
                        clone_type,
                        version_required,
                        remote_component.spec
                    )
                )
            return v
        elif remote_component.remoteType() == 'git':
            v = tagOrBranchVersion(
                remote_component.tagOrBranchSpec(),
                local_clone.availableTags(),
                local_clone.availableBranches(),
                name
            )
            if v:
                return v
            raise Exception(
                '%s repository "%s" does not have any tags or branches matching "%s"' % (
                    clone_type, version_required, spec
                )
            )
        else:
            raise Exception("invalid spec for hg source: tags/branches are not supported yet!")
    
    # !!! FIXME: next: generic http urls to tarballs
    
    return None

def searchPathsForComponent(name, version_required, search_paths):
    for path in search_paths:
        component_path = os.path.join(path, name)
        logger.debug("check path %s for %s" % (component_path, name))
        local_component = component.Component(
                     component_path,
               installed_previously = True,
                   installed_linked = fsutils.isLink(component_path),
            latest_suitable_version = None
        )
        if local_component:
            return local_component
    return None


def satisfyVersionFromAvailble(name, version_required, available):
    spec = None
    if name in available and available[name]:
        logger.debug('satisfy %s from already installed components' % name)
        # we still need to check the version specification - which the remote
        # components know how to parse:
        remote_component = remoteComponentFor(name, version_required, 'modules')
        if remote_component.versionSpec():
            if not remote_component.versionSpec().match(available[name].version):
                raise access_common.SpecificationNotMet(
                    "Installed component %s doesn't match specification %s" % (name, remote_component.versionSpec())
                ) 
        r = available[name]
        if spec and not spec.match(r.getVersion()):
            raise Exception('Previously added component %s@%s doesn\'t meet spec %s' % (name, r.getVersion(), spec))
        if name != r.getName():
            raise Exception('Component %s was installed as different name %s in %s' % (
                r.getName(), name, r.path
            ))
        return r
    return None

def satisfyVersionFromSearchPaths(name, version_required, search_paths, update=False):
    ''' returns a Component for the specified version, if found in the list of
        search paths. If `update' is True, then also check for newer versions
        of the found component, and update it in-place (unless it was installed
        via a symlink).
    '''
    spec = None
    v    = None

    local_component = searchPathsForComponent(name, version_required, search_paths)
    logger.debug("%s %s locally" % (('found', 'not found')[not local_component], name))
    if local_component:
        if update and not local_component.installedLinked():
            #logger.debug('attempt to check latest version of %s @%s...' % (name, version_required))
            v = latestSuitableVersion(name, version_required)
            if local_component:
                local_component.setLatestAvailable(v)

        # if we don't need to update, then we're done
        if local_component.installedLinked() or not local_component.outdated():
            logger.debug("satisfy component from directory: %s" % local_component.path)
            # if a component exists (has a valid description file), and either is
            # not outdated, or we are not updating
            if name != local_component.getName():
                raise Exception('Component %s found in incorrectly named directory %s (%s)' % (
                    local_component.getName(), name, local_component.path
                ))
            return local_component
        
        # otherwise, we need to update the installed component
        logger.info('update outdated: %s@%s -> %s' % (
            name,
            local_component.getVersion(),
            v
        ))
        # must rm the old component before continuing
        fsutils.rmRf(local_component.path)
        return _satisfyVersionByInstallingVersion(name, version_required, local_component.path, v)
    return None

def satisfyVersionByInstalling(name, version_required, working_directory):
    ''' installs and returns a Component for the specified name+version
        requirement, into a subdirectory of `working_directory'
    '''
    v = latestSuitableVersion(name, version_required)
    install_into = os.path.join(working_directory, name)
    return _satisfyVersionByInstallingVersion(name, version_required, install_into, v)

def _satisfyVersionByInstallingVersion(name, version_required, working_directory, version):
    ''' installs and returns a Component for the specified version requirement into
        'working_directory' using the provided remote version object.
        This function is not normally called via `satisfyVersionByInstalling',
        which looks up a suitable remote version object.
    '''
    assert(version)
    logger.info('download ' + name)
    version.unpackInto(working_directory)
    r = component.Component(working_directory)
    if not r:
        raise Exception(
            'Dependency "%s":"%s" is not a valid component.' % (name, version_required)
        )
    if name != r.getName():
        raise Exception('Component %s (specification %s) has incorrect name %s' % (
            name, version_required, r.getName()
        ))
    return r

def satisfyVersion(
        name,
        version_required,
        available,
        search_paths,
        working_directory,
        update_installed=None
    ):
    ''' returns a Component for the specified version (either to an already
        installed copy (from the available list, or from disk), or to a newly
        downloaded one), or None if the version could not be satisfied.

        update_installed = None / 'Update'
            None:   prevent any attempt to look for new versions if the
                    component already exists
            Update: replace any existing version with the newest available, if
                    the newest available has a higher version
    '''

    r = satisfyVersionFromAvailble(name, version_required, available)
    if r is not None:
        return r
    
    r = satisfyVersionFromSearchPaths(name, version_required, search_paths, update_installed == 'Update')
    if r is not None:
        return r

    return satisfyVersionByInstalling(name, version_required, working_directory)


def satisfyTarget(name, version_required, working_directory, update_installed=None):
    ''' returns a Target for the specified version (either to an already
        installed copy (from disk), or to a newly downloaded one), or None if
        the version could not be satisfied.

        update_installed = {None, 'Check', 'Update'}
            None:   prevent any attempt to look for new versions if the
                    target already exists
            Check:  check for new versions, and pass new version information to
                    the target object
            Update: replace any existing version with the newest available, if
                    the newest available has a higher version
    '''
    
    spec = None
    v = None
    
    target_path = os.path.join(working_directory, name)
    local_target = target.Target(
                    target_path,
               installed_linked = fsutils.isLink(target_path),
        latest_suitable_version = v
    )
    
    if local_target and (local_target.installedLinked() or update_installed != 'Update' or not local_target.outdated()):
        # if a target exists (has a valid description file), and either is
        # not outdated, or we are not updating
        return local_target

    # if we need to check for latest versions, get the latest available version
    # before checking for a local target so that we can create the local
    # target with a handle to its latest available version
    if update_installed is None:
        logger.debug('attempt to check latest version of %s @%s...' % (name, version_required))
        v = latestSuitableVersion(name, version_required, registry='targets')
    elif local_target and local_target.outdated():
        logger.info('%soutdated: %s@%s -> %s' % (
            ('update ' if update_installed == 'Update' else ''),
            name,
            local_target.getVersion(),
            v
        ))
        # must rm the old target before continuing
        fsutils.rmRf(target_path)

    if not v and update_installed is not None:
        v = latestSuitableVersion(name, version_required, registry='targets')

    if not v:
        raise access_common.TargetUnavailable(
            '"%s" is not a supported specification for a target (the target is %s)' % (version_required, name)
        )
    directory = os.path.join(working_directory, name)
    v.unpackInto(directory)
    r = target.Target(directory)
    if not r:
        raise Exception(
            '"%s":"%s" is not a valid target (its description file is invalid)' % (name, version_required)
        )
    return r

    
