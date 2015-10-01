#!/usr/bin/env python
# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# standard library modules, , ,
import unittest
from collections import namedtuple

# settings, , load and save settings, internal
from yotta.lib import settings
# globalconf, share global arguments between modules, internal
from yotta.lib import globalconf
# install, , install components, internal
from yotta import install

globalconf.set('interactive', False)

Test_Name = 'testing-dummy'
Test_Deps_Name = "autopulated/github-access-testing"
Test_Branch_Name = "autopulated/github-access-testing#master"
Test_Deps_Target = "x86-osx-native,*"

def hasGithubConfig():
    # can't run tests that hit github without an authn token
    if not settings.getProperty('github', 'authtoken'):
        return False
    return True

class TestGitHubAccess(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @unittest.skipIf(not hasGithubConfig(), "a github authtoken must be specified for this test (run yotta login, or set YOTTA_GITHUB_AUTHTOKEN)")
    def test_installDeps(self):
        Args = namedtuple('Args', ['component', 'target', 'act_globally', 'install_linked', 'install_test_deps'])
        install.installComponent(Args(Test_Deps_Name, Test_Deps_Target, False, False, 'own'))

    @unittest.skipIf(not hasGithubConfig(), "a github authtoken must be specified for this test (run yotta login, or set YOTTA_GITHUB_AUTHTOKEN)")
    def test_branchAccess(self):
        Args = namedtuple('Args', ['component', 'target', 'act_globally', 'install_linked', 'install_test_deps'])
        install.installComponent(Args(Test_Branch_Name, Test_Deps_Target, False, False, 'own'))


if __name__ == '__main__':
    unittest.main()


