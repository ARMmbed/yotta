---
layout: default
title: Handling Circular Dependencies in yotta
section: tutorial/circulardeps
---

# Handling Circular Dependencies in yotta

It is possible for two or more yotta modules depend on each other in a loop. In
general this should be avoided. It might indicate that your modules are strongly
coupled, and perhaps should be shipped as a single module or that they should be divided
up differently. If however it *is* necessary to use circular dependencies,
that's something that yotta supports. In this case there are some guidelines
that can help you handle circular dependencies successfully.

## <a name="alternatives" href="#alternatives">#</a> Alternatives to Circular Dependency Patterns

If you can separate your modules in ways that avoid circular dependencies, then
this is preferred. Some common circular dependency patterns have simple
alternatives:

### <a name="interdependent-modules" href="#interdependent-modules">#</a> Interdependent Modules

![illustration of interdependent modules](/assets/img/interdependent-circle.png)

If two modules (`a` and `b` above) both call functions from each other, this
can be an indication of two things:

Either these modules are on the whole not independent, and should be combined into
a single module:

![illustration of combined module](/assets/img/interdependent-combined.png)

Or these modules are largely independent, but a small parts of both of them are
strongly connected. In this case at least one of these parts should be
separated into a third module, on which each module then depends. This only
needs to remove one of the dependencies between the two modules to break the
cycle:

![illustration of separated module](/assets/img/interdependent-separated.png)


### <a name="abstract-and-impl" href="#abstract-and-impl">#</a> Abstract API with Multiple Implementations
Sometimes you have an API that has multiple possible implementations (which
might be for different hardware platforms, or different network transports, for
example).

In this case you might have a module, `foo`, which provides some re-usable
functionality. `foo` itself might depend on `foo-implementation-windows`, or
`foo-implementation-posix` depending on what platform it's being built for, if
the functionality it is providing is implemented in different ways on different
platforms.

Each of these implementations would in turn depend on the `foo` module in order
to have access to the header files that declare the interface they are
implementing, leading to a circular dependency. For example:

![illustration of circular dependencies](/assets/img/foo-api-circle.png)

This circular dependency can be avoided by moving the header files with
declarations into a third module, called `foo-api` below, on which both of the
other modules depend. In this case `foo` is still the public module that other
people would depend on (and it could contain header files that include
appropriate `foo-api` headers, so that users do not need to know anything about
the`foo-api` module's existence).

![illustration of resolving circular dependencies](/assets/img/foo-api-nocircle.png)

## <a name="guidelines" href="#guidelines">#</a> Handling Circular Dependencies Successfully
### <a name="version-specifications" href="#version-specifications">#</a> Version Specifications

If you have a set of modules which depend on each other in a cycle, and which
all impose [version specifications](/reference/module.html#dependencies) around
that cycle, then this can make it very hard to update to new versions of any of
the modules as updating any one module at a time might break the version
requirements of others.

To prevent this situation from arising, one point in the cycle needs to
have a relaxed version specification (such as the wildcard "`*`").

![illustration of circular dependency version specifications](/assets/img/circular-deps-1.png)

A simple rule to do this is to identify the modules in the cycle which will
only normally be depended on by other modules that are also in the cycle (such
as API implementation modules, as described above). Since these modules won't
normally be depended on externally, they can have wildcard "`*`" version
specifications on the other modules in the cycle on which they depend. The
versions of these dependencies will instead by controlled by the external
dependencies on them.

