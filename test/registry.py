#! /usr/bin/env python2.7
import os
import shutil
import errno
import logging

from yotta.lib import access
from yotta.lib import component
from yotta.lib.pool import pool

package_json = '''{
  "name": "registry-test",
  "version": "0.0.0",
  "description": "",
  "dependencies": {
    "cmsis-core": "*",
    "thisdoesnotexist": "*"
  }
}
'''

testdir = '/tmp/yttest/registry-access'

#logging.basicConfig(
#    level=logging.DEBUG,
#    format='%(message)s'
#)

def mkDirP(path):
    try:
        os.makedirs(path)
    except OSError, e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

try:
    shutil.rmtree(testdir)
except OSError: pass

mkDirP(testdir)
with open(os.path.join(testdir, 'package.json'), 'w') as f:
    f.write(package_json)

c = component.Component(testdir)

available = []

installed, errs = c.satisfyDependenciesRecursive()

for x in installed:
    print 'installed', x
for e in errs:
    print 'Error:', e


