# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import platform
import sys

# settings, , load and save settings, internal
import settings

def defaultTarget(ignore_set_target=False):
    set_target = settings.getProperty('build', 'target')
    if set_target:
        return set_target
    else:
        return systemDefaultTarget()

def systemDefaultTarget():
    machine = platform.machine()

    x86 = machine.find('86') != -1
    arm = machine.find('arm') != -1 or machine.find('aarch') != -1

    prefix = "x86-" if x86 else "arm-" if arm else ""
    platf = 'unknown'

    if sys.platform.startswith('linux'):
        platf = 'linux-native'
    elif sys.platform == 'darwin':
        platf = 'osx-native'
    elif sys.platform.find('win') != -1:
        platf = 'win'
    return prefix + platf + ','


