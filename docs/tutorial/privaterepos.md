---
layout: default
title: Using yotta with Private Repositories
section: tutorial/privaterepos
---

# Private Repositories

As well as installing dependencies from the public registry, yotta can install dependencies directly from GitHub URLs, including private github repositories.

Sometimes it may not be appropriate publish a module to the public package registry, some modules may contain the secret sauce that powers your product, some may be too early in development to release and some may be too specific to a project to be useful to anyone else. Yotta supports several ways of integrating these modules into your project:

###Using yotta with GitHub repositories

Yotta provides a shorthand way to specify that a dependency should be included from a GitHub repository:

```
...
	"dependencies": {
		"secretsauce": "username/reponame"
	}
...
```

The shorthand GitHub URL is formed of two parts: `<username>/<reponame>` where `<username>` is the GitHub user or organisation name of the repository owner and `<reponame>` is the name of the repositiry. e.g. the yotta repositry can be found at `ARMmbed/yotta`.

You can specify a particular branch or tag to use by providing it in the URL. The supported GitHub URL formats are:

```
username/reponame
username/reponame#<[versionspec](versionspec)>
username/reponame#<branchname>
username/reponame#<tagname>
```


###Other ways to depend on private repositories 
Using shorthand GitHub URLs is the easiest and reccomneded method of working with private repositories, however as not all projects are hosted on GitHub, yotta supports using git and hg URLs directly as well.

For example, to include a privately hosted git repository from example.com:

```
...
	"dependencies": {
		"usefulmodule": "git+ssh://user@example.com:path/to/repo"
	}
...
```

Git URLs support branch, version and tags specifications:

```
git+ssh://example.com/path/to/repo
git+ssh://example.com/path/to/repo#<versionspec, branch or tag>
anything://example.com/path/to/repo.git
anything://example.com/path/to/repo.git<versionspec branch or tag>
```

Currently, mercurial URLs only support a version specification:

```
hg+ssh://example.com/path/to/repo
hg+ssh://example.com/path/to/repo#<versionspec>
anything://example.com/path/to/repo.hg
anything://example.com/path/to/repo.hg<versionspec>
```

