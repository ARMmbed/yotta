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

# pycrypto, Public Domain, Python Crypto Library, pip install pyCRypto
import Crypto
from Crypto.Util.number import long_to_bytes


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


def openSSH(pubkey):
    e = long_to_bytes(pubkey.e)
    n = long_to_bytes(pubkey.n)

    if bord(e[0]) & 0x80:
        e = bchr(0) + e

    if bord(n[0]) & 0x80:
        n = bchr(0) + n

    key_bytes = b'ssh-rsa' + struct.pack('>I', len(e)) + e + struct.pack('>I', len(n)) + n

    return b'ssh-rsa ' + binascii.b2a_base64(key_bytes)[:-1]
