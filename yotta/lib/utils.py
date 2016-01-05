# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# utility function to indicate whether the current item is the last one in a
# generator
def islast(generator):
    ''' indicate whether the current item is the last one in a generator
    '''
    next_x = None
    first = True
    for x in generator:
        if not first:
            yield (next_x, False)
        next_x = x
        first = False
    if not first:
        yield (next_x, True)
