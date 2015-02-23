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

