#! /usr/bin/env python2.7
import os
import shutil
import errno

from lib import access
from lib import component
from lib.pool import pool

package_json = '''{
  "name": "yottos",
  "version": "0.0.7",
  "description": "The core Yottos scheduler.",
  "private": false,
  "main": "",
  "scripts": {
    "test": "echo \\"Error: no test specified\\" && exit 1"
  },
  "repository": {
    "type": "git",
    "url": "ssh://nadc-login2.nadc.arm.com//projects/pd/randd/git/iot/yottos/yottos"
  },
  "homepage": "ssh://nadc-login2.nadc.arm.com//projects/pd/randd/git/iot/yottos/yottos",
  "bugs": {
    "url": "about:blank",
    "email": "project@hostname.com"
  },
  "author": "James Crosby <James.Crosby@arm.com>",
  "licenses": [
    {
      "type": "Copyright (C) 2013 ARM Limited, all rights reserved.",
      "url": "about:blank"
    }
  ],
  "dependencies": {
    "toolchain": "ARM-RD/toolchain",
    "libc": "ARM-RD/libc",
    "objc2": "ARM-RD/libobjc2 @>0.0.7",
    "yottos_platform": "ARM-RD/yottos-platform @0.0.3",
    "emlib": "ARM-RD/emlib",
    "nsobject": "ARM-RD/nsobject",
    "nslog": "ARM-RD/nslog",
    "nsassert": "ARM-RD/nsassert",
    "thisdoesnotexist": "ARM-RD/thisdoesnotexist"
  },
  "devDependencies": {}
}
'''

testdir = '/tmp/yttest/yottos'


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

pool.map(
    lambda (name, ver_req): access.satisfyVersion(name, ver_req, testdir, available),
    c.getDependencies()
)


