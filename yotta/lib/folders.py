# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# !!! FIXME: there are now multiple .py files that contain platform dependent
# code and conditions such as 'if os.name == "nt"' Ideally, all these platform
# dependent function would live in an OS abstraction module

# standard library modules, , ,
import os
import sys

def prefix():
    if 'YOTTA_PREFIX' in os.environ:
        return os.environ['YOTTA_PREFIX']
    else:
        # we only use sys.exec_prefix on windows, because on *nixes it might
        # well be /usr, and we don't want to create things in /usr/xxx
        if os.name == 'nt':
            return sys.exec_prefix
        else:
            return '/usr/local'

def userSettingsDirectory():
    if 'YOTTA_USER_SETTINGS_DIR' in os.environ:
        return os.environ['YOTTA_USER_SETTINGS_DIR']
    else:
        return os.path.expanduser('~/.yotta')

def globalInstallDirectory():
    if os.name == 'nt':
        return os.path.join(prefix(), 'Lib', 'yotta_modules')
    else:
        return os.path.join(prefix(), 'lib', 'yotta_modules')

def globalTargetInstallDirectory():
    if os.name == 'nt':
        return os.path.join(prefix(), 'Lib', 'yotta_targets')
    else:
        return os.path.join(prefix(), 'lib', 'yotta_targets')
