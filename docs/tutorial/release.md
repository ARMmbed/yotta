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

## <a name="versions" href="#versions">#</a> Release Version Numbers

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

See [handling updates to dependencies](#dependency-updates) for guidance on how
to deal with breaking changes in your dependencies.

## <a name="branches" href="#branches">#</a> Release Branches

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
## <a name="namespaces" href="#namespaces">#</a> Release Namesapces

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


## <a name="embedded-version-numbers" href="#embedded-version-numbers">#</a> Embedded Version Numbers

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


## <a name="dependency-updates" href="##dependency-updates">#</a> Handling Updates to Dependencies

The [Semantic Versioning](https://semver.org) rules clearly explain how to
increment the version number of your module when its functionality changes, but
they don't offer a clear guide to how to handle breaking changes made in
dependencies of your module. In this case there are some guidelines you can
follow to minimise the disruption to users of your module:

### <a name="impl-update" href="#impl-update">#</a> Breaking Changes in Private Dependencies
One common pattern is for a yotta module to have private "implementation"
modules, which implement the functionality for different compilation targets,
with the right implementation module included based on [config
information](/reference/config.html).

In these cases the base module (`foo` below) is the only module on which users
will depend: the implementation modules are not depended on directly by
anything other than the main module.

![illustration of API with implementation modules](/assets/img/foo-impl-simple.png)

In this case, to handle a backwards incompatible change being made to the
`foo-impl-1` implementation module, perform the following steps:

 1. make the changes to the `-impl` module, and publish a new major version 3.0
   (following the [semver](http://semver.org) rule for incrementing the major
   version on a breaking change)

     At this point foo does not yet use the new version, because its `^2.0.0`
     [dependency specification](/reference/module.html#dependencies) restricts
     it to compatible versions.

 2. Update foo to use the new implementation, and update its dependency
    specification on `foo-impl-1` accordingly to `^3.0.0`.

 3. Publish a new **minor** version of foo, increasing its version from `1.0.0`
    to `1.1.0`.

 4. Now, when applications [update](/reference/commands.html#yotta-update) they will
    get a new minor version of foo, and new major version of foo-impl.

It's possible to do this because the app (or any other module depending on foo)
**does not depend on the implementation modules directly**. It only depends on them via foo.

The implementation modules should have warnings in their README's that they
should not be depended on directly: if someone depends on them then it will not
be possible to just update the minor version of foo (this is the [next
case](#shared-deps-update)).

### <a name="shared-deps-update" href="#shared-deps-update">#</a> Breaking Changes in Shared Dependencies
Another pattern is that our module might rely on another module for its
implementation which is **not** solely used by your own module. This might be
the case if, for example, you depend on a utility library that other modules
and applications also depend on. For example:

![illustration of depending on a shared utility library](/assets/img/foo-utility-dependency.png)

In this case, the sequence of events when the shared module (`utility` in this
example) makes a new major release with breaking changes is:

 * **(1)** A new major version of utility with the breaking changes is published
           (`3.0.0`).
    
      As before, neither foo, nor our hypothetical application use the new
      version at this point, because their ^2.0.0` [dependency
      specifications](/reference/module.html#dependencies) restrict the
      versions that will be used to compatible ones.

 * Update foo to use the new `utility` version, at this point there are
   two possibilities:
   * **(2A)** it's possible to make foo support **both** the old and new versions
     of `utility` (perhaps by `#ifdef`ing on the `YOTTA_<MODULENAME>_VERSION_MAJOR`
     definition which yotta will make available for every module).
   * **(2B)** it's **only** possible to support one of the major versions of
     `utility` at a time

#### <a name="exposed-dep-compatible-update" href="#exposed-dep-compatible-update">#</a> Handled in a Backwards Compatible Way
If **(A)** is possible, then:

  * **(3A)** publish a new minor version of foo which is compatible with both
             version `2.x` and `3.x` of utility, with a corresponding
             dependency specification: `">=2.0.0,<4.0.0"`

  * **(4A)** when applications update, they will get the new `utility` version unless
      they have other dependencies on an older version
 
#### <a name="exposed-dep-noncompatible-update" href="#exposed-dep-noncompatible-update">#</a> Handled in a Backwards Incompatible Way
In case **(B)** things are harder:

  * **(3B)** Publish a new **major** version of `foo`, with dependency specification on
             3.x of `utility`.

  * **(4B)** The app still won't use either the new version of `foo`, or the new version
             of `utility`.

  * **(5B)** The app (or any other module which uses both `utility` and
             `foo`) must increase its dependency specs for both `foo` and
             `utility` before being able to update.

     Anything else that depends on either `foo` or `utility` needs to
     repeat the process from **(2)**, to determine whether its own
     major version needs to be updated. For a module which updated its version
     only because 

### <a name="shared-private-dep" href="#shared-private-dep">#</a> Synchronised Updates

Case (B) above is bad because it potentially forces major version updates of
lots of modules, and places a high burden on users. Fortunately there are cases
even where (B) applies that we can avoid a major version bump to `foo`.

![shared synchronised dependencies](/assets/img/shared-private-dep.png)

If the shared dependency (`utility` in this case) is depended on not directly
by applications, but instead it is depended on *only* by another module(s)
`bar`, then we can avoid the major update to `foo` with a synchronised update to
`foo` and `bar`:

(This is possible, for example, in internal modules in [`mbed
OS`](https://github.com/armmbed/mbed-os), where the only other things that
depend on them are also internal mbed OS modules. It's also common in private
modules shared only within your own applications.)

 * **(3C)** Update both `foo` and `bar` to use the new major version of `utility`.
            Review and test these changes together using `yotta link`.
 * **(4C)** Publish **minor** updates of both `foo` and `bar` simultaneously,
            which depend on the new major version of `utility`.
 * **(5C)** Any user who updates or installs will either get new versions of *both* 
            `foo` and `bar`, or old versions of both of them: both of which are
            working configurations.

Note that this is compatible with semantic versioning since the APIs of neither
`foo` nor `bar` have changed in a backwards incompatible way. In the future a
smarter dependency solver in yotta should also make this case automatic, by
solving for a working set of dependencies globally, rather than locally at each
point in the dependency graph.

