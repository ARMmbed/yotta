# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# override re.compile so that it doesn't actually do any compilation until the
# regex is first used. Many, many modules compile regexes when they are
# imported, even if these are only needed for a subset of the module's
# functionality, so this can significantly speed up importing modules:

import re

_original_re_compile = re.compile

class ReCompileProxy(object):
    def __init__(self, *args, **kwargs):
        self._args     = args
        self._kwargs   = kwargs
        self._real_obj = None

    def __getattribute__(self, name):
        if object.__getattribute__(self, '_real_obj') is None:
            self._real_obj = _original_re_compile(
                 *object.__getattribute__(self,'_args'),
                **object.__getattribute__(self,'_kwargs')
            )
            self._args   = None
            self._kwargs = None
        return getattr(object.__getattribute__(self, '_real_obj'), name)

def overrideRECompile(*args, **kwargs):
    return ReCompileProxy(*args, **kwargs)

re.compile = overrideRECompile

