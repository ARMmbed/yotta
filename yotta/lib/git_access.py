# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import logging

# version, , represent versions and specifications, internal
from yotta.lib import version
# access_common, , things shared between different component access modules, internal
from yotta.lib import access_common

logger = logging.getLogger('access')


# a GitCloneVersion represents a version in a git clone. (the version may be
# different from the checked out version in the working_copy, but should be a
# version that exists as a tag in the working_copy)
class GitCloneVersion(version.Version):
    def __init__(self, semver, tag, working_copy):
        self.working_copy = working_copy
        self.tag = tag
        super(GitCloneVersion, self).__init__(semver)

    def unpackInto(self, directory):
        # vcs, , represent version controlled directories, internal
        from yotta.lib import vcs
        # fsutils, , misc filesystem utils, internal
        from yotta.lib import fsutils
        logger.debug('unpack version %s from git repo %s to %s' % (self.version, self.working_copy.directory, directory))
        tag = self.tag
        fsutils.rmRf(directory)
        vcs.Git.cloneToDirectory(self.working_copy.directory, directory, tag)

        # remove temporary files created by the GitWorkingCopy clone
        self.working_copy.remove()

class GitWorkingCopy(object):
    def __init__(self, vcs):
        self.vcs = vcs
        self.directory = vcs.workingDirectory()

    def remove(self):
        self.vcs.remove()
        self.directory = None

    def availableVersions(self):
        ''' return a list of GitCloneVersion objects for tags which are valid
            semantic version idenfitifiers.
        '''
        r = []
        for t in self.vcs.tags():
            logger.debug("available version tag: %s", t)
            # ignore empty tags:
            if not len(t.strip()):
                continue
            try:
                r.append(GitCloneVersion(t, t, self))
            except ValueError:
                logger.debug('invalid version tag: %s', t)
        return r

    def availableTags(self):
        ''' return a list of GitCloneVersion objects for all tags
        '''
        return [GitCloneVersion('', t, self) for t in self.vcs.tags()]

    def availableBranches(self):
        ''' return a list of GitCloneVersion objects for the tip of each branch
        '''
        return [GitCloneVersion('', b, self) for b in self.vcs.branches()]


    def tipVersion(self):
        return GitCloneVersion('', '', self)

    def commitVersion(self, spec):
        ''' return a GithubComponentVersion object for a specific commit if valid
        '''
        import re

        commit_match = re.match('^[a-f0-9]{7,40}$', spec, re.I)
        if commit_match:
            return GitCloneVersion('', spec, self)

        return None

class GitComponent(access_common.RemoteComponent):
    def __init__(self, url, tag_or_branch=None, semantic_spec=None):
        logging.debug('create git component for url:%s version spec:%s' % (url, semantic_spec or tag_or_branch))
        self.url = url
        # !!! TODO: handle non-semantic spec
        self.spec = semantic_spec
        self.tag_or_branch = tag_or_branch

    @classmethod
    def createFromSource(cls, vs, name=None):
        ''' returns a git component for any git:// url, or None if this is not
            a git component.

            Normally version will be empty, unless the original url was of the
            form 'git://...#version', which can be used to grab a particular
            tag or branch, or ...#>=1.2.3, which can be used to specify
            semantic version specifications on tags.
        '''
        return GitComponent(vs.location, vs.spec, vs.semantic_spec)

    def versionSpec(self):
        return self.spec

    def tagOrBranchSpec(self):
        return self.tag_or_branch

    # clone the remote repository: this is necessary to find out what tagged
    # versions are available.
    # The clone is created in /tmp, and is not automatically deleted, but the
    # returned version object maintains a handle to it, so that when a specific
    # version is requested it can be retrieved from the temporary clone,
    # instead of from the remote origin.
    def clone(self):
        # vcs, , represent version controlled directories, internal
        from yotta.lib import vcs
        clone = vcs.Git.cloneToTemporaryDir(self.url)
        clone.fetchAllBranches()
        return GitWorkingCopy(clone)

    @classmethod
    def remoteType(cls):
        return 'git'
