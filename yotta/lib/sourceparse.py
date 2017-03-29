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

# version, , represent versions and specifications, internal
from yotta.lib import version


class InvalidVersionSpec(ValueError):
    pass

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
        if isinstance(v, str):
            v = version.Version(v)
        if self.semantic_spec is None:
            return True
        else:
            return self.semantic_spec.match(v)


def _getNonRegistryRef(source_url):
    import re

    # something/something#spec = github
    # something/something@spec = github
    # something/something spec = github
    github_match = re.match('^([.a-z0-9_-]+/([.a-z0-9_-]+)) *[@#]?([.a-z0-9_\-\*\^\~\>\<\=]*)$', source_url, re.I)
    if github_match:
        return github_match.group(2), VersionSource('github', github_match.group(1), github_match.group(3))

    parsed = urlsplit(source_url)

    # github
    if parsed.netloc.endswith('github.com'):
        # any URL onto github should be fetched over the github API, even if it
        # would parse as a valid git URL
        name_match = re.match('^/([.a-z0-9_-]+/([.a-z0-9_-]+?))(.git)?$', parsed.path, re.I)
        if name_match:
            return name_match.group(2), VersionSource('github', name_match.group(1), parsed.fragment)

    if '#' in source_url:
        without_fragment = source_url[:source_url.index('#')]
    else:
        without_fragment = source_url

    # git
    if parsed.scheme.startswith('git+') or parsed.path.endswith('.git'):
        # git+anything://anything or anything.git is a git repo:
        name_match = re.match('^.*?([.a-z0-9_-]+?)(.git)?$', parsed.path, re.I)
        if name_match:
            return name_match.group(1), VersionSource('git', without_fragment, parsed.fragment)

    # mercurial
    if parsed.scheme.startswith('hg+') or parsed.path.endswith('.hg'):
        # hg+anything://anything or anything.hg is a hg repo:
        name_match = re.match('^.*?([.a-z0-9_-]+?)(.hg)?$', parsed.path, re.I)
        if name_match:
            return name_match.group(1), VersionSource('hg', without_fragment, parsed.fragment)

    return None, None


def parseSourceURL(source_url):
    ''' Parse the specified version source URL (or version spec), and return an
        instance of VersionSource
    '''
    name, spec = _getNonRegistryRef(source_url)
    if spec:
        return spec

    try:
        url_is_spec = version.Spec(source_url)
    except ValueError:
        url_is_spec = None

    if url_is_spec is not None:
        # if the url is an unadorned version specification (including an empty
        # string) then the source is the module registry:
        return VersionSource('registry', '', source_url)

    raise InvalidVersionSpec("Invalid version specification: \"%s\"" % (source_url))


def isValidSpec(spec_or_source_url):
    ''' Check if the specified version source URL (or version spec), can be
        parsed successfully.
    '''
    try:
        parseSourceURL(spec_or_source_url)
        return True
    except InvalidVersionSpec:
        return False


def parseTargetNameAndSpec(target_name_and_spec):
    ''' Parse targetname[@versionspec] and return a tuple
        (target_name_string, version_spec_string).

        targetname[,versionspec] is also supported (this is how target names
        and specifications are stored internally, and was the documented way of
        setting the spec on the commandline)

        Also accepts raw github version specs (Owner/reponame#whatever), as the
        name can be deduced from these.

        Note that the specification split from the name is not validated. If
        there is no specification (just a target name) passed in, then '*' will
        be returned as the specification.
    '''
    import re
    # fist check if this is a raw github specification that we can get the
    # target name from:
    name, spec = _getNonRegistryRef(target_name_and_spec)
    if name:
        return name, target_name_and_spec

    # next split at the first @ or , if any
    split_at = '@'
    if target_name_and_spec.find('@') > target_name_and_spec.find(',') and \
            ',' in target_name_and_spec:
        split_at = ','
    name = target_name_and_spec.split(split_at)[0]
    spec = target_name_and_spec[len(name)+1:]

    name = name.strip()

    # if there's no specification, return the explicit any-version
    # specification:
    if not spec:
        spec = '*'

    return name, spec

def parseModuleNameAndSpec(module_name_and_spec):
    ''' Parse modulename[@versionspec] and return a tuple
        (module_name_string, version_spec_string).

        Also accepts raw github version specs (Owner/reponame#whatever), as the
        name can be deduced from these.

        Note that the specification split from the name is not validated. If
        there is no specification (just a module name) passed in, then '*' will
        be returned as the specification.
    '''
    import re
    # fist check if this is a raw github specification that we can get the
    # module name from:
    name, spec = _getNonRegistryRef(module_name_and_spec)
    if name:
        return name, module_name_and_spec

    # next split at the first @, if any
    name = module_name_and_spec.split('@')[0]
    spec = module_name_and_spec[len(name)+1:]

    name = name.strip()

    # if there's no specification, return the explicit any-version
    # specification:
    if not spec:
        spec = '*'

    return name, spec
