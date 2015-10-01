# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# re-implementation of the pycrypto exportKey method for openSSH, to work
# around python 3 bug

# standard library modules
import struct
import binascii
import sys

if sys.version_info[0] == 3:
    def bord(x):
        return x
    def bchr(x):
        return bytes([x])

elif sys.version_info[0] == 2:
    def bord(x):
        return ord(x)
    def bchr(x):
        return chr(x)

# long_to_bytes: from PyCrypto,public domain, a vailable at:
# https://github.com/dlitz/pycrypto/blob/7acba5f3a6ff10f1424c309d0d34d2b713233019/lib/Crypto/Util/number.py
def long_to_bytes(n, blocksize=0):
    """long_to_bytes(n:long, blocksize:int) : string
    Convert a long integer to a byte string.

    If optional blocksize is given and greater than zero, pad the front of the
    byte string with binary zeros so that the length is a multiple of
    blocksize.
    """
    # after much testing, this algorithm was deemed to be the fastest
    s = b''
    n = int(n)
    pack = struct.pack
    while n > 0:
        s = pack('>I', n & 0xffffffff) + s
        n = n >> 32
    # strip off leading zeros
    for i in range(len(s)):
        if s[i] != '\000':
            break
    else:
        # only happens when n == 0
        s = '\000'
        i = 0
    s = s[i:]
    # add back some pad bytes.  this could be done more efficiently w.r.t. the
    # de-padding being done above, but sigh...
    if blocksize > 0 and len(s) % blocksize:
        s = (blocksize - len(s) % blocksize) * '\000' + s
    return s

def openSSH(pubkey):
    e = long_to_bytes(pubkey.e)
    n = long_to_bytes(pubkey.n)

    if bord(e[0]) & 0x80:
        e = bchr(0) + e

    if bord(n[0]) & 0x80:
        n = bchr(0) + n

    key_bytes = b'ssh-rsa' + struct.pack('>I', len(e)) + e + struct.pack('>I', len(n)) + n

    return b'ssh-rsa ' + binascii.b2a_base64(key_bytes)[:-1]
