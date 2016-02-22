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
system](/reference/config.html), but some other information is also available.

### Information Always Available
The name of the library being built by the current module is available as
`YOTTA_MODULE_NAME`, as if it were defined:

```
#define YOTTA_MODULE_NAME modulename-unquoted
```

No header needs to be included for this definition to be available.

Use the [preprocessor stringification
trick](https://gcc.gnu.org/onlinedocs/cpp/Stringification.html) to get the
module name as a string, if desired. Note that this definition is **not**
currently available when compiling tests, and there are other circumstances
where using custom CMake can make it unavailable.


### Information Available in the Build Info Header
If the yotta build information header is included, then you can also access
other information. Note that this header changes with every build (as it
includes a build timestamp and unique ID), so do not include it unnecessarily.

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
#define YOTTA_BUILD_VCS_DESCRIPTION v0.5-57-gad36348 // git describe or mercurial equivalent
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


### <a href="#cmake-examples" name="cmake-examples">#</a> Custom CMake Examples

All the following examples are using standard [CMake](http://cmake.org) syntax.
For documentation on the commands used, pleas see the [CMake
docs](https://cmake.org/documentation/).

General tips for writing CMake:

 * Always wrap expanded `"${VARIABLES}"` in quotes (or expand them inside a
   quoted string), if they are unquoted then any spaces in the expanded
   variable will cause it to be split into separate arguments

 * Where possible, avoid overriding yotta's generated CMakeLists.txt, and use
   the automatically included `.cmake` files to modify what yotta defined
   instead.

#### <a href="#generating-files" name="generating-files">#</a> Generating Files

If you have a script `./scripts/munge.py <input> <output>` that you want to run on an input file
`./resources/input.data` to generate an output C file to include in the build,
you can use a custom CMake file like this:

`./source/CMakeLists.txt`

```cmake
# construct the output path for our generated file (in the build directory, so
# that it gets removed by `yotta clean`):
set(MYMODULE_GENERATED_FILES ${CMAKE_BINARY_DIR}/generated/mymodule)

# ensure that the directory for the generated file exists:
file(MAKE_DIRECTORY "${MYMODULE_GENERATED_FILES}")

# save the paths to the script, input and output files, for convenience:
set(MYMODULE_MUNGE_SCRIPT "${CMAKE_CURRENT_LIST_DIR}/../scripts/munge.py")
set(MYMODULE_MUNGE_INPUT  "${CMAKE_CURRENT_LIST_DIR}/../resources/input.data")
set(MYMODULE_MUNGE_OUTPUT "${MYMODULE_GENERATED_FILES}/generated.c")

# define the command to generate this file
add_custom_command(
    OUTPUT "${MYMODULE_GENERATED_FILES}/generated.c"
    DEPENDS "${MYMODULE_MUNGE_SCRIPT}"
            "${MYMODULE_MUNGE_INPUT}"
    COMMAND python "${MYMODULE_MUNGE_SCRIPT}" "${MYMODULE_MUNGE_INPUT}" "${MYMODULE_MUNGE_OUTPUT}"
    COMMENT "Munging input into generated.c"
)

# define the library for this module, using the generated file:
add_library(mymodule # your module must create a library with its own name
    sourcefile1.c
    sourcefile2.c
    "${MYMODULE_GENERATED_FILES}/generated.c"
)

# link against the module's dependencies
target_link_libraries(mymodule
    mydependency
    myotherdependency
)

```

Note that as we're replacing the yotta-generated CMakeLists for the source
directory, you need to make sure you're still linking against all of your
module's dependencies

#### <a href="#changing-flags" name="changing-flags">#</a> Changing the Compilation Flags for a module

You can use a `.cmake` file to change the link flags of an existing target
without having to redefine the automatically generated build rules. For
example, if your module is called `mymodule`, you could add this:

`./source/override_flags.cmake`:

```CMake
# add -funroll loops to the compile commands used for the sources in this
# module... loops deserve some fun too!
set_target_properties(mymodule COMPILE_FLAGS "-funroll-loops")
```

Note that here "mymodule" is the name of the static library that your module is
generating (the CMake "target" that it defines – nothing to do with the yotta
target). By convention all yotta modules produce a static library with the same
name as the module

For documentation on the other things that you can set with
set_target_properties, including preprocessor definitions, see the [CMake
docs](https://cmake.org/cmake/help/v3.0/command/set_target_properties.html).

#### <a href="#linking-external" name="linking-external">#</a> Linking an External Library

`./source/link_foo.cmake`:

```CMake
# link ./precompiled/foo.a into mymodule, in addition to its yotta
# dependencies:

target_link_libraries(mymodule "${CMAKE_CURRENT_LIST_DIR}/../precompiled/foo.a")
```


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

