# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# !!! FIXME: this implementation uses NTFS junctions points:
# http://msdn.microsoft.com/en-gb/library/windows/desktop/aa365006%28v=vs.85%29.aspx
# These don't work when linking a non-local volume (for example a network share)
# If that'll be required in the future, symlinks (CreateSymbolicLink) must be used instead

# ntfsutils, 2-clause BSD, NTFS link handling, pip install ntfsutils
import ntfsutils.junction as junction #pylint: disable=import-error
import os

def dropRootPrivs(fn):
    ''' decorator to drop su/sudo privilages before running a function on
        unix/linux.

        ** on windows this function does nothing **
    '''
    def wrapper(*args, **kwargs):
        # !!! TODO: what can we do to de-priv on windows?
        return fn(*args, **kwargs)
    return wrapper

def isLink(path):
    return junction.isjunction(path)

def tryReadLink(path):
    try:
        prevPath, initialPath = path, path
        readlinkCount, maxReadlinkCount = 0, 100
        while isLink(path):
            path = junction.readlink(path)
            if path == prevPath: # no idea if this can happen, but why risk it
                break
            # Prevent infinite loop if circular paths are present (A->B->C->A)
            readlinkCount = readlinkCount + 1
            if readlinkCount == maxReadlinkCount:
                return initialPath
            prevPath = path
        return path
    except:
        return None

def _symlink(source, link_name):
    junction.create(source, link_name)

def realpath(path):
    return os.path.abspath(tryReadLink(path) or path)

def rmLink(path):
    # Apparently, it's possible to delete both directory links and file links
    # with 'rmdir' in Windows
    os.rmdir(path)
