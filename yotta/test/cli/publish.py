#!/usr/bin/env python
# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import unittest

# internal modules:
from . import util
from . import cli

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

class TestCLIPublish(unittest.TestCase):
    def test_warnOfficialKeywords(self):
        path = util.writeTestFiles(Test_Publish, True)

        stdout, stderr, statuscode = cli.run(['-t', 'x86-linux-native', 'publish', '--noninteractive'], cwd=path)
        self.assertNotEqual(statuscode, 0)
        self.assertIn('Is this really an officially supported mbed module', stdout + stderr)

        util.rmRf(path)

