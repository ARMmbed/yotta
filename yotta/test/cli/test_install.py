#!/usr/bin/env python
# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# standard library modules, , ,
import unittest
import os
import tempfile
import re

# internal modules:
from yotta.lib.fsutils import rmRf
from yotta.test.cli import cli
from yotta.test.cli import util
from yotta.lib import settings


Test_Name = 'testing-dummy'
Test_Github_Name = "yottatest/github-access-testing"
Test_Target = "x86-osx-native,*"

Test_Module_JSON = '''{
  "name": "testmod",
  "version": "0.0.0",
  "description": "a test module",
  "keywords": [
  ],
  "author": "Someone Somewhere <someone.somewhere@yottabuild.org>",
  "repository": {
    "url": "git@github.com:mbedmicro/testmod.git",
    "type": "git"
  },
  "homepage": "https://github.com/mbedmicro/testmod",
  "licenses": [
    {
      "url": "https://spdx.org/licenses/Apache-2.0",
      "type": "Apache-2.0"
    }
  ],
  "dependencies": {
    "testing-dummy": "*"
  },
  "targetDependencies": {
    "x86-osx-native": {
        "other-testing-dummy": "git@github.com:yottatest/other-testing-dummy.git#0.0.5"
    }
  },
  "testDependencies": {
    "test-testing-dummy": "~0.0.2"
  },
  "testTargetDependencies": {
    "x86-osx-native": {
      "test-target-dep": "~0.0.1"
    }
  }
}
'''

Test_Complex_Module_JSON = '''{
  "name": "test-testdep-a",
  "version": "0.0.2",
  "description": "Module to test test-dependencies",
  "licenses": [
    {
      "url": "https://spdx.org/licenses/Apache-2.0",
      "type": "Apache-2.0"
    }
  ],
  "dependencies": {
    "test-testdep-b": "0.0.8",
    "test-testdep-c": "*",
    "test-testdep-d": "*"
  },
  "testDependencies": {
    "test-testdep-e": "*"
  }
}
'''

def hasGithubConfig():
    # can't run tests that hit github without an authn token
    if not settings.getProperty('github', 'authtoken'):
        return False
    return True

class TestCLIInstall(unittest.TestCase):
    @unittest.skipIf(not hasGithubConfig(), "a github authtoken must be specified for this test (run yotta login, or set YOTTA_GITHUB_AUTHTOKEN)")
    def test_installRegistryRef(self):
        test_dir = tempfile.mkdtemp()
        stdout = self.runCheckCommand(['--target', Test_Target, 'install', Test_Name], test_dir)
        rmRf(test_dir)

    @unittest.skipIf(not hasGithubConfig(), "a github authtoken must be specified for this test (run yotta login, or set YOTTA_GITHUB_AUTHTOKEN)")
    def test_installGithubRef(self):
        test_dir = tempfile.mkdtemp()
        stdout = self.runCheckCommand(['--target', Test_Target, 'install', Test_Github_Name], test_dir)
        rmRf(test_dir)

    @unittest.skipIf(not hasGithubConfig(), "a github authtoken must be specified for this test (run yotta login, or set YOTTA_GITHUB_AUTHTOKEN)")
    def test_installDeps(self):
        test_dir = tempfile.mkdtemp()
        with open(os.path.join(test_dir, 'module.json'), 'w') as f:
            f.write(Test_Module_JSON)
        stdout = self.runCheckCommand(['--target', Test_Target, 'install'], test_dir)

        # also sanity-check listing:
        stdout = self.runCheckCommand(['--target', Test_Target, 'ls'], test_dir)
        self.assertIn('testmod', stdout)
        self.assertIn('other-testing-dummy', stdout)
        self.assertIn('test-testing-dummy', stdout)
        self.assertIn('test-target-dep', stdout)

        stdout = self.runCheckCommand(['--target', Test_Target, 'ls', '-a'], test_dir)
        self.assertIn('testmod', stdout)
        self.assertIn('other-testing-dummy', stdout)
        self.assertIn('test-testing-dummy', stdout)
        self.assertIn('test-target-dep', stdout)

        # and test install <modulename>
        stdout = self.runCheckCommand(['--target', Test_Target, 'install', 'hg-access-testing'], test_dir)
        stdout = self.runCheckCommand(['--target', Test_Target, 'ls'], test_dir)
        self.assertIn('hg-access-testing', stdout)
        rmRf(test_dir)

    @unittest.skipIf(not hasGithubConfig(), "a github authtoken must be specified for this test (run yotta login, or set YOTTA_GITHUB_AUTHTOKEN)")
    def test_installAllTestDeps(self):
        test_dir = tempfile.mkdtemp()
        with open(os.path.join(test_dir, 'module.json'), 'w') as f:
            f.write(Test_Module_JSON)
        stdout = self.runCheckCommand(['--target', Test_Target, 'install', '--test-dependencies', 'all'], test_dir)

        # also sanity-check listing:
        stdout = self.runCheckCommand(['--target', Test_Target, 'ls', '-a'], test_dir)
        self.assertIn('testmod', stdout)
        self.assertIn('other-testing-dummy', stdout)
        self.assertIn('test-testing-dummy', stdout)
        self.assertIn('test-target-dep', stdout)
        self.assertNotIn('missing', stdout)
        rmRf(test_dir)

    @unittest.skipIf(not hasGithubConfig(), "a github authtoken must be specified for this test (run yotta login, or set YOTTA_GITHUB_AUTHTOKEN)")
    def test_installNoTestDeps(self):
        test_dir = tempfile.mkdtemp()
        with open(os.path.join(test_dir, 'module.json'), 'w') as f:
            f.write(Test_Module_JSON)
        stdout = self.runCheckCommand(['--target', Test_Target, 'install', '--test-dependencies', 'none'], test_dir)

        # also sanity-check listing:
        stdout = self.runCheckCommand(['--target', Test_Target, 'ls'], test_dir)
        self.assertIn('testmod', stdout)
        self.assertIn('other-testing-dummy', stdout)
        self.assertTrue(re.search('test-testing-dummy.*missing', stdout))
        self.assertTrue(re.search('test-target-dep.*missing', stdout))

        stdout = self.runCheckCommand(['--target', Test_Target, 'ls', '-a'], test_dir)
        self.assertIn('testmod', stdout)
        self.assertIn('other-testing-dummy', stdout)
        self.assertTrue(re.search('test-testing-dummy.*missing', stdout))
        self.assertTrue(re.search('test-target-dep.*missing', stdout))

        rmRf(test_dir)

    @unittest.skipIf(not hasGithubConfig(), "a github authtoken must be specified for this test (run yotta login, or set YOTTA_GITHUB_AUTHTOKEN)")
    def test_installComplexDeps(self):
        test_dir = tempfile.mkdtemp()
        with open(os.path.join(test_dir, 'module.json'), 'w') as f:
            f.write(Test_Complex_Module_JSON)
        stdout = self.runCheckCommand(['--target', Test_Target, 'install'], test_dir)

        # also sanity-check listing:
        stdout = self.runCheckCommand(['--target', Test_Target, 'ls'], test_dir)

        self.assertIn('test-testdep-b', stdout)
        self.assertIn('test-testdep-c', stdout)
        self.assertIn('test-testdep-d', stdout)
        self.assertIn('test-testdep-e', stdout)
        self.assertIn('test-testdep-f', stdout)
        self.assertIn('test-testdep-h', stdout)
        self.assertNotIn('test-testdep-g', stdout)
        self.assertNotIn('test-testdep-i', stdout)
        self.assertNotIn('test-testdep-j', stdout)
        self.assertNotIn('test-testdep-k', stdout)
        self.assertNotIn('missing', stdout)

        stdout = self.runCheckCommand(['--target', Test_Target, 'ls', '-a'], test_dir)

        self.assertIn('test-testdep-b', stdout)
        self.assertIn('test-testdep-c', stdout)
        self.assertIn('test-testdep-d', stdout)
        self.assertIn('test-testdep-e', stdout)
        self.assertIn('test-testdep-f', stdout)
        self.assertIn('test-testdep-h', stdout)
        self.assertTrue(re.search('test-testdep-nodeps.*missing', stdout))
        self.assertTrue(re.search('test-testdep-i.*missing', stdout))
        self.assertTrue(re.search('test-testdep-g.*missing', stdout))
        self.assertNotIn('test-testdep-j', stdout)
        self.assertNotIn('test-testdep-k', stdout)

        # test update
        stdout = self.runCheckCommand(['--target', Test_Target, 'up'], test_dir)

        rmRf(test_dir)

    @unittest.skipIf(not hasGithubConfig(), "a github authtoken must be specified for this test (run yotta login, or set YOTTA_GITHUB_AUTHTOKEN)")
    def test_installAllComplexTestDeps(self):
        test_dir = tempfile.mkdtemp()
        with open(os.path.join(test_dir, 'module.json'), 'w') as f:
            f.write(Test_Complex_Module_JSON)
        stdout = self.runCheckCommand(['--target', Test_Target, 'install', '--test-dependencies', 'all'], test_dir)

        # also sanity-check listing:
        stdout = self.runCheckCommand(['--target', Test_Target, 'ls', '-a'], test_dir)

        self.assertIn('test-testdep-b', stdout)
        self.assertIn('test-testdep-c', stdout)
        self.assertIn('test-testdep-d', stdout)
        self.assertIn('test-testdep-e', stdout)
        self.assertIn('test-testdep-f', stdout)
        self.assertIn('test-testdep-g', stdout)
        self.assertIn('test-testdep-h', stdout)
        self.assertIn('test-testdep-i', stdout)
        self.assertNotIn('test-testdep-j', stdout)
        self.assertNotIn('test-testdep-k', stdout)
        self.assertNotIn('missing', stdout)

        rmRf(test_dir)

    @unittest.skipIf(not hasGithubConfig(), "a github authtoken must be specified for this test (run yotta login, or set YOTTA_GITHUB_AUTHTOKEN)")
    def test_installNoComplexTestDeps(self):
        test_dir = tempfile.mkdtemp()
        with open(os.path.join(test_dir, 'module.json'), 'w') as f:
            f.write(Test_Complex_Module_JSON)
        stdout = self.runCheckCommand(['--target', Test_Target, 'install', '--test-dependencies', 'none'], test_dir)

        # also sanity-check listing:
        stdout = self.runCheckCommand(['--target', Test_Target, 'ls'], test_dir)

        self.assertIn('test-testdep-b', stdout)
        self.assertIn('test-testdep-c', stdout)
        self.assertIn('test-testdep-d', stdout)
        # e should be installed because it is both a test dep and non-test dep:
        # maybe it shouldn't show up in the listing without -a though?
        self.assertIn('test-testdep-e', stdout)
        self.assertIn('test-testdep-f', stdout)
        self.assertIn('test-testdep-h', stdout)
        self.assertNotIn('test-testdep-g', stdout)
        self.assertNotIn('test-testdep-i', stdout)
        self.assertNotIn('test-testdep-j', stdout)
        self.assertNotIn('test-testdep-k', stdout)
        self.assertNotIn('missing', stdout)

        stdout = self.runCheckCommand(['--target', Test_Target, 'ls', '-a'], test_dir)

        self.assertIn('test-testdep-b', stdout)
        self.assertIn('test-testdep-c', stdout)
        self.assertIn('test-testdep-d', stdout)
        self.assertIn('test-testdep-e', stdout)
        self.assertIn('test-testdep-f', stdout)
        self.assertIn('test-testdep-h', stdout)
        self.assertTrue(re.search('test-testdep-nodeps.*missing', stdout))
        self.assertTrue(re.search('test-testdep-i.*missing', stdout))
        self.assertTrue(re.search('test-testdep-g.*missing', stdout))
        self.assertNotIn('test-testdep-j', stdout)
        self.assertNotIn('test-testdep-k', stdout)

        rmRf(test_dir)

    @unittest.skipIf(not hasGithubConfig(), "a github authtoken must be specified for this test (run yotta login, or set YOTTA_GITHUB_AUTHTOKEN)")
    def test_remove(self):
        test_dir = tempfile.mkdtemp()
        with open(os.path.join(test_dir, 'module.json'), 'w') as f:
            f.write(Test_Module_JSON)
        stdout = self.runCheckCommand(['--target', Test_Target, 'install'], test_dir)
        self.assertTrue(os.path.exists(os.path.join(test_dir, 'yotta_modules', 'testing-dummy')))

        self.runCheckCommand(['remove', 'testing-dummy'], test_dir)
        self.assertFalse(os.path.exists(os.path.join(test_dir, 'yotta_modules', 'testing-dummy')))

        stdout = self.runCheckCommand(['--target', Test_Target, 'ls', '-a'], test_dir)
        self.assertIn('testing-dummy', stdout)

        rmRf(test_dir)

    @unittest.skipIf(not hasGithubConfig(), "a github authtoken must be specified for this test (run yotta login, or set YOTTA_GITHUB_AUTHTOKEN)")
    def test_uninstall(self):
        test_dir = tempfile.mkdtemp()
        with open(os.path.join(test_dir, 'module.json'), 'w') as f:
            f.write(Test_Module_JSON)
        stdout = self.runCheckCommand(['--target', Test_Target, 'install'], test_dir)
        self.assertTrue(os.path.exists(os.path.join(test_dir, 'yotta_modules', 'testing-dummy')))

        self.runCheckCommand(['uninstall', 'testing-dummy'], test_dir)
        self.assertFalse(os.path.exists(os.path.join(test_dir, 'yotta_modules', 'testing-dummy')))

        stdout = self.runCheckCommand(['--target', Test_Target, 'ls', '-a'], test_dir)
        self.assertNotIn(' testing-dummy', stdout)

        rmRf(test_dir)

    @unittest.skipIf(not hasGithubConfig(), "a github authtoken must be specified for this test (run yotta login, or set YOTTA_GITHUB_AUTHTOKEN)")
    def test_uninstallNonExistent(self):
        test_dir = tempfile.mkdtemp()
        with open(os.path.join(test_dir, 'module.json'), 'w') as f:
            f.write(Test_Module_JSON)
        stdout = self.runCheckCommand(['--target', Test_Target, 'install'], test_dir)
        self.assertTrue(os.path.exists(os.path.join(test_dir, 'yotta_modules', 'testing-dummy')))

        stdout, stderr, statuscode = cli.run(['uninstall', 'nonexistent'], cwd=test_dir)
        self.assertNotEqual(statuscode, 0)

        rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "cannot build natively")
    def test_postInstall_topLevel(self):
        test_dir = util.writeTestFiles({})
        self.runCheckCommand(['--target', util.nativeTarget(), 'install', 'test-post-install'], test_dir)
        output = self.runCheckCommand(['--target', util.nativeTarget(), 'build'], os.path.join(test_dir, 'test-post-install'))
        self.assertIn('post-install generated file compiled', output)
        self.assertIn('post-install generated header file included', output)
        self.assertIn('generated .cmake file included', output)

    @unittest.skipIf(not util.canBuildNatively(), "cannot build natively")
    def test_postInstall_dependency(self):
        test_dir = util.writeTestFiles({
'module.json':'''{
  "name": "test-postinstall",
  "version": "1.0.0",
  "license": "Apache-2.0",
  "dependencies": {
    "test-post-install": "*"
  },
  "bin":"./source"
}''',

'source/lib.c':'''
#include <stdio.h>
#include "test-post-install/generated.h"
int main(){ printf("generated return val=%d\\n", postInstallGenerated()); return 0; }
'''})
        output = self.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)
        self.assertIn('post-install generated file compiled', output)
        self.assertIn('post-install generated header file included', output)
        self.assertIn('generated .cmake file included', output)

    def runCheckCommand(self, args, test_dir):
        stdout, stderr, statuscode = cli.run(args, cwd=test_dir)
        #print stdout
        self.assertEqual(statuscode, 0)
        return stdout + stderr


if __name__ == '__main__':
    unittest.main()



