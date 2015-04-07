## yotta: Build Software with Reusable Components
[![Build Status](https://travis-ci.org/ARMmbed/yotta.svg)](https://travis-ci.org/ARMmbed/yotta)
[![Build Status](https://circleci.com/gh/ARMmbed/yotta.svg?style=svg)](https://circleci.com/gh/ARMmbed/yotta)

yotta is a tool that we're building at [mbed](https://mbed.org), to make it easier to build better software written in C, C++ or other C-family languages. It's still early in development, so if you have questions/feedback or issues, please [report them](https://github.com/ARMmbed/yotta/issues).

### Installation
Detailed instructions can be found on the [documentation
site](http://docs.yottabuild.org/#installing), in summary, to use yotta you
need:

 * yotta itself
 * [CMake](http://www.cmake.org/download/)
 * a compiler

**To install yotta itself**, open a terminal, then run:
``` bash
pip install yotta
```

yotta runs in [python](https://www.python.org/downloads/release/python-279/), and is installed using [pip](http://pip.readthedocs.org/en/latest/installing.html). Version 2.7.9 of python is recommended if you do not already have python installed. If permission is denied on Linux or OS X, you may need to run `sudo pip install yotta`. 

**Install CMake** from the [CMake download page](http://www.cmake.org/download/), or using your system's package manager. Make sure to check the option in the installer to add it to your path. 

**Which compiler** you need depends on whether you're building programs for your host system, or cross-compiling them run on an embedded device:

 * to cross-compile, install [arm-none-eabi-gcc](https://launchpad.net/gcc-arm-embedded/+download).
 * to compile natively on OS X, [install Xcode](https://developer.apple.com/xcode/downloads/), including the command-line tools.
 * to compile natively on Linux, install clang with your system's package manager.

Further information on installing yotta for different platforms can be found on the [documentation site](http://docs.yottabuild.org/#installing).

### Get Started!
The best way to get started is to [follow the tutorial](http://docs.yottabuild.org/tutorial/tutorial.html).

### What `yotta` does
yotta downloads the software components that your program depends on (it's similar in concept to npm, pip or gem). To install a new module, you run `yotta install --save <modulename>`, and yotta will install both the module you've specified and any of its dependencies that you don't already have installed, and save the fact that you depend on that module into your module's description file.

To really understand how yotta works, you should install yotta (see above), then [follow the tutorial](http://docs.yottabuild.org/tutorial/tutorial.html).

### Further Documentation
For further documentation see the [yotta docs](http://armmbed.github.io/yotta/) website.

### Tips
 * `yt` is a shorthand for the `yotta` command, and it's much quicker to type!
 * yotta is strongly influenced by [npm](http://npmjs.org), the awesome node.js software packaging system. Much of the syntax for module description and commands is very similar.

### License
yotta is licensed under Apache-2.0
