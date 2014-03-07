###Yotta: Software Components for Embedded Systems

####Install Yotta
```bash
brew tap ARM-RD/formulae
brew install yotta
```
or
``` bash
sudo pip install -e git://github.com/ARM-RD/yotta.git#egg=yotta
```

####Build a Project
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
    
```bash
# get the version-controlled source
git clone git@github.com/ARM-RD/yottos
cd yottos

# set the target device:
yotta target stk-3700

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

