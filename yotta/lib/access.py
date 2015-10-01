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
# Pack, , base class for targets and components, internal
import pack
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

def latestSuitableVersion(name, version_required, registry='modules', quiet=False):
    ''' Return a RemoteVersion object representing the latest suitable
        version of the named component or target.

        All RemoteVersion objects have a .unpackInto(directory) method.
    '''

    remote_component = remoteComponentFor(name, version_required, registry)

    if quiet:
        logger.debug('get versions for ' + name)
    else:
        logger.info('get versions for ' + name)

    if remote_component.remoteType() == 'registry':
        logger.debug('satisfy %s from %s registry' % (name, registry))
        vers = remote_component.availableVersions()
        spec = remote_component.versionSpec()
        v = spec.select(vers)
        logger.debug("%s selected %s from %s", spec, v, vers)
        if not v:
            raise access_common.Unavailable(
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
                raise access_common.Unavailable(
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
            raise access_common.Unavailable(
                'Github repository "%s" does not have any tags or branches matching "%s"' % (
                    version_required, remote_component.tagOrBranchSpec()
                )
            )

    elif remote_component.remoteType() in ('git', 'hg'):
        clone_type = remote_component.remoteType()
        logger.debug('satisfy %s from %s url' % (name, clone_type))
        local_clone = remote_component.clone()
        if not local_clone:
            raise access_common.Unavailable(
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
                raise access_common.Unavailable(
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
            raise access_common.Unavailable(
                '%s repository "%s" does not have any tags or branches matching "%s"' % (
                    clone_type, version_required, spec
                )
            )
        else:
            raise Exception("invalid spec for hg source: tags/branches are not supported yet!")

    # !!! FIXME: next: generic http urls to tarballs

    return None

def searchPathsFor(name, spec, search_paths, type='module'):
    for path in search_paths:
        check_path = os.path.join(path, name)
        logger.debug("check path %s for %s" % (check_path, name))
        instance = _clsForType(type)(
                     check_path,
                   installed_linked = fsutils.isLink(check_path),
            latest_suitable_version = None
        )
        if instance:
            logger.debug("got %s v=%s spec %s matches? %s", instance, instance.getVersion(), spec, spec.match(instance.getVersion()))
            if spec.match(instance.getVersion()):
                return instance
        else:
            logger.debug("got %s", instance)
    return None

def _registryNamespaceForType(type):
    assert(type in ('module', 'target'))
    return type + 's'

def _clsForType(type):
    assert(type in ('module', 'target'))
    return {'module':component.Component, 'target':target.Target}[type]

def satisfyFromAvailable(name, available, type='module'):
    if name in available and available[name]:
        logger.debug('satisfy %s from already installed %ss' % (name, type))
        r = available[name]
        if name != r.getName():
            raise access_common.Unavailable('%s %s was installed as different name %s in %s' % (
                type, r.getName(), name, r.path
            ))
        return r
    return None

def satisfyVersionFromSearchPaths(name, version_required, search_paths, update=False, type='module'):
    ''' returns a Component/Target for the specified version, if found in the
        list of search paths. If `update' is True, then also check for newer
        versions of the found component, and update it in-place (unless it was
        installed via a symlink).
    '''
    v    = None

    try:
        local_version = searchPathsFor(
            name,
            sourceparse.parseSourceURL(version_required).semanticSpec(),
            search_paths,
            type
        )
    except pack.InvalidDescription as e:
        logger.error(e)
        return None

    logger.debug("%s %s locally" % (('found', 'not found')[not local_version], name))
    if local_version:
        if update and not local_version.installedLinked():
            #logger.debug('attempt to check latest version of %s @%s...' % (name, version_required))
            v = latestSuitableVersion(name, version_required, registry=_registryNamespaceForType(type))
            if local_version:
                local_version.setLatestAvailable(v)

        # if we don't need to update, then we're done
        if local_version.installedLinked() or not local_version.outdated():
            logger.debug("satisfy component from directory: %s" % local_version.path)
            # if a component exists (has a valid description file), and either is
            # not outdated, or we are not updating
            if name != local_version.getName():
                raise Exception('Component %s found in incorrectly named directory %s (%s)' % (
                    local_version.getName(), name, local_version.path
                ))
            return local_version

        # otherwise, we need to update the installed component
        logger.info('update outdated: %s@%s -> %s' % (
            name,
            local_version.getVersion(),
            v
        ))
        # must rm the old component before continuing
        fsutils.rmRf(local_version.path)
        return _satisfyVersionByInstallingVersion(name, version_required, local_version.path, v, type=type)
    return None

def satisfyVersionByInstalling(name, version_required, working_directory, type='module'):
    ''' installs and returns a Component/Target for the specified name+version
        requirement, into a subdirectory of `working_directory'
    '''
    v = latestSuitableVersion(name, version_required, _registryNamespaceForType(type))
    install_into = os.path.join(working_directory, name)
    return _satisfyVersionByInstallingVersion(
        name, version_required, install_into, v, type=type
    )

def _satisfyVersionByInstallingVersion(name, version_required, working_directory, version, type='module'):
    ''' installs and returns a Component/Target for the specified version requirement into
        'working_directory' using the provided remote version object.
        This function is not normally called via `satisfyVersionByInstalling',
        which looks up a suitable remote version object.
    '''
    assert(version)
    logger.info('download %s', version)
    version.unpackInto(working_directory)
    r = _clsForType(type)(working_directory)
    if not r:
        raise Exception(
            'Dependency "%s":"%s" is not a valid %s.' % (name, version_required, type)
        )
    if name != r.getName():
        raise Exception('%s %s (specification %s) has incorrect name %s' % (
            type, name, version_required, r.getName()
        ))
    return r

def satisfyVersion(
        name,
        version_required,
        available,
        search_paths,
        working_directory,
        update_installed=None,
        type='module'  # or 'target'
    ):
    ''' returns a Component/Target for the specified version (either to an already
        installed copy (from the available list, or from disk), or to a newly
        downloaded one), or None if the version could not be satisfied.

        update_installed = None / 'Update'
            None:   prevent any attempt to look for new versions if the
                    component/target already exists
            Update: replace any existing version with the newest available, if
                    the newest available has a higher version
    '''

    r = satisfyFromAvailable(name, available, type=type)
    if r is not None:
        if not sourceparse.parseSourceURL(version_required).semanticSpecMatches(r.getVersion()):
            raise access_common.SpecificationNotMet(
                "Installed %s %s doesn't match specification %s" % (type, name, version_required)
            )
        return r

    r = satisfyVersionFromSearchPaths(name, version_required, search_paths, update_installed == 'Update', type=type)
    if r is not None:
        return r

    return satisfyVersionByInstalling(name, version_required, working_directory, type=type)


def satisfyTarget(name, version_required, working_directory, update_installed=None):
    return satisfyVersion(
                    name = name,
        version_required = version_required,
               available = {},
            search_paths = [working_directory],
       working_directory = working_directory,
        update_installed = update_installed,
                    type = 'target'
    )
