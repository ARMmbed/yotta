# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# Utilities for parsing version source URLs, and determining how the
# specified version should be fetched.

# standard library modules, , ,
try:
    from urlparse import urlsplit
except ImportError:
    from urllib.parse import urlsplit #pylint: disable=no-name-in-module,import-error
import re

# version, , represent versions and specifications, internal
import version

class VersionSource(object):
    def __init__(self, source_type, location, spec):
        assert(source_type in ('registry', 'github', 'git', 'hg'))
        self.source_type = source_type
        self.location = location
        self.spec = spec
        try:
            self.semantic_spec = version.Spec(spec)
        except ValueError:
            # for git/github source URLs the spec is allowed to be a branch
            # name or tag name, as well as a valid semantic version
            # specification
            # !!! TODO: also allow hg here
            if source_type in ('git', 'github'):
                self.semantic_spec = None
            else:
                raise ValueError(
                    "Invalid semantic version spec: \"%s\"" % spec
                )

    def semanticSpec(self):
        return self.semantic_spec or version.Spec('*')

    def semanticSpecMatches(self, v):
        if self.semantic_spec is None:
            return True
        else:
            return self.semantic_spec.match(v)


def parseSourceURL(source_url):
    ''' Parse the specified version source URL (or version spec), and return an
        instance of VersionSource
    '''
    parsed = urlsplit(source_url)

    if '#' in source_url:
        without_fragment = source_url[:source_url.index('#')]
    else:
        without_fragment = source_url

    try:
        url_is_spec = version.Spec(source_url)
    except ValueError:
        url_is_spec = None

    if url_is_spec is not None:
        # if the url is an unadorned version specification (including an empty
        # string) then the source is the module registry:
        return VersionSource('registry', '', source_url)
    elif parsed.netloc.endswith('github.com'):
        # any URL onto github should be fetched over the github API, even if it
        # would parse as a valid git URL
        return VersionSource('github', parsed.path, parsed.fragment)
    elif parsed.scheme.startswith('git+') or parsed.path.endswith('.git'):
        # git+anything://anything or anything.git is a git repo:
        return VersionSource('git', without_fragment, parsed.fragment)
    elif parsed.scheme.startswith('hg+') or parsed.path.endswith('.hg'):
        # hg+anything://anything or anything.hg is a hg repo:
        return VersionSource('hg', without_fragment, parsed.fragment)
    elif re.match('^[a-z0-9_-]+/[a-z0-9_-]+$', without_fragment, re.I):
        # something/something#spec = github
        return VersionSource('github', without_fragment, parsed.fragment)

    # something/something@spec = github
    alternate_github_match = re.match('([a-z0-9_-]+/[a-z0-9_-]+) *@?([~^><=.0-9a-z\*-]*)', source_url, re.I)
    if alternate_github_match:
        return VersionSource('github', alternate_github_match.group(0), alternate_github_match.group(1))

    raise ValueError("Invalid version source url: \"%s\"" % (source_url))

