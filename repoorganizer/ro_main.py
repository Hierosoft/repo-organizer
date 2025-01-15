#!/usr/bin/env python
from __future__ import print_function
import os
import sys

from repoorganizer import (
    load_settings,
    settings_path,  # only use for error messages here. See load_settings.
)

from repoorganizer.repocollection import (
    gather_repos,
)

MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(MODULE_DIR)
REPOS_DIR = os.path.dirname(REPO_DIR)
if os.path.isfile(os.path.join(REPOS_DIR, "hierosoft", "hierosoft",
                               "__init__.py")):
    sys.path.insert(0, os.path.join(REPOS_DIR, "hierosoft"))

from hierosoft.logging2 import getLogger  # noqa: E402  #type:ignore

logger = getLogger(__name__)


def echo_settings_help_repo():
    """Show help regarding repos with missing tokens.
    """
    print(
        "Your list of repos need to be set"
        " (one or more orgs or users) See readme.")
    print(
        '{\n'
        '  "sources": {\n'
        '    "github":  {\n'
        '      "orgs":  [...]\n'
        '      "users":  [...]\n'
        '      "tokens": {\n'
        '        "user_or_org": "..."\n'
        '      }\n')
    print(
        "- where user_or_org is your GitHub username or organization name,"
        " and ... is the token matching each"
        " (You must generate separate a separate token for"
        " your user(s) and organization(s)"
        " to list or clone private repos)")


def echo_settings_help_token(no_token):
    """Show help regarding repos with missing tokens.

    Args:
        no_token (dict[str,str]): Dictionary mapping category ('user' or
            'org') to a list of entries with no token.
    """
    print(
        "Your tokens need to be set and have permissions"
        " to read repositories, branches, etc.! See readme.")
    print(
        "The following names have no tokens in the 'tokens'"
        " dict in 'github' in {}: "
        .format(repr(settings_path)))
    print(
        '{\n'
        '  "sources": {\n'
        '    "github":  {\n'
        '      "tokens": {\n')
    for cat_name in ("orgs", "users"):
        for name in no_token[cat_name]:
            print(
                '        "{}": "[some {} token]",'
                .format(name, cat_name))


def main():
    """Main entry point for the script."""
    if not os.path.exists(settings_path):
        echo_settings_help_repo()
        logger.error("Settings file not found: %s" % settings_path)
        return 1

    settings = load_settings()

    # Validate structure
    if "sources" not in settings:
        echo_settings_help_repo()
        logger.error("Missing 'sources' key in settings.")
        return 1

    github = settings["sources"].get("github")
    if github is None:
        echo_settings_help_repo()
        logger.error("Missing 'github' key in 'sources'.")
        return 1

    refresh = False
    for arg in sys.argv[1:]:
        if arg == "--refresh":
            refresh = True
        else:
            logger.error("Unknown argument: {}".format(arg))
            return 1

    github = settings["sources"]["github"]
    orgs = github.get("orgs")
    users = github.get("users")

    if not orgs and not users:
        echo_settings_help_repo()
        logger.error(
            'No "orgs" or "users" specified under'
            ' "sources":{"github"... in settings.')
        return 1

    sources = settings.get('sources')
    github = None
    tokens = None
    if sources:
        github = sources.get('github')
    if github:
        tokens = github.get('tokens')
    else:
        github = {}
    if not tokens:
        tokens = {}
    counts = {}
    collections = []
    no_token = {}
    no_token_total = 0
    for cat_name in ("orgs", "users"):
        no_token[cat_name] = []
        counts[cat_name] = 0
        names = github.get(cat_name)
        # if cat_name == "users": break  # for debug only!
        if names is None:
            logger.info("'{}' is None".format(cat_name))
        elif isinstance(names, list):
            for name in names:
                token = tokens.get(name)
                if not token:
                    no_token[cat_name].append(name)
                    no_token_total += 1
                collection = gather_repos(name, is_org=(cat_name == "orgs"),
                                          token=token,
                                          refresh=refresh,
                                          dry_run=False)  # True is debug only!
                collections.append(collection)
                counts[cat_name] += 1
        else:
            logger.error(
                "{} is a {} (expected list). Check {}"
                .format(repr(cat_name), type(cat_name).__name__,
                        repr(settings_path)))
    # else the URL is used which lists all repos user can access
    #   (full name covers directory structure)

    logger.info(
        "Processed {} orgs {} users".format(counts['orgs'], counts['users']))
    print()
    if no_token_total:
        echo_settings_help_token(no_token)
    else:
        print("INFO: If private repos are still not cloned,"
              " try the --refresh argument."
              " Otherwise, ensure tokens have permissions to read repos"
              " for respective user or organization"
              " (must have separate token owned by organization)"
              " and are not expired."
              " Tokens were used for all list URLs during this run.")
    print("JSON URLs used:")
    for collection in collections:
        for json_url in collection.json_urls:
            print("- {}".format(json_url))
    return 0


if __name__ == "__main__":
    sys.exit(main())
