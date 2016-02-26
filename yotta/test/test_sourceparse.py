#!/usr/bin/env python
# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# standard library modules, , ,
import unittest

# sourceparse, , parse version source urls, internal
from yotta.lib import sourceparse


Registry_URLs = [
    '',
    '*',
    '1.2.3',
    '>=1.2.3',
    '^0.1.2',
    '~0.1.2',
]

Github_URLs = [
    'username/reponame',
    'username/reponame#1.2.3',
    'username/reponame#^1.2.3',
    'username/reponame#-1.2.3',
    'username/reponame#branch-or-tag-name',
    'username/reponame@1.2.3',
    'username/reponame@^1.2.3',
    'username/reponame@-1.2.3',
    'username/reponame@branch-or-tag-name',
]

Git_URLs = [
    'git+ssh://somewhere.com/something/etc/etc',
    'git+ssh://somewhere.com/something/etc/etc#1.2.3',
    'git+ssh://somewhere.com/something/etc/etc#^1.2.3',
    'git+ssh://somewhere.com/something/etc/etc#~1.2.3',
    'git+ssh://somewhere.com/something/etc/etc#branch-name',
    'ssh://somewhere.com/something/etc/etc.git',
    'ssh://somewhere.com/something/etc/etc.git#^1.2.3',
    'ssh://somewhere.com/something/etc/etc.git#~1.2.3',
    'ssh://somewhere.com/something/etc/etc.git#branch-name',
    'http://somewhere.something/something.git',
]

HG_URLs = [
    'hg+ssh://somewhere.com/something/etc/etc',
    'hg+ssh://somewhere.com/something/etc/etc#1.2.3',
    'hg+ssh://somewhere.com/something/etc/etc#^1.2.3',
    'hg+ssh://somewhere.com/something/etc/etc#~1.2.3',
    'ssh://somewhere.com/something/etc/etc.hg',
    'ssh://somewhere.com/something/etc/etc.hg#^1.2.3',
    'ssh://somewhere.com/something/etc/etc.hg#~1.2.3',
    'http://somewhere.something/something.hg',
]

test_invalid_urls = [
    'stuff otherstuff',
    'somthing/somethingelse/somethingelseagain'
]


class TestParseSourceURL(unittest.TestCase):
    def test_registryURLs(self):
        for url in Registry_URLs:
            sv = sourceparse.parseSourceURL(url)
            self.assertEqual(sv.source_type, 'registry')

    def test_githubURLs(self):
        for url in Github_URLs:
            sv = sourceparse.parseSourceURL(url)
            self.assertEqual(sv.source_type, 'github')

    def test_gitURLs(self):
        for url in Git_URLs:
            sv = sourceparse.parseSourceURL(url)
            self.assertEqual(sv.source_type, 'git')

    def test_hgURLs(self):
        for url in HG_URLs:
            sv = sourceparse.parseSourceURL(url)
            self.assertEqual(sv.source_type, 'hg')

    def test_invalid(self):
        for url in test_invalid_urls:
            self.assertRaises(ValueError, sourceparse.parseSourceURL, url)

Valid_Names = [
    'validname',
    'another-validname',
    'another-valid2name123'
]

class TestParseModuleNameAndSpec(unittest.TestCase):
    def test_validNames(self):
        for name in Valid_Names:
            n, s = sourceparse.parseModuleNameAndSpec(name)
            self.assertEqual(n, name)
            self.assertEqual(s, '*')

    def test_GithubRefs(self):
        for url in Github_URLs:
            n, s = sourceparse.parseModuleNameAndSpec(url)
            self.assertEqual(n, 'reponame')

    def test_atVersion(self):
        for name in Valid_Names:
            for v in Registry_URLs:
                if len(v):
                    nv = name + '@' + v
                    n, s = sourceparse.parseModuleNameAndSpec(nv)
                    self.assertEqual(n, name)
                    self.assertEqual(s, v)

    def test_atGitURL(self):
        for name in Valid_Names:
            for v in Git_URLs:
                nv = name + '@' + v
                n, s = sourceparse.parseModuleNameAndSpec(nv)
                self.assertEqual(n, name)
                self.assertEqual(s, v)

    def test_atHGURL(self):
        for name in Valid_Names:
            for v in HG_URLs:
                nv = name + '@' + v
                n, s = sourceparse.parseModuleNameAndSpec(nv)
                self.assertEqual(n, name)
                self.assertEqual(s, v)


if __name__ == '__main__':
    unittest.main()


