# standard library modules, , ,
import re
import logging

# access_common, , things shared between different component access modules, internal
import access_common
# version, , represent versions and specifications, internal
import version


# Internal functions

# ...


# API
class RegistryComponentVersion(access_common.RemoteVersion):
    def unpackInto(self, directory):
        # we get the tarball by requesting our version info from the registry,
        # with /tarball appended
        pass
        #_getTarball(url, directory)

class RegistryComponent(access_common.RemoteComponent):
    def __init__(self, name, version_spec):
        self.name = name
        self.spec = version.Spec(version_spec)
    
    @classmethod
    def createFromNameAndSpec(cls, version_spec, name):
        ''' returns a registry component for anything that's a valid package
            name (this does not guarantee that the component actually exists in
            the registry: use availableVersions() for that).
        '''
        # we deliberately allow only lowercase, hyphen, and (unfortunately)
        # numbers in package names, to reduce the possibility of confusingly
        # similar names: if the name doesn't match this then escalate to make
        # the user fix it
        name_match = re.match('^([a-z0-9-]+)$', name)
        if not name_match:
            logging.warning(
                'Dependency name "%s" is not valid (must contain only lowercase letters, hyphen, and numbers)' % name
            )
            return None
        try:
            spec = version.Spec(version_spec)
            return RegistryComponent(name, version_spec)
        except ValueError, e:
            pass
        return None

    def versionSpec(self):
        return self.spec

    def availableVersions(self):
        #''' return a list of Version objects, each able to retrieve a tarball '''
        return []

    def tipVersion(self):
        #return RegistryComponentVersion('', _getTipArchiveURL(self.repo))
        return None
    
