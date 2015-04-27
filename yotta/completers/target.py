# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# argcomplete, pip install argcomplete, tab-completion for argparse, Apache-2
import argcomplete

def targetCompleter(prefix, action, parser, parsed_args):
    argcomplete.warn('targetCompleter executed')
    return ['moo']

