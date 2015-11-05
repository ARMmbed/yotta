---
layout: default
title: yotta
section: yotta/registry
---

# The yotta Public Registry
When you use [`yotta publish`](tutorial/release.html) to publish your re-usable
modules, they are uploaded to the yotta public registry.

They are immediately available to find via search
[online](http://yotta.mbed.com), and via the [`yotta
search`](reference/commands.html#yotta-search) subcommand, and for anyone to
install as a dependency of their own project.

## <a href="#module-ownership" name="module-ownership">#</a> Module Ownership
Before you can publish a module (or a target description), yotta will ask you
to log in. When you do, your email address(es) from the account you log in with
on the webpage are associated with the keys stored in your local yotta
settings.

These keys are used to sign requests made to the registry, proving to the
registry that you control the email address in question. This allows you to
publish updates to the same module in the future: if you switch to a different
computer then you'll need to log in again to regain access to publish your
modules.

To remove the stored keys from your settings, use the [`yotta logout`]() command.

The [`yotta owners`](/reference/commands.html#yotta-owners) subcommands (`yotta
owners list`, `yotta owner add` and `yotta owner remove`) allow you to add or
remove other people (by email address) from those allowed to publish new
versions (and modify ownership) of your modules and targets.

## <a href="#network-access" name="network-access">#</a> Network Access
In order to use the yotta registry, yotta needs access to several different
domains, which host various parts of the registry infrastructure. You may need
to allow access to these domains though your firewall:

 * `https://registry.yottabuild.org`: the registry API itself
 * `https://yotta.blob.core.windows.net`: the blob store where versions of
    modules and targets are downloaded from.
 * `http://yotta.mbed.com` and `https://yottabuild.org`: (these are the same
    website), and are necessary for the login mechanism.

**Note** that all of these domains may use multiple IP addresses, and each may
share their IP addresses with other domains.

