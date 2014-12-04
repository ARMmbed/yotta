#!/usr/bin/env python
# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# standard library modules, , ,
import unittest
import os
import subprocess
from collections import namedtuple

# version, , represent versions and specifications, internal
from yotta.lib import version
# settings, , load and save settings, internal
from yotta.lib import settings
# install, , install components, internal
from yotta import install


Test_Name = 'testing-dummy'
Test_Deps_Name = "autopulated/github-access-testing"
Test_Branch_Name = "autopulated/github-access-testing#master"
Test_Deps_Target = "x86-osx-native,*"
Test_Username = 'yottatest'
Test_Access_Token = 'c53aadbd89caefdcadb0d43d18ef863e1d9cbcf4'

def ensureGithubConfig():
    # ensure we have authentication for the test github account
    if not settings.getProperty('github', 'authtoken'):
        settings.setProperty('github', 'authtoken', Test_Access_Token)


class TestGitHubAccess(unittest.TestCase):
    def setUp(self):
        ensureGithubConfig()
        
    def tearDown(self):
        pass

    def test_installDeps(self):
        Args = namedtuple('Args', ['component', 'target', 'act_globally', 'install_linked', 'save', 'save_target'])
        install.installComponent(Args(Test_Deps_Name, Test_Deps_Target, False, False, False, False))

    def test_branchAccess(self):
        Args = namedtuple('Args', ['component', 'target', 'act_globally', 'install_linked', 'save', 'save_target'])
        install.installComponent(Args(Test_Branch_Name, Test_Deps_Target, False, False, False, False))


if __name__ == '__main__':
    unittest.main()


