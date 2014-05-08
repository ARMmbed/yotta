# standard library modules, , ,
import os
import errno
import shutil

def mkDirP(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def rmRf(path):
    try:
        shutil.rmtree(path)
    except OSError as exception:
        if 'cannot call rmtree on a symbolic link' in str(exception).lower():
            os.unlink(path)
        elif exception.errno != errno.ENOENT:
            raise

def rmF(path):
    try:
        os.remove(path)
    except OSError as exception: 
        if exception.errno != errno.ENOENT:
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

def isLink(path):
    # !!! FIXME: when windows symlinks are supported this check needs to
    # support them too
    return os.path.islink(path)

def symlink(src, dst):
    # !!! FIXME: recent windowses do support symlinks, but os.symlink doesn't
    # work on windows, so use something else
    try:
        os.symlink(src, dst)
    except OSError as exception:
        if exception.errno != errno.EEXIST and (os.readlink(dst) != src):
            raise
