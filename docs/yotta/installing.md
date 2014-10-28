---
layout: default
title: Installing Yotta
section: yotta/installing
---

# Installing
yotta is distributed as a pip module, which can be installed with python's pip tool:

First download the latest [release tarball](https://github.com/ARMmbed/yotta/releases), then:

``` bash
sudo pip install -U setuptools
sudo pip install ./path/to/yotta-a.b.c.tar.gz
```
You may need to [install pip](http://pip.readthedocs.org/en/latest/installing.html), if you do not already have it.


### Other dependencies
Yotta also requires:

 * [CMake](http://www.cmake.org), on OS X this can be installed with [homebrew](http://brew.sh), and on linux via the system's package manager.
 * Your system's compiler (gcc or clang.) If you're cross-compiling using a target description, then the target will have its own requirements for an installed compiler.


### Solving Installation problems

On OS X, if you get an unknown argument error from Clang, it means some of yotta's dependencies have not yet been updated to support Xcode 5.1. Insert `ARCHFLAGS=-Wno-error=unused-command-line-argument-hard-error-in-future` between `sudo` and `pip` above.


