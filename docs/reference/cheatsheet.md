---
layout: default
title: Quick reference guide
section: yotta/cheatsheet
---

{% capture colOne %}
## Installation

### Instructions
 - [Video Guides](https://goo.gl/cJT1tO).
 - [Linux Instructions](http://docs.yottabuild.org/#installing-on-linux).
 - [OS X Instructions](http://docs.yottabuild.org/#installing-on-osx).
 - [Windows Instructions](http://docs.yottabuild.org/#installing-on-windows).

### Manual Installation
`pip install -U yotta`

You will also need [CMake](https://cmake.org),
[ninja](https://github.com/martine/ninja/releases),
[Python](https://www.python.org/downloads/release/python-2710/) and
[arm-none-eabi-gcc](https://launchpad.net/gcc-arm-embedded).


## Modules
There are two types of modules: executable and library.

### Library Modules
Library modules are reusable code, which provide functionality useful to lots
of different apps such as network stacks, drivers and encoders/decoders. Anyone
can publish a library module to the [yotta registry](http://yottabuild.org)
where other people can find useful modules and reuse them.

#### Creating Library Modules
[Written tutorial](/tutorial/tutorial.html) or [video guide](https://www.youtube.com/playlist?list=PLiVCejcvpsevVVpgdIo4QxSl563ToLOIB).

### Executable Modules
Executable modules compile into a binary. Executable modules should not
generally be published to the yotta registry (because they cannot be reused by
other applications). Instead they should be shared somewhere like GitHub.

#### Creating Executable Modules
Video guides: [build from
scratch](https://www.youtube.com/watch?v=qYgHSZbl0RE&index=4&list=PLiVCejcvpsevVVpgdIo4QxSl563ToLOIB),
[clone from existing
repo](https://www.youtube.com/watch?v=gay1Jy6lMkQ&index=5&list=PLiVCejcvpsevVVpgdIo4QxSl563ToLOIB).

[Written tutorial](/tutorial/tutorial.html#Creating%20an%20Executable).

## Targets
Targets describe which platform you are building for, and how the compiler
should be run.

Guide to [using targets](/tutorial/targets.html) and [writing
targets](/tutorial/targets.html#writing-targets).

## Semantic Versioning

`major.minor.patch`

yotta modules use [semantic versioning](http://semver.org). A `0.x.y` version number
indicates a module that does not yet have a stable API. When the API is stable
increment to `1.0.0`.

For modules with a major version >= 1, the major version number must be
incremented whenever backwards-incompatible changes are made. The minor and
patch versions are used for new (backwards-compatible) features and bug-fixes respectively.

{% endcapture %}
<div class="col-md-6">
{{ colOne | markdownify }}
</div>

{% capture colTwo %}

## Commands

`yt` is short for `yotta`, and can be used with all commands.

### Create a New Module
**`yotta init`** - run in a new empty directory to create a module or
executable skeleton.

### Find and Install Modules

**`yotta search`**` module <search-query>` - search the public registry for modules.

**`yotta install`**` <dependency-name>` - install the specified module as a dependency.

### Find and Use Targets
Targets specify hardware-specific compiler settings.

**`yotta search`**` target <target-name>` - search the online registry for targets.

**`yotta target`**` <target-name>` - set the target for the current directory.

**`yotta target --global`**` <target-name>` - set a global target for all yotta projects. 

### Building
You normally build executables, but you can also build library modules.

**`yotta build`** - binaries will be produced in `./build/<targetname>/source`.

**`yotta clean`** - remove all temporary build files.

### Tests
**`yotta test`** - compile and run the tests from your `./test` folder.


### Publishing Your Modules

**`yotta publish`** - publish the current library module to the public registry.

**`yotta version`**` <major/minor/patch>` - increment the major, minor or patch version number. 

### Debugging

**`yotta debug`** - launch a debugger (uses [valinor](https://github.com/armmbed/valinor) to choose the debugger).

### List Dependencies

**`yotta list`** - display all the dependencies of the current application.

### Updating Modules

**`yotta outdated`** - display modules with newer versions available.

**`yotta update`** - update a module(s) to the latest possible versions. 


{% endcapture %}
<div class="col-md-6">
{{ colTwo | markdownify }}
</div>
<div class="clearfix"></div>

