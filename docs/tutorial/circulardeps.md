---
layout: default
title: Handling Circular Dependencies in yotta
section: tutorial/circulardeps
---

# Handling Circular Dependencies in yotta

Sometimes two or more yotta modules depend on each other in a loop. In general
this should be avoided. It indicates that your modules are strongly coupled,
and perhaps should be shipped as a single module or should be divided up
differently, but if this is necessary it's something that yotta supports. In
this case there are some guidelines that can help you handle circular
dependencies successfully.

## Alternatives to Common Circular Dependency Patterns

### Abstract API with Multiple Implementations
Sometimes you have an API that has multiple possible implementations (which
might be for different hardware platforms, or different network transports, for
example).

In this case you might have an "API" module, `foo`, which provides the
interface that users of `foo` need to use about, and will be the thing that they
depend on. `foo` might depend on `foo-implementation-windows`, or
`foo-implementation-posix` depending on what platform it's being built for.

Each of these implementations would in turn depend on the `foo` module in order
to have access to the header files that declare the interface they are
implementing, leading to a circular dependency.


## Handling Circular Dependencies Successfully
### Version Specifications

If you have a set of modules which depend on each other in a cycle, and which
all impose [version specifications](/reference/module.html#dependencies) around
that cycle, then this can make it very hard to update to new versions of any of
the modules. Updating any one module at a time might break the version
requirements of others, making it difficult to seamlessly update to newer
versions of modules.

To prevent this situation from arising, one point in the cycle needs
not to have a relaxed version specification (such as `*`). On its own this will
not cause any version of the module being depended on to be 

A simple rule to do this is to identify the modules in the cycle which will
only normally be depended on by other modules that are also in the cycle (such
as API implementation modules, as described above). Since these modules won't
normally be depended on externally, they can have wildcard `*` version
specifications on the other modules in the cycle on which they depend. The
versions of these dependencies will instead by controlled by the external
dependencies on them.

### Adding a New Implementation of an Abstract API


