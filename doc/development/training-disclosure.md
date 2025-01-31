# Training Disclosure for repo-organizer
This Training Disclosure, which may be more specifically titled above here (and in this document possibly referred to as "this disclosure"), is based on **Training Disclosure version 1.1.4** at https://github.com/Hierosoft/training-disclosure by Jake Gustafson. Jake Gustafson is probably *not* an author of the project unless listed as a project author, nor necessarily the disclosure editor(s) of this copy of the disclosure unless this copy is the original which among other places I, Jake Gustafson, state IANAL. The original disclosure is released under the [CC0](https://creativecommons.org/public-domain/cc0/) license, but regarding any text that differs from the original:

This disclosure also functions as a claim of copyright to the scope described in the paragraph below since potentially in some jurisdictions output not of direct human origin, by certain means of generation at least, may not be copyrightable (again, IANAL):

Various author(s) may make claims of authorship to content in the project not mentioned in this disclosure, which this disclosure by way of omission unless stated elsewhere implies is of direct human origin unless stated elsewhere. Such statements elsewhere are present and complete if applicable to the best of the disclosure editor(s) ability. Additionally, the project author(s) hereby claim copyright and claim direct human origin to any and all content in the subsections of this disclosure itself, where scope is defined to the best of the ability of the disclosure editor(s), including the subsection names themselves, unless where stated, and unless implied such as by context, being copyrighted or trademarked elsewhere, or other means of statement or implication according to law in applicable jurisdiction(s).

Disclosure editor(s): Hierosoft LLC

Project author: Hierosoft LLC

This disclosure is a voluntary of how and where content in or used by this project was produced by LLM(s) or any tools that are "trained" in any way.

The main section of this disclosure lists such tools. For each, the version, install location, and a scope of their training sources in a way that is specific as possible.

Subsections of this disclosure contain prompts used to generate content, in a way that is complete to the best ability of the disclosure editor(s).

tool(s) used:
- GPT-4-Turbo (Version 4o, chatgpt.com)

Scope of use: code described in subsections--typically modified by hand to improve logic, variable naming, integration, etc.


## repoorganizer
### __init__.py
- 2024-12-02

Create a python script with a RepoCollection class. Set a global called ENABLE_SSH = true. At the beginning of the script, ensure "~/.config/repo-organizer" exists (always use expanduser when using ~ in a path). The constructor should set self.repos = None and self.name = None. It should have a set_name method that sets self.name. The class should have a load_repos(self, refresh=False) method that uses the GitHub API to list all repositories for github.com/{self.name}. The method can simply download all of the json then the json module to parse it, and set  self.repos to the result. If refresh is False the refresh_repos method should first set repo_cache = "~/.config/repo-organizer/{self.name}/repos.json" and see if repo_cache exists, and if so, load it with json.load and return from the method early. If there is any output, use the logging module for the entire program, using info, warning, or error as appropriate. For example, if refresh is False and the repo_cache file does not exist, log a warning "No, {repo_cache}, so downloading {url}". If the file is downloaded, set a local variable downloaded = True. At the end of the method, if downloaded is True, save the data to repo_path. The main function should be called under "if __name__ == "__main__" like sys.exit(main()) and main should return 0 if ok. The main function should set org_name = "traincontrolsystems", repos_path = None, then iterate through a list of possible folders: try_paths = [@"C:\Projects", "~/git", "~/GitHub", "~/Documents/GitHub"] using expanduser to see which one has a subfolder called "mirror-{org_name}", then set repos_path and break. if repos_path is still None, show an "No repos dir was found, so for safety nothing was done. Create mirror-{org_name} folder in one of the following first: {try_paths}" then return 1. Then the main function should create org = RepoCollection() and org.set_name(org_name) then call org.load_repos(repos_path). You must also create this load_repos method. The load_repos method should iterate self.repos. In each iteration, construct the repo clone URL normally, but if ENABLE_SSH then construct it like "git@github.com/{self.name}/{repo_name}.git" For each entry in self.repos, which is constructed as per the GitHub API call you would have made to make it, check if a folder with the name of the repo exists under repos_path. If not, clone the repo there. If does exists, pull. If any fail to pull or clone, append a line to "~/.config/repo-organizer/errors.log" like "failed to clone {url}" or "failed to clone {url}". For predictable determination of failures, create a log_error method that opens the file in 'a' mode each time. Ensure the loop continues in either error case. If the clone or mirror is successful, use a new method called log_success that operates similarly but appends to a file called  ~/.config/repo-organizer/repo-organizer.log where each appears like a shell command such as "cd {path} && git pull" or "git clone {url} {repos_path}/{self.name}/{repo_name}". Make the script python 2 compatible, converting all of my format code to use percent-sign substitutions instead, and at the top of the script but the shebang for python and then from __future__ import print_function

Move the logic of main to a gather_repos function that accepts org_name

instead of having a hard-coded value for org_name, eliminate traincontrolsystems literal and look for a list called "org_names" in os.path.join(config_dir, "settings.json") and iterate through, calling gather_repos using each list element as the argument. Use get('org_names') and if the result is None or empty list or not isinstance list, show a specific error for each settings problem.

First rename "org_names" to "orgs". Then change the loading process so the settings.json file requires orgs to be inside of another dict called "github" that is in another dict called "sources". If "sources" is missing from the root of the dict (parsed json), show an error, If "github" is not within "sources", show an error for that. Then continue the orgs checking, but check for it in this new settings structure (via settings['sources']['github'].get('orgs')) and only show an error if also settings['sources']['github'].get('users') is None, empty list, or not isinstance list. Require a boolean in the set_name method that sets self.is_org. The gather_repos call will also require an is_org argument and pass it along to set_name. Return the entire settings object from load_settings instead of only the orgs, then iterate for org_name in settings['sources']['github'].get('orgs') if not None and add True to the gather_repos call. Then iterate user_name in settings['sources']['github'].get('users') if not None, using False as the second argument to gather_repos. Check the boolean in load_repos and change the url so the "orgs/" part is omitted from the url in that case.

To fully implement the Python 2 compatibility, require https://github.com/Hierosoft/hierosoft main branch, from hierosoft import logging2 as logging, and change the code to use urllib instead of requests: if sys.version_info.major >= 3:
```
    import urllib.request
    request = urllib.request
    from urllib.error import (
        HTTPError,
        URLError,
    )

    html_is_missing_a_submodule = False
    try:
        from html.parser import HTMLParser
    except ModuleNotFoundError as ex:
        html_is_missing_a_submodule = True
    if html_is_missing_a_submodule:
        import html
        # ^ Doesn't fix issue #3, but provides tracing info below.
        print("", file=sys.stderr)
        raise ModuleNotFoundError(
            "The html module is incomplete: {}"
            " If not using PyInstaller, ensure there is no extra"
            " html module (html directory or html.py file)"
            " that is not Python's builtin html/__init__.py"
            "\n\nIf using PyInstaller, you must add the following to"
            " your main py file (the file that is the first argument"
            " of the Analysis call in your spec file): "
            "\nimport html.parser\nimport html.entities"
            "".format(html.__file__)
        )
        # INFO:
        # - Adding 'parser' and 'entities' to __all__ in
        #   html/__init__.py did not solve the issue.

    from urllib.parse import urlparse, parse_qs
    from urllib.parse import quote as urllib_quote
    from urllib.parse import quote_plus as urllib_quote_plus
    from urllib.parse import urlencode
else:
    # Python 2
    import urllib2 as urllib  # type: ignore
    request = urllib
    from urllib2 import (  # type: ignore
        HTTPError,
        URLError,
    )
    from HTMLParser import HTMLParser  # noqa: F401 # type: ignore
    print("HTMLParser imported.", file=sys.stderr)
    from urlparse import urlparse, parse_qs  # noqa: F401 # type: ignore
    from urllib import quote as urllib_quote  # noqa: F401 # type: ignore
    from urllib import quote_plus as urllib_quote_plus  # noqa: F401,E501 # type: ignore
    from urllib import urlencode  # noqa: F401 # type: ignore
```

- 2025-01-13

Here is the updated class. Add a condition that adds the appropriate http headers required by the github API for sending a token in the case that self.token is set. The proper header is "Authorization: Bearer" (self.token) and correct URL for authenticated listing of repos is https://api.github.com/search/repositories?q=user:USERNAME where USERNAME is RepoCollection.user (add a new static attribute that defaults to "", and whenever set_name is called with is_org is False, set the static member to name):

- (pasted the imports and RepoCollection class)

### moregitcli.py
- 2025-01-15

Create a python function that takes a folder path of a local git repo and returns a list of all remote branches

It doesn't get the remote branches that weren't fetched yet. Make sure that gets done.

### ro_main.py
Change this to use argparse. Store true if this is passed. Add another boolean arg --no-forks. Add a string argument --destination.     for arg in sys.argv[1:]:
        if arg == "--refresh":
            refresh = True
        else:
            logger.error("Unknown argument: {}".format(arg))
            return 1

The default destination is settings_path from from repoorganizer import (
    load_settings,
    settings_path,  # only use for error messages here. See load_settings.
)

## pyproject.toml
- 2024-12-02
Make a pyproject.toml assuming this file is called repoorganizer/__init__.py, preferring classifiers the as metadata format.

Now  make the pyproject.toml require https://github.com/Hierosoft/hierosoft.git package as a requirement, using the appropriate url formatting as required by the pyproject.toml format

## setup.py
- 2024-12-02
Now create a setup.py equivalent to the pyproject.toml, and add the https://github.com/Hierosoft/hierosoft.git package as a requirement, using the appropriate url formatting as required by setuptools.
