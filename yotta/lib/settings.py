# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import logging
import os
import errno
import threading
try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

# fsutils, , misc filesystem utils, internal
import fsutils

#
# yotta's settings always written to ~/.yotta/config, but are read, in order
# from:
#
#  1. environment variables (YOTTA_{config_section_name.upper()}_{config_variable_name.upper()})
#  2. ~/.yotta/config
#  3. /usr/local/etc/yottaconfig
#  4. /etc/yottaconfig.
#
# As soon as a value is found for a variable, the search is stopped.
#


# constants
user_ini_file = '~/.yotta/config'
ini_files     = [user_ini_file, '/usr/local/etc/yottaconfig', '/etc/yottaconfig']

# private state
parser = None
parser_lock = threading.Lock()

# private API
def _iniFiles():
    for x in ini_files:
        yield os.path.expanduser(x)

def _ensureParser():
    global parser
    with parser_lock:
        if not parser:
            parser = ConfigParser.RawConfigParser()
            parser.read(_iniFiles())

def _checkEnv(section, name):
    env_key = 'YOTTA_%s_%s' % (section.upper(), name.upper())
    try:
        return os.environ[env_key]
    except KeyError:
        return None

# public API
def getProperty(section, name):
    value = _checkEnv(section, name)
    if value:
        logging.debug('read property from environment: %s:%s', section, name)
        return value
    _ensureParser()
    try:
        with parser_lock:
            return parser.get(section, name)
    except ConfigParser.NoSectionError:
        return None
    except ConfigParser.NoOptionError:
        return None

def setProperty(section, name, value):
    logging.debug('setProperty: %s:%s %s:%s', type(name), name, type(value), value)
    # use a local parser instance so that we don't copy system-wide settings
    # into the user config file
    p = ConfigParser.RawConfigParser()
    full_ini_path = os.path.expanduser(user_ini_file)
    ini_directory = os.path.dirname(full_ini_path)
    fsutils.mkDirP(ini_directory)
    def saveTofile(f):
        p.readfp(f)
        f.seek(0)
        if not p.has_section(section):
            p.add_section(section)
        p.set(section, name, value)
        p.write(f)
        f.truncate()
    try:
        with open(full_ini_path, 'r+') as f:
            saveTofile(f)
    except IOError as e:
        # if the file didn't exist we can't open in r+, so open with w,
        # exclusively, and making sure to set the right permissions
        if e.errno == errno.ENOENT:
            fd = os.open(full_ini_path, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o0600)
            with os.fdopen(fd, 'w+') as f:
                saveTofile(f)
        else: 
            raise
    # also update the in-memory settings:
    with parser_lock:
        if parser is not None:
            if not parser.has_section(section):
                parser.add_section(section)
            parser.set(section, name, value)

