# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# !!! FIXME: on Windows, this creates a "yotta" directory under Program Files and
# links there. Needs to be fixed (how?)

# !!! FIXME: "PROGRAMFILES" env variable might exist only on Windows 7 and above.
# Needs testing on other Windows systems

# !!! FIXME: there are now multiple .py files that contain platform dependent
# code and conditions such as 'if os.name == "nt"' Ideally, all these platform
# dependent function would live in an OS abstraction module

# standard library modules, , ,
import os
# fsutils, , misc filesystem utils, internal
import fsutils

def prefix():
    if 'YOTTA_PREFIX' in os.environ:
        return os.environ['YOTTA_PREFIX']
    else:
        if os.name == 'nt':
            dirname = os.path.join(os.getenv("PROGRAMFILES"), "yotta")
            fsutils.mkDirP(dirname)
            return dirname
        else:
            return '/usr/local'

def globalInstallDirectory():
    if os.name == 'nt':
        return os.path.join(prefix(), 'yotta_modules')
    else:
        return os.path.join(prefix(), 'lib', 'yotta_modules')

def globalTargetInstallDirectory():
    if os.name == 'nt':
        return os.path.join(prefix(), 'yotta_targets')
    else:
        return os.path.join(prefix(), 'lib', 'yotta_targets')

