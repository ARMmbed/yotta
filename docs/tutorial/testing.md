---
layout: default
title: Testing With yotta
section: tutorial/testing
---

## Testing With yotta

Good tests are a really important part of writing software that can be re-used
by other people. Even if you also use the yotta modules that you publish within
your own application: it's likely that other people will exercise your code in
ways you don't.

A good set of tests will exercise everything that your module does, and take
care to cover edge cases which may occur rarely, but cause failures which are
hard to track down and fix.

yotta supports testing through the `test` directory in every module, and the
[`yotta test`](/reference/commands.html#yotta-test) command.


## The `test` Directory

Each separate source file in the top level of the test directory will be
compiled into a separate executable (so each test should either have a `main()`
function or use a framework that provides a `main()`. In [mbed
OS](https://github.com/ARMmbed/mbed-os), `main` is defined by the system, and
each test application should define an
[`app_start`](https://github.com/armmbed/minar#impact) entry point, unless a
test framework is being used with other requirements.

For more complex tests, composed of a number of files, all of the source files
under each subdirectory within the test directory will be compiled into a
single executable.

A test directory that looks like this:

```
mymodule
 |_test
 |  |_foo.c
 |  |_bar.c
 |  \_complex
 |     |_support.c
 |     |_other
 |     |  \_other.c
 |     \_main.c
```

Will result in the following test executables:

 * `test/mymodule-test-foo`, compiled from `foo.c`
 * `test/mymodule-test-bar`, compiled from `bar.c`
 * `test/mymodule-test-complex`, compiled from `support.c`, `main.c` and `other.c`.


## `testDependencies`
The [`testDependencies` section](/reference/module.html#testDependencies) in
each module's `module.json` file can be used for dependencies like testing
frameworks which are only required for tests. Note that *all* the listed
`testDependencies` will be linked against all of the tests.

`testDependencies` should be used to depend on test frameworks, or modules that
are only required when running tests. For example, if your module is commonly
used with other modules, you may write tests to ensure that your module works
correctly when used with them. In this case these other modules should only be
listed as test dependencies so they are not required if someone does not wish
to run your tests.

## `yotta test`

To run the tests for your module, display their output, and whether they
passed/failed, run:

```
yotta test
```

Or to run the tests for all modules:

```
yotta test all
```

You can also name specific tests to run in place of `all`. Unless you are using
a specific [test reporter](#testreporter), yotta takes the exit status of your
test program to indicate success/failure (following the Unix convention that a
status of 0 means success).

<a name=cross-compiled-tests'></a>
### Cross-Compiling Target Support

yotta [build targets](/tutorial/targets.html) can be used to build modules to
run on devices other than the computer where yotta is running
(cross-compilation). In this case, yotta does not run the tests directly, but
needs the target description to provide a [`scripts.test`
command](/reference/target.html#scripts). This command is provided with the
path to the binary for the program being debugged by expanding any occurences
of `$program` in the arguments to the script into the path to the binary.

The test script is expected to load the binary onto the target device, execute
it, print its output to stdout, and exit with 0 if the test was successful, or
a non-zero status if it was not.

<a name=testreporter'></a>
### Test Reporter Scripts

Relying on the exit status of a test program to determine pass/fail can be
limiting. Depending on the test framework being used it may be necessary to
parse the output of the test and look for specific values to check for a
pass/fail, or it may be necessary to use an external program to verify the
correct behaviour of a test, instead of relying on self-test.

yotta allows this through the [`testReporter`
script](/reference/module.html#scripts) that each module can define.

When the tests for each module are run, their output is passed to the
`testReporter` script for verification.


<a name='advanced'></a>
## Advanced Testing

As well as putting source files in the `test` directory, you can also add tests
anywhere in custom `CMakeLists.txt` files. (yotta will not automatically
generate a CMakeLists.txt file describing what should be built for any
directory that already has one).

To do this, you should use the cmake `add_test` command in your
`CMakeLists.txt`, and add an additional dependency on the `all_tests` target:

```CMake
add_test(yourmodulename-test-yourtestname)
add_dependencies(all_tests yourmodulename-test-yourtestname)
```

