---
layout: default
title: Using yotta with Private Repositories
section: tutorial/privaterepos
---

# Private Repositories

As well as installing dependencies from the public registry, `yotta` can install dependencies directly from GitHub URLs, including private github repositories.

Sometimes it may not be appropriate publish a module to the public package registry, some modules may contain the secret sauce that powers your product, some may be too early in development to release and some may be too specific to a project to be useful to anyone else. `yotta` supports several ways of integrating these modules into your project:

###Using yotta with GitHub repositories

`yotta` provides a shorthand way to specify that a dependency should be included from a GitHub repository:

```
...
	"dependencies": {
		"secretsauce": "username/reponame"
	}
...
```

The shorthand GitHub URL is formed of two parts: `<username>/<reponame>` where `<username>` is the GitHub user or organisation name of the repository owner and `<reponame>` is the name of the repositiry. e.g. the `yotta` repositry can be found at `ARMmbed/yotta`.

You can specify a particular branch, tag or commit to use by providing it in the URL. The supported GitHub URL formats are:

```
username/reponame
username/reponame#<branchname>
username/reponame#<tagname>
username/reponame#<commit>
https://github.com/username/reponame
https://github.com/username/reponame#<branchname>
https://github.com/username/reponame#<tagname>
https://github.com/username/reponame#<commit>
```

If the GitHub repository is public, the dependency will simply be downloaded. If the GitHub repository is private and this is the first time you are downloading from a private GitHub repository, you will be prompted to log in to GitHub using a URL.

If you have a private GitHub repository and you would prefer to download it using SSH keys, you can use the following dependency form:

```
git@github.com:username/reponame.git
git@github.com:username/reponame.git#<branchname>
git@github.com:username/reponame.git#<tagname>
git@github.com:username/reponame.git#<commit>
```

###Other ways to depend on private repositories 
Using shorthand GitHub URLs is the easiest and recommended method of working with private repositories, however as not all projects are hosted on GitHub, `yotta` supports using git and hg URLs directly as well.

For example, to include a privately hosted git repository from example.com:

```
...
	"dependencies": {
		"usefulmodule": "git+ssh://user@example.com:path/to/repo"
	}
...
```

Git URLs support branch, version, tag and commit specifications:

```
git+ssh://example.com/path/to/repo
git+ssh://example.com/path/to/repo#<versionspec, branch, tag or commit>
anything://example.com/path/to/repo.git
anything://example.com/path/to/repo.git#<versionspec, branch, tag or commit>
```

Currently, mercurial URLs only support a version specification:

```
hg+ssh://example.com/path/to/repo
hg+ssh://example.com/path/to/repo#<versionspec>
anything://example.com/path/to/repo.hg
anything://example.com/path/to/repo.hg#<versionspec>
```

