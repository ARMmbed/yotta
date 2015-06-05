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
import base64
import webbrowser
import os
try:
    from urllib import quote as quoteURL
except ImportError:
    from urllib.parse import quote as quoteURL

# requests, apache2
import requests

# PyJWT, MIT, Jason Web Tokens, pip install PyJWT
import jwt
# cryptography, Apache License, Python Cryptography library, 
import cryptography
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# settings, , load and save settings, internal
import settings
# access_common, , things shared between different component access modules, internal
import access_common
# version, , represent versions and specifications, internal
import version
# Ordered JSON, , read & write json, internal
import ordered_json
# Github Access, , access repositories on github, internal
import github_access
# export key, , export pycrypto keys, internal
import exportkey

Registry_Base_URL = 'https://registry.yottabuild.org'
Registry_Auth_Audience = 'http://registry.yottabuild.org'
Website_Base_URL  = 'http://yottabuild.org'
_OpenSSH_Keyfile_Strip = re.compile(b"^(ssh-[a-z0-9]*\s+)|(\s+.+\@.+)|\n", re.MULTILINE)

logger = logging.getLogger('access')

# suppress logging from the requests library
logging.getLogger("requests").setLevel(logging.WARNING)

class AuthError(RuntimeError):
    pass

# Internal functions

def generate_jwt_token(private_key, registry=None):
    registry = registry or Registry_Base_URL    
    expires = calendar.timegm((datetime.datetime.utcnow() + datetime.timedelta(hours=2)).timetuple())
    prn = _fingerprint(private_key.public_key())
    logger.debug('fingerprint: %s' % prn)
    token_fields = {
        "iss": 'yotta',
        "aud": registry,
        "prn": prn,
        "exp": str(expires)
    }
    logger.debug('token fields: %s' % token_fields)
    private_key_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
    )
    token = jwt.encode(token_fields, private_key_pem, 'RS256').decode('ascii')
    logger.debug('encoded token: %s' % token)

    return token

def _pubkeyWireFormat(pubkey):
    pubk_numbers = pubkey.public_numbers()
    logger.debug('openssh format publickey:\n%s' % exportkey.openSSH(pubk_numbers))
    return quoteURL(_OpenSSH_Keyfile_Strip.sub(b'', exportkey.openSSH(pubk_numbers)))

def _fingerprint(pubkey):
    stripped = _OpenSSH_Keyfile_Strip.sub(b'', exportkey.openSSH(pubkey.public_numbers()))
    decoded  = base64.b64decode(stripped)
    khash    = hashlib.md5(decoded).hexdigest()
    return ':'.join([khash[i:i+2] for i in range(0, len(khash), 2)])


def _returnRequestError(fn):
    ''' Decorator that captures requests.exceptions.RequestException errors
        and returns them as an error message. If no error occurs the reture
        value of the wrapped function is returned (normally None). '''
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except requests.exceptions.RequestException as e:
            return "server returned status %s: %s" % (e.response.status_code, e.message)
    return wrapped
 
def _handleAuth(fn):
    ''' Decorator to re-try API calls after asking the user for authentication. '''
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == requests.codes.unauthorized:
                logger.debug('%s unauthorised', fn)
                github_access.authorizeUser()
                logger.debug('trying with authtoken: %s', settings.getProperty('github', 'authtoken'))
                return fn(*args, **kwargs)
            else:
                raise
    return wrapped

def _friendlyAuthError(fn):
    ''' Decorator to print a friendly you-are-not-authorised message. Use
        **outside** the _handleAuth decorator to only print the message after
        the user has been given a chance to login. '''
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == requests.codes.unauthorized:
                logger.error('insufficient permission')
                return None
            else:
                raise
    return wrapped

def _getPrivateRegistryKey():
    if 'YOTTA_PRIVATE_REGISTRY_API_KEY' in os.environ:
        return os.environ['YOTTA_PRIVATE_REGISTRY_API_KEY']
    return None

def _listVersions(namespace, name):
    sources = _getSources()

    registry_urls = [s['url'] for s in sources if 'type' in s and s['type'] == 'registry']

    # look in the public registry last
    registry_urls.append(Registry_Base_URL)

    versions = []

    for registry in registry_urls:
        # list versions of the package:
        url = '%s/%s/%s/versions' % (
            registry,
            namespace,
            name
        )
        
        request_headers = _headersForRegistry(registry)
        
        logger.debug("GET %s, %s", url, request_headers)
        response = requests.get(url, headers=request_headers)
        
        if response.status_code == 404:
            continue

        # raise any other HTTP errors
        response.raise_for_status()

        for x in ordered_json.loads(response.text):
            rtv = RegistryThingVersion(x, namespace, name, registry=registry)
            if not rtv in versions:
                versions.append(rtv)

    if not len(versions):
        raise access_common.Unavailable(
            ('%s does not exist in the %s registry. '+
            'Check that the name is correct, and that it has been published.') % (name, namespace)
        )

    return versions

def _tarballURL(namespace, name, version, registry=None):
    registry = registry or Registry_Base_URL    
    return '%s/%s/%s/versions/%s/tarball' % (
        registry, namespace, name, version
    )

def _getTarball(url, directory, sha256):
    logger.debug('registry: get: %s' % url)

    if not sha256:
        logger.warn('tarball %s has no hash to check' % url)
    
    # figure out which registry we're fetching this tarball from (if any) and
    # add appropriate headers
    registry = Registry_Base_URL

    for source in _getSources():
        if ('type' in source and source['type'] == 'registry' and
             'url' in source and url.startswith(source['url'])):
            registry = source['url']
            break

    request_headers = _headersForRegistry(registry)
    
    logger.debug('GET %s, %s', url, request_headers)
    response = requests.get(url, headers=request_headers, allow_redirects=True, stream=True)
    response.raise_for_status()

    return access_common.unpackTarballStream(response, directory, ('sha256', sha256))

def _getSources():
    sources = settings.get('sources')
    if sources is None:
        sources = []
    return sources

def _isPublicRegistry(registry):
    return (registry is None) or (registry == Registry_Base_URL)

def _friendlyRegistryName(registry):
    return registry

def _getPrivateKey(registry):
    if _isPublicRegistry(registry):
        return settings.getProperty('keys', 'private')
    else:
        for s in _getSources():
            if _sourceMatches(s, registry):
                if 'keys' in s and s['keys'] and 'private' in s['keys']:
                    return s['keys']['private']
        return None

def _sourceMatches(source, registry):
    return ('type' in source and source['type'] == 'registry' and
             'url' in source and source['url'] == registry)

def _generateAndSaveKeys(registry=None):
    registry = registry or Registry_Base_URL    
    k = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    privatekey_pem = k.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
    )

    pubkey_pem = k.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )

    if _isPublicRegistry(registry):
        settings.setProperty('keys', 'private', privatekey_pem)
        settings.setProperty('keys', 'public', pubkey_pem)
    else:
        sources = _getSources()
        keys = None
        for s in sources:
            if _sourceMatches(s, registry):
                if not 'keys' in s:
                    s['keys'] = dict()
                keys = s['keys']
                break
        if keys is None:
            keys = dict()
            sources.append({
               'type':'registry',
                'url':registry,
               'keys':keys
            })
        keys['private'] = privatekey_pem
        keys['public']  = pubkey_pem
        settings.set('sources', sources)
    return pubkey_pem, privatekey_pem

def _getPrivateKeyObject(registry=None):
    registry = registry or Registry_Base_URL
    privatekey_pem = _getPrivateKey(registry)
    if not privatekey_pem:
        pubkey_pem, privatekey_pem = _generateAndSaveKeys(registry)
    else:
        # settings are unicode, we should be able to safely decode to ascii for
        # the key though, as it will either be hex or PEM encoded:
        privatekey_pem = privatekey_pem.encode('ascii')
    # if the key doesn't look like PEM, it might be hex-encided-DER (which we
    # used historically), so try loading that:
    if '-----BEGIN PRIVATE KEY-----' in privatekey_pem:
        return serialization.load_pem_private_key(
            privatekey_pem, None, default_backend()
        )
    else:
        privatekey_der = binascii.unhexlify(privatekey_pem)
        return serialization.load_der_private_key(
            privatekey_der, None, default_backend()
        )


def _headersForRegistry(registry):
    registry = registry or Registry_Base_URL
    auth_token = generate_jwt_token(_getPrivateKeyObject(registry), registry)
    r = {
        'Authorization': 'Bearer %s' % auth_token
    }
    if registry == Registry_Base_URL:
        return r
    for s in _getSources():
        if _sourceMatches(s, registry):
            if 'apikey' in s:
                r['X-Api-Key'] = s['apikey']
                break
    return r

# API
class RegistryThingVersion(access_common.RemoteVersion):
    def __init__(self, data, namespace, name, registry=None):
        logger.debug('RegistryThingVersion %s/%s data: %s' % (namespace, name, data))
        version = data['version']
        self.namespace = namespace
        self.name      = name
        self.version   = version
        if 'hash' in data and 'sha256' in data['hash']:
            self.sha256 = data['hash']['sha256']
        else:
            self.sha256 = None
        url = _tarballURL(self.namespace, self.name, version, registry)
        super(RegistryThingVersion, self).__init__(
            version, url, name=name, friendly_source=_friendlyRegistryName(registry)
        )

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

@_handleAuth
def publish(namespace, name, version, description_file, tar_file, readme_file,
            readme_file_ext, registry=None):
    ''' Publish a tarblob to the registry, if the request fails, an exception
        is raised, which either triggers re-authentication, or is turned into a
        return value by the decorators. (If successful, the decorated function
        returns None)
    '''
    registry = registry or Registry_Base_URL    

    url = '%s/%s/%s/versions/%s' % (
        registry,
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
    body = OrderedDict([('metadata', (None, description_file.read(),'application/json')),
                        ('tarball',('tarball', tar_file)),
                        (readme_section_name, (readme_section_name, readme_file))])

    headers = _headersForRegistry(registry)
    
    response = requests.put(url, headers=headers, files=body)

    if not response.ok:
        return "server returned status %s: %s" % (response.status_code, response.text)

    return None

@_handleAuth
def unpublish(namespace, name, version, registry=None):
    ''' Try to unpublish a recently published version. Return any errors that
        occur.
    '''
    registry = registry or Registry_Base_URL    

    url = '%s/%s/%s/versions/%s' % (
        registry,
        namespace,
        name,
        version
    )
    
    headers = _headersForRegistry(registry)
    response = requests.delete(url, headers=headers)

    if not response.ok:
        return "server returned status %s: %s" % (response.status_code, response.text)

    return None

@_friendlyAuthError
@_handleAuth
def listOwners(namespace, name, registry=None):
    ''' List the owners of a module or target (owners are the people with
        permission to publish versions and add/remove the owners). 
    '''
    registry = registry or Registry_Base_URL
    
    url = '%s/%s/%s/owners' % (
        registry,
        namespace,
        name
    )

    request_headers = _headersForRegistry(registry)

    response = requests.get(url, headers=request_headers)

    if response.status_code == 404:
        logger.error('no such %s, "%s"' % (namespace[:-1], name))
        return []
    
    # raise exceptions for other errors - the auth decorators handle these and
    # re-try if appropriate
    response.raise_for_status()

    return ordered_json.loads(response.text)

@_friendlyAuthError
@_handleAuth
def addOwner(namespace, name, owner, registry=None):
    ''' Add an owner for a module or target (owners are the people with
        permission to publish versions and add/remove the owners). 
    '''
    registry = registry or Registry_Base_URL
    
    url = '%s/%s/%s/owners/%s' % (
        registry,
        namespace,
        name,
        owner
    )

    request_headers = _headersForRegistry(registry)

    response = requests.put(url, headers=request_headers)

    if response.status_code == 404:
        logger.error('no such %s, "%s"' % (namespace[:-1], name))
        return

    # raise exceptions for other errors - the auth decorators handle these and
    # re-try if appropriate
    response.raise_for_status()


@_friendlyAuthError
@_handleAuth
def removeOwner(namespace, name, owner, registry=None):
    ''' Remove an owner for a module or target (owners are the people with
        permission to publish versions and add/remove the owners). 
    '''
    registry = registry or Registry_Base_URL
    
    url = '%s/%s/%s/owners/%s' % (
        registry,
        namespace,
        name,
        owner
    )

    request_headers = _headersForRegistry(registry)

    response = requests.delete(url, headers=request_headers)

    if response.status_code == 404:
        logger.error('no such %s, "%s"' % (namespace[:-1], name))
        return

    # raise exceptions for other errors - the auth decorators handle these and
    # re-try if appropriate
    response.raise_for_status()


def search(query='', keywords=[], registry=None):
    ''' generator of objects returned by the search endpoint (both modules and
        targets).
        
        Query is a full-text search (description, name, keywords), keywords
        search only the module/target description keywords lists.
        
        If both parameters are specified the search is the intersection of the
        two queries.
    '''
    registry = registry or Registry_Base_URL

    url = '%s/search' % registry

    headers = _headersForRegistry(registry)

    params = {
         'skip': 0,
        'limit': 50
    }
    if len(query):
        params['query'] = query
    if len(keywords):
        params['keywords[]'] = keywords
    
    while True:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        objects = ordered_json.loads(response.text)
        if len(objects):
            for o in objects:
                yield o
            params['skip'] += params['limit']
        else:
            break
    

def deauthorize(registry=None):
    registry = registry or Registry_Base_URL
    if _isPublicRegistry(registry):
        if settings.get('keys'):
            settings.set('keys', dict())
    else:
        sources = [s for s in _getSources() if not _sourceMatches(s, registry)]
        settings.set('sources', sources)

def setAPIKey(registry, api_key):
    ''' Set the api key for accessing a registry. This is only necessary for
        development/test registries.
    '''
    if (registry is None) or (registry == Registry_Base_URL):
        return
    sources = _getSources()
    source = None
    for s in sources:
        if _sourceMatches(s, registry):
            source = s
    if source is None:
        source = {
           'type':'registry',
            'url':registry,
        }
        sources.append(source)
    source['apikey'] = api_key
    settings.set('sources', sources)


def getPublicKey(registry=None):
    ''' Return the user's public key (generating and saving a new key pair if necessary) '''
    registry = registry or Registry_Base_URL
    pubkey_pem = None
    if _isPublicRegistry(registry):
        pubkey_pem = settings.getProperty('keys', 'public')
    else:
        for s in _getSources():
            if _sourceMatches(s, registry):
                if 'keys' in s and s['keys'] and 'public' in s['keys']:
                    pubkey_pem = s['keys']['public']
                    break
    if not pubkey_pem:
        pubkey_pem, privatekey_pem = _generateAndSaveKeys()
    else:
        # settings are unicode, we should be able to safely decode to ascii for
        # the key though, as it will either be hex or PEM encoded:
        pubkey_pem = pubkey_pem.encode('ascii')
    # if the key doesn't look like PEM, it might be hex-encided-DER (which we
    # used historically), so try loading that:
    if '-----BEGIN PUBLIC KEY-----' in pubkey_pem:
        pubkey = serialization.load_pem_public_key(pubkey_pem, default_backend())
    else:
        pubkey_der = binascii.unhexlify(pubkey_pem)        
        pubkey = serialization.load_der_public_key(pubkey_der, default_backend())
    return _pubkeyWireFormat(pubkey)


def testLogin(registry=None):
    registry = registry or Registry_Base_URL    
    url = '%s/users/me' % (
        registry
    )

    request_headers = _headersForRegistry(registry)

    logger.debug('test login...')
    response = requests.get(url, headers=request_headers)
    response.raise_for_status()

def getAuthData(registry=None):
    ''' Poll the registry to get the result of a completed authentication
        (which, depending on the authentication the user chose or was directed
        to, will include a github or other access token)
    '''
    registry = registry or Registry_Base_URL
    url = '%s/tokens' % (
        registry
    )
    
    request_headers = _headersForRegistry(registry)

    logger.debug('poll for tokens... %s', request_headers)

    try:
        response = requests.get(url, headers=request_headers)
    except requests.RequestException as e:
        logger.debug(str(e))
        return None

    if response.status_code == requests.codes.unauthorized:
        logger.debug('Unauthorised')
        return None
    elif response.status_code == requests.codes.not_found:
        logger.debug('Not Found')
        return None

    body = response.text
    logger.debug('auth data response: %s' % body);
    r = {}

    parsed_response = ordered_json.loads(body)

    if 'error' in parsed_response:
        raise AuthError(parsed_response['error'])

    for token in parsed_response:
        if token['provider'] == 'github':
            r['github'] = token['accessToken']
            break

    logger.debug('parsed auth tokens %s' % r);
    return r

def getLoginURL(provider=None, registry=None):
    registry = registry or Registry_Base_URL
    if provider:
        query = '?provider=github'
    else:
        query = ''
    if not _isPublicRegistry(registry):
        if not len(query):
            query = '?'
        query += '&private=1'
    return  Website_Base_URL + '/' + query + '#login/' + getPublicKey(registry)

def openBrowserLogin(provider=None, registry=None):
    registry = registry or Registry_Base_URL    
    webbrowser.open(getLoginURL(provider=provider, registry=registry))
