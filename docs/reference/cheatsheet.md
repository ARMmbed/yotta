---
layout: default
title: ARMmbed yotta cheat-sheet
byline: yotta is the open source modular orchestrator that facilitates building mbedOS and other embedded projects. This cheat sheet summarizes commonly used yotta command line instructions for quick reference.
leadingpath: ../
---

{% capture colOne %}
## Installation

### Instructions
 - [Video Guides](https://goo.gl/cJT1tO)
 - [Linux Instructions](yottadocs.mbed.com/#installing-on-linux)
 - [OS X Instructions](http://yottadocs.mbed.com/#installing-on-osx)
 - [Windows Instructions](http://yottadocs.mbed.com/#installing-on-windows)

### Manual Installation
`pip install -U yotta`

You will also need [cmake](https://cmake.org),
[ninja](https://github.com/martine/ninja/releases),
[python](https://www.python.org/downloads/release/python-2710/) and
[arm-none-eabi-gcc](https://launchpad.net/gcc-arm-embedded).


## Modules
There are two types of modules, executable and library.

### Library Modules
Library modules are re-usable code, which provide functionality useful to lots
of different apps such as network stacks, drivers, encoders/decoders. Anyone
can publish a library module to the [yotta registry](http://yotta.mbed.com)
where other people can find useful modules and re-use them.

#### Creating Library Modules
[Written tutorial](/tutorial/tutorial.html), or [video guide](https://www.youtube.com/playlist?list=PLiVCejcvpsevVVpgdIo4QxSl563ToLOIB).

### Executable Modules
Executable modules compile into a binary. Executable modules should not
generally be published to the yotta registry (because they cannot be re-used by
other applications). Instead they should be shared somewhere like Github.

#### Creating Executable Modules
Video guides: [build from
scratch](https://www.youtube.com/watch?v=qYgHSZbl0RE&index=4&list=PLiVCejcvpsevVVpgdIo4QxSl563ToLOIB),
[clone from existing
repo](https://www.youtube.com/watch?v=gay1Jy6lMkQ&index=5&list=PLiVCejcvpsevVVpgdIo4QxSl563ToLOIB),
or [written tutorial](/tutorial/tutorial.html#Creating%20an%20Executable)

## Targets
Targets describe which platform you are building for, and how the compiler
should be run.

Guide to [using targets](/tutorial/targets.html), and [writing
targets](/tutorial/targets.html#writing-targets).

## Semantic Versioning

`major.minor.patch`

yotta modules use [semantic versioning](semver.org). A `0.x.y` version number
indicates a module that does not yet have a stable API, when the API is stable
increment to `1.0.0`.

For modules with a major version >= 1 The major version number must be
incremented whenever backwards-incompatible changes are made. The minor and
patch versions are used for new features and bugfixes respectively.

{% endcapture %}
<div class="col-md-6">
{{ colOne | markdownify }}
</div>

{% capture colTwo %}

## Commands

`yt` is short for `yotta`, and can be used with all commands.

### Find and Install Modules

`yotta search module <search-query>` - search the public registry for modules

`yotta install <dependency-name>` - install the specified module as a dependency

### Find and Use Targets
Targets specify hardware specific compiler settings.

`yotta search target <target-name>` - search the online registry for targets.

`yotta target <target-name>` - set the target for the current directory.

`yotta target `**`--global`**` <target-name>` - set a global target for all yotta projects. 

### Build a Executable or Library Module
`yotta build` - binaries will be produced in `./build/<targetname>/source`

`yotta clean` - Remove all temporary build files.

### Tests
`yotta test` - compile and run the tests from your `./test` folder


### Publishing Your Modules

`yotta publish` - publish the current library module to the public registry

`yotta version <major/minor/patch>` - Increment the major, minor or patch version number. 


### Debugging

`yotta debug` - Launch a debugger (uses [valinor](https://github.com/armmbed/valinor) to choose the debugger).


### Updating Modules

`yotta outdated` - Display modules with newer versions available.

`yotta update` - Update a module(s) to the latest possible versions. 


{% endcapture %}
<div class="col-md-6">
{{ colTwo | markdownify }}
</div>
<div class="clearfix"></div>

---

{% capture colThree %}


{% endcapture %}
<div class="col-md-6">
{{ colThree | markdownify }}
</div>

