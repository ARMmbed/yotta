---
layout: default
title: yotta
section: yotta/index
---

<div class="page-header">
  <h1>Yotta Documentation</h1>
</div>

<a name="introduction"></a>
## Introduction
yotta is a tool that we're building at [mbed](https://mbed.org) to help ourselves and others build better software for C-family languages (that's C, C++ and Objective-C). It's a command line tool `yotta`, but also a culture of building software components that do one thing well, declare a clear interface, and can be re-used.

Get started by [installing yotta](#installing), and following [the tutorial](/../tutorial/tutorial.html). yotta is still early in development, so if you have questions/feedback or issues, please report them on our github [issue tracker](https://github.com/ARMmbed/yotta/issues).


<a name="installing"></a>
## Installing
yotta is written in [python](https://www.python.org/download/releases/2.7/),
and distributed using
[pip](http://pip.readthedocs.org/en/latest/installing.html), the python package
manager. You will need a working installation of both python and pip to install
yotta. If you have these, you can run **`pip install -U yotta`** to install the
latest version of yotta.

Because yotta is used to build software, you will also need a working
development environment for compiling software, including:

 * **[CMake](http://www.cmake.org)**, the build system that yotta uses.
 * a **compiler**, to actually compile the code into working problems.

yotta supports compiling with different compilers by specifying different
[targets](../tutorial/tutorial.html) for the compilation.

### Installing On OS X
...

#### Using Xcode's compiler to build natively for OS X
...

#### Cross-compiling from OS X
...

#### Solving Common OS X installation problems
On OS X, if you get an unknown argument error from Clang, it means some of yotta's dependencies have not yet been updated to support Xcode 5.1. Insert `ARCHFLAGS=-Wno-error=unused-command-line-argument-hard-error-in-future` before `pip` when running `pip install yotta`.



### Installing On Linux
...

#### Using clang to build natively for Linux
...

#### Cross-compiling from Linux
...

### Installing On Windows
...

#### Building natively for windows
Building natively for windows isn't yet supported. If you're adventurous and
get it working, submit a [pull request](https://github.com/armmbed/yotta/pulls)
to update these docs.

#### Cross-compiling from Windows
...



