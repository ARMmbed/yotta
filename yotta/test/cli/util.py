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
from yotta.lib import fsutils
from yotta.lib.detect import systemDefaultTarget
from yotta.test.cli import cli

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

Test_Complex_Lib = {
'module.json':'''{
  "name": "test-testdep-a",
  "version": "0.0.2",
  "description": "Module to test more complex scenarios",
  "license": "Apache-2.0",
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
#include <stdio.h>
int main(){ printf("[trivial-exe-running]\\n"); return 0; }
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


Test_Custom_CMake_Exe = {
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
''',
'source/CMakeLists.txt':'''
add_executable(test-trivial-exe "lib.c")
'''
}

Test_Extra_CMake_Exe = {
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
#if TEST_MUST_BE_DEFINED != 1
#error "additional CMake not included correctly"
#endif
int main(){ return 0; }
''',
'source/addNeededDefinition.cmake':'''
target_compile_definitions(test-trivial-exe PRIVATE "-DTEST_MUST_BE_DEFINED=1")
'''
}

Test_Custom_CMake_Lib = {
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
''',
'source/CMakeLists.txt':'''
add_library(test-trivial-lib "lib.c")
'''
}

Test_Extra_CMake_Lib = {
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
#if TEST_MUST_BE_DEFINED != 1
#error "additional CMake not included correctly"
#endif
int foo(){ return 7; }
''',
'source/addNeededDefinition.cmake':'''
target_compile_definitions(test-trivial-lib PRIVATE "-DTEST_MUST_BE_DEFINED=1")
'''
}

Test_Test_Custom_CMake = {
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
''',
'test/main.c':'''
#include "test-trivial-lib/lib.h"
int main(){
    if(foo() == 7){
        return 0;
    }else{
        return -1;
    }
}
''',
'test/CMakeLists.txt':'''
add_executable(test-trivial-lib-maintest main.c)
target_link_libraries(test-trivial-lib-maintest test-trivial-lib)
add_test(test-trivial-lib-maintest test-trivial-lib-maintest)
add_dependencies(all_tests test-trivial-lib-maintest)
'''
}

Test_Test_Extra_CMake = {
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
''',
'test/main.c':'''
#include "test-trivial-lib/lib.h"
#if TEST_MUST_BE_DEFINED != 1
#error "additional CMake not included correctly"
#endif
int main(){
    if(foo() == 7){
        return 0;
    }else{
        return -1;
    }
}
''',
'test/addNeededDefinition.cmake':'''
target_compile_definitions(test-trivial-lib-test-main PRIVATE "-DTEST_MUST_BE_DEFINED=1")
'''
}



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


def writeTestFiles(files, add_space_in_path=False, test_dir=None):
    ''' write a dictionary of filename:contents into a new temporary directory
    '''
    if test_dir is None:
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

def runCheckCommand(args, test_dir):
    stdout, stderr, statuscode = cli.run(args, cwd=test_dir)
    if statuscode != 0:
        print('command failed with status %s' % statuscode)
        print(stdout)
        print(stderr)
    assert(statuscode == 0)
    return '%s %s' % (stdout, stderr)

def setupGitUser():
    # override the git user for subprocesses:
    os.environ['GIT_COMMITTER_NAME'] = 'Yotta Test'
    os.environ['GIT_COMMITTER_EMAIL'] = 'test@yottabuild.org'
    os.environ['GIT_AUTHOR_NAME'] = 'Yotta Test'
    os.environ['GIT_AUTHOR_EMAIL'] = 'test@yottabuild.org'

#expose rmRf for convenience
rmRf = fsutils.rmRf
