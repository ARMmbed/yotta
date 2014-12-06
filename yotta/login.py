# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# Github Access, , access repositories on github, internal
from .lib import github_access

def addOptions(parser):
    pass

def execCommand(args, following_args):
    github_access.authorizeUser()

