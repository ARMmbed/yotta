## yotta: Build Software with Reusable Components
[![Build Status](https://travis-ci.org/ARMmbed/yotta.svg)](https://travis-ci.org/ARMmbed/yotta)
[![Build Status](https://circleci.com/gh/ARMmbed/yotta.svg?style=svg)](https://circleci.com/gh/ARMmbed/yotta)

yotta is a tool that we're building at [mbed](https://mbed.org), to make it
easier to build better software written in C, C++ or other C-family languages.
It's still early in development, so if you have questions/feedback or issues,
please [report them](https://github.com/ARMmbed/yotta/issues).

### Installation
yotta is written in
[python](https://www.python.org/downloads/release/python-279/), and is
installed using [pip](http://pip.readthedocs.org/en/latest/installing.html).
Install yotta itself by running:

```bash
pip install yotta
```

**Note that yotta needs several non-python dependencies to be installed
correctly in order to do anything useful.** Please follow the [detailed
installation instructions](http://docs.yottabuild.org/#installing) on the yotta
docs website to ensure a working installation.

Exactly which other dependencies (such as compilers and other build tools) are
required will also depend on the [yotta target
description](http://docs.yottabuild.org/tutorial/targets.html) that you intend
to use, so please be sure to also check its own documentation.

### Get Started!
The best way to get started is to [follow the
tutorial](http://docs.yottabuild.org/tutorial/tutorial.html).

### What `yotta` does
yotta downloads the software components that your program depends on (it's
similar in concept to npm, pip or gem). To install a new module, you run `yotta
install --save <modulename>`, and yotta will install both the module you've
specified and any of its dependencies that you don't already have installed,
and save the fact that you depend on that module into your module's description
file.

To really understand how yotta works, you should install yotta (see above),
then [follow the tutorial](http://docs.yottabuild.org/tutorial/tutorial.html).

### Further Documentation
For further documentation see the [yotta docs](http://docs.yottabuild.org)
website.

### Tips
 * `yt` is a shorthand for the `yotta` command, and it's much quicker to type!
 * yotta is strongly influenced by [npm](http://npmjs.org), the awesome node.js
   software packaging system. Much of the syntax for module description and
   commands is very similar.

### License
yotta is licensed under Apache-2.0
