---
layout: default
title: yotta Configuration System Reference
section: reference/buildsystem
---

# Build System Reference

yotta defines the way that software builds in order to make it easier for
separate modules to work together. It has both a simple automatic build system
that will build modules based on the source files discovered in the `source`
directory, and the capability to support building modules of any complexity
using [CMake](http://cmake.org).

## <a href="#info" name="info">#</a> Information Available To Builds

yotta makes some useful information available to the modules being compiled, which
can be embedded in the built binary or otherwise used at compile time. The
majority of this information is defined by yotta's [configuration
system](/reference/config.html), but if the yotta build information header is
included, then you can also access other information:

To include the yotta build information header:

```C
#include YOTTA_BUILD_INFO_HEADER
```

This header defines the following:

```C
#define YOTTA_BUILD_YEAR   2015 // the current year, UTC
#define YOTTA_BUILD_MONTH  9    // the current month, 1-12, UTC
#define YOTTA_BUILD_DAY    16   // the current day of the month, 1-31, UTC
#define YOTTA_BUILD_HOUR   18   // UTC hour 0-23
#define YOTTA_BUILD_MINUTE 16   // UTC minute 0-59
#define YOTTA_BUILD_SECOND 47   // UTC second 0-61 (1)
#define YOTTA_BUILD_UUID   1f37f267-f31b-48c0-bfdd-2a7a5449817b // a uuid representing the build (2)
```

If yotta finds a mercurial or git repository in the module or application being
built, then the following will also be defined in this header:

```C
#define YOTTA_BUILD_VCS_ID 0123456789abcdef // git or mercurial hash, variable length up to 40 characters
#define YOTTA_BUILD_VCS_CLEAN 1             // 1 if there were no uncommitted changes, else 0
```

Corresponding definitions for all of the build information are always available
in CMake without including any files.

Notes:

 * (1) Leap seconds will not currently occur in the _SECOND value, but they may do
   in future, so allow for the possibility of values up to and including 61 here.
 * (2) The build UUID changes every time that yotta build is invoked, even if the
   build would otherwise be identical.



## <a href="#automatic" name="automatic">#</a> Automatic Build System

yotta will automatically build the contents of the `source` and `test`
subdirectories of a software module. If you wan to exclude files from being
picked up by this build system then you can add them to a
[`.yotta_ignore`](/reference/ignore.html) file placed at the top of the module.

Any files in the source directory, and any of its subdirectories, will be
compiled into a single static library (for normal modules), or into the
application (for an executable module).

Any source files at the top-level of the test directory will be compiled into
separate test executables, and the (recursive) contents of any subdirectories
will each be compiled into a single test executable. You can use the
`yotta test` subcommand to build and run these tests.

Files in any other directories are normally ignored by yotta. By convention,
public header files that a module exposes are placed in a subdirectory with the
same name as the module, and then should be included as:

```C
#include "modulename/headername.h"
```


## <a href="#custom-cmake" name="custom-cmake">#</a> Using Custom CMake to Control The Build

To override yotta's default build rules for the `source` and `test`
directories, place your own CMakeLists.txt file in these directories. yotta
will also ensure that any CMakeLists.txt file in any other top-level
subdirectory of your module is included in the build. The testing with yotta
guide explains how to make yotta aware of any tests you add manually so that
`yotta test` can run them.

yotta will also respect a CMakeLists.txt file at the top-level of your module.
If this file is detected, then yotta will not automatically generate any build
rules. This is useful if you're adding yotta support to a module with an
existing build system, especially if the build system already uses CMake.

To ensure that yotta can automatically link your module to other modules, make
sure you define exactly one library with the same name as your module. A custom
build system may also define other build artifacts. In this case take care to
ensure that you name them in a way that minimizes the likelihood of name
collisions with other modules.

### <a href="#cmakelists" name="cmakelists">#</a> Places CMake Rules Can be Defined

There are various places you can define CMake rules to control the build, these
each have different effects:

 * **`./CMakeLists.txt` (in the module root)**: if you define a
   `CMakeLists.txt` file in the root of your module or executable, then yotta
   completely delegates building your module to this file.
 * **`./source/CMakeLists.txt`**: defining a `CMakeLists.txt` file in the
   source directory replaces yotta's default build rules for your library or
   executable, but yotta will still generate default rules for yout test
   directory (if any).
 * **`./source/<anything>.cmake`**: any .cmake files found in the source
   directory will be included at the *end* of the yotta-generated build rules
   for the source directory. If you want to make a very simple modification
   (such as definining a new preprocessor macro that your module needs), then
   this is the best way to do it. 
 * **`./test/CMakeLists.txt`**: defining a `CMakeLists.txt` file in the
   test directory replaces yotta's default build rules for your tests. yotta
   will build your library or executable from the contents of the source
   directory as normal.
 * **`./<anything>/CMakeLists.txt`**: Any subdirectory with a `CMakeLists.txt`
   file will be included in the build (unless it is ignored in the
   .yotta_ignore file). There aren't very many good reasons to do this.


### <a href="#cmake-definitions" name="cmake-definitions">#</a> Definitions Available in CMake Lists

yotta makes all the definitions which are available to the preprocessor
available to CMake scripts (including, for example, the path to the build
information header, and the definitions derived from the config information).

In addition, several other definitions are available, including:

 * `YOTTA_CONFIG_MERGED_JSON_FILE`: This expands to the full path of a file
   where the current yotta config information has been written. If you want to
   use the config information for advanced pre-build steps (such as including
   portions of it in the executable in a parseable form), then this is the file
   you should read the config information from.


## <a href="#build-products" name="build-products">#</a> Build Products

Everything that yotta generates during the build is created within the `build`
subdirectory. Within this directory build products are further divided by the
name of the [target](tutorial/targets.html) being built. This makes it safe to
switch between building for different targets without cleaning.

