## yotta: Build Software with Reusable Components
> TODO add build status back here


### Installation
First download the latest [release tarball](https://github.com/ARMmbed/yotta/releases), then:
``` bash
sudo pip install -U setuptools
sudo pip install ./path/to/yotta-a.b.c.tar.gz
```
(If you don't have `pip` installed, you may need to install that first using `easy_install pip`)  
(If you get an unknown argument error from Clang, it means some of the components have not been updated to support Apple LLVM in XCode 5.1. Insert 'ARCHFLAGS=-Wno-error=unused-command-line-argument-hard-error-in-future' between 'sudo' and 'pip' above.)

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



