# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# this module exists to share global config amongst modules

conf = {}

def set(name, value):
    global conf
    conf[name] = value

def get(name):
    global conf
    return conf[name]

