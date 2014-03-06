# standard library modules, , ,
import logging
import json
import getpass
import os
import re
import functools

# settings, , load and save settings, internal
import settings
# version, , represent versions and specifications, internal
import version
# access_common, , things shared between different component access modules, internal
import access_common
# connection_pool, , shared connection pool, internal
import connection_pool

# restkit, MIT, HTTP client library for RESTful APIs, pip install restkit
from restkit import Resource, BasicAuth, Connection, request

# PyGithub, LGPL, Python library for Github API v3, pip install PyGithub
import github
from github import Github

# Constants
_github_url = 'https://api.github.com'


## NOTE
## It may be tempting to re-use resources (like Github instances) between
## functions below, however it must be possible to call these functions in
## parallel, so they must not share resources that are stateful and do not
## maintain their state in a threadsafe way

# Internal functions

def _userAuthorized():
    return settings.getProperty('github', 'user') and \
           settings.getProperty('github', 'authtoken')
 
def _handleAuth(fn):
    ''' Decorator to re-try API calls after asking the user for authentication. '''
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except github.BadCredentialsException:
            authorizeUser()
            logging.debug('trying with authtoken:', settings.getProperty('github', 'authtoken'))
            return fn(*args, **kwargs)
        except github.UnknownObjectException:
            # some endpoints return 404 if the user doesn't have access, maybe
            # it would be better to prompt for another username and password,
            # and store multiple tokens that we can try for each request....
            # but for now we assume that if the user is logged in then a 404
            # really is a 404
            if not _userAuthorized():
                authorizeUser()
                return fn(*args, **kwargs)
            else:
                raise
    return wrapped

@_handleAuth
def _getTags(repo):
    ''' return a dictionary of {tag: tarball_url}'''
    g = Github(settings.getProperty('github', 'authtoken'))
    #print 'get repo:', repo
    repo = g.get_repo(repo)
    tags = repo.get_tags()
    return {t.name: t.tarball_url for t in tags}

@_handleAuth
def _getTipArchiveURL(repo):
    ''' return a string containing a tarball url '''
    g = Github(settings.getProperty('github', 'authtoken'))
    repo = g.get_repo(repo)
    return repo.get_archive_link('tarball')

    
@_handleAuth
def _getTarball(url, into_directory):
    '''unpack the specified tarball url into the specified directory'''
    resource = Resource(url, pool=connection_pool.getPool(), follow_redirect=True)
    response = resource.get(
        headers = {'Authorization': 'token ' + settings.getProperty('github', 'authtoken')}, 
    )
    logging.debug('getting file: %s', url)
    # TODO: there's an MD5 in the response headers, verify it
    access_common.unpackTarballStream(response.body_stream(), into_directory)


# API
def authorizeUser():
    # using basic auth request an access token, then save it so that we don't
    # have to repeatedly ask for basic authentication credentials

    # !!! FIXME: if we already have a github authtoken, but it isn't working,
    # then we should try to delete it before creating a new one (we're limited
    # to 5 concurrent tokens per app), just in case the error wasn't that the
    # authorisation had been revoked/expired
    # !!! FIXME-also: could just get /authorizations, and re-use an existing
    # token

    user = settings.getProperty('github', 'user')
    if not user:
        user = raw_input('enter your github username:')
        settings.setProperty('github', 'user', user)

    auth = BasicAuth(user, getpass.getpass('Enter the password for github user %s:' % user))

    request_data = {
        'scopes': ['repo'],
          'note': 'yotta'
    }
    resource = Resource(_github_url + '/authorizations', pool=connection_pool.getPool(), filters=[auth])
    response = resource.post(
        headers = {'Content-Type': 'application/json'}, 
        payload = json.dumps(request_data)
    )
    token = json.loads(response.body_string())['token']
    settings.setProperty('github', 'authtoken', token)


class GithubComponentVersion(access_common.RemoteVersion):
    def unpackInto(self, directory):
        assert(self.url)
        _getTarball(self.url, directory)

class GithubComponent(access_common.RemoteComponent):
    def __init__(self, repo, version_spec=''):
        self.repo = repo
        self.spec = version.Spec(version_spec)
    
    @classmethod
    def createFromNameAndSpec(cls, url, name=None):    
        ''' returns a github component for any github url (including
            git+ssh:// git+http:// etc. or None if this is not a Github URL.
            For all of these we use the github api to grab a tarball, because
            that's faster.

            Normally version will be empty, unless the original url was of the
            form: 'owner/repo @version' or 'url://...#version', which can be used
            to grab a particular tagged version.

            (Note that for github components we ignore the package name, and
             just test to see if the "spec" looks like one of the supported URI
             schemes)
        '''
        # owner/package [@1.2.3] format
        url = url.strip()
        m = re.match('([^/\s]*/[^/\s]*) *@?([><=.0-9a-zA-Z\*-]*)', url)
        if m:
            return GithubComponent(*m.groups())
        # something://[anything.|anything@]github.com/owner/package[#1.2.3] format
        m = re.match('[^:/]*://(?:[^:/]*\.|[^:/]*@)?github\.com/([^/]*/[^/#]*)#?([><=.0-9a-zA-Z\*-]*)', url)
        if m:
            return GithubComponent(*m.groups())
        return None

    def versionSpec(self):
        return self.spec

    def availableVersions(self):
        ''' return a list of Version objects, each with a tarball URL set '''
        try:
            return [GithubComponentVersion(t[0], url=t[1]) for t in _getTags(self.repo).iteritems()]
        except github.UnknownObjectException, e:
            raise access_common.ComponentUnavailable(
                'could not locate github component "%s", either the name is misspelt, you do not have access to it, or it does not exist' % self.repo
            )

    def tipVersion(self):
        return GithubComponentVersion('', _getTipArchiveURL(self.repo))
    
