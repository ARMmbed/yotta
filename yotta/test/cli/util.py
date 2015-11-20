#!/usr/bin/env python
# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import tempfile
import os
import copy

# internal modules:
import yotta.lib.fsutils as fsutils
from yotta.lib.detect import systemDefaultTarget

# some simple example module definitions that can be re-used by multiple tests:
Test_Trivial_Lib = {
'module.json':'''{
  "name": "test-trivial-lib",
  "version": "1.0.0",
  "description": "Module to test trivial lib compilation",
  "license": "Apache-2.0",
  "dependencies": {
  }
}''',

'test-trivial-lib/lib.h': '''
int foo();
''',

'source/lib.c':'''
#include "test-trivial-lib/lib.h"
int foo(){ return 7; }
'''
}

Test_Trivial_Exe = {
'module.json':'''{
  "name": "test-trivial-exe",
  "version": "1.0.0",
  "description": "Module to test trivial exe compilation",
  "license": "Apache-2.0",
  "dependencies": {
  },
  "bin":"./source"
}''',

'source/lib.c':'''
int main(){ return 0; }
'''
}

Test_Testing_Trivial_Lib_Dep = {
'module.json':'''{
  "name": "test-simple-module",
  "version": "1.0.0",
  "description": "a simple test module",
  "author": "Someone Somewhere <someone.somewhere@yottabuild.org>",
  "license": "Apache-2.0",
  "dependencies": {
    "test-trivial-lib": "^1.0.0"
  }
}
''',

'test-simple-module/simple.h': '''
int simple();
''',

'source/lib.c':'''
#include "test-simple-module/simple.h"
int simple(){ return 123; }
'''
}

Test_Testing_Trivial_Lib_Dep_Preinstalled = copy.copy(Test_Testing_Trivial_Lib_Dep)
for k, v in Test_Trivial_Lib.items():
    Test_Testing_Trivial_Lib_Dep_Preinstalled['yotta_modules/test-trivial-lib/' + k] = v


def getNativeTargetDescription():
    # actually returns a trivial target which inherits from the native target
    native_target = nativeTarget()
    if ',' in native_target:
        native_target = native_target[:native_target.find(',')]
    return {
    'target.json':'''{
      "name": "test-native-target",
      "version": "1.0.0",
      "license": "Apache-2.0",
      "inherits": {
        "%s": "*"
      }
    }
    ''' % native_target
    }


def writeTestFiles(files, add_space_in_path=False):
    ''' write a dictionary of filename:contents into a new temporary directory
    '''
    test_dir = tempfile.mkdtemp()
    if add_space_in_path:
        test_dir = test_dir + ' spaces in path'

    for path, contents in files.items():
        path_dir, file_name =  os.path.split(path)
        path_dir = os.path.join(test_dir, path_dir)
        fsutils.mkDirP(path_dir)
        with open(os.path.join(path_dir, file_name), 'w') as f:
            f.write(contents)
    return test_dir

def isWindows():
    # can't run tests that hit github without an authn token
    return os.name == 'nt'

def canBuildNatively():
    return not isWindows()

def nativeTarget():
    assert(canBuildNatively())
    return systemDefaultTarget()

#expose rmRf for convenience
rmRf = fsutils.rmRf
