# standard library modules, , ,
import os
import subprocess


class VCS(object):
    def isClean(self):
        raise NotImplementedError()
    def commit(self, message, tag=None):
        raise NotImplementedError()
    def markForCommit(self, path):
        pass
    def __nonzero__(self):
        raise NotImplementedError()
    

class Git(VCS):
    def __init__(self, path):
        self.worktree = path
        self.gitdir = os.path.join(path, '.git')

    def _gitCmd(self, *args):
        return ['git','--work-tree=%s' % self.worktree,'--git-dir=%s'%self.gitdir] + list(args);

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
        for cmd in commands:
            child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = child.communicate()
            if child.returncode:
                raise Exception('command failed: %s', cmd)


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
                raise Exception('command failed: %s', cmd)

    def __nonzero__(self):
        return True


def getVCS(path):
    # crude heuristic, does the job...
    if os.path.isdir(os.path.join(path, '.git')):
        return Git(path)
    # !!! FIXME: support other version control systems than git
    return None


