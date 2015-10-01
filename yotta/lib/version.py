# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import re

# Semantic Versioning, BSD, Represent and compare version strings, pip install -e git://github.com/autopulated/python-semanticversion.git#egg=semantic_version
# not sure why pylint can't import this...
import semantic_version

# Parse and match pure version strings and version specifications
#
# Versions:
#   "v1.2.3"
#   "1.2.3"
#   "v1.2.3b1"
#   ""        (tip)
#
# Version Specifications:
#  "1.2.3"
#  ">1.2.3"
#  "<1.2.3"
#  ">=1.2.3"
#  "<=1.2.3"
#  "*"        (any version)
#  ""         (any version)
#
# For full details see semantic_version documentation
#

class TipVersion(object):
    pass

class Version(object):
    def __init__(self, version_string, url=None):
        ''' Wrap the semantic_version Version class so that we can represent
            'tip' versions as well as specific versions, and store an optional
            URL that can represent the location from which we can retrieve this
            version.

            Also add some useful methods for manipulating versions.
        '''
        super(Version, self).__init__()
        self.url = url
        version_string = str(version_string.strip())
        # strip of leading v or = characters, these are permitted in npm's
        # semver, and npm tags versions as v1.2.3
        self.version = None
        if version_string.startswith('v') or version_string.startswith('='):
            self.version = semantic_version.Version(version_string[1:], partial=False)
        elif not version_string:
            self.version = TipVersion()
        else:
            self.version = semantic_version.Version(version_string, partial=False)
        self.url = url

    def isTip(self):
        return isinstance(self.version, TipVersion)

    def major(self):
        assert(not isinstance(self.version, TipVersion))
        return self.version.major
    def minor(self):
        assert(not isinstance(self.version, TipVersion))
        return self.version.minor
    def patch(self):
        assert(not isinstance(self.version, TipVersion))
        return self.version.patch

    def bump(self, bumptype):
        if isinstance(self.version, str):
            raise ValueError('cannot bump generic version "%s"' % self.version)
        if bumptype == 'major':
            self.version.major = self.version.major + 1
            self.version.minor = 0
            self.version.patch = 0
            self.version.prerelease = ''
            self.version.build = ''
        elif bumptype == 'minor':
            self.version.minor = self.version.minor + 1
            self.version.patch = 0
            self.version.prerelease = ''
            self.version.build = ''
        elif bumptype == 'patch':
            self.version.patch = self.version.patch + 1
            self.version.prerelease = ''
            self.version.build = ''
        else:
            raise ValueError('bumptype must be "major", "minor" or "patch"')
        self.version.prerelease = None
        self.version.build = None

    def __str__(self):
        return str(self.version)

    def __repr__(self):
        return 'Version(%s %s)' % (self.version, self.url)

    def __cmp__(self, other):
        # if the other is an unwrapped version (used within the Spec class)
        if isinstance(other, semantic_version.Version):
            other_is_specific_ver = True
            other_is_unwrapped = True
        elif not hasattr(other, 'version'):
            return NotImplemented
        else:
            other_is_specific_ver = isinstance(other.version, semantic_version.Version)
            other_is_unwrapped = False

        self_is_specific_ver  = isinstance(self.version, semantic_version.Version)

        if isinstance(self.version, TipVersion) and other_is_specific_ver:
            return 1
        elif (not other_is_unwrapped) and isinstance(other.version, TipVersion) and self_is_specific_ver:
            return -1
        elif self_is_specific_ver and other_is_specific_ver:
            if other_is_unwrapped:
                return semantic_version.Version.__cmp__(self.version, other)
            else:
                return semantic_version.Version.__cmp__(self.version, other.version)
        elif isinstance(self.version, TipVersion) and isinstance(other.version, TipVersion):
            raise Exception('Comparing two "tip" versions is undefined')
        else:
            raise Exception('Unsupported version comparison: "%s" vs. "%s"' % (self.version, other.version))

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __hash__(self):
        return hash(self.version)

    def __ne__(self, other):
        return self.__cmp__(other) != 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def __le__(self, other):
        return self.__cmp__(other) <= 0

    def __gt__(self, other):
        return self.__cmp__(other) > 0

    def __ge__(self, other):
        return self.__cmp__(other) >= 0


# subclass to allow empty specification strings (equivalent to '*')
class Spec(semantic_version.Spec):
    def __init__(self, version_spec):
        if not version_spec:
            version_spec = '*'
        # add support for version specs that are unadorned versions, or a
        # single equals
        if re.match('^[0-9]', version_spec):
            version_spec = '==' + version_spec
        elif re.match('^=[0-9]', version_spec):
            version_spec = '=' + version_spec
        # add support for the ~ and ^ version specifiers:
        #  ~1.2.3 := >=1.2.3-0 <1.3.0-0
        #  ^1.2.3 := >=1.2.3-0 <2.0.0-0
        #  ^0.1.2 := 0.1.2 exactly (for 0.x.x versions)
        elif re.match('^\^', version_spec):
            v = semantic_version.Version(version_spec[1:])
            if v.major == 0:
                # for 0. releases, ^ means exact version only
                version_spec = '==' + str(v)
            else:
                v2 = Version(version_spec[1:])
                v2.bump('major')
                version_spec = '>=' + str(v) + ',<' +str(v2)
        elif re.match('^~', version_spec):
            v = semantic_version.Version(version_spec[1:])
            v2 = Version(version_spec[1:])
            v2.bump('minor')
            version_spec = '>=' + str(v) + ',<' +str(v2)
        super(Spec, self).__init__(version_spec)

    # base type contains function checks the type, so must replace it
    def __contains__(self, version):
        return self.match(version)
