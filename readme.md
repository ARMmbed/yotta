## yotta: Build Software with Reusable Components
[![Build Status](https://magnum.travis-ci.com/ARMmbed/yotta.svg?token=XG7YezaYG4fZCZqqBSsP)](https://magnum.travis-ci.com/ARMmbed/yotta)

Yotta is a tool that we're building at [mbed](https://mbed.org), to make it easier to build better software written in C, C++ or other C-family languages. It's still early in development, so if you have questions/feedback or issues, please report them on our  issue tracker.

### Installation
First download the latest [release tarball](https://github.com/ARMmbed/yotta/releases), then:
``` bash
sudo pip install -U setuptools
sudo pip install ./path/to/yotta-a.b.c.tar.gz
```
You may need to [install pip](http://pip.readthedocs.org/en/latest/installing.html), if you do not already have it.
 
On OS X, if you get an unknown argument error from Clang, it means some of yotta's dependencies have not yet been updated to support XCode 5.1. Insert `ARCHFLAGS=-Wno-error=unused-command-line-argument-hard-error-in-future` between `sudo` and `pip` above.

Yotta also requires:

 * [CMake](http://www.cmake.org), on OS X this can be installed with [homebrew](http://brew.sh), and on linux via the system's package manager.
 * Your system's compiler. (gcc or clang.) If you're cross-compiling using a target description, then the target will have its own requirements for an installed compiler.


### Further Documentation
For further documentation see the [yotta docs](http://armmbed.github.io/yotta-docs/) website.


### Tips
 * `yt` is a shorthand for the `yotta` command, and it's much quicker to type!
 * yotta is strongly influenced by [npm](http://npmjs.org), the awesome node.js software packaging system. Much of the syntax for module description and commands is very similar.


### mbed Internal Users

For additional instructions on setting up internal toolchains, see [the internal docs](https://github.com/arm-rd/target-stk3700) for the stk3700 target.



