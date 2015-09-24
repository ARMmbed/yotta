# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import os
import pwd
import multiprocessing
import logging
import sys
import traceback

def _getNobodyPidGid():
    entry = pwd.getpwnam('nobody')
    return (entry.pw_uid, entry.pw_gid)


def _dropPrivsReturnViaQueue(q, fn, args, kwargs):
    running_as_root = (os.geteuid() == 0)
    if running_as_root:
        nobody_uid, nobody_gid = _getNobodyPidGid()
        if os.environ.get('SUDO_UID', None) is not None:
            logging.debug('drop SUDO -> %s', os.environ['SUDO_UID'])
        else:
            logging.debug('drop SU -> nobody')
        os.setgid(int(os.environ.get('SUDO_GID', nobody_gid)))
        os.setgid(int(os.environ.get('SUDO_UID', nobody_uid)))
    try:
        logging.debug('run wrapped function...')
        try:
            r = fn(*args, **kwargs)
        except KeyboardInterrupt:
            logging.warning('child interrupted')
            return
        logging.debug('wrapped function completed...')
        q.put(('return', r))
    except Exception as e:
        logging.debug('exception in wrapped function: %s', traceback.format_exc())
        # the exception info isn't pickleable, so this is the best we can do
        e_type, e_message, e_traceback = sys.exc_info()
        q.put(('exception', e_type, e_message))
    finally:
        q.put(('finish',))

def dropRootPrivs(fn):
    ''' decorator to drop su/sudo privilages before running a function on
        unix/linux.
        The *real* uid is modified, so privileges are permanently dropped for
        the process. (i.e. make sure you don't need to do

        If there is a SUDO_UID environment variable, then we drop to that,
        otherwise we drop to nobody.
    '''

    def wrapped_fn(*args, **kwargs):
        q = multiprocessing.Queue()
        p = multiprocessing.Process(target=_dropPrivsReturnViaQueue, args=(q, fn, args, kwargs))
        p.start()

        r = None
        e = None
        while True:
            msg = q.get()
            if msg[0] == 'return':
                r = msg[1]
            if msg[0] == 'exception':
                e = msg[1](msg[2])
            if msg[0] == 'finish':
                # if the command raised an exception, propagate this:
                if e is not None:
                    raise e #pylint: disable=raising-bad-type
                return r

    return wrapped_fn

def isLink(path):
    return os.path.islink(path)

def tryReadLink(path):
    try:
        return os.readlink(path)
    except OSError as e:
        return None

def _symlink(source, link_name):
    os.symlink(source, link_name)

def realpath(path):
    return os.path.realpath(path)

def rmLink(path):
    os.unlink(path)
