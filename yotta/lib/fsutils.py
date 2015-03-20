# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import os
import errno
import shutil
import platform
import stat

def mkDirP(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def rmF(path):
    try:
        os.remove(path)
    except OSError as exception: 
        if exception.errno != errno.ENOENT:
            raise

def rmRf(path):
    # we may have to make files writable before we can successfully delete
    # them, to do this
    def fixPermissions(fn, path, excinfo):
        if os.access(path, os.W_OK):
            raise
        else:
            os.chmod(path, stat.S_IWUSR)
            fn(path)
    try:
        shutil.rmtree(path, onerror=fixPermissions)
    except OSError as exception:
        if 'cannot call rmtree on a symbolic link' in str(exception).lower():
            os.unlink(path)
        elif exception.errno == errno.ENOTDIR:
            rmF(path)
        elif exception.errno != errno.ENOENT:
            raise

def fullySplitPath(path):
    components = []
    while True:
        path, component = os.path.split(path)
        if component != '':
            components.append(component)
        else:
            if path != '':
                components.append(path)
            break
    components.reverse()
    return components

# The link-related functions are platform-dependent
links = __import__("fsutils_win" if os.name == 'nt' else "fsutils_posix", globals(), locals(), ['*'])
isLink = links.isLink
tryReadLink = links.tryReadLink
_symlink = links._symlink
realpath = links.realpath

# !!! FIXME: the logic in the "except" block below probably doesn't work in Windows
def symlink(source, link_name):
    try:
        # os.symlink doesn't update existing links, so need to rm first
        rmF(link_name)
        _symlink(source, link_name)
    except OSError as exception:
        if exception.errno != errno.EEXIST and (tryReadLink(link_name) != source):
            raise
