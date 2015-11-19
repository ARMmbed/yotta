#!/usr/bin/env python
# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import tempfile
import os

# internal modules:
from yotta.lib.fsutils import mkDirP

# some simple example module definitions that can be re-used by multiple tests:
Test_Trivial_Lib = {
'module.json':'''{
  "name": "test-trivial-lib",
  "version": "0.0.2",
  "description": "Module to test trivial lib compilation",
  "licenses": [
    {
      "url": "https://spdx.org/licenses/Apache-2.0",
      "type": "Apache-2.0"
    }
  ],
  "dependencies": {
  }
}''',

'test-trivial-lib/lib.h': '''
int foo();
''',

'source/lib.c':'''
#include "test-trivial-lib/lib.h"

int foo(){
    return 7;
}
'''
}

Test_Trivial_Exe = {
'module.json':'''{
  "name": "test-trivial-exe",
  "version": "0.0.2",
  "description": "Module to test trivial exe compilation",
  "licenses": [
    {
      "url": "https://spdx.org/licenses/Apache-2.0",
      "type": "Apache-2.0"
    }
  ],
  "dependencies": {
  },
  "bin":"./source"
}''',

'source/lib.c':'''
int main(){
    return 0;
}
'''
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
        mkDirP(path_dir)
        with open(os.path.join(path_dir, file_name), 'w') as f:
            f.write(contents)
    return test_dir

