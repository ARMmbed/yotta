# standard library modules, , ,
import logging
import re

# version, , represent versions and specifications, internal
import version
# access_common, , things shared between different component access modules, internal
import access_common
# vcs, , represent version controlled directories, internal
import vcs

logger = logging.getLogger('access')


# a GitCloneVersion represents a version in a git clone. (the version may be
# different from the checked out version in the working_copy, but should be a
# version that exists as a tag in the working_copy)
class GitCloneVersion(version.Version):
    def __init__(self, tag, working_copy):
        self.working_copy = working_copy
        self.tag = tag
        return super(GitCloneVersion, self).__init__(tag)

    def unpackInto(self, directory):
        logger.debug('unpack version %s from git repo %s to %s' % (self.version, self.working_copy.directory, directory))
        if self.isTip():
            tag = None
        else:
            tag = self.tag
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
        # return a list of GitCloneVersion objects
        return [GitCloneVersion(t, self) for t in self.vcs.tags()]

    def tipVersion(self):
        raise NotImplementedError


class GitComponent(access_common.RemoteComponent):
    def __init__(self, url, version_spec=''):
        self.url = url
        self.spec = version.Spec(version_spec)
    
    @classmethod
    def createFromNameAndSpec(cls, url, name=None):    
        ''' returns a git component for any git:// url, or None if this is not
            a git component.

            Normally version will be empty, unless the original url was of the
            form 'git://...#version', which can be used to grab a particular
            tagged version.
        '''
        # git+ssh://anything#tag or anything.git#tag formats
        m = re.match('(git\+ssh://.*|.*\.git)#?([><=.0-9a-zA-Z\*-]*)', url)
        if m:
            return GitComponent(*m.groups())
        return None

    def versionSpec(self):
        return self.spec

    # clone the remote repository: this is necessary to find out what tagged
    # versions are available.
    # The clone is created in /tmp, and is not automatically deleted, but the
    # returned version object maintains a handle to it, so that when a specific
    # version is requested it can be retrieved from the temporary clone,
    # instead of from the remote origin.
    def clone(self):
        clone = vcs.Git.cloneToTemporaryDir(self.url)
        return GitWorkingCopy(clone)

    @classmethod
    def remoteType(cls):
        return 'git'
