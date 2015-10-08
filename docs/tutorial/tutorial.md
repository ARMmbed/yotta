---
layout: default
title: Tutorial
section: tutorial/tutorial
---

# Tutorial
There are two sorts of things that `yotta` builds: modules, and executables. Modules are re-usable, and the source code for them is distributed in the `yotta` registry. Executables are stand-alone programs that depend on modules, and which are not normally published themselves.

We’ll look at creating and publishing a module, then using that module in a simple command line executable.

<a name="Creating a Module"></a>
## Creating a Module
Before creating a module you should always check the [yotta registry](https://yotta.mbed.com) to see if another module already exists that does the same thing. If it does, think about submitting a pull-request to that module first.

Let’s create a module that provides a really simple logging framework:

### yotta init
First create a directory with the name we want, and `cd` into it.

```sh
# in these code examples, lines that you type have "> " at the beginning, other
# lines are output from the running program:
> mkdir simplelog
> cd simplelog
```

[yotta init](/../reference/commands.html#yotta-init), will create the module description for us, after asking a few questions. It’ll provide some helpful defaults, too.

```sh
> yotta init
Enter the module name: <simplelog>
Enter the initial version: <0.0.0>
Short description: Really simple logging.
Keywords: <> logging
Author: James Crosby <james.crosby@arm.com>
Repository url: ssh://git@github.com/ARM-RD/simplelog
Homepage: http://github.com/ARM-RD/simplelog
What is the license for this project (ISC, MIT, Apache-2 etc.)?  <ISC>
Is this module an executable? <no>
> 
```

### Module Structure
`yotta init` also creates some directories for us to put things in:

```sh
> ls -l
total 4
-rw-r--r--  1 james  staff   420B 15 Sep 16:55 module.json
drwxr-xr-x  4 james  staff   136B 15 Sep 16:35 simplelog
drwxr-xr-x  4 james  staff   136B 15 Sep 16:41 source
drwxr-xr-x  4 james  staff   136B 15 Sep 16:41 test
```
Any source files placed in the `source` directory will be compiled automatically by yotta, when we build, and each source file placed into the `test` directory will be compiled into a separate executable (to learn more about testing with yotta see the [testing tutorial](/tutorial/testing.html).

Headers that define the interface to your module should be placed in the directory with the same name as your module (`simplelog` in this case). This pattern forces headers to be included with their full paths e.g. `#include "simplelog/log.h"`, instead of just `#include "log.h"`, which might be a header name that multiple different modules use.

### Implement!
The implementation of our logging module is just three files, a header file, an implementation file and a test:

The header file, `./simplelog/log.h`, declares the public interface to our module. It’s important to keep the public interface to the bare minimum (avoid including unnecessary headers, for example), as all users of your module (direct and indirect) will be exposed to the contents of your public header files.

For the same reason we prefix everything in the public header with the name of our module. Here we’re using the conventions that types are `UpperCamelCase`, functions are `lowerCamelCase`, and global variables are `Upper_Case_Underscore_Separated`. The exact conventions you use are up to you, but you **must** prefix all exported symbols.

```C
// header guard: C and C++ headers must guard themselves against multiple
// inclusion.
#ifndef SIMPLELOG_LOG_H
#define SIMPLELOG_LOG_H

// make sure the header works when included from C++
#ifdef __cplusplus
extern "C" {
#endif // def __cplusplus

// Log levels: note that we prefix everything with the module name. It's OK to
// use various Casing and underscore separated conventions to denote different
// types of symbols, since module names are forced to be lower case, and cannot
// include underscores (only - characters).
enum SimpleLogLevel{
    Simple_Log_Critical = 0,
    Simple_Log_Notice   = 1,
    Simple_Log_Error    = 2,
    Simple_Log_Warning  = 3,
    Simple_Log_Info     = 4,
    Simple_Log_Debug    = 100
};

// log the message at the given level
void simpleLog(enum SimpleLogLevel level, const char* msg);

// shortcut functions, still prefixed
void simpleLogError(const char* msg);
void simpleLogWarning(const char* msg);
void simpleLogInfo(const char* msg);
void simpleLogDebug(const char* msg);

#ifdef __cplusplus
} // extern "C"
#endif // def __cplusplus

// end the header inclusion guard
#endif // ndef SIMPLELOG_LOG_H
```

The source file, `./source/log.c`, simply implements the header, using `printf` to log messages:

```C
// include the libc header for printf
#include <stdio.h>

// include our own public header
#include "simplelog/log.h"

const char* prefixForLevel(enum SimpleLogLevel level){
    if(level <= Simple_Log_Critical){
        return "[critical]";
    }else if(level <= Simple_Log_Notice){
        return "[notice]";
    }else if(level <= Simple_Log_Error){
        return "[error]";
    }else if(level <= Simple_Log_Warning){
        return "[warning]";
    }else if(level <= Simple_Log_Info){
        return "[info]";
    }else{
        return "[debug]";
    }
}

// log the message at the given level
void simpleLog(enum SimpleLogLevel level, const char* msg){
    printf("%s %s\n", prefixForLevel(level), msg);
}

void simpleLogError(const char* msg){
    return simpleLog(Simple_Log_Error, msg);
}
void simpleLogWarning(const char* msg){
    return simpleLog(Simple_Log_Warning, msg);
}
void simpleLogInfo(const char* msg){
    return simpleLog(Simple_Log_Info, msg);
}
void simpleLogDebug(const char* msg){
    return simpleLog(Simple_Log_Debug, msg);
}
```

After implementing these files, our module's structure should look something
like this:

```sh
├── module.json
├── simplelog
│   └── log.h
├── source
│   └── simplelog.c
└── test
```

### yotta build
Now we have a header and implementation file, we can build our module!

```sh
> yotta build
info: generate for target: x86-osx-native 0.0.3 at /Dev/simplelog/yotta_targets/x86-osx-native
-- Configuring done
-- Generating done
-- Build files have been written to: /Dev/simplelog/build/x86-osx-native
Scanning dependencies of target simplelog
[100%] Building C object source/CMakeFiles/simplelog.dir/Dev/simplelog/source/simplelog.c.o
Linking C static library libsimplelog.a
[100%] Built target simplelog
```

Great, we’ve built our library! What next? Testing it, of course.

#### Test Test Test
Our module is not complete without a test that it’s working. For now we’ll just add a simple program, but ideally you would exercise all of your module’s API in one or more tests.

`yotta build` scans the `./test` directory, and will build a separate executable for each source file found there, so to add our test we can add a file called `./test/basic.c` with the following `main()` routine:

```C
#include "simplelog/log.h"

int main(){
    simpleLogDebug("hello simplelog!");
    return 0;
}
```

Now, when we run `yotta build`, yotta will also build our test:

```sh
> yotta build
info: generate for target: x86-osx-native 0.0.3 at /Dev/simplelog/yotta_targets/x86-osx-native
-- Configuring done
-- Generating done
-- Build files have been written to: /Dev/simplelog/build/x86-osx-native
[ 50%] Built target simplelog
Scanning dependencies of target simplelog-test-basic
[100%] Building C object test/CMakeFiles/simplelog-basic.dir/Dev/simplelog/test/basic.c.o
Linking C executable simplelog-test-basic
[100%] Built target simplelog-test-basic
```

Now let’s run our test, you’ll find it at `./build/x86-osx-native/test/simplelog-test-basic` (more on that path name later):

```sh
> ./build/x86-osx-native/test/simplelog-test-basic
[debug] hello simplelog!
```

Looks like things are working! Now, more on that path. It’s made up of three parts:

 * **`./build/`**: the build directory, everything that `yotta` generates when building is placed in here.
 * `./build/`**`x86-osx-native`**: this is the *target* that `yotta` was building for. If you don’t explicitly set the target, then yotta builds to run on the current computer. (If you built on a linux or windows computer `x86-osx-native` would be different.)
 * `./build/x86-osx-native/`**`test/simplelog-test-basic`**: the path to the test. The test name is automatically prefixed with `<modulename>-test-` as executable names must be globally unique.

### A Few Words About Targets
In ARM we use `yotta` to build software for embedded devices – not just desktop computers. When you’re compiling the same software for lots of different devices you need a mechanism to do different things, and often to include different dependencies, for each of the different devices.

The `yotta target` command lets you do this. It defaults to the system you’re building on (`x86-osx-native` on mac, `x86-linux-native` on linux, etc.) You can display the current target by running `yotta target` with no arguments:`

```sh
> yotta target
x86-osx-native
```

If you set a different target, by running `yotta target <targetname>`, then `yotta` will build code for that target instead.

### yotta publish
The most important part of `yotta` is the ability to publish our module so other can use it. Now that we’ve tested our module, lets do that!

```
> yotta publish
info: generate archive extracting to "simplelog-0.0.0"
warning: no readme.md file detected
info: published latest version: 0.0.0
```

Now anyone can install and use our module in their own program. We should probably add some documentation, too. Do this by creating a readme.md that uses Markdown to describe what your module does.

Publishing publishes the *source* of the module, not the built binaries (as the binaries would only be useful to people building on exactly the same platform).

Note that if you also created a module called simplelog you won't be able to publish it – only one module can exist in the public registry with any given name, so if you've created a better logging module (simplelog doesn't make the bar very high), then you'll need to think of a new name and change it by editing your module.json file. See the [module.json reference](/../reference/module.html) for details.

<a name="Creating an Executable"></a>
## Creating an Executable
Executables are runnable programs that depend on any number of other modules, and add their own code to build a program that does something useful. `yotta` isn’t designed for *distributing* executables, so they shouldn’t normally be published to the public registry, but it works great for building them.

### yotta init
Let’s start by creating a new directory for our executable, and running `yotta init` again, if you previously created the `simplelog` module, then cd up one directory first: `cd ..`

```sh
> mkdir helloyotta
> cd helloyotta
helloyotta james$ yotta init
Enter the module name: <helloyotta>
...
Is this module an executable? <no> yes
```

Note that this time we answered **yes** to the last question. This makes `yotta` add a `"bin"` property in the `module.json` module description file that it generates. If we open this file in a text editor, we'll see that it says to create a binary executable out of the contents of the `./source` directory:

```json
{
  "name": "helloyotta",
  ...
  "bin": "./source"
}
```

### Add Dependencies!
Now we can tell `yotta` that we want to use the module we created earlier, `simplelog`.

```sh
> yotta install simplelog
info: get versions for x86-osx-native
info: get versions for simplelog
info: download simplelog
```

This has saved `simplelog` as a dependency in the `module.json` file, specifying that the version should be approximately equal to the current version. See the [`yotta install`](/../reference/commands.html#yotta-install) documentation for more details.

```json
  "dependencies": {
    "simplelog": "~0.0.0"
  },
```

`yotta install` also creates a `yotta_modules` directory in the module's directory, which it uses to store your dependencies. This, along with a corresponding `yotta_targets directory`, and the `build` directory, may be overwritten by `yotta` at any time, so generally shouldn't be modified, and you should not create files in them.

### Implement
When `yotta` builds, it will automatically arrange that our executable is linked against the dependencies we've specified, and that their header files are available, so we can create a single file in the `./source` directory to get a working executable. For this example, use a file called `./source/hello.cpp`:

```C
#include "simplelog/log.h"

int main(){
    simpleLog(Simple_Log_Info, "Hello yotta!");
    return 0;
}
```

### Build
Just like building a module, when we run `yotta build` yotta will arrange for everything necessary to be compiled, and produce a result:

```sh
> yotta build
info: generate for target: x86-osx-native 0.0.3 at /Dev/helloyotta/yotta_targets/x86-osx-native
-- Configuring done
-- Generating done
-- Build files have been written to: /Dev/helloyotta/build/x86-osx-native
Scanning dependencies of target simplelog
...
[100%] Building C object source/CMakeFiles/helloyotta.dir/Dev/helloyotta/source/hello.cpp.o
Linking C executable helloyotta
[100%] Built target helloyotta
```

Notice that `yotta` also built simplelog's library: as modules are distributed as source, they need to be compiled too.

Our executable will have been placed in `./build/x86-osx-native/source`, (or `./build/<targetname>/source` if you're compiling for a different target.). Let's run it:

```sh
> ./build/x86-osx-native/source/helloyotta
[info] Hello yotta!
```

### That's it!
That's all of the basic principles of using `yotta`, for more information check out the full [command reference](/../reference/commands.html).

