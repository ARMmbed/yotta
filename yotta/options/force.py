# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

def addTo(parser):
    parser.add_argument('-f', '--force', action='store_true', dest="force",
        help='Force the operation to (try to) continue even in situations which '+
             'would be an error.'
    )


