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

First install [homebrew](http://brew.sh), a package manager for OS X that we'll use to
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
Before installing yotta in Windows, you need to have a working installation of Python and pip
(a Python package manager) . There are a number of places that provide installers for Python on
Windows, including:

- [python.org](https://www.python.org/downloads/). If you use this, you'll also need to [install pip manually](https://pip.pypa.io/en/latest/installing.html).
- [ActivePython](http://www.activestate.com/activepython/downloads). This distribution already includes pip and other useful modules.

Choose an installer for the latest available Python 2.7 version.

During installation, make sure to check the "add to path" option in the installer. After the installation,
you should be able to open cmd.exe and run `python`. If that doesn't work, the most likely cause
is that the Python installation directory (typically **c:\Python27**) is not in your PATH, so make sure
you add it (following, for example, [this guide](http://superuser.com/questions/317631/setting-path-in-windows-7-command-prompt)).
You also need to add the "scripts" subdirectory of your Python installation (typically **c:\Python27\Scripts**)
to your PATH. If the "scripts" subdirectory is properly added to your PATH, you should be able to
execute `pip` from the command prompt.

With Python and pip properly installed, follow these steps to install yotta:

- install PyCrypto 2.6 for Python 2.7 from [Voidspace](http://www.voidspace.org.uk/python/modules.shtml#pycrypto).
Make sure that you use the installer that matches your Python installation (32 or 64 bit).
- open cmd.exe and run `pip install -U yotta`
- [cmake](http://www.cmake.org/) is a makefile generator, used by yotta internally. Download and install
it from [here](http://www.cmake.org/download/). yotta on Windows was tested mostly with version 3.1.0-rc2
of cmake, but 3.0.2 (the latest stable version at the time of writing this) should work too. Make sure to
check the "add cmake to the path for current user" option during installation.
- [ninja](http://martine.github.io/ninja/) is a fast and small build system that works well in Windows.
Download the release archive from [here](https://github.com/martine/ninja/releases/download/v1.5.3/ninja-win.zip)
and extract 'ninja.exe' to **c:\ninja** or any other directory. Add that directory to your PATH.
- [sed](https://www.gnu.org/software/sed/) is another tool used by yotta in Windows. A binary installer can be
found [here](http://gnuwin32.sourceforge.net/packages/sed.htm). After installing sed, add the directory with
'sed.exe' to your PATH.

### Building natively for windows
Building natively for windows isn't yet supported. If you're adventurous and
get it working, submit a [pull request](https://github.com/armmbed/yotta/pulls)
to update these docs.

### Cross-compiling from Windows
First install the [`arm-none-eabi-gcc` compiler](https://launchpad.net/gcc-arm-embedded). At the
time of writing this, the latest version used for cross-compiling with yotta is
[gcc 4.8](https://launchpad.net/gcc-arm-embedded/4.8/4.8-2014-q3-update/+download/gcc-arm-none-eabi-4_8-2014q3-20140805-win32.exe).
Download and install it, then add the bin/ subdirectory of the installation directory to your PATH.
After you do that, you should be able to open cmd.exe and run `arm-none-eabi-gcc` from
the command prompt. If that doesn't work, make sure that your PATH is properly set.

To use this compiler, you'll need to select a supported cross-compilation
target, such as
[frdm-k64f-gcc](https://github.com/ARMmbed/target-frdm-k64f-gcc), by running
`yotta target frdm-k64f-gcc` before building.

