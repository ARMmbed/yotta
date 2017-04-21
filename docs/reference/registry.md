---
layout: default
title: The yotta Public Registry Reference
section: yotta/registry
---

# The yotta Public Registry
When you use [`yotta publish`](tutorial/release.html) to publish your re-usable
modules, they are uploaded to the yotta public registry.

They are immediately available to find via search
[online](http://yottabuild.org), and via the [`yotta
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
 * `https://yottabuild.org`: necessary for the login mechanism.

**Note** that all of these domains may use multiple IP addresses, and each may
share their IP addresses with other domains.

## <a href="#disputes" name="disputes">#</a> Disputes and Names
Please open an issue on the [Github issue
tracker](https://github.com/armmbed/yotta/issues) for any disputes arising over
module ownership. Do not publish an empty module in order to "reserve" a name
for your future use - either implement something useful, or let someone else do
the same. If someone else wants to publish a useful module under a name you
have published only an empty module to then ownership of your module will be
granted to them.

If you use a trademark belonging to a company in your module name (e.g. a
silicon vendor's name) and that company later wants to support their hardware
or software in yotta, you may be asked to let them contribute to your module,
or take over maintenance of it.

To take over ownership of a module abandoned by its owner please open an issue
on Github, it is likely that these requests will be granted if contact cannot
be re-established with the owner within a reasonable amount of time.

## <a href="#terms" name="terms">#</a> Terms of Use
The yotta registry is for yotta modules (that's software that can usefully be
used with other yotta modules to build an application for at least one target).
yotta modules can support any target hardware (ARM or otherwise), but we
reserve the right to remove anything from the registry which isn't a useful
yotta module.

The [mbed terms of use](http://www.mbed.com/about-mbed/terms-use) apply to
your use of the yotta registry, and the content you upload.

