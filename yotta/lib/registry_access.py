# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import re
import logging
from collections import OrderedDict
import uuid
import functools
import json
import binascii
import calendar
import datetime
import hashlib
import itertools
import urllib
import base64
import webbrowser
    
# restkit, MIT, HTTP client library for RESTful APIs, pip install restkit
from restkit import Resource, BasicAuth, errors as restkit_errors
from restkit.forms import multipart_form_encode

# PyJWT, MIT, Jason Web Tokens, pip install PyJWT
import jwt
# pycrypto, Public Domain, Python Crypto Library, pip install pyCRypto
import Crypto
from Crypto.PublicKey import RSA

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
# Github Access, , access repositories on github, internal
import github_access

# !!! FIXME get SSL cert for main domain, then use HTTPS
Registry_Base_URL = 'http://registry.yottabuild.org'
Website_Base_URL  = 'http://yottabuild.org'
_OpenSSH_Keyfile_Strip = re.compile("^(ssh-[a-z0-9]*\s+)|(\s+.+\@.+)|\n", re.MULTILINE)

logger = logging.getLogger('access')

# Internal functions

class _BearerJWTFilter(object):
    def __init__(self, private_key):
        super(_BearerJWTFilter, self).__init__()
        expires = calendar.timegm((datetime.datetime.utcnow() + datetime.timedelta(hours=2)).timetuple())
        prn = _fingerprint(private_key.publickey())
        logger.debug('fingerprint: %s' % prn)
        token_fields = {
            "iss": 'yotta',
            "aud": Registry_Base_URL,
            "prn": prn,
            "exp": str(expires)
        }
        logger.debug('token fields: %s' % token_fields)
        self.token = jwt.encode(token_fields, private_key, 'RS256')
        logger.debug('encoded token: %s' % self.token)

    def on_request(self, request):
        request.headers['Authorization'] = 'Bearer ' + self.token


def _pubkeyWireFormat(pubkey):
    return urllib.quote(_OpenSSH_Keyfile_Strip.sub('', pubkey.exportKey('OpenSSH')))

def _fingerprint(pubkey):
    stripped = _OpenSSH_Keyfile_Strip.sub('', pubkey.exportKey('OpenSSH'))
    decoded  = base64.b64decode(stripped)
    khash    = hashlib.md5(decoded).hexdigest()
    return ':'.join([khash[i:i+2] for i in xrange(0, len(khash), 2)])


def _registryAuthFilter():
    # basic auth until we release publicly, to prevent outside registry access,
    # after that this will be removed
    return  _BearerJWTFilter(_getPrivateKeyObject())

def _returnRequestError(fn):
    ''' Decorator that captures un-caught restkit_errors.RequestFailed errors
        and returns them as an error message. If no error occurs the reture
        value of the wrapped function is returned (normally None). '''
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except restkit_errors.RequestFailed as e:
            return "sever returned status %s: %s" % (e.status_int, e.message)
    return wrapped
 
def _handleAuth(fn):
    ''' Decorator to re-try API calls after asking the user for authentication. '''
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except restkit_errors.Unauthorized as e:
            github_access.authorizeUser()
            logger.debug('trying with authtoken:', settings.getProperty('github', 'authtoken'))
            return fn(*args, **kwargs)
    return wrapped

def _friendlyAuthError(fn):
    ''' Decorator to print a friendly you-are-not-authorised message. Use
        **outside** the _handleAuth decorator to only print the message after
        the user has been given a chance to login. '''
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except restkit_errors.Unauthorized as e:
            logger.error('insufficient permission')
            return None
    return wrapped

def _listVersions(namespace, name):
    # list versions of the package:
    url = '%s/%s/%s/versions' % (
        Registry_Base_URL,
        namespace,
        name
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
    return [RegistryThingVersion(x, namespace, name) for x in ordered_json.loads(body_s)]

def _tarballURL(namespace, name, version):
    return '%s/%s/%s/versions/%s/tarball' % (
        Registry_Base_URL, namespace, name, version
    )

def _getTarball(url, directory, sha256):
    auth = _registryAuthFilter()
    logger.debug('registry: get: %s' % url)
    if not sha256:
        logger.warn('tarball %s has no hash to check' % url)
    resource = Resource(url, pool=connection_pool.getPool(), filters=[auth])
    #resource = Resource('http://blobs.yottos.org/targets/stk3700-0.0.0.tar.gz', pool=connection_pool.getPool(), follow_redirect=True)
    response = resource.get()
    # there seems to be an issue with following the redirect using restkit:
    # follow redirect manually
    if response.status_int == 302 and 'Location' in response.headers:
        redirect_url = response.headers['Location']
        logger.debug('registry: redirect to: %s' % redirect_url)
        resource = Resource(redirect_url, pool=connection_pool.getPool())
        response = resource.get()
    return access_common.unpackTarballStream(response.body_stream(), directory, ('sha256', sha256))

def _generateAndSaveKeys():
    k = RSA.generate(2048)
    privatekey_hex = binascii.hexlify(k.exportKey('DER'))
    settings.setProperty('keys', 'private', privatekey_hex)
    pubkey_hex = binascii.hexlify(k.publickey().exportKey('DER'))
    settings.setProperty('keys', 'public', pubkey_hex)
    return pubkey_hex, privatekey_hex

def _getPrivateKeyObject():
    privatekey_hex =  settings.getProperty('keys', 'private')
    if not privatekey_hex:
        pubkey_hex, privatekey_hex = _generateAndSaveKeys()
    return RSA.importKey(binascii.unhexlify(privatekey_hex))

# API
class RegistryThingVersion(access_common.RemoteVersion):
    def __init__(self, data, namespace, name):
        logger.debug('RegistryThingVersion %s/%s data: %s' % (namespace, name, data))
        version = data['version']
        self.namespace = namespace
        self.name = name
        if 'hash' in data and 'sha256' in data['hash']:
            self.sha256 = data['hash']['sha256']
        else:
            self.sha256 = None
        url = _tarballURL(self.namespace, self.name, version)
        super(RegistryThingVersion, self).__init__(version, url)

    def unpackInto(self, directory):
        assert(self.url)
        _getTarball(self.url, directory, self.sha256)

class RegistryThing(access_common.RemoteComponent):
    def __init__(self, name, version_spec, namespace):
        self.name = name
        self.spec = version_spec
        self.namespace = namespace
    
    @classmethod
    def createFromSource(cls, vs, name, registry):
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
            logger.warning(
                
            )
            raise ValueError('Dependency name "%s" is not valid (must contain only lowercase letters, hyphen, and numbers)' % name)
        assert(vs.semantic_spec)
        return RegistryThing(name, vs.semantic_spec, registry)

    def versionSpec(self):
        return self.spec

    def availableVersions(self):
        ''' return a list of Version objects, each able to retrieve a tarball '''
        return _listVersions(self.namespace, self.name)

    def tipVersion(self):
        raise NotImplementedError()
    
    @classmethod
    def remoteType(cls):
        return 'registry'

@_returnRequestError
@_handleAuth
def publish(namespace, name, version, description_file, tar_file, readme_file, readme_file_ext):
    ''' Publish a tarblob to the registry, if the request fails, an exception
        is raised, which either triggers re-authentication, or is turned into a
        return value by the decorators. (If successful, the decorated function
        returns None)
    '''

    url = '%s/%s/%s/versions/%s' % (
        Registry_Base_URL,
        namespace,
        name,
        version
    )

    if readme_file_ext == '.md':
        readme_section_name = 'readme.md'
    elif readme_file_ext == '':
        readme_section_name = 'readme'
    else:
        raise ValueError('unsupported readme type: "%s"' % readne_file_ext)
    
    # description file is in place as text (so read it), tar file is a file
    body = OrderedDict([('metadata',description_file.read()), ('tarball',tar_file), (readme_section_name, readme_file)])
    headers = { }
    body, headers = multipart_form_encode(body, headers, uuid.uuid4().hex)

    auth = _registryAuthFilter()
    resource = Resource(url, pool=connection_pool.getPool(), filters=[auth])

    response = resource.put(
        headers = headers,
        payload = body
    )

    return None

@_friendlyAuthError
@_handleAuth
def listOwners(namespace, name):
    ''' List the owners of a module or target (owners are the people with
        permission to publish versions and add/remove the owners). 
    '''
    url = '%s/%s/%s/owners' % (
        Registry_Base_URL,
        namespace,
        name
    )
    auth = _registryAuthFilter()
    resource = Resource(url, pool=connection_pool.getPool(), filters=[auth])
    try:
        response = resource.get()
    except restkit_errors.ResourceNotFound as e:
        logger.error('no such %s, "%s"' % (namespace, name))
        return None
    return ordered_json.loads(response.body_string())

@_friendlyAuthError
@_handleAuth
def addOwner(namespace, name, owner):
    ''' Add an owner for a module or target (owners are the people with
        permission to publish versions and add/remove the owners). 
    '''
    url = '%s/%s/%s/owners/%s' % (
        Registry_Base_URL,
        namespace,
        name,
        owner
    )
    auth = _registryAuthFilter()
    resource = Resource(url, pool=connection_pool.getPool(), filters=[auth])

    try:
        response = resource.put()
    except restkit_errors.ResourceNotFound as e:
        logger.error('no such %s, "%s"' % (namespace, name))

@_friendlyAuthError
@_handleAuth
def removeOwner(namespace, name, owner):
    ''' Remove an owner for a module or target (owners are the people with
        permission to publish versions and add/remove the owners). 
    '''
    url = '%s/%s/%s/owners/%s' % (
        Registry_Base_URL,
        namespace,
        name,
        owner
    )
    auth = _registryAuthFilter()
    resource = Resource(url, pool=connection_pool.getPool(), filters=[auth])
    
    try:
        response = resource.delete()
    except restkit_errors.ResourceNotFound as e:
        logger.error('no such %s, "%s"' % (namespace, name))


def deauthorize():
    if settings.getProperty('keys', 'private'):
        settings.setProperty('keys', 'private', '')
    if settings.getProperty('keys', 'public'):
        settings.setProperty('keys', 'public', '')

def getPublicKey():
    ''' Return the user's public key (generating and saving a new key pair if necessary) '''
    pubkey_hex = settings.getProperty('keys', 'public')
    if not pubkey_hex:
        k = RSA.generate(2048)
        settings.setProperty('keys', 'private', binascii.hexlify(k.exportKey('DER')))
        pubkey_hex = binascii.hexlify(k.publickey().exportKey('DER'))
        settings.setProperty('keys', 'public', pubkey_hex)
        pubkey_hex, privatekey_hex = _generateAndSaveKeys()
    return _pubkeyWireFormat(RSA.importKey(binascii.unhexlify(pubkey_hex)))

def testLogin():
    url = '%s/users/me' % (
        Registry_Base_URL
    )
    headers = { }
    auth = _registryAuthFilter()
    resource = Resource(url, pool=connection_pool.getPool(), filters=[auth])
    logger.debug('test login...')
    response = resource.get(
        headers = headers
    )

def getAuthData():
    ''' Poll the registry to get the result of a completed authentication
        (which, depending on the authentication the user chose or was directed
        to, will include a github or other access token)
    '''
    url = '%s/tokens' % (
        Registry_Base_URL
    )
    headers = { }
    auth = _registryAuthFilter()
    resource = Resource(url, pool=connection_pool.getPool(), filters=[auth])
    try:
        logger.debug('poll for tokens...')
        response = resource.get(
            headers = headers
        )
    except restkit_errors.Unauthorized as e:
        logger.debug(str(e))
        return None
    except restkit_errors.ResourceNotFound as e:
        logger.debug(str(e))
        return None    
    except restkit_errors.RequestFailed as e:
        logger.debug(str(e))
        return None
    body = response.body_string()
    logger.debug('auth data response: %s' % body);
    r = {}
    for token in ordered_json.loads(body):
        if token['provider'] == 'github':
            r['github'] = token['accessToken']
            break
    logger.debug('parsed auth tokens %s' % r);
    return r

def openBrowserLogin(provider=None):
    if provider:
        query = '?provider=github'
    else:
        query = ''
    webbrowser.open(Website_Base_URL + '/#login/' + getPublicKey() + query)
