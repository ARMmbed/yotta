# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import logging
import os
import threading
from collections import OrderedDict

# fsutils, , misc filesystem utils, internal
import fsutils
# Ordered JSON, , read & write json, internal
import ordered_json
# folders, , get places to install things, internal
import folders

#
# yotta's settings always written to ~/.yotta/config.json, but are read, in
# order from:
#
#  1. environment variables (YOTTA_{section_name.upper()}_{variable_name.upper()})
#  2. ~/.yotta/config.json
#  3. /usr/local/etc/yottaconfig.json
#  4. /etc/yottaconfig.json
#
# As soon as a value is found for a variable, the search is stopped.
#
#

# constants
user_config_file = os.path.join(folders.userSettingsDirectory(), 'config.json')
dir_config_file  = os.path.join('.','.yotta.json')

config_files = [
    dir_config_file,
    user_config_file,
]
if os.name == 'nt':
    config_files += [
        os.path.expanduser(os.path.join(folders.prefix(),'yotta.json'))
    ]
else:
    config_files += [
        os.path.expanduser(os.path.join(folders.prefix(),'etc','yotta.json')),
        os.path.join('etc','yotta.json')
    ]


# private state
parser = None
parser_lock = threading.Lock()

# private API

# class for reading JSON config files,
class _JSONConfigParser(object):
    def __init__(self):
        self.configs = OrderedDict()

    def read(self, filenames):
        '''' Read a list of files. Their configuration values are merged, with
             preference to values from files earlier in the list.
        '''
        for fn in filenames:
            try:
                self.configs[fn] = ordered_json.load(fn)
            except IOError:
                self.configs[fn] = OrderedDict()

    def get(self, path):
        ''' return a configuration value

            usage:
                get('section.property')

            Note that currently array indexes are not supported. You must
            get the whole array.

            returns None if any path element or the property is missing
        '''
        path = _splitPath([path])
        for config in self.configs.values():
            cur = config
            for el in path:
                if el in cur:
                    cur = cur[el]
                else:
                    cur = None
                    break
            if cur is not None:
                return cur
        return None

    def set(self, path, value=None, filename=None):
        ''' Set a configuration value. If no filename is specified, the
            property is set in the first configuration file. Note that if a
            filename is specified and the property path is present in an
            earlier filename then set property will be hidden.

            usage:
                set('section.property', value='somevalue')

            Note that currently array indexes are not supported. You must
            set the whole array.
        '''
        if filename is None:
            config = self._firstConfig()[1]
        else:
            config = self.configs[filename]

        path = _splitPath([path])
        for el in path[:-1]:
            if el in config:
                config = config[el]
            else:
                config[el] = OrderedDict()
                config = config[el]
        config[path[-1]] = value

    def write(self, filename=None):
        if filename is None:
            filename, data = self._firstConfig()
        elif filename in self.configs:
            data = self.configs[filename]
        else:
            raise ValueError('No such file.')
        dirname = os.path.dirname(filename)
        fsutils.mkDirP(dirname)
        ordered_json.dump(filename, data)

    def _firstConfig(self):
        for fn, data in self.configs.items():
            return fn, data
        raise ValueError('No configs available.')

def _splitPath(path):
    r = []
    for p in path:
        r += p.split('.')
    if not len(p):
        raise ValueError('A path must be specified.')
    return r

def _ensureParser():
    global parser
    with parser_lock:
        if not parser:
            parser = _JSONConfigParser()
            parser.read(config_files)

def _checkEnv(path):
    env_key = '_'.join(['YOTTA'] + [x.upper() for x in _splitPath(path)])
    try:
        return os.environ[env_key]
    except KeyError:
        return None

# public API

def get(path):
    value = _checkEnv(path)
    if value:
        logging.debug('read property from environment: %s', path)
        return value
    _ensureParser()
    with parser_lock:
        return parser.get(path)

def getProperty(section, name):
    return get(section + '.' + name)

def set(path, value, save_locally=False):
    if save_locally:
        filename = dir_config_file
    else:
        filename = user_config_file

    logging.debug('setProperty: %s %s:%s', path, type(value), value)
    _ensureParser()
    with parser_lock:
        parser.set(path, value=value, filename=filename)
        parser.write(filename)

def setProperty(section, name, value, save_locally=False):
    set(section+'.'+name, value, save_locally)

