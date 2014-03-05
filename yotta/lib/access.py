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
# version, , represent versions and specifications, internal
import version
# fsutils, , misc filesystem utils, internal
import fsutils


# Version requirement strings we want to support:
#
# (>,>=,<,<=,)version                         # central repo
# 1.2.x                                       # central repo
# http://...                                  # tarball or zipfile
# owner/repo @((>,>=,<,<=,,)version)          # Github
# git://github.com/user/project(#version)     # Github
# git+(ssh://..., http://...)(#hash-or-tag)   # git
# hg+(ssh://..., http://...)(#hash-or-tag)    # hg
# * (any version)                             # central repo
#
# Currently working:
#
#

def latestSuitableVersion(name, version_required, registry='component'):
    ''' Return a RemoteVersion object representing the latest suitable
        version of the named component or target.

        All RemoteVersion objects have a .unpackInto(directory) method.
    '''
    if registry in ('component', 'target'):
        # If the name/spec looks like a reference to a component in the registry
        # then that takes precedence
        remote_component = registry_access.RegistryThing.createFromNameAndSpec(
            version_required, name, registry=registry
        )
        if remote_component:
            logging.debug('satisfy %s from %s registry' % (name, registry))
            vers = remote_component.availableVersions()
            spec = remote_component.versionSpec()
            v = spec.select(vers)
            if not v:
                raise Exception(
                    'The %s registry does not provide a version of "%s" matching "%s"' % (
                        registry, name, spec
                    )
                )
            return v
    else:
        raise Exception('no known registry namespace "%s"' % registry)

    # if it doesn't look like a registered component, then other schemes have a
    # go at matching the name/spec
    remote_component = github_access.GithubComponent.createFromNameAndSpec(version_required, name)
    if remote_component is not None:
        logging.debug('satisfy %s from github url' % name)
        vers = remote_component.availableVersions()
        if not len(vers):
            logging.warning(
                'Github repository "%s" has no tagged versions, master branch will be used' % (
                    remote_component.repo
                )
            )
            vers = [remote_component.tipVersion()]
        spec = remote_component.versionSpec()
        v = spec.select(vers)
        if not v:
            raise Exception(
                'Github repository "%s" does not provide a version matching "%s"' % (
                    remote_component.repo,
                    remote_component.spec
                )
            )
        return v
    
    # !!! FIXME: next test generic git/hg/etc urls
    
    return None


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

        update_installed = {None, 'Check', 'Update'}
            None:   prevent any attempt to look for new versions if the
                    component already exists
            Check:  check for new versions, and pass new version information to
                    the component object
            Update: replace any existing version with the newest available, if
                    the newest available has a higher version
    '''
    
    spec = None
    v = None

    if name in available:
        logging.debug('satisfy %s from already installed components' % name)
        try:
            spec = version.Spec(version_required)
        except Exception:
            pass
        r = available[name]
        if spec and not spec.match(r.getVersion()):
            raise Exception('Previously added component %s@%s doesn\'t meet spec %s' % (name, r.getVersion(), spec))
        return r


    # !!! FIXME: we don't update linked components, so really we should check
    # to see if the component is satisfied by a symlink before checking for the
    # latest available version

    # if we need to check for latest versions, get the latest available version
    # before checking for a local component so that we can create the local
    # component with a handle to its latest available version
    if update_installed is not None:
        #logging.debug('attempt to check latest version of %s @%s...' % (name, version_required))
        v = latestSuitableVersion(name, version_required)
    
    for path in search_paths:
        component_path = os.path.join(path, name)
        logging.debug("check path %s for %s" % (component_path, name))
        local_component = component.Component(
                     component_path,
               installed_previously = True,
                   installed_linked = fsutils.isLink(component_path),
            latest_suitable_version = v
        )
        logging.debug("%s %s" % (('found', 'not found')[not local_component], name))
        if local_component and (local_component.installedLinked() or update_installed != 'Update' or not local_component.outdated()):
            logging.debug("satisfy component from directory: %s" % component_path)
            # if a component exists (has a valid description file), and either is
            # not outdated, or we are not updating
            return local_component
        elif local_component and local_component.outdated():
            logging.info('%soutdated: %s@%s -> %s' % (
                ('update ' if update_installed == 'Update' else ''),
                name,
                local_component.getVersion(),
                v
            ))
            # must rm the old component before continuing
            fsutils.rmRf(component_path)
        if local_component:
            # once we've found one stop (ignore any other matching components
            # in the search path)
            break

    if not v and update_installed is None:
        v = latestSuitableVersion(name, version_required)

    if not v:
        raise access_common.ComponentUnavailable(
            'Dependency "%s":"%s" is not a supported form.' % (name, version_required)
        )
    directory = os.path.join(working_directory, name)
    v.unpackInto(directory)
    r = component.Component(directory)
    if not r:
        raise Exception(
            'Dependency "%s":"%s" is not a valid component.' % (name, version_required)
        )
    return r


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

    # if we need to check for latest versions, get the latest available version
    # before checking for a local target so that we can create the local
    # target with a handle to its latest available version
    if update_installed is not None:
        logging.debug('attempt to check latest version of %s @%s...' % (name, version_required))
        v = latestSuitableVersion(name, version_required, registry='target')
    
    target_path = os.path.join(working_directory, name)
    local_target = target.Target(
                    target_path,
               installed_linked = fsutils.isLink(target_path),
        latest_suitable_version = v
    )
    if local_target and (update_installed != 'Update' or not local_target.outdated()):
        # if a target exists (has a valid description file), and either is
        # not outdated, or we are not updating
        return local_target
    elif local_target and local_target.outdated():
        logging.info('%soutdated: %s@%s -> %s' % (
            ('update ' if update_installed == 'Update' else ''),
            name,
            local_target.getVersion(),
            v
        ))
        # must rm the old target before continuing
        fsutils.rmRf(target_path)

    if not v and update_installed is None:
        v = latestSuitableVersion(name, version_required, registry='target')

    if not v:
        raise access_common.TargetUnavailable(
            'Target "%s":"%s" is not a supported form.' % (name, version_required)
        )
    directory = os.path.join(working_directory, name)
    v.unpackInto(directory)
    r = target.Target(directory)
    if not r:
        raise Exception(
            'Dependency "%s":"%s" is not a valid target.' % (name, version_required)
        )
    return r

    
