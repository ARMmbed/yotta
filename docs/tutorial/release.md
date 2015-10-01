---
layout: default
title: Releasing Software With yotta
section: tutorial/releasing
---

# Releasing Software With yotta

At its simplest, the lifecycle of a yotta module is three steps:

 1. Write some code
 2. Commit it to version control (our favourite is [Github](http://github/com))
 3. Publish your module to the yotta registry

The yotta registry, which hosts released versions of yotta modules and makes
them searchable and accessible to other people, makes sure that every version
of your module that you publish will be available forever. So even if you
abandon your source code, delete your Github and run away to live in the
mountains, people who are using your code won't be left stranded.

(If you want to take ownership of an abandoned yotta module, to publish fixes
and improvements, please submit a ticket on the yotta [issue
tracker](https://github.com/armmbed/yotta/issues).)

<a name="versions"></a>
## Release Version Numbers

As far as yotta is concerned, you can manage your source code however you like.
When you run `yotta publish`, the version number will be read from your
`module.json` file, and a new version uploaded to the yotta registry. But there
are some rules you must follow to play nicely with people using your module:

 * Backwards incompatible releases should increase the major version number.
   (run `yotta version major` to do this for you, and create an associated git tag, if
   you're using git)

 * If you introduce additional functionality you should increase the minor
   version number (`yotta version minor`)

 * Any other changes (bugfixes, changes with no external effect) should change
   the patch version number. (`yotta version patch`)

These are the basic rules of [semantic versioning](http://semver.org), there
are some exceptions for `0.x.x` releases during early development, but if you
stick to the basics it's hard to go wrong.

<a name="branches"></a>
## Release Branches

If you increase the major version of your module, you should bear in mind that
people may continue to use the previous version for some time. So it's a good
idea to back-port any important security patches or bugfixes to earlier major
versions.

For example, if you're releasing version `2.0.1` to fix a bug in the `2.0.0`
release, and this bug is also present in the older `1.7.4` release, you should
back-port the fix and release version `1.7.5`. Anyone using your old version
will be able to update to a fixed version *without worrying about backwards
incompatible changes*.

If you're using git to manage your code, you can easily go back to an earlier
version, and start a new branch for bugfix releases like this:

```
git checkout -b 1.7-bugfixes v1.7.5
```

This creates a new branch called `1.7-bugfixes`, based on the existing tag
`v1.7.5`, which `yotta version` will have created for you when you increased
the version to 1.7.5. (If you don't see any tags in your Github repository,
that's probably because you need to run `git push --tags` to push your tags to
the remote.)

Once you've got this branch you can make and commit changes, then use
`yotta version patch` and `yotta publish` to bump the version and publish a new
version, before switching back to your master branch:

```
git checkout master
```
<a name="namespaces"></a>
## Release Namesapces

If your module is written in C++, you should also take advantage of C++
namespaces to provide backwards compatibility. Namespaces allow you to provide old
versions of your API alongside new versions, make it obvious which version of
an API someone is using, and make it easy for your users to switch between
versions of your API.

In fact, namespaces are such a useful feature of C++ that we'd recommend using
them even if your module is otherwise C.

For example:

```C++
// file: mymodule/api.h

namespace mymodule{

  namespace v1{
    // the old version of foo
    void foo();
  } // namespace v1
  
  namespace v2{
    // the new version of foo, which foos in an incompatible way to before
    void foo();
  } // namespace v2
  
  namespace current {
      // import all symbols from mymodule::v2 into mymodule::current. Anyone
      // who wants to live on the bleeding edge can use
      // mymodule::current::foo()
      using namespace ::mymodule::v2;
  } // namespace current

} // namespace mymodule
```

This allows use of both versions of `foo` in the same program, if that is
necessary.

```C++
//#include "mymodule/api.h"
int main(){
    // we live on the edge :)
    using mymodule::current::foo;
    
    // calls the foo() we've imported with the using declaration (v2)
    foo();

    // but sometimes it's nice to have an old friend around:
    mymodule::v1::foo();

    return 0;
}
```

Note that you should **never** use `using namespace xxx` declarations in the
global scope in header files, as this would pollute the global namespace. 

The `using` declaration in the example above is OK because it only imports
names from one `mymodule::` namespace into another `mymodule::` namespace, both
of which are under the control of the module author.


<a name="embedded-version-numbers"></a>
## Embedded Version Numbers

yotta makes the versions of modules available to CMake, and as preprocessor
definitions. This can be useful to include in built software so that a running
program can be queried for its version information. The definitions are:

```C
#define YOTTA_<MODULENAME>_VERSION_STRING "0.2.3"
#define YOTTA_<MODULENAME>_VERSION_MAJOR 0
#define YOTTA_<MODULENAME>_VERSION_MINOR 2
#define YOTTA_<MODULENAME>_VERSION_PATCH 3
```

These are defined for all modules in the system. Any non-alphanumeric
characters in the module name are converted to underscores, and the module name
is uppercase.

