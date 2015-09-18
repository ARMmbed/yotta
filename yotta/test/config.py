# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import unittest
import copy
import os
import tempfile
import logging

# internal modules:
from yotta.lib.fsutils import mkDirP, rmRf
from yotta.lib import validate

logging.basicConfig(
    level=logging.ERROR
)

Test_Target_Config_Merge = {
# app itself
'module.json':'''{
  "name": "testapp",
  "version": "0.0.0",
  "license": "Apache-2.0",
  "dependencies": { },
  "bin":"./source"
}''',
'source/main.c':'int main(){ return 0; }\n',
# target foo
'yotta_targets/foo/target.json':'''{
  "name": "foo",
  "version": "0.0.0",
  "license": "Apache-2.0",
  "config": {
    "foo":{
       "a":123,
       "b":456,
       "c":789
    }
  }
}''',
# target bar
'yotta_targets/bar/target.json':'''{
  "name": "bar",
  "version": "0.0.0",
  "license": "Apache-2.0",
  "inherits":{ "foo":"*" },
  "config": {
    "foo":{
       "a":321
    },
    "bar":{
       "d":"def"
    }
  }
}'''
}

Test_Target_Config_Merge_App = copy.copy(Test_Target_Config_Merge)
Test_Target_Config_Merge_App['config.json'] = '''{
  "foo":{
    "c":112233
  },
  "bar":{
    "d":"ghi"
  },
  "new":123
}'''

Test_Module_Config_Ignored = copy.copy(Test_Target_Config_Merge_App)
Test_Module_Config_Ignored['module.json'] = '''{
  "name": "testmod",
  "version": "0.0.0",
  "license": "Apache-2.0",
  "dependencies": { }
}'''

class ConfigTest(unittest.TestCase):
    def writeTestFiles(self, files, add_space_in_path=False):
        test_dir = tempfile.mkdtemp()
        if add_space_in_path:
            test_dir = test_dir + ' spaces in path'

        for path, contents in files.items():
            path_dir, file_name =  os.path.split(path)
            path_dir = os.path.join(test_dir, path_dir)
            mkDirP(path_dir)
            with open(os.path.join(path_dir, file_name), 'w') as f:
                f.write(contents)
        return test_dir

    def setUp(self):
        self.restore_cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self.restore_cwd)

    def test_targetConfigMerge(self):
        test_dir = self.writeTestFiles(Test_Target_Config_Merge, True)

        os.chdir(test_dir)
        c = validate.currentDirectoryModule()
        target, errors = c.satisfyTarget('bar,')
        merged_config = target.getMergedConfig()

        self.assertIn("foo", merged_config)
        self.assertIn("bar", merged_config)
        self.assertIn("a", merged_config['foo'])
        self.assertIn("b", merged_config['foo'])
        self.assertIn("c", merged_config['foo'])
        self.assertEqual(merged_config['foo']['a'], 321)
        self.assertEqual(merged_config['foo']['b'], 456)
        self.assertEqual(merged_config['foo']['c'], 789)
        self.assertIn("bar", merged_config)
        self.assertIn("d", merged_config['bar'])
        self.assertEqual(merged_config['bar']['d'], "def")

        os.chdir(self.restore_cwd)
        rmRf(test_dir)

    def test_targetAppConfigMerge(self):
        test_dir = self.writeTestFiles(Test_Target_Config_Merge_App, True)

        os.chdir(test_dir)
        c = validate.currentDirectoryModule()
        target, errors = c.satisfyTarget('bar,')
        merged_config = target.getMergedConfig()

        self.assertIn("foo", merged_config)
        self.assertIn("bar", merged_config)
        self.assertIn("new", merged_config)
        self.assertIn("a", merged_config['foo'])
        self.assertIn("b", merged_config['foo'])
        self.assertIn("c", merged_config['foo'])
        self.assertEqual(merged_config['foo']['a'], 321)
        self.assertEqual(merged_config['foo']['b'], 456)
        self.assertEqual(merged_config['foo']['c'], 112233)
        self.assertIn("bar", merged_config)
        self.assertIn("d", merged_config['bar'])
        self.assertEqual(merged_config['bar']['d'], "ghi")
        self.assertIn("new", merged_config)
        self.assertEqual(merged_config['new'], 123)

        os.chdir(self.restore_cwd)
        rmRf(test_dir)

    def test_moduleConfigIgnored(self):
        test_dir = self.writeTestFiles(Test_Module_Config_Ignored, True)

        os.chdir(test_dir)
        c = validate.currentDirectoryModule()
        target, errors = c.satisfyTarget('bar,')
        merged_config = target.getMergedConfig()

        self.assertNotIn("new", merged_config)

        os.chdir(self.restore_cwd)
        rmRf(test_dir)

