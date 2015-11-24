#!/usr/bin/env python
# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# standard library modules, , ,
import unittest
import os
import subprocess
import hgapi

# vcs, , represent version controlled directories, internal
from yotta.lib import vcs
# fsutils, , misc filesystem utils, internal
from yotta.lib import fsutils


Test_Repo_git = "git@github.com:autopulated/testing-dummy.git"
Test_Repo_hg  = "ssh://hg@bitbucket.org/autopulated/hg-testing-dummy"

class TestGit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
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
        cls.working_copy = vcs.Git.cloneToTemporaryDir(Test_Repo_git)

    @classmethod
    def tearDownClass(cls):
        cls.working_copy.remove()

    def test_creation(self):
        self.assertTrue(self.working_copy)

    def test_getCommitId(self):
        commit_id = self.working_copy.getCommitId()
        self.assertTrue(len(commit_id) >= 6)

    def test_isClean(self):
        self.assertTrue(self.working_copy.isClean())
        fsutils.rmF(os.path.join(self.working_copy.workingDirectory(), 'module.json'))
        self.assertFalse(self.working_copy.isClean())

    def test_commit(self):
        with open(os.path.join(self.working_copy.workingDirectory(), 'module.json'), "a") as f:
            f.write("\n")
        self.working_copy.markForCommit('module.json')
        self.working_copy.commit('test commit: DO NOT PUSH')
        self.assertTrue(self.working_copy.isClean())

class TestHg(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # test if we have a git user set up, if not we need to set one
        info = hgapi.Repo.command(".", os.environ, "showconfig")
        if info.find("ui.username") == -1:
            # hg doesn't provide a way to set the username from the command line.
            # The HGUSER environment variable can be used for that purpose.
            os.environ['HGUSER'] = 'Yotta Test <test@yottabuild.org>'
        cls.working_copy = vcs.HG.cloneToTemporaryDir(Test_Repo_hg)

    @classmethod
    def tearDownClass(cls):
        cls.working_copy.remove()

    def test_creation(self):
        self.assertTrue(self.working_copy)

    def test_getCommitId(self):
        commit_id = self.working_copy.getCommitId()
        self.assertTrue(len(commit_id) >= 6)

    def test_isClean(self):
        self.assertTrue(self.working_copy.isClean())
        fsutils.rmF(os.path.join(self.working_copy.workingDirectory(), 'module.json'))
        self.assertFalse(self.working_copy.isClean())

    def test_commit(self):
        with open(os.path.join(self.working_copy.workingDirectory(), 'module.json'), "a") as f:
            f.write("\n")
        self.working_copy.markForCommit('module.json')
        self.working_copy.commit('test commit: DO NOT PUSH')
        self.assertTrue(self.working_copy.isClean())

if __name__ == '__main__':
    unittest.main()
