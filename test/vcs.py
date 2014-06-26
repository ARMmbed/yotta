#!/usr/bin/env python

# standard library modules, , ,
import unittest
import os
import subprocess

# vcs, , represent version controlled directories, internal
from yotta.lib import vcs
# fsutils, , misc filesystem utils, internal
from yotta.lib import fsutils


Test_Repo = "git@github.com:autopulated/testing-dummy.git"

class TestGit(unittest.TestCase):
    def setUp(self):
        # test if we have a git user set up, if not we need to set one
        child = subprocess.Popen([
                'git','config', '--global', 'user.email'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        out, err = child.communicate()
        if not len(out):
            commands = [
                ['git','config', '--global', 'user.email', 'test@yottabuild.org'],
                ['git','config', '--global', 'user.name', 'Yotta Test']
            ]
            for cmd in commands:
                child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = child.communicate()
        self.working_copy = vcs.Git.cloneToTemporaryDir(Test_Repo)
        self.assertTrue(self.working_copy)
        
    def tearDown(self):
        self.working_copy.remove()

    def test_isClean(self):
        self.assertTrue(self.working_copy.isClean())
        fsutils.rmF(os.path.join(self.working_copy.workingDirectory(), 'package.json'))
        self.assertFalse(self.working_copy.isClean())
    
    def test_commit(self):
        with open(os.path.join(self.working_copy.workingDirectory(), 'package.json'), "a") as f:
            f.write("\n")
        self.working_copy.markForCommit('package.json')
        self.working_copy.commit('test commit: DO NOT PUSH')
        self.assertTrue(self.working_copy.isClean())

if __name__ == '__main__':
    unittest.main()
