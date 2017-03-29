#!/usr/bin/env python
# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# standard library modules, , ,
import unittest

# sourceparse, , parse version source urls, internal
from yotta.lib import sourceparse

# Shorthand URLs for GitHub
ShortHand_URLs = [
    'username/reponame',
]

# Longhand URLs for GitHub
Github_URLs = [
    'https://github.com/username/reponame.git',
    'git://github.com/username/reponame.git',
    'git+http://username@github.com/username/reponame.git',
    'git+https://username@github.com/username/reponame.git',
]

Git_URLs = [
    'http://somewhere.something/reponame.git',
    'https://somewhere.something/reponame.git',
    'ssh://somewhere.com/something/etc/reponame.git',
    'git+ssh://somewhere.com/something/etc/reponame',
    'git@github.com:username/reponame.git',
]

HG_URLs = [
    'http://somewhere.something/reponame.hg',
    'https://somewhere.something/reponame.hg',
    'ssh://somewhere.com/something/etc/reponame.hg',
    'hg+ssh://somewhere.com/something/etc/reponame',
]

# We support version spec, branch name, tag name and commit id for GitHub and Git
Git_Specs = [
    '',
    '1.2.3',
    '^1.2.3',
    '~1.2.3',
    '-1.2.3',
    'branch-or-tag-name',
    'd5f5049',
]

# We support only version spec for HG
HG_Specs = [
    '',
    '1.2.3',
    '^1.2.3',
    '~1.2.3',
]

Registry_Specs = [
    '',
    '*',
    '1.2.3',
    '>=1.2.3',
    '^0.1.2',
    '~0.1.2',
]

test_invalid_urls = [
    'stuff otherstuff',
    'somthing/somethingelse/somethingelseagain'
]


class TestParseSourceURL(unittest.TestCase):
    def test_registryURLs(self):
        for url in Registry_Specs:
            sv = sourceparse.parseSourceURL(url)
            self.assertEqual(sv.source_type, 'registry')

    def test_shorthandURLs(self):
        for url in ShortHand_URLs:
            for s in Git_Specs:
                if len(s):
                    # Shorthand URLs support '@' and ' ' as well as '#'
                    for m in ['#', '@', ' ']:
                        sv = sourceparse.parseSourceURL(url + m + s)
                        self.assertEqual(sv.source_type, 'github')
                        self.assertEqual(sv.spec, s)
                else:
                    sv = sourceparse.parseSourceURL(url)
                    self.assertEqual(sv.source_type, 'github')
                    self.assertEqual(sv.spec, s)

    def test_githubURLs(self):
        for url in Github_URLs:
            for s in Git_Specs:
                if len(s):
                    source = url + '#' + s
                else:
                    source = url
                sv = sourceparse.parseSourceURL(source)
                self.assertEqual(sv.source_type, 'github')
                self.assertEqual(sv.spec, s)

    def test_gitURLs(self):
        for url in Git_URLs:
            for s in Git_Specs:
                if len(s):
                    source = url + '#' + s
                else:
                    source = url
                sv = sourceparse.parseSourceURL(source)
                self.assertEqual(sv.source_type, 'git')
                self.assertEqual(sv.spec, s)

    def test_hgURLs(self):
        for url in HG_URLs:
            for s in HG_Specs:
                if len(s):
                    source = url + '#' + s
                else:
                    source = url
                sv = sourceparse.parseSourceURL(source)
                self.assertEqual(sv.source_type, 'hg')
                self.assertEqual(sv.spec, s)

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

    def test_ShorthandRefs(self):
        for url in ShortHand_URLs:
            for spec in Git_Specs:
                if len(spec):
                    # Shorthand URLs support '@' and ' ' as well as '#'
                    for m in ['#', '@', ' ']:
                        ns = url + m + spec
                        n, s = sourceparse.parseModuleNameAndSpec(ns)
                        self.assertEqual(n, 'reponame')
                        self.assertEqual(s, ns)
                else:
                    n, s = sourceparse.parseModuleNameAndSpec(url)
                    self.assertEqual(n, 'reponame')
                    self.assertEqual(s, url)

    def test_GithubRefs(self):
        for url in Github_URLs:
            for spec in Git_Specs:
                if len(spec):
                    ns = url + '#' + spec
                else:
                    ns = url
                n, s = sourceparse.parseModuleNameAndSpec(ns)
                self.assertEqual(n, 'reponame')
                self.assertEqual(s, ns)

    def test_GitRefs(self):
        for url in Git_URLs:
            for spec in Git_Specs:
                if len(spec):
                    ns = url + '#' + spec
                else:
                    ns = url
                n, s = sourceparse.parseModuleNameAndSpec(ns)
                self.assertEqual(n, 'reponame')
                self.assertEqual(s, ns)

    def test_HGRefs(self):
        for url in HG_URLs:
            for spec in HG_Specs:
                if len(spec):
                    ns = url + '#' + spec
                else:
                    ns = url
                n, s = sourceparse.parseModuleNameAndSpec(ns)
                self.assertEqual(n, 'reponame')
                self.assertEqual(s, ns)

    def test_atVersion(self):
        for name in Valid_Names:
            for v in Registry_Specs:
                if len(v):
                    nv = name + '@' + v
                    n, s = sourceparse.parseModuleNameAndSpec(nv)
                    self.assertEqual(n, name)
                    self.assertEqual(s, v)


if __name__ == '__main__':
    unittest.main()
