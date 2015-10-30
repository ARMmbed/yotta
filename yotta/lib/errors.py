# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# yotta's error handling utilities

# standard library modules, , ,
import sys

def _addExceptHook(fn):
    # standard library modules, , ,
    import functools
    previous_excepthook = sys.excepthook
    @functools.wraps(fn)
    def chainExceptHook(*args, **kwargs):
        fn(*args, **kwargs)
        return previous_excepthook(*args, **kwargs)
    sys.excepthook = chainExceptHook


def _yottaExceptHook(exc_type, exc_val, exc_tb):
    try:
        import pkg_resources
        sys.stderr.write('Fatal Exception, yotta=' + pkg_resources.require("yotta")[0].version + '\n')
    except Exception as e:
        sys.stderr.write('Fatal Exception, yotta=unknown\n')
_addExceptHook(_yottaExceptHook)
