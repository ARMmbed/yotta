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
yotta.

If you have these, and a working development environment, you can run
**`pip install -U yotta`** to install the latest version of yotta. In case of
problems while installing yotta, you can update pip to the latest
version by using **`sudo pip install -U pip`**. If you don't know that you
already have a working development environment set up, follow the more detailed instructions for your OS below
([windows](#installing-on-windows), [mac](#installing-on-osx), or
[linux](#installing-on-linux)).

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
sudo apt-get install python-pip cmake build-essential ninja-build python-dev
```

and on Fedora Linux (tested on FC21):

```sh
# install development tool dependencies
sudo yum install python-pip cmake ninja-build python-devel clang
sudo yum groupinstall "Development Tools" "Development Libraries"

# update pip to latest release
sudo yum remove python-pip
curl -o get-pip.py https://bootstrap.pypa.io/get-pip.py
sudo python get-pip.py
```


Then install yotta itself (you may need to use `sudo` for this, depending on
your configuration):

```sh
pip install -U yotta
```

You can use the following commands to allow the current user to override module
dependencies using [`yotta link`](/reference/commands.html#yotta-link) without
sudo:

```bash
sudo mkdir -p /usr/local/lib/yotta_modules
sudo chown $USER /usr/local/lib/yotta_modules
chmod 755 /usr/local/lib/yotta_modules
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

 1. **Install [python](https://www.python.org/downloads/release/python-279/)**. You
    **must** install [python
    2.7.9](https://www.python.org/downloads/release/python-279/) for yotta to
    work on windows. Select either the [x86-64
    installer](https://www.python.org/ftp/python/2.7.9/python-2.7.9.amd64.msi)
    if you use 64-bit
    windows, or the [x86
    installer](https://www.python.org/ftp/python/2.7.9/python-2.7.9.msi) if you
    use 32-bit windows.

    **During installation, be sure to select the "add to path" option.** This
    will let you run python easily from a command prompt.

 2. Install PyCrypto 2.6 for Python 2.7 from
    [Voidspace](http://www.voidspace.org.uk/python/modules.shtml#pycrypto).
    Select either the [32-bit
    installer](http://www.voidspace.org.uk/downloads/pycrypto26/pycrypto-2.6.win32-py2.7.exe)
    or the [64-bit
    installer](http://www.voidspace.org.uk/downloads/pycrypto26/pycrypto-2.6.win-amd64-py2.7.exe)
    matching the python version that you installed.

    If pip cannot be found, you need to add the python scripts directory to
    your path. This is `C:\Python27\Scripts` unless you selected a different
    directory during python installation. [These instructions](#windows-path)
    will guide you through the process.

 3. **Install [CMake](http://www.cmake.org/download/)**. yotta uses CMake to
    generate makefiles that control the build. Select the latest available
    version, currently 3.2.1 The [32-bit
    version](http://www.cmake.org/files/v3.2/cmake-3.2.1-win32-x86.exe)
    will work on all versions of windows. Be sure to check the "add cmake to
    the path for current user" option during installation.

 4. **Install Ninja**, the small and extremely fast build system that yotta
    uses. Download the release archive from the [releases
    page](https://github.com/martine/ninja/releases/download/v1.5.3/ninja-win.zip),
    and extract it to a directory (for example `C:\ninja`).
 
 5. Add the directory you installed Ninja in to [your path](#windows-path).

 6. Install the **[arm-none-eabi-gcc](#windows-cross-compile) cross-compiler** in
    order to build software to run on embedded devices.

 7. Finally, **open cmd.exe and run `pip install -U yotta`** to install yotta
    itself.


### Building programs natively to run on windows
yotta does not yet allow compiling programs to run on windows. If you are
adventurous and get it working, submit a [pull
request](https://github.com/armmbed/yotta/pulls) to update these docs.

<a name="windows-cross-compile"></a>
### Cross-compiling from Windows
To use yotta to cross-compile binaries to run on embedded hardware, you need to
first install the [`arm-none-eabi-gcc`
compiler](https://launchpad.net/gcc-arm-embedded). At the time of writing this,
the latest version used for cross-compiling with yotta is [gcc
4.8](https://launchpad.net/gcc-arm-embedded/4.8/4.8-2014-q3-update/+download/gcc-arm-none-eabi-4_8-2014q3-20140805-win32.exe).
Download and install it, then add the bin/ subdirectory of the installation
directory to [your path](#windows-path).  After you do that, you should be able to open cmd.exe
and run `arm-none-eabi-gcc` from the command prompt. If that doesn't work, make
sure that your path is properly set.

To use this compiler, you'll need to select a supported cross-compilation
target, such as
[frdm-k64f-gcc](https://github.com/ARMmbed/target-frdm-k64f-gcc), by running
`yotta target frdm-k64f-gcc` before building.

<a name="windows-common-issues"></a>
### Solving Common Windows Installation Problems

#### `error: command ['ninja'] failed`
If you get an error when running `yotta build` which looks something like this:

```sh
':' is not recognized as an internal or external command,
operable program or batch file.
...
ninja: build stopped: subcommand failed.
error: command ['ninja'] failed
```
This is caused by re-trying a `yotta build` after fixing a missing
[cross-compiler installation](#windows-cross-compile). After completing the
installation of the compiler, you'll need to **delete the `./build` directory**
before running build again.

<a name="windows-path"></a>
### Adding things to your PATH in windows
Your PATH environment variable holds the location of programs that can be
easily executed by other programs. If yotta fails to find one of its
dependencies (such as cmake.exe) the first thing to check is that you have
added the directory that contains the dependencies executable to the PATH. To
add things to your path:

 1. Right click on Computer, select `Properties`
 2. Select `Advanced System Settings`
 3. Select the `Advanced` tab
 4. Click the `Environment Variables` button
 5. Find the `Path` variable, edit it, and append the path you want to add,
    preceded by a semicolon, for example: `;C:\Path\to\wherever`
 6. **close then re-open any open cmd.exe windows**

<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
