# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import logging
import sys
import os
import datetime
import time
import webbrowser

# colorama, BSD 3-Clause license, cross-platform terminal colours, pip install colorama
import colorama

# Registry Access, , access packages in the registry, internal
import registry_access
# settings, , load and save settings, internal
import settings
# globalconf, share global arguments between modules, internal
import yotta.lib.globalconf as globalconf

logger = logging.getLogger('access')

class AuthException(Exception):
    pass

class AuthTimedOut(AuthException):
    pass

def _pollForAuth(registry=None):
    tokens = registry_access.getAuthData(registry=registry)
    if tokens:
        if 'github' in tokens:
            settings.setProperty('github', 'authtoken', tokens['github'])
        if 'mbed' in tokens:
            settings.setProperty('mbed', 'authtoken', tokens['mbed'])
        return True
    return False


def _openBrowserLogin(provider=None, registry=None):
    webbrowser.open(registry_access.getLoginURL(provider=provider, registry=registry))

def authorizeUser(registry=None, provider='github', interactive=True):
    if not globalconf.get('plain'):
        DIM    = colorama.Style.DIM    #pylint: disable=no-member
        BRIGHT = colorama.Style.BRIGHT #pylint: disable=no-member
        NORMAL = colorama.Style.NORMAL #pylint: disable=no-member
    else:
        DIM = BRIGHT = NORMAL = u''

    # poll once with any existing public key, just in case a previous login
    # attempt was interrupted after it completed
    try:
        if _pollForAuth(registry=registry):
            return 0
    except registry_access.AuthError as e:
        logger.error('%s' % e)
        return 1

    # python 2 + 3 compatibility
    try:
        global input
        input = raw_input
    except NameError:
        pass

    if interactive:
        login_instruction = '\nYou need to log in to do this.\n'
        if provider == 'github':
            login_instruction = '\nYou need to log in with Github to do this.\n'

        sys.stdout.write(login_instruction)

        if os.name == 'nt' or os.environ.get('DISPLAY'):
            input(
                BRIGHT+
                'Press enter to continue.\n'+
                DIM+
                'Your browser will open to complete login.'+
                NORMAL+'\n'
            )

            _openBrowserLogin(provider=provider, registry=registry)

            sys.stdout.write('waiting for response...')
            sys.stdout.write(
                DIM+
                '\nIf you are unable to use a browser on this machine, please copy and '+
                'paste this URL into a browser:\n'+
                registry_access.getLoginURL(provider=provider, registry=registry)+'\n'+
                NORMAL
            )
            sys.stdout.flush()
        else:
            sys.stdout.write(
                '\nyotta is unable to open a browser for you to complete login '+
                'on this machine. Please copy and paste this URL into a '
                'browser to complete login:\n'+
                registry_access.getLoginURL(provider=provider, registry=registry)+'\n'
            )
            sys.stdout.write('waiting for response...')
            sys.stdout.flush()

        poll_start = datetime.datetime.utcnow()
        while datetime.datetime.utcnow() - poll_start < datetime.timedelta(minutes=5):
            time.sleep(5)
            sys.stdout.write('.')
            sys.stdout.flush()
            try:
                if _pollForAuth(registry=registry):
                    sys.stdout.write('\n')
                    return 0
            except registry_access.AuthError as e:
                logger.error('%s' % e)
                return 1
        raise AuthTimedOut('timed out: please try again.')

    else:
        logger.error('login required (yotta is running in noninteractive mode)')
        logger.info('login URL: %s', registry_access.getLoginURL(provider=provider, registry=registry))
        return 1



