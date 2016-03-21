---
layout: default
title: yotta
section: yotta/index
---

<div class="page-header">
  <h1>yotta Documentation</h1>
</div>

# <a href="#introduction" name="introduction">#</a> Introduction
yotta is a tool that we're building at [mbed](https://mbed.org) to help
ourselves and others build better software for C-family languages by making it
easier to share and re-use software modules. It's a command line tool `yotta`,
but also a culture of building software components that do one thing well,
declare a clear interface, and can be re-used.

Get started by [installing yotta](#installing), and following [the
tutorial](/../tutorial/tutorial.html). yotta is still early in development, so
if you have questions/feedback or issues, please report them on our github
[issue tracker](https://github.com/ARMmbed/yotta/issues).


<br>
# <a href="#installing" name="installing">#</a> Installation
yotta is written in [python](https://www.python.org/download/releases/2.7/),
and distributed using
[pip](http://pip.readthedocs.org/en/latest/installing.html), the python package
manager. You will need a working installation of both python and pip to install
yotta, as well as a working development environment for compiling software, including:

 * **[CMake](http://www.cmake.org)**, the build system that yotta uses.
 * a **compiler**, to actually compile the code into working programs.

yotta supports compiling with different compilers by specifying different
[targets](../tutorial/targets.html) for the compilation, and a compilation
target may have its own specific requirements.

To install yotta, please follow the detailed installation instructions for your
operating system below:

 * [Windows](#installing-on-windows)
 * [Mac](#installing-on-osx)
 * [Linux](#installing-on-linux)

If you have a complex python setup on your system, you may want to consider
installing yotta in a [virtualenv](#virtualenv-install), in order to separate
its dependencies from other python programs on your system.

To upgrade an existing installation to a new version, see
[upgrading](#upgrading) (the same for all systems).

If you have a restrictive firewall setup, then for yotta to be fully
functional you may also need to ensure that it can access
the [required domains](/reference/registry.html#network-access).

<br>
<br>
## <a href="#installing-on-osx" name="installing-on-osx">#</a> Installing On OS X
To install yotta on OS X you can either use the packaged [yotta.app](https://github.com/ARMmbed/yotta_osx_installer/releases/latest) or install yotta and its dependencies yourself.
### <a href="#osx-yotta-app" name="osx-yotta-app">#</a> Using yotta.app
Download the latest [**OS X yotta.app**](https://mbed-media.mbed.com/filer_public/91/56/91567e17-7a78-41ec-a998-4ee38e6274a2/yotta_osx_installer_v004.dmg), and drag yotta.app from the disk image into your applications folder.

When you run yotta.app, a terminal will open where you can use yotta commands.

### <a href="#osx-manual-install" name="osx-manual-install">#</a> Manual Installation
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
pip install yotta
```

### <a href="#osx-cross-compile" name="osx-cross-compile">#</a> Cross-compiling from OS X
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


### <a href="#osx-native-compile" name="osx-native-compile">#</a> Using Xcode's compiler to build natively for OS X
To compile things natively you need to have the Xcode command line tools
installed. Install [Xcode](https://developer.apple.com/xcode/downloads/) from
the Mac app store, then run:

```sh
xcode-select --install
```

To use this compiler to build a module, you should run `yotta target
x86-osx-native` before building. This selects the yotta target description for
the native compiler.


### <a href="#solve-osx-problems" name="solve-osx-problems">#</a> Solving Common OS X installation problems
On OS X, if you get an unknown argument error when running `pip install yotta`, it means some of yotta's dependencies have not yet been updated to support Xcode 5.1.
To fix this, install yotta by running:

```sh
ARCHFLAGS=-Wno-error=unused-command-line-argument-hard-error-in-future pip install yotta
```


<br>
<br>
## <a href="#installing-on-linux" name="installing-on-linux">#</a> Installing On Linux
### <a href="#dependencies-linux" name="dependencies-linux">#</a> Installing Dependencies
First install yotta's dependencies using your system's package manager. Use
whatever 2.7.* python version is provided by your distribution (python 3
support is currently experimental).

**on Debian and Ubuntu:**

```sh
sudo apt-get update && sudo apt-get install python-setuptools  cmake build-essential ninja-build python-dev libffi-dev libssl-dev && sudo easy_install pip
```

**and on Fedora Linux (tested on FC21):**

```sh
# install development tool dependencies
sudo yum install python-pip cmake ninja-build python-devel libffi-devel openssl-devel clang
sudo yum groupinstall "Development Tools" "Development Libraries"

# update pip to latest release
sudo yum remove python-pip
curl -o get-pip.py https://bootstrap.pypa.io/get-pip.py
sudo python get-pip.py
```

**or under cygwin (on windows)**, which presents a linux-like environment to yotta:

 * install the [windows dependencies](#installing-on-windows)
 * install the libffi-developer and openssl-developer cygwin modules as both
   binary and source
 * install python and pip in cygwin


### <a href="#yotta-itself-linux" name="yotta-itself-linux">#</a> Install yotta Itself 

After installing the dependencies, install yotta itself using pip (you may need
to use `sudo` for this, depending on your configuration):

```sh
pip install yotta
```

If you experience problems with a systemwide yotta installation on linux, you
can try installing yotta in a [virtualenv](https://virtualenv.pypa.io) by
following [these instructions](#virtualenv-install).

You can use the following commands to allow the current user to override module
dependencies using [`yotta link`](/reference/commands.html#yotta-link) without
sudo:

```bash
sudo mkdir -p /usr/local/lib/yotta_modules
sudo chown $USER /usr/local/lib/yotta_modules
chmod 755 /usr/local/lib/yotta_modules
```

### <a href="#linux-cross-compile" name="linux-cross-compile">#</a> Cross-compiling from Linux
To cross-compile yotta modules for embedded targets, you first need install the
[`arm-none-eabi-gcc` compiler](https://launchpad.net/gcc-arm-embedded).

On most Linux distributions (although not Ubuntu), this can be done by running:

```sh
sudo apt-get install gcc-arm-none-eabi
```

On Ubuntu it's necessary to use the ARM-maintained [gcc-arm-embedded
package](https://launchpad.net/gcc-arm-embedded), instead:

```sh
# remove the built-in package, if installed:
sudo apt-get remove binutils-arm-none-eabi gcc-arm-none-eabi
# set up the PPA for the ARM-maintained package:
sudo add-apt-repository ppa:team-gcc-arm-embedded/ppa
sudo apt-get update
# install:
sudo apt-get install gcc-arm-embedded
```

To use this compiler, you'll need to select a supported cross-compilation
target, such as
[frdm-k64f-gcc](https://github.com/ARMmbed/target-frdm-k64f-gcc), by running
`yotta target frdm-k64f-gcc` before building.


### <a href="#linux-native-compile" name="linux-native-compile">#</a> Using clang to build natively for Linux
Install a native compiler, such as clang:

```sh
sudo apt-get install clang-3.5
```

To use this compiler to build a module, you should run `yotta target
x86-linux-native` before building. This selects the yotta target description for
the native compiler.

### <a href="#linux-common-issues" name="linux-common-issues">#</a> Solving Common Linux installation problems
If you are having trouble with pip not installing yotta, try running `sudo pip install -U pip` to update your pip installation. Check that your pip installation is up to date by running `pip -V`, you should get a response of `7.1.2` or greater. 

On Ubuntu the default pip installation `python-pip` is out of date (1.5.2) and cannot upgrade itself via `sudo pip install -U pip`. To solve this you will need to install pip from `easy_install` by running `easy_install pip`. You should then be able to install yotta by running `pip2 install yotta`. 

You can also try [installing pip from the Pypy registry](https://pip.pypa.io/en/stable/installing/) if everything else fails.




<br>
## <a href="#installing-on-windows" name="installing-on-windows">#</a> Installing on Windows
To install yotta on windows you can either use the one shot windows installer or install all the dependencies and yotta manually.
### <a href="#windows-installer" name="windows-installer">#</a> yotta Windows Installer
 1. Download the latest [**yotta windows installer**](https://mbed-media.mbed.com/filer_public/2f/0b/2f0b924c-1fac-4907-989b-f2afe3f5785e/yotta_install_v023.exe).
 2. Run the installer. 
 3. Click on `Run Yotta` shortcut on desktop or in start menu to run session with yotta path temporarily pre-pended to system path. 

### <a href="#manual-windows-installation" name="manual-windows-installation">#</a> Manual Installation
1. **Install [python](https://www.python.org/downloads/release/python-279/)**. You
    **must** install [python
    2.7.9 or later](https://www.python.org/downloads/release/python-279/) for yotta to
    work on windows. Select either the [x86-64
    installer](https://www.python.org/ftp/python/2.7.9/python-2.7.9.amd64.msi)
    if you use 64-bit
    windows, or the [x86
    installer](https://www.python.org/ftp/python/2.7.9/python-2.7.9.msi) if you
    use 32-bit windows.

    **During installation, be sure to select the "add to path" option.** This
    will let you run python easily from a command prompt.
 
 2. **Install [CMake](http://www.cmake.org/download/)**. yotta uses CMake to
    generate makefiles that control the build. Select the latest available
    version, currently 3.2.1 The [32-bit
    version](http://www.cmake.org/files/v3.2/cmake-3.2.1-win32-x86.exe)
    will work on all versions of windows. Be sure to check the "add cmake to
    the path for current user" option during installation.

 3. **Install Ninja**, the small and extremely fast build system that yotta
    uses. Download the release archive from the [releases
    page](https://github.com/martine/ninja/releases/download/v1.5.3/ninja-win.zip),
    and extract it to a directory (for example `C:\ninja`).
 
 4. Add the directory you installed Ninja in to [your path](#windows-path).

 5. Install the **[arm-none-eabi-gcc](#windows-cross-compile) cross-compiler** in
    order to build software to run on embedded devices.

 6. Finally, **open cmd.exe and run `pip install -U yotta`** to install yotta
    itself.

### <a href="#windows-cross-compile" name="windows-cross-compile">#</a> Cross-compiling from Windows
To use yotta to cross-compile binaries to run on embedded hardware, you need to
first install the [`arm-none-eabi-gcc`
compiler](https://launchpad.net/gcc-arm-embedded). At the time of writing this,
the latest version used for cross-compiling with yotta is [gcc
4.9](https://launchpad.net/gcc-arm-embedded/4.9/4.9-2015-q2-update/+download/gcc-arm-none-eabi-4_9-2015q2-20150609-win32.exe).
Download and install it, then add the bin/ subdirectory of the installation
directory to [your path](#windows-path).  After you do that, you should be able to open cmd.exe
and run `arm-none-eabi-gcc` from the command prompt. If that doesn't work, make
sure that your path is properly set.

To use this compiler, you'll need to select a supported cross-compilation
target, such as
[frdm-k64f-gcc](https://github.com/ARMmbed/target-frdm-k64f-gcc), by running
`yotta target frdm-k64f-gcc` before building.


### <a href="#windows-native-compile" name="windows-native-compile">#</a> Building programs natively to run on windows
yotta does not yet allow compiling programs to run on windows. If you are
adventurous and get it working, submit a [pull
request](https://github.com/armmbed/yotta/pulls) to update these docs.


### <a href="#windows-common-issues" name="windows-common-issues">#</a> Solving Common Windows Installation Problems

#### <a href="#windows-ninja-failed" name="windows-ninja-failed"></a> `error: command ['ninja'] failed`
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
installation of the compiler, you'll need to run **`yotta clean`**
before running build again.


### <a href="#windows-path" name="windows-path">#</a> Adding things to your PATH in windows
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
    
    **NOTE:** be careful not to add any spaces before or after the semicolon,
    this can cause commands to fail later.

 6. **finally,** close then re-open any open cmd.exe windows


<br>
## <a href="#virtualenv-install" name="virtualenv-install">#</a> Installing in a Virtualenv

[Virtualenv](https://virtualenv.pypa.io/en/latest/) is a way of separating
different python programs installed on the same system from each other. If you
have a complex python environment on your system it's recommended that you
install yotta inside a virtualenv. To do this, first install the non-python
dependencies following the normal instructions for your platform, then:

1.  Ensure you have virtualenv itself installed. It can be installed with:

        pip install virtualenv

    Check that your installation is succesful by running `virtualenv --version`.

2.  Create a directory to use for the yotta virtualenv:

        mkdir yotta-venv
        virtualenv ./yotta-venv

3.  activate the new virtualenv:

        source ./yotta-venv/bin/activate

4.  install yotta in the virtualenv:

        pip install yotta

5.  (optional) add the binary directory of your virtualenv to your PATH: (if
    you omit this step, you will need to run yotta as
    `../path/to/yotta-venv/bin/yotta` instead of simply `yotta`.

        export PATH="/path/to/yotta-venv/bin:$PATH"

Now yotta should work as normal. You will need to activate the virtualenv
any time you want to run yotta commands (you can deactivate it afterwards, by
simply running `deactivate`). 


<br>
## <a href="#upgrading" name="upgrading">#</a> Upgrading yotta (all platforms)
To update yotta itself, run:

```
pip install -U --no-deps yotta
pip install yotta
```

This will update yotta to the latest available version, and then install any
missing dependencies required by the new version.

You can also run:

```
pip install -U yotta
```

This will also attempt to update all of yotta's dependencies to their latest
versions.

On Linux and OS X you may have to run these commands as `sudo pip ....`, if
permission is denied.

<br>
## <a href="#tabcomplete" name="tabcomplete">#</a> Setting up Tab Completion
yotta uses [argcomplete](https://github.com/kislyuk/argcomplete) to provide tab
completion, so you can set up completion on Linux and OS X by adding the
following to your .bashrc or .bash_profile file:

```sh
eval "$(register-python-argcomplete yotta)"
eval "$(register-python-argcomplete yt)"
```

For more detailed instructions, see the [argcomplete
documentation](https://github.com/kislyuk/argcomplete#synopsis).

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
