# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import os
import subprocess
import tempfile
import logging
import errno

# fsutils, , misc filesystem utils, internal
import fsutils

git_logger = logging.getLogger('git')
hg_logger = logging.getLogger('hg')

class VCSError(Exception):
    def __init__(self, message, returncode=None):
        super(VCSError, self).__init__(message)
        self.returncode = returncode

class VCS(object):
    @classmethod
    def cloneToTemporaryDir(cls, remote):
        raise NotImplementedError()

    @classmethod
    def cloneToDirectory(cls, remote, directory, tag=None):
        raise NotImplementedError()

    def commit(self, message, tag=None):
        raise NotImplementedError()
    def isClean(self):
        raise NotImplementedError()
    def tags(self):
        raise NotImplementedError()
    def markForCommit(self, path):
        pass
    def remove(self):
        raise NotImplementedError()
    def getCommitId(self):
        raise NotImplementedError()
    def __nonzero__(self):
        raise NotImplementedError()
    # python 3 truthiness
    def __bool__(self):
        return self.__nonzero__()


class Git(VCS):
    def __init__(self, path):
        self.worktree = path
        self.gitdir = os.path.join(path, '.git')

    @classmethod
    def cloneToTemporaryDir(cls, remote):
        return cls.cloneToDirectory(remote, tempfile.mkdtemp())

    @classmethod
    def cloneToDirectory(cls, remote, directory, tag=None):
        commands = [
            ['git', 'clone',  remote, directory]
        ]
        cls._execCommands(commands)
        r = Git(directory)
        if tag is not None:
            r.updateToTag(tag)
        return r

    def fetchAllBranches(self):
        remote_branches = []
        local_branches = []

        # list remote branches
        out, err = self._execCommands([self._gitCmd('branch', '-r')])

        for line in out.split(b'\n'):
            branch_info = line.split(b' -> ')
            # skip HEAD:
            if len(branch_info) > 1:
                continue
            remote_branch = branch_info[0].strip()
            branch = b'/'.join(remote_branch.split(b'/')[1:])
            remote_branches.append((remote_branch, branch))

        # list already-existing local branches
        out, err = self._execCommands([self._gitCmd('branch')])
        for line in out.split(b'\n'):
            local_branches.append(line.strip(b' *'))

        for remote, branchname in remote_branches:
            # don't try to replace existing local branches
            if branchname in local_branches:
                continue
            try:
                out, err = self._execCommands([
                    self._gitCmd('checkout', '-b', branchname, remote)
                ])
            except VCSError as e:
                git_logger.error('failed to fetch remote branch %s %s' % (remote, branchname))
                raise

    def remove(self):
        fsutils.rmRf(self.worktree)

    def getCommitId(self):
        out, err = self._execCommands([self._gitCmd('rev-parse', 'HEAD')])
        return out.strip()

    def workingDirectory(self):
        return self.worktree

    def _gitCmd(self, *args):
        return ['git','--work-tree=%s' % self.worktree,'--git-dir=%s'%self.gitdir.replace('\\', '/')] + list(args);

    @classmethod
    def _execCommands(cls, commands):
        out, err = None, None
        for cmd in commands:
            try:
                child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except OSError as e:
                if e.errno == errno.ENOENT:
                    if cmd[0] == 'git':
                        raise VCSError(
                            'git is not installed, or not in your path. Please follow the installation instructions at http://docs.yottabuild.org/#installing'
                        )
                    else:
                        raise VCSError('%s is not installed' % (cmd[0]))
                else:
                    raise VCSError('command %s failed' % (cmd))
            out, err = child.communicate()
            returncode = child.returncode
            if returncode:
                raise VCSError("command failed: %s:%s" % (cmd, err or out), returncode=returncode)
        return out, err

    def isClean(self):
        commands = [
            self._gitCmd('diff', '--quiet', '--exit-code'),
            self._gitCmd('diff', '--cached', '--quiet', '--exit-code'),
        ]
        try:
            out, err = self._execCommands(commands)
        except VCSError as e:
            if e.returncode:
                return False
            else:
                raise
        return True

    def markForCommit(self, relative_path):
        commands = [
            self._gitCmd('add', os.path.join(self.worktree, relative_path)),
        ]
        self._execCommands(commands)

    def updateToTag(self, tag):
        commands = [
            self._gitCmd('checkout', tag),
        ]
        self._execCommands(commands)


    def tags(self):
        commands = [
            self._gitCmd('tag', '-l')
        ]
        out, err = self._execCommands(commands)
        # I think utf-8 is the right encoding? commit messages are utf-8
        # encoded, couldn't find any documentation on tag names.
        return out.decode('utf-8').split(u'\n')

    def branches(self):
        commands = [
            self._gitCmd('branch', '--list')
        ]
        out, err = self._execCommands(commands)
        return [x.lstrip(' *') for x in out.decode('utf-8').split('\n')]

    def commit(self, message, tag=None):
        commands = [
            self._gitCmd('commit', '-m', message),
        ]
        if tag:
            commands.append(
                self._gitCmd('tag', tag, '-a', '-m', tag),
            )
        self._execCommands(commands)

    def __nonzero__(self):
        return True


# FIXME: hgapi will throw HgException when something goes wrong, it may be worth trying
# to catch that in some methods
class HG(VCS):
    hgapi = None
    def __init__(self, path):
        self._loadHGApi()
        self.worktree = path
        self.repo = self.hgapi.Repo(path)

    @classmethod
    def _loadHGApi(cls):
        # only import hgapi on demand, since it is rarely needed
        if cls.hgapi is None:
            import hgapi
            cls.hgapi = hgapi

    @classmethod
    def cloneToTemporaryDir(cls, remote):
        return cls.cloneToDirectory(remote, tempfile.mkdtemp())

    @classmethod
    def cloneToDirectory(cls, remote, directory, tag=None):
        cls._loadHGApi()
        # hg doesn't automatically create the directories needed by destination
        try:
            os.makedirs(directory)
        except:
            pass
        hg_logger.debug('will clone %s into %s', remote, directory)
        cls.hgapi.Repo.hg_clone(remote, directory)
        r = HG(directory)
        if tag is not None:
            r.updateToTag(tag)
        return r

    def remove(self):
        fsutils.rmRf(self.worktree)

    def getCommitId(self):
        return self.repo.hg_node()

    def workingDirectory(self):
        return self.worktree

    def isClean(self):
        return not bool(self.repo.hg_status(empty=True))

    def markForCommit(self, relative_path):
        self.repo.hg_add(os.path.join(self.worktree, relative_path))

    def updateToTag(self, tag):
        self.repo.hg_update(tag)

    def tags(self):
        l = list(self.repo.hg_tags().keys())
        l.remove('tip')
        return l

    def commit(self, message, tag=None):
        self.repo.hg_commit(message)
        if tag:
            self.repo.hg_tag(tag)

    def __nonzero__(self):
        return True

def getVCS(path):
    # crude heuristic, does the job...
    if os.path.exists(os.path.join(path, '.git')):
        return Git(path)
    if os.path.isdir(os.path.join(path, '.hg')):
        return HG(path)
    return None

