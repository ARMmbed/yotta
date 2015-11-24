#!/usr/bin/env python
# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# standard library modules, , ,
import unittest
import os
from collections import namedtuple

# hgapi, pip install hgapi, python api to hg command, "Do whatever you want,
# but don't blame me"
import hgapi

# hg_access, , access to components available from hg repositories, internal
from yotta.lib import hg_access
# fsutils, , misc filesystem utils, internal
from yotta.lib import fsutils
# version, , represent versions and specifications, internal
from yotta.lib import version
# sourceparse, , parse version source urls, internal
from yotta.lib import sourceparse
# install, , install components, internal
from yotta import install


Test_Name = 'hg-testing-dummy'
Test_Repo = "hg+ssh://hg@bitbucket.org/autopulated/hg-testing-dummy"
Test_Repo_With_Spec = "hg+ssh://hg@bitbucket.org/autopulated/hg-testing-dummy#0.0.2"
Test_Deps_Name = 'hg-access-testing'
Test_Deps_Target = 'x86-osx-native,*'


def ensureHGConfig():
    # test if we have a hg user set up, if not we need to set one
    info = hgapi.Repo.command(".", os.environ, "showconfig")
    if info.find("ui.username") == -1:
        # hg doesn't provide a way to set the username from the command line.
        # The HGUSER environment variable can be used for that purpose.
        os.environ['HGUSER'] = 'Yotta Test <test@yottabuild.org>'

class TestHGAccess(unittest.TestCase):
    def setUp(self):
        ensureHGConfig()
        vs = sourceparse.parseSourceURL(Test_Repo)
        self.remote_component = hg_access.HGComponent.createFromSource(vs, Test_Name)
        self.assertTrue(self.remote_component)
        self.working_copy = self.remote_component.clone()
        self.assertTrue(self.working_copy)

    def tearDown(self):
        fsutils.rmRf(self.working_copy.directory)

    def test_installDeps(self):
        Args = namedtuple('Args', ['component', 'target', 'act_globally', 'install_linked', 'install_test_deps'])
        install.installComponent(Args(Test_Deps_Name, Test_Deps_Target, False, False, 'own'))

    def test_availableVersions(self):
        versions = self.working_copy.availableVersions()
        self.assertIn(version.Version('v0.0.1'), versions)

    def test_versionSpec(self):
        vs = sourceparse.parseSourceURL(Test_Repo_With_Spec)
        spec = hg_access.HGComponent.createFromSource(vs, Test_Name).versionSpec()
        v = spec.select(self.working_copy.availableVersions())
        self.assertTrue(v)

if __name__ == '__main__':
    unittest.main()

