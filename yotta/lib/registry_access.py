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

# Internal functions

def generate_jwt_token(private_key):
    expires = calendar.timegm((datetime.datetime.utcnow() + datetime.timedelta(hours=2)).timetuple())
    prn = _fingerprint(private_key.public_key())
    logger.debug('fingerprint: %s' % prn)
    token_fields = {
        "iss": 'yotta',
        "aud": Registry_Auth_Audience,
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


def _registryAuthFilter():
    # basic auth until we release publicly, to prevent outside registry access,
    # after that this will be removed
    return  _BearerJWTFilter(_getPrivateKeyObject())

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
                github_access.authorizeUser()
                logger.debug('trying with authtoken:', settings.getProperty('github', 'authtoken'))
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

def _listVersions(namespace, name):
    # list versions of the package:
    url = '%s/%s/%s/versions' % (
        Registry_Base_URL,
        namespace,
        name
    )
    auth_token = generate_jwt_token(_getPrivateKeyObject())

    request_headers = {
        'Authorization': 'Bearer %s' % auth_token
    }

    response = requests.get(url, headers=request_headers)
    
    if response.status_code == 404:
        raise access_common.ComponentUnavailable(
            ('%s does not exist in the %s registry. '+
            'Check that the name is correct, and that it has been published.') % (name, namespace)
        )

    # raise any other HTTP errors
    response.raise_for_status()

    return [RegistryThingVersion(x, namespace, name) for x in ordered_json.loads(response.text)]

def _tarballURL(namespace, name, version):
    return '%s/%s/%s/versions/%s/tarball' % (
        Registry_Base_URL, namespace, name, version
    )

def _getTarball(url, directory, sha256):
    logger.debug('registry: get: %s' % url)

    if not sha256:
        logger.warn('tarball %s has no hash to check' % url)

    auth_token = generate_jwt_token(_getPrivateKeyObject())

    request_headers = {
        'Authorization': 'Bearer %s' % auth_token
    }

    response = requests.get(url, headers=request_headers, allow_redirects=True, stream=True)
    response.raise_for_status()

    return access_common.unpackTarballStream(response, directory, ('sha256', sha256))

def _generateAndSaveKeys():
    k = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    privatekey_pem = k.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
    )
    settings.setProperty('keys', 'private', privatekey_pem)

    pubkey_pem = k.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )
    settings.setProperty('keys', 'public', pubkey_pem)
    return pubkey_pem, privatekey_pem

def _getPrivateKeyObject():
    privatekey_pem =  settings.getProperty('keys', 'private')
    if not privatekey_pem:
        pubkey_pem, privatekey_pem = _generateAndSaveKeys()
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
    body = OrderedDict([('metadata', (None, description_file.read(),'application/json')),
                        ('tarball',('tarball', tar_file)),
                        (readme_section_name, (readme_section_name, readme_file))])
    headers = {}
    
    headers['Authorization'] = 'Bearer %s' % generate_jwt_token(_getPrivateKeyObject())
    response = requests.put(url, headers=headers, files=body)

    if not response.ok:
        return "server returned status %s: %s" % (response.status_code, response.text)

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

    auth_token = generate_jwt_token(_getPrivateKeyObject())

    request_headers = {
        'Authorization': 'Bearer %s' % auth_token
    }

    response = requests.get(url, headers=request_headers)

    if response.status_code == 404:
        logger.error('no such %s, "%s"' % (namespace[:-1], name))
        return None
    
    # raise exceptions for other errors - the auth decorators handle these and
    # re-try if appropriate
    response.raise_for_status()

    return ordered_json.loads(response.text)


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

    auth_token = generate_jwt_token(_getPrivateKeyObject())

    request_headers = {
        'Authorization': 'Bearer %s' % auth_token
    }

    response = requests.put(url, headers=request_headers)

    if response.status_code == 404:
        logger.error('no such %s, "%s"' % (namespace[:-1], name))
        return

    # raise exceptions for other errors - the auth decorators handle these and
    # re-try if appropriate
    response.raise_for_status()


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

    auth_token = generate_jwt_token(_getPrivateKeyObject())

    request_headers = {
        'Authorization': 'Bearer %s' % auth_token
    }

    response = requests.delete(url, headers=request_headers)

    if response.status_code == 404:
        logger.error('no such %s, "%s"' % (namespace[:-1], name))
        return

    # raise exceptions for other errors - the auth decorators handle these and
    # re-try if appropriate
    response.raise_for_status()


def search(query='', keywords=[]):
    ''' generator of objects returned by the search endpoint (both modules and
        targets).
        
        Query is a full-text search (description, name, keywords), keywords
        search only the module/target description keywords lists.
        
        If both parameters are specified the search is the intersection of the
        two queries.
    '''

    url = '%s/search' % Registry_Base_URL
    params = {
         'skip': 0,
        'limit': 50
    }
    if len(query):
        params['query'] = query
    if len(keywords):
        params['keywords[]'] = keywords
    
    while True:
        response = requests.get(url, params=params)
        response.raise_for_status()
        objects = ordered_json.loads(response.text)
        if len(objects):
            for o in objects:
                yield o
            params['skip'] += params['limit']
        else:
            break
    

def deauthorize():
    if settings.getProperty('keys', 'private'):
        settings.setProperty('keys', 'private', '')
    if settings.getProperty('keys', 'public'):
        settings.setProperty('keys', 'public', '')

def getPublicKey():
    ''' Return the user's public key (generating and saving a new key pair if necessary) '''
    pubkey_pem = settings.getProperty('keys', 'public')
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


def testLogin():
    url = '%s/users/me' % (
        Registry_Base_URL
    )

    auth_token = generate_jwt_token(_getPrivateKeyObject())

    request_headers = {
        'Authorization': 'Bearer %s' % auth_token
    }

    logger.debug('test login...')
    response = requests.get(url, headers=request_headers)
    response.raise_for_status()

def getAuthData():
    ''' Poll the registry to get the result of a completed authentication
        (which, depending on the authentication the user chose or was directed
        to, will include a github or other access token)
    '''
    url = '%s/tokens' % (
        Registry_Base_URL
    )
    headers = {}

    auth_token = generate_jwt_token(_getPrivateKeyObject())

    request_headers = {
        'Authorization': 'Bearer %s' % auth_token
    }

    logger.debug('poll for tokens...')

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

    json_body = ordered_json.loads(body)

    if 'error' in json_body:
        raise Exception(json_body['error'])

    for token in json_body:
        if token['provider'] == 'github':
            r['github'] = token['accessToken']
            break

    logger.debug('parsed auth tokens %s' % r);
    return r

def getLoginURL(provider=None):
    if provider:
        query = '?provider=github'
    else:
        query = ''
    return  Website_Base_URL + '/#login/' + getPublicKey() + query

def openBrowserLogin(provider=None):
    webbrowser.open(getLoginURL(provider=provider))
