# standard library modules, , ,
import os
import logging

# Component, , represents an installed component, internal
import component
# Access common, , components shared between access modules, internal
import access_common
# Github Access, , access repositories on github, internal
import github_access
# version, , represent versions and specifications, internal
import version



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

def satisfyVersion(name, version_required, working_directory, available):
    ''' returns a Component for the specified version (either to an already
        installed copy (from the available list), or to a newly downloaded
        one), or None if the version could not be satisfied.
    '''
    
    spec = None

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

    # !!! FIXME: next test against the central module repository (mbed?)

    remote_component = github_access.GithubComponent.createFromURL(version_required)
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
        directory = os.path.join(working_directory, name)
        v.unpackInto(directory)
        r = component.Component(directory)
        if not r:
            raise Exception(
                'Github repository "%s" version "%s" is not a valid component' % (
                    remote_component.repo,
                    remote_component.spec
                )
            )
        return r
    
    # !!! FIXME: next test generic git/hg/etc urls
    
    raise access_common.ComponentUnavailable('Dependency "%s":"%s" is not a supported form.' % (name, version_required))
