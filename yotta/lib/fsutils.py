# standard library modules, , ,
import os
import errno

def mkDirP(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
