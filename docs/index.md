---
layout: default
title: yotta
section: yotta/index
---

<div class="page-header">
  <h1>Yotta Documentation</h1>
</div>

<a name="introduction"></a>
# Introduction
yotta is a tool that we're building at [mbed](https://mbed.org) to help ourselves and others build better software for C-family languages (that's C, C++ and Objective-C). It's a command line tool `yotta`, but also a culture of building software components that do one thing well, declare a clear interface, and can be re-used.

Get started by [installing yotta](#installing), and following [the tutorial](/../tutorial/tutorial.html). yotta is still early in development, so if you have questions/feedback or issues, please report them on our github [issue tracker](https://github.com/ARMmbed/yotta/issues).


<br>
<a name="installing"></a>
# Installing
yotta is written in [python](https://www.python.org/download/releases/2.7/),
and distributed using
[pip](http://pip.readthedocs.org/en/latest/installing.html), the python package
manager. You will need a working installation of both python and pip to install
yotta. If you have these, you can run **`pip install -U yotta`** to install the
latest version of yotta.  If you don't know that you already have these, follow
the more detailed instructions for your OS below.

Because yotta is used to build software, you will also need a working
development environment for compiling software, including:

 * **[CMake](http://www.cmake.org)**, the build system that yotta uses.
 * a **compiler**, to actually compile the code into working programs.

yotta supports compiling with different compilers by specifying different
[targets](../tutorial/targets.html) for the compilation.

<br>
<a name="installing-on-osx"></a>
## Installing On OS X

First install [homebrew](brew.sh), a package manager for OS X that we'll use to
install all of yotta's dependencies.

Next, tap the ARMmbed [brew
formulae](https://github.com/armmbed/homebrew-formulae), which lets brew
install packages from the mbed team:

```sh
brew tap ARMmbed/homebrew-formulae
```

Now we can install everything that yotta needs:

```sh
brew install python cmake ninja arm-none-eabi-gcc
```

And install yotta itself:

```sh
pip install -U yotta
```


### Using Xcode's compiler to build natively for OS X
To compile things natively you need to have the Xcode command line tools
installed. Install [Xcode](https://developer.apple.com/xcode/downloads/) from
the Mac app store, then run:

```sh
xcode-select --install
```

To use this compiler to build a module, you should run `yotta target
x86-osx-native` before building. This selects the yotta target description for
the native compiler.


### Cross-compiling from OS X
To cross-compile, you need the `arm-none-eabi-gcc` cross-compiler. You can
install this using homebrew, after tapping the ARMmbed homebrew [package
repository](https://github.com/armmbed/homebrew-formulae).

```sh
brew install arm-none-eabi-gcc
```

To use this compiler, you'll need to select a supported cross-compilation
target, such as
[frdm-k64f-gcc](https://github.com/ARMmbed/target-frdm-k64f-gcc), by running
`yotta target frdm-k64f-gcc` before building.


### Solving Common OS X installation problems
On OS X, if you get an unknown argument error when running `pip install yotta`, it means some of yotta's dependencies have not yet been updated to support Xcode 5.1.
To fix this, install yotta by running:

```sh
ARCHFLAGS=-Wno-error=unused-command-line-argument-hard-error-in-future pip install yotta
```


<br>
<a name="installing-on-linux"></a>
## Installing On Linux
First install yotta's dependencies using your system's package manager, for
example on Debian and Ubuntu:

```sh
sudo apt-get install python-pip cmake build-essential ninja-build
```

Then install yotta itself (you may need to use `sudo` for this, depending on
your configuration):

```sh
pip install -U yotta
```



### Using clang to build natively for Linux
Install a native compiler, such as clang:

```sh
sudo apt-get install clang-3.5 
```

To use this compiler to build a module, you should run `yotta target
x86-linux-native` before building. This selects the yotta target description for
the native compiler.


### Cross-compiling from Linux

First install the [`arm-none-eabi-gcc`
compiler](https://launchpad.net/gcc-arm-embedded):

```sh
sudo apt-get install gcc-arm-none-eabi 
```

To use this compiler, you'll need to select a supported cross-compilation
target, such as
[frdm-k64f-gcc](https://github.com/ARMmbed/target-frdm-k64f-gcc), by running
`yotta target frdm-k64f-gcc` before building.


<br>
<a name="installing-on-windows"></a>
## Installing On Windows
...

### Building natively for windows
Building natively for windows isn't yet supported. If you're adventurous and
get it working, submit a [pull request](https://github.com/armmbed/yotta/pulls)
to update these docs.

### Cross-compiling from Windows
...



