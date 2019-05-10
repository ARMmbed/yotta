#!/usr/bin/env python
# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# standard library modules, , ,
import unittest
import os
import tempfile

# internal modules:
from yotta.lib.fsutils import rmRf
from yotta.test.cli import cli
from yotta.test.cli import util

Test_Target = "x86-osx-native,*"

Private_Module_JSON = '''{
  "name": "testmod",
  "version": "0.0.0",
  "description": "a test module",
  "private": true,
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
  }
}
'''

Public_Module_JSON = '''{
  "name": "testmod",
  "version": "0.0.0",
  "license": "Apache-2.0"
}'''


Test_Publish = {
'module.json':'''{
  "name": "test-publish",
  "version": "0.0.0",
  "description": "Test yotta publish",
  "author": "James Crosby <james.crosby@arm.com>",
  "license": "Apache-2.0",
  "keywords": ["mbed-official"],
  "dependencies":{
  }
}''',
'readme.md':'''##This is a test module used in yotta's test suite.''',
'source/foo.c':'''#include "stdio.h"
int foo(){
    printf("foo!\\n");
    return 7;
}'''
}

Test_prePublish_Prevents_Publish = {
  'module.json':'''{
  "name": "test-publish-prevented",
  "version": "0.0.0",
  "description": "Test yotta publish",
  "author": "James Crosby <james.crosby@arm.com>",
  "license": "Apache-2.0",
  "scripts": {
    "prePublish": "false"
  }
}''',
'readme.md':'''##This is a test module used in yotta's test suite.''',
}


class TestCLIPublish(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        rmRf(cls.test_dir)

    def test_publishPrivate(self):
        with open(os.path.join(self.test_dir, 'module.json'), 'w') as f:
            f.write(Private_Module_JSON)
        stdout, stderr, status = cli.run(['--target', Test_Target, 'publish'], cwd=self.test_dir)
        self.assertNotEqual(status, 0)
        self.assertTrue('is private and cannot be published' in ('%s %s' % (stdout, stderr)))

    def test_publishNotAuthed(self):
        # ensure we're not logged in by setting a different settings directory:
        saved_settings_dir = None
        if 'YOTTA_USER_SETTINGS_DIR' in os.environ:
            saved_settings_dir = os.environ['YOTTA_USER_SETTINGS_DIR']
        os.environ['YOTTA_USER_SETTINGS_DIR'] = 'tmp_yotta_settings'
        try:
            with open(os.path.join(self.test_dir, 'module.json'), 'w') as f:
                f.write(Public_Module_JSON)
            stdout, stderr, status = cli.run(['-n', '--target', Test_Target, 'publish'], cwd=self.test_dir)
            if status != 0:
                out = stdout+stderr
                self.assertTrue(out.find('login required') != -1 or out.find('not module owner') != -1)
        finally:
            if saved_settings_dir is not None:
                os.environ['YOTTA_USER_SETTINGS_DIR'] = saved_settings_dir
            else:
                del os.environ['YOTTA_USER_SETTINGS_DIR']

    def test_prePublishPreventsPublish(self):
        path = util.writeTestFiles(Test_prePublish_Prevents_Publish, True)

        stdout, stderr, statuscode = cli.run(['-t', 'x86-linux-native', '--noninteractive', 'publish'], cwd=path)
        self.assertNotEqual(statuscode, 0)
        self.assertIn('prePublish script error code 1 prevents publishing', stdout + stderr)

        util.rmRf(path)

    def test_warnOfficialKeywords(self):
        path = util.writeTestFiles(Test_Publish, True)

        stdout, stderr, statuscode = cli.run(['-t', 'x86-linux-native', '--noninteractive', 'publish'], cwd=path)
        self.assertNotEqual(statuscode, 0)
        self.assertIn('Is this really an officially supported mbed module', stdout + stderr)

        util.rmRf(path)

if __name__ == '__main__':
    unittest.main()




