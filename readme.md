## yotta: Build Software with Reusable Components
[![Build Status](https://travis-ci.org/ARMmbed/yotta.svg)](https://travis-ci.org/ARMmbed/yotta)
[![Build Status](https://circleci.com/gh/ARMmbed/yotta.svg?style=svg)](https://circleci.com/gh/ARMmbed/yotta)

yotta is a tool from [ARM mbed](https://mbed.org), to make it easier to build
better software with C++ and C by re-using modules. Publish your own modules to
the [yotta registry](http://yottabuild.org/) to share them with other people,
or re-use them privately in your own projects.

Whenever you build a project with yotta, you first select a [yotta
target](http://docs.yottabuild.org/tutorial/targets.html). Targets describe the
platform that you're building for (such as an [embedded IoT development
board](http://yotta.mbed.com/#/target/frdm-k64f-gcc), or natively for
[Mac](http://yotta.mbed.com/#/target/x86-osx-native) or
[Linux](http://yotta.mbed.com/#/target/x86-linux-native)), and provide all the
information that yotta and modules you're using need to configure themselves
correctly for that platform.

### Installation
yotta is written in
[python](https://www.python.org/downloads/release/python-279/), and is
installed using [pip](https://pip.pypa.io/en/stable/installing/).
Install yotta itself by running:

```bash
pip install yotta
```

**Note that yotta needs several non-python dependencies to be installed
correctly (such as a C++ compiler).** The **[detailed installation
instructions](http://yottadocs.mbed.com/#installing)** include a full guide.

Exactly which other dependencies (such as compilers and other build tools) are
required will also depend on the [yotta target
description](http://yottadocs.mbed.com/tutorial/targets.html) that you intend
to use, so please be sure to also check the target description's own
documentation.

## Get Started!
The best way to get started is to [follow the
tutorial](http://yottadocs.mbed.com/tutorial/tutorial.html), or if you have
questions/feedback please [create an
issue](https://github.com/ARMmbed/yotta/issues)!

## How `yotta` works
Every yotta module or application includes a
[`module.json`](http://docs.yottabuild.org/reference/module.html) file, which
lists the other modules that it needs (amongst other information like the
module's license, and where to submit bug reports).

When you run [`yotta build`](http://docs.yottabuild.org/tutorial/building.html)
to build your project, yotta downloads your dependencies, and makes them
available to your project. It's similar in concept to npm, pip or gem: although
because C and C++ are compiled languages, yotta also controls the build of your
software in order to ensure downloaded modules are available to use in your
code.

To add a new module to your program run `yotta install <modulename>`.  yotta
will install both the module you've specified and any of its dependencies that
you don't already have. It will also update your module.json file to reflect
the new dependency.

The best way to really understand how yotta works is to [follow the
tutorial](http://yottadocs.mbed.com/tutorial/tutorial.html).

## Further Documentation
For further documentation see the [yotta docs](http://yottadocs.mbed.com)
website.

## Tips
 * `yt` is a shorthand for the `yotta` command, and it's much quicker to type!
 * yotta is strongly influenced by [npm](http://npmjs.org), the awesome node.js
   software packaging system. Much of the syntax for module description and
   commands is very similar.

## License
yotta is licensed under Apache-2.0

