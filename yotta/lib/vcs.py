# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import os
import subprocess
import tempfile
import logging
import hgapi

# fsutils, , misc filesystem utils, internal
import fsutils

git_logger = logging.getLogger('git')
hg_logger = logging.getLogger('hg')



class VCS(object):
    @classmethod
    def cloneToTemporaryDir(cls, remote):
        raise NotImplementedError()

    @classmethod
    def cloneToDirectory(cls, remote, directory, tag=None):
        raise NotImplementedError()

    def isClean(self):
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
        for cmd in commands:
            git_logger.debug('will clone %s into %s', remote, directory)
            child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = child.communicate()
            git_logger.debug('clone %s into %s: %s', remote, directory, out or err)
            if child.returncode:
                raise Exception('failed to clone repository %s: %s', remote, err or out)
        r = Git(directory)
        if tag is not None:
            r.updateToTag(tag)
        return r
    
    def fetchAllBranches(self):
        remote_branches = []
        local_branches = []
        
        # list remote branches
        cmd = self._gitCmd('branch', '-r')
        child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = child.communicate()
        if child.returncode:
            raise Exception('command failed: %s:%s', cmd, err or out)

        for line in out.split(b'\n'):
            branch_info = line.split(b' -> ')
            # skip HEAD:
            if len(branch_info) > 1:
                continue
            remote_branch = branch_info[0].strip()
            branch = b'/'.join(remote_branch.split(b'/')[1:])
            remote_branches.append((remote_branch, branch))
        
        # list already-existing local branches
        cmd = self._gitCmd('branch')
        child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = child.communicate()
        if child.returncode:
            raise Exception('command failed: %s:%s', cmd, err or out)
        for line in out.split(b'\n'):
            local_branches.append(line.strip(b' *'))

        for remote, branchname in remote_branches:
            # don't try to replace existing local branches
            if branchname in local_branches:
                continue
            cmd = self._gitCmd('checkout', '-b', branchname, remote)
            child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = child.communicate()
            if child.returncode:
                raise Exception('failed to fetch remote branches %s:%s', cmd, err or out)

    def remove(self):
        fsutils.rmRf(self.worktree)

    def workingDirectory(self):
        return self.worktree

    def _gitCmd(self, *args):
        return ['git','--work-tree=%s' % self.worktree,'--git-dir=%s'%self.gitdir] + list(args);

    def _execCommands(self, commands):
        out, err = None, None
        for cmd in commands:
            child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = child.communicate()
            if child.returncode:
                raise Exception('command failed: %s:%s', cmd, err or out)
        return out, err

    def isClean(self):
        commands = [
            self._gitCmd('diff', '--quiet', '--exit-code'),
            self._gitCmd('diff', '--cached', '--quiet', '--exit-code'),
        ]
        for cmd in commands:
            child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = child.communicate()
            if child.returncode:
                return False
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
                self._gitCmd('tag', tag),
            )
        for cmd in commands:
            child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = child.communicate()
            if child.returncode:
                raise Exception('command failed: %s:%s', cmd, err or out)

    def __nonzero__(self):
        return True


# FIXME: hgapi will throw HgException when something goes wrong, it may be worth trying
# to catch that in some methods
class HG(VCS):
    def __init__(self, path):
        self.worktree = path
        self.repo = hgapi.Repo(path)

    @classmethod
    def cloneToTemporaryDir(cls, remote):
        return cls.cloneToDirectory(remote, tempfile.mkdtemp())

    @classmethod
    def cloneToDirectory(cls, remote, directory, tag=None):
        # hg doesn't automatically create the directories needed by destination
        try:
            os.makedirs(directory)
        except:
            pass
        hg_logger.debug('will clone %s into %s', remote, directory)
        hgapi.Repo.hg_clone(remote, directory)
        r = HG(directory)
        if tag is not None:
            r.updateToTag(tag)
        return r

    def remove(self):
        fsutils.rmRf(self.worktree)

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
    if os.path.isdir(os.path.join(path, '.git')):
        return Git(path)
    if os.path.isdir(os.path.join(path, '.hg')):
        return HG(path)
    return None

