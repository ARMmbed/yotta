# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

def globalInstallDirectory():
    # !!! FIXME: windows support: we should really install to the same prefix
    # that yotta binary is installed under
    return '/usr/local/lib/yotta_modules'

def globalTargetInstallDirectory():
    # !!! FIXME: windows support: we should really install to the same prefix
    # that yotta binary is installed under
    return '/usr/local/lib/yotta_targets'

