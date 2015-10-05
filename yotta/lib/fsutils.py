# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import os
import errno
import shutil
import stat

def mkDirP(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def rmF(path):
    try:
        if isLink(path):
            rmLink(path)
        else:
            os.remove(path)
    except OSError as exception:
        if exception.errno != errno.ENOENT:
            raise

def _rmRfNoRetry(path):
    # we may have to make files writable before we can successfully delete
    # them, to do this
    def fixPermissions(fn, path, excinfo):
        if os.access(path, os.W_OK):
            raise
        else:
            os.chmod(path, stat.S_IWUSR)
            fn(path)
    try:
        if isLink(path):
            rmLink(path)
        elif os.path.isfile(path):
            rmF(path)
        else:
            shutil.rmtree(path, onerror=fixPermissions)
    except OSError as exception:
        if exception.errno == errno.ENOTDIR:
            rmF(path)
        elif exception.errno != errno.ENOENT:
            raise

def rmRf(path):
    # on windows, it seems that various system processes (antivirus, search
    # indexing, and possibly other things) seem to keep files "open" after
    # python has closed them, preventing them from being removed if we
    # later (in the same process) try to remove them ...
    for x in range(0, 100):
        try:
            _rmRfNoRetry(path)
            break
        # ... ultimately leading to this error ...
        except WindowsError as e: #pylint: disable=undefined-variable
            if e.errno != 145: # != Directory not empty
                raise
            # ... trying again should fix the problem


def fullySplitPath(path):
    components = []
    while True:
        part, component = os.path.split(path)
        if part == path:
            # absolute path
            components.append(part)
            break
        elif component == path:
            components.append(component)
            break
        else:
            components.append(component)
            path = part
    components.reverse()
    return components

# Some functions are platform-dependent
_platform_dep = __import__("fsutils_win" if os.name == 'nt' else "fsutils_posix", globals(), locals(), ['*'])
isLink = _platform_dep.isLink
tryReadLink = _platform_dep.tryReadLink
_symlink = _platform_dep._symlink
realpath = _platform_dep.realpath
dropRootPrivs = _platform_dep.dropRootPrivs
rmLink = _platform_dep.rmLink

# !!! FIXME: the logic in the "except" block below probably doesn't work in Windows
def symlink(source, link_name):
    try:
        # os.symlink doesn't update existing links, so need to rm first
        rmF(link_name)
        _symlink(source, link_name)
    except OSError as exception:
        if exception.errno != errno.EEXIST and (tryReadLink(link_name) != source):
            raise
