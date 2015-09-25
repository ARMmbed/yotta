#!/usr/bin/env python
# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import unittest
import functools
import os
import re
import tempfile

# requests, apache2
import requests

# internal modules:
from yotta.lib.fsutils import rmRf
from . import cli

Test_Module_JSON = '''{
  "name": "testmod",
  "version": "0.0.0",
  "license": "apache-2.0"
}
'''

def loggedout(fn):
    # decorator to ensure that we're logged out before running a function
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        rmRf(os.path.join('tmp_yotta_settings', "config.json"))
        fn(*args, **kwargs)
    return wrapped

def loggedin(fn):
    # decorator to ensure that we're logged in before running a function
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        # get a login URL:
        stdout, stderr, status = cli.run(['--plain', '--noninteractive', 'login'])
        login_url_match = re.search(r'login URL: (http.*/#login/)(.*)(?:\n|$)', stdout+stderr)
        assert(login_url_match)
        login_url_data = login_url_match.group(2)
        # our yottatest user's mbed authn cookies >:)
        mbed_authn_cookies = {
            'sessionid_developer':'5ftqkn887r6ehdc2j1ffleql469p8jo8',
            'THEITFSID':'f245642ab2d86058ff738812baf64c7c',
            'compiler_version':'1.8.15.1'
        }
        session = requests.Session()
        # first load the login URL, so the registry knows about this
        # authentication flow:
        registry_response = session.get(
            'http://yottabuild.org/#login/' + login_url_data
        )
        assert(registry_response.status_code == 200)
        # now get the mbed login URL:
        registry_response = session.get(
            'https://registry.yottabuild.org/login/mbed?state='+login_url_data,
            cookies = mbed_authn_cookies,
            allow_redirects = False
        )
        assert(registry_response.status_code == 302)
        # the registry will return a redirect to the mbed Oauth page:
        oauth_ok_page = session.get(
            registry_response.headers['Location'],
            cookies = mbed_authn_cookies
        )
        #print('Oauth OK Page:\n' + str(oauth_ok_page.status_code) + ' ' +oauth_ok_page.url)
        oauth_ok_page.raise_for_status()
        # grab the CSRF token to post with the "OK":
        csrf_token_match = re.search(r'<input[^>]*name=["\']csrfmiddlewaretoken["\'][^>]*value=["\']([^"\']*)["\']', oauth_ok_page.text)
        assert(csrf_token_match)
        csrf_token = csrf_token_match.group(1)
        # post the "OK" to the oauth flow:
        post_data = {
         'csrfmiddlewaretoken':csrf_token,
                'redirect_uri':'https://registry.yottabuild.org/login/mbed/callback',
                       'scope':'read',
                   'client_id':'ZKq4UTea7PiIrsOQYt32iBVouLktjrlanj1yf8hV',
                       'state':login_url_data,
               'response_type':'code',
                       'allow':'Authorize'
        }
        response = session.post(
            r'https://developer.mbed.org/o/authorize/?response_type=code&redirect_uri=https%3A%2F%2Fregistry.yottabuild.org%2Flogin%2Fmbed%2Fcallback&scope=read&state='+login_url_data+r'&client_id=ZKq4UTea7PiIrsOQYt32iBVouLktjrlanj1yf8hV',
            data = post_data,
            headers = {
                'Referer': r'https://developer.mbed.org/o/authorize/?response_type=code&redirect_uri=https%3A%2F%2Fregistry.yottabuild.org%2Flogin%2Fmbed%2Fcallback&scope=read&state='+login_url_data+r'&client_id=ZKq4UTea7PiIrsOQYt32iBVouLktjrlanj1yf8hV'
            },
            cookies = mbed_authn_cookies
        )
        #print("DONE PAGE:\n" + str(response.status_code) + ' ' + response.url)
        response.raise_for_status()
        # run login one more time to fetch the token from the registry, then
        # we're logged in!
        stdout, stderr, status = cli.run(['--plain', '--noninteractive', 'login'])
        #print(stdout+stderr)
        # a non-interactive login returns status 0 when completing a previously
        # initiated login, if it returns nonzero then our login attempt above
        # failed for some reason
        assert(status == 0)
        return fn(*args, **kwargs)
    return wrapped

class TestCLIAccount(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp()
        with open(os.path.join(cls.test_dir, 'module.json'), 'w') as f:
            f.write(Test_Module_JSON)
        cls.saved_settings_dir = None
        # override the settings directory, so we don't clobber any actual
        # user's settings
        if 'YOTTA_USER_SETTINGS_DIR' in os.environ:
            cls.saved_settings_dir = os.environ['YOTTA_USER_SETTINGS_DIR']
        # use a directory called tmp_yotta_settings in the working directory:
        os.environ['YOTTA_USER_SETTINGS_DIR'] = 'tmp_yotta_settings'

    @classmethod
    def tearDownClass(cls):
        rmRf(cls.test_dir)
        cls.test_dir = None
        if cls.saved_settings_dir is not None:
            os.environ['YOTTA_USER_SETTINGS_DIR'] = cls.saved_settings_dir
            cls.saved_settings_dir = None
        else:
            del os.environ['YOTTA_USER_SETTINGS_DIR']

    @loggedout
    def test_logoutLoggedOut(self):
        # test logging out when already logged out: should be a no-op
        stdout, stderr, status = cli.run(['logout'])
        self.assertEqual(status, 0)
        # check that we're still logged out:
        stdout, stderr, status = cli.run(['whoami'])
        self.assertIn('not logged in', stdout+stderr)

    # !!! FIXME: adding a test for interactive login is somewhat difficult.
    # Non-interactive login is implicitly tested by all the @loggedin tests
    #@loggedout
    #def test_loginLoggedOut(self):
    #    # test logging in when logged out
    #    pass

    @loggedout
    def test_whoamiLoggedOut(self):
        # test whoami when loggedout
        stdout, stderr, status = cli.run(['whoami'])
        self.assertIn('not logged in', stdout+stderr)
        self.assertNotEqual(status, 0)

    # !!! FIXME: test login isn't currently working
    #@loggedin
    #def test_logoutLoggedIn(self):
    #    # test logging out when logged in
    #    stdout, stderr, status = cli.run(['logout'])
    #    self.assertEqual(status, 0)
    #    # test whoami is "not logged in":
    #    stdout, stderr, status = cli.run(['whoami'])
    #    self.assertIn('not logged in', stdout+stderr)
    #    # check that we can no longer do actions requiring auth:
    #    stdout, stderr, status = cli.run(['owners', 'ls', 'compiler-polyfill'])

    #@loggedin
    #def test_whoamiLoggedIn(self):
    #    # test whoami when logged in
    #    stdout, stderr, status = cli.run(['whoami'])
    #    self.assertNotIn('not logged in', stdout+stderr, )
    #    self.assertIn('yottatest', stdout+stderr)
    #    self.assertEqual(status, 0)
