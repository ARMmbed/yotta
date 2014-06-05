###Yotta: Software Components for Embedded Systems

[![Build Status](https://magnum.travis-ci.com/ARM-RD/yotta.svg?token=XG7YezaYG4fZCZqqBSsP&branch=master)](https://magnum.travis-ci.com/ARM-RD/yotta)

####Install Yotta
``` bash
sudo pip install -e git+ssh://git@github.com/ARM-RD/yotta.git#egg=yotta
```
(If you don't have `pip` installed, you may need to install that first using `easy_install pip`, and you will need a [ssh public key](https://help.github.com/articles/generating-ssh-keys) added to github.)  

The toolchain can be installed with [homebrew](https://github.com/ARM-RD/homebrew-formulae):
```bash
brew tap ARM-RD/homebrew-formulae
brew install arm-rd-clang arm-none-eabi-gcc cmake ninja jlink
```

On Linux, the current workaround is to use [linuxbrew](https://github.com/Homebrew/linuxbrew) to install the packages above. Alternatively, [jlink](http://www.segger.com/jlink-software.html) and [arm-gcc](https://launchpad.net/gcc-arm-embedded/+download) can be downloaded seperately. Since linuxbrew puts the Cellar directory in ~/.linuxbrew/Cellar, make a symlink to it in /usr/local/Cellar. 

####Build a Project
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

#### Developing on an Existing Project
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

#### Attach a debugger `yotta debug`
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


