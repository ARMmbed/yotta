#!/usr/bin/env python
# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# standard library modules, , ,
import unittest
import subprocess
from collections import namedtuple

# git_access, , access to components available from git repositories, internal
from yotta.lib import git_access
# fsutils, , misc filesystem utils, internal
from yotta.lib import fsutils
# version, , represent versions and specifications, internal
from yotta.lib import version
# sourceparse, , parse version source urls, internal
from yotta.lib import sourceparse
# install, , install components, internal
from yotta import install


Test_Name = 'testing-dummy'
Test_Repo = "git@github.com:autopulated/testing-dummy.git"
Test_Repo_With_Spec = "git@github.com:autopulated/testing-dummy.git#0.0.1"
Test_Deps_Name = 'git-access-testing'
Test_Deps_Target = 'x86-osx-native,*'


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
        vs = sourceparse.parseSourceURL(Test_Repo)
        self.remote_component = git_access.GitComponent.createFromSource(vs, Test_Name)
        self.assertTrue(self.remote_component)
        self.working_copy = self.remote_component.clone()
        self.assertTrue(self.working_copy)

    def tearDown(self):
        fsutils.rmRf(self.working_copy.directory)

    def test_availableVersions(self):
        versions = self.working_copy.availableVersions()
        self.assertIn(version.Version('v0.0.1'), versions)

    def test_versionSpec(self):
        vs = sourceparse.parseSourceURL(Test_Repo_With_Spec)
        spec = git_access.GitComponent.createFromSource(vs, Test_Name).versionSpec()
        v = spec.select(self.working_copy.availableVersions())
        self.assertTrue(v)

    def test_installDeps(self):
        Args = namedtuple('Args', ['component', 'target', 'act_globally', 'install_linked', 'install_test_deps'])
        install.installComponent(Args(Test_Deps_Name, Test_Deps_Target, False, False, 'own'))


if __name__ == '__main__':
    unittest.main()

