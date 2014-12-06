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
from .lib import fsutils

def globalInstallDirectory():
    if os.name == 'nt':
        dirname = os.path.join(os.getenv("PROGRAMFILES"), "yotta", "yotta_modules")
        fsutils.mkDirP(dirname)
        return dirname
    else:
        return '/usr/local/lib/yotta_modules'

def globalTargetInstallDirectory():
    if os.name == 'nt':
        dirname = os.path.join(os.getenv("PROGRAMFILES"), "yotta", "yotta_targets")
        fsutils.mkDirP(dirname)
        return dirname
    else:
        return '/usr/local/lib/yotta_targets'

