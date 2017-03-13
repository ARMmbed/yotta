#!/usr/bin/env python
# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import unittest
import subprocess
import copy
import re
import datetime

# internal modules:
from yotta.test.cli import cli
from yotta.test.cli import util

Test_Complex = {
'module.json': '''{
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
    "test-testdep-b": "*",
    "test-testdep-c": "*",
    "test-testdep-d": "*"
  },
  "testDependencies": {
    "test-testdep-e": "*"
  }
}
''',

'source/a.c': '''
#include "a/a.h"
#include "b/b.h"
#include "c/c.h"
#include "d/d.h"

int a(){
    return 1 + b() + c() + d(); // 35
}
''',

'source/a.c': '''
#include "a/a.h"
#include "b/b.h"
#include "c/c.h"
#include "d/d.h"

int a(){
    return 1 + b() + c() + d(); // 35
}
''',

'a/a.h':'''
#ifndef __A_H__
#define __A_H__
int a();
#endif
''',

'test/check.c': '''
#include <stdio.h>

#include "a/a.h"
#include "b/b.h"
#include "c/c.h"
#include "d/d.h"
#include "e/e.h"


int main(){
    int result = a() + b() + c() + d() + e();
    printf("%d\\n", result);
    return !(result == 86);
}
'''
}

Test_Build_Info = copy.copy(util.Test_Trivial_Exe)
Test_Build_Info['source/lib.c'] = '''
#include "stdio.h"
#include YOTTA_BUILD_INFO_HEADER

#define STRINGIFY(s) STRINGIFY_INDIRECT(s)
#define STRINGIFY_INDIRECT(s) #s

int main(){
    printf("vcs ID: %s\\n", STRINGIFY(YOTTA_BUILD_VCS_ID));
    printf("vcs clean: %d\\n", YOTTA_BUILD_VCS_CLEAN);
    printf("build UUID: %s\\n", STRINGIFY(YOTTA_BUILD_UUID));
    printf(
        "build timestamp: %.4d-%.2d-%.2d-%.2d-%.2d-%.2d\\n",
        YOTTA_BUILD_YEAR,
        YOTTA_BUILD_MONTH,
        YOTTA_BUILD_DAY,
        YOTTA_BUILD_HOUR,
        YOTTA_BUILD_MINUTE,
        YOTTA_BUILD_SECOND
    );
    return 0;
}

'''

Test_Tests = {
'module.json':'''{
  "name": "test-tests",
  "version": "0.0.0",
  "description": "Test yotta's compilation of tests.",
  "keywords": [],
  "author": "James Crosby <james.crosby@arm.com>",
  "licenses": [
    {
      "url": "https://spdx.org/licenses/Apache-2.0",
      "type": "Apache-2.0"
    }
  ],
  "dependencies": {},
  "targetDependencies": {}
}''',
'source/foo.c':'''#include "stdio.h"
int foo(){
    printf("foo!\\n");
    return 7;
}''',
'test-tests/foo.h':'int foo();',
'test/a/bar.c':'#include "test-tests/foo.h"\nint main(){ foo(); return 0; }',
'test/b/a/bar.c':'#include "test-tests/foo.h"\nint bar(); int main(){ foo(); bar(); return 0; }',
'test/b/b/bar.c':'#include "stdio.h"\nint bar(){ printf("bar!\\n"); return 7; }',
'test/c/a/a/bar.c':'#include "test-tests/foo.h"\nint bar(); int main(){ foo(); bar(); return 0; }',
'test/c/b/a/bar.c':'#include "stdio.h"\nint bar(){ printf("bar!\\n"); return 7; }',
'test/d/a/a/bar.c':'#include "test-tests/foo.h"\nint bar(); int main(){ foo(); bar(); return 0; }',
'test/d/a/b/bar.c':'#include "stdio.h"\nint bar(){ printf("bar!\\n"); return 7; }',
'test/e/a/a/a/bar.c':'#include "test-tests/foo.h"\nint bar(); int main(){ foo(); bar(); return 0; }',
'test/e/b/a/a/bar.c':'#include "stdio.h"\nint bar(){ printf("bar!\\n"); return 7; }',
'test/f/a/a/a/bar.c':'#include "test-tests/foo.h"\nint bar(); int main(){ foo(); bar(); return 0; }',
'test/f/a/b/a/bar.c':'#include "stdio.h"\nint bar(){ printf("bar!\\n"); return 7; }',
'test/g/a/a/a/bar.c':'#include "test-tests/foo.h"\nint bar(); int main(){ foo(); bar(); return 0; }',
'test/g/a/a/b/bar.c':'#include "stdio.h"\nint bar(){ printf("bar!\\n"); return 7; }'
}

Test_Ignore_Custom_Cmake = {
'module.json':'''{
  "name": "cmake-ignore-test",
  "version": "0.0.0",
  "keywords": [],
  "author": "",
  "license": "Apache-2.0",
  "dependencies": {}
}''',
'.yotta_ignore':'''
./source/CMakeLists.txt
CMakeLists.txt
./source/empty.c
./source/ignoreme.cmake
./test/CMakeLists.txt
./test/ignoreme.cmake
''',
'source/CMakeLists.txt':'''
message("source CMakeLists.txt should be ignored!")
add_library(cmake-ignore-test "empty.c")
''',
'CMakeLists.txt': '''
message("root cmakelist should be ignored!")
add_subdirectory(source)
add_subdirectory(test)
''',
'source/empty.c': '''
int foo(){ }
''',
'source/ignoreme.cmake': '''
message(".cmake file should be ignored!")
''',
'test/CMakeLists.txt': '''
message("test CMakeLists.txt file should be ignored!")
''',
'test/ignoreme.cmake': '''
message("test .cmake file should be ignored!")
''',
'test/empty.c': '''
int main(){ return 0; }
'''
}

def _generateTestCustomLibBinDir(subdir='mysubdir', bin=False):
    if bin:
        libbin = 'bin'
        fnname = 'main'
    else:
        libbin = 'lib'
        fnname = 'foo'
    return {
        'module.json':'''{
          "name": "test-custom-dir-%s",
          "version": "1.0.0",
          "description": "Module to test trivial %s compilation",
          "license": "Apache-2.0",
          "%s": "%s"
        }''' % (libbin, libbin, libbin, subdir),
        'test-custom-dir-%s/%s.h' % (libbin, libbin): '''
        int %s();
        ''' % (fnname),
        '%s/%s.c' % (subdir, libbin):'''
        #warning "this message should be printed"
        #include "test-custom-dir-%s/%s.h"
        int %s(){ return 7; }
        ''' % (libbin, libbin, fnname)
    }

Test_Custom_Lib_Dir = _generateTestCustomLibBinDir('mylibdir', 'lib')
Test_Custom_Lib_Sub_Dir = _generateTestCustomLibBinDir('mylibdir/subdir', 'lib')
Test_Custom_Lib_Sub_Source_Dir = _generateTestCustomLibBinDir('source/mysourcesubdir', 'lib')
Test_Custom_Bin_Dir = _generateTestCustomLibBinDir('mybindir', 'bin')
Test_Custom_Bin_Sub_Dir = _generateTestCustomLibBinDir('mybindir/subdir', 'bin')
Test_Custom_Bin_Sub_Source_Dir = _generateTestCustomLibBinDir('source/somewhere/mybindir', 'bin')

# expect an error message
Test_Lib_And_Bin = {
'module.json':'''{
  "name": "test-custom-dir-lib",
  "version": "1.0.0",
  "description": "Module to test trivial lib compilation",
  "license": "Apache-2.0",
  "lib": "mylibdir",
  "bin": "mylibdir"
}''',
'mylibdir/lib.c':'''
int foo(){ return 7; }
'''
}

# expect an error message
Test_Lib_Nonexistent = {
'module.json':'''{
  "name": "test-custom-dir-lib",
  "version": "1.0.0",
  "description": "Module to test trivial lib compilation",
  "license": "Apache-2.0",
  "lib": "doesntexist"
}'''
}

# expect an error message
Test_Bin_Nonexistent = {
'module.json':'''{
  "name": "test-custom-dir-lib",
  "version": "1.0.0",
  "description": "Module to test trivial lib compilation",
  "license": "Apache-2.0",
  "bin": "doesntexist"
}'''
}

# expect a warning message for "Source" and "src" implicit source directory
# names: only "source" is supported as an implicit source directory name:
Test_Misspelt_Source_Dir_1 = {
'module.json':'''{
  "name": "test-mod",
  "version": "1.0.0",
  "description": "Module to test misspelt source dir names",
  "license": "Apache-2.0"
}''',
'Source/lib.c':"int foo(){return 0;}\n"
}

Test_Misspelt_Source_Dir_2 = {
'module.json':'''{
  "name": "test-mod",
  "version": "1.0.0",
  "description": "Module to test misspelt source dir names",
  "license": "Apache-2.0"
}''',
'src/lib.c':"int foo(){return 0;}\n"
}

# ...but if the misspelt directory is ignored, then no warning should be issued
Test_Ignored_Misspelt_Source_Dir = {
'module.json':'''{
  "name": "test-mod",
  "version": "1.0.0",
  "description": "Module to test misspelt source dir names",
  "license": "Apache-2.0"
}''',
'src/lib.c':"int foo(){return 0;}\n",
'.yotta_ignore':"./src"
}

Test_Scripts_PreBuild = {
'module.json':'''{
  "name": "test-tests",
  "version": "0.0.0",
  "description": "Test yotta's compilation of tests.",
  "keywords": [],
  "license": "Apache-2.0",
  "scripts": {
    "preBuild": "./scripts/nop.py"
  }
}''',
'source/foo.c':'''#include "stdio.h"
int foo(){
    printf("foo!\\n");
    return 7;
}''',
'./scripts/nop.py':'''
print('running prebuild')
'''
}

Test_Scripts_PostBuild = {
'module.json':'''{
  "name": "test-tests",
  "version": "0.0.0",
  "description": "Test yotta's compilation of tests.",
  "keywords": [],
  "license": "Apache-2.0",
  "scripts": {
    "postBuild": "./scripts/nop.py"
  }
}''',
'source/foo.c':'''#include "stdio.h"
int foo(){
    printf("foo!\\n");
    return 7;
}''',
'./scripts/nop.py':'''
print('running postbuild')
'''
}

Test_Scripts_PreGenerate = {
'module.json':'''{
  "name": "test-tests",
  "version": "0.0.0",
  "description": "Test yotta's compilation of tests.",
  "keywords": [],
  "license": "Apache-2.0",
  "scripts": {
    "preGenerate": "./scripts/nop.py"
  }
}''',
'source/foo.c':'''#include "stdio.h"
int foo(){
    printf("foo!\\n");
    return 7;
}''',
'./scripts/nop.py':'''
print('running pregenerate')
'''
}

Test_Defines_Application = {
'module.json':'''{
  "name": "test-defines-app",
  "version": "0.0.0",
  "description": "Test defines.json in application",
  "keywords": [],
  "license": "Apache-2.0",
  "bin": "source"
}''',
'defines.json':'''{
  "INT_MACRO": 1234,
  "TEXT_MACRO": "\\"yotta\\""
}''',
'source/foo.c':'''#include "stdio.h"
int main(){
    printf("%d %s\\n", INT_MACRO, TEXT_MACRO);
    return 0;
}'''
}

Test_Defines_Library = {
'module.json':'''{
  "name": "test-defines-lib",
  "version": "0.0.0",
  "description": "Test defines.json in library",
  "keywords": [],
  "license": "Apache-2.0"
}''',
'defines.json':'''{
  "INT_MACRO": 1234,
  "TEXT_MACRO": "\\"yotta\\""
}''',
'source/foo.c':'''#include "stdio.h"
int foo(){
    return 0;
}'''
}

class TestCLIBuild(unittest.TestCase):
    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_buildTrivialLib(self):
        test_dir = util.writeTestFiles(util.Test_Trivial_Lib)

        stdout = self.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)

        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_buildTrivialExe(self):
        test_dir = util.writeTestFiles(util.Test_Trivial_Exe)

        stdout = self.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)

        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_buildComplex(self):
        test_dir = util.writeTestFiles(Test_Complex)

        stdout = self.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)

        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_buildComplexSpaceInPath(self):
        test_dir = util.writeTestFiles(Test_Complex, True)

        stdout = self.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)

        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_buildTests(self):
        test_dir = util.writeTestFiles(Test_Tests, True)
        stdout = self.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)
        stdout = self.runCheckCommand(['--target', util.nativeTarget(), 'test'], test_dir)
        self.assertIn('test-a', stdout)
        self.assertIn('test-c', stdout)
        self.assertIn('test-d', stdout)
        self.assertIn('test-e', stdout)
        self.assertIn('test-f', stdout)
        self.assertIn('test-g', stdout)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_buildInfo(self):
        test_dir = util.writeTestFiles(Test_Build_Info, True)
        # commit all the test files to git so that the VCS build info gets
        # defined:
        # (set up the git user env vars so we can run git commit without barfing)
        util.setupGitUser()
        subprocess.check_call(['git', 'init', '-q'], cwd=test_dir)
        subprocess.check_call(['git', 'add', '.'], cwd=test_dir)
        subprocess.check_call(['git', 'commit', '-m', 'test build info automated commit', '-q'], cwd=test_dir)

        self.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)

        build_time = datetime.datetime.utcnow()
        output = subprocess.check_output(['./build/' + util.nativeTarget().split(',')[0] + '/source/test-trivial-exe'], cwd=test_dir).decode()
        self.assertIn('vcs clean: 1', output)

        # check build timestamp
        self.assertIn('build timestamp: ', output)
        build_timestamp_s = re.search('build timestamp: (.*)\n', output)
        self.assertTrue(build_timestamp_s)
        build_timestamp_s = build_timestamp_s.group(1)
        build_time_parsed = datetime.datetime.strptime(build_timestamp_s, '%Y-%m-%d-%H-%M-%S')
        build_time_skew = build_time_parsed - build_time
        self.assertTrue(abs(build_time_skew.total_seconds()) < 3)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_extraCMakeBuild(self):
        test_dir = util.writeTestFiles(util.Test_Extra_CMake_Lib, True)
        stdout = self.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_customCMakeBuild(self):
        test_dir = util.writeTestFiles(util.Test_Custom_CMake_Lib, True)
        stdout = self.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_extraCMakeBuildExe(self):
        test_dir = util.writeTestFiles(util.Test_Extra_CMake_Exe, True)
        stdout = self.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_customCMakeBuildExe(self):
        test_dir = util.writeTestFiles(util.Test_Custom_CMake_Exe, True)
        stdout = self.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_ignoreCustomCMake(self):
        test_dir = util.writeTestFiles(Test_Ignore_Custom_Cmake, True)
        stdout = self.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)
        self.assertNotIn('should be ignored', stdout)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_customLibDir(self):
        test_dir = util.writeTestFiles(Test_Custom_Lib_Dir, True)
        stdout = self.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)
        self.assertIn('this message should be printed', stdout)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_customLibSubDir(self):
        test_dir = util.writeTestFiles(Test_Custom_Lib_Sub_Dir, True)
        stdout = self.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)
        self.assertIn('this message should be printed', stdout)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_customLibSubSourceDir(self):
        test_dir = util.writeTestFiles(Test_Custom_Lib_Sub_Source_Dir, True)
        stdout = self.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)
        self.assertIn('this message should be printed', stdout)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_customBinDir(self):
        test_dir = util.writeTestFiles(Test_Custom_Bin_Dir, True)
        stdout = self.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)
        self.assertIn('this message should be printed', stdout)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_customBinSubDir(self):
        test_dir = util.writeTestFiles(Test_Custom_Bin_Sub_Dir, True)
        stdout = self.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)
        self.assertIn('this message should be printed', stdout)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_customBinSubSourceDir(self):
        test_dir = util.writeTestFiles(Test_Custom_Bin_Sub_Source_Dir, True)
        stdout = self.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)
        self.assertIn('this message should be printed', stdout)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_libAndBinSpecified(self):
        test_dir = util.writeTestFiles(Test_Lib_And_Bin)
        stdout, stderr, statuscode = cli.run(['--target', util.nativeTarget(), 'build'], cwd=test_dir)
        self.assertNotEqual(statuscode, 0)
        self.assertIn('Both "lib" and "bin" are specified in module.json: only one is allowed', stdout+stderr)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_libNonExistent(self):
        test_dir = util.writeTestFiles(Test_Lib_Nonexistent)
        stdout, stderr, statuscode = cli.run(['--target', util.nativeTarget(), 'build'], cwd=test_dir)
        self.assertIn('directory "doesntexist" doesn\'t exist', stdout+stderr)
        # !!! FIXME: should this error be fatal?
        # self.assertNotEqual(statuscode, 0)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_binNonExistent(self):
        test_dir = util.writeTestFiles(Test_Bin_Nonexistent)
        stdout, stderr, statuscode = cli.run(['--target', util.nativeTarget(), 'build'], cwd=test_dir)
        self.assertIn('directory "doesntexist" doesn\'t exist', stdout+stderr)
        # !!! FIXME: should this error be fatal?
        # self.assertNotEqual(statuscode, 0)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_misspeltSourceDir1(self):
        test_dir = util.writeTestFiles(Test_Misspelt_Source_Dir_1)
        stdout = self.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)
        self.assertIn("has non-standard source directory name", stdout)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_misspeltSourceDir2(self):
        test_dir = util.writeTestFiles(Test_Misspelt_Source_Dir_2)
        stdout = self.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)
        self.assertIn("has non-standard source directory name", stdout)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_misspeltSourceDirIgnored(self):
        test_dir = util.writeTestFiles(Test_Ignored_Misspelt_Source_Dir)
        stdout = self.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)
        self.assertNotIn("has non-standard source directory name", stdout)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_scriptsPreBuild(self):
        test_dir = util.writeTestFiles(Test_Scripts_PreBuild)
        stdout = self.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)
        self.assertIn("running prebuild", stdout)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_scriptsPostBuild(self):
        test_dir = util.writeTestFiles(Test_Scripts_PostBuild)
        stdout = self.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)
        self.assertIn("running postbuild", stdout)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_scriptsPreGenerate(self):
        test_dir = util.writeTestFiles(Test_Scripts_PreGenerate)
        stdout = self.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)
        self.assertIn("running pregenerate", stdout)
        util.rmRf(test_dir)

    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_Defines_Application(self):
        test_dir = util.writeTestFiles(Test_Defines_Application)
        stdout = self.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)
        output = subprocess.check_output(['./build/' + util.nativeTarget().split(',')[0] + '/source/test-defines-app'], cwd=test_dir).decode()
        self.assertIn("1234 yotta", output)
        util.rmRf(test_dir)


    @unittest.skipIf(not util.canBuildNatively(), "can't build natively on windows yet")
    def test_Defines_Library(self):
        test_dir = util.writeTestFiles(Test_Defines_Library)
        stdout = self.runCheckCommand(['--target', util.nativeTarget(), 'build'], test_dir)
        self.assertIn("defines.json ignored in library module 'test-defines-lib'", stdout)
        util.rmRf(test_dir)

    def runCheckCommand(self, args, test_dir):
        stdout, stderr, statuscode = cli.run(args, cwd=test_dir)
        if statuscode != 0:
            print('command failed with status %s' % statuscode)
            print(stdout)
            print(stderr)
        self.assertEqual(statuscode, 0)
        return stdout + stderr
