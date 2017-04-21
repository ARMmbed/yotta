---
layout: default
title: Using yotta link to fix bugs in dependencies
section: tutorial/yotta_link
---

## Using `yotta link` to Fix a Bug in a Dependency

It's possible, even in well-tested software, for issues to arise only when
modules are used in particular ways that were not anticipated by the authors.
Sometimes these can be hard to isolate, and its necessary to fix the bug while
working with a test application.

The [`yotta link`](/reference/commands.html#yotta-link) command is designed to
make it possible to investigate and fix issues in the dependencies of your
module or application. It allows you to "link" a development version of the
dependency where a problem is suspected (obtained, for example from GitHub)
into your test application.

### <a name="update" href="#update">#</a> **Step 0:** Update To Latest Versions
Before embarking on debugging a problem, it's a good idea to update to the
latest version of your dependencies, in case the problem has already been fixed
by someone else.

You can use the [`yotta outdated`](/reference/commands.html#yotta-outdated)
command to see which of your dependencies have newer versions available, and
the [`yotta update`](/reference/commands.html#yotta-update) command to download
updated versions.

Note that your module (or your dependencies) might have [version
specifications](/reference/module.html#dependencies) on dependencies that
prevent updates from being automatically downloaded. In this case you might
have to first relax the version specifications by editing your module.json file
(or ask the author of one of your dependencies to do the same): possibly
requiring changes to your module to accommodate breaking changes in the latest
version of your dependencies.

### <a name="identify" href="#identify">#</a> **Step 1:** Identify The Module With a Problem
The first step of fixing a bug is to identify which component is the source of
the problem. Sometimes this can be a challenge in itself. Assuming the bug
is a simple compilation error, it's easy to identify the file and module
involved from the compilation command:

(by default, if a compilation command fails, the full command that was run will
be displayed: this itself can be helpful for debugging)

```
helloyotta:jamcro01 git:master! $ yt build
info: generate for target: x86-osx-native 0.0.7 at /path/to/helloyotta/yotta_targets/x86-osx-native
-- Configuring done
-- Generating done
-- Build files have been written to: /path/to/helloyotta/build/x86-osx-native
[1/3] Building C object ym/simplelog/source/CMakeFiles/simplelog.dir/path/to/helloyotta/yotta_modules/simplelog/source/simplelog.c.o
FAILED: /usr/bin/cc -I/path/to/helloyotta -I/path/to/helloyotta/yotta_modules/simplelog -I/path/to/helloyotta/yotta_modules/simplelog/source -O2 -g -DNDEBUG   -include "/path/to/helloyotta/build/x86-osx-native/yotta_config.h" -MMD -MT ym/simplelog/source/CMakeFiles/simplelog.dir/path/to/helloyotta/yotta_modules/simplelog/source/simplelog.c.o -MF ym/simplelog/source/CMakeFiles/simplelog.dir/path/to/helloyotta/yotta_modules/simplelog/source/simplelog.c.o.d -o ym/simplelog/source/CMakeFiles/simplelog.dir/path/to/helloyotta/yotta_modules/simplelog/source/simplelog.c.o   -c /path/to/helloyotta/yotta_modules/simplelog/source/simplelog.c
/path/to/helloyotta/yotta_modules/simplelog/source/simplelog.c:25:50: error: expected ';' after expression
    printf("%s %s\n", prefixForLevel(level), msg) // deliberately missing semicolon
                                                 ^
                                                 ;
1 error generated.
ninja: build stopped: subcommand failed.
error: command ['ninja'] failed
```

Here we can see that the file that was being built when the error occurred was:

```
[1/3] Building C object ym/simplelog/source/CMakeFiles/simplelog.dir/path/to/helloyotta/yotta_modules/simplelog/source/simplelog.c.o
```

This is a path relative to the build directory, the `ym` directory is the
subdirectory where dependencies are built, and is always followed immediately
by a dependency name (if there were no `ym/` at the start of the path then the
object would belong to the top-level module/app being built). So from
`/ym/simplelog/...` we can tell that the failed file is in the `simplelog`
dependency.

This is also visible from the source file where the error is reported:

```
/path/to/helloyotta/yotta_modules/simplelog/source/simplelog.c:25:50: error: expected ';' after expression
```

In this case, the module name can be found from the section of the path
following `yotta_modules`:
<code>/path/to/helloyotta<b>/yotta_modules/simplelog</b>/source/...</code>.

Of course these are very simple cases, but the same rules can be used to
determine which modules paths in more complex error messages refer to.


### <a name="download" href="#download">#</a> **Step 2:** Download The Development Version 
Having identified that we have a problem with the `simplelog` dependency, the
next step is to download the latest source version.

The yotta registry page for a module will display the `repository` and
`homepage` fields from its description file, which can help us find this. For
example [for simplelog](http://yottabuild.org/#/module/simplelog/1.0.0). The
repository is listed as the github repository
[ARMmbed/simplelog](https://github.com/ARMmbed/simplelog).

If this information is missing, you can also check who published the module
using the `yotta owners` command, and contact them to ask them to add it, and
make their source repository available:

```
> yotta owners list simplelog
...
```

When you find the development repository, you may want to
[fork](https://help.github.com/articles/fork-a-repo/) it, so that
you have your own version that you can commit changes to. This will make it
easy to submit a [pull
request](https://help.github.com/articles/using-pull-requests/) to the original
repository later, once we've fixed the issue.

Now clone the fork into a convenient location (but do **not** do this inside
another yotta module, yotta may pick up the cloned subdirectory and build it as
part of the parent module):

```
git clone git@github.com:autopulated/simplelog.git ~/my/workspace/simplelog
...
```

### <a name="link-globally" href="#link-globally">#</a> **Step 3:** Link The Development Version Globally
Once downloaded, open a new terminal in the development version of the module.
At this point it might be a good idea to compile and run this module's own
tests (with [`yotta test`](http://localhost:4000/tutorial/testing.html)), to
check that the development version is functioning correctly.

We want to make this development version available to other
modules/applications that we're building. To do this, run [`yotta
link`](http://localhost:4000/reference/commands.html#yotta-link), to create a
link from the system-wide yotta modules directory to this development version
of the module:

```
> yotta link
info: /usr/local/lib/yotta_modules/simplelog -> ~/my/workspace/simplelog
```

(You may need to run this command with `sudo` if you do not have permission to
write to the system-wide yotta_modules directory where yotta attempts to create
the link)

### <a name="link-in" href="#link-in">#</a> **Step 4:** Link Into Test Module(s)
Once the `yotta link` step in the development version of the module is
completed, that version is now available for any other yotta module or
application that we're building to use.

To use the linked version when compiling another application, we need to run
`yotta link <modulename>` in the directory of the application we're building.
For example, to use it in our `helloyotta` program where we originally
encountered the bug:

```
> yotta link simplelog
info: ~/my/workspace/helloyotta/yotta_modules/simplelog -> /usr/local/lib/yotta_modules/simplelog -> ~/my/workspace/simplelog
```

Now when we build `helloyotta`, the source files that we cloned from the
development repository will be used.

If you have a bug which is affecting multiple example applications, and it's
useful to test out your fixes in all of them, then you can use `yotta link` to
link the development version into multiple different modules by repeating the
second link command. Just re-run (in this example) `yotta link simplelog` in
the directory of as many test applications as you like.

### <a name="debug" href="#debug">#</a> **Step 5:** Edit and Debug
Because the dependency that we downloaded is linked, rather than copied, into
the test application, any edits made to the development version will
immediately be available when we re-build.

This makes it easy to debug as normal (whether by using [`yotta
debug`](http://localhost:4000/reference/commands.html#yotta-debug) to launch an
interactive debugger, or adding additional logging to find the source of the
problem).

In our `simplelog` example the fix is trivial, we just need to insert a
semicolon on the correct line of the source file, where the compiler indicated
one was missing.

### <a name="submit-fix" href="#submit-fix">#</a> **Step 6:** Submit Pull Request
Once you've identified the fix for a module, submit a [pull
request](https://help.github.com/articles/using-pull-requests/) with your
changes from your fork of the module back to the original.

The author will then be able to review and merge your changes, and publish a
fixed version for everyone: sit back and enjoy the warm fuzzy feeling of
helping to make someone else's experience a little bit better!

<br>
<br>
<br>
## <a name="link-target" href="#link-target">#</a> Using `yotta link-target` to link Target Descriptions
`yotta link` is really useful for fixing bugs in modules. Sometimes bugs can
also occur in the target descriptions being used for compilation (for example,
some aspect of the device description in the [config information]() might be
incorrect).

`yotta link-target` can be used in the same way to link in the development
version of a target description:

After downloading the development version of a target description run:

```
yotta link-target
```

To link it into the global targets directory. Then use:

```
yotta link-target <targetname>
```

In the application that you want to build.

**NOTE:** CMake does not accurately track the dependencies on all of the
toolchain files, so after editing a target description it's best to use
`yotta clean` before rebuilding to ensure that your changes are accurately
reflected in the build.

<br>
## <a name="dependency-handling" href="#dependency-handling">#</a> Dependency Handling With `yotta link`
Note that when modules are linked the places on disk where dependencies are
read from might change. In some circumstances may be read from the
`yotta_modules` folder of a linked module, if the version there satisfies
version constraints that the one in the root module's `yotta_modules` folder
does not.

The `yotta update` and `yotta install` commands (and other commands that call
`yotta install` implicitly, such as `yotta build`) will never modify a linked
module, or perform any actions though the links that it creates, so if you need
to update a dependency that is being used through a link you will have to run
the `yotta update` command in the linked module itself.

Running `yotta list --all` will always show you whether there are any linked
modules in your current dependency graph, and show you the versions that are
bing used in the build.


