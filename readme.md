###Yotta: Software Components for Embedded Systems

[![Build Status](https://magnum.travis-ci.com/ARM-RD/yotta.svg?token=XG7YezaYG4fZCZqqBSsP&branch=master)](https://magnum.travis-ci.com/ARM-RD/yotta)

####Install Yotta
``` bash
sudo pip install -e git+ssh://git@github.com/ARM-RD/yotta.git#egg=yotta
```
(If you don't have `pip` installed, you may need to install that first using `easy_install pip`, and you will need a [ssh public key](https://help.github.com/articles/generating-ssh-keys) added to github.)  

The toolchain can be installed with [homebrew](https://github.com/ARM-RD/homebrew-formulae):
```bash
brew tap ARM-RD/formulae
brew install arm-rd-clang arm-none-eabi-gcc cmake ninja
```

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

# generate build files, and build
yotta build
cd build
cmake . && make
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

# generate build files, and build
yotta build
cd build
cmake . && make

# go back up and work on things
cd ..
vim ./source/somefile.h
...

# commit your work
git commit -m "make stuff more awesome, getting ready for a new release"

# tag a new minor version of this project, and push it to github
yotta version minor
git push && git push --tags

# publish the new version to the world
yotta publish
```

# Make changes to a dependency: `yotta link`
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

# regenerate build files and rebuild
yotta build
cd build
make

# now you can make changes to the dependency, rebuild, and they will
# be immediately reflected in the main project
```


