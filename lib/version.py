# Semantic Versioning, BSD, Represent and compare version strings, pip install semantic_version
import semantic_version


# Parse and match pure version strings and version specifications
#
# Versions:
#   1.2.3
#   1.2.3b1
#
# Version Specifications:
#  1.2.3
#  >1.2.3
#  <1.2.3
#  >=1.2.3
#  <=1.2.3
#
# For full details see semantic_version documentation
#

class TipVersion(object):


class Version(semantic_version.Version):
    def __init__(self, version_string, url=None):
        # Extend the semantic_version Version class with a url parameter that
        # can be used to store the URL from which we can obtain this version.
        # Don't allow partial versions.
        super(Version, self).__init__(version_string, partial=False)
        self.url = url


# Extend the spec to accept 'any version' strings ('' or '*')
class AnySpec(object):
    def filter(self, versions):
        return versions
    def select(self, versions):
        try:
            return sorted(versions)[-1]
        except IndexError:
            return None
    def __repr__(self):
        return '*'

class Spec(semantic_version.Spec):
    @staticmethod
    def __new__(cls, version_spec):
        if version_spec == '' or version_spec == '*':
            return AnySpec.__new__(AnySpec)
        else:
            return semantic_version.Spec.__new__(cls)

