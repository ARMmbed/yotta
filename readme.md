##Yotta: Software Components for Embedded Systems

###Build a Project from Github

```bash
# set the target device:
yotta target stk3700

# install a yotta-enabled github project, and all its dependencies
yotta install ARM-RD/objectador

# cd into the installed project
cd objectador

# generate build files, and build 
yotta build
cd build
cmake . && make
```

### Developing on an Existing Project
    
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

# change some files
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

