##Yotta: Reusable Software Components

[![Build Status](https://magnum.travis-ci.com/ARM-RD/yotta.svg?token=XG7YezaYG4fZCZqqBSsP&branch=master)](https://magnum.travis-ci.com/ARM-RD/yotta)

###Install Yotta on Mac
Download the latest [release tarball](https://github.com/ARM-RD/yotta/releases).
``` bash
sudo pip install -U setuptools
sudo pip install ./path/to/yotta-a.b.c.tar.gz
```
(If you don't have `pip` installed, you may need to install that first using `easy_install pip`, and you will need a [ssh public key](https://help.github.com/articles/generating-ssh-keys) added to github.)  

The toolchain can be installed with [homebrew](https://github.com/ARM-RD/homebrew-formulae):
```bash
brew tap ARM-RD/homebrew-formulae
brew install arm-rd-clang arm-none-eabi-gcc cmake ninja jlink
```

###Install Yotta on Debian/Ubuntu
Add Yotta repository to /etc/apt/sources.list:
```bash
# 32-bit architecture
deb https://yottos.blob.core.windows.net 97be88d77f5daa7f37574a2a0600a87d/
 
# 64-bit architecture
deb https://yottos.blob.core.windows.net 631ac5876889410e847e527b137756dc/

# Yotta requires CMake 2.8.12 or higher
# In Debian, add the testing repository (jessie) to get access to CMake 2.8.12
```

Update the package list and install Yotta using the meta-package:
```bash
sudo apt-get update
sudo apt-get install yottos-build-tools
```

Note: packages have been tested on Ubuntu 14.04 LTS 32/64-bit and Debian 7 32-bit.


###Build a Project
Use yotta to download and build the current version of a project.
```bash
# set the target device:
yotta target stk3700

# install from the public registry (also accepts Owner/Project github URLs,
# including privately accessible repos, such as ARM-RD/objectador)
yotta install matrixlcd

# cd into the installed project
cd matrixlcd

# build (generates top level CMake files, runs cmake, then make)
yotta build
```

### Create a new Component
```bash
# create a directory for the new software component
mkdir my-component
cd my-component
# run `yotta init` to create a template component desctiption (package.json file):
yotta init
...
```
Components should have the following basic layout:
```bash
source/<source files>
<projectname>/<public header files>
test/<source files>
readme.md
```
Any directories (normally just the source and test directories) that contain libraries or executables to be built should contain a [CMakeLists.txt](http://www.cmake.org/cmake/help/v2.8.8/cmake.html#section_Description) file describing the libraries and/or executables to built from the files in that directory.

Here's an example:
```CMake
# the actual library we export
add_library(my-library
    some_file.c
    some_other_file.c
)

target_link_libraries(my-library
    some-dependency
)
```
In this case, we're telling CMake to link our library against `some-dependency`. We need to also make sure this dependency is installed and built by yotta by adding it to the `package.json` file, in the `dependencies` section:
```json
{
  "name": "my-library",
  "version": "0.0.1",
  "description": "My awesome new library",
  "dependencies": {
    "some-dependency": "*"
  }
}
```
Now you can `yotta install` and `yotta build` to build the new component. When you're ready to share it with other people, use `yotta publish` to publish it to the component registry for others to use.

### Developing on an Existing Project
To develop a project we want to grab the source using git, so we have a copy we can can use to commit and push changes:
```bash
# get the version-controlled source
git clone git@github.com:ARM-RD/yottos.git
cd yottos

# set the target device:
yotta target stk3700

# install dependencies
yotta install

# build
yotta build

# go back up and work on things
cd ..
vim ./source/somefile.h
...

# commit your work
git commit -m "make stuff more awesome, getting ready for a new release"

# tag a new minor version of this project, and push it to github
yotta version minor
git push && git push --tags

# publish the new version to the world (note: you have to be the owner of the project inorder to publish)
yotta publish
```

#### Make changes to a dependency: `yotta link`
It's often useful to make changes to a dependency of what you're working on, and have those changes immediately reflected in your main project, yotta makes this really easy:

```bash
# create a new project directory with the version-controlled source of
# the dependency you care about:
git clone git@github.com:ARM-RD/libc.git
cd libc

# install the dependencies
yotta install

# link this component into the globally installed component
# (may need `sudo' depending on your configuration)
yotta link

# go back to the main project
cd ../yottos
yotta link libc

# rebuild
yotta build

# now you can make changes to the dependency, rebuild, and they will
# be immediately reflected in the main project
```

### Attach a debugger `yotta debug`
For targets that support it, you can attach a debugger to download and run code directly from yotta:

Currently the only target that supports this is [stk3700](https://github.com/ARM-RD/target-stk3700), which has more help on debugging in its readme.

```

yotta target stk3700
yotta build

# launch a debugger connected (possibly via a debug server) to the target
yotta debug test/mytest

...

Waiting for GDB connection...Connected to 127.0.0.1
Reading all registers
Read 4 bytes @ address 0x00000000 (Data = 0x20005D00)
0x00000000 in __isr_vector ()
Selecting device: EFM32GG990F1024
Flash download enabled
SWO started.
> load
...
Transfer rate: 16536 KB/sec, 15240 bytes/write.
> monitor reset
Resetting target
> continue
```

### Secret Tips
Congratulations for reading to the end of the readme, unless you skipped straight here, in which case, naughty you. In either case, here's some helpful tips:

 * `yt` is a shorthand for the `yotta` command, and it's much quicker to type!
 * yotta is strongly influenced by [npm](http://npmjs.org), the awesome node.js software packaging system. Much of the syntax for package description and commands is very similar.

