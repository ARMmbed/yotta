# standard library modules, , ,
import re
import logging
from collections import OrderedDict
import uuid
    
# restkit, MIT, HTTP client library for RESTful APIs, pip install restkit
from restkit import Resource, BasicAuth, errors as restkit_errors
from restkit.forms import multipart_form_encode

# settings, , load and save settings, internal
import settings
# connection_pool, , shared connection pool, internal
import connection_pool
# access_common, , things shared between different component access modules, internal
import access_common
# version, , represent versions and specifications, internal
import version
# Ordered JSON, , read & write json, internal
import ordered_json


# !!! FIXME get SSL cert for main domain
#Registry_Base_URL = 'https://registry.yottos.org' 
Registry_Base_URL = 'https://pure-earth-8670.herokuapp.com'


# Internal functions

def _registryAuthFilter():
    # basic auth until we release publicly, to prevent outside registry access,
    # after that this will be removed
    return  BasicAuth('yotta','h297fb08625rixmzw7s9')

# !!! FIXME: wrap for github auth
def _listVersions(namespace, name):
    # list versions of the package:
    url = '%s/%s/%s?access_token=%s' % (
        Registry_Base_URL,
        namespace,
        name,
        settings.getProperty('github', 'authtoken')
    )
    headers = { }
    auth = _registryAuthFilter()
    resource = Resource(url, pool=connection_pool.getPool(), filters=[auth])
    try:
        response = resource.get(
            headers = headers
        )
    except restkit_errors.ResourceNotFound as e:
        raise access_common.ComponentUnavailable(
            '%s does not exist in the %s registry' % (name, namespace)
        )
    body_s = response.body_string()
    return [x['version'] for x in ordered_json.loads(body_s)]

def _tarballURL(namespace, name, version):
    return '%s/%s/%s/%s/tarball' % (
        Registry_Base_URL, namespace, name, version
    )

# !!! FIXME: wrap for github auth
def _getTarball(tarball_url, directory):
    url = '%s?access_token=%s' % (
        tarball_url,
        settings.getProperty('github', 'authtoken')
    )
    headers = { }
    auth = _registryAuthFilter()
    resource = Resource(url, pool=connection_pool.getPool(), filters=[auth], follow_redirect=True)
    response = resource.get(
        headers = headers
    )
    print 'response:', response
    print 'headers:', dict(response.headers.items())
    return access_common.unpackTarballStream(response.body_stream(), directory)


# API
class RegistryThingVersion(access_common.RemoteVersion):
    def unpackInto(self, directory):
        assert(self.url)
        _getTarball(self.url, directory)

class RegistryThing(access_common.RemoteComponent):
    def __init__(self, name, version_spec, namespace):
        self.name = name
        self.spec = version.Spec(version_spec)
        # !!! FIXME: switch the /package namespace to /component to be
        # consistent, and remove this
        if namespace == 'component':
            namespace = 'package'
        self.namespace = namespace
    
    @classmethod
    def createFromNameAndSpec(cls, version_spec, name, registry):
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
            return RegistryThing(name, version_spec, registry)
        except ValueError, e:
            pass
        return None

    def versionSpec(self):
        return self.spec

    def availableVersions(self):
        ''' return a list of Version objects, each able to retrieve a tarball '''
        version_strings = _listVersions(self.namespace, self.name)
        return [RegistryThingVersion(s, _tarballURL(self.namespace, self.name, s)) for s in version_strings]

    def tipVersion(self):
        raise NotImplementedError()


# !!! FIXME: wrap for github auth
def publish(namespace, name, version, description_file, tar_file):
    ''' Publish a tarblob to the registry, return any error encountered, or
        None if successful.
    '''

    url = '%s/%s/%s/%s?access_token=%s' % (
        Registry_Base_URL,
        namespace,
        name,
        version,
        settings.getProperty('github', 'authtoken')
    )
    
    # description file is in place as text (so read it), tar file is a file
    body = OrderedDict([('metadata',description_file.read()), ('tarball',tar_file)])
    headers = { }
    body, headers = multipart_form_encode(body, headers, uuid.uuid4().hex)

    auth = _registryAuthFilter()
    resource = Resource(url, pool=connection_pool.getPool(), filters=[auth])

    try:
        response = resource.put(
            headers = headers,
            payload = body
        )
    except restkit_errors.RequestFailed as e:
        return "sever returned status %s: %s" % (e.status_int, e.message)

    return None

