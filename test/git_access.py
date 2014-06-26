#!/usr/bin/env python

# standard library modules, , ,
import unittest
import os
import subprocess

# git_access, , access to components available from git repositories, internal
from yotta.lib import git_access
# fsutils, , misc filesystem utils, internal
from yotta.lib import fsutils
# version, , represent versions and specifications, internal
from yotta.lib import version


Test_Name = 'testing-dummy'
Test_Repo = "git@github.com:autopulated/testing-dummy.git"
Test_Repo_With_Spec = "git@github.com:autopulated/testing-dummy.git#0.0.1"


def ensureGitConfig():
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


class TestGitAccess(unittest.TestCase):
    def setUp(self):
        ensureGitConfig()
        self.remote_component = git_access.GitComponent.createFromNameAndSpec(Test_Repo, Test_Name)
        self.assertTrue(self.remote_component)
        self.working_copy = self.remote_component.clone()
        self.assertTrue(self.working_copy)
        
    def tearDown(self):
        fsutils.rmRf(self.working_copy.directory)

    def test_availableVersions(self):
        versions = self.working_copy.availableVersions()
        self.assertIn(version.Version('v0.0.1'), versions)

    def test_versionSpec(self):
        spec = git_access.GitComponent.createFromNameAndSpec(Test_Repo_With_Spec, Test_Name).versionSpec()
        v = spec.select(self.working_copy.availableVersions())
        self.assertTrue(v)

if __name__ == '__main__':
    unittest.main()

