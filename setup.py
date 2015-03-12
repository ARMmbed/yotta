# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

import os
from setuptools import setup, find_packages

# Utility function to cat in a file (used for the README)
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

# On Windows, fix the version of PyCrypto dependency to 2.6, so we can use
# the binary installer from voidspace.org.uk (otherwise pip tries to install
# a newer pycrypto from PyPI). Also, we need 'ntfsutils' in Windows
if os.name == 'nt':
    platform_deps = ['ntfsutils>=0.1.3,<0.2']
    pycrypto_dep = 'PyCrypto==2.6'
else:
    platform_deps = []
    pycrypto_dep = 'PyCrypto>=2.5,<3'

setup(
    name = "yotta",
    version = "0.1.0",
    author = "James Crosby",
    author_email = "James.Crosby@arm.com",
    description = ("Re-usable components for embedded software."),
    license = "Apache-2.0",
    keywords = "embedded package module dependency management",
    url = "about:blank",
    packages=find_packages(),
    package_data={
        'yotta': ['lib/schema/*.json', 'lib/templates/*.txt']
    },
    long_description=read('readme.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: Apache Software License",
        "Environment :: Console",
    ],
    entry_points={
        "console_scripts": [
            "yotta=yotta:main",
               "yt=yotta:main",
        ],
    },
    test_suite = 'yotta.test',
    install_requires=[
        'semantic_version>=2.3.1,<3',
        'requests>=2.5,<3',
        'PyGithub>=1.25,<2',
        'colorama>=0.3,<0.4',
        'hgapi>=1.7,<2',
        'Jinja2>=2.7.0,<3',
        pycrypto_dep,
        'PyJWT>=0.3,<0.4',
        'pathlib>=1.0.1,<1.1',
        'jsonschema>=2.4.0,<3.0',
        'valinor>=0.0.0,<1.0'
    ] + platform_deps
)
