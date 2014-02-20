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
